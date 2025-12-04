#!/usr/bin/env python3
"""
下載 2023 和 2024 賽季的排位賽 (Q) 數據
使用 FastF1 API 獲取真實的排位賽結果
"""

import fastf1
import json
from pathlib import Path
from datetime import datetime

# 設定 FastF1 緩存
PROJECT_ROOT = Path(__file__).parent.parent
CACHE_DIR = PROJECT_ROOT / "f1_analysis_cache"
CACHE_DIR.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

JSON_DIR = PROJECT_ROOT / "json"

# 2023 和 2024 賽程
RACES_2023 = [
    "Bahrain", "Saudi Arabia", "Australia", "Azerbaijan", "Miami",
    "Monaco", "Spain", "Canada", "Austria", "Great Britain",
    "Hungary", "Belgium", "Netherlands", "Italy", "Singapore",
    "Japan", "Qatar", "United States", "Mexico", "Brazil",
    "Las Vegas", "Abu Dhabi"
]

RACES_2024 = [
    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
    "Miami", "Emilia Romagna", "Monaco", "Canada", "Spain",
    "Austria", "Great Britain", "Hungary", "Belgium", "Netherlands",
    "Italy", "Azerbaijan", "Singapore", "United States", "Mexico",
    "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
]


def download_qualifying_data(year: int, races: list):
    """
    下載指定年份的所有排位賽數據
    """
    print(f"\n{'='*60}")
    print(f"📥 下載 {year} 賽季排位賽數據")
    print(f"{'='*60}")
    
    all_data = {}
    
    for race_name in races:
        print(f"\n🏎️ {race_name}...")
        
        try:
            # 載入排位賽 (不載入 telemetry 和 weather)
            session = fastf1.get_session(year, race_name, 'Q')
            session.load(telemetry=False, weather=False, messages=False)
            
            # 獲取排位結果
            results = session.results
            
            if results is None or len(results) == 0:
                print(f"   ⚠️ 無排位賽數據")
                continue
            
            q_data = {
                "metadata": {
                    "year": year,
                    "race": race_name,
                    "session": "Q",
                    "download_time": datetime.now().isoformat(),
                    "has_actual_results": True,
                },
                "results": []
            }
            
            for idx, row in results.iterrows():
                driver_data = {
                    "position": int(row['Position']) if not pd.isna(row['Position']) else 99,
                    "driver": row['Abbreviation'],
                    "driver_number": str(row['DriverNumber']),
                    "team": row['TeamName'],
                    "q1_time": str(row['Q1']) if not pd.isna(row['Q1']) else None,
                    "q2_time": str(row['Q2']) if not pd.isna(row['Q2']) else None,
                    "q3_time": str(row['Q3']) if not pd.isna(row['Q3']) else None,
                }
                q_data["results"].append(driver_data)
            
            # 排序
            q_data["results"].sort(key=lambda x: x["position"])
            
            all_data[race_name] = q_data
            
            pole_driver = q_data["results"][0]["driver"] if q_data["results"] else "?"
            print(f"   ✅ {len(q_data['results'])} 車手, 桿位: {pole_driver}")
            
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
            continue
    
    return all_data


def download_race_results(year: int, races: list):
    """
    下載指定年份的所有比賽結果
    """
    print(f"\n{'='*60}")
    print(f"📥 下載 {year} 賽季比賽結果")
    print(f"{'='*60}")
    
    all_data = {}
    
    for race_name in races:
        print(f"\n🏁 {race_name}...")
        
        try:
            # 載入比賽 (不載入 telemetry 和 weather)
            session = fastf1.get_session(year, race_name, 'R')
            session.load(telemetry=False, weather=False, messages=False)
            
            results = session.results
            
            if results is None or len(results) == 0:
                print(f"   ⚠️ 無比賽數據")
                continue
            
            r_data = {
                "metadata": {
                    "year": year,
                    "race": race_name,
                    "session": "R",
                    "download_time": datetime.now().isoformat(),
                },
                "results": []
            }
            
            for idx, row in results.iterrows():
                driver_data = {
                    "position": int(row['Position']) if not pd.isna(row['Position']) else 99,
                    "grid_position": int(row['GridPosition']) if not pd.isna(row['GridPosition']) else 99,
                    "driver": row['Abbreviation'],
                    "driver_number": str(row['DriverNumber']),
                    "team": row['TeamName'],
                    "status": row['Status'] if 'Status' in row else None,
                    "points": float(row['Points']) if not pd.isna(row['Points']) else 0,
                }
                r_data["results"].append(driver_data)
            
            # 排序
            r_data["results"].sort(key=lambda x: x["position"])
            
            all_data[race_name] = r_data
            
            winner = r_data["results"][0]["driver"] if r_data["results"] else "?"
            print(f"   ✅ {len(r_data['results'])} 車手, 冠軍: {winner}")
            
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
            continue
    
    return all_data


def save_data(data: dict, year: int, session_type: str):
    """儲存數據到 JSON"""
    output_file = JSON_DIR / f"fastf1_{year}_{session_type}_results.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 已儲存: {output_file}")
    return output_file


def main():
    import pandas as pd
    global pd
    
    print("🏎️ FastF1 排位賽和比賽數據下載器")
    print("=" * 60)
    
    # 下載 2023 數據
    q_2023 = download_qualifying_data(2023, RACES_2023)
    r_2023 = download_race_results(2023, RACES_2023)
    
    if q_2023:
        save_data(q_2023, 2023, "qualifying")
    if r_2023:
        save_data(r_2023, 2023, "race")
    
    # 下載 2024 數據
    q_2024 = download_qualifying_data(2024, RACES_2024)
    r_2024 = download_race_results(2024, RACES_2024)
    
    if q_2024:
        save_data(q_2024, 2024, "qualifying")
    if r_2024:
        save_data(r_2024, 2024, "race")
    
    # 統計
    print("\n" + "=" * 60)
    print("📊 下載統計")
    print("=" * 60)
    print(f"2023 Q: {len(q_2023)} 場")
    print(f"2023 R: {len(r_2023)} 場")
    print(f"2024 Q: {len(q_2024)} 場")
    print(f"2024 R: {len(r_2024)} 場")


if __name__ == "__main__":
    import pandas as pd
    main()
