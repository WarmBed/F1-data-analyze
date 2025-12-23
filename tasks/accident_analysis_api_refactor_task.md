# 任務：Accident Analysis 模組 API 化改造

- **目標**：將事故分析 GUI 模組的資料載入流程改為優先透過 FastAPI 取得功能 6/8 的分析結果，並保留 API 不可用時回退至既有 JSON/CLI 的機制。
- **負責人**：GitHub Copilot 自動化工作階段
- **建立日期**：2025-10-05

## 工作重點
1. 建立事故分析專用的 API worker，整合 `/api/v2/analysis/execute` 端點並支援 function_id 6 與 8。
2. 重構 `AccidentDataManager` 以採用 `UniversalDataLoader` 架構，API 成功時發送現有 GUI 所需的信號，失敗時觸發本地 JSON 搜尋與 CLI 生成後備流程。
3. 調整 GUI 模組狀態訊息，顯示資料來源（API 或本地），並確保原有 `statistics_loaded`、`all_incidents_loaded` 等信號正常運作。
4. 完成基本語法檢查與手動驗證，確保 API 工作流程在 GUI 中可正確載入事故統計與事件清單。

## 待辦清單
- [x] 新增事故分析 API worker 並串接資料載入流程。
- [x] 重構 `AccidentDataManager`，整合 `UniversalDataLoader` 與 API 優先策略。
- [x] 對齊事故 JSON 命名（API / GUI）改採 `all_incidents_summary_{year}_{race}_{session}.json`。
- [ ] 更新 GUI 端狀態訊息與回退流程，確保 UI 響應一致。
- [ ] 執行語法檢查與必要測試，確認改動無誤。

## 測試計畫
- `python -m py_compile modules/gui/accident_analysis/accident_analysis_mdi.py`
- （可選）啟動 API 服務後於 GUI 中切換事故分析模組，驗證 API 載入與回退行為。

## 備註
- API 基底網址以 `F1_API_BASE_URL` 環境變數優先，再讀取 `config/api_config.json`，預設為 `https://api.f1telemetrystationpro.org`。
- 若 API 回傳格式錯誤或成功標記為 False 必須立即回退至本地 JSON/CLI 管線，維持 GUI 可用性。
- 2025-10-05：調整事故詳細列表 Widget 以支援多種 API/JSON 結構，自動擴充 `all_incidents` 欄位並修正事件資料驗證流程，同步新增 CLI 檔名正規化（含 session 標籤）。
