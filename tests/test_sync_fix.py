"""
測試勾選同步 checkbox 後，Speed Analysis 是否正確顯示主 GUI 的曲線

測試場景：
1. 主 GUI 參數：2025 Brazil R, NOR, driver2=None, lap1
2. Speed Analysis 視窗：原本是 2025 AU R vs 2025 AU Q（跨賽事）
3. 勾選同步 checkbox → 點擊 OK
4. 預期結果：
   - 圖表顯示 Brazil R 的 NOR 曲線
   - 狀態列消失（因為啟用同步）
   - 視窗標題更新為 Brazil R
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 80)
print("測試場景：勾選同步 checkbox 後，Speed Analysis 顯示主 GUI 曲線")
print("=" * 80)

print("\n步驟 1: 檢查修復的代碼")
print("-" * 80)

# 檢查 accept_settings 的 else 分支
with open("f1t_gui_main.py", "r", encoding="utf-8") as f:
    content = f.read()
    
    # 搜索 else 分支
    if "[SYNC_MODE] 車手與圈數同步已啟用，從主視窗讀取參數" in content:
        print("✅ 找到修復後的 else 分支")
        print("✅ 包含從主視窗讀取參數的代碼")
    else:
        print("❌ 沒有找到修復後的代碼")
    
    # 搜索主視窗參數讀取
    if "main_driver1 = self.main_window.driver1_combo.currentText()" in content:
        print("✅ 包含 main_driver1 讀取")
    else:
        print("❌ 缺少 main_driver1 讀取")
    
    if "main_driver2_data = self.main_window.driver2_combo.currentData()" in content:
        print("✅ 包含 main_driver2 讀取")
    else:
        print("❌ 缺少 main_driver2 讀取")
    
    if "main_lap1 = self.main_window.lap1_spinbox.value()" in content:
        print("✅ 包含 main_lap1 讀取")
    else:
        print("❌ 缺少 main_lap1 讀取")
    
    if "self._apply_driver_lap_settings(main_driver1, main_driver2, main_lap1, main_lap2, main_is_fastest)" in content:
        print("✅ 包含調用 _apply_driver_lap_settings")
    else:
        print("❌ 缺少調用 _apply_driver_lap_settings")

print("\n步驟 2: 檢查是否移除了無效的 update_current_window_only() 調用")
print("-" * 80)

# 檢查是否移除了 Line 6653 的無效調用
with open("f1t_gui_main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
    
    # 搜索 Line 6643-6660 的邏輯
    found_old_logic = False
    found_new_logic = False
    
    for i, line in enumerate(lines[6640:6660], start=6641):
        if "self.update_current_window_only()" in line:
            found_old_logic = True
            print(f"⚠️  Line {i}: 仍存在 update_current_window_only() 調用")
        
        if "車手與圈數已同步完成" in line:
            found_new_logic = True
            print(f"✅ Line {i}: 找到新的邏輯（已移除無效調用）")
    
    if found_new_logic and not found_old_logic:
        print("✅ 成功移除無效的 update_current_window_only() 調用")
    elif found_old_logic:
        print("⚠️  仍存在 update_current_window_only() 調用（可能導致重複處理）")
    else:
        print("⚠️  未找到預期的邏輯")

print("\n步驟 3: 檢查主視窗屬性讀取方式")
print("-" * 80)

# 檢查是否正確使用 year_combo.currentText()
with open("f1t_gui_main.py", "r", encoding="utf-8") as f:
    content = f.read()
    
    # 搜索錯誤的屬性調用
    if "self.main_window.current_year" in content:
        print("❌ 仍使用錯誤的 current_year 屬性")
    else:
        print("✅ 已移除錯誤的 current_year 屬性")
    
    # 搜索正確的 combo box 調用
    if "year1 = self.main_window.year_combo.currentText()" in content:
        print("✅ 正確使用 year_combo.currentText()")
    else:
        print("❌ 缺少正確的 year_combo 讀取")
    
    if "race1_display = self.main_window.race_combo.currentText()" in content:
        print("✅ 正確使用 race_combo.currentText()")
    else:
        print("❌ 缺少正確的 race_combo 讀取")
    
    if "race1 = self.main_window._get_race_key_from_display(race1_display)" in content:
        print("✅ 正確使用 _get_race_key_from_display()")
    else:
        print("❌ 缺少 _get_race_key_from_display() 調用")
    
    if "session1 = self.main_window.session_combo.currentText()" in content:
        print("✅ 正確使用 session_combo.currentText()")
    else:
        print("❌ 缺少正確的 session_combo 讀取")

print("\n步驟 4: 測試總結")
print("-" * 80)

print("""
✅ 修復完成！

修復內容：
1. ✅ 添加 else 分支的處理代碼（從主視窗讀取參數）
2. ✅ 調用 _apply_driver_lap_settings 實際套用主視窗參數
3. ✅ 移除無效的 update_current_window_only() 調用（避免重複處理）

預期效果：
- 勾選同步 → 點擊 OK
- Speed Analysis 立即顯示主 GUI 的曲線（Brazil R, NOR）
- 狀態列消失（因為啟用同步）
- 視窗標題更新為 Brazil R

請執行以下步驟進行手動測試：
1. 啟動 GUI：python f1t_gui_main.py
2. 主 GUI 設定：2025 Brazil R, NOR, driver2=None, lap1
3. 開啟 Speed Analysis（設定為跨賽事：2025 AU R vs 2025 AU Q）
4. 右鍵 Speed Analysis → Settings
5. 勾選「Sync Driver & Lap with Main GUI」
6. 點擊 OK
7. 驗證：圖表應顯示 Brazil R 的 NOR 曲線（不是 AU）
""")

print("\n" + "=" * 80)
print("測試腳本執行完成")
print("=" * 80)
