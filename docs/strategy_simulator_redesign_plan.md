# F1T 策略模擬器 GUI 重構計劃

**日期**: 2026-01-04  
**狀態**: 開發中  
**目標**: 將策略模擬器從靜態結果展示升級為動態模擬視覺化系統

---

## 問題分析

### 原有設計的問題

1. **重複造輪子**: 創建了獨立的 `longrun_dialog.py`，而主 GUI 已有完整的 Long Run 分析模組
2. **缺少動態視覺化**: 只顯示最終策略排名，無法看到逐圈比賽過程
3. **Monte Carlo 結果不完整**: 只有簡單的勝率百分比，缺少分布圖、箱線圖等專業分析
4. **SC 事件配置簡陋**: 只有單一 SC 的簡單配置，無法模擬多次 SC 或 VSC
5. **靜態分析為主**: 無法視覺化策略在比賽中的動態變化

---

## 重構目標

### 核心功能目標

#### 1. **逐圈動態模擬動畫** (RaceAnimationWidget)
**目的**: 將策略模擬結果轉換為可視化的比賽過程

**功能需求**:
- 逐圈位置變化時間軸圖表
- 播放/暫停/步進控制
- 速度調整（1x, 2x, 4x, 8x）
- 顯示當前圈數、各策略位置、時間差
- SC/VSC 區域視覺化標記
- 進站事件標記和提示
- 策略資訊卡片（配方、輪胎壽命）

**數據來源**:
- `StrategySimulationResult.lap_times[]` - 每圈時間
- `StrategySimulationResult.stints[]` - Stint 資訊
- SC 事件列表

---

#### 2. **Monte Carlo 結果分布視覺化** (MonteCarloChartWidget)
**目的**: 深入展示 MC 模擬的統計結果，而非只有勝率百分比

**功能需求**:

##### 2.1 勝率分布圖 (WinProbabilityChart)
- 水平條形圖顯示各策略勝率
- 按勝率排序
- 顏色區分高/中/低勝率

##### 2.2 完賽時間分布直方圖 (TimeDistributionChart)
- 每個策略的完賽時間分布 histogram
- 顯示平均值、標準差
- 多策略疊加比較

##### 2.3 完賽位置箱線圖 (PositionBoxPlotChart)
- Box plot 顯示各策略的位置分布
- 顯示中位數、四分位數、異常值
- 位置穩定性分析

##### 2.4 SC 影響分析表 (SCImpactChart)
- SC 發生率統計
- 有/無 SC 時各策略表現對比
- SC 時機對策略影響分析

**數據來源**:
- `MonteCarloSummary` - MC 結果摘要
- 原始 MC 迭代數據（可選）

---

#### 3. **SC/VSC 事件手動注入器** (SCEventInjectorWidget)
**目的**: 替換簡單的單一 SC 配置，支援複雜的 SC 場景模擬

**功能需求**:

##### 3.1 三種模式
- **無 SC**: 綠旗比賽
- **隨機 SC**: Monte Carlo 使用隨機概率
- **手動 SC**: 指定具體事件

##### 3.2 手動事件配置
- 事件列表表格
  - 圈數 (Lap)
  - 持續時間 (Duration)
  - 類型 (SC/VSC)
- 新增/刪除事件按鈕
- 事件驗證（圈數範圍、重疊檢查）

##### 3.3 快速預設
- 早期 SC (Lap 10-15)
- 中期 SC (Lap 25-30)
- 晚期 SC (Lap 45-50)
- 雙 SC (Lap 15 + Lap 40)

**數據輸出**:
```python
[
    (start_lap: int, duration: int, is_vsc: bool),
    (20, 4, False),  # SC at lap 20, 4 laps, not VSC
    (45, 3, True),   # VSC at lap 45, 3 laps
]
```

---

#### 4. **整合動態模擬頁籤** (SimulationTab)
**目的**: 將動畫和 MC 圖表整合到統一介面

**佈局設計**:
```
┌─────────────────────────────────────────┐
│   Race Simulation Animation             │
│   ┌───────────────────────────────────┐ │
│   │  Position Timeline (pyqtgraph)    │ │
│   │  [Play] [Pause] [<<] [>>] Speed   │ │
│   └───────────────────────────────────┘ │
├─────────────────────────────────────────┤
│   Monte Carlo Analysis                  │
│   ┌──────────┬──────────┬─────────────┐│
│   │ Win Prob │ Time Dist│ Box Plot    ││
│   └──────────┴──────────┴─────────────┘│
└─────────────────────────────────────────┘
```

**資料流**:
1. `main_window._on_run_simulation()` 執行模擬
2. 結果傳遞到 `SimulationTab.set_results(results, params)`
3. SC 事件傳遞到 `SimulationTab.set_sc_events(events)`
4. MC 完成後傳遞到 `SimulationTab.set_monte_carlo_summary(summary)`

---

#### 5. **主 GUI Long Run 模組整合**
**目的**: 直接使用主 GUI 的 Long Run 分析，避免重複開發

**整合方式**:
```python
# 策略模擬器開啟 Long Run 對話框
dialog = QDialog()
longrun_widget = LongRunAnalysis(year=2025, race="Abu Dhabi", session="FP2")
dialog.addWidget(longrun_widget)
dialog.exec_()
```

**數據回傳**:
- 選中的 stints 資訊
- 計算出的退化率
- 套用到策略模擬器的輪胎參數

---

## 技術架構

### 目錄結構
```
strategy_simulator/
├── gui/
│   ├── main_window.py              # 主視窗
│   ├── input_panel.py              # 輸入面板（整合 SCEventInjector）
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── race_animation.py       # 動畫 Widget
│   │   ├── monte_carlo_chart.py    # MC 圖表 Widget
│   │   └── sc_event_injector.py    # SC 注入器 Widget
│   └── results_tabs/
│       ├── simulation_tab.py       # 動態模擬頁籤 (NEW)
│       ├── comparison_tab.py       # 策略對比頁籤
│       ├── chart_tab.py            # 圖表頁籤
│       └── ...
└── core/
    ├── lap_simulator.py            # 逐圈模擬引擎
    └── monte_carlo.py              # MC 模擬引擎
```

### 數據流設計

#### 模擬執行流程
```
用戶點擊 "執行模擬"
    ↓
input_panel.get_parameters()
    ├─ sc_mode: 'none' / 'random' / 'manual'
    └─ sc_events: [(lap, duration, is_vsc), ...]
    ↓
main_window._on_run_simulation(params)
    ↓
1. 策略優化 → results[]
2. 更新所有頁籤
    ├─ comparison_tab.update_results()
    ├─ chart_tab.update_results()
    └─ simulation_tab.set_results(results, params)
    ↓
3. 傳遞 SC 事件
    └─ simulation_tab.set_sc_events(events)
    ↓
4. Monte Carlo 模擬（可選）
    └─ simulation_tab.set_monte_carlo_summary(summary)
```

#### Widget 內部數據流

**RaceAnimationWidget**:
```python
set_simulation_results(results, params)
    ↓
_extract_lap_states(result) → LapState[]
    ↓
StrategyAnimation(name, color, lap_states)
    ↓
_update_chart() → pyqtgraph 繪製
```

**MonteCarloChartWidget**:
```python
set_monte_carlo_summary(summary)
    ↓
_update_win_probability(summary.win_percentages)
_update_time_distribution(summary.avg_times, summary.std_devs)
_update_position_boxplot(summary.position_distributions)
_update_sc_impact(summary.sc_stats)
```

---

## 依賴關係

### 外部函式庫
- `PyQt5`: GUI 框架
- `pyqtgraph`: 高效能圖表繪製（動畫、時間軸）
- `numpy`: 數據處理（直方圖、統計）
- `dataclasses`: 數據結構

### 內部模組
- `strategy_simulator.core.lap_simulator`: 逐圈模擬引擎
- `strategy_simulator.core.monte_carlo`: MC 模擬引擎
- `modules.gui.long_run_analysis.long_run_mdi`: 主 GUI Long Run 模組

---

## 已知問題與解決

### 問題 1: Long Run 對話框載入空白
**原因**: `LongRunAnalysis()` 創建時未傳入 `year`, `race`, `session` 參數  
**解決**: 修改為 `LongRunAnalysis(year=year, race=track_name, session="FP2")`

### 問題 2: RaceAnimationWidget 屬性錯誤
**原因**: 使用 `params.total_laps`，但實際屬性是 `params.race_laps`  
**解決**: 修改為正確屬性名稱

### 問題 3: SC 事件參數格式不一致
**原因**: 舊版使用單一 SC 配置，新版使用事件列表  
**影響**: `_run_sc_scenario_analysis()` 需同時支援新舊格式  
**解決**: 添加兼容層，優先使用 `sc_events`，回退到舊參數

---

## 測試計劃

### 單元測試
- [ ] `RaceAnimationWidget._extract_lap_states()` - 數據提取正確性
- [ ] `MonteCarloChartWidget` 各圖表渲染
- [ ] `SCEventInjectorWidget.get_events()` - 事件驗證

### 整合測試
- [ ] 完整模擬流程：輸入 → 模擬 → 視覺化
- [ ] Long Run 數據回傳到策略模擬器
- [ ] SC 事件正確傳遞到模擬引擎和動畫
- [ ] MC 結果正確顯示在圖表

### GUI 測試
- [ ] 動畫播放流暢性（60 FPS 目標）
- [ ] 圖表交互性（縮放、懸停提示）
- [ ] 大量迭代時的性能（1000+ MC 迭代）

---

## 開發進度

### ✅ 已完成
1. ✅ 刪除 `longrun_dialog.py`
2. ✅ 創建 `RaceAnimationWidget` (~450 行)
3. ✅ 創建 `MonteCarloChartWidget` (~400 行)
4. ✅ 創建 `SCEventInjectorWidget` (~300 行)
5. ✅ 創建 `SimulationTab` 整合頁籤
6. ✅ 整合到 `input_panel.py`（替換舊 SC 設置）
7. ✅ 整合到 `main_window.py`（數據流連接）
8. ✅ 修復 Long Run 參數傳遞問題
9. ✅ 修復 `race_laps` 屬性名稱錯誤

### 🔄 進行中
- 🔄 完整功能測試
- 🔄 錯誤處理完善

### 📋 待辦
- [ ] 性能優化（大量數據時的渲染）
- [ ] 用戶文檔撰寫
- [ ] 導出動畫為 GIF/視頻
- [ ] 國際化（i18n）支援

---

## 設計原則

### 1. 複用優先
- ✅ 直接使用主 GUI 的 `LongRunAnalysis`，不重複開發
- ✅ 使用現有的 `lap_simulator` 和 `monte_carlo` 引擎

### 2. 模組化
- ✅ 每個功能獨立成 Widget，便於測試和維護
- ✅ 清晰的數據流和介面定義

### 3. 向後兼容
- ✅ 新參數格式同時支援舊格式回退
- ✅ 現有功能不受影響

### 4. 性能考量
- ✅ 使用 `pyqtgraph` 而非 `matplotlib` 提升渲染速度
- ✅ 大量數據時使用採樣和批次渲染

---

## 參考資料

### 相關文件
- `tasks/strategy_simulator_redesign.md` - 原始任務文檔
- `CLI_modules/cli/core/function_mapper.py` - 功能映射參考
- `modules/gui/long_run_analysis/` - Long Run 模組實現

### API 文檔
- PyQtGraph: https://pyqtgraph.readthedocs.io/
- NumPy Histogram: https://numpy.org/doc/stable/reference/generated/numpy.histogram.html

---

## 結論

本次重構將策略模擬器從**靜態結果展示工具**升級為**動態模擬視覺化平台**，提供：
1. 直觀的逐圈比賽動畫
2. 專業的 Monte Carlo 統計分析
3. 靈活的 SC 場景配置
4. 與主 GUI 的無縫整合

通過模組化設計和清晰的數據流，系統易於維護和擴展，為未來的功能（如對手策略分析、實時策略建議）奠定基礎。
