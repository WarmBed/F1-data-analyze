# -*- coding: utf-8 -*-
"""
LapAnalysisControlsCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QSpinBox
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LapAnalysisControlsCreator:
    """從 f1t_gui_main.py 提取的 _create_lap_analysis_controls 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _create_lap_analysis_controls(self):
        """創建遙測分析控件（不添加到工具欄）"""
        logger.debug("[LAP_CONTROL] [DEBUG]   🏗️ 創建遙測分析控件...")
        
        # 動態遙測分析控件
        self.main_window.lap_separator = None
        
        # 車手1控件
        self.main_window.driver1_label = QLabel(tr("driver1_label", "Driver 1:"))
        self.main_window.driver1_label.setVisible(False)  # 初始隱藏
        self.main_window.driver1_combo = QComboBox()
        self.main_window.driver1_combo.setObjectName("ParameterCombo")
        self.main_window.driver1_combo.setFixedWidth(60)
        self.main_window.driver1_combo.setVisible(False)  # 初始隱藏
        
        # 圈數1控件
        self.main_window.lap1_label = QLabel(tr("lap_label", "Lap:"))
        self.main_window.lap1_label.setVisible(False)  # 初始隱藏
        self.main_window.lap1_spinbox = QSpinBox()
        self.main_window.lap1_spinbox.setRange(1, 100)
        self.main_window.lap1_spinbox.setValue(1)
        self.main_window.lap1_spinbox.setFixedWidth(50)
        self.main_window.lap1_spinbox.setVisible(False)  # 初始隱藏
        
        # 車手2控件
        self.main_window.driver2_label = QLabel(tr("driver2_label", "Driver 2:"))
        self.main_window.driver2_label.setVisible(False)  # 初始隱藏
        self.main_window.driver2_combo = QComboBox()
        self.main_window.driver2_combo.setObjectName("ParameterCombo")
        self.main_window.driver2_combo.addItem(tr("none_option", "None"))  # 預設選項
        self.main_window.driver2_combo.setFixedWidth(60)
        self.main_window.driver2_combo.setVisible(False)  # 初始隱藏
        
        # 圈數2控件
        self.main_window.lap2_label = QLabel(tr("lap_label", "Lap:"))
        self.main_window.lap2_label.setVisible(False)  # 初始隱藏
        self.main_window.lap2_spinbox = QSpinBox()
        self.main_window.lap2_spinbox.setRange(1, 100)
        self.main_window.lap2_spinbox.setValue(1)
        self.main_window.lap2_spinbox.setFixedWidth(50)
        self.main_window.lap2_spinbox.setVisible(False)  # 初始隱藏
        
        # 最速圈選項
        self.main_window.fastest_lap_checkbox = QCheckBox(tr("fastest_lap_option", "Fastest Lap"))
        self.main_window.fastest_lap_checkbox.setVisible(False)  # 初始隱藏
        
        # 🏁 連接最速圈checkbox的變更事件，自動設置圈數為99
        self.main_window.fastest_lap_checkbox.toggled.connect(self.main_window._on_main_fastest_lap_changed)

        # 使用時間軸選項
        self.main_window.use_time_axis_checkbox = QCheckBox(tr("use_time_axis_option", "Use Time Axis"))
        self.main_window.use_time_axis_checkbox.setVisible(False)
        
        # 更新按鈕動作（稍後動態添加）
        self.main_window.update_all_action = None
        
        # 🔄 手動更新模式：控件變更不會自動觸發更新
        # 用戶必須手動點擊 "Update All Analysis" 按鈕才會更新所有模組
        # 已移除自動連接：
        # self.main_window.driver1_combo.currentTextChanged.connect(self.main_window.on_lap_parameters_changed)
        # self.main_window.driver2_combo.currentTextChanged.connect(self.main_window.on_lap_parameters_changed)
        # self.main_window.lap1_spinbox.valueChanged.connect(self.main_window.on_lap_parameters_changed)
        # self.main_window.lap2_spinbox.valueChanged.connect(self.main_window.on_lap_parameters_changed)
        # self.main_window.fastest_lap_checkbox.toggled.connect(self.main_window.on_lap_parameters_changed)
        
        logger.debug("[LAP_CONTROL] [DEBUG]   ✅ 遙測分析控件創建完成（手動更新模式已啟用）")
