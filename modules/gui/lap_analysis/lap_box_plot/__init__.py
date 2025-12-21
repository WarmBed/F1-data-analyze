"""
LapTimeBoxPlotAnalysis - 圈速箱型圖分析模組

此模組提供圈速分布的箱型圖視覺化分析

主要組件:
- LapTimeBoxPlotAnalysis: MDI 主模組類（繼承 UniversalAnalysisMDI）
- LapTimeBoxPlotDataManager: 數據管理器（繼承 UniversalDataLoader）
- LapTimeBoxPlotChartWidget: 圖表組件
- LapTimeBoxPlotControlWidget: 控制面板
- LapTimeBoxPlotApiWorker: API 工作線程

功能特性:
- 箱型圖視覺化
- IQR 異常值過濾
- 進站圈過濾
- 統計指標顯示
- 車隊配色方案
- 圖表匯出功能

數據源: CLI Function 28 (detailed_laptime_analysis)
作者: F1T Team
版本: 1.0.0
"""

from .lap_box_plot_analysis_mdi import (
    LapTimeBoxPlotAnalysis,
    LapTimeBoxPlotDataManager,
    LapTimeBoxPlotControlWidget,
    LapTimeBoxPlotApiWorker
)
from .lap_box_plot_chart_widget import LapTimeBoxPlotChartWidget

__all__ = [
    'LapTimeBoxPlotAnalysis',
    'LapTimeBoxPlotDataManager',
    'LapTimeBoxPlotChartWidget',
    'LapTimeBoxPlotControlWidget',
    'LapTimeBoxPlotApiWorker'
]

__version__ = "1.0.0"
__author__ = "F1T Team"
