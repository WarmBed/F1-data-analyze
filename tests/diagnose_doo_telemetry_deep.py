#!/usr/bin/env python3
"""深度分析 DOO 的遙測數據 - 為什麼加速提前停止？"""

import sys
import warnings
warnings.filterwarnings('ignore')

# 添加專案路徑
sys.path.insert(0, r'C:\Users\mike2\OneDrive\Code\F1-data-analyze')

from CLI_modules.cli.data_loader import UnifiedDataLoader
import pandas as pd

# 初始化數據載入器
loader = UnifiedDataLoader()
success = loader.load_session(year=2025, race="China", session_type="R")

if not success:
    print("❌ 無法載入 2025 China R 數據")
    sys.exit(1)

# 獲取 DOO 的最速圈
session = loader.session
doo_laps = session.laps.pick_driver("DOO")
fastest_lap = doo_laps.pick_fastest()
car_data = fastest_lap.get_car_data()

# 提取關鍵數據
speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
distances = pd.to_numeric(car_data["Distance"], errors="coerce")
times = car_data["Time"]

# 計算加速度
if "Acceleration" in car_data.columns:
    accelerations = pd.to_numeric(car_data["Acceleration"], errors="coerce")
else:
    speed_ms = speeds / 3.6
    time_diffs = []
    for i in range(len(times)):
        if i == 0:
            time_diffs.append(0.0)
        else:
            t1 = times.iloc[i-1]
            t2 = times.iloc[i]
            if hasattr(t1, "total_seconds"):
                dt = t2.total_seconds() - t1.total_seconds()
            else:
                dt = float(t2) - float(t1)
            time_diffs.append(dt if dt > 0 else 0.0)
    time_diffs_series = pd.Series(time_diffs, index=speeds.index)
    speed_diffs = speed_ms.diff()
    accelerations = speed_diffs / time_diffs_series
    accelerations = accelerations.fillna(0.0)

# 移除 NaN
valid_mask = ~(speeds.isna() | distances.isna() | accelerations.isna())
speeds = speeds[valid_mask]
distances = distances[valid_mask]
accelerations = accelerations[valid_mask]

print("=" * 100)
print("🔍 DOO 遙測數據深度分析 - 2025 China R")
print("=" * 100)

# 找到關鍵位置
hardcoded_start = 3544  # China 硬編碼起點
doo_actual_start = 3549.3  # 實際測量起點
doo_end = 3549.3 + 363.94  # DOO 的終點（約 3913m）
reference_end = 4335.5  # 參考範圍終點

print(f"\n📍 關鍵位置:")
print(f"  硬編碼起點: {hardcoded_start}m")
print(f"  實際測量起點: {doo_actual_start:.1f}m")
print(f"  DOO 的終點: {doo_end:.1f}m ⚠️")
print(f"  參考範圍終點: {reference_end:.1f}m")
print(f"  提前停止距離: {reference_end - doo_end:.1f}m")

# 分析 3500m - 4400m 範圍的數據
analysis_range = (distances >= 3500) & (distances <= 4400)
analysis_data = pd.DataFrame({
    'Distance': distances[analysis_range],
    'Speed': speeds[analysis_range],
    'Acceleration': accelerations[analysis_range]
})

print(f"\n📊 加速段數據分析（3500m - 4400m）:")
print(f"  數據點數: {len(analysis_data)}")

# 找到關鍵點
start_idx = (distances - doo_actual_start).abs().idxmin()
end_idx = (distances - doo_end).abs().idxmin()

print(f"\n✅ 起點（約 {doo_actual_start:.1f}m）:")
print(f"  實際距離: {distances[start_idx]:.1f}m")
print(f"  速度: {speeds[start_idx]:.1f} km/h")
print(f"  加速度: {accelerations[start_idx]:.2f} m/s²")

print(f"\n⚠️  終點（約 {doo_end:.1f}m）:")
print(f"  實際距離: {distances[end_idx]:.1f}m")
print(f"  速度: {speeds[end_idx]:.1f} km/h")
print(f"  加速度: {accelerations[end_idx]:.2f} m/s²")

# 檢查終點後的數據
after_end_mask = (distances > doo_end) & (distances <= reference_end)
after_end_data = pd.DataFrame({
    'Distance': distances[after_end_mask],
    'Speed': speeds[after_end_mask],
    'Acceleration': accelerations[after_end_mask]
})

if len(after_end_data) > 0:
    print(f"\n🔍 終點後的數據（{doo_end:.1f}m - {reference_end:.1f}m）:")
    print(f"  數據點數: {len(after_end_data)}")
    print(f"  速度範圍: {after_end_data['Speed'].min():.1f} - {after_end_data['Speed'].max():.1f} km/h")
    print(f"  加速度範圍: {after_end_data['Acceleration'].min():.2f} - {after_end_data['Acceleration'].max():.2f} m/s²")
    print(f"  平均加速度: {after_end_data['Acceleration'].mean():.2f} m/s²")
    
    # 找到第一個負加速度的點
    negative_accel = after_end_data[after_end_data['Acceleration'] < -0.5]
    if len(negative_accel) > 0:
        first_negative = negative_accel.iloc[0]
        print(f"\n  ⭐ 第一個負加速度點 (< -0.5):")
        print(f"    距離: {first_negative['Distance']:.1f}m")
        print(f"    速度: {first_negative['Speed']:.1f} km/h")
        print(f"    加速度: {first_negative['Acceleration']:.2f} m/s²")
    else:
        print(f"\n  ✅ 沒有發現負加速度點 (< -0.5)")

# 詳細列出 3900m - 3950m 的數據
detail_range = (distances >= 3900) & (distances <= 3950)
detail_data = pd.DataFrame({
    'Distance': distances[detail_range],
    'Speed': speeds[detail_range],
    'Acceleration': accelerations[detail_range]
})

print(f"\n📋 詳細數據（3900m - 3950m）:")
print(f"{'距離 (m)':<12} {'速度 (km/h)':<15} {'加速度 (m/s²)':<18}")
print("-" * 45)
for idx, row in detail_data.head(20).iterrows():
    marker = " ⚠️" if row['Acceleration'] < -0.5 else ""
    print(f"{row['Distance']:<12.1f} {row['Speed']:<15.1f} {row['Acceleration']:<18.2f}{marker}")

# 檢查 DOO 的最高速度點
max_speed = speeds.max()
max_speed_idx = speeds.idxmax()
max_speed_distance = distances[max_speed_idx]

print(f"\n🏁 DOO 的最高速度點:")
print(f"  最高速度: {max_speed:.1f} km/h")
print(f"  位置: {max_speed_distance:.1f}m")
print(f"  與參考終點的距離: {reference_end - max_speed_distance:.1f}m")

print("\n" + "=" * 100)
