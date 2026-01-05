#!/usr/bin/env python3
"""
FP2-Race Long Run Correlation Analyzer (Function 131)

Analyzes correlation between FP2 Long Run simulation laps and actual Race performance.
This module uses EXACTLY the same calculation logic as the GUI Long Run module to ensure consistency.

Core Calculation Logic (Same as GUI long_run_mdi.py):
1. IQR-based outlier filtering for stint detection
2. Fuel correction: fuel_consumed * fuel_effect_coefficient
3. Track evolution: statistical median method
4. Fully-Corrected Lap Times = raw + fuel_correction - track_evolution

Author: F1T Team
Date: 2025-01-01
Version: 1.0.0
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
import statistics

import numpy as np
import pandas as pd

# Use lazy logger import
_logger = None
def _get_logger():
    global _logger
    if _logger is None:
        from core.logger import get_logger
        _logger = get_logger(__name__)
    return _logger


# ============================================================================
# Data Classes - Same structures as GUI long_run_calculator.py
# ============================================================================

@dataclass
class LapData:
    """Single lap data structure"""
    lap_number: int
    lap_time: float  # seconds
    stint: int
    compound: str
    tyre_life: int
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
    confidence: float = 0.0
    
    # IQR filtered data
    filtered_laps: List[int] = field(default_factory=list)
    filtered_times: List[float] = field(default_factory=list)
    outlier_laps: List[int] = field(default_factory=list)


@dataclass
class FuelSettings:
    """Fuel settings for correction calculation"""
    start_fuel_kg: float = 85.0
    fuel_kg_per_lap: float = 1.70
    fuel_effect_coefficient: float = 0.030


@dataclass
class CorrelationResult:
    """FP2-Race correlation result for a driver"""
    driver_code: str
    team: str
    compound: str
    
    # FP2 Analysis
    fp2_stint_laps: List[int] = field(default_factory=list)
    fp2_raw_times: List[float] = field(default_factory=list)
    fp2_corrected_times: List[float] = field(default_factory=list)
    fp2_degradation_per_lap: float = 0.0
    fp2_avg_pace: float = 0.0
    
    # Race Analysis
    race_estimated_laps: List[int] = field(default_factory=list)
    race_raw_times: List[float] = field(default_factory=list)
    race_corrected_times: List[float] = field(default_factory=list)
    race_degradation_per_lap: float = 0.0
    race_avg_pace: float = 0.0
    
    # Correlation
    fp2_to_race_lap_offset: int = 0  # FP2 lap 1 = Race lap X
    pace_delta: float = 0.0  # Race pace - FP2 pace
    degradation_delta: float = 0.0  # Race deg - FP2 deg
    correlation_score: float = 0.0  # 0-1, how well FP2 predicted race


# ============================================================================
# Core Calculation Engine - EXACTLY matches GUI long_run_mdi.py
# ============================================================================

class FP2RaceCorrelationAnalyzer:
    """
    FP2-Race Long Run Correlation Analyzer
    
    Uses EXACTLY the same calculation logic as GUI Long Run module:
    1. IQR-based outlier filtering (1.5 * IQR rule)
    2. Fuel correction: fuel_consumed * fuel_effect_coefficient
    3. Track evolution: statistical median method
    4. Fully-Corrected Lap Times = raw + fuel_correction - track_evolution
    """
    
    # Detection thresholds - same as GUI
    MIN_CONSECUTIVE_LAPS = 4
    MAX_LAP_TIME_STDDEV = 2.0
    OUTLAP_TIME_THRESHOLD = 5.0
    
    def __init__(self):
        self._fp2_laps: Dict[str, List[LapData]] = {}
        self._race_laps: Dict[str, List[LapData]] = {}
        self._fuel_settings: FuelSettings = FuelSettings()
        self._track_evolution_fp2: Dict[int, float] = {}
        self._track_evolution_race: Dict[int, float] = {}
        
    def set_fuel_settings(self, 
                          start_fuel: float = 85.0, 
                          consumption: float = 1.70, 
                          effect: float = 0.030):
        """Set fuel correction parameters"""
        self._fuel_settings = FuelSettings(
            start_fuel_kg=start_fuel,
            fuel_kg_per_lap=consumption,
            fuel_effect_coefficient=effect
        )
        
    def load_session_data(self, api_data: Dict, session_type: str) -> bool:
        """
        Load lap data from Function 28 API response
        
        Args:
            api_data: API response containing lap data
            session_type: "FP2" or "R"
        
        Returns:
            True if data loaded successfully
        """
        target = self._fp2_laps if session_type == "FP2" else self._race_laps
        target.clear()
        
        try:
            # Handle various API response formats
            if 'data' in api_data:
                data = api_data['data']
            else:
                data = api_data
            
            # Format 1: 'drivers' dict with driver data
            if 'drivers' in data:
                drivers_data = data['drivers']
                for driver_code, driver_info in drivers_data.items():
                    laps = self._parse_driver_laps(driver_code, driver_info)
                    if laps:
                        target[driver_code] = laps
            
            print(f"[F131] Loaded {session_type} data for {len(target)} drivers")
            return len(target) > 0
            
        except Exception as e:
            print(f"[F131] Failed to load {session_type} data: {e}")
            return False
    
    def _parse_driver_laps(self, driver_code: str, driver_info: Dict) -> List[LapData]:
        """Parse laps for a single driver"""
        laps = []
        
        laps_data = driver_info.get('laps', driver_info.get('lap_times', []))
        
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
            
            # Check for NaN values first
            if pd.isna(lap_time) or pd.isna(lap_number):
                return None
            
            # Convert lap time if in timedelta format or string
            if isinstance(lap_time, str):
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
                is_pit_in=bool(lap_entry.get('PitInTime', lap_entry.get('pit_in', False))),
                is_pit_out=bool(lap_entry.get('PitOutTime', lap_entry.get('pit_out', False))),
                is_valid=lap_entry.get('IsAccurate', lap_entry.get('is_valid', True)),
                driver_code=driver_code
            )
        except Exception as e:
            print(f"[F131] WARNING: Failed to parse lap: {e}")
            return None
    
    # ========================================================================
    # IQR Filtering - EXACTLY matches GUI _filter_outliers_iqr()
    # ========================================================================
    
    def _filter_outliers_iqr(self, times: List[float], laps: List[int]) -> Tuple[List[float], List[int], List[int]]:
        """
        Filter outliers using IQR method
        
        EXACTLY matches GUI long_run_mdi.py _filter_outliers_iqr()
        
        Args:
            times: List of lap times in seconds
            laps: Corresponding list of lap numbers
            
        Returns:
            Tuple of (filtered_times, filtered_laps, outlier_laps)
        """
        if len(times) < 4:
            return times, laps, []
        
        times_array = np.array(times)
        
        q1 = np.percentile(times_array, 25)
        q3 = np.percentile(times_array, 75)
        iqr = q3 - q1
        
        # Use 1.5 * IQR rule for outlier detection
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Set minimum threshold to avoid rejecting gradual degradation
        median = np.median(times_array)
        lower_bound = max(lower_bound, median - 5.0)  # At least 5s slower than median
        upper_bound = max(upper_bound, median + 10.0)  # At least 10s faster than median
        
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
    
    # ========================================================================
    # Stint Detection - Similar to GUI _finalize_stint()
    # ========================================================================
    
    def detect_long_runs(self, session_type: str, min_laps: int = None) -> Dict[str, List[StintInfo]]:
        """
        Detect Long Run stints for all drivers
        
        Args:
            session_type: "FP2" or "R"
            min_laps: Minimum consecutive laps
            
        Returns:
            Dict of driver_code -> List of StintInfo
        """
        if min_laps is None:
            min_laps = self.MIN_CONSECUTIVE_LAPS
        
        laps_data = self._fp2_laps if session_type == "FP2" else self._race_laps
        all_stints = {}
        
        for driver_code, laps in laps_data.items():
            driver_stints = self._detect_driver_stints(driver_code, laps, min_laps)
            if driver_stints:
                all_stints[driver_code] = driver_stints
        
        return all_stints
    
    def _detect_driver_stints(self, driver_code: str, laps: List[LapData], 
                               min_laps: int) -> List[StintInfo]:
        """Detect stints for a single driver with IQR filtering"""
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
            
            # Get times and lap numbers
            lap_times = [lap.lap_time for lap in valid_laps]
            lap_numbers = [lap.lap_number for lap in valid_laps]
            
            # Apply IQR filtering
            filtered_times, filtered_laps, outlier_laps = self._filter_outliers_iqr(
                lap_times, lap_numbers
            )
            
            if len(filtered_laps) < min_laps:
                continue
            
            # Calculate stability score
            stddev = statistics.stdev(filtered_times) if len(filtered_times) > 1 else 0
            is_long_run = stddev < self.MAX_LAP_TIME_STDDEV
            confidence = max(0, 1 - (stddev / self.MAX_LAP_TIME_STDDEV))
            
            # Get compound
            compound = valid_laps[0].compound if valid_laps else "UNKNOWN"
            
            stint_info = StintInfo(
                driver_code=driver_code,
                stint_number=stint_num,
                start_lap=filtered_laps[0],
                end_lap=filtered_laps[-1],
                lap_count=len(filtered_laps),
                compound=compound,
                is_long_run=is_long_run,
                confidence=confidence,
                filtered_laps=filtered_laps,
                filtered_times=filtered_times,
                outlier_laps=outlier_laps
            )
            stints.append(stint_info)
        
        return stints
    
    # ========================================================================
    # Track Evolution - EXACTLY matches GUI statistical method
    # ========================================================================
    
    def _calculate_track_evolution(self, stints: Dict[str, List[StintInfo]], 
                                    laps_data: Dict[str, List[LapData]]) -> Dict[int, float]:
        """
        Calculate Track Evolution using statistical median method
        
        EXACTLY matches GUI long_run_calculator.py _calculate_track_evolution_statistical()
        """
        lap_times_by_number: Dict[int, List[float]] = {}
        
        for driver_code, driver_stints in stints.items():
            driver_laps = laps_data.get(driver_code, [])
            
            for stint in driver_stints:
                if not stint.is_long_run:
                    continue
                    
                for lap in driver_laps:
                    if stint.start_lap <= lap.lap_number <= stint.end_lap:
                        if lap.is_valid and not lap.is_pit_in and not lap.is_pit_out:
                            if lap.lap_number in stint.filtered_laps:
                                if lap.lap_number not in lap_times_by_number:
                                    lap_times_by_number[lap.lap_number] = []
                                lap_times_by_number[lap.lap_number].append(lap.lap_time)
        
        if not lap_times_by_number:
            return {}
        
        # Calculate median for each lap number
        medians = {}
        for lap_num, times in lap_times_by_number.items():
            medians[lap_num] = statistics.median(times)
        
        # Find baseline
        sorted_laps = sorted(medians.keys())
        if not sorted_laps:
            return {}
        
        baseline = medians[sorted_laps[0]]
        
        # Calculate delta from baseline
        track_evo = {}
        for lap_num in sorted_laps:
            track_evo[lap_num] = medians[lap_num] - baseline
        
        return track_evo
    
    # ========================================================================
    # Fuel Correction - EXACTLY matches GUI fuel correction logic
    # ========================================================================
    
    def _apply_fuel_correction(self, 
                                times: List[float], 
                                laps: List[int],
                                simulate_from_lap: int = 0) -> List[float]:
        """
        Apply fuel correction to lap times
        
        EXACTLY matches GUI long_run_mdi.py fuel correction logic
        
        Args:
            times: Raw lap times
            laps: Lap numbers
            simulate_from_lap: Target race lap for Race Simulation Mode (0 = disabled)
            
        Returns:
            Fuel-corrected lap times
        """
        fuel = self._fuel_settings
        
        if simulate_from_lap > 0:
            # Race Simulation Mode
            target_fuel = fuel.start_fuel_kg - (simulate_from_lap * fuel.fuel_kg_per_lap)
            target_fuel = max(target_fuel, 5.0)
            
            corrections = []
            for i, lap in enumerate(laps):
                current_fuel = fuel.start_fuel_kg - (i * fuel.fuel_kg_per_lap)
                fuel_diff = current_fuel - target_fuel
                correction = -fuel_diff * fuel.fuel_effect_coefficient
                corrections.append(correction)
            
            return [t + c for t, c in zip(times, corrections)]
        else:
            # Original mode: normalize within stint
            corrections = [i * fuel.fuel_kg_per_lap * fuel.fuel_effect_coefficient 
                          for i in range(len(times))]
            return [t + c for t, c in zip(times, corrections)]
    
    def _apply_track_evolution_correction(self, 
                                           times: List[float], 
                                           laps: List[int],
                                           track_evo: Dict[int, float]) -> List[float]:
        """
        Apply track evolution correction to lap times
        
        Args:
            times: Lap times (already fuel-corrected)
            laps: Lap numbers
            track_evo: Track evolution per lap
            
        Returns:
            Fully-corrected lap times (fuel + track evolution)
        """
        if not track_evo:
            return times
        
        # Get per-lap evolution rate
        if len(track_evo) >= 2:
            sorted_laps = sorted(track_evo.keys())
            total_evo = track_evo[sorted_laps[-1]] - track_evo[sorted_laps[0]]
            per_lap_evo = total_evo / (sorted_laps[-1] - sorted_laps[0])
        else:
            per_lap_evo = 0.0
        
        # Apply correction
        corrected = []
        for i, (t, lap) in enumerate(zip(times, laps)):
            track_correction = i * per_lap_evo
            corrected.append(t - track_correction)
        
        return corrected
    
    # ========================================================================
    # Correlation Analysis
    # ========================================================================
    
    def analyze_correlation(self, 
                            fp2_simulate_from_lap: int = 20) -> Dict[str, CorrelationResult]:
        """
        Analyze FP2-Race correlation for all drivers
        
        Args:
            fp2_simulate_from_lap: FP2 lap to simulate as race lap X
            
        Returns:
            Dict of driver_code -> CorrelationResult
        """
        # Detect long runs in both sessions
        fp2_stints = self.detect_long_runs("FP2")
        race_stints = self.detect_long_runs("R")
        
        # Calculate track evolution for both sessions
        self._track_evolution_fp2 = self._calculate_track_evolution(fp2_stints, self._fp2_laps)
        self._track_evolution_race = self._calculate_track_evolution(race_stints, self._race_laps)
        
        results = {}
        
        # Find common drivers
        common_drivers = set(fp2_stints.keys()) & set(race_stints.keys())
        
        for driver in common_drivers:
            fp2_driver_stints = fp2_stints[driver]
            race_driver_stints = race_stints[driver]
            
            # Find matching compound stints
            for fp2_stint in fp2_driver_stints:
                if not fp2_stint.is_long_run:
                    continue
                
                # Find race stint with same compound
                matching_race = None
                for race_stint in race_driver_stints:
                    if race_stint.is_long_run and race_stint.compound == fp2_stint.compound:
                        matching_race = race_stint
                        break
                
                if not matching_race:
                    continue
                
                # Apply corrections
                fp2_fuel_corrected = self._apply_fuel_correction(
                    fp2_stint.filtered_times,
                    fp2_stint.filtered_laps,
                    simulate_from_lap=fp2_simulate_from_lap
                )
                fp2_fully_corrected = self._apply_track_evolution_correction(
                    fp2_fuel_corrected,
                    fp2_stint.filtered_laps,
                    self._track_evolution_fp2
                )
                
                race_fuel_corrected = self._apply_fuel_correction(
                    matching_race.filtered_times,
                    matching_race.filtered_laps,
                    simulate_from_lap=0  # Race uses actual fuel levels
                )
                race_fully_corrected = self._apply_track_evolution_correction(
                    race_fuel_corrected,
                    matching_race.filtered_laps,
                    self._track_evolution_race
                )
                
                # Calculate degradation per lap
                fp2_deg = self._calculate_degradation_rate(fp2_fully_corrected)
                race_deg = self._calculate_degradation_rate(race_fully_corrected)
                
                # Calculate average pace
                fp2_avg = statistics.mean(fp2_fully_corrected) if fp2_fully_corrected else 0
                race_avg = statistics.mean(race_fully_corrected) if race_fully_corrected else 0
                
                # Correlation result
                result = CorrelationResult(
                    driver_code=driver,
                    team=self._get_driver_team(driver),
                    compound=fp2_stint.compound,
                    fp2_stint_laps=fp2_stint.filtered_laps,
                    fp2_raw_times=fp2_stint.filtered_times,
                    fp2_corrected_times=fp2_fully_corrected,
                    fp2_degradation_per_lap=fp2_deg,
                    fp2_avg_pace=fp2_avg,
                    race_estimated_laps=matching_race.filtered_laps,
                    race_raw_times=matching_race.filtered_times,
                    race_corrected_times=race_fully_corrected,
                    race_degradation_per_lap=race_deg,
                    race_avg_pace=race_avg,
                    fp2_to_race_lap_offset=fp2_simulate_from_lap,
                    pace_delta=race_avg - fp2_avg,
                    degradation_delta=race_deg - fp2_deg,
                    correlation_score=self._calculate_correlation_score(
                        fp2_deg, race_deg, fp2_avg, race_avg
                    )
                )
                
                key = f"{driver}_{fp2_stint.compound}"
                results[key] = result
        
        return results
    
    def _calculate_degradation_rate(self, corrected_times: List[float]) -> float:
        """Calculate degradation rate using linear regression"""
        if len(corrected_times) < 2:
            return 0.0
        
        x = np.arange(len(corrected_times))
        y = np.array(corrected_times)
        
        # Simple linear regression
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_xx = np.sum(x * x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x + 1e-10)
        return slope
    
    def _calculate_correlation_score(self, fp2_deg: float, race_deg: float,
                                       fp2_pace: float, race_pace: float) -> float:
        """Calculate correlation score (0-1)"""
        # Degradation similarity (closer = better)
        deg_diff = abs(fp2_deg - race_deg)
        deg_score = max(0, 1 - deg_diff / 0.1)  # 0.1s/lap = 0 score
        
        # Pace similarity (closer = better)
        pace_diff = abs(fp2_pace - race_pace)
        pace_score = max(0, 1 - pace_diff / 2.0)  # 2s difference = 0 score
        
        # Combined score (weighted)
        return 0.6 * deg_score + 0.4 * pace_score
    
    def _get_driver_team(self, driver_code: str) -> str:
        """Get team name for driver"""
        # 2025 driver-team mapping
        teams = {
            'VER': 'Red Bull', 'LAW': 'Red Bull',
            'LEC': 'Ferrari', 'HAM': 'Ferrari',
            'NOR': 'McLaren', 'PIA': 'McLaren',
            'RUS': 'Mercedes', 'ANT': 'Mercedes',
            'ALO': 'Aston Martin', 'STR': 'Aston Martin',
            'GAS': 'Alpine', 'DOO': 'Alpine',
            'TSU': 'Racing Bulls', 'HAD': 'Racing Bulls',
            'ALB': 'Williams', 'SAI': 'Williams',
            'HUL': 'Sauber', 'BOR': 'Sauber',
            'OCO': 'Haas', 'BEA': 'Haas',
        }
        return teams.get(driver_code, 'Unknown')


# ============================================================================
# JSON Export
# ============================================================================

def export_correlation_results(results: Dict[str, CorrelationResult], 
                                year: int, race: str,
                                output_dir: str = "json") -> str:
    """
    Export correlation results to JSON
    
    Args:
        results: Dict of driver_compound -> CorrelationResult
        year: Season year
        race: Race name
        output_dir: Output directory
        
    Returns:
        Path to saved JSON file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    output = {
        "metadata": {
            "year": year,
            "race": race,
            "analysis_type": "fp2_race_long_run_correlation",
            "generated_at": datetime.now().isoformat(),
            "calculation_method": {
                "iqr_filtering": True,
                "fuel_correction": True,
                "track_evolution": "statistical_median",
                "fully_corrected_times": True
            }
        },
        "correlations": {}
    }
    
    for key, result in results.items():
        output["correlations"][key] = asdict(result)
    
    # Calculate team summaries
    team_stats = {}
    for key, result in results.items():
        team = result.team
        if team not in team_stats:
            team_stats[team] = {
                "drivers": [],
                "avg_pace_delta": [],
                "avg_deg_delta": [],
                "avg_correlation": []
            }
        team_stats[team]["drivers"].append(result.driver_code)
        team_stats[team]["avg_pace_delta"].append(result.pace_delta)
        team_stats[team]["avg_deg_delta"].append(result.degradation_delta)
        team_stats[team]["avg_correlation"].append(result.correlation_score)
    
    # Aggregate team stats
    for team, stats in team_stats.items():
        stats["avg_pace_delta"] = statistics.mean(stats["avg_pace_delta"]) if stats["avg_pace_delta"] else 0
        stats["avg_deg_delta"] = statistics.mean(stats["avg_deg_delta"]) if stats["avg_deg_delta"] else 0
        stats["avg_correlation"] = statistics.mean(stats["avg_correlation"]) if stats["avg_correlation"] else 0
    
    output["team_summary"] = team_stats
    
    # Save file
    filename = f"fp2_race_correlation_{year}_{race.replace(' ', '_')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"[F131] Saved correlation results to: {filepath}")
    return filepath


# ============================================================================
# Main Entry Point for CLI
# ============================================================================

def run_fp2_race_correlation_analysis(year: int, race: str, 
                                       fp2_simulate_lap: int = 20,
                                       fuel_start: float = 85.0,
                                       fuel_consumption: float = 1.70,
                                       fuel_effect: float = 0.030,
                                       save_json: bool = True) -> Dict[str, Any]:
    """
    Run FP2-Race Long Run correlation analysis
    
    Args:
        year: Season year
        race: Race name
        fp2_simulate_lap: FP2 lap to simulate as race lap X
        fuel_start: Race start fuel (kg)
        fuel_consumption: Fuel per lap (kg)
        fuel_effect: Fuel effect coefficient (s/kg)
        save_json: Whether to save JSON output
        
    Returns:
        Analysis results dict
    """
    print(f"\n[F131] FP2-Race Long Run Correlation Analysis")
    print(f"  Year: {year}")
    print(f"  Race: {race}")
    print(f"  FP2 Simulate Lap: {fp2_simulate_lap}")
    print(f"  Fuel Settings: {fuel_start}kg start, {fuel_consumption}kg/lap, {fuel_effect}s/kg effect")
    
    try:
        import fastf1
        
        # Enable cache
        cache_dir = "./cache"
        fastf1.Cache.enable_cache(cache_dir)
        print(f"[F131] FastF1 cache enabled: {cache_dir}")
        
        # Initialize analyzer
        analyzer = FP2RaceCorrelationAnalyzer()
        analyzer.set_fuel_settings(fuel_start, fuel_consumption, fuel_effect)
        
        # Load FP2 data
        print(f"\n[F131] Loading FP2 session data...")
        try:
            fp2_session = fastf1.get_session(year, race, "FP2")
            fp2_session.load()
            
            if fp2_session.laps is None or fp2_session.laps.empty:
                return {"success": False, "message": "No FP2 lap data available"}
            
            fp2_data = _convert_fastf1_laps_to_api_format(fp2_session)
            print(f"[F131] FP2 data loaded: {len(fp2_data.get('drivers', {}))} drivers")
        except Exception as e:
            return {"success": False, "message": f"Failed to load FP2 data: {e}"}
        
        # Load Race data
        print(f"[F131] Loading Race session data...")
        try:
            race_session = fastf1.get_session(year, race, "R")
            race_session.load()
            
            if race_session.laps is None or race_session.laps.empty:
                return {"success": False, "message": "No Race lap data available"}
            
            race_data = _convert_fastf1_laps_to_api_format(race_session)
            print(f"[F131] Race data loaded: {len(race_data.get('drivers', {}))} drivers")
        except Exception as e:
            return {"success": False, "message": f"Failed to load Race data: {e}"}
        
        # Load data into analyzer
        print("[F131] Parsing FP2 data into analyzer...")
        if not analyzer.load_session_data(fp2_data, "FP2"):
            return {"success": False, "message": "Failed to parse FP2 data"}
        print(f"[F131] FP2 data parsed: {len(analyzer._fp2_laps)} drivers")
        
        print("[F131] Parsing Race data into analyzer...")
        if not analyzer.load_session_data(race_data, "R"):
            return {"success": False, "message": "Failed to parse Race data"}
        print(f"[F131] Race data parsed: {len(analyzer._race_laps)} drivers")
        
        # Run correlation analysis
        print("[F131] Running correlation analysis...")
        results = analyzer.analyze_correlation(fp2_simulate_lap)
        print(f"[F131] Correlation analysis complete: {len(results)} results")
        
        if not results:
            return {
                "success": False,
                "message": "No matching Long Run stints found between FP2 and Race"
            }
        
        # Export to JSON
        json_path = None
        if save_json:
            json_path = export_correlation_results(results, year, race)
        
        return {
            "success": True,
            "message": f"FP2-Race correlation analysis completed for {len(results)} driver-compound combinations",
            "year": year,
            "race": race,
            "correlation_count": len(results),
            "json_path": json_path,
            "data": {key: asdict(val) for key, val in results.items()}
        }
        
    except Exception as e:
        print(f"[F131] ERROR: Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Analysis failed: {e}"
        }


def _convert_fastf1_laps_to_api_format(session) -> Dict[str, Any]:
    """
    Convert FastF1 session laps to API-compatible format
    
    Args:
        session: FastF1 Session object with loaded laps
        
    Returns:
        Dict in API format with 'drivers' key
    """
    laps = session.laps
    
    result = {"drivers": {}}
    
    for driver_code in laps['Driver'].unique():
        driver_laps = laps[laps['Driver'] == driver_code]
        
        driver_data = {"laps": []}
        
        for _, lap in driver_laps.iterrows():
            # Convert lap time
            lap_time = lap['LapTime']
            if hasattr(lap_time, 'total_seconds'):
                lap_time_sec = lap_time.total_seconds()
            elif isinstance(lap_time, (int, float)):
                lap_time_sec = float(lap_time)
            else:
                continue  # Skip invalid lap times
            
            if lap_time_sec <= 0 or lap_time_sec > 300:  # Skip invalid times
                continue
            
            lap_entry = {
                "LapNumber": int(lap['LapNumber']) if not pd.isna(lap['LapNumber']) else 0,
                "LapTime": lap_time_sec,
                "Stint": int(lap['Stint']) if not pd.isna(lap['Stint']) else 1,
                "Compound": str(lap['Compound']).upper() if not pd.isna(lap['Compound']) else "UNKNOWN",
                "TyreLife": int(lap['TyreLife']) if not pd.isna(lap['TyreLife']) else 1,
                "PitInTime": lap['PitInTime'] if not pd.isna(lap['PitInTime']) else None,
                "PitOutTime": lap['PitOutTime'] if not pd.isna(lap['PitOutTime']) else None,
                "IsAccurate": bool(lap['IsAccurate']) if not pd.isna(lap['IsAccurate']) else True
            }
            
            driver_data["laps"].append(lap_entry)
        
        if driver_data["laps"]:
            result["drivers"][driver_code] = driver_data
    
    return result
