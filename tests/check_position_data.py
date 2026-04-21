import requests
import json

url = "http://localhost:8000/api/v2/analysis/execute"
params = {"function_id": "100", "year": "2025", "race": "Brazil", "session": "R"}

print("正在請求 API...")
response = requests.post(url, params=params, timeout=60)
data = response.json()["data"]["data"]

yearly_summary = data.get("yearly_summary", {})
print("\n=== yearly_summary 結構 ===")
for year, year_data in list(yearly_summary.items())[:2]:
    print(f"\n{year}:")
    print(f"  Keys: {list(year_data.keys())}")
    print(f"  Values:")
    for key, value in year_data.items():
        print(f"    {key}: {value}")
