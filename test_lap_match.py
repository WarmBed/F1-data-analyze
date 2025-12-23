#!/usr/bin/env python3
"""測試 lap_lookup 是否正確匹配 Live Timing 的時間"""
import sys
sys.path.insert(0, '.')
import pickle
from pathlib import Path

from CLI_modules.cli.analyzer.live_timing_traffic_distance_analysis import (
    _build_lap_lookup_from_fastf1_cache,
    _get_lap_from_lookup,
)

# Build lap_lookup
print("Building lap_lookup...")
lap_lookup = _build_lap_lookup_from_fastf1_cache(2025, 'Abu Dhabi', 'R')

# Load Live Timing snapshots
lt_path = Path('data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl')
with lt_path.open('rb') as f:
    lt_data = pickle.load(f)

snapshots = lt_data['snapshots']
print(f"Total snapshots: {len(snapshots)}")

# 測試 VER 在各個時間點的圈數
test_times = [3592.8, 3650.0, 3681.8, 3750.0, 3771.4, 4000.0, 5000.0, 8000.0, 9000.0]

print("\n=== Testing _get_lap_from_lookup for VER ===")
for t in test_times:
    lap = _get_lap_from_lookup(lap_lookup, '1', t)
    print(f"  t={t:.1f}s: lap_lookup says Lap {lap}")

# 比較幾個實際 snapshot 的結果
print("\n=== Comparing with actual snapshots ===")
sample_indices = [0, 100, 500, 1000, 2000, 5000, 10000, 15000, 20000]
for i in sample_indices:
    if i >= len(snapshots):
        break
    snap = snapshots[i]
    t = snap.get('race_time_seconds', 0)
    ver = snap.get('drivers', {}).get('1', {})
    snap_lap = ver.get('lap')
    lookup_lap = _get_lap_from_lookup(lap_lookup, '1', t)
    match = "OK" if snap_lap == lookup_lap else "MISMATCH!"
    print(f"  [{i}] t={t:.1f}s: snapshot_lap={snap_lap}, lookup_lap={lookup_lap} {match}")

# 統計有多少 snapshot 的 lap 能被 lap_lookup 正確匹配
print("\n=== Statistics ===")
total = 0
matched = 0
not_in_lookup = 0
for snap in snapshots:
    t = snap.get('race_time_seconds', 0)
    ver = snap.get('drivers', {}).get('1', {})
    snap_lap = ver.get('lap')
    if snap_lap is None:
        continue
    total += 1
    lookup_lap = _get_lap_from_lookup(lap_lookup, '1', t)
    if lookup_lap is None:
        not_in_lookup += 1
    elif snap_lap == lookup_lap:
        matched += 1

print(f"Total snapshots with VER lap: {total}")
print(f"Matched: {matched} ({100*matched/total:.1f}%)")
print(f"Not in lookup: {not_in_lookup} ({100*not_in_lookup/total:.1f}%)")
print(f"Mismatched: {total - matched - not_in_lookup} ({100*(total-matched-not_in_lookup)/total:.1f}%)")
