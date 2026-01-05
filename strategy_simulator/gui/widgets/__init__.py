#!/usr/bin/env python3
"""
Custom widgets for Race Strategy Simulator.

New widgets (2026-01-04):
- RaceAnimationWidget: Lap-by-lap race simulation animation
- MonteCarloChartWidget: MC results visualization (histograms, box plots)
- SCEventInjectorWidget: Manual SC/VSC event injection

Legacy widgets:
- StrategyChart: Strategy visualization
- GapTimeline: Gap evolution timeline
"""

# New visualization widgets
from .race_animation import RaceAnimationWidget
from .monte_carlo_chart import MonteCarloChartWidget
from .sc_event_injector import SCEventInjectorWidget

__all__ = [
    'RaceAnimationWidget',
    'MonteCarloChartWidget', 
    'SCEventInjectorWidget',
]
