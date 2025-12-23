#!/usr/bin/env python3
"""
診斷 Flag Statistics Summary 空白區域問題
檢查容器和表格的實際高度
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def diagnose_layout_spacing():
    """診斷布局間距問題"""
    print("🔍 診斷 Flag Statistics Summary 空白區域...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentStatisticsWidget
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建應用程式
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建主視窗
        main_window = QMainWindow()
        main_window.setWindowTitle("F1T Accident Analysis - 空白區域診斷")
        main_window.setGeometry(100, 100, 900, 600)
        
        # 創建中央 Widget
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加說明標籤
        info_label = QLabel("🔍 空白區域診斷 - 檢查各組件的實際高度")
        info_label.setStyleSheet("font-weight: bold; color: #333; padding: 5px; background-color: #ffe6e6; border-radius: 4px;")
        layout.addWidget(info_label)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        layout.addWidget(stats_widget)
        
        # 創建診斷按鈕
        diagnose_button = QPushButton("🔍 執行高度診斷")
        layout.addWidget(diagnose_button)
        
        def diagnose_heights():
            print("\n📏 高度診斷結果:")
            
            # 檢查主 widget
            print(f"主 AccidentStatisticsWidget:")
            print(f"  • 高度: {stats_widget.height()}px")
            print(f"  • 大小提示: {stats_widget.sizeHint()}")
            print(f"  • 大小政策: H={stats_widget.sizePolicy().horizontalPolicy()}, V={stats_widget.sizePolicy().verticalPolicy()}")
            
            # 檢查統計表格容器
            if hasattr(stats_widget, 'statistics_table'):
                container = stats_widget.statistics_table
                print(f"\nFlag Statistics 容器:")
                print(f"  • 高度: {container.height()}px")
                print(f"  • 大小提示: {container.sizeHint()}")
                print(f"  • 大小政策: H={container.sizePolicy().horizontalPolicy()}, V={container.sizePolicy().verticalPolicy()}")
                
                # 檢查容器內的佈局
                if container.layout():
                    layout_obj = container.layout()
                    print(f"  • 佈局邊距: {layout_obj.contentsMargins()}")
                    print(f"  • 佈局間距: {layout_obj.spacing()}px")
                
                # 檢查實際的表格 widget
                if hasattr(container, 'stats_table'):
                    table = container.stats_table
                    print(f"\n實際表格 (stats_table):")
                    print(f"  • 高度: {table.height()}px")
                    print(f"  • 固定高度: {table.maximumHeight()}px")
                    print(f"  • 大小提示: {table.sizeHint()}")
                    print(f"  • 大小政策: H={table.sizePolicy().horizontalPolicy()}, V={table.sizePolicy().verticalPolicy()}")
            
            # 檢查車手圖表
            if hasattr(stats_widget, 'driver_chart'):
                chart = stats_widget.driver_chart
                print(f"\nDriver Chart:")
                print(f"  • 高度: {chart.height()}px")
                print(f"  • 大小提示: {chart.sizeHint()}")
                print(f"  • 大小政策: H={chart.sizePolicy().horizontalPolicy()}, V={chart.sizePolicy().verticalPolicy()}")
            
            # 檢查安全期間 widget
            if hasattr(stats_widget, 'safety_periods_widget'):
                safety = stats_widget.safety_periods_widget
                print(f"\nSafety Periods:")
                print(f"  • 高度: {safety.height()}px")
                print(f"  • 大小提示: {safety.sizeHint()}")
                print(f"  • 大小政策: H={safety.sizePolicy().horizontalPolicy()}, V={safety.sizePolicy().verticalPolicy()}")
            
            # 檢查主佈局
            main_layout = stats_widget.layout()
            if main_layout:
                print(f"\n主佈局:")
                print(f"  • 佈局邊距: {main_layout.contentsMargins()}")
                print(f"  • 佈局間距: {main_layout.spacing()}px")
                print(f"  • 佈局項目數: {main_layout.count()}")
                
                # 檢查每個佈局項目的 stretch 值
                for i in range(main_layout.count()):
                    item = main_layout.itemAt(i)
                    stretch = main_layout.stretch(i)
                    if item and item.widget():
                        widget_name = item.widget().__class__.__name__
                        print(f"  • 項目 {i}: {widget_name}, stretch={stretch}")
            
            print(f"\n💡 分析:")
            print(f"如果容器高度 > 表格高度，那空白區域就在容器內部")
            print(f"如果主 widget 高度很大，可能是佈局 stretch 設定問題")
        
        diagnose_button.clicked.connect(diagnose_heights)
        
        # 載入測試數據
        test_data = {
            'data': {
                'all_incidents': [
                    {'driver_code': 'VER', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'HAM', 'message': 'Yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'LEC', 'message': 'Double yellow', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'SAI', 'message': 'Red flag', 'category': 'RED_FLAG'},
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Debris cleanup'},
                ]
            }
        }
        
        stats_widget.update_statistics_data(test_data)
        
        # 顯示視窗
        main_window.show()
        
        # 自動執行診斷
        diagnose_heights()
        
        # 執行應用程式（如果是獨立運行）
        if __name__ == "__main__":
            sys.exit(app.exec_())
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    diagnose_layout_spacing()