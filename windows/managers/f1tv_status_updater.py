# -*- coding: utf-8 -*-
"""
F1tvStatusUpdater - 從 f1t_gui_main.py 提取
"""

from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(__name__)


class F1tvStatusUpdater:
    """從 f1t_gui_main.py 提取的 _update_f1tv_status_label 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _update_f1tv_status_label(self):
        """更新 F1TV 狀態標籤"""
        if not hasattr(self.main_window, 'f1tv_status_label') or self.main_window.f1tv_status_label is None:
            return
        
        if not hasattr(self.main_window, 'f1tv_auth_manager') or self.main_window.f1tv_auth_manager is None:
            self.main_window.f1tv_status_label.setText('[F1TV] Not Logged In')
            self.main_window.f1tv_status_label.setStyleSheet('color: #888888; font-weight: bold;')
            return
        
        token_info = self.main_window.f1tv_auth_manager.get_token_info()
        
        if token_info is None:
            self.main_window.f1tv_status_label.setText('[F1TV] Not Logged In')
            self.main_window.f1tv_status_label.setStyleSheet('color: #888888; font-weight: bold;')
            self.main_window.f1tv_status_label.setToolTip(tr(
                'f1tv_click_to_login',
                'Click to login to F1TV account'
            ))
        elif token_info.get('expired'):
            self.main_window.f1tv_status_label.setText('[F1TV] Expired')
            self.main_window.f1tv_status_label.setStyleSheet('color: #f1c40f; font-weight: bold;')
            self.main_window.f1tv_status_label.setToolTip(tr(
                'f1tv_token_expired',
                'Token expired. Click to re-login.'
            ))
        else:
            self.main_window.f1tv_status_label.setText('[F1TV] Logged In')
            self.main_window.f1tv_status_label.setStyleSheet('color: #2ecc71; font-weight: bold;')
            product = token_info.get('product', 'F1TV')
            exp_str = token_info.get('exp_str', 'Unknown')
            self.main_window.f1tv_status_label.setToolTip(f"{product}\nExpires: {exp_str}")
