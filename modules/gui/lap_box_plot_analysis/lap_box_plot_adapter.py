#!/usr/bin/env python3
"""
LapTimeBoxPlotAnalysisAdapter - Lap Box Plot Workspace Adapter
============================================================

Workspace-safe adapter for Lap Time Box Plot Analysis module.
完全模仿 RainAnalysisModuleAdapter 的三層隔離架構。

架構模式：
    Adapter → Module → MDI (UniversalAnalysisMDI)

安全特性：
    - 只接受參數並傳遞給 MDI
    - 不調用 update_parameters()（避免執行緒啟動）
    - 適用於 Workspace 快速重建場景

Author: F1T Team
Date: 2025-10-22
Version: 1.0.0
"""

from typing import Optional
from PyQt5.QtCore import QObject

from core.logger import get_logger
logger = get_logger(__name__)

# 導入 MDI 類別
try:
    from .lap_box_plot_analysis_mdi import LapTimeBoxPlotAnalysis
except ImportError:
    from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import LapTimeBoxPlotAnalysis


class LapTimeBoxPlotAnalysisAdapter(QObject):
    """
    圈速盒鬚圖分析模組適配器
    
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
        super().__init__(parent)
        
        # 提取參數
        year = kwargs.get('year')
        race = kwargs.get('race')
        session = kwargs.get('session')
        
        logger.debug(f"[LAP_BOXPLOT_ADAPTER] 初始化 Adapter: year={year}, race={race}, session={session}")
        
        # 創建內部 MDI 實例
        self._mdi_core = LapTimeBoxPlotAnalysis(parent=parent)
        
        # ✅ 只設置參數屬性，不調用 update_parameters()（避免啟動執行緒）
        if year is not None and hasattr(self._mdi_core, 'current_year'):
            self._mdi_core.current_year = str(year)
        if race is not None and hasattr(self._mdi_core, 'current_race'):
            self._mdi_core.current_race = race
        if session is not None and hasattr(self._mdi_core, 'current_session'):
            self._mdi_core.current_session = session
        
        # 參數提供者（由外部設置）
        self._mdi_core.parameter_provider = None
        
        # 適配器版本
        self.adapter_version = "1.0.0"
        
        logger.info(f"[LAP_BOXPLOT_ADAPTER] Adapter 初始化完成")
    
    def get_widget(self):
        """返回內部 MDI 的 Widget（不是 MDI 對象本身）"""
        if hasattr(self._mdi_core, 'get_widget'):
            # MDI 有 get_widget() 方法，調用它獲取真正的 QWidget
            return self._mdi_core.get_widget()
        elif hasattr(self._mdi_core, 'main_widget'):
            # 回退：直接獲取 main_widget 屬性
            return self._mdi_core.main_widget
        else:
            # 最後回退：返回 MDI 對象（可能不work）
            logger.warning(f"[LAP_BOXPLOT_ADAPTER] ⚠️  MDI 沒有 get_widget() 或 main_widget，返回 MDI 對象")
            return self._mdi_core
    
    def __getattr__(self, name):
        """代理所有未定義的屬性和方法到內部 MDI"""
        return getattr(self._mdi_core, name)


# 導出
__all__ = ['LapTimeBoxPlotAnalysisAdapter']
