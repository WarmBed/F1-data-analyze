# 任務：Pitstop Analysis 模組切換至 API 資料來源

- **目標**：將 Pitstop Analysis GUI 模組的資料載入流程改為透過 FastAPI `/api/v2/analysis/execute`（function_id=3/4/5）取得最新車手與車隊進站分析資料，並提供受控的 JSON/CLI 後備策略。
- **負責人**：GitHub Copilot 自動化工作階段
- **建立日期**：2025-10-09

## 工作重點
1. 建立可重用的 `PitstopAnalysisApiWorker`，支援車手/車隊/詳細進站三種資料型態的 API 呼叫與進度回報。
2. 將 `PitstopDataManager` 改為 API 優先，統一管理請求參數、狀態訊息與 metadata，並記錄最後一次 API 呼叫資訊。
3. 實作 `F1T_ALLOW_PITSTOP_JSON_FALLBACK` 控制的本地 JSON/CLI 後備流程，確保 API 故障時可以安全退回既有產物。
4. 維護既有 CLI 生成流程與重新載入訊號，確保舊資料仍可被 GUI 消費。

## 待辦清單
- [x] 新增 Pitstop Analysis 專用 API worker 並整合進度/錯誤訊號。
- [x] 更新 `PitstopDataManager` 使 `load_data`/`load_team_data`/`load_driver_detailed_data` 走 API 優先流程。
- [x] 補強 JSON 載入流程，將來源、回退策略、force refresh 等資訊寫入 `metadata`。
- [ ] GUI 內實測：在 API 正常與故障時確認三種資料皆能正確顯示並回退。
- [ ] 補充自動化測試或腳本，驗證 function_id=3/4/5 API 回傳結構與回退邏輯。

## 測試計畫
- `python -m py_compile modules/gui/pitstop_analysis/pitstop_analysis_mdi.py`
- 啟動 FastAPI 伺服器後，於 GUI 觸發 Pitstop Analysis，觀察 API 成功/失敗時的行為與後備策略。
- （選擇）設定 `F1T_ALLOW_PITSTOP_JSON_FALLBACK=1` 並停用 API，確認 CLI 重新產出後 GUI 能載入新 JSON。

## 備註
- API 基底網址優先讀取 `F1_API_BASE_URL`，其次為 `config/api_config.json` 的 `api_base_url`，預設 `https://api.f1telemetrystationpro.org`。
- 後備策略可透過環境變數或 `set_local_fallback_allowed()` 手動切換，預設停用本地 JSON。
- API 回傳的 metadata 會寫入 GUI 顯示層，可用於追蹤來源與延遲時間。
