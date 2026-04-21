#!/usr/bin/env python3
"""
FIA Parts Analysis MDI 視窗
FIA Parts Analysis MDI Window

負責管理 FIA 部件變更分析的 MDI 視窗，整合 API 資料載入和表格元件

作者: F1T Team
日期: 2025-11-08
版本: 1.0.0
"""

import sys
import time
import requests
import certifi
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QProgressBar, QLabel,
    QApplication, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal

from core.gui_i18n import tr

# 導入基類
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

from core.logger import get_logger
logger = get_logger(__name__)




class PartsAnalysisApiWorker(QThread):
    """
    Parts Analysis API 請求工作執行緒
    
    負責異步調用 API 獲取 FIA Parts Analysis 數據
    API 端點: POST /api/v2/analysis/execute?function_id=29
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        """
        初始化 API Worker
        
        Args:
            params: API 參數 (year, team, driver, race, etc.)
            base_url: API 基礎 URL (預設: http://localhost:8000)
            timeout: 請求超時時間（秒）
        """
        super().__init__()
        self.base_url = (base_url or "http://localhost:8000").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        """執行 API 請求"""
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            # 構建查詢參數
            query_params: Dict[str, Any] = {
                "function_id": 29,  # CLI Function 29 - FIA Parts Analysis V2.0
                "year": int(self.params.get("year")),
            }
            
            # 可選參數
            if self.params.get("team"):
                query_params["team"] = self.params["team"]
            if self.params.get("driver"):
                query_params["driver"] = self.params["driver"]
            if self.params.get("race"):
                query_params["race"] = self.params["race"]
            if self.params.get("change_type"):
                query_params["change_type"] = self.params["change_type"]
            if self.params.get("min_confidence") is not None:
                query_params["min_confidence"] = float(self.params["min_confidence"])
            if self.params.get("exclude_noise") is not None:
                query_params["exclude_noise"] = bool(self.params["exclude_noise"])
            
            # 強制刷新（可選）
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            logger.info("[API_WORKER] 🌐 調用 API: %s", endpoint)
            logger.info("[API_WORKER] 📋 參數: %s", query_params)
            
            # ✅ 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                return
            
            # 發送 POST 請求
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
            )
            self.progress.emit(70)
            
            # ✅ 中斷檢查點 3: HTTP 請求後
            if self.isInterruptionRequested():
                return
            
            # 檢查 HTTP 狀態
            response.raise_for_status()
            
            # 解析 JSON 回應
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API 回應必須是 JSON 物件")
            
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API 返回 success=False"))
            
            # 提取數據
            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API 回應缺少 'data' 物件")
            
            # 計算延遲
            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            
            # 構建元數據
            meta = {
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }
            
            logger.info("[API_WORKER] ✅ API 調用成功")
            logger.info("[API_WORKER] ⏱️  延遲: %sms", meta["latency_ms"])
            logger.info("[API_WORKER] 📊 數據源: %s", meta["source"])
            
            self.progress.emit(90)
            # ✅ 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                return
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API 請求失敗: {str(exc)}"
            logger.exception("[API_WORKER] ❌ %s", error_msg)
            self.failure.emit(error_msg)
        finally:
            # ✅ 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


try:
    from .parts_analysis_widget import PartsAnalysisWidget
except ImportError:
    from parts_analysis_widget import PartsAnalysisWidget


class PartsAnalysisMDI(UniversalAnalysisMDI):
    """
    FIA Parts Analysis MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 API 資料載入和表格元件，完全基於 API，不使用本地 JSON 讀取
    """
    
    # 在類別層級註冊模組類型
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="parts_analysis",
                display_name="FIA Parts Analysis",
                default_size=(1200, 700),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("parts_analysis", config)
            cls._REGISTERED = True
            logger.info("[PARTS_MDI] ✅ 模組類型已註冊")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        logger.info("[PARTS_MDI] PartsAnalysisMDI 開始初始化...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="parts_analysis", parent=parent)
        
        # 初始化參數（將在 initialize_module 中設置）
        self.year = None
        self.api_base_url = "http://localhost:8000"
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        logger.debug("[PARTS_MDI] 基類初始化完成, 等待參數設置...")
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組（UniversalAnalysisMDI 要求的方法）
        
        Args:
            parent_widget: 父元件
            **kwargs: 額外參數
        
        Returns:
            bool: 初始化是否成功
        """
        logger.debug("[PARTS_MDI] initialize_module 被調用, kwargs=%s", kwargs)
        
        # 設置年份參數（在基類初始化之前）
        if hasattr(self, 'parameter_provider') and self.parameter_provider:
            try:
                self.year = str(self.parameter_provider.get_current_year())
                logger.info("[PARTS_MDI] 從 parameter_provider 獲取年份: %s", self.year)
            except Exception as e:
                logger.warning("[PARTS_MDI] ⚠️ 無法從 parameter_provider 獲取年份: %s", e)
                self.year = "2025"
        else:
            self.year = kwargs.get('year', "2025")
        
        logger.info("[PARTS_MDI] 參數設置完成，年份=%s", self.year)
        
        # ✅ 調用基類的 initialize_module()
        # 基類會自動調用：
        # 1. create_data_manager()
        # 2. create_chart_widget()  ← 創建 parts_widget 並載入數據
        # 3. _setup_ui()
        logger.debug("[PARTS_MDI] 調用基類 initialize_module()...")
        result = super().initialize_module(parent_widget, **kwargs)
        logger.info("[PARTS_MDI] 基類 initialize_module() 完成，結果=%s", result)
        
        return result
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self):
        """
        創建資料管理器（由基類調用）
        
        ⚠️ Parts Analysis 使用 API Worker 而非傳統 DataLoader
        返回一個空的 DataLoader 對象以滿足基類要求
        
        Returns:
            PartsAnalysisDummyDataLoader: 空的資料管理器
        """
        logger.debug("[PARTS_MDI] create_data_manager 被調用（Parts Analysis 使用 API Worker）")
        
        # 創建一個空的 DataLoader 對象以滿足基類要求
        # Parts Analysis 不使用傳統 DataLoader，而是使用 API Worker
        class PartsAnalysisDummyDataLoader:
            """空的 DataLoader，Parts Analysis 使用 API Worker"""
            def __init__(self):
                # 基類需要這些信號
                from PyQt5.QtCore import pyqtSignal, QObject
                class DummySignals(QObject):
                    data_loaded = pyqtSignal(dict)
                    error_occurred = pyqtSignal(str)
                    status_changed = pyqtSignal(str)
                self._signals = DummySignals()
                self.data_loaded = self._signals.data_loaded
                self.error_occurred = self._signals.error_occurred
                self.status_changed = self._signals.status_changed
        
        dummy_loader = PartsAnalysisDummyDataLoader()
        logger.info("[PARTS_MDI] ✅ 創建空的 DataLoader（Parts Analysis 使用 API Worker）")
        return dummy_loader
    
    def create_chart_widget(self) -> QWidget:
        """
        創建圖表元件（由基類調用）
        
        Returns:
            PartsAnalysisWidget: 表格元件實例
        """
        logger.info("[PARTS_MDI] 創建 Parts Analysis Widget...")
        # ⚠️ parent 必須傳 None，因為 UniversalAnalysisMDI 不是 QWidget
        self.parts_widget = PartsAnalysisWidget(
            api_base_url=self.api_base_url,
            year=int(self.year) if self.year else 2025,
            parent=None
        )
        logger.info("[PARTS_MDI] ✅ Parts Analysis Widget 已創建")
        
        # 觸發初始數據載入
        self._trigger_initial_load()
        
        return self.parts_widget
    
    def get_widget(self) -> QWidget:
        """
        返回內容元件（UniversalAnalysisMDI 要求的方法）
        
        Returns:
            QWidget: PartsAnalysisWidget 實例，如果尚未創建則返回 None
        """
        if hasattr(self, 'parts_widget') and self.parts_widget:
            return self.parts_widget
        else:
            logger.warning("[PARTS_MDI] ⚠️  parts_widget 尚未創建")
            return None  # ✅ 修正：返回 None 而不是 self
    
    def _setup_ui(self):
        """
        設置 UI - Parts Analysis 只需創建 Widget
        
        ⚠️ PartsAnalysisMDI 不是 QWidget，不能直接設置佈局
        內容通過 create_chart_widget() 提供給基類
        """
        logger.debug("[PARTS_MDI] _setup_ui 被調用...")
        
        # Parts Analysis Widget（已在 create_chart_widget 中創建）
        # 這裡不需要創建，基類會調用 create_chart_widget()
        logger.info("[PARTS_MDI] ⚠️  _setup_ui: Widget 由基類透過 create_chart_widget() 創建")
        pass
    
    def _trigger_initial_load(self):
        """
        觸發初始數據載入 - 強制使用 API
        
        優先級：
        1. API 調用 (http://localhost:8000)
        2. 無備援（API-ONLY 模式）
        """
        logger.info("[PARTS_MDI] 🚀 觸發初始載入: year=%s", self.year)
        
        # 創建 API Worker
        api_params = {
            "year": self.year,
            "exclude_noise": True,  # 排除噪音數據
            "force_refresh": False  # 可選：強制刷新
        }
        
        logger.debug("[PARTS_MDI] 🌐 創建 API Worker...")
        self.api_worker = PartsAnalysisApiWorker(
            params=api_params,
            base_url=self.api_base_url,
            timeout=60.0
        )
        
        # 連接信號
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 啟動 API 請求
        logger.info("[PARTS_MDI] ▶️  啟動 API 請求...")
        self.api_worker.start()
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API 請求進度更新"""
        logger.debug("[PARTS_MDI] 📊 API 進度: %s%%", progress)
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict[str, Any]):
        """API 請求成功"""
        try:
            logger.info("[PARTS_MDI] ✅ API 調用成功")
            
            # API 返回的 data 是完整的 JSON 內容
            api_response = result.get("data", {})
            meta = result.get("meta", {})
            
            logger.info("[PARTS_MDI] 📦 數據源: %s", meta.get("source"))
            logger.info("[PARTS_MDI] ⏱️  延遲: %sms", meta.get("latency_ms"))
            
            # 觸發 Widget 的數據載入
            logger.info("[PARTS_MDI] 📋 傳遞數據到 Widget...")
            if hasattr(self, 'parts_widget') and self.parts_widget:
                self.parts_widget.on_data_loaded(api_response)
            else:
                logger.warning("[PARTS_MDI] ⚠️  parts_widget 尚未創建")
            
        except Exception as e:
            logger.exception("❌ [PARTS_MDI] API 數據處理失敗: %s", e)
            self._on_api_failure(str(e))
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API 請求失敗 - API-ONLY 模式，無備援"""
        logger.error("❌ [PARTS_MDI] API 調用失敗: %s", error_msg)
        
        # 顯示錯誤訊息（需要找到父 Widget）
        parent = self.parts_widget if hasattr(self, 'parts_widget') else None
        QMessageBox.critical(
            parent,
            tr("api_error", "API 錯誤"),
            tr("api_error_message", "無法從 API 載入數據，請檢查網路連接或稍後再試。\n\n錯誤詳情: {}").format(error_msg)
        )


# 測試代碼
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 測試 MDI 視窗
    mdi = PartsAnalysisMDI(year="2025")
    mdi.setWindowTitle(tr('fia_parts_analysis_test', "FIA Parts Analysis Test"))
    mdi.resize(1400, 800)
    mdi.show()
    
    sys.exit(app.exec_())
