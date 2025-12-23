#!/usr/bin/env python3
"""
顯示重組後的主要升級 JSON 結構摘要
展示: 車隊 → 車手 → 賽事 → 升級詳情
"""
import json


def display_organized_upgrades(json_file="2025_f1_major_upgrades_organized.json", max_teams=3, max_drivers_per_team=2):
    """顯示重組後的升級記錄摘要"""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data['metadata']
    teams = data['車隊升級記錄']
    
    print("\n" + "="*120)
    print(f"📊 {metadata['資料標題']}")
    print("="*120)
    print(f"生成時間: {metadata['生成時間']}")
    print(f"數據源: {metadata['數據源']}")
    print("\n🌍 全局統計:")
    print(f"  • 總升級次數: {metadata['全局統計']['總升級次數']}")
    print(f"  • 涉及車隊數: {metadata['全局統計']['涉及車隊數']}")
    print(f"  • 涉及賽事數: {metadata['全局統計']['涉及賽事數']}")
    print(f"  • 涉及賽事: {', '.join(metadata['全局統計']['涉及賽事'][:10])}...")
    
    print("\n" + "="*120)
    print(f"📋 詳細記錄結構示範（顯示前 {max_teams} 個車隊）")
    print("="*120)
    
    for team_idx, (team_name, team_data) in enumerate(list(teams.items())[:max_teams], 1):
        print(f"\n{'─'*120}")
        print(f"🏁 車隊 #{team_idx}: {team_name}")
        print(f"{'─'*120}")
        
        team_stats = team_data['車隊統計']
        print(f"📈 車隊統計:")
        print(f"   • 總升級次數: {team_stats['總升級次數']}")
        print(f"   • 涉及賽事 ({len(team_stats['涉及賽事'])} 場): {', '.join(team_stats['涉及賽事'])}")
        print(f"   • 部件類別分佈:")
        for category, count in sorted(team_stats['部件類別分佈'].items(), key=lambda x: x[1], reverse=True):
            print(f"     - {category}: {count} 次")
        
        drivers = team_data['車手']
        print(f"\n👨‍🏎️ 車手 ({len(drivers)} 位):")
        
        for driver_idx, (driver_name, driver_data) in enumerate(list(drivers.items())[:max_drivers_per_team], 1):
            driver_info = driver_data['車手資訊']
            driver_stats = driver_data['車手統計']
            upgrades = driver_data['升級記錄']
            
            print(f"\n   {driver_idx}. {driver_name} (車號 {driver_info['車號']})")
            print(f"      • 升級次數: {driver_stats['總升級次數']}")
            print(f"      • 涉及賽事: {', '.join(driver_stats['涉及賽事'])}")
            print(f"      • 部件類別: {', '.join([f'{k}({v})' for k,v in driver_stats['部件類別分佈'].items()])}")
            
            # 顯示前 3 筆升級記錄
            print(f"\n      📝 升級記錄（顯示前 3 筆，共 {len(upgrades)} 筆）:")
            for upgrade_idx, upgrade in enumerate(upgrades[:3], 1):
                print(f"         {upgrade_idx}. [{upgrade['比賽日期']}] {upgrade['賽事名稱']}")
                print(f"            • 更換部件: {upgrade['更換部件']}")
                print(f"            • 部件類別: {upgrade['部件類別']}")
                print(f"            • 資料來源: {upgrade['資料來源']['文件名稱'][:60]}... (第 {upgrade['資料來源']['頁碼']} 頁)")
                print(f"            • 原始記錄: {upgrade['原始記錄'][:80]}...")
        
        if len(drivers) > max_drivers_per_team:
            print(f"\n   ... 還有 {len(drivers) - max_drivers_per_team} 位車手未顯示")
    
    if len(teams) > max_teams:
        print(f"\n{'─'*120}")
        print(f"... 還有 {len(teams) - max_teams} 個車隊未顯示")
    
    print("\n" + "="*120)
    print("✅ JSON 檔案結構:")
    print("="*120)
    print("""
{
  "metadata": {
    "資料標題": "2025 F1 主要部件升級完整記錄",
    "生成時間": "...",
    "全局統計": { ... }
  },
  "車隊升級記錄": {
    "車隊名稱": {
      "車隊統計": {
        "總升級次數": ...,
        "涉及賽事": [...],
        "部件類別分佈": { ... }
      },
      "車手": {
        "車手名稱": {
          "車手資訊": {
            "車號": "...",
            "車手姓名": "...",
            "所屬車隊": "..."
          },
          "車手統計": {
            "總升級次數": ...,
            "涉及賽事": [...],
            "部件類別分佈": { ... }
          },
          "升級記錄": [
            {
              "賽事名稱": "...",
              "比賽日期": "...",
              "更換部件": "...",
              "部件類別": "...",
              "資料來源": {
                "文件名稱": "...",
                "頁碼": ...
              },
              "原始記錄": "..."
            }
          ]
        }
      }
    }
  }
}
    """)
    print("="*120)
    print(f"\n💾 完整數據已儲存至: {json_file}")
    print("="*120 + "\n")


if __name__ == '__main__':
    display_organized_upgrades(max_teams=2, max_drivers_per_team=2)
