#!/usr/bin/env python3
"""
Ideal Lap Sector Comparison Module
理想圈分段比較模組

使用 Matplotlib 堆疊棒狀圖顯示理想圈 vs 最快圈的分段對比。

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0
"""

__version__ = "1.0.0"

# 導出模組類別
from .ideal_lap_sector_comparison_module import IdealLapSectorComparisonModule
from .ideal_lap_sector_comparison_mdi import (
    IdealLapSectorComparisonMDI,
    SectorComparisonControlPanel  # ✅ 從 MDI 導出控制面板
)
from .ideal_lap_sector_comparison_data_loader import IdealLapSectorComparisonDataLoader
from .ideal_lap_sector_comparison_widget import IdealLapSectorComparisonWidget

__all__ = [
    "IdealLapSectorComparisonModule",
    "IdealLapSectorComparisonMDI",
    "IdealLapSectorComparisonDataLoader",
    "IdealLapSectorComparisonWidget",
    "SectorComparisonControlPanel"
]

# 自動註冊模組到工廠
try:
    from .register_module import register
    register()
except Exception as e:
    print(f"⚠️  IdealLapSectorComparison 自動註冊失敗: {e}")
