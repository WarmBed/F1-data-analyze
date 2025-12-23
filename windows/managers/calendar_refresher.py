# -*- coding: utf-8 -*-
"""
CalendarRefresher - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QWidget

from core.logger import get_logger
from core.gui_i18n import tr
from typing import Optional
from modules.gui.shared.season_calendar_provider import SeasonEvent
from f1t_gui_main import select_preferred_event

logger = get_logger(__name__)


class CalendarRefresher:
    """從 f1t_gui_main.py 提取的 _refresh_calendar_for_year 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _refresh_calendar_for_year(
        self,
        year: int,
        *,
        preserve_race_key: Optional[str] = None,
        preserve_session_code: Optional[str] = None,
    ) -> None:
        events = self._get_calendar_events(year)

        self.race_combo.blockSignals(True)
        self.race_combo.clear()
        self._race_event_lookup.clear()
        self._display_to_race_key.clear()

        if events:
            completed_events = [event for event in events if event.is_completed]
            upcoming_events = [event for event in events if not event.is_completed]

            def add_event_to_combo(event: SeasonEvent) -> None:
                label = self._format_race_display(event)
                self._race_event_lookup[event.race_key] = event
                self._display_to_race_key[label] = event.race_key
                self._display_to_race_key[event.display_label] = event.race_key
                plain_label = self._strip_race_display(label)
                if plain_label:
                    self._display_to_race_key.setdefault(plain_label, event.race_key)
                self.race_combo.addItem(label, event)

            for event in completed_events:
                add_event_to_combo(event)

            if completed_events and upcoming_events:
                self.race_combo.insertSeparator(self.race_combo.count())

            for event in upcoming_events:
                add_event_to_combo(event)

            selection_applied = False
            if preserve_race_key and preserve_race_key in self._race_event_lookup:
                target_event = self._race_event_lookup[preserve_race_key]
                index = self.race_combo.findData(target_event)
                if index >= 0:
                    self.race_combo.setCurrentIndex(index)
                    selection_applied = True

            if not selection_applied:
                preferred_event = select_preferred_event(completed_events, upcoming_events)
                if preferred_event is not None:
                    self._select_race_by_key(preferred_event.race_key)
                    selection_applied = self.race_combo.currentIndex() >= 0

            if not selection_applied and self.race_combo.count() > 0:
                self.race_combo.setCurrentIndex(0)
        else:
            placeholder = tr("season_calendar_placeholder", "[無已完成賽事]")
            self.race_combo.addItem(placeholder, None)

        self.race_combo.blockSignals(False)

        self._update_session_combo(preserve_session_code=preserve_session_code)

        # 同步本地參數以便其他模組獲取正確預設值
        self.local_year = str(year)
        selected_event = self.get_selected_event()
        if selected_event:
            self.local_race = selected_event.race_key
        logger.debug(
            "[RACE_DEFAULT][MAIN] final selection: %s",
            {
                "index": self.race_combo.currentIndex(),
                "text": self.race_combo.currentText(),
                "race_key": getattr(selected_event, "race_key", None),
            },
        )
        self.local_session = self.get_selected_session_code()

        if self._season_error_message and self.statusBar():
            self.statusBar().showMessage(self._season_error_message, 10000)
