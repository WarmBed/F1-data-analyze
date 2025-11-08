import json

json_file = "json/all_drivers_straight_line_speed_2018_Great Britain_FP3.json"
with open(json_file, 'r', encoding='utf-8') as f:
    response = json.load(f)

# 正確的結構：response.data.driver_speeds
data = response.get('data', {})

print(f"✅ JSON 解析成功！")
print(f"成功狀態: {response.get('success')}")
print(f"車手數量: {data.get('metadata', {}).get('drivers_total')}")
print(f"賽事資訊: {data.get('metadata', {}).get('year')} {data.get('metadata', {}).get('race')} {data.get('metadata', {}).get('session')}")
print(f"最速車手: {data.get('summary', {}).get('fastest_driver')} - {data.get('summary', {}).get('fastest_speed_kmh')} km/h")
if data.get('driver_speeds'):
    print(f"第一位車手: {data['driver_speeds'][0]['driver']} - {data['driver_speeds'][0].get('max_speed_kmh', 'N/A')} km/h")
