#!/usr/bin/env python3
"""
Compound Comparison Widget

Tab 5: Bar chart comparing different tire compounds' degradation.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger(__name__)


class CompoundComparisonWidget(QWidget):
    """
    Compound comparison bar chart widget
    
    Displays side-by-side comparison of degradation rates by compound.
    """
    
    # Signals
    export_requested = pyqtSignal(str)  # format: 'png', 'csv'
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._results: Dict[str, Any] = {}
        self._chart_widget = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Comparison type selector
        selector_layout = QHBoxLayout()
        
        selector_layout.addWidget(QLabel(tr("long_run.compound.compare_by", "Compare by:")))
        
        self.compare_combo = QComboBox()
        self.compare_combo.addItems([
            tr("long_run.compound.deg_per_lap", "Degradation per Lap"),
            tr("long_run.compound.normalized", "Normalized (per 10 laps)"),
            tr("long_run.compound.avg_time", "Average Corrected Time"),
        ])
        self.compare_combo.currentIndexChanged.connect(self._update_chart)
        selector_layout.addWidget(self.compare_combo)
        
        selector_layout.addStretch()
        
        layout.addLayout(selector_layout)
        
        # Chart container
        chart_group = QGroupBox(tr("long_run.compound.chart_title", "Compound Degradation Comparison"))
        chart_layout = QVBoxLayout(chart_group)
        
        try:
            from modules.gui.base.universal_chart_widget import UniversalChartWidget
            self._chart_widget = UniversalChartWidget()
            chart_layout.addWidget(self._chart_widget)
        except ImportError:
            placeholder = QLabel(tr("long_run.compound.no_chart", 
                "Chart widget not available."))
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setMinimumHeight(400)
            placeholder.setStyleSheet("background-color: #f5f5f5; border: 1px dashed #ccc;")
            chart_layout.addWidget(placeholder)
        
        layout.addWidget(chart_group, 1)
        
        # Legend / Insight panel
        insight_group = QGroupBox(tr("long_run.compound.insights", "Insights"))
        insight_layout = QVBoxLayout(insight_group)
        
        self.insight_label = QLabel(tr("long_run.compound.no_insights", 
            "Load data and calculate degradation to see insights."))
        self.insight_label.setWordWrap(True)
        insight_layout.addWidget(self.insight_label)
        
        layout.addWidget(insight_group)
        
        # Navigation buttons
        button_layout = QHBoxLayout()
        
        self.back_btn = QPushButton(tr("long_run.back.results", "Back: Results"))
        self.back_btn.clicked.connect(self.back_requested.emit)
        button_layout.addWidget(self.back_btn)
        
        button_layout.addStretch()
        
        self.export_btn = QPushButton(tr("long_run.export.chart", "Export Chart"))
        self.export_btn.clicked.connect(lambda: self.export_requested.emit('png'))
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
    
    def set_results(self, results: Dict[str, Any]) -> None:
        """Set calculation results"""
        self._results = results
        self._update_chart()
        self._update_insights()
    
    def _update_chart(self) -> None:
        """Update comparison bar chart"""
        if not self._chart_widget or not self._results:
            return
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            driver_results = self._results.get('driver_results', {})
            if not driver_results:
                return
            
            # Group by compound
            compound_data = {}
            for driver, data in driver_results.items():
                compound = data.get('compound', 'Unknown')
                if compound not in compound_data:
                    compound_data[compound] = {'drivers': [], 'values': []}
                
                # Get value based on comparison type
                compare_idx = self.compare_combo.currentIndex()
                if compare_idx == 0:
                    value = data.get('degradation_per_lap', 0)
                elif compare_idx == 1:
                    value = data.get('normalized_degradation', 0)
                else:
                    value = data.get('average_corrected_time', 0)
                
                if value is not None:
                    compound_data[compound]['drivers'].append(driver)
                    compound_data[compound]['values'].append(value)
            
            # Create grouped bar chart
            fig, ax = plt.subplots(figsize=(12, 6))
            
            compounds = list(compound_data.keys())
            compound_colors = {
                'SOFT': '#FF6666',
                'MEDIUM': '#FFFF66',
                'HARD': '#CCCCCC',
                'INTERMEDIATE': '#66CC66',
                'WET': '#6699FF',
            }
            
            x = np.arange(len(compounds))
            width = 0.8
            
            # Plot average bar for each compound
            avgs = []
            for compound in compounds:
                values = compound_data[compound]['values']
                avg = sum(values) / len(values) if values else 0
                avgs.append(avg)
            
            bars = ax.bar(x, avgs, width, 
                         color=[compound_colors.get(c.upper(), '#AAAAAA') for c in compounds],
                         edgecolor='black', linewidth=1)
            
            # Add individual driver points as scatter
            for i, compound in enumerate(compounds):
                values = compound_data[compound]['values']
                drivers = compound_data[compound]['drivers']
                jitter = np.random.uniform(-0.1, 0.1, len(values))
                ax.scatter(x[i] + jitter, values, color='black', s=30, zorder=5, alpha=0.6)
                
                # Label each point with driver code
                for j, (drv, val) in enumerate(zip(drivers, values)):
                    ax.annotate(drv, (x[i] + jitter[j], val), 
                               textcoords="offset points", xytext=(0, 5),
                               ha='center', fontsize=7, alpha=0.8)
            
            ax.set_xticks(x)
            ax.set_xticklabels(compounds)
            ax.set_xlabel(tr("long_run.compound.x_label", "Tire Compound"))
            
            # Y-axis label based on comparison type
            compare_idx = self.compare_combo.currentIndex()
            if compare_idx == 0:
                ylabel = tr("long_run.compound.y_deg", "Degradation (s/lap)")
            elif compare_idx == 1:
                ylabel = tr("long_run.compound.y_norm", "Normalized Degradation (s/10 laps)")
            else:
                ylabel = tr("long_run.compound.y_time", "Average Corrected Time (s)")
            
            ax.set_ylabel(ylabel)
            ax.set_title(tr("long_run.compound.title", "Tire Compound Comparison"))
            ax.grid(axis='y', alpha=0.3)
            
            # Add value labels on bars
            for bar, avg in zip(bars, avgs):
                height = bar.get_height()
                ax.annotate(f'{avg:.3f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontweight='bold')
            
            self._chart_widget.set_figure(fig)
            plt.close(fig)
            
        except Exception as e:
            logger.error(f"[COMPOUND_COMPARISON] Error updating chart: {e}")
    
    def _update_insights(self) -> None:
        """Update insights panel"""
        driver_results = self._results.get('driver_results', {})
        if not driver_results:
            return
        
        # Group by compound and calculate averages
        compound_stats = {}
        for driver, data in driver_results.items():
            compound = data.get('compound', 'Unknown')
            deg = data.get('degradation_per_lap')
            if deg is not None:
                if compound not in compound_stats:
                    compound_stats[compound] = []
                compound_stats[compound].append(deg)
        
        insights = []
        
        # Find best compound
        avg_degs = {}
        for compound, degs in compound_stats.items():
            avg_degs[compound] = sum(degs) / len(degs)
        
        if avg_degs:
            best_compound = min(avg_degs, key=avg_degs.get)
            worst_compound = max(avg_degs, key=avg_degs.get)
            
            insights.append(tr("long_run.insight.best", 
                "Best compound: {compound} ({deg:.3f} s/lap avg)"
            ).format(compound=best_compound, deg=avg_degs[best_compound]))
            
            if best_compound != worst_compound:
                diff = avg_degs[worst_compound] - avg_degs[best_compound]
                insights.append(tr("long_run.insight.diff",
                    "Degradation difference: {diff:.3f} s/lap between {best} and {worst}"
                ).format(diff=diff, best=best_compound, worst=worst_compound))
        
        # Find driver with lowest degradation
        best_driver = None
        best_deg = float('inf')
        for driver, data in driver_results.items():
            deg = data.get('degradation_per_lap')
            if deg is not None and deg < best_deg:
                best_deg = deg
                best_driver = driver
        
        if best_driver:
            insights.append(tr("long_run.insight.best_driver",
                "Lowest degradation: {driver} ({deg:.3f} s/lap)"
            ).format(driver=best_driver, deg=best_deg))
        
        self.insight_label.setText("\n".join(insights) if insights else 
            tr("long_run.compound.no_insights", "No insights available."))
