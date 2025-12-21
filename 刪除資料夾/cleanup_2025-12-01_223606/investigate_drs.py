#!/usr/bin/env python3
"""調查 FastF1 DRS 欄位的含義"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print("載入 2025 巴西正賽數據...")
session = fastf1.get_session(2025, 'Brazil', 'R')
session.load(laps=True, telemetry=True)

# 檢查 VER Lap 17 (346 km/h)
ver_laps = session.laps.pick_drivers('VER')
lap17 = ver_laps[ver_laps['LapNumber'] == 17].iloc[0]
telemetry = lap17.get_telemetry()

print(f"\n📊 VER Lap 17 遙測數據分析:")
print(f"   總數據點: {len(telemetry)}")
print(f"   欄位: {telemetry.columns.tolist()}")

# 分析 DRS 欄位的值
if 'DRS' in telemetry.columns:
    drs_values = telemetry['DRS'].unique()
    print(f"\n🔍 DRS 欄位的所有值: {sorted(drs_values)}")
    
    # 統計每個值的數量
    print(f"\n📈 DRS 值分佈:")
    for value in sorted(drs_values):
        count = len(telemetry[telemetry['DRS'] == value])
        percentage = count / len(telemetry) * 100
        print(f"   DRS={value}: {count} 點 ({percentage:.1f}%)")
    
    # 找出高速路段的 DRS 狀態
    print(f"\n⚡ 速度 > 300 km/h 的路段 DRS 狀態:")
    high_speed = telemetry[telemetry['Speed'] > 300]
    if not high_speed.empty:
        for value in sorted(high_speed['DRS'].unique()):
            count = len(high_speed[high_speed['DRS'] == value])
            percentage = count / len(high_speed) * 100
            print(f"   DRS={value}: {count} 點 ({percentage:.1f}%)")
    
    # 檢查最高速度點的 DRS
    max_speed_idx = telemetry['Speed'].idxmax()
    max_speed_row = telemetry.loc[max_speed_idx]
    print(f"\n🏁 最高速度點 (346 km/h):")
    print(f"   DRS: {max_speed_row['DRS']}")
    print(f"   距離: {max_speed_row['Distance']:.1f}m")
    print(f"   油門: {max_speed_row['Throttle']:.1f}%")
    
    # 分析 DRS 區域
    print(f"\n🗺️ DRS 區域分析:")
    drs_active = telemetry[telemetry['DRS'] >= 10]  # 假設 DRS >= 10 表示開啟
    if not drs_active.empty:
        print(f"   DRS 開啟數據點: {len(drs_active)}")
        print(f"   距離範圍: {drs_active['Distance'].min():.1f}m - {drs_active['Distance'].max():.1f}m")
        print(f"   速度範圍: {drs_active['Speed'].min():.1f} - {drs_active['Speed'].max():.1f} km/h")
        
        # 找出可能的 DRS 區域（連續的 DRS 開啟區域）
        drs_active_sorted = drs_active.sort_values('Distance')
        distance_gaps = drs_active_sorted['Distance'].diff()
        
        # 如果距離差 > 100m，視為不同的 DRS 區域
        drs_zones = []
        current_zone_start = None
        current_zone_end = None
        
        for idx, row in drs_active_sorted.iterrows():
            if current_zone_start is None:
                current_zone_start = row['Distance']
                current_zone_end = row['Distance']
            else:
                gap = row['Distance'] - current_zone_end
                if gap > 100:  # 新區域
                    drs_zones.append((current_zone_start, current_zone_end))
                    current_zone_start = row['Distance']
                    current_zone_end = row['Distance']
                else:
                    current_zone_end = row['Distance']
        
        if current_zone_start is not None:
            drs_zones.append((current_zone_start, current_zone_end))
        
        print(f"\n   可能的 DRS 區域數量: {len(drs_zones)}")
        for i, (start, end) in enumerate(drs_zones, 1):
            print(f"   區域 {i}: {start:.0f}m - {end:.0f}m (長度: {end-start:.0f}m)")

# 檢查 FastF1 文檔說明
print(f"\n📚 FastF1 文檔提示:")
print(f"   DRS 欄位通常的值:")
print(f"   - 0: DRS 關閉")
print(f"   - 1-9: DRS 可用但未開啟")
print(f"   - 10-14: DRS 開啟狀態（不同程度）")
print(f"   - 具體數值可能因年份和數據來源而異")
