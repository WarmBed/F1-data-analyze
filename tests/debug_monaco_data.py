#!/usr/bin/env python3
"""調試 Monaco 數據載入"""

import json
import os

def find_2025_data_file(race_number):
    """找到 2025 年特定賽事的最新數據檔案"""
    json_dir = "json/predictionJSON"
    pattern = f"fp_q_data_2025_{race_number}_"
    
    matching_files = [f for f in os.listdir(json_dir) if f.startswith(pattern)]
    if not matching_files:
        return None
    
    # 返回最新的檔案（按時間戳排序）
    matching_files.sort(reverse=True)
    return os.path.join(json_dir, matching_files[0])

# 測試 Monaco (race 6)
data_file = find_2025_data_file(6)
print(f"Monaco FP3/Q 數據檔案: {data_file}")

if data_file:
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"有 practice_sessions: {'practice_sessions' in data}")
    if 'practice_sessions' in data:
        print(f"有 FP3: {'FP3' in data['practice_sessions']}")
    
    print(f"有 qualifying: {'qualifying' in data}")
    print(f"有 drivers: {'drivers' in data}")
    
    if 'drivers' in data:
        print(f"車手數: {len(data['drivers'])}")

# 測試彎角分析檔案
cornering_file = "json/all_drivers_cornering_analysis_2025_Monaco_FP3.json"
print(f"\n彎角分析檔案存在: {os.path.exists(cornering_file)}")

if os.path.exists(cornering_file):
    with open(cornering_file, 'r', encoding='utf-8') as f:
        corner_data = json.load(f)
    
    print(f"有 fastest_lap_analysis: {'fastest_lap_analysis' in corner_data}")
    if 'fastest_lap_analysis' in corner_data:
        drivers = corner_data['fastest_lap_analysis'].get('drivers', [])
        print(f"彎角分析車手數: {len(drivers)}")
        if drivers:
            print(f"第一位車手: {drivers[0]['driver']}")
