"""
完整 Workspace Adapter 測試腳本
================================

測試方案 1A + 1B 的完整實施
"""

print("=" * 80)
print("WORKSPACE ADAPTER COMPLETE TEST")
print("=" * 80)

# Test 1: 驗證 workspace_serializer.py 使用正確路徑
print("\n[Test 1] Checking workspace_serializer.py import paths...")

with open('core/workspace_serializer.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    if 'modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module' in content:
        print("  [OK] Laptime path correct")
    else:
        print("  [FAIL] Laptime path incorrect")
    
    if 'modules.gui.lap_box_plot_analysis.lap_box_plot_adapter' in content:
        print("  [OK] LapBoxPlot path correct")
    else:
        print("  [FAIL] LapBoxPlot path incorrect")
    
    if 'modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_adapter' in content:
        print("  [OK] ThrottleBoxPlot path correct")
    else:
        print("  [FAIL] ThrottleBoxPlot path incorrect")
    
    if 'modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_adapter' in content:
        print("  [OK] ThrottleLine path correct")
    else:
        print("  [FAIL] ThrottleLine path incorrect")

# Test 2: 驗證 Adapter 類別存在
print("\n[Test 2] Checking Adapter classes...")

# Check driverLapAnalysisModuleAdapter
with open('modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_module.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'class driverLapAnalysisModuleAdapter' in content:
        print("  [OK] driverLapAnalysisModuleAdapter class exists")
    else:
        print("  [FAIL] driverLapAnalysisModuleAdapter class missing")

# Check other adapters
import os
adapter_files = [
    ('LapBoxPlot', 'modules/gui/lap_box_plot_analysis/lap_box_plot_adapter.py', 'LapTimeBoxPlotAnalysisAdapter'),
    ('ThrottleBoxPlot', 'modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_adapter.py', 'ThrottleBoxPlotAnalysisAdapter'),
    ('ThrottleLine', 'modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_adapter.py', 'ThrottleLineChartAdapter'),
]

for name, filepath, classname in adapter_files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            if f'class {classname}' in f.read():
                print(f"  [OK] {name} adapter exists")
            else:
                print(f"  [FAIL] {name} adapter class missing")
    else:
        print(f"  [FAIL] {name} adapter file missing")

# Test 3: 驗證基類有 workspace 標誌
print("\n[Test 3] Checking UniversalAnalysisMDI base class...")

with open('modules/gui/base/universal_analysis_mdi_base.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    if '_workspace_loading_mode = False' in content:
        print("  [OK] _workspace_loading_mode flag exists in __init__")
    else:
        print("  [FAIL] _workspace_loading_mode flag missing")
    
    if "if getattr(self, '_workspace_loading_mode', False):" in content:
        print("  [OK] _workspace_loading_mode check in _load_data_with_current_parameters")
    else:
        print("  [FAIL] _workspace_loading_mode check missing")

print("\n" + "=" * 80)
print("STATIC TESTS COMPLETE")
print("=" * 80)
print("\nNOTE: Runtime import tests require Qt environment")
print("Please run GUI and test Workspace save/load manually")
