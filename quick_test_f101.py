#!/usr/bin/env python3
"""Quick test for F101 loader - no logger dependency"""

import sys
import json
from pathlib import Path

print('Python:', sys.executable, flush=True)

# 簡化版數據載入 (不使用 logger)
DRIVER_NAMES = {
    '1': 'VER', '4': 'NOR', '5': 'BEA', '6': 'TSU', '10': 'GAS',
    '12': 'DOO', '14': 'ALO', '16': 'LEC', '18': 'STR', '22': 'ANT',
    '23': 'ALB', '27': 'HUL', '30': 'RIC', '31': 'OCO', '43': 'COL',
    '44': 'HAM', '55': 'SAI', '63': 'RUS', '81': 'PIA', '87': 'HAD'
}

def parse_ts(ts):
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0

def interpolate_time(t1, v1, t2, v2, target_v):
    if v2 == v1:
        return t1
    ratio = (target_v - v1) / (v2 - v1)
    return t1 + ratio * (t2 - t1)

try:
    race_dir = Path('json/LiveF1/2025/Abu_Dhabi_Race')
    print(f'Race dir: {race_dir}', flush=True)
    print(f'Exists: {race_dir.exists()}', flush=True)
    
    # Get race start
    with open(race_dir / 'SessionData.json', 'r', encoding='utf-8') as f:
        session = json.load(f)
    
    race_start_ts = None
    for rec in session.get('records', []):
        status = rec.get('data', {}).get('StatusSeries', {})
        if isinstance(status, dict):
            for key, val in status.items():
                if isinstance(val, dict) and val.get('SessionStatus') == 'Started':
                    race_start_ts = parse_ts(rec.get('timestamp', ''))
                    break
        if race_start_ts:
            break
    
    print(f'Race start: {race_start_ts}', flush=True)
    
    # Load CarData
    with open(race_dir / 'CarData.json', 'r', encoding='utf-8') as f:
        cardata = json.load(f)
    
    records = cardata.get('records', [])
    print(f'CarData records: {len(records)}', flush=True)
    
    # Analyze acceleration
    driver_speeds = {d: [] for d in DRIVER_NAMES.keys()}
    
    for rec in records:
        ts = parse_ts(rec.get('timestamp', ''))
        if ts < race_start_ts or ts > race_start_ts + 30:
            continue
        
        entries = rec.get('data', {}).get('Entries', [])
        if not entries:
            continue
        
        cars = entries[0].get('Cars', {})
        
        for drv in DRIVER_NAMES.keys():
            if drv in cars:
                speed = cars[drv].get('Channels', {}).get('2', 0)
                relative_time = ts - race_start_ts
                driver_speeds[drv].append((relative_time, speed))
    
    # Calculate times
    results = []
    for drv, speeds in driver_speeds.items():
        if not speeds:
            continue
        
        t50, t100 = None, None
        for i in range(1, len(speeds)):
            t_prev, v_prev = speeds[i-1]
            t_curr, v_curr = speeds[i]
            
            if t50 is None and v_prev < 50 <= v_curr:
                t50 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 50)
            if t100 is None and v_prev < 100 <= v_curr:
                t100 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 100)
        
        if t50 and t100:
            results.append((DRIVER_NAMES[drv], t50, t100))
    
    # Sort by t50
    results.sort(key=lambda x: x[1])
    
    print(f'\nResults ({len(results)} drivers):', flush=True)
    for name, t50, t100 in results:
        print(f'  {name}: 0-50={t50:.3f}s, 0-100={t100:.3f}s', flush=True)
    
    print('\nTest PASSED!', flush=True)
    
except Exception as e:
    print(f'Error: {e}', flush=True)
    import traceback
    traceback.print_exc()
