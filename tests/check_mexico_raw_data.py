import json

# 讀取完整數據
with open('2025_f1_parts_changes_complete.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找出墨西哥的數據
mexico_data = [item for item in data if item.get('比賽') == 'Mexico City']

print(f"📊 墨西哥總記錄數: {len(mexico_data)}\n")

# 顯示所有墨西哥記錄的部件名稱
print("📋 墨西哥所有部件列表：")
for i, item in enumerate(mexico_data, 1):
    print(f"\n  {i}. 車隊: {item.get('車隊')}, 車手: {item.get('車手')}")
    print(f"     部件: {item.get('部件')}")
    print(f"     原始文本: {item.get('原始文本')[:80]}...")

# 檢查這些部件是否匹配主要部件規則
print("\n\n🔍 檢查為何被過濾掉:")
from extract_major_upgrades_2025 import MajorUpgradeExtractor

extractor = MajorUpgradeExtractor()
matched = 0
not_matched = 0

for item in mexico_data:
    is_major, category = extractor.is_major_component(item.get('部件', ''))
    if is_major:
        matched += 1
        print(f"  ✅ {item.get('部件')} → {category}")
    else:
        not_matched += 1
        print(f"  ❌ {item.get('部件')}")

print(f"\n📊 匹配統計: 匹配 {matched} 筆, 未匹配 {not_matched} 筆")
