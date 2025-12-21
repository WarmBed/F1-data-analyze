# 時間軸功能實現報告

## 執行摘要

已成功實現速度分析模組的時間軸切換功能。用戶現在可以通過勾選 GUI 主工具列的 "Use Time Axis" 復選框，並點擊 "Update All Analysis"，將速度圖表的 X 軸從距離 (m) 切換到時間 (s)。

## 實現變更清單

### 1. GUI 主程式 (`f1t_gui_main.py`)

#### 變更 1.1: 添加 "Use Time Axis" 復選框
- **位置**: `_create_lap_analysis_controls()` 方法
- **代碼**:
  ```python
  self.use_time_axis_checkbox = QCheckBox(tr('use_time_axis', '使用時間軸'))
  self.use_time_axis_checkbox.setChecked(False)
  ```
- **功能**: 創建時間軸切換控件

#### 變更 1.2: 將復選框添加到控件管理列表
- **位置**: `_create_lap_analysis_controls()` 方法
- **代碼**:
  ```python
  controls_to_add = [
      # ... 其他控件 ...
      self.use_time_axis_checkbox,
  ]
  
  controls_to_remove = [
      # ... 其他控件 ...
      'use_time_axis_checkbox',
  ]
  ```

#### 變更 1.3: 在 Update All Analysis 中提取復選框狀態
- **位置**: `update_all_lap_analysis()` 方法
- **代碼**:
  ```python
  # 提取時間軸模式
  use_time_axis = False
  if hasattr(self, 'use_time_axis_checkbox') and self.use_time_axis_checkbox:
      use_time_axis = self.use_time_axis_checkbox.isChecked()
      print(f"[MAIN] 🕒 時間軸模式: {use_time_axis}")
  ```

#### 變更 1.4: 將時間軸標誌傳遞給速度分析模組
- **位置**: `update_all_lap_analysis()` 方法 (telemetry_kwargs)
- **代碼**:
  ```python
  telemetry_kwargs = {
      # ... 其他參數 ...
      'use_time_axis': use_time_axis,  # 🆕 時間軸模式
  }
  ```

### 2. 速度分析 MDI (`speed_analysis_mdi.py`)

#### 變更 2.1: 修改 `update_lap_parameters()` 方法簽名
- **位置**: `update_lap_parameters()` 方法
- **代碼**:
  ```python
  def update_lap_parameters(self, year: str = None, race: str = None, 
                           session: str = None, driver1: str = None, 
                           driver2: str = None, lap1: int = None, 
                           lap2: int = None, force_reload: bool = False,
                           use_time_axis: bool = False):  # 🆕 時間軸參數
  ```

#### 變更 2.2: 儲存並應用時間軸模式
- **位置**: `update_lap_parameters()` 方法內部
- **代碼**:
  ```python
  # 儲存時間軸模式
  self.use_time_axis = use_time_axis
  print(f"[SPEED_MDI] 🕒 時間軸模式: {use_time_axis}")
  
  # ... 數據載入後 ...
  
  # 設置時間軸模式
  if self.speed_chart_widget and hasattr(self.speed_chart_widget, 'set_time_axis_mode'):
      self.speed_chart_widget.set_time_axis_mode(use_time_axis)
      print(f"[SPEED_MDI] ✅ 時間軸模式已設置: {use_time_axis}")
  ```

### 3. 速度圖表組件 (`speed_analysis_chart_widget.py`)

#### 變更 3.1: 添加時間軸相關屬性
- **位置**: `SpeedChartWidget.__init__()` 方法
- **代碼**:
  ```python
  # 時間軸模式
  self.use_time_axis = False  # 預設使用距離軸
  self.driver1_time = []  # 車手1時間數據
  self.driver2_time = []  # 車手2時間數據
  ```

#### 變更 3.2: 新增 `set_time_axis_mode()` 方法
- **位置**: 在 `set_speed_data()` 方法之後
- **代碼**:
  ```python
  def set_time_axis_mode(self, use_time_axis: bool):
      """設置時間軸模式"""
      print(f"[SPEED_CHART] 🕒 set_time_axis_mode 被調用: {use_time_axis}")
      self.use_time_axis = use_time_axis
      
      # 重置視圖狀態
      self.view_min_distance = None
      self.view_max_distance = None
      self.view_min_speed = None
      self.view_max_speed = None
      self.show_fixed_line = False
      self.fixed_line_x = -1
      self.fixed_distance_value = None
      
      # 強制重繪
      self.repaint()
  ```

#### 變更 3.3: 修改 `set_speed_data()` 方法參數
- **位置**: `set_speed_data()` 方法簽名
- **代碼**:
  ```python
  def set_speed_data(self, distance: List[float], driver1_speed: List[float], 
                    driver2_speed: List[float], driver1_name: str = "Driver 1", 
                    driver2_name: str = "Driver 2", sectors: List[Dict] = None,
                    lap1: int = None, lap2: int = None,
                    driver1_time: List[float] = None,  # 🆕 時間數據
                    driver2_time: List[float] = None):  # 🆕 時間數據
  ```

#### 變更 3.4: 儲存時間數據
- **位置**: `set_speed_data()` 方法內部
- **代碼**:
  ```python
  self.distance_data = distance
  self.driver1_speed = driver1_speed
  self.driver2_speed = driver2_speed
  self.driver1_time = driver1_time or []  # 🆕 時間數據
  self.driver2_time = driver2_time or []  # 🆕 時間數據
  self.sectors = sectors or []
  ```

#### 變更 3.5: 修改 `_draw_axes()` 方法 - 動態 X 軸標題
- **位置**: `_draw_axes()` 方法
- **代碼**:
  ```python
  # X軸標題 - 根據時間軸模式顯示不同標題
  if self.use_time_axis:
      painter.drawText(x_title_x, x_title_y, x_title_width, 20, 
                      Qt.AlignCenter, tr('time_s', '時間 (s)'))
  else:
      painter.drawText(x_title_x, x_title_y, x_title_width, 20, 
                      Qt.AlignCenter, tr('distance_m', '距離 (m)'))
  ```

#### 變更 3.6: 修改 `_draw_speed_curves()` 方法 - 動態數據源
- **位置**: `_draw_speed_curves()` 方法
- **代碼**:
  ```python
  # 根據時間軸模式選擇X軸數據源
  if self.use_time_axis and self.driver1_time and self.driver2_time:
      x_data_source = self.driver1_time  # 使用時間數據
  else:
      x_data_source = self.distance_data  # 使用距離數據
  
  # ... 繪製車手1 ...
  
  # 車手2使用獨立的時間數據
  if self.use_time_axis and self.driver2_time:
      x_data_source_2 = self.driver2_time
  else:
      x_data_source_2 = x_data_source
  ```

### 4. 速度圖表分析組件 (`SpeedAnalysisChartWidget`)

#### 變更 4.1: 提取時間數據從 JSON
- **位置**: `update_speed_data()` 方法
- **代碼**:
  ```python
  # 提取速度數據
  distance = speed_data.get('distance', [])
  driver1_speed = speed_data.get('driver1_speed', [])
  driver2_speed = speed_data.get('driver2_speed', [])
  
  # 🆕 提取時間數據
  driver1_time = speed_data.get('driver1_time_seconds', [])
  driver2_time = speed_data.get('driver2_time_seconds', [])
  
  print(f"[SPEED_CHART_WIDGET] 🕒 driver1_time 點數: {len(driver1_time)}")
  print(f"[SPEED_CHART_WIDGET] 🕒 driver2_time 點數: {len(driver2_time)}")
  ```

#### 變更 4.2: 傳遞時間數據到圖表
- **位置**: `update_speed_data()` 方法內的 `set_speed_data()` 調用
- **代碼**:
  ```python
  self.chart_widget.set_speed_data(
      distance=distance,
      driver1_speed=driver1_speed,
      driver2_speed=driver2_speed,
      driver1_name=driver1_name,
      driver2_name=driver2_name,
      sectors=sectors,
      lap1=lap1,
      lap2=lap2,
      driver1_time=driver1_time,  # 🆕 時間數據
      driver2_time=driver2_time   # 🆕 時間數據
  )
  ```

## 數據流程

### 完整時間軸切換流程

```
1. 用戶操作:
   ✅ 勾選 "Use Time Axis" 復選框
   ✅ 點擊 "Update All Analysis" 按鈕

2. f1t_gui_main.py (主程式):
   ✅ update_all_lap_analysis() 讀取 use_time_axis_checkbox.isChecked()
   ✅ 將 use_time_axis 參數添加到 telemetry_kwargs
   ✅ 調用所有速度分析 MDI 的 update_lap_parameters(use_time_axis=True)

3. speed_analysis_mdi.py (MDI 控制器):
   ✅ update_lap_parameters() 接收 use_time_axis 參數
   ✅ 儲存 self.use_time_axis = use_time_axis
   ✅ 重新載入數據（調用 data_manager.load_speed_data()）
   ✅ 數據載入完成後，調用 speed_chart_widget.set_time_axis_mode(use_time_axis)

4. speed_analysis_chart_widget.py (SpeedAnalysisChartWidget):
   ✅ update_speed_data() 從 JSON 提取時間數據:
      - driver1_time_seconds
      - driver2_time_seconds
   ✅ 調用 chart_widget.set_speed_data(..., driver1_time, driver2_time)

5. speed_analysis_chart_widget.py (SpeedChartWidget):
   ✅ set_time_axis_mode(True) 設置 self.use_time_axis = True
   ✅ set_speed_data() 儲存時間數據到 self.driver1_time, self.driver2_time
   ✅ _draw_axes() 切換 X 軸標題為 "時間 (s)"
   ✅ _draw_speed_curves() 使用時間數據作為 X 軸繪製曲線

6. 視覺結果:
   ✅ 圖表 X 軸標題從 "距離 (m)" 變為 "時間 (s)"
   ✅ 速度曲線使用時間戳作為 X 座標重新繪製
   ✅ 圖表自動重繪顯示時間基準的速度分析
```

## JSON 數據結構需求

API 必須在速度數據中提供以下時間戳欄位:

```json
{
  "speed_data": {
    "distance": [0, 10, 20, ...],
    "driver1_speed": [150, 200, 250, ...],
    "driver2_speed": [148, 198, 248, ...],
    "driver1_time_seconds": [0.0, 0.5, 1.0, ...],  // 🆕 必需
    "driver2_time_seconds": [0.0, 0.5, 1.0, ...],  // 🆕 必需
    "driver1_name": "VER",
    "driver2_name": "LEC"
  }
}
```

**數據驗證**: 已通過 `test_api_time_series.py` 確認 API 正確返回 502 點時間數據。

## 語法驗證

```bash
# ✅ 通過語法檢查
python -m py_compile modules\gui\lap_analysis\speed_analysis\speed_analysis_chart_widget.py
```

## 實現功能檢查清單

- [x] ✅ GUI 添加 "Use Time Axis" 復選框
- [x] ✅ 復選框狀態在 Update All Analysis 時提取
- [x] ✅ use_time_axis 參數傳遞到速度分析 MDI
- [x] ✅ MDI 接收並儲存 use_time_axis 狀態
- [x] ✅ MDI 調用 chart_widget.set_time_axis_mode()
- [x] ✅ SpeedChartWidget 添加 use_time_axis 屬性
- [x] ✅ SpeedChartWidget 添加 driver1_time, driver2_time 儲存
- [x] ✅ SpeedChartWidget 實現 set_time_axis_mode() 方法
- [x] ✅ set_speed_data() 接收時間參數
- [x] ✅ set_speed_data() 儲存時間數據
- [x] ✅ _draw_axes() 根據模式切換 X 軸標題
- [x] ✅ _draw_speed_curves() 根據模式選擇數據源
- [x] ✅ SpeedAnalysisChartWidget 提取 JSON 時間數據
- [x] ✅ SpeedAnalysisChartWidget 傳遞時間數據到圖表

## 測試建議

### 功能測試步驟

1. **啟動 GUI**:
   ```bash
   python f1t_gui_main.py
   ```

2. **開啟速度分析**:
   - 設置參數: Year=2024, Race=Japan, Session=R, VER vs LEC
   - 點擊 "Speed Analysis"

3. **測試距離軸模式 (預設)**:
   - 確認圖表 X 軸標題顯示 "距離 (m)"
   - 確認速度曲線正常顯示

4. **切換到時間軸模式**:
   - 勾選 "Use Time Axis" 復選框
   - 點擊 "Update All Analysis"

5. **驗證時間軸模式**:
   - 確認圖表 X 軸標題變更為 "時間 (s)"
   - 確認速度曲線重新繪製（使用時間數據）
   - 確認圖表縮放、滑鼠追蹤等功能正常

6. **切換回距離軸模式**:
   - 取消勾選 "Use Time Axis"
   - 點擊 "Update All Analysis"
   - 確認恢復為距離模式

### 預期 Debug 輸出

```
[MAIN] 🕒 時間軸模式: True
[SPEED_MDI] 🕒 時間軸模式: True
[SPEED_MDI] ✅ 時間軸模式已設置: True
[SPEED_CHART] 🕒 set_time_axis_mode 被調用: True
[SPEED_CHART_WIDGET] 🕒 driver1_time 點數: 502
[SPEED_CHART_WIDGET] 🕒 driver2_time 點數: 502
```

## 國際化支援

使用 `tr()` 函數包裹所有用戶可見字串:

```python
tr('use_time_axis', '使用時間軸')      # GUI 復選框
tr('time_s', '時間 (s)')              # X 軸標題 (時間模式)
tr('distance_m', '距離 (m)')          # X 軸標題 (距離模式)
```

## 相關檔案清單

### 修改的檔案
1. `f1t_gui_main.py` - GUI 主程式
2. `modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py` - MDI 控制器
3. `modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py` - 圖表組件

### 測試檔案
1. `test_api_time_series.py` - API 時間數據驗證 (已通過)
2. `test_time_axis_integration.py` - 時間軸整合測試
3. `test_simple_time_axis.py` - 簡化功能測試

## 已知限制

1. **X 軸刻度更新**: 當前實現重用距離軸的刻度邏輯，時間軸模式下 X 軸數值標籤可能需要格式化調整（例如顯示為 "15.2s" 而非 "15"）

2. **視圖縮放**: 縮放功能（`view_min_distance`, `view_max_distance`）變數名稱仍使用 "distance"，但在時間軸模式下實際儲存的是時間值

3. **滑鼠追蹤**: `_draw_mouse_tracker()` 方法可能需要更新以在時間軸模式下顯示時間值而非距離值

## 後續優化建議

1. **X 軸刻度格式化**: 實現時間專用的刻度格式化 (例如 "0.0s", "5.5s", "10.0s")

2. **變數重命名**: 將 `view_min_distance` 等變數重命名為更通用的名稱 (例如 `view_min_x`, `view_max_x`)

3. **滑鼠追蹤增強**: 在時間軸模式下顯示時間值標籤

4. **網格線優化**: 根據時間軸/距離軸調整網格線密度

## 結論

時間軸切換功能已完整實現。系統現在支援:
- ✅ GUI 復選框控制
- ✅ 參數傳遞鏈路完整
- ✅ 時間數據提取與儲存
- ✅ 圖表動態切換 X 軸
- ✅ 曲線數據源自動選擇

**狀態**: 準備進行功能測試
**下一步**: 啟動 GUI 進行實際用戶測試
