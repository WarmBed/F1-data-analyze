# -*- coding: utf-8 -*-
"""
LapAnalysisOptionsDialog - 遙測分析選項對話框
=============================================

從 f1t_gui_main.py 提取的遙測分析選項對話框。
讓使用者選擇要顯示的遙測圖表和車手。
"""

from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QComboBox, QCheckBox, QPushButton, QLabel, QGroupBox,
    QListWidget, QListWidgetItem, QLineEdit, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger(__name__)


class LapAnalysisOptionsDialog(QDialog):
    """遙測分析選項對話框 - 讓使用者選擇要顯示的遙測圖表和車手"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # 保存父視窗引用
        # 保留用戶當前語言設定，不強制切換
        # set_gui_language('en')  # 已移除強制設定
        
        self.setWindowTitle(tr("telemetry_options_title"))
        self.setModal(True)
        self.setFixedSize(420, 520)
        
        # 設置字體 - 與主程式保持一致
        font = QFont("Arial", 8)  # 與主程式app.setFont(font)一致
        self.setFont(font)
        
        # 設置視窗樣式 - 採用主程式風格
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                color: #333333;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
            }
            QListWidget {
                background-color: #f9f9f9;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                padding: 2px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
                alternate-background-color: #f0f0f0;
            }
            QListWidget::item {
                padding: 3px 8px;
                border-bottom: 1px solid #e8e8e8;
                min-height: 16px;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
            }
            QListWidget::item:selected {
                background-color: #d1e7dd;
                color: #333333;
                border: 1px solid #a3cfbb;
            }
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 8pt;
                padding: 4px 12px;
                min-height: 18px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
            QLabel {
                color: #333333;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
            }
            QComboBox {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                padding: 2px 5px;
                font-size: 8pt;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                min-height: 18px;
            }
            QComboBox:hover {
                border: 1px solid #999999;
            }
            QComboBox::drop-down {
                border: none;
                width: 15px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid #999999;
                width: 3px;
                height: 3px;
                border-top: none;
                border-left: none;
                margin-right: 3px;
            }
            QLineEdit {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                padding: 2px 5px;
                font-size: 8pt;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                min-height: 18px;
            }
            QLineEdit:hover {
                border: 1px solid #999999;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
            QCheckBox {
                color: #333333;
                font-size: 8pt;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #999999;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
            }
            QCheckBox::indicator:checked:before {
                content: "✓";
                color: white;
                font-weight: bold;
                text-align: center;
            }
            QGroupBox {
                color: #333333;
                font-weight: bold;
                font-size: 8pt;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 5px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
                background: #f0f0f0;
            }
        """)
        
        self.init_ui()
        self.selected_charts = []
        
    def init_ui(self):
        """初始化使用者介面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 標題
        title_label = QLabel(tr("select_telemetry_charts"))
        title_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #333333; margin-bottom: 5px; font-family: 'Arial', 'Microsoft JhengHei', sans-serif;")
        layout.addWidget(title_label)
        
        # 車手選擇區域
        driver_group = QGroupBox(tr("driver_lap_selection"))
        driver_layout = QGridLayout(driver_group)
        driver_layout.setSpacing(8)
        
        # 車手1 (必選)
        driver1_label = QLabel(tr("driver1_required"))
        self.driver1_combo = QComboBox()
        self.driver1_combo.setFixedWidth(100)
        driver_layout.addWidget(driver1_label, 0, 0)
        driver_layout.addWidget(self.driver1_combo, 0, 1)
        
        # 車手1圈數
        lap1_label = QLabel(tr("lap_number"))
        self.lap1_input = QLineEdit()
        self.lap1_input.setText("1")
        self.lap1_input.setFixedWidth(50)
        self.lap1_input.setPlaceholderText(tr("lap", "Lap"))
        driver_layout.addWidget(lap1_label, 0, 2)
        driver_layout.addWidget(self.lap1_input, 0, 3)
        
        # 車手2 (選用)
        driver2_label = QLabel(tr("driver2_optional"))
        self.driver2_combo = QComboBox()
        self.driver2_combo.setFixedWidth(100)
        self.driver2_combo.addItem(tr("none_option", "None"), None)  # 第一個選項為無
        driver_layout.addWidget(driver2_label, 1, 0)
        driver_layout.addWidget(self.driver2_combo, 1, 1)
        
        # 車手2圈數
        lap2_label = QLabel(tr("lap_number"))
        self.lap2_input = QLineEdit()
        self.lap2_input.setText("1")
        self.lap2_input.setFixedWidth(50)
        self.lap2_input.setPlaceholderText(tr("lap", "Lap"))
        driver_layout.addWidget(lap2_label, 1, 2)
        driver_layout.addWidget(self.lap2_input, 1, 3)
        
        # 最速圈勾選框
        self.fastest_lap_checkbox = QCheckBox(tr("fastest_lap_option", "Fastest Lap"))
        self.fastest_lap_checkbox.setMinimumWidth(110)
        self.fastest_lap_checkbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.fastest_lap_checkbox.setChecked(False)
        self.fastest_lap_checkbox.stateChanged.connect(self._on_fastest_lap_changed)
        driver_layout.addWidget(self.fastest_lap_checkbox, 0, 4, 2, 1)  # 跨兩行放在右邊
        
        # 設置列寬度比例
        driver_layout.setColumnStretch(4, 1)  # 添加彈性空間
        
        layout.addWidget(driver_group)
        
        # 🆕 從主視窗快取載入車手列表
        year = int(self.parent_window.year_combo.currentText()) if self.parent_window and hasattr(self.parent_window, 'year_combo') else 2025
        drivers = self.parent_window.get_drivers_for_year(year) if self.parent_window and hasattr(self.parent_window, 'get_drivers_for_year') else []
        
        # 填充車手下拉選單
        if drivers:
            self.driver1_combo.addItems(drivers)
            self.driver1_combo.setCurrentText(drivers[0])  # 預設第一位
            
            self.driver2_combo.addItem(tr("none_option", "None"))
            self.driver2_combo.addItems(drivers)
            self.driver2_combo.setCurrentIndex(0)  # 預設 None
            logger.debug(f"[DIALOG] ✅ 已載入 {len(drivers)} 位車手到對話框")
        else:
            logger.debug(f"[DIALOG] ⚠️  無車手數據")
        
        # 創建列表控件 - 更緊湊的設計
        telemetry_group = QGroupBox(tr("telemetry_options"))
        telemetry_layout = QVBoxLayout(telemetry_group)
        
        self.telemetry_list = QListWidget()
        self.telemetry_list.setSelectionMode(QListWidget.MultiSelection)
        self.telemetry_list.setAlternatingRowColors(True)
        
        # 定義遙測選項
        self.telemetry_options = {
            "speed_analysis": ("⚡", "speed_analysis", True),
            "brake": ("🛑", "brake_analysis", True),
            "throttle": ("⚡", "throttle_analysis", True),
            "gear": ("⚙️", "gear_analysis", True),
            "rpm": ("🔄", "rpm_analysis", True),
            "acceleration": ("📈", "acceleration_analysis", True),
            "speed_diff": ("📊", "speeddiff_analysis", True),
            "distancediff": ("📏", "distancediff_analysis", True),
        }

        # 添加選項到列表
        for key, (emoji, label_key, default_checked) in self.telemetry_options.items():
            label_text = tr(label_key, label_key.replace("_", " ").title())
            item = QListWidgetItem(f"{emoji} {label_text}")
            item.setData(Qt.UserRole, key)  # 存儲鍵值
            self.telemetry_list.addItem(item)
            if default_checked:
                item.setSelected(True)
        
        telemetry_layout.addWidget(self.telemetry_list)
        layout.addWidget(telemetry_group)
        
        # 快速選擇按鈕 - 更緊湊的布局
        quick_select_layout = QHBoxLayout()
        quick_select_layout.setSpacing(8)
        
        select_all_btn = QPushButton(tr("select_all"))
        select_all_btn.setFixedHeight(28)
        select_all_btn.clicked.connect(self.select_all)
        quick_select_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton(tr("select_none"))
        select_none_btn.setFixedHeight(28)
        select_none_btn.clicked.connect(self.select_none)
        quick_select_layout.addWidget(select_none_btn)
        
        default_btn = QPushButton(tr("restore_default"))
        default_btn.setFixedHeight(28)
        default_btn.clicked.connect(self.set_default)
        quick_select_layout.addWidget(default_btn)
        
        quick_select_layout.addStretch()
        layout.addLayout(quick_select_layout)
        
        # 對話框按鈕
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()
        
        ok_btn = QPushButton(tr("ok"))
        ok_btn.setFixedSize(60, 26)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.setFixedSize(60, 26)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    # 🗑️ 舊方法已移除：_load_available_drivers()
    # 現在統一使用主視窗的 get_drivers_for_year() 方法
    # 原 API-first 載入邏輯已整合至主視窗的快取機制
    
    def _on_fastest_lap_changed(self, state):
        """當最速圈勾選框變更時的處理"""
        if state == 2:  # 勾選時 (Qt.Checked)
            # 最速圈被選中，禁用兩個圈數輸入並顯示99
            self.lap1_input.setEnabled(False)
            self.lap1_input.setText("99")  # 顯示99代表最速圈
            self.lap1_input.setStyleSheet("color: #666666;")
            
            self.lap2_input.setEnabled(False)
            self.lap2_input.setText("99")  # 顯示99代表最速圈
            self.lap2_input.setStyleSheet("color: #666666;")
        else:
            # 最速圈未選中，啟用兩個圈數輸入
            self.lap1_input.setEnabled(True)
            self.lap1_input.setText("1")
            self.lap1_input.setStyleSheet("")
            
            self.lap2_input.setEnabled(True)
            self.lap2_input.setText("1")
            self.lap2_input.setStyleSheet("")
    
    def get_selected_drivers(self):
        """獲取選擇的車手和圈數資訊"""
        driver1_data = self.driver1_combo.currentData()
        driver1 = driver1_data if driver1_data else self.driver1_combo.currentText()

        driver2_data = self.driver2_combo.currentData()
        driver2 = driver2_data if driver2_data else self.driver2_combo.currentText()
        
        # 判斷是否選擇最速圈
        is_fastest_lap = self.fastest_lap_checkbox.isChecked()
        
        if is_fastest_lap:
            # 🏁 最速圈邏輯：使用圈數99代表最速圈
            # 這與CLI命令 python f1_analysis_modular_main.py -f 13 --lap1 99 --lap2 99 一致
            lap1_number = 99
            lap2_number = 99
            lap_type = tr("fastest_lap_type", "Fastest Lap")
        else:
            # 嘗試解析車手1圈數輸入
            try:
                lap1_number = int(self.lap1_input.text())
            except ValueError:
                lap1_number = 1  # 預設值
            
            # 嘗試解析車手2圈數輸入
            try:
                lap2_number = int(self.lap2_input.text())
            except ValueError:
                lap2_number = 1  # 預設值
                
            lap_type = tr("specific_lap", "Specific Lap")
        
        # 如果車手2選擇了"無"，則返回None
        if driver2_data is None:
            driver2 = None
            lap2_number = None
            
        return {
            'driver1': driver1,
            'driver2': driver2,
            'lap1_number': lap1_number,
            'lap2_number': lap2_number,
            'lap_type': lap_type,
            'is_fastest_lap': is_fastest_lap
        }
        
    def select_all(self):
        """全選所有選項"""
        for i in range(self.telemetry_list.count()):
            item = self.telemetry_list.item(i)
            item.setSelected(True)
            
    def select_none(self):
        """取消所有選項"""
        self.telemetry_list.clearSelection()
            
    def set_default(self):
        """恢復預設選項"""
        self.telemetry_list.clearSelection()
        for i in range(self.telemetry_list.count()):
            item = self.telemetry_list.item(i)
            key = item.data(Qt.UserRole)
            option_config = self.telemetry_options.get(key)
            default_checked = option_config[2] if option_config else False
            if default_checked:
                item.setSelected(True)
    
    def get_selected_charts(self):
        """獲取使用者選擇的圖表類型"""
        selected = []
        for item in self.telemetry_list.selectedItems():
            key = item.data(Qt.UserRole)
            selected.append(key)
        return selected

