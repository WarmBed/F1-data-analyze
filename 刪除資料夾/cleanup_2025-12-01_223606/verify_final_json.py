"""驗證最終生成的 API JSON 檔案"""
import json
from pathlib import Path

def verify_json():
    json_file = Path("json/fia_parts_analysis_2025.json")
    
    if not json_file.exists():
        print("❌ 找不到 JSON 檔案")
        return
    
    # 讀取 JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("✅ JSON 結構驗證成功")
    print("=" * 60)
    print(f"📄 檔案: {json_file.name}")
    print(f"📊 記錄數: {len(data['records'])} 筆")
    print(f"🏁 賽事數: {len(set(r['賽事'] for r in data['records']))} 場")
    print(f"🏎️  車隊數: {len(set(r['車隊'] for r in data['records']))} 隊")
    
    # 噪音關鍵字檢查
    noise_keywords = [
        'request from the team',
        'Article 40.3',
        'Jo Bauer',
        'Technical Delegate',
        'All above parts',
        'Sporting Regulations',
        'approval of the',
        'being in accordance',
        'From The FIA'
    ]
    
    print(f"\n🔍 噪音關鍵字檢查:")
    noise_found = False
    for keyword in noise_keywords:
        count = sum(1 for r in data['records'] if keyword.lower() in r['部件'].lower())
        if count > 0:
            print(f"⚠️  '{keyword}': {count} 筆")
            noise_found = True
        else:
            print(f"✅ '{keyword}': 0 筆")
    
    if not noise_found:
        print(f"\n✅ 沒有找到噪音記錄！過濾成功")
    else:
        print(f"\n⚠️  發現噪音記錄，需要檢查")
    
    # 顯示有效部件範例
    print(f"\n📋 有效部件記錄範例 (前 10 筆):")
    for i, record in enumerate(data['records'][:10], 1):
        print(f"{i}. {record['車隊']} - {record['部件']} ({record['賽事']})")
    
    # 賽事分佈統計
    race_counts = {}
    for r in data['records']:
        race = r['賽事']
        race_counts[race] = race_counts.get(race, 0) + 1
    
    print(f"\n🏁 賽事分佈 (部件變更數):")
    for race, count in sorted(race_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {race}: {count} 筆")

if __name__ == "__main__":
    verify_json()
