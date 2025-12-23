#!/usr/bin/env python3
"""
部件名稱標準化工具
合併重複的部件名稱變體
"""
import json
import re
from collections import Counter

def normalize_part_name(part_name):
    """標準化部件名稱"""
    if not part_name:
        return part_name
    
    # 移除尾部的 FIA 技術代表註記
    part_name = re.sub(r'From The FIA Formula One Technical Delegate.*$', '', part_name, flags=re.IGNORECASE)
    
    # 移除車號和車隊資訊
    part_name = re.sub(r'Car \d+:.*$', '', part_name)
    part_name = re.sub(r'\s+(Red Bull Racing|Mercedes|Ferrari|McLaren|Alpine|Aston Martin|Williams|Haas|RB|Kick Sauber).*$', '', part_name)
    
    # 標準化空格（在其他處理之前）
    part_name = re.sub(r'\s+', ' ', part_name)
    
    # 標準化 front wing/nose 的多種寫法
    # 匹配: "Front wing/nose assembly", "Front wing / nose assembly", "Front wing/nosebox assembly"
    if re.search(r'front\s*wing\s*/\s*nose', part_name, flags=re.IGNORECASE):
        part_name = 'Front wing/nose assembly'
    
    # 標準化其他常見變體
    # Floor assembly 系列
    if 'floor assembly (excluding skids and plank)' in part_name.lower():
        part_name = 'Floor assembly (excluding skids and plank)'
    
    # Rear wing assembly
    if part_name.lower() == 'rear wing assemblyFrom The FIA Formula One Technical Delegate'.lower():
        part_name = 'Rear wing assembly'
    
    # Parameter changes 標準化（移除多餘空格）
    if 'parameter changes' in part_name.lower():
        part_name = re.sub(r'\s+the\s+', ' the ', part_name)
        part_name = re.sub(r'\s+', ' ', part_name)
    
    # MGU-K 變體標準化
    if re.match(r'MGU-K\s*\(previously used\)', part_name, flags=re.IGNORECASE):
        part_name = 'MGU-K (previously used)'
    
    # 移除首尾空格
    part_name = part_name.strip()
    
    return part_name

def main():
    # 讀取原始數據
    print("讀取數據...")
    with open('2025_f1_parts_changes_v2_classified.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 統計原始和清理後的部件名稱
    original_parts = [r.get('部件', '') for r in data if r.get('部件')]
    
    # 排除噪音
    exclude = ['Date ', 'Time ', 'To The Stewards', 'written request']
    valid_original = [p for p in original_parts if not any(ex in p for ex in exclude)]
    valid_normalized = [normalize_part_name(p) for p in valid_original]
    
    original_count = len(set(valid_original))
    normalized_count = len(set(valid_normalized))
    
    print(f'\n原始部件種類數: {original_count}')
    print(f'標準化後部件種類數: {normalized_count}')
    print(f'合併了 {original_count - normalized_count} 個重複項\n')
    
    # 顯示前翼相關的合併範例
    print('=== 前翼合併範例 ===')
    front_wing_variants = sorted([p for p in set(valid_original) if 'front wing' in p.lower() and 'nose' in p.lower()])
    
    print(f'\n找到 {len(front_wing_variants)} 個 Front wing/nose 變體:\n')
    for variant in front_wing_variants:
        normalized = normalize_part_name(variant)
        print(f'原始: "{variant}"')
        print(f'標準化: "{normalized}"')
        print()
    
    # 顯示其他常見的重複項
    print('\n=== 其他常見重複項 ===\n')
    
    # 建立映射表
    part_mapping = {}
    for orig, norm in zip(valid_original, valid_normalized):
        if orig != norm:
            if norm not in part_mapping:
                part_mapping[norm] = []
            if orig not in part_mapping[norm]:
                part_mapping[norm].append(orig)
    
    # 顯示有多個變體的部件
    multi_variant_parts = {k: v for k, v in part_mapping.items() if len(v) > 1}
    
    for norm_name, variants in sorted(multi_variant_parts.items())[:10]:
        print(f'標準化名稱: "{norm_name}"')
        print(f'  變體數量: {len(variants)}')
        for v in variants:
            print(f'    - "{v}"')
        print()
    
    # 建議：創建標準化後的新 JSON
    print('\n是否要創建標準化後的新 JSON 檔案？')
    print('這將會：')
    print('1. 更新所有記錄的「部件」欄位為標準化名稱')
    print('2. 保存為 2025_f1_parts_changes_v2_normalized.json')
    
    choice = input('\n輸入 y 確認創建: ').lower()
    
    if choice == 'y':
        # 創建標準化版本
        normalized_data = []
        for record in data:
            new_record = record.copy()
            if '部件' in new_record and new_record['部件']:
                new_record['部件'] = normalize_part_name(new_record['部件'])
            normalized_data.append(new_record)
        
        # 保存
        output_file = '2025_f1_parts_changes_v2_normalized.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(normalized_data, f, ensure_ascii=False, indent=2)
        
        print(f'\n✅ 已保存標準化數據到: {output_file}')
        print(f'   總記錄數: {len(normalized_data)}')
        print(f'   部件種類: {len(set([r.get("部件", "") for r in normalized_data if r.get("部件")]))}')

if __name__ == '__main__':
    main()
