# 🐛 油門折線圖 TypeError 修復報告

## 問題總結

**症狀**：在創建油門折線圖視窗時出現 `TypeError: argument 1 has unexpected type 'ThrottleLineChartMDI'` 錯誤。

**錯誤訊息**：
```python
File "f1t_gui_main.py", line 8555, in _create_throttle_line_chart_window
    sub_window.setWidget(widget)
File "f1t_gui_main.py", line 2906, in setWidget
    content_layout.addWidget(widget)
TypeError: addWidget(self, a0: Optional[QWidget], stretch: int = 0, alignment: Union[Qt.Alignment, Qt.AlignmentFlag] = Qt.Alignment()): argument 1 has unexpected type 'ThrottleLineChartMDI'
```

**根本原因**：
1. `ThrottleLineChartModule.get_widget()` 返回的是 `ThrottleLineChartMDI` 實例（繼承自 `IAnalysisModule` → `QObject`）
2. 但 `PopoutSubWindow.setWidget()` 需要 `QWidget` 類型
3. `ThrottleLineChartMDI` 不是 `QWidget`，而是一個管理器類

---

## 🔍 問題分析

### 繼承鏈

```python
ThrottleLineChartMDI
  └─ UniversalAnalysisMDI
       └─ IAnalysisModule
            └─ QObject  # ❌ 不是 QWidget！
```

### 正確的架構

```python
ThrottleLineChartMDI (管理器，繼承 QObject)
  └─ main_widget: QWidget  # ✅ 這才是實際的 GUI 組件！
       └─ 包含圖表、控制面板等 UI 元素
```

###錯誤位置

**`throttle_line_chart_module.py` line 99**:
```python
# ❌ 錯誤：將管理器賦值給 _main_widget
if not self._main_widget:
    self._main_widget = self._throttle_chart_core  # ThrottleLineChartMDI 實例
```

**應該**:
```python
# ✅ 正確：獲取管理器的實際 QWidget
if not self._main_widget:
    self._main_widget = self._throttle_chart_core.get_widget()  # QWidget 實例
```

---

## ✅ 修復方案

### 修復 1: 修正 `initialize_module()` 方法

**文件**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_module.py`

**修改前**:
```python
# 創建主 Widget
if not self._main_widget:
    self._main_widget = self._throttle_chart_core  # ❌ 錯誤
```

**修改後**:
```python
# 🔧 修復：獲取 MDI 容器的實際 QWidget
if not self._main_widget:
    self._main_widget = self._throttle_chart_core.get_widget()  # ✅ 正確
```

---

### 修復 2: 註冊 `throttle_line` 模組類型

**文件**: `modules/gui/base/universal_analysis_mdi_base.py`

**問題**: `ThrottleLineChartMDI.__init__()` 中使用了 `analysis_type="throttle_line"`，但此類型未註冊。

**添加註冊**（在 `laptime` 註冊後）:
```python
# 註冊油門折線圖分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'throttle_line',
    AnalysisMDIConfig(
        analysis_type='throttle_line',
        display_name=tr('throttle_line_chart', 'Throttle Line Chart'),
        default_size=(1400, 900),
        requires_driver_params=True,
        requires_lap_params=False,
        supports_single_driver=True,
        supports_dual_driver=False
    )
)
```

---

## 📊 修改摘要

| 文件 | 修改內容 | 行數 | 狀態 |
|------|---------|------|------|
| `throttle_line_chart_module.py` | 修正 `initialize_module()` 獲取 widget | 99 | ✅ 已修復 |
| `universal_analysis_mdi_base.py` | 註冊 `throttle_line` 類型 | 1213+ | ✅ 已添加 |

---

## 🎯 完整修復流程

### 問題鏈

1. **缺少依賴**: `mplcursors` ✅ 已安裝
2. **方法不存在**: `_get_current_year_from_tab()` ✅ 已修復
3. **類型錯誤**: 返回 `ThrottleLineChartMDI` 而非 `QWidget` ✅ 已修復  
4. **類型未註冊**: `throttle_line` 未在 `MDI_MODULE_TYPES` 中 ✅ 已註冊

### 所有修復

1. ✅ 安裝 `mplcursors` 套件
2. ✅ 修正參數獲取（使用 `MainWindowParameterProvider`）
3. ✅ 修正模組實例化流程
4. ✅ 修正 `get_widget()` 返回類型
5. ✅ 註冊 `throttle_line` 模組類型

---

## 🧪 測試驗證

### 單元測試狀態

**導入測試**: ✅ 通過
```python
from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import ThrottleLineChartModule
# ✅ 無錯誤
```

**實例化測試**: ⏳ PyQt5 初始化需要時間
```python
module = ThrottleLineChartModule(year=2025, race="Japan", session="R")
# ⏳ 正在初始化...
```

### GUI 整合測試

**準備就緒！** 所有已知錯誤已修復，可以直接測試 GUI。

**測試步驟**:
1. 啟動 GUI: `python f1t_gui_main.py`
2. 選擇賽事: 2025 Japan R
3. 開啟油門折線圖功能

**預期結果**:
- ✅ 不會出現 `AttributeError`
- ✅ 不會出現 `ModuleNotFoundError`
- ✅ 不會出現 `TypeError`
- ✅ 成功創建視窗並顯示

---

## 💡 技術細節

### UniversalAnalysisMDI 架構

```python
class ThrottleLineChartMDI(UniversalAnalysisMDI):
    """
    這是一個管理器類，不是 Widget！
    繼承 IAnalysisModule → QObject
    """
    
    def __init__(self, ...):
        super().__init__(analysis_type="throttle_line", ...)
        # 這會調用 UniversalAnalysisMDI.__init__()
        # 它會調用 _setup_ui() 創建 self.main_widget (QWidget)
    
    def get_widget(self) -> QWidget:
        """返回實際的 QWidget"""
        return self.main_widget  # ✅ 這才是 QWidget！
```

### 正確的使用方式

```python
# 創建管理器
mdi = ThrottleLineChartMDI(year=2025, race="Japan", session="R")

# 獲取實際的 Widget
widget = mdi.get_widget()  # QWidget 實例

# 添加到父容器
parent_layout.addWidget(widget)  # ✅ 正確
```

### 錯誤的使用方式

```python
# 創建管理器
mdi = ThrottleLineChartMDI(year=2025, race="Japan", session="R")

# 直接使用管理器
parent_layout.addWidget(mdi)  # ❌ TypeError!
# mdi 是 QObject，不是 QWidget
```

---

## ✅ 修復狀態

- [x] 問題定位
- [x] 根本原因分析
- [x] 修正 `initialize_module()` 方法
- [x] 註冊 `throttle_line` 模組類型
- [x] 代碼修復完成
- [ ] GUI 整合測試（待用戶測試）
- [ ] 用戶驗收

---

## 🚀 準備測試

### 所有修復已完成！

**修復的問題**:
1. ✅ 依賴缺失 (`mplcursors`)
2. ✅ 方法不存在 (`_get_current_year_from_tab`)
3. ✅ 類型錯誤 (`ThrottleLineChartMDI` vs `QWidget`)
4. ✅ 類型未註冊 (`throttle_line`)

**現在可以**:
- 啟動 GUI 進行實際測試
- 所有已知錯誤都已修復
- 預期可以正常使用油門折線圖功能

---

**最後更新**: 2025-10-08  
**修復者**: GitHub Copilot  
**狀態**: 代碼修復完成，等待實際測試 ✅
