#!/usr/bin/env python3
"""測試 2025 年積分榜的 API 智慧刷新"""

import requests
import json
from datetime import datetime

print("=" * 80)
print("測試 API 智慧刷新 - 2025 賽季")
print("=" * 80)
print()

params = {
    'function_id': '97',
    'year': 2025,
    'force_refresh': False
}

print(f'📡 調用 API: POST /api/v2/analysis/execute')
print(f'📋 參數: {json.dumps(params, indent=2)}')
print()
print('⏳ 等待響應...')
print()

try:
    start = datetime.now()
    resp = requests.post('http://127.0.0.1:8000/api/v2/analysis/execute', params=params, timeout=120)
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
    
    print(f'📊 數據統計:')
    print(f'   ├─ 車手數量: {len(drivers)}')
    print(f'   ├─ 車隊數量: {len(constructors)}')
    print(f'   ├─ 賽季年份: {metadata.get("season_year")}')
    print(f'   └─ 當前輪次: {metadata.get("resolved_round")}')
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
    
    print('✅ 測試完成！')
    
except Exception as e:
    print(f'❌ 錯誤: {e}')
    import traceback
    traceback.print_exc()
