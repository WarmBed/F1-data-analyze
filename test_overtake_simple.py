#!/usr/bin/env python3
"""簡單測試 overtake_detector"""
import sys
print("Step 1: Starting", flush=True)

# 直接用 importlib 載入，避免可能的 __init__.py 問題
import importlib.util
import os

detector_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "modules", "gui", "live_timing", "utils", "overtake_detector.py"
)

print(f"Step 2: Loading from {detector_path}", flush=True)
print(f"Step 3: Path exists = {os.path.exists(detector_path)}", flush=True)

spec = importlib.util.spec_from_file_location("overtake_detector_test", detector_path)
print("Step 4: spec created", flush=True)

module = importlib.util.module_from_spec(spec)
print("Step 5: module created", flush=True)

sys.modules["overtake_detector_test"] = module
spec.loader.exec_module(module)
print("Step 6: module loaded", flush=True)

# 創建檢測器
detector = module.LiveTimingOvertakeDetector(2025, 'Abu Dhabi', 'R')
print(f"Step 7: Detector created, data_dir = {detector.data_dir}", flush=True)
print(f"Step 8: Directory exists = {os.path.exists(detector.data_dir)}", flush=True)

# 執行分析
print("Step 9: Running analyze()...", flush=True)
stats = detector.analyze()
print("Step 10: Analysis complete!", flush=True)

print("\n" + "=" * 60, flush=True)
print("RESULTS:", flush=True)
print(f"Total overtakes: {stats.total_overtakes}", flush=True)
print(f"On-track overtakes: {stats.on_track_overtakes}", flush=True)
print(f"Pit-related changes: {stats.pit_related_changes}", flush=True)
print(f"Lap 1 changes: {stats.lap_one_changes}", flush=True)
print(f"SC-related changes: {stats.sc_related_changes}", flush=True)
