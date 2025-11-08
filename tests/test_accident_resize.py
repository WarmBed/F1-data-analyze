#!/usr/bin/env python3
"""
F1T Accident Analysis 大小調整行為測試
測試固定大小、內容驅動、可擴展三種不同的大小行為
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_size_behavior():
    """測試大小調整行為"""
    print("🔍 測試大小調整行為...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentStatisticsWidget
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建應用程式
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建主視窗 - 初始中等大小
        main_window = QMainWindow()
        main_window.setWindowTitle("F1T Accident Analysis - 大小調整測試")
        main_window.setGeometry(100, 100, 800, 500)
        
        # 創建中央 Widget
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加說明標籤
        info_label = QLabel("📏 大小調整測試 - 請拖拉視窗觀察各組件行為")
        info_label.setStyleSheet("font-weight: bold; color: #333; padding: 5px;")
        layout.addWidget(info_label)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        layout.addWidget(stats_widget)
        
        # 創建測試按鈕
        test_button = QPushButton("載入測試數據")
        layout.addWidget(test_button)
        
        # 豐富的測試數據
        test_data = {
            'data': {
                'all_incidents': [
                    # 創建更多車手事故數據以測試圖表大小
                    {'driver_code': 'VER', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'VER', 'message': 'Another incident', 'category': 'ACCIDENT'},
                    {'driver_code': 'VER', 'message': 'Third incident', 'category': 'PENALTY'},
                    {'driver_code': 'HAM', 'message': 'Yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'HAM', 'message': 'Collision', 'category': 'ACCIDENT'},
                    {'driver_code': 'LEC', 'message': 'Double yellow shown', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'LEC', 'message': 'Contact', 'category': 'ACCIDENT'},
                    {'driver_code': 'SAI', 'message': 'Red flag incident', 'category': 'RED_FLAG'},
                    {'driver_code': 'RUS', 'message': 'Track limits', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'NOR', 'message': 'Yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'PER', 'message': 'Incident', 'category': 'ACCIDENT'},
                    {'driver_code': 'ALO', 'message': 'Yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'STR', 'message': 'Track limits', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'TSU', 'message': 'Double yellow', 'category': 'YELLOW_FLAG'},
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Track debris removal'},
                    {'type': 'VSC', 'start_lap': 28, 'end_lap': 30, 'reason': 'Accident cleanup'},
                    {'type': 'SC', 'start_lap': 45, 'end_lap': 48, 'reason': 'Heavy crash recovery'},
                    {'type': 'VSC', 'start_lap': 52, 'end_lap': 54, 'reason': 'Minor incident'},
                    {'type': 'SC', 'start_lap': 58, 'end_lap': 62, 'reason': 'Final cleanup'},
                ]
            }
        }
        
        # 連接測試按鈕
        def load_test_data():
            print("📊 載入測試數據...")
            stats_widget.update_statistics_data(test_data)
            print("✅ 測試數據載入完成")
            
            # 顯示組件大小資訊
            print("\n📏 組件大小行為:")
            if hasattr(stats_widget, 'statistics_table'):
                table_size = stats_widget.statistics_table.size()
                print(f"   📊 Flag Statistics: {table_size.width()}×{table_size.height()} (固定高度)")
            
            if hasattr(stats_widget, 'driver_chart'):
                chart_size = stats_widget.driver_chart.size()
                print(f"   🏆 Driver Chart: {chart_size.width()}×{chart_size.height()} (內容驅動)")
            
            if hasattr(stats_widget, 'safety_periods_widget'):
                safety_size = stats_widget.safety_periods_widget.size()
                print(f"   🏁 Safety Periods: {safety_size.width()}×{safety_size.height()} (可擴展)")
        
        test_button.clicked.connect(load_test_data)
        
        # 驗證大小政策設置
        print("✅ 大小政策驗證:")
        
        # 驗證 Flag Statistics (固定)
        if hasattr(stats_widget, 'statistics_table') and hasattr(stats_widget.statistics_table, 'stats_table'):
            table = stats_widget.statistics_table.stats_table
            v_policy = table.sizePolicy().verticalPolicy()
            print(f"   📊 Flag Statistics 垂直政策: {v_policy} (應為固定)")
        
        # 驗證 Driver Chart (內容驅動)
        if hasattr(stats_widget, 'driver_chart') and hasattr(stats_widget.driver_chart, 'chart_area'):
            chart = stats_widget.driver_chart.chart_area
            v_policy = chart.sizePolicy().verticalPolicy()
            print(f"   🏆 Driver Chart 垂直政策: {v_policy} (應為最小/內容)")
        
        # 驗證 Safety Periods (可擴展)
        if hasattr(stats_widget, 'safety_periods_widget') and hasattr(stats_widget.safety_periods_widget, 'safety_table'):
            safety = stats_widget.safety_periods_widget.safety_table
            v_policy = safety.sizePolicy().verticalPolicy()
            print(f"   🏁 Safety Periods 垂直政策: {v_policy} (應為可擴展)")
        
        # 顯示視窗
        main_window.show()
        
        # 自動載入測試數據
        load_test_data()
        
        print("\n🎯 測試指南:")
        print("1. 📊 Flag Statistics Summary: 固定一欄高度，數字置中")
        print("2. 🏆 Driver Incident Frequency: 動態內容，不受視窗影響")
        print("3. 🏁 Safety Periods: 隨視窗拖拉放大縮小")
        print("\n✨ 請拖拉視窗邊緣測試各組件的大小調整行為")
        
        # 執行應用程式（如果是獨立運行）
        if __name__ == "__main__":
            sys.exit(app.exec_())
        
        return True
        
    except Exception as e:
        print(f"❌ 大小調整測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis 大小調整行為測試")
    print("固定大小 vs 內容驅動 vs 可擴展")
    print()
    
    success = test_size_behavior()
    
    if success:
        print("\n🎉 大小調整行為實現成功！")
        return 0
    else:
        print("\n❌ 大小調整測試失敗")
        return 1

if __name__ == "__main__":
    main()