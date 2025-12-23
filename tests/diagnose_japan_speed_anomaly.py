"""診斷 Japan R 全車手速度數據 - 找出異常值"""
import json

json_file = "json/all_drivers_straight_line_speed_2025_Japan_R.json"

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

driver_speeds = data["data"]["data"]["driver_speeds"]

print("=" * 100)
print("全車手終點距離與速度分析")
print("=" * 100)

# 按終點距離排序
sorted_by_distance = sorted(driver_speeds, key=lambda x: x["distance_m"])

print("\n按最高速度距離排序：")
print(f"{'排名':<4} {'車手':<6} {'最高速度':<10} {'距離':<10} {'油門%':<8} {'速度增益':<10} {'加速時間':<10} {'狀態'}")
print("-" * 100)

for i, driver in enumerate(sorted_by_distance, 1):
    status = "❌ 異常" if driver["distance_m"] < 6000 else "✅ 正常"
    print(f"{i:<4} {driver['driver']:<6} {driver['max_speed_kmh']:<10.1f} "
          f"{driver['distance_m']:<10.1f} {driver['throttle_percent']:<8.1f} "
          f"{driver['segment_speed_gain_kmh']:<10.1f} {driver['segment_accel_time_seconds']:<10.2f} "
          f"{status}")

# 統計分析
distances = [d["distance_m"] for d in driver_speeds]
speeds = [d["max_speed_kmh"] for d in driver_speeds]
end_speeds = [d["segment_end_speed_kmh"] for d in driver_speeds]

print("\n" + "=" * 100)
print("統計摘要")
print("=" * 100)
print(f"最高速度距離範圍: {min(distances):.1f}m ~ {max(distances):.1f}m")
print(f"最高速度範圍: {min(speeds):.1f} ~ {max(speeds):.1f} km/h")
print(f"終點速度範圍: {min(end_speeds):.1f} ~ {max(end_speeds):.1f} km/h")
print(f"統一終點速度: {driver_speeds[0]['segment_unified_end_speed_kmh']:.1f} km/h")

# 找出異常車手（距離 < 6000m）
abnormal = [d for d in driver_speeds if d["distance_m"] < 6000]
print(f"\n異常車手數量: {len(abnormal)}")
if abnormal:
    print("異常車手詳情:")
    for d in abnormal:
        print(f"  - {d['driver']}: 距離 {d['distance_m']:.1f}m, 速度 {d['max_speed_kmh']:.1f} km/h, "
              f"油門 {d['throttle_percent']:.1f}%, 終點速度 {d['segment_end_speed_kmh']:.1f} km/h")

# 建議的統一終點速度（排除異常值）
normal_end_speeds = [d["segment_end_speed_kmh"] for d in driver_speeds if d["distance_m"] >= 6000]
if normal_end_speeds:
    suggested_unified = min(normal_end_speeds)
    print(f"\n建議的統一終點速度（排除異常車手）: {suggested_unified:.1f} km/h")
    print(f"  (使用距離 >= 6000m 的車手，共 {len(normal_end_speeds)} 位)")
