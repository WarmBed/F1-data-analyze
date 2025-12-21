# 🔍 深度架構比較：Lap Time Box Plot vs Throttle Box Plot

## 執行日期：2025-11-13
## 目的：找出為什麼 Throttle 右鍵選單可以運作，而 Lap Time 不行

---

## ⚙️ 階段 1：GUI 主程式的創建流程

### Lap Time Box Plot (`_create_detailed_lap_boxplot_window`)
```python
# 步驟 1：直接導入 MDI 類別
from modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
    LapTimeBoxPlotAnalysis,  # ← MDI 類別
)

# 步驟 2：直接創建 MDI 實例
analysis_module = LapTimeBoxPlotAnalysis(parent=self)

# 步驟 3：直接獲取 Widget
sub_window.setWidget(analysis_module.get_widget())
```

**架構層級**：
```
GUI Main → LapTimeBoxPlotAnalysis (MDI) → get_widget() → LapTimeBoxPlotChartWidget
```

---

### Throttle Box Plot (`module_factory` 通用創建)
```python
# 步驟 1：導入包裝器模組
from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module import (
    ThrottleBoxPlotAnalysisModule,  # ← 包裝器類別
)

# 步驟 2：創建包裝器實例
module = ThrottleBoxPlotAnalysisModule(parent=self)

# 步驟 3：初始化包裝器（內部創建 MDI）
module.initialize_module()

# 步驟 4：透過包裝器獲取 Widget
widget = module.get_widget()
```

**架構層級**：
```
GUI Main → ThrottleBoxPlotAnalysisModule (包裝器)
           ↓
           ThrottleBoxPlotAnalysis (MDI)
           ↓
           get_widget() → ThrottleBoxPlotChartWidget
```

---

## 🚨 關鍵差異 1：架構複雜度

| 項目 | Lap Time | Throttle |
|------|----------|----------|
| **架構層數** | 2 層（GUI → MDI → Widget） | **3 層**（GUI → 包裝器 → MDI → Widget） |
| **導入的類別** | `LapTimeBoxPlotAnalysis` (MDI) | `ThrottleBoxPlotAnalysisModule` (包裝器) |
| **Widget 獲取** | 直接從 MDI 獲取 | 透過包裝器的 `get_widget()` |
| **初始化方式** | 直接調用 MDI 初始化 | 包裝器初始化 → 內部創建 MDI |

---

## 📂 階段 2：檔案結構比較

### Lap Time Box Plot
```
modules/gui/driver_race/lap_box_plot_analysis/
├── lap_box_plot_analysis_mdi.py         # MDI 類別
├── lap_box_plot_chart_widget.py          # Chart Widget
└── lap_box_plot_analysis_module.py       # ❌ 內容錯誤（是 RainAnalysisModule）
```

### Throttle Box Plot
```
modules/gui/Throttle_analysis/throttle_box_plot_analysis/
├── throttle_box_plot_analysis_module.py  # ✅ 包裝器類別
├── throttle_box_plot_analysis_mdi.py     # MDI 類別
└── throttle_box_plot_chart_widget.py     # Chart Widget
```

**關鍵差異**：
- ✅ Throttle 有正確的 `ThrottleBoxPlotAnalysisModule` 包裝器
- ❌ Lap Time 的 `lap_box_plot_analysis_module.py` **內容是 RainAnalysisModule**（檔案混淆！）

---

## 🏗️ 階段 3：類別繼承鏈比較

### Lap Time Box Plot
```python
# lap_box_plot_analysis_mdi.py
class LapTimeBoxPlotAnalysis(UniversalAnalysisMDI):
    def create_chart_widget(self):
        return LapTimeBoxPlotChartWidget(parent=None)
```

### Throttle Box Plot
```python
# throttle_box_plot_analysis_module.py (包裝器)
class ThrottleBoxPlotAnalysisModule(IAnalysisModule):
    def initialize_module(self):
        self._throttle_boxplot_core = ThrottleBoxPlotAnalysis(...)
        self._main_widget = self._throttle_boxplot_core.get_widget()
    
    def get_widget(self):
        return self._main_widget

# throttle_box_plot_analysis_mdi.py (MDI)
class ThrottleBoxPlotAnalysis(UniversalAnalysisMDI):
    def create_chart_widget(self):
        return ThrottleBoxPlotChartWidget(parent=None)
```

**關鍵差異**：
- Throttle 的 Widget 是透過**包裝器的 `_main_widget` 屬性**返回
- Lap Time 的 Widget 是直接從 **MDI 的 `get_widget()`** 返回

---

## 🖼️ 階段 4：Widget 在 MDI 中的嵌套結構

### 共同的基類結構 (UniversalAnalysisMDI._setup_ui)
```python
# Line 657-663: universal_analysis_mdi_base.py
chart_frame = QFrame()
chart_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
chart_frame.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # ← 剛修改
chart_frame.setFocusPolicy(Qt.NoFocus)  # ← 剛修改

chart_layout = QVBoxLayout(chart_frame)
chart_layout.addWidget(self.chart_widget)  # ← Widget 被包裹在 QFrame 中
```

**嵌套層級**：
```
QMdiSubWindow
└── QSplitter (中央分割器)
    └── QFrame (chart_frame)
        └── QVBoxLayout
            └── ChartWidget (實際的繪圖 Widget)
```

---

## 🖱️ 階段 5：滑鼠事件處理比較

### Chart Widget 的 mousePressEvent 實現

#### Lap Time Box Plot
```python
# lap_box_plot_chart_widget.py (Lines 670-700)
def mousePressEvent(self, event):
    print(f"🖱️ mousePressEvent 被觸發！Button: {event.button()}")  # ← 調試輸出
    
    if event.button() == Qt.RightButton:
        print(f"🖱️ 右鍵點擊！Position: {event.pos()}")
        
        hovered_driver = self._detect_hovered_driver(event.pos())
        print(f"🖱️ 檢測到的車手: {hovered_driver}")
        
        if hovered_driver:
            print(f"🖱️ 顯示選單: 隱藏 {hovered_driver}")
            menu = QMenu(self)
            hide_action = menu.addAction(f"隱藏 {hovered_driver}")
            hide_action.triggered.connect(lambda: self._hide_driver(hovered_driver))
            menu.exec_(self.mapToGlobal(event.pos()))
            event.accept()
            return
    
    super().mousePressEvent(event)
```

**特點**：
- ✅ 有詳細的調試輸出
- ✅ 使用 `_detect_hovered_driver` 實時檢測
- ✅ 邏輯完整

#### Throttle Box Plot
```python
# throttle_box_plot_chart_widget.py (Lines 434-464)
def mousePressEvent(self, event):
    # ❌ 無調試輸出
    
    if event.button() == Qt.RightButton:
        hovered_driver = self._detect_hovered_driver(event.pos())
        
        if hovered_driver:
            menu = QMenu(self)
            hide_action = menu.addAction(f"隱藏 {hovered_driver}")
            hide_action.triggered.connect(lambda: self._hide_driver(hovered_driver))
            menu.exec_(self.mapToGlobal(event.pos()))
            event.accept()
            return
    
    super().mousePressEvent(event)
```

**特點**：
- ❌ 無調試輸出
- ✅ 使用 `_detect_hovered_driver` 實時檢測
- ✅ 邏輯與 Lap Time 完全一致

---

## 🔧 階段 6：Widget 初始化設置比較

### Lap Time Box Plot
```python
# lap_box_plot_chart_widget.py (__init__)
self.setFocusPolicy(Qt.StrongFocus)  # ← 有設置
self.setAttribute(Qt.WA_Hover, True)  # ← 有設置
self.setMouseTracking(True)
```

### Throttle Box Plot
```python
# throttle_box_plot_chart_widget.py (__init__)
# ❌ 沒有 setFocusPolicy
# ❌ 沒有 setAttribute(Qt.WA_Hover)
self.setMouseTracking(True)
```

**關鍵差異**：
- Lap Time 多了 `setFocusPolicy` 和 `setAttribute(Qt.WA_Hover)`
- 但 Throttle 沒有這些設置**卻仍然能正常工作**！

---

## 📊 階段 7：測試結果對比

### 獨立測試腳本 (test_laptime_mouse_events.py)
```
✅ Lap Time Widget 本身功能正常
✅ mousePressEvent 被觸發
✅ 右鍵選單成功彈出
✅ Filter 功能正常
```

**結論**：Widget 代碼本身沒有問題！

### GUI 中的實際測試
```
❌ Lap Time：右鍵選單無法彈出
❌ Log 完全沒有 mousePressEvent 的輸出
❌ 事件完全沒有到達 Widget

✅ Throttle：右鍵選單正常運作
✅ Filter 功能正常
✅ 事件成功傳遞到 Widget
```

---

## 🚨 關鍵問題總結

### 問題現象
1. **獨立運行正常，GUI 中失敗** → 問題在 MDI/佈局層
2. **Throttle 成功，Lap Time 失敗** → 架構差異導致
3. **無 log 輸出** → 事件完全沒有到達 Widget

### 懷疑的根本原因

#### ❌ 已排除的原因
- ~~Widget 代碼問題~~ → 獨立測試成功
- ~~mousePressEvent 實現問題~~ → 邏輯與 Throttle 一致
- ~~QFrame 攔截問題~~ → 剛修改了 `WA_TransparentForMouseEvents`

#### 🎯 可能的根本原因（按優先級）

**1. 包裝器架構差異（最可能）**
- Throttle 使用 3 層架構（GUI → 包裝器 → MDI → Widget）
- Lap Time 使用 2 層架構（GUI → MDI → Widget）
- **猜測**：包裝器層可能有額外的事件處理或 Widget 設置

**2. Widget 的父對象設置不同**
- Throttle: `self._main_widget = self._throttle_boxplot_core.get_widget()`
- Lap Time: 直接從 MDI 獲取
- **猜測**：Widget 的 parent 設置可能影響事件傳遞

**3. 檔案混淆問題**
- `lap_box_plot_analysis_module.py` 內容是 `RainAnalysisModule`
- 可能導致某些初始化流程異常

**4. MDI 子視窗的創建方式不同**
- Lap Time: `sub_window.setWidget(analysis_module.get_widget())`
- Throttle: 透過 `module.get_widget()` 獲取
- **猜測**：Widget 被設置到 SubWindow 的方式可能影響事件

---

## 🔬 下一步診斷計劃

### 方案 A：為 Lap Time 創建包裝器模組（推薦）
1. 修正 `lap_box_plot_analysis_module.py` 的內容
2. 創建正確的 `LapTimeBoxPlotAnalysisModule` 包裝器
3. 模仿 Throttle 的 3 層架構
4. 修改 GUI 主程式使用包裝器而非直接 MDI

**優點**：
- ✅ 與 Throttle 架構完全一致
- ✅ 可能解決根本問題
- ✅ 符合系統設計模式

**缺點**：
- ⏱️ 需要修改多個檔案
- ⏱️ 需要測試驗證

---

### 方案 B：深度調試事件傳遞鏈
1. 在 QFrame 添加 mousePressEvent 調試
2. 在 QSplitter 添加事件過濾器
3. 在 MDI 添加事件監控
4. 追蹤事件在哪一層被攔截

**優點**：
- ✅ 能找到確切的問題點
- ✅ 不需要大量修改代碼

**缺點**：
- ⏱️ 調試過程繁瑣
- ❓ 可能仍需要架構調整

---

### 方案 C：簡化測試（快速驗證）
1. 暫時移除 Lap Time 的 `setFocusPolicy` 和 `setAttribute`
2. 驗證是否是這些設置導致問題

**優點**：
- ⚡ 快速測試
- ⚡ 一行代碼

**缺點**：
- ❓ 機率較低（Throttle 沒有這些設置也能工作）

---

## 💡 推薦方案

**立即執行方案 A**：
1. 創建正確的 `LapTimeBoxPlotAnalysisModule` 包裝器
2. 修改 GUI 主程式使用包裝器
3. 測試驗證

**理由**：
- Throttle 的包裝器架構已驗證可行
- 統一架構模式符合系統設計
- 可能是根本問題所在

**預估時間**：15-20 分鐘

---

## 📋 總結：所有已知差異列表

| # | 差異項目 | Lap Time | Throttle | 影響等級 |
|---|---------|----------|----------|---------|
| 1 | **架構層數** | 2 層 | **3 層（多包裝器）** | 🔴 高 |
| 2 | **GUI 導入類別** | MDI 直接導入 | **包裝器導入** | 🔴 高 |
| 3 | **Widget 獲取方式** | MDI.get_widget() | **包裝器.get_widget()** | 🔴 高 |
| 4 | **module.py 檔案內容** | ❌ RainAnalysisModule | ✅ ThrottleBoxPlotAnalysisModule | 🔴 高 |
| 5 | **Widget 初始化設置** | 有 setFocusPolicy | 無 setFocusPolicy | 🟡 中 |
| 6 | **調試輸出** | 有詳細 log | 無 log | 🟢 低 |
| 7 | **mousePressEvent 邏輯** | 與 Throttle 一致 | 與 Lap Time 一致 | 🟢 無 |

---

**結論**：最可能的問題是**架構層數差異**導致的事件傳遞異常。建議立即實施方案 A。
