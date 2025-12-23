"""
診斷 STR 加速度計算問題
詳細檢查 JSON 數據中的所有加速度相關欄位
"""
import json

json_file = "json/all_drivers_straight_line_speed_2025_China_R.json"

with open(json_file, 'r', encoding='utf-8') as f:
    full_data = json.load(f)

data = full_data.get("data", {})
driver_speeds = data.get("driver_speeds", [])
metadata = data.get("metadata", {})
unified_range = metadata.get("unified_speed_range", {})

start_speed = unified_range.get("start_speed_kmh", 100)
end_speed = unified_range.get("end_speed_kmh", 300)

print("=" * 100)
print(f"STR 加速度計算診斷報告 - China 2025")
print("=" * 100)
print(f"\n統一速度範圍: {start_speed}→{end_speed} km/h")
print(f"速度差 Δv = ({end_speed} - {start_speed}) = {end_speed - start_speed} km/h")
print(f"速度差 Δv (m/s) = {(end_speed - start_speed) / 3.6:.2f} m/s")

# 找到 STR
str_data = None
for driver in driver_speeds:
    if driver.get("driver") == "STR":
        str_data = driver
        break

if not str_data:
    print("\n❌ 找不到 STR 數據！")
    exit(1)

print("\n" + "=" * 100)
print("STR 完整數據:")
print("=" * 100)

# 打印所有欄位
for key, value in str_data.items():
    print(f"  {key:<40}: {value}")

print("\n" + "=" * 100)
print("加速度計算驗證:")
print("=" * 100)

# 提取關鍵數據
accel_time = str_data.get("acceleration_time_100_300_seconds")
accel_dist = str_data.get("acceleration_distance_100_300_meters")
avg_accel = str_data.get("avg_acceleration_100_300_ms2")
max_speed = str_data.get("max_speed_kmh")

print(f"\n📊 JSON 數據:")
print(f"  加速時間: {accel_time}s")
print(f"  加速距離: {accel_dist}m")
print(f"  平均加速度: {avg_accel} m/s²")
print(f"  最高速度: {max_speed} km/h")

# 計算驗證
delta_v_ms = (end_speed - start_speed) / 3.6

print(f"\n🔬 計算驗證（使用統一速度範圍 {start_speed}→{end_speed} km/h）:")
print(f"  Δv = ({end_speed} - {start_speed}) / 3.6 = {delta_v_ms:.2f} m/s")
print(f"  Δt = {accel_time}s")
print(f"  a = Δv / Δt = {delta_v_ms:.2f} / {accel_time} = {delta_v_ms / accel_time:.2f} m/s²")
print(f"  JSON 值 = {avg_accel} m/s²")
print(f"  差異 = {abs((delta_v_ms / accel_time) - avg_accel):.2f} m/s²")

# 反推實際使用的速度範圍
actual_delta_v = avg_accel * accel_time
actual_delta_v_kmh = actual_delta_v * 3.6

print(f"\n🔍 反推分析（從 JSON 加速度反推實際速度範圍）:")
print(f"  a = Δv / Δt")
print(f"  Δv = a × Δt = {avg_accel} × {accel_time} = {actual_delta_v:.2f} m/s")
print(f"  Δv (km/h) = {actual_delta_v:.2f} × 3.6 = {actual_delta_v_kmh:.2f} km/h")

# 可能的速度範圍組合
print(f"\n💡 可能的速度範圍:")
possible_ranges = [
    (100, 100 + actual_delta_v_kmh),
    (110, 110 + actual_delta_v_kmh),
    (actual_delta_v_kmh / 2, actual_delta_v_kmh / 2 + actual_delta_v_kmh),
]

for start, end in possible_ranges:
    print(f"  - {start:.1f}→{end:.1f} km/h (差 {end - start:.1f} km/h)")

# 檢查是否有其他加速度相關欄位
print(f"\n🔎 其他可能的加速度欄位:")
accel_keys = [k for k in str_data.keys() if 'accel' in k.lower() or 'speed' in k.lower()]
for key in accel_keys:
    print(f"  {key}: {str_data[key]}")

print("\n" + "=" * 100)
print("結論:")
print("=" * 100)

if abs((delta_v_ms / accel_time) - avg_accel) > 1.0:
    print("❌ STR 的加速度計算明顯錯誤！")
    print(f"   正確值應為: {delta_v_ms / accel_time:.2f} m/s²")
    print(f"   JSON 值為: {avg_accel} m/s²")
    print(f"   誤差: {abs((delta_v_ms / accel_time) - avg_accel):.2f} m/s²")
    print(f"\n💡 可能原因:")
    print(f"   1. 使用了錯誤的速度範圍（{actual_delta_v_kmh:.1f} km/h 而非 {end_speed - start_speed} km/h）")
    print(f"   2. 計算公式有誤")
    print(f"   3. JSON 欄位命名不一致（key 名稱是 100_300 但實際是 {start_speed}_{end_speed}）")
else:
    print("✅ STR 的加速度計算正確！")

print("\n" + "=" * 100)
