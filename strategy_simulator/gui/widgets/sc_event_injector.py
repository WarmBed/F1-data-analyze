#!/usr/bin/env python3
"""
SC Event Injector Widget

Allows users to manually inject SC/VSC events for scenario testing.

Author: F1T Team
Date: 2026-01-04
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
    QPushButton, QLabel, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QButtonGroup, QFrame, QComboBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor


@dataclass
class SCEvent:
    """Single SC or VSC event"""
    start_lap: int
    duration: int
    is_vsc: bool = False
    
    @property
    def end_lap(self) -> int:
        return self.start_lap + self.duration - 1
    
    @property
    def event_type(self) -> str:
        return "VSC" if self.is_vsc else "SC"
    
    def to_tuple(self) -> Tuple[int, int, bool]:
        return (self.start_lap, self.duration, self.is_vsc)


class SCEventInjectorWidget(QWidget):
    """
    Widget for configuring SC/VSC events in simulation.
    
    Features:
    - No SC mode (deterministic)
    - Random SC mode (probabilistic)
    - Manual SC injection
    
    Signals:
        events_changed: Emitted when events are modified
    """
    
    events_changed = pyqtSignal(list)  # List of SCEvent
    mode_changed = pyqtSignal(str)  # 'none', 'random', 'manual'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._events: List[SCEvent] = []
        self._total_laps: int = 58
        self._mode: str = 'random'  # 'none', 'random', 'manual'
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Mode selection group
        mode_group = QGroupBox("SC Event Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_button_group = QButtonGroup(self)
        
        # No SC mode
        self.no_sc_radio = QRadioButton("No SC (Deterministic)")
        self.no_sc_radio.setToolTip("No safety car events - pure pace simulation")
        self.mode_button_group.addButton(self.no_sc_radio, 0)
        mode_layout.addWidget(self.no_sc_radio)
        
        # Random SC mode
        random_layout = QHBoxLayout()
        self.random_sc_radio = QRadioButton("Random SC")
        self.random_sc_radio.setChecked(True)
        self.random_sc_radio.setToolTip("Probabilistic SC events in Monte Carlo")
        self.mode_button_group.addButton(self.random_sc_radio, 1)
        random_layout.addWidget(self.random_sc_radio)
        
        random_layout.addWidget(QLabel("("))
        self.sc_prob_spin = QSpinBox()
        self.sc_prob_spin.setRange(0, 10)
        self.sc_prob_spin.setValue(2)
        self.sc_prob_spin.setSuffix("% / lap")
        self.sc_prob_spin.setToolTip("SC probability per lap")
        random_layout.addWidget(self.sc_prob_spin)
        random_layout.addWidget(QLabel(")"))
        random_layout.addStretch()
        mode_layout.addLayout(random_layout)
        
        # Manual SC mode
        self.manual_sc_radio = QRadioButton("Manual Injection")
        self.manual_sc_radio.setToolTip("Manually specify SC/VSC events")
        self.mode_button_group.addButton(self.manual_sc_radio, 2)
        mode_layout.addWidget(self.manual_sc_radio)
        
        layout.addWidget(mode_group)
        
        # Connect mode changes
        self.mode_button_group.buttonClicked.connect(self._on_mode_changed)
        
        # Manual events panel (hidden by default)
        self.manual_panel = QGroupBox("Manual SC Events")
        manual_layout = QVBoxLayout(self.manual_panel)
        
        # Add event controls
        add_layout = QHBoxLayout()
        
        add_layout.addWidget(QLabel("Lap:"))
        self.lap_spin = QSpinBox()
        self.lap_spin.setRange(1, 58)
        self.lap_spin.setValue(20)
        add_layout.addWidget(self.lap_spin)
        
        add_layout.addWidget(QLabel("Duration:"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 10)
        self.duration_spin.setValue(3)
        self.duration_spin.setSuffix(" laps")
        add_layout.addWidget(self.duration_spin)
        
        add_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["SC", "VSC"])
        add_layout.addWidget(self.type_combo)
        
        self.add_btn = QPushButton("Add Event")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.add_btn.clicked.connect(self._add_event)
        add_layout.addWidget(self.add_btn)
        
        add_layout.addStretch()
        manual_layout.addLayout(add_layout)
        
        # Events table
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(5)
        self.events_table.setHorizontalHeaderLabels([
            "Type", "Start Lap", "End Lap", "Duration", "Action"
        ])
        
        header = self.events_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.events_table.setColumnWidth(0, 60)
        self.events_table.setColumnWidth(4, 80)
        
        self.events_table.setMaximumHeight(150)
        manual_layout.addWidget(self.events_table)
        
        # Clear all button
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        self.clear_btn = QPushButton("Clear All Events")
        self.clear_btn.clicked.connect(self._clear_events)
        clear_layout.addWidget(self.clear_btn)
        manual_layout.addLayout(clear_layout)
        
        self.manual_panel.setVisible(False)
        layout.addWidget(self.manual_panel)
        
        # Quick presets
        preset_group = QGroupBox("Quick Presets")
        preset_layout = QHBoxLayout(preset_group)
        
        early_btn = QPushButton("Early SC (L15)")
        early_btn.setToolTip("SC on lap 15 - tests undercut scenarios")
        early_btn.clicked.connect(lambda: self._apply_preset('early'))
        preset_layout.addWidget(early_btn)
        
        mid_btn = QPushButton("Mid SC (L30)")
        mid_btn.setToolTip("SC on lap 30 - tests pit window optimization")
        mid_btn.clicked.connect(lambda: self._apply_preset('mid'))
        preset_layout.addWidget(mid_btn)
        
        late_btn = QPushButton("Late SC (L45)")
        late_btn.setToolTip("SC on lap 45 - tests one-stop feasibility")
        late_btn.clicked.connect(lambda: self._apply_preset('late'))
        preset_layout.addWidget(late_btn)
        
        multi_btn = QPushButton("Double SC")
        multi_btn.setToolTip("SC on lap 15 and 40 - tests strategy flexibility")
        multi_btn.clicked.connect(lambda: self._apply_preset('double'))
        preset_layout.addWidget(multi_btn)
        
        self.preset_group = preset_group
        self.preset_group.setVisible(False)
        layout.addWidget(preset_group)
        
        # Spacer
        layout.addStretch()
    
    def set_total_laps(self, laps: int):
        """Set total race laps"""
        self._total_laps = laps
        self.lap_spin.setMaximum(laps - 1)
    
    def _on_mode_changed(self, button):
        """Handle mode radio button change"""
        button_id = self.mode_button_group.id(button)
        
        if button_id == 0:
            self._mode = 'none'
            self.manual_panel.setVisible(False)
            self.preset_group.setVisible(False)
            self._events.clear()
        elif button_id == 1:
            self._mode = 'random'
            self.manual_panel.setVisible(False)
            self.preset_group.setVisible(False)
            self._events.clear()
        else:
            self._mode = 'manual'
            self.manual_panel.setVisible(True)
            self.preset_group.setVisible(True)
        
        self._update_table()
        self.mode_changed.emit(self._mode)
        self.events_changed.emit([e.to_tuple() for e in self._events])
    
    def _add_event(self):
        """Add a new SC/VSC event"""
        start_lap = self.lap_spin.value()
        duration = self.duration_spin.value()
        is_vsc = self.type_combo.currentText() == "VSC"
        
        # Validate no overlap
        new_event = SCEvent(start_lap, duration, is_vsc)
        
        for existing in self._events:
            if self._events_overlap(existing, new_event):
                QMessageBox.warning(
                    self, 
                    "Overlap Detected",
                    f"This event overlaps with existing {existing.event_type} "
                    f"(L{existing.start_lap}-{existing.end_lap})"
                )
                return
        
        self._events.append(new_event)
        self._events.sort(key=lambda e: e.start_lap)
        self._update_table()
        self.events_changed.emit([e.to_tuple() for e in self._events])
    
    def _events_overlap(self, e1: SCEvent, e2: SCEvent) -> bool:
        """Check if two events overlap"""
        return not (e1.end_lap < e2.start_lap or e2.end_lap < e1.start_lap)
    
    def _remove_event(self, index: int):
        """Remove event at index"""
        if 0 <= index < len(self._events):
            del self._events[index]
            self._update_table()
            self.events_changed.emit([e.to_tuple() for e in self._events])
    
    def _clear_events(self):
        """Clear all events"""
        self._events.clear()
        self._update_table()
        self.events_changed.emit([])
    
    def _update_table(self):
        """Update events table"""
        self.events_table.setRowCount(len(self._events))
        
        for row, event in enumerate(self._events):
            # Type
            type_item = QTableWidgetItem(event.event_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            if event.is_vsc:
                type_item.setBackground(QColor('#FFF59D'))  # Yellow
            else:
                type_item.setBackground(QColor('#FFCDD2'))  # Red
            self.events_table.setItem(row, 0, type_item)
            
            # Start lap
            self.events_table.setItem(row, 1, QTableWidgetItem(str(event.start_lap)))
            
            # End lap
            self.events_table.setItem(row, 2, QTableWidgetItem(str(event.end_lap)))
            
            # Duration
            self.events_table.setItem(row, 3, QTableWidgetItem(f"{event.duration} laps"))
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #f44336; color: white;")
            delete_btn.clicked.connect(lambda checked, r=row: self._remove_event(r))
            self.events_table.setCellWidget(row, 4, delete_btn)
    
    def _apply_preset(self, preset: str):
        """Apply a preset SC scenario"""
        self._events.clear()
        
        if preset == 'early':
            self._events.append(SCEvent(15, 4, False))
        elif preset == 'mid':
            self._events.append(SCEvent(30, 3, False))
        elif preset == 'late':
            self._events.append(SCEvent(45, 3, False))
        elif preset == 'double':
            self._events.append(SCEvent(15, 3, False))
            self._events.append(SCEvent(40, 3, False))
        
        # Switch to manual mode
        self.manual_sc_radio.setChecked(True)
        self._mode = 'manual'
        self.manual_panel.setVisible(True)
        self.preset_group.setVisible(True)
        
        self._update_table()
        self.mode_changed.emit(self._mode)
        self.events_changed.emit([e.to_tuple() for e in self._events])
    
    def get_events(self) -> List[Tuple[int, int, bool]]:
        """Get list of SC events as tuples"""
        return [e.to_tuple() for e in self._events]
    
    def get_mode(self) -> str:
        """Get current mode"""
        return self._mode
    
    def get_sc_probability(self) -> float:
        """Get SC probability per lap (for random mode)"""
        return self.sc_prob_spin.value() / 100.0
    
    def set_events(self, events: List[Tuple[int, int, bool]]):
        """Set SC events from tuples"""
        self._events = [SCEvent(s, d, v) for s, d, v in events]
        self._update_table()
        
        if self._events:
            self.manual_sc_radio.setChecked(True)
            self._mode = 'manual'
            self.manual_panel.setVisible(True)
            self.preset_group.setVisible(True)
