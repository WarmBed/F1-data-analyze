# -*- coding: utf-8 -*-
"""
Hover Tooltip Mixin for Live Timing Chart Widgets

提供滑鼠懸停時顯示垂直線和浮動框的功能。
支援多曲線顯示、智慧定位、車手顏色標記。
支援 Linkage 跨模組 hover 位置同步。

使用方式:
1. 繼承 HoverTooltipMixin
2. 實現 _get_hover_data_at_x(x_value) 方法
3. 在 paintEvent 中調用 _draw_hover_elements(painter)
4. 在 __init__ 中調用 _init_hover_tracking()
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics

import logging

logger = logging.getLogger(__name__)


# 導入全局同步信號
def _get_hover_sync_signal():
    """延遲導入避免循環依賴"""
    from modules.gui.live_timing.core.global_sync_signal import get_global_sync_signal
    return get_global_sync_signal()


@dataclass
class HoverDataPoint:
    """單一曲線在懸停位置的數據點"""
    label: str              # 曲線標籤 (例如: "VER", "LEC Best", "SF%")
    value: float            # Y 軸數值
    formatted_value: str    # 格式化的顯示值 (例如: "287 km/h", "-3.2%")
    color: str = "#FFFFFF"  # 曲線顏色 (hex)
    is_primary: bool = True # 是否為主要曲線


@dataclass
class HoverInfo:
    """懸停位置的完整資訊"""
    x_value: float                        # X 軸數值 (圈數或距離)
    x_label: str                          # X 軸標籤 (例如: "Lap: 15", "Dist: 2345m")
    data_points: List[HoverDataPoint] = field(default_factory=list)  # 所有曲線的數據點
    is_valid: bool = True                 # 是否有效數據


class HoverTooltipMixin:
    """
    滑鼠懸停顯示垂直線和浮動框的 Mixin
    
    功能:
    - 白色虛線垂直線跟隨滑鼠
    - 半透明黑底浮動框顯示數值
    - 智慧定位 (靠近邊緣時自動調整)
    - 支援多曲線顯示
    - 滑鼠離開時立即隱藏
    """
    
    # 浮動框樣式常數
    TOOLTIP_BG_COLOR = QColor(0, 0, 0, 200)      # 半透明黑色
    TOOLTIP_BORDER_COLOR = QColor(100, 100, 100) # 灰色邊框
    TOOLTIP_TEXT_COLOR = QColor(255, 255, 255)   # 白色文字
    TOOLTIP_PADDING = 8                          # 內邊距
    TOOLTIP_OFFSET = 15                          # 與滑鼠的距離
    
    # 垂直線樣式
    HOVER_LINE_COLOR = QColor(255, 255, 255)     # 白色
    HOVER_LINE_WIDTH = 1
    
    def _init_hover_tracking(self):
        """初始化懸停追蹤 - 必須在 __init__ 中調用"""
        # 啟用滑鼠追蹤
        self.setMouseTracking(True)
        
        # 懸停狀態
        self._hover_enabled = True
        self._hover_x_pixel: Optional[int] = None  # 滑鼠 X 像素位置
        self._hover_y_pixel: Optional[int] = None  # 滑鼠 Y 像素位置
        self._hover_info: Optional[HoverInfo] = None
        self._is_hovering = False
        
        # Linkage 狀態 - hover 位置同步
        self._hover_linkage_enabled = True  # 是否啟用 hover 位置同步
        self._synced_x_value: Optional[float] = None  # 從其他模組同步的 X 值
        self._is_synced_hover = False  # 是否是同步觸發的 hover
        
        # 連接全局 hover 同步信號
        try:
            sync_signal = _get_hover_sync_signal()
            sync_signal.hover_position_changed.connect(self._on_hover_position_synced)
        except Exception as e:
            logger.warning(f"[HOVER_MIXIN] Failed to connect hover sync signal: {e}")
        
        # 字體
        self._tooltip_font = QFont("Consolas", 9)
        self._tooltip_font_metrics = QFontMetrics(self._tooltip_font)
        
        logger.debug("[HOVER_MIXIN] Hover tracking initialized with linkage support")
    
    def _on_hover_position_synced(self, data: dict):
        """
        接收其他模組的 hover 位置同步
        
        Args:
            data: {'source_widget': int, 'x_value': float, 'is_hovering': bool, 'is_trace_module': bool}
        """
        # 忽略自己發送的信號
        if data.get('source_widget') == id(self):
            return
        
        # 只接收來自 Trace 模組的信號
        if not data.get('is_trace_module', False):
            return
        
        # 只有自己也是 Trace 模組才接收同步
        if not getattr(self, '_is_trace_module', False):
            return
        
        # 檢查 linkage 是否啟用
        if not getattr(self, '_hover_linkage_enabled', True):
            return
        
        # 檢查個別連動是否啟用 (使用現有的 _individual_linkage_enabled)
        if not getattr(self, '_individual_linkage_enabled', True):
            return
        
        is_hovering = data.get('is_hovering', False)
        x_value = data.get('x_value')
        
        if is_hovering and x_value is not None:
            # 設置同步的 hover 位置
            self._synced_x_value = x_value
            self._is_synced_hover = True
            self._is_hovering = True
            
            # 更新 hover 資訊
            self._hover_info = self._get_hover_data_at_x(x_value)
            
            # 計算像素位置
            chart_rect = self._get_chart_rect()
            self._hover_x_pixel = self._x_value_to_pixel(x_value, chart_rect)
            self._hover_y_pixel = chart_rect.center().y()  # 居中
            
            self.update()
        else:
            # 清除同步的 hover
            if self._is_synced_hover:
                self._is_synced_hover = False
                self._synced_x_value = None
                self._is_hovering = False
                self._hover_info = None
                self._hover_x_pixel = None
                self._hover_y_pixel = None
                self.update()
    
    def _emit_hover_position(self, x_value: float, is_hovering: bool):
        """發送 hover 位置到其他模組 (僅 Trace 模組之間同步)"""
        if not getattr(self, '_hover_linkage_enabled', True):
            return
        
        if not getattr(self, '_individual_linkage_enabled', True):
            return
        
        # 檢查是否為 Trace 模組 (通過 _is_trace_module 屬性)
        is_trace_module = getattr(self, '_is_trace_module', False)
        if not is_trace_module:
            return
        
        try:
            sync_signal = _get_hover_sync_signal()
            sync_signal.hover_position_changed.emit({
                'source_widget': id(self),
                'x_value': x_value,
                'is_hovering': is_hovering,
                'is_trace_module': True  # 標識這是 Trace 模組發送的
            })
        except Exception as e:
            logger.warning(f"[HOVER_MIXIN] Failed to emit hover position: {e}")
    
    def _x_value_to_pixel(self, x_value: float, chart_rect: QRect) -> int:
        """
        將數據 X 值轉換為像素 X 座標
        
        Args:
            x_value: 數據 X 值
            chart_rect: 圖表區域
            
        Returns:
            int: 像素 X 座標
        """
        if chart_rect.width() <= 0:
            return chart_rect.left()
        
        x_min = getattr(self, '_x_min', 0)
        x_max = getattr(self, '_x_max', getattr(self, '_max_distance', 5000))
        
        if x_max <= x_min:
            return chart_rect.left()
        
        ratio = (x_value - x_min) / (x_max - x_min)
        return int(chart_rect.left() + ratio * chart_rect.width())
    
    def set_hover_linkage_enabled(self, enabled: bool):
        """設置 hover 位置同步是否啟用"""
        self._hover_linkage_enabled = enabled
        if not enabled:
            self._is_synced_hover = False
            self._synced_x_value = None
    
    def _handle_mouse_move(self, event) -> bool:
        """
        處理滑鼠移動事件
        
        Args:
            event: QMouseEvent
            
        Returns:
            bool: 是否需要重繪
        """
        if not self._hover_enabled:
            return False
        
        # 取得滑鼠位置
        pos = event.pos()
        x, y = pos.x(), pos.y()
        
        # 取得圖表繪圖區域
        chart_rect = self._get_chart_rect()
        
        # 檢查是否在圖表區域內
        if chart_rect.contains(pos):
            self._is_hovering = True
            self._hover_x_pixel = x
            self._hover_y_pixel = y
            
            # 清除同步狀態 - 這是本地滑鼠事件
            self._is_synced_hover = False
            
            # 將像素 X 轉換為數據 X 值
            x_value = self._pixel_to_x_value(x, chart_rect)
            
            # 獲取該 X 值的所有曲線數據
            self._hover_info = self._get_hover_data_at_x(x_value)
            
            # 發送 hover 位置同步到其他模組
            self._emit_hover_position(x_value, True)
            
            return True
        else:
            # 離開圖表區域
            if self._is_hovering:
                self._is_hovering = False
                self._hover_x_pixel = None
                self._hover_y_pixel = None
                self._hover_info = None
                
                # 發送 hover 結束同步
                self._emit_hover_position(0, False)
                
                return True
            return False
    
    def _handle_mouse_leave(self) -> bool:
        """
        處理滑鼠離開事件
        
        Returns:
            bool: 是否需要重繪
        """
        if self._is_hovering:
            self._is_hovering = False
            self._hover_x_pixel = None
            self._hover_y_pixel = None
            self._hover_info = None
            
            # 發送 hover 結束同步
            self._emit_hover_position(0, False)
            
            return True
        return False
    
    def _get_chart_rect(self) -> QRect:
        """
        取得圖表繪圖區域 (子類需要覆寫或確保有 margin 屬性)
        
        Returns:
            QRect: 圖表繪圖區域
        """
        # 預設使用常見的 margin 屬性名稱
        margin_left = getattr(self, '_margin_left', getattr(self, 'margin_left', 50))
        margin_right = getattr(self, '_margin_right', getattr(self, 'margin_right', 20))
        margin_top = getattr(self, '_margin_top', getattr(self, 'margin_top', 30))
        margin_bottom = getattr(self, '_margin_bottom', getattr(self, 'margin_bottom', 30))
        
        return QRect(
            margin_left,
            margin_top,
            self.width() - margin_left - margin_right,
            self.height() - margin_top - margin_bottom
        )
    
    def _pixel_to_x_value(self, pixel_x: int, chart_rect: QRect) -> float:
        """
        將像素 X 座標轉換為數據 X 值
        
        子類應該覆寫此方法以提供正確的轉換邏輯
        
        Args:
            pixel_x: 像素 X 座標
            chart_rect: 圖表區域
            
        Returns:
            float: 數據 X 值 (圈數或距離)
        """
        # 預設實現 - 線性映射
        if chart_rect.width() <= 0:
            return 0.0
        
        # 獲取 X 軸範圍
        x_min = getattr(self, '_x_min', 1)
        x_max = getattr(self, '_x_max', getattr(self, '_total_laps', 60))
        
        ratio = (pixel_x - chart_rect.left()) / chart_rect.width()
        return x_min + ratio * (x_max - x_min)
    
    def _get_hover_data_at_x(self, x_value: float) -> Optional[HoverInfo]:
        """
        獲取指定 X 值的所有曲線數據
        
        子類必須覆寫此方法
        
        Args:
            x_value: X 軸數值
            
        Returns:
            HoverInfo: 懸停資訊，如果沒有數據則返回 None
        """
        # 預設實現 - 子類需要覆寫
        logger.warning("[HOVER_MIXIN] _get_hover_data_at_x not implemented")
        return None
    
    def _draw_hover_elements(self, painter: QPainter):
        """
        繪製懸停元素 (垂直線 + 浮動框)
        
        在 paintEvent 中調用此方法
        
        Args:
            painter: QPainter 實例
        """
        if not self._is_hovering or self._hover_x_pixel is None:
            return
        
        chart_rect = self._get_chart_rect()
        
        # 1. 繪製垂直虛線
        self._draw_vertical_line(painter, self._hover_x_pixel, chart_rect)
        
        # 2. 繪製浮動框
        if self._hover_info and self._hover_info.is_valid:
            self._draw_tooltip(painter, chart_rect)
    
    def _draw_vertical_line(self, painter: QPainter, x: int, chart_rect: QRect):
        """繪製垂直虛線"""
        pen = QPen(self.HOVER_LINE_COLOR, self.HOVER_LINE_WIDTH, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(x, chart_rect.top(), x, chart_rect.bottom())
    
    def _draw_tooltip(self, painter: QPainter, chart_rect: QRect):
        """繪製浮動框"""
        if not self._hover_info:
            return
        
        # 計算浮動框內容
        lines = self._build_tooltip_lines()
        if not lines:
            return
        
        # 計算浮動框尺寸
        max_width = 0
        line_height = self._tooltip_font_metrics.height()
        
        for text, _ in lines:
            width = self._tooltip_font_metrics.horizontalAdvance(text)
            max_width = max(max_width, width)
        
        tooltip_width = max_width + self.TOOLTIP_PADDING * 2
        tooltip_height = len(lines) * line_height + self.TOOLTIP_PADDING * 2
        
        # 智慧定位
        tooltip_pos = self._calculate_tooltip_position(
            self._hover_x_pixel, self._hover_y_pixel,
            tooltip_width, tooltip_height, chart_rect
        )
        
        # 繪製背景
        painter.fillRect(
            tooltip_pos.x(), tooltip_pos.y(),
            tooltip_width, tooltip_height,
            self.TOOLTIP_BG_COLOR
        )
        
        # 繪製邊框
        painter.setPen(QPen(self.TOOLTIP_BORDER_COLOR, 1))
        painter.drawRect(
            tooltip_pos.x(), tooltip_pos.y(),
            tooltip_width, tooltip_height
        )
        
        # 繪製文字
        painter.setFont(self._tooltip_font)
        y = tooltip_pos.y() + self.TOOLTIP_PADDING + self._tooltip_font_metrics.ascent()
        
        for text, color in lines:
            painter.setPen(QColor(color))
            painter.drawText(
                tooltip_pos.x() + self.TOOLTIP_PADDING,
                y,
                text
            )
            y += line_height
    
    def _build_tooltip_lines(self) -> List[Tuple[str, str]]:
        """
        建構浮動框的文字行
        
        Returns:
            List[Tuple[str, str]]: [(文字, 顏色), ...]
        """
        if not self._hover_info:
            return []
        
        lines = []
        
        # X 軸標籤
        lines.append((self._hover_info.x_label, "#FFFFFF"))
        
        # 各曲線數據
        for dp in self._hover_info.data_points:
            text = f"{dp.label}: {dp.formatted_value}"
            lines.append((text, dp.color))
        
        return lines
    
    def _calculate_tooltip_position(
        self, 
        mouse_x: int, 
        mouse_y: int,
        tooltip_width: int, 
        tooltip_height: int,
        chart_rect: QRect
    ) -> QPoint:
        """
        智慧計算浮動框位置
        
        Args:
            mouse_x, mouse_y: 滑鼠位置
            tooltip_width, tooltip_height: 浮動框尺寸
            chart_rect: 圖表區域
            
        Returns:
            QPoint: 浮動框左上角位置
        """
        # 預設在滑鼠右下方
        x = mouse_x + self.TOOLTIP_OFFSET
        y = mouse_y + self.TOOLTIP_OFFSET
        
        # 檢查右邊界
        if x + tooltip_width > self.width() - 5:
            x = mouse_x - tooltip_width - self.TOOLTIP_OFFSET
        
        # 檢查下邊界
        if y + tooltip_height > self.height() - 5:
            y = mouse_y - tooltip_height - self.TOOLTIP_OFFSET
        
        # 確保不超出左邊界
        x = max(5, x)
        
        # 確保不超出上邊界
        y = max(5, y)
        
        return QPoint(x, y)
    
    def set_hover_enabled(self, enabled: bool):
        """啟用/禁用懸停功能"""
        self._hover_enabled = enabled
        if not enabled:
            self._is_hovering = False
            self._hover_info = None
            self.update()
