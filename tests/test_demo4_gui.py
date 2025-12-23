#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo 4 分類功能快速測試啟動器
僅啟動 Demo 4 視窗，測試分類篩選功能
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
from modules.gui.classification_analysis.demo_4_detailed_table import ClassificationDetailedTableWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 4 分類功能測試")
        self.setGeometry(100, 100, 1400, 800)
        
        # 創建 MDI 區域
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        
        # 創建 Demo 4 視窗
        self.create_demo4_window()
    
    def create_demo4_window(self):
        """創建 Demo 4 視窗"""
        api_base_url = "http://localhost:8000"  # 本地 API
        year = 2025
        
        demo4_widget = ClassificationDetailedTableWidget(api_base_url, year)
        
        sub_window = QMdiSubWindow()
        sub_window.setWidget(demo4_widget)
        sub_window.setWindowTitle(f"Demo 4: 2025 Parts Changes (分類視圖)")
        
        self.mdi_area.addSubWindow(sub_window)
        sub_window.showMaximized()

if __name__ == "__main__":
    print("🚀 啟動 Demo 4 分類功能測試視窗...")
    print()
    print("測試項目:")
    print("  1. 數據載入（優先使用 classified_with_categories.json）")
    print("  2. 主分類篩選器（15 個主分類）")
    print("  3. 子分類篩選器（動態更新）")
    print("  4. 表格顯示主分類和子分類欄位")
    print("  5. 組合篩選功能")
    print()
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("✅ 視窗已啟動，請測試以下功能:")
    print("  • 檢查表格是否有「主分類」和「子分類」欄位")
    print("  • 測試主分類下拉選單（應有 15 個選項）")
    print("  • 測試子分類下拉選單（選擇主分類後動態更新）")
    print("  • 測試組合篩選（賽事 + 車隊 + 主分類）")
    print("  • 測試搜尋功能（關鍵字包含分類名稱）")
    print()
    
    sys.exit(app.exec_())
