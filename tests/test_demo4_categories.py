#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Demo 4 分類功能
驗證：
1. 數據載入（優先使用 classified_with_categories.json）
2. 主分類和子分類欄位存在
3. 篩選功能正常運作
"""

import json
import os

def test_data_loading():
    """測試數據載入優先順序"""
    print("=" * 60)
    print("測試 1: 數據載入優先順序")
    print("=" * 60)
    
    year = 2025
    files = [
        f"{year}_f1_parts_changes_v2_classified_with_categories.json",
        f"{year}_f1_parts_changes_v2_normalized.json",
        f"{year}_f1_parts_changes_v2_classified.json"
    ]
    
    for i, file_path in enumerate(files, 1):
        exists = os.path.exists(file_path)
        priority = "🥇 第一優先" if i == 1 else "🥈 第二優先" if i == 2 else "🥉 第三優先"
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"{priority} | {file_path}")
        print(f"         狀態: {status}")
        
        if exists and i == 1:
            # 檢查第一優先檔案的分類欄位
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"         記錄數: {len(data)} 筆")
            
            # 檢查前 3 筆記錄的分類欄位
            print("\n         前 3 筆記錄的分類欄位:")
            for idx, record in enumerate(data[:3], 1):
                main_cat = record.get("主分類", "N/A")
                sub_cat = record.get("子分類", "N/A")
                part = record.get("部件", "N/A")
                print(f"           記錄 {idx}:")
                print(f"             部件: {part}")
                print(f"             主分類: {main_cat}")
                print(f"             子分類: {sub_cat}")
    
    print()

def test_category_coverage():
    """測試分類覆蓋率"""
    print("=" * 60)
    print("測試 2: 分類覆蓋率")
    print("=" * 60)
    
    file_path = "2025_f1_parts_changes_v2_classified_with_categories.json"
    
    if not os.path.exists(file_path):
        print("❌ 檔案不存在，跳過測試")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_records = len(data)
    valid_records = [r for r in data if "噪音" not in r.get("變更類型", "")]
    noise_records = total_records - len(valid_records)
    
    # 統計分類情況
    with_main_cat = [r for r in valid_records if r.get("主分類")]
    with_sub_cat = [r for r in valid_records if r.get("子分類")]
    
    print(f"總記錄數: {total_records} 筆")
    print(f"有效記錄: {len(valid_records)} 筆")
    print(f"噪音記錄: {noise_records} 筆")
    print()
    print(f"有主分類: {len(with_main_cat)} 筆 ({len(with_main_cat)/len(valid_records)*100:.1f}%)")
    print(f"有子分類: {len(with_sub_cat)} 筆 ({len(with_sub_cat)/len(valid_records)*100:.1f}%)")
    print()

def test_category_distribution():
    """測試分類分佈"""
    print("=" * 60)
    print("測試 3: 分類分佈統計")
    print("=" * 60)
    
    file_path = "2025_f1_parts_changes_v2_classified_with_categories.json"
    
    if not os.path.exists(file_path):
        print("❌ 檔案不存在，跳過測試")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    valid_records = [r for r in data if "噪音" not in r.get("變更類型", "")]
    
    # 統計主分類分佈
    main_categories = {}
    for record in valid_records:
        main_cat = record.get("主分類", "未分類")
        main_categories[main_cat] = main_categories.get(main_cat, 0) + 1
    
    print("主分類分佈（前 10 名）:")
    for i, (cat, count) in enumerate(sorted(main_categories.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        percentage = count / len(valid_records) * 100
        print(f"  {i:2d}. {cat:20s} | {count:3d} 筆 ({percentage:5.1f}%)")
    
    print()
    
    # 統計子分類分佈
    sub_categories = {}
    for record in valid_records:
        sub_cat = record.get("子分類", "未分類")
        sub_categories[sub_cat] = sub_categories.get(sub_cat, 0) + 1
    
    print("子分類分佈（前 10 名）:")
    for i, (cat, count) in enumerate(sorted(sub_categories.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        percentage = count / len(valid_records) * 100
        print(f"  {i:2d}. {cat:25s} | {count:3d} 筆 ({percentage:5.1f}%)")
    
    print()

def test_demo4_import():
    """測試 Demo 4 模組導入"""
    print("=" * 60)
    print("測試 4: Demo 4 模組導入")
    print("=" * 60)
    
    try:
        import sys
        sys.path.insert(0, '.')
        from modules.gui.classification_analysis.demo_4_detailed_table import ClassificationDetailedTableWidget
        print("✅ Demo 4 模組導入成功")
        
        # 檢查新增的屬性
        expected_attrs = [
            'main_category_combo',
            'sub_category_combo',
            'on_main_category_changed'
        ]
        
        print("\n檢查新增的分類功能:")
        for attr in expected_attrs:
            # 檢查類別定義中是否有相關代碼
            has_attr = f"self.{attr}" in open("modules/gui/classification_analysis/demo_4_detailed_table.py").read()
            status = "✅" if has_attr else "❌"
            print(f"  {status} {attr}")
        
    except Exception as e:
        print(f"❌ Demo 4 模組導入失敗: {e}")
    
    print()

if __name__ == "__main__":
    print("\n🧪 Demo 4 分類功能測試\n")
    
    test_data_loading()
    test_category_coverage()
    test_category_distribution()
    test_demo4_import()
    
    print("=" * 60)
    print("✅ 所有測試完成")
    print("=" * 60)
