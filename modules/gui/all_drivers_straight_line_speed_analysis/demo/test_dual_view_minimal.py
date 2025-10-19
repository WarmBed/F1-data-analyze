#!/usr/bin/env python3
"""
測試雙視圖容器 - 最小化測試
"""

import sys
from pathlib import Path

# 添加專案根目錄
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer

# 導入雙視圖容器
from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_dual_view import (
    AllDriversStraightLineSpeedDualView
)

def main():
    """主程式"""
    app = QApplication(sys.argv)
    
    print("🧪 測試雙視圖容器初始化...")
    
    # 創建主視窗
    main_window = QMainWindow()
    main_window.setWindowTitle("雙視圖測試 - 最小化")
    main_window.resize(1200, 800)
    
    # 創建中央 Widget
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    main_window.setCentralWidget(central_widget)
    
    print("✅ 主視窗創建完成")
    
    # 創建雙視圖容器
    print("📦 創建雙視圖容器...")
    dual_view = AllDriversStraightLineSpeedDualView()
    layout.addWidget(dual_view)
    print("✅ 雙視圖容器創建完成")
    
    # 顯示視窗
    main_window.show()
    print("✅ 視窗已顯示")
    
    # 5 秒後自動關閉
    QTimer.singleShot(5000, app.quit)
    print("⏰ 5 秒後自動關閉...")
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
