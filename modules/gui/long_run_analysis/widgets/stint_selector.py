#!/usr/bin/env python3
"""
Stint Selector Widget

Tab 1: Auto-detect and select Long Run stints.
Displays detected stints with checkboxes and edit buttons.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QCheckBox, QSpinBox, QGroupBox, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger(__name__)

# Import stint info type
try:
    from ..long_run_calculator import StintInfo
except ImportError:
    from modules.gui.long_run_analysis.long_run_calculator import StintInfo


class StintSelectorWidget(QWidget):
    """
    Stint selector widget for Long Run analysis
    
    Displays auto-detected Long Run stints and allows user selection.
    """
    
    # Signals
    stints_selected = pyqtSignal(list)  # List of selected StintInfo
    edit_stint_requested = pyqtSignal(object)  # StintInfo to edit
    next_step_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._stints: List[StintInfo] = []
        self._checkboxes: List[QCheckBox] = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Filter settings group
        filter_group = QGroupBox(tr("long_run.filter.title", "Filter Settings"))
        filter_layout = QHBoxLayout(filter_group)
        
        # Minimum consecutive laps
        filter_layout.addWidget(QLabel(tr("long_run.filter.min_laps", "Min Consecutive Laps:")))
        self.min_laps_spin = QSpinBox()
        self.min_laps_spin.setRange(2, 20)
        self.min_laps_spin.setValue(4)
        filter_layout.addWidget(self.min_laps_spin)
        
        # Exclude out/in laps
        self.exclude_pit_laps = QCheckBox(tr("long_run.filter.exclude_pit", "Exclude Out/In Laps"))
        self.exclude_pit_laps.setChecked(True)
        filter_layout.addWidget(self.exclude_pit_laps)
        
        filter_layout.addStretch()
        
        # Auto-detect button
        self.detect_btn = QPushButton(tr("long_run.detect", "Auto-Detect Long Runs"))
        self.detect_btn.clicked.connect(self._on_detect_clicked)
        filter_layout.addWidget(self.detect_btn)
        
        layout.addWidget(filter_group)
        
        # Stints table
        stints_group = QGroupBox(tr("long_run.stints.title", "Detected Long Run Stints"))
        stints_layout = QVBoxLayout(stints_group)
        
        self.stints_table = QTableWidget()
        self.stints_table.setColumnCount(8)
        self.stints_table.setHorizontalHeaderLabels([
            tr("long_run.col.select", "Select"),
            tr("long_run.col.driver", "Driver"),
            tr("long_run.col.stint", "Stint"),
            tr("long_run.col.laps", "Laps"),
            tr("long_run.col.count", "Count"),
            tr("long_run.col.compound", "Compound"),
            tr("long_run.col.status", "Status"),
            tr("long_run.col.edit", "Edit"),
        ])
        
        # Table settings
        self.stints_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stints_table.setAlternatingRowColors(True)
        self.stints_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.stints_table.horizontalHeader().setStretchLastSection(True)
        
        stints_layout.addWidget(self.stints_table)
        
        # Legend
        legend_label = QLabel(tr("long_run.legend", 
            "* = System detected as suspected Long Run (>=4 laps + stable lap times)"))
        legend_label.setStyleSheet("color: gray; font-style: italic;")
        stints_layout.addWidget(legend_label)
        
        layout.addWidget(stints_group, 1)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        self.next_btn = QPushButton(tr("long_run.next.fuel", "Next: Fuel Settings"))
        self.next_btn.clicked.connect(self.next_step_requested.emit)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
    
    def set_stints(self, stints: List[StintInfo]) -> None:
        """Set stints to display"""
        self._stints = stints
        self._update_table()
    
    def _update_table(self) -> None:
        """Update stints table"""
        self.stints_table.setRowCount(len(self._stints))
        self._checkboxes.clear()
        
        for row, stint in enumerate(self._stints):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(stint.selected)
            checkbox.stateChanged.connect(lambda state, s=stint: self._on_checkbox_changed(s, state))
            self._checkboxes.append(checkbox)
            
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.stints_table.setCellWidget(row, 0, checkbox_widget)
            
            # Driver
            self.stints_table.setItem(row, 1, QTableWidgetItem(stint.driver_code))
            
            # Stint number
            self.stints_table.setItem(row, 2, QTableWidgetItem(str(stint.stint_number)))
            
            # Lap range
            lap_range = f"Lap {stint.start_lap}-{stint.end_lap}"
            self.stints_table.setItem(row, 3, QTableWidgetItem(lap_range))
            
            # Lap count
            count_item = QTableWidgetItem(f"{stint.lap_count} laps")
            self.stints_table.setItem(row, 4, count_item)
            
            # Compound
            compound_item = QTableWidgetItem(stint.compound)
            compound_item.setBackground(self._get_compound_color(stint.compound))
            self.stints_table.setItem(row, 5, compound_item)
            
            # Status
            if stint.is_long_run:
                status = tr("long_run.status.detected", "Long Run *")
            elif stint.lap_count >= 4:
                status = tr("long_run.status.possible", "Possible")
            else:
                status = tr("long_run.status.short", "Short Stint")
            status_item = QTableWidgetItem(status)
            self.stints_table.setItem(row, 6, status_item)
            
            # Edit button
            edit_btn = QPushButton(tr("long_run.edit", "Edit"))
            edit_btn.clicked.connect(lambda checked, s=stint: self._on_edit_clicked(s))
            self.stints_table.setCellWidget(row, 7, edit_btn)
    
    def _get_compound_color(self, compound: str) -> QColor:
        """Get compound color"""
        colors = {
            'SOFT': QColor(255, 100, 100, 100),
            'MEDIUM': QColor(255, 255, 100, 100),
            'HARD': QColor(200, 200, 200, 100),
        }
        return colors.get(compound.upper(), QColor(255, 255, 255, 0))
    
    def _on_checkbox_changed(self, stint: StintInfo, state: int) -> None:
        """Handle checkbox state change"""
        stint.selected = (state == Qt.Checked)
        self._emit_selected_stints()
    
    def _on_edit_clicked(self, stint: StintInfo) -> None:
        """Handle edit button click"""
        logger.debug(f"[STINT_SELECTOR] Edit requested for {stint.driver_code} stint {stint.stint_number}")
        self.edit_stint_requested.emit(stint)
    
    def _on_detect_clicked(self) -> None:
        """Handle auto-detect button click"""
        # This will trigger parent to re-detect with new settings
        logger.debug("[STINT_SELECTOR] Auto-detect requested")
    
    def _emit_selected_stints(self) -> None:
        """Emit selected stints signal"""
        selected = [s for s in self._stints if s.selected]
        self.stints_selected.emit(selected)
    
    def get_selected_stints(self) -> List[StintInfo]:
        """Get currently selected stints"""
        return [s for s in self._stints if s.selected]
    
    def get_min_laps(self) -> int:
        """Get minimum laps setting"""
        return self.min_laps_spin.value()
