"""Lazy public exports for Live Timing GUI modules."""


_LAZY_EXPORTS = {
    "LocalLiveF1DataSource": (".core.local_source", "LocalLiveF1DataSource"),
    "LiveF1DataSource": (".core.local_source", "LiveF1DataSource"),
    "LivePositionDataProcessor": (".core.position_processor", "LivePositionDataProcessor"),
    "LiveTimingDataManager": (".core.data_manager", "LiveTimingDataManager"),
    "BaseLiveTimingMDI": (".core.base_live_mdi", "BaseLiveTimingMDI"),
    "LiveTimingModuleFactory": (".core.module_factory", "LiveTimingModuleFactory"),
    "is_live_timing_module": (".core.module_factory", "is_live_timing_module"),
    "create_live_timing_module": (".core.module_factory", "create_live_timing_module"),
    "LiveTimingControlPanel": (".live_timing_modules.control_panel", "LiveTimingControlPanel"),
    "LiveTimingControlDock": (".live_timing_modules.control_dock", "LiveTimingControlDock"),
    "LiveTimingTrackMap": (".live_timing_modules.track_map", "LiveTimingTrackMap"),
    "TrackMapWidget": (".live_timing_modules.track_map", "TrackMapWidget"),
    "LiveTimingRankingTower": (".live_timing_modules.ranking_tower", "LiveTimingRankingTower"),
    "RankingTableWidget": (".live_timing_modules.ranking_tower", "RankingTableWidget"),
    "LiveTimingRaceControlMessages": (
        ".live_timing_modules.race_control_messages",
        "LiveTimingRaceControlMessages",
    ),
    "RaceControlMessagesWidget": (
        ".live_timing_modules.race_control_messages",
        "RaceControlMessagesWidget",
    ),
}


def __getattr__(name):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = importlib.import_module(module_name, __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


__all__ = [
    "LiveTimingDataManager",
    "LocalLiveF1DataSource",
    "LiveF1DataSource",
    "LivePositionDataProcessor",
    "BaseLiveTimingMDI",
    "LiveTimingModuleFactory",
    "is_live_timing_module",
    "create_live_timing_module",
    "LiveTimingControlPanel",
    "LiveTimingControlDock",
    "LiveTimingTrackMap",
    "TrackMapWidget",
    "LiveTimingRankingTower",
    "RankingTableWidget",
    "LiveTimingRaceControlMessages",
    "RaceControlMessagesWidget",
]
