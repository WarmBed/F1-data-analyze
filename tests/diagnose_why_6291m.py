"""
診斷為什麼終點在 6291m 而不是 700m
驗證全油門點的分佈
"""

import fastf1
import pandas as pd

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

print("=" * 80)
print("正在載入 2025 Japan R 賽事數據...")
print("=" * 80)

session = fastf1.get_session(2025, 'Japan', 'R')
session.load()

print("\n✅ 賽事數據載入完成\n")

# 找最速車手和最速圈
fastest_driver = None
fastest_lap = None
fastest_time = None

for driver in session.drivers:
    driver_code = session.get_driver(driver)['Abbreviation']
    driver_laps = session.laps.pick_driver(driver_code)
    
    if driver_laps.empty:
        continue
    
    valid_laps = driver_laps[driver_laps['LapTime'].notna()]
    if valid_laps.empty:
        continue
    
    min_time = valid_laps['LapTime'].min()
    
    if fastest_time is None or min_time < fastest_time:
        fastest_time = min_time
        fastest_driver = driver_code
        fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]

print(f"最速車手: {fastest_driver}")
print(f"最速圈數: Lap {fastest_lap['LapNumber']}")
print(f"圈速: {fastest_lap['LapTime']}")

# 獲取遙測數據
car_data = fastest_lap.get_car_data()
car_data = car_data.add_distance()

speeds = car_data['Speed']
distances = car_data['Distance']
throttles = car_data['Throttle']

# 硬編碼起點 0m
hardcoded_start = 0.0
start_mask = distances >= hardcoded_start
start_idx = start_mask.idxmax()

print(f"\n硬編碼起點: {hardcoded_start}m")
print(f"實際起點: {distances[start_idx]:.1f}m @ {speeds[start_idx]:.1f} km/h, 油門 {throttles[start_idx]:.1f}%")

# 找所有 throttle >= 99% 的點
print(f"\n掃描全圈油門數據...")
full_throttle_indices = []

for idx in car_data.index:
    if idx < start_idx:
        continue
    
    if idx in throttles.index and not pd.isna(throttles[idx]):
        if throttles[idx] >= 99:
            full_throttle_indices.append(idx)

print(f"✅ 找到 {len(full_throttle_indices)} 個油門 >= 99% 的點")

# 分段顯示
print(f"\n油門 >= 99% 的點分佈:")
print("-" * 80)

if full_throttle_indices:
    # 分組顯示（每 50m 為一組）
    prev_dist = None
    segment_count = 0
    segment_start = None
    
    for idx in full_throttle_indices:
        curr_dist = distances[idx]
        
        # 檢查是否是新的連續段（距離差 > 100m）
        if prev_dist is None or curr_dist - prev_dist > 100:
            if segment_start is not None:
                print(f"  段 {segment_count}: {segment_start:.1f}m - {prev_dist:.1f}m")
            segment_count += 1
            segment_start = curr_dist
        
        prev_dist = curr_dist
    
    # 最後一段
    if segment_start is not None:
        print(f"  段 {segment_count}: {segment_start:.1f}m - {prev_dist:.1f}m")
    
    # 找速度最高的點
    max_speed = -1
    max_speed_idx = None
    
    for idx in full_throttle_indices:
        if speeds[idx] > max_speed:
            max_speed = speeds[idx]
            max_speed_idx = idx
    
    print(f"\n✅ 速度最高的全油門點:")
    print(f"  距離: {distances[max_speed_idx]:.1f}m")
    print(f"  速度: {speeds[max_speed_idx]:.1f} km/h")
    print(f"  油門: {throttles[max_speed_idx]:.1f}%")
    
    print(f"\n🔴 這就是 segment_distance_end = {distances[max_speed_idx]:.1f}m 的原因！")

# 檢查 700m 附近的油門
print(f"\n檢查 700m 附近的油門:")
print("-" * 80)
range_mask = (distances >= 650) & (distances <= 750)
range_data = car_data[range_mask][['Distance', 'Speed', 'Throttle']].head(20)
print(range_data.to_string(index=False))

print("\n診斷完成！")
