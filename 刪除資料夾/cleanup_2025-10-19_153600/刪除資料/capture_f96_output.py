#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "f1_analysis_modular_main.py", "-f", "96", "-y", "2025", "-r", "Japan"],
    capture_output=True,
    text=True,
    cwd="D:\\OneDrive\\Code\\F1-data-analyze"
)

with open("f96_stdout.txt", "w", encoding="utf-8") as f:
    f.write(result.stdout)

with open("f96_stderr.txt", "w", encoding="utf-8") as f:
    f.write(result.stderr)

print("=== STDOUT (first 3000 chars) ===")
print(result.stdout[:3000])
print("\n=== STDERR (first 3000 chars) ===")
print(result.stderr[:3000])
print(f"\n=== Exit Code: {result.returncode} ===")

sys.exit(result.returncode)
