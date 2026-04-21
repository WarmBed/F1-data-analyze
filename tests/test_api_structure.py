"""
檢查 API 實際返回的數據結構
"""
import requests
import json

url = 'http://localhost:8000/api/v2/analysis/execute'
params = {
    'function_id': 2,
    'year': 2024,
    'race': 'Japan',
    'session': 'R'
}

print("正在請求 API...")
response = requests.post(url, params=params, timeout=60)

if response.status_code == 200:
    data = response.json()
    
    print("\n=== API 返回結構 ===")
    print(f"Top-level keys: {list(data.keys())}")
    
    if 'data' in data:
        print(f"\ndata 類型: {type(data['data'])}")
        if isinstance(data['data'], dict):
            print(f"data keys: {list(data['data'].keys())}")
        elif isinstance(data['data'], str):
            print(f"data 是字串，長度: {len(data['data'])}")
            print(f"前 500 字元:\n{data['data'][:500]}")
    
    # 保存完整數據到檔案
    output_file = "test_api_track_position_response.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 完整數據已保存到: {output_file}")
    print(f"檔案大小: {len(json.dumps(data))} bytes")
else:
    print(f"❌ API 請求失敗: {response.status_code}")
