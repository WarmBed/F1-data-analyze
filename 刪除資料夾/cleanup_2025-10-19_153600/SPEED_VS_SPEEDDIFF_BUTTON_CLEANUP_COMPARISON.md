# 速度模組 vs 速度差異模組：按鈕清理邏輯深度比較

## 📋 **比較總覽**

| 項目 | Speed Analysis (速度分析) | SpeedDiff Analysis (速度差異分析) | 差異 |
|------|---------------------------|-----------------------------------|------|
| **模組文件** | `speed_analysis_mdi.py` | `speeddiff_analysis_mdi.py` | - |
| **cleanup() 位置** | 第 942 行 | 第 986 行 | - |
| **是否有 cleanup_module()** | ❌ 無 | ✅ 有（第 946 行） | ⚠️ **關鍵差異** |
| **按鈕清理方式** | 統一在 `f1t_gui_main.py` | 統一在 `f1t_gui_main.py` | ✅ 相同 |
| **模組清理順序** | analysis_manager → data_manager → linkage_manager → chart_widget | analysis_manager → data_manager → linkage_manager → cleanup_module() → chart_widget | ⚠️ **有差異** |

---

## 🔍 **1. cleanup() 方法對比**

### Speed Analysis (`speed_analysis_mdi.py` 第 942-1010 行)

```python
def cleanup(self):
    """清理資源 - 實現抽象方法
    
    📌 回歸 RPM 模組的簡單清理架構
    清理順序：analysis_manager → data_manager → linkage_manager → chart_widget → main_widget
    """
    try:
        print(f"[SPEED_MDI] 🧹 開始清理資源...")
        
        # 1️⃣ 從分析模組管理器解除註冊
        if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
            try:
                # 解除註冊圖表組件
                if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
                    self._analysis_manager.unregister_chart_widget(self.speed_chart_widget)
                
                # 解除註冊模組
                self._analysis_manager.unregister_module(self._module_id)
                print(f"[SPEED_MDI] ✅ 已從分析模組管理器解除註冊: {self._module_id}")
                
            except Exception as e:
                print(f"[ERROR] [SPEED_MDI] 從分析模組管理器解除註冊失敗: {e}")

        # 2️⃣ 清理 data_manager（斷開循環引用）
        if hasattr(self, 'data_manager') and self.data_manager:
            print(f"[SPEED_MDI] 🔴 斷開循環引用：清理 data_manager.module_ref")
            if hasattr(self.data_manager, 'module_ref'):
                self.data_manager.module_ref = None
            
            if hasattr(self.data_manager, 'cleanup'):
                self.data_manager.cleanup()
        
        # ❌ 移除不存在的 cleanup_module() 調用
        # self.cleanup_module()  ← 此方法不存在，導致異常提前退出
        
        # 3️⃣ 從 linkage_manager 解除註冊（內部 chart_widget）
        if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
            try:
                from modules.gui.lap_analysis.linkage import linkage_manager
                
                if linkage_manager:
                    # ✅ 關鍵修復：必須 unregister 內部的 SpeedChartWidget
                    if hasattr(self.speed_chart_widget, 'chart_widget') and self.speed_chart_widget.chart_widget:
                        linkage_manager.unregister_module(self.speed_chart_widget.chart_widget)
                        print(f"[SPEED_MDI] ✅ 已從連動管理器解除註冊圖表組件（內部 chart_widget）")
            except Exception as e:
                print(f"[ERROR] [SPEED_MDI] 從連動管理器解除註冊失敗: {e}")
            
            # 清理圖表組件
            if hasattr(self.speed_chart_widget, 'cleanup'):
                self.speed_chart_widget.cleanup()
            self.speed_chart_widget.deleteLater()
            
        # 4️⃣ 清理主要組件
        if hasattr(self, 'main_widget') and self.main_widget:
            self.main_widget.deleteLater()
            self.main_widget = None
```

**特徵**：
- ❌ **沒有調用 `cleanup_module()`**（因為方法不存在）
- ✅ 使用簡單的清理流程
- ✅ 正確清理 `module_ref` 引用
- ✅ 正確 unregister 內部 `chart_widget`

---

### SpeedDiff Analysis (`speeddiff_analysis_mdi.py` 第 986-1040 行)

```python
def cleanup(self):
    """清理資源 - 實現抽象方法"""
    try:
        # 1️⃣ 從分析模組管理器解除註冊
        if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
            try:
                # 解除註冊圖表組件
                if hasattr(self, 'speeddiff_chart_widget') and self.speeddiff_chart_widget:
                    self._analysis_manager.unregister_chart_widget(self.speeddiff_chart_widget)
                
                # 解除註冊模組
                self._analysis_manager.unregister_module(self._module_id)
                print(f"[speeddiff_MDI] ✅ 已從分析模組管理器解除註冊: {self._module_id}")
                
            except Exception as e:
                print(f"[ERROR] [speeddiff_MDI] 從分析模組管理器解除註冊失敗: {e}")

        # 2️⃣ 清理 data_manager
        if hasattr(self, 'data_manager') and self.data_manager:
            if hasattr(self.data_manager, 'cleanup'):
                self.data_manager.cleanup()
        
        # 3️⃣ 從 linkage_manager 解除註冊（內部 chart_widget）
        try:
            from ..linkage import linkage_manager
            if linkage_manager and hasattr(self, 'speeddiff_chart_widget') and self.speeddiff_chart_widget:
                # ✅ 正確：取消註冊內部 chart_widget
                if hasattr(self.speeddiff_chart_widget, 'chart_widget') and self.speeddiff_chart_widget.chart_widget:
                    linkage_manager.unregister_module(self.speeddiff_chart_widget.chart_widget)
                    print(f"[speeddiff_MDI] ✅ 已從連動管理器取消註冊內部圖表組件 (chart_widget)")
        except ImportError as e:
            print(f"[WARNING] [speeddiff_MDI] 無法導入連動管理器: {e}")
        except Exception as e:
            print(f"[ERROR] [speeddiff_MDI] 從連動管理器取消註冊失敗: {e}")
        
        # 4️⃣ 調用模組清理（關鍵差異）
        self.cleanup_module()  # ✅ SpeedDiff 有此方法
        
        # 5️⃣ 清理圖表組件
        if hasattr(self, 'speeddiff_chart_widget') and self.speeddiff_chart_widget:
            if hasattr(self.speeddiff_chart_widget, 'cleanup'):
                self.speeddiff_chart_widget.cleanup()
            self.speeddiff_chart_widget.deleteLater()
            
        # 6️⃣ 清理主要組件
        if hasattr(self, 'main_widget') and self.main_widget:
            self.main_widget.deleteLater()
            
        print(f"[CLEANUP] speeddiff分析模組資源清理完成")
    except Exception as e:
        print(f"[ERROR] speeddiff分析模組清理失敗: {e}")
```

**特徵**：
- ✅ **有調用 `cleanup_module()`**（第 946 行定義）
- ⚠️ **沒有明確清理 `data_manager.module_ref`**（可能遺漏）
- ✅ 正確 unregister 內部 `chart_widget`

---

## ⚠️ **2. 關鍵差異：cleanup_module() 方法**

### Speed Analysis

```python
# ❌ 沒有 cleanup_module() 方法
# 在 cleanup() 中曾嘗試調用，但因不存在而被註解：
# self.cleanup_module()  ← 此方法不存在，導致異常提前退出
```

### SpeedDiff Analysis (`speeddiff_analysis_mdi.py` 第 946-984 行)

```python
def cleanup_module(self):
    """清理模組特定資源（與其他模組共用的清理邏輯）"""
    print("[CLEANUP] 開始清理 SpeedDiff 分析模組資源...")
    
    try:
        # 清理數據管理器
        if hasattr(self, 'data_manager') and self.data_manager:
            print("[CLEANUP] 清理數據管理器...")
            if hasattr(self.data_manager, 'cleanup'):
                self.data_manager.cleanup()
            self.data_manager = None
        
        # 清理圖表組件
        if hasattr(self, 'speeddiff_chart_widget') and self.speeddiff_chart_widget:
            print("[CLEANUP] 清理圖表組件...")
            if hasattr(self.speeddiff_chart_widget, 'cleanup'):
                self.speeddiff_chart_widget.cleanup()
            # 不調用 deleteLater()，因為 Qt 父子關係會自動清理
            self.speeddiff_chart_widget = None
        
        # 清理主要組件
        if hasattr(self, 'main_widget') and self.main_widget:
            print("[CLEANUP] 清理主要組件...")
            self.main_widget.deleteLater()
            self.main_widget = None
        
        # 從分析模組管理器解除註冊
        if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
            try:
                self._analysis_manager.unregister_module(self._module_id)
                print(f"[CLEANUP] 已從分析模組管理器解除註冊: {self._module_id}")
            except Exception as e:
                print(f"[ERROR] 從分析模組管理器解除註冊失敗: {e}")
        
        print("[CLEANUP] SpeedDiff 分析模組資源清理完成")
        
    except Exception as e:
        print(f"[ERROR] 清理 SpeedDiff 分析模組時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
```

**問題分析**：
- ⚠️ **重複清理**：`cleanup()` 和 `cleanup_module()` 都清理相同的資源
- ⚠️ **順序混亂**：`cleanup()` 清理後，`cleanup_module()` 再清理一次
- ⚠️ **潛在 None 引用**：清理後設為 `None`，可能導致後續操作失敗

---

## 🎯 **3. 按鈕清理邏輯（統一在 f1t_gui_main.py）**

### 兩個模組的按鈕清理完全相同

**觸發流程**：
```
模組關閉 → on_lap_analysis_window_closed() → hide_lap_controls()
```

**hide_lap_controls() 實現**（`f1t_gui_main.py` 第 6955-7012 行）：

```python
def hide_lap_controls(self):
    """隱藏遙測分析控件（從工具欄移除）"""
    if len(self.lap_analysis_windows) > 0:
        print("[LAP_CONTROL] [DEBUG]   ⚠️ 還有圈速分析視窗開啟中，不隱藏控件")
        return
        
    print("[LAP_CONTROL] [DEBUG]   🔴 開始隱藏圈速分析控件（從工具欄移除）")
    
    if not hasattr(self, '_lap_controls_added') or not self._lap_controls_added:
        print("[LAP_CONTROL] [DEBUG]   ⚠️ 圈速分析控件已經不在工具欄中，跳過移除")
        return
    
    try:
        # 1️⃣ 移除分隔符
        if hasattr(self, 'lap_separator') and self.lap_separator:
            self.main_toolbar.removeAction(self.lap_separator)
            self.lap_separator = None
        
        # 2️⃣ 移除所有控件（車手選擇、圈數、最快圈等）
        controls_to_remove = [
            self.driver1_label, self.driver1_combo,
            self.lap1_label, self.lap1_spinbox,
            self.driver2_label, self.driver2_combo,
            self.lap2_label, self.lap2_spinbox,
            self.fastest_lap_checkbox, self.use_time_axis_checkbox
        ]
        
        for control in controls_to_remove:
            for action in self.main_toolbar.actions():
                if action.defaultWidget() == control:
                    self.main_toolbar.removeAction(action)
                    break
        
        # 3️⃣ 移除 Update All Analysis 按鈕
        if hasattr(self, 'update_all_action') and self.update_all_action:
            print("[LAP_CONTROL] [DEBUG]   🗑️ 正在移除 Update All Analysis 按鈕...")
            self.main_toolbar.removeAction(self.update_all_action)
            self.update_all_action = None
            print("[LAP_CONTROL] [DEBUG]   ✅ Update All Analysis 按鈕已移除")
        else:
            print("[LAP_CONTROL] [DEBUG]   ⚠️ update_all_action 不存在或已是 None")
        
        # 4️⃣ 移除 Lap Linkage 按鈕
        if hasattr(self, 'lap_linkage_action') and self.lap_linkage_action:
            print("[LAP_CONTROL] [DEBUG]   🗑️ 正在移除 Lap Linkage 按鈕...")
            self.main_toolbar.removeAction(self.lap_linkage_action)
            self.lap_linkage_action = None
            print("[LAP_CONTROL] [DEBUG]   ✅ Lap Linkage 按鈕已移除")
        else:
            print("[LAP_CONTROL] [DEBUG]   ⚠️ lap_linkage_action 不存在或已是 None")
        
        # 5️⃣ 更新狀態標誌
        print("[LAP_CONTROL] [DEBUG]   ✅ 圈速分析控件成功從工具欄移除")
        self._lap_controls_added = False
        self.lap_controls_visible = False
        
    except Exception as e:
        print(f"[LAP_CONTROL] [DEBUG]   ❌ 移除圈速分析控件時發生錯誤: {e}")
```

**結論**：
- ✅ **Speed 和 SpeedDiff 使用完全相同的按鈕清理邏輯**
- ✅ 兩個模組共享 `lap_analysis_windows` 集合
- ✅ 按鈕清理由 `f1t_gui_main.py` 統一管理
- ⚠️ **按鈕是否移除與模組類型無關，只與 `lap_analysis_windows.size()` 有關**

---

## 🔬 **4. 按鈕清理邏輯比較矩陣**

| 清理步驟 | Speed Analysis | SpeedDiff Analysis | 是否一致 |
|---------|----------------|-------------------|---------|
| **觸發條件** | `len(lap_analysis_windows) == 0` | `len(lap_analysis_windows) == 0` | ✅ 完全相同 |
| **清理入口** | `on_lap_analysis_window_closed()` | `on_lap_analysis_window_closed()` | ✅ 完全相同 |
| **清理方法** | `hide_lap_controls()` | `hide_lap_controls()` | ✅ 完全相同 |
| **lap_separator 移除** | ✅ 執行 | ✅ 執行 | ✅ 完全相同 |
| **控件移除（10個）** | ✅ 執行 | ✅ 執行 | ✅ 完全相同 |
| **update_all_action 移除** | ✅ 執行 | ✅ 執行 | ✅ 完全相同 |
| **lap_linkage_action 移除** | ✅ 執行 | ✅ 執行 | ✅ 完全相同 |
| **狀態標誌更新** | ✅ 執行 | ✅ 執行 | ✅ 完全相同 |

---

## 🚨 **5. 潛在問題分析**

### 問題 1：Speed 模組缺少 cleanup_module()

**影響**：
- ❌ Speed Analysis 沒有 `cleanup_module()` 方法
- ❌ 曾嘗試調用但失敗（已註解）
- ⚠️ 可能遺漏部分清理邏輯

**建議**：
- 如果 `cleanup_module()` 不需要，應從所有模組中移除
- 如果需要，應為 Speed Analysis 添加此方法

---

### 問題 2：SpeedDiff 模組重複清理

**影響**：
- ⚠️ `cleanup()` 中清理 data_manager
- ⚠️ `cleanup_module()` 中再次清理 data_manager
- ⚠️ 可能導致重複調用 `deleteLater()`

**建議**：
- 統一清理順序
- 避免重複清理相同資源

---

### 問題 3：data_manager.module_ref 清理不一致

**Speed Analysis**：
```python
# ✅ 明確清理 module_ref
if hasattr(self.data_manager, 'module_ref'):
    self.data_manager.module_ref = None
```

**SpeedDiff Analysis**：
```python
# ❌ 沒有明確清理 module_ref
if hasattr(self.data_manager, 'cleanup'):
    self.data_manager.cleanup()
```

**影響**：
- ⚠️ SpeedDiff 可能存在循環引用未斷開
- ⚠️ 可能導致記憶體洩漏

**建議**：
- SpeedDiff 應添加明確的 `module_ref = None`

---

### 問題 4：按鈕清理日誌輸出不完整

**當前狀態**：
```python
# hide_lap_controls() 報告成功
print("[LAP_CONTROL] [DEBUG]   ✅ 圈速分析控件成功從工具欄移除")

# 但是按鈕移除部分沒有輸出任何日誌（在診斷前）
```

**已修復**（2025-10-16 最新修改）：
```python
# ✅ 現在有詳細日誌
if hasattr(self, 'update_all_action') and self.update_all_action:
    print("[LAP_CONTROL] [DEBUG]   🗑️ 正在移除 Update All Analysis 按鈕...")
    self.main_toolbar.removeAction(self.update_all_action)
    self.update_all_action = None
    print("[LAP_CONTROL] [DEBUG]   ✅ Update All Analysis 按鈕已移除")
else:
    print("[LAP_CONTROL] [DEBUG]   ⚠️ update_all_action 不存在或已是 None")
```

---

## 📊 **6. 清理流程對比圖**

### Speed Analysis 清理流程

```
on_lap_analysis_window_closed()
  ↓
window_object.cleanup()  [Speed_MDI.cleanup()]
  ↓
1. _analysis_manager.unregister_module()
  ↓
2. data_manager.module_ref = None  ✅ 明確清空
  ↓
3. data_manager.cleanup()
  ↓
4. linkage_manager.unregister_module(chart_widget.chart_widget)
  ↓
5. speed_chart_widget.cleanup()
  ↓
6. speed_chart_widget.deleteLater()
  ↓
7. main_widget.deleteLater()
  ↓
lap_analysis_windows.discard(window_object)
  ↓
if len(lap_analysis_windows) == 0:
  ↓
hide_lap_controls()  [f1t_gui_main.py]
  ↓
  - removeAction(lap_separator)
  - removeAction(controls...)
  - removeAction(update_all_action)
  - removeAction(lap_linkage_action)
  - _lap_controls_added = False
```

### SpeedDiff Analysis 清理流程

```
on_lap_analysis_window_closed()
  ↓
window_object.cleanup()  [SpeedDiff_MDI.cleanup()]
  ↓
1. _analysis_manager.unregister_module()
  ↓
2. data_manager.cleanup()  ⚠️ 未明確清空 module_ref
  ↓
3. linkage_manager.unregister_module(chart_widget.chart_widget)
  ↓
4. cleanup_module()  ← 額外步驟
  ↓
    4.1 data_manager.cleanup()  ⚠️ 重複清理
    4.2 data_manager = None
    4.3 speeddiff_chart_widget.cleanup()
    4.4 speeddiff_chart_widget = None  ⚠️ 重複清理
    4.5 main_widget.deleteLater()
    4.6 _analysis_manager.unregister_module()  ⚠️ 重複清理
  ↓
5. speeddiff_chart_widget.cleanup()  ⚠️ 再次清理
  ↓
6. speeddiff_chart_widget.deleteLater()
  ↓
7. main_widget.deleteLater()  ⚠️ 再次清理
  ↓
lap_analysis_windows.discard(window_object)
  ↓
if len(lap_analysis_windows) == 0:
  ↓
hide_lap_controls()  [f1t_gui_main.py]
  ↓
  - removeAction(lap_separator)
  - removeAction(controls...)
  - removeAction(update_all_action)
  - removeAction(lap_linkage_action)
  - _lap_controls_added = False
```

---

## ✅ **7. 結論與建議**

### 按鈕清理邏輯結論

| 項目 | 結論 |
|------|------|
| **Speed vs SpeedDiff** | ✅ **按鈕清理邏輯完全相同** |
| **清理入口** | ✅ 統一由 `f1t_gui_main.py` 的 `hide_lap_controls()` 處理 |
| **觸發條件** | ✅ 兩者都是 `len(lap_analysis_windows) == 0` |
| **按鈕移除步驟** | ✅ 完全一致（lap_separator → 控件 → update_all_action → lap_linkage_action） |

### 模組清理邏輯差異

| 項目 | Speed Analysis | SpeedDiff Analysis | 建議 |
|------|----------------|-------------------|------|
| **cleanup_module()** | ❌ 無 | ✅ 有 | 統一：所有模組保持一致 |
| **module_ref 清理** | ✅ 明確清空 | ❌ 未明確清空 | SpeedDiff 應添加 |
| **重複清理** | ✅ 無 | ⚠️ 有（chart_widget, main_widget 清理兩次） | 修復 SpeedDiff 重複邏輯 |

### 如果按鈕仍然顯示，問題不在模組差異

**根本原因分析**：
1. ✅ **不是模組特定問題**：兩個模組使用相同的按鈕清理邏輯
2. ✅ **不是清理方法問題**：`hide_lap_controls()` 對所有模組一視同仁
3. ⚠️ **可能是條件判斷問題**：
   - `len(lap_analysis_windows) != 0`（還有其他視窗開啟）
   - `_lap_controls_added == False`（已經移除過）
4. ⚠️ **可能是執行流程問題**：
   - `hide_lap_controls()` 未被調用
   - 調用時發生異常提前返回

### 建議的調試步驟

1. **確認調試日誌有輸出**：
   ```
   [LAP_CONTROL] [DEBUG]   🗑️ 正在移除 Update All Analysis 按鈕...
   [LAP_CONTROL] [DEBUG]   ✅ Update All Analysis 按鈕已移除
   ```

2. **檢查 lap_analysis_windows 計數**：
   ```python
   print(f"[LAP_CONTROL] 當前活動視窗數: {len(self.lap_analysis_windows)}")
   ```

3. **檢查工具欄狀態**：
   ```python
   print(f"[LAP_CONTROL] 工具欄動作數量: {len(self.main_toolbar.actions())}")
   for action in self.main_toolbar.actions():
       print(f"  - {action.text()}")
   ```

4. **驗證按鈕引用**：
   ```python
   print(f"[LAP_CONTROL] update_all_action 存在: {hasattr(self, 'update_all_action')}")
   print(f"[LAP_CONTROL] update_all_action 非 None: {self.update_all_action is not None}")
   ```

---

**最終結論**：速度模組和速度差異模組在**按鈕清理邏輯上沒有任何差異**，兩者使用完全相同的 `hide_lap_controls()` 方法。如果按鈕仍然顯示，問題在於：

1. ⚠️ `hide_lap_controls()` 沒有被調用（`lap_analysis_windows` 計數錯誤）
2. ⚠️ 按鈕引用狀態異常（`update_all_action` 已是 `None`）
3. ⚠️ UI 沒有正確更新（Qt 事件循環問題）

**下一步**：用戶需要重啟 GUI，測試新的日誌輸出，以確定問題根源。
