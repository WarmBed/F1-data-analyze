# Lap Box Plot Analysis 模組重構任務

## 目標
- 將 `modules/gui/lap_box_plot_analysis` 下的模組整合到 `modules/gui/driver_race` 命名空間中。
- 保持 API-ONLY 模式與現有 Lap Analysis 功能的相容性。
- 確保所有引用路徑、初始化流程與測試同步更新。

## 子任務清單
- [ ] 盤點既有檔案 (`lap_box_plot_analysis_mdi.py`, `lap_box_plot_analysis_module.py`, `lap_box_plot_chart_widget.py`, `__init__.py`) 與相依關係。
- [ ] 將上述檔案搬移至 `modules/gui/driver_race/lap_box_plot_analysis/` 並更新匯入路徑。
- [ ] 清理舊資料夾、確認無殘留的重複實作或相容層。
- [ ] 更新 `f1t_gui_main.py`、模組註冊與測試程式所引用的模組路徑。
- [ ] 重新檢查 System Settings（特別是 Filter Pit Laps）與 Lap Analysis 的互動。
- [ ] 執行相關測試（最少 `pytest tests/test_boxplot_mdi_full.py`）與 `python -m py_compile` 驗證語法。

## 驗證計畫
1. `python -m py_compile` 檢查所有被移動的新檔案。
2. `pytest tests/test_boxplot_mdi_full.py -k boxplot`（或其他相關測試）。
3. GUI 啟動手動驗證（必要時記錄）。

## 風險與注意事項
- GUI 模組多處動態匯入，必須確保新的路徑同步更新。
- 需確保 `UniversalAnalysisMDI` 的動態載入設定仍能找到模組。
- 避免破壞既有的 System Settings 連動邏輯。
- API-ONLY 政策：不可引入 CLI 直接啟動。
