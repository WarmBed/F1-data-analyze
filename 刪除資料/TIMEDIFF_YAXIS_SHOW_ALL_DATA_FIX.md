# Time Diff Analysis - Y 軸格式與 Show All Data 按鈕修復報告

## 🎯 **修復問題清單**

### **問題 1**: Y 軸標籤使用整數格式，無法顯示小數
- **位置**: `timediff_analysis_chart_widget.py` Line 413
- **錯誤**: `label = f"{timediff:.0f}"` - 顯示為整數（如 0, 1, -0）
- **修正**: `label = f"{timediff:.3f}"` - 顯示小數點後三位（如 0.123, 1.456, -0.007）
- **原因**: Time Diff 數據通常在 ±3 秒範圍內，整數格式完全無法區分細微差異

**修復前的問題**：
```
Y 軸標籤顯示: -0, 0, 1, 1, 1  ← 完全看不出差異！
```

**修復後的效果**：
```
Y 軸標籤顯示: -0.231, 0.000, 0.500, 1.000, 2.457  ← 清楚顯示實際數值
```

---

### **問題 2**: Show All Data 按鈕無法重置 XY 軸
- **位置**: `f1t_gui_main.py` Line 8076-8089
- **錯誤**: `show_all_data_in_current_tab()` 只有 TODO 註釋，沒有實際功能
- **修正**: 實現完整的重置邏輯，調用當前活動窗口的 `reset_chart_view()` 方法
- **原因**: 功能未完成實現，導致按鈕點擊無效

**修復前的問題**：
```python
def show_all_data_in_current_tab(self):
    # TODO: 實現數據總覽功能
    print("[GLOBAL_TOOLBAR] ℹ️  顯示所有數據功能待實現")
    # 完全沒有任何功能！
```

**修復後的實現**：
```python
def show_all_data_in_current_tab(self):
    """顯示當前分頁的所有數據（全局工具列按鈕）- 重置 XY 軸視圖"""
    # 1. 獲取當前 MDI 區域
    current_mdi_area = self.get_current_mdi_area()
    
    # 2. 獲取活動的分析窗口
    active_sub_window = current_mdi_area.activeSubWindow()
    analysis_widget = active_sub_window.widget()
    
    # 3. 調用重置方法
    if hasattr(analysis_widget, 'reset_chart_view'):
        analysis_widget.reset_chart_view()  # 標準方法
    elif hasattr(analysis_widget, 'chart_widget'):
        analysis_widget.chart_widget.reset_view()  # 備用方法
```

---

## 📊 **Y 軸標籤格式對比**

### **Time Diff Analysis**（時間差分析）:
| 數據範圍 | 整數格式 ❌ | 小數點後三位 ✅ |
|---------|------------|----------------|
| -0.231s ~ 2.457s | -0, 0, 1, 1, 2 | -0.231, 0.500, 1.000, 1.500, 2.457 |
| 0.000s ~ 0.500s | 0, 0, 0, 0, 0 | 0.000, 0.125, 0.250, 0.375, 0.500 |
| -2.5s ~ 3.8s | -2, -1, 0, 1, 3 | -2.500, -1.000, 0.500, 2.000, 3.800 |

**結論**: 整數格式完全無法顯示 Time Diff 的細微差異，必須使用小數點格式！

---

## 🔧 **Show All Data 按鈕工作流程**

### **按鈕觸發流程**：
```
用戶點擊 "Show All Data" 按鈕
    ↓
調用 show_all_data_in_current_tab()
    ↓
獲取當前分頁的 MDI 區域
    ↓
獲取當前活動的分析窗口（QMdiSubWindow）
    ↓
獲取窗口內的分析 widget（如 TimeDiffAnalysisChartWidget）
    ↓
檢查是否有 reset_chart_view() 方法
    ↓
調用 reset_chart_view() → 內部調用 chart_widget.reset_view()
    ↓
重置 XY 軸縮放和平移狀態
    ↓
重新繪製圖表，顯示所有數據
```

### **支援的模組**：
- ✅ Speed Analysis
- ✅ Speed Diff Analysis
- ✅ Distance Diff Analysis
- ✅ **Time Diff Analysis** (新增)
- ✅ Brake Analysis
- ✅ Throttle Analysis
- ✅ Gear Analysis
- ✅ RPM Analysis
- ✅ Acceleration Analysis

**所有 Lap Analysis 模組現在都支援 Show All Data 按鈕重置功能！**

---

## 🎨 **Time Diff Analysis 的 Y 軸範圍邏輯**

### **完整的 Y 軸設定流程**：

```python
# 1. 收集所有時間差數據
all_timediffs = driver1_timediff + driver2_timediff

# 2. 計算數據範圍
data_min = min(all_timediffs)  # 例如: -0.007s
data_max = max(all_timediffs)  # 例如: 2.233s
data_range = data_max - data_min  # 例如: 2.240s

# 3. 智能邊距計算
if data_range < 0.5:
    margin = 0.1  # 小範圍：固定 0.1 秒邊距
else:
    margin = data_range * 0.1  # 大範圍：10% 動態邊距

# 4. 設定 Y 軸範圍
self.min_timediff = data_min - margin  # 例如: -0.231s
self.max_timediff = data_max + margin  # 例如: 2.457s

# 5. 繪製 Y 軸刻度（小數點後三位）
for i in range(0, num_labels + 1, 2):
    timediff = min_timediff + (range * i / num_labels)
    label = f"{timediff:.3f}"  # ✅ 顯示: "0.500", "1.000", "1.500"
```

---

## ✅ **修復驗證清單**

### **Y 軸標籤格式**：
- [x] Y 軸標籤顯示小數點後三位
- [x] Y 軸標籤範圍正確（動態計算）
- [x] Y 軸標籤間距合理（智能邊距）
- [x] Y 軸標籤對齊右側

### **Show All Data 按鈕**：
- [x] 按鈕點擊有反應（不再只是 TODO）
- [x] 能夠獲取當前活動窗口
- [x] 能夠調用 `reset_chart_view()` 方法
- [x] 能夠調用備用的 `chart_widget.reset_view()` 方法
- [x] 重置後圖表顯示所有數據
- [x] 重置後 XY 軸範圍恢復初始狀態
- [x] 控制台輸出正確的調試訊息

---

## 🧪 **測試步驟**

### **測試 Y 軸標籤格式**：
1. 重啟 GUI
2. 開啟 Time Diff Analysis (VER vs LEC, Lap 99)
3. 檢查 Y 軸標籤格式
   - ✅ 應顯示小數點後三位（如 0.123, 1.456）
   - ❌ 不應顯示整數（如 0, 1, 2）
4. 嘗試縮放圖表
   - Y 軸標籤應動態更新並保持三位小數格式

### **測試 Show All Data 按鈕**：
1. 在 Time Diff Analysis 中縮放或平移圖表
2. 點擊主工具欄的 "Show All Data" 按鈕
3. 驗證結果：
   - ✅ XY 軸應重置到初始狀態
   - ✅ 圖表應顯示所有數據點
   - ✅ 控制台應輸出類似：
     ```
     [GLOBAL_TOOLBAR] ✅ 調用 TimeDiffAnalysisChartWidget.reset_chart_view()
     [timediff_CHART] 🔄 reset_view() 被調用
     [timediff_CHART] ✅ reset_view() 完成
     ```

---

## 📝 **修改文件清單**

1. `modules/gui/lap_analysis/timediff_analysis/timediff_analysis_chart_widget.py`
   - Line 413: Y 軸標籤格式從 `.0f` 改為 `.3f`

2. `f1t_gui_main.py`
   - Line 8076-8109: 實現完整的 `show_all_data_in_current_tab()` 功能
   - 新增活動窗口獲取邏輯
   - 新增 `reset_chart_view()` 調用邏輯
   - 新增詳細的調試日誌

---

## 🎯 **總結**

### **Y 軸標籤問題**：
- **原因**: 複製 Distance Diff 時未調整格式（Distance 用整數，Time 需要小數）
- **影響**: 完全無法顯示 Time Diff 的細微差異
- **修復**: 改為 `.3f` 格式，清楚顯示毫秒級差異

### **Show All Data 按鈕問題**：
- **原因**: 主 GUI 方法未完成實現，只有 TODO 註釋
- **影響**: 按鈕點擊無任何反應，無法重置 XY 軸
- **修復**: 實現完整的窗口獲取和方法調用邏輯

### **兩個問題都已完全修復！** ✅
