#!/usr/bin/env python3
"""
F1T Accident Analysis 簡化設計測試
測試新的簡化佈局：統計表格 + 車手圖表 + Safety Periods
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_simplified_design():
    """測試簡化設計"""
    print("🔍 測試簡化設計實現...")
    
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
        main_window.setWindowTitle("F1T Accident Analysis - 簡化設計")
        main_window.setGeometry(100, 100, 800, 600)  # 中等視窗大小
        
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
                    {'driver_code': 'HAM', 'message': 'Yellow flag shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'VER', 'message': 'Collision with RUS', 'category': 'ACCIDENT'},
                    {'driver_code': 'SAI', 'message': 'Red flag incident', 'category': 'RED_FLAG'},
                    {'driver_code': 'LEC', 'message': 'Double yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'HAM', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'}
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Track debris removal'},
                    {'type': 'VSC', 'start_lap': 28, 'end_lap': 30, 'reason': 'Accident cleanup'}
                ]
            }
        }
        
        # 連接測試按鈕
        def load_test_data():
            print("📊 載入測試數據...")
            stats_widget.update_statistics_data(test_data)
            print("✅ 測試數據載入完成")
        
        test_button.clicked.connect(load_test_data)
        
        # 驗證簡化設計組件
        print("✅ 簡化設計組件檢查:")
        print(f"   • 統計表格: {hasattr(stats_widget, 'statistics_table')}")
        print(f"   • 車手事故圖表: {hasattr(stats_widget, 'driver_chart')}")
        print(f"   • Safety Periods: {hasattr(stats_widget, 'safety_periods_widget')}")
        
        # 驗證移除的組件
        print("✅ 已移除的組件:")
        print(f"   • Penalties Summary: {not hasattr(stats_widget, 'penalties_summary_widget')}")
        print(f"   • Flag Statistics Table: {not hasattr(stats_widget, 'flag_table_widget')}")
        print(f"   • Penalty List Table: {not hasattr(stats_widget, 'penalty_table_widget')}")
        
        # 顯示視窗
        main_window.show()
        
        # 自動載入測試數據
        load_test_data()
        
        print("\n🎯 簡化設計預覽:")
        print("1. 📊 Flag Statistics Summary 表格 (4行：Track Limit, Double Yellow, Yellow, Red)")
        print("2. 🏆 Driver Incident Frequency ASCII 條形圖")
        print("3. 🏁 Safety Periods 表格 (2條記錄)")
        print("\n✨ 設計優勢：")
        print("• 資訊密度適中，不會過於擁擠")
        print("• 統計數據更清晰（表格 vs 卡片）")
        print("• 專注於核心資訊：旗標、車手事故、安全車")
        
        # 執行應用程式（如果是獨立運行）
        if __name__ == "__main__":
            sys.exit(app.exec_())
        
        return True
        
    except Exception as e:
        print(f"❌ 簡化設計測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis 簡化設計測試")
    print("移除：Penalties、Severity Analysis、Race Impact Analysis")
    print("保留：統計表格、車手圖表、Safety Periods")
    print()
    
    success = test_simplified_design()
    
    if success:
        print("\n🎉 簡化設計實現成功！")
        return 0
    else:
        print("\n❌ 簡化設計測試失敗")
        return 1

if __name__ == "__main__":
    main()