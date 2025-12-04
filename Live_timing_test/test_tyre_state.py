#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""測試輪胎狀態索引"""

from Live_timing_test.demo_histroy_live_position_tracking import *
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)

# 使用與主程式相同的方式初始化
ds = LiveF1DataSource(2025, "Japan", "Race")
ds.load_all_data()

proc = LivePositionDataProcessor(ds)
proc.process()

print("=" * 60)
print("輪胎狀態索引測試")
print("=" * 60)

# 1. 檢查輪胎時間戳格式
print("\n=== 輪胎時間戳 ===")
if proc._tyre_timestamps:
    print(f"總數: {len(proc._tyre_timestamps)}")
    print(f"前 3 個: {proc._tyre_timestamps[:3]}")
    print(f"後 3 個: {proc._tyre_timestamps[-3:]}")
else:
    print("沒有輪胎時間戳!")

# 2. 檢查 snapshot 時間戳格式
print("\n=== 快照時間戳 ===")
snapshots = proc.get_snapshots()
if snapshots:
    print(f"總數: {len(snapshots)}")
    print(f"第 1 個: {snapshots[0].get('timestamp')}")
    print(f"第 100 個: {snapshots[100].get('timestamp') if len(snapshots) > 100 else 'N/A'}")
    print(f"最後 1 個: {snapshots[-1].get('timestamp')}")
else:
    print("沒有快照!")

# 3. 比較格式
print("\n=== 格式比較 ===")
if proc._tyre_timestamps and snapshots:
    tyre_ts_sample = proc._tyre_timestamps[0]
    snap_ts_sample = snapshots[100].get('timestamp') if len(snapshots) > 100 else snapshots[0].get('timestamp')
    print(f"輪胎時間戳格式: '{tyre_ts_sample}'")
    print(f"快照時間戳格式: '{snap_ts_sample}'")
    print(f"輪胎時間戳類型: {type(tyre_ts_sample)}")
    print(f"快照時間戳類型: {type(snap_ts_sample)}")

# 4. 測試 get_tyre_state_at_time
print("\n=== 查詢測試 ===")
if snapshots:
    test_ts = snapshots[100].get('timestamp') if len(snapshots) > 100 else snapshots[0].get('timestamp')
    print(f"測試時間戳: '{test_ts}'")
    result = proc.get_tyre_state_at_time(test_ts)
    print(f"返回車手數: {len(result)}")
    if result:
        for driver, info in list(result.items())[:3]:
            print(f"  {driver}: {info}")
    else:
        print("結果為空!")

# 5. 手動測試比較
print("\n=== 手動比較 ===")
if proc._tyre_timestamps and snapshots:
    snap_ts = snapshots[500].get('timestamp') if len(snapshots) > 500 else snapshots[-1].get('timestamp')
    print(f"目標時間戳: '{snap_ts}'")
    
    # 嘗試找匹配
    matches = [ts for ts in proc._tyre_timestamps if ts <= snap_ts]
    print(f"匹配的輪胎時間戳數量: {len(matches)}")
    if matches:
        print(f"最接近的: '{matches[-1]}'")
        print(f"該時間戳的狀態: {list(proc._tyre_state_index.get(matches[-1], {}).items())[:2]}")
