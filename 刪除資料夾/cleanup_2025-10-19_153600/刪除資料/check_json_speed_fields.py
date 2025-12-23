"""
檢查 JSON 中的速度欄位
"""

import json

with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 解析 JSON 結構
if 'data' in data and 'data' in data['data']:
    inner_data = data['data']['data']
elif 'data' in data:
    inner_data = data['data']
else:
    inner_data = data

drivers = inner_data.get('driver_speeds', [])

if drivers:
    print("第一個車手 (LAW) 的所有速度/加速度相關欄位:")
    print("="*80)
    
    first_driver = drivers[0]
    for key, value in first_driver.items():
        if 'speed' in key.lower() or 'accel' in key.lower():
            print(f"  {key}: {value}")
