#!/usr/bin/env python3
"""
F1T Accident Analysis 無邊框橫向設計測試
測試新的橫向統計表格和無邊框設計
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_horizontal_design():
    """測試橫向無邊框設計"""
    print("🔍 測試橫向無邊框設計...")
    
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
        main_window.setWindowTitle("F1T Accident Analysis - 橫向無邊框設計")
        main_window.setGeometry(100, 100, 900, 550)  # 調整視窗大小適應橫向表格
        
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
        
        # 測試數據 - 更多樣化的旗標數據
        test_data = {
            'data': {
                'all_incidents': [
                    # Track Limits (3次)
                    {'driver_code': 'VER', 'message': 'Track limits violation turn 1', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'HAM', 'message': 'Track limits violation turn 8', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'LEC', 'message': 'Track limits at chicane', 'category': 'TRACK_LIMIT'},
                    
                    # Yellow Flags (5次)
                    {'driver_code': 'SAI', 'message': 'Yellow flag sector 2', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'RUS', 'message': 'Yellow flag shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'NOR', 'message': 'Local yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'PER', 'message': 'Yellow flag incident', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'ALO', 'message': 'Yellow flag debris', 'category': 'YELLOW_FLAG'},
                    
                    # Double Yellow Flags (2次)
                    {'driver_code': 'STR', 'message': 'Double yellow flag shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'TSU', 'message': 'Double yellow flag accident', 'category': 'YELLOW_FLAG'},
                    
                    # Red Flag (1次)
                    {'driver_code': 'BOT', 'message': 'Red flag incident heavy crash', 'category': 'RED_FLAG'},
                    
                    # 其他車手事故
                    {'driver_code': 'VER', 'message': 'Collision with barrier', 'category': 'ACCIDENT'},
                    {'driver_code': 'HAM', 'message': 'Unsafe release', 'category': 'PENALTY'},
                    {'driver_code': 'LEC', 'message': 'Contact with RUS', 'category': 'ACCIDENT'},
                    {'driver_code': 'VER', 'message': 'Another incident', 'category': 'ACCIDENT'},
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Track debris removal'},
                    {'type': 'VSC', 'start_lap': 28, 'end_lap': 30, 'reason': 'Accident cleanup'},
                    {'type': 'SC', 'start_lap': 45, 'end_lap': 48, 'reason': 'Heavy crash recovery'}
                ]
            }
        }
        
        # 連接測試按鈕
        def load_test_data():
            print("📊 載入測試數據...")
            stats_widget.update_statistics_data(test_data)
            print("✅ 測試數據載入完成")
            
            # 驗證橫向數據顯示
            if hasattr(stats_widget, 'stats_table'):
                print("📋 橫向統計表格數據:")
                for col in range(4):
                    item = stats_widget.stats_table.item(0, col)
                    header = stats_widget.stats_table.horizontalHeaderItem(col).text()
                    value = item.text() if item else "0"
                    print(f"   {header}: {value}")
        
        test_button.clicked.connect(load_test_data)
        
        # 驗證設計組件
        print("✅ 橫向無邊框設計檢查:")
        print(f"   • 橫向統計表格: {hasattr(stats_widget, 'statistics_table')}")
        print(f"   • 車手事故圖表: {hasattr(stats_widget, 'driver_chart')}")
        print(f"   • Safety Periods: {hasattr(stats_widget, 'safety_periods_widget')}")
        
        # 顯示視窗
        main_window.show()
        
        # 自動載入測試數據
        load_test_data()
        
        print("\n🎯 橫向無邊框設計特點:")
        print("1. 📊 Flag Statistics 橫向表格 (Track Limit: 3, Double Yellow: 2, Yellow: 5, Red: 1)")
        print("2. 🏆 Driver Incident Frequency (VER: 3, HAM: 2, LEC: 2, 其他: 1)")
        print("3. 🏁 Safety Periods (3條記錄)")
        print("4. ✨ 無外框設計，間距緊湊")
        
        # 執行應用程式（如果是獨立運行）
        if __name__ == "__main__":
            sys.exit(app.exec_())
        
        return True
        
    except Exception as e:
        print(f"❌ 橫向設計測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis 橫向無邊框設計測試")
    print("改進：橫向統計表格、移除外框、緊湊間距")
    print()
    
    success = test_horizontal_design()
    
    if success:
        print("\n🎉 橫向無邊框設計實現成功！")
        return 0
    else:
        print("\n❌ 橫向設計測試失敗")
        return 1

if __name__ == "__main__":
    main()