"""
深度檢查 DOO 的油門和速度數據
找出為什麼在 278 km/h 就停止測量
"""

import fastf1
import pandas as pd
from pathlib import Path

# 設置緩存
cache_dir = Path("f1_analysis_cache")
cache_dir.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(cache_dir))

print("=" * 100)
print("🔍 載入 2025 China R 的賽事數據...")
print("=" * 100)

session = fastf1.get_session(2025, "China", "R")
session.load()

print("✅ 賽事數據載入完成")
print()

# 獲取 DOO 的單圈數據
doo_laps = session.laps.pick_drivers("DOO")
fastest_lap_num = doo_laps["LapTime"].idxmin()
fastest_lap = doo_laps.loc[fastest_lap_num]

print("=" * 100)
print(f"🏎️  DOO 的最快單圈數據（Lap {fastest_lap['LapNumber']}）")
print("=" * 100)
print(f"   單圈時間: {fastest_lap['LapTime']}")
print()

# 獲取遙測數據
telemetry = fastest_lap.get_telemetry()

# 中國站硬編碼起點
CHINA_START = 3544

# 找到起點附近的數據（±200m）
start_region = telemetry[
    (telemetry["Distance"] >= CHINA_START - 50) &
    (telemetry["Distance"] <= CHINA_START + 1600)
].copy()

print("=" * 100)
print(f"📊 DOO 在直線段的遙測數據（{CHINA_START}m 起）")
print("=" * 100)
print(f"{'距離 (m)':>10} {'速度 (km/h)':>12} {'油門 (%)':>10} {'DRS':>6} {'註記':>30}")
print("-" * 100)

# 每隔 50m 顯示一個數據點
prev_distance = 0
for idx, row in start_region.iterrows():
    dist = row["Distance"]
    speed = row["Speed"]
    throttle = row["Throttle"]
    drs = "ON" if row.get("DRS", 0) > 0 else "OFF"
    
    # 每 50m 顯示一次
    if dist - prev_distance >= 50 or throttle <= 5:
        note = ""
        if throttle <= 5:
            note = "⚠️ 油門 <= 5% (終點候選)"
        elif throttle <= 50:
            note = "⚠️ 油門 <= 50%"
        elif speed > 300:
            note = "✅ 高速區"
        
        print(f"{dist:>10.1f} {speed:>12.1f} {throttle:>10.1f} {drs:>6} {note:>30}")
        prev_distance = dist
        
        # 如果找到油門 <= 5% 就停止
        if throttle <= 5:
            print("-" * 100)
            print(f"🛑 找到第一個油門 <= 5% 的點: {dist:.1f}m, 速度 {speed:.1f} km/h")
            break

print("=" * 100)

# 統計油門分布
print(f"\n📊 油門統計（{CHINA_START}m 後 1000m 範圍）:")
region_1000m = telemetry[
    (telemetry["Distance"] >= CHINA_START) &
    (telemetry["Distance"] <= CHINA_START + 1000)
]

throttle_stats = region_1000m["Throttle"].describe()
print(f"   最小值: {throttle_stats['min']:.1f}%")
print(f"   25% 分位: {throttle_stats['25%']:.1f}%")
print(f"   中位數: {throttle_stats['50%']:.1f}%")
print(f"   75% 分位: {throttle_stats['75%']:.1f}%")
print(f"   最大值: {throttle_stats['max']:.1f}%")

# 計算油門 <= 5% 的點數
low_throttle_count = (region_1000m["Throttle"] <= 5).sum()
print(f"   油門 <= 5% 的點數: {low_throttle_count} / {len(region_1000m)} ({low_throttle_count/len(region_1000m)*100:.1f}%)")

print("=" * 100)
