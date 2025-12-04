"""
使用 LiveF1 提取 HAM Lap 10 速度資料
展示正確的整合方式
"""
import livef1

print("="*70)
print("Using LiveF1 to extract HAM Lap 10 Speed Data")
print("="*70)

# 使用 LiveF1
print("\n[1] Loading session with LiveF1...")
session = livef1.get_session(
    season=2025,
    meeting_identifier="Japan",
    session_identifier="Race"
)

print("\n[2] Processing data (generating Silver layer)...")
session.generate(silver=True)

print("\n[3] Getting laps data...")
laps = session.get_laps()

# 過濾 HAM 的資料
print("\n[4] Filtering HAM's laps...")
ham_laps = laps[laps['DriverNo'] == 44]
print(f"  Total HAM laps: {len(ham_laps)}")

# 取得 Lap 10
if len(ham_laps) >= 10:
    lap10 = ham_laps[ham_laps['lap_number'] == 10].iloc[0]
    
    print(f"\n[5] Lap 10 Info:")
    print(f"  Lap Time: {lap10['lap_time']}")
    print(f"  Lap Start: {lap10['lap_start_time']}")
    
    # 取得遙測
    print(f"\n[6] Getting telemetry...")
    telemetry = session.get_car_telemetry()
    
    # 過濾 HAM + Lap 10
    lap10_telemetry = telemetry[
        (telemetry['DriverNo'] == 44) &
        (telemetry['lap_number'] == 10)
    ]
    
    speed_data = lap10_telemetry['speed'].dropna()
    
    print(f"\n{'='*70}")
    print("Results:")
    print("="*70)
    print(f"  Total speed readings: {len(speed_data)}")
    print(f"  Speed range: {speed_data.min():.0f} - {speed_data.max():.0f} km/h")
    print(f"  Average speed: {speed_data.mean():.0f} km/h")
    
    print(f"\n  First 5 readings:")
    for i, speed in enumerate(speed_data.head()):
        print(f"    {i+1}. {speed:.0f} km/h")
    
    print(f"\n{'='*70}")
    print("Comparison:")
    print("="*70)
    print(f"  LiveF1:   {len(speed_data)} points")
    print(f"  fastf1:   714 points (from previous test)")
    print(f"  Custom:   0 points (time alignment issue)")
    
    print(f"\n{'='*70}")
    print("Conclusion:")
    print("="*70)
    print("""
Using libraries (LiveF1/fastf1) vs Manual integration:

LiveF1/fastf1:
  + Automatic data source integration
  + Correct time alignment built-in
  + Ready to use
  + Maintained by community

Manual integration:
  + Full control
  + Learning experience
  - Complex time alignment logic required
  - Need to handle edge cases
  - Requires deep understanding of all data sources
    """)
else:
    print(f"[ERROR] HAM has only {len(ham_laps)} laps")
