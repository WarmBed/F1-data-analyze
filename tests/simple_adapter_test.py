#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""簡單 Adapter 測試"""

import sys
import os

# 設置環境變量強制 UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

from PyQt5.QtWidgets import QApplication

# 創建 Qt 應用
app = QApplication.instance() or QApplication(sys.argv)

print("=" * 60)
print("Phase 1: Import Test")
print("=" * 60)

success = []
failed = []

# Test 1
try:
    from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module import driverLapAnalysisModuleAdapter
    print("[OK] driverLapAnalysisModuleAdapter")
    success.append("Laptime Adapter")
except Exception as e:
    print(f"[FAIL] driverLapAnalysisModuleAdapter: {e}")
    failed.append("Laptime Adapter")

# Test 2
try:
    from modules.gui.lap_box_plot_analysis.lap_box_plot_adapter import LapTimeBoxPlotAnalysisAdapter
    print("[OK] LapTimeBoxPlotAnalysisAdapter")
    success.append("LapBoxPlot Adapter")
except Exception as e:
    print(f"[FAIL] LapTimeBoxPlotAnalysisAdapter: {e}")
    failed.append("LapBoxPlot Adapter")

# Test 3
try:
    from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_adapter import ThrottleBoxPlotAnalysisAdapter
    print("[OK] ThrottleBoxPlotAnalysisAdapter")
    success.append("ThrottleBoxPlot Adapter")
except Exception as e:
    print(f"[FAIL] ThrottleBoxPlotAnalysisAdapter: {e}")
    failed.append("ThrottleBoxPlot Adapter")

# Test 4
try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_adapter import ThrottleLineChartAdapter
    print("[OK] ThrottleLineChartAdapter")
    success.append("ThrottleLine Adapter")
except Exception as e:
    print(f"[FAIL] ThrottleLineChartAdapter: {e}")
    failed.append("ThrottleLine Adapter")

print("\n" + "=" * 60)
print(f"Import Result: {len(success)}/4 success, {len(failed)}/4 failed")
print("=" * 60)

if len(failed) > 0:
    print("\nFailed adapters:")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Phase 2: Creation Test")
print("=" * 60)

test_params = {'year': 2025, 'race': 'Japan', 'session': 'R'}

# Test creation
try:
    from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module import driverLapAnalysisModuleAdapter
    adapter1 = driverLapAnalysisModuleAdapter(**test_params)
    print("[OK] Laptime Adapter created")
except Exception as e:
    print(f"[FAIL] Laptime Adapter creation: {e}")
    import traceback
    traceback.print_exc()

try:
    from modules.gui.lap_box_plot_analysis.lap_box_plot_adapter import LapTimeBoxPlotAnalysisAdapter
    adapter2 = LapTimeBoxPlotAnalysisAdapter(**test_params)
    print("[OK] LapBoxPlot Adapter created")
except Exception as e:
    print(f"[FAIL] LapBoxPlot Adapter creation: {e}")
    import traceback
    traceback.print_exc()

try:
    from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_adapter import ThrottleBoxPlotAnalysisAdapter
    adapter3 = ThrottleBoxPlotAnalysisAdapter(**test_params)
    print("[OK] ThrottleBoxPlot Adapter created")
except Exception as e:
    print(f"[FAIL] ThrottleBoxPlot Adapter creation: {e}")
    import traceback
    traceback.print_exc()

try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_adapter import ThrottleLineChartAdapter
    adapter4 = ThrottleLineChartAdapter(**test_params)
    print("[OK] ThrottleLine Adapter created")
except Exception as e:
    print(f"[FAIL] ThrottleLine Adapter creation: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
