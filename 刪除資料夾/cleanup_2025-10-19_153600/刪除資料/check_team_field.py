"""檢查 team 欄位"""
import json

with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['data']['driver_speeds'][:5]

print("前 5 名車手的 team 欄位：")
for d in drivers:
    print(f"{d['driver']:3} -> {d['team']}")
