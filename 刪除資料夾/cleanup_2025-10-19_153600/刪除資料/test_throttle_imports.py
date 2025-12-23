# -*- coding: utf-8 -*-
"""Simple import test for Throttle Line Chart module"""

import sys
import os

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("="*60)
print("Throttle Line Chart Import Test")
print("="*60)

# Test 1: Data Loader
print("\n[1] Testing ThrottleLineChartDataLoader...")
try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_data_loader import ThrottleLineChartDataLoader
    print("    [OK] Import successful")
    loader = ThrottleLineChartDataLoader()
    print(f"    [OK] Instance created (type={loader.analysis_type})")
except Exception as e:
    print(f"    [FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Chart Widgets
print("\n[2] Testing ThrottleDurationChartWidget...")
try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_duration_chart_widget import ThrottleDurationChartWidget
    print("    [OK] Import successful")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

print("\n[3] Testing LapTimeChartWidget...")
try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.lap_time_chart_widget import LapTimeChartWidget
    print("    [OK] Import successful")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

# Test 3: MDI Container
print("\n[4] Testing ThrottleLineChartMDI...")
try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi import ThrottleLineChartMDI
    print("    [OK] Import successful")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

# Test 4: Module Interface
print("\n[5] Testing ThrottleLineChartModule...")
try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import ThrottleLineChartModule
    print("    [OK] Import successful")
    module = ThrottleLineChartModule()
    print(f"    [OK] Instance created")
    print(f"    [INFO] Default size: {module.get_default_size()}")
    print(f"    [INFO] Window title: {module.get_window_title()}")
except Exception as e:
    print(f"    [FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("ALL TESTS PASSED!")
print("="*60)
print("\nNext steps:")
print("  1. Run GUI: python f1t_gui_main.py")
print("  2. Select race and session")
print("  3. Click 'Throttle Analysis' -> 'Throttle Line Chart'")
