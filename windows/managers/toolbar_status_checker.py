# -*- coding: utf-8 -*-
"""
ToolbarStatusChecker - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class ToolbarStatusChecker:
    """從 f1t_gui_main.py 提取的 _check_and_update_toolbar_status 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _check_and_update_toolbar_status(self):
        """檢查當前活動的分析模組並更新工具欄狀態"""
        try:
            # 查找當前分頁中的MDI區域
            current_tab = self.main_window.tab_widget.currentWidget()
            if not current_tab:
                self.main_window.clear_toolbar_status()
                return
            
            # 查找MDI區域
            mdi_area = None
            if isinstance(current_tab, CustomMdiArea):
                mdi_area = current_tab
            else:
                for child in current_tab.findChildren(CustomMdiArea):
                    mdi_area = child
                    break
            
            if not mdi_area:
                self.main_window.clear_toolbar_status()
                return
            
            # 檢查MDI區域中是否有子視窗
            subwindows = mdi_area.subWindowList()
            if not subwindows:
                # 沒有子視窗，清除工具欄狀態
                self.main_window.clear_toolbar_status()
                logger.debug(f"[TOOLBAR_STATUS] 沒有活動的分析模組，已清除工具欄狀態")
            else:
                logger.debug(f"[TOOLBAR_STATUS] 當前有 {len(subwindows)} 個活動的分析模組")
                
        except Exception as e:
            logger.error(f"[ERROR] 檢查工具欄狀態失敗: {e}")
            self.main_window.clear_toolbar_status()
