"""檢查 Abu Dhabi 2025 Live Timing 緩存中 VER 的圈數分佈"""
import sys
sys.path.insert(0, '.')

from api.f1_api_downloader import F1APIDownloader

downloader = F1APIDownloader()
cache_data = downloader.download_and_cache(year=2025, race="Abu_Dhabi", session="R", force=False)

snapshots = cache_data.get("snapshots", [])
print(f"Total snapshots: {len(snapshots)}")

# 統計每位車手在各圈的 snapshot 數量
from collections import defaultdict
lap_counts = defaultdict(lambda: defaultdict(int))  # driver -> lap -> count

for snap in snapshots:
    drivers = snap.get("drivers", {}) or {}
    for drv_num, d in drivers.items():
        if not isinstance(d, dict):
            continue
        lap = d.get("lap")
        if lap is not None and lap > 0:
            lap_counts[drv_num][int(lap)] += 1

# 找 VER (driver number = 1)
print("\n=== VER (driver #1) lap distribution ===")
ver_laps = lap_counts.get("1", {})
if ver_laps:
    sorted_laps = sorted(ver_laps.keys())
    print(f"Laps with data: {sorted_laps}")
    print(f"Total laps: {len(sorted_laps)}")
    print(f"Min lap: {min(sorted_laps)}, Max lap: {max(sorted_laps)}")
    
    # 找缺失的圈
    if sorted_laps:
        missing = [i for i in range(1, max(sorted_laps)+1) if i not in sorted_laps]
        print(f"Missing laps: {missing}")
else:
    print("No data for VER!")

# 對比其他車手
print("\n=== All drivers lap count ===")
for drv_num in sorted(lap_counts.keys(), key=lambda x: int(x) if x.isdigit() else 999):
    laps = lap_counts[drv_num]
    sorted_laps = sorted(laps.keys())
    if sorted_laps:
        print(f"Driver #{drv_num}: Lap {min(sorted_laps)}-{max(sorted_laps)} ({len(sorted_laps)} laps)")
