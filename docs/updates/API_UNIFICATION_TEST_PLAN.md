# 🧪 API 統一化測試計畫

**關聯任務**: API-UNIFICATION-001  
**測試類型**: 單元測試 + 整合測試 + GUI 測試  
**測試覆蓋目標**: > 90%  
**建立日期**: 2025-10-11

---

## 📊 測試範圍總覽

### 測試金字塔

```
        /\
       /  \     GUI 測試 (手動 + 自動)
      /────\    ~10 個測試場景
     /      \
    /────────\  整合測試
   /  19模組  \ ~50 個測試案例
  /────────────\
 / 單元測試     \ ~100 個測試案例
/________________\
```

### 測試環境需求

- Python 3.10+
- PyQt5 5.15+
- pytest 7.0+
- pytest-qt (GUI 測試)
- pytest-cov (覆蓋率)
- requests-mock (API Mock)
- API Server 運行中 (整合測試)

---

## 1️⃣ 單元測試計畫

### 1.1 AnalysisApiClient 測試

**檔案**: `tests/test_analysis_api_client.py`

```python
"""
測試目標: 確保 API Client 正確處理 HTTP 通訊層
測試覆蓋: 100% (核心模組)
"""

import pytest
import requests_mock
from core.analysis_api_client import AnalysisApiClient, ApiRequest, ApiResponse

# ========== 初始化測試 ==========
def test_client_initialization_default():
    """測試預設初始化"""
    client = AnalysisApiClient()
    assert client._base_url == "https://api.f1telemetrystationpro.org"
    assert client._timeout == 60.0

def test_client_initialization_custom():
    """測試自訂初始化"""
    client = AnalysisApiClient(
        base_url="https://staging.example.com",
        timeout=30.0
    )
    assert client._base_url == "https://staging.example.com"
    assert client._timeout == 30.0

def test_client_base_url_normalization():
    """測試 base URL 自動標準化"""
    client = AnalysisApiClient(base_url="https://api.example.com/")
    # 應自動移除尾部斜線
    assert not client._base_url.endswith("/")

# ========== 查詢參數建構測試 ==========
def test_build_query_params_minimal():
    """測試最小必要參數"""
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    params = client._build_query_params(request)
    
    assert params["function_id"] == 1
    assert params["year"] == 2024
    assert params["race"] == "Japan"
    assert params["session"] == "R"
    assert "driver1" not in params
    assert "driver2" not in params

def test_build_query_params_with_drivers():
    """測試包含車手參數"""
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=13,
        year=2024,
        race="Japan",
        session="R",
        driver1="VER",
        driver2="LEC"
    )
    params = client._build_query_params(request)
    
    assert params["driver1"] == "VER"
    assert params["driver2"] == "LEC"

def test_build_query_params_with_laps():
    """測試包含圈數參數"""
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=13,
        year=2024,
        race="Japan",
        session="R",
        lap1=10,
        lap2=15
    )
    params = client._build_query_params(request)
    
    assert params["lap1"] == 10
    assert params["lap2"] == 15

def test_build_query_params_force_refresh():
    """測試強制刷新參數"""
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R",
        force_refresh=True
    )
    params = client._build_query_params(request)
    
    assert params["force_refresh"] is True

def test_build_query_params_extra_params():
    """測試額外自訂參數"""
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R",
        extra_params={"custom_field": "custom_value"}
    )
    params = client._build_query_params(request)
    
    assert params["custom_field"] == "custom_value"

def test_build_query_params_driver_uppercase():
    """測試車手代碼自動轉大寫"""
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=13,
        year=2024,
        race="Japan",
        session="R",
        driver1="ver",  # 小寫
        driver2="lec"
    )
    params = client._build_query_params(request)
    
    assert params["driver1"] == "VER"
    assert params["driver2"] == "LEC"

# ========== API 執行測試 ==========
def test_execute_success(requests_mock):
    """測試成功的 API 請求"""
    mock_response = {
        "success": True,
        "data": {"test_key": "test_value"},
        "source": "api",
        "execution_time": "1.23s",
        "request_id": "test-req-123",
        "timestamp": "2024-10-11T10:00:00Z"
    }
    
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        json=mock_response
    )
    
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    response = client.execute(request)
    
    assert response.success is True
    assert response.data == {"test_key": "test_value"}
    assert response.meta["source"] == "api"
    assert response.meta["function_id"] == 1
    assert response.error is None
    assert response.latency_ms > 0

def test_execute_http_error(requests_mock):
    """測試 HTTP 錯誤 (500)"""
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        status_code=500,
        text="Internal Server Error"
    )
    
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    response = client.execute(request)
    
    assert response.success is False
    assert response.data is None
    assert response.error is not None
    assert "500" in response.error or "Server Error" in response.error

def test_execute_timeout(requests_mock):
    """測試請求逾時"""
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        exc=requests.exceptions.Timeout
    )
    
    client = AnalysisApiClient(timeout=1.0)
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    response = client.execute(request)
    
    assert response.success is False
    assert "timeout" in response.error.lower() or "Timeout" in response.error

def test_execute_connection_error(requests_mock):
    """測試連線錯誤"""
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        exc=requests.exceptions.ConnectionError
    )
    
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    response = client.execute(request)
    
    assert response.success is False
    assert response.error is not None

def test_execute_invalid_json(requests_mock):
    """測試無效的 JSON 回應"""
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        text="This is not JSON"
    )
    
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    response = client.execute(request)
    
    assert response.success is False
    assert "JSON" in response.error or "json" in response.error

def test_execute_api_success_false(requests_mock):
    """測試 API 回傳 success=False"""
    mock_response = {
        "success": False,
        "message": "找不到該場比賽的資料",
        "data": None
    }
    
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        json=mock_response
    )
    
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    response = client.execute(request)
    
    assert response.success is False
    assert "找不到該場比賽的資料" in response.error

def test_execute_missing_data_field(requests_mock):
    """測試缺少 data 欄位"""
    mock_response = {
        "success": True,
        # 缺少 data 欄位
    }
    
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        json=mock_response
    )
    
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    response = client.execute(request)
    
    # 應該仍視為成功，但 data 為 None
    assert response.success is True
    assert response.data is None

# ========== 健康檢查測試 ==========
def test_health_check_available(requests_mock):
    """測試 API 健康檢查 - 可用"""
    requests_mock.get(
        "https://api.f1telemetrystationpro.org/health",
        status_code=200
    )
    
    client = AnalysisApiClient()
    assert client.health_check() is True

def test_health_check_unavailable(requests_mock):
    """測試 API 健康檢查 - 不可用"""
    requests_mock.get(
        "https://api.f1telemetrystationpro.org/health",
        status_code=500
    )
    
    client = AnalysisApiClient()
    assert client.health_check() is False

def test_health_check_timeout(requests_mock):
    """測試健康檢查逾時"""
    requests_mock.get(
        "https://api.f1telemetrystationpro.org/health",
        exc=requests.exceptions.Timeout
    )
    
    client = AnalysisApiClient()
    assert client.health_check() is False

def test_health_check_connection_error(requests_mock):
    """測試健康檢查連線錯誤"""
    requests_mock.get(
        "https://api.f1telemetrystationpro.org/health",
        exc=requests.exceptions.ConnectionError
    )
    
    client = AnalysisApiClient()
    assert client.health_check() is False

# ========== 邊界條件測試 ==========
def test_execute_with_all_parameters(requests_mock):
    """測試包含所有可能參數的請求"""
    mock_response = {
        "success": True,
        "data": {"test": "data"},
        "source": "api"
    }
    
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        json=mock_response
    )
    
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=13,
        year=2024,
        race="Japan",
        session="R",
        driver1="VER",
        driver2="LEC",
        lap1=10,
        lap2=15,
        force_refresh=True,
        extra_params={"custom": "value"}
    )
    
    response = client.execute(request)
    
    assert response.success is True
    
    # 驗證請求參數正確傳遞
    last_request = requests_mock.last_request
    assert last_request.qs["function_id"][0] == "13"
    assert last_request.qs["year"][0] == "2024"
    assert last_request.qs["driver1"][0] == "VER"
    assert last_request.qs["lap1"][0] == "10"

def test_execute_latency_measurement():
    """測試延遲時間測量準確性"""
    # 使用實際 mock，確保延遲測量正常
    pass  # 實作時補充

# ========== 執行統計 ==========
# 總測試案例: ~25 個
# 預估執行時間: < 5 秒
# 覆蓋率目標: 100%
```

### 1.2 AnalysisApiWorker 測試

**檔案**: `tests/test_analysis_api_worker.py`

```python
"""
測試目標: 確保 API Worker 正確處理背景執行緒與信號
測試覆蓋: 95% (排除 QThread 內部)
"""

import pytest
from PyQt5.QtCore import QCoreApplication, QTimer
from pytestqt.qtbot import QtBot
from core.analysis_api_worker import AnalysisApiWorker
from core.analysis_api_client import ApiRequest

# ========== 初始化測試 ==========
def test_worker_initialization(qtbot):
    """測試 Worker 初始化"""
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    worker = AnalysisApiWorker(
        request=request,
        timeout=30.0,
        request_token=12345
    )
    
    assert worker.request == request
    assert worker.request_token == 12345
    assert worker.client is not None

# ========== 信號測試 ==========
def test_worker_signals_defined(qtbot):
    """測試 Worker 信號已定義"""
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    worker = AnalysisApiWorker(request=request)
    
    # 驗證信號存在
    assert hasattr(worker, 'progress')
    assert hasattr(worker, 'success')
    assert hasattr(worker, 'failure')

def test_worker_success_signal(qtbot, requests_mock):
    """測試成功信號觸發"""
    mock_response = {
        "success": True,
        "data": {"test_key": "test_value"},
        "source": "api"
    }
    
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        json=mock_response
    )
    
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    worker = AnalysisApiWorker(request=request)
    
    # 監聽信號
    with qtbot.waitSignal(worker.success, timeout=5000) as blocker:
        worker.start()
    
    # 驗證回傳數據
    result = blocker.args[0]
    assert result["data"]["test_key"] == "test_value"
    assert "meta" in result
    assert "payload" in result

def test_worker_failure_signal(qtbot, requests_mock):
    """測試失敗信號觸發"""
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        status_code=500
    )
    
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    worker = AnalysisApiWorker(request=request, timeout=2.0)
    
    # 監聽失敗信號
    with qtbot.waitSignal(worker.failure, timeout=5000) as blocker:
        worker.start()
    
    # 驗證錯誤訊息
    error_msg = blocker.args[0]
    assert error_msg is not None
    assert isinstance(error_msg, str)

def test_worker_progress_signals(qtbot, requests_mock):
    """測試進度信號觸發"""
    mock_response = {
        "success": True,
        "data": {},
        "source": "api"
    }
    
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        json=mock_response
    )
    
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    worker = AnalysisApiWorker(request=request)
    
    progress_values = []
    
    def on_progress(value, message):
        progress_values.append(value)
    
    worker.progress.connect(on_progress)
    
    with qtbot.waitSignal(worker.success, timeout=5000):
        worker.start()
    
    # 驗證進度值遞增
    assert len(progress_values) > 0
    assert progress_values[-1] == 100  # 最終應為 100

def test_worker_request_token_preserved(qtbot, requests_mock):
    """測試 request_token 正確保留"""
    mock_response = {
        "success": True,
        "data": {"test": "data"},
        "source": "api"
    }
    
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        json=mock_response
    )
    
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    worker = AnalysisApiWorker(
        request=request,
        request_token=99999
    )
    
    with qtbot.waitSignal(worker.success, timeout=5000) as blocker:
        worker.start()
    
    result = blocker.args[0]
    assert result["request_token"] == 99999

# ========== 清理測試 ==========
def test_worker_cleanup(qtbot, requests_mock):
    """測試 Worker 完成後正確清理"""
    mock_response = {
        "success": True,
        "data": {},
        "source": "api"
    }
    
    requests_mock.post(
        "https://api.f1telemetrystationpro.org/api/v2/analysis/execute",
        json=mock_response
    )
    
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    worker = AnalysisApiWorker(request=request)
    
    with qtbot.waitSignal(worker.finished, timeout=5000):
        worker.start()
    
    # 驗證執行緒已結束
    assert not worker.isRunning()

# ========== 執行統計 ==========
# 總測試案例: ~10 個
# 預估執行時間: < 10 秒 (含 Qt 事件循環)
# 覆蓋率目標: 95%
```

---

## 2️⃣ 整合測試計畫

### 2.1 模組遷移驗證測試

**檔案**: `tests/integration/test_rain_analysis_migration.py`

```python
"""
測試目標: 驗證 Rain Analysis 遷移至統一 API Worker 後功能正常
"""

def test_rain_analysis_load_data_api_success(qtbot):
    """測試透過 API 成功載入雨量資料"""
    from modules.gui.rain_analysis.rain_analysis_mdi import RainAnalysisDataManager
    
    manager = RainAnalysisDataManager()
    
    with qtbot.waitSignal(manager.load_success, timeout=30000) as blocker:
        result = manager.load_data(
            year=2024,
            race="Japan",
            session="R"
        )
    
    assert result is True
    data = blocker.args[0]
    assert data is not None
    assert isinstance(data, dict)

def test_rain_analysis_load_data_api_failure(qtbot):
    """測試 API 失敗時錯誤處理"""
    from modules.gui.rain_analysis.rain_analysis_mdi import RainAnalysisDataManager
    
    manager = RainAnalysisDataManager()
    
    # 模擬 API 不可用
    manager._api_base_url = "http://localhost:9999"
    
    with qtbot.waitSignal(manager.load_error, timeout=10000) as blocker:
        manager.load_data(
            year=2024,
            race="InvalidRace",
            session="R"
        )
    
    error_msg = blocker.args[0]
    assert error_msg is not None
```

### 2.2 多模組並行測試

```python
"""
測試目標: 驗證多個模組可同時使用統一 API Worker
"""

def test_concurrent_api_requests(qtbot):
    """測試並行 API 請求"""
    from modules.gui.rain_analysis.rain_analysis_mdi import RainAnalysisDataManager
    from modules.gui.tire_analysis.tire_analysis_mdi import TireAnalysisDataManager
    
    rain_manager = RainAnalysisDataManager()
    tire_manager = TireAnalysisDataManager()
    
    # 同時啟動兩個請求
    rain_manager.load_data(year=2024, race="Japan", session="R")
    tire_manager.load_data(year=2024, race="Japan", session="R")
    
    # 驗證兩個都成功
    # ...
```

---

## 3️⃣ GUI 測試計畫

### 3.1 手動測試檢查清單

```markdown
## Rain Analysis 模組
- [ ] 啟動 GUI 無錯誤
- [ ] 選單項目「降雨分析」可點擊
- [ ] 參數選擇面板正常顯示
- [ ] 點擊「載入資料」後進度條顯示
- [ ] 圖表正確繪製
- [ ] 錯誤情況顯示錯誤訊息

## Tire Analysis 模組
- [ ] ...（重複上述檢查）

## Telemetry Series 模組
- [ ] ...（重複上述檢查）
```

### 3.2 自動化 GUI 測試

```python
"""
檔案: tests/gui/test_rain_analysis_gui.py
測試目標: 自動化驗證 GUI 互動
"""

def test_rain_analysis_gui_workflow(qtbot):
    """測試完整 GUI 工作流程"""
    from f1t_gui_main import StyleHMainWindow
    
    window = StyleHMainWindow()
    qtbot.addWidget(window)
    
    # 1. 點擊選單
    # 2. 驗證 MDI 視窗打開
    # 3. 選擇參數
    # 4. 點擊載入
    # 5. 等待完成
    # 6. 驗證圖表顯示
```

---

## 4️⃣ 性能測試計畫

### 4.1 基準測試

```python
"""
檔案: tests/performance/test_api_performance.py
"""

def test_api_request_latency_benchmark():
    """測試 API 請求延遲基準"""
    import time
    from core.analysis_api_client import AnalysisApiClient, ApiRequest
    
    client = AnalysisApiClient()
    request = ApiRequest(
        function_id=1,
        year=2024,
        race="Japan",
        session="R"
    )
    
    latencies = []
    for _ in range(10):
        start = time.perf_counter()
        response = client.execute(request)
        latency = time.perf_counter() - start
        latencies.append(latency)
    
    avg_latency = sum(latencies) / len(latencies)
    
    # 平均延遲應 < 5 秒
    assert avg_latency < 5.0
    print(f"平均延遲: {avg_latency:.2f}s")
```

---

## 5️⃣ 測試執行流程

### 開發時測試
```powershell
# 執行單元測試
python -m pytest tests/test_analysis_api_client.py -v

# 執行特定測試
python -m pytest tests/test_analysis_api_client.py::test_execute_success -v

# 查看覆蓋率
python -m pytest tests/ --cov=core --cov-report=html
```

### CI/CD 測試
```powershell
# 完整測試套件
python -m pytest tests/ -v --tb=short --cov=core --cov=modules/gui --cov-report=term-missing

# 快速測試（排除慢速測試）
python -m pytest tests/ -v -m "not slow"
```

---

## 6️⃣ 測試通過標準

### 單元測試
- ✅ 所有測試通過 (100%)
- ✅ 代碼覆蓋率 > 90%
- ✅ 無 flaky 測試
- ✅ 執行時間 < 30 秒

### 整合測試
- ✅ 所有模組遷移測試通過
- ✅ 並行請求測試通過
- ✅ 無記憶體洩漏

### GUI 測試
- ✅ 所有手動檢查項目通過
- ✅ 自動化 GUI 測試通過
- ✅ 無視覺迴歸

### 性能測試
- ✅ API 延遲 ≤ 遷移前
- ✅ 記憶體使用無增加
- ✅ 並發請求正常處理

---

## 📝 測試報告範本

```markdown
# API 統一化測試報告

## 測試摘要
- 執行日期: YYYY-MM-DD
- 測試覆蓋率: XX%
- 通過率: XX%
- 失敗案例: X 個

## 詳細結果
### 單元測試
- AnalysisApiClient: ✅ 25/25 通過
- AnalysisApiWorker: ✅ 10/10 通過

### 整合測試
- Rain Analysis: ✅ 通過
- Tire Analysis: ✅ 通過
- ...

### GUI 測試
- 手動測試: ✅ 10/10 通過
- 自動化測試: ✅ 5/5 通過

### 性能測試
- 平均延遲: 2.3s (基準: 2.5s) ✅
- 記憶體使用: 150MB (基準: 145MB) ✅

## 問題與風險
無

## 結論
所有測試通過，可進入下一階段。
```

---

**下一步**: 開始實作 `core/analysis_api_client.py` 並撰寫對應測試
