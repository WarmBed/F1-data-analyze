import json

# 載入 JSON
with open('json/comparison_telemetry_VER_VER_2025_Japan_R_Lap1_Lap1.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# 模擬處理
telemetry_type = 'speed'
data_field = 'Speed'

results = raw_data['results']
telemetry_comp = results['telemetry_comparison']
telemetry_raw = telemetry_comp[data_field]

print('=== 原始 JSON 結構 ===')
print(f'telemetry_raw keys: {list(telemetry_raw.keys())}')
print(f'distance points: {len(telemetry_raw.get("distance", []))}')
print(f'driver1_data points: {len(telemetry_raw.get("driver1_data", []))}')
print(f'driver2_data points: {len(telemetry_raw.get("driver2_data", []))}')

# 處理後的數據結構
data_key = f'{telemetry_type}_data'
processed_data = {
    data_key: {
        'distance': telemetry_raw.get('distance', []),
        f'driver1_{telemetry_type}': telemetry_raw.get('driver1_data', []),
        f'driver2_{telemetry_type}': telemetry_raw.get('driver2_data', [])
    }
}

print('\n=== 處理後的數據結構 ===')
print(f'data_key: {data_key}')
print(f'Keys in {data_key}: {list(processed_data[data_key].keys())}')
print(f'distance points: {len(processed_data[data_key]["distance"])}')
print(f'driver1_speed points: {len(processed_data[data_key]["driver1_speed"])}')
print(f'driver2_speed points: {len(processed_data[data_key]["driver2_speed"])}')

# 驗證數據提取
speed_data = processed_data.get('speed_data', {})
print('\n=== GUI 預期的數據提取 ===')
print(f'speed_data keys: {list(speed_data.keys())}')
distance = speed_data.get('distance', [])
driver1_speed = speed_data.get('driver1_speed', [])
driver2_speed = speed_data.get('driver2_speed', [])
print(f'distance: {len(distance)} points')
print(f'driver1_speed: {len(driver1_speed)} points')
print(f'driver2_speed: {len(driver2_speed)} points')

if len(distance) > 0 and len(driver1_speed) > 0:
    print('\n✅ 數據處理正確！')
    print(f'首5個距離值: {distance[:5]}')
    print(f'首5個速度值: {driver1_speed[:5]}')
else:
    print('\n❌ 數據處理有問題！')
