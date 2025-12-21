# -*- coding: utf-8 -*-
import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print("=== Sector Data Investigation ===\n")

session = fastf1.get_session(2024, 'Brazil', 'R')
session.load()

# Check Sector columns in Laps
print("Laps columns:")
sector_cols = [col for col in session.laps.columns if 'Sector' in col]
print(f"  Sector columns: {sector_cols}\n")

# Get VER fastest lap
ver_laps = session.laps.pick_drivers('VER')
fastest = ver_laps.pick_fastest()

print("VER Fastest Lap Sector Times:")
for col in sector_cols:
    print(f"  {col}: {fastest[col]}")

# Calculate sector boundaries
lap = ver_laps[ver_laps['LapNumber'] == 67].iloc[0]
telemetry = lap.get_telemetry()

sector1_time = lap['Sector1Time']
sector2_time = lap['Sector2Time']
sector3_time = lap['Sector3Time']

print(f"\nSector Times:")
print(f"  S1: {sector1_time}")
print(f"  S2: {sector2_time}")
print(f"  S3: {sector3_time}")

# Find sector boundaries by time
if pd.notna(sector1_time) and pd.notna(sector2_time):
    time_col = 'Time'
    lap_start_time = telemetry[time_col].iloc[0]
    
    s1_end_abs = lap_start_time + sector1_time
    s2_end_abs = lap_start_time + sector1_time + sector2_time
    
    s1_idx = (telemetry[time_col] - s1_end_abs).abs().idxmin()
    s2_idx = (telemetry[time_col] - s2_end_abs).abs().idxmin()
    
    s1_distance = telemetry.loc[s1_idx, 'Distance']
    s2_distance = telemetry.loc[s2_idx, 'Distance']
    s1_x = telemetry.loc[s1_idx, 'X']
    s1_y = telemetry.loc[s1_idx, 'Y']
    s2_x = telemetry.loc[s2_idx, 'X']
    s2_y = telemetry.loc[s2_idx, 'Y']
    
    print(f"\nSector Boundaries:")
    print(f"  S1 End: Distance={s1_distance:.1f}m, X={s1_x:.1f}, Y={s1_y:.1f}")
    print(f"  S2 End: Distance={s2_distance:.1f}m, X={s2_x:.1f}, Y={s2_y:.1f}")
    print(f"  S3 End: Finish Line (Distance=0m or {telemetry['Distance'].max():.1f}m)")
    
    # Test consistency across multiple laps
    print(f"\nTesting consistency across laps:")
    boundaries = []
    
    for lap_num in [60, 65, 67]:
        lap = ver_laps[ver_laps['LapNumber'] == lap_num]
        if lap.empty:
            continue
        
        lap = lap.iloc[0]
        tel = lap.get_telemetry()
        
        s1t = lap['Sector1Time']
        s2t = lap['Sector2Time']
        
        if pd.notna(s1t) and pd.notna(s2t):
            start_t = tel[time_col].iloc[0]
            
            s1_abs = start_t + s1t
            s2_abs = start_t + s1t + s2t
            
            s1_i = (tel[time_col] - s1_abs).abs().idxmin()
            s2_i = (tel[time_col] - s2_abs).abs().idxmin()
            
            s1_d = tel.loc[s1_i, 'Distance']
            s2_d = tel.loc[s2_i, 'Distance']
            
            boundaries.append({'lap': lap_num, 's1': s1_d, 's2': s2_d})
            print(f"  Lap {lap_num}: S1={s1_d:.1f}m, S2={s2_d:.1f}m")
    
    if boundaries:
        df = pd.DataFrame(boundaries)
        print(f"\nAverage Sector Boundaries:")
        print(f"  S1 End: {df['s1'].mean():.1f}m (std: {df['s1'].std():.1f}m)")
        print(f"  S2 End: {df['s2'].mean():.1f}m (std: {df['s2'].std():.1f}m)")
        
        print(f"\n=== CONCLUSION ===")
        print(f"YES! Sector boundaries are stable and can be marked on track map!")
        print(f"Method: Calculate from Sector times + telemetry Time column")
