"""檢查 Singapore 的 Speed 數據"""
import json

# 讀取 Singapore 數據
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    response = json.load(f)

data = response['data']['data']
driver_speeds = data['driver_speeds']

print("=" * 100)
print("🔍 Singapore All Drivers Speed 數據檢查")
print("=" * 100)

# 檢查前 5 位車手
for i, driver in enumerate(driver_speeds[:5]):
    print(f"\n車手 {i+1}: {driver['driver']} ({driver['team']})")
    print("-" * 100)
    print(f"  最高速度: {driver['max_speed_kmh']} km/h")
    print(f"  segment_accel_time_seconds: {driver.get('segment_accel_time_seconds')} 秒")
    print(f"  max_speed_time_seconds: {driver.get('max_speed_time_seconds')} 秒")
    print(f"  起始速度: {driver.get('segment_start_speed_kmh')} km/h")
    print(f"  統一結束速度: {driver.get('segment_unified_end_speed_kmh')} km/h")
    print(f"  個人最高速度: {driver.get('segment_personal_max_speed_kmh')} km/h")

print("\n" + "=" * 100)
print("🎯 截圖中的數值分析")
print("=" * 100)
print("從截圖中我看到:")
print("  - 'Max Speed Time' 欄位: 約 7.2-8.3 秒")
print("  - 'Accel Time' 欄位: 約 5.7-6.7 秒")
print()
print("從 JSON 數據看到:")
print(f"  - segment_accel_time_seconds: {[driver.get('segment_accel_time_seconds') for driver in driver_speeds[:5]]}")
print(f"  - max_speed_time_seconds: {[driver.get('max_speed_time_seconds') for driver in driver_speeds[:5]]}")
print()
print("❓ 這些數值相符嗎？")
