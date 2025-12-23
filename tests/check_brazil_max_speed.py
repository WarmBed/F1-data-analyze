#!/usr/bin/env python3
"""驗證 2025 巴西正賽的真實最高速度"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print("載入 2025 巴西正賽數據...")
session = fastf1.get_session(2025, 'Brazil', 'R')
session.load(laps=True, telemetry=True)

drivers = pd.unique(session.laps['Driver'])
print(f"共 {len(drivers)} 位車手")

max_speed = 0.0
max_speed_driver = None
max_speed_lap = None

for driver in drivers:
    try:
        driver_laps = session.laps.pick_drivers(driver)
        fastest_lap = driver_laps.pick_fastest()
        
        if fastest_lap is None or (isinstance(fastest_lap, pd.Series) and fastest_lap.empty):
            print(f"{driver}: 無有效圈速")
            continue
        
        telemetry = fastest_lap.get_telemetry()
        if telemetry is None or telemetry.empty or 'Speed' not in telemetry.columns:
            print(f"{driver}: 無遙測數據")
            continue
        
        lap_max_speed = float(telemetry['Speed'].max())
        lap_number = fastest_lap['LapNumber'] if 'LapNumber' in fastest_lap else None
        
        print(f"{driver}: {lap_max_speed:.1f} km/h (Lap {lap_number})")
        
        if lap_max_speed > max_speed:
            max_speed = lap_max_speed
            max_speed_driver = driver
            max_speed_lap = lap_number
    
    except Exception as e:
        print(f"{driver}: 錯誤 - {e}")

print("\n" + "="*60)
print(f"✅ 全賽事最高速度: {max_speed:.1f} km/h")
print(f"   車手: {max_speed_driver}")
print(f"   圈數: {max_speed_lap}")
print("="*60)
