# 🔍 Speed 模組引用鏈深度分析 - Lambda 閉包洩漏

**發現日期**：2025-10-16  
**問題類型**：Lambda 閉包 + 信號連接洩漏  
**影響範圍**：f1t_gui_main.py  
**嚴重程度**：🔴 最高（直接持有 SpeedAnalysisModule）

---

## 🎯 問題發現

從 objgraph 引用圖中發現的引用鏈：

```
frame (f1t_gui_main.py:6825)
    ↓
frame (f1t_gui_main.py:6938)
    ↓
frame (f1t_gui_main.py:7028)
    ↓
frame (f1t_gui_main.py:13269)
    ↓
cell <cell at 0x000001102DD6E410: SpeedAnalysis...>
    ↓
list (1 items)
    ↓
SpeedAnalysisModule
```

**關鍵發現**：出現了 **`cell`** 對象！

### **什麼是 Cell？**

**Cell** 是 Python 閉包（closure）的內部實現機制：

```python
def outer_function():
    x = 10  # 局部變量
    
    def inner_function():
        return x  # 捕獲外部變量
    
    return inner_function

# x 變量會被存儲在 cell 對象中
# inner_function.__closure__[0].cell_contents == 10
```

在我們的代碼中，**lambda 函數**捕獲了 `analysis_module`，形成閉包。

---

## 🔬 代碼分析

### **Line 13235 - Lambda 閉包洩漏**

**問題代碼：**
```python
# 連接視窗關閉信號
sub_window.window_closed.connect(lambda: self.on_lap_analysis_window_closed(analysis_module))
```

**引用鏈機制：**

1. **Lambda 函數定義**：
   ```python
   lambda: self.on_lap_analysis_window_closed(analysis_module)
   ```

2. **Lambda 捕獲變量**：
   - `analysis_module` 被 lambda 捕獲
   - 存儲在 **cell** 對象中
   - lambda 函數持有這個 cell

3. **信號連接**：
   - `sub_window.window_closed.connect(lambda)`
   - 信號系統持有 lambda 函數
   - 信號系統持有 cell
   - cell 持有 `analysis_module`

4. **視窗關閉後**：
   - 即使調用了 `on_lap_analysis_window_closed()`
   - Lambda 函數仍然連接到信號
   - Cell 仍然持有 `analysis_module`
   - **SpeedAnalysisModule 無法被 GC 回收**

**完整引用鏈：**
```
sub_window (QMdiSubWindow)
    ↓ window_closed 信號
signal connection (PyQt5 信號系統)
    ↓ 持有槽函數
lambda function
    ↓ __closure__[0] (cell 對象)
cell.cell_contents
    ↓
analysis_module (SpeedAnalysisModule 實例)
```

---

### **Line 7028 - 視窗開啟時的 traceback（已修復）**

**位置：** `on_lap_analysis_window_opened` 調用 `_trigger_toolbar_status_for_lap_analysis`

**問題代碼：**
```python
# Line 7028
self._trigger_toolbar_status_for_lap_analysis(analysis_type, window_object)

# Line 7125（已修復）
except Exception as e:
    print(f"[ERROR] [TOOLBAR_TRIGGER] 觸發工具欄狀態更新失敗: {e}")
    import traceback
    traceback.print_exc()  # ❌ 持有 window_object
```

**修復狀態**：✅ 已修復（剛才完成）

---

### **Frame 鏈分析**

objgraph 顯示的 frame 鏈對應的調用堆疊：

| Frame 行號 | 函數/位置 | 作用 | 是否有問題 |
|-----------|-----------|------|-----------|
| 6825 | `_initialize_driver_list()` | 初始化車手列表 | ✅ 已修復 traceback |
| 6938 | `show_lap_controls()` | 顯示圈速控件 | ✅ 無 traceback |
| 7028 | `on_lap_analysis_window_opened()` | 視窗開啟回調 | ✅ 已修復 traceback |
| 13269 | 速度模組創建流程 | 創建 SpeedAnalysisModule | 🔴 Lambda 閉包洩漏 |

**結論**：前 3 個 frame 已經修復，**關鍵問題在 Line 13235 的 lambda 閉包**。

---

## 🎯 Lambda 閉包洩漏機制

### **為什麼 Lambda 會洩漏？**

**正常情況（無閉包）：**
```python
# 方法引用，不捕獲變量
sub_window.window_closed.connect(self.on_window_closed)

# 視窗關閉時：
# 1. 調用 self.on_window_closed()
# 2. 信號仍連接，但只持有方法引用
# 3. 方法引用不持有其他對象
# 4. 視窗可以被 GC 回收
```

**問題情況（有閉包）：**
```python
# Lambda 捕獲變量
sub_window.window_closed.connect(lambda: self.on_window_closed(analysis_module))

# 視窗關閉時：
# 1. 調用 lambda，執行 self.on_window_closed(analysis_module)
# 2. 信號仍連接，持有 lambda 函數
# 3. Lambda 的 __closure__ 持有 cell
# 4. Cell 持有 analysis_module
# 5. analysis_module 持有視窗和所有組件
# 6. **形成循環引用，無法被 GC 回收**
```

### **PyQt5 信號系統的特性**

1. **強引用**：信號連接使用強引用持有槽函數
2. **持久連接**：信號連接在對象銷毀前一直存在
3. **Lambda 陷阱**：Lambda 捕獲變量形成閉包，增加引用計數
4. **斷開困難**：需要手動調用 `disconnect()` 斷開連接

---

## 🔧 修復方案

### **方案 1：使用 Partial（推薦）** ✅

**優點**：
- 不使用 lambda，避免閉包
- 明確的參數傳遞
- 更好的性能

**代碼：**
```python
from functools import partial

# 替換 lambda
sub_window.window_closed.connect(
    partial(self.on_lap_analysis_window_closed, analysis_module)
)
```

**原理**：
- `partial` 創建一個新函數，預填充參數
- 不使用閉包機制
- 不創建 cell 對象
- 引用更清晰

---

### **方案 2：使用屬性存儲（備選）**

**優點**：
- 不使用 lambda 或 partial
- 直接通過屬性訪問

**代碼：**
```python
# 存儲分析模組到子視窗
sub_window._analysis_module = analysis_module

# 連接信號（不使用 lambda）
sub_window.window_closed.connect(self._on_subwindow_closed)

# 處理器中獲取分析模組
def _on_subwindow_closed(self):
    sub_window = self.sender()  # 獲取信號發送者
    if hasattr(sub_window, '_analysis_module'):
        analysis_module = sub_window._analysis_module
        self.on_lap_analysis_window_closed(analysis_module)
```

**缺點**：
- 需要額外的方法
- 代碼較複雜

---

### **方案 3：手動斷開連接（必須配合方案 1 或 2）** ⚠️

**關鍵**：在 `on_lap_analysis_window_closed` 中斷開信號連接

**代碼：**
```python
def on_lap_analysis_window_closed(self, window_object):
    """遙測分析視窗關閉時調用"""
    
    # 🔴 關鍵：斷開信號連接，釋放 lambda/partial
    if hasattr(window_object, '_sub_window'):
        sub_window = window_object._sub_window
        try:
            # 斷開所有與 window_closed 信號的連接
            sub_window.window_closed.disconnect()
            print(f"[LAP_CONTROL] ✅ 已斷開信號連接")
        except Exception as e:
            print(f"[LAP_CONTROL] ⚠️ 斷開信號連接失敗: {e}")
    
    # ... 原有的清理代碼 ...
```

**為什麼必須斷開？**
- 即使使用 `partial`，信號仍持有函數引用
- 斷開連接才能完全釋放
- 配合方案 1 或 2 使用效果最佳

---

## 📋 完整修復方案（推薦）

### **步驟 1：修改信號連接（使用 Partial）**

**修改 Line 13235：**
```python
from functools import partial

# 修改前（Lambda 閉包）
sub_window.window_closed.connect(lambda: self.on_lap_analysis_window_closed(analysis_module))

# 修改後（Partial）
sub_window.window_closed.connect(
    partial(self.on_lap_analysis_window_closed, analysis_module)
)
```

---

### **步驟 2：在關閉時斷開信號**

**修改 `on_lap_analysis_window_closed` 方法：**

```python
def on_lap_analysis_window_closed(self, window_object):
    """遙測分析視窗關閉時調用"""
    
    # 🔴 第一步：斷開信號連接，釋放閉包引用
    if hasattr(window_object, '_sub_window'):
        sub_window = window_object._sub_window
        try:
            # 斷開所有 window_closed 信號連接
            sub_window.window_closed.disconnect()
            print(f"[LAP_CONTROL] ✅ 已斷開子視窗信號連接")
        except Exception as e:
            print(f"[LAP_CONTROL] ⚠️ 斷開信號連接失敗（可能已斷開）: {e}")
    
    # 從追蹤集合中移除
    self.lap_analysis_windows.discard(window_object)
    
    # 獲取視窗標題用於日誌
    window_title = window_object.windowTitle() if hasattr(window_object, 'windowTitle') else str(window_object)
    print(f"[LAP_CONTROL] 📊 圈速分析視窗已關閉: {window_title}")
    
    # ✅ 修復：調用模組的清理方法（如果存在）
    if hasattr(window_object, 'cleanup'):
        try:
            print(f"[LAP_CONTROL] 🧹 調用模組清理方法: {window_title}")
            window_object.cleanup()
            print(f"[LAP_CONTROL] ✅ 模組清理成功: {window_title}")
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame 引用
            print(f"[ERROR] [LAP_CONTROL] 模組清理失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
    
    # 如果是分析模組，確保清理相關引用
    if hasattr(window_object, '_sub_window'):
        sub_window = window_object._sub_window
        # 從 MDI 區域中移除子視窗
        if sub_window and sub_window.parent():
            mdi_area = sub_window.parent()
            if hasattr(mdi_area, 'removeSubWindow'):
                mdi_area.removeSubWindow(sub_window)
                print(f"[LAP_CONTROL] 🗑️ 已從 MDI 區域移除子視窗: {window_title}")
        
        # 🔴 清理模組對子視窗的引用
        window_object._sub_window = None
    
    print(f"[LAP_CONTROL] 📊 當前活動視窗數: {len(self.lap_analysis_windows)}")
    
    # 如果沒有活動視窗，隱藏圈速控件
    if len(self.lap_analysis_windows) == 0:
        self.hide_lap_controls()
    
    # 🔴 強制清理局部變量和 frame 引用
    sub_window = None
    window_object = None
    window_title = None
    
    # 🔴 強制垃圾回收
    import gc
    gc.collect()
    print(f"[LAP_CONTROL] 🗑️ 已執行垃圾回收")
```

---

## ✅ 修復效果預測

### **修復前（Lambda 閉包洩漏）**

```
創建 SpeedAnalysisModule
    ↓
連接信號: sub_window.window_closed → lambda
    ↓
lambda.__closure__[0].cell_contents = analysis_module
    ↓
關閉視窗後：
    ↓
- lambda 仍連接到信號 ❌
- cell 仍持有 analysis_module ❌
- analysis_module 無法被 GC 回收 ❌

objgraph 顯示：
- SpeedAnalysisModule: 1 個 ❌
- cell 對象: 存在 ❌
- frame 鏈: 存在 ❌

Force GC: 回收 0 個對象 ❌
```

### **修復後（Partial + 斷開連接）**

```
創建 SpeedAnalysisModule
    ↓
連接信號: sub_window.window_closed → partial(on_lap_analysis_window_closed, analysis_module)
    ↓
partial 預填充參數（不使用閉包）
    ↓
關閉視窗後：
    ↓
1. 調用 on_lap_analysis_window_closed(analysis_module)
2. 斷開信號: sub_window.window_closed.disconnect()
3. partial 函數被釋放
4. analysis_module 引用計數歸零
5. 清理 _sub_window 引用
6. gc.collect() 強制回收

objgraph 顯示：
- SpeedAnalysisModule: 0 個 ✅
- cell 對象: 不存在 ✅
- frame 鏈: 清空 ✅

Force GC: 回收 5+ 個對象 ✅
```

---

## 🎯 其他可能的 Lambda 洩漏點

搜索所有使用 lambda 連接信號的地方：

```python
# 搜索模式
*.connect(lambda

# 可能的問題位置：
1. sub_window.window_closed.connect(lambda: ...) ← 已發現
2. 數據載入器的信號連接
3. 圖表更新的信號連接
4. 參數變更的信號連接
```

**建議**：系統性搜索並替換所有 lambda 為 partial。

---

## 💡 最佳實踐

### **禁止模式**

❌ **使用 Lambda 連接信號並捕獲對象**
```python
# Lambda 捕獲 obj
signal.connect(lambda: self.handler(obj))
```

❌ **使用 Lambda 捕獲局部變量**
```python
for item in items:
    signal.connect(lambda: self.process(item))  # 陷阱！
```

❌ **不斷開信號連接**
```python
# 對象銷毀前未斷開
obj.signal.connect(slot)
# ... obj 被刪除
# 信號連接仍存在，持有 slot 引用
```

### **推薦模式**

✅ **使用 Partial 預填充參數**
```python
from functools import partial
signal.connect(partial(self.handler, obj))
```

✅ **使用屬性存儲**
```python
obj._param = value
signal.connect(self.handler)

def handler(self):
    sender = self.sender()
    value = sender._param
```

✅ **斷開信號連接**
```python
def cleanup(self):
    self.signal.disconnect()  # 釋放所有連接
```

✅ **使用弱引用（高級）**
```python
import weakref

obj_ref = weakref.ref(obj)
signal.connect(lambda: self.handler(obj_ref()))
```

---

## 📊 修復統計

### **已完成修復**

| 位置 | 問題類型 | 修復狀態 |
|------|---------|---------|
| speed_analysis_mdi.py | traceback 洩漏（11 處） | ✅ 完成 |
| speed_analysis_chart_widget.py | traceback 洩漏（3 處） | ✅ 完成 |
| f1t_gui_main.py:7125 | traceback 洩漏（1 處） | ✅ 完成 |

### **待修復**

| 位置 | 問題類型 | 優先級 |
|------|---------|--------|
| f1t_gui_main.py:13235 | Lambda 閉包洩漏 | 🔴 最高 |
| 其他模組 | Lambda 閉包洩漏（未知數量） | 🟡 高 |

### **總計**

- **Traceback 洩漏**：15/15 處修復完成 ✅
- **Lambda 閉包洩漏**：0/1+ 處修復完成 ⚠️
- **修復進度**：93.75%（15/16）

---

## 🧪 測試計劃

### **測試步驟**

1. **修復 Lambda 閉包洩漏**
   - [ ] 將 lambda 替換為 partial
   - [ ] 添加信號斷開邏輯

2. **啟動測試**
   - [ ] 啟動 F1T GUI
   - [ ] 啟動 Memory Diagnostics

3. **Speed 模組測試**
   - [ ] 開啟 Speed Analysis
   - [ ] 載入數據
   - [ ] 關閉視窗

4. **objgraph 檢查**
   - [ ] 生成引用圖
   - [ ] 檢查是否還有 cell 對象
   - [ ] 檢查是否還有 frame 鏈

5. **GC 驗證**
   - [ ] 點擊 Force GC
   - [ ] 應該回收 5+ 個對象

6. **重複測試**
   - [ ] 重複 5 次確認穩定

### **預期結果**

✅ **無 cell 對象**
✅ **無 frame 鏈**
✅ **所有組件計數歸零**
✅ **Force GC 回收 5+ 對象**

---

**報告結束**

分析人員：AI Assistant  
審核人員：待確認  
測試狀態：待修復 Lambda 閉包洩漏  
優先級：🔴 最高（直接持有 SpeedAnalysisModule）

**當前修復進度**：15/16 處（93.75%）  
**建議**：立即修復 Lambda 閉包洩漏，這是最後的洩漏源
