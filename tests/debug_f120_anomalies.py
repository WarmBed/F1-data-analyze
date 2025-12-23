"""
F120 異常值調查腳本
檢查 ANT、ALO、NOR、OCO、PIA 的異常數據
"""

import json
from pathlib import Path

# 載入 JSON
json_file = Path("json/fp2_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers_data = data['mode_a_unified']['drivers']
selected_corners = data['selected_corners']

print("=" * 80)
print("F120 異常值調查")
print("=" * 80)

# 彎道資訊
print("\n選擇的彎道:")
for corner_type, corner_info in selected_corners.items():
    if corner_info:
        print(f"  {corner_type}: T{corner_info['corner_number']}")

# 檢查問題車手
problem_drivers = ['ANT', 'ALO', 'NOR', 'OCO', 'PIA']

for driver_code in problem_drivers:
    driver_data = [d for d in drivers_data if d['driver'] == driver_code]
    if not driver_data:
        print(f"\n❌ 找不到 {driver_code} 的數據")
        continue
    
    driver_data = driver_data[0]
    print(f"\n{'=' * 80}")
    print(f"車手: {driver_code}")
    print(f"{'=' * 80}")
    print(f"總圈數: {driver_data['total_laps']}")
    print(f"過濾統計: {driver_data.get('filtering_summary', {})}")
    
    corners = driver_data.get('corners', {})
    
    for corner_key, stats in corners.items():
        print(f"\n  {corner_key}:")
        print(f"    有效圈數: {stats.get('valid_laps')}")
        print(f"    過濾圈數: {stats.get('filtered_laps')}")
        print(f"    中位數: {stats.get('median_speed')} km/h")
        print(f"    平均數: {stats.get('mean_speed')} km/h")
        print(f"    標準差: {stats.get('std_dev')} km/h")
        print(f"    變異係數: {stats.get('cv')}%")
        print(f"    最小值: {stats.get('min_speed')} km/h")
        print(f"    最大值: {stats.get('max_speed')} km/h")
        print(f"    Q1: {stats.get('q1')} km/h")
        print(f"    Q3: {stats.get('q3')} km/h")
        
        # 顯示原始速度
        speeds = stats.get('speeds_raw', [])
        if speeds:
            print(f"    原始速度數量: {len(speeds)}")
            print(f"    原始速度範例: {speeds[:10]}")
            
            # 檢查異常值
            if len(speeds) > 0:
                speeds_sorted = sorted(speeds)
                print(f"    最慢 3 圈: {speeds_sorted[:3]}")
                print(f"    最快 3 圈: {speeds_sorted[-3:]}")
        
        # 警告
        if 'warnings' in stats:
            print(f"    ⚠️  警告: {stats['warnings']}")

print("\n" + "=" * 80)
print("調查完成")
print("=" * 80)
