================================================================================
速度模組記憶體洩漏 - 修復後測試結果分析
================================================================================
測試時間: 2025-10-15 18:53:24
報告文件: objgraph_report_20251015_185324.txt
修復狀態: 🔴 **仍然洩漏 - 修復無效**

## 📊 測試數據對比

### 時間線

| 時間 | 操作 | 物件總數 | 變化 | 狀態 |
|------|------|---------|------|------|
| 18:52:51 | GUI 啟動 | 113,223 | +0 | 初始 |
| 18:53:01 | **開啟速度模組** | 112,278 | +6 | 模組創建 |
| 18:53:08 | 數據載入完成 | 113,158 | +680 | 完全初始化 |
| 18:53:14 | **關閉速度模組** | 113,164 | +6 | 調用 cleanup() |
| 18:53:17 | 關閉後 3 秒 | 113,086 | -78 | 部分清理 |
| 18:53:19 | 關閉後 5 秒 | 113,103 | +17 | **最終狀態** |

### 🚨 關鍵發現

#### 1. **5 個核心組件仍然洩漏**

**成長追蹤記錄（行 114-123）：**
```
SpeedAnalysisModule                0 → 1  (+1)
SpeedDataManager                   0 → 1  (+1)
SpeedAnalysisChartWidget           0 → 1  (+1)
SpeedChartWidget                   0 → 1  (+1)
SpeedAnalysisDataLoader            0 → 1  (+1)
```

**開啟時快照（行 2046-2055）：**
```
54. ↑ SpeedAnalysisModule           1 (+1)
55. ↑ SpeedDataManager              1 (+1)
56. ↑ SpeedAnalysisChartWidget      1 (+1)
57. ↑ SpeedChartWidget              1 (+1)
63. ↑ SpeedAnalysisDataLoader       1 (+1)
```

**關閉後所有快照（18:53:17 - 18:53:19）：**
- ❌ **Speed 組件完全消失在列表中**
- ❌ **但不是因為被刪除，而是數量沒變化**
- ❌ **objgraph Growth 只追蹤變化，沒變化 = 仍是 1 個**

#### 2. **物件數量異常分析**

```
預期變化:
  開啟前: 113,223
  開啟後: 113,158 (+935 個速度相關物件)
  關閉後: 113,223 (應恢復初始值)
  
實際變化:
  開啟前: 113,223
  開啟後: 113,158 (+935)
  關閉後: 113,103 (只減少 55)
  
洩漏數量: 113,103 - 113,223 = -120
```

**問題：** 物件數少於初始值 120 個，但這不代表沒洩漏！可能是：
1. GC 清理了其他無關物件（正常系統垃圾）
2. 但 Speed 核心組件仍未釋放
3. 兩者相抵導致總數看似正常

#### 3. **修復代碼被執行了嗎？**

**證據檢查：**
```python
# 我的修復代碼中添加了這些日誌：
print(f"[SPEEDDATAMANAGER] ✅ 已處理事件循環")
print(f"[SPEEDDATAMANAGER] ✅ 已執行垃圾回收")
print(f"[SPEED_MDI] ✅ 已處理事件循環")
print(f"[SPEED_MDI] ✅ 已執行垃圾回收")
```

**問題：** objgraph 報告中沒有顯示這些日誌！
**可能原因：**
1. GUI 終端輸出未被捕獲到報告中
2. 或者根本沒有執行到這些代碼
3. 需要檢查是否真的調用了 cleanup()

## 🔍 深度診斷

### 假設 1: cleanup() 根本沒被調用 ⚠️

**驗證方法：**
```python
# 在 cleanup() 第一行添加
print(f"[CRITICAL] ========== CLEANUP CALLED ==========")
```

如果這行沒出現，說明 MDI 關閉沒有調用 cleanup()

### 假設 2: processEvents() 和 gc.collect() 時機太早 ⚠️

**問題分析：**
```python
def cleanup(self):
    # 1. 斷開信號
    # 2. 刪除子組件
    self.speed_chart_widget.deleteLater()
    
    # 3. 立即 processEvents() - 可能太早！
    QApplication.processEvents()
    
    # 4. 立即 gc.collect() - 可能太早！
    gc.collect()
```

**問題：** deleteLater() 是**異步**的，即使調用 processEvents()，Qt 可能需要**多次事件循環**才能真正刪除物件！

**正確做法：**
```python
# 需要等待一段時間或多次 processEvents
self.speed_chart_widget.deleteLater()

for i in range(5):  # 多次處理事件
    QApplication.processEvents()
    time.sleep(0.05)  # 給 Qt 時間處理

gc.collect()
```

### 假設 3: 全域管理器仍持有引用 ⚠️

**問題代碼：**
```python
# analysis_manager 的字典
self._registered_modules = {
    "speed_analysis_12345": <SpeedAnalysisModule>,  # 強引用！
}

# linkage_manager 的字典
self._linkage_map = {
    "speed_chart": <SpeedChartWidget>  # 強引用！
}
```

**即使調用：**
```python
self._analysis_manager.unregister_module(self._module_id)
linkage_manager.unregister_module(self.speed_chart_widget)
```

**如果 unregister 實現有問題：**
```python
def unregister_module(self, module_id):
    # ❌ 錯誤實現：只標記為不活躍，不刪除引用
    self._registered_modules[module_id]["active"] = False
    
    # ✅ 正確實現：必須刪除字典項
    if module_id in self._registered_modules:
        del self._registered_modules[module_id]
```

### 假設 4: 信號連接未真正斷開 ⚠️

**我的修復代碼：**
```python
try:
    self.data_manager.data_loaded.disconnect()
except (TypeError, RuntimeError):
    pass
```

**問題：** `disconnect()` 不帶參數時會斷開**所有**連接，但如果：
1. 信號從未連接過（程序流程問題）
2. 信號連接在其他地方（不只是 cleanup 中）
3. PyQt 信號系統的內部引用問題

**更安全的做法：**
```python
# 明確斷開特定的槽函數
try:
    self.data_manager.data_loaded.disconnect(self._update_chart)
except (TypeError, RuntimeError):
    pass
```

## 🎯 下一步行動計畫

### 優先級 1: 確認 cleanup() 被調用 ✅ 

**修改代碼：**
```python
def cleanup(self):
    print(f"[CRITICAL] ========== SPEED_MDI CLEANUP CALLED ==========")
    print(f"[CRITICAL] Module ID: {getattr(self, '_module_id', 'Unknown')}")
    print(f"[CRITICAL] Has data_manager: {hasattr(self, 'data_manager')}")
    print(f"[CRITICAL] Has speed_chart_widget: {hasattr(self, 'speed_chart_widget')}")
```

### 優先級 2: 增強事件處理 ✅

**修改代碼：**
```python
# 階段 4: 多次處理事件循環
try:
    from PyQt5.QtWidgets import QApplication
    import time
    
    for i in range(10):  # 10 次循環
        QApplication.processEvents()
        time.sleep(0.02)  # 20ms 間隔
    
    print(f"[SPEED_MDI] ✅ 已處理 10 輪事件循環")
except Exception as e:
    print(f"[SPEED_MDI] ⚠️ 處理事件循環失敗: {e}")
```

### 優先級 3: 驗證 unregister 實現 ✅

**檢查代碼：**
```bash
# 檢查 analysis_manager 的 unregister_module 實現
grep -A 10 "def unregister_module" modules/gui/lap_analysis/analysis_module_manager.py

# 檢查 linkage_manager 的 unregister_module 實現
grep -A 10 "def unregister_module" modules/gui/lap_analysis/linkage/linkage_manager.py
```

### 優先級 4: 添加引用計數檢查 ✅

**診斷代碼：**
```python
def cleanup(self):
    import sys
    
    # 檢查引用計數
    if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
        refcount = sys.getrefcount(self.speed_chart_widget)
        print(f"[DEBUG] speed_chart_widget 引用數: {refcount}")
        
        # 找出誰持有引用
        import gc
        referrers = gc.get_referrers(self.speed_chart_widget)
        print(f"[DEBUG] 引用來源數量: {len(referrers)}")
        for i, ref in enumerate(referrers[:5]):
            print(f"[DEBUG]   [{i}] {type(ref).__name__}")
```

## ✅ 立即執行的修復

我現在立即實施以下修復：

1. **添加關鍵日誌**：確認 cleanup() 被調用
2. **增強事件處理**：10 輪 processEvents() + sleep
3. **添加引用計數診斷**：找出誰持有引用

修復後重新測試，觀察：
- cleanup() 日誌是否出現
- 引用計數是否下降到 2（預期的最低值：函數參數 + getrefcount 本身）
- Speed 組件是否在最終快照顯示 (-1)

================================================================================
報告結束 - 準備實施修復 v2
================================================================================
