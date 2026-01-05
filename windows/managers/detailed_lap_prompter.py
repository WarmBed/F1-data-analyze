# -*- coding: utf-8 -*-
"""
DetailedLapPrompter - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class DetailedLapPrompter:
    """從 f1t_gui_main.py 提取的 _prompt_detailed_lap_options 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _prompt_detailed_lap_options(self):
        """顯示詳細圈速分析選項並回傳使用者選擇。"""
        try:
            from modules.gui.driver_race.detailed_lap_analysis.detailed_lap_options_dialog import (
                DetailedLapAnalysisOptionsDialog,
            )
            from PyQt5.QtWidgets import QDialog
        except ImportError as exc:
            logger.debug(f"[DETAILED_LAP] 無法載入選項對話框: {exc}")
            return {"detail_table": True, "box_plot": False}

        dialog = DetailedLapAnalysisOptionsDialog(self.main_window)
        result = dialog.exec_()

        if result != QDialog.Accepted:
            return None

        selected_types = dialog.get_selected_types()
        selection = {
            "detail_table": DetailedLapAnalysisOptionsDialog.TYPE_DETAIL_TABLE in selected_types,
            "box_plot": DetailedLapAnalysisOptionsDialog.TYPE_BOX_PLOT in selected_types,
        }

        if not selection["detail_table"] and not selection["box_plot"]:
            selection["detail_table"] = True

        logger.debug(f"[DETAILED_LAP] 選項結果: {selection}")
        return selection
