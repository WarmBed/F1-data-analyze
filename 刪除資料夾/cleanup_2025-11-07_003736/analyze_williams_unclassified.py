import json
from collections import Counter

print("=" * 80)
print("🔍 Williams 未分類部件詳細分析")
print("=" * 80)

# 載入分類結果
with open('2025_f1_parts_changes_classified.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 篩選 Williams 的未分類記錄
williams_unclassified = [
    item for item in data 
    if item.get('車隊') == 'Williams' and item.get('變更類型') == '未分類 (Unclassified)'
]

print(f"\n📊 Williams 未分類記錄: {len(williams_unclassified)} 筆")
print(f"佔 Williams 總記錄比例: {len(williams_unclassified)}/94 = {len(williams_unclassified)/94*100:.1f}%\n")

# 統計部件類型
part_counter = Counter(item.get('部件', 'Unknown') for item in williams_unclassified)

print("📋 未分類部件統計 (按出現次數排序):")
print("-" * 80)
for i, (part, count) in enumerate(part_counter.most_common(), 1):
    print(f"  {i:2}. [{count:2}次] {part}")

# 按比賽分組
print(f"\n🏁 按比賽分組:")
print("-" * 80)
race_groups = {}
for item in williams_unclassified:
    race = item.get('比賽', 'Unknown')
    if race not in race_groups:
        race_groups[race] = []
    race_groups[race].append(item)

for race, items in sorted(race_groups.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n  {race} ({len(items)} 筆):")
    for item in items[:5]:  # 只顯示前5筆
        print(f"    • {item.get('車手'):20} - {item.get('部件')}")
    if len(items) > 5:
        print(f"    ... 還有 {len(items)-5} 筆")

# 詳細記錄（前 20 筆）
print(f"\n📄 詳細記錄 (前 20 筆):")
print("-" * 80)
for i, item in enumerate(williams_unclassified[:20], 1):
    print(f"\n  {i:2}. 比賽: {item.get('比賽')}, 車手: {item.get('車手')}")
    print(f"      部件: {item.get('部件')}")
    print(f"      原始文本: {item.get('原始文本')[:70]}...")
    if item.get('來源文件'):
        doc = item.get('來源文件').split('/')[-1][:50]
        print(f"      來源: {doc}...")

print("\n" + "=" * 80)
print("✅ 分析完成")
print("=" * 80)
