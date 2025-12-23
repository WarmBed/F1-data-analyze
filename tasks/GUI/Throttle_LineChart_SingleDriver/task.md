# Throttle Line Chart (Single Driver) 任務追蹤

**建立日期**: 2025-10-08  
**負責人**: AI 編程助手  
**狀態**: 進行中

---

## 🎯 目標

在 `modules/gui/Throttle_analysis/throttle_line_chart_analysis/` 目錄下完成「Throttle Line Chart (Single Driver)」GUI 系統：

- 透過 API-ONLY 流程 (Function 54) 載入單車手全油門分析資料。
- 提供兩個同步的視覺化視窗：
  - 全油門秒數折線圖。
  - 圈速折線圖。
- 支援滑鼠游標、縮放、拖曳等互動同步。
- 提供過濾器、臨界值標示、基本匯出與統計摘要。

---

## 📦 交付項目

1. `ThrottleLineChartDataLoader` (繼承 `UniversalDataLoader`)
2. `ThrottleLineChartMDI` (繼承 `UniversalAnalysisMDI`)
3. `ThrottleLineChartModule` (`IAnalysisModule` 實作)
4. 專屬圖表元件與同步訊號匯流排
5. 控制面板 (過濾器、匯出、臨界值設定)
6. 單元 / 腳本測試通過 (`test_throttle_line_chart.py` 等)

---

## ✅ 驗收基準

- [ ] 透過 GUI 可建立 Throttle Line Chart 視窗並載入資料
- [ ] 兩個視窗在 hover / 縮放 / 拖曳時同步
- [ ] Tooltip 顯示必要欄位 (Lap, 全油門秒數, 圈速, Compound, DRS/ERS 等)
- [ ] 過濾設定生效 (Pit 圈、黃旗、臨界值標示)
- [ ] 匯出圖表或 CSV 成功
- [ ] 控制台 / 日誌無未處理例外
- [ ] 相關測試腳本執行成功

---

## 📝 工作清單

- [x] 建立任務追蹤檔
- [x] 建立資料載入器 (API + 本地 JSON 回退)
- [x] 建立同步圖表元件與 SignalBus
- [x] 實作 MDI / Module 邏輯並整合控制面板
- [x] 加入匯出與統計摘要
- [ ] 撰寫/更新測試，確認腳本可執行
- [ ] 最終驗證與文件更新

---

## 🧪 測試計畫

| 測試內容 | 執行方式 | 預期結果 |
|----------|----------|-----------|
| 匯入測試 | `python test_throttle_simple.py` | 所有模組可成功導入 |
| 模組測試 | `python test_throttle_module.py` | Widget 建立成功，無例外 |
| 功能測試 | `python test_throttle_line_chart.py` | 所有檢查通過 |
| GUI 手動驗證 | 啟動 `f1t_gui_main.py` | 兩視圖正常顯示並同步 |

---

## 📌 備註

- 嚴格遵守 API-ONLY 政策；禁止自動執行 CLI。
- 儘量重用 `UniversalChartWidget`，確保樣式一致。
- 依需求補充 i18n 金鑰與日誌輸出，方便偵錯。
- 若 CLI JSON 缺欄位需紀錄警告但不可崩潰。
