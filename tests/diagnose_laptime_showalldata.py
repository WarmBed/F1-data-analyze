"""
診斷 Lap Time Box Plot 的實際問題

可能的問題場景：
1. Widget 被重新創建
2. hidden_drivers 在某處被重置
3. 主 GUI 調用鏈斷裂
"""

print("=" * 80)
print("Lap Time Box Plot - Show All Data 功能診斷")
print("=" * 80)

print("\n[步驟 1] 檢查 Lap Time Box Plot 的架構模式")
print("-" * 80)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
        LapTimeBoxPlotAnalysis,
        LapBoxPlotAnalysisModule
    )
    print("✅ 成功導入 Lap Time Box Plot 類別")
    
    # 檢查繼承關係
    print(f"\nLapTimeBoxPlotAnalysis 基類: {LapTimeBoxPlotAnalysis.__bases__}")
    print(f"LapBoxPlotAnalysisModule 基類: {LapBoxPlotAnalysisModule.__bases__}")
    
    # 檢查是否有 reset_chart_view 方法
    has_reset_in_main = hasattr(LapTimeBoxPlotAnalysis, 'reset_chart_view')
    has_reset_in_module = hasattr(LapBoxPlotAnalysisModule, 'reset_chart_view')
    
    print(f"\nLapTimeBoxPlotAnalysis 有 reset_chart_view: {has_reset_in_main}")
    print(f"LapBoxPlotAnalysisModule 有 reset_chart_view: {has_reset_in_module}")
    
    if has_reset_in_main:
        print("✅ LapTimeBoxPlotAnalysis.reset_chart_view 存在")
    else:
        print("❌ LapTimeBoxPlotAnalysis.reset_chart_view 不存在")
    
    if has_reset_in_module:
        print("✅ LapBoxPlotAnalysisModule.reset_chart_view 存在（繼承）")
    else:
        print("❌ LapBoxPlotAnalysisModule.reset_chart_view 不存在")
    
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n[步驟 2] 檢查 Chart Widget 的方法")
print("-" * 80)

try:
    from modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_chart_widget import (
        LapTimeBoxPlotChartWidget
    )
    print("✅ 成功導入 LapTimeBoxPlotChartWidget")
    
    # 檢查方法
    has_show_all = hasattr(LapTimeBoxPlotChartWidget, 'show_all_drivers')
    has_hidden_drivers = 'hidden_drivers' in dir(LapTimeBoxPlotChartWidget)
    
    print(f"\nLapTimeBoxPlotChartWidget 有 show_all_drivers: {has_show_all}")
    print(f"LapTimeBoxPlotChartWidget 有 hidden_drivers: {has_hidden_drivers}")
    
    if has_show_all:
        print("✅ show_all_drivers 方法存在")
    else:
        print("❌ show_all_drivers 方法不存在")
    
    # 創建測試實例
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    widget = LapTimeBoxPlotChartWidget()
    print(f"\n測試實例創建成功")
    print(f"  - hidden_drivers 初始值: {widget.hidden_drivers}")
    print(f"  - hidden_drivers 類型: {type(widget.hidden_drivers)}")
    
    # 測試隱藏功能
    widget._hide_driver('VER')
    print(f"  - 隱藏 VER 後: {widget.hidden_drivers}")
    
    # 測試恢復功能
    widget.show_all_drivers()
    print(f"  - show_all_drivers 後: {widget.hidden_drivers}")
    
    if len(widget.hidden_drivers) == 0:
        print("✅ Widget 層級的 show_all_drivers 功能正常")
    else:
        print("❌ Widget 層級的 show_all_drivers 功能失效")
    
except Exception as e:
    print(f"❌ Widget 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n[步驟 3] 檢查主 GUI 調用鏈")
print("-" * 80)

# 模擬主 GUI 的調用
class MockSubWindow:
    def __init__(self, analysis_module):
        self.analysis_module = analysis_module
    
    def widget(self):
        if hasattr(self.analysis_module, 'get_widget'):
            return self.analysis_module.get_widget()
        return self.analysis_module

try:
    # 創建 MDI 實例
    mdi = LapTimeBoxPlotAnalysis(parent=None)
    print("✅ 創建 LapTimeBoxPlotAnalysis 實例")
    
    # 初始化
    if mdi.initialize_module():
        print("✅ MDI 初始化成功")
    else:
        print("❌ MDI 初始化失敗")
        sys.exit(1)
    
    # 創建模擬子視窗
    sub_window = MockSubWindow(mdi)
    print("✅ 創建模擬子視窗")
    
    # 模擬主 GUI 的調用邏輯
    print("\n模擬主 GUI show_all_data_in_current_tab 調用:")
    
    # 步驟 1: 檢查是否有 analysis_module
    if hasattr(sub_window, 'analysis_module'):
        analysis_module = sub_window.analysis_module
        print(f"  ✅ 找到 analysis_module: {analysis_module.__class__.__name__}")
    else:
        print("  ❌ 沒有 analysis_module")
        sys.exit(1)
    
    # 步驟 2: 檢查是否有 reset_chart_view
    if hasattr(analysis_module, 'reset_chart_view'):
        print(f"  ✅ analysis_module 有 reset_chart_view 方法")
        
        # 先隱藏一個車手
        if hasattr(mdi, 'chart_widget') and mdi.chart_widget:
            print("\n  測試隱藏功能:")
            mdi.chart_widget._hide_driver('VER')
            print(f"    - 隱藏 VER 後: {mdi.chart_widget.hidden_drivers}")
            
            # 調用 reset_chart_view
            print("\n  調用 reset_chart_view:")
            analysis_module.reset_chart_view()
            
            # 檢查結果
            print(f"    - 調用後 hidden_drivers: {mdi.chart_widget.hidden_drivers}")
            
            if len(mdi.chart_widget.hidden_drivers) == 0:
                print("\n  ✅ 主 GUI 調用鏈正常工作")
            else:
                print("\n  ❌ 主 GUI 調用鏈失效")
        else:
            print("  ⚠️  chart_widget 不存在，無法測試")
    else:
        print(f"  ❌ analysis_module 沒有 reset_chart_view 方法")
    
except Exception as e:
    print(f"❌ 調用鏈測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("診斷完成")
print("=" * 80)
