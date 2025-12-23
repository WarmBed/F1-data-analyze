# -*- coding: utf-8 -*-
"""
SubwindowCloser - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class SubwindowCloser:
    """從 f1t_gui_main.py 提取的 close_all_subwindows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def close_all_subwindows(self):
        """關閉所有子視窗"""
        try:
            # 關閉所有MDI子視窗
            for mdi_area in self.main_window.mdi_areas:
                subwindows = mdi_area.subWindowList()
                
                for sub_window in subwindows:
                    try:
                        sub_window.close()
                    except Exception as e:
                        logger.debug(f"[MAIN] ⚠️ 關閉子視窗時發生錯誤: {e}")
                        
                # 清除MDI區域
                mdi_area.closeAllSubWindows()
            
            # 清理追蹤列表
            if hasattr(self, 'active_subwindows'):
                self.main_window.active_subwindows.clear()
                
        except Exception as e:
            logger.debug(f"[MAIN] ⚠️ 關閉子視窗過程中發生錯誤: {e}")
