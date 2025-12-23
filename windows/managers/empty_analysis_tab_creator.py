# -*- coding: utf-8 -*-
"""
EmptyAnalysisTabCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMdiArea

logger = get_logger(__name__)


class EmptyAnalysisTabCreator:
    """從 f1t_gui_main.py 提取的 create_empty_analysis_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_empty_analysis_tab(self):
        """創建空白的分析分頁，只包含MDI區域"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #F0F0F0;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 標題標籤
        from core.gui_i18n import tr
        title_label = QLabel(tr('analysis_workspace', 'Analysis Workspace'))
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 關閉所有視窗按鈕
        from core.gui_i18n import tr
        close_all_btn = QPushButton(tr('close_all_windows', 'Close All Windows'))
        close_all_btn.setFixedSize(120, 25)
        close_all_btn.setStyleSheet("""
            QPushButton {
                background: #FFE6E6;
                color: #CC0000;
                border: 1px solid #FFAAAA;
                border-radius: 3px;
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
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton(tr("show_all_data", "Show All Data"))
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #F8F8F8;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #E8E8E8;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #DDDDDD;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        
        # 添加分隔符
        separator = QLabel("|")
        separator.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        toolbar_layout.addWidget(separator)
        
        # 創建動態狀態信息區域
        self.main_window.toolbar_status_widget = self.main_window._create_toolbar_status_widget()
        toolbar_layout.addWidget(self.main_window.toolbar_status_widget)
        
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(close_all_btn)
        toolbar_layout.addWidget(reset_btn)
        
        # 創建空白的MDI區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("AnalysisMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # [TOOL] 修復: 註冊MDI區域到主視窗
        self.main_window.register_mdi_area(mdi_area)
        logger.debug(f"[OK] [MDI] 已註冊分析MDI區域: {mdi_area.objectName()}")
        
        # 連接關閉所有視窗按鈕
        close_all_btn.clicked.connect(lambda: self.main_window.close_all_mdi_windows(mdi_area))
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.main_window.reset_all_charts(mdi_area))
        
        # 強制設置白色背景
        self.main_window.force_white_background(mdi_area)
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
