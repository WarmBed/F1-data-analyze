# GUI資料來源切換設計文件

## 概覽

本設計文件詳細描述F1 GUI資料來源切換功能的技術架構，實現本地模式與API模式之間的無縫切換，確保使用者體驗一致性和系統可靠性。

## 架構設計

### 整體架構原則

1. **抽象化資料存取**
   - 透過ServiceAdapter介面統一資料存取
   - GUI層與具體資料來源解耦
   - 支援未來擴展其他資料來源

2. **保持向後相容**
   - 現有GUI功能完全不變
   - 現有資料格式和API保持一致
   - 漸進式重構，降低風險

3. **智慧切換機制**
   - 自動健康檢查和故障偵測
   - 智慧fallback和錯誤恢復
   - 使用者友善的切換體驗

## 核心組件設計

### 1. ServiceAdapter抽象介面

#### 設計目標
- 提供統一的資料存取介面
- 封裝不同資料來源的實現細節
- 支援非同步操作和進度回報

#### 介面設計
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class DataSourceType(Enum):
    LOCAL = "local"
    API = "api"

@dataclass
class AnalysisRequest:
    """分析請求參數"""
    function_id: str
    year: int
    race: str
    session: str
    parameters: Optional[Dict[str, Any]] = None

@dataclass
class AnalysisResponse:
    """統一的分析回應格式"""
    success: bool
    data: Optional[Dict[str, Any]]
    source: str  # "local-cache", "local-cli", "api"
    message: str
    error: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: Optional[str] = None

class ServiceAdapter(ABC):
    """資料來源服務適配器抽象基類"""
    
    @abstractmethod
    async def execute_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """執行分析並返回結果"""
        pass
    
    @abstractmethod
    async def list_functions(self) -> AnalysisResponse:
        """列出可用的分析功能"""
        pass
    
    @abstractmethod
    async def health_check(self) -> AnalysisResponse:
        """檢查資料來源健康狀態"""
        pass
    
    @abstractmethod
    def get_source_type(self) -> DataSourceType:
        """獲取資料來源類型"""
        pass
```

### 2. LocalDataSource實現

#### 設計目標
- 整合現有的快取服務和CLI執行邏輯
- 保持現有的「快取優先，CLI備援」流程
- 提供詳細的執行狀態和錯誤資訊

#### 實現設計
```python
import asyncio
from pathlib import Path
from typing import Dict, Any
import json
import subprocess
import time

class LocalDataSource(ServiceAdapter):
    """本地資料來源實現"""
    
    def __init__(self, cache_service=None):
        self.cache_service = cache_service or F1AnalysisCacheService()
        self.cli_timeout = 300  # 5分鐘超時
        
    async def execute_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """執行本地分析"""
        start_time = time.time()
        
        try:
            # 步驟1: 搜尋快取
            cached_result = await self._search_cache(request)
            if cached_result:
                return AnalysisResponse(
                    success=True,
                    data=cached_result,
                    source="local-cache",
                    message="從本地快取載入",
                    execution_time=time.time() - start_time
                )
            
            # 步驟2: 執行CLI生成
            cli_result = await self._execute_cli(request)
            if cli_result:
                # 步驟3: 重新讀取生成的檔案
                new_result = await self._search_cache(request)
                if new_result:
                    return AnalysisResponse(
                        success=True,
                        data=new_result,
                        source="local-cli",
                        message="CLI執行成功並載入結果",
                        execution_time=time.time() - start_time
                    )
            
            return AnalysisResponse(
                success=False,
                data=None,
                source="local-cli",
                message="CLI執行失敗或未產生結果檔案",
                error="分析執行失敗",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AnalysisResponse(
                success=False,
                data=None,
                source="local-error",
                message="本地分析執行異常",
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _search_cache(self, request: AnalysisRequest) -> Optional[Dict[str, Any]]:
        """搜尋快取檔案"""
        # 整合現有的F1AnalysisCacheService邏輯
        pass
    
    async def _execute_cli(self, request: AnalysisRequest) -> bool:
        """執行CLI命令"""
        cmd = [
            "python", "f1_analysis_modular_main.py",
            "-f", request.function_id,
            "-y", str(request.year),
            "-r", request.race,
            "-s", request.session
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=self.cli_timeout
            )
            
            stdout, stderr = await process.communicate()
            return process.returncode == 0
            
        except asyncio.TimeoutError:
            return False
        except Exception:
            return False
```

### 3. ApiClient和ApiDataSource實現

#### ApiClient設計
```python
import aiohttp
import asyncio
from typing import Dict, Any, Optional
import json

class ApiClient:
    """API客戶端"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def post_analysis_execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行分析API呼叫"""
        url = f"{self.base_url}/analysis/execute"
        
        async with self.session.post(url, json=request_data) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_detail = await response.text()
                raise ApiError(f"API呼叫失敗: {response.status} - {error_detail}")
    
    async def get_analysis_functions(self) -> Dict[str, Any]:
        """獲取可用功能列表"""
        url = f"{self.base_url}/analysis/functions"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise ApiError(f"獲取功能列表失敗: {response.status}")
    
    async def get_analysis_status(self) -> Dict[str, Any]:
        """獲取API狀態"""
        url = f"{self.base_url}/analysis/status"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise ApiError(f"健康檢查失敗: {response.status}")

class ApiError(Exception):
    """API錯誤異常"""
    pass
```

#### ApiDataSource設計
```python
class ApiDataSource(ServiceAdapter):
    """API資料來源實現"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        
    async def execute_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """透過API執行分析"""
        start_time = time.time()
        
        try:
            async with ApiClient(self.base_url, self.timeout) as client:
                request_data = {
                    "function_id": request.function_id,
                    "year": request.year,
                    "race": request.race,
                    "session": request.session,
                    "parameters": request.parameters or {}
                }
                
                api_response = await client.post_analysis_execute(request_data)
                
                return AnalysisResponse(
                    success=api_response.get("success", False),
                    data=api_response.get("data"),
                    source="api",
                    message=api_response.get("message", "API執行完成"),
                    error=api_response.get("error"),
                    execution_time=time.time() - start_time
                )
                
        except ApiError as e:
            return AnalysisResponse(
                success=False,
                data=None,
                source="api",
                message="API呼叫失敗",
                error=str(e),
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return AnalysisResponse(
                success=False,
                data=None,
                source="api",
                message="API執行異常",
                error=str(e),
                execution_time=time.time() - start_time
            )
```

### 4. GUI整合設計

#### DataSourceManager設計
```python
from typing import Optional
from enum import Enum

class DataSourceManager:
    """資料來源管理器"""
    
    def __init__(self):
        self.current_adapter: Optional[ServiceAdapter] = None
        self.current_type: Optional[DataSourceType] = None
        self.config = self._load_config()
        
    def switch_to_local(self) -> bool:
        """切換到本地模式"""
        try:
            self.current_adapter = LocalDataSource()
            self.current_type = DataSourceType.LOCAL
            self._save_config_preference(DataSourceType.LOCAL)
            return True
        except Exception as e:
            print(f"切換到本地模式失敗: {e}")
            return False
    
    async def switch_to_api(self, base_url: str) -> bool:
        """切換到API模式"""
        try:
            # 先進行健康檢查
            test_adapter = ApiDataSource(base_url)
            health_result = await test_adapter.health_check()
            
            if health_result.success:
                self.current_adapter = test_adapter
                self.current_type = DataSourceType.API
                self._save_config_preference(DataSourceType.API, base_url)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"切換到API模式失敗: {e}")
            return False
    
    async def execute_analysis_with_fallback(self, request: AnalysisRequest) -> AnalysisResponse:
        """執行分析，支援自動fallback"""
        if not self.current_adapter:
            # 預設使用本地模式
            self.switch_to_local()
        
        try:
            result = await self.current_adapter.execute_analysis(request)
            
            # 如果API模式失敗，自動fallback到本地模式
            if not result.success and self.current_type == DataSourceType.API:
                print("API模式失敗，自動切換到本地模式")
                self.switch_to_local()
                result = await self.current_adapter.execute_analysis(request)
                result.message += " (已自動切換到本地模式)"
            
            return result
            
        except Exception as e:
            # 發生異常時也嘗試fallback
            if self.current_type == DataSourceType.API:
                print(f"API模式異常，嘗試本地模式: {e}")
                self.switch_to_local()
                return await self.current_adapter.execute_analysis(request)
            else:
                raise
```

### 5. 模式切換UI設計

#### 設定管理
```python
import json
from pathlib import Path
from typing import Dict, Any, Optional

class DataSourceConfig:
    """資料來源配置管理"""
    
    def __init__(self, config_file: str = "data_source_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置檔案"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "default_source": "local",
            "api_settings": {
                "base_url": "http://localhost:8000",
                "timeout": 30,
                "retry_count": 3
            },
            "local_settings": {
                "cache_directory": "json",
                "cli_timeout": 300
            },
            "ui_settings": {
                "show_source_indicator": True,
                "auto_fallback": True,
                "health_check_interval": 60
            }
        }
    
    def save_config(self):
        """儲存配置到檔案"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
```

#### GUI切換控件
```python
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QLineEdit, QGroupBox, QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal, QTimer

class DataSourceSwitchWidget(QWidget):
    """資料來源切換控件"""
    
    source_changed = pyqtSignal(str)  # 資料來源變更信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_source_manager = DataSourceManager()
        self.setup_ui()
        self.setup_health_check_timer()
    
    def setup_ui(self):
        """設置UI"""
        layout = QHBoxLayout(self)
        
        # 資料來源選擇
        self.source_combo = QComboBox()
        self.source_combo.addItems(["本地模式", "API模式"])
        self.source_combo.currentTextChanged.connect(self.on_source_changed)
        
        # API URL輸入
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("API Base URL")
        self.api_url_input.setText("http://localhost:8000")
        
        # 狀態指示器
        self.status_label = QLabel("本地模式")
        self.status_label.setStyleSheet("color: green;")
        
        # 健康檢查按鈕
        self.health_check_btn = QPushButton("檢查狀態")
        self.health_check_btn.clicked.connect(self.manual_health_check)
        
        layout.addWidget(QLabel("資料來源:"))
        layout.addWidget(self.source_combo)
        layout.addWidget(self.api_url_input)
        layout.addWidget(self.status_label)
        layout.addWidget(self.health_check_btn)
    
    def setup_health_check_timer(self):
        """設置健康檢查定時器"""
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.auto_health_check)
        self.health_timer.start(60000)  # 每分鐘檢查一次
    
    async def on_source_changed(self, source_text: str):
        """處理資料來源變更"""
        if source_text == "本地模式":
            success = self.data_source_manager.switch_to_local()
            if success:
                self.status_label.setText("本地模式")
                self.status_label.setStyleSheet("color: green;")
                self.api_url_input.setEnabled(False)
        
        elif source_text == "API模式":
            self.api_url_input.setEnabled(True)
            api_url = self.api_url_input.text()
            success = await self.data_source_manager.switch_to_api(api_url)
            
            if success:
                self.status_label.setText("API模式 (已連線)")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText("API模式 (連線失敗)")
                self.status_label.setStyleSheet("color: red;")
                # 提供fallback選項
                self.show_fallback_dialog()
        
        self.source_changed.emit(source_text)
    
    def show_fallback_dialog(self):
        """顯示fallback對話框"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, "API連線失敗",
            "無法連線到API伺服器，是否切換回本地模式？",
            QMessageBox.Yes | QMessageBox.Retry | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            self.source_combo.setCurrentText("本地模式")
        elif reply == QMessageBox.Retry:
            # 重新嘗試連線
            asyncio.create_task(self.on_source_changed("API模式"))
```

## 錯誤處理設計

### 統一錯誤處理機制
```python
from enum import Enum
from typing import Dict, Any, Optional

class ErrorType(Enum):
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    API_ERROR = "api_error"
    CLI_ERROR = "cli_error"
    CACHE_ERROR = "cache_error"
    CONFIG_ERROR = "config_error"

class ErrorHandler:
    """統一錯誤處理器"""
    
    ERROR_MESSAGES = {
        ErrorType.NETWORK_ERROR: "網路連線失敗，請檢查網路設定",
        ErrorType.TIMEOUT_ERROR: "操作超時，請稍後再試",
        ErrorType.API_ERROR: "API服務異常，請聯繫管理員",
        ErrorType.CLI_ERROR: "本地分析執行失敗",
        ErrorType.CACHE_ERROR: "快取檔案讀取失敗",
        ErrorType.CONFIG_ERROR: "配置檔案錯誤"
    }
    
    @staticmethod
    def handle_error(error_type: ErrorType, details: str = "") -> str:
        """處理錯誤並返回使用者友善訊息"""
        base_message = ErrorHandler.ERROR_MESSAGES.get(
            error_type, "未知錯誤"
        )
        
        if details:
            return f"{base_message}: {details}"
        else:
            return base_message
    
    @staticmethod
    def suggest_recovery_action(error_type: ErrorType) -> str:
        """建議恢復操作"""
        suggestions = {
            ErrorType.NETWORK_ERROR: "請檢查網路連線或切換到本地模式",
            ErrorType.TIMEOUT_ERROR: "請稍後重試或調整超時設定",
            ErrorType.API_ERROR: "請切換到本地模式或聯繫管理員",
            ErrorType.CLI_ERROR: "請檢查本地環境或重新安裝",
            ErrorType.CACHE_ERROR: "請清理快取或重新生成數據",
            ErrorType.CONFIG_ERROR: "請檢查配置檔案或重置為預設值"
        }
        
        return suggestions.get(error_type, "請聯繫技術支援")
```

## 測試策略

### 單元測試設計
```python
import pytest
import asyncio
from unittest.mock import Mock, patch

class TestLocalDataSource:
    """LocalDataSource單元測試"""
    
    @pytest.fixture
    def local_source(self):
        return LocalDataSource()
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, local_source):
        """測試快取命中情境"""
        # Mock快取服務返回數據
        with patch.object(local_source, '_search_cache') as mock_search:
            mock_search.return_value = {"test": "data"}
            
            request = AnalysisRequest("1", 2024, "Japan", "R")
            result = await local_source.execute_analysis(request)
            
            assert result.success is True
            assert result.source == "local-cache"
            assert result.data == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_cache_miss_cli_success(self, local_source):
        """測試快取未命中但CLI成功情境"""
        with patch.object(local_source, '_search_cache') as mock_search, \
             patch.object(local_source, '_execute_cli') as mock_cli:
            
            # 第一次搜尋快取失敗，CLI執行成功，第二次搜尋成功
            mock_search.side_effect = [None, {"cli": "generated"}]
            mock_cli.return_value = True
            
            request = AnalysisRequest("1", 2024, "Japan", "R")
            result = await local_source.execute_analysis(request)
            
            assert result.success is True
            assert result.source == "local-cli"
            assert result.data == {"cli": "generated"}

class TestApiDataSource:
    """ApiDataSource單元測試"""
    
    @pytest.fixture
    def api_source(self):
        return ApiDataSource("http://test-api.com")
    
    @pytest.mark.asyncio
    async def test_api_success(self, api_source):
        """測試API成功情境"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {"api": "result"},
                "message": "成功"
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            request = AnalysisRequest("1", 2024, "Japan", "R")
            result = await api_source.execute_analysis(request)
            
            assert result.success is True
            assert result.source == "api"
            assert result.data == {"api": "result"}
```

### 整合測試設計
```python
class TestDataSourceIntegration:
    """資料來源整合測試"""
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self):
        """測試自動fallback機制"""
        manager = DataSourceManager()
        
        # 設置API模式但API不可用
        with patch.object(ApiDataSource, 'execute_analysis') as mock_api:
            mock_api.side_effect = Exception("API不可用")
            
            # 設置本地模式可用
            with patch.object(LocalDataSource, 'execute_analysis') as mock_local:
                mock_local.return_value = AnalysisResponse(
                    success=True, data={"fallback": "success"}, 
                    source="local-cache", message="fallback成功"
                )
                
                await manager.switch_to_api("http://unavailable-api.com")
                request = AnalysisRequest("1", 2024, "Japan", "R")
                result = await manager.execute_analysis_with_fallback(request)
                
                assert result.success is True
                assert "fallback" in result.message
                assert manager.current_type == DataSourceType.LOCAL
```

## 部署和維護

### 配置管理
- 支援環境變數覆寫配置
- 提供配置檔案範本和驗證
- 支援熱重載配置更新

### 監控和日誌
- 記錄資料來源切換事件
- 監控API健康狀態和響應時間
- 提供詳細的錯誤診斷日誌

### 效能優化
- 實現連線池和請求快取
- 優化CLI執行和檔案讀取
- 支援批次操作和並行處理

這個設計確保了系統的可靠性、可維護性和使用者體驗，同時保持了與現有系統的完全相容性。