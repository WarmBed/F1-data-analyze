#!/usr/bin/env python3
"""保存完整的 API 響應以供檢查"""

import requests
import json

API_BASE = "https://localhost:8000"
endpoint = f"{API_BASE}/api/v2/analysis/execute"

query_params = {
    "function_id": 100,
    "race": "Abu Dhabi",
    "year": 2025,
    "session": "R"
}

print('調用 API...')

try:
    response = requests.post(
        endpoint,
        params=query_params,
        timeout=60,
        headers={"Accept": "application/json"}
    )
    
    if response.status_code == 200:
        payload = response.json()
        
        # 保存完整響應
        output_file = 'test_api_track_position_response.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        print(f'✅ API 響應已保存到: {output_file}')
        
        # 提取 yearly_summary
        data = payload.get('data', {}).get('data', {})
        yearly_summary = data.get('yearly_summary', {})
        
        print(f'\n📊 yearly_summary 包含的年份: {sorted(yearly_summary.keys())}')
        
        for year in sorted(yearly_summary.keys()):
            year_data = yearly_summary[year]
            pos_changes = year_data.get('position_changes', 0)
            print(f'   {year}: {pos_changes} 次名次變更')
        
        # 檢查 2025
        if '2025' not in yearly_summary:
            print(f'\n❌ API 沒有返回 2025 年的數據')
            print(f'📝 本地 JSON 有 2025 數據，但 API 沒有')
        
    else:
        print(f'❌ HTTP {response.status_code}')
        print(response.text[:500])
        
except Exception as e:
    print(f'❌ 錯誤: {e}')
    import traceback
    traceback.print_exc()
