# Speed vs Brake Worker 逐字比對報告

## 📋 宣告反幻覺編碼五原則

**原則 0：宣告原則（最高優先）**
- ✅ 本次執行前已宣告五原則

**原則 1：禁止幻覺編碼**
- ✅ 使用 `grep_search` 搜索 Worker 類別
- ✅ 使用 `read_file` 讀取實際代碼
- ❌ 絕不憑想像編寫代碼

**原則 2：模組資料夾優先**
- ✅ 以 Speed 模組為參考範本
- ✅ 完整複製 Speed 的 Worker 實現

**原則 3：通用模組優先**
- ✅ 使用相同的 API 架構
- ✅ 使用相同的信號機制

**原則 4：多國語言化**
- ⏳ Worker 內部無用戶可見字串

**原則 5：Logger 輸出**
- ✅ 使用 print() 輸出調試信息

---

## 🔍 完整逐字比對表格

### 1. 類別定義

| 項目 | Speed (Line 31) | Brake (Line 33) | 狀態 |
|------|----------------|----------------|------|
| **類別名稱** | `CrossEventComparisonWorker` | `CrossEventBrakeComparisonWorker` | ⚠️ 不同（可接受）|
| **父類別** | `QThread` | `QThread` | ✅ 相同 |
| **Docstring** | `跨賽事比較 API Worker - 調用 /api/v2/analysis/cross-event-comparison 端點` | `跨賽事比較 API Worker - 調用 /api/v2/analysis/cross-event-comparison 端點` | ✅ 相同 |

### 2. 信號定義

| 項目 | Speed (Line 34-36) | Brake (Line 36-38) | 狀態 |
|------|-------------------|-------------------|------|
| **信號 1** | `progress = pyqtSignal(int)` | `success = pyqtSignal(dict)` | ❌ 順序不同！|
| **信號 2** | `success = pyqtSignal(dict)` | `failure = pyqtSignal(str)` | ❌ 順序不同！|
| **信號 3** | `failure = pyqtSignal(str)` | `progress = pyqtSignal(int)` | ❌ 順序不同！|

**差異**：
- Speed 順序：**progress → success → failure**
- Brake 順序：**success → failure → progress**

### 3. `__init__` 方法參數

| 參數 | Speed (Line 38-40) | Brake (Line 40-42) | 狀態 |
|------|-------------------|-------------------|------|
| **driver1** | `driver1: str` | `driver1: str` | ✅ 相同 |
| **year1** | `year1: int` | `year1: int` | ✅ 相同 |
| **race1** | `race1: str` | `race1: str` | ✅ 相同 |
| **session1** | `session1: str` | `session1: str` | ✅ 相同 |
| **lap1** | `lap1: int` | `lap1: int` | ✅ 相同 |
| **driver2** | `driver2: str` | `driver2: str` | ✅ 相同 |
| **year2** | `year2: int` | `year2: int` | ✅ 相同 |
| **race2** | `race2: str` | `race2: str` | ✅ 相同 |
| **session2** | `session2: str` | `session2: str` | ✅ 相同 |
| **lap2** | `lap2: int` | `lap2: int` | ✅ 相同 |
| **force_refresh** | `force_refresh: bool = False` | `force_refresh: bool = False` | ✅ 相同 |
| **timeout** | `timeout: float = 120.0` | `timeout: int = 60` | ❌ 類型和值不同！|
| **parent** | `parent=None` | `parent=None` | ✅ 相同 |

**差異**：
- Speed timeout：`float = 120.0`（120 秒）
- Brake timeout：`int = 60`（60 秒）

### 4. 實例變數初始化

| 行號 | Speed (Line 41-58) | Brake (Line 43-61) | 狀態 |
|------|-------------------|-------------------|------|
| 1 | `super().__init__(parent)` | `super().__init__(parent)` | ✅ 相同 |
| 2 | `self.driver1 = driver1` | `self.driver1 = driver1` | ✅ 相同 |
| 3 | `self.year1 = year1` | `self.year1 = year1` | ✅ 相同 |
| 4 | `self.race1 = race1` | `self.race1 = race1` | ✅ 相同 |
| 5 | `self.session1 = session1` | `self.session1 = session1` | ✅ 相同 |
| 6 | `self.lap1 = lap1` | `self.lap1 = lap1` | ✅ 相同 |
| 7 | （空行）| （無空行）| ⚠️ 格式不同 |
| 8 | `self.driver2 = driver2` | `self.driver2 = driver2` | ✅ 相同 |
| 9 | `self.year2 = year2` | `self.year2 = year2` | ✅ 相同 |
| 10 | `self.race2 = race2` | `self.race2 = race2` | ✅ 相同 |
| 11 | `self.session2 = session2` | `self.session2 = session2` | ✅ 相同 |
| 12 | `self.lap2 = lap2` | `self.lap2 = lap2` | ✅ 相同 |
| 13 | （空行）| （無空行）| ⚠️ 格式不同 |
| 14 | `self.force_refresh = force_refresh` | `self.force_refresh = force_refresh` | ✅ 相同 |
| 15 | `self.timeout = timeout` | `self.timeout = timeout` | ✅ 相同 |
| 16 | `self.base_url = resolve_api_base_url().rstrip('/')` | `self.base_url = "https://localhost:8000"` | ❌ **關鍵差異！** |

**差異**：
- Speed：`resolve_api_base_url().rstrip('/')` （動態解析）
- Brake：`"https://localhost:8000"` （硬編碼）

### 5. `run()` 方法 - 變數定義

| 行號 | Speed (Line 60-76) | Brake (Line 63-87) | 狀態 |
|------|-------------------|-------------------|------|
| 1 | `try:` | `try:` | ✅ 相同 |
| 2 | `self.progress.emit(20)` | `print(f"[BRAKE-CROSS-EVENT-WORKER] 🚀 開始跨賽事比較 API 請求")` | ❌ Brake 多加調試 |
| 3 | `endpoint = f"{self.base_url}/api/v2/analysis/cross-event-comparison"` | `start_ts = time.perf_counter()` | ⚠️ 順序不同 |
| 4 | （空行）| `self.progress.emit(10)` | ⚠️ Brake emit 10 不是 20 |
| 5 | `# 構建請求參數` | `# 構建請求 URL` | ⚠️ 註釋不同 |
| 6 | `query_params: Dict[str, Any] = {` | `url = f"{self.base_url}/api/v2/analysis/cross-event-comparison"` | ❌ Speed 先定義參數，Brake 先定義 URL |

**差異**：
- Speed：先 emit 20 → 定義 endpoint → 定義 query_params
- Brake：先打印 → start timer → emit 10 → 定義 url → 定義 params

### 6. 請求參數構建

| 行號 | Speed (Line 63-75) | Brake (Line 73-87) | 狀態 |
|------|-------------------|-------------------|------|
| 變數名 | `query_params: Dict[str, Any] = {` | `params = {` | ❌ 類型註解缺失！|
| driver1 | `"driver1": self.driver1,` | `'driver1': self.driver1,` | ⚠️ 引號類型不同 |
| year1 | `"year1": int(self.year1),` | `'year1': self.year1,` | ⚠️ Speed 有 int()，Brake 沒有 |
| race1 | `"race1": self.race1,` | `'race1': self.race1,` | ⚠️ 引號類型不同 |
| session1 | `"session1": self.session1,` | `'session1': self.session1,` | ⚠️ 引號類型不同 |
| lap1 | `"lap1": self.lap1,` | `'lap1': self.lap1,` | ⚠️ 引號類型不同 |
| driver2 | `"driver2": self.driver2,` | `'driver2': self.driver2,` | ⚠️ 引號類型不同 |
| year2 | `"year2": int(self.year2),` | `'year2': self.year2,` | ⚠️ Speed 有 int()，Brake 沒有 |
| race2 | `"race2": self.race2,` | `'race2': self.race2,` | ⚠️ 引號類型不同 |
| session2 | `"session2": self.session2,` | `'session2': self.session2,` | ⚠️ 引號類型不同 |
| lap2 | `"lap2": self.lap2,` | `'lap2': self.lap2,` | ⚠️ 引號類型不同 |
| **額外參數** | （無）| `'analysis_type': 'brake'  # ⚠️ 指定為 brake 分析` | ❌ **Brake 多加！** |

**差異**：
1. Speed 使用雙引號 `"`，Brake 使用單引號 `'`
2. Speed 明確轉換 year 為 `int()`，Brake 沒有
3. **Brake 多加了 `'analysis_type': 'brake'` 參數**

### 7. force_refresh 處理

| 項目 | Speed (Line 76-77) | Brake (Line 73-87) | 狀態 |
|------|-------------------|-------------------|------|
| **if 檢查** | `if self.force_refresh:` | （無）| ❌ **Brake 缺失！** |
| **參數添加** | `query_params["force_refresh"] = True` | （無）| ❌ **Brake 缺失！** |

**差異**：Brake 完全沒有處理 `force_refresh` 參數！

### 8. 調試輸出

| 行號 | Speed (Line 79-80) | Brake (Line 88-89) | 狀態 |
|------|-------------------|-------------------|------|
| 1 | `print(f"[CROSS-EVENT-WORKER] 請求 API: {endpoint}")` | `print(f"[BRAKE-CROSS-EVENT-WORKER] 參數: {params}")` | ⚠️ 內容不同 |
| 2 | `print(f"[CROSS-EVENT-WORKER] 參數: {query_params}")` | （之前已打印 URL）| ⚠️ 順序不同 |

### 9. API 請求發送 - **關鍵差異！**

| 項目 | Speed (Line 82-87) | Brake (Line 93-98) | 狀態 |
|------|-------------------|-------------------|------|
| **計時開始** | `start_ts = time.perf_counter()` | `start_ts = time.perf_counter()` | ✅ 相同（但位置不同）|
| **請求方法** | `response = requests.post(` | `response = requests.post(` | ✅ 相同 |
| **URL 參數** | `endpoint,` | `url,` | ⚠️ 變數名不同 |
| **參數傳遞** | `params=query_params,` | `json=params,` | ❌ **關鍵差異！** |
| **timeout** | `timeout=self.timeout,` | `timeout=self.timeout,` | ✅ 相同 |
| **headers** | `headers={"Accept": "application/json"}` | `headers={'Content-Type': 'application/json'}` | ❌ **Header 不同！** |
| **progress** | `self.progress.emit(70)` | `self.progress.emit(70)` | ✅ 相同 |
| **raise** | `response.raise_for_status()` | `response.raise_for_status()` | ✅ 相同 |

**關鍵差異**：
1. **Speed 使用 `params=query_params`**
   - 參數編碼為 **URL 查詢字串**
   - 例：`POST /api/v2/analysis/cross-event-comparison?driver1=VER&year1=2025...`

2. **Brake 使用 `json=params`**
   - 參數編碼為 **JSON 請求 Body**
   - 例：`POST /api/v2/analysis/cross-event-comparison` with body `{"driver1": "VER", ...}`

3. **Speed Header: `Accept: application/json`** （期望 JSON 回應）
4. **Brake Header: `Content-Type: application/json`** （發送 JSON 內容）

### 10. 響應處理

| 行號 | Speed (Line 88-111) | Brake (Line 101-128) | 狀態 |
|------|---------------------|---------------------|------|
| 響應解析 | `payload = response.json()` | `payload = response.json()` | ✅ 相同 |
| 類型檢查 | `if not isinstance(payload, dict):` | `if not isinstance(payload, dict):` | ✅ 相同 |
| 錯誤訊息 | `raise ValueError("API response must be a JSON object")` | `raise ValueError(f"Invalid API response type: {type(payload)}")` | ⚠️ 訊息不同 |
| success 檢查 | `if not payload.get("success", False):` | （無）| ❌ **Brake 缺失！** |
| success 錯誤 | `raise RuntimeError(payload.get("message", "API returned success=False"))` | （無）| ❌ **Brake 缺失！** |
| 數據提取 | `data = payload.get("data")` | `data = payload.get("data")` | ✅ 相同 |
| 數據檢查 | `if not isinstance(data, dict):` | `if not isinstance(data, dict):` | ✅ 相同 |
| 數據錯誤 | `raise ValueError("API response missing 'data' object")` | `raise ValueError("API response missing 'data' object")` | ✅ 相同 |

**差異**：
- **Speed 檢查 `payload.get("success")`，Brake 沒有！**

### 11. metadata 構建

| 欄位 | Speed | Brake | 狀態 |
|------|-------|-------|------|
| source | `"cross_event_api"` | `"cross_event_api"` | ✅ 相同 |
| cross_event | `True` | `True` | ✅ 相同 |
| execution_time | `payload.get("execution_time")` | `payload.get("execution_time")` | ✅ 相同 |
| request_id | `payload.get("request_id")` | `payload.get("request_id")` | ✅ 相同 |
| timestamp | `payload.get("timestamp")` | `payload.get("timestamp")` | ✅ 相同 |
| latency_ms | `round(latency_ms, 2)` | `round(latency_ms, 2)` | ✅ 相同 |
| base_url | `self.base_url` | `self.base_url` | ✅ 相同 |

**相同** ✅

### 12. 信號發送

| 項目 | Speed (Line 112-113) | Brake (Line 129-130) | 狀態 |
|------|---------------------|---------------------|------|
| progress | `self.progress.emit(90)` | `self.progress.emit(90)` | ✅ 相同 |
| success | `self.success.emit({"data": data, "meta": meta})` | `self.success.emit({"data": data, "meta": meta})` | ✅ 相同 |

### 13. 異常處理

| 項目 | Speed (Line 115-120) | Brake (Line 132-137) | 狀態 |
|------|---------------------|---------------------|------|
| print | `print(f"[CROSS-EVENT-WORKER] ❌ 請求失敗: {exc}")` | `print(f"[BRAKE-CROSS-EVENT-WORKER] ❌ 請求失敗: {exc}")` | ⚠️ 前綴不同 |
| traceback | `import traceback` | `import traceback` | ✅ 相同 |
| print_exc | `traceback.print_exc()` | `traceback.print_exc()` | ✅ 相同 |
| failure | `self.failure.emit(str(exc))` | `self.failure.emit(str(exc))` | ✅ 相同 |

### 14. finally 塊

| 項目 | Speed (Line 122-123) | Brake (Line 139-140) | 狀態 |
|------|---------------------|---------------------|------|
| progress | `self.progress.emit(100)` | `self.progress.emit(100)` | ✅ 相同 |

---

## 🚨 發現的關鍵差異總結

### ❌ 嚴重差異（會導致崩潰或功能異常）

1. **API 請求參數傳遞方式**
   - Speed: `params=query_params` （URL 查詢字串）
   - Brake: `json=params` （JSON 請求 Body）
   - **影響**：API 端點可能期望特定格式，用錯會導致 422 錯誤

2. **缺失 `force_refresh` 處理**
   - Speed: 有檢查並添加參數
   - Brake: 完全缺失
   - **影響**：無法強制刷新緩存

3. **缺失 `success` 檢查**
   - Speed: 檢查 `payload.get("success")`
   - Brake: 沒有檢查
   - **影響**：API 返回 `success: False` 時不會觸發錯誤

4. **額外的 `analysis_type` 參數**
   - Speed: 無此參數
   - Brake: 有 `'analysis_type': 'brake'`
   - **影響**：API 可能不支援此參數，導致 422 錯誤

### ⚠️ 中等差異（影響一致性）

5. **`base_url` 來源**
   - Speed: `resolve_api_base_url().rstrip('/')`（動態）
   - Brake: 硬編碼 `"https://localhost:8000"`
   - **影響**：無法支援本地開發環境

6. **timeout 類型和值**
   - Speed: `float = 120.0`
   - Brake: `int = 60`
   - **影響**：Brake 超時時間只有 Speed 的一半

7. **HTTP Header**
   - Speed: `Accept: application/json`
   - Brake: `Content-Type: application/json`
   - **影響**：語義不同，可能影響 API 響應

8. **信號定義順序**
   - Speed: `progress, success, failure`
   - Brake: `success, failure, progress`
   - **影響**：Python 不在乎順序，但破壞一致性

### ⚡ 輕微差異（不影響功能）

9. **變數命名**
   - Speed: `query_params: Dict[str, Any]`
   - Brake: `params`（無類型註解）

10. **引號風格**
    - Speed: 雙引號 `"`
    - Brake: 單引號 `'`

11. **調試訊息前綴**
    - Speed: `[CROSS-EVENT-WORKER]`
    - Brake: `[BRAKE-CROSS-EVENT-WORKER]`

12. **year 參數轉換**
    - Speed: `int(self.year1)`
    - Brake: `self.year1`（已經是 int）

13. **空行格式**
    - Speed: 在變數組之間有空行
    - Brake: 沒有空行

---

## 💡 修復建議

### 優先級 1（必須修復）

1. **統一 API 請求方式** - 改用 `params=query_params`
2. **移除 `analysis_type` 參數** - Speed 沒有
3. **添加 `force_refresh` 處理**
4. **添加 `success` 檢查**

### 優先級 2（強烈建議）

5. **使用 `resolve_api_base_url()`** - 支援本地開發
6. **timeout 改為 `float = 120.0`** - 保持一致
7. **HTTP Header 改為 `Accept: application/json`**

### 優先級 3（可選）

8. **信號定義順序** - 改為 `progress, success, failure`
9. **變數命名和類型註解** - 改為 `query_params: Dict[str, Any]`
10. **引號風格** - 統一使用雙引號
11. **添加 `int()` 轉換** - 明確轉換 year
12. **調試訊息前綴** - 可保持 Brake 專屬前綴

---

## 🔧 修復代碼範例

```python
class CrossEventBrakeComparisonWorker(QThread):
    """跨賽事比較 API Worker - 調用 /api/v2/analysis/cross-event-comparison 端點"""

    progress = pyqtSignal(int)  # ✅ 修復順序
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, driver1: str, year1: int, race1: str, session1: str, lap1: int,
                 driver2: str, year2: int, race2: str, session2: str, lap2: int,
                 force_refresh: bool = False, timeout: float = 120.0, parent=None):  # ✅ 修復 timeout
        super().__init__(parent)
        self.driver1 = driver1
        self.year1 = year1
        self.race1 = race1
        self.session1 = session1
        self.lap1 = lap1
        
        self.driver2 = driver2
        self.year2 = year2
        self.race2 = race2
        self.session2 = session2
        self.lap2 = lap2
        
        self.force_refresh = force_refresh
        self.timeout = timeout
        self.base_url = resolve_api_base_url().rstrip('/')  # ✅ 修復 base_url

    def run(self):
        try:
            self.progress.emit(20)  # ✅ 修復 emit 值
            endpoint = f"{self.base_url}/api/v2/analysis/cross-event-comparison"
            
            # 構建請求參數
            query_params: Dict[str, Any] = {  # ✅ 修復變數名和類型
                "driver1": self.driver1,
                "year1": int(self.year1),  # ✅ 添加 int()
                "race1": self.race1,
                "session1": self.session1,
                "lap1": self.lap1,
                "driver2": self.driver2,
                "year2": int(self.year2),  # ✅ 添加 int()
                "race2": self.race2,
                "session2": self.session2,
                "lap2": self.lap2,
                # ❌ 移除 'analysis_type': 'brake'
            }
            
            # ✅ 添加 force_refresh 處理
            if self.force_refresh:
                query_params["force_refresh"] = True

            print(f"[BRAKE-CROSS-EVENT-WORKER] 請求 API: {endpoint}")
            print(f"[BRAKE-CROSS-EVENT-WORKER] 參數: {query_params}")
            
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,  # ✅ 修復：使用 params
                timeout=self.timeout,
                headers={"Accept": "application/json"}  # ✅ 修復 Header
            )
            self.progress.emit(70)
            response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be a JSON object")
            
            # ✅ 添加 success 檢查
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API returned success=False"))

            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API response missing 'data' object")

            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            meta = {
                "source": "cross_event_api",
                "cross_event": True,
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }

            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            print(f"[BRAKE-CROSS-EVENT-WORKER] ❌ 請求失敗: {exc}")
            import traceback
            traceback.print_exc()
            self.failure.emit(str(exc))
            
        finally:
            self.progress.emit(100)
```

---

## 📊 修復前後對比

| 項目 | 修復前（Brake）| 修復後（完全複製 Speed）| 狀態 |
|------|---------------|----------------------|------|
| 信號順序 | `success, failure, progress` | `progress, success, failure` | ✅ 已修復 |
| timeout | `int = 60` | `float = 120.0` | ✅ 已修復 |
| base_url | 硬編碼 | `resolve_api_base_url()` | ✅ 已修復 |
| 請求方式 | `json=params` | `params=query_params` | ✅ 已修復 |
| Header | `Content-Type` | `Accept` | ✅ 已修復 |
| analysis_type | 有 | 無 | ✅ 已移除 |
| force_refresh | 無 | 有 | ✅ 已添加 |
| success 檢查 | 無 | 有 | ✅ 已添加 |
| 變數命名 | `params` | `query_params: Dict[str, Any]` | ✅ 已修復 |
| year 轉換 | 無 | `int()` | ✅ 已添加 |
| emit 值 | 10 | 20 | ✅ 已修復 |

---

## 🧪 測試計畫

### 測試步驟

1. **Import 測試**
   ```python
   from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import CrossEventBrakeComparisonWorker
   print("✅ Import 成功")
   ```

2. **Worker 創建測試**
   ```python
   worker = CrossEventBrakeComparisonWorker(
       driver1="NOR", year1=2025, race1="Australia", session1="R", lap1=99,
       driver2="NOR", year2=2025, race2="Australia", session2="Q", lap2=99
   )
   print("✅ Worker 創建成功")
   ```

3. **信號連接測試**
   ```python
   worker.progress.connect(lambda p: print(f"Progress: {p}%"))
   worker.success.connect(lambda d: print(f"✅ Success: {list(d.keys())}"))
   worker.failure.connect(lambda e: print(f"❌ Failure: {e}"))
   worker.start()
   ```

4. **GUI 整合測試**
   - 啟動 GUI
   - 開啟 Brake Analysis
   - 右鍵 → Settings
   - 取消勾選「與主視窗同步車手與圈數」
   - 設定跨賽事參數
   - 點擊 OK
   - **驗證**：GUI 不崩潰，數據正常載入

### 預期結果

- ✅ Worker 成功發送請求
- ✅ API 返回 200 OK
- ✅ 數據正常解析
- ✅ 圖表正常繪製
- ✅ GUI 不崩潰
- ✅ 日誌無錯誤

---

## 📝 總結

根據逐字比對，Brake Worker 有 **13 個差異**，其中 **4 個嚴重差異**會導致功能異常或崩潰：

1. ❌ API 請求方式錯誤（`json=` vs `params=`）
2. ❌ 缺失 `force_refresh` 處理
3. ❌ 缺失 `success` 檢查
4. ❌ 額外的 `analysis_type` 參數

**修復後，Brake Worker 將與 Speed Worker 完全一致（除了類別名稱和調試前綴），確保功能穩定性。**

