"""
測試 build_exe_gui.py 的 spec 檔案轉換功能
"""
import sys
sys.path.insert(0, r'c:\Users\mike2\OneDrive\Code\F1-data-analyze')

from build_exe_gui import EXEBuilderGUI
from pathlib import Path

# 讀取實際的 spec 檔案
spec_file = Path(r'c:\Users\mike2\OneDrive\Code\F1-data-analyze\F1T_GUI_clean.spec')
original_content = spec_file.read_text(encoding='utf-8')

print("=" * 80)
print("📄 原始 spec 檔案分析")
print("=" * 80)
print(f"✅ 包含 'exclude_binaries=True': {'exclude_binaries=True' in original_content}")
print(f"✅ 包含 'COLLECT': {'COLLECT' in original_content}")
print(f"✅ 包含 'coll = COLLECT': {'coll = COLLECT' in original_content}")
print()

# 創建一個測試實例（不啟動 GUI）
class TestBuilder:
    def __init__(self):
        pass
    
    # 複製轉換方法
    from build_exe_gui import EXEBuilderGUI
    _convert_to_onedir_spec = EXEBuilderGUI._convert_to_onedir_spec
    _convert_to_onefile_spec = EXEBuilderGUI._convert_to_onefile_spec

builder = TestBuilder()

# 測試 1: onedir → onefile 轉換
print("=" * 80)
print("🧪 測試 1: 目錄模式 → 單檔案模式")
print("=" * 80)
onefile_content = builder._convert_to_onefile_spec(original_content)

print(f"✅ 轉換後包含 'exclude_binaries=False': {'exclude_binaries=False' in onefile_content}")
print(f"✅ 轉換後包含 'a.binaries': {'a.binaries' in onefile_content}")
print(f"❌ 轉換後不包含 'COLLECT': {'COLLECT' not in onefile_content}")
print()

# 測試 2: onefile → onedir 轉換
print("=" * 80)
print("🧪 測試 2: 單檔案模式 → 目錄模式")
print("=" * 80)
onedir_content = builder._convert_to_onedir_spec(onefile_content)

print(f"✅ 轉換後包含 'exclude_binaries=True': {'exclude_binaries=True' in onedir_content}")
print(f"✅ 轉換後包含 'COLLECT': {'COLLECT' in onedir_content}")
print(f"❌ 轉換後 EXE() 不直接包含 'a.binaries': {onedir_content.find('exe = EXE') < onedir_content.find('a.binaries') < onedir_content.find('COLLECT')}")
print()

# 測試 3: 檢查 EXE 區塊
print("=" * 80)
print("📋 單檔案模式 EXE 配置預覽")
print("=" * 80)
import re
exe_match = re.search(r'exe = EXE\((.*?)\)', onefile_content, re.DOTALL)
if exe_match:
    print(exe_match.group(0)[:500])
print()

print("=" * 80)
print("📋 目錄模式 EXE 配置預覽")
print("=" * 80)
exe_match = re.search(r'exe = EXE\((.*?)\)', onedir_content, re.DOTALL)
if exe_match:
    print(exe_match.group(0)[:500])
print()

print("=" * 80)
print("📋 目錄模式 COLLECT 配置預覽")
print("=" * 80)
collect_match = re.search(r'coll = COLLECT\((.*?)\)', onedir_content, re.DOTALL)
if collect_match:
    print(collect_match.group(0)[:500])
else:
    print("❌ 未找到 COLLECT 區塊！")

print()
print("=" * 80)
print("✅ 所有測試完成！")
print("=" * 80)
