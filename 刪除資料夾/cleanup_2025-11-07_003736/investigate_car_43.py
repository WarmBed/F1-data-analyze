#!/usr/bin/env python3
"""檢查車號 43 的原始文件內容"""
import json
from pathlib import Path

# 載入完整數據
with open('2025_f1_parts_changes_complete.json', 'r', encoding='utf-8') as f:
    all_changes = json.load(f)

# 找出所有車號 43 的記錄
car_43_records = [r for r in all_changes if r['車號'] == '43']

print("="*100)
print(f"🔍 找到 {len(car_43_records)} 筆車號 43 的記錄")
print("="*100)

# 依來源文件分組
by_file = {}
for r in car_43_records:
    filename = r['來源文件']
    if filename not in by_file:
        by_file[filename] = []
    by_file[filename].append(r)

for filename, records in by_file.items():
    print(f"\n📄 {filename}")
    print(f"   共 {len(records)} 筆記錄")
    print(f"   比賽: {records[0]['比賽']}")
    print(f"   日期: {records[0]['日期']}")
    print("\n   前 5 筆原始文本:")
    for i, r in enumerate(records[:5], 1):
        print(f"   {i}. {r['原始文本']}")

print("\n" + "="*100)
print("💡 分析結果:")
print("="*100)
print("車號 43 不在 2025 F1 官方車號列表中 (1, 4, 5, 6, 7, 10, 12, 14, 16, 18, 22, 23, 27, 30, 31, 44, 55, 63, 81, 87)")
print("\n可能原因:")
print("1. 測試車手或替補車手使用的臨時車號")
print("2. PDF 解析錯誤（例如頁碼或其他數字被誤認為車號）")
print("3. FIA 文件中的特殊情況（例如測試日或展示活動）")
print("\n建議:")
print("• 手動檢查原始 PDF 文件確認車號 43 是否真實存在")
print("• 如果是測試車手，需要更新車號映射表")
print("• 如果是解析錯誤，需要修正 PDF 解析邏輯")
print("="*100)
