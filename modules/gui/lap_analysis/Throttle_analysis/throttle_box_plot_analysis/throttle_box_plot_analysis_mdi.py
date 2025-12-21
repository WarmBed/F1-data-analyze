#!/usr/bin/env python3
"""
ThrottleBoxPlotAnalysis - F1T 全油門百分比箱型圖分析模組
=======================================================

基於通用 MDI 架構實現，提供：
- 每位車手全油門百分比的箱型圖可視化（使用 full_throttle_ratio）
- IQR 方法異常值過濾
- 進站圈/黃旗圈過濾
- 圖表匯出與統計摘要

資料來源：CLI Function 54 (Lap Throttle Ratio Per Driver)
作者: F1T Team
日期: 2025-10-08 (百分比模式更新)
版本: 1.1.0
"""

from __future__ import annotations

import os
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Set

import numpy as np
import requests
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSignalBlocker
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QGroupBox,
    QFileDialog,
    QMessageBox,
)

from core.gui_i18n import tr
from core.gui_settings_manager import gui_settings_manager
from core.logger import get_logger
from core.api_base_url import resolve_api_base_url

# 導入圈速過濾工具
from modules.gui.driver_race.detailed_lap_analysis.lap_filter_utils import (
    extract_caution_laps,
    extract_red_flag_laps,
    lap_is_under_caution,
    lap_is_under_red_flag,
    lap_is_pit_stop,
    normalize_lap_number,
)

try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
except ImportError:  # pragma: no cover
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig

from .throttle_box_plot_chart_widget import ThrottleBoxPlotChartWidget

logger = get_logger(__name__)


class ThrottleBoxPlotApiWorker(QThread):
    """背景工作執行緒，呼叫 REST API 取得油門分析資料。"""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 90.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip("/")
        self.params = dict(params)
        self.timeout = timeout

    def run(self) -> None:  # pragma: no cover - thread run
        try:
            # 檢查是否已被請求中斷
            if self.isInterruptionRequested():
                logger.debug("[THROTTLE_BOXPLOT_API_WORKER] 啟動前已被請求中斷，跳過執行")
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
                logger.debug("[THROTTLE_BOXPLOT_API_WORKER] 發送請求前被請求中斷")
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
                logger.debug("[THROTTLE_BOXPLOT_API_WORKER] API 回應後被請求中斷，放棄處理結果")
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

            # 發送信號前最後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[THROTTLE_BOXPLOT_API_WORKER] 發送成功信號前被請求中斷，放棄發送")
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


class ThrottleBoxPlotDataManager(UniversalDataLoader):
    """油門箱型圖資料管理器"""

    filter_settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        if "throttle_boxplot" not in UniversalDataLoader.ANALYSIS_TYPES:
            throttle_config = AnalysisConfig(
                display_name=tr("throttle_box_plot", "油門箱型圖"),
                debug_prefix="[THROTTLE_DATA]",
                data_source="api",
                cli_function="54",
                api_endpoint="/api/v2/analysis/execute",
                api_function_id=54,
                api_timeout=90.0,
                file_patterns=[
                    "throttle_ratio_{year}_{race}_{session}.json",
                    "throttle_ratio_{year}_{race}_{session}_*.json",
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                cache_enabled=True,
            )
            UniversalDataLoader.register_analysis_type("throttle_boxplot", throttle_config)

        super().__init__("throttle_boxplot", parent)

        self.driver_throttle_durations: Dict[str, List[float]] = {}
        self.statistics: Dict[str, Dict[str, float]] = {}
        self.filter_settings: Dict[str, Any] = {
            "filter_pit_laps": True,
            "filter_outliers": True,
            "outlier_threshold": 1.5,
            "filter_yellow_flags": True,
            "filter_red_flags": True,
            "filter_first_laps": True,
        }
        self.settings_manager = gui_settings_manager
        self._raw_data_cache: Optional[Dict[str, Any]] = None
        self._suppress_global_sync = False
        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[ThrottleBoxPlotApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        self._allow_local_fallback, self._fallback_policy_reason = self._resolve_local_fallback_policy()
        self._debug(
            f"本地 JSON 後備已{'啟用' if self._allow_local_fallback else '停用'} (策略: {self._fallback_policy_reason})"
        )

        try:
            self._apply_global_settings(self.settings_manager.get_boxplot_settings())
            self.settings_manager.boxplot_settings_changed.connect(self._on_global_boxplot_settings_changed)
        except Exception as exc:  # pragma: no cover - signal wiring failure
            self._debug(f"無法連結全域設定管理器: {exc}")

    # ------------------------------------------------------------------
    # 共用輔助
    # ------------------------------------------------------------------
    def _debug(self, message: str):
        logger.info("[THROTTLE_DATA] %s", message)

    def _determine_api_base_url(self) -> str:
        return resolve_api_base_url(event_logger=self._debug)

    def _resolve_local_fallback_policy(self) -> Tuple[bool, str]:
        env_value = os.getenv("F1T_ALLOW_THROTTLE_JSON_FALLBACK")
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True, f"環境變數 F1T_ALLOW_THROTTLE_JSON_FALLBACK={env_value}"
            return False, f"環境變數 F1T_ALLOW_THROTTLE_JSON_FALLBACK={env_value}"
        return True, "預設策略 (允許本地 JSON 後備)"

    def set_local_fallback_allowed(self, allowed: bool, reason: Optional[str] = None) -> None:
        self._allow_local_fallback = bool(allowed)
        self._fallback_policy_reason = reason or "手動覆寫"
        state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(f"本地 JSON 後備手動設為{state} (原因: {self._fallback_policy_reason})")

    # ------------------------------------------------------------------
    # 資料載入
    # ------------------------------------------------------------------
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")
        if not year or not race or not session:
            self._debug("參數不完整：需要年份、比賽和賽段")
            return False
        return True

    def load_data(self, **kwargs) -> bool:
        if self.config.data_source != "api":
            return super().load_data(**kwargs)

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
            self.status_changed.emit("API 載入失敗，改用本地資料")
            return super().load_data(**kwargs)

    def load_data_from_local(self, **kwargs) -> bool:
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
        """啟動 API 請求背景執行緒（完全複製 throttle_line_chart 的成功模式）"""
        self._cleanup_api_worker()

        worker_params = {
            "year": params.get("year"),
            "race": params.get("race"),
            "session": params.get("session"),
            "force_refresh": params.get("force_refresh", False),
        }

        timeout = getattr(self.config, "api_timeout", 90.0)
        self._api_worker = ThrottleBoxPlotApiWorker(
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
        try:
            bounded = max(0, min(int(value), 100))
            self.load_progress.emit(bounded)
        except Exception:  # pragma: no cover - UI signal issues
            pass

    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        self._debug("========== API 成功回調 ==========")
        try:
            raw_data = payload.get("data")
            meta = payload.get("meta", {})
            self._last_api_meta = meta or {}
            self._last_data_source = "api"

            # 🔧 處理雙層嵌套格式：API 返回 {success, data: {success, data: {metadata, analysis}}}
            # 如果 raw_data 是雙層嵌套格式，提取內層 data
            if isinstance(raw_data, dict) and "data" in raw_data and "success" in raw_data:
                self._debug(f"⚠️ 檢測到雙層嵌套格式，提取內層 data")
                self._debug(f"外層 keys: {list(raw_data.keys())}")
                raw_data = raw_data["data"]
                self._debug(f"內層 keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'NOT DICT'}")

            if not self._validate_data_format(raw_data):
                self._debug(f"❌ 驗證失敗！數據結構: {list(raw_data.keys()) if isinstance(raw_data, dict) else type(raw_data)}")
                raise ValueError("API 回傳數據格式不符合預期")

            processed_data = self._process_data(raw_data)
            metadata = processed_data.setdefault("metadata", {})
            metadata.setdefault("data_source", "api")
            if self._last_api_meta:
                metadata.setdefault("api", {}).update(self._last_api_meta)

            self._current_data = processed_data
            self._is_loading = False
            self.load_progress.emit(100)
            self.status_changed.emit("已從 API 載入資料")
            self._debug("✅ 數據處理完成，準備發送 data_loaded 信號")
            self.data_loaded.emit(processed_data)
            self._debug("========== API 成功回調結束 ==========")
        except Exception as exc:
            self._debug(f"❌ 處理 API 數據時發生異常: {exc}")
            import traceback

            traceback.print_exc()
            self._error(f"處理 API 數據失敗: {exc}")
            self._is_loading = False
            self.status_changed.emit("API 資料格式錯誤，改用本地資料")
            self._fallback_to_local(str(exc))

    def _on_api_error(self, message: str) -> None:
        self._debug("========== API 錯誤回調 ==========")
        self._debug(f"錯誤訊息: {message}")
        self._error(f"API 請求失敗: {message}")
        self._is_loading = False
        self.status_changed.emit("API 請求失敗，改用本地資料")
        self._fallback_to_local(message)

    def _fallback_to_local(self, reason: str) -> None:
        self._debug("========== 本地 JSON 回退流程 ==========")
        params = self._pending_params or {}
        if not params:
            self._debug("❌ 缺少待處理參數")
            self.load_error.emit(f"API 載入失敗: {reason}")
            return

        self._debug(f"待處理參數: {params}")
        self._debug(f"允許本地回退: {self._allow_local_fallback}")
        self._debug(f"回退策略原因: {self._fallback_policy_reason}")

        if not self._allow_local_fallback:
            self._last_data_source = "local-fallback-disabled"
            self.load_error.emit(f"API 載入失敗且禁止本地回退: {reason}")
            return

        self._debug("開始透過父類進行本地 JSON 載入...")
        result = super().load_data(**params)
        if not result:
            self._debug("❌ 父類 load_data() 返回 False")
            self.load_error.emit(f"本地 JSON 載入失敗: {reason}")
        else:
            self._debug("✅ 父類 load_data() 返回 True")
        self._debug("========== 本地 JSON 回退流程結束 ==========")

    def _cleanup_api_worker(self) -> None:
        """
        清理 API Worker 執行緒
        
        ✅ 完全複製 throttle_line_chart 和 accident 的成功模式
        """
        if self._api_worker:
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

    def stop_loading(self) -> None:
        """停止任何進行中的 API 載入流程。"""
        self._cleanup_api_worker()  # ✅ 直接調用 cleanup，移除多餘的 _stop_api_worker
        self._is_loading = False
        try:
            self.status_changed.emit(tr("throttle_box_plot.loading_cancelled", "已取消載入請求"))
        except Exception:
            pass

    def cleanup(self) -> None:
        self._debug("cleanup: releasing throttle API worker")
        self.stop_loading()
        self._raw_data_cache = None
        self._current_data = None

    def get_last_data_source(self) -> str:
        return getattr(self, "_last_data_source", "unknown")

    def get_last_api_metadata(self) -> Dict[str, Any]:
        return getattr(self, "_last_api_meta", {})

    def _build_filename_patterns(self, year: str, race: str, session: str, **kwargs) -> List[str]:
        patterns = []
        for pattern in self.config.file_patterns:
            patterns.append(pattern.format(year=year, race=race, session=session))
        return patterns

    def _validate_data_format(self, data: Any) -> bool:
        if not isinstance(data, dict):
            self._debug("數據格式錯誤：必須是字典格式")
            return False
        if "analysis" not in data:
            self._debug("數據格式錯誤：缺少 analysis 欄位")
            return False
        analysis = data["analysis"]
        if not isinstance(analysis, dict) or "drivers" not in analysis:
            self._debug("數據格式錯誤：analysis 中缺少 drivers")
            return False
        return True

    def _process_data(self, data: Any) -> Dict[str, Any]:
        return self.process_loaded_data(data)

    def _generate_data_via_cli(self, **kwargs) -> bool:
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取油門分析數據")
        return False

    # ------------------------------------------------------------------
    # 數據處理
    # ------------------------------------------------------------------
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not isinstance(data, dict):
                raise ValueError("數據格式不正確：必須是字典格式")

            self._raw_data_cache = data
            metadata = data.get("metadata", {}).copy()
            analysis = data.get("analysis", {})
            drivers = analysis.get("drivers", [])
            if isinstance(drivers, dict):
                drivers = list(drivers.values())
            if not isinstance(drivers, list):
                raise ValueError("分析資料中 drivers 應為列表")

            driver_throttle = self._extract_throttle_durations(drivers)

            if self.filter_settings.get("filter_outliers", True):
                driver_throttle = self._filter_outliers_iqr(
                    driver_throttle, self.filter_settings.get("outlier_threshold", 1.5)
                )

            statistics = self._calculate_statistics(driver_throttle)

            self.driver_throttle_durations = driver_throttle
            self.statistics = statistics

            processed = {
                "driver_throttle_durations": driver_throttle,
                "statistics": statistics,
                "metadata": metadata,
            }

            metadata.setdefault("data_source", self._last_data_source)
            if self._last_data_source == "api" and self._last_api_meta:
                metadata.setdefault("api", {}).update(self._last_api_meta)

            thresholds = metadata.get("thresholds") or analysis.get("thresholds")
            if thresholds:
                processed.setdefault("metadata", {})["thresholds"] = thresholds

            self._debug(f"成功處理 {len(driver_throttle)} 位車手的油門數據")
            return processed
        except Exception as exc:
            self._debug(f"數據處理失敗: {exc}")
            raise

    def _extract_throttle_durations(self, drivers: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        result: Dict[str, List[float]] = {}

        for driver_data in drivers:
            if not isinstance(driver_data, dict):
                continue
            driver_code = driver_data.get("driver_code") or driver_data.get("driver") or driver_data.get("code")
            if not driver_code:
                continue

            laps = driver_data.get("laps", [])
            if not isinstance(laps, list):
                continue

            caution_laps: Optional[Set[int]] = None
            if self.filter_settings.get("filter_yellow_flags", True):
                # 盡可能重用現有黃旗推測工具
                try:
                    caution_laps = extract_caution_laps(driver_data)
                except Exception:
                    caution_laps = None

            red_flag_laps: Optional[Set[int]] = None
            if self.filter_settings.get("filter_red_flags", True):
                try:
                    red_flag_laps = extract_red_flag_laps(driver_data)
                except Exception:
                    red_flag_laps = None

            durations: List[float] = []
            for lap in laps:
                if not isinstance(lap, dict):
                    continue

                data_status = lap.get("data_status")
                if data_status and str(data_status).lower() not in {"ok", "valid"}:
                    continue

                # 🔄 改用 full_throttle_ratio (百分比模式)
                throttle_ratio = lap.get("full_throttle_ratio")
                if throttle_ratio is None:
                    continue
                try:
                    # 轉換為百分比 (0-1 → 0-100%)
                    percentage = float(throttle_ratio) * 100.0
                except (TypeError, ValueError):
                    continue
                if percentage < 0 or percentage > 100:
                    continue

                lap_number = lap.get("lap_number")

                # 過濾前兩圈 (Lap 1 & 2)
                if self.filter_settings.get("filter_first_laps", True) and lap_number in (1, 2):
                    continue

                if self.filter_settings.get("filter_yellow_flags", True):
                    track_status = str(lap.get("track_status") or "").strip()
                    if track_status and any(ch not in {"1"} for ch in track_status if ch.isdigit()):
                        continue
                    if lap_is_under_caution(lap_number, lap, caution_laps):
                        continue

                if self.filter_settings.get("filter_red_flags", True):
                    if lap_is_under_red_flag(lap_number, lap, red_flag_laps):
                        continue

                if self.filter_settings.get("filter_pit_laps", True):
                    if lap_is_pit_stop(lap, driver_data.get("smart_markers_summary")):
                        continue
                    pit_status = lap.get("pit_status")
                    if pit_status and str(pit_status).strip().lower() not in {"", "none", "normal", "ok"}:
                        continue

                durations.append(percentage)

            if durations:
                result[driver_code] = durations

        return result

    def _filter_outliers_iqr(self, data: Dict[str, List[float]], threshold: float = 1.5) -> Dict[str, List[float]]:
        filtered: Dict[str, List[float]] = {}
        for driver, values in data.items():
            if len(values) < 4:
                filtered[driver] = values
                continue
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            filtered_values = [v for v in values if lower <= v <= upper]
            if filtered_values:
                filtered[driver] = filtered_values
        return filtered

    def _calculate_statistics(self, data: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        stats: Dict[str, Dict[str, float]] = {}
        for driver, values in data.items():
            if not values:
                continue
            stats[driver] = {
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "q1": float(np.percentile(values, 25)),
                "q3": float(np.percentile(values, 75)),
                "iqr": float(np.percentile(values, 75) - np.percentile(values, 25)),
                "count": len(values),
            }
        return stats

    def update_filter_settings(self, settings: Dict[str, Any]):
        if not isinstance(settings, dict):
            return

        updates: Dict[str, Any] = {}
        for key, value in settings.items():
            if key not in self.filter_settings:
                continue
            if self.filter_settings[key] != value:
                self.filter_settings[key] = value
                updates[key] = value

        if not updates:
            return

        self._debug(f"過濾設定已更新: {updates}")

        if self._raw_data_cache:
            processed = self.process_loaded_data(self._raw_data_cache)
            self._current_data = processed
            self.data_loaded.emit(processed)
        else:
            self._debug("尚未快取原始數據，跳過重新處理")

        self.filter_settings_changed.emit(dict(self.filter_settings))

    def get_processed_data(self) -> Optional[Dict[str, Any]]:
        if not self.driver_throttle_durations:
            return None
        return {
            "driver_throttle_durations": self.driver_throttle_durations,
            "statistics": self.statistics,
            "metadata": {},
        }

    # ------------------------------------------------------------------
    # 全域設定
    # ------------------------------------------------------------------
    def _apply_global_settings(self, settings: Dict[str, Any]) -> None:
        if not isinstance(settings, dict):
            return

        updates: Dict[str, Any] = {}
        for key in ("filter_pit_laps", "filter_outliers", "outlier_threshold", "filter_yellow_flags", "filter_red_flags", "filter_first_laps"):
            if key in settings and self.filter_settings.get(key) != settings[key]:
                updates[key] = settings[key]

        if updates:
            self._debug(f"套用全域設定: {updates}")
            self._suppress_global_sync = True
            try:
                self.update_filter_settings(updates)
            finally:
                self._suppress_global_sync = False

    def _on_global_boxplot_settings_changed(self, settings: Dict[str, Any]) -> None:
        if self._suppress_global_sync:
            return
        self._apply_global_settings(settings)


from .throttle_box_plot_chart_widget import ThrottleBoxPlotChartWidget


class ThrottleBoxPlotControlWidget(QWidget):
    """油門箱型圖控制面板"""

    settings_changed = pyqtSignal(dict)
    reload_requested = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        filter_group = QGroupBox(tr("filter_settings", "🔧 過濾設定"))
        filter_layout = QVBoxLayout()

        self.filter_pit_checkbox = QCheckBox(tr("filter_pit_laps", "過濾進站圈"))
        self.filter_pit_checkbox.setChecked(True)
        self.filter_pit_checkbox.setToolTip("排除與維修站相關的圈次")
        self.filter_pit_checkbox.stateChanged.connect(self._on_settings_changed)
        filter_layout.addWidget(self.filter_pit_checkbox)

        self.filter_outliers_checkbox = QCheckBox(tr("filter_outliers", "過濾異常值 (IQR 方法)"))
        self.filter_outliers_checkbox.setChecked(True)
        self.filter_outliers_checkbox.setToolTip("使用四分位距離 (IQR) 過濾異常油門時間")
        self.filter_outliers_checkbox.stateChanged.connect(self._on_settings_changed)
        filter_layout.addWidget(self.filter_outliers_checkbox)

        self.filter_caution_checkbox = QCheckBox(tr("filter_caution_laps", "過濾黃旗/安全車圈"))
        self.filter_caution_checkbox.setChecked(True)
        self.filter_caution_checkbox.setToolTip("排除黃旗、VSC、SC 狀態下的圈次")
        self.filter_caution_checkbox.stateChanged.connect(self._on_settings_changed)
        filter_layout.addWidget(self.filter_caution_checkbox)

        iqr_layout = QHBoxLayout()
        iqr_label = QLabel(tr("iqr_multiplier", "IQR 倍數:"))
        iqr_label.setToolTip("異常值判定倍數（建議 1.5-3.0）")
        self.iqr_spinbox = QDoubleSpinBox()
        self.iqr_spinbox.setRange(0.5, 5.0)
        self.iqr_spinbox.setSingleStep(0.5)
        self.iqr_spinbox.setValue(1.5)
        self.iqr_spinbox.setDecimals(1)
        self.iqr_spinbox.setSuffix(" × IQR")
        self.iqr_spinbox.valueChanged.connect(self._on_settings_changed)
        iqr_layout.addWidget(iqr_label)
        iqr_layout.addWidget(self.iqr_spinbox)
        iqr_layout.addStretch()
        filter_layout.addLayout(iqr_layout)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        action_group = QGroupBox(tr("actions", "⚙️ 操作"))
        action_layout = QVBoxLayout()

        self.reload_button = QPushButton(tr("reload_data", "🔄 重新載入數據"))
        self.reload_button.setToolTip("強制重新載入油門分析數據")
        self.reload_button.clicked.connect(self.reload_requested.emit)
        action_layout.addWidget(self.reload_button)

        self.export_button = QPushButton(tr("export_chart", "💾 匯出圖表"))
        self.export_button.setToolTip("將圖表儲存為圖片檔案")
        self.export_button.clicked.connect(self.export_requested.emit)
        action_layout.addWidget(self.export_button)

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        stats_group = QGroupBox(tr("statistics", "📊 統計資訊"))
        stats_layout = QVBoxLayout()
        self.stats_label = QLabel(tr("waiting_for_data", "等待數據..."))
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("font-size: 10px; color: gray;")
        stats_layout.addWidget(self.stats_label)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

    def _on_settings_changed(self):
        settings = self.get_filter_settings()
        self.settings_changed.emit(settings)

    def get_filter_settings(self) -> Dict[str, Any]:
        return {
            "filter_pit_laps": self.filter_pit_checkbox.isChecked(),
            "filter_outliers": self.filter_outliers_checkbox.isChecked(),
            "outlier_threshold": self.iqr_spinbox.value(),
            "filter_yellow_flags": self.filter_caution_checkbox.isChecked(),
        }

    def update_statistics(self, stats_text: str):
        self.stats_label.setText(stats_text)

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        if not isinstance(settings, dict):
            return

        with QSignalBlocker(self.filter_pit_checkbox):
            self.filter_pit_checkbox.setChecked(settings.get("filter_pit_laps", True))

        with QSignalBlocker(self.filter_outliers_checkbox):
            self.filter_outliers_checkbox.setChecked(settings.get("filter_outliers", True))

        with QSignalBlocker(self.filter_caution_checkbox):
            self.filter_caution_checkbox.setChecked(settings.get("filter_yellow_flags", True))

        with QSignalBlocker(self.iqr_spinbox):
            self.iqr_spinbox.setValue(float(settings.get("outlier_threshold", 1.5)))


class ThrottleBoxPlotAnalysis(UniversalAnalysisMDI):
    """油門箱型圖分析 MDI 模組"""

    def __init__(
        self,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        parent=None,
        **kwargs,
    ):
        logger.info("[THROTTLE_MDI] ThrottleBoxPlotAnalysis 開始初始化...")

        if "throttle_boxplot" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            throttle_config = AnalysisMDIConfig(
                analysis_type="throttle_boxplot",
                display_name=tr("throttle_box_plot", "油門箱型圖"),
                default_size=(1200, 700),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False,
                chart_types=["boxplot"],
            )
            UniversalAnalysisMDI.register_mdi_module_type("throttle_boxplot", throttle_config)

        super().__init__("throttle_boxplot", parent)
        logger.info("[THROTTLE_MDI] 基類初始化完成, 數據管理器: %s", self.data_manager)

        self.control_widget: Optional[ThrottleBoxPlotControlWidget] = None
        self._pending_boxplot_settings: Optional[Dict[str, Any]] = None

        logger.info("[THROTTLE_MDI] 開始初始化模組組件...")
        if not self.initialize_module():
            logger.error("[THROTTLE_MDI] ❌ 模組組件初始化失敗")
            return

        logger.info("[THROTTLE_MDI] ✅ 模組組件初始化完成")
        logger.info("[THROTTLE_MDI] 數據管理器: %s", self.data_manager)
        logger.info("[THROTTLE_MDI] 圖表組件: %s", self.chart_widget)

        self.set_responsive_layout()

        self.settings_manager = gui_settings_manager
        try:
            self.settings_manager.boxplot_settings_changed.connect(self._on_global_boxplot_settings_changed)
        except Exception as exc:
            logger.exception("[THROTTLE_MDI] 無法連接全域設定信號: %s", exc)
        self._on_global_boxplot_settings_changed(self.settings_manager.get_boxplot_settings())

        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session

        if kwargs:
            self._debug(f"忽略未使用的初始化參數: {kwargs}")

    def create_data_manager(self) -> ThrottleBoxPlotDataManager:
        return ThrottleBoxPlotDataManager(self)

    def create_chart_widget(self) -> ThrottleBoxPlotChartWidget:
        return ThrottleBoxPlotChartWidget(parent=None)

    def create_additional_widgets(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        try:
            control_widget = self.create_control_widget()
            self.control_widget = control_widget
        except Exception as exc:
            logger.exception("[THROTTLE_MDI] 建立控制面板失敗: %s", exc)
            import traceback

            traceback.print_exc()
            self.control_widget = None
            control_widget = None

        if control_widget is not None:
            control_widget.setVisible(False)
            if self._pending_boxplot_settings:
                control_widget.apply_settings(self._pending_boxplot_settings)

        return widgets

    def create_control_widget(self) -> ThrottleBoxPlotControlWidget:
        control_widget = ThrottleBoxPlotControlWidget(self.main_widget)
        control_widget.settings_changed.connect(self._on_filter_settings_changed)
        control_widget.reload_requested.connect(self._on_reload_requested)
        control_widget.export_requested.connect(self._on_export_requested)
        return control_widget

    def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        try:
            logger.info("[THROTTLE_MDI] ========== 油門箱型圖參數更新 ==========")
            logger.info("[THROTTLE_MDI] 收到參數: %s %s %s", year, race, session)
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
                logger.info("[THROTTLE_MDI] 數據載入結果: %s", result)
                if not result:
                    logger.warning("[THROTTLE_MDI] ⚠️ 數據載入請求未成功提交")
            logger.info("[THROTTLE_MDI] 參數更新完成")
            return True
        except Exception as exc:
            logger.exception("[THROTTLE_MDI] 參數更新失敗: %s", exc)
            import traceback

            traceback.print_exc()
            return False

    def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
        return self.update_lap_parameters(year=year, race=race, session=session)

    def _on_filter_settings_changed(self, settings: Dict[str, Any]):
        logger.info("[THROTTLE_MDI] 過濾設定變更: %s", settings)
        if not hasattr(self, "settings_manager") or self.settings_manager is None:
            return

        global_settings = self.settings_manager.get_boxplot_settings()
        payload = dict(global_settings)
        payload.update(
            {
                "filter_pit_laps": settings.get("filter_pit_laps", payload.get("filter_pit_laps", True)),
                "filter_outliers": settings.get("filter_outliers", payload.get("filter_outliers", True)),
                "outlier_threshold": settings.get("outlier_threshold", payload.get("outlier_threshold", 1.5)),
                "filter_yellow_flags": settings.get("filter_yellow_flags", payload.get("filter_yellow_flags", True)),
            }
        )
        self.settings_manager.update_boxplot_settings(**payload)

    def _on_global_boxplot_settings_changed(self, settings: Dict[str, Any]) -> None:
        if not isinstance(settings, dict):
            return

        self._pending_boxplot_settings = dict(settings)
        control_ready = hasattr(self, "control_widget") and self.control_widget is not None
        data_ready = hasattr(self, "data_manager") and self.data_manager is not None
        chart_ready = hasattr(self, "chart_widget") and self.chart_widget is not None

        if control_ready:
            self.control_widget.apply_settings(settings)

        if not data_ready:
            return

        try:
            self.data_manager.update_filter_settings(settings)
            processed = self.data_manager.get_processed_data()
            if processed and chart_ready:
                self.chart_widget.update_data(processed)
                if control_ready:
                    driver_data = processed.get("driver_throttle_durations", {}) or {}
                    total_drivers = len(driver_data)
                    total_laps = sum(len(durations) for durations in driver_data.values())
                    stats_text = f"✅ 車手: {total_drivers} | 取樣數: {total_laps}"
                    self.control_widget.update_statistics(stats_text)
        except Exception as exc:
            logger.exception("[THROTTLE_MDI] 全域設定套用失敗: %s", exc)
            import traceback

            traceback.print_exc()

    def _on_data_load_error(self, error_message: str):
        logger.error("[THROTTLE_MDI] ❌ 數據載入錯誤: %s", error_message)
        if hasattr(self, "control_widget") and self.control_widget:
            self.control_widget.update_statistics("❌ 數據載入失敗")

        if not hasattr(self, "main_widget") or self.main_widget is None:
            return

        if "API" in error_message and "本地" in error_message:
            solution_text = (
                f"無法載入{tr('throttle_box_plot', '油門箱型圖')}數據:\n{error_message}\n\n"
                "請執行以下操作之一:\n\n"
                "方案 1: 啟動 API 服務器\n"
                "   開啟新終端執行: python refactored_api.py\n"
                "   然後點擊「重新載入」按鈕\n\n"
                "方案 2: 手動生成數據檔案\n"
                f"   執行: python f1_analysis_modular_main.py -f 54 -y {self.current_year} -r {self.current_race} -s {self.current_session}\n"
                "   然後點擊「重新載入」按鈕"
            )
        else:
            solution_text = (
                f"數據載入失敗:\n{error_message}\n\n"
                "請檢查 API 服務器是否運行, 或確認本地 JSON 檔案存在。"
            )

        QMessageBox.warning(
            self.main_widget,
            f"{tr('throttle_box_plot', '油門箱型圖')} - 數據載入失敗",
            solution_text,
            QMessageBox.Ok,
        )

    def _on_reload_requested(self):
        logger.info("[THROTTLE_MDI] 重新載入數據...")
        if not self.data_manager:
            return
        success = self.data_manager.load_data(
            year=self.current_year,
            race=self.current_race,
            session=self.current_session,
            force_refresh=True,
        )
        if not success:
            logger.warning("[THROTTLE_MDI] 重新載入請求無法提交")
            if self.control_widget:
                self.control_widget.update_statistics("❌ 重新載入失敗")

    def _on_export_requested(self):
        if not self.chart_widget:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_widget,
            tr("throttle_box_plot.export_dialog_title", "儲存油門箱型圖"),
            "throttle_box_plot.png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg)",
        )
        if not file_path:
            return
        success = self.chart_widget.export_chart(file_path)
        if success:
            QMessageBox.information(
                self.main_widget,
                tr("throttle_box_plot.export_success_title", "匯出成功"),
                tr("throttle_box_plot.export_success_body", "圖表已成功匯出。"),
            )

    def export_current_chart(self) -> bool:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"throttle_box_plot_{self.current_year}_{self.current_race}_{self.current_session}_{timestamp}.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_widget,
            tr("throttle_box_plot.export_dialog_title", "儲存油門箱型圖"),
            default_name,
            "PNG (*.png);;JPEG (*.jpg *.jpeg)",
        )
        if not file_path:
            return False
        return self.chart_widget.export_chart(file_path) if self.chart_widget else False

    def refresh_analysis(self) -> None:
        self._on_reload_requested()

    def clear_data(self) -> None:
        if self.chart_widget:
            self.chart_widget.update_data({"driver_throttle_durations": {}, "statistics": {}})
        if self.control_widget:
            self.control_widget.update_statistics(tr("waiting_for_data", "等待數據..."))
    
    def reset_chart_view(self):
        """
        重置圖表視圖（主 GUI "Show All Data" 按鈕調用）
        
        這個方法會被主 GUI 的 show_all_data_in_current_tab() 調用
        用於恢復所有被隱藏的車手數據
        """
        try:
            logger.info("[THROTTLE_MDI] 🔄 收到 reset_chart_view 請求")
            
            # 檢查 chart_widget 是否存在
            if not hasattr(self, 'chart_widget') or not self.chart_widget:
                logger.warning("[THROTTLE_MDI] ⚠️  chart_widget 不存在")
                return
            
            # 檢查 chart_widget 是否有 show_all_drivers 方法
            if not hasattr(self.chart_widget, 'show_all_drivers'):
                logger.warning("[THROTTLE_MDI] ⚠️  chart_widget 沒有 show_all_drivers 方法")
                return
            
            # 調用 Widget 的 show_all_drivers() 方法
            logger.info("[THROTTLE_MDI] ✅ 調用 chart_widget.show_all_drivers()")
            self.chart_widget.show_all_drivers()
            
        except Exception as e:
            logger.exception("[THROTTLE_MDI] ❌ reset_chart_view 失敗: %s", e)
            import traceback
            traceback.print_exc()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        if export_format.lower() != "json":
            logger.warning("[THROTTLE_MDI] 不支援的匯出格式: %s", export_format)
            return False
        try:
            current_data = self.data_manager.get_processed_data() if self.data_manager else None
            if not current_data:
                logger.warning("[THROTTLE_MDI] 沒有可匯出的數據")
                return False
            payload = {
                "module": "throttle_box_plot",
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
            logger.exception("[THROTTLE_MDI] 匯出數據失敗: %s", exc)
            return False

    def resizeEvent(self, event):
        """在 MDI 視窗尺寸變更時維護圖表佈局。"""
        try:
            try:
                super().resizeEvent(event)
            except AttributeError:
                # 基底 QObject 沒有 resizeEvent，忽略即可
                pass

            if not event:
                return

            old_size = event.oldSize() if hasattr(event, "oldSize") else None
            new_size = event.size() if hasattr(event, "size") else None

            if old_size and new_size:
                logger.info(
                    "[THROTTLE_MDI] resizeEvent: MDI視窗縮放 %sx%s -> %sx%s",
                    old_size.width(),
                    old_size.height(),
                    new_size.width(),
                    new_size.height(),
                )

            if hasattr(self, "chart_widget") and self.chart_widget:
                if hasattr(self.chart_widget, "update_chart_layout"):
                    logger.info("[THROTTLE_MDI] resizeEvent: 觸發圖表重新佈局")
                    self.chart_widget.update_chart_layout()
                else:
                    logger.info("[THROTTLE_MDI] resizeEvent: 圖表組件不支援動態佈局更新")
            else:
                logger.info("[THROTTLE_MDI] resizeEvent: 圖表組件尚未初始化")

        except Exception as exc:
            logger.exception("[ERROR] [THROTTLE_MDI] resizeEvent 處理失敗: %s", exc)

    def set_responsive_layout(self):
        """為主視圖與子元件套用響應式大小策略。"""
        try:
            from PyQt5.QtWidgets import QSizePolicy

            if hasattr(self, "main_widget") and self.main_widget:
                self.main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            if hasattr(self, "chart_widget") and self.chart_widget:
                self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            if hasattr(self, "control_widget") and self.control_widget:
                self.control_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

            logger.info("[THROTTLE_MDI] 響應式佈局已設置")

        except Exception as exc:
            logger.exception("[ERROR] [THROTTLE_MDI] 設置響應式佈局失敗: %s", exc)


