#!/usr/bin/env python3
"""
正賽預測模組
Race Prediction Module

提供基於排位賽數據和動態車隊評級的正賽成績預測功能
使用 Function 80 動態車隊評級系統進行預測

作者: F1T Team
日期: 2025-11-27
版本: 1.0.0
"""

__version__ = "1.0.0"

# 導出模組類別
from .race_prediction_mdi import RacePredictionMDI
from .race_prediction_data_loader import RacePredictionDataLoader
from .race_prediction_widget import RacePredictionWidget

__all__ = [
    'RacePredictionMDI',
    'RacePredictionDataLoader',
    'RacePredictionWidget',
]
