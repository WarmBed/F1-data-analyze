#!/usr/bin/env python3
"""測試本地 API vs 遠程 API"""

import requests
import json

print('=== 對比本地 API vs 遠程 API ===\n')

params = {
    "function_id": 100,
    "race": "Abu Dhabi",
    "year": 2025,
    "session": "R"
}

# 測試 1: 本地 API
print('📍 測試 1: 本地 API (localhost:8000)')
print('=' * 60)
try:
    local_response = requests.post(
        "http://localhost:8000/api/v2/analysis/execute",
        params=params,
        timeout=30
    )
    
    if local_response.status_code == 200:
        local_data = local_response.json()
        local_timestamp = local_data.get('data', {}).get('timestamp')
        local_years = sorted(local_data.get('data', {}).get('data', {}).get('yearly_summary', {}).keys())
        local_source = local_data.get('source', 'unknown')
        
        print(f'✅ 本地 API 調用成功')
        print(f'   source: {local_source}')
        print(f'   timestamp: {local_timestamp}')
        print(f'   包含的年份: {local_years}')
        
        if '2025' in local_years:
            pos_changes = local_data['data']['data']['yearly_summary']['2025'].get('position_changes')
            print(f'   ✅ 包含 2025 數據: position_changes = {pos_changes}')
        else:
            print(f'   ❌ 缺少 2025 數據')
    else:
        print(f'❌ HTTP {local_response.status_code}')
except Exception as e:
    print(f'❌ 本地 API 連接失敗: {e}')

print('\n')

# 測試 2: 遠程 API
print('🌐 測試 2: 遠程 API (api.f1telemetrystationpro.org)')
print('=' * 60)
try:
    remote_response = requests.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        params=params,
        timeout=30
    )
    
    if remote_response.status_code == 200:
        remote_data = remote_response.json()
        remote_timestamp = remote_data.get('data', {}).get('timestamp')
        remote_years = sorted(remote_data.get('data', {}).get('data', {}).get('yearly_summary', {}).keys())
        remote_source = remote_data.get('source', 'unknown')
        
        print(f'✅ 遠程 API 調用成功')
        print(f'   source: {remote_source}')
        print(f'   timestamp: {remote_timestamp}')
        print(f'   包含的年份: {remote_years}')
        
        if '2025' in remote_years:
            pos_changes = remote_data['data']['data']['yearly_summary']['2025'].get('position_changes')
            print(f'   ✅ 包含 2025 數據: position_changes = {pos_changes}')
        else:
            print(f'   ❌ 缺少 2025 數據')
    else:
        print(f'❌ HTTP {remote_response.status_code}')
except Exception as e:
    print(f'❌ 遠程 API 連接失敗: {e}')

print('\n')

# 測試 3: 本地 JSON 檔案
print('📁 測試 3: 本地 JSON 檔案')
print('=' * 60)
try:
    with open('json/historical_flags_Abu_Dhabi_2022-2025.json', 'r', encoding='utf-8') as f:
        local_json = json.load(f)
    
    json_timestamp = local_json.get('timestamp')
    json_years = sorted(local_json.get('data', {}).get('yearly_summary', {}).keys())
    
    print(f'✅ 本地 JSON 讀取成功')
    print(f'   timestamp: {json_timestamp}')
    print(f'   包含的年份: {json_years}')
    
    if '2025' in json_years:
        pos_changes = local_json['data']['yearly_summary']['2025'].get('position_changes')
        print(f'   ✅ 包含 2025 數據: position_changes = {pos_changes}')
    else:
        print(f'   ❌ 缺少 2025 數據')
except Exception as e:
    print(f'❌ 本地 JSON 讀取失敗: {e}')

print('\n')
print('=' * 60)
print('🎯 結論:')
print('=' * 60)
print('檢查上面的輸出，對比三個數據源的差異')
