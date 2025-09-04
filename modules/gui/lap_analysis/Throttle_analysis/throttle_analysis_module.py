#!/usr/bin/env python3
"""
F1T 油門分析模組
提供油門數據的可視化分析功能
"""

import sys
import os
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QComboBox, QSpinBox,
                           QCheckBox, QGroupBox, QSplitter, QMessageBox)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont

# 導入油門分析組件
from .throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
from .throttle_analysis_data_loader import ThrottleAnalysisDataLoader

class ThrottleAnalysisModule(QWidget):
    """油門分析模組主介面"""
    
    # 信號定義
    data_loaded = pyqtSignal(dict)
    analysis_started = pyqtSignal()
    analysis_completed = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, global_signals=None, parent=None):
        super().__init__(parent)
        
        # 全域信號連接
        self.global_signals = global_signals
        
        # 組件初始化
        self.data_loader = None
        self.chart_widget = None
        self.current_data = None
        
        # 設置UI
        self.setup_ui()
        self.setup_data_loader()
        
        # 連接全域信號
        self.connect_global_signals()
        
    def setup_ui(self):
        """設置用戶介面"""
        self.setObjectName("ThrottleAnalysisModule")
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 標題區域
        title_layout = self.create_title_section()
        main_layout.addLayout(title_layout)
        
        # 控制區域
        control_layout = self.create_control_section()
        main_layout.addLayout(control_layout)
        
        # 圖表區域
        chart_layout = self.create_chart_section()
        main_layout.addLayout(chart_layout, 1)  # 設置伸縮因子為1
        
        print("[THROTTLE_MODULE] UI 設置完成")
    
    def create_title_section(self) -> QHBoxLayout:
        """創建標題區域"""
        layout = QHBoxLayout()
        
        # 標題
        title_label = QLabel("🚀 油門分析")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 狀態標籤
        self.status_label = QLabel("準備就緒")
        self.status_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.status_label)
        
        return layout
    
    def create_control_section(self) -> QHBoxLayout:
        """創建控制區域"""
        layout = QHBoxLayout()
        
        # 車手控制組
        driver_group = QGroupBox("車手選擇")
        driver_layout = QHBoxLayout(driver_group)
        
        # 車手1控制
        driver1_layout = QVBoxLayout()
        driver1_layout.addWidget(QLabel("車手1:"))
        self.driver1_combo = QComboBox()
        self.driver1_combo.setMinimumWidth(80)
        driver1_layout.addWidget(self.driver1_combo)
        
        lap1_layout = QVBoxLayout()
        lap1_layout.addWidget(QLabel("圈數:"))
        self.lap1_spin = QSpinBox()
        self.lap1_spin.setMinimum(1)
        self.lap1_spin.setMaximum(100)
        self.lap1_spin.setValue(1)
        lap1_layout.addWidget(self.lap1_spin)
        
        driver1_container = QHBoxLayout()
        driver1_container.addLayout(driver1_layout)
        driver1_container.addLayout(lap1_layout)
        driver_layout.addLayout(driver1_container)
        
        # 對比模式控制
        self.comparison_checkbox = QCheckBox("雙車手對比")
        self.comparison_checkbox.stateChanged.connect(self.on_comparison_mode_changed)
        driver_layout.addWidget(self.comparison_checkbox)
        
        # 車手2控制
        self.driver2_container = QWidget()
        driver2_layout = QHBoxLayout(self.driver2_container)
        driver2_layout.setContentsMargins(0, 0, 0, 0)
        
        driver2_info_layout = QVBoxLayout()
        driver2_info_layout.addWidget(QLabel("車手2:"))
        self.driver2_combo = QComboBox()
        self.driver2_combo.setMinimumWidth(80)
        driver2_info_layout.addWidget(self.driver2_combo)
        
        lap2_layout = QVBoxLayout()
        lap2_layout.addWidget(QLabel("圈數:"))
        self.lap2_spin = QSpinBox()
        self.lap2_spin.setMinimum(1)
        self.lap2_spin.setMaximum(100)
        self.lap2_spin.setValue(1)
        lap2_layout.addWidget(self.lap2_spin)
        
        driver2_layout.addLayout(driver2_info_layout)
        driver2_layout.addLayout(lap2_layout)
        driver_layout.addWidget(self.driver2_container)
        
        # 初始隱藏車手2控制
        self.driver2_container.setVisible(False)
        
        layout.addWidget(driver_group)
        
        # 分析控制組
        analysis_group = QGroupBox("分析控制")
        analysis_layout = QVBoxLayout(analysis_group)
        
        # 載入按鈕
        self.load_button = QPushButton("🔄 載入數據")
        self.load_button.clicked.connect(self.load_data)
        analysis_layout.addWidget(self.load_button)
        
        # 清除按鈕
        self.clear_button = QPushButton("🗑️ 清除")
        self.clear_button.clicked.connect(self.clear_data)
        self.clear_button.setEnabled(False)
        analysis_layout.addWidget(self.clear_button)
        
        layout.addWidget(analysis_group)
        
        layout.addStretch()
        
        return layout
    
    def create_chart_section(self) -> QVBoxLayout:
        """創建圖表區域"""
        layout = QVBoxLayout()
        
        # 創建圖表 widget
        self.chart_widget = ThrottleAnalysisChartWidget()
        layout.addWidget(self.chart_widget)
        
        print("[THROTTLE_MODULE] 圖表組件創建完成")
        
        return layout
    
    def setup_data_loader(self):
        """設置數據載入器"""
        self.data_loader = ThrottleAnalysisDataLoader()
        
        # 連接信號
        self.data_loader.data_loaded.connect(self.on_data_loaded)
        self.data_loader.load_error.connect(self.on_load_error)
        self.data_loader.status_changed.connect(self.on_status_changed)
        self.data_loader.load_progress.connect(self.on_load_progress)
        
        print("[THROTTLE_MODULE] 數據載入器設置完成")
    
    def connect_global_signals(self):
        """連接全域信號"""
        if self.global_signals:
            # 監聽會話更新信號
            if hasattr(self.global_signals, 'session_updated'):
                self.global_signals.session_updated.connect(self.on_session_updated)
            
            # 監聽車手列表更新信號
            if hasattr(self.global_signals, 'drivers_updated'):
                self.global_signals.drivers_updated.connect(self.on_drivers_updated)
            
            print("[THROTTLE_MODULE] 全域信號連接完成")
    
    def on_comparison_mode_changed(self, state):
        """對比模式變更處理"""
        is_comparison = state == Qt.Checked
        self.driver2_container.setVisible(is_comparison)
        
        print(f"[THROTTLE_MODULE] 對比模式: {'啟用' if is_comparison else '停用'}")
    
    def load_data(self):
        """載入油門數據"""
        try:
            # 檢查車手選擇
            driver1 = self.driver1_combo.currentText()
            if not driver1:
                QMessageBox.warning(self, "警告", "請選擇車手1")
                return
            
            # 構建會話信息
            session_info = {
                'driver1': driver1,
                'lap1': self.lap1_spin.value(),
                'is_fastest_lap': False
            }
            
            # 檢查對比模式
            if self.comparison_checkbox.isChecked():
                driver2 = self.driver2_combo.currentText()
                if not driver2:
                    QMessageBox.warning(self, "警告", "請選擇車手2")
                    return
                session_info['driver2'] = driver2
                session_info['lap2'] = self.lap2_spin.value()
            else:
                session_info['driver2'] = None
                session_info['lap2'] = None
            
            # 從全域信號獲取會話資訊
            if self.global_signals and hasattr(self.global_signals, 'get_current_session'):
                current_session = self.global_signals.get_current_session()
                if current_session:
                    session_info.update({
                        'year': current_session.get('year', 2025),
                        'race': current_session.get('race', 'Japan'),  # 預設值
                        'session': current_session.get('session', 'R')
                    })
            else:
                # 如果沒有全域信號，使用預設值
                session_info.update({
                    'year': 2025,
                    'race': 'Japan',  # 預設值
                    'session': 'R'
                })
            
            print(f"[THROTTLE_MODULE] 開始載入數據: {session_info}")
            
            # 開始載入
            self.analysis_started.emit()
            self.load_button.setEnabled(False)
            self.data_loader.load_throttle_analysis_data(session_info)
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MODULE] 載入數據失敗: {e}")
            self.error_occurred.emit(f"載入數據失敗: {str(e)}")
    
    def clear_data(self):
        """清除數據"""
        try:
            if self.chart_widget:
                self.chart_widget.clear_chart()
            
            self.current_data = None
            self.clear_button.setEnabled(False)
            self.status_label.setText("已清除")
            
            print("[THROTTLE_MODULE] 數據已清除")
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MODULE] 清除數據失敗: {e}")
    
    def on_data_loaded(self, data):
        """數據載入完成處理"""
        try:
            print(f"[THROTTLE_MODULE] 數據載入完成")
            
            self.current_data = data
            
            # 更新圖表
            if self.chart_widget:
                self.chart_widget.update_throttle_data(data)
            
            # 更新UI狀態
            self.load_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            self.status_label.setText("數據載入完成")
            
            # 發送完成信號
            self.analysis_completed.emit()
            self.data_loaded.emit(data)
            
            print("[THROTTLE_MODULE] 油門分析數據處理完成")
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MODULE] 數據處理失敗: {e}")
            self.on_load_error(f"數據處理失敗: {str(e)}")
    
    def on_load_error(self, error_msg):
        """載入錯誤處理"""
        print(f"[ERROR] [THROTTLE_MODULE] {error_msg}")
        
        self.load_button.setEnabled(True)
        self.status_label.setText(f"錯誤: {error_msg}")
        
        # 顯示錯誤訊息
        QMessageBox.critical(self, "載入錯誤", error_msg)
        
        self.error_occurred.emit(error_msg)
    
    def on_status_changed(self, status):
        """狀態變更處理"""
        self.status_label.setText(status)
        print(f"[THROTTLE_MODULE] 狀態: {status}")
    
    def on_load_progress(self, progress):
        """載入進度處理"""
        self.status_label.setText(f"載入中... {progress}%")
    
    def on_session_updated(self, session_info):
        """會話更新處理"""
        print(f"[THROTTLE_MODULE] 會話更新: {session_info}")
        # 這裡可以根據新的會話資訊更新UI
    
    def on_drivers_updated(self, drivers):
        """車手列表更新處理"""
        print(f"[THROTTLE_MODULE] 車手列表更新: {drivers}")
        
        # 更新車手下拉選單
        self.driver1_combo.clear()
        self.driver2_combo.clear()
        
        for driver in drivers:
            self.driver1_combo.addItem(driver)
            self.driver2_combo.addItem(driver)
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前數據"""
        return self.current_data
    
    def update_drivers(self, drivers: List[str]):
        """更新車手列表"""
        self.on_drivers_updated(drivers)
    
    def update_session(self, session_info: Dict[str, Any]):
        """更新會話信息"""
        self.on_session_updated(session_info)


# 測試程式
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建測試數據
    test_drivers = ['VER', 'HAM', 'LEC', 'NOR', 'SAI']
    
    # 創建模組
    module = ThrottleAnalysisModule()
    module.update_drivers(test_drivers)
    module.show()
    
    print("[TEST] 油門分析模組測試啟動")
    
    sys.exit(app.exec_())
