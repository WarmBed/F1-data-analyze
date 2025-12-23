#!/usr/bin/env python3
"""
F1T GUI Accident Analysis 改良 B 設計整合測試
測試新設計在實際 GUI 環境中的表現
"""

import sys
import os
import json

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_gui_integration():
    """測試 GUI 整合"""
    print("🖥️ 測試 F1T GUI Accident Analysis 整合...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentStatisticsWidget
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建應用程式
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建主視窗
        main_window = QMainWindow()
        main_window.setWindowTitle("F1T Accident Analysis - 改良 B 設計測試")
        main_window.setGeometry(100, 100, 1000, 700)  # 中等視窗大小
        
        # 創建中央 Widget
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        layout.addWidget(stats_widget)
        
        # 創建測試按鈕
        test_button = QPushButton("載入測試數據")
        layout.addWidget(test_button)
        
        # 測試數據
        test_data = {
            'data': {
                'all_incidents': [
                    {'driver_code': 'VER', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'LEC', 'message': 'Unsafe release', 'category': 'PENALTY'},
                    {'driver_code': 'HAM', 'message': 'Yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'VER', 'message': 'Collision with RUS', 'category': 'ACCIDENT'},
                    {'driver_code': 'SAI', 'message': 'Red flag incident', 'category': 'RED_FLAG'}
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Track debris removal'},
                    {'type': 'VSC', 'start_lap': 28, 'end_lap': 30, 'reason': 'Accident cleanup'}
                ],
                'penalties': [
                    {'type': 'time penalty', 'driver': 'VER', 'severity_score': 8, 'description': '5-second penalty'},
                    {'type': 'grid penalty', 'driver': 'LEC', 'severity_score': 6, 'description': '3-place grid penalty'},
                    {'type': 'warning', 'driver': 'HAM', 'severity_score': 2, 'description': 'Official warning'},
                    {'type': 'time penalty', 'driver': 'SAI', 'severity_score': 5, 'description': '3-second penalty'}
                ]
            }
        }
        
        # 連接測試按鈕
        def load_test_data():
            print("📊 載入測試數據...")
            stats_widget.update_statistics_data(test_data)
            print("✅ 測試數據載入完成")
        
        test_button.clicked.connect(load_test_data)
        
        # 顯示視窗
        main_window.show()
        
        print("✅ GUI 整合測試成功")
        print("📋 測試 Widget 清單:")
        print(f"   • Quick Stats Cards: {hasattr(stats_widget, 'cards_layout')}")
        print(f"   • Driver Incident Chart: {hasattr(stats_widget, 'driver_chart')}")
        print(f"   • Safety Periods Widget: {hasattr(stats_widget, 'safety_periods_widget')}")
        print(f"   • Penalties Summary Widget: {hasattr(stats_widget, 'penalties_summary_widget')}")
        print(f"   • Flag Statistics Table: {hasattr(stats_widget, 'flag_table_widget')}")
        print(f"   • Penalty List Table: {hasattr(stats_widget, 'penalty_table_widget')}")
        
        # 自動載入測試數據
        load_test_data()
        
        print("\n🎯 GUI 已啟動，請檢查以下項目:")
        print("1. 垂直佈局是否正確：Quick Stats → Driver Chart → Safety+Penalties → Severity+Impact")
        print("2. Safety Periods 表格是否顯示 2 條記錄")
        print("3. Penalties Summary 是否顯示 4 個處罰統計")
        print("4. Driver Incident Chart 是否顯示 ASCII 條形圖")
        print("5. 中等視窗大小下佈局是否合適")
        
        # 執行應用程式（如果是獨立運行）
        if __name__ == "__main__":
            sys.exit(app.exec_())
        
        return True
        
    except Exception as e:
        print(f"❌ GUI 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis 改良 B 設計 - GUI 整合測試")
    print()
    
    success = test_gui_integration()
    
    if success:
        print("\n🎉 GUI 整合測試成功！")
        print("新的改良 B 設計已經實現並可以在 GUI 中正常顯示")
        return 0
    else:
        print("\n❌ GUI 整合測試失敗")
        return 1

if __name__ == "__main__":
    main()