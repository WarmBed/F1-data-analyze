# -*- coding: utf-8 -*-
"""
Driver Strategy Widget - PyQt5 Native Drawing Version
=====================================================
Displays predicted vs actual lap times for drivers.

Features:
- Actual lap time curve (cyan, solid line with circle markers)
- Predicted lap time curve (red, dashed line)
- Prediction range fill (red, semi-transparent)
- SC/VSC zones (yellow fill)
- Pit stop markers (yellow vertical lines with "PIT" text)
- Current lap indicator (cyan dotted vertical line)
- Interactive context menu
- Multi-driver tracking (all 20 drivers tracked simultaneously)

Uses PyQt5 native QPainter for optimal real-time performance.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal, pyqtSlot, QEvent
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPainterPath, QLinearGradient, QPolygonF
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QMenu, QAction, QMdiSubWindow
)

from core.gui_i18n import tr

# =============================================================================
# Color Palette
# =============================================================================
COLOR_BACKGROUND = '#1a1a1a'
COLOR_CHART_BG = '#242424'
COLOR_GRID = '#3a3a3a'
COLOR_AXIS = '#888888'
COLOR_TEXT = '#ffffff'
COLOR_TEXT_DIM = '#888888'

COLOR_ACTUAL = '#4ECDC4'      # Cyan - actual lap times (default)
COLOR_PREDICTED = '#BB86FC'   # Light purple - predicted lap times
COLOR_PREDICTION_FILL = '#BB86FC'  # Light purple fill for prediction range
COLOR_SC_ZONE = '#FFD700'     # Yellow - SC/VSC zones
COLOR_PIT_MARKER = '#FFD700'  # Yellow - pit stop markers
COLOR_CURRENT_LAP = '#4ECDC4' # Cyan - current lap indicator

# Tyre compound colors
COLOR_TYRE_SOFT = '#FF3333'      # Red
COLOR_TYRE_MEDIUM = '#FFCC00'    # Yellow
COLOR_TYRE_HARD = '#FFFFFF'      # White
COLOR_TYRE_INTERMEDIATE = '#00CC00'  # Green
COLOR_TYRE_WET = '#0066FF'       # Blue


# =============================================================================
# DriverLapData - Lightweight Data Structure for Per-Driver Tracking
# =============================================================================
@dataclass
class DriverLapData:
    """
    Lightweight data structure to store per-driver lap data.
    Uses __slots__ equivalent via dataclass for memory efficiency.
    
    Tracks all 20 drivers simultaneously so switching is instant with full history.
    """
    driver_num: str = ""
    driver_tla: str = ""
    team_color: str = "FFFFFF"
    
    # Actual lap times: {lap_number: lap_time_seconds}
    actual_lap_times: Dict[int, float] = field(default_factory=dict)
    
    # Tyre compound per lap: {lap_number: compound_str}
    lap_compounds: Dict[int, str] = field(default_factory=dict)
    
    # Pit stop laps
    pit_laps: List[int] = field(default_factory=list)
    
    # PIT out laps (lap after pit - excluded from prediction)
    pit_out_laps: set = field(default_factory=set)
    
    # Last recorded lap number (to avoid duplicate processing)
    last_lap_recorded: int = 0
    
    # Current compound
    current_compound: str = ""
    
    def reset(self):
        """Reset all data for race restart."""
        self.actual_lap_times.clear()
        self.lap_compounds.clear()
        self.pit_laps.clear()
        self.pit_out_laps.clear()
        self.last_lap_recorded = 0
        self.current_compound = ""


# =============================================================================
# DriverStrategyWidget - Main PyQt5 Native Drawing Widget
# =============================================================================
class DriverStrategyWidget(QWidget):
    """
    Driver strategy visualization using PyQt5 native drawing.
    
    Displays actual vs predicted lap times with SC zones, pit markers,
    and prediction range.
    """
    
    # Signals
    error_occurred = pyqtSignal(str)
    data_updated = pyqtSignal()
    driver_change_requested = pyqtSignal(str)  # 請求切換車手
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Chart area margins
        self._margin_left = 60
        self._margin_right = 20
        self._margin_top = 30  # Space for info bar
        self._margin_bottom = 35
        
        # Available drivers for context menu
        self._available_drivers: Dict[str, Dict[str, Any]] = {}
        
        # Data storage
        self._total_laps: int = 0
        self._current_lap: int = 0
        self._driver_code: str = ""
        self._driver_name: str = ""
        self._team_name: str = ""
        self._team_color: str = "4ECDC4"  # Default cyan
        self._current_compound: str = ""
        self._circuit_key: str = ""
        
        # Actual lap data: {lap_number: lap_time_seconds}
        self._actual_lap_times: Dict[int, float] = {}
        
        # Predicted lap data: {lap_number: lap_time_seconds}
        self._predicted_lap_times: Dict[int, float] = {}
        
        # Prediction range: {lap_number: (min_time, max_time)}
        self._prediction_range: Dict[int, Tuple[float, float]] = {}
        
        # Pit stop laps: [lap1, lap2, ...]
        self._pit_laps: List[int] = []
        
        # SC/VSC zones: [(start_lap, end_lap), ...]
        self._sc_zones: List[Tuple[int, int]] = []
        
        # SC lap set for exclusion (laps under SC/VSC should not be displayed or predicted)
        self._sc_laps: set = set()
        
        # SC restart laps (lap after SC ends - also excluded)
        self._sc_restart_laps: set = set()
        
        # PIT out laps (lap after pit stop - excluded from prediction)
        self._pit_out_laps: set = set()
        
        # Tyre compound per lap: {lap_number: compound_str}
        self._lap_compounds: Dict[int, str] = {}
        
        # Stint tracking for pit prediction
        self._stint_start_lap: int = 1  # 當前 stint 開始圈數
        # List of (predicted_lap, actual_pit_lap) - actual_pit_lap=0 means not yet pitted
        self._predicted_pit_laps: List[Tuple[int, int]] = []
        self._current_predicted_pit: int = 0  # 當前 stint 的預估換胎圈數
        
        # Prediction error correction
        self._correction_factor: float = 0.0
        self._correction_enabled: bool = True
        
        # Database references
        self._strategy_database: Dict[str, Any] = {}
        self._tyre_deg_database: Dict[str, Any] = {}
        self._fuel_coeff_database: Dict[str, Any] = {}
        
        # Y-axis range (lap time in seconds)
        self._y_min: float = 0.0
        self._y_max: float = 120.0
        
        # Cached fonts
        self._font_title = QFont("Arial", 11, QFont.Bold)
        self._font_label = QFont("Arial", 9)
        self._font_axis = QFont("Arial", 8)
        self._font_legend = QFont("Arial", 9)
        
        # Initialize UI
        self._setup_ui()
        self._load_databases()
        
        # Update timer for smooth animations
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self.update)
        
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def _setup_ui(self):
        """Setup the main UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(2)
        
        # Info bar at top (using layout, not frame)
        self._setup_info_bar(main_layout)
        
        # Add stretch for chart area (widget draws itself via paintEvent)
        main_layout.addStretch()
        
        # Chart area (this widget draws itself)
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        
        # Right-click menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _show_context_menu(self, pos):
        """Show context menu at position."""
        global_pos = self.mapToGlobal(pos)
        
        class FakeEvent:
            def globalPos(self_inner):
                return global_pos
        
        self.contextMenuEvent(FakeEvent())
        
    def _setup_info_bar(self, layout: QVBoxLayout):
        """Setup the information bar at the top using layout."""
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        
        # Driver label
        self._driver_label = QLabel(tr("Driver") + ": --")
        self._driver_label.setStyleSheet(f"color: {COLOR_ACTUAL}; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(self._driver_label)
        
        # Tyre label
        self._tyre_label = QLabel(tr("Tyre") + ": --")
        self._tyre_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 11px;")
        info_layout.addWidget(self._tyre_label)
        
        info_layout.addStretch()
        
        # Lap counter
        self._lap_counter_label = QLabel(tr("Lap") + ": 0/0")
        self._lap_counter_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(self._lap_counter_label)
        
        layout.addLayout(info_layout)
        
    def _load_databases(self):
        """Load strategy, tyre degradation, and fuel coefficient databases."""
        config_dir = Path(__file__).parents[4] / "config"
        
        # Strategy database
        strategy_file = config_dir / "track_features_database.json"
        if strategy_file.exists():
            try:
                with open(strategy_file, 'r', encoding='utf-8') as f:
                    self._strategy_database = json.load(f)
            except Exception:
                pass
                
        # Tyre degradation database
        tyre_file = config_dir / "tire_degradation_database.json"
        if tyre_file.exists():
            try:
                with open(tyre_file, 'r', encoding='utf-8') as f:
                    self._tyre_deg_database = json.load(f)
            except Exception:
                pass
                
        # Fuel coefficient database
        fuel_file = config_dir / "fuel_coefficients_database.json"
        if fuel_file.exists():
            try:
                with open(fuel_file, 'r', encoding='utf-8') as f:
                    self._fuel_coeff_database = json.load(f)
            except Exception:
                pass
    
    # =========================================================================
    # Data Setters
    # =========================================================================
    
    def set_total_laps(self, laps: int):
        """Set total laps for the race."""
        self._total_laps = laps
        self._update_lap_counter()
        self.update()
        
    def set_driver_info(self, driver_code: str, driver_name: str = "", team_color: str = ""):
        """Set driver information with team color."""
        self._driver_code = driver_code
        self._driver_name = driver_name or driver_code
        self._team_color = team_color or "4ECDC4"  # Default cyan
        
        # Update label with team color
        self._driver_label.setText(f"{tr('Driver')}: {self._driver_code}")
        self._driver_label.setStyleSheet(f"color: #{self._team_color}; font-weight: bold; font-size: 11px;")
        self.update()
        
    def set_circuit(self, circuit_key: str):
        """Set circuit key for database lookups."""
        self._circuit_key = circuit_key
        
    def set_compound(self, compound: str):
        """Set current tyre compound with color coding."""
        self._current_compound = compound
        
        # 輪胎顏色: M=黃色, S=紅色, H=白色, I=綠色
        compound_colors = {
            'SOFT': '#FF3333',      # 紅色
            'S': '#FF3333',
            'MEDIUM': '#FFCC00',    # 黃色
            'M': '#FFCC00',
            'HARD': '#FFFFFF',      # 白色
            'H': '#FFFFFF',
            'INTERMEDIATE': '#00CC00',  # 綠色
            'I': '#00CC00',
            'WET': '#0066FF',       # 藍色
            'W': '#0066FF',
        }
        
        color = compound_colors.get(compound.upper(), '#CCCCCC')
        self._tyre_label.setText(f"{tr('Tyre')}: {compound}")
        self._tyre_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
        
    def select_driver(self, driver_code: str, driver_name: str = "", team_color: str = ""):
        """Select a driver and reset data for fresh display."""
        self._reset_driver_data()
        self.set_driver_info(driver_code, driver_name, team_color)
        
    def _reset_driver_data(self):
        """Reset all driver-specific data."""
        self._actual_lap_times.clear()
        self._predicted_lap_times.clear()
        self._prediction_range.clear()
        self._pit_laps.clear()
        self._sc_zones.clear()
        self._sc_laps.clear()
        self._sc_restart_laps.clear()
        self._pit_out_laps.clear()
        self._lap_compounds.clear()
        self._predicted_pit_laps.clear()  # Clear predicted pit history
        self._current_predicted_pit = 0
        self._stint_start_lap = 1
        self._current_lap = 0
        self._correction_factor = 0.0
        self._current_compound = ""
        self._update_lap_counter()
        self.update()
        
    def load_driver_history(self, actual_lap_times: Dict[int, float],
                            lap_compounds: Dict[int, str],
                            pit_laps: List[int],
                            pit_out_laps: set,
                            sc_laps: set = None,
                            sc_restart_laps: set = None,
                            current_compound: str = "",
                            current_lap: int = 0):
        """
        Load complete driver history from MDI's multi-driver tracking.
        
        This enables instant switching between drivers with full history preserved.
        Called when user switches to a different driver.
        
        Args:
            actual_lap_times: {lap_number: lap_time_seconds}
            lap_compounds: {lap_number: compound_str}
            pit_laps: List of pit stop lap numbers
            pit_out_laps: Set of pit out lap numbers
            sc_laps: Set of SC/VSC lap numbers (global)
            sc_restart_laps: Set of SC restart lap numbers (global)
            current_compound: Current tyre compound
            current_lap: Current/last lap number
        """
        # Reset first to clear old data
        self._reset_driver_data()
        
        # Load all historical data
        self._actual_lap_times = actual_lap_times
        self._lap_compounds = lap_compounds
        self._pit_laps = list(pit_laps)
        self._pit_out_laps = pit_out_laps
        self._current_compound = current_compound
        self._current_lap = current_lap
        
        # Calculate stint start lap from last pit stop
        if pit_laps:
            self._stint_start_lap = max(pit_laps) + 1
        else:
            self._stint_start_lap = 1
        
        # Load global SC data and generate zones for drawing
        if sc_laps is not None:
            self._sc_laps = sc_laps
            # Generate _sc_zones from _sc_laps for drawing
            self._generate_sc_zones_from_laps()
        if sc_restart_laps is not None:
            self._sc_restart_laps = sc_restart_laps
        
        # Update compound display
        if current_compound:
            self.set_compound(current_compound)
        
        # Recalculate predictions based on loaded history
        if self._actual_lap_times:
            self._calculate_all_predictions()
            # Backfill historical stint predictions for each stint
            self._backfill_historical_pit_predictions(pit_laps, lap_compounds)
            # Calculate current stint prediction
            self._update_predicted_pit_lap()
            self._calculate_y_range()
        
        # Update UI
        self._update_lap_counter()
        self.update()
        self.data_updated.emit()
        
        print(f"[DRIVER_STRATEGY] load_driver_history: loaded {len(actual_lap_times)} laps, sc={len(sc_laps or set())} laps, current={current_lap}")
        
    # =========================================================================
    # Lap Data Update
    # =========================================================================
    
    def update_lap_data(self, lap_number: int, lap_time: Optional[float],
                        compound: str = "", is_pit_lap: bool = False,
                        is_sc_lap: bool = False, is_vsc_lap: bool = False):
        """
        Update data for a specific lap.
        
        Args:
            lap_number: The lap number
            lap_time: Actual lap time in seconds (None if not available)
            compound: Tyre compound
            is_pit_lap: Whether this lap includes a pit stop
            is_sc_lap: Whether SC was deployed
            is_vsc_lap: Whether VSC was deployed
        """
        print(f"[DRIVER_STRATEGY] update_lap_data: lap={lap_number}, time={lap_time}, compound={compound}, SC={is_sc_lap}, VSC={is_vsc_lap}")
        
        self._current_lap = lap_number
        
        # Update compound and store for this lap
        if compound:
            self.set_compound(compound)
            self._lap_compounds[lap_number] = compound
        elif self._current_compound:
            # Use current compound if not specified
            self._lap_compounds[lap_number] = self._current_compound
        
        # Track SC/VSC zones and exclude SC laps
        if is_sc_lap or is_vsc_lap:
            self._update_sc_zone(lap_number)
            self._sc_laps.add(lap_number)
            print(f"[DRIVER_STRATEGY] SC/VSC lap {lap_number} excluded from display and prediction")
            # Don't store SC lap time, just update UI and return
            self._update_lap_counter()
            self.update()
            self.data_updated.emit()
            return
        
        # Check if this is a SC restart lap (previous lap was SC)
        if (lap_number - 1) in self._sc_laps:
            self._sc_restart_laps.add(lap_number)
            print(f"[DRIVER_STRATEGY] SC restart lap {lap_number} excluded from display and prediction")
            # Don't store SC restart lap time, but still update predictions and UI
            self._calculate_all_predictions()
            self._calculate_y_range()
            self._update_lap_counter()
            self.update()
            self.data_updated.emit()
            return
        
        # Check if this is a PIT out lap (previous lap was pit)
        if (lap_number - 1) in self._pit_laps:
            self._pit_out_laps.add(lap_number)
            print(f"[DRIVER_STRATEGY] PIT out lap {lap_number} - not used for prediction")
            # Store the time but mark for exclusion in prediction
            
        # Check if this is a PIT lap
        is_excluded_pit = is_pit_lap or lap_number in self._pit_out_laps
        
        # Store actual lap time (excluding SC, SC restart, PIT, PIT out laps)
        if lap_time is not None and lap_time > 0 and not is_excluded_pit:
            self._actual_lap_times[lap_number] = lap_time
            print(f"[DRIVER_STRATEGY] Stored lap time: lap {lap_number} = {lap_time:.3f}s, total points: {len(self._actual_lap_times)}")
        elif lap_time is not None and lap_time > 0 and is_excluded_pit:
            print(f"[DRIVER_STRATEGY] PIT/PIT-out lap {lap_number} time={lap_time:.3f}s excluded from prediction")
            
        # Track pit stops
        if is_pit_lap and lap_number not in self._pit_laps:
            self._pit_laps.append(lap_number)
            # Mark next lap as pit out lap for future reference
            self._pit_out_laps.add(lap_number + 1)
            # Reset stint start lap for new tyres
            self._stint_start_lap = lap_number + 1
            print(f"[DRIVER_STRATEGY] PIT at lap {lap_number}, new stint starts at lap {self._stint_start_lap}")
            
        # Calculate predictions
        self._calculate_all_predictions()
        
        # Update predicted pit lap based on optimal stint length
        self._update_predicted_pit_lap()
        
        # Apply self-correction if enabled
        if self._correction_enabled:
            self._apply_self_correction()
            
        # Update Y range
        self._calculate_y_range()
        
        # Update UI
        self._update_lap_counter()
        self.update()
        self.data_updated.emit()
        
    def _update_sc_zone(self, lap_number: int):
        """Update SC/VSC zones with the given lap."""
        if not self._sc_zones:
            self._sc_zones.append((lap_number, lap_number))
        else:
            # Extend the last zone if consecutive
            last_start, last_end = self._sc_zones[-1]
            if lap_number == last_end + 1:
                self._sc_zones[-1] = (last_start, lap_number)
            elif lap_number > last_end + 1:
                self._sc_zones.append((lap_number, lap_number))
                
    def _generate_sc_zones_from_laps(self):
        """
        Generate _sc_zones list from _sc_laps set.
        Converts individual SC laps into continuous zones for drawing.
        """
        self._sc_zones.clear()
        if not self._sc_laps:
            return
            
        sorted_laps = sorted(self._sc_laps)
        if not sorted_laps:
            return
            
        # Build zones from consecutive laps
        zone_start = sorted_laps[0]
        zone_end = sorted_laps[0]
        
        for lap in sorted_laps[1:]:
            if lap == zone_end + 1:
                # Extend current zone
                zone_end = lap
            else:
                # Save current zone and start new one
                self._sc_zones.append((zone_start, zone_end))
                zone_start = lap
                zone_end = lap
        
        # Don't forget the last zone
        self._sc_zones.append((zone_start, zone_end))
        print(f"[DRIVER_STRATEGY] Generated SC zones: {self._sc_zones}")
                
    def _update_lap_counter(self):
        """Update the lap counter label."""
        self._lap_counter_label.setText(f"{tr('Lap')}: {self._current_lap}/{self._total_laps}")
    
    # 賽事名稱到賽道名稱的映射 (race name -> circuit key in database)
    RACE_TO_CIRCUIT_MAP = {
        'Qatar': 'Lusail',
        'Abu Dhabi': 'Yas_Marina',
        'Saudi Arabia': 'Jeddah',
        'Australia': 'Melbourne',
        'Japan': 'Suzuka',
        'China': 'Shanghai',
        'Emilia Romagna': 'Imola',
        'Canada': 'Montreal',
        'Spain': 'Barcelona',
        'Austria': 'Spielberg',
        'Great Britain': 'Silverstone',
        'Britain': 'Silverstone',
        'Hungary': 'Budapest',
        'Belgium': 'Spa',
        'Netherlands': 'Zandvoort',
        'Italy': 'Monza',
        'Azerbaijan': 'Baku',
        'United States': 'Austin',
        'USA': 'Austin',
        'Mexico': 'Mexico',
        'Brazil': 'Interlagos',
        'Las Vegas': 'Las_Vegas',
    }
    
    def _backfill_historical_pit_predictions(self, pit_laps, lap_compounds: Dict[int, str]):
        """
        Backfill predicted pit laps for historical stints.
        
        When loading historical data, we need to calculate what the predicted
        pit lap would have been for each past stint based on optimal stint length.
        """
        print(f"[DRIVER_STRATEGY] _backfill called: circuit={self._circuit_key}, pit_laps={pit_laps}, lap_compounds keys={list(lap_compounds.keys())[:5]}")
        
        if not self._circuit_key:
            print(f"[DRIVER_STRATEGY] Backfill skipped: no circuit_key")
            return
            
        # Get circuit data for optimal stint calculation
        circuit_db_key = self.RACE_TO_CIRCUIT_MAP.get(self._circuit_key, self._circuit_key)
        circuits = self._tyre_deg_database.get('circuits', {})
        circuit_data = circuits.get(circuit_db_key, {})
        
        if not circuit_data:
            for key, data in circuits.items():
                if circuit_db_key.lower() in key.lower() or key.lower() in circuit_db_key.lower():
                    circuit_data = data
                    break
        
        if not circuit_data:
            print(f"[DRIVER_STRATEGY] Backfill skipped: no circuit_data for {circuit_db_key}")
            return
            
        optimal_stint = circuit_data.get('optimal_stint_length', {})
        
        # Sort pit laps - handle both Set and List
        sorted_pits = sorted(list(pit_laps)) if pit_laps else []
        print(f"[DRIVER_STRATEGY] Backfill sorted_pits={sorted_pits}")
        
        # Calculate stint boundaries: [(stint_start, stint_end, compound), ...]
        stint_boundaries = []
        
        # First stint starts at lap 1
        prev_stint_start = 1
        for pit_lap in sorted_pits:
            # Find compound for this stint - search from stint start to pit lap
            compound = ''
            for lap in range(prev_stint_start, pit_lap + 1):
                compound = lap_compounds.get(lap, '')
                if compound:
                    break
            print(f"[DRIVER_STRATEGY] Backfill stint: start={prev_stint_start}, pit={pit_lap}, compound={compound}")
            if compound:
                stint_boundaries.append((prev_stint_start, pit_lap, compound))
            prev_stint_start = pit_lap + 1
        
        # Calculate predicted pit for each historical stint
        for stint_start, actual_pit, compound in stint_boundaries:
            compound_key = compound.upper()
            if compound_key in ['S', 'SOFT']:
                compound_key = 'SOFT'
            elif compound_key in ['M', 'MEDIUM']:
                compound_key = 'MEDIUM'
            elif compound_key in ['H', 'HARD']:
                compound_key = 'HARD'
            elif compound_key in ['I', 'INTERMEDIATE']:
                compound_key = 'INTERMEDIATE'
            elif compound_key in ['W', 'WET']:
                compound_key = 'WET'
            
            stint_length = optimal_stint.get(compound_key, 0)
            if stint_length <= 0:
                defaults = {'SOFT': 18, 'MEDIUM': 28, 'HARD': 40, 'INTERMEDIATE': 25, 'WET': 20}
                stint_length = defaults.get(compound_key, 25)
            
            predicted_lap = stint_start + stint_length
            
            if predicted_lap < self._total_laps:
                # Check if this prediction already exists
                existing = [p for p, a in self._predicted_pit_laps if p == predicted_lap]
                if not existing:
                    self._predicted_pit_laps.append((predicted_lap, actual_pit))
                    print(f"[DRIVER_STRATEGY] Backfilled historical PIT prediction: lap {predicted_lap}, actual={actual_pit} (stint {stint_start}-{actual_pit}, {compound_key})")
    
    def _update_predicted_pit_lap(self):
        """
        Update predicted pit lap based on optimal stint length from database.
        
        Uses current compound and circuit to look up optimal stint length,
        then calculates when the driver should pit based on stint start lap.
        """
        if not self._circuit_key or not self._current_compound:
            self._current_predicted_pit = 0
            print(f"[DRIVER_STRATEGY] PIT prediction skipped: circuit={self._circuit_key}, compound={self._current_compound}")
            return
        
        # 將賽事名稱映射到資料庫中的賽道 key
        circuit_db_key = self.RACE_TO_CIRCUIT_MAP.get(self._circuit_key, self._circuit_key)
            
        # Get circuit data from database
        circuits = self._tyre_deg_database.get('circuits', {})
        circuit_data = circuits.get(circuit_db_key, {})
        
        if not circuit_data:
            # Try matching by partial name using the mapped key
            for key, data in circuits.items():
                if circuit_db_key.lower() in key.lower() or key.lower() in circuit_db_key.lower():
                    circuit_data = data
                    print(f"[DRIVER_STRATEGY] Circuit matched: {self._circuit_key} -> {key}")
                    break
        
        if not circuit_data:
            self._current_predicted_pit = 0
            print(f"[DRIVER_STRATEGY] PIT prediction skipped: no circuit data for '{self._circuit_key}' (mapped: {circuit_db_key})")
            return
            
        # Get optimal stint length for current compound
        optimal_stint = circuit_data.get('optimal_stint_length', {})
        compound_key = self._current_compound.upper()
        
        # Handle compound name variations
        if compound_key in ['S', 'SOFT']:
            compound_key = 'SOFT'
        elif compound_key in ['M', 'MEDIUM']:
            compound_key = 'MEDIUM'
        elif compound_key in ['H', 'HARD']:
            compound_key = 'HARD'
        elif compound_key in ['I', 'INTERMEDIATE']:
            compound_key = 'INTERMEDIATE'
        elif compound_key in ['W', 'WET']:
            compound_key = 'WET'
            
        stint_length = optimal_stint.get(compound_key, 0)
        
        if stint_length <= 0:
            # Use default values if not in database
            defaults = {'SOFT': 18, 'MEDIUM': 28, 'HARD': 40, 'INTERMEDIATE': 25, 'WET': 20}
            stint_length = defaults.get(compound_key, 25)
        
        # Calculate predicted pit lap
        predicted_lap = self._stint_start_lap + stint_length
        
        # Don't predict beyond total laps
        if predicted_lap >= self._total_laps:
            self._current_predicted_pit = 0  # No pit needed - can finish on current tyres
            print(f"[DRIVER_STRATEGY] No PIT needed - predicted {predicted_lap} >= total {self._total_laps} (stint start: {self._stint_start_lap}, optimal: {stint_length} laps for {compound_key})")
        else:
            self._current_predicted_pit = predicted_lap
            # Add to history if not already there (0 means not yet pitted)
            existing = [p for p, a in self._predicted_pit_laps if p == predicted_lap]
            if not existing:
                self._predicted_pit_laps.append((predicted_lap, 0))
                print(f"[DRIVER_STRATEGY] Predicted PIT at lap {predicted_lap} (stint start: {self._stint_start_lap}, optimal: {stint_length} laps for {compound_key})")
        
    # =========================================================================
    # Prediction Calculations
    # =========================================================================
    
    def _calculate_all_predictions(self):
        """
        Calculate predicted lap times for ALL laps (past and future).
        Only starts predicting after having at least 3 valid laps of data.
        Predictions persist and cover the entire race.
        
        IMPORTANT: Excludes SC, VSC, PIT, and PIT out laps from calculation.
        """
        if self._total_laps <= 0:
            return
        
        # 收集所有需要排除的圈數（SC、SC restart、PIT、PIT out）
        excluded_laps = self._sc_laps | self._sc_restart_laps | set(self._pit_laps) | self._pit_out_laps
        
        # 只使用有效圈數的資料進行計算（排除 SC/PIT 圈）
        valid_lap_times = {
            lap: time for lap, time in self._actual_lap_times.items()
            if lap not in excluded_laps
        }
        
        # 需要至少 3 圈有效資料才開始預測
        if len(valid_lap_times) < 3:
            return
        
        # 計算有效圈數的平均時間作為基準
        actual_times = list(valid_lap_times.values())
        base_time = sum(actual_times) / len(actual_times)
        
        # 計算趨勢 (每圈變化量) - 使用線性回歸（只用有效圈數）
        trend = 0.0
        intercept = base_time
        laps = sorted(valid_lap_times.keys())
        n = len(laps)
        
        if n >= 2:
            sum_x = sum(laps)
            sum_y = sum(valid_lap_times[lap] for lap in laps)
            sum_xy = sum(lap * valid_lap_times[lap] for lap in laps)
            sum_x2 = sum(lap * lap for lap in laps)
            
            denominator = n * sum_x2 - sum_x * sum_x
            if denominator != 0:
                trend = (n * sum_xy - sum_x * sum_y) / denominator
                intercept = (sum_y - trend * sum_x) / n
        
        # 預測所有圈數（Lap 1 到 total_laps），除了排除的圈數
        self._predicted_lap_times.clear()
        self._prediction_range.clear()
        
        for lap in range(1, self._total_laps + 1):
            # 跳過排除的圈數（SC、PIT 等）
            if lap in excluded_laps:
                continue
            
            # 預測 = intercept + trend * lap + 修正因子
            predicted = intercept + (trend * lap) + self._correction_factor
            
            # 確保預測值在合理範圍
            predicted = max(predicted, 60.0)
            predicted = min(predicted, 180.0)
            
            self._predicted_lap_times[lap] = predicted
            
            # Calculate prediction range (+-3%)
            margin = predicted * 0.03
            self._prediction_range[lap] = (predicted - margin, predicted + margin)
                
    def _calculate_predicted_lap_time(self, lap_number: int) -> float:
        """
        Calculate predicted lap time for a specific lap.
        Uses tyre degradation and fuel effect models.
        """
        # Get base lap time from actual data or estimate
        if self._actual_lap_times:
            base_time = min(self._actual_lap_times.values())
        else:
            # Default base time
            base_time = 90.0
            
        # Tyre degradation effect
        tyre_deg = self._get_tyre_degradation(lap_number)
        
        # Fuel effect (lighter car = faster)
        fuel_effect = self._get_fuel_effect(lap_number)
        
        # Combine effects
        predicted = base_time + tyre_deg + fuel_effect + self._correction_factor
        
        return max(predicted, 60.0)  # Minimum realistic lap time
        
    def _get_tyre_degradation(self, lap_number: int) -> float:
        """Get tyre degradation effect for the lap."""
        if not self._current_compound or not self._circuit_key:
            return 0.0
            
        # Look up in database
        circuit_data = self._tyre_deg_database.get(self._circuit_key, {})
        compound_deg = circuit_data.get(self._current_compound.upper(), 0.03)
        
        # Degradation increases with lap number
        return compound_deg * lap_number
        
    def _get_fuel_effect(self, lap_number: int) -> float:
        """Get fuel effect for the lap (negative = faster)."""
        if self._total_laps <= 0:
            return 0.0
            
        # Fuel effect coefficient (seconds per lap of fuel burn)
        fuel_coeff = self._fuel_coeff_database.get(self._circuit_key, 0.03)
        
        # More fuel burned = lighter car = faster
        laps_remaining = self._total_laps - lap_number
        return -fuel_coeff * (self._total_laps - laps_remaining - 1)
        
    def _apply_self_correction(self):
        """Apply self-correction based on prediction errors."""
        if len(self._actual_lap_times) < 3:
            return
            
        # Calculate average error between actual and predicted
        errors = []
        for lap, actual in self._actual_lap_times.items():
            if lap in self._predicted_lap_times:
                predicted = self._predicted_lap_times[lap]
                errors.append(actual - predicted)
                
        if errors:
            avg_error = sum(errors) / len(errors)
            # Smooth correction factor update
            self._correction_factor = self._correction_factor * 0.7 + avg_error * 0.3
            
    # =========================================================================
    # Y-Axis Range Calculation
    # =========================================================================
    
    def _calculate_y_range(self):
        """Calculate Y-axis range based on valid data only.
        
        Excludes SC, SC restart, and PIT out laps from Y-axis calculation.
        """
        all_times = []
        
        # Laps to exclude from Y-axis calculation
        excluded_laps = self._sc_laps | self._sc_restart_laps | self._pit_out_laps
        
        # Collect only valid actual times (exclude SC/PIT out laps)
        for lap, time in self._actual_lap_times.items():
            if lap not in excluded_laps:
                all_times.append(time)
        
        # Collect all predicted times (already excludes SC/PIT)
        all_times.extend(self._predicted_lap_times.values())
        
        # Collect prediction range bounds
        for min_t, max_t in self._prediction_range.values():
            all_times.extend([min_t, max_t])
            
        if all_times:
            self._y_min = min(all_times) - 2.0
            self._y_max = max(all_times) + 2.0
        else:
            self._y_min = 80.0
            self._y_max = 100.0
            
    # =========================================================================
    # Context Menu
    # =========================================================================
    
    def contextMenuEvent(self, event):
        """Show context menu."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLOR_CHART_BG};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_GRID};
            }}
            QMenu::item:selected {{
                background-color: {COLOR_GRID};
            }}
        """)
        
        # Toggle correction
        correction_action = QAction(
            tr("Disable Correction") if self._correction_enabled else tr("Enable Correction"),
            self
        )
        correction_action.triggered.connect(self._toggle_correction)
        menu.addAction(correction_action)
        
        # Reset correction
        reset_action = QAction(tr("Reset Correction"), self)
        reset_action.triggered.connect(self._reset_correction)
        menu.addAction(reset_action)
        
        menu.addSeparator()
        
        # Driver selection submenu
        if self._available_drivers:
            driver_menu = menu.addMenu(tr("Select Driver"))
            
            # 按位置排序
            sorted_drivers = sorted(
                self._available_drivers.items(),
                key=lambda x: x[1].get('position', 99) if isinstance(x[1], dict) else 99
            )
            
            for driver_num, info in sorted_drivers:
                if not isinstance(info, dict):
                    continue
                    
                tla = info.get('driver_tla', info.get('tla', driver_num))
                position = info.get('position', '')
                team_color = info.get('team_color', 'FFFFFF')
                
                # 顯示格式: P1 VER (位置 + 車手代碼)
                display_text = f"P{position} {tla}" if position else tla
                action = driver_menu.addAction(display_text)
                action.setData(driver_num)
                
                # 標記當前選中
                if tla == self._driver_code:
                    action.setCheckable(True)
                    action.setChecked(True)
                
                action.triggered.connect(lambda checked, d=driver_num: self.driver_change_requested.emit(d))
        
        menu.exec_(event.globalPos())
    
    def set_available_drivers(self, drivers: Dict[str, Dict[str, Any]]):
        """Set available drivers for context menu selection."""
        self._available_drivers = drivers
        
    def _toggle_correction(self):
        """Toggle prediction correction on/off."""
        self._correction_enabled = not self._correction_enabled
        if not self._correction_enabled:
            self._correction_factor = 0.0
        self.update()
        
    def _reset_correction(self):
        """Reset correction factor to zero."""
        self._correction_factor = 0.0
        self._calculate_all_predictions()
        self.update()
        
    # =========================================================================
    # PyQt5 Native Drawing
    # =========================================================================
    
    def paintEvent(self, event):
        """Main paint event for custom drawing."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(COLOR_BACKGROUND))
        
        # Calculate chart area
        # Use margin_top to account for info bar space (similar to Speed Trace)
        chart_rect = QRectF(
            self._margin_left,
            self._margin_top,
            self.width() - self._margin_left - self._margin_right,
            self.height() - self._margin_top - self._margin_bottom
        )
        
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return
            
        # Draw chart background
        painter.fillRect(chart_rect, QColor(COLOR_CHART_BG))
        
        # Draw grid
        self._draw_grid(painter, chart_rect)
        
        # Draw SC/VSC zones
        self._draw_sc_zones(painter, chart_rect)
        
        # Draw prediction range fill
        self._draw_prediction_range(painter, chart_rect)
        
        # Draw prediction line
        self._draw_prediction_line(painter, chart_rect)
        
        # Draw actual lap times
        self._draw_actual_lap_times(painter, chart_rect)
        
        # Draw pit markers
        self._draw_pit_markers(painter, chart_rect)
        
        # Draw predicted pit marker
        self._draw_predicted_pit_marker(painter, chart_rect)
        
        # Draw current lap indicator
        self._draw_current_lap_indicator(painter, chart_rect)
        
        # Draw axes
        self._draw_axes(painter, chart_rect)
        
        # Draw legend
        self._draw_legend(painter, chart_rect)
        
        painter.end()
        
    def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
        """Draw grid lines."""
        pen = QPen(QColor(COLOR_GRID))
        pen.setStyle(Qt.DotLine)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Horizontal grid lines (Y-axis)
        y_range = self._y_max - self._y_min
        if y_range <= 0:
            return
            
        # Calculate nice tick interval
        tick_interval = self._calculate_tick_interval(y_range)
        
        y_start = math.ceil(self._y_min / tick_interval) * tick_interval
        y = y_start
        while y <= self._y_max:
            py = self._value_to_y(y, chart_rect)
            painter.drawLine(
                QPointF(chart_rect.left(), py),
                QPointF(chart_rect.right(), py)
            )
            y += tick_interval
            
        # Vertical grid lines (X-axis / laps)
        if self._total_laps > 0:
            lap_interval = max(1, self._total_laps // 10)
            for lap in range(0, self._total_laps + 1, lap_interval):
                if lap == 0:
                    continue
                px = self._lap_to_x(lap, chart_rect)
                painter.drawLine(
                    QPointF(px, chart_rect.top()),
                    QPointF(px, chart_rect.bottom())
                )
                
    def _draw_sc_zones(self, painter: QPainter, chart_rect: QRectF):
        """Draw SC/VSC zones as yellow fills with SC label."""
        if not self._sc_zones or self._total_laps <= 0:
            return
            
        color = QColor(COLOR_SC_ZONE)
        color.setAlpha(50)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        for start_lap, end_lap in self._sc_zones:
            x1 = self._lap_to_x(start_lap - 0.5, chart_rect)
            x2 = self._lap_to_x(end_lap + 0.5, chart_rect)
            painter.drawRect(QRectF(x1, chart_rect.top(), x2 - x1, chart_rect.height()))
            
            # Draw "SC" label at top of zone (consistent with S1/S2/S3)
            painter.setFont(self._font_label)
            painter.setPen(QColor(COLOR_SC_ZONE))
            mid_x = (x1 + x2) / 2
            painter.drawText(QPointF(mid_x - 8, chart_rect.top() + 15), "SC")
            
    def _draw_prediction_range(self, painter: QPainter, chart_rect: QRectF):
        """Draw prediction range as semi-transparent fill."""
        if not self._prediction_range or self._total_laps <= 0:
            return
            
        color = QColor(COLOR_PREDICTION_FILL)
        color.setAlpha(30)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        # Build polygon for the range
        upper_points = []
        lower_points = []
        
        for lap in sorted(self._prediction_range.keys()):
            min_t, max_t = self._prediction_range[lap]
            x = self._lap_to_x(lap, chart_rect)
            upper_points.append(QPointF(x, self._value_to_y(max_t, chart_rect)))
            lower_points.append(QPointF(x, self._value_to_y(min_t, chart_rect)))
            
        if upper_points and lower_points:
            polygon = QPolygonF()
            for p in upper_points:
                polygon.append(p)
            for p in reversed(lower_points):
                polygon.append(p)
            painter.drawPolygon(polygon)
            
    def _draw_prediction_line(self, painter: QPainter, chart_rect: QRectF):
        """Draw predicted lap times as dashed red line."""
        if not self._predicted_lap_times or self._total_laps <= 0:
            return
            
        pen = QPen(QColor(COLOR_PREDICTED))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Create path
        path = QPainterPath()
        first = True
        
        for lap in sorted(self._predicted_lap_times.keys()):
            time = self._predicted_lap_times[lap]
            x = self._lap_to_x(lap, chart_rect)
            y = self._value_to_y(time, chart_rect)
            
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
                
        painter.drawPath(path)
        
    def _draw_actual_lap_times(self, painter: QPainter, chart_rect: QRectF):
        """Draw actual lap times with tyre compound colors and small markers.
        
        Excludes SC, SC restart, and PIT out laps from display.
        """
        if not self._actual_lap_times or self._total_laps <= 0:
            return
        
        # Laps to exclude from display
        excluded_laps = self._sc_laps | self._sc_restart_laps | self._pit_out_laps
        
        # Collect points with compound info (excluding SC/PIT out laps)
        points = []  # (x, y, lap, diff, compound)
        
        for lap in sorted(self._actual_lap_times.keys()):
            # Skip excluded laps
            if lap in excluded_laps:
                continue
                
            actual_time = self._actual_lap_times[lap]
            x = self._lap_to_x(lap, chart_rect)
            y = self._value_to_y(actual_time, chart_rect)
            
            # Calculate diff with predicted
            diff = None
            if lap in self._predicted_lap_times:
                predicted_time = self._predicted_lap_times[lap]
                diff = actual_time - predicted_time
            
            # Get compound for this lap
            compound = self._lap_compounds.get(lap, self._current_compound)
            
            points.append((x, y, lap, diff, compound))
        
        # Draw line segments with tyre compound colors
        if len(points) >= 2:
            for i in range(len(points) - 1):
                x1, y1, lap1, _, compound1 = points[i]
                x2, y2, lap2, _, compound2 = points[i + 1]
                
                # Use the compound of the ending lap for segment color
                color = self._get_compound_color(compound2)
                pen = QPen(QColor(color))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        # Draw small circle markers with compound colors
        for x, y, lap, diff, compound in points:
            color = self._get_compound_color(compound)
            painter.setPen(QPen(QColor(color)))
            painter.setBrush(QBrush(QColor(color)))
            painter.drawEllipse(QPointF(x, y), 2.5, 2.5)  # Smaller circles
        
        # Draw diff label only for the CURRENT lap (latest actual lap)
        if points:
            # Get the last point (current lap)
            x, y, lap, diff, compound = points[-1]
            if diff is not None:
                painter.setFont(QFont("Arial", 9, QFont.Bold))
                # Format diff text
                sign = "+" if diff >= 0 else ""
                diff_text = f"{sign}{diff:.2f}s"
                
                # Color: red if slower than predicted, green if faster
                color = QColor('#FF6B6B') if diff >= 0 else QColor('#4ECDC4')
                painter.setPen(color)
                
                # Position label above the point
                label_y = y - 14 if y > chart_rect.top() + 25 else y + 18
                painter.drawText(QPointF(x - 18, label_y), diff_text)
    
    def _get_compound_color(self, compound: str) -> str:
        """Get color for tyre compound."""
        compound_upper = compound.upper() if compound else ''
        if 'SOFT' in compound_upper or compound_upper == 'S':
            return COLOR_TYRE_SOFT
        elif 'MEDIUM' in compound_upper or compound_upper == 'M':
            return COLOR_TYRE_MEDIUM
        elif 'HARD' in compound_upper or compound_upper == 'H':
            return COLOR_TYRE_HARD
        elif 'INTER' in compound_upper or compound_upper == 'I':
            return COLOR_TYRE_INTERMEDIATE
        elif 'WET' in compound_upper or compound_upper == 'W':
            return COLOR_TYRE_WET
        else:
            return COLOR_ACTUAL  # Default cyan
            
    def _draw_pit_markers(self, painter: QPainter, chart_rect: QRectF):
        """Draw pit stop markers as vertical lines with PIT label."""
        if not self._pit_laps or self._total_laps <= 0:
            return
            
        pen = QPen(QColor(COLOR_PIT_MARKER))
        pen.setWidth(2)
        pen.setStyle(Qt.DashDotLine)
        painter.setPen(pen)
        
        painter.setFont(self._font_axis)
        
        for lap in self._pit_laps:
            x = self._lap_to_x(lap, chart_rect)
            painter.drawLine(
                QPointF(x, chart_rect.top()),
                QPointF(x, chart_rect.bottom())
            )
            
            # Check if this pit was predicted (within ±1 lap tolerance)
            prediction_matched = any(
                abs(lap - pred) <= 1 
                for pred, actual in self._predicted_pit_laps if pred > 0
            )
            
            # Draw checkmark if prediction matched
            if prediction_matched:
                painter.save()
                painter.setPen(QPen(QColor('#00FF00')))  # Green checkmark
                painter.setFont(self._font_axis)
                painter.translate(x - 5, chart_rect.top() + 28)
                painter.rotate(-90)
                painter.drawText(0, 0, "✓")
                painter.restore()
            
            # Draw PIT label
            painter.save()
            painter.setPen(pen)  # Reset pen color
            painter.translate(x - 5, chart_rect.top() + 15)
            painter.rotate(-90)
            painter.drawText(0, 0, "PIT")
            painter.restore()
            
    def _draw_predicted_pit_marker(self, painter: QPainter, chart_rect: QRectF):
        """Draw all predicted pit stop markers (historical and current).
        
        Logic:
        1. If prediction accurate (actual within ±1 lap): Show checkmark on PIT line (handled in _draw_pit_markers)
        2. If pitted early (actual < predicted): Hide PIT? line
        3. If pitted late (actual > predicted): Keep PIT? line visible
        4. If not yet pitted (actual = 0): Show PIT? line
        """
        if self._total_laps <= 0:
            return
        
        painter.setFont(self._font_axis)
        
        # Draw predictions based on logic
        for predicted_lap, actual_pit in self._predicted_pit_laps:
            if predicted_lap <= 0:
                continue
            
            # Determine if we should show this prediction
            if actual_pit > 0:  # This stint has ended with a pit
                if abs(actual_pit - predicted_lap) <= 1:
                    # Accurate prediction - checkmark shown on PIT line, skip drawing PIT? here
                    continue
                elif actual_pit < predicted_lap:
                    # Pitted early - hide PIT? line
                    continue
                # else: pitted late - show PIT? line (fall through)
            # else: not yet pitted - show PIT? line (fall through)
            
            is_past = predicted_lap <= self._current_lap
            
            # 統一線條樣式與 S1/S2/S3 Comparison 一致
            # PIT 預測線: width=1, DashLine
            if is_past:
                pen = QPen(QColor('#CC7000'))  # Darker orange for past
            else:
                pen = QPen(QColor('#FF8C00'))  # Bright orange for future
            
            pen.setWidth(1)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            
            x = self._lap_to_x(predicted_lap, chart_rect)
            painter.drawLine(
                QPointF(x, chart_rect.top()),
                QPointF(x, chart_rect.bottom())
            )
            
            # Draw PIT label with translation
            painter.save()
            painter.translate(x + 8, chart_rect.top() + 15)
            painter.rotate(-90)
            painter.drawText(0, 0, tr("PIT Est."))
            painter.restore()
            
    def _draw_current_lap_indicator(self, painter: QPainter, chart_rect: QRectF):
        """Draw current lap indicator as dotted cyan line."""
        if self._current_lap <= 0 or self._total_laps <= 0:
            return
            
        pen = QPen(QColor(COLOR_CURRENT_LAP))
        pen.setWidth(1)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        
        x = self._lap_to_x(self._current_lap, chart_rect)
        painter.drawLine(
            QPointF(x, chart_rect.top()),
            QPointF(x, chart_rect.bottom())
        )
        
    def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
        """Draw X and Y axes with labels."""
        pen = QPen(QColor(COLOR_AXIS))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setFont(self._font_axis)
        
        # Y-axis (left side)
        painter.drawLine(
            QPointF(chart_rect.left(), chart_rect.top()),
            QPointF(chart_rect.left(), chart_rect.bottom())
        )
        
        # Y-axis labels
        y_range = self._y_max - self._y_min
        if y_range > 0:
            tick_interval = self._calculate_tick_interval(y_range)
            y_start = math.ceil(self._y_min / tick_interval) * tick_interval
            y = y_start
            while y <= self._y_max:
                py = self._value_to_y(y, chart_rect)
                # Tick mark
                painter.drawLine(
                    QPointF(chart_rect.left() - 5, py),
                    QPointF(chart_rect.left(), py)
                )
                # Label
                label = f"{y:.1f}"
                fm = QFontMetrics(self._font_axis)
                text_width = fm.horizontalAdvance(label)
                painter.drawText(
                    int(chart_rect.left() - text_width - 8),
                    int(py + fm.height() / 4),
                    label
                )
                y += tick_interval
                
        # Y-axis title (rotated)
        painter.save()
        painter.setFont(self._font_label)
        painter.setPen(QPen(QColor(COLOR_TEXT)))
        title = tr("Lap Time (s)")
        fm = QFontMetrics(self._font_label)
        title_width = fm.horizontalAdvance(title)
        painter.translate(15, chart_rect.center().y() + title_width / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, title)
        painter.restore()
        
        # X-axis (bottom)
        painter.setPen(pen)
        painter.drawLine(
            QPointF(chart_rect.left(), chart_rect.bottom()),
            QPointF(chart_rect.right(), chart_rect.bottom())
        )
        
        # X-axis labels (laps)
        if self._total_laps > 0:
            lap_interval = max(1, self._total_laps // 10)
            for lap in range(0, self._total_laps + 1, lap_interval):
                if lap == 0:
                    continue
                px = self._lap_to_x(lap, chart_rect)
                # Tick mark
                painter.drawLine(
                    QPointF(px, chart_rect.bottom()),
                    QPointF(px, chart_rect.bottom() + 5)
                )
                # Label
                label = str(lap)
                fm = QFontMetrics(self._font_axis)
                text_width = fm.horizontalAdvance(label)
                painter.drawText(
                    int(px - text_width / 2),
                    int(chart_rect.bottom() + 18),
                    label
                )
                
        # X-axis title
        painter.setFont(self._font_label)
        painter.setPen(QPen(QColor(COLOR_TEXT)))
        title = tr("Lap")
        fm = QFontMetrics(self._font_label)
        title_width = fm.horizontalAdvance(title)
        painter.drawText(
            int(chart_rect.center().x() - title_width / 2),
            int(chart_rect.bottom() + 35),
            title
        )
        
    def _draw_legend(self, painter: QPainter, chart_rect: QRectF):
        """Draw legend at top right of chart."""
        painter.setFont(self._font_legend)
        
        # Legend items: Predicted, SC/VSC, and Predicted PIT
        legend_items = [
            (COLOR_PREDICTED, tr("Predicted")),
            (COLOR_SC_ZONE, tr("SC/VSC")),
            ('#FF8C00', tr("PIT Est.")),  # Dark orange for predicted pit
        ]
        
        x = chart_rect.right() - 100
        y = chart_rect.top() + 15
        
        for color, label in legend_items:
            # Color box
            painter.fillRect(int(x), int(y - 8), 12, 12, QColor(color))
            
            # Label
            painter.setPen(QPen(QColor(COLOR_TEXT)))
            painter.drawText(int(x + 16), int(y + 2), label)
            
            y += 18
            
    # =========================================================================
    # Coordinate Conversion Helpers
    # =========================================================================
    
    def _lap_to_x(self, lap: float, chart_rect: QRectF) -> float:
        """Convert lap number to X coordinate."""
        if self._total_laps <= 0:
            return chart_rect.left()
        return chart_rect.left() + (lap / self._total_laps) * chart_rect.width()
        
    def _value_to_y(self, value: float, chart_rect: QRectF) -> float:
        """Convert lap time value to Y coordinate (inverted)."""
        y_range = self._y_max - self._y_min
        if y_range <= 0:
            return chart_rect.center().y()
        ratio = (value - self._y_min) / y_range
        return chart_rect.bottom() - ratio * chart_rect.height()
        
    def _calculate_tick_interval(self, data_range: float) -> float:
        """Calculate nice tick interval for axis."""
        if data_range <= 0:
            return 1.0
        rough_tick = data_range / 5
        magnitude = math.pow(10, math.floor(math.log10(rough_tick)))
        residual = rough_tick / magnitude
        
        if residual > 5:
            return 10 * magnitude
        elif residual > 2:
            return 5 * magnitude
        elif residual > 1:
            return 2 * magnitude
        else:
            return magnitude


# =============================================================================
# LiveTimingDriverStrategy - MDI Integration
# =============================================================================
from ..core.base_live_mdi import BaseLiveTimingMDI


class LiveTimingDriverStrategy(BaseLiveTimingMDI):
    """
    MDI sub-window wrapper for Driver Strategy widget.
    Inherits from BaseLiveTimingMDI for proper signal handling.
    
    ARCHITECTURE: Tracks ALL 20 drivers simultaneously for instant switching.
    - _all_drivers_lap_data: Dict[str, DriverLapData] stores all driver data
    - Widget only displays the currently selected driver
    - Switching drivers loads from _all_drivers_lap_data (no reset)
    """
    
    MODULE_ID = "live_timing_driver_strategy"
    DEFAULT_TITLE = "Driver Strategy"
    
    def __init__(self, parent=None, data_manager=None):
        self._current_driver: str = ""
        self._drivers_data: Dict[str, Any] = {}
        self._current_race_time: str = ""  # 當前 snapshot 的 race_time
        
        # Multi-driver tracking: stores data for ALL drivers
        self._all_drivers_lap_data: Dict[str, DriverLapData] = {}
        
        # Global SC data (shared across all drivers)
        self._sc_laps: set = set()
        self._sc_zones: List[Tuple[int, int]] = []
        self._sc_restart_laps: set = set()
        
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(self.DEFAULT_TITLE)
        self.resize(600, 400)
        
        # 連接 DataManager 車手選擇信號
        if self._data_manager:
            self._data_manager.driver_selected.connect(self._on_driver_selected)
        
        print("[DRIVER_STRATEGY_MDI] LiveTimingDriverStrategy initialized (multi-driver tracking)")
        
    def _setup_ui(self):
        """Setup the UI layout."""
        # Create strategy widget and add to main_layout from BaseLiveTimingMDI
        self._strategy_widget = DriverStrategyWidget(self)
        self._main_layout.addWidget(self._strategy_widget)
        
        # 連接車手切換請求信號
        self._strategy_widget.driver_change_requested.connect(self._on_driver_change_requested)
    
    def _on_driver_change_requested(self, driver_num: str):
        """處理車手切換請求"""
        print(f"[DRIVER_STRATEGY_MDI] Driver change requested: {driver_num}")
        self.select_driver(driver_num)
        
    def _on_driver_selected(self, driver_num: str):
        """處理車手選擇信號"""
        print(f"[DRIVER_STRATEGY_MDI] Driver selected from external: {driver_num}")
        if hasattr(self, '_strategy_widget'):
            self.select_driver(driver_num)
        
    def _get_or_create_driver_data(self, driver_num: str, driver_info: Dict[str, Any]) -> DriverLapData:
        """
        Get existing driver data or create new one.
        Efficient memory usage - only creates data structure when needed.
        """
        if driver_num not in self._all_drivers_lap_data:
            self._all_drivers_lap_data[driver_num] = DriverLapData(
                driver_num=driver_num,
                driver_tla=driver_info.get("driver_tla", driver_num),
                team_color=driver_info.get("team_color", "FFFFFF")
            )
        return self._all_drivers_lap_data[driver_num]
        
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """
        處理快照更新 - 更新 ALL 車手資料，不只當前車手。
        """
        if not hasattr(self, '_strategy_widget'):
            return
            
        # 從快照提取資料
        drivers = snapshot.get('drivers', {})
        
        # 儲存當前 snapshot 的 race_time（用於查詢 track_status）
        self._current_race_time = snapshot.get('race_time', '')
        
        # 調試: 打印第一次收到的資料結構
        if drivers and not self._current_driver:
            sample_driver = next(iter(drivers.keys()))
            sample_data = drivers[sample_driver]
            print(f"[DRIVER_STRATEGY_MDI] Sample driver data keys: {list(sample_data.keys()) if isinstance(sample_data, dict) else 'N/A'}")
        
        # 儲存車手資料
        self._drivers_data = drivers
        
        # 傳遞車手列表給 widget（供右鍵選單使用）
        self._strategy_widget.set_available_drivers(drivers)
        
        # 設定總圈數
        total_laps = snapshot.get('total_laps', 0)
        if total_laps > 0:
            self._strategy_widget.set_total_laps(total_laps)
        
        # 自動選擇 P1 車手
        if not self._current_driver and drivers:
            self._auto_select_p1_driver(drivers)
        
        # ========== 關鍵變更: 更新 ALL 車手資料 ==========
        # 檢查 track status（全域，所有車手共用）
        is_sc_lap = False
        is_vsc_lap = False
        if self._data_manager and self._current_race_time:
            track_status = self._data_manager.get_track_status_at_time(self._current_race_time)
            is_sc_lap = (track_status == '4')
            is_vsc_lap = (track_status == '6')
        
        # 獲取輪胎狀態（一次性獲取，供所有車手使用）
        tyre_state = {}
        if self._data_manager:
            tyre_state = self._data_manager.get_tyre_state()
        
        # 更新所有車手的圈速資料
        for driver_num, driver_info in drivers.items():
            if not isinstance(driver_info, dict):
                continue
            # 獲取當前圈數以記錄 SC
            lap_num = driver_info.get("lap")
            if lap_num is not None:
                try:
                    lap_num = int(lap_num)
                    # 記錄 SC/VSC 圈到全域 (只需記錄一次)
                    if is_sc_lap or is_vsc_lap:
                        if lap_num not in self._sc_laps:
                            self._sc_laps.add(lap_num)
                            print(f"[DRIVER_STRATEGY_MDI] SC lap recorded: {lap_num}")
                    # 檢查是否為 SC restart 圈 (前一圈是 SC)
                    elif (lap_num - 1) in self._sc_laps:
                        if lap_num not in self._sc_restart_laps:
                            self._sc_restart_laps.add(lap_num)
                            print(f"[DRIVER_STRATEGY_MDI] SC restart lap recorded: {lap_num}")
                except (ValueError, TypeError):
                    pass
            self._update_single_driver_data(driver_num, driver_info, tyre_state, is_sc_lap, is_vsc_lap)
        
        # 只更新當前顯示車手的 Widget
        if self._current_driver and self._current_driver in self._all_drivers_lap_data:
            self._refresh_widget_from_driver_data(self._current_driver)
            
    def _update_single_driver_data(self, driver_num: str, driver_info: Dict[str, Any],
                                    tyre_state: Dict[str, Any], is_sc_lap: bool, is_vsc_lap: bool):
        """
        更新單一車手的資料到 _all_drivers_lap_data。
        這會處理所有 20 位車手，不只當前選中的。
        """
        # 獲取或創建車手資料
        driver_data = self._get_or_create_driver_data(driver_num, driver_info)
        
        # 獲取圈數
        lap_num = driver_info.get("lap")
        if lap_num is None:
            return
            
        try:
            lap_num = int(lap_num)
        except (ValueError, TypeError):
            return
        
        # 檢查是否已記錄過這一圈
        if lap_num <= driver_data.last_lap_recorded:
            return
        
        # 獲取單圈時間
        lap_time_str = driver_info.get("last_lap_time", "")
        if not lap_time_str:
            return
        
        # 解析時間為秒數
        lap_time = self._parse_time_to_seconds(lap_time_str)
        if lap_time is None or lap_time <= 0:
            return
        
        # 獲取輪胎資訊
        compound = ""
        if driver_num in tyre_state:
            stints = tyre_state[driver_num].get('stints', [])
            if stints:
                compound = stints[-1].get('compound', '')
        driver_data.current_compound = compound
        
        # 獲取進站狀態
        is_pit = driver_info.get("in_pit", False) or driver_info.get("pit_out", False)
        
        # 記錄資料（排除 SC/VSC 圈）
        if not is_sc_lap and not is_vsc_lap:
            driver_data.actual_lap_times[lap_num] = lap_time
            if compound:
                driver_data.lap_compounds[lap_num] = compound
        
        # 記錄進站
        if is_pit:
            if lap_num not in driver_data.pit_laps:
                driver_data.pit_laps.append(lap_num)
            driver_data.pit_out_laps.add(lap_num + 1)
        
        # 更新最後記錄圈數
        driver_data.last_lap_recorded = lap_num
        
    def _refresh_widget_from_driver_data(self, driver_num: str):
        """
        從 _all_drivers_lap_data 刷新 Widget 顯示。
        這使得切換車手時可以立即顯示完整歷史資料。
        """
        if driver_num not in self._all_drivers_lap_data:
            return
            
        driver_data = self._all_drivers_lap_data[driver_num]
        
        # 批量載入所有圈速資料到 Widget（包含全域 SC 資料）
        self._strategy_widget.load_driver_history(
            actual_lap_times=driver_data.actual_lap_times.copy(),
            lap_compounds=driver_data.lap_compounds.copy(),
            pit_laps=driver_data.pit_laps.copy(),
            pit_out_laps=driver_data.pit_out_laps.copy(),
            sc_laps=self._sc_laps.copy(),
            sc_restart_laps=self._sc_restart_laps.copy(),
            current_compound=driver_data.current_compound,
            current_lap=driver_data.last_lap_recorded
        )
            
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """賽事載入完成"""
        print(f"[DRIVER_STRATEGY_MDI] Race loaded: {race_info.get('name', 'Unknown')}")
        
        # 設定賽道
        circuit = race_info.get('circuit', '')
        if circuit and hasattr(self, '_strategy_widget'):
            self._strategy_widget.set_circuit(circuit)
            
        # 設定總圈數
        total_laps = race_info.get('total_laps', 0)
        if total_laps > 0 and hasattr(self, '_strategy_widget'):
            self._strategy_widget.set_total_laps(total_laps)
            
    def _on_race_unloaded(self):
        """賽事卸載 - 清除所有車手資料"""
        print("[DRIVER_STRATEGY_MDI] Race unloaded - clearing all driver data")
        self._current_driver = ""
        self._drivers_data.clear()
        
        # 清除所有車手歷史資料
        self._all_drivers_lap_data.clear()
        self._sc_laps.clear()
        self._sc_zones.clear()
        self._sc_restart_laps.clear()
        
        if hasattr(self, '_strategy_widget'):
            self._strategy_widget._reset_driver_data()
        
    def get_strategy_widget(self) -> DriverStrategyWidget:
        """Get the strategy widget for external access."""
        return self._strategy_widget
        
    # =========================================================================
    # Driver Selection and Update
    # =========================================================================
    
    def _auto_select_p1_driver(self, drivers: Dict[str, Any]):
        """Auto-select the P1 driver."""
        p1_driver = None
        
        for driver_num, data in drivers.items():
            if isinstance(data, dict):
                position = data.get("position", 99)
                if position == 1:
                    p1_driver = driver_num
                    break
                
        if p1_driver:
            self.select_driver(p1_driver)
        elif drivers:
            # Fallback to first driver
            self.select_driver(list(drivers.keys())[0])
            
    def select_driver(self, driver_num: str):
        """
        Select a driver to display.
        
        ARCHITECTURE: Loads complete history from _all_drivers_lap_data.
        No data reset - instant switching with full history preserved.
        """
        if self._current_driver == driver_num:
            return  # Already selected, no action needed
            
        self._current_driver = driver_num
        
        driver_info = self._drivers_data.get(driver_num, {})
        if isinstance(driver_info, dict):
            # 獲取車手代碼 (TLA) - 欄位名稱是 driver_tla
            driver_code = driver_info.get("driver_tla", driver_num)
            driver_name = driver_info.get("name", driver_code)
            team_color = driver_info.get("team_color", "FFFFFF")
            
            print(f"[DRIVER_STRATEGY] select_driver: {driver_num} -> TLA={driver_code}, color={team_color}")
            
            # 設定車手基本資訊
            self._strategy_widget.select_driver(driver_code, driver_name, team_color)
            
            # 從 _all_drivers_lap_data 載入完整歷史資料
            if driver_num in self._all_drivers_lap_data:
                self._refresh_widget_from_driver_data(driver_num)
            else:
                # 首次選擇此車手，確保創建資料結構
                self._get_or_create_driver_data(driver_num, driver_info)
    
    def _parse_time_to_seconds(self, time_str: str) -> Optional[float]:
        """將時間字串解析為秒數 (參照 lap_history)"""
        if not time_str:
            return None
        
        try:
            # 格式: "1:23.456" 或 "23.456"
            if ':' in str(time_str):
                parts = str(time_str).split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except (ValueError, IndexError):
            return None
            
    def get_current_driver(self) -> str:
        """Get the currently selected driver number."""
        return self._current_driver
        
    def get_available_drivers(self) -> List[str]:
        """Get list of available driver numbers."""
        return list(self._drivers_data.keys())
