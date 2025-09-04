"""
圖表連動功能 Mixin 模組
提供可重用的X軸位置同步、滑鼠連動、點擊連動功能
"""

from PyQt5.QtCore import QObject
from typing import Optional, Protocol


class ChartLinkageProtocol(Protocol):
    """圖表連動協議，定義圖表組件需要實現的方法"""
    
    def update(self) -> None:
        """更新圖表顯示"""
        ...
    
    def get_chart_rect(self):
        """獲取圖表繪製區域"""
        ...
    
    def distance_to_x_coordinate(self, distance_value: float) -> Optional[float]:
        """將距離值轉換為X座標"""
        ...
    
    def x_coordinate_to_distance(self, x_coord: float) -> Optional[float]:
        """將X座標轉換為距離值"""
        ...


class ChartLinkageMixin:
    """
    圖表連動功能 Mixin 類別
    
    提供以下功能：
    1. X軸位置同步（滑鼠移動時）
    2. 點擊位置同步（滑鼠點擊時）
    3. Y軸高度同步
    4. 連動線條顯示/清除
    5. 連動狀態管理
    
    使用方法：
    class MyChartWidget(QWidget, ChartLinkageMixin):
        def __init__(self):
            super().__init__()
            self.init_linkage()
    """
    
    def init_linkage(self, global_signals=None, linkage_signals_prefix="lap_analysis"):
        """
        初始化連動功能
        
        Args:
            global_signals: 全域信號管理器實例
            linkage_signals_prefix: 信號前綴，用於區分不同類型的連動
        """
        # 連動狀態
        self.linkage_enabled = True
        self.is_sending_linkage = False
        
        # 連動數據
        self.linkage_distance_value = None
        self.linkage_y_relative = None
        self.show_linkage_line = False
        
        # 點擊連動數據
        self.click_linkage_distance_value = None
        self.show_click_linkage_line = False
        
        # 信號配置
        self.linkage_signals_prefix = linkage_signals_prefix
        
        # 連接信號
        if global_signals:
            self._connect_linkage_signals(global_signals)
    
    def _connect_linkage_signals(self, global_signals):
        """連接連動相關信號"""
        try:
            # X軸連動信號
            x_linkage_signal = getattr(global_signals, f"{self.linkage_signals_prefix}_x_linkage", None)
            if x_linkage_signal:
                x_linkage_signal.connect(self.on_x_linkage_received)
            
            x_clear_signal = getattr(global_signals, f"{self.linkage_signals_prefix}_x_clear", None)
            if x_clear_signal:
                x_clear_signal.connect(self.on_x_linkage_clear)
            
            # 點擊連動信號
            click_linkage_signal = getattr(global_signals, f"{self.linkage_signals_prefix}_click_linkage", None)
            if click_linkage_signal:
                click_linkage_signal.connect(self.on_click_linkage_received)
            
            click_clear_signal = getattr(global_signals, f"{self.linkage_signals_prefix}_click_clear", None)
            if click_clear_signal:
                click_clear_signal.connect(self.on_click_linkage_clear)
                
        except Exception as e:
            print(f"連動信號連接失敗: {e}")
    
    def on_x_linkage_received(self, distance_value: float, y_relative: float):
        """接收X軸連動信號"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.linkage_distance_value = distance_value
        self.linkage_y_relative = y_relative
        self.show_linkage_line = True
        
        # 更新顯示
        if hasattr(self, 'update'):
            self.update()
    
    def on_x_linkage_clear(self):
        """清除X軸連動"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.linkage_distance_value = None
        self.linkage_y_relative = None
        self.show_linkage_line = False
        
        # 更新顯示
        if hasattr(self, 'update'):
            self.update()
    
    def on_click_linkage_received(self, distance_value: float):
        """接收點擊連動信號"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.click_linkage_distance_value = distance_value
        self.show_click_linkage_line = True
        
        # 更新顯示
        if hasattr(self, 'update'):
            self.update()
    
    def on_click_linkage_clear(self):
        """清除點擊連動"""
        if not self.linkage_enabled or self.is_sending_linkage:
            return
        
        self.click_linkage_distance_value = None
        self.show_click_linkage_line = False
        
        # 更新顯示
        if hasattr(self, 'update'):
            self.update()
    
    def set_linkage_enabled(self, enabled: bool):
        """設置連動功能啟用狀態"""
        self.linkage_enabled = enabled
        
        # 如果停用連動，清除所有連動狀態
        if not enabled:
            self.linkage_distance_value = None
            self.linkage_y_relative = None
            self.show_linkage_line = False
            self.click_linkage_distance_value = None
            self.show_click_linkage_line = False
            
            if hasattr(self, 'update'):
                self.update()
    
    def send_x_linkage_signal(self, distance_value: float, y_relative: float, global_signals=None):
        """發送X軸連動信號"""
        if not self.linkage_enabled or not global_signals:
            return
        
        self.is_sending_linkage = True
        try:
            signal = getattr(global_signals, f"{self.linkage_signals_prefix}_x_linkage", None)
            if signal:
                signal.emit(distance_value, y_relative)
        finally:
            self.is_sending_linkage = False
    
    def send_x_clear_signal(self, global_signals=None):
        """發送X軸清除信號"""
        if not self.linkage_enabled or not global_signals:
            return
        
        self.is_sending_linkage = True
        try:
            signal = getattr(global_signals, f"{self.linkage_signals_prefix}_x_clear", None)
            if signal:
                signal.emit()
        finally:
            self.is_sending_linkage = False
    
    def send_click_linkage_signal(self, distance_value: float, global_signals=None):
        """發送點擊連動信號"""
        if not self.linkage_enabled or not global_signals:
            return
        
        self.is_sending_linkage = True
        try:
            signal = getattr(global_signals, f"{self.linkage_signals_prefix}_click_linkage", None)
            if signal:
                signal.emit(distance_value)
        finally:
            self.is_sending_linkage = False
    
    def send_click_clear_signal(self, global_signals=None):
        """發送點擊清除信號"""
        if not self.linkage_enabled or not global_signals:
            return
        
        self.is_sending_linkage = True
        try:
            signal = getattr(global_signals, f"{self.linkage_signals_prefix}_click_clear", None)
            if signal:
                signal.emit()
        finally:
            self.is_sending_linkage = False
    
    def handle_mouse_move_linkage(self, x_coord: float, y_relative: float, global_signals=None):
        """處理滑鼠移動連動（在圖表區域內）"""
        if not hasattr(self, 'x_coordinate_to_distance'):
            return
        
        distance_value = self.x_coordinate_to_distance(x_coord)
        if distance_value is not None:
            self.send_x_linkage_signal(distance_value, y_relative, global_signals)
    
    def handle_mouse_leave_linkage(self, global_signals=None):
        """處理滑鼠離開連動"""
        self.send_x_clear_signal(global_signals)
    
    def handle_mouse_click_linkage(self, x_coord: float, global_signals=None):
        """處理滑鼠點擊連動"""
        if not hasattr(self, 'x_coordinate_to_distance'):
            return
        
        distance_value = self.x_coordinate_to_distance(x_coord)
        if distance_value is not None:
            self.send_click_linkage_signal(distance_value, global_signals)
    
    def get_linkage_x_coordinate(self, distance_value: float) -> Optional[float]:
        """獲取連動距離值對應的X座標"""
        if not hasattr(self, 'distance_to_x_coordinate'):
            return None
        
        return self.distance_to_x_coordinate(distance_value)
    
    def draw_linkage_lines(self, painter, chart_rect):
        """
        繪製連動線條
        
        Args:
            painter: QPainter 實例
            chart_rect: 圖表繪製區域
        """
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QPen, QColor
        
        # 繪製X軸連動線（灰色虛線）
        if self.show_linkage_line and self.linkage_distance_value is not None:
            x_coord = self.get_linkage_x_coordinate(self.linkage_distance_value)
            if x_coord is not None and chart_rect.left() <= x_coord <= chart_rect.right():
                pen = QPen(QColor(128, 128, 128), 1, Qt.DashLine)
                painter.setPen(pen)
                painter.drawLine(int(x_coord), chart_rect.top(), int(x_coord), chart_rect.bottom())
        
        # 繪製點擊連動線（紅色實線）
        if self.show_click_linkage_line and self.click_linkage_distance_value is not None:
            x_coord = self.get_linkage_x_coordinate(self.click_linkage_distance_value)
            if x_coord is not None and chart_rect.left() <= x_coord <= chart_rect.right():
                pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawLine(int(x_coord), chart_rect.top(), int(x_coord), chart_rect.bottom())


class ChartLinkageManager:
    """
    圖表連動管理器
    用於管理多個圖表組件之間的連動關係
    """
    
    def __init__(self, global_signals, linkage_signals_prefix="lap_analysis"):
        self.global_signals = global_signals
        self.linkage_signals_prefix = linkage_signals_prefix
        self.registered_charts = []
    
    def register_chart(self, chart_widget):
        """註冊圖表組件到連動管理器"""
        if hasattr(chart_widget, 'init_linkage'):
            chart_widget.init_linkage(self.global_signals, self.linkage_signals_prefix)
            self.registered_charts.append(chart_widget)
    
    def unregister_chart(self, chart_widget):
        """從連動管理器移除圖表組件"""
        if chart_widget in self.registered_charts:
            self.registered_charts.remove(chart_widget)
    
    def set_all_linkage_enabled(self, enabled: bool):
        """設置所有註冊圖表的連動狀態"""
        for chart in self.registered_charts:
            if hasattr(chart, 'set_linkage_enabled'):
                chart.set_linkage_enabled(enabled)
    
    def clear_all_linkage(self):
        """清除所有連動狀態"""
        if self.global_signals:
            try:
                x_clear_signal = getattr(self.global_signals, f"{self.linkage_signals_prefix}_x_clear", None)
                if x_clear_signal:
                    x_clear_signal.emit()
                
                click_clear_signal = getattr(self.global_signals, f"{self.linkage_signals_prefix}_click_clear", None)
                if click_clear_signal:
                    click_clear_signal.emit()
            except Exception as e:
                print(f"清除連動狀態失敗: {e}")
