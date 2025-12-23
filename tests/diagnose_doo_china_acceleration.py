#!/usr/bin/env python3
"""深度診斷 DOO 2025 China R 的加速時間異常問題"""

import json
import sys

# 讀取 JSON 檔案
json_path = r"C:\Users\mike2\OneDrive\Code\F1-data-analyze\json\all_drivers_straight_line_speed_2025_China_R.json"

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 修正：JSON 結構是 data['data']['driver_speeds']（不是 data['data']['data']）
driver_speeds = data['data']['driver_speeds']
metadata = data['data']['metadata']

print("=" * 80)
print("🔍 2025 China R - Function 48 深度診斷報告")
print("=" * 80)

# 提取統一速度範圍
unified_range = metadata.get('unified_speed_range', {})
print(f"\n📌 統一速度範圍（Metadata）:")
print(f"  起始速度: {unified_range.get('start_speed_kmh', 'N/A')} km/h")
print(f"  終點速度: {unified_range.get('end_speed_kmh', 'N/A')} km/h")
print(f"  調整原因: {unified_range.get('adjustment_reason', 'N/A')}")

# 找到 DOO 和 HAM
doo_data = None
ham_data = None

for driver in driver_speeds:
    if driver['driver'] == 'DOO':
        doo_data = driver
    elif driver['driver'] == 'HAM':
        ham_data = driver

if not doo_data:
    print("\n❌ 找不到 DOO 的數據！")
    sys.exit(1)

if not ham_data:
    print("\n❌ 找不到 HAM 的數據！")
    sys.exit(1)

# 收集所有車手的加速時間
all_accel_times = []
for driver in driver_speeds:
    accel_time = driver.get('segment_accel_time_seconds')
    if accel_time:
        all_accel_times.append({
            'driver': driver['driver'],
            'time': accel_time,
            'start_speed': driver.get('segment_start_speed_kmh'),
            'end_speed': driver.get('segment_end_speed_kmh'),
            'speed_gain': driver.get('segment_speed_gain_kmh'),
            'distance': driver.get('segment_accel_distance_meters'),
            'max_speed': driver.get('max_speed_kmh')
        })

# 排序（按加速時間）
all_accel_times.sort(key=lambda x: x['time'])

print(f"\n📊 所有車手加速時間排序:")
print(f"{'排名':<4} {'車手':<6} {'加速時間':<12} {'起始速度':<12} {'終點速度':<12} {'速度增益':<12} {'距離':<12}")
print("-" * 80)
for rank, data in enumerate(all_accel_times, 1):
    marker = " ⚠️" if data['driver'] == 'DOO' else " ✅" if data['driver'] == 'HAM' else ""
    print(f"{rank:<4} {data['driver']:<6} {data['time']:<12.3f} "
          f"{data['start_speed']:<12.0f} {data['end_speed']:<12.0f} "
          f"{data['speed_gain']:<12.0f} {data['distance']:<12.1f}{marker}")

# 統計分析
times = [d['time'] for d in all_accel_times]
avg_time = sum(times) / len(times)
min_time = min(times)
max_time = max(times)

print(f"\n📈 統計分析:")
print(f"  平均加速時間: {avg_time:.3f}秒")
print(f"  最短加速時間: {min_time:.3f}秒")
print(f"  最長加速時間: {max_time:.3f}秒")
print(f"  標準範圍: {min_time:.3f}s - {max_time:.3f}s")

# DOO 詳細分析
print(f"\n🚨 DOO 異常分析:")
print(f"  車手: {doo_data['driver']} ({doo_data['full_name']})")
print(f"  車隊: {doo_data['team']}")
print(f"  最速圈: 第 {doo_data['lap_number']} 圈")
print(f"  最高速度: {doo_data['max_speed_kmh']:.0f} km/h")
print(f"  DRS: {doo_data['drs']}")
print(f"  在核心範圍內: {doo_data['in_core_range']}")
print(f"\n  ⚠️  Segment 加速數據（異常）:")
print(f"    加速時間: {doo_data['segment_accel_time_seconds']:.3f}秒")
print(f"    加速距離: {doo_data['segment_accel_distance_meters']:.2f}m")
print(f"    起始速度: {doo_data['segment_start_speed_kmh']:.0f} km/h ⚠️ (應接近 {unified_range.get('start_speed_kmh', 'N/A')} km/h)")
print(f"    終點速度: {doo_data['segment_end_speed_kmh']:.0f} km/h")
print(f"    速度增益: {doo_data['segment_speed_gain_kmh']:.0f} km/h ⚠️ (過小)")
print(f"    平均加速度: {doo_data['segment_avg_acceleration_ms2']:.2f} m/s²")
print(f"\n  ✅ 100-300 km/h 加速數據（正常）:")
print(f"    加速時間: {doo_data['acceleration_time_100_300_seconds']:.3f}秒")
print(f"    加速距離: {doo_data['acceleration_distance_100_300_meters']:.2f}m")
print(f"    平均加速度: {doo_data['avg_acceleration_100_300_ms2']:.2f} m/s²")

# HAM 對比
print(f"\n✅ HAM 對比分析:")
print(f"  車手: {ham_data['driver']} ({ham_data['full_name']})")
print(f"  車隊: {ham_data['team']}")
print(f"  最速圈: 第 {ham_data['lap_number']} 圈")
print(f"  最高速度: {ham_data['max_speed_kmh']:.0f} km/h")
print(f"  DRS: {ham_data['drs']}")
print(f"  在核心範圍內: {ham_data['in_core_range']}")
print(f"\n  ✅ Segment 加速數據（正常）:")
print(f"    加速時間: {ham_data['segment_accel_time_seconds']:.3f}秒")
print(f"    加速距離: {ham_data['segment_accel_distance_meters']:.2f}m")
print(f"    起始速度: {ham_data['segment_start_speed_kmh']:.0f} km/h")
print(f"    終點速度: {ham_data['segment_end_speed_kmh']:.0f} km/h")
print(f"    速度增益: {ham_data['segment_speed_gain_kmh']:.0f} km/h")
print(f"    平均加速度: {ham_data['segment_avg_acceleration_ms2']:.2f} m/s²")

# 問題分析
print(f"\n🔍 問題根因分析:")
print(f"\n1. ⚠️  DOO 的起始速度過高:")
print(f"   實際起始: {doo_data['segment_start_speed_kmh']:.0f} km/h")
print(f"   統一起點: {unified_range.get('start_speed_kmh', 'N/A')} km/h")
print(f"   差距: {doo_data['segment_start_speed_kmh'] - unified_range.get('start_speed_kmh', 0):.0f} km/h 過高")
print(f"\n2. ⚠️  DOO 的加速距離過短:")
print(f"   實際距離: {doo_data['segment_accel_distance_meters']:.2f}m")
print(f"   HAM 距離: {ham_data['segment_accel_distance_meters']:.2f}m")
print(f"   差距: {ham_data['segment_accel_distance_meters'] - doo_data['segment_accel_distance_meters']:.2f}m 過短")
print(f"\n3. ⚠️  DOO 的速度增益過小:")
print(f"   實際增益: {doo_data['segment_speed_gain_kmh']:.0f} km/h")
print(f"   HAM 增益: {ham_data['segment_speed_gain_kmh']:.0f} km/h")
print(f"   差距: {ham_data['segment_speed_gain_kmh'] - doo_data['segment_speed_gain_kmh']:.0f} km/h 過小")

print(f"\n💡 推測原因:")
print(f"   CLI 的 _calculate_segment_acceleration_improved() 函數在處理 DOO 時:")
print(f"   1. ❌ 沒有正確找到 {unified_range.get('start_speed_kmh', 'N/A')} km/h 的起點")
print(f"   2. ❌ 錯誤地從 {doo_data['segment_start_speed_kmh']:.0f} km/h 開始計算")
print(f"   3. ❌ 只計算了 {doo_data['segment_start_speed_kmh']:.0f} → {doo_data['segment_end_speed_kmh']:.0f} km/h 的小段加速")
print(f"   4. ⚠️  但「統一速度範圍」邏輯已過時，應該移除")

print(f"\n🎯 建議修正方案:")
print(f"   1. 移除所有「統一速度範圍」邏輯")
print(f"   2. 完全依賴硬編碼距離範圍（hardcoded_start_distance）")
print(f"   3. 檢查 DOO 的遙測數據是否有異常（缺失、跳躍等）")
print(f"   4. 重新執行 CLI -f 48 -y 2025 -r China -s R")

print("\n" + "=" * 80)
