#!/usr/bin/env python3
"""
測試 Accident Analysis 改良 B 設計實現
驗證新的 SafetyPeriodsWidget、PenaltiesSummaryWidget 和 DriverIncidentBarChart 是否正常工作
"""

import sys
import os
import traceback

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath('.'))

def test_import():
    """階段 1: Import 測試"""
    print("=" * 60)
    print("階段 1: Import 測試")
    print("=" * 60)
    
    try:
        # 測試新的 Widget 類別 import
        from modules.gui.accident_analysis.accident_analysis_mdi import (
            AccidentStatisticsWidget,
            SafetyPeriodsWidget, 
            PenaltiesSummaryWidget,
            DriverIncidentBarChart
        )
        print("✅ SafetyPeriodsWidget import 成功")
        print("✅ PenaltiesSummaryWidget import 成功")
        print("✅ DriverIncidentBarChart import 成功")
        print("✅ AccidentStatisticsWidget import 成功")
        return True
        
    except Exception as e:
        print(f"❌ Import 失敗: {e}")
        traceback.print_exc()
        return False

def test_widget_initialization():
    """階段 2: Widget 初始化測試"""
    print("\n" + "=" * 60)
    print("階段 2: Widget 初始化測試")
    print("=" * 60)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.accident_analysis.accident_analysis_mdi import (
            SafetyPeriodsWidget, 
            PenaltiesSummaryWidget,
            DriverIncidentBarChart
        )
        
        # 創建 QApplication (測試環境需要)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 測試 SafetyPeriodsWidget 初始化
        safety_widget = SafetyPeriodsWidget()
        print("✅ SafetyPeriodsWidget 初始化成功")
        print(f"   - 標題: {safety_widget.title()}")
        print(f"   - 表格欄位數: {safety_widget.safety_table.columnCount()}")
        
        # 測試 PenaltiesSummaryWidget 初始化
        penalties_widget = PenaltiesSummaryWidget()
        print("✅ PenaltiesSummaryWidget 初始化成功")
        print(f"   - 標題: {penalties_widget.title()}")
        print(f"   - 是否有處罰卡片: {hasattr(penalties_widget, 'time_penalty_card')}")
        
        # 測試 DriverIncidentBarChart 初始化
        chart_widget = DriverIncidentBarChart()
        print("✅ DriverIncidentBarChart 初始化成功")
        print(f"   - 是否有圖表區域: {hasattr(chart_widget, 'chart_area')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Widget 初始化失敗: {e}")
        traceback.print_exc()
        return False

def test_data_update():
    """階段 3: 數據更新測試"""
    print("\n" + "=" * 60)
    print("階段 3: 數據更新測試")
    print("=" * 60)
    
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
        
        # 測試數據
        sample_safety_periods = [
            {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Track debris removal'},
            {'type': 'VSC', 'start_lap': 28, 'end_lap': 30, 'reason': 'Accident cleanup'}
        ]
        
        sample_penalties = [
            {'type': 'time penalty', 'driver': 'VER', 'severity_score': 8},
            {'type': 'grid penalty', 'driver': 'LEC', 'severity_score': 6},
            {'type': 'warning', 'driver': 'HAM', 'severity_score': 2}
        ]
        
        sample_driver_incidents = {
            'VER': 3, 'LEC': 2, 'HAM': 2, 'RUS': 1, 'SAI': 1
        }
        
        # 測試 Safety Periods 數據更新
        safety_widget = SafetyPeriodsWidget()
        safety_widget.update_safety_periods_data(sample_safety_periods)
        print("✅ SafetyPeriodsWidget 數據更新成功")
        print(f"   - 表格行數: {safety_widget.safety_table.rowCount()}")
        
        # 測試 Penalties 數據更新
        penalties_widget = PenaltiesSummaryWidget()
        penalties_widget.update_penalties_data(sample_penalties)
        print("✅ PenaltiesSummaryWidget 數據更新成功")
        
        # 測試 Chart 數據更新
        chart_widget = DriverIncidentBarChart()
        chart_widget.update_chart_data(sample_driver_incidents)
        print("✅ DriverIncidentBarChart 數據更新成功")
        print(f"   - 圖表文字長度: {len(chart_widget.chart_area.text())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 數據更新測試失敗: {e}")
        traceback.print_exc()
        return False

def test_accident_statistics_widget_integration():
    """階段 4: AccidentStatisticsWidget 整合測試"""
    print("\n" + "=" * 60)
    print("階段 4: AccidentStatisticsWidget 整合測試")
    print("=" * 60)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentStatisticsWidget
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建數據管理器
        data_manager = AccidentDataManager()
        
        # 創建 AccidentStatisticsWidget
        stats_widget = AccidentStatisticsWidget(data_manager)
        print("✅ AccidentStatisticsWidget 創建成功")
        
        # 檢查新組件是否正確整合
        assert hasattr(stats_widget, 'driver_chart'), "Missing driver_chart"
        assert hasattr(stats_widget, 'safety_periods_widget'), "Missing safety_periods_widget"  
        assert hasattr(stats_widget, 'penalties_summary_widget'), "Missing penalties_summary_widget"
        print("✅ 所有新 Widget 組件都已正確整合")
        
        # 檢查新的數據更新方法
        assert hasattr(stats_widget, 'update_driver_incident_chart'), "Missing update_driver_incident_chart method"
        assert hasattr(stats_widget, 'update_safety_periods_data'), "Missing update_safety_periods_data method"
        assert hasattr(stats_widget, 'update_penalties_summary_data'), "Missing update_penalties_summary_data method"
        print("✅ 所有新數據更新方法都已實現")
        
        # 測試示例數據更新
        sample_json_data = {
            'data': {
                'all_incidents': [
                    {'driver_code': 'VER', 'message': 'Track limits violation'},
                    {'driver_code': 'LEC', 'message': 'Unsafe release'},
                    {'driver_code': 'VER', 'message': 'Collision'}
                ],
                'safety_periods': [
                    {'type': 'SC', 'start_lap': 12, 'end_lap': 15, 'reason': 'Debris'}
                ],
                'penalties': [
                    {'type': 'time penalty', 'driver': 'VER', 'severity_score': 8}
                ]
            }
        }
        
        stats_widget.update_statistics_data(sample_json_data)
        print("✅ AccidentStatisticsWidget 數據更新測試成功")
        
        return True
        
    except Exception as e:
        print(f"❌ AccidentStatisticsWidget 整合測試失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """主要測試流程"""
    print("🏎️ F1T Accident Analysis 改良 B 設計測試")
    print("測試新的 SafetyPeriodsWidget、PenaltiesSummaryWidget 和 DriverIncidentBarChart")
    print()
    
    # 執行所有測試階段
    results = []
    
    results.append(("Import 測試", test_import()))
    results.append(("Widget 初始化測試", test_widget_initialization()))
    results.append(("數據更新測試", test_data_update()))
    results.append(("AccidentStatisticsWidget 整合測試", test_accident_statistics_widget_integration()))
    
    # 測試結果總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！改良 B 設計實現成功")
        return 0
    else:
        print("⚠️ 部分測試失敗，需要修正")
        return 1

if __name__ == "__main__":
    sys.exit(main())