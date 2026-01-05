#!/usr/bin/env python3
"""Test strategy optimizer across all 2025 tracks"""

from strategy_simulator.core.config_loader import ConfigLoader
from strategy_simulator.core.strategy_optimizer import StrategyOptimizer, StrategyConstraints
from strategy_simulator.core.lap_simulator import SimulationParams, Compound

loader = ConfigLoader()
tracks = ['Bahrain', 'Jeddah', 'Melbourne', 'Suzuka', 'Shanghai', 'Miami', 
          'Monaco', 'Montreal', 'Barcelona', 'Spielberg', 'Silverstone',
          'Hungaroring', 'Spa', 'Zandvoort', 'Monza', 'Singapore', 'Austin',
          'Mexico City', 'Interlagos', 'Las Vegas', 'Lusail', 'Yas Marina']

print(f"{'Track':14} | Laps | Best Strategy      | Stops | Total Time")
print('-' * 75)

for track in tracks:
    try:
        config = loader.get_track_config(track)
        
        params = SimulationParams(
            race_laps=config.typical_race_laps,
            base_lap_time=config.base_lap_time,
            pit_loss_green=config.pit_loss_green,
            pit_loss_sc=config.pit_loss_sc,
            deg_rates={
                Compound.SOFT: config.deg_soft,
                Compound.MEDIUM: config.deg_medium,
                Compound.HARD: config.deg_hard,
            },
            compound_deltas={
                Compound.SOFT: -0.8,
                Compound.MEDIUM: 0.0,
                Compound.HARD: 0.5,
            },
            fuel_kg_per_lap=config.fuel_kg_per_lap,
            fuel_effect_coefficient=config.fuel_effect_coefficient,
            start_fuel_kg=config.start_fuel_kg,
        )
        
        optimizer = StrategyOptimizer(params)
        constraints = StrategyConstraints(
            available_compounds=[Compound.SOFT, Compound.MEDIUM, Compound.HARD],
            min_stops=1,
            max_stops=2,
        )
        
        results = optimizer.find_optimal_strategies(constraints)
        
        if results:
            best = results[0]
            stints_str = best.get_stint_notation()
            print(f'{track:14} | {config.typical_race_laps:4} | {stints_str:18} | {best.num_stops:5} | {best.total_time_formatted}')
        else:
            print(f'{track:14} | {config.typical_race_laps:4} | No strategies generated')
    except Exception as e:
        import traceback
        print(f'{track:14} | ERROR: {str(e)[:50]}')
        traceback.print_exc()
