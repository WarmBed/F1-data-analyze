#!/usr/bin/env python3
"""
測試 Workspace 序列化識別 - 診斷為什麼某些模組無法被識別
"""
import sys
from PyQt5.QtWidgets import QApplication

print("=" * 80)
print("🔍 Workspace 序列化診斷測試")
print("=" * 80)

app = QApplication(sys.argv)

# 測試 1: 檢查 driverLapAnalysisMDI 的 analysis_type
print("\n[測試 1] 檢查 driverLapAnalysisMDI 的 analysis_type")
print("-" * 80)

try:
    import os
    os.environ['F1T_WORKSPACE_LOADING'] = '1'
    
    from modules.gui.driver_race.detailed_lap_analysis import driverLapAnalysisMDI
    
    module = driverLapAnalysisMDI(parent=None)
    
    del os.environ['F1T_WORKSPACE_LOADING']
    
    print(f"✓ 模組創建成功")
    print(f"✓ 類別: {module.__class__.__name__}")
    print(f"✓ 繼承鏈: {[c.__name__ for c in module.__class__.__mro__]}")
    
    if hasattr(module, 'analysis_type'):
        print(f"✅ analysis_type 存在: '{module.analysis_type}'")
    else:
        print(f"❌ analysis_type 不存在")
    
    if hasattr(module, 'analysis_module'):
        print(f"✓ analysis_module 存在: {module.analysis_module}")
    else:
        print(f"⚠️  analysis_module 不存在（這是正常的，只有 Adapter 才有）")
    
    print(f"✓ 所有屬性: {[a for a in dir(module) if not a.startswith('_')][:20]}")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 2: 檢查 AllDriversStraightLineSpeedMDI 的 analysis_type
print("\n[測試 2] 檢查 AllDriversStraightLineSpeedMDI 的 analysis_type")
print("-" * 80)

try:
    os.environ['F1T_WORKSPACE_LOADING'] = '1'
    
    from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi import AllDriversStraightLineSpeedMDI
    
    module2 = AllDriversStraightLineSpeedMDI(parent=None)
    
    del os.environ['F1T_WORKSPACE_LOADING']
    
    print(f"✓ 模組創建成功")
    print(f"✓ 類別: {module2.__class__.__name__}")
    
    if hasattr(module2, 'analysis_type'):
        print(f"✅ analysis_type 存在: '{module2.analysis_type}'")
    else:
        print(f"❌ analysis_type 不存在")
    
    if hasattr(module2, 'analysis_module'):
        print(f"✓ analysis_module 存在: {module2.analysis_module}")
    else:
        print(f"⚠️  analysis_module 不存在（這是正常的，只有 Adapter 才有）")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 3: 比較兩者的差異
print("\n[測試 3] 比較兩者的差異")
print("-" * 80)

module1_attrs = set(dir(module))
module2_attrs = set(dir(module2))

only_in_module1 = module1_attrs - module2_attrs
only_in_module2 = module2_attrs - module1_attrs

print(f"只有 driverLapAnalysisMDI 有的屬性: {[a for a in only_in_module1 if not a.startswith('_')][:10]}")
print(f"只有 AllDriversStraightLineSpeedMDI 有的屬性: {[a for a in only_in_module2 if not a.startswith('_')][:10]}")

print("\n" + "=" * 80)
print("✅ 診斷測試完成")
print("=" * 80)

sys.exit(0)
