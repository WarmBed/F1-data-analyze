# Position Tracking Simulator 開發計畫

**建立日期**: 2026-01-05  
**最後更新**: 2026-01-06  
**狀態**: 開發中 (Phase 5-6: SC/VSC + GUI 整合完成)  
**優先級**: 高

---

## 專案概述

開發完整的位置追蹤模擬系統，讓使用者能夠模擬 20 台車的比賽過程，包含 DRS 啟動、超車判定、SC/VSC 處理等動態計算。

### 核心目標
1. 20 台車全場位置追蹤模擬
2. 超車成功率混合模型 (賽道 + 車隊 + 車手)
3. Monte Carlo 每次迭代執行完整位置追蹤
4. GUI Radio Button 模式選擇 (簡易 vs 完整)

### 開發進度摘要

| 模組 | 狀態 | 完成日期 | 說明 |
|------|------|----------|------|
| F134 超車事件收集器 | ✅ 完成 | 2026-01-05 | 1148 個超車事件 |
| F135 失敗嘗試收集器 | ✅ 完成 | 2026-01-05 | 8452 個失敗嘗試 |
| F136 賽道難度分析器 | ✅ 完成 | 2026-01-05 | 23 條賽道難度係數 |
| F137 車隊性能分析器 | ✅ 完成 | 2026-01-05 | 10 車隊對戰矩陣 |
| F138 超車模型訓練器 | ✅ 完成 | 2026-01-05 | LogReg 68% 準確率, AUC 0.7083 |
| F139 車手係數補全器 | ✅ 完成 | 2026-01-05 | 21 車手完整係數 |
| F142 Pit Lane 時間分析器 | ✅ 完成 | 2026-01-06 | 23 賽道, 1818 樣本, 平均 24.24s |
| SC/VSC 機率配置 | ✅ 完成 | 2026-01-06 | 24 賽道機率統計 |
| GUI 模式選擇 | ✅ 完成 | 2026-01-06 | Simple vs Complete Radio Button |


---

## 任務總覽

### 開發任務分類

| 類別 | 任務數量 | 優先級 |
|------|----------|--------|
| 數據收集 CLI 模組 | 4 個 | 高 |
| 模型訓練 CLI 模組 | 2 個 | 高 |
| 核心模擬器模組 | 5 個 | 高 |
| GUI 整合模組 | 3 個 | 中 |
| 輔助 CLI 模組 | 4 個 | 中 |

### 開發順序路線圖

```
Phase 1: 數據收集 (F134-F137) ← 當前階段
    ↓
Phase 2: 模型訓練 (F138-F139)
    ↓
Phase 3: 核心模擬器 (PositionTracker, SpeedModel, OvertakeCalculator)
    ↓
Phase 4: SC/VSC 處理
    ↓
Phase 5: GUI 整合
    ↓
Phase 6: 輔助模組 (F130-F133)
```

---

## 用戶需求確認

### Q1: 速度模型數據來源
**答案**: 
- **1.A** 確認已有直線速度模組:
  - `F48`: 全部車手直線速度分析 (`all_drivers_straight_line_speed_*.json`)
  - `F121`: FP2 直線速度全圈數分析 (`fp2_straight_line_all_laps_analysis_*.json`)
- **1.B** 使用 FP2 數據: **同意**
  - FP2 的 telemetry 可提供 Speed vs Distance
  - `main_straight` 提供直線起點/終點距離
  - 可從 FastF1 獲取完整 telemetry (Speed 欄位)

### Q2: DRS 區域配置
**答案**: **2.A 手動配置**
- 暫時開發但不使用 (設為 optional)
- 後續加入到 `track_map.json`
- **需要新 CLI 模組**: 從 FIA/FastF1 獲取 DRS 區域資料

### Q3: Pit Lane 時間損失
**答案**: 從歷史進站數據計算
- **需要新 CLI 模組**: 分析歷史進站數據，計算平均 pit_loss_time

### Q4: 時間步長與 GUI 插值
**答案**: **4.C 讓用戶選擇 Sim 步長，GUI 自動插值**
- Sim 預設 1.0s 步長 (可調 0.1s-10.0s)
- GUI 使用 16ms (60 FPS) 插值顯示

### Q5: SC 場景處理
**答案**: **5.A 保持當前位置，僅降速至 SC 速度 (約 120 km/h)**
- 時間間距需要從歷史數據評估
- **需要新 CLI 模組**: 分析 SC 期間的車輛間距數據

---

## 待開發的新 CLI 模組

### CLI 模組 1: DRS 區域配置獲取器 (F130)
```
目標: 從 FIA/FastF1 獲取每條賽道的 DRS 區域配置
輸出: drs_zones_{track}.json
結構:
{
  "track": "Suzuka",
  "drs_zones": [
    {
      "zone_id": 1,
      "detection_point_m": 5200,  // 檢測點距離 (米)
      "activation_point_m": 5400, // 啟動點距離
      "end_point_m": 5750         // 結束點距離
    },
    {
      "zone_id": 2,
      "detection_point_m": 200,
      "activation_point_m": 400,
      "end_point_m": 850
    }
  ],
  "total_zones": 2
}
狀態: 待開發
優先級: 中 (可暫時使用預設值)
```

### CLI 模組 2: Pit Lane 時間損失分析器 (F131)
```
目標: 從歷史進站數據計算每條賽道的平均 pit 損失時間
輸出: pit_lane_analysis_{track}.json
結構:
{
  "track": "Suzuka",
  "pit_lane_length_m": 350,       // pit lane 長度 (米)
  "pit_speed_limit_kmh": 80,      // pit 限速
  "avg_pit_loss_seconds": 22.5,   // 平均 pit 損失時間
  "min_pit_loss_seconds": 20.1,
  "max_pit_loss_seconds": 25.3,
  "sample_size": 45,              // 樣本數量
  "seasons_analyzed": [2023, 2024, 2025]
}
狀態: 待開發
優先級: 高 (影響策略模擬精確度)
```

### CLI 模組 3: SC 間距分析器 (F132)
```
目標: 分析 SC/VSC 期間的車輛間距變化
輸出: sc_gap_analysis_{track}.json
結構:
{
  "track": "Suzuka",
  "sc_speed_kmh": 120,            // SC 領跑速度
  "vsc_speed_reduction_pct": 40,  // VSC 降速百分比
  "gap_compression": {
    "normal_gap_s": 1.5,          // 正常間距
    "sc_gap_s": 0.8,              // SC 期間間距
    "compression_laps": 2         // 達到最小間距所需圈數
  },
  "restart_behavior": {
    "leader_acceleration_delay_s": 0.5,
    "following_reaction_time_s": 0.3
  }
}
狀態: 待開發
優先級: 中 (可使用預設值)
```

### CLI 模組 4: FP2 速度-位置曲線生成器 (F133)
```
目標: 從 FP2 telemetry 生成每條賽道的速度-位置曲線
輸出: speed_position_curve_{track}.json
結構:
{
  "track": "Suzuka",
  "track_length_m": 5807,
  "speed_curve": [
    {"distance_m": 0, "avg_speed_kmh": 280, "min_speed_kmh": 270, "max_speed_kmh": 295},
    {"distance_m": 50, "avg_speed_kmh": 285, ...},
    ...
  ],
  "corners": [
    {"corner_id": 1, "distance_m": 350, "apex_speed_kmh": 220, "type": "slow"},
    ...
  ],
  "straights": [
    {"start_m": 1200, "end_m": 1700, "max_speed_kmh": 315},
    ...
  ]
}
狀態: 待開發
優先級: 高 (速度模型核心數據)
```

---

## 超車成功率模型開發 (核心任務)

### 模型設計確認

| 項目 | 確認內容 |
|------|----------|
| 模型類型 | 混合模型 (賽道 + 車隊 + 車手) |
| 訓練數據 | 2024-2025 賽季 (Live Timing 數據較完整) |
| 新車手處理 | 使用車隊平均值 |
| 輪胎磨損 | 圈數差評估 (參考磨損值) |
| ML 演算法 | Logistic Regression |
| 超車條件 | 間距 <= 1 秒 (DRS 啟動條件) |
| 超車位置 | 不限制 (全賽道皆可嘗試) |
| 事故模擬 | 不包含 |
| 電池狀態 | 不包含 |

### 超車成功率公式

```
P(超車成功) = sigmoid(
    β0                              # 基礎截距
    + β1 × 賽道超車難度係數          # 來自 F136
    + β2 × 車隊性能差係數            # 來自 F137
    + β3 × 攻擊方車手係數            # 來自 F134
    + β4 × 防守方車手係數            # 來自 F134
    + β5 × 輪胎圈數差                # 實時計算
    + β6 × DRS 狀態 (0/1)            # 實時判斷
)
```

### CLI 模組 5: 超車事件歷史收集器 (F134)
```
目標: 從 PKL 快取提取 2024-2025 所有超車事件
數據來源: data/live_timing_cache/2024/*.pkl + data/live_timing_cache/2025/*.pkl
處理邏輯:
  1. 讀取每場比賽的 snapshots
  2. 偵測位置 (position) 變化 → 識別超車事件
  3. 記錄超車時的詳細資訊

輸出: overtake_events_history_2024_2025.json
結構:
{
  "metadata": {
    "seasons": [2024, 2025],
    "total_races": 48,
    "total_overtakes": 2500,
    "collection_date": "2026-01-05"
  },
  "events": [
    {
      "race": "2024_Bahrain_Race",
      "lap": 15,
      "race_time": "00:45:32.123",
      "attacker": {
        "driver": "VER",
        "team": "Red Bull Racing",
        "position_before": 3,
        "position_after": 2,
        "tyre_compound": "M",
        "tyre_age_laps": 8,
        "speed_kmh": 312
      },
      "defender": {
        "driver": "LEC",
        "team": "Ferrari",
        "position_before": 2,
        "position_after": 3,
        "tyre_compound": "H",
        "tyre_age_laps": 15,
        "speed_kmh": 305
      },
      "drs_active": true,
      "gap_before_s": 0.8,
      "gap_after_s": 0.5,
      "track_position_m": 1250,
      "overtake_success": true
    },
    ...
  ],
  "driver_stats": {
    "VER": {
      "total_attempts": 85,
      "successful": 72,
      "success_rate": 0.847,
      "defense_attempts": 45,
      "defense_success": 38,
      "defense_rate": 0.844
    },
    ...
  },
  "team_stats": {
    "Red Bull Racing": {
      "avg_attack_success": 0.823,
      "avg_defense_success": 0.812
    },
    ...
  }
}
狀態: ✅ 已完成 (2026-01-05)
優先級: 最高 (所有模型的基礎數據)
依賴: PKL 快取 (data/live_timing_cache/)
備註: 
  - 實現為 PKLOvertakeDetector 繼承自 BaseOvertakeDetector
  - 收集了 2025 賽季 23 場比賽，共 1148 個超車事件
  - 分類邏輯: on_track=420, pit_related=690, sc_related=76, lap_one=52
  - 輸出: json/overtake_events_history_2024_2025.json
```

### CLI 模組 6: 超車嘗試失敗收集器 (F135)
```
目標: 識別超車嘗試但失敗的事件 (補充 F134 的成功案例)
處理邏輯:
  1. 偵測 gap_ahead < 1.0s 且 DRS 啟動的情況
  2. 追蹤後續 10 秒內是否完成超車
  3. 若未完成 → 記錄為超車失敗事件

輸出: overtake_attempts_failed_2024_2025.json
結構:
{
  "metadata": {
    "total_failed_attempts": 1800,
    "avg_attempts_per_race": 37.5
  },
  "events": [
    {
      "race": "2024_Monaco_Race",
      "lap": 22,
      "attacker": "NOR",
      "defender": "SAI",
      "gap_closest_s": 0.4,
      "drs_active": true,
      "duration_in_drs_s": 8.5,
      "reason": "defender_position_held",
      "track_position_m": 800
    },
    ...
  ]
}
狀態: ✅ 已完成 (2026-01-05)
優先級: 最高 (訓練需要成功+失敗樣本)
依賴: F134 完成後
備註:
  - 使用冷卻機制避免重複記錄 (200 snapshots ≈ 20秒)
  - 過濾第一圈、SC/VSC 圈、車手進站圈
  - 收集了 2025 賽季 23 場比賽，共 8452 個失敗嘗試
  - 平均每場比賽 367.5 個失敗嘗試
  - 輸出: json/overtake_attempts_failed_2024_2025.json
```

### CLI 模組 7: 賽道超車難度分析器 (F136)
```
目標: 計算每條賽道的基礎超車難度係數
處理邏輯:
  1. 統計每賽道的超車次數 / 比賽圈數
  2. 計算 DRS 區域長度比例
  3. 考慮賽道寬度和彎道類型

輸出: track_overtake_difficulty.json
結構:
{
  "tracks": {
    "Bahrain": {
      "overtake_rate_per_lap": 1.25,
      "difficulty_coefficient": 0.35,  // 0=容易, 1=困難
      "drs_zone_coverage_pct": 18.5,
      "avg_overtakes_per_race": 65,
      "sample_races": 4
    },
    "Monaco": {
      "overtake_rate_per_lap": 0.12,
      "difficulty_coefficient": 0.92,
      "drs_zone_coverage_pct": 8.2,
      "avg_overtakes_per_race": 8,
      "sample_races": 4
    },
    ...
  }
}
狀態: ✅ 已完成 (2026-01-05)
優先級: 高
依賴: F134, F135
備註:
  - 分析了 23 條賽道
  - Monaco 最難超車 (0.946), Bahrain 最容易 (0.809)
  - 成功率範圍: 5.4% (Monaco) - 19.1% (Bahrain)
  - 輸出: json/track_overtake_difficulty.json
```

### CLI 模組 8: 車隊性能差係數計算器 (F137)
```
目標: 計算車隊間的相對性能差異係數
數據來源: 排位賽成績、比賽圈速
處理邏輯:
  1. 統計車隊間的平均圈速差
  2. 計算車隊對戰超車成功率
  3. 生成車隊 × 車隊的性能矩陣

輸出: team_performance_matrix.json
結構:
{
  "metadata": {
    "seasons": [2024, 2025],
    "teams": ["Red Bull Racing", "Ferrari", "McLaren", ...]
  },
  "lap_time_delta_matrix": {
    // 每秒差值 (正數 = 行車隊比列車隊快)
    "Red Bull Racing": {
      "Ferrari": -0.15,
      "McLaren": -0.22,
      "Mercedes": -0.35,
      ...
    },
    ...
  },
  "overtake_success_matrix": {
    // 攻擊成功率 (行車隊攻擊列車隊)
    "Red Bull Racing": {
      "Ferrari": 0.72,
      "McLaren": 0.68,
      "Mercedes": 0.81,
      ...
    },
    ...
  },
  "team_tier": {
    "Red Bull Racing": 1,
    "Ferrari": 1,
    "McLaren": 1,
    "Mercedes": 2,
    "Aston Martin": 2,
    ...
  }
}
狀態: ✅ 已完成 (2026-01-05)
優先級: 高
依賴: F134, F135
備註:
  - 分析了 10 個車隊的對戰數據
  - 生成了車隊對車隊的超車成功率矩陣
  - McLaren 攻擊成功率最高 (16.8%), Red Bull 防守成功率最高 (91.5%)
  - 輸出: json/team_performance_matrix.json
```

### CLI 模組 9: 超車成功率模型訓練器 (F138)
```
目標: 訓練 Logistic Regression 超車成功率模型
數據來源: F134 + F135 的合併數據
特徵工程:
  - 賽道超車難度係數 (from F136)
  - 車隊性能差 (from F137)
  - 攻擊方車手歷史成功率
  - 防守方車手歷史防守率
  - 輪胎圈數差 (攻擊方 - 防守方)
  - DRS 狀態 (0/1)

訓練流程:
  1. 合併成功/失敗樣本
  2. 特徵標準化
  3. 訓練 Logistic Regression
  4. 交叉驗證 (5-fold)
  5. 輸出模型和評估指標

輸出:
  - overtake_success_model.pkl          # 訓練好的模型
  - overtake_model_coefficients.json    # 模型係數 (可解釋)
  - overtake_model_evaluation.json      # 評估指標

結構 (overtake_model_coefficients.json):
{
  "model_type": "LogisticRegression",
  "training_date": "2026-01-05",
  "sample_size": {
    "total": 4300,
    "success": 2500,
    "failed": 1800
  },
  "coefficients": {
    "intercept": -0.523,
    "track_difficulty": -1.245,
    "team_performance_delta": 0.832,
    "attacker_success_rate": 1.156,
    "defender_defense_rate": -0.945,
    "tyre_age_delta": 0.078,
    "drs_active": 0.654
  },
  "feature_importance": {
    "track_difficulty": 0.28,
    "team_performance_delta": 0.22,
    "attacker_success_rate": 0.18,
    ...
  },
  "evaluation": {
    "accuracy": 0.745,
    "precision": 0.712,
    "recall": 0.789,
    "f1_score": 0.749,
    "auc_roc": 0.812
  }
}
狀態: 待開發
優先級: 最高 (核心模型)
依賴: F134, F135, F136, F137
```

### CLI 模組 10: 新車手係數補全器 (F139)
```
目標: 為缺乏歷史數據的新車手/替補車手生成預設係數
處理邏輯:
  1. 識別數據不足的車手 (少於 10 次超車嘗試)
  2. 使用該車手所屬車隊的平均值
  3. 如果是完全新車手,使用全場平均值

輸出: driver_coefficients_complete.json
結構:
{
  "drivers": {
    "VER": {
      "data_source": "historical",
      "sample_size": 85,
      "attack_coefficient": 1.23,
      "defense_coefficient": 1.18
    },
    "BEA": {
      "data_source": "team_average",  // 新車手,用 Haas 平均
      "sample_size": 3,
      "attack_coefficient": 0.95,
      "defense_coefficient": 0.88,
      "fallback_team": "Haas F1 Team"
    },
    ...
  }
}
狀態: 待開發
優先級: 中
依賴: F138
```

---

## 現有可用數據

### 直線速度分析 (F48)
- **位置**: `json/all_drivers_straight_line_speed_*.json`
- **數據**:
  - `max_speed_kmh`: 最高速度
  - `acceleration_time_100_300_seconds`: 100-300 km/h 加速時間
  - `segment_avg_acceleration_ms2`: 平均加速度

### FP2 直線速度全圈數分析 (F121)
- **位置**: `json/fp2_straight_line_all_laps_analysis_*.json`
- **數據**:
  - `main_straight.start_distance`: 直線起點距離
  - `main_straight.end_distance`: 直線終點距離
  - `speed_stats.median/mean/max`: 速度統計
  - `acceleration_100_300_stats`: 加速度統計

### 彎角速度分析 (F47)
- **位置**: `json/all_drivers_cornering_analysis_*.json`
- **數據**:
  - `selected_corners.low_speed/mid_speed/high_speed`: 三類彎角
  - `avg_apex_speed`: 平均 Apex 速度

### Live Timing 數據
- **位置**: `json/LiveF1/2025/{Race_Name}/`
- **注意**: Position.json 和 CarData.json 的 X,Y,Z 和速度數據大多為 0 (需 F1TV 訂閱)
- **可用數據**:
  - `TimingData.json`: 圈速、sector 時間
  - `PitLaneTimeCollection.json`: 進站時間
  - `TyreStintSeries.json`: 輪胎 stint 資訊

---

## 架構設計

### 模組結構
```
strategy_simulator/
├── core/
│   ├── lap_simulator.py          # 現有圈時模擬器 (已有 DRS/Lapping)
│   ├── position_tracker.py       # 新建: 位置追蹤模擬器
│   ├── speed_model.py            # 新建: 速度模型
│   ├── overtake_calculator.py    # 新建: 超車判定計算
│   └── monte_carlo.py            # 現有 Monte Carlo
├── data/
│   ├── track_config.py           # 新建: 賽道配置管理
│   ├── drs_zones.py              # 新建: DRS 區域配置
│   └── pit_config.py             # 新建: Pit 配置
└── gui/
    ├── input_panel.py            # 現有 (需新增模式選擇)
    ├── position_visualizer.py    # 新建: 位置視覺化
    └── strategy_comparison.py    # 現有策略比較
```

### 模擬模式選擇 (Radio Button)
```
[ ] 簡易模式 (Lap Time Accumulation)
    - 快速計算
    - 僅圈時累加
    - 適合快速策略比較

[x] 完整模式 (Position Tracking)
    - 精確模擬
    - 20 台車位置追蹤
    - DRS/超車/SC 動態計算
    - 時間步長: [1.0 ▼] 秒 (0.1-10.0)
```

### 位置追蹤核心邏輯
```python
class PositionTracker:
    def __init__(self, track_config: TrackConfig, time_step: float = 1.0):
        self.track_length = track_config.length_m
        self.speed_curve = track_config.speed_curve
        self.drs_zones = track_config.drs_zones
        self.time_step = time_step
        
    def simulate_step(self, car_states: List[CarState]) -> List[CarState]:
        """模擬一個時間步長"""
        for car in car_states:
            # 1. 計算當前位置的基礎速度
            base_speed = self._get_speed_at_position(car.position_m)
            
            # 2. 應用 DRS 加成 (如果在 DRS 區且前車在 1 秒內)
            if self._is_in_drs_zone(car.position_m) and car.gap_ahead_s < 1.0:
                base_speed += 10  # DRS 加成 10-15 km/h
            
            # 3. 計算新位置
            distance_covered = base_speed * (1000/3600) * self.time_step
            car.position_m = (car.position_m + distance_covered) % self.track_length
            
            # 4. 更新圈數
            if car.position_m < distance_covered:
                car.lap_number += 1
                
        # 5. 檢測超車
        self._detect_overtakes(car_states)
        
        return car_states
```

---

## GUI 整合計畫

### 1. 模式選擇 UI
- 在 `input_panel.py` 新增 Radio Button
- 簡易模式 vs 完整模式
- 完整模式顯示額外參數 (時間步長)

### 2. 視覺化面板
- 賽道地圖 (參考 `track_map.py`)
- 20 台車即時位置
- DRS 區域標示
- 超車事件高亮

### 3. 計算時間估算
- 顯示預估計算時間
- 進度條更新

---

## 開發順序

### Phase 1: 數據收集 (最高優先)
1. [ ] **F134**: 超車事件歷史收集器 - 從 PKL 提取成功超車
2. [ ] **F135**: 超車嘗試失敗收集器 - 補充失敗案例
3. [ ] **F136**: 賽道超車難度分析器 - 計算賽道係數
4. [ ] **F137**: 車隊性能差係數計算器 - 計算車隊矩陣

### Phase 2: 模型訓練 (高優先)
5. [x] **F138**: 超車成功率模型訓練器 - Logistic Regression (已完成, AUC 0.7083)
6. [x] **F139**: 新車手係數補全器 - 使用車隊平均值 (已完成, 21 車手)

### Phase 3: 核心模擬器 (高優先) ✅ 已完成 2026-01-05
7. [x] 建立 `TrackConfig` 資料結構 - 載入 F136 賽道難度
8. [x] 建立 `SpeedModel` 從 F47/F48 數據生成速度曲線 (整合到 TrackConfig)
9. [x] 建立 `PositionTracker` 核心邏輯 - 含車隊速度係數、輪胎衰退、隨機性
10. [x] 建立 `OvertakeCalculator` 整合 F138 模型 - 含 fallback 機率公式
11. [x] 修改 `MonteCarlo` 支援完整位置追蹤模式 - `run_full_position_simulation()`

### Phase 4: DRS 與超車整合 ✅ 已完成 2026-01-05
12. [x] 實現 DRS 區域判定邏輯 - TrackConfig.is_in_drs_zone()
13. [x] 整合超車成功率模型 - OvertakeCalculator.attempt_overtake()
14. [ ] 實現 lapping (被套圈) 處理

### Phase 5: SC/VSC 處理 ✅ 已完成 2026-01-06
15. [x] 實現 SC 觸發邏輯 - TrackConfig.sc_probability_per_lap_pct
16. [x] 實現 SC 期間速度降低和間距壓縮 - position_tracker._apply_sc_gap_compression()
17. [x] 實現賽道特定 SC/VSC 機率 - sc_probability_by_track.json (24 賽道)
18. [x] 新增 F142 Pit Lane 時間分析器 - pit_lane_time_loss_all_tracks.json (23 賽道)

### Phase 6: GUI 整合 ✅ 已完成 2026-01-06
19. [x] 新增模式選擇 Radio Button - FullRaceTab (Simple vs Complete)
20. [x] 整合賽道特定參數 - main_window.py 使用 TrackConfig
21. [ ] 整合位置視覺化
22. [ ] 整合策略比較結果

### Phase 7: 輔助 CLI 模組 (中優先)
23. [ ] **F130**: DRS 區域配置獲取器
24. [x] **F142**: Pit Lane 時間損失分析器 ✅ 2026-01-06 (替代 F131)
25. [ ] **F132**: SC 間距分析器
26. [ ] **F133**: FP2 速度-位置曲線生成器

---

## CLI 模組 ID 分配總表

| 模組 ID | 名稱 | 功能 | 狀態 |
|---------|------|------|------|
| F130 | DRS Zone Configurator | DRS 區域配置獲取 + 更新 track_map.json | 待開發 |
| F131 | (已廢棄) | 由 F142 取代 | - |
| F132 | SC Gap Analyzer | SC 間距分析 + 觸發機率統計 | 待開發 |
| F133 | Speed Position Curve Generator | 速度-位置曲線 | 待開發 |
| F134 | Overtake History Collector | 超車事件收集 | ✅ 完成 |
| F135 | Overtake Attempt Failed Collector | 失敗超車收集 | ✅ 完成 |
| F136 | Track Overtake Difficulty Analyzer | 賽道難度分析 | ✅ 完成 |
| F142 | Pit Lane Time Analyzer | Pit Lane 時間損失統計 (2022-2025) | ✅ 完成 |
| F137 | Team Performance Matrix Calculator | 車隊性能矩陣 | 待開發 |
| F138 | Overtake Success Model Trainer | 超車模型訓練 | 待開發 |
| F139 | New Driver Coefficient Completer | 新車手係數補全 | 待開發 |
| F140 | Qualifying Result Collector | 排位賽結果收集 (起跑位置) | 待開發 |
| F141 | SC Trigger Probability Model | SC 觸發機率模型 (歷史統計 + 彎道分布) | 待開發 |

---

## 補充需求確認 (2026-01-05)

### A. DRS 位置收集
- 從 PKL 收集車手實際 DRS 啟動的位置分布
- 更新到 track_map.json 中
- 改進現有 track map CLI (需確認功能號)

### B. 起跑位置
- 開發 F140: 排位賽結果收集器
- 也可檢查現有 FP2->Q 模組是否已有排位資訊

### C. 輪胎策略
- 從歷史數據學習車隊/車手的策略偏好
- 注意: 模擬器已有最佳策略模擬功能，此處用於其他 19 台車的預設策略

### D. SC/VSC 觸發
- 結合歷史統計 + 固定機率
- 模擬在哪個彎道發生
- 開發 F141: SC 觸發機率模型

---

## 測試計畫

### 單元測試
- `test_position_tracker.py`: 位置計算測試
- `test_speed_model.py`: 速度模型測試
- `test_overtake_logic.py`: 超車邏輯測試
- `test_overtake_model.py`: 超車成功率模型測試

### 數據驗證測試
- 驗證 F134 收集的超車事件數量合理 (預估 2000-3000 個)
- 驗證 F136 賽道難度係數分布 (Monaco 最高, Bahrain 最低)
- 驗證 F138 模型 AUC > 0.75

### 整合測試
- 使用 2025 Japan 數據進行完整模擬
- 對比真實比賽結果驗證準確性

---

## 數據依賴關係圖

```
PKL Cache (2024-2025)
    │
    ├──► F134 (超車成功事件)
    │        │
    │        ├──► F136 (賽道難度) ──────┐
    │        │                          │
    │        └──► F137 (車隊矩陣) ──────┤
    │                                   │
    └──► F135 (超車失敗事件) ───────────┤
                                        │
                                        ▼
                                 F138 (模型訓練)
                                        │
                                        ▼
                                 F139 (新車手補全)
                                        │
                                        ▼
                              OvertakeCalculator
                                        │
                                        ▼
                              PositionTracker (模擬器核心)
```

---

## 風險與備案

| 風險 | 影響 | 備案 |
|------|------|------|
| PKL 數據不完整 | 無法收集足夠超車事件 | 補充 FastF1 位置數據 |
| 超車樣本不平衡 | 模型偏向預測成功 | 使用 SMOTE 過採樣 |
| 新車手太多 | 車隊平均值不準 | 使用全場平均值 |
| 計算量過大 | 20車x53圈x1s 太慢 | 提供 10s 步長選項 |
| DRS 區域數據不全 | 無法精確判定 DRS 啟動 | 使用通用假設 |

---

## 預估工作量

| 階段 | 任務數 | 預估時間 |
|------|--------|----------|
| Phase 1: 數據收集 | 4 個 CLI | 8-12 小時 |
| Phase 2: 模型訓練 | 2 個 CLI | 4-6 小時 |
| Phase 3: 核心模擬器 | 5 個模組 | 12-16 小時 |
| Phase 4: DRS/超車 | 3 個功能 | 6-8 小時 |
| Phase 5: SC/VSC | 3 個功能 | 4-6 小時 |
| Phase 6: GUI 整合 | 3 個面板 | 8-10 小時 |
| Phase 7: 輔助模組 | 4 個 CLI | 6-8 小時 |
| **總計** | **24 個任務** | **48-66 小時** |

---

## 備註

- 系統專注於 2024-2025 賽季 (Live Timing 數據較完整)
- PKL 快取位於 `data/live_timing_cache/`
- 參考 `rain_analysis` 的架構模式實現 GUI 模組
- 所有字串使用 `tr()` 函數包裹
- 不使用 emoji
