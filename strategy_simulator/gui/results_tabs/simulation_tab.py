#!/usr/bin/env python3
"""
Simulation Tab

New unified tab combining:
- Race Animation Widget (lap-by-lap visualization)
- Monte Carlo Charts (results distribution)
- Position Timeline

Author: F1T Team
Date: 2026-01-04
"""

from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QLabel, QTabWidget, QPushButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..widgets.race_animation import RaceAnimationWidget
from ..widgets.monte_carlo_chart import MonteCarloChartWidget


class SimulationTab(QWidget):
    """
    Dynamic simulation visualization tab.
    
    Features:
    - Race animation with lap-by-lap position changes
    - Monte Carlo results distribution
    - Interactive playback controls
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._results: List = []
        self._params = None
        self._mc_summary = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Main splitter - top animation (hidden), bottom MC charts
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Top: Race Animation (HIDDEN - user requested to disable)
        animation_group = QGroupBox("賽事模擬動畫")
        animation_layout = QVBoxLayout(animation_group)
        animation_layout.setContentsMargins(5, 5, 5, 5)
        
        self.animation_widget = RaceAnimationWidget()
        animation_layout.addWidget(self.animation_widget)
        
        splitter.addWidget(animation_group)
        animation_group.setVisible(False)  # ✅ 隱藏動畫區塊
        
        # Bottom: Monte Carlo Charts (now takes full space)
        mc_group = QGroupBox("Monte Carlo 分析")
        mc_layout = QVBoxLayout(mc_group)
        mc_layout.setContentsMargins(5, 5, 5, 5)
        
        self.mc_chart_widget = MonteCarloChartWidget()
        mc_layout.addWidget(self.mc_chart_widget)
        
        splitter.addWidget(mc_group)
        
        # Set splitter stretch factors (MC takes all space now)
        splitter.setStretchFactor(0, 0)  # Animation widget (hidden)
        splitter.setStretchFactor(1, 1)  # MC charts (full)
        
        # Placeholder message
        self.placeholder = QLabel(
            "執行模擬後可查看逐圈動畫和 Monte Carlo 結果。\n\n"
            "1. 在左側面板配置賽事參數\n"
            "2. 點擊『執行模擬』\n"
            "3. 動畫和圖表將顯示於此"
        )
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 50px;
                background-color: #f8f8f8;
                border-radius: 10px;
            }
        """)
        # Initially show placeholder, hide content
        # This is managed by set_results
    
    def set_results(self, results: List, params=None):
        """
        Set simulation results for visualization.
        
        Args:
            results: List of StrategySimulationResult
            params: SimulationParams (optional)
        """
        self._results = results
        self._params = params
        
        if results:
            # Update animation widget
            self.animation_widget.set_simulation_results(results, params)
            
            # Hide placeholder (if implemented)
        else:
            # Show placeholder
            pass
    
    def set_monte_carlo_summary(self, summary, iterations: List = None):
        """
        Set Monte Carlo simulation results.
        
        Args:
            summary: MonteCarloSummary object
            iterations: Optional list of individual iterations for detailed charts
        """
        self._mc_summary = summary
        
        self.mc_chart_widget.set_monte_carlo_summary(summary)
        
        if iterations and self._results:
            strategy_names = [r.strategy_name for r in self._results]
            self.mc_chart_widget.set_raw_results(iterations, strategy_names)
    
    def set_sc_events(self, events: List):
        """
        Set SC events for visualization.
        
        Args:
            events: List of (start_lap, duration, is_vsc) tuples
        """
        self.animation_widget.set_sc_events(events)
    
    def clear(self):
        """Clear all visualizations"""
        self._results = []
        self._params = None
        self._mc_summary = None
        
        self.mc_chart_widget.clear()
        # Animation widget doesn't have clear method yet
