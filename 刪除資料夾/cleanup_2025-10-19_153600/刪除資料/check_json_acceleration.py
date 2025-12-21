#!/usr/bin/env python3
"""檢查最新 JSON 的加速數據"""

import json

with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找到 driver_speeds
if 'data' in data:
    if 'data' in data['data']:
        driver_speeds = data['data']['data'].get('driver_speeds', [])
    else:
        driver_speeds = data['data'].get('driver_speeds', [])
else:
    driver_speeds = data.get('driver_speeds', [])

if driver_speeds:
    first_driver = driver_speeds[0]
    print(f"第一名車手: {first_driver['driver']}")
    print(f"最高速度: {first_driver['max_speed_kmh']} km/h")
    print()
    print("加速數據:")
    print(f"  加速時間 (100→300): {first_driver.get('acceleration_time_100_300_seconds', 'N/A')}s")
    print(f"  加速距離 (100→300): {first_driver.get('acceleration_distance_100_300_meters', 'N/A')}m")
    print(f"  平均加速度: {first_driver.get('avg_acceleration_100_300_ms2', 'N/A')} m/s²")
    print(f"  加速連續時間: {first_driver.get('acceleration_continuous_time_seconds', 'N/A')}s")
else:
    print("找不到 driver_speeds")
