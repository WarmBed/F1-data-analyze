"""檢查 Live Timing 原始緩存中 VER 的 snapshot 分佈"""
import sys
sys.path.insert(0, '.')

print("Starting...", flush=True)

from modules.gui.live_timing.core.f1_api_downloader import F1APIDownloader
from collections import defaultdict

print("Imported modules", flush=True)

downloader = F1APIDownloader()
cache_data = downloader.download_and_cache(year=2025, race="Abu_Dhabi", session="R", force=False)

snapshots = cache_data.get("snapshots", [])
print(f"Total snapshots: {len(snapshots)}")

# 統計 VER 在各圈的 snapshot 數量
ver_lap_counts = defaultdict(int)
ver_lap_first_time = {}
ver_lap_last_time = {}

for snap in snapshots:
    t = snap.get("race_time_seconds", 0)
    drivers = snap.get("drivers", {}) or {}
    
    d = drivers.get("1")  # VER = driver number 1
    if d and isinstance(d, dict):
        lap = d.get("lap")
        if lap and lap > 0:
            ver_lap_counts[lap] += 1
            if lap not in ver_lap_first_time:
                ver_lap_first_time[lap] = t
            ver_lap_last_time[lap] = t

print(f"\n=== VER (driver #1) raw snapshot distribution ===")
print(f"Laps with snapshots: {sorted(ver_lap_counts.keys())}")
print(f"Total laps with data: {len(ver_lap_counts)}")

if ver_lap_counts:
    min_lap = min(ver_lap_counts.keys())
    max_lap = max(ver_lap_counts.keys())
    print(f"Lap range: {min_lap} - {max_lap}")
    
    missing = [i for i in range(1, 59) if i not in ver_lap_counts]
    print(f"Missing laps (1-58): {missing}")
    
    print(f"\nSnapshot count per lap:")
    for lap in sorted(ver_lap_counts.keys()):
        t_start = ver_lap_first_time.get(lap, 0)
        t_end = ver_lap_last_time.get(lap, 0)
        print(f"  Lap {lap:2d}: {ver_lap_counts[lap]:4d} snapshots (t={t_start:.1f}s - {t_end:.1f}s)")
