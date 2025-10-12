#!/usr/bin/env python3
"""
圈速分析連動混合類 (Mixin)
提供統一的連動功能實現，可被所有圈速分析圖表類繼承
"""

from typing import Optional, Callable
import math
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QRect
from PyQt5.QtWidgets import QPushButton, QToolBar
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont

# 導入國際化
try:
    from core.gui_i18n import tr
except ImportError:
    def tr(key, fallback):
        return fallback


class LapAnalysisLinkageMixin:
    """
    圈速分析連動混合類
    
    提供統一的連動功能：
    - 雙層連動控制（主開關 + 個別開關）
    - X軸位置同步
    - 點擊位置同步
    - 連動線繪製
    """
    
    def __init_linkage__(self):
        """初始化連動功能"""
        # 連動狀態
        self.linkage_enabled = True  # 模組本地連動開關
        self.master_linkage_enabled = True  # 主視窗總開關狀態
        self.is_sending_linkage = False  # 避免循環信號發送
        
        # 連動數據
        self.linkage_distance_value = None  # 連動接收的距離值
        self.linkage_y_relative = 0.5  # 連動接收的Y軸相對位置 (0.0-1.0)
        self.show_linkage_line = False  # 是否顯示連動線
        
        # 固定線數據
        self.fixed_distance_value = None  # 固定線對應的實際距離值
        self.show_fixed_line = False  # 是否顯示固定線
        
        # 連動回調函數（由具體圖表類設定）
        self.update_callback: Optional[Callable] = None
        
    def _is_linkage_fully_enabled(self) -> bool:
        """檢查連動功能是否完全啟用（主開關和個別開關都要開啟）"""
        return self.linkage_enabled and self.master_linkage_enabled
    
    def set_linkage_enabled(self, enabled: bool):
        """設置是否啟用個別連動功能"""
        self.linkage_enabled = enabled
        
    def set_master_linkage_enabled(self, enabled: bool):
        """設置主視窗連動總開關狀態"""
        self.master_linkage_enabled = enabled
        
    def on_master_linkage_changed(self, enabled: bool):
        """響應主視窗連動總開關變更"""
        self.set_master_linkage_enabled(enabled)
        if not enabled:
            # 當總開關關閉時，清除所有連動線
            self.show_linkage_line = False
            self.linkage_distance_value = None
            self.linkage_y_relative = 0.5
            if self.update_callback:
                self.update_callback()
    
    def on_x_linkage_received(self, distance_value: float, y_relative: float):
        """接收來自其他圖表的X軸連動信號"""
        if not self._is_linkage_fully_enabled() or self.is_sending_linkage:
            return
        
        # 根據距離值設置連動線 (使用滑鼠追蹤樣式)
        self.linkage_distance_value = distance_value
        self.linkage_y_relative = y_relative
        self.show_linkage_line = True
        if self.update_callback:
            self.update_callback()
    
    def on_x_linkage_clear(self):
        """接收X軸連動清除信號"""
        if not self._is_linkage_fully_enabled() or self.is_sending_linkage:
            return
        
        # 清除連動線
        self.show_linkage_line = False
        self.linkage_distance_value = None
        self.linkage_y_relative = 0.5
        if self.update_callback:
            self.update_callback()
    
    def on_click_linkage_received(self, distance_value: float):
        """接收來自其他圖表的點擊連動信號 (設置固定線)"""
        if not self._is_linkage_fully_enabled() or self.is_sending_linkage:
            return
        
        # 設置固定線
        self.fixed_distance_value = distance_value
        self.show_fixed_line = True
        if self.update_callback:
            self.update_callback()
    
    def on_click_linkage_clear(self):
        """接收點擊連動清除信號"""
        if not self._is_linkage_fully_enabled() or self.is_sending_linkage:
            return
        
        # 清除固定線
        self.show_fixed_line = False
        self.fixed_distance_value = None
        if self.update_callback:
            self.update_callback()
    
    def send_x_linkage_signal(self, distance_value: float, y_relative: float, signal_emitter):
        """發送X軸連動信號"""
        if not self._is_linkage_fully_enabled() or self.is_sending_linkage:
            return
        
        self.is_sending_linkage = True
        signal_emitter.emit(distance_value, y_relative)
        self.is_sending_linkage = False
    
    def send_click_linkage_signal(self, distance_value: float, signal_emitter):
        """發送點擊連動信號"""
        if not self._is_linkage_fully_enabled() or self.is_sending_linkage:
            return
        
        self.is_sending_linkage = True
        signal_emitter.emit(distance_value)
        self.is_sending_linkage = False
    
    def send_clear_signals(self, x_clear_emitter, click_clear_emitter):
        """發送清除信號"""
        if not self._is_linkage_fully_enabled() or self.is_sending_linkage:
            return
        
        self.is_sending_linkage = True
        x_clear_emitter.emit()
        click_clear_emitter.emit()
        self.is_sending_linkage = False
    
    def clear_fixed_line(self):
        """清除固定線條"""
        self.show_fixed_line = False
        self.fixed_distance_value = None
        if self.update_callback:
            self.update_callback()
    
    def toggle_linkage(self):
        """切換個別連動狀態"""
        self.linkage_enabled = not self.linkage_enabled
        # 此方法可以由具體實現類重寫以更新UI
        
    def _create_linkage_toolbar(self, toolbar: QToolBar) -> QPushButton:
        """建立連動功能工具列（可選使用）"""
        toolbar.addSeparator()
        
        # 個別連動開關
        linkage_button = QPushButton("🔗 個別連動")
        linkage_button.setCheckable(True)
        linkage_button.setChecked(True)  # 預設開啟
        linkage_button.clicked.connect(self.toggle_linkage)
        toolbar.addWidget(linkage_button)
        
        return linkage_button
    
    def set_update_callback(self, callback: Callable):
        """設置更新回調函數"""
        self.update_callback = callback


class LapAnalysisLinkageDrawingMixin:
    """
    連動線繪製混合類
    提供統一的連動線繪製功能
    """
    
    def draw_linkage_line(self, painter: QPainter, chart_rect: QRect, 
                         distance_data: list, driver1_name: str, driver2_name: str,
                         driver1_data: list, driver2_data: list, data_label: str = "數值"):
        """
        繪製連動線 (來自其他圖表的X軸位置)
        
        Args:
            painter: Qt繪圖器
            chart_rect: 圖表區域
            distance_data: 距離數據列表
            driver1_name: 車手1名稱
            driver2_name: 車手2名稱  
            driver1_data: 車手1數據列表
            driver2_data: 車手2數據列表
            data_label: 數據標籤（如"速度"、"RPM"、"油門"）
        """
        if not hasattr(self, 'linkage_distance_value') or not self.linkage_distance_value:
            return
            
        # 獲取當前的視圖範圍
        # 注意：在時間軸模式下，這些"distance"屬性實際存儲的是時間範圍
        # Speed/Distance Diff 使用 min_speed/max_speed
        # 其他模組使用 min_distance/max_distance
        current_min = (
            getattr(self, 'view_min_distance', None) or 
            getattr(self, 'view_min_speed', None) or 
            getattr(self, 'min_distance', None) or 
            getattr(self, 'min_speed', 0)
        )
        current_max = (
            getattr(self, 'view_max_distance', None) or 
            getattr(self, 'view_max_speed', None) or 
            getattr(self, 'max_distance', None) or 
            getattr(self, 'max_speed', 6000)
        )
        value_range = current_max - current_min
        
        if value_range <= 0:
            return
            
        # 計算 X 座標
        # linkage_distance_value 在時間軸模式下實際上是時間值，在距離模式下是距離值
        relative_pos = (self.linkage_distance_value - current_min) / value_range
        x_pos = chart_rect.left() + int(relative_pos * chart_rect.width())
        
        # 檢查是否在圖表範圍內
        if x_pos < chart_rect.left() or x_pos > chart_rect.right():
            return
            
        # 繪製連動垂直線
        painter.setPen(QPen(QColor(128, 128, 128), 1, Qt.DashLine))  # 灰色虛線
        painter.drawLine(x_pos, chart_rect.top(), x_pos, chart_rect.bottom())
        
        # 繪製連動標籤
        self._draw_linkage_label(painter, chart_rect, x_pos, distance_data, 
                               driver1_name, driver2_name, driver1_data, driver2_data, data_label)
    
    def _draw_linkage_label(self, painter: QPainter, chart_rect: QRect, x_pos: int,
                          distance_data: list, driver1_name: str, driver2_name: str,
                          driver1_data: list, driver2_data: list, data_label: str):
        """繪製連動標籤"""
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor, QFont, QBrush, QPen
        
        label_width = 160
        label_height = 60
        label_x = x_pos + 10
        
        # 使用同步的Y軸位置計算標籤位置
        label_y = chart_rect.bottom() - int(self.linkage_y_relative * chart_rect.height()) - label_height // 2
        
        # 確保標籤不會超出圖表區域
        label_y = max(chart_rect.top() + 10, min(label_y, chart_rect.bottom() - label_height - 10))
        
        # 如果標籤會超出右邊界，則放在線的左邊
        if label_x + label_width > chart_rect.right():
            label_x = x_pos - label_width - 10
            
        # 繪製標籤背景
        painter.setBrush(QBrush(QColor(255, 255, 255, 230)))  # 白色半透明背景
        painter.setPen(QPen(QColor(128, 128, 128), 1))
        painter.drawRect(label_x, label_y, label_width, label_height)
        
        # 繪製距離或時間資訊（根據時間軸模式）
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setFont(QFont("Arial", 9))
        
        # 檢查是否使用時間軸模式
        use_time_axis = getattr(self, 'use_time_axis', False)
        
        if use_time_axis:
            # 在時間軸模式下，linkage_distance_value 實際上已經是時間值（秒）
            painter.drawText(label_x + 5, label_y + 15, f"{tr('linkage_time', '連動時間')}: {self.linkage_distance_value:.2f} s")
        else:
            # 在距離模式下，linkage_distance_value 是距離值（米）
            painter.drawText(label_x + 5, label_y + 15, f"{tr('linkage_distance', '連動距離')}: {self.linkage_distance_value:.0f} m")
        
        # 顯示當前位置的數據資訊
        # 在時間軸模式下，使用 linkage_distance_value（時間值）在 driver1_time 中搜索
        # 在距離模式下，使用 linkage_distance_value（距離值）在 distance_data 中搜索
        use_time_axis = getattr(self, 'use_time_axis', False)
        driver1_time = getattr(self, 'driver1_time', None)
        
        if use_time_axis and driver1_time:
            # 時間軸模式：在時間數組中搜索
            search_data = driver1_time
        else:
            # 距離模式：在距離數組中搜索
            search_data = distance_data
            
        if search_data and driver1_data:
            # 找到最接近的數據點
            closest_idx = self._find_closest_data_index(search_data, self.linkage_distance_value)
            
            if closest_idx is not None:
                text_y = label_y + 30
                
                # 車手1數據
                if closest_idx < len(driver1_data):
                    value1 = self._coerce_numeric(driver1_data[closest_idx])
                    painter.setPen(QPen(getattr(self, 'driver1_color', QColor(0, 0, 255)), 1))
                    if value1 is not None:
                        painter.drawText(label_x + 5, text_y, f"{driver1_name}: {value1:.1f} {data_label}")
                    else:
                        painter.drawText(label_x + 5, text_y, f"{driver1_name}: N/A {data_label}")
                
                # 車手2數據 (如果存在且不同)
                if (driver2_data and closest_idx < len(driver2_data) and 
                    driver2_name != driver1_name):
                    value2 = self._coerce_numeric(driver2_data[closest_idx])
                    painter.setPen(QPen(getattr(self, 'driver2_color', QColor(255, 0, 0)), 1))
                    if value2 is not None:
                        painter.drawText(label_x + 5, text_y + 15, f"{driver2_name}: {value2:.1f} {data_label}")
                    else:
                        painter.drawText(label_x + 5, text_y + 15, f"{driver2_name}: N/A {data_label}")
    
    def _find_closest_data_index(self, distance_data: list, target_distance: float) -> Optional[int]:
        """找到最接近目標距離的數據索引"""
        if not distance_data:
            return None
            
        closest_idx = 0
        min_diff = abs(distance_data[0] - target_distance)
        
        for i, dist in enumerate(distance_data):
            diff = abs(dist - target_distance)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
                
        return closest_idx

    def _coerce_numeric(self, value) -> Optional[float]:
        """嘗試將值轉換為有限浮點數，失敗時返回 None。"""
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(numeric) or math.isinf(numeric):
            return None
        return numeric
