"""
Ideal Lap Sector Heatmap Module Registration
============================================

Registers the heatmap module with the global ModuleFactory.
"""

from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes

from .ideal_lap_sector_heatmap_module import IdealLapSectorHeatmapModule


def register() -> bool:
    try:
        ModuleFactory.register_module(
            ModuleTypes.IDEAL_LAP_SECTOR_HEATMAP,
            IdealLapSectorHeatmapModule,
        )
        print("[SECTOR_HEATMAP] Module registered")
        return True
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[SECTOR_HEATMAP] Module registration failed: {exc}")
        return False


if __name__ != "__main__":
    register()

