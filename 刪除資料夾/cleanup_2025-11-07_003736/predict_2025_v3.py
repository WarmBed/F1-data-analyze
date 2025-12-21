#!/usr/bin/env python3
"""
對已訓練的 v3.0 模型執行 2025 預測
"""
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score


def extract_2025_features(fp_q_data, corner_data):
    """提取 2025 特徵"""
    features_list = []
    
    # 數據結構
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
        
        # 驗證數據完整性
        if all(not np.isnan(features[k]) for k in ['ideal_s1', 'ideal_s2', 'ideal_s3', 'max_speed']):
            if all(features[k] > 0 for k in ['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']):
                features_list.append(features)
    
    return features_list


def predict_2025_race(race_name):
    """預測單場 2025 賽事"""
    print(f"\nPredicting: {race_name}")
    
    try:
        # 載入模型
        model_path = Path(f'models/track_specific_v3/{race_name}.pkl')
        if not model_path.exists():
            print(f"  [SKIP] No model found")
            return None
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        model = model_data['model']
        
        # 載入 2025 FP3→Q 數據（需要找到對應檔案）
        json_dir = Path('json/predictionJSON')
        fp_q_file = None
        
        # 掃描所有 2025 檔案找到匹配的賽道
        for file in json_dir.glob('fp_q_data_2025_*.json'):
            # 暫時跳過（因為沒有 race_name 欄位）
            pass
        
        # 改用 corner 數據中的資訊
        corner_file = Path(f'json/all_drivers_cornering_analysis_2025_{race_name}_FP3.json')
        if not corner_file.exists():
            print(f"  [SKIP] No corner data")
            return None
        
        # 從檔名推斷，掃描對應的 FP3→Q 檔案
        # 這需要手動映射或從 corner 數據中提取賽事編號
        # 暫時跳過此賽道
        print(f"  [SKIP] Need race number mapping")
        return None
    
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def main():
    print("="*70)
    print("2025 Season Prediction (v3.0 Models)")
    print("="*70)
    
    # 找出所有有 corner 數據的 2025 賽道
    corner_files = sorted(Path('json').glob('all_drivers_cornering_analysis_2025_*_FP3.json'))
    
    races_2025 = []
    for file in corner_files:
        # 提取賽道名稱
        race_name = file.stem.replace('all_drivers_cornering_analysis_2025_', '').replace('_FP3', '')
        races_2025.append(race_name)
    
    print(f"\nFound {len(races_2025)} races with corner data:")
    for race in sorted(races_2025):
        print(f"  - {race}")
    
    print(f"\n{'='*70}")
    print("Predicting...")
    print(f"{'='*70}")
    
    prediction_results = []
    for race in sorted(races_2025):
        result = predict_2025_race(race)
        if result:
            prediction_results.append(result)
    
    print(f"\n{'='*70}")
    print(f"Completed: {len(prediction_results)}/{len(races_2025)} predictions")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
