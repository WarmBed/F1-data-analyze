#!/usr/bin/env python3
"""直接測試 API 返回的顏色數據結構"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests

print("=== 直接測試 API Function 98 ===\n")

# 調用 API
url = "http://localhost:8000/api/v2/analysis/execute"
params = {"function_id": 98, "year": 2025}

print(f"1. 調用 API: {url}")
print(f"   參數: {params}")

try:
    response = requests.post(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    
    print(f"\n2. API 回應狀態: success={payload.get('success')}")
    
    # 解析嵌套結構
    outer_data = payload.get("data", {})
    inner_data = outer_data.get("data", outer_data)
    drivers = inner_data.get("drivers", {})
    teams = inner_data.get("teams", {})
    
    print(f"   teams 數量: {len(teams)}")
    print(f"   drivers 數量: {len(drivers)}")
    
    print("\n3. 車隊列表:")
    for slug, info in teams.items():
        print(f"   {slug}: {info.get('team_name')} - {info.get('selected_hex')}")
    
    print("\n4. 關鍵車手檢查:")
    print("-" * 60)
    key_drivers = ['HAM', 'SAI', 'BEA', 'ANT', 'TSU', 'LAW', 'VER', 'NOR']
    for code in key_drivers:
        info = drivers.get(code, {})
        if info:
            print(f"   {code}: team={info.get('team_name')}, hex={info.get('hex')}, team_slug={info.get('team_slug')}")
        else:
            print(f"   {code}: NOT FOUND!")
    
    print("\n5. 完整車手-車隊映射:")
    print("-" * 60)
    team_drivers = {}
    for code, info in drivers.items():
        team = info.get('team_name', 'Unknown')
        if team not in team_drivers:
            team_drivers[team] = []
        team_drivers[team].append((code, info.get('hex')))
    
    for team, members in sorted(team_drivers.items()):
        drivers_str = ", ".join([f"{c}({h})" for c, h in members])
        print(f"   {team}: {drivers_str}")

except Exception as e:
    print(f"錯誤: {e}")
    import traceback
    traceback.print_exc()
