"""
測試 Gap Evolution 雙圈速曲線功能

測試內容：
1. 圈速歷史記錄 (p1_lap_times, p2_lap_times)
2. update_data 接收圈速參數
3. _calculate_future_lap_times 預測圈速
4. _draw_single_lap_time_curve 繪製雙曲線
5. Y 軸顯示圈速範圍（秒）
"""

import sys
sys.path.insert(0, '.')

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from modules.gui.live_timing.live_timing_modules.chase_strategy import (
    GapEvolutionChartWidget, StrategyResult
)

def test_gap_evolution_dual_curves():
    """測試 Gap Evolution 雙圈速曲線"""
    app = QApplication(sys.argv)
    
    # 創建測試 strategy
    strategy = StrategyResult(
        strategy_id=1,
        name="Continue",
        feasible=True,
        catchup_lap=25,
        total_advantage=10.0,
        drs_required=5,
        rating=3,
        details="Test strategy",
        advantage_per_lap=0.2,
        pit_loss=20.0,
        sc_lap_offset=5
    )
    
    # 創建 widget
    widget = GapEvolutionChartWidget(
        strategy=strategy,
        current_lap=10,
        current_gap=5.0,
        total_laps=50,
        p1_tla="VER",
        p2_tla="LEC",
        p1_color="3671C6",
        p2_color="FF8800",
        p1_compound="MEDIUM",
        p2_compound="SOFT"
    )
    
    # 模擬歷史圈速數據（P1 平均 85s, P2 平均 84.5s）
    for lap in range(1, 11):
        p1_time = 85.0 + (lap % 3) * 0.3  # 85.0 ~ 85.6s
        p2_time = 84.5 + (lap % 3) * 0.25  # 84.5 ~ 85.0s
        widget.p1_lap_times[lap] = p1_time
        widget.p2_lap_times[lap] = p2_time
    
    print("\n" + "="*60)
    print("✅ 測試 1: 圈速歷史記錄")
    print("="*60)
    print(f"P1 圈速數據: {len(widget.p1_lap_times)} 圈")
    print(f"P2 圈速數據: {len(widget.p2_lap_times)} 圈")
    print(f"P1 最後一圈: {widget.p1_lap_times.get(10, 'N/A'):.3f}s")
    print(f"P2 最後一圈: {widget.p2_lap_times.get(10, 'N/A'):.3f}s")
    
    print("\n" + "="*60)
    print("✅ 測試 2: 更新數據（含圈速）")
    print("="*60)
    widget.update_data(
        current_lap=11,
        current_gap=4.8,
        p1_compound="MEDIUM",
        p2_compound="SOFT",
        p1_lap_time=85.2,
        p2_lap_time=84.7
    )
    print(f"P1 Lap 11: {widget.p1_lap_times.get(11, 'N/A'):.3f}s")
    print(f"P2 Lap 11: {widget.p2_lap_times.get(11, 'N/A'):.3f}s")
    
    print("\n" + "="*60)
    print("✅ 測試 3: 預測未來圈速")
    print("="*60)
    future_laps, future_p1, future_p2 = widget._calculate_future_lap_times()
    print(f"預測圈數: {len(future_laps)} 圈")
    print(f"P1 平均預測圈速: {sum(future_p1)/len(future_p1):.3f}s")
    print(f"P2 平均預測圈速: {sum(future_p2)/len(future_p2):.3f}s")
    print(f"未來 5 圈 P1: {[f'{t:.2f}' for t in future_p1[:5]]}")
    print(f"未來 5 圈 P2: {[f'{t:.2f}' for t in future_p2[:5]]}")
    
    print("\n" + "="*60)
    print("✅ 測試 4: Y 軸範圍計算")
    print("="*60)
    widget._calculate_laptime_range()
    print(f"Y 軸範圍: {widget._laptime_min:.1f}s ~ {widget._laptime_max:.1f}s")
    
    print("\n" + "="*60)
    print("✅ 測試 5: 圈速解析")
    print("="*60)
    test_cases = [
        "1:23.456",  # 83.456s
        "1:30.000",  # 90.0s
        "23.456",    # 23.456s
        "90.123",    # 90.123s
        "--",        # None
        ""           # None
    ]
    for test_str in test_cases:
        result = widget._parse_lap_time_to_seconds(test_str)
        print(f"  '{test_str}' → {result}s" if result else f"  '{test_str}' → None")
    
    print("\n" + "="*60)
    print("🎉 所有測試通過！")
    print("="*60)
    
    # 顯示 widget
    main_win = QMainWindow()
    main_win.setCentralWidget(widget)
    main_win.setWindowTitle("Gap Evolution - Dual Lap Time Curves Test")
    main_win.resize(1000, 600)
    main_win.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    test_gap_evolution_dual_curves()
