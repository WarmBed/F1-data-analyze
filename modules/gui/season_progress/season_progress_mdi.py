#!/usr/bin/env python3
"""
Season Progress MDI Window

Manages season progress summary MDI window, integrating data loader and widget components

Author: F1T Team  
Date: 2025-10-13
Version: 1.0.0
"""

import sys
import time
import requests
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QProgressBar, QLabel,
    QApplication, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal

from core.gui_i18n import tr


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
            base_url: API base URL (default: https://api.f1telemetrystationpro.org)
            timeout: Request timeout (seconds)
        """
        super().__init__()
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        """Execute API request"""
        try:
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
            
            print(f"[API_WORKER] Calling API: {endpoint}")
            print(f"[API_WORKER] Parameters: {query_params}")
            
            # Send POST request
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
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
            
            print(f"[API_WORKER] API call successful (latency: {latency_ms:.2f} ms)")
            self.progress.emit(100)
            self.success.emit(result)
            
        except requests.exceptions.Timeout:
            error_msg = f"API request timeout ({self.timeout}s)"
            print(f"[API_WORKER] {error_msg}")
            self.failure.emit(error_msg)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {e.response.status_code}"
            print(f"[API_WORKER] {error_msg}")
            self.failure.emit(error_msg)
            
        except Exception as e:
            error_msg = f"API request failed: {str(e)}"
            print(f"[API_WORKER] {error_msg}")
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
        print(f"[SEASON_PROGRESS_MDI] Triggering API load: year={self.year}")
        self._start_load_analysis()
    
    def _start_load_analysis(self):
        """Start API-based data loading"""
        if self.api_worker and self.api_worker.isRunning():
            print("[SEASON_PROGRESS_MDI] API worker already running")
            return
        
        # Prepare API parameters
        params = {
            "year": self.year,
            "force_refresh": False
        }
        
        # Create and start API worker
        self.api_worker = SeasonProgressApiWorker(params)
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        self.status_label.setText(tr("loading_status", "Loading season progress data from API..."))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        self.api_worker.start()
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API request progress update"""
        print(f"[SEASON_PROGRESS_MDI] API progress: {progress}%")
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"API loading... {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict[str, Any]):
        """API request success"""
        try:
            print("[SEASON_PROGRESS_MDI] API call successful")
            
            # Extract API response
            api_response = result.get("data", {})
            meta = result.get("meta", {})
            
            # Detect nested structure (API cache may return double-nested JSON)
            if "data" in api_response and isinstance(api_response["data"], dict):
                # Double-nested: data.data.drivers/constructors
                print("[SEASON_PROGRESS_MDI] Detected double-nested structure")
                metadata = api_response.get("metadata", {})
                data_payload = api_response.get("data", {})
            else:
                # Single-layer: data.drivers/constructors
                metadata = api_response.get("metadata", {})
                data_payload = api_response
                print("[SEASON_PROGRESS_MDI] Detected single-layer structure")
            
            # Validate data
            drivers = data_payload.get("drivers", [])
            constructors = data_payload.get("constructors", [])
            
            if not drivers and not constructors:
                raise ValueError("API data missing both 'drivers' and 'constructors'")
            
            print(f"[SEASON_PROGRESS_MDI] Loaded {len(drivers)} drivers, {len(constructors)} constructors")
            print(f"[SEASON_PROGRESS_MDI] Metadata: season_year={metadata.get('season_year')}, round={metadata.get('resolved_round')}")
            
            # Transform for display (mimicking DataLoader transform)
            from .season_progress_data_loader import SeasonProgressDataLoader
            loader = SeasonProgressDataLoader(self.year)
            
            # Build raw_data structure matching DataLoader expectations
            raw_data_for_transform = {
                "success": True,
                "data": {
                    "drivers": drivers,
                    "constructors": constructors,
                    "metadata": metadata
                }
            }
            
            display_data = loader._transform_data_for_display(raw_data_for_transform)
            
            print(f"[SEASON_PROGRESS_MDI] Transformed data: year={display_data.get('season_year')}, round={display_data.get('round')}")
            
            # Populate widget
            self._on_data_loaded(display_data)
            
            # Update status
            source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
            self.status_label.setText(f"Loaded from {source_label}")
            
        except Exception as e:
            print(f"[SEASON_PROGRESS_MDI] Error processing API data: {e}")
            self._show_error("Data Processing Error", str(e))
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API request failure"""
        print(f"[SEASON_PROGRESS_MDI] API call failed: {error_msg}")
        self.status_label.setText(f"API load failed: {error_msg}")
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        
        # ❌ 已禁用彈窗：改為僅在介面上顯示錯誤訊息
        # self._show_error("API Load Failed", error_msg)
    
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        Data loaded completion handler
        
        Args:
            data: Transformed season progress data
        """
        print(f"[SEASON_PROGRESS_MDI] Data loaded successfully")
        
        # Populate widget
        self.progress_widget.populate_data(data)
        
        # Update status
        self.status_label.setText(tr("load_success_status", "Load successful"))
        self.progress_bar.setValue(100)
        self.progress_bar.hide()
    
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
        print(f"[SEASON_PROGRESS_MDI] ⚠️ 錯誤: {title} - {message}")


# Test code
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test MDI
    mdi = SeasonProgressMDI(year="2025")
    mdi.setWindowTitle(tr("test_window_title", "Season Progress MDI Test"))
    mdi.resize(600, 400)
    mdi.show()
    
    sys.exit(app.exec_())
