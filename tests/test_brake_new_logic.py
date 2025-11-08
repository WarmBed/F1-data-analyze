#!/usr/bin/env python3
"""測試 Function 44 煞車分析新邏輯"""

import subprocess
import sys

# 執行 CLI 命令
result = subprocess.run(
    [sys.executable, "f1_analysis_modular_main.py", "-f", "44", "-y", "2025", "-r", "Japan", "-s", "R"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)

print("=== STDOUT ===")
print(result.stdout)
print("\n=== STDERR ===")
print(result.stderr)
print(f"\n=== EXIT CODE: {result.returncode} ===")

# 保存到檔案
with open("brake_test_japan_output.txt", "w", encoding='utf-8') as f:
    f.write("=== STDOUT ===\n")
    f.write(result.stdout)
    f.write("\n\n=== STDERR ===\n")
    f.write(result.stderr)
    f.write(f"\n\n=== EXIT CODE: {result.returncode} ===\n")

print("\n已保存到 brake_test_japan_output.txt")
