"""
生成 v3.8.1 模型對 2025 年的預測
"""

import json
import pickle
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

# 添加模組路徑
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3

def load_v381_model(track_name: str):
    """載入 v3.8.1 模型"""
    # v3.8.1 模型保存在 track_specific_v3 目錄中
    model_file = Path(f"models/track_specific_v3/{track_name}.pkl")
    if not model_file.exists():
        print(f"❌ 找不到模型檔案: {model_file}")
        return None
    
    print(f"  載入模型: {model_file}")
    with open(model_file, 'rb') as f:
        model_data = pickle.load(f)
    
    return model_data['model']

def predict_2025(trainer, model, track_name: str):
    """對 2025 年進行預測"""
    print(f"\n預測 {track_name} 2025...")
    
    # 載入 2025 年數據
    df_2025 = trainer.load_training_data_v3(track_name, start_year=2025, end_year=2025)
    
    if df_2025 is None or df_2025.empty:
        print(f"  ❌ 找不到 2025 年數據")
        return None
    
    # 提取特徵和目標
    feature_cols = [
        'ideal_lap', 'ideal_s1', 'ideal_s2', 'ideal_s3',
        's1_lap_ratio', 's2_lap_ratio', 's3_lap_ratio',
        'max_speed', 'max_speed_lap_ratio', 'max_speed_s2_ratio',
        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex',
        'sector_cv', 'speed_consistency',
        'fp3_gap_to_fastest', 'fp3_relative_position',
        'driver_historical_track_performance', 'driver_track_performance_gap'
    ]
    
    X_2025 = df_2025[feature_cols]
    y_actual = df_2025['q_time'].values
    drivers = df_2025['driver'].values
    
    # 預測
    y_pred = model.predict(X_2025)
    
    # 計算排名
    actual_ranks = pd.Series(y_actual).rank(method='min').astype(int).values
    pred_ranks = pd.Series(y_pred).rank(method='min').astype(int).values
    
    # 組織結果
    predictions = []
    for i, driver in enumerate(drivers):
        predictions.append({
            'driver': driver,
            'actual_q_time': float(y_actual[i]),
            'predicted_time': float(y_pred[i]),
            'actual_rank': int(actual_ranks[i]),
            'predicted_rank': int(pred_ranks[i]),
            'rank_diff': int(abs(actual_ranks[i] - pred_ranks[i]))
        })
    
    # 排序（按實際時間）
    predictions.sort(key=lambda x: x['actual_q_time'])
    
    # 計算統計數據
    mae = np.mean(np.abs(y_actual - y_pred))
    from scipy.stats import spearmanr
    spearman_corr, _ = spearmanr(y_actual, y_pred)
    
    # 計算 R²
    ss_res = np.sum((y_actual - y_pred) ** 2)
    ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    print(f"  ✅ MAE: {mae:.3f}s, R²: {r2:.4f}, Spearman: {spearman_corr:.4f}")
    
    return {
        'track': track_name,
        'mae': float(mae),
        'r2': float(r2),
        'spearman': float(spearman_corr),
        'predictions': predictions
    }

def main():
    print("=" * 60)
    print("生成 v3.8.1 模型對 2025 年的預測")
    print("=" * 60)
    
    # 載入訓練結果以獲取賽道列表
    with open('v3.8.1_training_results.json', 'r', encoding='utf-8') as f:
        training_results = json.load(f)
    
    tracks = list(training_results['results'].keys())
    print(f"\n找到 {len(tracks)} 個賽道: {', '.join(tracks)}")
    
    # 初始化 trainer
    trainer = TrackSpecificTrainerV3(verbose=True)
    
    # 對每個賽道進行預測
    all_results = {}
    
    for track in tracks:
        try:
            # 載入模型
            model = load_v381_model(track)
            if model is None:
                continue
            
            # 預測 2025
            result = predict_2025(trainer, model, track)
            if result:
                # 使用 race_id 作為鍵（與 v3.5 格式一致）
                race_id = f"2025_{track}"
                all_results[race_id] = result
                
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 保存結果
    output_file = 'v3.8.1_2025_predictions.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 預測完成！結果已保存至: {output_file}")
    print(f"   成功預測 {len(all_results)} 個賽道")

if __name__ == "__main__":
    main()
