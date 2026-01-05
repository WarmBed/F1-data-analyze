#!/usr/bin/env python3
"""
Competitive Strategy Optimizer

Optimizes strategy considering all 20 drivers on track.
Uses FP2->Q predictions for grid positions and Long Run data for pace.

Key Features:
1. Position-aware strategy optimization
2. Undercut/Overcut analysis vs opponents
3. Traffic and DRS considerations
4. Race simulation with all drivers

Author: F1T Team
Date: 2025-01-07
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import copy

from strategy_simulator.core.lap_simulator import (
    SimulationParams, Stint, Compound, LapSimulator, StrategySimulationResult
)
from strategy_simulator.core.strategy_optimizer import StrategyOptimizer, StrategyConstraints
from strategy_simulator.core.race_simulator import (
    FullRaceSimulator, FullRaceSimulation, DriverRaceState, RaceResult
)


@dataclass
class DriverPaceProfile:
    """Pace profile for a driver based on FP2 and Long Run data."""
    driver_code: str
    team: str
    grid_position: int
    
    # Base pace (from FP2->Q prediction)
    base_pace: float  # seconds per lap (race pace, not quali)
    
    # Degradation rates per compound (from Long Run)
    deg_soft: float = 0.120
    deg_medium: float = 0.080
    deg_hard: float = 0.045
    
    # Predicted strategy
    predicted_stops: int = 1
    predicted_tire_sequence: List[str] = field(default_factory=lambda: ['M', 'H'])
    
    def get_deg_rate(self, compound: Compound) -> float:
        """Get degradation rate for compound."""
        return {
            Compound.SOFT: self.deg_soft,
            Compound.MEDIUM: self.deg_medium,
            Compound.HARD: self.deg_hard,
        }.get(compound, self.deg_medium)


@dataclass
class CompetitiveResult:
    """Result of competitive strategy optimization."""
    # Base strategy result
    strategy_result: StrategySimulationResult
    
    # Position predictions
    predicted_finish_position: int
    positions_gained: int
    
    # Race simulation summary
    best_position_achieved: int
    worst_position_during_race: int
    
    # Competitor interactions
    drivers_overtaken: List[str] = field(default_factory=list)
    drivers_lost_to: List[str] = field(default_factory=list)
    
    # Win probability (from Monte Carlo)
    win_probability: float = 0.0
    podium_probability: float = 0.0
    points_probability: float = 0.0
    
    # Pit window analysis
    undercut_opportunities: List[Tuple[str, int]] = field(default_factory=list)  # (driver, lap)
    overcut_risks: List[Tuple[str, int]] = field(default_factory=list)
    
    def __lt__(self, other):
        """Sort by predicted finish position (lower is better)."""
        return self.predicted_finish_position < other.predicted_finish_position


class CompetitiveStrategyOptimizer:
    """
    Strategy optimizer that considers all 20 drivers.
    
    Workflow:
    1. Load driver pace profiles from FP2 predictions and Long Run data
    2. Generate candidate strategies for our driver
    3. For each strategy, simulate full race with all drivers
    4. Rank strategies by predicted finish position (not just lap time)
    
    Example:
        optimizer = CompetitiveStrategyOptimizer(sim_params)
        optimizer.load_driver_data(fp2_predictions, long_run_data, opponent_strategies)
        optimizer.set_our_driver("VER", grid_position=1)
        results = optimizer.optimize(constraints)
        
        # Results sorted by predicted position
        for r in results[:5]:
            print(f"{r.strategy_result.strategy_name}: P{r.predicted_finish_position}")
    """
    
    def __init__(
        self,
        params: SimulationParams,
        sc_probability: float = 0.015,  # Per-lap SC probability
        overtaking_difficulty: float = 0.5,
    ):
        """
        Initialize competitive optimizer.
        
        Args:
            params: Simulation parameters
            sc_probability: SC probability per lap
            overtaking_difficulty: 0 = easy to overtake, 1 = hard
        """
        self.params = params
        self.sc_probability = sc_probability
        self.overtaking_difficulty = overtaking_difficulty
        
        # Driver data
        self._driver_profiles: Dict[str, DriverPaceProfile] = {}
        self._opponent_strategies: Dict[str, List[str]] = {}  # driver -> tire sequence
        
        # Our driver
        self._our_driver: Optional[str] = None
        self._our_grid_position: int = 10
        
        # Base optimizer for strategy generation
        self._base_optimizer = StrategyOptimizer(params)
        
    def load_driver_data(
        self,
        fp2_predictions: List[Dict],
        long_run_data: Optional[Dict] = None,
        opponent_strategies: Optional[Dict[str, Dict]] = None,
    ):
        """
        Load all driver data for competitive simulation.
        
        Args:
            fp2_predictions: FP2->Q prediction list (20 drivers)
            long_run_data: Long Run degradation data
            opponent_strategies: Opponent strategy settings from UI
        """
        self._driver_profiles.clear()
        self._opponent_strategies.clear()
        
        # Default degradation rates
        default_deg = {'SOFT': 0.120, 'MEDIUM': 0.080, 'HARD': 0.045}
        
        for pred in fp2_predictions:
            driver_code = pred.get('driver', '')
            if not driver_code:
                continue
            
            # Grid position from prediction rank
            grid_pos = pred.get('rank', 20)
            
            # Base pace estimation
            # FP2 predicted Q time + race delta (typically 1.5-2.5s slower)
            predicted_q_time = pred.get('predicted_time', 90.0)
            base_race_pace = predicted_q_time + 2.0
            
            # Get degradation from Long Run data if available
            deg_soft = default_deg['SOFT']
            deg_medium = default_deg['MEDIUM']
            deg_hard = default_deg['HARD']
            
            if long_run_data:
                # Try to get driver-specific degradation
                driver_results = long_run_data.get('driver_results', {}).get(driver_code, [])
                for result in driver_results:
                    compound = result.get('compound', '').upper()
                    deg = result.get('deg_per_lap', result.get('degradation', 0))
                    if compound == 'SOFT':
                        deg_soft = abs(deg)
                    elif compound == 'MEDIUM':
                        deg_medium = abs(deg)
                    elif compound == 'HARD':
                        deg_hard = abs(deg)
            
            # Get predicted strategy
            tire_sequence = ['M', 'H']  # Default 1-stop M-H
            if opponent_strategies and driver_code in opponent_strategies:
                tire_sequence = opponent_strategies[driver_code].get('tire_sequence', ['M', 'H'])
            
            profile = DriverPaceProfile(
                driver_code=driver_code,
                team=pred.get('team', ''),
                grid_position=grid_pos,
                base_pace=base_race_pace,
                deg_soft=deg_soft,
                deg_medium=deg_medium,
                deg_hard=deg_hard,
                predicted_stops=len(tire_sequence) - 1,
                predicted_tire_sequence=tire_sequence,
            )
            
            self._driver_profiles[driver_code] = profile
            self._opponent_strategies[driver_code] = tire_sequence
        
        print(f"[COMPETITIVE] Loaded {len(self._driver_profiles)} driver profiles")
        
    def set_our_driver(self, driver_code: str, grid_position: Optional[int] = None):
        """
        Set which driver we are optimizing for.
        
        Args:
            driver_code: Our driver code
            grid_position: Override grid position (uses FP2 prediction if None)
        """
        self._our_driver = driver_code
        
        if grid_position is not None:
            self._our_grid_position = grid_position
        elif driver_code in self._driver_profiles:
            self._our_grid_position = self._driver_profiles[driver_code].grid_position
        else:
            self._our_grid_position = 10  # Default mid-grid
            
        print(f"[COMPETITIVE] Our driver: {driver_code} starting P{self._our_grid_position}")
    
    def optimize(
        self,
        constraints: Optional[StrategyConstraints] = None,
        top_n: int = 10,
        simulation_iterations: int = 50,
    ) -> List[CompetitiveResult]:
        """
        Find optimal strategies considering all competitors.
        
        Args:
            constraints: Strategy constraints
            top_n: Number of top strategies to return
            simulation_iterations: Number of race simulations per strategy
            
        Returns:
            List of CompetitiveResult sorted by predicted position
        """
        if not self._our_driver:
            raise ValueError("Must call set_our_driver() before optimize()")
        
        if not self._driver_profiles:
            raise ValueError("Must call load_driver_data() before optimize()")
        
        # Step 1: Generate candidate strategies using base optimizer
        print(f"[COMPETITIVE] Generating strategies...")
        base_results = self._base_optimizer.find_optimal_strategies(
            constraints, top_n=top_n * 2  # Generate more, will filter
        )
        
        if not base_results:
            print("[COMPETITIVE] No valid strategies found")
            return []
        
        print(f"[COMPETITIVE] Evaluating {len(base_results)} strategies with race simulation...")
        
        # Step 2: Evaluate each strategy with full race simulation
        competitive_results = []
        
        for i, strategy_result in enumerate(base_results):
            if i % 5 == 0:
                print(f"[COMPETITIVE] Evaluating strategy {i+1}/{len(base_results)}")
            
            comp_result = self._evaluate_strategy(
                strategy_result,
                iterations=simulation_iterations
            )
            competitive_results.append(comp_result)
        
        # Step 3: Sort by predicted finish position
        competitive_results.sort(key=lambda r: (
            r.predicted_finish_position,
            -r.positions_gained,
            r.strategy_result.total_time
        ))
        
        print(f"[COMPETITIVE] Top strategy: P{competitive_results[0].predicted_finish_position} "
              f"({competitive_results[0].strategy_result.get_stint_notation()})")
        
        return competitive_results[:top_n]
    
    def _evaluate_strategy(
        self,
        strategy_result: StrategySimulationResult,
        iterations: int = 50,
    ) -> CompetitiveResult:
        """
        Evaluate a strategy by simulating full race.
        
        Args:
            strategy_result: Base strategy to evaluate
            iterations: Number of Monte Carlo iterations
            
        Returns:
            CompetitiveResult with position predictions
        """
        # Create race simulator
        simulator = FullRaceSimulator(
            sim_params=self.params,
            sc_probability=self.sc_probability * self.params.race_laps,  # Per-race probability
            overtaking_difficulty=self.overtaking_difficulty,
        )
        
        # Build FP2 prediction format for simulator
        fp2_format = []
        for code, profile in self._driver_profiles.items():
            fp2_format.append({
                'driver': code,
                'team': profile.team,
                'rank': profile.grid_position,
                'predicted_time': profile.base_pace - 2.0,  # Convert back to Q pace
            })
        
        # Build Long Run format
        long_run_format = {
            'driver_results': {
                code: [{'degradation': profile.deg_medium}]
                for code, profile in self._driver_profiles.items()
            }
        }
        
        simulator.load_drivers(fp2_format, long_run_format)
        
        # Set opponent strategies
        opponent_settings = {}
        for code, tire_seq in self._opponent_strategies.items():
            if code != self._our_driver:
                opponent_settings[code] = {'tire_sequence': tire_seq}
        simulator.set_opponent_strategies(opponent_settings)
        
        # Set our strategy
        simulator.set_our_strategy(self._our_driver, strategy_result.stints)
        
        # Run multiple simulations
        finish_positions = []
        positions_gained_list = []
        best_positions = []
        worst_positions = []
        
        for seed in range(iterations):
            race_result = simulator.simulate_race(seed=seed)
            
            if race_result.our_result:
                finish_positions.append(race_result.our_result.final_position)
                positions_gained_list.append(race_result.our_result.positions_gained)
            
            # Track position range during race
            if race_result.lap_states:
                pos_history = [
                    ls.positions.get(self._our_driver, 20)
                    for ls in race_result.lap_states
                ]
                if pos_history:
                    best_positions.append(min(pos_history))
                    worst_positions.append(max(pos_history))
        
        # Calculate statistics
        if finish_positions:
            avg_position = sum(finish_positions) / len(finish_positions)
            avg_gained = sum(positions_gained_list) / len(positions_gained_list)
            win_prob = sum(1 for p in finish_positions if p == 1) / len(finish_positions)
            podium_prob = sum(1 for p in finish_positions if p <= 3) / len(finish_positions)
            points_prob = sum(1 for p in finish_positions if p <= 10) / len(finish_positions)
            best_pos = min(best_positions) if best_positions else self._our_grid_position
            worst_pos = max(worst_positions) if worst_positions else 20
        else:
            avg_position = self._our_grid_position
            avg_gained = 0
            win_prob = podium_prob = points_prob = 0.0
            best_pos = worst_pos = self._our_grid_position
        
        return CompetitiveResult(
            strategy_result=strategy_result,
            predicted_finish_position=round(avg_position),
            positions_gained=round(avg_gained),
            best_position_achieved=best_pos,
            worst_position_during_race=worst_pos,
            win_probability=win_prob,
            podium_probability=podium_prob,
            points_probability=points_prob,
        )
    
    def analyze_pit_windows(
        self,
        our_strategy: List[Stint],
    ) -> Dict[str, Any]:
        """
        Analyze undercut/overcut opportunities relative to competitors.
        
        Args:
            our_strategy: Our planned strategy
            
        Returns:
            Dict with undercut/overcut analysis
        """
        analysis = {
            'undercut_targets': [],
            'overcut_opportunities': [],
            'pit_overlap_risks': [],
        }
        
        our_pit_laps = [stint.start_lap for stint in our_strategy[1:]]  # Skip first stint
        
        for code, profile in self._driver_profiles.items():
            if code == self._our_driver:
                continue
            
            # Estimate opponent pit laps from their tire sequence
            tire_seq = self._opponent_strategies.get(code, ['M', 'H'])
            opp_pit_laps = self._estimate_pit_laps(tire_seq)
            
            for our_pit in our_pit_laps:
                for opp_pit in opp_pit_laps:
                    lap_diff = our_pit - opp_pit
                    
                    # Undercut: we pit 1-3 laps before opponent
                    if -3 <= lap_diff <= -1:
                        analysis['undercut_targets'].append({
                            'driver': code,
                            'our_pit_lap': our_pit,
                            'their_pit_lap': opp_pit,
                            'advantage': f"Undercut by {-lap_diff} laps"
                        })
                    
                    # Overcut: we pit 1-3 laps after opponent
                    elif 1 <= lap_diff <= 3:
                        analysis['overcut_opportunities'].append({
                            'driver': code,
                            'our_pit_lap': our_pit,
                            'their_pit_lap': opp_pit,
                            'note': f"Overcut by {lap_diff} laps"
                        })
                    
                    # Pit overlap risk
                    elif lap_diff == 0:
                        analysis['pit_overlap_risks'].append({
                            'driver': code,
                            'pit_lap': our_pit,
                            'risk': "Same lap pit stop - possible queue"
                        })
        
        return analysis
    
    def _estimate_pit_laps(self, tire_sequence: List[str]) -> List[int]:
        """Estimate pit stop laps from tire sequence."""
        if len(tire_sequence) <= 1:
            return []
        
        race_laps = self.params.race_laps
        laps_per_stint = race_laps // len(tire_sequence)
        
        pit_laps = []
        current_lap = laps_per_stint
        for i in range(len(tire_sequence) - 1):
            pit_laps.append(current_lap)
            current_lap += laps_per_stint
        
        return pit_laps
    
    def get_driver_profiles(self) -> Dict[str, DriverPaceProfile]:
        """Get all loaded driver profiles."""
        return self._driver_profiles.copy()
