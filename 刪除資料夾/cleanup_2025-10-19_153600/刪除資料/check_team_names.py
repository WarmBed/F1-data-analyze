#!/usr/bin/env python3
"""檢查 F48 JSON 中的車隊名稱"""

import json

# 讀取 JSON
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取車隊名稱
driver_speeds = data['data']['driver_speeds']

print("=== 車隊名稱清單 ===")
teams = set()
for driver in driver_speeds:
    team = driver['team']
    teams.add(team)
    print(f"{driver['driver']:4s} → {team}")

print("\n=== 不重複車隊名稱 ===")
for team in sorted(teams):
    print(f"  - '{team}'")

print(f"\n總共 {len(teams)} 支車隊")
