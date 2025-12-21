# Speed 模組記憶體洩漏診斷 v3.1 - 修復引用追蹤邏輯

## 📋 v3 測試結果分析

### 發現的問題

v3 測試雖然成功執行，但有一個**關鍵邏輯錯誤**：

#### 問題：清理後無法追蹤引用
```python
# 清理過程
self.speed_chart_widget.deleteLater()
self.speed_chart_widget = None  # ← 設為 None

# 清理後追蹤
if hasattr(self, 'speed_chart_widget'):
    widget_after = self.speed_chart_widget  # ← 已經是 None！
    if widget_after is not None:  # ← 條件失敗
        # 追蹤代碼永遠不會執行
```

**結果**：日誌顯示 "speed_chart_widget 已設為 None"，但我們無法知道物件是否真的被清理！

---

## 🔧 v3.1 修復方案

### 核心改進：保存引用用於最終檢查

**修復前**：
```python
# 清理
self.speed_chart_widget.deleteLater()
self.speed_chart_widget = None

# 無法追蹤（已經是 None）
widget_after = self.speed_chart_widget  # None!
```

**修復後**：
```python
# 🔍 保存引用（在設為 None 之前）
widget_for_final_check = self.speed_chart_widget

# 清理
self.speed_chart_widget.deleteLater()
self.speed_chart_widget = None

# ✅ 可以追蹤（使用保存的引用）
refcount = sys.getrefcount(widget_for_final_check)
referrers = gc.get_referrers(widget_for_final_check)
```

---

## 🎯 v3 測試結果回顧

### 清理前發現的引用持有者

從日誌 `logs/f1_gui_2025-10-15.log:108827-108835`：

```
[CRITICAL] speed_chart_widget 引用來源分類:
[CRITICAL]     - list: 2 個          ← 🎯 關鍵！
[CRITICAL]     - dict: 1 個
[CRITICAL]     - QWidget: 1 個
[CRITICAL]     - builtin_function_or_method: 1 個

[CRITICAL] 前 5 個引用來源詳情:
[CRITICAL]     [1] list: [<SpeedChartWidget object>]
[CRITICAL]     [2] list: [<SpeedAnalysisChartWidget object>]
[CRITICAL]     [3] dict: {'_module_name': 'SpeedAnalysisModule', ...}
[CRITICAL]     [4] QWidget: <PyQt5.QtWidgets.QWidget>
[CRITICAL]     [5] builtin_function_or_method: <built-in method update>
```

### 兩個 list 引用的來源

經過代碼分析，確認是：

1. **`analysis_manager._registered_chart_widgets`** - List[object]
   - 檔案：`modules/gui/lap_analysis/analysis_module_manager.py:41`
   - 用途：管理所有圖表組件的統計面板顯示

2. **`linkage_manager.registered_modules`** - List[Any]
   - 檔案：`modules/gui/lap_analysis/linkage/linkage_manager.py:36`
   - 用途：管理所有連動模組的信號分發

### 解除註冊確認

從日誌 `logs/f1_gui_2025-10-15.log:108837-108843`：

```
[ANALYSIS_MANAGER] Unregistered chart widget: SpeedAnalysisChartWidget  ← ✅
[ANALYSIS_MANAGER] ✅ Module unregistered successfully                  ← ✅
[LINKAGE_MANAGER] 已取消註冊連動模組，目前共 1 個模組                    ← ✅
```

**✅ 解除註冊執行成功！**

### GC 回收結果

從日誌 `logs/f1_gui_2025-10-15.log:108865`：

```
[CRITICAL] ⚠️⚠️⚠️ GC 回收了 0 個物件！物件仍被強引用！
```

**❌ 但 GC 仍然無法回收！**

---

## 🔍 v3.1 新增診斷能力

### 1. 保存引用用於最終檢查
```python
# 在清理前保存
widget_for_final_check = self.speed_chart_widget
manager_for_final_check = self.data_manager

# 清理後使用保存的引用追蹤
if widget_for_final_check is not None:
    refcount = sys.getrefcount(widget_for_final_check)
    referrers = gc.get_referrers(widget_for_final_check)
    # ... 分類和分析
```

### 2. 清理後引用來源分類
```python
# 分類清理後的引用
widget_ref_types_after = {}
for ref in referrers_widget_after:
    ref_type = type(ref).__name__
    widget_ref_types_after[ref_type] = widget_ref_types_after.get(ref_type, 0) + 1

# 顯示分類結果
print(f"[CRITICAL] 🔍 widget 清理後引用來源分類:")
for ref_type, count in sorted(...):
    print(f"[CRITICAL]     - {ref_type}: {count} 個")
```

### 3. List 引用特殊檢查
```python
# 🎯 關鍵檢查：list 引用是否還在？
if 'list' in widget_ref_types_after:
    print(f"[CRITICAL] ⚠️⚠️⚠️ widget 仍被 {count} 個 list 持有！")
```

---

## 🧪 測試預期

### 情況 A：清理成功（理想）
```
【清理前】
[CRITICAL] 🔍 widget 引用來源分類:
[CRITICAL]     - list: 2 個       ← analysis_manager + linkage_manager
[CRITICAL]     - dict: 1 個
[CRITICAL]     - QWidget: 1 個

【清理後】
[CRITICAL] 🔍 widget 清理後引用來源分類:
[CRITICAL]     - frame: 2 個       ← Python 堆疊（正常）
[CRITICAL]     - cell: 1 個        ← REPL（正常）
[SPEED_MDI] ✅ 已執行垃圾回收（回收 5 個物件）  ← 成功！
```

### 情況 B：清理失敗（問題）
```
【清理前】
[CRITICAL] 🔍 widget 引用來源分類:
[CRITICAL]     - list: 2 個

【清理後】
[CRITICAL] 🔍 widget 清理後引用來源分類:
[CRITICAL]     - list: 2 個       ← ⚠️ 仍然存在！
[CRITICAL] ⚠️⚠️⚠️ widget 仍被 2 個 list 持有！
[SPEED_MDI] ✅ 已執行垃圾回收（回收 0 個物件）  ← 失敗！
```

**如果是情況 B**，說明 `unregister_chart_widget()` 和 `unregister_module()` 雖然被調用，但**沒有真正從 list 中移除**！

---

## 🎯 診斷目標

v3.1 測試後，我們將能回答：

1. **清理後 list 引用還在嗎？**
   - 是 → unregister 方法有 bug
   - 否 → 問題在其他地方

2. **清理後引用數減少了嗎？**
   - 是 → 有進步，但還不夠
   - 否 → 完全沒效果

3. **哪些類型的引用沒有被清理？**
   - list → 全域管理器問題
   - dict → __dict__ 或其他字典問題
   - QWidget → Qt parent-child 問題

---

## 📝 測試步驟

### 執行測試
```powershell
# 1. 啟動 GUI
python f1t_gui_main.py

# 2. 打開速度模組 → 關閉

# 3. 查看詳細引用追蹤
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "🔍|⚠️⚠️⚠️" | Select-Object -Last 50
```

### 關鍵信息
請回報以下內容：

1. **清理前**：
   - `widget 引用來源分類` 有哪些類型？
   - list 有幾個？

2. **清理後**：
   - `widget 清理後引用來源分類` 有哪些類型？
   - list 還存在嗎？數量是多少？
   - 有沒有 `widget 仍被 X 個 list 持有` 的警告？

3. **GC 結果**：
   - `已執行垃圾回收（回收 X 個物件）`
   - X 是 0 還是 > 0？

---

## 🔧 後續修復方向

### 如果清理後 list 仍然存在

**檢查 unregister 實現**：
```python
# modules/gui/lap_analysis/analysis_module_manager.py
def unregister_chart_widget(self, chart_widget: object):
    if chart_widget in self._registered_chart_widgets:
        self._registered_chart_widgets.remove(chart_widget)  # ← 真的移除了嗎？
```

**可能的問題**：
1. `chart_widget in list` 比較失敗（物件比較問題）
2. `remove()` 沒有真正執行
3. list 有多個引用副本

**驗證方法**：
```python
# 在 unregister 前後打印 list 內容
print(f"Before: {len(self._registered_chart_widgets)}")
print(f"Contains: {chart_widget in self._registered_chart_widgets}")
self._registered_chart_widgets.remove(chart_widget)
print(f"After: {len(self._registered_chart_widgets)}")
```

---

**當前版本**: v3.1 引用追蹤邏輯修復  
**狀態**: 🧪 待測試  
**改進**: 修復了清理後無法追蹤引用的問題  
**預期**: 能夠精確判斷 list 引用是否被清除
