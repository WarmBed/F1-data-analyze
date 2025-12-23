#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析阿布達比模型的特徵重要性（從 XGBoost 模型直接提取）
"""
import pickle
import sys
from pathlib import Path
import numpy as np

# 設定輸出編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 載入阿布達比模型
model_path = Path('models/track_specific_v3/Abu Dhabi.pkl')

if not model_path.exists():
    print("找不到阿布達比模型檔案")
    sys.exit(1)

with open(model_path, 'rb') as f:
    model_data = pickle.load(f)

print("="*70)
print("阿布達比（Abu Dhabi）模型深度分析")
print("="*70)

# 基本資訊
print(f"\n[模型資訊]")
print(f"版本: {model_data.get('version', 'N/A')}")
print(f"訓練日期: {model_data.get('train_date', 'N/A')}")
print(f"賽道: {model_data.get('track', 'N/A')}")

# 效能指標
perf = model_data.get('performance', {})
print(f"\n[效能指標]")
print(f"總樣本: {perf.get('samples', 'N/A')}")
print(f"訓練樣本: {perf.get('train_samples', 'N/A')}")
print(f"測試樣本: {perf.get('test_samples', 'N/A')}")
print(f"訓練 MAE: {perf.get('train_mae', 'N/A'):.3f}秒")
print(f"測試 MAE: {perf.get('test_mae', 'N/A'):.3f}秒")
print(f"測試 R2: {perf.get('test_r2', 'N/A'):.4f}")

# 從 XGBoost 模型提取特徵重要性
model = model_data.get('model')
if model:
    # XGBoost 特徵重要性
    importance_dict = model.get_booster().get_score(importance_type='weight')
    
    # 特徵名稱映射
    feature_names = [
        'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex',
        'max_speed'
    ]
    
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
    
    # 轉換為百分比
    total_importance = sum(importance_dict.values())
    feature_importance = {}
    for i, fname in enumerate(feature_names):
        feat_key = f'f{i}'  # XGBoost 內部命名
        raw_imp = importance_dict.get(feat_key, 0)
        feature_importance[fname] = raw_imp / total_importance if total_importance > 0 else 0
    
    print(f"\n[特徵重要性排序]")
    print(f"{'特徵':<20} {'重要性':>10}  {'解釋'}")
    print("-"*70)
    
    # 排序並顯示
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    for feature, importance in sorted_features:
        zh_name = feature_names_zh.get(feature, feature)
        print(f"{feature:<20} {importance:>9.2%}  {zh_name}")
    
    # 計算主要特徵群組占比
    print(f"\n[特徵群組分析]")
    sector_importance = sum([feature_importance.get(f'ideal_s{i}', 0) for i in [1,2,3]])
    corner_importance = sum([feature_importance.get(f'{speed}_speed_apex', 0) 
                            for speed in ['low', 'mid', 'high']])
    
    print(f"Sector 時間總計: {sector_importance:.2%}")
    print(f"  - S1: {feature_importance.get('ideal_s1', 0):.2%}")
    print(f"  - S2: {feature_importance.get('ideal_s2', 0):.2%}")
    print(f"  - S3: {feature_importance.get('ideal_s3', 0):.2%}")
    print(f"\n彎角速度總計: {corner_importance:.2%}")
    print(f"  - 低速: {feature_importance.get('low_speed_apex', 0):.2%}")
    print(f"  - 中速: {feature_importance.get('mid_speed_apex', 0):.2%}")
    print(f"  - 高速: {feature_importance.get('high_speed_apex', 0):.2%}")
    print(f"\n其他特徵:")
    print(f"  - 最高速: {feature_importance.get('max_speed', 0):.2%}")
    print(f"  - 理想圈速: {feature_importance.get('ideal_lap', 0):.2%}")
    
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
    
    print(f"\n{'='*70}")
    print(f"與墨西哥（R2=0.8044）對比分析")
    print(f"{'='*70}")
    
    print(f"\n[效能對比]")
    print(f"{'指標':<25} {'阿布達比':>12} {'墨西哥':>12} {'差異':>12}")
    print("-"*70)
    print(f"{'測試 R2':<25} {perf.get('test_r2', 0):>12.4f} {0.8044:>12.4f} {perf.get('test_r2', 0)-0.8044:>+12.4f}")
    print(f"{'測試 MAE (秒)':<25} {perf.get('test_mae', 0):>12.3f} {0.379:>12.3f} {perf.get('test_mae', 0)-0.379:>+12.3f}")
    print(f"{'訓練樣本數':<25} {perf.get('train_samples', 0):>12} {46:>12} {perf.get('train_samples', 0)-46:>+12}")
    print(f"{'測試樣本數':<25} {perf.get('test_samples', 0):>12} {12:>12} {perf.get('test_samples', 0)-12:>+12}")
    
    print(f"\n[特徵重要性對比]")
    print(f"{'特徵':<20} {'阿布達比':>12} {'墨西哥':>12} {'差異':>12} {'變化'}")
    print("-"*70)
    for feature, abu_imp in sorted_features:
        mex_imp = mexico_features.get(feature, 0)
        diff = abu_imp - mex_imp
        change_pct = ((abu_imp / mex_imp) - 1) * 100 if mex_imp > 0 else 0
        arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"
        print(f"{feature:<20} {abu_imp:>11.2%} {mex_imp:>11.2%} {diff:>+11.2%}  {arrow} {abs(change_pct):>5.1f}%")
    
    # 關鍵發現
    print(f"\n{'='*70}")
    print(f"關鍵發現：阿布達比 R2 僅 0.5467 的原因")
    print(f"{'='*70}")
    
    # 分析差異
    abu_sector = sector_importance
    mex_sector = sum([mexico_features.get(f'ideal_s{i}', 0) for i in [1,2,3]])
    
    print(f"\n1. Sector 時間占比差異")
    print(f"   阿布達比: {abu_sector:.2%}")
    print(f"   墨西哥: {mex_sector:.2%}")
    print(f"   差異: {abu_sector - mex_sector:+.2%}")
    
    if abu_sector < mex_sector * 0.8:
        print(f"   ⚠️ Sector 時間重要性明顯偏低！")
    
    print(f"\n2. 樣本數與測試 MAE")
    print(f"   阿布達比: {perf.get('test_samples', 0)} 測試樣本, MAE {perf.get('test_mae', 0):.3f}秒")
    print(f"   墨西哥: 12 測試樣本, MAE 0.379秒")
    
    if perf.get('test_mae', 0) > 0.4:
        print(f"   ⚠️ 測試 MAE 較高，表示預測誤差大")
    
    print(f"\n3. 特徵分佈不均")
    importance_values = list(feature_importance.values())
    max_imp = max(importance_values)
    min_imp = min(importance_values)
    imp_range = max_imp - min_imp
    print(f"   最大重要性: {max_imp:.2%}")
    print(f"   最小重要性: {min_imp:.2%}")
    print(f"   範圍: {imp_range:.2%}")
    
    if imp_range < 0.15:
        print(f"   ⚠️ 特徵重要性差異小，模型可能無法有效區分關鍵特徵")
    
else:
    print("\n無法提取模型特徵重要性")

print(f"\n{'='*70}")
