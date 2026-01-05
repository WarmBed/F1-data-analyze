#!/usr/bin/env python3
"""
Strategy Optimizer

Generates and ranks optimal race strategies based on simulation results.

Author: F1T Team
Date: 2025-12-30
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Iterator
from itertools import product
import copy

from .lap_simulator import (
    Compound, Stint, SimulationParams, 
    LapSimulator, StrategySimulationResult
)


@dataclass
class StrategyConstraints:
    """Constraints for strategy generation"""
    # Must use compounds
    mandatory_compounds: List[Compound] = None
    
    # Available compounds
    available_compounds: List[Compound] = None
    
    # Stint length limits
    min_stint_length: int = 5
    max_stint_length: int = 45
    
    # Stop limits
    min_stops: int = 1
    max_stops: int = 3
    
    # First stint constraints
    first_stint_min: int = None  # Min laps for first stint
    first_stint_max: int = None  # Max laps for first stint
    
    # F1 Rule: Must use at least 2 different compounds in a dry race
    require_two_compounds: bool = True
    
    def __post_init__(self):
        if self.mandatory_compounds is None:
            self.mandatory_compounds = []
        if self.available_compounds is None:
            self.available_compounds = [Compound.SOFT, Compound.MEDIUM, Compound.HARD]


class StrategyOptimizer:
    """
    Strategy generation and optimization engine.
    
    Generates all viable strategies within given constraints,
    simulates each one, and ranks by total race time.
    
    Usage:
        params = SimulationParams(race_laps=53, ...)
        optimizer = StrategyOptimizer(params)
        
        constraints = StrategyConstraints(
            mandatory_compounds=[Compound.MEDIUM],
            min_stops=1,
            max_stops=2
        )
        
        results = optimizer.find_optimal_strategies(constraints)
        
        for r in results[:5]:
            print(f"{r.strategy_name}: {r.get_stint_notation()} = {r.total_time_formatted}")
    """
    
    def __init__(self, params: SimulationParams):
        """
        Initialize StrategyOptimizer.
        
        Args:
            params: Simulation parameters
        """
        self.params = params
        self.simulator = LapSimulator(params)
    
    def generate_strategies(
        self,
        constraints: StrategyConstraints = None
    ) -> Iterator[List[Stint]]:
        """
        Generate all viable strategies within constraints.
        
        Args:
            constraints: Strategy constraints
        
        Yields:
            List of Stint objects representing each strategy
        """
        if constraints is None:
            constraints = StrategyConstraints()
        
        race_laps = self.params.race_laps
        compounds = constraints.available_compounds
        
        # Generate for each number of stops
        for num_stops in range(constraints.min_stops, constraints.max_stops + 1):
            num_stints = num_stops + 1
            
            # Generate all compound combinations
            for compound_combo in product(compounds, repeat=num_stints):
                # F1 Rule: Must use at least 2 different compounds (dry race)
                if constraints.require_two_compounds:
                    unique_compounds = set(compound_combo)
                    if len(unique_compounds) < 2:
                        continue  # Skip single-compound strategies
                
                # Check mandatory compounds
                if constraints.mandatory_compounds:
                    if not all(c in compound_combo for c in constraints.mandatory_compounds):
                        continue
                
                # Generate stint length combinations
                for stint_lengths in self._generate_stint_lengths(
                    race_laps, 
                    num_stints, 
                    constraints
                ):
                    stints = []
                    start_lap = 1
                    
                    for i, (compound, length) in enumerate(zip(compound_combo, stint_lengths)):
                        stint = Stint(
                            compound=compound,
                            laps=length,
                            start_lap=start_lap
                        )
                        stints.append(stint)
                        start_lap += length
                    
                    yield stints
    
    def _generate_stint_lengths(
        self,
        total_laps: int,
        num_stints: int,
        constraints: StrategyConstraints
    ) -> Iterator[List[int]]:
        """
        Generate valid stint length combinations.
        
        Uses step of 3 laps to reduce combinations while maintaining coverage.
        """
        min_len = constraints.min_stint_length
        max_len = min(constraints.max_stint_length, total_laps - (num_stints - 1) * min_len)
        
        # For first stint, apply special constraints if set
        first_min = constraints.first_stint_min or min_len
        first_max = constraints.first_stint_max or max_len
        
        # Recursive generator
        def generate_recursive(
            remaining_laps: int, 
            remaining_stints: int,
            is_first: bool = False
        ) -> Iterator[List[int]]:
            if remaining_stints == 1:
                # Last stint takes all remaining laps
                if min_len <= remaining_laps <= max_len:
                    yield [remaining_laps]
                return
            
            # Determine range for this stint
            if is_first:
                stint_min = first_min
                stint_max = first_max
            else:
                stint_min = min_len
                stint_max = max_len
            
            # Calculate actual bounds
            actual_min = max(stint_min, remaining_laps - (remaining_stints - 1) * max_len)
            actual_max = min(stint_max, remaining_laps - (remaining_stints - 1) * min_len)
            
            # Generate with step of 3 laps (optimization)
            for length in range(actual_min, actual_max + 1, 3):
                for rest in generate_recursive(
                    remaining_laps - length,
                    remaining_stints - 1,
                    is_first=False
                ):
                    yield [length] + rest
        
        yield from generate_recursive(total_laps, num_stints, is_first=True)
    
    def find_optimal_strategies(
        self,
        constraints: StrategyConstraints = None,
        top_n: int = 10,
        include_duplicates: bool = False
    ) -> List[StrategySimulationResult]:
        """
        Find optimal strategies within constraints.
        
        Args:
            constraints: Strategy constraints
            top_n: Number of top strategies to return
            include_duplicates: Include strategies with same notation but different timing
        
        Returns:
            List of simulation results, sorted by total time
        """
        all_results: List[StrategySimulationResult] = []
        seen_notations: set = set()
        
        for stints in self.generate_strategies(constraints):
            result = self.simulator.simulate_strategy(stints)
            
            if not include_duplicates:
                notation = result.get_stint_notation()
                if notation in seen_notations:
                    # Only keep the faster version
                    for i, existing in enumerate(all_results):
                        if existing.get_stint_notation() == notation:
                            if result.total_time < existing.total_time:
                                all_results[i] = result
                            break
                    continue
                seen_notations.add(notation)
            
            all_results.append(result)
        
        # Sort by total time
        all_results.sort(key=lambda r: r.total_time)
        
        # Take top N
        top_results = all_results[:top_n]
        
        # Rename based on ranking
        for i, result in enumerate(top_results):
            result.strategy_name = f"Plan {chr(65+i)}"
        
        return top_results
    
    def compare_strategies(
        self,
        strategies: List[List[Stint]]
    ) -> List[StrategySimulationResult]:
        """
        Compare specific strategies (user-defined).
        
        Args:
            strategies: List of stint lists to compare
        
        Returns:
            Simulation results sorted by total time
        """
        return self.simulator.simulate_multiple(strategies)
    
    def calculate_undercut_overcut_window(
        self,
        our_strategy: List[Stint],
        opponent_strategy: List[Stint],
        current_gap: float = 0.0
    ) -> Dict:
        """
        Calculate undercut and overcut opportunity windows.
        
        Args:
            our_strategy: Our planned strategy
            opponent_strategy: Opponent's expected strategy
            current_gap: Current time gap to opponent (positive = behind)
        
        Returns:
            Dictionary with undercut/overcut analysis
        """
        our_result = self.simulator.simulate_strategy(our_strategy)
        opponent_result = self.simulator.simulate_strategy(opponent_strategy)
        
        # Find opponent's pit laps
        opponent_pit_laps = opponent_result.pit_laps
        
        analysis = {
            'opponent_pit_laps': opponent_pit_laps,
            'undercut_windows': [],
            'overcut_windows': [],
            'cumulative_delta': [],
        }
        
        # Calculate cumulative time delta at each lap
        cumulative_delta = 0.0
        for lap in range(1, self.params.race_laps + 1):
            our_lap_time = our_result.lap_results[lap - 1].net_time
            opp_lap_time = opponent_result.lap_results[lap - 1].net_time
            delta = our_lap_time - opp_lap_time
            cumulative_delta += delta
            
            analysis['cumulative_delta'].append({
                'lap': lap,
                'delta': round(cumulative_delta, 3),
                'gap': round(current_gap + cumulative_delta, 3)
            })
        
        # Analyze each opponent pit lap for undercut/overcut
        for pit_lap in opponent_pit_laps:
            # Undercut window: pit 1-3 laps before opponent
            undercut_start = max(1, pit_lap - 3)
            undercut_end = pit_lap - 1
            
            if undercut_end >= undercut_start:
                # Calculate gain from undercut
                undercut_gain = self._estimate_undercut_gain(
                    pit_lap - 1,  # Our pit lap
                    pit_lap,      # Their pit lap
                    our_result,
                    opponent_result
                )
                
                analysis['undercut_windows'].append({
                    'opponent_pit': pit_lap,
                    'window': (undercut_start, undercut_end),
                    'optimal_lap': undercut_end,
                    'estimated_gain': round(undercut_gain, 3),
                    'recommendation': 'STRONG' if undercut_gain > 0.5 else 'MARGINAL'
                })
            
            # Overcut window: stay out 1-3 laps after opponent pits
            overcut_start = pit_lap + 1
            overcut_end = min(self.params.race_laps, pit_lap + 3)
            
            if overcut_end > overcut_start:
                overcut_gain = self._estimate_overcut_gain(
                    pit_lap + 2,  # Our pit lap
                    pit_lap,      # Their pit lap
                    our_result,
                    opponent_result
                )
                
                analysis['overcut_windows'].append({
                    'opponent_pit': pit_lap,
                    'window': (overcut_start, overcut_end),
                    'optimal_lap': overcut_start + 1,
                    'estimated_gain': round(overcut_gain, 3),
                    'recommendation': 'STRONG' if overcut_gain > 0.5 else 'MARGINAL'
                })
        
        return analysis
    
    def _estimate_undercut_gain(
        self,
        our_pit_lap: int,
        their_pit_lap: int,
        our_result: StrategySimulationResult,
        opponent_result: StrategySimulationResult
    ) -> float:
        """Estimate time gained from undercut."""
        # Undercut gains:
        # 1. Fresh tire advantage on out-lap
        # 2. They're on old tires for extra lap
        
        if our_pit_lap >= self.params.race_laps or their_pit_lap > self.params.race_laps:
            return 0.0
        
        # Their lap time on old tires (the lap they should have pitted)
        their_old_tire_lap = opponent_result.lap_results[our_pit_lap - 1].net_time
        
        # Our lap time on new tires (after pit)
        our_new_tire_lap = self.params.base_lap_time  # Fresh tire baseline
        
        # Pit loss difference (we pit earlier, they pit later)
        pit_delta = 0  # Same pit loss for both
        
        # Estimated gain = their old tire - our new tire
        gain = their_old_tire_lap - our_new_tire_lap - 1.5  # -1.5 for outlap disadvantage
        
        return max(0, gain)
    
    def _estimate_overcut_gain(
        self,
        our_pit_lap: int,
        their_pit_lap: int,
        our_result: StrategySimulationResult,
        opponent_result: StrategySimulationResult
    ) -> float:
        """Estimate time gained from overcut."""
        # Overcut gains:
        # 1. They have slow out-lap
        # 2. Track evolution (not modeled here)
        
        if their_pit_lap >= self.params.race_laps or our_pit_lap > self.params.race_laps:
            return 0.0
        
        # Their out-lap (typically 2-3s slower)
        their_outlap_penalty = 2.5
        
        # Our in-lap on old tires vs their in-lap
        our_old_tire = our_result.lap_results[their_pit_lap - 1].net_time
        their_outlap = opponent_result.lap_results[their_pit_lap].net_time + their_outlap_penalty
        
        # Estimated gain
        gain = their_outlap - our_old_tire - 1.0  # -1.0 for our eventual outlap
        
        return max(0, gain)


__all__ = ['StrategyConstraints', 'StrategyOptimizer']
