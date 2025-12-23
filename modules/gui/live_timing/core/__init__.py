"""
Live Timing 核心模組
====================

包含數據管理器、數據源、處理器等核心組件。

Author: F1T Team
Date: 2025-12-03

注意: 為了支援 CLI 模式（不依賴 PyQt5），部分模組採用延遲導入。
"""

# ============================================
# 非 GUI 依賴的模組 - 直接導入
# ============================================
from .local_source import LocalLiveF1DataSource, LiveF1DataSource
from .position_processor import LivePositionDataProcessor

# ============================================
# GUI 依賴的模組 - 延遲導入
# 這些模組依賴 PyQt5，在 CLI 模式下不應自動載入
# ============================================

# 延遲導入佔位符
LiveTimingDataManager = None
BaseLiveTimingMDI = None
LiveTimingModuleFactory = None
is_live_timing_module = None
create_live_timing_module = None
F1APIDownloader = None
download_race_data = None
is_race_cached = None
load_race_cache = None
LiveTimingAPIClient = None
get_api_client = None
RealtimeDatabase = None
get_realtime_db = None
DatabaseReader = None
get_database_reader = None


def _lazy_import_gui_modules():
    """延遲導入 GUI 相關模組"""
    global LiveTimingDataManager, BaseLiveTimingMDI, LiveTimingModuleFactory
    global is_live_timing_module, create_live_timing_module
    global F1APIDownloader, download_race_data, is_race_cached, load_race_cache
    global LiveTimingAPIClient, get_api_client
    global RealtimeDatabase, get_realtime_db, DatabaseReader, get_database_reader
    
    from .data_manager import LiveTimingDataManager as _LiveTimingDataManager
    from .base_live_mdi import BaseLiveTimingMDI as _BaseLiveTimingMDI
    from .module_factory import (
        LiveTimingModuleFactory as _LiveTimingModuleFactory,
        is_live_timing_module as _is_live_timing_module,
        create_live_timing_module as _create_live_timing_module,
    )
    from .f1_api_downloader import (
        F1APIDownloader as _F1APIDownloader,
        download_race_data as _download_race_data,
        is_race_cached as _is_race_cached,
        load_race_cache as _load_race_cache,
    )
    from .api_client import (
        LiveTimingAPIClient as _LiveTimingAPIClient,
        get_api_client as _get_api_client,
    )
    from .realtime_database import (
        RealtimeDatabase as _RealtimeDatabase,
        get_realtime_db as _get_realtime_db,
    )
    from .database_reader import (
        DatabaseReader as _DatabaseReader,
        get_database_reader as _get_database_reader,
    )
    
    LiveTimingDataManager = _LiveTimingDataManager
    BaseLiveTimingMDI = _BaseLiveTimingMDI
    LiveTimingModuleFactory = _LiveTimingModuleFactory
    is_live_timing_module = _is_live_timing_module
    create_live_timing_module = _create_live_timing_module
    F1APIDownloader = _F1APIDownloader
    download_race_data = _download_race_data
    is_race_cached = _is_race_cached
    load_race_cache = _load_race_cache
    LiveTimingAPIClient = _LiveTimingAPIClient
    get_api_client = _get_api_client
    RealtimeDatabase = _RealtimeDatabase
    get_realtime_db = _get_realtime_db
    DatabaseReader = _DatabaseReader
    get_database_reader = _get_database_reader


def __getattr__(name):
    """支援延遲導入的 __getattr__"""
    lazy_modules = {
        'LiveTimingDataManager', 'BaseLiveTimingMDI', 'LiveTimingModuleFactory',
        'is_live_timing_module', 'create_live_timing_module',
        'F1APIDownloader', 'download_race_data', 'is_race_cached', 'load_race_cache',
        'LiveTimingAPIClient', 'get_api_client',
        'RealtimeDatabase', 'get_realtime_db', 'DatabaseReader', 'get_database_reader',
    }
    
    if name in lazy_modules:
        _lazy_import_gui_modules()
        return globals()[name]
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'LiveTimingDataManager',
    'LocalLiveF1DataSource',
    'LiveF1DataSource',
    'LivePositionDataProcessor',
    'BaseLiveTimingMDI',
    'LiveTimingModuleFactory',
    'is_live_timing_module',
    'create_live_timing_module',
    # F1 API 下載器
    'F1APIDownloader',
    'download_race_data',
    'is_race_cached',
    'load_race_cache',
    # API 客戶端
    'LiveTimingAPIClient',
    'get_api_client',
    # 即時資料庫
    'RealtimeDatabase',
    'get_realtime_db',
    'DatabaseReader',
    'get_database_reader',
]
