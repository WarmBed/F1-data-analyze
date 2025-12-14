#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
輪胎性能自動訓練系統

功能:
1. 每場比賽後自動收集輪胎數據
2. 按輪胎種類分別訓練
3. 檢測配方變化 (2025 可能不同)
4. 生成更新建議

架構:
- TyreDataCollector: 收集單場比賽數據
- TyrePerformanceTrainer: 訓練輪胎模型
- TyreConfigUpdater: 生成配置更新

輸出:
- data/live_win_probability/tyre_performance_trained.json (累積數據)
- data/live_win_probability/tyre_config_update.json (建議更新)

使用方式:
    # 訓練單場比賽
    python train_tyre_model.py --year 2025 --race Monaco
    
    # 訓練整季
    python train_tyre_model.py --year 2025 --all
    
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')
    # 比較年度差異
    python train_tyre_model.py --compare 2024 2025
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
import pandas as pd

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import fastf1
    fastf1.Cache.enable_cache(str(PROJECT_ROOT / "f1_analysis_cache"))
    FASTF1_AVAILABLE = True
except ImportError:
    FASTF1_AVAILABLE = False
    print("[ERROR] FastF1 not installed")

DATA_DIR = PROJECT_ROOT / "data" / "live_win_probability"
TYRE_DATA_FILE = DATA_DIR / "tyre_training_data.json"
TYRE_CONFIG_FILE = DATA_DIR / "tyre_performance_trained.json"


@dataclass
class TyreStintData:
    """單個 stint 的輪胎數據"""
    year: int
    race: str
    driver: str
    compound: str
    stint_number: int
    start_lap: int
    end_lap: int
    lap_times: List[float]  # 秒
    avg_pace: float  # 平均圈時
    degradation_rate: float  # 秒/圈
    cliff_detected: bool
    cliff_lap: Optional[int]


@dataclass 
class TyrePerformanceStats:
    """輪胎性能統計"""
    compound: str
    year: int
    sample_size: int
    avg_new_pace: float  # 新胎平均圈時 (秒)
    relative_speed: float  # 相對 SOFT 的速度係數
    avg_degradation: float  # 平均衰退率 (秒/圈)
    deg_std: float  # 衰退率標準差
    avg_cliff_lap: float  # 平均 cliff 圈數
    cliff_rate: float  # cliff 發生率


class TyreDataCollector:
    """輪胎數據收集器"""
    
    def __init__(self):
        self.collected_data: List[TyreStintData] = []
        
    def collect_race(self, year: int, race: str) -> List[TyreStintData]:
        """
        收集單場比賽的輪胎數據
        
        Returns:
            List of TyreStintData
        """
        if not FASTF1_AVAILABLE:
            print(f"[ERROR] FastF1 not available")
            return []
            
        try:
            print(f"  [COLLECT] {year} {race}...")
            
            session = fastf1.get_session(year, race, 'R')
            session.load(laps=True, telemetry=False, weather=False, messages=False)
            
            laps = session.laps
            if laps.empty:
                return []
            
            stints = []
            
            # 按車手和 stint 分組
            for driver in laps['Driver'].unique():
                driver_laps = laps[laps['Driver'] == driver].sort_values('LapNumber')
                
                # 識別 stint (輪胎變化)
                stint_groups = self._identify_stints(driver_laps)
                
                for stint_num, stint_laps in enumerate(stint_groups, 1):
                    stint_data = self._analyze_stint(
                        year, race, driver, stint_num, stint_laps
                    )
                    if stint_data:
                        stints.append(stint_data)
                        self.collected_data.append(stint_data)
            
            print(f"    → Collected {len(stints)} stints")
            return stints
            
        except Exception as e:
            print(f"  [ERROR] {year} {race}: {e}")
            return []
    
    def _identify_stints(self, driver_laps: pd.DataFrame) -> List[pd.DataFrame]:
        """識別不同的輪胎 stint"""
        stints = []
        current_stint = []
        prev_compound = None
        prev_tyre_life = 0
        
        for _, lap in driver_laps.iterrows():
            compound = lap.get('Compound', '')
            tyre_life = lap.get('TyreLife', 0)
            
            # 檢測進站 (輪胎變化或胎齡重置)
            is_new_stint = (
                compound != prev_compound or 
                (tyre_life < prev_tyre_life - 1)  # 胎齡跳躍
            )
            
            if is_new_stint and current_stint:
                stints.append(pd.DataFrame(current_stint))
                current_stint = []
            
            current_stint.append(lap)
            prev_compound = compound
            prev_tyre_life = tyre_life if not pd.isna(tyre_life) else 0
        
        if current_stint:
            stints.append(pd.DataFrame(current_stint))
        
        return stints
    
    def _analyze_stint(
        self, 
        year: int, 
        race: str, 
        driver: str, 
        stint_num: int,
        stint_laps: pd.DataFrame
    ) -> Optional[TyreStintData]:
        """分析單個 stint"""
        if len(stint_laps) < 5:
            return None
            
        compound = stint_laps.iloc[0].get('Compound', 'UNKNOWN')
        if compound in ['UNKNOWN', None, '']:
            return None
        
        # 提取圈時
        lap_times = []
        for _, lap in stint_laps.iterrows():
            lt = lap.get('LapTime')
            if pd.isna(lt):
                continue
            if hasattr(lt, 'total_seconds'):
                lt_sec = lt.total_seconds()
            else:
                lt_sec = float(lt)
            # 過濾異常值
            if 60 < lt_sec < 180:
                lap_times.append(lt_sec)
        
        if len(lap_times) < 5:
            return None
        
        # 計算統計
        avg_pace = np.median(lap_times)
        
        # 計算衰退率 (線性迴歸)
        if len(lap_times) >= 10:
            x = np.arange(len(lap_times))
            slope, _ = np.polyfit(x, lap_times, 1)
            degradation_rate = slope  # 秒/圈
        else:
            degradation_rate = 0.0
        
        # 檢測 cliff (圈時突然增加超過 1.5 秒)
        cliff_detected = False
        cliff_lap = None
        for i in range(5, len(lap_times)):
            if lap_times[i] - lap_times[i-1] > 1.5:
                cliff_detected = True
                cliff_lap = int(stint_laps.iloc[i].get('TyreLife', i))
                break
        
        return TyreStintData(
            year=year,
            race=race,
            driver=driver,
            compound=compound.upper(),
            stint_number=stint_num,
            start_lap=int(stint_laps.iloc[0].get('LapNumber', 1)),
            end_lap=int(stint_laps.iloc[-1].get('LapNumber', 1)),
            lap_times=lap_times,
            avg_pace=float(avg_pace),
            degradation_rate=float(degradation_rate),
            cliff_detected=cliff_detected,
            cliff_lap=cliff_lap,
        )


class TyrePerformanceTrainer:
    """輪胎性能訓練器"""
    
    def __init__(self):
        self.stats: Dict[str, Dict[int, TyrePerformanceStats]] = {}  # {compound: {year: stats}}
        
    def train(self, data: List[TyreStintData]) -> Dict[str, TyrePerformanceStats]:
        """
        訓練輪胎模型
        
        Returns:
            {compound: TyrePerformanceStats}
        """
        if not data:
            return {}
        
        df = pd.DataFrame([asdict(d) for d in data])
        
        results = {}
        
        # 計算 SOFT 新胎基準
        soft_data = df[df['compound'] == 'SOFT']
        if not soft_data.empty:
            # 取 stint 前 3 圈的平均作為「新胎」速度
            soft_new_paces = []
            for _, stint in soft_data.iterrows():
                lap_times = stint['lap_times']
                if len(lap_times) >= 3:
                    soft_new_paces.append(np.mean(lap_times[:3]))
            baseline_pace = np.median(soft_new_paces) if soft_new_paces else 100.0
        else:
            baseline_pace = df['avg_pace'].median()
        
        # 按輪胎種類統計
        for compound in ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']:
            compound_df = df[df['compound'] == compound]
            
            if len(compound_df) < 5:
                continue
            
            # 新胎速度 (stint 前 3 圈)
            new_paces = []
            for _, stint in compound_df.iterrows():
                lap_times = stint['lap_times']
                if len(lap_times) >= 3:
                    new_paces.append(np.mean(lap_times[:3]))
            
            if new_paces:
                avg_new_pace = np.median(new_paces)
                relative_speed = baseline_pace / avg_new_pace  # >1 = 比 SOFT 快
            else:
                avg_new_pace = baseline_pace
                relative_speed = 1.0
            
            # 衰退率
            deg_rates = compound_df['degradation_rate'].values
            avg_deg = np.median(deg_rates)
            deg_std = np.std(deg_rates)
            
            # cliff 統計
            cliff_laps = compound_df[compound_df['cliff_detected']]['cliff_lap'].dropna()
            if len(cliff_laps) > 0:
                avg_cliff = np.median(cliff_laps)
                cliff_rate = len(cliff_laps) / len(compound_df)
            else:
                avg_cliff = 40.0  # 預設
                cliff_rate = 0.0
            
            year = int(compound_df['year'].mode().iloc[0]) if len(compound_df) > 0 else 2024
            
            results[compound] = TyrePerformanceStats(
                compound=compound,
                year=year,
                sample_size=len(compound_df),
                avg_new_pace=float(avg_new_pace),
                relative_speed=float(np.clip(relative_speed, 0.85, 1.02)),
                avg_degradation=float(avg_deg),
                deg_std=float(deg_std),
                avg_cliff_lap=float(avg_cliff),
                cliff_rate=float(cliff_rate),
            )
            
            # 存儲年度數據
            if compound not in self.stats:
                self.stats[compound] = {}
            self.stats[compound][year] = results[compound]
        
        return results
    
    def compare_years(self, year1: int, year2: int) -> Dict[str, Dict]:
        """
        比較兩年的輪胎性能差異
        
        Returns:
            {compound: {speed_diff, deg_diff, cliff_diff, significant}}
        """
        comparison = {}
        
        for compound in ['SOFT', 'MEDIUM', 'HARD']:
            if compound not in self.stats:
                continue
            
            stats1 = self.stats[compound].get(year1)
            stats2 = self.stats[compound].get(year2)
            
            if not stats1 or not stats2:
                continue
            
            speed_diff = stats2.relative_speed - stats1.relative_speed
            deg_diff = stats2.avg_degradation - stats1.avg_degradation
            cliff_diff = stats2.avg_cliff_lap - stats1.avg_cliff_lap
            
            # 判斷是否有顯著變化 (>5% 或 >2 圈)
            significant = (
                abs(speed_diff) > 0.005 or  # 0.5% 速度差
                abs(deg_diff) > 0.02 or     # 0.02s/圈 衰退差
                abs(cliff_diff) > 3         # 3 圈 cliff 差
            )
            
            comparison[compound] = {
                'year1': year1,
                'year2': year2,
                'speed_diff': speed_diff,
                'speed_diff_pct': speed_diff * 100,
                'deg_diff': deg_diff,
                'cliff_diff': cliff_diff,
                'significant': significant,
                'recommendation': self._generate_recommendation(
                    compound, speed_diff, deg_diff, cliff_diff
                ),
            }
        
        return comparison
    
    def _generate_recommendation(
        self, 
        compound: str, 
        speed_diff: float,
        deg_diff: float,
        cliff_diff: float
    ) -> str:
        """生成更新建議"""
        if abs(speed_diff) < 0.002 and abs(deg_diff) < 0.01 and abs(cliff_diff) < 2:
            return "No update needed"
        
        parts = []
        if speed_diff > 0.002:
            parts.append(f"faster by {speed_diff*100:.2f}%")
        elif speed_diff < -0.002:
            parts.append(f"slower by {abs(speed_diff)*100:.2f}%")
        
        if deg_diff > 0.01:
            parts.append(f"degrades faster by {deg_diff:.3f}s/lap")
        elif deg_diff < -0.01:
            parts.append(f"degrades slower by {abs(deg_diff):.3f}s/lap")
        
        if cliff_diff > 2:
            parts.append(f"cliff {cliff_diff:.0f} laps later")
        elif cliff_diff < -2:
            parts.append(f"cliff {abs(cliff_diff):.0f} laps earlier")
        
        return f"UPDATE {compound}: " + ", ".join(parts) if parts else "No significant change"
    
    def generate_config(self) -> Dict[str, Dict]:
        """
        生成 TYRE_PERFORMANCE 配置
        
        Returns:
            {compound: {speed, deg_per_lap, ideal_laps, cliff_lap}}
        """
        config = {}
        
        for compound, year_stats in self.stats.items():
            # 使用最新年度的數據
            latest_year = max(year_stats.keys())
            stats = year_stats[latest_year]
            
            # 將衰退率轉換為相對係數
            # 假設基準圈時 100s，0.03s/圈 → 0.0003/圈
            baseline_time = stats.avg_new_pace if stats.avg_new_pace > 0 else 100.0
            deg_coefficient = stats.avg_degradation / baseline_time
            
            config[compound] = {
                'speed': round(stats.relative_speed, 4),
                'deg_per_lap': round(max(0.0001, deg_coefficient), 5),
                'ideal_laps': int(stats.avg_cliff_lap * 0.7),  # cliff 前 70%
                'cliff_lap': int(stats.avg_cliff_lap),
                'trained_from': f"{stats.year} ({stats.sample_size} stints)",
            }
        
        return config


def save_training_data(data: List[TyreStintData], filepath: Path):
    """保存訓練數據"""
    existing = []
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    
    # 合併數據 (避免重複)
    existing_keys = {(d['year'], d['race'], d['driver'], d['stint_number']) for d in existing}
    
    for stint in data:
        key = (stint.year, stint.race, stint.driver, stint.stint_number)
        if key not in existing_keys:
            existing.append(asdict(stint))
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    
    print(f"[SAVED] {len(existing)} stints to {filepath}")


def load_training_data(filepath: Path) -> List[TyreStintData]:
    """載入訓練數據"""
    if not filepath.exists():
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return [TyreStintData(**d) for d in data]


def main():
    parser = argparse.ArgumentParser(description="輪胎性能自動訓練系統")
    parser.add_argument('--year', type=int, default=2024)
    parser.add_argument('--race', type=str, default=None, help="單場比賽名稱")
    parser.add_argument('--all', action='store_true', help="訓練整季")
    parser.add_argument('--compare', type=int, nargs=2, help="比較兩年: --compare 2024 2025")
    parser.add_argument('--max-races', type=int, default=None)
    args = parser.parse_args()
    
    if not FASTF1_AVAILABLE:
        print("[ERROR] FastF1 not available")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"輪胎性能自動訓練系統")
    print(f"{'='*60}")
    
    collector = TyreDataCollector()
    trainer = TyrePerformanceTrainer()
    
    # 載入已有數據
    existing_data = load_training_data(TYRE_DATA_FILE)
    if existing_data:
        print(f"[LOAD] {len(existing_data)} existing stints")
        collector.collected_data = existing_data
    
    # 收集新數據
    if args.race:
        # 單場比賽
        new_data = collector.collect_race(args.year, args.race)
        if new_data:
            save_training_data(collector.collected_data, TYRE_DATA_FILE)
    elif args.all:
        # 整季
        try:
            schedule = fastf1.get_event_schedule(args.year)
            races = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
            
            if args.max_races:
                races = races[:args.max_races]
            
            for race in races:
                collector.collect_race(args.year, race)
            
            save_training_data(collector.collected_data, TYRE_DATA_FILE)
        except Exception as e:
            print(f"[ERROR] Cannot get schedule: {e}")
    
    # 訓練模型
    print(f"\n[TRAIN] Training on {len(collector.collected_data)} stints...")
    results = trainer.train(collector.collected_data)
    
    # 顯示結果
    print(f"\n{'='*60}")
    print("Training Results")
    print(f"{'='*60}")
    
    for compound, stats in results.items():
        print(f"\n{compound}:")
        print(f"  Speed:       {stats.relative_speed:.4f} (relative to SOFT)")
        print(f"  Degradation: {stats.avg_degradation:.4f}s/lap (std={stats.deg_std:.4f})")
        print(f"  Cliff:       Lap {stats.avg_cliff_lap:.0f} ({stats.cliff_rate*100:.1f}% detected)")
        print(f"  Samples:     {stats.sample_size} stints")
    
    # 比較年度
    if args.compare:
        year1, year2 = args.compare
        print(f"\n{'='*60}")
        print(f"Year Comparison: {year1} vs {year2}")
        print(f"{'='*60}")
        
        comparison = trainer.compare_years(year1, year2)
        for compound, diff in comparison.items():
            print(f"\n{compound}:")
            print(f"  Speed: {diff['speed_diff_pct']:+.2f}%")
            print(f"  Deg:   {diff['deg_diff']:+.4f}s/lap")
            print(f"  Cliff: {diff['cliff_diff']:+.0f} laps")
            print(f"  → {diff['recommendation']}")
    
    # 生成配置
    config = trainer.generate_config()
    
    TYRE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TYRE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Config saved to: {TYRE_CONFIG_FILE}")
    
    # 顯示 Python 格式
    print(f"\n{'='*60}")
    print("Python Dictionary (for predictor.py)")
    print(f"{'='*60}")
    print("TYRE_PERFORMANCE = {")
    for compound, cfg in config.items():
        print(f'    "{compound}": {{')
        print(f'        "speed": {cfg["speed"]},')
        print(f'        "deg_per_lap": {cfg["deg_per_lap"]},')
        print(f'        "ideal_laps": {cfg["ideal_laps"]},')
        print(f'        "cliff_lap": {cfg["cliff_lap"]},')
        print(f'    }},  # {cfg["trained_from"]}')
    print("}")


if __name__ == "__main__":
    main()
