#!/usr/bin/env python3
"""測試 Adapter 的 get_widget() 返回類型"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget

app = QApplication.instance() or QApplication(sys.argv)

print("=" * 80)
print("Testing Adapter get_widget() return types")
print("=" * 80)

test_params = {'year': 2025, 'race': 'Japan', 'session': 'R'}

# Test 1: driverLapAnalysisModuleAdapter
print("\n[Test 1] driverLapAnalysisModuleAdapter")
try:
    print("  Step 1: Importing...")
    from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module import driverLapAnalysisModuleAdapter
    print("  Step 2: Creating adapter...")
    adapter = driverLapAnalysisModuleAdapter(**test_params)
    print("  Step 3: Getting widget...")
    widget = adapter.get_widget()
    print(f"  Widget type: {type(widget)}")
    print(f"  Is QWidget: {isinstance(widget, QWidget)}")
    if isinstance(widget, QWidget):
        print("  [PASS] Returns QWidget")
    else:
        print("  [FAIL] Does NOT return QWidget")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

# Exit early to isolate issue
print("\nExiting after Test 1")
sys.exit(0)

# Test 2: LapTimeBoxPlotAnalysisAdapter
print("\n[Test 2] LapTimeBoxPlotAnalysisAdapter")
try:
    from modules.gui.lap_box_plot_analysis.lap_box_plot_adapter import LapTimeBoxPlotAnalysisAdapter
    adapter = LapTimeBoxPlotAnalysisAdapter(**test_params)
    widget = adapter.get_widget()
    print(f"  Widget type: {type(widget)}")
    print(f"  Is QWidget: {isinstance(widget, QWidget)}")
    if isinstance(widget, QWidget):
        print("  [PASS] Returns QWidget")
    else:
        print("  [FAIL] Does NOT return QWidget")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

# Test 3: ThrottleBoxPlotAnalysisAdapter
print("\n[Test 3] ThrottleBoxPlotAnalysisAdapter")
try:
    from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_adapter import ThrottleBoxPlotAnalysisAdapter
    adapter = ThrottleBoxPlotAnalysisAdapter(**test_params)
    widget = adapter.get_widget()
    print(f"  Widget type: {type(widget)}")
    print(f"  Is QWidget: {isinstance(widget, QWidget)}")
    if isinstance(widget, QWidget):
        print("  [PASS] Returns QWidget")
    else:
        print("  [FAIL] Does NOT return QWidget")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

# Test 4: ThrottleLineChartAdapter
print("\n[Test 4] ThrottleLineChartAdapter")
try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_adapter import ThrottleLineChartAdapter
    adapter = ThrottleLineChartAdapter(**test_params)
    widget = adapter.get_widget()
    print(f"  Widget type: {type(widget)}")
    print(f"  Is QWidget: {isinstance(widget, QWidget)}")
    if isinstance(widget, QWidget):
        print("  [PASS] Returns QWidget")
    else:
        print("  [FAIL] Does NOT return QWidget")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
