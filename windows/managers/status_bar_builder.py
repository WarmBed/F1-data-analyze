# -*- coding: utf-8 -*-
"""
StatusBarBuilder - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from core.gui_i18n import tr

from core.logger import get_logger
from PyQt5.QtWidgets import QStatusBar

logger = get_logger(__name__)


class StatusBarBuilder:
    """從 f1t_gui_main.py 提取的 create_professional_status_bar 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_professional_status_bar(self):
        """Create professional status bar - 簡化版，只顯示 API 狀態"""
        status_bar = QStatusBar()
        status_bar.setFixedHeight(16)
        self.main_window.setStatusBar(status_bar)

        # 只保留 API 狀態指示器
        self.main_window.api_status_label = QLabel('[API] Pending')
        self.main_window.api_status_label.setObjectName('StatusApi')
        self.main_window.api_status_label.setStyleSheet('color: #f1c40f; font-weight: bold;')
        
        # 保留變數引用以避免其他代碼報錯，但不顯示
        self.main_window.ready_label = QLabel('')
        self.main_window.cli_status_label = QLabel('')
        self.main_window.time_label = QLabel('')

        # 只添加 API 狀態
        status_bar.addWidget(self.main_window.api_status_label)
        
        # F1TV 狀態指示器
        self.main_window.f1tv_status_label = QLabel('[F1TV] Not Logged In')
        self.main_window.f1tv_status_label.setObjectName('StatusF1TV')
        self.main_window.f1tv_status_label.setStyleSheet('color: #888888; font-weight: bold;')
        self.main_window.f1tv_status_label.setCursor(Qt.PointingHandCursor)
        self.main_window.f1tv_status_label.setToolTip(tr('f1tv_click_to_login', 'Click to login to F1TV account'))
        self.main_window.f1tv_status_label.mousePressEvent = lambda e: self.main_window._open_f1tv_auth_dialog()
        status_bar.addWidget(self.main_window.f1tv_status_label)
        
        # 初始化 F1TV 狀態顯示
        self.main_window._update_f1tv_status_label()

        # Refresh status information
        self.main_window.update_status_bar()
