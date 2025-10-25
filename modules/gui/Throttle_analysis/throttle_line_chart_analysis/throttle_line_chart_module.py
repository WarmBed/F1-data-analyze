# -*- coding: utf-8 -*-
"""ThrottleLineChartModule - 單車手油門折線圖 GUI 模組。"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from PyQt5.QtWidgets import QWidget

try:  # pragma: no cover - 避免相對匯入失敗
    from ...interfaces.analysis_module import IAnalysisModule, ModuleFactory, ModuleTypes
except ImportError:  # pragma: no cover
    from modules.gui.interfaces.analysis_module import IAnalysisModule, ModuleFactory, ModuleTypes

from core.gui_i18n import tr

from .throttle_line_chart_mdi import ThrottleLineChartMDI


class ThrottleLineChartModule(IAnalysisModule):
    """整合 ThrottleLineChartMDI 與分析模組介面的包裝類。"""

    def __init__(self, parent=None, year: Optional[int] = None, race: Optional[str] = None, session: Optional[str] = None, driver: Optional[str] = None):
        super().__init__(parent)
        self._module_name = "throttle_line_chart"
        self._display_name = tr("throttle_line_chart.title", "Throttle Line Chart (Single Driver)")
        self._version = "1.0.0"
        self._description = tr(
            "throttle_line_chart.description",
            "Lap-by-lap full throttle duration vs lap time with synchronized charts",
        )

        self.current_year = str(year) if year is not None else "2025"
        self.current_race = race or "Japan"
        self.current_session = session or "R"
        self.current_driver = (driver or "VER").upper()

        self._mdi: Optional[ThrottleLineChartMDI] = None
        self._main_widget: Optional[QWidget] = None
        self._parameter_provider = None
        self._pending_parent_window = None

    # ------------------------------------------------------------------
    @property
    def module_name(self) -> str:
        return self._module_name

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return self._description

    # ------------------------------------------------------------------
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        if self._mdi is not None:
            return True
        try:
            self._mdi = ThrottleLineChartMDI(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                driver=self.current_driver,
                parent=parent_widget,
                **kwargs,
            )
            if hasattr(self._mdi, "driverChanged"):
                self._mdi.driverChanged.connect(self._on_mdi_driver_changed)
            if self._parameter_provider and hasattr(self._mdi, "parameter_provider"):
                self._mdi.parameter_provider = self._parameter_provider

            if self._pending_parent_window is not None and hasattr(self._mdi, "set_parent_window"):
                self._mdi.set_parent_window(self._pending_parent_window)
                self._pending_parent_window = None

            self._main_widget = self._mdi.get_widget()
            self._is_initialized = True
            return True
        except Exception as exc:  # pragma: no cover - 初始化失敗需記錄
            print(f"❌ [ThrottleLineChartModule] 初始化失敗: {exc}")
            import traceback

            traceback.print_exc()
            self._mdi = None
            self._main_widget = None
            return False

    def get_widget(self):
        if not self._mdi:
            self.initialize_module()
        return self._main_widget

    def update_parameters(self, year: int, race: str, session: str) -> bool:
        self.current_year = str(year)
        self.current_race = race
        self.current_session = session
        if self._mdi:
            return self._mdi.update_analysis_parameters(self.current_year, self.current_race, self.current_session, self.current_driver)
        return True

    def load_data(self, **kwargs) -> bool:
        if not self._mdi:
            self.initialize_module()
        if not self._mdi:
            return False
        params = {
            "year": kwargs.get("year", self.current_year),
            "race": kwargs.get("race", self.current_race),
            "session": kwargs.get("session", self.current_session),
            "driver": kwargs.get("driver", kwargs.get("driver_code", self.current_driver)),
        }
        driver_code = str(params["driver"]).upper()
        params["driver"] = driver_code
        self.current_driver = driver_code
        return self._mdi.load_data(**params)

    def refresh_analysis(self) -> None:
        if self._mdi:
            self._mdi.refresh_analysis()

    def clear_data(self) -> None:
        if self._mdi:
            self._mdi.clear_data()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        if self._mdi:
            return self._mdi.export_data(export_path, export_format)
        return False

    def get_current_data(self) -> Optional[Dict[str, Any]]:
        if self._mdi:
            return self._mdi.get_current_data()
        return None

    def get_default_size(self) -> Tuple[int, int]:
        if self._mdi:
            return self._mdi.get_default_size()
        return (1400, 820)

    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        if self._mdi:
            return self._mdi.get_window_title(year, race, session)
        translated = tr("throttle_line_chart.title", "Throttle Line Chart (Single Driver)")
        return translated

    @property
    def parameter_provider(self):
        return self._parameter_provider

    @parameter_provider.setter
    def parameter_provider(self, provider) -> None:
        self._parameter_provider = provider
        if self._mdi and hasattr(self._mdi, "parameter_provider"):
            self._mdi.parameter_provider = provider

    def set_parent_window(self, parent_window) -> None:
        if self._mdi and hasattr(self._mdi, "set_parent_window"):
            self._mdi.set_parent_window(parent_window)
        else:
            self._pending_parent_window = parent_window

    def _on_mdi_driver_changed(self, driver_code: str) -> None:
        driver = str(driver_code or "").strip().upper()
        if not driver:
            return
        self.current_driver = driver
        if self._mdi:
            self._mdi.update_window_title()

    def cleanup(self) -> None:
        if self._mdi:
            try:
                self._mdi.cleanup()
            except Exception as exc:  # pragma: no cover
                print(f"⚠️ [ThrottleLineChartModule] cleanup 失敗: {exc}")
            self._mdi = None
        if self._main_widget:
            self._main_widget.deleteLater()
            self._main_widget = None
        self._is_initialized = False


def create_throttle_line_chart_module(parent=None, **kwargs) -> ThrottleLineChartModule:
    return ThrottleLineChartModule(parent=parent, **kwargs)


if not ModuleFactory.module_exists(ModuleTypes.THROTTLE_LINE_CHART):
    ModuleFactory.register_module(ModuleTypes.THROTTLE_LINE_CHART, ThrottleLineChartModule)


__all__ = ["ThrottleLineChartModule", "create_throttle_line_chart_module"]
