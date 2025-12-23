#!/usr/bin/env python3
"""檢查 Historical Track Map 使用的最速圈是否包含 DRS 數據"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print("測試 2024 巴西賽道的最速圈 DRS 數據...")
print("=" * 80)

session = fastf1.get_session(2024, 'Brazil', 'R')
session.load()

# 模擬 Historical Track Map 的邏輯
laps = session.laps
fastest_lap = laps.pick_fastest()

if fastest_lap is not None:
    driver = fastest_lap['Driver']
    lap_time = fastest_lap['LapTime']
    lap_num = fastest_lap['LapNumber']
    
    print(f"\n📊 2024 巴西最速圈資訊:")
    print(f"   車手: {driver}")
    print(f"   圈數: Lap {lap_num}")
    print(f"   圈速: {lap_time}")
    
    # 獲取遙測數據
    telemetry = fastest_lap.get_telemetry()
    
    print(f"\n🔍 遙測數據欄位:")
    print(f"   {telemetry.columns.tolist()}")
    
    # 檢查 DRS 數據
    if 'DRS' in telemetry.columns:
        drs_values = telemetry['DRS'].unique()
        print(f"\n✅ DRS 欄位存在！")
        print(f"   DRS 值: {sorted(drs_values)}")
        
        # 統計 DRS 使用情況
        drs_active = telemetry[telemetry['DRS'] >= 10]
        print(f"\n📈 DRS 使用統計:")
        print(f"   總數據點: {len(telemetry)}")
        print(f"   DRS 開啟點: {len(drs_active)} ({len(drs_active)/len(telemetry)*100:.1f}%)")
        
        if len(drs_active) > 0:
            # 識別 DRS 區域
            drs_active_sorted = drs_active.sort_values('Distance')
            
            zones = []
            current_start = None
            current_end = None
            
            for idx, row in drs_active_sorted.iterrows():
                if current_start is None:
                    current_start = row['Distance']
                    current_end = row['Distance']
                else:
                    gap = row['Distance'] - current_end
                    if gap > 100:
                        zones.append((current_start, current_end))
                        current_start = row['Distance']
                        current_end = row['Distance']
                    else:
                        current_end = row['Distance']
            
            if current_start is not None:
                zones.append((current_start, current_end))
            
            print(f"\n🗺️ DRS 區域:")
            for i, (start, end) in enumerate(zones, 1):
                length = end - start
                print(f"   區域 {i}: {start:6.0f}m - {end:6.0f}m (長度: {length:4.0f}m)")
            
            print(f"\n✅ 結論: 最速圈**有** DRS 數據，可以顯示在歷史賽道地圖上！")
        else:
            print(f"\n⚠️ 注意: 最速圈中 DRS 未開啟（可能是排位賽或 DRS 不可用）")
    else:
        print(f"\n❌ DRS 欄位不存在")
        print(f"   可能原因: 舊版數據或數據不完整")

# 測試多個賽道
print(f"\n" + "=" * 80)
print(f"測試其他賽道的 DRS 數據...")
print("=" * 80)

test_tracks = [
    ('Monza', 2024),  # 著名的高速賽道
    ('Monaco', 2024), # 街道賽
    ('Spa', 2024),    # 長直線賽道
]

for track, year in test_tracks:
    try:
        session = fastf1.get_session(year, track, 'R')
        session.load()
        fastest_lap = session.laps.pick_fastest()
        
        if fastest_lap is not None:
            telemetry = fastest_lap.get_telemetry()
            has_drs = 'DRS' in telemetry.columns
            
            if has_drs:
                drs_active = telemetry[telemetry['DRS'] >= 10]
                drs_percentage = len(drs_active) / len(telemetry) * 100
                print(f"\n{track} {year}: ✅ 有 DRS ({drs_percentage:.1f}% 開啟)")
            else:
                print(f"\n{track} {year}: ❌ 無 DRS 數據")
    except Exception as e:
        print(f"\n{track} {year}: ⚠️ 錯誤 - {e}")
