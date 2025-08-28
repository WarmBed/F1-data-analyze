"""
賽道地圖子視窗
Track Map Sub Window

基於 QMdiSubWindow 的賽道地圖容器
"""

import logging
try:
    from PySide6.QtWidgets import QMdiSubWindow, QWidget, QVBoxLayout
    from PySide6.QtCore import Qt
except ImportError:
    try:
        from PyQt6.QtWidgets import QMdiSubWindow, QWidget, QVBoxLayout
        from PyQt6.QtCore import Qt
    except ImportError:
        from PyQt5.QtWidgets import QMdiSubWindow, QWidget, QVBoxLayout
        from PyQt5.QtCore import Qt

from typing import Dict, Optional
from ..models.track_data_model import TrackDataModel
from .track_map_widget import TrackMapWidget


class TrackMapSubWindow(QMdiSubWindow):
    """簡化的賽道地圖子視窗"""
    
    def __init__(self, track_data: Dict, parent: Optional[QWidget] = None):
        """
        初始化賽道地圖子視窗
        
        Args:
            track_data: 賽道數據字典
            parent: 父組件
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # 創建數據模型
        self.data_model = TrackDataModel(track_data)
        
        # 創建賽道繪圖組件
        self.track_widget = TrackMapWidget()
        
        # 設置子視窗內容
        self.setWidget(self.track_widget)
        
        # 設置視窗標題
        race_name = self.data_model.get_race_name()
        self.setWindowTitle(f"賽道地圖 - {race_name}")
        
        # 設置視窗大小
        self.resize(800, 600)
        
        # 載入賽道數據
        self.load_track_data()
        
        self.logger.info(f"賽道地圖子視窗創建完成: {race_name}")
        
    def load_track_data(self):
        """載入賽道數據到繪圖組件"""
        try:
            # 驗證數據
            if not self.data_model.validate_data():
                self.logger.error("賽道數據驗證失敗")
                return
                
            # 繪製賽道
            self.track_widget.plot_track_from_json(self.data_model.track_data)
            
            # 記錄統計信息
            total_points = self.data_model.get_total_points()
            total_distance = self.data_model.get_total_distance()
            
            self.logger.info(f"賽道數據載入完成 - 點數: {total_points}, 距離: {total_distance:.1f}m")
            
        except Exception as e:
            self.logger.error(f"載入賽道數據時發生錯誤: {e}")
            
    def get_track_widget(self) -> TrackMapWidget:
        """
        獲取賽道繪圖組件
        
        Returns:
            TrackMapWidget: 賽道繪圖組件
        """
        return self.track_widget
        
    def get_data_model(self) -> TrackDataModel:
        """
        獲取數據模型
        
        Returns:
            TrackDataModel: 賽道數據模型
        """
        return self.data_model
        
    def reset_view(self):
        """重置視圖"""
        self.track_widget.reset_view()
        
    def zoom_in(self):
        """放大視圖"""
        self.track_widget.zoom_in()
        
    def zoom_out(self):
        """縮小視圖"""
        self.track_widget.zoom_out()
        
    def closeEvent(self, event):
        """視窗關閉事件"""
        self.logger.info(f"關閉賽道地圖子視窗: {self.windowTitle()}")
        super().closeEvent(event)
