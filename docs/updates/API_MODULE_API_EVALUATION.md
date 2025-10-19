# GUI 模組 API 呼叫盤點與共用模組評估

## 目標與原則
- **統一 API 呼叫流程**：以共用的 API client / worker 取代各模組自行撰寫的 `QThread` + `requests.post`，減少重複碼與行為差異。
- **維持 API-ONLY 模式**：所有 GUI 模組預設僅透過 API 取得資料，不再啟動 CLI 或依賴本地 JSON。
- **保留快取擴充彈性**：`UniversalDataLoader.load_data()` 保持「快取入口」角色；若模組不使用快取，可在初始化時設定 `_local_storage_enabled = False`（或覆寫 `_get_search_directories()`）直接略過檔案流程。

## 現況總覽
- 速度、RPM、油門、雨量、輪胎、進站、賽道、事故、理想單圈、Throttle、色票、賽季行事曆等 GUI 模組，大多各自定義 `QThread` Worker 呼叫 `POST /api/v2/analysis/execute`，僅變更 `function_id` 與參數。
- Worker 內部重複撰寫逾時、錯誤處理、`success` 檢查與 `meta` 包裝邏輯；雖已透過 `resolve_api_base_url` 統一 base URL，但整體行為仍高度分散。
- `UniversalDataLoader.load_data()` 仍保留原本的本地 JSON → `QTimer` → `json.load` 流程。多數 API 模組完全不會呼叫 `load_data()`，但程式碼仍存在。

## 既有呼叫模式與差異
- **共通模式**：`requests.post` → `response.raise_for_status()` → `payload.get("success")` 檢查 → 解析 `payload["data"]` → 透過 `success` / `failure` 訊號回報 UI。
- **主要差異**：
  - `function_id`、逾時秒數、是否支援 `force_refresh`、額外參數（driver、lap、race、session）各不相同。
  - 進站、事故等模組需呼叫多組 `function_id`，甚至分批載入與驗證。
  - 健康檢查、fallback 策略缺乏一致性。
- **快取狀態**：雖已停用 CLI 與本地 JSON，但 `UniversalDataLoader` 仍需顯式關閉 `_local_storage_enabled`，才能避免多餘的檔案搜尋。

## 改進方向
1. **保留 `load_data()` 的快取職責**  
   - 仍需快取的模組維持原設計。  
   - API 模組在 DataLoader 初始化時關閉快取（或覆寫 `_get_search_directories()` 回傳空陣列），讓 `load_data()` 直接略過本地流程。

2. **建立共用 API client / worker**  
   - 新增 `core/analysis_api_client.py` 與 `core/analysis_api_worker.py`，統一處理：
     - Base URL 解析與健康檢查。
     - `function_id` / 查詢參數組裝、逾時與重試策略。
     - `success` / `failure` / `progress` 訊號。
     - 回傳標準結構 `{data, meta, payload}`。

3. **模組端整合**  
   - 各 GUI 模組改用共用 worker，只提供 `function_id` 與參數，並在成功後將資料交由原有的 DataLoader / Chart widget。
   - 若某模組需要在 GUI 端重用同一份 API 資料，可在 worker 層加上記憶體快取或訂閱機制，但仍遵守「不落地快取」原則。

## 多模組共用同一 API 的處理方式
- 例如 Function 13 被速度、RPM、油門模組同時使用；Function 26 被輪胎策略與相關圖表共用。
- 共用 API client 需支援以下能力：
  1. **並行呼叫**：每個模組帶入 `request_id` / `caller` 標識，worker 將回應送回正確的接收者，避免資料串流互相覆寫。
  2. **結果複用（選用）**：可在短時間窗內記錄最近的成功回應，若下一個請求參數相同則直接回傳，減少 API 壓力。
  3. **錯誤隔離**：即使多個模組呼叫同一 API，其中一個失敗也不應連帶影響其他模組的工作緒。
  4. **統一日誌與監控**：共用 client 可集中記錄 API 呼叫、耗時與錯誤碼，方便後續追蹤。

## 推薦開發流程
1. 實作共用 API client / worker（含單元測試），確保 `execute(function_id, params, timeout)` 等介面穩定。
2. 以 Telemetry 系列為試點（原 `TelemetryApiWorker`），導入共用 worker，驗證行為及既有測試。
3. 逐步遷移雨量、輪胎、賽道、事故、理想單圈、Throttle、行事曆、色票等模組；遷移後移除舊 Worker。
4. 更新 DataLoader 初始化邏輯，在 API 模組中關閉 `_local_storage_enabled`，確保 `load_data()` 不再搜尋本地檔案。
5. 視需要整合健康檢查與 fallback 策略，統一放在共用 client。

## 可行性評估
- **優點**
  - 大幅減少重複程式碼，API 行為維護集中化。
  - 錯誤處理、日誌、逾時設定一致，易於監控。
  - `UniversalDataLoader` 專注於快取機制，責任邊界清晰。
- **風險與成本**
  - 多數 GUI 模組的載入流程需重構，需完整回歸測試。
  - 共用 worker 必須覆蓋各種 `function_id` 參數需求。
  - 遷移期間需避免新舊流程同時存在造成重複請求。
- **先決條件**
  - 確認所有 GUI 模組已改走 API（無 CLI 依賴）。
  - 測試框架需能驗證 API 回應結構與 UI 行為。

## 受影響模組
- 遙測系列（速度、RPM、檔位、油門、煞車、加速度、距離差、速度差等）。
- 天氣與輪胎（雨量、輪胎策略）。
- 進站、賽道、事故模組與其 Data Manager。
- 理想單圈系列（Sector comparison、Heatmap、Ranking Table）。
- Throttle 系列（單車手折線圖、盒鬚圖）。
- 共用服務（色票 Function 98、賽季行事曆 Function 99）。
- 其他已改成 API-ONLY 的模組（Track Map、Driver Lap 分析、Lap Boxplot 等）。

## 後續行動清單
1. 完成共用 API client / worker 的雛形與測試。
2. Telemetry 系列導入共用 worker，並跑 `tests/test_telemetry_api.py` 等現有測試。
3. 依序遷移其他模組，並更新對應測試腳本。
4. 在 API 模組的 DataLoader 初始化階段關閉本地快取功能。
5. 更新開發文件與使用指南，說明 API-ONLY 原則與共用 client 的使用方式。
6. 完成整體回歸測試，確認 GUI 響應與 API 載入流程一致。
