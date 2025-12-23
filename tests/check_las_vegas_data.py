"""檢查 Las Vegas 訓練數據質量"""

import json
import pickle
from pathlib import Path

# 1. 檢查訓練結果統計
results_file = Path("v3.8_training_results.json")
if results_file.exists():
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lv = data["results"]["Las Vegas"]
    print("=" * 70)
    print("Las Vegas 訓練統計")
    print("=" * 70)
    print(f"樣本數: {lv['sample_count']}")
    print(f"訓練 R²: {lv['train_r2']:.6f}  ⚠️  {'極低！模型無法學習' if lv['train_r2'] < 0.1 else 'OK'}")
    print(f"訓練 MAE: {lv['train_mae']:.4f}")
    print(f"CV MAE: {lv['cv_mae']:.4f}")

# 2. 檢查模型文件
model_file = Path("models/track_specific_v3.8/Las Vegas.pkl")
if model_file.exists():
    with open(model_file, 'rb') as f:
        model_data = pickle.load(f)
    
    print("\n" + "=" * 70)
    print("模型特徵重要性")
    print("=" * 70)
    
    feature_names = model_data['feature_names']
    feature_importances = model_data['model'].feature_importances_
    
    # 排序
    importance_pairs = list(zip(feature_names, feature_importances))
    importance_pairs.sort(key=lambda x: x[1], reverse=True)
    
    for i, (feat, imp) in enumerate(importance_pairs[:10], 1):
        print(f"{i:2d}. {feat:30s}: {imp*100:6.2f}%")
    
    # 統計
    non_zero = sum(1 for _, imp in importance_pairs if imp > 0.001)
    print(f"\n非零特徵數 (>0.1%): {non_zero}/{len(feature_names)}")
    
    if non_zero < 3:
        print("\n⚠️  警告：只有極少數特徵有非零重要性，表示訓練數據可能存在問題")
        print("可能原因：")
        print("  1. Las Vegas 賽事數據樣本太少（只有 40 筆）")
        print("  2. 數據中某些特徵為常數或線性相關")
        print("  3. 目標變量（Q時間）與特徵間無明顯關係")

# 3. 比較其他賽道
print("\n" + "=" * 70)
print("其他賽道 R² 對比（前 5 名 vs Las Vegas）")
print("=" * 70)

if results_file.exists():
    with open(results_file, 'r', encoding='utf-8') as f:
        all_results = json.load(f)
    
    # 按 R² 排序
    tracks = []
    for track, stats in all_results["results"].items():
        tracks.append((track, stats['train_r2'], stats['sample_count']))
    
    tracks.sort(key=lambda x: x[1], reverse=True)
    
    print("TOP 5 最佳 R²:")
    for i, (track, r2, count) in enumerate(tracks[:5], 1):
        print(f"  {i}. {track:25s}: R²={r2:.4f}, 樣本數={count}")
    
    print("\nLas Vegas:")
    lv_idx = next(i for i, (t, _, _) in enumerate(tracks) if t == "Las Vegas")
    track, r2, count = tracks[lv_idx]
    print(f"  {lv_idx+1}. {track:25s}: R²={r2:.4f}, 樣本數={count}  ⚠️  倒數第幾？")
