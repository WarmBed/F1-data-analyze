"""檢查 v3.3 的新欄位"""
import json

with open('json/all_drivers_straight_line_speed_2025_China_R.json', encoding='utf-8') as f:
    data = json.load(f)

# 檢查 algorithm_version
print("=" * 80)
print(f"Algorithm Version: {data['data'].get('algorithm_version')}")
print(f"Unified End Speed: {data['data'].get('unified_end_speed_kmh')} km/h")
print("=" * 80)
print()

# 檢查 DOO 的數據
doo = [d for d in data['data']['driver_speeds'] if d['driver'] == 'DOO'][0]

print("DOO 的完整數據:")
print("=" * 80)
print(f"segment_accel_time_seconds: {doo.get('segment_accel_time_seconds')}")
print(f"segment_end_speed_kmh: {doo.get('segment_end_speed_kmh')}")
print(f"max_speed_time_seconds: {doo.get('max_speed_time_seconds')} ⭐ 新欄位")
print(f"max_speed_distance_meters: {doo.get('max_speed_distance_meters')} ⭐ 新欄位")
print(f"segment_unified_end_speed_kmh: {doo.get('segment_unified_end_speed_kmh')} ⭐ 新欄位")
print(f"segment_personal_max_speed_kmh: {doo.get('segment_personal_max_speed_kmh')} ⭐ 新欄位")
print("=" * 80)
print()

# 檢查前 5 位車手
print("前 5 位車手的加速時間和最高速度時間對比:")
print("=" * 80)
print(f"{'車手':<6} {'加速時間':>10} {'最高速度時間':>14} {'終點速度':>10} {'個人最高速度':>14}")
print("-" * 80)

for driver_data in data['data']['driver_speeds'][:5]:
    driver = driver_data['driver']
    accel_time = driver_data.get('segment_accel_time_seconds')
    max_time = driver_data.get('max_speed_time_seconds')
    end_speed = driver_data.get('segment_end_speed_kmh')
    personal_max = driver_data.get('segment_personal_max_speed_kmh')
    
    print(f"{driver:<6} {accel_time if accel_time else 'N/A':>10} " +
          f"{max_time if max_time else 'N/A':>14} " +
          f"{end_speed if end_speed else 'N/A':>10} " +
          f"{personal_max if personal_max else 'N/A':>14}")

print("=" * 80)
