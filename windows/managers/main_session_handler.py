# -*- coding: utf-8 -*-
"""
MainSessionHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class MainSessionHandler:
    """從 f1t_gui_main.py 提取的 on_main_session_changed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_main_session_changed(self, session):
        """主視窗賽段變更處理"""
        # ✅ 調試點 1: 方法入口
        logger.info(f"🔵 [DEBUG]    on_main_session_changed 被調用: session={session}")
        logger.debug(f"🔵 [DEBUG]    on_main_session_changed 被調用: session={session}")
        
        session_code = self.main_window.get_selected_session_code()
        logger.debug(f"[F1] [MAIN] 主視窗賽段變更為: {session_code}")
        logger.info(f"[F1] [MAIN] 主視窗賽段變更為: {session_code}")
        self.main_window.update_status_bar()
        
        # Debounced parameter broadcast for main window session change
        logger.info("🔵 [DEBUG]    on_main_session_changed - scheduling parameter broadcast")
        logger.debug("🔵 [DEBUG]    on_main_session_changed - scheduling parameter broadcast")
        self.main_window._schedule_parameter_broadcast("main_session_changed")
