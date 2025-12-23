"""查找 format 錯誤的具體位置"""
import subprocess
import sys

# 執行 CLI 並捕獲完整輸出
result = subprocess.run(
    [sys.executable, "f1_analysis_modular_main.py", "-f", "48", "-y", "2025", "-r", "Australia", "-s", "R"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print("=" * 80)
print("STDOUT:")
print("=" * 80)
print(result.stdout)

print("\n" + "=" * 80)
print("STDERR:")
print("=" * 80)
print(result.stderr)

print(f"\nReturn code: {result.returncode}")
