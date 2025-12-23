#!/usr/bin/env python3
"""
正賽預測 MDI 視窗
Race Prediction MDI

負責管理正賽預測的 MDI 視窗，整合資料載入器和表格元件
基於排位賽數據和動態車隊評級進行預測

作者: F1T Team
日期: 2025-11-27
版本: 1.0.0
"""

import time
import requests
from typing import Dict, Any
from PyQt5.QtWidgets import QGroupBox, QPushButton, QLabel, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig


logger = get_logger(component="race_prediction_mdi")


class RacePredictionApiWorker(QThread):
    """
    正賽預測 API 請求工作執行緒
    
    負責異步調用 API 獲取正賽預測數據
    API 端點: POST /api/v2/analysis/execute?function_id=80
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        """
        初始化 API Worker
        
        Args:
            params: API 參數 (year, race, etc.)
            base_url: API 基礎 URL (預設: https://localhost:8000)
            timeout: 請求超時時間（秒）
        """
        super().__init__()
        self.base_url = (base_url or "https://localhost:8000").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        """執行 API 請求"""
        try:
            # 檢查是否已被請求中斷
            if self.isInterruptionRequested():
                logger.debug("[RACE_PRED_API_WORKER] 啟動前已被請求中斷，跳過執行")
                return
                
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            # 構建查詢參數
            query_params: Dict[str, Any] = {
                "function_id": 80,  # Function 80 - 動態車隊評級分析
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
            }
            
            # 強制刷新（可選）
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            logger.info("[RACE_PRED_API_WORKER] Calling API: %s", endpoint)
            logger.debug("[RACE_PRED_API_WORKER] Parameters: %s", query_params)
            
            # 再次檢查中斷（在發送請求前）
            if self.isInterruptionRequested():
                logger.debug("[RACE_PRED_API_WORKER] 發送請求前被請求中斷")
                return
                
            # 發送 POST 請求
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            
            # 請求完成後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[RACE_PRED_API_WORKER] API 回應後被請求中斷，放棄處理結果")
                return
                
            self.progress.emit(70)
            
            # 檢查 HTTP 狀態
            response.raise_for_status()
            
            # 解析 JSON 回應
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be a JSON object")
            
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API returned success=False"))
            
            # 提取數據
            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API response missing 'data' object")
            
            # 計算延遲
            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            
            # 構建元數據
            meta = {
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "function_spec": payload.get("function_spec"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }
            
            logger.info("[RACE_PRED_API_WORKER] API call successful")
            logger.info("[RACE_PRED_API_WORKER] Latency: %sms", meta["latency_ms"])
            logger.debug("[RACE_PRED_API_WORKER] Source: %s", meta["source"])
            
            # 發送信號前最後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[RACE_PRED_API_WORKER] 發送成功信號前被請求中斷，放棄發送")
                return
                
            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            error_msg = f"API request failed: {str(exc)}"
            logger.error("[RACE_PRED_API_WORKER] %s", error_msg)
            import traceback
            traceback.print_exc()
            # 如果被中斷，不發送失敗信號
            if not self.isInterruptionRequested():
                self.failure.emit(error_msg)
        finally:
            # 只有在未中斷時才發送完成信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


# 導入資料載入器和元件
try:
    from .race_prediction_data_loader import RacePredictionDataLoader
    from .race_prediction_widget import RacePredictionWidget
except ImportError:
    from modules.gui.race_prediction.race_prediction_data_loader import RacePredictionDataLoader
    from modules.gui.race_prediction.race_prediction_widget import RacePredictionWidget


class RacePredictionMDI(UniversalAnalysisMDI):
    """
    正賽預測 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 RacePredictionDataLoader 和 RacePredictionWidget
    """
    
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="race_prediction",
                display_name="Race Prediction",
                default_size=(1400, 800),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("race_prediction", config)
            cls._REGISTERED = True
            logger.debug("[RACE_PRED_MDI] Module type registered")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        logger.info("[RACE_PRED_MDI] Initializing...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="race_prediction", parent=parent)
        
        # 初始化參數
        self.year = None
        self.race = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        # API Worker 引用（防止 GC）
        self.api_worker = None
        
        logger.debug("[RACE_PRED_MDI] Base initialization complete")
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組
        
        Args:
            parent_widget: 父級 widget
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("[RACE_PRED_MDI] Starting module initialization...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.error("[RACE_PRED_MDI] Missing current_year")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.error("[RACE_PRED_MDI] Missing current_race")
                return False
            
            # 設置參數
            self.year = str(self.current_year)
            self.race = self.current_race
            
            logger.info("[RACE_PRED_MDI] Parameters: %s %s", self.year, self.race)
            
            # 調用基類初始化
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                logger.error("[RACE_PRED_MDI] Base initialization failed")
                return False
            
            # 驗證組件
            if not self.chart_widget:
                logger.error("[RACE_PRED_MDI] chart_widget not created")
                return False
            
            if not self.data_manager:
                logger.error("[RACE_PRED_MDI] data_manager not created")
                return False
            
            logger.info("[RACE_PRED_MDI] Components created successfully")
            
            # 載入初始數據
            self.load_initial_data()
            
            logger.info("[RACE_PRED_MDI] Module initialization complete")
            return True
            
        except Exception as e:
            logger.exception("[RACE_PRED_MDI] Initialization failed", exc_info=e)
            return False
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self) -> RacePredictionDataLoader:
        """創建資料載入器"""
        logger.debug("[RACE_PRED_MDI] Creating data loader...")
        loader = RacePredictionDataLoader(
            year=self.year,
            race=self.race,
            parent=self
        )
        
        # 連接信號
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        loader.status_changed.connect(self._on_status_changed)
        
        logger.debug("[RACE_PRED_MDI] Data loader created")
        return loader
    
    def create_chart_widget(self) -> RacePredictionWidget:
        """創建表格元件"""
        logger.debug("[RACE_PRED_MDI] Creating widget...")
        widget = RacePredictionWidget(parent=None)
        logger.debug("[RACE_PRED_MDI] Widget created")
        return widget
    
    def _setup_control_panel(self):
        """設置控制面板"""
        logger.debug("[RACE_PRED_MDI] Setting up control panel...")
        
        # 創建控制面板容器
        control_panel = QGroupBox(tr("control_panel", "Control Panel"))
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)
        
        # 重新載入按鈕
        self.btn_reload = QPushButton(tr("reload_button", "Reload"))
        self.btn_reload.clicked.connect(self._on_reload_clicked)
        control_layout.addWidget(self.btn_reload)
        
        # 彈性空間
        control_layout.addStretch()
        
        # 狀態標籤
        self.lbl_control_status = QLabel(tr("status_ready", "Ready"))
        control_layout.addWidget(self.lbl_control_status)
        
        # 添加到主佈局
        if hasattr(self, 'main_layout'):
            self.main_layout.addWidget(control_panel)
        
        logger.debug("[RACE_PRED_MDI] Control panel setup complete")
    
    # ========== 數據流處理 ==========
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """資料載入完成回調"""
        try:
            logger.info("[RACE_PRED_MDI] Data loaded, processing...")
            
            # 驗證資料結構
            if not isinstance(data, dict):
                self._show_error(tr("data_format_error", "Data format error"), tr("not_dict", "Data is not a dictionary"))
                return
            
            if "metadata" not in data:
                self._show_error(tr("data_structure_error", "Data structure error"), tr("missing_metadata", "Missing 'metadata'"))
                return
            
            if "predictions" not in data:
                self._show_error(tr("data_structure_error", "Data structure error"), tr("missing_predictions", "Missing 'predictions'"))
                return
            
            # 儲存資料
            self._current_data = data
            self._is_data_loaded = True
            
            # 更新 Widget
            predictions = data["predictions"]
            logger.info("[RACE_PRED_MDI] Updating display (%s drivers)...", len(predictions))
            self.chart_widget.update_display(data)
            
            # 更新狀態
            if hasattr(self, 'lbl_control_status'):
                self.lbl_control_status.setText(
                    tr("data_loaded_status", "Loaded {count} drivers").format(count=len(predictions))
                )
            
            logger.info("[RACE_PRED_MDI] Data processing complete")
            
        except Exception as e:
            logger.exception("[RACE_PRED_MDI] Data processing failed", exc_info=e)
            self._show_error(tr("data_processing_error", "Data processing failed"), str(e))
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """資料載入錯誤回調"""
        logger.error("[RACE_PRED_MDI] Load error: %s", error_msg)
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(f"{tr('error', 'Error')}: {error_msg}")
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """狀態變更回調"""
        logger.info("[RACE_PRED_MDI] Status: %s", status)
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(status)
    
    # ========== 事件處理 ==========
    
    def _on_reload_clicked(self):
        """處理重新載入按鈕點擊"""
        logger.info("[RACE_PRED_MDI] Reloading data...")
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(tr("reloading", "Reloading..."))
        
        # 清空表格
        self.chart_widget.clear_display()
        
        # 重新載入
        self.load_initial_data()
    
    # ========== 公開方法 ==========
    
    def load_initial_data(self):
        """
        載入初始資料 - 強制使用 API
        
        優先級：
        1. API 調用 (https://localhost:8000)
        2. 備援: 本地 JSON 檔案（API 失敗時）
        """
        logger.info("[RACE_PRED_MDI] Starting data load...")
        logger.info("[RACE_PRED_MDI] Parameters: %s %s", self.year, self.race)
        
        # 更新狀態
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(tr("loading_from_api", "Loading from API..."))
        
        # 創建 API Worker
        api_params = {
            "year": self.year,
            "race": self.race,
            "force_refresh": False
        }
        
        logger.debug("[RACE_PRED_MDI] Creating API Worker...")
        self.api_worker = RacePredictionApiWorker(
            params=api_params,
            base_url="https://localhost:8000",
            timeout=60.0
        )
        
        # 連接信號（使用 Qt.QueuedConnection 確保 UI 線程安全）
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 啟動 API 請求
        logger.info("[RACE_PRED_MDI] Starting API request...")
        self.api_worker.start()
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API 請求進度更新"""
        logger.debug("[RACE_PRED_MDI] API progress: %s%%", progress)
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(f"{tr('api_loading', 'API Loading')}... {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict[str, Any]):
        """API 請求成功"""
        try:
            logger.info("[RACE_PRED_MDI] API call successful")
            
            # 提取數據和元數據
            data = result.get("data", {})
            meta = result.get("meta", {})
            
            logger.debug("[RACE_PRED_MDI] Source: %s", meta.get('source'))
            logger.info("[RACE_PRED_MDI] Latency: %sms", meta.get('latency_ms'))
            
            # 使用 DataLoader 轉換數據
            if hasattr(self, 'data_manager') and self.data_manager:
                # 構建原始格式
                raw_data = {"success": True, "data": data}
                transformed_data = self.data_manager._transform_data_for_display(raw_data)
                
                if transformed_data:
                    self._on_data_loaded(transformed_data)
                else:
                    raise ValueError("Data transformation failed")
            else:
                raise ValueError("data_manager not available")
            
            # 更新狀態
            if hasattr(self, 'lbl_control_status'):
                source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
                self.lbl_control_status.setText(
                    tr("data_loaded_from_source", "Loaded from {source}").format(source=source_label)
                )
            
        except Exception as e:
            logger.exception("[RACE_PRED_MDI] API data processing failed", exc_info=e)
            self._on_api_failure(str(e))
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API 請求失敗 - API-ONLY 模式，不使用本地 JSON 備援"""
        logger.error("[RACE_PRED_MDI] API call failed: %s", error_msg)
        
        # API-ONLY 模式：不嘗試本地 JSON 備援
        # 根據專案政策，GUI 只能通過 API 獲取數據
        
        # 更新狀態標籤（與 FP3->Q 保持一致）
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(
                tr("race_pred_api_failure", "API request failed, please try again later")
            )
        
        # 顯示錯誤
        self._show_error(
            tr("race_pred_api_failure_title", "Load Failed"),
            tr(
                "race_pred_api_failure_message",
                "Race prediction data can only be loaded via API. Please ensure API service is available.\n\nError:\n{error}"
            ).format(error=error_msg)
        )
        logger.error("[RACE_PRED_MDI] All fallback options exhausted")
    
    def update_analysis_parameters(self, year: str, race: str) -> bool:
        """更新分析參數並重新載入資料"""
        try:
            logger.info("[RACE_PRED_MDI] Updating parameters: %s %s", year, race)
            
            self.current_year = str(year)
            self.current_race = race
            self.year = str(year)
            self.race = race
            
            # 更新 DataLoader 參數（支援 data_manager 和 data_loader）
            if hasattr(self, 'data_manager') and self.data_manager:
                self.data_manager.year = str(year)
                self.data_manager.race = race
                logger.debug("[RACE_PRED_MDI] DataManager parameters synced")
            elif hasattr(self, 'data_loader') and self.data_loader:
                self.data_loader.year = str(year)
                self.data_loader.race = race
                logger.debug("[RACE_PRED_MDI] DataLoader parameters synced")
            
            # 重新載入
            logger.info("[RACE_PRED_MDI] Triggering data reload...")
            self.load_initial_data()
            return True
            
        except Exception as e:
            logger.exception("[RACE_PRED_MDI] Parameter update failed", exc_info=e)
            return False
    
    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """覆寫通用參數更新邏輯"""
        try:
            logger.debug("[RACE_PRED_MDI] update_parameters called")
            logger.debug("   Received: year=%s, race=%s, session=%s", year, race, session)
            logger.debug(
                "   Current: year=%s, race=%s",
                self.year if hasattr(self, 'year') else 'N/A',
                self.race if hasattr(self, 'race') else 'N/A',
            )
            
            target_year = year if year is not None else (self.year or getattr(self, 'current_year', None))
            target_race = race if race is not None else (self.race or getattr(self, 'current_race', None))
            
            if not all([target_year, target_race]):
                logger.error("[RACE_PRED_MDI] Missing required parameters")
                return False
            
            normalized_year = str(target_year)
            normalized_race = target_race
            
            logger.debug("[RACE_PRED_MDI] Normalized: year=%s, race=%s", normalized_year, normalized_race)
            
            self.current_year = normalized_year
            self.current_race = normalized_race
            
            params_payload = {
                'year': self.current_year,
                'race': self.current_race
            }
            self.parameters_updated.emit(params_payload)
            self.update_window_title()
            
            logger.info("[RACE_PRED_MDI] Calling update_analysis_parameters...")
            return self.update_analysis_parameters(self.current_year, self.current_race)
            
        except Exception as exc:
            logger.exception("[RACE_PRED_MDI] update_parameters failed", exc_info=exc)
            return False
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """返回視窗標題"""
        return tr("race_prediction", "Race Prediction")
    
    def get_widget(self):
        """獲取主要元件"""
        if hasattr(self, 'chart_widget') and self.chart_widget:
            return self.chart_widget
        return None
    
    # ========== 輔助方法 ==========
    
    def _show_error(self, title: str, message: str):
        """顯示錯誤對話框"""
        parent = self.chart_widget if hasattr(self, 'chart_widget') else None
        QMessageBox.critical(parent, title, message)


# ========== 測試代碼 ==========
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    logger.info("=" * 60)
    logger.info("Race Prediction MDI - Standalone Test")
    logger.info("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 創建 MDI 視窗
    mdi = RacePredictionMDI(parent=None)
    
    # 設置參數
    mdi.current_year = "2025"
    mdi.current_race = "Japan"
    
    # 初始化模組
    if mdi.initialize_module():
        logger.info("\nModule initialization successful")
        
        # 獲取主要元件
        widget = mdi.get_widget()
        if widget and hasattr(widget, 'setWindowTitle'):
            widget.setWindowTitle("Race Prediction MDI - Test")
        if widget and hasattr(widget, 'resize'):
            widget.resize(1400, 800)
        if widget and hasattr(widget, 'show'):
            widget.show()
        
        logger.info("Test window displayed")
    else:
        logger.error("\nModule initialization failed")
        sys.exit(1)
    
    sys.exit(app.exec_())
