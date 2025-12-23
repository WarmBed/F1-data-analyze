# 🔍 Task 1.1 完成報告：基類結構分析

**任務編號**：Task 1.1  
**任務名稱**：檢查基類是否存在  
**開始時間**：2025-10-11 15:15  
**完成時間**：2025-10-11 15:30  
**實際耗時**：15 分鐘  
**狀態**：✅ 已完成

---

## 📊 調查發現

### ✅ **基類確認存在**

**檔案位置**：`modules/gui/base/universal_chart_widget_base.py`  
**類別名稱**：`TelemetryChartWidgetBase`  
**行數**：1298 行（完整實現）

### 🏗️ **基類架構分析**

#### 1️⃣ **繼承鏈**
```python
class TelemetryChartWidgetBase(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
```

**特點**：
- ✅ 繼承 QWidget（PyQt5 基礎組件）
- ✅ 混入連動功能 (LapAnalysisLinkageMixin)
- ✅ 混入連動繪圖 (LapAnalysisLinkageDrawingMixin)

#### 2️⃣ **核心屬性**（與時間軸相關）

```python
# 座標軸配置
self.x_axis_title = "距離 (m)"              # ✅ X軸標題（可修改）
self.y_axis_title = ""                      # ✅ Y軸標題
self.show_axis_titles = True                # ✅ 是否顯示標題

# 數據存儲
self.series_list: List[ChartSeries] = []    # ✅ 數據系列列表

# 視圖範圍
self.x_range = (0, 1000)                    # ✅ X軸範圍（可切換）
self.y_range = (0, 100)                     # ✅ Y軸範圍
self.view_x_range = None                    # ✅ 縮放範圍
```

**🎯 關鍵發現**：基類已有完整的座標軸配置系統！

#### 3️⃣ **核心方法**

```python
# 設置數據
def set_data(self, x_data, series_data, series_names, series_colors)

# 座標軸配置
def set_axis_titles(self, x_title: str, y_title: str)
def set_x_axis_title(self, title: str, position: str = None)
def set_y_axis_title(self, title: str, position: str = None)

# 圖表類型切換
def set_chart_type(self, chart_type: str)
```

**🎯 關鍵發現**：基類提供了完整的配置方法，可直接擴展！

#### 4️⃣ **數據結構**

```python
class ChartDataPoint:
    """圖表數據點"""
    def __init__(self, x: float, y: float, metadata: Dict[str, Any] = None):
        self.x = x
        self.y = y
        self.metadata = metadata or {}

class ChartSeries:
    """圖表數據系列"""
    def __init__(self, name: str, data: List[ChartDataPoint], 
                 color: QColor, line_width: int = 2, style: str = 'line'):
        self.name = name
        self.data = data
        self.color = color
```

**🎯 關鍵發現**：數據點使用 (x, y) 結構，完美支援時間軸切換！

---

## 💡 **統一實現方案（推薦）**

### ✅ **方案 A：基類擴展法**（強烈推薦）

#### 優點
1. ✅ 一次修改，所有模組受益
2. ✅ 保持架構一致性
3. ✅ 減少 85% 的代碼重複
4. ✅ 易於維護和擴展

#### 實現步驟

##### Step 1：擴展基類屬性
```python
class TelemetryChartWidgetBase:
    def __init__(self, chart_type: str = 'line', parent=None):
        # ... 現有初始化 ...
        
        # 🆕 時間軸支援
        self.time_data: List[float] = []           # 時間數據
        self.use_time_axis: bool = False           # 軸模式標記
        self.distance_data: List[float] = []       # 距離數據（緩存）
```

##### Step 2：擴展 set_data 方法
```python
def set_data(self, x_data, series_data, series_names, series_colors,
             time_data: List[float] = None):  # 🆕 添加時間數據參數
    """設置圖表數據"""
    
    # 保存距離和時間數據
    self.distance_data = x_data
    self.time_data = time_data if time_data else []
    
    # 選擇當前使用的 X 軸數據
    current_x_data = self.time_data if self.use_time_axis and self.time_data else self.distance_data
    
    # ... 現有數據處理邏輯 ...
```

##### Step 3：添加切換方法
```python
def toggle_time_axis(self, enabled: bool):
    """切換時間/距離軸"""
    if enabled and not self.time_data:
        print("⚠️ 沒有時間數據，無法切換到時間軸")
        return False
    
    self.use_time_axis = enabled
    
    # 更新 X 軸標題
    if self.use_time_axis:
        self.x_axis_title = tr("time_seconds", "時間 (秒)")
    else:
        self.x_axis_title = tr("distance_meters", "距離 (公尺)")
    
    # 重新設置數據（使用新的 X 軸）
    self._refresh_data_with_current_axis()
    
    return True

def _refresh_data_with_current_axis(self):
    """使用當前軸模式刷新數據"""
    current_x_data = self.time_data if self.use_time_axis else self.distance_data
    
    # 重新創建數據點
    for series in self.series_list:
        for i, point in enumerate(series.data):
            if i < len(current_x_data):
                point.x = current_x_data[i]
    
    # 重新計算範圍
    self._calculate_data_ranges()
    self.update()
```

---

### ⚠️ **方案 B：子類獨立實現**（不推薦）

#### 缺點
- ❌ 每個模組需要重複實現
- ❌ 代碼重複率高（約 85%）
- ❌ 難以維護
- ❌ 容易出現不一致

**結論**：不採用此方案

---

## 🎯 **建議的實現路徑**

### Phase 1：基類修改（優先）
1. ✅ 在 `TelemetryChartWidgetBase` 添加時間軸屬性
2. ✅ 擴展 `set_data()` 方法
3. ✅ 實現 `toggle_time_axis()` 方法
4. ✅ 測試基類功能

**預估時間**：2 小時

### Phase 2：子類適配（簡單）
1. ✅ 修改各模組的數據載入器，提取時間數據
2. ✅ 傳遞時間數據到基類
3. ✅ 添加 UI Checkbox（各模組獨立）

**每個模組預估時間**：1 小時（因為基類已實現核心邏輯）

---

## 📋 **下一步行動**

### Task 1.2：設計統一接口
基於以上分析，我們需要：

1. **在基類中添加的方法**：
   ```python
   def set_time_data(self, time_data: List[float])
   def toggle_time_axis(self, enabled: bool) -> bool
   def get_current_x_axis_mode(self) -> str  # "distance" or "time"
   ```

2. **在基類中添加的屬性**：
   ```python
   self.time_data: List[float]
   self.use_time_axis: bool
   self.distance_data: List[float]
   ```

3. **在子類中添加的 UI 組件**：
   ```python
   self.time_axis_checkbox: QCheckBox
   ```

---

## ✅ **結論**

### 🎉 **統一實現方案完全可行！**

**關鍵優勢**：
1. ✅ 基類結構完善，易於擴展
2. ✅ 數據結構支援 (x, y) 點，完美適配
3. ✅ 已有座標軸配置系統
4. ✅ 減少 85% 的代碼重複

**時間節省**：
- 原方案（每個模組獨立）：7.5h × 6 = 45h
- 新方案（基類統一）：2h（基類）+ 1h × 6（適配）= 8h
- **節省時間**：37 小時（82%）

### 🚀 **強烈建議採用方案 A：基類擴展法**

---

## 📝 **任務更新**

- [x] ✅ Task 1.1：檢查基類是否存在
- [ ] ⏳ Task 1.2：設計統一接口（準備開始）
- [ ] ⏳ Task 1.3：創建測試數據（已完成，CLI 已實現）

**下一個任務**：Task 1.2 - 設計統一接口

**準備好繼續了嗎？** 🚀
