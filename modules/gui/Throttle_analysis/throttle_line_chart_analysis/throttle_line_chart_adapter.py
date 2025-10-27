#!/usr/bin/env python3
"""
ThrottleLineChartAdapter - Throttle Line Chart Workspace Adapter
==============================================================

Workspace-safe adapter for Throttle Line Chart Analysis module.
完全模仿 RainAnalysisModuleAdapter 的三層隔離架構。

架構模式：
    Adapter → Module → Widget

安全特性：
    - 只接受參數並傳遞給 Module
    - 不調用 update_parameters()（避免執行緒啟動）
    - 適用於 Workspace 快速重建場景

Author: F1T Team
Date: 2025-10-22
Version: 1.0.0
"""

from typing import Optional

# 導入 Module 類別
try:
    from .throttle_line_chart_module import ThrottleLineChartModule
except ImportError:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import ThrottleLineChartModule


class ThrottleLineChartAdapter(ThrottleLineChartModule):
    """
    油門折線圖分析模組適配器
    
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
        
        print(f"🚀 [THROTTLE_LINE_ADAPTER] 初始化 Adapter: year={year}, race={race}, session={session}")
        
        # 呼叫父類建構函數（ThrottleLineChartModule）
        super().__init__(parent, year, race, session)
        
        # 適配器版本
        self.adapter_version = "1.0.0"
        
        print(f"✅ [THROTTLE_LINE_ADAPTER] Adapter 初始化完成")


# 導出
__all__ = ['ThrottleLineChartAdapter']
