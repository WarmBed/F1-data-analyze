# 任務：GUI 多語言化改造

- **目標**：確保所有 GUI 介面文字都能切換語言（預設英文，可選中文），避免出現中英混合；統一字串管理與翻譯流程。
- **負責人**：Codex 自動化工作階段
- **建立日期**：2025-09-29

## 工作重點
1. 盤點所有 GUI 模組的硬編字串，建立國際化清單與翻譯檔 (en / zh)。
2. 更新 `core/gui_i18n.py` 或擴充框架，支援字串 key 化、動態載入、快取與 fallback。
3. 替換 GUI 代碼中的直接字面字串為翻譯函數（如 `tr("key", default)`），確保預設顯示英文。
4. 規劃翻譯檔維護流程（命名規則、檔案位置、審閱方式），並補上自動檢查避免回退混合語言。
5. 執行 GUI 介面的中/英語實測（含常見模組，例如 lap_analysis、driver_analysis、tire_analysis 等）。

## 待辦清單
- [ ] 整理硬編字串清單與對應模組，提供翻譯所需上下文。
- [ ] 建立英文/中文詞彙對照與翻譯檔骨架（優先處理 lap_analysis、driver_analysis、telemetry 模組）。
- [ ] 擬定 GUI 模組優先順序（例如 Rain Analysis、Track Analysis、Driver/Tire/Telemetry MDI 先行），分批替換字串。
- [ ] 規劃/實作多語翻譯檔案格式（建議 JSON 或 YAML）與載入流程。
- [ ] 針對已有語言系統的核心畫面（如 Rain、Track、Driver、Telemetry MDI）優先將中文硬字串改成英文或翻譯鍵。
- [ ] 導入翻譯函式庫，替換 GUI 程式碼中的字串呼叫並設定英文為預設語言。
- [ ] 建立翻譯檔維護與審核流程（含自動檢查或開發工具），並定期掃描殘留中文字串。
- [ ] 對核心 GUI 模組進行中英文切換測試，紀錄結果與問題。

## 備註
- `modules/gui/lap_analysis/*`、`driver_analysis`、`telemetry_analysis_mdi.py` 等檔案含大量中文字串；需優先處理並提供英文對照。
- 建議先完成詞彙對照及優先級規劃，再分批導入翻譯函式。
- 目前 `core/gui_i18n.py` 功能有限，建議重構以支援多語 JSON 與動態載入。
