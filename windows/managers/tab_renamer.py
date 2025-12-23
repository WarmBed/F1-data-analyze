# -*- coding: utf-8 -*-
"""
TabRenamer - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QInputDialog
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger
from PyQt5.QtWidgets import QLineEdit

logger = get_logger(__name__)


class TabRenamer:
    """從 f1t_gui_main.py 提取的 rename_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def rename_tab(self, tab_index):
        """重新命名分頁"""
        try:
            # 禁止重命名主頁
            if tab_index == 0:
                logger.debug(f"[TAB_RENAME] {tr('home_tab_no_rename')}")
                return
            
            # 獲取當前分頁名稱（移除可能的 🔗 圖標）
            current_name = self.main_window.tab_widget.tabText(tab_index).replace("🔗 ", "")
            
            # 彈出輸入對話框
            new_name, ok = QInputDialog.getText(
                self,
                tr('tab_rename_dialog_title'),
                tr('tab_rename_dialog_label'),
                QLineEdit.Normal,
                current_name
            )
            
            # 用戶取消或未輸入
            if not ok or not new_name:
                logger.debug(f"[TAB_RENAME] User cancelled rename operation")
                return
            
            # 去除首尾空白
            new_name = new_name.strip()
            
            # 檢查名稱是否與當前相同
            if new_name == current_name:
                logger.debug(f"[TAB_RENAME] Tab name unchanged: {current_name}")
                return
            
            # 處理重複名稱：自動添加 (1), (2), (3) 後綴
            final_name = self.main_window._get_unique_tab_name(new_name)
            
            # 更新分頁名稱
            is_popped_out = (tab_index in self.main_window.popped_out_tabs)
            
            if is_popped_out:
                # 如果已彈出，保留 🔗 圖標
                self.main_window.tab_widget.setTabText(tab_index, f"🔗 {final_name}")
                
                # 同步更新獨立視窗標題
                popout_info = self.main_window.popped_out_tabs[tab_index]
                standalone_window = popout_info['standalone_window']
                standalone_window.setWindowTitle(f"{final_name} - {APP_FULL_TITLE}")
                
                # 更新追蹤字典中的名稱
                popout_info['tab_name'] = final_name
                
                logger.debug(f"[TAB_RENAME] {tr('tab_rename_success').format(index=tab_index, name=final_name)} (已彈出)")
            else:
                # 一般分頁，直接更新名稱
                self.main_window.tab_widget.setTabText(tab_index, final_name)
                logger.debug(f"[TAB_RENAME] {tr('tab_rename_success').format(index=tab_index, name=final_name)}")
            
        except Exception as e:
            logger.debug(f"[TAB_RENAME] ❌ 重新命名失敗: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
