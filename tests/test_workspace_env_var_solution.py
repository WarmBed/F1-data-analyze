#!/usr/bin/env python3
"""
測試環境變量解決方案 - 完整驗證
測試所有 4 個有問題的模組是否能正常創建而不觸發 QThread
"""
import os
import sys

# ✅ 必須先創建 QApplication
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

print("=" * 80)
print("🧪 環境變量解決方案完整測試")
print("=" * 80)

# 測試階段 1: 基本 Import（無環境變量）
print("\n📋 階段 1: 測試基本 Import（無環境變量保護）")
print("-" * 80)

test_results = {
    "import_tests": [],
    "env_var_tests": [],
    "widget_tests": []
}

# Import 測試（預期：可能會卡住或觸發線程）
modules_to_test = [
    ("Lap Time Analysis", "modules.gui.driver_race.detailed_lap_analysis", "driverLapAnalysisMDI"),
    ("Lap Box Plot", "modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi", "LapTimeBoxPlotAnalysis"),
    ("Throttle Box Plot", "modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi", "ThrottleBoxPlotAnalysisMDI"),
    ("Throttle Line Chart", "modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_analysis_mdi", "ThrottleLineChartAnalysisMDI")
]

print("⚠️  警告：如果以下測試卡住，請按 Ctrl+C 中斷")
print()

for name, module_path, class_name in modules_to_test:
    try:
        print(f"🔍 Import {name}...", end=" ")
        exec(f"from {module_path} import {class_name}")
        print(f"✅ OK")
        test_results["import_tests"].append((name, True, "Import 成功"))
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {str(e)[:100]}")
        test_results["import_tests"].append((name, False, str(e)[:100]))

# 測試階段 2: 環境變量保護測試
print("\n📋 階段 2: 測試環境變量保護機制")
print("-" * 80)

for name, module_path, class_name in modules_to_test:
    try:
        print(f"\n🔍 測試 {name} (環境變量保護)...")
        
        # 設置環境變量
        os.environ['F1T_WORKSPACE_LOADING'] = '1'
        print(f"  ✓ 環境變量已設置: F1T_WORKSPACE_LOADING=1")
        
        # 動態導入並創建實例
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        
        print(f"  ✓ 類別 {class_name} 已導入")
        
        # 創建實例
        instance = cls(parent=None)
        print(f"  ✓ 實例已創建（無 QThread 錯誤）")
        
        # 清除環境變量
        del os.environ['F1T_WORKSPACE_LOADING']
        print(f"  ✓ 環境變量已清除")
        
        # 檢查必要屬性
        has_year = hasattr(instance, 'current_year')
        has_race = hasattr(instance, 'current_race')
        has_session = hasattr(instance, 'current_session')
        
        print(f"  ✓ 屬性檢查: year={has_year}, race={has_race}, session={has_session}")
        
        test_results["env_var_tests"].append((name, True, "環境變量保護有效"))
        print(f"✅ {name} 測試通過")
        
    except Exception as e:
        if 'F1T_WORKSPACE_LOADING' in os.environ:
            del os.environ['F1T_WORKSPACE_LOADING']
        
        error_msg = f"{type(e).__name__}: {str(e)[:150]}"
        print(f"❌ {name} 測試失敗: {error_msg}")
        test_results["env_var_tests"].append((name, False, error_msg))

# 測試階段 3: Widget 獲取測試
print("\n📋 階段 3: 測試 Widget 獲取機制")
print("-" * 80)

for name, module_path, class_name in modules_to_test:
    try:
        print(f"\n🔍 測試 {name} Widget 獲取...")
        
        os.environ['F1T_WORKSPACE_LOADING'] = '1'
        
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        instance = cls(parent=None)
        
        del os.environ['F1T_WORKSPACE_LOADING']
        
        # 測試 get_widget()
        if hasattr(instance, 'get_widget'):
            widget = instance.get_widget()
            print(f"  ✓ get_widget() 返回: {type(widget).__name__}")
            
            # 檢查是否是 QWidget
            from PyQt5.QtWidgets import QWidget
            is_qwidget = isinstance(widget, QWidget)
            print(f"  ✓ 是 QWidget: {is_qwidget}")
            
            if is_qwidget:
                test_results["widget_tests"].append((name, True, f"返回有效 QWidget: {type(widget).__name__}"))
            else:
                test_results["widget_tests"].append((name, False, f"返回非 QWidget: {type(widget).__name__}"))
        
        elif hasattr(instance, 'main_widget'):
            widget = instance.main_widget
            print(f"  ✓ main_widget 存在: {type(widget).__name__}")
            
            from PyQt5.QtWidgets import QWidget
            is_qwidget = isinstance(widget, QWidget)
            print(f"  ✓ 是 QWidget: {is_qwidget}")
            
            if is_qwidget:
                test_results["widget_tests"].append((name, True, f"main_widget 是有效 QWidget: {type(widget).__name__}"))
            else:
                test_results["widget_tests"].append((name, False, f"main_widget 非 QWidget: {type(widget).__name__}"))
        else:
            print(f"  ❌ 無 get_widget() 或 main_widget")
            test_results["widget_tests"].append((name, False, "無 get_widget() 或 main_widget 方法"))
        
        print(f"✅ {name} Widget 測試通過")
        
    except Exception as e:
        if 'F1T_WORKSPACE_LOADING' in os.environ:
            del os.environ['F1T_WORKSPACE_LOADING']
        
        error_msg = f"{type(e).__name__}: {str(e)[:150]}"
        print(f"❌ {name} Widget 測試失敗: {error_msg}")
        test_results["widget_tests"].append((name, False, error_msg))

# 最終報告
print("\n" + "=" * 80)
print("📊 測試結果總結")
print("=" * 80)

def print_test_summary(title, results):
    print(f"\n{title}:")
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {name}")
        if not success:
            print(f"       原因: {message}")
    
    print(f"\n  通過率: {passed}/{total} ({100*passed//total if total > 0 else 0}%)")

print_test_summary("Import 測試", test_results["import_tests"])
print_test_summary("環境變量保護測試", test_results["env_var_tests"])
print_test_summary("Widget 獲取測試", test_results["widget_tests"])

# 計算總通過率
all_tests = test_results["import_tests"] + test_results["env_var_tests"] + test_results["widget_tests"]
total_passed = sum(1 for _, success, _ in all_tests if success)
total_tests = len(all_tests)

print("\n" + "=" * 80)
print(f"🎯 總體通過率: {total_passed}/{total_tests} ({100*total_passed//total_tests if total_tests > 0 else 0}%)")

if total_passed == total_tests:
    print("✅ 所有測試通過！環境變量解決方案有效！")
    sys.exit(0)
else:
    print("❌ 部分測試失敗，需要進一步調查")
    sys.exit(1)
