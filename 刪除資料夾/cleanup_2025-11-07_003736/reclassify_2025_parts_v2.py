#!/usr/bin/env python3
"""
重新分類 2025 F1 Parts Changes - 使用 V2.0 優化分類器
目的：提升分類準確率、信心度標準、資料品質
"""
import json
import sys
from pathlib import Path
from upgrade_classifier_v2 import UpgradeClassifierV2
from collections import Counter


def reclassify_2025_parts():
    """重新分類 2025 年部件變更"""
    
    # 載入現有資料
    input_file = "2025_f1_parts_changes_classified.json"
    output_file = "2025_f1_parts_changes_v2_classified.json"
    
    print(f"\n{'='*100}")
    print(f"重新分類 2025 F1 Parts Changes - V2.0")
    print(f"{'='*100}\n")
    
    if not Path(input_file).exists():
        print(f"❌ 找不到輸入檔案: {input_file}")
        return False
    
    with open(input_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    print(f"✅ 載入 {len(original_data)} 筆原始記錄")
    
    # 統計原始分類
    original_types = Counter([r.get("變更類型", "未知") for r in original_data])
    print(f"\n原始分類分佈:")
    for type_name, count in sorted(original_types.items(), key=lambda x: -x[1]):
        percentage = count / len(original_data) * 100
        print(f"  {type_name}: {count} 筆 ({percentage:.2f}%)")
    
    # 初始化 V2 分類器
    classifier = UpgradeClassifierV2()
    
    # 重新分類（含去重）
    print(f"\n🔄 執行重新分類（含去重、前處理、正規化）...")
    reclassified_data = classifier.classify_batch(original_data, remove_duplicates=True)
    
    print(f"✅ 去重後剩餘 {len(reclassified_data)} 筆記錄")
    
    # 統計新分類
    new_types = Counter([r.get("變更類型", "未知") for r in reclassified_data])
    print(f"\nV2.0 分類分佈:")
    for type_name, count in sorted(new_types.items(), key=lambda x: -x[1]):
        percentage = count / len(reclassified_data) * 100
        print(f"  {type_name}: {count} 筆 ({percentage:.2f}%)")
    
    # 獲取統計資訊
    stats = classifier.get_classification_stats(reclassified_data)
    print(f"\n統計資訊:")
    print(f"  總記錄數: {stats['總記錄數']}")
    print(f"  平均信心度: {stats['平均信心度']:.2f}")
    print(f"  低信心度記錄 (<0.70): {stats['低信心度記錄']} 筆")
    
    # 信心度分佈
    confidences = [r.get("分類信心度", 0.0) for r in reclassified_data]
    confidence_bins = {
        "0.95+": sum(1 for c in confidences if c >= 0.95),
        "0.90-0.94": sum(1 for c in confidences if 0.90 <= c < 0.95),
        "0.80-0.89": sum(1 for c in confidences if 0.80 <= c < 0.90),
        "0.70-0.79": sum(1 for c in confidences if 0.70 <= c < 0.80),
        "0.60-0.69": sum(1 for c in confidences if 0.60 <= c < 0.70),
        "<0.60": sum(1 for c in confidences if c < 0.60)
    }
    
    print(f"\n信心度分佈:")
    for bin_range, count in confidence_bins.items():
        percentage = count / len(reclassified_data) * 100 if reclassified_data else 0
        print(f"  {bin_range}: {count} 筆 ({percentage:.2f}%)")
    
    # 比較變化
    print(f"\n分類變化分析:")
    changed_count = 0
    for i, (orig, new) in enumerate(zip(original_data, reclassified_data[:len(original_data)])):
        orig_type = orig.get("變更類型", "")
        new_type = new.get("變更類型", "")
        if orig_type != new_type:
            changed_count += 1
    
    print(f"  變更的記錄: {changed_count} 筆 ({changed_count/len(original_data)*100:.2f}%)")
    
    # 儲存結果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reclassified_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 重新分類完成！")
    print(f"📄 輸出檔案: {output_file}")
    
    # 顯示低信心度樣本
    if stats['低信心度記錄'] > 0:
        print(f"\n⚠️  低信心度記錄範例 (前 5 筆):")
        low_confidence_samples = [
            r for r in reclassified_data 
            if r.get("分類信心度", 1.0) < 0.70
        ][:5]
        
        for i, sample in enumerate(low_confidence_samples, 1):
            print(f"\n  {i}. {sample.get('部件', 'N/A')}")
            print(f"     分類: {sample.get('變更類型', 'N/A')}")
            print(f"     信心度: {sample.get('分類信心度', 0):.2f}")
            print(f"     關鍵字: {sample.get('匹配關鍵字', 'N/A')}")
    
    # 顯示 NOISE 樣本
    noise_samples = [r for r in reclassified_data if r.get("變更類型") == "噪音 (Noise)"]
    if noise_samples:
        print(f"\n🔇 NOISE 類別範例 (前 5 筆):")
        for i, sample in enumerate(noise_samples[:5], 1):
            print(f"  {i}. {sample.get('部件', 'N/A')}")
    
    return True


if __name__ == '__main__':
    success = reclassify_2025_parts()
    sys.exit(0 if success else 1)
