#!/usr/bin/env python3
"""
F1T Accident Analysis Flag Statistics 數字可見性測試
專門測試數字是否清晰可見，不被壓縮
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_number_visibility():
    """測試 Flag Statistics 數字可見性"""
    print("🔍 測試 Flag Statistics Summary 數字可見性...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
        from PyQt5.QtCore import Qt
        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentStatisticsWidget
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建應用程式
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建主視窗
        main_window = QMainWindow()
        main_window.setWindowTitle("F1T - Flag Statistics 數字可見性測試")
        main_window.setGeometry(100, 100, 900, 550)
        
        # 創建中央 Widget
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加說明標籤 - 紅色警告框
        info_label = QLabel(
            "🎯 測試目標：Flag Statistics Summary 數字必須清晰可見\n"
            "✅ 預期：每欄下方應該清楚顯示數字 (3, 2, 4, 2)\n"
            "📏 尺寸：表格總高56px = 標題20px + 數據32px + 邊框4px\n"
            "🔤 字體：20px Bold，確保在32px高度內完整顯示"
        )
        info_label.setStyleSheet("""
            font-weight: bold; 
            color: #d32f2f; 
            padding: 12px; 
            background-color: #ffebee; 
            border: 2px solid #d32f2f;
            border-radius: 6px;
            line-height: 1.8;
            font-size: 13px;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        layout.addWidget(stats_widget)
        
        # 測試數據
        test_data = {
            'data': {
                'all_incidents': [
                    # Track Limits (3)
                    {'driver_code': 'VER', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'HAM', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'},
                    {'driver_code': 'LEC', 'message': 'Track limits violation', 'category': 'TRACK_LIMIT'},
                    
                    # Double Yellow (2)
                    {'driver_code': 'VER', 'message': 'Double yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'HAM', 'message': 'Double yellow flag', 'category': 'YELLOW_FLAG'},
                    
                    # Yellow Flags (4)
                    {'driver_code': 'LEC', 'message': 'Yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'SAI', 'message': 'Yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'RUS', 'message': 'Yellow flag', 'category': 'YELLOW_FLAG'},
                    {'driver_code': 'NOR', 'message': 'Yellow flag', 'category': 'YELLOW_FLAG'},
                    
                    # Red Flag (2)
                    {'driver_code': 'PER', 'message': 'Red flag', 'category': 'RED_FLAG'},
                    {'driver_code': 'ALO', 'message': 'Red flag', 'category': 'RED_FLAG'},
                ],
                'safety_periods': []
            }
        }
        
        # 載入測試數據
        print("📊 載入測試數據...")
        stats_widget.update_statistics_data(test_data)
        
        # 驗證表格設置
        if hasattr(stats_widget, 'statistics_table') and hasattr(stats_widget.statistics_table, 'stats_table'):
            table = stats_widget.statistics_table.stats_table
            
            print(f"\n✅ Flag Statistics 表格配置驗證:")
            print(f"   📏 表格總高度: {table.height()}px (目標: 56px)")
            print(f"   📏 標題行高度: {table.horizontalHeader().height()}px (目標: 20px)")
            print(f"   📏 數據行高度: {table.rowHeight(0)}px (目標: 32px)")
            print(f"   📏 行數: {table.rowCount()} (應為: 1)")
            print(f"   📏 列數: {table.columnCount()} (應為: 4)")
            
            print(f"\n   📊 數據內容驗證:")
            expected = [3, 2, 4, 2]
            all_visible = True
            
            for col in range(4):
                header = table.horizontalHeaderItem(col).text()
                item = table.item(0, col)
                
                if item:
                    value = item.text()
                    is_correct = int(value) == expected[col]
                    alignment = item.textAlignment()
                    is_centered = (alignment & Qt.AlignCenter) == Qt.AlignCenter
                    
                    # 檢查字體大小
                    font = item.font()
                    font_size = font.pointSize()
                    
                    status = "✅" if is_correct else "❌"
                    print(f"   {status} {header}: {value} (預期: {expected[col]}, 置中: {is_centered}, 字體: {font_size}pt)")
                    
                    if not is_correct:
                        all_visible = False
                else:
                    print(f"   ❌ {header}: 無數據項 (預期: {expected[col]})")
                    all_visible = False
            
            # 計算理論高度
            header_h = table.horizontalHeader().height()
            row_h = table.rowHeight(0)
            total_h = table.height()
            calculated = header_h + row_h
            
            print(f"\n   📐 高度計算:")
            print(f"      標題行: {header_h}px")
            print(f"      數據行: {row_h}px")
            print(f"      理論總計: {calculated}px")
            print(f"      實際總高: {total_h}px")
            print(f"      差值: {total_h - calculated}px (邊框和間距)")
            
            if all_visible and row_h >= 30:
                print(f"\n   🎉 數字應該清晰可見！")
            elif row_h < 30:
                print(f"\n   ⚠️ 警告：數據行高度 {row_h}px 可能太小，建議至少 30px")
            else:
                print(f"\n   ⚠️ 部分數據有問題")
        
        # 顯示視窗
        main_window.show()
        
        print("\n🎯 請視覺確認:")
        print("   1. Flag Statistics Summary 的每個數字是否清晰可見？")
        print("   2. 數字是否被壓縮或部分隱藏？")
        print("   3. 數字是否完全置中對齊？")
        print("   4. 表格總高度是否保持緊湊（約56px）？")
        
        # 執行應用程式
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
    print("🏎️ F1T Accident Analysis - Flag Statistics 數字可見性測試")
    print("=" * 70)
    print("問題：數字被壓縮在太小的空間內，難以閱讀")
    print("解決方案：")
    print("  • 表格總高度：55px → 56px")
    print("  • 標題行高度：自動 → 固定20px")
    print("  • 數據行高度：25px → 32px")
    print("  • 字體大小：18px → 20px Bold")
    print("=" * 70)
    print()
    
    success = test_number_visibility()
    
    if success:
        print("\n🎉 測試配置完成！")
        print("請檢查 GUI 視窗確認數字是否清晰可見")
        return 0
    else:
        print("\n❌ 測試失敗")
        return 1

if __name__ == "__main__":
    main()
