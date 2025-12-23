"""
重新診斷 PIA 和 STR 在 Japan R 的油門數據
使用正確的硬編碼起點：Japan = 5650m
"""

import fastf1
import pandas as pd
import numpy as np

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

print("=" * 80)
print("正在載入 2025 Japan R 賽事數據...")
print("=" * 80)

session = fastf1.get_session(2025, 'Japan', 'R')
session.load()

print("\n✅ 賽事數據載入完成\n")

# Japan 的硬編碼起點
JAPAN_HARDCODED_START = 5650.0

# 分析 PIA 和 STR
drivers_to_check = ['PIA', 'STR']

for driver_code in drivers_to_check:
    print("=" * 80)
    print(f"車手: {driver_code}")
    print("=" * 80)
    
    # 獲取車手數據
    driver_laps = session.laps.pick_driver(driver_code)
    if driver_laps.empty:
        print(f"❌ 沒有找到 {driver_code} 的圈速數據")
        continue
    
    # 找最快圈或有效圈
    valid_laps = driver_laps[driver_laps['LapTime'].notna()]
    if valid_laps.empty:
        print(f"❌ 沒有有效圈速")
        continue
    
    fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]
    lap_number = fastest_lap['LapNumber']
    
    print(f"\n分析圈數: Lap {lap_number}")
    print(f"圈速: {fastest_lap['LapTime']}")
    
    # 獲取遙測數據
    car_data = fastest_lap.get_car_data()
    if car_data is None or car_data.empty:
        print(f"❌ 無法獲取遙測數據")
        continue
    
    # 提取必要欄位
    car_data = car_data.add_distance()
    speeds = car_data['Speed']
    distances = car_data['Distance']
    throttles = car_data['Throttle']
    
    # 找硬編碼起點 5650m 附近
    print(f"\n✅ 硬編碼起點: {JAPAN_HARDCODED_START}m")
    start_mask = (distances >= JAPAN_HARDCODED_START) & (distances <= JAPAN_HARDCODED_START + 100)
    
    if not start_mask.any():
        print(f"❌ 沒有在起點 {JAPAN_HARDCODED_START}m 附近找到數據")
        continue
    
    start_idx = start_mask.idxmax()
    
    print(f"\n起點數據:")
    print(f"  距離: {distances[start_idx]:.1f}m")
    print(f"  速度: {speeds[start_idx]:.1f} km/h")
    print(f"  油門: {throttles[start_idx]:.1f}%")
    
    # 找全圈最高速度
    max_speed_idx = speeds.idxmax()
    max_speed = speeds[max_speed_idx]
    max_speed_distance = distances[max_speed_idx]
    max_speed_throttle = throttles[max_speed_idx]
    
    print(f"\n全圈最高速度:")
    print(f"  速度: {max_speed:.1f} km/h")
    print(f"  距離: {max_speed_distance:.1f}m")
    print(f"  油門: {max_speed_throttle:.1f}%")
    
    # 關鍵分析：從起點開始的油門變化
    print(f"\n油門變化分析（從起點 {distances[start_idx]:.1f}m 開始）:")
    print("-" * 80)
    
    # 檢查起點油門是否 < 95%
    if throttles[start_idx] < 95.0:
        print(f"\n⚠️  起點油門 {throttles[start_idx]:.1f}% < 95%，需要往後找第一個 >= 95% 的點")
        
        future_data = car_data.loc[start_idx:]
        high_throttle_mask = future_data['Throttle'] >= 95.0
        
        if high_throttle_mask.any():
            actual_start_idx = high_throttle_mask[high_throttle_mask].index[0]
            print(f"✅ 找到高油門起點:")
            print(f"  距離: {distances[actual_start_idx]:.1f}m")
            print(f"  速度: {speeds[actual_start_idx]:.1f} km/h")
            print(f"  油門: {throttles[actual_start_idx]:.1f}%")
        else:
            print(f"❌ 沒有找到油門 >= 95% 的點")
            actual_start_idx = start_idx
    else:
        print(f"✅ 起點油門 {throttles[start_idx]:.1f}% >= 95%，無需調整")
        actual_start_idx = start_idx
    
    # 從實際起點開始，找第一個油門 < 95% 的點
    future_data = car_data.loc[actual_start_idx:]
    low_throttle_mask = future_data['Throttle'] < 95.0
    
    if low_throttle_mask.any():
        first_low_throttle_idx = low_throttle_mask[low_throttle_mask].index[0]
        print(f"\n⚠️  第一個油門 < 95% 的點:")
        print(f"  距離: {distances[first_low_throttle_idx]:.1f}m")
        print(f"  速度: {speeds[first_low_throttle_idx]:.1f} km/h")
        print(f"  油門: {throttles[first_low_throttle_idx]:.1f}%")
        
        # 找油門降低前的範圍內最高速度
        future_throttles = throttles.loc[actual_start_idx:]
        loc_in_future = future_throttles.index.get_loc(first_low_throttle_idx)
        
        if loc_in_future > 0:
            last_high_throttle_idx = future_throttles.index[loc_in_future - 1]
            speed_range = speeds.loc[actual_start_idx:last_high_throttle_idx]
            
            if len(speed_range) > 0:
                end_idx = speed_range.idxmax()
                print(f"\n✅ 系統選擇的終點（油門降低前範圍內最高速度）:")
                print(f"  距離: {distances[end_idx]:.1f}m")
                print(f"  速度: {speeds[end_idx]:.1f} km/h")
                print(f"  油門: {throttles[end_idx]:.1f}%")
                
                # 計算加速時間和距離
                time_data = car_data['Time']
                start_time = time_data[actual_start_idx].total_seconds()
                end_time = time_data[end_idx].total_seconds()
                accel_time = end_time - start_time
                accel_distance = distances[end_idx] - distances[actual_start_idx]
                
                print(f"\n加速性能:")
                print(f"  時間: {accel_time:.3f}秒")
                print(f"  距離: {accel_distance:.1f}m")
                print(f"  起點速度: {speeds[actual_start_idx]:.1f} km/h")
                print(f"  終點速度: {speeds[end_idx]:.1f} km/h")
                print(f"  速度增益: {speeds[end_idx] - speeds[actual_start_idx]:.1f} km/h")
                
                print(f"\n🔴 JSON 顯示的數據對比:")
                print(f"  JSON segment_end_speed_kmh: {speeds[end_idx]:.1f} km/h")
                print(f"  JSON distance_m: {max_speed_distance:.1f}m (全圈最高速度位置)")
                print(f"  JSON max_speed_kmh: {max_speed:.1f} km/h (全圈最高速度)")
    else:
        print(f"\n✅ 油門一直保持 >= 95%，沒有提前降低")
        print(f"  終點 = 全圈最高速度點")
    
    print("\n" + "=" * 80 + "\n")

print("\n診斷完成！")
