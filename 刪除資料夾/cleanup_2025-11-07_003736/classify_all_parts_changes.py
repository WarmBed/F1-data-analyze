#!/usr/bin/env python3
"""
為所有部件變更記錄執行自動分類
根據更新後的 6 分類系統：
1. 升級套件 (Upgrade Package)
2. 重大更新 (Major Update)
3. 變更 (Change)
4. 參數調整 (Parameter Adjustment)
5. 安全/標準件 (Safety/Standard Parts)
6. 維修 (Repair)
"""
import json
from pathlib import Path
from upgrade_classifier import UpgradeClassifier


def classify_all_changes():
    """對所有部件變更執行分類並保存"""
    
    # 載入完整數據
    input_file = "2025_f1_parts_changes_complete.json"
    output_file = "2025_f1_parts_changes_classified.json"
    
    print("=" * 80)
    print("🔍 部件變更自動分類系統")
    print("=" * 80)
    
    if not Path(input_file).exists():
        print(f"❌ 找不到檔案: {input_file}")
        return
    
    # 載入數據
    with open(input_file, 'r', encoding='utf-8') as f:
        all_changes = json.load(f)
    
    print(f"\n✅ 已載入 {len(all_changes)} 筆部件變更記錄")
    
    # 初始化分類器
    classifier = UpgradeClassifier()
    
    print(f"\n🤖 開始執行分類...")
    print(f"   分類規則: 6 種類型")
    print(f"   1. 升級套件 (Upgrade Package)")
    print(f"   2. 重大更新 (Major Update)")
    print(f"   3. 變更 (Change)")
    print(f"   4. 參數調整 (Parameter Adjustment)")
    print(f"   5. 安全/標準件 (Safety/Standard Parts)")
    print(f"   6. 維修 (Repair)")
    
    # 執行分類
    classified_changes = []
    stats = {
        "升級套件 (Upgrade Package)": 0,
        "重大更新 (Major Update)": 0,
        "變更 (Change)": 0,
        "參數調整 (Parameter Adjustment)": 0,
        "安全/標準件 (Safety/Standard Parts)": 0,
        "維修 (Repair)": 0,
        "未分類 (Unclassified)": 0
    }
    
    for i, change in enumerate(all_changes, 1):
        # 顯示進度
        if i % 50 == 0 or i == len(all_changes):
            print(f"   處理進度: {i}/{len(all_changes)} ({i/len(all_changes)*100:.1f}%)")
        
        # 執行分類
        part_name = change.get("部件", "")
        original_text = change.get("原始文本", "")
        classification = classifier.classify_part_change(part_name, original_text)
        
        # 添加分類資訊到記錄（扁平化結構 - 選項A）
        classified_change = change.copy()
        classified_change["變更類型"] = classification["變更類型"]
        classified_change["類型說明"] = classification["類型說明"]
        classified_change["匹配關鍵字"] = ", ".join(classification["匹配關鍵字"]) if classification["匹配關鍵字"] else ""
        classified_change["分類信心度"] = classification["信心度"]
        
        classified_changes.append(classified_change)
        
        # 統計
        change_type = classification["變更類型"]
        stats[change_type] = stats.get(change_type, 0) + 1
    
    # 保存分類結果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(classified_changes, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 分類完成！")
    print(f"💾 已保存至: {output_file}")
    
    # 顯示統計
    print(f"\n📊 分類統計結果:")
    print("-" * 80)
    total = len(classified_changes)
    for change_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = count / total * 100
            bar_length = int(percentage / 2)
            bar = "█" * bar_length
            print(f"  {change_type:40} {count:4} 筆 ({percentage:5.1f}%) {bar}")
    
    print("-" * 80)
    print(f"  總計: {total} 筆")
    
    # 顯示墨西哥範例
    print(f"\n🇲🇽 墨西哥數據分類範例:")
    print("-" * 80)
    mexico_data = [item for item in classified_changes if item.get('比賽') == 'Mexico City']
    
    if mexico_data:
        # 統計墨西哥的分類
        mexico_stats = {}
        for item in mexico_data:
            change_type = item.get('變更類型', '未知')
            mexico_stats[change_type] = mexico_stats.get(change_type, 0) + 1
        
        print(f"  墨西哥總記錄: {len(mexico_data)} 筆")
        print(f"  分類分布:")
        for change_type, count in sorted(mexico_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"    • {change_type}: {count} 筆")
        
        print(f"\n  前 5 筆範例:")
        for i, item in enumerate(mexico_data[:5], 1):
            print(f"\n  {i}. {item.get('車隊')} - {item.get('車手')}")
            print(f"     部件: {item.get('部件')}")
            print(f"     分類: {item.get('變更類型')}")
            print(f"     信心度: {item.get('分類信心度'):.0%}")
            if item.get('匹配關鍵字'):
                print(f"     關鍵字: {item.get('匹配關鍵字')}")
    else:
        print(f"  ⚠️  未找到墨西哥數據")
    
    print("\n" + "=" * 80)
    print("✅ 分類作業完成")
    print("=" * 80)
    
    return classified_changes, stats


if __name__ == '__main__':
    classify_all_changes()
