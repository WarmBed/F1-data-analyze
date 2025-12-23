# -*- coding: utf-8 -*-
"""
LeftPanelCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger

logger = get_logger(__name__)


class LeftPanelCreator:
    """從 f1t_gui_main.py 提取的 create_left_panel 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_left_panel(self):
        """創建左側面板 (僅包含功能樹)。"""
        widget = QWidget()
        widget.setObjectName("LeftPanel")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)

        function_tree = self.main_window.create_professional_function_tree()
        layout.addWidget(function_tree)

        return widget
