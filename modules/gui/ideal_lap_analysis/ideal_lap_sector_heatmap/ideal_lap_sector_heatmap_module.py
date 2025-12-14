#!/usr/bin/env python3
"""
Ideal Lap Sector Heatmap Module
--------------------------------

Facade implementing IAnalysisModule for the sector heatmap view.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PyQt5.QtWidgets import QWidget

from modules.gui.interfaces.analysis_module import IAnalysisModule

from .ideal_lap_sector_heatmap_mdi import IdealLapSectorHeatmapMDI

from core.logger import get_logger
logger = get_logger(__name__)


class IdealLapSectorHeatmapModule(IAnalysisModule):
    """
    IAnalysisModule wrapper around the IdealLapSectorHeatmapMDI implementation.
    """

    def __init__(self, parent=None, year: Optional[int] = None,
                 race: Optional[str] = None, session: Optional[str] = None):
        super().__init__(parent)

        # ✅ 添加 analysis_type 屬性以支援批次更新
        self.analysis_type = 'ideal_lap'

        self._module_name = "IdealLapSectorHeatmap"
        self._display_name = "Ideal Lap Sector Heatmap"
        self._description = (
            "Visualise S1/S2/S3 sector performance for all drivers using a heatmap."
        )
        self._version = "1.0.0"

        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session

        self._heatmap_core: Optional[IdealLapSectorHeatmapMDI] = None
        self._main_widget: Optional[QWidget] = None

    # ------------------------------------------------------------------ #
    # IAnalysisModule properties
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # IAnalysisModule implementation
    # ------------------------------------------------------------------ #
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        if self._is_initialized:
            return True

        if not self.current_year or not self.current_race or not self.current_session:
            self.emit_error("Missing required parameters (year/race/session)")
            return False

        try:
            if not self._heatmap_core:
                self._heatmap_core = IdealLapSectorHeatmapMDI(parent=parent_widget)
                self._heatmap_core.current_year = self.current_year
                self._heatmap_core.current_race = self.current_race
                self._heatmap_core.current_session = self.current_session

                if not self._heatmap_core.initialize_module():
                    self.emit_error("Failed to initialise heatmap MDI")
                    self._heatmap_core = None
                    return False

            self._main_widget = self._heatmap_core.get_widget()
            self._is_initialized = True
            return True

        except Exception as exc:  # pragma: no cover - defensive
            self.emit_error(f"Initialisation failed: {exc}")
            return False

    def get_widget(self) -> Optional[QWidget]:
        return self._main_widget

    def load_data(self, **kwargs) -> bool:
        if not self._heatmap_core:
            return False
        return self._heatmap_core.load_data(**kwargs)

    def update_parameters(self, year: int, race: str, session: str) -> bool:
        self.current_year = str(year)
        self.current_race = race
        self.current_session = session

        if self._heatmap_core:
            return self._heatmap_core.update_parameters(year, race, session)
        return True

    def refresh_data(self, **kwargs) -> bool:
        if not self._heatmap_core:
            return False
        self._heatmap_core.refresh_analysis()
        return True

    def refresh_analysis(self) -> bool:
        return self.refresh_data()

    def clear_data(self) -> bool:
        try:
            if self._heatmap_core and hasattr(self._heatmap_core, "chart_widget"):
                widget = self._heatmap_core.chart_widget
                if hasattr(widget, "clear_data"):
                    widget.clear_data()
                elif hasattr(widget, "clear"):
                    widget.clear()
                return True
            return False
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug(f"[SECTOR_HEATMAP_MODULE] 清空資料失敗: {exc}")
            return False

    def cleanup(self):
        if self._heatmap_core:
            self._heatmap_core.cleanup()
            self._heatmap_core = None
        self._main_widget = None
        self._is_initialized = False

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        if not self._heatmap_core:
            return False
        return self._heatmap_core.export_data(export_path, export_format)

    def export_chart(self, file_path: str) -> bool:
        if not self._heatmap_core:
            return False
        if hasattr(self._heatmap_core, "export_chart"):
            return self._heatmap_core.export_chart(file_path)
        chart_widget = getattr(self._heatmap_core, "chart_widget", None)
        if chart_widget is None:
            return False
        if hasattr(chart_widget, "save_plot"):
            return chart_widget.save_plot(file_path)
        if hasattr(chart_widget, "export_chart"):
            return chart_widget.export_chart(file_path)
        logger.debug("[SECTOR_HEATMAP_MODULE] 無可用匯出方法")
        return False

    def get_current_data(self) -> Optional[Dict[str, Any]]:
        if not self._heatmap_core:
            return None
        return self._heatmap_core.get_current_data()

    def get_title(self) -> str:
        if self.current_year and self.current_race and self.current_session:
            return f"Ideal Lap Sector Heatmap - {self.current_year} {self.current_race} {self.current_session}"
        return self.display_name

    def get_default_size(self) -> Any:
        if self._heatmap_core and hasattr(self._heatmap_core, "get_default_size"):
            return self._heatmap_core.get_default_size()
        return (1280, 860)
