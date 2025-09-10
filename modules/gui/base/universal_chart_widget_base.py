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
    AXIS_TITLE_FONT = QFont("Microsoft YaHei", 7)  # 座標軸標題字體 - 改為7號字體，不使用Bold
    VALUE_FONT = QFont("Arial", 9)
    
    # 邊距配置
    MARGIN_LEFT = 80
    MARGIN_RIGHT = 20
    MARGIN_TOP = 20
    MARGIN_BOTTOM = 20  # 下邊距從80改為20


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
        
        # 座標軸標題配置
        self.x_axis_title = "距離 (m)"              # X軸標題
        self.y_axis_title = ""                      # Y軸標題  
        self.x_title_position = "bottom-center"     # X軸標題位置: "bottom-center", "bottom-left"
        self.y_title_position = "left-center"       # Y軸標題位置: "left-center", "left-bottom"
        self.show_axis_titles = True                # 是否顯示座標軸標題
        
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
        
        # 增強交互功能
        self.middle_dragging = False
        self.last_drag_pos = QPoint()
        self.show_value_tooltip = True  # 是否顯示數值提示
        self.tooltip_precision = 1      # 數值提示精度
        
        # 連動狀態
        self.linkage_enabled = True
        self.master_linkage_enabled = True
        self.is_sending_linkage = False
        self.linkage_distance_value = None
        self.linkage_y_relative = 0.5
        self.show_linkage_line = False
        
        # UI 設置
        self.setMouseTracking(True)
        self.setMinimumSize(200, 100)  # 極小最小尺寸，提供更高的佈局靈活性
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
    
    # ========== 座標軸標題配置方法 ==========
    
    def set_axis_titles(self, x_title: str, y_title: str):
        """設定座標軸標題"""
        self.x_axis_title = x_title
        self.y_axis_title = y_title
        self.update()
    
    def set_axis_title_positions(self, x_position: str, y_position: str):
        """
        設定座標軸標題位置
        
        Args:
            x_position: X軸標題位置 ("bottom-center", "bottom-left")
            y_position: Y軸標題位置 ("left-center", "left-bottom")
        """
        valid_x_positions = ["bottom-center", "bottom-left"]
        valid_y_positions = ["left-center", "left-bottom"]
        
        if x_position in valid_x_positions:
            self.x_title_position = x_position
        else:
            print(f"⚠️ 無效的X軸標題位置: {x_position}. 可用選項: {valid_x_positions}")
            
        if y_position in valid_y_positions:
            self.y_title_position = y_position
        else:
            print(f"⚠️ 無效的Y軸標題位置: {y_position}. 可用選項: {valid_y_positions}")
            
        self.update()
    
    def set_show_axis_titles(self, show: bool):
        """設定是否顯示座標軸標題"""
        self.show_axis_titles = show
        self.update()
    
    def set_x_axis_title(self, title: str, position: str = None):
        """設定X軸標題和位置"""
        self.x_axis_title = title
        if position:
            self.set_axis_title_positions(position, self.y_title_position)
        else:
            self.update()
    
    def set_y_axis_title(self, title: str, position: str = None):
        """設定Y軸標題和位置"""
        self.y_axis_title = title
        if position:
            self.set_axis_title_positions(self.x_title_position, position)
        else:
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
        
        # 繪製數值追蹤線和提示
        self._draw_tracking_elements(painter, plot_rect, current_x_range, current_y_range)
        
        # 繪製座標軸標題
        if self.show_axis_titles:
            self._draw_axis_titles(painter, plot_rect)
    
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
        """繪製基礎交互元素"""
        
        # 繪製連動線
        if self.show_linkage_line and self.linkage_distance_value is not None:
            linkage_x = rect.left() + int((self.linkage_distance_value - x_range[0]) / 
                                        (x_range[1] - x_range[0]) * rect.width())
            pen = QPen(QColor(0, 255, 0), 2)  # 綠色
            painter.setPen(pen)
            painter.drawLine(linkage_x, rect.top(), linkage_x, rect.bottom())
    
    def _draw_tracking_elements(self, painter: QPainter, rect: QRect, 
                               x_range: Tuple[float, float], y_range: Tuple[float, float]):
        """繪製追蹤元素（固定線、跟隨線、數值提示）"""
        
        # 繪製固定線（如果有的話）
        if self.show_fixed_line and self.fixed_distance_value is not None:
            if x_range[0] <= self.fixed_distance_value <= x_range[1]:
                fixed_x = rect.left() + int((self.fixed_distance_value - x_range[0]) / 
                                          (x_range[1] - x_range[0]) * rect.width())
                self._draw_tracking_line(painter, rect, fixed_x, x_range, y_range, is_fixed=True)
        
        # 繪製滑鼠跟隨線
        if rect.contains(self.mouse_x, self.mouse_y) and self.show_value_tooltip:
            self._draw_tracking_line(painter, rect, self.mouse_x, x_range, y_range, is_fixed=False)
    
    def _draw_tracking_line(self, painter: QPainter, rect: QRect, x_pos: int, 
                           x_range: Tuple[float, float], y_range: Tuple[float, float], is_fixed: bool):
        """繪製追蹤線和數值顯示 - 仿照 DistanceDiff 實現"""
        if not rect.contains(x_pos, rect.center().y()):
            return
            
        # 設置線條樣式
        if is_fixed:
            # 固定線：綠色實線
            painter.setPen(QPen(QColor(0, 180, 0), 2, Qt.SolidLine))
        else:
            # 跟隨線：灰色虛線
            painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
            
        painter.drawLine(x_pos, rect.top(), x_pos, rect.bottom())
        
        # 計算當前位置對應的數據值
        x_range_size = x_range[1] - x_range[0]
        if x_range_size <= 0 or not self.series_list:
            return
            
        # 計算X軸數據值
        relative_x = x_pos - rect.left()
        x_value = x_range[0] + (relative_x / rect.width()) * x_range_size
        
        # 獲取對應位置的數據值
        values_at_position = self.renderer.get_value_at_position(x_pos, rect, self.series_list, x_range)
        
        if not values_at_position:
            return
            
        # 準備顯示的數據
        series_values = values_at_position.get("series_values", {})
        if not series_values:
            return
            
        # 計算標籤尺寸
        base_height = 25  # X值顯示的基本高度
        series_height = 20 * len(series_values)  # 每個系列20像素高度
        label_height = base_height + series_height + 10  # 額外邊距
        
        # 繪製數值標籤背景
        label_width = 180
        label_x = min(x_pos + 15, self.width() - label_width - 10)
        
        # 根據線條類型決定標籤位置
        if is_fixed:
            label_y = max(rect.top() + 10, 10)
        else:
            label_y = max(self.mouse_y - label_height - 10, 10)
        
        # 確保標籤在可視區域內
        label_y = min(label_y, self.height() - label_height - 10)
        
        # 設置標籤背景顏色
        bg_color = QColor(255, 240, 240, 240) if is_fixed else QColor(255, 255, 255, 240)
        border_color = QColor(0, 180, 0) if is_fixed else QColor(150, 150, 150)
        
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(label_x, label_y, label_width, label_height)
        
        # 繪製數值文字
        painter.setPen(QPen(self.theme.TEXT_COLOR, 1))
        painter.setFont(QFont("Arial", 9))
        
        text_y = label_y + 18
        
        # 顯示X軸數值
        x_label = self.x_axis_title if self.x_axis_title else "X"
        painter.drawText(label_x + 8, text_y, f"{x_label}: {x_value:.{self.tooltip_precision}f}")
        
        # 顯示各系列的Y值
        for i, (series_name, value_info) in enumerate(series_values.items()):
            y_value = value_info.get("value", 0)
            
            # 根據系列選擇顏色
            series_color = self.theme.DRIVER1_COLOR if i == 0 else self.theme.DRIVER2_COLOR
            if len(self.series_list) > i:
                series_color = self.series_list[i].color
                
            painter.setPen(QPen(series_color, 1))
            painter.drawText(label_x + 8, text_y + 20 + (i * 20), 
                           f"{series_name}: {y_value:.{self.tooltip_precision}f}")
            
            # 如果是差異圖表，添加額外信息
            if hasattr(value_info, 'get') and "difference_type" in value_info:
                diff_type = value_info["difference_type"]
                status = "領先" if diff_type == "positive" else "落後"
                painter.setPen(QPen(self.theme.TEXT_COLOR, 1))
                painter.drawText(label_x + 100, text_y + 20 + (i * 20), f"({status})")
    
    def _draw_axis_titles(self, painter: QPainter, rect: QRect):
        """繪製座標軸標題 - 統一配置位置"""
        print(f"[BASE_CHART] 🎨 _draw_axis_titles 開始繪製")
        print(f"  rect: {rect}")
        print(f"  X軸標題: '{self.x_axis_title}' 位置: {self.x_title_position}")
        print(f"  Y軸標題: '{self.y_axis_title}' 位置: {self.y_title_position}")
        
        painter.setFont(self.theme.AXIS_TITLE_FONT)
        painter.setPen(QPen(self.theme.TEXT_COLOR))
        
        # X軸標題
        if self.x_axis_title:
            print(f"[BASE_CHART] 繪製X軸標題: '{self.x_axis_title}'")
            if self.x_title_position == "bottom-left":
                # 🎯 位置在X軸0點左邊（水平顯示）- 確保在可見區域內
                x_title_rect = QRect(
                    rect.left() - 40,           # 在X軸0點左邊，但不要太遠
                    rect.bottom() + 5,          # X軸下方一點點
                    80, 20                      # 寬度足夠顯示標題
                )
                painter.drawText(x_title_rect, Qt.AlignLeft | Qt.AlignVCenter, self.x_axis_title)
                print(f"[BASE_CHART] ✅ X軸標題繪製完成: rect={x_title_rect}")
            else:  # "bottom-center" (預設)
                # 位置在圖表底部中央
                x_title_rect = QRect(
                    rect.center().x() - 50,     # 圖表中央
                    rect.bottom() + 5,          # 圖表下方一點點
                    100, 20
                )
                painter.drawText(x_title_rect, Qt.AlignCenter, self.x_axis_title)
                print(f"[BASE_CHART] ✅ X軸標題繪製完成: rect={x_title_rect}")
        
        # Y軸標題
        if self.y_axis_title:
            print(f"[BASE_CHART] 繪製Y軸標題: '{self.y_axis_title}'")
            painter.save()
            # 🎯 Y軸標題始終在Y軸中間（垂直顯示）
            y_center = rect.center().y()
            painter.translate(30, y_center)            # Y軸左側，確保可見
            painter.rotate(-90)                        # 逆時針旋轉90度
            y_title_rect = QRect(-40, -10, 80, 20)    # 更寬的矩形容納標題
            painter.drawText(y_title_rect, Qt.AlignCenter, self.y_axis_title)
            painter.restore()
            print(f"[BASE_CHART] ✅ Y軸標題繪製完成: center_y={y_center}, x=30")
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """滑鼠移動事件 - 增強版本"""
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        
        # 計算圖表區域
        plot_rect = QRect(
            self.theme.MARGIN_LEFT,
            self.theme.MARGIN_TOP,
            self.width() - self.theme.MARGIN_LEFT - self.theme.MARGIN_RIGHT,
            self.height() - self.theme.MARGIN_TOP - self.theme.MARGIN_BOTTOM
        )
        
        # 處理中鍵拖拽
        if self.middle_dragging and not self.last_drag_pos.isNull():
            self._handle_middle_drag(event, plot_rect)
        
        # 處理連動和數據計算
        if plot_rect.contains(event.pos()):
            current_x_range = self.view_x_range or self.x_range
            current_y_range = self.view_y_range or self.y_range
            
            # 計算當前滑鼠對應的數據值
            x_range_size = current_x_range[1] - current_x_range[0]
            if x_range_size > 0:
                relative_x = event.x() - plot_rect.left()
                x_value = current_x_range[0] + (relative_x / plot_rect.width()) * x_range_size
                
                # 計算Y軸相對位置
                relative_y = (plot_rect.bottom() - event.y()) / plot_rect.height()
                relative_y = max(0.0, min(1.0, relative_y))
                
                # 發送連動信號
                if linkage_manager and self.linkage_enabled and not self.is_sending_linkage:
                    linkage_manager.send_x_linkage(x_value, relative_y, self)
                
                # 獲取數據值
                values = self.renderer.get_value_at_position(self.mouse_x, plot_rect, 
                                                           self.series_list, current_x_range)
                if values:
                    # 發送位置變更信號
                    y_value = 0
                    series_values = values.get("series_values", {})
                    if series_values:
                        first_series = next(iter(series_values.values()))
                        y_value = first_series.get("value", 0)
                    
                    self.mouse_position_changed.emit(x_value, y_value)
        
        self.update()
        super().mouseMoveEvent(event)
    
    def _handle_middle_drag(self, event: QMouseEvent, plot_rect: QRect):
        """處理中鍵拖拽移動"""
        # 計算移動距離
        dx = event.x() - self.last_drag_pos.x()
        dy = event.y() - self.last_drag_pos.y()
        
        if plot_rect.width() > 0 and plot_rect.height() > 0:
            # 初始化視圖範圍
            if self.view_x_range is None:
                self.view_x_range = list(self.x_range)
            if self.view_y_range is None:
                self.view_y_range = list(self.y_range)
            
            # X軸移動
            x_range_size = self.view_x_range[1] - self.view_x_range[0]
            x_move = -dx * x_range_size / plot_rect.width()
            
            # Y軸移動（Y軸是倒置的）
            y_range_size = self.view_y_range[1] - self.view_y_range[0]
            y_move = dy * y_range_size / plot_rect.height()
            
            # 更新視圖範圍
            self.view_x_range[0] += x_move
            self.view_x_range[1] += x_move
            self.view_y_range[0] += y_move
            self.view_y_range[1] += y_move
            
            # 限制在原始範圍內（可選）
            # self._clamp_view_ranges()
        
        self.last_drag_pos = event.pos()
    
    def mousePressEvent(self, event: QMouseEvent):
        """滑鼠按下事件 - 增強版本"""
        plot_rect = QRect(
            self.theme.MARGIN_LEFT,
            self.theme.MARGIN_TOP,
            self.width() - self.theme.MARGIN_LEFT - self.theme.MARGIN_RIGHT,
            self.height() - self.theme.MARGIN_TOP - self.theme.MARGIN_BOTTOM
        )
        
        if event.button() == Qt.LeftButton:
            # 左鍵點擊：設置固定線
            if plot_rect.contains(event.pos()):
                current_x_range = self.view_x_range or self.x_range
                x_range_size = current_x_range[1] - current_x_range[0]
                
                if x_range_size > 0:
                    relative_x = event.x() - plot_rect.left()
                    self.fixed_distance_value = current_x_range[0] + (relative_x / plot_rect.width()) * x_range_size
                    self.show_fixed_line = True
                    
                    # 發送連動信號
                    if self.linkage_enabled and not self.is_sending_linkage and linkage_manager:
                        self.is_sending_linkage = True
                        linkage_manager.send_click_linkage(self.fixed_distance_value, self)
                        self.is_sending_linkage = False
                    
                    self.update()
                    
        elif event.button() == Qt.RightButton:
            # 右鍵點擊：清除固定線
            self.clear_fixed_line()
            
            # 發送清除連動信號
            if linkage_manager and self.linkage_enabled:
                linkage_manager.send_click_linkage_clear(sender=self)
            
        elif event.button() == Qt.MiddleButton:
            # 中鍵按下：開始拖拽
            if plot_rect.contains(event.pos()):
                self.middle_dragging = True
                self.last_drag_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
        
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """滑鼠雙擊事件 - 清除固定線"""
        if event.button() == Qt.LeftButton:
            self.clear_fixed_line()
            
            # 發送清除連動信號
            if linkage_manager and self.linkage_enabled:
                linkage_manager.send_click_linkage_clear(sender=self)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """滑鼠釋放事件"""
        if event.button() == Qt.MiddleButton:
            # 中鍵釋放：結束拖拽
            self.middle_dragging = False
            self.setCursor(Qt.ArrowCursor)
        
        super().mouseReleaseEvent(event)
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.mouse_x = -1
        self.mouse_y = -1
        
        # 發送連動清除信號
        if linkage_manager and self.linkage_enabled:
            linkage_manager.send_x_linkage_clear(self)
        
        self.update()
        super().leaveEvent(event)
    
    def wheelEvent(self, event: QWheelEvent):
        """滾輪縮放事件 - 增強版本"""
        # 獲取滾輪方向
        delta = event.angleDelta().y()
        zoom_factor = 1.15 if delta > 0 else 1.0 / 1.15
        
        # 計算圖表區域
        plot_rect = QRect(
            self.theme.MARGIN_LEFT,
            self.theme.MARGIN_TOP,
            self.width() - self.theme.MARGIN_LEFT - self.theme.MARGIN_RIGHT,
            self.height() - self.theme.MARGIN_TOP - self.theme.MARGIN_BOTTOM
        )
        
        if plot_rect.contains(event.pos()):
            # 計算滑鼠位置對應的數據值比例
            mouse_rel_x = (event.x() - plot_rect.left()) / plot_rect.width()
            mouse_rel_y = (plot_rect.bottom() - event.y()) / plot_rect.height()
            
            # 限制比例範圍
            mouse_rel_x = max(0.0, min(1.0, mouse_rel_x))
            mouse_rel_y = max(0.0, min(1.0, mouse_rel_y))
            
            # 初始化視圖範圍
            if self.view_x_range is None:
                self.view_x_range = list(self.x_range)
            if self.view_y_range is None:
                self.view_y_range = list(self.y_range)
            
            # 執行雙軸縮放
            self._zoom_at_position(zoom_factor, mouse_rel_x, mouse_rel_y)
            
            self.update()
        
        super().wheelEvent(event)
    
    def _zoom_at_position(self, zoom_factor: float, rel_x: float, rel_y: float):
        """在指定相對位置進行縮放"""
        # X軸縮放
        x_range_size = self.view_x_range[1] - self.view_x_range[0]
        mouse_x_value = self.view_x_range[0] + rel_x * x_range_size
        
        new_x_range_size = x_range_size / zoom_factor
        self.view_x_range[0] = mouse_x_value - rel_x * new_x_range_size
        self.view_x_range[1] = mouse_x_value + (1 - rel_x) * new_x_range_size
        
        # Y軸縮放
        y_range_size = self.view_y_range[1] - self.view_y_range[0]
        mouse_y_value = self.view_y_range[0] + rel_y * y_range_size
        
        new_y_range_size = y_range_size / zoom_factor
        self.view_y_range[0] = mouse_y_value - rel_y * new_y_range_size
        self.view_y_range[1] = mouse_y_value + (1 - rel_y) * new_y_range_size
        
        # 限制縮放範圍（避免過度縮放）
        self._clamp_view_ranges()
    
    def _clamp_view_ranges(self):
        """限制視圖範圍在合理區間內"""
        # X軸範圍限制
        original_x_size = self.x_range[1] - self.x_range[0]
        min_x_size = original_x_size * 0.01  # 最小1%
        max_x_size = original_x_size * 2.0   # 最大200%
        
        current_x_size = self.view_x_range[1] - self.view_x_range[0]
        if current_x_size < min_x_size:
            center_x = (self.view_x_range[0] + self.view_x_range[1]) / 2
            self.view_x_range[0] = center_x - min_x_size / 2
            self.view_x_range[1] = center_x + min_x_size / 2
        elif current_x_size > max_x_size:
            center_x = (self.view_x_range[0] + self.view_x_range[1]) / 2
            self.view_x_range[0] = center_x - max_x_size / 2
            self.view_x_range[1] = center_x + max_x_size / 2
        
        # Y軸範圍限制
        original_y_size = self.y_range[1] - self.y_range[0]
        min_y_size = original_y_size * 0.01  # 最小1%
        max_y_size = original_y_size * 2.0   # 最大200%
        
        current_y_size = self.view_y_range[1] - self.view_y_range[0]
        if current_y_size < min_y_size:
            center_y = (self.view_y_range[0] + self.view_y_range[1]) / 2
            self.view_y_range[0] = center_y - min_y_size / 2
            self.view_y_range[1] = center_y + min_y_size / 2
        elif current_y_size > max_y_size:
            center_y = (self.view_y_range[0] + self.view_y_range[1]) / 2
            self.view_y_range[0] = center_y - max_y_size / 2
            self.view_y_range[1] = center_y + max_y_size / 2
    
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
    
    def reset_view(self):
        """重置視圖到原始狀態 - 包含縮放和固定線"""
        self.view_x_range = None
        self.view_y_range = None
        self.clear_fixed_line()
        self.update()
    
    def clear_fixed_line(self):
        """清除固定線"""
        self.show_fixed_line = False
        self.fixed_distance_value = None
        self.update()
    
    def set_tooltip_enabled(self, enabled: bool):
        """設置數值提示開關"""
        self.show_value_tooltip = enabled
        self.update()
    
    def set_tooltip_precision(self, precision: int):
        """設置數值提示精度"""
        self.tooltip_precision = max(0, min(precision, 6))  # 限制在0-6位小數
        self.update()
    
    def get_mouse_data_value(self) -> Optional[Dict[str, Any]]:
        """獲取當前滑鼠位置對應的數據值"""
        if self.mouse_x < 0 or self.mouse_y < 0:
            return None
            
        plot_rect = QRect(
            self.theme.MARGIN_LEFT,
            self.theme.MARGIN_TOP,
            self.width() - self.theme.MARGIN_LEFT - self.theme.MARGIN_RIGHT,
            self.height() - self.theme.MARGIN_TOP - self.theme.MARGIN_BOTTOM
        )
        
        if not plot_rect.contains(self.mouse_x, self.mouse_y):
            return None
            
        current_x_range = self.view_x_range or self.x_range
        return self.renderer.get_value_at_position(self.mouse_x, plot_rect, self.series_list, current_x_range)
    
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
