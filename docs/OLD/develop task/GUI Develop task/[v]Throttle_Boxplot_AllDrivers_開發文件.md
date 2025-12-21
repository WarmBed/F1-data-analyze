# 油門分析箱型圖 (全車手) - GUI 模組規劃

**模組分類**: GUI Develop Task  
**對應 CLI 功能**: Function 54 - Lap Throttle Ratio Per Driver  
**狀態**: 📝 規劃草案  
**建立日期**: 2025-10-07  
**最後更新**: 2025-10-07

---

## 🎯 目標概述

建立一個 GUI 視圖，使用箱型圖展示指定賽事中各車手的 **全油門秒數分佈**，協助分析不同車手的油門使用風格。資料來源為 CLI Function 54 輸出的 JSON (`full_throttle_duration_s`)，支援 API-ONLY 模式下的資料載入。

### 關鍵問題
- 各車手在整場賽事中每圈油門 ≥ 90% 的時間分佈如何？
- 是否存在異常圈 (outlier) 顯示不尋常的油門行為？
- 不同輪胎化合物或天氣條件是否影響箱型圖結果？

---

## 📊 視覺化需求

| 項目 | 說明 |
|------|------|
| 圖型 | 箱型圖 (Box Plot) |
| X 軸 | 車手 (`driver_code`)，需可選擇排序方式 (依中位數、字母、車隊) |
| Y 軸 | `full_throttle_duration_s` (單位：秒) |
| 群組 | 預設單一箱型圖；提供切換以輪胎 (`compound`) 或 stint 為群組的選項 |
| 異常值 | 顯示圓點，支援 hover tooltip 顯示圈號、輪胎、圈速等細節 |
| 顏色 | 依車隊主題色 (使用既有顏色映射) |
| Tooltip | `LapNumber`, `LapTime (格式化)`, `Compound`, `full_throttle_ratio`, `avg_throttle`, `DRS %` (若有) |
| 篩選 | - 車手多選  
|      | - 輪胎化合物切換 (All / Soft / Medium / Hard / Wet)  
|      | - 門檻調整回饋 (顯示當前門檻資訊)
| 匯出 | 支援圖表截圖與資料 CSV 匯出 |

---

## 🧱 架構設計

### MDI 與元件
- `UniversalAnalysisMDI` 新增「油門箱型圖」子視窗。
- 視窗內容：
  - `UniversalChartWidget` 內嵌 matplotlib。
  - 側邊控制面板 (Qt Widgets)：車手多選、輪胎 filter、排序下拉、門檻顯示。
- API-ONLY 概念：
  - 使用 `UniversalDataLoader` 子類 `ThrottleBoxplotDataLoader` 讀取 function_id 54，優先從 API，其次讀取本地 JSON。
  - 不可呼叫 CLI 進程。

### 資料流程
1. `ThrottleBoxplotDataLoader.fetch_data()`：
   - 呼叫 `/analyze` 帶入 `function_id=54` 與 GUI 參數 (driver list optional)。
   - 接收 JSON 後驗證 schema (`metadata`, `analysis.drivers[].laps[]`).
2. 轉換為 `pandas.DataFrame`：欄位 `driver`, `lap_number`, `full_throttle_duration_s`, `full_throttle_ratio`, `compound`, `lap_time_seconds`, `avg_throttle`, `stint`, `drs_usage`。
3. `ChartController` 處理篩選、群組，更新箱型圖資料集。

---

## 🛠️ 實作步驟 (草案)

1. **資料載入**
   - 建立 `ThrottleBoxplotDataLoader`：繼承 `UniversalDataLoader`。
   - 實作 `_validate_data_format` 確認必要欄位存在。
   - 實作 `_transform_data_for_display` 回傳 DataFrame。

2. **圖表繪製**
   - 在 `ThrottleBoxplotWindow` 中建立 `matplotlib` Figure + Axes。
   - `draw_boxplot(filtered_df)`：
     - 依 car order 排序。
     - 使用 `matplotlib.axes.Axes.boxplot` 或 `seaborn.boxplot` (需評估是否可引入 seaborn)。
     - 套用車隊顏色。
     - 使用 `matplotlib.widgets.Cursor` 或自定 hover 邏輯顯示 tooltip。

3. **互動控制**
   - 車手清單：預設全選，變更時重新繪圖。
   - 群組切換：`None` / `Compound` / `Stint` → 透過 facet 或多圖。
   - 排序選項：`Alphabetical`, `Median Desc`, `Outlier Count`。
   - 匯出：
     - Export PNG → `chart_widget.export_png()`。
     - Export CSV → 過濾後 DataFrame to CSV。

4. **狀態顯示**
   - 顯示使用的油門門檻 (例如「全油門門檻：>=0.90」)。
   - 顯示資料筆數、圈數統計。

---

## ✅ 測試計畫

| 測試項目 | 說明 |
|----------|------|
| API 響應測試 | 模擬 `/analyze function_id=54` 回傳，驗證 loader 正確解析 |
| 空資料處理 | 當某車手無有效圈速時，圖表需顯示提示文本而非崩潰 |
| 群組切換 | 切換不同輪胎/車手組合時箱型圖更新正確 |
| Tooltip | Hover 異常值顯示圈號、圈速無誤且不阻塞 UI |
| 匯出功能 | PNG/CSV 匯出內容與當前篩選狀態一致 |
| i18n | 支援中英文顯示 (使用既有翻譯資源) |

---

## ⚠️ 風險與注意事項

- **資料量大**：若賽事圈數多、車手多，箱型圖繪製時間可能增加；需評估是否預先分組或 lazy loading。
- **顏色一致性**：需沿用現有車隊顏色設定 (`core/team_colors.py` 等)，避免色彩錯亂。
- **API-ONLY**：若 JSON 缺值，GUI 需顯示提醒，引導使用者重新呼叫 API，而非嘗試生成資料。
- **互動穩定性**：大量 hover 事件可能造成卡頓，建議限制 tooltip 為最近點或加快搜尋。

---

## 📌 下一步建議

1. 建立對應的 `tasks/GUI/Throttle_Boxplot_AllDrivers/task.md`，規劃驗收清單。  
2. 與 CLI Function 54 開發者對齊欄位格式，確保 `full_throttle_duration_s` 等欄位命名固定。  
3. 實作 DataLoader 與視窗骨架，預留 chart 更新接口。  
4. 制定單元測試與 GUI 手動測試腳本。  
5. 更新 GUI 使用手冊，介紹該視圖的使用方式。  

---

> 本文件為初版規劃，後續若需求更新，請同步修訂並記錄變更。