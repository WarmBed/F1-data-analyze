# -*- coding: utf-8 -*-
"""
ThrottleOptionsPrompter - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class ThrottleOptionsPrompter:
    """從 f1t_gui_main.py 提取的 _prompt_throttle_analysis_options 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _prompt_throttle_analysis_options(self):
        """顯示油門分析選項並回傳使用者選擇。"""
        try:
            from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_options_dialog import (
                ThrottleAnalysisOptionsDialog,
            )
        except ImportError as exc:
            logger.debug(f"[THROTTLE] 無法載入油門分析選項對話框: {exc}")
            return {"box_plot": True, "line_chart": False}

        dialog = ThrottleAnalysisOptionsDialog(self)
        result = dialog.exec_()

        if result != QDialog.Accepted:
            return None

        selected_types = dialog.get_selected_types()
        selection = {
            "box_plot": ThrottleAnalysisOptionsDialog.TYPE_BOX_PLOT in selected_types,
            "line_chart": ThrottleAnalysisOptionsDialog.TYPE_LINE_CHART in selected_types,
        }

        if not selection["box_plot"] and not selection["line_chart"]:
            selection["box_plot"] = True

        logger.debug(f"[THROTTLE] 選項結果: {selection}")
        return selection
