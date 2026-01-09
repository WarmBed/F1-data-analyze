#!/usr/bin/env python3
"""
Test TrafficHeatmapWidget 創建和基本功能
"""

import sys
from PyQt5.QtWidgets import QApplication
from strategy_simulator.gui.widgets.traffic_heatmap_widget import TrafficHeatmapWidget


def test_widget_creation():
    """測試 Widget 創建"""
    print("[TEST] Creating TrafficHeatmapWidget...")
    widget = TrafficHeatmapWidget()
    print(f"[TEST] ✅ Widget created: {widget.__class__.__name__}")
    print(f"[TEST] ✅ Minimum size: {widget.minimumSize()}")
    print(f"[TEST] ✅ Cell width: {widget.cell_width}, Cell height: {widget.cell_height}")
    return widget


def test_data_update():
    """測試數據更新"""
    print("\n[TEST] Testing data update...")
    
    # 創建測試數據
    drivers_data = [
        {
            "driver_code": "VER",
            "final_position": 1,
            "lap_states": {
                1: 0, 2: 0, 3: 1, 4: 1, 5: 0,  # 0=clean, 1=traffic, 2=sc_vsc
                6: 1, 7: 0, 8: 0, 9: 2, 10: 0
            },
            "traffic_stats": {
                "blocked_laps": 3,
                "clean_laps": 6,
                "sc_vsc_laps": 1
            }
        },
        {
            "driver_code": "LEC",
            "final_position": 2,
            "lap_states": {
                1: 0, 2: 1, 3: 1, 4: 0, 5: 1,
                6: 1, 7: 1, 8: 0, 9: 2, 10: 0
            },
            "traffic_stats": {
                "blocked_laps": 5,
                "clean_laps": 4,
                "sc_vsc_laps": 1
            }
        },
        {
            "driver_code": "NOR",
            "final_position": 3,
            "lap_states": {
                1: 1, 2: 1, 3: 1, 4: 1, 5: 1,
                6: 1, 7: 1, 8: 0, 9: 2, 10: 0
            },
            "traffic_stats": {
                "blocked_laps": 7,
                "clean_laps": 2,
                "sc_vsc_laps": 1
            }
        }
    ]
    
    widget = TrafficHeatmapWidget()
    widget.update_data(drivers_data, max_lap=10, race_info="Test Race")
    
    print(f"[TEST] ✅ Data updated: {len(widget._drivers_data)} drivers, {widget._max_lap} laps")
    print(f"[TEST] ✅ Race info: {widget._race_info}")
    
    # 驗證數據
    assert len(widget._drivers_data) == 3, "Should have 3 drivers"
    assert widget._max_lap == 10, "Should have 10 laps"
    assert widget._drivers_data[0]["driver_code"] == "VER", "First driver should be VER (P1)"
    
    print("[TEST] ✅ All data validation passed")
    return widget


def main():
    print("=" * 60)
    print("TrafficHeatmapWidget Test Suite")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    try:
        # Test 1: Widget creation
        widget1 = test_widget_creation()
        
        # Test 2: Data update
        widget2 = test_data_update()
        
        # Test 3: Show widget
        print("\n[TEST] Displaying widget...")
        widget2.resize(1000, 600)
        widget2.show()
        print("[TEST] ✅ Widget displayed")
        
        print("\n" + "=" * 60)
        print("All tests passed! ✅")
        print("=" * 60)
        
        # Keep window open for visual inspection
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"\n[TEST] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
