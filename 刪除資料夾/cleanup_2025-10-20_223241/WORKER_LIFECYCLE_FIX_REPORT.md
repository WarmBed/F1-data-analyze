# 🔧 批量開啟模組時的 Worker 生命週期競爭條件修復報告

**日期**: 2025-10-20  
**問題**: `RuntimeError: wrapped C/C++ object has been deleted`  
**觸發場景**: 批量快速開啟/關閉 GUI 模組  
**影響範圍**: 8 個使用延遲 QTimer 的分析模組

---

## 📊 問題分析

### 錯誤訊息
```python
RuntimeError: wrapped C/C++ object of type IdealLapSectorHeatmapApiWorker has been deleted
  File "ideal_lap_sector_heatmap_mdi.py", line 516, in force_terminate
    if worker and worker.isRunning():
```

### 競爭條件時序圖

```
時間軸    用戶操作                Qt 事件                     問題
─────────────────────────────────────────────────────────────────
T+0ms    開啟模組 A            創建 Worker A
         開啟模組 B            創建 Worker B  
         開啟模組 C            創建 Worker C

T+100ms  快速關閉所有模組      調用 _stop_api_worker()
                              → Worker.quit()
                              → QTimer.singleShot(3000, force_terminate)
                              → Worker.deleteLater()

T+150ms                        Worker A 正常停止
                              → 觸發 finished 信號
                              → 調用 Worker.deleteLater()  
                              → Qt 刪除 C++ 物件 ✅

T+3100ms                       QTimer 觸發 force_terminate()
                              → 訪問 worker.isRunning()
                              → ❌ RuntimeError! (C++ 物件已刪除)
```

### 根本原因

**閉包捕獲已刪除物件的引用**：
```python
def force_terminate():
    if worker and worker.isRunning():  # ❌ worker 是閉包變量
        worker.terminate()

QTimer.singleShot(3000, force_terminate)
# 3 秒後，worker 的 C++ 物件可能已被 Qt 刪除
# 但 Python 閉包仍持有引用
```

---

## ✅ 修復方案

### 方案：添加 RuntimeError 保護

在所有 `force_terminate()` 閉包中添加 try-except 保護：

```python
def force_terminate():
    # ✅ 安全檢查：確保 worker 仍然有效且未被刪除
    try:
        if worker and worker.isRunning():
            print("[WARNING] API Worker 未在 3 秒內停止，強制終止")
            worker.terminate()
    except (RuntimeError, AttributeError):
        # Worker 已被刪除，無需處理
        pass

QTimer.singleShot(3000, force_terminate)
```

**為什麼有效**：
- ✅ 捕獲 `RuntimeError: wrapped C/C++ object has been deleted`
- ✅ 捕獲 `AttributeError`（Python 物件已刪除）
- ✅ 靜默失敗（Worker 已清理，無需終止）
- ✅ 不影響正常流程（Worker 仍在運行時正常終止）

---

## 📝 已修復的模組

### 修復清單（8 個模組，共 10 處修復）

| # | 模組路徑 | 行數 | 超時時間 | 狀態 |
|---|---------|------|---------|------|
| 1 | `modules/gui/ideal_lap_analysis/ideal_lap_sector_heatmap/ideal_lap_sector_heatmap_mdi.py` | 515-522 | 3000ms | ✅ |
| 2 | `modules/gui/rain_analysis/rain_analysis_mdi.py` | 387-394 | 200ms | ✅ |
| 3 | `modules/gui/pitstop_analysis/pitstop_analysis_mdi.py` | 221-228 | 1000ms | ✅ |
| 4 | `modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py` | 490-497 | 200ms | ✅ |
| 5 | `modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py` | 470-477 | 200ms | ✅ |
| 6 | `modules/gui/tire_analysis/tire_analysis_mdi.py` | 381-388 | 200ms | ✅ |
| 7 | `modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py` | 505-513 | 2000ms | ✅ |
| 8 | `modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py` | 595-603 | 2000ms | ✅ (CLI Worker) |
| 9 | `modules/gui/telemetry_analysis_mdi.py` | 302-310 | 1000ms | ✅ |

**注意**: `track_analysis_mdi.py` 已使用弱引用模式，無需修復

---

## 🧪 測試驗證

### 測試場景

1. **單模組正常開關**：✅ 通過
2. **批量快速開啟 5+ 模組**：✅ 通過（修復前會崩潰）
3. **快速開啟後立即全部關閉**：✅ 通過
4. **延遲 QTimer 觸發時 Worker 已刪除**：✅ 安全捕獲

### 預期行為

**修復前**：
```
RuntimeError: wrapped C/C++ object of type XXXApiWorker has been deleted
  File "xxx_mdi.py", line XXX, in force_terminate
    if worker and worker.isRunning():
```

**修復後**：
```
# 靜默處理，無錯誤輸出
# 或日誌：[DEBUG] Worker 已清理，跳過延遲終止
```

---

## 🎯 最佳實踐建議

### 1. **使用 try-except 保護所有延遲回調**

```python
# ✅ 正確
def delayed_callback():
    try:
        if obj and obj.isValid():
            obj.someMethod()
    except (RuntimeError, AttributeError):
        pass

# ❌ 錯誤
def delayed_callback():
    if obj and obj.isValid():  # 可能觸發 RuntimeError
        obj.someMethod()
```

### 2. **使用 QPointer（推薦用於複雜場景）**

```python
from PyQt5.QtCore import QPointer

worker = MyWorker()
worker_ptr = QPointer(worker)

def force_terminate():
    if not worker_ptr.isNull() and worker_ptr.isRunning():
        worker_ptr.terminate()
```

### 3. **使用弱引用（Python 物件）**

```python
import weakref

worker = MyWorker()
worker_ref = weakref.ref(worker)

def force_terminate():
    w = worker_ref()
    if w is not None and w.isRunning():
        w.terminate()
```

---

## 📚 相關文檔

- Qt 文檔: [QObject Lifecycle](https://doc.qt.io/qt-5/objecttrees.html)
- PyQt5 文檔: [QThread Best Practices](https://doc.qt.io/qt-5/qthread.html)
- 專案政策: [API-ONLY 模式](/.github/copilot-instructions.md#4-api-only-模式政策)

---

## ✅ 修復確認

- [x] 識別所有受影響的模組
- [x] 添加 RuntimeError/AttributeError 保護
- [x] 保持原有邏輯不變
- [x] 無破壞性變更
- [x] 通過批量開啟測試
- [x] 更新文檔

**修復完成時間**: 2025-10-20  
**測試通過**: ✅  
**可合併**: ✅
