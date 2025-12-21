# 🎉 Speed 模組記憶體洩漏完整修復報告

**修復日期**：2025-10-16  
**修復狀態**：✅ 完成（100%）  
**測試狀態**：⚠️ 待測試驗證  
**嚴重程度**：🔴 最高

---

## 📊 修復統計總覽

### **修復前**
- **洩漏組件**：5 個（SpeedAnalysisModule, SpeedDataManager, SpeedAnalysisChartWidget, SpeedChartWidget, SpeedAnalysisDataLoader）
- **Force GC 回收**：0 個對象 ❌
- **objgraph 計數**：全部 ≥ 1 ❌

### **修復後**
- **洩漏組件**：0 個（預期） ✅
- **Force GC 回收**：5+ 個對象（預期） ✅
- **objgraph 計數**：全部 = 0（預期） ✅

---

## 🎯 修復項目總覽

| 類別 | 問題類型 | 修復數量 | 修復狀態 |
|------|---------|---------|---------|
| **Circular Reference** | module_ref 循環引用 | 2 處 | ✅ 完成 |
| **QThread** | QThread 未正確停止 | 1 處 | ✅ 完成 |
| **Traceback Leak** | traceback 持有 frame | 15 處 | ✅ 完成 |
| **Lambda Closure** | lambda 閉包洩漏 | 11 處 | ✅ 完成 |
| **Signal Disconnection** | 信號未斷開 | 1 處 | ✅ 完成 |
| **總計** | - | **30 處** | **✅ 100%** |

---

## 🔧 詳細修復記錄

### **階段 1：Circular Reference（循環引用）** ✅

**問題**：SpeedAnalysisModule ↔ SpeedDataManager 雙向引用

**修復文件**：`speed_analysis_mdi.py`

**修復內容**：
1. **SpeedDataManager.cleanup()**（Line 318）
   ```python
   # 清理對主模組的引用
   if hasattr(self, 'module_ref'):
       self.module_ref = None
   ```

2. **SpeedAnalysisModule.cleanup()**（Line 960）
   ```python
   # 在調用 data_manager.cleanup() 前清理引用
   if self.data_manager:
       self.data_manager.module_ref = None
       self.data_manager.cleanup()
   
   # 最後清理 data_manager 本身
   self.data_manager = None
   ```

**修復日期**：2025-10-15

---

### **階段 2：QThread Crash（執行緒崩潰）** ✅

**問題**："QThread: Destroyed while thread is still running" 導致程式崩潰

**修復文件**：`telemetry_data_loader_base.py`

**修復內容**：完全重寫 `_cleanup_api_worker()` 方法
```python
def _cleanup_api_worker(self):
    if hasattr(self, '_api_worker') and self._api_worker is not None:
        if self._api_worker.isRunning():
            # 1. 請求中斷
            self._api_worker.requestInterruption()
            
            # 2. 停止事件循環
            self._api_worker.quit()
            
            # 3. 等待執行緒結束（5 秒超時）
            if not self._api_worker.wait(5000):
                # 4. 強制終止
                self._api_worker.terminate()
                self._api_worker.wait(1000)
            
            # 5. 確認執行緒已停止才 deleteLater
            if not self._api_worker.isRunning():
                self._api_worker.deleteLater()
            else:
                # 6. 延遲清理
                old_worker = self._api_worker
                old_worker.finished.connect(old_worker.deleteLater)
```

**修復日期**：2025-10-15

---

### **階段 3：Traceback Leak（Traceback 洩漏）** ✅

**問題**：`traceback.print_exc()` 持有 frame，frame 持有局部變量和 bound method

**修復文件**：
- `speed_analysis_mdi.py`：8 處
- `speed_analysis_chart_widget.py`：3 處
- `f1t_gui_main.py`：4 處

**修復模式**：統一替換為註解形式
```python
# 修復前
except Exception as e:
    print(f"[ERROR] 操作失敗: {e}")
    import traceback
    traceback.print_exc()

# 修復後
except Exception as e:
    # 🔴 簡化錯誤日誌避免 traceback 持有 frame（bound method 和實例）
    print(f"[ERROR] 操作失敗: {e}")
    # 調試時可以取消註解：
    # import traceback
    # traceback.print_exc()
```

**修復列表**：

#### **speed_analysis_mdi.py（8 處）**
1. Line 328-330：SpeedDataManager.cleanup()
2. Line 424-426：SpeedAnalysisModule.__init__()
3. Line 473-475：SpeedAnalysisModule._on_data_loaded()
4. Line 594-596：SpeedAnalysisModule.handle_lap_change()
5. Line 669-671：SpeedAnalysisModule.update_parameters()
6. Line 822：SpeedAnalysisModule.update_lap_parameters() (方法 1)
7. Line 851-853：SpeedAnalysisModule._update_window_title()
8. Line 1089：SpeedAnalysisModule.update_lap_parameters() (方法 2)
9. Line 1413-1415：SpeedAnalysisModule.notify_content_update()

#### **speed_analysis_chart_widget.py（3 處）**
1. Line 1524-1526：SpeedChartWidget.update_speed_data()
2. Line 1684-1686：SpeedAnalysisChartWidget.update_lap_parameters()
3. Line 1808-1810：SpeedAnalysisChartWidget.cleanup()

#### **f1t_gui_main.py（4 處）**
1. Line 6828：_initialize_driver_list()
2. Line 7046：on_lap_analysis_window_closed()
3. Line 7125：_trigger_toolbar_status_for_lap_analysis()
4. Line 13272：速度模組創建異常處理

**修復日期**：2025-10-16

---

### **階段 4：Lambda Closure（Lambda 閉包洩漏）** ✅

**問題**：Lambda 捕獲變量形成閉包，持有實例引用

**修復文件**：`f1t_gui_main.py`

**修復內容**：批次替換所有 lambda 為 `functools.partial`

**修復模式**：
```python
# 修復前（Lambda 閉包）
sub_window.window_closed.connect(lambda: self.on_lap_analysis_window_closed(analysis_module))

# 修復後（Partial）
from functools import partial
# 🔴 使用 partial 避免 lambda 閉包洩漏
sub_window.window_closed.connect(
    partial(self.on_lap_analysis_window_closed, analysis_module)
)
```

**批次修復統計**：
- `on_lap_analysis_window_closed(analysis_module)`：5 處
- `on_lap_analysis_window_closed(chart_widget)`：1 處
- `on_subwindow_closed(sub_window)`：5 處
- **總計**：11 處

**批次修復工具**：`fix_lambda_closures.py`

**修復日期**：2025-10-16

---

### **階段 5：Signal Disconnection（信號斷開）** ✅

**問題**：信號連接未斷開，持有 partial 函數和實例引用

**修復文件**：`f1t_gui_main.py`

**修復內容**：在 `on_lap_analysis_window_closed()` 中添加信號斷開邏輯

```python
def on_lap_analysis_window_closed(self, window_object):
    """遙測分析視窗關閉時調用"""
    
    # 🔴 第一步：斷開信號連接，釋放 partial 函數引用
    if hasattr(window_object, '_sub_window'):
        sub_window = window_object._sub_window
        if sub_window and hasattr(sub_window, 'window_closed'):
            try:
                # 斷開所有 window_closed 信號連接
                sub_window.window_closed.disconnect()
                print(f"[LAP_CONTROL] ✅ 已斷開子視窗信號連接")
            except Exception as e:
                print(f"[LAP_CONTROL] ⚠️ 斷開信號連接失敗（可能已斷開）: {e}")
    
    # ... 原有清理邏輯 ...
    
    # 🔴 清理模組對子視窗的引用
    if hasattr(window_object, '_sub_window'):
        window_object._sub_window = None
        sub_window = None
        print(f"[LAP_CONTROL] 🗑️ 已清理模組的子視窗引用")
    
    # 🔴 強制垃圾回收
    import gc
    gc.collect()
    print(f"[LAP_CONTROL] 🗑️ 已執行垃圾回收")
```

**修復日期**：2025-10-16

---

## 🎯 洩漏機制總結

### **1. Circular Reference（循環引用）**

```
SpeedAnalysisModule.data_manager
    ↓
SpeedDataManager.module_ref
    ↓
SpeedAnalysisModule（回到起點）
```

**為什麼洩漏？**
- Python 引用計數無法處理循環引用
- 需要 GC 的循環檢測才能回收
- 如果引用鏈中有強引用，GC 也無法回收

**修復方法**：
- 在 cleanup 中手動斷開循環
- 兩個方向都要清理（A.b = None, B.a = None）

---

### **2. QThread Leak（執行緒洩漏）**

```
SpeedAnalysisDataLoader._api_worker (QThread)
    ↓ isRunning() = True
嘗試 deleteLater()
    ↓
崩潰："Destroyed while thread is still running"
```

**為什麼崩潰？**
- Qt 禁止刪除正在運行的 QThread
- 原始代碼 `wait(200)` 太短
- 沒有調用 `quit()` 停止事件循環
- 沒有 `terminate()` 強制終止

**修復方法**：
- 完整的停止序列：requestInterruption() → quit() → wait(5000) → terminate() → wait(1000)
- 檢查 isRunning() 才 deleteLater()
- 延遲清理作為後備

---

### **3. Traceback Leak（Traceback 洩漏）**

```
traceback 對象
    ↓ tb_frame
frame (異常處理器的執行環境)
    ↓ f_locals['self']
SpeedAnalysisModule 實例
    ↓ (同時)
frame
    ↓ f_locals['update_lap_parameters'] (bound method)
    ↓ method.__self__
SpeedAnalysisModule 實例（雙重引用！）
```

**為什麼洩漏？**
- `traceback.print_exc()` 持有完整的調用堆疊
- frame 持有所有局部變量（包括 `self`）
- bound method 的 `__self__` 屬性持有實例
- 形成雙重引用鏈

**修復方法**：
- 移除所有 `traceback.print_exc()`
- 使用簡潔的錯誤訊息
- 開發時用註解形式保留

---

### **4. Lambda Closure Leak（Lambda 閉包洩漏）**

```
sub_window.window_closed 信號
    ↓ 持有槽函數
lambda: self.on_lap_analysis_window_closed(analysis_module)
    ↓ __closure__[0] (cell 對象)
cell.cell_contents
    ↓
analysis_module (SpeedAnalysisModule 實例)
```

**為什麼洩漏？**
- Lambda 捕獲外部變量形成閉包
- 閉包通過 cell 對象持有變量
- 信號連接持有 lambda 函數
- 即使視窗關閉，lambda 和 cell 仍然存在

**修復方法**：
- 使用 `functools.partial` 替代 lambda
- partial 不使用閉包機制
- 調用 `disconnect()` 斷開信號連接
- 清理 `_sub_window` 引用

---

## ✅ 預期修復效果

### **修復前（多重洩漏）**

```
開啟 Speed Analysis → 載入數據 → 關閉視窗
↓

objgraph 檢查：
┌─────────────────────────────────┐
│ SpeedAnalysisModule: 1 ❌       │
│ SpeedDataManager: 1 ❌          │
│ SpeedAnalysisChartWidget: 1 ❌  │
│ SpeedChartWidget: 1 ❌          │
│ SpeedAnalysisDataLoader: 1 ❌   │
└─────────────────────────────────┘

引用圖顯示：
┌─────────────────────────────────────────────┐
│ frame → frame → frame → bound method        │
│              ↓                               │
│            cell (lambda 閉包)                │
│              ↓                               │
│       SpeedAnalysisModule                   │
│              ↓                               │
│    循環引用：module_ref ↔ data_manager      │
│              ↓                               │
│    QThread 仍在運行                         │
└─────────────────────────────────────────────┘

Force GC：
回收 0 個對象 ❌
```

### **修復後（完全清理）**

```
開啟 Speed Analysis → 載入數據 → 關閉視窗
↓

關閉流程：
1. ✅ 斷開信號連接（釋放 partial 函數）
2. ✅ 調用 module.cleanup()
   - 清理 module_ref 循環引用
   - 停止 QThread（quit + wait + terminate）
   - 調用 data_manager.cleanup()
   - 清理所有引用
3. ✅ 清理 _sub_window 引用
4. ✅ 從 MDI 區域移除子視窗
5. ✅ 強制 gc.collect()

objgraph 檢查：
┌─────────────────────────────────┐
│ SpeedAnalysisModule: 0 ✅       │
│ SpeedDataManager: 0 ✅          │
│ SpeedAnalysisChartWidget: 0 ✅  │
│ SpeedChartWidget: 0 ✅          │
│ SpeedAnalysisDataLoader: 0 ✅   │
└─────────────────────────────────┘

引用圖顯示：
┌─────────────────────────────────┐
│ 無引用鏈 ✅                     │
│ 無 frame 對象 ✅                │
│ 無 cell 對象 ✅                 │
│ 無 bound method 引用 ✅         │
└─────────────────────────────────┘

Force GC：
回收 5+ 個對象 ✅
SpeedAnalysisModule (1)
SpeedDataManager (1)
SpeedAnalysisChartWidget (1)
SpeedChartWidget (1)
SpeedAnalysisDataLoader (1)
```

---

## 🧪 完整測試計劃

### **測試環境準備**

1. **確保代碼已更新**
   ```powershell
   git status
   # 應該顯示修改的文件：
   # - f1t_gui_main.py
   # - speed_analysis_mdi.py
   # - speed_analysis_chart_widget.py
   # - telemetry_data_loader_base.py
   ```

2. **啟動測試**
   ```powershell
   python f1t_gui_main.py
   ```

3. **啟動 Memory Diagnostics**
   - 在 GUI 中開啟記憶體診斷工具
   - 或單獨執行 objgraph 診斷視窗

---

### **測試步驟**

#### **Step 1：基本功能測試**

1. **開啟 Speed Analysis**
   - 選擇年份：2024
   - 選擇賽事：Japan
   - 選擇會話：R
   - 選擇車手：VER vs LEC
   - 選擇圈數：第 1 圈 vs 第 1 圈

2. **載入數據**
   - 點擊 "Load Speed Data"
   - 確認圖表正常顯示
   - 檢查統計表格

3. **測試互動功能**
   - 修改圈數參數
   - 切換車手
   - 使用批次更新（Update All Analysis）
   - 檢查視窗標題更新

4. **關閉視窗**
   - 點擊 X 關閉視窗
   - 觀察終端輸出：
     ```
     [LAP_CONTROL] ✅ 已斷開子視窗信號連接
     [LAP_CONTROL] 📊 圈速分析視窗已關閉: Speed Analysis - 2024 Japan R
     [LAP_CONTROL] 🧹 調用模組清理方法
     [SPEED_MDI] 🧹 開始清理速度分析模組...
     [SPEEDDATAMANAGER] 🧹 開始清理 SpeedDataManager...
     [SPEEDDATAMANAGER] ✅ 資源清理完成
     [SPEED_MDI] ✅ 資源清理完成
     [LAP_CONTROL] ✅ 模組清理成功
     [LAP_CONTROL] 🗑️ 已從 MDI 區域移除子視窗
     [LAP_CONTROL] 🗑️ 已清理模組的子視窗引用
     [LAP_CONTROL] 🗑️ 已執行垃圾回收
     ```

---

#### **Step 2：objgraph 檢查**

1. **檢查組件計數**
   - 在 Memory Diagnostics 中搜索：
     - `SpeedAnalysisModule`
     - `SpeedDataManager`
     - `SpeedAnalysisChartWidget`
     - `SpeedChartWidget`
     - `SpeedAnalysisDataLoader`
   - **預期結果**：所有計數 = 0 ✅

2. **生成引用圖**
   - 如果計數 > 0，生成引用圖
   - **預期結果**：無引用圖（對象已完全釋放）

3. **檢查 frame 和 cell**
   - 搜索 `frame` 類型
   - 搜索 `cell` 類型
   - **預期結果**：無 Speed 模組相關的 frame/cell

---

#### **Step 3：Force GC 驗證**

1. **執行垃圾回收**
   - 點擊 "Force GC" 按鈕
   - 觀察終端輸出

2. **預期輸出**
   ```
   [GC] 🗑️ 執行垃圾回收...
   [GC] 回收了 5 個對象
   [GC] 回收對象類型：
   - SpeedAnalysisModule: 1
   - SpeedDataManager: 1
   - SpeedAnalysisChartWidget: 1
   - SpeedChartWidget: 1
   - SpeedAnalysisDataLoader: 1
   [GC] ✅ 垃圾回收完成
   ```

3. **驗證**
   - 再次檢查 objgraph 計數
   - **應該保持 0** ✅

---

#### **Step 4：重複測試（穩定性）**

重複以下流程 **5 次**：

1. 開啟 Speed Analysis
2. 載入數據（不同車手/圈數組合）
3. 執行互動操作
4. 關閉視窗
5. 檢查 objgraph 計數
6. 執行 Force GC

**預期結果**：
- 所有 5 次測試，計數都歸零 ✅
- 無累積洩漏 ✅
- 無崩潰 ✅

---

#### **Step 5：壓力測試**

1. **快速開關測試**
   - 快速開啟/關閉 Speed Analysis 10 次
   - 不載入數據
   - 檢查是否有視窗殘留

2. **多視窗測試**
   - 同時開啟 3 個 Speed Analysis 視窗
   - 載入不同的數據
   - 逐一關閉
   - 檢查 objgraph 計數

3. **批次更新測試**
   - 開啟多個遙測分析視窗（Speed, RPM, Throttle）
   - 修改 year/race/session
   - 使用批次更新
   - 關閉所有視窗
   - 檢查記憶體

---

### **測試檢查清單**

- [ ] ✅ 基本功能正常（開啟、載入、關閉）
- [ ] ✅ objgraph 計數全部歸零
- [ ] ✅ 無 frame 引用鏈
- [ ] ✅ 無 cell 對象
- [ ] ✅ Force GC 回收 5+ 對象
- [ ] ✅ 重複測試無累積洩漏
- [ ] ✅ 快速開關無殘留
- [ ] ✅ 多視窗測試通過
- [ ] ✅ 批次更新測試通過
- [ ] ✅ 無崩潰或異常

---

## 💡 經驗總結

### **關鍵教訓**

1. **循環引用需要手動清理**
   - Python 引用計數無法處理循環
   - 必須在 cleanup 中雙向清理

2. **QThread 需要完整停止序列**
   - quit() → wait() → terminate()
   - 確認 isRunning() = False 才 deleteLater()

3. **Traceback 是隱形殺手**
   - 持有完整的 frame 鏈
   - Bound method 導致雙重引用
   - 任何實例方法中的 traceback 都會洩漏

4. **Lambda 閉包洩漏**
   - Lambda 捕獲變量形成 cell
   - 信號連接持有 lambda
   - 使用 partial 替代

5. **信號必須斷開**
   - PyQt5 信號使用強引用
   - 對象銷毀前必須 disconnect()
   - 否則槽函數永久存在

6. **objgraph 是唯一可靠的工具**
   - 無法靠代碼審查發現所有洩漏
   - 引用圖顯示完整的洩漏路徑
   - 必須配合 Force GC 測試

---

### **最佳實踐**

#### **禁止模式**

❌ **在實例方法中使用 traceback**
```python
class MyModule:
    def method(self):
        try:
            # ...
        except:
            traceback.print_exc()  # ❌ 洩漏 self
```

❌ **使用 lambda 連接信號**
```python
signal.connect(lambda: self.handler(obj))  # ❌ 閉包洩漏
```

❌ **不斷開信號連接**
```python
obj.signal.connect(slot)
# ... 對象刪除
# 信號仍連接 ❌
```

❌ **循環引用不清理**
```python
a.b = b
b.a = a
# cleanup 中不清理 ❌
```

❌ **QThread wait 時間太短**
```python
thread.wait(200)  # ❌ 太短
thread.deleteLater()  # 可能崩潰
```

#### **推薦模式**

✅ **使用簡潔的錯誤訊息**
```python
except Exception as e:
    print(f"[ERROR] 操作失敗: {e}")
    # 不使用 traceback
```

✅ **使用 partial 連接信號**
```python
from functools import partial
signal.connect(partial(self.handler, obj))
```

✅ **斷開信號連接**
```python
def cleanup(self):
    if hasattr(self, 'signal'):
        self.signal.disconnect()
```

✅ **雙向清理循環引用**
```python
def cleanup(self):
    if self.a:
        self.a.b = None
        self.a = None
    if self.b:
        self.b.a = None
        self.b = None
```

✅ **完整的 QThread 停止序列**
```python
def cleanup_thread(self):
    if self.thread and self.thread.isRunning():
        self.thread.requestInterruption()
        self.thread.quit()
        if not self.thread.wait(5000):
            self.thread.terminate()
            self.thread.wait(1000)
        if not self.thread.isRunning():
            self.thread.deleteLater()
```

---

## 🎯 後續行動

### **立即行動**（當前 session）

1. ⚠️ **執行完整測試**
   - 啟動 F1T GUI
   - 執行測試計劃
   - 驗證所有修復

2. ⚠️ **記錄測試結果**
   - 截圖 objgraph 計數 = 0
   - 截圖 Force GC 回收對象
   - 記錄終端日誌

---

### **短期行動**（本週內）

3. ⚠️ **檢查其他遙測模組**
   - RPM Analysis
   - Throttle Analysis
   - Gear Analysis
   - Brake Analysis
   - Acceleration Analysis
   - 搜索 lambda 和 traceback

4. ⚠️ **統一修復方案**
   - 將修復方案應用到所有模組
   - 建立檢測腳本
   - CI/CD 整合

---

### **中期行動**（本月內）

5. ⚠️ **建立最佳實踐文檔**
   - 記憶體管理指南
   - PyQt5 信號使用規範
   - QThread 使用規範
   - 代碼審查清單

6. ⚠️ **自動化檢測工具**
   - Lambda 閉包檢測
   - Traceback 檢測
   - 循環引用檢測
   - QThread 檢測

---

### **長期行動**（下個月）

7. ⚠️ **重構基礎架構**
   - 統一的信號管理機制
   - 統一的 cleanup 模式
   - 統一的錯誤處理

8. ⚠️ **記憶體監控系統**
   - 運行時記憶體追蹤
   - 自動洩漏檢測
   - 警報機制

---

## 📚 參考文件

### **生成的修復報告**

1. `SPEED_MODULE_CIRCULAR_REFERENCE_FIX.md` - 循環引用修復
2. `QTHREAD_CRASH_FIX_REPORT.md` - QThread 崩潰修復
3. `FRAME_REFERENCE_LEAK_FIX_REPORT.md` - Frame 引用洩漏修復
4. `REFERENCE_CHAIN_DEEP_ANALYSIS.md` - 引用鏈深度分析
5. `SPEED_MODULE_INTERNAL_LEAK_ANALYSIS.md` - 模組內部洩漏分析
6. `SPEED_MODULE_TRACEBACK_COMPLETE_FIX.md` - Traceback 完整修復
7. `LAMBDA_CLOSURE_LEAK_ANALYSIS.md` - Lambda 閉包洩漏分析
8. `SPEED_MODULE_COMPLETE_FIX_REPORT.md` - **本報告（總結）**

### **修復工具**

1. `fix_lambda_closures.py` - Lambda 批次修復腳本

---

**報告結束**

修復人員：AI Assistant  
審核人員：待確認  
測試狀態：✅ 代碼修復完成，⚠️ 待測試驗證  
優先級：🔴 最高

**最終修復進度**：30/30 處（100%） ✅  
**建議**：立即執行完整測試計劃，驗證所有修復效果

---

**✨ Speed 模組記憶體洩漏修復完成！請執行測試驗證。**
