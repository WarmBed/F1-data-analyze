#!/usr/bin/env python3
"""
Degradation Chart Widget

Matplotlib chart for displaying degradation curves with driver selection.
Shows corrected lap times and degradation trends.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Dict, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox,
    QPushButton, QScrollArea
)
from PyQt5.QtCore import pyqtSignal

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger(__name__)

# Import for team colors
try:
    from ..utils.team_color_helper import TeamColorHelper
except ImportError:
    from modules.gui.long_run_analysis.utils.team_color_helper import TeamColorHelper


class DegradationChartWidget(QWidget):
    """
    Degradation curve chart with driver selection checkboxes
    """
    
    # Signals
    driver_selection_changed = pyqtSignal(list)  # List of selected driver codes
    export_requested = pyqtSignal(str)  # export format: 'png', 'csv', 'json'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._results: Dict[str, Any] = {}
        self._drivers: List[str] = []
        self._selected_drivers: List[str] = []
        self._driver_checkboxes: Dict[str, QCheckBox] = {}
        self._color_helper = TeamColorHelper()
        
        self._chart_widget = None  # Will be set when UniversalChartWidget is available
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Driver selection toolbar
        selection_scroll = QScrollArea()
        selection_scroll.setWidgetResizable(True)
        selection_scroll.setMaximumHeight(60)
        
        selection_widget = QWidget()
        self.selection_layout = QHBoxLayout(selection_widget)
        self.selection_layout.setContentsMargins(5, 5, 5, 5)
        self.selection_layout.setSpacing(10)
        
        # Select All / Clear All buttons
        self.select_all_btn = QPushButton(tr("long_run.chart.select_all", "All"))
        self.select_all_btn.setMaximumWidth(50)
        self.select_all_btn.clicked.connect(self._select_all)
        self.selection_layout.addWidget(self.select_all_btn)
        
        self.clear_all_btn = QPushButton(tr("long_run.chart.clear_all", "Clear"))
        self.clear_all_btn.setMaximumWidth(50)
        self.clear_all_btn.clicked.connect(self._clear_all)
        self.selection_layout.addWidget(self.clear_all_btn)
        
        # Separator
        self.selection_layout.addSpacing(10)
        
        # Driver checkboxes will be added dynamically
        self.selection_layout.addStretch()
        
        selection_scroll.setWidget(selection_widget)
        layout.addWidget(selection_scroll)
        
        # Chart container
        self.chart_group = QGroupBox(tr("long_run.chart.title", "Degradation Curves"))
        chart_layout = QVBoxLayout(self.chart_group)
        
        # Import and create chart widget
        try:
            from modules.gui.base.universal_chart_widget import UniversalChartWidget
            self._chart_widget = UniversalChartWidget()
            chart_layout.addWidget(self._chart_widget)
        except ImportError:
            # Fallback to placeholder
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtCore import Qt
            placeholder = QLabel(tr("long_run.chart.placeholder", 
                "Chart widget not available. Please ensure UniversalChartWidget is installed."))
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setMinimumHeight(400)
            placeholder.setStyleSheet("background-color: #f5f5f5; border: 1px dashed #ccc;")
            chart_layout.addWidget(placeholder)
        
        layout.addWidget(self.chart_group, 1)
    
    def set_drivers(self, drivers: List[str], team_mapping: Optional[Dict[str, str]] = None) -> None:
        """Set available drivers with team mapping"""
        self._drivers = drivers
        
        # Update color helper with team mapping
        if team_mapping:
            self._color_helper.update_team_mapping(team_mapping)
        
        # Clear existing checkboxes
        for checkbox in self._driver_checkboxes.values():
            checkbox.deleteLater()
        self._driver_checkboxes.clear()
        
        # Add checkboxes for each driver
        for driver in drivers:
            checkbox = QCheckBox(driver)
            checkbox.setChecked(True)  # Default selected
            
            # Set color indicator
            color = self._color_helper.get_driver_color(driver)
            checkbox.setStyleSheet(f"QCheckBox {{ color: {color}; font-weight: bold; }}")
            
            checkbox.stateChanged.connect(self._on_driver_checkbox_changed)
            
            # Insert before stretch
            self.selection_layout.insertWidget(
                self.selection_layout.count() - 1, checkbox
            )
            self._driver_checkboxes[driver] = checkbox
        
        self._selected_drivers = list(drivers)
    
    def set_results(self, results: Dict[str, Any]) -> None:
        """Set calculation results and update chart"""
        self._results = results
        self._update_chart()
    
    def _on_driver_checkbox_changed(self) -> None:
        """Handle driver checkbox changes"""
        self._selected_drivers = [
            driver for driver, cb in self._driver_checkboxes.items()
            if cb.isChecked()
        ]
        self.driver_selection_changed.emit(self._selected_drivers)
        self._update_chart()
    
    def _select_all(self) -> None:
        """Select all drivers"""
        for checkbox in self._driver_checkboxes.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(True)
            checkbox.blockSignals(False)
        self._selected_drivers = list(self._drivers)
        self.driver_selection_changed.emit(self._selected_drivers)
        self._update_chart()
    
    def _clear_all(self) -> None:
        """Clear all driver selections"""
        for checkbox in self._driver_checkboxes.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.blockSignals(False)
        self._selected_drivers = []
        self.driver_selection_changed.emit(self._selected_drivers)
        self._update_chart()
    
    def _update_chart(self) -> None:
        """Update the degradation chart"""
        if not self._chart_widget:
            return
        
        if not self._results or not self._selected_drivers:
            self._chart_widget.clear()
            return
        
        # Prepare chart data
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for driver in self._selected_drivers:
                if driver not in self._results:
                    continue
                    
                driver_data = self._results[driver]
                
                # Get style info
                color = self._color_helper.get_driver_color(driver)
                is_second = self._color_helper.is_second_driver(driver)
                linestyle = '--' if is_second else '-'
                
                # Plot corrected lap times
                laps = driver_data.get('laps', [])
                corrected = driver_data.get('corrected_times', [])
                
                if laps and corrected:
                    ax.plot(laps, corrected, 
                           color=color, linestyle=linestyle,
                           marker='o', markersize=4,
                           label=driver, linewidth=2)
                    
                    # Plot trend line if available
                    trend = driver_data.get('trend_line', [])
                    if trend:
                        ax.plot(laps, trend, 
                               color=color, linestyle=':', 
                               linewidth=1, alpha=0.7)
            
            ax.set_xlabel(tr("long_run.chart.x_label", "Lap Number"))
            ax.set_ylabel(tr("long_run.chart.y_label", "Corrected Lap Time (s)"))
            ax.set_title(tr("long_run.chart.degradation_title", "Tire Degradation (Fuel & Track Corrected)"))
            ax.legend(loc='upper left', ncol=4)
            ax.grid(True, alpha=0.3)
            
            # Update chart widget
            self._chart_widget.set_figure(fig)
            plt.close(fig)
            
        except Exception as e:
            logger.error(f"[DEGRADATION_CHART] Error updating chart: {e}")
    
    def get_selected_drivers(self) -> List[str]:
        """Get currently selected drivers"""
        return self._selected_drivers
