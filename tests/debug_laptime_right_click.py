"""
調試 Lap Time Box Plot 右鍵選單問題

檢查點：
1. mousePressEvent 是否被觸發
2. _detect_hovered_driver 是否正確檢測
3. _show_context_menu 是否被調用
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPoint
from modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_chart_widget import LapTimeBoxPlotChartWidget

# 創建測試數據
test_data = {
    'driver_laptimes': {
        'VER': [86.5, 87.2, 86.8, 87.0],
        'LEC': [87.1, 87.5, 87.3, 87.2],
        'HAM': [87.8, 88.0, 87.9, 88.1]
    },
    'statistics': {
        'VER': {'median': 86.9, 'mean': 86.875, 'q1': 86.65, 'q3': 87.1, 'iqr': 0.45, 'count': 4},
        'LEC': {'median': 87.25, 'mean': 87.275, 'q1': 87.15, 'q3': 87.4, 'iqr': 0.25, 'count': 4},
        'HAM': {'median': 87.95, 'mean': 87.95, 'q1': 87.85, 'q3': 88.05, 'iqr': 0.20, 'count': 4}
    },
    'metadata': {'year': 2025, 'race': 'Japan', 'session': 'R'}
}

def test_right_click():
    app = QApplication(sys.argv)
    
    # 創建 Widget
    widget = LapTimeBoxPlotChartWidget()
    widget.resize(800, 600)
    widget.update_data(test_data)
    widget.show()
    
    print("\n" + "="*60)
    print("Lap Time Box Plot 右鍵選單測試")
    print("="*60)
    
    # 等待 Widget 完全渲染
    app.processEvents()
    
    # 測試點 1: 檢查 chart_rect
    print(f"\n📊 圖表區域: {widget.chart_rect}")
    print(f"   - Left: {widget.chart_rect.left()}")
    print(f"   - Top: {widget.chart_rect.top()}")
    print(f"   - Width: {widget.chart_rect.width()}")
    print(f"   - Height: {widget.chart_rect.height()}")
    
    # 測試點 2: 計算第一個箱型圖的位置
    drivers = sorted(widget.driver_laptimes.keys())
    n_drivers = len(drivers)
    box_spacing = widget.chart_rect.width() / (n_drivers + 1)
    box_width = min(40, box_spacing * 0.6)
    
    print(f"\n📦 箱型圖佈局:")
    print(f"   - 車手數量: {n_drivers}")
    print(f"   - 箱型圖間距: {box_spacing:.2f}")
    print(f"   - 箱型圖寬度: {box_width:.2f}")
    
    # 測試點 3: 模擬點擊第一個箱型圖
    for i, driver in enumerate(drivers):
        x_center = widget.chart_rect.left() + (i + 1) * box_spacing
        y_center = widget.chart_rect.center().y()
        
        print(f"\n   {driver}: 中心點 ({x_center:.0f}, {y_center:.0f})")
        
        # 測試 _detect_hovered_driver
        test_point = QPoint(int(x_center), int(y_center))
        detected = widget._detect_hovered_driver(test_point)
        print(f"      - 檢測結果: {detected}")
        
        if detected != driver:
            print(f"      ❌ 錯誤！預期 {driver}，實際 {detected}")
        else:
            print(f"      ✅ 檢測正確")
    
    # 測試點 4: 檢查 mousePressEvent 的連接
    print(f"\n🔗 事件連接檢查:")
    print(f"   - mousePressEvent 方法存在: {hasattr(widget, 'mousePressEvent')}")
    print(f"   - _show_context_menu 方法存在: {hasattr(widget, '_show_context_menu')}")
    print(f"   - _hide_driver 方法存在: {hasattr(widget, '_hide_driver')}")
    
    # 測試點 5: 手動調用 _show_context_menu
    print(f"\n🧪 手動測試 _show_context_menu:")
    from PyQt5.QtGui import QMouseEvent
    from PyQt5.QtCore import QEvent
    
    # 創建模擬事件（右鍵點擊第一個箱型圖中心）
    x_center = widget.chart_rect.left() + box_spacing
    y_center = widget.chart_rect.center().y()
    test_pos = QPoint(int(x_center), int(y_center))
    
    print(f"   - 測試點: ({test_pos.x()}, {test_pos.y()})")
    
    # 檢測車手
    detected_driver = widget._detect_hovered_driver(test_pos)
    print(f"   - 檢測到車手: {detected_driver}")
    
    if detected_driver:
        print(f"   - 嘗試顯示右鍵選單...")
        # 注意：實際的右鍵選單需要真實的滑鼠事件，這裡只能檢查方法是否存在
        print(f"   - _show_context_menu 可調用: {callable(widget._show_context_menu)}")
    else:
        print(f"   ❌ 無法檢測到車手，無法測試選單")
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)
    
    sys.exit(0)

if __name__ == "__main__":
    test_right_click()
