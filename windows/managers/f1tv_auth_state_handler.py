# -*- coding: utf-8 -*-
"""
F1tvAuthStateHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

logger = get_logger(__name__)


class F1tvAuthStateHandler:
    """從 f1t_gui_main.py 提取的 _on_f1tv_auth_state_changed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _on_f1tv_auth_state_changed(self, authenticated: bool):
        """F1TV 認證狀態變更回調"""
        logger.debug(f"[F1TV] Auth state changed: authenticated={authenticated}")
        if hasattr(self.main_window, '_update_f1tv_status_label'):
            self.main_window._update_f1tv_status_label()
        if hasattr(self.main_window, '_broadcast_f1tv_auth_state'):
            self.main_window._broadcast_f1tv_auth_state(authenticated)
