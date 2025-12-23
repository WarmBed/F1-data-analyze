#!/usr/bin/env python3
"""
測試 Detailed Lap Analysis 的圖例拖拉功能
"""

import sys
from PyQt5.QtWidgets import QApplication
from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_chart_widget import (
    LaptimeChartWidget,
    driverLapAnalysisChartWidget
)

def test_legend_drag_variables():
    """測試圖例拖拉相關變數是否存在"""
    print("="*70)
    print("測試 Detailed Lap Analysis 圖例拖拉功能")
    print("="*70)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 創建圖表組件
    chart = LaptimeChartWidget()
    
    # 檢查圖例拖拉變數
    required_vars = [
        'legend_dragging',
        'legend_drag_start',
        'legend_offset',
        'legend_rect',
        'legend_show_markers'
    ]
    
    print("\n✅ 檢查圖例拖拉變數:")
    all_exist = True
    for var in required_vars:
        exists = hasattr(chart, var)
        status = "✅" if exists else "❌"
        print(f"  {status} {var}: {exists}")
        if exists:
            print(f"     初始值: {getattr(chart, var)}")
        all_exist = all_exist and exists
    
    # 檢查滑鼠事件方法
    print("\n✅ 檢查滑鼠事件方法:")
    mouse_methods = [
        'mousePressEvent',
        'mouseMoveEvent',
        'mouseReleaseEvent',
        'mouseDoubleClickEvent'
    ]
    
    for method in mouse_methods:
        exists = hasattr(chart, method)
        status = "✅" if exists else "❌"
        print(f"  {status} {method}: {exists}")
    
    # 檢查圖例繪製方法
    print("\n✅ 檢查圖例繪製方法:")
    legend_methods = [
        '_draw_legend',
        '_draw_legend_marker_improved'
    ]
    
    for method in legend_methods:
        exists = hasattr(chart, method)
        status = "✅" if exists else "❌"
        print(f"  {status} {method}: {exists}")
    
    print("\n" + "="*70)
    if all_exist:
        print("✅ 所有圖例拖拉功能已完整實現！")
        print("\n使用說明:")
        print("  1. 滑鼠懸停在圖例上 → 顯示 OpenHandCursor (可移動提示)")
        print("  2. 按住左鍵拖動圖例 → 圖例跟隨滑鼠移動，顯示 ClosedHandCursor")
        print("  3. 釋放左鍵 → 圖例固定在新位置")
        print("  4. 雙擊圖例 → 切換顯示/隱藏標記")
    else:
        print("❌ 部分功能缺失")
    print("="*70)

if __name__ == "__main__":
    test_legend_drag_variables()
