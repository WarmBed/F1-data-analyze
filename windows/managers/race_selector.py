# -*- coding: utf-8 -*-
"""
RaceSelector - 從 f1t_gui_main.py 提取
"""

from typing import Optional

from core.logger import get_logger
from modules.gui.shared.season_calendar_provider import SeasonEvent

logger = get_logger(__name__)


class RaceSelector:
    """從 f1t_gui_main.py 提取的 _select_race_by_key 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _select_race_by_key(self, race_key: Optional[str]) -> None:
        """Select a race in the main race combo using its canonical key."""
        if not race_key or not self.main_window.race_combo:
            return

        # Preferred path: direct lookup from cached events
        event = self.main_window._race_event_lookup.get(race_key)
        if event is not None:
            index = self.main_window.race_combo.findData(event)
            if index >= 0:
                self.main_window.race_combo.setCurrentIndex(index)
                return

        # Fallback: resolve through display mapping or iterate items
        canonical_key = self.main_window._display_to_race_key.get(race_key, race_key)
        for index in range(self.main_window.race_combo.count()):
            data = self.main_window.race_combo.itemData(index)
            if isinstance(data, SeasonEvent) and data.race_key == canonical_key:
                self.main_window.race_combo.setCurrentIndex(index)
                return

            text = self.main_window.race_combo.itemText(index)
            mapped = self.main_window._display_to_race_key.get(text)
            if mapped == canonical_key:
                self.main_window.race_combo.setCurrentIndex(index)
                return

            if self.main_window._strip_race_display(text) == canonical_key:
                self.main_window.race_combo.setCurrentIndex(index)
                return
