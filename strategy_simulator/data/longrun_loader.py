#!/usr/bin/env python3
"""
Long Run Data Loader for Strategy Simulator

Imports core calculation engine from main GUI's Long Run module and provides
high-level API for strategy simulation needs. This ensures:
1. Unified calculation logic across GUI and Strategy Simulator
2. Easy future integration into main GUI
3. Additional strategy-specific data structures (LongRunData, DegradationData)

The core calculation classes (LongRunCalculator, LapData, StintInfo, etc.) are
imported from modules.gui.long_run_analysis.long_run_calculator.

Author: F1T Team
Date: 2025-12-30
Updated: 2026-01-04 (Use main GUI LongRunCalculator)
Version: 3.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import statistics
import os

# Lazy imports
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# =============================================================================
# Import core classes from main GUI Long Run module
# =============================================================================

try:
    from modules.gui.long_run_analysis.long_run_calculator import (
        LongRunCalculator as _MainGUILongRunCalculator,
        LapData,
        StintInfo,
        DriverFuelSettings,
        DegradationResult,
    )
    HAS_MAIN_GUI_CALCULATOR = True
    print("[LONGRUN_LOADER] Using main GUI LongRunCalculator")
except ImportError as e:
    HAS_MAIN_GUI_CALCULATOR = False
    print(f"[LONGRUN_LOADER] Warning: Could not import main GUI LongRunCalculator: {e}")
    print("[LONGRUN_LOADER] Falling back to local definitions")
    
    _MainGUILongRunCalculator = None
    DegradationResult = None
    
    # Fallback: Define core classes locally if import fails
    @dataclass
    class LapData:
        """Single lap data structure (fallback)"""
        lap_number: int
        lap_time: float  # seconds
        stint: int
        compound: str
        tyre_life: int
        driver_code: str = ""
        sector1: Optional[float] = None
        sector2: Optional[float] = None
        sector3: Optional[float] = None
        is_pit_in: bool = False
        is_pit_out: bool = False
        is_valid: bool = True
    
    @dataclass
    class StintInfo:
        """Detected stint information (fallback)"""
        driver_code: str
        stint_number: int
        start_lap: int
        end_lap: int
        lap_count: int
        compound: str
        lap_times: List[float] = field(default_factory=list)
        lap_numbers: List[int] = field(default_factory=list)
        is_long_run: bool = False
        confidence: float = 0.0
        selected: bool = False
        
        @property
        def lap_range(self) -> Tuple[int, int]:
            return (self.start_lap, self.end_lap)
    
    @dataclass
    class DriverFuelSettings:
        """Per-driver fuel settings (fallback)"""
        driver_code: str
        start_fuel_kg: float = 85.0
        fuel_kg_per_lap: float = 1.70
        fuel_effect_coefficient: float = 0.030
        use_track_defaults: bool = True


# =============================================================================
# Strategy Simulator Extended Data Classes
# =============================================================================
# These classes extend the main GUI's output for strategy simulation needs

@dataclass
class DriverDegradationResult:
    """Extended degradation result for strategy simulation"""
    driver_code: str
    compound: str
    stint_number: int
    lap_count: int
    raw_degradation: float  # seconds/lap
    fuel_adjustment: float  # seconds/lap
    track_evolution: float  # seconds/lap
    true_degradation: float  # seconds/lap (final result)
    fuel_corrected_times: List[float] = field(default_factory=list)
    lap_numbers: List[int] = field(default_factory=list)
    r_squared: float = 0.0
    
    @classmethod
    def from_main_gui_result(cls, result, stint_number: int = 1) -> 'DriverDegradationResult':
        """Convert main GUI DegradationResult to strategy simulator format"""
        return cls(
            driver_code=result.driver_code,
            compound=result.compound,
            stint_number=stint_number,
            lap_count=result.lap_count,
            raw_degradation=result.raw_degradation,
            fuel_adjustment=result.fuel_adjustment,
            track_evolution=result.track_evolution,
            true_degradation=result.degradation_per_lap,  # Note: renamed field
            fuel_corrected_times=result.fuel_corrected_times,
            lap_numbers=result.lap_numbers,
            r_squared=0.0
        )


@dataclass
class DegradationData:
    """Aggregated degradation data for a specific compound"""
    compound: str
    deg_per_lap: float
    sample_laps: int = 0
    confidence: float = 1.0
    driver_samples: List[str] = field(default_factory=list)
    min_deg: float = 0.0
    max_deg: float = 0.0
    driver_results: List[DriverDegradationResult] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'compound': self.compound,
            'deg_per_lap': round(self.deg_per_lap, 4),
            'sample_laps': self.sample_laps,
            'confidence': round(self.confidence, 2),
            'driver_samples': self.driver_samples,
            'min_deg': round(self.min_deg, 4),
            'max_deg': round(self.max_deg, 4),
            'driver_results': [
                {
                    'driver': r.driver_code,
                    'stint': r.stint_number,
                    'laps': r.lap_count,
                    'deg_per_lap': round(r.true_degradation, 4),
                    'raw_deg': round(r.raw_degradation, 4),
                    'fuel_adj': round(r.fuel_adjustment, 4),
                    'track_evo': round(r.track_evolution, 4),
                }
                for r in self.driver_results
            ]
        }


@dataclass
class LongRunData:
    """Complete Long Run data for strategy simulation"""
    track_name: str
    session_type: str
    year: int
    
    # Aggregated degradation rates per compound
    degradation: Dict[str, DegradationData] = field(default_factory=dict)
    
    # Per-driver detailed results
    driver_results: Dict[str, List[DriverDegradationResult]] = field(default_factory=dict)
    
    # Track specific parameters
    base_lap_time: Optional[float] = None
    base_lap_time_method: str = "estimated"  # "fp2_calculated" or "estimated"
    fuel_kg_per_lap: Optional[float] = None
    fuel_effect: Optional[float] = None
    
    # Degradation acceleration per compound (for quadratic model)
    deg_acceleration: Dict[str, float] = field(default_factory=lambda: {
        'SOFT': 0.0029, 'MEDIUM': 0.0019, 'HARD': 0.0012
    })
    
    # Compound deltas (relative to MEDIUM)
    compound_deltas: Dict[str, float] = field(default_factory=dict)
    
    # Track evolution data
    track_evolution_per_lap: float = 0.0
    
    # Metadata
    stints_analyzed: int = 0
    drivers_analyzed: int = 0
    calculation_method: str = "Cappello & Hoegh 2025"
    
    def get_deg_rate(self, compound: str) -> float:
        """Get average degradation rate for compound."""
        compound = compound.upper()
        if compound in self.degradation:
            return self.degradation[compound].deg_per_lap
        defaults = {'SOFT': 0.120, 'MEDIUM': 0.080, 'HARD': 0.045}
        return defaults.get(compound, 0.080)
    
    def get_driver_deg_rate(self, driver_code: str, compound: str) -> Optional[float]:
        """Get degradation rate for a specific driver and compound."""
        compound = compound.upper()
        if driver_code in self.driver_results:
            for result in self.driver_results[driver_code]:
                if result.compound.upper() == compound:
                    return result.true_degradation
        return None
    
    def get_compound_delta(self, compound: str) -> float:
        """Get compound delta (time difference from MEDIUM)."""
        compound = compound.upper()
        return self.compound_deltas.get(compound, 0.0)
    
    def get_deg_acceleration(self, compound: str) -> float:
        """Get degradation acceleration for compound (quadratic term)."""
        compound = compound.upper()
        if compound in self.deg_acceleration:
            return self.deg_acceleration[compound]
        defaults = {'SOFT': 0.0029, 'MEDIUM': 0.0019, 'HARD': 0.0012}
        return defaults.get(compound, 0.0019)
    
    def to_dict(self) -> dict:
        return {
            'track_name': self.track_name,
            'session_type': self.session_type,
            'year': self.year,
            'degradation': {k: v.to_dict() for k, v in self.degradation.items()},
            'driver_results': {
                driver: [
                    {
                        'compound': r.compound,
                        'stint': r.stint_number,
                        'laps': r.lap_count,
                        'deg_per_lap': round(r.true_degradation, 4),
                    }
                    for r in results
                ]
                for driver, results in self.driver_results.items()
            },
            'base_lap_time': self.base_lap_time,
            'base_lap_time_method': self.base_lap_time_method,
            'fuel_kg_per_lap': self.fuel_kg_per_lap,
            'fuel_effect': self.fuel_effect,
            'deg_acceleration': self.deg_acceleration,
            'compound_deltas': self.compound_deltas,
            'track_evolution_per_lap': round(self.track_evolution_per_lap, 4),
            'stints_analyzed': self.stints_analyzed,
            'drivers_analyzed': self.drivers_analyzed,
            'calculation_method': self.calculation_method,
        }


# =============================================================================
# Long Run Calculator Engine - Wrapper using Main GUI's Calculator
# =============================================================================

class LongRunCalculator:
    """
    Long Run calculation engine wrapper.
    
    When main GUI LongRunCalculator is available, delegates to it.
    Otherwise, uses local fallback implementation for backward compatibility.
    
    This ensures unified calculation logic while maintaining strategy simulator
    independence when main GUI modules are not available.
    """
    
    # Detection thresholds (same as main GUI)
    MIN_CONSECUTIVE_LAPS = 4
    MAX_LAP_TIME_STDDEV = 1.5  # seconds
    OUTLAP_TIME_THRESHOLD = 5.0  # seconds slower than average
    
    # Default fuel settings
    DEFAULT_FUEL_KG_PER_LAP = 1.70
    DEFAULT_FUEL_EFFECT = 0.030  # seconds per kg
    DEFAULT_START_FUEL = 85.0
    
    def __init__(self):
        self._use_main_gui = HAS_MAIN_GUI_CALCULATOR
        self._main_calculator = None
        
        # Initialize main GUI calculator if available
        if self._use_main_gui:
            try:
                self._main_calculator = _MainGUILongRunCalculator()
                print("[LONGRUN_CALC] Using main GUI calculator")
            except Exception as e:
                print(f"[LONGRUN_CALC] Failed to init main GUI calculator: {e}")
                self._use_main_gui = False
        
        # Local state for fallback and result conversion
        self._all_laps: Dict[str, List[LapData]] = {}
        self._detected_stints: List[StintInfo] = []
        self._selected_stints: List[StintInfo] = []
        self._fuel_settings: Dict[str, DriverFuelSettings] = {}
        self._track_evolution: Dict[int, float] = {}
        self._track_evolution_per_lap: float = 0.0
        self._results: List[DriverDegradationResult] = []
    
    def load_api_data(self, api_data: Dict[str, Any]) -> bool:
        """
        Load lap data from Function 28 API response.
        
        Delegates to main GUI calculator if available.
        """
        self._all_laps.clear()
        
        if self._use_main_gui and self._main_calculator:
            # Use main GUI's loader
            try:
                success = self._main_calculator.load_lap_data(api_data)
                if success:
                    # Cache driver codes for local access
                    for driver in self._main_calculator.get_driver_codes():
                        self._all_laps[driver] = self._main_calculator.get_driver_laps(driver)
                return success
            except Exception as e:
                print(f"[LONGRUN_CALC] Main GUI loader failed: {e}, using fallback")
        
        # Fallback: local parsing
        return self._load_api_data_local(api_data)
    
    def _load_api_data_local(self, api_data: Dict[str, Any]) -> bool:
        
        try:
            # Unwrap nested data
            data = api_data
            if 'data' in data:
                data = data['data']
            if 'all_drivers_detailed_laptime' in data:
                data = {'drivers': data['all_drivers_detailed_laptime']}
            
            # Parse each driver's laps
            drivers_data = data.get('drivers', data)
            if not isinstance(drivers_data, dict):
                print(f"[LONGRUN_CALC] Invalid data format: {type(drivers_data)}")
                return False
            
            for driver_code, driver_info in drivers_data.items():
                laps = self._parse_driver_laps(driver_code, driver_info)
                if laps:
                    self._all_laps[driver_code] = laps
            
            print(f"[LONGRUN_CALC] Loaded data for {len(self._all_laps)} drivers")
            return len(self._all_laps) > 0
            
        except Exception as e:
            print(f"[LONGRUN_CALC] Failed to load data: {e}")
            return False
    
    def _parse_driver_laps(self, driver_code: str, driver_info: Any) -> List[LapData]:
        """Parse laps for a single driver."""
        laps = []
        
        # Handle different data structures
        if isinstance(driver_info, dict):
            laps_data = driver_info.get('detailed_lap_data', 
                        driver_info.get('laps', 
                        driver_info.get('lap_times', [])))
        elif isinstance(driver_info, list):
            laps_data = driver_info
        else:
            return []
        
        for entry in laps_data:
            lap = self._parse_single_lap(entry, driver_code)
            if lap:
                laps.append(lap)
        
        return sorted(laps, key=lambda x: x.lap_number)
    
    def _parse_single_lap(self, entry: Dict, driver_code: str) -> Optional[LapData]:
        """Parse a single lap entry."""
        try:
            lap_number = entry.get('LapNumber', entry.get('lap_number', 0))
            lap_time = entry.get('LapTime', entry.get('lap_time', 
                      entry.get('lap_time_seconds', 0)))
            
            # Skip N/A or invalid lap times early
            if lap_time in (None, 'N/A', 'n/a', '', 'NaT'):
                return None
            
            # Convert lap time formats
            if isinstance(lap_time, str):
                # Check for N/A-like values
                if lap_time.upper() in ('N/A', 'NA', 'NAT', 'NONE', ''):
                    return None
                parts = lap_time.split(':')
                if len(parts) == 2:
                    lap_time = float(parts[0]) * 60 + float(parts[1])
                else:
                    lap_time = float(lap_time)
            elif hasattr(lap_time, 'total_seconds'):
                lap_time = lap_time.total_seconds()
            
            if not lap_number or not lap_time or lap_time <= 0:
                return None
            
            compound = entry.get('Compound', 
                       entry.get('compound', 
                       entry.get('tire_compound', 'UNKNOWN')))
            if isinstance(compound, str):
                compound = compound.upper()
            
            return LapData(
                lap_number=int(lap_number),
                lap_time=float(lap_time),
                stint=entry.get('Stint', entry.get('stint', 1)),
                compound=compound,
                tyre_life=entry.get('TyreLife', entry.get('tyre_life', 1)),
                driver_code=driver_code,
                sector1=entry.get('Sector1Time', entry.get('sector1')),
                sector2=entry.get('Sector2Time', entry.get('sector2')),
                sector3=entry.get('Sector3Time', entry.get('sector3')),
                is_pit_in=bool(entry.get('PitInTime', entry.get('pit_in', False))),
                is_pit_out=bool(entry.get('PitOutTime', entry.get('pit_out', False))),
                is_valid=entry.get('IsAccurate', entry.get('is_valid', True)),
            )
        except Exception as e:
            print(f"[LONGRUN_CALC] Failed to parse lap: {e}")
            return None
    
    def detect_long_runs(self, min_laps: int = None) -> List[StintInfo]:
        """
        Auto-detect Long Run stints.
        
        Delegates to main GUI calculator if available, otherwise uses local detection.
        """
        if min_laps is None:
            min_laps = self.MIN_CONSECUTIVE_LAPS
        
        self._detected_stints.clear()
        
        if self._use_main_gui and self._main_calculator:
            # Use main GUI's detection
            main_stints = self._main_calculator.auto_detect_long_runs(min_laps)
            # Convert to strategy simulator StintInfo format
            for ms in main_stints:
                stint = StintInfo(
                    driver_code=ms.driver_code,
                    stint_number=ms.stint_number,
                    start_lap=ms.start_lap,
                    end_lap=ms.end_lap,
                    lap_count=ms.lap_count,
                    compound=ms.compound,
                    is_long_run=ms.is_long_run,
                    confidence=ms.confidence,
                    selected=ms.selected
                )
                self._detected_stints.append(stint)
        else:
            # Fallback: local detection
            for driver_code, laps in self._all_laps.items():
                stints = self._detect_driver_stints(driver_code, laps, min_laps)
                self._detected_stints.extend(stints)
        
        # Sort by driver, then stint number
        self._detected_stints.sort(key=lambda x: (x.driver_code, x.stint_number))
        
        # Auto-select detected long runs
        self._selected_stints = [s for s in self._detected_stints if s.is_long_run]
        
        print(f"[LONGRUN_CALC] Detected {len(self._detected_stints)} stints, "
              f"{len(self._selected_stints)} auto-selected as long runs")
        return self._detected_stints
    
    def _detect_driver_stints(self, driver_code: str, laps: List[LapData], 
                               min_laps: int) -> List[StintInfo]:
        """Detect stints for a single driver."""
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
            
            # Calculate average and filter outlaps
            lap_times = [lap.lap_time for lap in valid_laps]
            avg_time = statistics.mean(lap_times)
            
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
            
            compound = clean_laps[0].compound if clean_laps else "UNKNOWN"
            
            # Skip UNKNOWN compound stints - not useful for strategy analysis
            if compound.upper() == "UNKNOWN":
                print(f"[LONGRUN_CALC] Skipping stint {stint_num} for {driver_code}: UNKNOWN compound")
                continue
            
            stint = StintInfo(
                driver_code=driver_code,
                stint_number=stint_num,
                start_lap=clean_laps[0].lap_number,
                end_lap=clean_laps[-1].lap_number,
                lap_count=len(clean_laps),
                compound=compound,
                lap_times=clean_times,
                lap_numbers=[lap.lap_number for lap in clean_laps],
                is_long_run=is_long_run,
                confidence=confidence,
                selected=is_long_run
            )
            stints.append(stint)
        
        return stints
    
    def set_fuel_settings(self, settings: Dict[str, DriverFuelSettings] = None):
        """Set fuel settings for each driver. Delegates to main GUI if available."""
        if settings:
            self._fuel_settings = settings
            
            # Also set in main GUI calculator if available
            if self._use_main_gui and self._main_calculator:
                self._main_calculator.set_fuel_settings(settings)
        else:
            # Apply defaults to all drivers
            for driver in self._all_laps.keys():
                self._fuel_settings[driver] = DriverFuelSettings(
                    driver_code=driver,
                    fuel_kg_per_lap=self.DEFAULT_FUEL_KG_PER_LAP,
                    fuel_effect_coefficient=self.DEFAULT_FUEL_EFFECT,
                    start_fuel_kg=self.DEFAULT_START_FUEL
                )
    
    def calculate_track_evolution(self, method: str = "statistical") -> Dict[int, float]:
        """
        Calculate track evolution using statistical median method.
        
        Returns:
            Dict mapping lap_number -> time delta (negative = faster)
        """
        lap_times_by_number: Dict[int, List[float]] = {}
        
        for stint in self._selected_stints:
            for lap_num, lap_time in zip(stint.lap_numbers, stint.lap_times):
                if lap_num not in lap_times_by_number:
                    lap_times_by_number[lap_num] = []
                lap_times_by_number[lap_num].append(lap_time)
        
        if not lap_times_by_number:
            return {}
        
        # Calculate median for each lap
        medians = {}
        for lap_num, times in lap_times_by_number.items():
            medians[lap_num] = statistics.median(times)
        
        if not medians:
            return {}
        
        # Calculate evolution relative to first lap
        sorted_laps = sorted(medians.keys())
        baseline = medians[sorted_laps[0]]
        
        self._track_evolution = {
            lap: medians[lap] - baseline for lap in sorted_laps
        }
        
        # Calculate per-lap evolution
        if len(sorted_laps) > 1:
            total_evo = medians[sorted_laps[-1]] - baseline
            self._track_evolution_per_lap = total_evo / (len(sorted_laps) - 1)
        else:
            self._track_evolution_per_lap = 0.0
        
        print(f"[LONGRUN_CALC] Track evolution: {self._track_evolution_per_lap:.4f} s/lap")
        return self._track_evolution
    
    def calculate_degradation(self) -> List[DriverDegradationResult]:
        """
        Calculate true degradation for all selected stints.
        
        Delegates to main GUI calculator if available, then converts results
        to strategy simulator format (DriverDegradationResult).
        """
        self._results.clear()
        
        if self._use_main_gui and self._main_calculator:
            # Use main GUI's calculation
            try:
                # Set selected stints in main calculator
                main_stints = self._main_calculator.get_detected_stints()
                selected = [s for s in main_stints if s.selected or s.is_long_run]
                self._main_calculator.set_selected_stints(selected)
                
                # Calculate
                main_results = self._main_calculator.calculate_degradation()
                
                # Convert to strategy simulator format
                for i, result in enumerate(main_results):
                    ss_result = DriverDegradationResult.from_main_gui_result(result, i + 1)
                    self._results.append(ss_result)
                
                print(f"[LONGRUN_CALC] (Main GUI) Calculated {len(self._results)} results")
                return self._results
            except Exception as e:
                print(f"[LONGRUN_CALC] Main GUI calculation failed: {e}, using fallback")
        
        # Fallback: local calculation
        if not self._selected_stints:
            print("[LONGRUN_CALC] No stints selected for analysis")
            return []
        
        # Ensure fuel settings exist
        if not self._fuel_settings:
            self.set_fuel_settings()
        
        # Calculate track evolution if not done
        if not self._track_evolution:
            self.calculate_track_evolution()
        
        for stint in self._selected_stints:
            result = self._calculate_stint_degradation(stint)
            if result:
                self._results.append(result)
        
        print(f"[LONGRUN_CALC] Calculated degradation for {len(self._results)} stints")
        return self._results
    
    def _calculate_stint_degradation(self, stint: StintInfo) -> Optional[DriverDegradationResult]:
        """Calculate degradation for a single stint."""
        if stint.lap_count < 2:
            return None
        
        times = stint.lap_times
        laps = stint.lap_numbers
        
        # Calculate raw degradation using linear regression
        raw_deg_per_lap, r_squared = self._linear_regression(times)
        
        # Get fuel settings
        fuel = self._fuel_settings.get(stint.driver_code, 
               DriverFuelSettings(driver_code=stint.driver_code))
        
        # Fuel adjustment per lap (car gets lighter -> faster)
        fuel_adj_per_lap = fuel.fuel_kg_per_lap * fuel.fuel_effect_coefficient
        
        # Track evolution per lap (negative = track faster)
        track_evo_per_lap = self._track_evolution_per_lap
        
        # True degradation = Raw + Fuel Adj - Track Evo
        # Raw deg is positive if times increase
        # Fuel adj is what we lose due to lighter car (add it back)
        # Track evo is negative if track improves (subtract to compensate)
        true_deg_per_lap = raw_deg_per_lap + fuel_adj_per_lap - track_evo_per_lap
        
        # Calculate fuel-corrected times
        fuel_corrected_times = []
        for i, (lap_num, lap_time) in enumerate(zip(laps, times)):
            # Fuel consumed since stint start
            fuel_consumed = i * fuel.fuel_kg_per_lap
            fuel_effect = fuel_consumed * fuel.fuel_effect_coefficient
            # Add back the time gained from lighter fuel
            corrected = lap_time + fuel_effect
            fuel_corrected_times.append(corrected)
        
        return DriverDegradationResult(
            driver_code=stint.driver_code,
            compound=stint.compound,
            stint_number=stint.stint_number,
            lap_count=stint.lap_count,
            raw_degradation=raw_deg_per_lap,
            fuel_adjustment=fuel_adj_per_lap,
            track_evolution=track_evo_per_lap,
            true_degradation=true_deg_per_lap,
            fuel_corrected_times=fuel_corrected_times,
            lap_numbers=laps,
            r_squared=r_squared
        )
    
    def _linear_regression(self, times: List[float]) -> Tuple[float, float]:
        """
        Calculate linear regression slope (degradation per lap).
        
        Returns:
            Tuple of (slope, r_squared)
        """
        if len(times) < 2:
            return 0.0, 0.0
        
        n = len(times)
        x = list(range(n))  # 0, 1, 2, ...
        y = times
        
        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0, 0.0
        
        slope = numerator / denominator
        
        # Calculate R-squared
        y_pred = [y_mean + slope * (x[i] - x_mean) for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return slope, r_squared
    
    def aggregate_results(self) -> Dict[str, DegradationData]:
        """
        Aggregate per-driver results into per-compound summary.
        
        Returns:
            Dict mapping compound -> DegradationData
        """
        compound_results: Dict[str, List[DriverDegradationResult]] = {}
        
        for result in self._results:
            compound = result.compound.upper()
            if compound not in compound_results:
                compound_results[compound] = []
            compound_results[compound].append(result)
        
        aggregated = {}
        for compound, results in compound_results.items():
            deg_values = [r.true_degradation for r in results]
            avg_deg = statistics.mean(deg_values)
            total_laps = sum(r.lap_count for r in results)
            drivers = list(set(r.driver_code for r in results))
            
            # Confidence based on sample size
            confidence = min(1.0, len(results) * total_laps / 20)
            
            aggregated[compound] = DegradationData(
                compound=compound,
                deg_per_lap=avg_deg,
                sample_laps=total_laps,
                confidence=confidence,
                driver_samples=drivers,
                min_deg=min(deg_values) if deg_values else 0,
                max_deg=max(deg_values) if deg_values else 0,
                driver_results=results
            )
        
        return aggregated
    
    def get_results(self) -> List[DriverDegradationResult]:
        """Get all calculation results."""
        return self._results
    
    def get_driver_codes(self) -> List[str]:
        """Get all driver codes in loaded data."""
        return list(self._all_laps.keys())


# =============================================================================
# Long Run Loader (High-level API)
# =============================================================================

class LongRunLoader:
    """
    High-level Long Run data loader with full calculation capabilities.
    
    Usage:
        loader = LongRunLoader()
        
        # Option 1: Load and calculate from API
        data = loader.load_and_calculate_from_api(2025, "Abu_Dhabi", "FP2")
        
        # Option 2: Load from cached JSON
        data = loader.load_from_json(json_path)
        
        # Option 3: Use existing calculator results
        data = loader.build_from_calculator(calculator)
        
        # Get degradation rates
        soft_deg = data.get_deg_rate('SOFT')
        ver_soft_deg = data.get_driver_deg_rate('VER', 'SOFT')
    """
    
    # API Configuration
    DEFAULT_API_TIMEOUT = 120.0
    CLI_FUNCTION_ID = 28
    
    # Track name to Grand Prix name mapping for API calls
    TRACK_TO_GP_NAME = {
        "Yas Marina": "Abu_Dhabi",
        "Abu Dhabi": "Abu_Dhabi",
        "Suzuka": "Japan",
        "Melbourne": "Australia",
        "Bahrain": "Bahrain",
        "Jeddah": "Saudi_Arabian",
        "Shanghai": "Chinese",
        "Miami": "Miami",
        "Imola": "Emilia_Romagna",
        "Monaco": "Monaco",
        "Montreal": "Canadian",
        "Barcelona": "Spanish",
        "Spielberg": "Austrian",
        "Silverstone": "British",
        "Hungaroring": "Hungarian",
        "Spa": "Belgian",
        "Zandvoort": "Netherlands",
        "Monza": "Italian",
        "Baku": "Azerbaijan",
        "Singapore": "Singapore",
        "Austin": "United_States",
        "Mexico City": "Mexico_City",
        "Interlagos": "Sao_Paulo",
        "Las Vegas": "Las_Vegas",
        "Lusail": "Qatar",
    }
    
    def __init__(self, cache_dir: Path = None, project_root: Path = None, debug: bool = False):
        if project_root is None:
            current = Path(__file__).resolve()
            project_root = current.parent.parent.parent
        
        self.project_root = Path(project_root)
        self._debug_enabled = debug
        
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = self.project_root / "json" / "long_run"
        
        self._calculator = LongRunCalculator()
        self._loaded_data: Optional[LongRunData] = None
    
    def _debug(self, message: str):
        """Print debug message if debug mode is enabled."""
        if self._debug_enabled:
            print(message)
    
    def load_and_calculate_from_api(
        self,
        year: int,
        race: str,
        session: str = "FP2",
        api_base_url: str = None,
        fuel_settings: Dict[str, DriverFuelSettings] = None
    ) -> Optional[LongRunData]:
        """
        Load data from API and perform full calculation.
        
        This is the main entry point for getting complete Long Run analysis.
        """
        if not HAS_REQUESTS:
            print("[LONGRUN_LOADER] requests library not available")
            return None
        
        # Determine API URL
        if not api_base_url:
            api_base_url = self._determine_api_base_url()
        
        # Fetch data from API
        api_data = self._fetch_api_data(api_base_url, year, race, session)
        if not api_data:
            return None
        
        # Run full calculation
        return self.calculate_from_data(
            api_data, 
            track_name=race, 
            session_type=session, 
            year=year,
            fuel_settings=fuel_settings
        )
    
    def calculate_from_data(
        self,
        api_data: Dict[str, Any],
        track_name: str,
        session_type: str = "FP2",
        year: int = 2025,
        fuel_settings: Dict[str, DriverFuelSettings] = None
    ) -> Optional[LongRunData]:
        """
        Run full Long Run calculation on API data.
        
        Steps:
        1. Load lap data
        2. Detect Long Run stints
        3. Set fuel settings
        4. Calculate track evolution
        5. Calculate true degradation per driver
        6. Aggregate results by compound
        """
        # Step 1: Load data
        if not self._calculator.load_api_data(api_data):
            print("[LONGRUN_LOADER] Failed to load API data")
            return None
        
        # Step 2: Detect Long Runs
        self._calculator.detect_long_runs()
        
        # Step 3: Set fuel settings
        self._calculator.set_fuel_settings(fuel_settings)
        
        # Step 4: Calculate track evolution
        self._calculator.calculate_track_evolution()
        
        # Step 5: Calculate degradation
        results = self._calculator.calculate_degradation()
        
        if not results:
            print("[LONGRUN_LOADER] No degradation results calculated")
            return None
        
        # Step 6: Aggregate and build LongRunData
        aggregated = self._calculator.aggregate_results()
        
        # Group results by driver
        driver_results: Dict[str, List[DriverDegradationResult]] = {}
        for result in results:
            if result.driver_code not in driver_results:
                driver_results[result.driver_code] = []
            driver_results[result.driver_code].append(result)
        
        # Calculate compound deltas
        compound_deltas = self._calculate_compound_deltas(results)
        
        # Build final data object
        data = LongRunData(
            track_name=track_name,
            session_type=session_type,
            year=year,
            degradation=aggregated,
            driver_results=driver_results,
            compound_deltas=compound_deltas,
            track_evolution_per_lap=self._calculator._track_evolution_per_lap,
            stints_analyzed=len(results),
            drivers_analyzed=len(driver_results),
        )
        
        # Calculate base lap time using enhanced method
        base_time, method = self._calculate_base_lap_time(results, fuel_settings)
        data.base_lap_time = base_time
        data.base_lap_time_method = method
        
        # Calculate degradation acceleration from observed data
        data.deg_acceleration = self._calculate_deg_acceleration(results)
        
        self._loaded_data = data
        return data
    
    def _calculate_base_lap_time(
        self, 
        results: List[DriverDegradationResult],
        fuel_settings: Dict[str, DriverFuelSettings]
    ) -> Tuple[float, str]:
        """
        Calculate base lap time from FP2 Long Run data.
        
        Method:
        1. For each stint, extrapolate to lap 1 (new tire) using linear regression intercept
        2. Adjust for fuel difference (FP2 vs race start)
        3. Take the best (fastest) result
        
        Args:
            results: List of driver degradation results
            fuel_settings: Fuel settings per driver
            
        Returns:
            Tuple of (base_lap_time, calculation_method)
        """
        if not results:
            return (90.0, "default_estimate")
        
        # Collect all stint base times (intercept from regression = lap 1 time)
        stint_base_times = []
        
        for result in results:
            if not result.fuel_corrected_times or len(result.fuel_corrected_times) < 3:
                continue
            
            times = result.fuel_corrected_times
            n = len(times)
            laps = list(range(1, n + 1))
            
            # Linear regression: time = intercept + slope * lap
            sum_x = sum(laps)
            sum_y = sum(times)
            sum_xy = sum(x * y for x, y in zip(laps, times))
            sum_x2 = sum(x * x for x in laps)
            
            denominator = n * sum_x2 - sum_x * sum_x
            if denominator == 0:
                continue
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
            
            # intercept = theoretical time at lap 1 (new tire, current fuel)
            # This is already fuel-corrected, so it represents "new tire at FP2 fuel level"
            
            stint_base_times.append({
                'driver': result.driver_code,
                'compound': result.compound,
                'base_time': intercept,
                'deg_slope': slope,
                'laps': n
            })
        
        if not stint_base_times:
            # Fallback: use fastest fuel-corrected time
            all_times = []
            for result in results:
                all_times.extend(result.fuel_corrected_times)
            if all_times:
                return (min(all_times), "fastest_corrected_lap")
            return (90.0, "default_estimate")
        
        # Find the fastest base time
        best_stint = min(stint_base_times, key=lambda x: x['base_time'])
        best_base_time = best_stint['base_time']
        
        # Adjust for FP2 vs race fuel difference
        # FP2 typically runs with ~85-90 kg, race starts with 110 kg
        # The intercept is at FP2 fuel level, we need to add time for heavier fuel
        fp2_fuel_estimate = 85.0  # kg (typical FP2 long run fuel)
        race_start_fuel = 110.0  # kg
        fuel_effect = 0.030  # seconds per kg (typical)
        
        # Race start will be slower due to more fuel
        fuel_adjustment = (race_start_fuel - fp2_fuel_estimate) * fuel_effect
        race_base_time = best_base_time + fuel_adjustment
        
        self._debug(f"[BASE_LAP_TIME] Best stint: {best_stint['driver']} {best_stint['compound']}")
        self._debug(f"[BASE_LAP_TIME] FP2 base time: {best_base_time:.3f}s")
        self._debug(f"[BASE_LAP_TIME] Fuel adjustment: +{fuel_adjustment:.3f}s")
        self._debug(f"[BASE_LAP_TIME] Race base time: {race_base_time:.3f}s")
        
        return (round(race_base_time, 3), "fp2_regression_extrapolation")
    
    def _calculate_deg_acceleration(
        self,
        results: List[DriverDegradationResult]
    ) -> Dict[str, float]:
        """
        Calculate degradation acceleration (quadratic term) from observed data.
        
        Uses the difference method:
        - Split stint into first half and second half
        - Calculate degradation rate for each half
        - Acceleration = (second_half_rate - first_half_rate) / (half_length)
        
        Args:
            results: List of driver degradation results
            
        Returns:
            Dict of compound -> acceleration coefficient
        """
        compound_accelerations: Dict[str, List[float]] = {'SOFT': [], 'MEDIUM': [], 'HARD': []}
        
        for result in results:
            if not result.fuel_corrected_times or len(result.fuel_corrected_times) < 6:
                continue
            
            times = result.fuel_corrected_times
            n = len(times)
            half = n // 2
            
            if half < 3:
                continue
            
            # Calculate degradation rate for first half
            first_half = times[:half]
            first_deg = (first_half[-1] - first_half[0]) / (len(first_half) - 1)
            
            # Calculate degradation rate for second half
            second_half = times[half:]
            second_deg = (second_half[-1] - second_half[0]) / (len(second_half) - 1)
            
            # Acceleration = change in degradation rate per lap
            acceleration = (second_deg - first_deg) / half
            
            # Only use positive accelerations (degradation should increase)
            if acceleration > 0:
                compound = result.compound.upper()
                if compound in compound_accelerations:
                    compound_accelerations[compound].append(acceleration)
        
        # Calculate averages
        deg_acceleration = {}
        defaults = {'SOFT': 0.0029, 'MEDIUM': 0.0019, 'HARD': 0.0012}
        
        for compound, accelerations in compound_accelerations.items():
            if accelerations:
                avg = sum(accelerations) / len(accelerations)
                # Clamp to reasonable range
                deg_acceleration[compound] = max(0.0005, min(0.005, round(avg, 5)))
            else:
                deg_acceleration[compound] = defaults[compound]
        
        return deg_acceleration
    
    def _calculate_compound_deltas(self, results: List[DriverDegradationResult]) -> Dict[str, float]:
        """Calculate compound performance deltas relative to MEDIUM."""
        compound_best_times: Dict[str, float] = {}
        
        for result in results:
            compound = result.compound.upper()
            if result.fuel_corrected_times:
                best_time = min(result.fuel_corrected_times)
                if compound not in compound_best_times:
                    compound_best_times[compound] = best_time
                else:
                    compound_best_times[compound] = min(compound_best_times[compound], best_time)
        
        deltas = {}
        medium_baseline = compound_best_times.get('MEDIUM', 0)
        
        for compound, best_time in compound_best_times.items():
            if medium_baseline > 0:
                deltas[compound] = best_time - medium_baseline
            else:
                deltas[compound] = 0.0
        
        return deltas
    
    def _determine_api_base_url(self) -> str:
        """Determine API base URL."""
        # Check environment variable
        override = os.getenv("F1T_API_BASE_URL")
        if override:
            return override.rstrip('/')
        
        # Try to use core resolver
        try:
            from core.api_base_url import resolve_api_base_url
            return resolve_api_base_url()
        except ImportError:
            pass
        
        # Default to public API
        return "https://api.f1telemetrystationpro.org"
    
    def _fetch_api_data(
        self, 
        base_url: str, 
        year: int, 
        race: str, 
        session: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch lap data from Function 28 API."""
        try:
            # Convert track name to Grand Prix name for API
            api_race_name = self.TRACK_TO_GP_NAME.get(race, race.replace(" ", "_"))
            
            endpoint = f"{base_url}/api/v2/analysis/execute"
            payload = {
                "function_id": self.CLI_FUNCTION_ID,
                "year": year,
                "race": api_race_name,
                "session": session,
            }
            
            print(f"[LONGRUN_LOADER] Fetching: {endpoint} with {payload}")
            
            response = requests.post(
                endpoint,
                params=payload,
                timeout=self.DEFAULT_API_TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success", True):
                    return data.get("data", data)
                else:
                    print(f"[LONGRUN_LOADER] API error: {data.get('message')}")
            else:
                print(f"[LONGRUN_LOADER] HTTP {response.status_code}: {response.text[:200]}")
            
            return None
            
        except Exception as e:
            print(f"[LONGRUN_LOADER] API request failed: {e}")
            return None
    
    def load_fp2_data(
        self, 
        year: int, 
        race: str, 
        session: str = "FP2"
    ) -> Optional[LongRunData]:
        """
        Auto-search and load FP2 Long Run data.
        
        First tries to load from cached JSON, then falls back to API.
        """
        # Try cached JSON first
        json_data = self._search_cached_json(year, race, session)
        if json_data:
            return json_data
        
        # Fall back to API
        return self.load_and_calculate_from_api(year, race, session)
    
    def _search_cached_json(
        self, 
        year: int, 
        race: str, 
        session: str
    ) -> Optional[LongRunData]:
        """Search for cached Long Run JSON files."""
        race_normalized = race.replace(" ", "_")
        race_with_space = race.replace("_", " ")
        
        patterns = [
            f"long_run_{year}_{race_normalized}_{session}.json",
            f"long_run_{year}_{race_with_space}_{session}.json",
            f"degradation_{year}_{race_normalized}_{session}.json",
        ]
        
        search_dirs = [
            self.cache_dir,
            self.project_root / "json",
            self.project_root / "json" / "LiveF1" / str(year),
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for pattern in patterns:
                path = search_dir / pattern
                if path.exists():
                    print(f"[LONGRUN_LOADER] Found cached: {path}")
                    return self.load_from_json(path)
        
        return None
    
    def load_from_json(self, json_path: Path) -> Optional[LongRunData]:
        """Load Long Run data from JSON file."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            return self._parse_json_data(raw_data)
        except Exception as e:
            print(f"[LONGRUN_LOADER] Failed to load JSON: {e}")
            return None
    
    def _parse_json_data(self, raw_data: dict) -> LongRunData:
        """Parse JSON data into LongRunData object."""
        data = LongRunData(
            track_name=raw_data.get('track_name', raw_data.get('race', 'Unknown')),
            session_type=raw_data.get('session_type', raw_data.get('session', 'FP2')),
            year=raw_data.get('year', 2025)
        )
        
        # Parse degradation data
        if 'degradation' in raw_data:
            for compound, deg_info in raw_data['degradation'].items():
                if isinstance(deg_info, dict):
                    data.degradation[compound.upper()] = DegradationData(
                        compound=compound.upper(),
                        deg_per_lap=deg_info.get('deg_per_lap', 0.080),
                        sample_laps=deg_info.get('sample_laps', 0),
                        confidence=deg_info.get('confidence', 1.0),
                        driver_samples=deg_info.get('driver_samples', []),
                        min_deg=deg_info.get('min_deg', 0),
                        max_deg=deg_info.get('max_deg', 0),
                    )
                elif isinstance(deg_info, (int, float)):
                    data.degradation[compound.upper()] = DegradationData(
                        compound=compound.upper(),
                        deg_per_lap=float(deg_info)
                    )
        
        data.base_lap_time = raw_data.get('base_lap_time')
        data.base_lap_time_method = raw_data.get('base_lap_time_method', 'estimated')
        data.fuel_kg_per_lap = raw_data.get('fuel_kg_per_lap')
        data.fuel_effect = raw_data.get('fuel_effect')
        data.compound_deltas = raw_data.get('compound_deltas', {})
        data.track_evolution_per_lap = raw_data.get('track_evolution_per_lap', 0)
        data.stints_analyzed = raw_data.get('stints_analyzed', 0)
        data.drivers_analyzed = raw_data.get('drivers_analyzed', 0)
        
        self._loaded_data = data
        return data
    
    def save_to_json(self, data: LongRunData, output_path: Path = None) -> Path:
        """Save Long Run data to JSON file."""
        if output_path is None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            filename = f"long_run_{data.year}_{data.track_name}_{data.session_type}.json"
            output_path = self.cache_dir / filename
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data.to_dict(), f, indent=2, ensure_ascii=False)
        
        print(f"[LONGRUN_LOADER] Saved to: {output_path}")
        return output_path
    
    def create_manual_data(
        self,
        track_name: str,
        soft_deg: float = 0.120,
        medium_deg: float = 0.080,
        hard_deg: float = 0.045,
        soft_delta: float = -0.8,
        hard_delta: float = 0.5,
        base_lap_time: float = 90.0,
        session_type: str = "Manual",
        year: int = 2025
    ) -> LongRunData:
        """Create Long Run data from manual input."""
        data = LongRunData(
            track_name=track_name,
            session_type=session_type,
            year=year,
            base_lap_time=base_lap_time
        )
        
        data.degradation = {
            'SOFT': DegradationData(compound='SOFT', deg_per_lap=soft_deg),
            'MEDIUM': DegradationData(compound='MEDIUM', deg_per_lap=medium_deg),
            'HARD': DegradationData(compound='HARD', deg_per_lap=hard_deg),
        }
        
        data.compound_deltas = {
            'SOFT': soft_delta,
            'MEDIUM': 0.0,
            'HARD': hard_delta,
        }
        
        self._loaded_data = data
        return data
    
    def build_from_calculator(self, calculator: LongRunCalculator) -> LongRunData:
        """Build LongRunData from an existing calculator instance."""
        results = calculator.get_results()
        aggregated = calculator.aggregate_results()
        
        driver_results: Dict[str, List[DriverDegradationResult]] = {}
        for result in results:
            if result.driver_code not in driver_results:
                driver_results[result.driver_code] = []
            driver_results[result.driver_code].append(result)
        
        compound_deltas = self._calculate_compound_deltas(results)
        
        data = LongRunData(
            track_name="Unknown",
            session_type="FP2",
            year=2025,
            degradation=aggregated,
            driver_results=driver_results,
            compound_deltas=compound_deltas,
            track_evolution_per_lap=calculator._track_evolution_per_lap,
            stints_analyzed=len(results),
            drivers_analyzed=len(driver_results),
        )
        
        self._loaded_data = data
        return data
    
    @property
    def calculator(self) -> LongRunCalculator:
        """Get the underlying calculator instance."""
        return self._calculator
    
    @property
    def loaded_data(self) -> Optional[LongRunData]:
        """Get currently loaded data."""
        return self._loaded_data


__all__ = [
    'LapData', 'StintInfo', 'DriverFuelSettings', 'DriverDegradationResult',
    'DegradationData', 'LongRunData', 'LongRunCalculator', 'LongRunLoader'
]
