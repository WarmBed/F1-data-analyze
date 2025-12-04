# -*- coding: utf-8 -*-
"""
Sector Time Comparison Widget - PyQt5 Native Drawing Version
=============================================================
Compares sector times between two drivers across laps.

Features:
- Driver 1 sector time curve (team color, solid line)
- Driver 2 sector time curve (team color, solid line)
- Difference display (gap between drivers)
- SC/VSC zones (yellow fill)
- Pit stop markers (vertical lines)
- Current lap indicator
- Interactive driver selection via context menu

Uses PyQt5 native QPainter for optimal real-time performance.
"""

import math
from typing import Optional, Dict, Any, List, Tuple

from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont,
    QPainterPath, QPolygonF
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QMenu, QAction, QComboBox
)

from core.gui_i18n import tr
from ..core.base_live_mdi import BaseLiveTimingMDI

# =============================================================================
# Color Palette
# =============================================================================
COLOR_BACKGROUND = '#1a1a1a'
COLOR_CHART_BG = '#242424'
COLOR_GRID = '#3a3a3a'
COLOR_AXIS = '#888888'
COLOR_TEXT = '#ffffff'
COLOR_TEXT_DIM = '#888888'

COLOR_DRIVER1_DEFAULT = '#00D2BE'  # Mercedes teal (default)
COLOR_DRIVER2_DEFAULT = '#DC0000'  # Ferrari red (default)
COLOR_SC_ZONE = '#FFD700'          # Yellow - SC/VSC zones
COLOR_PIT_MARKER = '#FFD700'       # Yellow - pit stop markers
COLOR_CURRENT_LAP = '#4ECDC4'      # Cyan - current lap indicator
COLOR_DIFF_POSITIVE = '#FF6B6B'    # Red - driver 1 slower
COLOR_DIFF_NEGATIVE = '#4ECDC4'    # Green - driver 1 faster


# =============================================================================
# SectorComparisonWidget - Main PyQt5 Native Drawing Widget
# =============================================================================
class SectorComparisonWidget(QWidget):
    """
    Sector time comparison visualization using PyQt5 native drawing.
    
    Displays sector times for two drivers with difference indicators,
    SC zones, and pit markers.
    """
    
    # Signals
    error_occurred = pyqtSignal(str)
    data_updated = pyqtSignal()
    driver_change_requested = pyqtSignal(int, str)  # (driver_slot 1 or 2, driver_code)
    
    def __init__(self, sector_number: int = 1, parent=None):
        super().__init__(parent)
        
        # Sector number (1, 2, or 3)
        self._sector_number = sector_number
        
        # Chart area margins
        self._margin_left = 55
        self._margin_right = 20
        self._margin_top = 50   # Space for info bar
        self._margin_bottom = 35
        
        # Available drivers for context menu
        self._available_drivers: Dict[str, Dict[str, Any]] = {}
        
        # Data storage
        self._total_laps: int = 0
        self._current_lap: int = 0
        
        # Driver 1 info
        self._driver1_code: str = ""
        self._driver1_name: str = ""
        self._driver1_color: str = COLOR_DRIVER1_DEFAULT
        
        # Driver 2 info
        self._driver2_code: str = ""
        self._driver2_name: str = ""
        self._driver2_color: str = COLOR_DRIVER2_DEFAULT
        
        # Sector times: {lap_number: sector_time_seconds}
        self._driver1_sector_times: Dict[int, float] = {}
        self._driver2_sector_times: Dict[int, float] = {}
        
        # Pit stop laps for each driver
        self._driver1_pit_laps: List[int] = []
        self._driver2_pit_laps: List[int] = []
        
        # SC/VSC zones: [(start_lap, end_lap), ...]
        self._sc_zones: List[Tuple[int, int]] = []
        
        # SC lap set for exclusion
        self._sc_laps: set = set()
        
        # Y-axis range (sector time in seconds)
        self._y_min: float = 0.0
        self._y_max: float = 40.0
        
        # Cached fonts
        self._font_title = QFont("Microsoft YaHei", 10, QFont.Bold)
        self._font_label = QFont("Microsoft YaHei", 9)
        self._font_axis = QFont("Microsoft YaHei", 8)
        self._font_diff = QFont("Microsoft YaHei", 9, QFont.Bold)
        
        # Initialize UI
        self._setup_ui()
        
        self.setMinimumSize(400, 250)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def _setup_ui(self):
        """Setup the main UI layout (Speed Trace style)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # 頂部資訊列 (info bar)
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        # Sector title
        sector_title = QLabel(f"S{self._sector_number}")
        sector_title.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(sector_title)
        
        # Driver 1 label
        self._driver1_label = QLabel("Driver 1: --")
        self._driver1_label.setStyleSheet(f"color: {self._driver1_color}; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(self._driver1_label)
        
        # VS label
        vs_label = QLabel("vs")
        vs_label.setStyleSheet("color: #888888; font-size: 10px;")
        info_layout.addWidget(vs_label)
        
        # Driver 2 label
        self._driver2_label = QLabel("Driver 2: --")
        self._driver2_label.setStyleSheet(f"color: {self._driver2_color}; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(self._driver2_label)
        
        info_layout.addStretch()
        
        # Gap display
        self._gap_label = QLabel("Gap: --")
        self._gap_label.setStyleSheet("color: #4ECDC4; font-size: 11px;")
        info_layout.addWidget(self._gap_label)
        
        # Lap counter
        self._lap_label = QLabel("Lap: 0/0")
        self._lap_label.setStyleSheet("color: white; font-size: 11px;")
        info_layout.addWidget(self._lap_label)
        
        layout.addLayout(info_layout)
        
        # 圖表區域使用 stretch 讓它佔據剩餘空間
        layout.addStretch()
        
        # 設置背景色
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        
        # Right-click menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addLayout(info_layout)
        
    def _show_context_menu(self, pos):
        """Show context menu for driver selection."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
            }
            QMenu::item:selected {
                background-color: #444;
            }
        """)
        
        # Driver 1 submenu
        driver1_menu = menu.addMenu(f"{tr('Driver')} 1: {self._driver1_code or '--'}")
        for code, info in self._available_drivers.items():
            action = driver1_menu.addAction(f"{code} - {info.get('name', '')}")
            action.setData(('driver1', code))
            action.triggered.connect(lambda checked, c=code: self._on_driver_selected(1, c))
        
        # Driver 2 submenu
        driver2_menu = menu.addMenu(f"{tr('Driver')} 2: {self._driver2_code or '--'}")
        for code, info in self._available_drivers.items():
            action = driver2_menu.addAction(f"{code} - {info.get('name', '')}")
            action.setData(('driver2', code))
            action.triggered.connect(lambda checked, c=code: self._on_driver_selected(2, c))
        
        menu.exec_(self.mapToGlobal(pos))
        
    def _on_driver_selected(self, slot: int, driver_code: str):
        """Handle driver selection from context menu."""
        self.driver_change_requested.emit(slot, driver_code)
        
    # =========================================================================
    # Data Setters
    # =========================================================================
    
    def set_available_drivers(self, drivers: Dict[str, Dict[str, Any]]):
        """Set available drivers for selection."""
        self._available_drivers = drivers
        
    def set_total_laps(self, laps: int):
        """Set total laps for the race."""
        self._total_laps = laps
        self._update_lap_label()
        self.update()
        
    def set_current_lap(self, lap: int):
        """Set current lap."""
        self._current_lap = lap
        self._update_lap_label()
        self.update()
        
    def _update_lap_label(self):
        """Update lap counter label."""
        self._lap_label.setText(f"{tr('Lap')}: {self._current_lap}/{self._total_laps}")
        
    def set_driver1_info(self, driver_code: str, driver_name: str = "", team_color: str = ""):
        """Set driver 1 information."""
        self._driver1_code = driver_code
        self._driver1_name = driver_name or driver_code
        self._driver1_color = f"#{team_color}" if team_color else COLOR_DRIVER1_DEFAULT
        
        self._driver1_label.setText(f"{self._driver1_code}")
        self._driver1_label.setStyleSheet(f"color: {self._driver1_color}; font-weight: bold; font-size: 10px;")
        self.update()
        
    def set_driver2_info(self, driver_code: str, driver_name: str = "", team_color: str = ""):
        """Set driver 2 information."""
        self._driver2_code = driver_code
        self._driver2_name = driver_name or driver_code
        self._driver2_color = f"#{team_color}" if team_color else COLOR_DRIVER2_DEFAULT
        
        self._driver2_label.setText(f"{self._driver2_code}")
        self._driver2_label.setStyleSheet(f"color: {self._driver2_color}; font-weight: bold; font-size: 10px;")
        self.update()
        
    def add_driver1_sector_time(self, lap: int, sector_time: float):
        """Add sector time for driver 1."""
        if sector_time > 0:
            self._driver1_sector_times[lap] = sector_time
            self._update_y_range()
            self._update_gap_display()
            self.update()
            
    def add_driver2_sector_time(self, lap: int, sector_time: float):
        """Add sector time for driver 2."""
        if sector_time > 0:
            self._driver2_sector_times[lap] = sector_time
            self._update_y_range()
            self._update_gap_display()
            self.update()
            
    def set_driver1_pit_laps(self, pit_laps: List[int]):
        """Set pit stop laps for driver 1."""
        self._driver1_pit_laps = pit_laps
        self.update()
        
    def set_driver2_pit_laps(self, pit_laps: List[int]):
        """Set pit stop laps for driver 2."""
        self._driver2_pit_laps = pit_laps
        self.update()
        
    def add_sc_zone(self, start_lap: int, end_lap: int):
        """Add SC/VSC zone."""
        self._sc_zones.append((start_lap, end_lap))
        for lap in range(start_lap, end_lap + 1):
            self._sc_laps.add(lap)
        self.update()
        
    def add_sc_lap(self, lap_number: int):
        """
        Add a SC/VSC lap and update zones.
        Matches Driver Strategy pattern.
        """
        if lap_number in self._sc_laps:
            return  # Already recorded
        self._sc_laps.add(lap_number)
        self._update_sc_zone(lap_number)
        self.update()
        
    def _update_sc_zone(self, lap_number: int):
        """
        Update SC/VSC zones with the given lap.
        Converts individual SC laps into continuous zones for drawing.
        """
        if not self._sc_zones:
            self._sc_zones.append((lap_number, lap_number))
        else:
            # Extend the last zone if consecutive
            last_start, last_end = self._sc_zones[-1]
            if lap_number == last_end + 1:
                self._sc_zones[-1] = (last_start, lap_number)
            elif lap_number > last_end + 1:
                self._sc_zones.append((lap_number, lap_number))
                
    def set_sc_laps(self, sc_laps: set):
        """
        Set SC laps from external source and generate zones.
        Used for historical data loading.
        """
        self._sc_laps = sc_laps
        self._generate_sc_zones_from_laps()
        self.update()
        
    def _generate_sc_zones_from_laps(self):
        """
        Generate _sc_zones list from _sc_laps set.
        Converts individual SC laps into continuous zones for drawing.
        """
        self._sc_zones.clear()
        if not self._sc_laps:
            return
            
        sorted_laps = sorted(self._sc_laps)
        if not sorted_laps:
            return
            
        # Build zones from consecutive laps
        zone_start = sorted_laps[0]
        zone_end = sorted_laps[0]
        
        for lap in sorted_laps[1:]:
            if lap == zone_end + 1:
                # Extend current zone
                zone_end = lap
            else:
                # Save current zone and start new one
                self._sc_zones.append((zone_start, zone_end))
                zone_start = lap
                zone_end = lap
        
        # Don't forget the last zone
        self._sc_zones.append((zone_start, zone_end))
        print(f"[SECTOR_COMPARISON] Generated SC zones: {self._sc_zones}")
        
    def clear_data(self):
        """Clear all data."""
        self._driver1_sector_times.clear()
        self._driver2_sector_times.clear()
        self._driver1_pit_laps.clear()
        self._driver2_pit_laps.clear()
        self._sc_zones.clear()
        self._sc_laps.clear()
        self._current_lap = 0
        self._y_min = 0.0
        self._y_max = 40.0
        self.update()
        
    def _update_y_range(self):
        """Update Y-axis range based on data."""
        all_times = list(self._driver1_sector_times.values()) + list(self._driver2_sector_times.values())
        
        if all_times:
            min_time = min(all_times)
            max_time = max(all_times)
            margin = (max_time - min_time) * 0.15
            self._y_min = max(0, min_time - margin - 0.5)
            self._y_max = max_time + margin + 0.5
        else:
            self._y_min = 20.0
            self._y_max = 40.0
            
    def _update_gap_display(self):
        """Update gap display with latest sector time difference."""
        if not self._driver1_sector_times or not self._driver2_sector_times:
            self._gap_label.setText(f"{tr('Gap')}: --")
            return
            
        # Find latest common lap
        common_laps = set(self._driver1_sector_times.keys()) & set(self._driver2_sector_times.keys())
        if not common_laps:
            self._gap_label.setText(f"{tr('Gap')}: --")
            return
            
        latest_lap = max(common_laps)
        d1_time = self._driver1_sector_times[latest_lap]
        d2_time = self._driver2_sector_times[latest_lap]
        gap = d1_time - d2_time  # Positive = driver 1 slower
        
        sign = "+" if gap >= 0 else ""
        color = COLOR_DIFF_POSITIVE if gap >= 0 else COLOR_DIFF_NEGATIVE
        self._gap_label.setText(f"{tr('Gap')}: {sign}{gap:.3f}s")
        self._gap_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 10px;")
        
    # =========================================================================
    # PyQt5 Native Drawing
    # =========================================================================
    
    def paintEvent(self, event):
        """繪製圖表 (Speed Trace style)"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 清空背景
            painter.fillRect(self.rect(), QColor(COLOR_BACKGROUND))
            
            # 計算圖表區域
            chart_rect = QRectF(
                self._margin_left,
                self._margin_top,
                self.width() - self._margin_left - self._margin_right,
                self.height() - self._margin_top - self._margin_bottom
            )
            
            if chart_rect.width() <= 0 or chart_rect.height() <= 0:
                return
            
            # 繪製圖表背景
            painter.fillRect(chart_rect, QColor(COLOR_CHART_BG))
            
            # 繪製順序
            self._draw_grid(painter, chart_rect)
            self._draw_sc_zones(painter, chart_rect)
            self._draw_driver_curve(painter, chart_rect, self._driver1_sector_times, 
                                    self._driver1_color, self._driver1_pit_laps)
            self._draw_driver_curve(painter, chart_rect, self._driver2_sector_times, 
                                    self._driver2_color, self._driver2_pit_laps)
            self._draw_gap_labels(painter, chart_rect)  # Driver Strategy 風格的 gap 標籤
            self._draw_pit_markers(painter, chart_rect)
            self._draw_current_lap_indicator(painter, chart_rect)
            self._draw_axes(painter, chart_rect)
            self._draw_legend(painter, chart_rect)
            
        finally:
            painter.end()
        
    def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
        """Draw grid lines."""
        pen = QPen(QColor(COLOR_GRID))
        pen.setStyle(Qt.DotLine)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Horizontal grid lines (Y-axis)
        y_range = self._y_max - self._y_min
        if y_range <= 0:
            return
            
        tick_interval = self._calculate_tick_interval(y_range)
        
        y_start = math.ceil(self._y_min / tick_interval) * tick_interval
        y = y_start
        while y <= self._y_max:
            py = self._value_to_y(y, chart_rect)
            painter.drawLine(QPointF(chart_rect.left(), py), QPointF(chart_rect.right(), py))
            y += tick_interval
            
        # Vertical grid lines (X-axis / laps)
        if self._total_laps > 0:
            lap_interval = max(1, self._total_laps // 10)
            for lap in range(0, self._total_laps + 1, lap_interval):
                if lap == 0:
                    continue
                px = self._lap_to_x(lap, chart_rect)
                painter.drawLine(QPointF(px, chart_rect.top()), QPointF(px, chart_rect.bottom()))
                
    def _draw_sc_zones(self, painter: QPainter, chart_rect: QRectF):
        """Draw SC/VSC zones as yellow fills."""
        if not self._sc_zones or self._total_laps <= 0:
            return
            
        color = QColor(COLOR_SC_ZONE)
        color.setAlpha(50)  # 半透明
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        for start_lap, end_lap in self._sc_zones:
            x1 = self._lap_to_x(start_lap - 0.5, chart_rect)
            x2 = self._lap_to_x(end_lap + 0.5, chart_rect)
            painter.drawRect(QRectF(x1, chart_rect.top(), x2 - x1, chart_rect.height()))
            
            # Draw "SC" label at top of zone
            painter.setFont(self._font_label)
            painter.setPen(QColor(COLOR_SC_ZONE))
            mid_x = (x1 + x2) / 2
            painter.drawText(QPointF(mid_x - 8, chart_rect.top() + 15), "SC")
            
    def _draw_driver_curve(self, painter: QPainter, chart_rect: QRectF,
                           sector_times: Dict[int, float], color: str, pit_laps: List[int]):
        """Draw sector time curve for a driver."""
        if not sector_times or self._total_laps <= 0:
            return
            
        # Collect valid points (excluding SC laps)
        points = []
        for lap in sorted(sector_times.keys()):
            if lap in self._sc_laps:
                continue
            time = sector_times[lap]
            x = self._lap_to_x(lap, chart_rect)
            y = self._value_to_y(time, chart_rect)
            points.append((x, y, lap))
            
        if len(points) < 1:
            return
            
        # Draw line segments
        pen = QPen(QColor(color))
        pen.setWidth(2)
        painter.setPen(pen)
        
        for i in range(len(points) - 1):
            x1, y1, lap1 = points[i]
            x2, y2, lap2 = points[i + 1]
            
            # Check if there's a pit stop between these laps
            has_pit = any(lap1 < pit <= lap2 for pit in pit_laps)
            
            if has_pit:
                # Dashed line through pit stop
                pen.setStyle(Qt.DashLine)
            else:
                pen.setStyle(Qt.SolidLine)
                
            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            
        # Draw circle markers
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(color)))
        
        for x, y, lap in points:
            painter.drawEllipse(QPointF(x, y), 2, 2)
            
    def _draw_gap_labels(self, painter: QPainter, chart_rect: QRectF):
        """
        Draw gap labels on data points (Driver Strategy style).
        在每個共同圈數的數據點上方顯示差異標籤
        """
        if not self._driver1_sector_times or not self._driver2_sector_times:
            return
            
        if self._total_laps <= 0:
            return
            
        # 找出共同的圈數
        common_laps = set(self._driver1_sector_times.keys()) & set(self._driver2_sector_times.keys())
        if not common_laps:
            return
            
        # 只在最新的圈數顯示 gap 標籤 (Driver Strategy 風格)
        latest_lap = max(common_laps)
        
        # 跳過 SC 圈
        if latest_lap in self._sc_laps:
            # 嘗試找上一個有效圈
            valid_laps = [l for l in common_laps if l not in self._sc_laps]
            if not valid_laps:
                return
            latest_lap = max(valid_laps)
        
        d1_time = self._driver1_sector_times[latest_lap]
        d2_time = self._driver2_sector_times[latest_lap]
        gap = d1_time - d2_time  # Positive = driver 1 slower
        
        # 計算 driver 1 的點位置
        x = self._lap_to_x(latest_lap, chart_rect)
        y1 = self._value_to_y(d1_time, chart_rect)
        y2 = self._value_to_y(d2_time, chart_rect)
        
        # 格式化 gap 文字
        sign = "+" if gap >= 0 else ""
        gap_text = f"{sign}{gap:.3f}s"
        
        # 顏色：紅色 = driver 1 較慢，綠色 = driver 1 較快
        color = QColor(COLOR_DIFF_POSITIVE) if gap >= 0 else QColor(COLOR_DIFF_NEGATIVE)
        
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.setPen(color)
        
        # 在兩個點之間顯示 gap 標籤
        mid_y = (y1 + y2) / 2
        
        # 確保標籤在圖表區域內
        label_y = mid_y
        if label_y < chart_rect.top() + 15:
            label_y = chart_rect.top() + 15
        elif label_y > chart_rect.bottom() - 5:
            label_y = chart_rect.bottom() - 5
            
        # 繪製標籤 (在點的右側)
        painter.drawText(QPointF(x + 6, label_y + 4), gap_text)
            
    def _draw_pit_markers(self, painter: QPainter, chart_rect: QRectF):
        """Draw pit stop markers."""
        if self._total_laps <= 0:
            return
            
        # Driver 1 pit markers
        for lap in self._driver1_pit_laps:
            self._draw_single_pit_marker(painter, chart_rect, lap, self._driver1_color)
            
        # Driver 2 pit markers
        for lap in self._driver2_pit_laps:
            self._draw_single_pit_marker(painter, chart_rect, lap, self._driver2_color, offset=8)
            
    def _draw_single_pit_marker(self, painter: QPainter, chart_rect: QRectF, 
                                 lap: int, color: str, offset: int = 0):
        """Draw a single pit marker."""
        x = self._lap_to_x(lap, chart_rect) + offset
        
        pen = QPen(QColor(color))
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        painter.drawLine(QPointF(x, chart_rect.top()), QPointF(x, chart_rect.bottom()))
        
        # Draw "PIT" label at top (above chart)
        painter.setFont(QFont("Microsoft YaHei", 7))
        painter.setPen(QColor(color))
        painter.drawText(QPointF(x - 8, chart_rect.top() - 3), "PIT")
        
    def _draw_current_lap_indicator(self, painter: QPainter, chart_rect: QRectF):
        """Draw current lap indicator."""
        if self._current_lap <= 0 or self._total_laps <= 0:
            return
            
        x = self._lap_to_x(self._current_lap, chart_rect)
        
        pen = QPen(QColor(COLOR_CURRENT_LAP))
        pen.setWidth(1)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        
        painter.drawLine(QPointF(x, chart_rect.top()), QPointF(x, chart_rect.bottom()))
        
    def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
        """Draw axis labels."""
        painter.setFont(self._font_axis)
        painter.setPen(QColor(COLOR_AXIS))
        
        # Y-axis labels (sector time)
        y_range = self._y_max - self._y_min
        if y_range > 0:
            tick_interval = self._calculate_tick_interval(y_range)
            y_start = math.ceil(self._y_min / tick_interval) * tick_interval
            y = y_start
            while y <= self._y_max:
                py = self._value_to_y(y, chart_rect)
                label = f"{y:.1f}s"
                painter.drawText(QPointF(5, py + 4), label)
                y += tick_interval
                
        # X-axis labels (laps)
        if self._total_laps > 0:
            lap_interval = max(1, self._total_laps // 10)
            for lap in range(0, self._total_laps + 1, lap_interval):
                if lap == 0:
                    continue
                px = self._lap_to_x(lap, chart_rect)
                painter.drawText(QPointF(px - 8, chart_rect.bottom() + 14), str(lap))
                
        # X-axis title
        painter.drawText(QPointF(chart_rect.center().x() - 15, self.height() - 3), tr("Lap"))
        
    def _draw_legend(self, painter: QPainter, chart_rect: QRectF):
        """Draw legend without background (transparent style)."""
        legends = []
        
        if self._driver1_code:
            legends.append((self._driver1_code, self._driver1_color))
        if self._driver2_code:
            legends.append((self._driver2_code, self._driver2_color))
            
        if not legends:
            return
        
        # Legend position (top-right corner)
        legend_x = chart_rect.right() - 60
        legend_y = chart_rect.top() + 14
        
        # Draw legend items (no background, no border)
        painter.setFont(self._font_label)
        y_offset = legend_y
        
        for label, color in legends:
            # Color dot
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawEllipse(QPointF(legend_x, y_offset - 3), 4, 4)
            
            # Text
            painter.setPen(QColor('#FFFFFF'))
            painter.drawText(QPointF(legend_x + 10, y_offset), label)
            
            y_offset += 16
        
    # =========================================================================
    # Coordinate Transformations
    # =========================================================================
    
    def _lap_to_x(self, lap: float, chart_rect: QRectF) -> float:
        """Convert lap number to X coordinate."""
        if self._total_laps <= 0:
            return chart_rect.left()
        return chart_rect.left() + (lap / self._total_laps) * chart_rect.width()
        
    def _value_to_y(self, value: float, chart_rect: QRectF) -> float:
        """Convert sector time to Y coordinate."""
        y_range = self._y_max - self._y_min
        if y_range <= 0:
            return chart_rect.center().y()
        normalized = (value - self._y_min) / y_range
        return chart_rect.bottom() - normalized * chart_rect.height()
        
    def _calculate_tick_interval(self, range_val: float) -> float:
        """Calculate nice tick interval for axis."""
        if range_val <= 0:
            return 1.0
        magnitude = 10 ** math.floor(math.log10(range_val))
        normalized = range_val / magnitude
        
        if normalized <= 2:
            return 0.2 * magnitude
        elif normalized <= 5:
            return 0.5 * magnitude
        else:
            return 1.0 * magnitude


# =============================================================================
# SectorComparisonMDI - MDI Wrapper for Live Timing Integration
# =============================================================================
class SectorComparisonMDI(BaseLiveTimingMDI):
    """
    MDI wrapper for Sector Comparison widget.
    Integrates with Live Timing data flow via BaseLiveTimingMDI.
    
    繼承 BaseLiveTimingMDI 以自動訂閱 DataManager 信號：
    - snapshot_updated: 接收 sector 時間更新
    - race_loaded: 接收賽事資訊
    """
    
    MODULE_ID = "live_timing_sector_comparison"
    DEFAULT_TITLE = "Sector Comparison"
    
    def __init__(self, sector_number: int = 1, parent=None, data_manager=None):
        # 必須先設置 sector_number，因為 _setup_ui 會用到
        self._sector_number = sector_number
        
        super().__init__(parent, data_manager)
        
        # Window title
        self.setWindowTitle(f"S{sector_number} {tr('Comparison')}")
        self.setMinimumSize(450, 280)
        self.resize(500, 320)
        
        # Driver data cache for all drivers
        # 格式: {driver_code: {name, team_color, sector1_times: {lap: time}, pit_laps: [...]}}
        self._all_drivers_data: Dict[str, Dict[str, Any]] = {}
        
        # Selected drivers
        self._driver1_code: str = ""
        self._driver2_code: str = ""
        
        # 當前圈數追蹤
        self._current_lap: int = 0
        self._total_laps: int = 0
        
        # 已處理的 sector 時間記錄 (避免重複處理)
        # 格式: {(driver_num, lap): sector_time}
        self._processed_sectors: Dict[Tuple[str, int], float] = {}
        
        # 車手位置追蹤 (用於自動選擇 P1/P2)
        # 格式: {driver_code: position}
        self._driver_positions: Dict[str, int] = {}
        
        # 是否已自動選擇車手
        self._auto_selected = False
        
        # SC/VSC 追蹤
        self._sc_laps: set = set()  # SC/VSC 圈數集合
        self._sc_restart_laps: set = set()  # SC 重啟圈
        self._current_race_time: str = ""  # 當前賽事時間 (字串格式，如 "01:18:42")
        
        print(f"[SECTOR_COMPARISON_MDI] S{sector_number} Comparison initialized")
        
    def _setup_ui(self):
        """Setup UI components - 由 BaseLiveTimingMDI 調用"""
        self._widget = SectorComparisonWidget(sector_number=self._sector_number)
        self._main_layout.addWidget(self._widget)
        
        # Connect widget signals
        self._widget.driver_change_requested.connect(self._on_driver_change_requested)
        
    def _on_driver_change_requested(self, slot: int, driver_code: str):
        """Handle driver selection from widget."""
        if slot == 1:
            self._select_driver1(driver_code)
        else:
            self._select_driver2(driver_code)
            
    def _select_driver1(self, driver_code: str):
        """Select driver 1 and update display."""
        self._driver1_code = driver_code
        
        if driver_code in self._all_drivers_data:
            info = self._all_drivers_data[driver_code]
            self._widget.set_driver1_info(
                driver_code,
                info.get('name', ''),
                info.get('team_color', '')
            )
            
            # Load sector times (filter out SC and SC restart laps)
            sector_key = f"sector{self._sector_number}_times"
            if sector_key in info:
                for lap, time in info[sector_key].items():
                    lap_int = int(lap)
                    # Skip SC laps and SC restart laps
                    if lap_int in self._sc_laps:
                        continue
                    if lap_int in self._sc_restart_laps:
                        continue
                    self._widget.add_driver1_sector_time(lap_int, float(time))
                    
            # Load pit laps
            if 'pit_laps' in info:
                self._widget.set_driver1_pit_laps(info['pit_laps'])
                
    def _select_driver2(self, driver_code: str):
        """Select driver 2 and update display."""
        self._driver2_code = driver_code
        
        if driver_code in self._all_drivers_data:
            info = self._all_drivers_data[driver_code]
            self._widget.set_driver2_info(
                driver_code,
                info.get('name', ''),
                info.get('team_color', '')
            )
            
            # Load sector times (filter out SC and SC restart laps)
            sector_key = f"sector{self._sector_number}_times"
            if sector_key in info:
                for lap, time in info[sector_key].items():
                    lap_int = int(lap)
                    # Skip SC laps and SC restart laps
                    if lap_int in self._sc_laps:
                        continue
                    if lap_int in self._sc_restart_laps:
                        continue
                    self._widget.add_driver2_sector_time(lap_int, float(time))
                    
            # Load pit laps
            if 'pit_laps' in info:
                self._widget.set_driver2_pit_laps(info['pit_laps'])
                
    # =========================================================================
    # Public API for Live Timing Integration
    # =========================================================================
    
    def set_total_laps(self, laps: int):
        """Set total laps."""
        self._widget.set_total_laps(laps)
        
    def set_current_lap(self, lap: int):
        """Set current lap."""
        self._widget.set_current_lap(lap)
        
    def set_available_drivers(self, drivers: Dict[str, Dict[str, Any]]):
        """Set available drivers for selection."""
        self._all_drivers_data = drivers
        self._widget.set_available_drivers(drivers)
        
    def update_driver_sector_time(self, driver_code: str, lap: int, sector_time: float):
        """Update sector time for a driver."""
        # Store in cache
        if driver_code not in self._all_drivers_data:
            self._all_drivers_data[driver_code] = {}
            
        sector_key = f"sector{self._sector_number}_times"
        if sector_key not in self._all_drivers_data[driver_code]:
            self._all_drivers_data[driver_code][sector_key] = {}
            
        self._all_drivers_data[driver_code][sector_key][lap] = sector_time
        
        # Update widget if this driver is selected
        if driver_code == self._driver1_code:
            self._widget.add_driver1_sector_time(lap, sector_time)
        elif driver_code == self._driver2_code:
            self._widget.add_driver2_sector_time(lap, sector_time)
            
    def update_driver_pit(self, driver_code: str, lap: int):
        """Record pit stop for a driver."""
        if driver_code not in self._all_drivers_data:
            self._all_drivers_data[driver_code] = {}
            
        if 'pit_laps' not in self._all_drivers_data[driver_code]:
            self._all_drivers_data[driver_code]['pit_laps'] = []
            
        if lap not in self._all_drivers_data[driver_code]['pit_laps']:
            self._all_drivers_data[driver_code]['pit_laps'].append(lap)
            
        # Update widget if this driver is selected
        if driver_code == self._driver1_code:
            self._widget.set_driver1_pit_laps(self._all_drivers_data[driver_code]['pit_laps'])
        elif driver_code == self._driver2_code:
            self._widget.set_driver2_pit_laps(self._all_drivers_data[driver_code]['pit_laps'])
            
    def add_sc_zone(self, start_lap: int, end_lap: int):
        """Add SC/VSC zone."""
        self._widget.add_sc_zone(start_lap, end_lap)
        
    def clear(self):
        """Clear all data."""
        self._all_drivers_data.clear()
        self._driver1_code = ""
        self._driver2_code = ""
        self._widget.clear_data()
        
    def select_drivers(self, driver1_code: str, driver2_code: str):
        """Select two drivers for comparison."""
        self._select_driver1(driver1_code)
        self._select_driver2(driver2_code)
        
    # =========================================================================
    # BaseLiveTimingMDI 覆寫方法 - 數據流處理
    # =========================================================================
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """
        處理快照更新 - 從 DataManager 接收數據
        
        Snapshot 結構:
        {
            'race_time_seconds': float,
            'current_lap': int,
            'drivers': {
                'driver_num': {
                    'driver_code': str,  # e.g., 'VER'
                    'name': str,
                    'team_color': str,
                    'lap': int,
                    's1_time': str,  # e.g., '25.123'
                    's2_time': str,
                    's3_time': str,
                    's1_personal_fastest': bool,
                    's2_personal_fastest': bool,
                    's3_personal_fastest': bool,
                    'in_pit': bool,
                    ...
                }
            }
        }
        """
        if not hasattr(self, '_widget'):
            return
            
        drivers = snapshot.get('drivers', {})
        current_lap = snapshot.get('current_lap', 0)
        # 使用 'race_time' (字串格式) 而不是 'race_time_seconds' (float)
        # 因為 get_track_status_at_time() 需要字串格式
        self._current_race_time = snapshot.get('race_time', '')
        
        if current_lap > self._current_lap:
            self._current_lap = current_lap
            self._widget.set_current_lap(current_lap)
        
        # 檢查 SC/VSC 狀態 (從 DataManager 獲取)
        is_sc_lap = False
        is_vsc_lap = False
        if self._data_manager and self._current_race_time:
            track_status = self._data_manager.get_track_status_at_time(self._current_race_time)
            is_sc_lap = (track_status == '4')  # SC
            is_vsc_lap = (track_status == '6')  # VSC
        
        # 記錄 SC/VSC 圈 (在處理車手資料之前)
        if (is_sc_lap or is_vsc_lap) and current_lap > 0:
            if current_lap not in self._sc_laps:
                self._sc_laps.add(current_lap)
                self._widget.add_sc_lap(current_lap)
                print(f"[SECTOR_COMPARISON_MDI] S{self._sector_number} SC lap recorded: {current_lap}")
        # 檢查是否為 SC restart 圈 (前一圈是 SC)
        elif current_lap > 0 and (current_lap - 1) in self._sc_laps:
            if current_lap not in self._sc_restart_laps:
                self._sc_restart_laps.add(current_lap)
                print(f"[SECTOR_COMPARISON_MDI] S{self._sector_number} SC restart lap recorded: {current_lap}")
        
        # 決定要讀取哪個 sector 時間欄位
        sector_time_key = f's{self._sector_number}_time'
        
        for driver_num, driver_data in drivers.items():
            # 使用 driver_tla (如 VER, NOR) 而不是 driver_num (如 01, 04)
            driver_tla = driver_data.get('driver_tla', driver_num)
            driver_name = driver_data.get('driver_name', driver_tla)
            driver_lap = driver_data.get('lap', 0)
            sector_time_str = driver_data.get(sector_time_key)
            
            # 追蹤車手位置 (用於自動選擇 P1/P2)
            position = driver_data.get('position')
            if position is not None and driver_tla:
                try:
                    self._driver_positions[driver_tla] = int(position)
                except (ValueError, TypeError):
                    pass
            
            if not sector_time_str or not driver_lap:
                continue
                
            # 解析 sector 時間（可能是字串格式）
            try:
                if isinstance(sector_time_str, str):
                    sector_time = float(sector_time_str)
                else:
                    sector_time = float(sector_time_str)
            except (ValueError, TypeError):
                continue
                
            # 檢查是否已處理過這個 sector 時間
            cache_key = (driver_num, driver_lap)
            if cache_key in self._processed_sectors:
                if self._processed_sectors[cache_key] == sector_time:
                    continue  # 已處理，跳過
                    
            self._processed_sectors[cache_key] = sector_time
            
            # SC/VSC 圈不記錄 sector 時間 (與 Driver Strategy 一致)
            # 必須在存入 cache 之前檢查，避免歷史資料包含 SC 圈
            if driver_lap in self._sc_laps:
                print(f"[SECTOR_COMPARISON_MDI] S{self._sector_number} Skipping SC lap {driver_lap} for {driver_tla}")
                continue
                
            # SC restart 圈也不記錄 (前一圈是 SC)
            if driver_lap in self._sc_restart_laps:
                print(f"[SECTOR_COMPARISON_MDI] S{self._sector_number} Skipping SC restart lap {driver_lap} for {driver_tla}")
                continue
            
            # 更新車手資料快取 (使用 driver_tla 作為 key)
            # 只有非 SC 圈的數據才會存入 cache
            if driver_tla not in self._all_drivers_data:
                self._all_drivers_data[driver_tla] = {
                    'name': driver_name,
                    'team_color': driver_data.get('team_color', '#FFFFFF'),
                    'pit_laps': [],
                    f'sector{self._sector_number}_times': {}
                }
            else:
                # 更新 name 和 team_color（可能之前是空的）
                if driver_name:
                    self._all_drivers_data[driver_tla]['name'] = driver_name
                if driver_data.get('team_color'):
                    self._all_drivers_data[driver_tla]['team_color'] = driver_data['team_color']
                    
            # 添加 sector 時間 (已確認不是 SC 圈)
            sector_key = f'sector{self._sector_number}_times'
            if sector_key not in self._all_drivers_data[driver_tla]:
                self._all_drivers_data[driver_tla][sector_key] = {}
            self._all_drivers_data[driver_tla][sector_key][driver_lap] = sector_time
            
            # 如果這個車手已被選中，更新 widget
            if driver_tla == self._driver1_code:
                self._widget.add_driver1_sector_time(driver_lap, sector_time)
            elif driver_tla == self._driver2_code:
                self._widget.add_driver2_sector_time(driver_lap, sector_time)
                
            # 檢查進站狀態
            in_pit = driver_data.get('in_pit', False)
            if in_pit and driver_lap > 0:
                if 'pit_laps' not in self._all_drivers_data[driver_tla]:
                    self._all_drivers_data[driver_tla]['pit_laps'] = []
                if driver_lap not in self._all_drivers_data[driver_tla]['pit_laps']:
                    self._all_drivers_data[driver_tla]['pit_laps'].append(driver_lap)
                    
                    # 更新 widget
                    if driver_tla == self._driver1_code:
                        self._widget.set_driver1_pit_laps(self._all_drivers_data[driver_tla]['pit_laps'])
                    elif driver_tla == self._driver2_code:
                        self._widget.set_driver2_pit_laps(self._all_drivers_data[driver_tla]['pit_laps'])
        
        # 更新可選車手列表
        self._widget.set_available_drivers(self._all_drivers_data)
        
        # 自動選擇 P1 和 P2 車手 (只在尚未選擇時)
        if not self._auto_selected and len(self._driver_positions) >= 2:
            self._auto_select_p1_p2()
        
    def _auto_select_p1_p2(self):
        """
        自動選擇 P1 和 P2 車手
        與 Speed Trace 邏輯一致：P1 為主車手，P2 為對比車手
        """
        if not self._driver_positions:
            return
            
        # 按位置排序找出 P1 和 P2
        sorted_drivers = sorted(
            self._driver_positions.items(),
            key=lambda x: x[1] if x[1] is not None else 999
        )
        
        p1_driver = None
        p2_driver = None
        
        for driver_code, position in sorted_drivers:
            if position == 1:
                p1_driver = driver_code
            elif position == 2:
                p2_driver = driver_code
                
            if p1_driver and p2_driver:
                break
        
        # 如果找不到精確的 P1/P2，使用前兩名
        if not p1_driver and len(sorted_drivers) >= 1:
            p1_driver = sorted_drivers[0][0]
        if not p2_driver and len(sorted_drivers) >= 2:
            p2_driver = sorted_drivers[1][0]
            
        # 選擇車手
        if p1_driver and p1_driver != self._driver1_code:
            self._select_driver1(p1_driver)
            print(f"[SECTOR_COMPARISON_MDI] Auto-selected P1: {p1_driver}")
            
        if p2_driver and p2_driver != self._driver2_code:
            self._select_driver2(p2_driver)
            print(f"[SECTOR_COMPARISON_MDI] Auto-selected P2: {p2_driver}")
            
        if p1_driver or p2_driver:
            self._auto_selected = True
        
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """
        賽事載入完成
        
        race_info 結構:
        {
            'year': int,
            'race': str,
            'session': str,
            'total_laps': int,
            'driver_info': {...},
            ...
        }
        """
        total_laps = race_info.get('total_laps', 0)
        if total_laps > 0:
            self._total_laps = total_laps
            self._widget.set_total_laps(total_laps)
            
        # 預先載入車手資訊
        driver_info = race_info.get('driver_info', {})
        for driver_num, info in driver_info.items():
            # 使用 tla (如 VER) 而不是 driver_num (如 01)
            driver_tla = info.get('tla', info.get('driver_code', driver_num))
            driver_name = info.get('name', driver_tla)
            if driver_tla not in self._all_drivers_data:
                self._all_drivers_data[driver_tla] = {
                    'name': driver_name,
                    'team_color': info.get('team_color', '#FFFFFF'),
                    'pit_laps': [],
                    f'sector{self._sector_number}_times': {}
                }
                
        print(f"[SECTOR_COMPARISON_MDI] Race loaded: {race_info.get('year')} {race_info.get('race')}, total_laps={total_laps}")
        
    def _on_race_unloaded(self):
        """賽事卸載 - 清除數據"""
        self.clear()
        self._processed_sectors.clear()
        self._driver_positions.clear()
        self._sc_laps.clear()
        self._sc_restart_laps.clear()
        self._current_lap = 0
        self._total_laps = 0
        self._current_race_time = ""
        self._auto_selected = False
        print(f"[SECTOR_COMPARISON_MDI] Race unloaded, data cleared")


# =============================================================================
# Specialized MDI Classes for Factory Registration
# =============================================================================
class SectorComparisonS1MDI(SectorComparisonMDI):
    """Sector 1 Comparison MDI for factory registration."""
    
    MODULE_ID = "live_timing_sector_s1_comparison"
    DEFAULT_TITLE = "S1 Comparison"
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(sector_number=1, parent=parent, data_manager=data_manager)


class SectorComparisonS2MDI(SectorComparisonMDI):
    """Sector 2 Comparison MDI for factory registration."""
    
    MODULE_ID = "live_timing_sector_s2_comparison"
    DEFAULT_TITLE = "S2 Comparison"
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(sector_number=2, parent=parent, data_manager=data_manager)


class SectorComparisonS3MDI(SectorComparisonMDI):
    """Sector 3 Comparison MDI for factory registration."""
    
    MODULE_ID = "live_timing_sector_s3_comparison"
    DEFAULT_TITLE = "S3 Comparison"
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(sector_number=3, parent=parent, data_manager=data_manager)
