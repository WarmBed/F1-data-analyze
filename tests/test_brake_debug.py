"""測試 Brake Performance 並捕獲詳細輸出"""
import subprocess
import sys

print("執行 Brake Performance 分析...")
print("=" * 80)

result = subprocess.run(
    [sys.executable, "f1_analysis_modular_main.py", "-f", "34", "-y", "2025", "-r", "Singapore", "-s", "R"],
    capture_output=True,
    text=True,
    encoding='utf-8'
)

print("STDOUT:")
print(result.stdout)
print("\n" + "=" * 80)
print("STDERR:")
print(result.stderr)
print("\n" + "=" * 80)
print(f"Exit Code: {result.returncode}")
