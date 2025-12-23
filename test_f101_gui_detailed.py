#!/usr/bin/env python3
"""
F101 起跑反應分析 GUI 測試 - 詳細輸出版本
"""

import sys
import os

os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

print("=" * 60)
print("F101 GUI Test - Detailed")
print("=" * 60)

try:
    print("\n[1] PyQt5 imports...")
    from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
    from PyQt5.QtCore import Qt
    print("    OK")
    
    print("\n[2] Import StartReactionAnalysisMDI...")
    from modules.gui.race_analysis.start_reaction import StartReactionAnalysisMDI
    print("    OK")
    
    print("\n[3] Create QApplication...")
    app = QApplication(sys.argv)
    print("    OK")
    
    print("\n[4] Create main window...")
    main_window = QMainWindow()
    main_window.setWindowTitle("F101 Start Reaction Analysis Test")
    main_window.resize(1600, 900)
    print("    OK")
    
    print("\n[5] Create MDI area...")
    mdi_area = QMdiArea()
    main_window.setCentralWidget(mdi_area)
    print("    OK")
    
    print("\n[6] Create StartReactionAnalysisMDI...")
    analysis_module = StartReactionAnalysisMDI()
    print("    OK")
    
    print("\n[7] Set parameters...")
    analysis_module.current_year = 2025
    analysis_module.current_race = "Abu_Dhabi"
    analysis_module.current_session = "R"
    print("    OK")
    
    print("\n[8] Initialize module...")
    success = analysis_module.initialize_module()
    print(f"    Result: {success}")
    
    if not success:
        print("    ERROR: Module initialization failed!")
        sys.exit(1)
    
    print("\n[9] Get widget...")
    widget = analysis_module.get_widget()
    print(f"    Widget: {widget}")
    
    if not widget:
        print("    ERROR: get_widget() returned None!")
        sys.exit(1)
    
    print("\n[10] Create MDI sub-window...")
    sub_window = QMdiSubWindow()
    sub_window.setWidget(widget)
    sub_window.setWindowTitle("F101 起跑反應分析 - Abu Dhabi 2025")
    sub_window.resize(1400, 800)
    print("    OK")
    
    print("\n[11] Add to MDI area...")
    mdi_area.addSubWindow(sub_window)
    sub_window.show()
    print("    OK")
    
    print("\n[12] Show main window...")
    main_window.show()
    print("    OK")
    
    print("\n" + "=" * 60)
    print("GUI is running. Close the window to exit.")
    print("=" * 60)
    
    sys.exit(app.exec_())
    
except Exception as e:
    print(f"\n ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
