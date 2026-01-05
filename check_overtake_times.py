# -*- coding: utf-8 -*-
"""輸出前 10 次真正賽道超車的時間戳供驗證"""

import json
import os
from collections import defaultdict

BASE_DIR = r'json\LiveF1\2025\Abu_Dhabi_Race'

def load_json(filename):
    with open(os.path.join(BASE_DIR, filename), 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('records', data) if isinstance(data, dict) else data

# 載入車手
drivers = {}
for r in load_json('DriverList.json'):
    for num, info in r.get('data', {}).items():
        if isinstance(info, dict) and 'Tla' in info:
            drivers[num] = info['Tla']

# 載入進站資料
pit_laps = defaultdict(set)
for r in load_json('PitLaneTimeCollection.json'):
    for num, info in r.get('data', {}).get('PitTimes', {}).items():
        if isinstance(info, dict) and 'Lap' in info:
            pit_laps[num].add(int(info['Lap']))

all_pit_laps = set()
for laps in pit_laps.values():
    all_pit_laps.update(laps)
    # 同時加入出站圈 (進站圈 + 1)
    all_pit_laps.update(lap + 1 for lap in laps)

# 圈數更新
lap_updates = []
for r in load_json('TimingData.json'):
    ts = r.get('timestamp', '')
    for num, info in r.get('data', {}).get('Lines', {}).items():
        if isinstance(info, dict) and 'NumberOfLaps' in info:
            lap_updates.append((ts, num, info['NumberOfLaps']))

# 分析位置變化
current_laps = defaultdict(int)
lap_idx = 0
last_pos = {}
on_track_overtakes = []

for r in load_json('TimingAppData.json'):
    ts = r.get('timestamp', '')
    
    while lap_idx < len(lap_updates) and lap_updates[lap_idx][0] <= ts:
        _, num, lap = lap_updates[lap_idx]
        current_laps[num] = lap
        lap_idx += 1
    
    for num, info in r.get('data', {}).get('Lines', {}).items():
        if not isinstance(info, dict) or 'Line' not in info:
            continue
        
        new_pos = info['Line']
        old_pos = last_pos.get(num, new_pos)
        
        if new_pos < old_pos:
            lap = current_laps.get(num, 1)
            # 只記錄真正賽道超車 (排除第一圈和進站圈)
            if lap > 1 and lap not in all_pit_laps:
                on_track_overtakes.append({
                    'ts': ts,
                    'lap': lap,
                    'driver': drivers.get(num, num),
                    'old': old_pos,
                    'new': new_pos
                })
        
        last_pos[num] = new_pos

print('=' * 60)
print('Abu Dhabi 2025 真正賽道超車 - 前 10 次')
print('=' * 60)
print(f'進站圈: {sorted(all_pit_laps)}')
print()
print('時間戳             | 圈數 | 車手 | 位置變化')
print('-' * 60)
for i, o in enumerate(on_track_overtakes[:10]):
    print(f"{o['ts']:18s} | L{o['lap']:2d}  | {o['driver']:3s}  | P{o['old']} -> P{o['new']}")

print(f"\n總共真正賽道超車: {len(on_track_overtakes)} 次事件")
