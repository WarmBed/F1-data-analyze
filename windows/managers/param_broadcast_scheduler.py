# -*- coding: utf-8 -*-
"""
ParamBroadcastScheduler - 從 f1t_gui_main.py 提取
"""

from core.gui_i18n import tr
from core.logger import get_logger
from core.api_runtime_state import set_pending_update

from core.logger import get_logger

logger = get_logger(__name__)


class ParamBroadcastScheduler:
    """從 f1t_gui_main.py 提取的 _schedule_parameter_broadcast 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _schedule_parameter_broadcast(self, reason: str) -> None:
        """Debounce rapid year/race/session changes before updating modules."""
        logger.info(f"[BROADCAST_DEBUG] _schedule_parameter_broadcast 被調用: reason={reason}")
        
        try:
            payload = {
                "reason": reason,
                "year": self.main_window.year_combo.currentText() if hasattr(self, "year_combo") else None,
                "race": self.main_window.get_selected_race_key() if hasattr(self, "get_selected_race_key") else None,
                "session": self.main_window.get_selected_session_code() if hasattr(self, "get_selected_session_code") else None,
            }
        except Exception as e:
            logger.error(f"[BROADCAST_DEBUG] 獲取參數時出錯: {e}")
            payload = {"reason": reason}

        self.main_window._pending_parameter_payload = payload
        set_pending_update(reason, payload)

        logger.info(f"[BROADCAST_DEBUG] Pending payload: {payload}")

        try:
            status_bar = self.main_window.statusBar()
            if status_bar:
                status_bar.showMessage(tr("pending_analysis_update", "Queuing analysis refresh…"), 1500)
        except Exception:
            pass

        logger.info("[PARAMS] Queued parameter broadcast (%s): %s", reason, payload)
        
        logger.info("[BROADCAST_DEBUG] 啟動 timer (350ms)")
        self.main_window._parameter_broadcast_timer.start()
