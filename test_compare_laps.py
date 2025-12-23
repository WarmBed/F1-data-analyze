#!/usr/bin/env python3
"""比較 FastF1 和 Live Timing 的圈數編號"""
import sys
sys.path.insert(0, '.')
import pickle
from pathlib import Path

# Live Timing cache
lt_path = Path('data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl')
with lt_path.open('rb') as f:
    lt_data = pickle.load(f)

# FastF1 cache
ff1_path = Path('cache/2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-07_Race/_extended_timing_data.ff1pkl')
with ff1_path.open('rb') as f:
    ff1_data = pickle.load(f)

ff1_df = ff1_data['data'][0]
ver_ff1 = ff1_df[ff1_df['Driver'] == '1'].dropna(subset=['NumberOfLaps']).sort_values('Time')

print('FastF1 VER lap end times:')
for _, row in ver_ff1.head(5).iterrows():
    t = row['Time']
    if hasattr(t, 'total_seconds'):
        t_s = t.total_seconds()
    else:
        t_s = float(t)
    lap = int(row['NumberOfLaps'])
    print(f'  Lap {lap} ends at: {t_s:.1f}s')

print()

# Live Timing
snapshots = lt_data['snapshots']
# 找每個圈開始和結束的時間
lt_lap_ranges = {}
for snap in snapshots:
    t = snap.get('race_time_seconds', 0)
    ver = snap.get('drivers', {}).get('1', {})
    lap = ver.get('lap')
    if lap:
        if lap not in lt_lap_ranges:
            lt_lap_ranges[lap] = {'start': t, 'end': t}
        else:
            lt_lap_ranges[lap]['end'] = max(lt_lap_ranges[lap]['end'], t)
            lt_lap_ranges[lap]['start'] = min(lt_lap_ranges[lap]['start'], t)

print('Live Timing VER lap ranges:')
for lap in sorted(lt_lap_ranges.keys())[:5]:
    r = lt_lap_ranges[lap]
    print(f"  Lap {lap}: {r['start']:.1f}s - {r['end']:.1f}s")

print()
print("Comparison:")
print("  FastF1 Lap 1 ends at 3592.4s")
print("  Live Timing Lap 1 starts at 3592.8s")
print("  => Live Timing 'Lap 1' = FastF1 'Lap 2' (offset by 1)")
