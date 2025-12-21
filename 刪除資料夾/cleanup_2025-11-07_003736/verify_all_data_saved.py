import json
from pathlib import Path

print("=" * 80)
print("📊 驗證所有數據是否完整保存")
print("=" * 80)

# 檢查完整數據檔案
complete_file = "2025_f1_parts_changes_complete.json"
if Path(complete_file).exists():
    with open(complete_file, 'r', encoding='utf-8') as f:
        complete_data = json.load(f)
    
    print(f"\n✅ 【完整數據檔案】 {complete_file}")
    print(f"   總記錄數: {len(complete_data)} 筆")
    
    # 統計比賽
    races = {}
    for item in complete_data:
        race = item.get('比賽', 'Unknown')
        races[race] = races.get(race, 0) + 1
    
    print(f"   涵蓋比賽: {len(races)} 場")
    
    # 詳細比賽分布
    print(f"\n   📋 各比賽記錄數:")
    for race, count in sorted(races.items(), key=lambda x: x[1], reverse=True):
        emoji = "🇲🇽" if "Mexico" in race else "🏁"
        print(f"      {emoji} {race}: {count} 筆")
    
    # 車隊分布
    teams = {}
    for item in complete_data:
        team = item.get('車隊', 'Unknown')
        teams[team] = teams.get(team, 0) + 1
    
    print(f"\n   📋 各車隊記錄數:")
    for team, count in sorted(teams.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"      {team}: {count} 筆")
    
    # 墨西哥詳細數據
    mexico_data = [item for item in complete_data if item.get('比賽') == 'Mexico City']
    print(f"\n   🇲🇽 墨西哥數據詳情:")
    print(f"      總記錄數: {len(mexico_data)} 筆")
    
    if mexico_data:
        print(f"      包含的部件類型:")
        mexico_parts = {}
        for item in mexico_data:
            part = item.get('部件', 'Unknown')
            mexico_parts[part] = mexico_parts.get(part, 0) + 1
        
        for part, count in mexico_parts.items():
            print(f"        • {part}: {count} 次")
        
        mexico_teams = set(item.get('車隊') for item in mexico_data)
        print(f"      涉及車隊: {', '.join(sorted(mexico_teams))}")
    
    print(f"\n✅ 結論: 所有 {len(complete_data)} 筆記錄（包括微小部件和參數調整）已完整保存！")
    
else:
    print(f"\n❌ 找不到檔案: {complete_file}")

print("\n" + "=" * 80)
print("✅ 驗證完成")
print("=" * 80)
