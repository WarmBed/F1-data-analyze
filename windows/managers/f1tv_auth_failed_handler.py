# -*- coding: utf-8 -*-
"""
F1tvAuthFailedHandler - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(__name__)


class F1tvAuthFailedHandler:
    """從 f1t_gui_main.py 提取的 _on_f1tv_auth_failed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _on_f1tv_auth_failed(self, error: str):
        """F1TV 認證失敗回調"""
        logger.debug(f"[F1TV] Authentication failed: {error}")
        QMessageBox.warning(
            self.main_window,
            tr('error', 'Error'),
            tr('f1tv_login_failed', 'Login failed: {error}').format(error=error)
        )
