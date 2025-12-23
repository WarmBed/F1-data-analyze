#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析阿布達比模型的特徵重要性
"""
import pickle
import sys
from pathlib import Path

# 設定輸出編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 載入阿布達比模型
model_path = Path('models/track_specific_v3/Abu Dhabi.pkl')

if model_path.exists():
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    print("="*70)
    print("阿布達比（Abu Dhabi）模型分析")
    print("="*70)
    
    # 基本資訊
    print(f"\n[模型資訊]")
    print(f"版本: {model_data.get('version', 'N/A')}")
    print(f"訓練日期: {model_data.get('train_date', 'N/A')}")
    
    # 效能指標
    perf = model_data.get('performance', {})
    print(f"\n[效能指標]")
    print(f"訓練樣本: {perf.get('train_samples', 'N/A')}")
    print(f"測試樣本: {perf.get('test_samples', 'N/A')}")
    print(f"訓練 MAE: {perf.get('train_mae', 'N/A'):.3f}秒")
    print(f"測試 MAE: {perf.get('test_mae', 'N/A'):.3f}秒")
    print(f"測試 R2: {perf.get('test_r2', 'N/A'):.4f}")
    
    # 特徵重要性
    feature_importance = model_data.get('feature_importance', {})
    print(f"\n[特徵重要性排序]")
    print(f"{'特徵':<20} {'重要性':>10} {'解釋'}")
    print("-"*70)
    
    # 排序並顯示
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    feature_names_zh = {
        'ideal_s1': 'Sector 1 最佳時間',
        'ideal_s2': 'Sector 2 最佳時間',
        'ideal_s3': 'Sector 3 最佳時間',
        'ideal_lap': 'FP3 最佳圈速',
        'low_speed_apex': '低速彎頂點速度',
        'mid_speed_apex': '中速彎頂點速度',
        'high_speed_apex': '高速彎頂點速度',
        'max_speed': '最高速度'
    }
    
    for feature, importance in sorted_features:
        zh_name = feature_names_zh.get(feature, feature)
        print(f"{feature:<20} {importance:>9.2%}  {zh_name}")
    
    # 計算主要特徵群組占比
    print(f"\n[特徵群組分析]")
    sector_importance = sum([feature_importance.get(f'ideal_s{i}', 0) for i in [1,2,3]])
    corner_importance = sum([feature_importance.get(f'{speed}_speed_apex', 0) 
                            for speed in ['low', 'mid', 'high']])
    
    print(f"Sector 時間總計: {sector_importance:.2%}")
    print(f"彎角速度總計: {corner_importance:.2%}")
    print(f"最高速: {feature_importance.get('max_speed', 0):.2%}")
    print(f"理想圈速: {feature_importance.get('ideal_lap', 0):.2%}")
    
    # 對比墨西哥（參考）
    print(f"\n[與墨西哥（R2=0.8044）對比]")
    print(f"{'指標':<25} {'阿布達比':>12} {'墨西哥':>12} {'差異':>12}")
    print("-"*70)
    print(f"{'測試 R2':<25} {perf.get('test_r2', 0):>12.4f} {0.8044:>12.4f} {perf.get('test_r2', 0)-0.8044:>+12.4f}")
    print(f"{'測試 MAE (秒)':<25} {perf.get('test_mae', 0):>12.3f} {0.379:>12.3f} {perf.get('test_mae', 0)-0.379:>+12.3f}")
    print(f"{'訓練樣本數':<25} {perf.get('train_samples', 0):>12} {46:>12} {perf.get('train_samples', 0)-46:>+12}")
    print(f"{'測試樣本數':<25} {perf.get('test_samples', 0):>12} {12:>12} {perf.get('test_samples', 0)-12:>+12}")
    
    # 墨西哥特徵重要性（參考）
    mexico_features = {
        'ideal_s1': 0.2955,
        'ideal_s2': 0.2862,
        'ideal_s3': 0.1092,
        'max_speed': 0.0769,
        'low_speed_apex': 0.0756,
        'ideal_lap': 0.0735,
        'mid_speed_apex': 0.0444,
        'high_speed_apex': 0.0388
    }
    
    print(f"\n[特徵重要性對比]")
    print(f"{'特徵':<20} {'阿布達比':>12} {'墨西哥':>12} {'差異':>12}")
    print("-"*70)
    for feature in sorted_features:
        feat_name = feature[0]
        abu_imp = feature[1]
        mex_imp = mexico_features.get(feat_name, 0)
        diff = abu_imp - mex_imp
        print(f"{feat_name:<20} {abu_imp:>11.2%} {mex_imp:>11.2%} {diff:>+11.2%}")
    
else:
    print("找不到阿布達比模型檔案")
