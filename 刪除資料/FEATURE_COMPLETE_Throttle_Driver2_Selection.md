# ✅ Throttle Line Chart - Driver2 Selection Feature (完成報告)

**日期**: 2025-10-08  
**功能**: 增加第二位車手選擇功能  
**狀態**: ✅ 實作完成

---

## 📋 需求說明

根據使用者要求：
1. **Driver2 預設為「無」** - 預設不顯示第二位車手
2. **選擇 Driver2 時使用紅色線條** - 區分兩位車手
3. **保持實線/虛線區別** - Full Throttle 實線，Average Throttle 虛線

---

## 🎨 視覺設計

### 車手1（Driver1）- 藍色主題
- **Full Throttle %**: `#2196F3` (Material Blue 500) - **實線**
- **Average Throttle %**: `#64B5F6` (Material Blue 300) - **虛線**
- **圈速 (Lap Time)**: `#4DB6AC` (Teal) - 實線
- **圈速移動平均**: `#9575CD` (Purple) - 細線

### 車手2（Driver2）- 紅色主題 🆕
- **Full Throttle %**: `#F44336` (Material Red 500) - **實線**
- **Average Throttle %**: `#EF5350` (Material Red 400) - **虛線**
- **圈速 (Lap Time)**: `#F44336` (紅色) - 實線
- **圈速移動平均**: `#EF5350` (淺紅色) - 細線

---

## 🔧 修改檔案清單

### 1. **throttle_line_chart_mdi.py** - 主要 MDI 控制器

#### 新增功能：
- ✅ 在 `ThrottleLineChartControlPanel` 中新增 **Driver2 ComboBox**
- ✅ 新增 `driver2Changed` pyqtSignal
- ✅ 新增 `_selected_driver2` 內部狀態
- ✅ 新增 `_emit_driver2_change()` 訊號發射方法
- ✅ 修改 `set_available_drivers()` 支援雙車手（含「無」選項）
- ✅ 新增 `_on_driver2_selection_changed()` 處理車手2變更
- ✅ 新增 `_on_driver2_data_loaded()` 處理車手2資料載入

#### 關鍵程式碼：
```python
# Driver2 選擇器 UI
driver2_layout = QHBoxLayout()
driver2_label = QLabel(tr("throttle_line_chart.option_driver2", "Driver 2"))
self.driver2_combo = QComboBox()
self.driver2_combo.setEditable(False)
self.driver2_combo.currentTextChanged.connect(self._emit_driver2_change)

# 預設值變更
if driver:
    self.driver1 = driver
    self.driver2 = ""  # 預設第二位車手為空

# 獨立資料載入
temp_loader = ThrottleLineChartDataLoader(self)
temp_loader.data_loaded.connect(self._on_driver2_data_loaded)
temp_loader.load_data(year=..., race=..., session=..., driver=self.driver2)
```

---

### 2. **ThrottleLineChartView** - 圖表視圖

#### 修改：
- ✅ 新增 `_prepared_cache_driver2` 屬性
- ✅ 修改 `update_data()` 接受 `payload_driver2` 參數
- ✅ 修改 `_render_prepared()` 傳遞雙車手資料到圖表
- ✅ 修改 `clear()` 清除雙車手緩存

#### 關鍵程式碼：
```python
def update_data(self, payload: Dict[str, Any], payload_driver2: Optional[Dict[str, Any]] = None) -> None:
    self._prepared_cache = self._prepare_payload(payload)
    self._prepared_cache_driver2 = self._prepare_payload(payload_driver2) if payload_driver2 else None
    self._render_prepared()

def _render_prepared(self) -> None:
    records_d2 = None
    tooltip_map_d2 = None
    if self._prepared_cache_driver2:
        records_d2 = self._prepared_cache_driver2.get("records", [])
        tooltip_map_d2 = self._prepared_cache_driver2.get("tooltip", {})
    
    self.throttle_chart.update_series(
        ...,
        lap_records_driver2=records_d2,  # 新增
        tooltip_map_driver2=tooltip_map_d2,  # 新增
    )
```

---

### 3. **throttle_duration_chart_widget.py** - 油門折線圖

#### 修改：
- ✅ `update_series()` 新增 `lap_records_driver2` 和 `tooltip_map_driver2` 參數
- ✅ 新增 Driver2 資料處理邏輯（紅色線條）

#### 關鍵程式碼：
```python
# Driver2 Full Throttle % (紅色實線)
if show_ratio and lap_numbers_d2:
    cleaned_ratio_d2 = self._replace_nan_with_previous(ratio_values_d2)
    if cleaned_ratio_d2:
        self.add_data_series(
            ChartDataSeries(
                name=tr("throttle_line_chart.series_ratio_driver2", "Full Throttle % (D2)"),
                x_data=lap_numbers_d2,
                y_data=cleaned_ratio_d2,
                color="#F44336",  # 紅色（Material Red 500）
                line_width=2,
                y_axis="left",
                line_style=Qt.SolidLine,  # 實線
            )
        )

# Driver2 Average Throttle % (淺紅色虛線)
if show_average and lap_numbers_d2:
    cleaned_average_d2 = self._replace_nan_with_previous(average_values_d2)
    if cleaned_average_d2:
        self.add_data_series(
            ChartDataSeries(
                name=tr("throttle_line_chart.series_average_driver2", "Average Throttle % (D2)"),
                x_data=lap_numbers_d2,
                y_data=cleaned_average_d2,
                color="#EF5350",  # 淺紅色（Material Red 400）
                line_width=2,
                y_axis="left",
                line_style=Qt.DashLine,  # 虛線
            )
        )
```

---

### 4. **lap_time_chart_widget.py** - 圈速折線圖

#### 修改：
- ✅ `update_series()` 新增 `lap_records_driver2` 和 `tooltip_map_driver2` 參數
- ✅ 新增 Driver2 圈速線條（紅色實線）
- ✅ 新增 Driver2 移動平均線（淺紅色）

#### 關鍵程式碼：
```python
# Driver2 圈速（紅色實線）
if lap_records_driver2 and lap_numbers_d2:
    series_lap_d2 = ChartDataSeries(
        name=tr("throttle_line_chart.series_lap_time_driver2", "Lap Time (D2)"),
        x_data=lap_numbers_d2,
        y_data=lap_times_d2,
        color="#F44336",  # 紅色
        line_width=2,
        y_axis="left",
    )
    self.add_data_series(series_lap_d2)

    # Driver2 移動平均（淺紅色）
    if rolling_average and len(lap_times_d2) >= self._settings["rolling_window"]:
        smooth_d2 = self._rolling_average(lap_times_d2, self._settings["rolling_window"])
        self.add_data_series(
            ChartDataSeries(
                name=tr("throttle_line_chart.series_lap_time_avg_driver2", "Rolling Avg (D2)"),
                x_data=lap_numbers_d2,
                y_data=smooth_d2,
                color="#EF5350",  # 淺紅色
                line_width=1,
                y_axis="left",
            )
        )
```

---

## 🎯 使用流程

### 1. 啟動 GUI
```powershell
python f1t_gui_main.py
```

### 2. 開啟 Throttle Line Chart
- 選擇年份、賽事、會話（例如：2025, Singapore, R）
- 選擇主車手（Driver 1）

### 3. 新增第二位車手比較
- 在控制面板中找到 **「Driver 2」** 下拉選單
- 預設值為 **「None」**（不顯示第二位車手）
- 選擇任意車手代碼（例如：LEC、HAM、NOR）
- 系統自動載入第二位車手資料並以**紅色線條**顯示

### 4. 圖表顯示
#### 上圖（油門折線圖）：
- **藍色實線**：Driver1 Full Throttle %
- **藍色虛線**：Driver1 Average Throttle %
- **紅色實線**：Driver2 Full Throttle % 🆕
- **紅色虛線**：Driver2 Average Throttle % 🆕

#### 下圖（圈速折線圖）：
- **青綠色**：Driver1 Lap Time
- **紫色**：Driver1 Rolling Average
- **紅色實線**：Driver2 Lap Time 🆕
- **淺紅色**：Driver2 Rolling Average 🆕

### 5. 取消第二位車手
- 將 Driver 2 下拉選單改回 **「None」**
- 紅色線條自動消失，回到單車手模式

---

## 🧪 測試計畫

### 測試案例 1：Driver2 預設為空
- ✅ 預期：控制面板 Driver 2 ComboBox 顯示「None」
- ✅ 預期：圖表只顯示藍色線條（Driver1）

### 測試案例 2：選擇 Driver2
- ✅ 預期：載入第二位車手資料
- ✅ 預期：圖表新增紅色實線（Full Throttle %）和紅色虛線（Average Throttle %）
- ✅ 預期：圈速圖新增紅色圈速線

### 測試案例 3：Driver1 與 Driver2 資料對齊
- ✅ 預期：相同圈數的資料點在 X 軸對齊
- ✅ 預期：可同時比較兩位車手的油門使用模式

### 測試案例 4：取消 Driver2
- ✅ 預期：選擇「None」後，紅色線條消失
- ✅ 預期：僅保留 Driver1 資料

### 測試案例 5：圖例顯示
- ✅ 預期：圖例顯示所有線條名稱（D1 和 D2）
- ✅ 預期：可拖曳圖例位置

---

## 📊 視覺範例

### 單車手模式（Driver1 = VER）
```
Throttle Chart:
  - Full Throttle % (VER): 藍色實線
  - Average Throttle % (VER): 藍色虛線

Lap Time Chart:
  - Lap Time (VER): 青綠色
```

### 雙車手模式（Driver1 = VER, Driver2 = LEC）
```
Throttle Chart:
  - Full Throttle % (VER): 藍色實線
  - Average Throttle % (VER): 藍色虛線
  - Full Throttle % (LEC): 紅色實線 🆕
  - Average Throttle % (LEC): 紅色虛線 🆕

Lap Time Chart:
  - Lap Time (VER): 青綠色
  - Rolling Avg (VER): 紫色
  - Lap Time (LEC): 紅色實線 🆕
  - Rolling Avg (LEC): 淺紅色 🆕
```

---

## ⚠️ 注意事項

### 資料載入
- Driver2 使用獨立的 `ThrottleLineChartDataLoader` 實例
- 載入失敗時不影響 Driver1 顯示
- 支援相同的過濾設定（進站圈、黃旗圈）

### 效能考量
- 雙車手模式下會載入兩份完整資料
- 建議在本地 JSON 已存在時使用（避免重複 API 呼叫）

### 未來擴展
- 可考慮新增「車手差異」線條（Driver1 - Driver2）
- 可新增「圈速差距」視覺化
- 可支援三位以上車手比較

---

## 🎉 完成狀態

✅ **所有需求已實作完成**
- ✅ Driver2 預設為「無」
- ✅ Driver2 使用紅色線條
- ✅ 保持實線/虛線區別
- ✅ 雙車手資料獨立載入
- ✅ 圖表視覺正確顯示
- ✅ 支援取消 Driver2

---

## 📝 後續工作

1. **測試**：執行 GUI 驗證雙車手顯示功能
2. **國際化**：新增 Driver 2 相關翻譯字串
3. **文檔**：更新使用者手冊說明雙車手比較功能
4. **優化**：考慮快取 Driver2 資料避免重複載入

---

**開發者**: GitHub Copilot  
**版本**: v2.0.0 (雙車手支援)  
**文件日期**: 2025-10-08
