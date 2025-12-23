#!/usr/bin/env python3
"""調試 LAW Lap 21 的速度數據"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print("載入 2025 巴西正賽數據...")
session = fastf1.get_session(2025, 'Brazil', 'R')
session.load(laps=True, telemetry=True)

# 取得 LAW 的 Lap 21
law_laps = session.laps.pick_drivers('LAW')
lap21 = law_laps[law_laps['LapNumber'] == 21]

if lap21.empty:
    print("❌ 找不到 LAW Lap 21")
    exit(1)

print(f"\n📊 LAW Lap 21 基本資訊:")
print(f"   圈速: {lap21.iloc[0]['LapTime']}")
print(f"   是否最速圈: {lap21.iloc[0]['IsPersonalBest']}")

# 取得遙測數據
telemetry = lap21.iloc[0].get_telemetry()

if telemetry.empty:
    print("❌ 無遙測數據")
    exit(1)

print(f"\n🏁 遙測數據統計:")
print(f"   數據點數: {len(telemetry)}")
print(f"   最高速度: {telemetry['Speed'].max():.1f} km/h")
print(f"   最低速度: {telemetry['Speed'].min():.1f} km/h")
print(f"   距離範圍: {telemetry['Distance'].min():.1f}m - {telemetry['Distance'].max():.1f}m")

# 找出最高速度的位置
max_speed_idx = telemetry['Speed'].idxmax()
max_speed_row = telemetry.loc[max_speed_idx]

print(f"\n⚡ 最高速度點:")
print(f"   速度: {max_speed_row['Speed']:.1f} km/h")
print(f"   距離: {max_speed_row['Distance']:.1f}m")
print(f"   油門: {max_speed_row['Throttle']:.1f}%")
print(f"   DRS: {max_speed_row['DRS']}")
print(f"   時間: {max_speed_row['Time']}")

# 檢查 1205m 附近的速度
print(f"\n🔍 距離 1205m 附近的速度 (±50m):")
nearby = telemetry[(telemetry['Distance'] >= 1155) & (telemetry['Distance'] <= 1255)]
if not nearby.empty:
    print(f"   範圍內數據點: {len(nearby)}")
    print(f"   範圍內最高速度: {nearby['Speed'].max():.1f} km/h")
    print(f"   範圍內最高速度位置: {nearby.loc[nearby['Speed'].idxmax(), 'Distance']:.1f}m")
else:
    print("   ⚠️ 1205m 附近沒有數據點")

# 檢查是否有跨圈合併
print(f"\n🔄 檢查跨圈合併:")
# 取得 Lap 22
lap22 = law_laps[law_laps['LapNumber'] == 22]
if not lap22.empty:
    telemetry22 = lap22.iloc[0].get_telemetry()
    if not telemetry22.empty:
        print(f"   Lap 22 最高速度: {telemetry22['Speed'].max():.1f} km/h")
        print(f"   Lap 22 距離範圍: {telemetry22['Distance'].min():.1f}m - {telemetry22['Distance'].max():.1f}m")
        
        # 檢查 Lap 22 前段 (0-1000m) 是否有更高速度
        lap22_start = telemetry22[telemetry22['Distance'] <= 1000]
        if not lap22_start.empty:
            print(f"   Lap 22 前段 (0-1000m) 最高速度: {lap22_start['Speed'].max():.1f} km/h")

# 檢查最速圈
fastest_lap = law_laps.pick_fastest()
fastest_lap_num = fastest_lap['LapNumber'] if hasattr(fastest_lap, '__getitem__') else None
print(f"\n🏆 LAW 最速圈: Lap {fastest_lap_num}")
if fastest_lap_num:
    fastest_telemetry = fastest_lap.get_telemetry()
    print(f"   最速圈最高速度: {fastest_telemetry['Speed'].max():.1f} km/h")
