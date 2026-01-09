"""
分析各賽道的 P10 vs P1 差距特性
目標: 建立賽道專屬的 race_pace_delta 係數
"""
import json
from pathlib import Path
from collections import defaultdict

def analyze_track_specific_gaps():
    """分析各賽道的差距特性"""
    json_dir = Path("json")
    
    # 搜索所有 detailed_laptime_analysis 檔案 (正賽)
    race_files = list(json_dir.glob("detailed_laptime_analysis_*_R_all_drivers.json"))
    
    print(f"找到 {len(race_files)} 個正賽數據檔案")
    print("=" * 80)
    
    # 按賽道分類統計
    track_stats = defaultdict(list)
    
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
            
            # 找出比賽總圈數
            max_laps = 0
            for driver_info in drivers_data.values():
                if driver_info.get("success"):
                    total_laps = driver_info.get("total_laps", 0)
                    if total_laps > max_laps:
                        max_laps = total_laps
            
            # 只分析完整比賽 (40+ 圈)
            if max_laps < 40:
                continue
            
            # 計算每位車手的總時間
            driver_race_times = {}
            
            for driver, driver_info in drivers_data.items():
                if not driver_info.get("success"):
                    continue
                    
                laps = driver_info.get("detailed_lap_data", [])
                total_laps = driver_info.get("total_laps", 0)
                
                if not laps or total_laps < max_laps - 3:
                    continue
                
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
                continue
            
            # 按總時間排序
            sorted_drivers = sorted(
                driver_race_times.items(),
                key=lambda x: x[1]["total_time"]
            )
            
            p1_driver, p1_data = sorted_drivers[0]
            p1_time = p1_data["total_time"]
            
            # 計算各位置差距
            gaps = {}
            for i, (driver, data) in enumerate(sorted_drivers):
                pos = i + 1
                gap = data["total_time"] - p1_time
                gaps[pos] = gap
            
            # 計算每圈平均差距 (position * delta_per_lap)
            if 10 in gaps:
                gap_per_lap_p10 = gaps[10] / max_laps / 10  # 每個位置每圈差距
                
                track_stats[race].append({
                    "year": year,
                    "total_laps": max_laps,
                    "p10_gap": gaps.get(10, 0),
                    "p5_gap": gaps.get(5, 0),
                    "gap_per_position_per_lap": gap_per_lap_p10,
                    "finishers": len(sorted_drivers)
                })
            
        except Exception as e:
            print(f"處理 {race_file} 時發生錯誤: {e}")
    
    # 輸出各賽道統計
    print("\n各賽道 race_pace_delta 分析:")
    print("=" * 80)
    print(f"{'賽道':<25} {'場次':>6} {'P10差距':>10} {'每位每圈':>10} {'建議係數':>10}")
    print("-" * 80)
    
    track_coefficients = {}
    
    for track, races in sorted(track_stats.items()):
        if len(races) >= 1:
            avg_p10_gap = sum(r["p10_gap"] for r in races) / len(races)
            avg_gap_per_pos = sum(r["gap_per_position_per_lap"] for r in races) / len(races)
            avg_laps = sum(r["total_laps"] for r in races) / len(races)
            
            # 建議係數 = 平均差距 / (位置 * 圈數)
            # 目標: P10 累計差距 ≈ 真實值
            suggested_coef = avg_p10_gap / (10 * avg_laps) if avg_laps > 0 else 0.20
            
            track_coefficients[track] = {
                "avg_p10_gap": avg_p10_gap,
                "avg_gap_per_position_per_lap": avg_gap_per_pos,
                "suggested_coefficient": suggested_coef,
                "race_count": len(races),
                "avg_laps": avg_laps
            }
            
            print(f"{track:<25} {len(races):>6} {avg_p10_gap:>10.1f}s {avg_gap_per_pos:>10.3f}s {suggested_coef:>10.3f}")
    
    # 分類賽道類型
    print("\n\n賽道分類建議:")
    print("=" * 80)
    
    street_circuits = ["Monaco", "Singapore", "Las Vegas", "Azerbaijan", "Saudi Arabia"]
    high_speed = ["Italy", "Belgium", "Mexico", "Great Britain"]
    high_degradation = ["Bahrain", "Spain", "China"]
    
    # 計算各類別平均
    for category, tracks in [
        ("街道賽道 (低差距)", street_circuits),
        ("高速賽道 (高差距)", high_speed),
        ("高降解賽道", high_degradation)
    ]:
        matching = [c for t, c in track_coefficients.items() if any(s in t for s in tracks)]
        if matching:
            avg_coef = sum(m["suggested_coefficient"] for m in matching) / len(matching)
            print(f"{category}: 建議係數 = {avg_coef:.3f}")
    
    # 輸出 JSON 格式的賽道係數
    print("\n\n賽道係數 JSON 格式:")
    print("-" * 80)
    
    output = {
        "description": "基於 2023-2025 真實數據分析的賽道專屬 race_pace_delta 係數",
        "default_coefficient": 0.20,
        "track_coefficients": {}
    }
    
    for track, data in track_coefficients.items():
        # 標準化賽道名稱
        normalized_track = track.replace(" ", "_").lower()
        output["track_coefficients"][normalized_track] = {
            "coefficient": round(data["suggested_coefficient"], 3),
            "avg_p10_gap": round(data["avg_p10_gap"], 1),
            "sample_races": data["race_count"]
        }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))
    
    # 儲存到 JSON 檔案
    output_file = Path("json/track_gap_coefficients.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n已儲存到 {output_file}")

if __name__ == "__main__":
    analyze_track_specific_gaps()
