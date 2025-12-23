# 任務：整理 CLI 功能與 GUI 對應關係

- **目標**：寫腳本盤點 `F1AnalysisFunctionMapper` 的 `_execute_*` 與對應分析器，並整理 GUI 模組串接狀況與功能分類。
- **負責人**：Codex 自動化工作階段
- **建立日期**：2025-09-29

## 工作重點
1. 功能盤點腳本：掃描 `function_mapper.py` 內的 `_execute_*` 函式，檢測是否呼叫產生 JSON 的流程（含 `_save_json`、寫入 `json/` 等）。
2. GUI 連結對照：逐一檢視 `modules/gui/**/` 的 `AnalysisConfig` 或硬編 CLI 呼叫，確認 GUI 對應的功能 ID 或子功能。
3. 狀態分類：
   - A 類：CLI 可執行、GUI 有串接、並生成 JSON。
   - B 類：CLI 可執行但 GUI 尚未串接。
   - C 類：CLI/GUI 為半成品或標示 Deprecated，需決定是否保留。
4. 映射器策略：評估是否持續使用 `F1AnalysisFunctionMapper` 做為統一入口，並避免出現 `4.1` 這類含小數點的功能呼叫，必要時提出清理方案。

## 待辦清單
- [x] 建立腳本分析 CLI 功能與 JSON 產出狀態。
- [x] 彙整 GUI 模組與 CLI 功能映射表。
- [x] 完成本次功能分類（A/B/C）並提出後續建議。
- [x] 評估 mapper 清理方案，包含移除小數點功能 ID 的需求。
- [x] 執行單項驗證（例如：腳本結果與手動抽查是否一致）。

## 備註
- CLI/GUI 功能分類結果已輸出至 `investigation_output/cli_gui_function_classification.json`，後續可依 A/B/C 清單安排整併或下架作業。
- 建議下一階段針對 A 類功能撰寫自動化測試並製作小數點功能 ID 的替換腳本；目前測試仍待執行。
