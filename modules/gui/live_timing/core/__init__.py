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

__all__ = [
    'LiveTimingDataManager',
    'LocalLiveF1DataSource',
    'LiveF1DataSource',
    'LivePositionDataProcessor',
    'BaseLiveTimingMDI',
    'LiveTimingModuleFactory',
    'is_live_timing_module',
    'create_live_timing_module',
    # 新增：F1 API 下載器
    'F1APIDownloader',
    'download_race_data',
    'is_race_cached',
    'load_race_cache',
]
