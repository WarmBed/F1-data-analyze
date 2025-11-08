import json

data = json.load(open('json/all_drivers_straight_line_speed_2025_China_R.json', 'r', encoding='utf-8'))
drivers = data['data']['driver_speeds']

print(f"Driver count: {len(drivers)}")
print(f"Algorithm Version: {data['data'].get('algorithm_version', 'N/A')}")
print(f"Unified End Speed: {data['data'].get('unified_end_speed_kmh', 'N/A')} km/h")

first = drivers[0]
print(f"\nFirst driver: {first.get('driver', 'N/A')}")
print(f"  segment_accel_time_seconds: {first.get('segment_accel_time_seconds', 'N/A')}")
print(f"  max_speed_time_seconds: {first.get('max_speed_time_seconds', 'N/A')}")
print(f"  segment_unified_end_speed_kmh: {first.get('segment_unified_end_speed_kmh', 'N/A')}")
print(f"  segment_personal_max_speed_kmh: {first.get('segment_personal_max_speed_kmh', 'N/A')}")

if "max_speed_time_seconds" in first:
    print("\n✅ JSON 數據包含 'max_speed_time_seconds' 欄位")
else:
    print("\n❌ JSON 數據不包含 'max_speed_time_seconds' 欄位")
