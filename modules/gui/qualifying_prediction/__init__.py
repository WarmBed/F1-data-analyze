#!/usr/bin/env python3
"""
排位賽預測模組
Qualifying Prediction Module

提供基於機器學習模型的排位賽成績預測功能

作者: F1T Team
日期: 2025-11-05
版本: 1.0.0
"""

__version__ = "1.0.0"

# 導出模組類別
from .qualifying_prediction_mdi import QualifyingPredictionMDI
from .qualifying_prediction_data_loader import QualifyingPredictionDataLoader
from .qualifying_prediction_widget import QualifyingPredictionWidget

__all__ = [
    'QualifyingPredictionMDI',
    'QualifyingPredictionDataLoader',
    'QualifyingPredictionWidget',
]
