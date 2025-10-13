#!/usr/bin/env python3
"""
理想圈分析模組 - 共用顏色配置
Ideal Lap Analysis - Shared Color Configuration

統一 Ideal Lap Analysis 所有子模組的顏色配置，確保視覺一致性

作者: F1T Team
日期: 2025-10-10
版本: 1.0.0
"""

from PyQt5.QtGui import QColor
from typing import Dict


# ========== 車隊顏色 (2025 賽季 - 柔和版本) ==========
# 參考速度模組的柔和配色風格 (降低飽和度與亮度)
TEAM_COLORS: Dict[str, QColor] = {
    "Red Bull Racing": QColor(0, 80, 180),      # 柔和藍色 (原 #3671C6)
    "Ferrari": QColor(200, 50, 60),             # 柔和紅色 (原 #E8002D)
    "Mercedes": QColor(39, 180, 160),           # 柔和青色 (原 #27F4D2)
    "McLaren": QColor(200, 120, 0),             # 柔和橙色 (原 #FF8000)
    "Aston Martin": QColor(34, 130, 100),       # 柔和綠色 (原 #229971)
    "Alpine": QColor(200, 100, 160),            # 柔和粉色 (原 #FF87BC)
    "Williams": QColor(80, 160, 220),           # 柔和淺藍 (原 #64C4FF)
    "RB": QColor(80, 120, 200),                 # 柔和靛藍 (原 #6692FF)
    "Kick Sauber": QColor(60, 180, 60),         # 柔和螢光綠 (原 #52E252)
    "Haas F1 Team": QColor(140, 145, 150),      # 柔和灰色 (原 #B6BABD)
}


# ========== 差異顏色梯度 (理想圈 vs 最速圈) ==========

def get_gap_color(gap: float) -> QColor:
    """
    根據差異返回梯度顏色
    
    統一配色標準：
    - gap < 0.001: 淺綠色 (完美，無改善空間)
    - 0.001 ≤ gap < 0.2: 淺藍色 (小幅改善空間)
    - 0.2 ≤ gap < 0.5: 淺黃色 (中等改善空間)
    - gap ≥ 0.5: 淺紅色 (明顯改善空間)
    
    Args:
        gap: 差異（秒）
        
    Returns:
        QColor: 顏色
    """
    abs_gap = abs(gap)
    
    if abs_gap < 0.001:
        # 完美分段：淺綠色
        return QColor(144, 238, 144)  # LightGreen
    elif abs_gap < 0.2:
        # 小幅改善空間：淺藍色（溫和）
        return QColor(173, 216, 230)  # LightBlue
    elif abs_gap < 0.5:
        # 中等改善空間：淺黃色
        return QColor(255, 255, 153)  # LightYellow
    else:
        # 明顯改善空間：淺紅色
        return QColor(255, 182, 193)  # LightPink


# ========== 競爭力顏色 (與全場最速差距) ==========

def get_competitiveness_color(gap: float) -> QColor:
    """
    根據與全場最速的差距返回競爭力顏色
    
    統一配色標準：
    - gap < 0.5: 深綠色 (極具競爭力)
    - 0.5 ≤ gap < 1.0: 淺綠色 (具競爭力)
    - 1.0 ≤ gap < 2.0: 淺黃色 (中等競爭力)
    - gap ≥ 2.0: 淺紅色 (競爭力不足)
    
    Args:
        gap: 與全場最速的差距（秒）
        
    Returns:
        QColor: 顏色
    """
    abs_gap = abs(gap)
    
    if abs_gap < 0.5:
        return QColor(34, 139, 34)    # ForestGreen (極具競爭力)
    elif abs_gap < 1.0:
        return QColor(144, 238, 144)  # LightGreen (具競爭力)
    elif abs_gap < 2.0:
        return QColor(255, 255, 153)  # LightYellow (中等競爭力)
    else:
        return QColor(255, 182, 193)  # LightPink (競爭力不足)


# ========== 累積差異棒狀圖顏色 ==========

def get_cumulative_bar_color(cumulative: float) -> QColor:
    """
    累積差異棒狀圖顏色
    
    統一配色標準：
    - cumulative ≤ 0.05: 綠色 (幾乎完美)
    - 0.05 < cumulative ≤ 0.2: 黃色 (小幅改善空間)
    - cumulative > 0.2: 紅色 (明顯改善空間)
    
    Args:
        cumulative: 累積差異（秒）
        
    Returns:
        QColor: 顏色（含透明度）
    """
    if cumulative <= 0.050:
        return QColor(100, 200, 100, 200)  # 綠色
    elif cumulative <= 0.200:
        return QColor(255, 200, 100, 200)  # 黃色
    else:
        return QColor(255, 100, 100, 200)  # 紅色


# ========== 輔助函數 ==========

def get_team_color(team: str) -> QColor:
    """
    獲取車隊顏色
    
    Args:
        team: 車隊名稱
        
    Returns:
        QColor: 車隊顏色（預設灰色）
    """
    return TEAM_COLORS.get(team, QColor(128, 128, 128))
