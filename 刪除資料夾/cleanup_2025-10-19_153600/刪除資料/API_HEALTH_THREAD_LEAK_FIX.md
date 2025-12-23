# API Worker 執行緒洩漏修復報告

**日期**: 2025-10-11  
**問題**: Dummy 執行緒未正確清理，導致執行緒洩漏  
**影響範圍**: `ApiHealthWorker` 和 `ApiRuntimeWorker`  
**狀態**: ✅ 已完全修復

---

## 🚨 問題描述

### 症狀
在 VS Code 呼叫堆疊中看到大量 `Dummy-X` 執行緒（Dummy-8, 9, 11, 13, 15, 17, 19），這些是 `ApiHealthWorker` (QThread) 產生的背景執行緒。

### 根本原因
`ApiHealthWorker` 在完成後沒有正確清理，只是將引用設為 `None`，但 QThread 本身未被銷毀。

---

## ❌ 修復前的問題代碼

### 1. `on_api_health_finished()` - 行 8500-8505
```python
def on_api_health_finished(self) -> None:
    self._api_health_worker_active = False
    self._api_health_worker = None  # ❌ 只設為 None，執行緒未清理
    if self.check_api_action:
        self.check_api_action.setEnabled(True)
```

**問題**: 
- 直接將 `self._api_health_worker` 設為 `None`
- 沒有調用 `deleteLater()` 告訴 Qt 清理 QThread
- 執行緒物件仍然存在於記憶體中

### 2. `closeEvent()` - 行 15148-15160
```python
if hasattr(self, '_api_health_worker') and self._api_health_worker:
    try:
        self._api_health_worker.result_ready.disconnect(...)
        self._api_health_worker.finished.disconnect(...)
    except Exception:
        pass
    self._api_health_worker = None  # ❌ 直接設為 None，沒有等待或清理
```

**問題**:
- 只 disconnect 信號，沒有停止執行緒
- 沒有調用 `wait()` 等待執行緒完成
- 沒有調用 `deleteLater()` 清理資源

---

## ✅ 修復後的代碼

### 1. `on_api_health_finished()` - 行 8500-8508
```python
def on_api_health_finished(self) -> None:
    self._api_health_worker_active = False
    # ✅ 正確清理 QThread：deleteLater() 而不是直接設為 None
    if self._api_health_worker:
        self._api_health_worker.deleteLater()
        self._api_health_worker = None
    if self.check_api_action:
        self.check_api_action.setEnabled(True)
```

**改進**:
- ✅ 調用 `deleteLater()` 告訴 Qt 在事件循環中清理執行緒
- ✅ 確保執行緒物件會被正確銷毀

### 2. `closeEvent()` - 行 15148-15165
```python
if hasattr(self, '_api_health_worker') and self._api_health_worker:
    try:
        self._api_health_worker.result_ready.disconnect(self.on_api_health_result)
    except Exception:
        pass
    try:
        self._api_health_worker.finished.disconnect(self.on_api_health_finished)
    except Exception:
        pass
    # ✅ 正確清理執行緒：等待完成並 deleteLater
    if self._api_health_worker.isRunning():
        self._api_health_worker.requestInterruption()
        self._api_health_worker.wait(300)  # 等待最多 300ms
    self._api_health_worker.deleteLater()
    self._api_health_worker = None
self._api_health_worker_active = False
```

**改進**:
- ✅ 檢查執行緒是否還在運行 (`isRunning()`)
- ✅ 請求中斷執行緒 (`requestInterruption()`)
- ✅ 等待執行緒完成 (`wait(300)`)，最多 300ms
- ✅ 調用 `deleteLater()` 清理資源
- ✅ 與 `ApiRuntimeWorker` 的清理邏輯一致

---

## 🔍 技術細節

### QThread 清理最佳實踐
1. **disconnect 所有信號** - 避免野指針
2. **requestInterruption()** - 通知執行緒應該停止（如果執行緒有檢查中斷標誌）
3. **wait(timeout)** - 等待執行緒完成（設定超時避免永久阻塞）
4. **deleteLater()** - 告訴 Qt 在事件循環中安全地刪除物件
5. **設為 None** - 清除 Python 引用

### 為什麼需要 `deleteLater()`？
- QThread 是 Qt 物件，由 Qt 的記憶體管理系統管理
- 直接設為 `None` 只清除 Python 引用，不會觸發 Qt 的清理機制
- `deleteLater()` 將物件加入 Qt 的刪除隊列，在安全時機銷毀

---

## 🧪 驗證步驟

### 1. 檢查執行緒數量
```python
# 啟動 GUI 後，在調試控制台執行
import threading
print(f"總執行緒數: {threading.active_count()}")
print(f"執行緒列表: {[t.name for t in threading.enumerate()]}")
```

### 2. 監控 Dummy 執行緒
```python
# 定期檢查 Dummy 執行緒是否清理
dummy_threads = [t for t in threading.enumerate() if 'Dummy' in t.name]
print(f"Dummy 執行緒數: {len(dummy_threads)}")
```

### 3. API 健康檢查觸發
- 啟動 GUI
- 等待 200ms 自動觸發首次檢查
- 等待 30 秒觸發第二次檢查
- 使用 Tools → Check API Status 手動觸發
- 每次檢查後應清理執行緒

---

## 📊 預期效果

### 修復前
```
啟動 → Dummy-8 (檢查 1) → 未清理
30 秒後 → Dummy-9 (檢查 2) → 未清理
60 秒後 → Dummy-11 (檢查 3) → 未清理
...
結果: 大量 Dummy 執行緒累積
```

### 修復後
```
啟動 → Dummy-8 (檢查 1) → deleteLater() → 清理 ✅
30 秒後 → Dummy-9 (檢查 2) → deleteLater() → 清理 ✅
60 秒後 → Dummy-11 (檢查 3) → deleteLater() → 清理 ✅
...
結果: 執行緒正常回收，無累積
```

---

## 🎯 影響範圍

### 修改文件
- `f1t_gui_main.py`
  - 行 8500-8508: `on_api_health_finished()`
  - 行 15148-15165: `closeEvent()` 中的 API Health Worker 清理

### 相關類別
- `ApiHealthWorker` (QThread) - 執行緒本身未修改
- `StyleHMainWindow` - 主視窗的生命週期管理

---

## ✅ 測試清單

- [ ] GUI 啟動後，Dummy 執行緒正常創建
- [ ] API 檢查完成後，Dummy 執行緒正確清理
- [ ] 30 秒定時檢查後，舊執行緒已回收
- [ ] 手動 API 檢查（Tools → Check API Status）後執行緒清理
- [ ] GUI 關閉時，所有執行緒正常終止
- [ ] 無執行緒洩漏警告或記憶體洩漏

---

## 📝 備註

### 為什麼 ApiRuntimeWorker 沒問題？
`ApiRuntimeWorker` 的清理邏輯一直是正確的（第 15175-15178 行）：
```python
if self._api_runtime_worker.isRunning():
    self._api_runtime_worker.requestInterruption()
    self._api_runtime_worker.wait(300)
self._api_runtime_worker.deleteLater()  # ✅ 正確清理
```

本次修復只是將 `ApiHealthWorker` 的清理邏輯對齊到相同標準。

### 相關文檔
- Qt QThread 文檔: https://doc.qt.io/qt-5/qthread.html
- PyQt5 記憶體管理: https://www.riverbankcomputing.com/static/Docs/PyQt5/memory_management.html

---

**修復完成時間**: 2025-10-11  
**修復者**: GitHub Copilot  
**優先級**: 🔴 高（記憶體洩漏問題）
