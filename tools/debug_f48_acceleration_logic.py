#!/usr/bin/env python3
"""
Function 48 - 時間計算驗證腳本
用於調試加速時間計算是否正確
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from CLI_modules.cli.core.data_loader import F1DataLoader
from CLI_modules.cli.analyzer.all_drivers_straight_line_speed import AllDriversStraightLineSpeedAnalysis


def debug_single_driver_acceleration(year, race, session, driver_code):
    """調試單一車手的加速時間計算"""
    print(f"\n{'='*80}")
    print(f"🔍 調試 Function 48 - {driver_code} 加速時間計算")
    print(f"📅 賽事: {year} {race} {session}")
    print(f"{'='*80}\n")
    
    # 載入數據
    loader = F1DataLoader(year, race, session)
    loader.load_session_data()
    
    # 獲取車手圈數
    laps = loader.laps
    driver_laps = laps.pick_driver(driver_code)
    
    if driver_laps.empty:
        print(f"❌ 找不到 {driver_code} 的圈數數據")
        return
    
    print(f"✅ {driver_code} 總圈數: {len(driver_laps)}")
    print(f"\n{'='*80}")
    print(f"圈速分析:")
    print(f"{'='*80}")
    
    # 顯示所有圈的圈速
    lap_times = []
    for idx, lap in driver_laps.iterlaps():
        lap_num = lap.LapNumber
        lap_time = lap.LapTime
        
        if lap_time is not None and hasattr(lap_time, 'total_seconds'):
            lap_time_sec = lap_time.total_seconds()
            lap_times.append((lap_num, lap_time_sec))
            print(f"  圈 {lap_num:2d}: {lap_time_sec:7.3f}s")
    
    # 找到最速圈
    if lap_times:
        fastest_lap_num, fastest_time = min(lap_times, key=lambda x: x[1])
        print(f"\n🏆 最速圈: 圈 {fastest_lap_num} ({fastest_time:.3f}s)")
    else:
        print(f"\n❌ 沒有有效圈速數據")
        return
    
    print(f"\n{'='*80}")
    print(f"遍歷所有圈，分析加速性能:")
    print(f"{'='*80}\n")
    
    # 遍歷所有圈，分析加速性能
    acceleration_records = []
    
    for idx, lap in driver_laps.iterlaps():
        lap_num = lap.LapNumber
        
        try:
            car_data = lap.get_car_data()
            if car_data is None or "Speed" not in car_data.columns or "Time" not in car_data.columns:
                print(f"  圈 {lap_num:2d}: ⚠️ 沒有遙測數據")
                continue
            
            car_data = car_data.add_distance()
            
            # 計算加速時間（複製 Function 48 的邏輯）
            speeds = car_data["Speed"].dropna()
            if speeds.empty or len(speeds) < 10:
                print(f"  圈 {lap_num:2d}: ⚠️ 速度數據點不足")
                continue
            
            # 找到 100km/h 和 300km/h 的索引
            speed_100_idx = None
            speed_300_idx = None
            
            for i in speeds.index:
                speed = speeds[i]
                if speed >= 100 and speed_100_idx is None:
                    speed_100_idx = i
                if speed >= 300 and speed_300_idx is None:
                    speed_300_idx = i
                    break
            
            if speed_100_idx is None or speed_300_idx is None:
                print(f"  圈 {lap_num:2d}: ⚠️ 未達到 100-300 km/h 速度範圍")
                continue
            
            # 獲取時間數據
            time_100 = car_data.loc[speed_100_idx, "Time"]
            time_300 = car_data.loc[speed_300_idx, "Time"]
            
            # 處理時間數據
            if hasattr(time_100, "total_seconds"):
                time_100_sec = time_100.total_seconds()
            else:
                time_100_sec = float(time_100)
            
            if hasattr(time_300, "total_seconds"):
                time_300_sec = time_300.total_seconds()
            else:
                time_300_sec = float(time_300)
            
            time_diff = time_300_sec - time_100_sec
            
            # 獲取最高速度
            max_speed = speeds.max()
            
            # 獲取距離數據
            dist_100 = car_data.loc[speed_100_idx, "Distance"] if "Distance" in car_data.columns else None
            dist_300 = car_data.loc[speed_300_idx, "Distance"] if "Distance" in car_data.columns else None
            dist_diff = dist_300 - dist_100 if (dist_100 is not None and dist_300 is not None) else None
            
            acceleration_records.append({
                "lap_num": lap_num,
                "time_diff": time_diff,
                "max_speed": max_speed,
                "dist_diff": dist_diff,
                "time_100_sec": time_100_sec,
                "time_300_sec": time_300_sec,
                "speed_100_idx": speed_100_idx,
                "speed_300_idx": speed_300_idx
            })
            
            # 檢查時間是否合理
            time_status = "✅" if 2.0 < time_diff < 15.0 else "🔴"
            
            print(f"  圈 {lap_num:2d}: {time_status} 加速時間 = {time_diff:7.3f}s, 最高速度 = {max_speed:6.1f} km/h")
            if dist_diff:
                print(f"           距離差 = {dist_diff:6.1f}m")
            print(f"           時間點: 100km/h@{time_100_sec:.3f}s → 300km/h@{time_300_sec:.3f}s")
            print(f"           索引: {speed_100_idx} → {speed_300_idx}")
            
            if time_diff <= 0 or time_diff > 20:
                print(f"           ⚠️ 警告：時間差異常！")
            
        except Exception as e:
            print(f"  圈 {lap_num:2d}: ❌ 分析失敗 - {e}")
    
    # 總結
    print(f"\n{'='*80}")
    print(f"總結:")
    print(f"{'='*80}")
    
    if acceleration_records:
        # 找到最佳加速
        best_acceleration = min(acceleration_records, key=lambda x: x["time_diff"])
        # 找到最高速度
        best_speed = max(acceleration_records, key=lambda x: x["max_speed"])
        
        print(f"\n🚀 最佳加速: 圈 {best_acceleration['lap_num']} ({best_acceleration['time_diff']:.3f}s)")
        print(f"🏎️  最高速度: 圈 {best_speed['lap_num']} ({best_speed['max_speed']:.1f} km/h)")
        
        if best_acceleration['lap_num'] == fastest_lap_num:
            print(f"✅ 最佳加速圈 = 最速圈")
        else:
            print(f"⚠️ 最佳加速圈 ≠ 最速圈 (最速圈 = 圈 {fastest_lap_num})")
        
        if best_speed['lap_num'] == fastest_lap_num:
            print(f"✅ 最高速度圈 = 最速圈")
        else:
            print(f"⚠️ 最高速度圈 ≠ 最速圈 (最速圈 = 圈 {fastest_lap_num})")
        
        # 顯示所有加速時間
        print(f"\n加速時間分佈:")
        sorted_records = sorted(acceleration_records, key=lambda x: x["time_diff"])
        for rec in sorted_records:
            marker = "🏆" if rec["lap_num"] == best_acceleration["lap_num"] else "  "
            fastest_marker = "⭐" if rec["lap_num"] == fastest_lap_num else "  "
            print(f"  {marker}{fastest_marker} 圈 {rec['lap_num']:2d}: {rec['time_diff']:7.3f}s (速度: {rec['max_speed']:6.1f} km/h)")
    else:
        print(f"\n❌ 沒有有效的加速數據")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    # 測試 Singapore R - HAM
    debug_single_driver_acceleration(2025, "Singapore", "R", "HAM")
    
    # 測試 China R - HAM
    # debug_single_driver_acceleration(2025, "China", "R", "HAM")
