#!/usr/bin/env python3
"""檢查 2025 各賽道的 FP3 數據可用性"""

import json
import glob

# v3.6 的 10 個賽道
RACE_MAPPING = {
    1: 'Bahrain',
    2: 'Saudi Arabia',
    3: 'Japan',
    6: 'Monaco',
    9: 'Canada',
    11: 'Great Britain',
    13: 'Hungary',
    14: 'Netherlands',
    15: 'Italy',
    16: 'Azerbaijan'
}

print("=" * 70)
print("2025 賽道 FP3 數據可用性檢查")
print("=" * 70)

for race_num, track_name in sorted(RACE_MAPPING.items()):
    # 找到數據檔案
    files = glob.glob(f"json/predictionJSON/fp_q_data_2025_{race_num}_*.json")
    
    if not files:
        print(f"\n[{track_name}] Race {race_num}: ❌ 找不到數據檔案")
        continue
    
    latest_file = sorted(files, reverse=True)[0]
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    has_fp3 = 'FP3' in data.get('practice_sessions', {})
    has_q = 'qualifying' in data
    
    status = "✓" if (has_fp3 and has_q) else "❌"
    print(f"\n[{track_name}] Race {race_num}: {status}")
    print(f"  FP3: {'✓' if has_fp3 else '❌'}")
    print(f"  Q: {'✓' if has_q else '❌'}")
    
    if has_fp3:
        fp3_drivers = len(data['practice_sessions']['FP3'].get('driver_data', {}))
        print(f"  FP3 車手數: {fp3_drivers}")
