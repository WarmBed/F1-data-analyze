#!/usr/bin/env python3
"""檢查 FIA Parts Analysis JSON 檔案結構"""

import json

print("=" * 80)
print("檢查本地 JSON 檔案結構")
print("=" * 80)

# 讀取本地 JSON
json_file = "json/fia_parts_analysis_v2_2025.json"
print(f"\n📄 讀取檔案: {json_file}")

with open(json_file, 'r', encoding='utf-8') as f:
    local_data = json.load(f)

print("\n1️⃣ JSON 檔案的頂層鍵:")
for key in local_data.keys():
    print(f"   - {key}")

# 檢查 records
records = local_data.get('records', [])
print(f"\n2️⃣ records 數量: {len(records)}")

if records:
    print("\n3️⃣ 第一筆記錄的所有欄位:")
    first_record = records[0]
    for key in first_record.keys():
        value = first_record[key]
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + "..."
        print(f"   - {key}: {value}")
    
    print("\n4️⃣ 檢查關鍵欄位是否存在:")
    key_fields = [
        'main_category', 'sub_category', '變更類型',
        'main_cat', 'sub_cat', 'change_type'
    ]
    for field in key_fields:
        exists = field in first_record
        print(f"   - {field}: {'✅ 存在' if exists else '❌ 不存在'}")

print("\n" + "=" * 80)
print("檢查 API 響應結構")
print("=" * 80)

import requests

print("\n📡 調用 API...")
response = requests.post(
    "https://api.f1telemetrystationpro.org/api/v2/analysis/execute?function_id=29&year=2025&exclude_noise=True"
)
api_data = response.json()

print("\n5️⃣ API 響應的頂層鍵:")
for key in api_data.keys():
    print(f"   - {key}")

print("\n6️⃣ API data 的鍵:")
for key in api_data['data'].keys():
    print(f"   - {key}")

api_records = api_data['data'].get('records', [])
print(f"\n7️⃣ API records 數量: {len(api_records)}")

if api_records:
    print("\n8️⃣ API 第一筆記錄的所有欄位:")
    api_first = api_records[0]
    for key in api_first.keys():
        value = api_first[key]
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + "..."
        print(f"   - {key}: {value}")
    
    print("\n9️⃣ API 檢查關鍵欄位是否存在:")
    for field in key_fields:
        exists = field in api_first
        print(f"   - {field}: {'✅ 存在' if exists else '❌ 不存在'}")

print("\n" + "=" * 80)
print("🔍 結論")
print("=" * 80)

# 比較欄位
local_fields = set(first_record.keys())
api_fields = set(api_first.keys())

print("\n🔹 本地 JSON 獨有的欄位:")
for field in local_fields - api_fields:
    print(f"   - {field}")

print("\n🔹 API 獨有的欄位:")
for field in api_fields - local_fields:
    print(f"   - {field}")

print("\n🔹 共同欄位數量:")
print(f"   - 本地: {len(local_fields)}")
print(f"   - API: {len(api_fields)}")
print(f"   - 共同: {len(local_fields & api_fields)}")
