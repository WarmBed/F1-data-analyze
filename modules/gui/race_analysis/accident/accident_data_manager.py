#!/usr/bin/env python3
"""Accident analysis data manager with API-first workflow."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from core.api_base_url import resolve_api_base_url
from core.api_runtime_state import is_api_available
from PyQt5.QtCore import QObject, QThread, Qt, pyqtSignal

try:
    from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader
    from core.gui_i18n import tr
except ImportError:  # pragma: no cover - fallback for relative import during packaging
    from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader
    from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)


class AccidentAnalysisApiWorker(QThread):
    """Background worker responsible for fetching accident analysis data via REST API."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(
        self,
        base_url: str,
        function_id: str,
        params: Dict[str, Any],
        *,
        timeout: float = 60.0,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.base_url = (base_url or "https://localhost:8000").rstrip("/")
        self.function_id = str(function_id)
        self.params = dict(params)
        self.timeout = float(timeout)

    def run(self) -> None:  # pragma: no cover - executed in worker thread
        try:
            # 檢查是否已被請求中斷
            if self.isInterruptionRequested():
                logger.debug("[ACCIDENT_API_WORKER] 啟動前已被請求中斷，跳過執行")
                return
                
            self.progress.emit(15)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": self.function_id,
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }

            driver1 = self.params.get("driver1")
            driver2 = self.params.get("driver2")
            if driver1:
                query_params["driver1"] = str(driver1).upper()
            if driver2:
                query_params["driver2"] = str(driver2).upper()
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True

            # 再次檢查中斷（在發送請求前）
            if self.isInterruptionRequested():
                logger.debug("[ACCIDENT_API_WORKER] 發送請求前被請求中斷")
                return
                
            self.progress.emit(45)
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
            )
            
            # 請求完成後檢查中斷（避免在 widget 已銷毀後發送信號）
            if self.isInterruptionRequested():
                logger.debug("[ACCIDENT_API_WORKER] API 回應後被請求中斷，放棄處理結果")
                return
                
            self.progress.emit(70)
            
            # ✅ 修復：優雅處理 HTTP 錯誤（特別是 429）
            if response.status_code == 429:
                # API 限流錯誤 - 不要彈窗，靜默失敗
                self.failure.emit("API 請求過於頻繁，請稍後再試 (429 Too Many Requests)")
                return
            elif response.status_code >= 500:
                # 伺服器錯誤
                self.failure.emit(f"API 伺服器錯誤 ({response.status_code})")
                return
            elif response.status_code >= 400:
                # 客戶端錯誤（除了 429）
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", response.text)
                except Exception:
                    error_msg = response.text or response.reason
                self.failure.emit(f"API 請求錯誤 ({response.status_code}): {error_msg}")
                return
            
            response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be a JSON object")
            if not payload.get("success", False):
                message = payload.get("message", "API returned success=False")
                raise RuntimeError(message)

            data = payload.get("data")
            if data is None:
                raise ValueError("API response missing 'data'")

            meta = {
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "function_spec": payload.get("function_spec"),
                "endpoint": endpoint,
            }

            # 發送信號前最後檢查中斷（避免向已銷毀的 widget 發送信號）
            if self.isInterruptionRequested():
                logger.debug("[ACCIDENT_API_WORKER] 發送成功信號前被請求中斷，放棄發送")
                return
                
            self.progress.emit(95)
            self.success.emit(
                {
                    "function_id": self.function_id,
                    "data": data,
                    "payload": payload,
                    "meta": meta,
                }
            )
        except Exception as exc:  # pragma: no cover - reported to GUI
            # 如果被中斷，不發送失敗信號
            if not self.isInterruptionRequested():
                self.failure.emit(str(exc))
        finally:
            # 只有在未中斷時才發送完成信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class AccidentDataManager(UniversalDataLoader):
    """API-first data manager for the accident analysis module."""

    statistics_loaded = pyqtSignal(dict)
    statistics_reload_requested = pyqtSignal()
    all_incidents_loaded = pyqtSignal(dict)
    all_incidents_reload_requested = pyqtSignal()
    severity_loaded = pyqtSignal(dict)
    key_events_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    loading_progress = pyqtSignal(int)
    status_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        if "accident_api" not in UniversalDataLoader.ANALYSIS_TYPES:
            UniversalDataLoader.register_analysis_type(
                "accident_api",
                AnalysisConfig(
                    display_name="事故分析 (API)",
                    debug_prefix="ACCIDENT_API",
                    data_source="api",
                    cli_function="8",
                    api_endpoint="/api/v2/analysis/execute",
                    api_function_id="8",
                    api_timeout=90.0,
                    file_patterns=[
                        "all_incidents_summary_{year}_{race}_{session}.json",
                        "all_incidents_summary_{year}_{race}.json",
                        "raw_data_all_incidents_{year}_{race}_*.json",
                        "incident_details_{year}_{race}_{session}.json",
                        "accident_statistics_summary_{year}_{race}_{session}.json",
                    ],
                    search_directories=["json", "json_exports", "cache"],
                    cache_enabled=True,
                ),
            )

        super().__init__("accident_api", parent)

        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[AccidentAnalysisApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._pending_function_id: str = str(getattr(self.config, "api_function_id", "8"))
        self._current_target: str = "statistics"
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        (
            self._allow_local_fallback,
            self._fallback_policy_reason,
        ) = self._resolve_local_fallback_policy()

        self.data_loaded.connect(self._handle_local_data_loaded)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def loadAccidentStatistics(
        self,
        year: int | str,
        race: str,
        session: str,
        *,
        force_refresh: bool = False,
    ) -> bool:
        return self._request_analysis(
            target="statistics",
            function_id=str(getattr(self.config, "api_function_id", "8")),
            year=year,
            race=race,
            session=session,
            force_refresh=force_refresh,
        )

    def loadAllIncidentsSummary(
        self,
        year: int | str,
        race: str,
        session: str,
        *,
        force_refresh: bool = False,
    ) -> bool:
        return self.load_all_incidents_data(
            year, race, session, force_refresh=force_refresh
        )

    def load_all_incidents_data(
        self,
        year: int | str,
        race: str,
        session: str,
        *,
        force_refresh: bool = False,
    ) -> bool:
        return self._request_analysis(
            target="incidents",
            function_id=str(getattr(self.config, "api_function_id", "8")),
            year=year,
            race=race,
            session=session,
            force_refresh=force_refresh,
        )

    def get_last_data_source(self) -> str:
        return self._last_data_source

    def get_last_api_metadata(self) -> Dict[str, Any]:
        return dict(self._last_api_meta)

    def set_api_base_url(self, base_url: Optional[str]) -> None:
        if base_url:
            self._api_base_url = str(base_url).rstrip("/")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request_analysis(
        self,
        *,
        target: str,
        function_id: str,
        year: int | str,
        race: str,
        session: str,
        force_refresh: bool = False,
    ) -> bool:
        # ⚠️ 事故分析僅支援正賽 (R) 和排位賽 (Q)
        if session not in ['R', 'Q']:
            self._debug(f"⚠️  事故分析僅支援正賽 (R) 和排位賽 (Q)，當前賽段: {session}")
            self.error_occurred.emit(tr("accident_session_restriction", "事故分析僅適用於正賽 (R) 和排位賽 (Q)，練習賽無賽會控制訊息"))
            return False
        
        params = {
            "year": int(year),
            "race": race,
            "session": session,
            "force_refresh": bool(force_refresh),
        }

        if self._is_loading:
            self._debug("已有載入請求執行中，忽略新的請求")
            return False

        if not self._validate_load_parameters(params):
            self._error("載入參數驗證失敗")
            self.error_occurred.emit(tr('invalid_load_parameters', 'Invalid load parameters'))
            return False

        self._is_loading = True
        self._pending_params = params
        self._pending_function_id = str(function_id)
        self._current_target = target
        self._api_base_url = self._determine_api_base_url()

        self.loading_progress.emit(5)
        self.status_changed.emit(
            f"透過 API 載入事故分析資料 (功能 {self._pending_function_id})..."
        )

        if not self._is_api_available():
            self._debug("API 健康檢查失敗，跳過背景執行緒啟動")
            self._is_loading = False
            self.status_changed.emit("API 服務不可用，請啟動 API 或使用本地資料")
            if self._allow_local_fallback:
                self._fallback_to_local("API 不可用")
                return True
            self.error_occurred.emit("API 服務不可用且未啟用本地 JSON 後備")
            return False

        try:
            self._start_api_request()
            return True
        except Exception as exc:  # pragma: no cover - reported to GUI
            self._is_loading = False
            self._error(f"啟動 API 請求失敗: {exc}")
            if self._allow_local_fallback:
                self.status_changed.emit("API 載入啟動失敗，嘗試使用本地資料")
                self._fallback_to_local(str(exc))
                return True
            else:
                self.status_changed.emit("API 載入啟動失敗且未啟用本地 JSON 後備")
                self.error_occurred.emit(f"API 請求失敗: {exc}")
                return False

    def _start_api_request(self) -> None:
        self._cleanup_api_worker()

        timeout = getattr(self.config, "api_timeout", 90.0)
        self._api_worker = AccidentAnalysisApiWorker(
            self._api_base_url,
            self._pending_function_id,
            self._pending_params,
            timeout=timeout,
            parent=self,
        )
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker, Qt.QueuedConnection)
        self._api_worker.start()

    # ------------------------------------------------------------------
    # API callbacks
    # ------------------------------------------------------------------

    def _on_api_progress(self, value: int) -> None:
        bounded = max(0, min(int(value), 100))
        self.loading_progress.emit(bounded)

    def _on_api_success(self, packet: Dict[str, Any]) -> None:  # pragma: no cover - GUI path
        try:
            data = packet.get("data")
            if not self._validate_data_format(data):
                raise ValueError("API 回傳數據格式不符預期")

            self._last_data_source = "api"
            self._last_api_meta = packet.get("meta", {})
            processed_data = self._process_data(data)
            normalized_data = self._normalize_incident_payload(processed_data)
            self._current_data = normalized_data

            self.loading_progress.emit(100)
            self.status_changed.emit("已透過 API 載入事故分析資料")
            self._is_loading = False

            self._dispatch_loaded_data(normalized_data)
        except Exception as exc:
            self._error(f"處理 API 數據失敗: {exc}")
            self._is_loading = False
            if self._allow_local_fallback:
                self.status_changed.emit("API 資料錯誤，改用本地資料")
                self._fallback_to_local(str(exc))
            else:
                self.status_changed.emit("API 資料錯誤且未啟用本地 JSON 後備")
                self.error_occurred.emit(f"API 數據處理失敗: {exc}")

    def _on_api_error(self, message: str) -> None:  # pragma: no cover - GUI path
        self._error(f"API 請求失敗: {message}")
        self._is_loading = False
        
        # ✅ 修復：如果是 429 錯誤，靜默處理不彈窗
        is_rate_limit = "429" in message or "Too Many Requests" in message
        
        if self._allow_local_fallback:
            self.status_changed.emit("API 請求失敗，改用本地資料")
            self._fallback_to_local(message)
        else:
            if is_rate_limit:
                # 429 錯誤：靜默處理，只發送狀態訊息
                self.status_changed.emit("API 請求過於頻繁，請稍後手動重新載入")
                # ❌ 不發送 error_occurred 信號，避免彈窗
                logger.warning(f"[ACCIDENT_API] ⚠️ API 限流 (429): {message}")
            else:
                # 其他錯誤：正常處理
                self.status_changed.emit("API 請求失敗且未啟用本地 JSON 後備")
                self.error_occurred.emit(f"API 請求失敗: {message}")

    def _cleanup_api_worker(self) -> None:
        if not self._api_worker:
            return
        try:
            self._api_worker.progress.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.success.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.failure.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.finished.disconnect()
        except Exception:
            pass
        self._api_worker.deleteLater()
        self._api_worker = None

    # ------------------------------------------------------------------
    # Local fallback + data dispatch
    # ------------------------------------------------------------------

    def _fallback_to_local(self, reason: str) -> None:
        if not self._allow_local_fallback:
            self._last_data_source = "local-fallback-disabled"
            message = (
                "API 載入失敗且本地 JSON 後備已停用。"
                " 若需啟用，請設定環境變數 F1T_ALLOW_ACCIDENT_JSON_FALLBACK=1。"
            )
            self.error_occurred.emit(message)
            return

        self._debug(f"啟動本地 JSON/CLI 後備流程: {reason}")
        self.status_changed.emit("使用本地 JSON/CLI 後備載入事故資料...")
        self._last_data_source = "local-json"
        super().load_data(**self._pending_params)

    def _handle_local_data_loaded(self, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            self.error_occurred.emit(tr('local_data_format_error', 'Local data format error'))
            return

        normalized_data = self._normalize_incident_payload(data)
        self._last_data_source = "local-json"
        self._last_api_meta = {}
        self._current_data = normalized_data
        self._dispatch_loaded_data(normalized_data)

    def _dispatch_loaded_data(self, data: Dict[str, Any]) -> None:
        target = self._current_target or "statistics"
        normalized_data = self._normalize_incident_payload(data)

        incidents_payload = {}
        if isinstance(normalized_data, dict):
            payload_candidate = normalized_data.get("data")
            if isinstance(payload_candidate, dict):
                incidents_payload = payload_candidate

        incidents_list = (
            incidents_payload.get("all_incidents")
            if isinstance(incidents_payload, dict)
            else None
        )

        if target == "statistics":
            self.statistics_loaded.emit(normalized_data)
            if incidents_list is not None:
                self.all_incidents_loaded.emit(normalized_data)
            if isinstance(incidents_payload, dict):
                if "severity_distribution" in incidents_payload:
                    self.severity_loaded.emit(normalized_data)
                if "key_events" in incidents_payload:
                    self.key_events_loaded.emit(normalized_data)
        elif target == "incidents":
            self.all_incidents_loaded.emit(normalized_data)
        else:
            # 預設回傳給統計視圖
            self.statistics_loaded.emit(normalized_data)

    def _normalize_incident_payload(self, data: Any) -> Dict[str, Any]:
        """確保資料結構包含 all_incidents 欄位以供 GUI 使用。"""

        if isinstance(data, dict):
            normalized: Dict[str, Any] = deepcopy(data)
        elif isinstance(data, list):
            normalized = {"data": {"all_incidents": deepcopy(data)}}
        else:
            normalized = {"data": {}}

        payload = normalized.get("data")
        if isinstance(payload, list):
            payload = {"all_incidents": deepcopy(payload)}
            normalized["data"] = payload
        elif not isinstance(payload, dict):
            payload = {}
            normalized["data"] = payload

        incidents = self._extract_incident_list_from_structure(normalized)
        if incidents is None:
            payload.setdefault("all_incidents", [])
        else:
            payload["all_incidents"] = incidents

        return normalized

    def _extract_incident_list_from_structure(
        self, structure: Any
    ) -> Optional[List[Dict[str, Any]]]:
        """在巢狀結構中尋找事故列表。"""

        target_keys = {"all_incidents", "incidents", "incident_records", "incident_list"}
        visited: Set[int] = set()

        def _search(node: Any) -> Optional[List[Dict[str, Any]]]:
            node_id = id(node)
            if node_id in visited:
                return None
            visited.add(node_id)

            if isinstance(node, dict):
                for key in target_keys:
                    value = node.get(key)
                    if isinstance(value, list):
                        return value
                for value in node.values():
                    result = _search(value)
                    if result is not None:
                        return result
            elif isinstance(node, list):
                for item in node:
                    result = _search(item)
                    if result is not None:
                        return result
            return None

        return _search(structure)

    # ------------------------------------------------------------------
    # UniversalDataLoader overrides
    # ------------------------------------------------------------------

    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")
        return all(value not in (None, "") for value in (year, race, session))

    def _build_filename_patterns(
        self,
        *,
        year: int | str,
        race: str,
        session: str,
        **_: Any,
    ) -> List[str]:
        race_variants = self._resolve_race_variants(race)
        patterns: List[str] = []
        for base in getattr(self.config, "file_patterns", []):
            for race_name in race_variants:
                filename = base.format(
                    year=year,
                    race=race_name,
                    session=session,
                )
                patterns.append(filename)
        return patterns

    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] CLI 事故分析數據生成
        
        ⚠️ API-ONLY 模式: 此方法已禁用,系統只允許通過 API 獲取數據
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取事故分析數據")
        return False

    def _validate_data_format(self, raw_data: Any) -> bool:
        if not isinstance(raw_data, dict):
            return False
        return True

    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        if isinstance(raw_data, dict):
            return raw_data
        if isinstance(raw_data, str):
            try:
                return json.loads(raw_data)
            except json.JSONDecodeError:
                raise ValueError("無法解析事故分析 JSON 數據")
        raise ValueError("不支援的事故分析數據格式")

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _determine_api_base_url(self) -> str:
        return resolve_api_base_url(event_logger=self._debug)

    def _is_api_available(self) -> bool:
        available = is_api_available()
        if not available:
            self._debug("API marked offline by shared runtime cache")
        return available

    def _resolve_local_fallback_policy(self) -> Tuple[bool, str]:
        """
        ⚠️ API-ONLY 模式: 預設禁用本地 JSON 後備
        
        根據 API-ONLY 政策，GUI 模組必須強制使用 API 獲取數據。
        只有明確設置環境變數才允許本地 JSON 後備（僅用於開發/調試）。
        """
        env_value = os.getenv("F1T_ALLOW_ACCIDENT_JSON_FALLBACK")
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True, f"環境變數 F1T_ALLOW_ACCIDENT_JSON_FALLBACK={env_value}"
            return False, f"環境變數 F1T_ALLOW_ACCIDENT_JSON_FALLBACK={env_value}"
        # ⚠️ API-ONLY 模式: 預設禁用本地 JSON 後備
        return False, "API-ONLY 模式（預設政策）"

    def _resolve_race_variants(self, race: str) -> List[str]:
        if not race:
            return [""]
        variants = {race}
        variants.add(race.replace(" ", "_"))
        variants.add(race.replace(" ", ""))
        variants.add(race.title().replace(" ", "_"))
        if "Grand Prix" not in race and "_Grand_Prix" not in race:
            variants.add(f"{race}_Grand_Prix")
            variants.add(f"{race.replace(' ', '_')}_Grand_Prix")
        return list(variants)

    def _debug(self, message: str) -> None:
        prefix = getattr(self.config, "debug_prefix", "ACCIDENT")
        logger.debug(f"[{prefix} DEBUG] {message}")

    def _error(self, message: str) -> None:
        prefix = getattr(self.config, "debug_prefix", "ACCIDENT")
        logger.error(f"[{prefix}] {message}")
    
    def cleanup(self) -> None:
        """
        清理資源並停止所有背景執行緒
        
        當 AccidentAnalysisModule 關閉時調用此方法。
        確保 API worker 執行緒被正確終止，避免 QThread 警告。
        """
        logger.info("[ACCIDENT_DATA_MANAGER] 開始清理資源...")
        try:
            # 停止並清理 API worker
            if self._api_worker and self._api_worker.isRunning():
                logger.debug("[ACCIDENT_DATA_MANAGER] 正在停止 API worker 執行緒...")
                
                # 階段 1: 嘗試正常停止 (wait 1 秒)
                if not self._api_worker.wait(1000):
                    logger.debug("[ACCIDENT_DATA_MANAGER] wait() 超時，嘗試 requestInterruption()...")
                    
                    # 階段 2: 請求中斷並等待
                    self._api_worker.requestInterruption()
                    if not self._api_worker.wait(500):
                        logger.warning("[ACCIDENT_DATA_MANAGER] requestInterruption() 失敗，強制 terminate()...")
                        
                        # 階段 3: 強制終止
                        self._api_worker.terminate()
                        self._api_worker.wait(500)
                
                logger.debug("[ACCIDENT_DATA_MANAGER] API worker 執行緒已停止")
            
            # 清理 worker 引用
            self._cleanup_api_worker()
            
            # 調用父類的 cleanup() 清理計時器和信號
            super().cleanup()
            
            logger.info("[ACCIDENT_DATA_MANAGER] 資源清理完成")
        except Exception as e:
            logger.error(f"[ACCIDENT_DATA_MANAGER] 清理時發生錯誤: {e}")
