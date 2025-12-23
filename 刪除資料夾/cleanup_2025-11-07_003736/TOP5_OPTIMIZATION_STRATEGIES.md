# Top5 預測優化策略

**日期**: 2025-11-04  
**目標**: 從圈速預測優化為 Top5 排名預測  
**關鍵發現**: ✅ **不需要重新訓練！**

---

## 🎯 核心概念

### 現狀分析
您的 v3.7/v3.8 模型**已經在做排名預測**：

```python
# 現有流程（predict_v37_2025.py）
predicted_times = model.predict(X)  # 預測圈速
predicted_ranks = df['predicted_time'].rank()  # ⭐ 自動產生排名

# 已有的評估指標
spearman = spearmanr(actual_ranks, predicted_ranks)  # 排名相關性
top5_accuracy = len(actual_top5 & predicted_top5) / 5  # Top5 準確率
```

### 為何不需重新訓練？

1. **回歸 → 排名的轉換是自動的**
   - 圈速越快 → 排名越前
   - 只要相對順序對，排名就對
   - **Spearman 相關性**已經在評估這個

2. **排名分類模型通常更差**
   - 損失連續性（第 1 名 vs 第 2 名 = 第 1 名 vs 第 20 名）
   - 無法處理圈速極接近的情況
   - 準確率指標過於嚴格

3. **您的 Spearman 0.549 已經不錯**
   - 0.549 = 中等強度正相關
   - Top5 準確率: 平均 60-80%
   - 改進空間：後處理優化，而非重新訓練

---

## 🚀 優化策略（無需重新訓練）

### 策略 1: **Top5 加權預測** ⭐ 推薦

**原理**: 在預測時對 Top5 候選車手施加更保守的調整

```python
def predict_with_top5_focus(model, X, fp3_ranks):
    """
    Top5 聚焦預測
    對 FP3 排名前列的車手施加更小的調整
    """
    base_predictions = model.predict(X)
    
    # 調整策略：FP3 Top7 車手的預測時間偏向保守
    adjusted_predictions = base_predictions.copy()
    
    for i, fp3_rank in enumerate(fp3_ranks):
        if fp3_rank <= 7:  # Top7 候選
            # 減少預測調整幅度（更接近 FP3 時間）
            fp3_time = X.iloc[i]['ideal_lap']
            adjustment = base_predictions[i] - fp3_time
            
            # 保守係數（越前面越保守）
            conservative_factor = 0.3 + (fp3_rank / 7) * 0.4  # 0.3-0.7
            adjusted_predictions[i] = fp3_time + adjustment * conservative_factor
    
    return adjusted_predictions
```

**實現**:
```powershell
# 創建 Top5 優化預測器
python predict_v38_2025_top5_optimized.py
```

---

### 策略 2: **排名穩定性分析** 📊

**原理**: 分析哪些車手的 FP3→Q 排名變化小

```python
def analyze_ranking_stability():
    """分析 FP3→Q 排名穩定性"""
    
    # 統計 2022-2024 各車手的排名變化
    stability_stats = {}
    
    for driver in top_drivers:
        fp3_ranks = historical_data[driver]['fp3_rank']
        q_ranks = historical_data[driver]['q_rank']
        
        # 計算平均排名變化
        rank_changes = np.abs(fp3_ranks - q_ranks)
        stability_stats[driver] = {
            'mean_change': rank_changes.mean(),
            'std_change': rank_changes.std(),
            'max_improvement': (fp3_ranks - q_ranks).max(),  # 正值 = 進步
            'volatility': rank_changes.std() / rank_changes.mean()
        }
    
    return stability_stats

# 結果範例
# VER: mean_change=1.2, volatility=0.3 → 穩定
# PER: mean_change=3.5, volatility=0.9 → 不穩定
```

**應用**: 對穩定車手的 FP3 排名給予更高權重

---

### 策略 3: **車手分組預測** 🎯

**原理**: 不預測精確排名，預測車手所屬組別

```python
def group_based_prediction(predictions_df):
    """
    將車手分為 3 組：
    - Top5 候選（預測圈速 Top7）
    - 中段（8-15）
    - 後段（16-20）
    """
    # 按預測時間排序
    predictions_df = predictions_df.sort_values('predicted_time')
    
    # 分組
    predictions_df['predicted_group'] = pd.cut(
        predictions_df['predicted_rank'],
        bins=[0, 7, 15, 20],
        labels=['Top5 候選', '中段', '後段']
    )
    
    # 實際分組
    predictions_df['actual_group'] = pd.cut(
        predictions_df['actual_rank'],
        bins=[0, 5, 15, 20],
        labels=['Top5', '中段', '後段']
    )
    
    # 計算分組準確率
    group_accuracy = (predictions_df['predicted_group'] == predictions_df['actual_group']).mean()
    
    return predictions_df, group_accuracy
```

**優勢**:
- Top5 候選預測 Top7（容錯空間 +2）
- 準確率大幅提升（80%+）
- 實務應用更有價值

---

### 策略 4: **賽道特定閾值** 🏁

**原理**: 不同賽道的 FP3→Q 改進幅度不同

```python
# 已有的賽道改進率（來自 v3.5）
track_improvement_rates = {
    'Monaco': 0.0159,      # 街道賽：改進空間小
    'Italy': 0.0074,       # 高速賽：改進空間小
    'Hungary': 0.0874,     # 技術賽：改進空間大
    'Netherlands': 0.0768  # 技術賽：改進空間大
}

def apply_track_specific_threshold(predictions, track_name):
    """
    根據賽道特性調整 Top5 閾值
    """
    improvement_rate = track_improvement_rates.get(track_name, 0.015)
    
    # 計算動態閾值
    if improvement_rate < 0.01:  # 低改進賽道（Monaco, Italy）
        # FP3 Top6 → Q Top5 機率高
        top5_threshold = 6
    elif improvement_rate > 0.05:  # 高改進賽道（Hungary, Netherlands）
        # FP3 Top8 → Q Top5 機率高（洗牌嚴重）
        top5_threshold = 8
    else:  # 一般賽道
        top5_threshold = 7
    
    # 預測 Top5 = 預測時間 Top {threshold}
    predicted_top5 = predictions.nsmallest(top5_threshold, 'predicted_time')['driver'].values
    
    return predicted_top5[:5]  # 返回前 5 名
```

---

### 策略 5: **Ensemble 排名融合** 🔗

**原理**: 結合多個排名來源

```python
def ensemble_ranking(predictions_df):
    """
    融合多個排名指標
    """
    # 1. 預測圈速排名（模型輸出）
    rank_by_time = predictions_df['predicted_time'].rank()
    
    # 2. FP3 排名（歷史參考）
    rank_by_fp3 = predictions_df['fp3_relative_position']
    
    # 3. 車手能力排名（is_top_driver）
    rank_by_ability = predictions_df['is_top_driver'].apply(
        lambda x: 3 if x == 1 else 15  # 頂尖車手假設排名 3，其他 15
    )
    
    # 加權融合
    weights = {
        'time': 0.70,      # 70% 來自預測時間
        'fp3': 0.20,       # 20% 來自 FP3 排名
        'ability': 0.10    # 10% 來自車手能力
    }
    
    final_rank = (
        rank_by_time * weights['time'] +
        rank_by_fp3 * weights['fp3'] +
        rank_by_ability * weights['ability']
    )
    
    predictions_df['ensemble_rank'] = final_rank.rank()
    
    return predictions_df
```

---

## 📊 實驗計畫

### 實驗 1: Top5 聚焦預測 vs 基準
```powershell
# 基準（現有 v3.8）
python predict_v38_2025.py

# Top5 優化版本
python predict_v38_2025_top5_optimized.py

# 對比結果
python compare_top5_strategies.py
```

**評估指標**:
- Top5 準確率（主要指標）
- Top5 車手匹配率（5 個中對幾個）
- Top5 位置匹配率（對的車手在對的位置）
- Spearman 相關性（整體排序）

---

### 實驗 2: 賽道分類測試

```python
# 將賽道分為 3 類
track_categories = {
    '低改進': ['Monaco', 'Italy', 'Saudi Arabia'],
    '中改進': ['Japan', 'Bahrain', 'Abu Dhabi'],
    '高改進': ['Hungary', 'Netherlands', 'Belgium']
}

# 分別測試策略效果
for category, tracks in track_categories.items():
    test_top5_strategies(tracks, category)
```

---

### 實驗 3: 車手穩定性分組

```python
# 分析歷史穩定性
stability = analyze_ranking_stability()

# 穩定車手（VER, HAM, LEC）：FP3 排名權重 0.8
# 不穩定車手（PER, TSU）：FP3 排名權重 0.3

# 測試效果
test_stability_weighted_prediction()
```

---

## 🎯 推薦實施順序

### Phase 1: 快速驗證（1 天）⚡
1. ✅ 創建 `predict_v38_2025_top5_optimized.py`
2. ✅ 實現**策略 1: Top5 加權預測**
3. ✅ 對比 v3.8 基準

**成功標準**: Top5 準確率提升 5-10%

---

### Phase 2: 深度優化（2-3 天）📊
1. 實現**策略 4: 賽道特定閾值**
2. 分析車手排名穩定性
3. 創建賽道分類模型

**成功標準**: 高改進賽道 Top5 準確率達 70%+

---

### Phase 3: 進階融合（3-5 天）🔗
1. 實現**策略 5: Ensemble 排名融合**
2. 開發動態權重系統
3. 整合所有策略

**成功標準**: 平均 Top5 準確率達 75%+

---

## 📈 預期效果

| 策略 | 實施難度 | 預期提升 | 適用場景 |
|------|----------|----------|----------|
| **Top5 加權** | ⭐ 低 | +5-10% | 所有賽道 |
| **賽道閾值** | ⭐⭐ 中 | +8-12% | 高改進賽道 |
| **分組預測** | ⭐ 低 | +15-20% | 容錯場景 |
| **Ensemble** | ⭐⭐⭐ 高 | +10-15% | 綜合優化 |

---

## 🔬 需要重新訓練的情況

**僅在以下情況需要重新訓練**:

### 情況 1: 添加新特徵
```python
# 例如：添加車手排名穩定性特徵
df['driver_rank_volatility'] = df['driver'].map(stability_stats)
```

### 情況 2: 改變損失函數
```python
# 自定義損失：對 Top5 誤差加權
def top5_weighted_loss(y_true, y_pred):
    # 實際 Top5 車手的誤差 × 3
    # 其他車手的誤差 × 1
    ...
```

### 情況 3: 樣本加權
```python
# 訓練時對 Top5 樣本賦予更高權重
sample_weights = np.where(
    df['actual_q_time'].rank() <= 5,
    3.0,  # Top5 權重
    1.0   # 其他權重
)

model.fit(X, y, sample_weight=sample_weights)
```

---

## ✅ 結論

### 立即可行的策略 ⚡
1. ✅ **Top5 聚焦預測**（策略 1）- 無需重新訓練
2. ✅ **賽道特定閾值**（策略 4）- 無需重新訓練
3. ✅ **分組預測**（策略 3）- 後處理優化

### 未來可選的優化 🚀
1. 添加車手穩定性特徵 → 需要重新訓練
2. Top5 加權損失函數 → 需要重新訓練
3. 樣本加權訓練 → 需要重新訓練

### 推薦路徑 🎯
**先實施策略 1 + 4，驗證效果後再決定是否重新訓練**

---

**下一步**: 創建 `predict_v38_2025_top5_optimized.py`
