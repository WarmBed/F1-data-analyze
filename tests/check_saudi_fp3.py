#!/usr/bin/env python3
"""檢查 Saudi Arabia 的 fp_q_data 是否有 FP3"""

import json

file_path = 'json/predictionJSON/fp_q_data_2025_2_20251102_220731.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("Saudi Arabia fp_q_data 結構檢查")
print("=" * 70)

practice_sessions = data.get('practice_sessions', {})
print(f"\n練習賽會話: {list(practice_sessions.keys())}")

fp3_data = practice_sessions.get('FP3', {})
fp3_drivers = fp3_data.get('driver_data', {})

print(f"\nFP3 數據:")
print(f"  存在: {len(fp3_drivers) > 0}")
print(f"  車手數: {len(fp3_drivers)}")

if len(fp3_drivers) > 0:
    first_driver = list(fp3_drivers.keys())[0]
    print(f"  第一位車手: {first_driver}")
    print(f"  欄位: {list(fp3_drivers[first_driver].keys())}")
else:
    print("  ❌ FP3 無數據")
