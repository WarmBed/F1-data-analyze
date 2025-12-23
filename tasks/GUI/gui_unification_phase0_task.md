# GUI 模組統一化 Phase 0 準備任務

**狀態**: 草案建立中  
**建立日期**: 2025-10-11  
**最後更新**: 2025-10-11  
**負責人**: GitHub Copilot

## 目標

在進入 GUI 模組統一化計畫的 Phase 1 之前，完成所有準備工作，確保後續開發具備乾淨的工作狀態、完整的自動化檢查，以及可追蹤的驗證流程。

## 交付項目

1. 建立專用分支 `gui-unification-phase0` 並保持工作區乾淨。
2. 建立現有 GUI 模組快照以及架構比較報告，供後續差異分析與回退。
3. 建立最小自動化檢查工具組，覆蓋模組載入測試、i18n 硬編碼掃描、架構合規性檢查。
4. 定義後續階段通用測試流程與品質門檻，形成文檔化標準。

## 執行清單

### 0. 前置確認
- [x] 驗證當前分支與 Git 狀態，決定清理或備份策略。（2025-10-11 已確認，保留既有未追蹤資料，待後續分類）
- [x] 建立 `git status` 報告紀錄於 `logs/phase0_precheck_YYYYMMDD.txt`。（2025-10-11 完成）
- [ ] 若存在未追蹤或刪除項，完成分類：保留、移動至備份、或提交給相應子專案。

### 1. 分支與備份
- [ ] 將所有必要文件整理後，清理工作目錄至乾淨狀態。
- [x] 建立分支 `gui-unification-phase0`（自 `f54功能開發`）。
- [x] 匯出 `modules/gui/` 目錄結構與行數統計，輸出為 `reports/gui_modules_snapshot_phase0.json`。（2025-10-11 透過 `tools/generate_gui_module_snapshot.py` 完成）
- [ ] 建立 `reports/gui_architecture_matrix_phase0.md`，列出 19 個模組的基底類別、ApiWorker 類別、圖表 Widget 實作、國際化狀態。

### 2. 工具鏈建置
- [ ] 於 `tools/` 新增 `scan_hardcoded_strings.py`（或使用現有腳本）並整合 Phase 0 專用參數。
- [ ] 於 `tests/gui/` 建立 `test_module_import.py`，覆蓋 19 個模組 import 測試。
- [ ] 於 `tests/gui/` 建立 `test_universal_api_worker_stub.py`，先以 Skip 標記明確 Phase 1 才會啟用的測試。
- [ ] 於 `tools/` 建立 `verify_gui_architecture.py`，檢查各模組是否繼承通用基底，現階段可允許例外但需列出報告。

### 3. 文件與流程
- [ ] 更新 `docs/updates/GUI_MODULE_UNIFICATION_PLAN.md`，加入 Phase 0 進度追蹤區段（若未存在則新增）。
- [ ] 建立 `docs/process/gui_unification_onboarding.md`，說明開發者如何追蹤統一化進度。
- [ ] 撰寫 `docs/process/gui_unification_quality_gates.md`，記錄測試與驗收流程。
- [ ] 整理 Rain Analysis 作為範本的依賴清單與可重用元件清單，納入上述文件。

### 4. 驗證與交付
- [ ] 執行 `pytest tests/gui/test_module_import.py -v` 並記錄結果於 `logs/phase0_test_module_import.txt`。
- [ ] 執行硬編碼掃描與架構檢查，輸出報告於 `reports/phase0_validation_summary.md`。
- [ ] 完成 Phase 0 任務後，更新本檔狀態為「完成」，並在主計畫文件標記 Phase 0 完成。

## 風險與緩解

| 風險 | 描述 | 緩解方案 |
| --- | --- | --- |
| 工作區存在大量未追蹤檔案 | 可能導致建立分支失敗或誤刪檔案 | 先行分類與備份，必要時建立臨時提交或 Git stash |
| 工具鏈實作耗時 | Phase 0 工具涉及靜態分析與測試結構 | 先使用簡單版本，後續再疊代完善 |
| 現有模組資訊不一致 | 需手動蒐集或撰寫腳本 | 以 Rain Analysis 作為基準，延伸寫腳本自動收集 |

## 待確認事項

- [ ] 是否已有現成的硬編碼掃描工具可直接使用。
- [ ] 是否需保存現有已刪除的舊文件，或可直接移出版本控管。
- [ ] `TelemetryChartWidgetBase` 未被使用的原因是否存在阻礙，需要額外調查。
- [ ] API Worker 合併後的命名空間與現有模組路徑是否需事先保留。

## 訊息傳遞規範

- 本任務進度更新統一以此文件為主，每完成一子項目即更新核取方塊。
- 若發現阻塞或需決策，於 `docs/updates/GUI_MODULE_UNIFICATION_PLAN.md` 新增「阻塞項目」小節。
- 完成驗收後，於主專案 README 或發佈記錄簡述 Phase 0 成果。
