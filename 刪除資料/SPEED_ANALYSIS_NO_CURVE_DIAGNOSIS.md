# 速度分析模組無曲線顯示問題 - 深度診斷

## 當前狀況

你看到的終端輸出：
```
[SPEED DEBUG] ✅ API 回傳成功，開始處理數據
```

**之後就沒有任何輸出了！**

## 問題定位

### 正常的數據流應該是：

```
1. API 請求發送
   ↓
2. [SPEED DEBUG] 🚀 呼叫 API
   ↓
3. [SPEED DEBUG] ✅ API 回傳成功，開始處理數據  ← 你看到的最後一行
   ↓
4. [SPEED DEBUG] 📦 data 類型: <class 'dict'>  ← 應該看到但沒有
   ↓
5. [SPEED DEBUG] 🚀 準備調用 _handle_api_success
   ↓
6. [SPEED DEBUG] ========== _handle_api_success 開始 ==========
   ↓
7. 數據驗證、處理、發送信號
   ↓
8. GUI 顯示曲線
```

### 實際情況：

數據流在**步驟 3 之後就中斷了**！

## 可能的原因

### 原因 1: run_api_call 線程異常（最可能）

`run_api_call` 是在**背景線程**中執行的：
```python
thread = threading.Thread(target=run_api_call, daemon=True)
thread.start()
```

如果在 `self._debug("✅ API 回傳成功，開始處理數據")` 之後的任何操作拋出異常，可能被靜默吞沒。

**檢查點**：
- `data = payload.get('data')` 是否成功？
- `QTimer.singleShot(0, lambda: ...)` 是否正確排程？

### 原因 2: QTimer.singleShot 失敗

`QTimer.singleShot(0, lambda: self._handle_api_success(data, payload, current_token))`

這個調用需要：
1. Qt 事件循環正在運行
2. lambda 函數能正確捕獲變數
3. 主線程沒有被阻塞

**可能的問題**：
- Lambda 函數中的 `data`、`payload`、`current_token` 沒有正確捕獲
- Qt 事件循環有問題

### 原因 3: _handle_api_success 被調用但立即失敗

`_handle_api_success` 的第一行是：
```python
if request_token is not None and request_token != self._active_request_token:
    self._debug(f"忽略過時的 API 成功回應...")
    return
```

如果 token 不匹配，方法會直接返回，不會有任何輸出（除非啟用了調試）。

## 我已實施的修復

### 修復 1: 增強 run_api_call 調試

在 `run_api_call` 中添加：
```python
self._debug("✅ API 回傳成功，開始處理數據")
self._debug(f"📦 data 類型: {type(data)}")
self._debug(f"📦 data 鍵值: {list(data.keys())}")
self._debug(f"🚀 準備調用 _handle_api_success")
QTimer.singleShot(0, lambda: self._handle_api_success(data, payload, current_token))
self._debug("✅ QTimer.singleShot 已排程")
```

### 修復 2: 增強 _handle_api_success 調試

在方法的每個關鍵步驟添加調試輸出：
```python
def _handle_api_success(self, data, payload, request_token):
    self._debug("========== _handle_api_success 開始 ==========")
    
    # 檢查 token
    if request_token is not None and request_token != self._active_request_token:
        self._debug(f"忽略過時的 API 成功回應 (token {request_token} != {self._active_request_token})")
        return
    
    try:
        self._debug("✅ 步驟1: meta 數據構建完成")
        self._debug("✅ 步驟2: 數據格式驗證通過")
        # ... 每個步驟都有詳細日誌
    except Exception as exc:
        self._error(f"❌ 處理 API 數據失敗: {exc}")
        self._error(traceback.format_exc())
```

## 下一步測試

1. **重啟 GUI 並重新測試**
   ```powershell
   python f1t_gui_main.py
   ```

2. **打開速度分析模組**
   - 選擇：2025 Japan R VER vs VER Lap1

3. **觀察終端輸出**

### 情況 A: 如果看到新的調試輸出

```
[SPEED DEBUG] ✅ API 回傳成功，開始處理數據
[SPEED DEBUG] 📦 data 類型: <class 'dict'>
[SPEED DEBUG] 📦 data 鍵值: ['analysis_type', 'metadata', 'results']
[SPEED DEBUG] 🚀 準備調用 _handle_api_success
[SPEED DEBUG] ✅ QTimer.singleShot 已排程
```

**然後沒有 `========== _handle_api_success 開始 ==========`**

→ 這表示 `QTimer.singleShot` 沒有執行 lambda，可能是：
   - Qt 事件循環問題
   - Lambda 捕獲問題
   - 主線程阻塞

**解決方案**：改用直接調用或不同的線程同步方式

### 情況 B: 如果看到 `_handle_api_success 開始` 但中途停止

```
[SPEED DEBUG] ========== _handle_api_success 開始 ==========
[SPEED DEBUG] ✅ 步驟1: meta 數據構建完成
[SPEED DEBUG] ✅ 步驟2: 數據格式驗證通過
[SPEED DEBUG] ❌ 處理 API 數據失敗: ...
```

→ 這會告訴我們具體在哪個步驟失敗

### 情況 C: 如果仍然只看到 `✅ API 回傳成功`

→ 這表示在 `self._debug("✅ API 回傳成功，開始處理數據")` 之後的代碼根本沒有執行

**可能原因**：
- 線程被終止
- 異常被靜默捕獲
- 某個對象已被銷毀

**解決方案**：
```python
# 在 try 外添加 finally 塊
finally:
    print("run_api_call 線程結束")
```

## 臨時診斷方案

如果問題難以定位，可以嘗試：

### 方案 1: 繞過 QTimer

直接在主線程調用（不推薦，但可用於診斷）：
```python
self._handle_api_success(data, payload, current_token)
```

### 方案 2: 使用 PyQt5 信號

創建自定義信號：
```python
class TelemetryDataLoader(QObject):
    _api_success_signal = pyqtSignal(dict, dict, object)
    
    def __init__(self):
        super().__init__()
        self._api_success_signal.connect(self._handle_api_success)
    
    # 在 run_api_call 中：
    self._api_success_signal.emit(data, payload, current_token)
```

### 方案 3: 添加檔案日誌

如果終端輸出有問題：
```python
import logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG)
logging.debug("✅ API 回傳成功")
```

## 預期結果

修復後應該看到完整的調試鏈：
```
[SPEED DEBUG] ✅ API 回傳成功，開始處理數據
[SPEED DEBUG] 📦 data 類型: <class 'dict'>
[SPEED DEBUG] 🚀 準備調用 _handle_api_success
[SPEED DEBUG] ✅ QTimer.singleShot 已排程
[SPEED DEBUG] ========== _handle_api_success 開始 ==========
[SPEED DEBUG] ✅ 步驟1-7 全部完成
[SPEED DEBUG] 🚀 即將發送 data_loaded 信號
[SPEED_MDI_DATA] ========== 數據載入完成回調 ==========
[SPEED_MDI] ========== 更新速度圖表回調 ==========
[SPEED_CHART] ========== set_speed_data 被調用 ==========
```

最終 GUI 應該顯示曲線圖。
