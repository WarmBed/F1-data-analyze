#!/usr/bin/env python3
"""
統一遙測圖表組件測試腳本
驗證重構後的組件是否正常工作
"""

import sys
import os

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_universal_chart_import():
    """測試統一圖表組件導入"""
    try:
        from modules.universal_telemetry_chart_widget import UniversalTelemetryChartWidget
        print("✅ 統一遙測圖表組件導入成功")
        return True
    except Exception as e:
        print(f"❌ 統一遙測圖表組件導入失敗: {e}")
        return False

def test_speed_chart_import():
    """測試速度圖表組件導入"""
    try:
        from modules.speed_analysis_chart_widget_refactored import SpeedAnalysisChartWidget
        print("✅ 重構版速度分析圖表組件導入成功")
        return True
    except Exception as e:
        print(f"❌ 重構版速度分析圖表組件導入失敗: {e}")
        return False

def test_rpm_chart_import():
    """測試RPM圖表組件導入"""
    try:
        from modules.rpm_analysis_chart_widget_refactored import RPMAnalysisChartWidget
        print("✅ 重構版RPM分析圖表組件導入成功")
        return True
    except Exception as e:
        print(f"❌ 重構版RPM分析圖表組件導入失敗: {e}")
        return False

def test_chart_creation():
    """測試圖表組件創建"""
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.speed_analysis_chart_widget_refactored import SpeedAnalysisChartWidget
        from modules.rpm_analysis_chart_widget_refactored import RPMAnalysisChartWidget
        
        # 初始化QApplication（如果還沒有）
        import sys
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # 創建速度圖表
        speed_chart = SpeedAnalysisChartWidget()
        print("✅ 速度分析圖表組件創建成功")
        
        # 創建RPM圖表  
        rpm_chart = RPMAnalysisChartWidget()
        print("✅ RPM分析圖表組件創建成功")
        
        return True
    except Exception as e:
        print(f"❌ 圖表組件創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_compatibility():
    """測試API兼容性"""
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.speed_analysis_chart_widget_refactored import SpeedAnalysisChartWidget
        from modules.rpm_analysis_chart_widget_refactored import RPMAnalysisChartWidget
        
        # 初始化QApplication（如果還沒有）
        import sys
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # 測試速度圖表API
        speed_chart = SpeedAnalysisChartWidget()
        if hasattr(speed_chart, 'set_speed_data'):
            print("✅ 速度圖表 set_speed_data API 存在")
        else:
            print("❌ 速度圖表 set_speed_data API 缺失")
            return False
        
        # 測試RPM圖表API
        rpm_chart = RPMAnalysisChartWidget()
        if hasattr(rpm_chart, 'set_rpm_data'):
            print("✅ RPM圖表 set_rpm_data API 存在")
        else:
            print("❌ RPM圖表 set_rpm_data API 缺失")
            return False
            
        return True
    except Exception as e:
        print(f"❌ API兼容性測試失敗: {e}")
        return False

def run_all_tests():
    """執行所有測試"""
    print("🧪 開始統一遙測圖表組件測試")
    print("=" * 50)
    
    tests = [
        ("統一圖表組件導入", test_universal_chart_import),
        ("速度圖表組件導入", test_speed_chart_import),
        ("RPM圖表組件導入", test_rpm_chart_import),
        ("圖表組件創建", test_chart_creation),
        ("API兼容性", test_api_compatibility),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 測試: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 測試失敗")
        except Exception as e:
            print(f"❌ {test_name} 測試異常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！重構成功！")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查問題")
        return False

if __name__ == "__main__":
    run_all_tests()
