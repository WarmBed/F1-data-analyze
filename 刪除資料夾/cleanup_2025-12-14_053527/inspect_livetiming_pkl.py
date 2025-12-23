"""
檢查 Live Timing PKL 結構
==========================

用於了解 PKL 快照中實際可用的欄位
"""

import pickle
from pathlib import Path
from pprint import pprint

def inspect_pkl_structure(pkl_path: str):
    """檢查 PKL 結構"""
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
    
    print("=" * 80)
    print("PKL 頂層鍵值:")
    print("=" * 80)
    for key in data.keys():
        value = data[key]
        if isinstance(value, list):
            print(f"{key}: list[{len(value)}]")
        elif isinstance(value, dict):
            print(f"{key}: dict")
        else:
            print(f"{key}: {type(value).__name__}")
    
    print("\n" + "=" * 80)
    print("race_info 內容:")
    print("=" * 80)
    pprint(data.get('race_info', {}))
    
    print("\n" + "=" * 80)
    print("第一個快照 (snapshots[0]) 頂層鍵值:")
    print("=" * 80)
    snapshots = data.get('snapshots', [])
    if snapshots:
        first_snapshot = snapshots[0]
        for key in first_snapshot.keys():
            value = first_snapshot[key]
            if isinstance(value, dict):
                print(f"{key}: dict[{len(value)}]")
            elif isinstance(value, list):
                print(f"{key}: list[{len(value)}]")
            else:
                print(f"{key}: {type(value).__name__} = {value}")
    
    print("\n" + "=" * 80)
    print("第一個快照 - 第一位車手數據 (drivers 的第一筆):")
    print("=" * 80)
    if snapshots and 'drivers' in snapshots[0]:
        drivers = snapshots[0]['drivers']
        if drivers:
            first_driver_num = list(drivers.keys())[0]
            print(f"車手編號: {first_driver_num}")
            print("可用欄位:")
            pprint(drivers[first_driver_num])
    
    # 找一個中段快照（第 30 圈附近）
    print("\n" + "=" * 80)
    print("第 30 圈附近的快照:")
    print("=" * 80)
    for snapshot in snapshots:
        if snapshot.get('current_lap', 0) >= 30:
            print(f"current_lap: {snapshot.get('current_lap')}")
            print(f"race_time: {snapshot.get('race_time')}")
            print(f"drivers 數量: {len(snapshot.get('drivers', {}))}")
            
            drivers = snapshot.get('drivers', {})
            if drivers:
                # 找位置最前的兩位
                sorted_drivers = sorted(
                    [(num, data) for num, data in drivers.items()],
                    key=lambda x: x[1].get('position', 99)
                )
                
                print("\nP1 數據:")
                pprint(sorted_drivers[0][1])
                
                if len(sorted_drivers) > 1:
                    print("\nP2 數據:")
                    pprint(sorted_drivers[1][1])
            
            break  # 只看一個快照

if __name__ == "__main__":
    pkl_path = "data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl"
    
    if not Path(pkl_path).exists():
        print(f"找不到檔案: {pkl_path}")
    else:
        inspect_pkl_structure(pkl_path)
