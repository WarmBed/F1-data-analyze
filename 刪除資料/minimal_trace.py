"""
最簡化追蹤
"""
import sys

print("[1] 初始狀態:")
print(f"    tests.test_api_only_mode in sys.modules: {'tests.test_api_only_mode' in sys.modules}")

print("[2] 準備導入 UniversalDataLoader...")
from modules.gui.base.universal_data_loader_base import UniversalDataLoader
print("[3] 導入完成")

print("[4] 檢查狀態:")
print(f"    tests.test_api_only_mode in sys.modules: {'tests.test_api_only_mode' in sys.modules}")

print("[5] 完成！")
