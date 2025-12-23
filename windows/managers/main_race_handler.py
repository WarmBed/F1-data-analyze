# -*- coding: utf-8 -*-
"""
MainRaceHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class MainRaceHandler:
    """從 f1t_gui_main.py 提取的 on_main_race_changed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_main_race_changed(self, race):
        """主視窗賽事變更處理"""
        # ✅ 調試點 1: 方法入口
        logger.info(f"🔵 [DEBUG]    on_main_race_changed 被調用: race={race}")
        logger.debug(f"🔵 [DEBUG]    on_main_race_changed 被調用: race={race}")
        
        event = self.main_window.get_selected_event()
        self.main_window._update_session_combo(event)
        race_key = self.main_window.get_selected_race_key()
        logger.debug(f"[FINISH] [MAIN] 主視窗賽事變更為: {race_key}")
        logger.info(f"[FINISH] [MAIN] 主視窗賽事變更為: {race_key}")
        self.main_window.update_status_bar()
        
        # ✅ 調試點 2: 觸發批次更新前
        
        # Debounced parameter broadcast for main window race change
        logger.info("🔵 [DEBUG]    on_main_race_changed - scheduling parameter broadcast")
        logger.debug("🔵 [DEBUG]    on_main_race_changed - scheduling parameter broadcast")
        self.main_window._schedule_parameter_broadcast("main_race_changed")
