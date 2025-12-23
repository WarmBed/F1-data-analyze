#!/usr/bin/env python3
"""
TempAnalysisChartWidget - F1T 溫度分析圖表組件
==============================================

專門用於溫度分析的圖表組件，支援：
- 雙Y軸圖表（溫度+降雨）
- 多系列數據顯示
- 天氣數據視覺化
- 互動式縮放和平移
- 圖表類型動態切換

基於通用圖表基礎類別實現。

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

import sys
import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QFontMetrics, QMouseEvent, QPainterPath

# 導入翻譯函數
from core.gui_i18n import tr
# 導入集中式 logger
from core.logger import get_logger
# 導入圖表基礎類別
from modules.gui.base.universal_chart_widget_base import TelemetryChartWidgetBase

# 設定 logger
logger = get_logger("temp_chart", component="gui")


class TempChartTheme:
    """溫度分析專用圖表主題"""
    
    # 背景顏色
    BACKGROUND = QColor(250, 251, 252)
    MAIN_BACKGROUND = QColor(250, 251, 252)
    CHART_BACKGROUND = QColor(248, 249, 250)
    
    # 文字和標籤顏色
    LABEL_COLOR = QColor(50, 50, 50)
    TEXT_COLOR = QColor(50, 50, 50)
    AXIS_COLOR = QColor(50, 50, 50)
    GRID_COLOR = QColor(200, 200, 200)
    
    # 新版溫度分析專用顏色 (2025-12-21 更新)
    # 氣溫：#FF6B6B (珊瑚紅)
    AIR_TEMP_COLOR = QColor(0xFF, 0x6B, 0x6B)
    # 賽道溫度：#FF9F43 (橘黃)
    TRACK_TEMP_COLOR = QColor(0xFF, 0x9F, 0x43)
    # 風速：#1DD1A1 (青綠)
    WIND_SPEED_COLOR = QColor(0x1D, 0xD1, 0xA1)
    # 降雨區域：rgba(100, 149, 237, 0.3) (透明藍，30% 不透明)
    RAINFALL_AREA_COLOR = QColor(100, 149, 237, 77)  # 255 * 0.3 ≈ 77
    
    # 舊版顏色保留（向後相容）
    RAINFALL_COLOR = QColor(52, 152, 219)       # 藍色 - 降雨
    HUMIDITY_COLOR = QColor(46, 204, 113)       # 綠色 - 濕度
    PRESSURE_COLOR = QColor(52, 73, 94)         # 深灰色 - 氣壓
    
    # 降雨條顏色（舊版）
    RAIN_BAR_COLOR = QColor(52, 152, 219, 100)  # 半透明藍色
    DRY_BAR_COLOR = QColor(200, 200, 200, 50)   # 半透明灰色
    
    # 邊框顏色
    DEFAULT_BORDER_COLOR = QColor(108, 117, 125)


class TempAnalysisChartWidget(TelemetryChartWidgetBase):
    """溫度分析圖表組件 (繼承自 TelemetryChartWidgetBase)"""
    
    # 信號定義
    lap_selected = pyqtSignal(int, dict)    # 圈數, 圈數據
    data_point_clicked = pyqtSignal(dict)   # 數據點信息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 使用集中式 logger
        self._logger = get_logger("temp_chart", component="gui")
        
        # 圖表類型配置
        self.chart_types = {
            "primary": tr("rain_temp_chart", "降雨+氣溫"),
            "temperature": tr("temp_comparison_chart", "溫度對比"),
            "humidity_wind": tr("humidity_wind_chart", "濕度+風速"),
            "pressure": tr("pressure_chart", "氣壓變化")
        }
        
        self.current_chart_type = "primary"
        self.chart_data = {}
        
        # 使用翻譯的統一座標軸標題配置
        self.set_axis_titles(
            tr("lap_number", "Lap Number"), 
            tr("temperature_celsius", "Temperature (C)")
        )
        # X軸標題置中顯示，Y軸標題在中間垂直顯示
        self.set_axis_title_positions("bottom-center", "left-center")
        
        # 調試：確認座標軸標籤設置
        self._logger.debug("[TEMP_AXIS_DEBUG] 座標軸標題設置")
        self._logger.debug("[TEMP_AXIS_DEBUG]   X軸標題: %s", self.x_axis_title)
        self._logger.debug("[TEMP_AXIS_DEBUG]   左Y軸標題: %s", self.y_axis_left_title)
        
        # 圖表數據
        self.lap_data = []
        self.rainfall_data = []
        self.air_temp_data = []
        self.track_temp_data = []
        self.humidity_data = []
        self.wind_speed_data = []
        self.pressure_data = []
        
        # 數據範圍
        self.x_min = 0
        self.x_max = 60
        self.y_left_min = 0
        self.y_left_max = 50
        self.y_right_min = 0
        self.y_right_max = 100
        
        # 圖表區域（將在 paintEvent 中計算）
        self.chart_area = QRect()
        
        # 佈局參數
        self.left_margin = 70
        self.right_margin = 70
        self.top_margin = 40
        self.bottom_margin = 60
        
        # 顯示選項
        self.show_grid = True
        self.show_legend = True
        self.show_rainfall = True
        self.show_temperature = True
        
        # 互動狀態
        self.hover_pos = None
        self.is_dragging = False
        self.drag_start = None
        
        # 固定線（用於標記特定圈數）
        self.fixed_line_x = None
        
        # 縮放和平移
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        
        # 設定最小尺寸
        self.setMinimumSize(200, 100)
        self.setMouseTracking(True)
        
        # 設定樣式
        self.setup_temp_chart_style()
        
        self._logger.debug("[TEMP_CHART] 溫度分析圖表組件初始化完成")
    
    def set_axis_titles(self, x_title: str, y_title: str):
        """設定座標軸標題"""
        self.x_axis_title = x_title
        self.y_axis_left_title = y_title
        self.y_axis_right_title = tr("rainfall_status", "Rainfall")
    
    def set_axis_title_positions(self, x_pos: str, y_pos: str):
        """設定座標軸標題位置"""
        self.x_title_position = x_pos
        self.y_title_position = y_pos
    
    def setup_temp_chart_style(self):
        """設定溫度分析圖表樣式"""
        # 溫度相關顏色配置
        self.temp_colors = {
            "rainfall": TempChartTheme.RAINFALL_COLOR,
            "air_temp": TempChartTheme.AIR_TEMP_COLOR,
            "track_temp": TempChartTheme.TRACK_TEMP_COLOR,
            "humidity": TempChartTheme.HUMIDITY_COLOR,
            "wind_speed": TempChartTheme.WIND_SPEED_COLOR,
            "pressure": TempChartTheme.PRESSURE_COLOR
        }
        
        self._logger.debug("[TEMP_STYLE] 圖表樣式初始化完成")
    
    def update_data(self, data: Dict[str, Any]):
        """更新圖表數據
        
        Args:
            data: 包含天氣分析數據的字典
        """
        try:
            self._logger.debug("[TEMP_CHART] 收到數據更新: %s", type(data))
            
            self.chart_data = data
            
            # 解析數據結構
            if isinstance(data, dict):
                # 嘗試提取圈數天氣數據
                lap_weather = data.get('lap_weather_data', {})
                charts_data = data.get('charts_data', {})
                
                if lap_weather:
                    self._process_lap_weather_data(lap_weather)
                elif charts_data:
                    self._process_charts_data(charts_data)
                else:
                    # 直接使用數據
                    self._process_direct_data(data)
            
            # 計算數據範圍
            self._calculate_data_ranges()
            
            self._logger.debug("[TEMP_CHART] 數據處理完成: %d 圈", len(self.lap_data))
            
            self.update()
            
        except Exception as e:
            self._logger.exception("[TEMP_CHART] 數據更新錯誤: %s", str(e))
    
    def _process_lap_weather_data(self, lap_weather: Dict[str, Any]):
        """處理圈數天氣數據"""
        self.lap_data = []
        self.rainfall_data = []
        self.air_temp_data = []
        self.track_temp_data = []
        self.humidity_data = []
        self.wind_speed_data = []
        self.pressure_data = []
        
        # 按圈數排序
        lap_numbers = sorted([int(lap) for lap in lap_weather.keys() if lap.isdigit()])
        
        for lap_num in lap_numbers:
            lap_str = str(lap_num)
            lap_info = lap_weather.get(lap_str, {})
            
            self.lap_data.append(lap_num)
            
            # 降雨狀態（布林值轉數值）
            weather = lap_info.get('weather', {})
            rainfall = weather.get('rainfall', False)
            self.rainfall_data.append(1 if rainfall else 0)
            
            # 溫度數據
            temp_data = lap_info.get('temperature', {})
            self.air_temp_data.append(temp_data.get('air_temp', 0))
            self.track_temp_data.append(temp_data.get('track_temp', 0))
            
            # 濕度
            self.humidity_data.append(lap_info.get('humidity', 0))
            
            # 風速
            wind = lap_info.get('wind', {})
            self.wind_speed_data.append(wind.get('speed', 0))
            
            # 氣壓
            self.pressure_data.append(weather.get('pressure', 0))
        
        self._logger.debug("[TEMP_CHART] 處理了 %d 圈天氣數據", len(self.lap_data))
    
    def _process_charts_data(self, charts_data: Dict[str, Any]):
        """處理圖表數據格式"""
        primary = charts_data.get('primary', {})
        
        if 'x_data' in primary:
            self.lap_data = primary['x_data']
        if 'y1_data' in primary:
            self.rainfall_data = primary['y1_data']
        if 'y2_data' in primary:
            self.air_temp_data = primary['y2_data']
        
        # 溫度對比數據
        temp_data = charts_data.get('temperature', {})
        if 'y1_data' in temp_data:
            self.air_temp_data = temp_data['y1_data']
        if 'y2_data' in temp_data:
            self.track_temp_data = temp_data['y2_data']
        
        # 濕度風速數據
        hw_data = charts_data.get('humidity_wind', {})
        if 'y1_data' in hw_data:
            self.humidity_data = hw_data['y1_data']
        if 'y2_data' in hw_data:
            self.wind_speed_data = hw_data['y2_data']
        
        # 氣壓數據
        pressure_data = charts_data.get('pressure', {})
        if 'y_data' in pressure_data:
            self.pressure_data = pressure_data['y_data']
        
        self._logger.debug("[TEMP_CHART] 處理了圖表數據格式")
    
    def _process_direct_data(self, data: Dict[str, Any]):
        """處理直接數據格式"""
        self.lap_data = data.get('laps', [])
        self.rainfall_data = data.get('rainfall', [])
        self.air_temp_data = data.get('air_temp', [])
        self.track_temp_data = data.get('track_temp', [])
        self.humidity_data = data.get('humidity', [])
        self.wind_speed_data = data.get('wind_speed', [])
        self.pressure_data = data.get('pressure', [])
        
        self._logger.debug("[TEMP_CHART] 處理了直接數據格式")
    
    def set_data(self, *args, **kwargs):
        """設置數據的別名方法"""
        if args and isinstance(args[0], dict):
            self.update_data(args[0])
        elif 'data' in kwargs:
            self.update_data(kwargs['data'])
    
    def update_chart_data(self, data: Dict[str, Any]):
        """更新圖表數據（別名）"""
        self.update_data(data)
    
    def _calculate_data_ranges(self):
        """計算數據範圍 (2025-12-21 更新)"""
        # X軸範圍（圈數）
        if self.lap_data:
            self.x_min = min(self.lap_data)
            self.x_max = max(self.lap_data)
        else:
            self.x_min = 0
            self.x_max = 60
        
        # 確保範圍有意義
        if self.x_min == self.x_max:
            self.x_max = self.x_min + 1
        
        # 左Y軸範圍（根據圖表類型）
        if self.current_chart_type == "primary":
            # 新版設計：左軸是溫度(氣溫+賽道溫度)，右軸是風速
            all_temps = []
            if self.air_temp_data:
                all_temps.extend(self.air_temp_data)
            if self.track_temp_data:
                all_temps.extend(self.track_temp_data)
            
            if all_temps:
                self.y_left_min = min(all_temps) - 5
                self.y_left_max = max(all_temps) + 5
            else:
                self.y_left_min = 0
                self.y_left_max = 60
            
            # 右軸是風速
            if self.wind_speed_data:
                self.y_right_min = max(0, min(self.wind_speed_data) - 2)
                self.y_right_max = max(self.wind_speed_data) + 2
            else:
                self.y_right_min = 0
                self.y_right_max = 20
        
        elif self.current_chart_type == "temperature":
            # 溫度對比：氣溫 vs 賽道溫度
            all_temps = self.air_temp_data + self.track_temp_data
            if all_temps:
                self.y_left_min = min(all_temps) - 5
                self.y_left_max = max(all_temps) + 5
            else:
                self.y_left_min = 0
                self.y_left_max = 60
            self.y_right_min = self.y_left_min
            self.y_right_max = self.y_left_max
        
        elif self.current_chart_type == "humidity_wind":
            # 濕度 + 風速
            if self.humidity_data:
                self.y_left_min = min(self.humidity_data) - 5
                self.y_left_max = max(max(self.humidity_data) + 5, 100)
            else:
                self.y_left_min = 0
                self.y_left_max = 100
            
            if self.wind_speed_data:
                self.y_right_min = min(self.wind_speed_data) - 1
                self.y_right_max = max(self.wind_speed_data) + 2
            else:
                self.y_right_min = 0
                self.y_right_max = 20
        
        elif self.current_chart_type == "pressure":
            # 氣壓
            if self.pressure_data:
                self.y_left_min = min(self.pressure_data) - 10
                self.y_left_max = max(self.pressure_data) + 10
            else:
                self.y_left_min = 900
                self.y_left_max = 1100
            self.y_right_min = self.y_left_min
            self.y_right_max = self.y_left_max
        
        self._logger.debug("[TEMP_RANGE] X: %.1f-%.1f, Y_L: %.1f-%.1f, Y_R: %.1f-%.1f",
                          self.x_min, self.x_max, self.y_left_min, self.y_left_max,
                          self.y_right_min, self.y_right_max)
    
    def paintEvent(self, event):
        """繪製事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 計算圖表區域
        self._calculate_chart_areas()
        
        # 繪製背景
        self._draw_background(painter)
        
        # 繪製網格
        if self.show_grid:
            self._draw_grid(painter)
        
        # 繪製座標軸
        self._draw_axes(painter)
        
        # 繪製軸標籤
        self._draw_axis_labels(painter)
        
        # 繪製自定義軸標題
        self._draw_custom_axis_titles(painter)
        
        # 繪製數據
        self._draw_data(painter)
        
        # 繪製固定線
        if self.fixed_line_x is not None:
            self._draw_fixed_line(painter)
        
        # 繪製圖例
        if self.show_legend:
            self._draw_legend(painter)
        
        # 繪製滑鼠追蹤虛線
        if self.hover_pos and self.chart_area.contains(self.hover_pos):
            self._draw_crosshair_line(painter)
        
        # 繪製提示
        if self.hover_pos:
            self._draw_tooltip(painter)
        
        painter.end()
    
    def _calculate_chart_areas(self):
        """計算圖表區域"""
        width = self.width()
        height = self.height()
        
        self.chart_area = QRect(
            self.left_margin,
            self.top_margin,
            width - self.left_margin - self.right_margin,
            height - self.top_margin - self.bottom_margin
        )
    
    def _draw_background(self, painter: QPainter):
        """繪製背景"""
        # 主背景
        painter.fillRect(self.rect(), TempChartTheme.MAIN_BACKGROUND)
        
        # 圖表區域背景
        painter.fillRect(self.chart_area, TempChartTheme.CHART_BACKGROUND)
    
    def _draw_grid(self, painter: QPainter):
        """繪製網格"""
        pen = QPen(TempChartTheme.GRID_COLOR)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        # 垂直網格線（X軸）
        x_range = self.x_max - self.x_min
        if x_range > 0:
            step = max(1, x_range // 10)
            x = self.x_min
            while x <= self.x_max:
                px = self._map_x_to_pixel(x)
                painter.drawLine(px, self.chart_area.top(), px, self.chart_area.bottom())
                x += step
        
        # 水平網格線（Y軸）
        y_range = self.y_left_max - self.y_left_min
        if y_range > 0:
            step = y_range / 5
            y = self.y_left_min
            while y <= self.y_left_max:
                py = self._map_left_y_to_pixel(y)
                painter.drawLine(self.chart_area.left(), py, self.chart_area.right(), py)
                y += step
    
    def _draw_axes(self, painter: QPainter):
        """繪製座標軸"""
        pen = QPen(TempChartTheme.AXIS_COLOR)
        pen.setWidth(2)
        painter.setPen(pen)
        
        # X軸
        painter.drawLine(
            self.chart_area.left(), self.chart_area.bottom(),
            self.chart_area.right(), self.chart_area.bottom()
        )
        
        # 左Y軸
        painter.drawLine(
            self.chart_area.left(), self.chart_area.top(),
            self.chart_area.left(), self.chart_area.bottom()
        )
        
        # 右Y軸
        painter.drawLine(
            self.chart_area.right(), self.chart_area.top(),
            self.chart_area.right(), self.chart_area.bottom()
        )
    
    def _draw_axis_labels(self, painter: QPainter):
        """繪製軸標籤"""
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(TempChartTheme.TEXT_COLOR)
        
        fm = QFontMetrics(font)
        
        # X軸標籤
        x_range = self.x_max - self.x_min
        if x_range > 0:
            step = max(1, x_range // 10)
            x = self.x_min
            while x <= self.x_max:
                px = self._map_x_to_pixel(x)
                label = str(int(x))
                label_width = fm.horizontalAdvance(label)
                painter.drawText(
                    px - label_width // 2,
                    self.chart_area.bottom() + 15,
                    label
                )
                x += step
        
        # 左Y軸標籤
        y_range = self.y_left_max - self.y_left_min
        if y_range > 0:
            step = y_range / 5
            y = self.y_left_min
            while y <= self.y_left_max:
                py = self._map_left_y_to_pixel(y)
                label = f"{y:.1f}"
                label_width = fm.horizontalAdvance(label)
                painter.drawText(
                    self.chart_area.left() - label_width - 5,
                    py + fm.height() // 4,
                    label
                )
                y += step
        
        # 右Y軸標籤
        y_range = self.y_right_max - self.y_right_min
        if y_range > 0:
            step = y_range / 5
            y = self.y_right_min
            while y <= self.y_right_max:
                py = self._map_right_y_to_pixel(y)
                label = f"{y:.1f}"
                painter.drawText(
                    self.chart_area.right() + 5,
                    py + fm.height() // 4,
                    label
                )
                y += step
    
    def _draw_custom_axis_titles(self, painter: QPainter):
        """繪製自定義軸標題"""
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(TempChartTheme.TEXT_COLOR)
        
        fm = QFontMetrics(font)
        
        # X軸標題
        x_title = self.x_axis_title
        x_title_width = fm.horizontalAdvance(x_title)
        painter.drawText(
            self.chart_area.center().x() - x_title_width // 2,
            self.height() - 10,
            x_title
        )
        
        # 左Y軸標題（垂直）
        painter.save()
        painter.translate(15, self.chart_area.center().y())
        painter.rotate(-90)
        y_left_title = self._get_left_axis_title()
        y_left_width = fm.horizontalAdvance(y_left_title)
        painter.drawText(-y_left_width // 2, 0, y_left_title)
        painter.restore()
        
        # 右Y軸標題（垂直）
        painter.save()
        painter.translate(self.width() - 10, self.chart_area.center().y())
        painter.rotate(90)
        y_right_title = self._get_right_axis_title()
        y_right_width = fm.horizontalAdvance(y_right_title)
        painter.drawText(-y_right_width // 2, 0, y_right_title)
        painter.restore()
    
    def _get_left_axis_title(self) -> str:
        """獲取左Y軸標題 (2025-12-21 更新)"""
        if self.current_chart_type == "primary":
            return tr("temperature_celsius", "Temperature (C)")  # 新版：左軸是溫度
        elif self.current_chart_type == "temperature":
            return tr("air_temperature", "Air Temperature (C)")
        elif self.current_chart_type == "humidity_wind":
            return tr("humidity", "Humidity (%)")
        elif self.current_chart_type == "pressure":
            return tr("pressure", "Pressure (hPa)")
        return self.y_axis_left_title
    
    def _get_right_axis_title(self) -> str:
        """獲取右Y軸標題 (2025-12-21 更新)"""
        if self.current_chart_type == "primary":
            return tr("wind_speed", "Wind Speed (m/s)")  # 新版：右軸是風速
        elif self.current_chart_type == "temperature":
            return tr("track_temperature", "Track Temperature (C)")
        elif self.current_chart_type == "humidity_wind":
            return tr("wind_speed", "Wind Speed (m/s)")
        elif self.current_chart_type == "pressure":
            return ""
        return self.y_axis_right_title
    
    def _draw_data(self, painter: QPainter):
        """繪製數據"""
        if not self.lap_data:
            # 無數據時顯示提示
            painter.setPen(TempChartTheme.TEXT_COLOR)
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(
                self.chart_area,
                Qt.AlignCenter,
                tr("no_data_available", "No Data Available")
            )
            return
        
        # 根據圖表類型繪製不同的數據
        chart_info = self._get_chart_info()
        
        if self.current_chart_type == "primary":
            self._draw_rainfall_temperature(painter, chart_info)
        elif self.current_chart_type == "temperature":
            self._draw_temperature_comparison(painter, chart_info)
        elif self.current_chart_type == "humidity_wind":
            self._draw_humidity_wind(painter, chart_info)
        elif self.current_chart_type == "pressure":
            self._draw_pressure(painter, chart_info)
    
    def _get_chart_info(self) -> Dict[str, Any]:
        """獲取圖表信息"""
        return {
            "laps": self.lap_data,
            "rainfall": self.rainfall_data,
            "air_temp": self.air_temp_data,
            "track_temp": self.track_temp_data,
            "humidity": self.humidity_data,
            "wind_speed": self.wind_speed_data,
            "pressure": self.pressure_data
        }
    
    def _draw_rainfall_temperature(self, painter: QPainter, chart_info: Dict[str, Any]):
        """繪製新版溫度圖表：雙Y軸 + 降雨區域
        
        設計：
        - 左 Y 軸：氣溫 (#FF6B6B) + 賽道溫度 (#FF9F43)
        - 右 Y 軸：風速 (#1DD1A1)
        - 降雨區域：全高度透明藍色區域 (rgba(100,149,237,0.3))
        """
        laps = chart_info.get('laps', [])
        rainfall = chart_info.get('rainfall', [])
        air_temp = chart_info.get('air_temp', [])
        track_temp = chart_info.get('track_temp', [])
        wind_speed = chart_info.get('wind_speed', [])
        
        if not laps:
            return
        
        # 1. 繪製降雨區域（全高度透明藍色背景）
        bar_width = max(2, (self.chart_area.width() // len(laps)))
        for i, (lap, rain) in enumerate(zip(laps, rainfall)):
            if rain > 0:  # 有降雨
                px = self._map_x_to_pixel(lap)
                # 全高度區域
                painter.fillRect(
                    px - bar_width // 2, 
                    self.chart_area.top(),
                    bar_width, 
                    self.chart_area.height(),
                    TempChartTheme.RAINFALL_AREA_COLOR
                )
        
        # 2. 繪製氣溫折線（左Y軸，珊瑚紅 #FF6B6B）
        self._draw_line_chart(painter, laps, air_temp, TempChartTheme.AIR_TEMP_COLOR, "left")
        
        # 3. 繪製賽道溫度折線（左Y軸，橘黃 #FF9F43）
        if track_temp:
            self._draw_line_chart(painter, laps, track_temp, TempChartTheme.TRACK_TEMP_COLOR, "left")
        
        # 4. 繪製風速折線（右Y軸，青綠 #1DD1A1）
        if wind_speed:
            self._draw_line_chart(painter, laps, wind_speed, TempChartTheme.WIND_SPEED_COLOR, "right")
    
    def _draw_temperature_comparison(self, painter: QPainter, chart_info: Dict[str, Any]):
        """繪製溫度對比圖表"""
        laps = chart_info.get('laps', [])
        air_temp = chart_info.get('air_temp', [])
        track_temp = chart_info.get('track_temp', [])
        
        # 繪製氣溫折線
        self._draw_line_chart(painter, laps, air_temp, TempChartTheme.AIR_TEMP_COLOR, "left")
        
        # 繪製賽道溫度折線
        self._draw_line_chart(painter, laps, track_temp, TempChartTheme.TRACK_TEMP_COLOR, "left")
    
    def _draw_humidity_wind(self, painter: QPainter, chart_info: Dict[str, Any]):
        """繪製濕度+風速圖表"""
        laps = chart_info.get('laps', [])
        humidity = chart_info.get('humidity', [])
        wind_speed = chart_info.get('wind_speed', [])
        
        # 繪製濕度折線
        self._draw_line_chart(painter, laps, humidity, TempChartTheme.HUMIDITY_COLOR, "left")
        
        # 繪製風速折線
        self._draw_line_chart(painter, laps, wind_speed, TempChartTheme.WIND_SPEED_COLOR, "right")
    
    def _draw_pressure(self, painter: QPainter, chart_info: Dict[str, Any]):
        """繪製氣壓圖表"""
        laps = chart_info.get('laps', [])
        pressure = chart_info.get('pressure', [])
        
        # 繪製氣壓折線
        self._draw_line_chart(painter, laps, pressure, TempChartTheme.PRESSURE_COLOR, "left")
    
    def _draw_line_chart(self, painter: QPainter, x_data: List, y_data: List,
                        color: QColor, y_axis: str):
        """繪製平滑曲線圖（無圓點標記）"""
        if not x_data or not y_data or len(x_data) != len(y_data):
            return
        
        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 計算所有數據點的像素座標
        points = []
        for x, y in zip(x_data, y_data):
            px = self._map_x_to_pixel(x)
            if y_axis == "left":
                py = self._map_left_y_to_pixel(y)
            else:
                py = self._map_right_y_to_pixel(y)
            points.append(QPointF(px, py))
        
        if len(points) < 2:
            return
        
        # 使用 QPainterPath 繪製平滑曲線（Catmull-Rom 樣條插值）
        path = QPainterPath()
        path.moveTo(points[0])
        
        for i in range(len(points) - 1):
            # 計算控制點（使用相鄰點來平滑曲線）
            p0 = points[max(0, i - 1)]
            p1 = points[i]
            p2 = points[i + 1]
            p3 = points[min(len(points) - 1, i + 2)]
            
            # Catmull-Rom 轉換為 Bezier 控制點
            # 張力因子 0.5 提供平滑過渡
            tension = 0.5
            
            cp1x = p1.x() + (p2.x() - p0.x()) * tension / 3
            cp1y = p1.y() + (p2.y() - p0.y()) * tension / 3
            cp2x = p2.x() - (p3.x() - p1.x()) * tension / 3
            cp2y = p2.y() - (p3.y() - p1.y()) * tension / 3
            
            path.cubicTo(cp1x, cp1y, cp2x, cp2y, p2.x(), p2.y())
        
        painter.drawPath(path)
        
        # 不繪製數據點圓圈（已移除）
    
    def _draw_fixed_line(self, painter: QPainter):
        """繪製固定線"""
        if self.fixed_line_x is None:
            return
        
        px = self._map_x_to_pixel(self.fixed_line_x)
        
        pen = QPen(QColor(255, 0, 0))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        painter.drawLine(px, self.chart_area.top(), px, self.chart_area.bottom())
    
    def _draw_legend(self, painter: QPainter):
        """繪製圖例 (2025-12-21 更新)"""
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        fm = QFontMetrics(font)
        
        # 圖例項目
        legend_items = []
        
        if self.current_chart_type == "primary":
            # 新版設計：氣溫、賽道溫度、風速、降雨區域
            legend_items = [
                (TempChartTheme.AIR_TEMP_COLOR, tr("air_temp", "Air Temp")),
                (TempChartTheme.TRACK_TEMP_COLOR, tr("track_temp", "Track Temp")),
                (TempChartTheme.WIND_SPEED_COLOR, tr("wind_speed", "Wind Speed")),
                (TempChartTheme.RAINFALL_AREA_COLOR, tr("rainfall_area", "Rainfall"))
            ]
        elif self.current_chart_type == "temperature":
            legend_items = [
                (TempChartTheme.AIR_TEMP_COLOR, tr("air_temp", "Air Temp")),
                (TempChartTheme.TRACK_TEMP_COLOR, tr("track_temp", "Track Temp"))
            ]
        elif self.current_chart_type == "humidity_wind":
            legend_items = [
                (TempChartTheme.HUMIDITY_COLOR, tr("humidity", "Humidity")),
                (TempChartTheme.WIND_SPEED_COLOR, tr("wind_speed", "Wind Speed"))
            ]
        elif self.current_chart_type == "pressure":
            legend_items = [
                (TempChartTheme.PRESSURE_COLOR, tr("pressure", "Pressure"))
            ]
        
        # 計算圖例位置
        x = self.chart_area.right() - 100
        y = self.chart_area.top() + 10
        
        for color, text in legend_items:
            # 繪製顏色方塊 - 使用 QBrush 確保顏色正確
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(TempChartTheme.DEFAULT_BORDER_COLOR))
            painter.drawRect(x, y, 12, 12)
            
            # 繪製文字
            painter.setPen(TempChartTheme.TEXT_COLOR)
            painter.drawText(x + 18, y + 10, text)
            
            y += 18
    
    def _draw_tooltip(self, painter: QPainter):
        """繪製提示框"""
        if not self.hover_pos or not self.chart_area.contains(self.hover_pos):
            return
        
        # 查找最近的數據點
        if not self.lap_data:
            return
        
        # 將像素位置轉換為數據值
        x_val = self._pixel_to_x(self.hover_pos.x())
        
        # 找到最近的圈數
        closest_idx = 0
        min_dist = float('inf')
        for i, lap in enumerate(self.lap_data):
            dist = abs(lap - x_val)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i
        
        if closest_idx >= len(self.lap_data):
            return
        
        # 構建提示文字
        lap = self.lap_data[closest_idx]
        lines = [tr("lap_tooltip", "Lap: {lap}").format(lap=lap)]
        
        if self.current_chart_type == "primary":
            if closest_idx < len(self.rainfall_data):
                rain = "Yes" if self.rainfall_data[closest_idx] else "No"
                lines.append(tr("rainfall_tooltip", "Rainfall: {rain}").format(rain=rain))
            if closest_idx < len(self.air_temp_data):
                temp = self.air_temp_data[closest_idx]
                lines.append(tr("air_temp_tooltip", "Air Temp: {temp:.1f}C").format(temp=temp))
            if closest_idx < len(self.track_temp_data):
                track_temp = self.track_temp_data[closest_idx]
                lines.append(tr("track_temp_tooltip", "Track Temp: {temp:.1f}C").format(temp=track_temp))
        
        elif self.current_chart_type == "temperature":
            if closest_idx < len(self.air_temp_data):
                temp = self.air_temp_data[closest_idx]
                lines.append(tr("air_temp_tooltip", "Air Temp: {temp:.1f}C").format(temp=temp))
            if closest_idx < len(self.track_temp_data):
                temp = self.track_temp_data[closest_idx]
                lines.append(tr("track_temp_tooltip", "Track Temp: {temp:.1f}C").format(temp=temp))
        
        elif self.current_chart_type == "humidity_wind":
            if closest_idx < len(self.humidity_data):
                hum = self.humidity_data[closest_idx]
                lines.append(tr("humidity_tooltip", "Humidity: {hum:.1f}%").format(hum=hum))
            if closest_idx < len(self.wind_speed_data):
                wind = self.wind_speed_data[closest_idx]
                lines.append(tr("wind_speed_tooltip", "Wind: {wind:.1f}m/s").format(wind=wind))
        
        elif self.current_chart_type == "pressure":
            if closest_idx < len(self.pressure_data):
                pres = self.pressure_data[closest_idx]
                lines.append(tr("pressure_tooltip", "Pressure: {pres:.1f}hPa").format(pres=pres))
        
        # 繪製提示框
        fm = QFontMetrics(painter.font())
        line_height = fm.height()
        
        # 計算文字區域大小
        max_width = 0
        for line in lines:
            max_width = max(max_width, fm.horizontalAdvance(line))
        text_height = line_height * len(lines)
        
        # 計算提示框位置
        tooltip_x = self.hover_pos.x() + 10
        tooltip_y = self.hover_pos.y() - text_height - 10
        
        # 確保在視圖內
        if tooltip_x + max_width + 10 > self.width():
            tooltip_x = self.hover_pos.x() - max_width - 20
        if tooltip_y < 0:
            tooltip_y = self.hover_pos.y() + 10
        
        # 繪製背景
        bg_rect = QRect(tooltip_x - 5, tooltip_y - 5, max_width + 15, text_height + 12)
        painter.fillRect(bg_rect, QColor(255, 255, 255, 230))
        painter.setPen(TempChartTheme.DEFAULT_BORDER_COLOR)
        painter.drawRect(bg_rect)
        
        # 繪製每行文字
        painter.setPen(TempChartTheme.TEXT_COLOR)
        current_y = tooltip_y + line_height - 2
        for line in lines:
            painter.drawText(tooltip_x, current_y, line)
            current_y += line_height
    
    def _draw_crosshair_line(self, painter: QPainter):
        """繪製滑鼠追蹤垂直虛線"""
        if not self.hover_pos:
            return
        
        x = self.hover_pos.x()
        
        # 確保在圖表區域內
        if x < self.chart_area.left() or x > self.chart_area.right():
            return
        
        # 設置黑色虛線樣式
        pen = QPen(QColor(0, 0, 0))  # 黑色
        pen.setStyle(Qt.DashLine)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 繪製垂直線
        painter.drawLine(
            x, self.chart_area.top(),
            x, self.chart_area.bottom()
        )
    
    def _pixel_to_x(self, px: int) -> float:
        """將像素X座標轉換為數據值"""
        if self.chart_area.width() == 0:
            return self.x_min
        ratio = (px - self.chart_area.left()) / self.chart_area.width()
        return self.x_min + ratio * (self.x_max - self.x_min)
    
    def _map_x_to_pixel(self, x_val: float) -> int:
        """將X數據值轉換為像素座標"""
        x_range = self.x_max - self.x_min
        if x_range == 0:
            return self.chart_area.left()
        ratio = (x_val - self.x_min) / x_range
        return int(self.chart_area.left() + ratio * self.chart_area.width())
    
    def _map_left_y_to_pixel(self, y_val: float) -> int:
        """將左Y軸數據值轉換為像素座標"""
        y_range = self.y_left_max - self.y_left_min
        if y_range == 0:
            return self.chart_area.center().y()
        ratio = (y_val - self.y_left_min) / y_range
        return int(self.chart_area.bottom() - ratio * self.chart_area.height())
    
    def _map_right_y_to_pixel(self, y_val: float) -> int:
        """將右Y軸數據值轉換為像素座標"""
        y_range = self.y_right_max - self.y_right_min
        if y_range == 0:
            return self.chart_area.center().y()
        ratio = (y_val - self.y_right_min) / y_range
        return int(self.chart_area.bottom() - ratio * self.chart_area.height())
    
    def switch_chart_type(self, chart_type: str):
        """切換圖表類型"""
        if chart_type in self.chart_types:
            self._logger.debug("[TEMP_CHART] 切換圖表類型: %s -> %s", 
                             self.current_chart_type, chart_type)
            self.current_chart_type = chart_type
            self._calculate_data_ranges()
            self.update()
    
    def wheelEvent(self, event):
        """滾輪事件處理（縮放）"""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1
        
        self.zoom_level = max(0.5, min(5.0, self.zoom_level))
        self.update()
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.hover_pos = None
        self.update()
    
    def reset_zoom(self):
        """重置縮放"""
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """滑鼠按下事件"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start = event.pos()
            self._handle_data_point_click(event.pos())
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """滑鼠釋放事件"""
        self.is_dragging = False
        self.drag_start = None
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """滑鼠移動事件"""
        self.hover_pos = event.pos()
        
        if self.is_dragging and self.drag_start:
            # 平移
            delta = event.pos() - self.drag_start
            self.pan_offset += delta
            self.drag_start = event.pos()
        
        self._update_tooltip(event.pos())
        self.update()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """滑鼠雙擊事件"""
        if event.button() == Qt.LeftButton:
            # 設置固定線
            if self.chart_area.contains(event.pos()):
                self.fixed_line_x = self._pixel_to_x(event.pos().x())
                self.update()
    
    def update_display_options(self, option: str, value: bool):
        """更新顯示選項"""
        if option == "show_grid":
            self.show_grid = value
        elif option == "show_legend":
            self.show_legend = value
        elif option == "show_rainfall":
            self.show_rainfall = value
        elif option == "show_temperature":
            self.show_temperature = value
        
        self._logger.debug("[TEMP_CHART] 更新顯示選項: %s = %s", option, value)
        self.update()
    
    def _handle_data_point_click(self, pos: QPoint):
        """處理數據點點擊"""
        if not self.chart_area.contains(pos) or not self.lap_data:
            return
        
        x_val = self._pixel_to_x(pos.x())
        
        # 找到最近的圈數
        closest_idx = 0
        min_dist = float('inf')
        for i, lap in enumerate(self.lap_data):
            dist = abs(lap - x_val)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i
        
        if closest_idx < len(self.lap_data):
            lap_num = self.lap_data[closest_idx]
            lap_data = {
                'lap': lap_num,
                'rainfall': self.rainfall_data[closest_idx] if closest_idx < len(self.rainfall_data) else None,
                'air_temp': self.air_temp_data[closest_idx] if closest_idx < len(self.air_temp_data) else None,
                'track_temp': self.track_temp_data[closest_idx] if closest_idx < len(self.track_temp_data) else None
            }
            self.lap_selected.emit(lap_num, lap_data)
            self.data_point_clicked.emit(lap_data)
    
    def _update_tooltip(self, pos: QPoint):
        """更新提示框"""
        self.hover_pos = pos
    
    def resizeEvent(self, event):
        """視窗大小改變事件"""
        super().resizeEvent(event)
        self._calculate_chart_areas()
        self.update()
    
    def get_chart_area(self) -> QRect:
        """獲取圖表區域"""
        return self.chart_area
    
    def update_chart_layout(self):
        """更新圖表佈局"""
        self._calculate_chart_areas()
        self.update()
    
    def clear_fixed_line(self):
        """清除固定線"""
        self.fixed_line_x = None
        self.update()
    
    def reset_view(self):
        """重置視圖"""
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.fixed_line_x = None
        self.update()
    
    def get_current_lap_range(self) -> Tuple[float, float]:
        """獲取當前圈數範圍"""
        return (self.x_min, self.x_max)
