# -*- coding: utf-8 -*-
"""
WindowMaximizer - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class WindowMaximizer:
    """從 f1t_gui_main.py 提取的 maximize_all_windows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def maximize_all_windows(self):
        """最大化所有視窗"""
        #print("[檢視] 最大化所有視窗")
        
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
            
        # 獲取所有子視窗並最大化（排除固定視窗）
        all_subwindows = mdi_area.subWindowList()
        subwindows = [sw for sw in all_subwindows if not sw.property("is_welcome_fixed")]
        
        if not subwindows:
            #print("[ERROR] MDI區域中沒有非固定子視窗")
            return
            
        count = 0
        for subwindow in subwindows:
            subwindow.showMaximized()
            count += 1
            #print(f"[CHART] 最大化視窗: '{subwindow.windowTitle()}'")
            
        #print(f"[OK] 成功最大化 {count} 個視窗")
