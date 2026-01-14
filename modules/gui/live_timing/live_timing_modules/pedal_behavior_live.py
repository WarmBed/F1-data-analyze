"""
Live Timing Pedal Behavior Analysis
====================================

Pedal Behavior (Throttle/Brake State) - Live Timing Module

Displays real-time pedal behavior distribution for all drivers:
- throttle_only: Throttle > 0, Brake = 0
- brake_only: Throttle = 0, Brake > 0
- trail_braking: Throttle > 0, Brake > 0
- coasting: Throttle = 0, Brake = 0

Features:
- Stacked bar chart showing pedal state distribution
- Cumulative statistics (excluding PIT, SC, VSC, Flag laps)
- Updates at the end of each lap
- Sorted by current position (P1 on top)

Author: F1T Team
Date: 2026-01-12
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
)
from PyQt5.QtCore import Qt, QRect, QRectF
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont, QFontMetrics

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(__name__)


# ===========================================
# Pedal State Colors (Fixed)
# ===========================================
PEDAL_STATE_COLORS = {
    'throttle_only': QColor(144, 238, 144),    # Light Green
    'brake_only': QColor(255, 182, 193),       # Light Red/Pink
    'trail_braking': QColor(255, 218, 185),    # Light Orange/Peach
    'coasting': QColor(211, 211, 211)          # Light Gray
}

# Background colors
COLOR_BACKGROUND = '#1a1a1a'
COLOR_CHART_BG = '#242424'
COLOR_TEXT = '#E0E0E0'
COLOR_GRID = '#3a3a3a'


@dataclass
class DriverPedalStats:
    """Driver pedal behavior statistics"""
    driver_num: str
    tla: str = ""
    team_color: str = "CCCCCC"
    position: int = 99
    
    # Sample counters (per state)
    throttle_only_count: int = 0
    brake_only_count: int = 0
    trail_braking_count: int = 0
    coasting_count: int = 0
    total_samples: int = 0
    
    # Current lap tracking
    current_lap: int = 0
    current_lap_samples: List[tuple] = field(default_factory=list)  # [(throttle, brake), ...]
    
    # Excluded laps tracking
    excluded_laps: Set[int] = field(default_factory=set)
    
    # Valid laps count
    valid_laps_count: int = 0
    
    def get_ratios(self) -> Dict[str, float]:
        """Calculate pedal state ratios (sum = 100%)"""
        if self.total_samples == 0:
            return {
                'throttle_only': 0.0,
                'brake_only': 0.0,
                'trail_braking': 0.0,
                'coasting': 0.0
            }
        
        return {
            'throttle_only': (self.throttle_only_count / self.total_samples) * 100,
            'brake_only': (self.brake_only_count / self.total_samples) * 100,
            'trail_braking': (self.trail_braking_count / self.total_samples) * 100,
            'coasting': (self.coasting_count / self.total_samples) * 100
        }
    
    def add_sample(self, throttle: int, brake: int):
        """Add a sample to current lap"""
        self.current_lap_samples.append((throttle, brake))
    
    def finalize_lap(self, lap_num: int, is_excluded: bool):
        """
        Finalize current lap and accumulate stats
        
        Args:
            lap_num: Completed lap number
            is_excluded: Whether this lap should be excluded (PIT/SC/VSC/Flag)
        """
        if is_excluded:
            self.excluded_laps.add(lap_num)
            self.current_lap_samples.clear()
            return
        
        # Accumulate samples
        for throttle, brake in self.current_lap_samples:
            state = self._classify_state(throttle, brake)
            if state == 'throttle_only':
                self.throttle_only_count += 1
            elif state == 'brake_only':
                self.brake_only_count += 1
            elif state == 'trail_braking':
                self.trail_braking_count += 1
            else:  # coasting
                self.coasting_count += 1
            self.total_samples += 1
        
        self.valid_laps_count += 1
        self.current_lap_samples.clear()
    
    @staticmethod
    def _classify_state(throttle: int, brake: int) -> str:
        """
        Classify pedal state (mutually exclusive, sum = 100%)
        
        - throttle_only: Throttle > 0, Brake = 0
        - brake_only: Throttle = 0, Brake > 0
        - trail_braking: Throttle > 0, Brake > 0
        - coasting: Throttle = 0, Brake = 0
        """
        if throttle > 0 and brake == 0:
            return 'throttle_only'
        elif throttle == 0 and brake > 0:
            return 'brake_only'
        elif throttle > 0 and brake > 0:
            return 'trail_braking'
        else:  # throttle == 0 and brake == 0
            return 'coasting'


class PedalBehaviorLiveWidget(QWidget):
    """
    Pedal Behavior Stacked Bar Chart Widget
    
    Displays horizontal stacked bars for each driver showing pedal state distribution.
    Drivers are sorted by current position (P1 on top).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Deep background
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        self.setProperty("is_live_timing_widget", True)
        
        # Data storage
        self._driver_stats: Dict[str, DriverPedalStats] = {}
        
        # SC/VSC/Flag lap tracking (shared)
        self._flag_laps: Set[int] = set()
        
        # Layout parameters
        self._bar_height = 22
        self._bar_spacing = 4
        self._margin_left = 60
        self._margin_right = 10
        self._margin_top = 40
        self._margin_bottom = 50
        
        # Hover state
        self._hover_driver: Optional[str] = None
        
        self.setMouseTracking(True)
        self.setMinimumSize(300, 200)
        
        logger.info("[PEDAL_BEHAVIOR_LIVE] Widget initialized")
    
    def update_from_snapshot(self, snapshot: Dict[str, Any]):
        """Update from DataManager snapshot"""
        drivers = snapshot.get('drivers', {})
        track_status = snapshot.get('track_status', '1')
        
        # Check track status for exclusion
        is_flag_active = track_status not in ('1', '2')  # Not green/yellow flag
        is_sc = track_status == '4'  # Safety Car
        is_vsc = track_status == '6'  # Virtual Safety Car
        
        for driver_num, driver_data in drivers.items():
            throttle = driver_data.get('throttle')
            brake = driver_data.get('brake')
            lap_num = driver_data.get('lap')
            
            # Skip if missing essential data
            if throttle is None or brake is None:
                continue
            
            try:
                throttle = int(throttle)
                brake = int(brake)
                lap_num = int(lap_num) if lap_num is not None else 0
            except (ValueError, TypeError):
                continue
            
            # Initialize driver stats if needed
            if driver_num not in self._driver_stats:
                self._driver_stats[driver_num] = DriverPedalStats(driver_num=driver_num)
            
            stats = self._driver_stats[driver_num]
            
            # Update driver info
            stats.tla = driver_data.get('driver_tla', driver_num)
            stats.team_color = driver_data.get('team_color', 'CCCCCC')
            stats.position = driver_data.get('position', 99) or 99
            
            # Check if lap changed
            if lap_num > stats.current_lap and stats.current_lap > 0:
                # Determine if completed lap should be excluded
                completed_lap = stats.current_lap
                
                # Check PIT status
                is_pit = driver_data.get('in_pit', False) or driver_data.get('pit_out', False)
                
                # Check if this lap was under SC/VSC/Flag
                is_excluded = (
                    is_pit or 
                    completed_lap in self._flag_laps or
                    completed_lap in stats.excluded_laps
                )
                
                # Finalize the completed lap
                stats.finalize_lap(completed_lap, is_excluded)
            
            # Update current lap tracking
            if lap_num != stats.current_lap:
                stats.current_lap = lap_num
            
            # Mark current lap as excluded if under flag
            if is_flag_active or is_sc or is_vsc:
                self._flag_laps.add(lap_num)
                stats.excluded_laps.add(lap_num)
            
            # Add sample to current lap
            stats.add_sample(throttle, brake)
        
        # Trigger repaint
        self.update()
    
    def paintEvent(self, event):
        """Paint the stacked bar chart"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Clear background
            painter.fillRect(self.rect(), QColor(COLOR_BACKGROUND))
            
            # Get sorted drivers by position
            sorted_drivers = sorted(
                self._driver_stats.values(),
                key=lambda x: x.position
            )
            
            if not sorted_drivers:
                self._draw_no_data(painter)
                return
            
            # Calculate chart area
            chart_width = self.width() - self._margin_left - self._margin_right
            chart_height = self.height() - self._margin_top - self._margin_bottom
            
            if chart_width <= 0 or chart_height <= 0:
                return
            
            # Draw title
            self._draw_title(painter)
            
            # Draw legend
            self._draw_legend(painter)
            
            # Draw bars
            bar_total_height = self._bar_height + self._bar_spacing
            max_drivers = min(len(sorted_drivers), int(chart_height / bar_total_height))
            
            for i, stats in enumerate(sorted_drivers[:max_drivers]):
                y = self._margin_top + i * bar_total_height
                self._draw_driver_bar(painter, stats, y, chart_width)
            
        finally:
            painter.end()
    
    def _draw_no_data(self, painter: QPainter):
        """Draw 'No Data' message"""
        painter.setPen(QColor(COLOR_TEXT))
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(self.rect(), Qt.AlignCenter, tr("Waiting for data..."))
    
    def _draw_title(self, painter: QPainter):
        """Draw chart title"""
        painter.setPen(QColor(COLOR_TEXT))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(10, 20, tr("Pedal Behavior (Cumulative)"))
    
    def _draw_legend(self, painter: QPainter):
        """Draw legend at bottom"""
        legend_y = self.height() - 30
        legend_x = self._margin_left
        box_size = 12
        spacing = 10
        
        painter.setFont(QFont("Segoe UI", 9))
        
        legends = [
            ('throttle_only', tr("Throttle")),
            ('brake_only', tr("Brake")),
            ('trail_braking', tr("Trail Braking")),
            ('coasting', tr("Coasting"))
        ]
        
        for state, label in legends:
            color = PEDAL_STATE_COLORS[state]
            
            # Draw color box
            painter.fillRect(legend_x, legend_y, box_size, box_size, color)
            painter.setPen(QColor('#666666'))
            painter.drawRect(legend_x, legend_y, box_size, box_size)
            
            # Draw label
            painter.setPen(QColor(COLOR_TEXT))
            text_x = legend_x + box_size + 4
            painter.drawText(text_x, legend_y + box_size - 2, label)
            
            # Calculate next position
            fm = QFontMetrics(painter.font())
            text_width = fm.horizontalAdvance(label)
            legend_x += box_size + 4 + text_width + spacing
    
    def _draw_driver_bar(self, painter: QPainter, stats: DriverPedalStats, y: int, chart_width: int):
        """Draw a single driver's stacked bar"""
        x = self._margin_left
        
        # Draw driver label (TLA with position)
        painter.setPen(QColor(f"#{stats.team_color}"))
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        label = f"P{stats.position:02d} {stats.tla}"
        painter.drawText(5, y + self._bar_height - 5, label)
        
        # Get ratios
        ratios = stats.get_ratios()
        
        if stats.total_samples == 0:
            # Draw empty bar with "N/A"
            painter.fillRect(x, y, chart_width, self._bar_height, QColor(COLOR_CHART_BG))
            painter.setPen(QColor('#666666'))
            painter.drawRect(x, y, chart_width, self._bar_height)
            painter.setPen(QColor(COLOR_TEXT))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(x + 5, y + self._bar_height - 5, "N/A")
            return
        
        # Draw stacked bar segments
        current_x = float(x)
        states = ['throttle_only', 'brake_only', 'trail_braking', 'coasting']
        
        for state in states:
            ratio = ratios[state]
            segment_width = (ratio / 100.0) * chart_width
            
            if segment_width > 0:
                color = PEDAL_STATE_COLORS[state]
                rect = QRectF(current_x, y, segment_width, self._bar_height)
                painter.fillRect(rect, color)
                
                # Draw percentage text if segment is wide enough
                if segment_width > 30:
                    painter.setPen(QColor('#333333'))
                    painter.setFont(QFont("Segoe UI", 8))
                    text = f"{ratio:.1f}%"
                    text_rect = QRectF(current_x, y, segment_width, self._bar_height)
                    painter.drawText(text_rect, Qt.AlignCenter, text)
                
                current_x += segment_width
        
        # Draw border
        painter.setPen(QColor('#666666'))
        painter.drawRect(x, y, chart_width, self._bar_height)
    
    def reset(self):
        """Reset all data"""
        self._driver_stats.clear()
        self._flag_laps.clear()
        self.update()
        logger.info("[PEDAL_BEHAVIOR_LIVE] Data reset")


class LiveTimingPedalBehavior(BaseLiveTimingMDI):
    """
    Live Timing Pedal Behavior MDI Window
    
    Displays real-time pedal behavior distribution for all drivers.
    """
    
    # ✅ Workspace 保存/載入所需屬性 (2025-01-13)
    analysis_type = 'pedal_behavior_live'
    module_name = 'pedal_behavior_live'
    display_name = 'Pedal Behavior (Live)'
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        self.setWindowTitle(tr("Pedal Behavior"))
        self.setMinimumSize(400, 300)
        logger.info("[PEDAL_BEHAVIOR_LIVE] MDI initialized")
    
    def _setup_ui(self):
        """Setup UI components"""
        # Main widget
        self._chart_widget = PedalBehaviorLiveWidget(self)
        self._main_layout.addWidget(self._chart_widget)
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Handle snapshot update"""
        self._chart_widget.update_from_snapshot(snapshot)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Handle race loaded"""
        self._chart_widget.reset()
        logger.info("[PEDAL_BEHAVIOR_LIVE] Race loaded: %s", race_info.get('race_name', 'Unknown'))
    
    def _on_race_unloaded(self):
        """Handle race unloaded"""
        self._chart_widget.reset()
        logger.info("[PEDAL_BEHAVIOR_LIVE] Race unloaded")
    
    def _cleanup(self):
        """Cleanup resources"""
        self._chart_widget.reset()
