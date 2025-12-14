#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FP3/Q 補償數據收集器

收集 FP3 和 Q 的數據，用於補償正賽勝率預測。

數據用途:
- FP3: 長跑節奏、輪胎衰減、賽道適應性
- Q: 單圈絕對速度、車手信心指數、起跑位置

輸出:
- data/live_win_probability/fp3_compensation_data.csv
- data/live_win_probability/q_compensation_data.csv

使用方式:
    python collect_fp3_q_compensation_data.py --year 2023 --all
    python collect_fp3_q_compensation_data.py --year 2024 --race Japan
    
作者: F1T Dev Team
日期: 2025-12-01
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
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

# 添加專案根目錄到 path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import fastf1
    fastf1.Cache.enable_cache(str(PROJECT_ROOT / "f1_analysis_cache"))
    FASTF1_AVAILABLE = True
except ImportError:
    FASTF1_AVAILABLE = False
    print("[ERROR] FastF1 not installed. Run: pip install fastf1")


# 輸出目錄
OUTPUT_DIR = PROJECT_ROOT / "data" / "live_win_probability"


def get_race_calendar(year: int) -> List[str]:
    """獲取指定年份的賽事列表"""
    try:
        schedule = fastf1.get_event_schedule(year)
        races = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
        return races
    except Exception as e:
        print(f"[ERROR] 無法獲取 {year} 賽季列表: {e}")
        return []


def collect_fp3_data(year: int, race: str) -> Optional[pd.DataFrame]:
    """
    收集 FP3 數據
    
    提取:
    - 長跑節奏 (stint 圈速平均)
    - 輪胎衰減率
    - 賽道適應性 (sector times)
    
    Returns:
        DataFrame with columns:
        - year, race, driver_code
        - fp3_best_lap, fp3_avg_lap, fp3_long_run_pace
        - fp3_tyre_deg_rate, fp3_s1_avg, fp3_s2_avg, fp3_s3_avg
    """
    try:
        print(f"  [FP3] Loading {year} {race}...")
        session = fastf1.get_session(year, race, 'FP3')
        # 只載入圈速數據，不載入遙測和天氣
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        
        laps = session.laps
        if laps.empty:
            print(f"  [FP3] No laps data for {year} {race}")
            return None
        
        results = []
        
        for driver in laps['Driver'].unique():
            driver_laps = laps[laps['Driver'] == driver].copy()
            
            # 過濾有效圈速 (非 outliers)
            valid_laps = driver_laps[
                (driver_laps['LapTime'].notna()) & 
                (driver_laps['IsPersonalBest'].notna())
            ].copy()
            
            if valid_laps.empty:
                continue
            
            # 將 LapTime 轉換為秒
            valid_laps['LapTimeSeconds'] = valid_laps['LapTime'].dt.total_seconds()
            
            # 基本統計
            best_lap = valid_laps['LapTimeSeconds'].min()
            avg_lap = valid_laps['LapTimeSeconds'].mean()
            
            # 長跑節奏 (連續 5+ 圈的平均)
            long_run_pace = np.nan
            if len(valid_laps) >= 5:
                # 找最長的連續 stint
                valid_laps = valid_laps.sort_values('LapNumber')
                lap_nums = valid_laps['LapNumber'].values
                
                max_stint_len = 0
                max_stint_laps = []
                current_stint = [lap_nums[0]]
                
                for i in range(1, len(lap_nums)):
                    if lap_nums[i] == lap_nums[i-1] + 1:
                        current_stint.append(lap_nums[i])
                    else:
                        if len(current_stint) > max_stint_len:
                            max_stint_len = len(current_stint)
                            max_stint_laps = current_stint.copy()
                        current_stint = [lap_nums[i]]
                
                if len(current_stint) > max_stint_len:
                    max_stint_laps = current_stint
                
                if len(max_stint_laps) >= 5:
                    stint_data = valid_laps[valid_laps['LapNumber'].isin(max_stint_laps)]
                    long_run_pace = stint_data['LapTimeSeconds'].mean()
            
            # 輪胎衰減率 (如果有足夠數據)
            tyre_deg_rate = np.nan
            if len(valid_laps) >= 5:
                valid_laps['TyreAge'] = range(1, len(valid_laps) + 1)
                try:
                    from scipy import stats
                    slope, _, _, _, _ = stats.linregress(
                        valid_laps['TyreAge'], 
                        valid_laps['LapTimeSeconds']
                    )
                    tyre_deg_rate = slope  # 秒/圈
                except:
                    pass
            
            # Sector times
            s1_avg = valid_laps['Sector1Time'].dt.total_seconds().mean() if 'Sector1Time' in valid_laps.columns else np.nan
            s2_avg = valid_laps['Sector2Time'].dt.total_seconds().mean() if 'Sector2Time' in valid_laps.columns else np.nan
            s3_avg = valid_laps['Sector3Time'].dt.total_seconds().mean() if 'Sector3Time' in valid_laps.columns else np.nan
            
            results.append({
                'year': year,
                'race': race,
                'driver_code': driver,
                'fp3_best_lap': best_lap,
                'fp3_avg_lap': avg_lap,
                'fp3_long_run_pace': long_run_pace,
                'fp3_tyre_deg_rate': tyre_deg_rate,
                'fp3_s1_avg': s1_avg,
                'fp3_s2_avg': s2_avg,
                'fp3_s3_avg': s3_avg,
                'fp3_lap_count': len(valid_laps),
            })
        
        if results:
            df = pd.DataFrame(results)
            print(f"  [FP3] Collected {len(df)} driver records")
            return df
        return None
        
    except Exception as e:
        print(f"  [FP3] Error loading {year} {race}: {e}")
        return None


def collect_qualifying_data(year: int, race: str) -> Optional[pd.DataFrame]:
    """
    收集 Q 數據
    
    提取:
    - 排位最快圈
    - 排位位置
    - 各節 (Q1/Q2/Q3) 成績
    - 與桿位差距
    
    Returns:
        DataFrame with columns:
        - year, race, driver_code
        - q_position, q_best_lap, q_gap_to_pole
        - q1_time, q2_time, q3_time
    """
    try:
        print(f"  [Q] Loading {year} {race}...")
        session = fastf1.get_session(year, race, 'Q')
        # 只載入結果和圈速數據
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        
        results_df = session.results
        if results_df.empty:
            print(f"  [Q] No results data for {year} {race}")
            return None
        
        laps = session.laps
        
        results = []
        
        # 找到桿位圈速
        pole_time = None
        if 'Q3' in results_df.columns:
            pole_time = results_df['Q3'].min()
        elif 'Q2' in results_df.columns:
            pole_time = results_df['Q2'].min()
        elif 'Q1' in results_df.columns:
            pole_time = results_df['Q1'].min()
        
        if pole_time is not None and hasattr(pole_time, 'total_seconds'):
            pole_time = pole_time.total_seconds()
        
        for _, row in results_df.iterrows():
            driver = row.get('Abbreviation', row.get('Driver', ''))
            if not driver:
                continue
            
            # 排位位置
            q_position = row.get('Position', np.nan)
            
            # 各節成績
            q1_time = row.get('Q1')
            q2_time = row.get('Q2')
            q3_time = row.get('Q3')
            
            # 轉換為秒
            if q1_time is not None and hasattr(q1_time, 'total_seconds'):
                q1_time = q1_time.total_seconds()
            if q2_time is not None and hasattr(q2_time, 'total_seconds'):
                q2_time = q2_time.total_seconds()
            if q3_time is not None and hasattr(q3_time, 'total_seconds'):
                q3_time = q3_time.total_seconds()
            
            # 最快圈
            q_best_lap = q3_time or q2_time or q1_time
            
            # 與桿位差距
            q_gap_to_pole = np.nan
            if q_best_lap and pole_time and not np.isnan(q_best_lap) and not np.isnan(pole_time):
                q_gap_to_pole = q_best_lap - pole_time
            
            results.append({
                'year': year,
                'race': race,
                'driver_code': driver,
                'q_position': q_position,
                'q_best_lap': q_best_lap,
                'q_gap_to_pole': q_gap_to_pole,
                'q1_time': q1_time,
                'q2_time': q2_time,
                'q3_time': q3_time,
            })
        
        if results:
            df = pd.DataFrame(results)
            print(f"  [Q] Collected {len(df)} driver records")
            return df
        return None
        
    except Exception as e:
        print(f"  [Q] Error loading {year} {race}: {e}")
        return None


def collect_race_results(year: int, race: str) -> Optional[pd.DataFrame]:
    """
    收集正賽結果 (用於關聯 FP3/Q 補償效果)
    
    Returns:
        DataFrame with columns:
        - year, race, driver_code
        - final_position, race_time, points
    """
    try:
        print(f"  [R] Loading {year} {race}...")
        session = fastf1.get_session(year, race, 'R')
        # 只載入結果數據，不載入圈速和遙測
        session.load(laps=False, telemetry=False, weather=False, messages=False)
        
        results_df = session.results
        if results_df.empty:
            print(f"  [R] No results data for {year} {race}")
            return None
        
        results = []
        
        for _, row in results_df.iterrows():
            driver = row.get('Abbreviation', row.get('Driver', ''))
            if not driver:
                continue
            
            results.append({
                'year': year,
                'race': race,
                'driver_code': driver,
                'final_position': row.get('Position', np.nan),
                'race_points': row.get('Points', 0),
                'race_status': row.get('Status', ''),
            })
        
        if results:
            df = pd.DataFrame(results)
            print(f"  [R] Collected {len(df)} driver records")
            return df
        return None
        
    except Exception as e:
        print(f"  [R] Error loading {year} {race}: {e}")
        return None


def collect_all_data(year: int, races: List[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    收集指定年份的所有 FP3/Q/R 數據
    
    Returns:
        (fp3_q_combined_df, race_results_df)
    """
    if races is None:
        races = get_race_calendar(year)
    
    all_fp3 = []
    all_q = []
    all_race = []
    
    for race in races:
        print(f"\n[{year}] Processing: {race}")
        
        # 收集 FP3
        fp3_df = collect_fp3_data(year, race)
        if fp3_df is not None:
            all_fp3.append(fp3_df)
        
        # 收集 Q
        q_df = collect_qualifying_data(year, race)
        if q_df is not None:
            all_q.append(q_df)
        
        # 收集 R
        race_df = collect_race_results(year, race)
        if race_df is not None:
            all_race.append(race_df)
    
    # 合併數據
    fp3_combined = pd.concat(all_fp3, ignore_index=True) if all_fp3 else pd.DataFrame()
    q_combined = pd.concat(all_q, ignore_index=True) if all_q else pd.DataFrame()
    race_combined = pd.concat(all_race, ignore_index=True) if all_race else pd.DataFrame()
    
    # 合併 FP3 和 Q
    if not fp3_combined.empty and not q_combined.empty:
        fp3_q_combined = pd.merge(
            fp3_combined, q_combined,
            on=['year', 'race', 'driver_code'],
            how='outer'
        )
    elif not fp3_combined.empty:
        fp3_q_combined = fp3_combined
    elif not q_combined.empty:
        fp3_q_combined = q_combined
    else:
        fp3_q_combined = pd.DataFrame()
    
    # 合併正賽結果
    if not fp3_q_combined.empty and not race_combined.empty:
        final_df = pd.merge(
            fp3_q_combined, race_combined,
            on=['year', 'race', 'driver_code'],
            how='left'
        )
    else:
        final_df = fp3_q_combined
    
    return final_df, race_combined


def calculate_compensation_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算 FP3/Q 補償因子
    
    補償邏輯:
    1. fp3_pace_advantage = (race_winner_fp3_pace - driver_fp3_pace) / race_winner_fp3_pace
    2. q_position_factor = 1 - (q_position - 1) * 0.03  # 每落後一位，補償 3%
    3. fp3_tyre_deg_factor = 1 / (1 + fp3_tyre_deg_rate)  # 衰減越高，補償越低
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # 按賽事分組計算
    for (year, race), group in df.groupby(['year', 'race']):
        # FP3 長跑節奏優勢
        if 'fp3_long_run_pace' in group.columns:
            best_pace = group['fp3_long_run_pace'].min()
            if not np.isnan(best_pace) and best_pace > 0:
                df.loc[group.index, 'fp3_pace_advantage'] = (
                    group['fp3_long_run_pace'] - best_pace
                ) / best_pace
    
    # Q 位置補償因子
    if 'q_position' in df.columns:
        df['q_position_factor'] = 1 - (df['q_position'] - 1) * 0.03
        df['q_position_factor'] = df['q_position_factor'].clip(0.5, 1.0)
    
    # 輪胎衰減因子
    if 'fp3_tyre_deg_rate' in df.columns:
        df['fp3_tyre_deg_factor'] = 1 / (1 + df['fp3_tyre_deg_rate'].abs())
    
    # 綜合補償因子
    df['combined_compensation'] = 1.0
    
    if 'fp3_pace_advantage' in df.columns:
        df['combined_compensation'] *= (1 - df['fp3_pace_advantage'].fillna(0) * 0.5)
    
    if 'q_position_factor' in df.columns:
        df['combined_compensation'] *= df['q_position_factor'].fillna(1.0)
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description="FP3/Q 補償數據收集器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument('--year', type=int, required=True, help='賽季年份')
    parser.add_argument('--race', type=str, help='指定賽事 (可選)')
    parser.add_argument('--all', action='store_true', help='收集整季數據')
    parser.add_argument('--output', type=str, default=None, help='輸出檔案路徑')
    
    args = parser.parse_args()
    
    if not FASTF1_AVAILABLE:
        print("[ERROR] FastF1 not available")
        sys.exit(1)
    
    # 確保輸出目錄存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 決定賽事列表
    if args.race:
        races = [args.race]
    elif args.all:
        races = get_race_calendar(args.year)
    else:
        print("[ERROR] 必須指定 --race 或 --all")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"FP3/Q 補償數據收集器")
    print(f"Year: {args.year}, Races: {len(races)}")
    print(f"{'='*60}")
    
    # 收集數據
    combined_df, race_df = collect_all_data(args.year, races)
    
    if combined_df.empty:
        print("\n[WARNING] No data collected")
        sys.exit(1)
    
    # 計算補償因子
    combined_df = calculate_compensation_factors(combined_df)
    
    # 保存數據
    output_file = args.output or OUTPUT_DIR / f"fp3_q_compensation_{args.year}.csv"
    combined_df.to_csv(output_file, index=False)
    print(f"\n[SUCCESS] Data saved to: {output_file}")
    print(f"  Total records: {len(combined_df)}")
    print(f"  Columns: {list(combined_df.columns)}")
    
    # 顯示統計
    print(f"\n{'='*60}")
    print("Statistics:")
    print(f"{'='*60}")
    
    if 'fp3_pace_advantage' in combined_df.columns:
        print(f"  FP3 Pace Advantage: mean={combined_df['fp3_pace_advantage'].mean():.4f}")
    
    if 'q_position_factor' in combined_df.columns:
        print(f"  Q Position Factor: mean={combined_df['q_position_factor'].mean():.4f}")
    
    if 'combined_compensation' in combined_df.columns:
        print(f"  Combined Compensation: mean={combined_df['combined_compensation'].mean():.4f}")
    
    # 檢查 FP3 節奏與最終成績的相關性
    if 'fp3_long_run_pace' in combined_df.columns and 'final_position' in combined_df.columns:
        valid = combined_df[['fp3_long_run_pace', 'final_position']].dropna()
        if len(valid) > 10:
            corr = valid['fp3_long_run_pace'].corr(valid['final_position'])
            print(f"  FP3 Pace vs Final Position correlation: {corr:.4f}")
    
    if 'q_position' in combined_df.columns and 'final_position' in combined_df.columns:
        valid = combined_df[['q_position', 'final_position']].dropna()
        if len(valid) > 10:
            corr = valid['q_position'].corr(valid['final_position'])
            print(f"  Q Position vs Final Position correlation: {corr:.4f}")


if __name__ == "__main__":
    main()
