#!/usr/bin/env python3
"""
方案 B：強制特徵多樣性實驗 (v3.2)
保留 8 個特徵（包含 ideal_lap）
添加參數：colsample_bytree=0.7, colsample_bylevel=0.8
目標：降低單一特徵（S2）的主導性
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


def train_v32_model(track_name):
    """
    訓練 v3.2 模型（方案 B：強制特徵多樣性）
    - 8 個特徵（包含 ideal_lap）
    - colsample_bytree=0.7（每棵樹隨機選 70% 特徵）
    - colsample_bylevel=0.8（每層隨機選 80% 特徵）
    """
    print(f"\n{'='*80}")
    print(f"訓練 v3.2: {track_name}（方案 B：強制特徵多樣性）")
    print(f"{'='*80}")
    
    # 使用 v3.0 載入數據
    trainer = TrackSpecificTrainerV3(verbose=True)
    df = trainer.load_training_data_v3(track_name, 2022, 2024)
    
    if df.empty or len(df) < 20:
        print(f"  ✗ 數據不足")
        return None
    
    # ✅ 保留所有 8 個特徵（包含 ideal_lap）
    v32_features = [
        'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex',
        'max_speed'
    ]
    
    print(f"\n[v3.2 配置] 方案 B：強制特徵多樣性")
    print(f"  特徵數量: 8 個（保留 ideal_lap）")
    print(f"  colsample_bytree: 0.7（每棵樹隨機選 70% 特徵 = 5-6 個）")
    print(f"  colsample_bylevel: 0.8（每層隨機選 80% 特徵）")
    print(f"  目標: 降低 S2 單一主導，強制模型使用多種特徵")
    
    # 手動訓練
    from sklearn.model_selection import train_test_split
    from xgboost import XGBRegressor
    
    X = df[v32_features].values
    y = df['actual_q_time'].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # ✅ v3.2 模型：添加特徵採樣參數
    model = XGBRegressor(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        colsample_bytree=0.7,      # ← 方案 B: 每棵樹隨機選 70% 特徵
        colsample_bylevel=0.8,     # ← 方案 B: 每層隨機選 80% 特徵
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
    
    feature_importances = dict(zip(v32_features, model.feature_importances_))
    
    print(f"\n訓練結果:")
    print(f"  訓練樣本: {len(X_train)}")
    print(f"  測試樣本: {len(X_test)}")
    print(f"  訓練 MAE: {train_mae:.3f}s")
    print(f"  測試 MAE: {test_mae:.3f}s")
    print(f"  測試 R²: {test_r2:.4f}")
    
    print(f"\n特徵重要性 (v3.2 強制多樣性):")
    for feature, importance in sorted(feature_importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature:<20} {importance:>10.2%}")
    
    # 儲存 v3.2 模型
    model_dir = Path('models/track_specific_v3.2')
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
        'version': 'v3.2',
        'features': v32_features,
        'config': {
            'colsample_bytree': 0.7,
            'colsample_bylevel': 0.8,
            'n_estimators': 50,
            'max_depth': 3,
            'learning_rate': 0.1
        },
        'train_date': datetime.now().isoformat()
    }
    
    model_path = model_dir / f'{track_name}.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"\n✓ v3.2 模型已儲存: {model_path}")
    
    return {
        'track': track_name,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'test_r2': test_r2,
        'feature_importances': feature_importances
    }


def predict_2025_v32(track_name):
    """使用 v3.2 模型預測 2025"""
    print(f"\n{'='*80}")
    print(f"v3.2 預測 2025: {track_name}")
    print(f"{'='*80}")
    
    # 載入 v3.2 模型
    model_path = Path(f'models/track_specific_v3.2/{track_name}.pkl')
    if not model_path.exists():
        print(f"  ✗ 找不到 v3.2 模型")
        return None
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    v32_features = model_data['features']
    
    # 使用 TrainerV3 載入 2025 數據
    trainer = TrackSpecificTrainerV3(verbose=False)
    df_2025 = trainer.load_training_data_v3(track_name, 2025, 2025)
    
    if df_2025.empty:
        print(f"  ✗ 找不到 2025 數據")
        return None
    
    print(f"  2025 樣本數: {len(df_2025)}")
    
    # 預測
    X_2025 = df_2025[v32_features].values
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


def compare_v30_vs_v32(track_name):
    """對比 v3.0 (原始) vs v3.2 (強制多樣性)"""
    print(f"\n{'='*80}")
    print(f"對比 v3.0 vs v3.2: {track_name}")
    print(f"{'='*80}")
    
    # 載入 v3.0 模型
    v30_path = Path(f'models/track_specific_v3/{track_name}.pkl')
    if not v30_path.exists():
        print(f"  ✗ 找不到 v3.0 模型")
        return
    
    with open(v30_path, 'rb') as f:
        v30_data = pickle.load(f)
    
    # 載入 v3.2 模型
    v32_path = Path(f'models/track_specific_v3.2/{track_name}.pkl')
    if not v32_path.exists():
        print(f"  ✗ 找不到 v3.2 模型")
        return
    
    with open(v32_path, 'rb') as f:
        v32_data = pickle.load(f)
    
    v30_perf = v30_data['performance']
    v32_perf = v32_data['performance']
    
    v30_feat = v30_perf['feature_importances']
    v32_feat = v32_perf['feature_importances']
    
    print(f"\n{'='*80}")
    print("【效能指標對比】")
    print(f"{'='*80}")
    print(f"\n{'指標':<25} {'v3.0 (原始)':<20} {'v3.2 (多樣性)':<20} {'變化':<15} {'改善'}")
    print("-"*100)
    
    # R² 對比
    r2_diff = v32_perf['test_r2'] - v30_perf['test_r2']
    r2_pct = (r2_diff / v30_perf['test_r2']) * 100 if v30_perf['test_r2'] != 0 else 0
    r2_trend = "✅ 改善" if r2_diff > 0 else "❌ 下降" if r2_diff < -0.01 else "→ 持平"
    print(f"{'測試 R²':<25} {v30_perf['test_r2']:>19.4f} {v32_perf['test_r2']:>19.4f} {r2_diff:>+14.4f} {r2_trend}")
    
    # MAE 對比
    mae_diff = v32_perf['test_mae'] - v30_perf['test_mae']
    mae_pct = (mae_diff / v30_perf['test_mae']) * 100 if v30_perf['test_mae'] != 0 else 0
    mae_trend = "✅ 改善" if mae_diff < 0 else "❌ 惡化" if mae_diff > 0.02 else "→ 持平"
    print(f"{'測試 MAE (秒)':<25} {v30_perf['test_mae']:>19.3f} {v32_perf['test_mae']:>19.3f} {mae_diff:>+14.3f} {mae_trend}")
    
    print(f"{'訓練 MAE (秒)':<25} {v30_perf['train_mae']:>19.3f} {v32_perf['train_mae']:>19.3f} {v32_perf['train_mae']-v30_perf['train_mae']:>+14.3f}")
    
    print(f"\n{'='*80}")
    print("【特徵重要性對比】")
    print(f"{'='*80}")
    print(f"\n{'特徵':<20} {'v3.0 (原始)':<15} {'v3.2 (多樣性)':<15} {'變化':<12} {'趨勢'}")
    print("-"*80)
    
    all_features = set(v30_feat.keys()) | set(v32_feat.keys())
    feature_order = ['ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap', 
                     'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed']
    
    for feature in feature_order:
        if feature in all_features:
            v30_imp = v30_feat.get(feature, 0)
            v32_imp = v32_feat.get(feature, 0)
            diff = v32_imp - v30_imp
            
            if abs(diff) > 0.10:
                trend = "🔴 大幅" if diff < 0 else "🟢 大幅"
            elif abs(diff) > 0.05:
                trend = "⚠️  中度" if diff < 0 else "✅ 中度"
            else:
                trend = "→ 相近"
            
            print(f"{feature:<20} {v30_imp:>14.2%} {v32_imp:>14.2%} {diff:>+11.2%} {trend}")
    
    # 分析 S2 主導性變化
    print(f"\n{'='*80}")
    print("【關鍵發現】")
    print(f"{'='*80}")
    
    s2_v30 = v30_feat.get('ideal_s2', 0)
    s2_v32 = v32_feat.get('ideal_s2', 0)
    s2_change = s2_v32 - s2_v30
    
    if track_name == 'Abu Dhabi':
        print(f"\n阿布達比 S2 主導性分析：")
        print(f"  v3.0: S2 占比 {s2_v30:.2%}（過度主導）")
        print(f"  v3.2: S2 占比 {s2_v32:.2%}（強制多樣性後）")
        print(f"  變化: {s2_change:+.2%}")
        
        if abs(s2_change) < 0.05:
            print(f"  結論: ⚠️  強制特徵採樣效果有限，S2 仍然主導")
        elif s2_change < -0.10:
            print(f"  結論: ✅ 成功降低 S2 主導性")
        else:
            print(f"  結論: ❌ S2 主導性未改善")
    
    print(f"\n整體評估:")
    if r2_diff > 0.02 and mae_diff < 0:
        print(f"  ✅ 方案 B 成功！R² 提升且 MAE 降低")
    elif r2_diff > 0:
        print(f"  ✅ 方案 B 有效，R² 提升 {r2_pct:.1f}%")
    elif abs(r2_diff) < 0.02:
        print(f"  → 方案 B 效果中性，效能持平")
    else:
        print(f"  ❌ 方案 B 無效，效能下降 {abs(r2_pct):.1f}%")


def main():
    """主程式"""
    print("="*80)
    print("F1 Track-Specific Prediction v3.2")
    print("方案 B：強制特徵多樣性（colsample_bytree=0.7）")
    print("="*80)
    
    tracks = ['Mexico', 'Abu Dhabi']
    
    results = {
        'config': {
            'version': 'v3.2',
            'strategy': '方案 B：強制特徵多樣性',
            'changes': {
                'colsample_bytree': 0.7,
                'colsample_bylevel': 0.8,
                'features': 8,
                'note': '保留所有 8 個特徵（包含 ideal_lap）'
            }
        },
        'training': {},
        'prediction_2025': {},
        'comparison': {}
    }
    
    # 訓練 v3.2
    for track in tracks:
        train_result = train_v32_model(track)
        if train_result:
            results['training'][track] = {
                'test_r2': float(train_result['test_r2']),
                'test_mae': float(train_result['test_mae']),
                'feature_importances': {k: float(v) for k, v in train_result['feature_importances'].items()}
            }
    
    # 預測 2025（如果有數據）
    for track in tracks:
        pred_result = predict_2025_v32(track)
        if pred_result:
            results['prediction_2025'][track] = {
                'spearman': float(pred_result['spearman']),
                'mae': float(pred_result['mae']),
                'r2': float(pred_result['r2'])
            }
    
    # 對比 v3.0 vs v3.2
    for track in tracks:
        compare_v30_vs_v32(track)
    
    # 儲存結果
    output_file = Path('v3.2_feature_diversity_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✓ 完成！結果已儲存: {output_file}")
    print(f"{'='*80}")
    
    print(f"\n【下一步】")
    print(f"  - 如果 v3.2 效果不佳，考慮方案 C（增加交互特徵）")
    print(f"  - 如果 v3.2 效果良好，可批次訓練其他賽道")


if __name__ == '__main__':
    main()
