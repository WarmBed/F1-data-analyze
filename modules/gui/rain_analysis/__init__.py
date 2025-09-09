#!/usr/bin/env python3
"""
降雨分析模組套件
Rain Analysis Module Package

包含所有與F1降雨分析相關的GUI組件和分析工具
Contains all GUI components and analysis tools related to F1 rain analysis

基於通用 MDI 架構實現，提供：
- 降雨狀態分析
- 溫度變化追蹤
- 濕度和風速監測
- 氣壓變化分析
- 多種圖表類型支援

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

# 主要模組匯出
try:
    from .rain_analysis_module import RainAnalysisModule
    from .rain_analysis_mdi import RainAnalysisUniversal, RainAnalysisDataManager
    from .rain_analysis_chart_widget import RainAnalysisChartWidget, RainChartTheme
    from .rain_data_loader import RainDataLoader, create_rain_data_loader
except ImportError as e:
    print(f"[WARNING] 下雨分析模組導入部分失敗: {str(e)}")
    # 提供向後兼容性
    RainAnalysisModule = None
    RainAnalysisUniversal = None
    RainDataLoader = None

__all__ = [
    'RainAnalysisModule',
    'RainAnalysisUniversal', 
    'RainAnalysisDataManager',
    'RainAnalysisChartWidget',
    'RainChartTheme',
    'RainDataLoader',
    'create_rain_data_loader'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "F1T Team"
__date__ = "2025-09-10"
__description__ = "F1 下雨分析 GUI 模組套件 - 基於通用 MDI 架構"

# 便利函數
def create_rain_analysis_module(parent=None):
    """
    創建下雨分析模組實例
    
    Args:
        parent: 父級 QObject
        
    Returns:
        RainAnalysisModule: 下雨分析模組實例
    """
    if RainAnalysisModule is not None:
        return RainAnalysisModule(parent)
    else:
        raise ImportError("RainAnalysisModule 未能正確導入")

def create_rain_data_loader_instance(parent=None):
    """
    創建下雨數據載入器實例
    
    Args:
        parent: 父級 QObject
        
    Returns:
        RainDataLoader: 下雨數據載入器實例
    """
    if RainDataLoader is not None:
        return create_rain_data_loader(parent)
    else:
        raise ImportError("RainDataLoader 未能正確導入")

def get_module_info():
    """獲取模組信息"""
    return {
        "name": "下雨分析模組",
        "version": __version__,
        "author": __author__,
        "date": __date__,
        "description": __description__
    }
