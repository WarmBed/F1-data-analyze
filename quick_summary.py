#!/usr/bin/env python3
"""快速提取三车手对比摘要"""
import json

with open('json/driver_throttle_ratio_2025_Abu Dhabi_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers_data = data['data']['analysis']['drivers']
target_drivers = ['NOR', 'VER', 'PIA']

print('='*80)
print('2025 Abu Dhabi GP - NOR vs VER vs PIA - Throttle 95% Summary')
print('='*80)
print()

for code in target_drivers:
    driver = next((d for d in drivers_data if d['driver_code'] == code), None)
    if driver:
        laps = driver['laps']
        valid_laps = [l for l in laps if l['lap_time_seconds'] and l['lap_time_seconds'] < 200 and l['full_throttle_ratio']]
        
        if valid_laps:
            avg = sum(l['full_throttle_ratio'] for l in valid_laps) / len(valid_laps) * 100
            max_val = max(l['full_throttle_ratio'] for l in valid_laps) * 100
            min_val = min(l['full_throttle_ratio'] for l in valid_laps) * 100
            
            first_10 = valid_laps[:10]
            last_10 = valid_laps[-10:]
            
            avg_first = sum(l['full_throttle_ratio'] for l in first_10) / len(first_10) * 100
            avg_last = sum(l['full_throttle_ratio'] for l in last_10) / len(last_10) * 100
            trend = avg_last - avg_first
            
            team = driver['team']
            print(f'{code} ({team}):')
            print(f'  Average Throttle 95%: {avg:.2f}%')
            print(f'  Range: {min_val:.2f}% - {max_val:.2f}%')
            print(f'  First 10 laps avg: {avg_first:.2f}%')
            print(f'  Last 10 laps avg: {avg_last:.2f}%')
            trend_dir = "Rising" if trend > 0 else "Falling"
            print(f'  Trend: {trend:+.2f}% ({trend_dir})')
            print(f'  Total valid laps: {len(valid_laps)}')
            print()
