#!/usr/bin/env python3
"""測試 Season Progress 的智慧刷新功能"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("測試 Season Progress 智慧刷新 (Function 97 - 2025)")
print("=" * 80)
print()

# 測試參數
params = {
    'function_id': '97',
    'year': 2025,
    'force_refresh': True  # 強制刷新
}

print(f'📡 調用 API: POST /api/v2/analysis/execute')
print(f'📋 參數: {json.dumps(params, indent=2)}')
print(f'🔄 force_refresh=True (強制刷新)')
print()
print('⏳ 等待響應...')
print()

try:
    start = datetime.now()
    resp = requests.post(f'{API_BASE_URL}/api/v2/analysis/execute', params=params, timeout=120)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f'✅ API 響應 (耗時: {elapsed:.2f}s)')
    print(f'📊 狀態碼: {resp.status_code}')
    print()
    
    result = resp.json()
    print(f"📦 響應內容:")
    print(f"   ├─ success: {result.get('success')}")
    print(f"   ├─ message: {result.get('message')}")
    print(f"   ├─ source: {result.get('source')}")
    print(f"   └─ execution_time: {result.get('execution_time')}")
    print()
    
    data = result.get('data', {})
    drivers = data.get('drivers', [])
    constructors = data.get('constructors', [])
    metadata = data.get('metadata', {})
    calendar = data.get('calendar', {})
    
    print(f'📊 數據統計:')
    print(f'   ├─ 車手數量: {len(drivers)}')
    print(f'   ├─ 車隊數量: {len(constructors)}')
    print(f'   ├─ 賽季年份: {metadata.get("season_year")}')
    print(f'   └─ 當前輪次: {metadata.get("resolved_round")}')
    print()
    
    if calendar:
        print(f'📅 賽程資訊:')
        print(f'   ├─ 已完成: {calendar.get("completed")}')
        print(f'   ├─ 剩餘: {calendar.get("remaining")}')
        print(f'   └─ 總計: {calendar.get("total")}')
        print()
    
    # 顯示前三名車手
    if drivers:
        print('🏆 前三名車手:')
        for i, driver_entry in enumerate(drivers[:3], 1):
            driver_info = driver_entry.get('driver', {})
            points = driver_entry.get('points', 0)
            constructors_list = driver_entry.get('constructors', [])
            team = constructors_list[0].get('name', 'Unknown') if constructors_list else 'Unknown'
            
            print(f'   {i}. {driver_info.get("full_name", "Unknown")} ({team}) - {points} pts')
        print()
    
    # 顯示前三名車隊
    if constructors:
        print('🏆 前三名車隊:')
        for i, constructor_entry in enumerate(constructors[:3], 1):
            constructor_info = constructor_entry.get('constructor', {})
            points = constructor_entry.get('points', 0)
            
            print(f'   {i}. {constructor_info.get("name", "Unknown")} - {points} pts')
        print()
    
    if result.get('source') == 'cli':
        print('✅ 智慧刷新成功：數據已通過 CLI 重新生成')
    else:
        print('✅ 測試完成：使用了緩存數據')
    
except Exception as e:
    print(f'❌ 錯誤: {e}')
    import traceback
    traceback.print_exc()
