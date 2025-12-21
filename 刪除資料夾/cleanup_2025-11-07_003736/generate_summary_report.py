import json

print("=" * 80)
print(" 2025 F1 部件變更數據總結報告")
print("=" * 80)

# 1. 完整數據統計
print("\n📊 【完整部件變更數據】 (2025_f1_parts_changes_complete.json)")
with open('2025_f1_parts_changes_complete.json', 'r', encoding='utf-8') as f:
    complete_data = json.load(f)

print(f"   總記錄數: {len(complete_data)} 筆")

# 統計比賽
races_complete = {}
for item in complete_data:
    race = item.get('比賽', 'Unknown')
    races_complete[race] = races_complete.get(race, 0) + 1

print(f"   涵蓋比賽: {len(races_complete)} 場")
print(f"   比賽列表: {', '.join(sorted(races_complete.keys()))}")

# 墨西哥數據
mexico_complete = [item for item in complete_data if item.get('比賽') == 'Mexico City']
print(f"\n   🇲🇽 墨西哥數據:")
print(f"      記錄數: {len(mexico_complete)} 筆")
if mexico_complete:
    teams = set(item.get('車隊') for item in mexico_complete)
    print(f"      涉及車隊: {', '.join(sorted(teams))}")
    
    # 部件類型分布
    parts_types = {}
    for item in mexico_complete:
        part = item.get('部件', 'Unknown')
        parts_types[part] = parts_types.get(part, 0) + 1
    
    print(f"      部件類型:")
    for part, count in sorted(parts_types.items(), key=lambda x: x[1], reverse=True):
        print(f"        • {part}: {count} 次")

# 2. 主要升級統計
print("\n\n📊 【主要部件升級】 (2025_f1_major_upgrades.json)")
with open('2025_f1_major_upgrades.json', 'r', encoding='utf-8') as f:
    major_data = json.load(f)

upgrades = major_data['主要部件升級記錄']
metadata = major_data['metadata']

print(f"   總記錄數: {len(upgrades)} 筆")
print(f"   涵蓋比賽: {len(set(item.get('比賽') for item in upgrades))} 場")

# 墨西哥主要升級
mexico_major = [item for item in upgrades if item.get('比賽') == 'Mexico City']
print(f"\n   🇲🇽 墨西哥主要升級:")
print(f"      記錄數: {len(mexico_major)} 筆")
if len(mexico_major) == 0:
    print(f"      原因: 墨西哥站的 14 筆變更均為小部件或參數調整,無主要部件升級")

# 3. 過濾統計
print("\n\n📊 【過濾效果】")
print(f"   完整數據: {len(complete_data)} 筆")
print(f"   主要升級: {len(upgrades)} 筆")
print(f"   過濾率: {(1 - len(upgrades)/len(complete_data))*100:.1f}%")
print(f"   保留率: {(len(upgrades)/len(complete_data))*100:.1f}%")

# 4. 比賽覆蓋對比
print("\n\n📊 【比賽覆蓋對比】")
races_major = {}
for item in upgrades:
    race = item.get('比賽', 'Unknown')
    races_major[race] = races_major.get(race, 0) + 1

print(f"   完整數據涵蓋: {len(races_complete)} 場比賽")
print(f"   主要升級涵蓋: {len(races_major)} 場比賽")

# 找出沒有主要升級的比賽
no_major_races = set(races_complete.keys()) - set(races_major.keys())
if no_major_races:
    print(f"\n   ⚠️  無主要升級的比賽 ({len(no_major_races)} 場):")
    for race in sorted(no_major_races):
        print(f"      • {race}: {races_complete[race]} 筆變更 (全為小部件/參數)")

# 5. 頂級統計
print("\n\n📊 【頂級統計】")
print(f"   車隊主要升級 TOP 5:")
for i, (team, count) in enumerate(list(metadata['統計資訊']['各車隊主要升級次數'].items())[:5], 1):
    print(f"      {i}. {team}: {count} 次")

print(f"\n   車手主要升級 TOP 5:")
for i, (driver, count) in enumerate(list(metadata['統計資訊']['各車手主要升級次數'].items())[:5], 1):
    print(f"      {i}. {driver}: {count} 次")

print(f"\n   部件類別 TOP 5:")
for i, (category, count) in enumerate(list(metadata['統計資訊']['各部件類別次數'].items())[:5], 1):
    print(f"      {i}. {category}: {count} 次")

print("\n" + "=" * 80)
print(" 報告生成完成")
print("=" * 80)
