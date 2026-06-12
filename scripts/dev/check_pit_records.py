# -*- coding: utf-8 -*-
"""調查 L9 進站記錄"""

import json
from collections import defaultdict

BASE_DIR = r'json\LiveF1\2025\Abu_Dhabi_Race'

# 載入車手
with open(f'{BASE_DIR}/DriverList.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
drivers = {}
for r in data.get('records', data):
    for num, info in r.get('data', {}).items():
        if isinstance(info, dict) and 'Tla' in info:
            drivers[num] = info['Tla']

print("=== 所有車手 ===")
for num, tla in sorted(drivers.items(), key=lambda x: x[1]):
    print(f"  {num}: {tla}")

# 載入進站記錄
with open(f'{BASE_DIR}/PitLaneTimeCollection.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

records = data.get('records', data)
print(f"\n=== 進站記錄 (共 {len(records)} 條) ===")

all_pits = []
for r in records:
    ts = r.get('timestamp', '')
    pit_times = r.get('data', {}).get('PitTimes', {})
    for num, info in pit_times.items():
        if isinstance(info, dict) and 'Lap' in info:
            lap = info.get('Lap')
            duration = info.get('Duration', 'N/A')
            tla = drivers.get(num, num)
            all_pits.append({
                'ts': ts,
                'lap': lap,
                'driver': tla,
                'num': num,
                'duration': duration
            })

# 按圈排序
all_pits.sort(key=lambda x: (x['lap'], x['ts']))

print("\n所有進站 (按圈排序):")
for p in all_pits:
    print(f"  Lap {p['lap']:>2} | {p['driver']:3s} | {p['ts']} | Duration: {p['duration']}")

# 檢查第 9 圈
print("\n=== 第 9 圈相關 ===")
lap9_pits = [p for p in all_pits if p['lap'] == 9]
if lap9_pits:
    print("第 9 圈進站:")
    for p in lap9_pits:
        print(f"  {p['driver']} at {p['ts']}")
else:
    print("第 9 圈沒有進站記錄!")

# 檢查 HAM 和 ALB
print("\n=== HAM(44) 和 ALB(23) 進站 ===")
for p in all_pits:
    if p['driver'] in ['HAM', 'ALB']:
        print(f"  {p['driver']}: Lap {p['lap']} at {p['ts']}")
