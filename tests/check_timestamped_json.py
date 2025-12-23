#!/usr/bin/env python3
"""檢查帶時間戳的 JSON 檔案結構"""

import json

print("=" * 80)
print("檢查帶時間戳的 JSON 檔案")
print("=" * 80)

# 最新的檔案
json_file = "json/fia_parts_analysis_v2_2025_20251108T123525Z.json"
print(f"\n📄 讀取檔案: {json_file}")

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("\n1️⃣ JSON 檔案的頂層鍵:")
for key in data.keys():
    print(f"   - {key}")

# 檢查 records
records = data.get('records', [])
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
        'main_cat', 'sub_cat', 'change_type',
        '主分類', '子分類'  # 可能的中文欄位名
    ]
    for field in key_fields:
        exists = field in first_record
        status = '✅ 存在' if exists else '❌ 不存在'
        if exists:
            print(f"   - {field}: {status} = {first_record[field]}")
        else:
            print(f"   - {field}: {status}")

print("\n5️⃣ 檢查 metadata 中的分類資訊:")
metadata = data.get('metadata', {})
for key in metadata.keys():
    print(f"   - {key}: {metadata[key]}")

print("\n6️⃣ 完整記錄範例（前 3 筆）:")
for i, record in enumerate(records[:3], 1):
    print(f"\n   記錄 {i}:")
    print(f"      車隊: {record.get('車隊')}")
    print(f"      部件: {record.get('部件')}")
    print(f"      變更類型: {record.get('變更類型')}")
    print(f"      main_category: {record.get('main_category', '❌ 不存在')}")
    print(f"      sub_category: {record.get('sub_category', '❌ 不存在')}")
