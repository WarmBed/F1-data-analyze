"""
賽道地圖視覺化組件
Track Map Widget

基於 PyQtGraph 的高效能賽道繪圖組件
包含原點標註功能
"""

import logging
import pyqtgraph as pg
try:
    from PySide6.QtCore import Signal as pyqtSignal
    from PySide6.QtWidgets import QWidget
except ImportError:
    try:
        from PyQt6.QtCore import pyqtSignal
        from PyQt6.QtWidgets import QWidget
    except ImportError:
        # 如果都沒有，使用 PyQt5
        from PyQt5.QtCore import pyqtSignal
        from PyQt5.QtWidgets import QWidget
        
from typing import Dict, List, Optional, Tuple


class TrackMapWidget(pg.PlotWidget):
    """賽道地圖視覺化組件（含原點標註）"""
    
    # 信號定義
    point_selected = pyqtSignal(int)  # 賽道點選擇信號
    view_changed = pyqtSignal()       # 視圖變更信號
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化賽道地圖組件
        
        Args:
            parent: 父組件
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # 組件屬性
        self.track_line = None
        self.position_markers = []
        self.origin_marker = None
        self.track_data = {}
        
        # 設置繪圖環境
        self.setup_plot()
        
    def setup_plot(self):
        """設置繪圖環境"""
        # 設置軸標籤
        self.setLabel('left', 'Y Position (m)', color='white', size='12pt')
        self.setLabel('bottom', 'X Position (m)', color='white', size='12pt')
        self.setTitle('F1 賽道地圖', color='white', size='14pt')
        
        # 設置背景顏色
        self.setBackground('black')
        
        # 啟用網格
        self.showGrid(x=True, y=True, alpha=0.3)
        
        # 設置滑鼠交互
        self.setMouseEnabled(x=True, y=True)  # 啟用滑鼠平移和縮放
        
        # 連接視圖變更信號
        self.getViewBox().sigRangeChanged.connect(self._on_view_changed)
        
        self.logger.info("賽道地圖組件初始化完成")
        
    def plot_track_from_json(self, track_data: Dict):
        """
        從 JSON 數據繪製賽道（含原點標註）
        
        Args:
            track_data: 賽道數據字典
        """
        self.track_data = track_data
        
        # 獲取位置記錄
        positions = track_data.get('detailed_position_records', [])
        if not positions:
            self.logger.warning("沒有位置記錄數據可繪製")
            return
        
        # 提取座標
        x_coords = [pos['position_x'] for pos in positions]
        y_coords = [pos['position_y'] for pos in positions]
        
        # 清除先前的繪圖
        self.clear()
        
        # 繪製賽道路線
        self.plot_track_line(x_coords, y_coords)
        
        # 繪製位置標記
        self.plot_position_markers(x_coords, y_coords)
        
        # 標註原點 (JSON第一個信號點)
        self.mark_origin_point(positions[0])
        
        # 自動調整視圖範圍
        self.auto_range()
        
        self.logger.info(f"成功繪製賽道，共 {len(positions)} 個位置點")
        
    def plot_track_line(self, x_coords: List[float], y_coords: List[float]):
        """
        繪製賽道路線
        
        Args:
            x_coords: X座標列表
            y_coords: Y座標列表
        """
        # 使用白色線條繪製賽道輪廓
        pen = pg.mkPen(color='white', width=2)
        self.track_line = self.plot(
            x_coords, y_coords, 
            pen=pen, 
            name='賽道路線'
        )
        
    def plot_position_markers(self, x_coords: List[float], y_coords: List[float]):
        """
        繪製位置標記點
        
        Args:
            x_coords: X座標列表
            y_coords: Y座標列表
        """
        # 使用小的藍色圓點標記位置
        scatter = pg.ScatterPlotItem(
            x=x_coords, 
            y=y_coords,
            size=5,
            pen=pg.mkPen(color='cyan', width=1),
            brush=pg.mkBrush(color='cyan'),
            name='位置標記'
        )
        self.addItem(scatter)
        self.position_markers.append(scatter)
        
    def mark_origin_point(self, first_point: Dict):
        """
        標註原點 (JSON第一個信號點)
        
        Args:
            first_point: 第一個位置點數據
        """
        origin_x = first_point['position_x']
        origin_y = first_point['position_y']
        
        # 繪製紅色原點標記
        origin_scatter = pg.ScatterPlotItem(
            x=[origin_x], 
            y=[origin_y],
            size=12,
            pen=pg.mkPen(color='red', width=2),
            brush=pg.mkBrush(color='red'),
            name='起點 (原點)'
        )
        
        self.addItem(origin_scatter)
        self.origin_marker = origin_scatter
        
        self.logger.info(f"標註原點: ({origin_x:.1f}, {origin_y:.1f})")
        
    def auto_range(self):
        """自動調整視圖範圍以適應賽道"""
        if self.track_data:
            self.autoRange()
            
    def reset_view(self):
        """重置視圖到預設範圍"""
        self.auto_range()
        
    def zoom_in(self, factor: float = 1.2):
        """
        放大視圖
        
        Args:
            factor: 放大倍數
        """
        viewbox = self.getViewBox()
        viewbox.scaleBy((1/factor, 1/factor))
        
    def zoom_out(self, factor: float = 1.2):
        """
        縮小視圖
        
        Args:
            factor: 縮小倍數
        """
        viewbox = self.getViewBox()
        viewbox.scaleBy((factor, factor))
        
    def get_track_bounds(self) -> Tuple[float, float, float, float]:
        """
        獲取賽道邊界
        
        Returns:
            Tuple: (x_min, x_max, y_min, y_max)
        """
        if not self.track_data:
            return (0, 0, 0, 0)
            
        bounds = self.track_data.get('position_analysis', {}).get('track_bounds', {})
        return (
            bounds.get('x_min', 0.0),
            bounds.get('x_max', 0.0),
            bounds.get('y_min', 0.0),
            bounds.get('y_max', 0.0)
        )
        
    def clear_plot(self):
        """清除所有繪圖項目"""
        self.clear()
        self.track_line = None
        self.position_markers.clear()
        self.origin_marker = None
        self.track_data = {}
        
    def _on_view_changed(self):
        """視圖變更回調"""
        self.view_changed.emit()
        
    def mousePressEvent(self, event):
        """滑鼠點擊事件"""
        super().mousePressEvent(event)
        
        # 如果點擊在繪圖區域內，可以處理點選事件
        if event.button() == 1:  # 左鍵點擊
            scene_coords = self.getViewBox().mapSceneToView(event.pos())
            x, y = scene_coords.x(), scene_coords.y()
            self.logger.debug(f"滑鼠點擊座標: ({x:.1f}, {y:.1f})")
            
            # 這裡可以加入尋找最近位置點的邏輯
            # self._find_nearest_point(x, y)
            
    def _find_nearest_point(self, x: float, y: float) -> Optional[int]:
        """
        尋找最接近點擊位置的賽道點
        
        Args:
            x: 點擊的 X 座標
            y: 點擊的 Y 座標
            
        Returns:
            Optional[int]: 最近點的索引，如果沒有找到則返回 None
        """
        if not self.track_data:
            return None
            
        positions = self.track_data.get('detailed_position_records', [])
        if not positions:
            return None
            
        min_distance = float('inf')
        nearest_index = None
        
        for i, pos in enumerate(positions):
            pos_x = pos['position_x']
            pos_y = pos['position_y']
            distance = ((x - pos_x) ** 2 + (y - pos_y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_index = i
                
        if nearest_index is not None:
            self.point_selected.emit(nearest_index)
            
        return nearest_index
