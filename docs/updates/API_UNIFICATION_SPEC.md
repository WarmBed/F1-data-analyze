# 📐 API 統一化技術規格文件 (Specification)

**版本**: 1.0.0  
**狀態**: Draft  
**作者**: AI Copilot  
**建立日期**: 2025-10-11  
**關聯任務**: API-UNIFICATION-001

---

## 📚 目錄

1. [系統架構](#系統架構)
2. [核心模組規格](#核心模組規格)
3. [API 協議規範](#api-協議規範)
4. [數據結構定義](#數據結構定義)
5. [錯誤處理機制](#錯誤處理機制)
6. [性能需求](#性能需求)
7. [安全性考量](#安全性考量)
8. [向後相容性](#向後相容性)
9. [擴展性設計](#擴展性設計)
10. [部署指南](#部署指南)

---

## 1. 系統架構

### 1.1 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                       GUI 層 (PyQt5)                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐ │
│  │ Rain MDI  │  │ Tire MDI  │  │Telem MDI  │  │ ... 15個 │ │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────┬─────┘ │
└────────┼──────────────┼──────────────┼─────────────┼────────┘
         │              │              │             │
         │ load_data()  │ load_data()  │ load_data() │
         ▼              ▼              ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│               數據管理層 (UniversalDataLoader)                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ RainDataManager  │  │ TireDataManager  │  │ ...Manager │ │
│  │ - 快取管理       │  │ - 快取管理       │  │            │ │
│  │ - 數據轉換       │  │ - 數據轉換       │  │            │ │
│  │ - 驗證邏輯       │  │ - 驗證邏輯       │  │            │ │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬─────┘ │
└───────────┼────────────────────┼────────────────────┼────────┘
            │ _start_api_request()│                    │
            ▼                     ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│             🆕 統一 API Worker 層 (QThread)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        AnalysisApiWorker (單一類別)                   │   │
│  │  - progress 信號 (進度回報)                           │   │
│  │  - success 信號 (成功回傳)                            │   │
│  │  - failure 信號 (錯誤處理)                            │   │
│  │  - request_token 支援 (並發請求識別)                  │   │
│  └────────────────────┬─────────────────────────────────┘   │
└───────────────────────┼──────────────────────────────────────┘
                        │ execute(ApiRequest)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              🆕 統一 API Client 層 (HTTP)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        AnalysisApiClient (單一類別)                   │   │
│  │  - base_url 管理 (resolve_api_base_url)              │   │
│  │  - 查詢參數組裝 (_build_query_params)                │   │
│  │  - HTTP 請求處理 (requests.post)                      │   │
│  │  - 回應驗證與解析                                     │   │
│  │  - 健康檢查 (health_check)                            │   │
│  └────────────────────┬─────────────────────────────────┘   │
└───────────────────────┼──────────────────────────────────────┘
                        │ POST /api/v2/analysis/execute
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  REST API 服務器                             │
│       https://api.f1telemetrystationpro.org                 │
│              (FastAPI / refactored_api.py)                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 數據流向

#### 成功路徑
```
1. 用戶點擊「載入資料」
   ↓
2. GUI MDI → DataManager.load_data(**params)
   ↓
3. DataManager._start_api_request()
   ↓
4. 創建 ApiRequest 物件
   ↓
5. 創建 AnalysisApiWorker(request)
   ↓
6. Worker.run() → Client.execute(request)
   ↓
7. Client 發送 POST 請求
   ↓
8. API 回傳 {"success": true, "data": {...}}
   ↓
9. Client 包裝為 ApiResponse
   ↓
10. Worker 發出 success 信號
    ↓
11. DataManager._on_api_success(result)
    ↓
12. DataManager 轉換數據格式
    ↓
13. DataManager.load_success.emit(data)
    ↓
14. GUI 更新圖表顯示
```

#### 錯誤路徑
```
1-6. (同上)
   ↓
7. Client 發送 POST 請求
   ↓
8. HTTP 500 錯誤 或 Timeout
   ↓
9. Client 包裝為 ApiResponse(success=False, error="...")
   ↓
10. Worker 發出 failure 信號
    ↓
11. DataManager._on_api_error(error_msg)
    ↓
12. DataManager.load_error.emit(error_msg)
    ↓
13. GUI 顯示錯誤訊息對話框
```

---

## 2. 核心模組規格

### 2.1 `core/analysis_api_client.py`

#### 2.1.1 類別: `ApiRequest`

```python
@dataclass
class ApiRequest:
    """API 請求配置 - 不可變數據類別"""
    
    # 必要欄位
    function_id: int        # CLI Function ID (1-99)
    year: int              # 賽季年份 (2020-2025)
    race: str              # 比賽名稱 (例: "Japan", "Italy")
    session: str           # 會話類型 ("R", "Q", "FP1", "FP2", "FP3")
    
    # 可選欄位
    driver1: Optional[str] = None       # 車手1代碼 (3字母)
    driver2: Optional[str] = None       # 車手2代碼 (3字母)
    lap1: Optional[int] = None          # 圈數1 (>0)
    lap2: Optional[int] = None          # 圈數2 (>0)
    force_refresh: bool = False         # 強制刷新快取
    extra_params: Optional[Dict[str, Any]] = None  # 額外參數
    
    def __post_init__(self):
        """驗證輸入參數"""
        # 驗證 function_id 範圍
        if not (1 <= self.function_id <= 99):
            raise ValueError(f"function_id 必須在 1-99 範圍內，收到 {self.function_id}")
        
        # 驗證年份範圍
        if not (2020 <= self.year <= 2030):
            raise ValueError(f"year 必須在 2020-2030 範圍內，收到 {self.year}")
        
        # 驗證會話類型
        valid_sessions = {"R", "Q", "FP1", "FP2", "FP3", "S", "SS"}
        if self.session not in valid_sessions:
            raise ValueError(f"session 必須是 {valid_sessions} 之一，收到 {self.session}")
        
        # 驗證車手代碼長度
        if self.driver1 and len(self.driver1) != 3:
            raise ValueError(f"driver1 必須是3字母代碼，收到 {self.driver1}")
        if self.driver2 and len(self.driver2) != 3:
            raise ValueError(f"driver2 必須是3字母代碼，收到 {self.driver2}")
        
        # 驗證圈數正整數
        if self.lap1 is not None and self.lap1 < 1:
            raise ValueError(f"lap1 必須 > 0，收到 {self.lap1}")
        if self.lap2 is not None and self.lap2 < 1:
            raise ValueError(f"lap2 必須 > 0，收到 {self.lap2}")
```

#### 2.1.2 類別: `ApiResponse`

```python
@dataclass
class ApiResponse:
    """API 回應結構 - 統一回傳格式"""
    
    # 必要欄位
    success: bool                        # 請求是否成功
    data: Optional[Dict[str, Any]]       # 業務數據 (payload["data"])
    meta: Dict[str, Any]                 # 元數據 (來源、時間戳、延遲等)
    payload: Dict[str, Any]              # 原始 API 回應 (用於調試)
    
    # 可選欄位
    error: Optional[str] = None          # 錯誤訊息 (失敗時)
    latency_ms: float = 0.0              # 請求延遲 (毫秒)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典 (用於序列化)"""
        return {
            "success": self.success,
            "data": self.data,
            "meta": self.meta,
            "payload": self.payload,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }
```

#### 2.1.3 類別: `AnalysisApiClient`

```python
class AnalysisApiClient:
    """F1 分析 API 統一客戶端 - 負責 HTTP 通訊層"""
    
    # 類別常數
    DEFAULT_ENDPOINT: str = "/api/v2/analysis/execute"
    DEFAULT_TIMEOUT: float = 60.0
    DEFAULT_HEADERS: Dict[str, str] = {"Accept": "application/json"}
    
    # 公開方法
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        event_logger: Optional[Callable[[str], None]] = None
    ) -> None:
        """初始化 API Client
        
        🆕 並發請求管理 (Phase 1 新增):
        - _active_requests: 追蹤進行中的請求
        - _request_lock: 執行緒安全保護
        """
        self._base_url = (base_url or resolve_api_base_url()).rstrip('/')
        self._timeout = timeout
        self._event_logger = event_logger
        
        # 🆕 並發請求管理機制
        self._active_requests: Dict[int, ApiRequest] = {}
        self._request_lock = threading.Lock()
    
    def execute(
        self, 
        request: ApiRequest,
        request_id: Optional[int] = None
    ) -> ApiResponse:
        """執行 API 請求並返回統一回應
        
        🆕 並發請求支援:
        - request_id: 可選的請求識別碼，用於追蹤並發請求
        """
        # 🆕 註冊請求
        if request_id is not None:
            with self._request_lock:
                self._active_requests[request_id] = request
        
        try:
            # 執行 HTTP 請求
            response = self._make_request(...)
            return self._parse_response(response, ...)
        finally:
            # 🆕 清理請求
            if request_id is not None:
                with self._request_lock:
                    self._active_requests.pop(request_id, None)
    
    def get_active_requests(self) -> List[int]:
        """🆕 取得所有進行中的請求 ID"""
        with self._request_lock:
            return list(self._active_requests.keys())
    
    def cancel_request(self, request_id: int) -> bool:
        """🆕 取消特定請求 (未來擴展)"""
        with self._request_lock:
            if request_id in self._active_requests:
                del self._active_requests[request_id]
                return True
        return False
    
    def health_check(self, timeout: float = 2.0) -> bool:
        """快速健康檢查 - 不阻塞主執行緒"""
        pass
    
    # 私有方法
    def _build_query_params(self, request: ApiRequest) -> Dict[str, Any]:
        """構建查詢參數字典"""
        pass
    
    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        timeout: float
    ) -> requests.Response:
        """執行 HTTP POST 請求"""
        pass
    
    def _parse_response(
        self,
        response: requests.Response,
        start_time: float,
        request: ApiRequest
    ) -> ApiResponse:
        """解析 API 回應"""
        pass
    
    def _handle_exception(
        self,
        exc: Exception,
        start_time: float
    ) -> ApiResponse:
        """處理請求異常"""
        pass
```

### 2.2 `core/analysis_api_worker.py`

#### 2.2.1 類別: `AnalysisApiWorker`

```python
class AnalysisApiWorker(QThread):
    """統一 API 背景工作執行緒 - 負責非阻塞 API 調用"""
    
    # 信號定義
    progress = pyqtSignal(int, str)  # (進度百分比 0-100, 狀態訊息)
    success = pyqtSignal(dict)       # {data, meta, payload, request_token}
    failure = pyqtSignal(str)        # 錯誤訊息
    
    # 公開方法
    def __init__(
        self,
        request: ApiRequest,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        request_token: Optional[int] = None,
        parent: Optional[QObject] = None
    ) -> None:
        """初始化 API Worker"""
        pass
    
    def run(self) -> None:
        """QThread 執行入口 - 在背景執行緒中執行"""
        pass
    
    # 私有方法
    def _emit_progress(self, value: int, message: str) -> None:
        """安全發送進度信號"""
        pass
    
    def _build_result(
        self,
        response: ApiResponse
    ) -> Dict[str, Any]:
        """構建成功回傳結果"""
        pass
```

---

## 3. API 協議規範

### 3.1 HTTP 端點

#### 端點: `POST /api/v2/analysis/execute`

**基礎 URL**: `https://api.f1telemetrystationpro.org`

**請求格式**:
```http
POST /api/v2/analysis/execute?function_id=1&year=2024&race=Japan&session=R HTTP/1.1
Host: api.f1telemetrystationpro.org
Accept: application/json
Content-Length: 0
```

**查詢參數** (Query Parameters):

| 參數名 | 類型 | 必要 | 範例 | 說明 |
|--------|------|------|------|------|
| `function_id` | int | ✅ | `1` | CLI 功能編號 (1-99) |
| `year` | int | ✅ | `2024` | 賽季年份 |
| `race` | str | ✅ | `Japan` | 比賽名稱 |
| `session` | str | ✅ | `R` | 會話類型 |
| `driver1` | str | ❌ | `VER` | 車手1代碼 |
| `driver2` | str | ❌ | `LEC` | 車手2代碼 |
| `lap1` | int | ❌ | `10` | 圈數1 |
| `lap2` | int | ❌ | `15` | 圈數2 |
| `force_refresh` | bool | ❌ | `true` | 強制刷新 |

**成功回應** (200 OK):
```json
{
  "success": true,
  "data": {
    "analysis_type": "rain_intensity",
    "rain_detected": true,
    "weather_data": [...]
  },
  "source": "api",
  "execution_time": "2.34s",
  "request_id": "req_20241011_123456_abc123",
  "timestamp": "2024-10-11T10:30:00Z",
  "function_spec": {
    "id": 1,
    "name": "run_rain_intensity_analysis_json",
    "description": "降雨強度分析"
  }
}
```

**失敗回應** (200 OK, success=false):
```json
{
  "success": false,
  "message": "找不到該場比賽的資料",
  "error": "RaceNotFound",
  "data": null
}
```

**HTTP 錯誤回應**:
- `400 Bad Request`: 參數錯誤
- `404 Not Found`: 功能不存在
- `500 Internal Server Error`: 伺服器錯誤
- `503 Service Unavailable`: 服務暫時不可用

### 3.2 健康檢查端點

#### 端點: `GET /health`

**請求格式**:
```http
GET /health HTTP/1.1
Host: api.f1telemetrystationpro.org
```

**成功回應** (200 OK):
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-10-11T10:30:00Z"
}
```

---

## 4. 數據結構定義

### 4.1 Function ID 對應表

| Function ID | 分析類型 | 模組名稱 | Timeout |
|-------------|---------|---------|---------|
| 1 | 降雨分析 | Rain Analysis | 20s |
| 2 | 賽道分析 | Track Analysis | 60s |
| 3 | 進站分析 | Pitstop Analysis | 45s |
| 4 | 事故事件 | Accident Events | 60s |
| 5 | 進站影響 | Pitstop Impact | 45s |
| 6 | 事故統計 | Accident Statistics | 60s |
| 7 | 嚴重度分布 | Severity Distribution | 60s |
| 12 | 遙測分析 | Telemetry Analysis | 60s |
| 13 | 遙測比較 | Telemetry Comparison | 75s |
| 26 | 輪胎策略 | Tire Strategy | 60s |
| 28 | 詳細圈速 | Detailed Lap Time | 60s |
| 48 | 直線速度 | Straight Line Speed | 60s |
| 53 | 理想單圈 | Ideal Lap | 60s |
| 54 | 油門分析 | Throttle Analysis | 90s |
| 98 | 色票資料 | Color Palette | 10s |
| 99 | 賽季日曆 | Season Calendar | 10s |

### 4.2 Meta 數據結構

```python
MetaData = TypedDict('MetaData', {
    'source': str,              # "api" | "cache" | "json"
    'execution_time': str,      # "2.34s"
    'request_id': str,          # "req_20241011_123456_abc123"
    'timestamp': str,           # "2024-10-11T10:30:00Z"
    'function_spec': Dict[str, Any],  # {id, name, description}
    'latency_ms': float,        # 2340.56
    'base_url': str,            # "https://api.f1telemetrystationpro.org"
    'function_id': int,         # 1
})
```

---

## 5. 錯誤處理機制

### 5.1 錯誤分類

#### HTTP 錯誤
- `requests.exceptions.Timeout` → "API 請求逾時"
- `requests.exceptions.ConnectionError` → "無法連線至 API 服務器"
- `requests.exceptions.HTTPError` (4xx) → "請求參數錯誤"
- `requests.exceptions.HTTPError` (5xx) → "API 伺服器錯誤"

#### API 業務錯誤
- `success=false` → 使用 `payload["message"]`
- `data is None` → "API 未回傳數據"

#### 數據驗證錯誤
- Invalid JSON → "API 回應格式錯誤"
- Missing required fields → "API 回應缺少必要欄位"

### 5.2 錯誤處理流程

```python
try:
    # 1. 發送請求
    response = requests.post(...)
    
    # 2. 檢查 HTTP 狀態
    response.raise_for_status()
    
    # 3. 解析 JSON
    payload = response.json()
    
    # 4. 驗證回應結構
    if not isinstance(payload, dict):
        raise ValueError("...")
    
    # 5. 檢查業務成功
    if not payload.get("success", False):
        raise RuntimeError(payload.get("message"))
    
    # 6. 提取數據
    data = payload.get("data")
    
    return ApiResponse(success=True, data=data, ...)
    
except requests.exceptions.Timeout as exc:
    return ApiResponse(
        success=False,
        data=None,
        meta={},
        payload={},
        error=f"API 請求逾時: {exc}"
    )
except requests.exceptions.ConnectionError as exc:
    return ApiResponse(
        success=False,
        data=None,
        meta={},
        payload={},
        error=f"無法連線至 API: {exc}"
    )
except Exception as exc:
    return ApiResponse(
        success=False,
        data=None,
        meta={},
        payload={},
        error=f"未預期的錯誤: {exc}"
    )
```

---

## 6. 性能需求

### 6.1 延遲要求

| 場景 | 目標延遲 | 最大延遲 |
|------|---------|---------|
| 健康檢查 | < 500ms | 2s |
| 輕量級 API (F1, F98, F99) | < 3s | 10s |
| 中等 API (F2, F13, F26) | < 5s | 20s |
| 重量級 API (F28, F53, F54) | < 10s | 90s |

### 6.2 並發處理

- **支援並發請求**: 多個模組可同時發起 API 請求
- **Request Token 機制**: 用於識別並發請求
- **無鎖設計**: 每個 Worker 獨立執行，無共享狀態

### 6.3 記憶體使用

- **單次請求**: < 10MB (含 JSON 解析)
- **Worker 清理**: 請求完成後自動釋放資源
- **無洩漏**: 使用 `deleteLater()` 確保 Qt 物件清理

---

## 7. 安全性考量

### 7.1 URL 驗證

```python
# 強制使用公開 API，拒絕 localhost/內網
def _is_internal_host(hostname: str) -> bool:
    if hostname in {"localhost", "127.0.0.1"}:
        return True
    if hostname.endswith(".local"):
        return True
    if ipaddress.ip_address(hostname).is_private:
        return True
    return False
```

### 7.2 輸入驗證

- **Function ID**: 1-99 整數範圍
- **Year**: 2020-2030 範圍
- **Session**: 白名單檢查
- **Driver**: 3 字母代碼格式

### 7.3 HTTPS 強制

- 所有 HTTP URL 自動轉換為 HTTPS
- 拒絕不安全連線

---

## 8. 向後相容性

### 8.1 信號相容

**舊有 Worker 信號**:
```python
progress = pyqtSignal(int)  # 只有進度值
success = pyqtSignal(dict)  # {data, meta}
failure = pyqtSignal(str)   # 錯誤訊息
```

**新 Worker 信號**:
```python
progress = pyqtSignal(int, str)  # (進度值, 狀態訊息)
success = pyqtSignal(dict)       # {data, meta, payload, request_token}
failure = pyqtSignal(str)        # 錯誤訊息
```

**相容性保證**:
- `progress` 信號可選接收第二個參數
- `success` 回傳字典包含所有舊有欄位
- `failure` 信號格式不變

### 8.2 數據格式相容

- 保持 `{data, meta}` 結構不變
- 新增欄位向後相容
- 不移除既有欄位

---

## 9. 擴展性設計

### 9.1 新增 Function ID

```python
# 步驟1: 在 ApiRequest 中無需修改 (自動支援 1-99)

# 步驟2: 在模組中使用
request = ApiRequest(
    function_id=100,  # 新功能
    year=2025,
    race="Dubai",
    session="R"
)

# 步驟3: 啟動 Worker
worker = AnalysisApiWorker(request=request, timeout=120.0)
```

### 9.2 自訂 API 端點

```python
# 支援未來可能的 v3 API
client = AnalysisApiClient()
client.DEFAULT_ENDPOINT = "/api/v3/analysis/execute"
```

### 9.3 插件化錯誤處理

```python
# 允許模組自訂錯誤處理邏輯
class CustomApiClient(AnalysisApiClient):
    def _handle_exception(self, exc, start_time):
        # 自訂邏輯
        return super()._handle_exception(exc, start_time)
```

### 9.4 🆕 效能監控整合 (Phase 5 新增)

```python
# core/performance_monitor.py
from typing import List, Dict, Any
import statistics
from datetime import datetime

class ApiPerformanceMonitor:
    """追蹤 API 延遲趨勢與錯誤率"""
    
    def __init__(self):
        self.latency_history: List[Dict[str, Any]] = []
        self.error_count: int = 0
        self.success_count: int = 0
    
    def record_request(
        self, 
        function_id: int, 
        latency_ms: float, 
        success: bool,
        timestamp: Optional[datetime] = None
    ):
        """記錄單次請求"""
        self.latency_history.append({
            "function_id": function_id,
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": timestamp or datetime.now()
        })
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_stats(self, function_id: Optional[int] = None) -> Dict[str, Any]:
        """取得統計數據"""
        filtered = self.latency_history
        if function_id:
            filtered = [r for r in filtered if r["function_id"] == function_id]
        
        if not filtered:
            return {"error": "無資料"}
        
        latencies = [r["latency_ms"] for r in filtered]
        
        return {
            "total_requests": len(filtered),
            "avg_latency_ms": statistics.mean(latencies),
            "median_latency_ms": statistics.median(latencies),
            "p95_latency_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "error_rate": self.error_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0.0,
            "success_rate": self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0.0,
        }
    
    def export_to_json(self, filepath: str):
        """匯出監控資料至 JSON"""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": self.get_stats(),
                "history": self.latency_history
            }, f, indent=2, default=str)

# 使用範例
monitor = ApiPerformanceMonitor()

# 在 AnalysisApiClient.execute() 中整合
def execute(self, request: ApiRequest, request_id: Optional[int] = None) -> ApiResponse:
    start_time = time.perf_counter()
    response = self._make_request(...)
    latency_ms = (time.perf_counter() - start_time) * 1000
    
    # 🆕 記錄效能
    if hasattr(self, 'performance_monitor'):
        self.performance_monitor.record_request(
            function_id=request.function_id,
            latency_ms=latency_ms,
            success=response.success
        )
    
    return response
```

---

## 10. 部署指南

### 10.1 依賴安裝

```powershell
# requirements.txt 新增
requests>=2.28.0
PyQt5>=5.15.0
```

### 10.2 檔案結構

```
F1-data-analyze/
├── core/
│   ├── analysis_api_client.py    # 新增 ✅
│   ├── analysis_api_worker.py    # 新增 ✅
│   └── api_base_url.py           # 既有
├── modules/gui/
│   ├── rain_analysis/
│   │   └── rain_analysis_mdi.py  # 修改 🔄
│   └── tire_analysis/
│       └── tire_analysis_mdi.py  # 修改 🔄
└── tests/
    ├── test_analysis_api_client.py  # 新增 ✅
    └── test_analysis_api_worker.py  # 新增 ✅
```

### 10.3 遷移檢查清單

**遷移前**:
- [ ] 備份既有代碼
- [ ] 確認所有測試通過
- [ ] 記錄性能基準

**遷移中**:
- [ ] 實作新模組
- [ ] 撰寫測試
- [ ] 遷移單一模組
- [ ] 驗證功能無損

**遷移後**:
- [ ] 移除舊 Worker
- [ ] 更新文檔
- [ ] 性能對比測試
- [ ] 部署上線

---

## 📝 版本歷史

### v1.0.0 (2025-10-11)
- 🎉 初始版本
- ✅ 完整技術規格定義
- ✅ API 協議規範
- ✅ 錯誤處理機制

---

## 📚 參考文獻

- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [Requests 庫文檔](https://requests.readthedocs.io/)
- [PyQt5 文檔](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [F1T 開發指導原則](.github/copilot-instructions.md)

---

**文件狀態**: 等待審核 → 批准 → 實作
