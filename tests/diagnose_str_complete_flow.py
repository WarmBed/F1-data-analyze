"""深度診斷：STR 加速度計算的完整流程

模擬 F48 v2.1 的實際執行流程，找出為什麼只計算到 185 km/h
"""

import json
import fastf1
import pandas as pd
import math

# 載入 2025 中國站數據
print("正在載入 FastF1 數據...")
session = fastf1.get_session(2025, 'China', 'R')
session.load()

# 獲取 STR 的最速圈
str_laps = session.laps.pick_driver('STR')
fastest_lap = str_laps.pick_fastest()
car_data = fastest_lap.get_car_data().add_distance()

speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
distances = pd.to_numeric(car_data["Distance"], errors="coerce")

# 中國站賽道參數
track_straight_length = 1200
distance_start = 4600  # 參考直線段起點
distance_end = 5900    # 參考直線段終點
unified_start_speed = 110  # 統一起始速度
unified_end_speed = 310    # 統一終點速度

print("\n" + "=" * 80)
print("模擬 F48 v2.1 加速度計算流程（STR）")
print("=" * 80)

# ===== 步驟 1: _find_speed_in_position_range =====
print("\n【步驟 1: 在擴展範圍內找最高速度點】")
extended_start = distance_start - 200
extended_end = distance_end + 200
print(f"  參考範圍: {distance_start:.1f} ~ {distance_end:.1f} m")
print(f"  擴展範圍: {extended_start:.1f} ~ {extended_end:.1f} m (±200m)")

mask_extended = (distances >= extended_start) & (distances <= extended_end)
range_speeds = speeds[mask_extended]
range_indices = car_data[mask_extended].index

if not range_speeds.empty:
    max_speed_idx = range_speeds.idxmax()
    max_speed = range_speeds[max_speed_idx]
    max_speed_distance = distances[max_speed_idx]
    
    print(f"\n  找到的最高速度點:")
    print(f"    索引: {max_speed_idx}")
    print(f"    速度: {max_speed:.1f} km/h")
    print(f"    位置: {max_speed_distance:.1f} m")
    
    # ===== 步驟 2: _calculate_acceleration_in_position_range =====
    print("\n【步驟 2: 計算加速度（在位置範圍內）】")
    print(f"  接收到的 max_speed_idx: {max_speed_idx}")
    print(f"  統一起始速度: {unified_start_speed} km/h")
    print(f"  統一終點速度: {unified_end_speed} km/h")
    
    # 計算搜索範圍（基於 max_speed_idx）
    calculated_start = max_speed_distance - (track_straight_length - 100)
    search_distance_start = calculated_start
    search_distance_end = max_speed_distance + 200
    
    print(f"\n  計算加速度搜索範圍:")
    print(f"    公式: max_distance - (straight_length - 100)")
    print(f"    = {max_speed_distance:.1f} - ({track_straight_length} - 100)")
    print(f"    = {max_speed_distance:.1f} - {track_straight_length - 100}")
    print(f"    = {calculated_start:.1f} m")
    print(f"    搜索範圍: {search_distance_start:.1f} ~ {search_distance_end:.1f} m")
    
    # 過濾搜索範圍內的數據
    search_mask = (distances >= search_distance_start) & (distances <= search_distance_end)
    search_indices = car_data[search_mask].index
    
    print(f"    搜索範圍內數據點: {len(search_indices)} 個")
    
    # 如果搜索範圍內沒有數據，回退到整個最速圈
    if len(search_indices) == 0:
        print("  ⚠️  搜索範圍內沒有數據，回退到整個最速圈")
        search_indices = car_data.index
    
    # ===== 步驟 3: 尋找起始點（110 km/h） =====
    print(f"\n【步驟 3: 尋找加速起點（{unified_start_speed} km/h）】")
    
    # 只在最高速度點之前搜索
    search_indices_before_max = [idx for idx in search_indices if idx <= max_speed_idx]
    print(f"  最高速度點之前的數據點: {len(search_indices_before_max)} 個")
    
    speed_start_idx = None
    best_speed_diff = float('inf')
    
    # 優先找到最接近統一起始速度的點
    for idx in reversed(search_indices_before_max):
        if idx not in speeds.index:
            continue
        speed = speeds[idx]
        if math.isnan(speed):
            continue
        
        # 找到速度最接近目標起始速度的點（允許 ±10 km/h 容差）
        if speed <= unified_start_speed + 10:
            speed_diff = abs(speed - unified_start_speed)
            if speed_diff < best_speed_diff:
                best_speed_diff = speed_diff
                speed_start_idx = idx
                if speed_diff < 2:
                    break
    
    if speed_start_idx is not None:
        actual_start_speed = speeds[speed_start_idx]
        start_distance = distances[speed_start_idx]
        print(f"  ✅ 找到起始點:")
        print(f"    索引: {speed_start_idx}")
        print(f"    速度: {actual_start_speed:.1f} km/h (目標: {unified_start_speed} km/h)")
        print(f"    位置: {start_distance:.1f} m")
        print(f"    誤差: {best_speed_diff:.1f} km/h")
    else:
        print(f"  ❌ 找不到起始點！")
    
    # ===== 步驟 4: 尋找終點（310 km/h） =====
    print(f"\n【步驟 4: 尋找加速終點（{unified_end_speed} km/h）】")
    
    if speed_start_idx is None:
        print("  ⚠️  沒有起始點，無法計算加速度")
        speed_end_idx = None
    else:
        speed_end_idx = None
        for idx in car_data.index:
            if idx < speed_start_idx or idx > max_speed_idx:
                continue
            
            if idx not in speeds.index:
                continue
                
            speed = speeds[idx]
            if math.isnan(speed):
                continue
            
            # 找到第一個 >= 目標終點速度的點
            if speed >= unified_end_speed:
                speed_end_idx = idx
                break
        
        if speed_end_idx is not None:
            actual_end_speed = speeds[speed_end_idx]
            end_distance = distances[speed_end_idx]
            print(f"  ✅ 找到終點:")
            print(f"    索引: {speed_end_idx}")
            print(f"    速度: {actual_end_speed:.1f} km/h (目標: {unified_end_speed} km/h)")
            print(f"    位置: {end_distance:.1f} m")
        else:
            print(f"  ❌ 找不到終點！觸發強制全車手模式")
            print(f"\n  【強制全車手模式】")
            print(f"    使用最高速度點作為終點: {max_speed_idx}")
            print(f"    調整目標終點速度: {unified_end_speed} km/h → {speeds[max_speed_idx]:.1f} km/h")
            
            speed_end_idx = max_speed_idx
            target_speed_high = float(speeds[max_speed_idx])
            
            # 計算加速度
            time_start = car_data.loc[speed_start_idx, "Time"]
            time_end = car_data.loc[speed_end_idx, "Time"]
            
            if hasattr(time_start, "total_seconds"):
                time_start_sec = time_start.total_seconds()
            else:
                time_start_sec = float(time_start)
            
            if hasattr(time_end, "total_seconds"):
                time_end_sec = time_end.total_seconds()
            else:
                time_end_sec = float(time_end)
            
            time_diff = time_end_sec - time_start_sec
            
            actual_start_speed = speeds[speed_start_idx]
            velocity_change = (target_speed_high - float(actual_start_speed)) / 3.6
            avg_acceleration = velocity_change / time_diff
            
            print(f"\n  【錯誤的加速度計算】")
            print(f"    Δv = ({target_speed_high:.1f} - {actual_start_speed:.1f}) / 3.6")
            print(f"       = {velocity_change:.2f} m/s")
            print(f"    Δt = {time_diff:.3f} s")
            print(f"    a = {avg_acceleration:.2f} m/s² ❌")
            
            # 正確的計算
            correct_velocity_change = (unified_end_speed - float(actual_start_speed)) / 3.6
            correct_acceleration = correct_velocity_change / time_diff
            
            print(f"\n  【正確的加速度計算】")
            print(f"    Δv = ({unified_end_speed} - {actual_start_speed:.1f}) / 3.6")
            print(f"       = {correct_velocity_change:.2f} m/s")
            print(f"    Δt = {time_diff:.3f} s")
            print(f"    a = {correct_acceleration:.2f} m/s² ✅")
            
            print(f"\n  【誤差分析】")
            print(f"    錯誤加速度: {avg_acceleration:.2f} m/s²")
            print(f"    正確加速度: {correct_acceleration:.2f} m/s²")
            print(f"    誤差: {correct_acceleration - avg_acceleration:.2f} m/s²")

print("\n" + "=" * 80)
print("結論")
print("=" * 80)

print("""
問題確認：
1. 系統在「搜索範圍」（3420~4720m）內尋找 >= 310 km/h 的點
2. 搜索時限定在 speed_start_idx 到 max_speed_idx 之間
3. 如果 max_speed_idx 本身就 < 310 km/h，則永遠找不到終點
4. 觸發強制模式，使用 max_speed_idx 的速度作為終點

根本原因：
- max_speed_idx 是「擴展範圍內的最高速度點」，不是「全圈最高速度點」
- 如果擴展範圍沒有完全包含高速段，max_speed_idx 會指向錯誤的位置
- 系統限定搜索範圍在「speed_start_idx 到 max_speed_idx」之間
- 導致即使搜索範圍內有 310 km/h，也因為超過 max_speed_idx 而被忽略

解決方案：
✅ 修改 Line 1165-1181: 在尋找終點時，不限定 idx <= max_speed_idx
   允許搜索超過 max_speed_idx 的數據點（在搜索範圍內）
""")
