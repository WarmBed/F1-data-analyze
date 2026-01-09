#!/usr/bin/env python3
"""
Monte Carlo Chart Widget

Visualizes Monte Carlo simulation results with:
- Win probability bar chart
- Finish time distribution histogram
- Position box plots
- SC impact analysis

Author: F1T Team
Date: 2026-01-04
"""

from typing import List, Dict, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QLabel, QComboBox, QFrame, QSizePolicy, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# Strategy colors matching race_animation.py
STRATEGY_COLORS = [
    '#0072BD',  # Blue
    '#D95319',  # Orange
    '#77AC30',  # Green
    '#7E2F8E',  # Purple
    '#A2142F',  # Red
    '#4DBEEE',  # Cyan
    '#EDB120',  # Yellow
]


class WinProbabilityChart(QWidget):
    """Horizontal bar chart showing win probability per strategy"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: Dict[str, float] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("冠軍勝率分佈 (P1)")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        if HAS_PYQTGRAPH:
            self.chart = pg.PlotWidget()
            self.chart.setBackground('w')
            self.chart.showGrid(x=True, y=False, alpha=0.3)
            self.chart.setLabel('bottom', 'Win %')
            
            # Hide left axis labels (we'll use custom labels)
            self.chart.getAxis('left').setTicks([])
            
            layout.addWidget(self.chart)
        else:
            layout.addWidget(QLabel("pyqtgraph required"))
    
    def set_data(self, win_percentages: Dict[str, float]):
        """Set win probability data"""
        self._data = win_percentages
        self._update_chart()
    
    def _update_chart(self):
        """Update the chart with current data"""
        if not HAS_PYQTGRAPH or not self._data:
            return
        
        self.chart.clear()
        
        # Sort by probability descending
        sorted_data = sorted(self._data.items(), key=lambda x: x[1], reverse=True)
        
        # Create horizontal bars
        y_vals = list(range(len(sorted_data)))
        x_vals = [p for _, p in sorted_data]
        names = [n for n, _ in sorted_data]
        
        # Create bar graph
        for i, (name, prob) in enumerate(sorted_data):
            color = pg.mkColor(STRATEGY_COLORS[i % len(STRATEGY_COLORS)])
            
            bar = pg.BarGraphItem(
                x0=[0], 
                x1=[prob],
                y=[i],
                height=0.6,
                brush=color
            )
            self.chart.addItem(bar)
            
            # Add percentage label
            text = pg.TextItem(f"{prob:.1f}%", color='k')
            text.setPos(prob + 1, i)
            self.chart.addItem(text)
            
            # Add strategy name
            name_text = pg.TextItem(name, color='k', anchor=(1, 0.5))
            name_text.setPos(-1, i)
            self.chart.addItem(name_text)
        
        # Set range
        max_prob = max(x_vals) if x_vals else 100
        self.chart.setXRange(-len(names[0])*3, max_prob + 15)
        self.chart.setYRange(-0.5, len(y_vals) - 0.5)


class TimeDistributionChart(QWidget):
    """Histogram showing finish time distribution"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: Dict[str, List[float]] = {}
        self._selected_strategy: Optional[str] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with selector
        header = QHBoxLayout()
        title = QLabel("完賽時間分佈")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        header.addWidget(QLabel("策略:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.currentTextChanged.connect(self._on_strategy_changed)
        header.addWidget(self.strategy_combo)
        
        layout.addLayout(header)
        
        if HAS_PYQTGRAPH and HAS_NUMPY:
            self.chart = pg.PlotWidget()
            self.chart.setBackground('w')
            self.chart.showGrid(x=True, y=True, alpha=0.3)
            self.chart.setLabel('bottom', 'Total Race Time (s)')
            self.chart.setLabel('left', 'Frequency')
            layout.addWidget(self.chart)
        else:
            layout.addWidget(QLabel("pyqtgraph and numpy required"))
    
    def set_data(self, time_distributions: Dict[str, List[float]]):
        """Set time distribution data per strategy"""
        self._data = time_distributions
        
        # Update combo box
        self.strategy_combo.clear()
        self.strategy_combo.addItems(list(time_distributions.keys()))
        
        if time_distributions:
            self._selected_strategy = list(time_distributions.keys())[0]
            self._update_chart()
    
    def _on_strategy_changed(self, strategy: str):
        """Handle strategy selection change"""
        self._selected_strategy = strategy
        self._update_chart()
    
    def _update_chart(self):
        """Update histogram for selected strategy"""
        if not HAS_PYQTGRAPH or not HAS_NUMPY or not self._selected_strategy:
            return
        
        self.chart.clear()
        
        times = self._data.get(self._selected_strategy, [])
        if not times:
            return
        
        # Calculate histogram
        times_arr = np.array(times)
        hist, bin_edges = np.histogram(times_arr, bins=30)
        
        # Create bar items
        width = bin_edges[1] - bin_edges[0]
        
        for i, count in enumerate(hist):
            bar = pg.BarGraphItem(
                x=[bin_edges[i] + width/2],
                height=[count],
                width=width * 0.9,
                brush=pg.mkColor(STRATEGY_COLORS[0])
            )
            self.chart.addItem(bar)
        
        # Add mean line
        mean_time = np.mean(times_arr)
        mean_line = pg.InfiniteLine(
            pos=mean_time,
            angle=90,
            pen=pg.mkPen('r', width=2, style=Qt.DashLine)
        )
        self.chart.addItem(mean_line)
        
        # Add mean label
        mean_text = pg.TextItem(f"Mean: {mean_time:.1f}s", color='r')
        mean_text.setPos(mean_time, max(hist))
        self.chart.addItem(mean_text)
        
        # Add std info
        std_time = np.std(times_arr)
        self.chart.setTitle(f"Mean: {mean_time:.1f}s, Std: {std_time:.1f}s")


class PositionBoxPlotChart(QWidget):
    """Box plot showing position distribution per strategy"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("Expected Position (Box Plot)")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        if HAS_PYQTGRAPH:
            self.chart = pg.PlotWidget()
            self.chart.setBackground('w')
            self.chart.showGrid(x=False, y=True, alpha=0.3)
            self.chart.setLabel('left', 'Position')
            self.chart.invertY(True)  # P1 at top
            layout.addWidget(self.chart)
        else:
            layout.addWidget(QLabel("pyqtgraph required"))
    
    def set_data(self, position_data: Dict[str, Dict[str, Any]]):
        """
        Set position prediction data.
        
        Args:
            position_data: {strategy_name: {
                'expected': float,
                'best': int,
                'worst': int,
                'q25': float,
                'q75': float
            }}
        """
        self._data = position_data
        self._update_chart()
    
    def _update_chart(self):
        """Update box plot"""
        if not HAS_PYQTGRAPH or not self._data:
            return
        
        self.chart.clear()
        
        strategies = list(self._data.keys())
        
        for i, (name, data) in enumerate(self._data.items()):
            color = pg.mkColor(STRATEGY_COLORS[i % len(STRATEGY_COLORS)])
            x = i
            
            expected = data.get('expected', 10)
            best = data.get('best', 1)
            worst = data.get('worst', 20)
            q25 = data.get('q25', expected - 2)
            q75 = data.get('q75', expected + 2)
            
            # Draw whiskers (best to worst)
            whisker = pg.PlotDataItem(
                [x, x], [best, worst],
                pen=pg.mkPen(color, width=2)
            )
            self.chart.addItem(whisker)
            
            # Draw box (Q25 to Q75)
            box_height = q75 - q25
            box = pg.BarGraphItem(
                x=[x],
                y=[q25],
                height=[box_height],
                width=0.4,
                brush=color,
                pen=pg.mkPen('k', width=1)
            )
            self.chart.addItem(box)
            
            # Draw median line
            median_line = pg.PlotDataItem(
                [x - 0.2, x + 0.2], [expected, expected],
                pen=pg.mkPen('k', width=3)
            )
            self.chart.addItem(median_line)
            
            # Add strategy label
            text = pg.TextItem(name, color='k', anchor=(0.5, 0))
            text.setPos(x, worst + 1)
            self.chart.addItem(text)
        
        # Set range
        self.chart.setXRange(-0.5, len(strategies) - 0.5)
        self.chart.setYRange(0, 22)


class SCImpactChart(QWidget):
    """Shows how SC events impact different strategies"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: Dict[str, Dict[str, float]] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("SC 影響分析")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Table showing SC impact
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "策略", "無SC冠軍率", "有SC冠軍率", "SC效益"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
    
    def set_data(self, sc_impact: Dict[str, Dict[str, float]]):
        """
        Set SC impact data.
        
        Args:
            sc_impact: {strategy_name: {
                'no_sc_win': float,
                'with_sc_win': float,
                'benefit': float
            }}
        """
        self._data = sc_impact
        self._update_table()
    
    def _update_table(self):
        """Update SC impact table"""
        self.table.setRowCount(len(self._data))
        
        for row, (name, data) in enumerate(self._data.items()):
            # Strategy name
            self.table.setItem(row, 0, QTableWidgetItem(name))
            
            # No SC win %
            no_sc = data.get('no_sc_win', 0)
            self.table.setItem(row, 1, QTableWidgetItem(f"{no_sc:.1f}%"))
            
            # With SC win %
            with_sc = data.get('with_sc_win', 0)
            self.table.setItem(row, 2, QTableWidgetItem(f"{with_sc:.1f}%"))
            
            # Benefit
            benefit = data.get('benefit', 0)
            benefit_item = QTableWidgetItem(f"{benefit:+.1f}%")
            if benefit > 0:
                benefit_item.setForeground(QColor('#4CAF50'))
            elif benefit < 0:
                benefit_item.setForeground(QColor('#f44336'))
            self.table.setItem(row, 3, benefit_item)


class MonteCarloChartWidget(QWidget):
    """
    Complete Monte Carlo results visualization widget.
    
    Features:
    - Win probability bar chart
    - Time distribution histogram
    - Position box plots
    - SC impact analysis table
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._summary = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("Monte Carlo 模擬結果")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Splitter for charts
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter, 1)
        
        # Top row: Win probability + Time distribution
        top_frame = QFrame()
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.win_chart = WinProbabilityChart()
        top_layout.addWidget(self.win_chart)
        
        self.time_chart = TimeDistributionChart()
        top_layout.addWidget(self.time_chart)
        
        splitter.addWidget(top_frame)
        
        # Bottom row: Position box plot + SC impact
        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        self.position_chart = PositionBoxPlotChart()
        bottom_layout.addWidget(self.position_chart)
        
        self.sc_chart = SCImpactChart()
        bottom_layout.addWidget(self.sc_chart)
        
        splitter.addWidget(bottom_frame)
        
        # Summary label
        self.summary_label = QLabel()
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e9;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.summary_label)
    
    def set_monte_carlo_summary(self, summary):
        """
        Set Monte Carlo simulation summary.
        
        Args:
            summary: MonteCarloSummary object from monte_carlo.py
        """
        self._summary = summary
        
        # Update win probability chart
        if hasattr(summary, 'win_percentages'):
            self.win_chart.set_data(summary.win_percentages)
        
        # Update time distribution using mean/std to generate approximate distribution
        if HAS_NUMPY and hasattr(summary, 'mean_times') and hasattr(summary, 'std_times'):
            time_distributions = {}
            for name in summary.mean_times.keys():
                mean = summary.mean_times.get(name, 5400)
                std = summary.std_times.get(name, 10)
                # Generate simulated distribution for visualization
                if std > 0:
                    time_distributions[name] = np.random.normal(mean, std, 200).tolist()
                else:
                    time_distributions[name] = [mean] * 200
            if time_distributions:
                self.time_chart.set_data(time_distributions)
        
        # Update position chart
        if hasattr(summary, 'position_predictions'):
            position_data = {}
            for name, pred in summary.position_predictions.items():
                position_data[name] = {
                    'expected': pred.expected_position,
                    'best': pred.best_case_position,
                    'worst': pred.worst_case_position,
                    'q25': pred.expected_position - 2,  # Approximate
                    'q75': pred.expected_position + 2,
                }
            self.position_chart.set_data(position_data)
        
        # Update SC impact chart
        if hasattr(summary, 'sc_impact_analysis'):
            self.sc_chart.set_data(summary.sc_impact_analysis)
        
        # Update summary label
        self._update_summary_label()
    
    def set_raw_results(self, iterations: List, strategies: List[str]):
        """
        Set raw Monte Carlo iteration results for detailed charts.
        
        Args:
            iterations: List of MonteCarloIteration
            strategies: List of strategy names
        """
        if not HAS_NUMPY:
            return
        
        # Extract time distributions
        time_distributions = {s: [] for s in strategies}
        for it in iterations:
            for name, time in it.strategy_results.items():
                if name in time_distributions:
                    time_distributions[name].append(time)
        
        self.time_chart.set_data(time_distributions)
    
    def _update_summary_label(self):
        """Update summary text"""
        if not self._summary:
            self.summary_label.setText("No Monte Carlo results")
            return
        
        # Find best strategy
        ranking = self._summary.get_ranking() if hasattr(self._summary, 'get_ranking') else []
        if ranking:
            best_name, best_pct = ranking[0]
            iterations = self._summary.iterations
            sc_rate = self._summary.sc_occurrence_rate * 100
            
            self.summary_label.setText(
                f"Iterations: {iterations:,} | "
                f"Best: {best_name} ({best_pct:.1f}%) | "
                f"SC Rate: {sc_rate:.1f}%"
            )
        else:
            self.summary_label.setText(f"Iterations: {self._summary.iterations:,}")
    
    def clear(self):
        """Clear all charts"""
        self._summary = None
        # Clear would need to be implemented in each sub-widget
        self.summary_label.setText("Run Monte Carlo simulation to see results")
