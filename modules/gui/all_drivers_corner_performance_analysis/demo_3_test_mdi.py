#!/usr/bin/env python3
"""
Demo 3: 測試 MDI 視窗
Test Corner Performance MDI Window

測試項目：
1. 創建 MDI 視窗
2. 初始化模組
3. 載入數據
4. 顯示完整分析介面

執行命令：
python demo_3_test_mdi.py
"""

import sys
import os

# 設定路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
from PyQt5.QtCore import Qt
from modules.gui.all_drivers_corner_performance_analysis.all_drivers_corner_performance_mdi import (
    AllDriversCornerPerformanceMDI,
    create_mdi_window
)


class Demo3MainWindow(QMainWindow):
    """Demo 3 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 3: 彎道性能 MDI 測試")
        self.setGeometry(50, 50, 1600, 1200)
        
        # 創建 MDI 區域
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        
        # 創建 MDI 視窗
        self.create_corner_performance_mdi()
    
    def create_corner_performance_mdi(self):
        """創建彎道性能 MDI 視窗"""
        print("\n創建彎道性能 MDI 視窗...")
        
        # 使用工廠函數創建
        mdi_widget = create_mdi_window(
            parent=self,
            year=2024,
            race="Japan",
            session="R"
        )
        
        if not mdi_widget:
            print("❌ MDI 視窗創建失敗")
            return
        
        # 包裝成 MDI 子視窗
        sub_window = QMdiSubWindow()
        sub_window.setWidget(mdi_widget)
        sub_window.setWindowTitle("全車手彎道性能分析 - Japan 2024 R")
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        
        # 添加到 MDI 區域
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
        print("✅ MDI 視窗創建成功")


def main():
    print("=" * 60)
    print("Demo 3: 測試彎道性能 MDI 視窗")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    window = Demo3MainWindow()
    window.show()
    
    print("\n✅ Demo 3 啟動完成")
    print("提示: 請在 GUI 中切換不同的彎道類型查看效果")
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
