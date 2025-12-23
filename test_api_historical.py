import requests
import json

url = 'https://localhost:8000/api/v2/analysis/execute'
payload = {
    'function_id': 100,
    'year': 2025,
    'race': 'Abu Dhabi',
    'session': 'R'
}

print(f'請求 API: {url}')
print(f'參數: {payload}')

try:
    resp = requests.post(url, json=payload, timeout=30)
    print(f'\nHTTP Status: {resp.status_code}')
    
    data = resp.json()
    print(f'Response top-level keys: {list(data.keys())}')
    print(f'Success: {data.get("success")}')
    print(f'Has data field: {"data" in data}')
    
    if 'data' in data:
        data_dict = data['data']
        print(f'\n[data] keys (前 10 個): {list(data_dict.keys())[:10]}')
        
        # 檢查關鍵欄位
        print(f'\nyearly_summary 存在: {"yearly_summary" in data_dict}')
        print(f'corner_analysis 存在: {"corner_analysis" in data_dict}')
        print(f'official_corners 存在: {"official_corners" in data_dict}')
        print(f'sector_boundaries 存在: {"sector_boundaries" in data_dict}')
        print(f'detailed_position_records 存在: {"detailed_position_records" in data_dict}')
        
        if 'detailed_position_records' in data_dict:
            print(f'\nposition_records 長度: {len(data_dict["detailed_position_records"])}')
            
except Exception as e:
    print(f'錯誤: {e}')
    import traceback
    traceback.print_exc()
