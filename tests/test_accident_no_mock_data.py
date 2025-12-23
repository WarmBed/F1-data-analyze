#!/usr/bin/env python3
"""
F1T Accident Analysis 無模擬數據測試
驗證系統遵守禁用模擬數據政策
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_no_mock_data_policy():
    """測試禁用模擬數據政策"""
    print("🔍 測試禁用模擬數據政策...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
        from PyQt5.QtCore import Qt
        from modules.gui.accident_analysis.accident_analysis_mdi import (
            AccidentStatisticsWidget,
            DriverIncidentBarChart,
            SafetyPeriodsWidget
        )
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建應用程式
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建主視窗
        main_window = QMainWindow()
        main_window.setWindowTitle("F1T Accident Analysis - 無模擬數據測試")
        main_window.setGeometry(100, 100, 900, 700)
        
        # 創建中央 Widget
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加說明標籤
        info_label = QLabel(
            "⚠️ 無模擬數據政策測試\n\n"
            "本測試驗證系統遵守以下政策：\n"
            "✅ 禁止使用模擬或示例數據\n"
            "✅ 僅顯示來自 FastF1/OpenF1 API 的真實數據\n"
            "✅ 數據為空時顯示明確的無數據訊息\n\n"
            "測試場景：傳入空數據（模擬 API 無回應或無事故的賽事）"
        )
        info_label.setStyleSheet("""
            font-weight: bold; 
            color: #333; 
            padding: 12px; 
            background-color: #fff3cd; 
            border: 2px solid #ffc107;
            border-radius: 5px;
            line-height: 1.8;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        layout.addWidget(stats_widget)
        
        # 測試按鈕
        test_button = QPushButton("🧪 載入空數據（測試無模擬數據政策）")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #333;
                font-weight: bold;
                padding: 12px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ffb300;
            }
        """)
        layout.addWidget(test_button)
        
        # 空數據（模擬無事故的賽事）
        empty_data = {
            'data': {
                'all_incidents': [],  # ⚠️ 空事故列表
                'safety_periods': []  # ⚠️ 空安全車時段
            }
        }
        
        # 連接測試按鈕
        def load_empty_data_and_verify():
            print("\n" + "="*70)
            print("🧪 無模擬數據政策測試報告")
            print("="*70)
            print("\n📊 測試場景: 載入空數據（模擬無事故賽事）")
            
            # 載入空數據
            stats_widget.update_statistics_data(empty_data)
            
            # 驗證 Flag Statistics Summary
            print("\n✅ Flag Statistics Summary 驗證:")
            if hasattr(stats_widget, 'statistics_table') and hasattr(stats_widget.statistics_table, 'stats_table'):
                table = stats_widget.statistics_table.stats_table
                all_zero = True
                for col in range(4):
                    item = table.item(0, col)
                    value = item.text() if item else "?"
                    header = table.horizontalHeaderItem(col).text()
                    
                    if value == "0":
                        print(f"   ✅ {header}: {value} (正確：無數據顯示 0)")
                    else:
                        print(f"   ❌ {header}: {value} (錯誤：應該是 0)")
                        all_zero = False
                
                if all_zero:
                    print("   🎉 Flag Statistics 正確：所有數值為 0，無模擬數據")
                else:
                    print("   ⚠️ Flag Statistics 異常：發現非零數值")
            
            # 驗證 Driver Incident Chart
            print("\n✅ Driver Incident Frequency 驗證:")
            if hasattr(stats_widget, 'driver_chart'):
                chart_text = stats_widget.driver_chart.chart_area.text()
                
                if "No driver incident data available" in chart_text or "無數據" in chart_text:
                    print("   ✅ 正確顯示「無數據」訊息")
                    print(f"   📋 顯示內容: {chart_text[:100]}...")
                elif "VER" in chart_text or "HAM" in chart_text or "LEC" in chart_text:
                    print("   ❌ 錯誤：發現示例數據（VER/HAM/LEC）")
                    print(f"   ⚠️ 違反政策：不應顯示模擬車手數據")
                    print(f"   📋 實際內容:\n{chart_text}")
                else:
                    print(f"   ⚠️ 未知狀態")
                    print(f"   📋 內容: {chart_text[:200]}")
            
            # 驗證 Safety Periods
            print("\n✅ Safety Periods 驗證:")
            if hasattr(stats_widget, 'safety_periods_widget'):
                sp_widget = stats_widget.safety_periods_widget
                if hasattr(sp_widget, 'safety_table'):
                    row_count = sp_widget.safety_table.rowCount()
                    print(f"   📏 表格行數: {row_count}")
                    
                    if row_count == 1:
                        # 檢查是否顯示無數據訊息
                        reason_item = sp_widget.safety_table.item(0, 3)
                        if reason_item:
                            reason_text = reason_item.text()
                            if "No safety car periods" in reason_text or "無安全車" in reason_text:
                                print(f"   ✅ 正確顯示「無安全車時段」訊息")
                                print(f"   📋 訊息: {reason_text}")
                            elif "Track debris" in reason_text or "Accident cleanup" in reason_text:
                                print(f"   ❌ 錯誤：發現示例數據")
                                print(f"   ⚠️ 違反政策：不應顯示模擬原因")
                                print(f"   📋 實際內容: {reason_text}")
                            else:
                                print(f"   ⚠️ 未知狀態: {reason_text}")
                    elif row_count == 2:
                        print(f"   ❌ 錯誤：顯示 2 行數據（可能是示例數據）")
                        for row in range(2):
                            period = sp_widget.safety_table.item(row, 0).text() if sp_widget.safety_table.item(row, 0) else "?"
                            reason = sp_widget.safety_table.item(row, 3).text() if sp_widget.safety_table.item(row, 3) else "?"
                            print(f"   ⚠️ 行 {row+1}: {period} - {reason}")
                    else:
                        print(f"   ⚠️ 異常行數: {row_count}")
            
            print("\n" + "="*70)
            print("📝 測試結論")
            print("="*70)
            print("根據 F1T 開發政策：")
            print("✅ 禁用模擬數據政策 - 絕不使用生成、模擬或偽造的遙測數據")
            print("✅ API-ONLY 模式 - GUI 只能通過 API 或讀取本地 JSON 獲取真實數據")
            print("✅ 數據為空時 - 應顯示明確的無數據訊息，而非示例數據")
            print("\n請確認上述三個組件都沒有顯示模擬/示例數據！")
        
        test_button.clicked.connect(load_empty_data_and_verify)
        
        # 顯示視窗
        main_window.show()
        
        # 自動執行測試
        load_empty_data_and_verify()
        
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
    print("🏎️ F1T Accident Analysis 無模擬數據政策測試")
    print("=" * 70)
    print("政策: 禁用模擬數據 - 僅使用真實 F1 數據")
    print("=" * 70)
    print()
    
    success = test_no_mock_data_policy()
    
    if success:
        print("\n🎉 測試完成！")
        print("\n請視覺確認：")
        print("   1. Flag Statistics Summary 所有數值應為 0")
        print("   2. Driver Incident Frequency 應顯示「無數據」訊息")
        print("   3. Safety Periods 應顯示「無安全車時段」訊息")
        print("   4. 不應出現任何車手代碼（VER/HAM/LEC 等）")
        print("   5. 不應出現任何示例原因（Track debris/Accident cleanup）")
        return 0
    else:
        print("\n❌ 測試失敗")
        return 1

if __name__ == "__main__":
    main()
