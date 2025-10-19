#!/usr/bin/env python3
"""
Demo 4: 2024 日本大獎賽正賽 (Japan R)
測試正賽數據的直線速度與加速性能分析

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
    print("Demo 4: 2024 日本大獎賽正賽 (Japan R)")
    print("測試正賽數據")
    print("=" * 80)
    
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("Demo 4: 全車手直線速度分析 - 2024 Japan R")
    main_window.setGeometry(100, 100, 1400, 1000)
    
    mdi_area = QMdiArea()
    main_window.setCentralWidget(mdi_area)
    
    module = AllDriversStraightLineSpeedModule(parent=None, year=2024, race="Japan", session="R")
    
    if not module.initialize_module():
        print("[DEMO4] ❌ 模組初始化失敗")
        return 1
    
    widget = module.get_widget()
    if not widget:
        print("[DEMO4] ❌ 無法獲取 Widget")
        return 1
    
    sub_window = QMdiSubWindow()
    sub_window.setWidget(widget)
    sub_window.setWindowTitle("2024 Japan R - 直線速度與加速性能")
    mdi_area.addSubWindow(sub_window)
    sub_window.showMaximized()
    
    main_window.show()
    print("✅ [DEMO4] GUI 已啟動 (Japan Race)")
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
