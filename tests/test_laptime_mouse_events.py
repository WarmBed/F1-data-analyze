"""
測試 Lap Time Box Plot Widget 的滑鼠事件
直接測試 Widget 本身，排除 MDI/佈局問題
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_chart_widget import LapTimeBoxPlotChartWidget

# 測試數據
test_data = {
    'driver_laptimes': {
        'VER': [86.5, 87.2, 86.8, 87.0, 86.9],
        'LEC': [87.1, 87.5, 87.3, 87.2, 87.4],
        'HAM': [87.8, 88.0, 87.9, 88.1, 87.7]
    },
    'statistics': {
        'VER': {'median': 86.9, 'mean': 86.88, 'q1': 86.65, 'q3': 87.05, 'iqr': 0.40, 'count': 5},
        'LEC': {'median': 87.3, 'mean': 87.3, 'q1': 87.15, 'q3': 87.45, 'iqr': 0.30, 'count': 5},
        'HAM': {'median': 87.9, 'mean': 87.9, 'q1': 87.75, 'q3': 88.05, 'iqr': 0.30, 'count': 5}
    },
    'metadata': {'year': 2025, 'race': 'Japan', 'session': 'R'}
}

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 Lap Time Box Plot - 滑鼠事件測試")
        self.resize(800, 600)
        
        # 創建主 Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 創建 Chart Widget（直接添加，無任何包裝）
        self.chart_widget = LapTimeBoxPlotChartWidget()
        layout.addWidget(self.chart_widget)
        
        # 載入數據
        self.chart_widget.update_data(test_data)
        
        print("\n" + "="*60)
        print("🧪 測試環境已啟動")
        print("="*60)
        print("✅ Widget 已直接添加到主視窗（無 QFrame、QScrollArea 等包裝）")
        print("✅ 數據已載入（3 位車手）")
        print("\n📋 測試步驟：")
        print("   1. 在箱型圖上按右鍵")
        print("   2. 觀察終端輸出是否有 '🖱️ mousePressEvent 被觸發！'")
        print("   3. 檢查是否彈出選單")
        print("\n" + "="*60)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
