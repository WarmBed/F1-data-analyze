"""
ThrottleBoxPlotAnalysis - 油門箱型圖分析模組

此模組提供油門全開秒數分布的箱型圖視覺化分析。

主要組件:
- ThrottleBoxPlotAnalysis: MDI 主模組類（繼承 UniversalAnalysisMDI）
- ThrottleBoxPlotDataManager: 數據管理器（繼承 UniversalDataLoader）
- ThrottleBoxPlotChartWidget: 圖表組件
- ThrottleBoxPlotControlWidget: 控制面板
- ThrottleBoxPlotApiWorker: API 工作線程

功能特性:
- 箱型圖視覺化
- IQR 異常值過濾
- 進站圈/黃旗圈過濾
- 統計指標顯示
- 車隊配色方案
- 圖表匯出功能

數據源: CLI Function 54 (Lap Throttle Ratio Per Driver)
作者: F1T Team
版本: 1.0.0
"""

from .throttle_box_plot_analysis_mdi import (
    ThrottleBoxPlotAnalysis,
    ThrottleBoxPlotDataManager,
    ThrottleBoxPlotControlWidget,
    ThrottleBoxPlotApiWorker,
)
from .throttle_box_plot_chart_widget import ThrottleBoxPlotChartWidget
from .throttle_box_plot_analysis_module import (
    ThrottleBoxPlotAnalysisModule,
    create_throttle_boxplot_module,
)

__all__ = [
    "ThrottleBoxPlotAnalysis",
    "ThrottleBoxPlotDataManager",
    "ThrottleBoxPlotChartWidget",
    "ThrottleBoxPlotControlWidget",
    "ThrottleBoxPlotApiWorker",
    "ThrottleBoxPlotAnalysisModule",
    "create_throttle_boxplot_module",
]

__version__ = "1.0.0"
__author__ = "F1T Team"
