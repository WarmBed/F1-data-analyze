"""
簡化版追蹤：檢查 test_api_only_mode.py 是否在 GUI 啟動時被調用
"""
import sys

print("=" * 80)
print("[TRACE] 簡化追蹤")
print("=" * 80)

# 步驟 1: 初始狀態
print("\n[步驟 1] 初始狀態...")
if 'tests.test_api_only_mode' in sys.modules:
    print("  [WARNING] 測試已載入！")
else:
    print("  [OK] 測試未載入")

# 步驟 2: 導入 UniversalDataLoader
print("\n[步驟 2] 導入 UniversalDataLoader...")
try:
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader
    print("  [OK] 導入成功")
except Exception as e:
    print(f"  [ERROR] 導入失敗: {e}")

# 步驟 3: 檢查測試是否被載入
print("\n[步驟 3] 檢查測試是否被載入...")
if 'tests.test_api_only_mode' in sys.modules:
    print("  [WARNING] 測試已載入！")
    print(f"  [INFO] 檔案: {sys.modules['tests.test_api_only_mode'].__file__}")
else:
    print("  [OK] 測試未載入")

# 步驟 4: 列出所有 tests.* 模組
print("\n[步驟 4] 列出所有 tests.* 模組...")
tests_modules = [name for name in sys.modules.keys() if name.startswith('tests.')]
if tests_modules:
    print(f"  [WARNING] 發現 {len(tests_modules)} 個 tests.* 模組:")
    for mod in sorted(tests_modules):
        print(f"      - {mod}")
else:
    print("  [OK] 沒有 tests.* 模組")

print("\n" + "=" * 80)
print("[結論]")
if 'tests.test_api_only_mode' in sys.modules:
    print("  [FAIL] 測試腳本在 GUI 模組導入時被載入")
else:
    print("  [PASS] 測試腳本未在 GUI 模組導入時被載入")
print("=" * 80)
