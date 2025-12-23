#!/usr/bin/env python3
"""
簡化版 v3.1 訓練程式
直接使用 TrainerV3，只修改特徵列表移除 ideal_lap
"""
import sys
import json
import pickle
from pathlib import Path
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score

# 設定輸出編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 導入 v3.0 trainer
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


def train_v31_model(track_name):
    """
    訓練 v3.1 模型（移除 ideal_lap）
    使用 TrainerV3 的載入功能，但手動訓練移除 ideal_lap 的版本
    """
    print(f"\n{'='*80}")
    print(f"訓練 v3.1: {track_name}（移除 ideal_lap）")
    print(f"{'='*80}")
    
    # 使用 v3.0 載入數據
    trainer = TrackSpecificTrainerV3(verbose=True)
    df = trainer.load_training_data_v3(track_name, 2022, 2024)
    
    if df.empty or len(df) < 20:
        print(f"  ✗ 數據不足")
        return None
    
    # ✅ v3.1 特徵：移除 ideal_lap
    v31_features = [
        'ideal_s1', 'ideal_s2', 'ideal_s3',
        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex',
        'max_speed'
    ]
    
    print(f"\n[v3.1 特徵] 7 個特徵（移除 ideal_lap）:")
    for f in v31_features:
        print(f"  - {f}")
    
    # 手動訓練
    from sklearn.model_selection import train_test_split
    from xgboost import XGBRegressor
    
    X = df[v31_features].values
    y = df['actual_q_time'].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    model = XGBRegressor(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
        verbosity=0
    )
    
    model.fit(X_train, y_train)
    
    # 評估
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    feature_importances = dict(zip(v31_features, model.feature_importances_))
    
    print(f"\n訓練結果:")
    print(f"  訓練樣本: {len(X_train)}")
    print(f"  測試樣本: {len(X_test)}")
    print(f"  訓練 MAE: {train_mae:.3f}s")
    print(f"  測試 MAE: {test_mae:.3f}s")
    print(f"  測試 R²: {test_r2:.4f}")
    
    print(f"\n特徵重要性:")
    for feature, importance in sorted(feature_importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature:<20} {importance:>10.2%}")
    
    # 儲存 v3.1 模型
    model_dir = Path('models/track_specific_v3.1')
    model_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    model_data = {
        'model': model,
        'performance': {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'test_r2': test_r2,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'samples': len(df),
            'feature_importances': feature_importances
        },
        'track': track_name,
        'version': 'v3.1',
        'features': v31_features,
        'train_date': datetime.now().isoformat()
    }
    
    model_path = model_dir / f'{track_name}.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"\n✓ v3.1 模型已儲存: {model_path}")
    
    return {
        'track': track_name,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'test_r2': test_r2,
        'feature_importances': feature_importances
    }


def predict_2025_v31(track_name):
    """使用 v3.1 模型預測 2025"""
    print(f"\n{'='*80}")
    print(f"v3.1 預測 2025: {track_name}")
    print(f"{'='*80}")
    
    # 載入 v3.1 模型
    model_path = Path(f'models/track_specific_v3.1/{track_name}.pkl')
    if not model_path.exists():
        print(f"  ✗ 找不到 v3.1 模型")
        return None
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    v31_features = model_data['features']
    
    # 使用 TrainerV3 載入 2025 數據
    trainer = TrackSpecificTrainerV3(verbose=False)
    df_2025 = trainer.load_training_data_v3(track_name, 2025, 2025)
    
    if df_2025.empty:
        print(f"  ✗ 找不到 2025 數據")
        return None
    
    print(f"  2025 樣本數: {len(df_2025)}")
    
    # 預測
    X_2025 = df_2025[v31_features].values
    y_actual = df_2025['actual_q_time'].values
    
    y_pred = model.predict(X_2025)
    
    # 評估
    mae = mean_absolute_error(y_actual, y_pred)
    r2 = r2_score(y_actual, y_pred)
    
    # 排名相關性
    import pandas as pd
    df_2025['pred_time'] = y_pred
    df_2025['actual_rank'] = df_2025['actual_q_time'].rank()
    df_2025['pred_rank'] = df_2025['pred_time'].rank()
    
    spearman_corr, _ = spearmanr(df_2025['actual_rank'], df_2025['pred_rank'])
    
    print(f"\n2025 預測結果:")
    print(f"  Spearman 相關性: {spearman_corr:.4f}")
    print(f"  MAE: {mae:.4f}s")
    print(f"  R²: {r2:.4f}")
    
    return {
        'track': track_name,
        'spearman': spearman_corr,
        'mae': mae,
        'r2': r2
    }


def compare_v30_vs_v31(track_name):
    """對比 v3.0 vs v3.1"""
    print(f"\n{'='*80}")
    print(f"對比 v3.0 vs v3.1: {track_name}")
    print(f"{'='*80}")
    
    # 載入 v3.0 模型
    v30_path = Path(f'models/track_specific_v3/{track_name}.pkl')
    with open(v30_path, 'rb') as f:
        v30_data = pickle.load(f)
    
    # 載入 v3.1 模型
    v31_path = Path(f'models/track_specific_v3.1/{track_name}.pkl')
    with open(v31_path, 'rb') as f:
        v31_data = pickle.load(f)
    
    v30_perf = v30_data['performance']
    v31_perf = v31_data['performance']
    
    v30_feat = v30_perf['feature_importances']
    v31_feat = v31_perf['feature_importances']
    
    print(f"\n{'指標':<20} {'v3.0 (8特徵)':<20} {'v3.1 (7特徵)':<20} {'變化'}")
    print("-"*80)
    print(f"{'測試 R²':<20} {v30_perf['test_r2']:>19.4f} {v31_perf['test_r2']:>19.4f} {v31_perf['test_r2']-v30_perf['test_r2']:>+10.4f}")
    print(f"{'測試 MAE (秒)':<20} {v30_perf['test_mae']:>19.3f} {v31_perf['test_mae']:>19.3f} {v31_perf['test_mae']-v30_perf['test_mae']:>+10.3f}")
    print(f"{'訓練樣本':<20} {v30_perf['train_samples']:>19} {v31_perf['train_samples']:>19} {v31_perf['train_samples']-v30_perf['train_samples']:>+10}")
    
    print(f"\n特徵重要性對比:")
    print(f"{'特徵':<20} {'v3.0':<15} {'v3.1':<15} {'變化'}")
    print("-"*80)
    
    for feature in ['ideal_s1', 'ideal_s2', 'ideal_s3', 'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed']:
        v30_imp = v30_feat.get(feature, 0)
        v31_imp = v31_feat.get(feature, 0)
        diff = v31_imp - v30_imp
        print(f"{feature:<20} {v30_imp:>14.2%} {v31_imp:>14.2%} {diff:>+10.2%}")
    
    # v3.0 的 ideal_lap
    if 'ideal_lap' in v30_feat:
        print(f"{'ideal_lap (移除)':<20} {v30_feat['ideal_lap']:>14.2%} {'N/A':<15} {'已移除'}")


def main():
    """主程式"""
    print("="*80)
    print("F1 Track-Specific Prediction v3.1")
    print("方案 A：移除 ideal_lap 特徵")
    print("="*80)
    
    tracks = ['Mexico', 'Abu Dhabi']
    
    results = {}
    
    # 訓練 v3.1
    for track in tracks:
        train_result = train_v31_model(track)
        if train_result:
            results[f'{track}_train'] = train_result
    
    # 預測 2025
    for track in tracks:
        pred_result = predict_2025_v31(track)
        if pred_result:
            results[f'{track}_2025'] = pred_result
    
    # 對比 v3.0 vs v3.1
    for track in tracks:
        compare_v30_vs_v31(track)
    
    # 儲存結果
    output_file = Path('v3.1_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✓ 完成！結果已儲存: {output_file}")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
