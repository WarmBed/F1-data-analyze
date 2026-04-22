"""
詳細圈速分析 MDI 模組
功能: 提供詳細的圈速分析，包括圈速趨勢、智能標記和輪胎策略時間軸
"""

import os
import time
import copy
from typing import Dict, Any, List, Optional, Tuple

import certifi
from core import local_requests as requests
from core.api_base_url import resolve_api_base_url
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QLabel, QCheckBox, QGridLayout
from PyQt5.QtCore import pyqtSignal, QObject, QThread

# 導入翻譯函數
from core.gui_i18n import tr
from core.gui_settings_manager import gui_settings_manager

# 導入基類
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI
from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
from .lap_filter_utils import (
    extract_caution_laps,
    lap_is_pit_stop,
    lap_is_under_caution,
)


class DetailedLapAnalysisApiWorker(QThread):
    """Background worker responsible for fetching detailed lap analysis data via REST API."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(
        self,
        base_url: str,
        params: Dict[str, Any],
        *,
        timeout: float = 75.0,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.base_url = (base_url or "http://localhost:8000").rstrip("/")
        self.params = dict(params)
        self.timeout = float(timeout)

    def run(self) -> None:  # pragma: no cover - executed in worker thread
        try:
            self.progress.emit(10)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 28,
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }

            driver = self.params.get("driver_filter")
            if driver and str(driver).strip().upper() not in {"", "ALL", "ALL_DRIVERS"}:
                query_params["driver1"] = str(driver).strip().upper()

            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True

            if self.isInterruptionRequested():
                return

            self.progress.emit(40)
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
            )

            if self.isInterruptionRequested():
                return

            self.progress.emit(70)
            response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be a JSON object")
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API returned success=False"))

            data = payload.get("data")
            if data is None:
                raise ValueError("API response missing 'data'")

            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            meta = {
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "function_spec": payload.get("function_spec"),
                "latency_ms": round(latency_ms, 2),
                "endpoint": endpoint,
            }

            self.progress.emit(95)
            self.success.emit({"data": data, "meta": meta})
        except Exception as exc:  # pragma: no cover - propagated to GUI
            self.failure.emit(str(exc))
        finally:
            self.progress.emit(100)


class driverLapAnalysisDataManager(UniversalDataLoader):
    """詳細圈速分析數據管理器 - 整合架構，支援 CLI Function 28"""
    
    filter_settings_changed = pyqtSignal(dict)

    
    def __init__(self, parent=None):
        """
        初始化詳細圈速分析數據管理器 - 整合架構
        支援 CLI Function 28 格式的詳細圈速分析數據
        """
        # 註冊 laptime 分析類型（如果尚未註冊）
        if "laptime" not in UniversalDataLoader.ANALYSIS_TYPES:
            laptime_config = AnalysisConfig(
                display_name=tr("detailed_lap_analysis", "Detailed Lap Analysis"),
                debug_prefix="[F28_DATA]",
                data_source="api",
                cli_function="28",  # CLI -f28: 詳細圈速分析
                file_patterns=[
                    "detailed_laptime_analysis_{year}_{race}_{session}_{driver}.json",
                    "detailed_laptime_analysis_{year}_{race}_{session}_VER.json",  # CLI 預設輸出 VER
                    "detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json",
                    "detailed_laptime_analysis_{year}_{race}_{session}.json",
                    "detailed_driver_laptime_{year}_{race}_{session}_{driver}.json",
                    "detailed_driver_laptime_{year}_{race}_{session}.json"
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                required_params=["year", "race"],
                api_endpoint="/api/v2/analysis/execute"
            )
            UniversalDataLoader.register_analysis_type("laptime", laptime_config)
            logger.debug(f"[F28_DATA] 已註冊 laptime 分析類型")
        
        # 初始化基類
        super().__init__(analysis_type="laptime", parent=parent)
        
        # 詳細圈速分析特定屬性
        self.detailed_laptime_data = {}  # 存儲所有車手的詳細圈速數據
        self.available_drivers = []  # 可用車手列表
        self.selected_drivers = []  # 已選中的車手列表
        self.tire_strategy_data = {}  # 輪胎策略數據
        self.incident_markers = {}  # 事故標記數據

        self.filter_settings = {
            "filter_pit_laps": True,
            "filter_yellow_flags": True,
            "filter_first_laps": True,
        }
        self._filter_statistics: Dict[str, Dict[str, int]] = {}
        self._raw_driver_payloads: Dict[str, Any] = {}
        self._raw_driver_codes: List[str] = []
        self._raw_data_snapshot: Optional[Dict[str, Any]] = None
        self._suppress_global_sync = False
        self.settings_manager = gui_settings_manager
        
        # 載入狀態控制
        self._loading = False
        self._last_load_params: Optional[Tuple[Any, ...]] = None
        self._cached_data: Optional[Dict[str, Any]] = None
        self._signals_connected = False  # 添加信號連接狀態標記
        self._is_loading = False  # 與基類保持一致
        self._pending_data_source: Optional[str] = None

        # API 整合屬性
        self._api_worker: Optional[DetailedLapAnalysisApiWorker] = None
        self._api_timeout = float(os.getenv("F1T_LAPTIME_API_TIMEOUT", "75"))
        self._api_base_url = self._determine_api_base_url()
        self._api_enabled = self._is_api_enabled()
        self._allow_local_fallback = self._resolve_local_fallback_policy()
        self._current_api_params: Dict[str, Any] = {}
        self._last_api_metadata: Dict[str, Any] = {}
        self._last_data_source: Optional[str] = None
        self._last_error: Optional[str] = None
        self._api_progress: int = 0
        self._cli_generation_attempted: bool = False
        self._cli_worker = None
        # 舊版模組可能仍然引用 cli_worker，保留相容屬性
        self.cli_worker = None
        
        # 整合架構：直接繼承 UniversalDataLoader 功能
        # self.data_loader = driverLapUniversalDataLoader(parent=self)  # 分離架構（已廢棄）
        
        logger.debug(f"[LAPTIME_DATA_MANAGER] 詳細圈速分析數據管理器初始化完成")

        try:
            self._apply_global_settings(self.settings_manager.get_boxplot_settings())
            self.settings_manager.boxplot_settings_changed.connect(self._on_global_boxplot_settings_changed)
        except Exception as exc:
            self._debug(f"無法連接全域設定: {exc}")
        
    def load_data(self, **kwargs) -> bool:
        """載入詳細圈速分析數據，優先使用 API，必要時回退到本地 JSON/CLI。"""
        try:
            params = self._normalize_load_params(kwargs)
            cache_key = (params["year"], params["race"], params["session"], params.get("driver"))

            self._debug(
                f"load_data: params={params}, cached_key={self._last_load_params}, "
                f"is_loading={self._is_loading}, api_enabled={self._api_enabled}"
            )

            if self._is_loading:
                self._debug("load_data: already loading, ignore duplicate request")
                return False

            # 快取命中
            if (
                self._cached_data
                and self._last_load_params == cache_key
                and not params.get("force_refresh")
            ):
                self._debug("load_data: reuse cached data")
                self._current_data = self._cached_data
                self._last_data_source = self._last_data_source or "cache"
                self.data_loaded.emit(self._cached_data)
                return True

            # 重置狀態
            self._reset_loading_state()
            self._loading = True
            self._last_load_params = cache_key
            self._current_api_params = params
            self._last_error = None
            self._cli_generation_attempted = False

            if self._api_enabled:
                self._debug("load_data: starting API worker")
                self._is_loading = True
                self._pending_data_source = "api"
                self._start_api_request(params)
                return True

            self._debug("load_data: API disabled, falling back to local JSON")
            self._pending_data_source = "local-json"
            return self._load_via_local_json(params)

        except Exception as exc:  # pragma: no cover - defensive logging for UI
            self._error(f"load_data: unexpected failure -> {exc}")
            import traceback
            traceback.print_exc()
            self._last_error = str(exc)
            self._reset_loading_state()
            self.load_error.emit(str(exc))
            return False

    # ------------------------------------------------------------------
    # API 與回退管理
    # ------------------------------------------------------------------

    def _normalize_load_params(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """標準化載入參數，補齊預設值並準備 API 所需欄位。"""
        year = kwargs.get("year") or kwargs.get("current_year")
        race = kwargs.get("race") or kwargs.get("current_race")
        session = kwargs.get("session") or kwargs.get("current_session") or "R"
        driver_raw = (
            kwargs.get("driver")
            or kwargs.get("driver1")
            or kwargs.get("selected_driver")
            or "all_drivers"
        )

        if year is None or race is None:
            raise ValueError("載入詳細圈速分析需要提供 year 與 race 參數")

        try:
            year = int(year)
        except (TypeError, ValueError):
            raise ValueError(f"無效的年份參數: {year}")

        race = str(race).strip()
        session = str(session).strip().upper() or "R"

        driver_str = str(driver_raw).strip()
        if not driver_str or driver_str.lower() in {"all", "all_drivers", "*"}:
            driver_for_files = "all_drivers"
            selected_driver = None
        else:
            selected_driver = driver_str.upper()
            driver_for_files = "all_drivers"

        force_refresh = bool(kwargs.get("force_refresh") or kwargs.get("refresh"))

        normalized = {
            "year": year,
            "race": race,
            "session": session,
            "driver": driver_for_files,
            "selected_driver": selected_driver,
            "force_refresh": force_refresh,
        }

        self._debug(f"_normalize_load_params -> {normalized}")
        return normalized

    def _is_api_enabled(self) -> bool:
        """判斷是否啟用 API 模式。"""
        disable_flag = os.getenv("F1T_DISABLE_LAPTIME_API", "").strip().lower()
        if disable_flag in {"1", "true", "yes", "on"}:
            return False
        return True

    def _determine_api_base_url(self) -> str:
        """取得 API 基底網址，預設使用本機 FastAPI 服務。"""
        preferred: List[tuple[str, str]] = []
        override = os.getenv("F1T_API_BASE_URL")
        if override:
            preferred.append(("環境變數 F1T_API_BASE_URL", override))

        legacy_override = os.getenv("F1T_LAPTIME_API_BASE")
        if legacy_override:
            preferred.append(("環境變數 F1T_LAPTIME_API_BASE", legacy_override))

        base_url = resolve_api_base_url(
            event_logger=self._debug,
            preferred_urls=preferred or None,
        )
        self._debug(f"API base URL: {base_url}")
        return base_url

    def _resolve_local_fallback_policy(self) -> bool:
        """讀取環境變數設定，決定是否允許自動回退到 JSON/CLI。"""
        flag = os.getenv("F1T_ALLOW_LAPTIME_JSON_FALLBACK", "1").strip().lower()
        return flag not in {"0", "false", "no", "off"}

    def set_local_fallback_allowed(self, allowed: bool) -> None:
        """允許外部動態切換回退策略。"""
        self._allow_local_fallback = bool(allowed)

    def _start_api_request(self, params: Dict[str, Any]) -> None:
        """啟動後台 API 請求，確保同一時間僅有單一 worker 執行。"""
        self._stop_api_worker()

        api_payload = {
            "year": params["year"],
            "race": params["race"],
            "session": params["session"],
        }

        driver_filter = params.get("selected_driver")
        allow_filter = os.getenv("F1T_LAPTIME_API_ALLOW_DRIVER_FILTER", "0").strip().lower() in {"1", "true", "yes", "on"}
        if allow_filter and driver_filter:
            api_payload["driver_filter"] = driver_filter

        if params.get("force_refresh"):
            api_payload["force_refresh"] = True

        self._debug(f"_start_api_request -> payload={api_payload}")

        self._api_worker = DetailedLapAnalysisApiWorker(
            self._api_base_url,
            api_payload,
            timeout=self._api_timeout,
            parent=self,
        )
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker)
        self._api_worker.start()

        self.status_changed.emit("正在透過 API 取得詳細圈速分析數據...")
        self.load_progress.emit(5)

    def _on_api_progress(self, value: int) -> None:
        self._api_progress = value
        self.load_progress.emit(min(99, max(0, value)))

    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        self._debug("_on_api_success: 接收到 API 回應")

        try:
            raw_data = payload.get("data") if isinstance(payload, dict) else payload
            meta = payload.get("meta", {}) if isinstance(payload, dict) else {}

            if raw_data is None:
                raise ValueError("API 回傳缺少數據內容")

            if not self._validate_data_format(raw_data):
                raise ValueError("API 回傳數據格式無法通過驗證")

            self._pending_data_source = "api"
            processed = self._process_data(raw_data)

            self._cached_data = processed
            self._current_data = processed
            self._last_api_metadata = meta
            self._last_data_source = "api"
            self._reset_loading_state()
            self.load_progress.emit(100)
            self.status_changed.emit("API 數據載入完成")
            self.data_loaded.emit(processed)
        except Exception as exc:
            self._error(f"_on_api_success: 數據處理失敗 -> {exc}")
            self._last_error = str(exc)
            if self._allow_local_fallback:
                self._fallback_to_local("API 數據處理失敗，自動切換到本地 JSON")
            else:
                self.load_error.emit(str(exc))
                self._reset_loading_state()

    def _on_api_error(self, message: str) -> None:
        self._error(f"_on_api_error: {message}")
        self._last_error = message

        if self._allow_local_fallback:
            self._fallback_to_local("API 取得失敗，改用本地 JSON/CLI")
        else:
            self.load_error.emit(message)
            self._reset_loading_state()

    def _fallback_to_local(self, reason: str) -> None:
        self._debug(f"_fallback_to_local: {reason}")
        self.status_changed.emit(reason)
        self._pending_data_source = "local-json"
        self._load_via_local_json(self._current_api_params)

    def _load_via_local_json(self, params: Dict[str, Any]) -> bool:
        self._debug(f"_load_via_local_json -> {params}")
        # 允許基類重新管理載入狀態
        self._is_loading = False

        local_kwargs = {
            "year": params["year"],
            "race": params["race"],
            "session": params.get("session", "R"),
            "driver": params.get("driver", "all_drivers") or "all_drivers",
            "selected_driver": params.get("selected_driver"),
        }

        result = super().load_data(**local_kwargs)

        if not result:
            self._debug("_load_via_local_json: 無法啟動本地載入流程")
            self._reset_loading_state()
            self.load_error.emit("無法載入詳細圈速分析的本地資料")
        else:
            self.status_changed.emit("使用本地 JSON/CLI 取得詳細圈速分析數據")

        return result

    def _cleanup_api_worker(self) -> None:
        worker = self._api_worker
        if not worker:
            return

        self._api_worker = None

        for signal, slot in (
            (worker.progress, self._on_api_progress),
            (worker.success, self._on_api_success),
            (worker.failure, self._on_api_error),
            (worker.finished, self._cleanup_api_worker),
        ):
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass

        worker.setParent(None)
        worker.deleteLater()

    def _stop_api_worker(self) -> None:
        """
        異步停止 API Worker（方案 2: 信號驅動清理）
        ✅ 不阻塞主線程
        ✅ 使用信號自動清理
        """
        worker = self._api_worker
        if not worker:
            return

        if worker.isRunning():
            self._debug("_stop_api_worker: requesting interruption (non-blocking)")
            
            # 1. 請求中斷（非阻塞）
            worker.requestInterruption()
            worker.quit()
            
            # 2. 使用信號自動清理（當 Worker 停止時）
            def on_worker_stopped():
                """Worker 停止後自動清理"""
                self._debug("_stop_api_worker: Worker stopped, cleaning up")
                if worker:
                    worker.deleteLater()
                self._api_worker = None
            
            worker.finished.connect(on_worker_stopped)
            
            # 3. 延遲強制終止（2 秒後，但不阻塞主線程）
            from PyQt5.QtCore import QTimer
            def force_terminate():
                # ✅ 安全檢查：確保 worker 仍然有效且未被刪除
                try:
                    if worker and worker.isRunning():
                        self._debug("_stop_api_worker: worker timeout, forcing terminate()")
                        worker.terminate()
                except (RuntimeError, AttributeError):
                    # Worker 已被刪除，無需處理
                    pass
            
            QTimer.singleShot(2000, force_terminate)
        else:
            # Worker 已停止，立即清理
            self._cleanup_api_worker()

    def _reset_loading_state(self) -> None:
        self._loading = False
        self._is_loading = False

    def get_last_data_source(self) -> Optional[str]:
        """回傳最近一次資料載入來源 (api/local-json/cli-json/cache)。"""
        return self._last_data_source

    # ------------------------------------------------------------------
    # 終止/清理流程
    # ------------------------------------------------------------------

    def _on_cli_progress_updated(self, message: str) -> None:
        self._debug(f"[CLI] {message}")

    def _on_cli_output_received(self, output: str) -> None:
        self._debug(f"📤 CLI 輸出: {output}")

    def _on_cli_analysis_completed(self, success: bool, message: str) -> None:
        self._debug(f"✅ CLI 分析完成: {'成功' if success else '失敗'} - {message}")
        if success:
            self.status_changed.emit("CLI 生成完成，正在載入詳細圈速分析數據")
        else:
            self.load_error.emit(message)

    def _on_cli_worker_finished(self) -> None:
        self._debug("_on_cli_worker_finished: CLI worker finished")
        self._cleanup_cli_worker()

    def _cleanup_cli_worker(self) -> None:
        worker = self._cli_worker
        if not worker:
            return

        self._cli_worker = None
        self.cli_worker = None

        for signal, slot in (
            (worker.finished, self._on_cli_worker_finished),
            (worker.analysis_completed, self._on_cli_analysis_completed),
            (worker.output_received, self._on_cli_output_received),
            (worker.progress_updated, self._on_cli_progress_updated),
        ):
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass

        worker.setParent(None)
        worker.deleteLater()

    def _stop_cli_worker(self) -> None:
        worker = self._cli_worker
        if not worker:
            return

        if worker.isRunning():
            self._debug("_stop_cli_worker: requesting CLI worker stop (non-blocking)")
            
            # 1. 請求停止（非阻塞）
            try:
                worker.stop()
            except Exception as exc:
                self._error(f"_stop_cli_worker: stop() raised -> {exc}")
            
            # 2. 使用信號自動清理（當 Worker 停止時）
            def on_cli_worker_stopped():
                """CLI Worker 停止後自動清理"""
                self._debug("_stop_cli_worker: CLI Worker stopped, cleaning up")
                if worker:
                    worker.deleteLater()
                self._cli_worker = None
            
            worker.finished.connect(on_cli_worker_stopped)
            
            # 3. 延遲強制終止（2 秒後，但不阻塞主線程）
            from PyQt5.QtCore import QTimer
            def force_terminate_cli():
                # ✅ 安全檢查：確保 worker 仍然有效且未被刪除
                try:
                    if worker and worker.isRunning():
                        self._debug("_stop_cli_worker: worker timeout, forcing terminate()")
                        worker.terminate()
                except (RuntimeError, AttributeError):
                    # Worker 已被刪除，無需處理
                    pass
            
            QTimer.singleShot(2000, force_terminate_cli)
        else:
            # Worker 已停止，立即清理
            self._cleanup_cli_worker()

    def stop_loading(self) -> None:
        """外部停止任何正在進行的載入或分析流程。"""
        self._debug("stop_loading: 開始終止所有工作器")
        self._reset_loading_state()
        self._stop_api_worker()
        self._stop_cli_worker()

    def cleanup(self) -> None:
        """模組清理鉤子：確保離開時不留任何背景執行緒。"""
        self._debug("cleanup: 釋放詳細圈速分析管理器資源")
        self.stop_loading()
        self._cached_data = None
        self._current_data = None

    def get_last_api_metadata(self) -> Dict[str, Any]:
        """取得最近一次 API 成功回應的詳細資訊。"""
        return dict(self._last_api_metadata)
        
    def set_parameters(self, year: str, race: str, session: str):
        """設置分析參數"""
        logger.debug(f"🔧 [PARAMS] 設置分析參數: {year} {race} {session}")
        
        # 設置本地參數
        self.current_year = year
        self.current_race = race
        self.current_session = session
        logger.debug(f"🔧 [PARAMS] 本地參數設置完成: {year} {race} {session}")
        return True
        
    def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
        """更新分析參數（與 set_parameters 相同功能，提供不同的介面名稱）"""
        try:
            logger.debug(f"[UPDATE_PARAMS] 更新分析參數: {year} {race} {session}")
            result = self.set_parameters(year, race, session)
            if result:
                logger.info(f"[UPDATE_PARAMS] 更新分析參數成功: {year} {race} {session}")
            else:
                logger.error(f"[UPDATE_PARAMS] 更新分析參數失敗: {year} {race} {session}")
            return result
        except Exception as e:
            logger.error(f"[UPDATE_PARAMS] 更新分析參數失敗: {e}")
            return False
        
    def get_expected_file_patterns(self, year: int, race: str, session: str) -> List[str]:
        """取得預期的檔案模式"""
        patterns = [
            f"detailed_laptime_analysis_{year}_{race}_{session}*.json",
            f"{race}_{year}_detailed_laptime_*.json"
        ]
        return patterns
        
    def _validate_data_format(self, data: Any) -> bool:
        """驗證數據格式 - 支援 Function 28 JSON 格式"""
        if not isinstance(data, dict):
            logger.debug("數據格式錯誤：必須是字典格式")
            return False
        
        # 支援 Function 28 JSON 格式
        valid_formats = [
            "all_drivers_detailed_laptime",  # CLI -f28 主要格式
            "detailed_laptime_analysis"      # 另一種可能的格式
        ]
        
        has_valid_format = any(key in data for key in valid_formats)
        if not has_valid_format:
            logger.debug(f"數據格式錯誤：缺少必要欄位，支援格式: {valid_formats}")
            logger.debug(f"實際數據鍵值: {list(data.keys())}")
            return False
            
        return True
        
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """處理數據的具體實現"""
        return self.process_loaded_data(data)
        
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理載入的詳細圈速分析數據 - 支援 Function 28 JSON 格式"""
        try:
            if not isinstance(data, dict):
                raise ValueError("數據格式不正確：必須是字典格式")

            normalized_data, driver_payloads, driver_codes = self._normalize_driver_payload(data)

            self._raw_data_snapshot = copy.deepcopy(normalized_data)
            self._raw_driver_payloads = copy.deepcopy(driver_payloads)
            self._raw_driver_codes = list(driver_codes)

            filtered_payloads, filter_stats = self._apply_filters_to_cached_data(driver_payloads)
            self._filter_statistics = filter_stats

            if not filtered_payloads:
                raise ValueError("找不到支援的詳細圈速分析數據格式")

            # 儲存完整的原始數據與車手資訊
            self.data = normalized_data
            self.detailed_laptime_data = filtered_payloads

            filtered_driver_codes = list(filtered_payloads.keys())
            self.available_drivers = filtered_driver_codes

            if filtered_driver_codes:
                logger.debug(f"使用 {len(filtered_driver_codes)} 位車手詳細圈速數據：{filtered_driver_codes}")

            preferred_driver = None
            if isinstance(self._current_api_params, dict):
                preferred_driver = self._current_api_params.get("selected_driver")

            if preferred_driver and preferred_driver in filtered_driver_codes:
                self.selected_drivers = [preferred_driver]
            elif filtered_driver_codes:
                self.selected_drivers = [filtered_driver_codes[0]]
            else:
                self.selected_drivers = []

            # 獲取摘要數據
            if "analysis_info" in normalized_data:
                self.analysis_stats = normalized_data["analysis_info"]
            elif "metadata" in normalized_data:
                self.analysis_stats = normalized_data["metadata"]
                logger.debug("使用 metadata 作為摘要數據")
            else:
                self.analysis_stats = {}
                
            # 轉換為分析用數據格式
            processed_data = {
                "detailed_laptime_data": self._process_detailed_laptime_analysis_data(),
                "summary": self.analysis_stats,
                "metadata": data.get("metadata", {}),
                "analysis_mode": data.get("analysis_mode", "all"),
                "drivers_analyzed": normalized_data.get("drivers_analyzed", filtered_driver_codes or list(self.detailed_laptime_data.keys())),
                "selected_drivers": list(self.selected_drivers),
                "charts_data": self._prepare_detailed_laptime_chart_data(),
                "filter_settings": dict(self.filter_settings),
                "filter_statistics": copy.deepcopy(self._filter_statistics),
            }
            
            logger.debug(f"成功處理 {len(self.detailed_laptime_data)} 車手詳細圈速數據")
            
            self._cached_data = processed_data
            self._current_data = processed_data
            if self._pending_data_source:
                self._last_data_source = self._pending_data_source
            elif not self._last_data_source:
                self._last_data_source = "local-json"
            self._pending_data_source = None
            self._loading = False

            return processed_data
            
        except Exception as e:
            logger.debug(f"數據處理失敗: {e}")
            self._pending_data_source = None
            return {"error": str(e), "raw_data": data}

    def _normalize_driver_payload(
        self, raw_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
        """確保數據包含標準的多車手結構，支援單車手 JSON 轉換。"""

        normalized = raw_data
        driver_payloads: Dict[str, Any] = {}

        if isinstance(normalized.get("all_drivers_detailed_laptime"), dict):
            driver_payloads = normalized["all_drivers_detailed_laptime"]
        elif isinstance(normalized.get("detailed_laptime_analysis"), dict):
            driver_payloads = normalized["detailed_laptime_analysis"]
            normalized["all_drivers_detailed_laptime"] = driver_payloads
        elif normalized.get("driver") and isinstance(normalized.get("detailed_lap_data"), list):
            driver_code = str(normalized.get("driver")).strip().upper()
            if not driver_code:
                driver_code = "UNKNOWN"

            driver_payload = {
                "driver": driver_code,
                "success": normalized.get("success", True),
                "total_laps": normalized.get("total_laps"),
                "detailed_lap_data": normalized.get("detailed_lap_data", []),
                "smart_markers_summary": normalized.get("smart_markers_summary", {}),
                "summary_statistics": normalized.get("summary_statistics", {}),
                "analysis_metadata": normalized.get("analysis_metadata", {}),
            }

            driver_payloads = {driver_code: driver_payload}
            normalized["all_drivers_detailed_laptime"] = driver_payloads
            normalized["detailed_laptime_analysis"] = driver_payloads
            normalized.setdefault("drivers_analyzed", [driver_code])

            if "analysis_info" not in normalized:
                normalized["analysis_info"] = {
                    "total_drivers": 1,
                    "drivers": [driver_code],
                    "summary_statistics": normalized.get("summary_statistics", {}),
                    "smart_markers_summary": normalized.get("smart_markers_summary", {}),
                }
            else:
                info = normalized["analysis_info"]
                if isinstance(info, dict):
                    info.setdefault("total_drivers", 1)
                    info.setdefault("drivers", [driver_code])

            metadata = normalized.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            metadata.setdefault("driver", driver_code)
            metadata.setdefault("drivers", [driver_code])
            normalized["metadata"] = metadata
        else:
            driver_payloads = {}

        driver_codes = list(driver_payloads.keys())
        if driver_codes and "drivers_analyzed" not in normalized:
            normalized["drivers_analyzed"] = driver_codes
        return normalized, driver_payloads, driver_codes

    # ------------------------------------------------------------------
    # 過濾器整合邏輯
    # ------------------------------------------------------------------

    def _apply_global_settings(self, settings: Dict[str, Any]) -> None:
        if not isinstance(settings, dict):
            return

        self._suppress_global_sync = True
        try:
            self.update_filter_settings(
                filter_pit_laps=settings.get("filter_pit_laps"),
                filter_yellow_flags=settings.get("filter_yellow_flags"),
                filter_first_laps=settings.get("filter_first_laps"),
                sync_global=False,
                emit_signal=False,
            )
        finally:
            self._suppress_global_sync = False

    def _on_global_boxplot_settings_changed(self, settings: Dict[str, Any]) -> None:
        if self._suppress_global_sync:
            return

        self._suppress_global_sync = True
        try:
            self.update_filter_settings(
                filter_pit_laps=settings.get("filter_pit_laps"),
                filter_yellow_flags=settings.get("filter_yellow_flags"),
                filter_first_laps=settings.get("filter_first_laps"),
                sync_global=False,
            )
        finally:
            self._suppress_global_sync = False

    def update_filter_settings(
        self,
        *,
        filter_pit_laps: Optional[bool] = None,
        filter_yellow_flags: Optional[bool] = None,
        filter_first_laps: Optional[bool] = None,
        sync_global: bool = True,
        emit_signal: bool = True,
    ) -> bool:
        new_settings = dict(self.filter_settings)

        if filter_pit_laps is not None:
            new_settings["filter_pit_laps"] = bool(filter_pit_laps)
        if filter_yellow_flags is not None:
            new_settings["filter_yellow_flags"] = bool(filter_yellow_flags)
        if filter_first_laps is not None:
            new_settings["filter_first_laps"] = bool(filter_first_laps)

        if new_settings == self.filter_settings:
            return False

        self.filter_settings = new_settings

        if sync_global and not self._suppress_global_sync:
            try:
                self.settings_manager.update_boxplot_settings(
                    filter_pit_laps=self.filter_settings["filter_pit_laps"],
                    filter_yellow_flags=self.filter_settings["filter_yellow_flags"],
                    filter_first_laps=self.filter_settings["filter_first_laps"],
                )
            except Exception as exc:
                self._debug(f"無法同步全域設定: {exc}")

        self._rebuild_processed_data()

        if emit_signal:
            self.filter_settings_changed.emit(dict(self.filter_settings))

        return True

    def _apply_filters_to_cached_data(
        self, driver_payloads: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Dict[str, int]]]:
        filtered_payloads: Dict[str, Any] = {}
        statistics: Dict[str, Dict[str, int]] = {}

        for driver_code, payload in driver_payloads.items():
            if not isinstance(payload, dict):
                continue

            laps = list(payload.get("detailed_lap_data", []))
            filtered_laps: List[Any] = []
            removed_pit = 0
            removed_caution = 0
            removed_first_laps = 0
            caution_laps = extract_caution_laps(payload)
            smart_summary = payload.get("smart_markers_summary", {})

            for lap in laps:
                if not isinstance(lap, dict):
                    filtered_laps.append(lap)
                    continue
                lap_number = lap.get("lap_number") if isinstance(lap, dict) else None
                is_caution = lap_is_under_caution(lap_number, lap, caution_laps)
                is_pit = lap_is_pit_stop(lap, smart_summary)

                # 過濾前兩圈 (Lap 1 & 2)
                if self.filter_settings.get("filter_first_laps", True) and lap_number in (1, 2):
                    removed_first_laps += 1
                    continue

                if self.filter_settings.get("filter_yellow_flags", True) and is_caution:
                    removed_caution += 1
                    continue

                if self.filter_settings.get("filter_pit_laps", True) and is_pit:
                    removed_pit += 1
                    continue

                filtered_laps.append(lap)

            payload_copy = copy.deepcopy(payload)
            payload_copy["detailed_lap_data"] = filtered_laps
            payload_copy.setdefault("filters_applied", {})
            payload_copy["filters_applied"].update(
                {
                    "filter_pit_laps": bool(self.filter_settings.get("filter_pit_laps", True)),
                    "filter_yellow_flags": bool(self.filter_settings.get("filter_yellow_flags", True)),
                    "filter_first_laps": bool(self.filter_settings.get("filter_first_laps", True)),
                    "removed_pit_laps": removed_pit,
                    "removed_caution_laps": removed_caution,
                    "removed_first_laps": removed_first_laps,
                    "remaining_laps": len(filtered_laps),
                    "original_laps": len(laps),
                }
            )

            filtered_payloads[driver_code] = payload_copy
            statistics[driver_code] = {
                "removed_pit_laps": removed_pit,
                "removed_caution_laps": removed_caution,
                "removed_first_laps": removed_first_laps,
                "remaining_laps": len(filtered_laps),
                "original_laps": len(laps),
            }

        return filtered_payloads, statistics

    def _rebuild_processed_data(self) -> None:
        if not self._raw_driver_payloads:
            return

        filtered_payloads, stats = self._apply_filters_to_cached_data(self._raw_driver_payloads)
        self._filter_statistics = stats
        self.detailed_laptime_data = filtered_payloads
        self.available_drivers = list(filtered_payloads.keys())

        if self.selected_drivers:
            self.selected_drivers = [d for d in self.selected_drivers if d in self.available_drivers]
        if not self.selected_drivers and self.available_drivers:
            self.selected_drivers = [self.available_drivers[0]]

        detailed_data = self._process_detailed_laptime_analysis_data()
        charts_data = self._prepare_detailed_laptime_chart_data()

        base_summary = self.analysis_stats or {}
        base_metadata: Dict[str, Any] = {}
        base_mode = "all"

        if isinstance(self._cached_data, dict):
            base_summary = self._cached_data.get("summary", base_summary)
            base_metadata = self._cached_data.get("metadata", {})
            base_mode = self._cached_data.get("analysis_mode", base_mode)
        elif isinstance(self._raw_data_snapshot, dict):
            base_metadata = self._raw_data_snapshot.get("metadata", {})

        rebuilt_payload = {
            "detailed_laptime_data": detailed_data,
            "summary": base_summary,
            "metadata": base_metadata,
            "analysis_mode": base_mode,
            "drivers_analyzed": self._raw_data_snapshot.get("drivers_analyzed", self.available_drivers)
            if isinstance(self._raw_data_snapshot, dict)
            else self.available_drivers,
            "selected_drivers": list(self.selected_drivers),
            "charts_data": charts_data,
            "filter_settings": dict(self.filter_settings),
            "filter_statistics": copy.deepcopy(self._filter_statistics),
        }

        self._cached_data = rebuilt_payload
        self._current_data = rebuilt_payload
        self.data_loaded.emit(rebuilt_payload)
    
    def _process_detailed_laptime_analysis_data(self) -> Dict[str, List]:
        """處理詳細圈速分析數據"""
        drivers_data = []
        
        # 處理所有車手的詳細圈速數據
        for driver_code, driver_data in self.detailed_laptime_data.items():
            if isinstance(driver_data, dict):
                # 添加降雨檢測到智能標記
                enhanced_smart_markers = self._enhance_smart_markers_with_rain(driver_data)
                
                driver_info = {
                    "driver": driver_code,
                    "total_laps": driver_data.get("total_laps", 0),
                    "detailed_lap_data": driver_data.get("detailed_lap_data", []),
                    "smart_markers_summary": enhanced_smart_markers,
                    "fastest_lap": self._extract_fastest_lap(driver_data),
                    "analysis_success": driver_data.get("success", True)
                }
                drivers_data.append(driver_info)
        
        return {
            "drivers": drivers_data,
            "total_drivers": len(drivers_data)
        }
        
    def _enhance_smart_markers_with_rain(self, driver_data: Dict) -> Dict:
        """增強智能標記，添加降雨檢測 - 與降雨分析模組邏輯一致"""
        # 獲取原始智能標記
        original_markers = driver_data.get("smart_markers_summary", {})
        enhanced_markers = original_markers.copy()
        
        # 分析詳細圈速數據中的天氣信息
        detailed_laps = driver_data.get("detailed_lap_data", [])
        rain_lap_numbers = []
        
        for lap_data in detailed_laps:
            if isinstance(lap_data, dict):
                lap_number = lap_data.get("lap_number")
                weather = lap_data.get("weather")  # 布爾值：True=降雨, False=晴天
                
                # 與降雨分析模組一致的判斷邏輯：weather 為 True 時表示有雨
                if weather is True and lap_number is not None:
                    rain_lap_numbers.append(lap_number)
        
        # 添加降雨檢測結果到智能標記
        if rain_lap_numbers:
            enhanced_markers['rain_detection'] = {
                'rain_lap_numbers': rain_lap_numbers,
                'total_rain_laps': len(rain_lap_numbers),
                'rain_percentage': (len(rain_lap_numbers) / len(detailed_laps)) * 100 if detailed_laps else 0
            }
            logger.debug(f"[F28_DATA] 檢測到 {len(rain_lap_numbers)} 圈降雨 (圈數: {rain_lap_numbers})")
        else:
            enhanced_markers['rain_detection'] = {
                'rain_lap_numbers': [],
                'total_rain_laps': 0,
                'rain_percentage': 0
            }
            
        return enhanced_markers
        
    def _extract_fastest_lap(self, driver_data: Dict) -> Dict:
        """提取車手最快圈數據"""
        detailed_laps = driver_data.get("detailed_lap_data", [])
        if not detailed_laps:
            return {}
        
        # 找出最快圈
        fastest_lap = min(detailed_laps, key=lambda lap: lap.get("lap_time_seconds", float('inf')))
        return {
            "lap_number": fastest_lap.get("lap_number", 0),
            "lap_time": fastest_lap.get("lap_time", "N/A"),
            "lap_time_seconds": fastest_lap.get("lap_time_seconds", 0),
            "tire_compound": fastest_lap.get("tire_compound", "UNKNOWN")
        }
        
    def _prepare_detailed_laptime_chart_data(self) -> Dict[str, Any]:
        """準備詳細圈速圖表數據 - 構建圖表組件期望的數據結構"""
        if not hasattr(self, 'data') or not self.data:
            return {}
        
        # 構建圖表組件期望的數據結構
        chart_data = {
            "drivers_analyzed": list(self.detailed_laptime_data.keys()),
            "all_drivers_detailed_laptime": self.detailed_laptime_data,
            "detailed_laptime_analysis": self.detailed_laptime_data,
            "analysis_info": self.data.get("analysis_info", {}),
            "metadata": self.data.get("metadata", {}),
            "selected_drivers": list(self.selected_drivers),
            "filter_settings": dict(self.filter_settings),
            "filter_statistics": copy.deepcopy(self._filter_statistics),
        }
        
        logger.debug(f"圖表數據已準備：{len(chart_data['drivers_analyzed'])} 個車手")
        
        return chart_data
        
    def get_detailed_laptime_summary(self) -> Dict[str, Any]:
        """獲取詳細圈速分析摘要統計"""
        return {
            "total_drivers": len(self.detailed_laptime_data),
            "total_laps": sum(driver_data.get("total_laps", 0) 
                            for driver_data in self.detailed_laptime_data.values() 
                            if isinstance(driver_data, dict)),
            "smart_markers_available": any(
                driver_data.get("smart_markers_summary", {})
                for driver_data in self.detailed_laptime_data.values()
                if isinstance(driver_data, dict)
            ),
            "has_detailed_laptime_data": len(self.detailed_laptime_data) > 0,
            "analysis_stats": self.analysis_stats.get("summary", {})
        }
    
    # ==================== 抽象方法實現 ====================
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證載入參數"""
        required_params = ['year', 'race']
        return all(param in params for param in required_params)
    
    def _build_filename_patterns(self, **kwargs) -> List[str]:
        """構建詳細圈速分析檔案名稱搜尋模式 (Function 28)"""
        year = kwargs.get("year", "*")
        race = kwargs.get("race", "*")
        session = kwargs.get("session", "R")
        selected_driver = kwargs.get("selected_driver")

        race_safe = str(race).strip()

        patterns: List[str] = [
            f"detailed_laptime_analysis_{year}_{race_safe}_{session}.json",
            f"detailed_laptime_analysis_{year}_{race_safe}_{session}_all_drivers.json",
            f"detailed_driver_laptime_{year}_{race_safe}_{session}.json",
            f"detailed_laptime_analysis_{year}_{race_safe}_{session}.pkl",
        ]

        if selected_driver:
            driver_upper = str(selected_driver).strip().upper()
            patterns.extend([
                f"detailed_laptime_analysis_{year}_{race_safe}_{session}_{driver_upper}.json",
                f"detailed_driver_laptime_{year}_{race_safe}_{session}_{driver_upper}.json",
                f"detailed_laptime_analysis_{year}_{race_safe}_{session}_{driver_upper}.pkl",
            ])

        return patterns
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 透過 CLI -f28 工具生成詳細圈速分析數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用,系統只允許通過 API 獲取數據
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取車手圈速分析數據")
        return False
    
    def _validate_data_format(self, raw_data: Any) -> bool:
        """驗證詳細圈速分析數據格式 (Function 28)"""
        if not isinstance(raw_data, dict):
            return False
        
        # 檢查 Function 28 必要欄位
        required_fields = [
            'all_drivers_detailed_laptime',
            'drivers_analyzed',
            'success'
        ]
        return any(field in raw_data for field in required_fields)
    
    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """處理詳細圈速分析數據為標準格式 (Function 28)"""
        if not isinstance(raw_data, dict):
            return {'raw_data': raw_data}
        
        # 提取分析信息
        metadata = raw_data.get('metadata', {})
        
        # 基本元數據
        combined_metadata = {
            'year': raw_data.get('year') or metadata.get('year'),
            'race': raw_data.get('race') or metadata.get('race'), 
            'session': raw_data.get('session') or metadata.get('session'),
            'analysis_timestamp': raw_data.get('analysis_timestamp') or metadata.get('generated_at'),
            'success': raw_data.get('success', True),
            'function_id': '28',
            'analysis_type': 'detailed_laptime_analysis'
        }
        
        # 獲取車手詳細圈速數據
        detailed_laptime_data = raw_data.get('all_drivers_detailed_laptime', {})
        drivers_analyzed = raw_data.get('drivers_analyzed', list(detailed_laptime_data.keys()))
        
        logger.debug(f"[F28_DATA] 處理 Function 28 格式數據：{len(drivers_analyzed)} 個車手")
        
        return {
            'metadata': combined_metadata,
            'drivers_analyzed': drivers_analyzed,
            'all_drivers_detailed_laptime': detailed_laptime_data,
            'detailed_laptime_analysis': detailed_laptime_data,
            'raw_data': raw_data
        }


class driverLapAnalysisMDI(UniversalAnalysisMDI):
    """詳細圈速分析 MDI 類 - 實現 UniversalAnalysisMDI 介面"""
    
    # 信號定義
    driverChanged = pyqtSignal(str)  # Driver 1 變更
    driver2Changed = pyqtSignal(str)  # Driver 2 變更
    
    def __init__(self, parent=None):
        """初始化詳細圈速分析 MDI"""
        super().__init__(analysis_type='laptime', parent=parent)
        logger.debug(f"[LAPTIME_MDI] 詳細圈速分析 MDI 基類初始化完成")
        
        # 創建控制面板
        self.control_panel = None
        
        # 調用模組初始化來創建數據管理器和圖表組件
        if self.initialize_module(parent_widget=parent):
            logger.debug(f"[LAPTIME_MDI] 詳細圈速分析 MDI 完整初始化成功")
            # 初始化後創建控制面板
            self._setup_control_panel()
        else:
            logger.debug(f"[LAPTIME_MDI] 詳細圈速分析 MDI 初始化失敗")
        
    def create_data_manager(self):
        """創建數據管理器"""
        logger.debug(f"[LAPTIME_MDI] 創建詳細圈速分析數據管理器")
        manager = driverLapAnalysisDataManager(parent=self)
        manager.filter_settings_changed.connect(self._on_filter_settings_changed)
        return manager
    
    def _setup_control_panel(self):
        """設置車手控制面板"""
        try:
            logger.debug(f"[LAPTIME_MDI] 創建車手控制面板...")
            self.control_panel = DetailedLapDriverControlPanel(parent=self.main_widget)
            
            # 連接信號
            self.control_panel.driverChanged.connect(self._on_driver_changed)
            self.control_panel.driver2Changed.connect(self._on_driver2_changed)
            
            # 將控制面板添加到主界面
            if hasattr(self, 'main_widget') and self.main_widget:
                # 查找主佈局並插入控制面板
                main_layout = self.main_widget.layout()
                if main_layout and main_layout.count() > 0:
                    # 插入到頂部（索引 0）
                    main_layout.insertWidget(0, self.control_panel)
                    logger.info(f"[LAPTIME_MDI] ✅ 控制面板已插入主界面")
                else:
                    logger.warning(f"[LAPTIME_MDI] ⚠️  主界面佈局不可用")
            
            # 從主視窗獲取車手列表
            self._update_driver_list()
            
            logger.info(f"[LAPTIME_MDI] ✅ 車手控制面板設置完成")
        except Exception as e:
            logger.error(f"[LAPTIME_MDI] ❌ 控制面板設置失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_driver_list(self):
        """從主視窗更新車手列表"""
        try:
            if not self.control_panel:
                return
            
            # 獲取父視窗（主 GUI）
            parent_window = None
            if hasattr(self, 'parent_window') and self.parent_window:
                parent_window = self.parent_window
            elif hasattr(self, 'parameter_provider') and self.parameter_provider:
                # 嘗試從 parameter_provider 獲取主視窗
                parent_window = getattr(self.parameter_provider, 'main_window', None)
            
            if not parent_window:
                # 嘗試向上查找父視窗
                widget = self.main_widget
                while widget:
                    parent = widget.parent()
                    if hasattr(parent, 'get_drivers_for_year'):
                        parent_window = parent
                        break
                    widget = parent
            
            if parent_window and hasattr(parent_window, 'get_drivers_for_year'):
                year = int(self.current_year) if self.current_year else 2025
                drivers = parent_window.get_drivers_for_year(year)
                if drivers:
                    self.control_panel.set_available_drivers(drivers)
                    logger.info(f"[LAPTIME_MDI] ✅ 已載入 {len(drivers)} 位車手")
                else:
                    logger.warning(f"[LAPTIME_MDI] ⚠️  無車手數據")
            else:
                logger.warning(f"[LAPTIME_MDI] ⚠️  無法獲取主視窗引用")
        except Exception as e:
            logger.error(f"[LAPTIME_MDI] ❌ 更新車手列表失敗: {e}")
    
    def _on_driver_changed(self, driver: str):
        """處理 Driver 1 變更"""
        try:
            logger.debug(f"[LAPTIME_MDI] Driver 1 變更為: {driver}")
            self.driver1 = driver
            self.driverChanged.emit(driver)
            # 重新載入數據
            self._reload_data_with_current_params()
        except Exception as e:
            logger.error(f"[LAPTIME_MDI] ❌ Driver 1 變更處理失敗: {e}")
    
    def _on_driver2_changed(self, driver: str):
        """處理 Driver 2 變更"""
        try:
            driver2 = driver if driver else None
            logger.debug(f"[LAPTIME_MDI] Driver 2 變更為: {driver2 if driver2 else 'None'}")
            self.driver2 = driver2
            self.driver2Changed.emit(driver if driver else "")
            # 重新載入數據
            self._reload_data_with_current_params()
        except Exception as e:
            logger.error(f"[LAPTIME_MDI] ❌ Driver 2 變更處理失敗: {e}")
    
    def _reload_data_with_current_params(self):
        """使用當前參數重新載入數據"""
        try:
            if not self.data_manager:
                return
            
            # 構建載入參數
            params = {
                "year": int(self.current_year) if self.current_year else 2025,
                "race": self.current_race or "Japan",
                "session": self.current_session or "R",
                "driver": getattr(self, 'driver1', None) or "all_drivers",
                "force_refresh": False
            }
            
            logger.debug(f"[LAPTIME_MDI] 重新載入數據: {params}")
            self.data_manager.load_data(**params)
        except Exception as e:
            logger.error(f"[LAPTIME_MDI] ❌ 重新載入數據失敗: {e}")
    
    def set_parent_window(self, parent_window):
        """設置父視窗引用"""
        self.parent_window = parent_window
        # 更新車手列表
        self._update_driver_list()
        
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """覆蓋基類方法，返回純模組名稱"""
        from core.gui_i18n import tr
        translated_title = tr("detailed_lap_analysis", "Detailed Lap Analysis")
        return translated_title

    def create_chart_widget(self):
        """創建圖表組件"""
        try:
            from .driverlap_analysis_chart_widget import driverLapAnalysisChartWidget
            # 修正：不要傳遞 self 作為 parent，讓圖表組件自己處理父子關係
            chart_widget = driverLapAnalysisChartWidget()
            logger.debug(f"[LAPTIME_MDI] 詳細圈速分析圖表組件創建成功")
            return chart_widget
        except ImportError as e:
            logger.debug(f"[LAPTIME_MDI] 圖表組件導入失敗: {e}")
            # 創建一個簡單的替代組件
            from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
            from PyQt5.QtCore import Qt
            
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            label = QLabel("詳細圈速分析圖表")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("QLabel { color: blue; font-size: 16px; padding: 20px; }")
            
            status_label = QLabel("等待數據載入...")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet("QLabel { color: gray; font-size: 12px; }")
            
            layout.addWidget(label)
            layout.addWidget(status_label)
            
            # 添加一個簡單的更新方法
            def update_data(data):
                if isinstance(data, dict) and 'drivers_analyzed' in data:
                    drivers_count = len(data['drivers_analyzed'])
                    status_label.setText(f"已載入 {drivers_count} 位車手的詳細圈速數據")
                else:
                    status_label.setText("數據格式不正確")
            
            widget.update_data = update_data
            
            return widget
        except Exception as e:
            logger.debug(f"[LAPTIME_MDI] 創建詳細圈速分析圖表組件失敗: {e}")
            # 返回一個簡單的佔位符
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtCore import Qt
            placeholder = QLabel("詳細圈速分析圖表載入失敗")
            placeholder.setAlignment(Qt.AlignCenter)
            return placeholder

    def _on_filter_settings_changed(self, settings: Dict[str, Any]) -> None:
        chart = getattr(self, "chart_widget", None)
        if chart and hasattr(chart, "apply_filter_settings"):
            chart.apply_filter_settings(settings)

    def reset_chart_view(self):
        """重置圖表視圖（供全局 Show All Data 按鈕調用）"""
        try:
            chart = getattr(self, "chart_widget", None)
            if chart:
                # 嘗試調用 reset_zoom 方法
                if hasattr(chart, 'laptime_chart') and hasattr(chart.laptime_chart, 'reset_zoom'):
                    chart.laptime_chart.reset_zoom()
                    logger.debug(f"[LAPTIME_MDI] ✅ 成功調用 laptime_chart.reset_zoom()")
                elif hasattr(chart, 'reset_zoom'):
                    chart.reset_zoom()
                    logger.debug(f"[LAPTIME_MDI] ✅ 成功調用 chart_widget.reset_zoom()")
                else:
                    logger.debug(f"[LAPTIME_MDI] ⚠️  chart_widget 沒有 reset_zoom 方法")
            else:
                logger.debug(f"[LAPTIME_MDI] ⚠️  無法獲取 chart_widget")
        except Exception as e:
            logger.error(f"[LAPTIME_MDI] ❌ reset_chart_view 失敗: {e}")


# 導入專用圖表組件
from .driverlap_analysis_chart_widget import driverLapAnalysisChartWidget

from core.logger import get_logger
logger = get_logger(__name__)



class DetailedLapDriverControlPanel(QWidget):
    """
    詳細圈速分析車手控制面板
    參考 Throttle Line Chart 的 ThrottleLineChartControlPanel 實現
    提供與主 GUI 一致的 driver1/driver2 選擇邏輯
    """
    
    # 信號定義
    driverChanged = pyqtSignal(str)  # Driver 1 變更
    driver2Changed = pyqtSignal(str)  # Driver 2 變更
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._available_drivers: List[str] = []
        self._selected_driver: Optional[str] = None
        self._selected_driver2: Optional[str] = None
        self._build_ui()
    
    def _build_ui(self) -> None:
        """構建控制面板 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 車手選擇器（並排顯示以節省空間）
        drivers_layout = QHBoxLayout()
        drivers_layout.setSpacing(10)
        
        # Driver 1（左側）- 必選
        driver1_label = QLabel(tr("detailed_lap.driver1", "Driver 1"))
        driver1_label.setFixedWidth(55)
        self.driver_combo = QComboBox()
        self.driver_combo.setEditable(False)
        self.driver_combo.setMaximumWidth(100)
        self.driver_combo.currentTextChanged.connect(self._emit_driver_change)
        drivers_layout.addWidget(driver1_label)
        drivers_layout.addWidget(self.driver_combo)
        
        drivers_layout.addSpacing(10)  # 間隔
        
        # Driver 2（右側）- 選用
        driver2_label = QLabel(tr("detailed_lap.driver2", "Driver 2"))
        driver2_label.setFixedWidth(55)
        self.driver2_combo = QComboBox()
        self.driver2_combo.setEditable(False)
        self.driver2_combo.setMaximumWidth(100)
        self.driver2_combo.currentTextChanged.connect(self._emit_driver2_change)
        drivers_layout.addWidget(driver2_label)
        drivers_layout.addWidget(self.driver2_combo)
        
        drivers_layout.addStretch()  # 右側留空
        layout.addLayout(drivers_layout)
    
    def set_available_drivers(self, drivers: List[str], selected: Optional[str] = None, selected2: Optional[str] = None) -> None:
        """
        設定可用車手列表，並同時更新兩個選擇器
        與 Throttle Line Chart 和主 GUI 邏輯一致
        """
        normalized = [str(driver).upper() for driver in drivers if driver]
        if normalized == self._available_drivers:
            return
        
        self._available_drivers = normalized
        
        # ========== 更新車手1選擇器（必選） ==========
        self.driver_combo.blockSignals(True)
        self.driver_combo.clear()
        
        if not normalized:
            placeholder = tr("detailed_lap.select_driver", "Select driver")
            self.driver_combo.addItem(placeholder, "")
            self.driver_combo.setCurrentIndex(0)
            self._selected_driver = None
        else:
            for code in normalized:
                self.driver_combo.addItem(code, code)
            
            # 預設選擇邏輯：優先使用 selected，否則第一位
            desired = (selected or self._selected_driver or normalized[0]).upper()
            if desired not in normalized:
                desired = normalized[0]
            
            index = self.driver_combo.findData(desired)
            if index == -1:
                index = self.driver_combo.findText(desired)
            if index != -1:
                self.driver_combo.setCurrentIndex(index)
                self._selected_driver = desired
            else:
                self.driver_combo.setCurrentIndex(0)
                self._selected_driver = normalized[0]
        
        self.driver_combo.blockSignals(False)
        
        # ========== 更新車手2選擇器（選用） ==========
        self.driver2_combo.blockSignals(True)
        self.driver2_combo.clear()
        
        if not normalized:
            placeholder = tr("detailed_lap.select_driver", "Select driver")
            self.driver2_combo.addItem(placeholder, "")
            self.driver2_combo.setCurrentIndex(0)
            self._selected_driver2 = None
        else:
            # 添加「無」選項（與主 GUI 一致）
            self.driver2_combo.addItem(tr("none_option", "None"), "")
            for code in normalized:
                self.driver2_combo.addItem(code, code)
            
            # 預設為 None（與主 GUI 和 Throttle Line Chart 一致）
            if selected2 and selected2.upper() in normalized:
                desired2 = selected2.upper()
                index = self.driver2_combo.findData(desired2)
                if index == -1:
                    index = self.driver2_combo.findText(desired2)
                if index != -1:
                    self.driver2_combo.setCurrentIndex(index)
                    self._selected_driver2 = desired2
                else:
                    self.driver2_combo.setCurrentIndex(0)
                    self._selected_driver2 = None
            else:
                # 未指定 selected2，預設為 None
                self.driver2_combo.setCurrentIndex(0)
                self._selected_driver2 = None
        
        self.driver2_combo.blockSignals(False)
    
    def _emit_driver_change(self, value: str) -> None:
        """發射 Driver 1 變更訊號"""
        driver = str(value).strip().upper()
        if not driver:
            return
        if driver == self._selected_driver:
            return
        self._selected_driver = driver
        logger.debug(f"[DETAILED_LAP_CTRL] Driver 1 變更: {driver}")
        self.driverChanged.emit(driver)
    
    def _emit_driver2_change(self, value: str) -> None:
        """發射 Driver 2 變更訊號"""
        driver = str(value).strip().upper()
        # 允許空值（表示取消第二位車手）
        if driver == self._selected_driver2:
            return
        self._selected_driver2 = driver if driver else None
        logger.debug(f"[DETAILED_LAP_CTRL] Driver 2 變更: {driver if driver else 'None'}")
        self.driver2Changed.emit(driver if driver else "")
    
    def get_selected_driver(self) -> Optional[str]:
        """獲取當前選擇的 Driver 1"""
        return self._selected_driver
    
    def get_selected_driver2(self) -> Optional[str]:
        """獲取當前選擇的 Driver 2"""
        return self._selected_driver2


class driverLapAnalysisControlWidget(QWidget):
    """詳細圈速分析控制面板"""
    
    # 信號定義
    chart_type_changed = pyqtSignal(str)
    parameter_changed = pyqtSignal(str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        
        # 圖表選擇群組
        chart_group = QGroupBox("圖表類型")
        chart_layout = QGridLayout(chart_group)
        
        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            "詳細圈速分析",
            "圈速趨勢比較",
            "智能標記顯示"
        ])
        self.chart_combo.currentTextChanged.connect(self._on_chart_type_changed)
        
        chart_layout.addWidget(QLabel(tr("select_chart", "選擇圖表:")), 0, 0)
        chart_layout.addWidget(self.chart_combo, 0, 1)
        
        layout.addWidget(chart_group)
        
        # 顯示選項群組
        display_group = QGroupBox("顯示選項")
        display_layout = QGridLayout(display_group)
        
        self.show_grid_cb = QCheckBox("顯示網格")
        self.show_grid_cb.setChecked(True)
        self.show_grid_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_grid", x))
        
        self.show_legend_cb = QCheckBox("顯示圖例")
        self.show_legend_cb.setChecked(True)
        self.show_legend_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_legend", x))
        
        display_layout.addWidget(self.show_grid_cb, 0, 0)
        display_layout.addWidget(self.show_legend_cb, 0, 1)
        
        layout.addWidget(display_group)
        
        layout.addStretch()
        
    def _on_chart_type_changed(self, text: str):
        """圖表類型改變處理"""
        chart_type_map = {
            "詳細圈速分析": "laptime_analysis",
            "圈速趨勢比較": "laptime_trends",
            "智能標記顯示": "smart_markers"
        }
        
        chart_type = chart_type_map.get(text, "laptime_analysis")
        self.chart_type_changed.emit(chart_type)


# 模組註冊 - 確保在導入時自動註冊
def register_detailed_laptime_analysis_module():
    """註冊詳細圈速分析模組"""
    try:
        # 這裡可以添加到全局模組註冊表
        pass
    except Exception as e:
        logger.warning(f"詳細圈速分析模組註冊失敗: {str(e)}")

# 執行註冊
register_detailed_laptime_analysis_module()
