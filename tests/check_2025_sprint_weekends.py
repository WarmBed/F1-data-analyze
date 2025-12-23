#!/usr/bin/env python3
"""檢查 2025 衝刺賽週末"""

import json
import glob

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
print("2025 賽季練習賽會話檢查")
print("=" * 70)

sprint_races = []

for race_num, track_name in sorted(RACE_MAPPING.items()):
    files = glob.glob(f'json/predictionJSON/fp_q_data_2025_{race_num}_*.json')
    
    if not files:
        continue
    
    with open(files[0], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sessions = list(data.get('practice_sessions', {}).keys())
    
    has_fp3 = 'FP3' in sessions
    is_sprint = not has_fp3 and 'FP1' in sessions
    
    status = "正常週末" if has_fp3 else "衝刺賽週末"
    
    print(f"\n[{track_name}] Race {race_num}")
    print(f"  練習賽: {', '.join(sessions) if sessions else '無'}")
    print(f"  類型: {status}")
    
    if is_sprint:
        sprint_races.append(track_name)

print("\n" + "=" * 70)
print(f"2025 衝刺賽週末: {', '.join(sprint_races)}")
print("=" * 70)
