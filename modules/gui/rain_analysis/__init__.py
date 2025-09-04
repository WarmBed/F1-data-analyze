#!/usr/bin/env python3
"""
降雨分析模組套件
Rain Analysis Module Package

包含所有與F1降雨分析相關的GUI組件和分析工具
Contains all GUI components and analysis tools related to F1 rain analysis
"""

# 主要模組匯出
from .rain_analysis_module import RainAnalysisModule
from .rain_analysis_widget import RainAnalysisWidget
from .rain_analysis_chart_widget import RainAnalysisChartWidget
from .rain_analysis_dual_axis_widget import RainAnalysisDualAxisChart
from .rain_analysis_universal_widget import RainAnalysisUniversalWidget
from .rain_chart_utils import WeatherChartFormatter
from .rain_intensity_analyzer_json import run_rain_intensity_analysis_json

__all__ = [
    'RainAnalysisModule',
    'RainAnalysisWidget', 
    'RainAnalysisChartWidget',
    'RainAnalysisDualAxisChart',
    'RainAnalysisUniversalWidget',
    'WeatherChartFormatter',
    'run_rain_intensity_analysis_json'
]

__version__ = '1.0.0'
__author__ = 'F1 Data Analysis Team'
__description__ = 'F1 Rain Analysis GUI Module Package'
