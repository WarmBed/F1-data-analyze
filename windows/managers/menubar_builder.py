# -*- coding: utf-8 -*-
"""
MenubarBuilder - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QAction

from core.gui_i18n import tr
from core.gui_i18n import get_gui_language

class MenubarBuilder:
    """從 f1t_gui_main.py 提取的 create_professional_menubar 處理器"""

    def __init__(self, main_window):
        self.main_window = main_window
    def create_professional_menubar(self):
        """創建專業菜單欄"""
        menubar = self.menuBar()
        
        # 檔案菜單
        file_menu = menubar.addMenu(tr('file_menu'))
        file_menu.addAction(tr('save_workspace', 'Save Workspace'), self.save_workspace)
        file_menu.addAction(tr('load_workspace', 'Load Workspace'), self.load_workspace)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        
        # 檢視菜單 (已隱藏)
        # view_menu = menubar.addMenu(tr('view_menu'))
        # view_menu.addAction(tr('tile_windows', 'Tile Windows'), self.tile_windows)
        # view_menu.addAction(tr('cascade_windows', 'Cascade Windows'), self.cascade_windows)
        # view_menu.addSeparator()
        # view_menu.addAction(tr('minimize_all_windows', 'Minimize All Windows'), self.minimize_all_windows)
        # view_menu.addAction(tr('maximize_all_windows', 'Maximize All Windows'), self.maximize_all_windows)
        # view_menu.addAction(tr('restore_all_windows', 'Restore All Windows'), self.restore_all_windows)
        # view_menu.addSeparator()
        # view_menu.addAction(tr('close_all_windows', 'Close All Windows'), self.close_all_windows)
        # view_menu.addSeparator()
        # view_menu.addAction(tr('full_screen', 'Full Screen'), self.toggle_fullscreen)
        
        # 分析菜單 (已隱藏)
        # analysis_menu = menubar.addMenu(tr('menu_analysis', 'Analysis'))
        # analysis_menu.addAction(tr('menu_driver_standings', 'Driver Standings'), self.open_driver_standings)
        # analysis_menu.addAction(tr('menu_constructor_standings', 'Constructor Standings'), self.open_constructor_standings)
        # analysis_menu.addSeparator()
        # # Vehicle Parts Changes - 暫時禁用開發中
        # parts_action = analysis_menu.addAction(tr('menu_parts_analysis', 'Vehicle Parts Changes'), self.open_parts_analysis)
        # parts_action.setEnabled(False)  # 禁用
        # parts_action.setStatusTip(tr('parts_analysis_disabled', 'This feature is under development'))
        # analysis_menu.addSeparator()
        # analysis_menu.addAction(tr('menu_season_progress', 'Season Progress'), self.open_season_progress)
        
        # Live Timing 菜單 (使用 LiveTimingManager 重構)
        live_timing_menu = menubar.addMenu(tr('menu_live_timing', 'Live Timing'))
        self.live_timing_manager.setup_menu(live_timing_menu)
        
        # 工具菜單
        tools_menu = menubar.addMenu(tr('tools_menu'))
        tools_menu.addAction(tr('system_settings', 'System Settings'), self.system_settings)
        self.check_api_action = QAction(tr('check_api_status', 'Check API Status'), self)
        self.check_api_action.setStatusTip(tr('check_api_status_tip', 'Run an API health check immediately'))
        self.check_api_action.triggered.connect(self.manual_api_health_check)
        tools_menu.addAction(self.check_api_action)

        tools_menu.addSeparator()
        
        # 語言切換功能
        language_menu = tools_menu.addMenu(tr('language_menu', 'Language'))
        
        # 英文選項
        self.english_action = QAction('🇺🇸 English', self)
        self.english_action.setCheckable(True)
        self.english_action.triggered.connect(lambda: self.set_interface_language('en'))
        language_menu.addAction(self.english_action)
        
        # 中文選項
        self.chinese_action = QAction('🇹🇼 中文', self)
        self.chinese_action.setCheckable(True)
        self.chinese_action.triggered.connect(lambda: self.set_interface_language('zh'))
        language_menu.addAction(self.chinese_action)
        
        # 日文選項
        self.japanese_action = QAction('🇯🇵 日本語', self)
        self.japanese_action.setCheckable(True)
        self.japanese_action.triggered.connect(lambda: self.set_interface_language('ja'))
        language_menu.addAction(self.japanese_action)
        
        # 設定當前語言狀態
        current_lang = get_gui_language()
        if current_lang == 'en':
            self.english_action.setChecked(True)
        elif current_lang == 'ja':
            self.japanese_action.setChecked(True)
        else:
            self.chinese_action.setChecked(True)
        
        tools_menu.addSeparator()
        
        # X軸連動功能控制
        self.linkage_action = QAction('🔗 Telemetry X-Axis Linkage', self)
        self.linkage_action.setCheckable(True)
        self.linkage_action.setChecked(True)  # 預設啟用
        self.linkage_action.triggered.connect(self.toggle_lap_analysis_linkage)
        tools_menu.addAction(self.linkage_action)
        
        # F1TV Account 選單
        f1tv_menu = menubar.addMenu(tr('f1tv_account_menu', 'F1TV Account'))
        self.f1tv_login_action = QAction(tr('f1tv_login_action', 'Login / Manage Account'), self)
        self.f1tv_login_action.triggered.connect(self._open_f1tv_auth_dialog)
        f1tv_menu.addAction(self.f1tv_login_action)
        f1tv_menu.addSeparator()
        self.f1tv_logout_action = QAction(tr('f1tv_logout_action', 'Logout'), self)
        self.f1tv_logout_action.triggered.connect(self._logout_f1tv)
        f1tv_menu.addAction(self.f1tv_logout_action)

        # 說明菜單
        help_menu = menubar.addMenu(tr('help_menu', '說明'))
        help_menu.addAction(tr('about_action', '關於 F1T'), self.show_about_dialog)


    # ========== _setup_live_timing_menu 已移除，使用 LiveTimingManager.setup_menu() ==========

