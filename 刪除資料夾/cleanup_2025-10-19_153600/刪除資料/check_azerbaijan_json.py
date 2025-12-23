#!/usr/bin/env python3
"""檢查 Azerbaijan JSON 的數據結構"""

import json

# 讀取 JSON
with open('json/all_drivers_straight_line_speed_2025_Azerbaijan_R.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

print("=== JSON 頂層結構 ===")
print(f"Keys: {list(raw_data.keys())}")
print()

# 雙層嵌套：raw_data['data']['data']
if 'data' in raw_data:
    print("=== 第一層 data 內部結構 ===")
    print(f"Keys: {list(raw_data['data'].keys())}")
    print()
    
    if 'data' in raw_data['data']:
        data = raw_data['data']['data']
        print("=== 第二層 data 內部結構 ===")
        print(f"Keys: {list(data.keys())}")
        print()
        
        # 檢查 driver_speeds
        if 'driver_speeds' in data:
            driver_speeds = data['driver_speeds']
            print(f"=== driver_speeds 數量: {len(driver_speeds)} ===")
            print()
            
            # 顯示前 3 筆和第 10 筆
            for i in [0, 1, 2, 9]:
                if i < len(driver_speeds):
                    d = driver_speeds[i]
                    print(f"--- 車手 {i+1}: {d.get('driver', 'N/A')} ({d.get('team', 'N/A')}) ---")
                    print(json.dumps(d, indent=2, ensure_ascii=False))
                    print()
