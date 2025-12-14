#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
輪胎性能分析器

從 2023-2024 數據計算每種輪胎的:
1. 相對單圈速度 (SOFT=1.0 基準)
2. 衰退率 (deg_per_lap)
3. 理想使用圈數 (ideal_laps)

輸出:
- data/live_win_probability/tyre_performance_trained.json

使用方式:
    python analyze_tyre_performance.py --years 2023 2024
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List
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


def analyze_race_tyres(year: int, race: str) -> List[Dict]:
    """
    分析單場比賽的輪胎數據
    
    Returns:
        List of {compound, lap_number, lap_time, tyre_age, driver}
    """
    try:
        print(f"  [R] Analyzing {year} {race}...")
        
        session = fastf1.get_session(year, race, 'R')
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        
        laps = session.laps
        
        if laps.empty:
            return []
        
        results = []
        
        for _, lap in laps.iterrows():
            compound = lap.get('Compound', 'UNKNOWN')
            if compound in ['UNKNOWN', None, '']:
                continue
                
            lap_time = lap.get('LapTime')
            if pd.isna(lap_time):
                continue
            
            # 轉換為秒
            if hasattr(lap_time, 'total_seconds'):
                lap_time_sec = lap_time.total_seconds()
            else:
                lap_time_sec = float(lap_time)
            
            # 過濾異常圈時 (進站圈、SC 圈等)
            if lap_time_sec < 60 or lap_time_sec > 180:
                continue
            
            tyre_life = lap.get('TyreLife', 0)
            if pd.isna(tyre_life):
                tyre_life = 0
            
            driver = lap.get('Driver', 'UNK')
            lap_number = lap.get('LapNumber', 0)
            
            # 過濾第一圈 (起跑影響)
            if lap_number <= 1:
                continue
            
            results.append({
                'year': year,
                'race': race,
                'compound': compound.upper(),
                'lap_number': int(lap_number),
                'lap_time': float(lap_time_sec),
                'tyre_age': int(tyre_life),
                'driver': driver,
            })
        
        return results
        
    except Exception as e:
        print(f"  [ERROR] {year} {race}: {e}")
        return []


def calculate_tyre_performance(all_data: List[Dict]) -> Dict[str, Dict]:
    """
    計算輪胎性能參數
    
    方法:
    1. 將所有圈時按 compound 和 tyre_age 分組
    2. 計算每個 age 的平均圈時
    3. 用線性迴歸計算衰退率
    4. 相對速度以 SOFT age=1 為基準
    
    Returns:
        {compound: {speed, deg_per_lap, ideal_laps, sample_size}}
    """
    df = pd.DataFrame(all_data)
    
    if df.empty:
        print("[ERROR] No data to analyze")
        return {}
    
    print(f"\n[INFO] Total records: {len(df)}")
    print(f"[INFO] Compounds: {df['compound'].unique()}")
    
    results = {}
    
    # SOFT 新胎基準
    soft_new = df[(df['compound'] == 'SOFT') & (df['tyre_age'] <= 3)]
    if not soft_new.empty:
        baseline_time = soft_new['lap_time'].median()
    else:
        baseline_time = df['lap_time'].median()
    
    print(f"[INFO] Baseline (SOFT new): {baseline_time:.3f}s")
    
    for compound in ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']:
        compound_df = df[df['compound'] == compound]
        
        if len(compound_df) < 100:
            print(f"[WARN] {compound}: only {len(compound_df)} samples, skipping")
            continue
        
        # 新胎速度 (age 1-3 的中位數)
        new_tyre = compound_df[compound_df['tyre_age'] <= 3]
        if not new_tyre.empty:
            new_time = new_tyre['lap_time'].median()
            relative_speed = baseline_time / new_time  # >1 = 比基準快
        else:
            relative_speed = 1.0
        
        # 衰退率 (線性迴歸)
        # 只用 age 5-30 的數據，避免新胎 warm-up 影響
        mid_stint = compound_df[(compound_df['tyre_age'] >= 5) & (compound_df['tyre_age'] <= 30)]
        
        if len(mid_stint) >= 50:
            # 計算每個 age 的中位數圈時
            age_groups = mid_stint.groupby('tyre_age')['lap_time'].median()
            
            if len(age_groups) >= 5:
                # 線性迴歸
                ages = age_groups.index.values
                times = age_groups.values
                
                # deg = (time_old - time_new) / (age_old - age_new) / baseline
                # 每圈衰退的「相對速度」
                slope = np.polyfit(ages, times, 1)[0]  # 秒/圈
                deg_per_lap = slope / baseline_time  # 相對速度衰退
            else:
                deg_per_lap = 0.002  # 預設值
        else:
            deg_per_lap = 0.002
        
        # 理想圈數 (性能衰退超過 5% 前)
        # ideal = 0.05 / deg_per_lap
        if deg_per_lap > 0:
            ideal_laps = min(50, max(10, int(0.05 / deg_per_lap)))
        else:
            ideal_laps = 30
        
        results[compound] = {
            'speed': float(np.clip(relative_speed, 0.85, 1.02)),
            'deg_per_lap': float(np.clip(deg_per_lap, 0.0005, 0.01)),
            'ideal_laps': ideal_laps,
            'sample_size': len(compound_df),
        }
        
        print(f"[{compound:12s}] speed={relative_speed:.4f}, "
              f"deg={deg_per_lap:.5f}/lap, ideal={ideal_laps} laps, "
              f"N={len(compound_df)}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="輪胎性能分析器")
    parser.add_argument('--years', type=int, nargs='+', default=[2023, 2024])
    parser.add_argument('--max-races', type=int, default=None, help="每年最多分析幾場")
    args = parser.parse_args()
    
    if not FASTF1_AVAILABLE:
        print("[ERROR] FastF1 not available")
        sys.exit(1)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"輪胎性能分析器")
    print(f"Years: {args.years}")
    print(f"{'='*60}")
    
    # 收集所有數據
    all_data = []
    
    for year in args.years:
        print(f"\n[{year}] Processing...")
        races = get_race_calendar(year)
        
        if args.max_races:
            races = races[:args.max_races]
        
        for race in races:
            data = analyze_race_tyres(year, race)
            if data:
                all_data.extend(data)
                print(f"    → Collected {len(data)} laps")
    
    if not all_data:
        print("[ERROR] No data collected")
        sys.exit(1)
    
    # 計算性能參數
    print(f"\n{'='*60}")
    print("Calculating tyre performance...")
    print(f"{'='*60}")
    
    tyre_performance = calculate_tyre_performance(all_data)
    
    # 保存結果
    output_file = OUTPUT_DIR / "tyre_performance_trained.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tyre_performance, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Saved to: {output_file}")
    
    # 生成 Python 字典格式
    print(f"\n{'='*60}")
    print("Python Dictionary (for predictor.py)")
    print(f"{'='*60}")
    print("TYRE_PERFORMANCE = {")
    for compound, stats in tyre_performance.items():
        print(f'    "{compound}": {{"speed": {stats["speed"]:.3f}, '
              f'"deg_per_lap": {stats["deg_per_lap"]:.4f}, '
              f'"ideal_laps": {stats["ideal_laps"]}}},')
    print("}")


if __name__ == "__main__":
    main()
