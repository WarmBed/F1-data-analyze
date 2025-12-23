# -*- coding: utf-8 -*-
"""
ResizeEventHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class ResizeEventHandler:
    """從 f1t_gui_main.py 提取的 resizeEvent 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def resizeEvent(self, event):
        """主視窗調整大小時，同步調整固定視窗"""
        super().resizeEvent(event)
        
        # 尋找 Welcome Tab 中的 MDI 區域
        if hasattr(self, 'tab_widget'):
            for i in range(self.main_window.tab_widget.count()):
                tab_widget = self.main_window.tab_widget.widget(i)
                if tab_widget:
                    # 遞迴搜尋 CustomMdiArea
                    mdi_area = self.main_window._find_mdi_area(tab_widget)
                    if mdi_area and hasattr(mdi_area, '_rearrange_fixed_windows'):
                        logger.debug(f"[MAIN_RESIZE] 主視窗調整大小，觸發 MDI 重新排列")
                        mdi_area._rearrange_fixed_windows()
