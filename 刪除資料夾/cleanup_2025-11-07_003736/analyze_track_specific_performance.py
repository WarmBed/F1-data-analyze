"""
檢查當前模型在不同賽道上的預測表現
驗證「賽道混合訓練」的問題
"""
import pickle
import numpy as np
import pandas as pd
from collections import defaultdict
from CLI_modules.cli.prediction.xgboost_trainer import XGBoostTrainer

def analyze_track_specific_performance():
    print("=" * 70)
    print("賽道特定性能分析")
    print("=" * 70)
    
    # 載入訓練數據
    trainer = XGBoostTrainer(verbose=False)
    print("\n正在載入 2018-2024 訓練數據...")
    training_data = trainer.load_training_data(
        start_year=2018,
        end_year=2024,
        exclude_wet=True
    )
    
    X_train, y_train = trainer.prepare_features(training_data)
    
    # 載入模型
    print("載入 XGBoost 模型...")
    with open('models/xgboost_pure_fp3.pkl', 'rb') as f:
        model = pickle.load(f)
    
    # 預測訓練集
    y_pred = model.predict(X_train)
    
    # 按賽道分組分析
    print("\n按賽道分析預測性能:")
    print(f"訓練數據: {len(training_data)} 樣本")
    print(f"特徵數據: {len(X_train)} 樣本")
    print(f"目標數據: {len(y_train)} 樣本")
    print("-" * 70)
    
    # 使用 y_train 的實際長度
    track_stats = defaultdict(lambda: {
        'actual': [],
        'predicted': [],
        'errors': []
    })
    
    # y_train 可能是經過清洗後的，需要找到對應的原始數據
    # 使用 X_train 的索引來對應
    valid_indices = X_train.index if hasattr(X_train, 'index') else range(len(X_train))
    
    for idx in range(len(y_train)):
        # 找到對應的原始數據行
        orig_idx = valid_indices[idx] if hasattr(valid_indices, '__getitem__') else idx
        if orig_idx < len(training_data):
            row = training_data.iloc[orig_idx]
            race = row['race']
            actual = y_train.iloc[idx] if hasattr(y_train, 'iloc') else y_train[idx]
            pred = y_pred[idx]
            error = pred - actual
            
            track_stats[race]['actual'].append(actual)
            track_stats[race]['predicted'].append(pred)
            track_stats[race]['errors'].append(error)
    
    # 計算每個賽道的統計
    results = []
    for race, stats in track_stats.items():
        actual = np.array(stats['actual'])
        predicted = np.array(stats['predicted'])
        errors = np.array(stats['errors'])
        
        mae = np.abs(errors).mean()
        
        results.append({
            'race': race,
            'count': len(actual),
            'actual_mean': actual.mean(),
            'actual_range': f"{actual.min():.1f}-{actual.max():.1f}s",
            'pred_mean': predicted.mean(),
            'pred_range': f"{predicted.min():.1f}-{predicted.max():.1f}s",
            'mae': mae,
            'bias': errors.mean()  # 正值=高估，負值=低估
        })
    
    # 按實際平均時間排序
    results.sort(key=lambda x: x['actual_mean'])
    
    # 顯示結果
    print(f"\n{'賽道':<20} {'樣本':<6} {'實際平均':<10} {'預測平均':<10} {'MAE':<8} {'偏差':<8}")
    print("-" * 80)
    
    for r in results:
        bias_str = f"{r['bias']:+.2f}s"
        print(f"{r['race']:<20} {r['count']:<6} {r['actual_mean']:>8.2f}s {r['pred_mean']:>8.2f}s {r['mae']:>6.2f}s {bias_str:>8}")
    
    # 分析偏差模式
    print("\n" + "=" * 70)
    print("偏差模式分析:")
    print("=" * 70)
    
    # 快速賽道 vs 慢速賽道
    fast_tracks = [r for r in results if r['actual_mean'] < 75]
    slow_tracks = [r for r in results if r['actual_mean'] > 95]
    mid_tracks = [r for r in results if 75 <= r['actual_mean'] <= 95]
    
    print(f"\n快速賽道 (< 75s): {len(fast_tracks)} 條")
    if fast_tracks:
        fast_bias = np.mean([r['bias'] for r in fast_tracks])
        fast_mae = np.mean([r['mae'] for r in fast_tracks])
        print(f"  平均偏差: {fast_bias:+.2f}s ({'高估' if fast_bias > 0 else '低估'})")
        print(f"  平均 MAE: {fast_mae:.2f}s")
    
    print(f"\n中速賽道 (75-95s): {len(mid_tracks)} 條")
    if mid_tracks:
        mid_bias = np.mean([r['bias'] for r in mid_tracks])
        mid_mae = np.mean([r['mae'] for r in mid_tracks])
        print(f"  平均偏差: {mid_bias:+.2f}s ({'高估' if mid_bias > 0 else '低估'})")
        print(f"  平均 MAE: {mid_mae:.2f}s")
    
    print(f"\n慢速賽道 (> 95s): {len(slow_tracks)} 條")
    if slow_tracks:
        slow_bias = np.mean([r['bias'] for r in slow_tracks])
        slow_mae = np.mean([r['mae'] for r in slow_tracks])
        print(f"  平均偏差: {slow_bias:+.2f}s ({'高估' if slow_bias > 0 else '低估'})")
        print(f"  平均 MAE: {slow_mae:.2f}s")
    
    # 結論
    print("\n" + "=" * 70)
    print("結論:")
    print("=" * 70)
    
    if fast_tracks and slow_tracks:
        if fast_bias > 1 and slow_bias < -1:
            print("⚠️  模型存在系統性偏差:")
            print("   → 快速賽道被高估（預測過慢）")
            print("   → 慢速賽道被低估（預測過快）")
            print("   → 原因: 模型預測集中在平均值附近")
            print("")
            print("💡 建議: 改用相對時間建模或賽道特定模型")
        elif abs(fast_bias) < 0.5 and abs(slow_bias) < 0.5:
            print("✅ 模型在不同速度賽道上表現均衡")
        else:
            print(f"⚠️  模型存在不對稱偏差:")
            print(f"   快速賽道偏差: {fast_bias:+.2f}s")
            print(f"   慢速賽道偏差: {slow_bias:+.2f}s")

if __name__ == '__main__':
    analyze_track_specific_performance()
