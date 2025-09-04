"""
F1T 油門分析模組套件
圈速分析相關的油門分析組件
"""

from .throttle_analysis_module import ThrottleAnalysisModule
from .throttle_analysis_mdi import ThrottleAnalysisModule as ThrottleAnalysisMDIModule
from .throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
from .throttle_analysis_data_loader import ThrottleAnalysisDataLoader

__all__ = [
    'ThrottleAnalysisModule',
    'ThrottleAnalysisMDIModule',
    'ThrottleAnalysisChartWidget', 
    'ThrottleAnalysisDataLoader'
]
