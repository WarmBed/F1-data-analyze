#!/usr/bin/env python3
"""
分析 Live Timing 數據的採樣頻率和速度精度
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

race_dir = Path(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\json\LiveF1\2025\Abu_Dhabi_Race")

# 讀取 CarData
car_data_file = race_dir / 'CarData.json'
with open(car_data_file, 'r', encoding='utf-8') as f:
    car_data = json.load(f)

# 讀取 SessionData 找到比賽開始時間
session_file = race_dir / 'SessionData.json'
with open(session_file, 'r', encoding='utf-8') as f:
    session_data = json.load(f)

def parse_utc_to_seconds(utc_str):
    """解析 ISO UTC 時間為當天秒數"""
    # 格式: "2025-12-07T13:03:27.584Z"
    try:
        dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
        return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1_000_000
    except:
        return None

# 找比賽開始時間 (從 records 陣列中搜索)
race_start_ts = None
race_start_utc = None
for record in session_data.get('records', []):
    data = record.get('data', {})
    status_series = data.get('StatusSeries', {})
    # StatusSeries 可能是 list 或 dict
    if isinstance(status_series, dict):
        for key, entry in status_series.items():
            if entry.get('SessionStatus') == 'Started':
                race_start_utc = entry.get('Utc', '')
                race_start_ts = parse_utc_to_seconds(race_start_utc)
                break
    elif isinstance(status_series, list):
        for entry in status_series:
            if entry.get('SessionStatus') == 'Started':
                race_start_utc = entry.get('Utc', '')
                race_start_ts = parse_utc_to_seconds(race_start_utc)
                break
    if race_start_ts:
        break

print("=" * 70)
print("Live Timing 數據採樣頻率分析")
print("=" * 70)
print(f"\n比賽開始時間 UTC: {race_start_utc}")
print(f"比賽開始時間 (秒): {race_start_ts:.3f}s")

# 分析前 5 秒的數據（起跑階段）
records = car_data.get('records', [])

# 找出車手的速度數據
driver_speeds = defaultdict(list)

for record in records:
    data = record.get('data', {})
    entries = data.get('Entries', [])
    if not entries:
        continue
    
    for entry in entries:
        ts_str = entry.get('Utc', '')
        if not ts_str:
            continue
        
        ts = parse_utc_to_seconds(ts_str)
        if ts is None:
            continue
        
        # 只看比賽開始後 0-5 秒
        if race_start_ts and 0 <= (ts - race_start_ts) <= 5:
            cars = entry.get('Cars', {})
            for drv_num, car_info in cars.items():
                channels = car_info.get('Channels', {})
                speed = channels.get('2', 0)  # Channel 2 = Speed
                if speed > 0:
                    driver_speeds[drv_num].append((ts - race_start_ts, speed))

print(f"\n找到 {len(driver_speeds)} 位車手在起跑 5 秒內有速度數據")

# 分析 VER 的數據
print("\n" + "=" * 70)
print("VER (車手 1) 起跑 5 秒內的速度數據")
print("=" * 70)

ver_speeds = sorted(driver_speeds.get('1', []))
if ver_speeds:
    print(f"\n數據點數量: {len(ver_speeds)}")
    print(f"時間範圍: {ver_speeds[0][0]:.3f}s - {ver_speeds[-1][0]:.3f}s")
    
    # 計算採樣間隔
    intervals = []
    for i in range(1, len(ver_speeds)):
        interval = ver_speeds[i][0] - ver_speeds[i-1][0]
        intervals.append(interval)
    
    if intervals:
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)
        print(f"\n採樣間隔:")
        print(f"  平均: {avg_interval*1000:.1f} ms ({1/avg_interval:.1f} Hz)")
        print(f"  最小: {min_interval*1000:.1f} ms")
        print(f"  最大: {max_interval*1000:.1f} ms")
        print(f"\n理論最大誤差: ±{max_interval*1000:.0f} ms")
    
    print("\n詳細數據點 (前 15 個):")
    print("-" * 50)
    print(f"{'時間(s)':>10} | {'速度(km/h)':>12} | {'間隔(ms)':>10}")
    print("-" * 50)
    
    for i, (t, v) in enumerate(ver_speeds[:15]):
        if i > 0:
            interval = (t - ver_speeds[i-1][0]) * 1000
            print(f"{t:10.3f} | {v:12d} | {interval:10.1f}")
        else:
            print(f"{t:10.3f} | {v:12d} | {'---':>10}")
    
    # 找出達到特定速度的數據點
    print("\n" + "=" * 70)
    print("速度閾值達成分析")
    print("=" * 70)
    
    thresholds = [10, 20, 50]
    for threshold in thresholds:
        found = False
        for i in range(1, len(ver_speeds)):
            t_prev, v_prev = ver_speeds[i-1]
            t_curr, v_curr = ver_speeds[i]
            
            if v_prev < threshold <= v_curr:
                # 有跨越閾值
                print(f"\n0-{threshold} km/h:")
                print(f"  前一點: t={t_prev:.3f}s, v={v_prev} km/h")
                print(f"  後一點: t={t_curr:.3f}s, v={v_curr} km/h")
                print(f"  間隔: {(t_curr-t_prev)*1000:.1f} ms")
                print(f"  速度跳躍: {v_curr - v_prev} km/h")
                
                # 線性插值
                if v_curr != v_prev:
                    ratio = (threshold - v_prev) / (v_curr - v_prev)
                    interpolated_t = t_prev + ratio * (t_curr - t_prev)
                    print(f"  插值時間: {interpolated_t:.3f}s")
                    print(f"  插值誤差範圍: ±{(t_curr-t_prev)*1000/2:.1f} ms")
                
                found = True
                break
        
        if not found:
            print(f"\n0-{threshold} km/h: 未找到跨越點")

# 檢查是否有車手的速度數據直接跳過某個閾值
print("\n" + "=" * 70)
print("所有車手 0-10, 0-20 km/h 數據可用性")
print("=" * 70)

for drv_num in sorted(driver_speeds.keys(), key=lambda x: int(x)):
    speeds = sorted(driver_speeds[drv_num])
    
    has_below_10 = any(v < 10 for t, v in speeds)
    has_above_10 = any(v >= 10 for t, v in speeds)
    has_below_20 = any(v < 20 for t, v in speeds)
    has_above_20 = any(v >= 20 for t, v in speeds)
    
    can_calc_10 = has_below_10 and has_above_10
    can_calc_20 = has_below_20 and has_above_20
    
    first_speed = speeds[0][1] if speeds else 0
    
    print(f"  車手 {drv_num:>2}: 首個速度={first_speed:3d} km/h | 0-10={('✓' if can_calc_10 else '✗')} | 0-20={('✓' if can_calc_20 else '✗')}")
