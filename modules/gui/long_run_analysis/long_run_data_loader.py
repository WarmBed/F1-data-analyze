#!/usr/bin/env python3
"""
Long Run Analysis Data Loader

Uses Function 28 API for lap time data.
Follows API-ONLY mode policy (no direct FastF1 calls, no CLI subprocess).

Author: F1T Team
Date: 2025-12-30
Version: 1.0.0
"""

import os
import sys
from pathlib import Path

# CRITICAL: Add project root to sys.path FIRST to ensure 'core' module
# is resolved from project root, not from strategy_simulator/core/
def _setup_project_path():
    """Find project root and add it to sys.path at position 0."""
    current = Path(__file__).resolve().parent
    for _ in range(10):  # Prevent infinite loop
        # Check for both 'core' folder AND 'f1t_gui_main.py' to confirm it's the project root
        if (current / 'core' / 'logger.py').exists():
            # Remove any existing entries that might conflict
            str_path = str(current)
            while str_path in sys.path:
                sys.path.remove(str_path)
            # Insert at position 0 to take priority
            sys.path.insert(0, str_path)
            return current
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent
    return None

_PROJECT_ROOT = _setup_project_path()

from typing import Dict, Any, Optional, List
from PyQt5.QtCore import QThread, pyqtSignal, QObject

# Import core modules using absolute path to avoid conflict with strategy_simulator/core
_core_logger = None
_core_api_base_url = None
_core_gui_i18n = None

def _import_core_module(module_name: str):
    """Import a module from project_root/core/ using absolute path."""
    import importlib.util
    if _PROJECT_ROOT is None:
        return None
    module_path = _PROJECT_ROOT / 'core' / f'{module_name}.py'
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f'_core_{module_name}', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _get_logger():
    global _core_logger
    if _core_logger is None:
        mod = _import_core_module('logger')
        if mod:
            _core_logger = mod.get_logger(__name__)
        else:
            # Fallback: use print
            import logging
            _core_logger = logging.getLogger(__name__)
    return _core_logger

def _lazy_tr(key: str, default: str) -> str:
    """Lazy translation function"""
    global _core_gui_i18n
    try:
        if _core_gui_i18n is None:
            _core_gui_i18n = _import_core_module('gui_i18n')
        if _core_gui_i18n and hasattr(_core_gui_i18n, 'tr'):
            return _core_gui_i18n.tr(key, default)
    except Exception:
        pass
    return default

def _resolve_api_base_url():
    """Get resolve_api_base_url function from core."""
    global _core_api_base_url
    if _core_api_base_url is None:
        _core_api_base_url = _import_core_module('api_base_url')
    if _core_api_base_url and hasattr(_core_api_base_url, 'resolve_api_base_url'):
        return _core_api_base_url.resolve_api_base_url
    return None


class LongRunApiWorker(QThread):
    """Background worker for Long Run API requests (Function 28)"""
    
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    # CLI Function ID for Detailed Lap Analysis
    CLI_FUNCTION_ID = 28
    
    def __init__(self, base_url: str, params: Dict[str, Any], 
                 timeout: float = 120.0, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.params = params
        self.timeout = timeout
        self._is_cancelled = False
    
    def run(self):
        """Execute API request"""
        import requests
from core.gui_i18n import tr
        
        try:
            self.progress.emit(10)
            
            # Build API endpoint
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            # Build request payload
            payload = {
                "function_id": self.CLI_FUNCTION_ID,
                "year": self.params.get("year"),
                "race": self.params.get("race"),
                "session": self.params.get("session", "FP2"),
            }
            
            if self.params.get("force_refresh"):
                payload["force_refresh"] = True
            
            _get_logger().info(f"[LONGRUN_API] Requesting: {endpoint} with {payload}")
            self.progress.emit(30)
            
            if self._is_cancelled:
                return
            
            # Make request
            response = requests.post(
                endpoint,
                params=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            self.progress.emit(70)
            
            if self._is_cancelled:
                return
            
            if response.status_code == 200:
                data = response.json()
                self.progress.emit(90)
                
                if data.get("success", True):
                    self.success.emit({
                        "data": data.get("data", data),
                        "meta": {
                            "source": "api",
                            "function_id": self.CLI_FUNCTION_ID,
                            "status_code": response.status_code,
                        }
                    })
                else:
                    error_msg = data.get("message", data.get("error", "API returned success=false"))
                    self.failure.emit(f"API Error: {error_msg}")
            else:
                self.failure.emit(f"HTTP {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            self.failure.emit(f"API request timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            self.failure.emit(f"Connection error: {e}")
        except Exception as e:
            _get_logger().error(f"[LONGRUN_API] Unexpected error: {e}")
            self.failure.emit(f"Unexpected error: {e}")
    
    def cancel(self):
        """Cancel the request"""
        self._is_cancelled = True


class LongRunDataLoader(QObject):
    """
    Long Run Analysis Data Loader
    
    Simplified data loader using API-ONLY pattern.
    Uses Function 28 (Detailed Lap Analysis) for lap time data.
    
    API-ONLY Mode (2025-10-03):
    - Uses REST API (refactored_api.py) for data
    - No direct FastF1 calls from GUI
    - No automatic CLI subprocess invocation
    """
    
    # Signals
    data_loaded = pyqtSignal(object)
    load_error = pyqtSignal(str)
    load_progress = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    
    # CLI Function ID
    CLI_FUNCTION = 28
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # API state
        self._api_worker: Optional[LongRunApiWorker] = None
        self._api_base_url: str = ""
        self._api_timeout: float = 120.0
        self._is_loading: bool = False
        
        # Current request params
        self._pending_params: Dict[str, Any] = {}
        
        # Cached data
        self._last_data_source: str = ""
        self._last_api_metadata: Dict[str, Any] = {}
    
    def _debug(self, message: str) -> None:
        """Debug logging"""
        _get_logger().debug(f"[LONGRUN_LOADER] {message}")
    
    def _error(self, message: str) -> None:
        """Error logging"""
        _get_logger().error(f"[LONGRUN_LOADER] {message}")
    
    def load_data(self, **kwargs) -> bool:
        """
        Load lap data for Long Run analysis
        
        Args:
            year: Race year (required)
            race: Race name (required)
            session: Session type (default: "FP2")
            force_refresh: Force API refresh (default: False)
        
        Returns:
            True if load started successfully
        """
        try:
            # Validate parameters
            year = kwargs.get("year")
            race = kwargs.get("race")
            session = kwargs.get("session", "FP2")
            
            if not year or not race:
                self.load_error.emit(_lazy_tr("long_run.error.missing_params", 
                                        "Missing required parameters: year and race"))
                return False
            
            # Normalize parameters
            params = {
                "year": int(year),
                "race": str(race).strip(),
                "session": str(session).strip().upper() or "FP2",
                "force_refresh": bool(kwargs.get("force_refresh", False)),
            }
            
            self._pending_params = params
            self._is_loading = True
            
            # Determine API base URL
            self._api_base_url = self._determine_api_base_url()
            
            self._debug(f"Loading data: {params}")
            self.load_progress.emit(5)
            self.status_changed.emit(_lazy_tr("long_run.loading", "Loading Long Run data..."))
            
            # Start API request
            self._start_api_request(params)
            return True
            
        except Exception as e:
            self._error(f"load_data failed: {e}")
            self._is_loading = False
            self.load_error.emit(str(e))
            return False
    
    def _determine_api_base_url(self) -> str:
        """Determine API base URL"""
        resolve_fn = _resolve_api_base_url()
        
        if resolve_fn is None:
            # Fallback to default API URL
            self._debug("Could not load resolve_api_base_url, using default")
            return "http://localhost:8000"
        
        preferred: List[tuple] = []
        
        override = os.getenv("F1T_API_BASE_URL")
        if override:
            preferred.append(("Environment F1T_API_BASE_URL", override))
        
        base_url = resolve_fn(
            event_logger=self._debug,
            preferred_urls=preferred or None,
        )
        self._debug(f"API base URL: {base_url}")
        return base_url
    
    def _start_api_request(self, params: Dict[str, Any]) -> None:
        """Start background API request"""
        self._cleanup_api_worker()
        
        self._api_worker = LongRunApiWorker(
            self._api_base_url,
            params,
            timeout=self._api_timeout,
            parent=self,
        )
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker)
        self._api_worker.start()
        
        self.status_changed.emit(_lazy_tr("long_run.api_loading", "Loading via API..."))
    
    def _on_api_progress(self, value: int) -> None:
        """API progress callback"""
        try:
            bounded = max(0, min(int(value), 99))
            self.load_progress.emit(bounded)
        except Exception:
            pass
    
    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        """API success callback"""
        self._debug("API request successful")
        
        try:
            raw_data = payload.get("data") if isinstance(payload, dict) else payload
            meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
            
            if raw_data is None:
                raise ValueError("API returned empty data")
            
            if not self._validate_data_format(raw_data):
                raise ValueError("Invalid data format from API")
            
            # Store metadata
            self._last_api_metadata = meta
            self._last_data_source = "api"
            
            # Process and emit
            self._is_loading = False
            self.load_progress.emit(100)
            self.status_changed.emit(_lazy_tr("long_run.loaded", "Data loaded successfully"))
            self.data_loaded.emit(raw_data)
            
        except Exception as e:
            self._error(f"API data processing failed: {e}")
            self._on_api_error(str(e))
    
    def _on_api_error(self, message: str) -> None:
        """API error callback"""
        self._error(f"API error: {message}")
        self._is_loading = False
        self.load_error.emit(message)
    
    def _cleanup_api_worker(self) -> None:
        """Cleanup API worker thread"""
        if self._api_worker:
            try:
                if self._api_worker.isRunning():
                    self._api_worker.cancel()
                    self._api_worker.wait(2000)
                self._api_worker.deleteLater()
            except Exception:
                pass
            finally:
                self._api_worker = None
    
    def _validate_data_format(self, raw_data: Any) -> bool:
        """
        Validate API response data format
        
        Expected formats from Function 28 API:
        1. {'all_drivers_detailed_laptime': {'VER': [...], 'LEC': [...]}}  # Main format
        2. {'drivers': {'VER': {...}, 'LEC': {...}}}  # Alternative
        3. {'laps': [{...}, {...}]}  # Alternative
        4. {'data': {...}} (nested wrapper)
        5. {'success': True, 'all_drivers_detailed_laptime': {...}}  # Direct API response
        """
        if not raw_data:
            self._debug("Validation failed: raw_data is empty")
            return False
        
        if isinstance(raw_data, dict):
            # Check for Function 28 main format
            if 'all_drivers_detailed_laptime' in raw_data:
                lap_data = raw_data['all_drivers_detailed_laptime']
                if isinstance(lap_data, dict) and len(lap_data) > 0:
                    self._debug(f"Valid format: all_drivers_detailed_laptime with {len(lap_data)} drivers")
                    return True
            
            # Check for alternative formats
            if 'drivers' in raw_data or 'laps' in raw_data:
                self._debug("Valid format: drivers or laps key found")
                return True
            
            # Check for nested data structure
            if 'data' in raw_data:
                self._debug("Found nested 'data' key, validating inner structure")
                return self._validate_data_format(raw_data['data'])
            
            # Log available keys for debugging
            self._debug(f"Validation failed: unknown format. Keys: {list(raw_data.keys())[:10]}")
        else:
            self._debug(f"Validation failed: raw_data is not dict, type={type(raw_data).__name__}")
        
        return False
    
    def cancel(self) -> None:
        """Cancel any ongoing load operation"""
        self._cleanup_api_worker()
        self._is_loading = False
    
    def is_loading(self) -> bool:
        """Check if currently loading"""
        return self._is_loading
    
    def get_last_data_source(self) -> str:
        """Get last data source used"""
        return self._last_data_source
    
    def get_last_api_metadata(self) -> Dict[str, Any]:
        """Get last API metadata"""
        return self._last_api_metadata
