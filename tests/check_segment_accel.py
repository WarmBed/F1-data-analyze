import json

# 讀取 JSON 檔案
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8', errors='replace') as f:
    response = json.load(f)

# 獲取實際數據
data = response.get('data', {})
drivers = data.get('driver_speeds', [])
print(f'車手數量: {len(drivers)}')
print()

if drivers:
    first = drivers[0]
    print(f'第一位車手: {first.get("driver")}')
    print(f'max_speed_kmh: {first.get("max_speed_kmh")}')
    print()
    
    # 檢查新欄位
    print('=== 新增的賽道段加速度欄位 ===')
    print(f'segment_accel_time_seconds: {first.get("segment_accel_time_seconds")}')
    print(f'segment_accel_distance_meters: {first.get("segment_accel_distance_meters")}')
    print(f'segment_avg_acceleration_ms2: {first.get("segment_avg_acceleration_ms2")}')
    print(f'segment_start_speed_kmh: {first.get("segment_start_speed_kmh")}')
    print(f'segment_end_speed_kmh: {first.get("segment_end_speed_kmh")}')
    print(f'segment_speed_gain_kmh: {first.get("segment_speed_gain_kmh")}')
    print()
    
    # 檢查舊的加速度欄位（速度範圍基礎）
    print('=== 舊的速度範圍加速度欄位 ===')
    print(f'accel_time_seconds: {first.get("accel_time_seconds")}')
    print(f'avg_acceleration_ms2: {first.get("avg_acceleration_ms2")}')
    
    # 顯示所有車手的segment加速度
    print('\n=== 所有車手賽道段加速度 ===')
    print(f"{'車手':4s} {'加速度':>8s} {'時間':>8s} {'速度增益':>10s}")
    print("-" * 36)
    for driver in drivers:  # 顯示所有車手
        print(f"{driver['driver']:3s}  {driver.get('segment_avg_acceleration_ms2', 0):6.2f} m/s² "
              f"{driver.get('segment_accel_time_seconds', 0):6.2f} s  "
              f"{driver.get('segment_speed_gain_kmh', 0):6.1f} km/h")

