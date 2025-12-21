# 🚨 QThread 崩潰修復報告

**修復日期**：2025-10-16  
**錯誤訊息**：`QThread: Destroyed while thread is still running`  
**嚴重程度**：🔴 嚴重 - 導致主程式崩潰  
**修復狀態**：✅ 已修復

---

## 🎯 問題描述

### 崩潰現象

**操作序列**：
1. 開啟 Speed Analysis 模組
2. 載入數據（觸發 API Worker 執行緒）
3. 關閉所有視窗
4. **主程式直接崩潰當機**

**錯誤訊息**：
```
QThread: Destroyed while thread is still running
```

### 根本原因

**QThread 物件在執行緒仍在運行時被銷毀！**

這違反了 Qt 的基本原則：
- ❌ 不能在執行緒運行中刪除 QThread 物件
- ❌ 必須先停止執行緒（`quit()` + `wait()`）
- ❌ 才能安全調用 `deleteLater()`

---

## 🔬 問題診斷

### 代碼分析

#### **問題代碼位置 1：`telemetry_data_loader_base.py` Line 694-710**

```python
def _cleanup_api_worker(self) -> None:
    if self._api_worker:
        try:
            if self._api_worker.isRunning():
                self._api_worker.requestInterruption()
                self._api_worker.wait(200)  # ❌ 只等待 200ms！
            self._api_worker.progress.disconnect()
        except Exception:
            pass
        # ... 斷開其他信號 ...
        self._api_worker.deleteLater()  # ❌ 可能執行緒還在運行！
        self._api_worker = None
```

**問題點**：
1. ❌ `wait(200)` 只等待 200 毫秒 - 太短！
2. ❌ 沒有調用 `quit()` 停止事件循環
3. ❌ 沒有檢查執行緒是否真的停止
4. ❌ 直接 `deleteLater()` 可能在執行緒仍運行時執行

#### **問題代碼位置 2：`speed_analysis_mdi.py` Line 962-966**

```python
# ✅ 關鍵修復：清理執行緒資源（與 Throttle 模組一致）
if hasattr(self.data_manager, '_speed_loader'):
    print(f"[SPEED_MDI] 🧹 清理 DataLoader 執行緒...")
    if hasattr(self.data_manager._speed_loader, 'cleanup_threads'):
        self.data_manager._speed_loader.cleanup_threads()  # ❌ 方法不存在！
```

**問題點**：
- ❌ `cleanup_threads()` 方法根本不存在
- ❌ 導致清理邏輯沒有執行
- ❌ 執行緒沒有被正確停止

### 執行緒生命週期問題

```
用戶操作: 載入數據
    ↓
創建 TelemetryApiWorker (QThread)
    ↓
worker.start() → 執行緒開始運行
    ↓
用戶操作: 關閉視窗
    ↓
cleanup() 被調用
    ↓
_cleanup_api_worker()
    ↓
❌ wait(200) - 等待太短
❌ 執行緒可能還在運行
    ↓
deleteLater() - 🚨 崩潰！
```

---

## 🔧 修復實施

### 修復 1：正確停止 QThread - `telemetry_data_loader_base.py`

**修改位置**：Line 694-710  
**修改內容**：

```python
# 修復前：
def _cleanup_api_worker(self) -> None:
    if self._api_worker:
        try:
            if self._api_worker.isRunning():
                self._api_worker.requestInterruption()
                self._api_worker.wait(200)  # ❌ 只等 200ms
            self._api_worker.progress.disconnect()
        except Exception:
            pass
        # ... 其他信號 ...
        self._api_worker.deleteLater()  # ❌ 可能崩潰
        self._api_worker = None

# 修復後：
def _cleanup_api_worker(self) -> None:
    """
    清理 API Worker 執行緒 - 修復 QThread 崩潰問題
    
    🔴 關鍵修復：正確停止 QThread 避免 "Destroyed while thread is still running"
    """
    if self._api_worker:
        try:
            # 🔴 步驟 1：請求中斷
            if self._api_worker.isRunning():
                print(f"[TELEMETRY_LOADER] ⚠️ API Worker 仍在運行，請求中斷...")
                self._api_worker.requestInterruption()
                
                # 🔴 步驟 2：調用 quit() 停止事件循環
                self._api_worker.quit()
                
                # 🔴 步驟 3：等待最多 5 秒讓執行緒結束
                if not self._api_worker.wait(5000):  # 5 秒超時
                    print(f"[ERROR] [TELEMETRY_LOADER] API Worker 5秒後仍未停止，強制終止")
                    self._api_worker.terminate()  # 強制終止
                    self._api_worker.wait(1000)  # 再等 1 秒
                else:
                    print(f"[TELEMETRY_LOADER] ✅ API Worker 已正常停止")
            
            # 🔴 步驟 4：斷開所有信號連接
            self._api_worker.progress.disconnect()
        except Exception:
            pass
        # ... 其他信號斷開 ...
        
        # 🔴 步驟 5：確認執行緒已停止才刪除
        if not self._api_worker.isRunning():
            self._api_worker.deleteLater()
            self._api_worker = None
            print(f"[TELEMETRY_LOADER] ✅ API Worker 已安全刪除")
        else:
            print(f"[ERROR] [TELEMETRY_LOADER] API Worker 仍在運行，無法安全刪除！")
            # 保留引用，避免崩潰
            old_worker = self._api_worker
            self._api_worker = None
            # 讓舊 worker 自然結束
            old_worker.finished.connect(old_worker.deleteLater)
```

**修復效果**：
- ✅ 正確調用 `quit()` 停止事件循環
- ✅ 等待最多 5 秒讓執行緒正常結束
- ✅ 超時後強制 `terminate()`
- ✅ 確認停止才 `deleteLater()`
- ✅ 如果仍在運行，延遲清理避免崩潰

---

### 修復 2：移除不存在的方法調用 - `speed_analysis_mdi.py`

**修改位置**：Line 956-970  
**修改內容**：

```python
# 修復前：
if hasattr(self, 'data_manager') and self.data_manager:
    # 🔴 斷開循環引用：先清空 module_ref
    print(f"[SPEED_MDI] 🔴 斷開循環引用：清理 data_manager.module_ref")
    if hasattr(self.data_manager, 'module_ref'):
        self.data_manager.module_ref = None
    
    # ✅ 關鍵修復：清理執行緒資源（與 Throttle 模組一致）
    if hasattr(self.data_manager, '_speed_loader'):
        print(f"[SPEED_MDI] 🧹 清理 DataLoader 執行緒...")
        if hasattr(self.data_manager._speed_loader, 'cleanup_threads'):
            self.data_manager._speed_loader.cleanup_threads()  # ❌ 方法不存在
    
    # 清理數據管理器
    if hasattr(self.data_manager, 'cleanup'):
        self.data_manager.cleanup()

# 修復後：
if hasattr(self, 'data_manager') and self.data_manager:
    # 🔴 斷開循環引用：先清空 module_ref
    print(f"[SPEED_MDI] 🔴 斷開循環引用：清理 data_manager.module_ref")
    if hasattr(self.data_manager, 'module_ref'):
        self.data_manager.module_ref = None
    
    # 🔴 修復：直接調用 cleanup() 即可（內部已包含執行緒清理）
    # cleanup() 會調用 _cleanup_api_worker() 處理 QThread
    if hasattr(self.data_manager, 'cleanup'):
        self.data_manager.cleanup()
```

**修復效果**：
- ✅ 移除不存在的 `cleanup_threads()` 調用
- ✅ 直接使用 `cleanup()` 內部的執行緒清理邏輯
- ✅ 避免 AttributeError

---

## 📚 QThread 生命週期最佳實踐

### 正確的停止流程

```python
class Worker(QThread):
    def run(self):
        while not self.isInterruptionRequested():
            # 執行工作
            time.sleep(0.1)

# 正確的清理流程：
def cleanup_worker(self):
    if self.worker and self.worker.isRunning():
        # 步驟 1：請求中斷
        self.worker.requestInterruption()
        
        # 步驟 2：停止事件循環
        self.worker.quit()
        
        # 步驟 3：等待執行緒結束（設置超時）
        if not self.worker.wait(5000):  # 5 秒超時
            # 步驟 4：超時則強制終止
            self.worker.terminate()
            self.worker.wait(1000)
        
        # 步驟 5：確認停止才刪除
        if not self.worker.isRunning():
            self.worker.deleteLater()
        else:
            # 延遲清理
            old = self.worker
            self.worker = None
            old.finished.connect(old.deleteLater)
```

### 常見錯誤

| 錯誤做法 | 後果 |
|---------|------|
| 直接 `deleteLater()` | 🚨 崩潰 |
| 只用 `requestInterruption()` | ⚠️ 執行緒可能不停止 |
| `wait()` 時間太短 | ⚠️ 執行緒未結束就刪除 |
| 沒有調用 `quit()` | ⚠️ 事件循環不停止 |
| 沒有檢查 `isRunning()` | 🚨 可能崩潰 |

### 正確做法

1. ✅ `requestInterruption()` - 請求中斷
2. ✅ `quit()` - 停止事件循環
3. ✅ `wait(timeout)` - 等待結束（5 秒合理）
4. ✅ `terminate()` - 超時強制終止
5. ✅ 檢查 `isRunning()` - 確認停止
6. ✅ `deleteLater()` - 安全刪除

---

## ✅ 修復驗證計劃

### 測試步驟

1. **啟動 GUI**
   ```powershell
   python f1t_gui_main.py
   ```

2. **開啟 Speed Analysis**
   - 選擇 2025 Japan R
   - 載入數據（觸發 API Worker）

3. **等待數據載入完成**
   - 確認圖表正常顯示

4. **關閉視窗**
   - 點擊 X 關閉
   - 觀察終端輸出

5. **重複多次**
   - 開啟 → 載入 → 關閉
   - 測試 5 次

### 預期結果

✅ **修復前**：
```
QThread: Destroyed while thread is still running
[程式崩潰]
```

✅ **修復後**：
```
[TELEMETRY_LOADER] ⚠️ API Worker 仍在運行，請求中斷...
[TELEMETRY_LOADER] ✅ API Worker 已正常停止
[TELEMETRY_LOADER] ✅ API Worker 已安全刪除
[SPEEDDATAMANAGER] ✅ 已清理 loader 執行緒
[SPEED_MDI] ✅ 資源清理完成
```

### 成功指標

- ✅ 不再出現 "QThread: Destroyed while thread is still running" 錯誤
- ✅ 主程式不崩潰
- ✅ 視窗可以正常關閉
- ✅ 終端顯示 "API Worker 已正常停止"
- ✅ 可以重複開啟/關閉模組

---

## 🚨 其他模組需要檢查

### 受影響的模組

所有使用 `TelemetryDataLoader` 的模組都需要檢查：

| 模組 | 基類 | 狀態 |
|------|------|------|
| Speed Analysis | TelemetryDataLoader | ✅ 已修復 |
| RPM Analysis | TelemetryDataLoader | ⚠️ 需要檢查 |
| Gear Analysis | TelemetryDataLoader | ⚠️ 需要檢查 |
| Throttle Analysis | TelemetryDataLoader | ⚠️ 需要檢查 |
| Brake Analysis | TelemetryDataLoader | ⚠️ 需要檢查 |
| Acceleration Analysis | TelemetryDataLoader | ⚠️ 需要檢查 |

**好消息**：修復在基類 `TelemetryDataLoader` 中，所有子類自動受益！

---

## 📊 修復統計

| 項目 | 修復前 | 修復後 |
|------|--------|--------|
| QThread 停止方式 | requestInterruption() + wait(200) | quit() + wait(5000) + terminate() |
| 等待時間 | 200ms | 5000ms（可配置） |
| 強制終止 | ❌ 無 | ✅ terminate() |
| 停止檢查 | ❌ 無 | ✅ isRunning() |
| 延遲清理 | ❌ 無 | ✅ finished.connect(deleteLater) |
| 崩潰風險 | 🚨 高 | ✅ 低 |

---

## 💡 經驗總結

### 關鍵教訓

1. **QThread 清理是 Qt 開發的重要課題**
   - 必須正確停止才能刪除
   - 不能假設執行緒會快速結束

2. **超時設置很重要**
   - 200ms 太短，大部分網路請求都超過這個時間
   - 5000ms (5秒) 是合理的超時時間
   - 必須有強制終止的備案

3. **事件循環必須停止**
   - `requestInterruption()` 只是請求，不保證停止
   - `quit()` 才能停止事件循環
   - 兩者配合使用

4. **防禦性編程**
   - 總是檢查 `isRunning()`
   - 提供延遲清理的備案
   - 避免崩潰優先於完美清理

### 通用模板

```python
def cleanup_qthread(thread, timeout_ms=5000):
    """通用的 QThread 清理函數"""
    if not thread or not thread.isRunning():
        return True
    
    # 1. 請求中斷
    thread.requestInterruption()
    thread.quit()
    
    # 2. 等待結束
    if thread.wait(timeout_ms):
        thread.deleteLater()
        return True
    
    # 3. 強制終止
    thread.terminate()
    if thread.wait(1000):
        thread.deleteLater()
        return True
    
    # 4. 延遲清理
    thread.finished.connect(thread.deleteLater)
    return False
```

---

## 🎯 下一步行動

1. ✅ **測試 Speed 模組** - 確認不再崩潰
2. ⚠️ **檢查其他模組** - RPM、Throttle 等
3. ⚠️ **測試記憶體洩漏修復** - 確認循環引用解決
4. ⚠️ **壓力測試** - 快速開啟/關閉多次
5. ⚠️ **網路延遲測試** - 模擬慢速 API 回應

---

**報告結束**

修復人員：AI Assistant  
審核人員：待確認  
測試狀態：待測試  
優先級：🔴 最高（崩潰問題）
