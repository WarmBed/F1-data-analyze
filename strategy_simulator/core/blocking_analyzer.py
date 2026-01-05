#!/usr/bin/env python3
"""
Blocking Analysis Module for Strategy Simulator

Calculates per-lap time loss due to slower cars ahead based on:
1. FP2 Long Run pace data (actual race pace indicator)
2. Predicted qualifying positions (grid order)
3. Track overtaking difficulty
4. Speed differential between drivers

Author: F1T Team
Date: 2025-01-02
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import statistics


@dataclass
class DriverPaceInfo:
    """Driver pace information for blocking analysis"""
    driver_code: str
    team: str
    predicted_position: int  # Predicted Q position (grid)
    fp2_time: float  # FP2 best lap time (single lap pace)
    predicted_q_time: float  # Predicted Q time
    # Long Run pace (if available, more accurate for race)
    long_run_pace: Optional[float] = None
    long_run_compound: Optional[str] = None
    
    @property
    def race_pace(self) -> float:
        """Get estimated race pace (prefer Long Run if available)"""
        if self.long_run_pace:
            return self.long_run_pace
        # Estimate race pace from FP2: typically 1.5-2.5s slower than Q pace
        return self.fp2_time + 0.5  # Conservative estimate
    
    def pace_delta_vs(self, other: 'DriverPaceInfo') -> float:
        """
        Calculate pace delta vs another driver.
        Positive = self is slower, negative = self is faster
        """
        return self.race_pace - other.race_pace


@dataclass
class BlockingScenario:
    """Blocking scenario analysis result"""
    driver_code: str
    starting_position: int
    drivers_ahead: List[DriverPaceInfo]
    
    # Calculated values
    total_blocking_time: float = 0.0  # Total estimated time loss
    blocking_per_lap: float = 0.0  # Average time loss per lap
    critical_positions: List[int] = field(default_factory=list)  # Positions causing most blocking
    
    # Strategy recommendations
    recommended_stop_lap: Optional[int] = None
    undercut_potential: float = 0.0  # Seconds that can be gained by undercut
    overcut_potential: float = 0.0  # Seconds that can be gained by overcut
    
    # Risk assessment
    stuck_probability: float = 0.0  # Probability of being stuck behind slower cars
    position_improvement_potential: int = 0  # Expected positions gained from strategy
    
    def to_dict(self) -> dict:
        return {
            'driver': self.driver_code,
            'starting_position': self.starting_position,
            'drivers_ahead_count': len(self.drivers_ahead),
            'total_blocking_time': round(self.total_blocking_time, 2),
            'blocking_per_lap': round(self.blocking_per_lap, 3),
            'critical_positions': self.critical_positions,
            'recommended_stop_lap': self.recommended_stop_lap,
            'undercut_potential': round(self.undercut_potential, 2),
            'overcut_potential': round(self.overcut_potential, 2),
            'stuck_probability': round(self.stuck_probability, 2),
            'position_improvement_potential': self.position_improvement_potential,
        }


class BlockingAnalyzer:
    """
    Analyzes blocking scenarios and recommends strategies.
    
    Uses FP2 Long Run data and predicted grid order to calculate:
    - Per-lap time loss when stuck behind slower cars
    - Optimal pit stop windows to avoid traffic
    - Position improvement potential through strategy
    """
    
    # Constants
    DRS_EFFECT_SECONDS = 0.3  # Typical DRS advantage per lap
    OVERTAKE_ATTEMPT_SUCCESS_RATE = 0.4  # Base success rate per attempt
    DIRTY_AIR_LOSS_SECONDS = 0.3  # Time loss per lap in dirty air within 1s
    
    def __init__(
        self,
        overtaking_difficulty: float = 0.5,  # 0.0 = easy (Monza), 1.0 = hard (Monaco)
        race_laps: int = 53,
        pit_loss_green: float = 22.0,
        traffic_decay_rate: float = 0.04,  # How quickly traffic spreads out
    ):
        """
        Initialize blocking analyzer.
        
        Args:
            overtaking_difficulty: Track difficulty (0-1, higher = harder)
            race_laps: Total race laps
            pit_loss_green: Pit stop time loss under green flag
            traffic_decay_rate: How quickly traffic effect decays per lap
        """
        self.overtaking_difficulty = overtaking_difficulty
        self.race_laps = race_laps
        self.pit_loss_green = pit_loss_green
        self.traffic_decay_rate = traffic_decay_rate
        
        # All drivers' pace info
        self._driver_paces: Dict[str, DriverPaceInfo] = {}
        
    def set_driver_paces(self, paces: Dict[str, DriverPaceInfo]):
        """Set all driver pace information."""
        self._driver_paces = paces
        
    def load_from_fp2_prediction(
        self, 
        predictions: List[Dict[str, Any]],
        long_run_data: Optional[Dict[str, Any]] = None
    ):
        """
        Load driver pace data from FP2->Q prediction.
        
        Args:
            predictions: List of prediction dicts from FP2->Q JSON
            long_run_data: Optional Long Run data for more accurate pace
        """
        self._driver_paces.clear()
        
        for pred in predictions:
            driver_code = pred.get('driver', '')
            if not driver_code:
                continue
                
            pace_info = DriverPaceInfo(
                driver_code=driver_code,
                team=pred.get('team', ''),
                predicted_position=pred.get('rank', 20),
                fp2_time=pred.get('fp2_time', 0.0),
                predicted_q_time=pred.get('predicted_time', 0.0),
            )
            
            # Try to get Long Run pace from long_run_data
            if long_run_data:
                driver_lr = long_run_data.get('driver_results', {}).get(driver_code)
                if driver_lr and len(driver_lr) > 0:
                    # Get average pace from Long Run stints
                    lr_paces = [r.get('avg_lap_time', 0) for r in driver_lr 
                               if r.get('avg_lap_time', 0) > 0]
                    if lr_paces:
                        pace_info.long_run_pace = statistics.mean(lr_paces)
                        pace_info.long_run_compound = driver_lr[0].get('compound', 'MEDIUM')
                        
            self._driver_paces[driver_code] = pace_info
            
        print(f"[BLOCKING] Loaded {len(self._driver_paces)} drivers from FP2 prediction")
        
    def analyze_driver(
        self, 
        driver_code: str,
        starting_position: Optional[int] = None
    ) -> Optional[BlockingScenario]:
        """
        Analyze blocking scenario for a specific driver.
        
        Args:
            driver_code: Driver to analyze
            starting_position: Override starting position (default: use predicted)
            
        Returns:
            BlockingScenario with analysis results
        """
        if driver_code not in self._driver_paces:
            print(f"[BLOCKING] Driver {driver_code} not found in pace data")
            return None
            
        target = self._driver_paces[driver_code]
        position = starting_position or target.predicted_position
        
        # Get drivers ahead
        drivers_ahead = []
        for code, pace in self._driver_paces.items():
            if code == driver_code:
                continue
            if pace.predicted_position < position:
                drivers_ahead.append(pace)
                
        # Sort by position (P1 first)
        drivers_ahead.sort(key=lambda x: x.predicted_position)
        
        scenario = BlockingScenario(
            driver_code=driver_code,
            starting_position=position,
            drivers_ahead=drivers_ahead,
        )
        
        # Calculate blocking
        self._calculate_blocking_time(scenario, target)
        self._calculate_strategy_recommendations(scenario, target)
        
        return scenario
    
    def _calculate_blocking_time(
        self, 
        scenario: BlockingScenario,
        target: DriverPaceInfo
    ):
        """Calculate total and per-lap blocking time."""
        if not scenario.drivers_ahead:
            return
            
        target_pace = target.race_pace
        total_blocking = 0.0
        critical_positions = []
        
        # Analyze each driver ahead
        for ahead in scenario.drivers_ahead:
            pace_delta = ahead.race_pace - target_pace  # Positive = ahead is slower
            
            if pace_delta <= 0:
                # Driver ahead is faster or equal, no blocking
                continue
                
            # Calculate laps stuck behind this driver
            # Factor in overtaking difficulty
            overtake_difficulty_factor = 1.0 + self.overtaking_difficulty * 2.0  # 1x - 3x harder
            
            # Estimated laps to overtake = pace_delta * difficulty / DRS advantage
            if pace_delta > 0.5:  # Large pace advantage
                laps_to_overtake = int(pace_delta * overtake_difficulty_factor / self.DRS_EFFECT_SECONDS)
                laps_to_overtake = max(1, min(laps_to_overtake, 10))  # Cap at 10 laps
            else:
                # Small pace delta: may never overtake on hard tracks
                base_laps = pace_delta * 5 * overtake_difficulty_factor
                laps_to_overtake = int(base_laps)
                if self.overtaking_difficulty > 0.7:
                    # Very hard to overtake (Monaco-like)
                    laps_to_overtake = min(self.race_laps // 2, laps_to_overtake * 2)
                    
            # Time lost while stuck
            time_lost = laps_to_overtake * self.DIRTY_AIR_LOSS_SECONDS
            
            # Add pace loss for each lap stuck
            time_lost += pace_delta * laps_to_overtake * 0.5  # Partial pace loss
            
            total_blocking += time_lost
            
            # Track critical positions
            if pace_delta > 0.3:
                critical_positions.append(ahead.predicted_position)
                
        scenario.total_blocking_time = total_blocking
        scenario.blocking_per_lap = total_blocking / self.race_laps if self.race_laps > 0 else 0
        scenario.critical_positions = critical_positions[:3]  # Top 3 most critical
        
        # Calculate stuck probability
        slow_drivers_ahead = sum(1 for a in scenario.drivers_ahead 
                                 if a.race_pace - target.race_pace > 0.2)
        scenario.stuck_probability = min(1.0, slow_drivers_ahead * 0.15 * 
                                         (1 + self.overtaking_difficulty))
        
    def _calculate_strategy_recommendations(
        self,
        scenario: BlockingScenario,
        target: DriverPaceInfo
    ):
        """Calculate strategy recommendations to minimize blocking."""
        if not scenario.drivers_ahead:
            return
            
        # Undercut potential
        # Early stop to jump drivers during their stint
        undercut_positions = []
        for ahead in scenario.drivers_ahead:
            pace_delta = ahead.race_pace - target.race_pace
            if pace_delta > 0.1:  # Can undercut slower drivers
                # Undercut value = pit loss saved by avoiding traffic
                undercut_positions.append(ahead.predicted_position)
                
        if undercut_positions:
            # Each position undercut saves dirty air time
            scenario.undercut_potential = len(undercut_positions) * 1.5
            # Recommend early stop on lap where traffic accumulates
            scenario.recommended_stop_lap = max(8, scenario.starting_position * 2)
            
        # Overcut potential (less common)
        # Stay out when others pit, get clean air
        overcut_time = 0.0
        for ahead in scenario.drivers_ahead:
            if ahead.race_pace - target.race_pace < -0.3:  # Faster driver ahead
                # Overcut = free air when they pit
                overcut_time += 2.0  # Laps of clean air
                
        scenario.overcut_potential = overcut_time
        
        # Position improvement potential
        slow_count = sum(1 for a in scenario.drivers_ahead 
                        if a.race_pace > target.race_pace + 0.2)
        scenario.position_improvement_potential = min(slow_count, 5)
        
    def get_position_forecast(
        self,
        driver_code: str,
        strategy_type: str = "normal"  # "normal", "aggressive", "conservative"
    ) -> Dict[str, Any]:
        """
        Forecast final position based on strategy type.
        
        Args:
            driver_code: Driver to forecast
            strategy_type: Strategy approach
            
        Returns:
            Dict with position forecast and confidence
        """
        scenario = self.analyze_driver(driver_code)
        if not scenario:
            return {'error': 'Driver not found'}
            
        start_pos = scenario.starting_position
        
        if strategy_type == "aggressive":
            # Aggressive: early stops, risk for bigger gains
            expected_gain = scenario.position_improvement_potential
            risk_factor = 0.3  # 30% chance of backfiring
            best_case = start_pos - expected_gain - 2
            worst_case = start_pos + 2
            
        elif strategy_type == "conservative":
            # Conservative: safe strategy, smaller gains
            expected_gain = max(0, scenario.position_improvement_potential - 2)
            risk_factor = 0.1
            best_case = start_pos - expected_gain
            worst_case = start_pos
            
        else:  # normal
            expected_gain = scenario.position_improvement_potential // 2
            risk_factor = 0.2
            best_case = start_pos - expected_gain - 1
            worst_case = start_pos + 1
            
        expected_pos = start_pos - expected_gain
        
        return {
            'driver': driver_code,
            'start_position': start_pos,
            'strategy': strategy_type,
            'expected_finish': max(1, expected_pos),
            'best_case': max(1, best_case),
            'worst_case': min(20, worst_case),
            'position_gain': expected_gain,
            'confidence': 1.0 - risk_factor,
            'blocking_risk': scenario.stuck_probability,
            'recommended_stop': scenario.recommended_stop_lap,
        }
        
    def calculate_traffic_adjusted_params(
        self,
        driver_code: str,
        base_traffic_loss: float = 0.15
    ) -> Dict[str, float]:
        """
        Calculate traffic parameters adjusted for this driver's specific situation.
        
        Args:
            driver_code: Driver to calculate for
            base_traffic_loss: Base traffic loss per position
            
        Returns:
            Dict with adjusted traffic parameters
        """
        scenario = self.analyze_driver(driver_code)
        if not scenario:
            return {
                'traffic_loss_per_position': base_traffic_loss,
                'traffic_decay_rate': self.traffic_decay_rate,
                'additional_first_lap_loss': 0.0,
            }
            
        # Adjust based on drivers ahead analysis
        slow_ratio = scenario.stuck_probability
        
        # If many slow drivers ahead, increase traffic loss
        adjusted_loss = base_traffic_loss * (1.0 + slow_ratio * 0.5)
        
        # High overtaking difficulty = slower decay
        adjusted_decay = self.traffic_decay_rate * (1.0 - self.overtaking_difficulty * 0.5)
        adjusted_decay = max(0.01, adjusted_decay)
        
        # Additional first lap loss for midfield starts
        first_lap_adjustment = 0.0
        if 8 <= scenario.starting_position <= 15:
            first_lap_adjustment = 1.0 + slow_ratio * 2.0  # Midfield chaos
        elif scenario.starting_position > 15:
            first_lap_adjustment = 0.5  # Back of grid, less chaos but more positions
            
        return {
            'traffic_loss_per_position': round(adjusted_loss, 3),
            'traffic_decay_rate': round(adjusted_decay, 4),
            'additional_first_lap_loss': round(first_lap_adjustment, 2),
            'blocking_time_per_lap': round(scenario.blocking_per_lap, 3),
            'total_blocking_time': round(scenario.total_blocking_time, 2),
        }
