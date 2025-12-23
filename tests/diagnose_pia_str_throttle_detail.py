"""
診斷 PIA 和 STR 在 Japan R 的油門數據
目標：找出為什麼系統在 5747-5771m 停止測量
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
    
    # 找硬編碼起點 3544m 附近
    hardcoded_start = 3544.0
    start_mask = (distances >= hardcoded_start) & (distances <= hardcoded_start + 100)
    
    if not start_mask.any():
        print(f"❌ 沒有在起點 {hardcoded_start}m 附近找到數據")
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
    
    # 關鍵分析：從起點到最高速度之後的油門變化
    print(f"\n油門變化分析（從起點 {distances[start_idx]:.1f}m 開始）:")
    print("-" * 80)
    
    # 找第一個油門 >= 95% 的點
    high_throttle_mask = throttles >= 95.0
    high_throttle_indices = car_data[high_throttle_mask & (distances >= distances[start_idx])].index
    
    if len(high_throttle_indices) > 0:
        first_high_throttle_idx = high_throttle_indices[0]
        print(f"\n✅ 第一個油門 >= 95% 的點:")
        print(f"  距離: {distances[first_high_throttle_idx]:.1f}m")
        print(f"  速度: {speeds[first_high_throttle_idx]:.1f} km/h")
        print(f"  油門: {throttles[first_high_throttle_idx]:.1f}%")
        
        # 從這個點往後找第一個 < 95% 的點
        future_data = car_data.loc[first_high_throttle_idx:]
        low_throttle_mask = future_data['Throttle'] < 95.0
        
        if low_throttle_mask.any():
            first_low_throttle_idx = low_throttle_mask[low_throttle_mask].index[0]
            print(f"\n⚠️  第一個油門 < 95% 的點:")
            print(f"  距離: {distances[first_low_throttle_idx]:.1f}m")
            print(f"  速度: {speeds[first_low_throttle_idx]:.1f} km/h")
            print(f"  油門: {throttles[first_low_throttle_idx]:.1f}%")
            
            # 找油門降低前的範圍內最高速度
            speed_range = speeds.loc[first_high_throttle_idx:first_low_throttle_idx]
            if len(speed_range) > 1:
                # 排除最後一個點（油門已降低）
                speed_range = speeds.loc[first_high_throttle_idx:future_data.index[future_data.index.get_loc(first_low_throttle_idx) - 1]]
            
            if len(speed_range) > 0:
                end_idx = speed_range.idxmax()
                print(f"\n✅ 系統選擇的終點（油門降低前範圍內最高速度）:")
                print(f"  距離: {distances[end_idx]:.1f}m")
                print(f"  速度: {speeds[end_idx]:.1f} km/h")
                print(f"  油門: {throttles[end_idx]:.1f}%")
                print(f"\n🔴 問題: 這個終點距離 {distances[end_idx]:.1f}m 遠早於正常終點 6100-6368m！")
        else:
            print(f"\n✅ 油門一直保持 >= 95%，沒有提前降低")
    else:
        print(f"\n❌ 沒有找到油門 >= 95% 的數據點")
    
    # 檢查 5700-5800m 範圍的油門數據
    print(f"\n詳細檢查 5700-5800m 範圍的油門變化:")
    print("-" * 80)
    distance_range_mask = (distances >= 5700) & (distances <= 5800)
    range_data = car_data[distance_range_mask][['Distance', 'Speed', 'Throttle']]
    
    if not range_data.empty:
        print(range_data.to_string(index=False))
        
        # 檢查是否有 < 95% 的點
        low_throttle_in_range = range_data[range_data['Throttle'] < 95.0]
        if not low_throttle_in_range.empty:
            print(f"\n⚠️  在 5700-5800m 範圍內發現 {len(low_throttle_in_range)} 個油門 < 95% 的點:")
            print(low_throttle_in_range.to_string(index=False))
        else:
            print(f"\n✅ 在 5700-5800m 範圍內所有油門都 >= 95%")
    
    print("\n" + "=" * 80 + "\n")

print("\n診斷完成！")
