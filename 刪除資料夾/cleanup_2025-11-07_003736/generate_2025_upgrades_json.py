#!/usr/bin/env python3
"""
將 2025 F1 車隊升級數據轉換為 JSON 格式
基於 FIA 官方文件分析結果
"""
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime


def load_and_process_data():
    """載入 CSV 並處理數據"""
    df = pd.read_csv('2025_upgrades_comprehensive.csv', encoding='utf-8-sig')
    
    # 只保留 Parc Fermé 變更（排除 Power Unit，因為不確定是否為升級）
    # 您可以根據需要調整此篩選條件
    df_filtered = df[df['evidence_type'] == 'Parc Fermé 變更'].copy()
    
    return df_filtered


def generate_json_by_team(df):
    """按車隊分組生成 JSON"""
    upgrades_by_team = defaultdict(lambda: {
        "team_name": "",
        "total_upgrades": 0,
        "races": []
    })
    
    # 按車隊和分站分組
    for team in df['team'].unique():
        team_data = df[df['team'] == team].copy()
        upgrades_by_team[team]["team_name"] = team
        upgrades_by_team[team]["total_upgrades"] = len(team_data)
        
        # 按分站組織
        race_dict = defaultdict(list)
        for _, row in team_data.iterrows():
            race_dict[row['race']].append({
                "component": row['component'],
                "car_number": str(row['car_number']),
                "evidence_type": row['evidence_type'],
                "context": row['context']
            })
        
        # 轉換為列表格式
        for race, components in race_dict.items():
            race_date = team_data[team_data['race'] == race]['date'].iloc[0]
            upgrades_by_team[team]["races"].append({
                "race": race,
                "date": race_date,
                "component_count": len(components),
                "components": components
            })
        
        # 按日期排序
        upgrades_by_team[team]["races"].sort(key=lambda x: x['date'])
    
    return dict(upgrades_by_team)


def generate_json_by_race(df):
    """按分站分組生成 JSON"""
    upgrades_by_race = []
    
    for race in sorted(df['race'].unique()):
        race_data = df[df['race'] == race].copy()
        race_date = race_data['date'].iloc[0]
        
        teams_dict = defaultdict(list)
        for _, row in race_data.iterrows():
            teams_dict[row['team']].append({
                "component": row['component'],
                "car_number": str(row['car_number']),
                "evidence_type": row['evidence_type'],
                "context": row['context']
            })
        
        # 轉換為列表格式
        teams_list = []
        for team, components in teams_dict.items():
            teams_list.append({
                "team": team,
                "component_count": len(components),
                "components": components
            })
        
        upgrades_by_race.append({
            "race": race,
            "date": race_date,
            "total_teams": len(teams_dict),
            "total_components": len(race_data),
            "teams": teams_list
        })
    
    # 按日期排序
    upgrades_by_race.sort(key=lambda x: x['date'])
    
    return upgrades_by_race


def generate_complete_json(df):
    """生成完整的 JSON 結構"""
    complete_data = {
        "metadata": {
            "season": 2025,
            "data_source": "FIA Official Documents (fiadoc)",
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "total_records": len(df),
            "evidence_types": df['evidence_type'].value_counts().to_dict(),
            "note": "僅包含 Parc Fermé 變更記錄，動力單元升級已排除"
        },
        "summary": {
            "total_teams": len(df['team'].unique()),
            "total_races": len(df['race'].unique()),
            "component_distribution": df['component'].value_counts().to_dict()
        },
        "by_team": generate_json_by_team(df),
        "by_race": generate_json_by_race(df)
    }
    
    return complete_data


def main():
    print("\n" + "="*80)
    print("🏁 2025 F1 車隊升級數據 JSON 生成器")
    print("="*80)
    
    # 載入數據
    print("\n📂 載入 CSV 數據...")
    df = load_and_process_data()
    print(f"   ✅ 已載入 {len(df)} 筆記錄")
    
    # 生成 JSON
    print("\n🔧 生成 JSON 結構...")
    json_data = generate_complete_json(df)
    
    # 儲存 JSON 檔案
    output_file = "2025_f1_upgrades.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ JSON 已儲存至: {output_file}")
    
    # 顯示摘要
    print("\n" + "="*80)
    print("📊 JSON 內容摘要")
    print("="*80)
    print(f"賽季: {json_data['metadata']['season']}")
    print(f"總記錄數: {json_data['metadata']['total_records']}")
    print(f"涵蓋車隊: {json_data['summary']['total_teams']} 支")
    print(f"涵蓋分站: {json_data['summary']['total_races']} 站")
    
    print("\n📋 各車隊升級次數:")
    team_counts = [(team, data['total_upgrades']) 
                   for team, data in json_data['by_team'].items()]
    team_counts.sort(key=lambda x: x[1], reverse=True)
    for team, count in team_counts:
        print(f"   {team:<20} {count:>3} 次")
    
    print("\n📦 部件類型分布:")
    for component, count in json_data['summary']['component_distribution'].items():
        print(f"   {component:<15} {count:>3} 次")
    
    print("\n" + "="*80)
    print("✅ 完成！")
    print("="*80)
    print("\nJSON 結構說明:")
    print("  - metadata: 元數據（賽季、數據來源、分析日期）")
    print("  - summary: 總覽統計")
    print("  - by_team: 按車隊分組的升級記錄")
    print("  - by_race: 按分站分組的升級記錄")
    print("="*80 + "\n")
    
    # 顯示範例 JSON 片段
    print("📝 JSON 範例片段:")
    print("-"*80)
    print(json.dumps({
        "範例_by_team": {
            list(json_data['by_team'].keys())[0]: 
            json_data['by_team'][list(json_data['by_team'].keys())[0]]
        }
    }, ensure_ascii=False, indent=2))
    print("-"*80 + "\n")


if __name__ == '__main__':
    main()
