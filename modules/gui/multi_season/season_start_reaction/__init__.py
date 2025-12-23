#!/usr/bin/env python3
"""
Season Start Reaction Analysis Module
=====================================

年度起跑反應分析模組，顯示全年度 0-50km/h 加速時間分布箱型圖。

作者: F1T Team
日期: 2025-12-22
版本: 2.0.0
"""

from .season_start_reaction_mdi import SeasonStartReactionAnalysis
from .season_start_reaction_chart_widget import SeasonStartReactionChartWidget

# 別名以保持向後相容
SeasonStartReactionMDI = SeasonStartReactionAnalysis

__all__ = [
    "SeasonStartReactionAnalysis",
    "SeasonStartReactionMDI",
    "SeasonStartReactionChartWidget",
]
