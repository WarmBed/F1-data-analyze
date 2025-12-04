"""
賽道超車難度分析器

從 2023-2024 數據計算每個賽道的:
1. 平均超車次數
2. Q 位置與最終位置的相關性 (越高 = 越難超車)
3. 起跑位置保持率 (Lap 1 後仍在原位的比例)

輸出:
- data/live_win_probability/circuit_overtake_difficulty.json

使用方式:
    python analyze_circuit_overtake.py --years 2023 2024
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

import numpy as np
import pandas as pd

# 添加專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import fastf1
    fastf1.Cache.enable_cache(str(PROJECT_ROOT / "f1_analysis_cache"))
    FASTF1_AVAILABLE = True
except ImportError:
    FASTF1_AVAILABLE = False
    print("[ERROR] FastF1 not installed")

OUTPUT_DIR = PROJECT_ROOT / "data" / "live_win_probability"


def get_race_calendar(year: int) -> List[str]:
    """獲取賽事列表"""
    try:
        schedule = fastf1.get_event_schedule(year)
        races = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
        return races
    except Exception as e:
        print(f"[ERROR] Cannot get {year} calendar: {e}")
        return []


def analyze_race_overtakes(year: int, race: str) -> Dict:
    """
    分析單場比賽的超車數據
    
    Returns:
        {
            'circuit': str,
            'total_overtakes': int,
            'avg_position_changes': float,
            'q_to_final_correlation': float,
            'lap1_position_retention': float,
        }
    """
    try:
        print(f"  [R] Analyzing {year} {race}...")
        
        # 載入排位賽結果
        q_session = fastf1.get_session(year, race, 'Q')
        q_session.load(laps=False, telemetry=False, weather=False, messages=False)
        q_results = q_session.results
        
        # 載入正賽
        r_session = fastf1.get_session(year, race, 'R')
        r_session.load(laps=True, telemetry=False, weather=False, messages=False)
        r_results = r_session.results
        laps = r_session.laps
        
        if q_results.empty or r_results.empty:
            return None
        
        # 獲取賽道名稱
        circuit_name = r_session.event.get('CircuitShortName', race)
        
        # 1. 計算 Q 位置與最終位置的相關性
        q_positions = {}
        for _, row in q_results.iterrows():
            driver = row.get('Abbreviation', '')
            if driver:
                q_positions[driver] = row.get('Position', 20)
        
        final_positions = {}
        for _, row in r_results.iterrows():
            driver = row.get('Abbreviation', '')
            if driver:
                final_positions[driver] = row.get('Position', 20)
        
        # 計算相關性
        common_drivers = set(q_positions.keys()) & set(final_positions.keys())
        if len(common_drivers) >= 10:
            q_list = [q_positions[d] for d in common_drivers]
            f_list = [final_positions[d] for d in common_drivers]
            correlation = np.corrcoef(q_list, f_list)[0, 1]
        else:
            correlation = 0.5
        
        # 2. 計算 Lap 1 後位置保持率
        lap1_retention = 0.0
        try:
            lap1_data = laps[laps['LapNumber'] == 1]
            if not lap1_data.empty:
                retained = 0
                total = 0
                for driver in common_drivers:
                    q_pos = q_positions.get(driver, 20)
                    driver_lap1 = lap1_data[lap1_data['Driver'] == driver]
                    if not driver_lap1.empty:
                        lap1_pos = driver_lap1.iloc[0].get('Position', 20)
                        if lap1_pos == q_pos:
                            retained += 1
                        total += 1
                if total > 0:
                    lap1_retention = retained / total
        except Exception as e:
            print(f"    [WARN] Lap1 analysis failed: {e}")
            lap1_retention = 0.5
        
        # 3. 計算總超車次數 (位置變化)
        total_overtakes = 0
        avg_position_changes = 0.0
        try:
            position_changes = []
            for driver in common_drivers:
                driver_laps = laps[laps['Driver'] == driver].sort_values('LapNumber')
                if len(driver_laps) >= 2:
                    positions = driver_laps['Position'].dropna().values
                    if len(positions) >= 2:
                        changes = np.abs(np.diff(positions))
                        position_changes.extend(changes)
                        total_overtakes += np.sum(changes > 0)
            
            if position_changes:
                avg_position_changes = np.mean(position_changes)
        except Exception as e:
            print(f"    [WARN] Overtake analysis failed: {e}")
        
        return {
            'circuit': circuit_name,
            'race_name': race,
            'year': year,
            'total_overtakes': int(total_overtakes),
            'avg_position_changes': float(avg_position_changes),
            'q_to_final_correlation': float(correlation),
            'lap1_position_retention': float(lap1_retention),
        }
        
    except Exception as e:
        print(f"  [ERROR] {year} {race}: {e}")
        return None


def calculate_overtake_difficulty(circuit_data: List[Dict]) -> Dict[str, float]:
    """
    計算每個賽道的超車難度
    
    難度 = 0.5 * Q相關性 + 0.3 * Lap1保持率 + 0.2 * (1 - 標準化超車數)
    
    Returns:
        {circuit_name: difficulty_score}  # 0.0 (最易超車) - 1.0 (最難超車)
    """
    # 按賽道分組
    circuit_stats = defaultdict(list)
    for data in circuit_data:
        if data:
            circuit_stats[data['circuit']].append(data)
    
    # 計算每個賽道的平均值
    results = {}
    all_overtakes = []
    
    for circuit, races in circuit_stats.items():
        avg_correlation = np.mean([r['q_to_final_correlation'] for r in races])
        avg_retention = np.mean([r['lap1_position_retention'] for r in races])
        avg_overtakes = np.mean([r['total_overtakes'] for r in races])
        
        results[circuit] = {
            'q_correlation': avg_correlation,
            'lap1_retention': avg_retention,
            'avg_overtakes': avg_overtakes,
            'race_count': len(races),
        }
        all_overtakes.append(avg_overtakes)
    
    # 標準化超車數 (越多超車 = 越容易超車)
    if all_overtakes:
        min_ot = min(all_overtakes)
        max_ot = max(all_overtakes)
        ot_range = max_ot - min_ot if max_ot > min_ot else 1
    else:
        min_ot, ot_range = 0, 1
    
    # 計算最終難度分數
    difficulty_scores = {}
    for circuit, stats in results.items():
        # 標準化超車數 (0 = 最多超車, 1 = 最少超車)
        norm_overtakes = 1 - (stats['avg_overtakes'] - min_ot) / ot_range
        
        # 綜合難度分數
        difficulty = (
            0.50 * stats['q_correlation'] +      # Q 相關性權重最高
            0.30 * stats['lap1_retention'] +     # Lap1 保持率
            0.20 * norm_overtakes                # 超車數 (反向)
        )
        
        # 限制範圍 [0.2, 0.95]
        difficulty = np.clip(difficulty, 0.20, 0.95)
        
        difficulty_scores[circuit] = {
            'difficulty': float(difficulty),
            'q_correlation': float(stats['q_correlation']),
            'lap1_retention': float(stats['lap1_retention']),
            'avg_overtakes': float(stats['avg_overtakes']),
            'race_count': stats['race_count'],
        }
    
    return difficulty_scores


def main():
    parser = argparse.ArgumentParser(description="賽道超車難度分析器")
    parser.add_argument('--years', type=int, nargs='+', default=[2023, 2024])
    args = parser.parse_args()
    
    if not FASTF1_AVAILABLE:
        print("[ERROR] FastF1 not available")
        sys.exit(1)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"賽道超車難度分析器")
    print(f"Years: {args.years}")
    print(f"{'='*60}")
    
    # 收集所有數據
    all_data = []
    
    for year in args.years:
        print(f"\n[{year}] Processing...")
        races = get_race_calendar(year)
        
        for race in races:
            data = analyze_race_overtakes(year, race)
            if data:
                all_data.append(data)
    
    if not all_data:
        print("[ERROR] No data collected")
        sys.exit(1)
    
    # 計算難度分數
    difficulty_scores = calculate_overtake_difficulty(all_data)
    
    # 保存結果
    output_file = OUTPUT_DIR / "circuit_overtake_difficulty.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(difficulty_scores, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Saved to: {output_file}")
    
    # 顯示排名
    print(f"\n{'='*60}")
    print("Circuit Overtake Difficulty Ranking")
    print("(Higher = Harder to overtake)")
    print(f"{'='*60}")
    
    sorted_circuits = sorted(difficulty_scores.items(), key=lambda x: x[1]['difficulty'], reverse=True)
    
    for i, (circuit, stats) in enumerate(sorted_circuits, 1):
        print(f"{i:2d}. {circuit:20s}: {stats['difficulty']:.3f} "
              f"(Q_corr={stats['q_correlation']:.2f}, "
              f"Lap1_ret={stats['lap1_retention']:.2f}, "
              f"OT={stats['avg_overtakes']:.0f})")


if __name__ == "__main__":
    main()
