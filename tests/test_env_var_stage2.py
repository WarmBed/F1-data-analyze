#!/usr/bin/env python3
"""
環境變量測試 - 階段 2：實例創建測試
"""
import os
import sys
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

print("=" * 80)
print("🧪 環境變量保護 - 實例創建測試")
print("=" * 80)

modules_to_test = [
    ("Lap Time Analysis", "modules.gui.driver_race.detailed_lap_analysis", "driverLapAnalysisMDI"),
    ("Lap Box Plot", "modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi", "LapTimeBoxPlotAnalysis"),
    ("Throttle Box Plot", "modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi", "ThrottleBoxPlotAnalysis"),
    ("Throttle Line Chart", "modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi", "ThrottleLineChartMDI")
]

success_count = 0
total_count = len(modules_to_test)

for name, module_path, class_name in modules_to_test:
    print(f"\n{'='*80}")
    print(f"📦 測試: {name}")
    print(f"{'='*80}")
    
    try:
        # Step 1: 設置環境變量
        print(f"  [1/6] 設置環境變量...")
        os.environ['F1T_WORKSPACE_LOADING'] = '1'
        print(f"       ✓ F1T_WORKSPACE_LOADING = {os.environ.get('F1T_WORKSPACE_LOADING')}")
        
        # Step 2: 導入模組
        print(f"  [2/6] 導入模組: {module_path}")
        module = __import__(module_path, fromlist=[class_name])
        print(f"       ✓ 模組導入成功")
        
        # Step 3: 獲取類別
        print(f"  [3/6] 獲取類別: {class_name}")
        cls = getattr(module, class_name)
        print(f"       ✓ 類別獲取成功: {cls}")
        
        # Step 4: 創建實例（關鍵步驟）
        print(f"  [4/6] 創建實例 (parent=None)...")
        instance = cls(parent=None)
        print(f"       ✓ 實例創建成功: {type(instance).__name__}")
        
        # Step 5: 清除環境變量
        print(f"  [5/6] 清除環境變量...")
        del os.environ['F1T_WORKSPACE_LOADING']
        print(f"       ✓ 環境變量已清除")
        
        # Step 6: 檢查屬性
        print(f"  [6/6] 檢查實例屬性...")
        checks = {
            'current_year': hasattr(instance, 'current_year'),
            'current_race': hasattr(instance, 'current_race'),
            'current_session': hasattr(instance, 'current_session'),
            'get_widget': hasattr(instance, 'get_widget'),
            'main_widget': hasattr(instance, 'main_widget')
        }
        
        for attr, exists in checks.items():
            status = "✓" if exists else "✗"
            print(f"       {status} {attr}: {exists}")
        
        print(f"\n✅ {name} 測試通過！")
        success_count += 1
        
    except Exception as e:
        # 清理環境變量
        if 'F1T_WORKSPACE_LOADING' in os.environ:
            del os.environ['F1T_WORKSPACE_LOADING']
        
        print(f"\n❌ {name} 測試失敗！")
        print(f"   錯誤類型: {type(e).__name__}")
        print(f"   錯誤訊息: {str(e)}")
        
        import traceback
        print(f"\n   完整堆疊追蹤:")
        traceback.print_exc()

# 最終報告
print("\n" + "=" * 80)
print("📊 測試結果總結")
print("=" * 80)
print(f"✅ 通過: {success_count}/{total_count}")
print(f"❌ 失敗: {total_count - success_count}/{total_count}")

if success_count == total_count:
    print("\n🎉 所有模組都能在環境變量保護下正常創建！")
    sys.exit(0)
else:
    print("\n⚠️  部分模組仍有問題，需要進一步修復")
    sys.exit(1)
