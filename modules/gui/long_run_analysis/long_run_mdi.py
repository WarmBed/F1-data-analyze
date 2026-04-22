#!/usr/bin/env python3
"""
Long Run Analysis MDI Module

Main MDI window for Long Run & Degradation Analysis.
Provides tabbed interface for stint selection, fuel settings, 
track evolution, and degradation results.

API-ONLY Mode (2025-10-03):
- Uses Function 28 API for lap time data
- No direct FastF1 calls from GUI
- No automatic CLI subprocess invocation

Author: F1T Team
Date: 2025-12-30
Version: 1.0.0
"""

import sys
import time
from pathlib import Path

# CRITICAL: Add project root to sys.path FIRST to ensure 'core' module
# is resolved from project root, not from strategy_simulator/core/
def _setup_project_path():
    """Find project root and add it to sys.path at position 0."""
    current = Path(__file__).resolve().parent
    for _ in range(10):  # Prevent infinite loop
        # Check for both 'core' folder AND 'logger.py' to confirm it's the project root
        if (current / 'core' / 'logger.py').exists():
            # Remove any existing entries that might conflict
            str_path = str(current)
            while str_path in sys.path:
                sys.path.remove(str_path)
            # Insert at position 0 to take priority
            sys.path.insert(0, str_path)
            return current
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent
    return None

_PROJECT_ROOT = _setup_project_path()

from typing import Dict, Any, Optional, List, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QMessageBox, QSplitter, QFrame, QStatusBar, QPushButton,
    QProgressBar, QSizePolicy, QComboBox, QGroupBox, QGridLayout,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
    QCheckBox, QSpinBox, QDoubleSpinBox, QFormLayout, QTableWidget,
    QTableWidgetItem, QDialog, QDialogButtonBox, QRadioButton,
    QButtonGroup, QListWidget, QListWidgetItem, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QBrush

# Import core modules using absolute path to avoid conflict with strategy_simulator/core
_core_logger = None
_core_gui_i18n = None

def _import_core_module(module_name: str):
    """Import a module from project_root/core/ using absolute path."""
    import importlib.util
    if _PROJECT_ROOT is None:
        return None
    module_path = _PROJECT_ROOT / 'core' / f'{module_name}.py'
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f'_core_{module_name}', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _get_logger():
    global _core_logger
    if _core_logger is None:
        mod = _import_core_module('logger')
        if mod:
            _core_logger = mod.get_logger(__name__)
        else:
            # Fallback: use standard logging
            import logging
            _core_logger = logging.getLogger(__name__)
    return _core_logger

def _lazy_tr(key: str, default: str) -> str:
    """Lazy translation function"""
    global _core_gui_i18n
    try:
        if _core_gui_i18n is None:
            _core_gui_i18n = _import_core_module('gui_i18n')
        if _core_gui_i18n and hasattr(_core_gui_i18n, 'tr'):
            return _core_gui_i18n.tr(key, default)
    except Exception:
        pass
    return default


class LongRunAnalysis(QWidget):
    """
    Long Run & Degradation Analysis MDI Widget
    
    Provides a tabbed interface for:
    - Stint Selection: Auto-detect and manually select long run stints
    - Fuel Settings: Configure per-driver fuel parameters
    - Track Evolution: View track evolution estimation
    - Degradation Results: Fuel-corrected degradation rates
    - Chart View: Visual degradation comparison
    """
    
    # Signals
    data_loaded = pyqtSignal(object)
    load_error = pyqtSignal(str)
    load_progress = pyqtSignal(int)
    analysis_complete = pyqtSignal(dict)
    
    def __init__(self, year: int = 2025, race: str = "Japan", 
                 session: str = "FP2", parent=None):
        super().__init__(parent)
        
        self.year = year
        self.race = race
        self.session = session
        
        # Analysis type for parameter change detection
        self.analysis_type = 'long_run'
        
        # State
        self._data: Optional[Dict[str, Any]] = None
        self._is_loading: bool = False
        self._data_loader = None
        self._last_loaded_signature: Optional[Tuple[int, str, str]] = None
        self._last_loaded_at: float = 0.0
        self._team_fuel_habits: Dict[str, Dict] = {}  # Team -> habits data
        
        # Load team fuel habits training data
        self._load_team_fuel_habits()
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
        # Auto-load data if parameters provided
        if year and race and session:
            QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        """Setup the main UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 2)
        layout.setSpacing(0)
        
        # Main tab widget (no header, maximized space)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        layout.addWidget(self.tab_widget, 1)
        
        # Create tabs
        self._create_tabs()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.hide()
        self.status_bar.addPermanentWidget(self.progress_bar)
        layout.addWidget(self.status_bar)
        
        self._update_status(_lazy_tr("long_run.ready", "Ready"))
    
    def _create_header(self) -> QWidget:
        """Create header widget with session info only (no title to save space)"""
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 2, 8, 2)
        
        layout.addStretch()
        
        # Session info only (title removed to save space)
        session_info = QLabel(f"{self.year} {self.race} - {self.session}")
        session_info.setStyleSheet("color: #888;")
        layout.addWidget(session_info)
        
        # Refresh button
        refresh_btn = QPushButton(_lazy_tr("common.refresh", "Refresh"))
        refresh_btn.clicked.connect(self._load_data)
        layout.addWidget(refresh_btn)
        
        return header
    
    def _load_team_fuel_habits(self):
        """
        Load team fuel habits - API-ONLY 模式下此方法不再主動載入本地 JSON
        
        燃油習慣數據現在從 Function 28 API 返回，在 _on_data_loaded 中處理
        此方法保留作為向後兼容的入口點（初始化時調用但不執行實際載入）
        """
        # API-ONLY 模式：不再主動載入本地 JSON
        # 燃油習慣數據將在 _on_data_loaded 中從 API 數據提取
        _get_logger().debug("Team fuel habits will be loaded from API data")
    
    def _load_team_fuel_habits_local(self):
        """
        備用方法：從本地 JSON 載入車隊燃油習慣
        
        僅當 API 沒有返回 team_fuel_habits 時才調用此方法
        """
        try:
            import json
            
            # 🔧 EXE 模式路徑處理
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # EXE 模式：從 PyInstaller 解壓目錄載入
                base_path = Path(sys._MEIPASS)
            elif _PROJECT_ROOT:
                base_path = Path(_PROJECT_ROOT)
            else:
                # 後備：使用當前文件的父目錄向上查找
                base_path = Path(__file__).resolve().parent.parent.parent.parent
            
            habits_path = base_path / 'training_data' / 'team_fuel_habits.json'
            
            if not habits_path.exists():
                _get_logger().warning(f"[FALLBACK] Team fuel habits file not found: {habits_path}")
                return
            
            with open(habits_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._team_fuel_habits = data.get('team_habits', {})
            
            _get_logger().info(f"[FALLBACK] Loaded team fuel habits from local file: {len(self._team_fuel_habits)} teams")
            
        except Exception as e:
            _get_logger().error(f"[FALLBACK] Failed to load team fuel habits: {e}")
            self._team_fuel_habits = {}
    
    def _get_recommended_sim_lap(self, team_name: str) -> int:
        """
        Get recommended simulate from lap based on team fuel habits.
        
        Args:
            team_name: Team name (e.g., "Red Bull Racing")
        
        Returns:
            Recommended lap number (0 = use FP2 mode, >0 = race sim mode)
        """
        if not self._team_fuel_habits or team_name not in self._team_fuel_habits:
            return 0  # Default: FP2 mode
        
        habits = self._team_fuel_habits[team_name]
        
        # Estimate FP2 fuel load in kg
        fp2_fuel_kg = habits.get('estimated_fp2_fuel_kg', 0)
        
        if fp2_fuel_kg <= 0:
            return 0  # No data, use FP2 mode
        
        # Constants (from learn_team_fuel_habits.py)
        FUEL_COEF = 0.032  # s/kg
        RACE_START_FUEL_KG = 110  # Race start fuel (full tank)
        RACE_FUEL_PER_LAP_KG = 1.8  # Fuel consumption per lap
        
        # Calculate which race lap would have similar fuel load as FP2
        # FP2_fuel = RACE_START - (lap * FUEL_PER_LAP)
        # lap = (RACE_START - FP2_fuel) / FUEL_PER_LAP
        
        sim_lap = round((RACE_START_FUEL_KG - fp2_fuel_kg) / RACE_FUEL_PER_LAP_KG)
        
        # Clamp to reasonable range
        sim_lap = max(0, min(sim_lap, 40))
        
        return sim_lap
    
    def _get_driver_team(self, driver_code: str) -> Optional[str]:
        """
        Get team name for a driver.
        
        Args:
            driver_code: Driver code (e.g., "VER")
        
        Returns:
            Team name or None if not found
        """
        # Try to get from data first
        if hasattr(self, '_data') and self._data:
            # Check if data contains team info
            if 'all_drivers_detailed_laptime' in self._data:
                driver_data = self._data['all_drivers_detailed_laptime'].get(driver_code)
                if isinstance(driver_data, dict) and 'team' in driver_data:
                    team = driver_data['team']
                    _get_logger().info(f"Driver {driver_code} team from data: {team}")
                    return team
        
        # Fallback: 2025 driver-team mapping (expanded)
        DRIVER_TEAM_2025 = {
            # Red Bull Racing
            'VER': 'Red Bull Racing',
            'PER': 'Red Bull Racing',
            # McLaren
            'NOR': 'McLaren',
            'PIA': 'McLaren',
            # Ferrari
            'LEC': 'Ferrari',
            'SAI': 'Ferrari',
            'HAM': 'Ferrari',  # 2025 transfer
            # Mercedes
            'RUS': 'Mercedes',
            'ANT': 'Mercedes',  # Antonelli (2025 rookie)
            # Aston Martin
            'ALO': 'Aston Martin',
            'STR': 'Aston Martin',
            # Racing Bulls (RB)
            'TSU': 'Racing Bulls',
            'LAW': 'Racing Bulls',
            'HAD': 'Racing Bulls',  # Hadjar (potential 2025)
            # Haas F1 Team
            'HUL': 'Haas F1 Team',
            'MAG': 'Haas F1 Team',
            'BEA': 'Haas F1 Team',  # Bearman (2025)
            # Alpine
            'GAS': 'Alpine',
            'OCO': 'Alpine',
            'DOO': 'Alpine',  # Doohan (2025)
            # Williams
            'ALB': 'Williams',
            'SAR': 'Williams',
            'COL': 'Williams',  # Colapinto (test/reserve)
            # Kick Sauber (Alfa Romeo)
            'BOT': 'Kick Sauber',
            'ZHO': 'Kick Sauber',
            'POR': 'Kick Sauber',  # Pourchaire (reserve)
        }
        
        team = DRIVER_TEAM_2025.get(driver_code)
        if team:
            _get_logger().info(f"Driver {driver_code} team from mapping: {team}")
        else:
            _get_logger().warning(f"Driver {driver_code} not found in mapping")
        
        return team
    
    def _create_tabs(self):
        """Create the tab pages"""
        # Tab 1: Stint Selector
        self.stint_tab = self._create_stint_selector_tab()
        self.tab_widget.addTab(self.stint_tab, 
                               _lazy_tr("long_run.tab.stint", "Stint Selection"))
        
        # Tab 2: Fuel Settings
        self.fuel_tab = self._create_fuel_settings_tab()
        self.tab_widget.addTab(self.fuel_tab, 
                               _lazy_tr("long_run.tab.fuel", "Fuel Settings"))
        
        # Tab 3: Track Evolution
        self.track_tab = self._create_track_evolution_tab()
        self.tab_widget.addTab(self.track_tab, 
                               _lazy_tr("long_run.tab.track", "Track Evolution"))
        
        # Tab 4: Degradation Results
        self.results_tab = self._create_results_tab()
        self.tab_widget.addTab(self.results_tab, 
                               _lazy_tr("long_run.tab.results", "Degradation Results"))
        
        # Tab 5: Chart View
        self.chart_tab = self._create_chart_tab()
        self.tab_widget.addTab(self.chart_tab, 
                               _lazy_tr("long_run.tab.chart", "Chart View"))
    
    def _create_stint_selector_tab(self) -> QWidget:
        """Create stint selector tab with driver/stint tree"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Import widgets
        from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QHeaderView, 
                                     QSpinBox, QCheckBox)
        from PyQt5.QtGui import QColor, QBrush
        
        # Filter controls
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.addWidget(QLabel(_lazy_tr("long_run.min_laps", "Min consecutive laps:")))
        
        self.min_laps_spin = QSpinBox()
        self.min_laps_spin.setRange(3, 20)
        self.min_laps_spin.setValue(4)
        self.min_laps_spin.valueChanged.connect(self._detect_long_runs)
        filter_layout.addWidget(self.min_laps_spin)
        
        # Checkbox to ignore pit laps
        self.ignore_pit_laps_cb = QCheckBox(_lazy_tr("long_run.ignore_pit", "Ignore pit laps"))
        self.ignore_pit_laps_cb.setChecked(True)
        self.ignore_pit_laps_cb.stateChanged.connect(self._detect_long_runs)
        filter_layout.addWidget(self.ignore_pit_laps_cb)
        
        filter_layout.addStretch()
        
        detect_btn = QPushButton(_lazy_tr("long_run.auto_detect", "Auto Detect Long Runs"))
        detect_btn.clicked.connect(self._detect_long_runs)
        filter_layout.addWidget(detect_btn)
        
        layout.addWidget(filter_frame)
        
        # Stint tree (grouped by driver)
        self.stint_tree = QTreeWidget()
        self.stint_tree.setColumnCount(6)
        self.stint_tree.setHeaderLabels([
            _lazy_tr("long_run.col.driver_stint", "Driver / Stint"),
            _lazy_tr("long_run.col.laps", "Laps"),
            _lazy_tr("long_run.col.compound", "Compound"),
            _lazy_tr("long_run.col.avg_time", "Avg Time"),
            _lazy_tr("long_run.col.status", "Status"),
            _lazy_tr("long_run.col.action", "Action")
        ])
        self.stint_tree.setAlternatingRowColors(True)
        self.stint_tree.setRootIsDecorated(True)
        self.stint_tree.itemDoubleClicked.connect(self._on_stint_edit)
        
        # Set column widths
        header = self.stint_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.stint_tree, 1)
        
        # Placeholder label (shown when no data)
        self.stint_placeholder = QLabel(_lazy_tr("long_run.stint.placeholder", 
                                       "Stint selection will be available after data loads"))
        self.stint_placeholder.setAlignment(Qt.AlignCenter)
        self.stint_placeholder.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.stint_placeholder)
        
        # Initially hide tree, show placeholder
        self.stint_tree.hide()
        
        return tab
    
    def _get_driver_color(self, driver_code: str) -> str:
        """Get driver color from color palette provider"""
        try:
            from modules.gui.themes import color_palette_provider
            color = color_palette_provider.get_driver_color(driver_code, format='hex')
            return color if color else '#CCCCCC'
        except Exception:
            return '#CCCCCC'
    
    def _create_fuel_settings_tab(self) -> QWidget:
        """Create fuel settings tab with per-driver fuel configuration"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        
        from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, 
                                     QDoubleSpinBox, QSpinBox)
        
        # Track defaults frame
        defaults_frame = QGroupBox(_lazy_tr("long_run.fuel.track_defaults", "Track Default Values"))
        defaults_layout = QGridLayout(defaults_frame)
        
        # Row 0: Race Simulation Settings
        # Race Start Fuel
        defaults_layout.addWidget(QLabel(_lazy_tr("long_run.fuel.race_start", "Race Start Fuel (kg):")), 0, 0)
        self.race_start_fuel_spin = QDoubleSpinBox()
        self.race_start_fuel_spin.setRange(50.0, 115.0)
        self.race_start_fuel_spin.setValue(110.0)
        self.race_start_fuel_spin.setDecimals(1)
        self.race_start_fuel_spin.setSingleStep(5.0)
        self.race_start_fuel_spin.setSuffix(" kg")
        defaults_layout.addWidget(self.race_start_fuel_spin, 0, 1)
        
        # Row 1: Fuel Parameters
        # Fuel consumption per lap
        defaults_layout.addWidget(QLabel(_lazy_tr("long_run.fuel.consumption", "Fuel consumption (kg/lap):")), 0, 2)
        self.fuel_consumption_spin = QDoubleSpinBox()
        self.fuel_consumption_spin.setRange(1.0, 3.0)
        self.fuel_consumption_spin.setValue(1.65)
        self.fuel_consumption_spin.setDecimals(2)
        self.fuel_consumption_spin.setSingleStep(0.05)
        defaults_layout.addWidget(self.fuel_consumption_spin, 0, 3)
        
        # Fuel effect (seconds per kg)
        defaults_layout.addWidget(QLabel(_lazy_tr("long_run.fuel.effect", "Fuel effect (s/kg):")), 1, 0)
        self.fuel_effect_spin = QDoubleSpinBox()
        self.fuel_effect_spin.setRange(0.01, 0.10)
        self.fuel_effect_spin.setValue(0.030)
        self.fuel_effect_spin.setDecimals(3)
        self.fuel_effect_spin.setSingleStep(0.005)
        defaults_layout.addWidget(self.fuel_effect_spin, 1, 1)
        
        # Apply to all button
        apply_all_btn = QPushButton(_lazy_tr("long_run.fuel.apply_all", "Apply to All Drivers"))
        apply_all_btn.clicked.connect(self._apply_fuel_defaults_to_all)
        defaults_layout.addWidget(apply_all_btn, 1, 2)
        
        layout.addWidget(defaults_frame)
        
        # Per-driver fuel table
        self.fuel_table = QTableWidget()
        self.fuel_table.setColumnCount(5)
        self.fuel_table.setHorizontalHeaderLabels([
            _lazy_tr("long_run.fuel.col.driver", "Driver"),
            _lazy_tr("long_run.fuel.col.start_fuel", "Start Fuel (kg)"),
            _lazy_tr("long_run.fuel.col.consumption", "Consumption (kg/lap)"),
            _lazy_tr("long_run.fuel.col.effect", "Effect (s/kg)"),
            _lazy_tr("long_run.fuel.col.use_default", "Use Default")
        ])
        self.fuel_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.fuel_table, 1)
        
        # Placeholder
        self.fuel_placeholder = QLabel(_lazy_tr("long_run.fuel.placeholder", 
                                       "Fuel settings will be available after data loads"))
        self.fuel_placeholder.setAlignment(Qt.AlignCenter)
        self.fuel_placeholder.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.fuel_placeholder)
        
        # Initially hide table
        self.fuel_table.hide()
        
        # Tips
        tips = QLabel(_lazy_tr("long_run.fuel.tips", 
                              "Tip: FP sessions typically use 60-100 kg, race start uses ~110 kg"))
        tips.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(tips)
        
        return tab
    
    def _populate_fuel_table(self):
        """Populate the fuel settings table with driver data"""
        if not hasattr(self, 'fuel_table') or not hasattr(self, '_raw_lap_data'):
            return
        
        self.fuel_table.setRowCount(0)
        
        # Get unique drivers
        drivers = list(self._raw_lap_data.keys())
        self.fuel_table.setRowCount(len(drivers))
        
        # Also populate reference driver combo for track evolution
        if hasattr(self, 'ref_driver_combo'):
            self.ref_driver_combo.clear()
            self.ref_driver_combo.addItems(drivers)
        
        for row, driver in enumerate(drivers):
            # Column 0: Driver code (with color)
            driver_item = QTableWidgetItem(driver)
            color = self._get_driver_color(driver)
            if color:
                driver_item.setBackground(QColor(color))
                # Set text color based on background brightness
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                driver_item.setForeground(QColor('#000000' if brightness > 128 else '#ffffff'))
            self.fuel_table.setItem(row, 0, driver_item)
            
            # Column 1: Start Fuel (kg) - spinbox
            start_fuel_spin = QDoubleSpinBox()
            start_fuel_spin.setRange(50.0, 110.0)
            start_fuel_spin.setValue(105.0)  # Typical race start fuel
            start_fuel_spin.setSuffix(" kg")
            start_fuel_spin.setDecimals(1)
            self.fuel_table.setCellWidget(row, 1, start_fuel_spin)
            
            # Column 2: Consumption (kg/lap) - spinbox
            consumption_spin = QDoubleSpinBox()
            consumption_spin.setRange(1.0, 3.0)
            consumption_spin.setValue(self.fuel_consumption_spin.value())
            consumption_spin.setSuffix(" kg/lap")
            consumption_spin.setDecimals(2)
            self.fuel_table.setCellWidget(row, 2, consumption_spin)
            
            # Column 3: Fuel Effect (s/kg) - spinbox
            effect_spin = QDoubleSpinBox()
            effect_spin.setRange(0.010, 0.100)
            effect_spin.setValue(self.fuel_effect_spin.value())
            effect_spin.setSuffix(" s/kg")
            effect_spin.setDecimals(3)
            effect_spin.setSingleStep(0.005)
            self.fuel_table.setCellWidget(row, 3, effect_spin)
            
            # Column 4: Use Default - checkbox
            use_default_cb = QCheckBox()
            use_default_cb.setChecked(True)
            use_default_cb.setToolTip(_lazy_tr("long_run.fuel.use_default_tip", 
                                                "Use track default values"))
            # Center the checkbox
            cb_container = QWidget()
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.addWidget(use_default_cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.fuel_table.setCellWidget(row, 4, cb_container)
        
        self.fuel_table.resizeColumnsToContents()
        
        # Show table and hide placeholder
        self.fuel_table.show()
        if hasattr(self, 'fuel_placeholder'):
            self.fuel_placeholder.hide()
    
    def _apply_fuel_defaults_to_all(self):
        """Apply default fuel values to all drivers"""
        if not hasattr(self, 'fuel_table') or self.fuel_table.rowCount() == 0:
            return
        
        start_fuel = self.race_start_fuel_spin.value()
        consumption = self.fuel_consumption_spin.value()
        effect = self.fuel_effect_spin.value()
        
        for row in range(self.fuel_table.rowCount()):
            # Update start fuel (column 1)
            start_fuel_widget = self.fuel_table.cellWidget(row, 1)
            if isinstance(start_fuel_widget, QDoubleSpinBox):
                start_fuel_widget.setValue(start_fuel)
            
            # Update consumption (column 2)
            consumption_widget = self.fuel_table.cellWidget(row, 2)
            if isinstance(consumption_widget, QDoubleSpinBox):
                consumption_widget.setValue(consumption)
            
            # Update effect (column 3)
            effect_widget = self.fuel_table.cellWidget(row, 3)
            if isinstance(effect_widget, QDoubleSpinBox):
                effect_widget.setValue(effect)
    
    def _create_track_evolution_tab(self) -> QWidget:
        """Create track evolution tab with calculation method selection"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Method Selection GroupBox
        method_group = QGroupBox(_lazy_tr("long_run.track.method", "Calculation Method"))
        method_layout = QVBoxLayout(method_group)
        
        # Radio buttons for method selection
        self.track_evo_method_group = QButtonGroup(tab)
        
        # Method 1: Statistical
        self.stat_method_rb = QRadioButton(_lazy_tr("long_run.track.statistical", 
                                                     "Statistical (median of all drivers)"))
        self.stat_method_rb.setToolTip(_lazy_tr("long_run.track.statistical_tip",
            "Calculate track evolution by taking the median improvement across all drivers per lap"))
        self.track_evo_method_group.addButton(self.stat_method_rb, 0)
        method_layout.addWidget(self.stat_method_rb)
        
        # Method 2: Reference Driver
        ref_driver_layout = QHBoxLayout()
        self.ref_driver_rb = QRadioButton(_lazy_tr("long_run.track.reference", 
                                                    "Reference Driver:"))
        self.ref_driver_rb.setToolTip(_lazy_tr("long_run.track.reference_tip",
            "Use a single driver's improvement curve as the reference"))
        self.track_evo_method_group.addButton(self.ref_driver_rb, 1)
        ref_driver_layout.addWidget(self.ref_driver_rb)
        
        self.ref_driver_combo = QComboBox()
        self.ref_driver_combo.setMinimumWidth(80)
        self.ref_driver_combo.setEnabled(False)
        ref_driver_layout.addWidget(self.ref_driver_combo)
        ref_driver_layout.addStretch()
        method_layout.addLayout(ref_driver_layout)
        
        # Connect radio to enable/disable combo
        self.ref_driver_rb.toggled.connect(self.ref_driver_combo.setEnabled)
        
        # Method 3: Hybrid
        self.hybrid_method_rb = QRadioButton(_lazy_tr("long_run.track.hybrid", 
                                                       "Hybrid (statistical + tire aging filter)"))
        self.hybrid_method_rb.setToolTip(_lazy_tr("long_run.track.hybrid_tip",
            "Use statistical method but filter out early tire warm-up laps"))
        self.track_evo_method_group.addButton(self.hybrid_method_rb, 2)
        method_layout.addWidget(self.hybrid_method_rb)
        
        # Default selection
        self.stat_method_rb.setChecked(True)
        
        layout.addWidget(method_group)
        
        # Parameters GroupBox
        params_group = QGroupBox(_lazy_tr("long_run.track.params", "Parameters"))
        params_layout = QFormLayout(params_group)
        
        # Window size for smoothing
        self.track_window_spin = QSpinBox()
        self.track_window_spin.setRange(1, 10)
        self.track_window_spin.setValue(3)
        self.track_window_spin.setToolTip(_lazy_tr("long_run.track.window_tip",
            "Number of laps to use for rolling average smoothing"))
        params_layout.addRow(_lazy_tr("long_run.track.window", "Smoothing Window (laps):"), 
                             self.track_window_spin)
        
        # Outlier threshold
        self.track_outlier_spin = QDoubleSpinBox()
        self.track_outlier_spin.setRange(1.0, 5.0)
        self.track_outlier_spin.setValue(2.0)
        self.track_outlier_spin.setSuffix(" sigma")
        self.track_outlier_spin.setDecimals(1)
        self.track_outlier_spin.setToolTip(_lazy_tr("long_run.track.outlier_tip",
            "Remove outliers beyond this standard deviation threshold"))
        params_layout.addRow(_lazy_tr("long_run.track.outlier", "Outlier Threshold:"), 
                             self.track_outlier_spin)
        
        layout.addWidget(params_group)
        
        # Calculate Button
        calc_btn = QPushButton(_lazy_tr("long_run.track.calculate", "Calculate Track Evolution"))
        calc_btn.clicked.connect(self._calculate_track_evolution)
        layout.addWidget(calc_btn)
        
        # Preview Chart placeholder
        preview_group = QGroupBox(_lazy_tr("long_run.track.preview", "Preview"))
        preview_layout = QVBoxLayout(preview_group)
        
        self.track_evo_label = QLabel(_lazy_tr("long_run.track.no_data", 
                                                "No track evolution data yet. Load data and calculate."))
        self.track_evo_label.setAlignment(Qt.AlignCenter)
        self.track_evo_label.setStyleSheet("color: #888; font-size: 12px;")
        preview_layout.addWidget(self.track_evo_label)
        
        layout.addWidget(preview_group)
        layout.addStretch()
        
        return tab
    
    def _calculate_track_evolution(self):
        """Calculate track evolution based on selected method"""
        _get_logger().info("Calculate Track Evolution button clicked")
        
        if not hasattr(self, '_raw_lap_data') or not self._raw_lap_data:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(None, 
                               _lazy_tr("long_run.track.no_data_title", "No Data"),
                               _lazy_tr("long_run.track.no_data_msg", "Please load session data first."))
            return
        
        method = self.track_evo_method_group.checkedId()
        method_names = {0: "Statistical", 1: "Reference Driver", 2: "Hybrid"}
        method_name = method_names.get(method, "Unknown")
        
        _get_logger().info(f"Track evolution calculation: method={method_name}")
        
        # Collect selected stints from stint tree
        selected_stints = self._get_selected_stints()
        if not selected_stints:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(None,
                               _lazy_tr("long_run.track.no_stints_title", "No Stints Selected"),
                               _lazy_tr("long_run.track.no_stints_msg", 
                                        "Please select at least one stint in 'Stint Selection' tab."))
            return
        
        # Calculate track evolution based on method
        try:
            if method == 0:  # Statistical
                track_evo_data = self._calculate_statistical_track_evo(selected_stints)
            elif method == 1:  # Reference Driver
                ref_driver = self.ref_driver_combo.currentText()
                if not ref_driver:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(None,
                                       _lazy_tr("long_run.track.no_ref_title", "No Reference Driver"),
                                       _lazy_tr("long_run.track.no_ref_msg", 
                                                "Please select a reference driver."))
                    return
                track_evo_data = self._calculate_reference_track_evo(selected_stints, ref_driver)
            else:  # Hybrid
                ref_driver = self.ref_driver_combo.currentText()
                track_evo_data = self._calculate_hybrid_track_evo(selected_stints, ref_driver)
            
            # Store result
            self._track_evolution = track_evo_data
            
            # Update preview
            if track_evo_data:
                total_evo = track_evo_data.get('total_evolution', 0)
                per_lap = track_evo_data.get('per_lap_evolution', 0)
                lap_count = track_evo_data.get('lap_count', 0)
                
                result_text = _lazy_tr("long_run.track.result",
                    "Track Evolution Calculated!\n\n"
                    "Method: {}\n"
                    "Lap Range: {} laps\n"
                    "Total Evolution: {:.3f}s\n"
                    "Per Lap: {:.4f}s/lap\n"
                    "(Negative = track getting faster)").format(
                        method_name, lap_count, total_evo, per_lap)
                
                self.track_evo_label.setText(result_text)
                self.track_evo_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(None,
                                       _lazy_tr("long_run.track.success_title", "Calculation Complete"),
                                       _lazy_tr("long_run.track.success_msg",
                                                "Track evolution calculated successfully.\n"
                                                "Total: {:.3f}s over {} laps").format(total_evo, lap_count))
            else:
                self.track_evo_label.setText(_lazy_tr("long_run.track.no_result",
                    "Could not calculate track evolution.\nInsufficient data."))
                self.track_evo_label.setStyleSheet("color: #F44336; font-size: 12px;")
                
        except Exception as e:
            _get_logger().error(f"Track evolution calculation error: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(None,
                                _lazy_tr("long_run.track.error_title", "Calculation Error"),
                                _lazy_tr("long_run.track.error_msg", 
                                         "Error calculating track evolution:\n{}").format(str(e)))
    
    def _get_selected_stints(self) -> List[Dict]:
        """Get all selected stints from the stint tree
        
        Returns:
            List of stint dictionaries with 'driver' field added
        """
        selected = []
        if not hasattr(self, 'stint_tree'):
            return selected
        
        for i in range(self.stint_tree.topLevelItemCount()):
            driver_item = self.stint_tree.topLevelItem(i)
            for j in range(driver_item.childCount()):
                stint_item = driver_item.child(j)
                if stint_item.checkState(0) == Qt.Checked:
                    stint_data = stint_item.data(0, Qt.UserRole)
                    if stint_data and stint_data.get('type') == 'stint':
                        # Extract stint info and add driver field
                        stint_info = stint_data.get('stint', {}).copy()
                        stint_info['driver'] = stint_data.get('driver', '')
                        selected.append(stint_info)
        return selected
    
    def _calculate_statistical_track_evo(self, selected_stints: List[Dict]) -> Dict:
        """Calculate track evolution using statistical median method"""
        _get_logger().info(f"Calculating statistical track evo for {len(selected_stints)} stints")
        
        # Collect all lap times organized by lap number
        lap_times_by_number = {}
        
        for stint in selected_stints:
            driver = stint.get('driver', '')
            # Use valid lap range (excluding pit laps)
            start_lap = stint.get('valid_start_lap', stint.get('start_lap', 0))
            end_lap = stint.get('valid_end_lap', stint.get('end_lap', 0))
            pit_laps = stint.get('pit_laps', [])
            
            if driver in self._raw_lap_data:
                driver_info = self._raw_lap_data[driver]
                
                # Handle different data structures
                if isinstance(driver_info, dict):
                    laps = driver_info.get('detailed_lap_data', [])
                elif isinstance(driver_info, list):
                    laps = driver_info
                else:
                    laps = []
                
                for lap in laps:
                    if not isinstance(lap, dict):
                        continue
                    lap_num = lap.get('lap_number', 0)
                    # Skip pit laps
                    if lap_num in pit_laps:
                        continue
                    if start_lap <= lap_num <= end_lap:
                        lap_time = lap.get('lap_time_seconds', 0)
                        if lap_time and lap_time > 0:
                            if lap_num not in lap_times_by_number:
                                lap_times_by_number[lap_num] = []
                            lap_times_by_number[lap_num].append(lap_time)
        
        if not lap_times_by_number:
            return {}
        
        # Calculate median for each lap
        import statistics
        lap_numbers = sorted(lap_times_by_number.keys())
        medians = {}
        for lap_num in lap_numbers:
            times = lap_times_by_number[lap_num]
            if len(times) >= 1:
                medians[lap_num] = statistics.median(times)
        
        if not medians:
            return {}
        
        # Calculate evolution relative to first lap
        first_lap = min(medians.keys())
        baseline = medians[first_lap]
        
        evolution = {lap: time - baseline for lap, time in medians.items()}
        total_evo = medians[max(medians.keys())] - baseline
        lap_count = len(medians)
        per_lap = total_evo / max(1, lap_count - 1)
        
        return {
            'method': 'Statistical',
            'evolution_by_lap': evolution,
            'total_evolution': total_evo,
            'per_lap_evolution': per_lap,
            'lap_count': lap_count,
            'baseline_lap': first_lap
        }
    
    def _calculate_reference_track_evo(self, selected_stints: List[Dict], ref_driver: str) -> Dict:
        """Calculate track evolution using reference driver method"""
        _get_logger().info(f"Calculating reference track evo using {ref_driver}")
        
        # Find the reference driver's fresh tire stint
        if ref_driver not in self._raw_lap_data:
            return {}
        
        driver_info = self._raw_lap_data[ref_driver]
        
        # Handle different data structures
        if isinstance(driver_info, dict):
            ref_laps = driver_info.get('detailed_lap_data', [])
        elif isinstance(driver_info, list):
            ref_laps = driver_info
        else:
            ref_laps = []
        
        # Use reference driver lap times as baseline
        lap_times = {}
        for lap in ref_laps:
            if not isinstance(lap, dict):
                continue
            lap_num = lap.get('lap_number', 0)
            lap_time = lap.get('lap_time_seconds', 0)
            tire_life = lap.get('tire_life', 1)
            
            # Only use early tire laps (fresh tire)
            if lap_time and lap_time > 0 and tire_life <= 3:
                lap_times[lap_num] = lap_time
        
        if not lap_times:
            return {}
        
        first_lap = min(lap_times.keys())
        baseline = lap_times[first_lap]
        
        evolution = {lap: time - baseline for lap, time in lap_times.items()}
        total_evo = lap_times.get(max(lap_times.keys()), baseline) - baseline
        lap_count = len(lap_times)
        per_lap = total_evo / max(1, lap_count - 1)
        
        return {
            'method': f'Reference ({ref_driver})',
            'evolution_by_lap': evolution,
            'total_evolution': total_evo,
            'per_lap_evolution': per_lap,
            'lap_count': lap_count,
            'baseline_lap': first_lap
        }
    
    def _calculate_hybrid_track_evo(self, selected_stints: List[Dict], ref_driver: str) -> Dict:
        """Calculate track evolution using hybrid method (statistical + reference weighted)"""
        _get_logger().info(f"Calculating hybrid track evo")
        
        stat_result = self._calculate_statistical_track_evo(selected_stints)
        ref_result = self._calculate_reference_track_evo(selected_stints, ref_driver) if ref_driver else {}
        
        if stat_result and ref_result:
            # Weighted average: 70% statistical, 30% reference
            stat_weight = 0.7
            ref_weight = 0.3
            
            total_evo = (stat_result['total_evolution'] * stat_weight + 
                        ref_result['total_evolution'] * ref_weight)
            per_lap = (stat_result['per_lap_evolution'] * stat_weight + 
                      ref_result['per_lap_evolution'] * ref_weight)
            
            return {
                'method': 'Hybrid (70% Stat + 30% Ref)',
                'total_evolution': total_evo,
                'per_lap_evolution': per_lap,
                'lap_count': stat_result.get('lap_count', 0),
                'baseline_lap': stat_result.get('baseline_lap', 0)
            }
        elif stat_result:
            stat_result['method'] = 'Hybrid (Statistical only)'
            return stat_result
        elif ref_result:
            ref_result['method'] = 'Hybrid (Reference only)'
            return ref_result
        
        return {}
        
        # Placeholder result
        self.track_evo_label.setText(_lazy_tr("long_run.track.result_placeholder",
            "Track Evolution: ~0.15s improvement over race distance\n"
            "(Calculation logic not yet implemented)"))
    
    def _create_results_tab(self) -> QWidget:
        """Create degradation results tab with summary table"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions label
        instructions = QLabel(_lazy_tr("long_run.results.instructions",
            "Select stints in 'Stint Selection' tab, configure fuel settings, "
            "then click 'Calculate Degradation' to see results."))
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Calculate button
        calc_btn = QPushButton(_lazy_tr("long_run.results.calculate", "Calculate Degradation"))
        calc_btn.clicked.connect(self._calculate_degradation)
        layout.addWidget(calc_btn)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            _lazy_tr("long_run.results.driver", "Driver"),
            _lazy_tr("long_run.results.stint", "Stint"),
            _lazy_tr("long_run.results.compound", "Compound"),
            _lazy_tr("long_run.results.laps", "Laps"),
            _lazy_tr("long_run.results.raw_deg", "Raw Deg (s)"),
            _lazy_tr("long_run.results.fuel_adj", "Fuel Adj (s)"),
            _lazy_tr("long_run.results.track_evo", "Track Evo (s)"),
            _lazy_tr("long_run.results.true_deg", "True Deg (s/lap)")
        ])
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)
        
        # Summary box
        summary_group = QGroupBox(_lazy_tr("long_run.results.summary", "Summary"))
        summary_layout = QVBoxLayout(summary_group)
        
        self.results_summary_label = QLabel(_lazy_tr("long_run.results.no_calc",
            "No degradation calculated yet."))
        self.results_summary_label.setWordWrap(True)
        summary_layout.addWidget(self.results_summary_label)
        
        layout.addWidget(summary_group)
        
        # Export button
        export_btn = QPushButton(_lazy_tr("long_run.results.export", "Export Results to CSV"))
        export_btn.clicked.connect(self._export_results)
        layout.addWidget(export_btn)
        
        return tab
    
    def _calculate_degradation(self):
        """Calculate degradation for selected stints with fuel and track evolution adjustments"""
        if not hasattr(self, 'stint_tree') or self.stint_tree.topLevelItemCount() == 0:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(None,
                               _lazy_tr("long_run.results.no_stints_title", "No Stints"),
                               _lazy_tr("long_run.results.no_stints_msg", 
                                        "Please load data and select stints first."))
            return
        
        # Collect selected stints (properly extract stint info)
        selected_stints = self._get_selected_stints()
        
        if not selected_stints:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(None,
                               _lazy_tr("long_run.results.no_selected_title", "No Selection"),
                               _lazy_tr("long_run.results.no_selected_msg", 
                                        "Please check at least one stint to analyze."))
            return
        
        # Get fuel settings from Fuel Settings tab
        fuel_settings = self._get_fuel_settings()
        
        # Get track evolution data if calculated
        track_evo_per_lap = 0.0
        if hasattr(self, '_track_evolution') and self._track_evolution:
            track_evo_per_lap = self._track_evolution.get('per_lap_evolution', 0.0)
        
        # Clear and populate results table
        self.results_table.setRowCount(len(selected_stints))
        
        all_deg_results = []
        
        for row, stint in enumerate(selected_stints):
            driver = stint.get('driver', 'N/A')
            stint_num = stint.get('stint', 0)
            compound = stint.get('compound', 'N/A')
            
            # Use filtered laps (excluding outliers and pit laps)
            filtered_times = stint.get('filtered_times', stint.get('times', []))
            filtered_laps = stint.get('filtered_laps', stint.get('valid_laps', []))
            lap_count = len(filtered_times)
            
            # Calculate raw degradation using linear regression
            raw_deg, deg_per_lap = self._calculate_raw_degradation(filtered_times, filtered_laps)
            
            # Fuel adjustment: fuel burns off → car gets lighter → faster
            # So we need to ADD the fuel effect to get true degradation
            driver_fuel = fuel_settings.get(driver, {})
            fuel_consumption = driver_fuel.get('consumption', self.fuel_consumption_spin.value())
            fuel_effect = driver_fuel.get('effect', self.fuel_effect_spin.value())
            fuel_adj_per_lap = fuel_consumption * fuel_effect  # s/lap improvement from fuel burn
            
            # Total fuel adjustment for the stint
            fuel_adj = fuel_adj_per_lap * max(0, lap_count - 1)
            
            # Track evolution adjustment (negative = faster track, so add to get true deg)
            track_evo = track_evo_per_lap * max(0, lap_count - 1)
            
            # True degradation = Raw deg + Fuel adj + Track evo
            # Raw deg is positive if times increase
            # Fuel adj is what we lose due to lighter car (should add)
            # Track evo is negative if track improves (should add to compensate)
            true_deg_per_lap = deg_per_lap + fuel_adj_per_lap - track_evo_per_lap
            
            items = [
                driver,
                str(stint_num),
                compound,
                str(lap_count),
                f"{raw_deg:.3f}",
                f"{fuel_adj:.3f}",
                f"{track_evo:.3f}",
                f"{true_deg_per_lap:.3f}"
            ]
            
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col == 0:  # Driver column with color
                    color = self._get_driver_color(driver)
                    if color:
                        item.setBackground(QColor(color))
                        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                        brightness = (r * 299 + g * 587 + b * 114) / 1000
                        item.setForeground(QColor('#000000' if brightness > 128 else '#ffffff'))
                self.results_table.setItem(row, col, item)
            
            all_deg_results.append({
                'driver': driver,
                'stint': stint_num,
                'compound': compound,
                'lap_count': lap_count,
                'raw_deg': raw_deg,
                'deg_per_lap': deg_per_lap,
                'fuel_adj_per_lap': fuel_adj_per_lap,
                'track_evo_per_lap': track_evo_per_lap,
                'true_deg_per_lap': true_deg_per_lap
            })
        
        self.results_table.resizeColumnsToContents()
        
        # Update summary with compound averages
        summary_text = self._generate_degradation_summary(all_deg_results)
        self.results_summary_label.setText(summary_text)
        
        _get_logger().info(f"Degradation calculation complete: {len(selected_stints)} stints analyzed")
    
    def _calculate_raw_degradation(self, times: List[float], laps: List[int]) -> Tuple[float, float]:
        """Calculate raw degradation using linear regression
        
        Returns:
            Tuple of (total_degradation, degradation_per_lap)
        """
        if len(times) < 2:
            return 0.0, 0.0
        
        import numpy as np
        
        # Use lap indices (0, 1, 2, ...) for regression
        x = np.arange(len(times))
        y = np.array(times)
        
        # Linear regression: y = mx + b
        # m is the degradation per lap
        try:
            coeffs = np.polyfit(x, y, 1)
            deg_per_lap = coeffs[0]  # Slope = degradation per lap
            total_deg = deg_per_lap * (len(times) - 1)
            return total_deg, deg_per_lap
        except:
            return 0.0, 0.0
    
    def _get_fuel_settings(self) -> Dict[str, Dict]:
        """Get fuel settings for each driver from the Fuel Settings table"""
        settings = {}
        if not hasattr(self, 'fuel_table'):
            return settings
        
        for row in range(self.fuel_table.rowCount()):
            driver_item = self.fuel_table.item(row, 0)
            if not driver_item:
                continue
            driver = driver_item.text()
            
            # Get start fuel from spinbox
            start_fuel_widget = self.fuel_table.cellWidget(row, 1)
            start_fuel = start_fuel_widget.value() if start_fuel_widget else self.race_start_fuel_spin.value()
            
            # Get consumption from spinbox
            consumption_widget = self.fuel_table.cellWidget(row, 2)
            consumption = consumption_widget.value() if consumption_widget else self.fuel_consumption_spin.value()
            
            # Get effect from spinbox  
            effect_widget = self.fuel_table.cellWidget(row, 3)
            effect = effect_widget.value() if effect_widget else self.fuel_effect_spin.value()
            
            settings[driver] = {
                'start_fuel': start_fuel,
                'consumption': consumption,
                'effect': effect
            }
        
        return settings
    
    def _generate_degradation_summary(self, results: List[Dict]) -> str:
        """Generate summary text with compound averages"""
        if not results:
            return "No results to summarize."
        
        # Group by compound
        by_compound = {}
        for r in results:
            compound = r.get('compound', 'UNKNOWN')
            if compound not in by_compound:
                by_compound[compound] = []
            by_compound[compound].append(r)
        
        lines = [f"Analyzed {len(results)} stints from {len(set(r['driver'] for r in results))} drivers.\n"]
        
        for compound, stints in sorted(by_compound.items()):
            if not stints:
                continue
            avg_deg = sum(s['true_deg_per_lap'] for s in stints) / len(stints)
            min_deg = min(s['true_deg_per_lap'] for s in stints)
            max_deg = max(s['true_deg_per_lap'] for s in stints)
            
            lines.append(f"{compound}: Avg {avg_deg:.3f} s/lap (range: {min_deg:.3f} - {max_deg:.3f})")
        
        return "\n".join(lines)
    
    def _export_results(self):
        """Export degradation results to CSV"""
        if not hasattr(self, 'results_table') or self.results_table.rowCount() == 0:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(None,
                                   _lazy_tr("long_run.results.export_title", "Export"),
                                   _lazy_tr("long_run.results.no_results", 
                                            "No results to export. Calculate degradation first."))
            return
        
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            _lazy_tr("long_run.results.save_csv", "Save CSV"),
            "degradation_results.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header
                headers = [self.results_table.horizontalHeaderItem(i).text() 
                          for i in range(self.results_table.columnCount())]
                writer.writerow(headers)
                # Data
                for row in range(self.results_table.rowCount()):
                    row_data = [self.results_table.item(row, col).text() 
                               for col in range(self.results_table.columnCount())]
                    writer.writerow(row_data)
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(None,
                                   _lazy_tr("long_run.results.export_title", "Export"),
                                   _lazy_tr("long_run.results.export_success", 
                                            "Results exported to: {}").format(file_path))
    
    def _create_chart_tab(self) -> QWidget:
        """Create chart view tab with driver selector and chart options"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Top control panel with explicit height
        control_panel = QWidget()
        control_panel.setMinimumHeight(200)  # Ensure minimum height for driver list
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setAlignment(Qt.AlignTop)  # Align contents to top
        
        # Driver filter with exclude input per driver
        driver_group = QGroupBox(_lazy_tr("long_run.chart.drivers", "Drivers"))
        driver_group.setMinimumHeight(180)  # Minimum height for driver group
        driver_layout = QVBoxLayout(driver_group)
        
        # Select all / none buttons
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton(_lazy_tr("long_run.chart.select_all", "Select All"))
        select_none_btn = QPushButton(_lazy_tr("long_run.chart.select_none", "Select None"))
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(select_none_btn)
        driver_layout.addLayout(btn_layout)
        
        # Scrollable driver list with checkboxes and exclude inputs
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(150)  # Minimum height to show at least 5 drivers
        
        self.driver_list_container = QWidget()
        self.driver_list_layout = QVBoxLayout(self.driver_list_container)
        self.driver_list_layout.setContentsMargins(5, 5, 5, 5)
        self.driver_list_layout.setSpacing(2)
        
        # Initialize empty dicts - will be populated when data loads
        if not hasattr(self, 'driver_checkboxes'):
            self.driver_checkboxes = {}  # driver -> QCheckBox
        if not hasattr(self, 'driver_exclude_edits'):
            self.driver_exclude_edits = {}  # driver -> QLineEdit
        if not hasattr(self, 'driver_sim_lap_spins'):
            self.driver_sim_lap_spins = {}  # driver -> QSpinBox for simulate from lap
        
        scroll_area.setWidget(self.driver_list_container)
        driver_layout.addWidget(scroll_area)
        
        select_all_btn.clicked.connect(self._select_all_drivers_chart)
        select_none_btn.clicked.connect(self._select_no_drivers_chart)
        
        control_layout.addWidget(driver_group)
        
        # Chart options
        options_group = QGroupBox(_lazy_tr("long_run.chart.options", "Chart Options"))
        options_layout = QFormLayout(options_group)
        
        # Chart type
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            _lazy_tr("long_run.chart.type_full", "Fully-Corrected Lap Times"),
            _lazy_tr("long_run.chart.type_deg", "Degradation per Lap"),
            _lazy_tr("long_run.chart.type_raw", "Raw Lap Times"),
            _lazy_tr("long_run.chart.type_true", "True Degradation")
        ])
        options_layout.addRow(_lazy_tr("long_run.chart.type", "Chart Type:"), self.chart_type_combo)
        
        # Show trendline
        self.show_trendline_cb = QCheckBox()
        self.show_trendline_cb.setChecked(True)
        options_layout.addRow(_lazy_tr("long_run.chart.trendline", "Show Trendline:"), 
                             self.show_trendline_cb)
        
        # Group by stint
        self.group_by_stint_cb = QCheckBox()
        self.group_by_stint_cb.setChecked(True)
        options_layout.addRow(_lazy_tr("long_run.chart.group_stint", "Group by Stint:"), 
                             self.group_by_stint_cb)
        
        # Tire compound filter
        self.tire_filter_combo = QComboBox()
        self.tire_filter_combo.addItems([
            _lazy_tr("long_run.filter.all", "All Compounds"),
            _lazy_tr("long_run.filter.soft", "SOFT only"),
            _lazy_tr("long_run.filter.medium", "MEDIUM only"),
            _lazy_tr("long_run.filter.hard", "HARD only")
        ])
        options_layout.addRow(_lazy_tr("long_run.chart.tire_filter", "Tire Filter:"),
                             self.tire_filter_combo)
        
        control_layout.addWidget(options_group)
        
        # Draw chart button (moved to right of options)
        draw_btn = QPushButton(_lazy_tr("long_run.chart.draw", "Draw Chart"))
        draw_btn.setMinimumHeight(40)
        draw_btn.clicked.connect(self._draw_degradation_chart)
        control_layout.addWidget(draw_btn)
        
        control_layout.addStretch()
        
        layout.addWidget(control_panel)
        
        # Chart placeholder
        self.chart_container = QWidget()
        chart_layout = QVBoxLayout(self.chart_container)
        
        self.chart_placeholder = QLabel(_lazy_tr("long_run.chart.placeholder", 
                                                  "Degradation chart will be displayed after analysis"))
        self.chart_placeholder.setAlignment(Qt.AlignCenter)
        self.chart_placeholder.setStyleSheet("color: #888; font-size: 12px; min-height: 300px;")
        chart_layout.addWidget(self.chart_placeholder)
        
        layout.addWidget(self.chart_container, 1)  # Give it stretch factor
        
        return tab
    
    def _select_all_drivers_chart(self):
        """Select all drivers in chart driver list"""
        if hasattr(self, 'driver_checkboxes') and self.driver_checkboxes:
            for checkbox in self.driver_checkboxes.values():
                checkbox.setChecked(True)
    
    def _select_no_drivers_chart(self):
        """Deselect all drivers in chart driver list"""
        if hasattr(self, 'driver_checkboxes') and self.driver_checkboxes:
            for checkbox in self.driver_checkboxes.values():
                checkbox.setChecked(False)
    
    def _populate_chart_driver_list(self):
        """Populate driver list for chart view with checkboxes and exclude inputs"""
        if not hasattr(self, 'driver_list_layout') or not hasattr(self, '_raw_lap_data'):
            return
        
        # Clear existing widgets
        while self.driver_list_layout.count():
            child = self.driver_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.driver_checkboxes = {}
        self.driver_exclude_edits = {}
        self.driver_sim_lap_spins = {}
        
        drivers = list(self._raw_lap_data.keys())
        
        for driver in drivers:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(2, 1, 2, 1)
            row_layout.setSpacing(5)
            
            # Checkbox with driver name
            checkbox = QCheckBox(driver)
            checkbox.setChecked(True)
            checkbox.setMinimumWidth(50)
            
            # Set driver color as background with contrasting text
            color = self._get_driver_color(driver)
            if color:
                # Calculate brightness to determine text color
                try:
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    brightness = (r * 299 + g * 587 + b * 114) / 1000
                    text_color = '#000000' if brightness > 128 else '#ffffff'
                except:
                    text_color = '#000000'
                checkbox.setStyleSheet(f"QCheckBox {{ background-color: {color}; color: {text_color}; padding: 2px 5px; }}")
            
            row_layout.addWidget(checkbox)
            
            # Get driver's team for recommended Sim value
            driver_team = self._get_driver_team(driver)
            recommended_sim = self._get_recommended_sim_lap(driver_team) if driver_team else 0
            
            # Simulate from Lap spinbox (per driver)
            sim_lap_spin = QSpinBox()
            sim_lap_spin.setRange(0, 70)
            sim_lap_spin.setValue(recommended_sim)
            sim_lap_spin.setMaximumWidth(50)
            
            # Enhanced tooltip with recommendation info
            if recommended_sim > 0:
                tooltip_text = _lazy_tr(
                    "long_run.sim.tooltip_recommended",
                    f"Recommended Sim: {recommended_sim} (based on {driver_team} fuel habits)\n0 = FP2 mode, >0 = Race simulation mode"
                )
            else:
                tooltip_text = _lazy_tr(
                    "long_run.sim.tooltip_default",
                    f"Simulate race lap for {driver} (0 = FP2 mode)"
                )
            sim_lap_spin.setToolTip(tooltip_text)
            
            row_layout.addWidget(QLabel(_lazy_tr("long_run.sim.label", "Sim:")))
            row_layout.addWidget(sim_lap_spin)
            
            # Exclude laps input
            exclude_edit = QLineEdit()
            exclude_edit.setPlaceholderText(_lazy_tr("long_run.excl.placeholder", "Excl: 20,22"))
            exclude_edit.setMaximumWidth(100)
            exclude_edit.setToolTip(_lazy_tr(
                "long_run.excl.tooltip",
                f"Exclude laps for {driver}: e.g. 20,22 or 18-20"
            ))
            row_layout.addWidget(exclude_edit)
            
            row_layout.addStretch()
            
            self.driver_list_layout.addWidget(row_widget)
            self.driver_checkboxes[driver] = checkbox
            self.driver_exclude_edits[driver] = exclude_edit
            self.driver_sim_lap_spins[driver] = sim_lap_spin
        
        # Add stretch at end
        self.driver_list_layout.addStretch()
    
    def _draw_degradation_chart(self):
        """Draw the degradation chart using matplotlib with white background"""
        if not hasattr(self, '_raw_lap_data') or not self._raw_lap_data:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(None,
                               _lazy_tr("long_run.chart.no_data_title", "No Data"),
                               _lazy_tr("long_run.chart.no_data_msg", "Please load session data first."))
            return
        
        # Get selected drivers from checkboxes
        selected_drivers = []
        for driver, checkbox in self.driver_checkboxes.items():
            if checkbox.isChecked():
                selected_drivers.append(driver)
        
        if not selected_drivers:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(None,
                               _lazy_tr("long_run.chart.no_drivers_title", "No Drivers"),
                               _lazy_tr("long_run.chart.no_drivers_msg", 
                                        "Please select at least one driver."))
            return
        
        chart_type = self.chart_type_combo.currentIndex()
        show_trendline = self.show_trendline_cb.isChecked()
        group_by_stint = self.group_by_stint_cb.isChecked()
        
        # Parse exclude laps input
        exclude_laps = self._parse_exclude_laps()
        
        # Get fuel settings for fuel-corrected mode
        fuel_settings = self._get_fuel_settings()
        
        # Reset scatter data for hover tooltips
        self._scatter_data = []
        
        # Clear pinned annotations from previous chart
        if hasattr(self, '_pinned_annotations'):
            self._pinned_annotations = []
        
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            import numpy as np
            
            # Create figure
            fig = Figure(figsize=(12, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Set light theme (white background)
            fig.patch.set_facecolor('#ffffff')
            ax.set_facecolor('#ffffff')
            ax.tick_params(colors='black')
            ax.xaxis.label.set_color('black')
            ax.yaxis.label.set_color('black')
            ax.title.set_color('black')
            for spine in ax.spines.values():
                spine.set_color('#cccccc')
            ax.grid(True, linestyle='--', alpha=0.3, color='#888888')
            
            chart_titles = ["Fully-Corrected Lap Times", "Degradation per Lap", "Raw Lap Times", "True Degradation"]
            ax.set_title(f"{chart_titles[chart_type]} - {self.year} {self.race} {self.session}")
            ax.set_xlabel("Lap Number")
            
            # Y-axis label depends on chart type
            if chart_type in [1, 3]:  # Degradation per Lap or True Degradation
                ax.set_ylabel("Degradation (s/lap)")
            else:
                ax.set_ylabel("Lap Time (s)")
            
            # Get selected stints
            selected_stints = self._get_selected_stints()
            
            # Get tire filter selection
            tire_filter = self.tire_filter_combo.currentText()
            filter_compound = None
            if "SOFT" in tire_filter:
                filter_compound = "SOFT"
            elif "MEDIUM" in tire_filter:
                filter_compound = "MEDIUM"
            elif "HARD" in tire_filter:
                filter_compound = "HARD"
            
            # Plot data for each driver
            for driver in selected_drivers:
                driver_color = self._get_driver_color(driver) or '#ffffff'
                
                # Get driver's selected stints
                driver_stints = [s for s in selected_stints if s.get('driver') == driver]
                
                if not driver_stints:
                    continue
                
                for stint in driver_stints:
                    stint_num = stint.get('stint', 0)
                    compound = stint.get('compound', 'UNKNOWN')
                    
                    # Apply tire compound filter
                    if filter_compound and compound != filter_compound:
                        continue
                    
                    filtered_laps = stint.get('filtered_laps', [])
                    filtered_times = stint.get('filtered_times', [])
                    
                    if not filtered_times:
                        continue
                    
                    # Apply manual exclusion
                    driver_excludes = exclude_laps.get(driver, set()) | exclude_laps.get('*', set())
                    if driver_excludes:
                        clean_laps = []
                        clean_times = []
                        for lap, time in zip(filtered_laps, filtered_times):
                            if lap not in driver_excludes:
                                clean_laps.append(lap)
                                clean_times.append(time)
                        filtered_laps = clean_laps
                        filtered_times = clean_times
                    
                    if not filtered_times:
                        continue
                    
                    x_data = np.array(filtered_laps)
                    y_data = np.array(filtered_times)
                    
                    # Fully corrected lap times for chart_type 0 (fuel + track evolution)
                    if chart_type == 0:
                        driver_fuel = fuel_settings.get(driver, {})
                        start_fuel = driver_fuel.get('start_fuel', self.race_start_fuel_spin.value())
                        fuel_consumption = driver_fuel.get('consumption', self.fuel_consumption_spin.value())
                        fuel_effect = driver_fuel.get('effect', self.fuel_effect_spin.value())
                        
                        # Get per-driver race simulation setting from Chart View
                        simulate_from_lap = 0
                        if hasattr(self, 'driver_sim_lap_spins') and driver in self.driver_sim_lap_spins:
                            simulate_from_lap = self.driver_sim_lap_spins[driver].value()
                        
                        # Get track evolution per lap
                        track_evo_per_lap = 0.0
                        if hasattr(self, '_track_evolution') and self._track_evolution:
                            track_evo_per_lap = self._track_evolution.get('per_lap_evolution', 0.0)
                        
                        # Race Simulation Mode:
                        # Calculate what fuel level would be at the simulated race lap
                        # Then normalize all lap times to that fuel level
                        
                        if simulate_from_lap > 0:
                            # Simulating race conditions at lap X
                            # Target fuel = Race start fuel - (simulate_lap * consumption)
                            target_fuel = start_fuel - (simulate_from_lap * fuel_consumption)
                            target_fuel = max(target_fuel, 5.0)  # Minimum 5kg
                            
                            # For each lap in the stint, calculate fuel correction
                            # to normalize to target_fuel level
                            corrections = []
                            for i, lap in enumerate(filtered_laps):
                                # Current fuel at this lap (FP2 estimation based on stint position)
                                # Assume stint starts with start_fuel
                                current_fuel = start_fuel - (i * fuel_consumption)
                                
                                # Fuel difference from target
                                fuel_diff = current_fuel - target_fuel
                                
                                # If current_fuel > target_fuel, car is heavier, so it's slower
                                # We need to subtract time to normalize (make it faster to match lighter car)
                                # But we want to show "race conditions", so we ADD time if car is lighter
                                correction = -fuel_diff * fuel_effect
                                corrections.append(correction)
                            
                            fuel_correction = np.array(corrections)
                        else:
                            # Original mode: normalize within stint (first lap = reference)
                            lap_indices = np.arange(len(filtered_times))
                            fuel_correction = lap_indices * fuel_consumption * fuel_effect
                        
                        # Track evolution correction
                        lap_indices = np.arange(len(filtered_times))
                        track_correction = lap_indices * track_evo_per_lap
                        
                        # Fully corrected = raw + fuel_correction - track_evolution
                        y_data = y_data + fuel_correction - track_correction
                    
                    # Degradation per lap for chart_type 1
                    elif chart_type == 1:
                        if len(y_data) >= 2:
                            # Calculate lap-to-lap difference
                            y_data = np.diff(y_data)
                            x_data = x_data[1:]  # Remove first lap
                        else:
                            continue
                    
                    # True Degradation for chart_type 3
                    elif chart_type == 3:
                        if len(y_data) >= 2:
                            # Get fuel and track evolution settings
                            driver_fuel = fuel_settings.get(driver, {})
                            fuel_consumption = driver_fuel.get('consumption', self.fuel_consumption_spin.value())
                            fuel_effect = driver_fuel.get('effect', self.fuel_effect_spin.value())
                            
                            track_evo_per_lap = 0.0
                            if hasattr(self, '_track_evolution') and self._track_evolution:
                                track_evo_per_lap = self._track_evolution.get('per_lap_evolution', 0.0)
                            
                            # Calculate raw degradation (linear regression)
                            lap_indices = np.arange(len(y_data))
                            coeffs = np.polyfit(lap_indices, y_data, 1)
                            raw_deg_per_lap = coeffs[0]  # Slope
                            
                            # Calculate true degradation per lap
                            fuel_adj_per_lap = fuel_consumption * fuel_effect
                            true_deg_per_lap = raw_deg_per_lap + fuel_adj_per_lap - track_evo_per_lap
                            
                            # Create constant line showing true degradation
                            y_data = np.full(len(x_data), true_deg_per_lap)
                        else:
                            continue
                    
                    # Plot data points (2px marker and line size)
                    label = f"{driver} S{stint_num} ({compound})" if group_by_stint else driver
                    scatter = ax.scatter(x_data, y_data, color=driver_color, s=16, alpha=0.7, label=label, picker=True)
                    ax.plot(x_data, y_data, color=driver_color, alpha=0.4, linewidth=1)
                    
                    # Store scatter data for hover tooltip
                    if not hasattr(self, '_scatter_data'):
                        self._scatter_data = []
                    self._scatter_data.append({
                        'scatter': scatter,
                        'driver': driver,
                        'stint': stint_num,
                        'compound': compound,
                        'x_data': x_data,
                        'y_data': y_data,
                        'raw_times': np.array(filtered_times) if chart_type != 0 else y_data,
                        'color': driver_color  # Store driver color for tooltip
                    })
                    
                    # Add trendline (2px dashed line)
                    if show_trendline and len(x_data) >= 2:
                        z = np.polyfit(x_data, y_data, 1)
                        p = np.poly1d(z)
                        ax.plot(x_data, p(x_data), color=driver_color, linestyle='--', 
                               linewidth=1, alpha=0.8)
            
            # Add legend
            ax.legend(loc='upper left', fontsize=8, facecolor='#ffffff', 
                     labelcolor='black', framealpha=0.9, edgecolor='#cccccc')
            
            # Create hover annotation
            self._hover_annot = ax.annotate("", xy=(0, 0), xytext=(15, 15),
                                           textcoords="offset points",
                                           bbox=dict(boxstyle="round,pad=0.5", fc="#333333", ec="#666666", alpha=0.9),
                                           fontsize=9, color='white',
                                           arrowprops=dict(arrowstyle="->", color='#666666'))
            self._hover_annot.set_visible(False)
            
            # Adjust layout
            fig.tight_layout()
            
            # Create canvas and embed in chart container
            canvas = FigureCanvas(fig)
            
            # Connect mouse events for hover tooltip
            self._current_fig = fig
            self._current_ax = ax
            canvas.mpl_connect('motion_notify_event', self._on_chart_hover)
            canvas.mpl_connect('button_press_event', self._on_chart_click)
            
            # Clear old chart
            chart_layout = self.chart_container.layout()
            while chart_layout.count():
                child = chart_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Add new canvas
            chart_layout.addWidget(canvas)
            self._current_canvas = canvas
            
            _get_logger().info(f"Chart drawn: {len(selected_drivers)} drivers, type={chart_type}")
            
        except Exception as e:
            _get_logger().error(f"Error drawing chart: {e}")
            import traceback
            traceback.print_exc()
            self.chart_placeholder.setText(f"Error drawing chart:\n{str(e)}")
    
    def _on_chart_hover(self, event):
        """Handle mouse hover on chart to show tooltip"""
        if not hasattr(self, '_hover_annot') or not hasattr(self, '_scatter_data'):
            return
        
        if event.inaxes != self._current_ax:
            if self._hover_annot.get_visible():
                self._hover_annot.set_visible(False)
                self._current_canvas.draw_idle()
            return
        
        # Find nearest point
        found = False
        for data in self._scatter_data:
            scatter = data['scatter']
            cont, ind = scatter.contains(event)
            if cont:
                # Get the point index
                idx = ind['ind'][0]
                lap = int(data['x_data'][idx])
                y_val = data['y_data'][idx]
                driver = data['driver']
                stint = data['stint']
                compound = data['compound']
                driver_color = data.get('color', '#888888')
                
                # Calculate text color based on background brightness
                try:
                    r = int(driver_color[1:3], 16)
                    g = int(driver_color[3:5], 16)
                    b = int(driver_color[5:7], 16)
                    brightness = (r * 299 + g * 587 + b * 114) / 1000
                    text_color = 'black' if brightness > 128 else 'white'
                except:
                    text_color = 'white'
                
                # Format tooltip text
                chart_type = self.chart_type_combo.currentIndex()
                if chart_type in [1, 3]:  # Degradation types
                    tooltip = f"{driver} - Lap {lap}\nDeg: {y_val:.3f} s/lap\nTire: {compound}"
                else:
                    # Convert to mm:ss.sss format
                    mins = int(y_val // 60)
                    secs = y_val % 60
                    time_str = f"{mins}:{secs:06.3f}" if mins > 0 else f"{secs:.3f}s"
                    tooltip = f"{driver} - Lap {lap}\nTime: {time_str}\nTire: {compound}"
                
                # Calculate offset direction based on point position
                ax = self._current_ax
                x_lim = ax.get_xlim()
                y_lim = ax.get_ylim()
                x_range = x_lim[1] - x_lim[0]
                y_range = y_lim[1] - y_lim[0]
                
                # Position offset: move left if near right edge, move down if near top
                x_pos = data['x_data'][idx]
                x_offset = -80 if (x_pos - x_lim[0]) > 0.7 * x_range else 15
                y_offset = -50 if (y_val - y_lim[0]) > 0.7 * y_range else 15
                
                # Update annotation style with driver color
                self._hover_annot.xy = (x_pos, y_val)
                self._hover_annot.set_position((x_offset, y_offset))
                self._hover_annot.set_text(tooltip)
                self._hover_annot.get_bbox_patch().set_facecolor(driver_color)
                self._hover_annot.get_bbox_patch().set_edgecolor('#333333')
                self._hover_annot.set_color(text_color)
                self._hover_annot.set_visible(True)
                self._current_canvas.draw_idle()
                found = True
                break
        
        if not found and self._hover_annot.get_visible():
            self._hover_annot.set_visible(False)
            self._current_canvas.draw_idle()
    
    def _on_chart_click(self, event):
        """Handle mouse click on chart to show persistent tooltip"""
        if not hasattr(self, '_scatter_data') or event.inaxes != self._current_ax:
            return
        
        # Find clicked point
        for data in self._scatter_data:
            scatter = data['scatter']
            cont, ind = scatter.contains(event)
            if cont:
                idx = ind['ind'][0]
                lap = int(data['x_data'][idx])
                y_val = data['y_data'][idx]
                driver = data['driver']
                compound = data['compound']
                stint = data['stint']
                x_pos = data['x_data'][idx]
                driver_color = data.get('color', '#888888')
                
                # Calculate text color based on background brightness
                try:
                    r = int(driver_color[1:3], 16)
                    g = int(driver_color[3:5], 16)
                    b = int(driver_color[5:7], 16)
                    brightness = (r * 299 + g * 587 + b * 114) / 1000
                    text_color = 'black' if brightness > 128 else 'white'
                except:
                    text_color = 'white'
                
                # Format tooltip text
                chart_type = self.chart_type_combo.currentIndex()
                if chart_type in [1, 3]:
                    tooltip = f"{driver} - Lap {lap}\nDeg: {y_val:.3f} s/lap\nTire: {compound}"
                else:
                    mins = int(y_val // 60)
                    secs = y_val % 60
                    time_str = f"{mins}:{secs:06.3f}" if mins > 0 else f"{secs:.3f}s"
                    tooltip = f"{driver} - Lap {lap}\nTime: {time_str}\nTire: {compound}"
                
                # Calculate offset direction
                ax = self._current_ax
                x_lim = ax.get_xlim()
                y_lim = ax.get_ylim()
                x_range = x_lim[1] - x_lim[0]
                y_range = y_lim[1] - y_lim[0]
                x_offset = -80 if (x_pos - x_lim[0]) > 0.7 * x_range else 15
                y_offset = -50 if (y_val - y_lim[0]) > 0.7 * y_range else 15
                
                # Create persistent annotation with driver color
                pinned_annot = ax.annotate(tooltip, xy=(x_pos, y_val), 
                                          xytext=(x_offset, y_offset),
                                          textcoords="offset points",
                                          bbox=dict(boxstyle="round,pad=0.5", fc=driver_color, ec="#333333", alpha=0.95),
                                          fontsize=9, color=text_color,
                                          arrowprops=dict(arrowstyle="->", color=driver_color))
                
                # Store pinned annotations for later cleanup
                if not hasattr(self, '_pinned_annotations'):
                    self._pinned_annotations = []
                self._pinned_annotations.append(pinned_annot)
                
                self._current_canvas.draw_idle()
                
                # Also show in status bar
                if chart_type in [1, 3]:
                    msg = f"{driver} Stint {stint} - Lap {lap}: Degradation {y_val:.3f} s/lap ({compound})"
                else:
                    msg = f"{driver} Stint {stint} - Lap {lap}: {time_str} ({compound})"
                self._update_status(msg)
                break
    
    def _parse_exclude_laps(self) -> Dict[str, set]:
        """Parse exclude laps from per-driver input fields
        
        Returns:
            Dict mapping driver code to set of lap numbers to exclude
        """
        exclude = {}
        
        if not hasattr(self, 'driver_exclude_edits'):
            return exclude
        
        for driver, edit in self.driver_exclude_edits.items():
            text = edit.text().strip()
            if not text:
                continue
            
            # Parse lap numbers
            try:
                laps = set()
                for lap_str in text.split(','):
                    lap_str = lap_str.strip()
                    if lap_str:
                        if '-' in lap_str:
                            # Range: 20-25
                            start, end = lap_str.split('-')
                            laps.update(range(int(start), int(end) + 1))
                        else:
                            laps.add(int(lap_str))
                
                if laps:
                    exclude[driver] = laps
            except ValueError:
                _get_logger().warning(f"Invalid exclude laps format for {driver}: {text}")
        
        return exclude
    
    def _connect_signals(self):
        """Connect internal signals"""
        self.data_loaded.connect(self._on_data_loaded)
        self.load_error.connect(self._on_load_error)
        self.load_progress.connect(self._on_load_progress)
    
    def _load_data(self):
        """Load lap data via API"""
        if self._is_loading:
            return

        signature = (int(self.year), str(self.race), str(self.session))
        if (
            self._data is not None
            and self._last_loaded_signature == signature
            and (time.monotonic() - self._last_loaded_at) < 5.0
        ):
            _get_logger().debug("Skipping duplicate Long Run load for %s", signature)
            return
        
        self._is_loading = True
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self._update_status(_lazy_tr("long_run.loading", "Loading data..."))
        
        try:
            # Import data loader here to avoid circular imports
            from modules.gui.long_run_analysis.long_run_data_loader import LongRunDataLoader
            
            if self._data_loader is None:
                self._data_loader = LongRunDataLoader(self)
                self._data_loader.data_loaded.connect(self._on_data_received)
                self._data_loader.load_error.connect(self._on_data_error)
                self._data_loader.load_progress.connect(self._on_load_progress)
            
            self._data_loader.load_data(
                year=self.year,
                race=self.race,
                session=self.session
            )
        except Exception as e:
            _get_logger().error(f"Failed to start data loading: {e}")
            self._on_load_error(str(e))
    
    def _on_data_received(self, data: Any):
        """Handle received data"""
        self._is_loading = False
        self._data = data
        self._last_loaded_signature = (int(self.year), str(self.race), str(self.session))
        self._last_loaded_at = time.monotonic()
        self.progress_bar.setValue(100)
        self.progress_bar.hide()
        self._update_status(_lazy_tr("long_run.loaded", "Data loaded successfully"))
        self.data_loaded.emit(data)
    
    def _on_data_error(self, message: str):
        """Handle data loading error"""
        self._is_loading = False
        self.progress_bar.hide()
        self._update_status(f"Error: {message}")
        self.load_error.emit(message)
    
    def _on_load_progress(self, value: int):
        """Handle load progress update"""
        self.progress_bar.setValue(value)
    
    def _on_data_loaded(self, data: Any):
        """Handle data loaded signal - populate tabs with data"""
        _get_logger().info(f"Data loaded: {type(data)}")
        
        if not data:
            _get_logger().warning("No data received")
            return
        
        # 🆕 從 API 數據中提取車隊燃油習慣（優先於本地讀取）
        if isinstance(data, dict) and 'team_fuel_habits' in data:
            self._team_fuel_habits = data['team_fuel_habits']
            _get_logger().info(f"Loaded team fuel habits from API: {len(self._team_fuel_habits)} teams")
        elif not self._team_fuel_habits:
            # 備用：如果 API 沒有返回且本地也沒有，嘗試本地讀取
            self._load_team_fuel_habits_local()
        
        # Store raw lap data for later use
        self._raw_lap_data = self._extract_lap_data(data)
        
        # Populate stint tree
        self._populate_stint_tree(data)
        
        # Populate fuel settings table
        self._populate_fuel_table()
        
        # Populate chart driver list
        self._populate_chart_driver_list()
    
    def _extract_lap_data(self, data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Extract lap data from API response"""
        lap_data = None
        if isinstance(data, dict):
            if 'all_drivers_detailed_laptime' in data:
                lap_data = data['all_drivers_detailed_laptime']
            elif 'data' in data and isinstance(data['data'], dict):
                inner = data['data']
                if 'all_drivers_detailed_laptime' in inner:
                    lap_data = inner['all_drivers_detailed_laptime']
        return lap_data or {}
    
    def _populate_stint_tree(self, data: Dict[str, Any]):
        """Populate stint selection tree with driver lap data (grouped by driver)"""
        from PyQt5.QtWidgets import QTreeWidgetItem, QPushButton
        from PyQt5.QtGui import QColor, QBrush
        
        # Hide placeholder, show tree
        self.stint_placeholder.hide()
        self.stint_tree.show()
        
        # Get lap data
        lap_data = self._extract_lap_data(data)
        
        if not lap_data:
            _get_logger().warning(f"Could not find lap data in response")
            return
        
        # Clear existing items
        self.stint_tree.clear()
        
        # Store stint data for later use
        self._driver_stints = {}
        
        # Get ignore pit laps setting
        ignore_pit = self.ignore_pit_laps_cb.isChecked() if hasattr(self, 'ignore_pit_laps_cb') else True
        
        # Process each driver
        driver_count = 0
        stint_count = 0
        
        for driver_code, driver_info in lap_data.items():
            if not driver_info:
                continue
            
            # Get detailed_lap_data from driver info
            if isinstance(driver_info, dict):
                laps = driver_info.get('detailed_lap_data', [])
            elif isinstance(driver_info, list):
                laps = driver_info
            else:
                continue
            
            if not laps:
                continue
            
            # Detect stints for this driver
            stints = self._detect_driver_stints(driver_code, laps, ignore_pit)
            self._driver_stints[driver_code] = stints
            
            if not stints:
                continue
            
            # Get driver color
            driver_color = self._get_driver_color(driver_code)
            
            # Create driver parent item
            driver_item = QTreeWidgetItem()
            driver_item.setText(0, f"{driver_code}")
            driver_item.setData(0, Qt.UserRole, {'type': 'driver', 'code': driver_code})
            driver_item.setCheckState(0, Qt.Unchecked)
            
            # Set driver color as background
            color = QColor(driver_color)
            color.setAlpha(60)  # Semi-transparent
            driver_item.setBackground(0, QBrush(color))
            
            # Count long runs for this driver
            long_run_count = sum(1 for s in stints if s.get('is_long_run', False))
            driver_item.setText(4, f"{long_run_count} Long Runs")
            
            # Add stint children
            for stint_info in stints:
                stint_item = QTreeWidgetItem(driver_item)
                stint_item.setData(0, Qt.UserRole, {
                    'type': 'stint', 
                    'driver': driver_code,
                    'stint': stint_info
                })
                
                # Stint number
                stint_item.setText(0, f"Stint {stint_info['stint']}")
                
                # Checkbox for selection
                is_long_run = stint_info.get('is_long_run', False)
                stint_item.setCheckState(0, Qt.Checked if is_long_run else Qt.Unchecked)
                
                # Laps range - show valid range (excluding pit laps and outliers)
                valid_start = stint_info.get('valid_start_lap', stint_info['start_lap'])
                valid_end = stint_info.get('valid_end_lap', stint_info['end_lap'])
                valid_count = stint_info.get('valid_lap_count', 0)
                pit_count = stint_info.get('pit_lap_count', 0)
                outlier_count = stint_info.get('outlier_count', 0)
                raw_count = stint_info.get('raw_lap_count', valid_count)
                
                # Build lap range display string
                lap_parts = [f"{valid_count} valid"]
                if outlier_count > 0:
                    lap_parts.append(f"{outlier_count} outlier")
                if pit_count > 0:
                    lap_parts.append(f"{pit_count} pit")
                
                lap_range = f"{valid_start}-{valid_end} ({', '.join(lap_parts)})"
                stint_item.setText(1, lap_range)
                
                # Compound with color
                compound = stint_info.get('compound', 'UNKNOWN')
                stint_item.setText(2, compound)
                if compound == 'SOFT':
                    stint_item.setBackground(2, QBrush(QColor(255, 100, 100)))
                elif compound == 'MEDIUM':
                    stint_item.setBackground(2, QBrush(QColor(255, 255, 100)))
                elif compound == 'HARD':
                    stint_item.setBackground(2, QBrush(QColor(255, 255, 255)))
                
                # Avg time
                avg_time = stint_info.get('avg_time', 0)
                stint_item.setText(3, f"{avg_time:.3f}s" if avg_time else "-")
                
                # Status - show more info including std_dev
                std_dev = stint_info.get('std_dev', 0)
                if is_long_run:
                    # Get translated template and format with actual value
                    status_template = _lazy_tr("long_run.status.long_run", "Long Run (std={0:.2f}s)")
                    status = status_template.format(std_dev)
                elif valid_count < 4:
                    status_template = _lazy_tr("long_run.status.short", "Short ({0} laps)")
                    status = status_template.format(valid_count)
                else:
                    status_template = _lazy_tr("long_run.status.inconsistent", "Inconsistent (std={0:.2f}s)")
                    status = status_template.format(std_dev)
                stint_item.setText(4, status)
                
                # Edit button placeholder
                stint_item.setText(5, _lazy_tr("long_run.action.double_click", "Double-click to edit"))
                
                stint_count += 1
            
            self.stint_tree.addTopLevelItem(driver_item)
            driver_item.setExpanded(True)
            driver_count += 1
        
        _get_logger().info(f"Populated {driver_count} drivers with {stint_count} stints")
    
    def _detect_driver_stints(self, driver_code: str, laps: List[Dict], ignore_pit: bool = True) -> List[Dict]:
        """Detect stints for a driver based on lap data
        
        Args:
            driver_code: Driver code (e.g., 'VER')
            laps: List of lap data dictionaries
            ignore_pit: If True, exclude pit in/out laps from lap time calculation
        
        API response format per lap:
        {
            'lap_number': 1, 
            'lap_time': '1:32.456' or 'N/A',
            'lap_time_seconds': 92.456 or None,
            'tire_compound': 'MEDIUM',
            'tire_life': 1.0,
            'pit_status': '🔧進站' or None,
            'smart_markers': {'pit_stop_detection': {...}}
        }
        """
        if not laps:
            return []
        
        stints = []
        current_stint = None
        min_laps = self.min_laps_spin.value() if hasattr(self, 'min_laps_spin') else 4
        last_tire_life = 0
        stint_counter = 1
        
        for lap in laps:
            # Get lap data - handle API field names
            lap_num = lap.get('lap_number', lap.get('LapNumber', 0))
            
            # Check if this is a pit lap
            is_pit_lap = self._is_pit_lap(lap)
            
            # Get lap time - prefer seconds value
            lap_time = lap.get('lap_time_seconds')
            if lap_time is None:
                lap_time_str = lap.get('lap_time', lap.get('LapTime', ''))
                lap_time = self._parse_lap_time(lap_time_str)
            
            # Get compound
            compound = lap.get('tire_compound', lap.get('Compound', 'UNKNOWN'))
            if compound:
                compound = compound.upper()
            
            # Get tire life to detect stint changes
            tire_life = lap.get('tire_life', lap.get('TyreLife', 0))
            if tire_life is None:
                tire_life = 0
            
            # Detect stint change: tire life reset (new tires)
            is_new_stint = False
            if current_stint is None:
                is_new_stint = True
            elif tire_life < last_tire_life:
                # Tire life reset indicates new stint
                is_new_stint = True
            elif compound != current_stint.get('compound'):
                # Compound change indicates new stint
                is_new_stint = True
            
            last_tire_life = tire_life
            
            if is_new_stint:
                # Save previous stint
                if current_stint:
                    self._finalize_stint(current_stint, min_laps)
                    stints.append(current_stint)
                    stint_counter += 1
                
                # Start new stint
                current_stint = {
                    'stint': stint_counter,
                    'start_lap': lap_num,
                    'end_lap': lap_num,
                    'compound': compound,
                    'times': [],
                    'valid_laps': [],  # Laps with valid times (non-pit)
                    'pit_laps': [],     # Pit laps
                    'all_laps': [lap]   # Store all laps for editing
                }
            
            # Add lap to current stint
            current_stint['end_lap'] = lap_num
            current_stint['all_laps'].append(lap) if lap not in current_stint.get('all_laps', []) else None
            
            if is_pit_lap:
                current_stint['pit_laps'].append(lap_num)
                # Don't include pit lap time in calculations
            elif lap_time and lap_time > 0:
                current_stint['times'].append(lap_time)
                current_stint['valid_laps'].append(lap_num)
        
        # Save last stint
        if current_stint:
            self._finalize_stint(current_stint, min_laps)
            stints.append(current_stint)
        
        return stints
    
    def _finalize_stint(self, stint: Dict, min_laps: int):
        """Finalize stint calculations with IQR-based outlier rejection
        
        Uses IQR method to filter outliers before calculating std deviation.
        This prevents slow laps (traffic, waiting, out laps) from invalidating
        otherwise consistent long runs.
        """
        stint['lap_count'] = stint['end_lap'] - stint['start_lap'] + 1
        valid_times = stint.get('times', [])
        valid_laps = stint.get('valid_laps', [])
        
        # Filter outliers using IQR method
        filtered_times, filtered_laps, outlier_laps = self._filter_outliers_iqr(
            valid_times, valid_laps
        )
        
        stint['filtered_times'] = filtered_times
        stint['filtered_laps'] = filtered_laps
        stint['outlier_laps'] = outlier_laps
        
        stint['avg_time'] = sum(filtered_times) / len(filtered_times) if filtered_times else 0
        stint['valid_lap_count'] = len(filtered_times)  # Count after outlier removal
        stint['raw_lap_count'] = len(valid_times)  # Count before outlier removal
        stint['pit_lap_count'] = len(stint.get('pit_laps', []))
        stint['outlier_count'] = len(outlier_laps)
        
        # Long Run detection using filtered data:
        # 1. At least min_laps after outlier removal
        # 2. Lap time std deviation should be reasonable (< 2 seconds)
        is_long_run = stint['valid_lap_count'] >= min_laps
        stint['std_dev'] = 0.0
        
        if is_long_run and len(filtered_times) >= 2:
            import statistics
            try:
                std_dev = statistics.stdev(filtered_times)
                stint['std_dev'] = std_dev
                # If std dev > 2s after outlier removal, probably not consistent
                if std_dev > 2.0:
                    is_long_run = False
            except:
                pass
        
        stint['is_long_run'] = is_long_run
        
        # Calculate valid lap range (using filtered laps, excluding outliers)
        if filtered_laps:
            stint['valid_start_lap'] = min(filtered_laps)
            stint['valid_end_lap'] = max(filtered_laps)
        else:
            stint['valid_start_lap'] = stint['start_lap']
            stint['valid_end_lap'] = stint['end_lap']
    
    def _filter_outliers_iqr(self, times: List[float], laps: List[int]) -> Tuple[List[float], List[int], List[int]]:
        """Filter outliers using IQR method
        
        Args:
            times: List of lap times in seconds
            laps: Corresponding list of lap numbers
            
        Returns:
            Tuple of (filtered_times, filtered_laps, outlier_laps)
        """
        if len(times) < 4:
            # Not enough data for IQR, return as-is
            return times, laps, []
        
        import numpy as np
        times_array = np.array(times)
        
        q1 = np.percentile(times_array, 25)
        q3 = np.percentile(times_array, 75)
        iqr = q3 - q1
        
        # Use 1.5 * IQR rule for outlier detection
        # But also set a minimum bound of 3 seconds difference from median
        # to avoid rejecting valid degradation patterns
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Set minimum threshold to avoid rejecting gradual degradation
        median = np.median(times_array)
        lower_bound = max(lower_bound, median - 5.0)  # At least 5s slower than median
        upper_bound = max(upper_bound, median + 10.0)  # At least 10s faster than median (slow lap)
        
        filtered_times = []
        filtered_laps = []
        outlier_laps = []
        
        for t, l in zip(times, laps):
            if lower_bound <= t <= upper_bound:
                filtered_times.append(t)
                filtered_laps.append(l)
            else:
                outlier_laps.append(l)
        
        return filtered_times, filtered_laps, outlier_laps
    
    def _is_pit_lap(self, lap: Dict) -> bool:
        """Check if a lap is a pit in/out lap"""
        # Check pit_status field
        pit_status = lap.get('pit_status', '')
        if pit_status and ('進站' in str(pit_status) or 'pit' in str(pit_status).lower()):
            return True
        
        # Check smart_markers
        smart_markers = lap.get('smart_markers', {})
        pit_detection = smart_markers.get('pit_stop_detection', {})
        if pit_detection.get('is_pit_lap', False):
            return True
        
        # Check remarks
        remarks = lap.get('remarks', '')
        if '進站' in str(remarks) or 'pit' in str(remarks).lower():
            return True
        
        return False
    
    def _parse_lap_time(self, lap_time_str) -> float:
        """Parse lap time string to seconds"""
        if not lap_time_str or lap_time_str == 'N/A':
            return 0.0
        
        if isinstance(lap_time_str, (int, float)):
            return float(lap_time_str)
        
        try:
            # Handle "0 days 00:01:30.123" format
            if 'days' in str(lap_time_str):
                parts = str(lap_time_str).split(' ')
                time_part = parts[-1]
                h, m, s = time_part.split(':')
                return float(h) * 3600 + float(m) * 60 + float(s)
            
            # Handle "1:32.456" format
            parts = str(lap_time_str).split(':')
            if len(parts) == 3:
                h, m, s = parts
                return float(h) * 3600 + float(m) * 60 + float(s)
            elif len(parts) == 2:
                m, s = parts
                return float(m) * 60 + float(s)
            else:
                return float(lap_time_str)
        except:
            return 0.0
    
    def _detect_long_runs(self):
        """Re-detect long runs with current settings"""
        if self._data:
            self._populate_stint_tree(self._data)
    
    def _on_stint_edit(self, item, column):
        """Handle double-click on stint item to edit"""
        data = item.data(0, Qt.UserRole)
        if not data or data.get('type') != 'stint':
            return
        
        driver = data.get('driver')
        stint = data.get('stint')
        
        if not stint:
            return
        
        # Show edit dialog
        self._show_stint_edit_dialog(driver, stint)
    
    def _show_stint_edit_dialog(self, driver: str, stint: Dict):
        """Show dialog to edit stint lap range"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {driver} Stint {stint['stint']}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Info
        info = QLabel(f"Driver: {driver}\nCompound: {stint['compound']}\nOriginal: Lap {stint['start_lap']}-{stint['end_lap']}")
        layout.addWidget(info)
        
        # Start lap
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start Lap:"))
        start_spin = QSpinBox()
        start_spin.setRange(1, 100)
        start_spin.setValue(stint['start_lap'])
        start_layout.addWidget(start_spin)
        layout.addLayout(start_layout)
        
        # End lap
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("End Lap:"))
        end_spin = QSpinBox()
        end_spin.setRange(1, 100)
        end_spin.setValue(stint['end_lap'])
        end_layout.addWidget(end_spin)
        layout.addLayout(end_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            # Update stint
            stint['start_lap'] = start_spin.value()
            stint['end_lap'] = end_spin.value()
            stint['lap_count'] = stint['end_lap'] - stint['start_lap'] + 1
            stint['is_long_run'] = stint['lap_count'] >= self.min_laps_spin.value()
            
            # Refresh display
            self._detect_long_runs()
            _get_logger().info(f"Updated {driver} stint {stint['stint']} to lap {stint['start_lap']}-{stint['end_lap']}")
    
    def _on_load_error(self, message: str):
        """Handle load error signal"""
        _get_logger().error(f"Load error: {message}")
        QMessageBox.warning(
            self,
            _lazy_tr("long_run.error.title", "Load Error"),
            message
        )
    
    def _update_status(self, message: str):
        """Update status bar"""
        self.status_bar.showMessage(message)
    
    # =====================================================
    # Public API for MDI Integration
    # =====================================================
    
    def get_widget(self) -> QWidget:
        """Return module's main widget for MDI embedding
        
        Required by analysis_window_creator.py for PopoutSubWindow integration.
        Returns self since this widget IS the content.
        """
        return self
    
    def get_title(self) -> str:
        """Get window title for MDI (fallback)"""
        return f"Long Run_{self.year}_{self.race}_{self.session}"
    
    def get_window_title(self, year: int, race: str, session: str) -> str:
        """Generate window title with parameters
        
        Required by analysis_window_creator.py for dynamic title generation.
        """
        try:
            from core.gui_i18n import tr, get_gui_language
            language = get_gui_language()
            if language == 'zh':
                return tr('long_run_analysis', 'Long Run & Degradation Analysis')
            else:
                return "Long Run & Degradation Analysis"
        except ImportError:
            return "Long Run & Degradation Analysis"
    
    def get_default_size(self) -> tuple:
        """Get default window size
        
        Required by analysis_window_creator.py for window sizing.
        Returns (width, height) tuple.
        """
        return (1400, 900)
    
    def set_parent_window(self, parent_window):
        """Set parent window reference for popout integration
        
        Optional: Called by analysis_window_creator.py if available.
        """
        self._parent_window = parent_window
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session info"""
        return {
            "year": self.year,
            "race": self.race,
            "session": self.session
        }
    
    def get_degradation_results(self) -> Dict[str, Dict[str, float]]:
        """
        Get aggregated degradation results by compound.
        
        Returns:
            Dictionary with compound as key, containing:
            - deg_per_lap: Average degradation per lap (s/lap) - uses absolute value
            - count: Number of stints analyzed
            - min_deg: Minimum degradation
            - max_deg: Maximum degradation
            
        Example:
            {
                'SOFT': {'deg_per_lap': 0.120, 'count': 5, 'min_deg': 0.08, 'max_deg': 0.15},
                'MEDIUM': {'deg_per_lap': 0.080, 'count': 8, 'min_deg': 0.06, 'max_deg': 0.10},
                'HARD': {'deg_per_lap': 0.045, 'count': 3, 'min_deg': 0.03, 'max_deg': 0.06}
            }
        """
        results = {}
        
        if not hasattr(self, 'results_table') or self.results_table.rowCount() == 0:
            return results
        
        # Parse results table
        by_compound = {}
        for row in range(self.results_table.rowCount()):
            compound_item = self.results_table.item(row, 2)  # Compound column
            deg_item = self.results_table.item(row, 7)       # True Deg column
            
            if not compound_item or not deg_item:
                continue
            
            compound = compound_item.text().upper()
            try:
                deg_value = float(deg_item.text())
            except ValueError:
                continue
            
            if compound not in by_compound:
                by_compound[compound] = []
            by_compound[compound].append(deg_value)
        
        # Aggregate - use absolute value for degradation (positive = tire getting slower)
        for compound, values in by_compound.items():
            if values:
                avg_deg = sum(values) / len(values)
                results[compound] = {
                    'deg_per_lap': abs(avg_deg),  # Use absolute value for strategy sim
                    'raw_deg_per_lap': avg_deg,   # Keep original value
                    'count': len(values),
                    'min_deg': min(values),
                    'max_deg': max(values)
                }
        
        return results
    
    def get_fuel_settings(self) -> Dict[str, float]:
        """
        Get current fuel settings from the analysis.
        
        Returns:
            Dictionary with fuel parameters:
            - consumption: Fuel consumption (kg/lap)
            - effect: Fuel effect (s/kg)
        """
        return {
            'consumption': self.fuel_consumption_spin.value() if hasattr(self, 'fuel_consumption_spin') else 1.65,
            'effect': self.fuel_effect_spin.value() if hasattr(self, 'fuel_effect_spin') else 0.030
        }
    
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """Update analysis parameters and reload data
        
        Returns True if parameters updated successfully.
        """
        try:
            self.year = year
            self.race = race
            self.session = session
            # Trigger data reload
            QTimer.singleShot(100, self._load_data)
            return True
        except Exception as e:
            _get_logger().error(f"Failed to update parameters: {e}")
            return False
    
    def refresh_data(self):
        """Refresh data from API"""
        self._load_data()
