"""診斷 STR 的搜索範圍問題

檢查為什麼 STR 在加速度計算時只找到 185 km/h，而不是 336 km/h
"""

import json
import fastf1
import pandas as pd

# 載入 2025 中國站數據
session = fastf1.get_session(2025, 'China', 'R')
session.load()

# 獲取 STR 的最速圈
str_laps = session.laps.pick_driver('STR')
fastest_lap = str_laps.pick_fastest()
car_data = fastest_lap.get_car_data().add_distance()

speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
distances = pd.to_numeric(car_data["Distance"], errors="coerce")

# 中國站賽道參數
track_straight_length = 1200  # 中國站直線長度
distance_start = 4600  # 參考直線段起點
distance_end = 5900    # 參考直線段終點

print("=" * 80)
print("STR 2025 中國站速度分析")
print("=" * 80)

# 1. 全圈最高速度
full_lap_max_speed = speeds.max()
full_lap_max_idx = speeds.idxmax()
full_lap_max_distance = distances[full_lap_max_idx]

print(f"\n【全圈數據】")
print(f"  最高速度: {full_lap_max_speed:.1f} km/h")
print(f"  位置: {full_lap_max_distance:.1f} m")
print(f"  索引: {full_lap_max_idx}")

# 2. 擴展範圍內的最高速度（參考範圍 ± 200m）
extended_start = distance_start - 200
extended_end = distance_end + 200
mask_extended = (distances >= extended_start) & (distances <= extended_end)
extended_speeds = speeds[mask_extended]

if not extended_speeds.empty:
    extended_max_speed = extended_speeds.max()
    extended_max_idx = extended_speeds.idxmax()
    extended_max_distance = distances[extended_max_idx]
    
    print(f"\n【擴展範圍內最高速度】")
    print(f"  範圍: {extended_start:.1f} ~ {extended_end:.1f} m")
    print(f"  最高速度: {extended_max_speed:.1f} km/h")
    print(f"  位置: {extended_max_distance:.1f} m")
    print(f"  索引: {extended_max_idx}")
    
    # 使用擴展範圍內的最高速度點計算搜索範圍
    calculated_start = extended_max_distance - (track_straight_length - 100)
    search_start = calculated_start
    search_end = extended_max_distance + 200
    
    print(f"\n【加速度搜索範圍】")
    print(f"  計算公式: max_distance - (straight_length - 100)")
    print(f"  = {extended_max_distance:.1f} - ({track_straight_length} - 100)")
    print(f"  = {extended_max_distance:.1f} - {track_straight_length - 100}")
    print(f"  = {calculated_start:.1f} m")
    print(f"  搜索範圍: {search_start:.1f} ~ {search_end:.1f} m")
    
    # 在搜索範圍內的最高速度
    mask_search = (distances >= search_start) & (distances <= search_end)
    search_speeds = speeds[mask_search]
    
    if not search_speeds.empty:
        search_max_speed = search_speeds.max()
        search_max_idx = search_speeds.idxmax()
        search_max_distance = distances[search_max_idx]
        
        print(f"\n【搜索範圍內的速度數據】")
        print(f"  資料點數量: {len(search_speeds)}")
        print(f"  最高速度: {search_max_speed:.1f} km/h")
        print(f"  位置: {search_max_distance:.1f} m")
        print(f"  最低速度: {search_speeds.min():.1f} km/h")
        
        # 檢查 310 km/h 是否在搜索範圍內
        speeds_above_310 = search_speeds[search_speeds >= 310]
        print(f"\n【310 km/h 檢查】")
        print(f"  搜索範圍內 >= 310 km/h 的點: {len(speeds_above_310)} 個")
        
        if len(speeds_above_310) > 0:
            first_310_idx = speeds_above_310.index[0]
            first_310_distance = distances[first_310_idx]
            print(f"  第一個 >= 310 km/h 的點:")
            print(f"    速度: {speeds_above_310.iloc[0]:.1f} km/h")
            print(f"    位置: {first_310_distance:.1f} m")
            print(f"  ✅ 結論: 310 km/h 在搜索範圍內，應該可以正確計算")
        else:
            print(f"  ❌ 結論: 310 km/h 不在搜索範圍內！")
            print(f"  這就是為什麼系統只找到 {search_max_speed:.1f} km/h")

# 3. 檢查 336 km/h 的位置
speeds_above_330 = speeds[speeds >= 330]
if len(speeds_above_330) > 0:
    first_330_idx = speeds_above_330.index[0]
    first_330_distance = distances[first_330_idx]
    print(f"\n【336 km/h 位置分析】")
    print(f"  >= 330 km/h 的點數量: {len(speeds_above_330)}")
    print(f"  第一個 >= 330 km/h 的點:")
    print(f"    速度: {speeds_above_330.iloc[0]:.1f} km/h")
    print(f"    位置: {first_330_distance:.1f} m")
    print(f"  是否在擴展範圍內 ({extended_start:.1f}~{extended_end:.1f}): {extended_start <= first_330_distance <= extended_end}")
    print(f"  是否在搜索範圍內 ({search_start:.1f}~{search_end:.1f}): {search_start <= first_330_distance <= search_end}")

print("\n" + "=" * 80)
print("問題分析")
print("=" * 80)

print("""
可能的原因：
1. 擴展範圍（distance_start - 200 ~ distance_end + 200）沒有包含全圈最高速度點
2. 系統使用「擴展範圍內的最高速度點」計算搜索範圍，而不是「全圈最高速度點」
3. 導致加速度計算的搜索範圍過窄，錯過了 310 km/h 以上的速度段

解決方案：
- 應該使用「全圈最高速度點」來計算加速度搜索範圍
- 或者擴大「擴展範圍」的容差（從 ±200m 增加到 ±500m）
""")
