"""
Ideal Lap Ranking Table Module
理想圈排名表格模組

顯示所有車手的理想圈排名、車手最速圈、差異與全場最速實際圈對比。
"""

__version__ = "1.0.0"

# 導出模組類別
from .ideal_lap_ranking_table_module import IdealLapRankingTableModule
from .ideal_lap_ranking_table_mdi import IdealLapRankingTableMDI
from .ideal_lap_ranking_table_data_loader import IdealLapRankingTableDataLoader
from .ideal_lap_ranking_table_widget import IdealLapRankingTableWidget

__all__ = [
    "IdealLapRankingTableModule",
    "IdealLapRankingTableMDI",
    "IdealLapRankingTableDataLoader",
    "IdealLapRankingTableWidget",
]
