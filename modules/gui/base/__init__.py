#!/usr/bin/env python3
"""
F1T GUI Base Module
==================

這個模組包含了所有 F1T GUI 組件的基礎類別和工具函數。

主要組件：
- UniversalDataLoader: 通用數據載入器基類
- AnalysisConfig: 分析類型配置類

Author: F1T Team
Date: 2025-09-09
Version: 1.0.0
"""

from .universal_data_loader_base import UniversalDataLoader, AnalysisConfig
from .universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
from .universal_chart_widget_base import TelemetryChartWidgetBase, ChartTheme

__all__ = [
    'UniversalDataLoader',
    'AnalysisConfig',
    'UniversalAnalysisMDI',
    'AnalysisMDIConfig', 
    'TelemetryChartWidgetBase',
    'ChartTheme'
]

__version__ = '1.0.0'
