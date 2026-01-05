#!/usr/bin/env python3
"""
Long Run Analysis Widgets

Contains all UI components for the Long Run & Degradation Analysis module.

Widgets:
- StintSelectorWidget: Tab 1 - Auto-detect and select Long Run stints
- LapPickerDialog: Tab 1.5 - Interactive lap selector dialog
- LapChartWidget: Clickable lap time chart with drag selection
- LapTableWidget: Lap details table with checkboxes
- FuelSettingsWidget: Tab 2 - Fuel parameters configuration
- TrackEvolutionWidget: Tab 3 - Track Evolution settings
- DegradationResultsWidget: Tab 4 - Results table and chart
- DegradationChartWidget: Degradation curve chart with driver selection
- CompoundComparisonWidget: Tab 5 - Compound comparison

Author: F1T Team
Date: 2025-12-30
"""

from .stint_selector import StintSelectorWidget
from .fuel_settings import FuelSettingsWidget
from .track_evolution import TrackEvolutionWidget
from .degradation_results import DegradationResultsWidget
from .degradation_chart import DegradationChartWidget
from .compound_comparison import CompoundComparisonWidget

__all__ = [
    'StintSelectorWidget',
    'FuelSettingsWidget',
    'TrackEvolutionWidget',
    'DegradationResultsWidget',
    'DegradationChartWidget',
    'CompoundComparisonWidget',
]
