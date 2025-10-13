#!/usr/bin/env python3
"""測試 API 返回的數據結構"""

import requests
import json

response = requests.post(
    "http://localhost:8000/api/v2/analysis/execute",
    params={
        "function_id": 96,
        "year": 2025,
        "race": "Singapore Grand Prix",
        "session": "R"
    }
)

print("=" * 60)
print("API 返回結構分析")
print("=" * 60)

data = response.json()

print(f"\n1. HTTP 狀態碼: {response.status_code}")
print(f"\n2. 頂層鍵: {list(data.keys())}")
print(f"\n3. success: {data.get('success')}")
print(f"\n4. data 類型: {type(data.get('data'))}")

if isinstance(data.get('data'), dict):
    data_obj = data['data']
    print(f"\n5. data 的鍵: {list(data_obj.keys())}")
    
    # 檢查是否是雙層嵌套（CLI JSON 被包在 data 裡）
    if 'data' in data_obj:
        print(f"\n⚠️ 發現雙層嵌套！data.data 的鍵: {list(data_obj['data'].keys())}")
    
    # 檢查 forecast 位置
    if 'forecast' in data_obj:
        print(f"\n✅ forecast 在 data 層級")
        print(f"   forecast.days 數量: {len(data_obj['forecast'].get('days', []))}")
    elif 'data' in data_obj and 'forecast' in data_obj['data']:
        print(f"\n✅ forecast 在 data.data 層級（雙層嵌套）")
        print(f"   forecast.days 數量: {len(data_obj['data']['forecast'].get('days', []))}")
    else:
        print(f"\n❌ 找不到 forecast！")

print("\n" + "=" * 60)
