#!/usr/bin/env python3
"""
TrafficTimelineAnalysis - F1T Traffic 時間線分析模組
====================================================

基於通用 MDI 架構實現，提供：
- 每位車手每一圈的 traffic 狀態可視化
- 類似 Tire Strategy 風格的時間線圖表
- 白色主題風格

資料來源：CLI Function 127 (Live Timing Traffic Distance)
Author: F1T Team
Date: 2025-12-23
Version: 1.0.0
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional

import certifi
import requests
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox

from core.gui_i18n import tr
from core.logger import get_logger
from core.api_base_url import resolve_api_base_url

try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig

from .traffic_timeline_chart_widget import TrafficTimelineChartWidget


logger = get_logger("gui.traffic_timeline_mdi", component="gui")


class TrafficTimelineApiWorker(QThread):
    """Background worker thread to call REST API for traffic timeline data."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 120.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "https://localhost:8000").rstrip("/")
        self.params = dict(params)
        self.timeout = timeout

    def run(self) -> None:
        try:
            if self.isInterruptionRequested():
                logger.debug("[TRAFFIC_TIMELINE_API_WORKER] Interrupted before start")
                return

            self.progress.emit(15)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 127,
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True

            if self.isInterruptionRequested():
                logger.debug("[TRAFFIC_TIMELINE_API_WORKER] Interrupted before request")
                return

            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
            )

            if self.isInterruptionRequested():
                logger.debug("[TRAFFIC_TIMELINE_API_WORKER] Interrupted after response")
                return

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
                "function_spec": payload.get("function_spec"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
                "params": dict(query_params),
            }

            if self.isInterruptionRequested():
                logger.debug("[TRAFFIC_TIMELINE_API_WORKER] Interrupted before emit")
                return

            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})

        except Exception as exc:
            if not self.isInterruptionRequested():
                self.failure.emit(str(exc))
        finally:
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class TrafficTimelineDataManager(UniversalDataLoader):
    """Traffic Timeline Data Manager"""

    def __init__(self, parent=None):
        if "traffic_timeline" not in UniversalDataLoader.ANALYSIS_TYPES:
            traffic_config = AnalysisConfig(
                display_name=tr("traffic_timeline", "Traffic Timeline"),
                debug_prefix="[TRAFFIC_TIMELINE_DATA]",
                data_source="api",
                cli_function="127",
                api_endpoint="/api/v2/analysis/execute",
                api_function_id=127,
                api_timeout=120.0,
                file_patterns=[
                    "live_timing_traffic_distance_{year}_{race}_{session}.json",
                    "live_timing_traffic_distance_{year}_{race}_{session}_*.json",
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                cache_enabled=True,
            )
            UniversalDataLoader.register_analysis_type("traffic_timeline", traffic_config)

        super().__init__("traffic_timeline", parent)

        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[TrafficTimelineApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}

    def _debug(self, message: str):
        logger.info("[TRAFFIC_TIMELINE_DATA] %s", message)

    def _determine_api_base_url(self) -> str:
        return resolve_api_base_url(event_logger=self._debug)

    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")
        if not year or not race or not session:
            self._debug("Incomplete parameters: need year, race, session")
            return False
        return True

    def load_data(self, **kwargs) -> bool:
        if self.config.data_source != "api":
            return super().load_data(**kwargs)

        if self._is_loading:
            self._debug("Loading already in progress, ignoring new request")
            return False

        if not self._validate_load_parameters(kwargs):
            self._error("API load parameter validation failed")
            self.load_error.emit("Invalid load parameters")
            return False

        self._is_loading = True
        self._pending_params = dict(kwargs)
        self._api_base_url = self._determine_api_base_url()
        self._debug(f"Loading traffic timeline via API: base_url={self._api_base_url}, params={self._pending_params}")
        self.load_progress.emit(5)
        self.status_changed.emit(tr("traffic_timeline.loading", "Loading traffic timeline data..."))

        try:
            self._start_api_request(self._pending_params)
            return True
        except Exception as exc:
            self._error(f"Failed to start API request: {exc}")
            self._is_loading = False
            self.status_changed.emit(tr("traffic_timeline.api_failed", "API load failed"))
            return super().load_data(**kwargs)

    def _start_api_request(self, params: Dict[str, Any]) -> None:
        """Start API request background thread"""
        self._cleanup_api_worker()

        worker_params = {
            "year": params.get("year"),
            "race": params.get("race"),
            "session": params.get("session"),
            "force_refresh": params.get("force_refresh", False),
        }

        timeout = getattr(self.config, "api_timeout", 120.0)
        self._api_worker = TrafficTimelineApiWorker(
            self._api_base_url,
            worker_params,
            timeout=timeout,
            parent=self,
        )
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker)
        self._api_worker.start()

    def _cleanup_api_worker(self) -> None:
        """Cleanup API worker thread"""
        if self._api_worker is not None:
            try:
                if self._api_worker.isRunning():
                    self._api_worker.requestInterruption()
                    self._api_worker.wait(3000)
                self._api_worker.deleteLater()
            except Exception:
                pass
            self._api_worker = None

    def _on_api_progress(self, value: int) -> None:
        try:
            bounded = max(0, min(int(value), 100))
            self.load_progress.emit(bounded)
        except Exception:
            pass

    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        self._debug("========== API Success Callback ==========")
        try:
            raw_data = payload.get("data")
            meta = payload.get("meta", {})
            self._last_api_meta = meta or {}
            self._last_data_source = "api"
            
            # Debug: show what we received
            self._debug(f"raw_data type: {type(raw_data)}")
            if isinstance(raw_data, dict):
                self._debug(f"raw_data keys: {list(raw_data.keys())}")

            # Extract nested data - handle multiple possible formats:
            # Format 1: {"drivers": {...}} - direct
            # Format 2: {"data": {"drivers": {...}}} - one level nested  
            # Format 3: {"data": {"success": true, "drivers": {...}}} - CLI JSON format
            # Format 4: {"function_id": 127, "data": {"drivers": {...}}} - cache format
            
            if isinstance(raw_data, dict):
                # Check if drivers is directly available
                if "drivers" in raw_data:
                    self._debug("Found drivers at top level")
                    extracted_data = raw_data
                # Check nested in "data" key
                elif "data" in raw_data and isinstance(raw_data["data"], dict):
                    nested = raw_data["data"]
                    self._debug(f"Checking nested 'data' key, keys: {list(nested.keys())}")
                    if "drivers" in nested:
                        self._debug("Found drivers in nested data")
                        extracted_data = nested
                    elif "data" in nested and isinstance(nested["data"], dict):
                        # Double nested
                        double_nested = nested["data"]
                        self._debug(f"Checking double nested, keys: {list(double_nested.keys())}")
                        if "drivers" in double_nested:
                            self._debug("Found drivers in double nested data")
                            extracted_data = double_nested
                        else:
                            extracted_data = raw_data
                    else:
                        extracted_data = nested
                else:
                    extracted_data = raw_data
            else:
                extracted_data = raw_data

            self._debug(f"Final extracted_data keys: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'N/A'}")

            if not self._validate_data_format(extracted_data):
                self._debug(f"Validation failed! extracted_data type: {type(extracted_data)}")
                if isinstance(extracted_data, dict):
                    self._debug(f"extracted_data keys: {list(extracted_data.keys())}")
                raise ValueError("API response data format invalid")

            processed_data = self._process_data(extracted_data)
            metadata = processed_data.setdefault("metadata", {})
            metadata.setdefault("data_source", "api")
            if self._last_api_meta:
                metadata.setdefault("api", {}).update(self._last_api_meta)

            self._current_data = processed_data
            self._is_loading = False
            self.load_progress.emit(100)
            self.status_changed.emit(tr("traffic_timeline.loaded", "Data loaded from API"))
            self._debug("Data processing complete, emitting data_loaded signal")
            self.data_loaded.emit(processed_data)

        except Exception as exc:
            self._debug(f"Exception processing API data: {exc}")
            import traceback
            traceback.print_exc()
            self._error(f"Failed to process API data: {exc}")
            self._is_loading = False
            self.load_error.emit(str(exc))

    def _on_api_error(self, message: str) -> None:
        self._debug(f"========== API Error Callback: {message} ==========")
        self._error(f"API request failed: {message}")
        self._is_loading = False
        self.status_changed.emit(tr("traffic_timeline.api_error", "API request failed"))
        self.load_error.emit(message)

    def _validate_data_format(self, raw_data: Any) -> bool:
        """Validate API response data format"""
        if not isinstance(raw_data, dict):
            return False
        # Must have 'drivers' key
        if "drivers" not in raw_data:
            return False
        return True

    def _process_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw API data"""
        # The data is already in the correct format from F127
        return dict(raw_data)

    def get_processed_data(self) -> Optional[Dict[str, Any]]:
        return self._current_data


class TrafficTimelineAnalysis(UniversalAnalysisMDI):
    """Traffic Timeline Analysis MDI Module"""

    def __init__(
        self,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        parent=None,
        **kwargs,
    ):
        logger.info("[TRAFFIC_TIMELINE_MDI] TrafficTimelineAnalysis initializing...")

        if "traffic_timeline" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            traffic_config = AnalysisMDIConfig(
                analysis_type="traffic_timeline",
                display_name=tr("traffic_timeline", "Traffic Timeline"),
                default_size=(1200, 700),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False,
                chart_types=["timeline"],
            )
            UniversalAnalysisMDI.register_mdi_module_type("traffic_timeline", traffic_config)

        super().__init__("traffic_timeline", parent)
        logger.info("[TRAFFIC_TIMELINE_MDI] Base class initialized, data_manager: %s", self.data_manager)

        logger.info("[TRAFFIC_TIMELINE_MDI] Initializing module components...")
        if not self.initialize_module():
            logger.error("[TRAFFIC_TIMELINE_MDI] Module component initialization failed")
            return

        logger.info("[TRAFFIC_TIMELINE_MDI] Module components initialized")
        logger.info("[TRAFFIC_TIMELINE_MDI] data_manager: %s", self.data_manager)
        logger.info("[TRAFFIC_TIMELINE_MDI] chart_widget: %s", self.chart_widget)

        self.set_responsive_layout()

        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session

        if kwargs:
            self._debug(f"Ignoring unused init params: {kwargs}")

    def create_data_manager(self) -> TrafficTimelineDataManager:
        return TrafficTimelineDataManager(self)

    def create_chart_widget(self) -> TrafficTimelineChartWidget:
        return TrafficTimelineChartWidget(parent=None)

    def create_additional_widgets(self) -> List[QWidget]:
        # No control panel needed
        return []

    def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        try:
            logger.info("[TRAFFIC_TIMELINE_MDI] ========== Parameter Update ==========")
            logger.info("[TRAFFIC_TIMELINE_MDI] Received params: %s %s %s", year, race, session)
            self.current_year = str(year)
            self.current_race = str(race)
            self.current_session = str(session)

            if not hasattr(self, "_error_handler_connected"):
                if hasattr(self, "data_manager") and self.data_manager:
                    self.data_manager.load_error.connect(self._on_data_load_error)
                    self._error_handler_connected = True

            if hasattr(self, "data_manager") and self.data_manager:
                self.data_manager.year = self.current_year
                self.data_manager.race = self.current_race
                self.data_manager.session = self.current_session
                result = self.data_manager.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    **kwargs,
                )
                logger.info("[TRAFFIC_TIMELINE_MDI] Data load result: %s", result)
                if not result:
                    logger.warning("[TRAFFIC_TIMELINE_MDI] Data load request failed to submit")

            logger.info("[TRAFFIC_TIMELINE_MDI] Parameter update complete")
            return True

        except Exception as exc:
            logger.exception("[TRAFFIC_TIMELINE_MDI] Parameter update failed: %s", exc)
            return False

    def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
        return self.update_lap_parameters(year=year, race=race, session=session)

    def _on_data_load_error(self, error_message: str):
        logger.error("[TRAFFIC_TIMELINE_MDI] Data load error: %s", error_message)

        if not hasattr(self, "main_widget") or self.main_widget is None:
            return

        solution_text = (
            f"{tr('traffic_timeline.load_failed', 'Failed to load traffic timeline data')}:\n{error_message}\n\n"
            f"{tr('traffic_timeline.check_api', 'Please check if API server is running.')}"
        )

        QMessageBox.warning(
            self.main_widget,
            f"{tr('traffic_timeline', 'Traffic Timeline')} - {tr('load_failed', 'Load Failed')}",
            solution_text,
            QMessageBox.Ok,
        )

    def refresh_analysis(self) -> None:
        logger.info("[TRAFFIC_TIMELINE_MDI] Refreshing data...")
        if not self.data_manager:
            return
        success = self.data_manager.load_data(
            year=self.current_year,
            race=self.current_race,
            session=self.current_session,
            force_refresh=True,
        )
        if not success:
            logger.warning("[TRAFFIC_TIMELINE_MDI] Refresh request failed")

    def clear_data(self) -> None:
        if self.chart_widget:
            self.chart_widget.update_data({})

    def export_current_chart(self) -> bool:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"traffic_timeline_{self.current_year}_{self.current_race}_{self.current_session}_{timestamp}.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_widget,
            tr("traffic_timeline.export_dialog_title", "Save Traffic Timeline"),
            default_name,
            "PNG (*.png);;JPEG (*.jpg *.jpeg)",
        )
        if not file_path:
            return False
        return self.chart_widget.export_chart(file_path) if self.chart_widget else False

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        if export_format.lower() != "json":
            logger.warning("[TRAFFIC_TIMELINE_MDI] Unsupported export format: %s", export_format)
            return False
        try:
            import json
            current_data = self.data_manager.get_processed_data() if self.data_manager else None
            if not current_data:
                logger.warning("[TRAFFIC_TIMELINE_MDI] No data to export")
                return False
            payload = {
                "module": "traffic_timeline",
                "params": {
                    "year": self.current_year,
                    "race": self.current_race,
                    "session": self.current_session,
                },
                "data": current_data,
            }
            with open(export_path, "w", encoding="utf-8") as fp:
                json.dump(payload, fp, ensure_ascii=False, indent=2)
            return True
        except Exception as exc:
            logger.exception("[TRAFFIC_TIMELINE_MDI] Export failed: %s", exc)
            return False

    def set_responsive_layout(self):
        """Set responsive size policies for main view and child components."""
        try:
            from PyQt5.QtWidgets import QSizePolicy

            if hasattr(self, "main_widget") and self.main_widget:
                self.main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            if hasattr(self, "chart_widget") and self.chart_widget:
                self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            logger.info("[TRAFFIC_TIMELINE_MDI] Responsive layout set")

        except Exception as exc:
            logger.exception("[TRAFFIC_TIMELINE_MDI] Failed to set responsive layout: %s", exc)
