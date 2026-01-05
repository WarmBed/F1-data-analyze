#!/usr/bin/env python3
"""
Opponent Strategy Settings Panel

UI for configuring opponent pit strategies.

Author: F1T Team
Date: 2025-12-31
"""

from typing import Dict, List, Optional, Callable
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QFormLayout, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush

# Import i18n with lazy loading
from strategy_simulator.gui.i18n_helper import tr


# Available tire strategies
TIRE_STRATEGIES = {
    1: [  # 1-stop strategies
        ["S", "M"],
        ["S", "H"],
        ["M", "H"],
        ["M", "S"],
        ["H", "M"],
    ],
    2: [  # 2-stop strategies
        ["S", "M", "M"],
        ["S", "M", "H"],
        ["S", "S", "M"],
        ["S", "S", "H"],
        ["M", "S", "S"],
        ["S", "H", "S"],
    ],
    3: [  # 3-stop strategies
        ["S", "S", "S", "M"],
        ["S", "S", "M", "M"],
        ["S", "M", "S", "S"],
    ],
}


class OpponentStrategyPanel(QWidget):
    """
    Panel for configuring opponent strategies.
    
    Features:
    - Global default settings (stops, tire strategy)
    - Per-driver custom overrides
    - FP2 data integration toggle
    
    Signals:
        settings_changed: Emitted when any setting changes
    """
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._predictions: List[Dict] = []
        self._custom_settings: Dict[str, Dict] = {}  # driver -> {stops, tires}
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Global settings group
        global_group = self._create_global_settings()
        layout.addWidget(global_group)
        
        # Per-driver settings
        driver_group = self._create_driver_settings()
        layout.addWidget(driver_group, 1)  # Stretch
        
    def _create_global_settings(self) -> QGroupBox:
        """Create global default settings group."""
        group = QGroupBox(tr("GLOBAL_STRATEGY_SETTINGS", "Global Strategy Settings"))
        layout = QFormLayout(group)
        
        # Default stops
        self.stops_combo = QComboBox()
        self.stops_combo.addItems(["1 " + tr("STOP", "Stop"), "2 " + tr("STOPS", "Stops"), "3 " + tr("STOPS", "Stops")])
        self.stops_combo.setCurrentIndex(0)
        self.stops_combo.currentIndexChanged.connect(self._on_global_stops_changed)
        layout.addRow(tr("DEFAULT_STOPS", "Default Stops") + ":", self.stops_combo)
        
        # Default tire strategy
        self.tire_combo = QComboBox()
        self._update_tire_combo(1)
        self.tire_combo.currentIndexChanged.connect(self._on_settings_changed)
        layout.addRow(tr("DEFAULT_TIRES", "Default Tire Strategy") + ":", self.tire_combo)
        
        # Use FP2 prediction
        self.use_fp2_check = QCheckBox(tr("USE_FP2_PREDICTION", "Use FP2 Long Run Data for Prediction"))
        self.use_fp2_check.setChecked(True)
        self.use_fp2_check.stateChanged.connect(self._on_settings_changed)
        layout.addRow(self.use_fp2_check)
        
        # Apply to all button
        apply_btn = QPushButton(tr("APPLY_TO_ALL", "Apply to All Drivers"))
        apply_btn.clicked.connect(self._apply_global_to_all)
        layout.addRow(apply_btn)
        
        return group
        
    def _create_driver_settings(self) -> QGroupBox:
        """Create per-driver settings group."""
        group = QGroupBox(tr("DRIVER_STRATEGY_SETTINGS", "Driver Strategy Settings"))
        layout = QVBoxLayout(group)
        
        # Scroll area for many drivers
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Table for driver settings
        self.driver_table = QTableWidget()
        self.driver_table.setColumnCount(5)
        self.driver_table.setHorizontalHeaderLabels([
            tr("POSITION", "Pos"),
            tr("DRIVER", "Driver"),
            tr("STOPS", "Stops"),
            tr("TIRES", "Tires"),
            tr("ACTION", "Action"),
        ])
        
        # Column widths
        self.driver_table.setColumnWidth(0, 50)
        self.driver_table.setColumnWidth(1, 80)
        self.driver_table.setColumnWidth(2, 80)
        self.driver_table.setColumnWidth(3, 120)
        self.driver_table.setColumnWidth(4, 100)
        
        header = self.driver_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        self.driver_table.setAlternatingRowColors(True)
        self.driver_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        scroll.setWidget(self.driver_table)
        layout.addWidget(scroll)
        
        return group
        
    def _update_tire_combo(self, num_stops: int):
        """Update tire strategy combo for given number of stops."""
        self.tire_combo.blockSignals(True)
        self.tire_combo.clear()
        
        strategies = TIRE_STRATEGIES.get(num_stops, TIRE_STRATEGIES[1])
        for strategy in strategies:
            self.tire_combo.addItem("-".join(strategy))
            
        self.tire_combo.blockSignals(False)
        
    def _on_global_stops_changed(self, index: int):
        """Handle global stops change."""
        num_stops = index + 1
        self._update_tire_combo(num_stops)
        self._on_settings_changed()
        
    def _on_settings_changed(self):
        """Handle any settings change."""
        self.settings_changed.emit()
        
    def _apply_global_to_all(self):
        """Apply global settings to all drivers."""
        self._custom_settings.clear()
        self._populate_driver_table()
        self._on_settings_changed()
    
    def load_default_drivers(self):
        """
        Load default 2025 F1 driver list when no FP2 data is available.
        This ensures opponent strategy panel always has drivers to configure.
        """
        default_drivers = [
            {"driver": "VER", "rank": 1, "team": "Red Bull"},
            {"driver": "NOR", "rank": 2, "team": "McLaren"},
            {"driver": "LEC", "rank": 3, "team": "Ferrari"},
            {"driver": "SAI", "rank": 4, "team": "Ferrari"},
            {"driver": "PIA", "rank": 5, "team": "McLaren"},
            {"driver": "RUS", "rank": 6, "team": "Mercedes"},
            {"driver": "HAM", "rank": 7, "team": "Mercedes"},
            {"driver": "PER", "rank": 8, "team": "Red Bull"},
            {"driver": "ALO", "rank": 9, "team": "Aston Martin"},
            {"driver": "STR", "rank": 10, "team": "Aston Martin"},
            {"driver": "GAS", "rank": 11, "team": "Alpine"},
            {"driver": "OCO", "rank": 12, "team": "Alpine"},
            {"driver": "TSU", "rank": 13, "team": "RB"},
            {"driver": "RIC", "rank": 14, "team": "RB"},
            {"driver": "ALB", "rank": 15, "team": "Williams"},
            {"driver": "SAR", "rank": 16, "team": "Williams"},
            {"driver": "MAG", "rank": 17, "team": "Haas"},
            {"driver": "HUL", "rank": 18, "team": "Haas"},
            {"driver": "BOT", "rank": 19, "team": "Sauber"},
            {"driver": "ZHO", "rank": 20, "team": "Sauber"},
        ]
        self._predictions = default_drivers
        self._populate_driver_table()
        
    def load_predictions(self, predictions: List[Dict]):
        """
        Load FP2->Q predictions to populate driver list.
        
        Args:
            predictions: List of prediction dicts with driver, rank, team
        """
        self._predictions = predictions
        self._populate_driver_table()
        
    def _populate_driver_table(self):
        """Populate driver table with predictions."""
        self.driver_table.setRowCount(len(self._predictions))
        
        for row, pred in enumerate(self._predictions):
            driver = pred.get("driver", "N/A")
            rank = pred.get("rank", row + 1)
            team = pred.get("team", "Unknown")
            
            # Position
            pos_item = QTableWidgetItem(str(rank))
            pos_item.setTextAlignment(Qt.AlignCenter)
            pos_item.setFlags(pos_item.flags() & ~Qt.ItemIsEditable)
            self.driver_table.setItem(row, 0, pos_item)
            
            # Driver
            driver_item = QTableWidgetItem(driver)
            driver_item.setTextAlignment(Qt.AlignCenter)
            driver_item.setFlags(driver_item.flags() & ~Qt.ItemIsEditable)
            self.driver_table.setItem(row, 1, driver_item)
            
            # Get custom or default settings
            custom = self._custom_settings.get(driver, {})
            num_stops = custom.get("stops", self.stops_combo.currentIndex() + 1)
            tire_strategy = custom.get("tires", self.tire_combo.currentText())
            
            # Stops combo
            stops_combo = QComboBox()
            stops_combo.addItems(["1", "2", "3"])
            stops_combo.setCurrentIndex(num_stops - 1)
            stops_combo.currentIndexChanged.connect(
                lambda idx, d=driver: self._on_driver_stops_changed(d, idx + 1)
            )
            self.driver_table.setCellWidget(row, 2, stops_combo)
            
            # Tires combo
            tires_combo = QComboBox()
            strategies = TIRE_STRATEGIES.get(num_stops, TIRE_STRATEGIES[1])
            for s in strategies:
                tires_combo.addItem("-".join(s))
            
            # Set current tire strategy
            idx = tires_combo.findText(tire_strategy)
            if idx >= 0:
                tires_combo.setCurrentIndex(idx)
            tires_combo.currentIndexChanged.connect(
                lambda idx, d=driver, tc=tires_combo: self._on_driver_tires_changed(d, tc.currentText())
            )
            self.driver_table.setCellWidget(row, 3, tires_combo)
            
            # Reset button
            reset_btn = QPushButton(tr("RESET", "Reset"))
            reset_btn.setMaximumWidth(80)
            reset_btn.clicked.connect(lambda checked, d=driver: self._reset_driver(d))
            
            if driver in self._custom_settings:
                reset_btn.setStyleSheet("background-color: #FFD700;")
            else:
                reset_btn.setEnabled(False)
                
            self.driver_table.setCellWidget(row, 4, reset_btn)
            
    def _on_driver_stops_changed(self, driver: str, num_stops: int):
        """Handle per-driver stops change."""
        if driver not in self._custom_settings:
            self._custom_settings[driver] = {}
            
        self._custom_settings[driver]["stops"] = num_stops
        
        # Update tire combo for this driver
        self._update_driver_tire_combo(driver, num_stops)
        self._on_settings_changed()
        
    def _update_driver_tire_combo(self, driver: str, num_stops: int):
        """Update tire combo for a specific driver."""
        # Find the row for this driver
        for row in range(self.driver_table.rowCount()):
            driver_item = self.driver_table.item(row, 1)
            if driver_item and driver_item.text() == driver:
                tires_combo = self.driver_table.cellWidget(row, 3)
                if isinstance(tires_combo, QComboBox):
                    tires_combo.blockSignals(True)
                    tires_combo.clear()
                    strategies = TIRE_STRATEGIES.get(num_stops, TIRE_STRATEGIES[1])
                    for s in strategies:
                        tires_combo.addItem("-".join(s))
                    tires_combo.blockSignals(False)
                    
                    # Update custom settings
                    if driver in self._custom_settings:
                        self._custom_settings[driver]["tires"] = tires_combo.currentText()
                        
                # Enable reset button
                reset_btn = self.driver_table.cellWidget(row, 4)
                if isinstance(reset_btn, QPushButton):
                    reset_btn.setEnabled(True)
                    reset_btn.setStyleSheet("background-color: #FFD700;")
                break
                
    def _on_driver_tires_changed(self, driver: str, tires: str):
        """Handle per-driver tires change."""
        if driver not in self._custom_settings:
            self._custom_settings[driver] = {}
            
        self._custom_settings[driver]["tires"] = tires
        
        # Enable reset button
        for row in range(self.driver_table.rowCount()):
            driver_item = self.driver_table.item(row, 1)
            if driver_item and driver_item.text() == driver:
                reset_btn = self.driver_table.cellWidget(row, 4)
                if isinstance(reset_btn, QPushButton):
                    reset_btn.setEnabled(True)
                    reset_btn.setStyleSheet("background-color: #FFD700;")
                break
                
        self._on_settings_changed()
        
    def _reset_driver(self, driver: str):
        """Reset driver to global defaults."""
        if driver in self._custom_settings:
            del self._custom_settings[driver]
            
        self._populate_driver_table()
        self._on_settings_changed()
        
    def get_global_settings(self) -> Dict:
        """Get current global settings."""
        return {
            "num_stops": self.stops_combo.currentIndex() + 1,
            "tire_strategy": self.tire_combo.currentText().split("-"),
            "use_fp2": self.use_fp2_check.isChecked(),
        }
        
    def get_driver_settings(self, driver: str) -> Dict:
        """Get settings for a specific driver (custom or global)."""
        if driver in self._custom_settings:
            custom = self._custom_settings[driver]
            return {
                "num_stops": custom.get("stops", self.stops_combo.currentIndex() + 1),
                "tire_strategy": custom.get("tires", self.tire_combo.currentText()).split("-"),
                "is_custom": True,
            }
        else:
            return {
                "num_stops": self.stops_combo.currentIndex() + 1,
                "tire_strategy": self.tire_combo.currentText().split("-"),
                "is_custom": False,
            }
            
    def get_all_driver_settings(self) -> Dict[str, Dict]:
        """Get settings for all drivers."""
        result = {}
        for pred in self._predictions:
            driver = pred.get("driver", "")
            if driver:
                result[driver] = self.get_driver_settings(driver)
                result[driver]["rank"] = pred.get("rank", 20)
                result[driver]["team"] = pred.get("team", "")
        return result
    
    def display_auto_assigned_strategies(self, auto_strategies: Dict):
        """
        Display auto-assigned strategies in the table.
        
        Called after simulation runs with auto-assigned strategies.
        Updates table to show what strategy each driver is using.
        
        Args:
            auto_strategies: Dict mapping driver_code to OpponentStrategy
        """
        if not auto_strategies:
            return
        
        for row in range(self.driver_table.rowCount()):
            driver_item = self.driver_table.item(row, 1)
            if not driver_item:
                continue
            
            driver = driver_item.text()
            if driver not in auto_strategies:
                continue
            
            strategy = auto_strategies[driver]
            
            # Get tire sequence from OpponentStrategy
            if hasattr(strategy, 'tire_sequence'):
                tire_seq = strategy.tire_sequence
            elif isinstance(strategy, dict):
                tire_seq = strategy.get('tire_sequence', ['M', 'H'])
            else:
                continue
            
            num_stops = len(tire_seq) - 1
            tire_str = "-".join(tire_seq)
            
            # Update stops combo
            stops_combo = self.driver_table.cellWidget(row, 2)
            if isinstance(stops_combo, QComboBox):
                stops_combo.blockSignals(True)
                if 0 <= num_stops <= 2:
                    stops_combo.setCurrentIndex(num_stops)
                stops_combo.blockSignals(False)
            
            # Update tires combo
            tires_combo = self.driver_table.cellWidget(row, 3)
            if isinstance(tires_combo, QComboBox):
                tires_combo.blockSignals(True)
                tires_combo.clear()
                strategies = TIRE_STRATEGIES.get(num_stops + 1, TIRE_STRATEGIES[1])
                for s in strategies:
                    tires_combo.addItem("-".join(s))
                
                # Try to find the matching strategy
                idx = tires_combo.findText(tire_str)
                if idx >= 0:
                    tires_combo.setCurrentIndex(idx)
                else:
                    # Add the auto-assigned strategy if not in list
                    tires_combo.addItem(tire_str)
                    tires_combo.setCurrentIndex(tires_combo.count() - 1)
                tires_combo.blockSignals(False)
            
            # Mark as auto-assigned (not custom) by disabling reset button
            reset_btn = self.driver_table.cellWidget(row, 4)
            if isinstance(reset_btn, QPushButton):
                if driver not in self._custom_settings:
                    reset_btn.setEnabled(False)
                    reset_btn.setStyleSheet("")  # Clear yellow
        
        print(f"[OPPONENT_PANEL] Displayed auto-assigned strategies for {len(auto_strategies)} drivers")

