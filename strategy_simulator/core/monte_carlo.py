#!/usr/bin/env python3
"""
Monte Carlo Simulator

Probabilistic race simulation with randomness for:
- Safety Car timing
- Degradation variance
- Fuel consumption variance
- Track position changes

Author: F1T Team
Date: 2025-12-30
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random
from collections import defaultdict
import math

from .lap_simulator import (
    Compound, Stint, SimulationParams, 
    LapSimulator, StrategySimulationResult
)
from .position_tracker import PositionTracker, create_position_tracker, SimulationResult
from ..data.track_config import get_track_config


@dataclass
class MonteCarloParams:
    """Parameters for Monte Carlo simulation"""
    # Number of iterations
    iterations: int = 200  # Changed from 1000 to 200 (2026-01-05)
    
    # Safety Car probability per lap (percentage)
    sc_probability_per_lap: float = 1.5  # 1.5% per lap
    
    # VSC probability per lap
    vsc_probability_per_lap: float = 2.0  # 2.0% per lap
    
    # SC duration range (laps)
    sc_duration_min: int = 3
    sc_duration_max: int = 6
    
    # VSC duration range (laps)
    vsc_duration_min: int = 1
    vsc_duration_max: int = 3
    
    # Degradation variance (standard deviation as fraction of mean)
    deg_variance: float = 0.10  # 10% variance
    
    # Fuel variance
    fuel_variance: float = 0.05  # 5% variance
    
    # Random seed (None for random)
    seed: Optional[int] = None


@dataclass
class SafetyCarEvent:
    """A Safety Car or VSC event"""
    start_lap: int
    duration: int
    is_vsc: bool = False
    
    @property
    def end_lap(self) -> int:
        return self.start_lap + self.duration - 1
    
    @property
    def event_type(self) -> str:
        return "VSC" if self.is_vsc else "SC"
    
    def __repr__(self) -> str:
        return f"{self.event_type}(L{self.start_lap}-{self.end_lap})"


@dataclass
class MonteCarloIteration:
    """Result of a single Monte Carlo iteration"""
    iteration_id: int
    strategy_results: Dict[str, float]  # strategy_name -> total_time
    winner: str
    sc_events: List[SafetyCarEvent] = field(default_factory=list)
    
    def get_scenario_type(self, race_laps: int = 53) -> str:
        """Classify this iteration into a scenario type."""
        if not self.sc_events:
            return "no_sc"
        
        # Find earliest SC start
        earliest_sc = min(e.start_lap for e in self.sc_events)
        
        # Classify by SC timing (as percentage of race)
        race_third = race_laps / 3
        if earliest_sc <= race_third:
            return "early_sc"  # Lap 1-17 for 53 lap race
        elif earliest_sc <= race_third * 2:
            return "mid_sc"   # Lap 18-35
        else:
            return "late_sc"  # Lap 36-53
    
    def to_dict(self) -> dict:
        return {
            'iteration': self.iteration_id,
            'results': self.strategy_results,
            'winner': self.winner,
            'sc_events': [str(e) for e in self.sc_events]
        }


@dataclass
class FullPositionIteration:
    """Result of a single Monte Carlo iteration with full position tracking."""
    iteration_id: int
    final_positions: List[str]  # Ordered list of drivers
    overtake_count: int
    successful_overtakes: int
    sc_events: List[SafetyCarEvent] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'iteration': self.iteration_id,
            'final_positions': self.final_positions,
            'overtake_count': self.overtake_count,
            'successful_overtakes': self.successful_overtakes,
            'sc_events': [str(e) for e in self.sc_events]
        }


@dataclass
class FullPositionSummary:
    """Summary statistics from Monte Carlo simulation with full position tracking."""
    iterations: int
    track_name: str
    total_laps: int
    
    # Position statistics per driver
    # {driver: {position: count}}
    position_distributions: Dict[str, Dict[int, int]] = field(default_factory=dict)
    
    # Average positions
    mean_positions: Dict[str, float] = field(default_factory=dict)
    
    # Overtake statistics
    mean_overtakes: float = 0.0
    mean_successful_overtakes: float = 0.0
    
    # Position change from start
    avg_position_changes: Dict[str, float] = field(default_factory=dict)
    
    # Best/worst case for each driver
    best_positions: Dict[str, int] = field(default_factory=dict)
    worst_positions: Dict[str, int] = field(default_factory=dict)
    
    # Win probabilities
    win_probabilities: Dict[str, float] = field(default_factory=dict)
    podium_probabilities: Dict[str, float] = field(default_factory=dict)
    points_probabilities: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'iterations': self.iterations,
            'track_name': self.track_name,
            'total_laps': self.total_laps,
            'mean_positions': {k: round(v, 2) for k, v in self.mean_positions.items()},
            'mean_overtakes': round(self.mean_overtakes, 1),
            'mean_successful_overtakes': round(self.mean_successful_overtakes, 1),
            'avg_position_changes': {k: round(v, 2) for k, v in self.avg_position_changes.items()},
            'win_probabilities': {k: round(v, 1) for k, v in self.win_probabilities.items()},
            'podium_probabilities': {k: round(v, 1) for k, v in self.podium_probabilities.items()},
            'points_probabilities': {k: round(v, 1) for k, v in self.points_probabilities.items()}
        }


@dataclass
class ScenarioAnalysis:
    """Analysis results for a specific race scenario."""
    scenario_type: str  # "no_sc", "early_sc", "mid_sc", "late_sc"
    scenario_name: str  # Display name
    occurrence_rate: float  # Percentage of simulations
    iteration_count: int
    
    # Best strategy for this scenario
    best_strategy: str
    best_strategy_win_rate: float
    
    # Win rates per strategy in this scenario
    strategy_win_rates: Dict[str, float] = field(default_factory=dict)
    strategy_avg_times: Dict[str, float] = field(default_factory=dict)
    
    # SC-specific recommendations
    decision_advice: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'type': self.scenario_type,
            'name': self.scenario_name,
            'occurrence_rate': round(self.occurrence_rate, 1),
            'count': self.iteration_count,
            'best_strategy': self.best_strategy,
            'best_win_rate': round(self.best_strategy_win_rate, 1),
            'win_rates': {k: round(v, 1) for k, v in self.strategy_win_rates.items()},
            'advice': self.decision_advice
        }


@dataclass
class PositionPrediction:
    """Position prediction for a strategy based on starting position and opponents."""
    strategy_name: str
    starting_position: int
    
    # Expected finish position
    expected_position: float = 0.0
    best_case_position: int = 1
    worst_case_position: int = 20
    
    # Probability distributions
    podium_probability: float = 0.0  # P1-P3
    points_probability: float = 0.0  # P1-P10
    top5_probability: float = 0.0    # P1-P5
    
    # Position change statistics
    expected_gain: float = 0.0  # Positive = gained positions
    gain_variance: float = 0.0
    
    # Finish position distribution (P1-P20 -> probability)
    position_distribution: Dict[int, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'strategy': self.strategy_name,
            'starting_position': self.starting_position,
            'expected_position': round(self.expected_position, 1),
            'best_case': self.best_case_position,
            'worst_case': self.worst_case_position,
            'podium_probability': round(self.podium_probability, 1),
            'points_probability': round(self.points_probability, 1),
            'top5_probability': round(self.top5_probability, 1),
            'expected_gain': round(self.expected_gain, 1),
            'position_distribution': {k: round(v, 2) for k, v in self.position_distribution.items()}
        }


@dataclass
class MonteCarloSummary:
    """Summary statistics from Monte Carlo simulation"""
    iterations: int
    
    # Win statistics per strategy
    win_counts: Dict[str, int] = field(default_factory=dict)
    win_percentages: Dict[str, float] = field(default_factory=dict)
    
    # Time statistics per strategy
    mean_times: Dict[str, float] = field(default_factory=dict)
    std_times: Dict[str, float] = field(default_factory=dict)
    min_times: Dict[str, float] = field(default_factory=dict)
    max_times: Dict[str, float] = field(default_factory=dict)
    
    # SC statistics
    sc_occurrence_rate: float = 0.0
    mean_sc_count: float = 0.0
    sc_impact_analysis: Dict[str, Dict] = field(default_factory=dict)
    
    # Position analysis
    starting_position: int = 10
    position_predictions: Dict[str, PositionPrediction] = field(default_factory=dict)
    
    # Scenario analysis (NEW - for scene-based recommendations)
    scenario_analyses: Dict[str, ScenarioAnalysis] = field(default_factory=dict)
    race_laps: int = 53
    
    def get_ranking(self) -> List[Tuple[str, float]]:
        """Get strategies ranked by win percentage."""
        return sorted(
            self.win_percentages.items(),
            key=lambda x: x[1],
            reverse=True
        )
    
    def get_best_strategy_for_position(self) -> Optional[str]:
        """Get the best strategy based on position gain potential."""
        if not self.position_predictions:
            return None
        best = max(self.position_predictions.values(), 
                   key=lambda p: p.expected_gain)
        return best.strategy_name
    
    def get_scenario_recommendation(self) -> str:
        """Generate comprehensive recommendation based on all scenarios."""
        if not self.scenario_analyses:
            return "請執行 Monte Carlo 模擬以獲取場景分析。"
        
        lines = ["📊 綜合策略建議:"]
        
        # Find most robust strategy (best average across scenarios)
        strategy_scores = defaultdict(float)
        for scenario in self.scenario_analyses.values():
            for strat, rate in scenario.strategy_win_rates.items():
                # Weight by scenario occurrence
                strategy_scores[strat] += rate * (scenario.occurrence_rate / 100)
        
        if strategy_scores:
            best_overall = max(strategy_scores, key=strategy_scores.get)
            lines.append(f"• 最穩健策略: {best_overall} (加權勝率: {strategy_scores[best_overall]:.1f}%)")
        
        # Scenario-specific advice
        for scenario_type in ["no_sc", "early_sc", "mid_sc", "late_sc"]:
            if scenario_type in self.scenario_analyses:
                s = self.scenario_analyses[scenario_type]
                lines.append(f"• {s.scenario_name}: 最佳 {s.best_strategy} ({s.best_strategy_win_rate:.0f}%)")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        return {
            'iterations': self.iterations,
            'win_counts': self.win_counts,
            'win_percentages': {k: round(v, 2) for k, v in self.win_percentages.items()},
            'mean_times': {k: round(v, 3) for k, v in self.mean_times.items()},
            'std_times': {k: round(v, 3) for k, v in self.std_times.items()},
            'sc_occurrence_rate': round(self.sc_occurrence_rate, 2),
            'mean_sc_count': round(self.mean_sc_count, 2),
            'ranking': self.get_ranking(),
            'starting_position': self.starting_position,
            'position_predictions': {k: v.to_dict() for k, v in self.position_predictions.items()},
            'scenario_analyses': {k: v.to_dict() for k, v in self.scenario_analyses.items()},
            'race_laps': self.race_laps
        }


class MonteCarloSimulator:
    """
    Monte Carlo race simulation with probabilistic events.
    
    Simulates multiple race scenarios with random:
    - Safety Car timing
    - Degradation variance
    - Pit timing optimization
    
    Usage:
        params = SimulationParams(...)
        mc_params = MonteCarloParams(iterations=1000)
        
        mc = MonteCarloSimulator(params, mc_params)
        
        strategies = [
            [Stint(Compound.MEDIUM, 22), Stint(Compound.HARD, 31)],
            [Stint(Compound.SOFT, 15), Stint(Compound.HARD, 38)],
        ]
        
        summary = mc.run_simulation(strategies)
        print(f"Plan A wins {summary.win_percentages['Plan A']:.1f}% of races")
    """
    
    def __init__(
        self, 
        sim_params: SimulationParams,
        mc_params: MonteCarloParams = None
    ):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            sim_params: Base simulation parameters
            mc_params: Monte Carlo specific parameters
        """
        self.sim_params = sim_params
        self.mc_params = mc_params or MonteCarloParams()
        self.base_simulator = LapSimulator(sim_params)
        
        if self.mc_params.seed is not None:
            random.seed(self.mc_params.seed)
    
    def generate_sc_events(self) -> List[SafetyCarEvent]:
        """Generate random SC/VSC events for one iteration."""
        events = []
        race_laps = self.sim_params.race_laps
        current_lap = 1
        
        while current_lap <= race_laps:
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
                current_lap += duration
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
                current_lap += duration
                continue
            
            current_lap += 1
        
        return events
    
    def apply_variance_to_params(
        self, 
        base_params: SimulationParams
    ) -> SimulationParams:
        """Apply random variance to simulation parameters."""
        # Create modified params
        new_deg_rates = {}
        for compound, rate in base_params.deg_rates.items():
            variance = rate * self.mc_params.deg_variance
            new_rate = rate + random.gauss(0, variance)
            new_deg_rates[compound] = max(0.01, new_rate)  # Ensure positive
        
        # Fuel variance
        new_fuel_effect = base_params.fuel_effect_coefficient * (
            1 + random.gauss(0, self.mc_params.fuel_variance)
        )
        
        return SimulationParams(
            race_laps=base_params.race_laps,
            base_lap_time=base_params.base_lap_time,
            start_fuel_kg=base_params.start_fuel_kg,
            fuel_kg_per_lap=base_params.fuel_kg_per_lap,
            fuel_effect_coefficient=new_fuel_effect,
            deg_rates=new_deg_rates,
            pit_loss_green=base_params.pit_loss_green,
            pit_loss_sc=base_params.pit_loss_sc,
            pit_loss_vsc=base_params.pit_loss_vsc,
            compound_deltas=base_params.compound_deltas,
        )
    
    def simulate_with_sc(
        self,
        stints: List[Stint],
        sc_events: List[SafetyCarEvent],
        varied_params: SimulationParams
    ) -> float:
        """
        Simulate a race with SC events affecting pit loss.
        
        If pit occurs during SC/VSC, use reduced pit loss.
        """
        simulator = LapSimulator(varied_params)
        
        # Determine pit laps
        pit_laps = []
        current_lap = 1
        for i, stint in enumerate(stints[:-1]):
            pit_lap = current_lap + stint.laps - 1
            pit_laps.append(pit_lap)
            current_lap += stint.laps
        
        # Calculate pit loss for each stop
        total_pit_loss = 0.0
        for pit_lap in pit_laps:
            # Check if pit is during SC/VSC
            pit_loss = varied_params.pit_loss_green  # Default
            
            for event in sc_events:
                if event.start_lap <= pit_lap <= event.end_lap:
                    if event.is_vsc:
                        pit_loss = varied_params.pit_loss_vsc
                    else:
                        pit_loss = varied_params.pit_loss_sc
                    break
            
            total_pit_loss += pit_loss
        
        # Simulate laps
        result = simulator.simulate_strategy(stints)
        
        # Override pit loss with our calculated value
        result.total_pit_loss = total_pit_loss
        
        return result.total_time
    
    def run_single_iteration(
        self,
        strategies: List[List[Stint]],
        strategy_names: List[str],
        iteration_id: int
    ) -> MonteCarloIteration:
        """Run a single Monte Carlo iteration."""
        # Generate random events
        sc_events = self.generate_sc_events()
        
        # Apply parameter variance
        varied_params = self.apply_variance_to_params(self.sim_params)
        
        # Simulate each strategy
        results = {}
        for name, stints in zip(strategy_names, strategies):
            # Deep copy stints to avoid mutation
            stints_copy = [
                Stint(s.compound, s.laps, s.start_lap) 
                for s in stints
            ]
            total_time = self.simulate_with_sc(stints_copy, sc_events, varied_params)
            results[name] = total_time
        
        # Determine winner
        winner = min(results, key=results.get)
        
        return MonteCarloIteration(
            iteration_id=iteration_id,
            strategy_results=results,
            winner=winner,
            sc_events=sc_events
        )
    
    def run_simulation(
        self,
        strategies: List[List[Stint]],
        strategy_names: List[str] = None
    ) -> MonteCarloSummary:
        """
        Run full Monte Carlo simulation.
        
        Args:
            strategies: List of strategies (each is a list of Stints)
            strategy_names: Optional names for strategies
        
        Returns:
            MonteCarloSummary with statistics
        """
        if strategy_names is None:
            strategy_names = [f"Plan {chr(65+i)}" for i in range(len(strategies))]
        
        # Collect results
        iterations_data: List[MonteCarloIteration] = []
        win_counts = defaultdict(int)
        all_times = defaultdict(list)
        sc_counts = []
        
        for i in range(self.mc_params.iterations):
            result = self.run_single_iteration(strategies, strategy_names, i)
            iterations_data.append(result)
            
            win_counts[result.winner] += 1
            for name, time in result.strategy_results.items():
                all_times[name].append(time)
            
            sc_counts.append(len(result.sc_events))
        
        # Calculate statistics
        summary = MonteCarloSummary(iterations=self.mc_params.iterations)
        
        # Win statistics
        for name in strategy_names:
            summary.win_counts[name] = win_counts[name]
            summary.win_percentages[name] = (
                win_counts[name] / self.mc_params.iterations * 100
            )
        
        # Time statistics
        for name in strategy_names:
            times = all_times[name]
            summary.mean_times[name] = sum(times) / len(times)
            summary.min_times[name] = min(times)
            summary.max_times[name] = max(times)
            
            # Standard deviation
            mean = summary.mean_times[name]
            variance = sum((t - mean) ** 2 for t in times) / len(times)
            summary.std_times[name] = math.sqrt(variance)
        
        # SC statistics
        races_with_sc = sum(1 for c in sc_counts if c > 0)
        summary.sc_occurrence_rate = races_with_sc / self.mc_params.iterations * 100
        summary.mean_sc_count = sum(sc_counts) / len(sc_counts)
        
        # SC impact analysis per strategy
        for name in strategy_names:
            with_sc = []
            without_sc = []
            for iter_data in iterations_data:
                if iter_data.sc_events:
                    with_sc.append(iter_data.strategy_results[name])
                else:
                    without_sc.append(iter_data.strategy_results[name])
            
            summary.sc_impact_analysis[name] = {
                'mean_with_sc': sum(with_sc) / len(with_sc) if with_sc else 0,
                'mean_without_sc': sum(without_sc) / len(without_sc) if without_sc else 0,
                'wins_with_sc': sum(1 for d in iterations_data 
                                   if d.sc_events and d.winner == name),
                'wins_without_sc': sum(1 for d in iterations_data 
                                      if not d.sc_events and d.winner == name),
            }
        
        # === NEW: Scenario-based analysis ===
        summary.race_laps = self.sim_params.race_laps
        summary.scenario_analyses = self._analyze_scenarios(
            iterations_data, strategy_names, self.sim_params.race_laps
        )
        
        return summary
    
    def _analyze_scenarios(
        self,
        iterations_data: List[MonteCarloIteration],
        strategy_names: List[str],
        race_laps: int
    ) -> Dict[str, ScenarioAnalysis]:
        """
        Analyze simulation results by scenario type.
        
        Args:
            iterations_data: All Monte Carlo iterations
            strategy_names: Names of strategies
            race_laps: Total race laps
            
        Returns:
            Dictionary mapping scenario_type to ScenarioAnalysis
        """
        # Classify iterations by scenario
        scenario_iterations = defaultdict(list)
        for iter_data in iterations_data:
            scenario_type = iter_data.get_scenario_type(race_laps)
            scenario_iterations[scenario_type].append(iter_data)
        
        scenario_names = {
            "no_sc": "無安全車",
            "early_sc": f"早期SC (L1-{race_laps//3})",
            "mid_sc": f"中期SC (L{race_laps//3+1}-{2*race_laps//3})",
            "late_sc": f"晚期SC (L{2*race_laps//3+1}-{race_laps})"
        }
        
        results = {}
        total_iterations = len(iterations_data)
        
        for scenario_type, scenario_name in scenario_names.items():
            iters = scenario_iterations[scenario_type]
            if not iters:
                # No iterations for this scenario
                continue
                
            occurrence_rate = len(iters) / total_iterations * 100
            
            # Calculate win rates per strategy in this scenario
            win_counts = defaultdict(int)
            for iter_data in iters:
                win_counts[iter_data.winner] += 1
            
            strategy_win_rates = {}
            for name in strategy_names:
                strategy_win_rates[name] = win_counts[name] / len(iters) * 100 if iters else 0
            
            # Find best strategy
            best_strategy = max(strategy_win_rates, key=strategy_win_rates.get)
            best_win_rate = strategy_win_rates[best_strategy]
            
            # Generate decision advice
            decision_advice = self._generate_scenario_advice(
                scenario_type, best_strategy, best_win_rate, strategy_win_rates
            )
            
            results[scenario_type] = ScenarioAnalysis(
                scenario_type=scenario_type,
                scenario_name=scenario_name,
                occurrence_rate=occurrence_rate,
                iteration_count=len(iters),
                best_strategy=best_strategy,
                best_strategy_win_rate=best_win_rate,
                strategy_win_rates=strategy_win_rates,
                decision_advice=decision_advice
            )
        
        return results
    
    def _generate_scenario_advice(
        self,
        scenario_type: str,
        best_strategy: str,
        best_win_rate: float,
        strategy_win_rates: Dict[str, float]
    ) -> List[str]:
        """Generate strategic advice for a specific scenario."""
        advice = []
        
        if scenario_type == "no_sc":
            advice.append(f"無SC時 {best_strategy} 表現最佳 ({best_win_rate:.0f}%)")
            if best_win_rate < 60:
                advice.append("策略差異不大，選擇更適合賽道特性的策略")
        
        elif scenario_type == "early_sc":
            advice.append(f"早期SC時建議 {best_strategy} ({best_win_rate:.0f}%)")
            if "1-stop" in best_strategy.lower() or "一停" in best_strategy:
                advice.append("一停策略在早期SC時通常有優勢（免費進站）")
            else:
                advice.append("二停策略可能因提前用掉一次進站而受益")
        
        elif scenario_type == "mid_sc":
            advice.append(f"中期SC時 {best_strategy} 最優 ({best_win_rate:.0f}%)")
            advice.append("考慮在SC期間進站以減少時間損失")
        
        elif scenario_type == "late_sc":
            advice.append(f"晚期SC時 {best_strategy} 最優 ({best_win_rate:.0f}%)")
            advice.append("晚期SC可能影響輪胎策略的計劃進站時機")
            if best_win_rate > 70:
                advice.append("此策略對晚期SC有明顯優勢")
        
        # Add comparison advice
        sorted_rates = sorted(strategy_win_rates.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_rates) >= 2:
            gap = sorted_rates[0][1] - sorted_rates[1][1]
            if gap < 5:
                advice.append("策略差距小，可根據實際賽況靈活調整")
            elif gap > 20:
                advice.append(f"強烈建議使用 {best_strategy}")
        
        return advice
    
    def analyze_sc_windows(
        self,
        strategy: List[Stint]
    ) -> Dict:
        """
        Analyze optimal SC timing windows for a strategy.
        
        Returns:
            Dictionary with SC window recommendations
        """
        # Find pit laps
        pit_laps = []
        current_lap = 1
        for stint in strategy[:-1]:
            pit_lap = current_lap + stint.laps - 1
            pit_laps.append(pit_lap)
            current_lap += stint.laps
        
        windows = []
        for pit_lap in pit_laps:
            # Best SC window is 1-3 laps before pit
            best_start = max(1, pit_lap - 3)
            best_end = pit_lap
            
            # Calculate pit loss saving
            green_loss = self.sim_params.pit_loss_green
            sc_loss = self.sim_params.pit_loss_sc
            saving = green_loss - sc_loss
            
            windows.append({
                'pit_lap': pit_lap,
                'optimal_sc_window': (best_start, best_end),
                'pit_loss_saving': round(saving, 1),
                'recommendation': f"SC at L{best_start}-{best_end} saves {saving:.1f}s"
            })
        
        return {
            'strategy_notation': "→".join(s.compound.short_name() for s in strategy),
            'pit_laps': pit_laps,
            'sc_windows': windows
        }
    
    def run_simulation_with_position(
        self,
        strategies: List[List[Stint]],
        strategy_names: List[str] = None,
        starting_position: int = 10,
        opponent_strategies: Dict = None,
        overtaking_difficulty: float = 0.5
    ) -> MonteCarloSummary:
        """
        Run Monte Carlo simulation with position tracking.
        
        This enhanced simulation considers:
        - Starting grid position
        - Opponent strategies and their pit timing
        - Position changes based on pace difference
        - Overtaking difficulty of the track
        
        Args:
            strategies: List of strategies (each is a list of Stints)
            strategy_names: Optional names for strategies
            starting_position: Grid position (1-20)
            opponent_strategies: Dict of opponent strategies from OpponentStrategyPredictor
            overtaking_difficulty: Track difficulty (0=easy, 1=hard) affects position change
        
        Returns:
            MonteCarloSummary with position predictions
        """
        # First run standard MC simulation
        summary = self.run_simulation(strategies, strategy_names)
        
        # Store starting position
        summary.starting_position = starting_position
        
        # Generate position predictions for each strategy
        if strategy_names is None:
            strategy_names = [f"Plan {chr(65+i)}" for i in range(len(strategies))]
        
        # Calculate position predictions for each strategy
        for idx, name in enumerate(strategy_names):
            pred = self._calculate_position_prediction(
                strategy=strategies[idx],
                strategy_name=name,
                starting_position=starting_position,
                mean_time=summary.mean_times.get(name, 0),
                std_time=summary.std_times.get(name, 0),
                best_mean_time=min(summary.mean_times.values()) if summary.mean_times else 0,
                opponent_strategies=opponent_strategies,
                overtaking_difficulty=overtaking_difficulty
            )
            summary.position_predictions[name] = pred
        
        return summary
    
    def _calculate_position_prediction(
        self,
        strategy: List[Stint],
        strategy_name: str,
        starting_position: int,
        mean_time: float,
        std_time: float,
        best_mean_time: float,
        opponent_strategies: Dict = None,
        overtaking_difficulty: float = 0.5
    ) -> PositionPrediction:
        """
        Calculate position prediction for a strategy.
        
        Uses a simplified model:
        - Each second of pace advantage = ~0.5 positions gained (modified by overtaking difficulty)
        - SC events create position shuffle opportunities
        - Pit timing relative to opponents affects track position
        """
        pred = PositionPrediction(
            strategy_name=strategy_name,
            starting_position=starting_position
        )
        
        # Calculate pace-based position gain potential
        # Time delta to best strategy (negative = slower)
        time_delta = mean_time - best_mean_time
        
        # Overtaking factor: lower difficulty = easier to gain positions
        overtake_factor = 1.0 - (overtaking_difficulty * 0.6)  # 0.4 to 1.0
        
        # Estimate position change based on pace
        # Roughly: 1 second pace advantage = 0.3-0.7 positions depending on track
        pace_based_gain = -time_delta * 0.08 * overtake_factor  # Positive = gain
        
        # Factor in starting position effects
        # P1-P3: Hard to gain, easy to lose
        # P10-P15: Most opportunity for gains
        # P18-P20: Limited upward mobility
        position_factor = self._get_position_factor(starting_position)
        
        # Calculate expected gain
        expected_gain = pace_based_gain * position_factor
        
        # Limit expected gain based on starting position
        max_gain = starting_position - 1  # Can't gain more than start-1 positions
        max_loss = 20 - starting_position  # Can't lose more than 20-start positions
        
        expected_gain = max(-max_loss, min(max_gain, expected_gain))
        pred.expected_gain = expected_gain
        
        # Expected finish position
        expected_position = starting_position - expected_gain
        pred.expected_position = max(1, min(20, expected_position))
        
        # Best/worst case based on variance
        variance_positions = std_time * 0.05  # Roughly 0.05 positions per second variance
        pred.best_case_position = max(1, int(expected_position - variance_positions - 2))
        pred.worst_case_position = min(20, int(expected_position + variance_positions + 2))
        
        # Calculate probability distributions
        pred.position_distribution = self._calculate_position_distribution(
            expected_position=pred.expected_position,
            variance=variance_positions + 1.5,  # Add baseline variance
            starting_position=starting_position
        )
        
        # Calculate probabilities from distribution
        pred.podium_probability = sum(pred.position_distribution.get(p, 0) for p in [1, 2, 3])
        pred.top5_probability = sum(pred.position_distribution.get(p, 0) for p in range(1, 6))
        pred.points_probability = sum(pred.position_distribution.get(p, 0) for p in range(1, 11))
        
        pred.gain_variance = variance_positions
        
        return pred
    
    def _get_position_factor(self, position: int) -> float:
        """
        Get position change factor based on starting position.
        
        P1-P3: 0.3 (hard to improve)
        P4-P6: 0.6 (some opportunity)
        P7-P10: 0.9 (good opportunity)
        P11-P15: 1.0 (maximum opportunity)
        P16-P20: 0.7 (limited by car performance)
        """
        if position <= 3:
            return 0.3
        elif position <= 6:
            return 0.6
        elif position <= 10:
            return 0.9
        elif position <= 15:
            return 1.0
        else:
            return 0.7
    
    def _calculate_position_distribution(
        self,
        expected_position: float,
        variance: float,
        starting_position: int
    ) -> Dict[int, float]:
        """
        Calculate probability distribution of finish positions.
        
        Uses a truncated normal-like distribution centered on expected position.
        """
        distribution = {}
        total = 0.0
        
        for pos in range(1, 21):
            # Calculate probability using simplified normal distribution
            z = (pos - expected_position) / max(variance, 0.5)
            prob = math.exp(-0.5 * z * z)
            
            # Apply position-based modifiers
            # Starting from P1-P3 has low probability of finishing P15+
            if starting_position <= 3 and pos >= 15:
                prob *= 0.1
            # Starting from P15+ has low probability of podium
            elif starting_position >= 15 and pos <= 3:
                prob *= 0.05
            
            distribution[pos] = prob
            total += prob
        
        # Normalize to percentages
        if total > 0:
            for pos in distribution:
                distribution[pos] = (distribution[pos] / total) * 100
        
        return distribution
    
    def run_full_position_simulation(
        self,
        grid: List[Dict],
        track_name: str,
        total_laps: int = None,
        time_step: float = 1.0,
        iterations: int = None
    ) -> FullPositionSummary:
        """
        Run Monte Carlo simulation with full position tracking using PositionTracker.
        
        This is the "Complete Mode" that simulates all 20 cars with:
        - Overtake attempts and success rates
        - DRS activation
        - SC/VSC events
        - Position changes lap by lap
        
        Args:
            grid: Starting grid, format: [{"driver": "VER", "team": "Red Bull Racing", "tyre": "M"}, ...]
            track_name: Name of the track (e.g., "Japan", "Bahrain")
            total_laps: Total race laps (defaults to sim_params.race_laps)
            time_step: Simulation time step in seconds (default 1.0)
            iterations: Number of Monte Carlo iterations (defaults to mc_params.iterations)
        
        Returns:
            FullPositionSummary with position statistics for all drivers
        """
        if iterations is None:
            iterations = self.mc_params.iterations
        if total_laps is None:
            total_laps = self.sim_params.race_laps
            
        # Track starting positions
        starting_positions = {entry['driver']: i + 1 for i, entry in enumerate(grid)}
        
        # Results storage
        all_iterations: List[FullPositionIteration] = []
        position_counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        total_overtakes = 0
        total_successful = 0
        
        print(f"[MonteCarlo] Starting full position simulation")
        print(f"[MonteCarlo] Track: {track_name}, Laps: {total_laps}, Iterations: {iterations}")
        
        for iteration in range(iterations):
            # Generate SC/VSC events for this iteration
            sc_events = self.generate_sc_events()
            
            # Create position tracker
            tracker = create_position_tracker(track_name, time_step, total_laps)
            tracker.initialize_grid(grid)
            
            # Apply SC/VSC events
            # Note: In a more complete implementation, we would inject these events
            # during simulation. For now, we'll set initial SC state if early SC.
            for event in sc_events:
                if event.start_lap == 1:
                    tracker.sc_active = not event.is_vsc
                    tracker.vsc_active = event.is_vsc
                    
            # Run simulation
            result = tracker.run_simulation()
            
            # Record results
            overtake_count = len(result.overtake_attempts)
            successful_count = sum(1 for a in result.overtake_attempts if a.success)
            
            iteration_result = FullPositionIteration(
                iteration_id=iteration,
                final_positions=result.final_positions,
                overtake_count=overtake_count,
                successful_overtakes=successful_count,
                sc_events=sc_events
            )
            all_iterations.append(iteration_result)
            
            # Update position counts
            for pos, driver in enumerate(result.final_positions, 1):
                position_counts[driver][pos] += 1
                
            total_overtakes += overtake_count
            total_successful += successful_count
            
            # Progress update every 20%
            if (iteration + 1) % max(1, iterations // 5) == 0:
                print(f"[MonteCarlo] Progress: {iteration + 1}/{iterations} ({(iteration + 1) * 100 // iterations}%)")
        
        # Calculate summary statistics
        summary = FullPositionSummary(
            iterations=iterations,
            track_name=track_name,
            total_laps=total_laps,
            position_distributions=dict(position_counts),
            mean_overtakes=total_overtakes / iterations,
            mean_successful_overtakes=total_successful / iterations
        )
        
        # Calculate per-driver statistics
        for driver in starting_positions:
            if driver in position_counts:
                counts = position_counts[driver]
                total_pos = sum(pos * count for pos, count in counts.items())
                mean_pos = total_pos / iterations
                summary.mean_positions[driver] = mean_pos
                
                # Position change from start
                summary.avg_position_changes[driver] = starting_positions[driver] - mean_pos
                
                # Best/worst
                summary.best_positions[driver] = min(counts.keys())
                summary.worst_positions[driver] = max(counts.keys())
                
                # Probabilities
                summary.win_probabilities[driver] = counts.get(1, 0) / iterations * 100
                summary.podium_probabilities[driver] = sum(counts.get(p, 0) for p in [1, 2, 3]) / iterations * 100
                summary.points_probabilities[driver] = sum(counts.get(p, 0) for p in range(1, 11)) / iterations * 100
        
        print(f"[MonteCarlo] Full position simulation complete")
        print(f"[MonteCarlo] Average overtakes per race: {summary.mean_overtakes:.1f}")
        print(f"[MonteCarlo] Average successful: {summary.mean_successful_overtakes:.1f}")
        
        return summary


__all__ = ['MonteCarloParams', 'SafetyCarEvent', 'MonteCarloIteration',
           'MonteCarloSummary', 'MonteCarloSimulator', 'PositionPrediction',
           'FullPositionIteration', 'FullPositionSummary']
