#!/usr/bin/env python3
"""
溫度分析模組套件
Temperature Analysis Module Package

包含所有與F1溫度分析相關的GUI組件和分析工具
Contains all GUI components and analysis tools related to F1 temperature analysis

基於通用 MDI 架構實現，提供：
- 氣溫變化分析
- 賽道溫度追蹤
- 風速監測
- 降雨狀態顯示
- 雙Y軸圖表支援

Author: F1T Team
Date: 2025-12-21
Version: 2.0.0
"""

# 主要模組匯出
from core.logger import get_logger


logger = get_logger(component="temp_analysis_init")

try:
    from .temp_analysis_module import TempAnalysisModule
    from .temp_analysis_mdi import TempAnalysisUniversal, TempAnalysisDataManager
    from .temp_analysis_chart_widget import TempAnalysisChartWidget, TempChartTheme
except ImportError as e:
    logger.warning("[WARNING] 溫度分析模組導入部分失敗: %s", e)
    # 提供向後兼容性
    TempAnalysisModule = None
    TempAnalysisUniversal = None

__all__ = [
    'TempAnalysisModule',
    'TempAnalysisUniversal', 
    'TempAnalysisDataManager',
    'TempAnalysisChartWidget',
    'TempChartTheme'
]

# 版本信息
__version__ = "2.0.0"
__author__ = "F1T Team"
__date__ = "2025-12-21"
__description__ = "F1 溫度分析 GUI 模組套件 - 基於通用 MDI 架構"

# 便利函數
def create_temp_analysis_module(parent=None):
    """
    創建溫度分析模組實例
    
    Args:
        parent: 父級 QObject
        
    Returns:
        TempAnalysisModule: 溫度分析模組實例
    """
    if TempAnalysisModule is not None:
        return TempAnalysisModule(parent)
    else:
        raise ImportError("TempAnalysisModule 未能正確導入")

def get_module_info():
    """獲取模組信息"""
    return {
        "name": "溫度分析模組",
        "version": __version__,
        "author": __author__,
        "date": __date__,
        "description": __description__
    }
