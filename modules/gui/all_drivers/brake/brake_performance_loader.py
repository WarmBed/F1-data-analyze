#!/usr/bin/env python3
"""GUI data loader for the all-drivers straight-line speed analysis (Function 34)."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
import certifi
from PyQt5.QtCore import QThread, pyqtSignal

from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader


class BrakePerformanceApiWorker(QThread):
    """
    全車手煞車性能 API 請求工作執行緒
    
    ✅ 修復 GUI 阻塞問題：使用 QThread 在背景執行緒執行 API 請求
    參考實現：IdealLapRankingApiWorker
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, params: Dict[str, Any], base_url: str, timeout: float = 45.0):
        """
        初始化 API Worker
        
        Args:
            params: API 參數 (function_id, year, race, session)
            base_url: API 基礎 URL
            timeout: 請求超時時間（秒）
        """
        super().__init__()
        self.params = dict(params)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._logger = get_logger(component="brake_performance_api_worker")
    
    def run(self):
        """✅ 在背景執行緒執行 API 請求"""
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            self._logger.info("[BRAKE_API_WORKER] 🌐 調用 API: %s", endpoint)
            self._logger.debug("[BRAKE_API_WORKER] 📋 參數: %s", self.params)
            
            # ✅ 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                return
            
            # ✅ 在背景執行緒發送 POST 請求（不阻塞主 GUI）
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=self.params,
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
            
            self._logger.info("[BRAKE_API_WORKER] ✅ API 調用成功")
            self._logger.info("[BRAKE_API_WORKER] ⏱️  延遲: %sms", meta['latency_ms'])
            self._logger.debug("[BRAKE_API_WORKER] 📊 數據源: %s", meta['source'])
            
            self.progress.emit(90)
            # ✅ 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                return
            # ✅ 通過信號將結果返回主線程
            self.success.emit({"payload": payload, "meta": meta})
            
        except Exception as exc:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API 請求失敗: {str(exc)}"
            self._logger.exception("[BRAKE_API_WORKER] ❌ %s", error_msg)
            # ✅ 通過信號發送錯誤訊息
            self.failure.emit(error_msg)
        finally:
            # ✅ 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class BrakePerformanceDataLoader(UniversalDataLoader):
    """Unified loader for Function 34 results with API-first behaviour."""

    ANALYSIS_TYPE = "brake_performance"

    def __init__(self, parent=None):
        config = AnalysisConfig(
            display_name=tr("brake_performance_analysis", "煞車性能分析"),
            debug_prefix="BRAKE_PERF",
            data_source="json",
            cli_function="34",
            file_patterns=["all_drivers_brake_performance_*.json", "brake_performance_*.json"],
        )

        if self.ANALYSIS_TYPE not in self.ANALYSIS_TYPES:
            self.register_analysis_type(self.ANALYSIS_TYPE, config)

        super().__init__(self.ANALYSIS_TYPE, parent)

        self._api_base_url = self._determine_api_base_url()
        self._api_timeout = 45.0
        self._last_api_payload: Optional[Dict[str, Any]] = None
        self._api_worker: Optional[BrakePerformanceApiWorker] = None  # ✅ API Worker 實例

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_data(self, **kwargs) -> bool:  # type: ignore[override]
        """Load straight-line speed data, fetching from API when needed."""

        if not self._validate_load_parameters(kwargs):
            self._error(tr("brake_perf_load_param_validation_failed", "載入參數驗證失敗"))
            self.load_error.emit(tr("brake_perf_load_param_invalid", "載入參數不正確"))
            return False

        existing = self._find_data_file(**kwargs)
        if not existing:
            self._debug(tr("brake_perf_no_local_file", "找不到本地煞車性能檔案，準備透過 API 取得最新資料"))
            # ✅ 修復：使用異步 API Worker（不阻塞主 GUI）
            self._fetch_via_api_async(**kwargs)
            return True  # 立即返回，不阻塞

        return super().load_data(**kwargs)

    # ------------------------------------------------------------------
    # UniversalDataLoader contract
    # ------------------------------------------------------------------

    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")

        try:
            year_int = int(year)
        except (TypeError, ValueError):
            return False

        if year_int < 2000 or year_int > 2100:
            return False
        if not isinstance(race, str) or len(race.strip()) < 2:
            return False
        if not isinstance(session, str) or not session.strip():
            return False
        return True

    def _build_filename_patterns(self, **kwargs) -> List[str]:
        year = kwargs.get("year", "*")
        race = kwargs.get("race", "*")
        session = kwargs.get("session", "*")

        race_slug = self._sanitize_for_filename(race)
        session_slug = self._sanitize_for_filename(session)

        return [
            f"all_drivers_brake_performance_{year}_{race}_{session}.json",
            f"all_drivers_brake_performance_{year}_{race_slug}_{session_slug}.json",
            f"all_drivers_brake_performance_*_{race}_{session}.json",
            f"all_drivers_brake_performance_*_{race_slug}_{session_slug}.json",
            f"brake_performance_{year}_{race}_{session}.json",
            f"brake_performance_{year}_{race_slug}_{session_slug}.json",
        ]

    def _generate_data_via_cli(self, **kwargs) -> bool:
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用 (Function 34)")
        self._debug("💡 請透過 API 或手動執行 CLI 生成 JSON")
        return False

    def _validate_data_format(self, raw_data: Any) -> bool:
        if not isinstance(raw_data, dict):
            return False
        if not raw_data.get("success", False):
            return False

        # ⚠️ 修正：API 返回的數據可能有多層嵌套，需要遞歸穿透
        # 嘗試找到包含 'driver_brakes' 的層級
        current = raw_data.get("data")
        max_depth = 20  # 防止無限遞歸
        depth = 0
        
        while isinstance(current, dict) and depth < max_depth:
            # 檢查是否到達實際數據層
            if "driver_brakes" in current:
                driver_brakes = current.get("driver_brakes")
                if isinstance(driver_brakes, list):
                    self._debug(f"✅ 在第 {depth + 1} 層找到有效的 driver_brakes (車手數: {len(driver_brakes)})")
                    return True
                else:
                    self._error(f"driver_brakes 不是列表: {type(driver_brakes)}")
                    return False
            
            # 繼續往下一層穿透
            if "data" in current:
                current = current["data"]
                depth += 1
            else:
                # 沒有更多嵌套但也沒找到 driver_brakes
                self._error(f"在第 {depth + 1} 層找不到 'driver_brakes' 鍵")
                self._error(f"當前層的鍵: {list(current.keys())}")
                return False
        
        if depth >= max_depth:
            self._error(f"數據嵌套層數超過 {max_depth}，可能存在循環引用")
            return False
        
        self._error("無法找到包含 'driver_brakes' 的數據層")
        return False

    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        # ⚠️ 修正：API 返回的數據可能有多層嵌套，需要遞歸穿透找到實際數據
        current = raw_data.get("data", {}) if isinstance(raw_data, dict) else {}
        max_depth = 20
        depth = 0
        
        # 穿透嵌套找到包含 'driver_brakes' 的層級
        while isinstance(current, dict) and depth < max_depth:
            if "driver_brakes" in current:
                # 找到實際數據層
                payload = current
                self._debug(f"✅ 在第 {depth + 1} 層找到實際數據")
                break
            
            if "data" in current:
                current = current["data"]
                depth += 1
            else:
                # 沒找到，使用當前層作為 fallback
                payload = current
                self._debug(f"⚠️ 在第 {depth + 1} 層停止穿透，使用當前層")
                break
        else:
            # 超過最大深度或 current 不是字典
            payload = current if isinstance(current, dict) else {}
            self._debug(f"⚠️ 使用最終層級 (depth={depth})")
        
        metadata = dict(payload.get("metadata") or {})
        summary = payload.get("summary") or {}
        chart = payload.get("chart_data")

        metadata.setdefault("function_id", raw_data.get("function_id", "34"))
        metadata.setdefault("message", raw_data.get("message"))
        metadata.setdefault("source", raw_data.get("source", "local-json"))
        metadata.setdefault("success", raw_data.get("success"))
        if self._last_api_payload and raw_data is self._last_api_payload:
            metadata["source"] = "api"
        metadata.setdefault("drivers_total", len(payload.get("driver_brakes") or []))

        processed = {
            "metadata": metadata,
            "driver_brakes": payload.get("driver_brakes") or [],
            "reference_brake_zone": payload.get("reference_brake_zone") or {},
            "summary": summary,
            "chart_data": chart,
            "raw_payload": raw_data,
        }
        return processed

    # ------------------------------------------------------------------
    # Async API Methods (✅ 修復 GUI 阻塞)
    # ------------------------------------------------------------------

    def _fetch_via_api_async(self, **kwargs):
        """
        ✅ 異步 API 請求（不阻塞主 GUI）
        
        使用 BrakePerformanceApiWorker 在背景執行緒執行 API 請求
        """
        try:
            year = int(kwargs["year"])
            race = str(kwargs["race"])
            session = str(kwargs["session"])
        except (KeyError, TypeError, ValueError) as exc:
            self._error(tr("brake_perf_api_missing_params", "缺少必要參數，無法呼叫 API: {error}").format(error=str(exc)))
            self.load_error.emit(tr("brake_perf_load_missing_params", "缺少必要參數，無法載入煞車性能分析"))
            return

        params = {
            "function_id": 34,
            "year": year,
            "race": race,
            "session": session,
        }
        if kwargs.get("force_refresh"):
            params["force_refresh"] = True

        self.status_changed.emit(tr("brake_perf_loading_via_api", "透過 API 載入全部車手煞車性能資料..."))
        self.load_progress.emit(10)

        # ✅ 創建並啟動 API Worker
        self._api_worker = BrakePerformanceApiWorker(
            params,
            self._api_base_url,
            self._api_timeout
        )

        # ✅ 連接信號
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_failure)
        self._api_worker.progress.connect(self.load_progress.emit)

        # ✅ 啟動背景執行緒（主 GUI 不阻塞）
        self._api_worker.start()
        self._debug("✅ API Worker 已啟動，主 GUI 保持響應")

    def _on_api_success(self, result: dict):
        """
        ✅ API 成功回調（在主線程執行）
        
        Args:
            result: {"payload": API回應, "meta": 元數據}
        """
        payload = result.get("payload")
        meta = result.get("meta", {})
        
        self._debug(f"✅ API 調用成功，延遲: {meta.get('latency_ms')}ms")
        self._last_api_payload = payload

        try:
            # 驗證數據格式
            if not self._validate_data_format(payload):
                self._error("API 返回的數據格式驗證失敗")
                self.load_error.emit(tr("brake_perf_invalid_data_format", "數據格式不正確"))
                return

            # 處理數據
            processed_data = self._process_data(payload)
            self._current_data = processed_data

            # 發送成功信號
            self.load_progress.emit(100)
            self.status_changed.emit(tr("brake_perf_load_success", "煞車性能數據載入完成"))
            self.data_loaded.emit(processed_data)

            self._debug("✅ API 數據處理完成，已發送 data_loaded 信號")

        except Exception as e:
            self._error(f"處理 API 數據時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.load_error.emit(f"數據處理失敗: {str(e)}")

    def _on_api_failure(self, error_msg: str):
        """
        ✅ API 失敗回調（在主線程執行）
        
        Args:
            error_msg: 錯誤訊息
        """
        self._error(f"API 請求失敗: {error_msg}")
        self.load_progress.emit(0)
        self.status_changed.emit("API 請求失敗")
        # ⚠️ 不發送 load_error 信號，避免彈窗（API 失敗是正常情況）
        self._debug("💡 提示: API 暫時不可用，請稍後重試或檢查網絡連接")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fetch_via_api_and_cache(self, **kwargs) -> Optional[str]:
        try:
            year = int(kwargs["year"])
            race = str(kwargs["race"])
            session = str(kwargs["session"])
        except (KeyError, TypeError, ValueError) as exc:
            self._error(tr("brake_perf_api_missing_params", "缺少必要參數，無法呼叫 API: {error}").format(error=str(exc)))
            self.load_error.emit(tr("brake_perf_load_missing_params", "缺少必要參數，無法載入煞車性能分析"))
            return None

        params = {
            "function_id": 34,
            "year": year,
            "race": race,
            "session": session,
        }
        if kwargs.get("force_refresh"):
            params["force_refresh"] = True

        endpoint = f"{self._api_base_url}/api/v2/analysis/execute"
        self.status_changed.emit(tr("brake_perf_loading_via_api", "透過 API 載入全部車手煞車性能資料..."))
        self.load_progress.emit(25)

        try:
            response = requests.post(
                endpoint,
                params=params,
                timeout=self._api_timeout,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # broad catch to emit signal and log
            self._error(tr("brake_perf_api_load_failed", "API 載入失敗: {error}").format(error=str(exc)))
            # ⚠️ [API-ONLY 模式修正] 不發送 load_error 信號，避免彈窗
            # API 失敗是正常情況，讓用戶通過其他方式獲取數據
            self._debug("💡 提示: API 暫時不可用，請稍後重試或檢查網絡連接")
            return None

        if not isinstance(payload, dict) or not payload.get("success", False):
            message = payload.get("message") if isinstance(payload, dict) else tr("brake_perf_unknown_error", "未知錯誤")
            self._error(tr("brake_perf_api_return_failed", "API 返回失敗: {message}").format(message=message))
            # ⚠️ [API-ONLY 模式修正] 不發送 load_error 信號，避免彈窗
            self._debug("💡 提示: API 響應異常，請檢查後端服務狀態")
            return None

        self._last_api_payload = payload

        # ✅ [API-ONLY 模式] 禁止自動寫入 JSON 檔案
        # API 數據僅保存在記憶體中，不寫入磁碟
        self._debug("✅ API 數據已載入至記憶體（API-ONLY 模式：不寫入本地檔案）")
        self.load_progress.emit(60)
        
        # 返回 None 表示沒有檔案生成（這是正確的行為）
        return None

    # ❌ [API-ONLY 模式] 已禁用自動寫入功能
    # def _write_payload_to_cache(self, payload: Dict[str, Any], year: int, race: str, session: str) -> Optional[str]:
    #     """
    #     [已禁用] 寫入 API 結果到本地緩存
    #     
    #     ⚠️ API-ONLY 模式: 此方法已禁用，GUI 不應自動生成 JSON 檔案
    #     API 數據僅保存在記憶體中（self._last_api_payload）
    #     """
    #     try:
    #         os.makedirs("json", exist_ok=True)
    #         filename = self._make_filename(year, race, session)
    #         path = os.path.join("json", filename)
    #         with open(path, "w", encoding="utf-8") as handle:
    #             json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
    #         self._debug(tr("brake_perf_api_result_saved", "API 結果已寫入 {path}").format(path=path))
    #         return path
    #     except Exception as exc:
    #         self._error(tr("brake_perf_write_json_failed", "寫入 JSON 檔案失敗: {error}").format(error=str(exc)))
    #         return None

    def _make_filename(self, year: int, race: str, session: str) -> str:
        race_slug = self._sanitize_for_filename(race)
        session_slug = self._sanitize_for_filename(session)
        return f"all_drivers_brake_performance_{year}_{race_slug}_{session_slug}.json"

    def _sanitize_for_filename(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return "unknown"
        sanitized = []
        for ch in text:
            if ch.isalnum() or ch in {"-", "_"}:
                sanitized.append(ch)
            else:
                sanitized.append("_")
        collapsed = "".join(sanitized)
        while "__" in collapsed:
            collapsed = collapsed.replace("__", "_")
        return collapsed.strip("_") or "value"

    def _determine_api_base_url(self) -> str:
        return resolve_api_base_url(event_logger=self._debug)


__all__ = ["BrakePerformanceDataLoader"]
