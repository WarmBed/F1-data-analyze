# Speed 模組記憶體洩漏診斷 v3.2 - 修復引用保存時機

## 🐛 v3.1 測試結果分析

### 問題確認

從日誌 `logs/f1_gui_2025-10-15.log` (19:25:32 時間段) 發現：

#### ✅ 清理前引用追蹤正常
```
[CRITICAL] speed_chart_widget 引用來源分類:
[CRITICAL]     - list: 2 個
[CRITICAL]     - dict: 1 個
[CRITICAL]     - QWidget: 1 個
```

#### ❌ 清理後引用追蹤缺失
```
[CRITICAL] ⚠️⚠️⚠️ GC 回收了 0 個物件！物件仍被強引用！
[CRITICAL]     - dict: 1 個
[CRITICAL]     - frame: 1 個
[CRITICAL] ========== SPEED_MDI CLEANUP COMPLETED ==========
```

**沒有 "widget 清理後引用" 的日誌！** 這意味著 `widget_for_final_check` 是 `None`！

---

## 🔍 根本原因

### 錯誤的代碼邏輯（v3.1）

```python
# 階段 3: 清理子組件
# 🔍 保存引用
widget_for_final_check = None          # ❌ 先初始化為 None
manager_for_final_check = None         # ❌ 先初始化為 None

# 3.1 清理 data_manager
if hasattr(self, 'data_manager') and self.data_manager:
    manager_for_final_check = self.data_manager  # ✅ 這裡保存了
    # ...

# 3.2 清理 chart_widget
if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
    widget_for_final_check = self.speed_chart_widget  # ✅ 這裡保存了
    # ...
```

**問題**：雖然在 if 區塊內保存了引用，但如果條件檢查失敗（例如異常或順序問題），變數就會保持為 `None`！

### 為什麼條件可能失敗？

可能的情況：
1. **異常發生**：在保存引用前發生異常
2. **順序問題**：某些情況下 widget 已經被提前清理
3. **條件檢查失敗**：`hasattr()` 或 `self.speed_chart_widget` 檢查失敗

---

## 🔧 v3.2 修復方案

### 正確的邏輯（v3.2）

```python
# 階段 3: 清理子組件
# 🔍 保存引用（在清理前立即保存）
widget_for_final_check = self.speed_chart_widget if hasattr(self, 'speed_chart_widget') else None
manager_for_final_check = self.data_manager if hasattr(self, 'data_manager') else None

print(f"[CRITICAL] 🔍 已保存引用用於最終檢查:")
print(f"[CRITICAL]   widget_for_final_check: {widget_for_final_check is not None}")
print(f"[CRITICAL]   manager_for_final_check: {manager_for_final_check is not None}")

# 3.1 清理 data_manager（不再重複保存）
if hasattr(self, 'data_manager') and self.data_manager:
    # ... 清理代碼

# 3.2 清理 chart_widget（不再重複保存）
if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
    # ... 清理代碼
```

**改進**：
1. ✅ **提前保存**：在任何清理操作前就保存引用
2. ✅ **條件表達式**：用三元運算符確保一定有值（要麼物件，要麼 None）
3. ✅ **診斷輸出**：立即打印保存狀態，方便驗證
4. ✅ **避免重複**：不在 if 區塊內重複保存

---

## 🎯 預期改進

### v3.2 測試後應該看到

#### 保存引用確認
```
[CRITICAL] 🔍 已保存引用用於最終檢查:
[CRITICAL]   widget_for_final_check: True
[CRITICAL]   manager_for_final_check: True
```

#### 清理前引用狀態
```
[CRITICAL] speed_chart_widget 引用來源分類:
[CRITICAL]     - list: 2 個
[CRITICAL]     - dict: 1 個
```

#### 清理後引用狀態（關鍵！）
```
[CRITICAL] 🔍 widget 清理後引用數: X
[CRITICAL] 🔍 widget 清理後被引用數量: Y
[CRITICAL] 🔍 widget 清理後引用來源分類:
[CRITICAL]     - list: Z 個  ← 關鍵：是 0 還是仍然 > 0？
[CRITICAL]     - frame: N 個
```

#### 如果 list 仍然存在
```
[CRITICAL] ⚠️⚠️⚠️ widget 仍被 2 個 list 持有！
```

---

## 🧪 測試步驟

### 執行測試
```powershell
# 1. 啟動 GUI
python f1t_gui_main.py

# 2. 打開速度模組 → 關閉

# 3. 查看保存引用確認
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已保存引用" | Select-Object -Last 5

# 4. 查看清理後引用狀態
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "widget 清理後|⚠️⚠️⚠️.*list" | Select-Object -Last 20
```

---

## 📊 診斷決策樹

根據 v3.2 測試結果，可以判斷：

### 情況 A：保存失敗
```
[CRITICAL]   widget_for_final_check: False  ← 沒保存到
```
**原因**：`self.speed_chart_widget` 根本不存在  
**下一步**：檢查 widget 初始化邏輯

### 情況 B：保存成功，但清理後 list 仍在
```
[CRITICAL]   widget_for_final_check: True
[CRITICAL] 🔍 widget 清理後引用來源分類:
[CRITICAL]     - list: 2 個  ← 仍然有 2 個！
[CRITICAL] ⚠️⚠️⚠️ widget 仍被 2 個 list 持有！
```
**原因**：`unregister_chart_widget()` 和 `unregister_module()` 沒有真正從 list 移除  
**下一步**：深入檢查 `analysis_manager` 和 `linkage_manager` 的 unregister 實現

### 情況 C：保存成功，list 已清除
```
[CRITICAL]   widget_for_final_check: True
[CRITICAL] 🔍 widget 清理後引用來源分類:
[CRITICAL]     - frame: 2 個  ← 只剩 Python 堆疊
[SPEED_MDI] ✅ 已執行垃圾回收（回收 5 個物件）  ← 成功！
```
**結果**：修復成功！  
**下一步**：應用到其他模組

---

## 🔧 如果是情況 B（list 未清除）

需要深入檢查 unregister 實現：

### 檢查點 1：analysis_manager.unregister_chart_widget()
```python
# modules/gui/lap_analysis/analysis_module_manager.py
def unregister_chart_widget(self, chart_widget: object):
    if chart_widget in self._registered_chart_widgets:
        # 🔍 需要驗證：
        # 1. chart_widget in list 是否返回 True？
        # 2. remove() 是否真的執行？
        # 3. 異常是否被捕獲？
        self._registered_chart_widgets.remove(chart_widget)
```

### 檢查點 2：linkage_manager.unregister_module()
```python
# modules/gui/lap_analysis/linkage/linkage_manager.py
def unregister_module(self, module):
    if module in self.registered_modules:
        # 🔍 需要驗證：
        # 1. module in list 是否返回 True？
        # 2. remove() 是否真的執行？
        self.registered_modules.remove(module)
```

### 驗證方法：添加診斷日誌
```python
def unregister_chart_widget(self, chart_widget: object):
    print(f"[ANALYSIS_MANAGER] unregister 前 list 長度: {len(self._registered_chart_widgets)}")
    print(f"[ANALYSIS_MANAGER] widget 是否在 list 中: {chart_widget in self._registered_chart_widgets}")
    
    if chart_widget in self._registered_chart_widgets:
        print(f"[ANALYSIS_MANAGER] 準備從 list 移除...")
        self._registered_chart_widgets.remove(chart_widget)
        print(f"[ANALYSIS_MANAGER] unregister 後 list 長度: {len(self._registered_chart_widgets)}")
    else:
        print(f"[ANALYSIS_MANAGER] ⚠️ widget 不在 list 中，無法移除！")
```

---

**當前版本**: v3.2 引用保存時機修復  
**狀態**: 🧪 待測試  
**關鍵改進**: 在清理操作前立即保存引用，確保清理後可以追蹤  
**預期**: 能夠看到清理後的引用狀態，判斷 list 是否被清除
