#!/usr/bin/env python3
"""
賽道地圖繪製元件 - TrackMapWidget (Universal 版)
===============================================

從舊版 Track Analysis Module 移植的完整賽道繪圖邏輯，
支援：
1. 依據位置點繪製平滑賽道路徑
2. 顯示起迄點與距離標記
3. 視窗縮放自適應與手動縮放
4. 選項控制：網格、標記、標籤

Author: F1T Team
Date: 2025-10-02
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from bisect import bisect_left

from core.logger import get_logger
from core.gui_i18n import tr
from PyQt5.QtCore import QPointF, Qt, pyqtSignal, QSize, QPoint, QTimer, QRectF
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt5.QtWidgets import QWidget, QToolTip, QLabel

# 連動管理器 (Lap Analysis linkage)
try:
    from modules.gui.lap_analysis.linkage import linkage_manager
except ImportError:
    linkage_manager = None


logger = get_logger(component="gui.track_map")


class CornerTooltipLabel(QLabel):
    """
    自定義彎道標籤 Widget - TrackMapWidget 的子 Widget
    
    特點：
    - 半透明背景
    - 圓角邊框
    - 支援 HTML 格式
    - 右鍵關閉
    - 跟隨父 Widget 移動（使用相對座標）
    """
    
    def __init__(self, html_content: str, parent: QWidget):
        """
        初始化標籤
        
        Args:
            html_content: HTML 格式的標籤內容
            parent: 父 Widget (TrackMapWidget)，必須提供！
        """
        super().__init__(html_content, parent)  # 必須有 parent
        
        # 設定 HTML 內容
        self.setTextFormat(Qt.RichText)
        
        # 設定樣式
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 240, 240);
                border: 2px solid #2980b9;
                border-radius: 8px;
                padding: 8px;
                font-family: Arial;
                font-size: 10pt;
            }
        """)
        
        # ✅ 不設定 WindowFlags - 作為普通子 Widget
        # ❌ 不使用 Qt.ToolTip - 那會讓它變成頂層視窗！
        
        # 設定滑鼠追蹤和游標
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # 調整大小以適應內容
        self.adjustSize()
        
        # 確保標籤在最上層（相對於父 Widget 的其他子元素）
        self.raise_()
    
    def mousePressEvent(self, event):
        """右鍵關閉標籤"""
        if event.button() == Qt.RightButton:
            # 通知父 Widget 移除此標籤
            if self.parent():
                self.parent().remove_tooltip_label(self)
            event.accept()
        else:
            super().mousePressEvent(event)


class TrackMapWidget(QWidget):
    """可視化賽道位置資料的 PyQt Widget。"""

    point_clicked = pyqtSignal(dict)
    point_hovered = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.track_data: Optional[Dict[str, Any]] = None
        self.position_data: List[Dict[str, Any]] = []
        self.track_bounds: Optional[Dict[str, float]] = None

        self._base_scale: float = 1.0
        self.scale_factor: float = 1.0
        self._pending_fit: bool = False
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self._last_size: QSize = QSize(0, 0)

        self.show_start_point: bool = False
        self.show_finish_point: bool = False
        self.show_distance_markers: bool = False
        self.show_track_labels: bool = False
        self.show_grid: bool = False
        self.show_official_corners: bool = True  # 預設開啟：顯示 FastF1 官方彎道
        self.use_speed_gradient: bool = False  # 預設關閉：速度漸層模式
        self.show_speed_distribution: bool = True  # ✅ 新增：速度分布圓餅圖（預設開啟）
        self.speed_distribution_data: Optional[Dict[str, Any]] = None  # ✅ 儲存速度分布數據

        self._grid_spacing: float = 500.0  # 公尺
        self._max_grid_lines: int = 12
        
        # FastF1 官方彎道數據
        self.official_corners: List[Dict[str, Any]] = []
        
        # 🚩 彎道旗幟數據（用於危險度標記）
        self.corner_flags: Dict[str, Dict[str, Any]] = {}  # {"T1": {corner_analysis_data}, ...}
        
        # 🏁 Sector 邊界數據（S1/S2/S3 分隔線）
        self.sector_boundaries: List[Dict[str, Any]] = []  # [{"sector": 1, "name": "S1 End", "position_x": ..., ...}, ...]
        self.show_sector_boundaries: bool = True  # 預設開啟：顯示 Sector 邊界
        self._last_track_name: Optional[str] = None  # 記錄上次載入的賽道名稱（用於檢測賽道變更）
        
        # 🏎️ 超車事件數據（用於超車點標記）
        self.overtake_events: List[Dict[str, Any]] = []  # 超車事件列表
        self.show_overtake_markers: bool = True  # 預設開啟：顯示超車標記
        self.hovered_overtake_index: Optional[int] = None  # 當前懸停的超車事件索引
        
        # ✅ 新版標籤系統：多標籤支援，隨視窗移動
        self.hovered_corner: Optional[str] = None  # 當前懸停的彎道（例如 "T7"）
        self.pinned_tooltips: List[Dict[str, Any]] = []  # 固定的標籤列表
        # 每個元素: {
        #   'corner_key': str,           # 例如 "T5"
        #   'label': CornerTooltipLabel, # QLabel 實例
        #   'corner_world_pos': tuple,   # (x, y) 彎道世界座標
        #   'offset': tuple,             # (dx, dy) 相對彎道的偏移
        #   'custom_pos': QPoint or None # 自訂位置（拖動後）
        # }
        
        # 🆕 標籤拖動功能（參考 UniversalChartWidget）
        self.dragging_tooltip = False  # 是否正在拖動標籤
        self.dragging_tooltip_index = -1  # 正在拖動的標籤索引
        self.tooltip_drag_offset = QPoint(0, 0)  # 拖動偏移量

        # 連動狀態
        self._linkage_registered: bool = False
        self._master_linkage_enabled: bool = True
        self._dynamic_marker_visible: bool = True
        self._fixed_marker_visible: bool = True

        # 個別連動開關狀態
        self._linkage_enabled: bool = True

        # 時間軸支援
        self._use_time_axis: bool = False
        self._time_lookup: List[Tuple[float, float, float]] = []  # (time_seconds, x, y)
        self._time_values: List[float] = []
        self._time_available: bool = False

        # 連動標記資料
        self._distance_lookup: List[Tuple[float, float, float]] = []
        self._distance_values: List[float] = []
        self._distance_scale: float = 1.0
        self._raw_distance_range: Tuple[float, float] = (0.0, 0.0)
        self._dynamic_marker_distance: Optional[float] = None
        self._dynamic_marker_world: Optional[Tuple[float, float]] = None
        self._fixed_marker_distance: Optional[float] = None
        self._fixed_marker_world: Optional[Tuple[float, float]] = None

        # 記錄最後一次收到的連動訊號 (for debug/diagnostics)
        self._last_linkage_relative_y: float = 0.5

        self.setMouseTracking(True)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")

        self._register_linkage()

    # ------------------------------------------------------------------
    # 資料載入與設定
    # ------------------------------------------------------------------
    def load_track_data(self, track_data: Dict[str, Any]) -> bool:
        """供 Universal MDI 呼叫的資料載入接口。"""
        try:
            logger.info("[TRACK_MAP] load_track_data 開始")
            session_info = track_data.get("session_info", {})
            track_name = session_info.get("track_name") or session_info.get("event_name") or "Unknown"
            logger.info("[TRACK_MAP] 賽道名稱: %s", track_name)
            logger.debug("[TRACK_MAP] track_data keys: %s", list(track_data.keys()))
            
            # 🏎️ 清空舊的超車事件數據（避免賽道切換時座標錯位）
            self.overtake_events = []
            logger.debug("[TRACK_MAP] 已清空舊的超車事件數據")
            
            self.track_data = track_data or {}
            records = track_data.get("detailed_position_records") or track_data.get("position_records") or []
            self.position_data = [record for record in records if isinstance(record, dict)]

            bounds = track_data.get("position_analysis", {}).get("track_bounds")
            if not bounds:
                bounds = track_data.get("track_bounds")
            if not bounds:
                bounds = self._calculate_bounds_from_positions(self.position_data)

            self.track_bounds = bounds if isinstance(bounds, dict) else None
            
            # 載入 FastF1 官方彎道數據
            logger.info("[TRACK_MAP] 載入 official_corners")
            official_corners_data = track_data.get("official_corners", {})
            logger.debug("[TRACK_MAP] official_corners_data 類型: %s", type(official_corners_data))
            if isinstance(official_corners_data, dict):
                logger.debug("[TRACK_MAP] official_corners_data 內容: %s", official_corners_data)
            else:
                logger.warning("[TRACK_MAP] official_corners_data 不是 dict: %s", type(official_corners_data))
            
            if official_corners_data.get("available") and official_corners_data.get("corners"):
                self.official_corners = official_corners_data.get("corners", [])
                logger.info("[TRACK_MAP] 成功載入 %d 個官方彎道", len(self.official_corners))
                if self.official_corners:
                    first = self.official_corners[0]
                    logger.debug(
                        "[TRACK_MAP] 第一個彎道: number=%s, x=%s, y=%s",
                        first.get("number"),
                        first.get("x"),
                        first.get("y"),
                    )
            else:
                self.official_corners = []
                logger.warning("[TRACK_MAP] 未載入官方彎道")
                logger.debug("[TRACK_MAP] available: %s", official_corners_data.get("available"))
                logger.debug("[TRACK_MAP] corners 存在: %s", "corners" in official_corners_data)
                logger.debug("[TRACK_MAP] corners 數量: %d", len(official_corners_data.get("corners", [])))
            
            logger.debug("[TRACK_MAP] self.official_corners 最終狀態: 長度=%d", len(self.official_corners))
            logger.debug("[TRACK_MAP] self.show_official_corners 狀態: %s", self.show_official_corners)
            
            # 🏁 載入 Sector 邊界數據
            logger.info("[TRACK_MAP] 載入 sector_boundaries")
            
            # 🚨 檢測賽道變更（用於智能保護邏輯）
            current_track = track_name  # 從上方 session_info 已取得
            track_changed = (self._last_track_name is not None and 
                           current_track != "Unknown" and 
                           self._last_track_name != current_track)
            
            if track_changed:
                logger.info("[TRACK_MAP] 檢測到賽道變更: %s → %s", self._last_track_name, current_track)
            else:
                logger.info("[TRACK_MAP] 同一賽道: %s", current_track)
            
            # ⚠️ 關鍵問題：API 響應中 sector_boundaries 可能不存在
            # 原因：CLI Function 100 在 Line 1440-1441 只在有數據時才添加到 result
            #   if sector_boundaries:
            #       result["sector_boundaries"] = sector_boundaries
            # 這導致：API 響應可能完全沒有 "sector_boundaries" 欄位
            
            sector_boundaries_data = track_data.get("sector_boundaries", None)  # 改用 None 作為預設值
            logger.debug("[TRACK_MAP] sector_boundaries_data 類型: %s", type(sector_boundaries_data))
            logger.debug(
                "[TRACK_MAP] sector_boundaries_data: %s",
                sector_boundaries_data if sector_boundaries_data is not None else "欄位不存在",
            )
            logger.debug("[TRACK_MAP] 當前 self.sector_boundaries 數量: %d", len(self.sector_boundaries))
            
            if sector_boundaries_data and isinstance(sector_boundaries_data, list):
                # ✅ 有新數據：直接載入
                self.sector_boundaries = sector_boundaries_data
                logger.info("[TRACK_MAP] 成功載入 %d 個 Sector 邊界", len(self.sector_boundaries))
                for boundary in self.sector_boundaries:
                    logger.debug(
                        "[TRACK_MAP] - %s: distance=%s m, pos=(%s, %s)",
                        boundary.get("name"),
                        boundary.get("distance_m"),
                        boundary.get("position_x"),
                        boundary.get("position_y"),
                    )
            else:
                # 🛡️ 智能保護邏輯：區分「欄位不存在」vs「空列表」
                if track_changed:
                    # ✅ 賽道變更且無新數據：清空（避免座標錯位）
                    self.sector_boundaries = []
                    logger.info("[TRACK_MAP] 賽道變更且無新 Sector 數據，清空避免座標錯位")
                elif self.sector_boundaries:
                    # ✅ 同一賽道且無新數據：保留（避免消失）
                    logger.info(
                        "[TRACK_MAP] 同一賽道，保留現有 %d 個 Sector 邊界（API 未返回數據）",
                        len(self.sector_boundaries),
                    )
                    # 不修改 self.sector_boundaries - 保留現有數據
                else:
                    self.sector_boundaries = []
                    logger.warning("[TRACK_MAP] 無 Sector 邊界數據且當前為空，設置為空列表")
            
            # 更新記錄的賽道名稱
            if current_track != "Unknown":
                self._last_track_name = current_track
            
            logger.debug("[TRACK_MAP] self.sector_boundaries 最終狀態: 長度=%d", len(self.sector_boundaries))
            logger.debug("[TRACK_MAP] self.show_sector_boundaries 狀態: %s", self.show_sector_boundaries)
            
            self._build_distance_lookup()
            self._clear_dynamic_marker()
            self._clear_fixed_marker()

            if self.track_bounds:
                self._pending_fit = True
                self.fit_to_view()
            else:
                self.scale_factor = 1.0
                self.offset_x = 0.0
                self.offset_y = 0.0

            self.update()

            info = track_data.get("session_info", {})
            track_name = info.get("track_name") or info.get("event_name") or "Unknown"
            logger.info("[TRACK_MAP] Data loaded: %s, points=%d bounds=%s", track_name, len(self.position_data), self.track_bounds)
            
            # ✅ 載入速度分布數據
            speed_dist = track_data.get("speed_distribution")
            if speed_dist:
                self.speed_distribution_data = speed_dist
                logger.info(
                    "[TRACK_MAP] 已載入速度分布數據: Low=%.1f%%, Mid=%.1f%%, High=%.1f%%",
                    speed_dist.get("low_speed_percentage", 0),
                    speed_dist.get("mid_speed_percentage", 0),
                    speed_dist.get("high_speed_percentage", 0),
                )
            else:
                self.speed_distribution_data = None
                logger.warning("[TRACK_MAP] 未找到速度分布數據")
            
            return bool(self.position_data)
        except Exception as exc:
            logger.exception("[TRACK_MAP] Failed to load data")
            return False

    def set_corner_flags(self, corner_flags_data: Dict[str, Dict[str, Any]]) -> None:
        """
        設定彎道旗幟數據用於危險度視覺化
        
        Args:
            corner_flags_data: {"T1": {corner_analysis_data}, "T2": {...}, ...}
        """
        self.corner_flags = corner_flags_data
        logger.info("[TRACK_MAP] 已載入 %d 個彎道的旗幟數據", len(corner_flags_data))
        self.update()  # 觸發重繪

    def set_sector_boundaries(self, sector_boundaries_data: List[Dict[str, Any]]) -> None:
        """
        設定 Sector 邊界數據用於分隔線繪製
        
        Args:
            sector_boundaries_data: [
                {"sector": 1, "name": "S1 End", "position_x": 2126.9, "position_y": -2616.1, "distance_m": 1233.1},
                {"sector": 2, "name": "S2 End", "position_x": -4.0, "position_y": 660.0, "distance_m": 3130.3},
                {"sector": 3, "name": "S3 End (Finish Line)", "position_x": -3674.2, "position_y": -5269.4, "distance_m": 0.0}
            ]
        """
        self.sector_boundaries = sector_boundaries_data or []
        logger.info("[TRACK_MAP] 已載入 %d 個 Sector 邊界", len(self.sector_boundaries))
        if self.sector_boundaries:
            for boundary in self.sector_boundaries:
                logger.debug("[TRACK_MAP] Sector 邊界: %s 距離=%s", boundary.get("name", "Unknown"), boundary.get("distance_m", 0))
        self.update()  # 觸發重繪

    def set_overtake_events(self, overtake_events_data: List[Dict[str, Any]]) -> None:
        """
        設定超車事件數據用於超車點標記繪製
        
        Args:
            overtake_events_data: [
                {
                    "timestamp": "01:12:05.123",
                    "lap": 5,
                    "overtaking_driver_tla": "VER",
                    "overtaken_driver_tla": "LEC",
                    "x": 1234,  # GPS X 座標
                    "y": -5678,  # GPS Y 座標
                    "overtake_type": "on_track"
                },
                ...
            ]
        """
        self.overtake_events = overtake_events_data or []
        logger.info("[TRACK_MAP] 已載入 %d 個超車事件", len(self.overtake_events))
        if self.overtake_events:
            for event in self.overtake_events[:3]:  # 只顯示前3個
                logger.debug(
                    "[TRACK_MAP] 超車: %s 超越 %s @ (%s, %s)",
                    event.get("overtaking_driver_tla", "?"),
                    event.get("overtaken_driver_tla", "?"),
                    event.get("x", 0),
                    event.get("y", 0)
                )
        self.update()  # 觸發重繪

    def set_show_overtake_markers(self, show: bool) -> None:
        """設定是否顯示超車標記"""
        self.show_overtake_markers = show
        self.update()

    def set_track_data(self, position_data: List[Dict[str, Any]], track_bounds: Dict[str, float]) -> None:
        """兼容 legacy API。"""
        self.position_data = position_data or []
        self.track_bounds = track_bounds or self._calculate_bounds_from_positions(self.position_data)
        self.official_corners = []  # Legacy API 不包含官方彎道
        self._build_distance_lookup()
        self._clear_dynamic_marker()
        self._clear_fixed_marker()
        self._pending_fit = True
        self.fit_to_view()
        self.update()

    def set_display_options(
        self,
        show_start: Optional[bool] = None,
        show_finish: Optional[bool] = None,
        show_markers: Optional[bool] = None,
        show_labels: Optional[bool] = None,
        show_grid: Optional[bool] = None,
        show_corners: Optional[bool] = None,  # 新增：官方彎道開關
    ) -> None:
        if show_start is not None:
            self.show_start_point = bool(show_start)
        if show_finish is not None:
            self.show_finish_point = bool(show_finish)
        if show_markers is not None:
            self.show_distance_markers = bool(show_markers)
        if show_labels is not None:
            self.show_track_labels = bool(show_labels)
        if show_grid is not None:
            self.show_grid = bool(show_grid)
        if show_corners is not None:
            self.show_official_corners = bool(show_corners)
        self.update()

    # ------------------------------------------------------------------
    # 縮放與視圖控制
    # ------------------------------------------------------------------
    def fit_to_view(self) -> None:
        if not self.track_bounds:
            return

        self._base_scale, self.offset_x, self.offset_y = self._compute_fit_to_view()
        self.scale_factor = self._base_scale
        self._pending_fit = False
        self.update()

    def calculate_scale(self) -> None:
        """Legacy compatibility wrapper for older modules."""
        self.fit_to_view()

    def set_zoom(self, zoom_factor: float) -> None:
        if zoom_factor <= 0.0:
            self.fit_to_view()
            return

        if not self.track_bounds:
            return

        if self._pending_fit:
            self.fit_to_view()

        self.scale_factor = self._base_scale * zoom_factor
        self._recenter_after_zoom()
        self.update()

    def get_zoom(self) -> float:
        if self._base_scale == 0:
            return 1.0
        return self.scale_factor / self._base_scale

    def set_show_grid(self, show: bool) -> None:
        self.show_grid = bool(show)
        self.update()

    def set_show_markers(self, show: bool) -> None:
        self.show_distance_markers = bool(show)
        self.update()

    def set_speed_gradient_enabled(self, enabled: bool) -> None:
        """設置是否啟用速度漸層模式"""
        self.use_speed_gradient = bool(enabled)
        self.update()
    
    def set_speed_distribution_enabled(self, enabled: bool) -> None:
        """設置是否顯示速度分布圓餅圖"""
        self.show_speed_distribution = bool(enabled)
        self.update()

    def _recenter_after_zoom(self) -> None:
        if not self.track_bounds:
            return

        track_width = self.track_bounds["x_max"] - self.track_bounds["x_min"]
        track_height = self.track_bounds["y_max"] - self.track_bounds["y_min"]
        scaled_width = track_width * self.scale_factor
        scaled_height = track_height * self.scale_factor
        self.offset_x = (self.width() - scaled_width) / 2
        self.offset_y = (self.height() - scaled_height) / 2

    def _compute_fit_to_view(self) -> Tuple[float, float, float]:
        widget_width = max(1, self.width())
        widget_height = max(1, self.height())
        track_width = self.track_bounds["x_max"] - self.track_bounds["x_min"]
        track_height = self.track_bounds["y_max"] - self.track_bounds["y_min"]

        if track_width <= 0 or track_height <= 0:
            return 1.0, 0.0, 0.0

        margin_ratio = 0.9
        scale_x = (widget_width * margin_ratio) / track_width
        scale_y = (widget_height * margin_ratio) / track_height
        base_scale = min(scale_x, scale_y)

        offset_x = (widget_width - track_width * base_scale) / 2
        offset_y = (widget_height - track_height * base_scale) / 2
        return base_scale, offset_x, offset_y

    # ------------------------------------------------------------------
    # 繪圖邏輯
    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: D401 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(245, 245, 245))

        if not self.position_data or not self.track_bounds:
            painter.setPen(QPen(QColor(120, 120, 120)))
            painter.setFont(QFont("Microsoft YaHei", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "賽道地圖\n等待數據...")
            return

        if self._pending_fit or self.size() != self._last_size:
            self.fit_to_view()
            self._last_size = self.size()

        if self.show_grid:
            self._draw_grid(painter)

        points = self._create_screen_points()
        if len(points) < 2:
            painter.setPen(QPen(QColor(120, 120, 120)))
            painter.drawText(self.rect(), Qt.AlignCenter, "賽道點數不足以繪製")
            return

        path = self._build_track_path(points)

        # 🚀 根據 Speed 數據繪製不同顏色的路徑
        self._draw_speed_colored_path(painter, points)

        if self.show_distance_markers:
            self._draw_distance_markers(painter, points)
        
        # 繪製 FastF1 官方彎道標記
        if self.show_official_corners and self.official_corners:
            logger.debug("[TRACK_MAP] paintEvent: 準備繪製 %d 個彎道", len(self.official_corners))
            self._draw_official_corners(painter)
        else:
            if not self.show_official_corners:
                logger.debug("[TRACK_MAP] paintEvent: show_official_corners=%s (未啟用)", self.show_official_corners)
            if not self.official_corners:
                logger.debug("[TRACK_MAP] paintEvent: official_corners 為空 (長度=%d)", len(self.official_corners))
        
        # 繪製 Sector 邊界分隔線
        if self.show_sector_boundaries and self.sector_boundaries:
            logger.debug("[TRACK_MAP] paintEvent: 準備繪製 %d 個 Sector 邊界", len(self.sector_boundaries))
            self._draw_sector_boundaries(painter)
        else:
            if not self.show_sector_boundaries:
                logger.debug(
                    "[TRACK_MAP] paintEvent: show_sector_boundaries=%s (未啟用)",
                    self.show_sector_boundaries,
                )
            if not self.sector_boundaries:
                logger.debug(
                    "[TRACK_MAP] paintEvent: sector_boundaries 為空 (長度=%d)",
                    len(self.sector_boundaries),
                )

        # 🏎️ 繪製超車事件標記（綠色圓點）
        if self.show_overtake_markers and self.overtake_events:
            logger.debug("[TRACK_MAP] paintEvent: 準備繪製 %d 個超車標記", len(self.overtake_events))
            self._draw_overtake_markers(painter)

        # 在路徑繪製後呈現同步標記
        self._draw_markers(painter)
        
        # ✅ 繪製速度分布圓餅圖（左下角）
        if self.show_speed_distribution and self.speed_distribution_data:
            self._draw_speed_distribution_pie(painter)
        else:
            if not self.show_speed_distribution:
                logger.debug("[TRACK_MAP] show_speed_distribution = False（未啟用）")
            if not self.speed_distribution_data:
                logger.debug("[TRACK_MAP] 無 speed_distribution 數據")

    def _draw_speed_colored_path(self, painter: QPainter, points: List[QPointF]) -> None:
        """使用逐段繪製根據速度繪製漸層色賽道
        
        顏色方案：藍色（最高速） → 紅色（最慢速）
        
        ⚠️ 修復：不再使用 QLinearGradient（會導致對角線漸層錯位）
        改用逐段繪製，為每段線段設定精確速度顏色
        """
        # 檢查是否啟用速度漸層模式
        if not self.use_speed_gradient or not self.position_data or len(self.position_data) == 0:
            # 使用原始藍色（一般模式）
            path = self._build_track_path(points)
            painter.setPen(QPen(QColor(40, 40, 200), 4))
            painter.drawPath(path)
            painter.setPen(QPen(QColor(120, 120, 255), 1))
            painter.drawPath(path)
            return
        
        # 1. 收集所有速度值
        speeds = [record.get('speed', 0) for record in self.position_data]
        if not speeds or max(speeds) == 0:
            # 無有效速度數據，使用原始藍色
            path = self._build_track_path(points)
            painter.setPen(QPen(QColor(40, 40, 200), 4))
            painter.drawPath(path)
            return
        
        min_speed = min(speeds)
        max_speed = max(speeds)
        
        # 2. 逐段繪製賽道，為每段設定精確顏色
        # 設定圓滑線條樣式
        pen = QPen()
        pen.setWidth(5)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        
        for i in range(len(points) - 1):
            # 獲取當前線段的速度（使用線段中點的速度）
            if i < len(speeds):
                speed = speeds[i]
            else:
                speed = speeds[-1]
            
            # 計算速度對應的顏色（藍色 → 紅色）
            speed_ratio = (speed - min_speed) / (max_speed - min_speed) if max_speed > min_speed else 0.5
            
            # 速度漸層：高速=藍色，低速=紅色
            # 藍色 RGB(33, 150, 243) - Material Blue 500
            # 紅色 RGB(244, 67, 54) - Material Red 500
            r = int(33 + (244 - 33) * (1 - speed_ratio))
            g = int(150 + (67 - 150) * (1 - speed_ratio))
            b = int(243 + (54 - 243) * (1 - speed_ratio))
            
            color = QColor(r, g, b)
            pen.setColor(color)
            painter.setPen(pen)
            
            # 繪製線段
            painter.drawLine(points[i], points[i + 1])

    def _draw_grid(self, painter: QPainter) -> None:
        if not self.track_bounds:
            return

        spacing = self._grid_spacing
        bounds = self.track_bounds
        x_min, x_max = bounds["x_min"], bounds["x_max"]
        y_min, y_max = bounds["y_min"], bounds["y_max"]

        painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))

        count = 0
        x = (int(x_min // spacing) + 1) * spacing
        while x < x_max and count < self._max_grid_lines:
            sx1, sy1 = self.world_to_screen(x, y_min)
            sx2, sy2 = self.world_to_screen(x, y_max)
            painter.drawLine(sx1, sy1, sx2, sy2)
            count += 1
            x += spacing

        count = 0
        y = (int(y_min // spacing) + 1) * spacing
        while y < y_max and count < self._max_grid_lines:
            sx1, sy1 = self.world_to_screen(x_min, y)
            sx2, sy2 = self.world_to_screen(x_max, y)
            painter.drawLine(sx1, sy1, sx2, sy2)
            count += 1
            y += spacing
    
    def _draw_speed_distribution_pie(self, painter: QPainter) -> None:
        """
        在左下角繪製速度分布圓餅圖
        
        顏色方案（與速度梯度一致）：
        - 低速 (<120 km/h): 紅色
        - 中速 (120-200 km/h): 黃色
        - 高速 (>200 km/h): 藍色
        """
        if not self.speed_distribution_data:
            return
        
        # 提取百分比數據
        low_pct = self.speed_distribution_data.get('low_speed_percentage', 0)
        mid_pct = self.speed_distribution_data.get('mid_speed_percentage', 0)
        high_pct = self.speed_distribution_data.get('high_speed_percentage', 0)
        
        # 圓餅圖參數
        pie_diameter = 120  # 圓餅圖直徑（120px）
        margin_x = 15  # 左邊距
        margin_y = 15  # 下邊距
        
        # 計算圓餅圖位置（左下角）
        pie_x = margin_x
        pie_y = self.height() - pie_diameter - margin_y
        pie_rect = QRectF(pie_x, pie_y, pie_diameter, pie_diameter)
        
        # 定義顏色（與速度梯度一致）
        low_color = QColor(244, 67, 54)      # 紅色（低速）
        mid_color = QColor(255, 193, 7)      # 黃色（中速）
        high_color = QColor(33, 150, 243)    # 藍色（高速）
        
        # 繪製圓餅圖扇區
        # Qt 使用 16 分度（1度 = 16單位），起始角度從3點鐘方向開始，逆時針為正
        start_angle = 90 * 16  # 從12點鐘方向開始（90度）
        
        # 🔴 低速扇區
        low_span = int(low_pct * 360 / 100 * 16)
        painter.setBrush(QBrush(low_color))
        painter.setPen(QPen(Qt.white, 2))  # 白色邊框
        painter.drawPie(pie_rect, start_angle, -low_span)  # 逆時針
        
        # 🟡 中速扇區
        mid_span = int(mid_pct * 360 / 100 * 16)
        painter.setBrush(QBrush(mid_color))
        painter.drawPie(pie_rect, start_angle - low_span, -mid_span)
        
        # 🔵 高速扇區
        high_span = int(high_pct * 360 / 100 * 16)
        painter.setBrush(QBrush(high_color))
        painter.drawPie(pie_rect, start_angle - low_span - mid_span, -high_span)
        
        # 繪製文字標籤（圓餅圖右側）
        label_x = pie_x + pie_diameter + 10  # 圓餅圖右側 + 10px 間距
        label_start_y = pie_y + 15  # 從圓餅圖頂部往下一點開始
        label_spacing = 20  # 行間距
        
        # 設定文字字體（8pt，與表格一致）
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        # 🔴 低速標籤
        painter.setPen(QPen(low_color))
        low_text = f"<120km/h: {low_pct:.1f}%"
        painter.drawText(label_x, label_start_y, low_text)
        
        # 🟡 中速標籤
        painter.setPen(QPen(mid_color))
        mid_text = f"120-200km/h: {mid_pct:.1f}%"
        painter.drawText(label_x, label_start_y + label_spacing, mid_text)
        
        # 🔵 高速標籤
        painter.setPen(QPen(high_color))
        high_text = f">200km/h: {high_pct:.1f}%"
        painter.drawText(label_x, label_start_y + label_spacing * 2, high_text)

    def _create_screen_points(self) -> List[QPointF]:
        return [QPointF(*self.world_to_screen(rec.get("position_x", 0), rec.get("position_y", 0))) for rec in self.position_data]

    def _build_track_path(self, points: List[QPointF]) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(points[0])
        for idx in range(1, len(points)):
            if idx < len(points) - 1:
                mid = QPointF((points[idx].x() + points[idx + 1].x()) / 2, (points[idx].y() + points[idx + 1].y()) / 2)
                path.quadTo(points[idx], mid)
            else:
                path.lineTo(points[idx])
        return path

    def _draw_start_finish(self, painter: QPainter, points: List[QPointF]) -> None:
        if self.show_start_point and points:
            painter.setBrush(QBrush(QColor(0, 200, 0)))
            painter.setPen(QPen(QColor(0, 120, 0), 2))
            painter.drawEllipse(points[0], 6, 6)
            if self.show_track_labels:
                painter.setFont(QFont("Arial", 8, QFont.Bold))
                painter.setPen(QPen(QColor(0, 100, 0)))
                painter.drawText(int(points[0].x()) + 10, int(points[0].y()) - 5, "START")

        if self.show_finish_point and len(points) > 1:
            painter.setBrush(QBrush(QColor(200, 0, 0)))
            painter.setPen(QPen(QColor(120, 0, 0), 2))
            painter.drawEllipse(points[-1], 6, 6)
            if self.show_track_labels:
                painter.setFont(QFont("Arial", 8, QFont.Bold))
                painter.setPen(QPen(QColor(100, 0, 0)))
                painter.drawText(int(points[-1].x()) + 10, int(points[-1].y()) - 5, "FINISH")

    def _draw_distance_markers(self, painter: QPainter, points: List[QPointF]) -> None:
        if not self.position_data:
            return

        painter.setBrush(QBrush(QColor(0, 0, 200)))
        painter.setPen(QPen(QColor(0, 0, 150), 1))
        step = max(1, len(points) // 8)
        for idx in range(step, len(points) - 1, step):
            painter.drawEllipse(points[idx], 3, 3)
            distance_raw = self._extract_distance(self.position_data[idx])
            distance_m = self._normalize_distance(distance_raw)
            if distance_m is not None:
                painter.setFont(QFont("Arial", 7))
                painter.setPen(QPen(QColor(0, 0, 120)))
                painter.drawText(int(points[idx].x()) + 5, int(points[idx].y()) + 15, f"{distance_m/1000:.1f} km")
    
    def _draw_official_corners(self, painter: QPainter) -> None:
        """繪製 FastF1 官方彎道標記 - 根據旗幟數據顯示危險度"""
        
        logger.debug("[TRACK_MAP] _draw_official_corners() 執行，數量=%d", len(self.official_corners))
        
        if not self.official_corners:
            logger.debug("[TRACK_MAP] self.official_corners 為空，跳過繪製")
            return
        
        logger.debug("[TRACK_MAP] 準備繪製 %d 個彎道標記", len(self.official_corners))
        if len(self.official_corners) > 0:
            first = self.official_corners[0]
            logger.debug("[TRACK_MAP] 第 1 個彎道: %s", first)
        
        # 預設樣式 - 白底黑字
        default_bg_color = QColor(255, 255, 255, 240)
        border_color = QColor(0, 0, 0)
        text_color = QColor(0, 0, 0)
        
        # 旗幟顏色
        yellow_color = QColor(255, 255, 0, 220)  # 黃色
        red_color = QColor(255, 0, 0, 220)  # 紅色
        
        border_pen = QPen(border_color, 2)
        text_pen = QPen(text_color)
        text_font = QFont("Arial", 8, QFont.Bold)
        
        painter.setFont(text_font)
        
        marker_radius = 11
        offset_distance = 20
        
        drawn_count = 0
        for corner in self.official_corners:
            corner_x = corner.get("x", 0.0)
            corner_y = corner.get("y", 0.0)
            corner_num = corner.get("number", 0)
            
            # 計算偏移
            offset_x, offset_y = self._calculate_corner_offset(corner_x, corner_y, offset_distance)
            screen_x, screen_y = self.world_to_screen(offset_x, offset_y)
            
            # 檢查視口
            margin = 50
            if (screen_x < -margin or screen_x > self.width() + margin or
                screen_y < -margin or screen_y > self.height() + margin):
                continue
            
            # 🚩 檢查該彎道的旗幟數據
            corner_key = f"T{corner_num}"
            has_yellow = False
            has_safety_car = False
            
            if corner_key in self.corner_flags:
                corner_data = self.corner_flags[corner_key]
                yearly_breakdown = corner_data.get('yearly_breakdown', {})
                
                # 統計所有年份的旗幟
                for year_data in yearly_breakdown.values():
                    if year_data.get('yellow', 0) > 0 or year_data.get('double_yellow', 0) > 0:
                        has_yellow = True
                    if year_data.get('safety_car', 0) > 0:
                        has_safety_car = True
            
            # 🎨 根據旗幟類型繪製圓圈
            # 黃色 = 黃旗/雙黃旗，淺紫色 = 安全車觸發點
            lavender_color = QColor(200, 162, 200, 220)  # 淺紫色（薰衣草色）
            
            if has_yellow and has_safety_car:
                # 左半圓黃色，右半圓淺紫色
                from PyQt5.QtCore import QRectF
                rect = QRectF(screen_x - marker_radius, screen_y - marker_radius, 
                            marker_radius * 2, marker_radius * 2)
                
                # 繪製左半圓（黃色）
                painter.setPen(border_pen)
                painter.setBrush(QBrush(yellow_color))
                painter.drawPie(rect, 90 * 16, 180 * 16)  # 從 90° 繪製 180°
                
                # 繪製右半圓（淺紫色）
                painter.setBrush(QBrush(lavender_color))
                painter.drawPie(rect, 270 * 16, 180 * 16)  # 從 270° 繪製 180°
                
            elif has_safety_car:
                # 全淺紫色（安全車）
                painter.setPen(border_pen)
                painter.setBrush(QBrush(lavender_color))
                painter.drawEllipse(screen_x - marker_radius, screen_y - marker_radius, 
                                  marker_radius * 2, marker_radius * 2)
                
            elif has_yellow:
                # 全黃色（黃旗/雙黃旗）
                painter.setPen(border_pen)
                painter.setBrush(QBrush(yellow_color))
                painter.drawEllipse(screen_x - marker_radius, screen_y - marker_radius, 
                                  marker_radius * 2, marker_radius * 2)
            else:
                # 預設白色（無旗幟事件）
                painter.setPen(border_pen)
                painter.setBrush(QBrush(default_bg_color))
                painter.drawEllipse(screen_x - marker_radius, screen_y - marker_radius, 
                                  marker_radius * 2, marker_radius * 2)
            
            # 繪製黑色彎道編號
            painter.setPen(text_pen)
            text = str(corner_num)
            
            from PyQt5.QtCore import QRect
            text_rect = QRect(
                screen_x - marker_radius,
                screen_y - marker_radius,
                marker_radius * 2,
                marker_radius * 2
            )
            
            painter.drawText(text_rect, Qt.AlignCenter, text)
            drawn_count += 1
        
        if drawn_count == 0:
            logger.warning(
                "[TRACK_MAP] 0 個彎道在視口內（共 %d 個彎道）",
                len(self.official_corners),
            )
    
    def _calculate_corner_offset(self, corner_x: float, corner_y: float, offset_dist: float) -> Tuple[float, float]:
        """
        計算彎道標記的智能偏移位置
        
        策略：找到最近的賽道點，計算從賽道點到彎道的方向，然後沿該方向偏移
        """
        if not self.position_data:
            return corner_x, corner_y
        
        import math
        
        # 找到最近的賽道點
        min_dist = float('inf')
        nearest_track_x = corner_x
        nearest_track_y = corner_y
        
        for pos in self.position_data:
            track_x = pos.get("position_x", 0.0)
            track_y = pos.get("position_y", 0.0)
            
            dist = math.sqrt((track_x - corner_x)**2 + (track_y - corner_y)**2)
            if dist < min_dist:
                min_dist = dist
                nearest_track_x = track_x
                nearest_track_y = track_y
        
        # 計算從賽道點到彎道位置的向量（這是向外的方向）
        dx = corner_x - nearest_track_x
        dy = corner_y - nearest_track_y
        
        # 正規化方向向量
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx /= length
            dy /= length
        else:
            # 如果彎道點和賽道點重合，使用預設方向
            dx, dy = 1.0, 0.0
        
        # 沿著向外方向偏移
        offset_x = corner_x + dx * offset_dist
        offset_y = corner_y + dy * offset_dist
        
        return offset_x, offset_y

    def _draw_sector_boundaries(self, painter: QPainter) -> None:
        """
        繪製 Sector 邊界分隔線 (S1/S2/S3)
        
        在每個 Sector 邊界位置繪製垂直於賽道的線段，並標註 S1/S2/S3 文字
        """
        import math
        import numpy as np
        
        logger.debug("[TRACK_MAP] 準備繪製 %d 個 Sector 邊界", len(self.sector_boundaries))
        
        for boundary in self.sector_boundaries:
            sector_num = boundary.get('sector', 0)
            sector_name = boundary.get('name', f'S{sector_num}')
            position_x = boundary.get('position_x', 0.0)
            position_y = boundary.get('position_y', 0.0)
            distance_m = boundary.get('distance_m', 0.0)
            
            # 轉換到屏幕座標
            screen_x, screen_y = self.world_to_screen(position_x, position_y)
            
            # 檢查是否在視口內
            margin = 100
            if (screen_x < -margin or screen_x > self.width() + margin or
                screen_y < -margin or screen_y > self.height() + margin):
                continue
            
            # 🎯 計算賽道切線方向（找到該位置附近的賽道點）
            tangent_vector = self._get_track_tangent_at_position(position_x, position_y)
            
            # 🎯 計算法向量（垂直方向）
            if tangent_vector:
                # 法向量 = (-tangent_y, tangent_x) - 逆時針旋轉 90°
                normal_x = -tangent_vector[1]
                normal_y = tangent_vector[0]
                
                # 正規化
                length = math.sqrt(normal_x**2 + normal_y**2)
                if length > 0:
                    normal_x /= length
                    normal_y /= length
            else:
                # 預設方向（水平）
                normal_x, normal_y = 0.0, 1.0
            
            # 🎨 繪製垂直線段（兩側各延伸，垂直於賽道方向）
            line_length = 400.0  # 世界座標單位（公尺） - 改為 400m
            start_x = position_x - normal_x * line_length
            start_y = position_y - normal_y * line_length
            end_x = position_x + normal_x * line_length
            end_y = position_y + normal_y * line_length
            
            # 轉換到屏幕座標
            start_screen_x, start_screen_y = self.world_to_screen(start_x, start_y)
            end_screen_x, end_screen_y = self.world_to_screen(end_x, end_y)
            
            # 🎨 繪製黑色虛線（垂直於賽道）
            pen = QPen(QColor(0, 0, 0), 1, Qt.DashLine)  # 黑色虛線，細 1px
            painter.setPen(pen)
            painter.drawLine(int(start_screen_x), int(start_screen_y), int(end_screen_x), int(end_screen_y))
            
            logger.debug(
                "[TRACK_MAP] 繪製 %s 線條: 世界座標 (%.1f,%.1f)->(%.1f,%.1f)",
                sector_name,
                start_x,
                start_y,
                end_x,
                end_y,
            )
            logger.debug(
                "[TRACK_MAP] %s 線條屏幕座標 (%d,%d)->(%d,%d)",
                sector_name,
                int(start_screen_x),
                int(start_screen_y),
                int(end_screen_x),
                int(end_screen_y),
            )
            
            # 🎨 繪製 Sector 標籤文字（例如 "S1", "S2", "S3"）
            # 決定標籤簡稱
            if sector_num == 1:
                label_text = "S1"
            elif sector_num == 2:
                label_text = "S2"
            elif sector_num == 3:
                label_text = "S3"
            else:
                label_text = f"S{sector_num}"
            
            # 標籤背景框
            font = QFont("Arial", 10, QFont.Normal)  # 字體改小 (12→10)，不要粗體
            painter.setFont(font)
            
            # 計算文字尺寸
            from PyQt5.QtCore import QRectF
            text_rect = painter.boundingRect(QRectF(), Qt.AlignCenter, label_text)
            text_width = text_rect.width()
            text_height = text_rect.height()
            
            # 標籤位置：放在線段尾端（賽道外側 - 反方向）
            label_offset = -800.0  # 負值 = 往法向量反方向，-800m 更遠離賽道
            label_x = position_x + normal_x * label_offset
            label_y = position_y + normal_y * label_offset
            label_screen_x, label_screen_y = self.world_to_screen(label_x, label_y)
            
            # 繪製白色半透明背景框（無外框）
            padding = 6
            box_rect = QRectF(
                label_screen_x - text_width / 2 - padding,
                label_screen_y - text_height / 2 - padding,
                text_width + 2 * padding,
                text_height + 2 * padding
            )
            
            painter.setPen(Qt.NoPen)  # 取消黑色外框
            painter.setBrush(QBrush(QColor(255, 255, 255, 230)))  # 白色半透明背景
            painter.drawRoundedRect(box_rect, 5, 5)
            
            # 繪製黑色文字
            painter.setPen(QPen(QColor(0, 0, 0)))
            text_draw_rect = QRectF(
                label_screen_x - text_width / 2,
                label_screen_y - text_height / 2,
                text_width,
                text_height
            )
            painter.drawText(text_draw_rect, Qt.AlignCenter, label_text)
            
            logger.debug(
                "[TRACK_MAP] 已繪製 %s at (%.1f, %.1f)",
                sector_name,
                position_x,
                position_y,
            )
    
    def _draw_overtake_markers(self, painter: QPainter) -> None:
        """
        繪製超車事件標記（綠色圓點）
        
        在每個超車發生的 GPS 位置繪製綠色圓點標記，
        Tooltip 顯示超車詳情（超車車手、被超車手、圈數）
        """
        logger.debug("[TRACK_MAP] 準備繪製 %d 個超車標記", len(self.overtake_events))
        
        for event in self.overtake_events:
            # 獲取 GPS 座標
            x = event.get('x', 0)
            y = event.get('y', 0)
            
            # 跳過無效座標
            if x == 0 and y == 0:
                continue
            
            # 轉換到屏幕座標
            screen_x, screen_y = self.world_to_screen(x, y)
            
            # 檢查是否在視口內
            margin = 50
            if (screen_x < -margin or screen_x > self.width() + margin or
                screen_y < -margin or screen_y > self.height() + margin):
                continue
            
            # 🎨 繪製綠色圓點標記
            marker_radius = 6  # 圓點半徑（像素）
            
            # 綠色填充 (Material Green 500)
            painter.setBrush(QBrush(QColor(76, 175, 80, 200)))  # 綠色，略透明
            painter.setPen(QPen(QColor(255, 255, 255), 2))  # 白色邊框
            painter.drawEllipse(
                QPointF(screen_x, screen_y),
                marker_radius,
                marker_radius
            )
            
            logger.debug(
                "[TRACK_MAP] 繪製超車標記: %s > %s @ (%d, %d) -> screen (%d, %d)",
                event.get("overtaking_driver_tla", "?"),
                event.get("overtaken_driver_tla", "?"),
                x,
                y,
                int(screen_x),
                int(screen_y)
            )
    
    def _get_overtake_at_position(self, screen_x: int, screen_y: int) -> Optional[int]:
        """
        檢測滑鼠位置是否在超車標記附近
        
        Args:
            screen_x: 滑鼠屏幕 X 座標
            screen_y: 滑鼠屏幕 Y 座標
            
        Returns:
            超車事件索引，如果沒有懸停則返回 None
        """
        if not self.show_overtake_markers or not self.overtake_events:
            return None
        
        hover_radius = 10  # 懸停檢測半徑（像素）
        
        for i, event in enumerate(self.overtake_events):
            x = event.get('x', 0)
            y = event.get('y', 0)
            
            if x == 0 and y == 0:
                continue
            
            # 轉換到屏幕座標
            marker_screen_x, marker_screen_y = self.world_to_screen(x, y)
            
            # 計算距離
            dx = screen_x - marker_screen_x
            dy = screen_y - marker_screen_y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance <= hover_radius:
                return i
        
        return None
    
    def _format_overtake_tooltip(self, event_index: int) -> str:
        """
        格式化超車事件的 tooltip 顯示內容
        
        Args:
            event_index: 超車事件索引
            
        Returns:
            格式化的 HTML tooltip 內容
        """
        if not (0 <= event_index < len(self.overtake_events)):
            return ""
        
        event = self.overtake_events[event_index]
        
        # 提取事件資訊
        year = event.get('year', '?')
        lap = event.get('lap', '?')
        overtaking_driver = event.get('overtaking_driver_tla', '?')
        overtaken_driver = event.get('overtaken_driver_tla', '?')
        old_position = event.get('old_position', '?')
        new_position = event.get('new_position', '?')
        
        # 計算排名變化
        if isinstance(old_position, int) and isinstance(new_position, int):
            position_gain = old_position - new_position
            if position_gain > 0:
                position_change_text = f"<span style='color: #4CAF50;'>↑ {position_gain}</span>"
            elif position_gain < 0:
                position_change_text = f"<span style='color: #F44336;'>↓ {abs(position_gain)}</span>"
            else:
                position_change_text = "="
        else:
            position_change_text = "?"
        
        # 格式化位置變化
        position_text = f"P{old_position} → P{new_position} ({position_change_text})"
        
        # 構建 HTML tooltip（多國語言化）
        tooltip = f"""
        <div style='font-family: Arial; font-size: 11pt;'>
            <b style='color: #4CAF50; font-size: 12pt;'>{tr("overtake_event", "Overtake Event")}</b><br>
            <hr style='margin: 4px 0; border: none; border-top: 1px solid #ddd;'>
            <b>{tr("year", "Year")}:</b> {year}<br>
            <b>{tr("lap", "Lap")}:</b> {lap}<br>
            <b>{tr("overtaking_driver", "Overtaking Driver")}:</b> <span style='color: #2196F3; font-weight: bold;'>{overtaking_driver}</span><br>
            <b>{tr("overtaken_driver", "Overtaken Driver")}:</b> <span style='color: #FF9800;'>{overtaken_driver}</span><br>
            <b>{tr("position_change", "Position Change")}:</b> {position_text}
        </div>
        """
        
        return tooltip
    
    def _get_track_tangent_at_position(self, target_x: float, target_y: float) -> Optional[Tuple[float, float]]:
        """
        計算賽道在指定位置的切線方向
        
        Args:
            target_x: 目標位置的 X 座標（世界座標）
            target_y: 目標位置的 Y 座標（世界座標）
            
        Returns:
            (tangent_x, tangent_y): 正規化的切線向量，如果無法計算則返回 None
        """
        import math
        
        if not self.position_data or len(self.position_data) < 2:
            return None
        
        # 找到最接近目標位置的賽道點索引
        min_dist = float('inf')
        nearest_index = 0
        
        for i, pos in enumerate(self.position_data):
            track_x = pos.get("position_x", 0.0)
            track_y = pos.get("position_y", 0.0)
            dist = math.sqrt((track_x - target_x)**2 + (track_y - target_y)**2)
            
            if dist < min_dist:
                min_dist = dist
                nearest_index = i
        
        # 取前後各 5 個點計算平均切線方向（更平滑）
        window = 5
        start_idx = max(0, nearest_index - window)
        end_idx = min(len(self.position_data) - 1, nearest_index + window)
        
        if start_idx >= end_idx:
            return None
        
        # 計算從起點到終點的向量
        start_pos = self.position_data[start_idx]
        end_pos = self.position_data[end_idx]
        
        dx = end_pos.get("position_x", 0.0) - start_pos.get("position_x", 0.0)
        dy = end_pos.get("position_y", 0.0) - start_pos.get("position_y", 0.0)
        
        # 正規化
        length = math.sqrt(dx**2 + dy**2)
        if length > 0:
            dx /= length
            dy /= length
            return (dx, dy)
        
        return None

    # ------------------------------------------------------------------
    # 座標轉換
    # ------------------------------------------------------------------
    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        if not self.track_bounds:
            return int(x), int(y)

        sx = (x - self.track_bounds["x_min"]) * self.scale_factor + self.offset_x
        sy = (self.track_bounds["y_max"] - y) * self.scale_factor + self.offset_y
        return int(sx), int(sy)

    def _calculate_bounds_from_positions(self, positions: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        if not positions:
            return None
        xs = [p.get("position_x", 0.0) for p in positions]
        ys = [p.get("position_y", 0.0) for p in positions]
        return {
            "x_min": min(xs),
            "x_max": max(xs),
            "y_min": min(ys),
            "y_max": max(ys),
        }

    # ------------------------------------------------------------------
    # 互動事件
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event) -> None:
        """滑鼠移動事件 - 處理標籤拖動和懸停顯示"""
        # 🆕 處理標籤拖動（最優先）
        if self.dragging_tooltip and 0 <= self.dragging_tooltip_index < len(self.pinned_tooltips):
            # 計算新位置（滑鼠位置 - 拖動偏移量）
            new_pos = event.pos() - self.tooltip_drag_offset
            
            # 限制在視窗範圍內
            tooltip_info = self.pinned_tooltips[self.dragging_tooltip_index]
            label = tooltip_info['label']
            new_x = max(0, min(new_pos.x(), self.width() - label.width()))
            new_y = max(0, min(new_pos.y(), self.height() - label.height()))
            new_pos = QPoint(new_x, new_y)
            
            # 更新標籤位置
            label.move(new_pos)
            
            # 儲存自訂位置
            tooltip_info['custom_pos'] = new_pos
            
            # 拖動時不再執行其他邏輯
            event.accept()
            return
        
        # 如果有固定的標籤，不處理懸停（避免懸停提示干擾固定標籤）
        if self.pinned_tooltips:
            super().mouseMoveEvent(event)
            return
        
        # 🏎️ 優先檢測滑鼠是否懸停在超車標記上
        detected_overtake = self._get_overtake_at_position(event.x(), event.y())
        
        if detected_overtake is not None:
            # 懸停在超車標記上
            if detected_overtake != self.hovered_overtake_index:
                self.hovered_overtake_index = detected_overtake
                tooltip_text = self._format_overtake_tooltip(detected_overtake)
                if tooltip_text:
                    QToolTip.showText(event.globalPos(), tooltip_text, self)
            super().mouseMoveEvent(event)
            return
        else:
            # 沒有懸停在超車標記上，重置索引
            if self.hovered_overtake_index is not None:
                self.hovered_overtake_index = None
        
        # 檢測滑鼠是否懸停在彎道圓圈上
        detected_corner = self._get_corner_at_position(event.x(), event.y())
        
        if detected_corner != self.hovered_corner:
            self.hovered_corner = detected_corner
            
            if self.hovered_corner:
                # 顯示 tooltip
                tooltip_text = self._format_corner_tooltip(self.hovered_corner)
                if tooltip_text:
                    QToolTip.showText(event.globalPos(), tooltip_text, self)
            else:
                # 隱藏 tooltip
                QToolTip.hideText()
        
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event) -> None:  # noqa: D401 - Qt override
        if event.button() == Qt.LeftButton:
            # 🆕 【最優先】檢查是否點擊已固定的標籤（用於拖動）
            for i, tooltip_info in enumerate(self.pinned_tooltips):
                label = tooltip_info['label']
                # 檢查點擊位置是否在標籤範圍內
                label_rect = label.geometry()
                if label_rect.contains(event.pos()):
                    # 開始拖動此標籤
                    self.dragging_tooltip = True
                    self.dragging_tooltip_index = i
                    self.tooltip_drag_offset = event.pos() - label.pos()
                    self.setCursor(Qt.ClosedHandCursor)
                    logger.debug("[TRACK_MAP] 開始拖動標籤 #%d: %s", i, tooltip_info['corner_key'])
                    event.accept()
                    return
            
            # 檢查是否點擊彎道圓圈
            clicked_corner = self._get_corner_at_position(event.x(), event.y())
            
            if clicked_corner:
                # ✅ 新版：創建固定標籤（靜態，不重複載入）
                
                # 檢查是否已固定該彎道
                for tooltip_info in self.pinned_tooltips:
                    if tooltip_info['corner_key'] == clicked_corner:
                        logger.debug("[TRACK_MAP] 彎道 %s 的標籤已固定", clicked_corner)
                        event.accept()
                        return
                
                # 生成 HTML 內容（只生成一次）
                html_content = self._format_corner_tooltip(clicked_corner)
                if not html_content:
                    logger.warning("[TRACK_MAP] 彎道 %s 沒有旗幟數據", clicked_corner)
                    return
                
                # 獲取彎道世界座標
                corner_data = self.corner_flags[clicked_corner]
                corner_num = corner_data.get('corner_number', 0)
                corner_world_pos = None
                
                for corner in self.official_corners:
                    if corner.get('number') == corner_num:
                        corner_world_pos = (
                            corner.get('x', 0.0),
                            corner.get('y', 0.0)
                        )
                        break
                
                if not corner_world_pos:
                    logger.warning("[TRACK_MAP] 找不到彎道 %s 的座標", clicked_corner)
                    return
                
                # 計算智能偏移量
                offset = self._calculate_tooltip_offset(corner_world_pos)
                
                # 創建 QLabel 標籤
                label = CornerTooltipLabel(html_content, self)
                
                # 計算初始位置
                screen_x, screen_y = self.world_to_screen(*corner_world_pos)
                label.move(int(screen_x + offset[0]), int(screen_y + offset[1]))
                label.show()
                
                # 儲存標籤資訊
                self.pinned_tooltips.append({
                    'corner_key': clicked_corner,
                    'label': label,
                    'corner_world_pos': corner_world_pos,
                    'offset': offset,
                    'custom_pos': None  # 初始化自訂位置
                })

                logger.info("[TRACK_MAP] 已固定標籤: %s", clicked_corner)
                event.accept()
                return
            
            # 原有的點擊事件處理
            if self.position_data:
                info = {
                    "x": event.x(),
                    "y": event.y(),
                    "total_points": len(self.position_data),
                }
                self.point_clicked.emit(info)
        
        elif event.button() == Qt.RightButton:
            # 🆕 右鍵清除所有固定標籤（在空白處點擊）
            if self.pinned_tooltips:
                # 清理所有標籤
                for tooltip_info in self.pinned_tooltips:
                    tooltip_info['label'].hide()
                    tooltip_info['label'].deleteLater()
                self.pinned_tooltips.clear()
                logger.info("[TRACK_MAP] 右鍵清除所有固定標籤")
                self.update()
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """滑鼠放開事件 - 結束標籤拖動"""
        if event.button() == Qt.LeftButton:
            if self.dragging_tooltip:
                # 結束拖動
                logger.debug("[TRACK_MAP] 結束拖動標籤 (索引: %d)", self.dragging_tooltip_index)
                self.dragging_tooltip = False
                self.dragging_tooltip_index = -1
                self.tooltip_drag_offset = QPoint(0, 0)  # 重置偏移量
                self.setCursor(Qt.ArrowCursor)
                event.accept()
                return  # 重要：立即返回，不執行後續處理
        
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: D401 - Qt override
        super().resizeEvent(event)
        if self.track_bounds:
            self._pending_fit = True
        # ✅ 更新所有標籤位置
        self._update_tooltip_positions()
        self.update()

    # ------------------------------------------------------------------
    # 輔助工具
    # ------------------------------------------------------------------
    def clear_map(self) -> None:
        self.track_data = None
        self.position_data = []
        self.track_bounds = None
        self.scale_factor = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._distance_lookup = []
        self._distance_values = []
        self._clear_dynamic_marker()
        self._clear_fixed_marker()
        self.update()

    def get_track_info(self) -> Dict[str, Any]:
        return {
            "position_count": len(self.position_data),
            "track_bounds": dict(self.track_bounds) if self.track_bounds else {},
            "has_data": bool(self.position_data),
        }

    def force_rescale(self) -> None:
        if not self.track_bounds:
            return
        self._pending_fit = True
        self.fit_to_view()

    # ------------------------------------------------------------------
    # 時間軸支援
    # ------------------------------------------------------------------
    def set_time_axis_mode(self, use_time_axis: bool) -> bool:
        """
        設置是否使用時間軸模式
        
        Args:
            use_time_axis: True=使用時間軸, False=使用距離軸
            
        Returns:
            bool: 是否成功設置（如果沒有時間數據則失敗）
        """
        if use_time_axis and not self._time_available:
            logger.warning("[TRACK_MAP] 無法切換至時間軸：缺少時間數據")
            return False
        
        if self._use_time_axis != use_time_axis:
            self._use_time_axis = use_time_axis
            logger.info(
                "[TRACK_MAP] 時間軸模式: %s",
                "啟用" if use_time_axis else "停用（使用距離軸）",
            )
            
            # 清除現有標記（避免錯誤的單位混淆）
            self._clear_dynamic_marker(update_view=False)
            self._clear_fixed_marker(update_view=False)
            self.update()
        
        return True
    
    def is_time_axis_mode(self) -> bool:
        """返回當前是否使用時間軸模式"""
        return self._use_time_axis
    
    def is_time_axis_available(self) -> bool:
        """返回是否有時間數據可用"""
        return self._time_available

    # ------------------------------------------------------------------
    # 連動整合
    # ------------------------------------------------------------------
    def _register_linkage(self) -> None:
        if linkage_manager is not None and not self._linkage_registered:
            try:
                linkage_manager.register_module(self, "track_map")
                self._master_linkage_enabled = linkage_manager.is_master_linkage_enabled()
                
                # ✅ 同步時間軸模式狀態
                current_time_axis_mode = linkage_manager.is_time_axis_mode()
                if current_time_axis_mode and self._time_available:
                    self._use_time_axis = True
                    logger.info("[TRACK_MAP] 已同步時間軸模式: 啟用")
                elif current_time_axis_mode and not self._time_available:
                    logger.warning("[TRACK_MAP] LinkageManager 啟用時間軸，但本模組缺少時間數據")
                
                self._linkage_registered = True
                logger.info("[TRACK_MAP] 已註冊至 linkage_manager，主連動狀態: %s", self._master_linkage_enabled)
            except Exception as exc:
                logger.exception("[TRACK_MAP] linkage 註冊失敗")

    def _unregister_linkage(self) -> None:
        if linkage_manager is not None and self._linkage_registered:
            try:
                linkage_manager.unregister_module(self)
                logger.info("[TRACK_MAP] 已自 linkage_manager 解除註冊")
            finally:
                self._linkage_registered = False

    def closeEvent(self, event) -> None:  # noqa: D401 - Qt override
        # ✅ 清理所有標籤
        for tooltip_info in self.pinned_tooltips:
            tooltip_info['label'].deleteLater()
        self.pinned_tooltips.clear()
        
        self._unregister_linkage()
        super().closeEvent(event)

    # linkage manager 會呼叫 set_master_linkage_enabled 或 on_master_linkage_changed
    def set_master_linkage_enabled(self, enabled: bool) -> None:
        self._master_linkage_enabled = bool(enabled)
        if not self._master_linkage_enabled:
            self._clear_dynamic_marker(update_view=False)
            self._clear_fixed_marker(update_view=False)
        self.update()

    def on_master_linkage_changed(self, enabled: bool) -> None:
        self.set_master_linkage_enabled(enabled)

    # linkage signals -------------------------------------------------
    def on_x_linkage_received(self, distance_or_time_value: float, y_relative: float) -> None:
        """
        接收連動信號（支援距離或時間值）
        
        Args:
            distance_or_time_value: 距離值（公尺）或時間值（秒），根據當前模式自動判斷
            y_relative: Y軸相對位置（0.0 ~ 1.0）
        """
        if not self._master_linkage_enabled or not self._linkage_enabled:
            return
        
        self._last_linkage_relative_y = y_relative
        
        # 根據當前模式選擇使用距離或時間查找
        if self._use_time_axis and self._time_available:
            # 時間軸模式：將時間值轉換為位置
            self._update_dynamic_marker_by_time(distance_or_time_value)
        else:
            # 距離軸模式：直接使用距離值
            self._update_dynamic_marker(distance_or_time_value)

    def on_x_linkage_clear(self) -> None:
        if not self._linkage_enabled:
            return
        self._clear_dynamic_marker()

    def on_click_linkage_received(self, distance_or_time_value: float) -> None:
        """
        接收點擊連動信號（支援距離或時間值）
        
        Args:
            distance_or_time_value: 距離值（公尺）或時間值（秒），根據當前模式自動判斷
        """
        if not self._master_linkage_enabled or not self._linkage_enabled:
            return
        
        # 根據當前模式選擇使用距離或時間查找
        if self._use_time_axis and self._time_available:
            self._update_fixed_marker_by_time(distance_or_time_value)
        else:
            self._update_fixed_marker(distance_or_time_value)

    def on_click_linkage_clear(self) -> None:
        if not self._linkage_enabled:
            return
        self._clear_fixed_marker()

    def set_linkage_enabled(self, enabled: bool) -> None:
        new_state = bool(enabled)
        if self._linkage_enabled == new_state:
            return

        self._linkage_enabled = new_state

        if not new_state:
            # 關閉時清除現有標記但保留可見性設定
            self._clear_dynamic_marker(update_view=False)
            self._clear_fixed_marker(update_view=False)
        # 重新繪製以反映狀態變化
        self.update()

    def is_linkage_enabled(self) -> bool:
        return self._linkage_enabled

    # ------------------------------------------------------------------
    # 標記狀態與繪製
    # ------------------------------------------------------------------
    def set_dynamic_marker_visibility(self, visible: bool) -> None:
        self._dynamic_marker_visible = bool(visible)
        self.update()

    def set_fixed_marker_visibility(self, visible: bool) -> None:
        self._fixed_marker_visible = bool(visible)
        self.update()

    def get_marker_state(self) -> Dict[str, Any]:
        return {
            "dynamic_distance": self._dynamic_marker_distance,
            "dynamic_world": self._dynamic_marker_world,
            "fixed_distance": self._fixed_marker_distance,
            "fixed_world": self._fixed_marker_world,
            "dynamic_visible": self._dynamic_marker_visible,
            "fixed_visible": self._fixed_marker_visible,
            "master_enabled": self._master_linkage_enabled,
        }

    def _draw_markers(self, painter: QPainter) -> None:
        if not self.track_bounds:
            return

        if (
            self._dynamic_marker_world
            and self._master_linkage_enabled
            and self._dynamic_marker_visible
        ):
            x, y = self.world_to_screen(*self._dynamic_marker_world)
            painter.setBrush(QBrush(QColor(0, 180, 0, 220)))
            painter.setPen(QPen(QColor(0, 120, 0), 2))
            painter.drawEllipse(QPointF(x, y), 6, 6)

        if (
            self._fixed_marker_world
            and self._master_linkage_enabled
            and self._fixed_marker_visible
        ):
            x, y = self.world_to_screen(*self._fixed_marker_world)
            painter.setBrush(QBrush(QColor(220, 60, 60, 230)))
            painter.setPen(QPen(QColor(160, 30, 30), 2))
            painter.drawEllipse(QPointF(x, y), 7, 7)

    def _update_dynamic_marker(self, distance_value: float) -> None:
        world_pos = self._find_world_coordinate(distance_value)
        if world_pos:
            self._dynamic_marker_distance = float(distance_value)
            self._dynamic_marker_world = world_pos
        else:
            self._dynamic_marker_distance = None
            self._dynamic_marker_world = None
        self.update()

    def _update_fixed_marker(self, distance_value: float) -> None:
        world_pos = self._find_world_coordinate(distance_value)
        if world_pos:
            self._fixed_marker_distance = float(distance_value)
            self._fixed_marker_world = world_pos
        else:
            self._fixed_marker_distance = None
            self._fixed_marker_world = None
        self.update()

    def _clear_dynamic_marker(self, update_view: bool = True) -> None:
        self._dynamic_marker_distance = None
        self._dynamic_marker_world = None
        if update_view:
            self.update()

    def _clear_fixed_marker(self, update_view: bool = True) -> None:
        self._fixed_marker_distance = None
        self._fixed_marker_world = None
        if update_view:
            self.update()

    def _update_dynamic_marker_by_time(self, time_value: float) -> None:
        """基於時間值更新動態標記"""
        world_pos = self._find_world_coordinate_by_time(time_value)
        if world_pos:
            self._dynamic_marker_distance = float(time_value)  # 在時間模式下存儲時間值
            self._dynamic_marker_world = world_pos
        else:
            self._dynamic_marker_distance = None
            self._dynamic_marker_world = None
        self.update()

    def _update_fixed_marker_by_time(self, time_value: float) -> None:
        """基於時間值更新固定標記"""
        world_pos = self._find_world_coordinate_by_time(time_value)
        if world_pos:
            self._fixed_marker_distance = float(time_value)  # 在時間模式下存儲時間值
            self._fixed_marker_world = world_pos
        else:
            self._fixed_marker_distance = None
            self._fixed_marker_world = None
        self.update()

    # ------------------------------------------------------------------
    # 距離索引與座標計算
    # ------------------------------------------------------------------
    def _build_distance_lookup(self) -> None:
        """建立距離和時間的位置查找表"""
        distance_entries: List[Tuple[float, float, float]] = []
        time_entries: List[Tuple[float, float, float]] = []
        last_distance: Optional[float] = None
        last_time: Optional[float] = None
        skipped = 0
        has_time_data = False

        for record in self.position_data:
            distance = self._extract_distance(record)
            time_seconds = record.get("time_seconds")
            
            if distance is None:
                skipped += 1
                continue

            x = record.get("position_x")
            y = record.get("position_y")
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                skipped += 1
                continue

            # 距離查找表
            if last_distance is not None and distance < last_distance:
                distance = last_distance
            distance_entries.append((float(distance), float(x), float(y)))
            last_distance = distance
            
            # 時間查找表（如果有時間數據）
            if isinstance(time_seconds, (int, float)):
                time = float(time_seconds)
                if last_time is not None and time < last_time:
                    time = last_time
                time_entries.append((time, float(x), float(y)))
                last_time = time
                has_time_data = True

        # 處理距離查找表
        distance_entries.sort(key=lambda item: item[0])
        if distance_entries:
            self._raw_distance_range = (distance_entries[0][0], distance_entries[-1][0])
        else:
            self._raw_distance_range = (0.0, 0.0)

        self._distance_scale = self._determine_distance_scale(distance_entries)
        if self._distance_scale != 1.0:
            distance_entries = [(item[0] * self._distance_scale, item[1], item[2]) for item in distance_entries]

        self._distance_lookup = distance_entries
        self._distance_values = [item[0] for item in distance_entries]
        
        # 處理時間查找表
        time_entries.sort(key=lambda item: item[0])
        self._time_lookup = time_entries
        self._time_values = [item[0] for item in time_entries]
        self._time_available = has_time_data and len(time_entries) > 0

        # 日誌輸出
        if skipped and distance_entries:
            logger.info(
                "[TRACK_MAP] 索引建立完成: %d 筆距離資料，忽略 %d 筆缺失或不合法資料",
                len(distance_entries),
                skipped,
            )
        elif not distance_entries:
            logger.warning("[TRACK_MAP] 無法建立距離索引：缺少 distance 資料")
        else:
            logger.info("[TRACK_MAP] 建立距離索引: %d 筆有效資料", len(distance_entries))
            
        if self._time_available:
            logger.info("[TRACK_MAP] 時間軸支援: 建立 %d 筆時間索引", len(time_entries))
            logger.debug(
                "[TRACK_MAP] 時間範圍: %.2fs ~ %.2fs",
                self._time_values[0],
                self._time_values[-1],
            )
        else:
            logger.warning("[TRACK_MAP] 時間軸不可用：缺少 time_seconds 資料")
            
        if distance_entries and self._distance_scale != 1.0:
            logger.info(
                "[TRACK_MAP] 自動距離縮放：原始最大距離 %.2f → 正規化 %.2f 公尺",
                self._raw_distance_range[1],
                self._distance_values[-1],
            )

    def _extract_distance(self, record: Dict[str, Any]) -> Optional[float]:
        for key in (
            "distance_m",
            "distance",
            "lap_distance",
            "path_distance",
            "s",
        ):
            value = record.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    def _determine_distance_scale(self, entries: List[Tuple[float, float, float]]) -> float:
        if not entries:
            return 1.0

        max_distance = entries[-1][0]
        if max_distance <= 0:
            return 1.0

        scale = 1.0
        scaled_max = max_distance
        while scaled_max > 10000:
            scale *= 0.1
            scaled_max *= 0.1

        # Avoid tiny floating noise; treat near-1 as 1
        if abs(scale - 1.0) < 1e-6:
            return 1.0
        return scale

    def _normalize_distance(self, raw_distance: Optional[float]) -> Optional[float]:
        if raw_distance is None:
            return None
        return raw_distance * self._distance_scale

    def _find_world_coordinate(self, distance_value: float) -> Optional[Tuple[float, float]]:
        if not self._distance_lookup:
            return None

        distance = float(distance_value)
        idx = bisect_left(self._distance_values, distance)

        if idx <= 0:
            base = self._distance_lookup[0]
            return base[1], base[2]
        if idx >= len(self._distance_lookup):
            base = self._distance_lookup[-1]
            return base[1], base[2]

        prev_entry = self._distance_lookup[idx - 1]
        next_entry = self._distance_lookup[idx]
        prev_dist, prev_x, prev_y = prev_entry
        next_dist, next_x, next_y = next_entry

        if next_dist == prev_dist:
            return prev_x, prev_y

        ratio = (distance - prev_dist) / (next_dist - prev_dist)
        ratio = max(0.0, min(1.0, ratio))
        interp_x = prev_x + (next_x - prev_x) * ratio
        interp_y = prev_y + (next_y - prev_y) * ratio
        return interp_x, interp_y

    def _find_world_coordinate_by_time(self, time_value: float) -> Optional[Tuple[float, float]]:
        """基於時間值查找世界座標（線性插值）"""
        if not self._time_lookup or not self._time_available:
            return None

        time = float(time_value)
        idx = bisect_left(self._time_values, time)

        if idx <= 0:
            base = self._time_lookup[0]
            return base[1], base[2]
        if idx >= len(self._time_lookup):
            base = self._time_lookup[-1]
            return base[1], base[2]

        prev_entry = self._time_lookup[idx - 1]
        next_entry = self._time_lookup[idx]
        prev_time, prev_x, prev_y = prev_entry
        next_time, next_x, next_y = next_entry

        if next_time == prev_time:
            return prev_x, prev_y

        ratio = (time - prev_time) / (next_time - prev_time)
        ratio = max(0.0, min(1.0, ratio))
        interp_x = prev_x + (next_x - prev_x) * ratio
        interp_y = prev_y + (next_y - prev_y) * ratio
        return interp_x, interp_y

    def get_distance_scale(self) -> float:
        return self._distance_scale
    
    def _get_corner_at_position(self, x: int, y: int) -> Optional[str]:
        """
        檢測滑鼠位置是否在彎道圓圈上
        
        Args:
            x: 滑鼠 X 座標（螢幕座標）
            y: 滑鼠 Y 座標（螢幕座標）
            
        Returns:
            彎道 key（例如 "T7"）或 None
        """
        if not self.official_corners or not self.track_bounds:
            return None
        
        # 彎道圓圈的半徑（與繪製時一致）
        marker_radius = 12
        hit_tolerance = marker_radius + 5  # 增加5像素容錯範圍
        
        closest_corner = None
        closest_distance = float('inf')
        
        for corner in self.official_corners:
            corner_num = corner.get('number', corner.get('Number', 0))
            corner_x = corner.get('x', corner.get('X', 0.0))
            corner_y = corner.get('y', corner.get('Y', 0.0))
            
            if corner_x == 0.0 and corner_y == 0.0:
                continue
            
            # 計算偏移（與繪製時一致）
            offset_x, offset_y = self._calculate_corner_offset(corner_x, corner_y, 20)
            # 轉換世界座標到螢幕座標（使用與繪製相同的方法）
            screen_x, screen_y = self.world_to_screen(offset_x, offset_y)
            
            # 計算距離
            dx = x - screen_x
            dy = y - screen_y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < closest_distance:
                closest_distance = distance
                closest_corner = (corner_num, distance)
            
            if distance <= hit_tolerance:
                corner_key = f"T{corner_num}"
                # 檢查該彎道是否有旗幟數據（只有有顏色的彎道才顯示 tooltip）
                if corner_key in self.corner_flags:
                    corner_data = self.corner_flags[corner_key]
                    yearly_breakdown = corner_data.get('yearly_breakdown', {})
                    if yearly_breakdown:  # 有歷史數據才返回
                        return corner_key
        
        return None
    
    def _format_corner_tooltip(self, corner_key: str) -> str:
        """
        格式化彎道 tooltip 文字
        
        Args:
            corner_key: 彎道 key（例如 "T7"）
            
        Returns:
            格式化的 HTML 文字
        """
        if corner_key not in self.corner_flags:
            return ""
        
        corner_data = self.corner_flags[corner_key]
        corner_num = corner_data.get('corner_number', '')
        yearly_breakdown = corner_data.get('yearly_breakdown', {})
        
        if not yearly_breakdown:
            return ""
        
        # 構建 tooltip HTML
        html_lines = [
            f"<b style='font-size:12pt;'>Turn {corner_num}</b>",
            "<hr style='margin:4px 0;'>",
        ]
        
        # 按年份排序
        sorted_years = sorted(yearly_breakdown.keys(), reverse=True)
        
        for year in sorted_years:
            year_data = yearly_breakdown[year]
            yellow_count = year_data.get('yellow', 0)
            double_yellow_count = year_data.get('double_yellow', 0)
            safety_car_count = year_data.get('safety_car', 0)
            messages = year_data.get('messages', [])  # ✅ 獲取詳細訊息
            
            # 只顯示有事件的年份
            if yellow_count == 0 and double_yellow_count == 0 and safety_car_count == 0:
                continue
            
            html_lines.append(f"<b>{year}:</b>")
            
            # ✅ 按 flag_type 分組圈數
            yellow_laps = []
            double_yellow_laps = []
            safety_car_laps = []
            
            for msg in messages:
                lap = msg.get('lap', 0)
                flag_type = msg.get('flag_type', '')
                
                if lap > 0:
                    if flag_type == 'yellow':
                        yellow_laps.append(lap)
                    elif flag_type == 'double_yellow':
                        double_yellow_laps.append(lap)
                    elif flag_type == 'safety_car':
                        safety_car_laps.append(lap)
            
            # 顯示每種旗幟及其圈數
            if yellow_count > 0:
                if yellow_count >= 1:
                    html_lines.append(f"<span style='color:#FFD700;'>●</span> Yellow Flag")
                else:
                    html_lines.append(f"<span style='color:#FFD700;'>●</span> Yellow Flag (partial)")
                
                # 顯示圈數
                for lap in sorted(yellow_laps):
                    html_lines.append(f"<span style='font-size:9pt;color:#666;'>  → Lap {lap}</span>")
                    
            if double_yellow_count > 0:
                if double_yellow_count >= 1:
                    html_lines.append(f"<span style='color:#FFA500;'>●</span> Double Yellow")
                else:
                    html_lines.append(f"<span style='color:#FFA500;'>●</span> Double Yellow (partial)")
                
                # 顯示圈數
                for lap in sorted(double_yellow_laps):
                    html_lines.append(f"<span style='font-size:9pt;color:#666;'>  → Lap {lap}</span>")
                    
            if safety_car_count > 0:
                if safety_car_count >= 1:
                    html_lines.append(f"<span style='color:#C8A2C8;'>●</span> Safety Car")
                else:
                    html_lines.append(f"<span style='color:#C8A2C8;'>●</span> Safety Car (partial)")
                
                # 顯示圈數
                for lap in sorted(safety_car_laps):
                    html_lines.append(f"<span style='font-size:9pt;color:#666;'>  → Lap {lap}</span>")
            
            html_lines.append("")  # 空行
        
        # 移除最後的空行
        if html_lines and html_lines[-1] == "":
            html_lines.pop()
        
        return "<br>".join(html_lines)
    
    def _calculate_tooltip_offset(self, corner_world_pos: Tuple[float, float]) -> Tuple[int, int]:
        """
        根據彎道在地圖中的位置，智能計算標籤偏移量
        
        Args:
            corner_world_pos: 彎道的世界座標 (x, y)
            
        Returns:
            (offset_x, offset_y): 相對於彎道圓圈的像素偏移量
        """
        if not self.track_bounds:
            # 無法計算，使用預設偏移
            return (15, -30)
        
        # 計算賽道中心點
        center_x = (self.track_bounds["x_min"] + self.track_bounds["x_max"]) / 2.0
        center_y = (self.track_bounds["y_min"] + self.track_bounds["y_max"]) / 2.0
        
        corner_x, corner_y = corner_world_pos
        
        # 根據彎道相對於中心的位置，決定標籤方向
        # 水平方向
        if corner_x > center_x:
            offset_x = -15  # 彎道在右側 → 標籤在左側
        else:
            offset_x = 15   # 彎道在左側 → 標籤在右側
        
        # 垂直方向
        if corner_y > center_y:
            offset_y = -40  # 彎道在上方 → 標籤在下方
        else:
            offset_y = -40  # 彎道在下方 → 標籤在上方（保持在上方以避免遮擋）
        
        return (offset_x, offset_y)
    
    def _update_tooltip_positions(self):
        """更新所有固定標籤的位置（當視窗移動/縮放時調用）"""
        for tooltip_info in self.pinned_tooltips:
            label = tooltip_info['label']
            
            # 🆕 如果有自訂位置（拖動過），使用自訂位置
            custom_pos = tooltip_info.get('custom_pos')
            if custom_pos:
                # 使用拖動後的自訂位置（不跟隨彎道）
                label.move(custom_pos)
            else:
                # 使用預設位置（跟隨彎道）
                corner_world_pos = tooltip_info['corner_world_pos']
                offset = tooltip_info['offset']
                
                # 世界座標 → 螢幕座標
                screen_x, screen_y = self.world_to_screen(*corner_world_pos)
                
                # 應用偏移量
                final_x = int(screen_x + offset[0])
                final_y = int(screen_y + offset[1])
                
                # 移動標籤
                label.move(final_x, final_y)
            
            # 確保標籤可見
            label.show()
    
    def remove_tooltip_label(self, label: CornerTooltipLabel):
        """
        移除指定的標籤（由 CornerTooltipLabel 的右鍵事件調用）
        
        Args:
            label: 要移除的標籤實例
        """
        # 找到對應的 tooltip_info
        for tooltip_info in self.pinned_tooltips:
            if tooltip_info['label'] == label:
                label.hide()
                label.deleteLater()
                self.pinned_tooltips.remove(tooltip_info)
                logger.info("[TRACK_MAP] 已移除標籤: %s", tooltip_info['corner_key'])
                break


__all__ = ["TrackMapWidget"]
