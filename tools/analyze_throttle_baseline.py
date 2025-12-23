#!/usr/bin/env python3
"""
分析歷史賽事數據，建立每個賽道的 full_throttle_ratio 基準值

輸出：config/throttle_baseline_database.json
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import fastf1
import numpy as np
from collections import defaultdict

# 設定 FastF1 緩存
cache_dir = project_root / "f1_analysis_cache"
cache_dir.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(cache_dir))


def analyze_session_throttle(year: int, race: str, session_type: str = "R") -> dict:
    """
    分析單場賽事的 throttle 數據
    
    Returns:
        {
            "avg_full_throttle_ratio": float,  # 平均全油門比例
            "std_full_throttle_ratio": float,  # 標準差
            "min_full_throttle_ratio": float,  # 最小值
            "max_full_throttle_ratio": float,  # 最大值
            "sample_count": int,               # 採樣圈數
            "drivers_analyzed": int            # 分析車手數
        }
    """
    try:
        print(f"[分析中] {year} {race} {session_type}...")
        
        session = fastf1.get_session(year, race, session_type)
        session.load(telemetry=True, laps=True)
        
        all_ratios = []
        drivers_analyzed = 0
        
        for driver in session.drivers:
            try:
                driver_laps = session.laps.pick_drivers(driver)
                
                # 只分析有效圈 (排除 SC、進站圈等)
                valid_laps = driver_laps[
                    (driver_laps['IsAccurate'] == True) & 
                    (driver_laps['TrackStatus'] == '1')  # 綠旗
                ]
                
                if len(valid_laps) < 3:
                    continue
                
                for _, lap in valid_laps.iterrows():
                    try:
                        # 使用 get_car_data() 而非 get_telemetry()
                        car_data = lap.get_car_data()
                        if car_data is None or len(car_data) == 0:
                            continue
                        
                        if 'Throttle' not in car_data.columns:
                            continue
                        
                        throttle = car_data['Throttle'].values
                        if len(throttle) < 100:  # 至少需要 100 個採樣點
                            continue
                        
                        # 計算 full throttle ratio (throttle >= 95%)
                        full_throttle_count = np.sum(throttle >= 95)
                        ratio = full_throttle_count / len(throttle)
                        
                        all_ratios.append(ratio)
                        
                    except Exception as e:
                        continue
                
                drivers_analyzed += 1
                
            except Exception as e:
                continue
        
        if len(all_ratios) < 10:
            print(f"  [警告] 採樣不足: {len(all_ratios)} 圈")
            return None
        
        result = {
            "avg_full_throttle_ratio": float(np.mean(all_ratios)),
            "std_full_throttle_ratio": float(np.std(all_ratios)),
            "min_full_throttle_ratio": float(np.min(all_ratios)),
            "max_full_throttle_ratio": float(np.max(all_ratios)),
            "percentile_25": float(np.percentile(all_ratios, 25)),
            "percentile_75": float(np.percentile(all_ratios, 75)),
            "sample_count": len(all_ratios),
            "drivers_analyzed": drivers_analyzed
        }
        
        print(f"  [完成] 平均={result['avg_full_throttle_ratio']:.3f}, "
              f"標準差={result['std_full_throttle_ratio']:.3f}, "
              f"樣本={result['sample_count']}")
        
        return result
        
    except Exception as e:
        print(f"  [錯誤] {e}")
        return None


def build_throttle_database():
    """
    建立 throttle baseline 資料庫
    """
    # 分析的賽事列表 (2023-2024)
    races_to_analyze = [
        # 2024 賽季
        (2024, "Bahrain", "R"),
        (2024, "Saudi Arabia", "R"),
        (2024, "Australia", "R"),
        (2024, "Japan", "R"),
        (2024, "China", "R"),
        (2024, "Miami", "R"),
        (2024, "Emilia Romagna", "R"),
        (2024, "Monaco", "R"),
        (2024, "Canada", "R"),
        (2024, "Spain", "R"),
        (2024, "Austria", "R"),
        (2024, "Great Britain", "R"),
        (2024, "Hungary", "R"),
        (2024, "Belgium", "R"),
        (2024, "Netherlands", "R"),
        (2024, "Italy", "R"),
        (2024, "Azerbaijan", "R"),
        (2024, "Singapore", "R"),
        (2024, "United States", "R"),
        (2024, "Mexico", "R"),
        (2024, "Brazil", "R"),
        (2024, "Las Vegas", "R"),
        (2024, "Qatar", "R"),
        (2024, "Abu Dhabi", "R"),
        # 2023 賽季 (補充數據)
        (2023, "Bahrain", "R"),
        (2023, "Japan", "R"),
        (2023, "Monaco", "R"),
        (2023, "Singapore", "R"),
        (2023, "Italy", "R"),
    ]
    
    # 賽道名稱映射
    track_name_mapping = {
        "Bahrain": "Bahrain",
        "Saudi Arabia": "Jeddah",
        "Australia": "Melbourne",
        "Japan": "Suzuka",
        "China": "Shanghai",
        "Miami": "Miami",
        "Emilia Romagna": "Imola",
        "Monaco": "Monaco",
        "Canada": "Montreal",
        "Spain": "Barcelona",
        "Austria": "Spielberg",
        "Great Britain": "Silverstone",
        "Hungary": "Budapest",
        "Belgium": "Spa",
        "Netherlands": "Zandvoort",
        "Italy": "Monza",
        "Azerbaijan": "Baku",
        "Singapore": "Singapore",
        "United States": "Austin",
        "Mexico": "Mexico City",
        "Brazil": "Interlagos",
        "Las Vegas": "Las Vegas",
        "Qatar": "Losail",
        "Abu Dhabi": "Yas Marina",
    }
    
    # 收集每個賽道的數據
    track_data = defaultdict(list)
    
    for year, race, session_type in races_to_analyze:
        result = analyze_session_throttle(year, race, session_type)
        if result:
            track_name = track_name_mapping.get(race, race)
            track_data[track_name].append({
                "year": year,
                "race": race,
                **result
            })
    
    # 計算每個賽道的彙總數據
    database = {
        "_metadata": {
            "version": "1.0.0",
            "description": "F1 賽道 Full Throttle Ratio 基準資料庫 - 用於省胎分析",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "sources": [
                "FastF1 Telemetry Data 2023-2024"
            ],
            "notes": {
                "avg_full_throttle_ratio": "正常推進時的平均全油門比例",
                "tire_saving_threshold": "低於此值開始計算省胎分數",
                "calculation": "SF% = max(0, (threshold - actual_ratio) / (threshold - 0.40) * 100)"
            }
        },
        "circuits": {}
    }
    
    for track_name, sessions in track_data.items():
        # 彙總多場賽事的數據
        all_avgs = [s["avg_full_throttle_ratio"] for s in sessions]
        all_stds = [s["std_full_throttle_ratio"] for s in sessions]
        
        avg_ratio = np.mean(all_avgs)
        std_ratio = np.mean(all_stds)
        
        # 省胎閾值 = 平均值 - 1.5 個標準差
        # 低於此值才開始計算省胎
        tire_saving_threshold = max(0.50, avg_ratio - 1.5 * std_ratio)
        
        database["circuits"][track_name] = {
            "avg_full_throttle_ratio": round(avg_ratio, 4),
            "std_full_throttle_ratio": round(std_ratio, 4),
            "tire_saving_threshold": round(tire_saving_threshold, 4),
            "sample_sessions": len(sessions),
            "total_laps_analyzed": sum(s["sample_count"] for s in sessions),
            "sessions": [
                {
                    "year": s["year"],
                    "avg": round(s["avg_full_throttle_ratio"], 4),
                    "std": round(s["std_full_throttle_ratio"], 4)
                }
                for s in sessions
            ]
        }
    
    # 計算全域預設值
    all_track_avgs = [t["avg_full_throttle_ratio"] for t in database["circuits"].values()]
    database["_default"] = {
        "avg_full_throttle_ratio": round(np.mean(all_track_avgs), 4),
        "std_full_throttle_ratio": round(np.std(all_track_avgs), 4),
        "tire_saving_threshold": round(np.mean(all_track_avgs) - 1.5 * np.std(all_track_avgs), 4),
        "notes": "當賽道沒有專屬數據時使用此預設值"
    }
    
    return database


def main():
    print("=" * 60)
    print("F1 Full Throttle Ratio 基準分析")
    print("=" * 60)
    
    database = build_throttle_database()
    
    # 保存到 config 目錄
    output_path = project_root / "config" / "throttle_baseline_database.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"資料庫已保存到: {output_path}")
    print(f"共分析 {len(database['circuits'])} 個賽道")
    print("=" * 60)
    
    # 輸出摘要
    print("\n賽道彙總:")
    for track, data in sorted(database["circuits"].items()):
        print(f"  {track:15s}: avg={data['avg_full_throttle_ratio']:.3f}, "
              f"threshold={data['tire_saving_threshold']:.3f}, "
              f"sessions={data['sample_sessions']}")
    
    print(f"\n預設值: avg={database['_default']['avg_full_throttle_ratio']:.3f}, "
          f"threshold={database['_default']['tire_saving_threshold']:.3f}")


if __name__ == "__main__":
    main()
