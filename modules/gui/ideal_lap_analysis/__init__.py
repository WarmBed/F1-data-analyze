"""
Ideal Lap Analysis GUI Module
理想圈分析 GUI 模組

提供三個子模組：
1. ideal_lap_ranking_table - 排名表格總覽
2. ideal_lap_sector_heatmap - 分段熱力圖
3. ideal_lap_sector_comparison - 分段比較圖

所有模組遵循通用模組架構 (IAnalysisModule → UniversalAnalysisMDI → UniversalDataLoader → UniversalChartWidget)
"""

__version__ = "1.0.0"
__author__ = "F1T Development Team"

# 導出對話框（已完成）
from .ideal_lap_options_dialog import IdealLapAnalysisOptionsDialog

# 導出主要類別（待實作後啟用）
# from .ideal_lap_ranking_table.ideal_lap_ranking_table_module import (
#     IdealLapRankingTableModule
# )

__all__ = [
    "IdealLapAnalysisOptionsDialog",
    # "IdealLapRankingTableModule",
]
