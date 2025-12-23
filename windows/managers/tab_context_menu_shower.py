# -*- coding: utf-8 -*-
"""
TabContextMenuShower - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMenu
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class TabContextMenuShower:
    """從 f1t_gui_main.py 提取的 _show_tab_context_menu 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _show_tab_context_menu(self, pos):
        """顯示分頁右鍵選單"""
        # 獲取右鍵點擊的分頁索引
        tab_bar = self.main_window.tab_widget.tabBar()
        tab_index = tab_bar.tabAt(pos)
        
        if tab_index == -1:
            return  # 沒有點擊到分頁
        
        # 檢查是否為 HOME 主頁（index=0）或已彈出的分頁
        is_home_tab = (tab_index == 0)
        is_popped_out = (tab_index in self.main_window.popped_out_tabs)
        
        # HOME 主頁不顯示任何選單
        if is_home_tab:
            logger.debug(f"[TAB_MENU] {tr('home_tab_no_popout')} / {tr('home_tab_no_rename')}")
            return
        
        # 創建右鍵選單
        menu = QMenu(self)
        
        if is_popped_out:
            # 已彈出：顯示「返回主視窗」+ 「重新命名」選項
            return_action = menu.addAction(tr('tab_return_menu'))
            return_action.triggered.connect(lambda: self.main_window.pop_back_in_tab(tab_index))
            
            menu.addSeparator()  # 分隔線
            
            rename_action = menu.addAction(tr('tab_rename_menu'))
            rename_action.triggered.connect(lambda: self.main_window.rename_tab(tab_index))
        else:
            # 未彈出：顯示「彈出為獨立視窗」+ 「重新命名」選項
            popout_action = menu.addAction(tr('tab_popout_menu'))
            popout_action.triggered.connect(lambda: self.main_window.pop_out_tab(tab_index))
            
            menu.addSeparator()  # 分隔線
            
            rename_action = menu.addAction(tr('tab_rename_menu'))
            rename_action.triggered.connect(lambda: self.main_window.rename_tab(tab_index))
        
        # 顯示選單
        global_pos = tab_bar.mapToGlobal(pos)
        menu.exec_(global_pos)
        logger.debug(f"[TAB_MENU] Show tab {tab_index} context menu (popped_out={is_popped_out})")
