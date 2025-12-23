#!/usr/bin/env python3
"""
全車手加速度圖表資料載入器
All Drivers Acceleration Chart Data Loader

呼叫 F121 API 獲取全圈數直線速度統計數據
用於速度-加速度圖表視覺化

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests
from PyQt5.QtCore import QThread, pyqtSignal, QObject

from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger("acceleration_chart_loader", component="gui")


class AccelerationChartApiWorker(QThread):
    """
    加速度圖表 API 請求工作執行緒
    
    呼叫 F121 API 在背景執行緒執行，避免 GUI 阻塞
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
            timeout: 請求超時時間（秒）
        """
        super().__init__()
        self.params = dict(params)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def run(self):
        """在背景執行緒執行 API 請求"""
        try:
            if self.isInterruptionRequested():
                logger.debug("[ACCEL_CHART_API] 啟動前已被請求中斷")
                return
                
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            logger.info(f"[ACCEL_CHART_API] 調用 API: {endpoint}")
            logger.info(f"[ACCEL_CHART_API] 參數: {self.params}")
            
            if self.isInterruptionRequested():
                return
                
            # 發送 POST 請求
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=self.params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            
            if self.isInterruptionRequested():
                return
                
            self.progress.emit(70)
            
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
            
            # 添加元數據
            payload["_metadata"] = {
                "source": "api",
                "latency_ms": latency_ms,
                "timestamp": time.time()
            }
            
            self.progress.emit(100)
            logger.info(f"[ACCEL_CHART_API] API 請求成功，延遲: {latency_ms:.1f}ms")
            self.success.emit(payload)
            
        except requests.exceptions.Timeout:
            error_msg = f"API 請求超時 ({self.timeout}s)"
            logger.error(f"[ACCEL_CHART_API] {error_msg}")
            self.failure.emit(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"無法連接到 API 服務器: {e}"
            logger.error(f"[ACCEL_CHART_API] {error_msg}")
            self.failure.emit(error_msg)
            
        except Exception as e:
            error_msg = f"API 請求失敗: {e}"
            logger.exception(f"[ACCEL_CHART_API] {error_msg}")
            self.failure.emit(error_msg)


class AccelerationChartDataLoader(QObject):
    """
    加速度圖表資料載入器
    
    負責：
    1. 呼叫 F121 API 獲取數據
    2. 轉換數據格式供圖表使用
    """
    
    # 信號
    data_loaded = pyqtSignal(dict)      # 數據載入成功
    load_error = pyqtSignal(str)        # 載入錯誤
    status_changed = pyqtSignal(str)    # 狀態變更
    progress_updated = pyqtSignal(int)  # 進度更新
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._api_worker: Optional[AccelerationChartApiWorker] = None
        self._current_params: Dict[str, Any] = {}
        self._cached_data: Optional[Dict[str, Any]] = None
    
    def load_data(self, year: int, race: str, session: str, force_refresh: bool = False):
        """
        載入加速度圖表數據
        
        API-ONLY 模式: 僅使用 API，不使用本地 JSON
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型 (FP1/FP2/FP3/Q/R)
            force_refresh: 保留參數以保持介面一致性（無作用）
        """
        self._current_params = {
            "function_id": "121",
            "year": year,
            "race": race,
            "session": session
        }
        
        logger.info(f"[ACCEL_CHART_LOADER] 載入數據: {year} {race} {session}")
        logger.info("[ACCEL_CHART_LOADER] API-ONLY 模式: 僅調用 API")
        self.status_changed.emit(tr("Loading data..."))
        
        # 直接調用 API
        self._start_api_request()
    
    def _start_api_request(self):
        """啟動 API 請求"""
        # 取消現有請求
        if self._api_worker and self._api_worker.isRunning():
            self._api_worker.requestInterruption()
            self._api_worker.wait(1000)
        
        # 獲取 API 基礎 URL
        base_url = resolve_api_base_url()
        
        # 創建並啟動 worker
        self._api_worker = AccelerationChartApiWorker(
            params=self._current_params,
            base_url=base_url,
            timeout=60.0
        )
        
        # 連接信號
        self._api_worker.progress.connect(self._on_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_failure)
        
        self._api_worker.start()
    
    def _on_progress(self, value: int):
        """進度更新回調"""
        self.progress_updated.emit(value)
    
    def _on_api_success(self, data: Dict[str, Any]):
        """API 成功回調"""
        logger.info("[ACCEL_CHART_LOADER] API 數據載入成功")
        self._cached_data = data
        self.status_changed.emit(tr("Data loaded successfully"))
        self.data_loaded.emit(data)
    
    def _on_api_failure(self, error: str):
        """API 失敗回調"""
        logger.error(f"[ACCEL_CHART_LOADER] API 失敗: {error}")
        self.status_changed.emit(tr("Load failed"))
        self.load_error.emit(error)
    
    def get_cached_data(self) -> Optional[Dict[str, Any]]:
        """獲取快取的數據"""
        return self._cached_data
    
    def cancel(self):
        """取消載入"""
        if self._api_worker and self._api_worker.isRunning():
            self._api_worker.requestInterruption()
            self._api_worker.wait(2000)
