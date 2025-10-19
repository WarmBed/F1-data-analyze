#!/usr/bin/env python3
"""
Demo 1: 2024 日本大獎賽排位賽 (Japan Q)
測試全車手直線速度與加速性能分析

作者: F1T Team
日期: 2025-10-14
"""

import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea
from PyQt5.QtCore import Qt

# 導入模組
from modules.gui.all_drivers_straight_line_speed_analysis import AllDriversStraightLineSpeedModule


def main():
    """主程式"""
    print("=" * 80)
    print("Demo 1: 2024 日本大獎賽排位賽 (Japan Q)")
    print("=" * 80)
    
    # 創建 Qt 應用程式
    app = QApplication(sys.argv)
    
    # 創建主視窗
    main_window = QMainWindow()
    main_window.setWindowTitle("Demo 1: 全車手直線速度分析 - 2024 Japan Q")
    main_window.setGeometry(100, 100, 1400, 1000)
    
    # 創建 MDI 區域
    mdi_area = QMdiArea()
    main_window.setCentralWidget(mdi_area)
    
    # 創建分析模組
    print("\n[DEMO1] 創建分析模組...")
    module = AllDriversStraightLineSpeedModule(
        parent=None,
        year=2024,
        race="Japan",
        session="Q"
    )
    
    # 初始化模組
    print("[DEMO1] 初始化模組...")
    if not module.initialize_module():
        print("[DEMO1] ❌ 模組初始化失敗")
        return 1
    
    # 獲取 Widget
    print("[DEMO1] 獲取 Widget...")
    widget = module.get_widget()
    if not widget:
        print("[DEMO1] ❌ 無法獲取 Widget")
        return 1
    
    # 添加到 MDI 區域
    print("[DEMO1] 添加到 MDI 區域...")
    from PyQt5.QtWidgets import QMdiSubWindow
    sub_window = QMdiSubWindow()
    sub_window.setWidget(widget)
    sub_window.setWindowTitle("2024 Japan Q - 直線速度與加速性能")
    mdi_area.addSubWindow(sub_window)
    sub_window.showMaximized()
    
    # 顯示主視窗
    main_window.show()
    
    print("\n✅ [DEMO1] GUI 已啟動")
    print("=" * 80)
    print("測試項目：")
    print("1. 視窗是否正常顯示")
    print("2. 統計面板是否顯示正確資訊")
    print("3. 加速圖表是否正常繪製")
    print("4. 圖表切換功能是否正常")
    print("5. 數據是否正確載入（HUL 最快）")
    print("=" * 80)
    
    # 運行應用程式
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
