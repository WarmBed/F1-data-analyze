"""
檢查 JSON 中的統一速度範圍資訊
"""

import json

json_file = "json/all_drivers_straight_line_speed_2025_Singapore_R.json"

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("檢查統一速度範圍實現")
print("="*80)

# 檢查 metadata
# 先確認 JSON 結構
if 'data' in data and 'data' in data['data']:
    inner_data = data['data']['data']
elif 'data' in data:
    inner_data = data['data']
else:
    inner_data = data

metadata = inner_data.get('metadata', {})
algorithm_version = inner_data.get('algorithm_version', 'N/A')

print(f"\n算法版本: {algorithm_version}")

# 檢查統一速度範圍
unified_range = metadata.get('unified_speed_range')

if unified_range:
    print("\n✅ 找到統一速度範圍配置:")
    print(f"  起始速度: {unified_range.get('start_speed_kmh', 'N/A')} km/h")
    print(f"  終點速度: {unified_range.get('end_speed_kmh', 'N/A')} km/h")
    print(f"  調整原因: {unified_range.get('adjustment_reason', 'N/A')}")
else:
    print("\n❌ metadata 中未找到 unified_speed_range")

# 檢查 driver_speeds 中的加速數據
driver_speeds = inner_data.get('driver_speeds', [])

if driver_speeds:
    print(f"\n檢查前 3 個車手的加速數據:")
    for i, driver_data in enumerate(driver_speeds[:3]):
        driver = driver_data.get('driver', 'N/A')
        accel_time = driver_data.get('acceleration_time_100_300_seconds', 'N/A')
        avg_accel = driver_data.get('avg_acceleration_100_300_ms2', 'N/A')
        
        print(f"\n{i+1}. {driver}:")
        print(f"   加速時間: {accel_time}")
        print(f"   平均加速度: {avg_accel}")
        
        # 檢查是否有新的速度範圍欄位
        if 'speed_start_kmh' in driver_data or 'speed_end_kmh' in driver_data:
            print(f"   ⚠️  在 driver_data 層級發現速度欄位（不符合扁平化格式）")

print("\n" + "="*80)
