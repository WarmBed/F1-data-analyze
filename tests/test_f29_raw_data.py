#!/usr/bin/env python3
"""測試 Function 29 PDF 原始資料"""
import json

# 讀取 JSON
with open('json/fia_parts_analysis_2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print(" Function 29 - PDF 原始資料測試")
print("=" * 80)

# 檢查結構
print(f"\n✅ 成功載入 JSON")
print(f"總記錄數: {len(data.get('records', []))}")
print(f"Data Version: {data.get('data_version', 'N/A')}")
print(f"Note: {data.get('metadata', {}).get('note', 'N/A')}")

# 檢查前 10 筆記錄
print(f"\n" + "=" * 80)
print(" 前 10 筆記錄檢查")
print("=" * 80)

for i, record in enumerate(data['records'][:10], 1):
    print(f"\n{i}. 賽事: {record.get('賽事', '')}")
    print(f"   賽事日期: {record.get('賽事日期', '❌ 無日期')}")
    print(f"   車隊: {record.get('車隊', '')}")
    print(f"   車手: {record.get('車手', '')}")
    print(f"   車號: {record.get('車號', '')}")
    print(f"   部件: {record.get('部件', '')[:50]}...")  # 只顯示前 50 字元

# 檢查欄位名稱
print(f"\n" + "=" * 80)
print(" 記錄欄位檢查")
print("=" * 80)
sample_record = data['records'][0]
print(f"欄位列表: {list(sample_record.keys())}")

# ❌ 檢查是否有分類欄位（應該不存在）
has_classification = any(key in sample_record for key in ['變更類型', '類型說明', '主分類', '子分類', '分類信心度'])
if has_classification:
    print(f"\n❌ 錯誤：發現分類欄位！")
    print(f"   包含: {[k for k in ['變更類型', '類型說明', '主分類', '子分類', '分類信心度'] if k in sample_record]}")
else:
    print(f"\n✅ 正確：無分類欄位，只有 PDF 原始資料")

# 檢查日期統計
print(f"\n" + "=" * 80)
print(" 日期統計")
print("=" * 80)
total = len(data['records'])
with_date = sum(1 for r in data['records'] if r.get('賽事日期'))
without_date = total - with_date
print(f"有日期: {with_date} 筆 ({with_date/total*100:.1f}%)")
print(f"無日期: {without_date} 筆 ({without_date/total*100:.1f}%)")

# 顯示沒有日期的賽事
races_without_date = set(r.get('賽事', '') for r in data['records'] if not r.get('賽事日期'))
if races_without_date:
    print(f"\n缺少日期的賽事: {', '.join(sorted(races_without_date))}")

print(f"\n" + "=" * 80)
print(" 測試完成！")
print("=" * 80)
