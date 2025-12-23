"""
F1T 圈速分析模組套件
包含所有圈速分析相關的子模組
"""

# 匯入速度分析子模組
from .speed_analysis import SpeedAnalysisModule, SpeedAnalysisChartWidget, SpeedAnalysisDataLoader

# 匯入 RPM 分析子模組
from .rpm_analysis import RPMAnalysisModule, RPMAnalysisChartWidget, RPMAnalysisDataLoader

# 匯入油門分析子模組
from .Throttle_analysis import ThrottleAnalysisModule, ThrottleAnalysisChartWidget, ThrottleAnalysisDataLoader

# 匯入分析模組管理器
from .analysis_module_manager import AnalysisModuleManager, get_analysis_module_manager

__all__ = [
    # 速度分析
    'SpeedAnalysisModule',
    'SpeedAnalysisChartWidget',
    'SpeedAnalysisDataLoader',
    # RPM 分析
    'RPMAnalysisModule',
    'RPMAnalysisChartWidget',
    'RPMAnalysisDataLoader',
    # 油門分析
    'ThrottleAnalysisModule',
    'ThrottleAnalysisChartWidget',
    'ThrottleAnalysisDataLoader',
    # 分析模組管理器
    'AnalysisModuleManager',
    'get_analysis_module_manager'
]
