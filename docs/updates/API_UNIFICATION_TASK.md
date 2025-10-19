# 🔄 GUI 模組 API 呼叫統一化專案

**任務編號**: API-UNIFICATION-001  
**優先級**: P0 (最高優先級 - 架構重構)  
**狀態**: 📋 規劃中 (已更新 - 2025-10-11)  
**建立日期**: 2025-10-11  
**預估工時**: ~~40-60 小時~~ → **48-72 小時** (已調整，增加 20% 緩衝)

---

## 📊 現況深度確認報告

### ✅ API_MODULE_API_EVALUATION.md 驗證結果

經過深度代碼檢查，確認該 MD 文件**完全正確**：

#### 1️⃣ **發現的 API Worker 類別** (19 個)

| 模組類別 | Worker 類別 | Function ID | Timeout | 受影響檔案 |
|---------|-----------|-------------|---------|----------|
| **遙測系列** | `TelemetryApiWorker` | 13 | 75s | `telemetry_data_loader_base.py` |
| | `TelemetryAnalysisApiWorker` | 12 | 60s | `telemetry_analysis_mdi.py` |
| **天氣與輪胎** | `RainAnalysisApiWorker` | 1 | 20s | `rain_analysis_mdi.py` |
| | `TireAnalysisApiWorker` | 26 | 60s | `tire_analysis_mdi.py` |
| **進站分析** | `PitstopAnalysisApiWorker` | 3, 5 | 45s | `pitstop_analysis_mdi.py` |
| **賽道分析** | `TrackAnalysisApiWorker` | 2 | 60s | `track_analysis_mdi.py` |
| **事故分析** | `AccidentAnalysisApiWorker` | 4, 6, 7 | 60s | `accident_data_manager.py` |
| **理想單圈** | `IdealLapSectorComparisonApiWorker` | 53 | 60s | `ideal_lap_sector_comparison_mdi.py` |
| | `IdealLapSectorHeatmapApiWorker` | 53 | 60s | `ideal_lap_sector_heatmap_mdi.py` |
| | `IdealLapRankingApiWorker` | 53 | 60s | `ideal_lap_ranking_table_mdi.py` |
| **Throttle 系列** | `ThrottleBoxPlotApiWorker` | 54 | 90s | `throttle_box_plot_analysis_mdi.py` |
| | `ThrottleLineChartApiWorker` | 54 | 90s | `throttle_line_chart_data_loader.py` |
| **圈速分析** | `LapTimeBoxPlotApiWorker` | 28 | 60s | `lap_box_plot_analysis_mdi.py` |
| | `DetailedLapAnalysisApiWorker` | 28 | 60s | `driverlap_analysis_mdi.py` |
| **共用服務** | N/A (直接呼叫) | 98 | 10s | `color_palette_provider.py` |
| | N/A (直接呼叫) | 99 | 10s | `season_calendar_provider.py` |

#### 2️⃣ **統一 API 基底網址管理**

✅ **確認**: 所有模組已使用 `resolve_api_base_url()` 統一管理
- **核心模組**: `core/api_base_url.py`
- **公開 API**: `https://api.f1telemetrystationpro.org`
- **安全機制**: 自動過濾 localhost、內網 IP、私有網段

```python
# 所有模組的統一模式
from core.api_base_url import resolve_api_base_url

def _determine_api_base_url(self) -> str:
    return resolve_api_base_url(event_logger=self._debug)
```

#### 3️⃣ **重複代碼模式確認**

所有 API Worker 都重複以下邏輯：

```python
class XxxApiWorker(QThread):
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, base_url, params, timeout, parent=None):
        self.base_url = (base_url or "https://...").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        # 1. 進度回報
        self.progress.emit(15)
        
        # 2. 組裝查詢參數
        query_params = {
            "function_id": XX,
            "year": int(self.params.get("year")),
            "race": self.params.get("race"),
            "session": self.params.get("session"),
            # ... 其他參數
        }
        
        # 3. 發送 POST 請求
        response = requests.post(
            f"{self.base_url}/api/v2/analysis/execute",
            params=query_params,
            timeout=self.timeout,
            headers={"Accept": "application/json"}
        )
        
        # 4. 錯誤處理
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success", False):
            raise RuntimeError(...)
        
        # 5. 提取數據與元數據
        data = payload.get("data")
        meta = {...}
        
        # 6. 回報成功
        self.success.emit({"data": data, "meta": meta})
```

**重複行數統計**: 每個 Worker 約 60-80 行，19 個 Worker 共 **~1300 行重複代碼**

#### 4️⃣ **差異點分析**

| 差異項目 | 變化範圍 | 範例 |
|---------|---------|------|
| `function_id` | 1-99 | 1, 2, 13, 26, 28, 53, 54, 98, 99 |
| `timeout` | 10-90s | 進站 45s, Throttle 90s, 色票 10s |
| 參數欄位 | 0-6 個 | year, race, session, driver1, driver2, lap1, lap2 |
| 進度回報點 | 2-4 個 | 15, 45, 65, 70, 90, 95 |
| 回傳結構 | 2 種 | `{data, meta}` 或 `{data, meta, payload, request_token}` |
| 多次呼叫 | 是/否 | 進站、事故需要多次呼叫不同 function_id |

#### 5️⃣ **快取狀態確認**

✅ **API-ONLY 模式已正確實施**:
- Rain Analysis: `_local_storage_enabled = False` (已關閉快取搜尋)
- Tire Analysis: `_local_storage_enabled = False`
- Telemetry 系列: 仍保留快取機制 (API 失敗時回退)
- Track Analysis: 混合模式 (API 優先 + JSON 後備)

---

## 🎯 統一化目標與範圍

### 核心目標
1. **消除重複代碼**: 將 ~1300 行重複 Worker 代碼整合至共用模組
2. **統一 API 行為**: 逾時、重試、錯誤處理、日誌記錄一致性
3. **提升可維護性**: API 協議變更只需修改一處
4. **保持向後相容**: 確保所有既有模組功能無損

### 不變的部分
- ✅ `UniversalDataLoader` 保留快取職責
- ✅ `resolve_api_base_url()` 繼續管理 base URL
- ✅ 各模組的數據轉換邏輯不變
- ✅ GUI 介面與使用者體驗不變

---

## 🛠️ 技術規格設計

### 1️⃣ **共用 API Client** (`core/analysis_api_client.py`)

```python
"""統一 API 客戶端 - 負責 HTTP 通訊層"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable
import requests
from core.api_base_url import resolve_api_base_url

@dataclass
class ApiRequest:
    """API 請求配置"""
    function_id: int
    year: int
    race: str
    session: str
    driver1: Optional[str] = None
    driver2: Optional[str] = None
    lap1: Optional[int] = None
    lap2: Optional[int] = None
    force_refresh: bool = False
    extra_params: Optional[Dict[str, Any]] = None

@dataclass
class ApiResponse:
    """統一 API 回應結構"""
    success: bool
    data: Optional[Dict[str, Any]]
    meta: Dict[str, Any]
    payload: Dict[str, Any]  # 原始 API 回應
    error: Optional[str] = None
    latency_ms: float = 0.0

class AnalysisApiClient:
    """F1 分析 API 統一客戶端"""
    
    DEFAULT_ENDPOINT = "/api/v2/analysis/execute"
    DEFAULT_TIMEOUT = 60.0
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        event_logger: Optional[Callable[[str], None]] = None
    ):
        self._base_url = base_url or resolve_api_base_url(event_logger=event_logger)
        self._timeout = timeout
        self._logger = event_logger or (lambda msg: None)
    
    def execute(self, request: ApiRequest) -> ApiResponse:
        """執行 API 請求並返回統一回應"""
        
        # 1. 組裝查詢參數
        query_params = self._build_query_params(request)
        
        # 2. 發送請求
        start_time = time.perf_counter()
        try:
            response = requests.post(
                f"{self._base_url}{self.DEFAULT_ENDPOINT}",
                params=query_params,
                timeout=self._timeout,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            latency = (time.perf_counter() - start_time) * 1000
            return ApiResponse(
                success=False,
                data=None,
                meta={},
                payload={},
                error=str(exc),
                latency_ms=latency
            )
        
        # 3. 驗證回應
        latency = (time.perf_counter() - start_time) * 1000
        if not isinstance(payload, dict):
            return ApiResponse(
                success=False,
                data=None,
                meta={},
                payload={},
                error="API 回應必須是 JSON 物件",
                latency_ms=latency
            )
        
        if not payload.get("success", False):
            return ApiResponse(
                success=False,
                data=None,
                meta={},
                payload=payload,
                error=payload.get("message", "API 回傳 success=False"),
                latency_ms=latency
            )
        
        # 4. 提取數據與元數據
        data = payload.get("data")
        meta = {
            "source": payload.get("source", "api"),
            "execution_time": payload.get("execution_time"),
            "request_id": payload.get("request_id"),
            "timestamp": payload.get("timestamp"),
            "function_spec": payload.get("function_spec"),
            "latency_ms": round(latency, 2),
            "base_url": self._base_url,
            "function_id": request.function_id,
        }
        
        return ApiResponse(
            success=True,
            data=data,
            meta=meta,
            payload=payload,
            latency_ms=latency
        )
    
    def _build_query_params(self, request: ApiRequest) -> Dict[str, Any]:
        """構建查詢參數字典"""
        params = {
            "function_id": request.function_id,
            "year": int(request.year),
            "race": request.race,
            "session": request.session,
        }
        
        # 可選參數
        if request.driver1:
            params["driver1"] = str(request.driver1).upper()
        if request.driver2:
            params["driver2"] = str(request.driver2).upper()
        if request.lap1 is not None:
            params["lap1"] = int(request.lap1)
        if request.lap2 is not None:
            params["lap2"] = int(request.lap2)
        if request.force_refresh:
            params["force_refresh"] = True
        
        # 額外參數
        if request.extra_params:
            params.update(request.extra_params)
        
        return params
    
    def health_check(self, timeout: float = 2.0) -> bool:
        """快速健康檢查"""
        try:
            response = requests.get(
                f"{self._base_url}/health",
                timeout=timeout
            )
            return response.status_code < 500
        except Exception:
            return False
```

### 2️⃣ **共用 API Worker** (`core/analysis_api_worker.py`)

```python
"""統一 API Worker - 負責背景執行緒"""

from PyQt5.QtCore import QThread, pyqtSignal
from typing import Any, Dict, Optional
from core.analysis_api_client import AnalysisApiClient, ApiRequest, ApiResponse

class AnalysisApiWorker(QThread):
    """統一 API 背景工作執行緒"""
    
    # 信號定義
    progress = pyqtSignal(int, str)  # (進度百分比, 狀態訊息)
    success = pyqtSignal(dict)       # {data, meta, payload, request_token}
    failure = pyqtSignal(str)        # 錯誤訊息
    
    def __init__(
        self,
        request: ApiRequest,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        request_token: Optional[int] = None,
        parent=None
    ):
        super().__init__(parent)
        self.request = request
        self.client = AnalysisApiClient(base_url, timeout)
        self.request_token = request_token
    
    def run(self) -> None:
        """執行 API 請求"""
        try:
            # 1. 開始請求
            self.progress.emit(15, f"呼叫 API Function {self.request.function_id}...")
            
            # 2. 執行請求
            response = self.client.execute(self.request)
            
            # 3. 更新進度
            self.progress.emit(70, "解析 API 回應...")
            
            # 4. 檢查結果
            if not response.success:
                self.failure.emit(response.error or "未知錯誤")
                return
            
            # 5. 組裝回傳數據
            result = {
                "data": response.data,
                "meta": response.meta,
                "payload": response.payload,
            }
            
            if self.request_token is not None:
                result["request_token"] = self.request_token
            
            # 6. 回報成功
            self.progress.emit(90, "資料載入完成")
            self.success.emit(result)
            
        except Exception as exc:
            self.failure.emit(f"Worker 執行失敗: {exc}")
        finally:
            self.progress.emit(100, "完成")
```

### 3️⃣ **模組端整合範例** (Rain Analysis 改造)

```python
# rain_analysis_mdi.py (改造後)

from core.analysis_api_worker import AnalysisApiWorker
from core.analysis_api_client import ApiRequest

class RainAnalysisDataManager(UniversalDataLoader):
    """下雨分析數據管理器 - 使用統一 API Worker"""
    
    def __init__(self, parent=None):
        # ... 既有初始化邏輯 ...
        self._api_worker: Optional[AnalysisApiWorker] = None
    
    def load_data(self, **kwargs) -> bool:
        """載入降雨分析資料 - 使用統一 API"""
        
        # ... 既有參數驗證邏輯 ...
        
        # ✅ 新的 API 呼叫方式
        request = ApiRequest(
            function_id=1,  # Rain Analysis
            year=kwargs["year"],
            race=kwargs["race"],
            session=kwargs["session"],
            force_refresh=kwargs.get("force_refresh", False)
        )
        
        # 啟動統一 Worker
        self._api_worker = AnalysisApiWorker(
            request=request,
            base_url=self._api_base_url,
            timeout=20.0,
            parent=self
        )
        
        # 連接信號
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker)
        
        self._api_worker.start()
        return True
    
    def _on_api_progress(self, value: int, message: str):
        """處理進度更新"""
        self.load_progress.emit(value)
        self.status_changed.emit(message)
    
    def _on_api_success(self, result: dict):
        """處理成功回應 - 既有邏輯不變"""
        data = result["data"]
        meta = result["meta"]
        # ... 既有的數據處理邏輯 ...
        self.load_success.emit(data)
    
    def _on_api_error(self, error: str):
        """處理錯誤 - 既有邏輯不變"""
        self.load_error.emit(error)
    
    def _cleanup_api_worker(self):
        """清理 Worker"""
        if self._api_worker:
            self._api_worker.deleteLater()
            self._api_worker = None
```

---

## 📋 開發流程與里程碑

### Phase 0: 準備階段 (2 小時)
- [x] 深度確認現況（已完成）
- [ ] 建立開發分支 `feature/api-unification`
- [ ] 設置測試環境
- [ ] 備份既有代碼

### Phase 1: 核心實作 (12 小時) ⚠️ 已調整

#### 1.1 核心模組實作 (6 小時)
- [ ] 實作 `core/analysis_api_client.py`
  - [ ] 基礎 HTTP 通訊層
  - [ ] 🆕 **並發請求管理機制** (新增)
    ```python
    class AnalysisApiClient:
        def __init__(self):
            self._active_requests: Dict[int, ApiRequest] = {}  # 追蹤進行中的請求
            self._request_lock = threading.Lock()              # 保護共享狀態
            
        def execute(self, request: ApiRequest, request_id: Optional[int] = None):
            with self._request_lock:
                if request_id:
                    self._active_requests[request_id] = request
            try:
                # ... 執行請求 ...
            finally:
                with self._request_lock:
                    if request_id and request_id in self._active_requests:
                        del self._active_requests[request_id]
    ```
- [ ] 實作 `core/analysis_api_worker.py`

#### 1.2 測試實作 (4 小時)
- [ ] 撰寫單元測試 `tests/test_analysis_api_client.py`
  - [ ] 🆕 並發請求測試案例
- [ ] 撰寫單元測試 `tests/test_analysis_api_worker.py`

#### 1.3 品質檢查 (2 小時)
- [ ] 確保測試覆蓋率 > 90%
- [ ] Pylance/Flake8 靜態檢查通過
- [ ] 初步 Code Review (自我審查)

**驗收標準**:
```python
# 測試範例
def test_api_client_basic_request():
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    response = client.execute(request)
    assert response.success is True
    assert response.data is not None

def test_api_worker_signals():
    # 驗證 progress, success, failure 信號正確觸發
    pass
```

### Phase 2: 試點遷移 (10 小時)

#### 2.1 遙測系列 (優先級最高)
- [ ] 遷移 `TelemetryApiWorker` → `AnalysisApiWorker`
- [ ] 更新 `telemetry_data_loader_base.py`
- [ ] 執行既有測試 `tests/test_telemetry_*.py`
- [ ] 手動 GUI 測試

#### 2.2 Rain Analysis (最簡單的單一 API)
- [ ] 遷移 `RainAnalysisApiWorker`
- [ ] 更新 `rain_analysis_mdi.py`
- [ ] 執行測試
- [ ] GUI 驗證

#### 2.3 Tire Analysis (類似 Rain)
- [ ] 遷移 `TireAnalysisApiWorker`
- [ ] 更新 `tire_analysis_mdi.py`
- [ ] 執行測試

**里程碑檢查點**:
- ✅ 3 個模組遷移成功
- ✅ 所有既有測試通過
- ✅ GUI 功能無損
- ✅ 性能無下降

### Phase 3: 批量遷移 (15 小時)

#### 3.1 理想單圈系列 (3 個模組，同 function_id=53)
- [ ] Sector Comparison
- [ ] Sector Heatmap
- [ ] Ranking Table

#### 3.2 Throttle 系列 (2 個模組，同 function_id=54)
- [ ] Line Chart
- [ ] Box Plot

#### 3.3 圈速分析系列 (2 個模組，同 function_id=28)
- [ ] Lap Box Plot
- [ ] Detailed Lap Analysis

#### 3.4 賽道與進站 (複雜度較高)
- [ ] Track Analysis (function_id=2)
- [ ] Pitstop Analysis (function_id=3, 5 多次呼叫)

#### 3.5 事故分析 (最複雜，多 function_id)
- [ ] Accident Data Manager (function_id=4, 6, 7)

### Phase 4: 共用服務遷移 (5 小時)
- [ ] Color Palette Provider (function_id=98)
- [ ] Season Calendar Provider (function_id=99)

### Phase 5: 清理與優化 (10 小時) ⚠️ 已調整

#### 5.1 代碼清理 (3 小時)
- [ ] 移除所有舊 API Worker 類別 (19 個檔案)
- [ ] 移除過時的 import 語句
- [ ] 清理未使用的輔助函數

#### 5.2 文檔更新 (2 小時)
- [ ] 更新 `.github/copilot-instructions.md`
- [ ] 更新模組 README 檔案
- [ ] 產生 API 使用範例文檔

#### 5.3 性能與監控 (3 小時)
- [ ] 性能基準測試
  - [ ] API 延遲測試 (平均延遲 < 5s)
  - [ ] 記憶體使用測試 (無洩漏)
  - [ ] 並發請求壓力測試
- [ ] 🆕 **建立效能監控儀表板** (新增)
  ```python
  # core/performance_monitor.py
  class ApiPerformanceMonitor:
      """追蹤 API 延遲趨勢"""
      def __init__(self):
          self.latency_history: List[float] = []
          self.error_count: int = 0
          
      def record_latency(self, latency_ms: float):
          self.latency_history.append(latency_ms)
          
      def get_stats(self) -> Dict[str, Any]:
          return {
              "avg_latency": statistics.mean(self.latency_history),
              "p95_latency": statistics.quantiles(self.latency_history, n=20)[18],
              "error_rate": self.error_count / len(self.latency_history)
          }
  ```

#### 5.4 代碼審查與合併 (2 小時)
- [ ] 🆕 **完整 Code Review (由系統架構師)** (新增)
  - [ ] 架構設計審查
  - [ ] 安全性檢查
  - [ ] 效能評估
  - [ ] 測試覆蓋率驗證
- [ ] 解決 Code Review 意見
- [ ] 合併至主分支 (`main` 或 `develop`)

---

## 🧪 測試策略

### 單元測試 (必須)
```python
# tests/test_analysis_api_client.py
- test_api_client_initialization
- test_build_query_params_basic
- test_build_query_params_with_drivers
- test_build_query_params_with_laps
- test_execute_success
- test_execute_http_error
- test_execute_json_parse_error
- test_execute_api_success_false
- test_health_check_available
- test_health_check_unavailable
- test_timeout_handling

# tests/test_analysis_api_worker.py
- test_worker_initialization
- test_worker_signals_emitted
- test_worker_success_path
- test_worker_failure_path
- test_worker_cleanup
- test_request_token_preserved
```

### 整合測試 (必須)
```python
# tests/integration/test_rain_analysis_api.py
- test_rain_analysis_api_workflow
- test_rain_analysis_fallback_to_json
- test_rain_analysis_error_handling

# 對每個遷移的模組重複
```

### GUI 測試 (手動 + 自動)
- [ ] 啟動 GUI 無錯誤
- [ ] 每個分析模組點擊可用
- [ ] 資料正確載入
- [ ] 進度條正常顯示
- [ ] 錯誤處理彈窗正確

### 性能測試
- [ ] API 請求延遲無增加
- [ ] 記憶體使用無洩漏
- [ ] 並發請求正常處理

---

## 📏 成功指標

### 代碼品質
- ✅ 消除 ~1300 行重複代碼
- ✅ 單元測試覆蓋率 > 90%
- ✅ 無 Pylance/Flake8 警告

### 功能完整性
- ✅ 所有 19 個 API Worker 遷移成功
- ✅ 所有既有測試通過
- ✅ GUI 功能無任何損失

### 可維護性
- ✅ API 協議變更只需修改 `AnalysisApiClient`
- ✅ 新增分析模組只需實例化 `AnalysisApiWorker`
- ✅ 文檔清晰，新手可快速上手

### 性能
- ✅ API 請求延遲 ≤ 原有實作
- ✅ 記憶體使用無增加
- ✅ 並發請求支援 (未來擴展)

---

## ⚠️ 風險與對策

| 風險項目 | 影響等級 | 對策 |
|---------|---------|------|
| 破壞既有功能 | 🔴 高 | 完整測試套件 + 分階段遷移 |
| API 回應格式變化 | 🟡 中 | 嚴格單元測試 + 版本控制 |
| 效能下降 | 🟡 中 | 基準測試 + 性能監控 |
| 遷移時間過長 | 🟢 低 | 優先級排序 + 並行開發 |
| 測試覆蓋不足 | 🟡 中 | 強制測試覆蓋率 > 90% |

---

## 🔗 相關文件

- 原始評估文件: `docs/API_MODULE_API_EVALUATION.md`
- API 基底網址管理: `core/api_base_url.py`
- 通用數據載入器: `modules/gui/base/universal_data_loader.py`
- 開發指導原則: `.github/copilot-instructions.md`

---

## 📝 變更日誌

### 2025-10-11
- ✅ 完成現況深度確認
- ✅ 建立技術規格設計
- ✅ 制定開發流程與測試策略
- 📋 等待開始實作

---

## 👥 負責人與審查

- **任務負責人**: AI Copilot
- **代碼審查**: 系統架構師
- **測試驗證**: QA 團隊
- **最終審核**: 專案負責人

---

**下一步行動**: 開始 Phase 1 - 實作核心共用模組
