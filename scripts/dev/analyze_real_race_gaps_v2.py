"""
分析真實 F1 賽事數據中的 P1 vs P20 差距 (V2 - 更精確)
只分析完整比賽且排除進站圈
"""
import json
import os
from pathlib import Path

def analyze_race_gaps_v2():
    """分析多場真實賽事的最終差距 - 更精確版本"""
    json_dir = Path("json")
    
    # 搜索所有 detailed_laptime_analysis 檔案 (正賽)
    race_files = list(json_dir.glob("detailed_laptime_analysis_*_R_all_drivers.json"))
    
    print(f"找到 {len(race_files)} 個正賽數據檔案")
    print("=" * 80)
    
    valid_races = []
    
    for race_file in race_files:
        try:
            with open(race_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data.get("success"):
                continue
                
            year = data.get("year", "?")
            race = data.get("race", "?")
            drivers_data = data.get("all_drivers_detailed_laptime", {})
            
            if not drivers_data:
                continue
            
            # 找出比賽總圈數 (取最大值)
            max_laps = 0
            for driver_info in drivers_data.values():
                if driver_info.get("success"):
                    total_laps = driver_info.get("total_laps", 0)
                    if total_laps > max_laps:
                        max_laps = total_laps
            
            # 只分析完整比賽 (40+ 圈)
            if max_laps < 40:
                print(f"跳過 {year} {race}: 只有 {max_laps} 圈 (可能是縮短或中斷的比賽)")
                continue
            
            # 計算每位車手的真實差距
            driver_race_times = {}
            
            for driver, driver_info in drivers_data.items():
                if not driver_info.get("success"):
                    continue
                    
                laps = driver_info.get("detailed_lap_data", [])
                total_laps = driver_info.get("total_laps", 0)
                
                if not laps or total_laps < max_laps - 3:  # 排除退賽車手
                    continue
                
                # 計算總時間 (包括所有圈)
                total_time = 0
                for lap in laps:
                    lap_seconds = lap.get("lap_time_seconds")
                    if lap_seconds and isinstance(lap_seconds, (int, float)) and lap_seconds > 0:
                        total_time += lap_seconds
                
                if total_time > 0:
                    driver_race_times[driver] = {
                        "total_time": total_time,
                        "completed_laps": len(laps),
                        "avg_lap": total_time / len(laps) if laps else 0
                    }
            
            if len(driver_race_times) < 10:
                print(f"跳過 {year} {race}: 只有 {len(driver_race_times)} 位完賽車手")
                continue
            
            # 按總時間排序
            sorted_drivers = sorted(
                driver_race_times.items(),
                key=lambda x: x[1]["total_time"]
            )
            
            p1_driver, p1_data = sorted_drivers[0]
            p1_time = p1_data["total_time"]
            
            race_info = {
                "race": f"{year} {race}",
                "total_laps": max_laps,
                "finishers": len(sorted_drivers),
                "p1_driver": p1_driver,
                "p1_time": p1_time,
                "p1_avg_lap": p1_data["avg_lap"],
                "gaps": []
            }
            
            print(f"\n{year} {race} Grand Prix ({max_laps} laps, {len(sorted_drivers)} finishers):")
            print(f"  P1 {p1_driver}: {p1_time:.1f}s (avg {p1_data['avg_lap']:.3f}s/lap)")
            
            for i, (driver, d_data) in enumerate(sorted_drivers[1:], 2):
                gap = d_data["total_time"] - p1_time
                race_info["gaps"].append({
                    "position": i,
                    "driver": driver,
                    "gap_to_p1": gap
                })
                if i in [2, 3, 5, 10, 15, 20]:
                    print(f"  P{i} {driver}: +{gap:.1f}s")
            
            valid_races.append(race_info)
            
        except Exception as e:
            print(f"Error processing {race_file}: {e}")
            continue
    
    # 統計分析
    print("\n" + "=" * 80)
    print(f"統計分析 (基於 {len(valid_races)} 場完整比賽):")
    print("=" * 80)
    
    # 按位置統計平均差距
    position_gaps = {}
    for race_data in valid_races:
        for gap_info in race_data["gaps"]:
            pos = gap_info["position"]
            gap = gap_info["gap_to_p1"]
            if pos not in position_gaps:
                position_gaps[pos] = []
            position_gaps[pos].append(gap)
    
    print("\n各位置與P1的平均差距 (秒):")
    print("-" * 60)
    
    for pos in sorted(position_gaps.keys())[:20]:
        gaps = position_gaps[pos]
        avg_gap = sum(gaps) / len(gaps)
        min_gap = min(gaps)
        max_gap = max(gaps)
        print(f"  P{pos:2d}: 平均 {avg_gap:6.1f}s (範圍 {min_gap:5.1f}s ~ {max_gap:6.1f}s) [n={len(gaps)}]")
    
    # 計算相鄰位置差距
    print("\n相鄰位置間的平均差距:")
    print("-" * 60)
    
    position_deltas = []
    for pos in range(2, 20):
        if pos in position_gaps and pos + 1 in position_gaps:
            avg_this = sum(position_gaps[pos]) / len(position_gaps[pos])
            avg_next = sum(position_gaps[pos + 1]) / len(position_gaps[pos + 1])
            delta = avg_next - avg_this
            position_deltas.append(delta)
            if pos <= 5 or pos == 10 or pos == 15:
                print(f"  P{pos} → P{pos+1}: {delta:.2f}s")
    
    if position_deltas:
        avg_delta = sum(position_deltas) / len(position_deltas)
        print(f"\n  平均每位置差距: {avg_delta:.2f}s")
    
    # 計算建議參數
    print("\n" + "=" * 80)
    print("建議的模擬器參數 (基於真實數據):")
    print("=" * 80)
    
    if valid_races:
        # 平均比賽圈數
        avg_laps = sum(r["total_laps"] for r in valid_races) / len(valid_races)
        
        # P5 和 P10 的平均差距
        if 5 in position_gaps and 10 in position_gaps:
            avg_p5_gap = sum(position_gaps[5]) / len(position_gaps[5])
            avg_p10_gap = sum(position_gaps[10]) / len(position_gaps[10])
            avg_p20_gap = sum(position_gaps.get(20, position_gaps.get(19, [0]))) / len(position_gaps.get(20, position_gaps.get(19, [1])))
            
            print(f"\n  真實數據統計:")
            print(f"    平均比賽圈數: {avg_laps:.0f} 圈")
            print(f"    P5 與 P1 平均差距: {avg_p5_gap:.1f}s")
            print(f"    P10 與 P1 平均差距: {avg_p10_gap:.1f}s")
            print(f"    P20 與 P1 平均差距: {avg_p20_gap:.1f}s")
            
            # 計算每圈每位置差距
            per_position_gap = avg_p10_gap / 10  # P10 代表 10 個位置的累計差距
            per_lap_per_position = per_position_gap / avg_laps
            
            print(f"\n  推算參數:")
            print(f"    每位置總差距 (整場比賽): {per_position_gap:.2f}s")
            print(f"    每圈每位置差距: {per_lap_per_position:.4f}s")
            print(f"    建議 race_pace_delta 公式: 1.5 + (position * {per_lap_per_position:.4f})")
            
            # 個人變異 (從同位置的差距範圍推算)
            p5_range = max(position_gaps[5]) - min(position_gaps[5])
            print(f"\n    P5 位置差距範圍: {p5_range:.1f}s (顯示個人/策略變異)")
            individual_var_per_lap = p5_range / avg_laps / 2  # ÷2 取半徑
            print(f"    推估每圈個人變異: ±{individual_var_per_lap:.3f}s")
    
    return valid_races

if __name__ == "__main__":
    analyze_race_gaps_v2()
