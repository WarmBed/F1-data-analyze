#!/usr/bin/env python3
"""
全車手彎道性能數據載入器
Corner Performance Data Loader for All Drivers

基於 UniversalDataLoader 實現 API-first 數據載入
支援 Function 47 的 JSON 數據格式

作者: F1T Team
日期: 2025-10-26
版本: 1.0.0
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

import certifi
import requests
from PyQt5.QtCore import QThread, pyqtSignal

from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader

logger = get_logger(component="gui")

class CornerPerformanceApiWorker(QThread):
    """
    全車手彎道性能 API 請求工作執行緒
    
    ✅ 修復 GUI 阻塞問題：使用 QThread 在背景執行緒執行 API 請求
    參考實現：IdealLapRankingApiWorker
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, payload: Dict[str, Any], endpoint: str, timeout: float = 45.0):
        """
        初始化 API Worker
        
        Args:
            payload: API 請求 payload (function_id, year, race, session)
            endpoint: API 端點 URL
            timeout: 請求超時時間（秒）
        """
        super().__init__()
        self.payload = dict(payload)
        self.endpoint = endpoint
        self.timeout = timeout
    
    def run(self):
        """✅ 在背景執行緒執行 API 請求"""
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            self.progress.emit(20)
            
            logger.info(f"[CORNER_API_WORKER] 🌐 調用 API: {self.endpoint}")
            logger.info(f"[CORNER_API_WORKER] 📋 Query Params: {self.payload}")
            
            # ✅ 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                return
            
            # ✅ 使用 query parameters（與 Ideal Lap Ranking 一致）
            start_ts = time.perf_counter()
            response = requests.post(
                self.endpoint,
                params=self.payload,  # ✅ 使用 params 而非 json
                timeout=self.timeout,
                headers={"Accept": "application/json"},  # ✅ 修改 header
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
            )
            self.progress.emit(70)
            
            # ✅ 中斷檢查點 3: HTTP 請求後
            if self.isInterruptionRequested():
                return
            
            # 檢查 HTTP 狀態
            response.raise_for_status()  # ✅ 使用 raise_for_status()
            
            # 解析 JSON 回應
            api_response = response.json()
            if not isinstance(api_response, dict):
                raise ValueError("API 回應必須是 JSON 物件")
            
            if not api_response.get("success", False):
                error_msg = api_response.get("message", "API 返回 success=False")
                raise RuntimeError(error_msg)
            
            # 提取數據
            data = api_response.get("data")
            if not isinstance(data, dict):
                raise ValueError("API 回應缺少 'data' 物件")
            
            # 計算延遲
            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            
            # 構建元數據
            meta = {
                "source": api_response.get("source", "api"),
                "execution_time": api_response.get("execution_time"),
                "request_id": api_response.get("request_id"),
                "timestamp": api_response.get("timestamp"),
                "function_spec": api_response.get("function_spec"),
                "latency_ms": round(latency_ms, 2),
                "endpoint": self.endpoint,
            }
            
            logger.info("[CORNER_API_WORKER] ✅ API 調用成功")
            logger.info(f"[CORNER_API_WORKER] ⏱️  延遲: {meta['latency_ms']}ms")
            
            self.progress.emit(90)
            # ✅ 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                return
            # ✅ 通過信號將結果返回主線程
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API 請求失敗: {str(exc)}"
            logger.error(f"[CORNER_API_WORKER] ❌ {error_msg}")
            logger.exception(exc)
            # ✅ 通過信號發送錯誤訊息
            self.failure.emit(error_msg)
        finally:
            # ✅ 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class CornerPerformanceDataLoader(UniversalDataLoader):
    """
    統一的彎道性能數據載入器（Function 120）
    
    ⚠️ API-ONLY 模式：
    - 僅通過 API 獲取數據
    - 禁用本地 JSON 檔案讀取
    - 數據格式驗證
    - 過濾旗標支援 (entry_filtered, exit_filtered)
    - 錯誤處理
    """

    ANALYSIS_TYPE = "corner_performance"

    def __init__(self, parent=None):
        """初始化數據載入器"""
        config = AnalysisConfig(
            display_name=tr("corner_performance_analysis", "彎道性能分析"),
            debug_prefix="CORNER_PERF",
            data_source="api",  # ✅ 改為 API 模式
            cli_function="120",
            file_patterns=[
                "F120_corner_all_laps_analysis_*.json",
                "corner_all_laps_analysis_*.json"
            ],
        )

        if self.ANALYSIS_TYPE not in self.ANALYSIS_TYPES:
            self.register_analysis_type(self.ANALYSIS_TYPE, config)

        super().__init__(self.ANALYSIS_TYPE, parent)

        # ✅ API-ONLY 模式：停用本地 JSON 後備
        self._allow_local_fallback = False
        self._debug("[CORNER_PERF] ⚠️ API-ONLY 模式已啟用，禁用本地 JSON 讀取")

        self._api_base_url = self._determine_api_base_url()
        self._api_timeout = 45.0
        self._last_api_payload: Optional[Dict[str, Any]] = None
        self._api_worker: Optional[CornerPerformanceApiWorker] = None  # ✅ API Worker 實例

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_data(self, **kwargs) -> bool:  # type: ignore[override]
        """
        載入彎道性能數據（API-ONLY 模式）
        
        ⚠️ 強制使用 API 獲取數據，禁用本地 JSON 讀取
        
        流程：
        1. 驗證參數
        2. 直接透過 API 獲取（異步）
        3. 處理並驗證數據
        
        Args:
            **kwargs: 載入參數（year, race, session）
            
        Returns:
            bool: 載入成功返回 True
        """
        if not self._validate_load_parameters(kwargs):
            self._error(tr("corner_perf_load_param_validation_failed", "載入參數驗證失敗"))
            self.load_error.emit(tr("corner_perf_load_param_invalid", "載入參數不正確"))
            return False

        # ✅ API-ONLY 模式：直接調用 API，不檢查本地 JSON
        self._debug(tr("corner_perf_api_only_mode", "⚠️ API-ONLY 模式：強制通過 API 獲取最新資料"))
        self._fetch_via_api_async(**kwargs)
        return True  # 立即返回，不阻塞

    # ------------------------------------------------------------------
    # UniversalDataLoader contract
    # ------------------------------------------------------------------

    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """
        驗證載入參數
        
        必須包含：year, race, session
        """
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")

        if not all([year, race, session]):
            self._error(f"缺少必要參數: year={year}, race={race}, session={session}")
            return False

        return True

    def _validate_data_format(self, raw_data: Any) -> bool:
        """
        驗證 Function 120 JSON 數據格式
        
        必須包含：
        - success: True
        - selected_corners: {low_speed, mid_speed, high_speed}
        - mode_a_unified: {drivers: [...]}
        
        每個車手的 corners 中應包含 entry_filtered, exit_filtered 過濾旗標
        """
        if not isinstance(raw_data, dict):
            self._error("數據不是字典格式")
            return False

        # 檢查必要欄位
        if not raw_data.get("success"):
            self._error("數據標記為失敗 (success: false)")
            return False

        # F120 結構檢查
        if "mode_a_unified" in raw_data:
            # F120 格式
            mode_a = raw_data["mode_a_unified"]
            if "drivers" not in mode_a or not isinstance(mode_a["drivers"], list):
                self._error("mode_a_unified.drivers 不是列表")
                return False
            
            # 檢查 selected_corners
            if "selected_corners" not in raw_data:
                self._error("缺少 selected_corners")
                return False
            
            self._debug("F120 數據格式驗證通過")
            return True
        
        # 兼容舊版 F47 格式
        elif "fastest_lap_analysis" in raw_data:
            self._debug("⚠️ 偵測到舊版 F47 格式數據")
            required_keys = ["selected_corners", "fastest_lap_analysis"]
            for key in required_keys:
                if key not in raw_data:
                    self._error(f"缺少必要欄位: {key}")
                    return False
            
            self._debug("F47 數據格式驗證通過 (兼容模式)")
            return True
        
        else:
            self._error("無法識別的數據格式 (非 F120 也非 F47)")
            return False

    def _process_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理原始數據
        
        F120 格式轉換為前端友好的格式，包含過濾旗標支援
        """
        try:
            # 判斷數據格式
            is_f120 = "mode_a_unified" in raw_data
            
            if is_f120:
                # F120 格式處理
                mode_a = raw_data["mode_a_unified"]
                drivers_data = mode_a.get("drivers", [])
                
                # 轉換為 GUI 兼容格式 (模擬 fastest_lap_analysis 結構)
                converted_drivers = []
                for driver_info in drivers_data:
                    driver = driver_info.get("driver", "")
                    corners = driver_info.get("corners", {})
                    
                    # 轉換彎道數據格式
                    converted_corners = {}
                    for corner_key, corner_data in corners.items():
                        converted_corners[corner_key] = {
                            # GUI 使用的欄位 (來自 F120 的 GUI 相容欄位)
                            "entry_50m_speed": corner_data.get("entry_50m_speed", corner_data.get("entry_speed_median", 0)),
                            "exit_50m_speed": corner_data.get("exit_50m_speed", corner_data.get("exit_speed_median", 0)),
                            "apex_speed": corner_data.get("apex_speed", corner_data.get("median_speed", 0)),
                            # 過濾旗標 (F120 新增)
                            "entry_filtered": corner_data.get("entry_filtered", False),
                            "exit_filtered": corner_data.get("exit_filtered", False),
                            # 保留原始統計數據
                            "median_speed": corner_data.get("median_speed", 0),
                            "entry_speed_median": corner_data.get("entry_speed_median", 0),
                            "exit_speed_median": corner_data.get("exit_speed_median", 0),
                        }
                    
                    converted_drivers.append({
                        "driver": driver,
                        "corners": converted_corners
                    })
                
                # 檢查並傳遞 stint 數據
                stints_available = raw_data.get("stints_available", False)
                
                processed = {
                    "success": True,
                    "year": raw_data.get("year"),
                    "race": raw_data.get("race"),
                    "session": raw_data.get("session"),
                    "data_source": "F120",
                    "selected_corners": raw_data.get("selected_corners", {}),
                    "fastest_lap_analysis": {
                        "total_drivers": len(converted_drivers),
                        "drivers": converted_drivers
                    },
                    "mode_a_unified": raw_data.get("mode_a_unified"),
                    "mode_b_grouped": raw_data.get("mode_b_grouped"),
                    "stints_available": stints_available,  # 傳遞 stint 可用性標記
                    "raw_data": raw_data
                }
                
                self._debug(f"F120 數據處理完成: {len(converted_drivers)} 位車手, stints_available={stints_available}")
                
            else:
                # F47 兼容模式 (舊版數據)
                self._debug("⚠️ 使用 F47 兼容模式處理數據")
                processed = {
                    "success": True,
                    "year": raw_data.get("year"),
                    "race": raw_data.get("race"),
                    "session": raw_data.get("session"),
                    "data_source": "F47",
                    "selected_corners": raw_data.get("selected_corners", {}),
                    "fastest_lap_analysis": raw_data.get("fastest_lap_analysis", {}),
                    "all_laps_analysis": raw_data.get("all_laps_analysis", {}),
                    "raw_data": raw_data
                }
                
                drivers_count = len(processed.get("fastest_lap_analysis", {}).get("drivers", []))
                self._debug(f"F47 數據處理完成: {drivers_count} 位車手")
            
            return processed

        except Exception as e:
            self._error(f"處理數據時發生錯誤: {e}")
            raise

    # ------------------------------------------------------------------
    # Async API Methods (✅ 修復 GUI 阻塞)
    # ------------------------------------------------------------------

    def _fetch_via_api_async(self, **kwargs):
        """
        ✅ 異步 API 請求（不阻塞主 GUI）
        
        使用 CornerPerformanceApiWorker 在背景執行緒執行 API 請求
        """
        year = kwargs.get("year")
        race = kwargs.get("race")
        session = kwargs.get("session")

        # ✅ 使用新版 API 端點（與 Ideal Lap Ranking 一致）
        endpoint = f"{self._api_base_url}/api/v2/analysis/execute"
        
        # ✅ 使用 query parameters（不是 POST body）
        payload = {
            "function_id": 120,  # ✅ 整數格式（不是字串）
            "year": int(year),
            "race": race,
            "session": session,
        }

        self.status_changed.emit(tr("corner_perf_fetching_api", "正在從 API 獲取彎道性能數據..."))
        self.load_progress.emit(10)

        # ✅ 創建並啟動 API Worker
        self._api_worker = CornerPerformanceApiWorker(
            payload,
            endpoint,
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
            result: {"data": API數據, "meta": 元數據}
        """
        data = result.get("data")
        meta = result.get("meta", {})
        
        self._debug(f"✅ API 調用成功，延遲: {meta.get('latency_ms')}ms")
        self._last_api_payload = data

        try:
            # 驗證數據格式
            if not self._validate_data_format(data):
                self._error("API 返回的數據格式驗證失敗")
                self.load_error.emit(tr("corner_perf_invalid_data_format", "數據格式不正確"))
                return

            # 處理數據
            processed_data = self._process_data(data)
            self._current_data = processed_data

            # 發送成功信號
            self.load_progress.emit(100)
            self.status_changed.emit(tr("corner_perf_load_success", "彎道性能數據載入完成"))
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
    # API Integration
    # ------------------------------------------------------------------

    def _determine_api_base_url(self) -> str:
        """決定 API 基礎 URL"""
        return resolve_api_base_url()

    def _fetch_via_api_and_cache(self, **kwargs) -> Optional[str]:
        """
        ⚠️ 已棄用：透過 API 獲取數據並快取（舊版同步方法）
        
        此方法已被 _fetch_via_api_async() 取代，不再使用。
        保留供參考，請勿調用。
        
        Returns:
            Optional[str]: 快取檔案路徑，失敗返回 None
        """
        # ⚠️ 強制拋出錯誤，禁止使用已棄用的方法
        raise DeprecationWarning(
            "⚠️ _fetch_via_api_and_cache() 已棄用！\n"
            "請使用 _fetch_via_api_async() 方法（異步 API Worker）。\n"
            "此方法使用已棄用的 /analyze 端點，且會阻塞主 GUI。"
        )
        
        # ⚠️ 以下代碼已停用（保留供參考）
        # year = kwargs.get("year")
        # race = kwargs.get("race")
        # session = kwargs.get("session")
        #
        # endpoint = f"{self._api_base_url}/analyze"  # ⚠️ 已棄用端點
        # payload = {
        #     "function_id": "120",
        #     "year": year,
        #     "race": race,
        #     "session": session,
        # }
        #
        # self._debug(f"發送 API 請求: {endpoint}")
        # self._debug(f"Payload: {payload}")
        #
        # try:
        #     self.status_changed.emit(tr("corner_perf_fetching_api", "正在從 API 獲取彎道性能數據..."))
        #
        #     response = requests.post(
        #         endpoint,
        #         json=payload,
        #         timeout=self._api_timeout,
        #         headers={"Content-Type": "application/json"}
        #     )
        #
        #     if response.status_code == 200:
        #         api_response = response.json()
        #         
        #         if not api_response.get("success"):
        #             error_msg = api_response.get("message", "未知錯誤")
        #             self._error(f"API 返回失敗: {error_msg}")
        #             return None
        #
        #         # 提取數據
        #         data = api_response.get("data", {})
        #         if not data:
        #             self._error("API 返回的數據為空")
        #             return None
        #
        #         # 儲存到快取
        #         self._last_api_payload = data
        #         
        #         # 寫入檔案
        #         cache_file = self._write_cache_file(data, **kwargs)
        #         
        #         return cache_file
        #
        #     else:
        #         self._error(f"API 請求失敗: HTTP {response.status_code}")
        #         return None
        #
        # except requests.Timeout:
        #     self._error(f"API 請求超時 ({self._api_timeout}s)")
        #     return None
        # except Exception as e:
        #     self._error(f"API 請求發生錯誤: {e}")
        #     import traceback
        #     traceback.print_exc()
        #     return None

    def _write_cache_file(self, data: Dict[str, Any], **kwargs) -> Optional[str]:
        """
        將數據寫入快取檔案
        
        Returns:
            Optional[str]: 快取檔案路徑
        """
        try:
            year = kwargs.get("year")
            race = kwargs.get("race")
            session = kwargs.get("session")

            cache_dir = os.path.join(os.getcwd(), "json")
            os.makedirs(cache_dir, exist_ok=True)

            filename = f"all_drivers_cornering_analysis_{year}_{race}_{session}.json"
            filepath = os.path.join(cache_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._debug(f"數據已儲存至: {filepath}")
            return filepath

        except Exception as e:
            self._error(f"寫入快取檔案失敗: {e}")
            return None
