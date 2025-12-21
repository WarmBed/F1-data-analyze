# -*- coding: utf-8 -*-
"""
CalendarEventsGetter - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from typing import List

from core.logger import get_logger
from modules.gui.shared.season_calendar_provider import SeasonEvent

logger = get_logger(__name__)


class CalendarEventsGetter:
    """從 f1t_gui_main.py 提取的 _get_calendar_events 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _get_calendar_events(self, year: int) -> List[SeasonEvent]:
        """Fetch completed events for the given year with basic caching."""
        if year in self.main_window._season_events_cache and self.main_window._season_events_cache[year]:
            return self.main_window._season_events_cache[year]

        try:
            events = self.main_window._season_provider.get_completed_events(year)
            if events:
                self.main_window._season_events_cache[year] = events
            self.main_window._season_error_message = None
            return events
        except SeasonCalendarError as exc:
            self.main_window._season_error_message = str(exc)
            logger.debug(f"[CALENDAR] {self.main_window._season_error_message}")
            return self.main_window._season_events_cache.get(year, [])
