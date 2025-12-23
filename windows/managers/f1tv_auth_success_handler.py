# -*- coding: utf-8 -*-
"""
F1tvAuthSuccessHandler - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(__name__)


class F1tvAuthSuccessHandler:
    """從 f1t_gui_main.py 提取的 _on_f1tv_auth_success 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _on_f1tv_auth_success(self, token: str):
        """F1TV 認證成功回調"""
        logger.debug(f"[F1TV] Authentication successful (token length: {len(token)})")
        self.main_window._update_f1tv_status_label()
        QMessageBox.information(
            self.main_window,
            tr('success', 'Success'),
            tr('f1tv_login_success', 'Successfully logged in to F1TV!')
        )
