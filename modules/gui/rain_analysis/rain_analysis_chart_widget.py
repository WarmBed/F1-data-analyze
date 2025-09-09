#!/usr/bin/env python3
"""
RainAnalysisChartWidget - F1T 下雨分析圖表組件
==============================================

專門用於下雨分析的圖表組件，支援：
- 雙Y軸圖表（降雨+溫度）
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
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QFontMetrics

# 導入基礎圖表組件
try:
    from ..base.universal_chart_widget_base import TelemetryChartWidgetBase, ChartTheme
except ImportError:
    from modules.gui.base.universal_chart_widget_base import TelemetryChartWidgetBase, ChartTheme


class RainChartTheme(ChartTheme):
    """下雨分析專用圖表主題"""
    
    # 背景顏色覆蓋
    BACKGROUND = QColor(250, 251, 252)          # 降雨分析專用淺背景
    MAIN_BACKGROUND = QColor(250, 251, 252)     # 主背景
    CHART_BACKGROUND = QColor(248, 249, 250)    # 圖表區域
    
    # 文字和標籤顏色
    LABEL_COLOR = QColor(50, 50, 50)           # 標籤顏色（與 TEXT_COLOR 一致）
    TEXT_COLOR = QColor(50, 50, 50)            # 文字顏色
    AXIS_COLOR = QColor(50, 50, 50)            # 座標軸顏色
    GRID_COLOR = QColor(200, 200, 200)         # 網格顏色
    
    # 天氣相關顏色
    RAINFALL_COLOR = QColor(52, 152, 219)       # 藍色 - 降雨
    AIR_TEMP_COLOR = QColor(255, 140, 0)        # 橘色 - 氣溫
    TRACK_TEMP_COLOR = QColor(230, 126, 34)     # 橙色 - 賽道溫度
    HUMIDITY_COLOR = QColor(46, 204, 113)       # 綠色 - 濕度
    WIND_SPEED_COLOR = QColor(155, 89, 182)     # 紫色 - 風速
    PRESSURE_COLOR = QColor(52, 73, 94)         # 深灰色 - 氣壓
    
    # 降雨狀態特殊顏色
    RAIN_TRUE_COLOR = QColor(135, 206, 250, 51)   # 有雨 - 淺藍色，透明度80% (255*0.2=51)
    RAIN_FALSE_COLOR = QColor(236, 240, 241)      # 無雨 - 淺灰色
    
    # 圖表背景（向後兼容）
    RAIN_CHART_BG = QColor(250, 251, 252)       # 淺背景


class RainAnalysisChartWidget(TelemetryChartWidgetBase):
    """下雨分析圖表組件"""
    
    # 圖表切換信號
    chart_type_switched = pyqtSignal(str)
    data_point_selected = pyqtSignal(int, dict)  # 圈數, 數據點
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 下雨分析特定配置
        self.chart_types = {
            "primary": "降雨+氣溫",
            "temperature": "溫度對比", 
            "humidity_wind": "濕度+風速",
            "pressure": "氣壓變化"
        }
        
        self.current_chart_type = "primary"
        self.chart_data = {}
        
        # 圖表繪製區域
        self.chart_rect = QRect()
        self.left_y_axis_rect = QRect()
        self.right_y_axis_rect = QRect()
        self.x_axis_rect = QRect()
        
        # 數據範圍
        self.x_range = (0, 100)
        self.left_y_range = (0, 100)
        self.right_y_range = (0, 100)
        
        # 顯示選項
        self.show_grid = True
        self.show_legend = True
        self.show_tooltips = True
        
        # 縮放和拖拉參數（與遙測分析一致）
        self.y_scale = 1.0  # Y軸縮放倍率
        self.y_offset = 0   # Y軸偏移
        self.x_offset = 0   # X軸偏移
        self.x_scale = 1.0  # X軸縮放倍率
        
        # 拖拉狀態
        self.dragging = False
        self.last_drag_pos = QPoint()
        
        # 滑鼠追蹤
        self.setMouseTracking(True)
        
        # 工具提示
        self.tooltip_visible = False
        self.tooltip_data = {}
        self.tooltip_pos = QPoint()
        
        # 設定樣式
        self.setup_rain_chart_style()
        
    def setup_rain_chart_style(self):
        """設定下雨分析圖表樣式"""
        self.setMinimumSize(800, 400)
        self.setStyleSheet("""
            RainAnalysisChartWidget {
                background-color: white;
                border: 1px solid #ddd;
            }
        """)
        
        # 字型設定
        self.title_font = QFont("Arial", 14, QFont.Bold)
        self.axis_font = QFont("Arial", 10)
        self.label_font = QFont("Arial", 9)
        
    def update_data(self, data: Dict[str, Any]):
        """更新數據（基類優先方法）"""
        print(f"✅ [RAIN_CHART] update_data 被調用!")
        print(f"   - 自身類型: {type(self)}")
        print(f"   - 數據類型: {type(data)}")
        print(f"   - 數據鍵: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        import traceback
        print(f"🔍 [RAIN_CHART] update_data 調用堆棧:")
        traceback.print_stack(limit=3)
        self.update_chart_data(data)
        
    def set_data(self, *args, **kwargs):
        """設置圖表數據（兼容基類接口）"""
        print(f"⚠️ [RAIN_CHART] set_data 被調用!")
        print(f"   - 自身類型: {type(self)}")
        print(f"   - 位置參數數量: {len(args)}")
        print(f"   - 關鍵字參數: {list(kwargs.keys())}")
        print(f"   - 參數類型: {[type(arg) for arg in args]}")
        import traceback
        print(f"🔍 [RAIN_CHART] set_data 調用堆棧:")
        traceback.print_stack(limit=5)
        
        # 如果只有一個參數且是字典，使用我們的方法
        if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
            print(f"   - ✅ 單字典參數，轉向 update_chart_data")
            self.update_chart_data(args[0])
        else:
            print(f"   - ⚠️ 多參數調用，可能是基類接口")
            # 嘗試調用父類方法
            try:
                super().set_data(*args, **kwargs)
            except Exception as e:
                print(f"   - ❌ 父類調用失敗: {e}")
                print(f"   - 🔄 嘗試作為單一數據處理")
                if args:
                    self.update_chart_data(args[0] if isinstance(args[0], dict) else {'data': args[0]})
        
    def update_chart_data(self, data: Dict[str, Any]):
        """更新圖表數據"""
        try:
            if "charts_data" in data:
                self.chart_data = data["charts_data"]
                self._calculate_data_ranges()
                self.update()
                
        except Exception as e:
            print(f"[RAIN_CHART] 更新數據失敗: {str(e)}")
            
    def _calculate_data_ranges(self):
        """計算數據範圍"""
        if not self.chart_data or self.current_chart_type not in self.chart_data:
            return
            
        chart_info = self.chart_data[self.current_chart_type]
        
        # X軸範圍（圈數）
        if "x_data" in chart_info:
            x_data = chart_info["x_data"]
            if x_data:
                self.x_range = (min(x_data), max(x_data))
                
        # 左Y軸範圍（現在用於溫度顯示，使用y2_data）
        if "y2_data" in chart_info:
            temp_data = chart_info["y2_data"]  # 溫度數據
            if temp_data:
                min_val = min(temp_data)
                max_val = max(temp_data)
                margin = (max_val - min_val) * 0.1 if max_val > min_val else 1
                self.left_y_range = (min_val - margin, max_val + margin)
                
        # 取消右Y軸範圍計算
        # if "y2_data" in chart_info:
        #     y2_data = chart_info["y2_data"]
        #     if y2_data:
        #         min_val = min(y2_data)
        #         max_val = max(y2_data)
        #         margin = (max_val - min_val) * 0.1 if max_val > min_val else 1
        #         self.right_y_range = (min_val - margin, max_val + margin)
        elif "y_data" in chart_info:  # 單Y軸圖表
            y_data = chart_info["y_data"]
            if y_data:
                min_val = min(y_data)
                max_val = max(y_data)
                margin = (max_val - min_val) * 0.1 if max_val > min_val else 1
                self.left_y_range = (min_val - margin, max_val + margin)
                
    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗鋸齒
        painter.setRenderHint(QPainter.SmoothPixmapTransform)  # 平滑變換
        
        # 計算繪製區域
        self._calculate_chart_areas()
        
        # 繪製背景
        self._draw_background(painter)
        
        # 繪製網格
        if self.show_grid:
            self._draw_grid(painter)
            
        # 繪製座標軸
        self._draw_axes(painter)
        
        # 繪製數據
        self._draw_data(painter)
        
        # 繪製圖例
        if self.show_legend:
            self._draw_legend(painter)
            
        # 繪製工具提示
        if self.tooltip_visible:
            self._draw_tooltip(painter)
            
    def _calculate_chart_areas(self):
        """計算圖表區域"""
        width = self.width()
        height = self.height()
        
        # 邊距
        left_margin = 80
        right_margin = 80
        top_margin = 40
        bottom_margin = 60
        
        # 主圖表區域
        self.chart_rect = QRect(
            left_margin, top_margin,
            width - left_margin - right_margin,
            height - top_margin - bottom_margin
        )
        
        # 座標軸區域
        self.left_y_axis_rect = QRect(10, top_margin, 70, self.chart_rect.height())
        self.right_y_axis_rect = QRect(width - 70, top_margin, 60, self.chart_rect.height())
        self.x_axis_rect = QRect(left_margin, height - 50, self.chart_rect.width(), 40)
        
    def _draw_background(self, painter: QPainter):
        """繪製背景"""
        # 主背景
        painter.fillRect(self.rect(), RainChartTheme.MAIN_BACKGROUND)
        
        # 圖表區域背景
        painter.fillRect(self.chart_rect, RainChartTheme.RAIN_CHART_BG)
        
    def _draw_grid(self, painter: QPainter):
        """繪製網格"""
        painter.setPen(QPen(RainChartTheme.GRID_COLOR, 1, Qt.DotLine))
        
        # 垂直網格線 (X軸)
        x_min, x_max = self.x_range
        x_step = max(1, (x_max - x_min) // 10)
        
        for x_val in range(int(x_min), int(x_max) + 1, int(x_step)):
            x_pos = self._map_x_to_pixel(x_val)
            painter.drawLine(x_pos, self.chart_rect.top(), x_pos, self.chart_rect.bottom())
            
        # 水平網格線 (左Y軸)
        y_min, y_max = self.left_y_range
        y_step = (y_max - y_min) / 8
        
        for i in range(9):
            y_val = y_min + i * y_step
            y_pos = self._map_left_y_to_pixel(y_val)
            painter.drawLine(self.chart_rect.left(), y_pos, self.chart_rect.right(), y_pos)
            
    def _draw_axes(self, painter: QPainter):
        """繪製座標軸"""
        painter.setPen(QPen(RainChartTheme.AXIS_COLOR, 2))
        
        # X軸
        painter.drawLine(self.chart_rect.bottomLeft(), self.chart_rect.bottomRight())
        
        # 左Y軸
        painter.drawLine(self.chart_rect.topLeft(), self.chart_rect.bottomLeft())
        
        # 取消右Y軸繪製
        # if self.current_chart_type in ["primary", "temperature", "humidity_wind"]:
        #     painter.drawLine(self.chart_rect.topRight(), self.chart_rect.bottomRight())
            
        # 繪製刻度標籤
        self._draw_axis_labels(painter)
        
    def _draw_axis_labels(self, painter: QPainter):
        """繪製座標軸標籤"""
        painter.setFont(self.label_font)
        painter.setPen(QPen(RainChartTheme.LABEL_COLOR))
        
        # X軸標籤 (圈數)
        x_min, x_max = self.x_range
        x_step = max(1, (x_max - x_min) // 8)
        
        for x_val in range(int(x_min), int(x_max) + 1, int(x_step)):
            x_pos = self._map_x_to_pixel(x_val)
            text_rect = QRect(x_pos - 20, self.chart_rect.bottom() + 5, 40, 20)
            painter.drawText(text_rect, Qt.AlignCenter, str(int(x_val)))
            
        # 左Y軸標籤
        y_min, y_max = self.left_y_range
        y_step = (y_max - y_min) / 6
        
        for i in range(7):
            y_val = y_min + i * y_step
            y_pos = self._map_left_y_to_pixel(y_val)
            text_rect = QRect(10, y_pos - 10, 60, 20)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{y_val:.1f}")
            
        # 繪製座標軸標題
        self._draw_axis_titles(painter)
            
        # 取消右Y軸標籤繪製
        # if self.current_chart_type in ["primary", "temperature", "humidity_wind"]:
        #     y_min, y_max = self.right_y_range
        #     y_step = (y_max - y_min) / 6
        #     
        #     for i in range(7):
        #         y_val = y_min + i * y_step
        #         y_pos = self._map_right_y_to_pixel(y_val)
        #         text_rect = QRect(self.width() - 70, y_pos - 10, 60, 20)
        #         painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{y_val:.1f}")
        
    def _draw_axis_titles(self, painter: QPainter):
        """繪製座標軸標題"""
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        painter.setPen(QPen(RainChartTheme.LABEL_COLOR))
        
        # X軸標題 (圈數)
        x_title_rect = QRect(
            self.chart_rect.center().x() - 50, 
            self.chart_rect.bottom() + 35, 
            100, 20
        )
        painter.drawText(x_title_rect, Qt.AlignCenter, "圈數")
        
        # 左Y軸標題 (溫度)
        painter.save()
        painter.translate(25, self.chart_rect.center().y())
        painter.rotate(-90)
        y_title_rect = QRect(-30, -10, 60, 20)
        painter.drawText(y_title_rect, Qt.AlignCenter, "溫度 (°C)")
        painter.restore()
                
    def _draw_data(self, painter: QPainter):
        """繪製數據"""
        if not self.chart_data or self.current_chart_type not in self.chart_data:
            return
            
        chart_info = self.chart_data[self.current_chart_type]
        
        if self.current_chart_type == "primary":
            self._draw_rainfall_temperature(painter, chart_info)
        elif self.current_chart_type == "temperature":
            self._draw_temperature_comparison(painter, chart_info)
        elif self.current_chart_type == "humidity_wind":
            self._draw_humidity_wind(painter, chart_info)
        elif self.current_chart_type == "pressure":
            self._draw_pressure(painter, chart_info)
            
    def _draw_rainfall_temperature(self, painter: QPainter, chart_info: Dict[str, Any]):
        """繪製降雨+氣溫圖表"""
        x_data = chart_info.get("x_data", [])
        rainfall_data = chart_info.get("y1_data", [])  # 降雨數據（用於背景區域）
        temp_data = chart_info.get("y2_data", [])      # 左Y軸：氣溫
        
        if not x_data or len(x_data) != len(rainfall_data) or len(x_data) != len(temp_data):
            return
            
        # 繪製降雨區域（左Y軸）- 使用連續區域而非獨立柱狀圖
        painter.setBrush(QBrush(RainChartTheme.RAIN_TRUE_COLOR))
        painter.setPen(QPen(RainChartTheme.RAINFALL_COLOR.darker(120), 1))
        
        # 找到連續降雨區間並繪製矩形區域
        i = 0
        while i < len(x_data):
            if rainfall_data[i] > 0:  # 找到降雨開始
                # 找到連續降雨的結束位置
                start_i = i
                while i < len(rainfall_data) and rainfall_data[i] > 0:
                    i += 1
                end_i = i - 1
                
                # 計算區域範圍
                start_x = self._map_x_to_pixel(x_data[start_i])
                end_x = self._map_x_to_pixel(x_data[end_i])
                
                # 降雨區域覆蓋整個圖表高度（作為背景）
                y_pos = self.chart_rect.top()
                bar_height = self.chart_rect.height()
                
                # 擴展區域寬度確保覆蓋完整的圈次範圍
                if len(x_data) > 1:
                    lap_width = (self.chart_rect.width() / (len(x_data) - 1)) / 2
                else:
                    lap_width = 5
                
                # 繪製連續降雨區域（全高度背景）
                rain_rect = QRect(int(start_x - lap_width), int(y_pos), 
                                int(end_x - start_x + 2 * lap_width), int(bar_height))
                painter.fillRect(rain_rect, RainChartTheme.RAIN_TRUE_COLOR)
            else:
                i += 1
                
        # 繪製氣溫線圖（左Y軸）
        painter.setPen(QPen(RainChartTheme.AIR_TEMP_COLOR, 3))
        
        points = []
        for x_val, temp_val in zip(x_data, temp_data):
            x_pos = self._map_x_to_pixel(x_val)
            y_pos = self._map_left_y_to_pixel(temp_val)  # 改用左Y軸
            points.append(QPoint(x_pos, y_pos))
            
        # 繪製線條
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
        # 移除數據點繪製以獲得更平滑的曲線
        # painter.setBrush(QBrush(RainChartTheme.AIR_TEMP_COLOR))
        # for point in points:
        #     painter.drawEllipse(point, 4, 4)
            
    def _draw_temperature_comparison(self, painter: QPainter, chart_info: Dict[str, Any]):
        """繪製溫度對比圖表"""
        x_data = chart_info.get("x_data", [])
        air_temp_data = chart_info.get("y1_data", [])
        track_temp_data = chart_info.get("y2_data", [])
        
        if not x_data or not air_temp_data or not track_temp_data:
            return
            
        # 繪製氣溫線
        self._draw_line_chart(painter, x_data, air_temp_data, 
                             RainChartTheme.AIR_TEMP_COLOR, "left")
                             
        # 繪製賽道溫度線
        self._draw_line_chart(painter, x_data, track_temp_data,
                             RainChartTheme.TRACK_TEMP_COLOR, "right")
                             
    def _draw_humidity_wind(self, painter: QPainter, chart_info: Dict[str, Any]):
        """繪製濕度+風速圖表"""
        x_data = chart_info.get("x_data", [])
        humidity_data = chart_info.get("y1_data", [])
        wind_data = chart_info.get("y2_data", [])
        
        if not x_data or not humidity_data or not wind_data:
            return
            
        # 繪製濕度線
        self._draw_line_chart(painter, x_data, humidity_data,
                             RainChartTheme.HUMIDITY_COLOR, "left")
                             
        # 繪製風速線  
        self._draw_line_chart(painter, x_data, wind_data,
                             RainChartTheme.WIND_SPEED_COLOR, "right")
                             
    def _draw_pressure(self, painter: QPainter, chart_info: Dict[str, Any]):
        """繪製氣壓圖表"""
        x_data = chart_info.get("x_data", [])
        pressure_data = chart_info.get("y_data", [])
        
        if not x_data or not pressure_data:
            return
            
        # 繪製氣壓線
        self._draw_line_chart(painter, x_data, pressure_data,
                             RainChartTheme.PRESSURE_COLOR, "left")
                             
    def _draw_line_chart(self, painter: QPainter, x_data: List, y_data: List, 
                        color: QColor, y_axis: str):
        """繪製線圖"""
        painter.setPen(QPen(color, 2))
        
        points = []
        for x_val, y_val in zip(x_data, y_data):
            x_pos = self._map_x_to_pixel(x_val)
            
            if y_axis == "left":
                y_pos = self._map_left_y_to_pixel(y_val)
            else:
                y_pos = self._map_right_y_to_pixel(y_val)
                
            points.append(QPoint(x_pos, y_pos))
            
        # 繪製線條
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
        # 移除數據點繪製以獲得更平滑的曲線
        # painter.setBrush(QBrush(color))
        # for point in points:
        #     painter.drawEllipse(point, 3, 3)
            
    def _draw_legend(self, painter: QPainter):
        """繪製圖例"""
        if self.current_chart_type not in self.chart_data:
            return
            
        chart_info = self.chart_data[self.current_chart_type]
        
        painter.setFont(self.label_font)
        
        legend_x = self.chart_rect.right() - 200
        legend_y = self.chart_rect.top() + 20
        
        # 根據圖表類型繪製不同的圖例
        if self.current_chart_type == "primary":
            # 降雨圖例
            painter.setBrush(QBrush(RainChartTheme.RAINFALL_COLOR))
            painter.drawRect(legend_x, legend_y, 15, 15)
            painter.drawText(legend_x + 20, legend_y + 12, "降雨")
            
            # 氣溫圖例
            painter.setPen(QPen(RainChartTheme.AIR_TEMP_COLOR, 3))
            painter.drawLine(legend_x, legend_y + 25, legend_x + 15, legend_y + 25)
            painter.drawText(legend_x + 20, legend_y + 30, "氣溫")
            
        # 可以為其他圖表類型添加更多圖例
        
    def _draw_tooltip(self, painter: QPainter):
        """繪製工具提示"""
        # 實作工具提示繪製
        pass
        
    def _map_x_to_pixel(self, x_val: float) -> int:
        """將X值映射到像素座標（支援縮放和偏移）"""
        x_min, x_max = self.x_range
        if x_max == x_min:
            return self.chart_rect.left()
            
        # 應用縮放和偏移
        ratio = (x_val - x_min) / (x_max - x_min)
        ratio = ratio * self.x_scale + self.x_offset / 100.0
        
        return int(self.chart_rect.left() + ratio * self.chart_rect.width())
        
    def _map_left_y_to_pixel(self, y_val: float) -> int:
        """將左Y值映射到像素座標（支援縮放和偏移）"""
        y_min, y_max = self.left_y_range
        if y_max == y_min:
            return self.chart_rect.bottom()
            
        # 應用縮放和偏移
        ratio = (y_val - y_min) / (y_max - y_min)
        ratio = ratio * self.y_scale + self.y_offset / 100.0
        
        return int(self.chart_rect.bottom() - ratio * self.chart_rect.height())
        
    def _map_right_y_to_pixel(self, y_val: float) -> int:
        """將右Y值映射到像素座標"""
        y_min, y_max = self.right_y_range
        if y_max == y_min:
            return self.chart_rect.bottom()
            
        ratio = (y_val - y_min) / (y_max - y_min)
        return int(self.chart_rect.bottom() - ratio * self.chart_rect.height())
        
    def switch_chart_type(self, chart_type: str):
        """切換圖表類型"""
        if chart_type in self.chart_types:
            self.current_chart_type = chart_type
            self._calculate_data_ranges()
            self.update()
            self.chart_type_switched.emit(chart_type)
    
    def wheelEvent(self, event):
        """滑鼠滾輪事件 - 智能縮放"""
        if self.chart_rect.contains(event.pos()):
            # 獲取滾輪滾動量
            delta = event.angleDelta().y()
            
            # 檢查修飾鍵
            modifiers = event.modifiers()
            
            if modifiers & Qt.ControlModifier:
                # Ctrl + 滾輪: X軸縮放
                zoom_factor = 1.2 if delta > 0 else 0.8
                self.x_scale *= zoom_factor
                self.x_scale = max(0.1, min(10.0, self.x_scale))
                
            elif modifiers & Qt.ShiftModifier:
                # Shift + 滾輪: 同步X+Y軸縮放
                zoom_factor = 1.2 if delta > 0 else 0.8
                self.x_scale *= zoom_factor
                self.y_scale *= zoom_factor
                self.x_scale = max(0.1, min(10.0, self.x_scale))
                self.y_scale = max(-10.0, min(10.0, self.y_scale))
                
            else:
                # 純滾輪: Y軸縮放
                zoom_factor = 1.3 if delta > 0 else 0.7
                self.y_scale *= zoom_factor
                self.y_scale = max(-10.0, min(10.0, self.y_scale))
                if abs(self.y_scale) < 0.1:
                    self.y_scale = 0.1 if self.y_scale >= 0 else -0.1
            
            self.update()
            event.accept()
            return
        
        super().wheelEvent(event)

    def mousePressEvent(self, event):
        """滑鼠按下事件 - 開始拖拉"""
        if event.button() == Qt.LeftButton and self.chart_rect.contains(event.pos()):
            self.dragging = True
            self.last_drag_pos = event.pos()
            event.accept()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖拉"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 拖拉圖表"""
        if self.dragging:
            # 計算拖拉偏移量
            delta_pos = event.pos() - self.last_drag_pos
            
            # 根據圖表區域大小計算相對偏移
            if self.chart_rect.width() > 0:
                x_ratio = delta_pos.x() / self.chart_rect.width()
                self.x_offset += x_ratio * 100  # 調整偏移量
                
            if self.chart_rect.height() > 0:
                y_ratio = -delta_pos.y() / self.chart_rect.height()  # 注意Y軸方向相反
                self.y_offset += y_ratio * 100  # 調整偏移量
                
            self.last_drag_pos = event.pos()
            self.update()
            event.accept()
        
        super().mouseMoveEvent(event)
            
    def update_display_options(self, option: str, value: bool):
        """更新顯示選項"""
        if option == "show_grid":
            self.show_grid = value
        elif option == "show_legend":
            self.show_legend = value
        elif option == "show_tooltips":
            self.show_tooltips = value
            
        self.update()
        
    def mousePressEvent(self, event):
        """滑鼠點擊事件 - 處理拖拉和數據點選擇"""
        if event.button() == Qt.LeftButton:
            # 檢查是否點擊在圖表區域
            if self.chart_rect.contains(event.pos()):
                # 開始拖拉
                self.dragging = True
                self.last_drag_pos = event.pos()
                
                # 找到對應的數據點
                self._handle_data_point_click(event.pos())
                
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖拉"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
        super().mouseReleaseEvent(event)
        
    def _handle_data_point_click(self, pos: QPoint):
        """處理數據點點擊"""
        # 將像素座標轉換回數據座標
        # 這裡可以實現數據點選擇和詳細信息顯示
        pass
        
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 處理拖拉和工具提示"""
        if self.dragging:
            # 計算拖拉偏移量
            delta_pos = event.pos() - self.last_drag_pos
            
            # 根據圖表區域大小計算相對偏移
            if self.chart_rect.width() > 0:
                x_ratio = delta_pos.x() / self.chart_rect.width()
                self.x_offset += x_ratio * 100  # 調整偏移量
                
            if self.chart_rect.height() > 0:
                y_ratio = -delta_pos.y() / self.chart_rect.height()  # 注意Y軸方向相反
                self.y_offset += y_ratio * 100  # 調整偏移量
                
            self.last_drag_pos = event.pos()
            self.update()
            event.accept()
            
        elif self.chart_rect.contains(event.pos()):
            # 更新工具提示
            if self.show_tooltips:
                self._update_tooltip(event.pos())
                
        super().mouseMoveEvent(event)
        
    def _update_tooltip(self, pos: QPoint):
        """更新工具提示"""
        # 實現工具提示邏輯
        pass
    
    def resizeEvent(self, event):
        """視窗大小改變事件 - 重新計算圖表區域"""
        super().resizeEvent(event)
        
        # 重新計算圖表繪製區域
        self._calculate_chart_areas()
        
        # 觸發重繪
        self.update()
