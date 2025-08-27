#!/usr/bin/env python3
"""
測試降雨標記視覺化功能
Test Rain Markers Visualization
"""

import sys
import os
import json

# 添加模組路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from modules.gui.rain_analysis_module import RainAnalysisModule

class TestRainMarkersWindow(QMainWindow):
    """測試降雨標記的主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("測試降雨標記視覺化")
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建中央視窗
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 創建測試按鈕
        test_button = QPushButton("測試 Great Britain 2025 降雨標記")
        test_button.clicked.connect(self.test_rain_markers)
        layout.addWidget(test_button)
        
        # 創建降雨分析模組
        self.rain_module = RainAnalysisModule(
            year=2025,
            race="Great Britain", 
            session="R",
            parent=self
        )
        layout.addWidget(self.rain_module)
    
    def test_rain_markers(self):
        """測試降雨標記功能"""
        print("🧪 開始測試降雨標記視覺化功能...")
        
        # 檢查是否有現有的JSON檔案
        json_path = "json/rain_intensity_2025_British_R_250826.json"
        
        if os.path.exists(json_path):
            print(f"📂 載入現有JSON檔案: {json_path}")
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                print(f"✅ JSON檔案載入成功")
                print(f"📊 數據點總數: {json_data.get('total_data_points', 'N/A')}")
                print(f"🌧️ 降雨數據點: {json_data.get('rain_data_points', 'N/A')}")
                print(f"💧 降雨百分比: {json_data.get('rain_percentage', 'N/A'):.2f}%" if 'rain_percentage' in json_data else "")
                
                # 載入到圖表
                self.rain_module.load_data_to_chart(json_data)
                print("🎨 降雨標記視覺化測試完成")
                
            except Exception as e:
                print(f"❌ JSON檔案載入失敗: {e}")
        else:
            print(f"⚠️ JSON檔案不存在: {json_path}")
            print("🔄 觸發降雨分析以生成數據...")
            # 觸發降雨分析
            self.rain_module.start_rain_analysis()

def main():
    """主函數"""
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyle('Fusion')
    
    # 創建測試視窗
    window = TestRainMarkersWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
