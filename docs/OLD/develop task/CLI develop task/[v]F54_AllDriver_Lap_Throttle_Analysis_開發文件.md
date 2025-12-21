# F54 全車手每圈油門比例分析 (Lap Throttle Ratio Per Driver) - 開發文件

**功能編號**: Function 54  
**CLI 指令**: `-f 54`  
**開發狀態**: 📝 規劃階段  
**目標版本**: v1.0.0  
**建立日期**: 2025-10-07  
**最後更新**: 2025-10-07

---

## 🔍 既有功能與編號衝突評估

- 已檢閱 `CLI_modules/cli/core/function_mapper.py`：目前功能映射表僅定義到 `53` 與 `99`，未發現 `54` 的既有實作或保留註記。
- 全域搜尋關鍵字 `"-f 54"`、`"function_id": 54`、`"Function 54"`：未找到任何 CLI 指令範例、測試案例、說明文件或 JSON 輸出對應到 54。
- 結論：`-f 54` 目前尚未被使用或保留，指派給「全車手每圈油門比例分析」沒有衝突風險。

---

## 🎯 功能目標

建立一個 CLI 功能，計算並輸出指定賽事中 **每位車手、每一圈的油門使用比例**，作為駕駛風格與動力輸出分析的基礎資料。主要指標包含：

1. **Lap Throttle Percentage**：該圈油門開度資料中，油門大於指定門檻 (預設 0.9) 的時間占比。
2. **Average Throttle**：整圈平均油門開度。
3. **Throttle Variability Index**：油門序列的標準差或 MAD，衡量油門波動程度。
4. **Full Throttle Duration (秒)**：油門 >= 0.9 的累計時間，提供直線性能分析基礎。
5. **Coasting Duration (秒)**：油門 <= 0.2 的累計時間，搭配煞車分析用。

逐圈資料需與車手、圈號、輪胎、天氣等資訊關聯，方便 GUI 或後續分析模組利用。

---

## 🧩 預期輸入參數

| 參數 | 必填 | 說明 | 範例 |
|------|------|------|------|
| `-f` | ✅ | 功能編號 (固定 54) | `54` |
| `-y` / `--year` | ✅ | 賽季年份 | `2024`, `2025` |
| `-r` / `--race` | ✅ | 賽事名稱 (FastF1 官方名稱) | `Japan`, `Monaco` |
| `-s` / `--session` | ✅ | 賽段 | `R`, `Q`, `FP1/2/3` |
| `--threshold` | ❌ | 自訂全油門門檻 (預設 0.9) | `0.85` |
| `--coast-threshold` | ❌ | 自訂滑行判定門檻 (預設 0.2) | `0.25` |

> **參數行為**：功能 54 一律輸出全車手資料；GUI 呼叫時無需傳入單一車手參數。

---

## 📈 計算流程 (初稿)

```
┌────────────────────────────────────────────┐
│ 步驟 1: 載入 FastF1 Session (含 Telemetry) │
└────────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────┐
│ 步驟 2: 取得每位車手的 Lap 資料與 Telemetry │
│ - session.laps.pick_driver(driver).index  │
│ - session.laps.get_telemetry(lap)         │
└────────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────┐
│ 步驟 3: 針對每圈計算油門序列指標            │
│ - 正規化時間序列為秒                       │
│ - full_throttle_ratio = (throttle ≥ T) / n │
│ - avg_throttle = throttle.mean()           │
│ - variability = throttle.std()             │
│ - full_throttle_duration = ΣΔt(throttle≥T) │
│ - coasting_duration = ΣΔt(throttle≤C)      │
└────────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────┐
│ 步驟 4: 彙整至資料列，加入圈速、輪胎等欄位 │
└────────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────┐
│ 步驟 5: 匯出結構化 JSON / 傳回分析結果     │
└────────────────────────────────────────────┘
```

---

## 🗂️ JSON 輸出規劃 (v1)

**檔名規則**：`throttle_ratio_{year}_{race}_{session}_[driver].json`

- 若輸出為全車手資料，檔名末段省略 `[driver]`，實際生成 `throttle_ratio_{year}_{race}_{session}.json`
- 如遇同名檔案會直接覆寫，保持單一檔案供 GUI 或 API 後續讀取。
- CLI 執行時會先檢查是否已有相同 `{year}_{race}_{session}` 且門檻一致的 JSON；若存在則直接載入既有檔案，不再重算；若門檻不同則覆寫同名檔案。

```json
{
  "metadata": {
    "function_id": 54,
    "function_name": "Lap Throttle Ratio Per Driver",
    "year": 2025,
    "race": "Japan",
    "session": "R",
    "driver_filter": null,
    "thresholds": {
      "full_throttle": 0.9,
      "coast": 0.2
    },
    "analysis_timestamp": "2025-10-07T12:34:56Z"
  },
  "analysis": {
    "drivers": [
      {
        "driver_code": "VER",
        "team": "RED BULL RACING",
        "laps": [
          {
            "lap_number": 12,
            "lap_time_seconds": 92.456,
            "compound": "MEDIUM",
            "average_throttle": 0.78,
            "full_throttle_ratio": 0.42,
            "full_throttle_duration_s": 34.2,
            "coasting_duration_s": 5.1,
            "throttle_variability": 0.18,
            "speed_avg_kmh": 204.3,
            "top_speed_kmh": 321.5
            "telemetry_sample_count": 1200,
            "data_status": "ok",
            "lap_time_formatted": "01:32.456",
            "sector1_time": 27.321,
            "sector2_time": 30.112,
            "sector3_time": 35.023,
            "drs_usage_ratio": 0.12,
            "ers_deploy_ratio": 0.45
          }
        ]
        "summary": {
          "valid_laps": 45,
          "avg_full_throttle_duration_s": 32.1,
          "median_full_throttle_duration_s": 31.8,
          "max_full_throttle_duration_s": 36.4,
          "min_full_throttle_duration_s": 28.7,
          "avg_full_throttle_ratio": 0.38,
          "avg_lap_time_seconds": 94.201
        }
      }
    ]
  }
}
```

- `telemetry_sample_count`：該圈可用遙測點數，有助於評估資料品質。
- `data_status`：`ok` 或 `insufficient`，標記是否成功完成計算。
- `lap_time_formatted`、`sector1_time` 等：提供 GUI 顯示用的時間格式化結果。
- `drs_usage_ratio` 與 `ers_deploy_ratio`：若 FastF1 Telemetry 含 `DRS` 或 `ERSDeployMode` 欄位則計算對應占比，缺失時回傳 `null`。

> **延伸欄位**：上述額外欄位為 GUI/報表所需資訊，若未被使用可在後續評估精簡。

---

## 🔗 API-ONLY 模式對應

- 功能開發完成後需透過 `refactored_api.py` 暴露新端點，或重用 `/analyze` 一般入口。  
- GUI 模組僅能呼叫 REST API 或讀取既有 JSON，禁止直接喚起 CLI；此功能的 CLI 實作需確保輸出 JSON 可被 GUI 後續載入。  
- 若需新的 GUI 模組，必須透過 `UniversalDataLoader` 實作 `function_id=54` 的資料載入邏輯。

---

## ✅ 驗證與測試需求 (初稿)

1. **單圈計算驗證**：使用已知 Telemetry 資料比對手算結果 (例如 2024 日本站 R，VER 第 12 圈)。
2. **多車手一致性**：確保所有車手皆能返回資料，即使某些圈缺少 Telemetry 時需妥善處理 (跳過或標記 `data_status = "missing"`)。
3. **門檻參數測試**：調整 `--threshold`、`--coast-threshold` 時結果應隨之變動。
4. **JSON Schema 檢核**：新增 `tests/test_throttle_ratio_schema.py`，使用 `jsonschema` 或簡易欄位驗證。
5. **API 回應測試**：透過 `pytest` 模擬 `POST /analyze` 請求，確認整合流程。

---

## ⚠️ 風險與待確認事項

- **Telemetry 密度**：FastF1 油門資料在節點間的時間間隔不均，需確認積分方法 (累計 Δt) 是否足夠精準。
- **缺失資料**：部分圈可能缺乏油門欄位或 `NaN`，需定義回傳格式 (例如 `"data_status": "insufficient"`)。
- **性能考量**：全車手全圈計算可能耗時，需確認是否加上快取或分批處理策略。
- **與現有功能協同**：若後續要與 `Function 53` 的理想圈分析或其他 lap-based 功能交叉使用，需統一欄位命名與時間單位。

---

## 📋 下一步行動建議

1. 撰寫 `tasks/` 對應工作項目 (含驗收、測試計畫)。
2. 在 `function_mapper.py` 中預留 `54: self._execute_driver_throttle_ratio` 對應函式並建立骨架。 
3. 建立分析模組檔案 (建議路徑：`CLI_modules/cli/analyzer/driver_throttle_ratio.py`)。  
4. 實作單元測試與 JSON Schema 驗證腳本。  
5. 更新 `docs/` 相關說明 (例如 CLI 快速指南、新功能介紹)。

---

## 🗂️ tasks/ 對應工作項目

- `tasks/F54_Lap_Throttle_Analysis/task.md`
  - **任務範圍**：涵蓋 CLI 計算模組、API 整合、GUI 箱型圖與折線圖雙視窗同步等交付物。
  - **驗收條件**：包含 CLI/GUI 功能完成、API `/analyze` 支援 function 54、文件更新與 QA 簽核等七項檢核點。
  - **測試計畫**：定義單元測試 (油門積分驗證、門檻變更、缺失資料處理)、整合測試 (CLI→JSON→GUI、API 測試) 與手動驗證流程。
  - **里程碑**：列出從 2025-10-12 起的 CLI、API、GUI 實作與整體收尾時程，用於追蹤進度。

---

> 此文件為初始規劃草案，後續評審或需求更新請以最新版本為準。
