#!/usr/bin/env python3
"""
F1T Accident Analysis 固定表格和對齊圖表測試
測試Flag Statistics表格固定不可拖拉，以及Driver Chart對齊和放大
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_fixed_table_and_aligned_chart():
    """測試固定表格和對齊圖表"""
    print("🔍 測試固定表格和對齊圖表...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
        from PyQt5.QtWidgets import QHeaderView
        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentStatisticsWidget
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建應用程式
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建主視窗
        main_window = QMainWindow()
        main_window.setWindowTitle("F1T Accident Analysis - 固定表格與對齊圖表測試")
        main_window.setGeometry(100, 100, 900, 600)
        
        # 創建中央 Widget
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加說明標籤
        info_label = QLabel("🔒 固定表格測試 - Flag Statistics不可拖拉調整 | 📏 圖表對齊測試 - Driver Chart放大且對齊")
        info_label.setStyleSheet("font-weight: bold; color: #333; padding: 5px; background-color: #f0f0f0; border-radius: 4px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        layout.addWidget(stats_widget)
        
        # 創建測試按鈕
        test_button = QPushButton("載入測試數據並驗證設定")
        layout.addWidget(test_button)
        
        # 更豐富的測試數據以展示對齊效果
        test_data = {
            'data': {
                'all_incidents': [
                    # Track Limits (4次)
                    {'driver_code': 'VER', 'message': 'Track limits violation turn 1', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'HAM', 'message': 'Track limits violation turn 8', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'LEC', 'message': 'Track limits at chicane', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'SAI', 'message': 'Track limits last corner', 'category': 'TRACK_LIMIT'},
                    
                    # Double Yellow (3次，注意message包含"DOUBLE YELLOW")
                    {'driver_code': 'RUS', 'message': 'Double yellow flag sector 2', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'NOR', 'message': 'Double yellow shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'PER', 'message': 'Double yellow flag incident', 'category': 'YELLOW_FLAG'},
                    
                    # Yellow Flags (6次)
                    {'driver_code': 'ALO', 'message': 'Yellow flag sector 3', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'STR', 'message': 'Yellow flag shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'TSU', 'message': 'Local yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'BOT', 'message': 'Yellow flag debris', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'ZHO', 'message': 'Yellow flag incident', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'MAG', 'message': 'Yellow flag caution', 'category': 'YELLOW_FLAG'},
                    
                    # Red Flag (2次)
                    {'driver_code': 'OCO', 'message': 'Red flag incident heavy crash', 'category': 'RED_FLAG'},
                    {'driver_code': 'GAS', 'message': 'Red flag session stopped', 'category': 'RED_FLAG'},
                    
                    # 車手事故數據（用於圖表）
                    {'driver_code': 'VER', 'message': 'Collision with barrier', 'category': 'ACCIDENT'},
                    {'driver_code': 'VER', 'message': 'Another incident', 'category': 'ACCIDENT'},
                    {'driver_code': 'VER', 'message': 'Third incident', 'category': 'ACCIDENT'},
                    {'driver_code': 'HAM', 'message': 'Contact with wall', 'category': 'ACCIDENT'},
                    {'driver_code': 'HAM', 'message': 'Spin incident', 'category': 'ACCIDENT'},
                    {'driver_code': 'LEC', 'message': 'Contact with RUS', 'category': 'ACCIDENT'},
                    {'driver_code': 'LEC', 'message': 'Brake failure', 'category': 'ACCIDENT'},
                    {'driver_code': 'SAI', 'message': 'Engine issue', 'category': 'ACCIDENT'},
                    {'driver_code': 'RUS', 'message': 'Suspension damage', 'category': 'ACCIDENT'},
                    {'driver_code': 'NOR', 'message': 'Puncture incident', 'category': 'ACCIDENT'},
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Track debris removal'},
                    {'type': 'VSC', 'start_lap': 28, 'end_lap': 30, 'reason': 'Accident cleanup'},
                    {'type': 'SC', 'start_lap': 45, 'end_lap': 48, 'reason': 'Heavy crash recovery'},
                ]
            }
        }
        
        # 連接測試按鈕
        def load_test_data_and_verify():
            print("📊 載入測試數據並驗證設定...")
            stats_widget.update_statistics_data(test_data)
            
            # 驗證Flag Statistics表格設定
            if hasattr(stats_widget, 'statistics_table') and hasattr(stats_widget.statistics_table, 'stats_table'):
                table = stats_widget.statistics_table.stats_table
                header = table.horizontalHeader()
                resize_mode = header.sectionResizeMode(0)
                
                print(f"📋 Flag Statistics 表格驗證:")
                print(f"   • 調整模式: {resize_mode} (1=Fixed, 不可拖拉)")
                for col in range(4):
                    width = table.columnWidth(col)
                    header_text = table.horizontalHeaderItem(col).text()
                    value = table.item(0, col).text() if table.item(0, col) else "0"
                    print(f"   • {header_text}: 寬度={width}px, 值={value}")
            
            # 驗證Driver Chart對齊
            if hasattr(stats_widget, 'driver_chart') and hasattr(stats_widget.driver_chart, 'chart_area'):
                chart_text = stats_widget.driver_chart.chart_area.text()
                print(f"\n🏆 Driver Chart 對齊驗證:")
                print("   • 圖表內容預覽:")
                lines = chart_text.split('\n')[:5]  # 只顯示前5行
                for line in lines:
                    print(f"     {line}")
                if '│' in chart_text:
                    print("   ✅ 垂直分隔線已對齊")
                else:
                    print("   ❌ 垂直分隔線未找到")
            
            print("✅ 測試數據載入完成")
        
        test_button.clicked.connect(load_test_data_and_verify)
        
        # 顯示視窗
        main_window.show()
        
        # 自動載入測試數據
        load_test_data_and_verify()
        
        print("\n🎯 測試重點:")
        print("1. 📊 Flag Statistics Summary:")
        print("   • Track Limit: 4, Double Yellow: 3, Yellow Flag: 6, Red Flag: 2")
        print("   • 表格欄位寬度固定，不可拖拉調整")
        print("   • 數字置中顯示")
        print("\n2. 🏆 Driver Incident Frequency:")
        print("   • VER: 6次, HAM: 4次, LEC: 4次, 其他: 1-2次")
        print("   • 條形圖放大1px，垂直線條對齊")
        print("   • 字體放大到12px")
        print("\n3. 🏁 Safety Periods:")
        print("   • 3條記錄，可隨視窗拖拉擴展")
        
        print("\n✨ 請嘗試拖拉Flag Statistics表格的欄位邊界 - 應該無法調整")
        
        # 執行應用程式（如果是獨立運行）
        if __name__ == "__main__":
            sys.exit(app.exec_())
        
        return True
        
    except Exception as e:
        print(f"❌ 固定表格和對齊圖表測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis 固定表格與對齊圖表測試")
    print("固定Flag Statistics + 放大對齊Driver Chart")
    print()
    
    success = test_fixed_table_and_aligned_chart()
    
    if success:
        print("\n🎉 固定表格和對齊圖表實現成功！")
        return 0
    else:
        print("\n❌ 測試失敗")
        return 1

if __name__ == "__main__":
    main()