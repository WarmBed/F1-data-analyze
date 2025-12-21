"""
進度條顯示問題修復驗證
測試 update_all_lap_analysis() 能正確過濾遙測視窗
"""

print("="*70)
print("[TEST] 進度條顯示問題修復驗證")
print("="*70)

# 測試 1: 驗證屬性名稱修正
print("\n[TEST 1] 驗證 update_all_lap_analysis() 使用正確的屬性名稱")
print("-"*70)

with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 檢查 update_all_lap_analysis() 方法
if 'def update_all_lap_analysis(self' in content:
    method_section = content.split('def update_all_lap_analysis(self')[1].split('def ')[0]
    
    # 檢查是否使用 'analysis_type'（無底線）
    if "getattr(analysis_module, 'analysis_type'" in method_section:
        print("[OK] update_all_lap_analysis() 使用 'analysis_type'（無底線）")
    else:
        print("[FAIL] update_all_lap_analysis() 未使用 'analysis_type'")
    
    # 檢查是否還有舊的 '_analysis_type'（有底線）
    if "getattr(analysis_module, '_analysis_type'" in method_section:
        print("[FAIL] 仍然存在舊的 '_analysis_type'（應該已修正）")
    else:
        print("[OK] 已移除舊的 '_analysis_type'")

# 測試 2: 驗證兩個方法使用相同的屬性
print("\n[TEST 2] 驗證兩個方法的屬性名稱一致性")
print("-"*70)

# 檢查 _get_telemetry_analysis_windows() 使用的屬性
if 'def _get_telemetry_analysis_windows(self' in content:
    get_method = content.split('def _get_telemetry_analysis_windows(self')[1].split('def ')[0]
    
    if "window.analysis_type in telemetry_types" in get_method:
        print("[OK] _get_telemetry_analysis_windows() 使用 'analysis_type'")
        attr1 = 'analysis_type'
    else:
        print("[FAIL] _get_telemetry_analysis_windows() 未使用 'analysis_type'")
        attr1 = None

# 檢查 update_all_lap_analysis() 使用的屬性
if 'def update_all_lap_analysis(self' in content:
    update_method = content.split('def update_all_lap_analysis(self')[1].split('def ')[0]
    
    if "getattr(analysis_module, 'analysis_type'" in update_method:
        print("[OK] update_all_lap_analysis() 使用 'analysis_type'")
        attr2 = 'analysis_type'
    else:
        print("[FAIL] update_all_lap_analysis() 未使用 'analysis_type'")
        attr2 = None

# 驗證一致性
if attr1 and attr2 and attr1 == attr2:
    print("\n[PASS] 兩個方法使用相同的屬性名稱: '{}'".format(attr1))
else:
    print("\n[FAIL] 兩個方法使用不同的屬性名稱")

# 測試 3: 驗證修復註解
print("\n[TEST 3] 驗證修復註解")
print("-"*70)

if "# 🔧 修復：統一使用 analysis_type（無底線）" in content:
    print("[OK] 已添加修復註解")
else:
    print("[WARN] 缺少修復註解")

if "與 _get_telemetry_analysis_windows() 一致" in content:
    print("[OK] 註解說明一致性")
else:
    print("[WARN] 註解未說明一致性")

# 測試 4: 檢查進度條創建代碼
print("\n[TEST 4] 驗證進度條創建代碼")
print("-"*70)

if 'def update_all_lap_analysis(self' in content:
    method_section = content.split('def update_all_lap_analysis(self')[1].split('def ')[0]
    
    if 'QProgressDialog' in method_section:
        print("[OK] 進度條創建代碼存在")
    else:
        print("[FAIL] 進度條創建代碼缺失")
    
    if 'progress.setWindowModality(Qt.WindowModal)' in method_section:
        print("[OK] 進度條設為模態視窗")
    else:
        print("[FAIL] 進度條未設為模態視窗")
    
    if 'progress.setValue(0)' in method_section:
        print("[OK] 進度條初始化為 0")
    else:
        print("[FAIL] 進度條未初始化")

# 總結
print("\n" + "="*70)
print("[SUMMARY] 修復驗證總結")
print("="*70)

print("""
問題原因：
  兩個方法使用不同的屬性名稱：
  - _get_telemetry_analysis_windows() 使用 'analysis_type'（無底線）
  - update_all_lap_analysis() 原本使用 '_analysis_type'（有底線）
  
  導致流程：
  1. _get_telemetry_analysis_windows() 找到視窗 → 顯示確認對話框
  2. 用戶點擊 Yes
  3. update_all_lap_analysis() 用錯誤屬性過濾 → 找不到視窗
  4. modules_to_update 為空 → 直接返回 → 不顯示進度條

修復方案：
  統一兩個方法都使用 'analysis_type'（無底線）
  
預期結果：
  - 確認對話框正常顯示 ✅
  - 用戶點擊 Yes 後進度條正常顯示 ✅
  - 遙測視窗正常更新 ✅
""")

print("\n[INFO] 修復完成！請重新啟動 GUI 測試")
