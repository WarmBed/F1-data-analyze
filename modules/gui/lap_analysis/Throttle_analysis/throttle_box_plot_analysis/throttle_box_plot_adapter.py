#!/usr/bin/env python3
"""
ThrottleBoxPlotAnalysisAdapter - Throttle Box Plot Workspace Adapter
==================================================================

Workspace-safe adapter for Throttle Box Plot Analysis module.
完全模仿 RainAnalysisModuleAdapter 的三層隔離架構。

架構模式：
    Adapter → Module → MDI (UniversalAnalysisMDI)

安全特性：
    - 只接受參數並傳遞給 Module
    - 不調用 update_parameters()（避免執行緒啟動）
    - 適用於 Workspace 快速重建場景

Author: F1T Team
Date: 2025-10-22
Version: 1.0.0
"""

from typing import Optional
from core.logger import get_logger

# 導入 Module 類別
try:
    from .throttle_box_plot_analysis_module import ThrottleBoxPlotAnalysisModule
except ImportError:
    from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module import ThrottleBoxPlotAnalysisModule


logger = get_logger("throttle_box_plot_adapter", component="gui")


class ThrottleBoxPlotAnalysisAdapter(ThrottleBoxPlotAnalysisModule):
    """
    油門盒鬚圖分析模組適配器
    
    為了與主 GUI 的工廠模式和 Workspace 系統兼容而提供的適配器類別。
    """
    
    def __init__(self, parent=None, **kwargs):
        """
        初始化適配器
        
        Args:
            parent: 父級 QObject
            **kwargs: 關鍵字參數，支援：
                - year: 賽季年份
                - race: 賽事名稱
                - session: 賽段類型
        """
        # 提取參數
        year = kwargs.get('year')
        race = kwargs.get('race')
        session = kwargs.get('session')
        
        logger.info("🚀 [THROTTLE_BOXPLOT_ADAPTER] 初始化 Adapter: year=%s, race=%s, session=%s", year, race, session)
        
        # 呼叫父類建構函數（ThrottleBoxPlotAnalysisModule）
        super().__init__(parent, year, race, session)
        
        # 適配器版本
        self.adapter_version = "1.0.0"
        
        logger.info("✅ [THROTTLE_BOXPLOT_ADAPTER] Adapter 初始化完成")


# 導出
__all__ = ['ThrottleBoxPlotAnalysisAdapter']
