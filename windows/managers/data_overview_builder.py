# -*- coding: utf-8 -*-
"""
DataOverviewBuilder - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMdiArea
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from core.gui_i18n import tr

from core.logger import get_logger
from PyQt5.QtWidgets import QPushButton
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class DataOverviewBuilder:
    """從 f1t_gui_main.py 提取的 create_data_overview_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_data_overview_tab(self):
        """創建數據總覽分頁"""
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
                background: #E8E8E8;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton(tr("show_all_data", "Show All Data"))
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        # 標題標籤
        title_label = QLabel(tr("data_overview", "[STATS] Data Overview"))
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
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(close_all_btn)
        toolbar_layout.addWidget(reset_btn)
        
        # 創建MDI區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("OverviewMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 連接關閉所有視窗按鈕
        close_all_btn.clicked.connect(lambda: self.main_window.close_all_mdi_windows(mdi_area))
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.main_window.reset_all_charts(mdi_area))
        
        # 深度修復背景問題 - 多層次設置
        self.main_window.force_white_background(mdi_area)
        
        # 添加統計視窗
        stats_window = PopoutSubWindow(tr("statistics_data", "Statistics Data"), mdi_area)
        stats_content = QLabel(tr("season_statistics", "[CHART] Season Statistics\n• Total Laps: 1,247\n• Average Lap Time: 1:18.456\n• Fastest Lap: 1:16.123"))
        stats_content.setObjectName("StatsContent")
        stats_window.setWidget(stats_content)
        stats_window.resize(300, 200)  # 改為resize，允許調整大小
        mdi_area.addSubWindow(stats_window)
        stats_window.move(10, 10)
        stats_window.show()
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
