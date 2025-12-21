#!/usr/bin/env python3
"""驗證 VER Lap 17 是否真的有 346.0 km/h"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print("載入 2025 巴西正賽數據...")
session = fastf1.get_session(2025, 'Brazil', 'R')
session.load(laps=True, telemetry=True)

# 檢查 VER Lap 17
ver_laps = session.laps.pick_drivers('VER')
lap17 = ver_laps[ver_laps['LapNumber'] == 17]

if lap17.empty:
    print("❌ 找不到 VER Lap 17")
    exit(1)

print(f"\n📊 VER Lap 17 基本資訊:")
print(f"   圈速: {lap17.iloc[0]['LapTime']}")

telemetry = lap17.iloc[0].get_telemetry()
max_speed = telemetry['Speed'].max()
max_speed_idx = telemetry['Speed'].idxmax()
max_speed_row = telemetry.loc[max_speed_idx]

print(f"\n⚡ 最高速度點:")
print(f"   速度: {max_speed:.1f} km/h")
print(f"   距離: {max_speed_row['Distance']:.1f}m")
print(f"   油門: {max_speed_row['Throttle']:.1f}%")
print(f"   DRS: {max_speed_row['DRS']}")

# 檢查 VER 所有圈
print(f"\n🔍 VER 所有圈的最高速度:")
all_speeds = []
for idx, lap in ver_laps.iterrows():
    lap_num = lap['LapNumber']
    try:
        tel = lap.get_telemetry()
        if not tel.empty and 'Speed' in tel.columns:
            lap_max = float(tel['Speed'].max())
            all_speeds.append({'lap': lap_num, 'speed': lap_max})
            if lap_max >= 340:
                print(f"   Lap {int(lap_num):2d}: {lap_max:5.1f} km/h 🔥")
    except:
        pass

if all_speeds:
    max_lap = max(all_speeds, key=lambda x: x['speed'])
    print(f"\n✅ VER 最高速度: {max_lap['speed']:.1f} km/h (Lap {int(max_lap['lap'])})")
