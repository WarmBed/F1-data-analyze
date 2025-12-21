# -*- coding: utf-8 -*-
"""
WorkspaceSnapshotBuilder - 從 f1t_gui_main.py 提取
"""

from typing import Dict
import datetime

from core.logger import get_logger
from modules.gui.shared.season_calendar_provider import SeasonEvent

logger = get_logger(__name__)


class WorkspaceSnapshotBuilder:
    """從 f1t_gui_main.py 提取的 _build_workspace_snapshot 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _build_workspace_snapshot(self) -> Dict[str, object]:
        """產生目前工作區的序列化快照"""
        selected_event = self.main_window.get_selected_event()
        race_key = selected_event.race_key if isinstance(selected_event, SeasonEvent) else self.main_window.get_selected_race_key()
        snapshot = {
            "version": 2,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "parameters": {
                "year": self.main_window.year_combo.currentText() if hasattr(self, 'year_combo') else None,
                "race_display": self.main_window.race_combo.currentText() if hasattr(self, 'race_combo') else None,
                "race_key": race_key,
                "session": self.main_window.get_selected_session_code() if hasattr(self, 'session_combo') else None,
            },
            "linkage_enabled": self.main_window.linkage_action.isChecked() if hasattr(self, 'linkage_action') else True,
            "lap_controls": {
                "driver1": self.main_window.driver1_combo.currentText() if hasattr(self, 'driver1_combo') else None,
                "driver2": self.main_window.driver2_combo.currentText() if hasattr(self, 'driver2_combo') else None,
                "lap1": self.main_window.lap1_spinbox.value() if hasattr(self, 'lap1_spinbox') else None,
                "lap2": self.main_window.lap2_spinbox.value() if hasattr(self, 'lap2_spinbox') else None,
                "fastest_lap": self.main_window.fastest_lap_checkbox.isChecked() if hasattr(self, 'fastest_lap_checkbox') else None,
            },
        }
        snapshot["open_windows"] = self.main_window._collect_open_windows_state()
        return snapshot
