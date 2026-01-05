# Task: Long Run & Degradation Analysis Module

## 📋 任務概述

**模組名稱**: `long_run_analysis`  
**類型**: Historical Analysis (非 Live Timing)  
**目標**: 分析練習賽 (FP1/FP2/FP3) 的長里程測試數據，計算真實輪胎衰退率

**核心功能**:
1. 自動偵測疑似 Long Run (連續 4 圈以上)
2. 用戶手動選擇/調整分析圈數範圍
3. 計算 Track Evolution (混合模式：統計模型 + 參考車手)
4. 計算燃油校正後的真實衰退率 (True Degradation)
5. 每車手獨立設定起始油量

---

## 🔧 數據來源分析

### ⚠️ API-ONLY 模式政策 (2025-10-03)

根據 F1T 系統架構政策，**GUI 不能直接調用 FastF1**，必須遵循：
1. **數據獲取**: 僅允許通過 REST API (`refactored_api.py`) 
2. **本地讀取**: 可讀取已存在的 JSON 檔案 (`json/` 目錄)
3. **禁止直接調用**: 不可在 GUI 中執行 `fastf1.get_session()` 或啟動 CLI 進程

### 現有資源評估

#### 參考實現: Detailed Lap Analysis (Function 28)
**檔案**: `modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py`

**數據載入模式**:
```python
# ✅ 正確模式：繼承 UniversalDataLoader + API Worker
class driverLapAnalysisDataManager(UniversalDataLoader):
    def load_data(self, **kwargs) -> bool:
        # 1. API 優先
        if self._api_enabled:
            self._start_api_request(params)  # 通過 REST API 獲取
            return True
        
        # 2. 本地 JSON 回退
        json_files = self._search_json_files(**params)
        if json_files:
            return self._load_json_data(json_files[0])
        
        # 3. 錯誤處理
        self.load_error.emit("找不到數據，請使用 API")
        return False
```

**API 請求範例**:
```python
class DetailedLapAnalysisApiWorker(QThread):
    def run(self):
        endpoint = f"{self.base_url}/api/v2/analysis/execute"
        query_params = {
            "function_id": 28,  # CLI Function 28: 詳細圈速分析
            "year": 2025,
            "race": "Japan",
            "session": "FP2"
        }
        response = requests.post(endpoint, params=query_params)
```

#### 必要的數據欄位 (來自 Function 28)
- **基礎圈速**: `LapTime`, `LapNumber`, `Stint`, `Compound`
- **輪胎資訊**: `TyreLife`, `FreshTyre`, `TyreAge`
- **分段時間**: `Sector1Time`, `Sector2Time`, `Sector3Time`
- **標記**: `IsPersonalBest`, `IsAccurate`, `PitInTime`, `PitOutTime`

### 需要新增 CLI 功能嗎？

#### 選項 A：複用 Function 28 (推薦) ✅
- **優勢**: 
  - 已有完整實現，無需開發
  - 包含所有需要的圈速數據
  - 支援多車手、多 Stint
- **實現**: 
  ```python
  # Long Run Analysis 可直接使用 Function 28 的數據
  cli_function = "28"  # 複用詳細圈速分析
  api_endpoint = "/api/v2/analysis/execute"
  ```

#### 選項 B：新增 Function (不推薦) ❌
- **缺點**: 
  - 需要額外開發 CLI 邏輯
  - Function 28 已滿足需求
  - 違反 DRY 原則

### 結論

✅ **不需要新增 CLI 功能**，Long Run Analysis 應：
1. **繼承 `UniversalDataLoader`** (基礎架構)
2. **複用 Function 28 API** (圈速數據來源)
3. **讀取現有資料庫** (燃油/衰退係數)

**數據來源清單**:

| 資源 | 路徑 | 用途 |
|------|------|------|
| **圈速數據 (API)** | `Function 28` → `/api/v2/analysis/execute` | 所有 FP 圈速、Stint、胎種 |
| **燃油係數資料庫** | `config/fuel_coefficients_database.json` | 各賽道每圈油耗 (kg/lap)、燃油效應係數 (s/kg) |
| **輪胎衰退資料庫** | `config/tire_degradation_database.json` | 各賽道各胎種衰退參數 (參考值) |

**參考檔案**:
- 數據載入: `modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py` (Lines 117-250)
- API Worker: `modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py` (Lines 26-115)
- CLI 實現: `CLI_modules/cli/core/function_mapper.py` (Function 28, Line 4490)

---

## 🎨 ASCII 視覺化草圖

### Tab 1: Long Run 選擇器

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Long Run Selector - 2025 Japanese Grand Prix FP2                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ 篩選條件 ──────────────────────────────────────────────────────────────────┐ │
│  │  最少連續圈數: [4]  │  排除 Out/In Lap: [✓]  │  [自動偵測 Long Run]        │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 偵測到的 Long Run Stints ─────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  [✓] VER  │ Stint 2  │ Lap 8-19  (12 laps) │ MEDIUM │ 疑似 Long Run ★ [編輯]│ │
│  │  [✓] LEC  │ Stint 2  │ Lap 10-22 (13 laps) │ HARD   │ 疑似 Long Run ★ [編輯]│ │
│  │  [ ] NOR  │ Stint 1  │ Lap 3-8   (6 laps)  │ SOFT   │ Quali Sim?      [編輯]│ │
│  │  [✓] HAM  │ Stint 2  │ Lap 12-23 (12 laps) │ MEDIUM │ 疑似 Long Run ★ [編輯]│ │
│  │  [ ] SAI  │ Stint 3  │ Lap 25-29 (5 laps)  │ SOFT   │ 短 Stint        [編輯]│ │
│  │  [✓] RUS  │ Stint 2  │ Lap 9-20  (12 laps) │ HARD   │ 疑似 Long Run ★ [編輯]│ │
│  │                                                                             │ │
│  │  ★ = 系統自動偵測為疑似 Long Run (連續 ≥4 圈 + 圈速穩定)                    │ │
│  │  點擊 [編輯] 開啟互動式圈速選擇器                                           │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│                                            [下一步: 燃油設定 →]                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 1.5: 互動式圈速選擇器 (點擊 [編輯] 後彈出)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Interactive Lap Selector - VER (FP2)                                  [X 關閉] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ 圈速曲線圖 (可點選) ──────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  Lap Time                                          圖例:                    │ │
│  │  (秒)                                              ● = 正常圈               │ │
│  │                                                    ○ = Out/In Lap (排除)    │ │
│  │  93.5  ○                                          ░ = 背景區 (未選)        │ │
│  │  93.0    ○                                        █ = 選中區 (Long Run)    │ │
│  │  92.5                                                                       │ │
│  │  92.0      ●░░░░░░█████████████░░░●                                        │ │
│  │  91.8        ●░░█████████████████░●  ● ●                                   │ │
│  │  91.6          ●███████████████████●    ●                                  │ │
│  │  91.4          ██●█●█●█●█●█●█●█●██        ●                                │ │
│  │  91.2          ███████████████████                                         │ │
│  │  91.0          ███████████████████              [← 拖曳選擇範圍 →]         │ │
│  │       └────────────────────────────────────────────                        │ │
│  │          1  3  5  7  9 11 13 15 17 19 21 23 25 27 29                       │ │
│  │                   Lap Number                                                │ │
│  │                                                                             │ │
│  │  💡 操作方式:                                                               │ │
│  │  • 點擊單個圈點 = 切換選中狀態                                              │ │
│  │  • 拖曳滑鼠 = 框選連續圈數範圍                                              │ │
│  │  • 右鍵點擊 = 清除選中狀態                                                  │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 圈速明細表 ────────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  Lap │ Time    │ Stint │ Compound │ TyreLife │ Sector1 │ Sector2 │ Sector3│ 選│ │
│  │  ────┼─────────┼───────┼──────────┼──────────┼─────────┼─────────┼────────┼──│ │
│  │   1  │ 93.526  │ 1     │ SOFT     │ 1        │ 32.145  │ 35.821  │ 25.560 │  │ │
│  │   2  │ 93.123  │ 1     │ SOFT     │ 2        │ 31.984  │ 35.602  │ 25.537 │  │ │
│  │  ... │ ......  │ ..... │ ........ │ ........ │ ....... │ ....... │ ...... │  │ │
│  │   8  │ 91.856 ◄│ 2     │ MEDIUM   │ 1        │ 31.523  │ 35.112  │ 25.221 │✓ │ │
│  │   9  │ 91.762  │ 2     │ MEDIUM   │ 2        │ 31.456  │ 35.089  │ 25.217 │✓ │ │
│  │  10  │ 91.698  │ 2     │ MEDIUM   │ 3        │ 31.412  │ 35.067  │ 25.219 │✓ │ │
│  │  ...                                                                        │ │
│  │  19  │ 91.995 ◄│ 2     │ MEDIUM   │ 12       │ 31.678  │ 35.213  │ 25.104 │✓ │ │
│  │  20  │ 92.456  │ 2     │ MEDIUM   │ 13       │ 31.823  │ 35.345  │ 25.288 │  │ │
│  │  ...                                                                        │ │
│  │                                                                             │ │
│  │  ◄ = 當前選擇範圍的起點/終點                                                │ │
│  │  ✓ = 已選為 Long Run 分析範圍                                               │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 當前選擇摘要 ─────────────────────────────────────────────────────────────┐ │
│  │  選中圈數: Lap 8-19 (共 12 圈)  │  胎種: MEDIUM  │  平均圈速: 91.812 s      │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  [套用選擇]  [重設為自動偵測]  [取消]                                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 2: 燃油設定

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Fuel Settings - 燃油校正參數                                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ 賽道預設值 (Suzuka) ───────────────────────────────────────────────────────┐ │
│  │  每圈油耗: 1.65 kg/lap  │  燃油效應: 0.030 s/kg  │  資料來源: 資料庫        │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 各車手燃油設定 ────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  車手   │ 起始油量(kg) │ 每圈消耗(kg) │ 燃油效應(s/kg) │ 套用賽道預設      │ │
│  │  ───────┼──────────────┼──────────────┼────────────────┼─────────────────── │ │
│  │  VER    │ [85]         │ [1.65]       │ [0.030]        │ [✓]               │ │
│  │  LEC    │ [90]         │ [1.70]       │ [0.030]        │ [ ]               │ │
│  │  HAM    │ [80]         │ [1.65]       │ [0.030]        │ [✓]               │ │
│  │  RUS    │ [85]         │ [1.65]       │ [0.030]        │ [✓]               │ │
│  │                                                                             │ │
│  │  💡 提示: FP 練習賽通常油量 60-100 kg，正賽起跑約 110 kg                     │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  [← 返回選擇器]                              [下一步: Track Evolution 設定 →]   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 3: Track Evolution 設定

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Track Evolution Settings - 賽道條件變化設定                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ 計算方法選擇 ─────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  (●) 統計模型 - 選中圈數中位數趨勢                                          │ │
│  │      使用所有車手在選中 Long Run 範圍內的圈速計算賽道條件變化               │ │
│  │      ⚠️ 樣本來源: 僅計算已勾選車手的 Long Run 圈數 (排除其他 Stint)        │ │
│  │      ⚠️ 車手數量少於 5 位時統計可能不穩定                                   │ │
│  │                                                                             │ │
│  │  ( ) 參考車手 - 指定 Baseline                                               │ │
│  │      選擇剛換新胎的車手作為無衰退基準                                        │ │
│  │      參考車手: [NOR ▼] (Stint 3, SOFT, Fresh)                              │ │
│  │      ⚠️ 參考車手必須在相同時間段內完成圈速                                  │ │
│  │                                                                             │ │
│  │  ( ) 混合模式 - 統計 + 參考車手加權                                          │ │
│  │      統計權重: [70]%  │  參考車手權重: [30]%                                │ │
│  │      結合兩種方法的優勢，提高 Track Evolution 估算準確性                     │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 預覽: Track Evolution 曲線 ───────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  Time │                                                                     │ │
│  │  Δ(s) │    ╲                                                               │ │
│  │  +0.0 │─────●────────────────────────────────────                          │ │
│  │  -0.2 │      ╲●                                                            │ │
│  │  -0.4 │        ╲●                                                          │ │
│  │  -0.6 │          ╲●●                                                       │ │
│  │  -0.8 │             ╲●●●                                                   │ │
│  │  -1.0 │                 ╲●●●●──────────── (賽道變快)                        │ │
│  │       └──────────────────────────────────────────────                      │ │
│  │          Lap 8   10   12   14   16   18   20                               │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  [← 返回燃油設定]                                     [執行分析 →]              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 4: 衰退分析結果

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Degradation Analysis Results - 2025 Japanese Grand Prix FP2                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ 衰退率摘要表 ─────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  車手 │ 胎種   │ 圈數  │ Raw Deg │ Track Evo │ Fuel Adj │ True Deg │ Deg/Lap│ │
│  │  ─────┼────────┼───────┼─────────┼───────────┼──────────┼──────────┼────────│ │
│  │  VER  │ MEDIUM │ 12    │ +0.84s  │ -0.36s    │ -0.59s   │ +0.89s   │ +0.074 │ │
│  │  LEC  │ HARD   │ 13    │ +0.52s  │ -0.39s    │ -0.66s   │ +0.57s   │ +0.044 │ │
│  │  HAM  │ MEDIUM │ 12    │ +0.96s  │ -0.36s    │ -0.59s   │ +1.01s   │ +0.084 │ │
│  │  RUS  │ HARD   │ 12    │ +0.48s  │ -0.36s    │ -0.59s   │ +0.53s   │ +0.044 │ │
│  │                                                                             │ │
│  │  📊 欄位說明:                                                               │ │
│  │  • Raw Deg = 最後圈 - 第一圈 (原始衰退)                                     │ │
│  │  • Track Evo = 賽道條件變化量 (負值 = 賽道變快)                             │ │
│  │  • Fuel Adj = 燃油校正量 (圈數 × 每圈油耗 × 燃油效應)                       │ │
│  │  • True Deg = Raw Deg - Track Evo - Fuel Adj (真實輪胎衰退)                 │ │
│  │  • Deg/Lap = True Deg / 圈數 (每圈衰退率)                                   │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 衰退曲線圖 ───────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  ┌─ 顯示車手選擇 ────────────────────────────────────────────────────────┐  │ │
│  │  │  [✓] VER  [✓] LEC  [ ] NOR  [✓] HAM  [ ] SAI  [✓] RUS  [ ] PER  [ ] ALO │  │ │
│  │  │  [ ] STR  [ ] GAS  [ ] TSU  [ ] BOT  [ ] ZHO  [ ] MAG  [ ] HUL  [ ] RIC │  │ │
│  │  │  [ ] ALB  [ ] OCO  [ ] SAR  [ ] BEA  [ ] LAW                            │  │ │
│  │  │                                              [全選] [清除] [僅前 5 名]   │  │ │
│  │  └───────────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                             │ │
│  │  Lap  │                         圖例:                                       │ │
│  │  Time │                         ━ VER                                     │ │
│  │  (s)  │                         ┅ PER                                     │ │
│  │       │                         ━ LEC                                     │ │
│  │ 92.0  │  ━                      ┅ SAI                                     │ │
│  │ 91.8  │   ━━                    ━ HAM                                     │ │
│  │ 91.6  │    ━━  ━                ┅ RUS                                     │ │
│  │ 91.4  │  ┅┅ ━━  ━━                                                         │ │
│  │ 91.2  │   ┅┅  ┅┅ ━━            💡 線條顏色 = 車隊顏色 (動態讀取)           │ │
│  │ 91.0  │    ┅┅  ┅┅  ┅┅━━        💡 虛線 = 同車隊第二車手                    │ │
│  │ 90.8  │         ┅┅  ┅┅ ━━                                                  │ │
│  │ 90.6  │              ┅┅  ━━                                                │ │
│  │       └──────────────────────────────────────────                          │ │
│  │          Lap 1   3    5    7    9   11   13                                │ │
│  │                                                                             │ │
│  │  💡 此圖為燃油校正後圈速 (Fuel-Corrected Lap Time)                          │ │
│  │     斜率 = 真實輪胎衰退率                                                   │ │
│  │  💡 建議顯示 3-6 位車手以避免圖表過於擁擠                                   │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  [匯出 CSV]  [匯出圖表]  [返回選擇器]                                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 5: 胎種比較 (Compound Comparison)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Compound Comparison - 胎種衰退比較                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ 各胎種平均衰退率 ─────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │       SOFT          MEDIUM          HARD                                    │ │
│  │       ┌───┐         ┌───┐          ┌───┐                                   │ │
│  │       │   │         │   │          │   │                                   │ │
│  │       │   │         │   │          │   │                                   │ │
│  │       │░░░│ 0.12    │▓▓▓│ 0.079    │███│ 0.044    (s/lap)                  │ │
│  │       │░░░│         │▓▓▓│          │███│                                   │ │
│  │       │░░░│         │▓▓▓│          │███│                                   │ │
│  │       └───┘         └───┘          └───┘                                   │ │
│  │                                                                             │ │
│  │   樣本數: 2          樣本數: 4       樣本數: 3                               │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ 策略建議 ─────────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  📌 根據 FP2 Long Run 數據:                                                 │ │
│  │                                                                             │ │
│  │  • SOFT:   衰退快 (+0.12 s/lap)，建議 Stint ≤ 15 圈                         │ │
│  │  • MEDIUM: 中等衰退 (+0.079 s/lap)，可持續 20-25 圈                         │ │
│  │  • HARD:   衰退慢 (+0.044 s/lap)，可持續 30+ 圈                             │ │
│  │                                                                             │ │
│  │  ⚠️ 注意: FP 數據可能與正賽不同 (燃油量、賽道溫度)                          │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 計算公式

### 1. 燃油校正 (Fuel Correction)

```
已消耗燃油 = 圈數 × 每圈油耗 (kg)
燃油效應 = 已消耗燃油 × 燃油效應係數 (s/kg)
燃油校正圈速 = 實際圈速 + 燃油效應
```

**範例** (Suzuka, 第 10 圈):
```
已消耗燃油 = 10 × 1.65 = 16.5 kg
燃油效應 = 16.5 × 0.030 = 0.495 s (車變輕了這麼多)
燃油校正圈速 = 91.2 + 0.495 = 91.695 s
```

### 2. Track Evolution 計算 (統計模型)

```python
# 方法: 選中 Long Run 圈數的中位數趨勢
def calculate_track_evolution(selected_drivers_laps, long_run_lap_range):
    """
    計算賽道條件變化
    
    Args:
        selected_drivers_laps: 所有已勾選車手的圈速數據
        long_run_lap_range: Long Run 圈數範圍 (例如: Lap 8-19)
    
    Returns:
        track_evo: 各圈相對於基準圈的時間變化 (負值 = 賽道變快)
    """
    # 步驟 1: 篩選只包含 Long Run 範圍內的圈速
    filtered_laps = selected_drivers_laps[
        (selected_drivers_laps['LapNumber'] >= long_run_lap_range[0]) &
        (selected_drivers_laps['LapNumber'] <= long_run_lap_range[1])
    ]
    
    # 步驟 2: 按圈數分組，計算中位數圈速
    grouped = filtered_laps.groupby('LapNumber')
    median_times = grouped['LapTime'].median()
    
    # 步驟 3: 相對於 Long Run 第一圈計算變化
    baseline = median_times.iloc[0]
    track_evo = median_times - baseline
    
    return track_evo  # 負值 = 賽道變快
```

**範例** (Suzuka FP2):
```python
# 場景: 4 位車手都選中 Lap 8-19 作為 Long Run
selected_drivers = ['VER', 'LEC', 'HAM', 'RUS']
long_run_range = (8, 19)

# 只計算這 4 位車手在 Lap 8-19 的圈速
# 排除其他車手的 Quali Sim、短 Stint 等
track_evo = calculate_track_evolution(data, long_run_range)

# 結果: Lap 8 = 0.0s (基準), Lap 19 = -0.8s (賽道變快)
```

### 3. 真實衰退率 (True Degradation)

```
Raw Degradation = 最後圈時間 - 第一圈時間
True Degradation = Raw Deg - Track Evolution - Fuel Correction
Degradation per Lap = True Degradation / 圈數
```

---

## 🗂️ 檔案結構

```
modules/gui/long_run_analysis/
├── __init__.py
├── long_run_mdi.py              # MDI 主視窗
├── long_run_data_loader.py      # 數據載入器 (繼承 UniversalDataLoader)
├── long_run_calculator.py       # 衰退率計算引擎
├── widgets/
│   ├── __init__.py
│   ├── stint_selector.py        # Tab 1: Long Run 選擇器
│   ├── lap_picker_dialog.py     # Tab 1.5: 互動式圈速選擇器 (彈出對話框)
│   ├── lap_chart_widget.py      # 可點選的圈速曲線圖 (支援拖曳選擇)
│   ├── lap_table_widget.py      # 圈速明細表 (支援點擊勾選)
│   ├── fuel_settings.py         # Tab 2: 燃油設定
│   ├── track_evolution.py       # Tab 3: Track Evolution 設定
│   ├── degradation_results.py   # Tab 4: 分析結果表格 + 衰退曲線圖
│   ├── degradation_chart.py     # 衰退曲線圖組件 (車手選擇 + 車隊顏色)
│   └── compound_comparison.py   # Tab 5: 胎種比較圖
└── utils/
    ├── __init__.py
    ├── fuel_database.py         # 讀取燃油係數資料庫
    └── team_color_helper.py     # 車隊顏色處理 (參考 Throttle 實現)
```

---

## ✅ 實施檢查清單

### 階段 1: 核心引擎 (無 GUI)

- [ ] 建立 `long_run_calculator.py`
  - [ ] 載入 Function 28 API 數據 (所有車手圈速)
  - [ ] 自動偵測 Long Run (≥4 連續圈)
  - [ ] 燃油校正計算
  - [ ] Track Evolution 計算 (統計模型 - 僅使用選中圈數範圍)
  - [ ] True Degradation 計算
- [ ] 單元測試: 使用 2024 Japanese GP FP2 驗證

### 階段 2: GUI 實現

- [ ] `stint_selector.py` - Long Run 選擇器主面板
  - [ ] 自動偵測 Long Run 列表顯示
  - [ ] 每行添加 [編輯] 按鈕
  - [ ] 勾選框狀態管理
- [ ] `lap_picker_dialog.py` - 互動式圈速選擇器 (彈出對話框)
  - [ ] 整合圈速曲線圖和明細表
  - [ ] 拖曳選擇範圍邏輯
  - [ ] 當前選擇摘要顯示
- [ ] `lap_chart_widget.py` - 可點選的圈速曲線圖
  - [ ] matplotlib 或 pyqtgraph 繪圖
  - [ ] 滑鼠點擊事件處理 (單圈選擇)
  - [ ] 滑鼠拖曳事件處理 (範圍選擇)
  - [ ] 視覺化選中狀態 (背景色區分)
- [ ] `lap_table_widget.py` - 圈速明細表
  - [ ] QTableWidget 顯示所有圈速數據
  - [ ] 勾選框欄位 (與圖表同步)
  - [ ] 點擊行切換選中狀態
- [ ] `fuel_settings.py` - 燃油參數設定
- [ ] `track_evolution.py` - Track Evo 方法選擇
- [ ] `degradation_results.py` - 結果表格顯示
- [ ] `degradation_chart.py` - 衰退曲線圖組件
  - [ ] 車手選擇器 (複選框)
  - [ ] 車隊顏色動態讀取 (參考 Throttle Lap 實現)
  - [ ] 同車隊第二車手使用虛線
  - [ ] 圖例顯示 (車手 + 車隊 + 線條樣式)
  - [ ] 建議顯示數量警告 (超過 6 位車手)
- [ ] `compound_comparison.py` - 胎種比較

### 階段 3: 整合

- [ ] `long_run_mdi.py` - MDI 主視窗整合
- [ ] 在 `function_tree_builder.py` 添加選單項目
- [ ] 匯出功能 (CSV, PNG)

### 階段 4: 互動式選擇器測試

- [ ] 測試拖曳選擇功能
- [ ] 測試圖表與表格同步
- [ ] 測試 Out/In Lap 自動排除
- [ ] 測試選擇範圍驗證 (最少 4 圈)

---

## 🎮 互動式圈速選擇器 - 技術規格

### 功能需求

1. **圖表互動**:
   - 左鍵點擊單個圈點 → 切換選中狀態
   - 左鍵拖曳 → 框選連續範圍
   - 右鍵點擊 → 清除所有選中
   - Ctrl+點擊 → 多段不連續選擇 (可選功能)

2. **表格同步**:
   - 圖表選擇 → 表格勾選框自動更新
   - 表格勾選 → 圖表視覺化自動更新
   - 雙向同步無延遲

3. **數據驗證**:
   - 最少選擇 4 圈 (可配置)
   - 自動排除 Out/In Lap (可選)
   - 提示不符合 Long Run 標準的選擇

### 視覺化設計

**圖表顏色編碼**:
```python
# 圈速選擇器顏色
colors = {
    'selected': '#4CAF50',        # 綠色 - 選中的圈
    'unselected': '#E0E0E0',      # 灰色 - 未選中的圈
    'outlap': '#FFC107',          # 橘色 - Out Lap (自動排除)
    'inlap': '#FF9800',           # 深橘 - In Lap (自動排除)
    'invalid': '#F44336',         # 紅色 - 無效圈速 (黃旗等)
    'selection_bg': 'rgba(76, 175, 80, 0.1)'  # 半透明綠 - 選擇範圍背景
}

# 衰退曲線圖 - 車隊顏色 (參考 Throttle Lap 實現)
# 檔案參考: modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py
def get_driver_color_and_style(driver_code: str, team_name: str) -> Tuple[str, str]:
    """
    獲取車手顏色和線條樣式
    
    Returns:
        (color, linestyle) - 顏色使用車隊色，同車隊第二車手使用虛線
    """
    # 讀取車隊顏色配置
    team_color = get_team_color(team_name)  # 動態讀取
    
    # 判斷是否為車隊第二車手
    is_second_driver = is_team_second_driver(driver_code, team_name)
    linestyle = '--' if is_second_driver else '-'  # 虛線 or 實線
    
    return team_color, linestyle
```

**滑鼠游標**:
- 預設: 十字準心 (精確點選)
- 拖曳中: 抓取手勢
- 不可選區域 (Out/In Lap): 禁止符號

### 數據結構

```python
class LapSelectionState:
    """圈速選擇狀態管理"""
    def __init__(self):
        self.selected_laps: Set[int] = set()  # 選中的圈數集合
        self.all_laps: List[LapData] = []     # 所有圈速數據
        self.excluded_laps: Set[int] = set()  # 自動排除的圈數
        
    def toggle_lap(self, lap_number: int):
        """切換單圈選中狀態"""
        pass
        
    def select_range(self, start_lap: int, end_lap: int):
        """選擇連續範圍"""
        pass
        
    def is_valid_selection(self) -> Tuple[bool, str]:
        """驗證當前選擇是否符合 Long Run 標準"""
        if len(self.selected_laps) < 4:
            return False, "最少需要 4 圈"
        # 檢查是否連續
        sorted_laps = sorted(self.selected_laps)
        for i in range(len(sorted_laps) - 1):
            if sorted_laps[i+1] - sorted_laps[i] != 1:
                return False, "Long Run 必須是連續圈數"
        return True, "有效的 Long Run 選擇"
```

### 事件處理流程

```
用戶操作 → 事件捕捉 → 狀態更新 → 視覺化同步 → 驗證檢查
    │                                       │
    └──────────── 錯誤提示 ←────────────────┘
```

---

## 🎨 衰退曲線圖 - 車隊顏色處理

### 參考實現
**檔案**: `modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py`

### 實現邏輯

```python
class DegradationChartWidget:
    """衰退曲線圖 - 支援車隊顏色和虛線區分"""
    
    def __init__(self):
        self.selected_drivers = []  # 用戶選中的車手列表
        self.max_recommended_drivers = 6  # 建議最多顯示數量
    
    def plot_degradation_curves(self, data: Dict[str, Any]):
        """繪製衰退曲線"""
        if len(self.selected_drivers) > self.max_recommended_drivers:
            self._show_warning(f"顯示 {len(self.selected_drivers)} 位車手可能導致圖表擁擠")
        
        for driver_code in self.selected_drivers:
            # 獲取車隊資訊
            team_name = self._get_driver_team(driver_code, data)
            
            # 獲取車隊顏色和線條樣式
            color, linestyle = self._get_driver_style(driver_code, team_name)
            
            # 繪製曲線
            lap_numbers = data[driver_code]['lap_numbers']
            corrected_times = data[driver_code]['fuel_corrected_times']
            
            self.ax.plot(
                lap_numbers, 
                corrected_times,
                color=color,
                linestyle=linestyle,
                linewidth=2,
                label=driver_code  # 只顯示車手代碼，顏色自動代表車隊
            )
    
    def _get_driver_style(self, driver_code: str, team_name: str) -> Tuple[str, str]:
        """獲取車手顏色和線條樣式"""
        # 讀取車隊顏色 (參考 Throttle Lap 實現)
        team_color = self._get_team_color(team_name)
        
        # 判斷是否為車隊第二車手
        team_drivers = self._get_team_drivers(team_name)
        is_second_driver = (len(team_drivers) > 1 and driver_code == team_drivers[1])
        
        linestyle = '--' if is_second_driver else '-'
        return team_color, linestyle
    
    def _get_team_color(self, team_name: str) -> str:
        """讀取車隊顏色配置"""
        # 從 dynamic_team_mapping 或配置檔案讀取
        # 參考: modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py
        pass
```

### 車手選擇器 UI

```python
class DriverSelectorWidget(QWidget):
    """車手選擇器 - 支援複選"""
    
    driver_selection_changed = pyqtSignal(list)  # 選中車手列表變更信號
    
    def __init__(self, available_drivers: List[str]):
        super().__init__()
        self.checkboxes = {}
        self._create_ui(available_drivers)
    
    def _create_ui(self, drivers: List[str]):
        """創建複選框網格"""
        layout = QGridLayout()
        
        # 每行顯示 8 位車手
        for i, driver in enumerate(drivers):
            row, col = divmod(i, 8)
            checkbox = QCheckBox(driver)
            checkbox.stateChanged.connect(self._on_selection_changed)
            self.checkboxes[driver] = checkbox
            layout.addWidget(checkbox, row, col)
        
        # 快速操作按鈕
        btn_layout = QHBoxLayout()
        btn_all = QPushButton(tr("long_run", "Select All"))
        btn_clear = QPushButton(tr("long_run", "Clear"))
        btn_top5 = QPushButton(tr("long_run", "Top 5 Only"))
        
        btn_all.clicked.connect(self._select_all)
        btn_clear.clicked.connect(self._clear_all)
        btn_top5.clicked.connect(self._select_top5)
        
        btn_layout.addWidget(btn_all)
        btn_layout.addWidget(btn_clear)
        btn_layout.addWidget(btn_top5)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
```

---

## ❓ 待確認事項

1. **自動偵測條件**: 連續 4 圈以上 + 圈速穩定 (標準差 < 0.5s)？
2. **Track Evolution 預設**: 統計模型為預設，參考車手為可選？
3. **互動式選擇器**:
   - 圖表庫選擇: matplotlib (靜態) 還是 pyqtgraph (動態互動性更好)？
   - 拖曳選擇: 支援多段不連續選擇？還是限制單一連續範圍？
   - 驗證規則: 最少選擇 4 圈？是否強制連續？
4. **位置**: 放在 Historical Analysis 下的哪個子選單？

---

## 📅 預估工時

| 階段 | 工時估算 |
|------|----------|
| 階段 1: 核心引擎 | 4-6 小時 |
| 階段 2: GUI 實現 | 8-10 小時 (+2 小時互動式選擇器) |
| 階段 3: 整合測試 | 2-3 小時 |
| 階段 4: 互動式選擇器測試 | 1-2 小時 |
| **總計** | **15-21 小時** |

---

請確認以上內容，我將開始實施！
