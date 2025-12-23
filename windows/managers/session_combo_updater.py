# -*- coding: utf-8 -*-
"""
SessionComboUpdater - 從 f1t_gui_main.py 提取
"""

from typing import Optional
from modules.gui.shared.season_calendar_provider import SeasonEvent

from core.logger import get_logger

logger = get_logger(__name__)


class SessionComboUpdater:
    """從 f1t_gui_main.py 提取的 _update_session_combo 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _update_session_combo(
        self,
        event: Optional[SeasonEvent] = None,
        *,
        preserve_session_code: Optional[str] = None,
    ) -> None:
        event = event or self.main_window.race_combo.currentData()
        self.main_window.session_combo.blockSignals(True)
        self.main_window.session_combo.clear()

        if isinstance(event, SeasonEvent) and event.sessions:
            codes_in_order = []
            for session in event.sessions:
                self.main_window.session_combo.addItem(session.code, session)
                codes_in_order.append(session.code)

            target_code = preserve_session_code or ("R" if "R" in codes_in_order else codes_in_order[0])
            index = self.main_window.session_combo.findText(target_code)
            if index < 0:
                index = self.main_window.session_combo.findText(target_code.upper())
            if index >= 0:
                self.main_window.session_combo.setCurrentIndex(index)
            elif self.main_window.session_combo.count() > 0:
                self.main_window.session_combo.setCurrentIndex(0)
        else:
            for code in ["FP1", "FP2", "FP3", "SQ", "S", "Q", "R"]:
                self.main_window.session_combo.addItem(code)
            if preserve_session_code:
                index = self.main_window.session_combo.findText(preserve_session_code)
                if index >= 0:
                    self.main_window.session_combo.setCurrentIndex(index)

        self.main_window.session_combo.blockSignals(False)
