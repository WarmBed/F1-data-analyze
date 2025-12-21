# -*- coding: utf-8 -*-
"""
SF% History Chart - PyQt5 Native Drawing Version
=================================================
Displays SF% (Stint Fuel Saving Percentage) history for a single driver.

Features:
- SF% curve (gradient green: bright for positive, dark for negative)
- Threshold zones (-3% yellow fill, -5% red fill)
- White dashed threshold lines (0%, -3%, -5%)
- SC zones (yellow fill with label)
- PIT markers (dashed vertical lines)
- Right-click driver selection menu
- Dynamic Y-axis range

Uses PyQt5 native QPainter for optimal real-time performance.
Follows driver_strategy.py patterns for consistency.

Author: F1T Team
Date: 2025-12-21
"""

from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass, field

from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPainterPath, QLinearGradient
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QMenu, QAction
)

from core.gui_i18n import tr
from core.logger import get_logger
from ..core.base_live_mdi import BaseLiveTimingMDI
from ..core.hover_tooltip_mixin import HoverTooltipMixin, HoverInfo, HoverDataPoint

logger = get_logger("live_timing.sf_percentage_chart", component="gui")


# =============================================================================
# Color Constants (consistent with driver_strategy.py)
# =============================================================================
COLOR_BACKGROUND = '#1a1a1a'
COLOR_CHART_BG = '#2a2a2a'
COLOR_GRID = '#404040'
COLOR_TEXT = '#E0E0E0'
COLOR_AXIS = '#888888'

# SF% specific colors
COLOR_SF_POSITIVE = '#00FF88'      # Bright green for positive SF%
COLOR_SF_NEGATIVE = '#006633'      # Dark green for negative SF%
COLOR_THRESHOLD_LINE = '#FFFFFF'   # White threshold lines
COLOR_ZONE_YELLOW = '#FFFF00'      # -3% threshold zone
COLOR_ZONE_RED = '#FF0000'         # -5% threshold zone

# SC/PIT colors (same as driver_strategy)
COLOR_SC_ZONE = '#FFD700'
COLOR_PIT_MARKER = '#FFFF00'


# =============================================================================
# SF% Data Structure
# =============================================================================
@dataclass
class SFPercentageData:
    """SF% data for a single driver."""
    driver_num: str = ""
    driver_tla: str = ""
    driver_name: str = ""
    team_color: str = "FFFFFF"
    position: int = 0
    
    # SF% data per lap: {lap_num: sf_pct}
    lap_sf_data: Dict[int, float] = field(default_factory=dict)
    
    # Throttle data per lap: {lap_num: throttle_95_pct}
    lap_throttle_data: Dict[int, float] = field(default_factory=dict)
    
    # Baseline per lap: {lap_num: baseline}
    lap_baseline_data: Dict[int, float] = field(default_factory=dict)
    
    # Lamp status per lap: {lap_num: 'R'|'Y'|''}
    lap_lamp_data: Dict[int, str] = field(default_factory=dict)
    
    # PIT laps
    pit_laps: List[int] = field(default_factory=list)
    pit_out_laps: Set[int] = field(default_factory=set)
    
    # SC laps (global)
    sc_laps: Set[int] = field(default_factory=set)
    
    current_lap: int = 0
    
    def clear(self):
        """Clear all data."""
        self.lap_sf_data.clear()
        self.lap_throttle_data.clear()
        self.lap_baseline_data.clear()
        self.lap_lamp_data.clear()
        self.pit_laps.clear()
        self.pit_out_laps.clear()
        self.sc_laps.clear()
        self.current_lap = 0


# =============================================================================
# SF% Chart Widget
# =============================================================================
class SFPercentageChartWidget(HoverTooltipMixin, QWidget):
    """
    SF% History Chart Widget using PyQt5 native drawing.
    
    Displays SF% (Stint Fuel Saving Percentage) curve for a single driver.
    SF% indicates how much the driver is saving fuel compared to baseline.
    
    Negative SF% = fuel saving (throttle below baseline)
    Positive SF% = pushing harder (throttle above baseline)
    """
    
    # Signal emitted when user requests driver change
    driver_change_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Data
        self._data = SFPercentageData()
        self._available_drivers: Dict[str, Dict[str, Any]] = {}
        
        # Chart settings
        self._total_laps: int = 60  # Will be updated from race info
        self._y_min: float = -15.0  # Will be dynamic
        self._y_max: float = 5.0    # Will be dynamic
        
        # Threshold values
        self._threshold_medium: float = -3.0  # Yellow zone
        self._threshold_high: float = -5.0    # Red zone
        
        # Margins
        self._margin_left = 50
        self._margin_right = 15
        self._margin_top = 40
        self._margin_bottom = 30
        
        # Fonts
        self._font_title = QFont("Consolas", 10, QFont.Bold)
        self._font_axis = QFont("Consolas", 8)
        self._font_label = QFont("Consolas", 9, QFont.Bold)
        
        # SC zones for drawing
        self._sc_zones: List[Tuple[int, int]] = []
        
        # Setup UI
        self._init_ui()
        
        # Enable right-click context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Initialize hover tracking (from HoverTooltipMixin)
        self._init_hover_tracking()
        
        logger.info("[SF_CHART] SFPercentageChartWidget initialized")
    
    def _init_ui(self):
        """Initialize UI layout."""
        self.setMinimumSize(400, 250)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Info bar at top
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(5, 2, 5, 2)
        info_layout.setSpacing(15)
        
        # Title label
        self._title_label = QLabel("SF% History")
        self._title_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(self._title_label)
        
        # Current lap label
        self._lap_label = QLabel(f"{tr('lap_number')}: -")
        self._lap_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 10px;")
        info_layout.addWidget(self._lap_label)
        
        # Current SF% label
        self._sf_label = QLabel("SF%: -")
        self._sf_label.setStyleSheet(f"color: {COLOR_SF_POSITIVE}; font-weight: bold; font-size: 10px;")
        info_layout.addWidget(self._sf_label)
        
        # Current Baseline label
        self._baseline_label = QLabel("Baseline: -")
        self._baseline_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 10px;")
        info_layout.addWidget(self._baseline_label)
        
        info_layout.addStretch()
        layout.addWidget(info_frame)
        
        # Chart area (we draw directly on widget, so just spacer)
        layout.addStretch()
    
    # =========================================================================
    # Public Methods
    # =========================================================================
    
    def set_driver_info(self, driver_num: str, driver_tla: str = "", 
                        driver_name: str = "", team_color: str = "FFFFFF",
                        position: int = 0):
        """Set driver information."""
        self._data.driver_num = driver_num
        self._data.driver_tla = driver_tla or driver_num
        self._data.driver_name = driver_name
        self._data.team_color = team_color
        self._data.position = position
        
        # Update title: SF% History - #1 VER
        title = f"SF% History - #{position} {driver_tla}" if position else f"SF% History - {driver_tla}"
        self._title_label.setText(title)
        
        # Update title color with team color
        self._title_label.setStyleSheet(
            f"color: #{team_color}; font-weight: bold; font-size: 11px;"
        )
    
    def select_driver(self, driver_num: str, driver_tla: str = "",
                      driver_name: str = "", team_color: str = "FFFFFF",
                      position: int = 0):
        """Select a new driver and reset data."""
        self._data.clear()
        self.set_driver_info(driver_num, driver_tla, driver_name, team_color, position)
        self.update()
    
    def load_driver_history(self, 
                            lap_sf_data: Dict[int, float],
                            lap_throttle_data: Dict[int, float],
                            lap_baseline_data: Dict[int, float],
                            lap_lamp_data: Dict[int, str],
                            pit_laps: List[int],
                            pit_out_laps: Set[int],
                            sc_laps: Set[int],
                            current_lap: int = 0):
        """
        Load complete driver SF% history.
        
        Called when switching drivers to restore full history.
        """
        self._data.clear()
        self._data.lap_sf_data = lap_sf_data.copy() if lap_sf_data else {}
        self._data.lap_throttle_data = lap_throttle_data.copy() if lap_throttle_data else {}
        self._data.lap_baseline_data = lap_baseline_data.copy() if lap_baseline_data else {}
        self._data.lap_lamp_data = lap_lamp_data.copy() if lap_lamp_data else {}
        self._data.pit_laps = list(pit_laps) if pit_laps else []
        self._data.pit_out_laps = set(pit_out_laps) if pit_out_laps else set()
        self._data.sc_laps = set(sc_laps) if sc_laps else set()
        self._data.current_lap = current_lap
        
        # Generate SC zones for drawing
        self._generate_sc_zones_from_laps()
        
        # Update dynamic Y range
        self._update_y_range()
        
        # Update lap counter
        self._update_info_labels()
        
        self.update()
    
    def update_lap_data(self, lap_num: int, sf_pct: float, 
                        throttle_pct: float = 0, baseline: float = 0,
                        lamp: str = "", is_pit: bool = False,
                        is_sc: bool = False):
        """
        Update data for a specific lap.
        
        Args:
            lap_num: Lap number
            sf_pct: SF percentage (negative = saving)
            throttle_pct: Throttle 95% ratio
            baseline: Dynamic baseline
            lamp: Warning lamp ('R', 'Y', '')
            is_pit: Whether this is a pit lap
            is_sc: Whether this is a SC lap
        """
        # Skip PIT and SC laps for SF% calculation
        if is_pit:
            if lap_num not in self._data.pit_laps:
                self._data.pit_laps.append(lap_num)
            self._data.pit_out_laps.add(lap_num)
            if lap_num > 1:
                self._data.pit_out_laps.add(lap_num - 1)
            self._data.pit_out_laps.add(lap_num + 1)
        
        if is_sc:
            self._data.sc_laps.add(lap_num)
            self._generate_sc_zones_from_laps()
        
        # Only store SF% data for valid laps (not PIT/SC)
        if not is_pit and not is_sc and lap_num not in self._data.pit_out_laps:
            self._data.lap_sf_data[lap_num] = sf_pct
            if throttle_pct > 0:
                self._data.lap_throttle_data[lap_num] = throttle_pct
            if baseline > 0:
                self._data.lap_baseline_data[lap_num] = baseline
            if lamp:
                self._data.lap_lamp_data[lap_num] = lamp
        
        self._data.current_lap = max(self._data.current_lap, lap_num)
        
        # Update dynamic Y range
        self._update_y_range()
        
        # Update info labels
        self._update_info_labels()
        
        self.update()
    
    def update_from_snapshot(self, snapshot: Dict[str, Any]):
        """
        Update SF% data from live timing snapshot.
        
        Reads throttle_95_pct, throttle_baseline, fuel_saving_lamp from driver data.
        """
        drivers = snapshot.get('drivers', {})
        driver_data = drivers.get(self._data.driver_num, {})
        
        if not driver_data:
            return
        
        lap_num = driver_data.get('lap', 0)
        if not lap_num or lap_num <= 0:
            return
        
        try:
            lap_num = int(lap_num)
        except (ValueError, TypeError):
            return
        
        # Skip if already recorded this lap
        if lap_num in self._data.lap_sf_data:
            return
        
        # Get throttle data
        throttle_pct = driver_data.get('throttle_95_pct', 0)
        baseline = driver_data.get('throttle_baseline', 0)
        lamp = driver_data.get('fuel_saving_lamp', '')
        
        # Check PIT/SC status
        is_pit = driver_data.get('in_pit', False) or driver_data.get('pit_out', False)
        
        # Check if SC lap (from race control messages)
        is_sc = lap_num in self._data.sc_laps
        
        # Calculate SF% if we have valid data
        sf_pct = 0.0
        if baseline and baseline > 0 and throttle_pct > 0:
            sf_pct = ((throttle_pct - baseline) / baseline) * 100
        
        # Update lap data
        self.update_lap_data(lap_num, sf_pct, throttle_pct, baseline, lamp, is_pit, is_sc)
    
    def set_total_laps(self, total_laps: int):
        """Set total race laps for X-axis."""
        self._total_laps = max(total_laps, 10)
        self.update()
    
    def set_sc_laps(self, sc_laps: Set[int]):
        """Set SC laps from race control."""
        self._data.sc_laps = set(sc_laps)
        self._generate_sc_zones_from_laps()
        self.update()
    
    def set_available_drivers(self, drivers: Dict[str, Dict[str, Any]]):
        """Set available drivers for context menu selection."""
        self._available_drivers = drivers
    
    # =========================================================================
    # Private Methods
    # =========================================================================
    
    def _update_y_range(self):
        """Update Y-axis range dynamically based on data."""
        if not self._data.lap_sf_data:
            self._y_min = -10.0
            self._y_max = 5.0
            return
        
        values = list(self._data.lap_sf_data.values())
        min_val = min(values)
        max_val = max(values)
        
        # Add padding
        self._y_min = min(min_val - 2, -8.0)  # At least show -8%
        self._y_max = max(max_val + 2, 5.0)   # At least show +5%
        
        # Ensure thresholds are visible
        self._y_min = min(self._y_min, self._threshold_high - 2)
    
    def _update_info_labels(self):
        """Update info bar labels."""
        self._lap_label.setText(f"{tr('lap_number')}: {self._data.current_lap}")
        
        # Get latest SF%
        if self._data.current_lap in self._data.lap_sf_data:
            sf_pct = self._data.lap_sf_data[self._data.current_lap]
            lamp = self._data.lap_lamp_data.get(self._data.current_lap, '')
            
            # Color based on lamp status
            if lamp == 'R':
                color = COLOR_ZONE_RED
            elif lamp == 'Y':
                color = COLOR_ZONE_YELLOW
            else:
                color = COLOR_SF_POSITIVE
            
            self._sf_label.setText(f"SF%: {sf_pct:.1f}%")
            self._sf_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 10px;")
        else:
            self._sf_label.setText("SF%: -")
            self._sf_label.setStyleSheet(f"color: {COLOR_SF_POSITIVE}; font-weight: bold; font-size: 10px;")
        
        # Get latest Baseline
        if self._data.current_lap in self._data.lap_baseline_data:
            baseline_pct = self._data.lap_baseline_data[self._data.current_lap]
            self._baseline_label.setText(f"Baseline: {baseline_pct:.1f}%")
        else:
            self._baseline_label.setText("Baseline: -")
    
    def _generate_sc_zones_from_laps(self):
        """Generate contiguous SC zones from individual SC laps."""
        self._sc_zones.clear()
        
        if not self._data.sc_laps:
            return
        
        sorted_laps = sorted(self._data.sc_laps)
        if not sorted_laps:
            return
        
        # Group consecutive laps
        zone_start = sorted_laps[0]
        zone_end = sorted_laps[0]
        
        for lap in sorted_laps[1:]:
            if lap == zone_end + 1:
                zone_end = lap
            else:
                self._sc_zones.append((zone_start, zone_end))
                zone_start = lap
                zone_end = lap
        
        self._sc_zones.append((zone_start, zone_end))
    
    def _lap_to_x(self, lap: float, chart_rect: QRectF) -> float:
        """Convert lap number to X coordinate."""
        if self._total_laps <= 1:
            return chart_rect.left()
        
        ratio = (lap - 1) / (self._total_laps - 1)
        return chart_rect.left() + ratio * chart_rect.width()
    
    def _value_to_y(self, value: float, chart_rect: QRectF) -> float:
        """Convert SF% value to Y coordinate."""
        y_range = self._y_max - self._y_min
        if y_range <= 0:
            return chart_rect.center().y()
        
        ratio = (value - self._y_min) / y_range
        return chart_rect.bottom() - ratio * chart_rect.height()
    
    def _get_sf_color(self, sf_pct: float) -> QColor:
        """Get color for SF% value (gradient from bright to dark green)."""
        # Normalize to 0-1 range
        # sf_pct > 0 = bright green, sf_pct < -10 = dark green
        normalized = (sf_pct + 10) / 15  # -10 to +5 -> 0 to 1
        normalized = max(0.0, min(1.0, normalized))
        
        # Interpolate between dark and bright green
        r = int(0 + normalized * 0)
        g = int(102 + normalized * 153)  # 102 to 255
        b = int(51 + normalized * 85)    # 51 to 136
        
        return QColor(r, g, b)
    
    # =========================================================================
    # Context Menu (follows driver_strategy pattern)
    # =========================================================================
    
    def _show_context_menu(self, pos):
        """Handle right-click for context menu."""
        class FakeEvent:
            def __init__(self, global_pos):
                self._global_pos = global_pos
            def globalPos(self):
                return self._global_pos
        
        self.contextMenuEvent(FakeEvent(self.mapToGlobal(pos)))
    
    def contextMenuEvent(self, event):
        """Show context menu with driver selection."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLOR_CHART_BG};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_GRID};
            }}
            QMenu::item:selected {{
                background-color: {COLOR_GRID};
            }}
        """)
        
        # Driver selection submenu
        if self._available_drivers:
            driver_menu = menu.addMenu(tr("select_driver"))
            
            # Sort by position
            sorted_drivers = sorted(
                self._available_drivers.items(),
                key=lambda x: x[1].get('position', 99) if isinstance(x[1], dict) else 99
            )
            
            for driver_num, info in sorted_drivers:
                if not isinstance(info, dict):
                    continue
                
                tla = info.get('driver_tla', info.get('tla', driver_num))
                position = info.get('position', '')
                team_color = info.get('team_color', 'FFFFFF')
                
                # Display format: P1 VER
                display_text = f"P{position} {tla}" if position else tla
                action = driver_menu.addAction(display_text)
                action.setData(driver_num)
                
                # Mark current selection
                if tla == self._data.driver_tla:
                    action.setCheckable(True)
                    action.setChecked(True)
                
                action.triggered.connect(
                    lambda checked, d=driver_num: self.driver_change_requested.emit(d)
                )
        
        menu.exec_(event.globalPos())
    
    # =========================================================================
    # PyQt5 Native Drawing
    # =========================================================================
    
    def paintEvent(self, event):
        """Main paint event for custom drawing."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(COLOR_BACKGROUND))
        
        # Calculate chart area
        chart_rect = QRectF(
            self._margin_left,
            self._margin_top,
            self.width() - self._margin_left - self._margin_right,
            self.height() - self._margin_top - self._margin_bottom
        )
        
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return
        
        # Draw chart background
        painter.fillRect(chart_rect, QColor(COLOR_CHART_BG))
        
        # Draw in order (back to front)
        self._draw_threshold_zones(painter, chart_rect)
        self._draw_sc_zones(painter, chart_rect)
        self._draw_grid(painter, chart_rect)
        self._draw_threshold_lines(painter, chart_rect)
        self._draw_pit_markers(painter, chart_rect)
        self._draw_sf_curve(painter, chart_rect)
        self._draw_axes(painter, chart_rect)
        
        # Draw hover elements (from HoverTooltipMixin)
        self._draw_hover_elements(painter)
    
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
        from PyQt5.QtCore import QRect
        return QRect(
            self._margin_left,
            self._margin_top,
            self.width() - self._margin_left - self._margin_right,
            self.height() - self._margin_top - self._margin_bottom
        )
    
    def _pixel_to_x_value(self, pixel_x: int, chart_rect) -> float:
        """Convert pixel X to lap number."""
        if chart_rect.width() <= 0:
            return 1.0
        
        ratio = (pixel_x - chart_rect.left()) / chart_rect.width()
        return 1 + ratio * (self._total_laps - 1)
    
    def _get_hover_data_at_x(self, x_value: float):
        """Get hover data at the specified lap number."""
        # Round to nearest lap
        lap = round(x_value)
        lap = max(1, min(lap, self._total_laps))
        
        # Get SF% data for this lap
        data_points = []
        
        if lap in self._data.lap_sf_data:
            sf_pct = self._data.lap_sf_data[lap]
            
            # Determine color based on lamp status
            lamp = self._data.lap_lamp_data.get(lap, '')
            if lamp == 'R':
                color = COLOR_ZONE_RED
            elif lamp == 'Y':
                color = COLOR_ZONE_YELLOW
            else:
                color = COLOR_SF_POSITIVE
            
            data_points.append(HoverDataPoint(
                label="SF%",
                value=sf_pct,
                formatted_value=f"{sf_pct:.1f}%",
                color=color
            ))
        
        # Add baseline if available
        if lap in self._data.lap_baseline_data:
            baseline = self._data.lap_baseline_data[lap]
            data_points.append(HoverDataPoint(
                label="Baseline",
                value=baseline,
                formatted_value=f"{baseline:.1f}%",
                color="#AAAAAA"
            ))
        
        # Add throttle if available
        if lap in self._data.lap_throttle_data:
            throttle = self._data.lap_throttle_data[lap]
            data_points.append(HoverDataPoint(
                label="Throttle",
                value=throttle,
                formatted_value=f"{throttle:.1f}%",
                color="#88FF88"
            ))
        
        if not data_points:
            return None
        
        return HoverInfo(
            x_value=float(lap),
            x_label=f"Lap: {lap}",
            data_points=data_points,
            is_valid=True
        )
    
    def _draw_threshold_zones(self, painter: QPainter, chart_rect: QRectF):
        """Draw threshold zone fills (-3% yellow, -5% red)."""
        # -3% to -5% zone (yellow, semi-transparent)
        y_3pct = self._value_to_y(self._threshold_medium, chart_rect)
        y_5pct = self._value_to_y(self._threshold_high, chart_rect)
        y_bottom = chart_rect.bottom()
        
        # Yellow zone: -3% to -5%
        color_yellow = QColor(COLOR_ZONE_YELLOW)
        color_yellow.setAlpha(25)
        painter.setBrush(QBrush(color_yellow))
        painter.setPen(Qt.NoPen)
        painter.drawRect(QRectF(
            chart_rect.left(), y_3pct,
            chart_rect.width(), y_5pct - y_3pct
        ))
        
        # Red zone: below -5%
        color_red = QColor(COLOR_ZONE_RED)
        color_red.setAlpha(25)
        painter.setBrush(QBrush(color_red))
        painter.drawRect(QRectF(
            chart_rect.left(), y_5pct,
            chart_rect.width(), y_bottom - y_5pct
        ))
    
    def _draw_sc_zones(self, painter: QPainter, chart_rect: QRectF):
        """Draw SC/VSC zones as yellow fills with SC label."""
        if not self._sc_zones or self._total_laps <= 0:
            return
        
        color = QColor(COLOR_SC_ZONE)
        color.setAlpha(50)
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
    
    def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
        """Draw grid lines."""
        pen = QPen(QColor(COLOR_GRID))
        pen.setWidth(1)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        
        # Horizontal grid lines (every 5%)
        y_step = 5.0
        y_val = int(self._y_min / y_step) * y_step
        while y_val <= self._y_max:
            y = self._value_to_y(y_val, chart_rect)
            if chart_rect.top() <= y <= chart_rect.bottom():
                painter.drawLine(
                    QPointF(chart_rect.left(), y),
                    QPointF(chart_rect.right(), y)
                )
            y_val += y_step
        
        # Vertical grid lines (every 5 laps)
        x_step = 5
        for lap in range(x_step, self._total_laps + 1, x_step):
            x = self._lap_to_x(lap, chart_rect)
            painter.drawLine(
                QPointF(x, chart_rect.top()),
                QPointF(x, chart_rect.bottom())
            )
    
    def _draw_threshold_lines(self, painter: QPainter, chart_rect: QRectF):
        """Draw threshold lines (0%, -3%, -5%) as white dashed lines."""
        pen = QPen(QColor(COLOR_THRESHOLD_LINE))
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        # 0% baseline
        y_0 = self._value_to_y(0, chart_rect)
        if chart_rect.top() <= y_0 <= chart_rect.bottom():
            painter.drawLine(
                QPointF(chart_rect.left(), y_0),
                QPointF(chart_rect.right(), y_0)
            )
        
        # -3% threshold
        y_3 = self._value_to_y(self._threshold_medium, chart_rect)
        if chart_rect.top() <= y_3 <= chart_rect.bottom():
            painter.drawLine(
                QPointF(chart_rect.left(), y_3),
                QPointF(chart_rect.right(), y_3)
            )
        
        # -5% threshold
        y_5 = self._value_to_y(self._threshold_high, chart_rect)
        if chart_rect.top() <= y_5 <= chart_rect.bottom():
            painter.drawLine(
                QPointF(chart_rect.left(), y_5),
                QPointF(chart_rect.right(), y_5)
            )
    
    def _draw_pit_markers(self, painter: QPainter, chart_rect: QRectF):
        """Draw pit stop markers as vertical dashed lines with PIT label."""
        if not self._data.pit_laps or self._total_laps <= 0:
            return
        
        pen = QPen(QColor(COLOR_PIT_MARKER))
        pen.setWidth(2)
        pen.setStyle(Qt.DashDotLine)
        painter.setPen(pen)
        painter.setFont(self._font_axis)
        
        for lap in self._data.pit_laps:
            x = self._lap_to_x(lap, chart_rect)
            painter.drawLine(
                QPointF(x, chart_rect.top()),
                QPointF(x, chart_rect.bottom())
            )
            
            # Draw PIT label
            painter.save()
            painter.translate(x - 5, chart_rect.top() + 15)
            painter.rotate(-90)
            painter.drawText(0, 0, "PIT")
            painter.restore()
    
    def _draw_sf_curve(self, painter: QPainter, chart_rect: QRectF):
        """Draw SF% curve with gradient green color."""
        if not self._data.lap_sf_data or self._total_laps <= 0:
            return
        
        # Filter out PIT/SC laps
        valid_laps = sorted([
            lap for lap in self._data.lap_sf_data.keys()
            if lap not in self._data.pit_out_laps and lap not in self._data.sc_laps
        ])
        
        if len(valid_laps) < 2:
            return
        
        # Draw line segments with gradient color
        pen = QPen()
        pen.setWidth(2)
        
        for i in range(len(valid_laps) - 1):
            lap1 = valid_laps[i]
            lap2 = valid_laps[i + 1]
            
            # Skip if laps are not consecutive (gap due to PIT/SC)
            if lap2 - lap1 > 2:
                continue
            
            sf1 = self._data.lap_sf_data[lap1]
            sf2 = self._data.lap_sf_data[lap2]
            
            x1 = self._lap_to_x(lap1, chart_rect)
            y1 = self._value_to_y(sf1, chart_rect)
            x2 = self._lap_to_x(lap2, chart_rect)
            y2 = self._value_to_y(sf2, chart_rect)
            
            # Average color for segment
            avg_sf = (sf1 + sf2) / 2
            color = self._get_sf_color(avg_sf)
            pen.setColor(color)
            painter.setPen(pen)
            
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    
    def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
        """Draw X and Y axes with labels."""
        painter.setFont(self._font_axis)
        painter.setPen(QColor(COLOR_AXIS))
        
        # Y-axis labels (SF%)
        y_step = 5.0
        y_val = int(self._y_min / y_step) * y_step
        while y_val <= self._y_max:
            y = self._value_to_y(y_val, chart_rect)
            if chart_rect.top() <= y <= chart_rect.bottom():
                text = f"{y_val:.0f}%"
                painter.drawText(
                    QRectF(2, y - 8, self._margin_left - 5, 16),
                    Qt.AlignRight | Qt.AlignVCenter,
                    text
                )
            y_val += y_step
        
        # X-axis labels (Lap numbers)
        x_step = 5
        for lap in range(1, self._total_laps + 1, x_step):
            x = self._lap_to_x(lap, chart_rect)
            text = str(lap)
            painter.drawText(
                QRectF(x - 15, chart_rect.bottom() + 5, 30, 20),
                Qt.AlignCenter,
                text
            )
        
        # X-axis title
        painter.drawText(
            QRectF(chart_rect.left(), chart_rect.bottom() + 15, 
                   chart_rect.width(), 20),
            Qt.AlignCenter,
            tr("lap_number")
        )


# =============================================================================
# SF% MDI Window (for integration with Live Timing MDI system)
# =============================================================================
class SFPercentageChartMDI:
    """
    MDI wrapper for SF% Chart.
    
    Manages the chart widget and handles driver switching.
    """
    
    def __init__(self, parent=None):
        self._chart = SFPercentageChartWidget(parent)
        self._current_driver_num: str = ""
        
        # Multi-driver data storage
        self._all_drivers_data: Dict[str, SFPercentageData] = {}
    
    @property
    def widget(self) -> SFPercentageChartWidget:
        """Get the chart widget."""
        return self._chart
    
    def switch_driver(self, driver_num: str, driver_info: Dict[str, Any]):
        """
        Switch to a different driver.
        
        Saves current driver data and loads new driver data.
        """
        # Save current driver data
        if self._current_driver_num:
            self._all_drivers_data[self._current_driver_num] = SFPercentageData(
                driver_num=self._current_driver_num,
                driver_tla=self._chart._data.driver_tla,
                driver_name=self._chart._data.driver_name,
                team_color=self._chart._data.team_color,
                position=self._chart._data.position,
                lap_sf_data=self._chart._data.lap_sf_data.copy(),
                lap_throttle_data=self._chart._data.lap_throttle_data.copy(),
                lap_baseline_data=self._chart._data.lap_baseline_data.copy(),
                lap_lamp_data=self._chart._data.lap_lamp_data.copy(),
                pit_laps=list(self._chart._data.pit_laps),
                pit_out_laps=set(self._chart._data.pit_out_laps),
                sc_laps=set(self._chart._data.sc_laps),
                current_lap=self._chart._data.current_lap
            )
        
        # Load new driver data
        self._current_driver_num = driver_num
        
        tla = driver_info.get('driver_tla', driver_info.get('tla', driver_num))
        name = driver_info.get('driver_name', driver_info.get('name', ''))
        team_color = driver_info.get('team_color', 'FFFFFF')
        position = driver_info.get('position', 0)
        
        self._chart.set_driver_info(driver_num, tla, name, team_color, position)
        
        # Restore saved data if available
        if driver_num in self._all_drivers_data:
            saved = self._all_drivers_data[driver_num]
            self._chart.load_driver_history(
                saved.lap_sf_data,
                saved.lap_throttle_data,
                saved.lap_baseline_data,
                saved.lap_lamp_data,
                saved.pit_laps,
                saved.pit_out_laps,
                saved.sc_laps,
                saved.current_lap
            )
        else:
            self._chart._data.clear()
            self._chart.update()
    
    def update_from_snapshot(self, snapshot: Dict[str, Any]):
        """Update chart from live timing snapshot."""
        self._chart.update_from_snapshot(snapshot)
    
    def set_available_drivers(self, drivers: Dict[str, Dict[str, Any]]):
        """Set available drivers for context menu."""
        self._chart.set_available_drivers(drivers)
    
    def set_total_laps(self, total_laps: int):
        """Set total race laps."""
        self._chart.set_total_laps(total_laps)
    
    def set_sc_laps(self, sc_laps: Set[int]):
        """Set SC laps."""
        self._chart.set_sc_laps(sc_laps)


# =============================================================================
# LiveTimingSFPercentageChart - BaseLiveTimingMDI Integration
# =============================================================================
class LiveTimingSFPercentageChart(BaseLiveTimingMDI):
    """
    SF% History Chart MDI module.
    
    Displays SF% (Stint Fuel Saving Percentage) history curve for a selected driver.
    Inherits from BaseLiveTimingMDI for proper signal handling.
    
    ARCHITECTURE: Tracks ALL drivers simultaneously for instant switching.
    - _all_drivers_sf_data: Dict[str, SFPercentageData] stores all driver data
    - Widget only displays the currently selected driver
    - Switching drivers loads from _all_drivers_sf_data (no reset)
    """
    
    MODULE_ID = "live_timing_sf_percentage_chart"
    DEFAULT_TITLE = "SF% History"
    
    def __init__(self, parent=None, data_manager=None):
        self._current_driver: str = ""
        self._drivers_data: Dict[str, Any] = {}
        
        # Multi-driver tracking: stores SF% data for ALL drivers
        self._all_drivers_sf_data: Dict[str, SFPercentageData] = {}
        
        # Global SC data (shared across all drivers)
        self._sc_laps: Set[int] = set()
        
        # Total laps from race info
        self._total_laps: int = 60
        
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(self.DEFAULT_TITLE)
        self.setMinimumSize(500, 300)
        self.resize(650, 400)
        
        # Connect DataManager driver selection signal
        if self._data_manager:
            self._data_manager.driver_selected.connect(self._on_driver_selected)
        
        logger.info("[SF_CHART_MDI] LiveTimingSFPercentageChart initialized")
    
    def _setup_ui(self):
        """Setup the UI layout."""
        # Create SF% chart widget and add to main_layout from BaseLiveTimingMDI
        self._chart_widget = SFPercentageChartWidget(self)
        self._main_layout.addWidget(self._chart_widget)
        
        # Connect driver change request signal
        self._chart_widget.driver_change_requested.connect(self._on_driver_change_requested)
    
    def _on_driver_change_requested(self, driver_num: str):
        """Handle driver change request from context menu."""
        logger.info("[SF_CHART_MDI] Driver change requested: %s", driver_num)
        self.select_driver(driver_num)
    
    def _on_driver_selected(self, driver_num: str):
        """Handle driver selection from DataManager."""
        logger.info("[SF_CHART_MDI] Driver selected from external: %s", driver_num)
        if hasattr(self, '_chart_widget'):
            self.select_driver(driver_num)
    
    def select_driver(self, driver_num: str):
        """
        Select and display a specific driver.
        
        Saves current driver data before switching.
        Loads saved data for the new driver if available.
        """
        if not driver_num or driver_num == self._current_driver:
            return
        
        # Save current driver data
        if self._current_driver and hasattr(self, '_chart_widget'):
            self._save_current_driver_data()
        
        # Get driver info
        driver_info = self._drivers_data.get(driver_num, {})
        
        tla = driver_info.get('driver_tla', driver_info.get('tla', driver_num))
        name = driver_info.get('driver_name', driver_info.get('name', ''))
        team_color = driver_info.get('team_color', 'FFFFFF')
        position = driver_info.get('position', 0)
        
        # Update current driver
        self._current_driver = driver_num
        
        # Update chart widget
        self._chart_widget.set_driver_info(driver_num, tla, name, team_color, position)
        
        # Update window title: SF% History - #1 VER
        title = f"SF% History - #{position} {tla}" if position else f"SF% History - {tla}"
        self.setWindowTitle(title)
        
        # Load saved data if available
        if driver_num in self._all_drivers_sf_data:
            saved = self._all_drivers_sf_data[driver_num]
            self._chart_widget.load_driver_history(
                saved.lap_sf_data,
                saved.lap_throttle_data,
                saved.lap_baseline_data,
                saved.lap_lamp_data,
                saved.pit_laps,
                saved.pit_out_laps,
                saved.sc_laps,
                saved.current_lap
            )
        else:
            # Initialize new driver data
            self._all_drivers_sf_data[driver_num] = SFPercentageData(
                driver_num=driver_num,
                driver_tla=tla,
                driver_name=name,
                team_color=team_color,
                position=position,
                sc_laps=self._sc_laps.copy()
            )
            self._chart_widget._data.clear()
            self._chart_widget._data.sc_laps = self._sc_laps.copy()
            self._chart_widget.update()
        
        logger.info("[SF_CHART_MDI] Switched to driver: %s (%s)", driver_num, tla)
    
    def _save_current_driver_data(self):
        """Save current driver's SF% data."""
        if not self._current_driver:
            return
        
        self._all_drivers_sf_data[self._current_driver] = SFPercentageData(
            driver_num=self._current_driver,
            driver_tla=self._chart_widget._data.driver_tla,
            driver_name=self._chart_widget._data.driver_name,
            team_color=self._chart_widget._data.team_color,
            position=self._chart_widget._data.position,
            lap_sf_data=self._chart_widget._data.lap_sf_data.copy(),
            lap_throttle_data=self._chart_widget._data.lap_throttle_data.copy(),
            lap_baseline_data=self._chart_widget._data.lap_baseline_data.copy(),
            lap_lamp_data=self._chart_widget._data.lap_lamp_data.copy(),
            pit_laps=list(self._chart_widget._data.pit_laps),
            pit_out_laps=set(self._chart_widget._data.pit_out_laps),
            sc_laps=set(self._chart_widget._data.sc_laps),
            current_lap=self._chart_widget._data.current_lap
        )
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Handle race loaded event."""
        # Get total laps
        self._total_laps = race_info.get('total_laps', 60)
        self._chart_widget.set_total_laps(self._total_laps)
        
        # Get driver info
        driver_info = race_info.get('driver_info', {})
        for driver_num, info in driver_info.items():
            self._drivers_data[driver_num] = info
        
        self._chart_widget.set_available_drivers(self._drivers_data)
        
        # Auto-select P1 driver if not already selected
        if not self._current_driver and self._drivers_data:
            # Find P1 driver
            sorted_drivers = sorted(
                self._drivers_data.items(),
                key=lambda x: x[1].get('position', 99) if isinstance(x[1], dict) else 99
            )
            if sorted_drivers:
                p1_driver = sorted_drivers[0][0]
                self.select_driver(p1_driver)
        
        logger.info("[SF_CHART_MDI] Race loaded: %s %s, total_laps=%d",
                   race_info.get('year'), race_info.get('race'), self._total_laps)
    
    def _on_race_unloaded(self):
        """Handle race unloaded event."""
        self._current_driver = ""
        self._drivers_data.clear()
        self._all_drivers_sf_data.clear()
        self._sc_laps.clear()
        self._chart_widget._data.clear()
        self._chart_widget.update()
        self.setWindowTitle(self.DEFAULT_TITLE)
        logger.info("[SF_CHART_MDI] Race unloaded")
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Handle snapshot update event."""
        drivers = snapshot.get('drivers', {})
        
        # Update drivers_data and available drivers
        for driver_num, driver_info in drivers.items():
            if driver_num not in self._drivers_data:
                self._drivers_data[driver_num] = {}
            self._drivers_data[driver_num].update(driver_info)
        
        self._chart_widget.set_available_drivers(self._drivers_data)
        
        # Update all drivers' SF% data
        self._update_all_drivers_sf_data(snapshot)
        
        # Update current driver's chart
        if self._current_driver:
            self._chart_widget.update_from_snapshot(snapshot)
    
    def _update_all_drivers_sf_data(self, snapshot: Dict[str, Any]):
        """
        Update SF% data for all drivers from snapshot.
        
        This tracks all drivers simultaneously so switching is instant.
        """
        drivers = snapshot.get('drivers', {})
        
        for driver_num, driver_info in drivers.items():
            lap_num = driver_info.get('lap', 0)
            if not lap_num or lap_num <= 0:
                continue
            
            try:
                lap_num = int(lap_num)
            except (ValueError, TypeError):
                continue
            
            # Get or create driver data
            if driver_num not in self._all_drivers_sf_data:
                tla = driver_info.get('driver_tla', driver_info.get('tla', driver_num))
                name = driver_info.get('driver_name', driver_info.get('name', ''))
                team_color = driver_info.get('team_color', 'FFFFFF')
                position = driver_info.get('position', 0)
                
                self._all_drivers_sf_data[driver_num] = SFPercentageData(
                    driver_num=driver_num,
                    driver_tla=tla,
                    driver_name=name,
                    team_color=team_color,
                    position=position,
                    sc_laps=self._sc_laps.copy()
                )
            
            sf_data = self._all_drivers_sf_data[driver_num]
            
            # Skip if already recorded this lap
            if lap_num in sf_data.lap_sf_data:
                continue
            
            # Get throttle data
            throttle_pct = driver_info.get('throttle_95_pct', 0)
            baseline = driver_info.get('throttle_baseline', 0)
            lamp = driver_info.get('fuel_saving_lamp', '')
            
            # Check PIT/SC status
            is_pit = driver_info.get('in_pit', False) or driver_info.get('pit_out', False)
            is_sc = lap_num in self._sc_laps
            
            # Update PIT laps
            if is_pit:
                if lap_num not in sf_data.pit_laps:
                    sf_data.pit_laps.append(lap_num)
                sf_data.pit_out_laps.add(lap_num)
                if lap_num > 1:
                    sf_data.pit_out_laps.add(lap_num - 1)
                sf_data.pit_out_laps.add(lap_num + 1)
            
            # Calculate SF% if valid (not PIT/SC)
            if not is_pit and not is_sc and lap_num not in sf_data.pit_out_laps:
                if baseline and baseline > 0 and throttle_pct > 0:
                    sf_pct = ((throttle_pct - baseline) / baseline) * 100
                    sf_data.lap_sf_data[lap_num] = sf_pct
                    sf_data.lap_throttle_data[lap_num] = throttle_pct
                    sf_data.lap_baseline_data[lap_num] = baseline
                    if lamp:
                        sf_data.lap_lamp_data[lap_num] = lamp
            
            sf_data.current_lap = max(sf_data.current_lap, lap_num)
            
            # Update position
            position = driver_info.get('position', 0)
            if position:
                sf_data.position = position
    
    def set_sc_laps(self, sc_laps: Set[int]):
        """Set global SC laps."""
        self._sc_laps = set(sc_laps)
        self._chart_widget.set_sc_laps(sc_laps)
        
        # Update all drivers' SC laps
        for sf_data in self._all_drivers_sf_data.values():
            sf_data.sc_laps = self._sc_laps.copy()
    
    def _cleanup(self):
        """Cleanup resources."""
        self._all_drivers_sf_data.clear()
        self._drivers_data.clear()
        self._current_driver = ""
        if hasattr(self, '_chart_widget'):
            self._chart_widget._data.clear()
