#!/usr/bin/env python3
"""
FIA Parts Analysis Module
==========================

FIA 部件變更分析模組 - 完全基於 API 的實現

模組結構：
- parts_analysis_mdi.py: MDI 視窗管理器（API Worker）
- parts_analysis_widget.py: 主要表格元件
- parts_analysis_data_loader.py: 數據載入器（備援用）

作者: F1T Team
日期: 2025-11-08
版本: 1.0.0
"""

from .parts_analysis_mdi import PartsAnalysisMDI
from .parts_analysis_widget import PartsAnalysisWidget

__all__ = ['PartsAnalysisMDI', 'PartsAnalysisWidget']
