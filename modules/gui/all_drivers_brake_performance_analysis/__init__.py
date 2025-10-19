#!/usr/bin/env python3
"""
All Drivers Brake Performance Analysis Module
全車手煞車性能分析模組

提供全車手的最大減速度、煞車距離和煞車時間分析
使用表格和圖表展示分析結果

作者: F1T Team
日期: 2025-10-18
版本: 1.0.0
"""

__version__ = "1.0.0"

# 導出模組類別（延遲載入，避免 Matplotlib 初始化阻塞）
# from .all_drivers_brake_performance_widget import AllDriversBrakePerformanceWidget  # 延遲載入
from .all_drivers_brake_performance_module import AllDriversBrakePerformanceModule
from .all_drivers_brake_performance_mdi import AllDriversBrakePerformanceMDI
from .all_drivers_brake_performance_table_widget import AllDriversBrakePerformanceTableWidget

__all__ = [
    "AllDriversBrakePerformanceModule",
    "AllDriversBrakePerformanceMDI",
    "AllDriversBrakePerformanceTableWidget",
    # "AllDriversBrakePerformanceWidget",  # 延遲載入，需要時才 import
]

# 自動註冊模組到工廠
try:
    from .register_module import register
    register()
except Exception as e:
    print(f"AllDriversBrakePerformance 自動註冊失敗: {e}")

