#!/usr/bin/env python3
"""
快速測試 PyQt5 高程圖表元件
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from modules.gui.track_elevation.elevation_chart_widget_pyqt5 import ElevationChartWidget

# 測試數據（模擬 Suzuka 賽道的高程數據）
test_track_outline = [
    {"distance_m": 0, "elevation": 542, "z": 542},
    {"distance_m": 500, "elevation": 580, "z": 580},
    {"distance_m": 1000, "elevation": 620, "z": 620},
    {"distance_m": 1500, "elevation": 680, "z": 680},
    {"distance_m": 2000, "elevation": 750, "z": 750},
    {"distance_m": 2500, "elevation": 820, "z": 820},
    {"distance_m": 3000, "elevation": 890, "z": 890},
    {"distance_m": 3500, "elevation": 920, "z": 920},
    {"distance_m": 4000, "elevation": 940, "z": 940},
    {"distance_m": 4500, "elevation": 945, "z": 945},
    {"distance_m": 5000, "elevation": 930, "z": 930},
    {"distance_m": 5500, "elevation": 880, "z": 880},
]

test_corners = [
    {"number": 1, "distance": 1200},
    {"number": 2, "distance": 2300},
    {"number": 3, "distance": 3100},
    {"number": 4, "distance": 4200},
]

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 高程圖表測試")
        self.setGeometry(100, 100, 1200, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 創建高程圖表
        self.elevation_chart = ElevationChartWidget()
        self.elevation_chart.set_circuit_name("Suzuka Test")
        layout.addWidget(self.elevation_chart)
        
        # 載入測試數據
        print("\n測試開始：繪製高程圖表")
        self.elevation_chart.plot_elevation(test_track_outline, test_corners)
        print("測試完成：圖表應該已顯示")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("\n視窗已開啟，請檢查：")
    print("1. 是否顯示高程曲線（藍色填充區域）")
    print("2. 是否顯示彎道標記（紅色圓點 + T1, T2, T3, T4）")
    print("3. 是否顯示網格和座標軸")
    print("4. 滑鼠移動時是否有連動線（需要與其他模組連動）")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
