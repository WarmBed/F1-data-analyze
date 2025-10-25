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

from PyQt5.QtCore import QPointF, Qt, pyqtSignal, QSize
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt5.QtWidgets import QWidget

# 連動管理器 (Lap Analysis linkage)
try:
    from modules.gui.lap_analysis.linkage import linkage_manager
except ImportError:
    linkage_manager = None


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

        self._grid_spacing: float = 500.0  # 公尺
        self._max_grid_lines: int = 12
        
        # FastF1 官方彎道數據
        self.official_corners: List[Dict[str, Any]] = []

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
            print(f"[TRACK_MAP] ==================== load_track_data 開始 ====================")
            print(f"[TRACK_MAP] track_data keys: {list(track_data.keys())}")
            
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
            print(f"[TRACK_MAP] ==================== 載入 official_corners ====================")
            official_corners_data = track_data.get("official_corners", {})
            print(f"[TRACK_MAP] official_corners_data 類型: {type(official_corners_data)}")
            print(f"[TRACK_MAP] official_corners_data 內容: {official_corners_data if isinstance(official_corners_data, dict) else 'NOT A DICT'}")
            
            if official_corners_data.get("available") and official_corners_data.get("corners"):
                self.official_corners = official_corners_data.get("corners", [])
                print(f"[TRACK_MAP] ✅ 成功載入 {len(self.official_corners)} 個官方彎道")
                if self.official_corners:
                    first = self.official_corners[0]
                    print(f"[TRACK_MAP]    第一個彎道: number={first.get('number')}, x={first.get('x')}, y={first.get('y')}")
            else:
                self.official_corners = []
                print(f"[TRACK_MAP] ❌ 未載入官方彎道")
                print(f"[TRACK_MAP]    available: {official_corners_data.get('available')}")
                print(f"[TRACK_MAP]    corners 存在: {'corners' in official_corners_data}")
                print(f"[TRACK_MAP]    corners 數量: {len(official_corners_data.get('corners', []))}")
            
            print(f"[TRACK_MAP] self.official_corners 最終狀態: 長度={len(self.official_corners)}")
            print(f"[TRACK_MAP] self.show_official_corners 狀態: {self.show_official_corners}")
            
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
            print(f"[TRACK_MAP] Data loaded: {track_name}, points={len(self.position_data)} bounds={self.track_bounds}")
            return bool(self.position_data)
        except Exception as exc:
            print(f"[TRACK_MAP] Failed to load data: {exc}")
            return False

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

        painter.setPen(QPen(QColor(40, 40, 200), 4))
        painter.drawPath(path)

        painter.setPen(QPen(QColor(120, 120, 255), 1))
        painter.drawPath(path)

        if self.show_distance_markers:
            self._draw_distance_markers(painter, points)
        
        # 繪製 FastF1 官方彎道標記
        if self.show_official_corners and self.official_corners:
            print(f"[TRACK_MAP] paintEvent: 準備繪製 {len(self.official_corners)} 個彎道")
            self._draw_official_corners(painter)
        else:
            if not self.show_official_corners:
                print(f"[TRACK_MAP] paintEvent: show_official_corners={self.show_official_corners} (未啟用)")
            if not self.official_corners:
                print(f"[TRACK_MAP] paintEvent: official_corners 為空 (長度={len(self.official_corners)})")

        # 在路徑繪製後呈現同步標記
        self._draw_markers(painter)

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
        """繪製 FastF1 官方彎道標記 - 白底黑字，智能偏移避免與賽道重疊"""
        print(f"[TRACK_MAP] _draw_official_corners: 開始繪製")
        print(f"[TRACK_MAP]    self.official_corners 長度: {len(self.official_corners)}")
        
        if not self.official_corners:
            print(f"[TRACK_MAP] _draw_official_corners: official_corners 為空，退出")
            return
        
        print(f"[TRACK_MAP] _draw_official_corners: 準備繪製 {len(self.official_corners)} 個彎道")
        
        # 設定彎道標記樣式 - 白底黑字
        bg_color = QColor(255, 255, 255, 240)  # 半透明白色背景
        border_color = QColor(0, 0, 0)  # 黑色邊框
        text_color = QColor(0, 0, 0)  # 黑色文字
        
        bg_brush = QBrush(bg_color)
        border_pen = QPen(border_color, 2)
        text_pen = QPen(text_color)
        text_font = QFont("Arial", 8, QFont.Bold)
        
        painter.setFont(text_font)
        
        marker_radius = 11
        offset_distance = 20  # 基礎偏移距離
        
        for corner in self.official_corners:
            # 獲取彎道位置 (FastF1 的 X, Y 座標)
            corner_x = corner.get("x", 0.0)
            corner_y = corner.get("y", 0.0)
            corner_num = corner.get("number", 0)
            
            # 計算智能偏移：找到最近的賽道點，然後向外偏移
            offset_x, offset_y = self._calculate_corner_offset(
                corner_x, corner_y, offset_distance
            )
            
            # 轉換為螢幕座標
            screen_x, screen_y = self.world_to_screen(offset_x, offset_y)
            
            # 繪製白色背景圓圈（圓圈中心在 screen_x, screen_y）
            painter.setPen(border_pen)
            painter.setBrush(bg_brush)
            painter.drawEllipse(screen_x - marker_radius, screen_y - marker_radius, 
                              marker_radius * 2, marker_radius * 2)
            
            # 繪製黑色彎道編號（使用 QRect 對齊方式精確居中）
            painter.setPen(text_pen)
            text = str(corner_num)
            
            # 使用 QRect 來定義文字繪製區域（與圓圈大小相同）
            from PyQt5.QtCore import QRect
            text_rect = QRect(
                screen_x - marker_radius,
                screen_y - marker_radius,
                marker_radius * 2,
                marker_radius * 2
            )
            
            # 使用對齊參數讓 Qt 自動居中文字
            painter.drawText(text_rect, Qt.AlignCenter, text)
    
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
    def mousePressEvent(self, event) -> None:  # noqa: D401 - Qt override
        if event.button() == Qt.LeftButton and self.position_data:
            info = {
                "x": event.x(),
                "y": event.y(),
                "total_points": len(self.position_data),
            }
            self.point_clicked.emit(info)
        super().mousePressEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: D401 - Qt override
        super().resizeEvent(event)
        if self.track_bounds:
            self._pending_fit = True
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
            print("[TRACK_MAP] ⚠️ 無法切換至時間軸：缺少時間數據")
            return False
        
        if self._use_time_axis != use_time_axis:
            self._use_time_axis = use_time_axis
            print(f"[TRACK_MAP] 🕒 時間軸模式: {'啟用' if use_time_axis else '停用（使用距離軸）'}")
            
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
                    print(f"[TRACK_MAP] 🕒 已同步時間軸模式: 啟用")
                elif current_time_axis_mode and not self._time_available:
                    print(f"[TRACK_MAP] ⚠️ LinkageManager 啟用時間軸，但本模組缺少時間數據")
                
                self._linkage_registered = True
                print("[TRACK_MAP] 已註冊至 linkage_manager，主連動狀態:", self._master_linkage_enabled)
            except Exception as exc:
                print(f"[TRACK_MAP] linkage 註冊失敗: {exc}")

    def _unregister_linkage(self) -> None:
        if linkage_manager is not None and self._linkage_registered:
            try:
                linkage_manager.unregister_module(self)
                print("[TRACK_MAP] 已自 linkage_manager 解除註冊")
            finally:
                self._linkage_registered = False

    def closeEvent(self, event) -> None:  # noqa: D401 - Qt override
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
            print(f"[TRACK_MAP] 索引建立完成: {len(distance_entries)} 筆距離資料，忽略 {skipped} 筆缺失或不合法資料")
        elif not distance_entries:
            print("[TRACK_MAP] ⚠️ 無法建立距離索引：缺少 distance 資料")
        else:
            print(f"[TRACK_MAP] 建立距離索引: {len(distance_entries)} 筆有效資料")
            
        if self._time_available:
            print(f"[TRACK_MAP] ✅ 時間軸支援: 建立 {len(time_entries)} 筆時間索引")
            print(f"[TRACK_MAP]    時間範圍: {self._time_values[0]:.2f}s ~ {self._time_values[-1]:.2f}s")
        else:
            print("[TRACK_MAP] ⚠️ 時間軸不可用：缺少 time_seconds 資料")
            
        if distance_entries and self._distance_scale != 1.0:
            print(
                "[TRACK_MAP] ⚙️ 自動距離縮放：原始最大距離 "
                f"{self._raw_distance_range[1]:.2f} → 正規化 {self._distance_values[-1]:.2f} 公尺"
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


__all__ = ["TrackMapWidget"]
