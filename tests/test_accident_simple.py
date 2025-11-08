#!/usr/bin/env python3
"""
簡化版 Accident Analysis 改良 B 設計測試
快速驗證基本 import 和 Widget 創建功能
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_basic_imports():
    """基本 Import 測試"""
    print("🔍 測試基本 Import...")
    
    try:
        # 測試核心翻譯功能
        from core.gui_i18n import tr
        print("✅ 翻譯模組 import 成功")
        
        # 測試 PyQt5 Widget
        from PyQt5.QtWidgets import QGroupBox, QTableWidget, QFrame, QLabel
        print("✅ PyQt5 Widget import 成功")
        
        # 測試新的 Widget 類別
        from modules.gui.accident_analysis.accident_analysis_mdi import (
            SafetyPeriodsWidget, 
            PenaltiesSummaryWidget,
            DriverIncidentBarChart
        )
        print("✅ 新 Widget 類別 import 成功")
        
        return True
        
    except Exception as e:
        print(f"❌ Import 失敗: {e}")
        return False

def test_widget_creation():
    """Widget 創建測試"""
    print("\n🔧 測試 Widget 創建...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.accident_analysis.accident_analysis_mdi import (
            SafetyPeriodsWidget, 
            PenaltiesSummaryWidget,
            DriverIncidentBarChart
        )
        
        # 創建 QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建 Widgets
        safety_widget = SafetyPeriodsWidget()
        penalties_widget = PenaltiesSummaryWidget()
        chart_widget = DriverIncidentBarChart()
        
        print("✅ SafetyPeriodsWidget 創建成功")
        print("✅ PenaltiesSummaryWidget 創建成功") 
        print("✅ DriverIncidentBarChart 創建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ Widget 創建失敗: {e}")
        return False

def test_widget_methods():
    """Widget 方法測試"""
    print("\n⚙️ 測試 Widget 方法...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.accident_analysis.accident_analysis_mdi import (
            SafetyPeriodsWidget, 
            PenaltiesSummaryWidget,
            DriverIncidentBarChart
        )
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 測試 SafetyPeriodsWidget 方法
        safety_widget = SafetyPeriodsWidget()
        safety_widget.update_safety_periods_data([])
        print("✅ SafetyPeriodsWidget.update_safety_periods_data() 工作正常")
        
        # 測試 PenaltiesSummaryWidget 方法
        penalties_widget = PenaltiesSummaryWidget()
        penalties_widget.update_penalties_data([])
        print("✅ PenaltiesSummaryWidget.update_penalties_data() 工作正常")
        
        # 測試 DriverIncidentBarChart 方法
        chart_widget = DriverIncidentBarChart()
        chart_widget.update_chart_data({})
        print("✅ DriverIncidentBarChart.update_chart_data() 工作正常")
        
        return True
        
    except Exception as e:
        print(f"❌ Widget 方法測試失敗: {e}")
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis 改良 B 設計 - 簡化測試")
    print()
    
    results = []
    results.append(("基本 Import", test_basic_imports()))
    results.append(("Widget 創建", test_widget_creation()))
    results.append(("Widget 方法", test_widget_methods()))
    
    # 結果總結
    print("\n" + "=" * 50)
    print("測試結果總結")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 基本功能測試通過！")
        return 0
    else:
        print("⚠️ 部分測試失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main())