"""
模擬 GUI 啟動並追蹤 test_api_only_mode 的執行
"""
import sys
import os

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔍 模擬 GUI 啟動並追蹤測試腳本")
print("=" * 80)

# 檢查初始狀態
print("\n[步驟 1] 檢查初始狀態...")
if 'tests.test_api_only_mode' in sys.modules:
    print("  ⚠️  測試腳本已在初始狀態時載入！")
else:
    print("  ✅ 測試腳本尚未載入")

# 導入核心模組
print("\n[步驟 2] 導入核心模組...")
try:
    from core.logger import setup_logging, get_logger
    print("  ✅ core.logger 導入成功")
    
    if 'tests.test_api_only_mode' in sys.modules:
        print("  ⚠️  測試腳本在導入 core.logger 後被載入！")
except Exception as e:
    print(f"  ❌ 導入失敗: {e}")

# 導入 GUI 基礎模組
print("\n[步驟 3] 導入 GUI 基礎模組...")
try:
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader
    print("  ✅ UniversalDataLoader 導入成功")
    
    if 'tests.test_api_only_mode' in sys.modules:
        print("  ⚠️  測試腳本在導入 UniversalDataLoader 後被載入！")
except Exception as e:
    print(f"  ❌ 導入失敗: {e}")

# 檢查 tests 目錄
print("\n[步驟 4] 檢查 tests 目錄...")
tests_dir = os.path.join(os.path.dirname(__file__), 'tests')
if os.path.exists(tests_dir):
    print(f"  📂 tests 目錄存在: {tests_dir}")
    
    # 檢查是否有 __init__.py
    init_file = os.path.join(tests_dir, '__init__.py')
    if os.path.exists(init_file):
        print(f"  ⚠️  tests/__init__.py 存在！")
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.strip():
                print("  ⚠️  tests/__init__.py 不是空的，內容:")
                print("  " + "\n  ".join(content.split('\n')[:10]))
    else:
        print("  ✅ tests/__init__.py 不存在")

# 檢查是否有自動發現機制
print("\n[步驟 5] 檢查 pytest 配置...")
pytest_ini = os.path.join(os.path.dirname(__file__), 'pytest.ini')
setup_cfg = os.path.join(os.path.dirname(__file__), 'setup.cfg')
pyproject_toml = os.path.join(os.path.dirname(__file__), 'pyproject.toml')

if os.path.exists(pytest_ini):
    print("  ⚠️  pytest.ini 存在")
elif os.path.exists(setup_cfg):
    print("  ⚠️  setup.cfg 存在")
elif os.path.exists(pyproject_toml):
    print("  ⚠️  pyproject.toml 存在")
else:
    print("  ✅ 沒有 pytest 配置檔案")

# 最終檢查
print("\n[最終狀態]")
if 'tests.test_api_only_mode' in sys.modules:
    print("  ⚠️  測試腳本已被載入！")
    module = sys.modules['tests.test_api_only_mode']
    if hasattr(module, '__file__'):
        print(f"     檔案: {module.__file__}")
else:
    print("  ✅ 測試腳本未被載入")

print("\n" + "=" * 80)
