# 🔧 Throttle Box Plot GUI 崩潰修復報告

**修復日期**: 2025-10-17  
**錯誤訊息**: `QThread: Destroyed while thread is still running`  
**修復方法**: 完全複製 throttle_line_chart 和 accident 的成功模式

---

## **問題根源**

錯誤訊息 `QThread: Destroyed while thread is still running` 表示 QThread 在還在運行時就被銷毀了。

**之前的錯誤嘗試**：
1. ❌ 嘗試使用 `worker.wait(200)` → 導致主執行緒阻塞
2. ❌ 嘗試在 `deleteLater()` 後不設置 `= None` → 導致下次調用時 Worker 仍存在
3. ❌ 嘗試創建 `_on_worker_finished()` 專用處理 → 過度複雜化

---

## **正確的解決方案：複製成功模式**

### **參考模組**
- ✅ **throttle_line_chart** (`throttle_line_chart_data_loader.py`)
- ✅ **accident** (`accident_data_manager.py`)

這兩個模組都能正常運行，且都使用相同的 Worker 清理模式。

### **成功模式的代碼**

#### **1. _cleanup_api_worker() - 簡單直接**

```python
def _cleanup_api_worker(self) -> None:
    """清理 API Worker 執行緒"""
    if self._api_worker:
        try:
            self._api_worker.progress.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.success.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.failure.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.finished.disconnect()
        except Exception:
            pass
        self._api_worker.deleteLater()
        self._api_worker = None  # ✅ 直接設置 None
```

**關鍵點**：
- ✅ 斷開所有信號連接
- ✅ 調用 `deleteLater()`
- ✅ **立即設置 `= None`**（不等待，不檢查 isRunning()）

#### **2. _start_api_request() - 直接清理舊 Worker**

```python
def _start_api_request(self, params: Dict[str, Any]) -> None:
    """啟動 API 請求背景執行緒"""
    self._cleanup_api_worker()  # ✅ 直接清理，不檢查狀態

    worker_params = { ... }
    
    self._api_worker = ThrottleBoxPlotApiWorker(...)
    self._api_worker.progress.connect(self._on_api_progress)
    self._api_worker.success.connect(self._on_api_success)
    self._api_worker.failure.connect(self._on_api_error)
    self._api_worker.finished.connect(self._cleanup_api_worker)  # ✅ 自動清理
    self._api_worker.start()
```

**關鍵點**：
- ✅ 開始前直接調用 `_cleanup_api_worker()`
- ✅ 不檢查 `isRunning()`
- ✅ `finished` 信號連接到 `_cleanup_api_worker`（自動清理）

---

## **為什麼這個模式能成功？**

### **Qt 的 deleteLater() 機制**

1. **延遲刪除**：`deleteLater()` 不會立即刪除物件，而是在事件循環中安全刪除
2. **執行緒安全**：即使執行緒仍在運行，Qt 也會等待適當時機刪除
3. **引用清空**：設置 `= None` 只是清空 Python 引用，不影響 Qt 的刪除機制

### **finished 信號的作用**

當 Worker 完成時：
1. `finished` 信號被發射
2. `_cleanup_api_worker()` 被調用
3. 斷開所有信號連接（防止重複處理）
4. `deleteLater()` 標記為待刪除
5. 設置 `= None` 清空 Python 引用

**重點**：整個流程是異步的，Qt 會在安全時機刪除物件。

---

## **修復的具體變更**

### **檔案**: `throttle_box_plot_analysis_mdi.py`

#### **變更 1: 簡化 _cleanup_api_worker()**

**修復前**（過度複雜）:
```python
def _cleanup_api_worker(self) -> None:
    if self._api_worker:
        if self._api_worker.isRunning():
            self._api_worker.requestInterruption()
        # ... 斷開信號 ...
        self._api_worker.deleteLater()
        # 🔴 不設置 = None（錯誤！）
```

**修復後**（完全複製成功模式）:
```python
def _cleanup_api_worker(self) -> None:
    if self._api_worker:
        try:
            self._api_worker.progress.disconnect()
        except Exception:
            pass
        # ... 其他 disconnect ...
        self._api_worker.deleteLater()
        self._api_worker = None  # ✅ 直接設置 None
```

#### **變更 2: 簡化 _start_api_request()**

**修復前**（檢查 isRunning()）:
```python
def _start_api_request(self, params: Dict[str, Any]) -> None:
    if self._api_worker:
        if not self._api_worker.isRunning():
            self._cleanup_api_worker()
            self._api_worker = None
        else:
            return  # 跳過請求
    # ... 創建新 Worker ...
```

**修復後**（直接清理）:
```python
def _start_api_request(self, params: Dict[str, Any]) -> None:
    self._cleanup_api_worker()  # ✅ 直接清理
    # ... 創建新 Worker ...
```

---

## **測試驗證**

### **測試步驟**

```powershell
# 啟動 GUI
python f1t_gui_main.py

# 測試操作：
# 1. 打開 Throttle Box Plot
# 2. 檢查是否正常載入
# 3. 更新參數（year/race/session）
# 4. 連續更新多次
# 5. 關閉視窗
# 6. 重複打開/關閉
```

### **預期結果**

- ✅ GUI 正常啟動，無崩潰
- ✅ Throttle Box Plot 正常打開
- ✅ 數據正常載入
- ✅ 參數更新無死鎖
- ✅ 關閉視窗無錯誤訊息
- ✅ 無 `QThread: Destroyed while thread is still running` 錯誤

---

## **經驗教訓**

### **應該做的**
1. ✅ **先檢查成功的參考實現**（throttle_line_chart, accident）
2. ✅ **完全複製成功模式**（不要自創複雜邏輯）
3. ✅ **保持簡單**（越簡單越不容易出錯）

### **不應該做的**
1. ❌ 不要過度複雜化（如創建專用的 finished 處理方法）
2. ❌ 不要假設 Qt 的行為（如假設需要等待執行緒停止）
3. ❌ 不要自創解決方案（當已有成功範例時）

---

## **相關檔案**

- ✅ **已修復**: `modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py`
- 📚 **參考**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_data_loader.py`
- 📚 **參考**: `modules/gui/accident_analysis/accident_data_manager.py`

---

**修復狀態**: ✅ 已完成  
**測試狀態**: ⏳ 等待用戶測試確認  
**修復方法**: 完全複製成功模式（throttle_line_chart + accident）
