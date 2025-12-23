# 任務：建立 CLI 功能 API 中繼站

- **目標**：以 API 層封裝核心 CLI 功能，提供網路服務並保持既有 JSON 輸出流程。
- **負責人**：Codex 自動化工作階段
- **建立日期**：2025-09-29

## 模組優先順序 (A 類 CLI 功能)
1. 功能 1 – Rain Analysis（產出雨量 JSON，GUI 已串接）
2. 功能 2 – Track Analysis（產出跑道 JSON）
3. 功能 13 – Telemetry Comparison / Driver Comparison
4. 功能 26 – Tire Strategy Analysis
5. 功能 28 – Detailed Lap Analysis

## 工作重點
1. 實作 API 中繼站架構（建議 FastAPI + subprocess 或內部函式呼叫）。
2. 參數驗證與輸入/輸出格式標準化（對應 CLI 所需參數與 JSON 結構）。
3. CLI 執行管理（執行環境、日誌、錯誤處理、超時控制、快取）。
4. 測試策略（單元測試 + 整合測試 + 功能端點驗證）。
5. 部署與監控規劃（可選：容器化、排程、資源限制）。

## 待辦清單
- [x] 確認各 A 類功能的輸入參數與 JSON 輸出對應（以 function_specs 定義）。
- [x] 設計 API 介面草稿（路由、請求/回應格式、錯誤碼）。
- [x] 實作中繼站原型（先封裝功能 1、2），支援 CLI 呼叫並回傳 JSON。
- [x] 新增整合測試：模擬 API 請求或指令生成，驗證 CLI 執行前的參數組裝。
- [ ] 規劃日誌與錯誤回傳機制（CLI stdout/stderr、執行時間、快取重用）。
- [ ] 定義部署/安全策略（例如節流、權限、資源管理）。
- [x] 擴充至功能 13、26、28，並紀錄任何特殊依賴。
- [ ] 更新使用文件，說明 API 呼叫範例與 CLI fallback 行為。

## 優先測試
- [ ] 優先驗證功能 1（Rain Analysis），確保可在 API 中繼站成功產生 JSON，並提供測試報告。
  - 建議命令：`curl -X POST "/analysis/execute?function_id=1&year=2025&race=Japan&session=R"`
  - 執行後檢查 `json/` 目錄是否生成新的 Rain JSON，並可由 GUI 讀取。

## 備註
- 現有 GUI 仍以 JSON 為主要資料來源；API 中繼站需保持與現有 JSON 結構相容。
- CLI 功能若無 GUI 依賴，可暫緩 API 化；專注 A 類確保穩定性，再視需求擴充。
