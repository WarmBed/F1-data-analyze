# -*- coding: utf-8 -*-
"""
F1tvAuthOpener - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(__name__)


class F1tvAuthOpener:
    """從 f1t_gui_main.py 提取的 _open_f1tv_auth_dialog 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _open_f1tv_auth_dialog(self, *args, **kwargs):
        """開啟 F1TV 登入對話框 (使用 QWebEngineView)
        
        Args:
            *args: 接收 signal 傳遞的額外參數 (例如 triggered 的 checked)
            **kwargs: 接收其他關鍵字參數
        """
        # 檢查是否已登入
        if self.main_window.f1tv_auth_manager.is_authenticated():
            token_info = self.main_window.f1tv_auth_manager.get_token_info()
            product = token_info.get('product', 'F1TV') if token_info else 'F1TV'
            exp_str = token_info.get('exp_str', 'Unknown') if token_info else 'Unknown'
            
            reply = QMessageBox.question(
                self.main_window,
                tr('f1tv_login_title', 'F1TV Account'),
                tr('f1tv_already_logged_in', 
                   'You are already logged in.\n\nProduct: {product}\nExpires: {exp_str}\n\nDo you want to re-login?'
                ).format(product=product, exp_str=exp_str),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # 顯示隱私通知對話框
        privacy_notice = QMessageBox(self.main_window)
        privacy_notice.setIcon(QMessageBox.Information)
        privacy_notice.setWindowTitle(tr('f1tv_privacy_notice_title', 'Privacy Notice'))
        privacy_notice.setText(
            tr('f1tv_privacy_notice_text', 
               'Your F1 TV account credentials will NOT be transmitted anywhere.\n\n'
               'This authentication is only used for accessing Realtime Live Timing data.')
        )
        privacy_notice.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        privacy_notice.setDefaultButton(QMessageBox.Ok)
        
        if privacy_notice.exec_() != QMessageBox.Ok:
            return
        
        # 啟動認證流程 (使用 QWebEngineView)
        logger.debug("[F1TV] Starting authentication flow...")
        self.main_window.f1tv_auth_manager.start_auth_flow(self.main_window)
