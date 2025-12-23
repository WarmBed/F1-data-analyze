#!/usr/bin/env python3
"""實時測試 API - 不使用緩存文件"""

import requests
import json
from datetime import datetime

API_BASE = "https://localhost:8000"
endpoint = f"{API_BASE}/api/v2/analysis/execute"

query_params = {
    "function_id": 100,
    "race": "Abu Dhabi",
    "year": 2025,
    "session": "R",
    "force_refresh": False  # 不強制刷新，看緩存
}

print(f'=== 實時 API 測試 ({datetime.now()}) ===\n')
print(f'端點: {endpoint}')
print(f'參數: {json.dumps(query_params, indent=2)}\n')

try:
    response = requests.post(
        endpoint,
        params=query_params,
        timeout=60,
        headers={"Accept": "application/json"}
    )
    
    if response.status_code == 200:
        payload = response.json()
        
        # 提取時間戳
        outer_timestamp = payload.get('data', {}).get('timestamp')
        inner_timestamp = payload.get('data', {}).get('data', {}).get('metadata', {}).get('generated_at')
        
        print(f'✅ API 調用成功')
        print(f'\n📅 時間戳信息:')
        print(f'   外層 timestamp: {outer_timestamp}')
        print(f'   內層 generated_at: {inner_timestamp}')
        
        # 提取 yearly_summary
        data = payload.get('data', {}).get('data', {})
        yearly_summary = data.get('yearly_summary', {})
        
        print(f'\n📊 yearly_summary:')
        print(f'   包含的年份: {sorted(yearly_summary.keys())}')
        
        for year in ['2022', '2023', '2024', '2025']:
            if year in yearly_summary:
                pos_changes = yearly_summary[year].get('position_changes', 0)
                print(f'   {year}: position_changes = {pos_changes}')
            else:
                print(f'   {year}: ❌ 不存在')
        
        # 對比本地 JSON
        print(f'\n🔍 對比本地 JSON:')
        with open('json/historical_flags_Abu_Dhabi_2022-2025.json', 'r', encoding='utf-8') as f:
            local_json = json.load(f)
        
        local_timestamp = local_json.get('timestamp')
        local_years = sorted(local_json.get('data', {}).get('yearly_summary', {}).keys())
        
        print(f'   本地 timestamp: {local_timestamp}')
        print(f'   本地年份: {local_years}')
        
        # 判斷
        if outer_timestamp == local_timestamp:
            print(f'\n✅ API 返回的是最新的 JSON（時間戳一致）')
        else:
            print(f'\n❌ API 返回的是舊的 JSON')
            print(f'   API 時間戳: {outer_timestamp}')
            print(f'   本地時間戳: {local_timestamp}')
            
        if '2025' in yearly_summary:
            print(f'\n✅ API 包含 2025 數據')
        else:
            print(f'\n❌ API 缺少 2025 數據（但本地 JSON 有）')
    else:
        print(f'❌ HTTP {response.status_code}')
        
except Exception as e:
    print(f'❌ 錯誤: {e}')
    import traceback
    traceback.print_exc()
