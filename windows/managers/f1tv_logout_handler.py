# -*- coding: utf-8 -*-
"""
F1tvLogoutHandler - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr

from core.logger import get_logger

logger = get_logger(__name__)


class F1tvLogoutHandler:
    """從 f1t_gui_main.py 提取的 _logout_f1tv 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _logout_f1tv(self, *args, **kwargs):
        """登出 F1TV
        
        Args:
            *args: 接收 signal 傳遞的額外參數
            **kwargs: 接收其他關鍵字參數
        """
        if not self.main_window.f1tv_auth_manager or not self.main_window.f1tv_auth_manager.is_authenticated():
            QMessageBox.information(
                self.main_window,
                tr('f1tv_login_title', 'F1TV Account'),
                tr('f1tv_not_logged_in', 'Not Logged In')
            )
            return
        
        reply = QMessageBox.question(
            self.main_window,
            tr('confirm', 'Confirm'),
            tr('f1tv_logout_confirm', 'Are you sure you want to logout from F1TV?'),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.main_window.f1tv_auth_manager.clear_token()
