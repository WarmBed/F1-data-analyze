#!/usr/bin/env python3
"""
Weather Timeline MDI Window

Manages weather timeline MDI window, integrating data loader and widget components

Author: F1T Team  
Date: 2025-10-13
Version: 1.0.0
"""

import logging
import sys
import time
import json
from core import local_requests as requests
import certifi
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QProgressBar, QLabel,
    QApplication, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal

from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)

logger = get_logger("weather_timeline.mdi", component="gui")


class WeatherTimelineApiWorker(QThread):
    """
    Weather Timeline API Request Worker Thread
    
    Handles async API calls to fetch weather forecast data
    API Endpoint: POST /api/v2/analysis/execute?function_id=96
    """
    
    # Signals
    progress = pyqtSignal(int)  # Progress (0-100)
    success = pyqtSignal(dict)  # Success (returns data)
    failure = pyqtSignal(str)   # Failure (error message)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        """
        Initialize API Worker
        
        Args:
            params: API parameters (year, event, etc.)
            base_url: API base URL (default: http://localhost:8000)
            timeout: Request timeout (seconds)
        """
        super().__init__()
        self.base_url = (base_url or "http://localhost:8000").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        """Execute API request"""
        try:
            # 檢查是否已被請求中斷
            if self.isInterruptionRequested():
                logger.debug("[WEATHER_API_WORKER] 啟動前已被請求中斷，跳過執行")
                return
                
            self.progress.emit(20)
            
            # Build API endpoint
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            # Build query parameters
            query_params: Dict[str, Any] = {
                "function_id": 96,  # CLI Function 96 - Race Weather Forecast
                "year": int(self.params.get("year")),
                "race": str(self.params.get("event")),
                "session": "R",  # Always use Race session for weather
            }
            
            # Force refresh (optional)
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[API_WORKER] Calling API: %s", endpoint)
                logger.debug("[API_WORKER] Parameters: %s", query_params)
            
            # 再次檢查中斷（在發送請求前）
            if self.isInterruptionRequested():
                logger.debug("[WEATHER_API_WORKER] 發送請求前被請求中斷")
                return
                
            # Send POST request
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ 明確指定 SSL 證書路徑（EXE 必須）
            )
            
            # 請求完成後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[WEATHER_API_WORKER] API 回應後被請求中斷，放棄處理結果")
                return
                
            self.progress.emit(70)
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse JSON response
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be JSON object")
            
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API returned success=False"))
            
            # Extract data
            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API response missing 'data' object")
            
            # 🔧 FIX: 檢查雙層嵌套（CLI JSON 被包在 API 的 data 裡）
            # CLI JSON 結構: {"success": true, "metadata": {...}, "data": {...}}
            # 如果 data 包含 'success' 和 'data'，則是雙層嵌套
            if 'success' in data and 'data' in data:
                logger.warning("[API_WORKER] Detected nested data payload; extracting inner data")
                data = data['data']  # 提取內層的實際數據
            
            # Calculate latency
            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            
            # 發送信號前最後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[WEATHER_API_WORKER] 發送成功信號前被請求中斷，放棄發送")
                return
                
            self.progress.emit(100)
            logger.info("[API_WORKER] Success in %.0fms", latency_ms)
            
            # Emit success signal
            self.success.emit(data)
            
        except requests.Timeout:
            # 如果被中斷，不發送失敗信號
            if self.isInterruptionRequested():
                return
            error_msg = tr("weather_api_timeout", "API 請求超時 ({timeout}s)").format(timeout=self.timeout)
            logger.error("[API_WORKER] Timeout: %s", error_msg)
            self.failure.emit(error_msg)
            
        except requests.RequestException as e:
            # 如果被中斷，不發送失敗信號
            if self.isInterruptionRequested():
                return
            error_msg = tr("weather_api_network_error", "網路錯誤: {error}").format(error=str(e))
            logger.error("[API_WORKER] Network error: %s", e)
            self.failure.emit(error_msg)
            
        except Exception as e:
            # 如果被中斷，不發送失敗信號
            if self.isInterruptionRequested():
                return
            error_msg = tr("weather_api_general_error", "API 錯誤: {error}").format(error=str(e))
            logger.error("[API_WORKER] General error: %s", e)
            self.failure.emit(error_msg)


class WeatherTimelineMDI(QWidget):
    """
    Weather Timeline MDI Window
    
    Manages weather timeline display:
    - Integrates WeatherTimelineDataLoader for data management
    - Integrates WeatherTimelineWidget for visualization
    - Handles API-ONLY mode (prioritizes API, allows local JSON fallback)
    - Shows loading progress during data fetch
    """
    
    def __init__(self, year: str, event: str, parent=None):
        """
        Initialize MDI Window
        
        Args:
            year: Season year (e.g., "2025")
            event: Event name (e.g., "United States")
            parent: Parent widget
        """
        super().__init__(parent)
        
        from .weather_timeline_data_loader import WeatherTimelineDataLoader
        from .weather_timeline_widget import WeatherTimelineWidget
        
        self.year = str(year)
        self.event = str(event)
        
        # Components
        self.data_loader = WeatherTimelineDataLoader(year, event, parent=self)
        self.widget = WeatherTimelineWidget(parent=self)
        
        # API Worker (will be created when needed)
        self.api_worker = None
        
        # UI Setup
        self._init_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Start loading data
        self._load_data()
    
    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Status bar (與 Season Progress 一致：預設隱藏)
        self.status_label = QLabel(tr("weather_loading", "Loading weather data..."), self)
        self.status_label.setStyleSheet("padding: 5px; background: #f0f0f0;")
        self.status_label.hide()  # Hide status bar by default
        layout.addWidget(self.status_label)
        
        # Progress bar (與 Season Progress 一致：預設隱藏，細條)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.hide()  # Hide progress bar by default
        layout.addWidget(self.progress_bar)
        
        # Weather widget (initially hidden)
        self.widget.setVisible(False)
        layout.addWidget(self.widget)
    
    def _connect_signals(self):
        """Connect signals"""
        # No data loader signals to connect (API-ONLY mode)
        # Signals are handled by API worker directly
        pass
    
    def _load_data(self):
        """Start loading data (API-ONLY mode)"""
        logger.info("[WEATHER_MDI] Loading data for %s %s", self.year, self.event)
        
        # ✅ API-ONLY 模式：強制使用 API，不讀取本地 JSON
        logger.info("[WEATHER_MDI] API-ONLY mode: Calling API")
        self._call_api()
    
    def _call_api(self):
        """Call API to fetch weather data"""
        logger.info("[WEATHER_MDI] Starting API request")
        
        # Create API worker
        params = {
            "year": self.year,
            "event": self.event,
            "force_refresh": False
        }
        
        self.api_worker = WeatherTimelineApiWorker(params)
        
        # Connect signals
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 🔧 與 Season Progress 完全一致：只顯示進度條，不顯示 status_label
        self.status_label.setText(tr("weather_loading_status", "Loading weather data from API..."))
        # 注意：Season Progress 不顯示 status_label，只顯示 progress_bar
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # Start worker
        self.api_worker.start()
    
    @pyqtSlot(int)
    def _on_api_progress(self, value: int):
        """API progress update (與 Season Progress 一致)"""
        logger.debug("[WEATHER_MDI] API progress: %d%%", value)
        self.progress_bar.setValue(value)
        self.status_label.setText(f"API loading... {value}%")  # 只設置文字，不顯示
    
    @pyqtSlot(dict)
    def _on_api_success(self, data: dict):
        """API request succeeded"""
        logger.info("[WEATHER_MDI] API request succeeded")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[WEATHER_MDI] Received data keys: %s", list(data.keys()))
        
        # Validate and transform data
        if self.data_loader._validate_data_format(data):
            transformed = self.data_loader._transform_data_for_display(data)
            self._on_load_completed(transformed)
        else:
            logger.error("[WEATHER_MDI] Data validation failed")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[WEATHER_MDI] Data structure: %s", json.dumps(data, indent=2)[:500])
            self._on_load_error(tr("weather_invalid_data", "API 返回的數據格式無效"))
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API request failed"""
        logger.error("[WEATHER_MDI] API request failed: %s", error_msg)
        self._on_load_error(error_msg)
    
    @pyqtSlot(dict)
    def _on_load_completed(self, data: dict):
        """Data loading completed (與 Season Progress 一致：顯示成功訊息)"""
        logger.info("[WEATHER_MDI] Data loading completed")
        
        # Show widget
        self.widget.setVisible(True)
        self.widget.populate_data(data)
        
        # 🔧 與 Season Progress 一致：顯示成功訊息
        self.status_label.setText(tr("load_success_status", "Load successful"))
        self.progress_bar.setValue(100)
        self.progress_bar.hide()
        
        logger.info("[WEATHER_MDI] Weather data displayed successfully")
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """Data loading failed - 顯示錯誤訊息而不是完全隱藏"""
        logger.error("[WEATHER_MDI] Data loading failed: %s", error_msg)
        
        # ✅ 修復：對於當前年份或未來年份，顯示友善的「賽季尚未開始」訊息
        from datetime import datetime
        year_int = int(self.year)
        current_year = datetime.now().year
        
        if year_int >= current_year:
            # 當前年份或未來年份：顯示友善訊息
            logger.info(f"[WEATHER_MDI] 當前/未來年份 {year_int}，顯示賽季尚未開始訊息")
            self.status_label.setText(tr("future_season_weather", "賽季尚未開始，天氣數據暫不可用"))
            self.status_label.setStyleSheet("""
                padding: 8px;
                background: #e7f3ff;
                color: #0066cc;
                border: 1px solid #b3d9ff;
                border-radius: 4px;
            """)
        else:
            # 過去年份：顯示一般錯誤訊息
            self.status_label.setText(tr("weather_load_failed", "天氣數據載入失敗"))
            self.status_label.setStyleSheet("""
                padding: 8px;
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeeba;
                border-radius: 4px;
            """)
        
        self.status_label.show()
        
        # Hide progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        
        # 🔧 修改：顯示 widget 並填充錯誤訊息，而不是完全隱藏
        self.widget.setVisible(True)
        self.widget.show_error_state(error_msg)
        
        logger.warning("[WEATHER_TIMELINE_MDI] Load error: %s", error_msg)


# Demo 測試
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 測試 MDI 視窗
    mdi = WeatherTimelineMDI("2025", "United States")
    mdi.setWindowTitle("Weather Timeline MDI Test")
    mdi.resize(1000, 600)
    mdi.show()
    
    sys.exit(app.exec_())
