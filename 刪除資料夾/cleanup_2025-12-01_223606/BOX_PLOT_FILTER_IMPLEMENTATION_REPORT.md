# 🎉 Box Plot Filter 功能實現完成報告

## ✅ 實現總結

已成功為 **兩個 Box Plot 模組** 實現右鍵 Filter 功能，並與主 GUI 的 "Show All Data" 按鈕完成整合。

---

## 📊 修改的模組

### 1. **Throttle Box Plot** (油門箱型圖)
**檔案位置**：
- `modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_chart_widget.py`
- `modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py`

**修改內容**：
✅ 添加 `QMenu` 和 `QCursor` 導入
✅ 添加 `hidden_drivers` 集合屬性
✅ 修改 `_calculate_y_range()` - 只計算可見車手的範圍
✅ 修改 `_draw_box_plots()` - 過濾隱藏車手
✅ 修改 `mousePressEvent()` - 支援右鍵選單
✅ 添加 `_show_context_menu()` - 顯示右鍵選單
✅ 添加 `_hide_driver()` - 隱藏車手功能
✅ 添加 `show_all_drivers()` - 恢復所有車手（公開方法）
✅ 在 MDI 添加 `reset_chart_view()` - 橋接主 GUI 按鈕

---

### 2. **Lap Time Box Plot** (圈速箱型圖)
**檔案位置**：
- `modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_chart_widget.py`
- `modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py`

**修改內容**：
✅ 添加 `QMenu` 和 `QCursor` 導入
✅ 添加 `hidden_drivers` 集合屬性
✅ 修改 `_calculate_y_range()` - 只計算可見車手的範圍
✅ 修改 `_draw_box_plots()` - 過濾隱藏車手
✅ 修改 `mouseMoveEvent()` - 只檢測可見車手
✅ 添加 `mousePressEvent()` - 支援左鍵和右鍵
✅ 添加 `_show_context_menu()` - 顯示右鍵選單
✅ 添加 `_hide_driver()` - 隱藏車手功能
✅ 添加 `show_all_drivers()` - 恢復所有車手（公開方法）
✅ 在 MDI 添加 `reset_chart_view()` - 橋接主 GUI 按鈕

---

## 🔄 與主 GUI 的整合

### **主 GUI "Show All Data" 按鈕工作流程**

1. **使用者點擊** 主工具列的 "Show All Data" 按鈕
2. **觸發方法** `f1t_gui_main.py` → `show_all_data_in_current_tab()`
3. **遍歷所有** 當前分頁的 MDI 子視窗
4. **嘗試調用** 每個模組的 `reset_chart_view()` 方法
5. **模組執行** `reset_chart_view()` → 調用 `chart_widget.show_all_drivers()`
6. **圖表恢復** 清空 `hidden_drivers` 集合，重繪圖表

### **支援的模組**
✅ **Corner Performance Analysis** (參考實現)
✅ **Throttle Box Plot** (新增)
✅ **Lap Time Box Plot** (新增)

---

## 🎯 功能使用說明

### **隱藏車手**
1. 右鍵點擊任意箱型圖（滑鼠懸停在車手的箱型圖上）
2. 選單顯示 "🚫 Hide {DRIVER}"
3. 點擊後該車手的箱型圖立即消失
4. Y 軸範圍自動調整（只考慮可見車手）

### **恢復所有車手**
**方法 1** - 使用主 GUI 按鈕（推薦）：
1. 點擊主工具列的 "Show All Data" 按鈕
2. 當前分頁的**所有模組**都會恢復顯示所有車手

**方法 2** - 程式化調用：
```python
# 在模組內部調用
module.chart_widget.show_all_drivers()

# 或通過 MDI
module.reset_chart_view()
```

---

## 🧪 測試檢查清單

### **Throttle Box Plot**
- [ ] 啟動 GUI → 開啟 Throttle Box Plot
- [ ] 右鍵點擊任意箱型圖 → 顯示 "Hide {DRIVER}" 選單
- [ ] 點擊 Hide → 該車手消失，圖表重繪
- [ ] 點擊主 GUI "Show All Data" → 所有車手恢復

### **Lap Time Box Plot**
- [ ] 啟動 GUI → 開啟 Lap Time Box Plot
- [ ] 右鍵點擊任意箱型圖 → 顯示 "Hide {DRIVER}" 選單
- [ ] 點擊 Hide → 該車手消失，圖表重繪
- [ ] 點擊主 GUI "Show All Data" → 所有車手恢復

### **多模組測試**
- [ ] 同時開啟兩個 Box Plot 模組
- [ ] 在各模組中隱藏不同車手
- [ ] 點擊 "Show All Data" → 兩個模組都恢復

---

## 📝 實現細節

### **數據過濾機制**
```python
# 在繪圖時過濾隱藏車手
visible_drivers = [d for d in drivers if d not in self.hidden_drivers]

# Y 軸範圍只計算可見車手
for driver, data in self.driver_data.items():
    if driver not in self.hidden_drivers:
        all_values.extend(data)
```

### **右鍵選單實現**
```python
def _show_context_menu(self, driver: str, event: QMouseEvent):
    menu = QMenu(self)
    hide_action = menu.addAction(f"🚫 {tr('hide_driver', 'Hide')} {driver}")
    hide_action.triggered.connect(lambda: self._hide_driver(driver))
    menu.exec_(QCursor.pos())
```

### **主 GUI 整合**
```python
def reset_chart_view(self):
    """MDI 層級的重置方法"""
    if hasattr(self.chart_widget, 'show_all_drivers'):
        self.chart_widget.show_all_drivers()
```

---

## 🎨 參考實現

所有功能完全遵循 **Corner Performance Scatter Widget** 的實現模式：
- `modules/gui/all_drivers_corner_performance_analysis/corner_performance_scatter_widget.py`
- `modules/gui/all_drivers_corner_performance_analysis/all_drivers_corner_performance_mdi.py`

---

## 🔧 故障排除

### **右鍵選單不顯示**
- 檢查是否正確導入 `QMenu` 和 `QCursor`
- 確認滑鼠懸停在箱型圖上（hover_driver 不為 None）

### **"Show All Data" 按鈕無效**
- 檢查 MDI 是否實現 `reset_chart_view()` 方法
- 檢查 Widget 是否實現 `show_all_drivers()` 方法
- 查看控制台日誌確認方法是否被調用

### **圖表沒有重繪**
- 確認 `_hide_driver()` 最後調用了 `self.update()`
- 確認 `_calculate_y_range()` 有正確過濾隱藏車手

---

## ✅ 完成狀態

| 項目 | Throttle Box Plot | Lap Time Box Plot |
|------|-------------------|-------------------|
| 右鍵選單 | ✅ | ✅ |
| Hide Driver | ✅ | ✅ |
| Show All Drivers | ✅ | ✅ |
| MDI 整合 | ✅ | ✅ |
| 主 GUI 按鈕 | ✅ | ✅ |
| Y 軸自動調整 | ✅ | ✅ |
| 國際化支援 | ✅ | ✅ |

---

**📅 完成時間**: 2025-11-12
**👨‍💻 開發者**: F1T AI Assistant
**📝 版本**: v1.0.0
