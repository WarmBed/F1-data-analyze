#!/usr/bin/env python3
"""測試 2025 Abu Dhabi 的 Live Timing 超車分析"""

import sys
import os

# 確保路徑正確
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing 2025 Abu Dhabi Live Timing Overtake Detection")
print("=" * 60)
import sys
sys.stdout.flush()

print("Importing LiveTimingOvertakeDetector...")
sys.stdout.flush()

from modules.gui.live_timing.utils.overtake_detector import LiveTimingOvertakeDetector

print("Import successful!")
sys.stdout.flush()

# 創建檢測器
print("Creating detector...")
sys.stdout.flush()
detector = LiveTimingOvertakeDetector(2025, 'Abu Dhabi', 'R')

print(f"Data directory: {detector.data_dir}")
print(f"Directory exists: {os.path.exists(detector.data_dir)}")

# 列出目錄內容
if os.path.exists(detector.data_dir):
    print("\nFiles in directory:")
    for f in os.listdir(detector.data_dir):
        print(f"  - {f}")

# 執行分析
print("\n" + "-" * 60)
print("Running analysis...")
stats = detector.analyze()

print("\n" + "=" * 60)
print("RESULTS:")
print("=" * 60)
print(f"Total overtakes: {stats.total_overtakes}")
print(f"On-track overtakes: {stats.on_track_overtakes}")
print(f"Pit-related changes: {stats.pit_related_changes}")
print(f"Lap 1 changes: {stats.lap_one_changes}")
print(f"SC-related changes: {stats.sc_related_changes}")

# 顯示車手數據（如果存在）
if hasattr(stats, 'per_driver_stats') and stats.per_driver_stats:
    print(f"\nPer-driver stats: {len(stats.per_driver_stats)} drivers")
    for driver, data in sorted(stats.per_driver_stats.items(), key=lambda x: x[1].get('overtakes_made', 0), reverse=True):
        overtakes = data.get('overtakes_made', 0)
        defended = data.get('positions_lost', 0)
        if overtakes > 0 or defended > 0:
            print(f"  {driver}: Overtakes={overtakes}, Lost={defended}")
