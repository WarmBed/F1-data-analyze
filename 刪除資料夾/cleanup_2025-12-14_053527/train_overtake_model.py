#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F82 超車預測模型訓練腳本
使用精簡輸出避免 VSC 過載
"""

import sys
import os

# 確保路徑正確
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 50)
    print("[F82] 超車預測模型訓練")
    print("=" * 50)
    
    try:
        print("\n[1/4] 載入模組...")
        from CLI_modules.cli.prediction.overtake_prediction.model_trainer import run_f82_model_training
        print("      OK")
        
        print("\n[2/4] 準備數據...")
        print("[3/4] 訓練模型 (請稍候)...")
        
        result = run_f82_model_training(
            version='v3',
            verbose=False  # 關閉詳細輸出
        )
        
        print("[4/4] 完成!")
        
        print("\n" + "=" * 50)
        print("[F82] 訓練結果")
        print("=" * 50)
        
        if result:
            # 從 summary 結構中提取 report
            report = result.get('report', {})
            
            print(f"\n模型指標:")
            metrics = report.get('metrics', {})
            if metrics:
                print(f"  - ROC-AUC: {metrics.get('roc_auc', 0):.4f}")
                print(f"  - Accuracy: {metrics.get('accuracy', 0):.4f}")
                print(f"  - Precision: {metrics.get('precision', 0):.4f}")
                print(f"  - Recall: {metrics.get('recall', 0):.4f}")
                print(f"  - F1 Score: {metrics.get('f1_score', 0):.4f}")
            else:
                print("  (無指標數據)")
            
            print(f"\n交叉驗證:")
            cv = report.get('cross_validation', {})
            if cv:
                print(f"  - CV Mean AUC: {cv.get('cv_mean_auc', 0):.4f}")
                print(f"  - CV Std: {cv.get('cv_std_auc', 0):.4f}")
            else:
                print("  (無交叉驗證數據)")
            
            print(f"\n特徵重要性 (Top 5):")
            importance = report.get('feature_importance', [])
            if importance:
                for i, feat in enumerate(importance[:5]):
                    print(f"  {i+1}. {feat['feature']}: {feat['importance']:.4f}")
            else:
                # 嘗試從檔案讀取
                import pandas as pd
                from pathlib import Path
                importance_file = Path('models/overtake_prediction/feature_importance_v2.csv')
                if importance_file.exists():
                    df = pd.read_csv(importance_file)
                    for i, row in df.head(5).iterrows():
                        print(f"  {i+1}. {row['feature']}: {row['importance']:.4f}")
                else:
                    print("  (無特徵重要性數據)")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] 訓練失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
