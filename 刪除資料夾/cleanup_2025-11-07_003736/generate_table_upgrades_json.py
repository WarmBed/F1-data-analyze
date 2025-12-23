#!/usr/bin/env python3
"""
生成符合需求的 JSON 格式：
車隊 | 日期 | 部件 | 推測升級 | 來源文件 | 頁碼
"""
import pandas as pd
import json


def generate_table_format_json():
    """生成表格格式的 JSON"""
    df = pd.read_csv('2025_upgrades_comprehensive.csv', encoding='utf-8-sig')
    
    # 只保留 Parc Fermé 變更
    df_filtered = df[df['evidence_type'] == 'Parc Fermé 變更'].copy()
    
    upgrades_list = []
    
    for _, row in df_filtered.iterrows():
        # 根據部件類型推測升級類型
        component = row['component']
        upgrade_type = ""
        
        if component == "floor":
            upgrade_type = "地板/底板升級（空氣動力學）"
        elif component == "front wing":
            upgrade_type = "前翼升級（空氣動力學）"
        elif component == "rear wing":
            upgrade_type = "後翼升級（空氣動力學）"
        elif component == "sidepod":
            upgrade_type = "側箱升級（空氣動力學/冷卻）"
        elif component == "nose":
            upgrade_type = "鼻錐/前翼組件升級"
        elif component == "cooling":
            upgrade_type = "冷卻系統升級/調整"
        elif component == "suspension":
            upgrade_type = "懸吊系統升級"
        elif component == "brake duct":
            upgrade_type = "煞車風道升級"
        else:
            upgrade_type = f"{component} 升級"
        
        upgrades_list.append({
            "車隊": row['team'],
            "日期": row['date'],
            "比賽": row['race'],
            "部件": component,
            "推測升級": upgrade_type,
            "來源文件": row['source_file'],
            "詳細說明": row['context']
        })
    
    # 按日期排序
    upgrades_list.sort(key=lambda x: x['日期'])
    
    return upgrades_list


def main():
    print("\n🔧 生成表格格式 JSON...")
    
    upgrades = generate_table_format_json()
    
    # 儲存 JSON
    output_file = "2025_f1_upgrades_table.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(upgrades, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已儲存至: {output_file}\n")
    
    # 顯示前 10 筆
    print("="*120)
    print("📋 2025 F1 車隊升級套件詳細記錄（前 10 筆）")
    print("="*120)
    print(f"{'車隊':<18} {'日期':<12} {'比賽':<18} {'部件':<15} {'推測升級':<35}")
    print("="*120)
    
    for upgrade in upgrades[:10]:
        print(f"{upgrade['車隊']:<18} {upgrade['日期']:<12} {upgrade['比賽']:<18} "
              f"{upgrade['部件']:<15} {upgrade['推測升級']:<35}")
    
    print("="*120)
    print(f"總計: {len(upgrades)} 筆記錄")
    print(f"完整資料請查看: {output_file}")
    print("="*120 + "\n")


if __name__ == '__main__':
    main()
