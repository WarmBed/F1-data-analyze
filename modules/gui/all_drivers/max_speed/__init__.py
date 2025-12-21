#!/usr/bin/env python3
"""
All Drivers Max Speed Analysis Module
全車手最高速度分析模組

使用 F121 API 提供全車手的最高速度和加速性能統計分析
支援所有會話類型 (FP1/FP2/FP3/Q/R)

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

__version__ = "1.0.0"

# 導出模組類別
from .all_drivers_max_speed_mdi import AllDriversMaxSpeedMDI
from .all_drivers_max_speed_module import AllDriversMaxSpeedModule

from core.logger import get_logger
logger = get_logger(__name__)

__all__ = [
    "AllDriversMaxSpeedModule",
    "AllDriversMaxSpeedMDI",
]

# 自動註冊模組到工廠
try:
    logger = get_logger("all_drivers_max_speed_analysis", component="gui")
    from .register_module import register
    register()
except Exception as e:
    logger.warning("AllDriversMaxSpeed 自動註冊失敗: %s", e)
