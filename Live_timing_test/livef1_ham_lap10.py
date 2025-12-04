"""
LiveF1 - HAM Lap 10 完整數據分析
展示 LiveF1 如何輕鬆提取圈數資料
"""
import livef1
import pandas as pd

print("="*70)
print("LiveF1 - HAM Lap 10 Speed Data Analysis")
print("2025 Japan Grand Prix")
print("="*70)

# 1. 載入賽段
print("\n[Step 1] Loading session...")
session = livef1.get_session(
    season=2025,
    meeting_identifier="Japan",
    session_identifier="Race"
)
print(f"  Session: {session.name}")
print(f"  Event: {session.meeting.name}")

# 2. 處理資料 (Silver layer)
print("\n[Step 2] Processing data (may take a minute)...")
session.generate(silver=True)
print("  Data processing complete!")

# 3. 取得所有圈數資料
print("\n[Step 3] Getting laps data...")
laps = session.get_laps()
print(f"  Total laps loaded: {len(laps)}")

# 4. 過濾 HAM 的圈數
print("\n[Step 4] Filtering HAM (Driver 44)...")
ham_laps = laps[laps['DriverNo'] == 44].copy()
print(f"  HAM total laps: {len(ham_laps)}")

if len(ham_laps) < 10:
    print(f"[ERROR] HAM only has {len(ham_laps)} laps")
    exit(1)

# 5. 取得 Lap 10
print("\n[Step 5] Extracting Lap 10...")
lap10 = ham_laps[ham_laps['lap_number'] == 10].iloc[0]

print(f"\n  Lap 10 Information:")
print(f"  ==================")
print(f"  Lap Time:       {lap10['lap_time']}")
print(f"  Lap Start Time: {lap10['lap_start_time']}")
print(f"  Lap Start Date: {lap10['lap_start_date']}")

# 6. 取得遙測資料
print("\n[Step 6] Getting telemetry data...")
telemetry_all = session.get_car_telemetry()
print(f"  Total telemetry records: {len(telemetry_all)}")

# 過濾 HAM + Lap 10
lap10_telemetry = telemetry_all[
    (telemetry_all['DriverNo'] == 44) &
    (telemetry_all['lap_number'] == 10)
].copy()

print(f"  Lap 10 telemetry records: {len(lap10_telemetry)}")

# 7. 分析速度資料
print("\n" + "="*70)
print("Lap 10 Speed Data Analysis")
print("="*70)

speed_data = lap10_telemetry['speed'].dropna()

if len(speed_data) > 0:
    print(f"\n總資料點數: {len(speed_data)}")
    print(f"速度範圍: {speed_data.min():.0f} - {speed_data.max():.0f} km/h")
    print(f"平均速度: {speed_data.mean():.0f} km/h")
    print(f"中位數速度: {speed_data.median():.0f} km/h")
    
    # 速度分布
    print(f"\n速度分布:")
    bins = [0, 100, 150, 200, 250, 300, 350]
    for i in range(len(bins)-1):
        count = ((speed_data >= bins[i]) & (speed_data < bins[i+1])).sum()
        pct = count / len(speed_data) * 100
        bar = '#' * int(pct / 2)
        print(f"  {bins[i]:3d}-{bins[i+1]:3d} km/h: {bar:20} {count:4d} ({pct:5.1f}%)")
    
    # 前10筆資料
    print(f"\n前 10 筆速度讀數:")
    for i in range(min(10, len(lap10_telemetry))):
        row = lap10_telemetry.iloc[i]
        print(f"  {i+1:2d}. Time: {row.get('Time', 'N/A'):12} | "
              f"Speed: {row['speed']:3.0f} km/h | "
              f"RPM: {row.get('rpm', 0):5.0f} | "
              f"Gear: {row.get('n_gear', 0):.0f}")
    
    print(f"\n... ({len(lap10_telemetry) - 20} more records) ...")
    
    # 後10筆資料
    print(f"\n最後 10 筆速度讀數:")
    for i in range(max(0, len(lap10_telemetry)-10), len(lap10_telemetry)):
        row = lap10_telemetry.iloc[i]
        print(f"  {i+1:2d}. Time: {row.get('Time', 'N/A'):12} | "
              f"Speed: {row['speed']:3.0f} km/h | "
              f"RPM: {row.get('rpm', 0):5.0f} | "
              f"Gear: {row.get('n_gear', 0):.0f}")
    
    # 8. 與 fastf1 比較
    print(f"\n" + "="*70)
    print("Comparison with fastf1")
    print("="*70)
    print(f"\nLiveF1 results:")
    print(f"  Data points: {len(speed_data)}")
    print(f"  Speed range: {speed_data.min():.0f} - {speed_data.max():.0f} km/h")
    
    print(f"\nfastf1 results (from previous test):")
    print(f"  Data points: 714")
    print(f"  Speed range: 69 - 309 km/h")
    
    diff = abs(len(speed_data) - 714)
    print(f"\nDifference: {diff} data points ({diff/714*100:.1f}%)")
    
    if diff < 50:
        print("  Status: Very close! Both tools extract similar data.")
    else:
        print("  Status: Some difference, possibly due to different filtering.")
    
else:
    print("[ERROR] No speed data found!")

print(f"\n" + "="*70)
print("Analysis Complete!")
print("="*70)

# 9. 儲存結果 (選用)
print(f"\n[Optional] Saving results to CSV...")
output_file = "ham_lap10_livef1.csv"
lap10_telemetry.to_csv(output_file, index=False)
print(f"  Saved to: {output_file}")
print(f"  Columns: {list(lap10_telemetry.columns)}")
