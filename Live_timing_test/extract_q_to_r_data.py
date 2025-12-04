#!/usr/bin/env python3
"""
Phase 1: 真正的 Q→R 預測數據提取器

數據來源:
1. qualifying_prediction_*.json - 取得 actual_q_rank (真實 Q 排名 = Grid Position)
2. LiveF1/*_Race/LapSeries.json - 取得最後一圈位置 (完賽結果)

目標: 用 Q 數據預測 R 結果，這才是真正的預測!
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
JSON_DIR = PROJECT_ROOT / "json"
LIVEF1_DIR = JSON_DIR / "LiveF1"

# 車手代碼到車號映射 (2025賽季)
DRIVER_NUMBER_MAP = {
    "1": "VER", "4": "NOR", "81": "PIA", "16": "LEC", "63": "SAI",
    "12": "ANT", "6": "LAW", "44": "HAM", "23": "ALB", "87": "BOR",
    "10": "GAS", "14": "ALO", "30": "DOO", "22": "TSU", "55": "SAI",
    "27": "HUL", "5": "HAD", "31": "OCO", "7": "BEA", "18": "STR"
}

# 2024 車手代碼
DRIVER_NUMBER_MAP_2024 = {
    "1": "VER", "4": "NOR", "81": "PIA", "16": "LEC", "55": "SAI",
    "44": "HAM", "63": "RUS", "14": "ALO", "18": "STR", "23": "ALB",
    "22": "TSU", "3": "RIC", "77": "BOT", "24": "ZHO", "10": "GAS",
    "31": "OCO", "27": "HUL", "20": "MAG", "11": "PER", "2": "SAR"
}

# 賽道對應表 (qualifying_prediction vs LiveF1)
TRACK_MAPPING = {
    "Australia": "Australian",
    "Bahrain": "Bahrain",
    "Saudi Arabia": "Saudi_Arabian",
    "Japan": "Japanese",
    "China": "Chinese",
    "Miami": "Miami",
    "Emilia Romagna": "Emilia_Romagna",
    "Monaco": "Monaco",
    "Canada": "Canadian",
    "Spain": "Spanish",
    "Austria": "Austrian",
    "United States": "United_States",
    "Las Vegas": "Las_Vegas",
    "Brazil": "São_Paulo",
    "Mexico": "Mexico_City",
    # 2024 賽道
    "Azerbaijan": "Azerbaijan",
    "British": "British",
    "Belgian": "Belgian",
    "Dutch": "Dutch",
    "Italian": "Italian",
    "Singapore": "Singapore",
    "Hungarian": "Hungarian",
    "Qatar": "Qatar",
    "Abu Dhabi": "Abu_Dhabi",
}

# 車隊評分 (2025)
TEAM_RATINGS = {
    "Red Bull Racing": 0.95,
    "McLaren": 0.94,
    "Ferrari": 0.92,
    "Mercedes": 0.88,
    "Aston Martin": 0.80,
    "Alpine": 0.75,
    "Williams": 0.72,
    "RB": 0.70,
    "Haas": 0.68,
    "Sauber": 0.65,
    "Kick Sauber": 0.65,
}


def load_qualifying_data(year: int) -> Dict[str, Dict]:
    """
    載入排位賽數據
    返回: {race_name: {driver: q_rank}}
    """
    q_data = {}
    pattern = f"qualifying_prediction_{year}_*.json"
    
    for q_file in JSON_DIR.glob(pattern):
        try:
            with open(q_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data.get("metadata", {}).get("has_actual_results"):
                print(f"  [SKIP] {q_file.name} - 無實際結果")
                continue
            
            race_name = data["metadata"]["track"]
            q_data[race_name] = {}
            
            for pred in data.get("predictions", []):
                driver = pred.get("driver")
                q_rank = pred.get("actual_q_rank")
                team = pred.get("team")
                
                if driver and q_rank:
                    q_data[race_name][driver] = {
                        "q_rank": q_rank,
                        "team": team
                    }
            
            print(f"  [OK] {race_name}: {len(q_data[race_name])} 車手")
            
        except Exception as e:
            print(f"  [ERROR] {q_file.name}: {e}")
    
    return q_data


def load_race_results(year: int) -> Dict[str, Dict]:
    """
    從 LiveF1 LapSeries.json 載入比賽結果
    返回: {race_name: {driver: finish_position}}
    """
    race_results = {}
    livef1_year_dir = LIVEF1_DIR / str(year)
    
    if not livef1_year_dir.exists():
        print(f"  [ERROR] LiveF1/{year} 目錄不存在")
        return race_results
    
    driver_map = DRIVER_NUMBER_MAP if year >= 2025 else DRIVER_NUMBER_MAP_2024
    
    for race_dir in livef1_year_dir.iterdir():
        if not race_dir.is_dir() or not race_dir.name.endswith("_Race"):
            continue
        
        lap_series_file = race_dir / "LapSeries.json"
        if not lap_series_file.exists():
            continue
        
        try:
            with open(lap_series_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            race_name = race_dir.name.replace("_Race", "")
            records = data.get("records", [])
            
            if not records:
                continue
            
            # 找出最後一圈的位置
            final_positions = {}
            max_lap = 0
            
            for record in records:
                record_data = record.get("data", {})
                for driver_num, driver_data in record_data.items():
                    lap_pos = driver_data.get("LapPosition", {})
                    
                    # LapPosition 格式: {"圈數": "位置"} 或 ["位置"]
                    if isinstance(lap_pos, dict):
                        for lap_str, pos_str in lap_pos.items():
                            lap = int(lap_str)
                            pos = int(pos_str)
                            if lap > max_lap:
                                max_lap = lap
                            if lap == max_lap:
                                driver_code = driver_map.get(driver_num, f"#{driver_num}")
                                final_positions[driver_code] = pos
                    elif isinstance(lap_pos, list) and lap_pos:
                        pos = int(lap_pos[0])
                        final_positions[driver_map.get(driver_num, f"#{driver_num}")] = pos
            
            # 確保使用最後一圈的位置
            if final_positions:
                race_results[race_name] = final_positions
                print(f"  [OK] {race_name}: {len(final_positions)} 車手完賽, 共{max_lap}圈")
            
        except Exception as e:
            print(f"  [ERROR] {race_dir.name}: {e}")
    
    return race_results


def match_tracks(q_data: Dict, race_results: Dict) -> List[Tuple[str, str]]:
    """
    匹配 Q 數據和比賽結果的賽道名稱
    返回: [(q_track, race_track), ...]
    """
    matched = []
    
    for q_track in q_data.keys():
        # 嘗試直接映射
        if q_track in TRACK_MAPPING:
            race_track = TRACK_MAPPING[q_track]
            if race_track in race_results:
                matched.append((q_track, race_track))
                continue
        
        # 嘗試模糊匹配
        for race_track in race_results.keys():
            if q_track.lower() in race_track.lower() or race_track.lower() in q_track.lower():
                matched.append((q_track, race_track))
                break
    
    return matched


def build_training_samples(year: int, q_data: Dict, race_results: Dict) -> List[Dict]:
    """
    建立訓練樣本
    """
    samples = []
    matched_tracks = match_tracks(q_data, race_results)
    
    print(f"\n📊 {year} 年匹配的賽道: {len(matched_tracks)}")
    
    for q_track, race_track in matched_tracks:
        q_drivers = q_data[q_track]
        race_positions = race_results[race_track]
        
        # 找出完賽的車手
        for driver, q_info in q_drivers.items():
            if driver not in race_positions:
                continue
            
            grid_position = q_info["q_rank"]
            finish_position = race_positions[driver]
            team = q_info.get("team", "Unknown")
            
            # 計算特徵
            sample = {
                "year": year,
                "race": q_track,
                "driver": driver,
                "team": team,
                "grid_position": grid_position,
                "finish_position": finish_position,
                "is_winner": 1 if finish_position == 1 else 0,
                "is_podium": 1 if finish_position <= 3 else 0,
                "team_rating": TEAM_RATINGS.get(team, 0.7),
                "is_pole": 1 if grid_position == 1 else 0,
                "is_front_row": 1 if grid_position <= 2 else 0,
                "grid_advantage": (20 - grid_position) / 19,  # 歸一化
            }
            
            samples.append(sample)
    
    return samples


def calculate_driver_stats(samples: List[Dict]) -> Dict:
    """
    計算車手歷史統計數據
    """
    driver_stats = {}
    
    for sample in samples:
        driver = sample["driver"]
        if driver not in driver_stats:
            driver_stats[driver] = {
                "races": 0,
                "wins": 0,
                "podiums": 0,
                "total_finish": 0,
            }
        
        stats = driver_stats[driver]
        stats["races"] += 1
        stats["wins"] += sample["is_winner"]
        stats["podiums"] += sample["is_podium"]
        stats["total_finish"] += sample["finish_position"]
    
    # 計算比率
    for driver, stats in driver_stats.items():
        if stats["races"] > 0:
            stats["win_rate"] = stats["wins"] / stats["races"]
            stats["podium_rate"] = stats["podiums"] / stats["races"]
            stats["avg_finish"] = stats["total_finish"] / stats["races"]
        else:
            stats["win_rate"] = 0
            stats["podium_rate"] = 0
            stats["avg_finish"] = 10
    
    return driver_stats


def main():
    """
    主程序: 提取 Q→R 訓練數據
    """
    print("=" * 60)
    print("🏎️ Phase 1: 真正的 Q→R 預測數據提取")
    print("=" * 60)
    
    all_samples = []
    
    # 處理 2024 和 2025 年數據
    for year in [2024, 2025]:
        print(f"\n📅 處理 {year} 年數據...")
        
        print(f"\n  載入排位賽數據...")
        q_data = load_qualifying_data(year)
        
        print(f"\n  載入比賽結果...")
        race_results = load_race_results(year)
        
        if not q_data or not race_results:
            print(f"  [WARN] {year} 年數據不完整")
            continue
        
        samples = build_training_samples(year, q_data, race_results)
        all_samples.extend(samples)
        
        print(f"\n  ✅ {year} 年樣本數: {len(samples)}")
    
    if not all_samples:
        print("\n❌ 無法提取任何訓練數據!")
        return
    
    # 計算車手統計
    driver_stats = calculate_driver_stats(all_samples)
    
    # 更新樣本的車手統計特徵
    for sample in all_samples:
        driver = sample["driver"]
        stats = driver_stats.get(driver, {})
        sample["driver_win_rate"] = stats.get("win_rate", 0)
        sample["driver_podium_rate"] = stats.get("podium_rate", 0)
        sample["driver_avg_finish"] = stats.get("avg_finish", 10)
    
    # 儲存訓練數據
    output_data = {
        "metadata": {
            "description": "Q→R 預測訓練數據",
            "source": "qualifying_prediction + LiveF1 LapSeries",
            "created": datetime.now().isoformat(),
            "sample_count": len(all_samples),
            "years": [2024, 2025],
        },
        "samples": all_samples,
        "driver_stats": driver_stats,
    }
    
    output_file = JSON_DIR / "q_to_r_training_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n" + "=" * 60)
    print(f"✅ 訓練數據已儲存: {output_file}")
    print(f"   總樣本數: {len(all_samples)}")
    print(f"   車手數: {len(driver_stats)}")
    print("=" * 60)
    
    # 顯示樣本統計
    wins = sum(1 for s in all_samples if s["is_winner"])
    print(f"\n📊 數據統計:")
    print(f"   勝利樣本: {wins} ({wins/len(all_samples)*100:.1f}%)")
    print(f"   非勝利樣本: {len(all_samples)-wins}")
    
    # 顯示前 5 筆樣本
    print(f"\n📋 樣本預覽:")
    for i, sample in enumerate(all_samples[:5]):
        print(f"   {i+1}. {sample['year']} {sample['race']}: "
              f"{sample['driver']} G{sample['grid_position']}→P{sample['finish_position']} "
              f"({'WIN' if sample['is_winner'] else ''})")


if __name__ == "__main__":
    main()
