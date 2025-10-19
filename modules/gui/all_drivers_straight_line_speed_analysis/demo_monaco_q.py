#!/usr/bin/env python3
"""
Demo 3: 2024 摩納哥大獎賽排位賽 (Monaco Q)
測試低速街道賽道的直線速度與加速性能分析

作者: F1T Team
日期: 2025-10-14
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
from modules.gui.all_drivers_straight_line_speed_analysis import AllDriversStraightLineSpeedModule


def main():
    print("=" * 80)
    print("Demo 3: 2024 摩納哥大獎賽排位賽 (Monaco Q)")
    print("測試低速街道賽道數據")
    print("=" * 80)
    
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("Demo 3: 全車手直線速度分析 - 2024 Monaco Q")
    main_window.setGeometry(100, 100, 1400, 1000)
    
    mdi_area = QMdiArea()
    main_window.setCentralWidget(mdi_area)
    
    module = AllDriversStraightLineSpeedModule(parent=None, year=2024, race="Monaco", session="Q")
    
    if not module.initialize_module():
        print("[DEMO3] ❌ 模組初始化失敗")
        return 1
    
    widget = module.get_widget()
    if not widget:
        print("[DEMO3] ❌ 無法獲取 Widget")
        return 1
    
    sub_window = QMdiSubWindow()
    sub_window.setWidget(widget)
    sub_window.setWindowTitle("2024 Monaco Q - 直線速度與加速性能")
    mdi_area.addSubWindow(sub_window)
    sub_window.showMaximized()
    
    main_window.show()
    print("✅ [DEMO3] GUI 已啟動 (Monaco - 低速街道賽)")
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
