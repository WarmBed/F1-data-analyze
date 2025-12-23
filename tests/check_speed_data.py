"""檢查 All Drivers Straight Line Speed 數據"""
import json

# 讀取 Japan 數據
with open('json/all_drivers_straight_line_speed_2025_Japan_R.json', 'r', encoding='utf-8') as f:
    response = json.load(f)

print("=" * 80)
print("檢查 All Drivers Straight Line Speed 數據")
print("=" * 80)
print(f"\nJSON 頂層 keys: {list(response.keys())}\n")

# 提取實際數據
data_level1 = response.get('data', {})
print(f"Data Level 1 keys: {list(data_level1.keys())}\n")

# 再提取一層
data_level2 = data_level1.get('data', {})
print(f"Data Level 2 keys: {list(data_level2.keys())}\n")

# 找出實際的 driver speeds key
driver_speeds = data_level2.get('driver_speeds', [])

if not driver_speeds:
    print("無法找到 driver_speeds 數據！")
    print(f"Data Level 2 內容: {data_level2}")
    exit(1)

print(f"找到 {len(driver_speeds)} 位車手\n")

# 先檢查第一位車手的數據結構
print("第一位車手的 keys:")
print(list(driver_speeds[0].keys()))
print("\n第一位車手的完整數據:")
print(json.dumps(driver_speeds[0], indent=2, ensure_ascii=False))
print("\n" + "=" * 80)

# 檢查前 3 位車手
for i, driver in enumerate(driver_speeds[:3]):
    print(f"\n車手 {i+1}: {driver['driver']} ({driver['team']})")
    print("-" * 80)
    print(f"  最高速度 (max_speed): {driver['max_speed']} km/h")
    print(f"  segment_accel_time_seconds: {driver.get('segment_accel_time_seconds')} 秒")
    print(f"  max_speed_time_seconds: {driver.get('max_speed_time_seconds')} 秒")
    print(f"  起始速度 (segment_start_speed_kmh): {driver.get('segment_start_speed_kmh')} km/h")
    print(f"  結束速度 (segment_end_speed_kmh): {driver.get('segment_end_speed_kmh')} km/h")
    print(f"  個人最高速度 (personal_max_speed_kmh): {driver.get('personal_max_speed_kmh')} km/h")
    print(f"  統一結束速度 (unified_end_speed_kmh): {driver.get('unified_end_speed_kmh')} km/h")

print("\n" + "=" * 80)
print("問題確認:")
print("=" * 80)
print("如果 segment_accel_time < max_speed_time，這邏輯上是不合理的！")
print("\n邏輯應該是：")
print("  - segment_accel_time: 從起始速度加速到統一結束速度的時間（較短時間）")
print("  - max_speed_time: 從起始速度加速到個人最高速度的時間（較長時間）")
print("\n因為 個人最高速度 >= 統一結束速度，所以：")
print("  max_speed_time 應該 >= segment_accel_time")
