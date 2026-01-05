#!/usr/bin/env python3
"""
Degradation Results Widget

Tab 4: Display calculation results in table format with embedded chart.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger(__name__)

# Import degradation chart
try:
    from .degradation_chart import DegradationChartWidget
except ImportError:
    from modules.gui.long_run_analysis.widgets.degradation_chart import DegradationChartWidget


class DegradationResultsWidget(QWidget):
    """
    Results display widget for Long Run analysis
    
    Shows degradation table and chart side by side.
    """
    
    # Signals
    export_requested = pyqtSignal(str)  # format: 'png', 'csv', 'json'
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._results: Dict[str, Any] = {}
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Splitter for table and chart
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Results table
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        table_group = QGroupBox(tr("long_run.results.table_title", "Degradation Summary"))
        table_group_layout = QVBoxLayout(table_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            tr("long_run.col.driver", "Driver"),
            tr("long_run.col.compound", "Compound"),
            tr("long_run.col.laps_analyzed", "Laps"),
            tr("long_run.col.deg_per_lap", "Deg/Lap (s)"),
            tr("long_run.col.normalized_deg", "Normalized (s)"),
            tr("long_run.col.avg_corrected", "Avg Time (s)"),
        ])
        
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSortingEnabled(True)
        
        table_group_layout.addWidget(self.results_table)
        table_layout.addWidget(table_group)
        
        # Statistics summary
        stats_label = QLabel()
        stats_label.setStyleSheet("color: gray; font-style: italic;")
        self.stats_label = stats_label
        table_layout.addWidget(stats_label)
        
        splitter.addWidget(table_container)
        
        # Right: Degradation chart
        self.chart_widget = DegradationChartWidget()
        splitter.addWidget(self.chart_widget)
        
        # Set initial sizes (40% table, 60% chart)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter, 1)
        
        # Export and navigation buttons
        button_layout = QHBoxLayout()
        
        self.back_btn = QPushButton(tr("long_run.back.track_evo", "Back: Track Evolution"))
        self.back_btn.clicked.connect(self.back_requested.emit)
        button_layout.addWidget(self.back_btn)
        
        button_layout.addStretch()
        
        self.export_csv_btn = QPushButton(tr("long_run.export.csv", "Export CSV"))
        self.export_csv_btn.clicked.connect(lambda: self.export_requested.emit('csv'))
        button_layout.addWidget(self.export_csv_btn)
        
        self.export_json_btn = QPushButton(tr("long_run.export.json", "Export JSON"))
        self.export_json_btn.clicked.connect(lambda: self.export_requested.emit('json'))
        button_layout.addWidget(self.export_json_btn)
        
        self.export_png_btn = QPushButton(tr("long_run.export.png", "Export Chart"))
        self.export_png_btn.clicked.connect(lambda: self.export_requested.emit('png'))
        button_layout.addWidget(self.export_png_btn)
        
        layout.addLayout(button_layout)
    
    def set_results(self, results: Dict[str, Any]) -> None:
        """Set calculation results"""
        self._results = results
        self._update_table()
        
        # Forward to chart widget
        if 'drivers' in results:
            self.chart_widget.set_results(results.get('driver_results', {}))
    
    def set_drivers(self, drivers: List[str], team_mapping: Optional[Dict[str, str]] = None) -> None:
        """Set drivers for chart widget"""
        self.chart_widget.set_drivers(drivers, team_mapping)
    
    def _update_table(self) -> None:
        """Update results table"""
        driver_results = self._results.get('driver_results', {})
        drivers = list(driver_results.keys())
        
        self.results_table.setRowCount(len(drivers))
        
        # Track min/max degradation for color coding
        all_degs = [
            r.get('degradation_per_lap', 0) 
            for r in driver_results.values()
            if r.get('degradation_per_lap') is not None
        ]
        min_deg = min(all_degs) if all_degs else 0
        max_deg = max(all_degs) if all_degs else 0
        
        for row, driver in enumerate(drivers):
            data = driver_results[driver]
            
            # Driver
            self.results_table.setItem(row, 0, QTableWidgetItem(driver))
            
            # Compound
            compound = data.get('compound', 'Unknown')
            compound_item = QTableWidgetItem(compound)
            compound_item.setBackground(self._get_compound_color(compound))
            self.results_table.setItem(row, 1, compound_item)
            
            # Laps analyzed
            laps = data.get('lap_count', 0)
            self.results_table.setItem(row, 2, QTableWidgetItem(str(laps)))
            
            # Degradation per lap
            deg = data.get('degradation_per_lap')
            if deg is not None:
                deg_item = QTableWidgetItem(f"{deg:.3f}")
                # Color code: green = low deg, red = high deg
                deg_item.setBackground(self._get_degradation_color(deg, min_deg, max_deg))
                self.results_table.setItem(row, 3, deg_item)
            else:
                self.results_table.setItem(row, 3, QTableWidgetItem("-"))
            
            # Normalized degradation (per 10 laps)
            norm_deg = data.get('normalized_degradation')
            if norm_deg is not None:
                self.results_table.setItem(row, 4, QTableWidgetItem(f"{norm_deg:.2f}"))
            else:
                self.results_table.setItem(row, 4, QTableWidgetItem("-"))
            
            # Average corrected lap time
            avg_time = data.get('average_corrected_time')
            if avg_time is not None:
                self.results_table.setItem(row, 5, QTableWidgetItem(f"{avg_time:.3f}"))
            else:
                self.results_table.setItem(row, 5, QTableWidgetItem("-"))
        
        # Update statistics summary
        self._update_stats_summary()
    
    def _update_stats_summary(self) -> None:
        """Update statistics summary label"""
        driver_results = self._results.get('driver_results', {})
        num_drivers = len(driver_results)
        
        if num_drivers == 0:
            self.stats_label.setText(tr("long_run.stats.no_data", "No data available"))
            return
        
        # Calculate average degradation
        degs = [r.get('degradation_per_lap', 0) for r in driver_results.values() 
                if r.get('degradation_per_lap') is not None]
        avg_deg = sum(degs) / len(degs) if degs else 0
        
        # Track evolution info
        track_evo = self._results.get('track_evolution', {})
        track_effect = track_evo.get('total_effect', 0)
        
        summary = tr("long_run.stats.summary", 
            "Analyzed {num_drivers} drivers | Average degradation: {avg_deg:.3f} s/lap | Track evolution effect: {track_effect:.2f} s"
        ).format(num_drivers=num_drivers, avg_deg=avg_deg, track_effect=track_effect)
        
        self.stats_label.setText(summary)
    
    def _get_compound_color(self, compound: str) -> QColor:
        """Get compound background color"""
        colors = {
            'SOFT': QColor(255, 100, 100, 80),
            'MEDIUM': QColor(255, 255, 100, 80),
            'HARD': QColor(200, 200, 200, 80),
            'INTERMEDIATE': QColor(100, 200, 100, 80),
            'WET': QColor(100, 150, 255, 80),
        }
        return colors.get(compound.upper(), QColor(255, 255, 255, 0))
    
    def _get_degradation_color(self, value: float, min_val: float, max_val: float) -> QColor:
        """Get degradation color (green=low, red=high)"""
        if max_val == min_val:
            return QColor(255, 255, 255, 0)
        
        # Normalize to 0-1
        ratio = (value - min_val) / (max_val - min_val)
        
        # Green to red gradient
        r = int(255 * ratio)
        g = int(255 * (1 - ratio))
        return QColor(r, g, 0, 60)
    
    def get_results(self) -> Dict[str, Any]:
        """Get current results"""
        return self._results
