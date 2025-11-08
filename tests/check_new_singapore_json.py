"""檢查新的 Singapore JSON 數據"""
import json

with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    response = json.load(f)

data = response['data']['data']
driver_speeds = data['driver_speeds']

print("=" * 100)
print("檢查新生成的 Singapore JSON 數據（前 3 位車手）")
print("=" * 100)

for i, driver in enumerate(driver_speeds[:3]):
    print(f"\n車手 {i+1}: {driver['driver']} ({driver['team']})")
    print("-" * 100)
    print(f"  segment_accel_time_seconds: {driver.get('segment_accel_time_seconds')} 秒")
    print(f"  max_speed_time_seconds: {driver.get('max_speed_time_seconds')} 秒")
    print(f"  統一結束速度: {driver.get('segment_unified_end_speed_kmh')} km/h")
    print(f"  個人最高速度: {driver.get('segment_personal_max_speed_kmh')} km/h")
    
    # 檢查邏輯
    seg_time = driver.get('segment_accel_time_seconds')
    max_time = driver.get('max_speed_time_seconds')
    
    if seg_time and max_time:
        if max_time < seg_time:
            print(f"  ✅ 邏輯正確: max_speed_time ({max_time}s) < segment_accel_time ({seg_time}s)")
        else:
            print(f"  ❌ 邏輯錯誤: max_speed_time ({max_time}s) >= segment_accel_time ({seg_time}s)")

print("\n" + "=" * 100)
print("結論:")
print("=" * 100)
print("如果看到 ✅，表示 CLI 修正成功")
print("如果看到 ❌，表示 JSON 還是舊的，需要重新生成")
