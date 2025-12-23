#!/usr/bin/env python3
"""GUI data loader for the all-drivers brake all laps analysis (Function 122)."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader


class BrakeAllLapsApiWorker(QThread):
    """
    全車手煞車全圈數分析 API 請求工作執行緒
    
    使用 QThread 在背景執行緒執行 API 請求，避免 GUI 阻塞
    參考實現：BrakePerformanceApiWorker (F34)
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, params: Dict[str, Any], base_url: str, timeout: float = 60.0):
        """
        初始化 API Worker
        
        Args:
            params: API 參數 (function_id, year, race, session)
            base_url: API 基礎 URL
            timeout: 請求超時時間（秒）- F122 全圈數分析需要更長時間
        """
        super().__init__()
        self.params = dict(params)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._logger = get_logger(component="brake_all_laps_api_worker")
    
    def run(self):
        """在背景執行緒執行 API 請求"""
        try:
            # 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            self._logger.info("[BRAKE_ALL_LAPS_API] 調用 API: %s", endpoint)
            self._logger.debug("[BRAKE_ALL_LAPS_API] 參數: %s", self.params)
            
            # 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                return
            
            # 在背景執行緒發送 POST 請求
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=self.params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            self.progress.emit(70)
            
            # 中斷檢查點 3: HTTP 請求後
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
            
            self._logger.info("[BRAKE_ALL_LAPS_API] API 調用成功")
            self._logger.info("[BRAKE_ALL_LAPS_API] 延遲: %sms", meta['latency_ms'])
            self._logger.debug("[BRAKE_ALL_LAPS_API] 數據源: %s", meta['source'])
            
            self.progress.emit(90)
            # 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                return
            # 通過信號將結果返回主線程
            self.success.emit({"payload": payload, "meta": meta})
            
        except Exception as exc:
            # 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API 請求失敗: {str(exc)}"
            self._logger.exception("[BRAKE_ALL_LAPS_API] %s", error_msg)
            # 通過信號發送錯誤訊息
            self.failure.emit(error_msg)
        finally:
            # 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class BrakeAllLapsDataLoader(UniversalDataLoader):
    """Unified loader for Function 122 results with API-first behaviour."""

    ANALYSIS_TYPE = "brake_all_laps"

    def __init__(self, parent=None):
        config = AnalysisConfig(
            display_name=tr("all_drivers_brake_all_laps_analysis", "All Drivers Brake All Laps Analysis"),
            debug_prefix="BRAKE_ALL_LAPS",
            data_source="api",  # API-ONLY 模式
            cli_function="122",
            file_patterns=[],   # 不使用本地 JSON
        )

        if self.ANALYSIS_TYPE not in self.ANALYSIS_TYPES:
            self.register_analysis_type(self.ANALYSIS_TYPE, config)

        super().__init__(self.ANALYSIS_TYPE, parent)

        self._api_base_url = self._determine_api_base_url()
        self._api_timeout = 60.0  # F122 需要更長超時時間
        self._last_api_payload: Optional[Dict[str, Any]] = None
        self._api_worker: Optional[BrakeAllLapsApiWorker] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_data(self, **kwargs) -> bool:  # type: ignore[override]
        """Load brake all laps data via API only (no local JSON)."""

        if not self._validate_load_parameters(kwargs):
            self._error(tr("brake_all_laps_load_param_validation_failed", "Parameter validation failed"))
            self.load_error.emit(tr("brake_all_laps_load_param_invalid", "Invalid load parameters"))
            return False

        # API-ONLY 模式：直接調用 API，不檢查本地 JSON
        self._debug(tr("brake_all_laps_api_only", "API-ONLY mode: Fetching data from API"))
        self._fetch_via_api_async(**kwargs)
        return True  # 立即返回，不阻塞

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

    # API-ONLY 模式：不需要 _build_filename_patterns 方法

    def _validate_data_format(self, raw_data: Any) -> bool:
        if not isinstance(raw_data, dict):
            return False
        if not raw_data.get("success", False):
            return False

        # 嘗試找到包含 'drivers' 的層級（F122 使用 'drivers' 而非 'driver_brakes'）
        current = raw_data.get("data")
        max_depth = 20  # 防止無限遞歸
        depth = 0
        
        while isinstance(current, dict) and depth < max_depth:
            # 檢查是否到達實際數據層
            if "drivers" in current:
                drivers = current.get("drivers")
                if isinstance(drivers, list):
                    self._debug(f"Found valid 'drivers' at depth {depth + 1} (count: {len(drivers)})")
                    return True
                else:
                    self._error(f"'drivers' is not a list: {type(drivers)}")
                    return False
            
            # 繼續往下一層穿透
            if "data" in current:
                current = current["data"]
                depth += 1
            else:
                # 沒有更多嵌套但也沒找到 drivers
                self._error(f"'drivers' key not found at depth {depth + 1}")
                self._error(f"Available keys: {list(current.keys())}")
                return False
        
        if depth >= max_depth:
            self._error(f"Nested depth exceeds {max_depth}, possible circular reference")
            return False
        
        self._error("Cannot find 'drivers' in data")
        return False

    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """處理 F122 數據格式"""
        # 穿透嵌套找到實際數據層
        current = raw_data.get("data", {}) if isinstance(raw_data, dict) else {}
        max_depth = 20
        depth = 0
        
        while isinstance(current, dict) and depth < max_depth:
            if "drivers" in current:
                # 找到實際數據層
                payload = current
                self._debug(f"Found actual data at depth {depth + 1}")
                break
            
            if "data" in current:
                current = current["data"]
                depth += 1
            else:
                # 沒找到，使用當前層作為 fallback
                payload = current
                self._debug(f"Stopped at depth {depth + 1}, using current layer")
                break
        else:
            # 超過最大深度或 current 不是字典
            payload = current if isinstance(current, dict) else {}
            self._debug(f"Using final layer (depth={depth})")
        
        # 提取元數據
        metadata = dict(payload.get("metadata") or {})
        main_brake_zone = payload.get("main_brake_zone") or {}

        metadata.setdefault("function_id", raw_data.get("function_id", "122"))
        metadata.setdefault("message", raw_data.get("message"))
        metadata.setdefault("source", raw_data.get("source", "local-json"))
        if self._last_api_payload and raw_data is self._last_api_payload:
            metadata["source"] = "api"
        metadata.setdefault("drivers_total", len(payload.get("drivers") or []))

        processed = {
            "metadata": metadata,
            "drivers": payload.get("drivers") or [],
            "main_brake_zone": main_brake_zone,
            "raw_payload": raw_data,
        }
        return processed

    # ------------------------------------------------------------------
    # Async API Methods
    # ------------------------------------------------------------------

    def _determine_api_base_url(self) -> str:
        """確定 API 基礎 URL"""
        return resolve_api_base_url()

    def _fetch_via_api_async(self, **kwargs):
        """異步 API 調用（不阻塞主 GUI）"""
        # 取消正在執行的 worker
        if self._api_worker and self._api_worker.isRunning():
            self._debug("Cancelling existing API worker")
            self._api_worker.requestInterruption()
            self._api_worker.wait(500)
        
        # 構建 API 參數
        params = {
            "function_id": "122",
            "year": str(kwargs.get("year", "")),
            "race": str(kwargs.get("race", "")),
            "session": str(kwargs.get("session", "")),
        }
        
        self._debug(f"Starting async API request: {params}")
        
        # 創建並啟動 worker
        self._api_worker = BrakeAllLapsApiWorker(
            params=params,
            base_url=self._api_base_url,
            timeout=self._api_timeout
        )
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_failure)
        self._api_worker.start()

    def _on_api_progress(self, progress: int):
        """API 進度回調"""
        self._debug(f"API progress: {progress}%")
        self.status_changed.emit(tr("loading_progress", "Loading... {progress}%").format(progress=progress))

    def _on_api_success(self, result: Dict[str, Any]):
        """API 成功回調"""
        try:
            payload = result.get("payload", {})
            meta = result.get("meta", {})
            
            self._last_api_payload = payload
            
            if not self._validate_data_format(payload):
                self.load_error.emit(tr("data_format_invalid", "Invalid data format"))
                return
            
            processed = self._process_data(payload)
            processed["metadata"]["source"] = "api"
            processed["metadata"]["latency_ms"] = meta.get("latency_ms")
            
            self._debug(f"API data processed, drivers count: {len(processed.get('drivers', []))}")
            
            self.data_loaded.emit(processed)
            
        except Exception as e:
            self._error(f"API data processing failed: {e}")
            self.load_error.emit(str(e))

    def _on_api_failure(self, error_msg: str):
        """API 失敗回調"""
        self._error(f"API request failed: {error_msg}")
        self.load_error.emit(error_msg)

    def _cleanup_api_worker(self, sync_wait: bool = False) -> None:
        """
        清理 API Worker 執行緒 - 修復 QThread 崩潰問題
        
        Args:
            sync_wait: 若為 True，使用阻塞等待（用於 closeEvent）
                      若為 False，使用異步清理（用於正常操作）
        
        修復 "QThread: Destroyed while thread is still running" 錯誤
        """
        if self._api_worker:
            # 1. 先斷開所有信號
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
            
            if self._api_worker.isRunning():
                # 2. 請求中斷
                self._api_worker.requestInterruption()
                self._api_worker.quit()
                
                if sync_wait:
                    # 3a. 同步等待（用於 closeEvent）
                    # 注意：如果 worker 被阻塞在 requests.post()，wait() 可能無效
                    # 使用短超時後強制終止
                    if not self._api_worker.wait(500):  # 500ms 超時
                        self._debug("API Worker 500ms 後仍未停止，強制終止")
                        self._api_worker.terminate()
                        self._api_worker.wait(200)  # 終止後短暫等待
                    else:
                        self._debug("API Worker 已正常停止")
                else:
                    # 3b. 異步清理（用於正常操作，非阻塞）
                    pass
            
            # 4. 解除引用
            self._api_worker = None
    
    def cleanup(self):
        """清理資源"""
        self._cleanup_api_worker(sync_wait=True)
        super().cleanup()
