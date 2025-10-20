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
    filter_yellow_flags: bool = True  # 新增：過濾黃旗圈
    filter_red_flags: bool = True  # 新增：過濾紅旗圈


@dataclass(frozen=True)
class ThrottleLineChartSettings:
    """Throttle Line Chart 預設顯示設定"""
    show_full_duration: bool = False
    show_ratio: bool = True
    show_average: bool = True
    show_delta: bool = False
    rolling_average: bool = False
    rolling_window: int = 3
    highlight_threshold: bool = True
    threshold_percent: float = 90.0


@dataclass(frozen=True)
class StraightSpeedAnalysisSettings:
    """Straight Speed Analysis 欄位顯示設定"""
    # All Drivers Speed 欄位 (車手、車隊、Accel Time、Avg Accel 永遠顯示)
    speed_show_max_speed: bool = False
    speed_show_start_speed: bool = False
    speed_show_max_speed_time: bool = False
    speed_show_performance_bar: bool = True
    
    # All Drivers Brake 欄位 (車手、車隊、Brake Time、Avg Decel 永遠顯示)
    brake_show_max_decel: bool = False
    brake_show_start_speed: bool = False
    brake_show_performance_bar: bool = True


class GuiSettingsManager(QObject):
    """Centralized GUI settings manager with signal-based updates."""

    boxplot_settings_changed = pyqtSignal(dict)
    throttle_line_chart_settings_changed = pyqtSignal(dict)  # 新增：Throttle Line Chart 設定變更訊號
    straight_speed_analysis_settings_changed = pyqtSignal(dict)  # 新增：Straight Speed Analysis 設定變更訊號

    def __init__(self) -> None:
        super().__init__()
        self._boxplot_settings: BoxPlotSettings = BoxPlotSettings()
        self._throttle_line_chart_settings: ThrottleLineChartSettings = ThrottleLineChartSettings()  # 新增
        self._straight_speed_analysis_settings: StraightSpeedAnalysisSettings = StraightSpeedAnalysisSettings()  # 新增

    # ------------------------------------------------------------------
    # Box plot settings
    # ------------------------------------------------------------------
    def get_boxplot_settings(self) -> Dict[str, float | bool]:
        settings = {
            "filter_pit_laps": self._boxplot_settings.filter_pit_laps,
            "filter_outliers": self._boxplot_settings.filter_outliers,
            "outlier_threshold": self._boxplot_settings.outlier_threshold,
            "filter_yellow_flags": self._boxplot_settings.filter_yellow_flags,
            "filter_red_flags": self._boxplot_settings.filter_red_flags,
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
    # Throttle Line Chart settings
    # ------------------------------------------------------------------
    def get_throttle_line_chart_settings(self) -> Dict[str, float | bool | int]:
        """取得 Throttle Line Chart 設定"""
        settings = {
            "show_full_duration": self._throttle_line_chart_settings.show_full_duration,
            "show_ratio": self._throttle_line_chart_settings.show_ratio,
            "show_average": self._throttle_line_chart_settings.show_average,
            "show_delta": self._throttle_line_chart_settings.show_delta,
            "rolling_average": self._throttle_line_chart_settings.rolling_average,
            "rolling_window": self._throttle_line_chart_settings.rolling_window,
            "highlight_threshold": self._throttle_line_chart_settings.highlight_threshold,
            "threshold_percent": self._throttle_line_chart_settings.threshold_percent,
        }
        return settings

    def update_throttle_line_chart_settings(self, **kwargs) -> None:
        """更新 Throttle Line Chart 設定"""
        current = self.get_throttle_line_chart_settings()
        changed = False
        for key, value in kwargs.items():
            if key in current and current[key] != value:
                current[key] = value
                changed = True

        if not changed:
            return

        self._throttle_line_chart_settings = ThrottleLineChartSettings(**current)
        self.throttle_line_chart_settings_changed.emit(self.get_throttle_line_chart_settings())

    # ------------------------------------------------------------------
    # Straight Speed Analysis settings
    # ------------------------------------------------------------------
    def get_straight_speed_analysis_settings(self) -> Dict[str, bool]:
        """取得 Straight Speed Analysis 設定"""
        settings = {
            "speed_show_max_speed": self._straight_speed_analysis_settings.speed_show_max_speed,
            "speed_show_start_speed": self._straight_speed_analysis_settings.speed_show_start_speed,
            "speed_show_max_speed_time": self._straight_speed_analysis_settings.speed_show_max_speed_time,
            "speed_show_performance_bar": self._straight_speed_analysis_settings.speed_show_performance_bar,
            "brake_show_max_decel": self._straight_speed_analysis_settings.brake_show_max_decel,
            "brake_show_start_speed": self._straight_speed_analysis_settings.brake_show_start_speed,
            "brake_show_performance_bar": self._straight_speed_analysis_settings.brake_show_performance_bar,
        }
        return settings

    def update_straight_speed_analysis_settings(self, **kwargs) -> None:
        """更新 Straight Speed Analysis 設定"""
        current = self.get_straight_speed_analysis_settings()
        changed = False
        for key, value in kwargs.items():
            if key in current and current[key] != value:
                current[key] = value
                changed = True

        if not changed:
            return

        self._straight_speed_analysis_settings = StraightSpeedAnalysisSettings(**current)
        self.straight_speed_analysis_settings_changed.emit(self.get_straight_speed_analysis_settings())

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
