#!/usr/bin/env python3
"""
F101 起跑反應分析 GUI 測試

測試 StartReactionAnalysisMDI 視窗能否正常載入並顯示 Abu Dhabi 2025 數據
"""

import sys
import os

# 設定工作目錄
os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
from PyQt5.QtCore import Qt

# 導入 F101 模組
from modules.gui.race_analysis.start_reaction import StartReactionAnalysisMDI

def main():
    app = QApplication(sys.argv)
    
    # 創建主視窗
    main_window = QMainWindow()
    main_window.setWindowTitle("F101 Start Reaction Analysis Test")
    main_window.resize(1600, 900)
    
    # 創建 MDI 區域
    mdi_area = QMdiArea()
    main_window.setCentralWidget(mdi_area)
    
    # 創建 F101 分析視窗
    print("[TEST] Creating StartReactionAnalysisMDI...")
    analysis_module = StartReactionAnalysisMDI()
    
    # 設置必要的屬性（模擬主程式的行為）
    analysis_module.current_year = 2025
    analysis_module.current_race = "Abu_Dhabi"
    analysis_module.current_session = "R"
    
    # 初始化模組（這會創建 main_widget 並載入數據）
    print("[TEST] Initializing module with Abu Dhabi 2025 data...")
    success = analysis_module.initialize_module()
    if success:
        print("[TEST] Module initialized successfully!")
    else:
        print("[TEST] Module initialization failed!")
        return
    
    # 獲取實際的 QWidget 來放入 MDI
    widget = analysis_module.get_widget()
    if not widget:
        print("[TEST] ERROR: get_widget() returned None!")
        return
    
    # 創建子視窗
    sub_window = QMdiSubWindow()
    sub_window.setWidget(widget)
    sub_window.setWindowTitle("F101 起跑反應分析 - Abu Dhabi 2025")
    sub_window.resize(1400, 800)
    
    # 添加到 MDI 區域
    mdi_area.addSubWindow(sub_window)
    sub_window.show()
    
    main_window.show()
    
    print("[TEST] GUI is running. Close the window to exit.")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
