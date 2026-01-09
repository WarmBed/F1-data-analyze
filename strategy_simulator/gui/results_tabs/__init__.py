#!/usr/bin/env python3
"""
Result tabs for Race Strategy Simulator.
"""

from .strategy_comparison import StrategyComparisonTab
from .lap_curves import LapCurvesTab
from .safety_car_tab import SafetyCarTab
from .opponent_tab import OpponentTab
from .detailed_data import DetailedDataTab
from .fp2_prediction_tab import FP2PredictionTab
# from .position_analysis_tab import PositionAnalysisTab  # ❌ 已移除
from .full_race_tab import FullRaceTab
from .race_result_analysis_tab import RaceResultAnalysisTab

__all__ = [
    'StrategyComparisonTab',
    'LapCurvesTab',
    'SafetyCarTab',
    'OpponentTab',
    'DetailedDataTab',
    'FP2PredictionTab',
    # 'PositionAnalysisTab',  # ❌ 已移除
    'FullRaceTab',
    'RaceResultAnalysisTab',
]
