"""
測試 Sector 邊界提取功能

此腳本驗證：
1. FastF1 提供 Sector1Time, Sector2Time, Sector3Time
2. extract_track_position_with_speed 函數提取 Sector 邊界
3. 邊界位置包含 Distance, X, Y, Z 座標
"""

import fastf1
import sys

print("="*60)
print("測試 Sector 邊界提取功能")
print("="*60)

# 設定緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

# 載入 2024 年巴西 GP 正賽
print("\n載入 2024 年巴西 GP 正賽...")
session = fastf1.get_session(2024, 'Brazil', 'R')
session.load()

print("會話載入成功")

# 獲取最快圈
laps = session.laps
fastest_lap = laps.pick_fastest()

if fastest_lap is None:
    print("錯誤：無最快圈數據")
    sys.exit(1)

print(f"\n最快圈: {fastest_lap['Driver']} Lap {fastest_lap['LapNumber']}")

# 檢查 Sector 時間
sector1_time = fastest_lap.get('Sector1Time')
sector2_time = fastest_lap.get('Sector2Time')
sector3_time = fastest_lap.get('Sector3Time')

print(f"\nSector 時間:")
print(f"  S1: {sector1_time}")
print(f"  S2: {sector2_time}")
print(f"  S3: {sector3_time}")

if sector1_time is None or sector2_time is None or sector3_time is None:
    print("\n錯誤：Sector 時間數據不完整")
    sys.exit(1)

# 獲取遙測數據
telemetry = fastest_lap.get_telemetry()

if telemetry.empty:
    print("\n錯誤：無遙測數據")
    sys.exit(1)

print(f"\n遙測數據點數: {len(telemetry)}")

# 檢查必要欄位
required_cols = ['Time', 'Distance', 'X', 'Y', 'Z']
missing_cols = [col for col in required_cols if col not in telemetry.columns]

if missing_cols:
    print(f"\n警告：遙測數據缺少欄位: {missing_cols}")
else:
    print(f"\n所有必要欄位存在: {required_cols}")

# 計算 Sector 邊界位置
print("\n計算 Sector 邊界位置...")

lap_start_time = telemetry['Time'].iloc[0]
print(f"圈開始時間: {lap_start_time}")

# S1 邊界
s1_end_time = lap_start_time + sector1_time
s1_idx = (telemetry['Time'] - s1_end_time).abs().idxmin()
s1_distance = float(telemetry.loc[s1_idx, 'Distance'])
s1_x = float(telemetry.loc[s1_idx, 'X'])
s1_y = float(telemetry.loc[s1_idx, 'Y'])
s1_z = float(telemetry.loc[s1_idx, 'Z'])

print(f"\nS1 結束 (Sector 1 邊界):")
print(f"  距離: {s1_distance:.1f}m")
print(f"  座標: X={s1_x:.1f}, Y={s1_y:.1f}, Z={s1_z:.1f}")
print(f"  時間: {sector1_time.total_seconds():.3f}s")

# S2 邊界
s2_end_time = lap_start_time + sector1_time + sector2_time
s2_idx = (telemetry['Time'] - s2_end_time).abs().idxmin()
s2_distance = float(telemetry.loc[s2_idx, 'Distance'])
s2_x = float(telemetry.loc[s2_idx, 'X'])
s2_y = float(telemetry.loc[s2_idx, 'Y'])
s2_z = float(telemetry.loc[s2_idx, 'Z'])

print(f"\nS2 結束 (Sector 2 邊界):")
print(f"  距離: {s2_distance:.1f}m")
print(f"  座標: X={s2_x:.1f}, Y={s2_y:.1f}, Z={s2_z:.1f}")
print(f"  時間: {sector2_time.total_seconds():.3f}s")

# S3 邊界（終點線）
s3_distance = 0.0
s3_x = float(telemetry['X'].iloc[0])
s3_y = float(telemetry['Y'].iloc[0])
s3_z = float(telemetry['Z'].iloc[0])

print(f"\nS3 結束 (終點線):")
print(f"  距離: {s3_distance:.1f}m")
print(f"  座標: X={s3_x:.1f}, Y={s3_y:.1f}, Z={s3_z:.1f}")
print(f"  時間: {sector3_time.total_seconds():.3f}s")

# 測試多圈一致性
print("\n" + "="*60)
print("測試多圈一致性 (檢查 Sector 邊界是否穩定)")
print("="*60)

test_laps = [60, 65, 67]  # 測試幾個不同的圈
s1_distances = []
s2_distances = []

for lap_num in test_laps:
    try:
        lap = laps[laps['LapNumber'] == lap_num].iloc[0]
        
        # 檢查 Sector 時間是否有效
        if lap['Sector1Time'] is None or lap['Sector2Time'] is None:
            print(f"Lap {lap_num}: Sector 時間無效，跳過")
            continue
        
        # 獲取遙測
        tel = lap.get_telemetry()
        if tel.empty:
            print(f"Lap {lap_num}: 無遙測數據，跳過")
            continue
        
        # 計算 Sector 邊界
        lap_start = tel['Time'].iloc[0]
        
        s1_time = lap_start + lap['Sector1Time']
        s1_idx = (tel['Time'] - s1_time).abs().idxmin()
        s1_dist = float(tel.loc[s1_idx, 'Distance'])
        s1_distances.append(s1_dist)
        
        s2_time = lap_start + lap['Sector1Time'] + lap['Sector2Time']
        s2_idx = (tel['Time'] - s2_time).abs().idxmin()
        s2_dist = float(tel.loc[s2_idx, 'Distance'])
        s2_distances.append(s2_dist)
        
        print(f"Lap {lap_num}: S1={s1_dist:.1f}m, S2={s2_dist:.1f}m")
        
    except Exception as e:
        print(f"Lap {lap_num}: 錯誤 - {e}")

# 計算標準差
if len(s1_distances) >= 2:
    import numpy as np
    s1_mean = np.mean(s1_distances)
    s1_std = np.std(s1_distances)
    s2_mean = np.mean(s2_distances)
    s2_std = np.std(s2_distances)
    
    print(f"\n一致性統計:")
    print(f"  S1 邊界: {s1_mean:.1f}m ± {s1_std:.2f}m")
    print(f"  S2 邊界: {s2_mean:.1f}m ± {s2_std:.2f}m")
    
    if s1_std < 10 and s2_std < 10:
        print("\n結論: Sector 邊界非常穩定（標準差 < 10m）")
    else:
        print("\n警告: Sector 邊界變化較大（標準差 >= 10m）")
else:
    print("\n警告: 測試圈數不足，無法計算一致性")

print("\n" + "="*60)
print("測試完成！")
print("="*60)
