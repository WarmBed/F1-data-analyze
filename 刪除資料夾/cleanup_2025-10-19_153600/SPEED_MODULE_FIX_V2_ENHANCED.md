================================================================================
速度模組記憶體洩漏修復 v2 - 增強診斷版
================================================================================
修復時間: 2025-10-15 19:10
狀態: ✅ 已實施，等待測試

## 📋 問題確認

根據 `objgraph_report_20251015_185324.txt` 的分析：

### ❌ v1 修復失敗

**現象：**
```
SpeedAnalysisModule          0 → 1 (+1)  [開啟時]
SpeedDataManager             0 → 1 (+1)  [開啟時]
SpeedAnalysisChartWidget     0 → 1 (+1)  [開啟時]
SpeedChartWidget             0 → 1 (+1)  [開啟時]
SpeedAnalysisDataLoader      0 → 1 (+1)  [開啟時]

關閉後: 所有組件消失在 Growth 列表 = 數量仍是 1 = 洩漏！
```

**原因分析：**
1. ❌ processEvents() 只執行 1 次（不足以完成異步刪除）
2. ❌ 缺少引用計數診斷（無法追蹤問題根源）
3. ❌ 缺少 CRITICAL 日誌（無法確認 cleanup() 被調用）
4. ❌ 可能全域管理器仍持有引用

## 🔧 v2 修復內容

### 1. **添加關鍵診斷日誌**

```python
def cleanup(self):
    print(f"[CRITICAL] ========== SPEED_MDI CLEANUP CALLED ==========")
    print(f"[CRITICAL] Module ID: {getattr(self, '_module_id', 'Unknown')}")
    print(f"[CRITICAL] Has data_manager: {hasattr(self, 'data_manager')}")
    print(f"[CRITICAL] Has speed_chart_widget: {hasattr(self, 'speed_chart_widget')}")
```

**目的：** 確認 cleanup() 真的被調用，並顯示模組狀態

### 2. **引用計數診斷**

```python
import sys
import gc

# 清理前
if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
    refcount_before = sys.getrefcount(self.speed_chart_widget)
    print(f"[DEBUG] speed_chart_widget 清理前引用數: {refcount_before}")
    
    # 找出誰持有引用
    referrers = gc.get_referrers(self.speed_chart_widget)
    print(f"[DEBUG] 引用來源數量: {len(referrers)}")
    for i, ref in enumerate(referrers[:3]):
        ref_type = type(ref).__name__
        print(f"[DEBUG]   [{i+1}] {ref_type}")

# ... 清理過程 ...

# 清理後
refcount_after = sys.getrefcount(self.speed_chart_widget)
print(f"[DEBUG] speed_chart_widget 清理後引用數: {refcount_after}")
```

**目的：**
- 看清理前有多少個引用（正常應該 3-5 個）
- 看引用來自哪裡（dict, list, 函數參數等）
- 看清理後引用數是否下降（理想是 2：函數參數 + getrefcount）

### 3. **增強事件處理（10 輪循環）**

```python
import time

print(f"[SPEED_MDI] 開始 10 輪事件處理...")
for i in range(10):
    QApplication.processEvents()
    time.sleep(0.02)  # 20ms 間隔

print(f"[SPEED_MDI] ✅ 已完成 10 輪事件循環")
```

**目的：**
- Qt 的 deleteLater() 需要事件循環處理
- 單次 processEvents() 可能不足以完成所有異步操作
- 10 輪 × 20ms = 200ms 總等待時間
- 每輪之間的 sleep 給 Qt 時間調度

### 4. **垃圾回收結果報告**

```python
collected = gc.collect()
print(f"[SPEED_MDI] ✅ 已執行垃圾回收（回收 {collected} 個物件）")
```

**目的：** 知道 GC 實際回收了多少物件（正常應該 > 0）

### 5. **完成標記**

```python
print(f"[CRITICAL] ========== SPEED_MDI CLEANUP COMPLETED ==========")
```

**目的：** 確認整個 cleanup 流程完整執行

## 📊 預期測試結果

### 成功標準

**1. 終端日誌應該顯示：**
```
[CRITICAL] ========== SPEED_MDI CLEANUP CALLED ==========
[CRITICAL] Module ID: speed_analysis_12345
[CRITICAL] Has data_manager: True
[CRITICAL] Has speed_chart_widget: True
[DEBUG] speed_chart_widget 清理前引用數: 4-6
[DEBUG] 引用來源數量: 3-5
[DEBUG]   [1] dict
[DEBUG]   [2] list
[DEBUG]   [3] frame
[SPEED_MDI] ✅ 已斷開所有信號連接
[SPEED_MDI] ✅ 已從分析模組管理器解除註冊
[SPEED_MDI] ✅ 已從連動管理器解除註冊
[SPEED_MDI] ✅ 已清理 data_manager
[CRITICAL] ========== SPEEDDATAMANAGER CLEANUP CALLED ==========
[SPEEDDATAMANAGER] 開始 10 輪事件處理...
[SPEEDDATAMANAGER] ✅ 已完成 10 輪事件循環
[SPEED_MDI] ✅ 已清理 speed_chart_widget
[SPEED_MDI] ✅ 已清理 main_widget
[SPEED_MDI] 開始 10 輪事件處理...
[SPEED_MDI] ✅ 已完成 10 輪事件循環
[SPEED_MDI] ✅ 已執行垃圾回收（回收 5-10 個物件）
[DEBUG] speed_chart_widget 清理後引用數: 2
[CRITICAL] ========== SPEED_MDI CLEANUP COMPLETED ==========
```

**2. objgraph 報告應該顯示：**
```
關閉後 Growth 追蹤：
SpeedAnalysisModule          1 → 0 (-1)  ✅
SpeedDataManager             1 → 0 (-1)  ✅
SpeedAnalysisChartWidget     1 → 0 (-1)  ✅
SpeedChartWidget             1 → 0 (-1)  ✅
SpeedAnalysisDataLoader      1 → 0 (-1)  ✅
```

**3. 物件總數變化：**
```
開啟前: 113,223
開啟後: 113,158 (+935)
關閉後: 113,223 (完全恢復) ✅
```

### 失敗診斷

**如果引用數清理後仍 > 2：**
→ 檢查引用來源（dict, list）
→ 可能是全域管理器未正確 unregister

**如果 GC 回收數 = 0：**
→ 物件仍被強引用，GC 無法回收
→ 需要檢查全域管理器的實現

**如果沒看到 CRITICAL 日誌：**
→ cleanup() 根本沒被調用
→ 需要檢查 MDI 關閉流程

## 🧪 測試步驟

### 步驟 1: 清除舊數據
```bash
# 重啟 GUI（確保載入最新代碼）
```

### 步驟 2: 執行測試
```
1. 開啟 GUI
2. 開啟 Memory Diagnostics
3. 拍攝快照（初始）
4. 開啟速度模組
5. 拍攝快照（開啟後）
6. 關閉速度模組（觀察終端日誌）
7. 等待 2 秒
8. 拍攝快照（關閉後 2 秒）
9. 再等待 3 秒
10. 拍攝快照（關閉後 5 秒）
11. 匯出報告並分析
```

### 步驟 3: 分析結果

**檢查終端日誌：**
- 是否看到 `[CRITICAL] CLEANUP CALLED`
- 引用數是否從 4-6 降到 2
- GC 是否回收了物件
- 是否完成 10 輪事件處理

**檢查 objgraph 報告：**
- Speed 組件是否顯示 (-1)
- 物件總數是否恢復初始值

## 🔍 進階診斷

### 如果仍然洩漏，執行以下檢查：

#### 1. 檢查全域管理器實現
```bash
grep -A 15 "def unregister_module" modules/gui/lap_analysis/analysis_module_manager.py
```

**尋找：**
```python
def unregister_module(self, module_id):
    # ✅ 正確：刪除引用
    if module_id in self._registered_modules:
        del self._registered_modules[module_id]
    
    # ❌ 錯誤：只標記不刪除
    if module_id in self._registered_modules:
        self._registered_modules[module_id]["active"] = False
```

#### 2. 檢查信號連接
```python
# 在 cleanup() 中添加
print(f"[DEBUG] Checking signal connections...")
print(f"  data_loaded receivers: {self.data_manager.data_loaded.receivers()}")
```

#### 3. 使用 objgraph 追蹤引用鏈
```python
import objgraph

if hasattr(self, 'speed_chart_widget'):
    # 生成引用圖
    objgraph.show_refs(
        [self.speed_chart_widget],
        filename='speed_chart_refs.png',
        max_depth=3
    )
```

## ✅ 下一步

1. **立即測試 v2 修復**
2. **收集完整日誌**
3. **分析引用來源**
4. **如果成功，擴展到其他 8 個模組**

================================================================================
等待測試結果...
================================================================================
