#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
賽道超車難度分析器 v2

從 2023-2024 Q 補償數據計算每個賽道的超車難度:
1. Q 位置與最終位置的相關性 (越高 = 越難超車)
2. 起跑位置增益/損失統計

輸出:
- data/live_win_probability/circuit_overtake_difficulty.json

使用方式:
    python analyze_circuit_overtake_v2.py
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
from pathlib import Path
from typing import Dict
from collections import defaultdict

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "live_win_probability"
OUTPUT_DIR = DATA_DIR


def load_compensation_data() -> pd.DataFrame:
    """載入 FP3/Q 補償數據"""
    combined_file = DATA_DIR / "fp3_q_compensation_combined.csv"
    
    if not combined_file.exists():
        # 嘗試合併 2023/2024 檔案
        dfs = []
        for year in [2023, 2024]:
            f = DATA_DIR / f"fp3_q_compensation_{year}.csv"
            if f.exists():
                dfs.append(pd.read_csv(f))
        
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        else:
            raise FileNotFoundError("No FP3/Q compensation data found")
    
    return pd.read_csv(combined_file)


def calculate_circuit_difficulty(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    計算每個賽道的超車難度
    
    難度公式:
    - Q 與 Final 位置相關性 (權重 0.6)
    - 位置保持率: Q == Final 的比例 (權重 0.4)
    
    Returns:
        {circuit_name: {difficulty, q_correlation, position_retention, ...}}
    """
    # 按賽道分組
    results = {}
    
    # 標準化賽道名稱映射
    circuit_mapping = {
        'Bahrain': 'Sakhir',
        'Saudi Arabian': 'Jeddah', 
        'Saudi Arabia': 'Jeddah',
        'Australian': 'Melbourne',
        'Azerbaijan': 'Baku',
        'Miami': 'Miami',
        'Monaco': 'Monaco',
        'Spanish': 'Catalunya',
        'Spain': 'Catalunya',
        'Canadian': 'Montreal',
        'Canada': 'Montreal',
        'Austrian': 'Spielberg',
        'Austria': 'Spielberg',
        'British': 'Silverstone',
        'United Kingdom': 'Silverstone',
        'Hungarian': 'Budapest',
        'Hungary': 'Budapest',
        'Belgian': 'Spa',
        'Belgium': 'Spa',
        'Dutch': 'Zandvoort',
        'Netherlands': 'Zandvoort',
        'Italian': 'Monza',
        'Italy': 'Monza',
        'Singapore': 'Singapore',
        'Japanese': 'Suzuka',
        'Japan': 'Suzuka',
        'Qatar': 'Lusail',
        'United States': 'Austin',
        'USA': 'Austin',
        'US': 'Austin',
        'Mexican': 'Mexico City',
        'Mexico': 'Mexico City',
        'Brazilian': 'Interlagos',
        'Brazil': 'Interlagos',
        'Las Vegas': 'Las Vegas',
        'Abu Dhabi': 'Yas Marina',
        'Chinese': 'Shanghai',
        'China': 'Shanghai',
        'Emilia Romagna': 'Imola',
    }
    
    # 嘗試識別賽道名稱
    def normalize_circuit(race_name: str) -> str:
        race_name = str(race_name)
        for key, value in circuit_mapping.items():
            if key.lower() in race_name.lower():
                return value
        # 直接使用第一個單字
        return race_name.split()[0] if race_name else 'Unknown'
    
    # 添加標準化賽道名稱
    df = df.copy()
    df['circuit'] = df['race'].apply(normalize_circuit)
    
    # 按賽道分組計算
    for circuit in df['circuit'].unique():
        circuit_df = df[df['circuit'] == circuit]
        
        if len(circuit_df) < 10:
            continue
        
        # 1. Q 與 Final 相關性
        q_positions = circuit_df['q_position'].dropna()
        final_positions = circuit_df['final_position'].dropna()
        
        if len(q_positions) >= 10 and len(final_positions) >= 10:
            # 確保數據對齊
            mask = circuit_df['q_position'].notna() & circuit_df['final_position'].notna()
            q_vals = circuit_df.loc[mask, 'q_position'].values
            f_vals = circuit_df.loc[mask, 'final_position'].values
            
            if len(q_vals) >= 10:
                correlation = np.corrcoef(q_vals, f_vals)[0, 1]
            else:
                correlation = 0.5
        else:
            correlation = 0.5
        
        # 2. 位置保持率 (Q == Final)
        mask = circuit_df['q_position'].notna() & circuit_df['final_position'].notna()
        total = mask.sum()
        if total > 0:
            same_position = (circuit_df.loc[mask, 'q_position'] == 
                           circuit_df.loc[mask, 'final_position']).sum()
            retention = same_position / total
        else:
            retention = 0.5
        
        # 3. 位置變化統計
        mask = circuit_df['q_position'].notna() & circuit_df['final_position'].notna()
        if mask.sum() > 0:
            pos_changes = (circuit_df.loc[mask, 'final_position'] - 
                         circuit_df.loc[mask, 'q_position'])
            avg_position_change = pos_changes.abs().mean()
            forward_rate = (pos_changes < 0).sum() / mask.sum()  # 進步比例
        else:
            avg_position_change = 2.0
            forward_rate = 0.5
        
        # 4. Q1 勝率
        q1_wins = ((circuit_df['q_position'] == 1) & 
                   (circuit_df['final_position'] == 1)).sum()
        q1_total = (circuit_df['q_position'] == 1).sum()
        q1_win_rate = q1_wins / q1_total if q1_total > 0 else 0.5
        
        # 計算綜合難度
        # 相關性高 = 難超車
        # 位置保持率高 = 難超車  
        # Q1 勝率高 = 難超車
        # 進步率低 = 難超車
        
        difficulty = (
            0.40 * np.clip(correlation, 0, 1) +      # Q相關性 (最重要)
            0.25 * retention +                        # 位置保持率
            0.20 * q1_win_rate +                      # Q1 勝率
            0.15 * (1 - forward_rate)                 # 進步率 (反向)
        )
        
        # 限制範圍 [0.20, 0.95]
        difficulty = float(np.clip(difficulty, 0.20, 0.95))
        
        results[circuit] = {
            'difficulty': difficulty,
            'q_correlation': float(correlation) if not np.isnan(correlation) else 0.5,
            'position_retention': float(retention),
            'q1_win_rate': float(q1_win_rate),
            'forward_rate': float(forward_rate),
            'avg_position_change': float(avg_position_change),
            'sample_size': int(len(circuit_df)),
        }
    
    return results


def main():
    print(f"\n{'='*60}")
    print("賽道超車難度分析器 v2")
    print(f"{'='*60}")
    
    # 載入數據
    print("\n[1] Loading FP3/Q compensation data...")
    df = load_compensation_data()
    print(f"    Total records: {len(df)}")
    
    # 計算難度
    print("\n[2] Calculating circuit difficulty...")
    difficulty_scores = calculate_circuit_difficulty(df)
    
    # 保存結果
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "circuit_overtake_difficulty.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(difficulty_scores, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Saved to: {output_file}")
    
    # 顯示排名
    print(f"\n{'='*60}")
    print("Circuit Overtake Difficulty Ranking")
    print("(Higher = Harder to overtake)")
    print(f"{'='*60}")
    
    sorted_circuits = sorted(difficulty_scores.items(), 
                            key=lambda x: x[1]['difficulty'], 
                            reverse=True)
    
    for i, (circuit, stats) in enumerate(sorted_circuits, 1):
        print(f"{i:2d}. {circuit:15s}: {stats['difficulty']:.3f} "
              f"(Q_corr={stats['q_correlation']:.2f}, "
              f"Q1_win={stats['q1_win_rate']:.2f}, "
              f"N={stats['sample_size']})")
    
    # 生成 Python 字典格式
    print(f"\n{'='*60}")
    print("Python Dictionary (for predictor.py)")
    print(f"{'='*60}")
    print("CIRCUIT_OVERTAKE_DIFFICULTY = {")
    for circuit, stats in sorted_circuits:
        print(f"    '{circuit}': {stats['difficulty']:.2f},")
    print("}")


if __name__ == "__main__":
    main()
