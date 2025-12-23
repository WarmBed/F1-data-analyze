# -*- coding: utf-8 -*-
"""
DefaultTabsInitializer - 從 f1t_gui_main.py 提取
"""

from core.gui_i18n import tr

from core.logger import get_logger

logger = get_logger(__name__)


class DefaultTabsInitializer:
    """從 f1t_gui_main.py 提取的 init_default_tabs 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def init_default_tabs(self):
        """初始化預設分頁 - 顯示歡迎畫面"""
        # 創建歡迎畫面作為預設主頁 (隱藏標題)
        welcome_tab = self.main_window.create_welcome_tab()
        welcome_tab.setObjectName("welcome_tab")  # 添加標識符
        self.main_window.tab_widget.addTab(welcome_tab, tr("home_page", "主頁"))  # 顯示 "主頁" 標題
        
        # 🆕 右鍵選單已由 TabManager 設置，不再需要手動調用
        # self.main_window._setup_tab_context_menu()  # 已移至 TabManager
        
        self.main_window.tab_manager.update_tab_count()
