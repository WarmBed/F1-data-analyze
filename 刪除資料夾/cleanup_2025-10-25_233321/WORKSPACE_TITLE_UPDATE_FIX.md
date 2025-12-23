# Workspace 標題更新修復報告

## 📋 問題描述

**現象**：從 Workspace 載入的 Rain Analysis 視窗，切換賽事後標題不更新

**用戶報告**：
- ✅ 手動開啟 Rain Analysis → 切換賽事 → 標題正常更新
- ❌ Workspace 載入 Rain Analysis → 切換賽事 → 標題不更新（停留在舊標題）
- ❌ 日誌顯示標題已更新，但 UI 上看不到變化

**具體案例**：
```
Workspace 載入：標題顯示 "Rain Analysis - 2025 United States R"
切換到 Australia：
  - 日誌：✅ 驗證當前標題: Rain Analysis - 2025 Australia R
  - UI：❌ 仍然顯示 "Rain Analysis - 2025 United States R"
```

---

## 🔍 問題調查過程

### 階段 1：初步診斷（假設是基礎架構問題）

**假設**：`parent_window` 未正確設置

**測試**：
```python
# 在 RainAnalysisModuleAdapter 中添加調試
if hasattr(self._rain_analysis_core, 'set_parent_window'):
    self._rain_analysis_core.set_parent_window(parent)
```

**結果**：❌ 問題依舊，`parent_window` 設置正確

---

### 階段 2：深度調試（添加詳細日誌）

**測試代碼**：
```python
# universal_analysis_mdi_base.py:886-946
def update_window_title(self):
    print(f"[UPDATE_TITLE_DEBUG] === 開始更新標題 ===")
    print(f"[UPDATE_TITLE_DEBUG] parent 類型: {type(parent)}")
    print(f"[UPDATE_TITLE_DEBUG] 設置新標題: {new_title}")
    parent.setWindowTitle(new_title)
    print(f"[UPDATE_TITLE_DEBUG] 驗證當前標題: {parent.windowTitle()}")
```

**日誌輸出**：
```
[UPDATE_TITLE_DEBUG] 設置新標題: Rain Analysis - 2025 Australia R
[UPDATE_TITLE_DEBUG] 驗證當前標題: Rain Analysis - 2025 Australia R
[UPDATE_TITLE_DEBUG] 標題是否正確: True ✅
```

**發現**：`parent.windowTitle()` 確實更新了！但 UI 沒變化 🤔

---

### 階段 3：架構分析（找到雙層標題系統）

**關鍵發現**：搜索 `f1t_gui_main.py` 找到 `DraggableTitleBar`

```python
# f1t_gui_main.py:3135 - PopoutSubWindow 初始化
self.title_bar = DraggableTitleBar(self, self.windowTitle())
```

**架構圖**：
```
PopoutSubWindow (QMdiSubWindow 子類)
├── windowTitle()           ← Qt 原生標題（內部儲存）
└── title_bar               ← DraggableTitleBar（視覺顯示）
    └── update_title()      ← 更新視覺標題的方法
```

**核心問題**：
- `setWindowTitle()` 只更新 **Qt 內部標題**
- **視覺標題** (`title_bar`) 需要手動調用 `update_title()`

---

### 階段 4：尋找正確實現（PopoutSubWindow 有完整邏輯）

**發現 `PopoutSubWindow.update_window_title()` 方法**：

```python
# f1t_gui_main.py:2508-2546
def update_window_title(self):
    """更新視窗標題（同時更新內部和視覺）"""
    # ... 生成 new_title ...
    
    # ✅ 更新 Qt 內部標題
    self.setWindowTitle(new_title)
    
    # ✅ 更新視覺標題列
    if hasattr(self, 'title_bar') and self.title_bar:
        self.title_bar.update_title(new_title)  # ← 關鍵！
```

**問題根源**：
- `UniversalAnalysisMDI.update_window_title()` 直接調用 `parent.setWindowTitle()`
- **沒有**調用 `parent.title_bar.update_title()`
- 結果：內部標題更新了，視覺標題沒更新

---

## ✅ 解決方案

### 修改文件：`modules/gui/base/universal_analysis_mdi_base.py`

**修改位置**：Line 910-920

**原始代碼**（❌ 錯誤）：
```python
# ✅ [FIX] 直接設置新標題（完全替換，不追加）
parent.setWindowTitle(new_title)

# 🔥 強制刷新視窗標題顯示
print(f"[UPDATE_TITLE_DEBUG] 強制刷新視窗標題...")
parent.update()
parent.repaint()
```

**修正代碼**（✅ 正確）：
```python
# ✅ [FIX] 直接設置新標題（完全替換，不追加）
parent.setWindowTitle(new_title)

# 🔥 **關鍵修正**: 同時更新自訂標題列（PopoutSubWindow 的 title_bar）
if hasattr(parent, 'title_bar') and parent.title_bar:
    print(f"[UPDATE_TITLE_DEBUG] 發現自訂標題列，更新標題...")
    if hasattr(parent.title_bar, 'update_title'):
        parent.title_bar.update_title(new_title)
        print(f"[UPDATE_TITLE_DEBUG] ✅ 自訂標題列已更新")
    else:
        print(f"[UPDATE_TITLE_DEBUG] ⚠️  title_bar 沒有 update_title 方法")
else:
    print(f"[UPDATE_TITLE_DEBUG] 沒有自訂標題列，跳過")

# 🔥 強制刷新視窗標題顯示
print(f"[UPDATE_TITLE_DEBUG] 強制刷新視窗標題...")
parent.update()
parent.repaint()
```

---

## 🎯 修復關鍵點

### 關鍵 1：理解雙層標題架構

```
用戶看到的標題 = DraggableTitleBar.update_title()
內部儲存的標題 = QMdiSubWindow.setWindowTitle()
```

兩者**必須同時更新**才能正常顯示！

### 關鍵 2：調用正確的更新方法

```python
# ❌ 錯誤：只更新內部標題
parent.setWindowTitle(new_title)

# ✅ 正確：同時更新內部和視覺標題
parent.setWindowTitle(new_title)              # 內部標題
parent.title_bar.update_title(new_title)      # 視覺標題
```

### 關鍵 3：安全檢查（兼容性）

```python
# ✅ 添加 hasattr 檢查，確保兼容非 PopoutSubWindow 的父視窗
if hasattr(parent, 'title_bar') and parent.title_bar:
    if hasattr(parent.title_bar, 'update_title'):
        parent.title_bar.update_title(new_title)
```

---

## 📊 修復前後對比

### 修復前（❌ 錯誤流程）

```
用戶切換賽事 → update_parameters()
              ↓
         update_window_title()
              ↓
         parent.setWindowTitle("Australia R")  ← 只更新內部標題
              ↓
         日誌顯示：✅ windowTitle() = "Australia R"
         UI 顯示： ❌ title_bar 仍顯示 "United States R"
```

### 修復後（✅ 正確流程）

```
用戶切換賽事 → update_parameters()
              ↓
         update_window_title()
              ↓
         parent.setWindowTitle("Australia R")           ← 更新內部標題
              ↓
         parent.title_bar.update_title("Australia R")   ← 更新視覺標題
              ↓
         日誌顯示：✅ windowTitle() = "Australia R"
         UI 顯示： ✅ title_bar 顯示 "Australia R"
```

---

## 🧪 測試驗證

### 測試場景 1：Workspace 載入
```
1. 開啟 Workspace ID=32（包含 Rain Analysis 視窗）
2. 初始標題：Rain Analysis - 2025 United States R
3. 切換到 Australia
4. ✅ 標題更新為：Rain Analysis - 2025 Australia R
```

### 測試場景 2：手動開啟
```
1. 左側選單 → Rain Analysis
2. 手動開啟視窗
3. 切換賽事
4. ✅ 標題正常更新
```

### 測試場景 3：其他分析模組
```
所有繼承 UniversalAnalysisMDI 的模組：
- Track Analysis ✅
- Pitstop Analysis ✅
- Tire Strategy Analysis ✅
```

---

## 📝 經驗總結

### 1. 調試技巧

**關鍵發現方法**：
```python
# ✅ 添加詳細日誌對比內部狀態 vs UI 顯示
print(f"內部標題: {parent.windowTitle()}")        # Qt 內部
print(f"視覺標題: {parent.title_bar.get_title()}") # UI 顯示
```

當日誌顯示「已更新」但 UI 沒變化時，說明有**雙重狀態儲存**！

### 2. 架構理解

**自訂 UI 組件的陷阱**：
- Qt 原生方法（`setWindowTitle()`）只更新內部狀態
- 自訂 UI 組件（`DraggableTitleBar`）需要手動同步
- **必須同時更新兩者**

### 3. 代碼搜索策略

**發現自訂組件的方法**：
```bash
# 搜索關鍵字
grep_search("TitleBar|title_bar|CustomTitle")

# 發現 DraggableTitleBar 後，搜索其初始化位置
grep_search("title_bar.*=.*DraggableTitleBar")

# 找到正確的更新方法
grep_search("def update_window_title")
```

### 4. 修復原則

**安全修復三原則**：
1. **保留原有邏輯**：`parent.setWindowTitle()` 仍需調用
2. **添加新邏輯**：`parent.title_bar.update_title()` 額外調用
3. **向下兼容**：使用 `hasattr()` 檢查，確保不影響其他父視窗

---

## 🔧 後續建議

### 建議 1：統一標題更新接口

**問題**：目前有兩個更新標題的地方
- `UniversalAnalysisMDI.update_window_title()`
- `PopoutSubWindow.update_window_title()`

**改進方案**：
```python
# 選項 A：讓 UniversalAnalysisMDI 調用 parent 的方法
if hasattr(parent, 'update_window_title') and callable(parent.update_window_title):
    parent.update_window_title()  # 由 parent 處理所有邏輯
else:
    parent.setWindowTitle(new_title)  # 向下兼容
```

### 建議 2：添加文檔注釋

```python
# modules/gui/base/universal_analysis_mdi_base.py
def update_window_title(self):
    """
    更新視窗標題
    
    ⚠️ 重要：PopoutSubWindow 使用雙層標題系統
    1. QMdiSubWindow.windowTitle() - Qt 內部標題
    2. DraggableTitleBar - 用戶可見的視覺標題
    
    必須同時更新兩者才能在 UI 上顯示正確！
    """
```

### 建議 3：單元測試

```python
def test_workspace_title_update():
    """測試 Workspace 載入後標題能正常更新"""
    # 1. 載入 Workspace
    # 2. 切換賽事
    # 3. 驗證內部標題
    # 4. 驗證視覺標題
    assert window.windowTitle() == "Australia R"
    assert window.title_bar.get_title() == "Australia R"
```

---

## 🎓 技術要點

### Qt 視窗標題更新機制

```python
# Qt 標準流程
window.setWindowTitle("New Title")  # 設置標題
window.windowTitle()                # 讀取標題
window.update()                     # 刷新視窗
```

### 自訂標題列更新機制

```python
# F1T 自訂流程
class PopoutSubWindow(QMdiSubWindow):
    def __init__(self):
        self.title_bar = DraggableTitleBar(self, title)
        
    def update_window_title(self):
        self.setWindowTitle(new_title)           # ← Qt 內部
        self.title_bar.update_title(new_title)   # ← 自訂 UI
```

### 雙重狀態同步模式

```python
# 通用模式：自訂 UI 組件時的狀態同步
class CustomWidget(BaseWidget):
    def set_value(self, value):
        # 1. 更新內部狀態
        super().set_value(value)
        
        # 2. 更新自訂 UI 組件
        if hasattr(self, 'custom_ui'):
            self.custom_ui.update_display(value)
```

---

## 📎 相關文件

- **修改文件**：`modules/gui/base/universal_analysis_mdi_base.py` (Line 910-920)
- **參考實現**：`f1t_gui_main.py` (Line 2508-2546)
- **自訂組件**：`f1t_gui_main.py` (Line 1985-2308) - DraggableTitleBar
- **初始化位置**：`f1t_gui_main.py` (Line 3135) - title_bar 創建

---

## ✅ 修復狀態

- **狀態**：✅ 已修復
- **測試**：✅ 通過
- **影響範圍**：所有繼承 `UniversalAnalysisMDI` 的分析模組
- **向下兼容**：✅ 完全兼容（使用 hasattr 檢查）
- **日期**：2025-10-23

---

## 🙏 致謝

感謝用戶提供詳細的調試日誌，特別是：
```
驗證當前標題: Rain Analysis - 2025 Australia R ✅
最終檢查標題: Rain Analysis - 2025 Australia R ✅
標題是否正確: True ✅
```

這些日誌明確指出「內部狀態正確，但 UI 顯示錯誤」，是找到雙層標題系統的關鍵線索！

---

**文件版本**：1.0  
**最後更新**：2025-10-23  
**作者**：GitHub Copilot  
**審核**：F1T 開發團隊
