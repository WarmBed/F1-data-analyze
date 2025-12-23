"""ThrottleLineChartDataLoader - 單車手油門折線圖資料處理器."""

from __future__ import annotations

import copy
import os
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from core.api_base_url import resolve_api_base_url
from core.gui_settings_manager import gui_settings_manager
from core.logger import get_logger
from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader
from modules.gui.driver_race.detailed_lap_analysis.lap_filter_utils import (
    extract_caution_laps,
    extract_red_flag_laps,
    lap_is_pit_stop,
    lap_is_under_caution,
    lap_is_under_red_flag,
)


_ANALYSIS_KEY = "throttle_line_chart_single_driver"
logger = get_logger(component="ThrottleLineChartDataLoader")


# ========================================================================
# API Worker - 背景執行緒呼叫 REST API
# ========================================================================
class ThrottleLineChartApiWorker(QThread):
    """背景工作執行緒，呼叫 REST API 取得油門分析資料（Function 54）。"""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 90.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "https://localhost:8000").rstrip("/")
        self.params = dict(params)
        self.timeout = timeout

    def run(self) -> None:  # pragma: no cover - thread run
        try:
            # 檢查是否已被請求中斷
            if self.isInterruptionRequested():
                logger.debug("[THROTTLE_LINE_API_WORKER] 啟動前已被請求中斷，跳過執行")
                return
                
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

            # 再次檢查中斷（在發送請求前）
            if self.isInterruptionRequested():
                logger.debug("[THROTTLE_LINE_API_WORKER] 發送請求前被請求中斷")
                return
                
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
            
            # 請求完成後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[THROTTLE_LINE_API_WORKER] API 回應後被請求中斷，放棄處理結果")
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
            }

            # 發送信號前最後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[THROTTLE_LINE_API_WORKER] 發送成功信號前被請求中斷，放棄發送")
                return
                
            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
        except Exception as exc:  # pragma: no cover - network errors
            # 如果被中斷，不發送失敗信號
            if not self.isInterruptionRequested():
                self.failure.emit(str(exc))
        finally:
            # 只有在未中斷時才發送完成信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class ThrottleLineChartDataLoader(UniversalDataLoader):
    """Function 54 JSON → 單車手折線圖所需結構的轉換器（支援 API 和 JSON）。"""

    def __init__(self, parent: Optional[QObject] = None):
        if _ANALYSIS_KEY not in UniversalDataLoader.ANALYSIS_TYPES:
            config = AnalysisConfig(
                display_name="Throttle Line Chart (Single Driver)",
                debug_prefix="THROTTLE-LINE",
                data_source="api",  # 🔧 FIX: 改為 API 優先 (EXE 環境修復)
                cli_function="54",
                api_endpoint="/api/v2/analysis/execute",  # ✅ 新增 API 支援
                api_function_id=54,  # ✅ Function 54
                api_timeout=90.0,  # ✅ API 超時設定
                file_patterns=[
                    "throttle_ratio_{year}_{race}_{session}.json",
                    "throttle_ratio_{year}_{race}_{session}_*.json",
                ],
                search_directories=["json", "json_exports", "cache"],  # ✅ JSON 後備目錄
                supports_realtime=False,  # ✅ 不支援即時更新
                cache_enabled=True,  # ✅ 啟用緩存
            )
            UniversalDataLoader.register_analysis_type(_ANALYSIS_KEY, config)

        super().__init__(_ANALYSIS_KEY, parent)
        self.cli_function = "54"
        self.analysis_name = "Throttle Line Chart (Single Driver)"
        self._target_driver: Optional[str] = None
        self._cached_metadata: Dict[str, Any] = {}
        self._cached_chart_payload: Dict[str, Any] = {}
        self._last_raw_data: Optional[Dict[str, Any]] = None
        self._filter_pit_laps: bool = True
        self._filter_yellow_flags: bool = True
        self._filter_red_flags: bool = True
        self._filter_first_laps: bool = True
        self._filter_statistics: Dict[str, Any] = {}
        self.settings_manager = gui_settings_manager

        # 🔧 API 支援屬性 (仿照 ThrottleBoxPlot)
        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[ThrottleLineChartApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        self._allow_local_fallback, self._fallback_policy_reason = self._resolve_local_fallback_policy()
        self._debug(
            f"本地 JSON 後備已{'啟用' if self._allow_local_fallback else '停用'} (策略: {self._fallback_policy_reason})"
        )

        # 🔍 DEBUG: 讀取初始過濾設定
        initial_filters = self.settings_manager.get_boxplot_settings()
        logger.debug(
            "[DataLoader.__init__] Initial filters from settings_manager: %s", initial_filters
        )
        logger.debug(
            "[DataLoader.__init__] Current filter attributes BEFORE update: pit=%s, yellow=%s, red=%s, first_laps=%s",
            self._filter_pit_laps,
            self._filter_yellow_flags,
            self._filter_red_flags,
            self._filter_first_laps,
        )
        
        self.update_filter_settings(
            filter_pit_laps=initial_filters.get("filter_pit_laps", True),
            filter_yellow_flags=initial_filters.get("filter_yellow_flags", True),
            filter_red_flags=initial_filters.get("filter_red_flags", True),
            filter_first_laps=initial_filters.get("filter_first_laps", True),
            reprocess=False,
        )
        
        logger.debug(
            "[DataLoader.__init__] Current filter attributes AFTER update: pit=%s, yellow=%s, red=%s, first_laps=%s",
            self._filter_pit_laps,
            self._filter_yellow_flags,
            self._filter_red_flags,
            self._filter_first_laps,
        )

        try:
            self.settings_manager.boxplot_settings_changed.connect(
                self._on_global_filter_settings_changed
            )
            logger.debug("[DataLoader.__init__] Successfully connected to boxplot_settings_changed signal")
        except Exception as exc:  # pragma: no cover - defensive logging
            self._debug(f"無法連接系統設定信號: {exc}")
            logger.exception("[DataLoader.__init__] Failed to connect signal", exc_info=exc)

    # ========================================================================
    # API 支援方法 (仿照 ThrottleBoxPlot)
    # ========================================================================
    def _determine_api_base_url(self) -> str:
        """取得 API 基礎網址（優先使用公開網域）。"""
        return resolve_api_base_url(event_logger=self._debug)

    def _resolve_local_fallback_policy(self) -> Tuple[bool, str]:
        """解析本地 JSON 後備政策（環境變數或預設）。"""
        env_value = os.getenv("F1T_ALLOW_THROTTLE_JSON_FALLBACK")
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True, f"環境變數 F1T_ALLOW_THROTTLE_JSON_FALLBACK={env_value}"
            return False, f"環境變數 F1T_ALLOW_THROTTLE_JSON_FALLBACK={env_value}"
        return True, "預設策略 (允許本地 JSON 後備)"

    def set_local_fallback_allowed(self, allowed: bool, reason: Optional[str] = None) -> None:
        """設定是否允許本地 JSON 後備。"""
        self._allow_local_fallback = bool(allowed)
        self._fallback_policy_reason = reason or "手動覆寫"
        state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(f"本地 JSON 後備已{state} (策略: {self._fallback_policy_reason})")

    def load_data(self, **kwargs) -> bool:
        """
        覆寫基類的 load_data 方法，支援 API 優先模式。
        
        🔧 FIX: 基類只支援 JSON 檔案搜尋，此處實作 API 呼叫邏輯。
        """
        # 如果不是 API 模式，使用基類的 JSON 載入
        if self.config.data_source != "api":
            return super().load_data(**kwargs)

        # API 模式 - 自訂處理流程
        if self._is_loading:
            self._debug("已有載入請求執行中，忽略新的請求")
            return False

        if not self._validate_load_parameters(kwargs):
            self._error("API 載入參數驗證失敗")
            self.load_error.emit("載入參數不正確")
            return False

        self._is_loading = True
        self._pending_params = dict(kwargs)
        self._api_base_url = self._determine_api_base_url()
        self._debug(f"透過 API 載入油門資料: base_url={self._api_base_url}, params={self._pending_params}")
        self.load_progress.emit(5)
        self.status_changed.emit("正在透過 API 載入油門分析資料...")

        try:
            self._start_api_request(self._pending_params)
            return True
        except Exception as exc:
            self._error(f"啟動 API 請求失敗: {exc}")
            self._is_loading = False
            # API 失敗時，嘗試本地 JSON 後備（如果允許）
            if self._allow_local_fallback:
                self._debug("API 載入失敗，嘗試本地 JSON 後備")
                self.status_changed.emit("API 載入失敗，改用本地資料")
                return super().load_data(**kwargs)
            else:
                self._error("API 載入失敗且本地 JSON 後備已停用")
                self.load_error.emit(f"API 載入失敗: {exc}")
                return False

    def load_data_from_local(self, **kwargs) -> bool:
        """手動診斷模式：強制使用本地 JSON 後備流程。"""
        previous_state = self._allow_local_fallback
        previous_reason = self._fallback_policy_reason
        try:
            self._allow_local_fallback = True
            self._fallback_policy_reason = "手動診斷模式"
            self._debug("以手動模式使用本地 JSON 後備流程")
            return super().load_data(**kwargs)
        finally:
            self._allow_local_fallback = previous_state
            self._fallback_policy_reason = previous_reason

    def _start_api_request(self, params: Dict[str, Any]) -> None:
        """啟動 API 請求背景執行緒。"""
        self._cleanup_api_worker()

        worker_params = {
            "year": params.get("year"),
            "race": params.get("race"),
            "session": params.get("session"),
            "force_refresh": params.get("force_refresh", False),
        }

        timeout = getattr(self.config, "api_timeout", 90.0)
        self._api_worker = ThrottleLineChartApiWorker(
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

    def _on_api_progress(self, value: int) -> None:
        """API 進度回調。"""
        try:
            bounded = max(0, min(int(value), 100))
            self.load_progress.emit(bounded)
        except Exception:  # pragma: no cover - UI signal issues
            pass

    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        """API 成功回調 - 處理返回的數據。"""
        self._debug("========== API 成功回調 ==========")
        try:
            raw_data = payload.get("data")
            meta = payload.get("meta", {})

            # 🔧 處理雙層嵌套格式：API 返回 {success, data: {success, data: {metadata, analysis}}}
            # 如果 raw_data 是雙層嵌套格式，提取內層 data
            if isinstance(raw_data, dict) and "data" in raw_data and "success" in raw_data:
                self._debug(f"⚠️ 檢測到雙層嵌套格式，提取內層 data")
                self._debug(f"外層 keys: {list(raw_data.keys())}")
                raw_data = raw_data["data"]
                self._debug(f"內層 keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'NOT DICT'}")

            if not self._validate_data_format(raw_data):
                self._debug(f"❌ 驗證失敗！數據結構: {list(raw_data.keys()) if isinstance(raw_data, dict) else type(raw_data)}")
                raise ValueError("API 返回的數據格式驗證失敗")

            self._debug(f"API 元數據: source={meta.get('source')}, latency={meta.get('latency_ms')}ms")
            self._last_data_source = "api"
            self._last_api_meta = meta

            # 處理數據
            processed_data = self._process_data(raw_data)
            processed_data["metadata"]["api_meta"] = meta
            processed_data["metadata"]["data_source"] = "api"

            self._current_data = processed_data
            self.status_changed.emit("API 載入成功")
            self.load_progress.emit(100)
            self.data_loaded.emit(processed_data)
            self._debug("✅ API 數據載入完成")
        except Exception as exc:
            self._error(f"API 成功回調處理失敗: {exc}")
            self._on_api_error(str(exc))
        finally:
            self._is_loading = False

    def _on_api_error(self, error_message: str) -> None:
        """API 錯誤回調。"""
        self._debug(f"========== API 錯誤回調 ==========")
        self._error(f"API 請求失敗: {error_message}")
        self._is_loading = False

        # 嘗試本地 JSON 後備（如果允許）
        if self._allow_local_fallback:
            self._debug("嘗試本地 JSON 後備...")
            self.status_changed.emit("API 失敗，嘗試本地資料...")
            try:
                # 使用基類的 JSON 載入流程
                super().load_data(**self._pending_params)
            except Exception as fallback_exc:
                self._error(f"本地 JSON 後備也失敗: {fallback_exc}")
                self.load_error.emit(f"API 和本地資料載入皆失敗: {error_message}")
        else:
            self.load_error.emit(f"API 載入失敗: {error_message}")
            self.status_changed.emit("載入失敗")

    def _cleanup_api_worker(self) -> None:
        """清理 API Worker 執行緒。"""
        if self._api_worker:
            try:
                self._api_worker.progress.disconnect()
                self._api_worker.success.disconnect()
                self._api_worker.failure.disconnect()
                self._api_worker.finished.disconnect()
            except Exception:  # pragma: no cover - signal disconnection issues
                pass
            self._api_worker.deleteLater()
            self._api_worker = None

    # ------------------------------------------------------------------
    # 基底覆寫
    # ------------------------------------------------------------------
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")
        driver = params.get("driver") or params.get("driver_code")

        if not year or not race or not session or not driver:
            self._debug(
                f"缺少必要參數: year={year!r}, race={race!r}, session={session!r}, driver={driver!r}"
            )
            return False

        self._target_driver = str(driver).upper()
        self._cached_metadata.clear()
        self._cached_chart_payload.clear()
        return True

    def _build_filename_patterns(self, year: Any, race: Any, session: Any, **_: Any) -> List[str]:
        slug_race = self._slugify(race)
        session_key = str(session) if session is not None else "Unknown"
        year_str = str(year)
        patterns = [
            f"throttle_ratio_{year_str}_{slug_race}_{session_key}.json",
            f"throttle_ratio_{year_str}_{slug_race}_{session_key.lower()}.json",
            f"throttle_ratio_{year_str}_{slug_race}_{session_key.upper()}.json",
            f"throttle_ratio_{year_str}_{slug_race}_*.json",
        ]
        return patterns

    def _validate_data_format(self, raw_data: Any) -> bool:
        if not isinstance(raw_data, dict):
            self._debug("Function 54 JSON 必須是字典格式")
            return False
        if "analysis" not in raw_data:
            self._debug("缺少 'analysis' 欄位")
            return False
        analysis = raw_data.get("analysis")
        if not isinstance(analysis, dict):
            self._debug("'analysis' 必須是字典")
            return False
        drivers = analysis.get("drivers")
        if isinstance(drivers, list):
            return True
        if isinstance(drivers, dict):
            return True
        self._debug("'analysis.drivers' 必須為列表或字典")
        return False

    def _process_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        self._last_raw_data = copy.deepcopy(raw_data)

        metadata = dict(raw_data.get("metadata") or {})
        analysis = raw_data.get("analysis") or {}
        drivers_raw = analysis.get("drivers") or []

        drivers: Sequence[Dict[str, Any]]
        if isinstance(drivers_raw, dict):
            drivers = list(drivers_raw.values())
        elif isinstance(drivers_raw, list):
            drivers = [d for d in drivers_raw if isinstance(d, dict)]
        else:
            drivers = []

        if not drivers:
            raise ValueError("Function 54 JSON 不包含任何車手資料")

        available_driver_codes = sorted(
            {
                str(driver.get("driver_code") or driver.get("driver") or "").upper()
                for driver in drivers
                if isinstance(driver, dict) and (driver.get("driver_code") or driver.get("driver"))
            }
        )
        available_driver_codes = [code for code in available_driver_codes if code]

        target = self._normalize_driver_payload(drivers)
        if target is None:
            raise ValueError(f"找不到指定車手 {self._target_driver} 的 Function 54 數據")

        lap_records = self._process_lap_records(target.get("laps") or [])
        lap_records.sort(key=lambda item: item["lap_number"])

        # 🔧 FIX: 先提取標記（從原始資料），再進行過濾
        # 這樣即使啟用 filter_pit_laps，P 標記仍會顯示在 X 軸上
        helper_sets = self._extract_flag_sets(lap_records)
        stint_ranges = self._build_stint_segments(lap_records)

        # 然後才過濾資料點（用於圖表繪製）
        # ✅ 傳遞 helper_sets 給 _apply_filters，使用已提取的 flag 資訊
        lap_records, filter_stats = self._apply_filters(lap_records, target, helper_sets)

        chart_series = self._build_chart_series(lap_records)

        result = {
            "metadata": self._enrich_metadata(metadata, analysis, available_driver_codes),
            "driver": {
                "code": target.get("driver_code") or self._target_driver,
                "team": target.get("team"),
                "summary": target.get("summary") or {},
            },
            "lap_records": lap_records,
            "chart_series": chart_series,
            "annotations": {
                "pit_laps": sorted(helper_sets["pit_laps"]),
                "invalid_laps": sorted(helper_sets["invalid_laps"]),
                "caution_laps": sorted(helper_sets["caution_laps"]),
                "flag_labels": helper_sets["flag_labels"],
                "stint_ranges": stint_ranges,
            },
            "available_drivers": available_driver_codes,
            "source_payload": {
                "driver": target,
                "analysis_summary": analysis.get("summary"),
            },
            "filters_applied": filter_stats,
        }

        result["metadata"].setdefault("filters_applied", filter_stats)

        self._cached_metadata = result["metadata"]
        self._cached_chart_payload = result
        self._filter_statistics = filter_stats
        return result

    def _apply_filters(
        self,
        lap_records: Sequence[Dict[str, Any]],
        driver_payload: Dict[str, Any],
        helper_sets: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        logger.debug("[_apply_filters] Starting filtering process...")
        logger.debug(
            "[_apply_filters] Input lap_records count: %s",
            len(lap_records) if lap_records else 0,
        )
        logger.debug(
            "[_apply_filters] Filter settings: pit=%s, yellow=%s, red=%s, first_laps=%s",
            self._filter_pit_laps,
            self._filter_yellow_flags,
            self._filter_red_flags,
            self._filter_first_laps,
        )
        logger.debug("[_apply_filters] helper_sets provided: %s", helper_sets is not None)
        
        if not lap_records:
            return list(lap_records), {
                "filter_pit_laps": bool(self._filter_pit_laps),
                "filter_yellow_flags": bool(self._filter_yellow_flags),
                "filter_red_flags": bool(self._filter_red_flags),
                "filter_first_laps": bool(self._filter_first_laps),
                "removed_pit_laps": 0,
                "removed_caution_laps": 0,
                "removed_red_flag_laps": 0,
                "removed_first_laps": 0,
                "remaining_laps": 0,
                "original_laps": 0,
            }

        # 🔍 DEBUG: 追蹤過濾設定狀態
        self._debug(f"🔧 [Filter Status] filter_pit_laps={self._filter_pit_laps}, filter_yellow_flags={self._filter_yellow_flags}, filter_red_flags={self._filter_red_flags}, filter_first_laps={self._filter_first_laps}")

        filtered: List[Dict[str, Any]] = []
        removed_pit = 0
        removed_caution = 0
        removed_red_flag = 0
        removed_first_laps = 0

        # ✅ 方案 B: 使用已提取的 helper_sets 數據（推薦）
        # 如果有 helper_sets，直接從中提取 Yellow Flag 和 Red Flag 圈數
        if helper_sets is not None:
            # 從 helper_sets 提取 Yellow Flag 圈數
            caution_laps = helper_sets.get("caution_laps", set()) if self._filter_yellow_flags else set()
            
            # 從 flag_labels 提取 Red Flag 圈數（標記為 'R' 的圈數）
            flag_labels = helper_sets.get("flag_labels", {})
            red_flag_laps = {lap for lap, label in flag_labels.items() if label == 'R'} if self._filter_red_flags else set()
            
            logger.info("[_apply_filters] Using helper_sets data")
            logger.debug("[_apply_filters] Caution laps (Yellow Flag): %s", caution_laps)
            logger.debug("[_apply_filters] Red flag laps: %s", red_flag_laps)
        else:
            # 舊方法：從 driver_payload 提取（可能會失敗）
            logger.warning(
                "[_apply_filters] No helper_sets, falling back to extract_caution_laps/extract_red_flag_laps"
            )
            caution_laps = (
                extract_caution_laps(driver_payload)
                if self._filter_yellow_flags
                else set()
            )
            red_flag_laps = (
                extract_red_flag_laps(driver_payload)
                if self._filter_red_flags
                else set()
            )
            logger.debug(
                "[_apply_filters] Caution laps (Yellow Flag): %s",
                caution_laps if caution_laps else "EMPTY SET (extracted nothing!)",
            )
            logger.debug(
                "[_apply_filters] Red flag laps: %s",
                red_flag_laps if red_flag_laps else "EMPTY SET (extracted nothing!)",
            )
        smart_summary = driver_payload.get("smart_markers_summary") or {}

        for record in lap_records:
            lap_number = record.get("lap_number")

            # 過濾前兩圈 (Lap 1 & 2)
            if self._filter_first_laps and lap_number in (1, 2):
                removed_first_laps += 1
                logger.debug("[_apply_filters] Removed First Lap: %s", lap_number)
                continue

            if self._filter_yellow_flags and lap_is_under_caution(lap_number, record, caution_laps):
                removed_caution += 1
                logger.debug("[_apply_filters] Removed Yellow Flag lap: %s", lap_number)
                continue

            if self._filter_red_flags and lap_is_under_red_flag(lap_number, record, red_flag_laps):
                removed_red_flag += 1
                logger.debug("[_apply_filters] Removed Red Flag lap: %s", lap_number)
                continue

            if self._filter_pit_laps and lap_is_pit_stop(record, smart_summary):
                removed_pit += 1
                logger.debug("[_apply_filters] Removed Pit Stop lap: %s", lap_number)
                continue

            filtered.append(record)

        stats = {
            "filter_pit_laps": bool(self._filter_pit_laps),
            "filter_yellow_flags": bool(self._filter_yellow_flags),
            "filter_red_flags": bool(self._filter_red_flags),
            "filter_first_laps": bool(self._filter_first_laps),
            "removed_pit_laps": removed_pit,
            "removed_caution_laps": removed_caution,
            "removed_red_flag_laps": removed_red_flag,
            "removed_first_laps": removed_first_laps,
            "remaining_laps": len(filtered),
            "original_laps": len(lap_records),
        }
        self._debug(f"🔍 [Filter Stats] {stats}")
        logger.info("[_apply_filters] Filtering completed")
        logger.debug(
            "[_apply_filters] Original laps: %s; Removed Pit: %s, Yellow: %s, Red: %s; Remaining: %s",
            len(lap_records),
            removed_pit,
            removed_caution,
            removed_red_flag,
            len(filtered),
        )
        return filtered, stats

    # ------------------------------------------------------------------
    # Lap 處理
    # ------------------------------------------------------------------
    def _process_lap_records(self, laps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed: List[Dict[str, Any]] = []
        seen_lap_numbers: set = set()
        lap_sequence = 0
        for lap in laps or []:
            if not isinstance(lap, dict):
                continue

            original_lap_number = self._safe_int(lap.get("lap_number"))
            lap_sequence += 1

            if original_lap_number is None or original_lap_number <= 0 or original_lap_number in seen_lap_numbers:
                lap_number = lap_sequence
            else:
                lap_number = original_lap_number
                lap_sequence = max(lap_sequence, lap_number)

            seen_lap_numbers.add(lap_number)

            record = dict(lap)
            record["lap_number"] = lap_number
            if original_lap_number != lap_number:
                record.setdefault("raw_lap_number", original_lap_number)
            record["full_throttle_duration_s"] = self._safe_float(lap.get("full_throttle_duration_s"))
            record["lap_time_seconds"] = self._safe_float(lap.get("lap_time_seconds"))
            record["full_throttle_ratio"] = self._safe_float(lap.get("full_throttle_ratio"))
            record["average_throttle"] = self._safe_float(lap.get("average_throttle"))
            record["coasting_duration_s"] = self._safe_float(lap.get("coasting_duration_s"))
            record["drs_usage_ratio"] = self._safe_float(lap.get("drs_usage_ratio"))
            record["ers_deploy_ratio"] = self._safe_float(lap.get("ers_deploy_ratio"))
            record["speed_avg_kmh"] = self._safe_float(lap.get("speed_avg_kmh"))
            record["top_speed_kmh"] = self._safe_float(lap.get("top_speed_kmh"))
            record["tyre_life"] = self._safe_int(lap.get("tyre_life"))
            record["stint"] = self._safe_int(lap.get("stint"))
            record["sector1_time"] = self._safe_float(lap.get("sector1_time"))
            record["sector2_time"] = self._safe_float(lap.get("sector2_time"))
            record["sector3_time"] = self._safe_float(lap.get("sector3_time"))

            data_status = str(lap.get("data_status", "ok"))
            record["data_status"] = data_status
            record["is_valid"] = data_status.lower() in {"ok", "valid"}

            record["drs_usage_percent"] = (
                None if record["drs_usage_ratio"] is None else round(record["drs_usage_ratio"] * 100.0, 2)
            )
            record["ers_deploy_percent"] = (
                None if record["ers_deploy_ratio"] is None else round(record["ers_deploy_ratio"] * 100.0, 2)
            )

            lap_time_fmt = record.get("lap_time_formatted")
            if not lap_time_fmt and record["lap_time_seconds"] is not None:
                record["lap_time_formatted"] = self._format_seconds(record["lap_time_seconds"])

            processed.append(record)

        best_lap = self._best_valid_lap(processed)
        for record in processed:
            lap_time = record.get("lap_time_seconds")
            if best_lap is None or lap_time is None:
                record["lap_time_delta"] = None
            else:
                record["lap_time_delta"] = round(lap_time - best_lap, 3)
        return processed

    def _best_valid_lap(self, laps: Sequence[Dict[str, Any]]) -> Optional[float]:
        valid_times = [
            lap.get("lap_time_seconds")
            for lap in laps
            if lap.get("is_valid") and lap.get("lap_time_seconds") is not None
        ]
        if not valid_times:
            return None
        return min(valid_times)

    # ------------------------------------------------------------------
    # Chart Series
    # ------------------------------------------------------------------
    def _build_chart_series(self, laps: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        lap_numbers: List[int] = []
        throttle_values: List[Optional[float]] = []
        lap_times: List[Optional[float]] = []
        ratios: List[Optional[float]] = []
        avg_throttle: List[Optional[float]] = []
        tooltip_map: Dict[int, Dict[str, Any]] = {}

        for lap in laps:
            lap_no = lap.get("lap_number")
            lap_numbers.append(lap_no)
            throttle_values.append(lap.get("full_throttle_duration_s"))
            lap_times.append(lap.get("lap_time_seconds"))
            ratios.append(None if lap.get("full_throttle_ratio") is None else round(lap["full_throttle_ratio"] * 100.0, 2))
            avg_throttle.append(
                None if lap.get("average_throttle") is None else round(lap.get("average_throttle") * 100.0, 2)
            )

            tooltip_map[lap_no] = {
                "lap_number": lap_no,
                "lap_time_formatted": lap.get("lap_time_formatted") or "N/A",
                "lap_time_seconds": lap.get("lap_time_seconds"),
                "full_throttle_duration_s": lap.get("full_throttle_duration_s"),
                "full_throttle_ratio_percent": ratios[-1],
                "average_throttle_percent": avg_throttle[-1],
                "compound": lap.get("compound") or "N/A",
                "stint": lap.get("stint"),
                "tyre_life": lap.get("tyre_life"),
                "drs_percent": lap.get("drs_usage_percent"),
                "ers_percent": lap.get("ers_deploy_percent"),
                "pit_status": lap.get("pit_status"),
                "track_status": lap.get("track_status"),
                "lap_time_delta": lap.get("lap_time_delta"),
                "speed_avg_kmh": lap.get("speed_avg_kmh"),
                "top_speed_kmh": lap.get("top_speed_kmh"),
                "data_status": lap.get("data_status"),
                "notes": lap.get("notes"),
            }

        return {
            "lap_numbers": lap_numbers,
            "full_throttle_duration_s": throttle_values,
            "lap_time_seconds": lap_times,
            "full_throttle_ratio_percent": ratios,
            "average_throttle_percent": avg_throttle,
            "tooltip": tooltip_map,
        }

    # ------------------------------------------------------------------
    # 標註資料
    # ------------------------------------------------------------------
    def _extract_flag_sets(self, laps: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        pit_laps: set = set()
        invalid_laps: set = set()
        caution_laps: set = set()
        flag_labels: Dict[int, str] = {}

        # 🔧 追蹤 stint 變化以檢測進站
        previous_stint: Optional[int] = None

        for lap in laps:
            lap_no = lap.get("lap_number")
            if not lap_no:
                continue

            try:
                lap_int = int(lap_no)
            except (TypeError, ValueError):
                continue

            # 🔧 FIX: 多重進站檢測邏輯
            is_pit_lap = False
            
            # 方法 1: 檢查 pit_status 欄位
            if lap.get("pit_status") and str(lap.get("pit_status")).strip().lower() not in {"", "none", "normal"}:
                is_pit_lap = True
            
            # 方法 2: 檢查 pit_out_time（出站圈）
            if lap.get("pit_out_time") is not None:
                is_pit_lap = True
            
            # 方法 3: 檢查 stint 變化 + tyre_life=1（換胎圈）
            current_stint = lap.get("stint")
            tyre_life = lap.get("tyre_life")
            if current_stint is not None and previous_stint is not None:
                if current_stint != previous_stint and tyre_life == 1:
                    is_pit_lap = True
            if current_stint is not None:
                previous_stint = current_stint
            
            if is_pit_lap:
                pit_laps.add(lap_int)

            if not lap.get("is_valid", False):
                invalid_laps.add(lap_int)

            track_status = str(lap.get("track_status") or "")
            label = self._track_status_to_flag_label(track_status)
            if label:
                flag_labels[lap_int] = label
            if track_status and any(ch for ch in track_status if ch not in {"1", " "}):
                caution_laps.add(lap_int)

        for lap_int in pit_laps:
            flag_labels.setdefault(int(lap_int), "P")

        # 🔍 DEBUG: 追蹤標記生成狀態
        self._debug(f"🏁 [Flag Markers] pit_laps={sorted(pit_laps)}, flag_labels={flag_labels}")

        return {
            "pit_laps": pit_laps,
            "invalid_laps": invalid_laps,
            "caution_laps": caution_laps,
            "flag_labels": flag_labels,
        }

    @staticmethod
    def _track_status_to_flag_label(track_status: str) -> Optional[str]:
        if not track_status:
            return None

        digits = {ch for ch in track_status if ch.isdigit() and ch != "1"}
        if not digits:
            return None

        # 優先順序：紅旗 > 安全車/VSC > 黃旗
        if any(code in digits for code in {"3", "6"}):
            return "R"
        if any(code in digits for code in {"5", "4"}):
            return "S"
        if "2" in digits:
            return "Y"
        return None

    def _build_stint_segments(self, laps: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        segments: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None

        for lap in laps:
            stint = lap.get("stint")
            lap_no = lap.get("lap_number")
            compound = lap.get("compound")
            if stint is None or lap_no is None:
                continue

            if current and current["stint"] == stint:
                current["end_lap"] = lap_no
            else:
                if current:
                    segments.append(current)
                current = {
                    "stint": stint,
                    "compound": compound,
                    "start_lap": lap_no,
                    "end_lap": lap_no,
                }

        if current:
            segments.append(current)
        return segments

    # ------------------------------------------------------------------
    # 輔助工具
    # ------------------------------------------------------------------
    def _normalize_driver_payload(self, drivers: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        target_code = (self._target_driver or "").upper()
        for driver in drivers:
            code = str(driver.get("driver_code") or driver.get("driver") or "").upper()
            if code == target_code:
                return driver
        return None

    def _enrich_metadata(
        self,
        metadata: Dict[str, Any],
        analysis: Dict[str, Any],
        available_driver_codes: Sequence[str],
    ) -> Dict[str, Any]:
        metadata = dict(metadata or {})
        metadata.setdefault("function_id", 54)
        metadata.setdefault("analysis_name", "Lap Throttle Ratio Per Driver")
        metadata.setdefault("driver_code", self._target_driver)
        metadata.setdefault("available_drivers", available_driver_codes)
        if not metadata.get("available_drivers"):
            metadata["available_drivers"] = available_driver_codes
        thresholds = metadata.get("thresholds") or analysis.get("thresholds")
        if thresholds:
            metadata["thresholds"] = thresholds
        return metadata

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            result = int(value)
        except (TypeError, ValueError):
            return None
        return result

    @staticmethod
    def _format_seconds(seconds: float) -> str:
        if seconds is None or seconds < 0:
            return "N/A"
        minutes, remainder = divmod(seconds, 60.0)
        return f"{int(minutes):02d}:{remainder:06.3f}"

    @staticmethod
    def _slugify(value: Any) -> str:
        text = str(value or "unknown")
        text = text.strip()
        if not text:
            return "unknown"
        text = text.replace(" ", "_")
        text = text.replace("/", "-")
        while "__" in text:
            text = text.replace("__", "_")
        return text.lower()

    # ------------------------------------------------------------------
    # 公開工具
    # ------------------------------------------------------------------
    def get_current_metadata(self) -> Dict[str, Any]:
        return dict(self._cached_metadata)

    def get_chart_payload(self) -> Dict[str, Any]:
        return dict(self._cached_chart_payload)

    # ------------------------------------------------------------------
    # 過濾器整合
    # ------------------------------------------------------------------
    def update_filter_settings(
        self,
        *,
        filter_pit_laps: Optional[bool] = None,
        filter_yellow_flags: Optional[bool] = None,
        filter_red_flags: Optional[bool] = None,
        filter_first_laps: Optional[bool] = None,
        reprocess: bool = True,
    ) -> bool:
        logger.debug(
            "[update_filter_settings] Called with: pit=%s, yellow=%s, red=%s, first_laps=%s, reprocess=%s",
            filter_pit_laps,
            filter_yellow_flags,
            filter_red_flags,
            filter_first_laps,
            reprocess,
        )
        logger.debug(
            "[update_filter_settings] Current values BEFORE: pit=%s, yellow=%s, red=%s, first_laps=%s",
            self._filter_pit_laps,
            self._filter_yellow_flags,
            self._filter_red_flags,
            self._filter_first_laps,
        )
        
        changed = False

        if filter_pit_laps is not None:
            new_value = bool(filter_pit_laps)
            if new_value != self._filter_pit_laps:
                self._debug(f"⚙️ [Settings] filter_pit_laps changed: {self._filter_pit_laps} → {new_value}")
                logger.info(
                    "[update_filter_settings] filter_pit_laps changed: %s → %s",
                    self._filter_pit_laps,
                    new_value,
                )
                self._filter_pit_laps = new_value
                changed = True
            else:
                logger.debug(
                    "[update_filter_settings] filter_pit_laps unchanged: %s", self._filter_pit_laps
                )

        if filter_yellow_flags is not None:
            new_value = bool(filter_yellow_flags)
            if new_value != self._filter_yellow_flags:
                self._debug(f"⚙️ [Settings] filter_yellow_flags changed: {self._filter_yellow_flags} → {new_value}")
                logger.info(
                    "[update_filter_settings] filter_yellow_flags changed: %s → %s",
                    self._filter_yellow_flags,
                    new_value,
                )
                self._filter_yellow_flags = new_value
                changed = True
            else:
                logger.debug(
                    "[update_filter_settings] filter_yellow_flags unchanged: %s", self._filter_yellow_flags
                )

        if filter_red_flags is not None:
            new_value = bool(filter_red_flags)
            if new_value != self._filter_red_flags:
                self._debug(f"⚙️ [Settings] filter_red_flags changed: {self._filter_red_flags} → {new_value}")
                logger.info(
                    "[update_filter_settings] filter_red_flags changed: %s → %s",
                    self._filter_red_flags,
                    new_value,
                )
                self._filter_red_flags = new_value
                changed = True
            else:
                logger.debug(
                    "[update_filter_settings] filter_red_flags unchanged: %s", self._filter_red_flags
                )

        if filter_first_laps is not None:
            new_value = bool(filter_first_laps)
            if new_value != self._filter_first_laps:
                self._debug(f"⚙️ [Settings] filter_first_laps changed: {self._filter_first_laps} → {new_value}")
                logger.info(
                    "[update_filter_settings] filter_first_laps changed: %s → %s",
                    self._filter_first_laps,
                    new_value,
                )
                self._filter_first_laps = new_value
                changed = True
            else:
                logger.debug(
                    "[update_filter_settings] filter_first_laps unchanged: %s", self._filter_first_laps
                )

        if not changed:
            self._debug(f"⚙️ [Settings] No changes detected (pit={self._filter_pit_laps}, yellow={self._filter_yellow_flags}, red={self._filter_red_flags}, first_laps={self._filter_first_laps})")
            logger.info(
                "[update_filter_settings] No changes detected, reprocess=%s", reprocess
            )
            logger.debug(
                "[update_filter_settings] Final values: pit=%s, yellow=%s, red=%s, first_laps=%s",
                self._filter_pit_laps,
                self._filter_yellow_flags,
                self._filter_red_flags,
                self._filter_first_laps,
            )
            return False

        logger.info(
            "[update_filter_settings] Settings changed! New values: pit=%s, yellow=%s, red=%s, first_laps=%s",
            self._filter_pit_laps,
            self._filter_yellow_flags,
            self._filter_red_flags,
            self._filter_first_laps,
        )
        
        if reprocess and self._last_raw_data is not None:
            try:
                self._debug(f"🔄 [Reprocess] Rebuilding data with new filter settings...")
                logger.info("[update_filter_settings] Reprocessing data with new filters...")
                rebuilt = self._process_data(copy.deepcopy(self._last_raw_data))
                logger.info("[update_filter_settings] Reprocessing completed successfully")
            except Exception as exc:  # pragma: no cover - defensive
                self._debug(f"重新套用過濾器失敗: {exc}")
                logger.exception("[update_filter_settings] Reprocessing failed", exc_info=exc)
                return False
            self._current_data = rebuilt
            self.data_loaded.emit(rebuilt)
        elif reprocess:
            logger.warning("[update_filter_settings] Reprocess requested but no _last_raw_data available")
        else:
            logger.info("[update_filter_settings] Reprocess=False, skipping data rebuild")

        return True

    def _on_global_filter_settings_changed(self, settings: Dict[str, Any]) -> None:
        if not isinstance(settings, dict):
            return
        self.update_filter_settings(
            filter_pit_laps=settings.get("filter_pit_laps"),
            filter_yellow_flags=settings.get("filter_yellow_flags"),
            filter_red_flags=settings.get("filter_red_flags"),
            filter_first_laps=settings.get("filter_first_laps"),
            reprocess=True,
        )


__all__ = ["ThrottleLineChartDataLoader"]
