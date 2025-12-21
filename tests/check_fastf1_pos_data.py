#!/usr/bin/env python3
"""檢查 FastF1 position data 的實際點數"""

import fastf1

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

# 載入 2024 日本 GP
print("載入 2024 日本 GP...")
session = fastf1.get_session(2024, 'Japan', 'R')
session.load()

# 獲取最快圈
laps = session.laps
fastest_lap = laps.pick_fastest()

print(f"\n最快圈: {fastest_lap['Driver']} - Lap {fastest_lap['LapNumber']}")
print(f"圈速: {fastest_lap['LapTime']}")

# 檢查 position data
print("\n=== Position Data (get_pos_data()) ===")
pos_data = fastest_lap.get_pos_data()
print(f"Position data 點數: {len(pos_data)}")
print(f"可用欄位: {list(pos_data.columns)}")
if 'Distance' in pos_data.columns:
    print(f"Distance 範圍: {pos_data['Distance'].min():.2f}m ~ {pos_data['Distance'].max():.2f}m")
else:
    print(f"⚠️ Position data 沒有 Distance 欄位！")

# 檢查 telemetry data
print("\n=== Telemetry Data (get_telemetry()) ===")
telemetry = fastest_lap.get_telemetry()
print(f"Telemetry 點數: {len(telemetry)}")
print(f"可用欄位: {list(telemetry.columns)[:10]}...")  # 只顯示前10個
if 'Distance' in telemetry.columns:
    print(f"Distance 範圍: {telemetry['Distance'].min():.2f}m ~ {telemetry['Distance'].max():.2f}m")
if 'X' in telemetry.columns and 'Y' in telemetry.columns:
    print(f"✅ Telemetry 包含 X, Y 座標")

# 比較
print("\n=== 結論 ===")
print(f"Position data: {len(pos_data)} 點 (粗略)")
print(f"Telemetry data: {len(telemetry)} 點 (詳細)")
print(f"建議: 使用 Telemetry 數據以獲得完整的賽道位置點")
