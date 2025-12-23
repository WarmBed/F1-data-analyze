"""檢查 Live Timing PKL 緩存中 VER 的 snapshot 分佈"""
import pickle
from pathlib import Path
from collections import defaultdict
import json

# 嘗試載入 Live Timing 緩存
pkl_dir = Path("cache/2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-07_Race")

# 檢查是否有已處理的 snapshots 緩存
live_timing_cache = list(pkl_dir.glob("live_timing_cache_*.pkl"))
print(f"Found Live Timing cache files: {[f.name for f in live_timing_cache]}", flush=True)

# 嘗試找 PKL 格式的快照緩存
if live_timing_cache:
    with live_timing_cache[0].open("rb") as f:
        data = pickle.load(f)
    
    snapshots = data.get("snapshots", [])
    print(f"\nTotal snapshots: {len(snapshots)}", flush=True)
    
    # 統計 VER 在各圈的出現次數
    ver_lap_counts = defaultdict(int)
    ver_lap_times = defaultdict(list)
    
    for snap in snapshots:
        t = snap.get("race_time_seconds", 0)
        drivers = snap.get("drivers", {}) or {}
        
        ver = drivers.get("1")
        if ver and isinstance(ver, dict):
            lap = ver.get("lap")
            if lap and lap > 0:
                ver_lap_counts[lap] += 1
                ver_lap_times[lap].append(t)
    
    print(f"\n=== VER (driver #1) in snapshots ===", flush=True)
    print(f"Laps with data: {sorted(ver_lap_counts.keys())}", flush=True)
    print(f"Total laps: {len(ver_lap_counts)}", flush=True)
    
    if ver_lap_counts:
        min_lap = min(ver_lap_counts.keys())
        max_lap = max(ver_lap_counts.keys())
        print(f"Lap range: {min_lap} - {max_lap}", flush=True)
        
        missing = [i for i in range(1, 59) if i not in ver_lap_counts]
        print(f"Missing laps (1-58): {missing}", flush=True)
else:
    print("No Live Timing cache file found", flush=True)
    
    # 檢查是否需要從 timing_app_data 載入
    timing_path = pkl_dir / "timing_app_data.ff1pkl"
    if timing_path.exists():
        print(f"\nLoading timing_app_data...", flush=True)
        with timing_path.open("rb") as f:
            timing_data = pickle.load(f)
        
        if isinstance(timing_data, dict):
            print(f"Keys: {list(timing_data.keys())}", flush=True)
            data = timing_data.get("data", timing_data)
            
            if hasattr(data, 'columns'):
                print(f"Columns: {data.columns.tolist()}", flush=True)
                print(f"Shape: {data.shape}", flush=True)
            elif isinstance(data, dict):
                print(f"Data keys: {list(data.keys())[:10]}", flush=True)
