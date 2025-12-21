#!/usr/bin/env python3
"""
全車手煞車圖表模組
All Drivers Brake Chart Module

提供模組元數據和工廠整合接口

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

from core.logger import get_logger
logger = get_logger("all_drivers_brake_chart_module", component="gui")


class AllDriversBrakeChartModule:
    """
    全車手煞車圖表模組
    
    提供:
    - 模組元數據
    - 視窗創建接口
    """
    
    # 模組元數據
    MODULE_ID = "all_drivers_brake_chart"
    MODULE_NAME = "All Drivers Brake Chart"
    MODULE_VERSION = "1.0.0"
    
    # 功能配置
    FUNCTION_ID = "122"  # 使用 F122 API
    REQUIRES_DRIVER = False
    REQUIRES_LAP = False
    
    @classmethod
    def get_module_info(cls) -> dict:
        """獲取模組資訊"""
        return {
            "id": cls.MODULE_ID,
            "name": cls.MODULE_NAME,
            "version": cls.MODULE_VERSION,
            "function_id": cls.FUNCTION_ID,
            "requires_driver": cls.REQUIRES_DRIVER,
            "requires_lap": cls.REQUIRES_LAP,
            "description": "Entry Speed vs Deceleration chart for all drivers"
        }
    
    @classmethod
    def create_mdi_window(cls, parent=None, **kwargs):
        """
        創建 MDI 視窗實例
        
        Args:
            parent: 父元件
            **kwargs: 額外參數
            
        Returns:
            AllDriversBrakeChartMDI: MDI 視窗實例
        """
        from .brake_chart_mdi import AllDriversBrakeChartMDI
        
        mdi = AllDriversBrakeChartMDI(parent=parent)
        
        # 設置參數
        for key, value in kwargs.items():
            if hasattr(mdi, key):
                setattr(mdi, key, value)
        
        return mdi


__all__ = ["AllDriversBrakeChartModule"]
