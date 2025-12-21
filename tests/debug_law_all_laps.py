#!/usr/bin/env python3
"""檢查 LAW 所有圈的速度，模擬 Function 100 的邏輯"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print("載入 2025 巴西正賽數據...")
session = fastf1.get_session(2025, 'Brazil', 'R')
session.load(laps=True, telemetry=True)

# 模擬 Function 100 的邏輯：只檢查最速圈
law_laps = session.laps.pick_drivers('LAW')
print(f"\n📊 LAW 總圈數: {len(law_laps)}")

# Function 100 的邏輯：pick_fastest()
fastest_lap = law_laps.pick_fastest()
fastest_lap_num = fastest_lap['LapNumber']
print(f"\n🏆 Function 100 邏輯：只檢查最速圈")
print(f"   最速圈: Lap {fastest_lap_num}")

fastest_telemetry = fastest_lap.get_telemetry()
print(f"   最速圈最高速度: {fastest_telemetry['Speed'].max():.1f} km/h")

# 檢查所有圈的最高速度
print(f"\n🔍 所有圈的速度比較:")
all_lap_speeds = []
for idx, lap in law_laps.iterrows():
    lap_num = lap['LapNumber']
    try:
        telemetry = lap.get_telemetry()
        if not telemetry.empty and 'Speed' in telemetry.columns:
            max_speed = float(telemetry['Speed'].max())
            all_lap_speeds.append({
                'lap': lap_num,
                'max_speed': max_speed
            })
            
            # 只顯示前 5 圈和最後 5 圈，以及特殊圈
            if lap_num <= 5 or lap_num >= len(law_laps) - 5 or lap_num in [21, 22]:
                marker = "⭐" if lap_num == fastest_lap_num else "🔥" if max_speed >= 335 else ""
                print(f"   Lap {int(lap_num):2d}: {max_speed:5.1f} km/h {marker}")
    except Exception as e:
        print(f"   Lap {int(lap_num):2d}: 無法載入遙測 ({e})")

# 找出實際全賽最高速度
if all_lap_speeds:
    max_speed_lap = max(all_lap_speeds, key=lambda x: x['max_speed'])
    print(f"\n✅ 實際全賽最高速度:")
    print(f"   速度: {max_speed_lap['max_speed']:.1f} km/h")
    print(f"   圈數: Lap {max_speed_lap['lap']}")
    
    if max_speed_lap['lap'] != fastest_lap_num:
        print(f"\n⚠️  最高速度圈 (Lap {max_speed_lap['lap']}) ≠ 最速圈 (Lap {fastest_lap_num})")
        print(f"   這就是為什麼 Function 100 沒找到 336 km/h")
        print(f"   Function 100 只檢查最速圈 (Lap {fastest_lap_num})，該圈最高速度為 {fastest_telemetry['Speed'].max():.1f} km/h")
    else:
        print(f"\n✅ 最高速度圈 = 最速圈")
