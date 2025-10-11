"""
Ideal Lap Sector Heatmap package exports.
"""

__version__ = "1.0.0"

from .ideal_lap_sector_heatmap_module import IdealLapSectorHeatmapModule
from .ideal_lap_sector_heatmap_mdi import IdealLapSectorHeatmapMDI
from .ideal_lap_sector_heatmap_data_loader import IdealLapSectorHeatmapDataLoader
from .ideal_lap_sector_heatmap_widget import IdealLapSectorHeatmapWidget

__all__ = [
    "IdealLapSectorHeatmapModule",
    "IdealLapSectorHeatmapMDI",
    "IdealLapSectorHeatmapDataLoader",
    "IdealLapSectorHeatmapWidget",
]

try:
    from .register_module import register
    register()
except Exception as exc:
    print(f"[SECTOR_HEATMAP] 模組註冊失敗: {exc}")
