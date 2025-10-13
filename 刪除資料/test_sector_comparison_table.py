#!/usr/bin/env python3
"""
測試 Sector Comparison 表格版本
"""

import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_table_widget import (
    IdealLapSectorComparisonTableWidget
)


def main():
    app = QApplication(sys.argv)
    
    # 創建主視窗
    window = QMainWindow()
    window.setWindowTitle("Sector Comparison Table Demo")
    window.resize(1000, 600)
    
    # 創建中央 widget
    central = QWidget()
    layout = QVBoxLayout(central)
    
    # 創建表格
    table_widget = IdealLapSectorComparisonTableWidget()
    layout.addWidget(table_widget)
    
    window.setCentralWidget(central)
    
    # 載入測試數據
    try:
        with open('json/ideal_lap_ranking_2025_Australia_R.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ 載入 Australia 數據成功")
        print(f"   車手數量: {len(data['analysis_result']['ranking'])}")
        
        # 更新表格
        table_widget.update_data(data)
        print("✅ 表格更新成功")
        
    except Exception as e:
        print(f"❌ 載入數據失敗: {e}")
        import traceback
        traceback.print_exc()
    
    # 顯示視窗
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
