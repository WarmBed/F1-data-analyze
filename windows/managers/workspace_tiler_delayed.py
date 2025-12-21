# -*- coding: utf-8 -*-
"""
WorkspaceTilerDelayed - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger
from PyQt5.QtWidgets import QApplication

logger = get_logger(__name__)


class WorkspaceTilerDelayed:
    """從 f1t_gui_main.py 提取的 _tile_all_workspace_windows_delayed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _tile_all_workspace_windows_delayed(self):
        """延遲執行的自動平鋪 - 確保 MDI 區域尺寸已更新"""
        logger.debug(f"[WORKSPACE] 🔲 開始延遲自動平鋪...")
        
        # 強制處理所有待處理事件，確保 MDI 區域尺寸已更新
        QApplication.processEvents()
        
        # 保存當前活動分頁
        current_tab_index = self.main_window.tab_widget.currentIndex()
        logger.debug(f"[WORKSPACE] 💾 當前活動分頁: index={current_tab_index}")
        
        # 遍歷所有分頁（跳過 HOME）
        tiled_tabs = 0
        for tab_index in range(1, self.main_window.tab_widget.count()):
            tab_name = self.main_window.tab_widget.tabText(tab_index)
            
            logger.debug(f"[WORKSPACE] 🔍 處理分頁 {tab_index}: '{tab_name}'")
            
            # 切換到該分頁
            self.main_window.tab_widget.setCurrentIndex(tab_index)
            
            # 強制處理事件，確保分頁完全激活
            QApplication.processEvents()
            
            # 使用智能 tile_windows() 方法來平鋪當前分頁
            self.main_window.tile_windows()
            
            tiled_tabs += 1
        
        # 恢復原本的活動分頁
        logger.debug(f"[WORKSPACE] 🔄 恢復活動分頁: index={current_tab_index}")
        self.main_window.tab_widget.setCurrentIndex(current_tab_index)
        
        logger.debug(f"[WORKSPACE] ✅ 延遲自動平鋪完成: 共處理 {tiled_tabs} 個分頁")
