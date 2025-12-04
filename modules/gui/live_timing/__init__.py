"""
Live Timing 模組總入口
======================

提供 F1 即時計時功能的模組化實現，包含：
- 核心數據管理 (LiveTimingDataManager)
- 數據源 (本地 JSON / 即時 SignalR)
- 可視化組件 (TrackMap, Ranking, PitWindow 等)

Author: F1T Team
Date: 2025-12-03
"""

# Core 模組
from .core.data_manager import LiveTimingDataManager
from .core.local_source import LocalLiveF1DataSource, LiveF1DataSource
from .core.position_processor import LivePositionDataProcessor
from .core.base_live_mdi import BaseLiveTimingMDI
from .core.module_factory import (
    LiveTimingModuleFactory,
    is_live_timing_module,
    create_live_timing_module,
)

# Live Timing Modules
from .live_timing_modules.control_panel import LiveTimingControlPanel
from .live_timing_modules.control_dock import LiveTimingControlDock
from .live_timing_modules.track_map import LiveTimingTrackMap, TrackMapWidget
from .live_timing_modules.ranking_tower import LiveTimingRankingTower, RankingTableWidget
from .live_timing_modules.race_control_messages import LiveTimingRaceControlMessages, RaceControlMessagesWidget

__all__ = [
    # Core
    'LiveTimingDataManager',
    'LocalLiveF1DataSource',
    'LiveF1DataSource',
    'LivePositionDataProcessor',
    'BaseLiveTimingMDI',
    # Factory
    'LiveTimingModuleFactory',
    'is_live_timing_module',
    'create_live_timing_module',
    # Modules
    'LiveTimingControlPanel',
    'LiveTimingControlDock',
    'LiveTimingTrackMap',
    'TrackMapWidget',
    'LiveTimingRankingTower',
    'RankingTableWidget',
    'LiveTimingRaceControlMessages',
    'RaceControlMessagesWidget',
]
