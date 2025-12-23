#!/usr/bin/env python3
"""調試 VER 在 Live Timing cache 中的數據狀況"""
import sys
sys.path.insert(0, '.')
import pickle
from pathlib import Path
from collections import defaultdict

# 載入正確的 Live Timing cache
cache_path = Path("data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl")
if not cache_path.exists():
    print(f"Cache not found: {cache_path}")
    sys.exit(1)

with cache_path.open("rb") as f:
    cache_data = pickle.load(f)

print(f"Cache keys: {list(cache_data.keys())}")

snapshots = cache_data.get("snapshots", [])
print(f"Total snapshots: {len(snapshots)}")

if not snapshots:
    print("No snapshots!")
    sys.exit(1)

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

print(f"\nVER total snapshots: {ver_total}")
print(f"VER snapshots with X: {ver_x_count}")
print(f"VER unique laps in snapshots: {len(ver_laps)}")
print(f"VER lap range: {min(ver_laps.keys()) if ver_laps else 'N/A'} - {max(ver_laps.keys()) if ver_laps else 'N/A'}")

# 檢查 lap_lookup 的時間範圍和 snapshots 的時間範圍是否匹配
from CLI_modules.cli.analyzer.live_timing_traffic_distance_analysis import _build_lap_lookup_from_fastf1_cache
lap_lookup = _build_lap_lookup_from_fastf1_cache(2025, 'Abu Dhabi', 'R')

print("\n=== Compare snapshot lap vs lap_lookup ===")
if '1' in lap_lookup:
    lookup_laps = set(r[2] for r in lap_lookup['1'])
    snapshot_laps = set(ver_laps.keys())
    
    print(f"Lap lookup laps: {min(lookup_laps)} - {max(lookup_laps)} ({len(lookup_laps)} laps)")
    print(f"Snapshot laps: {min(snapshot_laps) if snapshot_laps else 'N/A'} - {max(snapshot_laps) if snapshot_laps else 'N/A'} ({len(snapshot_laps)} laps)")
    
    # 哪些圈在 snapshot 中但不在 lap_lookup 中？
    in_snap_not_lookup = snapshot_laps - lookup_laps
    if in_snap_not_lookup:
        print(f"In snapshot but not in lookup: {sorted(in_snap_not_lookup)}")
    
    # 哪些圈在 lap_lookup 中但不在 snapshot 中？
    in_lookup_not_snap = lookup_laps - snapshot_laps
    if in_lookup_not_snap:
        print(f"In lookup but not in snapshot: {sorted(in_lookup_not_snap)}")

# 抽樣檢查
print("\n=== Sample snapshots ===")
for i in [0, 100, 500, 1000, 2000, 3000, 4000, 5000, len(snapshots)-1]:
    if i < len(snapshots):
        snap = snapshots[i]
        t = snap.get("race_time_seconds", 0)
        ver = snap.get("drivers", {}).get("1", {})
        lap = ver.get("lap")
        x = ver.get("x")
        print(f"  [{i}] t={t:.1f}s: lap={lap}, x={x}")
