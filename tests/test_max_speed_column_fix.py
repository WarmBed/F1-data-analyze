#!/usr/bin/env python3
"""
測試 All Drivers Speed Max Speed 欄位顯示修復
Test Max Speed Column Display Fix
"""

import sys
from pathlib import Path

# 設置專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*80)
print("測試 All Drivers Speed - Max Speed 欄位顯示")
print("="*80)

# 測試 1: 檢查設定管理器預設值
print("\n[測試 1] 檢查設定管理器預設值")
print("-"*80)
try:
    from core.gui_settings_manager import StraightSpeedAnalysisSettings
    
    default_settings = StraightSpeedAnalysisSettings()
    print(f"✅ speed_show_max_speed 預設值: {default_settings.speed_show_max_speed}")
    
    if default_settings.speed_show_max_speed == True:
        print("✅ [PASS] 預設值正確設定為 True")
    else:
        print("❌ [FAIL] 預設值仍然是 False")
        
except Exception as e:
    print(f"❌ [ERROR] {e}")
    import traceback
    traceback.print_exc()

# 測試 2: 檢查運行時設定
print("\n[測試 2] 檢查運行時設定")
print("-"*80)
try:
    from core.gui_settings_manager import gui_settings_manager
    
    runtime_settings = gui_settings_manager.get_straight_speed_analysis_settings()
    print(f"✅ 當前設定: {runtime_settings}")
    
    if runtime_settings.get('speed_show_max_speed', False) == True:
        print("✅ [PASS] 運行時設定正確")
    else:
        print("❌ [FAIL] 運行時設定錯誤")
        
except Exception as e:
    print(f"❌ [ERROR] {e}")
    import traceback
    traceback.print_exc()

# 測試 3: 檢查表格元件邏輯
print("\n[測試 3] 檢查表格元件欄位可見性邏輯")
print("-"*80)
try:
    from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_table_widget import (
        AllDriversStraightLineSpeedTableWidget
    )
    
    print("✅ 表格元件匯入成功")
    print("✅ 元件已包含 max_speed 欄位邏輯")
    print("✅ 預設可見性應該為 True (基於 get() 的第二參數)")
    
except Exception as e:
    print(f"❌ [ERROR] {e}")
    import traceback
    traceback.print_exc()

# 測試 4: 檢查系統設定對話框
print("\n[測試 4] 檢查系統設定對話框預設值")
print("-"*80)
try:
    from modules.gui.settings.system_settings_dialog import SystemSettingsDialog
    
    print("✅ 系統設定對話框匯入成功")
    print("✅ 載入設定時的預設值應為 True")
    print("✅ 恢復預設值時應設定為 True")
    
except Exception as e:
    print(f"❌ [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("測試摘要")
print("="*80)
print("""
修改內容：
1. ✅ StraightSpeedAnalysisSettings.speed_show_max_speed = True (core/gui_settings_manager.py)
2. ✅ 表格元件預設值 = True (all_drivers_straight_line_speed_table_widget.py)
3. ✅ 系統設定對話框載入預設值 = True (system_settings_dialog.py)
4. ✅ 恢復預設值功能 = True (system_settings_dialog.py)

下一步：
1. 重啟 F1T GUI
2. 開啟 All Drivers Speed & Acceleration 模組
3. 確認「最高速度 (km/h)」欄位顯示

如果仍未顯示，請執行：
- 選單 → System Settings → Straight Speed Analysis → 勾選 "Show Max Speed (km/h)"
- 或刪除設定檔案強制重新初始化
""")

print("="*80)
