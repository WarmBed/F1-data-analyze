#!/usr/bin/env python3
"""
全車手煞車圖表資料載入器
All Drivers Brake Chart Data Loader

呼叫 F122 API 獲取煞車性能全圈數統計數據
用於煞車前速度-減速度圖表視覺化

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from core import local_requests as requests
import certifi
from PyQt5.QtCore import QThread, pyqtSignal, QObject

from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger("brake_chart_loader", component="gui")


class BrakeChartApiWorker(QThread):
    """
    煞車圖表 API 請求工作執行緒
    
    呼叫 F122 API 在背景執行緒執行，避免 GUI 阻塞
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, params: Dict[str, Any], base_url: str, timeout: float = 90.0):
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
                logger.debug("[BRAKE_CHART_API] 啟動前已被請求中斷")
                return
                
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            logger.info(f"[BRAKE_CHART_API] 調用 API: {endpoint}")
            logger.info(f"[BRAKE_CHART_API] 參數: {self.params}")
            
            if self.isInterruptionRequested():
                return
                
            # 發送 POST 請求
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=self.params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
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
            logger.info(f"[BRAKE_CHART_API] API 請求成功，延遲: {latency_ms:.1f}ms")
            self.success.emit(payload)
            
        except requests.exceptions.Timeout:
            error_msg = f"API 請求超時 ({self.timeout}s)"
            logger.error(f"[BRAKE_CHART_API] {error_msg}")
            self.failure.emit(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"無法連接到 API 服務器: {e}"
            logger.error(f"[BRAKE_CHART_API] {error_msg}")
            self.failure.emit(error_msg)
            
        except Exception as e:
            error_msg = f"API 請求失敗: {e}"
            logger.exception(f"[BRAKE_CHART_API] {error_msg}")
            self.failure.emit(error_msg)


class BrakeChartDataLoader(QObject):
    """
    煞車圖表資料載入器
    
    負責：
    1. 呼叫 F122 API 獲取數據
    2. 轉換數據格式供圖表使用
    """
    
    # 信號
    data_loaded = pyqtSignal(dict)      # 數據載入成功
    load_error = pyqtSignal(str)        # 載入錯誤
    status_changed = pyqtSignal(str)    # 狀態變更
    progress_updated = pyqtSignal(int)  # 進度更新
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._api_worker: Optional[BrakeChartApiWorker] = None
        self._current_params: Dict[str, Any] = {}
        self._cached_data: Optional[Dict[str, Any]] = None
    
    def load_data(self, year: int, race: str, session: str, force_refresh: bool = False):
        """
        載入煞車分析數據
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型 (R, Q, FP1, FP2, FP3)
            force_refresh: 是否強制刷新（忽略緩存）
        """
        logger.info(f"[BRAKE_CHART_LOADER] 載入數據: {year} {race} {session}")
        logger.info("[BRAKE_CHART_LOADER] API-ONLY 模式: 僅調用 API")
        
        # 構建請求參數
        self._current_params = {
            "function_id": "122",  # F122 煞車性能全圈數分析
            "year": str(year),
            "race": race,
            "session": session
        }
        
        # 更新狀態
        self.status_changed.emit(tr("loading_data", "Loading data..."))
        
        # 啟動 API Worker
        self._start_api_worker()
    
    def _start_api_worker(self):
        """啟動 API 工作執行緒"""
        # 停止現有的 worker
        self._stop_current_worker()
        
        # 解析 API base URL
        base_url = resolve_api_base_url()
        logger.info(f"[BRAKE_CHART_LOADER] API Base URL: {base_url}")
        
        # 創建新 worker
        self._api_worker = BrakeChartApiWorker(
            params=self._current_params,
            base_url=base_url,
            timeout=90.0  # F122 可能需要較長時間
        )
        
        # 連接信號
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_failure)
        self._api_worker.progress.connect(self.progress_updated.emit)
        
        # 啟動
        self._api_worker.start()
    
    def _stop_current_worker(self):
        """停止當前的 worker"""
        if self._api_worker and self._api_worker.isRunning():
            self._api_worker.requestInterruption()
            self._api_worker.wait(3000)  # 等待最多 3 秒
    
    def _on_api_success(self, payload: Dict[str, Any]):
        """API 請求成功
        
        API 返回格式: {"success": true, "data": {...actual_data...}, ...}
        此方法提取 data 欄位傳遞給 MDI
        """
        logger.info("[BRAKE_CHART_LOADER] API 數據載入成功")
        
        # 提取實際數據 (API wrapper 中的 data 欄位)
        # 2025-01-19: 修復 - API 返回 {success, data: {...}} 結構
        actual_data = payload.get("data", payload)
        
        # 確保 drivers 存在
        if "drivers" not in actual_data and "drivers" in payload:
            actual_data = payload
        
        # 緩存數據
        self._cached_data = actual_data
        
        # 更新狀態
        self.status_changed.emit(tr("data_loaded", "Data loaded"))
        
        # 發送數據
        self.data_loaded.emit(actual_data)
    
    def _on_api_failure(self, error_msg: str):
        """API 請求失敗"""
        logger.error(f"[BRAKE_CHART_LOADER] API 失敗: {error_msg}")
        self.status_changed.emit(tr("load_failed", "Load failed"))
        self.load_error.emit(error_msg)
    
    def cleanup(self):
        """清理資源"""
        self._stop_current_worker()
        self._cached_data = None


__all__ = ["BrakeChartDataLoader", "BrakeChartApiWorker"]
