#!/usr/bin/env python3
"""
F1T 車手分析 GUI 模組包
Driver Analysis GUI Module Package

包含完整的車手分析功能模組：
- 車手數據統計總覽
- 車手遙測資料統計
- 車手綜合分析
"""

# 車手統計模組
from .driver_statistics_overview import run_driver_statistics_overview

# 車手遙測統計模組  
from .driver_telemetry_statistics import *

# 車手綜合分析模組
from .driver_comprehensive_full import *

__all__ = [
    'run_driver_statistics_overview',
    # 其他導出的函數會在這裡列出
]

__version__ = '2.0.0'
__author__ = 'F1T Development Team'
__description__ = 'F1 車手分析 GUI 模組包'
