#!/usr/bin/env python3
"""
測試 SpeedLegendWidget 的顯示效果
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QCheckBox, QVBoxLayout
from PyQt5.QtCore import Qt

# 導入 SpeedLegendWidget
from modules.gui.Historical_track_map.historical_track_map_mdi import SpeedLegendWidget


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speed Legend Widget Test")
        self.resize(300, 600)
        
        # 主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 控制 Checkbox
        self.checkbox = QCheckBox("Show Speed Legend")
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self._toggle_legend)
        layout.addWidget(self.checkbox)
        
        # 圖例容器
        legend_container = QWidget()
        legend_layout = QHBoxLayout(legend_container)
        legend_layout.setContentsMargins(50, 50, 50, 50)
        
        # SpeedLegendWidget
        self.legend = SpeedLegendWidget()
        self.legend.set_speed_range(120.5, 342.8)
        legend_layout.addWidget(self.legend)
        
        layout.addWidget(legend_container, stretch=1)
        
        print("Test Window initialized")
        print(f"Speed range: 120.5 - 342.8 km/h")
    
    def _toggle_legend(self, state):
        self.legend.setVisible(state == Qt.Checked)
        print(f"Legend visible: {state == Qt.Checked}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
