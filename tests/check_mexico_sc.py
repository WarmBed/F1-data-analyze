"""
檢查墨西哥站是否有 Safety Car
"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')
session = fastf1.get_session(2024, 'Mexico', 'R')
session.load()

# 檢查 TrackStatus
print("=" * 80)
print("墨西哥站 2024 - TrackStatus 檢查")
print("=" * 80)

# 檢查賽道狀態
track_status = session.track_status
if track_status is not None and len(track_status) > 0:
    print("\nTrackStatus 記錄:")
    print(track_status[['Time', 'Status', 'Message']].head(20).to_string())
else:
    print("\n⚠️ 沒有 TrackStatus 數據")

# 檢查 Race Control Messages
print("\n" + "=" * 80)
print("Race Control Messages (前 30 筆)")
print("=" * 80)

race_control = session.race_control_messages
if race_control is not None and len(race_control) > 0:
    # 過濾 Safety Car 相關訊息
    sc_messages = race_control[race_control['Message'].str.contains('SAFETY CAR|SC|VSC|VIRTUAL', case=False, na=False)]
    
    if len(sc_messages) > 0:
        print("\n🚨 發現 Safety Car 相關訊息:")
        print(sc_messages[['Time', 'Category', 'Message']].to_string())
    else:
        print("\n✅ 沒有 Safety Car 訊息")
    
    print("\n前 30 筆 Race Control Messages:")
    print(race_control[['Time', 'Category', 'Message']].head(30).to_string())
else:
    print("\n⚠️ 沒有 Race Control Messages")

# 檢查 VER 的圈速變化
print("\n" + "=" * 80)
print("VER 圈速分析（前 20 圈）")
print("=" * 80)

laps = session.laps.pick_driver('VER')
first_20 = laps[laps['LapNumber'] <= 20].copy()
first_20['LapTimeSeconds'] = first_20['LapTime'].dt.total_seconds()

print(first_20[['LapNumber', 'LapTimeSeconds', 'Compound']].to_string())

# 找出異常慢圈（> 120s）
slow_laps = first_20[first_20['LapTimeSeconds'] > 120]
if len(slow_laps) > 0:
    print(f"\n🐌 異常慢圈（> 120s）:")
    for _, lap in slow_laps.iterrows():
        print(f"  Lap {int(lap['LapNumber'])}: {lap['LapTimeSeconds']:.3f}s")

# 建議的 base_time 範圍
normal_laps = first_20[(first_20['LapTimeSeconds'] < 120) & (first_20['LapNumber'] >= 4)]
if len(normal_laps) > 0:
    base_time = normal_laps['LapTimeSeconds'].median()
    print(f"\n✅ 建議的 base_time (Lap 4+ 且 < 120s):")
    print(f"   中位數: {base_time:.3f}s")
    print(f"   範圍: {normal_laps['LapTimeSeconds'].min():.3f}s - {normal_laps['LapTimeSeconds'].max():.3f}s")
    print(f"   樣本數: {len(normal_laps)} 圈")
