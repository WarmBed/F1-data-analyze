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
from typing import Dict, List, Any, Optional, Tuple, Set
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QComboBox, QCheckBox, QGroupBox, QGridLayout, QScrollArea,
                            QFrame, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QFontMetrics

# 導入翻譯函數
from core.gui_i18n import tr
from core.gui_settings_manager import gui_settings_manager
from .lap_filter_utils import (
    extract_caution_laps,
    lap_is_under_caution,
    lap_is_pit_stop,
    normalize_lap_number,
)


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
    
    # 🆕 信號定義
    pinned_tooltips_changed = pyqtSignal(int, str)  # (固定數量, 時間差文字)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.series_list = []
        self.setMinimumSize(200, 100)  # 調整為與 Tire Analysis 一致的最小尺寸
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
            'W': QColor(100, 149, 237),  # 矢車菊藍 - 降雨天氣
            # 已停用的標記
            # 'A': QColor(220, 53, 69),  # 紅色 - 事故/危險 (已拆分為具體類型)
        }
        
        # 🆕 圖例拖移功能變數
        self.legend_dragging = False
        self.legend_drag_start = QPoint()
        self.legend_offset = QPoint(0, 0)  # 圖例的偏移位置
        self.legend_rect = QRect()  # 圖例的矩形區域
        
        # 🆕 圖例顯示控制變數
        self.legend_show_markers = True  # True: 顯示完整圖例, False: 僅顯示車手
        
        # 🆕 Tooltip 相關變數
        self.setMouseTracking(True)  # 啟用滑鼠追蹤以顯示 Tooltip
        self.hover_point = None  # 當前懸停的數據點
        self.hover_screen_pos = None  # 當前懸停點的螢幕座標（用於視覺反饋）
        self.hover_tooltip_text = ""  # 自繪 Tooltip 文字
        self.chart_rect = QRect()  # 圖表繪製區域（用於座標轉換）
        self.x_range = (0, 1)  # X 軸範圍
        self.y_range = (0, 1)  # Y 軸範圍
        
        # 🆕 固定 Tooltip 功能（左鍵點擊固定，最多2個）
        self.pinned_tooltips = []  # 固定的 Tooltip 列表 [{point, screen_pos, text, lap_time}, ...]
        self.max_pinned = 2  # 最多固定2個
        
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
                font = QFont()
                font.setPointSize(8)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignCenter, "Please select drivers to display lap time data")
                return
            
            # 計算繪製區域（動態邊距，適應小尺寸）
            # 根據視窗大小動態調整邊距，左側需要更多空間給 Y 軸標籤和標題
            base_margin = min(self.width(), self.height()) * 0.08  # 8% 動態邊距
            margin = max(20, min(60, int(base_margin)))  # 最小20px，最大60px
            left_margin = max(95, int(self.width() * 0.12))  # 左側邊距：最小95px或視窗12%（增加空間）
            chart_rect = QRect(
                left_margin,  # 使用較大的左側邊距
                margin, 
                self.width() - left_margin - margin,  # 調整寬度
                self.height() - 2 * margin
            )
            
            # 保存圖表區域和數據範圍供 Tooltip 使用
            self.chart_rect = chart_rect
            
            # 計算數據範圍
            x_min, x_max, y_min, y_max = self._calculate_data_range()
            self.x_range = (x_min, x_max)  # 保存供 Tooltip 使用
            self.y_range = (y_min, y_max)  # 保存供 Tooltip 使用
            
            if x_min >= x_max or y_min >= y_max:
                painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
                font = QFont()
                font.setPointSize(8)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignCenter, "Invalid data range")
                return
            
            # 繪製網格和軸
            self._draw_grid_and_axes(painter, chart_rect, (x_min, x_max), (y_min, y_max))
            
            # 繪製數據線
            self._draw_data_lines(painter, chart_rect, (x_min, x_max), (y_min, y_max))
            
            # 繪製智能標記
            self._draw_smart_markers(painter, chart_rect, (x_min, x_max), (y_min, y_max))
            
            # 🆕 繪製懸停點高亮（在圖例之前，避免被圖例遮擋）
            if self.hover_screen_pos:
                painter.setPen(QPen(QColor(255, 100, 100), 3))  # 紅色外框
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(self.hover_screen_pos, 12, 12)  # 繪製高亮圓圈
            
            # 繪製圖例 (重疊模式，右上角覆蓋)
            self._draw_legend(painter)
            
            # 🆕 繪製固定的 Tooltip（使用不同顏色標示）
            for pinned in self.pinned_tooltips:
                # 繪製固定點的高亮（藍色外框）
                painter.setPen(QPen(QColor(0, 123, 255), 3))  # 藍色外框
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(pinned['screen_pos'], 12, 12)
                # 繪製固定的 Tooltip（藍色背景）
                self._draw_custom_tooltip(painter, pinned['screen_pos'], pinned['text'], is_pinned=True)
            
            # 🆕 繪製懸停 Tooltip（黃色背景，最後繪製確保在最上層）
            if self.hover_tooltip_text and self.hover_screen_pos:
                self._draw_custom_tooltip(painter, self.hover_screen_pos, self.hover_tooltip_text, is_pinned=False)
            
        except Exception as e:
            print(f"[LAPTIME_CHART_WIDGET] 繪製錯誤: {e}")
            traceback.print_exc()
            
            # 顯示錯誤信息
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, f"Drawing Error: {str(e)}")
        finally:
            # 確保 painter 總是被正確結束
            if painter.isActive():
                painter.end()
    
    def _calculate_legend_space(self):
        """智能計算圖例所需空間"""
        if not self.series_list:
            return {'width': 0, 'height': 0, 'x': 0, 'y': 0}
        
        # 計算內容尺寸
        driver_count = len(self.series_list)
        marker_count = 5  # P, F, T, A, S
        
        # 寬度計算 - 響應式尺寸 (基於視窗寬度)
        widget_width = self.width()
        base_size = min(widget_width * 0.08, 80)  # 基礎尺寸：視窗8%或最大80px
        
        max_driver_width = base_size + 20     # 方塊 + 間距 + 車手名 + 邊距
        max_marker_width = base_size * 1.5 + 20   # 標記 + 間距 + 文字 + 邊距
        content_width = max(max_driver_width, max_marker_width)
        
        # 高度計算 - 響應式尺寸 (基於視窗高度)
        widget_height = self.height()
        base_height = min(widget_height * 0.04, 24)  # 基礎高度：視窗4%或最大24px
        
        header_height = base_height        # 只有一個標題 ("Drivers")
        driver_height = driver_count * max(base_height * 0.8, 16)   # 每個車手最小16px
        marker_height = marker_count * base_height   # 每個標記使用基礎高度
        spacing = max(base_height * 1.2, 20)         # 間距和邊距，最小20px
        content_height = header_height + driver_height + marker_height + spacing
        
        # 位置計算 (右上角)
        widget_width = self.width()
        widget_height = self.height()
        
        # 確保不超出邊界 - 響應式計算
        max_legend_width_ratio = 0.35 if widget_width < 400 else 0.3  # 小視窗時允許更大比例
        safe_width = min(content_width, widget_width * max_legend_width_ratio)
        
        top_margin = max(widget_height * 0.02, 10)  # 上邊距：視窗2%或最小10px
        bottom_margin = max(widget_height * 0.05, 20)  # 下邊距：視窗5%或最小20px
        safe_height = min(content_height, widget_height - top_margin - bottom_margin)
        
        legend_x = widget_width - safe_width - max(widget_width * 0.01, 5)  # 右邊距響應式
        legend_y = top_margin
        
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
            
            # X軸標籤 - 響應式字體
            if i < 5:
                lap = x_range[0] + i * (x_range[1] - x_range[0]) / 5
                painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
                axis_font_size = max(7, min(10, int(min(self.width(), self.height()) * 0.02)))
                font = QFont()
                font.setPointSize(8)
                painter.setFont(font)
                label_offset = max(15, int(self.height() * 0.025))  # 響應式標籤偏移
                painter.drawText(int(x) - 15, rect.bottom() + label_offset, f"Lap {int(lap)}")
                painter.setPen(QPen(ChartTheme.GRID_COLOR, 1))
        
        # 水平網格線（圈速）
        for i in range(6):
            y = rect.top() + i * rect.height() / 5
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
            
            # Y軸標籤 - 響應式字體，調整位置使其在Y軸線和標題之間
            if i < 5:
                laptime = y_range[1] - i * (y_range[1] - y_range[0]) / 5
                painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
                axis_font_size = max(7, min(10, int(min(self.width(), self.height()) * 0.02)))
                font = QFont()
                font.setPointSize(8)
                painter.setFont(font)
                # 調整標籤偏移量：應該在Y軸標題和Y軸線之間
                label_offset = max(45, int(self.width() * 0.06))  # 減少偏移量，更靠近Y軸線
                painter.drawText(rect.left() - label_offset, int(y) + 5, f"{laptime:.1f}s")
                painter.setPen(QPen(ChartTheme.GRID_COLOR, 1))
        
        # 繪製軸標題 - 響應式字體
        painter.setPen(QPen(ChartTheme.TEXT_COLOR, 1))
        title_font_size = max(8, min(12, int(min(self.width(), self.height()) * 0.025)))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        # X軸標題
        x_title_offset = max(20, int(self.height() * 0.04))
        painter.drawText(rect.center().x() - 30, rect.bottom() + x_title_offset, tr("lap_number_axis", "Lap Number"))
        
        # Y軸標題（旋轉）- 位置應該在Y軸數值的外側（更遠離圖表）
        painter.save()
        y_title_offset = max(80, int(self.width() * 0.105))  # 增加偏移量，確保在數值外側
        painter.translate(rect.left() - y_title_offset, rect.center().y())
        painter.rotate(-90)
        painter.drawText(-50, 0, "Lap Time (sec)")  # 調整文字位置
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
        
        # 統一的文字設置 - 響應式字體大小
        painter.setPen(QPen(color, 2))  # 使用傳入的顏色
        marker_font_size = max(8, min(14, int(min(self.width(), self.height()) * 0.03)))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
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
            
        elif marker_type == 'W':  # 降雨天氣
            painter.drawText(position.x() - 6, position.y() + 4, "W")
            
        # elif marker_type == 'A':  # 事故/危險 (已停用，拆分為具體類型)
        #     painter.drawText(position.x() - 6, position.y() + 4, "A")
            
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
        """繪製圖例 - 重疊模式，右上角覆蓋，強制白色背景 [VERSION 3.1 - 支援顯示/隱藏]"""
        if not self.series_list:
            print(f"[LEGEND_DEBUG] ⚠️ 沒有數據系列，跳過圖例繪製")
            return
        
        print(f"[LEGEND_DEBUG] 🎨 使用圖例版本 3.1 - 支援顯示/隱藏標記")
        print(f"[LEGEND_DEBUG] 數據系列數量: {len(self.series_list)}")
        print(f"[LEGEND_DEBUG] 標記顯示狀態: {self.legend_show_markers}")
        
        # 計算圖例尺寸和位置
        driver_count = len(self.series_list)
        marker_count = 5 if self.legend_show_markers else 0  # 隱藏時不計算標記
        
        # 內容尺寸計算 - 根據顯示模式調整
        content_width = 140  # 減少寬度，不再需要適應 "進站+換胎"
        header_height = 22 if self.legend_show_markers else 22  # 僅 Drivers 標題
        driver_height = driver_count * 20   # 每個車手20px
        marker_height = marker_count * 22 if self.legend_show_markers else 0   # 隱藏時不顯示標記
        padding = 20 if self.legend_show_markers else 10  # 隱藏時減少內邊距
        separator_height = 12 if self.legend_show_markers else 0  # 分隔線高度
        content_height = header_height + driver_height + separator_height + marker_height + padding
        
        # 位置：右上角，小幅偏移 + 用戶拖移的偏移量
        legend_x = self.width() - content_width - 15 + self.legend_offset.x()
        legend_y = 15 + self.legend_offset.y()
        
        # 🆕 保存圖例矩形區域供滑鼠事件使用
        self.legend_rect = QRect(legend_x, legend_y, content_width, content_height)
        
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
        title_font = QFont()
        title_font.setPointSize(8)
        painter.setFont(title_font)
        painter.drawText(content_x, current_y, "Drivers")
        current_y += 22
        
        # 響應式字體和尺寸設定
        widget_size = min(self.width(), self.height())
        font_size = max(8, min(12, int(widget_size * 0.025)))  # 基於視窗大小的字體
        square_size = max(10, min(16, int(widget_size * 0.035)))  # 響應式方塊大小
        line_spacing = max(16, min(24, int(square_size * 1.4)))  # 行距隨方塊大小調整
        
        # 車手圖例內容
        content_font = QFont()
        content_font.setPointSize(8)
        painter.setFont(content_font)
        for i, series in enumerate(self.series_list):
            # 顏色方塊
            painter.setBrush(QBrush(series.color))
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.fillRect(content_x, current_y - square_size//2, square_size, square_size, series.color)
            painter.drawRect(content_x, current_y - square_size//2, square_size, square_size)
            
            # 車手名稱
            painter.setPen(QPen(QColor(40, 40, 40), 1))
            painter.drawText(content_x + square_size + 8, current_y + 3, series.name)
            current_y += line_spacing
        
        # 🆕 僅在顯示標記模式下繪製分隔線和標記
        if self.legend_show_markers:
            # 分隔線
            current_y += max(4, font_size//2)
            painter.setPen(QPen(QColor(160, 160, 160), 1))
            painter.drawLine(content_x, current_y, content_x + content_width - 20, current_y)
            current_y += max(8, font_size)
            
            # 移除智能標記圖例標題，直接顯示標記內容
            # current_y += max(18, font_size * 2)  # 移除標題的垂直空間
            
            # 智能標記內容
            marker_content_font = QFont()
            marker_content_font.setPointSize(8)
            painter.setFont(marker_content_font)
            markers_info = [
            ('P', 'Pit Stop', self.marker_colors['P']),
            ('F', 'Fastest Lap', self.marker_colors['F']),
            # ('T', 'Tire Change', self.marker_colors.get('T', QColor(138, 43, 226))),  # 已移除
            ('Y', 'Yellow Flag', self.marker_colors.get('Y', QColor(255, 193, 7))),      # 黃色
            ('S', 'Safety Car', self.marker_colors.get('S', QColor(128, 128, 128))),   # 灰色
            ('R', 'Red Flag', self.marker_colors.get('R', QColor(220, 53, 69))),      # 紅色
            # ('W', 'Rain', self.marker_colors.get('W', QColor(100, 149, 237))),    # 矢車菊藍 - 已移除
                # ('PT', '進站+換胎', self.marker_colors['P']),  # 已移除組合標記
                # ('A', '事故/危險', self.marker_colors['A']),  # 已停用，拆分為具體類型
            ]
            
            for marker_type, description, color in markers_info:
                # 標記示例 - 改進版本，解決文字超出問題
                marker_pos = QPoint(content_x + square_size//2, current_y - 1)
                self._draw_legend_marker_improved(painter, marker_pos, marker_type, color, font_size)
                
                # 標記說明文字 - 只顯示描述，不重複字母
                painter.setPen(QPen(QColor(40, 40, 40), 1))
                painter.drawText(content_x + square_size + 8, current_y + 3, f"- {description}")
                current_y += line_spacing  # 使用響應式行距
    
    def _draw_legend_marker_improved(self, painter: QPainter, position: QPoint, marker_type: str, color: QColor, font_size: int = 10):
        """在圖例中繪製標記示例 - 純文字版本，支援組合標記"""
        
        # 統一的文字設置 - 響應式字體
        painter.setPen(QPen(color, 2))  # 使用傳入的顏色
        legend_marker_font = QFont()
        legend_marker_font.setPointSize(8)
        painter.setFont(legend_marker_font)  # 使用響應式字體
        
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
    
    # 🆕 滑鼠事件處理 - 圖例拖移功能和顯示切換
    def mouseDoubleClickEvent(self, event):
        """雙擊圖例切換顯示/隱藏標記"""
        if event.button() == Qt.LeftButton:
            if self.legend_rect.contains(event.pos()):
                self.legend_show_markers = not self.legend_show_markers
                print(f"[LEGEND] 切換標記顯示狀態: {self.legend_show_markers}")
                self.update()  # 重繪圖表
                event.accept()
                return
        super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 檢查是否點擊圖例 / 固定 Tooltip / 清除固定"""
        if event.button() == Qt.LeftButton:
            # 優先處理圖例拖移
            if self.legend_rect.contains(event.pos()):
                self.legend_dragging = True
                self.legend_drag_start = event.pos() - self.legend_offset
                self.setCursor(Qt.ClosedHandCursor)  # 改變游標為抓取狀
                event.accept()
                return
            
            # 🆕 左鍵點擊固定 Tooltip（最多2個）
            if self.hover_point and self.hover_screen_pos:
                self._pin_tooltip()
                event.accept()
                return
        
        elif event.button() == Qt.RightButton:
            # 🆕 右鍵清除所有固定的 Tooltip
            if self.pinned_tooltips:
                self.pinned_tooltips.clear()
                print("[TOOLTIP] 🗑️ 已清除所有固定 Tooltip")
                self._update_time_diff_display()  # 🆕 清空時間差顯示
                self.update()
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 拖移圖例 + 顯示數據點 Tooltip"""
        if self.legend_dragging:
            # 計算新的偏移量
            new_offset = event.pos() - self.legend_drag_start
            
            # 限制圖例不超出視窗範圍
            max_x = self.width() - self.legend_rect.width() - 15
            max_y = self.height() - self.legend_rect.height() - 15
            min_x = -self.width() + self.legend_rect.width() + 30
            min_y = -15
            
            new_offset.setX(max(min_x, min(max_x, new_offset.x())))
            new_offset.setY(max(min_y, min(max_y, new_offset.y())))
            
            self.legend_offset = new_offset
            self.update()  # 重繪圖表
            event.accept()
            return
        elif self.legend_rect.contains(event.pos()):
            # 滑鼠懸停在圖例上，顯示可移動提示
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            # 🆕 檢查是否懸停在數據點上
            self._check_hover_point(event.pos())
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖移"""
        if event.button() == Qt.LeftButton and self.legend_dragging:
            self.legend_dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
    
    def _pin_tooltip(self):
        """固定當前懸停的 Tooltip（最多2個）"""
        if not self.hover_point or not self.hover_screen_pos:
            return
        
        # 檢查是否已經固定過這個點
        for pinned in self.pinned_tooltips:
            if pinned['point'] == self.hover_point:
                print("[TOOLTIP] ⚠️ 此點已固定")
                return
        
        # 如果已達到最大固定數量，移除最舊的
        if len(self.pinned_tooltips) >= self.max_pinned:
            removed = self.pinned_tooltips.pop(0)
            print(f"[TOOLTIP] 🗑️ 移除最舊的固定點")
        
        # 提取圈速時間（用於計算時間差）
        lap_time = self.hover_point.y  # 假設 y 值就是圈速秒數
        
        # 固定新的 Tooltip
        pinned_data = {
            'point': self.hover_point,
            'screen_pos': QPoint(self.hover_screen_pos),
            'text': self.hover_tooltip_text,
            'lap_time': lap_time
        }
        self.pinned_tooltips.append(pinned_data)
        print(f"[TOOLTIP] 📌 已固定 Tooltip ({len(self.pinned_tooltips)}/{self.max_pinned})")
        
        # 🆕 更新時間差顯示
        self._update_time_diff_display()
        
        self.update()
    
    def get_pinned_time_diff(self) -> Optional[str]:
        """獲取兩個固定點的時間差（供外部使用）"""
        if len(self.pinned_tooltips) != 2:
            return None
        
        time1 = self.pinned_tooltips[0]['lap_time']
        time2 = self.pinned_tooltips[1]['lap_time']
        diff = abs(time2 - time1)
        
        # 格式化時間差
        if diff >= 60:
            minutes = int(diff // 60)
            seconds = diff % 60
            return f"+{minutes}:{seconds:06.3f}"
        else:
            return f"+{diff:.3f}s"
    
    def _update_time_diff_display(self):
        """更新時間差顯示（通過信號通知父容器）"""
        pinned_count = len(self.pinned_tooltips)
        time_diff_text = ""
        
        if pinned_count == 2:
            time_diff = self.get_pinned_time_diff()
            if time_diff:
                time_diff_text = f"Diff: {time_diff}"
                print(f"[TOOLTIP] ⏱️ 時間差: {time_diff}")
        
        # 發射信號通知父容器
        self.pinned_tooltips_changed.emit(pinned_count, time_diff_text)
    
    def _draw_custom_tooltip(self, painter: QPainter, anchor_pos: QPoint, text: str, is_pinned: bool = False):
        """繪製自訂 Tooltip（直接在圖表上繪製）"""
        # 分割多行文字
        lines = text.split('\n')
        
        # 計算 Tooltip 尺寸
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        max_width = 0
        total_height = 0
        line_heights = []
        
        for line in lines:
            line_width = fm.horizontalAdvance(line)
            line_height = fm.height()
            max_width = max(max_width, line_width)
            line_heights.append(line_height)
            total_height += line_height
        
        # 內邊距
        padding = 8
        tooltip_width = max_width + 2 * padding
        tooltip_height = total_height + 2 * padding
        
        # 計算 Tooltip 位置（在懸停點右上方）
        offset_x = 15
        offset_y = -15
        tooltip_x = anchor_pos.x() + offset_x
        tooltip_y = anchor_pos.y() + offset_y - tooltip_height
        
        # 確保 Tooltip 不超出視窗
        if tooltip_x + tooltip_width > self.width():
            tooltip_x = anchor_pos.x() - tooltip_width - 15
        if tooltip_y < 0:
            tooltip_y = anchor_pos.y() + 15
        
        # 繪製背景（懸停=淺黃色，固定=淺藍色）
        tooltip_rect = QRect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        if is_pinned:
            painter.setBrush(QBrush(QColor(173, 216, 230, 230)))  # 淺藍色（固定）
        else:
            painter.setBrush(QBrush(QColor(255, 255, 200, 230)))  # 淺黃色（懸停）
        painter.drawRoundedRect(tooltip_rect, 5, 5)
        
        # 繪製文字
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        current_y = tooltip_y + padding
        
        for i, line in enumerate(lines):
            painter.drawText(
                tooltip_x + padding,
                current_y + line_heights[i] - fm.descent(),
                line
            )
            current_y += line_heights[i]
    
    def _check_hover_point(self, mouse_pos: QPoint):
        """檢查滑鼠是否懸停在數據點上並顯示 Tooltip"""
        if not self.series_list or not self.chart_rect.isValid():
            self.setToolTip("")
            self.hover_point = None
            self.hover_screen_pos = None
            return
        
        # 搜索半徑（像素）- 增大到 20px 使更容易觸發
        search_radius = 20
        closest_point = None
        closest_distance = search_radius
        closest_series_name = ""
        closest_screen_pos = None
        
        # 遍歷所有數據系列和數據點
        for series in self.series_list:
            for data_point in series.data:
                # 座標轉換：數據座標 → 螢幕座標
                screen_x = self.chart_rect.left() + (data_point.x - self.x_range[0]) * self.chart_rect.width() / (self.x_range[1] - self.x_range[0])
                screen_y = self.chart_rect.bottom() - (data_point.y - self.y_range[0]) * self.chart_rect.height() / (self.y_range[1] - self.y_range[0])
                
                screen_point = QPoint(int(screen_x), int(screen_y))
                
                # 計算滑鼠與數據點的距離
                dx = mouse_pos.x() - screen_point.x()
                dy = mouse_pos.y() - screen_point.y()
                distance = (dx * dx + dy * dy) ** 0.5
                
                # 找到最近的點
                if distance < closest_distance:
                    closest_distance = distance
                    closest_point = data_point
                    closest_series_name = series.name
                    closest_screen_pos = screen_point
        
        # 如果找到懸停的點，顯示 Tooltip
        if closest_point:
            lap_number = int(closest_point.x)
            lap_time = closest_point.y
            
            # 格式化時間（秒 → 分:秒.毫秒）
            minutes = int(lap_time // 60)
            seconds = lap_time % 60
            
            if minutes > 0:
                time_str = f"{minutes}:{seconds:06.3f}"
            else:
                time_str = f"{seconds:.3f}s"
            
            # 顯示 Tooltip（同時使用 Qt 原生和自繪）
            tooltip_text = f"{closest_series_name} - Lap {lap_number}\nLap Time: {time_str}"
            self.setToolTip(tooltip_text)  # Qt 原生 Tooltip（備用）
            self.hover_point = closest_point
            self.hover_screen_pos = closest_screen_pos
            self.hover_tooltip_text = tooltip_text  # 自繪 Tooltip 文字
            print(f"[TOOLTIP] ✅ 顯示: {tooltip_text.replace(chr(10), ' | ')} | 距離: {closest_distance:.1f}px")
            self.update()  # 重繪以顯示高亮圓圈和 Tooltip
        else:
            self.setToolTip("")  # 清除 Tooltip
            if self.hover_point:  # 只有當之前有懸停點時才重繪
                self.hover_point = None
                self.hover_screen_pos = None
                self.hover_tooltip_text = ""
                self.update()  # 重繪以清除高亮圓圈和 Tooltip


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
        
        # 創建5個車手選擇下拉選單 - 響應式寬度
        for i in range(5):
            combo = QComboBox()
            combo.addItem(f"-- {tr('please_select', '請選擇')} --")
            combo.currentTextChanged.connect(self._on_driver_selection_changed)
            # 響應式寬度設定
            combo.setMinimumWidth(50)  # 小視窗下的最小寬度
            combo.setMaximumWidth(120)  # 大視窗下的最大寬度
            
            self.driver_combos.append(combo)
            driver_layout.addWidget(combo)
        
        # 響應式間距
        driver_layout.addSpacing(10)  # 減少間距適應小視窗
        
        # 控制按鈕 - 響應式寬度
        self.clear_button = QPushButton(tr('clear_button', 'Clear'))
        self.clear_button.clicked.connect(self._clear_selections)
        self.clear_button.setMaximumWidth(60)  # 縮小按鈕
        
        # 🆕 時間差顯示標籤（在 Clear 按鈕旁邊）
        self.time_diff_label = QLabel("")
        self.time_diff_label.setStyleSheet("QLabel { font-weight: bold; color: #0066cc; padding: 5px; }")
        self.time_diff_label.setMinimumWidth(150)
        
        # 匯出按鈕已移除 - 根據使用者要求
        # self.export_button = QPushButton(tr('export_button', 'Export'))
        # self.export_button.clicked.connect(self._export_chart)
        # self.export_button.setMaximumWidth(60)
        
        # driver_layout.addWidget(self.export_button)  # 已移除
        driver_layout.addWidget(self.clear_button)
        driver_layout.addWidget(self.time_diff_label)  # 🆕 添加時間差標籤
        driver_layout.addStretch()  # 推到左邊
        
        layout.addLayout(driver_layout)
        layout.addStretch()
    
    def set_chart_widget(self, chart_widget: 'LaptimeChartWidget'):
        """設置圖表組件並連接信號"""
        self.chart_widget = chart_widget
        # 🆕 連接圖表的固定 Tooltip 變化信號到時間差標籤更新
        self.chart_widget.pinned_tooltips_changed.connect(self._on_pinned_changed)
    
    def _on_pinned_changed(self, count: int, diff_text: str):
        """處理固定 Tooltip 變化事件"""
        self.time_diff_label.setText(diff_text)
        
    def update_available_drivers(self, drivers: List[str]):
        """更新可用車手列表"""
        print(f"[DRIVER_SELECTION] 🔄 更新車手列表: {drivers}")
        self.available_drivers = drivers
        
        # 暫停信號發射避免重複觸發
        for combo in self.driver_combos:
            combo.blockSignals(True)
        
        # 更新所有下拉選單
        for i, combo in enumerate(self.driver_combos):
            current_selection = combo.currentText()
            combo.clear()
            combo.addItem(f"-- {tr('please_select', '請選擇')} --")
            combo.addItems(drivers)
            
            # 恢復之前的選擇（如果仍然可用）
            if current_selection in drivers:
                combo.setCurrentText(current_selection)
        
        # 如果沒有預設選擇，自動選擇前3位車手
        placeholder = f"-- {tr('please_select', '請選擇')} --"
        if drivers and all(combo.currentText() == placeholder for combo in self.driver_combos):
            print(f"[DRIVER_SELECTION] 🎯 自動選擇前3位車手")
            for i, driver in enumerate(drivers[:3]):  # 自動選擇前3位車手
                if i < len(self.driver_combos):
                    self.driver_combos[i].setCurrentText(driver)
                    print(f"[DRIVER_SELECTION]   - 車手 {i+1}: {driver}")
        
        # 恢復信號發射
        for combo in self.driver_combos:
            combo.blockSignals(False)
        
        # 觸發一次選擇應用
        self._apply_selections()
        
        print(f"[DRIVER_SELECTION] ✅ 車手列表更新完成，總車手數: {len(drivers)}")
        print(f"[DRIVER_SELECTION] 當前選擇: {self.selected_drivers}")
                
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
        placeholder = f"-- {tr('please_select', '請選擇')} --"
        for combo in self.driver_combos:
            driver = combo.currentText()
            if driver != placeholder and driver not in selected:
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

        # 全域設定
        self.settings_manager = gui_settings_manager
        self.filter_pit_laps = True
        self.filter_yellow_flags = True
        self._apply_boxplot_settings(self.settings_manager.get_boxplot_settings())
        self.settings_manager.boxplot_settings_changed.connect(self._on_boxplot_settings_changed)
        
        # 設置UI
        self.setup_ui()
        
        print("[LAPTIME_CHART] 詳細圈速分析圖表組件初始化完成 (修正版架構)")
    
    def setup_ui(self):
        """設置主介面 - 垂直布局：車手選擇在上方，圖表在下方"""
        # 創建總佈局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 上方：車手選擇控制區 (響應式高度)
        self.driver_selection = DriverSelectionWidget()
        self.driver_selection.drivers_selected.connect(self._on_drivers_selected)
        self.driver_selection.setMaximumHeight(60)  # 減少高度適應小視窗
        self.driver_selection.setMinimumHeight(40)  # 設定最小高度
        
        # 下方：專用圖表組件
        self.chart_widget = LaptimeChartWidget()
        
        # 🆕 連接圖表組件到車手選擇器（用於時間差顯示）
        self.driver_selection.set_chart_widget(self.chart_widget)
        
        # 添加到主布局
        main_layout.addWidget(self.driver_selection)
        main_layout.addWidget(self.chart_widget)
        
        # 設置拉伸因子（車手選擇區 : 圖表區 = 0 : 1，圖表獲得所有額外空間）
        main_layout.setStretchFactor(self.driver_selection, 0)
        main_layout.setStretchFactor(self.chart_widget, 1)
        
        # 設置最小尺寸 - 與 Tire Analysis 一致
        self.setMinimumSize(200, 100)
    
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

                caution_laps = extract_caution_laps(driver_data)

                # 創建數據點列表
                data_points = []
                filtered_pit = 0
                filtered_caution = 0

                for lap_info in lap_data:
                    lap_num_raw = lap_info.get('lap_number', 0)
                    lap_num_normalized = normalize_lap_number(lap_num_raw)
                    lap_num_for_chart = lap_num_normalized if lap_num_normalized is not None else lap_num_raw
                    lap_time_sec = lap_info.get('lap_time_seconds', 0)

                    # 檢查數值有效性：不為 None 且大於 0
                    if lap_time_sec is None or lap_time_sec <= 0:
                        continue

                    if self.filter_yellow_flags and lap_is_under_caution(
                        lap_num_raw,
                        lap_info,
                        caution_laps,
                    ):
                        filtered_caution += 1
                        continue

                    if self.filter_pit_laps and lap_is_pit_stop(
                        lap_info,
                        driver_data.get('smart_markers_summary'),
                    ):
                        filtered_pit += 1
                        continue

                    # 提取智能標記
                    markers = self._extract_markers(driver_data, lap_info, caution_laps)

                    data_point = ChartDataPoint(
                        x=lap_num_for_chart,
                        y=lap_time_sec,
                        metadata={'markers': markers, 'driver': driver}
                    )
                    data_points.append(data_point)

                if filtered_pit or filtered_caution:
                    print(
                        f"[LAPTIME_CHART] {driver}: filtered {filtered_pit} pit laps, {filtered_caution} caution laps"
                    )

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
    
    def _extract_markers(
        self,
        driver_data: Dict,
        lap_info: Dict[str, Any],
        caution_laps: Optional[Set[int]] = None,
    ) -> List[str]:
        """提取指定圈數的智能標記"""
        markers: List[str] = []

        lap_num_raw = lap_info.get('lap_number', 0)
        lap_num = normalize_lap_number(lap_num_raw)
        lookup_value = lap_num if lap_num is not None else lap_num_raw

        smart_markers_summary = driver_data.get('smart_markers_summary', {})

        # 調試：只在第一圈顯示數據結構
        if lookup_value == 1:
            print(f"[LAPTIME_CHART_WIDGET] 智能標記數據結構:")
            print(f"[LAPTIME_CHART_WIDGET]   - driver_data 鍵: {list(driver_data.keys())}")
            print(f"[LAPTIME_CHART_WIDGET]   - smart_markers_summary 鍵: {list(smart_markers_summary.keys())}")

        def _contains_lap(collection: Any) -> bool:
            if not isinstance(collection, (list, tuple, set)):
                return False
            if lap_num is not None:
                return any(normalize_lap_number(val) == lap_num for val in collection)
            return lookup_value in collection

        # 進站檢測
        if lap_is_pit_stop(lap_info, smart_markers_summary):
            markers.append('P')

        # 輪胎更換檢測
        tire_data = smart_markers_summary.get('tire_change_detection', {})
        if _contains_lap(tire_data.get('tire_change_lap_numbers')):
            markers.append('T')

        # 最快圈檢測
        fastest_data = smart_markers_summary.get('fastest_lap_detection', {})
        if _contains_lap(fastest_data.get('fastest_lap_numbers')):
            markers.append('F')

        # 賽道狀況檢測
        if lap_is_under_caution(lap_num_raw, lap_info, caution_laps):
            markers.append('Y')

        # 降雨檢測 - 與降雨分析模組邏輯一致
        rain_data = smart_markers_summary.get('rain_detection', {})
        if _contains_lap(rain_data.get('rain_lap_numbers')):
            markers.append('W')

        if markers:
            print(f"[LAPTIME_CHART_WIDGET] 圈 {lookup_value} 找到標記: {markers}")

        return markers

    def _apply_boxplot_settings(self, settings: Dict[str, Any]) -> None:
        self.filter_pit_laps = settings.get('filter_pit_laps', True)
        self.filter_yellow_flags = settings.get('filter_yellow_flags', True)

    def _on_boxplot_settings_changed(self, settings: Dict[str, Any]) -> None:
        previous_filter = (
            self.filter_pit_laps,
            self.filter_yellow_flags,
        )
        self._apply_boxplot_settings(settings)

        current_filter = (
            self.filter_pit_laps,
            self.filter_yellow_flags,
        )

        if previous_filter != current_filter and self.chart_data:
            self._update_chart_data()

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
