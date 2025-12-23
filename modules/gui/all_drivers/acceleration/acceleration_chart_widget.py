#!/usr/bin/env python3
"""
全車手加速度圖表元件
All Drivers Acceleration Chart Widget

使用 Matplotlib 繪製速度-加速度散點圖
X軸: 速度 (km/h)
Y軸: 加速度 (m/s^2)

每個車手用不同顏色的點表示

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

logger = get_logger("acceleration_chart_widget", component="gui")


class AccelerationChartWidget(QWidget):
    """
    全車手加速度圖表元件
    
    視覺化:
    - X軸: 速度 (km/h) - 從起始速度(100)到目標速度(300/280/270)
    - Y軸: 加速度 (m/s^2)
    - 每個車手用車隊顏色標記
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
        
        logger.info("[ACCEL_CHART_WIDGET] 圖表元件初始化完成")
    
    def _init_empty_chart(self):
        """初始化空白圖表"""
        self.ax.clear()
        self.ax.text(
            0.5, 0.5, 
            tr("Waiting for data...", "Waiting for data..."),
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
        從 ColorPaletteProvider 獲取車隊名稱
        
        Args:
            driver_code: 車手代碼（如 VER, HAM）
            
        Returns:
            車隊名稱（如 Red Bull Racing, Mercedes）
        """
        # 使用 ColorPaletteProvider 統一獲取車隊名稱 (2025-12-14 更新)
        return color_palette_provider.get_driver_team(driver_code, fallback=True)
    
    def set_data(self, data: Dict[str, Any]):
        """
        設置數據並繪製圖表
        
        Args:
            data: API 返回的數據，包含 drivers 陣列
        """
        try:
            if not data or not isinstance(data, dict):
                logger.warning("[ACCEL_CHART_WIDGET] 無效的數據格式")
                return
            
            # 提取 drivers 數據
            drivers = data.get("drivers", [])
            if not drivers:
                drivers = data.get("data", {}).get("drivers", [])
            
            if not drivers:
                logger.warning("[ACCEL_CHART_WIDGET] 無 drivers 數據")
                self._init_empty_chart()
                return
            
            logger.info(f"[ACCEL_CHART_WIDGET] 設定數據: {len(drivers)} 位車手")
            
            self._drivers_data = drivers
            
            # 確保顏色數據已載入
            try:
                color_palette_provider.ensure_loaded()
            except Exception as e:
                logger.warning(f"[ACCEL_CHART_WIDGET] 顏色載入失敗: {e}")
            
            # 繪製圖表
            self._plot_chart()
            
        except Exception as e:
            logger.exception(f"[ACCEL_CHART_WIDGET] 設定數據失敗: {e}")
    
    def _plot_chart(self):
        """繪製速度-加速度圖表"""
        self.ax.clear()
        
        if not self._drivers_data:
            self._init_empty_chart()
            return
        
        # 收集所有車手的數據點
        plotted_drivers = []
        
        for driver_data in self._drivers_data:
            driver_code = driver_data.get("driver", "N/A")
            
            # 獲取加速度統計
            accel_stats = driver_data.get("acceleration_100_300_stats", {})
            speed_stats = driver_data.get("speed_stats", {})
            
            # 獲取關鍵數據
            avg_accel = accel_stats.get("avg_acceleration_ms2") or accel_stats.get("mean")
            max_speed = driver_data.get("absolute_max_speed_kmh") or speed_stats.get("max")
            
            # 如果沒有平均加速度，嘗試從中位數計算
            if avg_accel is None:
                accel_median = accel_stats.get("median")
                if accel_median and accel_median > 0:
                    # 假設從 100 到目標速度的平均加速度
                    # 使用 v = v0 + at 反推: a = (v - v0) / t
                    # 假設 v0 = 100 km/h, v = 300 km/h, t = accel_median
                    v0 = 100 / 3.6  # m/s
                    v = 300 / 3.6   # m/s
                    avg_accel = (v - v0) / accel_median
            
            if avg_accel is None or max_speed is None:
                continue
            
            # 獲取顏色
            color = self._get_driver_color_hex(driver_code)
            
            # 繪製散點
            self.ax.scatter(
                max_speed,     # X: 最高速度
                avg_accel,     # Y: 加速度
                c=color,
                s=150,         # 點大小
                alpha=0.8,
                edgecolors='white',
                linewidths=1.5,
                label=driver_code,
                zorder=5
            )
            
            # 添加車手標籤
            self.ax.annotate(
                driver_code,
                (max_speed, avg_accel),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=9,
                fontweight='bold',
                color=color
            )
            
            plotted_drivers.append(driver_code)
        
        if not plotted_drivers:
            self._init_empty_chart()
            return
        
        # 設置圖表樣式
        self.ax.set_xlabel(
            tr("accel_chart_x_label", "Max Speed (km/h)"),
            fontsize=12, fontweight='bold'
        )
        self.ax.set_ylabel(
            tr("accel_chart_y_label", "Average Acceleration (m/s^2)"),
            fontsize=12, fontweight='bold'
        )
        self.ax.set_title(
            tr("accel_chart_title", "Speed vs Acceleration - All Drivers"),
            fontsize=14, fontweight='bold', pad=15
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
        
        logger.info(f"[ACCEL_CHART_WIDGET] 圖表繪製完成: {len(plotted_drivers)} 位車手")
    
    def clear(self):
        """清空圖表"""
        self._drivers_data = []
        self._init_empty_chart()


__all__ = ["AccelerationChartWidget"]
