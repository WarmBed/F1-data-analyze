import json

# 載入分類後資料
with open('2025_f1_parts_changes_classified.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 篩選 Williams 資料
williams = [r for r in data if r['車隊'] == 'Williams']
unclassified = [r for r in williams if r['變更類型'] == '未分類']

print(f"Williams 總數: {len(williams)}")
print(f"未分類數量: {len(unclassified)} ({100*len(unclassified)/len(williams):.1f}%)")
print(f"改善: 從 28 筆 → {len(unclassified)} 筆 (減少 {28 - len(unclassified)} 筆)")

print("\n剩餘未分類項目:")
for r in unclassified:
    print(f"  - {r['部件名稱']} ({r['賽事']})")

# 統計 Williams 分類分布
from collections import Counter
williams_types = Counter([r['變更類型'] for r in williams])
print("\nWilliams 分類分布:")
for type_name, count in williams_types.most_common():
    print(f"  {type_name}: {count} 筆 ({100*count/len(williams):.1f}%)")
