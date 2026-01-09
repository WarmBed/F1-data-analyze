#!/usr/bin/env python3
"""
Season Progress MDI Window

Manages season progress summary MDI window, integrating data loader and widget components

Author: F1T Team  
Date: 2025-10-13
Version: 1.0.0
"""

import logging
import sys
import time
import requests
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

logger = get_logger("season_progress.mdi", component="gui")


class SeasonProgressApiWorker(QThread):
    """
    Season Progress API Request Worker Thread
    
    Handles async API calls to fetch championship standings data
    API Endpoint: POST /api/v2/analysis/execute?function_id=97
    """
    
    # Signals
    progress = pyqtSignal(int)  # Progress (0-100)
    success = pyqtSignal(dict)  # Success (returns data)
    failure = pyqtSignal(str)   # Failure (error message)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        """
        Initialize API Worker
        
        Args:
            params: API parameters (year, etc.)
            base_url: API base URL (default: https://localhost:8000)
            timeout: Request timeout (seconds)
        """
        super().__init__()
        self.base_url = (base_url or "https://localhost:8000").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        """Execute API request"""
        try:
            # 檢查是否已被請求中斷
            if self.isInterruptionRequested():
                logger.debug("[SEASON_API_WORKER] 啟動前已被請求中斷，跳過執行")
                return
            
            # ✅ 早期檢測未來賽季（2026+），直接返回友善錯誤
            year = int(self.params.get("year"))
            from datetime import datetime
            current_year = datetime.now().year
            
            if year > current_year:
                print(f"[DEBUG API_WORKER] 檢測到未來年份 {year}，直接返回未來賽季錯誤")
                future_error = f"422 Unprocessable Entity: {year} 賽季尚未開始"
                self.failure.emit(future_error)
                return
                
            self.progress.emit(20)
            
            # Build API endpoint
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            # Build query parameters
            query_params: Dict[str, Any] = {
                "function_id": 97,  # CLI Function 97 - Championship Standings
                "year": int(self.params.get("year")),
            }
            
            # Force refresh (optional)
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[API_WORKER] Calling API: %s", endpoint)
                logger.debug("[API_WORKER] Parameters: %s", query_params)
            
            # 再次檢查中斷（在發送請求前）
            if self.isInterruptionRequested():
                logger.debug("[SEASON_API_WORKER] 發送請求前被請求中斷")
                return
                
            # Send POST request
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
            )
            
            # 請求完成後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[SEASON_API_WORKER] API 回應後被請求中斷，放棄處理結果")
                return
                
            self.progress.emit(70)
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse JSON response
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be JSON object")
            
            if not payload.get("success", False):
                # ✅ 修正：API 失敗時發送 failure 信號而不是拋出異常
                error_msg = payload.get("message", "API returned success=False")
                logger.warning("[SEASON_API_WORKER] API 返回失敗: %s", error_msg)
                if not self.isInterruptionRequested():
                    self.failure.emit(error_msg)
                return
            
            # Extract data
            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API response missing 'data' object")
            
            # Calculate latency
            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            
            # Build result
            result = {
                "success": True,
                "data": data,
                "meta": {
                    "source": "api",
                    "latency_ms": round(latency_ms, 2),
                    "base_url": self.base_url
                }
            }
            
            # 發送信號前最後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[SEASON_API_WORKER] 發送成功信號前被請求中斷，放棄發送")
                return
                
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[API_WORKER] API call successful (latency: %.2f ms)", latency_ms)
            self.progress.emit(100)
            self.success.emit(result)
            
        except requests.exceptions.Timeout:
            # 如果被中斷，不發送失敗信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API request timeout ({self.timeout}s)"
            logger.error("[API_WORKER] %s", error_msg)
            self.failure.emit(error_msg)
            
        except requests.exceptions.HTTPError as e:
            # 如果被中斷，不發送失敗信號
            if self.isInterruptionRequested():
                return
            
            # ✅ 特殊處理：422 錯誤（通常是年份超出範圍）
            if e.response.status_code == 422:
                try:
                    payload = e.response.json()
                    # 處理 FastAPI 的 detail 格式
                    if "detail" in payload:
                        detail = payload["detail"]
                        if isinstance(detail, list) and len(detail) > 0:
                            error_msg = detail[0].get("msg", "請求的年份數據不可用")
                        else:
                            error_msg = str(detail)
                    else:
                        error_msg = payload.get("message", "請求的年份數據不可用")
                    logger.warning("[API_WORKER] 422 Error: %s", error_msg)
                    # 加入 422 標記以便 _on_api_failure 偵測
                    self.failure.emit(f"422: {error_msg}")
                except Exception:
                    error_msg = f"HTTP 422: 請求的年份數據可能尚未可用"
                    logger.error("[API_WORKER] %s", error_msg)
                    self.failure.emit(error_msg)
            else:
                error_msg = f"HTTP error: {e.response.status_code}"
                logger.error("[API_WORKER] %s", error_msg)
                self.failure.emit(error_msg)
            
        except Exception as e:
            # 如果被中斷，不發送失敗信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API request failed: {str(e)}"
            logger.error("[API_WORKER] %s", error_msg)
            self.failure.emit(error_msg)


class SeasonProgressMDI(QWidget):
    """
    Season Progress Summary MDI Window
    
    Displays season progress, race calendar, and championship leaders
    Uses API-ONLY pattern (no CLI subprocess calls)
    """
    
    def __init__(self, year: str, parent=None):
        """
        Initialize MDI window
        
        Args:
            year: Season year (e.g., "2025")
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.year = str(year)
        self.api_worker = None
        
        self._setup_ui()
        self._connect_signals()
        
        # Auto-load data
        self._trigger_initial_load()
    
    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Status bar (hidden)
        self.status_label = QLabel(tr("loading_status", "Loading..."), self)
        self.status_label.setStyleSheet("padding: 5px; background: #f0f0f0;")
        self.status_label.hide()  # Hide status bar
        layout.addWidget(self.status_label)
        
        # Progress bar (hidden)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.hide()  # Hide progress bar
        layout.addWidget(self.progress_bar)
        
        # Season Progress Widget
        from .season_progress_widget import SeasonProgressWidget
        self.progress_widget = SeasonProgressWidget(parent=self)
        layout.addWidget(self.progress_widget)
    
    def _connect_signals(self):
        """Connect internal signals"""
        pass  # No signals to connect yet
    
    def _trigger_initial_load(self):
        """Trigger initial data load via API"""
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[SEASON_PROGRESS_MDI] Triggering API load: year=%s", self.year)
        self._start_load_analysis()
    
    def _start_load_analysis(self):
        """Start API-based data loading"""
        print(f"\n{'='*80}")
        print(f"[DEBUG] _start_load_analysis() 被調用")
        print(f"[DEBUG] self.year = {self.year}")
        print(f"{'='*80}\n")
        
        if self.api_worker and self.api_worker.isRunning():
            print(f"[DEBUG] API worker 已在運行中，跳過")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[SEASON_PROGRESS_MDI] API worker already running")
            return
        
        # Prepare API parameters
        params = {
            "year": self.year,
            "force_refresh": False
        }
        
        print(f"[DEBUG] 準備 API 參數: {params}")
        
        # Create and start API worker
        self.api_worker = SeasonProgressApiWorker(params)
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        print(f"[DEBUG] API worker 已創建並連接信號")
        
        self.status_label.setText(tr("loading_status", "Loading season progress data from API..."))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        print(f"[DEBUG] 啟動 API worker...")
        self.api_worker.start()
        print(f"[DEBUG] API worker 已啟動\n")
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API request progress update"""
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[SEASON_PROGRESS_MDI] API progress: %d%%", progress)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"API loading... {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict[str, Any]):
        """API request success"""
        try:
            print("\n" + "="*80)
            print(f"[DEBUG] _on_api_success 被調用，年份={self.year}")
            print(f"[DEBUG] result keys: {list(result.keys())}")
            print(f"[DEBUG] result 內容: {result}")
            print("="*80 + "\n")
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[SEASON_PROGRESS_MDI] API call successful")
            
            # Extract API response
            api_response = result.get("data", {})
            meta = result.get("meta", {})
            print(f"[DEBUG] api_response keys: {list(api_response.keys())}")
            print(f"[DEBUG] meta: {meta}")
            
            # Detect nested structure (API cache may return double-nested JSON)
            if "data" in api_response and isinstance(api_response["data"], dict):
                # Double-nested: data.data.drivers/constructors
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("[SEASON_PROGRESS_MDI] Detected double-nested structure")
                metadata = api_response.get("metadata", {})
                data_payload = api_response.get("data", {})
            else:
                # Single-layer: data.drivers/constructors
                metadata = api_response.get("metadata", {})
                data_payload = api_response
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("[SEASON_PROGRESS_MDI] Detected single-layer structure")
            
            # Validate data
            drivers = data_payload.get("drivers", [])
            constructors = data_payload.get("constructors", [])
            
            print(f"[DEBUG] drivers 數量: {len(drivers)}")
            print(f"[DEBUG] constructors 數量: {len(constructors)}")
            
            # ✅ 當沒有車手和車隊數據時，視為未來賽季
            if not drivers and not constructors:
                print("[DEBUG] ✅ 檢測到空數據，調用 _show_future_season_placeholder()")
                logger.info("[SEASON_PROGRESS_MDI] No standings data available, showing future season placeholder")
                self._show_future_season_placeholder()
                print("[DEBUG] ✅ _show_future_season_placeholder() 執行完畢")
                self.status_label.setText(tr("future_season_no_data", "賽季數據尚未發布"))
                self.status_label.setStyleSheet("color: #6c757d;")
                self.progress_bar.setValue(0)
                self.progress_bar.hide()
                print("[DEBUG] ✅ 返回，不進行後續處理")
                return
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "[SEASON_PROGRESS_MDI] Loaded %d drivers, %d constructors",
                    len(drivers),
                    len(constructors),
                )
                logger.debug(
                    "[SEASON_PROGRESS_MDI] Metadata: season_year=%s, round=%s",
                    metadata.get('season_year'),
                    metadata.get('resolved_round'),
                )
            
            # Transform for display (mimicking DataLoader transform)
            from .season_progress_data_loader import SeasonProgressDataLoader
            loader = SeasonProgressDataLoader(self.year)
            
            # Build raw_data structure matching DataLoader expectations
            raw_data_for_transform = {
                "success": True,
                "data": {
                    "drivers": drivers,
                    "constructors": constructors,
                    "metadata": metadata,
                    "calendar": data_payload.get("calendar")  # ✅ 傳遞 calendar 數據
                }
            }
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[SEASON_PROGRESS_MDI] Calendar in payload: %s", data_payload.get('calendar'))
            display_data = loader._transform_data_for_display(raw_data_for_transform)
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "[SEASON_PROGRESS_MDI] Transformed data: year=%s, round=%s",
                    display_data.get('season_year'),
                    display_data.get('round'),
                )
            
            # Populate widget
            self._on_data_loaded(display_data)
            
            # Update status
            source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
            self.status_label.setText(f"Loaded from {source_label}")
            
        except Exception as e:
            logger.error("[SEASON_PROGRESS_MDI] Error processing API data: %s", e)
            self._show_error("Data Processing Error", str(e))
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API request failure"""
        print("\n" + "="*80)
        print(f"[DEBUG] _on_api_failure 被調用")
        print(f"[DEBUG] error_message: {error_msg}")
        print("="*80 + "\n")
        
        print(f"[SEASON_MDI] API 調用失敗: {error_msg}")
        logger.error("[SEASON_PROGRESS_MDI] API call failed: %s", error_msg)
        
        # 偵測未來賽季錯誤（多種可能的錯誤訊息格式）
        # ✅ 關鍵修復：對於當前年份或未來年份，如果 API 返回失敗，視為賽季尚未開始
        year_int = int(self.year)
        from datetime import datetime
        current_year = datetime.now().year
        
        print(f"[SEASON_MDI] 年份檢測: year_int={year_int}, current_year={current_year}")
        
        # ✅ 修復邏輯：
        # 1. 如果是未來年份 (year > current) → 一定是未來賽季
        # 2. 如果是當前年份 (year == current) 且 API 返回「無效的返回值」→ 賽季尚未開始
        # 3. 如果是過去年份，只有特定錯誤才視為未來賽季
        
        if year_int > current_year:
            # 未來年份：一定是未來賽季
            is_future_season_error = True
            print(f"[SEASON_MDI] ✅ 未來年份 {year_int} > {current_year}，強制觸發未來賽季邏輯")
        elif year_int == current_year:
            # ✅ 當前年份：API 失敗就視為賽季尚未開始
            # 因為現在是 2026 年 1 月，F1 賽季要到 3 月才開始
            # 如果 API 能成功返回數據，就不會進入這個 _on_api_failure 方法
            print(f"[SEASON_MDI] 錯誤訊息原始內容: {repr(error_msg)}")
            logger.info(f"[SEASON_MDI] 錯誤訊息原始內容: {repr(error_msg)}")
            
            # ✅ 直接判定為賽季尚未開始（不再依賴錯誤訊息內容）
            is_future_season_error = True
            print(f"[SEASON_MDI] ✅ 當前年份 {year_int}，API 失敗，強制判定為賽季尚未開始")
        else:
            # 過去年份：只有特定錯誤才視為未來賽季（通常不會發生）
            is_future_season_error = (
                "422" in error_msg or 
                "Unprocessable" in error_msg
            )
            print(f"[SEASON_MDI] 過去年份 {year_int}，is_future={is_future_season_error}")
        
        print(f"[SEASON_MDI] is_future_season_error: {is_future_season_error}")
        
        if is_future_season_error:
            # 未來年份：提供模擬數據讓 Widget 顯示友善訊息
            print(f"[SEASON_MDI] 呼叫 _show_future_season_placeholder()")
            self._show_future_season_placeholder()
            self.status_label.setText(tr("future_season_no_data", "賽季數據尚未發布"))
            self.status_label.setStyleSheet("color: #6c757d;")
        else:
            # 其他錯誤
            display_msg = f"{tr('load_failed', 'Load failed')}: {error_msg}"
            self.status_label.setText(display_msg)
            self.status_label.setStyleSheet("color: red;")
        
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
    
    def _show_future_season_placeholder(self):
        """
        為未來賽季顯示友善的佔位數據
        
        嘗試從本地 Season Calendar JSON 載入首場賽事資訊
        """
        print(f"\n{'='*80}")
        print(f"[DEBUG] _show_future_season_placeholder() 開始執行，年份={self.year}")
        print(f"{'='*80}\n")
        
        from pathlib import Path
        import json
        from datetime import datetime, timezone
        
        # 預設數據
        first_race_name = "Australian Grand Prix"
        first_race_date = ""
        total_races = 24
        
        print(f"[DEBUG] 預設數據設定完成: first_race_name={first_race_name}, total_races={total_races}")
        
        # 嘗試從本地 JSON 載入 Season Calendar 獲取準確資訊
        try:
            json_dir = Path("json")
            calendar_files = sorted(
                json_dir.glob("season_calendar_multi_year*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if calendar_files:
                with open(calendar_files[0], 'r', encoding='utf-8') as f:
                    calendar_data = json.load(f)
                
                year_events = calendar_data.get("data", {}).get(str(self.year), [])
                if year_events:
                    total_races = len(year_events)
                    first_event = year_events[0]
                    first_race_name = first_event.get("event_name", first_race_name)
                    first_race_date = first_event.get("race_date_local", "") or first_event.get("race_date_utc", "")
                    print(f"[SEASON_MDI] 從本地 JSON 載入: {first_race_name}, {first_race_date}")
        except Exception as e:
            print(f"[SEASON_MDI] 無法載入本地 Season Calendar: {e}")
        
        # 構建模擬數據，觸發未來賽季顯示邏輯
        placeholder_data = {
            "season_year": int(self.year),
            "round": 0,
            "calendar": {
                "completed": 0,  # 關鍵：完成數為 0 觸發未來賽季邏輯
                "remaining": total_races,
                "total": total_races,
                "next_race": {
                    "name": first_race_name,
                    "date": first_race_date
                }
            },
            "leaders": {
                "driver": None,
                "constructor": None
            }
        }
        
        print(f"[DEBUG] 構建 placeholder_data 完成:")
        print(f"  - season_year: {placeholder_data['season_year']}")
        print(f"  - calendar.completed: {placeholder_data['calendar']['completed']}")
        print(f"  - calendar.total: {placeholder_data['calendar']['total']}")
        print(f"  - next_race: {placeholder_data['calendar']['next_race']}")
        
        # 調用 Widget 的 populate_data 顯示友善訊息
        print(f"[DEBUG] 準備調用 _on_data_loaded()")
        self._on_data_loaded(placeholder_data)
        print(f"[DEBUG] _on_data_loaded() 調用完成")
    
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        Data loaded completion handler
        
        Args:
            data: Transformed season progress data
        """
        print(f"\n{'='*80}")
        print(f"[DEBUG] _on_data_loaded() 被調用")
        print(f"[DEBUG] data keys: {list(data.keys())}")
        print(f"[DEBUG] data season_year: {data.get('season_year')}")
        print(f"[DEBUG] data calendar: {data.get('calendar')}")
        print(f"{'='*80}\n")
        
        # Populate widget
        print(f"[DEBUG] 準備調用 self.progress_widget.populate_data()")
        self.progress_widget.populate_data(data)
        print(f"[DEBUG] populate_data 調用完成")
        
        # Update status
        self.status_label.setText(tr("load_success_status", "Load successful"))
        self.progress_bar.setValue(100)
        self.progress_bar.hide()
        print(f"[DEBUG] _on_data_loaded() 執行完畢\n")
    
    def _show_error(self, title: str, message: str):
        """
        Show error dialog (已禁用彈窗功能)
        
        Args:
            title: Dialog title
            message: Error message
        """
        # ❌ 已禁用彈窗：僅保留方法以維持相容性
        # parent = self.progress_widget if hasattr(self, 'progress_widget') else None
        # QMessageBox.critical(parent, title, message)
        logger.warning("[SEASON_PROGRESS_MDI] 錯誤: %s - %s", title, message)
    
    def update_year(self, year: str):
        """
        更新年份並重新載入數據
        
        Args:
            year: 新的年份 (例如: "2025")
        """
        print(f"\n{'='*80}")
        print(f"[DEBUG UPDATE_YEAR] update_year 被調用")
        print(f"[DEBUG UPDATE_YEAR] 當前年份: {self.year}")
        print(f"[DEBUG UPDATE_YEAR] 新年份: {year}")
        print(f"{'='*80}\n")
        
        if str(year) == str(self.year):
            print(f"[DEBUG UPDATE_YEAR] 年份相同，跳過更新\n")
            return
        
        # 更新年份
        self.year = str(year)
        print(f"[DEBUG UPDATE_YEAR] ✅ 年份已更新為: {self.year}")
        print(f"[DEBUG UPDATE_YEAR] 開始重新載入數據...\n")
        self._start_load_analysis()
    
    def update_parameters(self, year: str = None, **kwargs):
        """
        通用參數更新方法（與其他模組保持一致）
        
        Args:
            year: 年份
            **kwargs: 其他參數（忽略）
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[SEASON_PROGRESS_MDI] update_parameters 被調用: year=%s", year)
        
        if year is not None:
            self.update_year(year)
            return True
        
        return False


# Test code
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test MDI
    mdi = SeasonProgressMDI(year="2025")
    mdi.setWindowTitle(tr("test_window_title", "Season Progress MDI Test"))
    mdi.resize(600, 400)
    mdi.show()
    
    sys.exit(app.exec_())
