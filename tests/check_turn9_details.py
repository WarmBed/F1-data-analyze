#!/usr/bin/env python3
"""檢查 Turn 9 的詳細數據"""

import json

# 載入 JSON（使用最新的）
with open('json/historical_flags_Japan_2022-2025_20251109_172653.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

corner = data['data']['corner_analysis']['T9']
print('=== Turn 9 詳細數據 ===\n')

for year in sorted(corner['yearly_breakdown'].keys(), reverse=True):
    year_data = corner['yearly_breakdown'][year]
    
    yellow = year_data.get('yellow', 0)
    double_yellow = year_data.get('double_yellow', 0)
    safety_car = year_data.get('safety_car', 0)
    
    # 跳過沒有事件的年份
    if yellow == 0 and double_yellow == 0 and safety_car == 0:
        continue
    
    print(f'{year}:')
    print(f'  Yellow: {yellow}')
    print(f'  Double Yellow: {double_yellow}')
    print(f'  Safety Car: {safety_car}')
    
    messages = year_data.get('messages', [])
    print(f'  Messages: {len(messages)}')
    
    for i, msg in enumerate(messages, 1):
        lap = msg.get('lap', 0)
        flag_type = msg.get('flag_type', '')
        message_text = msg.get('message', '')[:60]
        
        print(f'    Message {i}:')
        print(f'      Lap: {lap}')
        print(f'      Flag Type: {flag_type}')
        print(f'      Message: {message_text}...')
    
    print()
