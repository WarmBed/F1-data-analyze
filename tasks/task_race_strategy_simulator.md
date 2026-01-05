# Task: Race Strategy Simulator (獨立 GUI)

## 📋 任務概述

**專案名稱**: `Race Strategy Simulator`  
**類型**: 獨立 GUI 應用程式 (非主 GUI 模組)  
**入口點**: `strategy_simulator_gui.py`

**核心目標**: 將 FP2 Long Run 數據轉化為正賽策略藍圖

---

## 🎯 核心功能

### 1. 單車最佳化矩陣 (Optimum Matrix)
- Lap-by-Lap 逐圈模擬
- 對沖三大變數：輪胎衰退 + 燃油效應 + 進站損失
- 產出多個 Plan 比較 (Plan A/B/C)

### 2. 蒙地卡羅模擬 (Monte Carlo)
- 隨機變異：衰退率波動、Pit Stop 時間波動
- 1000+ 次模擬取最佳策略分布
- 置信區間輸出

### 3. 安全車情境模擬 (Safety Car Scenarios)
- SC/VSC 進站損失差異 (50-55% / 35-40% of green)
- 低油量輪胎表現評估
- Bail-out Tyre 建議 (備援輪胎策略)

### 4. 對手策略互動
- 模擬對手策略組合
- Undercut / Overcut 效應
- 相對位置變化

---

## 🔧 已有資源確認

| 資源 | 路徑 | 狀態 |
|------|------|------|
| **Pit Loss 資料庫** | `config/pit_loss_database.json` | ✅ 完整 (含 SC/VSC) |
| **燃油係數資料庫** | `config/fuel_coefficients_database.json` | ✅ 完整 |
| **輪胎衰退資料庫** | `config/tire_degradation_database.json` | ✅ 完整 |
| **Long Run Calculator** | `modules/gui/long_run_analysis/long_run_calculator.py` | ✅ 可複用核心邏輯 |

### 主 GUI Long Run 模組分析

主 GUI 已有完整的 Long Run Analysis 模組 (`modules/gui/long_run_analysis/`)：

```
long_run_analysis/
├── long_run_mdi.py              # MDI 主視窗 (2364 行)
├── long_run_calculator.py       # 核心計算引擎 (515 行) ⭐ 可複用
├── long_run_data_loader.py      # API 數據載入器
├── widgets/
│   ├── stint_selector.py        # Stint 選擇器
│   ├── fuel_settings.py         # 燃油設定
│   ├── track_evolution.py       # Track Evolution
│   ├── degradation_results.py   # 衰退結果
│   ├── degradation_chart.py     # 衰退圖表
│   └── compound_comparison.py   # 胎種比較
└── utils/
    └── ...
```

**核心類別 (`LongRunCalculator`) 已實現：**
- ✅ `LapData` - 單圈數據結構
- ✅ `StintInfo` - Stint 偵測結果
- ✅ `DriverFuelSettings` - 燃油設定
- ✅ `DegradationResult` - 衰退計算結果
- ✅ `auto_detect_long_runs()` - 自動偵測 Long Run (≥4 圈)
- ✅ `calculate_degradation()` - 計算真實衰退率
- ✅ `_calculate_track_evolution_statistical()` - 統計模型
- ✅ `_calculate_track_evolution_reference()` - 參考車手模型

**Strategy Simulator 策略：**
- 直接 **複製** `long_run_calculator.py` 到獨立 GUI
- 或 **import** 使用（需確保路徑正確）
- 建議：複製並獨立維護，避免主 GUI 依賴問題

---

## 🎨 UI 設計 (ASCII 草圖)

### 主視窗佈局

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🏁 Race Strategy Simulator                                    [_] [□] [X]     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ 左側面板 (參數輸入) ────────┐  ┌─ 右側面板 (模擬結果) ─────────────────────┐ │
│  │                             │  │                                           │ │
│  │  [賽事選擇]                 │  │  ┌─ Tabs ─────────────────────────────┐   │ │
│  │  Year: [2025 ▼]             │  │  │ 策略比較 │ 曲線圖 │ SC情境 │ 詳細  │   │ │
│  │  Race: [Japan ▼]            │  │  └─────────────────────────────────────┘   │ │
│  │  Total Laps: [53]           │  │                                           │ │
│  │                             │  │  (根據 Tab 顯示不同內容)                   │ │
│  │  [衰退數據來源]             │  │                                           │ │
│  │  ○ 讀取 Long Run JSON       │  │                                           │ │
│  │  ○ 手動輸入衰退率           │  │                                           │ │
│  │  ○ 使用資料庫預設           │  │                                           │ │
│  │                             │  │                                           │ │
│  │  [輪胎衰退率 (s/lap)]       │  │                                           │ │
│  │  SOFT:   [0.120]            │  │                                           │ │
│  │  MEDIUM: [0.080]            │  │                                           │ │
│  │  HARD:   [0.045]            │  │                                           │ │
│  │                             │  │                                           │ │
│  │  [燃油參數]                 │  │                                           │ │
│  │  Start Fuel: [110] kg       │  │                                           │ │
│  │  Fuel/Lap:   [1.65] kg      │  │                                           │ │
│  │  Fuel Effect:[0.030] s/kg   │  │                                           │ │
│  │                             │  │                                           │ │
│  │  [進站參數]                 │  │                                           │ │
│  │  Pit Loss (GREEN): [24.0] s │  │                                           │ │
│  │  Pit Loss (SC):    [12.5] s │  │                                           │ │
│  │  Pit Loss (VSC):   [9.0] s  │  │                                           │ │
│  │                             │  │                                           │ │
│  │  [模擬設定]                 │  │                                           │ │
│  │  Max Stops: [3 ▼]           │  │                                           │ │
│  │  Monte Carlo: [1000] 次     │  │                                           │ │
│  │                             │  │                                           │ │
│  │  [🚀 執行模擬]              │  │                                           │ │
│  │                             │  │                                           │ │
│  └─────────────────────────────┘  └───────────────────────────────────────────┘ │
│                                                                                 │
│  Status: Ready                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 1: 策略比較 (Plan Comparison)

```
┌─ 策略比較 ──────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌─ 最佳策略排名 ─────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  Rank │ Strategy      │ Total Time   │ Δ to Best │ Confidence │ Status     │ │
│  │  ─────┼───────────────┼──────────────┼───────────┼────────────┼──────────  │ │
│  │  🥇 1 │ M→H (1-Stop)  │ 1:32:45.234  │ --        │ 85.2%      │ ⭐ OPTIMAL │ │
│  │  🥈 2 │ M→H→S (2-Stop)│ 1:32:48.891  │ +3.657s   │ 78.5%      │ ✓ VIABLE  │ │
│  │  🥉 3 │ S→M→H (2-Stop)│ 1:32:52.123  │ +6.889s   │ 72.3%      │ ✓ VIABLE  │ │
│  │     4 │ M→M→H (2-Stop)│ 1:33:01.456  │ +16.222s  │ 45.1%      │ ⚠ RISKY   │ │
│  │     5 │ H→M (1-Stop)  │ 1:33:05.789  │ +20.555s  │ 38.7%      │ ✗ SLOW    │ │
│  │                                                                             │ │
│  │  💡 Confidence = 蒙地卡羅模擬中該策略勝出的機率                              │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 最佳策略詳情 (Plan A: M→H) ───────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  Stint 1: Lap 1-22 (MEDIUM)  │  22 laps  │  Est. Deg: +1.76s               │ │
│  │  ════════════════════════════════════════════════════════════════════════  │ │
│  │                              ↓ PIT (Lap 22)  Pit Loss: 24.0s               │ │
│  │  ════════════════════════════════════════════════════════════════════════  │ │
│  │  Stint 2: Lap 23-53 (HARD)   │  31 laps  │  Est. Deg: +1.40s               │ │
│  │                                                                             │ │
│  │  📊 總計: 53 laps | 1 stop | Total Time: 1:32:45.234                       │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 2: 曲線圖 (Lap Time Curves)

```
┌─ 曲線圖 ────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌─ 顯示選項 ─────────────────────────────────────────────────────────────────┐ │
│  │  [✓] Plan A (M→H)  [✓] Plan B (M→H→S)  [ ] Plan C (S→M→H)                  │ │
│  │  [✓] 顯示燃油校正  [✓] 顯示累積時間                                         │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ Lap Time vs Lap Number ───────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  Time │                                                                     │ │
│  │  (s)  │                                                                     │ │
│  │       │  ─── Plan A (M→H)                                                   │ │
│  │ 94.0  │  ─── Plan B (M→H→S)                                                 │ │
│  │       │                                          ╱─────                     │ │
│  │ 93.5  │                                    ╱────╱                           │ │
│  │       │                              ╱────╱                                 │ │
│  │ 93.0  │                        ╱────╱                                       │ │
│  │       │  ╱─────────────────────╱                                            │ │
│  │ 92.5  │ ╱                    ╱│ Pit                                         │ │
│  │       │╱               ╱────╱ │                                             │ │
│  │ 92.0  │          ╱────╱       ↓                                             │ │
│  │       │    ╱────╱       ┌─────────────────────                              │ │
│  │ 91.5  │───╱             │ Fresh HARD tyres                                  │ │
│  │       │                 └──────────────────────────────────                 │ │
│  │ 91.0  │                                                                     │ │
│  │       └──────────────────────────────────────────────────────────────────   │ │
│  │          1    5   10   15   20   25   30   35   40   45   50   53          │ │
│  │                                  Lap Number                                 │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ Cumulative Time Comparison ───────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  Δ Time │                                                                   │ │
│  │  to     │           Plan B slower                                          │ │
│  │  Plan A │  +5s  ─────────────────────╲                                     │ │
│  │         │                             ╲                                    │ │
│  │         │   0  ═══════════════════════════════════════════                 │ │
│  │         │                               ╱                                  │ │
│  │         │  -5s ────────────────────────╱                                   │ │
│  │         │           Plan B faster (after 2nd pit)                          │ │
│  │         └────────────────────────────────────────────────────────────────  │ │
│  │            1    10    20    30    40    50                                 │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 3: 安全車情境 (Safety Car Scenarios)

```
┌─ 安全車情境模擬 ────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌─ SC 發生時機模擬 ─────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  如果 SC 發生在...  │  最佳反應        │  預期效益      │  風險           │ │
│  │  ───────────────────┼──────────────────┼────────────────┼───────────────  │ │
│  │  Lap 1-10 (早期)    │  維持策略        │  --            │  低             │ │
│  │  Lap 11-18          │  提前進站換 H    │  +8.5s         │  中 (H冷胎)     │ │
│  │  Lap 19-25 ⭐       │  順勢進站        │  +11.5s        │  低 ⭐ 最佳    │ │
│  │  Lap 26-35          │  延後換 S        │  +6.2s         │  中             │ │
│  │  Lap 36-53 (晚期)   │  換 S 衝刺       │  +3.8s         │  高 (S衰退快)   │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 低油量輪胎表現評估 ─────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  輪胎   │ 高油量 (>70kg) │ 中油量 (40-70kg) │ 低油量 (<40kg) │ 評估      │ │
│  │  ───────┼────────────────┼──────────────────┼────────────────┼─────────  │ │
│  │  SOFT   │ ⚠ 衰退快       │ ✓ 可接受         │ ⭐ 表現佳      │ 衝刺用    │ │
│  │  MEDIUM │ ✓ 穩定         │ ✓ 穩定           │ ✓ 穩定         │ 萬用      │ │
│  │  HARD   │ ✓ 耐久         │ ✓ 耐久           │ ⚠ 抓地不足     │ 長 Stint  │ │
│  │                                                                             │ │
│  │  ⚠️ 警告: HARD 在低油量 (Lap 40+) 表現可能下降                              │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ Bail-out Tyre 建議 (備援輪胎) ───────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  📌 根據模擬結果，建議準備以下備援輪胎:                                     │ │
│  │                                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │ │
│  │  │  🔴 SOFT x 1   - SC 發生時的衝刺選項                                │   │ │
│  │  │  🟡 MEDIUM x 1 - HARD 表現不佳時的備援                              │   │ │
│  │  └─────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                             │ │
│  │  理由:                                                                      │ │
│  │  • 模擬顯示 HARD 在 Lap 40+ 低油量時抓地力下降 12%                         │ │
│  │  • 若 Lap 35+ 發生 SC，換 MEDIUM 可降低風險                                │ │
│  │  • SOFT 適合 Lap 45+ 的 SC 後衝刺 (僅需撐 8-10 圈)                         │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 4: 詳細數據 (Detailed Data)

```
┌─ 詳細數據 ──────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌─ 逐圈模擬數據 (Plan A: M→H) ───────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  Lap │ Compound │ Tyre Age │ Fuel(kg) │ Raw Time │ Fuel Adj │ Deg Adj │ Net│ │
│  │  ────┼──────────┼──────────┼──────────┼──────────┼──────────┼─────────┼────│ │
│  │    1 │ MEDIUM   │    1     │  110.0   │  92.50   │  +0.00   │  +0.00  │92.5│ │
│  │    2 │ MEDIUM   │    2     │  108.4   │  92.58   │  -0.05   │  +0.08  │92.6│ │
│  │    3 │ MEDIUM   │    3     │  106.7   │  92.66   │  -0.10   │  +0.16  │92.7│ │
│  │  ... │ ...      │   ...    │  ...     │  ...     │  ...     │  ...    │... │ │
│  │   22 │ MEDIUM   │   22     │   73.7   │  94.26   │  -1.09   │  +1.76  │94.9│ │
│  │  ════════════════════════════ PIT STOP (24.0s) ════════════════════════════ │ │
│  │   23 │ HARD     │    1     │   72.1   │  92.00   │  -1.14   │  +0.00  │90.9│ │
│  │   24 │ HARD     │    2     │   70.4   │  92.05   │  -1.19   │  +0.05  │90.9│ │
│  │  ... │ ...      │   ...    │  ...     │  ...     │  ...     │  ...    │... │ │
│  │   53 │ HARD     │   31     │   24.9   │  93.40   │  -2.55   │  +1.40  │92.3│ │
│  │                                                                             │ │
│  │  ═══════════════════════════════════════════════════════════════════════   │ │
│  │  Total Race Time: 1:32:45.234  │  Pit Stops: 1  │  Total Pit Loss: 24.0s   │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  [匯出 CSV]  [匯出 Excel]  [複製到剪貼簿]                                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 核心演算法

### 1. 單圈時間計算

```python
def calculate_lap_time(
    base_lap_time: float,      # 最快圈速 (新胎滿油)
    tyre_age: int,             # 輪胎已跑圈數
    tyre_compound: str,        # SOFT/MEDIUM/HARD
    fuel_remaining: float,     # 剩餘燃油 (kg)
    fuel_start: float,         # 起始燃油 (kg)
    degradation_rate: float,   # 每圈衰退 (s/lap)
    fuel_effect: float         # 燃油效應 (s/kg)
) -> float:
    """
    計算預估單圈時間
    
    公式:
    lap_time = base + (tyre_age * deg_rate) - ((fuel_start - fuel_remaining) * fuel_effect)
    """
    tyre_degradation = tyre_age * degradation_rate
    fuel_benefit = (fuel_start - fuel_remaining) * fuel_effect
    
    return base_lap_time + tyre_degradation - fuel_benefit
```

### 2. 策略總時間計算

```python
def calculate_strategy_time(
    strategy: List[Stint],     # [Stint(compound='M', laps=22), Stint(compound='H', laps=31)]
    pit_loss: float,           # 進站損失
    race_laps: int,            # 總圈數
    params: SimulationParams   # 所有參數
) -> float:
    """
    計算策略總時間
    
    公式:
    total = Σ(lap_times) + (num_stops * pit_loss)
    """
    total_time = 0.0
    current_fuel = params.fuel_start
    
    for stint in strategy:
        for lap in range(stint.laps):
            lap_time = calculate_lap_time(
                base_lap_time=params.base_time,
                tyre_age=lap + 1,
                tyre_compound=stint.compound,
                fuel_remaining=current_fuel,
                fuel_start=params.fuel_start,
                degradation_rate=params.deg_rates[stint.compound],
                fuel_effect=params.fuel_effect
            )
            total_time += lap_time
            current_fuel -= params.fuel_per_lap
        
        # Add pit loss (except for last stint)
        if stint != strategy[-1]:
            total_time += pit_loss
    
    return total_time
```

### 3. 蒙地卡羅模擬

```python
def monte_carlo_simulation(
    strategies: List[Strategy],
    params: SimulationParams,
    iterations: int = 1000
) -> Dict[str, float]:
    """
    蒙地卡羅模擬 - 加入隨機變異
    
    變異參數:
    - 衰退率: ±15% 隨機波動
    - Pit Stop: ±2s 隨機波動
    - 安全車: 20% 機率發生 SC
    """
    win_counts = {s.name: 0 for s in strategies}
    
    for _ in range(iterations):
        # 加入隨機變異
        varied_params = params.with_random_variation(
            deg_variance=0.15,      # ±15% 衰退波動
            pit_variance=2.0,       # ±2s 進站波動
            sc_probability=0.20     # 20% SC 機率
        )
        
        # 計算各策略時間
        times = {}
        for strategy in strategies:
            if varied_params.safety_car_lap:
                # SC 情境計算
                times[strategy.name] = calculate_strategy_with_sc(
                    strategy, varied_params
                )
            else:
                times[strategy.name] = calculate_strategy_time(
                    strategy, varied_params
                )
        
        # 記錄勝出策略
        winner = min(times, key=times.get)
        win_counts[winner] += 1
    
    # 轉換為置信度百分比
    return {name: count / iterations * 100 for name, count in win_counts.items()}
```

### 4. 安全車情境評估

```python
def evaluate_safety_car_impact(
    strategy: Strategy,
    sc_lap: int,
    params: SimulationParams
) -> Dict[str, Any]:
    """
    評估 SC 發生時的策略影響
    
    返回:
    - 最佳反應 (維持/提前進站/延後進站)
    - 預期效益
    - 風險評估
    """
    # 計算 GREEN 進站損失 vs SC 進站損失
    green_pit_loss = params.pit_loss_green
    sc_pit_loss = params.pit_loss_sc
    benefit = green_pit_loss - sc_pit_loss  # 約 11-12s
    
    # 評估當前 Stint 狀態
    current_stint = strategy.get_stint_at_lap(sc_lap)
    remaining_stint_laps = current_stint.end_lap - sc_lap
    
    # 決策邏輯
    if remaining_stint_laps <= 3:
        # 接近原定進站點 - 提前進站
        return {
            'action': '提前進站',
            'benefit': benefit,
            'risk': 'LOW',
            'reason': f'原定 Lap {current_stint.end_lap} 進站，SC 效益 +{benefit:.1f}s'
        }
    elif remaining_stint_laps >= 10:
        # 距離進站還很遠 - 維持策略
        return {
            'action': '維持策略',
            'benefit': 0,
            'risk': 'LOW',
            'reason': '輪胎狀態良好，無需提前進站'
        }
    else:
        # 中間狀態 - 需要權衡
        return {
            'action': '考慮進站',
            'benefit': benefit * 0.7,  # 打折扣
            'risk': 'MEDIUM',
            'reason': f'需權衡：輪胎還剩 {remaining_stint_laps} 圈壽命'
        }
```

### 5. Bail-out Tyre 建議

```python
def suggest_bailout_tyres(
    primary_strategy: Strategy,
    simulation_results: Dict,
    params: SimulationParams
) -> List[BailoutSuggestion]:
    """
    根據模擬結果建議備援輪胎
    
    評估條件:
    1. 主策略最後 Stint 使用 HARD 且 Stint > 25 圈
    2. 低油量時 HARD 表現下降
    3. SC 發生機率高的賽道
    """
    suggestions = []
    
    last_stint = primary_strategy.stints[-1]
    
    # 條件 1: HARD 長 Stint 風險
    if last_stint.compound == 'HARD' and last_stint.laps > 25:
        suggestions.append(BailoutSuggestion(
            compound='MEDIUM',
            quantity=1,
            reason='HARD 在 Lap 40+ 低油量時抓地力下降，MEDIUM 作為備援'
        ))
    
    # 條件 2: SC 衝刺選項
    if simulation_results['sc_probability'] > 0.15:  # SC 機率 > 15%
        suggestions.append(BailoutSuggestion(
            compound='SOFT',
            quantity=1,
            reason='SC 發生時的衝刺選項 (最後 10 圈內)'
        ))
    
    return suggestions
```

### 6. Undercut/Overcut 計算 (對手策略互動)

```python
@dataclass
class OpponentStrategy:
    """對手策略設定"""
    driver_code: str
    strategy: List[Stint]  # 預估對手策略
    current_gap: float     # 當前差距 (秒, 正值=我在前)
    lap_time_delta: float  # 對手相對圈速差 (秒, 正值=我較快)


def calculate_undercut_window(
    my_strategy: Strategy,
    opponent: OpponentStrategy,
    params: SimulationParams
) -> Dict[str, Any]:
    """
    計算 Undercut 窗口
    
    Undercut 原理:
    - 提前進站換新胎，利用 Out Lap 的速度優勢抵銷 Pit Loss
    - 新胎 vs 舊胎的速度差 > Pit Loss 時間 / 圈數
    
    公式:
    undercut_gain_per_lap = tyre_delta (新胎 vs 舊胎速度差)
    break_even_laps = pit_loss / undercut_gain_per_lap
    """
    results = {
        'can_undercut': False,
        'optimal_lap': None,
        'expected_gain': 0.0,
        'window': [],
        'risk': 'LOW'
    }
    
    # 計算各圈 Undercut 效益
    for lap in range(1, params.race_laps + 1):
        # 假設我在 lap 圈進站
        my_new_tyre_time = calculate_lap_time(
            base_time=params.base_time,
            tyre_age=1,  # 新胎
            compound='HARD',  # 假設換硬胎
            fuel_remaining=params.fuel_at_lap(lap),
            ...
        )
        
        # 對手繼續用舊胎
        opponent_old_tyre_time = calculate_lap_time(
            base_time=params.base_time + opponent.lap_time_delta,
            tyre_age=lap,  # 舊胎
            compound='MEDIUM',
            ...
        )
        
        # 每圈 Undercut 優勢
        undercut_gain = opponent_old_tyre_time - my_new_tyre_time
        
        # 需要多少圈抵銷 Pit Loss
        if undercut_gain > 0:
            break_even_laps = params.pit_loss / undercut_gain
            
            # 對手預計進站圈
            opponent_pit_lap = opponent.strategy[0].laps
            remaining_laps_before_opponent_pit = opponent_pit_lap - lap
            
            # 如果能在對手進站前完成 Undercut
            if remaining_laps_before_opponent_pit > break_even_laps:
                results['window'].append({
                    'lap': lap,
                    'gain_per_lap': undercut_gain,
                    'break_even': break_even_laps,
                    'net_gain': (remaining_laps_before_opponent_pit - break_even_laps) * undercut_gain
                })
    
    # 找最佳 Undercut 時機
    if results['window']:
        best = max(results['window'], key=lambda x: x['net_gain'])
        results['can_undercut'] = True
        results['optimal_lap'] = best['lap']
        results['expected_gain'] = best['net_gain']
    
    return results


def calculate_overcut_window(
    my_strategy: Strategy,
    opponent: OpponentStrategy,
    params: SimulationParams
) -> Dict[str, Any]:
    """
    計算 Overcut 窗口
    
    Overcut 原理:
    - 延後進站，利用對手換新胎後 Out Lap 較慢的機會
    - 對手 Out Lap 損失 + 我的舊胎仍有速度 > Pit Loss 差異
    
    適用情境:
    - 對手提前進站
    - 我的輪胎狀態仍良好
    - 賽道 Track Position 很重要 (難超車)
    """
    results = {
        'can_overcut': False,
        'optimal_lap': None,
        'expected_gain': 0.0,
        'window': [],
        'risk': 'MEDIUM'  # Overcut 通常風險較高
    }
    
    # 對手進站圈
    opponent_pit_lap = opponent.strategy[0].laps
    
    # 計算對手進站後我延後進站的效益
    for delay in range(1, 6):  # 延後 1-5 圈
        my_lap = opponent_pit_lap + delay
        
        # 我繼續用舊胎
        my_old_tyre_time = calculate_lap_time(
            tyre_age=my_lap,
            compound='MEDIUM',
            ...
        )
        
        # 對手 Out Lap (新胎但尚未進入狀態)
        opponent_out_lap_penalty = 1.5  # 秒 (Out Lap 通常較慢)
        opponent_new_tyre_time = calculate_lap_time(
            tyre_age=1,
            compound='HARD',
            ...
        ) + opponent_out_lap_penalty
        
        # Overcut 效益
        overcut_gain = opponent_new_tyre_time - my_old_tyre_time
        
        if overcut_gain > 0:
            results['window'].append({
                'delay_laps': delay,
                'my_pit_lap': my_lap,
                'gain': overcut_gain * delay
            })
    
    if results['window']:
        best = max(results['window'], key=lambda x: x['gain'])
        results['can_overcut'] = True
        results['optimal_lap'] = best['my_pit_lap']
        results['expected_gain'] = best['gain']
    
    return results
```

### 7. 對手策略模擬 Tab (新增)

```
┌─ 對手策略互動 ──────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌─ 對手設定 ─────────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  對手名稱: [Opponent ▼]  │  當前差距: [+2.5] s  │  相對圈速: [-0.1] s      │ │
│  │  預估策略: [M→H (1-Stop) ▼]  │  預計進站: Lap [20]                          │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ Undercut 分析 ────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  📊 Undercut 可行性: ✅ YES                                                 │ │
│  │                                                                             │ │
│  │  最佳 Undercut 時機: Lap 17 (對手預計 Lap 20 進站)                          │ │
│  │  預期收益: +1.8s                                                            │ │
│  │  每圈優勢: +0.6s (新 HARD vs 舊 MEDIUM)                                     │ │
│  │  Break-even: 3.2 圈                                                         │ │
│  │                                                                             │ │
│  │  ⚠️ 風險: 若對手 Cover (跟進站)，優勢將消失                                │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ Overcut 分析 ─────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  📊 Overcut 可行性: ⚠️ MARGINAL                                            │ │
│  │                                                                             │ │
│  │  最佳 Overcut 時機: Lap 22 (對手 Lap 20 進站後延後 2 圈)                    │ │
│  │  預期收益: +0.5s                                                            │ │
│  │  風險: 輪胎衰退可能抵銷優勢                                                  │ │
│  │                                                                             │ │
│  │  💡 建議: Undercut 效益更高，優先考慮                                       │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 相對位置時間線 (pyqtgraph) ───────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  Gap │                                                                      │ │
│  │  (s) │  ═══════════════════════════════════════════════════                │ │
│  │  +3  │         ╱──────╲                                                    │ │
│  │  +2  │────────╱        ╲                                                   │ │
│  │  +1  │                  ╲───────────────────────                           │ │
│  │   0  │═══════════════════════════════════════════════════                  │ │
│  │  -1  │                              ↑ My Pit  ↑ Opp Pit                    │ │
│  │      └──────────────────────────────────────────────────────────────────   │ │
│  │         1    5   10   15   20   25   30   35   40   45   50               │ │
│  │                                                                             │ │
│  │  ── 我的策略 (M→H, Pit Lap 17)                                             │ │
│  │  ── 對手策略 (M→H, Pit Lap 20)                                             │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ 檔案結構

```
strategy_simulator/
├── strategy_simulator_gui.py        # 🚀 獨立入口點
├── core/
│   ├── __init__.py
│   ├── lap_simulator.py             # 逐圈模擬引擎
│   ├── strategy_optimizer.py        # 策略最佳化
│   ├── monte_carlo.py               # 蒙地卡羅模擬
│   ├── safety_car_analyzer.py       # SC 情境分析
│   ├── bailout_advisor.py           # Bail-out 建議
│   ├── undercut_overcut.py          # ⭐ Undercut/Overcut 計算 (新增)
│   └── long_run_calculator.py       # ⭐ 複製自主 GUI (核心衰退計算)
├── gui/
│   ├── __init__.py
│   ├── main_window.py               # 主視窗
│   ├── input_panel.py               # 左側參數輸入
│   ├── results_tabs/
│   │   ├── __init__.py
│   │   ├── strategy_comparison.py   # Tab 1: 策略比較
│   │   ├── lap_curves.py            # Tab 2: 曲線圖 (pyqtgraph)
│   │   ├── safety_car_tab.py        # Tab 3: SC 情境
│   │   ├── opponent_tab.py          # ⭐ Tab 4: 對手策略互動 (新增)
│   │   └── detailed_data.py         # Tab 5: 詳細數據
│   └── widgets/
│       ├── __init__.py
│       ├── strategy_chart.py        # 策略曲線圖元件 (pyqtgraph)
│       └── gap_timeline.py          # ⭐ 相對差距時間線 (新增)
├── data/
│   ├── __init__.py
│   ├── config_loader.py             # 讀取 config/*.json
│   └── longrun_loader.py            # ⭐ 內建 Long Run 分析 (複用主 GUI 邏輯)
└── README.md
```

---

## ✅ 實施檢查清單

### 階段 1: 核心引擎

- [ ] 複製 `long_run_calculator.py` 並調整 import
- [ ] `lap_simulator.py` - 單圈時間計算
- [ ] `strategy_optimizer.py` - 策略生成與排序
- [ ] `monte_carlo.py` - 蒙地卡羅模擬
- [ ] 單元測試: 使用 2024 Japan GP 數據驗證

### 階段 2: SC + 對手分析

- [ ] `safety_car_analyzer.py` - SC 影響評估
- [ ] `bailout_advisor.py` - Bail-out 建議
- [ ] `undercut_overcut.py` - Undercut/Overcut 窗口計算
- [ ] 整合 `pit_loss_database.json` (GREEN/SC/VSC)

### 階段 3: GUI 實現 (pyqtgraph)

- [ ] `main_window.py` - 主視窗框架
- [ ] `input_panel.py` - 參數輸入面板
- [ ] `strategy_comparison.py` - Tab 1
- [ ] `lap_curves.py` - Tab 2 (pyqtgraph 互動曲線圖)
- [ ] `safety_car_tab.py` - Tab 3
- [ ] `opponent_tab.py` - Tab 4 (對手策略 + Undercut/Overcut)
- [ ] `detailed_data.py` - Tab 5
- [ ] `gap_timeline.py` - 相對差距時間線 (pyqtgraph)

### 階段 4: 整合

- [ ] 內建 Long Run 分析功能 (複用主 GUI 邏輯)
- [ ] 讀取 config/ 資料庫
- [ ] 匯出功能 (CSV, PNG)

---

## 📅 預估工時

| 階段 | 工時估算 |
|------|----------|
| 階段 1: 核心引擎 | 6-8 小時 |
| 階段 2: SC + 對手分析 | 5-6 小時 |
| 階段 3: GUI 實現 (pyqtgraph) | 10-12 小時 |
| 階段 4: 整合測試 | 3-4 小時 |
| **總計** | **24-30 小時** |

---

## ✅ 已確認事項

1. **對手策略互動**: ✅ 進階模式 - Undercut/Overcut 窗口計算
2. **Long Run 數據**: ✅ 獨立 GUI 內建相同邏輯，複製 `long_run_calculator.py`
3. **圖表庫**: ✅ pyqtgraph (互動式，可縮放拖曳)
4. **輪胎配額**: ✅ 簡化模式 (M→H, M→S→H 形式，不計算 13 套限制)
5. **Pit Loss**: ✅ 內建資料庫 (`config/pit_loss_database.json`)
6. **Bail-out Tyre**: ✅ 包含 SC 情境 + 低油量 HARD 表現評估

---

## 📝 下一步

確認無誤後，開始實施 **階段 1: 核心引擎**！
