#!/usr/bin/env python3
"""
輪胎策略分析模組套件
Tire Analysis Module Package

包含所有與F1輪胎策略分析相關的GUI組件和分析工具
Contains all GUI components and analysis tools related to F1 tire strategy analysis

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
    from .tire_analysis_module import TireAnalysisModule
    from .tire_analysis_mdi import TireAnalysisUniversal, TireAnalysisDataManager
    from .tire_analysis_chart_widget import TireAnalysisChartWidget, TireChartTheme
except ImportError as e:
    print(f"[WARNING] 輪胎策略分析模組導入部分失敗: {str(e)}")
    # 提供向後兼容性
    TireAnalysisModule = None
    TireAnalysisUniversal = None

__all__ = [
    'TireAnalysisModule',
    'TireAnalysisUniversal', 
    'TireAnalysisDataManager',
    'TireAnalysisChartWidget',
    'TireChartTheme'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "F1T Team"
__date__ = "2025-09-10"
__description__ = "F1 輪胎策略分析 GUI 模組套件 - 基於通用 MDI 架構"

# 便利函數
def create_tire_analysis_module(parent=None):
    """
    創建輪胎策略分析模組實例
    
    Args:
        parent: 父級 QObject
        
    Returns:
        TireAnalysisModule: 輪胎策略分析模組實例
    """
    if TireAnalysisModule is not None:
        return TireAnalysisModule(parent)
    else:
        raise ImportError("TireAnalysisModule 未能正確導入")

def create_tire_data_loader_instance(parent=None):
    """
    創建輪胎策略數據載入器實例 - 已廢棄
    
    Args:
        parent: 父級 QObject
        
    Returns:
        None: 此功能已整合到 TireAnalysisDataManager 中
    """
    print("[WARNING] create_tire_data_loader_instance 已廢棄，請使用 TireAnalysisDataManager")
    return None

def get_module_info():
    """獲取模組信息"""
    return {
        "name": "輪胎策略分析模組",
        "version": __version__,
        "author": __author__,
        "date": __date__,
        "description": __description__
    }
