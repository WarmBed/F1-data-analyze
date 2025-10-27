#!/usr/bin/env python3
"""
Demo 2: 測試散點圖元件
Test Corner Performance Scatter Widget

測試項目：
1. 創建散點圖元件
2. 載入數據
3. 顯示低速彎散點圖
4. 測試彎道切換功能

執行命令：
python demo_2_test_scatter_widget.py
"""

import sys
import os
import json

# 設定路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from modules.gui.all_drivers_corner_performance_analysis.corner_performance_scatter_widget import CornerPerformanceScatterWidget


class Demo2Window(QMainWindow):
    """Demo 2 測試視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 2: 彎道性能散點圖測試")
        self.setGeometry(100, 100, 1400, 1000)
        
        # 創建中心元件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 創建散點圖元件
        self.scatter_widget = CornerPerformanceScatterWidget()
        layout.addWidget(self.scatter_widget)
        
        # 連接信號
        self.scatter_widget.corner_switched.connect(self.on_corner_switched)
        self.scatter_widget.driver_clicked.connect(self.on_driver_clicked)
        
        # 載入數據
        self.load_test_data()
    
    def load_test_data(self):
        """載入測試數據"""
        try:
            json_file = "json/all_drivers_cornering_analysis_2024_Japan_R.json"
            
            if not os.path.exists(json_file):
                print(f"❌ JSON 檔案不存在: {json_file}")
                return
            
            print(f"載入測試數據: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("✅ 數據載入成功")
            print(f"Year: {data.get('year')}")
            print(f"Race: {data.get('race')}")
            print(f"Session: {data.get('session')}")
            
            # 更新圖表
            self.scatter_widget.update_data(data)
            print("✅ 散點圖已更新")
            
        except Exception as e:
            print(f"❌ 載入數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def on_corner_switched(self, corner_type):
        """彎道切換回調"""
        print(f"彎道切換: {corner_type}")
    
    def on_driver_clicked(self, driver):
        """車手點擊回調"""
        print(f"車手點擊: {driver}")


def main():
    print("=" * 60)
    print("Demo 2: 測試彎道性能散點圖元件")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    window = Demo2Window()
    window.show()
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
