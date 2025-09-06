#!/usr/bin/env python3
"""
通用遙測圖表組件
統一的 PyQt5 原生繪圖實現，支援各種遙測數據類型
包含速度、RPM、煞車、油門、轉向等數據的距離-數值曲線圖表
支援雙車手對比和單場賽事車手分析，與系統其他組件保持一致的視覺風格
"""

import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QSplitter, QFrame, QHeaderView, QGroupBox, QGridLayout, QPushButton,
    QSizePolicy, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QFont, QPen, QColor, QPainter, QBrush, QMouseEvent, QWheelEvent

# 導入全域信號管理器
try:
    from f1t_gui_main import global_signals
except ImportError:
    global_signals = None

# 遙測數據類型配置
TELEMETRY_CONFIGS = {
    'speed': {
        'name': '速度',
        'unit': 'km/h',
        'default_min': 0,
        'default_max': 350,
        'margin_adjustment': 20,
        'color': QColor(0, 255, 0)  # 綠色
    },
    'rpm': {
        'name': 'RPM',
        'unit': '轉/分',
        'default_min': 1000,
        'default_max': 12000,
        'margin_adjustment': 500,
        'color': QColor(255, 165, 0)  # 橙色
    },
    'brake': {
        'name': '煞車',
        'unit': '%',
        'default_min': 0,
        'default_max': 100,
        'margin_adjustment': 5,
        'color': QColor(255, 0, 0)  # 紅色
    },
    'throttle': {
        'name': '油門',
        'unit': '%',
        'default_min': 0,
        'default_max': 100,
        'margin_adjustment': 5,
        'color': QColor(255, 255, 0)  # 黃色
    },
    'steering': {
        'name': '轉向',
        'unit': '°',
        'default_min': -100,
        'default_max': 100,
        'margin_adjustment': 10,
        'color': QColor(0, 255, 255)  # 青色
    },
    'gear': {
        'name': '檔位',
        'unit': '',
        'default_min': 1,
        'default_max': 8,
        'margin_adjustment': 1,
        'color': QColor(128, 0, 128)  # 紫色
    },
    'acceleration': {
        'name': '加速度',
        'unit': 'g',
        'default_min': -5,
        'default_max': 5,
        'margin_adjustment': 0.5,
        'color': QColor(255, 192, 203)  # 粉紅色
    }
}

class UniversalTelemetryChartWidget(QWidget):
    """通用遙測圖表繪製組件 - 使用 PyQt5 原生繪圖"""
    
    def __init__(self, telemetry_type: str = 'speed', parent=None):
        super().__init__(parent)
        
        # 設定遙測類型
        self.telemetry_type = telemetry_type
        self.config = TELEMETRY_CONFIGS.get(telemetry_type, TELEMETRY_CONFIGS['speed'])
        
        # 圖表設置 - 與原始模組保持完全一致
        self.margin_left = 80
        self.margin_right = 20
        self.margin_top = 20
        self.margin_bottom = 80
        
        # 數據存儲 - 使用通用變量名
        self.distance_data = []
        self.driver1_data = []  # 統一變量名，不再區分 speed/rpm
        self.driver2_data = []
        self.driver1_name = "Driver 1"
        self.driver2_name = "Driver 2"
        self.sectors = []
        
        # 數據範圍 - 根據遙測類型自動設定
        self.min_distance = 0
        self.max_distance = 6000
        self.min_value = self.config['default_min']
        self.max_value = self.config['default_max']
        
        # 視圖範圍 (用於縮放)
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_value = None
        self.view_max_value = None
        
        # 顏色設置 - 與原始模組完全一致
        self.bg_color = QColor(255, 255, 255)
        self.grid_color = QColor(200, 200, 200)
        self.axis_color = QColor(50, 50, 50)
        self.driver1_color = QColor(0, 0, 255)  # 藍色 - 車手1
        self.driver2_color = QColor(255, 0, 0)  # 紅色 - 車手2
        self.sector_color = QColor(100, 100, 100, 100)  # 半透明灰色
        
        # 滑鼠交互
        self.mouse_x = -1
        self.mouse_y = -1
        self.fixed_line_x = -1
        self.dragging = False
        self.last_drag_pos = QPoint()
        
        # 中鍵拖拉功能
        self.middle_dragging = False
        self.show_fixed_line = False
        self.fixed_distance_value = None
        
        # X軸連動功能 (獨立於同步功能)
        self.linkage_enabled = True
        self.is_sending_linkage = False
        self.linkage_distance_value = None
        self.linkage_y_relative = 0.5
        self.show_linkage_line = False
        
        # 連接X軸連動信號
        if global_signals:
            global_signals.lap_analysis_x_linkage.connect(self.on_x_linkage_received)
            global_signals.lap_analysis_x_clear.connect(self.on_x_linkage_clear)
            global_signals.lap_analysis_click_linkage.connect(self.on_click_linkage_received)
            global_signals.lap_analysis_click_clear.connect(self.on_click_linkage_clear)
        
        # 啟用鼠標追蹤
        self.setMouseTracking(True)
        
        self.setMinimumSize(600, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def set_telemetry_data(self, distance: List[float], driver1_data: List[float], 
                          driver2_data: List[float], driver1_name: str = "Driver 1", 
                          driver2_name: str = "Driver 2", sectors: List[Dict] = None):
        """設置遙測數據 - 通用接口"""
        print(f"[UNIVERSAL_CHART] 設置 {self.config['name']} 數據")
        
        # 重置視圖範圍
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_value = None
        self.view_max_value = None
        
        # 清除固定線和連動狀態
        self.show_fixed_line = False
        self.fixed_line_x = -1
        self.fixed_distance_value = None
        
        # 設置數據
        self.distance_data = distance
        self.driver1_data = driver1_data
        self.driver2_data = driver2_data
        self.driver1_name = driver1_name
        self.driver2_name = driver2_name
        self.sectors = sectors or []
        
        # 計算數據範圍
        if distance:
            self.min_distance = min(distance)
            self.max_distance = max(distance)
        
        # 根據數據自動調整數值範圍
        all_values = []
        if driver1_data:
            all_values.extend(driver1_data)
        if driver2_data:
            all_values.extend(driver2_data)
            
        if all_values:
            margin = self.config['margin_adjustment']
            self.min_value = max(self.config['default_min'], min(all_values) - margin)
            self.max_value = max(all_values) + margin
        
        print(f"[UNIVERSAL_CHART] 數據範圍: 距離 {self.min_distance}-{self.max_distance}, "
              f"{self.config['name']} {self.min_value}-{self.max_value}")
        
        # 強制重繪
        self.repaint()
    
    # 為了兼容性，提供特定類型的設置方法
    def set_speed_data(self, distance: List[float], driver1_speed: List[float], 
                      driver2_speed: List[float], driver1_name: str = "Driver 1", 
                      driver2_name: str = "Driver 2", sectors: List[Dict] = None):
        """速度數據設置接口 - 兼容性方法"""
        if self.telemetry_type != 'speed':
            print(f"[WARNING] 嘗試在 {self.telemetry_type} 圖表上設置速度數據")
        self.set_telemetry_data(distance, driver1_speed, driver2_speed, driver1_name, driver2_name, sectors)
    
    def set_rpm_data(self, distance: List[float], driver1_rpm: List[float], 
                     driver2_rpm: List[float], driver1_name: str = "Driver 1", 
                     driver2_name: str = "Driver 2", sectors: List[Dict] = None):
        """RPM數據設置接口 - 兼容性方法"""
        if self.telemetry_type != 'rpm':
            print(f"[WARNING] 嘗試在 {self.telemetry_type} 圖表上設置RPM數據")
        self.set_telemetry_data(distance, driver1_rpm, driver2_rpm, driver1_name, driver2_name, sectors)
    
    def reset_view(self):
        """重置視圖到原始範圍"""
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_value = None
        self.view_max_value = None
        self.repaint()
    
    def reset_data(self):
        """重置所有數據和視圖"""
        self.distance_data = []
        self.driver1_data = []
        self.driver2_data = []
        self.sectors = []
        self.reset_view()
        self.repaint()
    
    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 清空背景
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # 計算圖表區域
        chart_rect = QRect(
            self.margin_left,
            self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
        # 繪製背景
        painter.fillRect(chart_rect, QColor(248, 249, 250))
        
        # 繪製順序很重要 - 後繪製的會覆蓋先繪製的
        self._draw_grid(painter, chart_rect)
        self._draw_axes(painter, chart_rect)
        self._draw_sectors(painter, chart_rect)
        self._draw_telemetry_curves(painter, chart_rect)
        self._draw_mouse_tracker(painter, chart_rect)
        
        # 繪製連動線 (來自其他圖表的X軸連動)
        if self.show_linkage_line and self.linkage_distance_value is not None:
            self._draw_linkage_line(painter, chart_rect)
        
        # 繪製圖例
        self._draw_legend(painter)
    
    def _get_current_ranges(self) -> Tuple[float, float, float, float]:
        """獲取當前視圖範圍"""
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        current_min_value = self.view_min_value if self.view_min_value is not None else self.min_value
        current_max_value = self.view_max_value if self.view_max_value is not None else self.max_value
        
        return current_min_distance, current_max_distance, current_min_value, current_max_value
    
    def _draw_grid(self, painter: QPainter, chart_rect: QRect):
        """繪製網格"""
        painter.setPen(QPen(self.grid_color, 1))
        
        current_min_distance, current_max_distance, current_min_value, current_max_value = self._get_current_ranges()
        
        # 垂直網格線 (距離)
        distance_range = current_max_distance - current_min_distance
        if distance_range > 0:
            for i in range(11):
                distance = current_min_distance + (distance_range * i / 10)
                x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
        
        # 水平網格線 (數值)
        value_range = current_max_value - current_min_value
        if value_range > 0:
            for i in range(11):
                value = current_min_value + (value_range * i / 10)
                y = chart_rect.bottom() - (value - current_min_value) / value_range * chart_rect.height()
                painter.drawLine(chart_rect.left(), int(y), chart_rect.right(), int(y))
    
    def _draw_axes(self, painter: QPainter, chart_rect: QRect):
        """繪製坐標軸和標籤"""
        painter.setPen(QPen(self.axis_color, 2))
        
        # 繪製軸線
        painter.drawLine(chart_rect.left(), chart_rect.bottom(), chart_rect.right(), chart_rect.bottom())  # X軸
        painter.drawLine(chart_rect.left(), chart_rect.top(), chart_rect.left(), chart_rect.bottom())      # Y軸
        
        # 設置字體
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(QPen(self.axis_color, 1))
        
        current_min_distance, current_max_distance, current_min_value, current_max_value = self._get_current_ranges()
        
        # X軸標籤 (距離)
        distance_range = current_max_distance - current_min_distance
        if distance_range > 0:
            for i in range(0, 11, 2):  # 只顯示偶數刻度
                distance = current_min_distance + (distance_range * i / 10)
                x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                
                # 繪製刻度線
                painter.drawLine(int(x), chart_rect.bottom(), int(x), chart_rect.bottom() + 5)
                
                # 繪製標籤
                painter.drawText(int(x - 20), chart_rect.bottom() + 20, 40, 20, 
                               Qt.AlignCenter, f"{distance:.0f}")
        
        # Y軸標籤 (數值)
        value_range = current_max_value - current_min_value
        if value_range > 0:
            for i in range(0, 11, 2):  # 只顯示偶數刻度
                value = current_min_value + (value_range * i / 10)
                y = chart_rect.bottom() - (value - current_min_value) / value_range * chart_rect.height()
                
                # 繪製刻度線
                painter.drawLine(chart_rect.left() - 5, int(y), chart_rect.left(), int(y))
                
                # 繪製標籤
                painter.drawText(10, int(y - 10), self.margin_left - 20, 20, 
                               Qt.AlignRight | Qt.AlignVCenter, f"{value:.0f}")
        
        # 座標軸標題
        title_font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(title_font)
        
        # X軸標題
        painter.drawText(chart_rect.left(), self.height() - 30, chart_rect.width(), 20,
                        Qt.AlignCenter, "距離 (米)")
        
        # Y軸標題 (旋轉文字)
        painter.save()
        painter.translate(20, chart_rect.center().y())
        painter.rotate(-90)
        y_title = f"{self.config['name']} ({self.config['unit']})" if self.config['unit'] else self.config['name']
        painter.drawText(-50, -10, 100, 20, Qt.AlignCenter, y_title)
        painter.restore()
    
    def _draw_sectors(self, painter: QPainter, chart_rect: QRect):
        """繪製分段標記"""
        if not self.sectors:
            return
            
        # 使用一致的分段線設定
        sector_pen_color = QColor(120, 120, 120, 200)
        painter.setPen(QPen(sector_pen_color, 2, Qt.DashLine))
        
        current_min_distance, current_max_distance, _, _ = self._get_current_ranges()
        
        distance_range = current_max_distance - current_min_distance
        if distance_range <= 0:
            return
            
        for sector in self.sectors:
            if 'end_distance' in sector:
                end_distance = sector['end_distance']
                x = chart_rect.left() + (end_distance - current_min_distance) / distance_range * chart_rect.width()
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
                
                # 繪製S1, S2, S3標籤
                if 'sector' in sector:
                    painter.setPen(QPen(self.sector_color, 1))
                    painter.setFont(QFont("Arial", 8))
                    label_y = chart_rect.bottom() + 50
                    painter.drawText(int(x - 10), label_y, 20, 15,
                                   Qt.AlignCenter, f"S{sector['sector']}")
                    
                    # 恢復虛線樣式
                    painter.setPen(QPen(sector_pen_color, 2, Qt.DashLine))
    
    def _draw_telemetry_curves(self, painter: QPainter, chart_rect: QRect):
        """繪製遙測曲線"""
        if not self.distance_data:
            return
        
        current_min_distance, current_max_distance, current_min_value, current_max_value = self._get_current_ranges()
            
        distance_range = current_max_distance - current_min_distance
        value_range = current_max_value - current_min_value
        
        if distance_range <= 0 or value_range <= 0:
            return
        
        # 繪製車手1曲線
        if self.driver1_data and len(self.driver1_data) == len(self.distance_data):
            painter.setPen(QPen(self.driver1_color, 2))
            points = []
            
            for distance, value in zip(self.distance_data, self.driver1_data):
                if current_min_distance <= distance <= current_max_distance:
                    x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                    y = chart_rect.bottom() - (value - current_min_value) / value_range * chart_rect.height()
                    points.append(QPoint(int(x), int(y)))
            
            # 繪製連線
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        
        # 繪製車手2曲線
        if self.driver2_data and len(self.driver2_data) == len(self.distance_data):
            painter.setPen(QPen(self.driver2_color, 2))
            points = []
            
            for distance, value in zip(self.distance_data, self.driver2_data):
                if current_min_distance <= distance <= current_max_distance:
                    x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                    y = chart_rect.bottom() - (value - current_min_value) / value_range * chart_rect.height()
                    points.append(QPoint(int(x), int(y)))
            
            # 繪製連線
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
    
    def _draw_mouse_tracker(self, painter: QPainter, chart_rect: QRect):
        """繪製滑鼠追蹤線和固定線"""
        # 繪製固定垂直線
        if self.show_fixed_line and self.fixed_distance_value is not None:
            current_min_distance, current_max_distance, _, _ = self._get_current_ranges()
            distance_range = current_max_distance - current_min_distance
            
            if distance_range > 0 and current_min_distance <= self.fixed_distance_value <= current_max_distance:
                relative_pos = (self.fixed_distance_value - current_min_distance) / distance_range
                fixed_x = chart_rect.left() + relative_pos * chart_rect.width()
                self._draw_tracking_line(painter, chart_rect, int(fixed_x), is_fixed=True)
        
        # 繪製滑鼠跟隨線
        if chart_rect.contains(self.mouse_x, self.mouse_y):
            self._draw_tracking_line(painter, chart_rect, self.mouse_x, is_fixed=False)
    
    def _draw_tracking_line(self, painter: QPainter, chart_rect: QRect, x_pos: int, is_fixed: bool):
        """繪製追蹤線和數值顯示 - 修復：完整實現數據標籤顯示"""
        if not chart_rect.contains(x_pos, chart_rect.center().y()):
            return
            
        # 設置線條樣式
        if is_fixed:
            painter.setPen(QPen(QColor(200, 0, 0), 2, Qt.SolidLine))
        else:
            painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
            
        painter.drawLine(x_pos, chart_rect.top(), x_pos, chart_rect.bottom())
        
        # 修復：添加數值顯示邏輯（與RPM舊模組一致）
        if self.distance_data:
            current_min_distance, current_max_distance, current_min_value, current_max_value = self._get_current_ranges()
            distance_range = current_max_distance - current_min_distance
            value_range = current_max_value - current_min_value
            
            if distance_range > 0 and value_range > 0:
                # 計算當前距離和數值
                distance = current_min_distance + (x_pos - chart_rect.left()) / chart_rect.width() * distance_range
                
                # 尋找最接近的數據點並顯示車手數值
                closest_drivers = self._find_closest_values(distance)
                
                if closest_drivers:
                    # 根據車手數量動態調整標籤高度
                    base_height = 30  # 距離資訊的基本高度
                    driver_height = 15 * len(closest_drivers)  # 每個車手15像素高度
                    label_height = base_height + driver_height
                    label_width = 150
                    
                    # 計算標籤位置
                    if is_fixed:
                        # 固定線標籤位置（在頂部）
                        label_x = min(x_pos + 10, self.width() - label_width - 10)
                        label_y = max(chart_rect.top() + 10, 10)
                        # 固定線使用淺紅色背景
                        bg_color = QColor(255, 240, 240, 230)
                    else:
                        # 滑鼠追蹤標籤位置（跟隨滑鼠）
                        label_x = x_pos + 10
                        label_y = self.mouse_y - 60
                        
                        # 確保標籤不會超出邊界
                        if label_x + label_width > self.width():
                            label_x = x_pos - label_width - 10
                        if label_y < 10:
                            label_y = self.mouse_y + 10
                        # 滑鼠追蹤使用白色背景
                        bg_color = QColor(255, 255, 255, 230)
                    
                    # 繪製標籤背景
                    painter.setPen(QPen(self.axis_color, 1))
                    painter.fillRect(label_x, label_y, label_width, label_height, bg_color)
                    painter.drawRect(label_x, label_y, label_width, label_height)
                    
                    # 顯示數值文字
                    painter.setFont(QFont("Arial", 9))
                    painter.setPen(QPen(self.axis_color, 1))
                    
                    text_y = label_y + 15
                    painter.drawText(label_x + 5, text_y, f"距離: {distance:.0f}m")
                    
                    # 顯示車手數值
                    for i, (driver_name, value, color) in enumerate(closest_drivers):
                        painter.setPen(QPen(color, 1))
                        unit = self.config.get('unit', '')
                        painter.drawText(label_x + 5, text_y + 15 + (i * 15), 
                                       f"{driver_name}: {value:.0f} {unit}")
    
    def _find_closest_values(self, target_distance):
        """尋找最接近指定距離的數值 - 修復：新增此方法"""
        if not self.distance_data:
            return []
            
        # 找到最接近的距離索引
        closest_idx = 0
        min_diff = float('inf')
        for i, dist in enumerate(self.distance_data):
            diff = abs(dist - target_distance)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
        
        drivers_to_show = []
        
        # 檢查是否為單車手模式
        is_single_driver = (self.driver1_name == self.driver2_name or 
                           not self.driver2_name or 
                           not self.driver2_data)
        
        # 車手1
        if closest_idx < len(self.driver1_data):
            value = self.driver1_data[closest_idx]
            drivers_to_show.append((self.driver1_name, value, self.driver1_color))
        
        # 只有在非單車手模式且第二個車手數據不同時才添加第二個車手
        if (not is_single_driver and 
            closest_idx < len(self.driver2_data) and
            self.driver2_name and 
            self.driver2_name != self.driver1_name):
            value = self.driver2_data[closest_idx]
            drivers_to_show.append((self.driver2_name, value, self.driver2_color))
            
        return drivers_to_show
    
    def _draw_linkage_line(self, painter: QPainter, chart_rect: QRect):
        """繪製連動線"""
        if self.linkage_distance_value is None:
            return
            
        current_min_distance, current_max_distance, current_min_value, current_max_value = self._get_current_ranges()
        distance_range = current_max_distance - current_min_distance
        
        if distance_range <= 0:
            return
            
        if current_min_distance <= self.linkage_distance_value <= current_max_distance:
            relative_pos = (self.linkage_distance_value - current_min_distance) / distance_range
            x_pos = chart_rect.left() + relative_pos * chart_rect.width()
            
            # 計算Y位置
            y_pos = chart_rect.top() + self.linkage_y_relative * chart_rect.height()
            
            # 繪製連動線 - 綠色虛線
            painter.setPen(QPen(QColor(0, 255, 0), 2, Qt.DashDotLine))
            painter.drawLine(int(x_pos), chart_rect.top(), int(x_pos), chart_rect.bottom())
    
    def _draw_legend(self, painter: QPainter):
        """繪製圖例 - 修復：添加單車手模式檢測"""
        if not self.driver1_data and not self.driver2_data:
            return
            
        legend_x = self.width() - 200  # 修復：與舊模組一致的位置
        legend_y = 30
        
        painter.setFont(QFont("Arial", 9))
        
        # 修復：檢查是否為單車手模式（與RPM舊模組邏輯一致）
        is_single_driver = (self.driver1_name == self.driver2_name or 
                           not self.driver2_name or 
                           not self.driver2_data)
        
        # 車手1圖例
        if self.driver1_data:
            painter.setPen(QPen(self.driver1_color, 2))
            painter.drawLine(legend_x, legend_y, legend_x + 20, legend_y)
            painter.setPen(QPen(self.axis_color, 1))  # 修復：使用axis_color而非黑色
            painter.drawText(legend_x + 25, legend_y - 5, 100, 20, Qt.AlignLeft | Qt.AlignVCenter, self.driver1_name)
        
        # 修復：只有在非單車手模式且車手名稱不同時才顯示車手2圖例
        if not is_single_driver and self.driver2_name != self.driver1_name and self.driver2_data:
            painter.setPen(QPen(self.driver2_color, 2))
            painter.drawLine(legend_x, legend_y + 20, legend_x + 20, legend_y + 20)
            painter.setPen(QPen(self.axis_color, 1))
            painter.drawText(legend_x + 25, legend_y + 15, 100, 20, Qt.AlignLeft | Qt.AlignVCenter, self.driver2_name)
    
    # 連動功能實現
    def on_x_linkage_received(self, distance_value: float, y_relative: float):
        """接收X軸連動信號"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
            
        self.linkage_distance_value = distance_value
        self.linkage_y_relative = y_relative
        self.show_linkage_line = True
        self.update()
    
    def on_x_linkage_clear(self):
        """清除X軸連動"""
        self.show_linkage_line = False
        self.linkage_distance_value = None
        self.update()
    
    def on_click_linkage_received(self, distance_value: float):
        """接收點擊連動信號"""
        if not self.linkage_enabled:
            return
            
        # 設置固定線到連動位置
        self.fixed_distance_value = distance_value
        self.show_fixed_line = True
        self.update()
    
    def on_click_linkage_clear(self):
        """清除點擊連動"""
        self.show_fixed_line = False
        self.fixed_distance_value = None
        self.update()
    
    # 滑鼠事件處理 (簡化版本，可根據需要擴展)
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        self.update()
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        """滑鼠點擊事件 - 修復：與舊模組一致的交互方式"""
        if event.button() == Qt.LeftButton:
            # 修復：直接左鍵點擊固定垂直線（與舊模組一致）
            chart_rect = QRect(self.margin_left, self.margin_top,
                             self.width() - self.margin_left - self.margin_right,
                             self.height() - self.margin_top - self.margin_bottom)
            
            if chart_rect.contains(event.pos()):
                # 計算並保存實際的距離值
                current_min_distance, current_max_distance, _, _ = self._get_current_ranges()
                distance_range = current_max_distance - current_min_distance
                
                if distance_range > 0:
                    relative_x = event.x() - chart_rect.left()
                    self.fixed_distance_value = current_min_distance + (relative_x / chart_rect.width()) * distance_range
                    self.show_fixed_line = True
                    
                    # 修復：添加連動信號發送（與舊模組一致）
                    try:
                        from f1t_gui_main import global_signals
                        if global_signals and hasattr(self, 'linkage_enabled') and self.linkage_enabled:
                            if not hasattr(self, 'is_sending_linkage'):
                                self.is_sending_linkage = False
                            
                            if not self.is_sending_linkage:
                                self.is_sending_linkage = True
                                global_signals.lap_analysis_click_linkage.emit(self.fixed_distance_value)
                                self.is_sending_linkage = False
                    except (ImportError, AttributeError):
                        pass
                    
                    self.update()
                    
        elif event.button() == Qt.RightButton:
            # 右鍵點擊：清除固定線
            self.show_fixed_line = False
            self.fixed_distance_value = None
            
            # 修復：添加點擊清除連動信號（與舊模組一致）
            try:
                from f1t_gui_main import global_signals
                if global_signals and hasattr(self, 'linkage_enabled') and self.linkage_enabled:
                    if not hasattr(self, 'is_sending_linkage'):
                        self.is_sending_linkage = False
                        
                    if not self.is_sending_linkage:
                        self.is_sending_linkage = True
                        global_signals.lap_analysis_click_clear.emit()
                        self.is_sending_linkage = False
            except (ImportError, AttributeError):
                pass
                
            self.update()
        
        super().mousePressEvent(event)
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.mouse_x = -1
        self.mouse_y = -1
        self.update()
        super().leaveEvent(event)


# 兼容性別名，保持向下兼容
SpeedChartWidget = lambda parent=None: UniversalTelemetryChartWidget('speed', parent)
RPMChartWidget = lambda parent=None: UniversalTelemetryChartWidget('rpm', parent)

# 為其他遙測類型提供便捷構造函數
BrakeChartWidget = lambda parent=None: UniversalTelemetryChartWidget('brake', parent)
ThrottleChartWidget = lambda parent=None: UniversalTelemetryChartWidget('throttle', parent)
SteeringChartWidget = lambda parent=None: UniversalTelemetryChartWidget('steering', parent)
GearChartWidget = lambda parent=None: UniversalTelemetryChartWidget('gear', parent)
AccelerationChartWidget = lambda parent=None: UniversalTelemetryChartWidget('acceleration', parent)


# 擴展通用遙測圖表組件的功能
def update_telemetry_data(self, data):
    """更新遙測數據 - 與RPM舊模組保持一致的完整檢測邏輯"""
    try:
        print(f"[UNIVERSAL_CHART] ========== 更新{self.config['name']}數據 ==========")
        print(f"[UNIVERSAL_CHART] 收到數據鍵: {list(data.keys()) if data else 'None'}")
        
        if not data:
            print(f"[ERROR] [UNIVERSAL_CHART] 數據為空")
            return
        
        # 提取元數據
        metadata = data.get('metadata', {})
        telemetry_data = data.get(f'{self.telemetry_type}_data', {})
        statistics = data.get('statistics', {})
        
        print(f"[UNIVERSAL_CHART] metadata 鍵: {list(metadata.keys()) if metadata else 'None'}")
        print(f"[UNIVERSAL_CHART] {self.telemetry_type}_data 鍵: {list(telemetry_data.keys()) if telemetry_data else 'None'}")
        
        # 提取車手信息
        drivers = metadata.get('drivers', [])
        sectors = metadata.get('sectors', [])
        
        print(f"[UNIVERSAL_CHART] 車手數量: {len(drivers)}")
        print(f"[UNIVERSAL_CHART] 賽道區段: {len(sectors)}")
        
        # 提取遙測數據
        distance = telemetry_data.get('distance', [])
        driver1_data = telemetry_data.get(f'driver1_{self.telemetry_type}', [])
        driver2_data = telemetry_data.get(f'driver2_{self.telemetry_type}', [])
        driver1_name = telemetry_data.get('driver1_name', 'Driver 1')
        driver2_name = telemetry_data.get('driver2_name', 'Driver 2')
        
        print(f"[UNIVERSAL_CHART] 距離數據點: {len(distance)}")
        print(f"[UNIVERSAL_CHART] 車手1 數據點: {len(driver1_data)}")
        print(f"[UNIVERSAL_CHART] 車手2 數據點: {len(driver2_data)}")
        
        # 如果有車手信息，使用車手代碼作為名稱
        if len(drivers) >= 2:
            driver1_name = drivers[0].get('code', driver1_name)
            driver2_name = drivers[1].get('code', driver2_name)
            print(f"[UNIVERSAL_CHART] 車手名稱更新: {driver1_name} vs {driver2_name}")
        elif len(drivers) == 1:
            driver1_name = drivers[0].get('code', driver1_name)
            print(f"[UNIVERSAL_CHART] 單車手模式: {driver1_name}")
        
        # 檢測是否為單車手模式或相同車手比較 - 與RPM舊模組完全一致
        is_single_driver_mode = False
        if metadata.get('is_single_driver', False):
            # 明確標記的單車手模式
            is_single_driver_mode = True
            print(f"[UNIVERSAL_CHART] 🔍 檢測到單車手模式標記")
        elif driver1_name == driver2_name:
            # 相同車手比較（如 VER vs VER）
            is_single_driver_mode = True
            print(f"[UNIVERSAL_CHART] 🔍 檢測到相同車手比較: {driver1_name} vs {driver2_name}")
        elif len(drivers) == 1:
            # 只有一個車手的數據
            is_single_driver_mode = True
            print(f"[UNIVERSAL_CHART] 🔍 檢測到單車手數據: {driver1_name}")
        
        if is_single_driver_mode:
            print(f"[UNIVERSAL_CHART] 🎯 使用單車手模式顯示")
            # 清空車手2的數據，只顯示車手1
            driver2_data = []
            driver2_name = ""
        
        # 檢查數據完整性
        if not distance or not driver1_data:
            print(f"[ERROR] [UNIVERSAL_CHART] 關鍵數據缺失")
            print(f"[UNIVERSAL_CHART] distance: {len(distance) if distance else 0} 點")
            print(f"[UNIVERSAL_CHART] driver1_data: {len(driver1_data) if driver1_data else 0} 點")
            return
        
        # 更新圖表
        print(f"[UNIVERSAL_CHART] 📊 更新圖表...")
        self.set_telemetry_data(
            distance=distance,
            driver1_data=driver1_data,
            driver2_data=driver2_data,
            driver1_name=driver1_name,
            driver2_name=driver2_name,
            sectors=sectors
        )
        print(f"[UNIVERSAL_CHART] ✅ 圖表更新完成")
        
    except Exception as e:
        print(f"[ERROR] [UNIVERSAL_CHART] 更新數據失敗: {e}")
        import traceback
        traceback.print_exc()


def update_rpm_data(self, data):
    """RPM數據更新接口 - 兼容性方法"""
    if self.telemetry_type == 'rpm':
        return self.update_telemetry_data(data)
    else:
        print(f"[WARNING] 嘗試在 {self.telemetry_type} 圖表上更新RPM數據")


def update_speed_data(self, data):
    """速度數據更新接口 - 兼容性方法"""
    if self.telemetry_type == 'speed':
        return self.update_telemetry_data(data)
    else:
        print(f"[WARNING] 嘗試在 {self.telemetry_type} 圖表上更新速度數據")


def update_lap_parameters(self, year: str, race: str, session: str, 
                         driver1: str = None, driver2: str = None,
                         lap1: int = 1, lap2: int = 1, is_fastest: bool = False):
    """更新圈速參數並重新載入數據 - 與RPM/速度分析模組保持一致"""
    try:
        print(f"[UNIVERSAL_CHART] 🔄 更新圈速參數: {year} {race} {session}")
        print(f"[UNIVERSAL_CHART] 🏁 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
        
        # 檢查是否有對應的數據載入器
        loader_attr = f'{self.telemetry_type}_loader'
        if hasattr(self, loader_attr):
            loader = getattr(self, loader_attr)
            print(f"[UNIVERSAL_CHART] 📦 找到{self.config['name']}數據載入器，準備重新載入...")
            
            session_info = {
                'year': int(year) if year.isdigit() else year,
                'race': race,
                'session': session,
                'driver1': driver1 or 'VER',
                'driver2': driver2 or 'VER',
                'lap1': lap1,
                'lap2': lap2,
                'is_fastest_lap': is_fastest
            }
            
            # 根據遙測類型調用對應的載入方法
            if self.telemetry_type == 'speed':
                loader.load_speed_analysis_data(session_info)
            elif self.telemetry_type == 'rpm':
                loader.load_rpm_analysis_data(session_info)
            else:
                print(f"[WARNING] 未支援的遙測類型: {self.telemetry_type}")
                return False
                
            print(f"[UNIVERSAL_CHART] ✅ 數據重新載入請求已發送")
            return True
        else:
            print(f"[UNIVERSAL_CHART] ⚠️ 未找到{self.config['name']}數據載入器，僅更新顯示")
            return True
            
    except Exception as e:
        print(f"[ERROR] [UNIVERSAL_CHART] 更新圈速參數失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


# 添加方法到UniversalTelemetryChartWidget類
UniversalTelemetryChartWidget.update_telemetry_data = update_telemetry_data
UniversalTelemetryChartWidget.update_rpm_data = update_rpm_data
UniversalTelemetryChartWidget.update_speed_data = update_speed_data
UniversalTelemetryChartWidget.update_lap_parameters = update_lap_parameters
