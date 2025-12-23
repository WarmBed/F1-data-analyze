#!/usr/bin/env python3
"""檢查 2025 彎角分析 JSON 結構"""

import json

# 讀取 Japan FP3 檔案
with open('json/all_drivers_cornering_analysis_2025_Japan_FP3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("檔案結構分析")
print("=" * 70)
print(f"Top-level keys: {list(data.keys())}\n")

# 檢查 fastest_lap_analysis 結構
if 'fastest_lap_analysis' in data:
    drivers = data['fastest_lap_analysis'].get('drivers', [])
    print(f"找到 {len(drivers)} 位車手\n")
    
    if drivers:
        first_driver = drivers[0]
        print(f"第一位車手: {first_driver['driver']}")
        print(f"車手資料欄位: {list(first_driver.keys())}\n")
        
        # 檢查 corners 結構
        if 'corners' in first_driver:
            corners = first_driver['corners']
            print(f"彎角資料欄位: {list(corners.keys())}\n")
            
            # 檢查第一個彎角詳細資料
            first_corner = list(corners.keys())[0]
            print(f"彎角 {first_corner} 的資料:")
            print(f"  {corners[first_corner]}\n")

# 檢查是否有 driver_statistics
if 'driver_statistics' in data:
    stats = data['driver_statistics']
    print(f"\n找到 driver_statistics，共 {len(stats)} 位車手")
    first_driver_key = list(stats.keys())[0]
    print(f"第一位車手: {first_driver_key}")
    print(f"統計欄位: {list(stats[first_driver_key].keys())}")
