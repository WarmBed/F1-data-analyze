# 時間軸功能修復報告

## 🔍 問題診斷

通過深度追蹤 debug 輸出，發現了兩個關鍵問題導致時間軸功能無法工作。

### 問題 1: `SpeedAnalysisModule.update_lap_parameters()` 缺少參數

**症狀**:
```
⚠️ WARNING: update_lap_parameters 參數不匹配: 
SpeedAnalysisModule.update_lap_parameters() got an unexpected keyword argument 'use_time_axis'
```

**原因**:
- GUI 主程式正確讀取了復選框狀態 (`use_time_axis = True`) ✅
- GUI 正確將參數添加到 `telemetry_kwargs` ✅
- 但 `SpeedAnalysisModule` 類別中的 `update_lap_parameters()` 方法**沒有 `use_time_axis` 參數** ❌
- 系統改為調用 `update_parameters()`，但該方法也沒有處理 `use_time_axis`

**修復位置**: `modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py` 第 912 行

**修復前**:
```python
def update_lap_parameters(self, year: str, race: str, session: str,
                        driver1: str, driver2: str = None,
                        lap1: int = 1, lap2: int = None,
                        is_fastest: bool = False) -> bool:
```

**修復後**:
```python
def update_lap_parameters(self, year: str, race: str, session: str,
                        driver1: str, driver2: str = None,
                        lap1: int = 1, lap2: int = None,
                        is_fastest: bool = False, use_time_axis: bool = False) -> bool:
    # 儲存時間軸設定
    self.use_time_axis = use_time_axis
    
    # ... 數據載入 ...
    
    # 數據載入成功後設置圖表模式
    if success and self.speed_chart_widget:
        self.speed_chart_widget.set_time_axis_mode(use_time_axis)
```

---

### 問題 2: API 時間數據未傳遞到 GUI

**症狀**:
```
🕒 [TIME_AXIS_DEBUG]   speed_data 包含 driver1_time_seconds: False
🕒 [TIME_AXIS_DEBUG]   speed_data 包含 driver2_time_seconds: False
🕒 [TIME_AXIS_DEBUG]   driver1_time 點數: 0
🕒 [TIME_AXIS_DEBUG]   driver2_time 點數: 0
```

**但 API 確實返回了時間數據**:
```
[SPEED DEBUG] 常規遙測原始數據鍵值: ['name', 'driver1_data', 'driver2_data', 'distance', 'driver1_time_seconds', 'driver2_time_seconds', 'time_reference']
[SPEED DEBUG] 距離數據點數: 500
[SPEED DEBUG] 車手1數據點數: 500
[SPEED DEBUG] 車手2數據點數: 500
```

**原因**:
- API 正確返回了時間數據 (`driver1_time_seconds`, `driver2_time_seconds`) ✅
- 但在 `telemetry_data_loader_base.py` 的數據處理邏輯中，只提取了 `distance`、`driver1_data`、`driver2_data` ❌
- 時間數據被丟棄，沒有傳遞到 GUI

**修復位置**: `modules/gui/lap_analysis/telemetry_data_loader_base.py` 第 1429 行

**修復前**:
```python
else:
    # 常規遙測數據結構
    processed_data[data_key] = {
        "distance": telemetry_raw.get('distance', []),
        f"driver1_{self.telemetry_type}": telemetry_raw.get('driver1_data', []),
        f"driver2_{self.telemetry_type}": telemetry_raw.get('driver2_data', []),
        "driver1_name": metadata.get('driver1', comparison_info.get('driver1', 'UNK')),
        "driver2_name": metadata.get('driver2', comparison_info.get('driver2', 'UNK'))
    }
```

**修復後**:
```python
else:
    # 常規遙測數據結構
    processed_data[data_key] = {
        "distance": telemetry_raw.get('distance', []),
        f"driver1_{self.telemetry_type}": telemetry_raw.get('driver1_data', []),
        f"driver2_{self.telemetry_type}": telemetry_raw.get('driver2_data', []),
        "driver1_time_seconds": telemetry_raw.get('driver1_time_seconds', []),  # 🆕
        "driver2_time_seconds": telemetry_raw.get('driver2_time_seconds', []),  # 🆕
        "driver1_name": metadata.get('driver1', comparison_info.get('driver1', 'UNK')),
        "driver2_name": metadata.get('driver2', comparison_info.get('driver2', 'UNK'))
    }
    
    # 🆕 Debug: 顯示時間數據提取結果
    self._debug(f"🕒 [TIME_AXIS_DEBUG] 提取時間數據:")
    self._debug(f"🕒 [TIME_AXIS_DEBUG]   driver1_time_seconds 點數: {len(telemetry_raw.get('driver1_time_seconds', []))}")
    self._debug(f"🕒 [TIME_AXIS_DEBUG]   driver2_time_seconds 點數: {len(telemetry_raw.get('driver2_time_seconds', []))}")
```

---

## 📋 修復清單

### 已修復的檔案

1. **`modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py`**
   - ✅ 第 912 行：`SpeedAnalysisModule.update_lap_parameters()` 添加 `use_time_axis` 參數
   - ✅ 第 925 行：儲存 `self.use_time_axis = use_time_axis`
   - ✅ 第 959 行：數據載入成功後調用 `self.speed_chart_widget.set_time_axis_mode(use_time_axis)`

2. **`modules/gui/lap_analysis/telemetry_data_loader_base.py`**
   - ✅ 第 1429 行：提取並傳遞時間數據 (`driver1_time_seconds`, `driver2_time_seconds`)
   - ✅ 添加 debug 輸出顯示時間數據點數

### 之前已完成的修改（保持不變）

3. **`f1t_gui_main.py`**
   - ✅ 復選框創建和狀態讀取
   - ✅ 參數傳遞到 `telemetry_kwargs`

4. **`modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py`**
   - ✅ `SpeedChartWidget.set_time_axis_mode()` 方法
   - ✅ `set_speed_data()` 接收時間參數
   - ✅ `_draw_axes()` 切換 X 軸標題
   - ✅ `_draw_speed_curves()` 選擇數據源
   - ✅ `update_speed_data()` 提取時間數據

---

## 🎯 完整數據流（修復後）

```
1. 用戶勾選 "Use Time Axis" ✓
   ↓
2. GUI 讀取 use_time_axis = True ✓
   ↓
3. GUI 調用 SpeedAnalysisModule.update_lap_parameters(use_time_axis=True) ✓
   ↓
4. SpeedAnalysisModule 儲存 self.use_time_axis = True ✓ [新修復]
   ↓
5. SpeedAnalysisModule 調用 load_data()
   ↓
6. API 返回數據（包含 driver1_time_seconds, driver2_time_seconds）✓
   ↓
7. telemetry_data_loader_base 提取時間數據到 processed_data ✓ [新修復]
   ↓
8. 數據載入成功，SpeedAnalysisModule 調用 speed_chart_widget.set_time_axis_mode(True) ✓ [新修復]
   ↓
9. SpeedChartWidget 設置 self.use_time_axis = True ✓
   ↓
10. update_speed_data() 從 speed_data 提取時間數據 ✓（現在應該有數據了）
   ↓
11. _draw_axes() 繪製 "時間 (s)" X 軸標題 ✓
   ↓
12. _draw_speed_curves() 使用時間數據繪製曲線 ✓
```

---

## 🧪 預期測試結果

重新測試時，應該看到以下 debug 輸出：

### 步驟 1-3: GUI 參數傳遞（應該與之前相同）
```
🕒 [TIME_AXIS_DEBUG] 步驟 1: 讀取復選框狀態
🕒 [TIME_AXIS_DEBUG]   use_time_axis_checkbox.isChecked(): True
🕒 [TIME_AXIS_DEBUG]   最終 use_time_axis 值: True
```

### 步驟 4: MDI 接收參數（新增 - 不再出現錯誤）
```
🔍 [BATCH_DEBUG] 嘗試調用 update_lap_parameters
🕒 [TIME_AXIS_DEBUG] 步驟 4: SpeedAnalysisModule.update_lap_parameters 接收參數
🕒 [TIME_AXIS_DEBUG]   use_time_axis 參數值: True
🕒 [TIME_AXIS_DEBUG]   self.use_time_axis 已儲存: True
🔍 [BATCH_DEBUG] update_lap_parameters 返回: True  ← 不再出現 TypeError
```

### 步驟 5: 設置圖表模式（新增）
```
🕒 [TIME_AXIS_DEBUG] 步驟 5: SpeedAnalysisModule 準備設置圖表時間軸模式
🕒 [TIME_AXIS_DEBUG]   self.speed_chart_widget 存在: True
🕒 [TIME_AXIS_DEBUG]   調用 speed_chart_widget.set_time_axis_mode(True)
🕒 [TIME_AXIS_DEBUG]   ✅ set_time_axis_mode 調用完成
```

### 步驟 6: SpeedChartWidget 接收模式設置（新增）
```
🕒 [TIME_AXIS_DEBUG] 步驟 6: SpeedChartWidget.set_time_axis_mode 被調用
🕒 [TIME_AXIS_DEBUG]   接收參數 use_time_axis: True
🕒 [TIME_AXIS_DEBUG]   更新後 self.use_time_axis: True
```

### 步驟 7: X 軸標題切換（應該切換到時間軸）
```
🕒 [TIME_AXIS_DEBUG] 步驟 7: _draw_axes 繪製 X 軸標題
🕒 [TIME_AXIS_DEBUG]   self.use_time_axis: True  ← 現在應該是 True
🕒 [TIME_AXIS_DEBUG]   繪製時間軸標題: 時間 (s)  ← 現在應該顯示時間
```

### 步驟 8: 數據源選擇（應該使用時間數據）
```
🕒 [TIME_AXIS_DEBUG] 步驟 8: _draw_speed_curves 選擇數據源
🕒 [TIME_AXIS_DEBUG]   self.use_time_axis: True
🕒 [TIME_AXIS_DEBUG]   driver1_time 長度: 500  ← 現在應該有數據
🕒 [TIME_AXIS_DEBUG]   driver2_time 長度: 500  ← 現在應該有數據
🕒 [TIME_AXIS_DEBUG]   ✅ 使用時間數據作為 X 軸 (driver1_time)
```

### 步驟 9: 時間數據提取（新增 - 應該成功）
```
🕒 [TIME_AXIS_DEBUG] 步驟 9: update_speed_data 提取時間數據
🕒 [TIME_AXIS_DEBUG]   speed_data 包含 driver1_time_seconds: True  ← 現在應該是 True
🕒 [TIME_AXIS_DEBUG]   speed_data 包含 driver2_time_seconds: True  ← 現在應該是 True
🕒 [TIME_AXIS_DEBUG]   driver1_time 點數: 500  ← 現在應該有數據
🕒 [TIME_AXIS_DEBUG]   driver2_time 點數: 500  ← 現在應該有數據
```

---

## 🎉 修復結果

修復了兩個關鍵問題後，時間軸功能應該完全正常運作：

1. ✅ GUI 正確讀取復選框狀態
2. ✅ 參數正確傳遞到 `SpeedAnalysisModule.update_lap_parameters()`
3. ✅ MDI 儲存並應用時間軸設定
4. ✅ API 時間數據正確提取並傳遞到 GUI
5. ✅ 圖表正確切換到時間軸模式
6. ✅ X 軸標題顯示 "時間 (s)"
7. ✅ 速度曲線使用時間數據繪製

---

## 📝 測試步驟

1. 重新啟動 GUI: `python f1t_gui_main.py`
2. 開啟速度分析（例如: 2025 Australia R, VER）
3. 勾選 "Use Time Axis" 復選框
4. 點擊 "Update All Analysis"
5. 觀察圖表 X 軸標題應該從 "Distance (m)" 變為 "Time (s)"
6. 檢查終端輸出確認所有 debug 步驟都成功

---

**修復完成時間**: 2025-10-12
**修復的關鍵檔案**: 2 個
**新增代碼行數**: ~30 行
**預期效果**: 時間軸功能完全正常運作 ✅
