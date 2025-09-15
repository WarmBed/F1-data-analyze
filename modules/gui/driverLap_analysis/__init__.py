#!/usr/bin/env python3
"""
詳細圈速分析模組套件
Driver Lap Analysis Module Package

包含所有與F1詳細圈速分析相關的GUI組件和分析工具
Contains all GUI components and analysis tools related to F1 detailed lap time analysis

基於通用 MDI 架構實現，提供：
- 詳細圈速趨勢分析（每圈秒數顯示）
- 車手選擇控制區（最多5位車手同時比較）
- 智能標記系統（事故A、降雨R、進站P、最快圈F等）
- 輪胎策略時間軸（底部顯示各車手輪胎使用情況）
- 折線圖視覺化分析
- CLI -f28 數據生成

Author: F1T Team
Date: 2025-09-15
Version: 2.0.0
"""

# 主要模組匯出
try:
    from .driverlap_analysis_module import driverLapAnalysisModule
    from .driverlap_analysis_mdi import driverLapAnalysisMDI, driverLapAnalysisDataManager
    from .driverlap_analysis_chart_widget import driverLapAnalysisChartWidget
    # 移除已廢棄的 driverlap_data_loader 依賴
    print(f"[OK] 詳細圈速分析模組 - 整合架構載入成功")
except ImportError as e:
    print(f"[WARNING] 詳細圈速分析模組導入部分失敗: {str(e)}")
    # 提供向後兼容性
    driverLapAnalysisModule = None
    driverLapAnalysisMDI = None
    driverLapAnalysisDataManager = None

__all__ = [
    'driverLapAnalysisModule',
    'driverLapAnalysisMDI', 
    'driverLapAnalysisDataManager',
    'driverLapAnalysisChartWidget'
]

# 版本信息
__version__ = "2.0.0"
__author__ = "F1T Team"
__date__ = "2025-09-15"
__description__ = "F1 詳細圈速分析 GUI 模組套件 - 基於通用 MDI 架構"

# 便利函數
def create_driverLap_analysis_module(parent=None):
    """
    創建詳細圈速分析模組實例
    
    Args:
        parent: 父級 QObject
        
    Returns:
        driverLapAnalysisModule: 詳細圈速分析模組實例
    """
    if driverLapAnalysisModule is not None:
        return driverLapAnalysisModule(parent)
    else:
        raise ImportError("driverLapAnalysisModule 未能正確導入")

def create_driverLap_data_manager(parent=None):
    """
    創建詳細圈速數據管理器實例（整合架構）
    
    Args:
        parent: 父級 QObject
        
    Returns:
        driverLapAnalysisDataManager: 詳細圈速數據管理器實例
    """
    if driverLapAnalysisDataManager is not None:
        return driverLapAnalysisDataManager(parent)
    else:
        raise ImportError("driverLapAnalysisDataManager 未能正確導入")

def get_module_info():
    """獲取模組信息"""
    return {
        "name": "詳細圈速分析模組",
        "version": __version__,
        "author": __author__,
        "date": __date__,
        "description": __description__
    }
