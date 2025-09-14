#!/usr/bin/env python3
"""
driverLapAnalysisChartWidget - F1T 詳細圈速分析圖表組件 (修正版)
================================================================

基於正確邏輯的詳細圈速分析實現：
- 正確的圖表繪製架構
- 專用的圖表繪製區域
- 統一的 PyQt5 原生繪圖
- 智能標記系統
- 車手選擇和多車手比較

Author: F1T Team
Date: 2025-09-13
Version: 3.1.0 (修正圖表繪製邏輯)
"""

import sys
import math
import traceback
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QComboBox, QCheckBox, QGroupBox, QGridLayout, QScrollArea,
                            QFrame, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QFontMetrics


class ChartTheme:
    """圖表主題配置"""
    DRIVER1_COLOR = QColor(220, 53, 69)    # 紅色
    DRIVER2_COLOR = QColor(0, 123, 255)    # 藍色
    DRIVER3_COLOR = QColor(40, 167, 69)    # 綠色
    DRIVER4_COLOR = QColor(255, 193, 7)    # 黃色
    DRIVER5_COLOR = QColor(108, 117, 125)  # 灰色
    
    BACKGROUND = QColor(255, 255, 255)
    GRID_COLOR = QColor(200, 200, 200)
    TEXT_COLOR = QColor(0, 0, 0)


class ChartDataPoint:
    """圖表數據點"""
    def __init__(self, x, y, metadata=None):
        self.x = x
        self.y = y
        self.metadata = metadata or {}


class ChartSeries:
    """圖表數據系列"""
    def __init__(self, name, data, color, line_width=2, style='line'):
        self.name = name
        self.data = data
        self.color = color
        self.line_width = line_width
        self.style = style


class LaptimeChartWidget(QWidget):
    """專用的圈速圖表繪製組件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.series_list = []
        self.setMinimumSize(800, 600)
        # 移除固定的白色背景，讓paint事件處理背景色
        self.setStyleSheet("border: 1px solid #ccc;")
        
        # 標記顏色配置
        self.marker_colors = {
            'P': QColor(255, 193, 7),    # 黃色 - 進站
            'F': QColor(40, 167, 69),    # 綠色 - 最快圈
            'T': QColor(138, 43, 226),   # 紫羅蘭色 - 輪胎更換
            'A': QColor(220, 53, 69),    # 紅色 - 事故/危險
            'S': QColor(75, 85, 95),     # 深灰色 - 特殊圈 (替代突兀的藍色)
            'R': QColor(30, 144, 255),   # 天藍色 - 降雨 (待實現)
        }
        
        print("[LAPTIME_CHART_WIDGET] 專用圖表組件初始化完成")
    
    def update_series_data(self, series_list: List[ChartSeries]):
        """更新圖表數據系列"""
        self.series_list = series_list
        print(f"[LAPTIME_CHART_WIDGET] 更新數據系列，系列數: {len(series_list)}")
        for series in series_list:
            print(f"[LAPTIME_CHART_WIDGET]   - {series.name}: {len(series.data)} 數據點")
        self.update()  # 觸發重繪
    
    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        try:
            # 清除背景
            painter.fillRect(self.rect(), ChartTheme.BACKGROUND)
            
            if not self.series_list:
                # 顯示無數據提示
                painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
                painter.setFont(QFont("Arial", 12))
                painter.drawText(self.rect(), Qt.AlignCenter, "請選擇車手以顯示圈速數據")
                return
            
            # 計算繪製區域（留出邊距）
            margin = 60
            chart_rect = QRect(
                margin, 
                margin, 
                self.width() - 2 * margin, 
                self.height() - 2 * margin
            )
            
            # 計算數據範圍
            x_min, x_max, y_min, y_max = self._calculate_data_range()
            
            if x_min >= x_max or y_min >= y_max:
                painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
                painter.setFont(QFont("Arial", 12))
                painter.drawText(self.rect(), Qt.AlignCenter, "數據範圍無效")
                return
            
            # 繪製網格和軸
            self._draw_grid_and_axes(painter, chart_rect, (x_min, x_max), (y_min, y_max))
            
            # 繪製數據線
            self._draw_data_lines(painter, chart_rect, (x_min, x_max), (y_min, y_max))
            
            # 繪製智能標記
            self._draw_smart_markers(painter, chart_rect, (x_min, x_max), (y_min, y_max))
            
            # 繪製圖例
            self._draw_legend(painter)
            
        except Exception as e:
            print(f"[LAPTIME_CHART_WIDGET] 繪製錯誤: {e}")
            traceback.print_exc()
            
            # 顯示錯誤信息
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, f"繪製錯誤: {str(e)}")
    
    def _calculate_data_range(self):
        """計算數據範圍"""
        x_values = []
        y_values = []
        
        for series in self.series_list:
            for point in series.data:
                x_values.append(point.x)
                y_values.append(point.y)
        
        if not x_values or not y_values:
            return 0, 1, 0, 1
        
        x_min, x_max = min(x_values), max(x_values)
        y_min, y_max = min(y_values), max(y_values)
        
        # 添加5%邊距
        x_margin = max((x_max - x_min) * 0.05, 1)
        y_margin = max((y_max - y_min) * 0.05, 0.1)
        
        return x_min - x_margin, x_max + x_margin, y_min - y_margin, y_max + y_margin
    
    def _draw_grid_and_axes(self, painter: QPainter, rect: QRect, x_range: Tuple[float, float], y_range: Tuple[float, float]):
        """繪製網格和軸"""
        painter.setPen(QPen(ChartTheme.GRID_COLOR, 1))
        
        # 垂直網格線（圈數）
        for i in range(6):
            x = rect.left() + i * rect.width() / 5
            painter.drawLine(int(x), rect.top(), int(x), rect.bottom())
            
            # X軸標籤
            if i < 5:
                lap = x_range[0] + i * (x_range[1] - x_range[0]) / 5
                painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
                painter.setFont(QFont("Arial", 9))
                painter.drawText(int(x) - 15, rect.bottom() + 20, f"Lap {int(lap)}")
                painter.setPen(QPen(ChartTheme.GRID_COLOR, 1))
        
        # 水平網格線（圈速）
        for i in range(6):
            y = rect.top() + i * rect.height() / 5
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
            
            # Y軸標籤
            if i < 5:
                laptime = y_range[1] - i * (y_range[1] - y_range[0]) / 5
                painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
                painter.setFont(QFont("Arial", 9))
                painter.drawText(rect.left() - 50, int(y) + 5, f"{laptime:.1f}s")
                painter.setPen(QPen(ChartTheme.GRID_COLOR, 1))
        
        # 繪製軸標題
        painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        
        # X軸標題
        painter.drawText(rect.center().x() - 30, rect.bottom() + 45, "圈數 (Lap)")
        
        # Y軸標題（旋轉）
        painter.save()
        painter.translate(rect.left() - 40, rect.center().y())
        painter.rotate(-90)
        painter.drawText(-30, 0, "圈速 (秒)")
        painter.restore()
    
    def _draw_data_lines(self, painter: QPainter, rect: QRect, x_range: Tuple[float, float], y_range: Tuple[float, float]):
        """繪製數據線"""
        for series in self.series_list:
            if not series.data:
                continue
            
            painter.setPen(QPen(series.color, series.line_width))
            
            prev_point = None
            for data_point in series.data:
                # 座標轉換
                screen_x = rect.left() + (data_point.x - x_range[0]) * rect.width() / (x_range[1] - x_range[0])
                screen_y = rect.bottom() - (data_point.y - y_range[0]) * rect.height() / (y_range[1] - y_range[0])
                
                current_point = QPoint(int(screen_x), int(screen_y))
                
                # 繪製數據點
                painter.drawEllipse(current_point, 3, 3)
                
                # 繪製連接線
                if prev_point:
                    painter.drawLine(prev_point, current_point)
                
                prev_point = current_point
    
    def _draw_smart_markers(self, painter: QPainter, rect: QRect, x_range: Tuple[float, float], y_range: Tuple[float, float]):
        """繪製智能標記"""
        marker_count = 0
        for series in self.series_list:
            for data_point in series.data:
                markers = data_point.metadata.get('markers', [])
                
                if not markers:
                    continue
                
                marker_count += len(markers)
                
                # 座標轉換
                screen_x = rect.left() + (data_point.x - x_range[0]) * rect.width() / (x_range[1] - x_range[0])
                screen_y = rect.bottom() - (data_point.y - y_range[0]) * rect.height() / (y_range[1] - y_range[0])
                
                position = QPoint(int(screen_x), int(screen_y))
                
                # 繪製標記
                for i, marker_type in enumerate(markers):
                    color = self.marker_colors.get(marker_type, QColor(128, 128, 128))
                    offset_y = position.y() - 20 - i * 12  # 增加偏移距離避免重疊
                    self._draw_marker(painter, QPoint(position.x(), offset_y), marker_type, color)
        
        # 調試信息
        if marker_count > 0:
            print(f"[LAPTIME_CHART_WIDGET] 繪製了 {marker_count} 個智能標記")
        else:
            print(f"[LAPTIME_CHART_WIDGET] ⚠️ 沒有找到智能標記數據")
    
    def _draw_marker(self, painter: QPainter, position: QPoint, marker_type: str, color: QColor):
        """繪製單個標記 - 增強版本"""
        # 使用更粗的邊框和更大的尺寸
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(QBrush(color))
        
        if marker_type == 'P':  # 進站 - 正方形 (更大)
            painter.drawRect(position.x() - 6, position.y() - 6, 12, 12)
            # 添加文字標籤
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(position.x() - 3, position.y() + 2, "P")
            
        elif marker_type == 'A':  # 事故 - 三角形 (更大)
            points = [
                QPoint(position.x(), position.y() - 8),
                QPoint(position.x() - 6, position.y() + 4),
                QPoint(position.x() + 6, position.y() + 4)
            ]
            painter.drawPolygon(points)
            # 添加文字標籤
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(position.x() - 3, position.y() + 1, "A")
            
        elif marker_type == 'F':  # 最快圈 - 星形 (更大)
            self._draw_star(painter, position, 8)
            # 添加文字標籤
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(position.x() - 3, position.y() + 2, "F")
            
        elif marker_type == 'T':  # 輪胎更換 - 菱形 (新增)
            points = [
                QPoint(position.x(), position.y() - 6),
                QPoint(position.x() + 6, position.y()),
                QPoint(position.x(), position.y() + 6),
                QPoint(position.x() - 6, position.y())
            ]
            painter.drawPolygon(points)
            # 添加文字標籤
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(position.x() - 3, position.y() + 2, "T")
            
        elif marker_type == 'A':  # 事故/危險 - 三角形 (修正)
            points = [
                QPoint(position.x(), position.y() - 8),
                QPoint(position.x() - 6, position.y() + 4),
                QPoint(position.x() + 6, position.y() + 4)
            ]
            painter.drawPolygon(points)
            # 添加文字標籤
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(position.x() - 3, position.y() + 1, "A")
            
        elif marker_type == 'S':  # 特殊圈 - 圓形 (修正)
            painter.drawEllipse(position.x() - 6, position.y() - 6, 12, 12)
            # 添加文字標籤
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(position.x() - 3, position.y() + 2, "S")
            
        elif marker_type == 'R':  # 降雨 - 圓形 (待實現)
            painter.drawEllipse(position.x() - 6, position.y() - 6, 12, 12)
            # 添加文字標籤
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(position.x() - 3, position.y() + 2, "R")
            
        else:  # 未知類型 - 圓形
            painter.drawEllipse(position.x() - 5, position.y() - 5, 10, 10)
    
    def _draw_star(self, painter: QPainter, center: QPoint, radius: int):
        """繪製星形標記"""
        points = []
        for i in range(10):
            angle = i * math.pi / 5
            if i % 2 == 0:
                # 外部點
                x = center.x() + radius * math.cos(angle - math.pi / 2)
                y = center.y() + radius * math.sin(angle - math.pi / 2)
            else:
                # 內部點
                x = center.x() + radius * 0.4 * math.cos(angle - math.pi / 2)
                y = center.y() + radius * 0.4 * math.sin(angle - math.pi / 2)
            
            points.append(QPoint(int(x), int(y)))
        
        painter.drawPolygon(points)
    
    def _draw_legend(self, painter: QPainter):
        """繪製圖例 - 包含車手和智能標記說明"""
        if not self.series_list:
            return
        
        # 🎯 動態計算圖例位置和尺寸
        # 先計算所需寬度
        max_driver_width = 54 + 20  # 方塊 + 間距 + 車手名 + 邊距
        max_marker_width = 110 + 20  # 標記 + 間距 + 文字 + 邊距
        required_width = max(max_driver_width, max_marker_width)
        
        # 確保圖例不超出右邊界
        widget_width = self.width()
        safe_width = min(required_width, widget_width - 30)  # 保留30像素右邊距
        legend_x = widget_width - safe_width - 10  # 從右邊算起
        legend_y = 20
        
        painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
        painter.setFont(QFont("Arial", 9))
        
        # 計算圖例總高度
        driver_lines = len(self.series_list)
        marker_lines = 5  # P, F, T, A, S
        total_lines = driver_lines + marker_lines + 2  # +2 for spacing and headers
        legend_height = total_lines * 20 + 30  # 增加行距
        
        # 🎯 調試：圖例背景顏色 - 使用強制白色背景
        # 🔍 詳細調試：Widget和圖例信息
        widget_width = self.width()
        widget_height = self.height()
        actual_legend_x = legend_x - 10
        actual_legend_y = legend_y - 10
        
        # 圖例背景: 使用淡灰色替代藍色突兀問題
        background_color = QColor(248, 248, 248, 255)  # 淡灰色，完全不透明
        border_color = QColor(100, 100, 100)  # 深灰色邊框
        
        # 🔍 詳細尺寸分析
        legend_width = 175  # 當前設定寬度
        
        # 計算實際需要的寬度
        # 1. 車手名稱區域: 方塊(16) + 間距(8) + 最長車手名(約30) = 54
        # 2. 標記區域: 標記(16) + 間距(14) + 文字("T - 輪胎更換"約80) = 110
        # 3. 邊距: 左右各10 = 20
        max_driver_width = 54 + 20  # 74
        max_marker_width = 110 + 20  # 130
        calculated_width = max(max_driver_width, max_marker_width)  # 130
        
        print(f"[LEGEND_SIZE] ===== 圖例尺寸分析 =====")
        print(f"[LEGEND_SIZE] Widget尺寸: {widget_width} x {widget_height}")
        print(f"[LEGEND_SIZE] 當前圖例寬度設定: {legend_width}")
        print(f"[LEGEND_SIZE] 計算所需寬度: {calculated_width}")
        print(f"[LEGEND_SIZE] 圖例高度: {legend_height}")
        print(f"[LEGEND_SIZE] 圖例位置: x={actual_legend_x}, y={actual_legend_y}")
        print(f"[LEGEND_SIZE] 圖例右邊界: {actual_legend_x + legend_width}")
        print(f"[LEGEND_SIZE] Widget右邊界: {widget_width}")
        print(f"[LEGEND_SIZE] 是否超出: {'是' if actual_legend_x + legend_width > widget_width else '否'}")
        print(f"[LEGEND_SIZE] 超出距離: {max(0, actual_legend_x + legend_width - widget_width)}")
        
        # 使用計算出的寬度，但確保不超出邊界
        safe_width = min(calculated_width, widget_width - actual_legend_x - 10)
        print(f"[LEGEND_SIZE] 安全寬度: {safe_width}")
        
        # 圖例背景 - 使用安全寬度
        for i in range(3):  # 繪製3次確保覆蓋
            painter.fillRect(legend_x - 10, legend_y - 10, safe_width, legend_height, background_color)
        painter.setPen(QPen(border_color, 2))  # 粗邊框
        painter.drawRect(legend_x - 10, legend_y - 10, safe_width, legend_height)
        
        current_y = legend_y
        
        # 車手圖例標題 - 設置黑色
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(legend_x, current_y, "車手")
        current_y += 22
        
        # 車手圖例
        painter.setFont(QFont("Arial", 9))
        for i, series in enumerate(self.series_list):
            # 繪製加大的顏色方塊
            painter.setBrush(QBrush(series.color))
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.fillRect(legend_x, current_y - 8, 16, 16, series.color)
            painter.drawRect(legend_x, current_y - 8, 16, 16)
            
            # 繪製車手名稱
            painter.setPen(QPen(QColor(60, 60, 60), 1))
            painter.drawText(legend_x + 24, current_y + 4, series.name)
            current_y += 20
        
        # 分隔線
        current_y += 8
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawLine(legend_x, current_y, legend_x + 150, current_y)
        current_y += 15
        
        # 智能標記圖例標題
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(legend_x, current_y, "智能標記")
        current_y += 22
        
        # 智能標記圖例
        painter.setFont(QFont("Arial", 9))
        markers_info = [
            ('P', '進站', self.marker_colors['P']),
            ('F', '最快圈', self.marker_colors['F']),
            ('T', '輪胎更換', self.marker_colors.get('T', QColor(138, 43, 226))),
            ('A', '事故/危險', self.marker_colors['A']),
            ('S', '特殊圈', self.marker_colors['S']),
        ]
        
        for marker_type, description, color in markers_info:
            # 繪製加大的標記示例
            marker_pos = QPoint(legend_x + 10, current_y - 2)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(80, 80, 80), 2))
            
            # 🔍 調試：標記繪製信息
            print(f"[MARKER_DEBUG] 繪製標記 {marker_type}: 位置=({marker_pos.x()}, {marker_pos.y()}), 顏色=R{color.red()}G{color.green()}B{color.blue()}")
            
            if marker_type == 'P':
                # 進站 - 方形，加大尺寸
                print(f"[MARKER_DEBUG] {marker_type} - 方形: ({marker_pos.x() - 8}, {marker_pos.y() - 8}, 16, 16)")
                painter.fillRect(marker_pos.x() - 8, marker_pos.y() - 8, 16, 16, color)
                painter.drawRect(marker_pos.x() - 8, marker_pos.y() - 8, 16, 16)
            elif marker_type == 'F':
                # 最快圈 - 圓形，加大尺寸
                print(f"[MARKER_DEBUG] {marker_type} - 圓形: ({marker_pos.x() - 8}, {marker_pos.y() - 8}, 16, 16)")
                painter.drawEllipse(marker_pos.x() - 8, marker_pos.y() - 8, 16, 16)
            elif marker_type == 'T':
                # 輪胎更換 - 菱形，加大尺寸
                points = [
                    QPoint(marker_pos.x(), marker_pos.y() - 9),
                    QPoint(marker_pos.x() + 9, marker_pos.y()),
                    QPoint(marker_pos.x(), marker_pos.y() + 9),
                    QPoint(marker_pos.x() - 9, marker_pos.y())
                ]
                print(f"[MARKER_DEBUG] {marker_type} - 菱形: 4個點")
                painter.drawPolygon(points)
            elif marker_type == 'A':
                # 事故 - 三角形，加大尺寸
                points = [
                    QPoint(marker_pos.x(), marker_pos.y() - 10),
                    QPoint(marker_pos.x() - 9, marker_pos.y() + 6),
                    QPoint(marker_pos.x() + 9, marker_pos.y() + 6)
                ]
                print(f"[MARKER_DEBUG] {marker_type} - 三角形: 3個點")
                painter.drawPolygon(points)
            else:  # S - 特殊圈
                # 圓形，加大尺寸
                print(f"[MARKER_DEBUG] {marker_type} - 圓形: ({marker_pos.x() - 8}, {marker_pos.y() - 8}, 16, 16)")
                painter.drawEllipse(marker_pos.x() - 8, marker_pos.y() - 8, 16, 16)
            
            # 繪製標記說明 - 調整位置避免重疊
            painter.setPen(QPen(QColor(60, 60, 60), 1))
            painter.drawText(legend_x + 30, current_y + 4, f"{marker_type} - {description}")
            current_y += 24


class DriverSelectionWidget(QWidget):
    """車手選擇控制區"""
    
    drivers_selected = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_drivers = []
        self.selected_drivers = []
        self.driver_combos = []
        self.setup_ui()
        
    def setup_ui(self):
        """設置車手選擇介面 - 水平簡潔布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 車手選擇區域 - 水平布局
        driver_layout = QHBoxLayout()
        driver_layout.setSpacing(10)
        
        # 創建5個車手選擇下拉選單 - 水平排列
        for i in range(5):
            combo = QComboBox()
            combo.addItem("-- 請選擇 --")
            combo.currentTextChanged.connect(self._on_driver_selection_changed)
            combo.setMinimumWidth(80)
            combo.setMaximumWidth(100)
            
            self.driver_combos.append(combo)
            driver_layout.addWidget(combo)
        
        # 添加一些間距
        driver_layout.addSpacing(20)
        
        # 控制按鈕 - 在同一行
        self.clear_button = QPushButton("清除選擇")
        self.clear_button.clicked.connect(self._clear_selections)
        self.clear_button.setMaximumWidth(80)
        
        self.export_button = QPushButton("匯出圖表")
        self.export_button.clicked.connect(self._export_chart)
        self.export_button.setMaximumWidth(80)
        
        driver_layout.addWidget(self.export_button)
        driver_layout.addWidget(self.clear_button)
        driver_layout.addStretch()  # 推到左邊
        
        layout.addLayout(driver_layout)
        layout.addStretch()
        
    def update_available_drivers(self, drivers: List[str]):
        """更新可用車手列表"""
        print(f"[DRIVER_SELECTION] 🔄 更新車手列表: {drivers}")
        self.available_drivers = drivers
        
        # 更新所有下拉選單
        for i, combo in enumerate(self.driver_combos):
            current_selection = combo.currentText()
            combo.clear()
            combo.addItem("-- 請選擇 --")
            combo.addItems(drivers)
            
            # 恢復之前的選擇（如果仍然可用）
            if current_selection in drivers:
                combo.setCurrentText(current_selection)
        
        print(f"[DRIVER_SELECTION] ✅ 車手列表更新完成，總車手數: {len(drivers)}")
                
    def _on_driver_selection_changed(self):
        """車手選擇改變處理"""
        self._apply_selections()
        
    def _clear_selections(self):
        """清除所有選擇"""
        for combo in self.driver_combos:
            combo.setCurrentIndex(0)
        self._apply_selections()
        
    def _export_chart(self):
        """匯出圖表"""
        print("[DRIVER_SELECTION] 📊 匯出圖表功能待實現")
        # TODO: 實現圖表匯出功能
        
    def _apply_selections(self):
        """應用車手選擇"""
        selected = []
        for combo in self.driver_combos:
            driver = combo.currentText()
            if driver != "-- 請選擇 --" and driver not in selected:
                selected.append(driver)
        
        self.selected_drivers = selected
        self.drivers_selected.emit(selected)


class driverLapAnalysisChartWidget(QWidget):
    """詳細圈速分析主組件 - 修正版"""
    
    # 信號定義
    driver_selected = pyqtSignal(str)
    lap_selected = pyqtSignal(int, str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據存儲
        self.chart_data = {}
        self.selected_drivers = []
        
        # 設置UI
        self.setup_ui()
        
        print("[LAPTIME_CHART] 詳細圈速分析圖表組件初始化完成 (修正版架構)")
    
    def setup_ui(self):
        """設置主介面 - 垂直布局：車手選擇在上方，圖表在下方"""
        # 創建總佈局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 上方：車手選擇控制區 (水平緊湊布局)
        self.driver_selection = DriverSelectionWidget()
        self.driver_selection.drivers_selected.connect(self._on_drivers_selected)
        self.driver_selection.setMaximumHeight(80)  # 限制高度
        
        # 下方：專用圖表組件
        self.chart_widget = LaptimeChartWidget()
        
        # 添加到主布局
        main_layout.addWidget(self.driver_selection)
        main_layout.addWidget(self.chart_widget)
        
        # 設置拉伸因子（車手選擇區 : 圖表區 = 0 : 1，圖表獲得所有額外空間）
        main_layout.setStretchFactor(self.driver_selection, 0)
        main_layout.setStretchFactor(self.chart_widget, 1)
        
        # 設置最小尺寸
        self.setMinimumSize(1000, 600)
    
    def update_data(self, data: Dict[str, Any], selected_driver: str = None):
        """更新圖表數據"""
        try:
            print(f"[LAPTIME_CHART] 收到數據更新")
            print(f"[LAPTIME_CHART] 數據類型: {type(data)}")
            print(f"[LAPTIME_CHART] 數據鍵: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # 兼容處理：解包 charts_data
            if isinstance(data, dict) and 'charts_data' in data:
                data = data.get('charts_data', {})
                print("[LAPTIME_CHART] 解包 charts_data")
            
            self.chart_data = data
            
            # 獲取可用車手列表
            detailed_laptime_data = data.get('all_drivers_detailed_laptime', {})
            drivers_analyzed = data.get('drivers_analyzed', list(detailed_laptime_data.keys()))
            
            print(f"[LAPTIME_CHART] 可用車手: {drivers_analyzed}")
            
            # 更新車手選擇器
            self.driver_selection.update_available_drivers(drivers_analyzed)
            
            # 如果指定了預設車手，自動選擇
            if selected_driver and selected_driver in drivers_analyzed:
                if self.driver_selection.driver_combos:
                    self.driver_selection.driver_combos[0].setCurrentText(selected_driver)
            
            # 更新圖表（如果已有選擇的車手）
            if self.selected_drivers:
                self._update_chart_data()
                
        except Exception as e:
            print(f"[LAPTIME_CHART] 數據更新錯誤: {e}")
            traceback.print_exc()
    
    def _on_drivers_selected(self, drivers: List[str]):
        """處理車手選擇變更"""
        print(f"[LAPTIME_CHART] 車手選擇變更: {drivers}")
        self.selected_drivers = drivers
        self._update_chart_data()
        
        # 發射信號
        if drivers:
            self.driver_selected.emit(drivers[0])
    
    def _update_chart_data(self):
        """更新圖表數據"""
        try:
            print(f"[LAPTIME_CHART] 更新圖表，選中車手: {self.selected_drivers}")
            
            if not self.chart_data or not self.selected_drivers:
                self.chart_widget.update_series_data([])
                return
            
            # 獲取詳細圈速數據
            detailed_laptime_data = self.chart_data.get('all_drivers_detailed_laptime', {})
            
            # 轉換為圖表系列格式
            series_list = []
            colors = [
                ChartTheme.DRIVER1_COLOR,
                ChartTheme.DRIVER2_COLOR,
                ChartTheme.DRIVER3_COLOR,
                ChartTheme.DRIVER4_COLOR,
                ChartTheme.DRIVER5_COLOR
            ]
            
            for i, driver in enumerate(self.selected_drivers):
                if driver not in detailed_laptime_data:
                    continue
                    
                driver_data = detailed_laptime_data[driver]
                lap_data = driver_data.get('detailed_lap_data', [])
                
                if not lap_data:
                    continue
                
                # 創建數據點列表
                data_points = []
                for lap_info in lap_data:
                    lap_num = lap_info.get('lap_number', 0)
                    lap_time_sec = lap_info.get('lap_time_seconds', 0)
                    
                    if lap_time_sec > 0:  # 過濾無效圈速
                        # 提取智能標記
                        markers = self._extract_markers(driver_data, lap_num)
                        
                        data_point = ChartDataPoint(
                            x=lap_num,
                            y=lap_time_sec,
                            metadata={'markers': markers, 'driver': driver}
                        )
                        data_points.append(data_point)
                
                if data_points:
                    color = colors[i % len(colors)]
                    
                    series = ChartSeries(
                        name=driver,
                        data=data_points,
                        color=color,
                        line_width=2,
                        style='line'
                    )
                    series_list.append(series)
            
            # 更新圖表組件
            self.chart_widget.update_series_data(series_list)
            
        except Exception as e:
            print(f"[LAPTIME_CHART] 圖表數據更新錯誤: {e}")
            traceback.print_exc()
    
    def _extract_markers(self, driver_data: Dict, lap_num: int) -> List[str]:
        """提取指定圈數的智能標記"""
        markers = []
        smart_markers = driver_data.get('smart_markers_summary', {})
        
        # 調試：顯示智能標記數據結構
        if lap_num == 1:  # 只在第一圈顯示調試信息
            print(f"[LAPTIME_CHART_WIDGET] 智能標記數據結構:")
            print(f"[LAPTIME_CHART_WIDGET]   - driver_data 鍵: {list(driver_data.keys())}")
            print(f"[LAPTIME_CHART_WIDGET]   - smart_markers_summary 鍵: {list(smart_markers.keys())}")
            for key, value in smart_markers.items():
                if isinstance(value, dict) and 'lap_numbers' in str(value):
                    print(f"[LAPTIME_CHART_WIDGET]   - {key}: {value}")
        
        # 檢查各種標記類型 (修正後的結構)
        # 進站檢測
        pit_data = smart_markers.get('pit_stop_detection', {})
        if lap_num in pit_data.get('pit_lap_numbers', []):
            markers.append('P')
        
        # 最快圈檢測
        fastest_data = smart_markers.get('fastest_lap_detection', {})
        if lap_num in fastest_data.get('fastest_lap_numbers', []):
            markers.append('F')
            
        # 輪胎更換檢測 (作為進站的補充)
        tire_data = smart_markers.get('tire_change_detection', {})
        if lap_num in tire_data.get('tire_change_lap_numbers', []):
            if 'P' not in markers:  # 避免重複
                markers.append('T')  # 使用 T 表示輪胎更換
        
        # 事故/安全車檢測
        safety_data = smart_markers.get('accident_safety_detection', {})
        incident_laps = safety_data.get('incident_lap_numbers', [])
        if lap_num in incident_laps:
            markers.append('A')  # 事故/危險
            
        # 特殊圈數檢測 (起跑、終點等)
        special_data = smart_markers.get('special_lap_marking', {})
        if lap_num in special_data.get('special_lap_numbers', []):
            markers.append('S')  # 特殊圈
            
        # TODO: 未來可以加入降雨檢測 (當數據可用時)
        # rain_data = smart_markers.get('rain_detection', {})
        # if lap_num in rain_data.get('rain_lap_numbers', []):
        #     markers.append('R')
            
        # 調試：顯示找到的標記
        if markers:
            print(f"[LAPTIME_CHART_WIDGET] 圈 {lap_num} 找到標記: {markers}")
            
        return markers
    
    def set_data(self, data: Dict[str, Any]):
        """兼容舊版介面"""
        self.update_data(data)
    
    def update_chart(self):
        """兼容舊版介面"""
        self.chart_widget.update()


if __name__ == "__main__":
    """測試用例"""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 創建測試視窗
    widget = driverLapAnalysisChartWidget()
    
    # 模擬測試數據
    test_data = {
        'drivers_analyzed': ['VER', 'LEC', 'NOR'],
        'all_drivers_detailed_laptime': {
            'VER': {
                'total_laps': 10,
                'detailed_lap_data': [
                    {'lap_number': i, 'lap_time_seconds': 90 + i * 0.5 + (i % 3) * 0.2}
                    for i in range(1, 11)
                ],
                'smart_markers_summary': {
                    'pit_stops': [5],
                    'fastest_laps': [3],
                    'accidents': [],
                    'rain_laps': []
                }
            },
            'LEC': {
                'total_laps': 10,
                'detailed_lap_data': [
                    {'lap_number': i, 'lap_time_seconds': 90.5 + i * 0.3 + (i % 4) * 0.3}
                    for i in range(1, 11)
                ],
                'smart_markers_summary': {
                    'pit_stops': [6],
                    'fastest_laps': [4],
                    'accidents': [2],
                    'rain_laps': []
                }
            }
        }
    }
    
    # 更新數據並顯示
    widget.update_data(test_data)
    widget.show()
    
    print("詳細圈速分析圖表組件測試啟動 (修正版)")
    sys.exit(app.exec_())
