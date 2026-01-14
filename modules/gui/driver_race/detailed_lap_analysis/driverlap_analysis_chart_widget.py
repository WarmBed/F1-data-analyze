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
from core.logger import get_logger
from .lap_filter_utils import (
    extract_caution_laps,
    lap_is_under_caution,
    lap_is_pit_stop,
    normalize_lap_number,
)

# 跨模組同步信號
from modules.gui.base.global_chart_sync_signal import GlobalChartSyncSignal

# 統一顏色系統
from modules.gui.themes.color_palette_provider import color_palette_provider

logger = get_logger(__name__)

# 模組標識常量
MODULE_DETAILED_LAP = GlobalChartSyncSignal.MODULE_DETAILED_LAP

# 未選中車手的灰色
GRAY_COLOR = QColor(180, 180, 180)


class ChartTheme:
    """圖表主題配置 - 現在使用 color_palette_provider 獲取車手顏色"""
    # 舊的靜態顏色（向後兼容）
    DRIVER1_COLOR = QColor(220, 53, 69)    # 紅色
    DRIVER2_COLOR = QColor(0, 123, 255)    # 藍色
    DRIVER3_COLOR = QColor(40, 167, 69)    # 綠色
    DRIVER4_COLOR = QColor(255, 193, 7)    # 黃色
    DRIVER5_COLOR = QColor(108, 117, 125)  # 灰色
    
    BACKGROUND = QColor(255, 255, 255)
    GRID_COLOR = QColor(200, 200, 200)
    TEXT_COLOR = QColor(0, 0, 0)
    
    @staticmethod
    def get_driver_color(driver_code: str, selected_drivers: list = None) -> QColor:
        """
        獲取車手顏色
        
        Args:
            driver_code: 車手代碼 (VER, HAM, etc.)
            selected_drivers: 被選中的車手列表。如果為空，則所有車手都顯示顏色。
                             如果提供，只有在列表中的車手顯示顏色，其他顯示灰色。
        
        Returns:
            QColor: 車手顏色（使用 color_palette_provider）或灰色
        """
        if not driver_code:
            return GRAY_COLOR
        
        code = str(driver_code).strip().upper()
        
        # 如果有選中列表且車手不在其中，返回灰色
        if selected_drivers is not None:
            selected_upper = [d.upper() for d in selected_drivers if d]
            if code not in selected_upper:
                return GRAY_COLOR
        
        # 使用 color_palette_provider 獲取顏色
        qcolor = color_palette_provider.get_driver_color(code, format="qcolor")
        if qcolor and isinstance(qcolor, QColor) and qcolor.isValid():
            return qcolor
        
        # 如果獲取失敗，使用默認灰色
        return GRAY_COLOR


class ChartDataPoint:
    """圖表數據點"""
    def __init__(self, x, y, metadata=None):
        self.x = x
        self.y = y
        self.metadata = metadata or {}


class ChartSeries:
    """圖表數據系列"""
    def __init__(self, name, data, color, line_width=2, style='line', line_style=None, marker_only_points=None):
        self.name = name
        self.data = data
        self.color = color
        self.line_width = line_width
        self.style = style
        self.line_style = line_style  # Qt.SolidLine, Qt.DashLine, etc.
        self.marker_only_points = marker_only_points or []  # 被過濾但仍需繪製標記的點


class LaptimeChartWidget(QWidget):
    """專用的圈速圖表繪製組件"""
    
    # 🆕 信號定義
    pinned_tooltips_changed = pyqtSignal(int, str)  # (固定數量, 時間差文字)
    zoom_changed = pyqtSignal(bool)  # True=已縮放, False=全視圖
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.series_list = []
        self.setMinimumSize(200, 100)  # 調整為與 Tire Analysis 一致的最小尺寸
        # 移除固定的白色背景，讓paint事件處理背景色
        self.setStyleSheet("border: 1px solid #ccc;")
        
        # 🆕 縮放功能變數
        self.zoom_rect_start = None  # 右鍵框選起始點
        self.zoom_rect_end = None    # 右鍵框選結束點
        self.is_zooming = False      # 是否正在框選
        self.zoom_x_range = None     # 自定義 X 軸範圍 (縮放後)
        self.zoom_y_range = None     # 自定義 Y 軸範圍 (縮放後)
        self.is_zoomed = False       # 是否已縮放
        
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
        
        # 🆕 固定 Tooltip 功能（左鍵點擊固定，無限制）
        self.pinned_tooltips = []  # 固定的 Tooltip 列表 [{point, screen_pos, text, lap_time, tooltip_rect, custom_pos, driver_color}, ...]
        self.max_pinned = 999  # 無限制（原本為 2）
        
        # 🆕 左鍵框選功能
        self.selection_rect_start = None  # 框選起始點
        self.selection_rect_end = None  # 框選結束點
        self.is_selecting = False  # 是否正在框選
        
        # 🆕 Tooltip 拖動功能
        self.dragging_tooltip = False  # 是否正在拖動 tooltip
        self.dragging_tooltip_index = -1  # 正在拖動的 tooltip 索引
        self.tooltip_drag_offset = QPoint(0, 0)  # tooltip 拖動偏移量
        
        # 🚀 性能優化：防抖機制
        self._last_hover_point = None  # 記錄上次懸停點，避免重複重繪
        self._hover_check_counter = 0  # 計數器：每N次mouseMoveEvent才檢查懸停
        self._hover_check_interval = 3  # 間隔設定（每3次滑鼠移動才檢查一次）
        
        logger.debug("[LAPTIME_CHART_WIDGET] 專用圖表組件初始化完成")
    
    def update_series_data(self, series_list: List[ChartSeries]):
        """更新圖表數據系列"""
        self.series_list = series_list
        logger.debug(f"[LAPTIME_CHART_WIDGET] 更新數據系列，系列數: {len(series_list)}")
        for series in series_list:
            logger.debug(f"[LAPTIME_CHART_WIDGET] - {series.name}: {len(series.data)} 數據點")
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
            
            # 🆕 繪製縮放選擇框（右鍵拖動時）
            if self.is_zooming and self.zoom_rect_start and self.zoom_rect_end:
                zoom_rect = QRect(self.zoom_rect_start, self.zoom_rect_end).normalized()
                # 半透明藍色填充
                painter.setBrush(QBrush(QColor(100, 150, 255, 50)))
                painter.setPen(QPen(QColor(50, 100, 200), 2, Qt.DashLine))
                painter.drawRect(zoom_rect)
            
            # 🆕 繪製選取框（左鍵拖動時）
            if self.is_selecting and self.selection_rect_start and self.selection_rect_end:
                selection_rect = QRect(self.selection_rect_start, self.selection_rect_end).normalized()
                # 半透明綠色填充（與縮放框區分）
                painter.setBrush(QBrush(QColor(100, 255, 150, 50)))
                painter.setPen(QPen(QColor(50, 200, 100), 2, Qt.DashLine))
                painter.drawRect(selection_rect)
            
            # 繪製圖例 (重疊模式，右上角覆蓋)
            self._draw_legend(painter)
            
            # 繪製固定的 Tooltip（使用車手顏色邊框和輪胎 highlight，支援拖動）
            for i, pinned in enumerate(self.pinned_tooltips):
                # 繪製固定的 Tooltip（根據車手顏色和輪胎顏色，支援 custom_pos）
                tire = pinned.get('tire_compound')
                custom_pos = pinned.get('custom_pos')
                driver_color = pinned.get('driver_color')
                tooltip_rect = self._draw_custom_tooltip(
                    painter, 
                    pinned['screen_pos'], 
                    pinned['text'], 
                    is_pinned=True, 
                    tire_compound=tire,
                    custom_pos=custom_pos,
                    driver_color=driver_color
                )
                # 更新 tooltip_rect 供拖動檢測使用
                if tooltip_rect:
                    self.pinned_tooltips[i]['tooltip_rect'] = tooltip_rect
            
            # 繪製懸停 Tooltip（根據車手顏色和輪胎顏色，最後繪製確保在最上層）
            if self.hover_tooltip_text and self.hover_screen_pos:
                hover_tire = self.hover_point.metadata.get('tire_compound') if self.hover_point else None
                hover_driver_color = None
                if self.hover_point and hasattr(self.hover_point, 'metadata'):
                    driver_code = self.hover_point.metadata.get('driver_code') or self.hover_point.metadata.get('driver')
                    if driver_code:
                        # 確保顏色數據已載入
                        color_palette_provider.ensure_loaded()
                        hover_driver_color = color_palette_provider.get_driver_color(driver_code, format="qcolor")
                self._draw_custom_tooltip(painter, self.hover_screen_pos, self.hover_tooltip_text, is_pinned=False, tire_compound=hover_tire, driver_color=hover_driver_color)
            
        except Exception as e:
            logger.debug(f"[LAPTIME_CHART_WIDGET] 繪製錯誤: {e}")
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
        """計算數據範圍（優先使用縮放範圍）"""
        # 🆕 如果已縮放，返回縮放範圍
        if self.is_zoomed and self.zoom_x_range and self.zoom_y_range:
            return self.zoom_x_range[0], self.zoom_x_range[1], self.zoom_y_range[0], self.zoom_y_range[1]
        
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
            
            # 使用 line_style 參數，預設為實線
            pen = QPen(series.color, series.line_width)
            if series.line_style is not None:
                pen.setStyle(series.line_style)
            painter.setPen(pen)
            
            prev_point = None
            for data_point in series.data:
                # 座標轉換
                screen_x = rect.left() + (data_point.x - x_range[0]) * rect.width() / (x_range[1] - x_range[0])
                screen_y = rect.bottom() - (data_point.y - y_range[0]) * rect.height() / (y_range[1] - y_range[0])
                
                current_point = QPoint(int(screen_x), int(screen_y))
                
                # 繪製數據點（已禁用 - 用戶要求不顯示圓點）
                # painter.drawEllipse(current_point, 3, 3)
                
                # 繪製連接線
                if prev_point:
                    painter.drawLine(prev_point, current_point)
                
                prev_point = current_point
    
    def _draw_smart_markers(self, painter: QPainter, rect: QRect, x_range: Tuple[float, float], y_range: Tuple[float, float]):
        """繪製智能標記 - 使用垂直虛線顯示"""
        # 防護檢查：確保 series_list 已初始化且不為空
        if not hasattr(self, 'series_list') or not self.series_list:
            return
            
        for series in self.series_list:
            # 繪製普通數據點的標記
            for data_point in series.data:
                markers = data_point.metadata.get('markers', [])
                
                if not markers:
                    continue
                
                # 座標轉換 - 只需要 X 座標
                screen_x = rect.left() + (data_point.x - x_range[0]) * rect.width() / (x_range[1] - x_range[0])
                
                # 繪製垂直虛線和標記文字
                for i, marker_type in enumerate(markers):
                    color = self.marker_colors.get(marker_type, QColor(128, 128, 128))
                    self._draw_vertical_marker_line(painter, rect, int(screen_x), marker_type, color, i)
            
            # 繪製被過濾但保留標記的點（如 Pit 圈垂直線）
            if hasattr(series, 'marker_only_points') and series.marker_only_points:
                for data_point in series.marker_only_points:
                    markers = data_point.metadata.get('markers', [])
                    
                    if not markers:
                        continue
                    
                    # 座標轉換 - 只需要 X 座標
                    screen_x = rect.left() + (data_point.x - x_range[0]) * rect.width() / (x_range[1] - x_range[0])
                    
                    # 繪製垂直虛線和標記文字
                    for i, marker_type in enumerate(markers):
                        color = self.marker_colors.get(marker_type, QColor(128, 128, 128))
                        self._draw_vertical_marker_line(painter, rect, int(screen_x), marker_type, color, i)
    
    def _draw_vertical_marker_line(self, painter: QPainter, rect: QRect, screen_x: int, marker_type: str, color: QColor, offset_index: int = 0):
        """繪製垂直虛線標記 - PIT STOP, FASTEST LAP 等"""
        # 繪製垂直虛線（從圖表頂部到底部）
        pen = QPen(color, 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(screen_x, rect.top(), screen_x, rect.bottom())
        
        # 在頂部繪製標記文字
        painter.setPen(QPen(color, 2))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        # 計算文字位置（頂部，避免重疊）
        text_y = rect.top() - 5 - offset_index * 15
        text_x = screen_x - 6
        
        painter.drawText(text_x, text_y, marker_type)
    
    def _draw_marker(self, painter: QPainter, position: QPoint, marker_type: str, color: QColor):
        """繪製單個標記 - 純文字版本，支援組合標記"""
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
        """繪製圖例 - 重疊模式，右上角覆蓋，強制白色背景 [VERSION 3.2 - 性能優化]"""
        if not self.series_list:
            return
        
        # 計算圖例尺寸和位置
        driver_count = len(self.series_list)
        marker_count = 5 if self.legend_show_markers else 0  # 隱藏時不計算標記
        
        # 內容尺寸計算 - 根據顯示模式調整
        content_width = 140
        header_height = 22
        driver_height = driver_count * 20
        marker_height = marker_count * 22 if self.legend_show_markers else 0
        padding = 20 if self.legend_show_markers else 10
        separator_height = 12 if self.legend_show_markers else 0
        content_height = header_height + driver_height + separator_height + marker_height + padding
        
        # 位置：右上角，小幅偏移 + 用戶拖移的偏移量
        legend_x = self.width() - content_width - 15 + self.legend_offset.x()
        legend_y = 15 + self.legend_offset.y()
        
        # 保存圖例矩形區域供滑鼠事件使用
        self.legend_rect = QRect(legend_x, legend_y, content_width, content_height)
        
        # 白色背景 - 優化：只填充一次
        white_color = QColor(255, 255, 255, 255)
        painter.fillRect(legend_x - 5, legend_y - 5, content_width + 10, content_height + 10, white_color)
        
        # 黑色邊框
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.drawRect(legend_x, legend_y, content_width, content_height)
        
        # 內容繪製區域
        content_x = legend_x + 10
        current_y = legend_y + 15
        
        # 車手圖例標題
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        title_font = QFont()
        title_font.setPointSize(8)
        painter.setFont(title_font)
        painter.drawText(content_x, current_y, "Drivers")
        current_y += 22
        
        # 響應式字體和尺寸設定
        widget_size = min(self.width(), self.height())
        square_size = max(10, min(16, int(widget_size * 0.035)))
        line_spacing = max(16, min(24, int(square_size * 1.4)))
        
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
            current_y += 4
            painter.setPen(QPen(QColor(160, 160, 160), 1))
            painter.drawLine(content_x, current_y, content_x + content_width - 20, current_y)
            current_y += 8
            
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
                self._draw_legend_marker_improved(painter, marker_pos, marker_type, color)
                
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
    
    # 🆕 滑鼠事件處理 - 圖例拖移功能、顯示切換和縮放功能
    def wheelEvent(self, event):
        """滾輪縮放 - 以滑鼠位置為中心進行縮放"""
        if not self.chart_rect.contains(event.pos()):
            super().wheelEvent(event)
            return
        
        # 獲取滾動方向
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return
        
        # 縮放因子
        zoom_factor = 1.15 if delta > 0 else 0.87  # 放大或縮小
        
        # 獲取當前數據範圍
        if self.is_zoomed and self.zoom_x_range and self.zoom_y_range:
            current_x_min, current_x_max = self.zoom_x_range
            current_y_min, current_y_max = self.zoom_y_range
        else:
            x_values = []
            y_values = []
            for series in self.series_list:
                for point in series.data:
                    x_values.append(point.x)
                    y_values.append(point.y)
            if not x_values or not y_values:
                return
            x_margin = max((max(x_values) - min(x_values)) * 0.05, 1)
            y_margin = max((max(y_values) - min(y_values)) * 0.05, 0.1)
            current_x_min = min(x_values) - x_margin
            current_x_max = max(x_values) + x_margin
            current_y_min = min(y_values) - y_margin
            current_y_max = max(y_values) + y_margin
        
        # 計算滑鼠位置對應的數據座標（作為縮放中心）
        mouse_x = event.pos().x()
        mouse_y = event.pos().y()
        
        # 轉換為數據座標
        data_x = current_x_min + (mouse_x - self.chart_rect.left()) * (current_x_max - current_x_min) / self.chart_rect.width()
        data_y = current_y_max - (mouse_y - self.chart_rect.top()) * (current_y_max - current_y_min) / self.chart_rect.height()
        
        # 計算新的範圍（以滑鼠位置為中心縮放）
        new_x_range = (current_x_max - current_x_min) / zoom_factor
        new_y_range = (current_y_max - current_y_min) / zoom_factor
        
        # 保持滑鼠位置在相同的數據點上
        x_ratio = (data_x - current_x_min) / (current_x_max - current_x_min)
        y_ratio = (data_y - current_y_min) / (current_y_max - current_y_min)
        
        new_x_min = data_x - x_ratio * new_x_range
        new_x_max = data_x + (1 - x_ratio) * new_x_range
        new_y_min = data_y - y_ratio * new_y_range
        new_y_max = data_y + (1 - y_ratio) * new_y_range
        
        # 確保範圍有效
        if new_x_min >= new_x_max or new_y_min >= new_y_max:
            return
        
        # 應用縮放
        self.zoom_x_range = (new_x_min, new_x_max)
        self.zoom_y_range = (new_y_min, new_y_max)
        self.is_zoomed = True
        
        # 發射信號通知父組件
        self.zoom_changed.emit(True)
        
        # 重繪圖表
        self.update()
        event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """雙擊圖例切換顯示/隱藏標記，雙擊圖表重置縮放"""
        if event.button() == Qt.LeftButton:
            if self.legend_rect.contains(event.pos()):
                self.legend_show_markers = not self.legend_show_markers
                logger.debug(f"[LEGEND] 切換標記顯示狀態: {self.legend_show_markers}")
                self.update()  # 重繪圖表
                event.accept()
                return
            # 🆕 雙擊圖表區域重置縮放
            elif self.chart_rect.contains(event.pos()) and self.is_zoomed:
                self.reset_zoom()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 檢查是否點擊圖例 / 固定 Tooltip / 拖動 Tooltip / 開始縮放框選 / 開始左鍵選取"""
        if event.button() == Qt.LeftButton:
            # 優先處理圖例拖移
            if self.legend_rect.contains(event.pos()):
                self.legend_dragging = True
                self.legend_drag_start = event.pos() - self.legend_offset
                self.setCursor(Qt.ClosedHandCursor)  # 改變游標為抓取狀
                event.accept()
                return
            
            # 🆕 【最優先】檢查是否點擊已固定的 tooltip 框（用於拖動）
            for i, pinned in enumerate(self.pinned_tooltips):
                tooltip_rect = pinned.get('tooltip_rect')
                if tooltip_rect and tooltip_rect.contains(event.pos()):
                    # 開始拖動此 tooltip
                    self.dragging_tooltip = True
                    self.dragging_tooltip_index = i
                    self.tooltip_drag_offset = event.pos() - QPoint(tooltip_rect.x(), tooltip_rect.y())
                    self.setCursor(Qt.ClosedHandCursor)
                    logger.debug(f"[TOOLTIP] 開始拖動 Tooltip #{i}")
                    event.accept()
                    return
            
            # 左鍵點擊數據點固定 Tooltip
            if self.hover_point and self.hover_screen_pos:
                self._pin_tooltip()
                event.accept()
                return
            
            # 🆕 左鍵在空白處開始拖曳選取（不是清除 tooltip）
            if self.chart_rect.contains(event.pos()):
                self.is_selecting = True
                self.selection_rect_start = event.pos()
                self.selection_rect_end = event.pos()
                self.setCursor(Qt.CrossCursor)
                logger.debug(f"[SELECTION] 開始拖曳選取: {event.pos()}")
                event.accept()
                return
        
        elif event.button() == Qt.RightButton:
            # 🆕 右鍵開始縮放框選（在圖表區域內）
            if self.chart_rect.contains(event.pos()):
                self.is_zooming = True
                self.zoom_rect_start = event.pos()
                self.zoom_rect_end = event.pos()
                self.setCursor(Qt.CrossCursor)
                logger.debug(f"[ZOOM] 開始框選縮放: {event.pos()}")
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 拖移圖例 + 拖動 Tooltip + 顯示數據點 Tooltip + 縮放框選 + 選取框"""
        # 🆕 處理 Tooltip 拖動
        if self.dragging_tooltip and 0 <= self.dragging_tooltip_index < len(self.pinned_tooltips):
            new_pos = event.pos() - self.tooltip_drag_offset
            self.pinned_tooltips[self.dragging_tooltip_index]['custom_pos'] = new_pos
            self.update()
            event.accept()
            return
        
        # 🆕 處理縮放框選
        if self.is_zooming:
            self.zoom_rect_end = event.pos()
            self.update()  # 重繪以顯示選擇框
            event.accept()
            return
        
        # 🆕 處理左鍵拖曳選取
        if self.is_selecting:
            self.selection_rect_end = event.pos()
            self.update()  # 重繪以顯示選取框
            event.accept()
            return
        
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
            # 🆕 檢查是否懸停在固定的 tooltip 上
            hovering_tooltip = False
            for pinned in self.pinned_tooltips:
                tooltip_rect = pinned.get('tooltip_rect')
                if tooltip_rect and tooltip_rect.contains(event.pos()):
                    self.setCursor(Qt.OpenHandCursor)
                    hovering_tooltip = True
                    break
            
            if not hovering_tooltip:
                self.setCursor(Qt.ArrowCursor)
                # 🆕 檢查是否懸停在數據點上（使用防抖）
                self._hover_check_counter += 1
                if self._hover_check_counter >= self._hover_check_interval:
                    self._hover_check_counter = 0
                    self._check_hover_point(event.pos())
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖移 / 結束 Tooltip 拖動 / 完成縮放框選 / 完成選取框"""
        # 🆕 處理 Tooltip 拖動結束
        if event.button() == Qt.LeftButton and self.dragging_tooltip:
            self.dragging_tooltip = False
            self.dragging_tooltip_index = -1
            self.setCursor(Qt.ArrowCursor)
            logger.debug("[TOOLTIP] 結束拖動 Tooltip")
            event.accept()
            return
        
        # 🆕 處理左鍵拖曳選取完成
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.setCursor(Qt.ArrowCursor)
            
            # 計算選取框內的數據點並自動固定
            if self.selection_rect_start and self.selection_rect_end:
                self._apply_selection_from_rect()
            
            self.selection_rect_start = None
            self.selection_rect_end = None
            event.accept()
            return
        
        # 🆕 處理縮放框選完成
        if event.button() == Qt.RightButton and self.is_zooming:
            self.is_zooming = False
            self.setCursor(Qt.ArrowCursor)
            
            # 計算選擇框的範圍並應用縮放
            if self.zoom_rect_start and self.zoom_rect_end:
                self._apply_zoom_from_rect()
            
            self.zoom_rect_start = None
            self.zoom_rect_end = None
            event.accept()
            return
        
        if event.button() == Qt.LeftButton and self.legend_dragging:
            self.legend_dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
    
    def _apply_zoom_from_rect(self):
        """根據選擇框應用縮放"""
        if not self.zoom_rect_start or not self.zoom_rect_end:
            return
        
        # 計算選擇框的歸一化矩形
        rect = QRect(self.zoom_rect_start, self.zoom_rect_end).normalized()
        
        # 確保選擇框有最小尺寸（避免誤觸）
        if rect.width() < 20 or rect.height() < 20:
            logger.debug("[ZOOM] 選擇框太小，忽略縮放")
            return
        
        # 確保選擇框在圖表區域內
        if not self.chart_rect.isValid():
            return
        
        # 將螢幕座標轉換為數據座標
        # 計算原始數據範圍（不使用縮放範圍）
        x_values = []
        y_values = []
        for series in self.series_list:
            for point in series.data:
                x_values.append(point.x)
                y_values.append(point.y)
        
        if not x_values or not y_values:
            return
        
        # 如果已縮放，使用當前縮放範圍；否則使用原始數據範圍
        if self.is_zoomed and self.zoom_x_range and self.zoom_y_range:
            current_x_min, current_x_max = self.zoom_x_range
            current_y_min, current_y_max = self.zoom_y_range
        else:
            x_margin = max((max(x_values) - min(x_values)) * 0.05, 1)
            y_margin = max((max(y_values) - min(y_values)) * 0.05, 0.1)
            current_x_min = min(x_values) - x_margin
            current_x_max = max(x_values) + x_margin
            current_y_min = min(y_values) - y_margin
            current_y_max = max(y_values) + y_margin
        
        # 螢幕座標轉數據座標
        chart_left = self.chart_rect.left()
        chart_right = self.chart_rect.right()
        chart_top = self.chart_rect.top()
        chart_bottom = self.chart_rect.bottom()
        
        # X 座標轉換
        new_x_min = current_x_min + (rect.left() - chart_left) * (current_x_max - current_x_min) / (chart_right - chart_left)
        new_x_max = current_x_min + (rect.right() - chart_left) * (current_x_max - current_x_min) / (chart_right - chart_left)
        
        # Y 座標轉換（注意 Y 軸方向相反）
        new_y_max = current_y_max - (rect.top() - chart_top) * (current_y_max - current_y_min) / (chart_bottom - chart_top)
        new_y_min = current_y_max - (rect.bottom() - chart_top) * (current_y_max - current_y_min) / (chart_bottom - chart_top)
        
        # 確保範圍有效
        if new_x_min >= new_x_max or new_y_min >= new_y_max:
            logger.debug("[ZOOM] 無效的縮放範圍")
            return
        
        # 應用縮放
        self.zoom_x_range = (new_x_min, new_x_max)
        self.zoom_y_range = (new_y_min, new_y_max)
        self.is_zoomed = True
        
        logger.debug(f"[ZOOM] 應用縮放: X=({new_x_min:.1f}, {new_x_max:.1f}), Y=({new_y_min:.1f}, {new_y_max:.1f})")
        
        # 發射信號通知父組件
        self.zoom_changed.emit(True)
        
        # 重繪圖表
        self.update()
    
    def _apply_selection_from_rect(self):
        """根據選取框自動固定所有選中的數據點"""
        if not self.selection_rect_start or not self.selection_rect_end:
            return
        
        # 計算選取框的歸一化矩形
        rect = QRect(self.selection_rect_start, self.selection_rect_end).normalized()
        
        # 確保選取框有最小尺寸（避免誤觸）
        if rect.width() < 10 and rect.height() < 10:
            logger.debug("[SELECTION] 選取框太小，忽略選取")
            return
        
        if not self.chart_rect.isValid() or not self.series_list:
            return
        
        # 收集選取框內的所有數據點
        selected_points = []
        
        for series in self.series_list:
            for point in series.data:
                # 計算數據點的螢幕座標
                screen_pos = self._data_to_screen(point.x, point.y)
                if screen_pos and rect.contains(screen_pos):
                    # 取得車手顏色
                    driver_color = None
                    driver_code = (point.metadata.get('driver_code') or point.metadata.get('driver')) if hasattr(point, 'metadata') else None
                    if driver_code:
                        driver_color = color_palette_provider.get_driver_color(driver_code, format="qcolor")
                    
                    selected_points.append({
                        'point': point,
                        'screen_pos': screen_pos,
                        'series': series,
                        'driver_color': driver_color
                    })
        
        if not selected_points:
            logger.debug("[SELECTION] 選取框內沒有數據點")
            return
        
        logger.debug(f"[SELECTION] 選中 {len(selected_points)} 個數據點")
        
        # 清除現有的固定 tooltip（可選，或者追加）
        # self._clear_all_pinned_tooltips()  # 如果想追加而不是替換，註釋此行
        
        # 自動固定所有選中的數據點並自動排列
        self._pin_multiple_tooltips_with_arrangement(selected_points)
        
        self.update()
    
    def _pin_multiple_tooltips_with_arrangement(self, selected_points: list):
        """固定多個 tooltip 並自動排列避免重疊"""
        if not selected_points:
            return
        
        # 計算 tooltip 的預設尺寸
        tooltip_width = 150
        tooltip_height = 60
        spacing = 10
        
        # 計算起始排列位置（圖表右側）
        start_x = self.chart_rect.right() - tooltip_width - 20
        start_y = self.chart_rect.top() + 20
        
        # 追蹤已佔用的位置
        used_rects = []
        
        for i, sel in enumerate(selected_points):
            point = sel['point']
            screen_pos = sel['screen_pos']
            driver_color = sel['driver_color']
            
            # 檢查是否已經固定過這個點
            already_pinned = False
            for pinned in self.pinned_tooltips:
                if pinned['point'] == point:
                    already_pinned = True
                    break
            
            if already_pinned:
                continue
            
            # 建立 tooltip 文字
            lap_num = int(point.x)
            lap_time_seconds = point.y
            lap_time_str = self._format_lap_time_from_seconds(lap_time_seconds)
            tire = point.metadata.get('tire_compound', '') if hasattr(point, 'metadata') else ''
            driver = point.metadata.get('driver_code', '') if hasattr(point, 'metadata') else ''
            
            tooltip_text = f"Lap {lap_num}\n{driver}: {lap_time_str}"
            if tire:
                tooltip_text += f"\n{tire}"
            
            # 計算自動排列位置
            pos_x = start_x
            pos_y = start_y + (len(self.pinned_tooltips) % 10) * (tooltip_height + spacing)
            
            # 如果超出圖表底部，換到左側
            if pos_y + tooltip_height > self.chart_rect.bottom():
                pos_x = self.chart_rect.left() + 20
                pos_y = start_y + ((len(self.pinned_tooltips) % 10) - 5) * (tooltip_height + spacing)
            
            custom_pos = QPoint(pos_x, pos_y)
            
            # 建立 pinned 數據
            pinned_data = {
                'point': point,
                'screen_pos': screen_pos,
                'text': tooltip_text,
                'lap_time': lap_time_seconds,
                'tire_compound': tire,
                'driver_color': driver_color,
                'custom_pos': custom_pos,
                'tooltip_rect': None
            }
            
            self.pinned_tooltips.append(pinned_data)
            logger.debug(f"[SELECTION] 自動固定 Tooltip: Lap {lap_num}, {driver}")
        
        # 發射信號通知父容器
        pinned_count = len(self.pinned_tooltips)
        time_diff_text = ""
        if pinned_count == 2:
            time_diff = self.get_pinned_time_diff()
            if time_diff:
                time_diff_text = f"Diff: {time_diff}"
        
        self.pinned_tooltips_changed.emit(pinned_count, time_diff_text)
    
    def _data_to_screen(self, data_x: float, data_y: float) -> QPoint:
        """將數據座標轉換為螢幕座標"""
        if not self.chart_rect.isValid():
            return None
        
        # 取得當前顯示範圍
        x_values = []
        y_values = []
        for series in self.series_list:
            for point in series.data:
                x_values.append(point.x)
                y_values.append(point.y)
        
        if not x_values or not y_values:
            return None
        
        # 使用縮放範圍或原始範圍
        if self.is_zoomed and self.zoom_x_range and self.zoom_y_range:
            x_min, x_max = self.zoom_x_range
            y_min, y_max = self.zoom_y_range
        else:
            x_margin = max((max(x_values) - min(x_values)) * 0.05, 1)
            y_margin = max((max(y_values) - min(y_values)) * 0.05, 0.1)
            x_min = min(x_values) - x_margin
            x_max = max(x_values) + x_margin
            y_min = min(y_values) - y_margin
            y_max = max(y_values) + y_margin
        
        # 座標轉換
        x_range = x_max - x_min
        y_range = y_max - y_min
        
        if x_range <= 0 or y_range <= 0:
            return None
        
        screen_x = self.chart_rect.left() + (data_x - x_min) * self.chart_rect.width() / x_range
        screen_y = self.chart_rect.bottom() - (data_y - y_min) * self.chart_rect.height() / y_range
        
        return QPoint(int(screen_x), int(screen_y))

    def _format_lap_time_from_seconds(self, seconds: float) -> str:
        """將秒數轉換為圈速格式 (M:SS.sss)"""
        if seconds is None or math.isnan(seconds):
            return "--:--.---"
        
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:06.3f}"

    def reset_zoom(self):
        """重置縮放，顯示全部數據"""
        if not self.is_zoomed:
            return
        
        self.zoom_x_range = None
        self.zoom_y_range = None
        self.is_zoomed = False
        
        logger.debug("[ZOOM] 重置縮放，顯示全部數據")
        
        # 發射信號通知父組件
        self.zoom_changed.emit(False)
        
        # 重繪圖表
        self.update()
    
    def _pin_tooltip(self):
        """固定當前懸停的 Tooltip（最多2個）"""
        if not self.hover_point or not self.hover_screen_pos:
            return
        
        # 檢查是否已經固定過這個點
        for pinned in self.pinned_tooltips:
            if pinned['point'] == self.hover_point:
                logger.warning("[TOOLTIP] ⚠️ 此點已固定")
                return
        
        # 如果已達到最大固定數量，移除最舊的
        if len(self.pinned_tooltips) >= self.max_pinned:
            removed = self.pinned_tooltips.pop(0)
            logger.debug(f"[TOOLTIP] 移除最舊的固定點")
        
        # 提取圈速時間（用於計算時間差）
        lap_time = self.hover_point.y  # 假設 y 值就是圈速秒數
        
        # 提取輪胎類型
        tire_compound = self.hover_point.metadata.get('tire_compound') if self.hover_point else None
        
        # 取得車手顏色（從 driver_code 或 driver 轉換）
        driver_color = None
        if self.hover_point and hasattr(self.hover_point, 'metadata'):
            # 支援 driver_code 和 driver 兩種 key
            driver_code = self.hover_point.metadata.get('driver_code') or self.hover_point.metadata.get('driver')
            logger.info(f"[TOOLTIP_COLOR] driver_code from metadata: {driver_code}")
            logger.info(f"[TOOLTIP_COLOR] metadata keys: {list(self.hover_point.metadata.keys())}")
            if driver_code:
                # 確保顏色數據已載入
                color_palette_provider.ensure_loaded()
                driver_color = color_palette_provider.get_driver_color(driver_code, format="qcolor")
                if driver_color:
                    logger.info(f"[TOOLTIP_COLOR] driver_color for {driver_code}: RGB({driver_color.red()}, {driver_color.green()}, {driver_color.blue()}), valid: {driver_color.isValid()}")
                else:
                    logger.info(f"[TOOLTIP_COLOR] driver_color is None for {driver_code}")
        
        # 固定新的 Tooltip
        pinned_data = {
            'point': self.hover_point,
            'screen_pos': QPoint(self.hover_screen_pos),
            'text': self.hover_tooltip_text,
            'lap_time': lap_time,
            'tire_compound': tire_compound,
            'driver_color': driver_color,
            'custom_pos': None,
            'tooltip_rect': None
        }
        self.pinned_tooltips.append(pinned_data)
        logger.debug(f"[TOOLTIP] 已固定 Tooltip ({len(self.pinned_tooltips)}/{self.max_pinned})")
        
        # 更新時間差顯示
        self._update_time_diff_display()
        
        self.update()
    
    def _clear_all_pinned_tooltips(self):
        """清除所有固定的 Tooltip"""
        if self.pinned_tooltips:
            self.pinned_tooltips.clear()
            logger.debug("[TOOLTIP] 已清除所有固定的 Tooltip")
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
                logger.debug(f"[TOOLTIP] ⏱️ 時間差: {time_diff}")
        
        # 發射信號通知父容器
        self.pinned_tooltips_changed.emit(pinned_count, time_diff_text)
    
    def _draw_custom_tooltip(self, painter: QPainter, anchor_pos: QPoint, text: str, is_pinned: bool = False, tire_compound: str = None, custom_pos: QPoint = None, driver_color: QColor = None) -> QRect:
        """繪製自訂 Tooltip（直接在圖表上繪製）- 支援車手顏色邊框、輪胎顏色 highlight 和拖動
        
        Returns:
            QRect: tooltip 的矩形區域（供拖動檢測使用）
        """
        # 分割多行文字
        lines = text.split('\n')
        
        # 計算 Tooltip 尺寸 - 不使用粗體
        font = QFont()
        font.setPointSize(10)
        font.setBold(False)  # 不使用粗體
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
        
        # 🆕 如果有 custom_pos（拖動後的位置），使用它
        if custom_pos is not None:
            tooltip_x = custom_pos.x()
            tooltip_y = custom_pos.y()
        else:
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
        
        # 建立 tooltip 矩形
        tooltip_rect = QRect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        # 🆕 繪製從錨點到 tooltip 的虛線連接
        tooltip_center_x = tooltip_x + tooltip_width // 2
        tooltip_center_y = tooltip_y + tooltip_height // 2
        
        # 確定連接點（tooltip 邊緣最近點）
        if tooltip_x > anchor_pos.x():
            connect_x = tooltip_x  # 連接到 tooltip 左邊
        else:
            connect_x = tooltip_x + tooltip_width  # 連接到 tooltip 右邊
            
        if tooltip_y > anchor_pos.y():
            connect_y = tooltip_y  # 連接到 tooltip 上邊
        else:
            connect_y = tooltip_y + tooltip_height  # 連接到 tooltip 下邊
        
        # 繪製虛線 - 使用車手顏色或預設灰色
        dash_pen = QPen(driver_color if driver_color else QColor(128, 128, 128), 1, Qt.DashLine)
        painter.setPen(dash_pen)
        painter.drawLine(anchor_pos.x(), anchor_pos.y(), connect_x, connect_y)
        
        # 🆕 繪製錨點小圓點 - 使用車手顏色
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(driver_color if driver_color else QColor(255, 165, 0)))
        painter.drawEllipse(anchor_pos, 4, 4)
        
        # 繪製背景 - 使用車手顏色作為背景
        if driver_color:
            # 使用車手顏色作為背景，加點透明度
            bg_color = QColor(driver_color.red(), driver_color.green(), driver_color.blue(), 230)
        else:
            bg_color = QColor(200, 200, 200, 230)  # 預設灰色背景
        
        border_color = QColor(50, 50, 50)  # 深灰色邊框
        border_pen = QPen(border_color, 2)
        painter.setPen(border_pen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(tooltip_rect, 5, 5)
        
        # 計算文字顏色 - 根據背景亮度決定黑色或白色
        if driver_color:
            # 計算背景亮度 (使用相對亮度公式)
            luminance = 0.299 * driver_color.red() + 0.587 * driver_color.green() + 0.114 * driver_color.blue()
            text_color = QColor(0, 0, 0) if luminance > 128 else QColor(255, 255, 255)
        else:
            text_color = QColor(0, 0, 0)
        
        painter.setPen(QPen(text_color, 1))
        current_y = tooltip_y + padding
        
        for i, line in enumerate(lines):
            painter.drawText(
                tooltip_x + padding,
                current_y + line_heights[i] - fm.descent(),
                line
            )
            current_y += line_heights[i]
        
        return tooltip_rect
    
    def _get_tire_colors(self, tire_compound: str, is_pinned: bool) -> tuple:
        """根據輪胎類型返回背景色和文字色"""
        if not tire_compound:
            # 預設顏色
            if is_pinned:
                return QColor(173, 216, 230, 230), QColor(0, 0, 0)  # 淺藍色
            else:
                return QColor(255, 255, 200, 230), QColor(0, 0, 0)  # 淺黃色
        
        tire_upper = tire_compound.upper()
        
        # 輪胎顏色映射
        if tire_upper in ('SOFT', 'S'):
            return QColor(255, 60, 60, 230), QColor(255, 255, 255)  # 紅色底白字
        elif tire_upper in ('MEDIUM', 'M'):
            return QColor(255, 200, 0, 230), QColor(0, 0, 0)  # 黃色底黑字
        elif tire_upper in ('HARD', 'H'):
            return QColor(255, 255, 255, 230), QColor(0, 0, 0)  # 白色底黑字
        elif tire_upper in ('INTERMEDIATE', 'I'):
            return QColor(0, 180, 0, 230), QColor(255, 255, 255)  # 綠色底白字
        elif tire_upper in ('WET', 'W'):
            return QColor(0, 100, 255, 230), QColor(255, 255, 255)  # 藍色底白字
        else:
            # 未知輪胎類型，使用預設顏色
            if is_pinned:
                return QColor(173, 216, 230, 230), QColor(0, 0, 0)
            else:
                return QColor(255, 255, 200, 230), QColor(0, 0, 0)
    
    def _check_hover_point(self, mouse_pos: QPoint):
        """檢查滑鼠是否懸停在數據點上並顯示 Tooltip（優化版）"""
        import time
        start_time = time.perf_counter()  # 性能追蹤開始
        
        if not self.series_list or not self.chart_rect.isValid():
            if self.hover_point:  # 只有當有懸停點時才更新
                self.setToolTip("")
                self.hover_point = None
                self.hover_screen_pos = None
                self._last_hover_point = None
                self.update()
            return
        
        # 搜索半徑（像素）- 20px
        search_radius = 20
        closest_point = None
        closest_distance = search_radius
        closest_series_name = ""
        closest_screen_pos = None
        
        points_checked = 0  # 性能統計：檢查的點數
        
        # 遍歷所有數據系列和數據點
        for series in self.series_list:
            for data_point in series.data:
                points_checked += 1
                
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
        
        # 性能追蹤結束
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # 如果找到懸停的點，顯示 Tooltip
        if closest_point:
            # 🚀 優化：檢查是否與上次懸停點相同，避免重複重繪
            if self._last_hover_point is closest_point:
                # logger.debug(f"[TOOLTIP_PERF] 懸停點未變，跳過重繪 ({elapsed_ms:.2f}ms, {points_checked}點)")
                return  # 懸停點未改變，不重繪
            
            lap_number = int(closest_point.x)
            lap_time = closest_point.y
            
            # 格式化時間（秒 → 分:秒.毫秒）
            minutes = int(lap_time // 60)
            seconds = lap_time % 60
            
            if minutes > 0:
                time_str = f"{minutes}:{seconds:06.3f}"
            else:
                time_str = f"{seconds:.3f}s"
            
            # 獲取輪胎種類
            tire_compound = closest_point.metadata.get('tire_compound', 'N/A')
            
            # 顯示 Tooltip（同時使用 Qt 原生和自繪）- 添加輪胎種類
            tooltip_text = f"{closest_series_name} - Lap {lap_number}\nLap Time: {time_str}\nTire: {tire_compound}"
            self.setToolTip(tooltip_text)  # Qt 原生 Tooltip（備用）
            self.hover_point = closest_point
            self._last_hover_point = closest_point  # 🚀 記錄當前懸停點
            self.hover_screen_pos = closest_screen_pos
            self.hover_tooltip_text = tooltip_text  # 自繪 Tooltip 文字
            
            # 性能日誌（僅在耗時較長時記錄）
            if elapsed_ms > 50:  # 超過50ms記錄警告（提高門檻）
                logger.warning(f"[TOOLTIP_PERF] ⚠️ 懸停檢查耗時過長: {elapsed_ms:.2f}ms ({points_checked}點檢查)")
            
            self.update()  # 重繪以顯示高亮圓圈和 Tooltip
        else:
            # 🚀 優化：僅在之前有懸停點時才清除並重繪
            if self.hover_point:
                self.setToolTip("")  # 清除 Tooltip
                self.hover_point = None
                self._last_hover_point = None
                self.hover_screen_pos = None
                self.hover_tooltip_text = ""
                self.update()  # 重繪以清除高亮圓圈和 Tooltip


class DriverSelectionWidget(QWidget):
    """車手選擇控制區 - 整合跨模組同步"""
    
    drivers_selected = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_drivers = []
        self.selected_drivers = []
        self.driver_combos = []
        self._is_syncing = False  # 防止循環觸發
        self.setup_ui()
        self._register_global_sync()
        
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
        
        # 🆕 清除標籤按鈕（清除所有固定的 Tooltip）
        self.clear_labels_button = QPushButton(tr('clear_labels', 'Clear Labels'))
        self.clear_labels_button.clicked.connect(self._on_clear_labels_clicked)
        self.clear_labels_button.setMaximumWidth(90)
        self.clear_labels_button.setToolTip(tr('clear_labels_tooltip', 'Clear all pinned labels on chart'))
        
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
        driver_layout.addWidget(self.clear_labels_button)  # 🆕 添加清除標籤按鈕
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
        logger.debug(f"[DRIVER_SELECTION] 🔄 更新車手列表: {drivers}")
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
            logger.debug(f"[DRIVER_SELECTION] 🎯 自動選擇前3位車手")
            for i, driver in enumerate(drivers[:3]):  # 自動選擇前3位車手
                if i < len(self.driver_combos):
                    self.driver_combos[i].setCurrentText(driver)
                    logger.debug(f"[DRIVER_SELECTION] - 車手 {i+1}: {driver}")
        
        # 恢復信號發射
        for combo in self.driver_combos:
            combo.blockSignals(False)
        
        # 觸發一次選擇應用
        self._apply_selections()
        
        logger.info(f"[DRIVER_SELECTION] ✅ 車手列表更新完成，總車手數: {len(drivers)}")
        logger.debug(f"[DRIVER_SELECTION] 當前選擇: {self.selected_drivers}")
                
    def _on_driver_selection_changed(self):
        """車手選擇改變處理"""
        if self._is_syncing:
            return
        self._apply_selections()
        
    def _clear_selections(self):
        """清除所有選擇"""
        for combo in self.driver_combos:
            combo.setCurrentIndex(0)
        self._apply_selections()
    
    def _on_clear_labels_clicked(self):
        """清除所有固定的標籤（Tooltip）"""
        if self.chart_widget:
            self.chart_widget._clear_all_pinned_tooltips()
            logger.debug("[DRIVER_SELECTION] 已清除所有固定標籤")
        
    def _export_chart(self):
        """匯出圖表"""
        logger.debug("[DRIVER_SELECTION] 匯出圖表功能待實現")
        # TODO: 實現圖表匯出功能
        
    def _apply_selections(self):
        """應用車手選擇並發送同步信號"""
        selected = []
        placeholder = f"-- {tr('please_select', '請選擇')} --"
        for combo in self.driver_combos:
            driver = combo.currentText()
            if driver != placeholder and driver not in selected:
                selected.append(driver)
        
        self.selected_drivers = selected
        self.drivers_selected.emit(selected)
        
        # 發送同步信號到其他模組
        if not self._is_syncing:
            sync = GlobalChartSyncSignal.get_instance()
            sync.emit_drivers_changed(selected, MODULE_DETAILED_LAP)
            logger.debug(f"[DRIVER_SELECTION] Sync emitted: {selected}")

    # ------------------------------------------------------------------
    # GlobalChartSyncSignal 跨模組同步
    # ------------------------------------------------------------------
    def _register_global_sync(self) -> None:
        """註冊到全局同步信號"""
        # 🚀 暫時停用 GlobalChartSyncSignal 以排查性能問題
        return
        # sync = GlobalChartSyncSignal.get_instance()
        # sync.register_module(MODULE_DETAILED_LAP)
        # sync.drivers_changed.connect(self._on_global_drivers_changed)
        # logger.debug("[DRIVER_SELECTION] Registered to GlobalChartSyncSignal")

    def _unregister_global_sync(self) -> None:
        """取消註冊全局同步信號"""
        try:
            sync = GlobalChartSyncSignal.get_instance()
            sync.drivers_changed.disconnect(self._on_global_drivers_changed)
            sync.unregister_module(MODULE_DETAILED_LAP)
            logger.debug("[DRIVER_SELECTION] Unregistered from GlobalChartSyncSignal")
        except (TypeError, RuntimeError):
            pass

    def _on_global_drivers_changed(self, drivers: list, source: str) -> None:
        """處理來自其他模組的車手同步事件"""
        if source == MODULE_DETAILED_LAP:
            return  # 忽略自己發出的
        
        # 🚀 優化：如果車手列表相同，跳過處理避免無效更新
        new_drivers = [d.upper() for d in drivers if d]
        if new_drivers == self.selected_drivers:
            return
        
        # 🚀 移除 logger.info 減少 I/O
        # logger.debug(f"[DRIVER_SELECTION] Sync drivers from {source}: {drivers}")
        
        self._is_syncing = True
        
        # 先清空所有選擇
        placeholder = f"-- {tr('please_select', '請選擇')} --"
        for combo in self.driver_combos:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        
        # 設定新選擇
        for i, driver in enumerate(drivers[:5]):  # 最多 5 個
            if i < len(self.driver_combos):
                combo = self.driver_combos[i]
                combo.blockSignals(True)
                index = combo.findText(driver.upper())
                if index != -1:
                    combo.setCurrentIndex(index)
                combo.blockSignals(False)
        
        self.selected_drivers = new_drivers
        self.drivers_selected.emit(self.selected_drivers)
        
        self._is_syncing = False

    def set_selected_drivers(self, drivers: list) -> None:
        """設定選中的車手（用於外部同步）"""
        self._on_global_drivers_changed(drivers, "external")

    def cleanup(self) -> None:
        """清理資源"""
        self._unregister_global_sync()


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
        self.filter_first_laps = True
        self._apply_boxplot_settings(self.settings_manager.get_boxplot_settings())
        self.settings_manager.boxplot_settings_changed.connect(self._on_boxplot_settings_changed)
        
        # 設置UI
        self.setup_ui()
        
        logger.debug("[LAPTIME_CHART] 詳細圈速分析圖表組件初始化完成 (修正版架構)")
    
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
            logger.debug(f"[LAPTIME_CHART] 收到數據更新")
            logger.debug(f"[LAPTIME_CHART] 數據類型: {type(data)}")
            logger.debug(f"[LAPTIME_CHART] 數據鍵: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # 兼容處理：解包 charts_data
            if isinstance(data, dict) and 'charts_data' in data:
                data = data.get('charts_data', {})
                logger.debug("[LAPTIME_CHART] 解包 charts_data")
            
            self.chart_data = data
            
            # 獲取可用車手列表
            detailed_laptime_data = data.get('all_drivers_detailed_laptime', {})
            drivers_analyzed = data.get('drivers_analyzed', list(detailed_laptime_data.keys()))
            
            logger.debug(f"[LAPTIME_CHART] 可用車手: {drivers_analyzed}")
            
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
            logger.debug(f"[LAPTIME_CHART] 數據更新錯誤: {e}")
            traceback.print_exc()
    
    def _on_drivers_selected(self, drivers: List[str]):
        """處理車手選擇變更"""
        logger.debug(f"[LAPTIME_CHART] 車手選擇變更: {drivers}")
        self.selected_drivers = drivers
        self._update_chart_data()
        
        # 發射信號
        if drivers:
            self.driver_selected.emit(drivers[0])
    
    def _update_chart_data(self):
        """更新圖表數據 - 使用動態顏色（選中車手顯示顏色，未選中顯示灰色）"""
        try:
            logger.debug(f"[LAPTIME_CHART] 更新圖表，選中車手: {self.selected_drivers}")
            
            if not self.chart_data or not self.selected_drivers:
                self.chart_widget.update_series_data([])
                return
            
            # 獲取詳細圈速數據
            detailed_laptime_data = self.chart_data.get('all_drivers_detailed_laptime', {})
            
            # 轉換為圖表系列格式
            series_list = []
            
            # 追蹤同隊車手，用於虛線區分（同隊第二位使用虛線）
            team_driver_count: Dict[str, int] = {}
            
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
                marker_only_points = []  # 被過濾但仍需繪製標記的圈（如 Pit 圈垂直線）
                filtered_pit = 0
                filtered_caution = 0
                filtered_first_laps = 0

                for lap_info in lap_data:
                    lap_num_raw = lap_info.get('lap_number', 0)
                    lap_num_normalized = normalize_lap_number(lap_num_raw)
                    lap_num_for_chart = lap_num_normalized if lap_num_normalized is not None else lap_num_raw
                    lap_time_sec = lap_info.get('lap_time_seconds', 0)

                    # 檢查數值有效性：不為 None 且大於 0
                    if lap_time_sec is None or lap_time_sec <= 0:
                        continue

                    # 過濾前兩圈 (Lap 1 & 2)
                    if self.filter_first_laps and lap_num_raw in (1, 2):
                        filtered_first_laps += 1
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
                        # 保留 Pit 圈的標記資訊用於繪製垂直線
                        pit_markers = self._extract_markers(driver_data, lap_info, caution_laps)
                        if pit_markers:  # 只有有標記時才保留
                            marker_only_points.append(ChartDataPoint(
                                x=lap_num_for_chart,
                                y=0,  # Y 值不重要，只用於繪製垂直線
                                metadata={'markers': pit_markers, 'driver': driver, 'filtered': True}
                            ))
                        continue

                    # 提取智能標記
                    markers = self._extract_markers(driver_data, lap_info, caution_laps)
                    
                    # 提取輪胎種類
                    tire_compound = lap_info.get('tire_compound', 'N/A')

                    data_point = ChartDataPoint(
                        x=lap_num_for_chart,
                        y=lap_time_sec,
                        metadata={'markers': markers, 'driver': driver, 'tire_compound': tire_compound}
                    )
                    data_points.append(data_point)

                if filtered_pit or filtered_caution:
                    logger.debug(
                        f"[LAPTIME_CHART] {driver}: filtered {filtered_pit} pit laps, {filtered_caution} caution laps"
                    )

                if data_points:
                    # 使用 color_palette_provider 獲取車手顏色
                    color = ChartTheme.get_driver_color(driver, self.selected_drivers)
                    
                    # 同隊車手虛線區分：第二位同隊車手使用虛線
                    driver_team = color_palette_provider.get_driver_team(driver)
                    if driver_team:
                        team_driver_count[driver_team] = team_driver_count.get(driver_team, 0) + 1
                        use_dashed = team_driver_count[driver_team] > 1
                    else:
                        use_dashed = False
                    line_style = Qt.DashLine if use_dashed else Qt.SolidLine

                    series = ChartSeries(
                        name=driver,
                        data=data_points,
                        color=color,
                        line_width=2,
                        style='line',
                        line_style=line_style,
                        marker_only_points=marker_only_points,  # 傳入被過濾的 Pit 圈標記
                    )
                    series_list.append(series)
            
            # 更新圖表組件
            self.chart_widget.update_series_data(series_list)
            
        except Exception as e:
            logger.debug(f"[LAPTIME_CHART] 圖表數據更新錯誤: {e}")
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
            logger.debug(f"[LAPTIME_CHART_WIDGET] 智能標記數據結構:")
            logger.debug(f"[LAPTIME_CHART_WIDGET] - driver_data 鍵: {list(driver_data.keys())}")
            logger.debug(f"[LAPTIME_CHART_WIDGET] - smart_markers_summary 鍵: {list(smart_markers_summary.keys())}")

        def _contains_lap(collection: Any) -> bool:
            if not isinstance(collection, (list, tuple, set)):
                return False
            if lap_num is not None:
                return any(normalize_lap_number(val) == lap_num for val in collection)
            return lookup_value in collection

        # 進站檢測 - 只標記進站圈（pit_in），不標記出站圈（pit_out）
        smart_markers = lap_info.get('smart_markers', {})
        if isinstance(smart_markers, dict):
            pit_detection = smart_markers.get('pit_stop_detection', {})
            # 檢查 pit_type 是否為 'pit_in'（只標記進站圈）
            if pit_detection.get('is_pit_lap', False) and pit_detection.get('pit_type') == 'pit_in':
                markers.append('P')
        else:
            # 備用檢測：使用舊邏輯（如果沒有 smart_markers）
            if lap_is_pit_stop(lap_info, smart_markers_summary):
                # 進一步檢查是否有 pit_in_time（只標記進站圈）
                if lap_info.get('pit_in_time') is not None:
                    markers.append('P')

        # 輪胎更換檢測（已禁用 - 只顯示進站 P 標記）
        # tire_data = smart_markers_summary.get('tire_change_detection', {})
        # if _contains_lap(tire_data.get('tire_change_lap_numbers')):
        #     markers.append('T')

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
            logger.debug(f"[LAPTIME_CHART_WIDGET] 圈 {lookup_value} 找到標記: {markers}")

        return markers

    def _apply_boxplot_settings(self, settings: Dict[str, Any]) -> None:
        self.filter_pit_laps = settings.get('filter_pit_laps', True)
        self.filter_yellow_flags = settings.get('filter_yellow_flags', True)
        self.filter_first_laps = settings.get('filter_first_laps', True)

    def _on_boxplot_settings_changed(self, settings: Dict[str, Any]) -> None:
        previous_filter = (
            self.filter_pit_laps,
            self.filter_yellow_flags,
            self.filter_first_laps,
        )
        self._apply_boxplot_settings(settings)

        current_filter = (
            self.filter_pit_laps,
            self.filter_yellow_flags,
            self.filter_first_laps,
        )

        if previous_filter != current_filter and self.chart_data:
            self._update_chart_data()

    def set_data(self, data: Dict[str, Any]):
        """兼容舊版介面"""
        self.update_data(data)
    
    def update_chart(self):
        """兼容舊版介面"""
        self.chart_widget.update()
    
    def reset_zoom(self):
        """重置縮放（供全局 Show All Data 按鈕調用）"""
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'reset_zoom'):
            self.chart_widget.reset_zoom()
            logger.debug("[LAPTIME_CHART] 縮放已重置")


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
    
    logger.debug("詳細圈速分析圖表組件測試啟動 (修正版)")
    sys.exit(app.exec_())
