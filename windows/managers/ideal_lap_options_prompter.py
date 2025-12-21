# -*- coding: utf-8 -*-
"""
IdealLapOptionsPrompter - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class IdealLapOptionsPrompter:
    """從 f1t_gui_main.py 提取的 _prompt_ideal_lap_options 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _prompt_ideal_lap_options(self):
        """
        顯示理想圈分析選項對話框並回傳使用者選擇
        
        Returns:
            list[str] | None: 選中的分析類型列表，取消則返回 None
        """
        try:
            from modules.gui.lap_analysis.ideal_lap import IdealLapAnalysisOptionsDialog
        except ImportError as exc:
            logger.debug(f"[IDEAL_LAP] ❌ 無法載入選項對話框: {exc}")
            import traceback
            traceback.print_exc()
            return None

        dialog = IdealLapAnalysisOptionsDialog(self)
        result = dialog.exec_()

        if result != QDialog.Accepted:
            logger.debug("[IDEAL_LAP] 使用者取消對話框")
            return None

        selected_types = dialog.get_selected_types()
        
        if not selected_types:
            logger.debug("[IDEAL_LAP] ⚠️ 未選擇任何分析類型")
            return None

        logger.debug(f"[IDEAL_LAP] ✅ 選項結果: {selected_types}")
        return selected_types
