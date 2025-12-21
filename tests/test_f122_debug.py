#!/usr/bin/env python3
"""測試 F122 煞車點偵測"""

import pickle
import pandas as pd
import numpy as np

# 載入數據
data = pickle.load(open('f1_analysis_cache/f1_data_2025_Japan_R.pkl', 'rb'))
session = data['session']
laps = data['laps']

print(f"[INFO] Session type: {type(session)}")
print(f"[INFO] Has car_data: {hasattr(session, 'car_data')}")

if hasattr(session, 'car_data'):
    print(f"[INFO] Driver numbers in car_data: {list(session.car_data.keys())[:5]}")
    
    # 測試第一個車手
    first_driver_num = list(session.car_data.keys())[0]
    car_data = session.car_data[first_driver_num]
    
    print(f"\n[TEST] 測試車手 #{first_driver_num}")
    print(f"  Car data columns: {list(car_data.columns)}")
    print(f"  Car data shape: {car_data.shape}")
    print(f"  Has Speed: {'Speed' in car_data.columns}")
    print(f"  Has Time: {'Time' in car_data.columns}")
    print(f"  Speed range: {car_data['Speed'].min():.1f} - {car_data['Speed'].max():.1f} km/h" if 'Speed' in car_data.columns else "N/A")

# 測試圈數數據
print(f"\n[INFO] Laps data:")
print(f"  Total laps: {len(laps)}")
print(f"  Laps columns: {list(laps.columns)}")
print(f"  Drivers in laps: {laps['Driver'].unique()[:5]}")

# 測試有效圈數過濾
valid_laps = laps[
    (laps['LapTime'].notna()) &
    (~laps['Deleted'])
]
print(f"  Valid laps: {len(valid_laps)}")

# 測試獲取第一個車手的最快圈
first_driver = laps['Driver'].iloc[0]
driver_laps = laps[laps['Driver'] == first_driver]
driver_valid_laps = driver_laps[
    (driver_laps['LapTime'].notna()) &
    (~driver_laps['Deleted'])
]

if not driver_valid_laps.empty:
    fastest_lap = driver_valid_laps.loc[driver_valid_laps['LapTime'].idxmin()]
    print(f"\n[TEST] 車手 {first_driver} 最快圈:")
    print(f"  Lap number: {fastest_lap['LapNumber']}")
    print(f"  Lap time: {fastest_lap['LapTime']}")
    print(f"  Driver number: {fastest_lap['DriverNumber']}")
    
    # 測試獲取該圈 car_data
    driver_number = str(fastest_lap['DriverNumber'])
    if driver_number in session.car_data:
        print(f"  Car data available: YES")
        
        lap_start_time = fastest_lap['LapStartTime']
        lap_time = fastest_lap['LapTime']
        lap_end_time = lap_start_time + lap_time
        
        all_car_data = session.car_data[driver_number]
        
        if 'SessionTime' in all_car_data.columns:
            lap_car_data = all_car_data[
                (all_car_data['SessionTime'] >= lap_start_time) &
                (all_car_data['SessionTime'] <= lap_end_time)
            ]
            print(f"  Lap car_data points: {len(lap_car_data)}")
            
            if len(lap_car_data) > 0:
                # 測試減速度計算
                speeds_ms = lap_car_data['Speed'].values / 3.6
                times = lap_car_data['SessionTime'].values
                
                # 轉換為秒數（支援 numpy.timedelta64）
                times_sec = np.array([t / np.timedelta64(1, 's') for t in times])
                
                # 計算減速度
                decel = np.zeros(len(speeds_ms))
                for i in range(1, len(speeds_ms)):
                    delta_v = speeds_ms[i] - speeds_ms[i-1]
                    delta_t = times_sec[i] - times_sec[i-1]
                    if delta_t > 0:
                        decel[i] = delta_v / delta_t
                
                print(f"  Deceleration range: {decel.min():.2f} to {decel.max():.2f} m/s²")
                print(f"  Min decel (max braking): {decel.min():.2f} m/s²")
                
                # 測試閾值
                for threshold in [-20, -15, -10]:
                    brake_count = np.sum(decel <= threshold)
                    print(f"  Points with decel <= {threshold} m/s²: {brake_count}")
