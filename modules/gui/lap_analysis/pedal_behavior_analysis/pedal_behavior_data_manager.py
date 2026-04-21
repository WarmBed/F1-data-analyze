#!/usr/bin/env python3
"""
PedalBehaviorDataManager - 油門/煞車行為分析數據管理器
========================================================

管理 Function 54 (driver_throttle_ratio) 的數據載入與處理：
- 計算每位車手的平均 Pedal State 比例
- 過濾進站圈、黃旗圈、紅旗圈
- 支援 Stint Selection 分段過濾

數據來源：REST API (Function 54) 或本地 JSON 檔案
輸出格式：每位車手的 4 種 Pedal State 比例（throttle_only, brake_only, trail_braking, coasting）

Author: F1T Team
Date: 2026-01-12
Version: 2.0.0 (API-FIRST)
"""

import os
import time
import certifi
import requests
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtCore import pyqtSignal, QThread

from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
from core.logger import get_logger
from core.api_base_url import resolve_api_base_url

logger = get_logger(__name__)


class PedalBehaviorApiWorker(QThread):
    """背景工作執行緒，呼叫 REST API 取得 Pedal Behavior 分析資料"""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 90.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "http://localhost:8000").rstrip("/")
        self.params = dict(params)
        self.timeout = timeout

    def run(self) -> None:
        try:
            if self.isInterruptionRequested():
                logger.debug("[PEDAL_API_WORKER] 啟動前已被請求中斷，跳過執行")
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

            if self.isInterruptionRequested():
                logger.debug("[PEDAL_API_WORKER] 發送請求前被請求中斷")
                return
                
            logger.info(f"[PEDAL_API_WORKER] 呼叫 API: {endpoint}")
            logger.info(f"[PEDAL_API_WORKER] 參數: {query_params}")
            
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()
            )
            
            if self.isInterruptionRequested():
                logger.debug("[PEDAL_API_WORKER] API 回應後被請求中斷")
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
                logger.debug("[PEDAL_API_WORKER] 發送成功信號前被請求中斷")
                return

            self.progress.emit(100)
            logger.info(f"[PEDAL_API_WORKER] API 呼叫成功，延遲: {latency_ms:.0f}ms")
            self.success.emit({"data": data, "meta": meta})

        except requests.exceptions.Timeout:
            logger.error("[PEDAL_API_WORKER] API 請求超時")
            self.failure.emit("API 請求超時，請稍後重試")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[PEDAL_API_WORKER] 連線錯誤: {e}")
            self.failure.emit(f"無法連線到 API 伺服器: {e}")
        except Exception as e:
            logger.error(f"[PEDAL_API_WORKER] API 請求失敗: {e}")
            self.failure.emit(f"API 請求失敗: {e}")


class PedalBehaviorDataManager(UniversalDataLoader):
    """油門/煞車行為數據管理器 (API-FIRST 模式)"""
    
    # 自定義信號
    filter_settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        # 註冊 Pedal Behavior 分析類型 (API 模式)
        if "pedal_behavior" not in UniversalDataLoader.ANALYSIS_TYPES:
            pedal_config = AnalysisConfig(
                display_name="Pedal Behavior Analysis",
                debug_prefix="PEDAL_DATA",
                data_source="api",  # API 模式
                cli_function="54",
                api_endpoint="/api/v2/analysis/execute",
                api_function_id=54,
                api_timeout=90.0,
                file_patterns=[
                    "driver_throttle_ratio_{year}_{race}_{session}.json"
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                cache_enabled=True,
            )
            UniversalDataLoader.register_analysis_type("pedal_behavior", pedal_config)
        
        super().__init__(analysis_type="pedal_behavior", parent=parent)
        
        # Pedal Behavior 特定屬性
        self.driver_pedal_data: Dict[str, Dict[str, float]] = {}
        self.raw_lap_data: Dict[str, List[Dict]] = {}
        
        # 過濾設定
        self.filter_settings = {
            'filter_pit_laps': True,
            'filter_yellow_flags': True,
            'filter_red_flags': True,
            'filter_safety_car': True,
            'filter_vsc': True
        }
        
        # API 相關屬性
        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[PedalBehaviorApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        self._allow_local_fallback = True
        
        logger.info("[PEDAL_DATA_MGR] 初始化完成 (API-FIRST 模式)")
    
    def _determine_api_base_url(self) -> str:
        """決定 API 基礎 URL"""
        return resolve_api_base_url(event_logger=lambda msg: logger.debug(f"[PEDAL_DATA_MGR] {msg}"))
    
    def set_filter_settings(self, settings: Dict[str, bool]) -> None:
        """更新過濾設定並重新處理數據"""
        old_settings = self.filter_settings.copy()
        self.filter_settings.update(settings)
        
        logger.debug(f"[PEDAL_DATA_MGR] 過濾設定變更: {settings}")
        
        # 如果設定改變且有數據，重新處理
        if old_settings != self.filter_settings and self._raw_data_cache:
            processed = self._process_data(self._raw_data_cache)
            self.filter_settings_changed.emit(processed)
    
    # ========== API 載入方法（重寫 UniversalDataLoader）==========
    
    def load_data(self, **kwargs) -> bool:
        """
        載入數據 - API 優先模式
        
        如果 data_source 不是 "api"，則使用父類的本地 JSON 載入邏輯
        """
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
        self._debug(f"透過 API 載入 Pedal Behavior 資料: base_url={self._api_base_url}")
        self._debug(f"參數: {self._pending_params}")
        self.load_progress.emit(5)
        self.status_changed.emit("正在透過 API 載入 Pedal Behavior 分析資料...")

        try:
            self._start_api_request(self._pending_params)
            return True
        except Exception as exc:
            self._error(f"啟動 API 請求失敗: {exc}")
            self._is_loading = False
            if self._allow_local_fallback:
                self.status_changed.emit("API 載入失敗，改用本地資料")
                return super().load_data(**kwargs)
            else:
                self.load_error.emit(f"API 載入失敗: {exc}")
                return False
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證載入參數"""
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")
        if not year or not race or not session:
            self._debug("參數不完整：需要年份、比賽和賽段")
            return False
        return True
    
    def _start_api_request(self, params: Dict[str, Any]) -> None:
        """啟動 API 請求背景執行緒"""
        self._cleanup_api_worker()

        worker_params = {
            "year": params.get("year"),
            "race": params.get("race"),
            "session": params.get("session"),
            "force_refresh": params.get("force_refresh", False),
        }

        timeout = getattr(self.config, "api_timeout", 90.0)
        self._api_worker = PedalBehaviorApiWorker(
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
        
        logger.info("[PEDAL_DATA_MGR] API Worker 已啟動")

    def _cleanup_api_worker(self) -> None:
        """清理 API Worker"""
        if self._api_worker is not None:
            try:
                self._api_worker.requestInterruption()
                if self._api_worker.isRunning():
                    self._api_worker.quit()
                    self._api_worker.wait(1000)
            except Exception:
                pass
            self._api_worker = None

    def _on_api_progress(self, value: int) -> None:
        """處理 API 進度更新"""
        try:
            bounded = max(0, min(int(value), 100))
            self.load_progress.emit(bounded)
        except Exception:
            pass

    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        """處理 API 成功回調"""
        self._debug("========== API 成功回調 ==========")
        try:
            raw_data = payload.get("data")
            meta = payload.get("meta", {})
            self._last_api_meta = meta or {}
            self._last_data_source = "api"

            # 處理雙層嵌套格式
            if isinstance(raw_data, dict) and "data" in raw_data and "success" in raw_data:
                self._debug("檢測到雙層嵌套格式，提取內層 data")
                raw_data = raw_data["data"]

            if not self._validate_data_format(raw_data):
                self._debug(f"驗證失敗！數據結構: {list(raw_data.keys()) if isinstance(raw_data, dict) else type(raw_data)}")
                raise ValueError("API 回傳數據格式不符合預期")

            # 處理數據
            processed = self._process_data(raw_data)
            
            self._is_loading = False
            self.load_progress.emit(100)
            self.status_changed.emit("Pedal Behavior 數據載入完成")
            
            # 發送成功信號
            self.data_loaded.emit(processed)
            
            self._debug(f"Pedal Behavior 數據載入成功，共 {len(self.driver_pedal_data)} 位車手")

        except Exception as exc:
            self._error(f"API 數據處理失敗: {exc}")
            import traceback
            traceback.print_exc()
            self._is_loading = False
            
            if self._allow_local_fallback:
                self._debug("嘗試本地 JSON 後備...")
                super().load_data(**self._pending_params)
            else:
                self.load_error.emit(f"數據處理失敗: {exc}")

    def _on_api_error(self, error_message: str) -> None:
        """處理 API 錯誤"""
        self._error(f"API 錯誤: {error_message}")
        self._is_loading = False
        
        if self._allow_local_fallback:
            self._debug("API 失敗，嘗試本地 JSON 後備...")
            super().load_data(**self._pending_params)
        else:
            self.load_error.emit(error_message)
    
    # ========== 數據驗證和處理 ==========
    
    def _validate_data_format(self, data: Any) -> bool:
        """驗證 Function 54 數據格式"""
        if not isinstance(data, dict):
            self._debug("數據格式錯誤：必須是字典格式")
            return False
        
        # 檢查 Function 54 的標準輸出格式
        if "analysis" not in data:
            self._debug("數據格式錯誤：缺少 analysis 欄位")
            return False
        
        analysis = data["analysis"]
        if "drivers" not in analysis:
            self._debug("數據格式錯誤：缺少 analysis.drivers 欄位")
            return False
        
        return True
    
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """處理載入的 Function 54 數據"""
        try:
            if not isinstance(data, dict):
                raise ValueError("數據格式不正確：必須是字典格式")
            
            # 快取原始數據
            self._raw_data_cache = data
            
            # 解析 JSON 結構
            analysis = data.get("analysis", {})
            drivers = analysis.get("drivers", {})
            
            if not drivers:
                raise ValueError("找不到車手數據：analysis.drivers")
            
            # 提取每位車手的 Lap 數據
            self.raw_lap_data = self._extract_lap_data(drivers)
            
            # 計算平均 Pedal State 比例（應用過濾）
            self.driver_pedal_data = self._calculate_average_pedal_states(self.raw_lap_data)
            
            # 返回處理後的數據
            processed_data = {
                'driver_pedal_data': self.driver_pedal_data,
                'raw_lap_data': self.raw_lap_data,
                'metadata': data.get('metadata', {})
            }
            
            # 添加數據來源元數據
            metadata = processed_data.setdefault("metadata", {})
            if self._last_data_source:
                metadata["data_source"] = self._last_data_source
            if self._last_data_source == "api" and self._last_api_meta:
                metadata["api"] = self._last_api_meta
            
            self._debug(f"成功處理 {len(self.driver_pedal_data)} 位車手的 Pedal State 數據")
            
            return processed_data
            
        except Exception as e:
            self._debug(f"數據處理失敗: {str(e)}")
            raise
    
    def _extract_lap_data(self, drivers) -> Dict[str, List[Dict]]:
        """
        從 Function 54 數據中提取每位車手的 Lap 數據
        
        注意：drivers 可能是 list（API 格式）或 dict（舊格式）
        """
        raw_lap_data = {}
        
        # 處理 list 格式（Function 54 標準輸出格式）
        if isinstance(drivers, list):
            for driver_obj in drivers:
                if not isinstance(driver_obj, dict):
                    continue
                
                driver_code = driver_obj.get('driver_code')
                if not driver_code:
                    continue
                
                laps = driver_obj.get('laps', [])
                if not isinstance(laps, list):
                    continue
                
                raw_lap_data[driver_code] = laps
        
        # 處理 dict 格式（後備相容）
        elif isinstance(drivers, dict):
            for driver_code, driver_data in drivers.items():
                if not isinstance(driver_data, dict):
                    continue
                
                laps = driver_data.get('laps', [])
                if not isinstance(laps, list):
                    continue
                
                raw_lap_data[driver_code] = laps
        
        self._debug(f"已提取 {len(raw_lap_data)} 位車手的圈數數據")
        return raw_lap_data
    
    def _calculate_average_pedal_states(self, raw_lap_data: Dict[str, List[Dict]]) -> Dict[str, Dict[str, float]]:
        """計算每位車手的平均 Pedal State 比例（應用過濾）"""
        driver_pedal_data = {}
        
        for driver_code, laps in raw_lap_data.items():
            # 過濾圈數
            filtered_laps = self._filter_laps(laps)
            
            if not filtered_laps:
                logger.debug(f"[PEDAL_DATA_MGR] {driver_code}: 沒有有效圈數（全被過濾）")
                continue
            
            # 累加 Pedal State 比例
            total_throttle_only = 0.0
            total_brake_only = 0.0
            total_trail_braking = 0.0
            total_coasting = 0.0
            valid_lap_count = 0
            
            for lap in filtered_laps:
                pedal_states = lap.get('pedal_states', {})
                if not pedal_states:
                    continue
                
                total_throttle_only += pedal_states.get('throttle_only_ratio', 0.0)
                total_brake_only += pedal_states.get('brake_only_ratio', 0.0)
                total_trail_braking += pedal_states.get('trail_braking_ratio', 0.0)
                total_coasting += pedal_states.get('coasting_ratio', 0.0)
                valid_lap_count += 1
            
            if valid_lap_count == 0:
                continue
            
            # 計算平均值
            driver_pedal_data[driver_code] = {
                'throttle_only': total_throttle_only / valid_lap_count,
                'brake_only': total_brake_only / valid_lap_count,
                'trail_braking': total_trail_braking / valid_lap_count,
                'coasting': total_coasting / valid_lap_count,
                'valid_lap_count': valid_lap_count
            }
            
            logger.debug(f"[PEDAL_DATA_MGR] {driver_code}: {valid_lap_count} valid laps, "
                        f"throttle={driver_pedal_data[driver_code]['throttle_only']:.2%}")
        
        return driver_pedal_data
    
    def _filter_laps(self, laps: List[Dict]) -> List[Dict]:
        """根據過濾設定過濾圈數"""
        filtered = []
        
        for lap in laps:
            # 過濾進站圈
            if self.filter_settings['filter_pit_laps']:
                if lap.get('is_pit_lap', False):
                    continue
            
            # 過濾黃旗圈
            if self.filter_settings['filter_yellow_flags']:
                smart_markers = lap.get('smart_markers', {})
                if smart_markers.get('yellow_flag', False):
                    continue
            
            # 過濾紅旗圈
            if self.filter_settings['filter_red_flags']:
                smart_markers = lap.get('smart_markers', {})
                if smart_markers.get('red_flag', False):
                    continue
            
            # 過濾安全車圈
            if self.filter_settings['filter_safety_car']:
                smart_markers = lap.get('smart_markers', {})
                if smart_markers.get('safety_car', False):
                    continue
            
            # 過濾 VSC 圈
            if self.filter_settings['filter_vsc']:
                smart_markers = lap.get('smart_markers', {})
                if smart_markers.get('vsc', False):
                    continue
            
            filtered.append(lap)
        
        return filtered
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 通過 CLI 生成數據
        
        API-ONLY 模式: 此方法已禁用，系統只允許通過 API 獲取數據
        """
        self._debug("[API-ONLY] CLI 調用已禁用")
        self._debug("提示: 請使用 API 獲取 Pedal Behavior 數據")
        return False
    
    # ========== 公開 API ==========
    
    def get_raw_data(self) -> Optional[Dict]:
        """獲取原始數據（供 Stint Selector 使用）"""
        return self._raw_data_cache
    
    def get_driver_pedal_data(self) -> Dict[str, Dict[str, float]]:
        """獲取處理後的車手 Pedal State 數據"""
        return self.driver_pedal_data
    
    def get_raw_lap_data(self) -> Dict[str, List[Dict]]:
        """獲取原始 Lap 數據"""
        return self.raw_lap_data
    
    def get_processed_data(self) -> Optional[Dict[str, Any]]:
        """獲取處理後的數據"""
        if not self.driver_pedal_data:
            return None
        return {
            'driver_pedal_data': self.driver_pedal_data,
            'raw_lap_data': self.raw_lap_data,
            'metadata': getattr(self, '_raw_data_cache', {}).get('metadata', {}) if self._raw_data_cache else {}
        }
