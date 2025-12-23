# -*- coding: utf-8 -*-
"""
ProfessionalWorkspaceBuilder - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from core.gui_i18n import tr

from core.logger import get_logger
from PyQt5.QtWidgets import QSizePolicy

logger = get_logger(__name__)


class ProfessionalWorkspaceBuilder:
    """從 f1t_gui_main.py 提取的 create_professional_workspace 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_professional_workspace(self):
        """創建專業工作區 - 分頁式界面 + 全局工具列（整合到 TabBar）"""
        # 創建主容器
        main_container = QWidget()
        main_container.setObjectName("MainTabContainer")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 創建分頁容器
        self.main_window.tab_widget = QTabWidget()
        self.main_window.tab_widget.setObjectName("ProfessionalTabWidget")
        self.main_window.tab_widget.setTabPosition(QTabWidget.North)
        self.main_window.tab_widget.setTabsClosable(True)  # 啟用分頁關閉按鈕
        
        # ✅ 啟用標籤列顯示
        self.main_window.tab_widget.tabBar().setVisible(True)
        logger.debug(f"[TAB] ✅ 標籤列已啟用，可見性: {self.main_window.tab_widget.tabBar().isVisible()}")
        
        # 連接分頁關閉信號
        self.main_window.tab_widget.tabCloseRequested.connect(self.main_window.close_tab)
        self.main_window.tab_widget.currentChanged.connect(self.main_window._on_tab_changed)
        
        # 分頁標籤樣式（緊湊型）
        self.main_window.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                border-top: 1px solid #CCCCCC;
            }
            QTabBar::tab {
                background: #E0E0E0;
                border: 1px solid #CCCCCC;
                border-bottom: none;
                padding: 6px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                border-bottom-color: #FFFFFF;
            }
            QTabBar::tab:hover {
                background: #D0D0D0;
            }
        """)
        
        # ===== 左側：新增分頁按鈕（緊鄰標籤）=====
        # 創建左側按鈕容器（只有 "+" 按鈕）
        left_buttons_container = QWidget()
        left_buttons_layout = QHBoxLayout(left_buttons_container)
        left_buttons_layout.setContentsMargins(5, 0, 5, 0)
        left_buttons_layout.setSpacing(0)
        
        # 新增分頁按鈕（白底黑字）
        add_tab_btn = QPushButton("+")
        add_tab_btn.setObjectName("AddTabButton")
        add_tab_btn.setFixedSize(30, 30)
        add_tab_btn.setToolTip("新增分頁")
        add_tab_btn.clicked.connect(self.main_window.add_new_tab)
        add_tab_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #000000;
                font-size: 16pt;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        left_buttons_layout.addWidget(add_tab_btn)
        
        # 將左側按鈕設為 TabBar 的左上角 CornerWidget
        self.main_window.tab_widget.setCornerWidget(left_buttons_container, Qt.TopLeftCorner)
        
        # ===== 右側：全局控制按鈕 =====
        right_buttons_container = QWidget()
        right_buttons_layout = QHBoxLayout(right_buttons_container)
        right_buttons_layout.setContentsMargins(5, 0, 5, 0)
        right_buttons_layout.setSpacing(5)
        
        # Show All Data 按鈕（左側，移除粗體）
        self.main_window.show_all_data_btn = QPushButton("Show All Data")
        self.main_window.show_all_data_btn.setObjectName("ShowAllDataButton")
        self.main_window.show_all_data_btn.setFixedHeight(30)
        self.main_window.show_all_data_btn.setToolTip("顯示當前分頁的所有數據")
        self.main_window.show_all_data_btn.clicked.connect(self.main_window.show_all_data_in_current_tab)
        self.main_window.show_all_data_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                padding: 5px 15px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        right_buttons_layout.addWidget(self.main_window.show_all_data_btn)
        
        # Close All Windows 按鈕（右側，移除粗體）
        self.main_window.close_all_windows_btn = QPushButton("Close All Windows")
        self.main_window.close_all_windows_btn.setObjectName("CloseAllWindowsButton")
        self.main_window.close_all_windows_btn.setFixedHeight(30)
        self.main_window.close_all_windows_btn.setToolTip("關閉當前分頁的所有 MDI 視窗")
        self.main_window.close_all_windows_btn.clicked.connect(self.main_window.close_all_mdi_windows_in_current_tab)
        self.main_window.close_all_windows_btn.setStyleSheet("""
            QPushButton {
                background: #FFE6E6;
                color: #CC0000;
                border: 1px solid #FFAAAA;
                border-radius: 3px;
                padding: 5px 15px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #FFCCCC;
                border: 1px solid #FF6666;
            }
            QPushButton:pressed {
                background: #FFB3B3;
            }
        """)
        right_buttons_layout.addWidget(self.main_window.close_all_windows_btn)
        
        # 將右側按鈕容器設為 QTabWidget 的 CornerWidget
        self.main_window.tab_widget.setCornerWidget(right_buttons_container, Qt.TopRightCorner)
        
        # ===== 組裝主布局 =====
        # 移除全局工具列，直接使用 QTabWidget（按鈕已整合到 CornerWidget）
        main_layout.addWidget(self.main_window.tab_widget)  # 分頁容器
        
        # 隱藏的分頁數量標籤（保留以避免錯誤）
        self.main_window.tab_count_label = QLabel("分頁: 0")
        self.main_window.tab_count_label.setObjectName("TabCountLabel")
        self.main_window.tab_count_label.hide()  # 完全隱藏
        
        # 🆕 設置 TabManager (Phase 2 重構)
        self.main_window.tab_manager.setup_tab_widget(self.main_window.tab_widget, self.main_window.tab_count_label)
        
        # 初始化預設分頁
        self.main_window.init_default_tabs()
        
        return main_container
