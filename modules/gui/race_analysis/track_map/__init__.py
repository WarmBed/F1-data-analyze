#!/usr/bin/env python3
"""
Historical Track Map Analysis Module
歷年賽道旗幟統計分析模組

提供賽道地圖與歷年旗幟統計的整合視覺化介面，類似 demo_fastf1_z_elevation.py 的功能。

特點:
- 賽道平面圖顯示 (TrackMapWidget)
- 高程剖面圖 (ElevationChartWidget)
- 歷年旗幟統計表格 (2022-2025)
- 彎道旗幟熱圖
- 僅使用 API 獲取數據，不支援本地 JSON 回退

數據來源: Function 100 (歷年旗幟統計)

Author: F1T Team
Date: 2025-11-11
Version: 1.0.0
"""

from .historical_track_map_mdi import HistoricalTrackMapMDI

__all__ = ["HistoricalTrackMapMDI"]
