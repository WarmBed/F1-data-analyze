# 🏁 Pitstop Analysis API 調用 CLI Function 映射表

> **查詢日期**: 2025-10-25  
> **模組**: Pitstop Analysis  
> **檔案**: `modules/gui/pitstop_analysis/pitstop_analysis_mdi.py`

---

## 📊 Pitstop Analysis 使用的 CLI Functions

Pitstop Analysis 模組共使用 **3 個 CLI Functions**，對應不同的分析功能：

| 分析類型 | CLI Function ID | 描述 | API Endpoint |
|---------|----------------|------|--------------|
| **車手進站分析** | **Function 3** | 車手最快進站時間排行榜 | `/api/v2/analysis/execute?function_id=3` |
| **車隊進站分析** | **Function 4** | 車隊進站策略和統計 | `/api/v2/analysis/execute?function_id=4` |
| **車手詳細進站** | **Function 5** | 車手每次進站的詳細記錄 | `/api/v2/analysis/execute?function_id=5` |

---

## 🔍 詳細調用代碼

### 1. **車手進站分析 (Function 3)**

**檔案位置**: `pitstop_analysis_mdi.py` Line 816

```python
self._start_api_request(
    "driver",
    function_id=3,  # ✅ CLI Function 3
    params=self._driver_params,
    label="車手進站分析",
)
```

**API 請求範例**:
```python
POST https://api.f1telemetrystationpro.org/api/v2/analysis/execute
Params:
{
    "function_id": 3,
    "year": 2025,
    "race": "China",
    "session": "R"
}
```

**數據格式**:
```json
{
    "success": true,
    "data": {
        "function_id": 3,
        "analysis_type": "driver_pitstop_ranking",
        "drivers": [
            {
                "driver": "VER",
                "team": "Red Bull Racing",
                "fastest_pitstop": 2.145,
                "average_pitstop": 2.387,
                "total_pitstops": 2
            },
            ...
        ]
    }
}
```

---

### 2. **車隊進站分析 (Function 4)**

**檔案位置**: `pitstop_analysis_mdi.py` Line 923

```python
self._start_api_request(
    "team",
    function_id=4,  # ✅ CLI Function 4
    params=self._team_params,
    label="車隊進站分析",
)
```

**API 請求範例**:
```python
POST https://api.f1telemetrystationpro.org/api/v2/analysis/execute
Params:
{
    "function_id": 4,
    "year": 2025,
    "race": "China",
    "session": "R"
}
```

**數據格式**:
```json
{
    "success": true,
    "data": {
        "function_id": 4,
        "analysis_type": "team_pitstop_strategy",
        "teams": [
            {
                "team": "Red Bull Racing",
                "avg_pitstop_time": 2.456,
                "fastest_pitstop": 2.145,
                "total_pitstops": 4,
                "strategy": "2-stop"
            },
            ...
        ]
    }
}
```

**數據驗證**:
```python
# Line 965-967
if data.get("function_id") != 4:
    print(f"[ERROR] [VALIDATE] 車隊數據 function_id 不匹配: {data.get('function_id')}")
```

---

### 3. **車手詳細進站 (Function 5)**

**檔案位置**: `pitstop_analysis_mdi.py` Line 1102

```python
self._start_api_request(
    "detail",
    function_id=5,  # ✅ CLI Function 5
    params=self._detail_params,
    label="車手進站詳細分析",
)
```

**API 請求範例**:
```python
POST https://api.f1telemetrystationpro.org/api/v2/analysis/execute
Params:
{
    "function_id": 5,
    "year": 2025,
    "race": "China",
    "session": "R"
}
```

**數據格式**:
```json
{
    "success": true,
    "data": {
        "function_id": 5,
        "analysis_type": "driver_pitstop_details",
        "driver_details": {
            "VER": {
                "pitstops": [
                    {
                        "lap": 15,
                        "time": 2.145,
                        "duration": 25.3,
                        "tyre_change": "MEDIUM -> SOFT"
                    },
                    {
                        "lap": 35,
                        "time": 2.387,
                        "duration": 26.1,
                        "tyre_change": "SOFT -> HARD"
                    }
                ]
            },
            ...
        }
    }
}
```

**數據驗證**:
```python
# Line 1148-1149
elif data.get("function_id") == 5:
    # 檢查舊格式：{ "function_id": 5, "data": {...} }
```

---

## 🔌 API Worker 實現

### `PitstopAnalysisApiWorker` 類別

**檔案位置**: `pitstop_analysis_mdi.py` Line 47

```python
class PitstopAnalysisApiWorker(QThread):
    """Background worker for pitstop-related API calls."""

    progress = pyqtSignal(int, str)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(
        self,
        base_url: str,
        function_id: int,  # ✅ 接收 CLI Function ID
        params: Dict[str, Any],
        label: str,
        timeout: float = 45.0,
        parent=None,
    ):
        super().__init__(parent)
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.function_id = int(function_id)  # ✅ 保存 Function ID
        self.params = dict(params)
        self.label = label
        self.timeout = timeout

    def run(self) -> None:
        try:
            self.progress.emit(15, f"呼叫 API 取得{self.label}資料...")
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": self.function_id,  # ✅ 傳遞給 API
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            # ... API 調用邏輯
```

---

## 🎯 調用流程圖

```
用戶操作 (GUI)
    ↓
PitstopAnalysisModule._load_driver_data()
    ↓
PitstopDataManager._load_driver_pitstop()
    ↓
_start_api_request("driver", function_id=3, ...)  ✅ Function 3
    ↓
PitstopAnalysisApiWorker.run()
    ↓
POST https://api.f1telemetrystationpro.org/api/v2/analysis/execute?function_id=3
    ↓
API Server (refactored_api.py)
    ↓
SimpleF1AnalysisService.execute_analysis()
    ↓
CLI Function Mapper (F1AnalysisFunctionMapper)
    ↓
function_mapping[3]()  → _execute_driver_pitstop()
    ↓
CLI 分析邏輯執行
    ↓
返回 JSON 結果
    ↓
GUI 顯示數據
```

---

## 📋 CLI Function Mapper 對應

根據 `CLI_modules/cli/core/function_mapper.py`：

```python
function_mapping = {
    # ... 其他功能
    3: self._execute_driver_pitstop,      # ✅ 車手進站排行榜
    4: self._execute_team_pitstop,        # ✅ 車隊進站策略
    5: self._execute_driver_pitstop_detail,  # ✅ 車手詳細進站記錄
    # ... 其他功能
}
```

---

## 🧪 測試指令

### CLI 手動測試

```powershell
# Function 3: 車手進站分析
python f1_analysis_modular_main.py -f 3 -y 2025 -r China -s R

# Function 4: 車隊進站分析
python f1_analysis_modular_main.py -f 4 -y 2025 -r China -s R

# Function 5: 車手詳細進站
python f1_analysis_modular_main.py -f 5 -y 2025 -r China -s R
```

### API 手動測試

```powershell
# Function 3
curl -X POST "https://api.f1telemetrystationpro.org/api/v2/analysis/execute?function_id=3&year=2025&race=China&session=R"

# Function 4
curl -X POST "https://api.f1telemetrystationpro.org/api/v2/analysis/execute?function_id=4&year=2025&race=China&session=R"

# Function 5
curl -X POST "https://api.f1telemetrystationpro.org/api/v2/analysis/execute?function_id=5&year=2025&race=China&session=R"
```

---

## 🔄 Fallback 機制

如果 API 不可用，Pitstop Analysis 會回退到**本地 JSON 檔案**：

### 本地檔案搜索模式

```python
# Function 3: 車手進站
json/driver_pitstop_ranking_{year}_{race}_{session}_*.json

# Function 4: 車隊進站
json/team_pitstop_strategy_{year}_{race}_{session}_*.json

# Function 5: 車手詳細進站
json/driver_pitstop_details_{year}_{race}_{session}_*.json
```

---

## 📊 摘要表

| GUI 分析類型 | CLI Function | API Endpoint | 本地 JSON 模式 | 超時時間 |
|-------------|-------------|--------------|---------------|---------|
| Driver Pitstop Ranking | **3** | `/api/v2/analysis/execute?function_id=3` | `driver_pitstop_ranking_*.json` | 45s |
| Team Pitstop Strategy | **4** | `/api/v2/analysis/execute?function_id=4` | `team_pitstop_strategy_*.json` | 45s |
| Driver Pitstop Details | **5** | `/api/v2/analysis/execute?function_id=5` | `driver_pitstop_details_*.json` | 45s |

---

## 🔧 相關檔案

| 檔案 | 作用 |
|------|------|
| `modules/gui/pitstop_analysis/pitstop_analysis_mdi.py` | GUI 主模組（API 調用） |
| `CLI_modules/cli/core/function_mapper.py` | CLI 功能映射器 |
| `CLI_modules/cli/analyzer/pitstop_analysis.py` | CLI 進站分析實現 |
| `api/routers/analysis.py` | API 路由處理 |
| `api/services/simple_analysis_service.py` | API 服務層 |

---

**最後更新**: 2025-10-25  
**驗證狀態**: ✅ 已通過代碼驗證  
**數據來源**: 實際代碼分析
