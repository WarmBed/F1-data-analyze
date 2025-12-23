#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys

# 設置標準輸出編碼
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cmd = ["python", "f1_analysis_modular_main.py", "-f", "121", "-y", "2025", "-r", "Qatar", "-s", "FP2"]

print("執行命令:", ' '.join(cmd))
print("-" * 60)

process = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=60,
    encoding='utf-8',
    errors='replace'
)

print(f"返回碼: {process.returncode}\n")

stdout = process.stdout or ""
stderr = process.stderr or ""

# 提取所有 [ERROR] 行
errors = [line.strip() for line in stdout.split('\n') if '[ERROR]' in line]

print(f"找到 {len(errors)} 條 [ERROR] 訊息:")
for i, err in enumerate(errors, 1):
    print(f"{i}. {err}")

print("\n" + "=" * 60)
print("過濾測試:")
print("=" * 60)

# 測試過濾邏輯
real_errors = []
for line in stdout.split('\n'):
    if '[ERROR]' in line:
        # 跳過警告相關的錯誤
        if 'fastf1.api' in line or 'WARNING' in line.upper():
            print(f"[SKIP] {line.strip()[:80]}...")
            continue
        real_errors.append(line.strip())
        print(f"[KEEP] {line.strip()[:80]}...")

print(f"\n過濾後剩餘 {len(real_errors)} 條真實錯誤")
if real_errors:
    print(f"第一條: {real_errors[0]}")
