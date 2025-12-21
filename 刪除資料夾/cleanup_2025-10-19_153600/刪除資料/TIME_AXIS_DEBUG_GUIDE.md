# 時間軸功能深度追蹤指南

## 📋 測試步驟

1. **啟動 GUI**
   ```powershell
   python f1t_gui_main.py
   ```

2. **開啟速度分析窗口**
   - 設置參數 (例如: 2024, Japan, R, VER vs LEC)
   - 點擊 "Speed Analysis"

3. **勾選 "Use Time Axis" 復選框**

4. **點擊 "Update All Analysis" 按鈕**

5. **觀察終端輸出**

## 🔍 預期的 Debug 輸出流程

### 步驟 1: GUI 主程式讀取復選框
```
🕒 [TIME_AXIS_DEBUG] ========== 時間軸追蹤開始 ==========
🕒 [TIME_AXIS_DEBUG] 步驟 1: 讀取復選框狀態
🕒 [TIME_AXIS_DEBUG]   hasattr(self, 'use_time_axis_checkbox'): True
🕒 [TIME_AXIS_DEBUG]   use_time_axis_checkbox.isChecked(): True
🕒 [TIME_AXIS_DEBUG]   最終 use_time_axis 值: True
```

### 步驟 2: 準備參數字典
```
🕒 [TIME_AXIS_DEBUG] 步驟 2: 準備 telemetry_kwargs
🕒 [TIME_AXIS_DEBUG]   telemetry_kwargs['use_time_axis'] = True
```

### 步驟 3: 調用模組更新方法
```
🕒 [TIME_AXIS_DEBUG] 步驟 3: 調用 update_lap_parameters
🕒 [TIME_AXIS_DEBUG]   use_time_axis 參數值: True
```

### 步驟 4: MDI 接收參數
```
🕒 [TIME_AXIS_DEBUG] 步驟 4: MDI 收到 use_time_axis 參數
🕒 [TIME_AXIS_DEBUG]   use_time_axis 參數值: True
🕒 [TIME_AXIS_DEBUG]   self.use_time_axis 已儲存: True
```

### 步驟 5: MDI 設置圖表模式
```
🕒 [TIME_AXIS_DEBUG] 步驟 5: 準備設置圖表時間軸模式
🕒 [TIME_AXIS_DEBUG]   self.speed_chart_widget 存在: True
🕒 [TIME_AXIS_DEBUG]   hasattr(speed_chart_widget, 'set_time_axis_mode'): True
🕒 [TIME_AXIS_DEBUG]   調用 speed_chart_widget.set_time_axis_mode(True)
🕒 [TIME_AXIS_DEBUG]   ✅ set_time_axis_mode 調用完成
```

### 步驟 6: 圖表組件設置模式
```
🕒 [TIME_AXIS_DEBUG] 步驟 6: SpeedChartWidget.set_time_axis_mode 被調用
🕒 [TIME_AXIS_DEBUG]   接收參數 use_time_axis: True
🕒 [TIME_AXIS_DEBUG]   當前 self.use_time_axis: False
🕒 [TIME_AXIS_DEBUG]   更新後 self.use_time_axis: True
🕒 [TIME_AXIS_DEBUG]   調用 self.repaint() 強制重繪
🕒 [TIME_AXIS_DEBUG]   ✅ set_time_axis_mode 完成
```

### 步驟 7: 繪製 X 軸標題
```
🕒 [TIME_AXIS_DEBUG] 步驟 7: _draw_axes 繪製 X 軸標題
🕒 [TIME_AXIS_DEBUG]   self.use_time_axis: True
🕒 [TIME_AXIS_DEBUG]   繪製時間軸標題: 時間 (s)
```

### 步驟 8: 選擇數據源繪製曲線
```
🕒 [TIME_AXIS_DEBUG] 步驟 8: _draw_speed_curves 選擇數據源
🕒 [TIME_AXIS_DEBUG]   self.use_time_axis: True
🕒 [TIME_AXIS_DEBUG]   driver1_time 長度: 502
🕒 [TIME_AXIS_DEBUG]   driver2_time 長度: 502
🕒 [TIME_AXIS_DEBUG]   distance_data 長度: 502
🕒 [TIME_AXIS_DEBUG]   ✅ 使用時間數據作為 X 軸 (driver1_time)
```

### 步驟 9: 數據更新時提取時間數據
```
🕒 [TIME_AXIS_DEBUG] 步驟 9: update_speed_data 提取時間數據
🕒 [TIME_AXIS_DEBUG]   speed_data 包含 driver1_time_seconds: True
🕒 [TIME_AXIS_DEBUG]   speed_data 包含 driver2_time_seconds: True
🕒 [TIME_AXIS_DEBUG]   driver1_time 點數: 502
🕒 [TIME_AXIS_DEBUG]   driver2_time 點數: 502
```

## ❌ 常見問題診斷

### 問題 1: 復選框狀態未讀取
**症狀**: 步驟 1 輸出 `use_time_axis 值: False`
**原因**: 復選框未正確創建或未勾選
**解決**: 檢查 GUI 是否顯示復選框，確認已勾選

### 問題 2: 參數未傳遞到 MDI
**症狀**: 步驟 3 沒有輸出
**原因**: 
- 速度分析窗口不在 `all_analysis_windows` 列表中
- `analysis_type` 不在 `telemetry_types` 中
**解決**: 檢查模組註冊和分類

### 問題 3: MDI 未調用 set_time_axis_mode
**症狀**: 步驟 4 有輸出，但步驟 5 沒有輸出
**原因**:
- `self.speed_chart_widget` 為 None
- `speed_chart_widget` 沒有 `set_time_axis_mode` 方法
**解決**: 檢查 widget 初始化和方法實現

### 問題 4: 時間數據不存在
**症狀**: 步驟 9 輸出 `driver1_time 點數: 0`
**原因**:
- API 未返回時間數據
- JSON 結構不包含 `driver1_time_seconds` 欄位
**解決**: 檢查 API 響應和 JSON 結構

### 問題 5: 圖表未切換到時間軸
**症狀**: 步驟 6-7 都有輸出，但 X 軸標題仍顯示 "距離 (m)"
**原因**:
- `self.use_time_axis` 在 repaint 前被重置
- 圖表繪製使用了緩存的舊狀態
**解決**: 檢查 `set_time_axis_mode` 後是否有其他代碼覆蓋了 `use_time_axis`

### 問題 6: 使用距離數據而非時間數據
**症狀**: 步驟 8 輸出 `使用距離數據作為 X 軸`
**原因**:
- `self.use_time_axis` 為 False
- `self.driver1_time` 或 `self.driver2_time` 為空
**解決**: 確認步驟 6 正確設置，確認步驟 9 正確提取時間數據

## 🔧 完整追蹤流程圖

```
用戶勾選 "Use Time Axis" ✓
    ↓
[步驟 1] GUI 讀取 isChecked() → use_time_axis = True
    ↓
[步驟 2] 添加到 telemetry_kwargs
    ↓
[步驟 3] 調用 update_lap_parameters(use_time_axis=True)
    ↓
[步驟 4] MDI 儲存 self.use_time_axis = True
    ↓
        MDI 調用 data_manager.load_speed_data()
        ↓
        數據載入完成
        ↓
[步驟 5] MDI 調用 speed_chart_widget.set_time_axis_mode(True)
    ↓
[步驟 6] SpeedChartWidget 設置 self.use_time_axis = True
    ↓
        SpeedChartWidget 調用 self.repaint()
        ↓
        觸發 paintEvent()
        ↓
[步驟 7] _draw_axes() 檢查 self.use_time_axis
    ↓
    if True: 繪製 "時間 (s)"
    if False: 繪製 "距離 (m)"
    ↓
[步驟 8] _draw_speed_curves() 檢查 self.use_time_axis
    ↓
    if True AND driver1_time 存在:
        使用 driver1_time, driver2_time
    else:
        使用 distance_data
    ↓
    繪製速度曲線
```

## 📝 Debug 輸出過濾

如果終端輸出過多，可以使用以下命令過濾時間軸相關輸出:

```powershell
# Windows PowerShell
python f1t_gui_main.py 2>&1 | Select-String "TIME_AXIS_DEBUG"
```

## 🎯 測試檢查清單

- [ ] 步驟 1: 復選框狀態正確讀取為 True
- [ ] 步驟 2: telemetry_kwargs 包含 use_time_axis=True
- [ ] 步驟 3: update_lap_parameters 接收到參數
- [ ] 步驟 4: MDI 正確儲存參數
- [ ] 步驟 5: MDI 調用 set_time_axis_mode
- [ ] 步驟 6: SpeedChartWidget 更新 use_time_axis
- [ ] 步驟 7: X 軸標題顯示 "時間 (s)"
- [ ] 步驟 8: 使用時間數據繪製曲線
- [ ] 步驟 9: 時間數據正確提取 (502 點)

全部通過 ✓ = 功能正常運作
任一失敗 ✗ = 定位該步驟進行修復
