#!/usr/bin/env python3
"""
F1T 事故分析 GUI 模組包
Accident Analysis GUI Module Package

包含完整的事故分析功能模組：
- 主要 MDI 事故分析介面
- 統計摘要與可視化
- 嚴重程度分析
- 車隊風險評估
- 特殊事故事件分析
"""

# 主要事故分析模組
from .accident_analysis_mdi import AccidentAnalysisModule

# 完整分析功能
from .accident_analysis_complete import *

# 統計與摘要模組
from .accident_statistics_summary import *

# 專門分析模組
from .severity_distribution_analysis import *
from .team_risk_analysis import *
from .all_incidents_analysis import *
from .special_incidents_analysis import *

# 核心分析功能
from .accident_analysis import *

# 簡化版模組（備用）
# from .accident_analysis_mdi_simple import *

__all__ = [
    'AccidentAnalysisModule',
    # 其他導出的類別和函數會在這裡列出
]

__version__ = '2.0.0'
__author__ = 'F1T Development Team'
__description__ = 'F1 事故分析 GUI 模組包'
