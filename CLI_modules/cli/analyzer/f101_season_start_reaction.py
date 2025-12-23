#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 年度起跑反應分析模組 - Function 101
Season Start Reaction Analysis Module - Following Core Development Standards

分析整個賽季的起跑數據：
1. 0-50 km/h 時間分布（所有車手、所有比賽）
2. P1 車手在 Lap2 仍保持領先的場數
3. P1 車手在 Lap2 位置變化的場數

數據來源：Live Timing JSON (CarData.json, SessionData.json, LapCount.json)
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

import numpy as np

# 強制 UTF-8 輸出
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# 全域設定
JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")

# 車手編號對照
DRIVER_NAMES = {
    '1': 'VER', '4': 'NOR', '5': 'BEA', '6': 'TSU', '10': 'GAS',
    '12': 'DOO', '14': 'ALO', '16': 'LEC', '18': 'STR', '22': 'ANT',
    '23': 'ALB', '27': 'HUL', '30': 'LAW', '31': 'OCO', '43': 'COL',
    '44': 'HAM', '55': 'SAI', '63': 'RUS', '81': 'PIA', '87': 'HAD',
    '2': 'SAR', '3': 'RIC', '11': 'PER', '20': 'MAG', '24': 'ZHO',
    '77': 'BOT', '21': 'DEV'
}

# 車隊顏色
TEAM_COLORS = {
    'VER': '#3671C6', 'NOR': '#FF8000', 'PIA': '#FF8000',
    'LEC': '#E8002D', 'SAI': '#E8002D', 'HAM': '#27F4D2', 
    'RUS': '#27F4D2', 'ALO': '#229971', 'STR': '#229971',
    'GAS': '#FF87BC', 'DOO': '#52E252', 'TSU': '#6692FF',
    'LAW': '#6692FF', 'ALB': '#1868DB', 'COL': '#1868DB',
    'HUL': '#B6BABD', 'BEA': '#52E252', 'OCO': '#FF87BC',
    'HAD': '#B6BABD', 'ANT': '#52E252', 'PER': '#3671C6',
    'ZHO': '#52E252', 'BOT': '#52E252', 'MAG': '#B6BABD',
    'SAR': '#1868DB', 'RIC': '#6692FF', 'DEV': '#6692FF'
}


def parse_timestamp(ts: str) -> float:
    """解析時間戳為秒數"""
    if not ts:
        return 0.0
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def interpolate_time(t1: float, v1: float, t2: float, v2: float, target_v: float) -> float:
    """線性內插計算達到目標速度的時間"""
    if v2 == v1:
        return t1
    ratio = (target_v - v1) / (v2 - v1)
    return t1 + ratio * (t2 - t1)


def get_race_directories(year: int) -> List[Path]:
    """獲取指定年份的所有比賽目錄"""
    base_dir = Path(__file__).parent.parent.parent.parent / "json" / "LiveF1" / str(year)
    if not base_dir.exists():
        return []
    
    race_dirs = sorted([
        d for d in base_dir.iterdir() 
        if d.is_dir() and d.name.endswith('_Race')
    ])
    return race_dirs


def analyze_single_race(race_dir: Path) -> Optional[Dict[str, Any]]:
    """
    分析單場比賽的起跑數據
    
    Returns:
        {
            'race_name': str,
            'drivers': {
                'VER': {'t50': 3.5, 'grid_position': 1, 'lap2_position': 1},
                ...
            },
            'pole_driver': str,
            'pole_lap2_position': int,
            'pole_position_unchanged': bool
        }
    """
    session_file = race_dir / 'SessionData.json'
    cardata_file = race_dir / 'CarData.json'
    lapcount_file = race_dir / 'LapCount.json'
    
    if not session_file.exists() or not cardata_file.exists():
        return None
    
    race_name = race_dir.name.replace('_Race', '')
    result = {
        'race_name': race_name,
        'drivers': {},
        'pole_driver': None,
        'pole_lap2_position': None,
        'pole_position_unchanged': None
    }
    
    try:
        # 1. 讀取 SessionData 找起跑時間
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        race_start_ts = None
        for rec in session_data.get('records', []):
            status = rec.get('data', {}).get('StatusSeries', {})
            if isinstance(status, dict):
                for key, val in status.items():
                    if isinstance(val, dict) and val.get('SessionStatus') == 'Started':
                        race_start_ts = parse_timestamp(rec.get('timestamp', ''))
                        break
            if race_start_ts:
                break
        
        if not race_start_ts:
            print(f"  [F101] {race_name}: 找不到起跑時間")
            return None
        
        # 2. 讀取 CarData 分析起跑速度
        with open(cardata_file, 'r', encoding='utf-8') as f:
            cardata = json.load(f)
        
        driver_speeds = defaultdict(list)
        
        for rec in cardata.get('records', []):
            ts = parse_timestamp(rec.get('timestamp', ''))
            if ts < race_start_ts or ts > race_start_ts + 60:
                continue
            
            entries = rec.get('data', {}).get('Entries', [])
            if not entries:
                continue
            
            cars = entries[0].get('Cars', {})
            for drv_num, name in DRIVER_NAMES.items():
                if drv_num in cars:
                    speed = cars[drv_num].get('Channels', {}).get('2', 0)
                    driver_speeds[name].append((ts - race_start_ts, speed))
        
        # 計算每位車手的 T50
        for name, speeds in driver_speeds.items():
            if not speeds or len(speeds) < 2:
                continue
            
            speeds.sort(key=lambda x: x[0])
            t50 = None
            
            for i in range(1, len(speeds)):
                t_prev, v_prev = speeds[i-1]
                t_curr, v_curr = speeds[i]
                
                if t50 is None and v_prev < 50 <= v_curr:
                    t50 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 50)
                    break
            
            # 過濾異常值 (T50 應在 3-7 秒之間)
            if t50 and 2.0 <= t50 <= 8.0:
                result['drivers'][name] = {'t50': round(t50, 3)}
        
        # 3. 從 DriverList.json 獲取起跑格位 (Line 字段)
        driverlist_file = race_dir / 'DriverList.json'
        grid_positions = {}
        
        if driverlist_file.exists():
            with open(driverlist_file, 'r', encoding='utf-8') as f:
                driverlist_data = json.load(f)
            
            # 獲取第一條記錄（包含所有車手的 Line 位置）
            for rec in driverlist_data.get('records', []):
                data = rec.get('data', {})
                for drv_num, info in data.items():
                    if isinstance(info, dict):
                        line = info.get('Line')
                        tla = info.get('Tla')
                        if line and tla:
                            grid_positions[tla] = int(line)
                break  # 只需第一條記錄
        
        # 4. 從 LapSeries.json 獲取 Lap 2 結束時的位置
        # LapPosition 可以是 list 或 dict 格式，需要合併所有記錄
        lapseries_file = race_dir / 'LapSeries.json'
        lap2_positions = {}
        
        if lapseries_file.exists():
            with open(lapseries_file, 'r', encoding='utf-8') as f:
                lapseries_data = json.load(f)
            
            # 合併所有記錄的 LapPosition 數據
            driver_lap_positions = defaultdict(dict)
            
            for rec in lapseries_data.get('records', []):
                for drv_num, drv_info in rec.get('data', {}).items():
                    if isinstance(drv_info, dict):
                        lp = drv_info.get('LapPosition')
                        if isinstance(lp, list):
                            # 數組格式: [Lap1位置, Lap2位置, ...]
                            for i, pos in enumerate(lp, 1):
                                driver_lap_positions[drv_num][i] = int(pos)
                        elif isinstance(lp, dict):
                            # 字典格式: {'2': '1', '3': '1', ...}
                            for lap, pos in lp.items():
                                driver_lap_positions[drv_num][int(lap)] = int(pos)
            
            # 提取 Lap 2 位置
            for drv_num, laps in driver_lap_positions.items():
                if 2 in laps:
                    driver_code = DRIVER_NAMES.get(str(drv_num))
                    if driver_code:
                        lap2_positions[driver_code] = laps[2]
        
        # 5. 找出 P1 車手並統計
        if grid_positions:
            for driver, pos in grid_positions.items():
                if pos == 1:
                    result['pole_driver'] = driver
                    if driver in lap2_positions:
                        result['pole_lap2_position'] = lap2_positions[driver]
                        result['pole_position_unchanged'] = (lap2_positions[driver] == 1)
                    break
            
            # 更新車手位置數據
            for driver in result['drivers']:
                if driver in grid_positions:
                    result['drivers'][driver]['grid_position'] = grid_positions[driver]
                if driver in lap2_positions:
                    result['drivers'][driver]['lap2_position'] = lap2_positions[driver]
        
        return result
        
    except Exception as e:
        print(f"  [F101] {race_name} 錯誤: {e}")
        return None


def run_season_start_reaction_analysis(
    year: int = 2025,
    save_json: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    執行年度起跑反應分析
    
    Args:
        year: 分析年份
        save_json: 是否輸出 JSON
        
    Returns:
        標準化結果字典
    """
    print(f"\n{'='*70}")
    print(f"[FUNCTION 101] 年度起跑反應分析 ({year} 賽季)")
    print(f"{'='*70}")
    
    # 獲取所有比賽目錄
    race_dirs = get_race_directories(year)
    
    if not race_dirs:
        return {
            "success": False,
            "message": f"找不到 {year} 年的比賽數據",
            "function_id": "101"
        }
    
    print(f"\n[INFO] 找到 {len(race_dirs)} 場比賽")
    
    # 分析每場比賽
    all_races = []
    driver_t50_data = defaultdict(list)
    p1_unchanged_races = []
    p1_changed_races = []
    
    for race_dir in race_dirs:
        race_result = analyze_single_race(race_dir)
        if race_result:
            all_races.append(race_result)
            
            # 收集 T50 數據
            for driver, data in race_result['drivers'].items():
                if 't50' in data:
                    driver_t50_data[driver].append({
                        'race': race_result['race_name'],
                        't50': data['t50']
                    })
            
            # 統計 P1 位置變化
            if race_result['pole_driver'] and race_result['pole_position_unchanged'] is not None:
                race_info = {
                    'race': race_result['race_name'],
                    'pole_driver': race_result['pole_driver'],
                    'lap2_position': race_result['pole_lap2_position']
                }
                if race_result['pole_position_unchanged']:
                    p1_unchanged_races.append(race_info)
                else:
                    p1_changed_races.append(race_info)
            
            print(f"  ✅ {race_result['race_name']}: {len(race_result['drivers'])} 位車手")
    
    if not all_races:
        return {
            "success": False,
            "message": "沒有成功分析的比賽",
            "function_id": "101"
        }
    
    # 計算 T50 分布統計
    t50_distribution = {}
    for driver, races in driver_t50_data.items():
        if len(races) >= 3:  # 至少 3 場比賽才計入統計
            t50_values = [r['t50'] for r in races]
            t50_distribution[driver] = {
                'race_count': len(races),
                'median': round(float(np.median(t50_values)), 3),
                'mean': round(float(np.mean(t50_values)), 3),
                'min': round(float(np.min(t50_values)), 3),
                'max': round(float(np.max(t50_values)), 3),
                'q1': round(float(np.percentile(t50_values, 25)), 3),
                'q3': round(float(np.percentile(t50_values, 75)), 3),
                'std': round(float(np.std(t50_values)), 3),
                'races': races,
                'team_color': TEAM_COLORS.get(driver, '#888888')
            }
    
    # 按中位數排序
    sorted_drivers = sorted(t50_distribution.keys(), key=lambda x: t50_distribution[x]['median'])
    t50_distribution_sorted = {d: t50_distribution[d] for d in sorted_drivers}
    
    # 構建結果
    result_data = {
        "year": year,
        "total_races_analyzed": len(all_races),
        "total_drivers": len(t50_distribution),
        
        # 0-50 km/h 分布
        "t50_distribution": {
            "description": "0-50 km/h acceleration time distribution (seconds)",
            "sort_order": "median_ascending",
            "drivers": t50_distribution_sorted
        },
        
        # P1 位置不變
        "p1_lap2_position_unchanged": {
            "description": "Races where pole sitter maintained P1 at end of Lap 2",
            "count": len(p1_unchanged_races),
            "percentage": round(len(p1_unchanged_races) / len(all_races) * 100, 1) if all_races else 0,
            "races": p1_unchanged_races
        },
        
        # P1 位置變化
        "p1_lap2_position_changed": {
            "description": "Races where pole sitter lost P1 by end of Lap 2",
            "count": len(p1_changed_races),
            "percentage": round(len(p1_changed_races) / len(all_races) * 100, 1) if all_races else 0,
            "races": p1_changed_races
        },
        
        # 原始比賽數據（供 GUI 使用）
        "raw_race_data": all_races
    }
    
    result = {
        "success": True,
        "message": f"年度起跑反應分析完成 ({year} 賽季，{len(all_races)} 場比賽)",
        "function_id": "101",
        "data": result_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # 輸出統計摘要
    print(f"\n{'='*70}")
    print(f"[RESULT] 分析完成")
    print(f"{'='*70}")
    print(f"  賽季: {year}")
    print(f"  分析比賽數: {len(all_races)}")
    print(f"  有效車手數: {len(t50_distribution)}")
    print(f"\n  📊 T50 (0-50 km/h) 排名 (前5):")
    for i, driver in enumerate(sorted_drivers[:5], 1):
        stats = t50_distribution[driver]
        print(f"    {i}. {driver}: {stats['median']:.3f}s (median), {stats['race_count']} races")
    
    print(f"\n  🏁 P1 位置統計:")
    print(f"    保持領先 (Lap2 仍為 P1): {len(p1_unchanged_races)} 場 ({result_data['p1_lap2_position_unchanged']['percentage']:.1f}%)")
    print(f"    失去領先 (Lap2 非 P1): {len(p1_changed_races)} 場 ({result_data['p1_lap2_position_changed']['percentage']:.1f}%)")
    
    if p1_changed_races:
        print(f"\n  📋 P1 失去領先的比賽:")
        for race in p1_changed_races:
            print(f"    - {race['race']}: {race['pole_driver']} P1 → P{race['lap2_position']}")
    
    # 保存 JSON (固定檔名，無時間戳)
    if save_json:
        output_dir = Path(JSON_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"F101_season_start_reaction_{year}.json"
        output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n  💾 JSON 輸出: {output_path}")
    
    return result


# CLI 入口點
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="F101: Season Start Reaction Analysis")
    parser.add_argument("-y", "--year", type=int, default=2025, help="Season year")
    parser.add_argument("--no-save", action="store_true", help="Don't save JSON output")
    
    args = parser.parse_args()
    
    result = run_season_start_reaction_analysis(
        year=args.year,
        save_json=not args.no_save
    )
    
    if not result.get("success"):
        print(f"\n[ERROR] {result.get('message')}")
        sys.exit(1)
