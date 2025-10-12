# 時間軸功能全面推廣計畫

## 📅 創建日期：2025-10-12

## 🎯 目標
將 Speed Analysis 模組的 **Use Time Axis** 功能推廣到所有遙測分析模組，實現統一的時間/距離軸切換功能。

---

## ✅ 已完成模組

### 1. Speed Analysis ✅
- **Chart Widget**: `speed_analysis_chart_widget.py`
- **MDI Module**: `speed_analysis_mdi.py`
- **完成功能**:
  - ✅ `set_time_axis_mode()` 方法
  - ✅ X 軸範圍自動計算（時間/距離）
  - ✅ X 軸標題切換（"時間 (s)" / "距離 (m)"）
  - ✅ X 軸刻度格式化（浮點/整數）
  - ✅ 數據源選擇（driver1_time / distance）
  - ✅ 垂直線標籤更新（滑鼠追蹤線、固定線、連動線）
  - ✅ `update_lap_parameters(use_time_axis=True)` 參數傳遞

---

## 🔲 待更新模組清單

### 2. Brake Analysis 🔲
- **優先級**: ⭐⭐⭐ 高（與 Speed 相似度最高）
- **檔案位置**:
  - Chart Widget: `modules/gui/lap_analysis/brake_analysis/brake_analysis_chart_widget.py`
  - MDI Module: `modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py`
- **需要修改**:
  - [ ] 添加 `use_time_axis` 和 `driver1_time`, `driver2_time` 屬性
  - [ ] 實現 `set_time_axis_mode()` 方法
  - [ ] 修改 `set_brake_data()` 根據模式計算 X 軸範圍
  - [ ] 修改 `_draw_axes()` 切換 X 軸標題
  - [ ] 修改 `_draw_axes()` 切換 X 軸刻度格式
  - [ ] 修改 `_draw_brake_curves()` 選擇數據源
  - [ ] 修改 `_draw_tracking_line()` 更新標籤
  - [ ] 修改 `_draw_linkage_line()` 更新標籤
  - [ ] MDI: 添加 `use_time_axis` 參數到 `update_lap_parameters()`
  - [ ] 包裝類: 添加 `set_time_axis_mode()` 代理方法

---

### 3. Throttle Analysis 🔲
- **優先級**: ⭐⭐⭐ 高
- **檔案位置**:
  - Chart Widget: `modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py`
  - MDI Module: `modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_mdi.py`
- **需要修改**: （同 Brake Analysis）

---

### 4. Gear Analysis 🔲
- **優先級**: ⭐⭐ 中（離散數據，刻度顯示可能不同）
- **檔案位置**:
  - Chart Widget: `modules/gui/lap_analysis/gear_analysis/gear_analysis_chart_widget.py`
  - MDI Module: `modules/gui/lap_analysis/gear_analysis/gear_analysis_mdi.py`
- **需要修改**: （同上）
- **特殊考慮**:
  - Gear 是離散值（1-8 檔），Y 軸不變
  - 只需修改 X 軸時間/距離切換

---

### 5. RPM Analysis 🔲
- **優先級**: ⭐⭐ 中
- **檔案位置**:
  - Chart Widget: `modules/gui/lap_analysis/rpm_analysis/rpm_analysis_chart_widget.py`
  - MDI Module: `modules/gui/lap_analysis/rpm_analysis/rpm_analysis_mdi.py`
- **需要修改**: （同上）

---

### 6. Acceleration Analysis 🔲
- **優先級**: ⭐⭐ 中
- **檔案位置**:
  - Chart Widget: `modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_chart_widget.py`
  - MDI Module: `modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_mdi.py`
- **需要修改**: （同上）

---

### 7. Speed Diff Analysis 🔲
- **優先級**: ⭐ 低（差異分析，可能需要特殊處理）
- **檔案位置**:
  - Chart Widget: `modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_chart_widget.py`
  - MDI Module: `modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_mdi.py`
- **需要修改**: （同上）
- **特殊考慮**:
  - 顯示速度差異，Y 軸可能有正負值
  - 時間軸模式可能需要特殊對齊

---

### 8. Distance Diff Analysis 🔲
- **優先級**: ⭐ 低
- **檔案位置**:
  - Chart Widget: `modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_chart_widget.py`
  - MDI Module: `modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_mdi.py`
- **需要修改**: （同上）

---

## 🔧 標準化修改模板

### Chart Widget 修改清單

#### 1. 添加屬性（`__init__` 方法）
```python
def __init__(self, parent=None):
    super().__init__(parent)
    # ... 現有代碼 ...
    
    # 時間軸模式支援
    self.use_time_axis = False
    self.driver1_time = []
    self.driver2_time = []
```

#### 2. 修改 `set_XXX_data()` 方法簽名
```python
def set_brake_data(self, distance: List[float], driver1_brake: List[float], 
                   driver2_brake: List[float], driver1_name: str = "Driver 1", 
                   driver2_name: str = "Driver 2", sectors: List[Dict] = None,
                   lap1: int = None, lap2: int = None,
                   driver1_time: List[float] = None, driver2_time: List[float] = None):
    # 儲存時間數據
    self.driver1_time = driver1_time or []
    self.driver2_time = driver2_time or []
    
    # 計算 X 軸範圍（根據模式）
    if self.use_time_axis and (driver1_time or driver2_time):
        all_time_values = []
        if driver1_time:
            all_time_values.extend(driver1_time)
        if driver2_time:
            all_time_values.extend(driver2_time)
        
        if all_time_values:
            self.min_distance = min(all_time_values)
            self.max_distance = max(all_time_values)
    elif distance:
        self.min_distance = min(distance)
        self.max_distance = max(distance)
```

#### 3. 添加 `set_time_axis_mode()` 方法
```python
def set_time_axis_mode(self, use_time_axis: bool):
    """設置時間軸模式"""
    self.use_time_axis = use_time_axis
    
    # 重新計算 X 軸範圍
    if use_time_axis and self.driver1_time:
        all_time_values = list(self.driver1_time)
        if self.driver2_time:
            all_time_values.extend(self.driver2_time)
        
        self.min_distance = min(all_time_values)
        self.max_distance = max(all_time_values)
    elif self.distance_data:
        self.min_distance = min(self.distance_data)
        self.max_distance = max(self.distance_data)
    
    # 重置視圖狀態
    self.view_min_distance = None
    self.view_max_distance = None
    self.view_min_speed = None
    self.view_max_speed = None
    
    # 強制重繪
    self.repaint()
```

#### 4. 修改 `_draw_axes()` 方法
```python
def _draw_axes(self, painter: QPainter, chart_rect: QRect):
    # ... X 軸刻度 ...
    for i in range(0, 11, 2):
        distance_value = self.min_distance + i * distance_range / 10
        x = chart_rect.left() + i * chart_rect.width() / 10
        
        # 根據時間軸模式選擇格式
        if self.use_time_axis:
            label_text = f"{distance_value:.1f}"  # 時間: 浮點數
        else:
            label_text = f"{int(distance_value)}"  # 距離: 整數
        
        painter.drawText(int(x - 20), chart_rect.bottom() + 20, 40, 20, 
                       Qt.AlignCenter, label_text)
    
    # ... X 軸標題 ...
    if self.use_time_axis:
        x_axis_title = tr('time_s', '時間 (s)')
    else:
        x_axis_title = tr('distance_m', '距離 (m)')
    
    painter.drawText(x_title_x, x_title_y, x_title_width, 20, Qt.AlignCenter, x_axis_title)
```

#### 5. 修改 `_draw_XXX_curves()` 方法
```python
def _draw_brake_curves(self, painter: QPainter, chart_rect: QRect):
    # 根據時間軸模式選擇X軸數據源
    if self.use_time_axis and self.driver1_time and self.driver2_time:
        x_data_source = self.driver1_time
    else:
        x_data_source = self.distance_data
    
    if not x_data_source:
        return
    
    # 繪製車手1曲線
    if self.driver1_brake and len(self.driver1_brake) == len(x_data_source):
        for i, (x_value, brake) in enumerate(zip(x_data_source, self.driver1_brake)):
            # 繪製邏輯 ...
```

#### 6. 修改 `_draw_tracking_line()` 方法
```python
def _draw_tracking_line(self, painter: QPainter, chart_rect: QRect, x_pos: int, is_fixed: bool):
    # ... 計算 X 軸值 ...
    x_axis_value = current_min_distance + (relative_x / chart_rect.width()) * distance_range
    
    # 根據模式選擇搜索數據源
    if self.use_time_axis and self.driver1_time:
        search_data = self.driver1_time
    else:
        search_data = self.distance_data
    
    # ... 找到最接近點 ...
    
    # 標籤顯示
    if self.use_time_axis:
        painter.drawText(label_x + 5, text_y, f"時間: {x_axis_value:.2f} s")
    else:
        painter.drawText(label_x + 5, text_y, f"距離: {x_axis_value:.0f} m")
```

#### 7. 修改 `_draw_linkage_line()` 方法
```python
def _draw_linkage_line(self, painter: QPainter, chart_rect: QRect):
    # ... 連動線繪製 ...
    
    # 標籤顯示
    if self.use_time_axis:
        painter.drawText(label_x + 5, label_y + 15, f"連動時間: {self.linkage_distance_value:.2f} s")
    else:
        painter.drawText(label_x + 5, label_y + 15, f"連動距離: {self.linkage_distance_value:.0f} m")
    
    # 根據模式選擇搜索數據源
    if self.use_time_axis and self.driver1_time:
        search_data = self.driver1_time
    else:
        search_data = self.distance_data
```

---

### MDI Module 修改清單

#### 1. 修改 `update_lap_parameters()` 簽名
```python
def update_lap_parameters(self, year: str, race: str, session: str,
                         driver1: str, driver2: str = None,
                         lap1: int = 1, lap2: int = None,
                         is_fastest: bool = False, use_time_axis: bool = False) -> bool:
    # 儲存時間軸設定
    self.use_time_axis = use_time_axis
    
    # ... 現有載入邏輯 ...
```

#### 2. 調用 `set_time_axis_mode()`
```python
def update_lap_parameters(self, ...):
    # ... 載入數據 ...
    
    # 設置時間軸模式
    if self.brake_chart_widget and hasattr(self.brake_chart_widget, 'set_time_axis_mode'):
        self.brake_chart_widget.set_time_axis_mode(use_time_axis)
```

---

### 包裝類修改（如 BrakeAnalysisChartWidget）

#### 添加代理方法
```python
class BrakeAnalysisChartWidget(QWidget, ...):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ...
        self.chart_widget = BrakeChartWidget()  # 實際圖表
    
    def set_time_axis_mode(self, use_time_axis: bool):
        """代理方法：轉發到內部圖表"""
        if hasattr(self, 'chart_widget') and self.chart_widget is not None:
            self.chart_widget.set_time_axis_mode(use_time_axis)
    
    def update_brake_data(self, data: Dict[str, Any]):
        # 提取時間數據
        brake_data = data.get('brake_data', {})
        driver1_time = brake_data.get('driver1_time_seconds', [])
        driver2_time = brake_data.get('driver2_time_seconds', [])
        
        # 傳遞給圖表
        self.chart_widget.set_brake_data(
            distance=distance,
            driver1_brake=driver1_brake,
            driver2_brake=driver2_brake,
            driver1_time=driver1_time,
            driver2_time=driver2_time
        )
```

---

## 📊 實施順序建議

### 階段 1: 高優先級模組（預計 2-3 小時）
1. ✅ Speed Analysis（已完成）
2. 🔲 Brake Analysis
3. 🔲 Throttle Analysis

### 階段 2: 中優先級模組（預計 2-3 小時）
4. 🔲 Gear Analysis
5. 🔲 RPM Analysis
6. 🔲 Acceleration Analysis

### 階段 3: 低優先級模組（預計 1-2 小時）
7. 🔲 Speed Diff Analysis
8. 🔲 Distance Diff Analysis

---

## ✅ 測試檢查清單（每個模組）

### 功能測試
- [ ] 勾選 Use Time Axis → X 軸切換到時間 (s)
- [ ] 取消勾選 → X 軸切回距離 (m)
- [ ] X 軸範圍正確計算（時間: 0-95s, 距離: 0-5288m）
- [ ] X 軸刻度格式正確（時間: 浮點, 距離: 整數）
- [ ] 曲線數據點對齊正確

### 標籤測試
- [ ] 滑鼠追蹤線標籤顯示正確單位
- [ ] 固定垂直線標籤顯示正確單位
- [ ] 連動線標籤顯示正確單位

### 切換測試
- [ ] 多次切換時間/距離軸無錯誤
- [ ] 切換後圖表自動重繪
- [ ] 切換不影響速度數據正確性

---

## 📝 注意事項

1. **變數命名一致性**: 所有模組使用 `min_distance`, `max_distance` 作為 X 軸範圍變數名（即使是時間模式）
2. **搜索數據源**: 時間模式使用 `driver1_time`, 距離模式使用 `distance_data`
3. **格式化**: 時間顯示 2 位小數 (`:.2f`), 距離顯示整數 (`:0.f`)
4. **國際化**: 所有新增字串使用 `tr()` 函數包裹
5. **向後相容**: 新參數都使用預設值，確保舊代碼不會崩潰

---

## 🚀 開始實施

請確認準備好開始第一個模組（Brake Analysis）的更新。

---

## 📅 更新歷史

- **2025-10-12**: 創建文檔，Speed Analysis 完成
- **待續**: Brake Analysis 開始實施
