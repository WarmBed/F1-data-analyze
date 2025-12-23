# -*- coding: utf-8 -*-
"""
ToolbarStatusUpdater - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class ToolbarStatusUpdater:
    """從 f1t_gui_main.py 提取的 update_toolbar_status 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def update_toolbar_status(self, module_name: str = "", lap_time: str = "", 
                            tyre_compound: str = "", lap_numbers: str = ""):
        """更新工具欄狀態信息"""
        try:
            if hasattr(self, 'toolbar_status_widget'):
                # 如果沒有模組名稱，隱藏狀態區域
                if not module_name:
                    self.main_window.toolbar_status_widget.setVisible(False)
                    return
                
                # 更新模組名稱標籤
                self.main_window.toolbar_module_label.setText(f"📊 {module_name}")
                
                # 更新圈時間標籤
                if lap_time:
                    self.main_window.toolbar_lap_time_label.setText(f"⏱️ {lap_time}")
                    self.main_window.toolbar_lap_time_label.setVisible(True)
                else:
                    self.main_window.toolbar_lap_time_label.setVisible(False)
                
                # 更新輪胎配方標籤
                if tyre_compound:
                    self.main_window.toolbar_tyre_label.setText(f"🏎️ {tyre_compound}")
                    self.main_window.toolbar_tyre_label.setVisible(True)
                else:
                    self.main_window.toolbar_tyre_label.setVisible(False)
                
                # 更新圈數標籤
                if lap_numbers:
                    self.main_window.toolbar_lap_numbers_label.setText(f"🏁 {lap_numbers}")
                    self.main_window.toolbar_lap_numbers_label.setVisible(True)
                else:
                    self.main_window.toolbar_lap_numbers_label.setVisible(False)
                
                # 顯示狀態區域
                self.main_window.toolbar_status_widget.setVisible(True)
                
                logger.debug(f"[TOOLBAR_STATUS] 已更新: {module_name} | {lap_time} | {tyre_compound} | {lap_numbers}")
                
        except Exception as e:
            logger.error(f"[ERROR] 更新工具欄狀態失敗: {e}")
