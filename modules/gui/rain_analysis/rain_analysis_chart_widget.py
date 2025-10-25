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
import logging
from core.logger import get_logger
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QFontMetrics, QMouseEvent

# 導入 GUI 國際化模組
from core.gui_i18n import tr

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


# 使用集中式 logger (f1.gui.rain_chart)
logger = get_logger("rain_chart", component="gui")


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
        
        # 🆕 使用基類的統一座標軸標題配置（使用翻譯）
        self.set_axis_titles(tr("lap_number_rain", "Lap Number"), tr("temperature_celsius", "Temperature (°C)"))
        # 🎯 X軸標題置中顯示，Y軸標題在中間垂直顯示
        self.set_axis_title_positions("bottom-center", "left-center")
        
        # 🔍 除錯：確認座標軸標題設定
        print(f"[RAIN_AXIS_DEBUG] 座標軸標題設定:")
        print(f"  X軸標題: '{self.x_axis_title}'")
        print(f"  Y軸標題: '{self.y_axis_title}'") 
        print(f"  X軸位置: {self.x_title_position}")
        print(f"  Y軸位置: {self.y_title_position}")
        print(f"  顯示標題: {self.show_axis_titles}")
        
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
        
        # 圖表邊距 (優化間距配置)
        self.margin_left = 65   # 左邊距 (Y軸標籤) - 增加空間避免數值貼近曲線
        self.margin_bottom = 70 # 下邊距 (X軸標籤+標題) - 增加空間避免標題貼近刻度
        self.margin_top = 20    # 上邊距 - 保持20px給圖例
        self.margin_right = 20  # 右邊距 - 保持20px給雙Y軸設計
        
        # 滑鼠位置追蹤（用於同步）
        self.mouse_x = -1
        self.mouse_y = -1
        
        # 參照遙測分析：視圖範圍控制
        self.view_min_lap = None
        self.view_max_lap = None
        self.view_min_rain = None
        self.view_max_rain = None
        self.view_min_temp = None
        self.view_max_temp = None
        
        # 參照遙測分析：數據範圍
        self.min_lap = 0
        self.max_lap = 100
        self.min_rain = 0
        self.max_rain = 100
        self.min_temp = 0
        self.max_temp = 50
        
        # 參照遙測分析：拖拉狀態
        self.middle_dragging = False
        self.show_fixed_line = False
        self.fixed_lap_value = None
        
        # 工具提示
        self.tooltip_visible = False
        self.tooltip_data = {}
        self.tooltip_pos = QPoint()
        
        # 設定樣式
        self.setup_rain_chart_style()
        
    def setup_rain_chart_style(self):
        """設定下雨分析圖表樣式"""
        # 設定極小最小尺寸，提高視窗靈活性
        self.setMinimumSize(200, 100)  # 調整為200x100，提供更高的佈局靈活性
        # 參照遙測分析：設置擴展策略
        from PyQt5.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
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
        if logger.isEnabledFor(logging.DEBUG):
            keys = list(data.keys()) if isinstance(data, dict) else "Not a dict"
            logger.debug("update_data called type=%s keys=%s", type(data), keys)
        self.update_chart_data(data)
        
    def set_data(self, *args, **kwargs):
        """設置圖表數據（兼容基類接口）"""
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "set_data invoked type=%s args=%d kwargs=%s",
                type(self),
                len(args),
                list(kwargs.keys()),
            )
        
        # 如果只有一個參數且是字典，使用我們的方法
        if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("set_data forwarding single dict argument to update_chart_data")
            self.update_chart_data(args[0])
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("set_data detected multi-argument usage; delegating to super")
            # 嘗試調用父類方法
            try:
                super().set_data(*args, **kwargs)
            except Exception as e:
                logger.warning("set_data fallback due to error: %s", e)
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
                self.min_lap = min(x_data)
                self.max_lap = max(x_data)
                
        # 左Y軸範圍（現在用於溫度顯示，使用y2_data）
        if "y2_data" in chart_info:
            temp_data = chart_info["y2_data"]  # 溫度數據
            if temp_data:
                min_val = min(temp_data)
                max_val = max(temp_data)
                margin = (max_val - min_val) * 0.15 if max_val > min_val else 1  # 增加邊距到15%
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
        try:
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
            
            # 參照遙測分析：繪製固定線
            if self.show_fixed_line and self.fixed_lap_value is not None:
                self._draw_fixed_line(painter)
            
            # 繪製圖例
            if self.show_legend:
                self._draw_legend(painter)
                
            # 繪製工具提示
            if self.tooltip_visible:
                self._draw_tooltip(painter)
                
            # 🆕 繪製基類的統一座標軸標題
            if self.show_axis_titles:
                print(f"[RAIN_AXIS_DEBUG] 🎨 自訂座標軸標題繪製")
                self._draw_custom_axis_titles(painter)
            else:
                print(f"[RAIN_AXIS_DEBUG] ❌ 座標軸標題被停用 (show_axis_titles={self.show_axis_titles})")
        finally:
            # 🔑 關鍵修復：確保 painter 總是被正確結束
            painter.end()
            
    def _calculate_chart_areas(self):
        """計算圖表區域（與遙測分析一致）"""
        width = self.width()
        height = self.height()
        
        # 主圖表區域 - 使用標準邊距
        self.chart_rect = QRect(
            self.margin_left,
            self.margin_top,
            width - self.margin_left - self.margin_right,
            height - self.margin_top - self.margin_bottom
        )
        
        # 確保最小尺寸 - 適應極小視窗
        if self.chart_rect.width() < 50:  # 降低最小寬度要求
            self.chart_rect.setWidth(50)
        if self.chart_rect.height() < 30:  # 降低最小高度要求
            self.chart_rect.setHeight(30)
        
        # 座標軸區域
        self.left_y_axis_rect = QRect(10, self.margin_top, 70, self.chart_rect.height())
        self.right_y_axis_rect = QRect(width - 70, self.margin_top, 60, self.chart_rect.height())
        self.x_axis_rect = QRect(self.margin_left, height - 50, self.chart_rect.width(), 40)
        
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
        
        # 左Y軸 - 向右偏移避免與數值標籤重疊
        y_axis_x = self.chart_rect.left()  # 原本的Y軸位置
        painter.drawLine(y_axis_x, self.chart_rect.top(), y_axis_x, self.chart_rect.bottom())
        
        # 取消右Y軸繪製
        # if self.current_chart_type in ["primary", "temperature", "humidity_wind"]:
        #     painter.drawLine(self.chart_rect.topRight(), self.chart_rect.bottomRight())
            
        # 繪製刻度標籤
        self._draw_axis_labels(painter)
        
    def _draw_axis_labels(self, painter: QPainter):
        """繪製座標軸標籤（使用視圖範圍）"""
        painter.setFont(self.label_font)
        painter.setPen(QPen(RainChartTheme.LABEL_COLOR))
        
        # X軸標籤 (圈數) - 使用視圖範圍
        if self.view_min_lap is not None and self.view_max_lap is not None:
            x_min, x_max = self.view_min_lap, self.view_max_lap
        else:
            x_min, x_max = self.x_range

        chart_info = self.chart_data.get(self.current_chart_type, {}) if isinstance(self.chart_data, dict) else {}
        raw_x_values = []
        if isinstance(chart_info, dict):
            raw_x_values = chart_info.get("x_data", []) or []

        if raw_x_values:
            # 轉換為整數圈數並保持順序
            unique_x_values = []
            seen = set()
            for value in raw_x_values:
                lap_value = int(round(value))
                if lap_value not in seen:
                    unique_x_values.append((value, lap_value))
                    seen.add(lap_value)
            unique_x_values.sort(key=lambda item: item[0])
        else:
            # 回退：根據範圍生成等距圈數
            unique_x_values = []
            if x_max > x_min:
                step = max(1, int((x_max - x_min) / 20))
                for lap in range(int(math.floor(x_min)), int(math.ceil(x_max)) + 1, step):
                    unique_x_values.append((lap, int(lap)))

        metrics = QFontMetrics(self.label_font)
        min_spacing_px = max(48, metrics.horizontalAdvance("000") + 12)

        print(f"[RAIN_AXIS_DEBUG] 📊 X軸座標軸設置:")
        print(f"[RAIN_AXIS_DEBUG]   範圍: {x_min:.1f} - {x_max:.1f}")
        print(f"[RAIN_AXIS_DEBUG]   資料點: {len(unique_x_values)}")
        print(f"[RAIN_AXIS_DEBUG]   最小間距(px): {min_spacing_px}")

        drawn_positions: List[int] = []
        total_labels = len(unique_x_values)

        for index, (raw_value, display_value) in enumerate(unique_x_values):
            x_pos = self._map_x_to_pixel(raw_value)

            should_draw = index == 0 or index == total_labels - 1
            if not should_draw:
                should_draw = all(abs(x_pos - prev_pos) >= min_spacing_px for prev_pos in drawn_positions)

            if not should_draw:
                continue

            label_text = str(display_value)
            text_width = metrics.horizontalAdvance(label_text)
            text_rect = QRect(
                int(x_pos - text_width / 2) - 2,
                self.chart_rect.bottom() + 5,
                text_width + 4,
                20
            )
            painter.drawText(text_rect, Qt.AlignCenter, label_text)
            drawn_positions.append(x_pos)
        
        # 確保至少顯示起點與終點標籤
        if unique_x_values and len(drawn_positions) == 1:
            raw_value, display_value = unique_x_values[-1]
            x_pos = self._map_x_to_pixel(raw_value)
            if all(abs(x_pos - prev_pos) >= min_spacing_px for prev_pos in drawn_positions):
                label_text = str(display_value)
                text_width = metrics.horizontalAdvance(label_text)
                text_rect = QRect(
                    int(x_pos - text_width / 2) - 2,
                    self.chart_rect.bottom() + 5,
                    text_width + 4,
                    20
                )
                painter.drawText(text_rect, Qt.AlignCenter, label_text)
                drawn_positions.append(x_pos)
            
        # 左Y軸標籤 (溫度) - 使用視圖範圍
        if self.view_min_temp is not None and self.view_max_temp is not None:
            y_min, y_max = self.view_min_temp, self.view_max_temp
        else:
            y_min, y_max = self.left_y_range
        y_step = (y_max - y_min) / 6
        
        print(f"[RAIN_AXIS_DEBUG] 📊 Y軸座標軸設置:")
        print(f"[RAIN_AXIS_DEBUG]   範圍: {y_min:.3f} - {y_max:.3f}")
        print(f"[RAIN_AXIS_DEBUG]   間距: {y_step:.3f}")
        print(f"[RAIN_AXIS_DEBUG]   標籤數量: 7")
        
        for i in range(7):
            y_val = y_min + i * y_step
            y_pos = self._map_left_y_to_pixel(y_val)
            # 數值標籤位置：確保完全在Y軸線左側，留出足夠間距
            y_axis_x = self.chart_rect.left()  # Y軸線位置 (X=70)
            # 標籤區域：X=5 到 X=60，給Y軸線留出10px間距
            text_rect = QRect(5, y_pos - 10, 55, 20)  # 寬度固定55px，右邊界在X=60
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{y_val:.1f}")
            
        # 🆕 座標軸標題現在由基類統一處理
            
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
        
    # � 座標軸標題繪製方法已移除，現在由基類統一處理

    def _draw_custom_axis_titles(self, painter: QPainter):
        """繪製經過間距調整的座標軸標題"""
        painter.setFont(self.theme.AXIS_TITLE_FONT)
        painter.setPen(QPen(RainChartTheme.TEXT_COLOR))

        # X軸標題置中並與刻度保留距離
        if self.x_axis_title:
            title_width = max(120, self.theme.AXIS_TITLE_FONT.pointSize() * 10)
            x_title_rect = QRect(
                int(self.chart_rect.center().x() - title_width / 2),
                self.chart_rect.bottom() + 28,
                int(title_width),
                20
            )
            painter.drawText(x_title_rect, Qt.AlignCenter, self.x_axis_title)

        # Y軸標題保持垂直顯示
        if self.y_axis_title:
            painter.save()
            painter.translate(self.chart_rect.left() - 40, self.chart_rect.center().y())
            painter.rotate(-90)
            y_title_rect = QRect(-60, -10, 120, 20)
            painter.drawText(y_title_rect, Qt.AlignCenter, self.y_axis_title)
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
            
            # 邊界檢查：確保點在圖表區域內
            x_pos = max(self.chart_rect.left(), min(self.chart_rect.right(), x_pos))
            y_pos = max(self.chart_rect.top(), min(self.chart_rect.bottom(), y_pos))
            
            points.append(QPoint(x_pos, y_pos))
            
        # 繪製線條（只繪製在視圖範圍內的點）
        painter.setClipRect(self.chart_rect)  # 設置裁剪區域
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
        painter.setClipping(False)  # 取消裁剪
            
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
        """繪製線圖（包含邊界保護）"""
        painter.setPen(QPen(color, 2))
        
        points = []
        for x_val, y_val in zip(x_data, y_data):
            x_pos = self._map_x_to_pixel(x_val)
            
            if y_axis == "left":
                y_pos = self._map_left_y_to_pixel(y_val)
            else:
                y_pos = self._map_right_y_to_pixel(y_val)
                
            # 邊界檢查：確保點在圖表區域內
            x_pos = max(self.chart_rect.left(), min(self.chart_rect.right(), x_pos))
            y_pos = max(self.chart_rect.top(), min(self.chart_rect.bottom(), y_pos))
                
            points.append(QPoint(x_pos, y_pos))
            
        # 繪製線條（使用裁剪區域）
        painter.setClipRect(self.chart_rect)  # 設置裁剪區域
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
        painter.setClipping(False)  # 取消裁剪
            
        # 移除數據點繪製以獲得更平滑的曲線
        # painter.setBrush(QBrush(color))
        # for point in points:
        #     painter.drawEllipse(point, 3, 3)
            
    def _draw_fixed_line(self, painter: QPainter):
        """參照遙測分析：繪製固定垂直線"""
        if self.fixed_lap_value is None:
            return
            
        # 計算固定線的X座標
        current_min_lap = self.view_min_lap if self.view_min_lap is not None else self.min_lap
        current_max_lap = self.view_max_lap if self.view_max_lap is not None else self.max_lap
        lap_range = current_max_lap - current_min_lap
        
        if lap_range <= 0:
            return
            
        # 計算固定線位置
        relative_pos = (self.fixed_lap_value - current_min_lap) / lap_range
        line_x = self.chart_rect.left() + relative_pos * self.chart_rect.width()
        
        # 檢查是否在圖表範圍內
        if not (self.chart_rect.left() <= line_x <= self.chart_rect.right()):
            return
            
        # 繪製固定垂直線
        painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.DashLine))  # 紅色虛線
        painter.drawLine(int(line_x), self.chart_rect.top(), 
                        int(line_x), self.chart_rect.bottom())
        
        # 繪製圈數標籤
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setFont(QFont("Arial", 9))
        label = f"Lap {self.fixed_lap_value:.1f}"
        label_rect = QRect(int(line_x) - 25, self.chart_rect.bottom() + 5, 50, 20)
        painter.drawText(label_rect, Qt.AlignCenter, label)
    
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
            painter.drawText(legend_x + 20, legend_y + 12, "Rainfall")
            
            # 氣溫圖例
            painter.setPen(QPen(RainChartTheme.AIR_TEMP_COLOR, 3))
            painter.drawLine(legend_x, legend_y + 25, legend_x + 15, legend_y + 25)
            painter.drawText(legend_x + 20, legend_y + 30, "Air Temp")
            
        # 可以為其他圖表類型添加更多圖例
        
    def _draw_tooltip(self, painter: QPainter):
        """繪製工具提示"""
        # 實作工具提示繪製
        pass
        
    def _map_x_to_pixel(self, x_val: float) -> int:
        """將X值映射到像素座標（支援視圖範圍縮放）"""
        # 使用視圖範圍或原始範圍
        if self.view_min_lap is not None and self.view_max_lap is not None:
            x_min, x_max = self.view_min_lap, self.view_max_lap
        else:
            x_min, x_max = self.x_range
            
        if x_max == x_min:
            return self.chart_rect.left()
            
        # 映射到像素座標
        ratio = (x_val - x_min) / (x_max - x_min)
        return int(self.chart_rect.left() + ratio * self.chart_rect.width())
        
    def _map_left_y_to_pixel(self, y_val: float) -> int:
        """將左Y值映射到像素座標（支援視圖範圍縮放）"""
        # 使用視圖範圍或原始範圍
        if self.view_min_temp is not None and self.view_max_temp is not None:
            y_min, y_max = self.view_min_temp, self.view_max_temp
        else:
            y_min, y_max = self.left_y_range
            
        if y_max == y_min:
            return self.chart_rect.bottom()
            
        # 映射到像素座標
        ratio = (y_val - y_min) / (y_max - y_min)
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
        """滑鼠滾輪事件 - 雙Y軸降雨分析專用縮放邏輯"""
        print(f"[RAIN_WHEEL_DEBUG] ========== 滾輪事件開始 ==========")
        print(f"[RAIN_WHEEL_DEBUG] 事件位置: {event.pos()}")
        print(f"[RAIN_WHEEL_DEBUG] 滾輪角度: {event.angleDelta()}")
        
        # 獲取滾輪方向
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 1.0 / 1.1
        print(f"[RAIN_WHEEL_DEBUG] 滾輪方向: {delta}, 縮放因子: {zoom_factor}")
        
        # 獲取滑鼠在圖表中的相對位置
        chart_rect = QRect(
            self.margin_left, self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
        print(f"[RAIN_WHEEL_DEBUG] 圖表區域: {chart_rect}")
        print(f"[RAIN_WHEEL_DEBUG] 滑鼠在圖表區域內: {chart_rect.contains(event.pos())}")
        
        # 輸出當前數據範圍以供調試
        print(f"[RAIN_WHEEL_DEBUG] 📊 當前數據範圍:")
        print(f"[RAIN_WHEEL_DEBUG]    圈數: {self.min_lap:.3f} - {self.max_lap:.3f}")
        print(f"[RAIN_WHEEL_DEBUG]    左Y軸範圍: {self.left_y_range}")
        print(f"[RAIN_WHEEL_DEBUG]    右Y軸範圍: {self.right_y_range}")
        print(f"[RAIN_WHEEL_DEBUG]    當前圖表類型: {self.current_chart_type}")
        
        if chart_rect.contains(event.pos()):
            # 計算滑鼠位置對應的數據值
            mouse_rel_x = (event.x() - chart_rect.left()) / chart_rect.width()
            mouse_rel_y = (chart_rect.bottom() - event.y()) / chart_rect.height()
            print(f"[RAIN_WHEEL_DEBUG] 滑鼠相對位置: x={mouse_rel_x:.3f}, y={mouse_rel_y:.3f}")
            
            # 初始化視圖範圍（X軸 - 圈數）
            if self.view_min_lap is None:
                self.view_min_lap = self.min_lap
                self.view_max_lap = self.max_lap
                print(f"[RAIN_WHEEL_DEBUG] 初始化X軸(圈數)視圖範圍: {self.view_min_lap} - {self.view_max_lap}")
            
            # 初始化左Y軸視圖範圍（根據圖表類型）
            left_y_min, left_y_max = self.left_y_range
            if self.view_min_temp is None:
                self.view_min_temp = left_y_min
                self.view_max_temp = left_y_max
                print(f"[RAIN_WHEEL_DEBUG] 初始化左Y軸(溫度)視圖範圍: {self.view_min_temp} - {self.view_max_temp}")
            
            # 計算當前滑鼠對應的數據值
            lap_range = self.view_max_lap - self.view_min_lap
            temp_range = self.view_max_temp - self.view_min_temp
            print(f"[RAIN_WHEEL_DEBUG] 當前範圍 - X軸(圈數): {lap_range:.3f}, 左Y軸(溫度): {temp_range:.3f}")
            
            mouse_lap = self.view_min_lap + mouse_rel_x * lap_range
            mouse_temp = self.view_min_temp + mouse_rel_y * temp_range
            print(f"[RAIN_WHEEL_DEBUG] 滑鼠數據位置 - 圈數: {mouse_lap:.3f}, 溫度: {mouse_temp:.3f}")
            
            # 計算新的範圍，並添加最小範圍檢查
            original_lap_range = self.max_lap - self.min_lap
            original_temp_range = left_y_max - left_y_min
            
            new_lap_range = lap_range / zoom_factor
            new_temp_range = temp_range / zoom_factor
            
            # 設定最小縮放範圍限制（防止過度縮放）
            min_lap_range = original_lap_range * 0.01  # 最小為原始範圍的1%
            min_temp_range = original_temp_range * 0.01  # 最小為原始範圍的1%
            
            # 設定最大縮放範圍限制（防止過度縮小）
            max_lap_range = original_lap_range * 2.0   # 最大為原始範圍的2倍
            max_temp_range = original_temp_range * 2.0  # 最大為原始範圍的2倍
            
            new_lap_range = max(min_lap_range, min(max_lap_range, new_lap_range))
            new_temp_range = max(min_temp_range, min(max_temp_range, new_temp_range))
            
            print(f"[RAIN_WHEEL_DEBUG] 範圍限制 - 圈數: {min_lap_range:.3f} ~ {max_lap_range:.3f}")
            print(f"[RAIN_WHEEL_DEBUG] 範圍限制 - 溫度: {min_temp_range:.3f} ~ {max_temp_range:.3f}")
            print(f"[RAIN_WHEEL_DEBUG] 調整後範圍 - 圈數: {new_lap_range:.3f}, 溫度: {new_temp_range:.3f}")
            
            # 更新視圖範圍，保持滑鼠位置不變
            new_min_lap = mouse_lap - new_lap_range * mouse_rel_x
            new_max_lap = mouse_lap + new_lap_range * (1 - mouse_rel_x)
            new_min_temp = mouse_temp - new_temp_range * mouse_rel_y
            new_max_temp = mouse_temp + new_temp_range * (1 - mouse_rel_y)
            
            print(f"[RAIN_WHEEL_DEBUG] 初步計算 - 圈數: {new_min_lap:.3f} ~ {new_max_lap:.3f}")
            print(f"[RAIN_WHEEL_DEBUG] 初步計算 - 溫度: {new_min_temp:.3f} ~ {new_max_temp:.3f}")
            
            # 確保圈數範圍不超出原始數據範圍
            if new_min_lap < self.min_lap:
                offset = self.min_lap - new_min_lap
                new_min_lap = self.min_lap
                new_max_lap = min(self.max_lap, new_max_lap + offset)
                print(f"[RAIN_WHEEL_DEBUG] 圈數左邊界修正: offset={offset:.3f}")
            elif new_max_lap > self.max_lap:
                offset = new_max_lap - self.max_lap
                new_max_lap = self.max_lap
                new_min_lap = max(self.min_lap, new_min_lap - offset)
                print(f"[RAIN_WHEEL_DEBUG] 圈數右邊界修正: offset={offset:.3f}")
            
            # 確保溫度範圍不超出原始數據範圍
            if new_min_temp < left_y_min:
                offset = left_y_min - new_min_temp
                new_min_temp = left_y_min
                new_max_temp = min(left_y_max, new_max_temp + offset)
                print(f"[RAIN_WHEEL_DEBUG] 溫度下邊界修正: offset={offset:.3f}")
            elif new_max_temp > left_y_max:
                offset = new_max_temp - left_y_max
                new_max_temp = left_y_max
                new_min_temp = max(left_y_min, new_min_temp - offset)
                print(f"[RAIN_WHEEL_DEBUG] 溫度上邊界修正: offset={offset:.3f}")
            
            # 最終安全檢查：確保範圍有效
            if new_max_lap <= new_min_lap:
                print(f"[RAIN_WHEEL_DEBUG] ⚠️ 圈數範圍無效，恢復原始範圍")
                new_min_lap = self.view_min_lap
                new_max_lap = self.view_max_lap
            if new_max_temp <= new_min_temp:
                print(f"[RAIN_WHEEL_DEBUG] ⚠️ 溫度範圍無效，恢復原始範圍")
                new_min_temp = self.view_min_temp
                new_max_temp = self.view_max_temp
            
            # 應用新的視圖範圍
            self.view_min_lap = new_min_lap
            self.view_max_lap = new_max_lap
            self.view_min_temp = new_min_temp
            self.view_max_temp = new_max_temp
            
            print(f"[RAIN_WHEEL_DEBUG] ✅ 最終視圖範圍 - 圈數: {self.view_min_lap:.3f} - {self.view_max_lap:.3f}")
            print(f"[RAIN_WHEEL_DEBUG] ✅ 最終視圖範圍 - 溫度: {self.view_min_temp:.3f} - {self.view_max_temp:.3f}")
            print(f"[RAIN_WHEEL_DEBUG] 🎨 觸發重繪")
            
            self.update()
        else:
            print(f"[RAIN_WHEEL_DEBUG] ❌ 滑鼠不在圖表區域內，忽略縮放")
            
        print(f"[RAIN_WHEEL_DEBUG] ========== 滾輪事件結束 ==========")
        
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        # 清除滑鼠追蹤狀態，與其他分析模組保持一致
        if hasattr(self, 'mouse_x'):
            self.mouse_x = None
        if hasattr(self, 'mouse_y'):
            self.mouse_y = None
        self.update()

    def reset_zoom(self):
        """重置縮放到原始範圍"""
        print(f"[RAIN_WHEEL_DEBUG] 🔄 重置縮放到原始範圍")
        self.view_min_lap = None
        self.view_max_lap = None
        self.view_min_temp = None
        self.view_max_temp = None
        self.update()
        print(f"[RAIN_WHEEL_DEBUG] ✅ 縮放已重置")

    def mousePressEvent(self, event: QMouseEvent):
        """參照遙測分析：滑鼠按下事件"""
        print(f"[RAIN_MOUSE_DEBUG] ========== 滑鼠按下事件 ==========")
        print(f"[RAIN_MOUSE_DEBUG] 按鍵: {event.button()}")
        print(f"[RAIN_MOUSE_DEBUG] 位置: {event.pos()}")
        
        if event.button() == Qt.LeftButton:
            # 左鍵點擊：固定垂直線（如遙測分析）
            print(f"[RAIN_MOUSE_DEBUG] 🔴 左鍵點擊 - 顯示固定垂直線")
            chart_rect = QRect(
                self.margin_left, self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom
            )
            print(f"[RAIN_MOUSE_DEBUG] 圖表區域: {chart_rect}")
            
            if chart_rect.contains(event.pos()):
                # 計算並保存實際的圈數值
                current_min_lap = self.view_min_lap if self.view_min_lap is not None else self.min_lap
                current_max_lap = self.view_max_lap if self.view_max_lap is not None else self.max_lap
                lap_range = current_max_lap - current_min_lap
                
                if lap_range > 0:
                    relative_x = event.x() - chart_rect.left()
                    self.fixed_lap_value = current_min_lap + (relative_x / chart_rect.width()) * lap_range
                    self.show_fixed_line = True
                    
                    self.update()
            
        elif event.button() == Qt.RightButton:
            # 右鍵點擊：清除固定線並重置縮放（參照遙測分析並增強）
            print(f"[RAIN_MOUSE_DEBUG] 🔴 右鍵點擊 - 清除固定線並重置縮放")
            self.show_fixed_line = False
            self.fixed_lap_value = None
            self.reset_zoom()  # 添加重置縮放功能
            
        elif event.button() == Qt.MiddleButton:
            # 中鍵按下：開始拖拉（如遙測分析）
            print(f"[RAIN_MOUSE_DEBUG] 🟡 中鍵按下 - 開始拖拉模式")
            self.middle_dragging = True
            self.last_drag_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            print(f"[RAIN_MOUSE_DEBUG] 拖拉起始位置: {self.last_drag_pos}")
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """參照遙測分析：滑鼠釋放事件"""
        print(f"[RAIN_MOUSE_DEBUG] ========== 滑鼠釋放事件 ==========")
        print(f"[RAIN_MOUSE_DEBUG] 按鍵: {event.button()}")
        
        if event.button() == Qt.MiddleButton:
            # 中鍵釋放：結束拖拉
            print(f"[RAIN_MOUSE_DEBUG] 🟡 中鍵釋放 - 結束拖拉模式")
            self.middle_dragging = False
            self.setCursor(Qt.ArrowCursor)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """參照遙測分析：滑鼠移動事件"""
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        
        # 中鍵拖拉處理
        if self.middle_dragging and not self.last_drag_pos.isNull():
            print(f"[RAIN_DRAG_DEBUG] ========== 拖拉移動事件 ==========")
            # 計算移動距離
            dx = event.x() - self.last_drag_pos.x()
            dy = event.y() - self.last_drag_pos.y()
            print(f"[RAIN_DRAG_DEBUG] 移動距離: dx={dx}, dy={dy}")
            
            # 轉換為數據範圍的移動
            chart_rect = QRect(
                self.margin_left, self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom
            )
            
            print(f"[RAIN_DRAG_DEBUG] 圖表區域: {chart_rect}")
            
            if chart_rect.width() > 0 and chart_rect.height() > 0:
                # X軸移動（圈數）
                lap_range = (self.view_max_lap or self.max_lap) - (self.view_min_lap or self.min_lap)
                lap_move = -dx * lap_range / chart_rect.width()
                print(f"[RAIN_DRAG_DEBUG] X軸移動 - 範圍: {lap_range:.3f}, 移動量: {lap_move:.3f}")
                
                # Y軸移動（雨量/溫度）
                rain_range = (self.view_max_rain or self.max_rain) - (self.view_min_rain or self.min_rain)
                rain_move = dy * rain_range / chart_rect.height()  # Y軸是倒置的
                print(f"[RAIN_DRAG_DEBUG] Y軸移動 - 範圍: {rain_range:.3f}, 移動量: {rain_move:.3f}")
                
                # 更新視圖範圍
                if self.view_min_lap is None:
                    self.view_min_lap = self.min_lap
                    self.view_max_lap = self.max_lap
                    print(f"[RAIN_DRAG_DEBUG] 初始化圈數視圖: {self.view_min_lap} - {self.view_max_lap}")
                if self.view_min_rain is None:
                    self.view_min_rain = self.min_rain
                    self.view_max_rain = self.max_rain
                    print(f"[RAIN_DRAG_DEBUG] 初始化雨量視圖: {self.view_min_rain:.3f} - {self.view_max_rain:.3f}")
                
                print(f"[RAIN_DRAG_DEBUG] 拖拉前 - 圈數: {self.view_min_lap:.3f} - {self.view_max_lap:.3f}")
                print(f"[RAIN_DRAG_DEBUG] 拖拉前 - 雨量: {self.view_min_rain:.3f} - {self.view_max_rain:.3f}")
                
                self.view_min_lap += lap_move
                self.view_max_lap += lap_move
                self.view_min_rain += rain_move
                self.view_max_rain += rain_move
                
                print(f"[RAIN_DRAG_DEBUG] ✅ 拖拉後 - 圈數: {self.view_min_lap:.3f} - {self.view_max_lap:.3f}")
                print(f"[RAIN_DRAG_DEBUG] ✅ 拖拉後 - 雨量: {self.view_min_rain:.3f} - {self.view_max_rain:.3f}")
            else:
                print(f"[RAIN_DRAG_DEBUG] ❌ 圖表區域無效，跳過拖拉")
            
            self.last_drag_pos = event.pos()
            print(f"[RAIN_DRAG_DEBUG] 更新拖拉位置: {self.last_drag_pos}")
            print(f"[RAIN_DRAG_DEBUG] 🎨 觸發重繪")
            
            self.update()
        else:
            # 非拖拉狀態的滑鼠移動（可用於懸停效果）
            pass
    
    def leaveEvent(self, event):
        """滑鼠離開事件 - 參照遙測分析模組"""
        self.mouse_x = -1
        self.mouse_y = -1
        # TODO: 如需要連動功能，在此處添加連動清除信號
        # if linkage_manager and self._is_linkage_fully_enabled():
        #     linkage_manager.send_x_linkage_clear(self)
        self.update()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """參照遙測分析：滑鼠雙擊事件 - 清除固定線"""
        if event.button() == Qt.LeftButton:
            self.show_fixed_line = False
            self.fixed_lap_value = None
            self.update()
            
    def update_display_options(self, option: str, value: bool):
        """更新顯示選項"""
        if option == "show_grid":
            self.show_grid = value
        elif option == "show_legend":
            self.show_legend = value
        elif option == "show_tooltips":
            self.show_tooltips = value
            
        self.update()
        
    def _handle_data_point_click(self, pos: QPoint):
        """處理數據點點擊"""
        # 將像素座標轉換回數據座標
        # 這裡可以實現數據點選擇和詳細信息顯示
        pass
        
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
        
    def get_chart_area(self) -> QRect:
        """獲取圖表區域（與遙測分析一致的方法名稱）"""
        return self.chart_rect
    
    def leaveEvent(self, event):
        """滑鼠離開事件 - 隱藏動態游標線"""
        self.mouse_x = -1
        self.mouse_y = -1
        self.update()
        super().leaveEvent(event)
    
    def resizeEvent(self, event):
        """參照遙測分析：視窗大小調整時重新計算佈局"""
        super().resizeEvent(event)
        # 重新計算圖表區域和佈局
        self.update_chart_layout()
        
    def update_chart_layout(self):
        """參照遙測分析：更新圖表佈局以適應新尺寸"""
        try:
            # 重新計算圖表區域
            if hasattr(self, 'chart_rect'):
                # 根據當前尺寸重新計算圖表區域
                margin = 60
                self.chart_rect = QRect(
                    margin, 
                    margin, 
                    self.width() - 2 * margin, 
                    self.height() - 2 * margin
                )
                
            # 觸發重繪
            self.update()
            
        except Exception as e:
            print(f"[RAIN_CHART] 佈局更新失敗: {e}")
    
    def clear_fixed_line(self):
        """清除固定垂直線"""
        self.show_fixed_line = False
        self.fixed_lap_value = None
        self.update()
    
    def reset_view(self):
        """參照遙測分析：重置視圖到原始範圍"""
        self.view_min_lap = None
        self.view_max_lap = None
        self.view_min_rain = None
        self.view_max_rain = None
        self.view_min_temp = None
        self.view_max_temp = None
        
        # 清除固定線
        self.show_fixed_line = False
        self.fixed_lap_value = None
        
        self.update()
        
    def get_current_lap_range(self) -> Tuple[float, float]:
        """獲取當前顯示的圈數範圍"""
        min_lap = self.view_min_lap if self.view_min_lap is not None else self.min_lap
        max_lap = self.view_max_lap if self.view_max_lap is not None else self.max_lap
        return min_lap, max_lap
