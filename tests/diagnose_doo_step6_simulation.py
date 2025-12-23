"""
模擬 _calculate_segment_acceleration_improved() 的步驟 6
找出為什麼 DOO 的終點速度只有 278 km/h
"""

import fastf1
import pandas as pd
from pathlib import Path

# 設置緩存
cache_dir = Path("f1_analysis_cache")
cache_dir.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(cache_dir))

print("載入數據...")
session = fastf1.get_session(2025, "China", "R")
session.load()

# 獲取 DOO 的最快單圈
doo_laps = session.laps.pick_drivers("DOO")
fastest_lap = doo_laps.loc[doo_laps["LapTime"].idxmin()]
car_data = fastest_lap.get_telemetry()

# 中國站硬編碼起點
CHINA_START = 3544

print("=" * 100)
print("🔍 模擬步驟 1-3: 數據提取和清理")
print("=" * 100)

# 步驟 2: 提取數據
speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
distances = pd.to_numeric(car_data["Distance"], errors="coerce")
times = car_data["Time"]
throttles = pd.to_numeric(car_data["Throttle"], errors="coerce")

print(f"原始數據點數: {len(car_data)}")
print(f"距離範圍: {distances.min():.1f}m - {distances.max():.1f}m")

# 步驟 3: 移除 NaN
valid_mask = ~(speeds.isna() | distances.isna() | throttles.isna())
speeds = speeds[valid_mask]
distances = distances[valid_mask]
times = times[valid_mask]
throttles = throttles[valid_mask]

print(f"清理後數據點數: {len(speeds)}")
print(f"清理後距離範圍: {distances.min():.1f}m - {distances.max():.1f}m")
print()

print("=" * 100)
print("🔍 模擬步驟 4: 找到起點")
print("=" * 100)

# 步驟 4: 找到起點
valid_start_indices = distances[distances >= CHINA_START].index
if len(valid_start_indices) == 0:
    print("❌ 找不到起點")
    exit(1)

start_candidates = distances[valid_start_indices]
distance_diffs = (start_candidates - CHINA_START).abs()
start_idx = distance_diffs.idxmin()

print(f"起點索引: {start_idx}")
print(f"起點距離: {distances[start_idx]:.1f}m")
print(f"起點速度: {speeds[start_idx]:.1f} km/h")
print(f"起點油門: {throttles[start_idx]:.1f}%")
print()

print("=" * 100)
print("🔍 模擬步驟 5: 檢查起點油門")
print("=" * 100)

THROTTLE_START_MIN = 50
if throttles[start_idx] <= THROTTLE_START_MIN:
    print(f"起點油門 <= {THROTTLE_START_MIN}%，需要調整...")
    future_high_throttle = throttles.loc[start_idx:] > THROTTLE_START_MIN
    if future_high_throttle.any():
        start_idx = future_high_throttle[future_high_throttle].index[0]
        print(f"✅ 調整後起點索引: {start_idx}")
        print(f"   起點距離: {distances[start_idx]:.1f}m")
        print(f"   起點油門: {throttles[start_idx]:.1f}%")
else:
    print(f"✅ 起點油門 > {THROTTLE_START_MIN}%，無需調整")
print()

print("=" * 100)
print("🔍 模擬步驟 6: 搜尋低油門點 ⭐ 關鍵步驟")
print("=" * 100)

THROTTLE_END_MAX = 5
future_throttles = throttles.loc[start_idx:]  # 從起點開始的所有油門數據
low_throttle_mask = future_throttles <= THROTTLE_END_MAX  # 所有 <= 5% 的點

print(f"從起點開始的數據點數: {len(future_throttles)}")
print(f"油門範圍: {future_throttles.min():.1f}% - {future_throttles.max():.1f}%")
print(f"油門 <= {THROTTLE_END_MAX}% 的點數: {low_throttle_mask.sum()}")
print()

if low_throttle_mask.any():
    # 找到第一個 <= 5% 的點
    first_low_throttle_idx = low_throttle_mask[low_throttle_mask].index[0]
    print(f"✅ 找到第一個低油門點:")
    print(f"   索引: {first_low_throttle_idx}")
    print(f"   距離: {distances[first_low_throttle_idx]:.1f}m")
    print(f"   速度: {speeds[first_low_throttle_idx]:.1f} km/h")
    print(f"   油門: {throttles[first_low_throttle_idx]:.1f}%")
    print()
    
    # 終點是前一個點
    loc_in_future = future_throttles.index.get_loc(first_low_throttle_idx)
    print(f"   在 future_throttles 中的位置: {loc_in_future}")
    
    if loc_in_future > 0:
        potential_end_idx = future_throttles.index[loc_in_future - 1]
        end_idx = potential_end_idx if potential_end_idx > start_idx else start_idx
        
        print(f"✅ 終點（前一點）:")
        print(f"   索引: {end_idx}")
        print(f"   距離: {distances[end_idx]:.1f}m")
        print(f"   速度: {speeds[end_idx]:.1f} km/h ⭐")
        print(f"   油門: {throttles[end_idx]:.1f}%")
        print()
        
        # 計算加速數據
        print(f"📊 加速區間:")
        print(f"   距離: {distances[start_idx]:.1f}m → {distances[end_idx]:.1f}m")
        print(f"   距離差: {distances[end_idx] - distances[start_idx]:.1f}m")
        print(f"   速度: {speeds[start_idx]:.1f} → {speeds[end_idx]:.1f} km/h")
        print(f"   速度增益: {speeds[end_idx] - speeds[start_idx]:.1f} km/h ⭐")
    else:
        print("❌ 第一個低油門點就是起點，無法計算")
else:
    print("⚠️ 沒有找到低油門點，使用最後一個點")
    end_idx = future_throttles.index[-1]
    print(f"   終點距離: {distances[end_idx]:.1f}m")
    print(f"   終點速度: {speeds[end_idx]:.1f} km/h")
    print(f"   終點油門: {throttles[end_idx]:.1f}%")

print("=" * 100)

# 顯示起點到低油門點之間的完整遙測數據
print("\n" + "=" * 100)
print("📊 起點到第一個低油門點之間的遙測數據（每 50m 顯示）:")
print("=" * 100)
print(f"{'距離 (m)':>10} {'速度 (km/h)':>12} {'油門 (%)':>10} {'註記':>30}")
print("-" * 100)

segment_data = car_data.loc[start_idx:first_low_throttle_idx if low_throttle_mask.any() else end_idx]
prev_dist = 0
for idx in segment_data.index:
    dist = distances[idx]
    speed = speeds[idx]
    throttle = throttles[idx]
    
    if dist - prev_dist >= 50 or throttle <= THROTTLE_END_MAX:
        note = ""
        if idx == start_idx:
            note = "⭐ 起點"
        elif idx == end_idx:
            note = "⭐ 終點（前一點）"
        elif throttle <= THROTTLE_END_MAX:
            note = "⚠️ 油門 <= 5%"
        
        print(f"{dist:>10.1f} {speed:>12.1f} {throttle:>10.1f} {note:>30}")
        prev_dist = dist

print("=" * 100)
