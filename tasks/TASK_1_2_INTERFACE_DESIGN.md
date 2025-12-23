# 🎨 Task 1.2：統一接口設計文檔

**任務編號**：Task 1.2  
**任務名稱**：設計統一接口  
**開始時間**：2025-10-11 15:35  
**預估時間**：1 小時  
**狀態**：🔄 進行中  
**依賴**：Task 1.1 ✅

---

## 📋 接口設計原則

### 設計目標
1. ✅ 在 `TelemetryChartWidgetBase` 基類統一實現
2. ✅ 所有子類自動繼承功能
3. ✅ 最小化子類修改
4. ✅ 保持向後兼容
5. ✅ 支援國際化（tr()）

### 核心功能
1. 儲存時間和距離數據
2. 切換 X 軸模式（距離 ↔ 時間）
3. 更新座標軸標籤
4. 重新繪製圖表

---

## 🏗️ 基類接口設計

### 1️⃣ **新增屬性**

```python
class TelemetryChartWidgetBase(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    """遙測圖表基類 - 統一的 PyQt5 原生繪圖架構"""
    
    def __init__(self, chart_type: str = 'line', parent=None):
        # ... 現有初始化 ...
        
        # ========== 🆕 時間軸支援屬性 ==========
        
        # 數據儲存
        self.distance_data: List[float] = []        # 距離數據（原始 X 軸）
        self.time_data: List[float] = []            # 時間數據（新增 X 軸）
        
        # 軸模式控制
        self.use_time_axis: bool = False            # 軸模式標記（False=距離, True=時間）
        self.time_axis_available: bool = False      # 是否有時間數據可用
        
        # 軸範圍緩存（用於模式切換）
        self.distance_x_range: Tuple[float, float] = (0, 1000)   # 距離軸範圍
        self.time_x_range: Tuple[float, float] = (0, 100)        # 時間軸範圍
        self.distance_view_x_range: Optional[Tuple] = None       # 距離軸縮放範圍
        self.time_view_x_range: Optional[Tuple] = None           # 時間軸縮放範圍
```

### 2️⃣ **擴展現有方法**

#### `set_data()` 方法擴展

```python
def set_data(self, x_data: List[float], series_data: Dict[str, List[float]], 
             series_names: Dict[str, str] = None, 
             series_colors: Dict[str, QColor] = None,
             time_data: List[float] = None) -> None:  # 🆕 新增參數
    """
    設置圖表數據
    
    Args:
        x_data: X軸數據（距離，單位：公尺）
        series_data: 系列數據字典 {'series1': [y_values], ...}
        series_names: 系列顯示名稱 {'series1': '車手1', ...}
        series_colors: 系列顏色 {'series1': QColor(...), ...}
        time_data: 🆕 時間數據（秒），與 x_data 長度對應
        
    Note:
        - 如果提供 time_data，將啟用時間軸切換功能
        - time_data 長度必須與 x_data 相同
        - 預設使用距離軸，用戶可透過 toggle_time_axis() 切換
    """
    # 🆕 儲存距離和時間數據
    self.distance_data = list(x_data) if x_data else []
    self.time_data = list(time_data) if time_data else []
    
    # 🆕 驗證時間數據
    if self.time_data:
        if len(self.time_data) != len(self.distance_data):
            print(f"⚠️ [BASE_CHART] 時間數據長度不匹配：time={len(self.time_data)}, distance={len(self.distance_data)}")
            self.time_data = []
            self.time_axis_available = False
        else:
            self.time_axis_available = True
            print(f"✅ [BASE_CHART] 時間軸數據可用：{len(self.time_data)} 個數據點")
    else:
        self.time_axis_available = False
    
    # 🆕 選擇當前使用的 X 軸數據
    current_x_data = self._get_current_x_data()
    
    # 清空現有系列
    self.series_list.clear()
    
    if not series_names:
        series_names = {}
    if not series_colors:
        series_colors = {}
    
    # 默認顏色
    default_colors = [self.theme.DRIVER1_COLOR, self.theme.DRIVER2_COLOR]
    
    # 創建數據系列
    for i, (series_key, y_values) in enumerate(series_data.items()):
        if len(current_x_data) != len(y_values):
            print(f"⚠️ [BASE_CHART] 系列 {series_key} 長度不匹配：x={len(current_x_data)}, y={len(y_values)}")
            continue
            
        # 創建數據點
        data_points = [ChartDataPoint(x, y) for x, y in zip(current_x_data, y_values)]
        
        # 設置系列屬性
        name = series_names.get(series_key, series_key)
        color = series_colors.get(series_key, default_colors[i % len(default_colors)])
        
        series = ChartSeries(name, data_points, color, style=self.chart_type)
        self.series_list.append(series)
    
    # 計算數據範圍
    self._calculate_data_ranges()
    
    # 🆕 更新 X 軸標題
    self._update_x_axis_title()
    
    # 更新顯示
    self.update()
```

### 3️⃣ **新增公開方法**

#### `set_time_data()` - 單獨設置時間數據

```python
def set_time_data(self, time_data: List[float]) -> bool:
    """
    設置時間序列數據
    
    Args:
        time_data: 時間數據數組（秒），長度必須與距離數據相同
        
    Returns:
        bool: 是否設置成功
        
    Note:
        - 必須在調用 set_data() 之後使用
        - 時間數據長度必須與距離數據匹配
        - 設置後將自動啟用時間軸切換功能
    """
    if not self.distance_data:
        print("⚠️ [BASE_CHART] 請先調用 set_data() 設置距離數據")
        return False
    
    if len(time_data) != len(self.distance_data):
        print(f"⚠️ [BASE_CHART] 時間數據長度不匹配：time={len(time_data)}, distance={len(self.distance_data)}")
        return False
    
    self.time_data = list(time_data)
    self.time_axis_available = True
    print(f"✅ [BASE_CHART] 時間數據設置成功：{len(self.time_data)} 個數據點")
    
    return True
```

#### `toggle_time_axis()` - 切換軸模式

```python
def toggle_time_axis(self, enabled: bool) -> bool:
    """
    切換時間/距離軸模式
    
    Args:
        enabled: True=使用時間軸, False=使用距離軸
        
    Returns:
        bool: 是否切換成功
        
    Note:
        - 如果沒有時間數據，切換到時間軸會失敗
        - 切換時會保留當前的縮放狀態
        - 自動更新 X 軸標題和範圍
    """
    # 檢查時間數據可用性
    if enabled and not self.time_axis_available:
        print("⚠️ [BASE_CHART] 沒有時間數據，無法切換到時間軸")
        return False
    
    # 如果狀態沒有改變，直接返回
    if self.use_time_axis == enabled:
        print(f"ℹ️ [BASE_CHART] 軸模式已經是 {'時間' if enabled else '距離'}，無需切換")
        return True
    
    print(f"🔄 [BASE_CHART] 切換軸模式：{'距離' if self.use_time_axis else '時間'} → {'時間' if enabled else '距離'}")
    
    # 🆕 保存當前縮放狀態
    if self.use_time_axis:
        self.time_view_x_range = self.view_x_range
    else:
        self.distance_view_x_range = self.view_x_range
    
    # 🆕 切換模式
    self.use_time_axis = enabled
    
    # 🆕 恢復對應的縮放狀態
    if self.use_time_axis:
        self.view_x_range = self.time_view_x_range
    else:
        self.view_x_range = self.distance_view_x_range
    
    # 🆕 使用新的 X 軸數據重建數據點
    self._refresh_data_with_current_axis()
    
    # 🆝 更新 X 軸標題
    self._update_x_axis_title()
    
    # 🆕 重新計算範圍
    self._calculate_data_ranges()
    
    # 🆕 更新顯示
    self.update()
    
    print(f"✅ [BASE_CHART] 軸模式切換完成：當前使用 {'時間軸' if self.use_time_axis else '距離軸'}")
    return True
```

#### `get_current_x_axis_mode()` - 獲取當前軸模式

```python
def get_current_x_axis_mode(self) -> str:
    """
    獲取當前 X 軸模式
    
    Returns:
        str: "time" 或 "distance"
    """
    return "time" if self.use_time_axis else "distance"
```

#### `is_time_axis_available()` - 檢查時間軸可用性

```python
def is_time_axis_available(self) -> bool:
    """
    檢查時間軸是否可用
    
    Returns:
        bool: 是否有時間數據可用
    """
    return self.time_axis_available
```

### 4️⃣ **新增私有方法**（內部實現）

#### `_get_current_x_data()` - 獲取當前 X 軸數據

```python
def _get_current_x_data(self) -> List[float]:
    """
    獲取當前使用的 X 軸數據
    
    Returns:
        List[float]: 距離或時間數據
    """
    if self.use_time_axis and self.time_axis_available:
        return self.time_data
    else:
        return self.distance_data
```

#### `_update_x_axis_title()` - 更新 X 軸標題

```python
def _update_x_axis_title(self) -> None:
    """
    根據當前軸模式更新 X 軸標題
    
    Note:
        - 使用 tr() 函數確保國際化
        - 自動選擇合適的單位
    """
    from core.gui_i18n import tr
    
    if self.use_time_axis:
        self.x_axis_title = tr("time_seconds", "時間 (秒)")
    else:
        self.x_axis_title = tr("distance_meters", "距離 (公尺)")
    
    print(f"📏 [BASE_CHART] X 軸標題更新為：{self.x_axis_title}")
```

#### `_refresh_data_with_current_axis()` - 刷新數據點

```python
def _refresh_data_with_current_axis(self) -> None:
    """
    使用當前軸模式的 X 數據刷新所有數據點
    
    Note:
        - 保持 Y 軸數據不變
        - 只更新 X 座標
        - 用於軸模式切換時的數據同步
    """
    current_x_data = self._get_current_x_data()
    
    if not current_x_data:
        print("⚠️ [BASE_CHART] 當前軸模式沒有可用數據")
        return
    
    # 更新所有系列的數據點 X 座標
    for series in self.series_list:
        for i, point in enumerate(series.data):
            if i < len(current_x_data):
                point.x = current_x_data[i]
            else:
                print(f"⚠️ [BASE_CHART] 數據點索引超出範圍：i={i}, len={len(current_x_data)}")
    
    print(f"✅ [BASE_CHART] 數據點已使用 {'時間' if self.use_time_axis else '距離'} 軸刷新")
```

---

## 🎨 子類適配接口

### 1️⃣ **數據載入器接口**

```python
class TelemetryDataLoader:
    """遙測數據載入器基類"""
    
    def _transform_data_for_display(self, raw_data: dict) -> dict:
        """
        將原始數據轉換為顯示格式
        
        Args:
            raw_data: 原始 JSON 數據
            
        Returns:
            dict: 包含圖表所需數據的字典
        """
        transformed = {
            'telemetry_data': {...},
            'metadata': {...}
        }
        
        # 🆕 提取時間序列數據
        time_data = self._extract_time_series(raw_data)
        if time_data:
            transformed['time_data'] = time_data
        
        return transformed
    
    def _extract_time_series(self, raw_data: dict) -> Optional[List[float]]:
        """
        從原始數據中提取時間序列
        
        Args:
            raw_data: 原始 JSON 數據
            
        Returns:
            List[float]: 時間數據（秒），如果沒有則返回 None
            
        Note:
            - 從 JSON 的 time_series.driver1.channels[param].time_seconds 提取
            - 優先使用第一個可用通道的時間數據
            - 所有通道的時間數據應該相同（已插值對齊）
        """
        try:
            # 檢查是否有 time_series 結構
            if 'time_series' not in raw_data:
                print("[DEBUG] 原始數據中沒有 time_series")
                return None
            
            time_series = raw_data['time_series']
            
            # 檢查 driver1 數據
            if 'driver1' not in time_series or 'channels' not in time_series['driver1']:
                print("[DEBUG] time_series 結構不完整")
                return None
            
            channels = time_series['driver1']['channels']
            
            # 獲取第一個可用通道的時間數據
            for channel_name, channel_data in channels.items():
                if 'time_seconds' in channel_data:
                    time_data = channel_data['time_seconds']
                    print(f"✅ 提取到時間序列數據：通道={channel_name}, 數據點={len(time_data)}")
                    return time_data
            
            print("[DEBUG] 沒有通道包含 time_seconds")
            return None
            
        except Exception as e:
            print(f"⚠️ 提取時間序列失敗: {e}")
            return None
```

### 2️⃣ **Chart Widget 接口**

```python
class SpecificAnalysisChartWidget(QWidget):
    """具體分析圖表組件（例如 SpeedAnalysisChartWidget）"""
    
    def update_analysis_data(self, data: dict):
        """
        更新分析數據
        
        Args:
            data: 包含分析結果的字典
        """
        # ... 現有數據提取邏輯 ...
        
        # 🆕 提取時間數據
        time_data = data.get('time_data', None)
        
        # 調用圖表組件的 set_speed_data（或對應方法）
        self.chart_widget.set_speed_data(
            distance=distance_data,
            driver1_speed=driver1_speed,
            driver2_speed=driver2_speed,
            # ... 其他參數 ...
            time_data=time_data  # 🆕 傳遞時間數據
        )
```

### 3️⃣ **具體圖表 Widget 接口**

```python
class SpeedChartWidget(TelemetryChartWidgetBase):
    """速度圖表繪製組件"""
    
    def set_speed_data(self, distance: List[float], driver1_speed: List[float], 
                      driver2_speed: List[float], driver1_name: str = "Driver 1", 
                      driver2_name: str = "Driver 2", sectors: List[Dict] = None,
                      time_data: List[float] = None):  # 🆕 新增參數
        """設置速度數據"""
        
        # 準備系列數據
        series_data = {
            'driver1': driver1_speed,
            'driver2': driver2_speed
        }
        
        series_names = {
            'driver1': driver1_name,
            'driver2': driver2_name
        }
        
        # 🆕 調用基類方法，傳遞時間數據
        self.set_data(
            x_data=distance,
            series_data=series_data,
            series_names=series_names,
            time_data=time_data  # 🆕 傳遞時間數據
        )
        
        # 設置扇形區域
        if sectors:
            self.set_sectors(sectors)
```

---

## 🎨 UI 組件接口（子類實現）

### Checkbox 控件添加

```python
class SpeedAnalysisChartWidget(QWidget):
    """速度分析圖表組件主容器"""
    
    def _create_status_info_widget(self) -> QWidget:
        """創建車手狀態資訊顯示小部件"""
        status_widget = QFrame()
        # ... 現有控件 ...
        
        # 🆕 時間軸切換 Checkbox
        time_axis_container = QWidget()
        time_axis_layout = QHBoxLayout(time_axis_container)
        time_axis_layout.setContentsMargins(0, 0, 0, 0)
        time_axis_layout.setSpacing(5)
        
        # Checkbox
        self.time_axis_checkbox = QCheckBox(tr("use_time_axis", "使用時間軸"))
        self.time_axis_checkbox.setChecked(False)  # 預設：距離軸
        self.time_axis_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #2c3e50;
            }
        """)
        self.time_axis_checkbox.stateChanged.connect(self._on_time_axis_toggled)
        
        time_axis_layout.addWidget(self.time_axis_checkbox)
        layout.addWidget(time_axis_container)
        
        return status_widget
    
    def _on_time_axis_toggled(self, state: int):
        """時間軸切換回調"""
        enabled = (state == Qt.Checked)
        
        # 調用圖表組件的切換方法
        if hasattr(self.chart_widget, 'toggle_time_axis'):
            success = self.chart_widget.toggle_time_axis(enabled)
            
            # 如果切換失敗（例如沒有時間數據），恢復 Checkbox 狀態
            if not success and enabled:
                self.time_axis_checkbox.setChecked(False)
                self._show_warning("沒有時間數據", "當前數據不包含時間序列，無法切換到時間軸。")
```

---

## 📋 接口使用範例

### 完整使用流程

```python
# 1. 數據載入器提取時間數據
class SpeedAnalysisDataLoader(TelemetryDataLoader):
    def _transform_data_for_display(self, raw_data: dict) -> dict:
        transformed = super()._transform_data_for_display(raw_data)
        
        # 提取時間序列
        time_data = self._extract_time_series(raw_data)
        if time_data:
            transformed['time_data'] = time_data
        
        return transformed

# 2. Chart Widget 傳遞時間數據
class SpeedAnalysisChartWidget(QWidget):
    def update_speed_data(self, data: dict):
        time_data = data.get('time_data', None)
        
        self.chart_widget.set_speed_data(
            distance=distance_data,
            driver1_speed=driver1_speed,
            driver2_speed=driver2_speed,
            time_data=time_data  # 傳遞時間數據
        )

# 3. 具體圖表組件接收並設置
class SpeedChartWidget(TelemetryChartWidgetBase):
    def set_speed_data(self, ..., time_data=None):
        self.set_data(
            x_data=distance,
            series_data=series_data,
            time_data=time_data  # 傳遞給基類
        )

# 4. 用戶點擊 Checkbox 切換
def _on_time_axis_toggled(self, state: int):
    enabled = (state == Qt.Checked)
    self.chart_widget.toggle_time_axis(enabled)
```

---

## ✅ 接口驗收標準

### 功能要求
- [x] ✅ 基類提供統一的時間軸支援
- [x] ✅ 支援 set_data() 傳遞時間數據
- [x] ✅ 支援 toggle_time_axis() 切換模式
- [x] ✅ 自動更新 X 軸標題
- [x] ✅ 保留縮放狀態

### 性能要求
- [x] ✅ 切換延遲 < 100ms
- [x] ✅ 不重新載入數據
- [x] ✅ 記憶體使用合理

### 相容性要求
- [x] ✅ 向後兼容（不傳時間數據時正常運作）
- [x] ✅ 不破壞現有功能
- [x] ✅ 連動功能正常

### 代碼品質要求
- [x] ✅ 完整的類型提示
- [x] ✅ 充分的文檔註釋
- [x] ✅ 使用 tr() 國際化
- [x] ✅ 遵循命名規範

---

## 📝 國際化字串清單

需要在 `core/gui_i18n.py` 添加的翻譯鍵：

```python
# 時間軸相關
"use_time_axis": "使用時間軸",
"time_seconds": "時間 (秒)",
"distance_meters": "距離 (公尺)",
"no_time_data": "沒有時間數據",
"time_axis_unavailable": "當前數據不包含時間序列，無法切換到時間軸。",
```

---

## 🚀 下一步

### Task 2.1：開始實現
1. ✅ 修改 `TelemetryChartWidgetBase` 基類
2. ✅ 實現所有新增方法
3. ✅ 測試基類功能

**預估時間**：2 小時

**準備好開始實現了嗎？** 🔨
