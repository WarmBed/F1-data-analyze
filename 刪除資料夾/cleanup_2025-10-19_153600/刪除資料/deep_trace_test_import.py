"""
深度追蹤：檢查 test_api_only_mode.py 是否在 GUI 啟動時被調用
"""
import sys
import os

# 記錄初始已載入的模組
initial_modules = set(sys.modules.keys())

print("=" * 80)
print("[TRACE] 深度追蹤：test_api_only_mode.py 是否在 GUI 啟動時被調用")
print("=" * 80)

print("\n[步驟 1] 記錄初始狀態...")
print(f"  初始已載入模組數: {len(initial_modules)}")

# 檢查測試模組是否已經載入
if 'tests.test_api_only_mode' in sys.modules:
    print("  [WARNING] tests.test_api_only_mode 已在初始狀態時載入！")
else:
    print("  [OK] tests.test_api_only_mode 尚未載入")

# 模擬 GUI 啟動流程
print("\n[步驟 2] 模擬 GUI 啟動流程...")

# 2.1 導入日誌系統
print("  2.1 導入 core.logger...")
try:
    from core.logger import setup_logging, get_logger
    if 'tests.test_api_only_mode' in sys.modules:
        print("      [WARNING] 測試在導入 core.logger 後被載入！")
except Exception as e:
    print(f"      錯誤: {e}")

# 2.2 導入 GUI 基礎組件
print("  2.2 導入 PyQt5...")
try:
    from PyQt5.QtWidgets import QApplication
    if 'tests.test_api_only_mode' in sys.modules:
        print("      [WARNING] 測試在導入 PyQt5 後被載入！")
except Exception as e:
    print(f"      錯誤: {e}")

# 2.3 導入 GUI 模組
print("  2.3 導入 GUI 模組...")
try:
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader
    if 'tests.test_api_only_mode' in sys.modules:
        print("      [WARNING] 測試在導入 UniversalDataLoader 後被載入！")
except Exception as e:
    print(f"      錯誤: {e}")

# 2.4 導入 i18n
print("  2.4 導入 core.gui_i18n...")
try:
    from core.gui_i18n import tr
    if 'tests.test_api_only_mode' in sys.modules:
        print("      [WARNING] 測試在導入 gui_i18n 後被載入！")
except Exception as e:
    print(f"      錯誤: {e}")

# 2.5 導入主題
print("  2.5 導入 modules.gui.themes...")
try:
    from modules.gui.themes import color_palette_provider
    if 'tests.test_api_only_mode' in sys.modules:
        print("      [WARNING] 測試在導入 themes 後被載入！")
except Exception as e:
    print(f"      錯誤: {e}")

# 檢查所有新載入的模組
print("\n[步驟 3] 檢查新載入的模組...")
current_modules = set(sys.modules.keys())
new_modules = current_modules - initial_modules

# 過濾測試相關模組
test_related = [m for m in new_modules if 'test' in m.lower()]
if test_related:
    print(f"  [WARNING] 發現 {len(test_related)} 個與測試相關的新模組:")
    for module in sorted(test_related)[:10]:
        print(f"      - {module}")
else:
    print("  [OK] 沒有載入測試相關模組")

# 最終確認
print("\n[步驟 4] 最終確認...")
if 'tests.test_api_only_mode' in sys.modules:
    print("  [WARNING] tests.test_api_only_mode 已被載入！")
    module = sys.modules['tests.test_api_only_mode']
    if hasattr(module, '__file__'):
        print(f"     檔案位置: {module.__file__}")
    
    # 嘗試獲取調用棧
    import inspect
    print("\n  [調用棧追蹤]")
    for frame_info in inspect.stack()[:10]:
        print(f"      {frame_info.filename}:{frame_info.lineno} in {frame_info.function}")
else:
    print("  [OK] tests.test_api_only_mode 未被載入")

print("\n" + "=" * 80)
print("結論:")
if 'tests.test_api_only_mode' in sys.modules:
    print("  [FAIL] 測試腳本在 GUI 模組導入過程中被載入")
else:
    print("  [PASS] 測試腳本沒有在 GUI 模組導入過程中被載入")
print("=" * 80)
