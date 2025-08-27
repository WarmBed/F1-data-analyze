# UniversalChartWidget 技術文檔

## 📋 文檔資訊
- **文檔類型**: 模組技術文檔
- **創建日期**: 2025-08-25
- **最後更新**: 2025-08-25
- **版本**: 1.0.0
- **模組路徑**: `modules/gui/universal_chart_widget.py`
- **主要類別**: `UniversalChartWidget(QWidget)`

## 🎯 模組概述

`UniversalChartWidget` 是一個功能完整的通用圖表視窗組件，專為 F1T 系統設計，支援雙Y軸數據顯示、互動式操作、實時數據載入和高度自定義的視覺化功能。

### 🚀 核心特色
- **雙Y軸支援**: 同時顯示左Y軸和右Y軸數據，適合不同量級的數據對比
- **JSON數據載入**: 支援標準化 JSON 格式數據直接載入
- **互動式操作**: 滑鼠追蹤、縮放、拖拉、固定虛線等豐富互動功能
- **高度自定義**: 軸標籤、單位、顏色、線條寬度等完全可配置
- **標註系統**: 支援降雨、事件等特殊標註顯示
- **實時響應**: 所有操作即時生效，提供流暢的用戶體驗

## 🏗️ 類別架構

### 主要類別

#### 1. UniversalChartWidget(QWidget)
**功能**: 主要圖表視窗組件
**繼承**: PyQt5.QtWidgets.QWidget
**責任**: 圖表渲染、事件處理、數據管理

#### 2. ChartDataSeries
**功能**: 數據系列封裝類別
**責任**: 存儲單個數據系列的所有屬性和數據

#### 3. ChartAnnotation
**功能**: 圖表標註類別
**責任**: 管理圖表上的特殊標註（如降雨區間）

## 📡 信號與槽系統

### 📤 輸出信號 (Signals)
```python
# 圖表點擊信號
chart_clicked = pyqtSignal(float, float)  # 參數: (X座標, Y座標)

# 數據點懸停信號
data_point_hovered = pyqtSignal(str)      # 參數: 懸停信息字符串
```

### 🔄 信號流程圖
```
用戶操作 → 滑鼠事件 → 座標轉換 → 信號發射 → 外部處理
    ↓
[滑鼠點擊]     → mousePressEvent()  → screen_to_data_x()  → chart_clicked.emit()
[滑鼠懸停]     → mouseMoveEvent()   → get_y_value_at_x()  → data_point_hovered.emit()
[滾輪縮放]     → wheelEvent()       → 縮放計算           → update()
[拖拉操作]     → mouseMoveEvent()   → 偏移計算           → update()
```

### 🎛️ 事件處理流程
```
[用戶輸入] → [事件檢測] → [狀態判斷] → [座標轉換] → [視圖更新] → [信號發射]
     ↓              ↓              ↓              ↓              ↓
   滑鼠/鍵盤    →  Event Filter  →  修飾鍵檢查   →  數據座標計算  →  重繪觸發  →  外部通知
```

## 🔧 初始化參數

### 構造函數
```python
def __init__(self, title="通用圖表", parent=None):
```

**參數說明**:
- `title` (str): 圖表標題，默認為 "通用圖表"
- `parent` (QWidget): 父視窗組件，默認為 None

### 內部配置參數
```python
# 軸配置
self.left_y_axis_label = "左Y軸"       # 左Y軸標籤
self.right_y_axis_label = "右Y軸"      # 右Y軸標籤
self.x_axis_label = "X軸"              # X軸標籤
self.left_y_unit = ""                  # 左Y軸單位
self.right_y_unit = ""                 # 右Y軸單位
self.x_unit = ""                       # X軸單位

# 顯示控制
self.show_grid = True                  # 顯示網格
self.show_legend = True                # 顯示圖例
self.show_right_y_axis = False         # 顯示右Y軸（有數據時自動啟用）
self.show_value_tooltips = True        # 顯示數值提示

# 縮放和拖拉參數
self.y_scale = 1.0                     # 左Y軸縮放倍數
self.y_offset = 0                      # 左Y軸偏移量
self.x_scale = 1.0                     # X軸縮放倍數
self.x_offset = 0                      # X軸偏移量
self.right_y_scale = 1.0               # 右Y軸縮放倍數
self.right_y_offset = 0                # 右Y軸偏移量

# 圖表邊距
self.margin_left = 60                  # 左邊距
self.margin_bottom = 40                # 下邊距
self.margin_top = 30                   # 上邊距
self.margin_right = 60                 # 右邊距（右Y軸模式）
```

## 📊 JSON 數據格式規範

### 標準輸入格式
```json
{
    "chart_title": "圖表標題",
    "x_axis": {
        "label": "時間",
        "unit": "s",
        "data": [0, 1, 2, 3, 4, 5, ...]
    },
    "left_y_axis": {
        "label": "溫度",
        "unit": "°C", 
        "data": [20.0, 21.5, 23.0, 24.5, ...]
    },
    "right_y_axis": {
        "label": "風速",
        "unit": "km/h",
        "data": [10.0, 12.3, 15.6, 18.9, ...]
    },
    "annotations": [
        {
            "type": "rain",
            "start_x": 100,
            "end_x": 200,
            "label": "降雨期間",
            "color": "blue"
        }
    ]
}
```

### 欄位說明
| 欄位 | 類型 | 必需 | 說明 |
|------|------|------|------|
| `chart_title` | string | 否 | 圖表標題 |
| `x_axis.label` | string | 是 | X軸標籤名稱 |
| `x_axis.unit` | string | 否 | X軸單位 |
| `x_axis.data` | array | 是 | X軸數據陣列 |
| `left_y_axis.label` | string | 否 | 左Y軸標籤名稱 |
| `left_y_axis.unit` | string | 否 | 左Y軸單位 |
| `left_y_axis.data` | array | 否 | 左Y軸數據陣列 |
| `right_y_axis.label` | string | 否 | 右Y軸標籤名稱 |
| `right_y_axis.unit` | string | 否 | 右Y軸單位 |
| `right_y_axis.data` | array | 否 | 右Y軸數據陣列 |
| `annotations` | array | 否 | 標註陣列 |

## 🎮 互動操作指南

### 滑鼠操作
| 操作 | 功能 | 說明 |
|------|------|------|
| **滑鼠移動** | 虛線追蹤 | 顯示當前位置的X/Y值 |
| **左鍵拖拉** | 視圖平移 | 拖拉整個圖表視圖 |
| **Ctrl+左鍵** | 固定虛線 | 在點擊位置固定垂直虛線並顯示數值 |
| **滾輪** | Y軸縮放 | 雙Y軸同時縮放（左右同步） |
| **Ctrl+滾輪** | XY軸同時縮放 | X軸和雙Y軸同時縮放 |

### 鍵盤快捷鍵
| 按鍵 | 功能 | 說明 |
|------|------|------|
| **Ctrl** | 修飾鍵 | 配合滑鼠操作改變行為模式 |

### 縮放行為詳解
```python
# Ctrl + 滾輪: X軸和Y軸同時縮放
if modifiers & Qt.ControlModifier:
    zoom_factor = 1.2 if delta > 0 else 0.8
    self.x_scale *= zoom_factor      # X軸縮放
    self.y_scale *= zoom_factor      # 左Y軸縮放
    self.right_y_scale *= zoom_factor # 右Y軸縮放

# 純滾輪: 僅Y軸縮放（雙Y軸同步）
else:
    zoom_factor = 1.3 if delta > 0 else 0.7
    self.y_scale *= zoom_factor      # 左Y軸縮放
    self.right_y_scale *= zoom_factor # 右Y軸縮放
```

## 🔌 核心 API 方法

### 數據管理
```python
# 添加數據系列
def add_data_series(self, series: ChartDataSeries) -> None

# 添加標註
def add_annotation(self, annotation: ChartAnnotation) -> None

# 從JSON載入數據
def load_from_json(self, json_data: dict) -> None

# 清除所有數據
def clear_data(self) -> None
```

### 視圖控制
```python
# 設置軸標籤和單位
def set_axis_labels(self, x_label, left_y_label, right_y_label="", 
                   x_unit="", left_y_unit="", right_y_unit="") -> None

# 重置視圖
def reset_view(self) -> None

# 適應視圖
def fit_to_view(self) -> None

# 清除固定虛線
def clear_fixed_lines(self) -> None

# 切換數值提示
def toggle_value_tooltips(self) -> None
```

### 座標轉換
```python
# 螢幕座標轉數據座標
def screen_to_data_x(self, screen_x: int) -> float

# 根據X值獲取Y值（插值）
def get_y_value_at_x(self, target_x: float, y_axis: str = "left") -> float

# 獲取圖表繪製區域
def get_chart_area(self) -> QRect

# 獲取數據範圍
def get_overall_x_range(self) -> tuple
def get_y_range_for_axis(self, y_axis: str = "left") -> tuple
```

## 🎨 視覺化配置

### 顏色方案
```python
# 預設顏色
BACKGROUND_COLOR = QColor(0, 0, 0)           # 黑色背景
GRID_COLOR = QColor(50, 50, 50)              # 深灰網格
AXIS_COLOR = QColor(200, 200, 200)           # 淺灰軸線
TEXT_COLOR = QColor(255, 255, 255)           # 白色文字
TRACKING_LINE_COLOR = QColor(255, 255, 255)  # 白色追蹤線
FIXED_LINE_COLOR = QColor(255, 100, 100)     # 紅色固定線

# 數據系列顏色
LEFT_Y_DEFAULT_COLOR = "#FFA366"             # 左Y軸預設淺橘色
RIGHT_Y_DEFAULT_COLOR = "#66B3FF"            # 右Y軸預設淺藍色（偏藍）
```

### 線條配置
```python
# 線條寬度
AXIS_LINE_WIDTH = 2                          # 軸線寬度
GRID_LINE_WIDTH = 1                          # 網格線寬度
TRACKING_LINE_WIDTH = 2                      # 追蹤線寬度
FIXED_LINE_WIDTH = 3                         # 固定線寬度
DEFAULT_DATA_LINE_WIDTH = 2                  # 預設數據線寬度

# 線條樣式
TRACKING_LINE_STYLE = Qt.DashLine            # 追蹤線樣式
FIXED_LINE_STYLE = Qt.DashDotLine            # 固定線樣式
```

## 📈 使用範例

### 基本使用
```python
from PyQt5.QtWidgets import QApplication
from modules.gui.universal_chart_widget import UniversalChartWidget, ChartDataSeries

# 創建應用
app = QApplication(sys.argv)

# 創建圖表
chart = UniversalChartWidget("測試圖表")

# 準備數據
x_data = [0, 1, 2, 3, 4, 5]
temp_data = [20.0, 21.5, 23.0, 24.5, 26.0, 27.5]
wind_data = [10.0, 12.3, 15.6, 18.9, 22.1, 25.4]

# 創建數據系列
temp_series = ChartDataSeries("溫度", x_data, temp_data, "cyan", 2, "left")
wind_series = ChartDataSeries("風速", x_data, wind_data, "orange", 2, "right")

# 添加到圖表
chart.add_data_series(temp_series)
chart.add_data_series(wind_series)

# 設置軸標籤
chart.set_axis_labels("時間", "溫度", "風速", "秒", "°C", "km/h")

# 顯示圖表
chart.show()
app.exec_()
```

### JSON 載入範例
```python
# JSON 數據
json_data = {
    "chart_title": "環境監測數據",
    "x_axis": {"label": "時間", "unit": "s", "data": [0, 1, 2, 3, 4, 5]},
    "left_y_axis": {"label": "溫度", "unit": "°C", "data": [20.0, 21.5, 23.0, 24.5, 26.0, 27.5]},
    "right_y_axis": {"label": "風速", "unit": "km/h", "data": [10.0, 12.3, 15.6, 18.9, 22.1, 25.4]}
}

# 載入數據
chart.load_from_json(json_data)
```

### 信號連接範例
```python
# 連接信號
chart.chart_clicked.connect(self.on_chart_clicked)
chart.data_point_hovered.connect(self.on_data_hovered)

def on_chart_clicked(self, x, y):
    print(f"圖表點擊位置: X={x:.2f}, Y={y:.2f}")

def on_data_hovered(self, info):
    print(f"懸停信息: {info}")
```

## 🔧 技術實現細節

### 座標轉換算法
```python
# X座標轉換（考慮縮放和偏移）
def data_to_screen_x(self, data_x):
    chart_area = self.get_chart_area()
    x_min, x_max = self.get_overall_x_range()
    x_normalized = (data_x - x_min) / (x_max - x_min)
    screen_x_raw = chart_area.left() + x_normalized * chart_area.width()
    screen_x = screen_x_raw * self.x_scale + self.x_offset
    return screen_x

# Y座標轉換（考慮縮放和偏移）
def data_to_screen_y(self, data_y, y_axis="left"):
    chart_area = self.get_chart_area()
    y_min, y_max = self.get_y_range_for_axis(y_axis)
    y_normalized = (data_y - y_min) / (y_max - y_min)
    screen_y_raw = chart_area.bottom() - y_normalized * chart_area.height()
    
    if y_axis == "left":
        screen_y = screen_y_raw * self.y_scale + self.y_offset
    else:
        screen_y = screen_y_raw * self.right_y_scale + self.right_y_offset
    
    return screen_y
```

### 插值算法
```python
# 線性插值計算Y值
def get_y_value_at_x(self, target_x, y_axis="left"):
    series_for_axis = [s for s in self.data_series if s.y_axis == y_axis]
    if not series_for_axis:
        return None
    
    series = series_for_axis[0]
    x_data, y_data = series.x_data, series.y_data
    
    # 找到插值區間
    for i in range(len(x_data) - 1):
        if x_data[i] <= target_x <= x_data[i + 1]:
            x1, x2 = x_data[i], x_data[i + 1]
            y1, y2 = y_data[i], y_data[i + 1]
            
            if x2 == x1:
                return y1
            
            # 線性插值
            ratio = (target_x - x1) / (x2 - x1)
            return y1 + ratio * (y2 - y1)
    
    # 邊界處理
    if target_x < x_data[0]:
        return y_data[0]
    else:
        return y_data[-1]
```

## ⚠️ 使用注意事項

### 數據要求
1. **數據長度一致**: X軸數據長度必須與Y軸數據長度一致
2. **數據類型**: 所有數據必須為數值類型（int, float）
3. **數據範圍**: 避免極大或極小的數值，建議使用合理的數據範圍

### 性能考慮
1. **大數據集**: 超過10000個數據點時，建議進行數據採樣
2. **實時更新**: 頻繁更新數據時，建議批量處理而非逐點更新
3. **記憶體管理**: 清除不需要的數據系列以釋放記憶體

### 視覺效果
1. **顏色對比**: 確保數據線顏色與黑色背景有足夠對比度
2. **線條寬度**: 根據數據重要性調整線條寬度
3. **軸標籤**: 提供清晰的軸標籤和單位信息

## 🔗 相關資源

### 依賴模組
- `PyQt5.QtWidgets`: GUI 基礎組件
- `PyQt5.QtCore`: 核心功能（信號、槽、事件）
- `PyQt5.QtGui`: 繪圖功能（QPainter, QColor, QPen）

### 相關文檔
- [PyQt5 官方文檔](https://doc.qt.io/qtforpython/)
- [F1T 系統架構文檔](../../../README.md)
- [GUI 組件開發指南](../../development_tracking/GUI組件開發指南.md)

### 測試檔案
- `test_universal_chart.py`: 基本功能測試
- `tests/gui/test_universal_chart_widget.py`: 完整測試套件

## 📈 更新歷史

| 日期 | 版本 | 變更內容 | 作者 |
|------|------|----------|------|
| 2025-08-25 | 1.0.0 | 初始版本，完整功能實現 | AI Assistant |
| 2025-08-25 | 1.0.1 | 新增 Ctrl+滾輪同時縮放X軸和Y軸功能 | AI Assistant |
| 2025-08-25 | 1.0.2 | 修正雙Y軸座標刻度同步縮放顯示 | AI Assistant |

---
*本文檔由 F1T-LOCAL-V13 自動化文檔系統生成 - UniversalChartWidget 技術文檔*
