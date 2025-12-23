"""
分析 Great Britain 失準原因
對比 Mexico (成功) vs Azerbaijan (雨戰) vs Great Britain (失敗)
顯示特徵重要性占比
"""

import json
import pickle
from pathlib import Path

# 三個賽道對比
tracks_to_analyze = {
    "Mexico": {"spearman": 0.774, "status": "✅ 成功"},
    "Azerbaijan": {"spearman": 0.107, "status": "☔ 雨戰"},
    "Great Britain": {"spearman": 0.194, "status": "❌ 失敗"}
}

print("="*80)
print("Great Britain 失準原因分析")
print("對比三個賽道的特徵重要性")
print("="*80)

# 尋找模型檔案
models_dir = Path("models/track_specific_v3.3")

for track_name, info in tracks_to_analyze.items():
    print(f"\n{'='*80}")
    print(f"{track_name} (Spearman: {info['spearman']:.3f}) {info['status']}")
    print(f"{'='*80}")
    
    # 尋找模型檔案
    model_files = list(models_dir.glob(f"*{track_name}*.pkl"))
    
    if not model_files:
        print(f"⚠️  找不到 {track_name} 模型檔案")
        
        # 嘗試其他可能的名稱
        if track_name == "Great Britain":
            model_files = list(models_dir.glob("*Britain*.pkl"))
            if not model_files:
                model_files = list(models_dir.glob("*Silverstone*.pkl"))
        
        if not model_files:
            print(f"❌ 無法找到模型")
            continue
    
    # 讀取模型
    try:
        model_file = sorted(model_files)[-1]  # 最新的
        print(f"📂 模型檔案: {model_file.name}")
        
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        # 獲取特徵重要性
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_names = model.feature_names_in_ if hasattr(model, 'feature_names_in_') else \
                           [f"feature_{i}" for i in range(len(importances))]
            
            # 排序
            sorted_idx = importances.argsort()[::-1]
            
            print(f"\n特徵重要性 (Top 11):")
            print(f"{'排名':<4} {'特徵':<20} {'占比':>8} {'類型':<8}")
            print("-" * 45)
            
            total = 0
            for rank, idx in enumerate(sorted_idx[:11], 1):
                feat_name = feature_names[idx]
                importance = importances[idx] * 100
                total += importance
                
                # 判斷特徵類型
                if 'ratio' in feat_name.lower() or 'cv' in feat_name.lower():
                    feat_type = "交互"
                else:
                    feat_type = "基礎"
                
                print(f"{rank:<4} {feat_name:<20} {importance:>7.2f}% {feat_type:<8}")
            
            print("-" * 45)
            print(f"{'Top 11 總和':<24} {total:>7.2f}%")
            
            # 計算交互特徵總和
            interaction_total = sum(importances[idx] * 100 
                                   for idx in range(len(importances))
                                   if 'ratio' in feature_names[idx].lower() or 
                                      'cv' in feature_names[idx].lower())
            
            print(f"{'交互特徵總和':<24} {interaction_total:>7.2f}%")
            
            # 統計最強特徵
            top1 = feature_names[sorted_idx[0]]
            top1_pct = importances[sorted_idx[0]] * 100
            print(f"\n🏆 最強特徵: {top1} ({top1_pct:.2f}%)")
            
    except Exception as e:
        print(f"❌ 讀取模型失敗: {e}")

# 對比分析
print("\n" + "="*80)
print("對比分析")
print("="*80)

print("""
### Mexico (Spearman 0.774) - 成功案例 ✅

**特徵分佈特點：**
- ideal_s1 主導 (33.44%)
- s1_s2_ratio 交互特徵高 (15.55%)
- 交互特徵總和 18.90%
- 特徵分佈均衡

**成功原因：**
1. 平衡型賽道，S1/S2/S3 權重均衡
2. 交互特徵有效捕捉賽道特性
3. 訓練數據與 2025 相似

---

### Azerbaijan (Spearman 0.107) - 雨戰失敗 ☔

**失敗原因：**
1. ☔ 2025 排位賽下雨（FP3 乾地）
2. 模型基於乾地數據訓練
3. 雨戰條件完全不同
4. 輪胎策略、抓地力改變

**解決方案：**
- 添加 rainfall 特徵
- 雨戰時跳過預測
- 收集雨戰訓練數據

---

### Great Britain (Spearman 0.194) - 乾地失敗 ❌

**需要調查的問題：**
1. 特徵重要性是否異常？
2. 某個特徵過度主導？
3. 訓練數據質量問題？
4. 2025 賽道特性改變？

**與 Mexico 對比：**
- Mexico: 交互特徵 18.90%，分佈均衡
- Great Britain: 待確認特徵分佈

**可能原因假設：**
1. ❌ 不是雨戰（已確認乾地）
2. ⚠️ 訓練 MAE 已經 0.489s（18 賽道中最高）
3. ⚠️ 可能某特徵過度主導
4. ⚠️ 2025 賽道修改或 DRS 調整
""")

# 讀取訓練報告
print("\n" + "="*80)
print("訓練階段性能對比")
print("="*80)

training_stats = {
    "Mexico": {"R²": 0.9845, "MAE": "0.111s", "樣本數": 20},
    "Azerbaijan": {"R²": 0.9949, "MAE": "0.060s", "樣本數": 38},
    "Great Britain": {"R²": 0.9937, "MAE": "0.489s", "樣本數": 39}
}

print(f"\n{'賽道':<20} {'訓練 R²':>10} {'訓練 MAE':>12} {'樣本數':>8} {'2025 Spearman':>15}")
print("-" * 70)
for track, stats in training_stats.items():
    spearman = tracks_to_analyze[track]["spearman"]
    print(f"{track:<20} {stats['R²']:>10.4f} {stats['MAE']:>12} {stats['樣本數']:>8} {spearman:>15.3f}")

print("\n觀察:")
print("1. Great Britain 訓練 MAE 0.489s 遠高於其他賽道")
print("2. Mexico MAE 0.111s, Azerbaijan MAE 0.060s (正常)")
print("3. Great Britain 訓練時就已經有問題")
print("4. 2025 進一步惡化至 6.474s (MAE)")

print("\n結論:")
print("Great Britain 模型從訓練階段就有問題，")
print("不是 2025 特有現象，而是該賽道本身難以預測")
