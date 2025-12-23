"""
檢查墨西哥站前 3 圈數據
"""

import fastf1

fastf1.Cache.enable_cache('f1_analysis_cache')
session = fastf1.get_session(2024, 'Mexico', 'R')
session.load()

laps = session.laps.pick_driver('VER')
first_10 = laps[laps['LapNumber'].isin(range(1, 11))]

print("墨西哥站 VER 前 10 圈數據:")
print("=" * 80)
print(first_10[['LapNumber', 'LapTime', 'Compound']].to_string())

print(f"\n前 3 圈統計:")
first_3 = laps[laps['LapNumber'].isin([1, 2, 3])]
times = first_3['LapTime'].dt.total_seconds()
print(f"  圈速: {times.tolist()}")
print(f"  中位數: {times.median():.3f}s")
print(f"  平均: {times.mean():.3f}s")

print(f"\n全部圈速統計:")
all_laps = laps[laps['LapTime'].dt.total_seconds() < 200]
all_times = all_laps['LapTime'].dt.total_seconds()
print(f"  有效圈數: {len(all_times)}")
print(f"  平均: {all_times.mean():.3f}s")
print(f"  最快: {all_times.min():.3f}s")
print(f"  最慢: {all_times.max():.3f}s")
