# 油門分析折線圖 (單車手) - GUI 模組規劃

**模組分類**: GUI Develop Task  
**對應 CLI 功能**: Function 54 - Lap Throttle Ratio Per Driver  
**狀態**: 📝 規劃草案  
**建立日期**: 2025-10-07  
**最後更新**: 2025-10-07

---

## 🎯 目標概述

為單一車手提供 **Lap-by-Lap 全油門秒數折線圖**，並搭配圈速資料顯示，協助辨識節奏變化與策略分段。依需求將主要圖與次圖拆成 **兩個獨立的 MDI 子視窗**，但保持互動同步 (共享座標與游標)。支援 Tooltip 顯示輪胎、DRS、ERS 等關鍵資訊。

---

## 🖼️ 視覺元素設計

### 視窗 A：全油門秒數折線圖
- **X 軸**: `lap_number`
- **Y 軸**: `full_throttle_duration_s` (秒)
- **線條**: 主線顏色依車手/車隊顏色；可選擇折線或散點折線混合
- **標記**: 重要圈 (Pit、Safety Car) 以形狀標示
- **區域背景**: 可選擇 shading 標示不同輪胎 stint 範圍
- **Tooltip**: 顯示 `Lap`, `full_throttle_duration_s`, `LapTime`, `Compound`, `DRS %`, `ERS Deploy %` (若 JSON 提供)
- **互動控件**:
  - 門檻顯示 (≥0.90)
  - 突顯特定圈 (使用列表或滑桿選取)
  - Toggle 直線/散點顯示

### 視窗 B：圈速曲線圖
- **X 軸**: `lap_number` (與視窗 A 同步)
- **Y 軸**: `lap_time_seconds` (或相對最快圈的Δ秒)
- **顯示**:
  - 折線或散點
  - 可選擇顯示移動平均 (平滑處理)
  - Pit stop 圈使用特別標記
- **Tooltip**: 显示 `Lap`, `LapTime (格式化)`, `Compound`, `Pit?`

### 同步需求
- 兩個視窗皆使用 `UniversalAnalysisMDI` 的子視窗，但共享訊息渠道：
  - 滑鼠移到視窗 A 的第 N 圈時，視窗 B 同步 highlight 第 N 圈。
  - 縮放/平移 X 軸時，另個視窗跟隨。
  - 可考慮在 `UniversalAnalysisCoordinator` 中建立事件橋接器。

---

## 🧱 架構與資料流程

1. **資料來源**：
   - 使用 `ThrottleLineChartDataLoader` (繼承 `UniversalDataLoader`) 載入 Function 54 JSON。
   - 若 GUI 在單車手模式下發送 API 請求需附上 `driver` 參數。
   - 轉換為 DataFrame，欄位至少包含：`lap_number`, `full_throttle_duration_s`, `lap_time_seconds`, `compound`, `stint`, `drs_usage`, `ers_deploy`, `speed_avg_kmh`, `pit_status`。

2. **圖表控制層**：
   - `ThrottleLineChartController` 負責過濾與觸發事件。
   - 將 DataFrame 拆成兩個 `Series`：全油門秒數、圈速。

3. **視窗互動**：
   - 兩個 MDI 子視窗各自持有 `UniversalChartWidget`。
   - 建立 `SignalBus` (Qt Signals)：
     - `cursorMoved(lap_number)`
     - `xRangeChanged(start_lap, end_lap)`
   - 視窗 A 掃描事件 → emit → 視窗 B 接收並更新 highlight，反之亦然。

4. **Tooltip 實作**：
   - 使用 matplotlib `pick_event` 或 `mplcursors`。
   - 內容格式範例：
     ```
     Lap 12
     Full Throttle: 34.2 s
     Lap Time: 1:32.456
     Compound: MEDIUM
     DRS: 45%
     ERS Deploy: 62%
     ```
   - 若某欄位缺值，顯示 `N/A`。

5. **其他 UI 元件**：
   - 篩選器：選擇包含/排除 Pit 圈、Safety Car 圈。
   - 儲存/匯出：
     - 圖片輸出 (PNG/SVG)
     - 導出以圈為單位的 CSV
   - 狀態列：顯示目前圈速、全油門門檻、資料筆數。

---

## 🧪 測試與驗證

| 測試項目 | 說明 |
|----------|------|
| API 整合 | 搭配 Function 54 驗證單車手模式返回值正確 |
| Tooltip | 滑鼠移動顯示資訊是否完整且無延遲 |
| 同步機制 | 兩視窗中任一縮放/移動/hover 時，另一視窗同步更新 |
| 空資料 | 當某圈缺少 `full_throttle_duration_s` 或 `lap_time_seconds` 時需顯示警告 |
| 門檻調整 | 若 CLI 回傳不同門檻計算結果，GUI 正確顯示標籤 |
| i18n | 中英文切換時 Tooltip 與標籤翻譯正確 |
| 匯出功能 | 匯出檔名與內容需包含 driver/year/race/session |

---

## ⚠️ 風險與注意事項

- **雙視窗同步複雜度**：需確保滾輪縮放、滑鼠拖曳、鍵盤短鍵在兩視窗都能一致響應。
- **Performance**：若圈數多 (例如 FP sessions)，需評估繪圖性能與 hover 效能，可考慮使用 downsampling。
- **API 欄位依賴**：Tooltip 所需欄位需在 Function 54 JSON 中提供，若無則需 CLI 補齊。
- **使用者體驗**：需考慮提供「重置視圖」、「同步開關」、「單視窗模式」等 UI。

---

## 📌 下一步建議

1. 在 `tasks/GUI/Throttle_LineChart_SingleDriver/task.md` 建立任務追蹤，定義驗收標準。
2. 與 CLI 團隊確認 JSON 欄位 (特別是 DRS/ERS 與 Pit 標記)。
3. 建立 `ThrottleLineChartDataLoader` 雛形與單元測試。
4. 實作雙視窗同步訊號與 chart drawing 原型。
5. 撰寫操作指南，說明如何從箱型圖快速切換至單車手折線圖檢視。

---

> 本文件為初步規劃，後續若有需求更新或欄位調整，請同步修訂並記錄版本。