#!/usr/bin/env python3
"""
Workspace Adapter 快速測試腳本
============================

測試 4 個新 Adapter 能否正常導入和創建

執行方式：
    python test_workspace_adapters.py
"""

import sys
import traceback

# ✅ 添加 Qt 應用程式環境
from PyQt5.QtWidgets import QApplication

# 創建 QApplication（測試需要）
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)
    print("[OK] QApplication created")

print("=" * 80)
print("Workspace Adapter Test Start")
print("=" * 80)

# ============================================================================
# 階段 1: Import 測試
# ============================================================================
print("\n📦 階段 1: Import 測試")
print("-" * 80)

adapters = []
import_success = 0
import_failed = 0

# 測試 1: driverLapAnalysisModuleAdapter
try:
    from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module import driverLapAnalysisModuleAdapter
    print("✅ driverLapAnalysisModuleAdapter 導入成功")
    adapters.append(("Detailed Lap Analysis", driverLapAnalysisModuleAdapter))
    import_success += 1
except Exception as e:
    print(f"❌ driverLapAnalysisModuleAdapter 導入失敗: {e}")
    traceback.print_exc()
    import_failed += 1

# 測試 2: LapTimeBoxPlotAnalysisAdapter
try:
    from modules.gui.lap_box_plot_analysis.lap_box_plot_adapter import LapTimeBoxPlotAnalysisAdapter
    print("✅ LapTimeBoxPlotAnalysisAdapter 導入成功")
    adapters.append(("Lap Time Box Plot", LapTimeBoxPlotAnalysisAdapter))
    import_success += 1
except Exception as e:
    print(f"❌ LapTimeBoxPlotAnalysisAdapter 導入失敗: {e}")
    traceback.print_exc()
    import_failed += 1

# 測試 3: ThrottleBoxPlotAnalysisAdapter
try:
    from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_adapter import ThrottleBoxPlotAnalysisAdapter
    print("✅ ThrottleBoxPlotAnalysisAdapter 導入成功")
    adapters.append(("Throttle Box Plot", ThrottleBoxPlotAnalysisAdapter))
    import_success += 1
except Exception as e:
    print(f"❌ ThrottleBoxPlotAnalysisAdapter 導入失敗: {e}")
    traceback.print_exc()
    import_failed += 1

# 測試 4: ThrottleLineChartAdapter
try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_adapter import ThrottleLineChartAdapter
    print("✅ ThrottleLineChartAdapter 導入成功")
    adapters.append(("Throttle Line Chart", ThrottleLineChartAdapter))
    import_success += 1
except Exception as e:
    print(f"❌ ThrottleLineChartAdapter 導入失敗: {e}")
    traceback.print_exc()
    import_failed += 1

print(f"\n📊 Import 測試結果: {import_success}/4 成功, {import_failed}/4 失敗")

if import_failed > 0:
    print("\n⚠️  有 Adapter 導入失敗，跳過後續測試")
    sys.exit(1)

# ============================================================================
# 階段 2: Adapter 創建測試（無 GUI）
# ============================================================================
print("\n🔧 階段 2: Adapter 創建測試（無 GUI）")
print("-" * 80)

test_params = {
    'year': 2025,
    'race': 'Japan',
    'session': 'R'
}

creation_success = 0
creation_failed = 0

for name, AdapterClass in adapters:
    try:
        print(f"\n測試創建 {name} Adapter...")
        adapter = AdapterClass(**test_params)
        print(f"  ✅ {name} Adapter 創建成功")
        print(f"  📋 類型: {type(adapter).__name__}")
        
        # 檢查是否有 adapter_version 屬性
        if hasattr(adapter, 'adapter_version'):
            print(f"  📌 Adapter 版本: {adapter.adapter_version}")
        
        # 檢查是否有參數屬性
        if hasattr(adapter, 'current_year'):
            print(f"  📅 Year: {adapter.current_year}")
        if hasattr(adapter, 'current_race'):
            print(f"  🏁 Race: {adapter.current_race}")
        if hasattr(adapter, 'current_session'):
            print(f"  🎯 Session: {adapter.current_session}")
        
        creation_success += 1
        
    except Exception as e:
        print(f"  ❌ {name} Adapter 創建失敗: {e}")
        traceback.print_exc()
        creation_failed += 1

print(f"\n📊 創建測試結果: {creation_success}/4 成功, {creation_failed}/4 失敗")

# ============================================================================
# 階段 3: 基類標誌測試
# ============================================================================
print("\n🛡️  階段 3: 基類標誌測試")
print("-" * 80)

try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI
    
    # 檢查 _workspace_loading_mode 是否存在
    print("檢查 UniversalAnalysisMDI 基類...")
    
    # 讀取源碼檢查
    import inspect
    source = inspect.getsource(UniversalAnalysisMDI.__init__)
    
    if '_workspace_loading_mode' in source:
        print("  ✅ 基類包含 _workspace_loading_mode 標誌")
    else:
        print("  ⚠️  基類缺少 _workspace_loading_mode 標誌")
    
    # 檢查 _load_data_with_current_parameters
    if hasattr(UniversalAnalysisMDI, '_load_data_with_current_parameters'):
        source2 = inspect.getsource(UniversalAnalysisMDI._load_data_with_current_parameters)
        if '_workspace_loading_mode' in source2:
            print("  ✅ _load_data_with_current_parameters 包含標誌檢查")
        else:
            print("  ⚠️  _load_data_with_current_parameters 缺少標誌檢查")
    
except Exception as e:
    print(f"  ❌ 基類檢查失敗: {e}")
    traceback.print_exc()

# ============================================================================
# 總結
# ============================================================================
print("\n" + "=" * 80)
print("🏆 測試總結")
print("=" * 80)

total_tests = 4
passed_tests = import_success if import_success == creation_success else 0

if passed_tests == total_tests:
    print(f"✅ 所有測試通過！({passed_tests}/{total_tests})")
    print("\n✨ 4 個 Adapter 已準備好用於 Workspace 系統")
    print("\n📝 下一步：")
    print("  1. 啟動 F1T GUI")
    print("  2. 創建包含這 4 個模組的 Workspace")
    print("  3. 保存並重新載入 Workspace")
    print("  4. 驗證無 QThread 崩潰")
    sys.exit(0)
else:
    print(f"⚠️  有測試失敗 ({passed_tests}/{total_tests})")
    print("\n🔍 請檢查上方錯誤訊息")
    sys.exit(1)
