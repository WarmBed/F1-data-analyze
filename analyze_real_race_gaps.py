"""
分析真實 F1 賽事數據中的 P1 vs P20 差距
用於校準模擬器的差距參數
"""
import json
import os
from pathlib import Path

def analyze_race_gaps():
    """分析多場真實賽事的最終差距"""
    json_dir = Path("json")
    
    # 搜索所有 detailed_laptime_analysis 檔案 (正賽)
    race_files = list(json_dir.glob("detailed_laptime_analysis_*_R_all_drivers.json"))
    
    print(f"找到 {len(race_files)} 個正賽數據檔案")
    print("=" * 80)
    
    all_gaps = []
    
    for race_file in race_files[:10]:  # 分析前10場
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
            
            # 計算每位車手的總時間
            driver_total_times = {}
            
            for driver, driver_info in drivers_data.items():
                if not driver_info.get("success"):
                    continue
                    
                laps = driver_info.get("detailed_lap_data", [])
                if not laps:
                    continue
                
                total_time = 0
                valid_laps = 0
                
                for lap in laps:
                    lap_seconds = lap.get("lap_time_seconds")
                    if lap_seconds and isinstance(lap_seconds, (int, float)) and lap_seconds > 0:
                        # 排除進站圈 (通常時間較長)
                        pit_status = lap.get("pit_status", "")
                        if not pit_status:
                            total_time += lap_seconds
                            valid_laps += 1
                
                if valid_laps > 0:
                    driver_total_times[driver] = {
                        "total_time": total_time,
                        "valid_laps": valid_laps,
                        "avg_lap": total_time / valid_laps
                    }
            
            if len(driver_total_times) < 2:
                continue
            
            # 按總時間排序
            sorted_drivers = sorted(
                driver_total_times.items(),
                key=lambda x: x[1]["total_time"]
            )
            
            # 計算 P1 vs 各位置的差距
            p1_driver, p1_data = sorted_drivers[0]
            p1_time = p1_data["total_time"]
            
            print(f"\n{year} {race} Grand Prix:")
            print(f"  P1 {p1_driver}: {p1_time:.1f}s ({p1_data['valid_laps']} laps, avg {p1_data['avg_lap']:.3f}s)")
            
            gaps_in_race = []
            for i, (driver, d_data) in enumerate(sorted_drivers[1:min(20, len(sorted_drivers))], 2):
                gap = d_data["total_time"] - p1_time
                gaps_in_race.append({
                    "position": i,
                    "driver": driver,
                    "gap_to_p1": gap,
                    "laps": d_data["valid_laps"]
                })
                if i <= 5 or i == 10 or i == 15 or i == 20:
                    print(f"  P{i} {driver}: +{gap:.1f}s")
            
            all_gaps.append({
                "race": f"{year} {race}",
                "gaps": gaps_in_race
            })
            
        except Exception as e:
            print(f"Error processing {race_file}: {e}")
            continue
    
    # 統計分析
    print("\n" + "=" * 80)
    print("統計分析 (基於真實賽事數據):")
    print("=" * 80)
    
    # 按位置統計平均差距
    position_gaps = {}
    for race_data in all_gaps:
        for gap_info in race_data["gaps"]:
            pos = gap_info["position"]
            gap = gap_info["gap_to_p1"]
            if pos not in position_gaps:
                position_gaps[pos] = []
            position_gaps[pos].append(gap)
    
    print("\n各位置與P1的平均差距 (秒):")
    for pos in sorted(position_gaps.keys()):
        gaps = position_gaps[pos]
        avg_gap = sum(gaps) / len(gaps)
        min_gap = min(gaps)
        max_gap = max(gaps)
        print(f"  P{pos}: 平均 {avg_gap:6.1f}s, 範圍 [{min_gap:5.1f}s ~ {max_gap:6.1f}s]")
    
    # 計算建議參數
    print("\n" + "=" * 80)
    print("建議的模擬器參數 (基於真實數據):")
    print("=" * 80)
    
    if 10 in position_gaps and 5 in position_gaps:
        avg_p5_gap = sum(position_gaps[5]) / len(position_gaps[5])
        avg_p10_gap = sum(position_gaps[10]) / len(position_gaps[10])
        
        # 每位置差距 = (P10 gap - P5 gap) / 5
        per_position_delta = (avg_p10_gap - avg_p5_gap) / 5
        print(f"  每位置平均差距: {per_position_delta:.2f}s")
        
        # 換算成每圈差距 (假設 53 圈)
        per_lap_per_position = per_position_delta / 53
        print(f"  每圈每位置差距: {per_lap_per_position:.4f}s")
    
    return all_gaps

if __name__ == "__main__":
    analyze_race_gaps()
