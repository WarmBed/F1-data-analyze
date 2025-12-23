import json

with open('json/fia_parts_analysis_v2_2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

records = data.get('records', [])

print('=' * 120)
print('前 10 筆記錄的完整分類資訊')
print('=' * 120)
for i, r in enumerate(records[:10], 1):
    part = r.get('部件', '')[:35]
    main_cat = r.get('主分類', 'N/A')
    sub_cat = r.get('子分類', 'N/A')
    change_type = r.get('變更類型', 'N/A')
    print(f"{i:2}. {part:<35} | {main_cat:<18} | {sub_cat:<25} | {change_type}")

# 統計分析
from collections import Counter
main_cats = Counter([r.get('主分類') for r in records])
sub_cats = Counter([r.get('子分類') for r in records])

print('\n' + '=' * 120)
print('主分類統計')
print('=' * 120)
for cat, count in main_cats.most_common():
    pct = count / len(records) * 100
    print(f"  {cat:<25} {count:>4} ({pct:>5.1f}%)")

print('\n' + '=' * 120)
print('子分類統計 (Top 15)')
print('=' * 120)
for cat, count in sub_cats.most_common(15):
    pct = count / len(records) * 100
    print(f"  {cat:<30} {count:>4} ({pct:>5.1f}%)")
