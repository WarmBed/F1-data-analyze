#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F1 勝率預測模型 - Phase 1: 訓練數據提取器
==========================================

從 LiveF1 JSON 數據中提取比賽結果，生成訓練數據。

輸出: json/race_results_training.json

作者: F1 Telemetry Station Pro
日期: 2025-11-26
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Optional

# 已知的比賽結果 (2023-2024 賽季)
# 格式: {track: [(贏家代碼, 桿位代碼), ...]}
# 這是已知的歷史數據，用於補充 LiveF1 數據不完整的部分

KNOWN_RESULTS = {
    # 2023 賽季
    2023: {
        "Bahrain": {"winner": "VER", "pole": "VER", "podium": ["VER", "PER", "ALO"]},
        "Saudi_Arabian": {"winner": "PER", "pole": "PER", "podium": ["PER", "VER", "ALO"]},
        "Australian": {"winner": "VER", "pole": "VER", "podium": ["VER", "HAM", "ALO"]},
        "Azerbaijan": {"winner": "PER", "pole": "LEC", "podium": ["PER", "VER", "LEC"]},
        "Miami": {"winner": "PER", "pole": "PER", "podium": ["PER", "VER", "ALO"]},
        "Monaco": {"winner": "VER", "pole": "VER", "podium": ["VER", "ALO", "OCO"]},
        "Spanish": {"winner": "VER", "pole": "VER", "podium": ["VER", "HAM", "RUS"]},
        "Canadian": {"winner": "VER", "pole": "VER", "podium": ["VER", "ALO", "HAM"]},
        "Austrian": {"winner": "VER", "pole": "VER", "podium": ["VER", "LEC", "PER"]},
        "British": {"winner": "VER", "pole": "VER", "podium": ["VER", "NOR", "HAM"]},
        "Hungarian": {"winner": "VER", "pole": "HAM", "podium": ["VER", "NOR", "PER"]},
        "Belgian": {"winner": "VER", "pole": "LEC", "podium": ["VER", "PER", "LEC"]},
        "Dutch": {"winner": "VER", "pole": "VER", "podium": ["VER", "ALO", "GAS"]},
        "Italian": {"winner": "VER", "pole": "SAI", "podium": ["VER", "PER", "SAI"]},
        "Singapore": {"winner": "SAI", "pole": "SAI", "podium": ["SAI", "NOR", "HAM"]},
        "Japanese": {"winner": "VER", "pole": "VER", "podium": ["VER", "NOR", "PIA"]},
        "Qatar": {"winner": "VER", "pole": "VER", "podium": ["VER", "PIA", "NOR"]},
        "United_States": {"winner": "VER", "pole": "LEC", "podium": ["VER", "HAM", "NOR"]},
        "Mexico_City": {"winner": "VER", "pole": "LEC", "podium": ["VER", "HAM", "LEC"]},
        "São_Paulo": {"winner": "VER", "pole": "VER", "podium": ["VER", "NOR", "ALO"]},
        "Las_Vegas": {"winner": "VER", "pole": "LEC", "podium": ["VER", "LEC", "PER"]},
        "Abu_Dhabi": {"winner": "VER", "pole": "VER", "podium": ["VER", "LEC", "RUS"]},
    },
    # 2024 賽季
    2024: {
        "Bahrain": {"winner": "VER", "pole": "VER", "podium": ["VER", "PER", "SAI"]},
        "Saudi_Arabian": {"winner": "VER", "pole": "VER", "podium": ["VER", "PER", "LEC"]},
        "Australian": {"winner": "SAI", "pole": "VER", "podium": ["SAI", "LEC", "NOR"]},
        "Japanese": {"winner": "VER", "pole": "VER", "podium": ["VER", "PER", "SAI"]},
        "Chinese": {"winner": "VER", "pole": "VER", "podium": ["VER", "NOR", "PER"]},
        "Miami": {"winner": "NOR", "pole": "VER", "podium": ["NOR", "VER", "LEC"]},
        "Monaco": {"winner": "LEC", "pole": "LEC", "podium": ["LEC", "PIA", "SAI"]},
        "Canadian": {"winner": "VER", "pole": "RUS", "podium": ["VER", "NOR", "RUS"]},
        "Spanish": {"winner": "VER", "pole": "NOR", "podium": ["VER", "NOR", "HAM"]},
        "Austrian": {"winner": "RUS", "pole": "VER", "podium": ["RUS", "PIA", "SAI"]},
        "British": {"winner": "HAM", "pole": "RUS", "podium": ["HAM", "VER", "NOR"]},
        "Hungarian": {"winner": "PIA", "pole": "NOR", "podium": ["PIA", "NOR", "LEC"]},
        "Belgian": {"winner": "HAM", "pole": "LEC", "podium": ["HAM", "PIA", "LEC"]},
        "Dutch": {"winner": "NOR", "pole": "NOR", "podium": ["NOR", "VER", "LEC"]},
        "Italian": {"winner": "LEC", "pole": "NOR", "podium": ["LEC", "PIA", "NOR"]},
    },
    # 2025 賽季 (目前已知)
    2025: {
        "Australian": {"winner": "NOR", "pole": "NOR", "podium": ["NOR", "VER", "SAI"]},
        "Chinese": {"winner": "NOR", "pole": "VER", "podium": ["NOR", "VER", "RUS"]},
        "Japanese": {"winner": "VER", "pole": "VER", "podium": ["VER", "NOR", "LEC"]},
        "Bahrain": {"winner": "VER", "pole": "LEC", "podium": ["VER", "NOR", "SAI"]},
        "Saudi_Arabian": {"winner": "VER", "pole": "VER", "podium": ["VER", "LEC", "NOR"]},
        "Miami": {"winner": "NOR", "pole": "NOR", "podium": ["NOR", "VER", "LEC"]},
        "Monaco": {"winner": "LEC", "pole": "LEC", "podium": ["LEC", "NOR", "VER"]},
    },
}

# 車手號碼對應代碼 (2023-2025)
DRIVER_NUMBERS = {
    "1": "VER", "11": "PER", "44": "HAM", "63": "RUS",
    "16": "LEC", "55": "SAI", "4": "NOR", "81": "PIA",
    "14": "ALO", "18": "STR", "10": "GAS", "31": "OCO",
    "23": "ALB", "2": "SAR", "3": "RIC", "22": "TSU",
    "27": "HUL", "20": "MAG", "77": "BOT", "24": "ZHO",
    "21": "DEV", "87": "HAD", "12": "ANT", "30": "BEA",
    "6": "LAW", "43": "COL", "38": "DOO", "50": "BOR",
    # 2023 特殊
    "40": "DEV",
}

# 車隊評分
TEAM_RATINGS = {
    "Red Bull Racing": 0.95,
    "Ferrari": 0.88,
    "McLaren": 0.90,
    "Mercedes": 0.85,
    "Aston Martin": 0.70,
    "Alpine": 0.55,
    "Williams": 0.45,
    "RB": 0.50,
    "Racing Bulls": 0.50,
    "Kick Sauber": 0.35,
    "Haas F1 Team": 0.40,
    "Alfa Romeo": 0.35,
    "AlphaTauri": 0.50,
}


def extract_race_results_from_livef1(base_path: str) -> Dict:
    """從 LiveF1 JSON 提取比賽結果"""
    
    all_results = {
        "races": [],
        "driver_stats": {},
    }
    
    livef1_path = os.path.join(base_path, "json", "LiveF1")
    
    for year in [2023, 2024, 2025]:
        year_path = os.path.join(livef1_path, str(year))
        
        if not os.path.exists(year_path):
            print(f"[WARN] 找不到 {year} 數據")
            continue
        
        # 列出所有 _Race 資料夾
        races = [d for d in os.listdir(year_path) if d.endswith("_Race")]
        
        for race_folder in sorted(races):
            track = race_folder.replace("_Race", "")
            race_path = os.path.join(year_path, race_folder)
            
            print(f"[INFO] 處理 {year} {track}...")
            
            # 從 TimingData 提取最終位置
            final_positions = extract_final_positions(race_path)
            
            # 從 DriverList 提取車手資訊
            drivers = extract_driver_info(race_path)
            
            # 合併數據
            race_data = {
                "year": year,
                "track": track,
                "results": []
            }
            
            # 從已知結果獲取排位資訊
            known = KNOWN_RESULTS.get(year, {}).get(track, {})
            winner = known.get("winner", "")
            pole = known.get("pole", "")
            podium = known.get("podium", [])
            
            # 建立結果列表
            for num, pos in sorted(final_positions.items(), key=lambda x: x[1]):
                driver_code = DRIVER_NUMBERS.get(num, drivers.get(num, {}).get('code', ''))
                team = drivers.get(num, {}).get('team', '')
                
                # 估算起跑位置 (如果沒有真實數據)
                grid_pos = pos  # 預設用完賽位置
                if driver_code == pole:
                    grid_pos = 1
                elif driver_code in podium[:3]:
                    # 簡化假設：登台車手起跑前10
                    grid_pos = min(pos, 10)
                
                result = {
                    "driver_code": driver_code,
                    "team": team,
                    "grid_position": grid_pos,
                    "finish_position": pos,
                    "is_winner": (driver_code == winner) or (pos == 1),
                }
                race_data["results"].append(result)
            
            # 如果從 JSON 沒有提取到數據，使用已知結果
            if not race_data["results"] and known:
                # 使用已知的 podium 建立基本結果
                for i, code in enumerate(podium, 1):
                    race_data["results"].append({
                        "driver_code": code,
                        "team": "",
                        "grid_position": i,
                        "finish_position": i,
                        "is_winner": (i == 1),
                    })
            
            if race_data["results"]:
                all_results["races"].append(race_data)
    
    # 計算車手統計
    all_results["driver_stats"] = calculate_driver_stats(all_results["races"])
    
    return all_results


def extract_final_positions(race_path: str) -> Dict[str, int]:
    """從 TimingData.json 提取最終位置"""
    
    timing_path = os.path.join(race_path, "TimingData.json")
    
    if not os.path.exists(timing_path):
        return {}
    
    final_positions = {}
    
    try:
        with open(timing_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for rec in data.get('records', []):
            d = rec.get('data', {})
            if isinstance(d, dict) and 'Lines' in d:
                for num, info in d['Lines'].items():
                    if isinstance(info, dict) and 'Position' in info:
                        try:
                            final_positions[num] = int(info['Position'])
                        except:
                            pass
    except Exception as e:
        print(f"  [ERROR] 解析 TimingData: {e}")
    
    return final_positions


def extract_driver_info(race_path: str) -> Dict[str, Dict]:
    """從 DriverList.json 提取車手資訊"""
    
    driver_path = os.path.join(race_path, "DriverList.json")
    
    if not os.path.exists(driver_path):
        return {}
    
    drivers = {}
    
    try:
        with open(driver_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for rec in data.get('records', []):
            d = rec.get('data', {})
            if isinstance(d, dict):
                for num, info in d.items():
                    if isinstance(info, dict) and 'Tla' in info:
                        drivers[num] = {
                            'code': info.get('Tla', ''),
                            'team': info.get('TeamName', ''),
                        }
    except Exception as e:
        print(f"  [ERROR] 解析 DriverList: {e}")
    
    return drivers


def calculate_driver_stats(races: List[Dict]) -> Dict:
    """計算車手統計數據"""
    
    stats = defaultdict(lambda: {
        'total_races': 0,
        'wins': 0,
        'podiums': 0,
        'finishes': [],
        'grids': [],
        'track_performances': defaultdict(list),
    })
    
    for race in races:
        track = race['track']
        
        for result in race['results']:
            code = result['driver_code']
            if not code:
                continue
            
            pos = result['finish_position']
            grid = result['grid_position']
            
            # 跳過 DNF
            if pos > 20:
                continue
            
            stats[code]['total_races'] += 1
            stats[code]['finishes'].append(pos)
            stats[code]['grids'].append(grid)
            stats[code]['track_performances'][track].append(pos)
            
            if result['is_winner']:
                stats[code]['wins'] += 1
            if pos <= 3:
                stats[code]['podiums'] += 1
    
    # 計算衍生統計
    output = {}
    for code, data in stats.items():
        races = data['total_races']
        output[code] = {
            'total_races': races,
            'wins': data['wins'],
            'podiums': data['podiums'],
            'win_rate': data['wins'] / races if races > 0 else 0,
            'podium_rate': data['podiums'] / races if races > 0 else 0,
            'avg_finish': sum(data['finishes']) / len(data['finishes']) if data['finishes'] else 10,
            'avg_grid': sum(data['grids']) / len(data['grids']) if data['grids'] else 10,
            'track_performances': {k: v for k, v in data['track_performances'].items()},
        }
    
    return output


def main():
    """主函數"""
    
    print("=" * 60)
    print("F1 訓練數據提取器")
    print("=" * 60)
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 提取數據
    results = extract_race_results_from_livef1(base_path)
    
    # 保存
    output_path = os.path.join(base_path, "json", "race_results_training.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[INFO] 已保存到: {output_path}")
    print(f"[INFO] 總比賽數: {len(results['races'])}")
    print(f"[INFO] 車手數: {len(results['driver_stats'])}")
    
    # 顯示統計
    print("\n車手統計 (Top 10 勝率):")
    sorted_drivers = sorted(
        results['driver_stats'].items(),
        key=lambda x: x[1]['win_rate'],
        reverse=True
    )
    
    for code, stats in sorted_drivers[:10]:
        print(f"  {code}: 勝率 {stats['win_rate']*100:.1f}%, 登台率 {stats['podium_rate']*100:.1f}%, "
              f"平均完賽 P{stats['avg_finish']:.1f}")


if __name__ == "__main__":
    main()
