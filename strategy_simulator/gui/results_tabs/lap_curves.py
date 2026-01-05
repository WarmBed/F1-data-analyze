#!/usr/bin/env python3
"""
Lap Curves Tab

Interactive lap time and cumulative delta charts using pyqtgraph.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Optional, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QCheckBox, QPushButton, QLabel,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False
    print("[WARNING] pyqtgraph not installed. Charts will be disabled.")


# Compound colors
COMPOUND_COLORS = {
    'SOFT': (255, 80, 80),      # Red
    'MEDIUM': (255, 200, 0),    # Yellow  
    'HARD': (200, 200, 200),    # Gray
}

# Strategy colors
STRATEGY_COLORS = [
    (0, 114, 189),     # Blue
    (217, 83, 25),     # Orange
    (119, 172, 48),    # Green
    (126, 47, 142),    # Purple
    (162, 20, 47),     # Red
    (77, 190, 238),    # Cyan
    (255, 127, 14),    # Dark Orange
    (44, 160, 44),     # Dark Green
    (148, 103, 189),   # Light Purple
    (140, 86, 75),     # Brown
]


class LapCurvesTab(QWidget):
    """
    Lap curves tab with interactive pyqtgraph charts.
    
    Features:
    - Lap time progression chart
    - Cumulative delta chart
    - Strategy toggle checkboxes
    - Zoom/pan support
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: List = []
        self._params = None
        self._strategy_visible: Dict[int, bool] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        if not HAS_PYQTGRAPH:
            layout.addWidget(QLabel(
                "pyqtgraph 未安裝。\n"
                "請執行: pip install pyqtgraph"
            ))
            return
        
        # Configure pyqtgraph
        pg.setConfigOptions(antialias=True)
        
        # Top: Controls
        controls_layout = QHBoxLayout()
        
        # Strategy toggles
        self.toggle_frame = QFrame()
        self.toggle_layout = QHBoxLayout(self.toggle_frame)
        self.toggle_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(self.toggle_frame)
        
        controls_layout.addStretch()
        
        # Reset view button
        reset_btn = QPushButton("重置視圖")
        reset_btn.clicked.connect(self.reset_view)
        controls_layout.addWidget(reset_btn)
        
        layout.addLayout(controls_layout)
        
        # Charts splitter
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Top chart: Lap times
        lap_group = QGroupBox("單圈時間走勢")
        lap_layout = QVBoxLayout(lap_group)
        
        self.lap_plot = pg.PlotWidget()
        self.lap_plot.setBackground('w')
        self.lap_plot.setLabel('left', '單圈時間', units='s')
        self.lap_plot.setLabel('bottom', '圈數')
        self.lap_plot.showGrid(x=True, y=True, alpha=0.3)
        self.lap_plot.addLegend(offset=(10, 10))
        
        lap_layout.addWidget(self.lap_plot)
        splitter.addWidget(lap_group)
        
        # Bottom chart: Cumulative delta
        delta_group = QGroupBox("累積時間差距 (相對最佳策略)")
        delta_layout = QVBoxLayout(delta_group)
        
        self.delta_plot = pg.PlotWidget()
        self.delta_plot.setBackground('w')
        self.delta_plot.setLabel('left', '差距', units='s')
        self.delta_plot.setLabel('bottom', '圈數')
        self.delta_plot.showGrid(x=True, y=True, alpha=0.3)
        
        # Add zero line
        self.delta_plot.addLine(y=0, pen=pg.mkPen('k', width=1, style=Qt.DashLine))
        
        delta_layout.addWidget(self.delta_plot)
        splitter.addWidget(delta_group)
        
        # Link X axes
        self.delta_plot.setXLink(self.lap_plot)
        
        # Set splitter stretch factors (ratio instead of fixed pixels)
        splitter.setStretchFactor(0, 4)  # Lap time chart
        splitter.setStretchFactor(1, 3)  # Delta chart
    
    def update_results(self, results: List, params):
        """Update charts with simulation results."""
        if not HAS_PYQTGRAPH:
            return
        
        self._results = results
        self._params = params
        
        # Clear previous
        self.lap_plot.clear()
        self.delta_plot.clear()
        self._clear_toggles()
        
        if not results:
            return
        
        # Create toggle checkboxes
        for i, result in enumerate(results[:10]):  # Max 10 strategies
            self._strategy_visible[i] = i < 5  # Show first 5 by default
            
            checkbox = QCheckBox(f"{result.strategy_name} ({result.get_stint_notation()})")
            checkbox.setChecked(self._strategy_visible[i])
            checkbox.stateChanged.connect(lambda state, idx=i: self._on_toggle_strategy(idx, state))
            
            # Set color indicator
            color = STRATEGY_COLORS[i % len(STRATEGY_COLORS)]
            checkbox.setStyleSheet(f"color: rgb{color};")
            
            self.toggle_layout.addWidget(checkbox)
        
        # Draw charts
        self._draw_charts()
    
    def _draw_charts(self):
        """Draw all chart elements."""
        if not self._results:
            return
        
        self.lap_plot.clear()
        self.delta_plot.clear()
        
        # Add zero line to delta chart
        self.delta_plot.addLine(y=0, pen=pg.mkPen('k', width=1, style=Qt.DashLine))
        
        best_result = self._results[0]
        best_times = [r.net_time for r in best_result.lap_results]
        
        for i, result in enumerate(self._results):
            if not self._strategy_visible.get(i, False):
                continue
            
            color = STRATEGY_COLORS[i % len(STRATEGY_COLORS)]
            pen = pg.mkPen(color, width=2)
            
            # Lap times
            laps = [r.lap_number for r in result.lap_results]
            times = [r.net_time for r in result.lap_results]
            
            self.lap_plot.plot(
                laps, times, 
                pen=pen, 
                name=f"{result.strategy_name}"
            )
            
            # Mark pit laps
            for pit_lap in result.pit_laps:
                if pit_lap < len(times):
                    self.lap_plot.plot(
                        [pit_lap], [times[pit_lap - 1]],
                        pen=None,
                        symbol='o',
                        symbolPen=pg.mkPen(color),
                        symbolBrush=pg.mkBrush(*color),
                        symbolSize=8
                    )
            
            # Cumulative delta
            cumulative_delta = []
            total_delta = 0
            for lap_idx, (our_time, best_time) in enumerate(zip(times, best_times)):
                delta = our_time - best_time
                total_delta += delta
                cumulative_delta.append(total_delta)
            
            self.delta_plot.plot(
                laps, cumulative_delta,
                pen=pen,
                name=f"{result.strategy_name}"
            )
    
    def _on_toggle_strategy(self, idx: int, state: int):
        """Handle strategy visibility toggle."""
        self._strategy_visible[idx] = state == Qt.Checked
        self._draw_charts()
    
    def _clear_toggles(self):
        """Clear toggle checkboxes."""
        while self.toggle_layout.count():
            item = self.toggle_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._strategy_visible.clear()
    
    def reset_view(self):
        """Reset chart view to default."""
        if HAS_PYQTGRAPH:
            self.lap_plot.autoRange()
            self.delta_plot.autoRange()
