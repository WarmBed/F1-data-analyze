import json

# 讀取主要升級 JSON
with open('2025_f1_major_upgrades.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

print(f"📊 JSON 資料類型: {type(json_data)}")
print(f"📋 字典鍵值: {list(json_data.keys())}\n")

# 提取實際的記錄列表
if '主要部件升級記錄' in json_data:
    data = json_data['主要部件升級記錄']
    metadata = json_data.get('metadata', {})
    
    print(f"✅ 總記錄數: {len(data)}")
    print(f"📅 元數據: {metadata}\n")
    
    # 檢查墨西哥數據
    mexico_data = [item for item in data if item.get('比賽') == 'Mexico City']
    print(f"🇲🇽 墨西哥記錄數: {len(mexico_data)}")
    
    if mexico_data:
        print("\n📄 墨西哥數據範例 (前5筆):")
        for i, item in enumerate(mexico_data[:5], 1):
            print(f"\n  記錄 {i}:")
            print(f"    車隊: {item.get('車隊')}")
            print(f"    車手: {item.get('車手')}")
            print(f"    部件: {item.get('部件')}")
            print(f"    日期: {item.get('日期')}")
            print(f"    部件類別: {item.get('部件類別')}")
            print(f"    來源: {item.get('來源文件')}")
    else:
        print("\n❌ 沒有找到墨西哥數據")
        print("🔍 檢查可能的比賽名稱:")
        unique_races = set(item.get('比賽', 'Unknown') for item in data)
        for race in sorted(unique_races):
            if 'Mexico' in race or 'mexic' in race.lower():
                print(f"  ✅ 找到: {race}")
        
    # 統計所有比賽
    races = {}
    for item in data:
        race = item.get('比賽', 'Unknown')
        races[race] = races.get(race, 0) + 1
    
    print(f"\n📊 比賽分布 (共 {len(races)} 個比賽):")
    for race, count in sorted(races.items(), key=lambda x: x[1], reverse=True):
        emoji = "🇲🇽" if "Mexico" in race else "🏁"
        print(f"  {emoji} {race}: {count} 筆")
else:
    print(f"❌ 找不到 '主要部件升級記錄' 鍵值")
