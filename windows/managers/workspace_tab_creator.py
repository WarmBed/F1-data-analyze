# -*- coding: utf-8 -*-
"""
WorkspaceTabCreator - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class WorkspaceTabCreator:
    """從 f1t_gui_main.py 提取的 create_tab_for_workspace 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_tab_for_workspace(self, tab_name: str) -> 'CustomMdiArea':
        """
        專門用於 Workspace 載入的分頁創建方法
        ✅ 使用與 add_new_tab() 完全相同的邏輯，確保類別物件一致
        
        Returns:
            CustomMdiArea: 新創建的 MDI 區域（保證是本地類別實例）
        """
        # 計算分頁編號（排除歡迎頁）
        tab_count = self.main_window.tab_widget.count()
        
        # 創建空白 MDI 工作區（✅ 使用本地 CustomMdiArea 類別）
        new_mdi_area = CustomMdiArea()
        new_mdi_area.setObjectName(f"MdiArea_{tab_count}")
        
        # 添加到標籤列
        index = self.main_window.tab_widget.addTab(new_mdi_area, tab_name)
        
        # 追蹤 MDI 區域
        self.main_window.mdi_areas.append(new_mdi_area)
        
        logger.debug(f"[WORKSPACE] ✅ 已創建分頁（用於 workspace）: '{tab_name}' (index={index})")
        return new_mdi_area
