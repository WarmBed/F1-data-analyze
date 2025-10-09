#!/usr/bin/env python3
"""
ThrottleBoxPlotAnalysisModule - F1T 全油門百分比箱型圖分析模組
=============================================================

提供與主系統一致的通用介面，整合油門箱型圖 MDI 視窗。
依循 UniversalAnalysisMDI + UniversalDataLoader 架構，支援：
- API-ONLY 模式資料載入 (Function 54)
- 百分比模式顯示 (full_throttle_ratio)
- 多國語言顯示
- MDI 視窗同步設定

作者: F1T Team
日期: 2025-10-08 (百分比模式更新)
版本: 1.1.0
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget

try:
    from ...interfaces.analysis_module import IAnalysisModule, ModuleFactory, ModuleTypes
except ImportError:  # pragma: no cover
    from modules.gui.interfaces.analysis_module import (
        IAnalysisModule,
        ModuleFactory,
        ModuleTypes,
    )

try:
    from .throttle_box_plot_analysis_mdi import ThrottleBoxPlotAnalysis
except ImportError:  # pragma: no cover
    from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
        ThrottleBoxPlotAnalysis,
    )


class ThrottleBoxPlotAnalysisModule(IAnalysisModule):
    """油門箱型圖分析模組主類別"""

    def __init__(self, parent=None, year=None, race=None, session=None):
        super().__init__(parent)

        self._module_name = "throttle_box_plot_analysis"
        self._display_name = "🚀 Throttle Box Plot Analysis"
        self._version = "1.0.0"
        self._description = (
            "F1 All-Drivers full-throttle duration box plot analysis module"
        )

        self._is_initialized = False
        self._parameter_provider = None
        self.current_year = str(year) if year else "2025"
        self.current_race = race if race else "Japan"
        self.current_session = session if session else "R"

        self._throttle_boxplot_core: Optional[ThrottleBoxPlotAnalysis] = None
        self._main_widget: Optional[QWidget] = None

    # ------------------------------------------------------------------
    # IAnalysisModule interface
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

    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        try:
            if self._is_initialized:
                return True

            if not self._throttle_boxplot_core:
                self._throttle_boxplot_core = ThrottleBoxPlotAnalysis(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    parent=parent_widget,
                )

            if self._parameter_provider and hasattr(self._throttle_boxplot_core, "parameter_provider"):
                self._throttle_boxplot_core.parameter_provider = self._parameter_provider

            if not self._main_widget:
                if hasattr(self._throttle_boxplot_core, "get_widget"):
                    self._main_widget = self._throttle_boxplot_core.get_widget()
                else:
                    self._main_widget = None

            self._is_initialized = True
            return True
        except Exception as exc:
            print(f"❌ [THROTTLE_MODULE] 初始化失敗: {exc}")
            return False

    def get_widget(self):
        if not self._main_widget:
            self.initialize_module()
        return self._main_widget

    def update_parameters(self, year: int, race: str, session: str) -> bool:
        try:
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session

            if self._throttle_boxplot_core:
                return self._throttle_boxplot_core.update_analysis_parameters(
                    str(year), race, session
                )
            return False
        except Exception as exc:
            print(f"❌ [THROTTLE_MODULE] update_parameters 失敗: {exc}")
            return False

    def load_data(self, **kwargs) -> bool:
        try:
            if self._throttle_boxplot_core:
                return self._throttle_boxplot_core.load_data(**kwargs)
            return False
        except Exception as exc:
            print(f"❌ [THROTTLE_MODULE] 載入數據失敗: {exc}")
            return False

    def refresh_analysis(self) -> None:
        try:
            if self._throttle_boxplot_core:
                self._throttle_boxplot_core.refresh_analysis()
        except Exception as exc:
            print(f"❌ [THROTTLE_MODULE] refresh_analysis 失敗: {exc}")

    def clear_data(self) -> None:
        try:
            if self._throttle_boxplot_core:
                self._throttle_boxplot_core.clear_data()
        except Exception as exc:
            print(f"❌ [THROTTLE_MODULE] clear_data 失敗: {exc}")

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        try:
            if self._throttle_boxplot_core:
                return self._throttle_boxplot_core.export_data(export_path, export_format)
            return False
        except Exception as exc:
            print(f"❌ [THROTTLE_MODULE] export_data 失敗: {exc}")
            return False

    def get_current_data(self) -> Optional[Dict[str, Any]]:
        try:
            if self._throttle_boxplot_core and hasattr(
                self._throttle_boxplot_core, "data_manager"
            ):
                return self._throttle_boxplot_core.data_manager.get_processed_data()
            return None
        except Exception as exc:
            print(f"❌ [THROTTLE_MODULE] get_current_data 失敗: {exc}")
            return None

    def get_default_size(self) -> tuple:
        """返回預設視窗大小 (寬, 高)"""
        return (1200, 700)

    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """生成視窗標題"""
        year = year or self.current_year
        race = race or self.current_race
        session = session or self.current_session
        from core.gui_i18n import tr
        translated_name = tr("throttle_box_plot", "油門箱型圖")
        return f"{translated_name} - {year} {race} {session}"

    @property
    def parameter_provider(self):
        return self._parameter_provider

    @parameter_provider.setter
    def parameter_provider(self, provider):
        self._parameter_provider = provider
        if self._throttle_boxplot_core and hasattr(self._throttle_boxplot_core, "parameter_provider"):
            self._throttle_boxplot_core.parameter_provider = provider

    def cleanup(self):
        try:
            if self._throttle_boxplot_core:
                self._throttle_boxplot_core.clear_data()
            if self._main_widget:
                self._main_widget.deleteLater()
                self._main_widget = None
            self._throttle_boxplot_core = None
            self._is_initialized = False
            self._parameter_provider = None
        except Exception as exc:
            print(f"❌ [THROTTLE_MODULE] cleanup 失敗: {exc}")


def create_throttle_boxplot_module(parent=None, **kwargs) -> ThrottleBoxPlotAnalysisModule:
    return ThrottleBoxPlotAnalysisModule(parent=parent, **kwargs)


if not ModuleFactory.module_exists(ModuleTypes.THROTTLE_BOX_PLOT):
    ModuleFactory.register_module(ModuleTypes.THROTTLE_BOX_PLOT, ThrottleBoxPlotAnalysisModule)
