"""
Driver Position Analysis Module
車手比賽排名分析模組

顯示所有車手的比賽排名變化，包括起始排名、結束排名、最佳/最差排名和位置變化。
"""

__version__ = "1.0.0"

# 導出模組類別
from .driver_position_analysis_module import DriverPositionAnalysisModule
from .driver_position_analysis_mdi import DriverPositionAnalysisMDI
from .driver_position_analysis_widget import DriverPositionAnalysisWidget

__all__ = [
    "DriverPositionAnalysisModule",
    "DriverPositionAnalysisMDI",
    "DriverPositionAnalysisWidget",
]
