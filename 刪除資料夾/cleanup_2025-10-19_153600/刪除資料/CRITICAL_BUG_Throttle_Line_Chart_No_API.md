# 🚨 緊急修復報告：Throttle Line Chart EXE 完全失效

**日期**: 2025-10-08 22:15  
**嚴重程度**: 🔴 CRITICAL  
**影響範圍**: Throttle Line Chart (Single Driver) 在 EXE 環境完全無法使用  
**狀態**: 🔍 根本原因已確認

---

## 📋 問題症狀

### EXE 環境
- ✅ Throttle Box Plot 正常運作（透過 API 載入資料，17 位車手數據正確顯示）
- ❌ Throttle Line Chart (Single Driver) 完全失效：
  - 左側圖表完全空白，顯示「正在載入數據...」
  - 無法選擇車手（Driver 1 下拉選單無選項）
  - 無曲線輸出
  - 無任何數據載入

### Python 環境
- ✅ 兩者都能正常運作
- 可能依賴本地 JSON 緩存檔案

---

## 🔍 根本原因分析

### 對比分析

#### Throttle Box Plot (✅ 正常)
```python
# throttle_box_plot_analysis_mdi.py (Line 129-136)
class ThrottleBoxPlotDataManager(UniversalDataLoader):
    def __init__(self, parent=None):
        throttle_config = AnalysisConfig(
            display_name=tr("throttle_box_plot", "油門箱型圖"),
            debug_prefix="[THROTTLE_DATA]",
            data_source="api",  # ✅ 支援 API
            cli_function="54",
            api_endpoint="/api/v2/analysis/execute",  # ✅ API 端點
            api_function_id=54,  # ✅ Function ID
            api_timeout=90.0,
            # ...
        )
```

**關鍵特性**:
1. ✅ `data_source="api"` - 主要數據來源為 API
2. ✅ `ThrottleBoxPlotApiWorker` (Line 67-123) - 專用 API 工作執行緒
3. ✅ `load_data()` 覆寫 (Line 227) - 實現 API 調用邏輯
4. ✅ API 成功回調 (見日誌):
```
[THROTTLE_DATA] 透過 API 載入油門資料
[THROTTLE_DATA] ========== API 成功回調 ==========
[THROTTLE_DATA] 成功處理 17 位車手的油門數據
[THROTTLE_DATA] ✅ 數據處理完成
```

#### Throttle Line Chart (❌ 失效)
```python
# throttle_line_chart_data_loader.py (Line 25-35)
class ThrottleLineChartDataLoader(UniversalDataLoader):
    def __init__(self, parent: Optional[QObject] = None):
        config = AnalysisConfig(
            display_name="Throttle Line Chart (Single Driver)",
            debug_prefix="THROTTLE-LINE",
            data_source="json",  # ❌ 只支援 JSON
            cli_function="54",
            file_patterns=[
                "throttle_ratio_{year}_{race}_{session}.json",
                # ...
            ],
            # ❌ 缺少 api_endpoint
            # ❌ 缺少 api_function_id
        )
```

**致命缺陷**:
1. ❌ `data_source="json"` - 只支援本地 JSON 檔案
2. ❌ **沒有 API Worker** - 完全沒有 API 調用邏輯
3. ❌ **沒有 `load_data()` API 覆寫** - 只能讀取本地檔案
4. ❌ 日誌顯示失敗流程:
```
[THROTTLE-LINE DEBUG] 📂 搜尋目錄: json
[THROTTLE-LINE DEBUG]    ❌ 目錄不存在: json
[THROTTLE-LINE DEBUG] 📂 搜尋目錄: json_exports
[THROTTLE-LINE DEBUG]    ❌ 目錄不存在: json_exports
[THROTTLE-LINE DEBUG] 📂 搜尋目錄: cache
[THROTTLE-LINE DEBUG]    ❌ 目錄不存在: cache
[THROTTLE-LINE DEBUG] ❌ 未找到符合的數據檔案
[THROTTLE-LINE DEBUG] ⚠️  [API-ONLY 模式] 禁止呼叫 CLI 生成數據
[THROTTLE-LINE DEBUG] 💡 提示: 請透過 API 獲取數據或手動執行 CLI 生成檔案
```

### 為什麼 Python 環境可以運作？

**可能的原因**:
1. **本地 JSON 緩存**: 開發環境中可能有之前生成的 `throttle_ratio_*.json` 檔案
2. **工作目錄差異**: Python 直接執行時可能在不同的工作目錄
3. **調試模式**: 開發時可能手動執行過 CLI 命令生成數據

**EXE 環境為什麼失效**:
1. **完全乾淨環境**: EXE 打包後沒有任何 JSON 緩存
2. **API-ONLY 模式**: 禁止 CLI 調用，必須依賴 API
3. **沒有 API 支援**: Line Chart Data Loader 完全沒有 API 邏輯
4. **結果**: 無數據來源 → 完全失效

---

## 🛠️ 解決方案

### 方案 A: 最小修改（推薦）
**目標**: 僅修改 `AnalysisConfig`，利用 `UniversalDataLoader` 基類的 API 支援

**優點**:
- 最小程式碼變更（約 10 行）
- 利用現有基礎設施
- 與 Box Plot 保持一致

**實施步驟**:

#### 1. 更新 `throttle_line_chart_data_loader.py`

```python
# 在 Line 25-35 的 config 創建處修改

class ThrottleLineChartDataLoader(UniversalDataLoader):
    def __init__(self, parent: Optional[QObject] = None):
        if _ANALYSIS_KEY not in UniversalDataLoader.ANALYSIS_TYPES:
            config = AnalysisConfig(
                display_name="Throttle Line Chart (Single Driver)",
                debug_prefix="THROTTLE-LINE",
                data_source="api",  # 🔧 FIX: 改為 "api"
                cli_function="54",
                api_endpoint="/api/v2/analysis/execute",  # ✅ 新增
                api_function_id=54,  # ✅ 新增
                api_timeout=90.0,  # ✅ 新增
                file_patterns=[
                    "throttle_ratio_{year}_{race}_{session}.json",
                    "throttle_ratio_{year}_{race}_{session}_*.json",
                ],
                search_directories=["json", "json_exports", "cache"],  # ✅ 新增
                supports_realtime=False,  # ✅ 新增
                cache_enabled=True,  # ✅ 新增
            )
            UniversalDataLoader.register_analysis_type(_ANALYSIS_KEY, config)

        super().__init__(_ANALYSIS_KEY, parent)
        # ... 其餘代碼不變
```

#### 2. 驗證 `UniversalDataLoader` 基類支援

檢查 `universal_data_loader_base.py` 是否已實現：
- ✅ `load_data()` API 調用邏輯
- ✅ API Worker 執行緒
- ✅ 成功/失敗回調處理
- ✅ JSON 後備機制

### 方案 B: 完全實現（備用）
**目標**: 仿照 Box Plot 實現完整的 API Worker

**優點**:
- 完全控制 API 調用流程
- 可自訂 API 參數和錯誤處理

**缺點**:
- 程式碼重複（~150 行）
- 維護成本高

**實施步驟**:

#### 1. 創建 `ThrottleLineChartApiWorker`

```python
# 在 throttle_line_chart_data_loader.py 開頭添加

import time
import requests
from PyQt5.QtCore import QThread, pyqtSignal

class ThrottleLineChartApiWorker(QThread):
    """背景工作執行緒，呼叫 REST API 取得油門分析資料。"""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 90.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip("/")
        self.params = dict(params)
        self.timeout = timeout

    def run(self) -> None:
        try:
            self.progress.emit(15)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 54,
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True

            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
            self.progress.emit(65)
            response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be a JSON object")
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API returned success=False"))

            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API response missing 'data' object")

            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            meta = {
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }

            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
        except Exception as exc:
            self.failure.emit(str(exc))
        finally:
            self.progress.emit(100)
```

#### 2. 覆寫 `load_data()`

```python
def load_data(self, **kwargs) -> bool:
    """優先使用 API，失敗時回退到本地 JSON"""
    
    # 1. 驗證參數
    if not self._validate_load_parameters(kwargs):
        self._error("載入參數驗證失敗")
        self.load_error.emit("載入參數不正確")
        return False
    
    # 2. 檢查是否正在載入
    if self._is_loading:
        self._debug("已有載入請求執行中，忽略新的請求")
        return False
    
    # 3. 標記載入狀態
    self._is_loading = True
    self._pending_params = dict(kwargs)
    
    # 4. 決定 API Base URL
    from core.api_base_url import resolve_api_base_url
    self._api_base_url = resolve_api_base_url(event_logger=self._debug)
    
    # 5. 啟動 API 請求
    self._debug(f"透過 API 載入油門資料: base_url={self._api_base_url}, params={self._pending_params}")
    self.load_progress.emit(5)
    self.status_changed.emit("正在透過 API 載入油門分析資料...")
    
    try:
        self._start_api_request(self._pending_params)
        return True
    except Exception as exc:
        self._error(f"啟動 API 請求失敗: {exc}")
        self._is_loading = False
        self.status_changed.emit("API 載入失敗，改用本地資料")
        # 回退到基類的 JSON 載入
        return super().load_data(**kwargs)

def _start_api_request(self, params: Dict[str, Any]) -> None:
    """啟動 API 請求執行緒"""
    if self._api_worker is not None and self._api_worker.isRunning():
        self._debug("停止現有 API 工作")
        self._api_worker.quit()
        self._api_worker.wait(1000)
    
    self._api_worker = ThrottleLineChartApiWorker(
        base_url=self._api_base_url,
        params=params,
        timeout=90.0,
        parent=self
    )
    self._api_worker.progress.connect(self.load_progress.emit)
    self._api_worker.success.connect(self._on_api_success)
    self._api_worker.failure.connect(self._on_api_failure)
    self._api_worker.finished.connect(self._on_api_finished)
    self._api_worker.start()

def _on_api_success(self, payload: Dict[str, Any]) -> None:
    """API 成功回調"""
    try:
        self._debug("========== API 成功回調 ==========")
        data = payload.get("data")
        meta = payload.get("meta", {})
        
        # 驗證和處理數據
        if not self._validate_data_format(data):
            raise ValueError("API 返回數據格式無效")
        
        processed_data = self._process_data(data)
        
        # 發送成功信號
        self._debug("✅ 數據處理完成，準備發送 data_loaded 信號")
        self.data_loaded.emit(processed_data)
        self.status_changed.emit(f"已透過 API 載入數據 (延遲: {meta.get('latency_ms', 'N/A')} ms)")
        
    except Exception as exc:
        self._error(f"處理 API 數據失敗: {exc}")
        self.load_error.emit(f"數據處理失敗: {exc}")
    finally:
        self._is_loading = False
        self._debug("========== API 成功回調結束 ==========")

def _on_api_failure(self, error_message: str) -> None:
    """API 失敗回調"""
    self._error(f"API 請求失敗: {error_message}")
    self.load_error.emit(f"API 載入失敗: {error_message}")
    self._is_loading = False
    
    # 嘗試本地 JSON 後備
    self._debug("嘗試使用本地 JSON 後備")
    super().load_data(**self._pending_params)

def _on_api_finished(self) -> None:
    """API 工作執行緒結束"""
    if self._api_worker:
        self._api_worker.deleteLater()
        self._api_worker = None
```

---

## 🔧 實施建議

### 優先方案：方案 A（最小修改）

**理由**:
1. `UniversalDataLoader` 基類已實現完整的 API 調用邏輯
2. Box Plot 證明這個架構是可行的
3. 最小程式碼變更，降低引入 bug 的風險
4. 維護成本最低

**步驟**:
1. 修改 `throttle_line_chart_data_loader.py` 的 `AnalysisConfig`
2. 測試 Python 環境
3. 重新打包 EXE
4. 測試 EXE 環境

**預計工作時間**: 30 分鐘

### 備用方案：方案 B（完全實現）

**使用時機**: 如果基類不支援或需要自訂 API 行為

**步驟**:
1. 實現 `ThrottleLineChartApiWorker`
2. 覆寫 `load_data()` 和回調方法
3. 完整測試
4. 重新打包

**預計工作時間**: 2-3 小時

---

## 📊 影響範圍

### 修改檔案
- `throttle_line_chart_data_loader.py` - 核心修復

### 受影響模組
- Throttle Line Chart (Single Driver) - 主要受益
- 所有使用 `ThrottleLineChartDataLoader` 的模組

### 不受影響
- Throttle Box Plot - 已正常運作
- 其他分析模組 - 獨立運作

---

## ✅ 測試計畫

### 單元測試
1. API 調用成功
2. API 調用失敗 → JSON 後備
3. 參數驗證
4. 數據格式驗證

### Python 環境測試
1. Throttle Line Chart 開啟正常
2. 車手選擇功能正常
3. 曲線圖正確顯示
4. Driver 2 可選可空

### EXE 環境測試
1. ✅ 啟動無錯誤
2. ✅ Throttle Line Chart 開啟
3. ✅ API 調用成功（檢查日誌）
4. ✅ 車手列表正確載入
5. ✅ 曲線圖正確渲染
6. ✅ 與 Box Plot 並列測試

---

## 🚀 下一步行動

1. **立即修復**: 實施方案 A
2. **測試驗證**: Python + EXE 雙環境
3. **文檔更新**: 更新架構說明
4. **預防措施**: 添加自動化測試

---

**修復者**: GitHub Copilot  
**最後更新**: 2025-10-08 22:15  
**優先級**: 🔴 P0 (CRITICAL)
