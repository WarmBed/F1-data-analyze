#!/usr/bin/env python3
"""
F101 起跑反應分析 - 簡單 GUI 測試
直接使用 Widget 和 Loader，不經過 MDI
"""

import sys
import os

os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")
sys.path.insert(0, r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt

# 直接導入 widget 和 loader
from modules.gui.race_analysis.start_reaction.start_reaction_widget import StartReactionWidget
from modules.gui.race_analysis.start_reaction.start_reaction_loader import StartReactionDataLoader

def main():
    app = QApplication(sys.argv)
    
    # 創建主視窗
    window = QMainWindow()
    window.setWindowTitle("F101 起跑反應分析 - Abu Dhabi 2025")
    window.resize(1400, 900)
    
    # 創建 Widget
    print("[GUI] Creating StartReactionWidget...")
    widget = StartReactionWidget()
    window.setCentralWidget(widget)
    
    # 載入數據
    print("[GUI] Loading data for Abu Dhabi 2025...")
    loader = StartReactionDataLoader(2025, "Abu_Dhabi", "R")
    data = loader.load_data()
    
    if data:
        print(f"[GUI] Data loaded: {len(data.get('drivers', []))} drivers")
        widget.update_data(data)
    else:
        print("[GUI] ERROR: No data loaded!")
    
    window.show()
    print("[GUI] Window displayed. Close to exit.")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
