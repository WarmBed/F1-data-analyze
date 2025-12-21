#!/usr/bin/env python3
"""
All Drivers Acceleration Chart Module
全車手加速度圖表分析模組

使用 F121 API 提供全車手的速度-加速度圖表視覺化
X軸: 速度 (km/h)
Y軸: 加速度 (m/s^2)

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

__version__ = "1.0.0"

# 導出模組類別
from .acceleration_chart_mdi import AllDriversAccelerationChartMDI
from .acceleration_chart_module import AllDriversAccelerationChartModule

# 別名 (為了相容性)
AccelerationChartMDI = AllDriversAccelerationChartMDI
AccelerationChartModule = AllDriversAccelerationChartModule

from core.logger import get_logger
logger = get_logger(__name__)

__all__ = [
    "AllDriversAccelerationChartModule",
    "AllDriversAccelerationChartMDI",
    "AccelerationChartMDI",
    "AccelerationChartModule",
]

# 自動註冊模組到工廠
try:
    logger = get_logger("all_drivers_acceleration_chart", component="gui")
    from .register_module import register
    register()
except Exception as e:
    logger.warning("AllDriversAccelerationChart 自動註冊失敗: %s", e)
