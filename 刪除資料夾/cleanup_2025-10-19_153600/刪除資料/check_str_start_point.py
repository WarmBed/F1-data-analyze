"""檢查為什麼 STR 找不到 110 km/h 起始點"""

import json
import fastf1
import pandas as pd

session = fastf1.get_session(2025, 'China', 'R')
session.load()

str_laps = session.laps.pick_driver('STR')
fastest_lap = str_laps.pick_fastest()
car_data = fastest_lap.get_car_data().add_distance()

speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
distances = pd.to_numeric(car_data["Distance"], errors="coerce")

# 搜索範圍
search_start = 3420.0
search_end = 4720.0
max_speed_idx = 293

search_mask = (distances >= search_start) & (distances <= search_end)
search_indices = car_data[search_mask].index
search_indices_before_max = [idx for idx in search_indices if idx <= max_speed_idx]

print("=" * 80)
print("STR 搜索範圍內的速度分析")
print("=" * 80)

print(f"\n【搜索參數】")
print(f"  搜索範圍: {search_start:.1f} ~ {search_end:.1f} m")
print(f"  max_speed_idx: {max_speed_idx}")
print(f"  最高速度點位置: {distances[max_speed_idx]:.1f} m")
print(f"  最高速度點速度: {speeds[max_speed_idx]:.1f} km/h")

print(f"\n【搜索範圍內的數據】")
print(f"  總數據點: {len(search_indices)} 個")
print(f"  最高速度點之前: {len(search_indices_before_max)} 個")

# 檢查搜索範圍內的速度分佈
speeds_in_search = speeds[search_indices_before_max]
print(f"\n【速度分佈】")
print(f"  最小速度: {speeds_in_search.min():.1f} km/h")
print(f"  最大速度: {speeds_in_search.max():.1f} km/h")

# 尋找 <= 110 km/h 的點
speeds_below_110 = speeds_in_search[speeds_in_search <= 110]
print(f"\n【110 km/h 檢查】")
print(f"  <= 110 km/h 的點: {len(speeds_below_110)} 個")

if len(speeds_below_110) > 0:
    print(f"  最接近 110 km/h 的點:")
    closest_idx = (speeds_in_search - 110).abs().idxmin()
    print(f"    索引: {closest_idx}")
    print(f"    速度: {speeds[closest_idx]:.1f} km/h")
    print(f"    位置: {distances[closest_idx]:.1f} m")
else:
    print(f"  ❌ 找不到 <= 110 km/h 的點！")
    print(f"  最低速度: {speeds_in_search.min():.1f} km/h")
    print(f"  原因: 搜索範圍起點太晚，已經超過低速段")

# 檢查全圈是否有 110 km/h
all_speeds_below_110 = speeds[speeds <= 110]
print(f"\n【全圈 110 km/h 檢查】")
print(f"  全圈 <= 110 km/h 的點: {len(all_speeds_below_110)} 個")

if len(all_speeds_below_110) > 0:
    first_110_idx = all_speeds_below_110.index[0]
    last_110_idx = all_speeds_below_110.index[-1]
    print(f"  第一個 <= 110 km/h 的點:")
    print(f"    索引: {first_110_idx}")
    print(f"    速度: {speeds[first_110_idx]:.1f} km/h")
    print(f"    位置: {distances[first_110_idx]:.1f} m")
    print(f"  最後一個 <= 110 km/h 的點:")
    print(f"    索引: {last_110_idx}")
    print(f"    速度: {speeds[last_110_idx]:.1f} km/h")
    print(f"    位置: {distances[last_110_idx]:.1f} m")
    
    print(f"\n  是否在搜索範圍內:")
    print(f"    第一個: {distances[first_110_idx] >= search_start and distances[first_110_idx] <= search_end}")
    print(f"    最後一個: {distances[last_110_idx] >= search_start and distances[last_110_idx] <= search_end}")
    print(f"    是否在 max_speed_idx 之前: {last_110_idx <= max_speed_idx}")

print("\n" + "=" * 80)
print("結論")
print("=" * 80)
print("""
問題根源：
1. 搜索範圍起點 = max_speed_distance - (straight_length - 100)
2. 對於 STR: 4520 - 1100 = 3420 m
3. 但 STR 在 3420 m 之前已經超過 110 km/h
4. 所以搜索範圍內找不到 <= 110 km/h 的點

為什麼沒有回退到全圈搜索？
- 代碼 Line 1148-1158 有「強制全車手模式」處理找不到起點的情況
- 但這個模式會調整 target_speed_low 為搜索範圍內的最小速度
- 而不是使用統一的 110 km/h

修正方案：
✅ 尋找起點時，應該在「整個最速圈」中搜索，不限於搜索範圍
✅ 尋找終點時，也應該在「整個最速圈」中搜索，不限於 max_speed_idx
""")
