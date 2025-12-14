#!/usr/bin/env python3
"""
LapTimeBoxPlotAnalysisModule - F1T 圈速分布箱型圖分析模組
=============================================================

提供與主系統一致的通用介面，整合圈速箱型圖 MDI 視窗。
依循 UniversalAnalysisMDI + UniversalDataLoader 架構，支援：
- API-ONLY 模式資料載入 (Function 51)
- 圈速模式顯示 (lap_time_distribution)
- 多國語言顯示
- MDI 視窗同步設定

作者: F1T Team
日期: 2025-10-08 (圈速模式更新)
版本: 1.1.0
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger
logger = get_logger(__name__)

try:
    from ...interfaces.analysis_module import IAnalysisModule, ModuleFactory, ModuleTypes
except ImportError:  # pragma: no cover
    from modules.gui.interfaces.analysis_module import (
        IAnalysisModule,
        ModuleFactory,
        ModuleTypes,
    )

try:
    from .lap_box_plot_analysis_mdi import LapTimeBoxPlotAnalysis
except ImportError:  # pragma: no cover
    from modules.gui.Throttle_analysis.laptime_box_plot_analysis.lap_box_plot_analysis_mdi import (
        LapTimeBoxPlotAnalysis,
    )


class LapTimeBoxPlotAnalysisModule(IAnalysisModule):
    """圈速箱型圖分析模組主類別"""

    def __init__(self, parent=None, year=None, race=None, session=None):
        super().__init__(parent)

        self._module_name = "laptime_box_plot_analysis"
        self._display_name = "🚀 Throttle Box Plot Analysis"
        self._version = "1.0.0"
        self._description = (
            "F1 All-Drivers lap time distribution box plot analysis module"
        )

        self.analysis_type = "laptime_boxplot"
        self._is_initialized = False
        self._parameter_provider = None
        self.current_year = str(year) if year else "2025"
        self.current_race = race if race else "Japan"
        self.current_session = session if session else "R"

        self._laptime_boxplot_core: Optional[LapTimeBoxPlotAnalysis] = None
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

            if not self._laptime_boxplot_core:
                self._laptime_boxplot_core = LapTimeBoxPlotAnalysis(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    parent=parent_widget,
                )

            if self._parameter_provider and hasattr(self._laptime_boxplot_core, "parameter_provider"):
                self._laptime_boxplot_core.parameter_provider = self._parameter_provider

            if not self._main_widget:
                if hasattr(self._laptime_boxplot_core, "get_widget"):
                    self._main_widget = self._laptime_boxplot_core.get_widget()
                else:
                    self._main_widget = None

            self._is_initialized = True
            return True
        except Exception as exc:
            logger.error(f"[LAPTIME_MODULE] 初始化失敗: {exc}")
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

            if self._laptime_boxplot_core:
                return self._laptime_boxplot_core.update_analysis_parameters(
                    str(year), race, session
                )
            return False
        except Exception as exc:
            logger.error(f"[LAPTIME_MODULE] update_parameters 失敗: {exc}")
            return False

    def load_data(self, **kwargs) -> bool:
        try:
            if self._laptime_boxplot_core:
                return self._laptime_boxplot_core.load_data(**kwargs)
            return False
        except Exception as exc:
            logger.error(f"[LAPTIME_MODULE] 載入數據失敗: {exc}")
            return False

    def refresh_analysis(self) -> None:
        try:
            if self._laptime_boxplot_core:
                self._laptime_boxplot_core.refresh_analysis()
        except Exception as exc:
            logger.error(f"[LAPTIME_MODULE] refresh_analysis 失敗: {exc}")

    def clear_data(self) -> None:
        try:
            if self._laptime_boxplot_core:
                self._laptime_boxplot_core.clear_data()
        except Exception as exc:
            logger.error(f"[LAPTIME_MODULE] clear_data 失敗: {exc}")
    
    def reset_chart_view(self) -> None:
        """
        重置圖表視圖（主 GUI "Show All Data" 按鈕調用）
        
        這個方法橋接主 GUI 與內部 MDI 實例的 reset_chart_view()
        """
        try:
            logger.debug("[LAPTIME_MODULE] 🔄 收到 reset_chart_view 請求")
            
            if not self._laptime_boxplot_core:
                logger.warning("[LAPTIME_MODULE] ⚠️  MDI 核心實例不存在")
                return
            
            if not hasattr(self._laptime_boxplot_core, 'reset_chart_view'):
                logger.warning("[LAPTIME_MODULE] ⚠️  MDI 核心沒有 reset_chart_view 方法")
                return
            
            # 轉發到內部 MDI 實例
            logger.info("[LAPTIME_MODULE] ✅ 轉發 reset_chart_view 至 MDI 核心")
            self._laptime_boxplot_core.reset_chart_view()
            
        except Exception as exc:
            logger.error(f"[LAPTIME_MODULE] reset_chart_view 失敗: {exc}")
            import traceback
            traceback.print_exc()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        try:
            if self._laptime_boxplot_core:
                return self._laptime_boxplot_core.export_data(export_path, export_format)
            return False
        except Exception as exc:
            logger.error(f"[LAPTIME_MODULE] export_data 失敗: {exc}")
            return False

    def get_current_data(self) -> Optional[Dict[str, Any]]:
        try:
            if self._laptime_boxplot_core and hasattr(
                self._laptime_boxplot_core, "data_manager"
            ):
                return self._laptime_boxplot_core.data_manager.get_processed_data()
            return None
        except Exception as exc:
            logger.error(f"[LAPTIME_MODULE] get_current_data 失敗: {exc}")
            return None

    def get_default_size(self) -> tuple:
        """返回預設視窗大小 (寬, 高)"""
        return (1200, 700)

    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """生成視窗標題 - 只顯示模組名稱（支援多國語言）"""
        from core.gui_i18n import tr

        translated_name = tr("lap_time_box_plot", "Lap Time Box Plot")
        return translated_name

    @property
    def parameter_provider(self):
        return self._parameter_provider

    @parameter_provider.setter
    def parameter_provider(self, provider):
        self._parameter_provider = provider
        if self._laptime_boxplot_core and hasattr(self._laptime_boxplot_core, "parameter_provider"):
            self._laptime_boxplot_core.parameter_provider = provider

    def cleanup(self):
        try:
            if self._laptime_boxplot_core:
                self._laptime_boxplot_core.clear_data()
            if self._main_widget:
                self._main_widget.deleteLater()
                self._main_widget = None
            self._laptime_boxplot_core = None
            self._is_initialized = False
            self._parameter_provider = None
        except Exception as exc:
            logger.error(f"[LAPTIME_MODULE] cleanup 失敗: {exc}")


def create_laptime_boxplot_module(parent=None, **kwargs) -> LapTimeBoxPlotAnalysisModule:
    return LapTimeBoxPlotAnalysisModule(parent=parent, **kwargs)


# Module registration (if needed in the future)
# if not ModuleFactory.module_exists(ModuleTypes.LAPTIME_BOX_PLOT):
#     ModuleFactory.register_module(ModuleTypes.LAPTIME_BOX_PLOT, LapTimeBoxPlotAnalysisModule)
