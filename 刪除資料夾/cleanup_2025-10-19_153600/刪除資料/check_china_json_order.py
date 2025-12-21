"""檢查 China 2025 JSON 數據的原始順序"""
import json

json_file = "json/all_drivers_straight_line_speed_2025_China_R.json"

with open(json_file, 'r', encoding='utf-8') as f:
    full_data = json.load(f)

# 正確的嵌套結構
data = full_data.get("data", {}).get("data", {})
driver_speeds = data.get("driver_speeds", [])
metadata = data.get("metadata", {})
unified_range = metadata.get("unified_speed_range", {})

print("=" * 80)
print(f"China 2025 JSON 原始數據順序")
print("=" * 80)
print(f"統一速度範圍: {unified_range.get('start_speed_kmh')}→{unified_range.get('end_speed_kmh')} km/h")
print(f"總車手數: {len(driver_speeds)}")
print("\n原始 JSON 數據順序（前 10 名）:")
print(f"{'序號':<4} {'車手':<6} {'加速時間':<12} {'最高速度':<12}")
print("-" * 50)

for i, driver in enumerate(driver_speeds[:10], 1):
    driver_code = driver.get("driver", "N/A")
    accel_time = driver.get("acceleration_time_100_310_seconds", 
                           driver.get("acceleration_time_100_300_seconds", None))
    max_speed = driver.get("max_speed_kmh", 0)
    
    if accel_time is None:
        accel_str = "N/A"
    else:
        accel_str = f"{accel_time:.3f}s"
    
    print(f"{i:<4} {driver_code:<6} {accel_str:<12} {max_speed:.1f} km/h")

print("\n" + "=" * 80)
print("按加速時間排序（升序）：")
print("=" * 80)

sorted_by_accel = sorted(
    driver_speeds,
    key=lambda x: x.get("acceleration_time_100_310_seconds", 
                       x.get("acceleration_time_100_300_seconds", 9999))
)

for i, driver in enumerate(sorted_by_accel[:10], 1):
    driver_code = driver.get("driver", "N/A")
    accel_time = driver.get("acceleration_time_100_310_seconds",
                           driver.get("acceleration_time_100_300_seconds", None))
    if accel_time is None:
        accel_str = "N/A"
    else:
        accel_str = f"{accel_time:.3f}s"
    
    print(f"{i:<4} {driver_code:<6} {accel_str}")
