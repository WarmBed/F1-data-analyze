"""測試賽道特徵提取"""
import json
from pathlib import Path

track = "Japan"
year = 2024
session = "FP3"

# 測試 F48 速度
f48_file = Path(f"json/all_drivers_straight_line_speed_{year}_{track}_{session}.json")
if f48_file.exists():
    with open(f48_file, 'r', encoding='utf-8') as f:
        speed_data = json.load(f)
    
    print(f"\n=== F48 速度數據結構 ===")
    print(f"Keys: {list(speed_data.keys())}")
    
    drivers = speed_data.get('data', {}).get('driver_speeds', [])
    print(f"車手數量: {len(drivers)}")
    
    if drivers:
        print(f"\n第一個車手數據 keys: {list(drivers[0].keys())}")
        print(f"max_speed_kmh: {drivers[0].get('max_speed_kmh')}")
        print(f"avg_speed: {drivers[0].get('avg_speed')}")  # 檢查是否有 avg_speed 欄位
        
        # 嘗試提取平均速度
        speeds = [d.get('max_speed_kmh') for d in drivers if d.get('max_speed_kmh')]
        print(f"\n所有車手最大速度: {speeds[:5]}...")  # 顯示前5個
        
        import numpy as np
        avg = np.mean(speeds) if speeds else None
        max_speed = np.max(speeds) if speeds else None
        print(f"平均最大速度: {avg} km/h")
        print(f"最大速度: {max_speed} km/h")

# 測試 F54 油門
f54_file = Path(f"json/driver_throttle_ratio_{year}_{track}_{session}.json")
if f54_file.exists():
    with open(f54_file, 'r', encoding='utf-8') as f:
        throttle_data = json.load(f)
    
    print(f"\n=== F54 油門數據結構 ===")
    print(f"Keys: {list(throttle_data.keys())}")
    
    # 檢查數據結構
    data = throttle_data.get('data', {})
    print(f"Data keys: {list(data.keys())}")

# 測試 F34 煞車
f34_file = Path(f"json/brake_performance_{year}_{track}_{session}.json")
if f34_file.exists():
    with open(f34_file, 'r', encoding='utf-8') as f:
        brake_data = json.load(f)
    
    print(f"\n=== F34 煞車數據結構 ===")
    print(f"Keys: {list(brake_data.keys())}")
    
    # 檢查數據結構
    data = brake_data.get('data', {})
    print(f"Data keys: {list(data.keys())}")

# 測試 F47 彎道
f47_file = Path(f"json/all_drivers_cornering_analysis_{year}_{track}_{session}.json")
if f47_file.exists():
    with open(f47_file, 'r', encoding='utf-8') as f:
        corner_data = json.load(f)
    
    print(f"\n=== F47 彎道數據結構 ===")
    print(f"Keys: {list(corner_data.keys())}")
    
    # 檢查數據結構
    data = corner_data.get('data', {})
    print(f"Data keys: {list(data.keys())}")
