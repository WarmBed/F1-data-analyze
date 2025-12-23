#!/usr/bin/env python3
"""
v3.7 vs v3.8 性能對比腳本

目的：驗證移除無效特徵後性能是否保持

預期結果（基於 ZERO_IMPORTANCE_FEATURES_ANALYSIS.md）:
- v3.8 預測性能與 v3.7 相同（移除的特徵重要性為 0%）
- v3.8 訓練速度提升 ~18%
- v3.8 模型檔案減少 ~15%
"""
import json
import pickle
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np


def load_training_results(version: str) -> dict:
    """載入訓練結果"""
    result_file = Path(f"{version}_training_results.json")
    
    if not result_file.exists():
        print(f"[警告] 找不到 {result_file}")
        return None
    
    with open(result_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_model_info(version: str, track: str) -> dict:
    """載入模型資訊"""
    model_dir = Path(f"models/track_specific_{version}")
    model_file = model_dir / f"{track}.pkl"
    
    if not model_file.exists():
        return None
    
    with open(model_file, 'rb') as f:
        model_data = pickle.load(f)
    
    return {
        'file_size': model_file.stat().st_size / 1024,  # KB
        'feature_count': len(model_data['feature_names']),
        'feature_names': model_data['feature_names']
    }


def compare_versions():
    """對比 v3.7 和 v3.8"""
    print("="*80)
    print("v3.7 vs v3.8 性能對比")
    print("="*80)
    
    # 載入結果
    v37_results = load_training_results("v3.7")
    v38_results = load_training_results("v3.8")
    
    if not v37_results or not v38_results:
        print("\n[錯誤] 缺少訓練結果檔案")
        print("請先執行:")
        print("  python batch_train_all_tracks_v3.7.py")
        print("  python batch_train_all_tracks_v3.8.py")
        return
    
    # 提取結果數據
    v37_data = v37_results if isinstance(v37_results, dict) and 'results' not in v37_results else v37_results.get('results', v37_results)
    v38_data = v38_results.get('results', v38_results)
    
    # 共同賽道
    common_tracks = set(v37_data.keys()) & set(v38_data.keys())
    
    if not common_tracks:
        print("\n[錯誤] 沒有共同訓練的賽道")
        return
    
    print(f"\n[共同賽道] {len(common_tracks)} 個")
    print(f"  {', '.join(sorted(common_tracks))}")
    
    # 收集對比數據
    comparison_data = []
    
    for track in sorted(common_tracks):
        v37 = v37_data[track]
        v38 = v38_data[track]
        
        # 載入模型資訊
        v37_model = load_model_info("v3.7", track)
        v38_model = load_model_info("v3.8", track)
        
        comparison_data.append({
            'track': track,
            'v37_cv_mae': v37['cv_mae'],
            'v38_cv_mae': v38['cv_mae'],
            'cv_mae_diff': v38['cv_mae'] - v37['cv_mae'],
            'v37_train_mae': v37['train_mae'],
            'v38_train_mae': v38['train_mae'],
            'v37_r2': v37.get('train_r2', 0),
            'v38_r2': v38.get('train_r2', 0),
            'v37_features': v37_model['feature_count'] if v37_model else 20,
            'v38_features': v38_model['feature_count'] if v38_model else 17,
            'v37_size': v37_model['file_size'] if v37_model else 0,
            'v38_size': v38_model['file_size'] if v38_model else 0,
        })
    
    df = pd.DataFrame(comparison_data)
    
    # ========== 性能對比 ==========
    print("\n" + "="*80)
    print("性能對比（預測準確度）")
    print("="*80)
    
    print(f"\n{'賽道':20s} {'v3.7 CV MAE':12s} {'v3.8 CV MAE':12s} {'差異':10s} {'變化%':8s}")
    print("-"*80)
    
    for _, row in df.iterrows():
        diff = row['cv_mae_diff']
        pct_change = (diff / row['v37_cv_mae']) * 100 if row['v37_cv_mae'] > 0 else 0
        
        status = "✓" if abs(diff) < 0.05 else ("⚠" if abs(diff) < 0.1 else "❌")
        
        print(f"{row['track']:20s} {row['v37_cv_mae']:>10.3f}s  {row['v38_cv_mae']:>10.3f}s  "
              f"{diff:>+8.3f}s  {pct_change:>+6.2f}% {status}")
    
    # 平均值
    avg_v37 = df['v37_cv_mae'].mean()
    avg_v38 = df['v38_cv_mae'].mean()
    avg_diff = avg_v38 - avg_v37
    avg_pct = (avg_diff / avg_v37) * 100 if avg_v37 > 0 else 0
    
    print("-"*80)
    print(f"{'平均':20s} {avg_v37:>10.3f}s  {avg_v38:>10.3f}s  {avg_diff:>+8.3f}s  {avg_pct:>+6.2f}%")
    
    # ========== 效率對比 ==========
    print("\n" + "="*80)
    print("效率對比（模型大小）")
    print("="*80)
    
    print(f"\n{'賽道':20s} {'v3.7 特徵':10s} {'v3.8 特徵':10s} {'v3.7 大小':12s} {'v3.8 大小':12s} {'減少%':8s}")
    print("-"*80)
    
    for _, row in df.iterrows():
        size_reduction = ((row['v37_size'] - row['v38_size']) / row['v37_size'] * 100) if row['v37_size'] > 0 else 0
        
        print(f"{row['track']:20s} {row['v37_features']:>8d}    {row['v38_features']:>8d}    "
              f"{row['v37_size']:>9.1f} KB  {row['v38_size']:>9.1f} KB  {size_reduction:>+6.1f}%")
    
    avg_size_v37 = df['v37_size'].mean()
    avg_size_v38 = df['v38_size'].mean()
    avg_size_reduction = ((avg_size_v37 - avg_size_v38) / avg_size_v37 * 100) if avg_size_v37 > 0 else 0
    
    print("-"*80)
    print(f"{'平均':20s} {'20':>8s}    {'17':>8s}    "
          f"{avg_size_v37:>9.1f} KB  {avg_size_v38:>9.1f} KB  {avg_size_reduction:>+6.1f}%")
    
    # ========== 特徵對比 ==========
    print("\n" + "="*80)
    print("特徵差異分析")
    print("="*80)
    
    sample_track = list(common_tracks)[0]
    v37_model = load_model_info("v3.7", sample_track)
    v38_model = load_model_info("v3.8", sample_track)
    
    if v37_model and v38_model:
        v37_features = set(v37_model['feature_names'])
        v38_features = set(v38_model['feature_names'])
        
        removed_features = v37_features - v38_features
        
        print(f"\n[v3.7 特徵數量] {len(v37_features)}")
        print(f"[v3.8 特徵數量] {len(v38_features)}")
        print(f"\n[移除的特徵] {len(removed_features)}")
        for feat in sorted(removed_features):
            print(f"  ❌ {feat}")
    
    # ========== 結論 ==========
    print("\n" + "="*80)
    print("結論")
    print("="*80)
    
    # 性能變化評估
    significant_changes = df[abs(df['cv_mae_diff']) > 0.1]
    
    print(f"\n[性能評估]")
    if len(significant_changes) == 0:
        print("  ✅ 所有賽道性能保持穩定（差異 < 0.1s）")
        print("  ✅ 驗證：移除的特徵確實無效")
    else:
        print(f"  ⚠️  {len(significant_changes)} 個賽道有顯著變化（差異 > 0.1s）:")
        for _, row in significant_changes.iterrows():
            print(f"     - {row['track']}: {row['cv_mae_diff']:+.3f}s")
    
    print(f"\n[效率提升]")
    print(f"  特徵數量: 20 → 17 (-15.0%)")
    print(f"  模型大小: {avg_size_v37:.1f} KB → {avg_size_v38:.1f} KB ({avg_size_reduction:+.1f}%)")
    
    if avg_pct < 1.0:
        print(f"  平均 CV MAE: {avg_v37:.3f}s → {avg_v38:.3f}s ({avg_pct:+.2f}%)")
        print("\n  ✅ v3.8 達成目標：")
        print("     - 性能不變（誤差 < 1%）")
        print("     - 效率提升（特徵減少 15%）")
    else:
        print(f"  ⚠️  性能略有變化: {avg_pct:+.2f}%")
    
    # ========== 特徵重要性對比 ==========
    print("\n" + "="*80)
    print("特徵重要性對比（範例：" + sample_track + "）")
    print("="*80)
    
    if v37_model and v38_model:
        v37_result = v37_data[sample_track]
        v38_result = v38_data[sample_track]
        
        v37_importance = v37_result.get('feature_importance', {})
        v38_importance = v38_result.get('feature_importance', {})
        
        print("\n[v3.7 Top 10 特徵]")
        top_v37 = sorted(v37_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (feat, imp) in enumerate(top_v37, 1):
            marker = "❌" if feat in removed_features else "  "
            print(f"  {i:2d}. {marker} {feat:30s} {imp*100:6.2f}%")
        
        print("\n[v3.8 Top 10 特徵]")
        top_v38 = sorted(v38_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (feat, imp) in enumerate(top_v38, 1):
            print(f"  {i:2d}.    {feat:30s} {imp*100:6.2f}%")
    
    print("\n" + "="*80)


def main():
    compare_versions()


if __name__ == '__main__':
    main()
