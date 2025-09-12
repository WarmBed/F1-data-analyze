#!/usr/bin/env python3
"""
輪胎策略分析模組套件
driverLap Analysis Module Package

包含所有與F1輪胎策略分析相關的GUI組件和分析工具
Contains all GUI components and analysis tools related to F1 driverLap strategy analysis

基於通用 MDI 架構實現，提供：
- 輪胎配方策略分析
- Stint 時間分析和比較  
- 橫向長條圖視覺化
- CLI -f26 數據生成
- 車手輪胎策略追蹤

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

# 主要模組匯出
try:
    from .driverLap_analysis_module import RainAnalysisModule
    from .driverLap_analysis_mdi import RainAnalysisUniversal, RainAnalysisDataManager
    from .driverLap_analysis_chart_widget import RainAnalysisChartWidget, RainChartTheme
    from .driverLap_data_loader import RainDataLoader, create_driverLap_data_loader
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
    'create_driverLap_data_loader'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "F1T Team"
__date__ = "2025-09-10"
__description__ = "F1 下雨分析 GUI 模組套件 - 基於通用 MDI 架構"

# 便利函數
def create_driverLap_analysis_module(parent=None):
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

def create_driverLap_data_loader_instance(parent=None):
    """
    創建下雨數據載入器實例
    
    Args:
        parent: 父級 QObject
        
    Returns:
        RainDataLoader: 下雨數據載入器實例
    """
    if RainDataLoader is not None:
        return create_driverLap_data_loader(parent)
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
