# 任務：Telemetry Analysis 模組切換至 API 資料來源

- **目標**：將 Telemetry Analysis GUI 模組的資料載入流程由本地 JSON/CLI 轉為呼叫 FastAPI 服務，仍保留在 API 故障時的受控回退能力。
- **負責人**：GitHub Copilot 自動化工作階段
- **建立日期**：2025-10-06

## 工作重點
1. 新增專用的 `TelemetryAnalysisApiWorker`，以非阻塞方式呼叫 `/api/v2/analysis/execute` (function_id = 12)。
2. 將 `TelemetryDataManager` 改為 API 優先，並整合統一的進度/狀態訊息回報機制。
3. 在 API 失敗時啟用可控的本地 JSON/CLI 後備流程，並記錄落地中繼資料供 GUI 顯示。
4. 調整手動刷新邏輯，確保可觸發 API 重新分析並維持既有的 CLI 生成流程。

## 待辦清單
- [x] 建立 Telemetry Analysis 專用 API worker 並處理成功/失敗訊號。
- [x] 更新 `TelemetryDataManager.loadTelemetryData` 為 API 優先流程，包含 fallback 政策設定。
- [x] 擴充 JSON 載入流程，統一寫入 `metadata`（來源、回退原因、force refresh 狀態等）。
- [ ] 在 GUI 內實測 API 與本地後備流程的切換，確認所有分頁能正確顯示。
- [ ] 覆寫/新增單元測試或整合測試，驗證 API 回傳結構與 fallback 邏輯。

## 測試計畫
- `python -m py_compile modules/gui/telemetry_analysis_mdi.py`
- （建議）啟動 API 伺服器後於 GUI 內載入 Telemetry Analysis，觀察 API 成功與故障時的行為。
- （選擇）模擬 API 失敗並確認環境變數 `F1T_ALLOW_TELEMETRY_JSON_FALLBACK=1` 時可正確退回 CLI/JSON。

## 備註
- API 基底網址優先取自環境變數 `F1_API_BASE_URL`，其次讀取 `config/api_config.json`，預設為 `https://localhost:8000`。
- 本地回退策略可透過環境變數 `F1T_ALLOW_TELEMETRY_JSON_FALLBACK` 或 `set_local_fallback_allowed()` 手動調整。
- CLI 後備仍依賴既有的 Function 12 實作，產生的 JSON 會自動標記為 `data_source = "local-json"` 並附上回退原因。
