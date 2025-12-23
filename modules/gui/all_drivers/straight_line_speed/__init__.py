#!/usr/bin/env python3
"""
All Drivers Straight Line Speed Analysis Module
全車手直線速度與加速性能分析模組

提供全車手的最高速度和 100-300km/h 加速性能分析
使用水平長條圖和垂直長條圖展示分析結果

作者: F1T Team
日期: 2025-10-14
版本: 1.0.0
"""

__version__ = "1.0.0"

# 導出模組類別（延遲載入，避免 Matplotlib 初始化阻塞）
# from .all_drivers_straight_line_speed_widget import AllDriversStraightLineSpeedWidget  # 延遲載入
from .all_drivers_straight_line_speed_module import AllDriversStraightLineSpeedModule
from .all_drivers_straight_line_speed_mdi import AllDriversStraightLineSpeedMDI

__all__ = [
    "AllDriversStraightLineSpeedModule",
    "AllDriversStraightLineSpeedMDI",
    # "AllDriversStraightLineSpeedWidget",  # 延遲載入，需要時才 import
]

# 自動註冊模組到工廠
try:
    from .register_module import register
    register()
except Exception as e:
    print(f"⚠️  AllDriversStraightLineSpeed 自動註冊失敗: {e}")
