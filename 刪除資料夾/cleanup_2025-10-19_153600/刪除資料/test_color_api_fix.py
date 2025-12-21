#!/usr/bin/env python3
"""測試顏色 API 嵌套數據結構修復"""

import requests

# 調用 API
response = requests.post(
    'https://api.f1telemetrystationpro.org/api/v2/analysis/execute',
    params={'function_id': 98, 'year': 2025},
    timeout=30
)

payload = response.json()

# 舊邏輯（錯誤）
data_old = payload.get('data', {})
teams_old = data_old.get('teams', {})
drivers_old = data_old.get('drivers', {})

# 新邏輯（修復）
outer_data = payload.get('data', {})
inner_data = outer_data.get('data', outer_data)
teams_new = inner_data.get('teams', {})
drivers_new = inner_data.get('drivers', {})

print("=== 舊邏輯（錯誤）===")
print(f"Teams: {len(teams_old)}")
print(f"Drivers: {len(drivers_old)}")

print("\n=== 新邏輯（修復）===")
print(f"Teams: {len(teams_new)}")
print(f"Drivers: {len(drivers_new)}")
print(f"Sample team: {list(teams_new.keys())[0] if teams_new else 'N/A'}")
print(f"Sample driver: {list(drivers_new.keys())[0] if drivers_new else 'N/A'}")

if teams_new and drivers_new:
    print("\n✅ 修復成功！API 現在可以正確提取 teams 和 drivers 數據")
else:
    print("\n❌ 修復失敗，數據仍然為空")
