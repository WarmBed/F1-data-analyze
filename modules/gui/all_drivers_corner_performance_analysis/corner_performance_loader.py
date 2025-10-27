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

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader


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
            self.progress.emit(20)
            
            print(f"[CORNER_API_WORKER] 🌐 調用 API: {self.endpoint}")
            print(f"[CORNER_API_WORKER] 📋 Payload: {self.payload}")
            
            # ✅ 在背景執行緒發送 POST 請求（不阻塞主 GUI）
            start_ts = time.perf_counter()
            response = requests.post(
                self.endpoint,
                json=self.payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            self.progress.emit(70)
            
            # 檢查 HTTP 狀態
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}")
            
            # 解析 JSON 回應
            api_response = response.json()
            if not isinstance(api_response, dict):
                raise ValueError("API 回應必須是 JSON 物件")
            
            if not api_response.get("success"):
                error_msg = api_response.get("message", "API 返回 success=False")
                raise RuntimeError(error_msg)
            
            # 提取數據
            data = api_response.get("data", {})
            if not data:
                raise ValueError("API 返回的數據為空")
            
            # 計算延遲
            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            
            # 構建元數據
            meta = {
                "source": "api",
                "latency_ms": round(latency_ms, 2),
                "endpoint": self.endpoint,
            }
            
            print(f"[CORNER_API_WORKER] ✅ API 調用成功")
            print(f"[CORNER_API_WORKER] ⏱️  延遲: {meta['latency_ms']}ms")
            
            self.progress.emit(90)
            # ✅ 通過信號將結果返回主線程
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            error_msg = f"API 請求失敗: {str(exc)}"
            print(f"[CORNER_API_WORKER] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            # ✅ 通過信號發送錯誤訊息
            self.failure.emit(error_msg)
        finally:
            self.progress.emit(100)


class CornerPerformanceDataLoader(UniversalDataLoader):
    """
    統一的彎道性能數據載入器（Function 47）
    
    支援：
    - API 優先載入
    - 本地 JSON 檔案讀取
    - 數據格式驗證
    - 錯誤處理
    """

    ANALYSIS_TYPE = "corner_performance"

    def __init__(self, parent=None):
        """初始化數據載入器"""
        config = AnalysisConfig(
            display_name=tr("corner_performance_analysis", "彎道性能分析"),
            debug_prefix="CORNER_PERF",
            data_source="json",
            cli_function="47",
            file_patterns=[
                "all_drivers_cornering_analysis_*.json",
                "corner_performance_*.json"
            ],
        )

        if self.ANALYSIS_TYPE not in self.ANALYSIS_TYPES:
            self.register_analysis_type(self.ANALYSIS_TYPE, config)

        super().__init__(self.ANALYSIS_TYPE, parent)

        self._api_base_url = self._determine_api_base_url()
        self._api_timeout = 45.0
        self._last_api_payload: Optional[Dict[str, Any]] = None
        self._api_worker: Optional[CornerPerformanceApiWorker] = None  # ✅ API Worker 實例

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_data(self, **kwargs) -> bool:  # type: ignore[override]
        """
        載入彎道性能數據
        
        優先順序：
        1. 檢查本地 JSON 檔案
        2. 如果沒有本地檔案，透過 API 獲取（異步）
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

        existing = self._find_data_file(**kwargs)
        if not existing:
            self._debug(tr("corner_perf_no_local_file", "找不到本地彎道性能檔案，準備透過 API 取得最新資料"))
            # ✅ 修復：使用異步 API Worker（不阻塞主 GUI）
            self._fetch_via_api_async(**kwargs)
            return True  # 立即返回，不阻塞

        return super().load_data(**kwargs)

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
        驗證 Function 47 JSON 數據格式
        
        必須包含：
        - success: True
        - selected_corners: {low_speed, mid_speed, high_speed}
        - fastest_lap_analysis: {total_drivers, drivers}
        - all_laps_analysis: {total_drivers, drivers}
        """
        if not isinstance(raw_data, dict):
            self._error("數據不是字典格式")
            return False

        # 檢查必要欄位
        if not raw_data.get("success"):
            self._error("數據標記為失敗 (success: false)")
            return False

        required_keys = ["selected_corners", "fastest_lap_analysis", "all_laps_analysis"]
        for key in required_keys:
            if key not in raw_data:
                self._error(f"缺少必要欄位: {key}")
                return False

        # 檢查 selected_corners 結構
        corners = raw_data["selected_corners"]
        corner_types = ["low_speed", "mid_speed", "high_speed"]
        for corner_type in corner_types:
            if corner_type not in corners:
                self._error(f"缺少彎道類型: {corner_type}")
                return False
            
            corner_data = corners[corner_type]
            if not isinstance(corner_data, dict):
                self._error(f"{corner_type} 不是字典格式")
                return False
            
            # 檢查彎道數據欄位
            required_corner_keys = ["corner_number", "apex_distance", "avg_apex_speed"]
            for key in required_corner_keys:
                if key not in corner_data:
                    self._error(f"{corner_type} 缺少欄位: {key}")
                    return False

        # 檢查 fastest_lap_analysis 結構
        fastest = raw_data["fastest_lap_analysis"]
        if "drivers" not in fastest or not isinstance(fastest["drivers"], list):
            self._error("fastest_lap_analysis.drivers 不是列表")
            return False

        # 檢查 all_laps_analysis 結構
        all_laps = raw_data["all_laps_analysis"]
        if "drivers" not in all_laps or not isinstance(all_laps["drivers"], list):
            self._error("all_laps_analysis.drivers 不是列表")
            return False

        self._debug("數據格式驗證通過")
        return True

    def _process_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理原始數據
        
        轉換為前端友好的格式
        """
        try:
            processed = {
                "success": True,
                "year": raw_data.get("year"),
                "race": raw_data.get("race"),
                "session": raw_data.get("session"),
                "selected_corners": raw_data["selected_corners"],
                "fastest_lap_analysis": raw_data["fastest_lap_analysis"],
                "all_laps_analysis": raw_data["all_laps_analysis"],
                "raw_data": raw_data  # 保留原始數據
            }

            self._debug(f"數據處理完成: {len(processed['fastest_lap_analysis']['drivers'])} 位車手")
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

        endpoint = f"{self._api_base_url}/analyze"
        payload = {
            "function_id": "47",
            "year": year,
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
        透過 API 獲取數據並快取
        
        Returns:
            Optional[str]: 快取檔案路徑，失敗返回 None
        """
        year = kwargs.get("year")
        race = kwargs.get("race")
        session = kwargs.get("session")

        endpoint = f"{self._api_base_url}/analyze"
        payload = {
            "function_id": "47",
            "year": year,
            "race": race,
            "session": session,
        }

        self._debug(f"發送 API 請求: {endpoint}")
        self._debug(f"Payload: {payload}")

        try:
            self.status_changed.emit(tr("corner_perf_fetching_api", "正在從 API 獲取彎道性能數據..."))

            response = requests.post(
                endpoint,
                json=payload,
                timeout=self._api_timeout,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                api_response = response.json()
                
                if not api_response.get("success"):
                    error_msg = api_response.get("message", "未知錯誤")
                    self._error(f"API 返回失敗: {error_msg}")
                    return None

                # 提取數據
                data = api_response.get("data", {})
                if not data:
                    self._error("API 返回的數據為空")
                    return None

                # 儲存到快取
                self._last_api_payload = data
                
                # 寫入檔案
                cache_file = self._write_cache_file(data, **kwargs)
                
                return cache_file

            else:
                self._error(f"API 請求失敗: HTTP {response.status_code}")
                return None

        except requests.Timeout:
            self._error(f"API 請求超時 ({self._api_timeout}s)")
            return None
        except Exception as e:
            self._error(f"API 請求發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None

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
