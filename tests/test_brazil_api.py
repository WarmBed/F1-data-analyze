"""測試 Brazil 賽事 API 返回的 position_changes 數據"""
import requests
import json

url = "https://api.f1telemetrystationpro.org/api/v2/analysis/execute"
params = {
    "function_id": "100",
    "year": "2025",
    "race": "Brazil",
    "session": "R",
    "force_refresh": "true"  # ✅ 強制刷新
}

print(f"正在請求 Function 100 API (Brazil)...")
response = requests.post(url, params=params)  # 改用 POST
print(f"狀態碼: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data.get('success')}")
    print(f"Message: {data.get('message')}")
    
    # 提取 yearly_summary
    nested_data = data.get('data', {})
    inner_data = nested_data.get('data', {})
    yearly_summary = inner_data.get('yearly_summary', {})
    
    print(f"\n=== yearly_summary 所有年份 ===")
    for year in ['2022', '2023', '2024', '2025']:
        if year in yearly_summary:
            year_data = yearly_summary[year]
            position_changes = year_data.get('position_changes', 'KEY_NOT_FOUND')
            print(f"{year}: position_changes = {position_changes}")
        else:
            print(f"{year}: 年份不存在於 yearly_summary")
    
    print(f"\n=== 2025 完整數據 ===")
    if '2025' in yearly_summary:
        print(json.dumps(yearly_summary['2025'], indent=2, ensure_ascii=False))
    else:
        print("2025 年份不存在！")
else:
    print(f"API 請求失敗: {response.status_code}")
    print(response.text)
