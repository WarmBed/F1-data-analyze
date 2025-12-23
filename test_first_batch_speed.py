#!/usr/bin/env python3
"""
分析在「第一個數據批次」時各車手的速度
速度越高 = 反應越快 + 加速越好
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

print(f"綠燈時間: {race_start_ts:.3f}s")

# 讀取 CarData
with open(race_dir / 'CarData.json', 'r', encoding='utf-8') as f:
    cardata = json.load(f)

# 收集綠燈後前幾個數據批次
first_batch_found = False
first_batch_time = None
driver_speeds_at_first_batch = {}

all_batches = []  # 收集前 5 個批次

for rec in cardata.get('records', []):
    ts = parse_timestamp(rec.get('timestamp', ''))
    
    # 只看綠燈後
    if ts < race_start_ts:
        continue
    
    entries = rec.get('data', {}).get('Entries', [])
    if not entries:
        continue
    
    cars = entries[0].get('Cars', {})
    
    # 檢查這批是否有速度數據
    batch_speeds = {}
    for drv_num, name in DRIVER_NAMES.items():
        if drv_num in cars:
            speed = cars[drv_num].get('Channels', {}).get('2', 0)
            if speed > 0:
                batch_speeds[name] = speed
    
    if batch_speeds:
        relative_time = ts - race_start_ts
        all_batches.append({
            'time': relative_time,
            'speeds': batch_speeds
        })
        
        if len(all_batches) >= 5:
            break

print("\n" + "=" * 70)
print("綠燈後的前幾個數據批次")
print("=" * 70)

for i, batch in enumerate(all_batches):
    print(f"\n批次 {i+1} @ {batch['time']:.3f}s (綠燈後)")
    print(f"  車手數: {len(batch['speeds'])}")
    # 按速度排序
    sorted_speeds = sorted(batch['speeds'].items(), key=lambda x: -x[1])
    print("  速度排名 (前 5): ", end="")
    for name, speed in sorted_speeds[:5]:
        print(f"{name}:{speed}km/h  ", end="")
    print()

# 用第一個批次來評估「起跑速度」
if all_batches:
    first = all_batches[0]
    print("\n" + "=" * 70)
    print(f"第一批次 (t={first['time']:.3f}s) 速度排名 = 起跑反應")
    print("=" * 70)
    
    sorted_speeds = sorted(first['speeds'].items(), key=lambda x: -x[1])
    print(f"\n{'排名':<4} | {'車手':<6} | {'速度':>8}")
    print("-" * 30)
    for rank, (name, speed) in enumerate(sorted_speeds, 1):
        print(f"{rank:<4} | {name:<6} | {speed:>6} km/h")
    
    # 計算「速度得分」
    max_speed = max(first['speeds'].values())
    min_speed = min(first['speeds'].values())
    
    print("\n" + "=" * 70)
    print("結論")
    print("=" * 70)
    print(f"最快: {sorted_speeds[0][0]} ({sorted_speeds[0][1]} km/h)")
    print(f"最慢: {sorted_speeds[-1][0]} ({sorted_speeds[-1][1]} km/h)")
    print(f"速度差: {max_speed - min_speed} km/h")
    print(f"\n這個速度差代表了 ~{first['time']:.1f}秒內的反應差異")
