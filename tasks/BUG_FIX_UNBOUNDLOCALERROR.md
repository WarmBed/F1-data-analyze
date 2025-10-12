# 🔧 Bug 修復報告 - UnboundLocalError

**問題編號**：ISSUE-001  
**發生時間**：2025-10-11 16:05  
**修復時間**：2025-10-11 16:08  
**狀態**：✅ 已修復  

---

## 🐛 問題描述

### 錯誤訊息
```python
UnboundLocalError: cannot access local variable 'tr' where it is not associated with a value
```

### 錯誤位置
- **檔案**：`speed_analysis_chart_widget.py`
- **方法**：`_create_status_info_widget()`
- **行號**：1087

### 觸發條件
- 啟動 GUI
- 初始化 Speed Analysis 模組
- 創建狀態資訊 Widget

---

## 🔍 根本原因分析

### 問題代碼
```python
def _create_status_info_widget(self) -> QWidget:
    # ... 前面的代碼使用了 tr() 函數 ...
    self.lap_time_label = QLabel(f"⏱️ {tr('lap_time', '圈時間')}: ...")  # ✅ 這裡 tr 來自頂部 import
    
    # ... 中間代碼 ...
    
    # ❌ 錯誤：方法中間重複導入 tr
    from core.gui_i18n import tr
    self.time_axis_checkbox = QCheckBox(tr("use_time_axis", "使用時間軸"))
```

### 原因說明
1. **頂部導入**：`from core.gui_i18n import tr` 在檔案開頭已導入
2. **方法內重複導入**：在方法中間又執行 `from core.gui_i18n import tr`
3. **作用域問題**：Python 看到方法內有 `from ... import tr`，會認為 `tr` 是局部變數
4. **執行順序錯誤**：在導入語句之前就使用了 `tr()`，導致 UnboundLocalError

### 類比情況
```python
# 類似的錯誤範例
def bad_example():
    print(x)  # ❌ UnboundLocalError
    x = 10    # Python 看到這行，認為 x 是局部變數

# 正確做法
x = 5
def good_example():
    print(x)  # ✅ 使用全域變數
```

---

## ✅ 修復方案

### 修改內容

#### 1. 移除 `_create_status_info_widget()` 中的重複導入

**修改前**：
```python
# 時間軸切換 Checkbox
time_axis_container = QWidget()
time_axis_layout = QHBoxLayout(time_axis_container)
time_axis_layout.setContentsMargins(0, 0, 0, 0)
time_axis_layout.setSpacing(5)

from core.gui_i18n import tr  # ❌ 重複導入
self.time_axis_checkbox = QCheckBox(tr("use_time_axis", "使用時間軸"))
```

**修改後**：
```python
# 時間軸切換 Checkbox
time_axis_container = QWidget()
time_axis_layout = QHBoxLayout(time_axis_container)
time_axis_layout.setContentsMargins(0, 0, 0, 0)
time_axis_layout.setSpacing(5)

# tr 已在文件頂部導入，無需重複導入  # ✅ 添加註釋說明
self.time_axis_checkbox = QCheckBox(tr("use_time_axis", "使用時間軸"))
```

#### 2. 移除 `_on_time_axis_toggled()` 中的重複導入

**修改前**：
```python
if not success and enabled:
    self.time_axis_checkbox.setChecked(False)
    from core.gui_i18n import tr              # ❌ 重複導入
    from PyQt5.QtWidgets import QMessageBox   # ❌ 重複導入
    QMessageBox.warning(...)
```

**修改後**：
```python
if not success and enabled:
    self.time_axis_checkbox.setChecked(False)
    # tr 和 QMessageBox 已在文件頂部導入  # ✅ 添加註釋說明
    QMessageBox.warning(...)
```

---

## 🧪 驗證方法

### 1. 語法檢查
```powershell
python -m py_compile modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py
```
**預期結果**：無錯誤輸出

### 2. GUI 啟動測試
```powershell
python f1t_gui_main.py
```
**預期結果**：
- ✅ GUI 正常啟動
- ✅ Speed Analysis 模組可以初始化
- ✅ 狀態資訊 Widget 正常顯示
- ✅ Checkbox 正常顯示

### 3. 功能測試
1. 開啟 Speed Analysis 模組
2. 載入數據
3. 檢查 Checkbox 是否可見
4. 測試切換功能

---

## 📝 經驗教訓

### 1. **避免方法內導入**
❌ 不要在方法中間導入已在頂部導入的模組
✅ 統一在檔案頂部導入所有依賴

### 2. **檢查作用域**
- Python 的變數作用域規則：如果方法內有賦值語句（包括 import），該變數被視為局部變數
- 局部變數必須在使用前賦值

### 3. **程式碼審查**
- 添加新功能時，檢查是否有重複導入
- 使用 IDE 的 linting 工具自動檢測

### 4. **測試驅動**
- 先寫測試，再寫實現
- 及早發現問題

---

## 🔄 相關修改

### 修改檔案
- `modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py`

### 修改行數
- 移除 2 行重複導入
- 添加 2 行註釋

### 影響範圍
- 僅影響 Speed Analysis 模組
- 不影響其他模組

---

## ✅ 檢查清單

- [x] ✅ 移除 `_create_status_info_widget()` 中的重複導入
- [x] ✅ 移除 `_on_time_axis_toggled()` 中的重複導入
- [x] ✅ 添加說明註釋
- [ ] ⏳ 驗證 GUI 啟動
- [ ] ⏳ 驗證功能正常

---

## 📊 修復統計

| 項目 | 數量 |
|------|------|
| 修復檔案 | 1 |
| 移除行數 | 2 |
| 添加註釋 | 2 |
| 修復時間 | 3 分鐘 |

---

**修復人員**：GitHub Copilot AI Assistant  
**審核狀態**：待用戶驗證  
**優先級**：🔴 高（阻塞 GUI 啟動）
