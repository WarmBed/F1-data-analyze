# 速度模組記憶體洩漏診斷報告 v3.2 (2025-10-15 19:32)

## 🎯 核心問題確認

**GC 回收 0 個物件 = 清理失敗**

```
19:32:24 [SPEED_MDI] ✅ 已執行垃圾回收（回收 0 個物件）
19:32:24 [CRITICAL] ⚠️⚠️⚠️ GC 回收了 0 個物件！物件仍被強引用！
```

---

## 📊 記憶體洩漏證據（Objgraph）

| 階段 | 總物件數 | 變化量 | 說明 |
|------|---------|--------|------|
| 開啟前 | 112,275 | 基線 | 穩定狀態 |
| 開啟後 | 113,163 | **+888** ⬆️ | 模組創建 |
| 關閉後 | 112,857 | **-306** ⬇️ | 部分清理 |
| **洩漏量** | - | **+582** ❌ | **65.5% 未釋放** |

**結論**：開啟增加 888 個物件，關閉僅減少 306 個，**洩漏 582 個物件**！

---

## 🔍 清理流程分析

### ✅ 已執行的步驟

1. **清理前引用追蹤**（19:32:23）
   ```python
   [CRITICAL] speed_chart_widget 被以下物件引用:
       - list: 2 個  ← analysis_manager + linkage_manager
       - dict: 1 個
       - QWidget: 1 個
       - builtin_function_or_method: 1 個
   ```

2. **V3.2 引用保存**（19:32:23）
   ```python
   [CRITICAL] widget_for_final_check: True ✅
   [CRITICAL] manager_for_final_check: True ✅
   ```

3. **調用 unregister 方法**（19:32:23）
   ```python
   [SPEED_MDI] ✅ 已從分析模組管理器解除註冊
   [SPEED_MDI] ✅ 已從連動管理器解除註冊圖表組件
   ```

4. **清理組件**（19:32:24）
   ```python
   [SPEED_MDI] ✅ 已清理 data_manager
   [SPEED_MDI] ✅ 已清理 speed_chart_widget
   [SPEED_MDI] ✅ 已清理 main_widget
   ```

5. **事件循環與 GC**（19:32:24）
   ```python
   [SPEED_MDI] 開始 10 輪事件處理...
   [SPEED_MDI] ✅ 已完成 10 輪事件循環
   [SPEED_MDI] ✅ 已執行垃圾回收（回收 0 個物件）  ← ❌ 問題！
   ```

---

## ❓ 關鍵疑問

### 問題 1：unregister 是否真正執行了 list.remove()？

**程式碼檢查**：
```python
# analysis_module_manager.py (行 131)
if chart_widget in self._registered_chart_widgets:
    self._registered_chart_widgets.remove(chart_widget)  # ✅ 邏輯正確

# linkage_manager.py (行 68)
if module in self.registered_modules:
    self.registered_modules.remove(module)  # ✅ 邏輯正確
```

**可能問題**：
1. ❓ `chart_widget in list` 檢查失敗（物件比較問題）
2. ❓ remove() 拋出異常但被靜默捕獲
3. ❓ list 持有的是副本而非原始引用
4. ❓ 還有其他隱藏的引用來源

### 問題 2：為什麼 GC 回收 0 個物件？

**可能原因**：
1. ✅ **List 沒有釋放引用**（最可能）
   - unregister 方法可能沒有真正執行 remove
   - 或者 remove 失敗但沒有報錯

2. ❓ **還有其他強引用**
   - dict: 1 個（模組內部 `__dict__`）
   - QWidget: 1 個（父容器）
   - builtin_function_or_method: 1 個（Qt 方法）

3. ❓ **循環引用**
   - widget → data_manager → widget
   - widget → QWidget parent → widget

---

## 🛠️ 新增診斷代碼（已實施）

### A. analysis_module_manager.py

```python
def unregister_chart_widget(self, chart_widget: object):
    print(f"[ANALYSIS_MANAGER] 🔍 unregister 前: list 長度 = {len(self._registered_chart_widgets)}")
    print(f"[ANALYSIS_MANAGER] 🔍 widget 在 list 中: {chart_widget in self._registered_chart_widgets}")
    print(f"[ANALYSIS_MANAGER] 🔍 widget ID: {id(chart_widget)}")
    print(f"[ANALYSIS_MANAGER] 🔍 list 中的 ID: {[id(w) for w in self._registered_chart_widgets]}")
    
    if chart_widget in self._registered_chart_widgets:
        self._registered_chart_widgets.remove(chart_widget)
        print(f"[ANALYSIS_MANAGER] ✅ 已從 list 移除")
        print(f"[ANALYSIS_MANAGER] 🔍 unregister 後: list 長度 = {len(self._registered_chart_widgets)}")
    else:
        print(f"[ANALYSIS_MANAGER] ⚠️ widget 不在 list 中，無法移除")
```

### B. linkage_manager.py

```python
def unregister_module(self, module):
    print(f"[LINKAGE_MANAGER] 🔍 unregister 前: list 長度 = {len(self.registered_modules)}")
    print(f"[LINKAGE_MANAGER] 🔍 module 在 list 中: {module in self.registered_modules}")
    print(f"[LINKAGE_MANAGER] 🔍 module ID: {id(module)}")
    print(f"[LINKAGE_MANAGER] 🔍 list 中的 ID: {[id(m) for m in self.registered_modules]}")
    
    if module in self.registered_modules:
        self.registered_modules.remove(module)
        print(f"[LINKAGE_MANAGER] ✅ 已從 list 移除")
        print(f"[LINKAGE_MANAGER] 🔍 unregister 後: list 長度 = {len(self.registered_modules)}")
    else:
        print(f"[LINKAGE_MANAGER] ⚠️ module 不在 list 中，無法移除")
```

---

## 🧪 下次測試計畫

### 測試步驟
1. 啟動 GUI：`python f1t_gui_main.py`
2. 開啟速度模組
3. 關閉速度模組
4. 檢查日誌

### 預期結果

#### 場景 A：List 成功移除引用
```
[ANALYSIS_MANAGER] 🔍 unregister 前: list 長度 = 1
[ANALYSIS_MANAGER] 🔍 widget 在 list 中: True
[ANALYSIS_MANAGER] ✅ 已從 list 移除
[ANALYSIS_MANAGER] 🔍 unregister 後: list 長度 = 0

[LINKAGE_MANAGER] 🔍 unregister 前: list 長度 = 1
[LINKAGE_MANAGER] 🔍 module 在 list 中: True
[LINKAGE_MANAGER] ✅ 已從 list 移除
[LINKAGE_MANAGER] 🔍 unregister 後: list 長度 = 0
```
→ 如果是這個結果但 GC 仍回收 0 個，說明還有其他隱藏引用

#### 場景 B：Widget 不在 List 中
```
[ANALYSIS_MANAGER] 🔍 widget 在 list 中: False
[ANALYSIS_MANAGER] ⚠️ widget 不在 list 中，無法移除
```
→ 說明 register 和 unregister 的物件不一致（ID 不同）

#### 場景 C：ID 不匹配
```
[ANALYSIS_MANAGER] 🔍 widget ID: 2261568941536
[ANALYSIS_MANAGER] 🔍 list 中的 ID: [2261568999999]
[ANALYSIS_MANAGER] 🔍 widget 在 list 中: False
```
→ 說明 list 持有的是不同的物件實例

---

## 📝 檢查清單

### 測試後需要確認：

- [ ] unregister_chart_widget() 是否真的執行了？
- [ ] widget 是否在 list 中（`in` 檢查結果）？
- [ ] widget ID 是否與 list 中的 ID 匹配？
- [ ] list 長度是否從 1 降為 0？
- [ ] unregister_module() 是否真的執行了？
- [ ] module 是否在 list 中？
- [ ] GC 回收了多少個物件？
- [ ] Objgraph 顯示物件是否減少？

---

## 🎯 預期發現

根據症狀判斷，最可能的情況是：

1. **場景 1**：unregister 成功，但還有其他隱藏引用
   - 需要繼續追蹤其他引用來源（dict, QWidget, builtin_function_or_method）

2. **場景 2**：unregister 失敗（widget 不在 list 中）
   - 需要檢查 register 和 unregister 的物件是否一致
   - 可能是物件比較（`==` vs `is`）的問題

3. **場景 3**：list.remove() 拋出異常
   - 需要檢查 try-except 是否靜默吞掉了錯誤

---

## 📞 測試指令

```powershell
# 1. 啟動 GUI
python f1t_gui_main.py

# 2. 開啟速度模組 → 關閉速度模組

# 3. 搜尋 unregister 診斷日誌
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "ANALYSIS_MANAGER.*🔍|LINKAGE_MANAGER.*🔍" | Select-Object -Last 20

# 4. 搜尋 GC 結果
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已執行垃圾回收" | Select-Object -Last 5

# 5. 檢查 unregister 成功/失敗
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已從 list 移除|不在 list 中" | Select-Object -Last 10
```

---

## 🔧 如果 List 成功移除但 GC 仍為 0

需要檢查其他引用來源：

1. **dict 引用**：模組內部 `__dict__` 屬性
   - 需要手動清除：`del self.__dict__['speed_chart_widget']`

2. **QWidget 父容器**：
   - 需要先從父容器移除：`widget.setParent(None)`

3. **builtin_function_or_method**：Qt 的 update() 方法
   - 可能需要斷開 Qt 內部連接

4. **循環引用**：
   - 使用 `gc.get_referrers()` 深度追蹤引用鏈

---

**創建時間**：2025-10-15 19:50
**版本**：v3.2 診斷增強版
**狀態**：等待測試結果
