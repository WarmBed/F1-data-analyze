# -*- coding: utf-8 -*-
"""
WorkspaceSnapshotApplier - 從 f1t_gui_main.py 提取
"""

from typing import Dict

from core.logger import get_logger

logger = get_logger(__name__)


class WorkspaceSnapshotApplier:
    """從 f1t_gui_main.py 提取的 _apply_workspace_snapshot 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _apply_workspace_snapshot(self, snapshot: Dict[str, object]) -> None:
        """根據快照資料套用工作區設定"""
        parameters = snapshot.get("parameters", {}) if isinstance(snapshot, dict) else {}

        year_value = parameters.get("year") if isinstance(parameters, dict) else None
        race_key = parameters.get("race_key") if isinstance(parameters, dict) else None
        race_display = parameters.get("race_display") if isinstance(parameters, dict) else None
        session_code = parameters.get("session") if isinstance(parameters, dict) else None

        if year_value:
            try:
                year_int = int(year_value)
            except (TypeError, ValueError):
                year_int = None
            if year_int:
                if hasattr(self, 'year_combo'):
                    self.main_window.year_combo.setCurrentText(str(year_int))
                self.main_window._refresh_calendar_for_year(year_int, preserve_race_key=race_key, preserve_session_code=session_code)

        if race_key:
            self.main_window._select_race_by_key(race_key)
        elif race_display and hasattr(self, 'race_combo'):
            index = self.main_window.race_combo.findText(race_display)
            if index >= 0:
                self.main_window.race_combo.setCurrentIndex(index)

        if session_code and hasattr(self, 'session_combo'):
            index = self.main_window.session_combo.findText(session_code)
            if index >= 0:
                self.main_window.session_combo.setCurrentIndex(index)

        linkage_enabled = snapshot.get("linkage_enabled") if isinstance(snapshot, dict) else None
        if linkage_enabled is not None and hasattr(self, 'linkage_action'):
            self.main_window.linkage_action.setChecked(bool(linkage_enabled))

        lap_controls = snapshot.get("lap_controls") if isinstance(snapshot, dict) else {}
        if isinstance(lap_controls, dict) and lap_controls:
            if hasattr(self, 'driver1_combo') and self.main_window.driver1_combo.count() == 0:
                self.main_window.initialize_driver_lists()

            driver1 = lap_controls.get("driver1")
            if driver1 and hasattr(self, 'driver1_combo'):
                index = self.main_window.driver1_combo.findText(driver1)
                if index >= 0:
                    self.main_window.driver1_combo.setCurrentIndex(index)

            driver2 = lap_controls.get("driver2")
            if driver2 and hasattr(self, 'driver2_combo'):
                index = self.main_window.driver2_combo.findText(driver2)
                if index >= 0:
                    self.main_window.driver2_combo.setCurrentIndex(index)

            lap1 = lap_controls.get("lap1")
            if lap1 and hasattr(self, 'lap1_spinbox'):
                try:
                    self.main_window.lap1_spinbox.setValue(int(lap1))
                except (TypeError, ValueError):
                    pass

            lap2 = lap_controls.get("lap2")
            if lap2 and hasattr(self, 'lap2_spinbox'):
                try:
                    self.main_window.lap2_spinbox.setValue(int(lap2))
                except (TypeError, ValueError):
                    pass

            fastest_lap = lap_controls.get("fastest_lap")
            if fastest_lap is not None and hasattr(self, 'fastest_lap_checkbox'):
                self.main_window.fastest_lap_checkbox.setChecked(bool(fastest_lap))

            if hasattr(self, 'on_lap_parameters_changed'):
                self.main_window.on_lap_parameters_changed()

        open_windows_state = snapshot.get("open_windows") if isinstance(snapshot, dict) else None
        self.main_window._restore_open_windows(open_windows_state)
