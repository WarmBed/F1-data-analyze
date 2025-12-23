import json

# 讀取 JSON 檔案
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    response = json.load(f)

# 獲取參考範圍
data = response.get('data', {})
ref = data.get('reference_segment', {})

print('=== 參考範圍設定 ===')
print(f'Reference driver: {ref.get("reference_driver")}')
print(f'Distance range: {ref.get("segment_distance_start")} → {ref.get("segment_distance_end")} m')
print(f'Unified speed range: {ref.get("unified_start_speed")} → {ref.get("unified_end_speed")} km/h')
print()

# 找出 HAM 的數據
drivers = data.get('driver_speeds', [])
ham_data = next((d for d in drivers if d['driver'] == 'HAM'), None)

if ham_data:
    print('=== HAM 的賽道段加速度數據 ===')
    print(f'起始速度: {ham_data.get("segment_start_speed_kmh")} km/h')
    print(f'結束速度: {ham_data.get("segment_end_speed_kmh")} km/h')
    print(f'速度增益: {ham_data.get("segment_speed_gain_kmh")} km/h')
    print(f'加速時間: {ham_data.get("segment_accel_time_seconds")} 秒')
    print(f'加速距離: {ham_data.get("segment_accel_distance_meters")} m')
    print(f'平均加速度: {ham_data.get("segment_avg_acceleration_ms2")} m/s²')
    print()
    print(f'測量位置: {ham_data.get("distance_m")} m')
    print(f'最高速度: {ham_data.get("max_speed_kmh")} km/h')
