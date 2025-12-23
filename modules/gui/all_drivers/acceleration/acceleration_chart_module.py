#!/usr/bin/env python3
"""
全車手加速度圖表模組
All Drivers Acceleration Chart Module

提供模組元數據和工廠整合接口

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

from core.logger import get_logger
logger = get_logger("all_drivers_acceleration_chart_module", component="gui")


class AllDriversAccelerationChartModule:
    """
    全車手加速度圖表模組
    
    提供:
    - 模組元數據
    - 視窗創建接口
    """
    
    # 模組元數據
    MODULE_ID = "all_drivers_acceleration_chart"
    MODULE_NAME = "All Drivers Acceleration Chart"
    MODULE_VERSION = "1.0.0"
    
    # 功能配置
    FUNCTION_ID = "121"  # 使用 F121 API
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
            "description": "Speed vs Acceleration chart for all drivers"
        }
    
    @classmethod
    def create_mdi_window(cls, parent=None, **kwargs):
        """
        創建 MDI 視窗實例
        
        Args:
            parent: 父元件
            **kwargs: 額外參數
            
        Returns:
            AllDriversAccelerationChartMDI: MDI 視窗實例
        """
        from .acceleration_chart_mdi import AllDriversAccelerationChartMDI
        
        mdi = AllDriversAccelerationChartMDI(parent=parent)
        
        # 設置參數
        for key, value in kwargs.items():
            if hasattr(mdi, key):
                setattr(mdi, key, value)
        
        return mdi


__all__ = ["AllDriversAccelerationChartModule"]
