"""Lazy public exports for Live Timing core modules."""

_LAZY_EXPORTS = {
    "LocalLiveF1DataSource": (".local_source", "LocalLiveF1DataSource"),
    "LiveF1DataSource": (".local_source", "LiveF1DataSource"),
    "LivePositionDataProcessor": (".position_processor", "LivePositionDataProcessor"),
    "LiveTimingDataManager": (".data_manager", "LiveTimingDataManager"),
    "BaseLiveTimingMDI": (".base_live_mdi", "BaseLiveTimingMDI"),
    "LiveTimingModuleFactory": (".module_factory", "LiveTimingModuleFactory"),
    "is_live_timing_module": (".module_factory", "is_live_timing_module"),
    "create_live_timing_module": (".module_factory", "create_live_timing_module"),
    "F1APIDownloader": (".f1_api_downloader", "F1APIDownloader"),
    "download_race_data": (".f1_api_downloader", "download_race_data"),
    "is_race_cached": (".f1_api_downloader", "is_race_cached"),
    "load_race_cache": (".f1_api_downloader", "load_race_cache"),
    "LiveTimingAPIClient": (".api_client", "LiveTimingAPIClient"),
    "get_api_client": (".api_client", "get_api_client"),
    "RealtimeDatabase": (".realtime_database", "RealtimeDatabase"),
    "get_realtime_db": (".realtime_database", "get_realtime_db"),
    "DatabaseReader": (".database_reader", "DatabaseReader"),
    "get_database_reader": (".database_reader", "get_database_reader"),
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


__all__ = list(_LAZY_EXPORTS)
