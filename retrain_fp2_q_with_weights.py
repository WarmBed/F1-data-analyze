#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FP2→Q 預測模型重新訓練（帶權重）

方案：
1. 年份權重：近年數據權重更高
2. 車隊一致性權重：表現穩定的車隊權重更高
3. Quali Sim 識別權重：明確識別為 Quali Sim 的圈權重更高

作者: GitHub Copilot
日期: 2026-01-04
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb


# ===== 權重配置 =====
YEAR_WEIGHTS = {
    2025: 1.5,  # 最新年份，最高權重
    2024: 1.3,
    2023: 1.0,
    2022: 0.8,
    2021: 0.6,
    2020: 0.5,
}

# 車隊一致性權重（基於 FP2→Q 改進量的標準差）
# 標準差越小，表現越穩定，權重越高
TEAM_CONSISTENCY_BONUS = {
    'Red Bull Racing': 1.2,    # 表現一致
    'Ferrari': 1.2,
    'McLaren': 1.1,
    'Mercedes': 1.1,
    'Aston Martin': 1.0,
    'Alpine': 1.0,
    'Williams': 1.0,
    'Haas F1 Team': 0.9,
    'Kick Sauber': 0.8,        # FP2 表現不穩定
    'Racing Bulls': 0.8,       # FP2 表現不穩定
}


def load_training_data():
    """載入訓練數據"""
    training_dir = Path("training_data")
    data_file = training_dir / "fp2_q_training_data_2022_2025.json"
    
    if not data_file.exists():
        print(f"錯誤: 找不到訓練數據 {data_file}")
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"載入 {len(data)} 筆賽事記錄")
    return data


def load_team_fuel_habits():
    """載入車隊燃油習慣數據"""
    habits_file = Path("training_data/team_fuel_habits.json")
    
    if habits_file.exists():
        with open(habits_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('team_habits', {})
    return {}


def parse_time_to_seconds(time_str):
    """將時間字串轉換為秒數"""
    if not time_str or time_str == 'NaT':
        return None
    
    import re
    
    # 格式: "0 days 00:01:30.558000"
    match = re.search(r'(\d+):(\d+):(\d+\.?\d*)', str(time_str))
    if match:
        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    
    # 格式: 純數字秒數
    try:
        return float(time_str)
    except:
        return None


def extract_features_and_targets(data, team_fuel_habits):
    """
    從訓練數據中提取特徵、目標值和樣本權重
    
    返回: (X, y, weights, track_samples)
    """
    feature_names = [
        'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
        's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
        'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
        'fp2_relative_position', 'fp2_gap_to_fastest'
    ]
    
    track_samples = {}  # 按賽道組織樣本
    
    for record in data:
        # 獲取元數據
        metadata = record.get('metadata', {})
        year = metadata.get('year', 2024)
        track = metadata.get('race', record.get('track', 'Unknown'))
        
        if track not in track_samples:
            track_samples[track] = {'X': [], 'y': [], 'weights': [], 'info': []}
        
        # 獲取 FP2 和 Q 數據
        practice_sessions = record.get('practice_sessions', {})
        fp2_section = practice_sessions.get('FP2', {})
        fp2_drivers = fp2_section.get('driver_data', {})
        
        q_section = record.get('qualifying', {})
        q_results = q_section.get('results', {})
        
        if not fp2_drivers or not q_results:
            continue
        
        for driver, fp2_info in fp2_drivers.items():
            if driver not in q_results:
                continue
            
            q_info = q_results[driver]
            
            # 獲取 FP2 時間
            fp2_time = fp2_info.get('best_lap_time', fp2_info.get('fastest_lap', 0))
            if not fp2_time or fp2_time <= 0 or fp2_time > 120:
                continue
            
            # 獲取 Q 時間
            q_time_str = q_info.get('best_time', q_info.get('q3_time', q_info.get('q2_time', q_info.get('q1_time'))))
            q_time = parse_time_to_seconds(q_time_str)
            if not q_time or q_time <= 0 or q_time > 120:
                continue
            
            # 計算改進量（目標值）
            improvement = q_time - fp2_time  # Q 通常比 FP2 快，所以是負數
            
            # 計算特徵
            s1 = fp2_info.get('sector1_time', fp2_time / 3)
            s2 = fp2_info.get('sector2_time', fp2_time / 3)
            s3 = fp2_info.get('sector3_time', fp2_time / 3)
            
            if not s1 or s1 <= 0:
                s1 = fp2_time / 3
            if not s2 or s2 <= 0:
                s2 = fp2_time / 3
            if not s3 or s3 <= 0:
                s3 = fp2_time / 3
            
            max_speed = fp2_info.get('max_speed', 300.0) or 300.0
            avg_speed = fp2_info.get('avg_speed', 250.0) or 250.0
            
            # 構建特徵向量
            features = {
                'ideal_s1': s1,
                'ideal_s2': s2,
                'ideal_s3': s3,
                'ideal_lap': fp2_time,
                'low_speed_apex': avg_speed * 0.8,
                'mid_speed_apex': avg_speed,
                'high_speed_apex': avg_speed * 1.1,
                'max_speed': max_speed,
                's1_s2_ratio': s1 / s2 if s2 > 0 else 1.0,
                'sector_cv': 0.1,  # 預設值
                's2_lap_ratio': s2 / fp2_time if fp2_time > 0 else 0.33,
                'max_speed_lap_ratio': max_speed * fp2_time / 1000 if fp2_time > 0 else 20.0,
                'max_speed_s2_ratio': max_speed / s2 if s2 > 0 else 10.0,
                'speed_consistency': 0.9,  # 預設值
                'fp2_relative_position': 0.5,
                'fp2_gap_to_fastest': 0.0
            }
            
            feature_vector = [features.get(fname, 0.0) for fname in feature_names]
            
            # 計算樣本權重
            team = fp2_info.get('team', 'Unknown')
            
            # 1. 年份權重
            year_weight = YEAR_WEIGHTS.get(year, 0.5)
            
            # 2. 車隊一致性權重
            team_weight = TEAM_CONSISTENCY_BONUS.get(team, 1.0)
            
            # 3. Quali Sim 權重（輪胎壽命 <= 3 表示 Quali Sim）
            tire_age = fp2_info.get('tire_age_avg', 10)
            if tire_age is None or not isinstance(tire_age, (int, float)):
                tire_age = 10
            quali_sim_weight = 1.5 if tire_age <= 3 else 1.0
            
            # 綜合權重
            sample_weight = year_weight * team_weight * quali_sim_weight
            
            track_samples[track]['X'].append(feature_vector)
            track_samples[track]['y'].append(improvement)
            track_samples[track]['weights'].append(sample_weight)
            track_samples[track]['info'].append({
                'driver': driver,
                'team': team,
                'year': year,
                'fp2_time': fp2_time,
                'q_time': q_time,
                'improvement': improvement,
                'weight': sample_weight
            })
    
    return track_samples, feature_names


def train_weighted_model(X, y, weights, track_name, feature_names):
    """
    使用樣本權重訓練 XGBoost 模型
    """
    X = np.array(X)
    y = np.array(y)
    weights = np.array(weights)
    
    if len(X) < 10:
        print(f"  ⚠️ {track_name} 樣本不足 ({len(X)}), 跳過")
        return None
    
    print(f"\n訓練 {track_name} 模型 (樣本: {len(X)}, 加權樣本: {weights.sum():.1f})")
    
    # XGBoost 參數
    params = {
        'n_estimators': 200,
        'max_depth': 5,  # 降低深度防止過擬合
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'gamma': 0.2,  # 增加正則化
        'min_child_weight': 5,  # 增加防止過擬合
        'reg_alpha': 0.2,
        'reg_lambda': 1.5,
        'random_state': 42
    }
    
    model = xgb.XGBRegressor(**params)
    
    # 使用樣本權重訓練
    model.fit(X, y, sample_weight=weights)
    
    # 評估
    y_pred = model.predict(X)
    train_mae = mean_absolute_error(y, y_pred)
    train_r2 = r2_score(y, y_pred)
    
    # 交叉驗證
    cv = KFold(n_splits=min(3, len(X) // 3), shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring='neg_mean_absolute_error')
    cv_mae = -cv_scores.mean()
    
    print(f"  訓練 MAE: {train_mae:.3f}s, R²: {train_r2:.4f}")
    print(f"  交叉驗證 MAE: {cv_mae:.3f}s")
    
    return {
        'model': model,
        'feature_names': feature_names,
        'track': track_name,
        'train_mae': train_mae,
        'train_r2': train_r2,
        'cv_mae': cv_mae,
        'sample_count': len(X),
        'weighted_sample_count': weights.sum(),
        'version': 'v3.10_FP2_weighted',
        'trained_at': datetime.now().isoformat()
    }


def main():
    print("="*70)
    print("FP2→Q 預測模型重新訓練（帶權重）")
    print("="*70)
    print(f"\n年份權重配置: {YEAR_WEIGHTS}")
    print(f"車隊一致性權重: 見 TEAM_CONSISTENCY_BONUS")
    
    # 載入數據
    data = load_training_data()
    if not data:
        return
    
    team_fuel_habits = load_team_fuel_habits()
    print(f"載入 {len(team_fuel_habits)} 個車隊的燃油習慣")
    
    # 提取特徵和目標值
    print("\n提取特徵和目標值...")
    track_samples, feature_names = extract_features_and_targets(data, team_fuel_habits)
    print(f"共 {len(track_samples)} 個賽道的數據")
    
    # 創建模型目錄
    model_dir = Path("models/fp2_q_specific_v3.10")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # 訓練每個賽道的模型
    results = {}
    for track, samples in sorted(track_samples.items()):
        X = samples['X']
        y = samples['y']
        weights = samples['weights']
        
        model_data = train_weighted_model(X, y, weights, track, feature_names)
        if model_data:
            # 保存模型
            model_file = model_dir / f"{track}.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"  ✅ 模型已保存: {model_file}")
            
            results[track] = {
                'train_mae': model_data['train_mae'],
                'cv_mae': model_data['cv_mae'],
                'sample_count': model_data['sample_count'],
                'weighted_sample_count': model_data['weighted_sample_count']
            }
    
    # 保存訓練報告
    report = {
        'timestamp': datetime.now().isoformat(),
        'version': 'v3.10_FP2_weighted',
        'year_weights': YEAR_WEIGHTS,
        'team_weights': TEAM_CONSISTENCY_BONUS,
        'tracks': results,
        'summary': {
            'total_tracks': len(results),
            'avg_train_mae': np.mean([r['train_mae'] for r in results.values()]),
            'avg_cv_mae': np.mean([r['cv_mae'] for r in results.values()])
        }
    }
    
    report_file = Path("fp2_q_weighted_training_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("訓練完成!")
    print("="*70)
    print(f"訓練賽道數: {len(results)}")
    print(f"平均訓練 MAE: {report['summary']['avg_train_mae']:.3f}s")
    print(f"平均交叉驗證 MAE: {report['summary']['avg_cv_mae']:.3f}s")
    print(f"\n報告已保存: {report_file}")


if __name__ == "__main__":
    main()
