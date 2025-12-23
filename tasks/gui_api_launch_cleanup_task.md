# 任務：GUI 啟動流程與假系統日誌移除

- **目標**：同步調整 VS Code 偵錯設定，啟動時能同時掛起 API 伺服器與 GUI，並移除 GUI 內未連接後端的假系統日誌元件。
- **負責人**：GitHub Copilot 自動化工作階段
- **建立日期**：2025-10-03

## 工作重點
1. 更新 `.vscode/launch.json`，統一 API/GUI 所需環境變數並提供可直接偵錯的複合組態。
2. 確認 `Run GUI + API` 組態啟動順序正確，API 成功掛載後 GUI 才嘗試健康檢查。
3. 移除 GUI 端的假系統日誌面板與相關菜單項，避免誤導使用者。
4. 清理遺留的程式碼、註解與樣式設定，確保界面只顯示真實數據來源。

## 待辦清單
- [ ] 於 `launch.json` 中新增 GUI 所需的 `F1_API_BASE_URL` 等環境變數，並為 API 組態設定穩定的啟動參數。
- [ ] 檢查複合組態 (`Run GUI + API`)，加入必要的 `stopAll`/提示設定，確保停止時兩側皆能關閉。
- [ ] 刪除 GUI 側的假系統日誌元件、相關函式與菜單命令。
- [ ] 執行基本語法或單元測試，確認改動未引入語法錯誤。
- [ ] 手動（或文件化）驗證：啟動複合偵錯，確保 API 正常回應 /health，GUI 能看到真實狀態。

## 測試計畫
- `python -m py_compile f1t_gui_main.py`
-（可選）`python -m pytest tests/ -k "api" -v`

## 備註
- GUI 透過環境變數或 `api/api_config.json` 取得 API 位址，偵錯設定需與此一致。
- 清除假日誌後，若仍需記錄 GUI 端訊息，應透過 `core.logger` 及真實後端回報機制。
