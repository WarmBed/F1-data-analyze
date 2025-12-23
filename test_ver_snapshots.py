#!/usr/bin/env python3
"""調試 VER 在 snapshots 中的數據狀況"""
import sys
sys.path.insert(0, '.')
import pickle
from pathlib import Path
from collections import defaultdict

# 載入 Live Timing cache
cache_path = Path("cache/track_position_2025_Abu Dhabi Grand Prix_R.pkl")
if not cache_path.exists():
    print(f"Cache not found: {cache_path}")
    sys.exit(1)

with cache_path.open("rb") as f:
    cache_data = pickle.load(f)

snapshots = cache_data.get("snapshots", [])
print(f"Total snapshots: {len(snapshots)}")

# 檢查 VER (driver_num = '1') 在各個 snapshot 中的數據
ver_laps = defaultdict(int)  # lap -> count
ver_x_count = 0
ver_total = 0

for snap in snapshots:
    drivers = snap.get("drivers", {}) or {}
    ver_data = drivers.get("1")
    if ver_data:
        ver_total += 1
        lap = ver_data.get("lap")
        x = ver_data.get("x")
        if lap is not None:
            ver_laps[lap] += 1
        if x is not None:
            ver_x_count += 1

print(f"VER total snapshots: {ver_total}")
print(f"VER snapshots with X: {ver_x_count}")
print(f"VER laps distribution:")
for lap in sorted(ver_laps.keys()):
    print(f"  Lap {lap}: {ver_laps[lap]} snapshots")

# 檢查 lap_lookup 的時間範圍和 snapshots 的時間範圍是否匹配
from CLI_modules.cli.analyzer.live_timing_traffic_distance_analysis import _build_lap_lookup_from_fastf1_cache
lap_lookup = _build_lap_lookup_from_fastf1_cache(2025, 'Abu Dhabi', 'R')

print("\nVER lap_lookup time ranges:")
if '1' in lap_lookup:
    for lap_start, lap_end, lap_num in lap_lookup['1'][:3]:
        print(f"  Lap {lap_num}: {lap_start:.1f}s - {lap_end:.1f}s")
    print("  ...")
    for lap_start, lap_end, lap_num in lap_lookup['1'][-3:]:
        print(f"  Lap {lap_num}: {lap_start:.1f}s - {lap_end:.1f}s")

# 檢查 snapshots 的時間範圍
snapshot_times = []
for snap in snapshots:
    t = snap.get("race_time_seconds")
    if t is not None:
        snapshot_times.append(t)

if snapshot_times:
    print(f"\nSnapshot time range: {min(snapshot_times):.1f}s - {max(snapshot_times):.1f}s")

# 抽樣檢查 VER 在較晚時間的快照是否有 X/Y 數據
late_snapshots = [s for s in snapshots if (s.get("race_time_seconds") or 0) > 5000]
print(f"\nLate snapshots (>5000s): {len(late_snapshots)}")
ver_late_with_x = 0
for snap in late_snapshots[:10]:
    ver_data = snap.get("drivers", {}).get("1")
    if ver_data:
        t = snap.get("race_time_seconds")
        x = ver_data.get("x")
        lap = ver_data.get("lap")
        print(f"  t={t:.1f}s: lap={lap}, x={x}")
        if x is not None:
            ver_late_with_x += 1
