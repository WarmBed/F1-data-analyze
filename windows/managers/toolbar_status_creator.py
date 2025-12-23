# -*- coding: utf-8 -*-
"""
ToolbarStatusCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger

logger = get_logger(__name__)


class ToolbarStatusCreator:
    """從 f1t_gui_main.py 提取的 _create_toolbar_status_widget 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _create_toolbar_status_widget(self) -> QWidget:
        """創建工具欄狀態信息小部件"""
        status_container = QWidget()
        status_container.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        
        layout = QHBoxLayout(status_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 模組名稱標籤
        self.main_window.toolbar_module_label = QLabel("")
        self.main_window.toolbar_module_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(self.main_window.toolbar_module_label)
        
        # 圈時間標籤
        self.main_window.toolbar_lap_time_label = QLabel("")
        self.main_window.toolbar_lap_time_label.setStyleSheet("""
            QLabel {
                color: #D84315;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(self.main_window.toolbar_lap_time_label)
        
        # 輪胎配方標籤
        self.main_window.toolbar_tyre_label = QLabel("")
        self.main_window.toolbar_tyre_label.setStyleSheet("""
            QLabel {
                color: #388E3C;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(self.main_window.toolbar_tyre_label)
        
        # 圈數標籤
        self.main_window.toolbar_lap_numbers_label = QLabel("")
        self.main_window.toolbar_lap_numbers_label.setStyleSheet("""
            QLabel {
                color: #7B1FA2;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(self.main_window.toolbar_lap_numbers_label)
        
        # 初始隱藏
        status_container.setVisible(False)
        
        return status_container
