#!/usr/bin/env python3
"""驗證 time_difference 數據"""

import json
import statistics

# 讀取 JSON 文件
with open('json/comparison_telemetry_VER_LEC_2025_Australia_R_Lap99_Lap99.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 獲取 time_difference 區塊
td = data['results']['time_difference']

print("=" * 80)
print("Time Difference 數據驗證")
print("=" * 80)

print("\n✅ Time Difference 區塊鍵:", list(td.keys()))

print("\n📊 reference_time (共同時間軸):")
print(f"   數據點: {len(td['reference_time'])} 點")
print(f"   時間範圍: {td['reference_time'][0]:.2f}s - {td['reference_time'][-1]:.2f}s")

print("\n📊 cumulative_time_difference (累積時間差):")
print(f"   數據點: {len(td['cumulative_time_difference'])} 點")
print(f"   時間差範圍: {min(td['cumulative_time_difference']):.3f}s - {max(td['cumulative_time_difference']):.3f}s")
print(f"   平均時間差: {statistics.mean(td['cumulative_time_difference']):.3f}s")

print("\n📊 distance_gap (距離差):")
if 'distance_gap' in td:
    print(f"   數據點: {len(td['distance_gap'])} 點")
    print(f"   距離差範圍: {min(td['distance_gap']):.2f}m - {max(td['distance_gap']):.2f}m")
    print(f"   平均距離差: {statistics.mean(td['distance_gap']):.2f}m")

print("\n📊 driver1_distance_at_time (VER 在各時間點的距離):")
if 'driver1_distance_at_time' in td:
    print(f"   數據點: {len(td['driver1_distance_at_time'])} 點")
    print(f"   距離範圍: {td['driver1_distance_at_time'][0]:.2f}m - {td['driver1_distance_at_time'][-1]:.2f}m")

print("\n📊 driver2_distance_at_time (LEC 在各時間點的距離):")
if 'driver2_distance_at_time' in td:
    print(f"   數據點: {len(td['driver2_distance_at_time'])} 點")
    print(f"   距離範圍: {td['driver2_distance_at_time'][0]:.2f}m - {td['driver2_distance_at_time'][-1]:.2f}m")

print("\n📊 統計資訊:")
if 'time_diff_stats' in td:
    print(f"   最大時間差: {td['time_diff_stats']['max_diff']:.3f}s")
    print(f"   最小時間差: {td['time_diff_stats']['min_diff']:.3f}s")
    print(f"   平均時間差: {td['time_diff_stats']['mean_diff']:.3f}s")

if 'distance_gap_stats' in td:
    print(f"   最大距離差: {td['distance_gap_stats']['max_gap']:.2f}m")
    print(f"   最小距離差: {td['distance_gap_stats']['min_gap']:.2f}m")
    print(f"   平均距離差: {td['distance_gap_stats']['mean_gap']:.2f}m")

print("\n" + "=" * 80)
print("✅ Time Difference 數據驗證完成！")
print("=" * 80)
