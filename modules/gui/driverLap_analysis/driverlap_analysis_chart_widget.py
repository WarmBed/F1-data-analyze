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
        
        # 標記顏色配置 - 新的旗幟標記系統
        self.marker_colors = {
            'P': QColor(255, 193, 7),    # 黃色 - 進站
            'F': QColor(40, 167, 69),    # 綠色 - 最快圈
            'T': QColor(138, 43, 226),   # 紫羅蘭色 - 輪胎更換
            'Y': QColor(255, 193, 7),    # 黃色 - 黃旗/雙黃旗
            'S': QColor(128, 128, 128),  # 灰色 - 安全車/虛擬安全車
            'R': QColor(220, 53, 69),    # 紅色 - 紅旗
            # 已停用的標記
            # 'A': QColor(220, 53, 69),  # 紅色 - 事故/危險 (已拆分為具體類型)
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
            
            # 計算繪製區域（圖例重疊模式，不預留空間）
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
            
            # 繪製圖例 (重疊模式，右上角覆蓋)
            self._draw_legend(painter)
            
        except Exception as e:
            print(f"[LAPTIME_CHART_WIDGET] 繪製錯誤: {e}")
            traceback.print_exc()
            
            # 顯示錯誤信息
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, f"繪製錯誤: {str(e)}")
    
    def _calculate_legend_space(self):
        """智能計算圖例所需空間"""
        if not self.series_list:
            return {'width': 0, 'height': 0, 'x': 0, 'y': 0}
        
        # 計算內容尺寸
        driver_count = len(self.series_list)
        marker_count = 5  # P, F, T, A, S
        
        # 寬度計算 (取車手名稱和標記描述的最大寬度)
        max_driver_width = 54 + 20    # 方塊 + 間距 + 車手名 + 邊距
        max_marker_width = 110 + 20   # 標記 + 間距 + 文字 + 邊距
        content_width = max(max_driver_width, max_marker_width)
        
        # 高度計算
        header_height = 22 * 2        # 兩個標題
        driver_height = driver_count * 20   # 每個車手20px
        marker_height = marker_count * 24   # 每個標記24px
        spacing = 30                  # 間距和邊距
        content_height = header_height + driver_height + marker_height + spacing
        
        # 位置計算 (右上角)
        widget_width = self.width()
        widget_height = self.height()
        
        # 確保不超出邊界
        safe_width = min(content_width, widget_width * 0.3)  # 最多佔用30%寬度
        safe_height = min(content_height, widget_height - 40)  # 保留上下邊距
        
        legend_x = widget_width - safe_width - 10
        legend_y = 20
        
        return {
            'width': safe_width,
            'height': safe_height,
            'x': legend_x,
            'y': legend_y,
            'content_width': content_width,
            'content_height': content_height
        }
    
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
        # 防護檢查：確保 series_list 已初始化且不為空
        if not hasattr(self, 'series_list') or not self.series_list:
            print(f"[LAPTIME_CHART_WIDGET] ⚠️ series_list 未初始化或為空，跳過智能標記繪製")
            return
            
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
        """繪製單個標記 - 純文字版本，支援組合標記"""
        print(f"[MARKER_TEXT] 🎯 繪製文字標記 {marker_type} (純文字版本)")
        
        # 統一的文字設置 - 使用較大的字體確保可讀性
        painter.setPen(QPen(color, 2))  # 使用傳入的顏色
        painter.setFont(QFont("Arial", 12, QFont.Bold))  # 統一較大字體
        
        if marker_type == 'P':  # 進站
            painter.drawText(position.x() - 6, position.y() + 4, "P")
            
        elif marker_type == 'A':  # 事故
            painter.drawText(position.x() - 6, position.y() + 4, "A")
            
        elif marker_type == 'F':  # 最快圈
            painter.drawText(position.x() - 6, position.y() + 4, "F")
            
        elif marker_type == 'T':  # 輪胎更換
            painter.drawText(position.x() - 6, position.y() + 4, "T")
            
        elif marker_type == 'Y':  # 黃旗/雙黃旗
            painter.drawText(position.x() - 6, position.y() + 4, "Y")
            
        elif marker_type == 'S':  # 安全車/虛擬安全車
            painter.drawText(position.x() - 6, position.y() + 4, "S")
            
        elif marker_type == 'R':  # 紅旗
            painter.drawText(position.x() - 6, position.y() + 4, "R")
            
        # elif marker_type == 'A':  # 事故/危險 (已停用，拆分為具體類型)
        #     painter.drawText(position.x() - 6, position.y() + 4, "A")
            painter.drawText(position.x() - 4, position.y() + 2, "R")
            
        else:  # 未知類型 - 圓形
            painter.drawEllipse(position.x() - 6, position.y() - 6, 12, 12)
    
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
        """繪製圖例 - 重疊模式，右上角覆蓋，強制白色背景 [VERSION 3.0]"""
        if not self.series_list:
            print(f"[LEGEND_DEBUG] ⚠️ 沒有數據系列，跳過圖例繪製")
            return
        
        print(f"[LEGEND_DEBUG] � 使用圖例版本 3.0 - 強制白色背景調試版")
        print(f"[LEGEND_DEBUG] 數據系列數量: {len(self.series_list)}")
        
        # 計算圖例尺寸和位置
        driver_count = len(self.series_list)
        marker_count = 6  # P, F, T, Y, S, R (移除了 PT 組合標記)
        
        # 內容尺寸計算 - 調整寬度
        content_width = 140  # 減少寬度，不再需要適應 "進站+換胎"
        header_height = 22 * 2        # 兩個標題
        driver_height = driver_count * 20   # 每個車手20px
        marker_height = marker_count * 22   # 每個標記22px
        padding = 20                  # 內邊距
        content_height = header_height + driver_height + marker_height + padding
        
        # 位置：右上角，小幅偏移
        legend_x = self.width() - content_width - 15
        legend_y = 15
        
        print(f"[LEGEND_DEBUG] 圖例位置: ({legend_x}, {legend_y})")
        print(f"[LEGEND_DEBUG] 圖例尺寸: {content_width} x {content_height}")
        
        # 🔥 強制白色背景 - 版本 3.0 加強版
        white_color = QColor(255, 255, 255, 255)  # 完全不透明的白色
        print(f"[LEGEND_DEBUG] 🎨 設定背景色為: R{white_color.red()}, G{white_color.green()}, B{white_color.blue()}, A{white_color.alpha()}")
        
        # 多重白色填充確保效果
        for i in range(3):  # 重複填充3次
            painter.fillRect(legend_x - 5, legend_y - 5, content_width + 10, content_height + 10, white_color)
        print(f"[LEGEND_DEBUG] ✅ 白色背景填充完成 (重複3次)")
        
        # 黑色邊框
        border_color = QColor(60, 60, 60)
        painter.setPen(QPen(border_color, 2))
        painter.drawRect(legend_x, legend_y, content_width, content_height)
        print(f"[LEGEND_DEBUG] ✅ 邊框繪製完成")
        
        # 內容繪製區域
        content_x = legend_x + 10
        current_y = legend_y + 15
        
        print(f"[LEGEND] 圖例重疊模式: 位置=({legend_x}, {legend_y}), 尺寸={content_width}x{content_height}")
        
        # 車手圖例標題
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(content_x, current_y, "車手")
        current_y += 22
        
        # 車手圖例內容
        painter.setFont(QFont("Arial", 9))
        for i, series in enumerate(self.series_list):
            # 顏色方塊
            painter.setBrush(QBrush(series.color))
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.fillRect(content_x, current_y - 8, 14, 14, series.color)
            painter.drawRect(content_x, current_y - 8, 14, 14)
            
            # 車手名稱
            painter.setPen(QPen(QColor(40, 40, 40), 1))
            painter.drawText(content_x + 22, current_y + 3, series.name)
            current_y += 20
        
        # 分隔線
        current_y += 6
        painter.setPen(QPen(QColor(160, 160, 160), 1))
        painter.drawLine(content_x, current_y, content_x + content_width - 20, current_y)
        current_y += 12
        
        # 智能標記圖例標題
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(content_x, current_y, "智能標記")
        current_y += 22
        
        # 智能標記內容
        painter.setFont(QFont("Arial", 9))
        markers_info = [
            ('P', '進站', self.marker_colors['P']),
            ('F', '最快圈', self.marker_colors['F']),
            ('T', '輪胎更換', self.marker_colors.get('T', QColor(138, 43, 226))),
            ('Y', '黃旗', self.marker_colors.get('Y', QColor(255, 193, 7))),      # 黃色
            ('S', '安全車', self.marker_colors.get('S', QColor(128, 128, 128))),   # 灰色
            ('R', '紅旗', self.marker_colors.get('R', QColor(220, 53, 69))),      # 紅色
            # ('PT', '進站+換胎', self.marker_colors['P']),  # 已移除組合標記
            # ('A', '事故/危險', self.marker_colors['A']),  # 已停用，拆分為具體類型
        ]
        
        for marker_type, description, color in markers_info:
            # 標記示例 - 改進版本，解決文字超出問題
            marker_pos = QPoint(content_x + 8, current_y - 1)
            self._draw_legend_marker_improved(painter, marker_pos, marker_type, color)
            
            # 標記說明文字 - 只顯示描述，不重複字母
            painter.setPen(QPen(QColor(40, 40, 40), 1))
            painter.drawText(content_x + 25, current_y + 3, f"- {description}")
            current_y += 22  # 調整為22px間距，更緊湊
    
    def _draw_legend_marker_improved(self, painter: QPainter, position: QPoint, marker_type: str, color: QColor):
        """在圖例中繪製標記示例 - 純文字版本，支援組合標記"""
        
        # 統一的文字設置
        painter.setPen(QPen(color, 2))  # 使用傳入的顏色
        painter.setFont(QFont("Arial", 10, QFont.Bold))  # 統一字體
        
        if marker_type == 'P':  # 進站
            painter.drawText(position.x() - 5, position.y() + 3, "P")
            
        elif marker_type == 'F':  # 最快圈
            painter.drawText(position.x() - 5, position.y() + 3, "F")
            
        elif marker_type == 'T':  # 輪胎更換
            painter.drawText(position.x() - 5, position.y() + 3, "T")
            
        elif marker_type == 'Y':  # 黃旗
            painter.drawText(position.x() - 5, position.y() + 3, "Y")
            
        elif marker_type == 'S':  # 安全車
            painter.drawText(position.x() - 5, position.y() + 3, "S")
            
        elif marker_type == 'R':  # 紅旗
            painter.drawText(position.x() - 5, position.y() + 3, "R")
            
        # elif marker_type == 'A':  # 事故/危險 (已停用)
        #     painter.drawText(position.x() - 5, position.y() + 3, "A")


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

        # 輪胎更換檢測
        tire_data = smart_markers.get('tire_change_detection', {})
        if lap_num in tire_data.get('tire_change_lap_numbers', []):
            markers.append('T')

        # 最快圈檢測
        fastest_data = smart_markers.get('fastest_lap_detection', {})
        if lap_num in fastest_data.get('fastest_lap_numbers', []):
            markers.append('F')
        
        # 賽道狀況檢測 - 根據 smart_markers 中的事故檢測數據
        safety_data = smart_markers.get('accident_safety_detection', {})
        incident_laps = safety_data.get('incident_lap_numbers', [])
        
        # 檢查是否在事故圈次列表中
        if lap_num in incident_laps:
            # 因為目前的數據結構沒有提供具體的 TrackStatus 信息
            # 我們先使用通用的事故標記，未來可以根據更詳細的數據來區分
            # TODO: 需要在 CLI 分析中提供更詳細的 TrackStatus 信息
            markers.append('Y')  # 暫時使用黃旗作為通用事故標記
            
        # TODO: 未來可以加入特殊圈數檢測 (起跑、終點等)
        # special_data = smart_markers.get('special_lap_marking', {})
        # if lap_num in special_data.get('special_lap_numbers', []):
        #     markers.append('S')  # 特殊圈
            
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
