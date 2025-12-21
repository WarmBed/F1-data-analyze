#!/usr/bin/env python3
"""檢查 R21 São Paulo 的完賽狀態"""

import json

# 讀取最新的 season calendar JSON
with open('json/season_calendar_multi_year_20251111T040723Z.json', encoding='utf-8') as f:
    data = json.load(f)

# 找到 2025 年 R21
r21 = [e for e in data['data']['2025'] if e['round'] == 21][0]

print("=" * 60)
print("R21 São Paulo Grand Prix 狀態")
print("=" * 60)
print(f"✅ is_completed: {r21['is_completed']}")
print(f"📅 race_date_utc: {r21['race_date_utc']}")
print(f"⏰ days_until_race: {r21.get('days_until_race')}")
print("=" * 60)

if r21['is_completed']:
    print("✅ 狀態正確！R21 已標記為完賽")
else:
    print("❌ 狀態錯誤！R21 應該已完賽但標記為未完賽")
