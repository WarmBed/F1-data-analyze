#!/usr/bin/env python3
"""
TelemetryChartWidgetBase - F1T 遙測圖表基類
============================================

基於 PyQt5 原生繪圖的統一圖表架構，支援多種圖表類型：
- 線性圖表 (速度、RPM、油門等)
- 階梯圖表 (檔位)
- 差異圖表 (速度差、距離差)
- 雙Y軸圖表 (降雨分析等)
- 柱狀圖表 (進站時間等)

設計原則：
1. 統一使用 PyQt5 QPainter 繪圖
2. 策略模式支援不同圖表類型
3. 保持一致的交互體驗
4. 支援連動和縮放功能
5. 統一的顏色和樣式管理

Author: F1T Team
Date: 2025-09-09
Version: 1.0.0
"""

import sys
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QFont, QPen, QColor, QPainter, QBrush, QMouseEvent, QWheelEvent

# 導入連動管理器
try:
    from modules.gui.lap_analysis.linkage import LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin, linkage_manager
except ImportError:
    LapAnalysisLinkageMixin = object
    LapAnalysisLinkageDrawingMixin = object
    linkage_manager = None
    print("[WARNING] 連動管理器導入失敗，將使用舊版連動功能")


class ChartTheme:
    """圖表主題配置 - 與現有 speed_analysis 風格保持一致"""
    
    # 背景顏色配置
    MAIN_BACKGROUND = QColor(255, 255, 255)     # 主背景：純白色
    CHART_BACKGROUND = QColor(248, 249, 250)    # 圖表區域：淺灰色
    BACKGROUND = QColor(255, 255, 255)          # 預設背景：純白色
    
    # 網格和座標軸顏色
    GRID_COLOR = QColor(200, 200, 200)          # 淺灰網格
    AXIS_COLOR = QColor(50, 50, 50)             # 深灰座標軸
    TEXT_COLOR = QColor(50, 50, 50)             # 文字顏色
    
    # 車手顏色 (與現有完全一致)
    DRIVER1_COLOR = QColor(0, 0, 255)           # 藍色 - 車手1
    DRIVER2_COLOR = QColor(255, 0, 0)           # 紅色 - 車手2
    
    # 輔助顏色
    SECTOR_COLOR = QColor(100, 100, 100, 100)   # 半透明灰色 - 扇形區域
    SELECTION_COLOR = QColor(255, 255, 0, 100)  # 半透明黃色 - 選擇區域
    HOVER_COLOR = QColor(0, 255, 0, 100)        # 半透明綠色 - 懸停效果
    
    # 字體配置
    AXIS_FONT = QFont("Arial", 10)
    TITLE_FONT = QFont("Arial", 12, QFont.Bold)
    VALUE_FONT = QFont("Arial", 9)
    
    # 邊距配置
    MARGIN_LEFT = 80
    MARGIN_RIGHT = 20
    MARGIN_TOP = 20
    MARGIN_BOTTOM = 80


class ChartDataPoint:
    """圖表數據點"""
    
    def __init__(self, x: float, y: float, metadata: Dict[str, Any] = None):
        self.x = x
        self.y = y
        self.metadata = metadata or {}


class ChartSeries:
    """圖表數據系列"""
    
    def __init__(self, name: str, data: List[ChartDataPoint], 
                 color: QColor, line_width: int = 2, style: str = 'line'):
        self.name = name
        self.data = data
        self.color = color
        self.line_width = line_width
        self.style = style  # 'line', 'step', 'bar', 'scatter'


class ChartRenderer(ABC):
    """圖表渲染器基類 - 策略模式的核心"""
    
    @abstractmethod
    def render(self, painter: QPainter, rect: QRect, 
               series_list: List[ChartSeries], 
               x_range: Tuple[float, float], 
               y_range: Tuple[float, float],
               **kwargs) -> None:
        """
        渲染圖表
        
        Args:
            painter: QPainter 對象
            rect: 繪圖區域
            series_list: 數據系列列表
            x_range: X軸範圍 (min, max)
            y_range: Y軸範圍 (min, max)
            **kwargs: 額外的渲染參數
        """
        pass
    
    @abstractmethod
    def get_value_at_position(self, x_pixel: int, rect: QRect,
                             series_list: List[ChartSeries],
                             x_range: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """
        根據像素位置獲取數據值
        
        Args:
            x_pixel: X軸像素位置
            rect: 繪圖區域
            series_list: 數據系列列表
            x_range: X軸範圍
            
        Returns:
            Dict: 包含數據值的字典，如果沒有數據則返回 None
        """
        pass


class LineChartRenderer(ChartRenderer):
    """線性圖表渲染器 - 適用於速度、RPM、油門等"""
    
    def render(self, painter: QPainter, rect: QRect, 
               series_list: List[ChartSeries], 
               x_range: Tuple[float, float], 
               y_range: Tuple[float, float],
               **kwargs) -> None:
        """渲染線性圖表"""
        
        for series in series_list:
            if not series.data:
                continue
                
            # 設置畫筆
            pen = QPen(series.color, series.line_width)
            painter.setPen(pen)
            
            # 轉換數據點為像素座標
            points = []
            for point in series.data:
                x_pixel = self._map_x_to_pixel(point.x, x_range, rect)
                y_pixel = self._map_y_to_pixel(point.y, y_range, rect)
                points.append(QPoint(x_pixel, y_pixel))
            
            # 繪製線條
            if len(points) > 1:
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
    
    def get_value_at_position(self, x_pixel: int, rect: QRect,
                             series_list: List[ChartSeries],
                             x_range: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """根據X像素位置獲取數據值"""
        
        # 轉換像素位置為數據值
        x_value = self._map_pixel_to_x(x_pixel, x_range, rect)
        
        result = {"x_value": x_value, "series_values": {}}
        
        for series in series_list:
            if not series.data:
                continue
                
            # 找到最接近的數據點
            closest_point = min(series.data, key=lambda p: abs(p.x - x_value))
            result["series_values"][series.name] = {
                "value": closest_point.y,
                "metadata": closest_point.metadata
            }
        
        return result
    
    def _map_x_to_pixel(self, x_value: float, x_range: Tuple[float, float], rect: QRect) -> int:
        """將X數據值映射到像素位置"""
        x_min, x_max = x_range
        if x_max == x_min:
            return rect.left()
        ratio = (x_value - x_min) / (x_max - x_min)
        return rect.left() + int(ratio * rect.width())
    
    def _map_y_to_pixel(self, y_value: float, y_range: Tuple[float, float], rect: QRect) -> int:
        """將Y數據值映射到像素位置"""
        y_min, y_max = y_range
        if y_max == y_min:
            return rect.bottom()
        ratio = (y_value - y_min) / (y_max - y_min)
        return rect.bottom() - int(ratio * rect.height())  # Y軸反向
    
    def _map_pixel_to_x(self, x_pixel: int, x_range: Tuple[float, float], rect: QRect) -> float:
        """將X像素位置映射到數據值"""
        x_min, x_max = x_range
        if rect.width() == 0:
            return x_min
        ratio = (x_pixel - rect.left()) / rect.width()
        return x_min + ratio * (x_max - x_min)


class StepChartRenderer(ChartRenderer):
    """階梯圖表渲染器 - 適用於檔位等離散數據"""
    
    def render(self, painter: QPainter, rect: QRect, 
               series_list: List[ChartSeries], 
               x_range: Tuple[float, float], 
               y_range: Tuple[float, float],
               **kwargs) -> None:
        """渲染階梯圖表"""
        
        for series in series_list:
            if not series.data:
                continue
                
            # 設置畫筆
            pen = QPen(series.color, series.line_width)
            painter.setPen(pen)
            
            # 繪製階梯線
            for i in range(len(series.data) - 1):
                current_point = series.data[i]
                next_point = series.data[i + 1]
                
                # 當前點位置
                x1 = self._map_x_to_pixel(current_point.x, x_range, rect)
                y1 = self._map_y_to_pixel(current_point.y, y_range, rect)
                
                # 下一點位置
                x2 = self._map_x_to_pixel(next_point.x, x_range, rect)
                y2 = self._map_y_to_pixel(next_point.y, y_range, rect)
                
                # 繪製階梯：水平線 + 垂直線
                painter.drawLine(x1, y1, x2, y1)  # 水平線
                painter.drawLine(x2, y1, x2, y2)  # 垂直線
    
    def get_value_at_position(self, x_pixel: int, rect: QRect,
                             series_list: List[ChartSeries],
                             x_range: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """根據X像素位置獲取數據值 - 階梯圖特殊邏輯"""
        
        x_value = self._map_pixel_to_x(x_pixel, x_range, rect)
        
        result = {"x_value": x_value, "series_values": {}}
        
        for series in series_list:
            if not series.data:
                continue
                
            # 找到當前X位置對應的階梯值
            current_value = None
            for i in range(len(series.data) - 1):
                if series.data[i].x <= x_value < series.data[i + 1].x:
                    current_value = series.data[i].y
                    break
            
            if current_value is None and series.data:
                # 如果在範圍外，使用最後一個值
                current_value = series.data[-1].y
            
            result["series_values"][series.name] = {
                "value": current_value,
                "metadata": {}
            }
        
        return result
    
    def _map_x_to_pixel(self, x_value: float, x_range: Tuple[float, float], rect: QRect) -> int:
        x_min, x_max = x_range
        if x_max == x_min:
            return rect.left()
        ratio = (x_value - x_min) / (x_max - x_min)
        return rect.left() + int(ratio * rect.width())
    
    def _map_y_to_pixel(self, y_value: float, y_range: Tuple[float, float], rect: QRect) -> int:
        y_min, y_max = y_range
        if y_max == y_min:
            return rect.bottom()
        ratio = (y_value - y_min) / (y_max - y_min)
        return rect.bottom() - int(ratio * rect.height())
    
    def _map_pixel_to_x(self, x_pixel: int, x_range: Tuple[float, float], rect: QRect) -> float:
        x_min, x_max = x_range
        if rect.width() == 0:
            return x_min
        ratio = (x_pixel - rect.left()) / rect.width()
        return x_min + ratio * (x_max - x_min)


class DifferenceChartRenderer(ChartRenderer):
    """差異圖表渲染器 - 適用於速度差、距離差等"""
    
    def render(self, painter: QPainter, rect: QRect, 
               series_list: List[ChartSeries], 
               x_range: Tuple[float, float], 
               y_range: Tuple[float, float],
               **kwargs) -> None:
        """渲染差異圖表"""
        
        # 繪製零線
        zero_y = self._map_y_to_pixel(0, y_range, rect)
        if y_range[0] <= 0 <= y_range[1]:
            pen = QPen(ChartTheme.AXIS_COLOR, 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(rect.left(), zero_y, rect.right(), zero_y)
        
        for series in series_list:
            if not series.data:
                continue
                
            # 設置畫筆
            pen = QPen(series.color, series.line_width)
            painter.setPen(pen)
            
            # 繪製差異線，並根據正負值使用不同顏色
            for i in range(len(series.data) - 1):
                current_point = series.data[i]
                next_point = series.data[i + 1]
                
                # 根據值的正負設置顏色
                color = QColor(0, 255, 0) if current_point.y >= 0 else QColor(255, 0, 0)
                pen.setColor(color)
                painter.setPen(pen)
                
                x1 = self._map_x_to_pixel(current_point.x, x_range, rect)
                y1 = self._map_y_to_pixel(current_point.y, y_range, rect)
                x2 = self._map_x_to_pixel(next_point.x, x_range, rect)
                y2 = self._map_y_to_pixel(next_point.y, y_range, rect)
                
                painter.drawLine(x1, y1, x2, y2)
    
    def get_value_at_position(self, x_pixel: int, rect: QRect,
                             series_list: List[ChartSeries],
                             x_range: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """根據X像素位置獲取差異值"""
        
        x_value = self._map_pixel_to_x(x_pixel, x_range, rect)
        
        result = {"x_value": x_value, "series_values": {}}
        
        for series in series_list:
            if not series.data:
                continue
                
            closest_point = min(series.data, key=lambda p: abs(p.x - x_value))
            result["series_values"][series.name] = {
                "value": closest_point.y,
                "difference_type": "positive" if closest_point.y >= 0 else "negative",
                "metadata": closest_point.metadata
            }
        
        return result
    
    def _map_x_to_pixel(self, x_value: float, x_range: Tuple[float, float], rect: QRect) -> int:
        x_min, x_max = x_range
        if x_max == x_min:
            return rect.left()
        ratio = (x_value - x_min) / (x_max - x_min)
        return rect.left() + int(ratio * rect.width())
    
    def _map_y_to_pixel(self, y_value: float, y_range: Tuple[float, float], rect: QRect) -> int:
        y_min, y_max = y_range
        if y_max == y_min:
            return rect.bottom()
        ratio = (y_value - y_min) / (y_max - y_min)
        return rect.bottom() - int(ratio * rect.height())
    
    def _map_pixel_to_x(self, x_pixel: int, x_range: Tuple[float, float], rect: QRect) -> float:
        x_min, x_max = x_range
        if rect.width() == 0:
            return x_min
        ratio = (x_pixel - rect.left()) / rect.width()
        return x_min + ratio * (x_max - x_min)


class ChartRendererFactory:
    """圖表渲染器工廠"""
    
    RENDERER_MAPPING = {
        'line': LineChartRenderer,
        'step': StepChartRenderer,
        'difference': DifferenceChartRenderer,
        # 未來可以添加更多類型：
        # 'bar': BarChartRenderer,
        # 'dual_axis': DualAxisChartRenderer,
        # 'scatter': ScatterChartRenderer
    }
    
    @classmethod
    def create_renderer(cls, chart_type: str) -> ChartRenderer:
        """創建圖表渲染器"""
        renderer_class = cls.RENDERER_MAPPING.get(chart_type, LineChartRenderer)
        return renderer_class()
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """獲取可用的圖表類型"""
        return list(cls.RENDERER_MAPPING.keys())


class TelemetryChartWidgetBase(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    """
    遙測圖表基類 - 統一的 PyQt5 原生繪圖架構
    
    支援多種圖表類型，通過策略模式切換不同的渲染器
    """
    
    # 信號定義
    data_updated = pyqtSignal(dict)
    mouse_position_changed = pyqtSignal(float, float)  # (x_value, y_value)
    selection_changed = pyqtSignal(float, float)       # (x_start, x_end)
    
    def __init__(self, chart_type: str = 'line', parent=None):
        """
        初始化圖表組件
        
        Args:
            chart_type: 圖表類型 ('line', 'step', 'difference')
            parent: 父組件
        """
        super().__init__(parent)
        
        # 初始化連動混入類
        if hasattr(self, '__init_linkage__'):
            self.__init_linkage__()
        
        # 圖表配置
        self.chart_type = chart_type
        self.renderer = ChartRendererFactory.create_renderer(chart_type)
        self.theme = ChartTheme()
        
        # 數據存儲
        self.series_list: List[ChartSeries] = []
        self.sectors: List[Dict[str, Any]] = []
        
        # 視圖範圍
        self.x_range = (0, 1000)
        self.y_range = (0, 100)
        self.view_x_range = None  # 用於縮放
        self.view_y_range = None
        
        # 交互狀態
        self.mouse_x = -1
        self.mouse_y = -1
        self.fixed_line_x = -1
        self.show_fixed_line = False
        self.fixed_distance_value = None
        
        # 連動狀態
        self.linkage_enabled = True
        self.master_linkage_enabled = True
        self.is_sending_linkage = False
        self.linkage_distance_value = None
        self.linkage_y_relative = 0.5
        self.show_linkage_line = False
        
        # UI 設置
        self.setMouseTracking(True)
        self.setMinimumSize(600, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 註冊到連動管理器
        if linkage_manager:
            linkage_manager.register_module(self, f"{chart_type}_chart")
    
    def set_chart_type(self, chart_type: str):
        """切換圖表類型"""
        if chart_type in ChartRendererFactory.get_available_types():
            self.chart_type = chart_type
            self.renderer = ChartRendererFactory.create_renderer(chart_type)
            self.update()
    
    def set_data(self, x_data: List[float], series_data: Dict[str, List[float]], 
                 series_names: Dict[str, str] = None, 
                 series_colors: Dict[str, QColor] = None):
        """
        設置圖表數據
        
        Args:
            x_data: X軸數據 (通常是距離)
            series_data: 系列數據 {'series1': [y_values], 'series2': [y_values]}
            series_names: 系列顯示名稱 {'series1': '車手1', 'series2': '車手2'}
            series_colors: 系列顏色 {'series1': QColor, 'series2': QColor}
        """
        # 基類的 set_data 方法不應該被直接調用
        print(f"⚠️ [BASE_CHART] TelemetryChartWidgetBase.set_data 被調用 - 這通常表示子類沒有正確覆寫方法")
        print(f"   - 調用者類型: {type(self)}")
        
        self.series_list.clear()
        
        if not series_names:
            series_names = {}
        if not series_colors:
            series_colors = {}
        
        # 默認顏色
        default_colors = [self.theme.DRIVER1_COLOR, self.theme.DRIVER2_COLOR]
        
        for i, (series_key, y_values) in enumerate(series_data.items()):
            if len(x_data) != len(y_values):
                continue
                
            # 創建數據點
            data_points = [ChartDataPoint(x, y) for x, y in zip(x_data, y_values)]
            
            # 設置系列屬性
            name = series_names.get(series_key, series_key)
            color = series_colors.get(series_key, default_colors[i % len(default_colors)])
            
            series = ChartSeries(name, data_points, color, style=self.chart_type)
            self.series_list.append(series)
        
        # 計算數據範圍
        self._calculate_data_ranges()
        
        # 更新顯示
        self.update()
        
        # 發出數據更新信號
        self.data_updated.emit({"series_count": len(self.series_list)})
    
    def set_sectors(self, sectors: List[Dict[str, Any]]):
        """設置扇形區域數據"""
        self.sectors = sectors
        self.update()
    
    def paintEvent(self, event):
        """繪製事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 清除背景
        painter.fillRect(self.rect(), self.theme.BACKGROUND)
        
        # 計算繪圖區域
        plot_rect = QRect(
            self.theme.MARGIN_LEFT,
            self.theme.MARGIN_TOP,
            self.width() - self.theme.MARGIN_LEFT - self.theme.MARGIN_RIGHT,
            self.height() - self.theme.MARGIN_TOP - self.theme.MARGIN_BOTTOM
        )
        
        if plot_rect.width() <= 0 or plot_rect.height() <= 0:
            return
        
        # 繪製網格和軸
        self._draw_grid_and_axes(painter, plot_rect)
        
        # 繪製扇形區域
        self._draw_sectors(painter, plot_rect)
        
        # 使用渲染器繪製圖表
        current_x_range = self.view_x_range or self.x_range
        current_y_range = self.view_y_range or self.y_range
        
        self.renderer.render(painter, plot_rect, self.series_list, 
                           current_x_range, current_y_range)
        
        # 繪製交互元素
        self._draw_interaction_elements(painter, plot_rect, current_x_range)
    
    def _calculate_data_ranges(self):
        """計算數據範圍"""
        if not self.series_list:
            return
            
        all_x = []
        all_y = []
        
        for series in self.series_list:
            for point in series.data:
                all_x.append(point.x)
                all_y.append(point.y)
        
        if all_x and all_y:
            self.x_range = (min(all_x), max(all_x))
            self.y_range = (min(all_y), max(all_y))
            
            # 添加一些邊距
            y_margin = (self.y_range[1] - self.y_range[0]) * 0.1
            self.y_range = (self.y_range[0] - y_margin, self.y_range[1] + y_margin)
    
    def _draw_grid_and_axes(self, painter: QPainter, rect: QRect):
        """繪製網格和座標軸"""
        
        current_x_range = self.view_x_range or self.x_range
        current_y_range = self.view_y_range or self.y_range
        
        # 設置網格畫筆
        grid_pen = QPen(self.theme.GRID_COLOR, 1)
        painter.setPen(grid_pen)
        
        # 繪製垂直網格線 (X軸)
        x_step = (current_x_range[1] - current_x_range[0]) / 10
        for i in range(11):
            x_value = current_x_range[0] + i * x_step
            x_pixel = rect.left() + int((x_value - current_x_range[0]) / 
                                      (current_x_range[1] - current_x_range[0]) * rect.width())
            painter.drawLine(x_pixel, rect.top(), x_pixel, rect.bottom())
        
        # 繪製水平網格線 (Y軸)
        y_step = (current_y_range[1] - current_y_range[0]) / 8
        for i in range(9):
            y_value = current_y_range[0] + i * y_step
            y_pixel = rect.bottom() - int((y_value - current_y_range[0]) / 
                                        (current_y_range[1] - current_y_range[0]) * rect.height())
            painter.drawLine(rect.left(), y_pixel, rect.right(), y_pixel)
        
        # 繪製座標軸
        axis_pen = QPen(self.theme.AXIS_COLOR, 2)
        painter.setPen(axis_pen)
        painter.drawRect(rect)
        
        # 繪製刻度標籤
        painter.setFont(self.theme.AXIS_FONT)
        painter.setPen(self.theme.TEXT_COLOR)
        
        # X軸標籤
        for i in range(11):
            x_value = current_x_range[0] + i * x_step
            x_pixel = rect.left() + int((x_value - current_x_range[0]) / 
                                      (current_x_range[1] - current_x_range[0]) * rect.width())
            label = f"{x_value:.0f}"
            painter.drawText(x_pixel - 20, rect.bottom() + 20, 40, 20, Qt.AlignCenter, label)
        
        # Y軸標籤
        for i in range(9):
            y_value = current_y_range[0] + i * y_step
            y_pixel = rect.bottom() - int((y_value - current_y_range[0]) / 
                                        (current_y_range[1] - current_y_range[0]) * rect.height())
            label = f"{y_value:.1f}"
            painter.drawText(10, y_pixel - 10, 60, 20, Qt.AlignRight | Qt.AlignVCenter, label)
    
    def _draw_sectors(self, painter: QPainter, rect: QRect):
        """繪製扇形區域"""
        if not self.sectors:
            return
            
        current_x_range = self.view_x_range or self.x_range
        
        painter.setBrush(QBrush(self.theme.SECTOR_COLOR))
        painter.setPen(Qt.NoPen)
        
        for sector in self.sectors:
            start_x = sector.get('start', 0)
            end_x = sector.get('end', 0)
            
            start_pixel = rect.left() + int((start_x - current_x_range[0]) / 
                                          (current_x_range[1] - current_x_range[0]) * rect.width())
            end_pixel = rect.left() + int((end_x - current_x_range[0]) / 
                                        (current_x_range[1] - current_x_range[0]) * rect.width())
            
            sector_rect = QRect(start_pixel, rect.top(), end_pixel - start_pixel, rect.height())
            painter.drawRect(sector_rect)
    
    def _draw_interaction_elements(self, painter: QPainter, rect: QRect, x_range: Tuple[float, float]):
        """繪製交互元素"""
        
        # 繪製固定線
        if self.show_fixed_line and self.fixed_line_x >= 0:
            pen = QPen(QColor(255, 255, 0), 2)  # 黃色
            painter.setPen(pen)
            painter.drawLine(self.fixed_line_x, rect.top(), self.fixed_line_x, rect.bottom())
        
        # 繪製連動線
        if self.show_linkage_line and self.linkage_distance_value is not None:
            linkage_x = rect.left() + int((self.linkage_distance_value - x_range[0]) / 
                                        (x_range[1] - x_range[0]) * rect.width())
            pen = QPen(QColor(0, 255, 0), 2)  # 綠色
            painter.setPen(pen)
            painter.drawLine(linkage_x, rect.top(), linkage_x, rect.bottom())
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """滑鼠移動事件"""
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        
        # 計算數據值
        plot_rect = QRect(
            self.theme.MARGIN_LEFT,
            self.theme.MARGIN_TOP,
            self.width() - self.theme.MARGIN_LEFT - self.theme.MARGIN_RIGHT,
            self.height() - self.theme.MARGIN_TOP - self.theme.MARGIN_BOTTOM
        )
        
        if plot_rect.contains(event.pos()):
            current_x_range = self.view_x_range or self.x_range
            values = self.renderer.get_value_at_position(self.mouse_x, plot_rect, 
                                                       self.series_list, current_x_range)
            
            if values:
                self.mouse_position_changed.emit(values["x_value"], 0)  # Y值由具體實現決定
        
        self.update()
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """滑鼠按下事件"""
        if event.button() == Qt.LeftButton:
            # 設置固定線
            self.fixed_line_x = event.x()
            self.show_fixed_line = True
            
            # 計算對應的數據值
            plot_rect = QRect(
                self.theme.MARGIN_LEFT,
                self.theme.MARGIN_TOP,
                self.width() - self.theme.MARGIN_LEFT - self.theme.MARGIN_RIGHT,
                self.height() - self.theme.MARGIN_TOP - self.theme.MARGIN_BOTTOM
            )
            
            current_x_range = self.view_x_range or self.x_range
            values = self.renderer.get_value_at_position(self.fixed_line_x, plot_rect, 
                                                       self.series_list, current_x_range)
            
            if values:
                self.fixed_distance_value = values["x_value"]
                
                # 發送連動信號
                if self.linkage_enabled and not self.is_sending_linkage and linkage_manager:
                    self.is_sending_linkage = True
                    linkage_manager.send_click_linkage(self.fixed_distance_value, self)
                    self.is_sending_linkage = False
            
            self.update()
        
        super().mousePressEvent(event)
    
    def wheelEvent(self, event: QWheelEvent):
        """滾輪縮放事件"""
        # 簡單的縮放實現
        if event.angleDelta().y() > 0:
            # 放大
            self._zoom(1.1, event.x())
        else:
            # 縮小
            self._zoom(0.9, event.x())
        
        self.update()
        super().wheelEvent(event)
    
    def _zoom(self, factor: float, center_x: int):
        """縮放功能"""
        if not self.view_x_range:
            self.view_x_range = list(self.x_range)
        
        # 計算縮放中心
        plot_rect = QRect(
            self.theme.MARGIN_LEFT,
            self.theme.MARGIN_TOP,
            self.width() - self.theme.MARGIN_LEFT - self.theme.MARGIN_RIGHT,
            self.height() - self.theme.MARGIN_TOP - self.theme.MARGIN_BOTTOM
        )
        
        if plot_rect.width() > 0:
            center_ratio = (center_x - plot_rect.left()) / plot_rect.width()
            
            # 計算新的範圍
            current_width = self.view_x_range[1] - self.view_x_range[0]
            new_width = current_width / factor
            
            center_value = self.view_x_range[0] + center_ratio * current_width
            
            self.view_x_range[0] = center_value - center_ratio * new_width
            self.view_x_range[1] = center_value + (1 - center_ratio) * new_width
            
            # 限制範圍
            if self.view_x_range[0] < self.x_range[0]:
                self.view_x_range[0] = self.x_range[0]
            if self.view_x_range[1] > self.x_range[1]:
                self.view_x_range[1] = self.x_range[1]
    
    def reset_zoom(self):
        """重置縮放"""
        self.view_x_range = None
        self.view_y_range = None
        self.update()
    
    # 連動功能方法
    def set_linkage_enabled(self, enabled: bool):
        """設置連動開關"""
        self.linkage_enabled = enabled
    
    def set_master_linkage_enabled(self, enabled: bool):
        """設置主連動開關"""
        self.master_linkage_enabled = enabled
    
    def receive_distance_update(self, distance_value: float, sender):
        """接收連動距離更新"""
        if self.linkage_enabled and self.master_linkage_enabled and sender != self:
            self.linkage_distance_value = distance_value
            self.show_linkage_line = True
            self.update()
    
    def get_chart_type(self) -> str:
        """獲取圖表類型"""
        return self.chart_type
    
    def get_current_data(self) -> Dict[str, Any]:
        """獲取當前圖表數據"""
        return {
            "chart_type": self.chart_type,
            "series_count": len(self.series_list),
            "x_range": self.x_range,
            "y_range": self.y_range,
            "sectors_count": len(self.sectors)
        }


# ========== 工廠函數 ==========

def create_telemetry_chart(analysis_type: str, parent=None) -> TelemetryChartWidgetBase:
    """
    創建遙測圖表的工廠函數
    
    Args:
        analysis_type: 分析類型 ('speed', 'rpm', 'gear', 'throttle', 等)
        parent: 父組件
        
    Returns:
        TelemetryChartWidgetBase: 對應的圖表組件
    """
    
    # 根據分析類型選擇圖表類型
    chart_type_mapping = {
        'speed': 'line',
        'rpm': 'line', 
        'throttle': 'line',
        'brake': 'line',
        'gear': 'step',
        'acceleration': 'line',
        'speeddiff': 'difference',
        'distancediff': 'difference'
    }
    
    chart_type = chart_type_mapping.get(analysis_type, 'line')
    return TelemetryChartWidgetBase(chart_type, parent)
