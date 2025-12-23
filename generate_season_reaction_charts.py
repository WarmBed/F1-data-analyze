#!/usr/bin/env python3
"""
2025 全賽季起跑反應分布圖
包含：
- Reaction Speed (第二批次速度，綠燈後~2秒)
- 0-10 km/h
- 0-20 km/h
"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime

print("Starting...")

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

TEAM_COLORS = {
    'VER': '#3671C6', 'NOR': '#FF8000', 'PIA': '#FF8000',
    'LEC': '#E8002D', 'SAI': '#E8002D', 'HAM': '#27F4D2', 
    'RUS': '#27F4D2', 'ALO': '#229971', 'STR': '#229971',
    'GAS': '#FF87BC', 'DOO': '#52E252', 'TSU': '#6692FF',
    'LAW': '#6692FF', 'ALB': '#1868DB', 'COL': '#1868DB',
    'HUL': '#B6BABD', 'BEA': '#52E252', 'OCO': '#FF87BC',
    'HAD': '#B6BABD', 'ANT': '#52E252',
}

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


def interpolate_time(t1, v1, t2, v2, target_v):
    if v2 == v1:
        return t1
    ratio = (target_v - v1) / (v2 - v1)
    return t1 + ratio * (t2 - t1)


def analyze_race(race_dir):
    """分析單場賽事，返回 t10, t20, reaction_speed"""
    results = {}
    session_file = race_dir / 'SessionData.json'
    cardata_file = race_dir / 'CarData.json'
    
    if not session_file.exists() or not cardata_file.exists():
        return results
    
    try:
        # 找綠燈時間
        with open(session_file, 'r', encoding='utf-8') as f:
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
        
        if not race_start_ts:
            return results
        
        # 讀取 CarData
        with open(cardata_file, 'r', encoding='utf-8') as f:
            cardata = json.load(f)
        
        # 收集速度數據和批次
        driver_speeds = defaultdict(list)
        batches = []
        
        for rec in cardata.get('records', []):
            ts = parse_timestamp(rec.get('timestamp', ''))
            if ts < race_start_ts or ts > race_start_ts + 30:
                continue
            
            entries = rec.get('data', {}).get('Entries', [])
            if not entries:
                continue
            
            cars = entries[0].get('Cars', {})
            
            # 收集批次數據（前5秒）
            if ts <= race_start_ts + 5:
                batch_speeds = {}
                for drv_num, name in DRIVER_NAMES.items():
                    if drv_num in cars:
                        speed = cars[drv_num].get('Channels', {}).get('2', 0)
                        if speed > 0:
                            batch_speeds[drv_num] = speed
                if batch_speeds:
                    batches.append({'time': ts - race_start_ts, 'speeds': batch_speeds})
            
            # 收集速度歷史（前30秒）
            for drv_num, name in DRIVER_NAMES.items():
                if drv_num in cars:
                    speed = cars[drv_num].get('Channels', {}).get('2', 0)
                    driver_speeds[drv_num].append((ts - race_start_ts, speed))
        
        # 獲取第二批次速度
        reaction_speeds = {}
        if len(batches) >= 2:
            for drv_num, speed in batches[1]['speeds'].items():
                reaction_speeds[drv_num] = speed
        
        # 計算 t10, t20
        for drv_num, speeds in driver_speeds.items():
            if not speeds or len(speeds) < 2:
                continue
            
            name = DRIVER_NAMES.get(drv_num, drv_num)
            speeds.sort(key=lambda x: x[0])
            t10, t20 = None, None
            
            for i in range(1, len(speeds)):
                t_prev, v_prev = speeds[i-1]
                t_curr, v_curr = speeds[i]
                
                if t10 is None and v_prev < 10 <= v_curr:
                    t10 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 10)
                
                if t20 is None and v_prev < 20 <= v_curr:
                    t20 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 20)
            
            if t10 and t20:
                results[name] = {
                    't10': t10,
                    't20': t20,
                    'reaction': reaction_speeds.get(drv_num, 0)
                }
    
    except Exception as e:
        print(f"Error: {e}")
    
    return results


def create_chart(driver_data, metric, title, ylabel, is_speed=False):
    """創建分布圖"""
    driver_data = {k: v for k, v in driver_data.items() if len(v) >= 3}
    
    driver_stats = {}
    for driver, data in driver_data.items():
        values = [d['value'] for d in data]
        driver_stats[driver] = np.median(values)
    
    # 排序：速度從高到低，時間從低到高
    sorted_drivers = sorted(driver_stats.keys(), 
                           key=lambda x: -driver_stats[x] if is_speed else driver_stats[x])
    
    fig, ax = plt.subplots(figsize=(18, 10))
    
    for i, driver in enumerate(sorted_drivers):
        data = driver_data[driver]
        values = [d['value'] for d in data]
        color = TEAM_COLORS.get(driver, '#888888')
        
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        median = np.median(values)
        
        rect = mpatches.Rectangle((i - 0.35, q1), 0.7, q3 - q1,
            facecolor=color, alpha=0.3, edgecolor=color, linewidth=1)
        ax.add_patch(rect)
        ax.hlines(median, i - 0.35, i + 0.35, colors=color, linewidth=2)
        
        jitter = np.random.uniform(-0.25, 0.25, len(values))
        for j, value in enumerate(values):
            race_idx = data[j]['race_idx']
            ax.scatter(i + jitter[j], value, c=color, s=60, alpha=0.8, 
                      edgecolors='white', linewidth=0.5, zorder=5)
            ax.annotate(str(race_idx), (i + jitter[j], value), 
                       fontsize=6, ha='center', va='center', color='white', weight='bold')
    
    ax.set_xticks(range(len(sorted_drivers)))
    ax.set_xticklabels(sorted_drivers, fontsize=11, weight='bold')
    
    for i, driver in enumerate(sorted_drivers):
        color = TEAM_COLORS.get(driver, '#888888')
        ax.get_xticklabels()[i].set_bbox(dict(facecolor=color, alpha=0.7, edgecolor='none', pad=2))
        ax.get_xticklabels()[i].set_color('white')
    
    ax.set_title(title, fontsize=16, weight='bold', pad=20)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_xlabel('Driver', fontsize=12)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    output_path = Path('charts') / f'2025_season_{metric}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()


# Main
base_dir = Path(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\json\LiveF1\2025")
race_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.endswith('_Race')])

print(f"Found {len(race_dirs)} races")

all_data = {}
for idx, race_dir in enumerate(race_dirs, 1):
    race_name = race_dir.name.replace('_Race', '')
    results = analyze_race(race_dir)
    if results:
        all_data[race_name] = {'idx': idx, 'results': results}
        print(f"  {race_name}: {len(results)} drivers")

print(f"Total: {len(all_data)} races")

# 準備各指標的數據
reaction_data = defaultdict(list)
t10_data = defaultdict(list)
t20_data = defaultdict(list)

for race_name, race_info in all_data.items():
    idx = race_info['idx']
    for driver, times in race_info['results'].items():
        if times.get('reaction', 0) > 0:
            reaction_data[driver].append({'value': times['reaction'], 'race_idx': idx})
        if times.get('t10'):
            t10_data[driver].append({'value': times['t10'], 'race_idx': idx})
        if times.get('t20'):
            t20_data[driver].append({'value': times['t20'], 'race_idx': idx})

# 生成三張圖
print("\nGenerating Reaction Speed chart...")
create_chart(reaction_data, 'reaction', 
            '2025 Season Start Reaction Distribution\nReaction Speed at ~2s after green light (Higher = Better)',
            'Speed (km/h)', is_speed=True)

print("Generating 0-10 km/h chart...")
create_chart(t10_data, 't10',
            '2025 Season Start Reaction Distribution\n0-10 km/h (Clutch Reaction)',
            'Time (seconds)', is_speed=False)

print("Generating 0-20 km/h chart...")
create_chart(t20_data, 't20',
            '2025 Season Start Reaction Distribution\n0-20 km/h (Start Reaction)',
            'Time (seconds)', is_speed=False)

print("\nDone!")
