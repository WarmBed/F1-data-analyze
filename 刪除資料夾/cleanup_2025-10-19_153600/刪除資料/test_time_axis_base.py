#!/usr/bin/env python3
"""
時間軸功能測試腳本
====================

測試 TelemetryChartWidgetBase 的時間軸切換功能

測試項目：
1. 基類屬性初始化
2. set_data() 方法接受 time_data 參數
3. toggle_time_axis() 切換功能
4. 時間軸標題更新
5. 數據點 X 座標切換

Author: F1T Team
Date: 2025-10-11
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def test_base_class_attributes():
    """測試基類屬性"""
    print("\n" + "="*60)
    print("測試 1: 基類屬性初始化")
    print("="*60)
    
    try:
        from modules.gui.base.universal_chart_widget_base import TelemetryChartWidgetBase
        
        # 創建基類實例
        chart = TelemetryChartWidgetBase(chart_type='line')
        
        # 檢查新增屬性
        assert hasattr(chart, 'distance_data'), "❌ 缺少 distance_data 屬性"
        assert hasattr(chart, 'time_data'), "❌ 缺少 time_data 屬性"
        assert hasattr(chart, 'use_time_axis'), "❌ 缺少 use_time_axis 屬性"
        assert hasattr(chart, 'time_axis_available'), "❌ 缺少 time_axis_available 屬性"
        
        # 檢查初始值
        assert chart.distance_data == [], "❌ distance_data 初始值不正確"
        assert chart.time_data == [], "❌ time_data 初始值不正確"
        assert chart.use_time_axis == False, "❌ use_time_axis 初始值應為 False"
        assert chart.time_axis_available == False, "❌ time_axis_available 初始值應為 False"
        
        print("✅ 所有屬性初始化正確")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_set_data_with_time():
    """測試 set_data() 方法接受時間數據"""
    print("\n" + "="*60)
    print("測試 2: set_data() 方法時間數據支援")
    print("="*60)
    
    try:
        from modules.gui.base.universal_chart_widget_base import TelemetryChartWidgetBase
        
        # 創建基類實例
        chart = TelemetryChartWidgetBase(chart_type='line')
        
        # 準備測試數據
        distance_data = [0, 100, 200, 300, 400, 500]
        time_data = [0, 1.5, 3.0, 4.5, 6.0, 7.5]
        series_data = {
            'driver1': [250, 280, 300, 290, 270, 260],
            'driver2': [240, 270, 295, 285, 265, 255]
        }
        
        # 調用 set_data（不傳時間數據）
        chart.set_data(
            x_data=distance_data,
            series_data=series_data
        )
        
        assert chart.distance_data == distance_data, "❌ distance_data 設置失敗"
        assert chart.time_data == [], "❌ 未傳遞時間數據時應為空"
        assert chart.time_axis_available == False, "❌ 未傳遞時間數據時應不可用"
        
        print("✅ 不傳時間數據時正常工作")
        
        # 調用 set_data（傳遞時間數據）
        chart.set_data(
            x_data=distance_data,
            series_data=series_data,
            time_data=time_data
        )
        
        assert chart.distance_data == distance_data, "❌ distance_data 設置失敗"
        assert chart.time_data == time_data, "❌ time_data 設置失敗"
        assert chart.time_axis_available == True, "❌ 時間數據傳遞後應可用"
        
        print("✅ 傳遞時間數據成功")
        
        # 測試長度不匹配的時間數據
        wrong_time_data = [0, 1.5, 3.0]  # 只有 3 個點，應該有 6 個
        chart.set_data(
            x_data=distance_data,
            series_data=series_data,
            time_data=wrong_time_data
        )
        
        assert chart.time_axis_available == False, "❌ 長度不匹配時應拒絕時間數據"
        
        print("✅ 長度驗證正常")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_toggle_time_axis():
    """測試 toggle_time_axis() 切換功能"""
    print("\n" + "="*60)
    print("測試 3: toggle_time_axis() 切換功能")
    print("="*60)
    
    try:
        from modules.gui.base.universal_chart_widget_base import TelemetryChartWidgetBase
        
        # 創建基類實例
        chart = TelemetryChartWidgetBase(chart_type='line')
        
        # 準備測試數據
        distance_data = [0, 100, 200, 300, 400, 500]
        time_data = [0, 1.5, 3.0, 4.5, 6.0, 7.5]
        series_data = {
            'driver1': [250, 280, 300, 290, 270, 260],
            'driver2': [240, 270, 295, 285, 265, 255]
        }
        
        # 設置數據（包含時間數據）
        chart.set_data(
            x_data=distance_data,
            series_data=series_data,
            time_data=time_data
        )
        
        # 測試初始狀態（距離軸）
        assert chart.get_current_x_axis_mode() == "distance", "❌ 初始模式應為距離軸"
        print("✅ 初始模式：距離軸")
        
        # 切換到時間軸
        success = chart.toggle_time_axis(True)
        assert success == True, "❌ 切換到時間軸應成功"
        assert chart.get_current_x_axis_mode() == "time", "❌ 切換後應為時間軸"
        print("✅ 切換到時間軸成功")
        
        # 切換回距離軸
        success = chart.toggle_time_axis(False)
        assert success == True, "❌ 切換回距離軸應成功"
        assert chart.get_current_x_axis_mode() == "distance", "❌ 切換後應為距離軸"
        print("✅ 切換回距離軸成功")
        
        # 測試沒有時間數據時切換失敗
        chart2 = TelemetryChartWidgetBase(chart_type='line')
        chart2.set_data(
            x_data=distance_data,
            series_data=series_data
            # 不傳 time_data
        )
        
        success = chart2.toggle_time_axis(True)
        assert success == False, "❌ 沒有時間數據時切換應失敗"
        assert chart2.get_current_x_axis_mode() == "distance", "❌ 切換失敗後應保持距離軸"
        print("✅ 沒有時間數據時拒絕切換")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_x_axis_title_update():
    """測試 X 軸標題更新"""
    print("\n" + "="*60)
    print("測試 4: X 軸標題自動更新")
    print("="*60)
    
    try:
        from modules.gui.base.universal_chart_widget_base import TelemetryChartWidgetBase
        
        # 創建基類實例
        chart = TelemetryChartWidgetBase(chart_type='line')
        
        # 準備測試數據
        distance_data = [0, 100, 200]
        time_data = [0, 1.5, 3.0]
        series_data = {'driver1': [250, 280, 300]}
        
        chart.set_data(
            x_data=distance_data,
            series_data=series_data,
            time_data=time_data
        )
        
        # 檢查初始標題（距離軸）
        initial_title = chart.x_axis_title
        print(f"📏 初始標題: {initial_title}")
        assert "距離" in initial_title or "Distance" in initial_title, "❌ 初始標題應包含距離"
        
        # 切換到時間軸
        chart.toggle_time_axis(True)
        time_title = chart.x_axis_title
        print(f"⏱️ 時間軸標題: {time_title}")
        assert "時間" in time_title or "Time" in time_title, "❌ 時間軸標題應包含時間"
        
        # 切換回距離軸
        chart.toggle_time_axis(False)
        distance_title = chart.x_axis_title
        print(f"📏 距離軸標題: {distance_title}")
        assert "距離" in distance_title or "Distance" in distance_title, "❌ 距離軸標題應包含距離"
        
        print("✅ X 軸標題自動更新正常")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_point_x_coordinate():
    """測試數據點 X 座標切換"""
    print("\n" + "="*60)
    print("測試 5: 數據點 X 座標切換")
    print("="*60)
    
    try:
        from modules.gui.base.universal_chart_widget_base import TelemetryChartWidgetBase
        
        # 創建基類實例
        chart = TelemetryChartWidgetBase(chart_type='line')
        
        # 準備測試數據
        distance_data = [0, 100, 200]
        time_data = [0, 1.5, 3.0]
        series_data = {'driver1': [250, 280, 300]}
        
        chart.set_data(
            x_data=distance_data,
            series_data=series_data,
            time_data=time_data
        )
        
        # 檢查初始 X 座標（應為距離）
        if chart.series_list:
            first_series = chart.series_list[0]
            first_point_x = first_series.data[0].x
            assert first_point_x == distance_data[0], f"❌ 初始 X 座標應為距離: {first_point_x} != {distance_data[0]}"
            print(f"✅ 初始狀態：X={first_point_x} (距離)")
            
            # 切換到時間軸
            chart.toggle_time_axis(True)
            first_point_x = first_series.data[0].x
            assert first_point_x == time_data[0], f"❌ 時間軸 X 座標應為時間: {first_point_x} != {time_data[0]}"
            print(f"✅ 時間軸：X={first_point_x} (時間)")
            
            # 切換回距離軸
            chart.toggle_time_axis(False)
            first_point_x = first_series.data[0].x
            assert first_point_x == distance_data[0], f"❌ 距離軸 X 座標應為距離: {first_point_x} != {distance_data[0]}"
            print(f"✅ 距離軸：X={first_point_x} (距離)")
        
        print("✅ 數據點 X 座標切換正常")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print("\n" + "="*70)
    print(" 時間軸功能測試 - TelemetryChartWidgetBase")
    print("="*70)
    
    # 初始化 Qt 應用（GUI 組件需要）
    app = QApplication(sys.argv)
    
    results = []
    
    # 執行所有測試
    results.append(("屬性初始化", test_base_class_attributes()))
    results.append(("set_data() 時間數據", test_set_data_with_time()))
    results.append(("toggle_time_axis() 切換", test_toggle_time_axis()))
    results.append(("X 軸標題更新", test_x_axis_title_update()))
    results.append(("數據點座標切換", test_data_point_x_coordinate()))
    
    # 總結報告
    print("\n" + "="*70)
    print(" 測試總結")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*70)
    print(f" 總計: {passed}/{total} 通過 ({passed/total*100:.0f}%)")
    print("="*70 + "\n")
    
    if passed == total:
        print("🎉 所有測試通過！時間軸功能實現正確！")
        return 0
    else:
        print(f"⚠️ {total - passed} 個測試失敗，請檢查實現。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
