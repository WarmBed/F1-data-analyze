"""
檢查統一速度範圍後的加速數據
"""

import json

json_file = "json/all_drivers_straight_line_speed_2025_Singapore_R.json"

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*100)
print("統一速度範圍實施後 - 所有車手加速數據檢查")
print("="*100)

# 獲取數據
if 'data' in data and 'data' in data['data']:
    inner_data = data['data']['data']
elif 'data' in data:
    inner_data = data['data']
else:
    inner_data = data

metadata = inner_data.get('metadata', {})
driver_speeds = inner_data.get('driver_speeds', [])

# 顯示統一速度範圍
unified_range = metadata.get('unified_speed_range', {})
print(f"\n統一速度範圍:")
print(f"  起始: {unified_range.get('start_speed_kmh', 'N/A')} km/h")
print(f"  終點: {unified_range.get('end_speed_kmh', 'N/A')} km/h")
print(f"  調整原因: {unified_range.get('adjustment_reason', 'N/A')}")

# 統計加速數據
print(f"\n所有車手加速數據 (共 {len(driver_speeds)} 個車手):")
print("="*130)
print(f"{'排名':<4} {'車手':<6} {'最高速度':<12} {'起始→終點':<20} {'加速時間':<12} {'平均加速度':<15} {'加速距離':<12}")
print("="*130)

valid_accel_count = 0
accel_times = []
distances = []

for i, driver_data in enumerate(driver_speeds):
    driver = driver_data.get('driver', 'N/A')
    max_speed = driver_data.get('max_speed_kmh', 0)
    accel_time = driver_data.get('acceleration_time_100_300_seconds')
    avg_accel = driver_data.get('avg_acceleration_100_300_ms2')
    accel_dist = driver_data.get('acceleration_distance_100_300_meters')
    
    # ⚠️ 檢查是否有速度範圍資訊（新版 JSON 可能包含）
    # 由於 JSON 結構是扁平化的，速度資訊可能在別的欄位
    # 我們需要從 JSON 中尋找 speed_start_kmh 和 speed_end_kmh
    
    if accel_time is not None and avg_accel is not None:
        valid_accel_count += 1
        accel_times.append(accel_time)
        if accel_dist:
            distances.append(accel_dist)
        
        # 從加速度反推實際速度範圍（假設使用統一範圍）
        # avg_accel = delta_v / time
        # delta_v = avg_accel * time
        delta_v = avg_accel * accel_time  # m/s
        delta_v_kmh = delta_v * 3.6  # km/h
        
        # 假設終點是 250 km/h，反推起始
        assumed_end = 250.0
        calculated_start = assumed_end - delta_v_kmh
        
        speed_range = f"{calculated_start:.1f}→{assumed_end:.1f}"
        
        print(f"{i+1:<4} {driver:<6} {max_speed:.1f} km/h   "
              f"{speed_range:<20} "
              f"{accel_time:.3f}s     {avg_accel:.2f} m/s²      "
              f"{accel_dist:.1f}m" if accel_dist else "N/A")
    else:
        print(f"{i+1:<4} {driver:<6} {max_speed:.1f} km/h   "
              f"{'無加速數據':<80}")

print("="*130)
print(f"\n統計摘要:")
print(f"  有效加速數據: {valid_accel_count}/{len(driver_speeds)} 個車手")

if accel_times:
    print(f"  加速時間範圍: {min(accel_times):.3f}s ~ {max(accel_times):.3f}s")
    print(f"  平均加速時間: {sum(accel_times)/len(accel_times):.3f}s")

if distances:
    print(f"  加速距離範圍: {min(distances):.1f}m ~ {max(distances):.1f}m")
    print(f"  平均加速距離: {sum(distances)/len(distances):.1f}m")

# 驗證理論計算
if unified_range:
    start_speed = unified_range.get('start_speed_kmh', 150)
    end_speed = unified_range.get('end_speed_kmh', 250)
    
    delta_v = (end_speed - start_speed) / 3.6  # m/s
    
    print(f"\n理論驗證 ({start_speed:.0f}→{end_speed:.0f} km/h):")
    print(f"  速度變化: {delta_v:.2f} m/s")
    print(f"  預期加速時間範圍 (假設加速度 7-10 m/s²): {delta_v/10:.3f}s ~ {delta_v/7:.3f}s")
    
    # 檢查異常數據
    print(f"\n異常數據檢查:")
    for driver_data in driver_speeds:
        driver = driver_data.get('driver', 'N/A')
        accel_time = driver_data.get('acceleration_time_100_300_seconds')
        avg_accel = driver_data.get('avg_acceleration_100_300_ms2')
        
        if accel_time and avg_accel:
            # 理論加速度
            theoretical_accel = delta_v / accel_time
            error = abs(theoretical_accel - avg_accel)
            
            if error > 0.5:  # 誤差超過 0.5 m/s²
                print(f"  ⚠️  {driver}: 時間 {accel_time:.3f}s, "
                      f"記錄加速度 {avg_accel:.2f} m/s², "
                      f"理論加速度 {theoretical_accel:.2f} m/s², "
                      f"誤差 {error:.2f} m/s²")

print("\n" + "="*100)
