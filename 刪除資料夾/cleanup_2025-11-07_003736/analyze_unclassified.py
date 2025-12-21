import json
from collections import Counter

# 載入分類結果
with open('2025_f1_parts_changes_classified.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找出未分類記錄
unclassified = [item for item in data if item.get('變更類型') == '未分類 (Unclassified)']

print(f"📊 未分類記錄分析 ({len(unclassified)} 筆)")
print("=" * 80)

# 統計未分類的部件類型
part_counter = Counter(item.get('部件', 'Unknown') for item in unclassified)

print(f"\n🔍 未分類部件 TOP 20:")
for i, (part, count) in enumerate(part_counter.most_common(20), 1):
    print(f"  {i:2}. {part:60} {count:3} 次")

# 顯示一些完整範例
print(f"\n📋 未分類記錄範例 (前 10 筆):")
print("-" * 80)
for i, item in enumerate(unclassified[:10], 1):
    print(f"\n  {i}. 車隊: {item.get('車隊')}, 車手: {item.get('車手')}")
    print(f"     比賽: {item.get('比賽')}")
    print(f"     部件: {item.get('部件')}")
    print(f"     原始文本: {item.get('原始文本')[:80]}...")
