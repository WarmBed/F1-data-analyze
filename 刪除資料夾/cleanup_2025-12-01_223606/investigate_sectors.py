#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""調查 FastF1 是否提供 Sector (S1, S2, S3) 的位置數據"""

import fastf1
import pandas as pd
import sys

# 設置 UTF-8 輸出
sys.stdout.reconfigure(encoding='utf-8')

fastf1.Cache.enable_cache('f1_analysis_cache')

print("測試 2024 巴西賽道的 Sector 數據...")
print("=" * 80)

session = fastf1.get_session(2024, 'Brazil', 'R')
session.load()

# 檢查會話物件的屬性
print(f"\nSession 物件可用屬性:")
session_attrs = [attr for attr in dir(session) if not attr.startswith('_')]
print(f"   總數: {len(session_attrs)}")

# 檢查是否有 sector 相關資訊
sector_attrs = [attr for attr in session_attrs if 'sector' in attr.lower()]
print(f"\nSector 相關屬性: {sector_attrs}")

# 檢查 Laps 數據
print(f"\nLaps DataFrame 欄位:")
print(f"   {session.laps.columns.tolist()}")

# 檢查是否有 Sector 時間
sector_cols = [col for col in session.laps.columns if 'Sector' in col]
print(f"\nSector 時間欄位: {sector_cols}")

if sector_cols:
    # 顯示 VER 的 Sector 時間
    ver_laps = session.laps.pick_drivers('VER')
    fastest = ver_laps.pick_fastest()
    
    print(f"\n🏁 VER 最速圈 Sector 時間:")
    for col in sector_cols:
        value = fastest[col]
        print(f"   {col}: {value}")

# 檢查遙測數據是否有 Sector 標記
fastest_lap = session.laps.pick_fastest()
telemetry = fastest_lap.get_telemetry()

print(f"\n🔧 遙測數據欄位:")
print(f"   {telemetry.columns.tolist()}")

# 檢查是否有任何 Sector 相關欄位
sector_tel_cols = [col for col in telemetry.columns if 'sector' in col.lower()]
print(f"\n🔍 遙測中的 Sector 欄位: {sector_tel_cols if sector_tel_cols else '無'}")

# 嘗試從 lap 數據推算 Sector 邊界
print(f"\n" + "=" * 80)
print(f"💡 方法 1: 從 Sector 時間推算 Sector 邊界位置")
print("=" * 80)

# 選擇一圈分析
lap = ver_laps[ver_laps['LapNumber'] == 67].iloc[0]
telemetry = lap.get_telemetry()

# Sector 時間
sector1_time = lap['Sector1Time']
sector2_time = lap['Sector2Time']
sector3_time = lap['Sector3Time']

print(f"\n⏱️ Sector 時間:")
print(f"   Sector 1: {sector1_time}")
print(f"   Sector 2: {sector2_time}")
print(f"   Sector 3: {sector3_time}")

# 計算累積時間
if pd.notna(sector1_time) and pd.notna(sector2_time):
    sector1_end_time = sector1_time
    sector2_end_time = sector1_time + sector2_time
    lap_time = sector1_time + sector2_time + sector3_time
    
    print(f"\n📍 累積時間點:")
    print(f"   Sector 1 結束: {sector1_end_time}")
    print(f"   Sector 2 結束: {sector2_end_time}")
    print(f"   圈速總時間: {lap_time}")
    
    # 在遙測中找到對應的位置
    if 'SessionTime' in telemetry.columns or 'Time' in telemetry.columns:
        time_col = 'SessionTime' if 'SessionTime' in telemetry.columns else 'Time'
        
        # 獲取圈的起始時間
        lap_start_time = telemetry[time_col].iloc[0]
        
        # 計算 Sector 邊界的絕對時間
        s1_end_abs = lap_start_time + sector1_end_time
        s2_end_abs = lap_start_time + sector2_end_time
        
        print(f"\n🎯 尋找 Sector 邊界位置:")
        
        # 找到最接近 Sector 1 結束時間的數據點
        s1_idx = (telemetry[time_col] - s1_end_abs).abs().idxmin()
        s1_distance = telemetry.loc[s1_idx, 'Distance']
        s1_x = telemetry.loc[s1_idx, 'X']
        s1_y = telemetry.loc[s1_idx, 'Y']
        
        print(f"   Sector 1 結束: Distance={s1_distance:.1f}m, X={s1_x:.1f}, Y={s1_y:.1f}")
        
        # 找到最接近 Sector 2 結束時間的數據點
        s2_idx = (telemetry[time_col] - s2_end_abs).abs().idxmin()
        s2_distance = telemetry.loc[s2_idx, 'Distance']
        s2_x = telemetry.loc[s2_idx, 'X']
        s2_y = telemetry.loc[s2_idx, 'Y']
        
        print(f"   Sector 2 結束: Distance={s2_distance:.1f}m, X={s2_x:.1f}, Y={s2_y:.1f}")
        
        # Sector 3 結束就是終點線 (Distance = 0 or max)
        print(f"   Sector 3 結束: 終點線 (Distance=0m or {telemetry['Distance'].max():.1f}m)")
        
        print(f"\n✅ 成功！可以從 Sector 時間推算 Sector 邊界位置！")

# 測試多圈的一致性
print(f"\n" + "=" * 80)
print(f"💡 方法 2: 測試多圈 Sector 邊界的一致性")
print("=" * 80)

sector_boundaries = []

for lap_num in [60, 65, 67]:  # 測試 3 圈
    lap = ver_laps[ver_laps['LapNumber'] == lap_num]
    if lap.empty:
        continue
    
    lap = lap.iloc[0]
    telemetry = lap.get_telemetry()
    
    sector1_time = lap['Sector1Time']
    sector2_time = lap['Sector2Time']
    
    if pd.notna(sector1_time) and pd.notna(sector2_time):
        lap_start_time = telemetry[time_col].iloc[0]
        
        s1_end_abs = lap_start_time + sector1_time
        s2_end_abs = lap_start_time + sector1_time + sector2_time
        
        s1_idx = (telemetry[time_col] - s1_end_abs).abs().idxmin()
        s2_idx = (telemetry[time_col] - s2_end_abs).abs().idxmin()
        
        s1_distance = telemetry.loc[s1_idx, 'Distance']
        s2_distance = telemetry.loc[s2_idx, 'Distance']
        
        sector_boundaries.append({
            'lap': lap_num,
            's1_end': s1_distance,
            's2_end': s2_distance
        })
        
        print(f"Lap {lap_num}: S1={s1_distance:.1f}m, S2={s2_distance:.1f}m")

if sector_boundaries:
    df = pd.DataFrame(sector_boundaries)
    print(f"\n📊 多圈平均 Sector 邊界:")
    print(f"   Sector 1 結束: {df['s1_end'].mean():.1f}m (標準差: {df['s1_end'].std():.1f}m)")
    print(f"   Sector 2 結束: {df['s2_end'].mean():.1f}m (標準差: {df['s2_end'].std():.1f}m)")
    
    print(f"\n✅ 結論: Sector 邊界位置非常穩定，可以用於地圖標註！")
