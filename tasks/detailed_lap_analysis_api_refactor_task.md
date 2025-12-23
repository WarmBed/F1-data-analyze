# 任務：Detailed Lap Analysis 模組 API 化改造

- **目標**：讓詳細圈速分析（Function 28）改採 API 優先載入流程，維持 UniversalDataLoader 架構並保留必要的 JSON/CLI 後備。
- **負責人**：GitHub Copilot 自動化工作階段
- **建立日期**：2025-10-01

## 工作重點
1. 建立 F28 專用 API worker，接入 `/api/v2/analysis/execute` 並支援 `driver1` 參數。
2. 重構 `driverLapAnalysisDataManager`，調整分析類型註冊為 `data_source="api"`，加上本地 JSON 後備策略與快取管理。
3. 調整 GUI 與 CLI 生成流程的檔名規範，使 API、JSON、CLI 保持一致。
4. 在成功載入後更新快取與狀態訊息，並於失敗時確保能回退到現有 JSON/CLI 管線。

## 待辦清單
- [x] 審視現有 Function 28 GUI/CLI JSON 結構，確認 API 回傳格式相容性。
- [x] 新增 `DetailedLapAnalysisApiWorker` 並在資料管理器內建連線與錯誤處理流程。
- [x] 更新 `driverLapAnalysisDataManager` 的載入邏輯與檔案搜尋策略。
- [x] 驗證 CLI 生成後的 JSON 命名與 GUI 搜尋模式一致。

- [ ] 執行實際整合驗證：
	- [x] 語法檢查 (`python -m py_compile ...`).
	- [ ] 手動測試（API 成功）。
	- [x] 手動測試（API 失敗 -> 本地回退）。
	- [ ] 驗證關閉視窗／程式時不再出現 QThread 崩潰訊息。

## 測試計畫
- `python -m py_compile modules/gui/driverLap_analysis/driverlap_analysis_mdi.py`
- （選擇性）啟動 FastAPI 服務後於 GUI 觸發詳細圈速分析，確認 API 與回退流程。

## 備註
- 若需允許 JSON 後備，可使用環境變數 `F1T_ALLOW_LAPTIME_JSON_FALLBACK=1`；預設仍以 API 為優先。
- API 回傳 `success=False` 或資料格式異常時需立即切換至本地工作流程，避免 GUI 無資料狀態。
- GUI 讀取與 CLI 生成流程統一使用彙總檔 `detailed_laptime_analysis_{year}_{race}_{session}.json`，車手篩選僅在 UI 層管理。
- 已新增 `stop_loading/cleanup`，關閉模組時會安全釋放 API/CLI 背景工作執行緒。
- 2025-10-01：以手動測試腳本模擬 API 連線失敗情境，確認自動回退至本地 JSON 並成功渲染圖表。
- 2025-10-01：細化 API worker 清理流程，若執行緒在關閉時仍在運行會先等待 2 秒，必要時強制 `terminate()` 後再釋放，避免 QThread 「仍在運行即遭銷毀」的閃退風險。
- 2025-10-05：整併 API/CLI worker 生命週期管理，新增 `_stop_api_worker` / `_cleanup_cli_worker` 以確保所有訊號於 `finished` 後統一回收。
- 2025-10-05：阻擋重複載入請求並標準化 stop_loading 流程，確保視窗關閉時會先中斷 worker，再進行刪除。
