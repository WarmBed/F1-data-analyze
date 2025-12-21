#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""檢查 Mexico City 數據"""

import json

# 載入數據
with open('2025_f1_parts_changes_v2_classified_with_categories.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 篩選 Mexico City
mexico_records = [r for r in data if r.get('比賽') == 'Mexico City']

print(f"Mexico City 總記錄數: {len(mexico_records)}\n")
print("=" * 80)

# 檢查前 5 筆
for i, record in enumerate(mexico_records[:5], 1):
    print(f"\n記錄 {i}:")
    print(f"  車隊: {record.get('車隊', 'N/A')}")
    print(f"  車手: {record.get('車手', 'N/A')}")
    print(f"  部件: {record.get('部件', 'N/A')}")
    print(f"  變更類型: {record.get('變更類型', 'N/A')}")
    print(f"  類型說明: {record.get('類型說明', 'N/A')}")
    print(f"  日期: {record.get('日期', 'N/A')}")
    print(f"  主分類: {record.get('主分類', 'N/A')}")
    print(f"  子分類: {record.get('子分類', 'N/A')}")

# 統計有 Description 和 Date 的記錄
has_description = sum(1 for r in mexico_records if r.get('類型說明'))
has_date = sum(1 for r in mexico_records if r.get('日期'))

print("\n" + "=" * 80)
print(f"\n統計:")
print(f"  有類型說明的記錄: {has_description}/{len(mexico_records)} ({has_description/len(mexico_records)*100:.1f}%)")
print(f"  有日期的記錄: {has_date}/{len(mexico_records)} ({has_date/len(mexico_records)*100:.1f}%)")
