import json
from collections import Counter

# 載入分類後資料
with open('2025_f1_parts_changes_classified.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 篩選未分類項目
unclassified = [r for r in data if r['變更類型'] == '未分類 (Unclassified)']

print(f"未分類總數: {len(unclassified)} 筆\n")

# 按車隊統計
teams = Counter([r['車隊'] for r in unclassified])
print("📊 按車隊分布:")
print("-" * 80)
for team, count in teams.most_common():
    print(f"  {team}: {count} 筆 ({100*count/len(unclassified):.1f}%)")

# 按賽事統計
races = Counter([r['比賽'] for r in unclassified])
print("\n📍 按賽事分布:")
print("-" * 80)
for race, count in races.most_common(10):
    print(f"  {race}: {count} 筆")

# 分析部件名稱模式
print("\n🔍 所有未分類部件列表:")
print("-" * 80)
for i, r in enumerate(unclassified, 1):
    part_name = r['部件']
    print(f"{i:3}. [{r['車隊']:20s}] {part_name[:80]}")
    if len(part_name) > 80:
        print(f"     {part_name[80:]}")

# 關鍵字分析
print("\n📝 部件名稱關鍵字分析:")
print("-" * 80)
keywords = []
for r in unclassified:
    words = r['部件'].lower().split()
    keywords.extend(words)

keyword_freq = Counter(keywords)
print("最常出現的詞彙 (前 30 個):")
for word, count in keyword_freq.most_common(30):
    if len(word) > 2:  # 排除太短的詞
        print(f"  {word}: {count} 次")

# 特殊模式檢測
print("\n🔬 特殊模式檢測:")
print("-" * 80)

patterns = {
    '包含 "new"': [r for r in unclassified if 'new' in r['部件'].lower()],
    '包含 "parameter"': [r for r in unclassified if 'parameter' in r['部件'].lower()],
    '包含 "upgrade"': [r for r in unclassified if 'upgrade' in r['部件'].lower()],
    '包含 "revised"': [r for r in unclassified if 'revised' in r['部件'].lower()],
    '包含 "modified"': [r for r in unclassified if 'modified' in r['部件'].lower()],
    '包含 "updated"': [r for r in unclassified if 'updated' in r['部件'].lower()],
    '包含 "assembly"': [r for r in unclassified if 'assembly' in r['部件'].lower()],
    '包含 "specification"': [r for r in unclassified if 'specification' in r['部件'].lower()],
    '包含 "floor"': [r for r in unclassified if 'floor' in r['部件'].lower()],
    '包含 "wing"': [r for r in unclassified if 'wing' in r['部件'].lower()],
    '包含 "bodywork"': [r for r in unclassified if 'bodywork' in r['部件'].lower()],
    '包含 "sidepod"': [r for r in unclassified if 'sidepod' in r['部件'].lower()],
}

for pattern_name, matches in patterns.items():
    if matches:
        print(f"\n{pattern_name}: {len(matches)} 筆")
        for r in matches[:3]:  # 顯示前 3 個範例
            print(f"  - [{r['車隊']}] {r['部件'][:70]}")
