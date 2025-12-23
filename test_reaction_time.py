#!/usr/bin/env python3
"""
分析「綠燈到第一個速度數據」的時間
這才是真正的反應時間
"""
import json
from pathlib import Path
from collections import defaultdict

DRIVER_NAMES = {
    '1': 'VER', '4': 'NOR', '5': 'BEA', '6': 'TSU', '10': 'GAS',
    '12': 'DOO', '14': 'ALO', '16': 'LEC', '18': 'STR', '22': 'ANT',
    '23': 'ALB', '27': 'HUL', '30': 'LAW', '31': 'OCO', '43': 'COL',
    '44': 'HAM', '55': 'SAI', '63': 'RUS', '81': 'PIA', '87': 'HAD'
}

def parse_timestamp(ts):
    if not ts:
        return 0.0
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


race_dir = Path(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\json\LiveF1\2025\Abu_Dhabi_Race")

# 讀取 SessionData 找綠燈時間
with open(race_dir / 'SessionData.json', 'r', encoding='utf-8') as f:
    session_data = json.load(f)

race_start_ts = None
for rec in session_data.get('records', []):
    status = rec.get('data', {}).get('StatusSeries', {})
    if isinstance(status, dict):
        for key, val in status.items():
            if isinstance(val, dict) and val.get('SessionStatus') == 'Started':
                race_start_ts = parse_timestamp(rec.get('timestamp', ''))
                break
    if race_start_ts:
        break

print(f"綠燈時間 (SessionStatus=Started): {race_start_ts:.3f}s")

# 讀取 CarData
with open(race_dir / 'CarData.json', 'r', encoding='utf-8') as f:
    cardata = json.load(f)

# 找每位車手的「第一個速度 > 0」的時間點
driver_first_speed = {}

for rec in cardata.get('records', []):
    ts = parse_timestamp(rec.get('timestamp', ''))
    
    # 只看綠燈後 5 秒內
    if ts < race_start_ts or ts > race_start_ts + 5:
        continue
    
    entries = rec.get('data', {}).get('Entries', [])
    if not entries:
        continue
    
    cars = entries[0].get('Cars', {})
    
    for drv_num, name in DRIVER_NAMES.items():
        if name in driver_first_speed:
            continue  # 已經找到了
        
        if drv_num in cars:
            speed = cars[drv_num].get('Channels', {}).get('2', 0)
            if speed > 0:
                relative_time = ts - race_start_ts
                driver_first_speed[name] = {
                    'reaction_time': relative_time,
                    'first_speed': speed
                }

# 排序並顯示
print("\n" + "=" * 60)
print("真正的反應時間 (綠燈 → 第一個速度數據)")
print("=" * 60)
print(f"\n{'車手':<6} | {'反應時間':>10} | {'第一速度':>10}")
print("-" * 40)

sorted_drivers = sorted(driver_first_speed.items(), key=lambda x: x[1]['reaction_time'])

for name, data in sorted_drivers:
    print(f"{name:<6} | {data['reaction_time']:>8.3f}s | {data['first_speed']:>8} km/h")

print("\n" + "=" * 60)
print("分析")
print("=" * 60)

times = [d['reaction_time'] for d in driver_first_speed.values()]
speeds = [d['first_speed'] for d in driver_first_speed.values()]

print(f"最快反應: {min(times):.3f}s")
print(f"最慢反應: {max(times):.3f}s")
print(f"差距: {max(times) - min(times):.3f}s")
print(f"\n第一速度範圍: {min(speeds)}-{max(speeds)} km/h")
