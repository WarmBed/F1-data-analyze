"""檢查 JSON 數據結構"""
import json

# 讀取 JSON 檔案
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 獲取第一位車手數據
driver = data['data']['data']['driver_speeds'][0]

print("=" * 50)
print("第一位車手:", driver['driver'])
print("=" * 50)
print("\n所有欄位:")
for key in driver.keys():
    print(f"  - {key}: {driver[key]}")

print("\n" + "=" * 50)
print("加速相關欄位:")
print("=" * 50)
print(f"  acceleration_100_300 存在嗎? {'acceleration_100_300' in driver}")
print(f"  acceleration_time_100_300_seconds: {driver.get('acceleration_time_100_300_seconds')}")
print(f"  acceleration_distance_100_300_meters: {driver.get('acceleration_distance_100_300_meters')}")
print(f"  avg_acceleration_100_300_ms2: {driver.get('avg_acceleration_100_300_ms2')}")

print("\n" + "=" * 50)
print("結論:")
print("=" * 50)
if 'acceleration_100_300' in driver:
    print("✅ JSON 使用嵌套結構 (acceleration_100_300)")
else:
    print("✅ JSON 使用扁平化結構 (acceleration_time_100_300_seconds 等)")
