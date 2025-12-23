# -*- coding: utf-8 -*-
"""
ToolbarBuilder - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QLabel, QToolBar

from core.logger import get_logger
from core.gui_i18n import tr
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QComboBox

logger = get_logger(__name__)


class ToolbarBuilder:
    """從 f1t_gui_main.py 提取的 create_professional_toolbar 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_professional_toolbar(self):
        """創建專業工具欄"""
        toolbar = QToolBar()
        toolbar.setObjectName("ProfessionalToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        # 修改：增加工具欄高度以容納遙測分析控件
        toolbar.setFixedHeight(35)  # 從35增加到50像素
        self.addToolBar(toolbar)
        
        # 參數輸入區域
        toolbar.addWidget(QLabel(tr("year_label", "Year:")))
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("ParameterCombo")
        self.year_combo.addItems([str(year) for year in range(2020, 2027)])
        self.year_combo.setCurrentText("2025")
        self.year_combo.setFixedWidth(70)
        toolbar.addWidget(self.year_combo)
        
        toolbar.addWidget(QLabel(tr("race_label", "Race:")))
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("ParameterCombo")
        # 賽事項目將由 on_year_changed 方法動態填充
        self.race_combo.setFixedWidth(250)  # 增加寬度以容納較長的賽事名稱
        toolbar.addWidget(self.race_combo)
        
        toolbar.addWidget(QLabel(tr("session_label", "Session:")))
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("ParameterCombo")
        self.session_combo.addItems(["FP1", "FP2", "FP3", "SQ", "S", "Q", "R"])  # Sprint (S) 支援
        self.session_combo.setCurrentText("R")
        self.session_combo.setFixedWidth(50)
        toolbar.addWidget(self.session_combo)
        
        # 保存工具欄引用以便動態添加/移除控件
        self.main_toolbar = toolbar
        
        # 建立遙測分析控件但不添加到工具欄（將在需要時動態添加）
        self._create_lap_analysis_controls()
        
        toolbar.addSeparator()
        
        # 檢視控制
        toolbar.addAction(tr("tile_windows_action", "Tile Windows"), self.tile_windows)
        toolbar.addAction(tr("cascade_windows_action", "Cascade Windows"), self.cascade_windows)
        
        # 連接年份變更事件
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        
        # 連接賽事和會話變更事件 - 添加同步功能
        self.race_combo.currentTextChanged.connect(self.on_main_race_changed)
        self.session_combo.currentTextChanged.connect(self.on_main_session_changed)
        
        # 初始化賽事列表
        initial_year = int(self.year_combo.currentText())
        self._refresh_calendar_for_year(initial_year)

    # ------------------------------------------------------------------
    # 賽季日曆支援
    # ------------------------------------------------------------------