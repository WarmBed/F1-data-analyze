#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷速度模組關閉後按鈕仍顯示的問題
"""

import sys
import io

# 設置標準輸出為 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 80)
print("[DIAGNOSTIC] Speed Analysis Button Cleanup Test")
print("=" * 80)

print("\n[INFO] Reading latest log file...")

# 讀取日誌檔案
import os
from datetime import datetime

log_file = "logs/f1_gui_2025-10-16.log"

if not os.path.exists(log_file):
    print(f"[ERROR] Log file not found: {log_file}")
    sys.exit(1)

print(f"[INFO] Log file: {log_file}")
print(f"[INFO] File size: {os.path.getsize(log_file)} bytes")

# 讀取最後 1000 行
with open(log_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    last_1000 = lines[-1000:] if len(lines) > 1000 else lines

print(f"[INFO] Total lines: {len(lines)}, Reading last: {len(last_1000)}")

# 搜尋關鍵事件
events = {
    "speed_opened": [],
    "speed_closed": [],
    "hide_lap_controls_called": [],
    "hide_lap_controls_executed": [],
    "buttons_removed": [],
    "lap_windows_count": []
}

for i, line in enumerate(last_1000):
    # Speed Analysis 開啟
    if "Speed Analysis" in line and ("開啟" in line or "opened" in line.lower()):
        events["speed_opened"].append((i, line.strip()))
    
    # Speed Analysis 關閉
    if "Speed Analysis" in line and ("關閉" in line or "closed" in line.lower()):
        events["speed_closed"].append((i, line.strip()))
    
    # hide_lap_controls 被調用
    if "開始隱藏圈速分析控件" in line or "開始隱藏圈速分析控件" in line:
        events["hide_lap_controls_called"].append((i, line.strip()))
    
    # hide_lap_controls 執行成功
    if "圈速分析控件成功從工具欄移除" in line or "成功從工具欄移除" in line:
        events["hide_lap_controls_executed"].append((i, line.strip()))
    
    # 按鈕移除
    if "update_all_action" in line.lower() or "lap_linkage_action" in line.lower():
        events["buttons_removed"].append((i, line.strip()))
    
    # lap_analysis_windows 數量
    if "當前活動視窗數" in line or "lap_analysis_windows" in line.lower():
        events["lap_windows_count"].append((i, line.strip()))

# 報告結果
print("\n" + "=" * 80)
print("[ANALYSIS RESULTS]")
print("=" * 80)

print(f"\n[1] Speed Analysis Opened: {len(events['speed_opened'])} times")
for idx, (line_num, line) in enumerate(events['speed_opened'][-3:], 1):
    print(f"    [{idx}] Line {line_num}: {line[:100]}...")

print(f"\n[2] Speed Analysis Closed: {len(events['speed_closed'])} times")
for idx, (line_num, line) in enumerate(events['speed_closed'][-3:], 1):
    print(f"    [{idx}] Line {line_num}: {line[:100]}...")

print(f"\n[3] hide_lap_controls() Called: {len(events['hide_lap_controls_called'])} times")
for idx, (line_num, line) in enumerate(events['hide_lap_controls_called'][-3:], 1):
    print(f"    [{idx}] Line {line_num}: {line[:100]}...")

print(f"\n[4] hide_lap_controls() Executed Successfully: {len(events['hide_lap_controls_executed'])} times")
for idx, (line_num, line) in enumerate(events['hide_lap_controls_executed'][-3:], 1):
    print(f"    [{idx}] Line {line_num}: {line[:100]}...")

print(f"\n[5] Button Removal Events: {len(events['buttons_removed'])} times")
for idx, (line_num, line) in enumerate(events['buttons_removed'][-5:], 1):
    print(f"    [{idx}] Line {line_num}: {line[:100]}...")

print(f"\n[6] lap_analysis_windows Count: {len(events['lap_windows_count'])} times")
for idx, (line_num, line) in enumerate(events['lap_windows_count'][-5:], 1):
    print(f"    [{idx}] Line {line_num}: {line[:100]}...")

# 診斷結論
print("\n" + "=" * 80)
print("[DIAGNOSIS]")
print("=" * 80)

if len(events['speed_closed']) > 0 and len(events['hide_lap_controls_called']) == 0:
    print("\n[ISSUE FOUND] Speed Analysis closed, but hide_lap_controls() was NOT called!")
    print("[REASON] on_lap_analysis_window_closed() may not be triggered")
    print("[ACTION] Check if window_closed signal is connected")
elif len(events['hide_lap_controls_called']) > 0 and len(events['hide_lap_controls_executed']) == 0:
    print("\n[ISSUE FOUND] hide_lap_controls() called, but did NOT execute!")
    print("[REASON] Early return condition triggered:")
    print("  - Check: len(self.lap_analysis_windows) > 0")
    print("  - Check: not self._lap_controls_added")
    print("[ACTION] Review hide_lap_controls() conditions")
elif len(events['hide_lap_controls_executed']) > 0 and len(events['buttons_removed']) == 0:
    print("\n[ISSUE FOUND] hide_lap_controls() executed, but buttons NOT removed!")
    print("[REASON] Button removal logic may have errors")
    print("[ACTION] Check update_all_action and lap_linkage_action cleanup")
else:
    print("\n[STATUS] All events appear normal in logs")
    print("[NOTE] Issue may be:")
    print("  1. Buttons not actually removed from UI (visual bug)")
    print("  2. New buttons created that shouldn't exist")
    print("  3. Reference not cleared (memory leak)")

print("\n" + "=" * 80)
print("[NEXT STEPS]")
print("=" * 80)
print("1. Close Speed Analysis in GUI")
print("2. Run this script again to see updated logs")
print("3. Check if buttons are still visible in toolbar")
print("4. Use Memory Diagnostics to check QAction count")
print("=" * 80)
