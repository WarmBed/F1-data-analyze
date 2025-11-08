"""
檢查 DOO 在直線段的遙測數據完整性
找出是否有 NaN 值導致數據被截斷
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
telemetry = fastest_lap.get_telemetry()

# 中國站硬編碼起點
CHINA_START = 3544

# 找到起點附近的數據
start_region = telemetry[
    (telemetry["Distance"] >= CHINA_START) &
    (telemetry["Distance"] <= CHINA_START + 1200)
].copy()

print("=" * 100)
print(f"🔍 檢查 DOO 的遙測數據（{CHINA_START}m 起，範圍 1200m）")
print("=" * 100)
print(f"   總數據點數: {len(start_region)}")
print()

# 檢查 Speed 欄位的 NaN
speeds = pd.to_numeric(start_region["Speed"], errors="coerce")
speed_na_count = speeds.isna().sum()
print(f"📊 Speed 欄位:")
print(f"   NaN 數量: {speed_na_count} / {len(speeds)} ({speed_na_count/len(speeds)*100:.2f}%)")
if speed_na_count > 0:
    print(f"   ⚠️ 第一個 NaN 位置: 索引 {speeds.isna().idxmax()}")

# 檢查 Distance 欄位的 NaN
distances = pd.to_numeric(start_region["Distance"], errors="coerce")
distance_na_count = distances.isna().sum()
print(f"\n📊 Distance 欄位:")
print(f"   NaN 數量: {distance_na_count} / {len(distances)} ({distance_na_count/len(distances)*100:.2f}%)")
if distance_na_count > 0:
    print(f"   ⚠️ 第一個 NaN 位置: 索引 {distances.isna().idxmax()}")

# 檢查 Throttle 欄位的 NaN
throttles = pd.to_numeric(start_region["Throttle"], errors="coerce")
throttle_na_count = throttles.isna().sum()
print(f"\n📊 Throttle 欄位:")
print(f"   NaN 數量: {throttle_na_count} / {len(throttles)} ({throttle_na_count/len(throttles)*100:.2f}%)")
if throttle_na_count > 0:
    print(f"   ⚠️ 第一個 NaN 位置: 索引 {throttles.isna().idxmax()}")

# 檢查綜合 valid_mask
valid_mask = ~(speeds.isna() | distances.isna() | throttles.isna())
invalid_count = (~valid_mask).sum()
print(f"\n📊 綜合有效性:")
print(f"   有效點數: {valid_mask.sum()} / {len(valid_mask)}")
print(f"   無效點數: {invalid_count} ({invalid_count/len(valid_mask)*100:.2f}%)")

if invalid_count > 0:
    print(f"   ⚠️ 第一個無效位置: 索引 {(~valid_mask).idxmax()}")
    first_invalid_idx = (~valid_mask).idxmax()
    print(f"   第一個無效點的數據:")
    print(f"      Distance: {start_region.loc[first_invalid_idx, 'Distance']}")
    print(f"      Speed: {start_region.loc[first_invalid_idx, 'Speed']}")
    print(f"      Throttle: {start_region.loc[first_invalid_idx, 'Throttle']}")

# 顯示清理後的數據範圍
filtered_data = start_region[valid_mask]
if len(filtered_data) > 0:
    print(f"\n📊 清理後的數據範圍:")
    print(f"   距離: {filtered_data['Distance'].min():.1f}m - {filtered_data['Distance'].max():.1f}m")
    print(f"   速度: {filtered_data['Speed'].min():.1f} - {filtered_data['Speed'].max():.1f} km/h")
    print(f"   油門: {filtered_data['Throttle'].min():.1f}% - {filtered_data['Throttle'].max():.1f}%")
    
    # 檢查是否在清理後數據中能找到低油門點
    low_throttle_in_filtered = (filtered_data["Throttle"] <= 5).any()
    print(f"\n❓ 清理後的數據中是否有油門 <= 5%: {low_throttle_in_filtered}")
    
    if not low_throttle_in_filtered:
        print("   ⚠️ 這就是問題！清理後的數據中沒有低油門點，導致演算法使用最後一個點作為終點")

print("=" * 100)
