#!/usr/bin/env python3
"""
顯示變更類型分類統計
"""
import json
from collections import defaultdict


def show_classification_stats(json_file="2025_f1_major_upgrades_organized.json"):
    """顯示變更類型分類統計"""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data['metadata']
    teams = data['車隊升級記錄']
    
    print("\n" + "="*100)
    print(f"📊 {metadata['資料標題']} - 變更類型分類統計")
    print("="*100)
    print(f"生成時間: {metadata['生成時間']}")
    
    # 全局統計
    print("\n" + "="*100)
    print("🌍 全局變更類型分佈")
    print("="*100)
    
    global_stats = metadata['全局統計'].get('變更類型分佈', {})
    total = metadata['全局統計']['總升級次數']
    
    # 排序並顯示
    sorted_types = sorted(global_stats.items(), key=lambda x: x[1], reverse=True)
    
    for change_type, count in sorted_types:
        percentage = count / total * 100
        bar_length = int(percentage / 2)  # 每 2% 一個 █
        bar = "█" * bar_length
        
        print(f"{change_type:<35} {count:>3} 次 ({percentage:>5.1f}%) {bar}")
    
    # 各車隊變更類型分佈
    print("\n" + "="*100)
    print("🏁 各車隊變更類型分佈")
    print("="*100)
    
    team_change_types = {}
    
    for team_name, team_data in teams.items():
        team_change_types[team_name] = defaultdict(int)
        
        for driver_data in team_data['車手'].values():
            for upgrade in driver_data['升級記錄']:
                change_type = upgrade.get('變更類型', '未分類')
                team_change_types[team_name][change_type] += 1
    
    # 顯示各車隊統計（前 5 個車隊）
    for team_name, change_stats in list(team_change_types.items())[:5]:
        print(f"\n{team_name}:")
        team_total = sum(change_stats.values())
        
        for change_type, count in sorted(change_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = count / team_total * 100
            print(f"  {change_type:<33} {count:>2} 次 ({percentage:>4.0f}%)")
    
    # 變更類型定義
    print("\n" + "="*100)
    print("📝 變更類型定義")
    print("="*100)
    
    definitions = {
        "升級套件 (Upgrade Package)": "新設計、需 re-presented / re-homologated、性能提升",
        "重大更新 (Major Update)": "結構性改動、觸發 FIA 重新檢驗、但非全新套件",
        "變更 (Change)": "Parc Fermé 內合法調整、空力/配置切換",
        "維修 (Repair)": "損壞後更換舊件或備件",
        "未分類 (Unclassified)": "無法根據現有規則分類"
    }
    
    for change_type, description in definitions.items():
        print(f"\n{change_type}")
        print(f"  定義: {description}")
    
    # 範例展示
    print("\n" + "="*100)
    print("📋 各類型範例")
    print("="*100)
    
    examples_by_type = defaultdict(list)
    
    for team_data in teams.values():
        for driver_data in team_data['車手'].values():
            for upgrade in driver_data['升級記錄']:
                change_type = upgrade.get('變更類型', '未分類')
                if len(examples_by_type[change_type]) < 3:  # 每類型最多 3 個範例
                    examples_by_type[change_type].append({
                        "部件": upgrade['更換部件'],
                        "車手": driver_data['車手資訊']['車手姓名'],
                        "車隊": driver_data['車手資訊']['所屬車隊'],
                        "賽事": upgrade['賽事名稱']
                    })
    
    for change_type in ["升級套件 (Upgrade Package)", "重大更新 (Major Update)", 
                        "變更 (Change)", "維修 (Repair)"]:
        if change_type in examples_by_type:
            print(f"\n{change_type}:")
            for i, example in enumerate(examples_by_type[change_type], 1):
                print(f"  {i}. {example['車隊']} - {example['車手']} @ {example['賽事']}")
                print(f"     部件: {example['部件'][:70]}")
    
    print("\n" + "="*100)
    print(f"✅ 完整數據已儲存至: {json_file}")
    print("="*100 + "\n")


if __name__ == '__main__':
    show_classification_stats()
