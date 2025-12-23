"""
追蹤測試腳本執行來源
"""
import sys
import traceback

print("=" * 80)
print("🔍 追蹤測試腳本執行來源")
print("=" * 80)

# 獲取當前 Python 路徑
print("\n[Python 路徑]")
for i, path in enumerate(sys.path, 1):
    print(f"  {i}. {path}")

# 檢查已載入的模組
print("\n[已載入的測試相關模組]")
test_modules = [name for name in sys.modules.keys() if 'test' in name.lower()]
for module_name in sorted(test_modules)[:20]:  # 只顯示前 20 個
    print(f"  - {module_name}")

# 檢查是否有測試腳本在運行
print("\n[檢查測試腳本]")
if 'tests.test_api_only_mode' in sys.modules:
    print("  ⚠️  tests.test_api_only_mode 已被載入！")
    module = sys.modules['tests.test_api_only_mode']
    print(f"     檔案位置: {module.__file__ if hasattr(module, '__file__') else '未知'}")
else:
    print("  ✅ tests.test_api_only_mode 尚未載入")

# 列出所有 tests.* 模組
print("\n[所有 tests.* 模組]")
tests_modules = [name for name in sys.modules.keys() if name.startswith('tests.')]
if tests_modules:
    for module_name in sorted(tests_modules):
        print(f"  - {module_name}")
else:
    print("  (無)")

print("\n" + "=" * 80)
