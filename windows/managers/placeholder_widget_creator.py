# -*- coding: utf-8 -*-
"""
PlaceholderWidgetCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger

logger = get_logger(__name__)


class PlaceholderWidgetCreator:
    """從 f1t_gui_main.py 提取的 create_placeholder_telemetry_widget 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_placeholder_telemetry_widget(self, chart_type):
        """為尚未實現的圖表類型創建佔位符Widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        chart_info = self.main_window.get_chart_info(chart_type)
        
        # 標題
        title_label = QLabel(f"{chart_info['icon']} {chart_info['name']}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078d4; margin: 20px;")
        layout.addWidget(title_label)
        
        # 訊息
        message_label = QLabel("此圖表類型正在開發中...\n請等待後續版本更新")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("font-size: 14px; color: #666; margin: 20px;")
        layout.addWidget(message_label)
        
        # 狀態標籤
        status_label = QLabel("🚧 開發中 🚧")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("font-size: 16px; color: #ff6600; font-weight: bold; margin: 20px;")
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        return widget
