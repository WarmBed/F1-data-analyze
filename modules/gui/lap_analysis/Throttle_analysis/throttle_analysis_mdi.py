#!/usr/bin/env python3
"""
油門分析 MDI 模組
================

提供 F1 遙測數據的油門分析功能，支援單車手模式和雙車手比較模式。

特性：
- 從 JSON 檔案載入油門數據
- 支援車手比較模式
- 提供統計資訊顯示
- 原生 PyQt5 圖表繪製

Author: F1T Team
Date: 2025-09-04
Version: 1.0.0
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel, QCheckBox
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QFont
import sys
import os

# 將專案根目錄加入路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from modules.gui.base import BaseAnalysisModule
from .throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
from .throttle_analysis_data_loader import ThrottleAnalysisDataLoader


class ThrottleAnalysisModule(BaseAnalysisModule):
    """油門分析模組 - 提供 F1 遙測數據的油門分析功能"""
    
    # 定義信號
    module_sync_signal = pyqtSignal(int, str, str)  # 年份、賽事、賽段同步信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("油門分析模組")
        self.setFixedSize(1000, 700)  # 設定固定大小
        
        # 模組識別
        self.module_type = "throttle_analysis"
        
        # 數據屬性
        self.current_year = "2025"
        self.current_race = "Japan" 
        self.current_session = "R"
        
        # 組件引用
        self.chart_widget = None
        self.data_loader = None
        
        # 控制組件
        self.driver1_combo = None
        self.driver2_combo = None
        self.lap1_combo = None
        self.lap2_combo = None
        self.load_button = None
        self.comparison_mode_checkbox = None
        
        # 設置 UI
        self._setup_ui()
        
        # 創建數據載入器
        self._setup_data_loader()
        
        print(f"[THROTTLE_MODULE] 油門分析模組初始化完成")
    
    def _setup_ui(self):
        """設置用戶界面"""
        main_layout = QVBoxLayout()
        
        # 控制面板
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 圖表區域
        self.chart_widget = ThrottleAnalysisChartWidget(self)
        main_layout.addWidget(self.chart_widget)
        
        self.setLayout(main_layout)
        
        print(f"[THROTTLE_MODULE] UI 設置完成")
    
    def _create_control_panel(self):
        """創建控制面板"""
        control_widget = QWidget()
        layout = QVBoxLayout()
        
        # 第一行：比較模式選擇
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("比較模式:"))
        
        self.comparison_mode_checkbox = QCheckBox("雙車手比較")
        self.comparison_mode_checkbox.setChecked(False)  # 預設為單車手模式
        self.comparison_mode_checkbox.stateChanged.connect(self._on_comparison_mode_changed)
        mode_layout.addWidget(self.comparison_mode_checkbox)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # 第二行：車手和圈數選擇
        selection_layout = QHBoxLayout()
        
        # 車手1選擇
        selection_layout.addWidget(QLabel("車手1:"))
        self.driver1_combo = QComboBox()
        self.driver1_combo.addItems(["ALO", "VER", "HAM", "LEC", "NOR", "SAI", "RUS", "PER"])
        self.driver1_combo.setCurrentText("ALO")
        selection_layout.addWidget(self.driver1_combo)
        
        selection_layout.addWidget(QLabel("圈數1:"))
        self.lap1_combo = QComboBox()
        self.lap1_combo.addItems([str(i) for i in range(1, 11)])  # 1-10圈
        self.lap1_combo.setCurrentText("1")
        selection_layout.addWidget(self.lap1_combo)
        
        # 車手2選擇（雙車手模式時啟用）
        selection_layout.addWidget(QLabel("車手2:"))
        self.driver2_combo = QComboBox()
        self.driver2_combo.addItems(["ALO", "VER", "HAM", "LEC", "NOR", "SAI", "RUS", "PER"])
        self.driver2_combo.setCurrentText("VER")
        self.driver2_combo.setEnabled(False)  # 預設禁用
        selection_layout.addWidget(self.driver2_combo)
        
        selection_layout.addWidget(QLabel("圈數2:"))
        self.lap2_combo = QComboBox()
        self.lap2_combo.addItems([str(i) for i in range(1, 11)])  # 1-10圈
        self.lap2_combo.setCurrentText("1")
        self.lap2_combo.setEnabled(False)  # 預設禁用
        selection_layout.addWidget(self.lap2_combo)
        
        # 載入按鈕
        self.load_button = QPushButton("🔄 載入數據")
        self.load_button.clicked.connect(self._load_throttle_data)
        selection_layout.addWidget(self.load_button)
        
        selection_layout.addStretch()
        layout.addLayout(selection_layout)
        
        control_widget.setLayout(layout)
        return control_widget
    
    def _setup_data_loader(self):
        """設置數據載入器"""
        self.data_loader = ThrottleAnalysisDataLoader()
        
        # 連接信號
        self.data_loader.data_loaded.connect(self.chart_widget.update_throttle_data)
        self.data_loader.data_loaded.connect(self._on_data_loaded)  # 新增：數據載入成功後更新工具欄狀態
        self.data_loader.load_error.connect(self._on_data_load_failed)  # 修正：使用正確的信號名稱
        
        print(f"[THROTTLE_MODULE] 數據載入器設置完成")
    
    def _on_comparison_mode_changed(self, state):
        """比較模式變更時的處理"""
        is_comparison = state == 2  # Qt.Checked
        
        # 啟用/禁用車手2和圈數2的控件
        self.driver2_combo.setEnabled(is_comparison)
        self.lap2_combo.setEnabled(is_comparison)
        
        print(f"[THROTTLE_MODULE] 比較模式變更為: {'雙車手' if is_comparison else '單車手'}")
    
    def _load_throttle_data(self):
        """載入油門數據"""
        try:
            # 獲取參數
            year = int(self.current_year)
            race = self.current_race
            session = self.current_session
            driver1 = self.driver1_combo.currentText()
            lap1 = int(self.lap1_combo.currentText())
            
            # 檢查是否為比較模式
            is_comparison = self.comparison_mode_checkbox.isChecked()
            
            if is_comparison:
                driver2 = self.driver2_combo.currentText()
                lap2 = int(self.lap2_combo.currentText())
            else:
                driver2 = None
                lap2 = None
            
            print(f"[THROTTLE_MODULE] 載入油門數據: {year} {race} {session}")
            print(f"[THROTTLE_MODULE] 車手參數: {driver1}(L{lap1}) vs {driver2}(L{lap2})")
            
            # 更新載入按鈕狀態
            self.load_button.setText("⏳ 載入中...")
            self.load_button.setEnabled(False)
            
            # 使用數據載入器載入數據
            self.data_loader.load_throttle_data(
                year=year,
                race=race,
                session=session,
                driver1=driver1,
                driver2=driver2,
                lap1=lap1,
                lap2=lap2,
                is_fastest_lap=False
            )
            
            # 延遲恢復按鈕狀態
            QTimer.singleShot(2000, self._restore_load_button)
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MODULE] 載入數據失敗: {e}")
            self._restore_load_button()
    
    def _restore_load_button(self):
        """恢復載入按鈕狀態"""
        self.load_button.setText("🔄 載入數據")
        self.load_button.setEnabled(True)
    
    def _on_data_loaded(self, data):
        """數據載入成功後的處理"""
        try:
            print(f"[THROTTLE_MODULE] 數據載入成功，更新工具欄狀態")
            
            # 更新工具欄狀態信息
            self._update_toolbar_status(data)
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MODULE] 數據載入後處理失敗: {e}")
    
    def _update_toolbar_status(self, data: dict):
        """更新工具欄狀態信息"""
        try:
            # 獲取主視窗引用
            main_window = self._get_main_window()
            if not main_window or not hasattr(main_window, 'update_toolbar_status'):
                return
            
            # 提取狀態信息
            metadata = data.get('metadata', {})
            drivers = metadata.get('drivers', [])
            
            module_name = "油門分析"
            lap_time = ""
            tyre_compound = ""
            lap_numbers = ""
            
            if drivers:
                if len(drivers) >= 2:
                    # 雙車手模式
                    driver1 = drivers[0]
                    driver2 = drivers[1]
                    
                    lap_time1 = driver1.get('lap_time', 'N/A')
                    lap_time2 = driver2.get('lap_time', 'N/A')
                    lap_time = f"{lap_time1} | {lap_time2}"
                    
                    compound1 = driver1.get('compound', 'N/A')
                    compound2 = driver2.get('compound', 'N/A')
                    tyre_compound = f"{compound1} | {compound2}"
                    
                    driver1_code = driver1.get('code', self.driver1_combo.currentText())
                    driver2_code = driver2.get('code', self.driver2_combo.currentText())
                    lap_numbers = f"{driver1_code} 第{self.lap1_combo.currentText()}圈 vs {driver2_code} 第{self.lap2_combo.currentText()}圈"
                    
                elif len(drivers) >= 1:
                    # 單車手模式
                    driver1 = drivers[0]
                    lap_time = driver1.get('lap_time', 'N/A')
                    tyre_compound = driver1.get('compound', 'N/A')
                    
                    driver1_code = driver1.get('code', self.driver1_combo.currentText())
                    lap_numbers = f"{driver1_code} 第{self.lap1_combo.currentText()}圈"
            else:
                # 無車手數據時顯示基本信息
                lap_numbers = f"第{self.lap1_combo.currentText()}圈"
                if self.comparison_mode_checkbox.isChecked():
                    lap_numbers += f" vs 第{self.lap2_combo.currentText()}圈"
            
            # 更新工具欄狀態
            main_window.update_toolbar_status(
                module_name=module_name,
                lap_time=lap_time,
                tyre_compound=tyre_compound,
                lap_numbers=lap_numbers
            )
            
            print(f"[THROTTLE_MODULE] 已更新工具欄狀態: {module_name}")
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MODULE] 更新工具欄狀態失敗: {e}")
    
    def _get_main_window(self):
        """獲取主視窗引用"""
        try:
            # 通過父元件向上查找主視窗
            widget = self.parent()
            while widget and not hasattr(widget, 'update_toolbar_status'):
                widget = widget.parent()
            return widget
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MODULE] 獲取主視窗引用失敗: {e}")
            return None
    
    def _on_data_load_failed(self, error_message):
        """數據載入失敗時的處理"""
        print(f"[ERROR] [THROTTLE_MODULE] 數據載入失敗: {error_message}")
        self._restore_load_button()
    
    def initialize_module(self):
        """初始化模組"""
        try:
            print(f"[THROTTLE_MODULE] 開始初始化模組...")
            
            # 載入預設數據
            self._load_default_data()
            
            print(f"[THROTTLE_MODULE] ✅ 模組初始化成功")
            return True
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MODULE] 模組初始化失敗: {e}")
            return False
    
    def _load_default_data(self):
        """載入預設數據"""
        try:
            # 自動載入預設的 ALO 數據
            print(f"[THROTTLE_MODULE] 載入預設數據: {self.current_year} {self.current_race} {self.current_session}")
            self._load_throttle_data()
            
        except Exception as e:
            print(f"[WARNING] [THROTTLE_MODULE] 預設數據載入失敗: {e}")
    
    def update_parameters(self, year, race, session):
        """更新分析參數"""
        try:
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            print(f"[THROTTLE_MODULE] 參數更新: {year} {race} {session}")
            
            # 發送同步信號
            self.module_sync_signal.emit(year, race, session)
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MODULE] 參數更新失敗: {e}")
    
    def get_analysis_type(self):
        """獲取分析類型"""
        return "油門分析"
    
    def get_module_info(self):
        """獲取模組資訊"""
        return {
            "name": "油門分析模組",
            "version": "1.0.0",
            "type": "throttle_analysis",
            "description": "F1 遙測數據油門分析工具"
        }
        