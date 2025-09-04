"""
GUI 基礎架構模組
================

提供GUI分析模組的基礎架構和介面定義。

主要組件：
- IAnalysisModule: 分析模組標準介面
- BaseAnalysisModule: 基礎分析模組實現
- ModuleFactory: 模組工廠
- ModuleTypes: 模組類型定義

Author: F1T Team
Date: 2025-09-04
Version: 1.0.0
"""

from .base_analysis_module import (
    IAnalysisModule,
    IParameterProvider,
    BaseAnalysisModule,
    ModuleSignals,
    ModuleFactory,
    ModuleTypes
)

__version__ = "1.0.0"
__author__ = "F1T Team"

__all__ = [
    'IAnalysisModule',
    'IParameterProvider', 
    'BaseAnalysisModule',
    'ModuleSignals',
    'ModuleFactory',
    'ModuleTypes'
]
