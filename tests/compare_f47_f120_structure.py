import json
from pathlib import Path

# 查找 F47 JSON
f47_files = list(Path('json').glob('all_drivers_cornering_analysis_*.json'))
if f47_files:
    with open(f47_files[0], encoding='utf-8') as f:
        f47_data = json.load(f)
    print("=== F47 JSON 結構 ===")
    print(f"檔案: {f47_files[0].name}")
    print(f"Top keys: {list(f47_data.keys())}")
    
    if 'selected_corners' in f47_data:
        print(f"\nSelected corners: {list(f47_data['selected_corners'].keys())}")
    
    if 'fastest_lap_analysis' in f47_data:
        drivers = f47_data['fastest_lap_analysis'].get('drivers', [])
        if drivers:
            print(f"\n第一位車手: {drivers[0].get('driver')}")
            print(f"Corners keys: {list(drivers[0].get('corners', {}).keys())}")
            
            # 查看第一個彎道的結構
            first_corner = list(drivers[0].get('corners', {}).values())[0] if drivers[0].get('corners') else None
            if first_corner:
                print(f"\n彎道數據結構: {list(first_corner.keys())}")

# 查找 F120 JSON
f120_files = list(Path('json').glob('F120_corner_all_laps_analysis_*.json'))
if f120_files:
    with open(f120_files[0], encoding='utf-8') as f:
        f120_data = json.load(f)
    print("\n\n=== F120 JSON 結構 ===")
    print(f"檔案: {f120_files[0].name}")
    print(f"Top keys: {list(f120_data.keys())}")
    
    if 'mode_a_unified' in f120_data:
        mode_a = f120_data['mode_a_unified']
        drivers = mode_a.get('drivers', [])
        if drivers:
            print(f"\n第一位車手: {drivers[0].get('driver')}")
            print(f"Corners keys: {list(drivers[0].get('corners', {}).keys())}")
            
            # 查看第一個彎道的結構
            first_corner = list(drivers[0].get('corners', {}).values())[0] if drivers[0].get('corners') else None
            if first_corner:
                print(f"\n彎道數據結構: {list(first_corner.keys())}")
