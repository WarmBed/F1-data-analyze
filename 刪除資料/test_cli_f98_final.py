#!/usr/bin/env python3
"""最終測試：CLI Function 98 通過主程式執行"""

import sys
import subprocess

print("=" * 60)
print("CLI Function 98 完整測試")
print("=" * 60)

# 執行 CLI 命令
result = subprocess.run(
    [sys.executable, "f1_analysis_modular_main.py", "-f", "98", "-y", "2024", "--force"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)

print("\n[STDOUT]")
print(result.stdout)

if result.stderr:
    print("\n[STDERR]")
    print(result.stderr)

print(f"\n[EXIT CODE] {result.returncode}")

if result.returncode == 0:
    print("\n✅ CLI Function 98 執行成功!")
else:
    print("\n❌ CLI Function 98 執行失敗")
    
    # 檢查 JSON 輸出
    import os
    import glob
    
    json_files = glob.glob("json/team_colors_2024_*.json")
    if json_files:
        latest = max(json_files, key=os.path.getmtime)
        print(f"\n💡 但找到了 JSON 輸出檔案: {latest}")
        print("   可能是警告導致的非零退出碼")
