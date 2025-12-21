# -*- coding: utf-8 -*-
"""
UiInitializer - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class UiInitializer:
    """從 f1t_gui_main.py 提取的 init_ui 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def init_ui(self):
        """初始化用戶界面"""
        # 創建菜單欄
        self.main_window.create_professional_menubar()
        
        # 創建工具欄
        logger.debug("[INIT] 🔧 開始創建專業工具欄...")
        self.main_window.create_professional_toolbar()
        logger.debug("[INIT] ✅ 專業工具欄創建完成")
        
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        
        # 主布局 - 移除參數面板
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(1)
        
        # 主要分析區域
        analysis_splitter = QSplitter(Qt.Horizontal)
        analysis_splitter.setChildrenCollapsible(False)
        
        # 左側功能樹
        left_panel = self.main_window.create_left_panel()
        analysis_splitter.addWidget(left_panel)
        
        # 中央工作區域 - MDI多視窗
        center_panel = self.main_window.create_professional_workspace()
        analysis_splitter.addWidget(center_panel)
        
        # 設置分割比例 - 移除右側面板
        analysis_splitter.setSizes([200, 1400])
        
        # 監聽 Splitter 調整事件，標記用戶手動調整
        analysis_splitter.splitterMoved.connect(self.main_window._on_splitter_moved)
        
        # 保存 splitter 引用
        self.main_window.analysis_splitter = analysis_splitter
        
        main_layout.addWidget(analysis_splitter)
        
        # Live Timing Control Dock (預設隱藏，開啟任一 Live Timing 模組時自動顯示)
        self.main_window._setup_live_timing_dock()
        
        # 專業狀態列
        self.main_window.create_professional_status_bar()
