# -*- coding: utf-8 -*-
"""
LapControlsHider - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LapControlsHider:
    """從 f1t_gui_main.py 提取的 hide_lap_controls 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def hide_lap_controls(self):
        """隱藏遙測分析控件（從工具欄移除）"""
        if len(self.main_window.lap_analysis_windows) > 0:
            logger.debug("[LAP_CONTROL] [DEBUG]   ⚠️ 還有圈速分析視窗開啟中，不隱藏控件")
            return
            
        logger.debug("[LAP_CONTROL] [DEBUG]   🔴 開始隱藏圈速分析控件（從工具欄移除）")
        
        # 檢查是否已經從工具欄移除
        if not hasattr(self, '_lap_controls_added') or not self.main_window._lap_controls_added:
            logger.debug("[LAP_CONTROL] [DEBUG]   ⚠️ 圈速分析控件已經不在工具欄中，跳過移除")
            return
        
        try:
            # 移除所有遙測分析控件
            if hasattr(self, 'lap_separator') and self.main_window.lap_separator:
                self.main_window.main_toolbar.removeAction(self.main_window.lap_separator)
                self.main_window.lap_separator = None
            
            # 移除控件
            controls_to_remove = [
                self.main_window.driver1_label, self.main_window.driver1_combo,
                self.main_window.lap1_label, self.main_window.lap1_spinbox,
                self.main_window.driver2_label, self.main_window.driver2_combo,
                self.main_window.lap2_label, self.main_window.lap2_spinbox,
                self.main_window.fastest_lap_checkbox, self.main_window.use_time_axis_checkbox
            ]
            
            for control in controls_to_remove:
                # 查找包含這個widget的action並移除
                for action in self.main_window.main_toolbar.actions():
                    if action.defaultWidget() == control:
                        self.main_window.main_toolbar.removeAction(action)
                        break
            
            # 移除更新按鈕
            if hasattr(self, 'update_all_action') and self.main_window.update_all_action:
                logger.debug("[LAP_CONTROL] [DEBUG]   🗑️ 正在移除 Update All Analysis 按鈕...")
                self.main_window.main_toolbar.removeAction(self.main_window.update_all_action)
                self.main_window.update_all_action = None
                logger.debug("[LAP_CONTROL] [DEBUG]   ✅ Update All Analysis 按鈕已移除")
            else:
                logger.debug("[LAP_CONTROL] [DEBUG]   ⚠️ update_all_action 不存在或已是 None")
            
            # 🔧 修復：移除 Lap Linkage 按鈕
            if hasattr(self, 'lap_linkage_action') and self.main_window.lap_linkage_action:
                logger.debug("[LAP_CONTROL] [DEBUG]   🗑️ 正在移除 Lap Linkage 按鈕...")
                self.main_window.main_toolbar.removeAction(self.main_window.lap_linkage_action)
                self.main_window.lap_linkage_action = None
                logger.debug("[LAP_CONTROL] [DEBUG]   ✅ Lap Linkage 按鈕已移除")
            else:
                logger.debug("[LAP_CONTROL] [DEBUG]   ⚠️ lap_linkage_action 不存在或已是 None")
            
            logger.debug("[LAP_CONTROL] [DEBUG]   ✅ 圈速分析控件成功從工具欄移除")
            self.main_window._lap_controls_added = False
            self.main_window.lap_controls_visible = False
            
        except Exception as e:
            logger.debug(f"[LAP_CONTROL] [DEBUG]   ❌ 移除圈速分析控件時發生錯誤: {e}")


        logger.debug("[LAP_CONTROL] [DEBUG]   🔍 ========== 調試結束 ==========")
