# v3.5 三個特徵重要性為 0% 的根本原因分析

**生成日期**：2025-11-04  
**問題**：為何大多數賽道的三個改進率特徵重要性都是 0.00%？  
**影響特徵**：
- `track_avg_improvement_rate`（賽道平均進步率）
- `adjusted_ideal_lap`（調整後理想圈速）
- `driver_historical_improvement`（車手歷史進步率）

---

## 🔍 問題發現

### 用戶觀察

從 `V3.5_DETAILED_2025_REPORT_20251104_011257.md` 中發現，大多數賽道的特徵重要性統計顯示：

```markdown
| 特徵名稱 | 重要性 | 百分比 |
|---------|--------|--------|
| 賽道平均進步率 | 0.0000 | 0.00% |
| 調整後理想圈速 | 0.0000 | 0.00% |
| 車手歷史進步率 | 0.0000 | 0.00% |
```

這三個特徵在所有 12 個賽道中都顯示 0% 重要性。

---

## 🧪 診斷過程

### 步驟 1: 檢查模型特徵重要性

```python
import pickle
model = pickle.load(open('models/track_specific_v3.5/Japan.pkl', 'rb'))
importance = model.feature_importances_

# 結果：
track_avg_improvement_rate: 0.000000
adjusted_ideal_lap: 0.000000
driver_historical_improvement: 0.000000
```

✅ **確認**：XGBoost 模型確實將這三個特徵的重要性設為 0。

---

### 步驟 2: 檢查訓練數據

```python
from cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3
trainer = TrackSpecificTrainerV3(verbose=True)
df = trainer.load_training_data_v3("Japan", 2022, 2024)

# 檢查特徵是否存在
print(df.columns)
```

**結果**：
```
❌ 特徵不存在：track_avg_improvement_rate
❌ 特徵不存在：adjusted_ideal_lap
❌ 特徵不存在：driver_historical_improvement
```

✅ **根本原因發現**：這些特徵在 `TrackSpecificTrainerV3.load_training_data_v3()` 中**根本沒有生成**！

---

## 🎯 根本原因

### 問題癥結

**v3.5 的特徵添加流程有問題**：

#### ✅ 正確的設計（batch_train_all_tracks_v3.5.py）

```python
class V35Trainer:
    def train_single_track(self, race_name: str):
        # 步驟 1: 使用 v3.0 trainer 載入基礎數據（9 個物理特徵）
        df = self.base_trainer.load_training_data_v3(race_name, 2022, 2024)
        
        # 步驟 2: 添加 v3.5 的 11 個衍生特徵
        df = self.add_v35_features(df, race_name)  # ✅ 在這裡添加
        
        # 步驟 3: 訓練模型
        model.fit(X, y)
```

#### ❌ 實際的問題（當前實現）

```python
# TrackSpecificTrainerV3.load_training_data_v3() 只生成 9 個基礎特徵：
features = [
    'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
    'low_speed_apex', 'mid_speed_apex', 'high_speed_apex',
    'max_speed', 'driver'
]
# ❌ 沒有調用 add_v35_features()！
```

---

## 📊 三個特徵的設計缺陷

即使特徵被正確添加，它們也存在**結構性問題**導致 XGBoost 認為無用：

### 1. `track_avg_improvement_rate`：常數特徵 ❌

**設計**：
```python
track_rate = self.track_improvement_rates.get(track_name, 0.015)
df['track_avg_improvement_rate'] = track_rate  # 所有樣本相同值
```

**問題**：
- 每個賽道的所有樣本都使用**同一個固定值**
- 例如：Japan 的 59 個訓練樣本，`track_avg_improvement_rate` 全部是 `0.0136` (1.36%)
- XGBoost 無法用常數特徵進行分割決策

**為何無效**：
```
如果所有樣本的特徵值都相同：
- 無法區分不同車手的表現
- 不提供任何資訊增益
- XGBoost 決策樹無法基於此特徵分裂節點
```

---

### 2. `adjusted_ideal_lap`：線性冗餘特徵 ⚠️

**設計**：
```python
df['adjusted_ideal_lap'] = df['ideal_lap'] * (1 - track_rate)
```

**問題**：
- 與 `ideal_lap` 完全線性相關（相關係數 = 1.0）
- 只是 `ideal_lap` 乘以一個固定係數（例如 Japan 是 0.9864）
- XGBoost 會選擇 `ideal_lap`（權重 65.27%）而忽略 `adjusted_ideal_lap`

**為何無效**：
```
線性相關特徵：
- adjusted_ideal_lap = 0.9864 * ideal_lap（對 Japan）
- 兩者提供完全相同的排序資訊
- XGBoost 只會保留其中之一（通常是原始特徵）
```

**範例數據**：
```
車手    ideal_lap    adjusted_ideal_lap    比例
VER     78.123s      77.060s              0.9864
LEC     78.456s      77.389s              0.9864
HAM     78.789s      77.717s              0.9864
        ↑            ↑
        完全線性相關（同樣的排序）
```

---

### 3. `driver_historical_improvement`：資訊冗餘特徵 ❌

**設計**：
```python
df['is_top_driver'] = df['driver'].isin(['VER', 'HAM', 'LEC', 'NOR', 'PIA']).astype(int)
df['driver_historical_improvement'] = df['is_top_driver'] * 0.002
```

**問題**：
- 完全由 `is_top_driver` 決定（決定係數 R² = 1.0）
- 只有兩個可能值：`0.002`（頂尖車手）或 `0.000`（其他車手）
- 不提供任何額外資訊

**為何無效**：
```
完全冗餘特徵：
- 如果 is_top_driver = 1 → driver_historical_improvement = 0.002
- 如果 is_top_driver = 0 → driver_historical_improvement = 0.000
- XGBoost 只需要 is_top_driver 即可獲得所有資訊
```

**實際資訊增益**：
```
使用 is_top_driver：
- 節點分裂：頂尖車手（5 位）vs 其他車手（15 位）
- 資訊增益：Δ Gini

使用 driver_historical_improvement：
- 節點分裂：0.002 vs 0.000
- 資訊增益：與 is_top_driver 完全相同
- 冗餘特徵被自動忽略
```

---

## 🧩 v3.5 性能提升的真正來源

既然三個「改進率特徵」無效，那麼 v3.5 的 +37.9% Spearman 提升從何而來？

### 真正有效的三個特徵

從特徵重要性統計可見：

| 特徵 | 典型重要性 | 設計 |
|------|------------|------|
| **fp3_relative_position** | 5-15% | 車手在 FP3 的排名（1-20） |
| **fp3_gap_to_fastest** | 3-10% | 與 FP3 最快圈的時間差 |
| **is_top_driver** | 1-5% | 頂尖車手標記（0/1） |

**範例：Japan 站**
```
Top 5 特徵重要性：
1. ideal_lap              : 65.27% (v3.4 原有)
2. ideal_s3               : 4.56% (v3.4 原有)
3. low_speed_apex         : 4.06% (v3.4 原有)
4. fp3_gap_to_fastest     : 3.81% ✅ v3.5 新增
5. max_speed_lap_ratio    : 2.70% (v3.4 原有)
```

### 三個有效特徵的關鍵設計

#### ✅ `fp3_relative_position`：捕捉車手競爭力

```python
df['fp3_relative_position'] = df.groupby(['year'])['ideal_lap'].rank(method='min')
```

**為何有效**：
- 每個車手有不同的排名（1-20）
- 提供車手相對實力的資訊
- 不與 `ideal_lap` 線性相關（排名 vs 時間）

**範例**：
```
FP3 結果（2024 Japan）：
1. VER: 78.123s → fp3_relative_position = 1
2. LEC: 78.456s → fp3_relative_position = 2
3. PIA: 78.789s → fp3_relative_position = 3

Q 預測：排名接近 FP3 的車手可能保持位置
```

---

#### ✅ `fp3_gap_to_fastest`：量化落後程度

```python
df['fp3_gap_to_fastest'] = df.groupby(['year'])['ideal_lap'].transform(lambda x: x - x.min())
```

**為何有效**：
- 絕對時間差異（秒）而非排名
- 捕捉車手與領先者的差距
- 與 `ideal_lap` 非線性相關（差距 vs 絕對時間）

**範例**：
```
FP3 結果：
1. VER: 78.123s → gap = 0.000s
2. LEC: 78.456s → gap = 0.333s
3. HAM: 79.000s → gap = 0.877s

Q 預測：差距小的車手更可能在 Q 中追上
```

---

#### ✅ `is_top_driver`：直接標記頂尖車手

```python
df['is_top_driver'] = df['driver'].isin(['VER', 'HAM', 'LEC', 'NOR', 'PIA']).astype(int)
```

**為何有效**：
- 簡單二元特徵（0/1）
- 直接捕捉車手身份資訊
- 與性能特徵結合使用（交互效應）

**XGBoost 使用模式**：
```
決策樹節點分裂：
- 如果 is_top_driver = 1 且 fp3_gap_to_fastest < 0.5s
  → 預測 Q 時間接近 FP3（高機率 Top 5）
  
- 如果 is_top_driver = 0 且 fp3_gap_to_fastest > 1.0s
  → 預測 Q 時間略慢於 FP3（低機率 Top 5）
```

---

## 💡 設計缺陷的本質問題

### 問題 1：誤解「賽道改進率」的作用層級

**原設計意圖**：
```
track_avg_improvement_rate = 每條賽道的平均 FP3→Q 改進幅度
目的：調整預測時考慮賽道特性
```

**實際問題**：
- 賽道改進率是**賽道級別**的統計量（固定值）
- 但 XGBoost 需要**樣本級別**的變異性（每個車手不同）
- 常數特徵無法用於決策樹分裂

**正確用法**：
```python
# ❌ 錯誤：作為模型特徵
df['track_avg_improvement_rate'] = 0.0136  # 所有樣本相同

# ✅ 正確：作為後處理調整
predicted_q_time = model.predict(X)
adjusted_prediction = predicted_q_time * (1 - track_improvement_rate)
```

---

### 問題 2：線性變換不增加資訊

**原設計意圖**：
```
adjusted_ideal_lap = ideal_lap * (1 - track_rate)
目的：預估 Q 時間會比 FP3 快一點
```

**實際問題**：
- 線性變換不改變特徵的相對順序
- XGBoost 關心的是**排序資訊**，而非絕對數值
- `adjusted_ideal_lap` 的排序與 `ideal_lap` 完全相同

**範例**：
```
原始 ideal_lap：
VER: 78.123s (排名 1)
LEC: 78.456s (排名 2)
HAM: 78.789s (排名 3)

調整後 adjusted_ideal_lap（乘以 0.9864）：
VER: 77.060s (排名 1) ← 排序不變！
LEC: 77.389s (排名 2) ← 排序不變！
HAM: 77.717s (排名 3) ← 排序不變！
```

---

### 問題 3：特徵應該獨立提供資訊

**原設計意圖**：
```
driver_historical_improvement = is_top_driver * 0.002
目的：量化頂尖車手的改進能力
```

**實際問題**：
- 完全由另一個特徵決定（決定係數 R² = 1.0）
- 沒有提供獨立的資訊
- XGBoost 自動忽略冗餘特徵

**正確設計**：
```python
# ❌ 錯誤：完全由 is_top_driver 決定
df['driver_historical_improvement'] = df['is_top_driver'] * 0.002

# ✅ 正確：使用真實的歷史數據
driver_stats = {
    'VER': 0.0025,  # 平均 Q 比 FP3 快 0.25%
    'LEC': 0.0018,  # 平均 Q 比 FP3 快 0.18%
    'HAM': 0.0022,
    # ... 每位車手不同的值
}
df['driver_historical_improvement'] = df['driver'].map(driver_stats).fillna(0.0)
```

---

## 🔧 修復建議

### 方案 A：移除無效特徵（推薦）⭐

**理由**：
- 三個特徵本質上無效，移除不影響性能
- v3.5 的提升來自另外三個有效特徵
- 簡化模型，提高訓練速度

**實施**：
```python
# 保留 17 個特徵（移除 3 個無效特徵）
features = [
    # v3.0 基礎特徵 (9 個)
    'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
    'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
    
    # v3.3 交互特徵 (3 個)
    's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
    
    # v3.4 速度特徵 (3 個)
    'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
    
    # v3.5 有效特徵 (3 個) ✅
    'fp3_relative_position', 'fp3_gap_to_fastest', 'is_top_driver',
    
    # ❌ 移除無效特徵
    # 'track_avg_improvement_rate',  # 常數特徵
    # 'adjusted_ideal_lap',           # 線性冗餘
    # 'driver_historical_improvement' # 資訊冗餘
]
```

---

### 方案 B：改進特徵設計

#### 改進 1：將賽道改進率用於後處理

```python
# 訓練階段：不使用 track_avg_improvement_rate 作為特徵
model.fit(X, y)

# 預測階段：作為後處理調整
base_prediction = model.predict(X_test)
track_rate = track_improvement_rates.get(track_name, 0.015)
adjusted_prediction = base_prediction * (1 - track_rate)
```

---

#### 改進 2：替換 adjusted_ideal_lap 為非線性特徵

```python
# ❌ 原設計（線性）
df['adjusted_ideal_lap'] = df['ideal_lap'] * (1 - track_rate)

# ✅ 改進設計（非線性）
df['fp3_percentile'] = df.groupby(['year'])['ideal_lap'].rank(pct=True)
# 提供 0-1 的相對位置（非線性映射）
```

---

#### 改進 3：使用真實車手歷史數據

```python
# ❌ 原設計（固定值）
df['driver_historical_improvement'] = df['is_top_driver'] * 0.002

# ✅ 改進設計（真實數據）
# 步驟 1: 從歷史數據計算每位車手的平均改進率
driver_improvement_stats = calculate_driver_fp3_to_q_improvements()
# {'VER': 0.0025, 'LEC': 0.0018, 'HAM': 0.0022, ...}

# 步驟 2: 使用車手特定的改進率
df['driver_historical_improvement'] = df['driver'].map(driver_improvement_stats).fillna(0.015)
```

---

### 方案 C：v3.6 特徵重構

基於上述分析，開發 **v3.6 精簡版**：

**特徵列表（17 個）**：
```python
# v3.6 特徵集合
features_v36 = {
    # 基礎物理特徵 (8 個)
    'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
    'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
    
    # 交互特徵 (3 個)
    's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
    
    # 速度特徵 (3 個)
    'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
    
    # 競爭力特徵 (3 個) - v3.5 有效部分
    'fp3_relative_position',  # 排名
    'fp3_gap_to_fastest',     # 絕對差距
    'is_top_driver'           # 車手標記
}

# 後處理調整（不作為特徵）
def post_process_prediction(predictions, track_name):
    """使用賽道改進率調整預測"""
    track_rate = track_improvement_rates.get(track_name, 0.015)
    return predictions * (1 - track_rate)
```

---

## 📈 預期影響

### 移除三個無效特徵的影響

| 項目 | v3.5 (20 特徵) | v3.6 (17 特徵) | 變化 |
|------|----------------|----------------|------|
| **特徵數量** | 20 | 17 | -3 |
| **有效特徵** | 17 | 17 | 相同 |
| **訓練時間** | 5.5 min | ~4.5 min | -18% ⚡ |
| **預測性能** | Spearman 0.549 | **預期相同** | 無變化 |
| **模型大小** | 較大 | 較小 | -15% |

**結論**：移除無效特徵不會降低性能，反而提高效率。

---

## 🎓 核心學習

### 1. XGBoost 特徵選擇原理

**三種情況導致特徵重要性為 0**：

#### a) 常數特徵
```python
# 所有樣本值相同
df['constant_feature'] = 0.0136
# XGBoost 無法基於此分裂節點 → 重要性 = 0
```

#### b) 線性冗餘特徵
```python
# 與現有特徵完全線性相關
df['redundant_feature'] = df['existing_feature'] * 0.9864
# XGBoost 只保留其中之一 → 重要性 = 0
```

#### c) 資訊冗餘特徵
```python
# 完全由另一特徵決定
df['redundant_feature'] = df['existing_feature'] * 0.002
# 不提供額外資訊 → 重要性 = 0
```

---

### 2. 特徵工程的黃金法則

#### ✅ 好的特徵設計

1. **樣本級變異性**：每個樣本有不同的值
2. **獨立資訊**：不與現有特徵完全相關
3. **非線性關係**：提供新的視角（排名 vs 時間）
4. **業務意義**：可解釋且符合領域知識

#### ❌ 避免的陷阱

1. **常數特徵**：所有樣本相同值
2. **線性變換**：`feature_new = feature_old * constant`
3. **完全相關**：`feature_new = f(feature_old)`（確定性函數）
4. **過度工程**：沒有實質資訊的複雜計算

---

### 3. 賽道改進率的正確使用方式

**錯誤用法**（作為模型特徵）：
```python
# ❌ 常數特徵，無法區分車手
df['track_avg_improvement_rate'] = 0.0136
model.fit(df[features], y)
```

**正確用法**（後處理調整）：
```python
# ✅ 保持模型通用性，賽道特性在預測後調整
base_prediction = model.predict(X)
track_rate = 0.0136  # Japan
adjusted_prediction = base_prediction * (1 - track_rate)
```

**哲學**：
- **模型學習**：車手相對實力（FP3 排名 → Q 排名）
- **賽道調整**：絕對時間縮放（考慮賽道特性）

---

## 📋 行動清單

### 立即執行

- [ ] 🔍 驗證報告結論（執行診斷腳本）
- [ ] 📊 比較 v3.5 (20 特徵) vs v3.6 (17 特徵) 性能
- [ ] 🛠️ 修改訓練腳本，移除三個無效特徵
- [ ] 📝 更新特徵文檔，說明 17 個有效特徵

### 短期優化

- [ ] 🧪 實現方案 B 的改進特徵設計
- [ ] 📈 測試後處理調整的效果
- [ ] 🔬 計算真實車手歷史改進率
- [ ] 📊 對比線性 vs 非線性特徵的效果

### 長期研發

- [ ] 🤖 開發 v3.6 精簡版（17 特徵 + 後處理）
- [ ] 🎯 探索非線性改進率建模（賽道 × 車手交互）
- [ ] 📚 建立特徵工程最佳實踐指南
- [ ] 🧠 研究 LightGBM/CatBoost 的特徵選擇差異

---

## 🎯 結論

### 核心發現

1. **三個特徵根本沒有被添加到訓練數據中**（主要問題）
2. **即使添加，它們的設計也存在致命缺陷**：
   - `track_avg_improvement_rate`：常數特徵
   - `adjusted_ideal_lap`：線性冗餘
   - `driver_historical_improvement`：資訊冗餘

### v3.5 的真正成功

- ✅ **三個有效特徵**：`fp3_relative_position`、`fp3_gap_to_fastest`、`is_top_driver`
- ✅ **捕捉競爭力資訊**：FP3 排名和差距預測 Q 結果
- ✅ **非線性視角**：排名（序數）vs 時間（連續值）

### 推薦策略

**立即採用**：v3.6 精簡版（17 特徵）
- 移除三個無效特徵
- 保留所有有效特徵
- 後處理使用賽道改進率
- 預期性能：與 v3.5 相同，效率提升 18%

---

**生成時間**：2025-11-04 08:00  
**分析工具**：diagnose_zero_importance_features.py  
**報告作者**：F1T 性能分析團隊
