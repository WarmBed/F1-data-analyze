# -*- coding: utf-8 -*-
"""
TabChangeHandler - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import QTimer
from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class TabChangeHandler:
    """從 f1t_gui_main.py 提取的 _on_tab_changed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _on_tab_changed(self, index):
        """分頁切換事件處理"""
        try:
            # 當切換分頁時，檢查並更新工具欄狀態
            self.main_window._check_and_update_toolbar_status()
            
            # 🔧 新增: 當切換到 Home 頁面時，重新排列視窗
            if index == 0:  # Home 頁面是第一個分頁
                tab_widget = self.main_window.tab_widget.widget(index)
                if tab_widget:
                    # 尋找 MDI 區域
                    from PyQt5.QtCore import QTimer
                    def find_and_arrange():
                        mdi_areas = tab_widget.findChildren(CustomMdiArea)
                        if mdi_areas:
                            mdi_area = mdi_areas[0]
                            if hasattr(mdi_area, 'arrange_welcome_windows'):
                                logger.debug(f"[TAB_CHANGED] 🔧 切換到 Home 頁面，重新排列視窗")
                                mdi_area.arrange_welcome_windows()
                    # 延遲 200ms 以確保佈局完成
                    QTimer.singleShot(200, find_and_arrange)
        except Exception as e:
            logger.error(f"[ERROR] 分頁切換處理失敗: {e}")
