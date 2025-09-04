#!/usr/bin/env python3
"""
通用遙測圖表組件使用範例
展示如何使用統一的 UniversalTelemetryChartWidget 來處理不同類型的遙測數據
"""

import sys
import os
from typing import List
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QComboBox, QLabel
from PyQt5.QtCore import Qt

# 導入通用圖表組件
from universal_telemetry_chart_widget import (
    UniversalTelemetryChartWidget, 
    SpeedChartWidget, 
    RPMChartWidget,
    BrakeChartWidget,
    ThrottleChartWidget
)

class TelemetryChartDemo(QMainWindow):
    """遙測圖表展示範例"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("通用遙測圖表組件展示")
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建主要部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 控制面板
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # 圖表容器
        chart_layout = QHBoxLayout()
        layout.addLayout(chart_layout)
        
        # 創建不同類型的圖表
        self.speed_chart = UniversalTelemetryChartWidget('speed')
        self.rpm_chart = UniversalTelemetryChartWidget('rpm')
        
        chart_layout.addWidget(self.speed_chart)
        chart_layout.addWidget(self.rpm_chart)
        
        # 載入範例數據
        self._load_sample_data()
    
    def _create_control_panel(self) -> QWidget:
        """創建控制面板"""
        panel = QWidget()
        panel.setMaximumHeight(60)
        layout = QHBoxLayout(panel)
        
        # 圖表類型選擇器
        layout.addWidget(QLabel("左側圖表:"))
        self.left_chart_combo = QComboBox()
        self.left_chart_combo.addItems(['speed', 'rpm', 'brake', 'throttle', 'steering'])
        self.left_chart_combo.currentTextChanged.connect(self._on_left_chart_changed)
        layout.addWidget(self.left_chart_combo)
        
        layout.addWidget(QLabel("右側圖表:"))
        self.right_chart_combo = QComboBox()
        self.right_chart_combo.addItems(['speed', 'rpm', 'brake', 'throttle', 'steering'])
        self.right_chart_combo.setCurrentText('rpm')
        self.right_chart_combo.currentTextChanged.connect(self._on_right_chart_changed)
        layout.addWidget(self.right_chart_combo)
        
        # 重載數據按鈕
        reload_btn = QPushButton("重載範例數據")
        reload_btn.clicked.connect(self._load_sample_data)
        layout.addWidget(reload_btn)
        
        layout.addStretch()
        
        return panel
    
    def _on_left_chart_changed(self, chart_type: str):
        """左側圖表類型改變"""
        # 移除舊圖表
        layout = self.centralWidget().layout().itemAt(1).layout()
        old_chart = layout.itemAt(0).widget()
        layout.removeWidget(old_chart)
        old_chart.deleteLater()
        
        # 創建新圖表
        self.speed_chart = UniversalTelemetryChartWidget(chart_type)
        layout.insertWidget(0, self.speed_chart)
        
        # 重載數據
        self._load_sample_data()
    
    def _on_right_chart_changed(self, chart_type: str):
        """右側圖表類型改變"""
        # 移除舊圖表
        layout = self.centralWidget().layout().itemAt(1).layout()
        old_chart = layout.itemAt(1).widget()
        layout.removeWidget(old_chart)
        old_chart.deleteLater()
        
        # 創建新圖表
        self.rpm_chart = UniversalTelemetryChartWidget(chart_type)
        layout.insertWidget(1, self.rpm_chart)
        
        # 重載數據
        self._load_sample_data()
    
    def _load_sample_data(self):
        """載入範例數據"""
        print("載入範例遙測數據...")
        
        # 生成範例距離數據 (0-5000米的賽道)
        import numpy as np
        distance = list(np.linspace(0, 5000, 500))
        
        # 根據圖表類型生成對應的範例數據
        left_type = self.left_chart_combo.currentText()
        right_type = self.right_chart_combo.currentText()
        
        # 生成左側圖表數據
        driver1_left, driver2_left = self._generate_sample_data(left_type, distance)
        self.speed_chart.set_telemetry_data(
            distance, driver1_left, driver2_left,
            "VER", "LEC",
            self._generate_sample_sectors()
        )
        
        # 生成右側圖表數據
        driver1_right, driver2_right = self._generate_sample_data(right_type, distance)
        self.rpm_chart.set_telemetry_data(
            distance, driver1_right, driver2_right,
            "VER", "LEC",
            self._generate_sample_sectors()
        )
        
        print(f"已載入 {left_type} 和 {right_type} 數據")
    
    def _generate_sample_data(self, data_type: str, distance: List[float]):
        """根據數據類型生成範例數據"""
        import numpy as np
        import math
        
        # 基礎變化模式 (模擬賽道特性)
        base_pattern = np.array([
            math.sin(d / 1000) * 0.3 + math.cos(d / 500) * 0.2 + 0.5 
            for d in distance
        ])
        
        if data_type == 'speed':
            # 速度: 100-320 km/h
            driver1 = 100 + base_pattern * 220 + np.random.normal(0, 5, len(distance))
            driver2 = 95 + base_pattern * 225 + np.random.normal(0, 5, len(distance))
            
        elif data_type == 'rpm':
            # RPM: 8000-11500
            driver1 = 8000 + base_pattern * 3500 + np.random.normal(0, 100, len(distance))
            driver2 = 7800 + base_pattern * 3700 + np.random.normal(0, 100, len(distance))
            
        elif data_type == 'brake':
            # 煞車: 0-100%，大部分時間為0
            brake_zones = np.zeros_like(base_pattern)
            # 在特定區域設置煞車點
            for i in range(0, len(distance), 50):
                if base_pattern[i] < 0.3:  # 模擬彎道前煞車
                    brake_zones[i:min(i+10, len(distance))] = 80 + np.random.normal(0, 10, min(10, len(distance)-i))
            driver1 = np.maximum(0, brake_zones + np.random.normal(0, 5, len(distance)))
            driver2 = np.maximum(0, brake_zones + np.random.normal(0, 5, len(distance)))
            
        elif data_type == 'throttle':
            # 油門: 0-100%
            driver1 = np.maximum(0, 30 + base_pattern * 70 + np.random.normal(0, 10, len(distance)))
            driver2 = np.maximum(0, 25 + base_pattern * 75 + np.random.normal(0, 10, len(distance)))
            
        elif data_type == 'steering':
            # 轉向: -100° to +100°
            steering_pattern = np.array([
                math.sin(d / 800) * 60 + math.cos(d / 300) * 30
                for d in distance
            ])
            driver1 = steering_pattern + np.random.normal(0, 5, len(distance))
            driver2 = steering_pattern + np.random.normal(0, 5, len(distance))
            
        else:
            # 預設數據
            driver1 = base_pattern * 100 + np.random.normal(0, 5, len(distance))
            driver2 = base_pattern * 100 + np.random.normal(0, 5, len(distance))
        
        return driver1.tolist(), driver2.tolist()
    
    def _generate_sample_sectors(self):
        """生成範例分段數據"""
        return [
            {'sector': 1, 'end_distance': 1667},
            {'sector': 2, 'end_distance': 3333},
            {'sector': 3, 'end_distance': 5000}
        ]

def main():
    """主函數"""
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyle('Fusion')
    
    # 創建主視窗
    window = TelemetryChartDemo()
    window.show()
    
    # 運行應用程式
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
