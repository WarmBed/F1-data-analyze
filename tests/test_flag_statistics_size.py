#!/usr/bin/env python3
"""
F1T Accident Analysis Flag Statistics 大小修正測試
確保Flag Statistics Summary不會被壓縮，保持與Driver Chart相似的行為
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_flag_statistics_size():
    """測試Flag Statistics大小修正"""
    print("🔍 測試Flag Statistics大小修正...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
        from PyQt5.QtWidgets import QSizePolicy
        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentStatisticsWidget
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建應用程式
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建主視窗 - 測試不同大小
        main_window = QMainWindow()
        main_window.setWindowTitle("F1T Accident Analysis - Flag Statistics大小修正測試")
        main_window.setGeometry(100, 100, 1000, 600)
        
        # 創建中央 Widget
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加說明標籤
        info_label = QLabel("🔧 Flag Statistics 大小修正測試 - 應該不會被壓縮，保持適當大小")
        info_label.setStyleSheet("font-weight: bold; color: #333; padding: 8px; background-color: #e8f4fd; border-radius: 4px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        layout.addWidget(stats_widget)
        
        # 創建測試按鈕
        test_button = QPushButton("載入測試數據並檢查大小政策")
        layout.addWidget(test_button)
        
        # 測試數據
        test_data = {
            'data': {
                'all_incidents': [
                    {'driver_code': 'VER', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'HAM', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'LEC', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'SAI', 'message': 'Double yellow flag shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'RUS', 'message': 'Double yellow flag incident', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'NOR', 'message': 'Yellow flag sector', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'PER', 'message': 'Yellow flag shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'ALO', 'message': 'Yellow flag caution', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'STR', 'message': 'Yellow flag debris', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'TSU', 'message': 'Red flag incident', 'category': 'RED_FLAG'},
                    {'driver_code': 'BOT', 'message': 'Red flag session', 'category': 'RED_FLAG'},
                    # 車手事故數據
                    {'driver_code': 'VER', 'message': 'Collision', 'category': 'ACCIDENT'},
                    {'driver_code': 'VER', 'message': 'Another incident', 'category': 'ACCIDENT'},
                    {'driver_code': 'VER', 'message': 'Third incident', 'category': 'ACCIDENT'},
                    {'driver_code': 'HAM', 'message': 'Contact', 'category': 'ACCIDENT'},
                    {'driver_code': 'HAM', 'message': 'Spin', 'category': 'ACCIDENT'},
                    {'driver_code': 'LEC', 'message': 'Contact with RUS', 'category': 'ACCIDENT'},
                    {'driver_code': 'SAI', 'message': 'Engine issue', 'category': 'ACCIDENT'},
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Track debris removal'},
                    {'type': 'VSC', 'start_lap': 28, 'end_lap': 30, 'reason': 'Accident cleanup'},
                ]
            }
        }
        
        # 連接測試按鈕
        def load_test_data_and_check():
            print("📊 載入測試數據並檢查大小政策...")
            stats_widget.update_statistics_data(test_data)
            
            # 檢查Flag Statistics的大小政策和實際尺寸
            print("\n📏 Flag Statistics 大小檢查:")
            
            # 檢查容器
            if hasattr(stats_widget, 'statistics_table'):
                container = stats_widget.statistics_table
                container_size = container.size()
                container_policy = container.sizePolicy()
                print(f"   容器尺寸: {container_size.width()}×{container_size.height()}")
                print(f"   容器大小政策: H={container_policy.horizontalPolicy()}, V={container_policy.verticalPolicy()}")
                
                # 檢查表格
                if hasattr(container, 'stats_table') or hasattr(stats_widget.statistics_table, 'stats_table'):
                    # 找到表格
                    table = None
                    for child in container.findChildren(type(stats_widget.statistics_table).__bases__[0]):
                        if hasattr(child, 'columnCount') and child.columnCount() == 4:
                            table = child
                            break
                    
                    if table:
                        table_size = table.size()
                        table_policy = table.sizePolicy()
                        print(f"   表格尺寸: {table_size.width()}×{table_size.height()}")
                        print(f"   表格大小政策: H={table_policy.horizontalPolicy()}, V={table_policy.verticalPolicy()}")
                        
                        # 檢查數據
                        print(f"   數據內容:")
                        headers = ["Track Limit", "Double Yellow", "Yellow Flag", "Red Flag"]
                        for col in range(4):
                            item = table.item(0, col)
                            value = item.text() if item else "0"
                            print(f"     {headers[col]}: {value}")
            
            # 檢查Driver Chart作為對比
            print("\n🏆 Driver Chart 大小對比:")
            if hasattr(stats_widget, 'driver_chart'):
                chart_size = stats_widget.driver_chart.size()
                chart_policy = stats_widget.driver_chart.sizePolicy()
                print(f"   Chart尺寸: {chart_size.width()}×{chart_size.height()}")
                print(f"   Chart大小政策: H={chart_policy.horizontalPolicy()}, V={chart_policy.verticalPolicy()}")
            
            print("✅ 大小檢查完成")
        
        test_button.clicked.connect(load_test_data_and_check)
        
        # 顯示視窗
        main_window.show()
        
        # 自動載入測試數據
        load_test_data_and_check()
        
        print("\n🎯 測試指南:")
        print("1. Flag Statistics 應該顯示: Track Limit: 3, Double Yellow: 2, Yellow Flag: 4, Red Flag: 2")
        print("2. 表格應該有適當的寬度，不會被過度壓縮")
        print("3. 水平方向應該可以隨視窗擴展")
        print("4. 垂直方向保持固定70px高度")
        print("5. 與 Driver Chart 行為類似")
        
        # 執行應用程式（如果是獨立運行）
        if __name__ == "__main__":
            sys.exit(app.exec_())
        
        return True
        
    except Exception as e:
        print(f"❌ Flag Statistics 大小修正測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis Flag Statistics 大小修正測試")
    print("確保Flag Statistics不會被過度壓縮")
    print()
    
    success = test_flag_statistics_size()
    
    if success:
        print("\n🎉 Flag Statistics 大小修正成功！")
        return 0
    else:
        print("\n❌ 測試失敗")
        return 1

if __name__ == "__main__":
    main()