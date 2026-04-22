#!/usr/bin/env python3
"""
PoleDefenseAnalysis - F1T 桿位防守統計 MDI 模組
================================================

基於通用 MDI 架構實現，提供：
- 年度桿位防守時間軸格子圖可視化
- 顯示每位車手在每場比賽的桿位防守結果
- 按防守成功率排序

資料來源：CLI Function 101 (Season Start Reaction Analysis)
- p1_lap2_position_unchanged: 成功防守桿位的比賽
- p1_lap2_position_changed: 失去桿位的比賽

作者: F1T Team
日期: 2025-12-22
版本: 1.0.0
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional

import certifi
from core import local_requests as requests
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox

from core.gui_i18n import tr
from core.logger import get_logger
from core.api_base_url import resolve_api_base_url

try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig

from .pole_defense_chart_widget import PoleDefenseChartWidget

logger = get_logger(__name__)


class PoleDefenseApiWorker(QThread):
    """背景工作執行緒，呼叫 REST API 取得年度桿位防守資料。"""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, year: int, timeout: float = 120.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "http://localhost:8000").rstrip("/")
        self.year = year
        self.timeout = timeout

    def run(self) -> None:
        try:
            if self.isInterruptionRequested():
                logger.debug("[POLE_DEFENSE_API] Interrupted before start")
                return
                
            self.progress.emit(15)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params = {
                "function_id": 101,
                "year": self.year,
            }

            if self.isInterruptionRequested():
                return
                
            start_ts = time.perf_counter()
            logger.info(f"[POLE_DEFENSE_API] Calling {endpoint} with params: {query_params}")
            
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
            )
            
            if self.isInterruptionRequested():
                return
                
            self.progress.emit(65)
            response.raise_for_status()

            payload = response.json()
            logger.info(f"[POLE_DEFENSE_API] Response success: {payload.get('success')}")
            
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
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
                "year": self.year,
            }

            if self.isInterruptionRequested():
                return
                
            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
            
        except requests.exceptions.Timeout:
            if not self.isInterruptionRequested():
                self.failure.emit(tr("api_timeout", "API request timed out"))
        except requests.exceptions.ConnectionError:
            if not self.isInterruptionRequested():
                self.failure.emit(tr("api_connection_error", "Cannot connect to API server"))
        except Exception as exc:
            if not self.isInterruptionRequested():
                logger.exception(f"[POLE_DEFENSE_API] Error: {exc}")
                self.failure.emit(str(exc))
        finally:
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class PoleDefenseDataManager(UniversalDataLoader):
    """桿位防守統計資料管理器"""

    def __init__(self, parent=None):
        if "pole_defense" not in UniversalDataLoader.ANALYSIS_TYPES:
            config = AnalysisConfig(
                display_name=tr("pole_defense_statistics", "Pole Defense Statistics"),
                debug_prefix="[POLE_DEFENSE_DATA]",
                data_source="api",
                cli_function="101",
                api_endpoint="/api/v2/analysis/execute",
                api_function_id=101,
                api_timeout=120.0,
                file_patterns=[],
                search_directories=[],
                supports_realtime=False,
                cache_enabled=False,
            )
            UniversalDataLoader.register_analysis_type("pole_defense", config)

        super().__init__("pole_defense", parent)

        self._api_base_url = resolve_api_base_url()
        self._api_worker: Optional[PoleDefenseApiWorker] = None
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        self._pending_year: Optional[int] = None

    def _debug(self, message: str) -> None:
        logger.info("[POLE_DEFENSE_DATA] %s", message)

    def _error(self, message: str) -> None:
        logger.error("[POLE_DEFENSE_DATA] %s", message)

    def load_data(self, **kwargs) -> bool:
        """載入年度桿位防守數據"""
        if self._is_loading:
            self._debug("Already loading, ignoring request")
            return False

        year = kwargs.get("year")
        if not year:
            self._error("Year parameter required")
            self.load_error.emit("Year parameter required")
            return False

        self._is_loading = True
        self._pending_year = int(year)
        self._api_base_url = resolve_api_base_url()
        self._debug(f"Loading data for year {year} from {self._api_base_url}")
        self.load_progress.emit(5)
        self.status_changed.emit(tr("loading_data", "Loading data..."))

        try:
            self._start_api_request(self._pending_year)
            return True
        except Exception as exc:
            self._error(f"Failed to start API request: {exc}")
            self._is_loading = False
            self.load_error.emit(str(exc))
            return False

    def _start_api_request(self, year: int) -> None:
        """啟動 API 請求"""
        self._cleanup_api_worker()

        self._api_worker = PoleDefenseApiWorker(
            self._api_base_url,
            year,
            timeout=self.config.api_timeout,
            parent=self,
        )
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker)
        self._api_worker.start()

    def _on_api_progress(self, value: int) -> None:
        try:
            bounded = max(0, min(int(value), 100))
            self.load_progress.emit(bounded)
        except Exception:
            pass

    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        self._debug("========== API Success ==========")
        try:
            raw_data = payload.get("data")
            meta = payload.get("meta", {})
            self._last_api_meta = meta or {}
            self._last_data_source = "api"

            # 處理雙層嵌套格式
            if isinstance(raw_data, dict) and "data" in raw_data and "success" in raw_data:
                self._debug("Detected nested format, extracting inner data")
                raw_data = raw_data.get("data", raw_data)

            if not self._validate_data_format(raw_data):
                raise ValueError("Invalid data format from API")

            self._is_loading = False
            self.status_changed.emit(tr("data_loaded", "Data loaded"))
            self.data_loaded.emit(raw_data)
            
            # 計算桿位數據數量
            p1_unchanged = raw_data.get("p1_lap2_position_unchanged", {})
            p1_changed = raw_data.get("p1_lap2_position_changed", {})
            total_races = len(p1_unchanged.get("races", [])) + len(p1_changed.get("races", []))
            self._debug(f"Data loaded successfully: {total_races} pole position races")

        except Exception as exc:
            self._error(f"Failed to process API response: {exc}")
            self._is_loading = False
            self.load_error.emit(str(exc))

    def _on_api_error(self, error_msg: str) -> None:
        self._error(f"API error: {error_msg}")
        self._is_loading = False
        self.status_changed.emit(f"{tr('error', 'Error')}: {error_msg}")
        self.load_error.emit(error_msg)

    def _cleanup_api_worker(self) -> None:
        """清理 API Worker"""
        if self._api_worker is not None:
            try:
                if self._api_worker.isRunning():
                    self._api_worker.requestInterruption()
                    self._api_worker.wait(2000)
                self._api_worker.deleteLater()
            except Exception:
                pass
            self._api_worker = None

    def _validate_data_format(self, data: Any) -> bool:
        """驗證數據格式"""
        if not isinstance(data, dict):
            return False
        
        # 檢查 p1 相關數據
        p1_unchanged = data.get("p1_lap2_position_unchanged", {})
        p1_changed = data.get("p1_lap2_position_changed", {})
        
        # 至少要有其中一個有數據
        unchanged_races = p1_unchanged.get("races", [])
        changed_races = p1_changed.get("races", [])
        
        if not unchanged_races and not changed_races:
            self._debug("No pole defense data found")
            return False
        
        return True

    def cleanup(self) -> None:
        """清理資源"""
        self._cleanup_api_worker()
        super().cleanup()


class PoleDefenseAnalysis(UniversalAnalysisMDI):
    """桿位防守統計分析 MDI 模組"""

    def __init__(
        self,
        year: Optional[int] = None,
        parent=None,
        **kwargs,
    ):
        logger.info("[POLE_DEFENSE_MDI] Initializing...")

        if "pole_defense" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            config = AnalysisMDIConfig(
                analysis_type="pole_defense",
                display_name=tr("pole_defense_statistics", "Pole Defense Statistics"),
                default_size=(1000, 500),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False,
                chart_types=["timeline_grid"],
            )
            UniversalAnalysisMDI.register_mdi_module_type("pole_defense", config)

        super().__init__("pole_defense", parent)
        logger.info("[POLE_DEFENSE_MDI] Base init complete")

        logger.info("[POLE_DEFENSE_MDI] Starting module initialization...")
        if not self.initialize_module():
            logger.error("[POLE_DEFENSE_MDI] Module initialization failed")
            return

        logger.info("[POLE_DEFENSE_MDI] Module initialization complete")

        if year is not None:
            self.current_year = str(year)

        if kwargs:
            logger.debug(f"[POLE_DEFENSE_MDI] Ignored kwargs: {kwargs}")

    def create_data_manager(self) -> PoleDefenseDataManager:
        """創建資料管理器"""
        return PoleDefenseDataManager(self)

    def create_chart_widget(self) -> PoleDefenseChartWidget:
        """創建圖表組件"""
        return PoleDefenseChartWidget(parent=None)

    def create_additional_widgets(self) -> List[QWidget]:
        """創建額外組件（此模組不需要控制面板）"""
        return []

    def update_lap_parameters(self, year: str, race: str = None, session: str = None, **kwargs) -> bool:
        """更新參數（只使用年份）"""
        try:
            logger.info(f"[POLE_DEFENSE_MDI] ========== Parameter Update ==========")
            logger.info(f"[POLE_DEFENSE_MDI] Year: {year}")
            
            self.current_year = str(year)

            if hasattr(self, "data_manager") and self.data_manager:
                self.data_manager.year = self.current_year
                result = self.data_manager.load_data(year=self.current_year)
                logger.info(f"[POLE_DEFENSE_MDI] Load result: {result}")
                
            return True
        except Exception as exc:
            logger.exception(f"[POLE_DEFENSE_MDI] Parameter update failed: {exc}")
            return False

    def update_analysis_parameters(self, year: str, race: str = None, session: str = None) -> bool:
        """更新分析參數"""
        return self.update_lap_parameters(year=year, race=race, session=session)

    def receive_main_window_update_notification(self, param_type: str, value: Any) -> None:
        """接收主視窗參數更新通知"""
        try:
            logger.debug(f"[POLE_DEFENSE_MDI] Received update: {param_type} = {value}")
            
            if param_type == 'year':
                new_year = str(value)
                if new_year != self.current_year:
                    self.current_year = new_year
                    logger.info(f"[POLE_DEFENSE_MDI] Year changed to {new_year}, reloading...")
                    self.update_lap_parameters(year=new_year)
            
        except Exception as e:
            logger.error(f"[POLE_DEFENSE_MDI] Error handling update: {e}")

    def _on_data_loaded(self, data: Dict[str, Any]) -> None:
        """數據載入完成回調"""
        logger.info("[POLE_DEFENSE_MDI] Data loaded callback")
        try:
            if hasattr(self, "chart_widget") and self.chart_widget:
                self.chart_widget.update_data(data)
                logger.info("[POLE_DEFENSE_MDI] Chart updated")
        except Exception as e:
            logger.exception(f"[POLE_DEFENSE_MDI] Failed to update chart: {e}")

    def _on_data_load_error(self, error_msg: str) -> None:
        """數據載入錯誤回調"""
        logger.error(f"[POLE_DEFENSE_MDI] Load error: {error_msg}")
        if hasattr(self, "chart_widget") and self.chart_widget:
            self.chart_widget.clear_data()

    def reset_chart_view(self) -> None:
        """重置圖表視圖 - 供 Show All Data 按鈕使用"""
        try:
            if hasattr(self, "chart_widget") and self.chart_widget:
                if hasattr(self.chart_widget, "reset_view"):
                    self.chart_widget.reset_view()
                    logger.info("[POLE_DEFENSE_MDI] Chart view reset")
        except Exception as e:
            logger.error(f"[POLE_DEFENSE_MDI] Reset chart view failed: {e}")

    def cleanup(self) -> None:
        """清理資源"""
        if hasattr(self, "data_manager") and self.data_manager:
            self.data_manager.cleanup()
        super().cleanup()
