"""Global GUI settings manager for centralized configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from PyQt5.QtCore import QObject, pyqtSignal


@dataclass(frozen=True)
class BoxPlotSettings:
    filter_pit_laps: bool = True
    filter_outliers: bool = True
    outlier_threshold: float = 1.5


class GuiSettingsManager(QObject):
    """Centralized GUI settings manager with signal-based updates."""

    boxplot_settings_changed = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._boxplot_settings: BoxPlotSettings = BoxPlotSettings()

    # ------------------------------------------------------------------
    # Box plot settings
    # ------------------------------------------------------------------
    def get_boxplot_settings(self) -> Dict[str, float | bool]:
        settings = {
            "filter_pit_laps": self._boxplot_settings.filter_pit_laps,
            "filter_outliers": self._boxplot_settings.filter_outliers,
            "outlier_threshold": self._boxplot_settings.outlier_threshold,
        }
        return settings

    def update_boxplot_settings(self, **kwargs) -> None:
        current = self.get_boxplot_settings()
        changed = False
        for key, value in kwargs.items():
            if key in current and current[key] != value:
                current[key] = value
                changed = True

        if not changed:
            return

        self._boxplot_settings = BoxPlotSettings(**current)
        self.boxplot_settings_changed.emit(self.get_boxplot_settings())

    # ------------------------------------------------------------------
    # Dialog helpers
    # ------------------------------------------------------------------
    def open_system_settings_dialog(self, parent=None) -> None:
        """Open the System Settings dialog."""
        from modules.gui.settings.system_settings_dialog import SystemSettingsDialog

        dialog = SystemSettingsDialog(parent=parent, settings_manager=self)
        dialog.exec_()


# Global singleton instance
_gui_settings_manager: GuiSettingsManager | None = None


def get_gui_settings_manager() -> GuiSettingsManager:
    global _gui_settings_manager
    if _gui_settings_manager is None:
        _gui_settings_manager = GuiSettingsManager()
    return _gui_settings_manager


# Convenient alias
gui_settings_manager = get_gui_settings_manager()
