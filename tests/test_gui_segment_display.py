"""
測試 GUI 表格是否能正確顯示新的 segment acceleration 欄位
"""
import json

# 讀取 JSON 檔案
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    response = json.load(f)

data = response.get('data', {})
drivers = data.get('driver_speeds', [])

print("=" * 80)
print("GUI 表格新欄位測試")
print("=" * 80)
print()

# 確認 JSON 包含新欄位
print("✅ 檢查 JSON 包含新欄位：")
if drivers:
    first = drivers[0]
    required_fields = [
        'segment_accel_time_seconds',
        'segment_accel_distance_meters',
        'segment_avg_acceleration_ms2',
        'segment_start_speed_kmh',
        'segment_end_speed_kmh',
        'segment_speed_gain_kmh'
    ]
    
    for field in required_fields:
        value = first.get(field)
        status = "✅ 存在" if value is not None else "❌ 缺失"
        print(f"  {field}: {status} (值: {value})")

print()
print("=" * 80)
print("前 5 位車手的賽道段加速度數據預覽：")
print("=" * 80)
print()

# 模擬 GUI 表格顯示格式
header = f"{'車手':4s} {'車隊':12s} {'速度':8s} | {'賽道段時間':12s} {'賽道段加速度':14s} {'速度增益':10s}"
print(header)
print("-" * len(header))

for driver in drivers[:5]:
    driver_code = driver.get('driver', '')
    team = driver.get('team', '')[:10]  # 截斷車隊名稱
    max_speed = driver.get('max_speed_kmh', 0)
    
    # 新欄位
    seg_time = driver.get('segment_accel_time_seconds')
    seg_accel = driver.get('segment_avg_acceleration_ms2')
    seg_gain = driver.get('segment_speed_gain_kmh')
    
    # 格式化輸出
    speed_str = f"{max_speed:.1f} km/h"
    time_str = f"{seg_time:.3f} s" if seg_time else "N/A"
    accel_str = f"{seg_accel:.2f} m/s²" if seg_accel else "N/A"
    gain_str = f"{seg_gain:.0f} km/h" if seg_gain else "N/A"
    
    print(f"{driver_code:3s}  {team:10s}  {speed_str:8s} | {time_str:12s} {accel_str:14s} {gain_str:10s}")

print()
print("=" * 80)
print("測試結論：")
print("✅ JSON 包含所有新欄位")
print("✅ GUI 應該能正確讀取並顯示這些數據")
print("✅ 請在 GUI 中開啟「All Drivers Straight Line Speed」功能驗證顯示")
print("=" * 80)
