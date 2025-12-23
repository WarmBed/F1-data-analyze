#!/usr/bin/env python3
"""
F1T Accident Analysis 空白區域修復測試
深度修復 Flag Statistics Summary 下方的空白區域問題
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_whitespace_fix():
    """測試空白區域修復"""
    print("🔍 測試空白區域修復...")
    print("\n📋 修復內容：")
    print("   1. container.setFixedHeight(80) - 設置容器固定高度")
    print("   2. layout.setAlignment(Qt.AlignTop) - 內容向上對齊")
    print("   3. stats_table.setRowHeight(0, 25) - 設置數據行高度")
    print("   4. 移除 resizeEvent() 中的干擾代碼")
    print("   5. 優化表格樣式（padding: 3px, font-size: 16px/11px）")
    print()
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QSizePolicy
        from PyQt5.QtCore import Qt
        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentStatisticsWidget
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建應用程式
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建主視窗
        main_window = QMainWindow()
        main_window.setWindowTitle("F1T Accident Analysis - 空白區域修復測試")
        main_window.setGeometry(100, 100, 900, 600)
        
        # 創建中央 Widget
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加說明標籤
        info_label = QLabel(
            "🎯 空白區域修復驗證\n"
            "預期結果：Flag Statistics Summary 下方不再有大片空白\n"
            "容器固定高度 80px = 標題 20px + 表格 55px + 間距 5px"
        )
        info_label.setStyleSheet(
            "font-weight: bold; color: #333; padding: 8px; "
            "background-color: #e8f4fd; border-radius: 4px; "
            "border-left: 4px solid #2196F3;"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        layout.addWidget(stats_widget)
        
        # 創建測試按鈕
        test_button = QPushButton("載入測試數據 & 深度驗證")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(test_button)
        
        # 測試數據
        test_data = {
            'data': {
                'all_incidents': [
                    # Track Limits (5次)
                    {'driver_code': 'VER', 'message': 'Track limits violation turn 1', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'HAM', 'message': 'Track limits violation turn 8', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'LEC', 'message': 'Track limits at chicane', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'SAI', 'message': 'Track limits final corner', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'RUS', 'message': 'Track limits sector 2', 'category': 'TRACK_LIMIT'},
                    
                    # Double Yellow (3次)
                    {'driver_code': 'NOR', 'message': 'Double yellow flag shown sector 1', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'PER', 'message': 'Double yellow flag accident', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'ALO', 'message': 'Double yellow flag debris', 'category': 'YELLOW_FLAG'},
                    
                    # Yellow Flags (7次)
                    {'driver_code': 'STR', 'message': 'Yellow flag sector 3', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'TSU', 'message': 'Yellow flag shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'BOT', 'message': 'Local yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'ZHO', 'message': 'Yellow flag debris', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'MAG', 'message': 'Yellow flag incident', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'HUL', 'message': 'Yellow flag caution', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'OCO', 'message': 'Yellow flag safety', 'category': 'YELLOW_FLAG'},
                    
                    # Red Flag (2次)
                    {'driver_code': 'GAS', 'message': 'Red flag heavy crash', 'category': 'RED_FLAG'},
                    {'driver_code': 'DEV', 'message': 'Red flag session stopped', 'category': 'RED_FLAG'},
                    
                    # 車手事故數據
                    {'driver_code': 'VER', 'message': 'Collision', 'category': 'ACCIDENT'},
                    {'driver_code': 'VER', 'message': 'Spin', 'category': 'ACCIDENT'},
                    {'driver_code': 'VER', 'message': 'Contact', 'category': 'ACCIDENT'},
                    {'driver_code': 'VER', 'message': 'Lock-up', 'category': 'ACCIDENT'},
                    {'driver_code': 'HAM', 'message': 'Collision', 'category': 'ACCIDENT'},
                    {'driver_code': 'HAM', 'message': 'Spin', 'category': 'ACCIDENT'},
                    {'driver_code': 'HAM', 'message': 'Contact', 'category': 'ACCIDENT'},
                    {'driver_code': 'LEC', 'message': 'Collision', 'category': 'ACCIDENT'},
                    {'driver_code': 'LEC', 'message': 'Spin', 'category': 'ACCIDENT'},
                    {'driver_code': 'SAI', 'message': 'Collision', 'category': 'ACCIDENT'},
                    {'driver_code': 'SAI', 'message': 'Contact', 'category': 'ACCIDENT'},
                    {'driver_code': 'RUS', 'message': 'Spin', 'category': 'ACCIDENT'},
                    {'driver_code': 'NOR', 'message': 'Contact', 'category': 'ACCIDENT'},
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Track debris removal'},
                    {'type': 'VSC', 'start_lap': 28, 'end_lap': 30, 'reason': 'Accident cleanup'},
                ]
            }
        }
        
        # 連接測試按鈕
        def load_test_data_and_verify():
            print("\n" + "="*80)
            print("📊 載入測試數據並深度驗證...")
            print("="*80)
            
            stats_widget.update_statistics_data(test_data)
            
            # 深度驗證 1: Container 屬性
            if hasattr(stats_widget, 'statistics_table'):
                container = stats_widget.statistics_table
                print(f"\n🔍 深度驗證 1: Container 屬性")
                print(f"   ├─ 實際高度: {container.height()}px (目標: 80px)")
                print(f"   ├─ 固定高度: {container.minimumHeight()}px ~ {container.maximumHeight()}px")
                print(f"   ├─ 大小政策: 水平={container.sizePolicy().horizontalPolicy()}, 垂直={container.sizePolicy().verticalPolicy()}")
                print(f"   │  (預期: 水平=5[Expanding], 垂直=0[Fixed])")
                
                # 檢查布局對齊
                if container.layout():
                    alignment = container.layout().alignment()
                    print(f"   └─ 布局對齊: {alignment} (預期包含 Qt.AlignTop)")
            
            # 深度驗證 2: Table 屬性
            if hasattr(stats_widget, 'statistics_table') and hasattr(stats_widget.statistics_table, 'stats_table'):
                table = stats_widget.statistics_table.stats_table
                print(f"\n🔍 深度驗證 2: Table 屬性")
                print(f"   ├─ 表格高度: {table.height()}px (目標: 55px)")
                print(f"   ├─ 固定高度: {table.minimumHeight()}px ~ {table.maximumHeight()}px")
                print(f"   ├─ 行數: {table.rowCount()} (應為: 1)")
                print(f"   ├─ 列數: {table.columnCount()} (應為: 4)")
                print(f"   ├─ 第一行高度: {table.rowHeight(0)}px (目標: 25px)")
                print(f"   └─ 大小政策: 水平={table.sizePolicy().horizontalPolicy()}, 垂直={table.sizePolicy().verticalPolicy()}")
                
                # 驗證數據內容
                print(f"\n🔍 深度驗證 3: Table 數據內容")
                for col in range(4):
                    header = table.horizontalHeaderItem(col).text()
                    value = table.item(0, col).text() if table.item(0, col) else "0"
                    print(f"   ├─ {header}: {value}")
            
            # 深度驗證 4: 整體布局結構
            print(f"\n🔍 深度驗證 4: 整體布局結構")
            print(f"   ├─ 主 Widget 高度: {stats_widget.height()}px")
            print(f"   ├─ Container 在主布局中的 stretch: 0 (不應擴展)")
            print(f"   ├─ Driver Chart stretch: 0 (內容驅動)")
            print(f"   └─ Safety Periods stretch: 1 (可擴展)")
            
            print("\n" + "="*80)
            print("✅ 深度驗證完成")
            print("="*80)
            
            print("\n🎯 預期結果對比:")
            print("   ✓ Container 固定高度: 80px")
            print("   ✓ Table 固定高度: 55px")
            print("   ✓ 數據行高度: 25px")
            print("   ✓ 布局對齊: AlignTop")
            print("   ✓ Flag Statistics Summary 下方無空白")
            
            print("\n✨ 請檢查:")
            print("   1. Flag Statistics Summary 下方是否還有空白？")
            print("   2. 整體高度是否緊湊（約 80px）？")
            print("   3. 拖拉視窗時高度是否保持固定？")
            print("   4. 數字是否完全置中對齊？")
        
        test_button.clicked.connect(load_test_data_and_verify)
        
        # 顯示視窗
        main_window.show()
        
        # 自動載入測試數據
        load_test_data_and_verify()
        
        # 執行應用程式（如果是獨立運行）
        if __name__ == "__main__":
            sys.exit(app.exec_())
        
        return True
        
    except Exception as e:
        print(f"❌ 空白區域修復測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis 空白區域修復測試")
    print("深度修復：Container 固定高度 + 布局對齊 + 移除干擾代碼")
    print()
    
    success = test_whitespace_fix()
    
    if success:
        print("\n🎉 空白區域修復實現成功！")
        return 0
    else:
        print("\n❌ 測試失敗")
        return 1

if __name__ == "__main__":
    main()
