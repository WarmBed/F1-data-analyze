# 任務：GUI Driver Analysis 模組命名調整

- **目標**：將 GUI 功能樹與模組顯示名稱中原先標示為「Driver Ranking」的模組統一調整為「Driver Analysis」，並確保對應的翻譯鍵、模組屬性與映射表一致。
- **負責人**：GitHub Copilot 自動化工作階段
- **建立日期**：2025-09-30

## 工作重點
1. 更新功能樹節點與右鍵選單映射，使模組顯示為「Driver Analysis / 車手分析」。
2. 調整 `TelemetryAnalysisModule` 的內部識別名稱、顯示名稱與視窗標題，避免與「Telemetry Analysis」混淆。
3. 擴充 GUI i18n 翻譯鍵，新增 `driver_analysis` 對應條目，同步保留舊鍵 fallback 以維持相容性。
4. 確認模組工廠映射 (`module_mapping`) 指向正確模組型別，並維持既有的遙測數據邏輯。
5. 執行手動驗證：
   - 啟動 GUI，展開 `[TOOL] Single Race Analysis` 群組，確認中文與英文模式下皆顯示「車手分析 / Driver Analysis」。
   - 由功能樹點擊新節點，確認開啟的視窗標題與狀態列同步顯示更新後名稱。

## 待辦清單
- [x] 更新 `f1t_gui_main.py` 功能樹節點與模組映射表。
- [x] 調整 `TelemetryAnalysisModule` 的 `module_name`、`display_name`、`description` 與視窗標題輸出。
- [x] 擴充 `core/gui_i18n.py` 的翻譯鍵，加入 `driver_analysis` 對應值並保留舊鍵備援。
- [ ] 進行 GUI 手動驗證並在此檔案更新進度紀錄。

## 備註
- 模組仍沿用現有 `TelemetryAnalysisModule` 實作與 CLI Function 12 數據流程，僅調整命名與顯示文字。
- 若後續需進一步拆分 Driver 與 Telemetry 分析邏輯，需額外規劃專案任務。
