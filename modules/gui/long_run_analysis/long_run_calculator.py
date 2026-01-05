#!/usr/bin/env python3
"""
Long Run Calculator

Core calculation engine for Long Run & Degradation Analysis.
Handles:
1. Auto-detection of Long Run stints
2. Fuel correction calculations
3. Track Evolution calculation
4. True degradation rate calculation

Author: F1T Team
Date: 2025-12-30
Version: 1.0.0
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import statistics

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

# Import core modules using absolute path to avoid conflict with strategy_simulator/core
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

_core_logger = None
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


@dataclass
class LapData:
    """Single lap data structure"""
    lap_number: int
    lap_time: float  # seconds
    stint: int
    compound: str
    tyre_life: int
    sector1: Optional[float] = None
    sector2: Optional[float] = None
    sector3: Optional[float] = None
    is_pit_in: bool = False
    is_pit_out: bool = False
    is_valid: bool = True
    driver_code: str = ""


@dataclass
class StintInfo:
    """Detected stint information"""
    driver_code: str
    stint_number: int
    start_lap: int
    end_lap: int
    lap_count: int
    compound: str
    is_long_run: bool = False
    confidence: float = 0.0  # 0-1, how likely this is a genuine long run
    selected: bool = False  # User selection state
    
    @property
    def lap_range(self) -> Tuple[int, int]:
        return (self.start_lap, self.end_lap)


@dataclass
class DriverFuelSettings:
    """Per-driver fuel settings"""
    driver_code: str
    start_fuel_kg: float = 85.0
    fuel_kg_per_lap: float = 1.70
    fuel_effect_coefficient: float = 0.030
    use_track_defaults: bool = True


@dataclass
class DegradationResult:
    """Degradation calculation result for a driver"""
    driver_code: str
    compound: str
    lap_count: int
    raw_degradation: float  # seconds (last lap - first lap)
    track_evolution: float  # seconds (negative = track got faster)
    fuel_adjustment: float  # seconds (fuel correction amount)
    true_degradation: float  # seconds
    degradation_per_lap: float  # seconds/lap
    fuel_corrected_times: List[float] = field(default_factory=list)
    lap_numbers: List[int] = field(default_factory=list)


class LongRunCalculator:
    """
    Long Run & Degradation calculation engine
    
    Usage:
        calculator = LongRunCalculator()
        calculator.load_lap_data(api_data)
        stints = calculator.auto_detect_long_runs()
        
        # User selects stints...
        calculator.set_selected_stints(selected_stints)
        
        # Configure fuel settings
        calculator.set_fuel_settings(driver_settings)
        
        # Calculate
        results = calculator.calculate_degradation()
    """
    
    # Detection thresholds
    MIN_CONSECUTIVE_LAPS = 4
    MAX_LAP_TIME_STDDEV = 1.5  # seconds - threshold for "stable" lap times
    OUTLAP_TIME_THRESHOLD = 5.0  # seconds slower than average = outlap
    
    def __init__(self):
        self._all_laps: Dict[str, List[LapData]] = {}  # driver_code -> laps
        self._detected_stints: List[StintInfo] = []
        self._selected_stints: List[StintInfo] = []
        self._fuel_settings: Dict[str, DriverFuelSettings] = {}
        self._track_defaults: Dict[str, float] = {}
        self._track_evolution_method: str = "statistical"  # or "reference"
        self._reference_driver: Optional[str] = None
    
    def load_lap_data(self, api_data: Dict[str, Any]) -> bool:
        """
        Load lap data from Function 28 API response
        
        Args:
            api_data: API response containing lap data
        
        Returns:
            True if data loaded successfully
        """
        self._all_laps.clear()
        
        try:
            # Handle various API response formats
            if 'data' in api_data:
                data = api_data['data']
            else:
                data = api_data
            
            # Format 0: 'all_drivers_detailed_laptime' (Function 28 API)
            if 'all_drivers_detailed_laptime' in data:
                drivers_data = data['all_drivers_detailed_laptime']
                for driver_code, driver_info in drivers_data.items():
                    laps = self._parse_driver_laps(driver_code, driver_info)
                    if laps:
                        self._all_laps[driver_code] = laps
            
            # Format 1: 'drivers' dict with driver data
            elif 'drivers' in data:
                drivers_data = data['drivers']
                for driver_code, driver_info in drivers_data.items():
                    laps = self._parse_driver_laps(driver_code, driver_info)
                    if laps:
                        self._all_laps[driver_code] = laps
            
            # Format 2: 'laps' list with mixed driver data
            elif 'laps' in data:
                laps_list = data['laps']
                for lap_entry in laps_list:
                    driver = lap_entry.get('driver', lap_entry.get('Driver', ''))
                    if driver:
                        if driver not in self._all_laps:
                            self._all_laps[driver] = []
                        lap = self._parse_single_lap(lap_entry, driver)
                        if lap:
                            self._all_laps[driver].append(lap)
            
            _get_logger().info(f"[LONGRUN_CALC] Loaded lap data for {len(self._all_laps)} drivers")
            return len(self._all_laps) > 0
            
        except Exception as e:
            _get_logger().error(f"[LONGRUN_CALC] Failed to load lap data: {e}")
            return False
    
    def _parse_driver_laps(self, driver_code: str, driver_info: Dict) -> List[LapData]:
        """Parse laps for a single driver"""
        laps = []
        
        # Try various data structures (Function 28 uses 'detailed_lap_data')
        laps_data = driver_info.get('detailed_lap_data', 
                    driver_info.get('laps', 
                    driver_info.get('lap_times', [])))
        
        if isinstance(laps_data, list):
            for lap_entry in laps_data:
                lap = self._parse_single_lap(lap_entry, driver_code)
                if lap:
                    laps.append(lap)
        
        return sorted(laps, key=lambda x: x.lap_number)
    
    def _parse_single_lap(self, lap_entry: Dict, driver_code: str) -> Optional[LapData]:
        """Parse a single lap entry"""
        try:
            lap_number = lap_entry.get('LapNumber', lap_entry.get('lap_number', 0))
            lap_time = lap_entry.get('LapTime', lap_entry.get('lap_time', 0))
            
            # Convert lap time if in timedelta format or string
            if isinstance(lap_time, str):
                # Parse "M:SS.mmm" format
                parts = lap_time.split(':')
                if len(parts) == 2:
                    lap_time = float(parts[0]) * 60 + float(parts[1])
                else:
                    lap_time = float(lap_time)
            elif hasattr(lap_time, 'total_seconds'):
                lap_time = lap_time.total_seconds()
            
            if not lap_number or not lap_time or lap_time <= 0:
                return None
            
            return LapData(
                lap_number=int(lap_number),
                lap_time=float(lap_time),
                stint=lap_entry.get('Stint', lap_entry.get('stint', 1)),
                compound=lap_entry.get('Compound', lap_entry.get('compound', 'UNKNOWN')).upper(),
                tyre_life=lap_entry.get('TyreLife', lap_entry.get('tyre_life', 1)),
                sector1=lap_entry.get('Sector1Time', lap_entry.get('sector1')),
                sector2=lap_entry.get('Sector2Time', lap_entry.get('sector2')),
                sector3=lap_entry.get('Sector3Time', lap_entry.get('sector3')),
                is_pit_in=bool(lap_entry.get('PitInTime', lap_entry.get('pit_in', False))),
                is_pit_out=bool(lap_entry.get('PitOutTime', lap_entry.get('pit_out', False))),
                is_valid=lap_entry.get('IsAccurate', lap_entry.get('is_valid', True)),
                driver_code=driver_code
            )
        except Exception as e:
            _get_logger().warning(f"[LONGRUN_CALC] Failed to parse lap: {e}")
            return None
    
    def auto_detect_long_runs(self, min_laps: int = None) -> List[StintInfo]:
        """
        Auto-detect potential Long Run stints
        
        Args:
            min_laps: Minimum consecutive laps (default: MIN_CONSECUTIVE_LAPS)
        
        Returns:
            List of detected stints
        """
        if min_laps is None:
            min_laps = self.MIN_CONSECUTIVE_LAPS
        
        self._detected_stints.clear()
        
        for driver_code, laps in self._all_laps.items():
            driver_stints = self._detect_driver_stints(driver_code, laps, min_laps)
            self._detected_stints.extend(driver_stints)
        
        # Sort by driver, then stint number
        self._detected_stints.sort(key=lambda x: (x.driver_code, x.stint_number))
        
        _get_logger().info(f"[LONGRUN_CALC] Detected {len(self._detected_stints)} potential Long Run stints")
        return self._detected_stints
    
    def _detect_driver_stints(self, driver_code: str, laps: List[LapData], 
                               min_laps: int) -> List[StintInfo]:
        """Detect stints for a single driver"""
        stints = []
        
        # Group laps by stint number
        stint_groups: Dict[int, List[LapData]] = {}
        for lap in laps:
            if lap.stint not in stint_groups:
                stint_groups[lap.stint] = []
            stint_groups[lap.stint].append(lap)
        
        for stint_num, stint_laps in stint_groups.items():
            # Filter out pit laps and invalid laps
            valid_laps = [
                lap for lap in stint_laps 
                if lap.is_valid and not lap.is_pit_in and not lap.is_pit_out
            ]
            
            if len(valid_laps) < min_laps:
                continue
            
            # Check for stability (low standard deviation)
            lap_times = [lap.lap_time for lap in valid_laps]
            avg_time = statistics.mean(lap_times)
            
            # Exclude outlaps (significantly slower)
            clean_laps = [
                lap for lap in valid_laps 
                if lap.lap_time < avg_time + self.OUTLAP_TIME_THRESHOLD
            ]
            
            if len(clean_laps) < min_laps:
                continue
            
            # Calculate stability score
            clean_times = [lap.lap_time for lap in clean_laps]
            stddev = statistics.stdev(clean_times) if len(clean_times) > 1 else 0
            
            is_long_run = stddev < self.MAX_LAP_TIME_STDDEV
            confidence = max(0, 1 - (stddev / self.MAX_LAP_TIME_STDDEV))
            
            # Get compound from first lap
            compound = clean_laps[0].compound if clean_laps else "UNKNOWN"
            
            stint_info = StintInfo(
                driver_code=driver_code,
                stint_number=stint_num,
                start_lap=clean_laps[0].lap_number,
                end_lap=clean_laps[-1].lap_number,
                lap_count=len(clean_laps),
                compound=compound,
                is_long_run=is_long_run,
                confidence=confidence,
                selected=is_long_run  # Auto-select if detected as long run
            )
            stints.append(stint_info)
        
        return stints
    
    def set_selected_stints(self, stints: List[StintInfo]) -> None:
        """Set user-selected stints for analysis"""
        self._selected_stints = stints
        _get_logger().info(f"[LONGRUN_CALC] Selected {len(stints)} stints for analysis")
    
    def set_fuel_settings(self, settings: Dict[str, DriverFuelSettings]) -> None:
        """Set per-driver fuel settings"""
        self._fuel_settings = settings
    
    def set_track_defaults(self, defaults: Dict[str, float]) -> None:
        """Set track default fuel values"""
        self._track_defaults = defaults
    
    def set_track_evolution_method(self, method: str, reference_driver: str = None) -> None:
        """
        Set Track Evolution calculation method
        
        Args:
            method: "statistical", "reference", or "hybrid"
            reference_driver: Driver code for reference method
        """
        self._track_evolution_method = method
        self._reference_driver = reference_driver
    
    def calculate_degradation(self) -> List[DegradationResult]:
        """
        Calculate degradation for all selected stints
        
        Returns:
            List of DegradationResult for each driver/stint
        """
        results = []
        
        if not self._selected_stints:
            _get_logger().warning("[LONGRUN_CALC] No stints selected for analysis")
            return results
        
        # Calculate Track Evolution first
        track_evolution = self._calculate_track_evolution()
        
        for stint in self._selected_stints:
            result = self._calculate_stint_degradation(stint, track_evolution)
            if result:
                results.append(result)
        
        _get_logger().info(f"[LONGRUN_CALC] Calculated degradation for {len(results)} stints")
        return results
    
    def _calculate_track_evolution(self) -> Dict[int, float]:
        """
        Calculate Track Evolution for each lap number
        
        Uses only laps from selected stints (not all laps)
        
        Returns:
            Dict mapping lap_number -> time_delta (negative = faster)
        """
        if self._track_evolution_method == "reference" and self._reference_driver:
            return self._calculate_track_evolution_reference()
        else:
            return self._calculate_track_evolution_statistical()
    
    def _calculate_track_evolution_statistical(self) -> Dict[int, float]:
        """Statistical model: median lap times from selected drivers in selected lap range"""
        track_evo = {}
        
        # Collect all laps from selected stints only
        lap_times_by_number: Dict[int, List[float]] = {}
        
        for stint in self._selected_stints:
            driver_laps = self._all_laps.get(stint.driver_code, [])
            for lap in driver_laps:
                if stint.start_lap <= lap.lap_number <= stint.end_lap:
                    if lap.is_valid and not lap.is_pit_in and not lap.is_pit_out:
                        if lap.lap_number not in lap_times_by_number:
                            lap_times_by_number[lap.lap_number] = []
                        lap_times_by_number[lap.lap_number].append(lap.lap_time)
        
        if not lap_times_by_number:
            return {}
        
        # Calculate median for each lap number
        medians = {}
        for lap_num, times in lap_times_by_number.items():
            medians[lap_num] = statistics.median(times)
        
        # Find baseline (first common lap)
        sorted_laps = sorted(medians.keys())
        if not sorted_laps:
            return {}
        
        baseline = medians[sorted_laps[0]]
        
        # Calculate delta from baseline
        for lap_num in sorted_laps:
            track_evo[lap_num] = medians[lap_num] - baseline
        
        return track_evo
    
    def _calculate_track_evolution_reference(self) -> Dict[int, float]:
        """Reference driver method: use fresh-tyre driver as baseline"""
        track_evo = {}
        
        if not self._reference_driver or self._reference_driver not in self._all_laps:
            _get_logger().warning("[LONGRUN_CALC] Reference driver not found, falling back to statistical")
            return self._calculate_track_evolution_statistical()
        
        ref_laps = self._all_laps[self._reference_driver]
        if not ref_laps:
            return self._calculate_track_evolution_statistical()
        
        # Use reference driver's laps directly
        valid_laps = [
            lap for lap in ref_laps 
            if lap.is_valid and not lap.is_pit_in and not lap.is_pit_out
        ]
        
        if not valid_laps:
            return {}
        
        baseline = valid_laps[0].lap_time
        for lap in valid_laps:
            track_evo[lap.lap_number] = lap.lap_time - baseline
        
        return track_evo
    
    def _calculate_stint_degradation(self, stint: StintInfo, 
                                      track_evolution: Dict[int, float]) -> Optional[DegradationResult]:
        """Calculate degradation for a single stint"""
        driver_laps = self._all_laps.get(stint.driver_code, [])
        if not driver_laps:
            return None
        
        # Get laps in stint range
        stint_laps = [
            lap for lap in driver_laps
            if stint.start_lap <= lap.lap_number <= stint.end_lap
            and lap.is_valid and not lap.is_pit_in and not lap.is_pit_out
        ]
        
        if len(stint_laps) < 2:
            return None
        
        # Get fuel settings
        fuel = self._fuel_settings.get(stint.driver_code, DriverFuelSettings(driver_code=stint.driver_code))
        
        # Calculate fuel-corrected times
        fuel_corrected_times = []
        lap_numbers = []
        
        for lap in stint_laps:
            # Fuel consumed since stint start
            laps_into_stint = lap.tyre_life
            fuel_consumed = laps_into_stint * fuel.fuel_kg_per_lap
            fuel_effect = fuel_consumed * fuel.fuel_effect_coefficient
            
            # Fuel-corrected time (add back the time gained from lighter fuel)
            corrected_time = lap.lap_time + fuel_effect
            fuel_corrected_times.append(corrected_time)
            lap_numbers.append(lap.lap_number)
        
        # Calculate degradation
        first_lap_time = fuel_corrected_times[0]
        last_lap_time = fuel_corrected_times[-1]
        raw_deg = last_lap_time - first_lap_time
        
        # Get track evolution for this lap range
        start_evo = track_evolution.get(lap_numbers[0], 0)
        end_evo = track_evolution.get(lap_numbers[-1], 0)
        track_evo_delta = end_evo - start_evo
        
        # Total fuel adjustment
        total_fuel_consumed = len(stint_laps) * fuel.fuel_kg_per_lap
        fuel_adjustment = total_fuel_consumed * fuel.fuel_effect_coefficient
        
        # True degradation
        true_deg = raw_deg - track_evo_delta
        deg_per_lap = true_deg / len(stint_laps) if stint_laps else 0
        
        return DegradationResult(
            driver_code=stint.driver_code,
            compound=stint.compound,
            lap_count=len(stint_laps),
            raw_degradation=raw_deg,
            track_evolution=track_evo_delta,
            fuel_adjustment=fuel_adjustment,
            true_degradation=true_deg,
            degradation_per_lap=deg_per_lap,
            fuel_corrected_times=fuel_corrected_times,
            lap_numbers=lap_numbers
        )
    
    def get_driver_codes(self) -> List[str]:
        """Get list of all driver codes in loaded data"""
        return list(self._all_laps.keys())
    
    def get_driver_laps(self, driver_code: str) -> List[LapData]:
        """Get all laps for a driver"""
        return self._all_laps.get(driver_code, [])
    
    def get_detected_stints(self) -> List[StintInfo]:
        """Get all detected stints"""
        return self._detected_stints
    
    def get_selected_stints(self) -> List[StintInfo]:
        """Get user-selected stints"""
        return self._selected_stints
