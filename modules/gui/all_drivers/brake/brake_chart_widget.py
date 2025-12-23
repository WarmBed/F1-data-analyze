#!/usr/bin/env python3
"""
煞車性能散點圖元件
Brake Performance Scatter Chart Widget

使用 Matplotlib 繪製煞車前速度-減速度散點圖
X軸: 煞車前速度 (km/h)
Y軸: 減速度 (m/s²) - 使用絕對值

每個車手用車隊顏色的點表示

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

from typing import Dict, List, Any, Optional
import numpy as np

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from core.gui_i18n import tr
from modules.gui.themes.color_palette_provider import (
    color_palette_provider,
    DEFAULT_DRIVER_MAP
)
from core.logger import get_logger

logger = get_logger("brake_chart_widget", component="gui")


class BrakeChartWidget(QWidget):
    """
    煞車性能散點圖元件
    
    視覺化:
    - X軸: 煞車前速度中位數 (km/h)
    - Y軸: 減速度中位數 (m/s²) - 使用絕對值
    - 每個車手用車隊顏色標記
    - 點大小根據一致性(CV)調整
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # 數據存儲
        self._drivers_data: List[Dict[str, Any]] = []
        
        # 初始化 Matplotlib 圖表
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 佈局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.canvas)
        
        # 初始化空白圖表
        self._init_empty_chart()
        
        logger.info("[BRAKE_CHART_WIDGET] Chart widget initialized")
    
    def _init_empty_chart(self):
        """初始化空白圖表"""
        self.ax.clear()
        self.ax.text(
            0.5, 0.5, 
            tr("waiting_for_data", "Waiting for data..."),
            ha='center', va='center',
            transform=self.ax.transAxes,
            fontsize=14, color='gray'
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def _get_driver_color_hex(self, driver_code: str) -> str:
        """
        獲取車手的車隊顏色（十六進制格式）
        
        Args:
            driver_code: 車手代碼
            
        Returns:
            十六進制顏色字串 (例如 '#FF0000')
        """
        try:
            color_palette_provider.ensure_loaded()
            qcolor = color_palette_provider.get_driver_color(driver_code, fallback=True)
            if isinstance(qcolor, QColor):
                return qcolor.name()
            return '#666666'
        except Exception:
            return '#666666'
    
    def _get_team_name(self, driver_code: str) -> str:
        """
        從 DEFAULT_DRIVER_MAP 獲取車隊名稱
        
        Args:
            driver_code: 車手代碼（如 VER, HAM）
            
        Returns:
            車隊名稱（如 Red Bull Racing, Mercedes）
        """
        team_map = {
            "red bull": "Red Bull Racing",
            "mclaren": "McLaren",
            "ferrari": "Ferrari",
            "mercedes": "Mercedes",
            "aston martin": "Aston Martin",
            "alpine": "Alpine",
            "williams": "Williams",
            "haas": "Haas F1 Team",
            "rb": "RB",
            "kick sauber": "Kick Sauber",
        }
        
        if driver_code in DEFAULT_DRIVER_MAP:
            team_key = DEFAULT_DRIVER_MAP[driver_code][0]
            return team_map.get(team_key, team_key.title())
        
        return "Unknown"
    
    def set_data(self, data: Dict[str, Any]):
        """
        設置數據並繪製圖表
        
        Args:
            data: API 返回的數據，包含 drivers 陣列
        """
        try:
            if not data or not isinstance(data, dict):
                logger.warning("[BRAKE_CHART_WIDGET] Invalid data format")
                return
            
            # 提取 drivers 數據
            drivers = data.get("drivers", [])
            if not drivers:
                drivers = data.get("data", {}).get("drivers", [])
            
            if not drivers:
                logger.warning("[BRAKE_CHART_WIDGET] No drivers data")
                self._init_empty_chart()
                return
            
            logger.info(f"[BRAKE_CHART_WIDGET] Setting data: {len(drivers)} drivers")
            
            self._drivers_data = drivers
            
            # 確保顏色數據已載入
            try:
                color_palette_provider.ensure_loaded()
            except Exception as e:
                logger.warning(f"[BRAKE_CHART_WIDGET] Color loading failed: {e}")
            
            # 繪製圖表
            self._plot_chart()
            
        except Exception as e:
            logger.exception(f"[BRAKE_CHART_WIDGET] Failed to set data: {e}")
    
    def _plot_chart(self):
        """繪製煞車前速度-減速度散點圖"""
        self.ax.clear()
        
        if not self._drivers_data:
            self._init_empty_chart()
            return
        
        # 收集所有車手的數據點
        plotted_drivers = []
        x_values = []  # 煞車前速度
        y_values = []  # 減速度（絕對值）
        
        for driver_data in self._drivers_data:
            driver_code = driver_data.get("driver", "N/A")
            
            # 獲取減速度統計
            brake_stats = driver_data.get("brake_decel_stats", {})
            entry_speed_stats = driver_data.get("entry_speed_stats", {})
            
            # 獲取中位數減速度（使用絕對值）
            median_decel = brake_stats.get("median")
            if median_decel is not None:
                median_decel = abs(float(median_decel))
            
            # 獲取中位數煞車前速度
            median_entry_speed = entry_speed_stats.get("median")
            
            # 如果沒有煞車前速度數據，跳過
            if median_decel is None or median_entry_speed is None:
                logger.debug(f"[BRAKE_CHART_WIDGET] Skipping {driver_code}: missing data")
                continue
            
            # 獲取 CV 用於點大小（一致性越高，CV 越低，點越大）
            cv = brake_stats.get("cv", 10)
            # 反轉：CV 越低 → 點越大
            point_size = max(80, min(250, 300 - cv * 10))
            
            # 獲取顏色
            color = self._get_driver_color_hex(driver_code)
            team = self._get_team_name(driver_code)
            
            # 繪製散點
            self.ax.scatter(
                median_entry_speed,  # X: 煞車前速度
                median_decel,        # Y: 減速度（絕對值）
                c=color,
                s=point_size,
                alpha=0.85,
                edgecolors='white',
                linewidths=1.5,
                label=f"{driver_code} ({team})",
                zorder=5
            )
            
            # 添加車手標籤
            self.ax.annotate(
                driver_code,
                (median_entry_speed, median_decel),
                xytext=(6, 6),
                textcoords='offset points',
                fontsize=9,
                fontweight='bold',
                color=color
            )
            
            plotted_drivers.append(driver_code)
            x_values.append(median_entry_speed)
            y_values.append(median_decel)
        
        if not plotted_drivers:
            logger.warning("[BRAKE_CHART_WIDGET] No valid data points to plot")
            self._init_empty_chart()
            return
        
        # 添加趨勢線（可選）
        if len(x_values) >= 3:
            try:
                z = np.polyfit(x_values, y_values, 1)
                p = np.poly1d(z)
                x_trend = np.linspace(min(x_values) - 5, max(x_values) + 5, 100)
                self.ax.plot(x_trend, p(x_trend), '--', color='gray', alpha=0.5, 
                           label=tr("trend_line", "Trend Line"), zorder=1)
            except Exception as e:
                logger.debug(f"[BRAKE_CHART_WIDGET] Trend line failed: {e}")
        
        # 設置圖表樣式
        self.ax.set_xlabel(
            tr("brake_chart_x_label", "Entry Speed (km/h)"),
            fontsize=12, fontweight='bold'
        )
        self.ax.set_ylabel(
            tr("brake_chart_y_label", "Deceleration (m/s^2)"),
            fontsize=12, fontweight='bold'
        )
        self.ax.set_title(
            tr("brake_chart_title", "Brake Performance - Entry Speed vs Deceleration"),
            fontsize=14, fontweight='bold', pad=15
        )
        
        # 添加註解說明
        self.ax.text(
            0.02, 0.98,
            tr("brake_chart_note", "Point size = Consistency (larger = more consistent)"),
            transform=self.ax.transAxes,
            fontsize=9, color='gray',
            verticalalignment='top'
        )
        
        # 網格
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.set_axisbelow(True)
        
        # 設置背景色
        self.ax.set_facecolor('#f8f9fa')
        self.figure.patch.set_facecolor('#ffffff')
        
        # 調整邊距 - 使用固定邊距避免小視窗時 Y 軸標籤被擠出
        self.figure.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12)
        
        # 重繪
        self.canvas.draw()
        
        logger.info(f"[BRAKE_CHART_WIDGET] Chart plotted: {len(plotted_drivers)} drivers")
    
    def clear(self):
        """清空圖表"""
        self._drivers_data = []
        self._init_empty_chart()


__all__ = ["BrakeChartWidget"]
