#!/usr/bin/env python3
"""測試 lap_lookup 數據"""
import sys
sys.path.insert(0, '.')

from CLI_modules.cli.analyzer.live_timing_traffic_distance_analysis import _build_lap_lookup_from_fastf1_cache

print("Building lap lookup...")
lap_lookup = _build_lap_lookup_from_fastf1_cache(2025, 'Abu Dhabi', 'R')

print(f"Total drivers: {len(lap_lookup)}")
print(f"Available driver numbers: {list(lap_lookup.keys())[:10]}")

# VER 是 1 號車
if '1' in lap_lookup:
    ranges = lap_lookup['1']
    print(f"VER (1) lap ranges: {len(ranges)} laps")
    print(f"First 5 ranges: {ranges[:5]}")
    print(f"Last 5 ranges: {ranges[-5:]}")
else:
    print("VER (1) not found in lap_lookup!")
    # 嘗試其他可能的 key
    for key in lap_lookup.keys():
        print(f"  Driver {key}: {len(lap_lookup[key])} ranges")
