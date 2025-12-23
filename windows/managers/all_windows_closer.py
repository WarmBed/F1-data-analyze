# -*- coding: utf-8 -*-
"""
AllWindowsCloser - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class AllWindowsCloser:
    """從 f1t_gui_main.py 提取的 close_all_windows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def close_all_windows(self):
        """關閉所有視窗並清理相關註冊"""
        #print("[檢視] 關閉所有視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.main_window.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 使用改進的關閉方法
        self.main_window.close_all_mdi_windows(mdi_area)
