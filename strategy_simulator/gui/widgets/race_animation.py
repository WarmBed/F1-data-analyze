#!/usr/bin/env python3
"""
Race Animation Widget

Dynamic lap-by-lap race simulation visualization.
Shows position changes, pit stops, and SC/VSC events in an animated timeline.

Author: F1T Team
Date: 2026-01-04
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QSpinBox, QFrame, QSizePolicy, QGroupBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False


# Strategy colors
STRATEGY_COLORS = [
    '#0072BD',  # Blue
    '#D95319',  # Orange
    '#77AC30',  # Green
    '#7E2F8E',  # Purple
    '#A2142F',  # Red
    '#4DBEEE',  # Cyan
    '#EDB120',  # Yellow
]

# Compound colors
COMPOUND_COLORS = {
    'SOFT': '#FF5050',
    'MEDIUM': '#FFD700',
    'HARD': '#C8C8C8',
}


@dataclass
class LapState:
    """State of a strategy at a specific lap"""
    lap: int
    cumulative_time: float
    position: int
    compound: str
    tyre_age: int
    is_pit_lap: bool = False
    is_sc_lap: bool = False
    is_vsc_lap: bool = False
    gap_to_leader: float = 0.0


@dataclass
class StrategyAnimation:
    """Animation data for a single strategy"""
    name: str
    color: str
    lap_states: List[LapState]
    
    def get_state_at_lap(self, lap: int) -> Optional[LapState]:
        """Get state at specific lap"""
        for state in self.lap_states:
            if state.lap == lap:
                return state
        return None


class RaceAnimationWidget(QWidget):
    """
    Animated race simulation visualization.
    
    Features:
    - Lap-by-lap position timeline
    - Play/pause/step controls
    - Speed adjustment
    - SC/VSC visualization
    - Pit stop markers
    """
    
    # Signals
    lap_changed = pyqtSignal(int)  # Current lap changed
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._strategies: List[StrategyAnimation] = []
        self._current_lap: int = 1
        self._total_laps: int = 58
        self._is_playing: bool = False
        self._playback_speed: int = 1  # 1x, 2x, 4x, 8x
        self._timer: QTimer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        
        # SC events for visualization
        self._sc_events: List[Tuple[int, int, bool]] = []  # (start_lap, duration, is_vsc)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Top: Controls
        controls = self._create_controls()
        layout.addWidget(controls)
        
        # Middle: Position Timeline Chart
        if HAS_PYQTGRAPH:
            self._create_chart()
            layout.addWidget(self.chart_widget, 1)
        else:
            placeholder = QLabel("pyqtgraph 未安裝。請執行: pip install pyqtgraph")
            placeholder.setAlignment(Qt.AlignCenter)
            layout.addWidget(placeholder, 1)
        
        # Bottom: Current lap info
        self.info_frame = self._create_info_panel()
        layout.addWidget(self.info_frame)
    
    def _create_controls(self) -> QFrame:
        """Create playback controls"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Lap counter
        self.lap_label = QLabel("Lap 1 / 58")
        self.lap_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(self.lap_label)
        
        layout.addStretch()
        
        # Playback controls
        self.first_btn = QPushButton("⏮")
        self.first_btn.setFixedWidth(40)
        self.first_btn.clicked.connect(self._go_to_first)
        layout.addWidget(self.first_btn)
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.clicked.connect(self._go_to_prev)
        layout.addWidget(self.prev_btn)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedWidth(50)
        self.play_btn.clicked.connect(self._toggle_play)
        layout.addWidget(self.play_btn)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedWidth(40)
        self.next_btn.clicked.connect(self._go_to_next)
        layout.addWidget(self.next_btn)
        
        self.last_btn = QPushButton("⏭")
        self.last_btn.setFixedWidth(40)
        self.last_btn.clicked.connect(self._go_to_last)
        layout.addWidget(self.last_btn)
        
        layout.addSpacing(20)
        
        # Speed control
        layout.addWidget(QLabel("速度:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["1x", "2x", "4x", "8x"])
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        layout.addWidget(self.speed_combo)
        
        layout.addStretch()
        
        # Lap slider - use stretch instead of fixed width
        self.lap_slider = QSlider(Qt.Horizontal)
        self.lap_slider.setMinimum(1)
        self.lap_slider.setMaximum(58)
        self.lap_slider.setValue(1)
        self.lap_slider.setMinimumWidth(200)
        self.lap_slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.lap_slider, 1)  # Add stretch factor
        
        return frame
    
    def _create_chart(self):
        """Create the pyqtgraph position timeline chart"""
        pg.setConfigOptions(antialias=True)
        
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setBackground('w')
        self.chart_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Configure axes
        self.chart_widget.setLabel('bottom', 'Lap')
        self.chart_widget.setLabel('left', 'Gap to Leader (s)')
        
        # Invert Y axis (leader at top)
        self.chart_widget.invertY(False)
        
        # Store plot items
        self._plot_items: Dict[str, pg.PlotDataItem] = {}
        self._current_markers: Dict[str, pg.ScatterPlotItem] = {}
        self._pit_markers: List[pg.ScatterPlotItem] = []
        
        # SC zone items
        self._sc_zones: List[pg.LinearRegionItem] = []
    
    def _create_info_panel(self) -> QFrame:
        """Create current lap information panel"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("background-color: #f8f8f8;")
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Strategy cards
        self.strategy_cards: Dict[str, QLabel] = {}
        
        # Will be populated when strategies are set
        self.cards_layout = layout
        
        return frame
    
    def set_simulation_results(self, results: List, params=None):
        """
        Set simulation results for animation.
        
        Args:
            results: List of StrategySimulationResult
            params: SimulationParams (optional)
        """
        self._strategies.clear()
        
        if params:
            # SimulationParams uses 'race_laps', not 'total_laps'
            self._total_laps = params.race_laps
            self.lap_slider.setMaximum(self._total_laps)
        
        # Convert results to animation data
        for i, result in enumerate(results):
            color = STRATEGY_COLORS[i % len(STRATEGY_COLORS)]
            lap_states = self._extract_lap_states(result)
            
            anim = StrategyAnimation(
                name=result.strategy_name,
                color=color,
                lap_states=lap_states
            )
            self._strategies.append(anim)
        
        # Update chart
        self._update_chart()
        self._update_info_panel()
        self._go_to_first()
    
    def _extract_lap_states(self, result) -> List[LapState]:
        """Extract lap-by-lap states from simulation result"""
        states = []
        
        # Check for lap_results (the actual attribute name)
        if not hasattr(result, 'lap_results') or not result.lap_results:
            return states
        
        cumulative = 0.0
        current_stint_idx = 0
        current_stint = result.stints[0] if result.stints else None
        tyre_age = 0
        
        for lap_num, lap_result in enumerate(result.lap_results, start=1):
            lap_time = lap_result.net_time if hasattr(lap_result, 'net_time') else lap_result
            cumulative += lap_time
            tyre_age += 1
            
            # Check if pit lap
            is_pit_lap = False
            if current_stint and lap_num == current_stint.end_lap:
                is_pit_lap = True
                current_stint_idx += 1
                if current_stint_idx < len(result.stints):
                    current_stint = result.stints[current_stint_idx]
                    tyre_age = 0
            
            compound = current_stint.compound.value if current_stint else "MEDIUM"
            
            state = LapState(
                lap=lap_num,
                cumulative_time=cumulative,
                position=1,  # Will be calculated later
                compound=compound,
                tyre_age=tyre_age,
                is_pit_lap=is_pit_lap
            )
            states.append(state)
        
        return states
    
    def set_sc_events(self, events: List[Tuple[int, int, bool]]):
        """
        Set SC/VSC events for visualization.
        
        Args:
            events: List of (start_lap, duration, is_vsc)
        """
        self._sc_events = events
        self._update_sc_zones()
    
    def _update_chart(self):
        """Update the position timeline chart"""
        if not HAS_PYQTGRAPH:
            return
        
        # Clear existing plots
        self.chart_widget.clear()
        self._plot_items.clear()
        self._current_markers.clear()
        self._pit_markers.clear()
        
        if not self._strategies:
            return
        
        # Calculate positions at each lap (based on cumulative time)
        self._calculate_positions()
        
        # Plot each strategy
        for strat in self._strategies:
            laps = [s.lap for s in strat.lap_states]
            gaps = [s.gap_to_leader for s in strat.lap_states]
            
            # Main line
            color = pg.mkColor(strat.color)
            pen = pg.mkPen(color=color, width=2)
            plot = self.chart_widget.plot(laps, gaps, pen=pen, name=strat.name)
            self._plot_items[strat.name] = plot
            
            # Current position marker
            marker = pg.ScatterPlotItem(
                [1], [0], 
                size=15, 
                brush=pg.mkBrush(color),
                pen=pg.mkPen('k', width=1)
            )
            self.chart_widget.addItem(marker)
            self._current_markers[strat.name] = marker
            
            # Pit stop markers
            for state in strat.lap_states:
                if state.is_pit_lap:
                    pit_marker = pg.ScatterPlotItem(
                        [state.lap], [state.gap_to_leader],
                        symbol='o',
                        size=10,
                        brush=pg.mkBrush(COMPOUND_COLORS.get(state.compound, '#888')),
                        pen=pg.mkPen('k', width=2)
                    )
                    self.chart_widget.addItem(pit_marker)
                    self._pit_markers.append(pit_marker)
        
        # Update SC zones
        self._update_sc_zones()
        
        # Add legend
        self.chart_widget.addLegend()
    
    def _calculate_positions(self):
        """Calculate relative positions based on cumulative time"""
        if not self._strategies:
            return
        
        # For each lap, find the leader and calculate gaps
        for lap in range(1, self._total_laps + 1):
            lap_times = []
            for strat in self._strategies:
                state = strat.get_state_at_lap(lap)
                if state:
                    lap_times.append((strat.name, state.cumulative_time, state))
            
            if not lap_times:
                continue
            
            # Sort by cumulative time
            lap_times.sort(key=lambda x: x[1])
            leader_time = lap_times[0][1]
            
            # Update gaps and positions
            for pos, (name, time, state) in enumerate(lap_times, start=1):
                state.gap_to_leader = time - leader_time
                state.position = pos
    
    def _update_sc_zones(self):
        """Update SC/VSC zone visualization"""
        if not HAS_PYQTGRAPH:
            return
        
        # Clear existing zones
        for zone in self._sc_zones:
            self.chart_widget.removeItem(zone)
        self._sc_zones.clear()
        
        # Add new zones
        for start_lap, duration, is_vsc in self._sc_events:
            end_lap = start_lap + duration
            color = (255, 200, 0, 50) if is_vsc else (255, 100, 100, 50)  # Yellow for VSC, Red for SC
            
            zone = pg.LinearRegionItem(
                values=[start_lap, end_lap],
                brush=pg.mkBrush(color),
                movable=False
            )
            self.chart_widget.addItem(zone)
            self._sc_zones.append(zone)
    
    def _update_info_panel(self):
        """Update the strategy info cards"""
        # Clear existing cards
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.strategy_cards.clear()
        
        # Create new cards
        for strat in self._strategies:
            card = QLabel()
            card.setStyleSheet(f"""
                QLabel {{
                    background-color: {strat.color};
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }}
            """)
            card.setAlignment(Qt.AlignCenter)
            card.setMinimumWidth(150)
            self.cards_layout.addWidget(card)
            self.strategy_cards[strat.name] = card
        
        self.cards_layout.addStretch()
        self._update_current_lap_info()
    
    def _update_current_lap_info(self):
        """Update info cards for current lap"""
        for strat in self._strategies:
            state = strat.get_state_at_lap(self._current_lap)
            card = self.strategy_cards.get(strat.name)
            
            if state and card:
                gap_str = f"+{state.gap_to_leader:.1f}s" if state.gap_to_leader > 0 else "Leader"
                compound = state.compound[:1] if state.compound else "?"
                card.setText(
                    f"{strat.name}\n"
                    f"P{state.position} | {gap_str}\n"
                    f"{compound} (Age: {state.tyre_age})"
                )
        
        # Update markers
        self._update_current_markers()
    
    def _update_current_markers(self):
        """Update current position markers on chart"""
        if not HAS_PYQTGRAPH:
            return
        
        for strat in self._strategies:
            state = strat.get_state_at_lap(self._current_lap)
            marker = self._current_markers.get(strat.name)
            
            if state and marker:
                marker.setData([state.lap], [state.gap_to_leader])
    
    # Playback controls
    def _toggle_play(self):
        """Toggle play/pause"""
        if self._is_playing:
            self._pause()
        else:
            self._play()
    
    def _play(self):
        """Start animation"""
        self._is_playing = True
        self.play_btn.setText("⏸")
        
        # Timer interval based on speed
        intervals = {0: 500, 1: 250, 2: 125, 3: 62}  # 1x, 2x, 4x, 8x
        interval = intervals.get(self.speed_combo.currentIndex(), 500)
        
        self._timer.start(interval)
    
    def _pause(self):
        """Pause animation"""
        self._is_playing = False
        self.play_btn.setText("▶")
        self._timer.stop()
    
    def _on_timer_tick(self):
        """Timer tick - advance lap"""
        if self._current_lap < self._total_laps:
            self._set_current_lap(self._current_lap + 1)
        else:
            self._pause()
            self.animation_finished.emit()
    
    def _go_to_first(self):
        """Go to first lap"""
        self._set_current_lap(1)
    
    def _go_to_last(self):
        """Go to last lap"""
        self._set_current_lap(self._total_laps)
    
    def _go_to_prev(self):
        """Go to previous lap"""
        if self._current_lap > 1:
            self._set_current_lap(self._current_lap - 1)
    
    def _go_to_next(self):
        """Go to next lap"""
        if self._current_lap < self._total_laps:
            self._set_current_lap(self._current_lap + 1)
    
    def _on_slider_changed(self, value: int):
        """Handle slider change"""
        if value != self._current_lap:
            self._set_current_lap(value)
    
    def _on_speed_changed(self, index: int):
        """Handle speed change"""
        self._playback_speed = 2 ** index
        
        # If playing, restart timer with new interval
        if self._is_playing:
            self._timer.stop()
            self._play()
    
    def _set_current_lap(self, lap: int):
        """Set current lap and update display"""
        self._current_lap = max(1, min(lap, self._total_laps))
        
        # Update UI
        self.lap_label.setText(f"Lap {self._current_lap} / {self._total_laps}")
        self.lap_slider.blockSignals(True)
        self.lap_slider.setValue(self._current_lap)
        self.lap_slider.blockSignals(False)
        
        # Update info
        self._update_current_lap_info()
        
        # Emit signal
        self.lap_changed.emit(self._current_lap)
