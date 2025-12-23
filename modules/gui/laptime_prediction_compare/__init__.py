"""
Laptime Prediction Compare Module - 三曲線對比分析

功能: 比較三種圈速預測方法
- Real: 實際比賽圈速
- F57: 燃油+輪胎模型預測
- F91: 機器學習模型預測 (FP2→Race)

版本: 1.0.0
日期: 2025-12-13
"""

from .laptime_prediction_compare_mdi import LaptimePredictionCompareMDI

__all__ = ["LaptimePredictionCompareMDI"]
