# FP2 Long Run 與正賽圈速對應分析專案

## 專案概述

### 目標
建立 **2025 賽季各車隊 FP2 模擬圈數 ↔ 正賽圈數對應表**，用於預測正賽輪胎表現。

### 核心問題
每個車隊在 FP2 進行 Long Run 時的習慣不同：
- **起始燃油量不同**：有些車隊用 60kg，有些用 80kg
- **模擬目標不同**：有些模擬正賽前段（重車），有些模擬正賽中後段（輕車）
- **Stint 長度不同**：有些跑 8 圈，有些跑 15 圈

### 預期成果
```
┌─────────────┬────────────────────┬────────────────────┬────────────┐
│ 車隊        │ FP2 典型起始燃油   │ FP2 模擬圈數範圍   │ 對應正賽圈 │
├─────────────┼────────────────────┼────────────────────┼────────────┤
│ Red Bull    │ 65 kg              │ Lap 20-30          │ Lap 30-40  │
│ Ferrari     │ 70 kg              │ Lap 15-25          │ Lap 25-35  │
│ McLaren     │ 60 kg              │ Lap 25-35          │ Lap 35-45  │
│ Mercedes    │ 75 kg              │ Lap 10-20          │ Lap 20-30  │
│ ...         │ ...                │ ...                │ ...        │
└─────────────┴────────────────────┴────────────────────┴────────────┘
```

---

## 計算邏輯

### 1. FP2 燃油水平推算

**已知參數：**
- FP2 Session 總長度：60 分鐘
- 平均 Out Lap 時間：~2 分鐘
- Long Run 開始時間點（從 Session 開始算）

**推算公式：**
```
FP2_Current_Fuel = FP2_Start_Fuel - (FP2_Lap_Number × Fuel_Consumption)

其中：
- FP2_Start_Fuel：FP2 出場時的燃油量（需要估算）
- FP2_Lap_Number：在這個 Stint 的第幾圈
- Fuel_Consumption：每圈燃油消耗（約 1.6-1.8 kg/lap）
```

### 2. 正賽燃油水平計算

**已知參數：**
- Race Start Fuel：~110 kg
- Fuel Consumption：~1.65 kg/lap

**計算公式：**
```
Race_Current_Fuel = Race_Start_Fuel - (Race_Lap_Number × Fuel_Consumption)
                  = 110 - (Race_Lap × 1.65)
```

### 3. 燃油水平對應

**核心邏輯：相同燃油水平 = 相同車重 = 可比較的圈速**

```
當 FP2_Current_Fuel ≈ Race_Current_Fuel 時，圈速可直接比較

例如：
- FP2 Stint 開始燃油 65kg，跑到第 5 圈時燃油 = 65 - 5×1.65 = 56.75kg
- 正賽第 32 圈時燃油 = 110 - 32×1.65 = 57.2kg
- 兩者燃油接近，圈速可比較（需考慮賽道進化差異）
```

---

## 數據收集需求

### 每場比賽需要收集的數據

#### FP2 數據
| 欄位 | 說明 |
|------|------|
| Year | 年份 |
| Race | 賽事名稱 |
| Driver | 車手代碼 |
| Team | 車隊名稱 |
| Stint | Stint 編號 |
| Lap_Start | Stint 開始圈數 |
| Lap_End | Stint 結束圈數 |
| Stint_Length | Stint 長度（圈數） |
| Compound | 輪胎配方 |
| Avg_Lap_Time | 平均圈速（排除 outliers） |
| Degradation | 退化率（秒/圈） |
| Estimated_Start_Fuel | 估算起始燃油（kg） |

#### Race 數據
| 欄位 | 說明 |
|------|------|
| Year | 年份 |
| Race | 賽事名稱 |
| Driver | 車手代碼 |
| Team | 車隊名稱 |
| Stint | Stint 編號 |
| Lap_Start | Stint 開始圈數 |
| Lap_End | Stint 結束圈數 |
| Compound | 輪胎配方 |
| Avg_Lap_Time | 平均圈速（排除 SC/VSC） |
| Degradation | 退化率（秒/圈） |

---

## 分析步驟

### Phase 1: 數據收集（自動化）

```python
# 需要新增 CLI Function: 批次收集 FP2/Race Long Run 數據
# 建議 Function ID: 130

for race in RACES_2025:
    for session in ['FP2', 'R']:
        collect_long_run_data(year=2025, race=race, session=session)
        → 輸出 JSON: long_run_summary_2025_{race}_{session}.json
```

### Phase 2: 燃油水平估算

**估算 FP2 起始燃油的方法：**

1. **時間推算法**
   - 根據 Long Run 開始的 Session 時間點
   - 假設車隊在 FP2 開始時滿油 110kg
   - 減去 Out Lap + Installation Lap 消耗
   
2. **圈速對比法**（更準確）
   - 比較 FP2 Long Run 第一圈與正賽相同輪胎的圈速
   - 根據圈速差異反推燃油差異
   ```
   圈速差 = FP2_Lap_Time - Race_Lap_Time
   燃油差 = 圈速差 / Fuel_Effect
   ```

3. **車隊歷史模式法**
   - 分析該車隊過去的 FP2 模擬習慣
   - 建立車隊特定的燃油起始值

### Phase 3: 對應關係建立

```
對於每個 (車隊, 賽道) 組合：

1. 計算 FP2 Long Run 每圈的燃油水平
2. 計算正賽每圈的燃油水平
3. 找出 FP2 圈數 ↔ 正賽圈數的對應關係
4. 記錄圈速差異（考慮賽道進化）
```

### Phase 4: 統計分析

```
輸出報告：

1. 車隊 FP2 模擬習慣統計
   - 平均起始燃油
   - 平均 Stint 長度
   - 偏好模擬的正賽階段

2. 賽道特定分析
   - 不同賽道的 FP2/Race 圈速比例
   - 賽道進化幅度統計

3. 預測模型驗證
   - 使用前幾場比賽建立模型
   - 用後續比賽驗證預測準確度
```

---

## 實作計畫

### 新增功能

#### 1. CLI Function 130: Long Run 批次分析
```bash
python f1_analysis_modular_main.py -f 130 -y 2025 -s FP2
# 輸出: 2025 所有 FP2 的 Long Run 摘要

python f1_analysis_modular_main.py -f 130 -y 2025 -s R
# 輸出: 2025 所有正賽的 Long Run 摘要
```

#### 2. CLI Function 131: FP2/Race 對應分析
```bash
python f1_analysis_modular_main.py -f 131 -y 2025 -r "Abu Dhabi"
# 輸出: Abu Dhabi FP2 vs Race 對應表
```

#### 3. CLI Function 132: 車隊習慣分析
```bash
python f1_analysis_modular_main.py -f 132 -y 2025 --team "Red Bull"
# 輸出: Red Bull 2025 賽季 FP2 模擬習慣統計
```

#### 4. GUI 整合
- 在 Long Run Analysis 模組新增 "Race Correlation" 頁籤
- 顯示 FP2 ↔ Race 對應圖表
- 提供車隊選擇和燃油估算調整

---

## 預期輸出格式

### JSON 結構

```json
{
  "year": 2025,
  "race": "Abu Dhabi",
  "analysis_type": "fp2_race_correlation",
  "teams": {
    "Red Bull Racing": {
      "drivers": ["VER", "PER"],
      "fp2_analysis": {
        "typical_start_fuel_kg": 65,
        "long_run_stints": [
          {
            "driver": "VER",
            "stint": 3,
            "compound": "MEDIUM",
            "lap_range": [20, 30],
            "avg_lap_time": 89.5,
            "degradation": 0.045,
            "fuel_level_start_kg": 65,
            "fuel_level_end_kg": 48.5
          }
        ]
      },
      "race_correlation": {
        "fp2_lap_20": {
          "fp2_fuel_kg": 65,
          "equivalent_race_lap": 27,
          "race_fuel_kg": 65.5,
          "lap_time_diff": -0.3
        },
        "fp2_lap_25": {
          "fp2_fuel_kg": 56.75,
          "equivalent_race_lap": 32,
          "race_fuel_kg": 57.2,
          "lap_time_diff": -0.2
        }
      }
    }
  },
  "summary": {
    "avg_track_evolution": -0.25,
    "best_correlation_window": "Lap 25-35"
  }
}
```

---

## 時間估算

| 階段 | 任務 | 預估時間 |
|------|------|----------|
| Phase 1 | 設計數據結構 & JSON 格式 | 2 小時 |
| Phase 2 | 實作 CLI Function 130 (批次收集) | 4 小時 |
| Phase 3 | 實作 CLI Function 131 (對應分析) | 4 小時 |
| Phase 4 | 實作 CLI Function 132 (車隊統計) | 3 小時 |
| Phase 5 | GUI 整合 (Race Correlation 頁籤) | 6 小時 |
| Phase 6 | 測試 & 驗證 | 3 小時 |
| **總計** | | **22 小時** |

---

## 驗證方法

### 範例驗證：2025 Abu Dhabi

1. **FP2 數據**
   - VER Stint 3: Lap 20-30, MEDIUM, 平均 89.5s
   - 估算燃油: 65kg → 48.5kg

2. **Race 數據**
   - VER Stint 2: Lap 27-42, MEDIUM, 平均 89.8s
   - 燃油: 65.5kg → 40.8kg

3. **對應驗證**
   - FP2 Lap 25 (燃油 ~57kg) ≈ Race Lap 32 (燃油 ~57kg)
   - 預期圈速差: 0.2-0.3s (賽道進化 + 正賽節省輪胎)
   - 實際圈速差: 待驗證

---

## 下一步行動

1. **確認需求**：您同意這個設計嗎？有需要調整的地方嗎？
2. **選擇起點**：先從哪個 CLI Function 開始實作？
3. **數據驗證**：選擇一場比賽手動驗證計算邏輯

---

## 附錄：2025 賽季賽事列表

| # | 賽事 | 日期 | 圈數 |
|---|------|------|------|
| 1 | Bahrain | Mar 2 | 57 |
| 2 | Saudi Arabia | Mar 9 | 50 |
| 3 | Australia | Mar 23 | 58 |
| 4 | Japan | Apr 6 | 53 |
| 5 | China | Apr 20 | 56 |
| 6 | Miami | May 4 | 57 |
| 7 | Emilia Romagna | May 18 | 63 |
| 8 | Monaco | May 25 | 78 |
| 9 | Spain | Jun 1 | 66 |
| 10 | Canada | Jun 15 | 70 |
| 11 | Austria | Jun 29 | 71 |
| 12 | Great Britain | Jul 6 | 52 |
| 13 | Belgium | Jul 27 | 44 |
| 14 | Hungary | Aug 3 | 70 |
| 15 | Netherlands | Aug 31 | 72 |
| 16 | Italy | Sep 7 | 53 |
| 17 | Azerbaijan | Sep 21 | 51 |
| 18 | Singapore | Oct 5 | 62 |
| 19 | United States | Oct 19 | 56 |
| 20 | Mexico | Oct 26 | 71 |
| 21 | Brazil | Nov 9 | 71 |
| 22 | Las Vegas | Nov 22 | 50 |
| 23 | Qatar | Nov 30 | 57 |
| 24 | Abu Dhabi | Dec 7 | 58 |
