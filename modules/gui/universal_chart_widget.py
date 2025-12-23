#!/usr/bin/env python3
"""
通用圖表視窗 - Universal Chart Widget
支援任意X軸、Y軸數據，雙Y軸，和特殊標註功能
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QMenu, QAction, QDialog, QFormLayout, 
                             QDoubleSpinBox, QPushButton, QDialogButtonBox,
                             QCheckBox, QGroupBox, QGridLayout, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QPoint, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush
import json
import math  # 用於數據點距離計算
import logging

from core.logger import get_logger
logger = get_logger(__name__)


logger = get_logger("universal_chart_widget", component="gui")


class ChartDataSeries:
    """圖表數據系列類別"""
    
    def __init__(self, name, x_data, y_data, color="white", line_width=2, y_axis="left", line_style=Qt.SolidLine):
        self.name = name
        self.x_data = x_data  # X軸數據列表
        self.y_data = y_data  # Y軸數據列表
        self.color = color    # 線條顏色
        self.line_width = line_width
        self.y_axis = y_axis  # "left" 或 "right" (雙Y軸支援)
        self.line_style = line_style  # 線條樣式：Qt.SolidLine, Qt.DashLine, Qt.DotLine 等
        
    def get_x_range(self):
        """獲取X軸數據範圍"""
        if not self.x_data:
            return 0, 1
        return min(self.x_data), max(self.x_data)
    
    def get_y_range(self):
        """獲取Y軸數據範圍"""
        if not self.y_data:
            return 0, 1
        return min(self.y_data), max(self.y_data)


class ChartAnnotation:
    """圖表標註類別 - 用於降雨等特殊標註"""
    
    def __init__(self, annotation_type, start_x, end_x=None, y_position=0, text="", label="", color="#FF6B6B", intensity=None):
        self.annotation_type = annotation_type  # "rain", "event", "background_fill", etc.
        self.start_x = start_x
        self.end_x = end_x if end_x else start_x
        self.y_position = y_position
        self.text = text
        self.label = label
        self.color = color
        self.intensity = intensity  # 降雨強度等級


class UniversalChartWidget(QWidget):
    """通用圖表視窗 - 支援任意數據、雙Y軸、標註"""
    
    # 信號
    chart_clicked = pyqtSignal(float, float)  # X, Y座標點擊
    data_point_hovered = pyqtSignal(str)      # 數據點懸停
    rain_region_hovered = pyqtSignal(dict)    # 降雨區間懸停 - 新增
    background_region_added = pyqtSignal(dict)  # 背景區間已添加 - 新增
    
    def __init__(self, title="通用圖表", parent=None):
        super().__init__(parent)
        self.title = title
        self.data_series = []      # ChartDataSeries 列表
        self.annotations = []      # ChartAnnotation 列表
        
        # 軸配置
        self.left_y_axis_label = "左Y軸"
        self.right_y_axis_label = "右Y軸"
        self.x_axis_label = "X軸"
        self.left_y_unit = ""
        self.right_y_unit = ""
        self.x_unit = None
        self.default_x_unit = "分鐘"
        
        # 顯示控制
        self.show_grid = True
        self.show_legend = True
        self.show_right_y_axis = False  # 當有右Y軸數據時自動啟用
        
        # 滑鼠追蹤和縮放參數 (繼承自 TelemetryChartWidget)
        self.setMouseTracking(True)
        self.mouse_x = -1
        self.mouse_y = -1
        self.sync_enabled = True
        
        # 縮放和拖拉參數
        self.y_scale = 1.0
        self.y_offset = 0
        self.x_offset = 0
        self.x_scale = 1.0
        self.right_y_scale = 1.0    # 右Y軸縮放
        self.right_y_offset = 0     # 右Y軸偏移
        
        # 拖拉狀態
        self.dragging = False
        self.last_drag_pos = QPoint()
        
        # 圖例拖拉功能
        self.legend_dragging = False
        self.legend_drag_offset = QPoint()
        self.legend_position = QPoint(10, 30)  # 圖例初始位置
        self.legend_rect = None  # 圖例矩形區域（用於碰撞檢測）
        
        # 固定虛線功能
        self.fixed_vertical_lines = []  # 存儲固定的垂直線 [(x_pos, left_y_value, right_y_value), ...]
        self.show_value_tooltips = True  # 是否顯示數值提示
        
        # 🆕 數據點互動功能（參考 Detailed Lap Analysis）
        self.hover_data_point = None  # 當前懸停的數據點 {'series_idx': int, 'point_idx': int, 'x': float, 'y': float, 'screen_pos': QPoint}
        self.pinned_data_points = []  # 固定的數據點列表（最多2個），每個元素: {'series_idx', 'point_idx', 'x', 'y', 'screen_pos', 'tooltip_rect', 'custom_pos'}
        self.data_point_search_radius = 20  # 數據點檢測半徑（像素）
        self.data_point_radius = 3  # 數據點繪製半徑（像素）
        self.show_data_points = True  # 是否顯示數據點（線+點模式）
        
        # 🆕 Tooltip 拖動功能
        self.dragging_tooltip = False  # 是否正在拖動 tooltip
        self.dragging_tooltip_index = -1  # 正在拖動的 tooltip 索引
        self.tooltip_drag_offset = QPoint(0, 0)  # tooltip 拖動偏移量
        
        # 座標軸範圍控制 - 支援使用者自訂範圍
        self.manual_x_range = None      # (min, max) 或 None 表示自動
        self.manual_left_y_range = None # (min, max) 或 None 表示自動  
        self.manual_right_y_range = None # (min, max) 或 None 表示自動
        self.auto_range_enabled = True   # 是否啟用自動範圍計算
        
        # X軸間距設定 (以分鐘為單位)
        self.x_axis_interval_minutes = 15  # 預設15分鐘一個刻度點
        
        # 圖表邊距
        self.margin_left = 60
        self.margin_bottom = 40
        self.margin_top = 30
        self.margin_right = 60 if self.show_right_y_axis else 10
        
        # 字體大小設置 - 確保在所有情況下都有預設值
        self.axis_font_size = 9
        self.label_font_size = 10
        self.legend_font_size = 8
        
        # 降雨標記系統 - 確保總是初始化
        if not hasattr(self, 'rain_background_regions'):
            self.rain_background_regions = []  # 降雨背景區間
        if not hasattr(self, 'rain_text_markers'):
            self.rain_text_markers = []        # 降雨文字標記
        
        # 設置size policy讓圖表能夠自適應MDI視窗大小
        from PyQt5.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 移除最小尺寸限制，允許完全自由縮放
        # self.setMinimumSize(200, 120)  # 已移除尺寸限制
        
        # 動態字體大小
        self.axis_font_size = 9
        self.label_font_size = 10
        self.legend_font_size = 8
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 隱藏標題 - 避免覆蓋圖表
        # title_label = QLabel(self.title)
        # title_font = QFont()
        # title_font.setPointSize(14)
        # title_font.setBold(True)
        # title_label.setFont(title_font)
        # title_label.setAlignment(Qt.AlignCenter)
        # title_label.setStyleSheet("color: white; background: transparent;")
        # layout.addWidget(title_label)
        
        # 主圖表區域就是這個 widget 本身 - 設定為透明背景以支持降雨背景透明度
        # self.setStyleSheet("background-color: white;")  # 移除以支持透明度效果
    
    def resizeEvent(self, event):
        """處理視窗大小變更事件 - 優化版本，減少重複重繪"""
        super().resizeEvent(event)
        
        # 只在尺寸真正變化時才處理
        new_size = event.size()
        if hasattr(self, '_cached_size') and self._cached_size == new_size:
            return
        
        self._cached_size = new_size
        
        # 延遲處理自適應，避免頻繁調用
        if not hasattr(self, '_resize_timer'):
            from PyQt5.QtCore import QTimer
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._delayed_auto_fit)
        
        self._resize_timer.stop()
        self._resize_timer.start(50)  # 50ms 延遲
        
    def _delayed_auto_fit(self):
        """延遲執行的自適應調整"""
        self.auto_fit_to_window()
        self.update()  # 只調用一次update，不使用repaint
    
    def auto_fit_to_window(self):
        """自動調整圖表以適應視窗大小 - 最終優化版本，避免重複處理"""
        widget_size = self.size()
        
        # 防止重複處理相同的尺寸
        if hasattr(self, '_last_auto_fit_size') and self._last_auto_fit_size == widget_size:
            return
        
        self._last_auto_fit_size = widget_size
        
        # 根據視窗大小動態調整邊距，確保小視窗也能完整顯示
        width = widget_size.width()
        height = widget_size.height()
        
        # 為MDI環境優化：確保任何尺寸都能正確顯示
        if width <= 0 or height <= 0:
            return  # 防止無效尺寸
        
        # 固定邊距 - 不使用比例調整，保持一致的佈局
        self.margin_left = 60
        self.margin_right = 40
        self.margin_top = 25
        self.margin_bottom = 40
        self.axis_font_size = 9
        self.label_font_size = 10
        self.legend_font_size = 8
        
        # 確保右軸邊距正確設置
        if self.show_right_y_axis:
            self.margin_right = max(self.margin_right, 50)
        
        # 移除DEBUG輸出防止無限循環
        
        if not self.data_series:
            return
            
        # 重置縮放和偏移，確保圖表完全適應新尺寸
        self.x_scale = 1.0
        self.y_scale = 1.0
        self.right_y_scale = 1.0
        self.x_offset = 0
        self.y_offset = 0
        self.right_y_offset = 0
        
        # 計算新的圖表區域
        chart_area = self.get_chart_area()
        
        # 移除所有尺寸限制，允許圖表完全自由縮放
        # 即使圖表區域很小也允許繼續顯示
        
        # 只在圖表區域有效且尺寸真正變化時才輸出調試信息
        if chart_area.width() > 0 and chart_area.height() > 0:
            # 避免重複輸出相同的尺寸信息
            current_chart_size = (chart_area.width(), chart_area.height())
            if not hasattr(self, '_last_chart_size') or self._last_chart_size != current_chart_size:
                self._last_chart_size = current_chart_size
        
        # 計算數據範圍但不觸發重繪（避免在paintEvent中無限循環）
        if not hasattr(self, '_in_paint_event'):
            self.recalculate_data_ranges()
    
    def reset_view(self):
        """重置視圖到初始狀態 - 優化版本"""
        
        # 強制重新調整到視窗大小
        self.auto_fit_to_window()
        
        # 只調用一次更新
        self.update()
    
    def force_refresh(self):
        """強制刷新圖表 - 優化版本"""
        
        # 獲取當前尺寸
        current_size = self.size()
        
        # 重新計算邊距和縮放
        self.auto_fit_to_window()
        
        # 重新計算數據範圍
        self.recalculate_data_ranges()
        
        # 只調用一次更新
        self.update()
    
    def add_data_series(self, series):
        """添加數據系列"""
        self.data_series.append(series)
        
        # 如果有右Y軸數據，啟用右Y軸
        if series.y_axis == "right":
            self.show_right_y_axis = True
            self.margin_right = 60
        
        self.update()
    
    def add_annotation(self, annotation):
        """添加標註"""
        self.annotations.append(annotation)
        self.update()
    
    def clear_data(self):
        """清除所有數據"""
        self.data_series.clear()
        self.annotations.clear()
        self.show_right_y_axis = False
        self.margin_right = 10
        
        # 清除降雨標記 - 安全調用
        if hasattr(self, 'clear_rain_markers'):
            self.clear_rain_markers()
        else:
            # 如果方法不存在，手動清除屬性
            if hasattr(self, 'rain_text_markers'):
                for marker_info in self.rain_text_markers:
                    if isinstance(marker_info, dict) and 'widget' in marker_info and marker_info['widget']:
                        marker_info['widget'].deleteLater()
                self.rain_text_markers.clear()
            
            if hasattr(self, 'rain_background_regions'):
                self.rain_background_regions.clear()
                
            logger.info("已手動清除降雨標記")
        
        self.update()
    
    def recalculate_data_ranges(self):
        """重新計算數據範圍以適應新的視窗尺寸 - MDI自適應關鍵方法"""
        if not self.data_series:
            return
        
        # 重新計算所有數據範圍
        try:
            # 獲取整體X軸範圍
            x_range = self.get_overall_x_range()
            left_y_range = self.get_overall_left_y_range()
            right_y_range = self.get_overall_right_y_range() if self.show_right_y_axis else (0, 1)
            
            # 確保範圍有效
            if x_range[1] <= x_range[0]:
                logger.warning("[WARNING] X軸範圍無效，使用預設值")
                x_range = (0, 1)
            if left_y_range[1] <= left_y_range[0]:
                logger.warning("[WARNING] 左Y軸範圍無效，使用預設值")
                left_y_range = (0, 1)
            if self.show_right_y_axis and right_y_range[1] <= right_y_range[0]:
                logger.warning("[WARNING] 右Y軸範圍無效，使用預設值")
                right_y_range = (0, 1)
            
            # 保存計算的範圍供繪圖使用
            self._cached_x_range = x_range
            self._cached_left_y_range = left_y_range
            self._cached_right_y_range = right_y_range
            
        except Exception as e:
            logger.error("[ERROR] 重新計算數據範圍失敗: %s", e)
            # 使用安全的預設值
            self._cached_x_range = (0, 1)
            self._cached_left_y_range = (0, 1)
            self._cached_right_y_range = (0, 1)
    
    def set_axis_labels(self, x_label, left_y_label, right_y_label="", 
                       x_unit=None, left_y_unit="", right_y_unit=""):
        """設置軸標籤和單位"""
        self.x_axis_label = x_label
        self.left_y_axis_label = left_y_label
        self.right_y_axis_label = right_y_label
        self.x_unit = x_unit
        self.left_y_unit = left_y_unit
        self.right_y_unit = right_y_unit
        self.update()
    
    def load_from_json(self, json_data):
        """從JSON數據載入圖表
        
        預期JSON格式:
        {
            "chart_title": "圖表標題",
            "x_axis": {"label": "時間", "unit": "s", "data": [...]},
            "left_y_axis": {"label": "溫度", "unit": "°C", "data": [...]},
            "right_y_axis": {"label": "風速", "unit": "km/h", "data": [...]},
            "annotations": [
                {"type": "rain", "start_x": 100, "end_x": 200, "label": "降雨"}
            ]
        }
        """
        self.clear_data()
        
        if "chart_title" in json_data:
            self.title = json_data["chart_title"]
        
        # 處理X軸數據
        x_data = json_data.get("x_axis", {}).get("data", [])
        x_label = json_data.get("x_axis", {}).get("label", "X軸")
        x_unit = json_data.get("x_axis", {}).get("unit", "")
        
        # 處理左Y軸數據
        if "left_y_axis" in json_data:
            left_y_data = json_data["left_y_axis"].get("data", [])
            left_y_label = json_data["left_y_axis"].get("label", "左Y軸")
            left_y_unit = json_data["left_y_axis"].get("unit", "")
            
            if left_y_data and len(left_y_data) == len(x_data):
                left_series = ChartDataSeries(
                    name=left_y_label,
                    x_data=x_data,
                    y_data=left_y_data,
                    color="#FFA366",  # 淺橘色，在黑色背景下更明顯
                    line_width=2,  # 2像素寬度
                    y_axis="left"
                )
                self.add_data_series(left_series)
        # 處理右Y軸數據
        if "right_y_axis" in json_data:
            right_y_data = json_data["right_y_axis"].get("data", [])
            right_y_label = json_data["right_y_axis"].get("label", "右Y軸")
            right_y_unit = json_data["right_y_axis"].get("unit", "")
            
            if right_y_data and len(right_y_data) == len(x_data):
                right_series = ChartDataSeries(
                    name=right_y_label,
                    x_data=x_data,
                    y_data=right_y_data,
                    color="#66B3FF",  # 淺藍色（偏藍），在黑色背景下更明顯
                    line_width=2,  # 2像素寬度
                    y_axis="right"
                )
                self.add_data_series(right_series)
        
        # 設置軸標籤
        self.set_axis_labels(
            x_label, 
            json_data.get("left_y_axis", {}).get("label", "左Y軸"),
            json_data.get("right_y_axis", {}).get("label", "右Y軸"),
            x_unit,
            json_data.get("left_y_axis", {}).get("unit", ""),
            json_data.get("right_y_axis", {}).get("unit", "")
        )
        
        # 處理標註
        annotations_count = 0
        if "annotations" in json_data:
            for ann_data in json_data["annotations"]:
                annotation = ChartAnnotation(
                    annotation_type=ann_data.get("type", "event"),
                    start_x=ann_data.get("start_x", 0),
                    end_x=ann_data.get("end_x"),
                    label=ann_data.get("label", ""),
                    color=ann_data.get("color", "#FF6B6B")
                )
                self.add_annotation(annotation)
                annotations_count += 1
        
        logger.info(
            "[OK] 通用圖表載入完成: %d 個數據系列, %d 個標註",
            len(self.data_series),
            len(self.annotations)
        )
        self.auto_fit_to_window()  # 自動調整圖表以適配視窗大小
        self.update()  # 強制重繪
        # 移除DEBUG輸出防止無限循環
    
    def get_chart_area(self):
        """獲取圖表繪製區域 - 確保所有邊距都是整數"""
        return self.rect().adjusted(
            int(self.margin_left), 
            int(self.margin_top), 
            -int(self.margin_right), 
            -int(self.margin_bottom)
        )
    
    def get_overall_x_range(self):
        """獲取所有數據系列的X軸範圍 - 支援手動範圍"""
        # 如果有手動設定的範圍，優先使用
        if self.manual_x_range is not None:
            return self.manual_x_range
        
        # 否則自動計算範圍
        if not self.data_series:
            return 0, 1
        
        all_x_min = []
        all_x_max = []
        for series in self.data_series:
            x_min, x_max = series.get_x_range()
            all_x_min.append(x_min)
            all_x_max.append(x_max)
        
        return min(all_x_min), max(all_x_max)
    
    def get_y_range_for_axis(self, y_axis="left"):
        """獲取指定Y軸的數據範圍 - 支援手動範圍，並增加padding"""
        # 如果有手動設定的範圍，優先使用
        if y_axis == "left" and self.manual_left_y_range is not None:
            return self.manual_left_y_range
        elif y_axis == "right" and self.manual_right_y_range is not None:
            return self.manual_right_y_range
        
        # 否則自動計算範圍
        series_for_axis = [s for s in self.data_series if s.y_axis == y_axis]
        if not series_for_axis:
            return 0, 1
        
        all_y_min = []
        all_y_max = []
        for series in series_for_axis:
            y_min, y_max = series.get_y_range()
            all_y_min.append(y_min)
            all_y_max.append(y_max)
        
        data_min = min(all_y_min)
        data_max = max(all_y_max)
        
        # 增加10%的padding，確保數據線不會被切掉
        data_range = data_max - data_min
        if data_range == 0:
            # 如果所有數據都相同，設置一個最小範圍
            padding = 0.1
        else:
            padding = data_range * 0.1
        
        return data_min - padding, data_max + padding
    
    def get_overall_left_y_range(self):
        """獲取左Y軸的整體數據範圍"""
        return self.get_y_range_for_axis("left")
    
    def get_overall_right_y_range(self):
        """獲取右Y軸的整體數據範圍"""
        return self.get_y_range_for_axis("right")
    
    def paintEvent(self, event):
        """繪製圖表 - 優化版本，減少重複處理"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 設定標誌防止在paintEvent中觸發無限循環
            self._in_paint_event = True
            
            # 白色背景 (白色主題)
            painter.fillRect(self.rect(), QColor(255, 255, 255))
            
            # 獲取圖表繪製區域（不再在paintEvent中調整尺寸）
            chart_area = self.get_chart_area()
            
            # 防止無效的圖表區域
            if chart_area.width() <= 0 or chart_area.height() <= 0:
                painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色文字
                painter.setFont(QFont("Arial", 12))
                painter.drawText(self.rect().center(), "視窗太小無法顯示圖表")
                self._in_paint_event = False  # 清除標誌
                return
            
            # 繪製坐標軸
            self.draw_axes(painter, chart_area)
            
            # 如果沒有數據，顯示提示訊息
            if not self.data_series:
                painter.setPen(QPen(QColor(200, 200, 200), 1))
                painter.setFont(QFont("Arial", max(self.axis_font_size + 2, 12)))
                message = f"正在載入數據..."
                text_rect = painter.fontMetrics().boundingRect(message)
                center_x = chart_area.center().x() - text_rect.width() // 2
                center_y = chart_area.center().y()
                painter.drawText(center_x, center_y, message)
                self._in_paint_event = False  # 清除標誌
                return
            
            # 設定裁切區域為圖表區域
            painter.setClipRect(chart_area)
            
            # 繪製網格
            if self.show_grid:
                self.draw_grid(painter, chart_area)
            
            # 繪製數據曲線 (包含降雨背景)
            self.draw_data_series(painter, chart_area)
            
            # 清除標誌
            self._in_paint_event = False
            
            # 繪製動態滑鼠追蹤虛線
            if self.mouse_x >= 0 and chart_area.contains(QPoint(self.mouse_x, chart_area.center().y())):
                painter.setPen(QPen(QColor(128, 128, 128), 2, Qt.DashLine))  # 灰色虛線
                painter.drawLine(self.mouse_x, chart_area.top(), self.mouse_x, chart_area.bottom())
                
                # 顯示當前滑鼠位置的數值
                if self.show_value_tooltips:
                    self.draw_mouse_values(painter, chart_area, self.mouse_x)
            
            # 繪製固定垂直虛線
            self.draw_fixed_vertical_lines(painter, chart_area)
            
            # 🆕 繪製懸停和固定的數據點（線+點互動）
            self.draw_hover_and_pinned_data_points(painter, chart_area)
            
            # 取消裁切
            painter.setClipping(False)
            
            # 繪製圖例
            if self.show_legend:
                self.draw_legend(painter)
        finally:
            # 🔑 確保總是釋放 QPainter 資源
            painter.end()
    
    def draw_axes(self, painter, chart_area):
        """繪製坐標軸"""
        painter.setPen(QPen(QColor(100, 100, 100), 2))  # 深灰色座標軸線
        
        # Y軸 (左邊)
        painter.drawLine(chart_area.left(), chart_area.top(), chart_area.left(), chart_area.bottom())
        
        # X軸 (底部)
        painter.drawLine(chart_area.left(), chart_area.bottom(), chart_area.right(), chart_area.bottom())
        
        # 右Y軸 (如果啟用)
        if self.show_right_y_axis:
            painter.drawLine(chart_area.right(), chart_area.top(), chart_area.right(), chart_area.bottom())
        
        # 軸標籤和刻度
        painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色文字
        painter.setFont(QFont("Arial", self.axis_font_size))
        
        # X軸標籤和刻度
        self.draw_x_axis_labels(painter, chart_area)
        
        # 左Y軸標籤和刻度
        self.draw_left_y_axis_labels(painter, chart_area)
        
        # 右Y軸標籤和刻度 (如果啟用)
        if self.show_right_y_axis:
            self.draw_right_y_axis_labels(painter, chart_area)
        
        # 軸標題
        painter.setFont(QFont("Arial", self.label_font_size))
        
        unit = self.default_x_unit if self.x_unit is None else self.x_unit
        x_label_text = f"{self.x_axis_label} ({unit})" if unit else self.x_axis_label
        painter.drawText(chart_area.center().x() - 50, self.height() - 5, x_label_text)
        
        # 左Y軸標題
        left_y_label_text = f"{self.left_y_axis_label}" + (f" ({self.left_y_unit})" if self.left_y_unit else "")
        painter.save()
        # 根據邊距動態調整標籤位置，確保在極小視窗中也有足夠空間
        label_x_position = min(18, self.margin_left - 45)  # 確保標籤不會超出邊距
        painter.translate(label_x_position, chart_area.center().y())
        painter.rotate(-90)
        painter.drawText(-50, 0, left_y_label_text)
        painter.restore()
        
        # 右Y軸標題
        if self.show_right_y_axis:
            right_y_label_text = f"{self.right_y_axis_label}" + (f" ({self.right_y_unit})" if self.right_y_unit else "")
            painter.save()
            painter.translate(self.width() - 15, chart_area.center().y())
            painter.rotate(90)
            painter.drawText(-50, 0, right_y_label_text)
            painter.restore()
    
    def draw_x_axis_labels(self, painter, chart_area):
        """繪製X軸刻度和標籤 - 考慮縮放和偏移"""
        if not self.data_series:
            return
        
        x_min, x_max = self.get_overall_x_range()
        if x_max == x_min:
            return
        
        # 考慮縮放和偏移的可視範圍計算
        # 計算當前可視區域對應的數據範圍
        visible_x_range = (x_max - x_min) / self.x_scale
        visible_x_center = x_min + (x_max - x_min) * 0.5
        
        # 根據偏移調整中心點
        offset_factor = -self.x_offset / (chart_area.width() * self.x_scale)
        visible_x_center += (x_max - x_min) * offset_factor
        
        # 計算可視X軸範圍
        visible_x_min = visible_x_center - visible_x_range * 0.5
        visible_x_max = visible_x_center + visible_x_range * 0.5
        
        # 使用設定的間距 (分鐘轉秒)
        interval_seconds = self.x_axis_interval_minutes * 60
        
        # 計算刻度點 - 基於可視範圍
        start_tick = int(visible_x_min / interval_seconds) * interval_seconds
        current_tick = start_tick
        
        while current_tick <= visible_x_max:
            # 只繪製在可視範圍內的刻度
            if current_tick >= visible_x_min:
                # 計算屏幕座標 - 基於可視範圍
                progress = (current_tick - visible_x_min) / (visible_x_max - visible_x_min)
                screen_x = int(chart_area.left() + chart_area.width() * progress)
                
                # 確保刻度線在圖表區域內
                if screen_x >= chart_area.left() and screen_x <= chart_area.right():
                    # 繪製刻度線
                    painter.drawLine(screen_x, chart_area.bottom(), screen_x, chart_area.bottom() + 5)
                    
                    # 繪製標籤 (只顯示分鐘，不顯示秒數)
                    minutes = int(current_tick // 60)
                    label = f"{minutes}"
                    painter.drawText(screen_x - 10, chart_area.bottom() + 18, label)
            
            current_tick += interval_seconds
    
    def draw_left_y_axis_labels(self, painter, chart_area):
        """繪製左Y軸刻度和標籤 - 考慮縮放和偏移"""
        left_series = [s for s in self.data_series if s.y_axis == "left"]
        if not left_series:
            return
        
        y_min, y_max = self.get_y_range_for_axis("left")
        if y_max == y_min:
            return
        
        # 考慮縮放和偏移的可視範圍計算
        # 計算當前可視區域對應的數據範圍
        visible_y_range = (y_max - y_min) / self.y_scale
        visible_y_center = y_min + (y_max - y_min) * 0.5
        
        # 根據偏移調整中心點
        offset_factor = -self.y_offset / (chart_area.height() * self.y_scale)
        visible_y_center += (y_max - y_min) * offset_factor
        
        # 計算可視Y軸範圍
        visible_y_min = visible_y_center - visible_y_range * 0.5
        visible_y_max = visible_y_center + visible_y_range * 0.5
        
        #print(f"[DEBUG] 左Y軸可視範圍: {visible_y_min:.2f} - {visible_y_max:.2f} (縮放: {self.y_scale:.2f}, 偏移: {self.y_offset})")
        
        # 繪製5個主要刻度 - 基於可視範圍
        for i in range(6):
            y_value = visible_y_min + (visible_y_max - visible_y_min) * i / 5
            screen_y = int(chart_area.bottom() - chart_area.height() * i / 5)
            
            # 繪製刻度線
            painter.drawLine(chart_area.left() - 5, screen_y, chart_area.left(), screen_y)
            
            # 繪製標籤 - 顯示實際數值，位置動態適應邊距
            label = f"{y_value:.1f}"
            # 確保標籤在邊距範圍內，最少留5像素邊距
            label_x = max(5, chart_area.left() - int(self.margin_left * 0.7))
            painter.drawText(label_x, screen_y + 5, label)
    
    def draw_right_y_axis_labels(self, painter, chart_area):
        """繪製右Y軸刻度和標籤 - 考慮縮放和偏移"""
        right_series = [s for s in self.data_series if s.y_axis == "right"]
        if not right_series:
            return
        
        y_min, y_max = self.get_y_range_for_axis("right")
        if y_max == y_min:
            return
        
        # 考慮縮放和偏移的可視範圍計算
        # 計算當前可視區域對應的數據範圍
        visible_y_range = (y_max - y_min) / self.right_y_scale
        visible_y_center = y_min + (y_max - y_min) * 0.5
        
        # 根據偏移調整中心點
        offset_factor = -self.right_y_offset / (chart_area.height() * self.right_y_scale)
        visible_y_center += (y_max - y_min) * offset_factor
        
        # 計算可視Y軸範圍
        visible_y_min = visible_y_center - visible_y_range * 0.5
        visible_y_max = visible_y_center + visible_y_range * 0.5
        
        #print(f"[DEBUG] 右Y軸可視範圍: {visible_y_min:.2f} - {visible_y_max:.2f} (縮放: {self.right_y_scale:.2f}, 偏移: {self.right_y_offset})")
        
        # 繪製5個主要刻度 - 基於可視範圍
        for i in range(6):
            y_value = visible_y_min + (visible_y_max - visible_y_min) * i / 5
            screen_y = int(chart_area.bottom() - chart_area.height() * i / 5)
            
            # 繪製刻度線
            painter.drawLine(chart_area.right(), screen_y, chart_area.right() + 5, screen_y)
            
            # 繪製標籤 - 顯示實際數值，動態調整位置，增加與軸線的距離
            label = f"{y_value:.1f}"
            # 增加標籤與右Y軸的距離，右邊間距保持5像素
            label_x = min(chart_area.right() + 15, self.width() - 5)
            painter.drawText(label_x, screen_y + 5, label)
    
    def draw_grid(self, painter, chart_area):
        """繪製網格 - 與X軸刻度對齊，考慮縮放和偏移"""
        painter.setPen(QPen(QColor(220, 220, 220), 1))  # 淺灰色網格線
        
        # 垂直網格線 - 使用與X軸刻度相同的間距和縮放偏移
        x_min, x_max = self.get_overall_x_range()
        if x_max != x_min:
            # 考慮縮放和偏移的可視範圍計算
            visible_x_range = (x_max - x_min) / self.x_scale
            visible_x_center = x_min + (x_max - x_min) * 0.5
            
            # 根據偏移調整中心點
            offset_factor = -self.x_offset / (chart_area.width() * self.x_scale)
            visible_x_center += (x_max - x_min) * offset_factor
            
            # 計算可視X軸範圍
            visible_x_min = visible_x_center - visible_x_range * 0.5
            visible_x_max = visible_x_center + visible_x_range * 0.5
            
            interval_seconds = self.x_axis_interval_minutes * 60
            start_tick = int(visible_x_min / interval_seconds) * interval_seconds
            current_tick = start_tick
            
            while current_tick <= visible_x_max:
                if current_tick >= visible_x_min:
                    progress = (current_tick - visible_x_min) / (visible_x_max - visible_x_min)
                    x = int(chart_area.left() + chart_area.width() * progress)
                    
                    # 確保網格線在圖表區域內
                    if x >= chart_area.left() and x <= chart_area.right():
                        painter.drawLine(x, chart_area.top(), x, chart_area.bottom())
                current_tick += interval_seconds
        
        # 水平網格線 - 保持原有的等間距
        for i in range(1, 10):
            y = int(chart_area.top() + (chart_area.height() * i / 10))
            painter.drawLine(chart_area.left(), y, chart_area.right(), y)
    
    def draw_annotations(self, painter, chart_area):
        """舊的標註繪製方法 - 已停用，改用直接繪製"""
        return  # 停用舊的 annotation 系統
        
        x_min, x_max = self.get_overall_x_range()
        if x_max == x_min:
            logger.debug("[ANNOTATION_DEBUG] X軸範圍無效，跳過")
            return
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[ANNOTATION_DEBUG] X軸數據範圍: %s - %s", x_min, x_max)
            logger.debug("[ANNOTATION_DEBUG] 圖表區域: %s", chart_area)
            logger.debug("[ANNOTATION_DEBUG] 縮放: %s, 偏移: %s", self.x_scale, self.x_offset)
        
        # 考慮縮放和偏移的可視範圍計算
        visible_x_range = (x_max - x_min) / self.x_scale
        visible_x_center = x_min + (x_max - x_min) * 0.5
        
        # 根據偏移調整中心點
        offset_factor = -self.x_offset / (chart_area.width() * self.x_scale)
        visible_x_center += (x_max - x_min) * offset_factor
        
        # 計算可視X軸範圍
        visible_x_min = visible_x_center - visible_x_range * 0.5
        visible_x_max = visible_x_center + visible_x_range * 0.5
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[ANNOTATION_DEBUG] 可視範圍: %s - %s", visible_x_min, visible_x_max)
        
        rendered_count = 0
        for i, annotation in enumerate(self.annotations):
            logger.debug(
                "[ANNOTATION_DEBUG] 標註 %d: start_x=%s, end_x=%s, type=%s",
                i + 1,
                annotation.start_x,
                annotation.end_x,
                annotation.annotation_type,
            )
            
            # 對於 background_fill，start_x 和 end_x 已經是螢幕座標
            if annotation.annotation_type == 'background_fill':
                start_screen_x = int(annotation.start_x)
                end_screen_x = int(annotation.end_x)
                
                # 確保最小寬度至少 1 像素
                if end_screen_x <= start_screen_x:
                    end_screen_x = start_screen_x + 1
                    
                logger.debug(
                    "[ANNOTATION_DEBUG] 直接使用螢幕座標: %s - %s (寬度: %s)",
                    start_screen_x,
                    end_screen_x,
                    end_screen_x - start_screen_x,
                )
                
                # 檢查是否在圖表區域內
                if end_screen_x < chart_area.left() or start_screen_x > chart_area.right():
                    logger.debug("[ANNOTATION_DEBUG] 標註 %d 超出圖表區域，跳過", i + 1)
                    continue
                    
                logger.debug("[ANNOTATION_DEBUG] 標註 %d 在圖表區域內，開始繪製", i + 1)
                
                # 裁切到圖表區域
                start_screen_x = max(chart_area.left(), start_screen_x)
                end_screen_x = min(chart_area.right(), end_screen_x)
                
                logger.debug(
                    "[ANNOTATION_DEBUG] 裁切後座標: %s - %s",
                    start_screen_x,
                    end_screen_x,
                )
                
            else:
                # 其他類型的標註使用原有邏輯
                logger.debug(
                    "[ANNOTATION_DEBUG] 處理標註: type=%s, start_x=%s, end_x=%s",
                    annotation.annotation_type,
                    annotation.start_x,
                    annotation.end_x,
                )
                logger.debug("[ANNOTATION_DEBUG] 可視範圍: %s - %s", visible_x_min, visible_x_max)
                
                # 檢查標註是否在可視範圍內
                if annotation.end_x < visible_x_min or annotation.start_x > visible_x_max:
                    logger.debug("[ANNOTATION_DEBUG] 標註 %d 超出可視範圍，跳過", i + 1)
                    continue
                
                logger.debug("[ANNOTATION_DEBUG] 標註 %d 在可視範圍內，開始繪製", i + 1)
                
                # 計算標註的X座標範圍 - 基於可視範圍
                start_progress = max(0, (annotation.start_x - visible_x_min) / (visible_x_max - visible_x_min))
                end_progress = min(1, (annotation.end_x - visible_x_min) / (visible_x_max - visible_x_min))
                
                start_screen_x = int(chart_area.left() + start_progress * chart_area.width())
                end_screen_x = int(chart_area.left() + end_progress * chart_area.width())
                
                logger.debug(
                    "[ANNOTATION_DEBUG] 進度: %s - %s",
                    start_progress,
                    end_progress,
                )
                logger.debug(
                    "[ANNOTATION_DEBUG] 螢幕座標: %s - %s",
                    start_screen_x,
                    end_screen_x,
                )
                
                # 確保標註在圖表區域內
                start_screen_x = max(chart_area.left(), start_screen_x)
                end_screen_x = min(chart_area.right(), end_screen_x)
                
                logger.debug(
                    "[ANNOTATION_DEBUG] 裁切後座標: %s - %s",
                    start_screen_x,
                    end_screen_x,
                )
            
            # 繪製標註區域
            if annotation.annotation_type == "rain":
                # 降雨標註：半透明藍色區域
                painter.setPen(QPen(QColor(0, 150, 255, 100), 1))
                painter.setBrush(QBrush(QColor(0, 150, 255, 50)))
            elif annotation.annotation_type == "background_fill":
                # 降雨背景填充：使用指定的顏色
                logger.debug(
                    "[RENDER_DEBUG] 繪製背景填充: %s, 強度: %s",
                    annotation.color,
                    getattr(annotation, 'intensity', 'unknown'),
                )
                # 解析 rgba 顏色字符串
                if annotation.color.startswith('rgba('):
                    # 提取 rgba 數值
                    rgba_str = annotation.color[5:-1]  # 移除 'rgba(' 和 ')'
                    rgba_values = [float(x.strip()) for x in rgba_str.split(',')]
                    if len(rgba_values) == 4:
                        r, g, b, a = rgba_values
                        color = QColor(int(r), int(g), int(b), int(a * 255))
                        painter.setPen(QPen(color, 1))
                        painter.setBrush(QBrush(color))
                        logger.debug(
                            "[RENDER_DEBUG] 使用顏色: R=%d, G=%d, B=%d, A=%d",
                            int(r),
                            int(g),
                            int(b),
                            int(a * 255),
                        )
                    else:
                        # 預設為半透明黃色
                        painter.setPen(QPen(QColor(255, 255, 0, 100), 1))
                        painter.setBrush(QBrush(QColor(255, 255, 0, 50)))
                else:
                    # 預設為半透明黃色
                    painter.setPen(QPen(QColor(255, 255, 0, 100), 1))
                    painter.setBrush(QBrush(QColor(255, 255, 0, 50)))
            else:
                # 其他標註：半透明黃色區域
                painter.setPen(QPen(QColor(255, 255, 0, 100), 1))
                painter.setBrush(QBrush(QColor(255, 255, 0, 50)))
            
            # 繪製標註矩形
            painter.drawRect(start_screen_x, chart_area.top(), 
                           end_screen_x - start_screen_x, chart_area.height())
            
            # 繪製標註文字
            if annotation.label:
                painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色標註文字
                painter.setFont(QFont("Arial", self.legend_font_size))
                painter.drawText(start_screen_x + 5, chart_area.top() + 15, annotation.label)
    
    def draw_data_series(self, painter, chart_area):
        """繪製所有數據系列"""
        # 移除DEBUG輸出防止無限循環
        x_min, x_max = self.get_overall_x_range()
        
        if x_max == x_min:
            return
        
        # 先繪製降雨背景區間
        self.draw_rain_backgrounds(painter, chart_area, x_min, x_max)
        
        for i, series in enumerate(self.data_series):
            self.draw_single_series(painter, chart_area, series, x_min, x_max)
    
    def draw_rain_backgrounds(self, painter, chart_area, x_min, x_max):
        """直接繪製降雨背景區間 - 使用與溫度/風速相同的邏輯"""
        if not hasattr(self, 'background_regions') or not self.background_regions:
            return
        
        painter.save()
        
        for region in self.background_regions:
            # 檢查是否為降雨背景區間
            if region.get('type') not in ['background_region', 'rain_background', 'rain_intensity']:
                continue
                
            start_time = region['start_time']
            end_time = region['end_time']
            color_str = region['color']
            
            # 轉換時間字串為秒數 (不是座標)
            start_seconds = self.time_to_seconds(start_time)
            end_seconds = self.time_to_seconds(end_time)
            
            # 轉換為螢幕座標 - 使用與溫度/風速相同的邏輯
            x_range = x_max - x_min
            if x_range <= 0:
                continue
                
            start_progress = (start_seconds - x_min) / x_range
            end_progress = (end_seconds - x_min) / x_range
            
            x1 = chart_area.left() + start_progress * chart_area.width()
            x2 = chart_area.left() + end_progress * chart_area.width()
            
            # 解析顏色
            if color_str.startswith('rgba('):
                # 提取 rgba 數值
                rgba_str = color_str[5:-1]  # 移除 'rgba(' 和 ')'
                rgba_values = [float(x.strip()) for x in rgba_str.split(',')]
                if len(rgba_values) == 4:
                    r, g, b, a = rgba_values
                    # 轉換透明度 (0.3 -> 76)
                    alpha_255 = int(a * 255)
                    a = alpha_255
                else:
                    r, g, b, a = 128, 128, 128, 128  # 預設灰色
            else:
                r, g, b, a = 128, 128, 128, 128  # 預設灰色
            
            # 設定顏色並繪製
            color = QColor(int(r), int(g), int(b), int(a))
            brush = QBrush(color)
            painter.fillRect(int(x1), chart_area.top(), int(x2 - x1), chart_area.height(), brush)
        
        painter.restore()
    
    def draw_single_series(self, painter, chart_area, series, x_min, x_max):
        """繪製單個數據系列"""
        # 移除DEBUG輸出防止無限循環
        if len(series.x_data) != len(series.y_data) or len(series.x_data) == 0:
            return
        
        # 獲取Y軸範圍
        if series.y_axis == "left":
            y_min, y_max = self.get_y_range_for_axis("left")
            y_scale = self.y_scale
            y_offset = self.y_offset
        else:
            y_min, y_max = self.get_y_range_for_axis("right")
            y_scale = self.right_y_scale
            y_offset = self.right_y_offset
        
        #print(f"[DEBUG] Y範圍: {y_min} to {y_max}")
        
        if y_max == y_min:
            #print(f"[DEBUG] Y範圍無效，停止繪製")
            return
        
        # 設置線條樣式 - 確保顏色亮度足夠
        color = QColor(series.color) if isinstance(series.color, str) else series.color
        
        # 檢查並調整顏色亮度，避免與深灰背景重疊
        if color.lightness() < 100:  # 如果顏色太暗
            color = color.lighter(200)  # 調亮200%
        
        # 設定畫筆（包含線條樣式）
        painter.setPen(QPen(color, series.line_width, series.line_style))
        
        # 轉換數據點為螢幕座標並繪製
        points = []
        # print(f"[DEBUG] 座標轉換參數:")
        # print(f"   chart_area: left={chart_area.left()}, bottom={chart_area.bottom()}, width={chart_area.width()}, height={chart_area.height()}")
        # print(f"   X範圍: {x_min} - {x_max}")
        # print(f"   Y範圍: {y_min} - {y_max}")
        # print(f"   縮放: x_scale={self.x_scale}, y_scale={y_scale}")
        # print(f"   偏移: x_offset={self.x_offset}, y_offset={y_offset}")
        
        for i in range(len(series.x_data)):
            x_data_val = series.x_data[i]
            y_data_val = series.y_data[i]
            
            # X座標轉換 - 考慮縮放和偏移的可視範圍
            visible_x_range = (x_max - x_min) / self.x_scale
            visible_x_center = x_min + (x_max - x_min) * 0.5
            offset_factor = -self.x_offset / (chart_area.width() * self.x_scale)
            visible_x_center += (x_max - x_min) * offset_factor
            visible_x_min = visible_x_center - visible_x_range * 0.5
            visible_x_max = visible_x_center + visible_x_range * 0.5
            
            if visible_x_max != visible_x_min:
                x_progress = (x_data_val - visible_x_min) / (visible_x_max - visible_x_min)
                screen_x = chart_area.left() + x_progress * chart_area.width()
            else:
                screen_x = chart_area.left()
            
            # Y座標轉換 - 考慮縮放和偏移的可視範圍
            visible_y_range = (y_max - y_min) / y_scale
            visible_y_center = y_min + (y_max - y_min) * 0.5
            y_offset_factor = -y_offset / (chart_area.height() * y_scale)
            visible_y_center += (y_max - y_min) * y_offset_factor
            visible_y_min = visible_y_center - visible_y_range * 0.5
            visible_y_max = visible_y_center + visible_y_range * 0.5
            
            if visible_y_max != visible_y_min:
                y_progress = (y_data_val - visible_y_min) / (visible_y_max - visible_y_min)
                screen_y = chart_area.bottom() - y_progress * chart_area.height()
            else:
                screen_y = chart_area.bottom()
            
            # if i < 3:  # 只顯示前3個點的詳細轉換
            #     print(f"[DEBUG] 點{i}: 數據({x_data_val:.2f}, {y_data_val:.2f}) -> 螢幕({screen_x:.1f}, {screen_y:.1f})")
            #     print(f"   X轉換: {x_data_val:.2f} -> 標準化{x_normalized:.6f} -> 原始螢幕{screen_x_raw:.1f} -> 最終{screen_x:.1f}")
            #     print(f"   Y轉換: {y_data_val:.2f} -> 標準化{y_normalized:.6f} -> 原始螢幕{screen_y_raw:.1f} -> 最終{screen_y:.1f}")
            
            points.append(QPointF(screen_x, screen_y))
        
        # print(f"[DEBUG] 轉換了 {len(points)} 個點")
        # if len(points) > 0:
        #     print(f"[DEBUG] 第一個點: ({points[0].x()}, {points[0].y()})")
        #     print(f"[DEBUG] 最後一個點: ({points[-1].x()}, {points[-1].y()})")
        
        # 繪製連續線條和數據點
        line_count = 0
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            line_count += 1
        
        # 🆕 繪製數據點（線+點模式）
        if self.show_data_points:
            for point in points:
                # 🔧 跳過包含 NaN 的點
                if not (math.isnan(point.x()) or math.isnan(point.y())):
                    painter.drawEllipse(point, self.data_point_radius, self.data_point_radius)
        
        # print(f"[DEBUG] 繪製了 {line_count} 條線段")
    
    def draw_fixed_vertical_lines(self, painter, chart_area):
        """繪製固定的垂直虛線（不顯示座標數值）"""
        if not self.fixed_vertical_lines:
            return
        
        painter.setPen(QPen(QColor(255, 100, 100), 3, Qt.DashDotLine))  # 紅色虛點線
        
        for line in self.fixed_vertical_lines:
            # 只繪製垂直線，不顯示數值標籤
            painter.drawLine(line['screen_x'], chart_area.top(), line['screen_x'], chart_area.bottom())
    
    def draw_hover_and_pinned_data_points(self, painter, chart_area):
        """繪製懸停和固定的數據點高亮圈與 Tooltip（參考 Detailed Lap Analysis）"""
        # 繪製固定的數據點（淺藍色圓圈）
        if self.pinned_data_points:
            painter.setPen(QPen(QColor(100, 150, 255), 2))  # 藍色邊框
            painter.setBrush(QBrush(Qt.NoBrush))  # 不填充
            
            for pinned in self.pinned_data_points:
                screen_pos = pinned['screen_pos']
                painter.drawEllipse(screen_pos, 12, 12)  # 繪製高亮圓圈
        
        # 繪製懸停的數據點（黃色圓圈）
        if self.hover_data_point:
            painter.setPen(QPen(QColor(255, 200, 0), 2))  # 黃色邊框
            painter.setBrush(QBrush(Qt.NoBrush))
            screen_pos = self.hover_data_point['screen_pos']
            painter.drawEllipse(screen_pos, 12, 12)  # 繪製高亮圓圈
            
            # 繪製懸停 Tooltip
            self._draw_data_point_tooltip(painter, self.hover_data_point, is_pinned=False)
        
        # 繪製固定 Tooltip
        for i, pinned in enumerate(self.pinned_data_points):
            self._draw_data_point_tooltip(painter, pinned, is_pinned=True, pinned_index=i)
    
    def _draw_data_point_tooltip(self, painter, data_point, is_pinned=False, pinned_index=-1):
        """
        繪製數據點 Tooltip（參考 Detailed Lap Analysis）
        
        Args:
            painter: QPainter 物件
            data_point: 數據點資訊字典
            is_pinned: 是否為固定的 tooltip
            pinned_index: 如果是固定 tooltip，其在 pinned_data_points 中的索引
        """
        series_idx = data_point['series_idx']
        point_idx = data_point['point_idx']
        x_val = data_point['x']
        y_val = data_point['y']
        screen_pos = data_point['screen_pos']
        
        # 獲取系列名稱
        series_name = self.data_series[series_idx].name if series_idx < len(self.data_series) else "未知"
        
        # 🆕 嘗試使用自定義的 tooltip 格式化方法（Throttle Line Chart 專用）
        lines = []
        lap_number = int(round(x_val))  # X 軸通常是 Lap 編號
        if hasattr(self, 'format_tooltip_for_data_point'):
            # 新版本：傳入 series_name 參數（支援雙車手模式）
            try:
                lines = self.format_tooltip_for_data_point(lap_number, series_name)
            except TypeError:
                # 向下相容：舊版本不接受 series_name 參數
                lines = self.format_tooltip_for_data_point(lap_number)
        
        # 如果沒有自定義方法或返回空列表，使用默認格式
        if not lines:
            lines = [
                f"系列: {series_name}",
                f"X: {x_val:.2f}",
                f"Y: {y_val:.2f}",
            ]
        
        # 計算 Tooltip 尺寸
        fm = painter.fontMetrics()
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
        
        # 🆕 檢查是否有自訂位置
        if is_pinned and 'custom_pos' in data_point and data_point['custom_pos'] is not None:
            # 使用自訂位置
            tooltip_x = data_point['custom_pos'].x()
            tooltip_y = data_point['custom_pos'].y()
        else:
            # 計算預設 Tooltip 位置（在數據點右上方）
            offset_x = 15
            offset_y = -15
            tooltip_x = screen_pos.x() + offset_x
            tooltip_y = screen_pos.y() + offset_y - tooltip_height
            
            # 確保 Tooltip 不超出視窗
            if tooltip_x + tooltip_width > self.width():
                tooltip_x = screen_pos.x() - tooltip_width - 15
            if tooltip_y < 0:
                tooltip_y = screen_pos.y() + 15
        
        # 🆕 儲存 tooltip 矩形（用於拖動檢測）
        tooltip_rect = QRect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        if is_pinned and pinned_index >= 0:
            data_point['tooltip_rect'] = tooltip_rect
        
        # 🆕 如果是固定 tooltip，繪製連接線（數據點 → tooltip）
        if is_pinned:
            painter.save()
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.DashLine))
            # 從數據點繪製到 tooltip 的中心
            tooltip_center_x = tooltip_x + tooltip_width // 2
            tooltip_center_y = tooltip_y + tooltip_height // 2
            painter.drawLine(screen_pos.x(), screen_pos.y(), tooltip_center_x, tooltip_center_y)
            painter.restore()
        
        # 繪製背景（懸停=淺黃色，固定=淺藍色）
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
    
    def draw_mouse_values(self, painter, chart_area, screen_x):
        """繪製滑鼠位置的即時數值"""
        data_x = self.screen_to_data_x(screen_x)
        left_y = self.get_y_value_at_x(data_x, "left")
        right_y = self.get_y_value_at_x(data_x, "right")
        
        # 設置半透明背景
        painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色數值文字
        painter.setFont(QFont("Arial", 9))
        
        # 在虛線旁邊顯示數值
        text_x = screen_x + 10
        text_y = chart_area.top() + 20
        
        painter.drawText(text_x, text_y, f"X: {data_x:.2f}")
        if left_y is not None:
            painter.drawText(text_x, text_y + 15, f"左Y: {left_y:.2f}")
        if right_y is not None and self.show_right_y_axis:
            painter.drawText(text_x, text_y + 30, f"右Y: {right_y:.2f}")
    
    def draw_value_labels(self, painter, chart_area, screen_x, data_x, left_y, right_y):
        """繪製固定虛線的數值標籤"""
        # 設置醒目的背景和文字
        painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色固定線文字
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))  # 白色半透明背景
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        
        # 計算標籤位置
        label_x = screen_x + 5
        label_y = chart_area.top() + 10
        
        # 繪製背景矩形
        label_width = 100
        label_height = 45 if self.show_right_y_axis else 30
        painter.drawRect(label_x, label_y, label_width, label_height)
        
        # 繪製文字
        painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色文字
        painter.drawText(label_x + 5, label_y + 15, f"X: {data_x:.2f}")
        if left_y is not None:
            painter.drawText(label_x + 5, label_y + 30, f"左Y: {left_y:.2f}")
        if right_y is not None and self.show_right_y_axis:
            painter.drawText(label_x + 5, label_y + 45, f"右Y: {right_y:.2f}")
    
    def _check_hover_data_point(self, mouse_pos):
        """檢查滑鼠是否懸停在數據點上（參考 Detailed Lap Analysis）"""
        if not self.data_series:
            self.hover_data_point = None
            return
        
        chart_area = self.get_chart_area()
        if not chart_area.isValid():
            self.hover_data_point = None
            return
        
        # 搜索最近的數據點
        closest_distance = self.data_point_search_radius
        closest_point = None
        
        for series_idx, series in enumerate(self.data_series):
            for point_idx, (x_val, y_val) in enumerate(zip(series.x_data, series.y_data)):
                # 🔧 跳過 NaN 值
                if math.isnan(x_val) or math.isnan(y_val):
                    continue
                
                # 座標轉換：數據座標 → 螢幕座標
                screen_x, screen_y = self._data_to_screen(x_val, y_val, series.y_axis, chart_area)
                
                # 🔧 檢查轉換結果是否為 NaN
                if math.isnan(screen_x) or math.isnan(screen_y):
                    continue
                
                screen_point = QPoint(int(screen_x), int(screen_y))
                
                # 計算滑鼠與數據點的距離
                distance = math.sqrt((mouse_pos.x() - screen_x)**2 + (mouse_pos.y() - screen_y)**2)
                
                if distance < closest_distance:
                    closest_distance = distance
                    closest_point = {
                        'series_idx': series_idx,
                        'point_idx': point_idx,
                        'x': x_val,
                        'y': y_val,
                        'screen_pos': screen_point
                    }
        
        self.hover_data_point = closest_point
    
    def _data_to_screen(self, x_val, y_val, y_axis, chart_area):
        """數據座標轉換為螢幕座標"""
        # 獲取數據範圍
        x_range = self.get_overall_x_range()
        left_y_range = self.get_overall_left_y_range()
        right_y_range = self.get_overall_right_y_range() if self.show_right_y_axis else (0, 1)
        
        x_min, x_max = x_range
        left_y_min, left_y_max = left_y_range
        right_y_min, right_y_max = right_y_range
        
        # 選擇 Y 軸範圍
        if y_axis == "right":
            y_min, y_max = right_y_min, right_y_max
            y_scale = self.right_y_scale
            y_offset = self.right_y_offset
        else:
            y_min, y_max = left_y_min, left_y_max
            y_scale = self.y_scale
            y_offset = self.y_offset
        
        # X 座標轉換
        visible_x_range = (x_max - x_min) / self.x_scale
        visible_x_center = x_min + (x_max - x_min) * 0.5
        x_offset_factor = -self.x_offset / (chart_area.width() * self.x_scale)
        visible_x_center += (x_max - x_min) * x_offset_factor
        visible_x_min = visible_x_center - visible_x_range * 0.5
        visible_x_max = visible_x_center + visible_x_range * 0.5
        
        if visible_x_max != visible_x_min:
            x_progress = (x_val - visible_x_min) / (visible_x_max - visible_x_min)
            screen_x = chart_area.left() + x_progress * chart_area.width()
        else:
            screen_x = chart_area.left()
        
        # Y 座標轉換
        visible_y_range = (y_max - y_min) / y_scale
        visible_y_center = y_min + (y_max - y_min) * 0.5
        y_offset_factor = -y_offset / (chart_area.height() * y_scale)
        visible_y_center += (y_max - y_min) * y_offset_factor
        visible_y_min = visible_y_center - visible_y_range * 0.5
        visible_y_max = visible_y_center + visible_y_range * 0.5
        
        if visible_y_max != visible_y_min:
            y_progress = (y_val - visible_y_min) / (visible_y_max - visible_y_min)
            screen_y = chart_area.bottom() - y_progress * chart_area.height()
        else:
            screen_y = chart_area.bottom()
        
        return screen_x, screen_y
    
    def _pin_data_point(self):
        """固定當前懸停的數據點（最多2個）"""
        if not self.hover_data_point:
            return
        
        # 檢查是否已固定（避免重複）
        for pinned in self.pinned_data_points:
            if (pinned['series_idx'] == self.hover_data_point['series_idx'] and
                pinned['point_idx'] == self.hover_data_point['point_idx']):
                logger.debug("[DEBUG] 該數據點已固定，跳過")
                return
        
        # 限制最多2個固定點
        if len(self.pinned_data_points) >= 2:
            # 移除最舊的固定點
            removed = self.pinned_data_points.pop(0)
            logger.debug(
                "[DEBUG] 固定點已達上限，移除最舊的: 系列%s 點%s",
                removed['series_idx'],
                removed['point_idx'],
            )
        
        # 添加新的固定點，初始化 tooltip_rect 和 custom_pos
        new_pinned = dict(self.hover_data_point)
        new_pinned['tooltip_rect'] = None  # 將在繪製時計算
        new_pinned['custom_pos'] = None  # 自訂位置，初始為 None（使用預設位置）
        self.pinned_data_points.append(new_pinned)
        logger.debug(
            "[DEBUG] 固定數據點: 系列%s 點%s",
            self.hover_data_point['series_idx'],
            self.hover_data_point['point_idx'],
        )
        self.update()
    
    def reset_view(self):
        """重置視圖縮放和偏移到預設值"""
        logger.info("[DEBUG] 重置通用圖表視圖")
        self.x_scale = 1.0
        self.y_scale = 1.0
        self.x_offset = 0
        self.y_offset = 0
        self.right_y_scale = 1.0
        self.right_y_offset = 0
        
        # 清除固定虛線
        self.fixed_vertical_lines.clear()
        
        # 🆕 清除固定數據點
        self.pinned_data_points.clear()
        self.hover_data_point = None
        
        # 重置滑鼠狀態
        self.mouse_x = -1
        self.mouse_y = -1
        self.dragging = False
        self.setCursor(Qt.ArrowCursor)
        
        self.update()
        logger.info("[DEBUG] 通用圖表視圖已重置，清除了固定虛線和數據點")
    
    def fit_to_view(self):
        """調整視圖以適應所有數據"""
        self.reset_view()
    
    def zoom_to_fit(self):
        """縮放以適應所有數據"""
        self.reset_view()
    
    def clear_fixed_lines(self):
        """清除所有固定虛線"""
        self.fixed_vertical_lines.clear()
        self.update()
        logger.debug("[DEBUG] 已清除所有固定虛線")
    
    def toggle_value_tooltips(self):
        """切換數值提示顯示"""
        self.show_value_tooltips = not self.show_value_tooltips
        self.update()
        logger.debug("[DEBUG] 數值提示: %s", '開啟' if self.show_value_tooltips else '關閉')
    
    def draw_legend(self, painter):
        """繪製可拖拉的圖例"""
        if not self.data_series:
            self.legend_rect = None
            return
        
        painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色圖例文字
        font = QFont("Arial", self.legend_font_size)
        painter.setFont(font)
        
        # 計算圖例尺寸
        line_height = 20
        padding = 8
        color_line_width = 20
        text_offset = 25
        
        # 計算所有文字的最大寬度
        max_text_width = 0
        for series in self.data_series:
            # 不再顯示軸標示 (左/右)
            text = series.name
            text_width = painter.fontMetrics().width(text)
            max_text_width = max(max_text_width, text_width)
        
        # 計算圖例矩形
        legend_width = color_line_width + text_offset + max_text_width + padding * 2
        legend_height = len(self.data_series) * line_height + padding * 2
        
        legend_x = self.legend_position.x()
        legend_y = self.legend_position.y()
        
        # 儲存圖例矩形供碰撞檢測使用
        from PyQt5.QtCore import QRect
        self.legend_rect = QRect(legend_x - padding, legend_y - padding, 
                                  legend_width, legend_height)
        
        # 繪製半透明背景
        painter.save()
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))  # 白色半透明背景
        painter.setPen(QPen(QColor(100, 100, 100), 1))  # 灰色邊框
        painter.drawRoundedRect(self.legend_rect, 5, 5)
        painter.restore()
        
        # 繪製圖例項目
        for i, series in enumerate(self.data_series):
            y_pos = legend_y + i * line_height
            
            # 繪製顏色線條（包含線條樣式）
            color = QColor(series.color) if isinstance(series.color, str) else series.color
            painter.setPen(QPen(color, series.line_width, series.line_style))
            painter.drawLine(legend_x, y_pos, legend_x + color_line_width, y_pos)
            
            # 繪製系列名稱
            painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色圖例文字
            # 不再顯示軸標示 (左/右)
            painter.drawText(legend_x + text_offset, y_pos + 5, series.name)
    
    # 滑鼠事件處理系統 - 完整版
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 處理圖例拖拉、tooltip 拖動、數據點固定、圖表拖拉和固定虛線"""
        # 優先檢查是否點擊圖例（阻止所有其他互動）
        if self.legend_rect and self.legend_rect.contains(event.pos()):
            if event.button() == Qt.LeftButton:
                # 開始拖拉圖例
                self.legend_dragging = True
                self.legend_drag_offset = event.pos() - self.legend_position
                self.setCursor(Qt.ClosedHandCursor)
                logger.debug("[DEBUG] 開始拖拉圖例")
            # 無論按哪個按鈕，點擊圖例時都阻止後續處理
            event.accept()
            return
        
        # 檢查是否在圖表區域
        chart_area = self.get_chart_area()
        if chart_area.contains(event.pos()):
            if event.button() == Qt.LeftButton:
                # 🆕 【最優先】檢查是否點擊已固定的 tooltip 框（用於拖動）
                for i, pinned_point in enumerate(self.pinned_data_points):
                    tooltip_rect = pinned_point.get('tooltip_rect')
                    if tooltip_rect and tooltip_rect.contains(event.pos()):
                        # 開始拖動此 tooltip
                        self.dragging_tooltip = True
                        self.dragging_tooltip_index = i
                        self.tooltip_drag_offset = event.pos() - QPoint(tooltip_rect.x(), tooltip_rect.y())
                        self.setCursor(Qt.ClosedHandCursor)
                        logger.debug("[DEBUG] 開始拖動 Tooltip #%d", i)
                        event.accept()
                        return
                
                # 🆕 其次檢查是否點擊數據點（參考 Detailed Lap Analysis）
                if self.hover_data_point and self.show_data_points:
                    # 固定當前懸停的數據點（最多2個）
                    self._pin_data_point()
                    event.accept()
                    return
                
                modifiers = event.modifiers()
                
                if modifiers & Qt.ControlModifier:
                    # Ctrl + 左鍵: 固定垂直虛線並顯示Y軸值
                    self.add_fixed_vertical_line(event.pos())
                    logger.debug("[DEBUG] 固定垂直虛線於 X=%s", event.x())
                else:
                    # 純左鍵: 開始拖拉圖表
                    self.dragging = True
                    self.last_drag_pos = event.pos()
                    self.setCursor(Qt.ClosedHandCursor)
                    logger.debug("[DEBUG] 開始拖拉圖表")
                
                event.accept()
            elif event.button() == Qt.RightButton:
                # 🆕 右鍵清除所有固定的數據點
                if self.pinned_data_points:
                    self.pinned_data_points.clear()
                    logger.debug("[DEBUG] 已清除所有固定數據點")
                    self.update()
                    event.accept()
                    return
                
                # 右鍵: 顯示座標軸設定選單
                self.show_axis_context_menu(event.pos())
                event.accept()
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 處理圖例拖拉、tooltip 拖動、數據點檢測、圖表拖拉和虛線追蹤"""
        # 優先處理圖例拖拉
        if self.legend_dragging:
            # 更新圖例位置
            new_pos = event.pos() - self.legend_drag_offset
            # 限制圖例在視窗範圍內
            if self.legend_rect:
                new_pos.setX(max(0, min(new_pos.x(), self.width() - self.legend_rect.width())))
                new_pos.setY(max(0, min(new_pos.y(), self.height() - self.legend_rect.height())))
            self.legend_position = new_pos
            self.update()
            event.accept()
            return
        
        # 🆕 處理 tooltip 拖動
        if self.dragging_tooltip and 0 <= self.dragging_tooltip_index < len(self.pinned_data_points):
            # 計算新位置（滑鼠位置 - 拖動偏移量）
            new_pos = event.pos() - self.tooltip_drag_offset
            
            # 更新 custom_pos
            self.pinned_data_points[self.dragging_tooltip_index]['custom_pos'] = new_pos
            
            logger.debug(
                "[DEBUG] 拖動 Tooltip #%d 到 (%d, %d)",
                self.dragging_tooltip_index,
                new_pos.x(),
                new_pos.y(),
            )
            self.update()
            event.accept()
            return
        
        # 檢查滑鼠是否懸停在圖例上（顯示手型游標）
        if self.legend_rect and self.legend_rect.contains(event.pos()):
            self.setCursor(Qt.OpenHandCursor)
        elif not self.dragging:
            self.setCursor(Qt.ArrowCursor)
        
        # 處理圖表區域
        chart_area = self.get_chart_area()
        if chart_area.contains(event.pos()):
            if self.dragging:
                # 圖表拖拉模式
                delta = event.pos() - self.last_drag_pos
                
                # 更新偏移量
                self.x_offset += delta.x()
                self.y_offset += delta.y()
                if self.show_right_y_axis:
                    self.right_y_offset += delta.y()
                
                self.last_drag_pos = event.pos()
                self.update()
            else:
                # 🆕 檢查是否懸停在數據點上（參考 Detailed Lap Analysis）
                if self.show_data_points:
                    self._check_hover_data_point(event.pos())
                
                # 正常虛線追蹤模式
                self.mouse_x = event.x()
                self.mouse_y = event.y()
                self.update()
        
        event.accept()
    
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖拉和 tooltip 拖動"""
        if event.button() == Qt.LeftButton:
            if self.legend_dragging:
                # 結束圖例拖拉
                self.legend_dragging = False
                self.setCursor(Qt.ArrowCursor)
                logger.debug(
                    "[DEBUG] 圖例拖拉結束，位置: (%d, %d)",
                    self.legend_position.x(),
                    self.legend_position.y(),
                )
                event.accept()
            elif self.dragging_tooltip:
                # 🆕 結束 tooltip 拖動
                logger.debug("[DEBUG] Tooltip 拖動結束，最終位置已儲存")
                self.dragging_tooltip = False
                self.dragging_tooltip_index = -1
                self.tooltip_drag_offset = QPoint(0, 0)
                self.setCursor(Qt.ArrowCursor)
                event.accept()
            elif self.dragging:
                # 結束圖表拖拉
                self.dragging = False
                self.setCursor(Qt.ArrowCursor)
                logger.debug("[DEBUG] 圖表拖拉結束")
                event.accept()
    
    def add_fixed_vertical_line(self, pos):
        """添加固定垂直虛線並計算Y軸值"""
        chart_area = self.get_chart_area()
        if not chart_area.contains(pos):
            return
        
        # 將螢幕座標轉換為數據座標
        x_data_value = self.screen_to_data_x(pos.x())
        
        # 計算對應的Y軸值
        left_y_value = self.get_y_value_at_x(x_data_value, "left")
        right_y_value = self.get_y_value_at_x(x_data_value, "right")
        
        # 添加固定線
        fixed_line = {
            'screen_x': pos.x(),
            'data_x': x_data_value,
            'left_y': left_y_value,
            'right_y': right_y_value
        }
        self.fixed_vertical_lines.append(fixed_line)
        
        logger.debug(
            "[DEBUG] 固定虛線: X=%.2f, 左Y=%.2f, 右Y=%.2f",
            x_data_value,
            left_y_value,
            right_y_value,
        )
    
    def screen_to_data_x(self, screen_x):
        """將螢幕X座標轉換為數據X值"""
        if not self.data_series:
            return 0
        
        chart_area = self.get_chart_area()
        x_min, x_max = self.get_overall_x_range()
        
        # 考慮縮放和偏移的反向轉換
        adjusted_screen_x = (screen_x / self.x_scale) - self.x_offset
        relative_x = (adjusted_screen_x - chart_area.left()) / chart_area.width()
        data_x = x_min + relative_x * (x_max - x_min)
        
        return data_x
    
    def get_y_value_at_x(self, target_x, y_axis="left"):
        """根據X值插值計算對應的Y值"""
        series_for_axis = [s for s in self.data_series if s.y_axis == y_axis]
        if not series_for_axis:
            return 0
        
        # 使用第一個符合的數據系列進行插值
        series = series_for_axis[0]
        x_data = series.x_data
        y_data = series.y_data
        
        if len(x_data) < 2:
            return y_data[0] if y_data else 0
        
        # 線性插值
        for i in range(len(x_data) - 1):
            if x_data[i] <= target_x <= x_data[i + 1]:
                # 線性插值計算
                x1, x2 = x_data[i], x_data[i + 1]
                y1, y2 = y_data[i], y_data[i + 1]
                
                if x2 == x1:
                    return y1
                
                ratio = (target_x - x1) / (x2 - x1)
                interpolated_y = y1 + ratio * (y2 - y1)
                return interpolated_y
        
        # 如果超出範圍，返回最近的值
        if target_x < x_data[0]:
            return y_data[0]
        else:
            return y_data[-1]
    
    def wheelEvent(self, event):
        """滑鼠滾輪縮放 - 改進版支援雙Y軸同時縮放"""
        chart_area = self.get_chart_area()
        if chart_area.contains(event.pos()):
            delta = event.angleDelta().y()
            modifiers = event.modifiers()
            
            if modifiers & Qt.ControlModifier:
                # Ctrl + 滾輪: X軸和Y軸同時縮放
                zoom_factor = 1.2 if delta > 0 else 0.8
                
                # X軸縮放
                self.x_scale *= zoom_factor
                self.x_scale = max(0.1, min(10.0, self.x_scale))
                
                # 左Y軸縮放
                self.y_scale *= zoom_factor
                self.y_scale = max(0.1, min(10.0, self.y_scale))
                
                # 右Y軸同時縮放 (保持同步)
                if self.show_right_y_axis:
                    self.right_y_scale *= zoom_factor
                    self.right_y_scale = max(0.1, min(10.0, self.right_y_scale))
            else:
                # 純滾輪: 僅Y軸縮放 (左右Y軸同時縮放)
                zoom_factor = 1.3 if delta > 0 else 0.7
                
                # 左Y軸縮放
                self.y_scale *= zoom_factor
                self.y_scale = max(0.1, min(10.0, self.y_scale))
                
                # 右Y軸同時縮放 (保持同步)
                if self.show_right_y_axis:
                    self.right_y_scale *= zoom_factor
                    self.right_y_scale = max(0.1, min(10.0, self.right_y_scale))
                
                logger.debug(
                    "[DEBUG] 純滾輪Y軸縮放: 左=%.2f, 右=%.2f",
                    self.y_scale,
                    self.right_y_scale,
                )
            
            self.update()
            event.accept()
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.mouse_x = -1
        self.update()
    
    # ==================== 右鍵選單功能 ====================
    
    def show_axis_context_menu(self, position):
        """顯示座標軸設定右鍵選單"""
        menu = QMenu(self)
        
        # 設定座標軸範圍
        set_range_action = QAction("🎯 設定座標軸範圍...", self)
        set_range_action.triggered.connect(self.show_axis_range_dialog)
        menu.addAction(set_range_action)
        
        # 重置為自動範圍
        reset_range_action = QAction("🔄 重置為自動範圍", self)
        reset_range_action.triggered.connect(self.reset_to_auto_range)
        menu.addAction(reset_range_action)
        
        menu.addSeparator()
        
        # 縮放到數據範圍
        fit_data_action = QAction("📊 縮放到數據範圍", self)
        fit_data_action.triggered.connect(self.fit_to_data_range)
        menu.addAction(fit_data_action)
        
        # 重置視圖
        reset_view_action = QAction("🏠 重置視圖", self)
        reset_view_action.triggered.connect(self.reset_view)
        menu.addAction(reset_view_action)
        
        # 顯示選單
        menu.exec_(self.mapToGlobal(position))
    
    def show_axis_range_dialog(self):
        """顯示座標軸範圍設定對話框"""
        dialog = AxisRangeDialog(self, self)
        if dialog.exec_() == QDialog.Accepted:
            # 應用新的範圍設定
            ranges = dialog.get_ranges()
            
            self.manual_x_range = ranges['x_range']
            self.manual_left_y_range = ranges['left_y_range'] 
            self.manual_right_y_range = ranges['right_y_range']
            self.auto_range_enabled = ranges['auto_range']
            self.x_axis_interval_minutes = ranges['x_interval_minutes']
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[DEBUG] 應用新的座標軸範圍:")
                logger.debug("  X軸: %s", self.manual_x_range)
                logger.debug("  左Y軸: %s", self.manual_left_y_range)
                logger.debug("  右Y軸: %s", self.manual_right_y_range)
                logger.debug("  X軸間距: %s 分鐘", self.x_axis_interval_minutes)
                logger.debug("  自動範圍: %s", self.auto_range_enabled)
            
            # 重新計算和重繪
            self.recalculate_data_ranges()
            self.update()
    
    def reset_to_auto_range(self):
        """重置為自動範圍"""
        self.manual_x_range = None
        self.manual_left_y_range = None
        self.manual_right_y_range = None
        self.auto_range_enabled = True
        
        logger.debug("[DEBUG] 重置為自動座標軸範圍")
        
        # 重新計算和重繪
        self.recalculate_data_ranges()
        self.update()
    
    def fit_to_data_range(self):
        """縮放到數據範圍"""
        if not self.data_series:
            return
        
        # 重置為自動範圍並重新計算
        self.reset_to_auto_range()
        
        # 重置縮放和偏移
        self.x_scale = 1.0
        self.y_scale = 1.0
        self.right_y_scale = 1.0
        self.x_offset = 0
        self.y_offset = 0
        self.right_y_offset = 0
        
        logger.debug("[DEBUG] 縮放到數據範圍")
        self.update()

    def render_rain_background_regions(self, background_regions):
        """設置降雨背景區間數據 - 直接存儲供 draw_rain_backgrounds 使用"""
        logger.debug("[RENDER_DEBUG] 設置 %d 個降雨背景區間", len(background_regions))
        
        # 直接存儲背景區間數據
        self.background_regions = background_regions
        
        logger.info("UniversalChartWidget: 已設置 %d 個降雨背景區間", len(background_regions))
        self.update()  # 觸發重繪
    
    def render_rain_text_markers(self, rain_markers):
        """渲染降雨標記文字到圖表上方 - 符合架構文檔規範"""
        try:
            from PyQt5.QtWidgets import QLabel
            
            for marker in rain_markers:
                # 計算標記在圖表中的位置
                x_position = self.time_to_chart_x(marker["time_position"])
                y_position = self.get_chart_top_margin() - 25  # 圖表上方25像素
                
                # 獲取顏色，支援多種屬性名稱
                color = marker.get("color", 
                                 marker.get("text_color", 
                                          marker.get("marker_style", {}).get("text_color", "#FF6B6B")))
                
                # 創建標記標籤
                marker_label = QLabel(marker["text"], self)
                marker_label.setStyleSheet(f"""
                    QLabel {{
                        color: {color};
                        font-size: 10px;
                        font-weight: bold;
                        background: rgba(255, 255, 255, 180);
                        padding: 2px 4px;
                        border-radius: 3px;
                        border: 1px solid {color};
                    }}
                """)
                
                # 設置位置和顯示
                marker_label.move(int(x_position), int(y_position))
                marker_label.show()
                
                # 儲存到降雨標記列表
                self.rain_text_markers.append(marker_label)
            
            logger.info("UniversalChartWidget: 已渲染 %d 個降雨標記", len(rain_markers))
            
        except Exception as e:
            logger.error("[ERROR] 渲染降雨標記失敗: %s", e)

    def time_to_seconds(self, time_str):
        """將時間字符串轉換為秒數 (不進行座標轉換)"""
        try:
            # 解析時間字符串 (例如: "0:42:19.732")
            parts = time_str.split(":")
            
            if len(parts) == 2:
                # 格式: "MM:SS.mmm"
                minutes = int(parts[0])
                seconds_parts = parts[1].split(".")
                seconds = int(seconds_parts[0])
                milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
                total_seconds = minutes * 60 + seconds + milliseconds / 1000.0
            elif len(parts) == 3:
                # 格式: "H:MM:SS.mmm"
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds_parts = parts[2].split(".")
                seconds = int(seconds_parts[0])
                milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
                total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            else:
                return 0
            
            return total_seconds
            
        except Exception as e:
            logger.warning("[WARNING] 時間字符串轉換失敗: %s, 錯誤: %s", time_str, e)
            return 0

    def time_to_chart_x(self, time_str):
        """將時間字符串轉換為圖表X座標"""
        try:
            # 解析時間字符串 (例如: "0:42:19.732")
            parts = time_str.split(":")
            
            if len(parts) == 2:
                # 格式: "MM:SS.mmm"
                minutes = int(parts[0])
                seconds_parts = parts[1].split(".")
                seconds = int(seconds_parts[0])
                milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
                total_seconds = minutes * 60 + seconds + milliseconds / 1000.0
            elif len(parts) == 3:
                # 格式: "H:MM:SS.mmm"
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds_parts = parts[2].split(".")
                seconds = int(seconds_parts[0])
                milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
                total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            else:
                return 0
            
            # 轉換為圖表X座標
            screen_x = self.data_to_screen_x(total_seconds)
            return screen_x
            
        except Exception as e:
            logger.warning("[WARNING] 時間字符串轉換失敗: %s, 錯誤: %s", time_str, e)
            return 0
    
    def get_chart_top_margin(self):
        """獲取圖表上邊距"""
        return self.margin_top
    
    def data_to_screen_x(self, x_value):
        """將數據X值轉換為螢幕座標"""
        if not self.data_series:
            return self.margin_left
        
        # 從第一個數據系列獲取X軸數據範圍
        x_data = self.data_series[0].x_data
        if not x_data:
            return self.margin_left
        
        # 計算X軸的數據範圍
        x_min = min(x_data)
        x_max = max(x_data)
        x_range = x_max - x_min if x_max != x_min else 1
        
        # 計算圖表區域寬度
        chart_width = self.width() - self.margin_left - self.margin_right
        
        # 轉換為螢幕座標
        normalized_x = (x_value - x_min) / x_range
        screen_x = self.margin_left + normalized_x * chart_width
        
        return screen_x


# ==================== 座標軸範圍設定對話框 ====================

class AxisRangeDialog(QDialog):
    """座標軸範圍設定對話框"""
    
    def __init__(self, chart_widget, parent=None):
        super().__init__(parent)
        self.chart_widget = chart_widget
        self.setWindowTitle("座標軸範圍設定")
        self.setFixedSize(400, 350)
        
        self.init_ui()
        self.load_current_ranges()
    
    def init_ui(self):
        """初始化使用者介面"""
        # 設定對話框樣式
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                color: #333333;
            }
            QGroupBox {
                background-color: #F8F8F8;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 5px;
                font-weight: bold;
                color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #FFFFFF;
                color: #333333;
            }
            QLabel {
                color: #333333;
                font-size: 12px;
            }
            QCheckBox {
                color: #333333;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border: 1px solid #CCCCCC;
                background: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background: #4CAF50;
                border: 1px solid #45A049;
            }
            QDoubleSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 2px;
                color: #333333;
                font-size: 11px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #4CAF50;
            }
            QPushButton {
                background-color: #F8F8F8;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 5px 10px;
                color: #333333;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #E8E8E8;
            }
            QPushButton:pressed {
                background-color: #DDDDDD;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 自動範圍選項
        self.auto_range_checkbox = QCheckBox("使用自動範圍")
        self.auto_range_checkbox.toggled.connect(self.on_auto_range_toggled)
        layout.addWidget(self.auto_range_checkbox)
        
        # 手動範圍設定
        self.manual_group = QGroupBox("手動範圍設定")
        manual_layout = QGridLayout(self.manual_group)
        
        # X軸範圍
        manual_layout.addWidget(QLabel("X軸範圍:"), 0, 0)
        self.x_min_spinbox = QDoubleSpinBox()
        self.x_min_spinbox.setRange(-999999, 999999)
        self.x_min_spinbox.setDecimals(3)
        self.x_max_spinbox = QDoubleSpinBox()
        self.x_max_spinbox.setRange(-999999, 999999)
        self.x_max_spinbox.setDecimals(3)
        manual_layout.addWidget(QLabel("最小值:"), 0, 1)
        manual_layout.addWidget(self.x_min_spinbox, 0, 2)
        manual_layout.addWidget(QLabel("最大值:"), 0, 3)
        manual_layout.addWidget(self.x_max_spinbox, 0, 4)
        
        # X軸間距設定
        manual_layout.addWidget(QLabel("X軸間距(分鐘):"), 1, 0)
        self.x_interval_spinbox = QSpinBox()
        self.x_interval_spinbox.setRange(1, 120)  # 1分鐘到120分鐘
        self.x_interval_spinbox.setValue(15)  # 預設15分鐘
        self.x_interval_spinbox.setSuffix(" 分鐘")
        manual_layout.addWidget(self.x_interval_spinbox, 1, 1, 1, 2)  # 跨兩列
        
        # 左Y軸範圍
        manual_layout.addWidget(QLabel("左Y軸範圍:"), 2, 0)
        self.left_y_min_spinbox = QDoubleSpinBox()
        self.left_y_min_spinbox.setRange(-999999, 999999)
        self.left_y_min_spinbox.setDecimals(3)
        self.left_y_max_spinbox = QDoubleSpinBox()
        self.left_y_max_spinbox.setRange(-999999, 999999)
        self.left_y_max_spinbox.setDecimals(3)
        manual_layout.addWidget(QLabel("最小值:"), 2, 1)
        manual_layout.addWidget(self.left_y_min_spinbox, 2, 2)
        manual_layout.addWidget(QLabel("最大值:"), 2, 3)
        manual_layout.addWidget(self.left_y_max_spinbox, 2, 4)
        
        # 右Y軸範圍（如果有的話）
        if self.chart_widget.show_right_y_axis:
            manual_layout.addWidget(QLabel("右Y軸範圍:"), 3, 0)
            self.right_y_min_spinbox = QDoubleSpinBox()
            self.right_y_min_spinbox.setRange(-999999, 999999)
            self.right_y_min_spinbox.setDecimals(3)
            self.right_y_max_spinbox = QDoubleSpinBox()
            self.right_y_max_spinbox.setRange(-999999, 999999)
            self.right_y_max_spinbox.setDecimals(3)
            manual_layout.addWidget(QLabel("最小值:"), 3, 1)
            manual_layout.addWidget(self.right_y_min_spinbox, 3, 2)
            manual_layout.addWidget(QLabel("最大值:"), 3, 3)
            manual_layout.addWidget(self.right_y_max_spinbox, 3, 4)
        else:
            self.right_y_min_spinbox = None
            self.right_y_max_spinbox = None
        
        layout.addWidget(self.manual_group)
        
        # 按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_current_ranges(self):
        """載入當前的範圍設定"""
        # 檢查是否為自動範圍
        auto_mode = (self.chart_widget.manual_x_range is None and 
                    self.chart_widget.manual_left_y_range is None and
                    self.chart_widget.manual_right_y_range is None)
        
        self.auto_range_checkbox.setChecked(auto_mode)
        
        # 載入當前範圍值或使用數據範圍
        x_range = (self.chart_widget.manual_x_range or 
                  self.chart_widget.get_overall_x_range())
        left_y_range = (self.chart_widget.manual_left_y_range or 
                       self.chart_widget.get_y_range_for_axis("left"))
        
        self.x_min_spinbox.setValue(x_range[0])
        self.x_max_spinbox.setValue(x_range[1])
        self.left_y_min_spinbox.setValue(left_y_range[0])
        self.left_y_max_spinbox.setValue(left_y_range[1])
        
        # 載入X軸間距設定
        self.x_interval_spinbox.setValue(getattr(self.chart_widget, 'x_axis_interval_minutes', 15))
        
        if self.right_y_min_spinbox is not None:
            right_y_range = (self.chart_widget.manual_right_y_range or 
                           self.chart_widget.get_y_range_for_axis("right"))
            self.right_y_min_spinbox.setValue(right_y_range[0])
            self.right_y_max_spinbox.setValue(right_y_range[1])
    
    def on_auto_range_toggled(self, checked):
        """當自動範圍選項被切換時"""
        self.manual_group.setEnabled(not checked)
    
    def get_ranges(self):
        """獲取設定的範圍"""
        if self.auto_range_checkbox.isChecked():
            return {
                'x_range': None,
                'left_y_range': None,
                'right_y_range': None,
                'x_interval_minutes': self.x_interval_spinbox.value(),
                'auto_range': True
            }
        else:
            result = {
                'x_range': (self.x_min_spinbox.value(), self.x_max_spinbox.value()),
                'left_y_range': (self.left_y_min_spinbox.value(), self.left_y_max_spinbox.value()),
                'x_interval_minutes': self.x_interval_spinbox.value(),
                'auto_range': False
            }
            
            if self.right_y_min_spinbox is not None:
                result['right_y_range'] = (self.right_y_min_spinbox.value(), self.right_y_max_spinbox.value())
            else:
                result['right_y_range'] = None
            
            return result


if __name__ == "__main__":
    # 測試代碼
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建測試圖表
    chart = UniversalChartWidget("測試雙Y軸圖表")
    
    # 測試數據
    x_data = list(range(0, 100, 2))
    temp_data = [20 + i * 0.5 for i in range(50)]  # 溫度數據
    wind_data = [10 + i * 0.3 for i in range(50)]  # 風速數據
    
    # 添加溫度數據系列 (左Y軸)
    temp_series = ChartDataSeries("溫度", x_data, temp_data, "cyan", 2, "left")
    chart.add_data_series(temp_series)
    
    # 添加風速數據系列 (右Y軸)
    wind_series = ChartDataSeries("風速", x_data, wind_data, "orange", 2, "right")
    chart.add_data_series(wind_series)
    
    # 添加降雨標註
    rain_annotation = ChartAnnotation("rain", 20, 40, "降雨期間", "blue")
    chart.add_annotation(rain_annotation)
    
    # 設置軸標籤
    chart.set_axis_labels("時間", "溫度", "風速", "秒", "°C", "km/h")
    
    chart.show()
    sys.exit(app.exec_())
