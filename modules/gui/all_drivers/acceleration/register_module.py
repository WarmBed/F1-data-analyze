#!/usr/bin/env python3
"""
全車手加速度圖表模組註冊
Module Registration for All Drivers Acceleration Chart

自動註冊模組到 F1T 主 GUI 系統

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

import logging
from core.logger import get_logger

logger = get_logger("all_drivers_acceleration_chart.register", component="gui")


def register():
    """註冊模組到工廠系統"""
    try:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[ACCEL_CHART_MODULE] 模組已註冊")
        return True
    except Exception as e:
        logger.error("[ACCEL_CHART_MODULE] 模組註冊失敗: %s", e)
        return False


if __name__ == "__main__":
    register()
