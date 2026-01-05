#!/usr/bin/env python3
"""
Track Evolution Widget

Tab 3: Configure Track Evolution calculation method.
Supports statistical model, reference driver, and hybrid approaches.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
    QPushButton, QLabel, QComboBox, QSpinBox, QButtonGroup,
    QFrame
)
from PyQt5.QtCore import pyqtSignal

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger(__name__)


class TrackEvolutionWidget(QWidget):
    """
    Track Evolution settings widget for Long Run analysis
    
    Configures the method used to calculate track condition changes.
    """
    
    # Signals
    method_changed = pyqtSignal(str, str)  # method, reference_driver
    calculate_requested = pyqtSignal()
    prev_step_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._drivers: List[str] = []
        self._current_method = "statistical"
        self._reference_driver: Optional[str] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Method selection group
        method_group = QGroupBox(tr("long_run.track_evo.method", "Calculation Method"))
        method_layout = QVBoxLayout(method_group)
        
        self.method_button_group = QButtonGroup(self)
        
        # Statistical model
        self.statistical_radio = QRadioButton(
            tr("long_run.track_evo.statistical", "Statistical Model - Median Lap Times")
        )
        self.statistical_radio.setChecked(True)
        self.method_button_group.addButton(self.statistical_radio, 0)
        method_layout.addWidget(self.statistical_radio)
        
        statistical_desc = QLabel(tr("long_run.track_evo.statistical_desc",
            "Uses median lap times from all selected drivers in the Long Run range\n"
            "to calculate track condition changes. Warning: May be unstable with < 5 drivers."))
        statistical_desc.setStyleSheet("color: gray; margin-left: 20px;")
        statistical_desc.setWordWrap(True)
        method_layout.addWidget(statistical_desc)
        
        method_layout.addSpacing(10)
        
        # Reference driver
        self.reference_radio = QRadioButton(
            tr("long_run.track_evo.reference", "Reference Driver - Specify Baseline")
        )
        self.method_button_group.addButton(self.reference_radio, 1)
        method_layout.addWidget(self.reference_radio)
        
        # Reference driver selector
        ref_layout = QHBoxLayout()
        ref_layout.setContentsMargins(20, 0, 0, 0)
        
        ref_layout.addWidget(QLabel(tr("long_run.track_evo.ref_driver", "Reference Driver:")))
        self.reference_combo = QComboBox()
        self.reference_combo.setMinimumWidth(150)
        self.reference_combo.setEnabled(False)
        ref_layout.addWidget(self.reference_combo)
        ref_layout.addStretch()
        method_layout.addLayout(ref_layout)
        
        reference_desc = QLabel(tr("long_run.track_evo.reference_desc",
            "Uses a driver on fresh tires as the baseline for track evolution.\n"
            "Warning: Reference driver must complete laps during the same period."))
        reference_desc.setStyleSheet("color: gray; margin-left: 20px;")
        reference_desc.setWordWrap(True)
        method_layout.addWidget(reference_desc)
        
        method_layout.addSpacing(10)
        
        # Hybrid mode
        self.hybrid_radio = QRadioButton(
            tr("long_run.track_evo.hybrid", "Hybrid Mode - Statistical + Reference Weighted")
        )
        self.method_button_group.addButton(self.hybrid_radio, 2)
        method_layout.addWidget(self.hybrid_radio)
        
        # Weight sliders
        weight_layout = QHBoxLayout()
        weight_layout.setContentsMargins(20, 0, 0, 0)
        
        weight_layout.addWidget(QLabel(tr("long_run.track_evo.stat_weight", "Statistical Weight:")))
        self.stat_weight_spin = QSpinBox()
        self.stat_weight_spin.setRange(0, 100)
        self.stat_weight_spin.setValue(70)
        self.stat_weight_spin.setSuffix("%")
        self.stat_weight_spin.setEnabled(False)
        weight_layout.addWidget(self.stat_weight_spin)
        
        weight_layout.addWidget(QLabel(tr("long_run.track_evo.ref_weight", "Reference Weight:")))
        self.ref_weight_spin = QSpinBox()
        self.ref_weight_spin.setRange(0, 100)
        self.ref_weight_spin.setValue(30)
        self.ref_weight_spin.setSuffix("%")
        self.ref_weight_spin.setEnabled(False)
        weight_layout.addWidget(self.ref_weight_spin)
        
        weight_layout.addStretch()
        method_layout.addLayout(weight_layout)
        
        hybrid_desc = QLabel(tr("long_run.track_evo.hybrid_desc",
            "Combines statistical and reference methods for improved accuracy."))
        hybrid_desc.setStyleSheet("color: gray; margin-left: 20px;")
        method_layout.addWidget(hybrid_desc)
        
        layout.addWidget(method_group)
        
        # Preview placeholder
        preview_group = QGroupBox(tr("long_run.track_evo.preview", "Track Evolution Preview"))
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel(tr("long_run.track_evo.no_preview", 
            "Preview will be shown after selecting a method and calculating."))
        self.preview_label.setAlignment(Qt.AlignCenter if hasattr(Qt, 'AlignCenter') else 4)
        self.preview_label.setMinimumHeight(150)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        preview_layout.addWidget(self.preview_label)
        
        layout.addWidget(preview_group, 1)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton(tr("long_run.prev.fuel", "Back: Fuel Settings"))
        self.prev_btn.clicked.connect(self.prev_step_requested.emit)
        nav_layout.addWidget(self.prev_btn)
        
        nav_layout.addStretch()
        
        self.calculate_btn = QPushButton(tr("long_run.calculate", "Calculate Degradation"))
        self.calculate_btn.setStyleSheet("font-weight: bold;")
        self.calculate_btn.clicked.connect(self._on_calculate_clicked)
        nav_layout.addWidget(self.calculate_btn)
        
        layout.addLayout(nav_layout)
        
        # Connect signals
        self.method_button_group.buttonClicked.connect(self._on_method_changed)
        self.reference_combo.currentTextChanged.connect(self._on_reference_changed)
        self.stat_weight_spin.valueChanged.connect(self._on_weight_changed)
    
    def set_drivers(self, drivers: List[str]) -> None:
        """Set available drivers for reference selection"""
        self._drivers = drivers
        self.reference_combo.clear()
        self.reference_combo.addItems(drivers)
    
    def _on_method_changed(self, button: QRadioButton) -> None:
        """Handle method selection change"""
        if button == self.statistical_radio:
            self._current_method = "statistical"
            self.reference_combo.setEnabled(False)
            self.stat_weight_spin.setEnabled(False)
            self.ref_weight_spin.setEnabled(False)
        elif button == self.reference_radio:
            self._current_method = "reference"
            self.reference_combo.setEnabled(True)
            self.stat_weight_spin.setEnabled(False)
            self.ref_weight_spin.setEnabled(False)
        elif button == self.hybrid_radio:
            self._current_method = "hybrid"
            self.reference_combo.setEnabled(True)
            self.stat_weight_spin.setEnabled(True)
            self.ref_weight_spin.setEnabled(True)
        
        self._emit_method_changed()
    
    def _on_reference_changed(self, driver: str) -> None:
        """Handle reference driver change"""
        self._reference_driver = driver
        self._emit_method_changed()
    
    def _on_weight_changed(self, value: int) -> None:
        """Handle weight change - sync complementary weight"""
        if self.sender() == self.stat_weight_spin:
            self.ref_weight_spin.blockSignals(True)
            self.ref_weight_spin.setValue(100 - value)
            self.ref_weight_spin.blockSignals(False)
        self._emit_method_changed()
    
    def _emit_method_changed(self) -> None:
        """Emit method changed signal"""
        self.method_changed.emit(self._current_method, self._reference_driver or "")
    
    def _on_calculate_clicked(self) -> None:
        """Handle calculate button click"""
        self._emit_method_changed()
        self.calculate_requested.emit()
    
    def get_method(self) -> str:
        """Get current method"""
        return self._current_method
    
    def get_reference_driver(self) -> Optional[str]:
        """Get reference driver"""
        return self._reference_driver if self._current_method != "statistical" else None
    
    def get_weights(self) -> tuple:
        """Get hybrid weights"""
        return (self.stat_weight_spin.value(), self.ref_weight_spin.value())


# Fix Qt import
from PyQt5.QtCore import Qt
