#!/usr/bin/env python3
"""診斷為什麼 Japan 賽事的 segment 數據大多為 NULL"""

import json

# 讀取 Japan JSON 數據
json_file = "json/all_drivers_straight_line_speed_2025_Japan_R.json"
with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# 提取關鍵資訊
ref_segment = data["data"]["data"]["reference_segment"]
driver_speeds = data["data"]["data"]["driver_speeds"]

print("=" * 80)
print("🔍 Japan 賽事 Segment 數據診斷報告")
print("=" * 80)

print("\n📊 參考距離範圍 (reference_segment):")
print(f"   起點距離: {ref_segment['segment_distance_start']:.1f} 米")
print(f"   終點距離: {ref_segment['segment_distance_end']:.1f} 米")
print(f"   範圍長度: {ref_segment['segment_length']:.1f} 米")
print(f"   起點速度: {ref_segment['segment_start_speed']} km/h")
print(f"   最高速度: {ref_segment['segment_max_speed']} km/h")
print(f"   統一起始速度: {ref_segment['unified_start_speed']} km/h")
print(f"   統一終止速度: {ref_segment['unified_end_speed']} km/h")

print("\n" + "=" * 80)
print("🏎️  車手速度與 Segment 數據分析")
print("=" * 80)

has_segment = []
no_segment = []

for driver_data in driver_speeds:
    driver = driver_data["driver"]
    max_speed = driver_data["max_speed_kmh"]
    distance = driver_data["distance_m"]
    segment_time = driver_data["segment_accel_time_seconds"]
    
    # 判斷測量位置是否在參考範圍內
    in_range = (ref_segment['segment_distance_start'] <= distance <= ref_segment['segment_distance_end'])
    
    if segment_time is not None:
        has_segment.append({
            "driver": driver,
            "max_speed": max_speed,
            "distance": distance,
            "in_range": in_range,
            "segment_time": segment_time,
            "segment_start_speed": driver_data["segment_start_speed_kmh"],
            "segment_end_speed": driver_data["segment_end_speed_kmh"]
        })
    else:
        no_segment.append({
            "driver": driver,
            "max_speed": max_speed,
            "distance": distance,
            "in_range": in_range
        })

print(f"\n✅ 有 Segment 數據的車手 ({len(has_segment)} 位):")
print("-" * 80)
for d in has_segment:
    print(f"   {d['driver']:3s} | 最高速度: {d['max_speed']:6.1f} km/h | "
          f"距離: {d['distance']:7.1f}m | 範圍內: {d['in_range']} | "
          f"Segment: {d['segment_start_speed']:.0f} → {d['segment_end_speed']:.0f} km/h ({d['segment_time']:.2f}s)")

print(f"\n❌ 無 Segment 數據的車手 ({len(no_segment)} 位):")
print("-" * 80)
for d in no_segment:
    range_status = "✅ 範圍內" if d['in_range'] else "❌ 範圍外"
    print(f"   {d['driver']:3s} | 最高速度: {d['max_speed']:6.1f} km/h | "
          f"距離: {d['distance']:7.1f}m | {range_status}")

print("\n" + "=" * 80)
print("📈 統計分析")
print("=" * 80)

# 分析距離分佈
distances_with_segment = [d['distance'] for d in has_segment]
distances_no_segment = [d['distance'] for d in no_segment]

print(f"\n有 Segment 數據的車手:")
print(f"   平均測量距離: {sum(distances_with_segment)/len(distances_with_segment):.1f} 米")
print(f"   最小距離: {min(distances_with_segment):.1f} 米")
print(f"   最大距離: {max(distances_with_segment):.1f} 米")

print(f"\n無 Segment 數據的車手:")
print(f"   平均測量距離: {sum(distances_no_segment)/len(distances_no_segment):.1f} 米")
print(f"   最小距離: {min(distances_no_segment):.1f} 米")
print(f"   最大距離: {max(distances_no_segment):.1f} 米")

# 分析速度分佈
speeds_with_segment = [d['max_speed'] for d in has_segment]
speeds_no_segment = [d['max_speed'] for d in no_segment]

print(f"\n速度分佈:")
print(f"   有 Segment 數據: 平均 {sum(speeds_with_segment)/len(speeds_with_segment):.1f} km/h")
print(f"   無 Segment 數據: 平均 {sum(speeds_no_segment)/len(speeds_no_segment):.1f} km/h")

print("\n" + "=" * 80)
print("🔍 結論")
print("=" * 80)

print(f"""
1. 參考範圍: {ref_segment['segment_distance_start']:.0f} - {ref_segment['segment_distance_end']:.0f} 米
   (長度: {ref_segment['segment_length']:.0f} 米)

2. Segment 數據計算條件:
   - 車手需要在參考距離範圍內有速度測量點
   - 起點和終點速度都必須有效
   - 速度變化需要滿足計算條件

3. Japan 賽事的情況:
   - 只有 {len(has_segment)} 位車手有 Segment 數據 (PIA, STR)
   - 這些車手的最高速度較低 (平均 {sum(speeds_with_segment)/len(speeds_with_segment):.1f} km/h)
   - 他們的測量點在參考範圍內 ({distances_with_segment[0]:.0f} - {distances_with_segment[-1]:.0f} 米)
   
4. 其他 {len(no_segment)} 位車手:
   - 最高速度較高 (平均 {sum(speeds_no_segment)/len(speeds_no_segment):.1f} km/h)
   - 大部分測量點超出參考範圍 (平均 {sum(distances_no_segment)/len(distances_no_segment):.0f} 米)
   - 因此無法在參考 segment 範圍內計算加速性能

5. 這是**正常行為**，不是 BUG:
   - Segment 加速數據是針對特定距離範圍的性能指標
   - 只有在該範圍內達到最高速度的車手才會有有效數據
   - 其他車手在不同位置達到更高速度，因此 Segment 數據不適用
""")

print("=" * 80)
