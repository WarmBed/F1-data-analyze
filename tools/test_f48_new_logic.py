#!/usr/bin/env python3
"""
測試 Function 48 的新邏輯
驗證：最速圈 → 尾速最高直線段 → 該段內的加速時間
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
from CLI_modules.cli.analyzer.all_drivers_straight_line_speed import AllDriversStraightLineSpeedAnalysis


def test_new_logic(year, race, session, test_drivers=None):
    """測試新邏輯"""
    print(f"\n{'='*80}")
    print(f"[TEST] Function 48 New Logic Test")
    print(f"[RACE] {year} {race} {session}")
    print(f"{'='*80}\n")
    
    # 載入數據
    print(f"[LOAD] Loading data...")
    loader = CompatibleF1DataLoader()
    loader.load_race_data(year, race, session)
    
    # 執行分析
    print(f"[ANALYZE] Running analysis...")
    analyzer = AllDriversStraightLineSpeedAnalysis(loader)
    result = analyzer.run(include_chart=True)
    
    if not result["success"]:
        print(f"[ERROR] Analysis failed: {result.get('message')}")
        return
    
    print(f"[SUCCESS] Analysis complete\n")
    
    # 顯示結果
    driver_speeds = result["data"]["driver_speeds"]
    
    print(f"{'='*80}")
    print(f"[SUMMARY]")
    print(f"{'='*80}")
    print(f"Total drivers: {len(driver_speeds)}")
    
    if result["data"].get("summary"):
        summary = result["data"]["summary"]
        print(f"Fastest driver: {summary.get('fastest_driver')} ({summary.get('fastest_speed_kmh')} km/h)")
        print(f"Fastest lap: Lap {summary.get('fastest_lap')}")
        
        if "acceleration_performance" in summary:
            acc = summary["acceleration_performance"]
            print(f"\nAcceleration Performance:")
            print(f"  Fastest acceleration: {acc.get('fastest_acceleration_driver')} ({acc.get('fastest_acceleration_time')}s)")
            print(f"  Drivers with accel data: {acc.get('drivers_with_acceleration_data')}/{len(driver_speeds)}")
            print(f"  Average acceleration time: {acc.get('average_acceleration_time')}s")
    
    print(f"\n{'='*80}")
    print(f"[DRIVER DETAILS]")
    print(f"{'='*80}\n")
    
    # 過濾要顯示的車手
    if test_drivers:
        display_drivers = [d for d in driver_speeds if d["driver"] in test_drivers]
    else:
        display_drivers = driver_speeds[:10]  # 只顯示前10名
    
    for i, driver_data in enumerate(display_drivers, 1):
        driver = driver_data["driver"]
        team = driver_data.get("team", "Unknown")
        max_speed = driver_data["max_speed_kmh"]
        lap_num = driver_data.get("lap_number", "N/A")
        
        print(f"[{i:2d}] {driver:3s} ({team})")
        print(f"     Max speed: {max_speed:.1f} km/h (Lap {lap_num})")
        
        if "acceleration_100_300" in driver_data and driver_data["acceleration_100_300"]:
            acc = driver_data["acceleration_100_300"]
            time = acc.get("time_seconds", "N/A")
            dist = acc.get("distance_meters", "N/A")
            avg_acc = acc.get("avg_acceleration_ms2", "N/A")
            
            # 檢查時間是否合理
            if isinstance(time, (int, float)):
                if 2.0 <= time <= 10.0:
                    status = "[OK]"
                else:
                    status = "[WARN]"
            else:
                status = "[FAIL]"
            
            print(f"     Accel time: {status} {time}s (100->250 km/h)")
            if dist != "N/A":
                print(f"     Accel distance: {dist}m")
            if avg_acc != "N/A":
                print(f"     Avg acceleration: {avg_acc} m/s^2")
            
            # 顯示直線段信息
            if "segment_start_speed" in acc and "segment_max_speed" in acc:
                print(f"     Straight segment: {acc['segment_start_speed']:.1f} -> {acc['segment_max_speed']:.1f} km/h")
        else:
            print(f"     Accel time: [FAIL] No data")
        
        print()
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # 測試 Singapore R (用戶報告的問題賽事)
    test_new_logic(2025, "Singapore", "R", test_drivers=["HAM", "VER", "LEC", "NOR", "PIA"])
    
    # 測試 China R
    # test_new_logic(2025, "China", "R", test_drivers=["HAM", "VER", "LEC"])
    
    # 測試 Japan Q
    # test_new_logic(2025, "Japan", "Q", test_drivers=["VER", "NOR", "LEC"])
