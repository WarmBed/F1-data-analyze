# 🚨 F13 API 找不到數據導致 GUI 死當調查報告

## 📋 問題陳述

用戶報告：當 F13 (driver_comparison) 功能在 API 請求時找不到緩存檔案，可能導致主 GUI 死當。

**日誌證據**：
```
function_id=13&year=2024&race=Abu+Dhabi&session=R&driver1=ALB&driver2=ALB&lap1=99&lap2=99 HTTP/1.1" 200 OK
[CACHE] 搜尋功能 13 的緩存結果...
[CACHE] 參數: {'year': 2024, 'race': 'Abu Dhabi', 'session': 'R', 'driver1': 'ALB', 'driver2': 'ALB', 'lap1': 99, 'lap2': 99}
[CACHE] 🎯 精確雙圈匹配模式: Lap99_Lap99
[CACHE] 🔍 搜尋模式: comparison_telemetry_ALB_ALB_2024_abu_dhabi_R_Lap99_Lap99.json
[CACHE] ❌ 無匹配檔案
```

## 🔍 根本原因分析

### 1. **API 返回 200 OK 但數據為空**

**位置**: `api/services/cache_service.py:256`
```python
if not files:
    print(f"[CACHE] ❌ 無匹配檔案")
    continue  # ⚠️ 繼續循環，最終返回 None
```

**位置**: `api/services/cache_service.py:285`
```python
return None  # ⚠️ 找不到數據時返回 None
```

**位置**: `api/services/simple_analysis_service.py:100-130`
```python
# 步驟 1: 檢查緩存
cached = await asyncio.to_thread(
    self.cache_service.search_cached_analysis,
    canonical_id,
    **prepared_params,
)

if cached:
    # 返回緩存數據
    return {"success": True, "data": cached, "source": "cache"}

# 步驟 2: 沒有緩存，執行 CLI
if not force_refresh:
    # ⚠️ 如果 cached 為 None，會進入此分支
    # 但 API 仍然返回 200 OK，只是 data 為空
```

### 2. **GUI 層面錯誤處理不足**

**位置**: `modules/gui/lap_analysis/telemetry_data_loader_base.py:713-727`
```python
def _on_api_success(self, payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        self._on_api_error("無效的 API 回傳格式", None)
        return
    
    request_token = payload.get("request_token")
    data = payload.get("data")  # ⚠️ 如果 data 是 None 會發生什麼？
    raw_payload = payload.get("payload", {})
    meta = payload.get("meta", {})
    
    # ⚠️ 沒有檢查 data 是否為 None！
    self._handle_api_success(data, raw_payload, meta, request_token)
```

**潛在問題**:
- 如果 `data` 是 `None`，`_handle_api_success()` 可能會：
  - 嘗試處理空數據
  - 觸發 `KeyError` 或 `AttributeError`
  - 沒有正確的錯誤處理導致 GUI 卡住

### 3. **API 響應超時機制**

**位置**: `modules/gui/lap_analysis/telemetry_data_loader_base.py:61-65`
```python
# 🔴 修復：大幅減少超時時間
self.timeout = min(timeout, 10.0)  # 最多 10 秒
```

**位置**: `modules/gui/lap_analysis/telemetry_data_loader_base.py:748-764`
```python
def _cleanup_api_worker(self) -> None:
    if self._api_worker:
        if self._api_worker.isRunning():
            self._api_worker.requestInterruption()
            self._api_worker.quit()
            
            # ⚠️ 等待最多 5 秒
            if not self._api_worker.wait(5000):
                print(f"[ERROR] API Worker 5秒後仍未停止，強制終止")
                self._api_worker.terminate()  # 強制終止
                self._api_worker.wait(1000)
```

**分析**:
- API 請求超時：10 秒
- Worker 清理超時：5 秒 + 1 秒 = 6 秒
- 總計：16 秒內應該會響應或超時

### 4. **可能導致死當的場景**

#### 場景 A：無限等待 JSON 解析
```python
# GUI 等待 API 返回
response = requests.post(..., timeout=10.0)  # ✅ 有超時

# 解析 JSON
payload = response.json()  # ⚠️ 如果響應格式錯誤，可能卡住
```

#### 場景 B：錯誤處理路徑阻塞
```python
def _handle_api_success(self, data, raw_payload, meta, request_token):
    # 如果 data 是 None
    if data is None:
        # ⚠️ 沒有明確的錯誤處理
        # 可能嘗試訪問 data["key"] 導致 TypeError
        pass
```

#### 場景 C：信號連接死鎖
```python
# API Worker 發送 success 信號
self.success.emit({"data": None, ...})

# GUI 主線程處理
def _on_api_success(self, payload):
    # 如果這裡拋出異常但沒有被捕獲
    # 可能導致 Qt 事件循環卡住
    raise KeyError("data")  # ⚠️ 未捕獲的異常
```

## 🔧 問題修復方案

### 修復 1: API 層面 - 明確返回錯誤而非 None

**文件**: `api/services/simple_analysis_service.py`

```python
# 當前邏輯
if cached:
    return {"success": True, "data": cached, "source": "cache"}

# 修正後
if cached:
    return {"success": True, "data": cached, "source": "cache"}
else:
    # ✅ 明確返回錯誤訊息
    return {
        "success": False,
        "error": "no_cached_data",
        "message": f"找不到功能 {canonical_id} 的緩存數據",
        "params": prepared_params,
        "source": "cache_miss",
        "timestamp": datetime.now().isoformat()
    }
```

### 修復 2: GUI 層面 - 檢查數據有效性

**文件**: `modules/gui/lap_analysis/telemetry_data_loader_base.py`

```python
def _on_api_success(self, payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        self._on_api_error("無效的 API 回傳格式", None)
        return
    
    request_token = payload.get("request_token")
    data = payload.get("data")
    raw_payload = payload.get("payload", {})
    meta = payload.get("meta", {})
    
    # ✅ 新增：檢查 data 是否有效
    if data is None or (isinstance(data, dict) and not data):
        error_msg = raw_payload.get("message", "API 返回空數據")
        self._on_api_error(error_msg, request_token)
        return
    
    # ✅ 新增：檢查 API success 狀態
    if isinstance(raw_payload, dict) and not raw_payload.get("success", True):
        error_msg = raw_payload.get("message", "API 執行失敗")
        self._on_api_error(error_msg, request_token)
        return
    
    self._handle_api_success(data, raw_payload, meta, request_token)
```

### 修復 3: 添加防禦性異常捕獲

**文件**: `modules/gui/lap_analysis/telemetry_data_loader_base.py`

```python
def _on_api_success(self, payload: Dict[str, Any]) -> None:
    try:
        if not isinstance(payload, dict):
            self._on_api_error("無效的 API 回傳格式", None)
            return
        
        # ... 數據驗證邏輯 ...
        
        self._handle_api_success(data, raw_payload, meta, request_token)
        
    except KeyError as e:
        # ✅ 捕獲鍵錯誤
        error_msg = f"API 響應缺少必要鍵: {str(e)}"
        print(f"[ERROR] [TELEMETRY_LOADER] {error_msg}")
        self._on_api_error(error_msg, payload.get("request_token"))
        
    except TypeError as e:
        # ✅ 捕獲類型錯誤
        error_msg = f"API 響應數據類型錯誤: {str(e)}"
        print(f"[ERROR] [TELEMETRY_LOADER] {error_msg}")
        self._on_api_error(error_msg, payload.get("request_token"))
        
    except Exception as e:
        # ✅ 捕獲所有其他異常
        error_msg = f"處理 API 響應時發生錯誤: {str(e)}"
        print(f"[ERROR] [TELEMETRY_LOADER] {error_msg}")
        import traceback
        traceback.print_exc()
        self._on_api_error(error_msg, payload.get("request_token"))
```

### 修復 4: 確保回退機制正常工作

**文件**: `modules/gui/lap_analysis/telemetry_data_loader_base.py`

```python
def _on_api_error(self, message: str, request_token: Optional[int] = None) -> None:
    if request_token is not None and request_token != self._active_request_token:
        self._debug(f"忽略過時的 API 失敗回應 (token {request_token} != {self._active_request_token})")
        return
    
    self._error(f"API 請求失敗: {message}")
    self._is_loading = False
    self.status_changed.emit("API 請求失敗，嘗試本地 JSON/CLI 後備流程")
    
    # ✅ 確保回退機制被調用
    success = self._fallback_to_local(message, request_token)
    
    if not success:
        # ✅ 如果回退也失敗，發送明確的錯誤信號
        error_msg = f"API 載入失敗且本地回退失敗: {message}"
        print(f"[ERROR] [TELEMETRY_LOADER] {error_msg}")
        self.load_error.emit(error_msg)
        
        # ✅ 確保 GUI 不會卡住
        self.load_progress.emit(100)  # 完成進度條
        self.status_changed.emit("載入失敗")
```

## 🧪 測試驗證

### 測試案例 1: API 返回空數據
```python
# 模擬 API 返回
payload = {
    "success": True,
    "data": None,  # ⚠️ 空數據
    "source": "cache",
    "message": "找不到緩存"
}

# 預期結果
# ✅ GUI 應該顯示錯誤訊息
# ✅ GUI 不應該卡住
# ✅ 應該觸發本地回退流程
```

### 測試案例 2: API 返回錯誤狀態
```python
payload = {
    "success": False,
    "error": "no_cached_data",
    "message": "找不到功能 13 的緩存數據"
}

# 預期結果
# ✅ GUI 應該顯示 "找不到緩存數據"
# ✅ 應該觸發本地回退或 CLI 生成
```

### 測試案例 3: 檢查超時機制
```bash
# 模擬 API 延遲 15 秒
# 預期結果
# ✅ 10 秒後應該超時
# ✅ GUI 應該顯示 "API 請求超時"
# ✅ GUI 不應該永遠等待
```

## 📊 診斷結論

### 問題根源

1. **API 返回 200 OK 但 data 為 None**
   - 緩存未找到時，API 應該返回錯誤狀態，而非成功狀態
   
2. **GUI 沒有檢查 data 有效性**
   - `_on_api_success()` 假設 data 永遠有效
   - 沒有捕獲 KeyError/TypeError 異常
   
3. **錯誤處理路徑不完整**
   - 某些錯誤場景沒有觸發 `load_error` 信號
   - GUI 可能在等待永遠不會到來的信號

### 是否會導致死當？

**結論**: **有可能，但不是必然**

- ✅ **有超時機制**: 10 秒 API 超時 + 6 秒 Worker 清理 = 16 秒內會響應
- ❌ **異常處理不足**: 如果在數據處理中拋出未捕獲的異常，可能導致 GUI 卡住
- ❌ **信號未發送**: 如果錯誤路徑沒有發送 `load_error` 或 `load_progress(100)`，GUI 可能永遠等待

### 最可能的場景

**用戶體驗**: GUI 看起來"卡住"了，但實際上是：
1. API 返回空數據（200 OK）
2. GUI 嘗試處理 None 數據
3. 拋出異常但沒有被捕獲
4. 進度條卡在 70%
5. 狀態訊息顯示 "正在載入..."
6. 用戶等待但沒有任何反應

**不是真正的死鎖，而是錯誤處理不完整導致的假死狀態**

## 🎯 緊急修復優先級

1. **P0 (緊急)**: 在 GUI 的 `_on_api_success()` 中添加數據有效性檢查
2. **P1 (高)**: 在 API 返回時明確區分成功/失敗狀態
3. **P2 (中)**: 添加完整的異常捕獲機制
4. **P3 (低)**: 優化錯誤訊息顯示

## 📝 建議實施步驟

1. ✅ 先修復 GUI 層面的數據驗證（修復 2）
2. ✅ 添加防禦性異常捕獲（修復 3）
3. ✅ 確保錯誤回退機制完整（修復 4）
4. ⏳ 修改 API 返回格式（修復 1）- 需要更多測試

## 🔍 額外調查需求

建議添加詳細日誌來追蹤問題：

```python
# 在 _on_api_success 開頭添加
print(f"[DEBUG] _on_api_success 被調用")
print(f"[DEBUG] payload 類型: {type(payload)}")
print(f"[DEBUG] payload 內容: {payload}")
print(f"[DEBUG] data 類型: {type(payload.get('data'))}")
print(f"[DEBUG] data 內容: {payload.get('data')}")
```

這樣可以在日誌中看到實際發生了什麼。
