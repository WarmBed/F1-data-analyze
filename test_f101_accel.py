"""
F101 起跑反應分析 - 加速時間測試
"""

import json
from pathlib import Path

race_dir = Path('json/LiveF1/2025/Abu_Dhabi_Race')

def parse_ts(ts):
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    return 0

def interpolate_time(t1, v1, t2, v2, target_v):
    """線性插值計算達到目標速度的時間"""
    if v2 == v1:
        return t1
    ratio = (target_v - v1) / (v2 - v1)
    return t1 + ratio * (t2 - t1)

# Find race start from SessionData (SessionStatus: Started)
with open(race_dir / 'SessionData.json', 'r', encoding='utf-8') as f:
    session = json.load(f)

race_start_ts = None
for rec in session.get('records', []):
    status = rec.get('data', {}).get('StatusSeries', {})
    if isinstance(status, dict):
        for key, val in status.items():
            if isinstance(val, dict) and val.get('SessionStatus') == 'Started':
                race_start_ts = parse_ts(rec.get('timestamp', ''))
                print(f'Race start (lights out): {rec.get("timestamp")} ({race_start_ts:.2f}s)')
                break
    if race_start_ts:
        break

if not race_start_ts:
    race_start_ts = 3500
    print('Using fallback start detection')

with open(race_dir / 'CarData.json', 'r', encoding='utf-8') as f:
    cardata = json.load(f)

records = cardata.get('records', [])
print(f'Total CarData records: {len(records)}')

# Driver list
driver_nums = ['1', '4', '5', '6', '10', '12', '14', '16', '18', '22', '23', '27', '30', '31', '43', '44', '55', '63', '81', '87']

# Track speed history for each driver: {drv: [(time, speed), ...]}
driver_speeds = {d: [] for d in driver_nums}

# Process records - collect speed data
for rec in records:
    ts_str = rec.get('timestamp', '')
    ts = parse_ts(ts_str)
    
    # Only analyze from race start to +30 seconds
    if ts < race_start_ts or ts > race_start_ts + 30:
        continue
    
    entries = rec.get('data', {}).get('Entries', [])
    if not entries:
        continue
    
    cars = entries[0].get('Cars', {})
    
    for drv in driver_nums:
        if drv in cars:
            speed = cars[drv].get('Channels', {}).get('2', 0)
            relative_time = ts - race_start_ts
            driver_speeds[drv].append((relative_time, speed))

# Calculate acceleration times with interpolation
driver_results = {}

for drv, speeds in driver_speeds.items():
    if not speeds:
        driver_results[drv] = {'t50': None, 't100': None, 'max_speed': 0}
        continue
    
    t50, t100 = None, None
    max_spd = 0
    
    for i in range(1, len(speeds)):
        t_prev, v_prev = speeds[i-1]
        t_curr, v_curr = speeds[i]
        max_spd = max(max_spd, v_curr)
        
        # Interpolate for 50 km/h
        if t50 is None and v_prev < 50 <= v_curr:
            t50 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 50)
        
        # Interpolate for 100 km/h
        if t100 is None and v_prev < 100 <= v_curr:
            t100 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 100)
    
    driver_results[drv] = {'t50': t50, 't100': t100, 'max_speed': max_spd}

# Output
names = {
    '1': 'VER', '4': 'NOR', '5': 'BEA', '6': 'TSU', '10': 'GAS',
    '12': 'DOO', '14': 'ALO', '16': 'LEC', '18': 'STR', '22': 'ANT',
    '23': 'ALB', '27': 'HUL', '30': 'RIC', '31': 'OCO', '43': 'COL',
    '44': 'HAM', '55': 'SAI', '63': 'RUS', '81': 'PIA', '87': 'HAD'
}

print()
print('=== Abu Dhabi 2025 - F101 Start Reaction Analysis ===')
print()

# Sort by 0-50 time (reaction time)
sorted_drivers = sorted(driver_results.items(), key=lambda x: x[1]['t50'] or 999)

# ASCII visualization
print('=' * 70)
print('  0-50 km/h 起跑反應時間 (越短越好)')
print('=' * 70)

min_t50 = min(d['t50'] for d in driver_results.values() if d['t50'])
max_t50 = max(d['t50'] for d in driver_results.values() if d['t50'])

for drv, data in sorted_drivers:
    name = names.get(drv, drv)
    t50 = data['t50']
    if t50:
        # Normalize to bar length (max 40 chars)
        bar_len = int((t50 - min_t50) / (max_t50 - min_t50) * 35) + 5
        bar = '#' * bar_len
        print(f'{name:<4} | {t50:.3f}s | {bar}')

print()
print('=' * 70)
print('  0-100 km/h 加速時間')
print('=' * 70)

sorted_by_t100 = sorted(driver_results.items(), key=lambda x: x[1]['t100'] or 999)
min_t100 = min(d['t100'] for d in driver_results.values() if d['t100'])
max_t100 = max(d['t100'] for d in driver_results.values() if d['t100'])

for drv, data in sorted_by_t100:
    name = names.get(drv, drv)
    t100 = data['t100']
    if t100:
        bar_len = int((t100 - min_t100) / (max_t100 - min_t100) * 35) + 5
        bar = '=' * bar_len
        print(f'{name:<4} | {t100:.3f}s | {bar}')

# Load position data for combined analysis
print()
print('=' * 70)
print('  首圈位置變化 (Grid -> Lap 1 End)')
print('=' * 70)

# Get position data
with open(race_dir / 'LapCount.json', 'r', encoding='utf-8') as f:
    lapcount = json.load(f)

lap2_start_ts = None
for rec in lapcount.get('records', []):
    if rec['data'].get('CurrentLap', 0) == 2:
        lap2_start_ts = parse_ts(rec.get('timestamp', ''))
        break

with open(race_dir / 'TimingData.json', 'r', encoding='utf-8') as f:
    timing = json.load(f)

drivers_pos = {}
for rec in timing['records']:
    ts = parse_ts(rec.get('timestamp', ''))
    lines = rec.get('data', {}).get('Lines', {})
    
    for drv, data in lines.items():
        if not isinstance(data, dict):
            continue
        pos = data.get('Position')
        if pos is None:
            continue
        pos = int(pos)
        
        if drv not in drivers_pos:
            drivers_pos[drv] = {'grid': pos, 'lap1_pos': None}
        if drivers_pos[drv]['grid'] is None:
            drivers_pos[drv]['grid'] = pos
        if ts < lap2_start_ts:
            drivers_pos[drv]['lap1_pos'] = pos

# Show position changes
for drv, pos_data in sorted(drivers_pos.items(), key=lambda x: x[1].get('grid', 99)):
    grid = pos_data['grid']
    lap1 = pos_data['lap1_pos']
    name = names.get(drv, f'#{drv}')
    
    if grid and lap1:
        delta = grid - lap1
        if delta > 0:
            arrow = '+' * delta + '>'
            color = '[UP]  '
        elif delta < 0:
            arrow = '<' + '-' * abs(delta)
            color = '[DOWN]'
        else:
            arrow = '='
            color = '[HOLD]'
        print(f'{name:<4} | P{grid:>2} -> P{lap1:>2} | {color} {arrow}')

# Combined ranking
print()
print('=' * 70)
print('  綜合起跑表現排名')
print('=' * 70)
print()

# Calculate combined score
combined = []
for drv in driver_nums:
    name = names.get(drv, drv)
    t50 = driver_results[drv]['t50']
    t100 = driver_results[drv]['t100']
    pos_data = drivers_pos.get(drv, {})
    grid = pos_data.get('grid')
    lap1 = pos_data.get('lap1_pos')
    delta = (grid - lap1) if grid and lap1 else 0
    
    if t50 and t100:
        # Score: lower time = better, position gain = better
        reaction_score = (max_t50 - t50) / (max_t50 - min_t50) * 50  # 0-50 points
        accel_score = (max_t100 - t100) / (max_t100 - min_t100) * 30  # 0-30 points
        position_score = max(0, min(20, delta * 5 + 10))  # -10 to +20 points
        total = reaction_score + accel_score + position_score
        combined.append((name, t50, t100, delta, total))

combined.sort(key=lambda x: -x[4])  # Sort by total score descending

print(f'{"Rank":<4} | {"Driver":<5} | {"0-50":>7} | {"0-100":>7} | {"Pos":>4} | {"Score":>6}')
print('-' * 50)
for i, (name, t50, t100, delta, score) in enumerate(combined, 1):
    delta_str = f'+{delta}' if delta > 0 else str(delta)
    print(f'{i:<4} | {name:<5} | {t50:.3f}s | {t100:.3f}s | {delta_str:>4} | {score:>6.1f}')
