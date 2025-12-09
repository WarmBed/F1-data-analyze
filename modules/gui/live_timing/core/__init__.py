"""
Live Timing 核心模組
====================

包含數據管理器、數據源、處理器等核心組件。

Author: F1T Team
Date: 2025-12-03
"""

from .data_manager import LiveTimingDataManager
from .local_source import LocalLiveF1DataSource, LiveF1DataSource
from .position_processor import LivePositionDataProcessor
from .base_live_mdi import BaseLiveTimingMDI
from .module_factory import (
    LiveTimingModuleFactory,
    is_live_timing_module,
    create_live_timing_module,
)
from .f1_api_downloader import (
    F1APIDownloader,
    download_race_data,
    is_race_cached,
    load_race_cache,
)
from .api_client import (
    LiveTimingAPIClient,
    get_api_client,
)
from .realtime_database import (
    RealtimeDatabase,
    get_realtime_db,
)
from .database_reader import (
    DatabaseReader,
    get_database_reader,
)

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
