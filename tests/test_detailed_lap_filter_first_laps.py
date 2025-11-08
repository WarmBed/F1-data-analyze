"""測試 Detailed Lap Analysis 模組的 Filter First Laps 功能"""

import sys
from PyQt5.QtWidgets import QApplication
from core.gui_settings_manager import gui_settings_manager

def test_detailed_lap_analysis_filter():
    """測試 Detailed Lap Analysis 的過濾功能"""
    
    print("=" * 80)
    print("[TEST] Detailed Lap Analysis - Filter First Laps Integration")
    print("=" * 80)
    
    # 1. 驗證設定結構
    print("\n[階段 1] 驗證核心設定")
    settings = gui_settings_manager.get_boxplot_settings()
    
    required_keys = ["filter_pit_laps", "filter_yellow_flags", "filter_red_flags", "filter_first_laps"]
    for key in required_keys:
        if key in settings:
            print(f"  ✅ {key}: {settings[key]}")
        else:
            print(f"  ❌ {key}: 缺少！")
            return False
    
    # 2. 測試設定更新
    print("\n[階段 2] 測試設定更新")
    print("  → 設定 filter_first_laps=False")
    gui_settings_manager.update_boxplot_settings(filter_first_laps=False)
    
    updated = gui_settings_manager.get_boxplot_settings()
    if updated.get("filter_first_laps") == False:
        print(f"  ✅ 設定更新成功: {updated.get('filter_first_laps')}")
    else:
        print(f"  ❌ 設定更新失敗")
        return False
    
    # 3. 恢復預設值
    print("\n[階段 3] 恢復預設值")
    gui_settings_manager.update_boxplot_settings(filter_first_laps=True)
    
    restored = gui_settings_manager.get_boxplot_settings()
    if restored.get("filter_first_laps") == True:
        print(f"  ✅ 恢復預設值成功: {restored.get('filter_first_laps')}")
    else:
        print(f"  ❌ 恢復預設值失敗")
        return False
    
    # 4. 測試 Detailed Lap Analysis 模組整合
    print("\n[階段 4] 測試模組整合")
    try:
        from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi import (
            driverLapAnalysisDataManager
        )
        
        print("  ✅ 成功導入 driverLapAnalysisDataManager")
        
        # 檢查 filter_settings
        data_manager = driverLapAnalysisDataManager(parent=None)
        
        if "filter_first_laps" in data_manager.filter_settings:
            print(f"  ✅ filter_settings 包含 filter_first_laps: {data_manager.filter_settings['filter_first_laps']}")
        else:
            print(f"  ❌ filter_settings 缺少 filter_first_laps")
            return False
        
        # 測試 update_filter_settings 方法
        print("\n  測試 update_filter_settings 方法...")
        success = data_manager.update_filter_settings(
            filter_first_laps=False,
            sync_global=False,
            emit_signal=False
        )
        
        if success and data_manager.filter_settings.get("filter_first_laps") == False:
            print(f"  ✅ update_filter_settings 成功更新")
        else:
            print(f"  ❌ update_filter_settings 失敗")
            return False
        
    except Exception as exc:
        print(f"  ❌ 模組整合測試失敗: {exc}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 測試其他組件
    print("\n[階段 5] 測試其他組件")
    
    try:
        from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_chart_widget import (
            driverLapAnalysisChartWidget
        )
        print("  ✅ 成功導入 driverLapAnalysisChartWidget")
        
        chart_widget = driverLapAnalysisChartWidget()
        if hasattr(chart_widget, 'filter_first_laps'):
            print(f"  ✅ Chart Widget 有 filter_first_laps 屬性: {chart_widget.filter_first_laps}")
        else:
            print(f"  ❌ Chart Widget 缺少 filter_first_laps 屬性")
            return False
        
    except Exception as exc:
        print(f"  ❌ Chart Widget 測試失敗: {exc}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        from modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget import (
            LapTimeBoxPlotWidget
        )
        print("  ✅ 成功導入 LapTimeBoxPlotWidget")
        
        boxplot_widget = LapTimeBoxPlotWidget()
        if hasattr(boxplot_widget, 'filter_first_laps'):
            print(f"  ✅ BoxPlot Widget 有 filter_first_laps 屬性: {boxplot_widget.filter_first_laps}")
        else:
            print(f"  ❌ BoxPlot Widget 缺少 filter_first_laps 屬性")
            return False
        
    except Exception as exc:
        print(f"  ❌ BoxPlot Widget 測試失敗: {exc}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("[PASS] All tests passed! Detailed Lap Analysis integration complete!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        if test_detailed_lap_analysis_filter():
            print("\n[SUCCESS] Detailed Lap Analysis - Filter First Laps integration complete!")
            sys.exit(0)
        else:
            print("\n[FAIL] Tests failed")
            sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Test failed: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
