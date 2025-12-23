"""
輪胎策略分析模組
Tire Strategy Analysis Module

提供完整的 F1 輪胎策略分析功能，整合：
- FastF1 資料載入
- 智能快取管理  
- 統一 JSON 輸出
- CLI -f26 支援

主要功能:
- 單一車手輪胎策略分析
- 所有車手輪胎策略分析
- Stint 分析和換胎時機檢測
- 輪胎配方使用統計

作者: F1 Analysis Team
版本: 3.0
"""

from .tire_strategy_cli import (
    TireStrategyAnalyzer,
    run_tire_strategy_analysis,
    run_fastf1_tire_strategy_analysis,
    run_tire_change_timing_inference
)

__all__ = [
    'TireStrategyAnalyzer',
    'run_tire_strategy_analysis', 
    'run_fastf1_tire_strategy_analysis',
    'run_tire_change_timing_inference'
]

__version__ = "3.0"
__author__ = "F1 Analysis Team"
