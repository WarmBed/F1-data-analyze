#!/usr/bin/env python3
"""
測試 v3.0 模型在 2025 Mexico 的預測效果
"""
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

def load_2025_data():
    """載入 2025 Mexico 數據"""
    # FP3→Q 數據
    fp_q_file = 'json/predictionJSON/fp_q_data_2025_20_20251102_221403.json'
    with open(fp_q_file, 'r', encoding='utf-8') as f:
        fp_q_data = json.load(f)
    
    # 彎角數據（需要生成）
    corner_file = 'json/all_drivers_cornering_analysis_2025_Mexico_FP3.json'
    if not Path(corner_file).exists():
        print(f"ERROR: 找不到 2025 彎角數據")
        print(f"請執行: python f1_analysis_modular_main.py -f 47 -y 2025 -r Mexico -s FP3")
        return None, None
    
    with open(corner_file, 'r', encoding='utf-8') as f:
        corner_data = json.load(f)
    
    return fp_q_data, corner_data

def extract_2025_features(fp_q_data, corner_data):
    """提取 2025 特徵"""
    features_list = []
    
    # 實際數據結構（參考 2025 JSON）
    fp3_drivers = fp_q_data.get('practice_sessions', {}).get('FP3', {}).get('driver_data', {})
    q_results = fp_q_data.get('qualifying', {}).get('results', {})
    
    # 彎角數據
    corner_drivers = {d['driver']: d for d in corner_data.get('fastest_lap_analysis', {}).get('drivers', [])}
    selected_corners = corner_data.get('selected_corners', {})
    
    low_corner_num = selected_corners.get('low_speed', {}).get('corner_number')
    mid_corner_num = selected_corners.get('mid_speed', {}).get('corner_number')
    high_corner_num = selected_corners.get('high_speed', {}).get('corner_number')
    
    for driver in fp3_drivers.keys():
        if driver not in q_results or driver not in corner_drivers:
            continue
        
        fp3_data = fp3_drivers[driver]
        q_data = q_results[driver]
        corner_driver_data = corner_drivers[driver]
        
        # 提取 Q 時間
        q_time_str = str(q_data['best_time'])
        if 'days' in q_time_str:
            time_parts = q_time_str.split(' ')[-1]
            h, m, s = time_parts.split(':')
            actual_q_time = int(h) * 3600 + int(m) * 60 + float(s)
        else:
            continue
        
        # 特徵向量
        features = {
            'driver': driver,
            'ideal_s1': fp3_data.get('sector1_best', np.nan),
            'ideal_s2': fp3_data.get('sector2_best', np.nan),
            'ideal_s3': fp3_data.get('sector3_best', np.nan),
            'ideal_lap': fp3_data.get('best_lap_time', np.nan),
            'low_speed_apex': 0.0,
            'mid_speed_apex': 0.0,
            'high_speed_apex': 0.0,
            'max_speed': fp3_data.get('speed_trap_max', np.nan),
            'actual_q_time': actual_q_time,
            'actual_position': q_data['position']
        }
        
        # 彎角速度
        corners_dict = corner_driver_data.get('corners', {})
        if low_corner_num:
            corner_key = f"low_speed_corner_{low_corner_num}"
            if corner_key in corners_dict:
                features['low_speed_apex'] = corners_dict[corner_key].get('apex_speed', 0.0)
        
        if mid_corner_num:
            corner_key = f"mid_speed_corner_{mid_corner_num}"
            if corner_key in corners_dict:
                features['mid_speed_apex'] = corners_dict[corner_key].get('apex_speed', 0.0)
        
        if high_corner_num:
            corner_key = f"high_speed_corner_{high_corner_num}"
            if corner_key in corners_dict:
                features['high_speed_apex'] = corners_dict[corner_key].get('apex_speed', 0.0)
        
        if all(not np.isnan(features[k]) for k in ['ideal_s1', 'ideal_s2', 'ideal_s3', 'max_speed']):
            if all(features[k] > 0 for k in ['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']):
                features_list.append(features)
    
    return features_list

def main():
    print("="*70)
    print("v3.0 模型 2025 Mexico 預測測試")
    print("="*70)
    
    # 載入模型
    model_file = 'models/track_specific_v3/Mexico.pkl'
    if not Path(model_file).exists():
        print(f"ERROR: 找不到模型檔案")
        return
    
    with open(model_file, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    print(f"\n[模型] 版本: {model_data['version']}")
    print(f"[模型] 訓練日期: {model_data['train_date']}")
    print(f"[模型] 測試 MAE: {model_data['performance']['test_mae']:.3f}s")
    print(f"[模型] 測試 R2: {model_data['performance']['test_r2']:.4f}")
    
    # 載入 2025 數據
    print(f"\n[數據] 載入 2025 Mexico 數據...")
    fp_q_data, corner_data = load_2025_data()
    if fp_q_data is None:
        return
    
    # 提取特徵
    features_list = extract_2025_features(fp_q_data, corner_data)
    if not features_list:
        print("ERROR: 無法提取特徵")
        return
    
    df = pd.DataFrame(features_list)
    print(f"[數據] 成功載入 {len(df)} 名車手")
    
    # 預測
    feature_cols = [
        'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex',
        'max_speed'
    ]
    
    X = df[feature_cols]
    predictions = model.predict(X)
    
    df['predicted_q_time'] = predictions
    df['predicted_position'] = df['predicted_q_time'].rank()
    
    # 評估
    from sklearn.metrics import mean_absolute_error, r2_score
    
    mae = mean_absolute_error(df['actual_q_time'], df['predicted_q_time'])
    r2 = r2_score(df['actual_q_time'], df['predicted_q_time'])
    spearman_corr, _ = spearmanr(df['actual_position'], df['predicted_position'])
    
    print(f"\n{'='*70}")
    print(f"預測結果")
    print(f"{'='*70}")
    print(f"MAE (時間誤差): {mae:.4f}s")
    print(f"R2 Score: {r2:.4f}")
    print(f"Spearman (名次相關): {spearman_corr:.4f}")
    
    # 顯示預測 vs 實際
    df_sorted = df.sort_values('predicted_position')
    
    print(f"\n{'='*70}")
    print(f"預測 vs 實際（Top 10）")
    print(f"{'='*70}")
    print(f"{'預測':<4} {'車手':<6} {'預測時間':<10} {'實際時間':<10} {'實際名次':<8} {'誤差'}")
    print("-"*70)
    
    for idx, row in df_sorted.head(10).iterrows():
        pred_pos = int(row['predicted_position'])
        actual_pos = int(row['actual_position'])
        error = row['predicted_q_time'] - row['actual_q_time']
        
        print(f"{pred_pos:<4} {row['driver']:<6} {row['predicted_q_time']:>8.3f}s  "
              f"{row['actual_q_time']:>8.3f}s  {actual_pos:<8} {error:>+7.3f}s")
    
    print(f"\n{'='*70}")
    print(f"對比 v2.0:")
    print(f"{'='*70}")
    print(f"v2.0 (Function 78): Spearman = 0.2842, MAE = 0.6439s")
    print(f"v3.0 (物理特徵):    Spearman = {spearman_corr:.4f}, MAE = {mae:.4f}s")
    
    improvement_spearman = (spearman_corr - 0.2842) / 0.2842 * 100
    improvement_mae = (0.6439 - mae) / 0.6439 * 100
    
    print(f"\n改善幅度:")
    print(f"  Spearman: {improvement_spearman:+.1f}%")
    print(f"  MAE: {improvement_mae:+.1f}%")

if __name__ == '__main__':
    main()
