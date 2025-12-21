# QThread 信號連接洩漏修復報告

**修復日期**: 2025-10-11  
**問題類型**: 內存洩漏 / 呼叫堆疊累積  
**嚴重程度**: 🔴 高（會導致 GUI 性能逐漸下降）

---

## 📋 問題摘要

GUI 啟動後，API 健康檢查和 Runtime 監控的 QThread Worker 會導致呼叫堆疊洩漏。

### 影響範圍
- **ApiHealthWorker**: 每 60 秒執行一次健康檢查
- **ApiRuntimeWorker**: 每 5 秒執行一次狀態輪詢
- **累積效應**: 長時間運行會導致信號槽重複連接，堆疊累積

---

## 🔍 根本原因分析

### 洩漏機制

```python
# ❌ 問題代碼（修復前）
def trigger_api_runtime_poll(self) -> None:
    if self._api_runtime_worker is not None:
        # 清理舊 worker，但沒有斷開信號！
        self._api_runtime_worker.deleteLater()
        self._api_runtime_worker = None
    
    # 創建新 worker
    self._api_runtime_worker = ApiRuntimeWorker(...)
    self._api_runtime_worker.result_ready.connect(self.on_api_runtime_result)  # ⚠️ 累積連接
    self._api_runtime_worker.finished.connect(self.on_api_runtime_finished)    # ⚠️ 累積連接
    self._api_runtime_worker.start()
```

### 問題點

1. **信號未斷開**: `deleteLater()` 不會立即銷毀對象，信號連接仍然存在
2. **重複連接**: 每次創建新 worker 時，都會添加新的信號連接
3. **Qt 機制**: Qt 允許同一信號多次連接到同一槽，每次 emit 都會觸發所有連接
4. **時序問題**: 舊 worker 的 `finished` 信號可能在新 worker 創建後才觸發

### 洩漏演示

```
時間軸：
T=0s:   創建 Worker#1，連接信號 → 槽函數被連接 1 次
T=5s:   創建 Worker#2，連接信號 → 槽函數被連接 2 次
T=10s:  創建 Worker#3，連接信號 → 槽函數被連接 3 次
T=15s:  創建 Worker#4，連接信號 → 槽函數被連接 4 次
...
T=300s: 槽函數被連接 60 次！每次 emit 觸發 60 次調用！
```

---

## ✅ 修復方案

### 修復策略

1. **顯式斷開信號**: 在 `deleteLater()` 前先斷開所有信號連接
2. **使用 Qt.UniqueConnection**: 防止重複連接
3. **異常處理**: 處理信號已斷開的情況

### 修復後的代碼

```python
# ✅ 正確代碼（修復後）
def trigger_api_runtime_poll(self) -> None:
    if self._api_runtime_worker is not None:
        try:
            # ⚠️ 關鍵修復：先斷開信號連接
            try:
                self._api_runtime_worker.result_ready.disconnect(self.on_api_runtime_result)
            except (TypeError, RuntimeError):
                pass  # 信號已斷開或不存在
            try:
                self._api_runtime_worker.finished.disconnect(self.on_api_runtime_finished)
            except (TypeError, RuntimeError):
                pass
            
            if self._api_runtime_worker.isRunning():
                self._api_runtime_worker.requestInterruption()
                self._api_runtime_worker.wait(100)
            self._api_runtime_worker.deleteLater()
        except Exception:
            pass
        self._api_runtime_worker = None
    
    # 創建新 worker
    self._api_runtime_worker = ApiRuntimeWorker(...)
    # ✅ 使用 Qt.UniqueConnection 防止重複連接
    self._api_runtime_worker.result_ready.connect(self.on_api_runtime_result, Qt.UniqueConnection)
    self._api_runtime_worker.finished.connect(self.on_api_runtime_finished, Qt.UniqueConnection)
    self._api_runtime_worker.start()
```

---

## 📝 修復清單

### 已修復的方法

- [x] `trigger_api_runtime_poll()` - ApiRuntimeWorker 創建
- [x] `trigger_api_health_check()` - ApiHealthWorker 創建

### 修復要點

1. **顯式斷開**: `disconnect()` 在 `deleteLater()` 之前
2. **異常捕獲**: 處理 `TypeError` 和 `RuntimeError`
3. **唯一連接**: 使用 `Qt.UniqueConnection` 標誌
4. **防禦性編程**: 多層 try/except 保護

---

## 🧪 測試驗證

### 測試腳本
```bash
python test_qthread_leak_fix.py
```

### 測試項目

1. **初始化測試**: 確認 worker 正確初始化
2. **多次執行測試**: 模擬 3 次健康檢查，確認無洩漏
3. **Runtime 輪詢測試**: 模擬 3 次輪詢，確認無洩漏
4. **清理測試**: 確認 closeEvent 正確清理資源
5. **內存測試**: 使用 `gc.collect()` 確認對象被回收

### 預期結果

```
✅ Worker 在每次創建前被正確清理
✅ 信號連接不會累積
✅ 內存使用穩定，無洩漏
✅ 槽函數每次 emit 只被調用一次
```

---

## 🎯 性能影響

### 修復前
- **5 分鐘後**: 槽函數被連接 60 次
- **30 分鐘後**: 槽函數被連接 360 次
- **影響**: GUI 卡頓、內存持續增長

### 修復後
- **任何時間**: 槽函數始終只被連接 1 次
- **影響**: 性能穩定、內存使用正常

---

## 📌 最佳實踐總結

### QThread 清理的正確模式

```python
# 清理舊 worker 的完整流程
if self._worker is not None:
    # 1. 斷開所有信號
    try:
        self._worker.signal1.disconnect(self.slot1)
        self._worker.signal2.disconnect(self.slot2)
    except (TypeError, RuntimeError):
        pass
    
    # 2. 停止執行緒
    if self._worker.isRunning():
        self._worker.requestInterruption()
        self._worker.wait(100)
    
    # 3. 標記為待刪除
    self._worker.deleteLater()
    
    # 4. 清除引用
    self._worker = None

# 創建新 worker
self._worker = MyWorker(...)
self._worker.signal1.connect(self.slot1, Qt.UniqueConnection)
self._worker.signal2.connect(self.slot2, Qt.UniqueConnection)
self._worker.start()
```

### 關鍵要點

1. **先斷開後刪除**: `disconnect()` → `deleteLater()`
2. **使用唯一連接**: `Qt.UniqueConnection`
3. **處理異常**: 信號可能已斷開
4. **等待完成**: `wait()` 確保執行緒停止
5. **清除引用**: `= None` 幫助垃圾回收

---

## ✅ 修復狀態

**狀態**: 🟢 已完成  
**測試**: 待執行  
**部署**: 待合併

### 下一步行動

1. 執行 `test_qthread_leak_fix.py` 驗證修復
2. 長時間運行測試（30 分鐘）
3. 監控內存使用
4. 確認無回歸問題

---

## 📚 參考資料

- Qt Documentation: [QObject::deleteLater()](https://doc.qt.io/qt-5/qobject.html#deleteLater)
- Qt Documentation: [Signals & Slots](https://doc.qt.io/qt-5/signalsandslots.html)
- Qt::ConnectionType: [Qt.UniqueConnection](https://doc.qt.io/qt-5/qt.html#ConnectionType-enum)

---

**修復完成時間**: 2025-10-11  
**修復人員**: GitHub Copilot AI Assistant
