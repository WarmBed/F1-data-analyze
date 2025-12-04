import json

# 直接模擬 get_track_status_at_time 邏輯
with open('json/LiveF1/2025/Qatar_Race/TrackStatus.json', 'r') as f:
    data = json.load(f)

records = data['records']
print(f'Records: {len(records)}')
for r in records:
    print(f"  {r['timestamp']} -> Status {r['data']['Status']}")

def time_to_seconds(time_str):
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0

# 測試查詢
test_time = '01:09:43.000'
target_seconds = time_to_seconds(test_time)
print(f'\nQuery: {test_time} = {target_seconds} seconds')

current_status = '1'
for record in records:
    ts = record.get('timestamp', '')
    ts_seconds = time_to_seconds(ts)
    if ts_seconds <= target_seconds:
        status = record.get('data', {}).get('Status')
        if status:
            current_status = str(status)
            print(f'  Found: {ts} ({ts_seconds}s) -> Status {status}')
    elif ts_seconds > target_seconds:
        break

print(f'\nResult: Status = {current_status}')
