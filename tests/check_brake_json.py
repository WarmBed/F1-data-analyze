import json

# 讀取 JSON
with open('json/brake_performance_2025_Australia_R.json', encoding='utf-8') as f:
    data = json.load(f)

print('=== JSON 數據結構分析 ===')
print(f'Success: {data.get("success")}')
print(f'Function ID: {data.get("function_id")}')
print(f'Message: {data.get("message")}')
print()

data_obj = data.get('data', {})
print('Data keys:', list(data_obj.keys()))
print()

print('Metadata:', data_obj.get('metadata'))
print()

print('Total drivers:', data_obj.get('total_drivers'))
print()

reference_zone = data_obj.get('reference_brake_zone', {})
print('Reference brake zone:', reference_zone)
print()

driver_brakes = data_obj.get('driver_brakes', [])
print(f'Driver brakes count: {len(driver_brakes)}')

if driver_brakes:
    print('\nFirst driver data:')
    print(json.dumps(driver_brakes[0], indent=2, ensure_ascii=False))
    print('\nAll keys:', list(driver_brakes[0].keys()))
else:
    print('⚠️  沒有車手數據!')
