#!/usr/bin/env python3
"""
Competitive Monte Carlo Simulator

Monte Carlo simulation that considers all 20 drivers on track.
Each iteration simulates a full race with position changes.

Key Features:
1. 20-driver competition simulation per iteration
2. Position-based win probability (not just time)
3. Undercut/Overcut success rates
4. SC impact on position changes

Author: F1T Team
Date: 2025-01-04
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import random
import math

from .lap_simulator import SimulationParams, Stint, Compound, StrategySimulationResult
from .race_simulator import FullRaceSimulator, FullRaceSimulation, RaceResult
from .monte_carlo import MonteCarloParams, SafetyCarEvent


@dataclass
class CompetitiveIterationResult:
    """Result of a single competitive Monte Carlo iteration."""
    iteration_id: int
    
    # Our driver's result
    our_driver: str
    our_strategy: str
    finish_position: int
    grid_position: int
    positions_gained: int
    total_time: float
    
    # Race events
    sc_events: List[SafetyCarEvent] = field(default_factory=list)
    
    # Drivers we overtook/lost to
    overtaken: List[str] = field(default_factory=list)
    lost_to: List[str] = field(default_factory=list)
    
    def get_scenario_type(self, race_laps: int) -> str:
        """Classify this iteration by SC timing."""
        if not self.sc_events:
            return "no_sc"
        earliest_sc = min(e.start_lap for e in self.sc_events)
        race_third = race_laps / 3
        if earliest_sc <= race_third:
            return "early_sc"
        elif earliest_sc <= race_third * 2:
            return "mid_sc"
        else:
            return "late_sc"


@dataclass
class CompetitiveStrategySummary:
    """Summary for one strategy across all iterations."""
    strategy_name: str
    strategy_notation: str
    
    # Position statistics
    mean_finish_position: float = 0.0
    best_finish: int = 20
    worst_finish: int = 1
    finish_std: float = 0.0
    
    # Position change
    mean_positions_gained: float = 0.0
    positions_gained_std: float = 0.0
    
    # Win/Podium/Points probability (position-based)
    win_probability: float = 0.0      # P1
    podium_probability: float = 0.0   # P1-P3
    top5_probability: float = 0.0     # P1-P5
    points_probability: float = 0.0   # P1-P10
    
    # SC impact
    wins_with_sc: int = 0
    wins_without_sc: int = 0
    mean_position_with_sc: float = 0.0
    mean_position_without_sc: float = 0.0
    
    # Time statistics (for reference)
    mean_time: float = 0.0
    time_std: float = 0.0
    
    # Position distribution
    position_distribution: Dict[int, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'strategy': self.strategy_name,
            'notation': self.strategy_notation,
            'mean_position': round(self.mean_finish_position, 1),
            'best_finish': self.best_finish,
            'worst_finish': self.worst_finish,
            'mean_gained': round(self.mean_positions_gained, 1),
            'win_probability': round(self.win_probability, 1),
            'podium_probability': round(self.podium_probability, 1),
            'points_probability': round(self.points_probability, 1),
            'wins_with_sc': self.wins_with_sc,
            'wins_without_sc': self.wins_without_sc,
            'mean_time': round(self.mean_time, 3),
            'position_distribution': self.position_distribution,
        }


@dataclass
class CompetitiveMCSummary:
    """Complete Monte Carlo summary with 20-driver competition."""
    iterations: int
    our_driver: str
    grid_position: int
    total_drivers: int
    
    # Per-strategy summaries
    strategy_summaries: Dict[str, CompetitiveStrategySummary] = field(default_factory=dict)
    
    # Best strategy by different metrics
    best_by_position: str = ""      # Lowest mean finish position
    best_by_win_rate: str = ""      # Highest win probability
    best_by_consistency: str = ""   # Lowest position variance
    
    # SC statistics
    sc_occurrence_rate: float = 0.0
    mean_sc_count: float = 0.0
    
    # Scenario analysis (compatible with MonteCarloSummary)
    # Maps scenario_type ("no_sc", "early_sc", "mid_sc", "late_sc") to ScenarioAnalysis
    scenario_analyses: Dict = field(default_factory=dict)
    scenario_win_rates: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def get_ranking(self) -> List[Tuple[str, float]]:
        """Get strategies ranked by win probability (higher is better)."""
        return sorted(
            [(name, s.win_probability) for name, s in self.strategy_summaries.items()],
            key=lambda x: x[1],
            reverse=True  # Higher win rate is better
        )
    
    def to_dict(self) -> dict:
        return {
            'iterations': self.iterations,
            'our_driver': self.our_driver,
            'grid_position': self.grid_position,
            'total_drivers': self.total_drivers,
            'strategies': {k: v.to_dict() for k, v in self.strategy_summaries.items()},
            'best_by_position': self.best_by_position,
            'best_by_win_rate': self.best_by_win_rate,
            'sc_occurrence_rate': round(self.sc_occurrence_rate, 1),
            'ranking': self.get_ranking(),
        }


class CompetitiveMonteCarloSimulator:
    """
    Monte Carlo simulator with 20-driver competition.
    
    Each iteration:
    1. Randomly generates SC/VSC events
    2. Simulates full race with all drivers
    3. Tracks our driver's finish position
    
    Results show position probabilities, not just time comparisons.
    
    Usage:
        simulator = CompetitiveMonteCarloSimulator(
            sim_params, mc_params, 
            fp2_predictions, opponent_strategies
        )
        simulator.set_our_driver("ALB", grid_position=13)
        summary = simulator.run_simulation(strategies)
    """
    
    def __init__(
        self,
        sim_params: SimulationParams,
        mc_params: MonteCarloParams,
        fp2_predictions: List[Dict],
        opponent_strategies: Optional[Dict[str, Dict]] = None,
        long_run_data: Optional[Dict] = None,
    ):
        """
        Initialize competitive Monte Carlo simulator.
        
        Args:
            sim_params: Race simulation parameters
            mc_params: Monte Carlo parameters (iterations, SC probability)
            fp2_predictions: FP2->Q predictions for all 20 drivers
            opponent_strategies: Strategy settings for opponents
            long_run_data: Long run degradation data
        """
        self.sim_params = sim_params
        self.mc_params = mc_params
        self.fp2_predictions = fp2_predictions
        self.opponent_strategies = opponent_strategies or {}
        self.long_run_data = long_run_data
        
        # Our driver settings
        self._our_driver: str = ""
        self._our_grid_position: int = 10
        
        # Initialize random
        if mc_params.seed is not None:
            random.seed(mc_params.seed)
    
    def set_our_driver(self, driver_code: str, grid_position: Optional[int] = None):
        """Set which driver we're optimizing for."""
        self._our_driver = driver_code
        
        if grid_position is not None:
            self._our_grid_position = grid_position
        else:
            # Find from FP2 predictions
            for pred in self.fp2_predictions:
                if pred.get('driver') == driver_code:
                    self._our_grid_position = pred.get('rank', 10)
                    break
        
        print(f"[COMPETITIVE_MC] Our driver: {driver_code} starting P{self._our_grid_position}")
    
    def run_simulation(
        self,
        strategies: List[StrategySimulationResult],
        progress_callback=None,
    ) -> CompetitiveMCSummary:
        """
        Run Monte Carlo simulation with 20-driver competition.
        
        Args:
            strategies: List of strategy options to evaluate
            progress_callback: Optional callback(iteration, total) for progress
            
        Returns:
            CompetitiveMCSummary with position-based statistics
        """
        if not self._our_driver:
            raise ValueError("Must call set_our_driver() before simulation")
        
        iterations = self.mc_params.iterations
        race_laps = self.sim_params.race_laps
        
        # No hard limit - let user decide iteration count
        effective_iterations = iterations
        print(f"[COMPETITIVE_MC] Running {effective_iterations} iterations (user-defined)")
        
        # Storage for results per strategy
        results_per_strategy: Dict[str, List[CompetitiveIterationResult]] = {
            s.strategy_name: [] for s in strategies
        }
        
        sc_counts = []
        
        print(f"[COMPETITIVE_MC] Running {effective_iterations} iterations "
              f"x {len(strategies)} strategies x {len(self.fp2_predictions)} drivers...")
        
        for i in range(effective_iterations):
            # Update progress more frequently for better UI responsiveness
            if progress_callback:
                progress_callback(i, effective_iterations)
            
            # Print progress every 10 iterations (reduced from 20 for 1000+ iterations)
            if i % 10 == 0:
                print(f"[COMPETITIVE_MC] Iteration {i}/{effective_iterations}")
            
            # Generate SC events for this iteration
            sc_events = self._generate_sc_events()
            sc_counts.append(len(sc_events))
            
            # Simulate each strategy option
            for strategy in strategies:
                result = self._run_single_iteration(
                    strategy, 
                    sc_events, 
                    iteration_id=i
                )
                results_per_strategy[strategy.strategy_name].append(result)
        
        # Build summary
        summary = self._build_summary(
            results_per_strategy, 
            strategies, 
            effective_iterations,
            sc_counts
        )
        
        print(f"[COMPETITIVE_MC] Best strategy: {summary.best_by_position} "
              f"(mean P{summary.strategy_summaries[summary.best_by_position].mean_finish_position:.1f})")
        
        return summary
    
    def _run_single_iteration(
        self,
        strategy: StrategySimulationResult,
        sc_events: List[SafetyCarEvent],
        iteration_id: int,
    ) -> CompetitiveIterationResult:
        """Run one iteration with a specific strategy."""
        
        # Create race simulator (simple_mode=True for MC performance)
        simulator = FullRaceSimulator(
            sim_params=self.sim_params,
            sc_probability=0,  # We inject SC events manually
            overtaking_difficulty=0.5,
            simple_mode=True,  # Use simple mode for Monte Carlo iterations
        )
        
        # Load all drivers
        simulator.load_drivers(self.fp2_predictions, self.long_run_data)
        
        # Set opponent strategies
        simulator.set_opponent_strategies(self.opponent_strategies)
        
        # Set our strategy
        simulator.set_our_strategy(self._our_driver, strategy.stints)
        
        # Inject SC events
        simulator.inject_sc_events([
            (e.start_lap, e.duration, e.is_vsc) for e in sc_events
        ])
        
        # Run simulation
        race_result = simulator.simulate_race(seed=iteration_id)
        
        # Extract our result
        if race_result.our_result:
            our = race_result.our_result
            return CompetitiveIterationResult(
                iteration_id=iteration_id,
                our_driver=self._our_driver,
                our_strategy=strategy.strategy_name,
                finish_position=our.final_position,
                grid_position=our.grid_position,
                positions_gained=our.positions_gained,
                total_time=our.total_time,
                sc_events=sc_events,
            )
        else:
            # Fallback if our driver not found
            return CompetitiveIterationResult(
                iteration_id=iteration_id,
                our_driver=self._our_driver,
                our_strategy=strategy.strategy_name,
                finish_position=self._our_grid_position,
                grid_position=self._our_grid_position,
                positions_gained=0,
                total_time=0,
                sc_events=sc_events,
            )
    
    def _generate_sc_events(self) -> List[SafetyCarEvent]:
        """Generate random SC/VSC events for an iteration."""
        events = []
        race_laps = self.sim_params.race_laps
        
        current_lap = 1
        while current_lap < race_laps - 5:  # No SC in last 5 laps
            # Check for SC
            if random.random() * 100 < self.mc_params.sc_probability_per_lap:
                duration = random.randint(
                    self.mc_params.sc_duration_min,
                    self.mc_params.sc_duration_max
                )
                events.append(SafetyCarEvent(
                    start_lap=current_lap,
                    duration=duration,
                    is_vsc=False
                ))
                current_lap += duration + 3  # Gap after SC
                continue
            
            # Check for VSC
            if random.random() * 100 < self.mc_params.vsc_probability_per_lap:
                duration = random.randint(
                    self.mc_params.vsc_duration_min,
                    self.mc_params.vsc_duration_max
                )
                events.append(SafetyCarEvent(
                    start_lap=current_lap,
                    duration=duration,
                    is_vsc=True
                ))
                current_lap += duration + 2
                continue
            
            current_lap += 1
        
        return events
    
    def _build_summary(
        self,
        results_per_strategy: Dict[str, List[CompetitiveIterationResult]],
        strategies: List[StrategySimulationResult],
        iterations: int,
        sc_counts: List[int],
    ) -> CompetitiveMCSummary:
        """Build summary from all iteration results."""
        
        summary = CompetitiveMCSummary(
            iterations=iterations,
            our_driver=self._our_driver,
            grid_position=self._our_grid_position,
            total_drivers=len(self.fp2_predictions),
        )
        
        # SC statistics
        races_with_sc = sum(1 for c in sc_counts if c > 0)
        summary.sc_occurrence_rate = races_with_sc / iterations * 100
        summary.mean_sc_count = sum(sc_counts) / len(sc_counts)
        
        # Process each strategy
        best_position = 999.0
        best_win_rate = 0.0
        best_consistency = 999.0
        
        for strategy in strategies:
            name = strategy.strategy_name
            results = results_per_strategy[name]
            
            strat_summary = CompetitiveStrategySummary(
                strategy_name=name,
                strategy_notation=strategy.get_stint_notation(),
            )
            
            # Position statistics
            positions = [r.finish_position for r in results]
            times = [r.total_time for r in results if r.total_time > 0]
            gains = [r.positions_gained for r in results]
            
            strat_summary.mean_finish_position = sum(positions) / len(positions)
            strat_summary.best_finish = min(positions)
            strat_summary.worst_finish = max(positions)
            strat_summary.finish_std = self._std(positions)
            
            strat_summary.mean_positions_gained = sum(gains) / len(gains)
            strat_summary.positions_gained_std = self._std(gains)
            
            # Win/Podium/Points probabilities
            strat_summary.win_probability = sum(1 for p in positions if p == 1) / len(positions) * 100
            strat_summary.podium_probability = sum(1 for p in positions if p <= 3) / len(positions) * 100
            strat_summary.top5_probability = sum(1 for p in positions if p <= 5) / len(positions) * 100
            strat_summary.points_probability = sum(1 for p in positions if p <= 10) / len(positions) * 100
            
            # SC impact
            with_sc = [r for r in results if r.sc_events]
            without_sc = [r for r in results if not r.sc_events]
            
            strat_summary.wins_with_sc = sum(1 for r in with_sc if r.finish_position == 1)
            strat_summary.wins_without_sc = sum(1 for r in without_sc if r.finish_position == 1)
            
            if with_sc:
                strat_summary.mean_position_with_sc = sum(r.finish_position for r in with_sc) / len(with_sc)
            if without_sc:
                strat_summary.mean_position_without_sc = sum(r.finish_position for r in without_sc) / len(without_sc)
            
            # Time statistics
            if times:
                strat_summary.mean_time = sum(times) / len(times)
                strat_summary.time_std = self._std(times)
            
            # Position distribution
            pos_counts = defaultdict(int)
            for p in positions:
                pos_counts[p] += 1
            strat_summary.position_distribution = {
                p: count / len(positions) * 100 
                for p, count in sorted(pos_counts.items())
            }
            
            summary.strategy_summaries[name] = strat_summary
            
            # Track best strategies
            if strat_summary.mean_finish_position < best_position:
                best_position = strat_summary.mean_finish_position
                summary.best_by_position = name
            
            if strat_summary.win_probability > best_win_rate:
                best_win_rate = strat_summary.win_probability
                summary.best_by_win_rate = name
            
            if strat_summary.finish_std < best_consistency:
                best_consistency = strat_summary.finish_std
                summary.best_by_consistency = name
        
        # Build scenario analyses (compatible with MonteCarloSummary)
        summary.scenario_analyses = self._build_scenario_analyses(
            results_per_strategy, strategies, iterations
        )
        
        return summary
    
    def _build_scenario_analyses(
        self,
        results_per_strategy: Dict[str, List[CompetitiveIterationResult]],
        strategies: List[StrategySimulationResult],
        iterations: int,
    ) -> Dict:
        """
        Build scenario analysis compatible with MonteCarloSummary.scenario_analyses.
        
        Categorizes iterations by SC timing and calculates best strategy for each scenario.
        """
        from strategy_simulator.core.monte_carlo import ScenarioAnalysis
        
        race_laps = self.sim_params.race_laps
        
        # Categorize all iterations by scenario
        scenario_iterations: Dict[str, Dict[str, List[CompetitiveIterationResult]]] = {
            "no_sc": {s.strategy_name: [] for s in strategies},
            "early_sc": {s.strategy_name: [] for s in strategies},
            "mid_sc": {s.strategy_name: [] for s in strategies},
            "late_sc": {s.strategy_name: [] for s in strategies},
        }
        
        # Assign each iteration to a scenario
        for strategy in strategies:
            name = strategy.strategy_name
            for result in results_per_strategy[name]:
                scenario_type = result.get_scenario_type(race_laps)
                scenario_iterations[scenario_type][name].append(result)
        
        # Build ScenarioAnalysis for each scenario type
        analyses = {}
        scenario_names = {
            "no_sc": "No Safety Car",
            "early_sc": "Early SC (Lap 1-20)",
            "mid_sc": "Mid-Race SC (Lap 21-40)",
            "late_sc": "Late SC (Lap 41+)",
        }
        
        for scenario_type, name in scenario_names.items():
            strat_results = scenario_iterations[scenario_type]
            total_count = sum(len(results) for results in strat_results.values())
            
            if total_count == 0:
                continue
            
            # Calculate win rates and average positions for each strategy
            win_rates = {}
            avg_positions = {}
            avg_times = {}
            
            for strat_name, results in strat_results.items():
                if not results:
                    continue
                
                wins = sum(1 for r in results if r.finish_position == 1)
                win_rates[strat_name] = (wins / len(results)) * 100 if results else 0
                avg_positions[strat_name] = sum(r.finish_position for r in results) / len(results)
                times = [r.total_time for r in results if r.total_time > 0]
                avg_times[strat_name] = sum(times) / len(times) if times else 0
            
            # Find best strategy for this scenario (by average position)
            best_strat = min(avg_positions.items(), key=lambda x: x[1])[0] if avg_positions else ""
            best_win_rate = win_rates.get(best_strat, 0)
            
            # Generate decision advice
            advice = []
            if scenario_type == "no_sc":
                advice.append("標準賽事條件 - 執行最佳配速策略")
            elif scenario_type == "early_sc":
                advice.append("早期 SC 對尚未進站的車手有利")
                advice.append("考慮延長第一段輪胎")
            elif scenario_type == "mid_sc":
                advice.append("中段 SC - 進站時機變得關鍵")
                advice.append("注意 SC 期間「免費」進站機會")
            elif scenario_type == "late_sc":
                advice.append("晚期 SC - 最後一段換新胎至關重要")
                advice.append("考慮選擇激進輪胎衝刺終點")
            
            analyses[scenario_type] = ScenarioAnalysis(
                scenario_type=scenario_type,
                scenario_name=name,
                occurrence_rate=(total_count / iterations / len(strategies)) * 100,
                iteration_count=total_count // len(strategies),
                best_strategy=best_strat,
                best_strategy_win_rate=best_win_rate,
                strategy_win_rates=win_rates,
                strategy_avg_times=avg_times,
                decision_advice=advice,
            )
            
            print(f"[COMPETITIVE_MC] Scenario {scenario_type}: "
                  f"{total_count // len(strategies)} iters, best={best_strat}")
        
        return analyses
    
    def _std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance)
