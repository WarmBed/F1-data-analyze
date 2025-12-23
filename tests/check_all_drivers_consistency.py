"""
檢查 2025 China R 所有車手的加速數據一致性
驗證油門邏輯是否對所有車手都正常工作
"""

import json
from pathlib import Path

# 找到最新的 JSON 檔案
json_dir = Path("json")
json_files = sorted(
    [f for f in json_dir.glob("all_drivers_straight_line_speed_2025_China_R*.json")],
    key=lambda x: x.stat().st_mtime,
    reverse=True
)

if not json_files:
    print("❌ 找不到 JSON 檔案")
    exit(1)

latest_json = json_files[0]
print(f"📁 使用 JSON: {latest_json.name}")
print(f"   修改時間: {latest_json.stat().st_mtime}")
print()

# 載入數據
with open(latest_json, "r", encoding="utf-8") as f:
    data = json.load(f)

# 提取所有車手的 segment 數據
drivers = data["data"]["driver_speeds"]

print("=" * 120)
print(f"🏎️  所有車手的 Segment 加速數據（共 {len(drivers)} 位車手）")
print("=" * 120)
print(f"{'車手':<6} {'加速時間':>10} {'起始速度':>10} {'終點速度':>10} {'速度增益':>10} {'加速距離':>12} {'平均加速度':>12}")
print("-" * 120)

# 按加速時間排序
sorted_drivers = sorted(drivers, key=lambda d: d.get("segment_accel_time_seconds", 0))

for driver in sorted_drivers:
    abbr = driver["driver"]
    accel_time = driver.get("segment_accel_time_seconds", 0)
    start_speed = driver.get("segment_start_speed_kmh", 0)
    end_speed = driver.get("segment_end_speed_kmh", 0)
    speed_gain = driver.get("segment_speed_gain_kmh", 0)
    accel_dist = driver.get("segment_accel_distance_meters", 0)
    avg_accel = driver.get("segment_avg_acceleration_ms2", 0)
    
    # 判斷是否異常
    status = ""
    if accel_time < 7:
        status = " ⚠️ 過短"
    elif accel_time > 15:
        status = " ⚠️ 過長"
    elif speed_gain < 20:
        status = " ⚠️ 速度增益小"
    
    print(f"{abbr:<6} {accel_time:>10.2f}s {start_speed:>10.1f} {end_speed:>10.1f} {speed_gain:>10.1f} {accel_dist:>12.1f}m {avg_accel:>12.2f} m/s²{status}")

print("=" * 120)

# 統計分析
accel_times = [d.get("segment_accel_time_seconds", 0) for d in drivers if d.get("segment_accel_time_seconds")]
speed_gains = [d.get("segment_speed_gain_kmh", 0) for d in drivers if d.get("segment_speed_gain_kmh")]
distances = [d.get("segment_accel_distance_meters", 0) for d in drivers if d.get("segment_accel_distance_meters")]

if accel_times:
    print(f"📊 統計摘要:")
    print(f"   加速時間範圍: {min(accel_times):.2f}s - {max(accel_times):.2f}s (平均: {sum(accel_times)/len(accel_times):.2f}s)")
    print(f"   速度增益範圍: {min(speed_gains):.1f} - {max(speed_gains):.1f} km/h (平均: {sum(speed_gains)/len(speed_gains):.1f} km/h)")
    print(f"   加速距離範圍: {min(distances):.1f}m - {max(distances):.1f}m (平均: {sum(distances)/len(distances):.1f}m)")

# Algorithm Version
algo_version = data["data"].get("algorithm_version", "N/A")
print(f"\n🔧 Algorithm Version: {algo_version}")

print("=" * 120)
