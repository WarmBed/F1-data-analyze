r"""
Live Timing Throttle Trace Module
==============================

即時油門追蹤圖，顯示車手油門開度 vs 距離曲線。
使用 PyQt5 原生繪圖 (QPainter) 實現，與 Lap Analysis Throttle Analysis 風格一致。

功能：
- X 軸：距離 (m)，含彎道標記 (T1, T2, ...)
- 左 Y 軸：油門開度 (%)
- 右 Y 軸：Gap 距離差 (m)
- 支援多車手比較
- 右鍵選單切換顯示選項

Author: F1T Team
Date: 2025-12-11
"""

import math
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu, QAction,
    QActionGroup, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint, QPointF, QObject
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath, QLinearGradient

from ..core.base_live_mdi import BaseLiveTimingMDI
from ..core.global_sync_signal import get_global_sync_signal
from ..core.hover_tooltip_mixin import HoverTooltipMixin, HoverInfo, HoverDataPoint

from core.logger import get_logger
logger = get_logger(__name__)


logger = get_logger("live_timing.throttle_trace", component="gui")


# 預設顏色
COLOR_DELTA_POSITIVE = '#FF6B6B'  # 落後 - 紅色
COLOR_DELTA_NEGATIVE = '#4ECDC4'  # 領先 - 青色
COLOR_DELTA_NEUTRAL = '#888888'   # 中性 - 灰色
COLOR_CORNER_MARKER = '#90EE90'   # 彎道標記 - 淺綠
COLOR_BACKGROUND = '#1a1a1a'      # 深色背景
COLOR_CHART_BG = '#242424'        # 圖表區域背景
COLOR_GRID = '#3a3a3a'            # 網格線
COLOR_AXIS = '#666666'            # 軸線
COLOR_TEXT = '#CCCCCC'            # 文字顏色


@dataclass
class LapThrottleData:
    """單圈速度資料"""
    driver_num: str
    lap_number: int
    distances: List[float] = field(default_factory=list)  # 距離點 (m)
    throttles: List[float] = field(default_factory=list)      # 油門開度點 (%)
    timestamps: List[float] = field(default_factory=list)  # 時間點 (秒)
    lap_time: Optional[float] = None  # 完成圈時間
    is_complete: bool = False
    
    def add_point(self, distance: float, throttle: float, timestamp: float):
        """添加數據點"""
        self.distances.append(distance)
        self.throttles.append(throttle)
        self.timestamps.append(timestamp)
    
    def get_time_at_distance(self, target_distance: float) -> Optional[float]:
        """根據距離插值獲取時間"""
        if not self.distances or not self.timestamps:
            return None
        
        # 二分查找最近的距離點
        for i in range(len(self.distances) - 1):
            if self.distances[i] <= target_distance <= self.distances[i + 1]:
                # 線性插值
                ratio = (target_distance - self.distances[i]) / (self.distances[i + 1] - self.distances[i])
                return self.timestamps[i] + ratio * (self.timestamps[i + 1] - self.timestamps[i])
        
        # 超出範圍
        if target_distance <= self.distances[0]:
            return self.timestamps[0]
        if target_distance >= self.distances[-1]:
            return self.timestamps[-1]
        
        return None
    
    def get_distance_at_time(self, target_time: float) -> Optional[float]:
        """根據時間插值獲取距離"""
        if not self.distances or not self.timestamps:
            return None
        
        # 查找時間範圍
        for i in range(len(self.timestamps) - 1):
            if self.timestamps[i] <= target_time <= self.timestamps[i + 1]:
                # 線性插值
                t_range = self.timestamps[i + 1] - self.timestamps[i]
                if t_range > 0:
                    ratio = (target_time - self.timestamps[i]) / t_range
                    return self.distances[i] + ratio * (self.distances[i + 1] - self.distances[i])
        
        # 超出範圍
        if target_time <= self.timestamps[0]:
            return self.distances[0]
        if target_time >= self.timestamps[-1]:
            return self.distances[-1]
        
        return None


class ThrottleTraceWidget(HoverTooltipMixin, QWidget):
    """
    油門追蹤圖表 Widget - 使用 PyQt5 原生繪圖
    
    顯示：
    - 主車手當前圈油門曲線
    - 主車手最速圈油門曲線 (可選)
    - 對比車手當前圈油門曲線 (可選)
    - 對比車手最速圈油門曲線 (可選)
    - Gap 距離差曲線 (右 Y 軸)
    - 彎道標記 (X 軸)
    """
    
    # 信號
    driver_change_requested = pyqtSignal(str)  # 請求切換車手
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設置深色背景
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        self.setMinimumHeight(200)
        
        # ===== 繪圖參數 =====
        self.margin_left = 60
        self.margin_right = 60
        self.margin_top = 35
        self.margin_bottom = 35
        
        # ===== 數據儲存 =====
        # 主車手資料
        self._primary_driver: Optional[str] = None
        self._primary_current_lap: Optional[LapThrottleData] = None
        self._primary_best_lap: Optional[LapThrottleData] = None
        
        # 對比車手資料
        self._compare_driver: Optional[str] = None
        self._compare_current_lap: Optional[LapThrottleData] = None
        self._compare_best_lap: Optional[LapThrottleData] = None
        
        # 所有車手的最速圈快取 {driver_num: LapThrottleData}
        self._all_best_laps: Dict[str, LapThrottleData] = {}
        
        # 所有車手的當前圈資料 {driver_num: LapThrottleData}
        self._all_current_laps: Dict[str, LapThrottleData] = {}
        
        # 車手資訊 {driver_num: {'tla': str, 'team_color': str, ...}}
        self._driver_info: Dict[str, Dict[str, Any]] = {}
        
        # 賽道資訊
        self._track_length: float = 5000.0  # 預設賽道長度
        self._corners: List[Dict[str, Any]] = []  # 彎道資料
        
        # ===== 顯示選項 =====
        self._show_primary_current = True
        self._show_primary_best = False  # 關閉 Best 曲線顯示
        self._show_compare_current = False
        self._show_compare_best = False
        self._show_delta = True
        self._show_corners = True  # 顯示彎道標記
        self._show_gap = True  # 顯示 Gap 填充
        
        # ===== 數據範圍 =====
        self.min_distance = 0
        self.max_distance = 5000
        self.min_throttle = 0
        self.max_throttle = 100
        self.min_gap = -500
        self.max_gap = 500
        
        # Delta 參考來源: 'compare_current' (與對比車手比較)
        self._delta_reference = 'compare_current'
        
        # 圈內累積距離追蹤 {driver_num: {'distance': float, 'last_timestamp': float, 'last_lap': int}}
        self._distance_tracker: Dict[str, Dict[str, Any]] = {}
        
        # 即時位置追蹤 {driver_num: {'lap': int, 'lap_distance': float, 'total_distance': float}}
        self._realtime_positions: Dict[str, Dict[str, float]] = {}
        
        # Gap 歷史記錄 (用於繪製曲線)
        self._gap_history_distances: List[float] = []  # X 軸: Primary 的圈內距離
        self._gap_history_values: List[float] = []     # Y 軸: Gap 值 (m)
        
        # 滑鼠追蹤
        self.setMouseTracking(True)
        self._mouse_x = -1
        self._mouse_y = -1
        
        # ===== Linkage 同步控制 =====
        self._individual_linkage_enabled = True  # 預設啟用個別連動
        
        # 訂閱全局同步信號
        sync_signal = get_global_sync_signal()
        sync_signal.settings_changed.connect(self._on_settings_synced)
        
        self._init_ui()
        
        logger.info("[throttle_trace] ThrottleTraceWidget initialized (PyQt5 native)")
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # 頂部資訊列
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        self._primary_label = QLabel("Primary: --")
        self._primary_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(self._primary_label)
        
        self._compare_label = QLabel("Compare: --")
        self._compare_label.setStyleSheet("color: #888888; font-size: 11px;")
        info_layout.addWidget(self._compare_label)
        
        info_layout.addStretch()
        
        self._gap_label = QLabel("Gap: --")
        self._gap_label.setStyleSheet("color: #4ECDC4; font-size: 11px;")
        info_layout.addWidget(self._gap_label)
        
        layout.addLayout(info_layout)
        
        # 圖表區域 (使用 stretch 讓它佔據剩餘空間)
        layout.addStretch()
        
        # 右鍵選單
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Initialize hover tracking (from HoverTooltipMixin)
        self._init_hover_tracking()
        
        # 標識為 Trace 模組，用於 hover 位置同步過濾
        self._is_trace_module = True
    
    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 清空背景
            painter.fillRect(self.rect(), QColor(COLOR_BACKGROUND))
            
            # 計算圖表區域
            chart_rect = QRect(
                self.margin_left,
                self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom
            )
            
            if chart_rect.width() <= 0 or chart_rect.height() <= 0:
                return
            
            # 繪製背景
            painter.fillRect(chart_rect, QColor(COLOR_CHART_BG))
            
            # 繪製順序很重要
            self._draw_grid(painter, chart_rect)
            self._draw_corner_markers(painter, chart_rect)
            self._draw_gap_curve(painter, chart_rect)  # Gap 填充在油門曲線下面
            self._draw_throttle_curves(painter, chart_rect)
            self._draw_axes(painter, chart_rect)
            
            # Draw hover elements (from HoverTooltipMixin)
            self._draw_hover_elements(painter)
            
        finally:
            painter.end()
    
    # =========================================================================
    # Mouse Event Handlers for Hover
    # =========================================================================
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for hover tracking."""
        if self._handle_mouse_move(event):
            self.update()
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave."""
        if self._handle_mouse_leave():
            self.update()
        super().leaveEvent(event)
    
    def _get_chart_rect(self):
        """Override to return chart area as QRect."""
        return QRect(
            self.margin_left,
            self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
    
    def _pixel_to_x_value(self, pixel_x: int, chart_rect) -> float:
        """Convert pixel X to distance."""
        if chart_rect.width() <= 0:
            return 0.0
        
        ratio = (pixel_x - chart_rect.left()) / chart_rect.width()
        distance_range = self.max_distance - self.min_distance
        return self.min_distance + ratio * distance_range
    
    def _get_throttle_at_distance(self, lap_data, target_distance: float) -> Optional[float]:
        """Get throttle at a specific distance using interpolation."""
        if not lap_data or not lap_data.distances or not lap_data.throttles:
            return None
        
        for i in range(len(lap_data.distances) - 1):
            if lap_data.distances[i] <= target_distance <= lap_data.distances[i + 1]:
                d_range = lap_data.distances[i + 1] - lap_data.distances[i]
                if d_range > 0:
                    ratio = (target_distance - lap_data.distances[i]) / d_range
                    return lap_data.throttles[i] + ratio * (lap_data.throttles[i + 1] - lap_data.throttles[i])
        return None
    
    def _get_hover_data_at_x(self, x_value: float):
        """Get hover data at the specified distance."""
        distance = x_value
        data_points = []
        
        if self._show_primary_current and self._primary_current_lap and self._primary_driver:
            throttle = self._get_throttle_at_distance(self._primary_current_lap, distance)
            if throttle is not None:
                driver_info = self._driver_info.get(self._primary_driver, {})
                tla = driver_info.get('tla', self._primary_driver)
                team_color = driver_info.get('team_color', 'FFFFFF')
                data_points.append(HoverDataPoint(
                    label=f"{tla}",
                    value=throttle,
                    formatted_value=f"{throttle:.0f}%",
                    color=f"#{team_color}"
                ))
        
        if self._show_primary_best and self._primary_best_lap and self._primary_driver:
            throttle = self._get_throttle_at_distance(self._primary_best_lap, distance)
            if throttle is not None:
                driver_info = self._driver_info.get(self._primary_driver, {})
                tla = driver_info.get('tla', self._primary_driver)
                team_color = driver_info.get('team_color', 'FFFFFF')
                data_points.append(HoverDataPoint(
                    label=f"{tla} Best",
                    value=throttle,
                    formatted_value=f"{throttle:.0f}%",
                    color=f"#{team_color}",
                    is_primary=False
                ))
        
        if self._show_compare_current and self._compare_current_lap and self._compare_driver:
            throttle = self._get_throttle_at_distance(self._compare_current_lap, distance)
            if throttle is not None:
                driver_info = self._driver_info.get(self._compare_driver, {})
                tla = driver_info.get('tla', self._compare_driver)
                team_color = driver_info.get('team_color', '888888')
                data_points.append(HoverDataPoint(
                    label=f"{tla}",
                    value=throttle,
                    formatted_value=f"{throttle:.0f}%",
                    color=f"#{team_color}"
                ))
        
        if self._show_compare_best and self._compare_best_lap and self._compare_driver:
            throttle = self._get_throttle_at_distance(self._compare_best_lap, distance)
            if throttle is not None:
                driver_info = self._driver_info.get(self._compare_driver, {})
                tla = driver_info.get('tla', self._compare_driver)
                team_color = driver_info.get('team_color', '888888')
                data_points.append(HoverDataPoint(
                    label=f"{tla} Best",
                    value=throttle,
                    formatted_value=f"{throttle:.0f}%",
                    color=f"#{team_color}",
                    is_primary=False
                ))
        
        if not data_points:
            return None
        
        return HoverInfo(
            x_value=distance,
            x_label=f"Dist: {distance:.0f}m",
            data_points=data_points,
            is_valid=True
        )
    
    def _draw_grid(self, painter: QPainter, chart_rect: QRect):
        """繪製網格"""
        pen = QPen(QColor(COLOR_GRID), 1)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        
        # 垂直網格線 (距離)
        distance_range = self.max_distance - self.min_distance
        if distance_range > 0:
            num_lines = 10
            for i in range(1, num_lines):
                x = chart_rect.left() + i * chart_rect.width() / num_lines
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
        
        # 水平網格線 (速度)
        throttle_range = self.max_throttle - self.min_throttle
        if throttle_range > 0:
            num_lines = 7
            for i in range(1, num_lines):
                y = chart_rect.bottom() - i * chart_rect.height() / num_lines
                painter.drawLine(chart_rect.left(), int(y), chart_rect.right(), int(y))
    
    def _draw_axes(self, painter: QPainter, chart_rect: QRect):
        """繪製座標軸和標籤"""
        # 軸線
        pen = QPen(QColor(COLOR_AXIS), 2)
        painter.setPen(pen)
        painter.drawLine(chart_rect.left(), chart_rect.bottom(), chart_rect.right(), chart_rect.bottom())  # X軸
        painter.drawLine(chart_rect.left(), chart_rect.top(), chart_rect.left(), chart_rect.bottom())      # 左Y軸
        painter.drawLine(chart_rect.right(), chart_rect.top(), chart_rect.right(), chart_rect.bottom())    # 右Y軸
        
        # 字體設置
        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(COLOR_TEXT), 1))
        
        # X軸標籤 (距離)
        distance_range = self.max_distance - self.min_distance
        if distance_range > 0:
            for i in range(0, 11, 2):  # 只顯示偶數刻度
                distance_value = self.min_distance + i * distance_range / 10
                x = chart_rect.left() + i * chart_rect.width() / 10
                label_text = f"{int(distance_value)}"
                painter.drawText(int(x - 25), chart_rect.bottom() + 5, 50, 20, Qt.AlignCenter, label_text)
        
        # 左Y軸標籤 (速度)
        throttle_range = self.max_throttle - self.min_throttle
        if throttle_range > 0:
            for i in range(0, 8, 2):  # 只顯示偶數刻度
                throttle_value = self.min_throttle + i * throttle_range / 7
                y = chart_rect.bottom() - i * chart_rect.height() / 7
                painter.drawText(5, int(y - 10), self.margin_left - 10, 20, Qt.AlignRight | Qt.AlignVCenter, f"{int(throttle_value)}")
        
        # 右Y軸標籤 (Gap)
        painter.setPen(QPen(QColor(COLOR_DELTA_NEGATIVE), 1))
        gap_range = self.max_gap - self.min_gap
        if gap_range > 0:
            for i in range(0, 6):
                gap_value = self.min_gap + i * gap_range / 5
                y = chart_rect.bottom() - i * chart_rect.height() / 5
                label = f"{int(gap_value):+d}" if gap_value != 0 else "0"
                painter.drawText(chart_rect.right() + 5, int(y - 10), self.margin_right - 10, 20, Qt.AlignLeft | Qt.AlignVCenter, label)
        
        # 軸標題
        title_font = QFont("Microsoft YaHei", 9)
        painter.setFont(title_font)
        
        # X軸標題
        painter.setPen(QPen(QColor(COLOR_TEXT), 1))
        x_title_rect = QRect(chart_rect.left(), chart_rect.bottom() + 18, chart_rect.width(), 20)
        painter.drawText(x_title_rect, Qt.AlignCenter, "Distance (m)")
        
        # 左Y軸標題 (速度)
        painter.save()
        painter.translate(15, chart_rect.center().y())
        painter.rotate(-90)
        painter.drawText(-40, -10, 80, 20, Qt.AlignCenter, "throttle (%)")
        painter.restore()
        
        # 右Y軸標題 (Gap)
        painter.setPen(QPen(QColor(COLOR_DELTA_NEGATIVE), 1))
        painter.save()
        painter.translate(self.width() - 12, chart_rect.center().y())
        painter.rotate(90)
        painter.drawText(-30, -10, 60, 20, Qt.AlignCenter, "Gap (m)")
        painter.restore()
    
    def _draw_corner_markers(self, painter: QPainter, chart_rect: QRect):
        """繪製彎道標記"""
        if not self._corners or not self._show_corners:
            return
        
        # 設定虛線樣式，線寬 0.5 (更細)
        pen = QPen(QColor(COLOR_CORNER_MARKER), 0.5)
        pen.setStyle(Qt.DotLine)  # 點線更細緻
        painter.setPen(pen)
        
        font = QFont("Microsoft YaHei", 7)
        painter.setFont(font)
        
        distance_range = self.max_distance - self.min_distance
        if distance_range <= 0:
            return
        
        for corner in self._corners:
            corner_num = corner.get('number', 0)
            # 優先使用計算出的 lap_distance，否則嘗試 distance 或 mapped_distance
            corner_distance = corner.get('lap_distance', 0) or corner.get('distance', 0) or corner.get('mapped_distance', 0)
            
            # 只檢查是否在 X 軸可見範圍內
            if corner_distance <= 0:
                continue
            
            # 計算 X 座標
            x = chart_rect.left() + (corner_distance - self.min_distance) / distance_range * chart_rect.width()
            
            # 只繪製在圖表範圍內的彎道
            if x < chart_rect.left() or x > chart_rect.right():
                continue
            
            # 繪製垂直虛線
            painter.setPen(pen)  # 確保使用虛線筆
            painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
            
            # 標籤
            label_pen = QPen(QColor(COLOR_CORNER_MARKER), 1)
            label_pen.setStyle(Qt.SolidLine)  # 標籤用實線
            painter.setPen(label_pen)
            painter.drawText(int(x - 10), chart_rect.top() - 2, 20, 15, Qt.AlignCenter, f"T{corner_num}")
    
    def _draw_throttle_curves(self, painter: QPainter, chart_rect: QRect):
        """繪製油門曲線"""
        # 繪製主車手當前圈
        if self._show_primary_current and self._primary_current_lap:
            color = self._get_driver_color(self._primary_driver)
            self._draw_throttle_curve(painter, chart_rect, self._primary_current_lap, color, 1.5, Qt.SolidLine)
        
        # 繪製主車手最速圈
        if self._show_primary_best and self._primary_best_lap:
            color = self._get_driver_color(self._primary_driver)
            self._draw_throttle_curve(painter, chart_rect, self._primary_best_lap, color, 1.5, Qt.DashLine, 0.7)
        
        # 繪製對比車手當前圈
        if self._show_compare_current and self._compare_current_lap:
            color = self._get_driver_color(self._compare_driver)
            self._draw_throttle_curve(painter, chart_rect, self._compare_current_lap, color, 1.5, Qt.SolidLine)
        
        # 繪製對比車手最速圈
        if self._show_compare_best and self._compare_best_lap:
            color = self._get_driver_color(self._compare_driver)
            self._draw_throttle_curve(painter, chart_rect, self._compare_best_lap, color, 1.5, Qt.DashLine, 0.7)
    
    def _draw_throttle_curve(self, painter: QPainter, chart_rect: QRect, 
                          lap_data: LapThrottleData, color: str,
                          line_width: float = 2.0, line_style: Qt.PenStyle = Qt.SolidLine,
                          alpha: float = 1.0):
        """繪製單條油門曲線"""
        if not lap_data or len(lap_data.distances) < 2:
            return
        
        distance_range = self.max_distance - self.min_distance
        throttle_range = self.max_throttle - self.min_throttle
        
        if distance_range <= 0 or throttle_range <= 0:
            return
        
        # 設置畫筆
        qcolor = QColor(color)
        qcolor.setAlphaF(alpha)
        pen = QPen(qcolor, line_width)
        pen.setStyle(line_style)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        
        # 創建路徑
        path = QPainterPath()
        first_point = True
        
        for i in range(len(lap_data.distances)):
            dist = lap_data.distances[i]
            throttle = lap_data.throttles[i]
            
            # 轉換為螢幕座標
            x = chart_rect.left() + (dist - self.min_distance) / distance_range * chart_rect.width()
            y = chart_rect.bottom() - (throttle - self.min_throttle) / throttle_range * chart_rect.height()
            
            # 限制在圖表區域內
            x = max(chart_rect.left(), min(chart_rect.right(), x))
            y = max(chart_rect.top(), min(chart_rect.bottom(), y))
            
            if first_point:
                path.moveTo(x, y)
                first_point = False
            else:
                path.lineTo(x, y)
        
        painter.drawPath(path)
    
    def _draw_gap_curve(self, painter: QPainter, chart_rect: QRect):
        """繪製 Gap 曲線和填充"""
        if not self._show_gap:
            return
        if not self._gap_history_distances or len(self._gap_history_distances) < 2:
            return
        
        distance_range = self.max_distance - self.min_distance
        gap_range = self.max_gap - self.min_gap
        
        if distance_range <= 0 or gap_range <= 0:
            return
        
        # 繪製填充區域
        self._draw_gap_fill(painter, chart_rect, distance_range, gap_range)
        
        # 繪製 Gap 線
        pen = QPen(QColor('#FFFFFF'), 1.5)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        
        path = QPainterPath()
        first_point = True
        
        for i in range(len(self._gap_history_distances)):
            dist = self._gap_history_distances[i]
            gap = self._gap_history_values[i]
            
            x = chart_rect.left() + (dist - self.min_distance) / distance_range * chart_rect.width()
            y = chart_rect.bottom() - (gap - self.min_gap) / gap_range * chart_rect.height()
            
            x = max(chart_rect.left(), min(chart_rect.right(), x))
            y = max(chart_rect.top(), min(chart_rect.bottom(), y))
            
            if first_point:
                path.moveTo(x, y)
                first_point = False
            else:
                path.lineTo(x, y)
        
        painter.drawPath(path)
        
        # 繪製零線
        zero_y = chart_rect.bottom() - (0 - self.min_gap) / gap_range * chart_rect.height()
        if chart_rect.top() <= zero_y <= chart_rect.bottom():
            pen = QPen(QColor('#666666'), 1)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(chart_rect.left(), int(zero_y), chart_rect.right(), int(zero_y))
    
    def _draw_gap_fill(self, painter: QPainter, chart_rect: QRect, 
                       distance_range: float, gap_range: float):
        """繪製 Gap 填充區域"""
        if len(self._gap_history_distances) < 2:
            return
        
        # 計算零線 Y 座標
        zero_y = chart_rect.bottom() - (0 - self.min_gap) / gap_range * chart_rect.height()
        
        # 正值填充 (領先 - 青色)
        positive_path = QPainterPath()
        negative_path = QPainterPath()
        
        # 建立正值區域路徑
        positive_started = False
        for i in range(len(self._gap_history_distances)):
            dist = self._gap_history_distances[i]
            gap = self._gap_history_values[i]
            
            x = chart_rect.left() + (dist - self.min_distance) / distance_range * chart_rect.width()
            y = chart_rect.bottom() - (gap - self.min_gap) / gap_range * chart_rect.height()
            
            x = max(chart_rect.left(), min(chart_rect.right(), x))
            y = max(chart_rect.top(), min(chart_rect.bottom(), y))
            
            if gap > 0:
                if not positive_started:
                    positive_path.moveTo(x, zero_y)
                    positive_started = True
                positive_path.lineTo(x, y)
            else:
                if positive_started:
                    positive_path.lineTo(x, zero_y)
                    positive_started = False
        
        if positive_started:
            # 閉合路徑
            last_x = chart_rect.left() + (self._gap_history_distances[-1] - self.min_distance) / distance_range * chart_rect.width()
            positive_path.lineTo(last_x, zero_y)
        
        # 繪製正值填充
        if not positive_path.isEmpty():
            color = QColor(COLOR_DELTA_NEGATIVE)
            color.setAlpha(80)
            painter.fillPath(positive_path, QBrush(color))
        
        # 建立負值區域路徑
        negative_started = False
        for i in range(len(self._gap_history_distances)):
            dist = self._gap_history_distances[i]
            gap = self._gap_history_values[i]
            
            x = chart_rect.left() + (dist - self.min_distance) / distance_range * chart_rect.width()
            y = chart_rect.bottom() - (gap - self.min_gap) / gap_range * chart_rect.height()
            
            x = max(chart_rect.left(), min(chart_rect.right(), x))
            y = max(chart_rect.top(), min(chart_rect.bottom(), y))
            
            if gap <= 0:
                if not negative_started:
                    negative_path.moveTo(x, zero_y)
                    negative_started = True
                negative_path.lineTo(x, y)
            else:
                if negative_started:
                    negative_path.lineTo(x, zero_y)
                    negative_started = False
        
        if negative_started:
            last_x = chart_rect.left() + (self._gap_history_distances[-1] - self.min_distance) / distance_range * chart_rect.width()
            negative_path.lineTo(last_x, zero_y)
        
        # 繪製負值填充
        if not negative_path.isEmpty():
            color = QColor(COLOR_DELTA_POSITIVE)
            color.setAlpha(80)
            painter.fillPath(negative_path, QBrush(color))
    
    def _draw_legend(self, painter: QPainter, chart_rect: QRect):
        """繪製圖例"""
        legends = []
        
        if self._show_primary_current and self._primary_driver:
            tla = self._get_driver_tla(self._primary_driver)
            color = self._get_driver_color(self._primary_driver)
            legends.append((f"{tla} Current", color, Qt.SolidLine))
        
        if self._show_primary_best and self._primary_driver:
            tla = self._get_driver_tla(self._primary_driver)
            color = self._get_driver_color(self._primary_driver)
            legends.append((f"{tla} Best", color, Qt.DashLine))
        
        if self._show_compare_current and self._compare_driver:
            tla = self._get_driver_tla(self._compare_driver)
            color = self._get_driver_color(self._compare_driver)
            legends.append((f"{tla} Current", color, Qt.SolidLine))
        
        if self._show_compare_best and self._compare_driver:
            tla = self._get_driver_tla(self._compare_driver)
            color = self._get_driver_color(self._compare_driver)
            legends.append((f"{tla} Best", color, Qt.DashLine))
        
        if not legends:
            return
        
        # 繪製圖例背景
        legend_width = 100
        legend_height = len(legends) * 18 + 8
        legend_x = chart_rect.right() - legend_width - 10
        legend_y = chart_rect.top() + 10
        
        bg_color = QColor('#2a2a2a')
        bg_color.setAlpha(200)
        painter.fillRect(legend_x, legend_y, legend_width, legend_height, bg_color)
        
        border_color = QColor('#444444')
        painter.setPen(QPen(border_color, 1))
        painter.drawRect(legend_x, legend_y, legend_width, legend_height)
        
        # 繪製圖例項目
        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)
        
        y_offset = legend_y + 12
        for label, color, line_style in legends:
            # 線條樣本
            pen = QPen(QColor(color), 2)
            pen.setStyle(line_style)
            painter.setPen(pen)
            painter.drawLine(legend_x + 5, y_offset, legend_x + 25, y_offset)
            
            # 文字
            painter.setPen(QPen(QColor('#FFFFFF'), 1))
            painter.drawText(legend_x + 30, y_offset - 6, legend_width - 35, 16, Qt.AlignLeft | Qt.AlignVCenter, label)
            
            y_offset += 18
    
    # ===== 數據更新方法 =====
    
    def set_track_info(self, track_length: float, corners: List[Dict[str, Any]]):
        """設置賽道資訊"""
        self._corners = corners or []
        
        # 如果 track_length 無效，嘗試從彎道資料推算
        if track_length <= 0 and self._corners:
            # 取最後一個彎道的距離作為近似賽道長度
            max_corner_dist = max(
                c.get('distance', 0) or c.get('mapped_distance', 0) 
                for c in self._corners
            )
            # 通常最後一個彎道後還有一段直線到終點，加 10%
            track_length = max_corner_dist * 1.1
        
        self._track_length = track_length if track_length > 0 else 5000.0
        self.max_distance = self._track_length
        
        logger.info("[throttle_trace] Track info set: length=%sm, corners=%d", self._track_length, len(self._corners))
        self.update()
    
    def set_driver_info(self, driver_info: Dict[str, Dict[str, Any]]):
        """設置車手資訊"""
        self._driver_info = driver_info or {}
    
    def set_primary_driver(self, driver_num: str):
        """設置主車手"""
        if driver_num == self._primary_driver:
            return
        
        self._primary_driver = driver_num
        tla = self._driver_info.get(driver_num, {}).get('tla', driver_num)
        team_color = self._driver_info.get(driver_num, {}).get('team_color', 'FFFFFF')
        
        self._primary_label.setText(f"Primary: {tla}")
        self._primary_label.setStyleSheet(f"color: #{team_color}; font-weight: bold; font-size: 11px;")
        
        # 載入該車手的最速圈 (如果有)
        if driver_num in self._all_best_laps:
            self._primary_best_lap = self._all_best_laps[driver_num]
        else:
            self._primary_best_lap = None
        
        # 載入當前圈
        if driver_num in self._all_current_laps:
            self._primary_current_lap = self._all_current_laps[driver_num]
        else:
            self._primary_current_lap = None
        
        logger.info("[throttle_trace] Primary driver set: %s (%s)", tla, driver_num)
        self.update()
    
    def set_compare_driver(self, driver_num: Optional[str]):
        """設置對比車手"""
        if driver_num == self._compare_driver:
            return
        
        self._compare_driver = driver_num
        
        if driver_num:
            tla = self._driver_info.get(driver_num, {}).get('tla', driver_num)
            team_color = self._driver_info.get(driver_num, {}).get('team_color', '888888')
            self._compare_label.setText(f"Compare: {tla}")
            self._compare_label.setStyleSheet(f"color: #{team_color}; font-size: 11px;")
            
            # 載入對比車手資料
            self._compare_best_lap = self._all_best_laps.get(driver_num)
            self._compare_current_lap = self._all_current_laps.get(driver_num)
            
            # 自動切換 Delta 參考為 Compare Current
            self._delta_reference = 'compare_current'
        else:
            self._compare_label.setText("Compare: --")
            self._compare_label.setStyleSheet("color: #888888; font-size: 11px;")
            self._compare_best_lap = None
            self._compare_current_lap = None
            
            # 無 Compare 時，Delta 參考切回 Primary Best
            self._delta_reference = 'primary_best'
        
        logger.info("[throttle_trace] Compare driver set: %s, delta_reference=%s", driver_num, self._delta_reference)
        self.update()
    
    def update_from_snapshot(self, snapshot: Dict[str, Any]):
        """從快照更新數據"""
        drivers_data = snapshot.get('drivers', {})
        race_time_seconds = snapshot.get('race_time_seconds', 0.0)
        
        processed_count = 0
        for driver_num, driver_data in drivers_data.items():
            throttle = driver_data.get('throttle')
            lap_number = driver_data.get('lap')
            
            # 取得 GPS 座標 (來自 Position.z)
            x = driver_data.get('x')
            y = driver_data.get('y')
            
            # throttle 必須有效，lap 可以是 0 (編隊圈) 或正整數
            if throttle is None:
                continue
            
            # 處理 lap_number: None 視為 0 (編隊圈)
            if lap_number is None:
                lap_number = 0
            try:
                lap_number = int(lap_number)
            except (ValueError, TypeError):
                continue
            
            # lap_number 必須非負
            if lap_number < 0:
                continue
            
            processed_count += 1
            
            # 更新車手資訊
            if driver_num not in self._driver_info:
                self._driver_info[driver_num] = {}
            self._driver_info[driver_num]['tla'] = driver_data.get('driver_tla', driver_num)
            self._driver_info[driver_num]['team_color'] = driver_data.get('team_color', 'CCCCCC')
            self._driver_info[driver_num]['position'] = driver_data.get('position', 99)
            
            # 計算累積距離 (使用 GPS 座標)
            distance = self._calculate_distance(driver_num, throttle, race_time_seconds, lap_number, x, y)
            
            # 確保有當前圈資料結構
            if driver_num not in self._all_current_laps:
                self._all_current_laps[driver_num] = LapThrottleData(
                    driver_num=driver_num,
                    lap_number=lap_number
                )
            
            current_lap_data = self._all_current_laps[driver_num]
            
            # 檢查是否換圈
            if current_lap_data.lap_number != lap_number:
                # 完成上一圈，檢查是否為最速圈
                self._finalize_lap(driver_num, current_lap_data)
                
                # 開始新的一圈
                self._all_current_laps[driver_num] = LapThrottleData(
                    driver_num=driver_num,
                    lap_number=lap_number
                )
                current_lap_data = self._all_current_laps[driver_num]
                
                # 重置距離追蹤
                self._distance_tracker[driver_num] = {
                    'distance': 0.0,
                    'last_timestamp': race_time_seconds,
                    'last_lap': lap_number,
                    'last_x': x,
                    'last_y': y
                }
                distance = 0.0
            
            # 計算圈內時間
            lap_start_time = self._distance_tracker.get(driver_num, {}).get('lap_start_time', race_time_seconds)
            lap_time = race_time_seconds - lap_start_time
            
            # 添加數據點
            current_lap_data.add_point(distance, throttle, lap_time)
            
            # 更新即時位置 (用於 Gap 計算)
            total_distance = (lap_number * self._track_length) + distance
            self._realtime_positions[driver_num] = {
                'lap': lap_number,
                'lap_distance': distance,
                'total_distance': total_distance
            }
            
            # 更新主車手/對比車手的引用
            if driver_num == self._primary_driver:
                self._primary_current_lap = current_lap_data
            elif driver_num == self._compare_driver:
                self._compare_current_lap = current_lap_data
        
        # 更新 Gap 曲線
        self._update_gap_history()
        
        # 如果還沒有主車手，自動選擇最速者
        if not self._primary_driver:
            self._auto_select_fastest_driver()
        
        self.update()
    
    def _update_gap_history(self):
        """更新 Gap 歷史記錄"""
        primary_pos = self._realtime_positions.get(self._primary_driver) if self._primary_driver else None
        compare_pos = self._realtime_positions.get(self._compare_driver) if self._compare_driver else None
        
        if not primary_pos or not compare_pos:
            self._gap_label.setText("Gap: --")
            self._gap_label.setStyleSheet("color: #888888; font-size: 11px;")
            return
        
        # 計算總距離差
        primary_total = primary_pos['total_distance']
        compare_total = compare_pos['total_distance']
        gap = primary_total - compare_total  # 正值 = Primary 領先
        
        # 記錄 Gap 歷史 (使用 Primary 的圈內距離作為 X 軸)
        primary_lap_dist = primary_pos['lap_distance']
        
        # 換圈時清空歷史
        if self._gap_history_distances and primary_lap_dist < self._gap_history_distances[-1] - 100:
            self._gap_history_distances.clear()
            self._gap_history_values.clear()
        
        self._gap_history_distances.append(primary_lap_dist)
        self._gap_history_values.append(gap)
        
        # 更新 Gap 標籤
        if gap > 0:
            gap_text = f"+{gap:.0f}m"
            gap_color = COLOR_DELTA_NEGATIVE  # 領先用青色
        else:
            gap_text = f"{gap:.0f}m"
            gap_color = COLOR_DELTA_POSITIVE  # 落後用紅色
        
        self._gap_label.setText(f"Gap: {gap_text}")
        self._gap_label.setStyleSheet(f"color: {gap_color}; font-size: 11px;")
    
    def _calculate_distance(self, driver_num: str, throttle: float, timestamp: float, 
                            lap_number: int, x: float = None, y: float = None) -> float:
        """計算累積距離 (優先使用 GPS 座標，否則使用速度積分)"""
        if driver_num not in self._distance_tracker:
            self._distance_tracker[driver_num] = {
                'distance': 0.0,
                'last_timestamp': timestamp,
                'last_lap': lap_number,
                'lap_start_time': timestamp,
                'last_x': x,
                'last_y': y
            }
            return 0.0
        
        tracker = self._distance_tracker[driver_num]
        
        # 換圈時重置
        if tracker['last_lap'] != lap_number:
            tracker['distance'] = 0.0
            tracker['last_timestamp'] = timestamp
            tracker['last_lap'] = lap_number
            tracker['lap_start_time'] = timestamp
            tracker['last_x'] = x
            tracker['last_y'] = y
            return 0.0
        
        # 優先使用 GPS 座標計算距離 (更準確)
        if x is not None and y is not None:
            last_x = tracker.get('last_x')
            last_y = tracker.get('last_y')
            
            if last_x is not None and last_y is not None:
                # 計算兩點之間的歐幾里得距離
                dx = x - last_x
                dy = y - last_y
                coord_distance = math.sqrt(dx * dx + dy * dy)
                
                # Position.z 座標單位約 10 = 1 公尺，需要縮放
                COORD_TO_METER_SCALE = 10.0
                distance_delta = coord_distance / COORD_TO_METER_SCALE
                
                # 防止異常大的距離跳躍 (可能是座標錯誤或快照丟失)
                if distance_delta < 500:  # 最大允許 500m 的跳躍
                    tracker['distance'] += distance_delta
            
            # 更新座標
            tracker['last_x'] = x
            tracker['last_y'] = y
        else:
            # 回退到速度積分方式
            dt = timestamp - tracker['last_timestamp']
            if dt > 0 and dt < 5.0:  # 防止異常大的時間跳躍
                distance_delta = throttle * dt / 3.6
                tracker['distance'] += distance_delta
        
        tracker['last_timestamp'] = timestamp
        
        # 限制不超過賽道長度
        return min(tracker['distance'], self._track_length)
    
    def _finalize_lap(self, driver_num: str, lap_data: LapThrottleData):
        """完成一圈，檢查是否為最速圈"""
        if not lap_data.timestamps:
            return
        
        lap_data.is_complete = True
        lap_data.lap_time = lap_data.timestamps[-1] if lap_data.timestamps else None
        
        tla = self._driver_info.get(driver_num, {}).get('tla', driver_num)
        
        # 檢查是否為該車手的最速圈
        current_best = self._all_best_laps.get(driver_num)
        
        if lap_data.lap_time and lap_data.lap_time > 0:
            is_new_best = False
            if current_best is None:
                is_new_best = True
            elif current_best.lap_time is None:
                is_new_best = True
            elif lap_data.lap_time < current_best.lap_time:
                is_new_best = True
            
            if is_new_best:
                # 深拷貝保存為最速圈
                import copy
                self._all_best_laps[driver_num] = copy.deepcopy(lap_data)
                
                logger.info("[throttle_trace] New best lap for %s: %.3fs (Lap %s)", tla, lap_data.lap_time, lap_data.lap_number)
                
                # 更新主車手/對比車手的最速圈引用
                if driver_num == self._primary_driver:
                    self._primary_best_lap = self._all_best_laps[driver_num]
                elif driver_num == self._compare_driver:
                    self._compare_best_lap = self._all_best_laps[driver_num]
    
    def _auto_select_fastest_driver(self):
        """自動選擇最速車手作為主車手"""
        if not self._all_best_laps:
            # 沒有最速圈資料，選擇第一個有數據的車手
            if self._all_current_laps:
                first_driver = next(iter(self._all_current_laps.keys()))
                self.set_primary_driver(first_driver)
            return
        
        # 找出最速圈時間最短的車手
        fastest_driver = None
        fastest_time = float('inf')
        
        for driver_num, lap_data in self._all_best_laps.items():
            if lap_data.lap_time and lap_data.lap_time < fastest_time:
                fastest_time = lap_data.lap_time
                fastest_driver = driver_num
        
        if fastest_driver:
            self.set_primary_driver(fastest_driver)
    
    def _get_driver_color(self, driver_num: Optional[str]) -> str:
        """獲取車手顏色"""
        if not driver_num:
            return '#FFFFFF'
        color = self._driver_info.get(driver_num, {}).get('team_color', 'FFFFFF')
        return f'#{color}' if not color.startswith('#') else color
    
    def _get_driver_tla(self, driver_num: Optional[str]) -> str:
        """獲取車手代碼"""
        if not driver_num:
            return '--'
        return self._driver_info.get(driver_num, {}).get('tla', driver_num)
    
    def _show_context_menu(self, pos):
        """顯示右鍵選單"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444444;
            }
            QMenu::item:selected {
                background-color: #3a3a3a;
            }
            QMenu::separator {
                height: 1px;
                background: #444444;
            }
        """)
        
        # ===== 主車手選項 =====
        primary_menu = menu.addMenu(f"Primary: {self._get_driver_tla(self._primary_driver)}")
        
        # 顯示當前圈
        action_primary_current = primary_menu.addAction("Show Current Lap")
        action_primary_current.setCheckable(True)
        action_primary_current.setChecked(self._show_primary_current)
        action_primary_current.triggered.connect(lambda checked: self._toggle_option('primary_current', checked))
        
        # 顯示最速圈
        action_primary_best = primary_menu.addAction("Show Best Lap")
        action_primary_best.setCheckable(True)
        action_primary_best.setChecked(self._show_primary_best)
        action_primary_best.triggered.connect(lambda checked: self._toggle_option('primary_best', checked))
        
        # 選擇主車手
        primary_menu.addSeparator()
        select_primary_menu = primary_menu.addMenu("Select Driver")
        self._populate_driver_menu(select_primary_menu, is_primary=True)
        
        menu.addSeparator()
        
        # ===== 對比車手選項 =====
        compare_tla = self._get_driver_tla(self._compare_driver) if self._compare_driver else "(None)"
        compare_menu = menu.addMenu(f"Compare: {compare_tla}")
        
        # 清除對比
        action_clear_compare = compare_menu.addAction("Clear Compare")
        action_clear_compare.triggered.connect(lambda: self.set_compare_driver(None))
        
        compare_menu.addSeparator()
        
        # 顯示當前圈
        action_compare_current = compare_menu.addAction("Show Current Lap")
        action_compare_current.setCheckable(True)
        action_compare_current.setChecked(self._show_compare_current)
        action_compare_current.setEnabled(self._compare_driver is not None)
        action_compare_current.triggered.connect(lambda checked: self._toggle_option('compare_current', checked))
        
        # 顯示最速圈
        action_compare_best = compare_menu.addAction("Show Best Lap")
        action_compare_best.setCheckable(True)
        action_compare_best.setChecked(self._show_compare_best)
        action_compare_best.setEnabled(self._compare_driver is not None)
        action_compare_best.triggered.connect(lambda checked: self._toggle_option('compare_best', checked))
        
        # 選擇對比車手
        compare_menu.addSeparator()
        select_compare_menu = compare_menu.addMenu("Select Driver")
        self._populate_driver_menu(select_compare_menu, is_primary=False)
        
        menu.addSeparator()
        
        # ===== 彎道標記選項 =====
        action_show_corners = menu.addAction("Show Corner Markers")
        action_show_corners.setCheckable(True)
        action_show_corners.setChecked(self._show_corners)
        action_show_corners.setEnabled(len(self._corners) > 0)
        action_show_corners.triggered.connect(lambda checked: self._toggle_option('corners', checked))
        
        # ===== Gap 填充選項 =====
        action_show_gap = menu.addAction("Show Gap")
        action_show_gap.setCheckable(True)
        action_show_gap.setChecked(self._show_gap)
        action_show_gap.setEnabled(self._compare_driver is not None)
        action_show_gap.triggered.connect(lambda checked: self._toggle_option('gap', checked))
        
        menu.addSeparator()
        
        # ===== 同步參數選項 =====
        action_sync = menu.addAction("Sync Settings to All Traces")
        action_sync.setStatusTip("Synchronize driver selection, corner markers, and Gap settings to all trace modules")
        action_sync.triggered.connect(self._broadcast_settings)
        
        menu.exec_(self.mapToGlobal(pos))
    
    def _populate_driver_menu(self, menu: QMenu, is_primary: bool):
        """填充車手選擇子選單"""
        # 按位置排序
        sorted_drivers = sorted(
            self._driver_info.items(),
            key=lambda x: x[1].get('position', 99) if isinstance(x[1], dict) else 99
        )
        
        for driver_num, info in sorted_drivers:
            if not isinstance(info, dict):
                continue
            
            tla = info.get('tla', driver_num)
            team_color = info.get('team_color', 'FFFFFF')
            
            action = menu.addAction(tla)
            action.setData(driver_num)
            
            # 標記當前選中
            if is_primary and driver_num == self._primary_driver:
                action.setCheckable(True)
                action.setChecked(True)
            elif not is_primary and driver_num == self._compare_driver:
                action.setCheckable(True)
                action.setChecked(True)
            
            if is_primary:
                action.triggered.connect(lambda checked, d=driver_num: self.set_primary_driver(d))
            else:
                action.triggered.connect(lambda checked, d=driver_num: self._select_compare_driver(d))
    
    def _select_compare_driver(self, driver_num: str):
        """選擇對比車手並自動開啟顯示"""
        self.set_compare_driver(driver_num)
        self._show_compare_current = True
        self.update()
    
    def _toggle_option(self, option: str, checked: bool):
        """切換顯示選項"""
        if option == 'primary_current':
            self._show_primary_current = checked
        elif option == 'primary_best':
            self._show_primary_best = checked
        elif option == 'compare_current':
            self._show_compare_current = checked
        elif option == 'compare_best':
            self._show_compare_best = checked
        elif option == 'corners':
            self._show_corners = checked
        elif option == 'gap':
            self._show_gap = checked
        
        self.update()
    
    def _set_delta_reference(self, ref: str):
        """設置 Delta 參考來源"""
        self._delta_reference = ref
        self.update()
    
    def _broadcast_settings(self):
        """廣播當前設定到其他模組"""
        settings = {
            'primary_driver': self._primary_driver,
            'compare_driver': self._compare_driver,
            'show_primary_current': self._show_primary_current,
            'show_primary_best': self._show_primary_best,
            'show_compare_current': self._show_compare_current,
            'show_compare_best': self._show_compare_best,
            'show_corners': self._show_corners,
            'show_gap': self._show_gap,
            'source_widget': id(self)
        }
        sync_signal = get_global_sync_signal()
        sync_signal.settings_changed.emit(settings)
    
    def _on_settings_synced(self, settings: dict):
        """接收其他模組的設定同步"""
        if settings.get('source_widget') == id(self):
            return
        
        # 檢查個別連動是否啟用
        if not self._individual_linkage_enabled:
            return
        
        self._primary_driver = settings.get('primary_driver')
        self._compare_driver = settings.get('compare_driver')
        self._show_primary_current = settings.get('show_primary_current', True)
        self._show_primary_best = settings.get('show_primary_best', False)
        self._show_compare_current = settings.get('show_compare_current', False)
        self._show_compare_best = settings.get('show_compare_best', False)
        self._show_corners = settings.get('show_corners', True)
        self._show_gap = settings.get('show_gap', True)
        
        if hasattr(self, '_primary_label'):
            tla = self._get_driver_tla(self._primary_driver)
            self._primary_label.setText(f"Primary: {tla}")
        if hasattr(self, '_compare_label'):
            tla = self._get_driver_tla(self._compare_driver) if self._compare_driver else "--"
            self._compare_label.setText(f"Compare: {tla}")
        
        self.update()
    
    # =========================================================================
    # Linkage Control Methods
    # =========================================================================
    
    def set_individual_linkage_enabled(self, enabled: bool):
        """設置個別連動狀態"""
        self._individual_linkage_enabled = enabled
    
    def is_individual_linkage_enabled(self) -> bool:
        """獲取個別連動狀態"""
        return self._individual_linkage_enabled
    
    def clear(self):
        """清除所有資料"""
        self._primary_driver = None
        self._primary_current_lap = None
        self._primary_best_lap = None
        self._compare_driver = None
        self._compare_current_lap = None
        self._compare_best_lap = None
        self._all_best_laps.clear()
        self._all_current_laps.clear()
        self._driver_info.clear()
        self._distance_tracker.clear()
        self._gap_history_distances.clear()
        self._gap_history_values.clear()
        
        self._primary_label.setText("Primary: --")
        self._compare_label.setText("Compare: --")
        self._gap_label.setText("Gap: --")
        
        self.update()


class LiveTimingThrottleTrace(BaseLiveTimingMDI):
    """
    Throttle Trace MDI 視窗
    
    即時顯示車手油門開度 vs 距離曲線
    """
    
    MODULE_ID = "live_timing_throttle_trace"
    DEFAULT_TITLE = "Throttle Trace"
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(self.DEFAULT_TITLE)
        self.resize(800, 400)
        
        # 連接 DataManager 信號
        if self._data_manager:
            self._data_manager.driver_selected.connect(self._on_driver_selected)
        
        logger.info("[throttle_trace_MDI] LiveTimingThrottleTrace initialized (PyQt5 native)")
    
    def _setup_ui(self):
        """Setup UI components"""
        self.throttle_widget = ThrottleTraceWidget()
        self._main_layout.addWidget(self.throttle_widget)
    
    # =========================================================================
    # Linkage Control Methods (for DraggableTitleBar integration)
    # =========================================================================
    
    def set_linkage_enabled(self, enabled: bool):
        """設置連動狀態 - 被標題列的 L 按鈕調用"""
        if hasattr(self, 'throttle_widget'):
            self.throttle_widget.set_individual_linkage_enabled(enabled)
            # 同時控制 hover 位置同步
            if hasattr(self.throttle_widget, 'set_hover_linkage_enabled'):
                self.throttle_widget.set_hover_linkage_enabled(enabled)
    
    def is_linkage_enabled(self) -> bool:
        """獲取連動狀態"""
        if hasattr(self, 'throttle_widget'):
            return self.throttle_widget.is_individual_linkage_enabled()
        return True
    
    def _on_driver_selected(self, driver_num: str):
        """處理車手選擇信號 - 從 DataManager snapshot 獲取車手資訊"""
        logger.info("[throttle_trace_MDI] Driver selected from external: %s", driver_num)
        if hasattr(self, 'throttle_widget'):
            # 先確保 widget 有車手資訊 (從 DataManager 獲取 snapshot)
            if self._data_manager:
                snapshot = self._data_manager.get_current_snapshot()
                if snapshot:
                    drivers = snapshot.get('drivers', {})
                    driver_info = drivers.get(driver_num, {})
                    if driver_info:
                        # 確保 _driver_info 已填充
                        tla = driver_info.get('driver_tla', driver_num)
                        team_color = driver_info.get('team_color', 'FFFFFF')
                        if driver_num not in self.throttle_widget._driver_info:
                            self.throttle_widget._driver_info[driver_num] = {}
                        self.throttle_widget._driver_info[driver_num]['tla'] = tla
                        self.throttle_widget._driver_info[driver_num]['team_color'] = team_color
                        logger.debug("[throttle_trace_MDI] Driver info from snapshot: %s (%s)", tla, team_color)
            
            self.throttle_widget.set_primary_driver(driver_num)
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """從快照更新"""
        if hasattr(self, 'throttle_widget'):
            # 調試：檢查 snapshot 中的資料
            drivers = snapshot.get('drivers', {})
            if drivers:
                sample_driver = next(iter(drivers.values()))
                throttle = sample_driver.get('throttle')
                lap = sample_driver.get('lap')
                if throttle is not None:
                    logger.debug(
                        "[throttle_trace_DEBUG] Snapshot received: %d drivers, sample throttle=%s, lap=%s",
                        len(drivers),
                        throttle,
                        lap,
                    )
            
            self.throttle_widget.update_from_snapshot(snapshot)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """賽事載入完成 - 載入賽道資訊和彎道資料"""
        year = race_info.get('year', 2025)
        race_key = race_info.get('race', '')
        
        logger.info("[throttle_trace_MDI] Race loaded: %s %s", year, race_key)
        
        # 載入賽道資料（包含彎道資訊）
        self._load_track_data(year, race_key)
    
    def _load_track_data(self, year: int, race_key: str):
        """載入賽道資料 - 僅使用 API，禁止本地回退"""
        # 標準化賽事名稱
        track_name = race_key.replace('_', ' ').replace(' Grand Prix', '').strip()
        
        # 僅通過 API 獲取
        if self._load_track_via_api(year, track_name):
            return True
        
        # API 失敗，返回錯誤（禁止本地回退）
        logger.error("[throttle_trace_MDI] API 獲取失敗，請確認 API 服務器已啟動")
        return False
    
    def _load_track_via_api(self, year: int, track_name: str) -> bool:
        """通過 API (Function 2) 獲取賽道數據"""
        try:
            from ..core.api_client import get_api_client
            
            api_client = get_api_client()
            
            # 嘗試當年和其他年份
            years_to_try = [year, 2025, 2024, 2023]
            seen = set()
            
            for try_year in years_to_try:
                if try_year in seen:
                    continue
                seen.add(try_year)
                
                logger.info("[throttle_trace_MDI] 嘗試 API 獲取: %s %s", try_year, track_name)
                data = api_client.get_track_analysis(try_year, track_name, "R")
                
                if data:
                    return self._process_track_data(data, year, try_year, track_name, "API")
            
            return False
            
        except Exception as e:
            logger.exception("[throttle_trace_MDI] API 獲取賽道數據失敗: %s", e)
            return False
    
    def _process_track_data(self, data: dict, orig_year: int, loaded_year: int, track_name: str, source: str) -> bool:
        """處理賽道數據並設置到 widget"""
        try:
            # 獲取賽道長度
            bounds = data.get('track_bounds', {})
            track_length = bounds.get('track_length', 0)
            
            # 如果 track_length 無效，嘗試從 position_records 估算
            if track_length <= 0:
                position_records = data.get('position_records', [])
                if position_records:
                    max_dist = max(r.get('distance_m', 0) for r in position_records)
                    # 通過分析連續點的距離差來估算單圈長度
                    # 假設數據來自多圈遙測，找到距離重置的位置
                    track_length = self._estimate_track_length_from_records(position_records, max_dist)
            
            # 如果仍無法估算，使用彎道數據來估算
            if track_length <= 0:
                corners_data = data.get('official_corners', {})
                corners_raw = corners_data.get('corners', [])
                if corners_raw:
                    # 使用彎道的 mapped_distance 來估算
                    # 通常最後一個彎道在單圈末段，加上一段直線到終點
                    track_length = self._estimate_track_length_from_corners(corners_raw)
            
            # 確保 track_length 有效
            if track_length <= 0:
                track_length = 5000
                logger.warning("[throttle_trace_MDI] 無法估算賽道長度，使用默認值 %sm", track_length)
            
            # 獲取彎道資料 - 直接使用 JSON 中的 distance 欄位
            corners_data = data.get('official_corners', {})
            corners_raw = corners_data.get('corners', [])
            
            # 處理彎道資料（傳入 track_length 用於 mapped_distance 轉換）
            corners = self._process_corners_from_json(corners_raw, track_length)
            
            if hasattr(self, 'throttle_widget'):
                self.throttle_widget.set_track_info(track_length, corners)
            
            if loaded_year != orig_year:
                logger.info("[throttle_trace_MDI] 使用 %s 賽道數據 (%s, 原始年份 %s 不可用)", loaded_year, source, orig_year)
            logger.info(
                "[throttle_trace_MDI] 賽道載入成功 (%s): %s, length=%.0fm, corners=%d",
                source,
                track_name,
                track_length,
                len(corners),
            )
            return True
            
        except Exception as e:
            logger.exception("[throttle_trace_MDI] 處理賽道數據失敗: %s", e)
            return False
    
    def _estimate_track_length_from_records(self, position_records: List[Dict], max_dist: float) -> float:
        """從 position_records 估算賽道長度"""
        if not position_records or max_dist <= 0:
            return 0
        
        # 分析距離序列，找到距離重置的位置（圈數邊界）
        distances = [r.get('distance_m', 0) for r in position_records]
        lap_starts = [0]  # 第一圈開始於索引 0
        
        for i in range(1, len(distances)):
            # 如果當前距離比前一個小很多，說明是新一圈開始
            if distances[i] < distances[i-1] - 1000:
                lap_starts.append(i)
        
        if len(lap_starts) >= 2:
            # 使用第一圈的距離作為賽道長度
            first_lap_end_idx = lap_starts[1] - 1
            track_length = distances[first_lap_end_idx]
            logger.info(
                "[throttle_trace_MDI] 從 position_records 估算賽道長度: %.0fm (detected %d laps)",
                track_length,
                len(lap_starts),
            )
            return track_length
        else:
            # 無法檢測圈數邊界，使用 max_dist / 假設圈數
            # F1 賽道通常在 3-7km 之間
            estimated_laps = max(1, round(max_dist / 5000))
            track_length = max_dist / estimated_laps
            logger.warning(
                "[throttle_trace_MDI] 無法檢測圈數邊界，估算 %d 圈，賽道長度: %.0fm",
                estimated_laps,
                track_length,
            )
            return track_length
    
    def _estimate_track_length_from_corners(self, corners: List[Dict]) -> float:
        """從彎道數據估算賽道長度"""
        if not corners:
            return 0
        
        # 取所有彎道的 mapped_distance
        mapped_distances = [c.get('mapped_distance', 0) for c in corners if c.get('mapped_distance', 0) > 0]
        if not mapped_distances:
            return 0
        
        # 找到最小和最大的 mapped_distance
        min_dist = min(mapped_distances)
        max_dist = max(mapped_distances)
        
        # 如果所有彎道在一個相近的範圍內（說明是單圈數據）
        dist_range = max_dist - min_dist
        if dist_range < 7000:  # F1 賽道最長約 7km
            # 最後一個彎道通常在單圈末段，加 15% 作為到終點的估計
            track_length = max_dist * 1.15
            logger.info("[throttle_trace_MDI] 從彎道數據估算賽道長度: %.0fm", track_length)
            return track_length
        
        # 如果範圍很大，說明是多圈累積距離
        # 使用最小距離作為第一個彎道位置的估計
        # 假設第一個彎道在單圈 10%-20% 處
        estimated_track_length = min_dist / 0.5  # 假設 T1 在單圈 50% 處（保守估計）
        
        # 驗證：如果估算的賽道長度不在合理範圍內，調整
        if estimated_track_length < 3000 or estimated_track_length > 8000:
            # 使用彎道間距來估算
            # F1 賽道通常有 10-20 個彎道，平均每個彎道間隔 300-500m
            estimated_track_length = len(corners) * 350
        
        logger.info("[throttle_trace_MDI] 從彎道分布估算賽道長度: %.0fm", estimated_track_length)
        return estimated_track_length
    
    def _process_corners_from_json(self, corners: List[Dict], track_length: float = 5000.0) -> List[Dict]:
        """
        處理 JSON 中的彎道資料
        優先使用 FastF1 原始的 'distance' 欄位（單圈距離）
        
        JSON 彎道資料由 CLI -f 2 (track_position_analysis) 生成
        包含欄位：
        - distance: FastF1 原始單圈距離（正確值，新版本）
        - mapped_distance: 多圈累積距離（舊版本，需要轉換為單圈距離）
        - lap_distance: 向後相容欄位
        
        Args:
            corners: 彎道資料列表
            track_length: 賽道長度（用於 mapped_distance 轉換）
        """
        if not corners:
            return corners
        
        result = []
        
        for corner in corners:
            corner_num = corner.get('number', 0)
            
            # 優先使用 'distance' 欄位（FastF1 單圈距離）
            lap_distance = corner.get('distance', 0)
            
            # 如果沒有 distance，嘗試 lap_distance（向後相容）
            if lap_distance == 0:
                lap_distance = corner.get('lap_distance', 0)
            
            # 如果還是沒有，使用 mapped_distance 並轉換為單圈距離
            if lap_distance <= 0:
                mapped_dist = corner.get('mapped_distance', 0)
                if mapped_dist > 0 and track_length > 0:
                    # mapped_distance 是多圈累積距離，需要取模得到單圈距離
                    lap_distance = mapped_dist % track_length
                    logger.debug(
                        "[throttle_trace_MDI] T%d: mapped_distance=%.0fm -> lap_distance=%.0fm",
                        corner_num,
                        mapped_dist,
                        lap_distance,
                    )
            
            if lap_distance <= 0:
                logger.warning("[throttle_trace_MDI] T%d has no valid distance, skipping", corner_num)
                continue
            
            new_corner = corner.copy()
            new_corner['lap_distance'] = lap_distance
            result.append(new_corner)
        
        # 按單圈距離排序
        result.sort(key=lambda c: c.get('lap_distance', 0))
        
        logger.debug(
            "[throttle_trace_MDI] Processed corners: %s",
            [(c['number'], int(c.get('lap_distance', 0))) for c in result],
        )
        
        return result
    
    def _on_race_unloaded(self):
        """賽事卸載"""
        if hasattr(self, 'throttle_widget'):
            self.throttle_widget.clear()
    
    def clear(self):
        """清除資料"""
        if hasattr(self, 'throttle_widget'):
            self.throttle_widget.clear()
