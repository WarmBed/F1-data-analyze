"""
直接執行 CLI -f13 並捕獲完整輸出
"""
import subprocess

print("執行: python f1_analysis_modular_main.py -f 13 -y 2024 -r Japan -s R -d VER -d2 LEC")
print("=" * 80)

result = subprocess.run(
    ["python", "f1_analysis_modular_main.py", "-f", "13", "-y", "2024", "-r", "Japan", "-s", "R", "-d", "VER", "-d2", "LEC"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=120
)

print("STDOUT:")
print(result.stdout)

print("\n" + "=" * 80)
print("STDERR:")
print(result.stderr)

print("\n" + "=" * 80)
print(f"返回碼: {result.returncode}")
