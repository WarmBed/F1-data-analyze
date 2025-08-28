"""
F1T 賽道分析模組
===============

這個模組提供 F1 賽道位置軌跡的分析與視覺化功能。

主要組件：
- TrackAnalysisModule: 主要分析模組，實現 IAnalysisModule 介面
- TrackPlotWidget: 基於 PyQtGraph 的高效能繪圖組件
- TrackDataLoader: JSON 數據載入器

Author: F1T Team
Date: 2025-08-28
Version: 1.0.0
"""

from .track_analysis_module import TrackAnalysisModule
from .track_plot_widget import TrackPlotWidget
from .track_data_loader import TrackDataLoader

__version__ = "1.0.0"
__author__ = "F1T Team"

__all__ = [
    'TrackAnalysisModule',
    'TrackPlotWidget', 
    'TrackDataLoader'
]
