"""
理想圈分段對比模組 - 註冊腳本
Ideal Lap Sector Comparison Module Registration

將模組註冊到 ModuleFactory

作者: F1T Team
日期: 2025-10-09
"""

from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
from .ideal_lap_sector_comparison_module import IdealLapSectorComparisonModule


def register():
    """註冊理想圈分段對比模組到工廠"""
    try:
        ModuleFactory.register_module(
            ModuleTypes.IDEAL_LAP_SECTOR_COMPARISON,
            IdealLapSectorComparisonModule
        )
        print("✅ IdealLapSectorComparisonModule 已註冊到 ModuleFactory")
        return True
    except Exception as e:
        print(f"❌ 模組註冊失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


# 自動註冊（當模組被導入時）
if __name__ != "__main__":
    register()
