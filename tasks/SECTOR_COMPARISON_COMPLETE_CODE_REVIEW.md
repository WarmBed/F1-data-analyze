# 🔍 理想圈分段對比模組 - 完整深度 Code Review

**執行時間**: 2025-10-10  
**審查範圍**: `ideal_lap_sector_comparison` 與 3 個參考模組的逐行對比  
**審查目的**: 找出所有假設性編程問題，確保實現正確性

---

## 📋 執行概要

### 檢查的模組
1. ✅ **ideal_lap_ranking_table** (參考模組 1 - 表格型)
2. ✅ **detailed_lap_analysis** (參考模組 2 - QPainter 圖表型)
3. ✅ **lap_box_plot_analysis** (參考模組 3 - QPainter 圖表型)
4. ❌ **ideal_lap_sector_comparison** (當前錯誤模組)

### 錯誤嚴重程度
- 🔴 **阻斷性錯誤** (Blocker): 3 個
- 🟡 **嚴重錯誤** (Critical): 2 個
- 🟠 **重要問題** (Major): 4 個
- 🔵 **次要問題** (Minor): 3 個

**總計**: **12 個問題**

---

## 🔴 阻斷性錯誤 (Blocker) - 必須立即修正

### B1. 假設 UniversalChartWidget 使用 matplotlib ⚠️ **致命錯誤**

**發現位置**: `ideal_lap_sector_comparison_widget.py` Lines 76-211

**錯誤代碼**:
```python
# ❌ 錯誤：假設 UniversalChartWidget 有 matplotlib 屬性
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    def draw_comparison_bars(self, comparison_data, statistics):
        self.ax.clear()  # ❌ self.ax 不存在！
        self.ax.barh(...)  # ❌ matplotlib 方法
        self.figure.tight_layout()  # ❌ self.figure 不存在！
        self.canvas.draw()  # ❌ self.canvas 不存在！

    def _draw_no_data_message(self):
        self.ax.clear()  # ❌ Line 211
        self.ax.text(...)  # ❌ matplotlib 方法
        self.canvas.draw()  # ❌ 不存在

    def _draw_error_message(self, error: str):
        self.ax.clear()  # ❌ Line 225
        self.ax.text(...)  # ❌ matplotlib 方法
        self.canvas.draw()  # ❌ 不存在
```

**實際基類結構** (UniversalChartWidget):
```python
# ✅ 實際：UniversalChartWidget 使用 QPainter（PyQt5 原生繪圖）
class UniversalChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_series = []      # ✅ ChartDataSeries 列表
        self.annotations = []      # ✅ ChartAnnotation 列表
        # ❌ 沒有 self.ax, self.figure, self.canvas
    
    def paintEvent(self, event):
        """✅ 使用 QPainter 繪製"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        # ... QPainter 繪圖邏輯
        painter.end()
```

**正確實現** (參考 detailed_lap_analysis):
```python
# ✅ 正確模式 1：直接繼承 QWidget + 使用 QPainter
class LaptimeChartWidget(QWidget):  # ✅ 繼承 QWidget，不是 UniversalChartWidget
    def __init__(self, parent=None):
        super().__init__(parent)
        self.series_list = []  # ✅ 自定義數據結構
    
    def paintEvent(self, event):
        """✅ 使用 QPainter 繪製"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 繪製背景
        painter.fillRect(self.rect(), ChartTheme.BACKGROUND)
        
        # 繪製網格和軸
        self._draw_grid_and_axes(painter, chart_rect, x_range, y_range)
        
        # 繪製數據線
        self._draw_data_lines(painter, chart_rect, x_range, y_range)
        
        # 結束繪製
        painter.end()
```

**正確實現** (參考 lap_box_plot_analysis):
```python
# ✅ 正確模式 2：繼承 QWidget + 使用 QPainter
class LapTimeBoxPlotChartWidget(QWidget):  # ✅ 繼承 QWidget
    def paintEvent(self, event):
        """繪製事件"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 繪製背景
            self._draw_background(painter)
            
            # 繪製網格
            self._draw_grid(painter)
            
            # 繪製座標軸
            self._draw_axes(painter)
            
            # 繪製箱型圖
            if self.driver_laptimes:
                self._draw_box_plots(painter)
            else:
                self._draw_no_data_message(painter)
        finally:
            # 🔑 確保總是釋放 QPainter 資源
            painter.end()
```

**影響範圍**:
- ❌ **整個 Widget 的繪圖實現完全錯誤**（約 650 行代碼）
- ❌ 所有 `self.ax.*` 調用會拋出 `AttributeError`
- ❌ 所有 `self.figure.*` 調用會拋出 `AttributeError`
- ❌ 所有 `self.canvas.*` 調用會拋出 `AttributeError`

**修正方案**:
1. **選項 A**（推薦）：改為繼承 `QWidget`，參考 `LaptimeChartWidget` 實現
2. **選項 B**：使用 `UniversalChartWidget` 的正確方法（`self.data_series`, `paintEvent()`）

**假設性編程類型**: **創造性假設整個繪圖系統**

---

### B2. 沒有實現抽象基類方法 ⚠️

**發現位置**: `ideal_lap_sector_comparison_widget.py` - 缺少必要方法

**錯誤描述**:
如果 `IdealLapSectorComparisonWidget` 繼承 `UniversalChartWidget`，必須實現基類的抽象方法或覆寫關鍵方法。

**檢查 UniversalChartWidget 要求**:
```python
# UniversalChartWidget 的關鍵方法（需要檢查是否為抽象方法）
class UniversalChartWidget(QWidget):
    def paintEvent(self, event):  # ✅ 可覆寫
        # ...
    
    def get_chart_area(self):  # ⚠️ 需要檢查是否為抽象方法
        # ...
    
    def draw_axes(self, painter, chart_area):  # ⚠️
        # ...
```

**當前問題**:
- ❌ `IdealLapSectorComparisonWidget` 沒有覆寫 `paintEvent()`
- ❌ 沒有實現任何與 `UniversalChartWidget` 配合的方法

**正確實現** (如果必須使用 UniversalChartWidget):
```python
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    def paintEvent(self, event):
        """✅ 必須覆寫 paintEvent"""
        super().paintEvent(event)  # 或完全重寫
    
    # 其他必要方法...
```

**修正方案**:
1. 檢查 `UniversalChartWidget` 的抽象方法列表
2. 實現所有必要方法
3. **或改為直接繼承 `QWidget`**（推薦）

---

### B3. 假設 update_chart() 方法存在 ⚠️ **已在第二次錯誤中發現**

**發現位置**: `ideal_lap_sector_comparison_mdi.py` (已修正)

**錯誤代碼** (原始版本):
```python
# ❌ 錯誤：假設 chart_widget 有 update_chart() 方法
def _on_data_loaded(self, api_data):
    self.chart_widget.update_chart(data)  # ❌ 方法不存在！
```

**正確實現** (參考 ranking_table):
```python
# ✅ 正確：調用實際存在的方法
def _on_data_loaded(self, api_data):
    ranking_data = api_data.get("ranking", [])
    self.ranking_table.populate_table(ranking_data)  # ✅ 實際方法
```

**當前狀態**: ✅ 已修正為 `_on_data_loaded(api_data)`

---

## 🟡 嚴重錯誤 (Critical)

### C1. 錯誤的錯誤處理實現 ⚠️ **已在第二次錯誤中發現**

**發現位置**: `ideal_lap_sector_comparison_mdi.py` (已修正)

**錯誤代碼** (原始版本):
```python
# ❌ 錯誤：假設 self 是 QWidget，但實際繼承自 UniversalAnalysisMDI
def _on_api_error(self, error_msg: str):
    QMessageBox.warning(self, "API Error", error_msg)  # ❌ TypeError!
```

**UniversalAnalysisMDI 的實際基類**:
```python
# ❌ UniversalAnalysisMDI 不是 QWidget
class UniversalAnalysisMDI:
    """通用分析 MDI 管理器（不是 QWidget）"""
    def __init__(self, ...):
        self.chart_widget = widget_class(...)  # ✅ 這才是 QWidget
        # self 不是 QWidget！
```

**正確實現** (參考 ranking_table):
```python
# ✅ 正確：實現 _show_error() 方法
def _show_error(self, title: str, message: str):
    """顯示錯誤訊息對話框"""
    parent = self.chart_widget if hasattr(self, 'chart_widget') else None
    QMessageBox.critical(parent, title, message)

def _on_api_error(self, error_msg: str):
    """API 錯誤處理"""
    self._show_error("API 錯誤", error_msg)  # ✅ 使用基類方法
```

**當前狀態**: ✅ 已修正，添加了 `_show_error()` 方法

---

### C2. 缺少統計面板更新方法 ⚠️

**發現位置**: `ideal_lap_sector_comparison_widget.py` - 缺少方法

**問題描述**:
`IdealLapSectorComparisonWidget` 沒有實現統計資訊更新方法，但資料結構中有 `statistics` 欄位。

**參考實現** (ranking_table):
```python
# ✅ ranking_table 有完整的統計面板實現
class IdealLapRankingTableWidget(QWidget):
    def _create_statistics_panel(self) -> QGroupBox:
        """✅ 創建統計資訊面板"""
        stats_group = QGroupBox("統計資訊")
        # ... 創建統計標籤
        return stats_group
    
    def update_statistics_panel(self, statistics: Dict):
        """✅ 更新統計資訊"""
        self.stats_total_drivers.setText(str(statistics.get("total_drivers", 0)))
        # ... 更新其他統計資訊
```

**當前問題**:
```python
# ❌ sector_comparison_widget 缺少統計面板方法
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    def draw_comparison_bars(self, comparison_data, statistics):
        self.statistics = statistics or {}  # ✅ 接收統計資訊
        # ❌ 但沒有方法來顯示或更新統計資訊！
```

**修正方案**:
1. 添加 `_create_statistics_panel()` 方法
2. 添加 `update_statistics_panel(statistics)` 方法
3. 在 `draw_comparison_bars()` 中調用 `update_statistics_panel()`

**假設性編程類型**: **假設不需要統計面板**

---

## 🟠 重要問題 (Major)

### M1. 清空方法不完整 ⚠️

**發現位置**: `ideal_lap_sector_comparison_widget.py` Line 330

**錯誤代碼**:
```python
# ❌ 不完整：假設有 self.ax
def clear_chart(self):
    """清空圖表"""
    self.comparison_data = []
    self.statistics = {}
    
    # ❌ 假設 self.ax 存在
    if hasattr(self, 'ax') and self.ax:
        self.ax.clear()
        self.ax.text(...)  # ❌ matplotlib 方法
        self.canvas.draw()  # ❌ self.canvas 不存在
```

**正確實現** (參考 lap_box_plot_analysis):
```python
# ✅ 正確：使用 QPainter 重繪
def clear_chart(self):
    """清空圖表"""
    self.driver_laptimes = {}  # ✅ 清空數據
    self.statistics = {}
    self.current_data = None
    
    print("[BOXPLOT_CHART] 圖表已清空")
    self.update()  # ✅ 觸發重繪（會調用 paintEvent）
```

**正確實現** (參考 detailed_lap_analysis):
```python
# ✅ 正確：清空數據並重繪
def update_series_data(self, series_list: List[ChartSeries]):
    """更新圖表數據系列"""
    self.series_list = series_list  # ✅ 直接替換數據
    self.update()  # ✅ 觸發重繪
```

**修正方案**:
```python
# ✅ 修正後的 clear_chart()
def clear_chart(self):
    """清空圖表"""
    self.comparison_data = []
    self.statistics = {}
    
    print("[SECTOR_COMPARISON] 圖表已清空")
    self.update()  # ✅ 觸發 paintEvent 重繪
```

---

### M2. 缺少 _debug() 方法實現 ⚠️

**發現位置**: `ideal_lap_sector_comparison_widget.py` - 多處調用

**錯誤代碼**:
```python
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._debug("[SECTOR_COMPARISON_WIDGET] 圖表元件已初始化")  # ❌ 方法未定義
    
    def draw_comparison_bars(self, ...):
        self._debug(f"[DRAW] 開始繪製棒狀圖...")  # ❌ 方法未定義
```

**檢查基類**:
```python
# UniversalChartWidget 沒有 _debug() 方法
class UniversalChartWidget(QWidget):
    # ❌ 沒有 _debug() 方法
    pass
```

**正確實現選項**:

**選項 A** (推薦 - 參考 data_loader):
```python
# ✅ 在 Widget 中實現 _debug()
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._debug_enabled = True  # ✅ 調試開關
    
    def _debug(self, message: str):
        """調試輸出"""
        if self._debug_enabled:
            print(message)
```

**選項 B** (直接使用 print):
```python
# ✅ 直接使用 print（參考 lap_box_plot_analysis）
class IdealLapSectorComparisonWidget(QWidget):
    def draw_comparison_bars(self, ...):
        print("[SECTOR_COMPARISON] 開始繪製棒狀圖...")  # ✅ 直接 print
```

**當前問題**: 所有 `self._debug()` 調用會拋出 `AttributeError`

---

### M3. 排序方法沒有觸發重繪 ⚠️

**發現位置**: `ideal_lap_sector_comparison_widget.py` Line 260

**錯誤代碼**:
```python
def sort_data(self, sort_key: str):
    """排序資料並重繪"""
    # ... 排序邏輯
    self.draw_comparison_bars(sorted_data, self.statistics)  # ❌ 假設 matplotlib
```

**問題**:
1. `draw_comparison_bars()` 使用 matplotlib（會失敗）
2. 沒有使用 QPainter 的重繪機制

**正確實現** (QPainter 模式):
```python
def sort_data(self, sort_key: str):
    """排序資料並重繪"""
    if not self.comparison_data:
        return
    
    # 排序邏輯
    if sort_key == "position":
        sorted_data = sorted(self.comparison_data, key=lambda x: x.get("position", 99))
    # ... 其他排序選項
    
    self.comparison_data = sorted_data  # ✅ 更新數據
    self.current_sort = sort_key
    self.update()  # ✅ 觸發 paintEvent 重繪
    self.sort_changed.emit(sort_key)  # ✅ 發射信號
```

---

### M4. 缺少滑鼠事件處理 ⚠️

**發現位置**: `ideal_lap_sector_comparison_widget.py` - 未實現

**對比參考模組**:

**detailed_lap_analysis**:
```python
# ✅ 完整的滑鼠事件處理
class LaptimeChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # ✅ 啟用滑鼠追蹤
        self.hover_point = None
        self.pinned_tooltips = []
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """✅ 滑鼠移動事件"""
        # 檢測懸停點
        # 更新 tooltip
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """✅ 滑鼠點擊事件"""
        if event.button() == Qt.LeftButton:
            # 固定 tooltip
            pass
```

**lap_box_plot_analysis**:
```python
# ✅ 滑鼠事件處理
class LapTimeBoxPlotChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # ✅ 啟用滑鼠追蹤
        self.hover_driver = None
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """✅ 懸停檢測"""
        # 檢測懸停的箱型圖
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """✅ 點擊發射信號"""
        if self.hover_driver:
            self.chart_clicked.emit(self.hover_driver)  # ✅ 發射信號
```

**當前問題**:
```python
# ❌ sector_comparison 沒有任何滑鼠事件處理
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    # ❌ 沒有 mouseMoveEvent
    # ❌ 沒有 mousePressEvent
    # ❌ 沒有 setMouseTracking
    # ❌ 定義了 bar_clicked 信號但從未發射
    bar_clicked = pyqtSignal(str)  # ❌ 從未發射
```

**修正方案**:
1. 添加 `setMouseTracking(True)`
2. 實現 `mouseMoveEvent()` 檢測懸停
3. 實現 `mousePressEvent()` 發射 `bar_clicked` 信號
4. 添加懸停視覺反饋

---

## 🔵 次要問題 (Minor)

### N1. 缺少圖表匯出功能 ⚠️

**對比參考模組**:

**lap_box_plot_analysis**:
```python
# ✅ 完整的圖表匯出
def export_chart(self, filepath: str) -> bool:
    """✅ 匯出圖表為圖片"""
    try:
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        return pixmap.save(filepath)
    except Exception as e:
        print(f"[ERROR] 匯出失敗: {e}")
        return False
```

**當前問題**:
```python
# ❌ sector_comparison 沒有匯出功能
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    # ❌ 沒有 export_chart() 方法
    pass
```

**修正方案**: 添加圖表匯出方法

---

### N2. 沒有最小尺寸設置 ⚠️

**對比參考模組**:

**detailed_lap_analysis**:
```python
def __init__(self, parent=None):
    super().__init__(parent)
    self.setMinimumSize(200, 100)  # ✅ 設置最小尺寸
```

**lap_box_plot_analysis**:
```python
def __init__(self, parent=None):
    super().__init__(parent)
    self.setMinimumSize(200, 100)  # ✅ 統一為 200x100
```

**當前問題**:
```python
# ❌ sector_comparison 沒有設置最小尺寸
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ❌ 沒有 setMinimumSize
```

**修正方案**:
```python
def __init__(self, parent=None):
    super().__init__(parent)
    self.setMinimumSize(200, 100)  # ✅ 與其他模組一致
```

---

### N3. 國際化 (i18n) 支援缺失 ⚠️

**對比參考模組**:

**lap_box_plot_analysis**:
```python
# ✅ 使用國際化函數
from core.gui_i18n import tr

def _draw_axis_labels(self, painter: QPainter):
    painter.drawText(
        ...,
        tr("lap_box_plot.y_axis_title", "Lap Time (seconds)")  # ✅ i18n
    )
```

**當前問題**:
```python
# ❌ sector_comparison 沒有使用 i18n
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    def draw_comparison_bars(self, ...):
        self.ax.set_xlabel("Lap Time (seconds)", ...)  # ❌ 硬編碼英文
        self.ax.set_title("Ideal Lap vs Fastest Lap - Sector Breakdown", ...)  # ❌ 硬編碼
```

**修正方案**: 使用 `tr()` 函數包裝所有使用者可見文字

---

## 📊 完整假設性編程問題列表

### 假設類型 1: 假設基類實現
| 問題 ID | 假設內容 | 實際情況 | 嚴重程度 |
|---------|---------|---------|---------|
| B1 | 假設 `UniversalChartWidget` 有 `self.ax` | 沒有（使用 QPainter） | 🔴 Blocker |
| B1 | 假設 `UniversalChartWidget` 有 `self.figure` | 沒有（使用 QPainter） | 🔴 Blocker |
| B1 | 假設 `UniversalChartWidget` 有 `self.canvas` | 沒有（使用 QPainter） | 🔴 Blocker |
| B2 | 假設不需要覆寫 `paintEvent()` | 必須覆寫或使用基類實現 | 🔴 Blocker |

### 假設類型 2: 假設方法存在
| 問題 ID | 假設內容 | 實際情況 | 嚴重程度 |
|---------|---------|---------|---------|
| B3 | 假設 `chart_widget` 有 `update_chart()` | 沒有此方法 | 🔴 Blocker（已修正） |
| M2 | 假設基類有 `_debug()` 方法 | 沒有此方法 | 🟠 Major |

### 假設類型 3: 假設基類類型
| 問題 ID | 假設內容 | 實際情況 | 嚴重程度 |
|---------|---------|---------|---------|
| C1 | 假設 `UniversalAnalysisMDI` 是 `QWidget` | 不是 `QWidget` | 🟡 Critical（已修正） |

### 假設類型 4: 假設不需要實現
| 問題 ID | 假設內容 | 實際情況 | 嚴重程度 |
|---------|---------|---------|---------|
| C2 | 假設不需要統計面板更新方法 | 需要（參考 ranking_table） | 🟡 Critical |
| M4 | 假設不需要滑鼠事件處理 | 需要（參考 2 個圖表模組） | 🟠 Major |
| N1 | 假設不需要圖表匯出功能 | 需要（參考 lap_box_plot） | 🔵 Minor |

### 假設類型 5: 假設實現正確
| 問題 ID | 假設內容 | 實際情況 | 嚴重程度 |
|---------|---------|---------|---------|
| M1 | 假設 `clear_chart()` 的 matplotlib 實現正確 | 需要 QPainter 模式 | 🟠 Major |
| M3 | 假設 `sort_data()` 的 matplotlib 重繪正確 | 需要 `self.update()` | 🟠 Major |

### 假設類型 6: 假設不需要功能
| 問題 ID | 假設內容 | 實際情況 | 嚴重程度 |
|---------|---------|---------|---------|
| N2 | 假設不需要最小尺寸設置 | 需要（統一為 200x100） | 🔵 Minor |
| N3 | 假設不需要國際化支援 | 需要（使用 `tr()` 函數） | 🔵 Minor |

---

## 🔬 模組對比分析

### 對比 1: Widget 基類選擇

| 模組 | 基類 | 繪圖方式 | 是否正確 |
|------|------|---------|---------|
| **ideal_lap_ranking_table** | `QWidget` | Qt 原生（QTableWidget） | ✅ 正確 |
| **detailed_lap_analysis** | `QWidget` | QPainter | ✅ 正確 |
| **lap_box_plot_analysis** | `QWidget` | QPainter | ✅ 正確 |
| **sector_comparison** | `UniversalChartWidget` | ❌ matplotlib（錯誤） | ❌ 錯誤 |

**結論**: `sector_comparison` 應改為繼承 `QWidget` 並使用 QPainter 繪圖。

---

### 對比 2: paintEvent 實現

**detailed_lap_analysis**:
```python
def paintEvent(self, event):
    """✅ QPainter 繪製"""
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 清除背景
    painter.fillRect(self.rect(), ChartTheme.BACKGROUND)
    
    # 繪製數據
    self._draw_grid_and_axes(painter, chart_rect, x_range, y_range)
    self._draw_data_lines(painter, chart_rect, x_range, y_range)
    
    painter.end()  # ✅ 總是釋放資源
```

**lap_box_plot_analysis**:
```python
def paintEvent(self, event):
    """✅ QPainter 繪製"""
    painter = QPainter(self)
    try:
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 繪製背景
        self._draw_background(painter)
        
        # 繪製網格和軸
        self._draw_grid(painter)
        self._draw_axes(painter)
        
        # 繪製數據
        if self.driver_laptimes:
            self._draw_box_plots(painter)
        else:
            self._draw_no_data_message(painter)
    finally:
        painter.end()  # ✅ 總是釋放資源
```

**sector_comparison**:
```python
# ❌ 完全沒有 paintEvent 實現
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    # ❌ 沒有覆寫 paintEvent
    # ❌ 假設基類會自動繪製 matplotlib 圖表
    pass
```

**結論**: `sector_comparison` 必須實現 `paintEvent()` 並使用 QPainter 繪製。

---

### 對比 3: 錯誤處理方法

**ranking_table** (MDI):
```python
# ✅ 實現 _show_error() 方法
def _show_error(self, title: str, message: str):
    """顯示錯誤訊息對話框"""
    parent = self.ranking_table if hasattr(self, 'ranking_table') else None
    QMessageBox.critical(parent, title, message)

def _on_api_error(self, error_msg: str):
    """API 錯誤處理"""
    self._show_error("API 錯誤", error_msg)  # ✅ 使用基類方法
```

**sector_comparison** (MDI - 原始版本):
```python
# ❌ 錯誤：假設 self 是 QWidget
def _on_api_error(self, error_msg: str):
    QMessageBox.warning(self, "API Error", error_msg)  # ❌ TypeError!
```

**sector_comparison** (MDI - 修正後):
```python
# ✅ 已修正：實現 _show_error() 方法
def _show_error(self, title: str, message: str):
    """顯示錯誤訊息對話框"""
    parent = self.chart_widget if hasattr(self, 'chart_widget') else None
    QMessageBox.critical(parent, title, message)
```

**結論**: 錯誤處理已修正，符合 ranking_table 模式。

---

### 對比 4: 統計資訊更新

**ranking_table**:
```python
# ✅ 完整的統計面板實現
def _create_statistics_panel(self) -> QGroupBox:
    """創建統計資訊面板"""
    stats_group = QGroupBox("統計資訊")
    layout = QGridLayout()
    
    # 創建統計標籤
    self.stats_total_drivers = QLabel("0")
    self.stats_perfect_count = QLabel("0")
    # ...
    
    layout.addWidget(QLabel("總車手數:"), 0, 0)
    layout.addWidget(self.stats_total_drivers, 0, 1)
    # ...
    
    return stats_group

def update_statistics_panel(self, statistics: Dict):
    """更新統計資訊"""
    self.stats_total_drivers.setText(str(statistics.get("total_drivers", 0)))
    self.stats_perfect_count.setText(str(statistics.get("perfect_count", 0)))
    # ...

def populate_table(self, ranking_data):
    """填充表格資料"""
    # ... 填充表格
    
    # ✅ 更新統計面板
    if self.statistics:
        self.update_statistics_panel(self.statistics)
```

**sector_comparison**:
```python
# ❌ 沒有統計面板實現
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    def draw_comparison_bars(self, comparison_data, statistics):
        self.statistics = statistics or {}  # ✅ 接收統計資訊
        # ❌ 沒有方法來顯示統計資訊
```

**結論**: `sector_comparison` 需要添加統計面板實現。

---

### 對比 5: 清空方法

**lap_box_plot_analysis**:
```python
# ✅ QPainter 模式的清空方法
def clear_chart(self):
    """清空圖表"""
    self.driver_laptimes = {}
    self.statistics = {}
    self.current_data = None
    
    print("[BOXPLOT_CHART] 圖表已清空")
    self.update()  # ✅ 觸發 paintEvent 重繪
```

**sector_comparison**:
```python
# ❌ matplotlib 模式的清空方法（會失敗）
def clear_chart(self):
    """清空圖表"""
    self.comparison_data = []
    self.statistics = {}
    
    if hasattr(self, 'ax') and self.ax:
        self.ax.clear()  # ❌ self.ax 不存在
        self.ax.text(...)  # ❌ matplotlib 方法
        self.canvas.draw()  # ❌ self.canvas 不存在
```

**結論**: `sector_comparison` 的 `clear_chart()` 需要改為 QPainter 模式。

---

### 對比 6: 滑鼠事件處理

**detailed_lap_analysis**:
```python
# ✅ 完整的滑鼠事件處理
class LaptimeChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # ✅ 啟用滑鼠追蹤
        self.hover_point = None
        self.pinned_tooltips = []
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """滑鼠移動事件"""
        # 檢測懸停點邏輯
        # ...
        self.update()  # ✅ 觸發重繪
    
    def mousePressEvent(self, event: QMouseEvent):
        """滑鼠點擊事件"""
        if event.button() == Qt.LeftButton:
            # 固定 tooltip 邏輯
            # ...
```

**lap_box_plot_analysis**:
```python
# ✅ 滑鼠事件處理
class LapTimeBoxPlotChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # ✅ 啟用滑鼠追蹤
        self.hover_driver = None
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """懸停檢測"""
        # 檢測懸停的箱型圖
        # ...
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """點擊發射信號"""
        if self.hover_driver:
            self.chart_clicked.emit(self.hover_driver)  # ✅ 發射信號
```

**sector_comparison**:
```python
# ❌ 完全沒有滑鼠事件處理
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    bar_clicked = pyqtSignal(str)  # ❌ 定義信號但從未發射
    
    # ❌ 沒有 mouseMoveEvent
    # ❌ 沒有 mousePressEvent
    # ❌ 沒有 setMouseTracking
```

**結論**: `sector_comparison` 需要添加完整的滑鼠事件處理。

---

## 📋 完整修正檢查清單

### 🔴 阻斷性修正（必須立即完成）

- [ ] **B1: 重寫整個 Widget 繪圖邏輯**
  - [ ] 改為繼承 `QWidget` 而非 `UniversalChartWidget`
  - [ ] 刪除所有 matplotlib 代碼（`self.ax.*`, `self.figure.*`, `self.canvas.*`）
  - [ ] 實現 `paintEvent(self, event)` 方法
  - [ ] 使用 `QPainter` 繪製水平堆疊棒狀圖
  - [ ] 參考 `detailed_lap_analysis` 或 `lap_box_plot_analysis` 的實現

- [ ] **B2: 確保基類方法正確實現**
  - [ ] 如果繼承 `QWidget`：實現 `paintEvent()`
  - [ ] 如果繼承 `UniversalChartWidget`：檢查並實現所有抽象方法

- [ ] **B3: 驗證方法調用正確性** (已修正)
  - [x] 確認 `_on_data_loaded()` 方法調用正確
  - [x] 確認不再假設 `update_chart()` 存在

### 🟡 嚴重修正

- [x] **C1: 錯誤處理修正** (已修正)
  - [x] 實現 `_show_error()` 方法
  - [x] 修正所有 `QMessageBox` 調用

- [ ] **C2: 添加統計面板**
  - [ ] 實現 `_create_statistics_panel()` 方法
  - [ ] 實現 `update_statistics_panel(statistics)` 方法
  - [ ] 在數據載入時調用統計面板更新

### 🟠 重要修正

- [ ] **M1: 修正 clear_chart() 方法**
  - [ ] 刪除 matplotlib 代碼
  - [ ] 使用 `self.update()` 觸發重繪

- [ ] **M2: 實現 _debug() 方法**
  - [ ] 添加 `self._debug_enabled = True`
  - [ ] 實現 `_debug(message)` 方法
  - [ ] 或改為直接使用 `print()`

- [ ] **M3: 修正 sort_data() 方法**
  - [ ] 刪除 matplotlib 重繪代碼
  - [ ] 使用 `self.update()` 觸發重繪

- [ ] **M4: 添加滑鼠事件處理**
  - [ ] 添加 `setMouseTracking(True)`
  - [ ] 實現 `mouseMoveEvent()`
  - [ ] 實現 `mousePressEvent()`
  - [ ] 正確發射 `bar_clicked` 信號

### 🔵 次要修正

- [ ] **N1: 添加圖表匯出功能**
  - [ ] 實現 `export_chart(filepath)` 方法

- [ ] **N2: 設置最小尺寸**
  - [ ] 添加 `self.setMinimumSize(200, 100)`

- [ ] **N3: 國際化支援**
  - [ ] 導入 `from core.gui_i18n import tr`
  - [ ] 使用 `tr()` 包裝所有使用者可見文字

---

## 🧪 測試驗證清單

### 階段 1: Import 測試（5 分鐘內）
- [ ] 能成功 import Widget 模組
- [ ] 能成功 import MDI 模組
- [ ] 能成功 import DataLoader 模組
- [ ] 無任何 ImportError

### 階段 2: 方法驗證測試（10 分鐘內）
- [ ] Widget 有 `paintEvent()` 方法
- [ ] Widget 有 `update()` 方法
- [ ] Widget 有 `clear_chart()` 方法
- [ ] MDI 有 `_show_error()` 方法
- [ ] MDI 有 `_on_data_loaded()` 方法
- [ ] 所有引用的方法都已確認存在（不再假設）

### 階段 3: GUI 整合測試（15 分鐘內）
- [ ] GUI 啟動無錯誤
- [ ] 選單項目顯示正確
- [ ] 點擊選單項目無 AttributeError
- [ ] 點擊選單項目無 TypeError

### 階段 4: 功能測試（20 分鐘內）
- [ ] API 調用成功
- [ ] 圖表正常繪製（使用 QPainter）
- [ ] 清空圖表功能正常
- [ ] 排序功能正常
- [ ] 滑鼠懸停顯示 Tooltip
- [ ] 滑鼠點擊發射信號
- [ ] 錯誤處理正確觸發
- [ ] 無任何未處理異常

### 階段 5: 完整運行測試（30 分鐘內）
- [ ] 完整流程無任何錯誤
- [ ] 所有功能正常運作
- [ ] 無任何 `AttributeError`
- [ ] 無任何 `TypeError`
- [ ] 無任何假設性編程導致的錯誤

---

## 💡 關鍵學習點

### 1. 絕對不能假設基類實現
- ❌ **錯誤**: 假設 `UniversalChartWidget` 使用 matplotlib
- ✅ **正確**: 檢查基類的實際實現（使用 QPainter）

### 2. 必須參考同類型模組
- ❌ **錯誤**: 只參考 `ranking_table`（表格型）來實現圖表模組
- ✅ **正確**: 參考 `detailed_lap_analysis` 和 `lap_box_plot_analysis`（圖表型）

### 3. 必須實際運行測試
- ❌ **錯誤**: 聲稱"測試通過"但實際從未運行
- ✅ **正確**: 執行完整的 Import → 方法驗證 → GUI 整合 → 功能測試

### 4. 必須驗證每個方法調用
- ❌ **錯誤**: 假設方法存在（`update_chart()`, `self.ax.clear()`）
- ✅ **正確**: 用 `grep_search` 或 `read_file` 驗證方法是否存在

### 5. 必須理解基類類型
- ❌ **錯誤**: 假設 `UniversalAnalysisMDI` 是 `QWidget`
- ✅ **正確**: 檢查基類的繼承鏈，使用正確的錯誤處理方式

---

## 📝 結論

### 總結問題數量
- 🔴 **阻斷性錯誤**: 3 個（B1, B2, B3）
- 🟡 **嚴重錯誤**: 2 個（C1, C2）
- 🟠 **重要問題**: 4 個（M1, M2, M3, M4）
- 🔵 **次要問題**: 3 個（N1, N2, N3）

**總計**: **12 個問題**

### 根本原因
1. **系統性假設性編程**：整個 Widget 的實現基於錯誤的假設（matplotlib）
2. **參考模組選擇錯誤**：只參考了表格型模組，沒有參考圖表型模組
3. **測試缺失**：從未實際運行測試，導致錯誤未被發現
4. **對基類理解不足**：沒有檢查基類的實際實現就開始編碼

### 修正優先級
1. **最優先**：重寫整個 Widget（B1）
2. **次優先**：實現統計面板（C2）、清空方法（M1）、滑鼠事件（M4）
3. **可延後**：圖表匯出（N1）、國際化（N3）

### 預估工作量
- 重寫 Widget 繪圖邏輯：**4-6 小時**
- 添加統計面板：**1-2 小時**
- 修正次要問題：**1-2 小時**
- 完整測試驗證：**2-3 小時**

**總計**: **8-13 小時**

---

**審查完成時間**: 2025-10-10  
**審查員**: GitHub Copilot  
**狀態**: ⚠️ **需要完全重寫 Widget 繪圖邏輯**
