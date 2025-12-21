#!/usr/bin/env python3
"""測試 Tooltip 格式輸出"""

import json

# 載入 JSON
with open('json/historical_flags_Japan_2022-2025_20251109_172653.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

corner_data = data['data']['corner_analysis']['T9']
corner_num = corner_data.get('corner_number', '9')
yearly_breakdown = corner_data.get('yearly_breakdown', {})

print(f"Turn {corner_num}")
print("─" * 20)

# 按年份排序
sorted_years = sorted(yearly_breakdown.keys(), reverse=True)

for year in sorted_years:
    year_data = yearly_breakdown[year]
    yellow_count = year_data.get('yellow', 0)
    double_yellow_count = year_data.get('double_yellow', 0)
    safety_car_count = year_data.get('safety_car', 0)
    messages = year_data.get('messages', [])
    
    # 只顯示有事件的年份
    if yellow_count == 0 and double_yellow_count == 0 and safety_car_count == 0:
        continue
    
    print(f"\n{year}:")
    
    # 按 flag_type 分組圈數
    yellow_laps = []
    double_yellow_laps = []
    safety_car_laps = []
    
    for msg in messages:
        lap = msg.get('lap', 0)
        flag_type = msg.get('flag_type', '')
        
        if lap > 0:
            if flag_type == 'yellow':
                yellow_laps.append(lap)
            elif flag_type == 'double_yellow':
                double_yellow_laps.append(lap)
            elif flag_type == 'safety_car':
                safety_car_laps.append(lap)
    
    # 顯示每種旗幟及其圈數
    if yellow_count > 0:
        if yellow_count >= 1:
            print("● Yellow Flag")
        else:
            print("● Yellow Flag (partial)")
        
        for lap in sorted(yellow_laps):
            print(f"  → Lap {lap}")
            
    if double_yellow_count > 0:
        if double_yellow_count >= 1:
            print("● Double Yellow")
        else:
            print("● Double Yellow (partial)")
        
        for lap in sorted(double_yellow_laps):
            print(f"  → Lap {lap}")
            
    if safety_car_count > 0:
        if safety_car_count >= 1:
            print("● Safety Car")
        else:
            print("● Safety Car (partial)")
        
        for lap in sorted(safety_car_laps):
            print(f"  → Lap {lap}")
