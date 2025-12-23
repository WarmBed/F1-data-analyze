#!/usr/bin/env python3
"""詳細調試範圍內的速度分佈"""

import sys
import pandas as pd

def debug_speed_distribution():
    """檢查範圍內的速度分佈"""
    try:
        from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
        from CLI_modules.cli.analyzer.all_drivers_straight_line_speed import AllDriversStraightLineSpeedAnalysis
        
        # 載入數據
        data_loader = CompatibleF1DataLoader()
        data_loader.load_race_data(2025, "Singapore", "R")
        
        # 創建分析器
        analyzer = AllDriversStraightLineSpeedAnalysis(data_loader, year=2025, race="Singapore", session="R")
        
        # 找最速圈和主直線段
        result = analyzer._find_overall_fastest_lap()
        driver, lap_obj = result
        reference_segment = analyzer._identify_main_straight_position(driver, lap_obj)
        
        print(f"主直線段: {reference_segment['segment_distance_start']:.1f}m - {reference_segment['segment_distance_end']:.1f}m")
        print(f"起始速度: {reference_segment['segment_start_speed']:.1f} km/h")
        print(f"最高速度: {reference_segment['segment_max_speed']:.1f} km/h")
        print()
        
        # 獲取 HAM 的數據
        session = data_loader.session
        ham_laps = session.laps.pick_driver('HAM')
        valid_laps = ham_laps[ham_laps['LapTime'].notna()]
        fastest_lap_idx = valid_laps['LapTime'].idxmin()
        fastest_lap = valid_laps.loc[fastest_lap_idx]
        lap_number = int(fastest_lap['LapNumber'])
        
        ham_driver_laps = session.laps.pick_driver('HAM')
        ham_lap_obj = ham_driver_laps.pick_lap(lap_number)
        car_data = analyzer._extract_car_data(ham_lap_obj)
        
        # 過濾範圍內的數據
        distances = pd.to_numeric(car_data["Distance"], errors="coerce")
        speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
        
        mask = (distances >= reference_segment['segment_distance_start']) & (distances <= reference_segment['segment_distance_end'])
        range_data = car_data[mask].copy()
        range_data['Distance'] = distances[mask]
        range_data['Speed'] = speeds[mask]
        
        print(f"範圍內數據點數: {len(range_data)}")
        print(f"\n速度分佈:")
        print(f"  最小速度: {range_data['Speed'].min():.1f} km/h")
        print(f"  最大速度: {range_data['Speed'].max():.1f} km/h")
        print(f"  平均速度: {range_data['Speed'].mean():.1f} km/h")
        print()
        
        # 檢查是否有 100 km/h
        has_100 = (range_data['Speed'] <= 100).any()
        print(f"範圍內是否有 ≤100 km/h 的點: {has_100}")
        
        if not has_100:
            print("\n⚠️ 問題確認：範圍內最小速度都超過 100 km/h！")
            print("這就是為什麼找不到 100 km/h 的原因。")
            print()
            print("解決方案：")
            print("1. 向前擴展搜索範圍（超出主直線段起點）")
            print("2. 或者接受起始速度不是 100 km/h，改用實際起始速度計算")
        
        # 顯示前10個數據點
        print(f"\n前10個數據點（從範圍起點開始）:")
        print(range_data[['Distance', 'Speed']].head(10).to_string(index=False))
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_speed_distribution()
