"""
重新訓練 Las Vegas 賽道模型 (V3.8)
修復特徵重要性異常問題
"""

import sys
import importlib.util
from pathlib import Path

# 動態載入 v3.8 訓練器
spec = importlib.util.spec_from_file_location(
    "batch_train_all_tracks_v3_8",
    "batch_train_all_tracks_v3.8.py"
)
v38_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v38_module)
BatchTrainerV3_8 = v38_module.BatchTrainerV3_8

def retrain_las_vegas():
    """重新訓練 Las Vegas 賽道"""
    print("=" * 70)
    print("重新訓練 Las Vegas 賽道模型 (V3.8)")
    print("=" * 70)
    
    trainer = BatchTrainerV3_8(trials=500, cv_folds=3, workers=1)
    
    # 刪除舊模型
    import os
    old_model = "models/track_specific_v3.8/Las Vegas.pkl"
    if os.path.exists(old_model):
        os.remove(old_model)
        print(f"\n[已刪除] {old_model}")
    
    # 重新訓練
    print("\n[開始訓練] Las Vegas...")
    result = trainer.train_single_track("Las Vegas")
    
    if result:
        print("\n" + "=" * 70)
        print("訓練結果")
        print("=" * 70)
        print(f"賽道: {result['track']}")
        print(f"樣本數: {result['sample_count']}")
        print(f"訓練 MAE: {result['train_mae']:.4f}")
        print(f"訓練 R²: {result['train_r2']:.4f}")
        print(f"交叉驗證 MAE: {result['cv_mae']:.4f}")
        
        print(f"\n前五特徵重要性:")
        if result['feature_importance']:
            top5 = sorted(result['feature_importance'].items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (feat, imp) in enumerate(top5, 1):
                print(f"  {i}. {feat:30s}: {imp*100:6.2f}%")
        else:
            print("  [警告] 無特徵重要性數據")
        
        # 更新 v3.8_training_results.json
        import json
        from pathlib import Path
        
        results_file = Path("v3.8_training_results.json")
        if results_file.exists():
            with open(results_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
            
            # 更新 Las Vegas 結果
            all_results['results']['Las Vegas'] = result
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            
            print(f"\n[已更新] {results_file}")
        
        return result
    else:
        print("\n[錯誤] 訓練失敗")
        return None

if __name__ == "__main__":
    retrain_las_vegas()
