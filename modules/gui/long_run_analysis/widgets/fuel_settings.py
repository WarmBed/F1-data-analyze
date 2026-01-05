#!/usr/bin/env python3
"""
Fuel Settings Widget

Tab 2: Configure fuel parameters per driver.
Displays track defaults and allows per-driver customization.

Author: F1T Team
Date: 2025-12-30
"""

from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QCheckBox, QDoubleSpinBox, QGroupBox, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger(__name__)

# Import driver fuel settings type
try:
    from ..long_run_calculator import DriverFuelSettings
except ImportError:
    from modules.gui.long_run_analysis.long_run_calculator import DriverFuelSettings


class FuelSettingsWidget(QWidget):
    """
    Fuel settings widget for Long Run analysis
    
    Configures fuel consumption and effect parameters per driver.
    """
    
    # Signals
    settings_changed = pyqtSignal(dict)  # Dict of driver_code -> DriverFuelSettings
    next_step_requested = pyqtSignal()
    prev_step_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._track_defaults: Dict[str, Any] = {}
        self._drivers: List[str] = []
        self._settings: Dict[str, DriverFuelSettings] = {}
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Track defaults group
        defaults_group = QGroupBox(tr("long_run.fuel.track_defaults", "Track Defaults"))
        defaults_layout = QHBoxLayout(defaults_group)
        
        defaults_layout.addWidget(QLabel(tr("long_run.fuel.consumption", "Fuel/Lap:")))
        self.default_consumption_label = QLabel("1.70 kg/lap")
        defaults_layout.addWidget(self.default_consumption_label)
        
        defaults_layout.addSpacing(20)
        
        defaults_layout.addWidget(QLabel(tr("long_run.fuel.effect", "Fuel Effect:")))
        self.default_effect_label = QLabel("0.030 s/kg")
        defaults_layout.addWidget(self.default_effect_label)
        
        defaults_layout.addSpacing(20)
        
        defaults_layout.addWidget(QLabel(tr("long_run.fuel.source", "Source:")))
        self.source_label = QLabel("Database")
        defaults_layout.addWidget(self.source_label)
        
        defaults_layout.addStretch()
        
        layout.addWidget(defaults_group)
        
        # Per-driver settings group
        drivers_group = QGroupBox(tr("long_run.fuel.driver_settings", "Per-Driver Fuel Settings"))
        drivers_layout = QVBoxLayout(drivers_group)
        
        self.drivers_table = QTableWidget()
        self.drivers_table.setColumnCount(5)
        self.drivers_table.setHorizontalHeaderLabels([
            tr("long_run.col.driver", "Driver"),
            tr("long_run.fuel.start_fuel", "Start Fuel (kg)"),
            tr("long_run.fuel.consumption_per_lap", "Consumption (kg/lap)"),
            tr("long_run.fuel.effect_coef", "Effect (s/kg)"),
            tr("long_run.fuel.use_default", "Use Track Default"),
        ])
        
        self.drivers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.drivers_table.setAlternatingRowColors(True)
        self.drivers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        drivers_layout.addWidget(self.drivers_table)
        
        # Hint
        hint_label = QLabel(tr("long_run.fuel.hint", 
            "Tip: FP sessions typically use 60-100 kg fuel, race start ~110 kg"))
        hint_label.setStyleSheet("color: gray; font-style: italic;")
        drivers_layout.addWidget(hint_label)
        
        layout.addWidget(drivers_group, 1)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton(tr("long_run.prev.stint", "Back: Stint Selection"))
        self.prev_btn.clicked.connect(self.prev_step_requested.emit)
        nav_layout.addWidget(self.prev_btn)
        
        nav_layout.addStretch()
        
        self.next_btn = QPushButton(tr("long_run.next.track_evo", "Next: Track Evolution"))
        self.next_btn.clicked.connect(self._on_next_clicked)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
    
    def set_track_defaults(self, defaults: Dict[str, Any]) -> None:
        """Set track default fuel values"""
        self._track_defaults = defaults
        
        # Update labels
        consumption = defaults.get('fuel_kg_per_lap', 1.70)
        effect = defaults.get('fuel_effect_coefficient', 0.030)
        source = defaults.get('source', 'default')
        
        self.default_consumption_label.setText(f"{consumption:.2f} kg/lap")
        self.default_effect_label.setText(f"{effect:.3f} s/kg")
        self.source_label.setText(source)
        
        # Update driver settings with defaults
        for driver in self._drivers:
            if driver not in self._settings:
                self._settings[driver] = DriverFuelSettings(
                    driver_code=driver,
                    fuel_kg_per_lap=consumption,
                    fuel_effect_coefficient=effect,
                )
            elif self._settings[driver].use_track_defaults:
                self._settings[driver].fuel_kg_per_lap = consumption
                self._settings[driver].fuel_effect_coefficient = effect
        
        self._update_table()
    
    def set_drivers(self, drivers: List[str]) -> None:
        """Set driver list"""
        self._drivers = drivers
        
        # Initialize settings for new drivers
        consumption = self._track_defaults.get('fuel_kg_per_lap', 1.70)
        effect = self._track_defaults.get('fuel_effect_coefficient', 0.030)
        
        for driver in drivers:
            if driver not in self._settings:
                self._settings[driver] = DriverFuelSettings(
                    driver_code=driver,
                    fuel_kg_per_lap=consumption,
                    fuel_effect_coefficient=effect,
                )
        
        self._update_table()
    
    def _update_table(self) -> None:
        """Update drivers table"""
        self.drivers_table.setRowCount(len(self._drivers))
        
        for row, driver in enumerate(self._drivers):
            settings = self._settings.get(driver, DriverFuelSettings(driver_code=driver))
            
            # Driver code
            self.drivers_table.setItem(row, 0, QTableWidgetItem(driver))
            
            # Start fuel
            start_fuel_spin = QDoubleSpinBox()
            start_fuel_spin.setRange(20, 150)
            start_fuel_spin.setValue(settings.start_fuel_kg)
            start_fuel_spin.setSuffix(" kg")
            start_fuel_spin.valueChanged.connect(
                lambda val, d=driver: self._on_setting_changed(d, 'start_fuel_kg', val)
            )
            self.drivers_table.setCellWidget(row, 1, start_fuel_spin)
            
            # Fuel consumption
            consumption_spin = QDoubleSpinBox()
            consumption_spin.setRange(0.5, 3.0)
            consumption_spin.setDecimals(2)
            consumption_spin.setSingleStep(0.05)
            consumption_spin.setValue(settings.fuel_kg_per_lap)
            consumption_spin.setSuffix(" kg/lap")
            consumption_spin.valueChanged.connect(
                lambda val, d=driver: self._on_setting_changed(d, 'fuel_kg_per_lap', val)
            )
            self.drivers_table.setCellWidget(row, 2, consumption_spin)
            
            # Fuel effect coefficient
            effect_spin = QDoubleSpinBox()
            effect_spin.setRange(0.01, 0.10)
            effect_spin.setDecimals(3)
            effect_spin.setSingleStep(0.001)
            effect_spin.setValue(settings.fuel_effect_coefficient)
            effect_spin.setSuffix(" s/kg")
            effect_spin.valueChanged.connect(
                lambda val, d=driver: self._on_setting_changed(d, 'fuel_effect_coefficient', val)
            )
            self.drivers_table.setCellWidget(row, 3, effect_spin)
            
            # Use track default checkbox
            use_default = QCheckBox()
            use_default.setChecked(settings.use_track_defaults)
            use_default.stateChanged.connect(
                lambda state, d=driver: self._on_use_default_changed(d, state)
            )
            
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(use_default)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.drivers_table.setCellWidget(row, 4, checkbox_widget)
    
    def _on_setting_changed(self, driver: str, field: str, value: float) -> None:
        """Handle setting change"""
        if driver in self._settings:
            setattr(self._settings[driver], field, value)
            self._settings[driver].use_track_defaults = False
    
    def _on_use_default_changed(self, driver: str, state: int) -> None:
        """Handle use default checkbox change"""
        if driver in self._settings:
            use_default = (state == Qt.Checked)
            self._settings[driver].use_track_defaults = use_default
            
            if use_default:
                # Reset to track defaults
                self._settings[driver].fuel_kg_per_lap = self._track_defaults.get('fuel_kg_per_lap', 1.70)
                self._settings[driver].fuel_effect_coefficient = self._track_defaults.get('fuel_effect_coefficient', 0.030)
                self._update_table()
    
    def _on_next_clicked(self) -> None:
        """Handle next button click"""
        self.settings_changed.emit(self._settings)
        self.next_step_requested.emit()
    
    def get_settings(self) -> Dict[str, DriverFuelSettings]:
        """Get current fuel settings"""
        return self._settings
