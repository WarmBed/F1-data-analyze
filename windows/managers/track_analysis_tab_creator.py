# -*- coding: utf-8 -*-
"""
TrackAnalysisTabCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger

logger = get_logger(__name__)


class TrackAnalysisTabCreator:
    """從 f1t_gui_main.py 提取的 create_track_analysis_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_track_analysis_tab(self):
        """創建賽道分析分頁 - 使用通用 TrackAnalysisUniversal 模組"""
        # 直接調用新的賽道分析視窗功能
        self.main_window.open_track_analysis_window()
        
        # 返回一個空的容器，以保持分頁結構的兼容性
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顯示提示信息
        info_label = QLabel("[FINISH] 賽道軌跡分析已在新視窗中開啟")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                font-weight: bold;
                padding: 20px;
                background: #F8F8F8;
                border: 2px dashed #CCCCCC;
                border-radius: 8px;
            }
        """)
        tab_layout.addWidget(info_label)
        
        # 添加說明文字
        desc_label = QLabel("""
        新的賽道軌跡分析功能已升級為獨立的 MDI 子視窗：
        
        [OK] 高效能 PyQtGraph 繪圖引擎
        [OK] 互動式賽道軌跡顯示
        [OK] 原點標記與位置點選擇
        [OK] 支援縮放、平移操作
        [OK] 與主視窗參數同步
        
        請在獨立視窗中使用新的分析功能。
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("""
            QLabel {
                color: #555555;
                font-size: 11px;
                padding: 10px;
                background: transparent;
                line-height: 1.4;
            }
        """)
        tab_layout.addWidget(desc_label)
        
        return tab_container
