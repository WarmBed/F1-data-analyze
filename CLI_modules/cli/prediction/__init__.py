"""
CLI Prediction Module

此模組包含 FP->Q->R 預測系統的數據收集和模型訓練功能

功能列表:
- 功能 70: FP->Q 訓練數據收集器
- 功能 71: Q->R 訓練數據收集器 (規劃中)
- 功能 72: XGBoost 模型訓練器 (規劃中)
- 功能 73: 混合預測器 (規劃中)
- 功能 86: 省輪胎行為分析
- 功能 87: 車手策略預測器
"""

from .fp_q_data_collector import FPQDataCollector
from .tire_saving_analyzer import TireSavingAnalyzer, run_tire_saving_analysis
from .driver_strategy_predictor import DriverStrategyPredictor, run_driver_strategy_prediction

__all__ = [
    'FPQDataCollector',
    'TireSavingAnalyzer',
    'run_tire_saving_analysis',
    'DriverStrategyPredictor',
    'run_driver_strategy_prediction',
]
