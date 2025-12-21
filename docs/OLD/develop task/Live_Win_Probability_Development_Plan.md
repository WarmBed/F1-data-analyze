# Live Win Probability Predictor - 開發計畫

**專案名稱**: 每圈即時勝率預測系統 (Live Win Probability Predictor)  
**創建日期**: 2025-11-27  
**狀態**: 規劃中  
**優先級**: 高

---

## 1. 專案概述

### 1.1 目標
在比賽進行中，根據每圈的即時狀態（位置、間隔、輪胎、賽道狀態等），預測每位車手的 P1/P2/P3 機率分布。

### 1.2 核心價值
- 提供即時的比賽勝率分析
- 幫助觀眾理解比賽動態
- 賽後回測模型準確度

### 1.3 技術架構
```
┌─────────────────────────────────────────────────────────────┐
│                  Live Win Probability System                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Live F1     │───▶│  Feature     │───▶│  XGBoost     │  │
│  │  Data Feed   │    │  Engineering │    │  Model       │  │
│  │  (JSON)      │    │  Pipeline    │    │  Predictor   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                │            │
│                                                ▼            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Live Demo GUI (每圈更新)                │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Pos │ Driver │ Gap  │ Tyre │ Win% │ P3%   │    │   │
│  │  │   1  │  VER   │  -   │  H   │ 72%  │ 95%   │    │   │
│  │  │   2  │  NOR   │ 2.1s │  M   │ 18%  │ 78%   │    │   │
│  │  │   3  │  LEC   │ 4.5s │  S   │  6%  │ 52%   │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 需求規格

### 2.1 功能需求

| 項目 | 規格 |
|------|------|
| **輸入** | 每圈的即時狀態（位置、間隔、輪胎、賽道狀態等） |
| **輸出** | 每位車手的 P1/P2/P3 機率分布 |
| **模型** | XGBoost 回歸（預測最終名次 → 轉換為機率） |
| **訓練集** | 2023-2024 賽季（約 40,000 筆） |
| **驗證集** | 2025 賽季 22 場比賽 |
| **更新頻率** | 每圈一次 |
| **GUI** | 整合到 Live Demo 排名表 |

### 2.2 非功能需求

| 項目 | 規格 |
|------|------|
| **效能** | 後台計算，不要求即時（< 5 秒/圈可接受） |
| **準確度** | 「看起來合理」的估算 |
| **可擴展性** | 預留 LLM 解釋功能接口 |

---

## 3. 數據規格

### 3.1 數據來源

| 年份 | 比賽數量 | 用途 | 狀態 |
|------|----------|------|------|
| **2023** | 22 場 | 訓練集 | 已下載 |
| **2024** | 15 場 | 訓練集 | 已下載 |
| **2025** | 22 場 | 驗證集 | 已下載 |

### 3.2 數據檔案結構

```
json/LiveF1/{year}/{race_name}/
├── Position.json           # 每圈位置
├── TimingData.json         # 圈時、間隔
├── TyreStintSeries.json    # 輪胎策略
├── LapCount.json           # 圈數
├── TrackStatus.json        # 賽道狀態
├── WeatherData.json        # 天氣
├── PitLaneTimeCollection.json  # 進站
└── LapSeries.json          # 最終結果 (Label)
```

### 3.3 特徵清單 (Features)

#### 每圈即時數據
| # | 特徵名 | 說明 | 數據來源 |
|---|--------|------|----------|
| 1 | `position` | 當前排名 | Position.json |
| 2 | `gap_to_leader` | 與領先者間隔（秒） | TimingData.json |
| 3 | `gap_to_ahead` | 與前車間隔（秒） | TimingData.json |
| 4 | `lap_time` | 當前圈時 | TimingData.json |
| 5 | `best_lap_time` | 最佳圈時 | TimingData.json |
| 6 | `tyre_compound` | 輪胎類型 (S=0/M=1/H=2) | TyreStintSeries.json |
| 7 | `tyre_age` | 輪胎圈數 | TyreStintSeries.json |
| 8 | `pit_count` | 進站次數 | PitLaneTimeCollection.json |
| 9 | `laps_remaining` | 剩餘圈數 | LapCount.json |
| 10 | `track_status` | 賽道狀態 (GREEN=0/SC=1/VSC=2/RED=3) | TrackStatus.json |
| 11 | `air_temp` | 氣溫 | WeatherData.json |
| 12 | `rainfall` | 是否下雨 (0/1) | WeatherData.json |

#### 歷史/靜態數據
| # | 特徵名 | 說明 | 數據來源 |
|---|--------|------|----------|
| 13 | `driver_win_rate` | 車手歷史勝率 | 預計算統計 |
| 14 | `driver_podium_rate` | 車手頒獎台率 | 預計算統計 |
| 15 | `team_rating` | 車隊評級 | Dynamic Rating System |
| 16 | `circuit_overtake_rate` | 賽道超車率 | 歷史統計 |
| 17 | `circuit_sc_rate` | 賽道 SC 機率 | 歷史統計 |
| 18 | `qualifying_position` | 排位賽成績 | FastF1 / JSON |

### 3.4 標籤 (Label)

```python
# 標籤定義
label = final_position  # 1-20，DNF=21

# 機率轉換
# XGBoost 預測名次 → 轉換為 P1/P2/P3 機率
```

### 3.5 訓練數據估算

```
2023: 22 場 × 55 圈 × 20 車手 = 24,200 筆
2024: 15 場 × 55 圈 × 20 車手 = 16,500 筆
────────────────────────────────────────
總計: 約 40,700 筆訓練數據
```

---

## 4. 開發階段

### Phase 1: 數據準備
**預計時間**: 2-3 天

| 任務 | 說明 | 狀態 |
|------|------|------|
| 1.1 | 檢查 LiveF1 數據完整性 | 待開始 |
| 1.2 | 設計數據提取腳本結構 | 待開始 |
| 1.3 | 實現 JSON 解析器 | 待開始 |
| 1.4 | 提取 2023-2024 訓練特徵 | 待開始 |
| 1.5 | 提取 2025 驗證特徵 | 待開始 |
| 1.6 | 數據清洗與預處理 | 待開始 |

**交付物**:
- `CLI_modules/cli/prediction/live_win_probability/data_extractor.py`
- `json/training_data/win_probability_train_2023_2024.csv`
- `json/training_data/win_probability_test_2025.csv`

### Phase 2: 模型訓練
**預計時間**: 2-3 天

| 任務 | 說明 | 狀態 |
|------|------|------|
| 2.1 | 特徵工程（類別編碼、標準化） | 待開始 |
| 2.2 | XGBoost 模型訓練 | 待開始 |
| 2.3 | 超參數調優 | 待開始 |
| 2.4 | 2025 驗證集測試 | 待開始 |
| 2.5 | 特徵重要性分析 | 待開始 |
| 2.6 | 機率轉換函數設計 | 待開始 |

**交付物**:
- `models/live_win_probability_xgb.pkl`
- `docs/reports/win_probability_feature_importance.md`
- `docs/reports/win_probability_validation_2025.md`

### Phase 3: GUI 整合
**預計時間**: 2-3 天

| 任務 | 說明 | 狀態 |
|------|------|------|
| 3.1 | 設計預測器 API 接口 | 待開始 |
| 3.2 | 整合到 LiveRankingTableWidget | 待開始 |
| 3.3 | 新增 Win%/P3% 欄位 | 待開始 |
| 3.4 | 機率變化視覺化（可選） | 待開始 |
| 3.5 | 測試與調試 | 待開始 |

**交付物**:
- `CLI_modules/cli/prediction/live_win_probability/predictor.py`
- 修改 `Live_timing_test/demo_live_position_tracking.py`

### Phase 4: 進階功能（未來）
**預計時間**: 待定

| 任務 | 說明 | 狀態 |
|------|------|------|
| 4.1 | 進站時機分析整合 | 規劃中 |
| 4.2 | LLM 解釋功能 | 規劃中 |
| 4.3 | 策略建議 | 規劃中 |
| 4.4 | 勝率變化折線圖 | 規劃中 |

---

## 5. 技術細節

### 5.1 機率轉換方法

```python
import numpy as np
from scipy.special import softmax

def predict_probabilities(model, features, num_drivers=20):
    """
    預測每位車手的 P1/P2/P3 機率
    
    Args:
        model: 訓練好的 XGBoost 模型
        features: 特徵矩陣 (num_drivers, num_features)
        num_drivers: 車手數量
    
    Returns:
        dict: {driver: {'p1': float, 'p2': float, 'p3': float}}
    """
    # 預測最終名次
    predicted_positions = model.predict(features)
    
    # 轉換為機率（使用負數，因為名次越小越好）
    scores = -predicted_positions
    
    # Softmax 轉換
    probs = softmax(scores)
    
    # 計算 P1/P2/P3 機率
    # P1: 直接使用 softmax 機率
    # P3: 累積前三名的機率
    
    results = {}
    sorted_indices = np.argsort(predicted_positions)
    
    for i, driver_idx in enumerate(sorted_indices):
        driver = drivers[driver_idx]
        results[driver] = {
            'predicted_position': predicted_positions[driver_idx],
            'p1': probs[driver_idx],
            'p3': sum(probs[sorted_indices[:3]]) if i < 3 else calculate_p3_prob(...)
        }
    
    return results
```

### 5.2 特徵編碼

```python
# 類別特徵編碼
TYRE_COMPOUND_MAP = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2, 'INTERMEDIATE': 3, 'WET': 4}
TRACK_STATUS_MAP = {'GREEN': 0, 'YELLOW': 1, 'SC': 2, 'VSC': 3, 'RED': 4}

# 數值特徵標準化
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
```

### 5.3 模型參數（初始）

```python
import xgboost as xgb

params = {
    'objective': 'reg:squarederror',  # 回歸任務
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42
}
```

---

## 6. 驗證指標

### 6.1 模型準確度

| 指標 | 說明 | 目標 |
|------|------|------|
| **MAE** | 平均絕對誤差（名次） | < 3.0 |
| **Top-1 準確率** | P1 預測正確率 | > 50% |
| **Top-3 準確率** | 前三名預測正確率 | > 70% |

### 6.2 機率校準

- 預測 70% 勝率的車手，實際勝率應接近 70%
- 使用 Calibration Curve 評估

---

## 7. 風險與挑戰

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 數據不完整 | 訓練樣本不足 | 檢查並補充缺失數據 |
| 特徵不足 | 模型準確度低 | 增加歷史統計特徵 |
| 過擬合 | 驗證集表現差 | 交叉驗證、正則化 |
| SC/VSC 不可預測 | 機率波動大 | 接受限制，不模擬隨機事件 |

---

## 8. 未來擴展

### 8.1 LLM 整合（Phase 4）

```python
# 示例：使用 LLM 生成勝率變化解釋
def explain_probability_change(driver, old_prob, new_prob, context):
    """
    使用 LLM 解釋勝率變化原因
    
    輸入:
    - driver: "VER"
    - old_prob: 0.72
    - new_prob: 0.58
    - context: {"event": "pit_stop", "position_change": 1->3}
    
    輸出:
    "VER 勝率從 72% 下降至 58%，因為剛完成進站，
     目前位於 P3，與領先者差距擴大至 8.5 秒。"
    """
    pass
```

### 8.2 進站時機分析

- 整合輪胎劣化模型
- 預測最佳進站窗口
- 計算進站後的預期排名

---

## 9. 附錄

### 9.1 相關文件

- `docs/2025_WIN_PROBABILITY_REPORT.md` - 現有 Q→R 勝率預測報告
- `docs/2025_Q_TO_R_PREDICTION_REPORT.md` - Q→R 預測詳細報告
- `Live_timing_test/demo_live_position_tracking.py` - Live Demo GUI

### 9.2 參考資源

- XGBoost 文檔: https://xgboost.readthedocs.io/
- FastF1 API: https://docs.fastf1.dev/
- OpenF1 API: https://openf1.org/

---

## 10. 更新日誌

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2025-11-27 | v1.0 | 初始版本，完成需求討論與規格定義 |

