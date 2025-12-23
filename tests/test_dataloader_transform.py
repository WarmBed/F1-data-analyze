#!/usr/bin/env python3
"""
測試 QualifyingPredictionDataLoader 的數據轉換功能
驗證 _process_data() 是否正確調用 _transform_data_for_display()
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.gui.qualifying_prediction.qualifying_prediction_data_loader import QualifyingPredictionDataLoader
from PyQt5.QtWidgets import QApplication
import json


def main():
    app = QApplication(sys.argv)
    
    print("=" * 70)
    print("測試 QualifyingPredictionDataLoader 數據轉換功能")
    print("=" * 70)
    
    # 創建 DataLoader
    loader = QualifyingPredictionDataLoader(
        year="2025",
        race="Mexico"
    )
    loader._debug_enabled = True  # 啟用調試輸出
    
    # 讀取 JSON 檔案
    json_path = "json/qualifying_prediction_2025_Mexico.json"
    print(f"\n📂 讀取 JSON 檔案: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print(f"✅ JSON 讀取成功，包含 {len(raw_data['predictions'])} 位車手")
    
    # 檢查原始數據
    print("\n" + "=" * 70)
    print("原始數據檢查（前 3 位車手）:")
    print("=" * 70)
    for i, pred in enumerate(raw_data['predictions'][:3], 1):
        print(f"\n{i}. {pred['driver']}:")
        print(f"   actual_q_time: {pred.get('actual_q_time')}")
        print(f"   actual_q_rank: {pred.get('actual_q_rank', 'KEY NOT FOUND')}")
        print(f"   fp3_predicted_rank: {pred.get('fp3_predicted_rank', 'KEY NOT FOUND')}")
    
    # 測試 _process_data() 方法
    print("\n" + "=" * 70)
    print("測試 _process_data() 方法:")
    print("=" * 70)
    
    processed_data = loader._process_data(raw_data)
    
    # 檢查處理後的數據
    print("\n" + "=" * 70)
    print("處理後數據檢查（前 3 位車手）:")
    print("=" * 70)
    for i, pred in enumerate(processed_data['predictions'][:3], 1):
        print(f"\n{i}. {pred['driver']}:")
        print(f"   actual_q_time: {pred.get('actual_q_time')}")
        print(f"   actual_q_rank: {pred.get('actual_q_rank', 'KEY NOT FOUND')}")  # ← 應該已添加
        print(f"   fp3_predicted_rank: {pred.get('fp3_predicted_rank', 'KEY NOT FOUND')}")  # ← 應該已添加
    
    # 驗證所有車手的 Q 名次
    print("\n" + "=" * 70)
    print("完整 Q 名次排行榜:")
    print("=" * 70)
    
    # 按 Q 名次排序
    sorted_by_q_rank = sorted(
        [p for p in processed_data['predictions'] if p.get('actual_q_rank') is not None],
        key=lambda x: x['actual_q_rank']
    )
    
    print(f"\n{'排名':<6} {'車手':<6} {'Q 時間':<12} {'Q 名次':<8} {'FP3 預測名次':<12}")
    print("-" * 60)
    
    for pred in sorted_by_q_rank[:10]:  # 顯示前 10 名
        q_rank = pred.get('actual_q_rank', 'N/A')
        fp3_rank = pred.get('fp3_predicted_rank', 'N/A')
        actual_q_time = pred.get('actual_q_time', 'N/A')
        
        print(f"{pred['rank']:<6} {pred['driver']:<6} {actual_q_time:<12.3f} {q_rank:<8} {fp3_rank:<12}")
    
    # 測試結果
    print("\n" + "=" * 70)
    print("測試結果:")
    print("=" * 70)
    
    has_q_rank = all(
        p.get('actual_q_rank') is not None 
        for p in processed_data['predictions'] 
        if p.get('actual_q_time') is not None
    )
    
    has_fp3_rank = all(
        p.get('fp3_predicted_rank') is not None 
        for p in processed_data['predictions']
    )
    
    if has_q_rank and has_fp3_rank:
        print("✅ 測試通過：所有車手都有 Q 名次和 FP3 預測名次")
        print("✅ _process_data() 正確調用了 _transform_data_for_display()")
        return 0
    else:
        print("❌ 測試失敗：部分車手缺少計算欄位")
        if not has_q_rank:
            print("   - 缺少 Q 名次")
        if not has_fp3_rank:
            print("   - 缺少 FP3 預測名次")
        return 1


if __name__ == "__main__":
    sys.exit(main())
