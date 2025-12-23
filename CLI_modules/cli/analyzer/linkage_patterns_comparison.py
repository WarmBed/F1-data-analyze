"""
三種連動設計模式的差異比較
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, pyqtSignal, QRect
from abc import ABC, abstractmethod
from typing import Optional


# =====================================================
# 1. 抽象基類模式 (Abstract Base Class)
# =====================================================

class LinkageChartWidget(QWidget, ABC):
    """
    抽象基類模式 - 連動圖表組件基類
    
    特點：
    - 單一繼承關係
    - 強制子類實現抽象方法
    - 提供共同的連動功能實現
    - 適合有相似結構的圖表組件
    """
    
    def __init__(self, global_signals=None):
        super().__init__()
        
        # 連動狀態
        self.linkage_enabled = True
        self.is_sending_linkage = False
        self.linkage_distance_value = None
        self.linkage_y_relative = None
        self.show_linkage_line = False
        
        # 連接信號
        if global_signals:
            self._connect_signals(global_signals)
    
    def _connect_signals(self, global_signals):
        """連接連動信號"""
        global_signals.lap_analysis_x_linkage.connect(self.on_x_linkage_received)
        global_signals.lap_analysis_x_clear.connect(self.on_x_linkage_clear)
    
    def on_x_linkage_received(self, distance_value: float, y_relative: float):
        """接收連動信號"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.linkage_distance_value = distance_value
        self.linkage_y_relative = y_relative
        self.show_linkage_line = True
        self.update()
    
    def on_x_linkage_clear(self):
        """清除連動"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.linkage_distance_value = None
        self.show_linkage_line = False
        self.update()
    
    # 抽象方法 - 子類必須實現
    @abstractmethod
    def get_chart_rect(self):
        """獲取圖表區域"""
        pass
    
    @abstractmethod
    def distance_to_x_coordinate(self, distance_value: float) -> Optional[float]:
        """距離轉X座標"""
        pass
    
    @abstractmethod
    def x_coordinate_to_distance(self, x_coord: float) -> Optional[float]:
        """X座標轉距離"""
        pass
    
    @abstractmethod
    def draw_chart_content(self, painter):
        """繪製圖表內容"""
        pass


# 使用抽象基類的子類
class RPMChartWidget(LinkageChartWidget):
    """RPM圖表組件 - 繼承抽象基類"""
    
    def get_chart_rect(self):
        return QRect(50, 50, 400, 300)
    
    def distance_to_x_coordinate(self, distance_value: float) -> Optional[float]:
        # RPM特定的轉換邏輯
        pass
    
    def x_coordinate_to_distance(self, x_coord: float) -> Optional[float]:
        # RPM特定的轉換邏輯
        pass
    
    def draw_chart_content(self, painter):
        # RPM特定的繪製邏輯
        pass


# =====================================================
# 2. 模組化模式 (Composition)
# =====================================================

class ChartLinkageModule(QObject):
    """
    模組化模式 - 獨立的連動功能模組
    
    特點：
    - 組合關係，不是繼承
    - 可以動態添加到任何對象
    - 功能完全獨立
    - 更靈活，符合組合優於繼承原則
    """
    
    def __init__(self, parent_widget, global_signals=None):
        super().__init__()
        
        self.parent_widget = parent_widget
        self.linkage_enabled = True
        self.is_sending_linkage = False
        self.linkage_distance_value = None
        self.linkage_y_relative = None
        self.show_linkage_line = False
        
        # 連接信號
        if global_signals:
            self._connect_signals(global_signals)
    
    def _connect_signals(self, global_signals):
        """連接連動信號"""
        global_signals.lap_analysis_x_linkage.connect(self.on_x_linkage_received)
        global_signals.lap_analysis_x_clear.connect(self.on_x_linkage_clear)
    
    def on_x_linkage_received(self, distance_value: float, y_relative: float):
        """接收連動信號"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.linkage_distance_value = distance_value
        self.linkage_y_relative = y_relative
        self.show_linkage_line = True
        
        # 通知父組件更新
        if hasattr(self.parent_widget, 'update'):
            self.parent_widget.update()
    
    def on_x_linkage_clear(self):
        """清除連動"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.linkage_distance_value = None
        self.show_linkage_line = False
        
        if hasattr(self.parent_widget, 'update'):
            self.parent_widget.update()
    
    def handle_mouse_move(self, x_coord: float, y_relative: float, global_signals=None):
        """處理滑鼠移動"""
        if not self.linkage_enabled or not global_signals:
            return
        
        # 需要父組件提供轉換方法
        if hasattr(self.parent_widget, 'x_coordinate_to_distance'):
            distance_value = self.parent_widget.x_coordinate_to_distance(x_coord)
            if distance_value is not None:
                self.send_linkage_signal(distance_value, y_relative, global_signals)
    
    def send_linkage_signal(self, distance_value: float, y_relative: float, global_signals):
        """發送連動信號"""
        self.is_sending_linkage = True
        try:
            global_signals.lap_analysis_x_linkage.emit(distance_value, y_relative)
        finally:
            self.is_sending_linkage = False
    
    def draw_linkage_lines(self, painter, chart_rect):
        """繪製連動線條"""
        if not self.show_linkage_line or self.linkage_distance_value is None:
            return
        
        # 需要父組件提供轉換方法
        if hasattr(self.parent_widget, 'distance_to_x_coordinate'):
            x_coord = self.parent_widget.distance_to_x_coordinate(self.linkage_distance_value)
            if x_coord is not None:
                painter.drawLine(int(x_coord), chart_rect.top(), int(x_coord), chart_rect.bottom())


# 使用模組化的圖表組件
class ModularRPMChartWidget(QWidget):
    """RPM圖表組件 - 使用模組化連動"""
    
    def __init__(self, global_signals=None):
        super().__init__()
        
        # 組合連動模組
        self.linkage_module = ChartLinkageModule(self, global_signals)
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        # 委託給連動模組處理
        chart_rect = self.get_chart_rect()
        if chart_rect.contains(event.pos()):
            y_relative = (event.pos().y() - chart_rect.top()) / chart_rect.height()
            self.linkage_module.handle_mouse_move(
                event.pos().x(), 
                y_relative, 
                getattr(self, 'global_signals', None)
            )
    
    def paintEvent(self, event):
        """繪製事件"""
        from PyQt5.QtGui import QPainter
        painter = QPainter(self)
        
        # 繪製圖表內容
        self.draw_chart_content(painter)
        
        # 委託給連動模組繪製連動線
        self.linkage_module.draw_linkage_lines(painter, self.get_chart_rect())
        
        painter.end()
    
    def get_chart_rect(self):
        return QRect(50, 50, 400, 300)
    
    def distance_to_x_coordinate(self, distance_value: float) -> Optional[float]:
        # RPM特定的轉換邏輯
        pass
    
    def x_coordinate_to_distance(self, x_coord: float) -> Optional[float]:
        # RPM特定的轉換邏輯
        pass
    
    def draw_chart_content(self, painter):
        # RPM特定的繪製邏輯
        pass


# =====================================================
# 3. Mixin 模式 (Multiple Inheritance)
# =====================================================

class ChartLinkageMixin:
    """
    Mixin 模式 - 連動功能混入類別
    
    特點：
    - 多重繼承
    - 提供特定功能的混入
    - 可以與任何基類組合
    - 功能導向的設計
    """
    
    def init_linkage(self, global_signals=None):
        """初始化連動功能"""
        # 連動狀態
        self.linkage_enabled = True
        self.is_sending_linkage = False
        self.linkage_distance_value = None
        self.linkage_y_relative = None
        self.show_linkage_line = False
        
        # 連接信號
        if global_signals:
            self._connect_linkage_signals(global_signals)
    
    def _connect_linkage_signals(self, global_signals):
        """連接連動信號"""
        global_signals.lap_analysis_x_linkage.connect(self.on_x_linkage_received)
        global_signals.lap_analysis_x_clear.connect(self.on_x_linkage_clear)
    
    def on_x_linkage_received(self, distance_value: float, y_relative: float):
        """接收連動信號"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.linkage_distance_value = distance_value
        self.linkage_y_relative = y_relative
        self.show_linkage_line = True
        
        if hasattr(self, 'update'):
            self.update()
    
    def on_x_linkage_clear(self):
        """清除連動"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.linkage_distance_value = None
        self.show_linkage_line = False
        
        if hasattr(self, 'update'):
            self.update()
    
    def handle_mouse_move_linkage(self, x_coord: float, y_relative: float, global_signals=None):
        """處理滑鼠移動連動"""
        if not self.linkage_enabled or not global_signals:
            return
        
        if hasattr(self, 'x_coordinate_to_distance'):
            distance_value = self.x_coordinate_to_distance(x_coord)
            if distance_value is not None:
                self.send_linkage_signal(distance_value, y_relative, global_signals)
    
    def send_linkage_signal(self, distance_value: float, y_relative: float, global_signals):
        """發送連動信號"""
        self.is_sending_linkage = True
        try:
            global_signals.lap_analysis_x_linkage.emit(distance_value, y_relative)
        finally:
            self.is_sending_linkage = False
    
    def draw_linkage_lines(self, painter, chart_rect):
        """繪製連動線條"""
        if not self.show_linkage_line or self.linkage_distance_value is None:
            return
        
        if hasattr(self, 'distance_to_x_coordinate'):
            x_coord = self.distance_to_x_coordinate(self.linkage_distance_value)
            if x_coord is not None:
                painter.drawLine(int(x_coord), chart_rect.top(), int(x_coord), chart_rect.bottom())


# 使用 Mixin 的圖表組件
class MixinRPMChartWidget(QWidget, ChartLinkageMixin):
    """RPM圖表組件 - 使用 Mixin 模式"""
    
    def __init__(self, global_signals=None):
        super().__init__()
        
        # 初始化 Mixin 功能
        self.init_linkage(global_signals)
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        chart_rect = self.get_chart_rect()
        if chart_rect.contains(event.pos()):
            y_relative = (event.pos().y() - chart_rect.top()) / chart_rect.height()
            # 直接調用 Mixin 方法
            self.handle_mouse_move_linkage(
                event.pos().x(), 
                y_relative, 
                getattr(self, 'global_signals', None)
            )
    
    def paintEvent(self, event):
        """繪製事件"""
        from PyQt5.QtGui import QPainter
        painter = QPainter(self)
        
        # 繪製圖表內容
        self.draw_chart_content(painter)
        
        # 直接調用 Mixin 方法繪製連動線
        self.draw_linkage_lines(painter, self.get_chart_rect())
        
        painter.end()
    
    def get_chart_rect(self):
        return QRect(50, 50, 400, 300)
    
    def distance_to_x_coordinate(self, distance_value: float) -> Optional[float]:
        # RPM特定的轉換邏輯
        pass
    
    def x_coordinate_to_distance(self, x_coord: float) -> Optional[float]:
        # RPM特定的轉換邏輯
        pass
    
    def draw_chart_content(self, painter):
        # RPM特定的繪製邏輯
        pass
