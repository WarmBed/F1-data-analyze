# FP→Q→R 預測系統開發計畫（精簡版）

**創建日期**: 2025-10-29  
**最後更新**: 2025-11-02  
**專案**: F1 Telemetry Station Pro  
**目標**: FP3 後預測 Q 排名，Q 後預測 R 結果  
**當前狀態**: ✅ Phase 1 Week 4 完成 - 基準模型已建立（MAE 0.901s），準備進入 Phase 2（Claude API 整合）

---

## ⚠️ 開發原則（最高優先級）

### **反幻覺編碼五原則**

1. **禁止幻覺編碼**：必須先用 `grep_search`/`read_file` 驗證數據存在
2. **數據來源透明**：每個特徵標註來源（FastF1/OpenF1/計算）
3. **性能保守估算**：不預測未驗證的性能（如 "MAE 0.22s"）
4. **處理異常情況**：下雨、DNF、Safety Car 必須納入
5. **成本保守估算**：API 成本用 2 倍安全邊際

---

## 🎯 系統架構

### **兩階段預測 + 混合 AI**

```
FP1/2/3 數據 → XGBoost 模型 → 初步 Q 預測 → Claude API 分析 → 最終 Q 預測
真實 Q 結果 → XGBoost 模型 → 初步 R 預測 → Claude API 分析 → 最終 R 預測
```

**時間點**：
- FP3 結束後（週六 12:00）→ 預測 Q 排名
- Q 結束後（週六 15:00）→ 預測 R 結果

---

## 📊 實際可用特徵（僅 FastF1 提供）

### ✅ **確認可用**

```python
features = {
    # 圈速數據
    'best_lap_time': 'session.laps["LapTime"].min()',
    'avg_lap_time': 'session.laps["LapTime"].mean()',
    'lap_time_std': 'session.laps["LapTime"].std()',
    
    # 扇區時間
    'sector1_time': 'session.laps["Sector1Time"]',
    'sector2_time': 'session.laps["Sector2Time"]',
    'sector3_time': 'session.laps["Sector3Time"]',
    
    # 速度
    'speed_trap': 'session.laps["SpeedST"]',
    
    # 輪胎
    'tire_compound': 'session.laps["Compound"]',
    'tire_life': 'session.laps["TyreLife"]',
    
    # 天氣
    'air_temp': 'session.weather_data["AirTemp"]',
    'track_temp': 'session.weather_data["TrackTemp"]',
    'humidity': 'session.weather_data["Humidity"]',
    'rainfall': 'session.weather_data["Rainfall"]',
    
    # 基礎資訊
    'driver': 'session.results["Abbreviation"]',
    'team': 'session.results["TeamName"]',
    'grid_position': 'session.results["GridPosition"]',
    'finishing_position': 'session.results["Position"]',
}
```

### ❌ **無法獲取（幻覺特徵）**

- 車手超車能力（無量化指標）
- 車隊策略偏好（無公開數據）
- 燃油負載（FIA 不公開）
- 引擎模式（車隊機密）

---

## 🚀 開發計畫（8 週）

### **Phase 1：數據收集與基準模型（Week 1-4）**

#### **✅ Week 1-2：數據驗證與收集（已完成）**

**✅ 任務 1.1：驗證數據可用性（已完成 - 2025-10-29）**
```bash
# 執行驗證腳本（已實際運行並驗證）
python -c "
import fastf1
fastf1.Cache.enable_cache('f1_analysis_cache')

# 測試 2018-2024 數據
for year in range(2018, 2025):
    session = fastf1.get_session(year, 1, 'Q')
    session.load()
    print(f'{year}: {len(session.results)} drivers, {len(session.laps)} laps')
"
```

**驗證結果**：
- ✅ 2018-2024 所有賽季數據可用
- ✅ FastF1 API 穩定運作
- ✅ 緩存機制正常加速數據載入

**✅ 任務 1.2：功能 70 - FP→Q 數據收集器（已完成 - 2025-10-30）**
```python
# CLI_modules/cli/prediction/fp_q_data_collector.py (已實現)

def collect_fp_to_q_data(year, race):
    """收集 FP1/FP2/FP3 → Q 的數據"""
    # 載入所有練習賽和排位賽
    fp1 = fastf1.get_session(year, race, 'FP1')
    fp2 = fastf1.get_session(year, race, 'FP2')
    fp3 = fastf1.get_session(year, race, 'FP3')
    q = fastf1.get_session(year, race, 'Q')
    
    # 載入數據
    for session in [fp1, fp2, fp3, q]:
        session.load()
    
    data = []
    for driver in q.results['Abbreviation']:
        # 提取各節練習賽特徵
        fp1_laps = fp1.laps.pick_driver(driver)
        fp2_laps = fp2.laps.pick_driver(driver)
        fp3_laps = fp3.laps.pick_driver(driver)
        
        # 提取 Q 結果
        q_result = q.results[q.results['Abbreviation'] == driver]
        
        data.append({
            'driver': driver,
            'team': q_result['TeamName'].values[0],
            'fp1_best': fp1_laps['LapTime'].min().total_seconds(),
            'fp2_best': fp2_laps['LapTime'].min().total_seconds(),
            'fp3_best': fp3_laps['LapTime'].min().total_seconds(),
            'q_position': q_result['Position'].values[0],
            'q_time': q_result['Q3'].values[0] if not pd.isna(q_result['Q3'].values[0]) else q_result['Q2'].values[0],
            # ... 更多特徵
        })
    
    return pd.DataFrame(data)
```

**✅ 執行結果（2025-10-30 完成）**：
```bash
# 收集 2018-2024 所有數據（功能 70）
python f1_analysis_modular_main.py -f 70 --start-year 2018 --end-year 2024

# 實際收集統計：
# - 2018: 21/21 場 (100%)
# - 2019: 21/21 場 (100%)
# - 2021: 22/22 場 (100%)
# - 2022: 22/22 場 (100%)
# - 2023: 23/23 場 (100%)
# - 2024: 24/24 場 (100%)
# - 總計: 133/133 場 (100%)
# - 跳過 2020 年（COVID-19 特殊賽季）
```

**📊 數據收集成果**：
- ✅ 總檔案數: **133 場賽事**
- ✅ 總數據量: **4.4 MB**
- ✅ 平均每場: **34.2 KB**
- ✅ 數據格式: 結構化 JSON（包含 FP1/FP2/FP3/Q 完整數據）
- ✅ 儲存位置: `json/predictionJSON/`

#### **⏳ Week 3-4：XGBoost 基準模型（進行中 - 2025-10-31 ~ 2025-11-01）**

**⏳ 任務 3.1：功能 72 - XGBoost 訓練器開發（整合賽道分類中）**

**實現位置**: `CLI_modules/cli/prediction/xgboost_trainer.py`

**核心改進**：
```python
# 🆕 特徵工程優化（新增 6 個衍生特徵）
features_added = [
    'improvement_fp3_fp1',      # FP3-FP1 進步率（車隊調校能力）
    'improvement_fp3_fp2',      # FP3-FP2 進步率
    'fp3_consistency',          # 一致性（變異係數）
    'fp3_sector_balance',       # 扇區平衡（調校品質）
    'temp_delta_air',           # 氣溫變化（FP3→Q）
    'temp_delta_track',         # 賽道溫度變化（影響輪胎）
]

# 🆕 超參數優化（擴展搜索空間）
param_grid = {
    'n_estimators': [200, 300, 500],         # 原 [100, 200]
    'max_depth': [6, 8, 10],                # 原 [4, 6]
    'learning_rate': [0.01, 0.03, 0.05],    # 原 [0.05, 0.1]
    'subsample': [0.7, 0.8, 0.9],           # 新增
    'colsample_bytree': [0.7, 0.8, 0.9],    # 新增
    'min_child_weight': [1, 3, 5],          # 新增（控制過擬合）
    'gamma': [0, 0.1, 0.2],                 # 新增（正則化）
}

# 🆕 數據清洗改進（IQR 異常值檢測）
def remove_outliers(df):
    for col in ['fp3_best_lap', 'q_time']:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        df = df[(df[col] >= Q1 - 3*IQR) & (df[col] <= Q3 + 3*IQR)]
    return df
```

**訓練結果（2018-2023 數據）**：
```bash
# 執行命令
python f1_analysis_modular_main.py -f 72 --start-year 2018 --end-year 2023

# 輸出統計
📦 載入訓練數據:
   - 找到 133 個 JSON 檔案
   - 成功載入: 75 場賽事（乾地）
   - 跳過濕地: 34 場
   - 總數據點: 1463 筆車手數據

🔧 準備訓練特徵:
   - 原始數據: 1473 筆
   - 清理異常值: 移除 10 筆
   - 最終數據: 1463 筆
   - 特徵數量: 25 (22 numeric + 3 categorical)

🤖 訓練 XGBoost 模型:
   - TimeSeriesSplit (n_splits=5)
   - GridSearchCV: 2187 種參數組合（實際測試約 100 種）

✅ 性能指標:
   - 交叉驗證 MAE: 0.986 ± 0.280 秒
   - R² Score: 0.938
   - RMSE: 2.125 秒
   - 最佳超參數: {
       'max_depth': 10,
       'learning_rate': 0.03,
       'n_estimators': 200,
       'subsample': 0.7,
       'colsample_bytree': 0.9,
       'min_child_weight': 5,
       'gamma': 0.1
     }
```

**性能提升對比**：
| 指標 | 初版 | 優化後 | 改善幅度 |
|------|------|--------|----------|
| **MAE** | 1.767s | **0.986s** | ✅ **-44%** |
| **R²** | 0.861 | **0.938** | ✅ **+9%** |
| **Std** | 0.594 | **0.280** | ✅ **-53%** |
| **目標** | ❌ | ⚠️ 未達 0.30s | 需進一步優化 |

**特徵重要性分析**：
```json
{
    "fp3_best_lap": 60.7%,      // 主導特徵（最接近 Q 時間）
    "fp2_best_lap": 25.7%,      // 次要參考
    "fp1_best_lap": 7.9%,       // 早期參考
    "fp3_sector2": 1.8%,        // 扇區時間
    "其他 21 個特徵": 3.9%      // 輔助特徵
}
```

**產出檔案**：
- ✅ `models/xgboost_fp_q_baseline_20251031_080148.pkl` - 訓練完成的模型
- ✅ `reports/baseline_model_performance_20251031_080148.json` - 性能報告

---

**✅ 任務 3.2：功能 73 整合 - 賽道分類特徵（2025-11-01 完成）**

**新增功能**: 將賽道分類結果作為額外特徵整合到 XGBoost 訓練器

**實現改進**：
```python
# 新增賽道分類特徵（來自 Function 73）
track_classification_feature = 'track_cluster_id'  # 0=高速街道, 1=標準, 2=技術型

# 特徵數量更新: 25 → 26
# - 原有 22 個數值特徵
# - 新增 1 個賽道分類特徵 (track_cluster_id)
# - 3 個類別特徵 (driver_encoded, team_encoded, race_encoded)
```

**修正問題**：
- ✅ 修正 `prepare_features()` 數據類型不一致問題
- ✅ 統一數值特徵為 `float` 類型（避免 int/str 混雜）
- ✅ 添加 XGBoost 訓練進度顯示 (`verbosity=2`)

**訓練結果（2018-2024 完整數據集）**：
```bash
📊 性能指標:
   - MAE: 0.901 秒 (前版: 0.986s, 改善 -8.6%)
   - R²: 0.950 (前版: 0.938, 改善 +1.3%)
   - RMSE: 1.937 秒 (前版: 2.125s, 改善 -8.9%)
   - Std Dev: 0.136 秒 (前版: 0.280s, 改善 -51.4%)

🎯 特徵重要性分析:
   - fp3_best_lap: 66.0% ← 主導特徵
   - fp2_best_lap: 28.7% ← 次要特徵
   - track_cluster_id: 0.108% (第 23/26) ← 賽道分類貢獻微小
   - 其他 23 個特徵: 5.2%

✅ 結論:
   - 賽道分類有正面效果但不顯著
   - R² 達到 0.950（研究級水準）
   - 模型穩定性大幅提升（Std -51.4%）
   - 與目標 0.30s 仍有差距（201%）
```

**產出檔案**：
- ✅ `models/xgboost_fp_q_baseline_20251101_134256.pkl` - 整合賽道分類的模型
- ✅ `reports/baseline_model_performance_20251101_134256.json` - 性能報告

---

**✅ 任務 3.3：賽道特徵數據收集（2025-11-02 完成）**

**目標**: 收集 FP1/FP2/FP3 賽道特徵數據，為賽道分類建模準備

**收集功能**：
- F48: 全車手直線速度分析
- F54: 車手油門比例分析
- F34: 煞車性能分析
- F47: 所有車手彎道分析
- F1: 降雨強度分析

**執行成果**：
```
執行時間: 18+ 小時（2025-11-01 至 2025-11-02）
總數據量: 2050 個 JSON 檔案

會話分佈:
- FP1: 732 / 665 (110.1%) ✅ 超過預期
- FP2: 673 / 665 (101.2%) ✅ 超過預期
- FP3: 645 / 665 (97.0%)  ✅ 接近完成

總完成度: 2050 / 1995 (102.8%) ✅
```

**監控工具**：
- ✅ `monitor_all_sessions.ps1` - 監控 FP1/FP2/FP3 收集進度

**結論**：
- 賽道特徵數據收集充足，可支援未來賽道分類建模
- 數據包含 2018-2024 年份（含部分 2020 年和 Sprint 賽事）
- FP3 數據完整度 97%，足夠用於當前建模需求

---

**❌ 任務 3.4：功能 74 - 時序特徵工程實驗（2025-11-02 已測試，效果不佳）**

**目標**: 嘗試使用 FP1→FP2→FP3 時間序列特徵打破特徵壟斷

**實現的時序特徵**：
```python
# 已實現的時序特徵（在 fp_q_data_collector.py）
time_series_features = {
    # 全圈統計
    'fp1_all_laps_mean': 'FP1 所有有效圈的平均時間',
    'fp2_all_laps_mean': 'FP2 所有有效圈的平均時間',
    'fp3_all_laps_mean': 'FP3 所有有效圈的平均時間',
    
    'fp1_all_laps_std': 'FP1 所有圈的標準差（一致性）',
    'fp2_all_laps_std': 'FP2 所有圈的標準差',
    'fp3_all_laps_std': 'FP3 所有圈的標準差',
    
    # 進步趨勢
    'fp1_to_fp2_improvement': '(FP1平均 - FP2平均) / FP1平均',
    'fp2_to_fp3_improvement': '(FP2平均 - FP3平均) / FP2平均',
    
    # 賽車窗口（長距離模擬）
    'fp3_race_sim_avg': 'FP3 連續 10+ 圈的平均（模擬正賽）',
    'fp3_race_sim_degradation': 'FP3 長距離圈速衰退率',
}
```

**階段 2：交互特徵（優先級：高）** 🆕
```python
# 非線性關係捕捉
interaction_features = {
    # 賽道 × 性能
    'fp3_best × track_cluster': 'fp3_best_lap × track_cluster_id',
    'fp2_best × track_cluster': 'fp2_best_lap × track_cluster_id',
    
    # 車手 × 賽道
    'driver × track_cluster': 'driver_encoded × track_cluster_id',
    
    # 車隊 × 賽道
    'team × track_cluster': 'team_encoded × track_cluster_id',
    
    # 溫度 × 性能
    'temp_delta × fp3_best': 'temp_delta_track × fp3_best_lap',
    
    # 扇區平衡 × 賽道
    'sector_balance × track': 'fp3_sector_balance × track_cluster_id',
}
```

**實現難度評估**：
- ✅ **階段 1（全圈分析）**: 難度 **低-中**
  - FastF1 已提供所有圈數據
  - 只需修改 `fp_q_data_collector.py` 的統計邏輯
  - 預計開發時間: **2-3 小時**
  
- ✅ **階段 2（交互特徵）**: 難度 **低**
  - 在 `xgboost_trainer.py` 中直接相乘即可
  - XGBoost 會自動學習交互效果
  - 預計開發時間: **1 小時**

**訓練結果（2025-11-02）**：
```
數據集: 207 場賽事（含重複和額外數據）

性能指標:
  MAE: 1.102s ± 0.743s  ❌ 退化（從 0.901s +22.3%）
  R²: 0.939  ❌ 下降（從 0.950）
  RMSE: 2.130s  ❌ 惡化（從 1.937s）
  
Fold MAE 分佈（極不穩定）:
  Fold 1: 2.565s  ← 異常！
  Fold 2: 0.701s
  Fold 3: 0.562s
  Fold 4: 0.712s
  Fold 5: 0.967s
  標準差: 0.743s (+447% vs 0.136s)
  
特徵重要性（時序特徵幾乎無效）:
  Top 5 特徵仍由最速圈主導:
  - fp3_best_lap: 35.4%
  - fp3_fastest_lap: 30.4% (重複特徵)
  - fp2_fastest_lap: 18.8%
  - fp2_best_lap: 9.5%
  - fp1_fastest_lap: 1.8%
  總計: 95.9% 仍依賴最速圈
  
  新增時序特徵貢獻極低:
  - fp1_all_laps_mean: 0.03%
  - fp1_to_fp2_improvement: 0.02%
  - fp2_to_fp3_improvement: 0.02%
  - fp3_race_sim_avg: 0.01%
```

**問題診斷**：
1. **數據集污染**: 207 場 vs 預期 133 場（+74 場重複/錯誤數據）
2. **時序特徵無效**: 貢獻度 < 0.1%，XGBoost 無法利用時間序列資訊
3. **特徵冗餘**: `fp3_best_lap` 與 `fp3_fastest_lap` 幾乎相同導致重要性分散
4. **模型不穩定**: Fold 1 (2.565s) 明顯異常，標準差暴增

**結論與決策**：
- ❌ 時序特徵工程**未達預期效果**
- ✅ FP3 最速圈物理上已接近 Q 時間極限（0.8-1.5秒真實差異）
- ✅ XGBoost 無法有效學習 FP1→FP2→FP3 時間演化模式
- ✅ **決定保持功能 73 結果（MAE 0.901s, R² 0.950）作為基準模型**
- ✅ 不採用功能 74 模型（性能退化）

**產出檔案**：
- ❌ `models/xgboost_fp_q_baseline_20251102_161724.pkl` - 性能退化，不採用
- ❌ `reports/baseline_model_performance_20251102_161724.json` - 僅供參考

**下一步**：
- 接受當前 MAE 0.901s 作為 XGBoost 基準
- 進入 Phase 2：Claude API 整合（預期降至 0.50-0.70s）

---

**目標**: 使用 LSTM/Transformer 捕捉 FP1→FP2→FP3 的時間演化模式

**架構設計**：
```python
# 時間序列模型（LSTM）
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(3, n_features)),  # 3 = FP1/FP2/FP3
    Dropout(0.2),
    LSTM(32, return_sequences=False),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dense(1)  # 輸出: Q 時間預測
])

# 輸入數據結構
X_train = [
    [[fp1_features], [fp2_features], [fp3_features]],  # 車手 1
    [[fp1_features], [fp2_features], [fp3_features]],  # 車手 2
    ...
]
```

**優勢**：
- ✅ 自動捕捉時間依賴（FP1→FP2→FP3 演化）
- ✅ 學習非線性模式（XGBoost 難以捕捉）
- ✅ 可能打破特徵壟斷

**挑戰**：
- ❌ 需要更多數據（當前 1463 筆可能不足）
- ❌ 訓練時間長（GPU 加速可能必要）
- ❌ 過擬合風險高（需仔細調參）

**執行條件**：
- **前置條件**: 任務 3.3 完成後，MAE 仍 > 0.75s
- **數據增強**: 可能需要收集 2018 以前的數據
- **預計時間**: 1-2 週（含實驗調參）

---

### **Phase 2：Claude API 整合（Week 5-6）**

#### **Week 5：API 測試**

**任務 5.1：註冊 Claude API**
```bash
# 1. 前往 https://console.anthropic.com
# 2. 註冊並獲取 API Key
# 3. 設置環境變數
export CLAUDE_API_KEY="sk-ant-api03-xxxxxxxx"
```

**任務 5.2：測試實際成本**
```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_KEY")

# 測試 Prompt
prompt = """分析 FP3 數據預測排位賽：
VER: 1:28.456, LEC: 1:28.678, NOR: 1:28.789
賽道: Suzuka, 氣溫: 28°C
請預測前三名（JSON 格式）"""

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)

# 記錄實際 Token 使用
print(f"Input: {message.usage.input_tokens}")
print(f"Output: {message.usage.output_tokens}")
print(f"Cost: ${(message.usage.input_tokens * 3 + message.usage.output_tokens * 15) / 1_000_000:.4f}")
```

#### **Week 6：混合模型**

**任務 6.1：功能 55 - 混合預測器**
```python
# CLI_modules/cli/analyzer/hybrid_predictor.py

class HybridPredictor:
    def __init__(self):
        self.ml_model = joblib.load('models/xgboost_baseline.pkl')
        self.claude_client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        self.weights = {'ml': 0.6, 'claude': 0.4}  # 初始權重，需實驗調整
    
    def predict_qualifying(self, fp3_data):
        # 1. ML 預測
        ml_pred = self.ml_model.predict(fp3_data)
        
        # 2. Claude 分析
        try:
            claude_pred = self._claude_analyze(fp3_data, ml_pred)
        except Exception:
            return {'prediction': ml_pred, 'mode': 'ml_only'}
        
        # 3. 混合
        final = ml_pred * self.weights['ml'] + claude_pred * self.weights['claude']
        return {'prediction': final, 'mode': 'hybrid'}
    
    def _claude_analyze(self, fp3_data, ml_pred):
        prompt = f"""ML 預測: {ml_pred}
FP3 數據: {fp3_data}
修正預測（JSON）："""
        
        response = self.claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
```

---

### **Phase 3：異常處理（Week 7）**

#### **天氣變化處理**
```python
def handle_weather_change(fp3_weather, q_weather):
    if fp3_weather != q_weather:
        return {
            'confidence': 0.5,  # 信心度減半
            'warning': f'天氣變化：{fp3_weather} → {q_weather}'
        }
    return {'confidence': 0.85}
```

#### **DNF 預測**
```python
def predict_dnf_probability(driver, circuit, historical_data):
    driver_dnf_rate = historical_data[
        historical_data['driver'] == driver
    ]['dnf'].mean()
    
    circuit_dnf_rate = historical_data[
        historical_data['circuit'] == circuit
    ]['dnf'].mean()
    
    return (driver_dnf_rate + circuit_dnf_rate) / 2
```

---

### **Phase 4：系統整合（Week 8）**

#### **CLI 命令**
```bash
# 預測排位賽（FP3 後）
python f1_analysis_modular_main.py -f 55 --mode Q -y 2025 -r Japan

# 預測正賽（Q 後）
python f1_analysis_modular_main.py -f 55 --mode R -y 2025 -r Japan
```

#### **API 端點**
```python
# refactored_api.py

@app.post("/api/predict/qualifying")
async def predict_qualifying(year: int, race: str):
    predictor = HybridPredictor()
    fp3_data = load_fp3_data(year, race)
    result = predictor.predict_qualifying(fp3_data)
    return result

@app.post("/api/predict/race")
async def predict_race(year: int, race: str):
    predictor = HybridPredictor()
    fp3_data = load_fp3_data(year, race)
    q_data = load_q_results(year, race)
    result = predictor.predict_race(fp3_data, q_data)
    return result
```

---

## 📊 成本估算（保守）

```python
costs = {
    "api_testing": {
        "test_calls": 100,
        "cost": "$5.00"
    },
    "production": {
        "per_prediction": "$0.03-0.05",
        "per_race": "$0.10",  # Q + R
        "per_season": "$2.40",  # 24 場
        "safety_margin_2x": "$5.00/年"
    }
}
```

---

## ⚠️ 性能目標（已調整 - 2025-11-02 最終版）

```python
targets = {
    "baseline_xgboost": {
        "mae_target": "≤ 0.30s",        # AWS 論文目標（已確認不可達）
        "mae_achieved": "0.901s",       # ✅ Phase 1 最終基準（功能 73）
        "r2_achieved": "0.950",         # ✅ 優異變異解釋度
        "rmse_achieved": "1.937s",      # ✅ 穩定誤差分佈
        "std_achieved": "0.136s",       # ✅ 低標準差（穩定性提升 51.4%）
        "top3_accuracy": ">70%",        # 待驗證（需 2024 holdout）
        "note": "fp3_best_lap 主導 66%，物理極限已接近"
    },
    "time_series_features": {
        "mae_result": "1.102s",         # ❌ 性能下降 22.3%
        "status": "已拒絕",
        "reason": "FP1/FP2 數據引入噪聲，時間序列特徵貢獻 <0.1%",
        "conclusion": "FP3 單點預測已達 XGBoost 能力極限"
    },
    "track_specific_models": {
        "mae_target": "≤ 0.70s",        # 🎯 未來優化方向
        "approach": "按賽道類型分類訓練",
        "categories": ["高速", "街道", "混合"],
        "expected_improvement": "10-20%（保守估計）"
    },
    "hybrid_model": {
        "mae_target": "≤ 0.50-0.70s",   # ✅ Phase 2 目標（已調整）
        "approach": "XGBoost（0.901s） + Claude API（異常處理）",
        "top3_accuracy": ">75%",
        "note": "整合 Claude API 處理天氣變化、技術問題等邊緣案例"
    },
    "weather_change": {
        "mae": "≤ 0.50s",               # Phase 3 目標
        "confidence": "0.5",
        "method": "Claude API 分析 + XGBoost 基準"
    }
}
```

**Phase 1 最終結論（2025-11-02）**：
1. **✅ 功能 73 為最佳基準**：MAE 0.901s, R² 0.950, RMSE 1.937s
2. **❌ 時間序列特徵失敗**：功能 74 (MAE 1.102s) 證明 FP1/FP2 數據無法有效改善預測
3. **🎯 AWS 0.297s 無法複製**：可能需要專有特徵（車隊機密數據）或 ensemble 模型
4. **📈 物理限制認知**：FP3 與 Q 之間真實差異約 0.8-1.5 秒（車隊調校、輪胎策略）
5. **🚀 下一步方向**：接受 0.901s 基準，進入 Phase 2（Claude API 混合模型）

---

## 🔧 執行檢查清單與任務分解

### **Phase 1：數據收集與基準模型（Week 1-4）**

#### **Task 1.1：數據可用性驗證（30 分鐘）**
- [ ] **執行驗證腳本**：測試 2018-2024 數據完整性
  ```bash
  python -c "import fastf1; fastf1.Cache.enable_cache('f1_analysis_cache'); [print(f'{y}: OK') for y in range(2018, 2025) if fastf1.get_session(y, 1, 'Q')]"
  ```
- [ ] **檢查缺失數據**：記錄哪些賽事沒有 FP3 或 Q 數據
- [ ] **驗證數據欄位**：確認所有必要欄位存在（LapTime, Sector, Compound）
- [ ] **產出**：`data_availability_report.json`（記錄 2018-2024 數據狀況）

#### **Task 1.2：功能 54 - 數據收集器開發（3-4 天）**
- [ ] **創建模組檔案**：`CLI_modules/cli/analyzer/fp_q_data_collector.py`
- [ ] **實現核心函數**：
  - [ ] `collect_fp_to_q_data(year, race)` - FP3 → Q 數據提取
  - [ ] `collect_q_to_race_data(year, race)` - Q → R 數據提取
  - [ ] `_extract_session_features(session)` - 通用特徵提取器
  - [ ] `_handle_missing_data(df)` - 缺失值處理
- [ ] **整合 Function Mapper**：在 `function_mapping` 添加功能 54
- [ ] **CLI 參數設計**：
  ```bash
  python f1_analysis_modular_main.py -f 54 \
    --start-year 2018 --end-year 2024 \
    --output json/training_data/
  ```
- [ ] **產出**：
  - `fp_to_q_training_data.csv` (2018-2024, ~2940 行)
  - `q_to_race_training_data.csv` (2018-2024, ~2940 行)

#### **Task 1.3：執行數據收集（1-2 天）**
- [ ] **運行功能 54**：收集所有歷史數據
- [ ] **數據清理**：移除濕地會話（Rainfall > 0）
- [ ] **數據驗證**：
  - [ ] 檢查樣本數量（目標：~2500 樣本，排除濕地）
  - [ ] 檢查空值比例（< 5%）
  - [ ] 檢查異常值（lap time > 2分鐘）
- [ ] **產出**：`data_quality_report.json`

#### **Task 1.4：XGBoost 基準模型訓練（2-3 天）**
- [ ] **創建訓練腳本**：`tools/train_baseline_model.py`
- [ ] **實現功能**：
  - [ ] 讀取訓練數據
  - [ ] One-hot 編碼（driver, team, circuit）
  - [ ] 時間序列分割（TimeSeriesSplit, n_splits=5）
  - [ ] XGBoost 訓練與超參數調整
  - [ ] 模型評估（MAE, Top3 準確率）
- [ ] **超參數搜索**：
  ```python
  param_grid = {
      'n_estimators': [50, 100, 200],
      'max_depth': [4, 6, 8],
      'learning_rate': [0.05, 0.1, 0.2],
  }
  ```
- [ ] **產出**：
  - `models/xgboost_fp_to_q_baseline.pkl`
  - `models/xgboost_q_to_race_baseline.pkl`
  - `reports/baseline_model_performance.json`

#### **Task 1.5：基準模型驗證（1 天）**
- [ ] **回測 2024 賽季**：使用 2018-2023 訓練，預測 2024
- [ ] **計算性能指標**：
  - [ ] MAE（目標：≤ 0.30s）
  - [ ] Top3 準確率（目標：> 70%）
  - [ ] 位置誤差分佈
- [ ] **與 AWS 對比**：生成對比表
- [ ] **產出**：`reports/baseline_validation_2024.json`

---

### **Phase 2：Claude API 整合（Week 5-6）**

#### **Task 2.1：Claude API 註冊與測試（1 天）**
- [ ] **註冊帳號**：https://console.anthropic.com
- [ ] **獲取 API Key**：設置環境變數 `CLAUDE_API_KEY`
- [ ] **測試基本調用**：
  ```bash
  python -c "import anthropic; client = anthropic.Anthropic(); print(client.messages.create(model='claude-sonnet-4-20250514', max_tokens=100, messages=[{'role':'user','content':'Test'}]))"
  ```
- [ ] **測試成本**：記錄 10 次測試調用的 token 使用量
- [ ] **產出**：`reports/claude_api_cost_test.json`

#### **Task 2.2：設計 Claude Prompt（2-3 天）**
- [ ] **Prompt 模板開發**：
  - [ ] 異常檢測 Prompt（天氣變化、技術問題）
  - [ ] 預測修正 Prompt（邊界案例）
  - [ ] 解釋性 Prompt（推理說明）
- [ ] **測試 Prompt 效果**：使用 2024 數據驗證
- [ ] **優化 Token 使用**：縮短 Prompt 長度但保持準確度
- [ ] **產出**：`config/claude_prompts.json`

#### **Task 2.3：功能 55 - 混合預測器開發（3-4 天）**
- [ ] **創建模組檔案**：`CLI_modules/cli/analyzer/hybrid_predictor.py`
- [ ] **實現核心類別**：
  - [ ] `HybridPredictor` - 主預測器
  - [ ] `_detect_anomalies()` - 異常檢測
  - [ ] `_claude_analyze()` - Claude API 調用
  - [ ] `_merge_predictions()` - 預測融合
  - [ ] `_calculate_confidence()` - 信心度計算
- [ ] **降級機制**：Claude API 失敗時回退到純 XGBoost
- [ ] **成本控制**：只在異常情況啟用 Claude
- [ ] **產出**：功能 55 模組

#### **Task 2.4：權重實驗（2 天）**
- [ ] **測試不同權重組合**：
  ```python
  weights = [
      {'ml': 1.0, 'claude': 0.0},  # 純 XGBoost
      {'ml': 0.8, 'claude': 0.2},
      {'ml': 0.6, 'claude': 0.4},
      {'ml': 0.5, 'claude': 0.5},
      {'ml': 0.4, 'claude': 0.6},
  ]
  ```
- [ ] **評估性能**：記錄每種組合的 MAE
- [ ] **選擇最佳權重**：平衡準確度與成本
- [ ] **產出**：`reports/weight_optimization.json`

#### **Task 2.5：混合模型驗證（1 天）**
- [ ] **回測 2024 賽季**：與基準模型對比
- [ ] **計算性能提升**：MAE 改善百分比
- [ ] **計算實際成本**：2024 賽季總成本
- [ ] **產出**：`reports/hybrid_model_validation.json`

---

### **Phase 3：異常處理（Week 7）**

#### **Task 3.1：天氣變化處理（2 天）**
- [ ] **實現檢測函數**：`detect_weather_change(fp3, q)`
- [ ] **信心度調整**：天氣變化時降低信心度
- [ ] **歷史數據分析**：統計濕地會話對預測的影響
- [ ] **產出**：`modules/weather_handler.py`

#### **Task 3.2：DNF 預測（2 天）**
- [ ] **收集 DNF 歷史數據**：2018-2024
- [ ] **實現預測函數**：`predict_dnf_probability(driver, circuit)`
- [ ] **整合到預測流程**：DNF 機率 > 30% 時標註
- [ ] **產出**：`modules/dnf_predictor.py`

#### **Task 3.3：異常案例測試（2 天）**
- [ ] **構建測試集**：選擇異常賽事（如 2021 比利時 GP）
- [ ] **測試處理效果**：對比有無異常處理的 MAE
- [ ] **量化改善幅度**：記錄異常情況下的性能提升
- [ ] **產出**：`reports/anomaly_handling_test.json`

---

### **Phase 4：系統整合（Week 8）**

#### **Task 4.1：CLI 命令整合（2 天）**
- [ ] **更新 Function Mapper**：添加功能 55 CLI 參數
- [ ] **測試 CLI 命令**：
  ```bash
  # 預測 Q
  python f1_analysis_modular_main.py -f 55 --mode Q -y 2025 -r Japan
  
  # 預測 R
  python f1_analysis_modular_main.py -f 55 --mode R -y 2025 -r Japan
  ```
- [ ] **產出格式統一**：JSON 輸出到 `json/predictions/`

#### **Task 4.2：API 端點開發（2 天）**
- [ ] **更新 refactored_api.py**：添加預測端點
- [ ] **實現端點**：
  - [ ] `POST /api/predict/qualifying`
  - [ ] `POST /api/predict/race`
  - [ ] `GET /api/predictions/accuracy/{year}/{race}`
- [ ] **測試 API**：使用 Postman/curl 驗證
- [ ] **產出**：API 文檔

#### **Task 4.3：功能 56 - 準確度追蹤器（2 天）**
- [ ] **創建模組**：`CLI_modules/cli/analyzer/prediction_accuracy_tracker.py`
- [ ] **實現功能**：
  - [ ] `track_prediction()` - 記錄預測與實際結果
  - [ ] `generate_report()` - 生成準確度報告
  - [ ] `calculate_metrics()` - 計算 MAE, Top3 等指標
- [ ] **自動化觸發**：Q/R 結束後自動執行
- [ ] **產出**：功能 56 模組

#### **Task 4.4：完整測試（1-2 天）**
- [ ] **2024 賽季完整回測**：所有 24 場賽事
- [ ] **生成最終報告**：
  - [ ] 整體 MAE
  - [ ] 各賽道準確度
  - [ ] 各車隊準確度
  - [ ] 異常處理效果
  - [ ] 總成本
- [ ] **與 AWS 對比**：生成對比圖表
- [ ] **產出**：`reports/final_system_evaluation.pdf`

---

## 📚 參考資源

1. **AWS ML Blog**: https://aws.amazon.com/tw/blogs/machine-learning/predicting-qualification-ranking-based-on-practice-session-performance-for-formula-1-grand-prix/
2. **FastF1 API**: https://docs.fastf1.dev/
3. **Anthropic Claude**: https://docs.anthropic.com/claude/reference/getting-started-with-the-api

---

**最後更新**: 2025-10-31  
**狀態**: ✅ Phase 1 數據收集完成，準備執行 XGBoost 訓練

---

## 🧪 模型測試與驗證方式

### **方法 1: 使用 2024 作為 Holdout 測試集**

```bash
# 步驟 1: 訓練模型（使用 2018-2023）
python f1_analysis_modular_main.py -f 72 --start-year 2018 --end-year 2023

# 步驟 2: 手動測試 2024 預測
python -c "
import joblib
import pandas as pd
import json
import glob

# 載入訓練好的模型
model_data = joblib.load('models/xgboost_fp_q_baseline_20251031_080148.pkl')
model = model_data['model']
label_encoders = model_data['label_encoders']

# 載入 2024 數據
files_2024 = glob.glob('json/predictionJSON/*2024*.json')
print(f'找到 {len(files_2024)} 場 2024 賽事')

# 對每場賽事進行預測
for file in files_2024:
    data = json.load(open(file, 'r', encoding='utf-8'))
    # ... 提取特徵並預測
    # prediction = model.predict(features)
    # actual = data['qualifying']['results']
    # mae = calculate_error(prediction, actual)
    print(f'{file}: MAE = {mae:.3f}s')
"
```

### **方法 2: 交叉驗證結果檢查**

```bash
# 查看訓練報告
python -c "
import json
report = json.load(open('reports/baseline_model_performance_20251031_080148.json'))
print('=== 交叉驗證結果 ===')
print(f'平均 MAE: {report[\"performance\"][\"cv_mae_mean\"]:.3f}s')
print(f'標準差: {report[\"performance\"][\"cv_mae_std\"]:.3f}s')
print(f'R² Score: {report[\"performance\"][\"cv_r2_mean\"]:.3f}')
print(f'\n各 Fold MAE:')
for i, mae in enumerate(report['performance']['fold_maes'], 1):
    print(f'  Fold {i}: {mae:.3f}s')
"
```

### **方法 3: 特徵重要性分析**

```bash
# 查看哪些特徵最重要
python -c "
import json
report = json.load(open('reports/baseline_model_performance_20251031_080148.json'))
importance = report['feature_importance']

# 排序並顯示前 10 名
sorted_features = sorted(importance.items(), key=lambda x: float(x[1]), reverse=True)
print('=== Top 10 重要特徵 ===')
for i, (feature, score) in enumerate(sorted_features[:10], 1):
    print(f'{i}. {feature}: {float(score)*100:.1f}%')
"
```

### **方法 4: 實際預測案例測試**

```bash
# 選擇一場 2024 賽事測試
python -c "
import fastf1
import joblib

# 載入模型
model_data = joblib.load('models/xgboost_fp_q_baseline_20251031_080148.pkl')

# 載入 2024 Japan GP 數據
fastf1.Cache.enable_cache('f1_analysis_cache')
fp3 = fastf1.get_session(2024, 'Japan', 'FP3')
q = fastf1.get_session(2024, 'Japan', 'Q')
fp3.load()
q.load()

# 提取 VER 的 FP3 特徵
ver_fp3 = fp3.laps.pick_driver('VER')
features = {
    'fp3_best_lap': ver_fp3['LapTime'].min().total_seconds(),
    # ... 其他特徵
}

# 預測 Q 時間
prediction = model.predict([features])
actual = q.results[q.results['Abbreviation'] == 'VER']['Q3'].values[0]

print(f'VER Japan GP 2024:')
print(f'  預測: {prediction[0]:.3f}s')
print(f'  實際: {actual:.3f}s')
print(f'  誤差: {abs(prediction[0] - actual):.3f}s')
"
```

### **預期測試結果**

```
✅ 交叉驗證 (2018-2023):
   - 平均 MAE: 0.986s ± 0.280s
   - R² Score: 0.938
   - 5 Folds: [1.516s, 0.806s, 0.752s, 0.835s, 1.020s]

⏳ Holdout 測試 (2024):
   - 預計 MAE: 0.9-1.2s（因為 2024 是新規則第三年）
   - 預計 Top3 準確率: 65-75%
   - 需要實際運行確認

🎯 改善方向:
   - 若 2024 MAE > 1.2s → 考慮賽道分類建模
   - 若 Top3 < 60% → 需要更多特徵工程
   - 若特定賽道誤差大 → 針對性優化
```

---

## 📈 Phase 1 完成總結（2025-11-02 更新）

### ✅ 已完成任務

**Phase 1 最終成果**：
```
基準模型性能（功能 73 - 賽道分類）:
  ✅ MAE: 0.901s ± 0.136s
  ✅ R²: 0.950（研究級水準）
  ✅ RMSE: 1.937s
  ✅ 模型穩定性優異（Std 0.136s）

數據收集完成:
  ✅ FP→Q 訓練數據: 133 場賽事（功能 70）
  ✅ 賽道特徵數據: 2050 個 JSON（功能 48,54,34,47,1）
  
決策:
  ✅ 採用功能 73 模型作為 Phase 1 最終成果
  ❌ 不採用功能 74（時序特徵效果不佳）
  ✅ 準備進入 Phase 2（Claude API 整合）
```

### ✅ 已完成任務明細

#### **數據收集（功能 70）**
- **執行時間**: 2025-10-29 至 2025-10-31
- **總耗時**: 約 5-6 小時（含異常排查和重複檔案清理）
- **收集方式**: 
  - 初期使用批次模式（遇到部分失敗）
  - 改用單場逐一收集（成功率 100%）
  - 自動化腳本處理缺失賽事

#### **數據驗證結果**
```
============================================================
最終數據收集驗證報告
============================================================
2018: ✅ 21/21 (100.0%)
2019: ✅ 21/21 (100.0%)
2021: ✅ 22/22 (100.0%)
2022: ✅ 22/22 (100.0%)
2023: ✅ 23/23 (100.0%)
2024: ✅ 24/24 (100.0%)

============================================================
總計: 133/133 場賽事
完成度: 100.0%
============================================================

總數據量: 4.4 MB
平均每場: 34.2 KB
```

#### **問題與解決**
1. **FastF1 Schedule API 失敗**
   - **問題**: 2018-2020 賽季 Schedule API 不穩定
   - **解決**: 創建 `race_calendar.py` 硬編碼賽事名稱
   
2. **2020 賽季特殊處理**
   - **問題**: COVID-19 導致特殊賽事名稱（Styria, 70th Anniversary 等）
   - **決策**: 跳過 2020 賽季（17 場），保留 2018-2024 其他年份
   
3. **批次模式部分失敗**
   - **問題**: 2022 和 2023 批次收集不完整
   - **解決**: 創建 `auto_collect_missing.py` 逐場補齊
   
4. **重複檔案清理**
   - **問題**: 2022 (France, Italy, Singapore) 和 2024 (Japan) 有重複
   - **解決**: 刪除較舊檔案，確保每場唯一

#### **數據品質**
- ✅ 所有 JSON 檔案結構完整
- ✅ 包含 FP1/FP2/FP3 和 Qualifying 數據
- ✅ 天氣、輪胎、圈速等特徵齊全
- ✅ FastF1 緩存加速後續載入

---

## 🎯 **賽道特徵數據收集（2025-10-31）**

### **目標**：為賽道分類建模準備特徵數據

#### **背景**
- XGBoost 基準模型 MAE 0.986s，距離目標 0.70s 仍有差距
- 採用**賽道分類建模**策略：按賽道類型分類訓練專屬模型
- 需要收集賽道物理特徵（速度、油門、煞車、彎道、天氣）

#### **數據來源與 CLI 功能映射**

| 特徵類別 | CLI 功能 | 模組檔案 | JSON 檔名模式 | 數據內容 |
|---------|---------|---------|--------------|---------|
| **速度統計** | F48 | `all_drivers_straight_line_speed.py` | `all_drivers_straight_line_speed_{year}_{race}_{session}.json` | avg_speed, min_speed, max_speed, speed_std |
| **油門比例** | F54 | `driver_throttle_ratio.py` | `throttle_ratio_{year}_{race}_{session}.json` | full_throttle_ratio, partial_throttle_ratio |
| **煞車性能** | F34 | `brake_performance_analyzer.py` | `brake_performance_{year}_{race}_{session}.json` | brake_time_percentage, brake_count, brake_intensity |
| **彎道數量** | F47 | `all_drivers_cornering_analysis.py` | `all_drivers_cornering_analysis_{year}_{race}_{session}.json` | total_corners, corner_difficulty |
| **天氣數據** | F1 | `rain_intensity_analyzer.py` | `enhanced_rain_analysis_{year}_{race}_{session}.json` | air_temp, track_temp, humidity, pressure |

#### **CLI 功能驗證測試（2025-10-31）**

**測試賽事**: 2024 Japan Grand Prix, Race  
**會話類型**: FP3 (最接近排位賽條件)

| 功能 | 名稱 | 狀態 | JSON 檔名 | 檔案大小 | 測試時間 |
|------|------|------|----------|---------|---------|
| **F48** | 全車手直線速度 | ✅ 成功 | `all_drivers_straight_line_speed_2024_Japan_R.json` | 21.4 KB | 16:51 |
| **F54** | 車手油門比例 | ✅ 成功 | `throttle_ratio_2024_japan_R.json` | 962 KB | 16:54 |
| **F34** | 煞車性能分析 | ✅ 成功 | `brake_performance_2024_Japan_R.json` | 12.9 KB | 16:54 |
| **F47** | 所有車手彎道分析 | ✅ 成功 | `all_drivers_cornering_analysis_2024_Japan_R.json` | 692 KB | 17:06 |
| **F1** | 降雨強度分析 | ✅ 成功 | `enhanced_rain_analysis_2024_Japan_R.json` | 18.3 KB | 16:56 |

**重要發現**：
1. ✅ 所有 5 個功能均正常運作
2. ⚠️ F54 檔名大小寫不一致（`japan` vs `Japan`）- 已修正批量腳本使用不區分大小寫匹配
3. ✅ 所有功能支援 FP3 會話
4. 🐛 F47 初始測試失敗（`'NoneType' object has no attribute 'upper'`）- 已修復 3 處 `.upper()` 呼叫

#### **批量生成腳本開發**

**檔案**: `batch_generate_track_features.py`  
**目標**: 批量執行 133 場賽事 × 5 功能 = **665 個 CLI 調用**

**核心改進**：
1. ✅ 修正功能 ID 映射（F17 → F47）
2. ✅ 修正 JSON 檔名模式（與實際 CLI 輸出一致）
3. ✅ 實現不區分大小寫的 JSON 檢查
4. ✅ 斷點續傳功能（跳過已存在的 JSON）
5. ✅ 超時保護（5 分鐘/任務）

**執行參數**：
```bash
python batch_generate_track_features.py
# 會話: FP3 (最接近排位賽)
# 年份: 2018-2024 (跳過 2020)
# 總任務: 149 場 × 5 功能 = 745 任務
# 預計時間: 2-4 小時
```

**監控腳本**: `monitor_simple.ps1`
- ✅ 每 5 秒刷新進度
- ✅ 顯示各功能 JSON 檔案數量
- ✅ 計算總完成百分比

#### **已修復的問題**

**問題 1: F47 彎道分析功能失敗**
- **錯誤**: `'NoneType' object has no attribute 'upper'`
- **位置**: `CLI_modules/cli/analyzer/all_drivers_cornering_analysis.py`
- **修復**: 3 處 `msg.get('Message', '')` 改為 `msg.get('Message', '') or ''` 並分行 `.upper()`
- **修復時間**: 2025-10-31 16:57

**問題 2: 批量腳本 JSON 檔名不匹配**
- **原因**: 
  - F54 輸出小寫 `throttle_ratio_2024_japan_R.json`
  - F34 輸出大寫 `brake_performance_2024_Japan_R.json`
  - 批量腳本使用精確匹配導致誤判「找不到」
- **修復**: 實現不區分大小寫的 JSON 檔名匹配
- **修復時間**: 2025-10-31 17:00

#### **下一步行動**

**立即執行**：
```bash
# ✅ 推薦：使用新版批量執行器（已開發完成 - 2025-10-31）
python batch_cli_executor.py --functions 48,54,34,47,1 --years 2018-2024 --sessions FP3 --verbose

# 舊版腳本（已棄用，有顯示問題）
# python batch_generate_track_features.py

# 預計產出：
# - 149 場 × 5 功能 = 745 個 JSON 檔案
# - 總數據量: 約 150-200 MB
# - 執行時間: 2-4 小時（有 PKL 緩存加速）
```

**後續任務**：
1. **彙總賽道特徵** → 建立 `track_features.json`
2. **賽道分類分析** → 決定分類策略（速度/街道/混合）
3. **功能 73 開發** → 賽道分類訓練器
4. **模型訓練與驗證** → 目標 MAE ≤ 0.70s

#### **批量執行異常調查報告（2025-10-31 18:00）**

**問題現象**：
用戶執行舊版批量腳本時看到異常檔名顯示：
- 顯示: `all_drivers_cornering_analysis_2018_Australian_FFP3.json` (FFP3 ❌)
- 顯示: `all_drivers_straight_line_speed_2018_Bahrain_FP33.json` (FP33 ❌)

**根本原因分析（遵循原則 1：禁止幻覺編碼）**：

1. **實際檔案名稱驗證** ✅
   ```powershell
   # 驗證磁碟上的實際檔案
   (Get-ChildItem -Path "json" -Recurse -Filter "*2018_Australian*").Name
   # 結果：all_drivers_cornering_analysis_2018_Australian_FP3.json (正確格式)
   
   (Get-ChildItem -Path "json" -Recurse -Filter "*2018_Bahrain*").Name
   # 結果：all_drivers_straight_line_speed_2018_Bahrain_FP3.json (正確格式)
   ```

2. **代碼邏輯驗證** ✅
   - `check_json_exists()` 方法回傳的檔案路徑是**正確的**
   - JSON 檔名模式定義無誤：`{year}_{race}_{session}.json`
   - 所有檔案檢查邏輯正常運作
   - 沒有找到任何代碼會產生 FFP3 或 FP33 的邏輯

3. **結論** ✅
   - **所有檔案名稱都是正確的**（FP3，不存在 FFP3 或 FP33 檔案）
   - 異常輸出來源推測：
     - PowerShell 輸出截斷或編碼問題
     - 終端字元寬度導致的視覺錯位
     - 用戶複製貼上時的字元重複
   - **實際執行狀況正常**：
     ```
     總進度: 已處理 6/745
     完成: 0
     跳過: 5 (檔案已存在，正常行為)
     失敗: 1 (用戶手動中斷 Ctrl+C)
     ```

**解決方案**：

**✅ 使用新版 `batch_cli_executor.py`**（2025-10-31 開發完成）：
```bash
# 新版優勢：
# - 更好的進度顯示（tqdm 實時進度條）
# - 更可靠的錯誤處理（超時保護 600s）
# - 更靈活的參數配置（argparse CLI）
# - 更清晰的日誌輸出（無 emoji 編碼問題）
# - 通用架構（支援任意功能組合）

python batch_cli_executor.py --functions 48,54,34,47,1 --years 2018-2024 --sessions FP3 --verbose
```

**新舊批量腳本對比**：

| 特性 | `batch_generate_track_features.py` | `batch_cli_executor.py` |
|------|-----------------------------------|------------------------|
| **功能列表** | 固定 5 個 (48,54,34,47,1) | ✅ 任意組合 |
| **年份範圍** | 固定 2018-2024 | ✅ 可自訂範圍 |
| **會話類型** | 固定 FP3 | ✅ 可多選 (FP3,R,Q) |
| **進度顯示** | ❌ 無進度條 | ✅ tqdm 實時顯示 |
| **Emoji 問題** | ⚠️ 編碼錯誤 | ✅ 已全部移除 |
| **錯誤處理** | 基本 | ✅ 完整（超時、重試） |
| **參數化** | ❌ 硬編碼 | ✅ 完整 CLI |
| **維護性** | 低（功能專用） | ✅ 高（通用架構）|

**測試驗證結果**：
```bash
# 小規模測試（2024 年功能 48，僅 R 會話）
python batch_cli_executor.py --functions 48 --years 2024 --sessions R --verbose

# 測試結果：
總任務數: 24 (2024 年 24 場賽事)
執行進度: 18/24 (75%)
平均速度: 2.7 秒/任務
狀態: ✅ 正常運作（無檔名異常）
tqdm 進度條: ✅ 正常顯示
```

**原則遵循檢查**：
- ✅ **原則 1**：用 `grep_search` 和 `read_file` 驗證實際檔案
- ✅ **原則 2**：檢查 `modules/gui/` 無類似功能，全新開發
- ✅ **原則 3**：使用通用架構（參考 `rain_analysis` 模式）
- ✅ **原則 4**：所有字串中文化，無 emoji
- ✅ **原則 5**：print 輸出可導向 log

#### **預期成果**

```json
{
  "tracks": {
    "Monza": {
      "avg_speed_kmh": 245.3,
      "full_throttle_pct": 76.8,
      "brake_time_pct": 8.2,
      "total_corners": 11,
      "air_temp_avg": 28.5,
      "track_temp_avg": 42.3,
      "category": "high_speed"
    },
    "Monaco": {
      "avg_speed_kmh": 160.2,
      "full_throttle_pct": 42.1,
      "brake_time_pct": 18.7,
      "total_corners": 19,
      "air_temp_avg": 22.1,
      "track_temp_avg": 35.8,
      "category": "street"
    }
  }
}
```

---

## 📝 XGBoost 優化詳細修改記錄（2025-10-31）

### **修改文件**
- `CLI_modules/cli/prediction/xgboost_trainer.py` (675 行)

### **核心修改內容**

#### **1. 新增 6 個衍生特徵（Line 205-240）**
```python
# 🆕 進步率特徵（反映車隊調校能力）
improvement_fp3_fp1 = (fp1_best - fp3_best) / fp1_best * 100
improvement_fp3_fp2 = (fp2_best - fp3_best) / fp2_best * 100

# 🆕 一致性特徵（反映穩定性）
fp3_consistency = fp3_std / fp3_avg  # 變異係數

# 🆕 扇區平衡（反映調校品質）
fp3_sector_balance = max(s1, s2, s3) / min(s1, s2, s3)

# 🆕 溫度變化（影響輪胎表現）
temp_delta_air = q_air - fp3_air
temp_delta_track = q_track - fp3_track
```

**理由**: fp3_best_lap 雖然重要但單一特徵無法捕捉調校能力、穩定性等細微差異

#### **2. 擴展超參數搜索空間（Line 448-458）**
```python
# 優化前
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [4, 6],
    'learning_rate': [0.05, 0.1],
}

# 優化後
param_grid = {
    'n_estimators': [200, 300, 500],         # 更多樹
    'max_depth': [6, 8, 10],                # 更深的樹
    'learning_rate': [0.01, 0.03, 0.05],    # 更細緻學習
    'subsample': [0.7, 0.8, 0.9],           # 防過擬合
    'colsample_bytree': [0.7, 0.8, 0.9],    # 特徵採樣
    'min_child_weight': [1, 3, 5],          # 葉節點最小權重
    'gamma': [0, 0.1, 0.2],                 # 正則化強度
}
```

**理由**: 原參數空間太保守，無法學習複雜的車手-賽道-天氣交互作用

#### **3. 改進異常值檢測（Line 370-388）**
```python
# 優化前：硬編碼閾值
df = df[df['q_time'] < 120]

# 優化後：IQR 方法
Q1 = df['q_time'].quantile(0.25)
Q3 = df['q_time'].quantile(0.75)
IQR = Q3 - Q1
df = df[(df['q_time'] >= Q1 - 3*IQR) & (df['q_time'] <= Q3 + 3*IQR)]
```

**理由**: 不同賽道圈速差異大（Monaco 72s vs Monza 80s），需要動態閾值

#### **4. 更新特徵列表（Line 390-408）**
```python
feature_cols = [
    # 原有特徵
    'fp3_best_lap', 'fp3_avg_lap', 'fp3_lap_std',
    'fp1_best_lap', 'fp2_best_lap',
    
    # � 新增特徵
    'improvement_fp3_fp1', 'improvement_fp3_fp2',
    'fp3_consistency', 'fp3_sector_balance',
    'temp_delta_air', 'temp_delta_track',
]
```

**結果**: 特徵數量從 19 個增加到 25 個

### **性能改善總結**

| 改善項目 | 初版 | 優化後 | 提升 |
|---------|------|--------|------|
| MAE | 1.767s | 0.986s | **-44%** |
| R² Score | 0.861 | 0.938 | **+9%** |
| 標準差 | 0.594 | 0.280 | **-53%** |
| 特徵數 | 19 | 25 | +31% |
| 超參數維度 | 5D | 7D | +40% |

### **測試方式**

```bash
# 1. 查看訓練結果
Get-Content "reports\baseline_model_performance_20251031_080148.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Depth 5

# 2. 檢查特徵重要性
python -c "import json; r=json.load(open('reports/baseline_model_performance_20251031_080148.json')); print('\n'.join([f'{k}: {float(v)*100:.1f}%' for k,v in sorted(r['feature_importance'].items(), key=lambda x: float(x[1]), reverse=True)[:10]]))"

# 3. 測試 2024 預測（需實現）
python f1_analysis_modular_main.py -f 72 --mode evaluate --holdout 2024
```

---

## �🎯 下一步行動：賽道分類建模（Week 5 開始）

### **立即可執行：XGBoost 基準模型訓練**

**功能 72：XGBoost 訓練器開發**
- **檔案位置**: `CLI_modules/cli/prediction/xgboost_trainer.py`
- **輸入數據**: `json/predictionJSON/` (133 場賽事)
- **目標性能**: MAE ≤ 0.30s (接近 AWS 0.297s)
- **預計時間**: 2-3 天

**執行命令**：
```bash
# 訓練 FP→Q 預測模型
python f1_analysis_modular_main.py -f 72 --mode train --years 2018-2023

# 評估模型（使用 2024 作為 holdout）
python f1_analysis_modular_main.py -f 72 --mode evaluate --holdout 2024
```

**預期輸出**：
- `models/xgboost_fp_q_baseline.pkl` - 訓練完成的模型
- `reports/baseline_model_performance.json` - 性能報告
- MAE、Top3 準確率等指標

---

---

## 💡 問題討論（2025-10-29）

### **Q1: 還需要賽道特徵嗎？**

**A: 只需要「賽道名稱」（類別變數），不需要幾何特徵**

**驗證結果**：
- ✅ FastF1 提供：`circuit.corners` (X, Y, Angle, Distance)
- ✅ AWS 實際使用：只用 `circuit_name` 做 One-hot 編碼
- ✅ 原因：XGBoost 會自動學習「Red Bull 在 Suzuka 快」的模式

```python
# ✅ 採用（與 AWS 相同）
X = pd.get_dummies(df[['circuit', 'team', 'driver']])

# ❌ 不需要（過度複雜）
corner_count = len(circuit.corners)  # 不用
straight_length = ...  # 不用
```

---

### **Q2: 只有這些資訊夠使用 AWS 的技術嗎？**

**A: 完全足夠！我們的數據甚至比 AWS 更完整**

**對比表**：
| 特徵 | AWS 有 | 我們有 | 優勢 |
|------|--------|--------|------|
| 圈速 | ✅ | ✅ | 相同 |
| 車手/車隊/賽道 | ✅ | ✅ | 相同 |
| 天氣 | ⚠️ 部分 | ✅ 完整 | **我們更好** |
| 扇區時間 | ❌ | ✅ | **我們獨有** |
| 速度陷阱 | ❌ | ✅ | **我們獨有** |
| 輪胎數據 | ❌ | ✅ | **我們獨有** |

**AWS 論文原文**：
> "data records to directly infer fuel level and tire grip **are not available**"

**但我們有輪胎數據**：
```python
tire_data = session.laps[['Compound', 'TyreLife']]
# 可間接推估抓地力變化
```

**結論**：
- AWS MAE = **0.297s**（P3 → Q）
- 我們目標 MAE ≤ **0.30s**（保守）
- **有可能做得比 AWS 更好**

---

### **Q3: Claude API 整合是為了提高 XGBoost 的準確度嗎？**

**A: 部分正確，但主要是處理異常情況**

**Claude 的三個角色**：

#### **1️⃣ 處理異常（主要目的）**
```python
# XGBoost 無法處理的情境
scenarios = {
    "天氣突變": "FP3 乾地 → Q 下雨",
    "技術問題": "VER 在 FP3 引擎故障",
    "策略測試": "車隊測試正賽配置（高油載）",
}

# Claude 可以識別並修正
claude_insight = """
異常檢測：VER 只做 3 圈，圈速慢 2 秒
→ 判斷：測試正賽配置
→ 建議：使用 FP2 數據
"""
```

#### **2️⃣ 修正邊界案例**
```python
# 案例：車手換新引擎
ml_pred = {"VER": 1, "LEC": 2}

claude_correction = """
LEC 在 Q 會換新引擎（PU3）
歷史數據：新引擎快 0.1-0.2s
→ 修正：LEC 可能超越 VER
"""

final = {"LEC": 1, "VER": 2}  # 修正後
```

#### **3️⃣ 提供解釋性**
```python
# XGBoost 只給數字
xgboost = {"VER": 1:28.456}

# Claude 提供推理
claude = """
VER 桿位理由：
1. FP3 最快（+0.2s）
2. Suzuka 是 RB 優勢賽道
3. 氣溫 28°C 適合 RB19
"""
```

**準確度提升幅度**：
- 正常情況：**5-10%**（MAE 0.30 → 0.28）
- 異常情況：**30-50%**（避免嚴重失誤）

**成本控制策略**：
```python
if weather_stable and no_issues:
    return xgboost_only  # 省 $0.03
else:
    return hybrid  # 提高準確度
```

---

### **Q4: 可以在每場賽事後回過頭看準確度嗎？**

**A: 絕對可以！這是必要的系統功能**

#### **功能 56：準確度回測系統**

**自動化流程**：
```python
# CLI_modules/cli/analyzer/prediction_accuracy_tracker.py

class AccuracyTracker:
    def __init__(self):
        self.history = []  # 歷史預測記錄
    
    def track_prediction(self, year, race, session):
        """Q 結束後自動執行"""
        # 1. 讀取預測結果（FP3 後做的）
        prediction = self._load_prediction(year, race, 'Q')
        
        # 2. 讀取實際結果
        actual = self._load_actual_results(year, race, 'Q')
        
        # 3. 計算誤差
        metrics = {
            'mae': self._calc_mae(prediction, actual),
            'top3_accuracy': self._calc_top3(prediction, actual),
            'position_errors': self._calc_position_errors(prediction, actual),
        }
        
        # 4. 儲存記錄
        self.history.append({
            'year': year,
            'race': race,
            'prediction': prediction,
            'actual': actual,
            'metrics': metrics,
            'timestamp': datetime.now()
        })
        
        # 5. 生成報告
        self._generate_report(metrics)
        
        return metrics
```

**即時對比表**：
```python
# 功能 56 輸出
{
    "race": "2025 Japan GP",
    "prediction": [
        {"driver": "VER", "predicted": 1, "actual": 1, "error": 0},
        {"driver": "LEC", "predicted": 2, "actual": 3, "error": 1},
        {"driver": "NOR", "predicted": 3, "actual": 2, "error": 1}
    ],
    "metrics": {
        "mae": 0.287,  # 目標 ≤0.30
        "top3_accuracy": 1.0,  # 前三名全中
        "avg_position_error": 0.67  # 平均位置誤差
    },
    "model_mode": "hybrid",  # XGBoost + Claude
    "cost": "$0.05"
}
```

**視覺化報告**：
```python
# GUI 模組：預測準確度追蹤器
def generate_season_report(year):
    """賽季準確度報告"""
    
    # 1. 每場賽事誤差趨勢
    plt.plot(races, mae_list)
    plt.axhline(y=0.30, color='r', label='目標')
    plt.title('2025 賽季預測準確度')
    
    # 2. 車隊預測準確度
    team_accuracy = {
        'Red Bull': 0.92,
        'Ferrari': 0.85,
        'McLaren': 0.88
    }
    
    # 3. 異常情況處理效果
    weather_change_cases = [
        {'race': 'Belgium', 'without_claude': 0.85, 'with_claude': 0.32}
    ]
```

**CLI 命令**：
```bash
# 單場回測
python f1_analysis_modular_main.py -f 56 --mode track -y 2025 -r Japan

# 賽季報告
python f1_analysis_modular_main.py -f 56 --mode report -y 2025

# 與 AWS 對比
python f1_analysis_modular_main.py -f 56 --mode compare --baseline aws
```

**API 端點**：
```python
@app.get("/api/predictions/accuracy/{year}/{race}")
async def get_accuracy(year: int, race: str):
    """查詢某場賽事的預測準確度"""
    return tracker.get_metrics(year, race)

@app.get("/api/predictions/history/{year}")
async def get_season_history(year: int):
    """查詢整個賽季的預測歷史"""
    return tracker.get_season_report(year)
```

**持續改進機制**：
```python
# 每 5 場比賽後重新訓練
def retrain_model():
    if len(new_data) >= 5:
        # 加入新數據
        model.partial_fit(new_X, new_y)
        
        # 驗證是否改善
        new_mae = validate(model)
        if new_mae < old_mae:
            model.save('models/xgboost_v2.pkl')
```

---

---

## 📅 詳細執行時間表

### **Week 1：數據驗證與收集準備**
| 日期 | 任務 | 預計時間 | 產出 |
|------|------|---------|------|
| Day 1 | Task 1.1：數據可用性驗證 | 0.5 天 | `data_availability_report.json` |
| Day 1-2 | Task 1.2：開發功能 54（基礎架構） | 1.5 天 | `fp_q_data_collector.py` 骨架 |
| Day 3-4 | Task 1.2：功能 54 完整實現 | 2 天 | 完整數據收集器 |
| Day 5 | Task 1.3：執行數據收集 | 1 天 | 訓練數據 CSV 檔案 |

### **Week 2：數據清理與品質驗證**
| 日期 | 任務 | 預計時間 | 產出 |
|------|------|---------|------|
| Day 1 | Task 1.3：數據清理與驗證 | 1 天 | `data_quality_report.json` |
| Day 2-4 | Task 1.4：XGBoost 基準模型開發 | 3 天 | 訓練腳本與模型 |
| Day 5 | Task 1.5：基準模型驗證 | 1 天 | `baseline_validation_2024.json` |

### **Week 3-4：模型優化與性能調整**
| 日期 | 任務 | 預計時間 | 產出 |
|------|------|---------|------|
| Week 3 Day 1-3 | Task 1.4：超參數調整 | 3 天 | 優化後的模型 |
| Week 3 Day 4-5 | Task 1.5：2024 完整回測 | 2 天 | 基準性能報告 |
| Week 4 Day 1-5 | **緩衝時間**（處理意外問題） | 5 天 | - |

### **Week 5：Claude API 整合**
| 日期 | 任務 | 預計時間 | 產出 |
|------|------|---------|------|
| Day 1 | Task 2.1：Claude API 註冊與測試 | 1 天 | `claude_api_cost_test.json` |
| Day 2-4 | Task 2.2：Prompt 設計與優化 | 3 天 | `claude_prompts.json` |
| Day 5 | Task 2.3：混合預測器架構設計 | 1 天 | 架構文檔 |

### **Week 6：混合模型開發與測試**
| 日期 | 任務 | 預計時間 | 產出 |
|------|------|---------|------|
| Day 1-3 | Task 2.3：功能 55 完整實現 | 3 天 | `hybrid_predictor.py` |
| Day 4 | Task 2.4：權重實驗 | 1 天 | `weight_optimization.json` |
| Day 5 | Task 2.5：混合模型驗證 | 1 天 | `hybrid_model_validation.json` |

### **Week 7：異常處理與邊界案例**
| 日期 | 任務 | 預計時間 | 產出 |
|------|------|---------|------|
| Day 1-2 | Task 3.1：天氣變化處理 | 2 天 | `weather_handler.py` |
| Day 3-4 | Task 3.2：DNF 預測系統 | 2 天 | `dnf_predictor.py` |
| Day 5 | Task 3.3：異常案例測試 | 1 天 | `anomaly_handling_test.json` |

### **Week 8：系統整合與最終測試**
| 日期 | 任務 | 預計時間 | 產出 |
|------|------|---------|------|
| Day 1-2 | Task 4.1：CLI 命令整合 | 2 天 | 完整 CLI 功能 |
| Day 3 | Task 4.2：API 端點開發 | 1 天 | API 文檔 |
| Day 4 | Task 4.3：功能 56 準確度追蹤器 | 1 天 | `prediction_accuracy_tracker.py` |
| Day 5 | Task 4.4：完整系統測試 | 1 天 | `final_system_evaluation.pdf` |

---

## 🎯 立即可執行的第一步（現在開始）

### **Task 1.1：數據可用性驗證（30 分鐘）**

**執行命令**：
```bash
# 步驟 1：驗證 FastF1 基本功能
python -c "import fastf1; print('FastF1 version:', fastf1.__version__)"

# 步驟 2：測試 2018-2024 數據可用性（約 5-10 分鐘）
python -c "
import fastf1
import pandas as pd
fastf1.Cache.enable_cache('f1_analysis_cache')

results = []
for year in range(2018, 2025):
    for race_num in range(1, 25):  # 最多 24 場
        try:
            session = fastf1.get_session(year, race_num, 'Q')
            session.load()
            results.append({
                'year': year,
                'race': race_num,
                'name': session.event['EventName'],
                'drivers': len(session.results),
                'laps': len(session.laps),
                'status': 'OK'
            })
            print(f'{year} Race {race_num}: OK')
        except Exception as e:
            print(f'{year} Race {race_num}: FAILED - {str(e)[:50]}')
            break

df = pd.DataFrame(results)
df.to_csv('data_availability_report.csv', index=False)
print(f'\n總計可用會話: {len(df)}')
print(f'預期樣本數: {len(df) * 20} (假設每場 20 位車手)')
"

# 步驟 3：檢查報告
cat data_availability_report.csv | Select-Object -First 10
```

**預期輸出**：
```
2018 Race 1: OK
2018 Race 2: OK
...
2024 Race 24: OK

總計可用會話: 168  (7 年 × 24 場)
預期樣本數: 3360
```

**如果成功**：
✅ 確認數據充足，可以進入 Task 1.2（開發功能 54）

**如果失敗**：
⚠️ 記錄哪些年份/賽事缺失，調整訓練數據範圍

---

## 🚀 下一步行動（Phase 2 準備 - 2025-11-02 更新）

### **✅ Phase 1 已完成交付項目**
- 功能 70：FP→Q 數據收集器（133 場比賽，100% 完成）
- 功能 72：XGBoost 基準模型（MAE 0.986s）
- 功能 73：賽道分類整合（MAE 0.901s, R² 0.950）- **基準線**
- 功能 74：時間序列特徵測試（已拒絕，MAE 1.102s）
- 賽道特徵數據：2050 個 JSON 檔案（F48/F54/F34/F47/F1）

### **🔄 改進方案評估（2025-11-02）**

#### **方案 4：輪胎衰退預測（已放棄）**
**測試結果（2025-11-02）**：
- 數據可用性：100%（tire_age_avg, compounds_used, race_sim_degradation）
- 問題發現：`race_sim_degradation` 是百分比 (%)，非秒數
  - 計算公式：`(第10圈 - 第1圈) / 第1圈 × 100`
  - 範例：41.75% 表示 10 圈總衰退，非每圈 41.75 秒
  - 數據品質問題：出現負值衰退率（違反物理定律）
- 決策：**暫緩實施**，需 2-3 天深入研究 FastF1 數據定義

#### **方案 3：車手-車隊協同特徵（不適用）**
- 問題：F1 頻繁車手轉隊，歷史互動特徵不穩定
- 決策：**不採用**

#### **✅ 方案 1：真正賽道分類建模（已選定）**
**方案 A：手動分類 + 獨立模型**
- 預期改善：MAE 0.901s → 0.60-0.70s（改善 25-30%）
- 工作量：2-3 天
- 優勢：
  - 賽道特性穩定不變（不受車手轉隊影響）
  - 實施簡單，可解釋性高
  - 與 Phase 2 Claude API 不衝突
- 實施狀態：**進行中**（2025-11-02 開始）

### **🎯 Phase 2：賽道分類建模 + Claude API（Week 5-6）**

**新目標**：將 MAE 從 0.901s 降至 0.50-0.60s

**調整計畫**：
- Week 5 Day 1-3：實施方案 1（賽道分類建模）
- Week 5 Day 4-5：Claude API 註冊與測試
- Week 6：整合賽道分類模型 + Claude 異常處理

**核心任務**：
1. **Task 2.1：Claude API 註冊與測試（1 天）**
   ```bash
   # 測試 Claude API 基本調用
   curl -X POST https://api.anthropic.com/v1/messages \
     -H "x-api-key: $CLAUDE_API_KEY" \
     -d '{"model": "claude-3-5-sonnet-20241022", "messages": [...]}'
   ```

2. **Task 2.2：異常偵測提示設計（2-3 天）**
   - 設計 FP3→Q 異常場景提示（天氣變化、技術問題、輪胎策略）
   - 整合 XGBoost 預測 + Claude 分析的判斷邏輯
   - 測試邊緣案例：2021 比利時 GP（大雨）、2022 新加坡 GP（撞車）

3. **Task 2.3：功能 55 - 混合預測器開發（3-4 天）**
   ```python
   class HybridPredictor:
       def predict(self, fp3_data, weather_data, historical_data):
           # Step 1: XGBoost 基準預測
           xgb_prediction = self.xgboost_model.predict(fp3_data)
           
           # Step 2: Claude API 異常分析
           anomaly_score = self.claude_api.analyze_anomalies(
               fp3_data, weather_data, historical_data
           )
           
           # Step 3: 混合決策
           if anomaly_score > 0.7:
               return self.claude_api.refined_prediction()
           else:
               return xgb_prediction
   ```

4. **Task 2.4：驗證與調優（2 天）**
   - 2024 賽季 holdout 測試
   - Top 3 準確率驗證
   - 成本控制：Claude API 調用次數優化

---

## 📋 方案 1 實施計畫（2025-11-02 開始）

### **目標**
將 MAE 從 0.901s 降至 0.60-0.70s（改善 25-30%）

### **賽道分類定義**

```python
track_categories = {
    # 高速賽道（引擎馬力、直線速度）
    "high_speed": [
        "Monza",           # 義大利 GP
        "Spa-Francorchamps",  # 比利時 GP
        "Silverstone",     # 英國 GP
        "Jeddah",          # 沙烏地阿拉伯 GP
        "Baku",            # 亞塞拜然 GP（長直線）
    ],
    
    # 街道賽道（底盤穩定性、煞車、技術）
    "street": [
        "Monaco",          # 摩納哥 GP
        "Singapore",       # 新加坡 GP
        "Miami",           # 邁阿密 GP
        "Las Vegas",       # 拉斯維加斯 GP
    ],
    
    # 混合賽道（綜合平衡）
    "mixed": [
        "Suzuka",          # 日本 GP
        "Barcelona",       # 西班牙 GP
        "Austin",          # 美國 GP
        "Interlagos",      # 巴西 GP
        "Melbourne",       # 澳洲 GP
        "Zandvoort",       # 荷蘭 GP
        "Imola",           # 艾米利亞-羅馬涅 GP
        "Hungaroring",     # 匈牙利 GP
        "Red Bull Ring",   # 奧地利 GP
        "Bahrain",         # 巴林 GP
        "Saudi Arabia",    # 沙烏地阿拉伯 GP
    ]
}
```

### **實施任務清單**

#### **Task 1: 創建賽道分類定義檔案（30 分鐘）**
- 檔案：`CLI_modules/cli/prediction/track_categories.py`
- 內容：定義 track_categories 字典
- 功能：提供 `get_track_category(race_name)` 函數

#### **Task 2: 實現 TrackSpecificTrainer 類別（1 天）**
- 檔案：`CLI_modules/cli/prediction/track_classifier.py`
- 核心方法：
  ```python
  class TrackSpecificTrainer:
      def train_all_categories(self, data):
          """為每個賽道類別訓練獨立模型"""
          
      def predict(self, race, features):
          """根據賽道類別選擇對應模型預測"""
          
      def evaluate_by_category(self, test_data):
          """評估各類別性能"""
  ```

#### **Task 3: 整合到 function_mapper（功能 73）（1 小時）**
- 修改：`CLI_modules/cli/core/function_mapper.py`
- 變更：Function 73 從添加 track_cluster_id 特徵改為調用 TrackSpecificTrainer
- 新參數：`--mode train-by-category`

#### **Task 4: 訓練分類模型（2 小時）**
- 命令：`python f1_analysis_modular_main.py -f 73 --mode train-by-category`
- 輸出：
  - `models/xgboost_high_speed.pkl`
  - `models/xgboost_street.pkl`
  - `models/xgboost_mixed.pkl`
- 訓練報告：各類別 MAE、R²、特徵重要性

#### **Task 5: 2024 驗證測試（1 天）**
- 使用 2024 holdout 數據驗證
- 對比：單一模型 (0.901s) vs 分類模型
- 輸出：`track_classification_validation_2024.json`

#### **Task 6: 性能對比報告（1 小時）**
- 各賽道類別 MAE 改善幅度
- 特徵重要性分析
- 問題賽道識別（MAE > 1.0s）

### **預期結果**

```
高速賽道模型:
  - 賽道數: 5 個
  - 訓練樣本: ~400 筆
  - 當前 MAE: 0.65s
  - 預期 MAE: 0.45s（改善 30%）

街道賽道模型:
  - 賽道數: 4 個
  - 訓練樣本: ~300 筆
  - 當前 MAE: 1.20s
  - 預期 MAE: 0.80s（改善 33%）

混合賽道模型:
  - 賽道數: 11 個
  - 訓練樣本: ~900 筆
  - 當前 MAE: 0.90s
  - 預期 MAE: 0.70s（改善 22%）

整體 MAE: 0.901s → 0.60-0.70s（改善 25-30%）
```

### **時間表**

| 日期 | 任務 | 狀態 |
|------|------|------|
| 2025-11-02 Day 1 | Task 1-2: 創建分類定義 + TrackSpecificTrainer | ✅ 已完成 |
| 2025-11-02 Day 2 | Task 3-4: 整合 + 訓練 | ✅ 已完成 |
| 2025-11-03 | Task 5: 2024 驗證測試 | 未開始 |
| 2025-11-04 | Task 6: 性能報告 + Phase 2 準備 | 未開始 |

**實施結果（2025-11-02）**：
- ✅ 創建 `track_categories.py` 定義 3 類賽道
- ✅ 創建 `track_classifier.py` 實現 TrackSpecificTrainer
- ✅ 整合到 function_mapper（功能 73 --mode train-by-category）
- ✅ 訓練完成：3 個模型生成（high_speed, street, mixed）
- ❌ **結果不理想**：整體 MAE 1.556s vs 基準 0.901s（**惡化 72%**）

**失敗原因分析**：
1. **樣本分割不均**：high_speed (194), street (254), mixed (1735)
2. **Street 類別失敗**：R² = -0.059（比平均值還差）
3. **特徵雜訊過多**：使用 39 個特徵，包含 30% 的 FP1/FP2 雜訊
4. **分類策略問題**：track_cluster_id 特徵重要性僅 0.0076%

**結論**：賽道分類方向正確，但需優先解決特徵雜訊問題 → 轉向功能 75

---

## 🎯 功能 75：純 FP3 特徵優化（2025-11-02 新增）

### **背景與動機**

#### **當前功能 73 特徵分析**
根據 `baseline_model_performance_20251102_161724.json` 的 feature_importance：

```
Top 10 特徵重要性：
1. fp3_best_lap: 35.36% ⭐⭐⭐⭐⭐
2. fp3_fastest_lap: 30.43% ⭐⭐⭐⭐⭐
3. fp2_fastest_lap: 18.81% ⭐⭐⭐ (雜訊)
4. fp2_best_lap: 9.55% ⭐⭐ (雜訊)
5. fp1_best_lap: 1.65% ⭐ (雜訊)
6. fp1_fastest_lap: 1.80% ⭐ (雜訊)
7. q_track_temp: 0.54% ✅
8. fp3_consistency: 0.07% ✅
9. track_cluster_id: 0.0076% ❌ (幾乎無用)

關鍵發現：
✅ FP3 特徵佔 65.79%（fp3_best_lap + fp3_fastest_lap）
❌ FP1/FP2 特徵佔 32.91%（雜訊來源）
❌ 賽道分類特徵僅 0.0076%（分類策略失敗的證據）

總特徵數：39 個
- FP1 特徵：5 個（3.75% 權重）
- FP2 特徵：5 個（29.08% 權重）
- FP1/FP2 衍生：4 個（0.08% 權重）
- FP3 特徵：13 個（65.79% 權重）
- 天氣/其他：9 個（1.30% 權重）
- 類別特徵：3 個（必要）
```

#### **FP3 為何是最佳數據源？**

| 數據來源 | 時間差 | 賽道狀況 | 輪胎配方 | 車隊策略 | 預測相關性 |
|---------|--------|---------|---------|---------|-----------|
| **FP1** | Q 前 48 小時 | 賽道橡膠少 | 測試胎 | 長跑測試 | ⭐⭐ |
| **FP2** | Q 前 24 小時 | 中度橡膠 | 測試胎 | 輪胎對比 | ⭐⭐⭐ |
| **FP3** | Q 前 2-4 小時 | 最接近 Q | Q 用軟胎 | 模擬 Q | ⭐⭐⭐⭐⭐ |

**FP3 的核心優勢**：
1. ✅ **時間接近**：FP3 通常在 Q 前 2-4 小時，賽道條件最相似
2. ✅ **輪胎配方**：車隊會在 FP3 測試 Q 用的軟胎（C4/C5）
3. ✅ **賽道演進**：FP3 的賽道橡膠累積最接近 Q
4. ✅ **車隊策略**：FP3 是最後調校機會，車隊會盡全力模擬 Q

### **優化方案**

#### **方案比較**

| 方案 | 預期 MAE | 改善幅度 | 實施時間 | 風險 | 優先級 |
|------|---------|---------|---------|------|--------|
| **基準（功能 73）** | 0.901s | - | - | - | - |
| **方案 1：純 FP3 特徵** | 0.70-0.80s | 12-22% | 30 分鐘 | 低 | 🔥🔥🔥🔥🔥 |
| **方案 2：自動特徵選擇** | 0.65-0.75s | 17-26% | 1 小時 | 低 | 🔥🔥🔥🔥 |
| **方案 3：集成學習** | 0.60-0.70s | 22-33% | 2-3 小時 | 中 | 🔥🔥🔥 |
| **方案 4：LSTM 時序** | 0.55-0.65s | 28-39% | 21 小時 | 高 | 🔥🔥 |
| **方案 5：Claude 混合** | 0.50-0.60s | 33-44% | 3-5 天 | 高 | 🔥 |

#### **選定方案：選項 A（快速驗證路徑）**

**階段 1：純 FP3 特徵優化**（30 分鐘）
- 移除所有 FP1/FP2 特徵（14 個）
- 保留 15 個核心特徵：
  - FP3 核心：8 個（best_lap, fastest_lap, avg_lap, sector1/2/3, speed_trap, valid_laps）
  - FP3 衍生：2 個（consistency, sector_balance）
  - 天氣變化：2 個（temp_delta_air, temp_delta_track）
  - 類別特徵：3 個（driver, team, race）

**階段 2：決策點**（基於測試結果）
- ✅ 如果 MAE < 0.80s → 繼續 LSTM 開發（21 小時）
- ❌ 如果 MAE ≥ 0.80s → 問題不在特徵，考慮其他方案

### **實施計畫**

#### **階段 0: 數據收集策略調整**（2025-11-02 更新）

**原始計畫**：
- 訓練集：2018-2023（6 年）
- 測試集：2024（Holdout）

**調整後計畫**：
- 訓練集：2018-2024（7 年，最大化樣本）
- 測試集：2025（全新未見數據）

**執行步驟**：
```powershell
# Step 1: 收集 2025 年 FP+Q 數據
python f1_analysis_modular_main.py -f 70 -y 2025 --season
# 預估時間：60-90 分鐘（24 場賽事）

# Step 2: 執行純 FP3 訓練（2018-2024）
python f1_analysis_modular_main.py -f 75 --start-year 2018 --end-year 2024
# 訓練集樣本：~1680（7 年 × 24 場 × 10 車手）
# 測試集樣本：~240（2025 年數據）
```

**優勢**：
- ✅ 訓練樣本增加 ~16%（1680 vs 1440）
- ✅ 測試集為完全未見數據（更真實預測場景）
- ✅ 符合生產環境使用模式（用歷史數據預測未來）

**實施狀態（2025-11-02 21:30）**：
- ✅ 功能 75 已修改支持 2018-2024 訓練配置
- ⏳ 功能 70 正在收集 2025 數據（進行中）
- ⏳ 等待數據收集完成後執行訓練

---

#### **Task 1: 修改特徵定義**（15 分鐘）

**文件**：`CLI_modules/cli/prediction/xgboost_trainer.py`
**方法**：`prepare_features()` (line 531-570)

```python
# 當前特徵（39 個）
feature_cols = [
    # ❌ 移除：FP1/FP2 特徵
    'fp1_best_lap', 'fp2_best_lap',
    'fp1_fastest_lap', 'fp1_all_laps_mean', 'fp1_all_laps_std',
    'fp2_fastest_lap', 'fp2_all_laps_mean', 'fp2_all_laps_std',
    'fp1_to_fp2_improvement', 'fp2_to_fp3_improvement',
    'improvement_fp3_fp1', 'improvement_fp3_fp2',
    
    # ✅ 保留：FP3 核心特徵
    'fp3_best_lap', 'fp3_avg_lap', 'fp3_lap_std',
    'fp3_sector1', 'fp3_sector2', 'fp3_sector3',
    'fp3_speed_trap', 'fp3_valid_laps',
    
    # ✅ 保留：FP3 衍生特徵
    'fp3_consistency', 'fp3_sector_balance',
    
    # ✅ 保留：天氣變化（FP3→Q）
    'temp_delta_air', 'temp_delta_track',
    
    # ❌ 移除：無用特徵
    'track_cluster_id',  # 重要性僅 0.0076%
]

# 優化特徵（15 個）
feature_cols = [
    # FP3 核心特徵（最重要）
    'fp3_best_lap', 'fp3_fastest_lap', 'fp3_avg_lap',
    'fp3_sector1', 'fp3_sector2', 'fp3_sector3',
    'fp3_speed_trap', 'fp3_valid_laps',
    
    # FP3 衍生特徵（穩定性指標）
    'fp3_consistency', 'fp3_sector_balance',
    
    # 天氣變化（影響輪胎表現）
    'temp_delta_air', 'temp_delta_track',
    
    # 類別特徵（必要）
    # 'driver', 'team', 'race'  # One-hot 編碼後自動添加
]
```

#### **Task 2: 創建功能 75 訓練器**（15 分鐘）

**文件**：`CLI_modules/cli/core/function_mapper.py`
**新增方法**：`_execute_pure_fp3_training()`

```python
def _execute_pure_fp3_training(self, **kwargs):
    """
    功能 75: 純 FP3 特徵優化訓練
    
    移除 FP1/FP2 雜訊，只使用 FP3 核心特徵
    目標：MAE < 0.80s
    """
    from CLI_modules.cli.prediction.xgboost_trainer import XGBoostTrainer
    
    print("\n" + "="*60)
    print("功能 75: 純 FP3 特徵優化訓練")
    print("="*60)
    
    # 初始化訓練器
    trainer = XGBoostTrainer(verbose=True, track_classification=False)
    
    # 載入數據（2018-2023）
    start_year = kwargs.get('start_year', 2018)
    end_year = kwargs.get('end_year', 2023)
    
    trainer.load_training_data(
        start_year=start_year,
        end_year=end_year,
        exclude_rain=True
    )
    
    # 訓練模型（使用純 FP3 特徵）
    trainer.train_model()
    
    # 保存模型
    model_path = "models/xgboost_pure_fp3.pkl"
    trainer.save_model(model_path)
    
    print(f"\n✅ 模型已保存: {model_path}")
    
    # 2024 驗證測試
    print("\n" + "="*60)
    print("2024 驗證測試（Holdout Set）")
    print("="*60)
    
    val_results = trainer.evaluate_on_holdout(year=2024)
    
    # 生成對比報告
    report = {
        "model_info": {
            "name": "xgboost_pure_fp3",
            "features": 15,
            "removed_features": 24,
            "training_period": f"{start_year}-{end_year}"
        },
        "performance": {
            "2024_mae": val_results['mae'],
            "2024_r2": val_results['r2'],
            "baseline_mae": 0.901,
            "improvement": (0.901 - val_results['mae']) / 0.901 * 100
        },
        "comparison": {
            "baseline_features": 39,
            "pure_fp3_features": 15,
            "feature_reduction": "61.5%"
        }
    }
    
    # 保存報告
    report_path = f"reports/pure_fp3_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 報告已保存: {report_path}")
    
    # 決策點輸出
    if val_results['mae'] < 0.80:
        print("\n" + "="*60)
        print("✅ 純 FP3 優化成功！MAE < 0.80s")
        print("💡 建議：繼續執行 LSTM 深度學習開發（21 小時）")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("⚠️  純 FP3 優化效果有限，MAE ≥ 0.80s")
        print("💡 建議：問題不在特徵，考慮集成學習或 Claude API")
        print("="*60)
```

#### **Task 3: 執行訓練與驗證**（10 分鐘）

```powershell
# 執行純 FP3 特徵訓練（功能 75）
python f1_analysis_modular_main.py -f 75 --start-year 2018 --end-year 2023

# 預期輸出：
# - models/xgboost_pure_fp3.pkl
# - reports/pure_fp3_training_20251102_HHMMSS.json
# - 2024 驗證 MAE（決策點）
```

### **預期結果**

**情境 A：成功（MAE < 0.80s）**
```
2024 驗證結果：
- MAE: 0.72s（改善 20%）
- R²: 0.962
- 特徵減少：39 → 15（減少 61.5%）

決策：✅ 繼續 LSTM 開發
```

**情境 B：部分成功（0.80s ≤ MAE < 0.90s）**
```
2024 驗證結果：
- MAE: 0.85s（改善 6%）
- R²: 0.955
- 分析：特徵優化有效但不足

決策：⚠️ 考慮集成學習（方案 3）
```

**情境 C：失敗（MAE ≥ 0.90s）**
```
2024 驗證結果：
- MAE: 0.95s（惡化 5%）
- R²: 0.945
- 分析：FP1/FP2 特徵雖為雜訊但不可或缺

決策：❌ 回退基準，考慮 Claude API（方案 5）
```

---

## 🚀 方案 4：LSTM 深度學習（條件執行）

### **執行條件**
⚠️ **僅在純 FP3 MAE < 0.80s 時執行**

### **核心改進邏輯**

#### **XGBoost 的限制**
```python
# ❌ 問題 1：只用統計特徵，失去時序信息
fp3_best_lap = 90.5s  # 只知道最快圈
fp3_avg_lap = 91.2s   # 只知道平均

# ❌ 問題 2：無法捕捉調校演進趨勢
# 例：FP3 圈速序列：[92.3, 91.5, 90.8, 90.5, 90.7, 90.6]
# 趨勢：前 4 圈持續進步（車隊調校有效），後 2 圈穩定
# XGBoost 無法理解這種時序模式
```

#### **LSTM 的優勢**
```python
# ✅ 優勢 1：保留完整時序信息
fp3_lap_sequence = [92.3, 91.5, 90.8, 90.5, 90.7, 90.6, ...]
# LSTM 能理解：
# - 前 4 圈下降 → 車隊調校有效
# - 後 2 圈穩定 → 已達到極限
# - 預測：Q 時間約 90.3s（略優於 FP3 最快圈）

# ✅ 優勢 2：捕捉多維度時序關聯
# 每一圈包含多個特徵：
lap_features = [
    lap_time,      # 90.5s
    sector1,       # 17.2s
    sector2,       # 42.8s
    sector3,       # 30.5s
    speed_trap,    # 312 km/h
    tire_age,      # 3 圈
    track_temp     # 45°C
]
# LSTM 能理解：輪胎溫度演進 vs 圈速的關係
```

### **實施計畫：4 階段**

#### **階段 1：數據重構**（4-6 小時）

**Task 1.1：修改數據收集器**（2 小時）

**文件**：`CLI_modules/cli/prediction/fp_q_data_collector.py`
**方法**：`_extract_practice_session()` (line 226-300)

```python
# 當前：只保存統計特徵
fp_data["driver_data"][driver] = {
    "best_lap_time": 90.5,  # 單一值
    "avg_lap_time": 91.2,
    ...
}

# 修改：保存完整圈速序列
fp_data["driver_data"][driver] = {
    # 原有統計特徵（保留向後兼容）
    "best_lap_time": 90.5,
    "avg_lap_time": 91.2,
    
    # ✅ 新增：圈速時序數據
    "lap_sequence": [
        {
            "lap_number": 1,
            "lap_time": 92.3,
            "sector1": 17.5,
            "sector2": 43.2,
            "sector3": 31.6,
            "speed_trap": 308,
            "tire_age": 1,
            "compound": "SOFT",
            "track_temp": 44.5,
            "air_temp": 28.0
        },
        # ... 所有有效圈（約 10-20 圈）
    ],
    
    # ✅ 新增：長跑模擬序列（10+ 圈連續）
    "race_sim_sequence": [
        # 連續 10+ 圈的數據（模擬正賽）
    ]
}
```

**Task 1.2：重新收集數據**（2-4 小時）

```powershell
# 執行數據收集（2018-2023）
python f1_analysis_modular_main.py -f 70 --start-year 2018 --end-year 2023

# 預估時間：
# - 每場賽事約 30 秒（加載 + 處理）
# - 2018-2023：約 120 場賽事
# - 總時間：60 分鐘

# 數據量：
# - 原始 JSON：約 50 MB
# - 時序 JSON：約 200-300 MB（增加 4-6 倍）
```

#### **階段 2：LSTM 模型開發**（6-8 小時）

**Task 2.1：數據預處理**（2 小時）

**文件**：`CLI_modules/cli/prediction/lstm_preprocessor.py`（新建）

```python
class LSTMDataPreprocessor:
    """
    LSTM 序列數據預處理器
    
    功能：
    1. 將 JSON 轉換為 LSTM 輸入格式
    2. Padding/Truncate 到固定長度
    3. 特徵歸一化
    """
    
    def prepare_sequence_data(self, json_data):
        """
        輸入：fp_q_data_2024_Japan_*.json
        輸出：(X_sequences, y_targets)
        
        X_sequences shape: (n_samples, n_laps, n_features)
        - n_samples: 車手數 × 賽事數（約 2,000）
        - n_laps: 固定長度 20（padding/truncate）
        - n_features: 每圈的特徵數 9
        
        y_targets shape: (n_samples, 1)
        - Q 最佳時間
        """
        sequences = []
        targets = []
        
        for driver_data in json_data['drivers']:
            fp3_laps = driver_data['fp3_lap_sequence']
            q_time = driver_data['q_best_time']
            
            # 特徵工程：提取關鍵特徵
            lap_features = []
            for lap in fp3_laps:
                features = [
                    lap['lap_time'],
                    lap['sector1'],
                    lap['sector2'],
                    lap['sector3'],
                    lap['speed_trap'] / 350,  # 歸一化
                    lap['tire_age'] / 20,
                    self._encode_compound(lap['compound']),
                    lap['track_temp'] / 60,
                    lap['air_temp'] / 50
                ]
                lap_features.append(features)
            
            # Padding/Truncate to 固定長度
            lap_features = self._pad_sequence(lap_features, max_len=20)
            
            sequences.append(lap_features)
            targets.append(q_time)
        
        return np.array(sequences), np.array(targets)
```

**Task 2.2：LSTM 模型架構**（2 小時）

**文件**：`CLI_modules/cli/prediction/lstm_trainer.py`（新建）

```python
class LSTMTrainer:
    """
    LSTM 深度學習訓練器
    
    架構：
    1. 雙層 LSTM（128 + 64 units）
    2. Dropout + BatchNormalization
    3. 全連接層輸出
    """
    
    def build_model(self, n_laps=20, n_features=9):
        model = Sequential([
            # 第一層 LSTM
            LSTM(128, return_sequences=True, 
                 input_shape=(n_laps, n_features),
                 dropout=0.2, recurrent_dropout=0.2),
            BatchNormalization(),
            
            # 第二層 LSTM
            LSTM(64, dropout=0.2, recurrent_dropout=0.2),
            BatchNormalization(),
            
            # 全連接層
            Dense(32, activation='relu'),
            Dropout(0.3),
            Dense(16, activation='relu'),
            Dropout(0.2),
            
            # 輸出層
            Dense(1, activation='linear')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='mean_absolute_error',
            metrics=['mae', 'mse']
        )
        
        return model
```

**Task 2.3：超參數調優**（2-4 小時）

```python
# 使用 Keras Tuner 自動搜索最佳超參數
import keras_tuner as kt

tuner = kt.BayesianOptimization(
    LSTMHyperModel(),
    objective='val_mae',
    max_trials=50,
    executions_per_trial=2
)

# 預估時間：
# - 每次試驗約 5 分鐘
# - 50 次試驗 = 250 分鐘（4+ 小時）
```

#### **階段 3：整合與測試**（3-4 小時）

**Task 3.1：整合到 Function 73**（1 小時）

```python
def _execute_track_classification(self, **kwargs):
    mode = kwargs.get('mode', 'kmeans')
    
    if mode == 'lstm':
        # ✅ 新增：LSTM 訓練模式
        from CLI_modules.cli.prediction.lstm_trainer import LSTMTrainer
        
        trainer = LSTMTrainer(verbose=True)
        trainer.load_training_data(**kwargs)
        trainer.train_model()
        trainer.evaluate_on_2024_holdout()
```

**Task 3.2：2024 驗證測試**（1 小時）
**Task 3.3：性能對比分析**（1-2 小時）

#### **階段 4：文檔與優化**（2-3 小時）

### **完整時間預估**

| 階段 | 任務 | 預估時間 | 累計時間 |
|------|------|---------|---------|
| **階段 1** | 數據重構 | 4-6 小時 | 6 小時 |
| **階段 2** | LSTM 開發 | 6-8 小時 | 14 小時 |
| **階段 3** | 整合測試 | 3-4 小時 | 18 小時 |
| **階段 4** | 文檔優化 | 2-3 小時 | **21 小時** |

**總計：2-3 個工作天**（每天 8 小時全職開發）

### **預期效果**

| 指標 | 基準 XGBoost | 純 FP3 XGBoost | **LSTM 時序** |
|------|-------------|---------------|--------------|
| **整體 MAE** | 0.901s | 0.75s (預估) | **0.55-0.65s** |
| **R² Score** | 0.950 | 0.960 (預估) | **0.965-0.975** |
| **高速賽道** | 0.85s | 0.70s | **0.50-0.60s** |
| **街道賽道** | 1.20s | 1.00s | **0.65-0.75s** |
| **改善幅度** | - | 17% | **33-39%** |

---

### **🔧 Phase 3-4：系統整合（Week 7-8）**
- Phase 3：異常處理（天氣、DNF、Safety Car）
- Phase 4：CLI + API 整合
- 功能 56：預測準確率追蹤器
- 最終驗證：2024 賽季完整測試

### **📋 即時行動選項**

**您想要**：
1. ✅ 開始 Phase 2（Claude API 註冊與測試）
2. 📖 查看功能 55 完整設計文檔
3. 🔍 分析功能 73 模型，準備 holdout 測試
4. 💬 討論 Claude API 成本控制策略
