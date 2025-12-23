#!/usr/bin/env python3
"""
F1T Accident Analysis 數字顯示與線條對齊測試
測試兩個問題的修復：
1. Track Limit下面的數字正確顯示
2. Driver Incident Frequency的線條完美對齊
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_numbers_and_alignment():
    """測試數字顯示和線條對齊"""
    print("🔍 測試數字顯示和線條對齊...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
        from PyQt5.QtCore import Qt
        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentStatisticsWidget
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建應用程式
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建主視窗
        main_window = QMainWindow()
        main_window.setWindowTitle("F1T Accident Analysis - 數字與對齊測試")
        main_window.setGeometry(100, 100, 900, 600)
        
        # 創建中央 Widget
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加說明標籤
        info_label = QLabel(
            "🎯 測試目標:\n"
            "1️⃣ Flag Statistics Summary 數字應該在每欄下方清楚顯示 (3, 2, 4, 2)\n"
            "2️⃣ Driver Incident Frequency 的所有垂直線 │ 應該完美對齊"
        )
        info_label.setStyleSheet("""
            font-weight: bold; 
            color: #333; 
            padding: 8px; 
            background-color: #e8f4fd; 
            border-radius: 4px;
            line-height: 1.6;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        layout.addWidget(stats_widget)
        
        # 創建測試按鈕
        test_button = QPushButton("📊 載入測試數據 & 驗證顯示")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(test_button)
        
        # 測試數據 - 包含多個車手和事件
        test_data = {
            'data': {
                'all_incidents': [
                    # Track Limits (3次)
                    {'driver_code': 'VER', 'message': 'Track limits violation turn 1', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'HAM', 'message': 'Track limits violation turn 8', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'LEC', 'message': 'Track limits at chicane', 'category': 'TRACK_LIMIT'},
                    
                    # Double Yellow (2次)
                    {'driver_code': 'VER', 'message': 'Double yellow flag shown sector 1', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'VER', 'message': 'Double yellow flag accident', 'category': 'YELLOW_FLAG'},
                    
                    # Yellow Flags (4次)
                    {'driver_code': 'HAM', 'message': 'Yellow flag sector 3', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'HAM', 'message': 'Yellow flag shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'LEC', 'message': 'Local yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'LEC', 'message': 'Yellow flag debris', 'category': 'YELLOW_FLAG'},
                    
                    # Red Flag (2次)
                    {'driver_code': 'SAI', 'message': 'Red flag heavy crash', 'category': 'RED_FLAG'},
                    {'driver_code': 'SAI', 'message': 'Red flag session stopped', 'category': 'RED_FLAG'},
                    
                    # 額外車手事故 - 測試條形圖對齊
                    {'driver_code': 'RUS', 'message': 'Collision', 'category': 'ACCIDENT'},
                    {'driver_code': 'NOR', 'message': 'Spin', 'category': 'ACCIDENT'},
                    {'driver_code': 'PER', 'message': 'Contact', 'category': 'ACCIDENT'},
                    {'driver_code': 'ALO', 'message': 'Track excursion', 'category': 'ACCIDENT'},
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Track debris removal'},
                    {'type': 'VSC', 'start_lap': 28, 'end_lap': 30, 'reason': 'Accident cleanup'},
                ]
            }
        }
        
        # 連接測試按鈕
        def load_test_data_and_verify():
            print("📊 載入測試數據並驗證...")
            stats_widget.update_statistics_data(test_data)
            
            # 驗證表格數字顯示
            if hasattr(stats_widget, 'statistics_table') and hasattr(stats_widget.statistics_table, 'stats_table'):
                table = stats_widget.statistics_table.stats_table
                
                print(f"\n✅ Flag Statistics 表格驗證:")
                print(f"   📏 表格總高度: {table.height()}px (目標: 55px)")
                print(f"   📏 數據行高度: {table.rowHeight(0)}px (目標: 25px)")
                print(f"\n   📊 數據內容驗證:")
                
                expected_counts = [3, 2, 4, 2]
                all_correct = True
                
                for col in range(4):
                    header = table.horizontalHeaderItem(col).text()
                    item = table.item(0, col)
                    
                    if item:
                        value = item.text()
                        alignment = item.textAlignment()
                        is_centered = (alignment & Qt.AlignCenter) == Qt.AlignCenter
                        is_correct = int(value) == expected_counts[col]
                        
                        status = "✅" if is_correct and is_centered else "❌"
                        print(f"   {status} {header}: {value} (預期: {expected_counts[col]}, 置中: {is_centered})")
                        
                        if not (is_correct and is_centered):
                            all_correct = False
                    else:
                        print(f"   ❌ {header}: 無數據 (預期: {expected_counts[col]})")
                        all_correct = False
                
                if all_correct:
                    print("\n   🎉 所有數字正確顯示且置中！")
                else:
                    print("\n   ⚠️ 部分數字顯示或對齊有問題")
            
            # 驗證 Driver Chart 對齊
            if hasattr(stats_widget, 'driver_chart'):
                print(f"\n✅ Driver Incident Chart 驗證:")
                chart_text = stats_widget.driver_chart.chart_area.text()
                lines = chart_text.split('\n')
                
                print(f"   📏 總行數: {len(lines)}")
                
                # 檢查垂直線位置
                if len(lines) > 2:
                    # 找到第一條垂直線的位置
                    separator_line = lines[1] if len(lines) > 1 else ""
                    pipe_positions = [i for i, char in enumerate(separator_line) if char == '┼']
                    
                    if pipe_positions:
                        print(f"   📍 垂直線位置: {pipe_positions}")
                        
                        # 檢查所有行的垂直線是否對齊
                        all_aligned = True
                        for i, line in enumerate(lines):
                            line_pipes = [j for j, char in enumerate(line) if char == '│']
                            if line_pipes != pipe_positions:
                                if line_pipes:  # 只報告有垂直線但位置不對的情況
                                    print(f"   ⚠️ 第{i+1}行垂直線位置不對齊: {line_pipes}")
                                    all_aligned = False
                        
                        if all_aligned:
                            print(f"   🎉 所有垂直線完美對齊！")
                    else:
                        print(f"   ⚠️ 找不到垂直線分隔符")
                
                # 顯示前幾行供視覺檢查
                print(f"\n   📋 圖表前5行預覽:")
                for i, line in enumerate(lines[:5]):
                    print(f"      {line}")
            
            print("\n✅ 測試數據載入和驗證完成")
        
        test_button.clicked.connect(load_test_data_and_verify)
        
        # 顯示視窗
        main_window.show()
        
        # 自動載入測試數據
        load_test_data_and_verify()
        
        print("\n🎯 預期結果:")
        print("📊 Flag Statistics Summary:")
        print("   • Track Limit 下方應顯示: 3")
        print("   • Double Yellow 下方應顯示: 2") 
        print("   • Yellow Flag 下方應顯示: 4")
        print("   • Red Flag 下方應顯示: 2")
        print("\n📊 Driver Incident Frequency:")
        print("   • 所有垂直線 │ 應該在同一列")
        print("   • VER 應該有最長的條形 (5次事故)")
        print("   • HAM 和 LEC 次之 (各3次)")
        print("   • SAI 應該有2次")
        
        # 執行應用程式（如果是獨立運行）
        if __name__ == "__main__":
            sys.exit(app.exec_())
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis 數字顯示與線條對齊測試")
    print("目標：修復數字消失 + 線條對齊問題")
    print()
    
    success = test_numbers_and_alignment()
    
    if success:
        print("\n🎉 測試成功！請視覺確認：")
        print("   1. Flag Statistics 每欄下方都有數字")
        print("   2. Driver Chart 所有垂直線完美對齊")
        return 0
    else:
        print("\n❌ 測試失敗")
        return 1

if __name__ == "__main__":
    main()
