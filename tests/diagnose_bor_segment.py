"""
診斷 Segment 加速邏輯問題
直接測試 BOR 車手的遙測數據
"""

import fastf1
import pandas as pd

# 載入賽事數據
print("載入 2025 Japan R 賽事...")
session = fastf1.get_session(2025, "Japan", "R")
session.load()

# 選擇 BOR 車手
driver_code = "BOR"
driver_laps = session.laps.pick_drivers(driver_code)
fastest_lap = driver_laps.pick_fastest()

print(f"\n{driver_code} 最速圈: 第 {fastest_lap['LapNumber']} 圈")

# 獲取遙測數據
car_data = fastest_lap.get_car_data()
print(f"\n遙測數據欄位: {list(car_data.columns)}")
print(f"數據點數: {len(car_data)}")

# 檢查距離範圍
distances = car_data["Distance"]
print(f"\n距離範圍: {distances.min():.1f}m - {distances.max():.1f}m")

# 硬編碼起點
hardcoded_start = 5650.0
print(f"\n硬編碼起點: {hardcoded_start}m")

# 檢查起點附近的數據
start_area = car_data[(distances >= hardcoded_start - 100) & (distances <= hardcoded_start + 100)]
print(f"起點附近數據點數（±100m）: {len(start_area)}")

if len(start_area) > 0:
    print(f"起點附近距離範圍: {start_area['Distance'].min():.1f}m - {start_area['Distance'].max():.1f}m")
    print(f"起點附近速度範圍: {start_area['Speed'].min():.1f} - {start_area['Speed'].max():.1f} km/h")
    
    # 計算加速度
    speeds_ms = start_area["Speed"] / 3.6
    times = start_area["Time"]
    
    print(f"\n計算加速度:")
    for i in range(min(5, len(start_area))):
        idx = start_area.index[i]
        if i == 0:
            print(f"  點 {i+1}: 距離 {car_data.loc[idx, 'Distance']:.1f}m, 速度 {car_data.loc[idx, 'Speed']:.1f} km/h")
        else:
            prev_idx = start_area.index[i-1]
            speed_diff = speeds_ms.iloc[i] - speeds_ms.iloc[i-1]
            time_diff = (times.iloc[i] - times.iloc[i-1]).total_seconds()
            accel = speed_diff / time_diff if time_diff > 0 else 0
            print(f"  點 {i+1}: 距離 {car_data.loc[idx, 'Distance']:.1f}m, 速度 {car_data.loc[idx, 'Speed']:.1f} km/h, 加速度 {accel:.2f} m/s²")

# 檢查是否有 Acceleration 欄位
if "Acceleration" in car_data.columns:
    print(f"\n✅ 有 Acceleration 欄位")
else:
    print(f"\n❌ 沒有 Acceleration 欄位（需要手動計算）")

print("\n" + "="*80)
