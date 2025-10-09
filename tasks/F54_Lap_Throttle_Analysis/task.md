# Task: Function 54 – Lap Throttle Ratio Analysis

**建立日期**: 2025-10-07  
**狀態**: � 進行中  
**負責人**: _TBD_  
**關聯功能**: CLI Function 54、GUI 油門箱型圖、GUI 油門折線圖  
**依賴專案**: FastF1 / OpenF1 API、既有 UniversalDataLoader 架構、UniversalChartWidget

---

## 🎯 任務概要

實作並整合新的 Lap Throttle Ratio 分析功能：
1. **CLI 功能 (Function 54)** – 針對指定賽事計算所有車手的逐圈油門指標。  
2. **API / JSON 輸出** – 以標準化結構輸出結果，供 GUI 讀取。  
3. **GUI 模組** – 建立兩個視圖：
   - 全車手油門箱型圖 (Box Plot)。
   - 單車手油門折線圖 + 圈速同步視窗。

任務需符合 API-ONLY 政策，禁止 GUI 直接呼叫 CLI 進程。

---

## 📦 交付物

| 類別 | 交付內容 |
|------|----------|
| CLI | `CLI_modules/cli/analyzer/driver_throttle_ratio.py` (新模組)、`function_mapper.py` 內 `54` 映射、JSON 導出邏輯、單元測試 |
| API | `refactored_api.py` 中 Function 54 支援、`tests/` 內 API 測試 (POST /analyze) |
| JSON 資料 | `throttle_ratio_{year}_{race}_{session}_[driver].json` – 包含 Metadata、Drivers、Laps、油門/圈速相關欄位 |
| GUI – Box Plot | `modules/gui/throttle_analysis/throttle_boxplot_window.py`、對應 DataLoader、互動欄位、i18n 支援 |
| GUI – Line Chart | `modules/gui/throttle_analysis/throttle_linechart_window.py`、雙 MDI 視窗同步、tooltip 實作 |
| 文件 | CLI 規格 (`docs/develop task/CLI develop task/F54...` 更新)、GUI 規劃 (`docs/develop task/GUI Develop task/...`)、使用者說明更新 |
| 測試 | `tests/test_throttle_ratio_calculations.py`、`tests/test_throttle_ratio_schema.py`、GUI 手動測試清單 |

---

## ✅ 功能需求

### CLI 計算指標
- `Lap Throttle Percentage`: 油門 ≥ 門檻 (`--threshold`, 預設 0.9) 的時間占比。
- `Average Throttle`: 整圈油門平均值。
- `Throttle Variability Index`: 標準差或 MAD (需於文件中標註採用模式)。
- `Full Throttle Duration (秒)`: 油門 ≥ 門檻的累計秒數。 _※ GUI 主要使用欄位_
- `Coasting Duration (秒)`: 油門 ≤ `--coast-threshold` 的累計秒數 (預設 0.2)。
- 其他欄位：`lap_time_seconds`, `compound`, `stint`, `drs_usage_ratio`, `ers_deploy_ratio`, `speed_avg_kmh`, `top_speed_kmh`, `pit_status`, `data_status`。

### CLI 執行模式
- 支援 `-d` 選項限制單一車手。
- JSON 應含 `metadata` + `analysis.drivers[].laps[]`。
- 缺失 Telemetry 時：在 `laps[]` 中以 `data_status = "insufficient"` 標記，並避免 GUI 崩潰。

### GUI 視圖需求
- **箱型圖 (全車手)**：
  - 顯示 `full_throttle_duration_s` 分佈；車手顏色沿用既有車隊色。
  - 欄位篩選：車手多選、輪胎群組、排序方式。
  - Tooltip 顯示圈號、圈速、輪胎、油門比、DRS/ERS 資訊。
- **折線圖 (單車手)**：
  - 主要視窗：Lap-by-Lap `full_throttle_duration_s` 折線/散點。
  - 次視窗：圈速折線 (可切換秒數或 Δs)。
  - 兩視窗透過 signal bus 同步 hover/縮放；tooltip 顯示輪胎、DRS、ERS、Pit。
  - 提供匯出 (PNG/SVG、CSV)、閾值顯示、Pit/SafetyCar 筛選。

---

## 🔗 API-ONLY 合規事項
- GUI 僅能透過 `UniversalDataLoader` → REST API (`/analyze`) 或已存在 JSON。  
- CLI 自動生成步驟必須回傳错误並提示使用者手動生成。  
- 相關 log 記錄需遵守現有的 debug/_info 風格。

---

## 🧪 測試計畫

1. **單元測試**
   - `driver_throttle_ratio.py`：
     - 最基本圈的油門積分結果與手算相符。
     - 門檻(`--threshold`) 和滑行閾值變化後輸出正確更新。
     - 缺失資料 (`NaN`/空 Telemetry) 時回傳 `data_status`。
   - JSON Schema 驗證：所有欄位存在、類型正確。

2. **整合測試**
   - CLI → JSON 寫檔 → GUI 讀檔流程。
   - API `/analyze` 回應 200，資料結構符合 GUI 需求。
   - GUI 測試腳本：
     - 篩選/排序正確。
     - Tooltip 顯示內容完整。
     - 雙視窗同步無顯著延遲。

3. **手動驗證**
   - 選定賽事 (例如 2024 日本站 R)：比對 FastF1 Telemetry 片段，人工驗證 2-3 圈結果。
   - 可視化檢查：確認箱型圖/折線圖展示合理。

---

## 📝 驗收條件
- [ ] CLI 功能能在指定賽事成功執行並輸出 JSON，五項指標皆有值或合理標記缺失。  
- [ ] CLI 單元測試與整合測試全部通過。  
- [ ] API `/analyze` 支援 `function_id=54` 並通過測試。  
- [ ] GUI 箱型圖與折線圖可於 Universal MDI 中載入、操作 (篩選、匯出、tooltip)。  
- [ ] GUI 視圖不可直接呼叫 CLI；資料缺失時提供友好提示。  
- [ ] 文件與 README/使用者指南已更新，包含功能用途、操作步驟、限制。  
- [ ] QA 手動測試簽核完成（附測試紀錄）。

---

## 📌 里程碑與時間

| 里程碑 | 預估日期 | 備註 |
|--------|----------|------|
| CLI 計算模組完成 | 2025-10-12 | 含單元測試、JSON 輸出 |
| API 整合就緒 | 2025-10-14 | `/analyze` 更新、pytest 就緒 |
| GUI 箱型圖視圖完成 | 2025-10-18 | 功能 + 控制面板 + 匯出 |
| GUI 折線圖雙視窗完成 | 2025-10-22 | 同步 + tooltip |
| 整體測試與文件收尾 | 2025-10-25 | 測試報告、文件更新 |

> 實際日程視資源安排調整，更新請記錄於此檔案。

---

## 🤝 協作與依賴
- **CLI 團隊**：提供 Telemetry 欄位定義與 FastF1 資料來源最佳實踐。
- **GUI 團隊**：確認 UniversalChartWidget 支援雙視窗同步；評估性能優化。
- **QA / 測試**：制定測試腳本、指標驗證流程。
- **文件維護**：更新使用者指南與內部訓練教材。

---

## 📚 參考資料
- `docs/develop task/CLI develop task/F54_AllDriver_Lap_Throttle_Analysis_開發文件.md`
- `docs/develop task/GUI Develop task/Throttle_Boxplot_AllDrivers_開發文件.md`
- `docs/develop task/GUI Develop task/Throttle_LineChart_SingleDriver_開發文件.md`
- FastF1 Telemetry API 參考文件
- UniversalDataLoader / UniversalChartWidget 開發指南

---

> 更新紀錄：
> - 2025-10-08：Function 54 修正：`_calculate_lap_metrics_from_telemetry` 現在保留外層圈號（telemetry 無 `LapNumber` 時不再回落到 0），新增 `lap_number` 參數並補齊單元測試；同日完成單車手油門折線圖「圈數為 X 軸」與車手下拉選擇功能，且在 GUI 端保留圈序 fallback。通過 `test_throttle_ratio_calculations.py`、`tests/gui/test_throttle_line_chart_data_loader.py`。
> - 2025-10-07：建立初版任務描述，整合 CLI 與 GUI 需求。