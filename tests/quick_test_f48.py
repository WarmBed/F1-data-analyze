#!/usr/bin/env python3
"""快速測試 F48 位置標準化"""
import subprocess
import sys

print("執行 -f48 新加坡測試...")
print("="*80)

result = subprocess.run(
    [sys.executable, "f1_analysis_modular_main.py", "-f", "48", "-y", "2024", "-r", "Singapore", "-s", "R"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
