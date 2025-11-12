import requests
import json

url = "https://api.f1telemetrystationpro.org/api/v2/analysis/execute"
params = {
    "function_id": "100",
    "year": "2025",
    "race": "Brazil",
    "session": "R"
}

print("正在請求 API...")
response = requests.post(url, params=params, timeout=60)
print(f"狀態碼: {response.status_code}\n")

data = response.json()
print("=== Top Level ===")
print(f"Keys: {list(data.keys())}")
print(f"success: {data.get('success')}")

print("\n=== data (Level 1) ===")
level1 = data.get("data")
print(f"Type: {type(level1)}")
if isinstance(level1, dict):
    print(f"Keys: {list(level1.keys())}")
    
    print("\n=== data.data (Level 2) ===")
    level2 = level1.get("data")
    print(f"Type: {type(level2)}")
    if isinstance(level2, dict):
        print(f"Keys: {list(level2.keys())}")
        print(f"\nHas 'yearly_summary': {'yearly_summary' in level2}")
        print(f"Has 'corner_analysis': {'corner_analysis' in level2}")
        
        print("\n=== 正確的數據位置 ===")
        print(f"payload.get('data').get('data') 包含:")
        for key in list(level2.keys())[:8]:
            print(f"  - {key}")
