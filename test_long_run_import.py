#!/usr/bin/env python3
"""Test Long Run Analysis import"""
import sys
import traceback

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

print("=" * 50)
print("Testing Long Run Analysis Module Import")
print("=" * 50)

try:
    print("\n[1] Importing LongRunCalculator...")
    from modules.gui.long_run_analysis.long_run_calculator import LongRunCalculator, LapData, StintInfo
    print("    [OK] LongRunCalculator imported")
    
    print("\n[2] Importing LongRunDataLoader...")
    from modules.gui.long_run_analysis.long_run_data_loader import LongRunDataLoader
    print("    [OK] LongRunDataLoader imported")
    
    print("\n[3] Importing widgets...")
    from modules.gui.long_run_analysis.widgets.stint_selector import StintSelectorWidget
    print("    [OK] StintSelectorWidget imported")
    
    from modules.gui.long_run_analysis.widgets.fuel_settings import FuelSettingsWidget
    print("    [OK] FuelSettingsWidget imported")
    
    from modules.gui.long_run_analysis.widgets.track_evolution import TrackEvolutionWidget
    print("    [OK] TrackEvolutionWidget imported")
    
    from modules.gui.long_run_analysis.widgets.degradation_chart import DegradationChartWidget
    print("    [OK] DegradationChartWidget imported")
    
    from modules.gui.long_run_analysis.widgets.degradation_results import DegradationResultsWidget
    print("    [OK] DegradationResultsWidget imported")
    
    from modules.gui.long_run_analysis.widgets.compound_comparison import CompoundComparisonWidget
    print("    [OK] CompoundComparisonWidget imported")
    
    print("\n[4] Importing LongRunAnalysis (main module)...")
    from modules.gui.long_run_analysis import LongRunAnalysis
    print("    [OK] LongRunAnalysis imported")
    
    print("\n" + "=" * 50)
    print("ALL IMPORTS SUCCESSFUL!")
    print("=" * 50)
    
except Exception as e:
    print(f"\n[ERROR] Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)
