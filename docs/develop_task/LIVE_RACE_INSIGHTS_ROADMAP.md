# Live Race Insights 開發路線圖

**建立日期**: 2025-12-01  
**狀態**: 規劃中  
**優先級**: 高

---

## 專案目標

基於現有的 Live Win Probability 系統，擴展開發類似 AWS F1 Insights 的進階即時分析功能。

---

## 功能規劃

### 1. Battle Forecast (車手對戰預測)

**目標**: 預測兩位車手之間的超車機率和對戰結果

**功能需求**:
- [ ] 計算兩車之間的距離和相對速度
- [ ] 評估 DRS 可用性對超車的影響
- [ ] 考慮賽道特性（超車難度係數）
- [ ] 分析輪胎差異對對戰的影響
- [ ] 預測超車成功機率 (%)

**數據來源**:
- Live Timing: 位置、間距、速度
- FastF1: 賽道超車難度數據
- 歷史數據: 車手間對戰記錄

**技術方案**:
```
輸入特徵:
- gap_to_car_ahead (秒)
- relative_pace (秒/圈)
- drs_available (bool)
- tyre_compound_diff
- track_overtaking_difficulty
- driver_overtake_rating

輸出:
- overtake_probability (%)
- estimated_laps_to_pass
- battle_intensity_score
```

---

### 2. Pit Strategy (進站策略分析)

**目標**: 預測最佳進站時機和策略

**功能需求**:
- [ ] 計算當前輪胎剩餘壽命
- [ ] 預測進站後的位置變化
- [ ] 分析 Undercut/Overcut 可行性
- [ ] 建議最佳進站圈數
- [ ] 多策略比較（一停 vs 兩停）
- [ ] Monte Carlo 模擬不同策略結果分布

**數據來源**:
- Live Timing: 輪胎圈數、單圈時間變化
- FastF1: 輪胎衰退曲線
- 歷史數據: 各賽道最佳策略

**技術方案**:
```
輸入特徵:
- current_tyre_age (laps)
- tyre_compound
- track_tyre_degradation
- remaining_race_laps
- current_position
- pit_delta (秒)

輸出:
- optimal_pit_window (lap range)
- position_after_pit
- recommended_strategy
- strategy_comparison_chart
```

#### Monte Carlo 模擬框架

**核心思路**：模擬不同進站策略的結果分布，找出期望值最高的策略

```python
# Monte Carlo 進站策略模擬
def simulate_pit_strategy(current_state, num_simulations=10000):
    """
    模擬不同進站策略的結果分布
    
    current_state:
        - current_lap: 當前圈數
        - total_laps: 總圈數
        - tyre_age: 輪胎已使用圈數
        - position: 當前位置
        - gap_ahead/behind: 與前後車的間距
    """
    strategies = ['1-stop', '2-stop', 'stay-out']
    results = {s: [] for s in strategies}
    
    for strategy in strategies:
        for _ in range(num_simulations):
            # 模擬輪胎衰退
            tyre_degradation = sample_degradation_curve()
            
            # 模擬進站時機
            pit_windows = generate_pit_windows(strategy)
            
            # 模擬對手行為
            opponent_actions = simulate_opponents()
            
            # 模擬 Safety Car / VSC
            safety_car_events = sample_safety_car_probability()
            
            # 計算最終位置
            final_position = calculate_final_position(...)
            results[strategy].append(final_position)
    
    # 計算期望值和風險分布
    return {
        strategy: {
            'expected_position': np.mean(results[strategy]),
            'std': np.std(results[strategy]),
            'best_case': np.percentile(results[strategy], 10),
            'worst_case': np.percentile(results[strategy], 90)
        }
        for strategy in strategies
    }
```

**關鍵模擬參數**：
| 參數 | 說明 | 數據來源 |
|-----|------|---------|
| 輪胎衰退曲線 | 不同胎種的圈速損失 | 歷史數據擬合 |
| Pit Delta | 進站損失時間 | 各賽道實測 |
| Safety Car 機率 | 每圈 SC 出動機率 | 歷史統計 ~3% |
| 對手策略分布 | 對手可能的進站時機 | ML 預測 |

#### 學術參考文獻

**核心論文**：

1. **Data-driven pit stop decision support for Formula 1 using deep learning models** (2025)
   - 作者: Sasikumar et al.
   - 來源: Frontiers in Artificial Intelligence (PMC12626961)
   - 方法: Bi-LSTM, TCN-GRU, GRU, InceptionTime, CNN-BiLSTM
   - 結果: Bi-LSTM 達到 F1-score 0.81, Recall 0.86
   - 數據: FastF1 API, 2020-2024 賽季
   - 關鍵技術: SMOTE 類別平衡, 10-timestep 序列

2. **Explainable Reinforcement Learning for Formula One Race Strategy** (2025)
   - 作者: Thomas et al. (Mercedes-AMG PETRONAS F1 Team + Imperial College)
   - 來源: ACM SAC '25 (10.1145/3672608.3707766)
   - 方法: PPO (Proximal Policy Optimization) + SHAP 解釋
   - 結果: 平均改善 8.6 秒, 76% 比賽進入前五
   - 特色: 可解釋 AI, 決策樹代理模型

3. **Virtual Strategy Engineer (VSE)** (2020)
   - 作者: Heilmeier et al.
   - 方法: FFNN + LSTM 混合架構
   - 結果: 2019 中國 GP 模擬平均 P9.51

4. **On the optimization of pit stop strategies via dynamic programming** (2023)
   - 作者: Heine & Thraves
   - 來源: Central European Journal of Operations Research
   - 方法: 動態規劃 + Monte Carlo

5. **Optimizing Pit-Stop Strategies with Competition in a Zero-Sum Feedback Stackelberg Game** (2023)
   - 作者: Aguad & Thraves
   - 方法: 博弈論框架
   - 結果: 平均節省 2.3 秒, 降低 17.8% Undercut 風險

6. **Lo Stratega: predicting F1 race strategies with reinforcement learning** (2021)
   - 作者: Marinaro (Politecnico di Milano)
   - 方法: 多智能體強化學習

7. **Open loop planning for formula 1 race strategy identification** (2021)
   - 作者: Piccinotti et al.
   - 方法: Q-learning + Open-Loop UCT + Monte Carlo + TD
   - 特色: Bayesian 超參數優化

8. **Mastering Nordschleife - A comprehensive race simulation for AI strategy decision-making** (2023)
   - 作者: Boettinger & Klotz
   - 來源: arXiv:2306.16088
   - 方法: OpenAI Gym + 強化學習
   - 特色: GT 賽車策略, Nurburgring 24h

---

### 3. Undercut Threat (Undercut 威脅分析)

**目標**: 評估 Undercut 戰術的威脅程度

**功能需求**:
- [ ] 計算 Undercut 成功所需條件
- [ ] 評估後方車手 Undercut 威脅等級
- [ ] 預警系統：提醒潛在 Undercut 風險
- [ ] 分析防守方應對時機

**數據來源**:
- Live Timing: 位置間距、進站狀態
- FastF1: Pit Delta、Out Lap 預估
- 歷史數據: Undercut 成功率統計

**技術方案**:
```
輸入特徵:
- gap_to_car_behind (秒)
- opponent_tyre_age
- pit_delta
- out_lap_estimate
- track_pit_lane_time

輸出:
- undercut_threat_level (Low/Medium/High/Critical)
- safe_pit_window
- recommended_response_lap
```

---

### 4. Track Pulse (賽道脈動)

**目標**: 提供整場比賽的即時動態概覽

**功能需求**:
- [ ] 即時戰況摘要生成
- [ ] 關鍵事件偵測和標記
- [ ] 冠軍預測動態更新
- [ ] 激戰熱區識別
- [ ] 趨勢分析（誰在追趕/掉速）

**數據來源**:
- Live Timing: 全場車手數據
- 現有 Win Probability: 勝率變化
- 事件偵測: Safety Car、紅旗、事故

**技術方案**:
```
輸出內容:
- race_summary_text (自然語言)
- key_battles[] (正在進行的對戰)
- momentum_drivers[] (上升趨勢車手)
- championship_implications
- next_predicted_event
```

---

## 開發優先順序

| 順序 | 功能 | 難度 | 預估時間 | 依賴 |
|-----|------|-----|---------|-----|
| 1 | Undercut Threat | 中 | 1-2 週 | Win Probability |
| 2 | Battle Forecast | 高 | 2-3 週 | Undercut Threat |
| 3 | Pit Strategy | 高 | 2-3 週 | Undercut Threat |
| 4 | Track Pulse | 中 | 1-2 週 | 以上全部 |

---

## 技術架構

### 模組結構
```
CLI_modules/cli/prediction/
├── live_win_probability/     # 現有
│   ├── predictor.py
│   └── model_trainer.py
├── battle_forecast/          # 新增
│   ├── predictor.py
│   └── overtake_model.py
├── pit_strategy/             # 新增
│   ├── analyzer.py
│   └── tyre_model.py
├── undercut_threat/          # 新增
│   └── evaluator.py
└── track_pulse/              # 新增
    └── summarizer.py
```

### GUI 整合
```
modules/gui/
├── live_insights/            # 新增
│   ├── battle_forecast_widget.py
│   ├── pit_strategy_widget.py
│   ├── undercut_threat_widget.py
│   └── track_pulse_widget.py
```

---

## 參考資料

- AWS F1 Insights: https://aws.amazon.com/sports/f1/
- 現有 Win Probability 實現: `CLI_modules/cli/prediction/live_win_probability/`
- Rain Analysis 架構參考: `modules/gui/rain_analysis/`

---

## 核心方法論：Monte Carlo 模擬

### 概念說明

Monte Carlo 模擬是一種基於隨機採樣的數值計算方法，用於處理複雜的機率問題。在運動分析領域（特別是足球和 F1 賽事），Monte Carlo 方法被廣泛用於預測比賽結果和策略評估。

### 足球勝率預測的 Monte Carlo 方法 (參考 American Soccer Analysis)

**核心思想**：將比賽分割為小時間段，根據進球機率模擬多次比賽

```python
# 足球勝率 Monte Carlo 模擬 (業界標準)
def simulate_soccer_match(home_xg, away_xg, current_score, remaining_minutes, n_simulations=10000):
    """
    home_xg: 主場隊預期進球數/90分鐘
    away_xg: 客場隊預期進球數/90分鐘
    current_score: (home_goals, away_goals)
    remaining_minutes: 剩餘時間
    """
    home_wins, draws, away_wins = 0, 0, 0
    
    # 計算每分鐘進球率 (泊松分布)
    home_rate = home_xg / 90
    away_rate = away_xg / 90
    
    for _ in range(n_simulations):
        home_goals, away_goals = current_score
        
        # 模擬每分鐘
        for minute in range(remaining_minutes):
            # 泊松過程：進球機率
            if np.random.random() < home_rate:
                home_goals += 1
            if np.random.random() < away_rate:
                away_goals += 1
        
        # 統計結果
        if home_goals > away_goals:
            home_wins += 1
        elif home_goals < away_goals:
            away_wins += 1
        else:
            draws += 1
    
    return {
        'home_win': home_wins / n_simulations,
        'draw': draws / n_simulations,
        'away_win': away_wins / n_simulations
    }
```

### F1 Win Probability 的 Monte Carlo 應用

與足球不同，F1 比賽的 Monte Carlo 模擬需要考慮：

| 因素 | 足球 | F1 |
|-----|------|-----|
| 關鍵事件 | 進球 | 進站、超車、故障、SC/VSC |
| 時間單位 | 每分鐘 | 每圈 |
| 隨機變量 | 進球機率 | 輪胎衰退、對手策略、安全車 |
| 結果類型 | 勝/平/負 | 20 位車手排名 |

**F1 適用的 Monte Carlo 框架**：

```python
def simulate_f1_race_outcome(current_state, remaining_laps, n_simulations=10000):
    """
    模擬 F1 比賽結果分布
    """
    position_counts = {driver: [] for driver in current_state.drivers}
    
    for _ in range(n_simulations):
        # 複製當前狀態
        sim_state = copy.deepcopy(current_state)
        
        for lap in range(remaining_laps):
            # 1. 模擬輪胎衰退
            for driver in sim_state.drivers:
                sim_state.lap_time[driver] += sample_degradation(
                    tyre_age=sim_state.tyre_age[driver],
                    compound=sim_state.tyre_compound[driver],
                    track_wear=sim_state.track_rubber
                )
            
            # 2. 模擬進站決策
            for driver in sim_state.drivers:
                if should_pit(sim_state, driver):
                    sim_state = execute_pit(sim_state, driver)
            
            # 3. 模擬超車
            sim_state = simulate_overtakes(sim_state)
            
            # 4. 模擬隨機事件 (SC, VSC, 故障)
            event = sample_random_event(lap, remaining_laps)
            if event:
                sim_state = apply_event(sim_state, event)
            
            # 更新位置
            sim_state = update_positions(sim_state)
        
        # 記錄最終位置
        for driver, position in sim_state.final_positions.items():
            position_counts[driver].append(position)
    
    # 計算各車手期望位置和勝率
    return {
        driver: {
            'win_probability': sum(1 for p in positions if p == 1) / n_simulations,
            'expected_position': np.mean(positions),
            'position_std': np.std(positions)
        }
        for driver, positions in position_counts.items()
    }
```

### 與現有系統的整合計劃

**階段 1**: 在 Pit Strategy 模組中實現策略評估 Monte Carlo
```
pit_strategy/
├── monte_carlo_simulator.py  # 策略模擬引擎
├── degradation_model.py      # 輪胎衰退模型
└── event_sampler.py          # 隨機事件採樣器
```

**階段 2**: 擴展至 Win Probability 系統
```
live_win_probability/
├── predictor.py              # 現有 XGBoost 模型
├── monte_carlo_predictor.py  # 新增 Monte Carlo 版本
└── hybrid_predictor.py       # 結合 ML + Monte Carlo
```

---

## 學術參考文獻總覽

### F1 進站策略 (Pit Strategy)

| 論文 | 作者 | 年份 | 方法 | 核心成果 |
|-----|------|-----|------|---------|
| Data-driven pit stop decision support using DL | Sasikumar et al. | 2025 | Bi-LSTM, TCN-GRU | F1-score 0.81 |
| Explainable RL for F1 Race Strategy | Thomas et al. (Mercedes) | 2025 | PPO + SHAP | P5.33 平均成績 |
| Virtual Strategy Engineer | Heilmeier et al. | 2020 | FFNN + LSTM | P9.51 模擬成績 |
| Pit-Stop via Dynamic Programming | Heine & Thraves | 2023 | DP + Monte Carlo | 最優解保證 |
| Zero-Sum Stackelberg Game | Aguad & Thraves | 2023 | 博弈論 | 降低 17.8% Undercut 風險 |
| Lo Stratega | Marinaro | 2021 | Multi-Agent RL | 多車策略互動 |
| Open Loop UCT Planning | Piccinotti et al. | 2021 | Q-learning + MCTS | Bayesian 優化 |

### 運動勝率預測 (Win Probability)

| 論文/來源 | 領域 | 方法 | 說明 |
|----------|-----|------|-----|
| American Soccer Analysis | 足球 | Monte Carlo | 業界標準, 10000 次模擬 |
| Opta Analytics | 足球 | 貝葉斯 + ML | 官方數據供應商 |
| FiveThirtyEight | 多運動 | ELO + Monte Carlo | 最知名勝率模型 |
| AWS F1 Insights | F1 | 不公開 (疑似 RL) | 官方合作 |
| KU Leuven DTAI Sports Lab | 足球 | Temporal Point Process | 學術研究 |

### 關鍵數據源

- **FastF1 API**: Python 套件, 免費, 賽道/遙測/計時數據
- **OpenF1 API**: 即時計時數據, 用於 Live 功能
- **Ergast API**: 歷史比賽結果 (1950-2024)
- **FIA 官方文件**: 規則、罰則、技術指令

---

## 更新記錄

| 日期 | 更新內容 |
|-----|---------|
| 2025-12-01 | 建立初始規劃文檔 |
| 2025-12-01 | 新增 Monte Carlo 模擬方法論 |
| 2025-12-01 | 新增 8 篇 Pit Strategy 學術論文參考 |
| 2025-12-01 | 新增足球與 F1 勝率預測對照表 |

