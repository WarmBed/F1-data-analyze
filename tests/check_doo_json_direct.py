"""直接檢查 DOO 的 JSON 數據"""
import json

with open('json/all_drivers_straight_line_speed_2025_China_R.json', encoding='utf-8') as f:
    data = json.load(f)

# 找到 DOO 的數據
doo = [d for d in data['data']['driver_speeds'] if d['driver'] == 'DOO'][0]

print("=" * 80)
print("DOO 的完整 Segment 數據:")
print("=" * 80)
print(f"segment_accel_time_seconds: {doo.get('segment_accel_time_seconds')}")
print(f"segment_start_speed_kmh: {doo.get('segment_start_speed_kmh')}")
print(f"segment_end_speed_kmh: {doo.get('segment_end_speed_kmh')}")
print(f"segment_speed_gain_kmh: {doo.get('segment_speed_gain_kmh')}")
print(f"segment_accel_distance_meters: {doo.get('segment_accel_distance_meters')}")
print(f"segment_avg_acceleration_ms2: {doo.get('segment_avg_acceleration_ms2')}")
print()
print(f"Algorithm Version: {data['data'].get('algorithm_version')}")
print("=" * 80)

# 檢查是否有其他車手也有低速度增益的問題
print("\n所有速度增益 < 20 km/h 的車手:")
print("=" * 80)
low_gain_drivers = [
    (d['driver'], d.get('segment_speed_gain_kmh', 0))
    for d in data['data']['driver_speeds']
    if d.get('segment_speed_gain_kmh', 0) < 20
]
for driver, gain in sorted(low_gain_drivers, key=lambda x: x[1]):
    print(f"{driver}: {gain} km/h")
print("=" * 80)
