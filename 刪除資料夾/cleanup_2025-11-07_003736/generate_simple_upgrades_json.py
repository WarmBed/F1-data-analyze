#!/usr/bin/env python3
"""
生成簡化版 JSON: 車隊 → 比賽 → 零件列表
"""
import pandas as pd
import json
from collections import defaultdict


def generate_simplified_json():
    """生成簡化的 JSON 格式"""
    df = pd.read_csv('2025_upgrades_comprehensive.csv', encoding='utf-8-sig')
    
    # 只保留 Parc Fermé 變更
    df_filtered = df[df['evidence_type'] == 'Parc Fermé 變更'].copy()
    
    # 結構: { 車隊: [ { race, date, parts: [] } ] }
    upgrades = {}
    
    for team in sorted(df_filtered['team'].unique()):
        team_data = df_filtered[df_filtered['team'] == team].copy()
        
        races_dict = defaultdict(list)
        dates_dict = {}
        
        for _, row in team_data.iterrows():
            races_dict[row['race']].append(row['component'])
            dates_dict[row['race']] = row['date']
        
        # 轉換為列表
        races_list = []
        for race, parts in races_dict.items():
            races_list.append({
                "比賽": race,
                "日期": dates_dict[race],
                "零件": list(set(parts))  # 去重
            })
        
        # 按日期排序
        races_list.sort(key=lambda x: x['日期'])
        
        upgrades[team] = races_list
    
    return upgrades


def main():
    print("\n🔧 生成簡化版 JSON (車隊 → 比賽 → 零件)...")
    
    upgrades = generate_simplified_json()
    
    # 儲存 JSON
    output_file = "2025_f1_upgrades_simple.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(upgrades, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已儲存至: {output_file}\n")
    
    # 顯示內容
    print("="*80)
    print("📋 2025 F1 車隊升級套件一覽表")
    print("="*80)
    
    for team, races in upgrades.items():
        print(f"\n🏎️  {team} ({len(races)} 個分站)")
        print("-"*80)
        for race_data in races:
            parts_str = ", ".join(race_data['零件'])
            print(f"  📍 {race_data['比賽']:<18} ({race_data['日期']})  →  {parts_str}")
    
    print("\n" + "="*80)
    print(f"✅ 完整 JSON 已儲存至: {output_file}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
