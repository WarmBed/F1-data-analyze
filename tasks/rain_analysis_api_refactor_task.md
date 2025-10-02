# 任務：Rain Analysis 模組切換至 API 資料來源

- **目標**：將 Rain Analysis GUI 模組的資料載入流程由本地 JSON/CLI 轉為呼叫 FastAPI 服務，並保留在 API 故障時自動退回既有 JSON 管線的能力。
- **負責人**：GitHub Copilot 自動化工作階段
- **建立日期**：2025-10-03

## 工作重點
1. 導入非阻塞的 API worker，於背景執行 `/api/v2/analysis/execute` (function_id=1) 請求。
2. 將 `RainAnalysisDataManager` 預設資料來源改為 API，並於成功回應後沿用原有處理/圖表邏輯。
3. 失敗時觸發本地 JSON/CLI 後備流程，確保 GUI 仍可顯示既有資料。
4. 替換舊有檔案搜尋狀態訊息為 API 專用提示，記錄資料來源以供後續模組顯示。

## 待辦清單
- [x] 新增 Rain Analysis 專用的 API worker 並串接至資料載入流程。
- [x] 更新 `RainAnalysisDataManager`，支援 API 載入與本地後備策略。
- [x] 調整模組摘要/狀態資訊，標示資料取自 API 或本地快取。
- [x] 執行語法檢查與基本功能測試，確保改動無誤。

## 測試計畫
- `python -m py_compile modules/gui/rain_analysis/rain_analysis_mdi.py`
- `python -m py_compile modules/gui/rain_analysis/rain_analysis_module.py`
- （可選）在 API 服務開啟時於 GUI 內手動載入 Rain Analysis，驗證 API 與後備模式切換。

## 備註
- API 基底網址以環境變數 `F1_API_BASE_URL` 優先，其次讀取 `config/api_config.json`，預設為 `http://127.0.0.1:8000`。
- 若 API 返回 `success=False` 或格式不正確，須立即退回本地 JSON/CLI 管線，避免 GUI 無資料可用。
