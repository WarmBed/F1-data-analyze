#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 策略係數聯合訓練器 - 車隊+賽道+輪胎維度

功能：
1. 從 FastF1 收集 2023-2025 賽季數據
2. 數據清洗（排除 SC/PIT/異常圈）
3. 多元回歸擬合：輪胎衰退 + 燃油效果 + 賽道進化
4. 輸出車隊維度的係數到 JSON

訓練公式：
  圈速(t) = base_time 
          + (α × tyre_age + 0.5 × β × tyre_age²)  ← 輪胎衰退
          + (γ × fuel_consumed_kg)                 ← 燃油效果（負值）
          + (δ × lap_number)                       ← 賽道進化（負值）

使用方式：
  python train_strategy_coefficients.py --years 2023 2024 2025 --test-year 2025

作者: F1 Analysis Team
日期: 2026-01-11
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field, asdict
import logging
import numpy as np
import pandas as pd

# 機器學習庫
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# FastF1
try:
    import fastf1
    from fastf1 import Cache
except ImportError:
    print("錯誤：請安裝 fastf1: pip install fastf1")
    sys.exit(1)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# 賽道名稱對照
CIRCUIT_MAPPING = {
    'Bahrain': 'Bahrain',
    'Saudi Arabia': 'Jeddah',
    'Australia': 'Melbourne',
    'Japan': 'Suzuka',
    'China': 'Shanghai',
    'Miami': 'Miami',
    'Emilia Romagna': 'Imola',
    'Monaco': 'Monaco',
    'Canada': 'Montreal',
    'Spain': 'Barcelona',
    'Austria': 'Spielberg',
    'Great Britain': 'Silverstone',
    'Hungary': 'Hungaroring',
    'Belgium': 'Spa',
    'Netherlands': 'Zandvoort',
    'Italy': 'Monza',
    'Azerbaijan': 'Baku',
    'Singapore': 'Singapore',
    'United States': 'Austin',
    'Mexico': 'Mexico_City',
    'Brazil': 'Sao_Paulo',
    'Las Vegas': 'Las_Vegas',
    'Qatar': 'Qatar',
    'Abu Dhabi': 'Abu_Dhabi',
}

# 車隊名稱對照
TEAM_MAPPING = {
    'Red Bull Racing': 'Red Bull Racing',
    'Red Bull': 'Red Bull Racing',
    'Ferrari': 'Ferrari',
    'Mercedes': 'Mercedes',
    'McLaren': 'McLaren',
    'Aston Martin': 'Aston Martin',
    'Alpine': 'Alpine',
    'Williams': 'Williams',
    'AlphaTauri': 'AlphaTauri',
    'RB': 'RB',
    'Alfa Romeo': 'Alfa Romeo',
    'Haas F1 Team': 'Haas',
    'Haas': 'Haas',
    'Kick Sauber': 'Sauber',
    'Sauber': 'Sauber',
}


@dataclass
class LapData:
    """單圈數據"""
    lap_number: int
    lap_time: float  # 秒
    tyre_compound: str
    tyre_age: int
    fuel_consumed_kg: float  # 估計已消耗燃油
    team: str
    driver: str
    is_valid: bool = True


@dataclass
class StintData:
    """單 Stint 數據"""
    stint_number: int
    compound: str
    start_lap: int
    end_lap: int
    laps: List[LapData] = field(default_factory=list)


@dataclass
class TrainingResult:
    """訓練結果"""
    team: str
    circuit: str
    compound: str
    base_rate: float  # 輪胎基礎衰退率
    acceleration: float  # 輪胎衰退加速度
    fuel_effect_per_kg: float  # 燃油效應係數
    track_evolution_per_lap: float  # 賽道進化基準
    r2_score: float
    mae: float
    sample_count: int


class StrategyCoefficientsTrainer:
    """策略係數聯合訓練器"""
    
    def __init__(self, cache_dir: str = "fastf1_cache", verbose: bool = True):
        """初始化訓練器"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.verbose = verbose
        
        # 設置 FastF1 緩存
        Cache.enable_cache(str(self.cache_dir))
        
        # 訓練數據
        self.all_lap_data: Dict[str, Dict[str, Dict[str, List[LapData]]]] = {}
        # 結構: {team: {circuit: {compound: [LapData]}}}
        
        # 訓練結果
        self.training_results: List[TrainingResult] = []
        
        # 燃油參數（估計）
        self.fuel_kg_per_lap = 1.8  # 平均每圈消耗
        self.total_fuel_kg = 110.0  # 起始燃油量
        
        logger.info("策略係數訓練器初始化完成")
        
    def load_race_data(self, year: int, race_name: str) -> Optional[List[LapData]]:
        """載入單場比賽數據"""
        try:
            logger.info(f"載入 {year} {race_name}...")
            
            # 獲取比賽
            session = fastf1.get_session(year, race_name, 'R')
            session.load(telemetry=False, weather=False, messages=False)
            
            laps = session.laps
            
            if laps.empty:
                logger.warning(f"  {race_name} 無圈速數據")
                return None
            
            lap_data_list = []
            
            for _, lap in laps.iterrows():
                # 跳過無效圈
                if lap['LapTime'] is None or pd.isna(lap['LapTime']):
                    continue
                    
                lap_time_sec = lap['LapTime'].total_seconds()
                
                # 跳過異常圈速
                if lap_time_sec < 60 or lap_time_sec > 180:
                    continue
                
                # 跳過 PIT 圈 - 使用 pd.isna 檢查
                pit_in = lap['PitInTime']
                pit_out = lap['PitOutTime']
                if not pd.isna(pit_in) or not pd.isna(pit_out):
                    continue
                    
                # 獲取輪胎資訊
                compound = lap['Compound'] if 'Compound' in lap.index else 'UNKNOWN'
                if pd.isna(compound):
                    compound = 'UNKNOWN'
                tyre_age = lap['TyreLife'] if 'TyreLife' in lap.index else 1
                
                if not isinstance(tyre_age, (int, float)) or pd.isna(tyre_age):
                    tyre_age = 1
                    
                # 獲取車隊
                team = lap['Team'] if 'Team' in lap.index else 'Unknown'
                if pd.isna(team):
                    team = 'Unknown'
                team = TEAM_MAPPING.get(team, team)
                
                driver = lap['Driver'] if 'Driver' in lap.index else 'Unknown'
                if pd.isna(driver):
                    driver = 'Unknown'
                lap_number = int(lap['LapNumber']) if 'LapNumber' in lap.index else 0
                
                # 估計已消耗燃油
                fuel_consumed = self.fuel_kg_per_lap * (lap_number - 1)
                
                # 檢查 SC/VSC 狀態 - TrackStatus 可能是數字或字串
                track_status = lap['TrackStatus'] if 'TrackStatus' in lap.index else '1'
                if pd.isna(track_status):
                    track_status = '1'
                track_status = str(track_status)
                is_sc = track_status in ['4', '5', '6', '7']  # SC/VSC 狀態
                
                lap_data = LapData(
                    lap_number=lap_number,
                    lap_time=lap_time_sec,
                    tyre_compound=compound.upper() if compound and not pd.isna(compound) else 'UNKNOWN',
                    tyre_age=int(tyre_age),
                    fuel_consumed_kg=fuel_consumed,
                    team=team,
                    driver=driver,
                    is_valid=not is_sc
                )
                
                lap_data_list.append(lap_data)
            
            logger.info(f"  載入 {len(lap_data_list)} 筆有效圈速")
            return lap_data_list
            
        except Exception as e:
            logger.error(f"  載入失敗: {e}")
            return None
    
    def collect_training_data(self, years: List[int], test_races: List[str] = None):
        """收集所有訓練數據"""
        import pandas as pd
        
        logger.info(f"收集訓練數據：{years}")
        
        for year in years:
            try:
                # 獲取該年所有比賽
                schedule = fastf1.get_event_schedule(year)
                
                for _, event in schedule.iterrows():
                    race_name = event['EventName']
                    
                    # 跳過測試賽
                    if 'Test' in race_name or 'Pre-Season' in race_name:
                        continue
                    
                    # 跳過測試比賽（如果指定）
                    if test_races and race_name in test_races:
                        logger.info(f"  跳過測試比賽: {race_name}")
                        continue
                    
                    circuit = CIRCUIT_MAPPING.get(race_name, race_name.replace(' ', '_'))
                    
                    lap_data = self.load_race_data(year, race_name)
                    
                    if not lap_data:
                        continue
                    
                    # 按車隊+賽道+輪胎分組
                    for lap in lap_data:
                        if not lap.is_valid:
                            continue
                            
                        team = lap.team
                        compound = lap.tyre_compound
                        
                        if compound not in ['SOFT', 'MEDIUM', 'HARD']:
                            continue
                        
                        if team not in self.all_lap_data:
                            self.all_lap_data[team] = {}
                        if circuit not in self.all_lap_data[team]:
                            self.all_lap_data[team][circuit] = {}
                        if compound not in self.all_lap_data[team][circuit]:
                            self.all_lap_data[team][circuit][compound] = []
                        
                        self.all_lap_data[team][circuit][compound].append(lap)
                        
            except Exception as e:
                logger.error(f"年份 {year} 處理失敗: {e}")
                continue
        
        # 統計
        total_laps = 0
        for team in self.all_lap_data:
            for circuit in self.all_lap_data[team]:
                for compound in self.all_lap_data[team][circuit]:
                    total_laps += len(self.all_lap_data[team][circuit][compound])
        
        logger.info(f"數據收集完成: {len(self.all_lap_data)} 車隊, {total_laps} 總圈數")
        
    def train_coefficients(self, min_samples: int = 30):
        """訓練所有係數"""
        logger.info("開始訓練係數...")
        
        for team in self.all_lap_data:
            for circuit in self.all_lap_data[team]:
                for compound in self.all_lap_data[team][circuit]:
                    laps = self.all_lap_data[team][circuit][compound]
                    
                    if len(laps) < min_samples:
                        continue
                    
                    result = self._fit_coefficients(team, circuit, compound, laps)
                    
                    if result:
                        self.training_results.append(result)
                        
        logger.info(f"訓練完成: {len(self.training_results)} 組係數")
        
    def _fit_coefficients(self, team: str, circuit: str, compound: str, 
                          laps: List[LapData]) -> Optional[TrainingResult]:
        """擬合單組係數"""
        try:
            # 準備特徵
            X = []
            y = []
            
            for lap in laps:
                # 特徵: [tyre_age, tyre_age², fuel_consumed, lap_number]
                features = [
                    lap.tyre_age,
                    lap.tyre_age ** 2 * 0.5,  # 加速度項
                    lap.fuel_consumed_kg,
                    lap.lap_number
                ]
                X.append(features)
                y.append(lap.lap_time)
            
            X = np.array(X)
            y = np.array(y)
            
            # 使用 Ridge 回歸（避免過擬合）
            model = Ridge(alpha=1.0)
            model.fit(X, y)
            
            # 預測並計算誤差
            y_pred = model.predict(X)
            mae = mean_absolute_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            
            # 提取係數
            # coef_ = [base_rate, acceleration_factor, fuel_effect, track_evo]
            base_rate = model.coef_[0]
            acceleration = model.coef_[1] * 2  # 還原 0.5 倍
            fuel_effect = model.coef_[2]
            track_evo = model.coef_[3]
            
            # 合理性檢查
            if base_rate < 0 or base_rate > 0.5:
                base_rate = 0.05  # 預設值
            if acceleration < 0:
                acceleration = 0.002
            if fuel_effect > 0:  # 燃油效果應該是負的
                fuel_effect = -0.03
            
            return TrainingResult(
                team=team,
                circuit=circuit,
                compound=compound,
                base_rate=round(base_rate, 5),
                acceleration=round(acceleration, 6),
                fuel_effect_per_kg=round(fuel_effect, 5),
                track_evolution_per_lap=round(track_evo, 5),
                r2_score=round(r2, 4),
                mae=round(mae, 4),
                sample_count=len(laps)
            )
            
        except Exception as e:
            logger.warning(f"  擬合失敗 {team}/{circuit}/{compound}: {e}")
            return None
    
    def evaluate_accuracy(self, test_year: int, test_races: List[str]) -> Dict[str, Any]:
        """評估訓練結果的準確性"""
        logger.info(f"評估準確性（測試年份: {test_year}）...")
        
        import pandas as pd
        
        results = {
            'before': {'mae': [], 'predictions': []},
            'after': {'mae': [], 'predictions': []}
        }
        
        # 舊係數（預設值）
        default_coeffs = {
            'SOFT': {'base_rate': 0.08, 'acceleration': 0.003},
            'MEDIUM': {'base_rate': 0.05, 'acceleration': 0.002},
            'HARD': {'base_rate': 0.03, 'acceleration': 0.001}
        }
        default_fuel = -0.03
        
        for race_name in test_races:
            lap_data = self.load_race_data(test_year, race_name)
            
            if not lap_data:
                continue
                
            circuit = CIRCUIT_MAPPING.get(race_name, race_name.replace(' ', '_'))
            
            for lap in lap_data:
                if not lap.is_valid:
                    continue
                if lap.tyre_compound not in ['SOFT', 'MEDIUM', 'HARD']:
                    continue
                
                actual = lap.lap_time
                
                # 估計 base_time（使用該 stint 的前幾圈平均）
                base_time = actual - 2.0  # 簡化：假設 base 比實際快 2 秒
                
                # 舊預測
                old_coeffs = default_coeffs.get(lap.tyre_compound, default_coeffs['MEDIUM'])
                old_pred = base_time + (
                    old_coeffs['base_rate'] * lap.tyre_age +
                    0.5 * old_coeffs['acceleration'] * lap.tyre_age ** 2 +
                    default_fuel * lap.fuel_consumed_kg
                )
                
                # 新預測（查找訓練結果）
                new_coeffs = self._get_trained_coeffs(lap.team, circuit, lap.tyre_compound)
                if new_coeffs:
                    new_pred = base_time + (
                        new_coeffs['base_rate'] * lap.tyre_age +
                        0.5 * new_coeffs['acceleration'] * lap.tyre_age ** 2 +
                        new_coeffs['fuel_effect'] * lap.fuel_consumed_kg +
                        new_coeffs['track_evo'] * lap.lap_number
                    )
                else:
                    new_pred = old_pred  # Fallback
                
                results['before']['mae'].append(abs(actual - old_pred))
                results['after']['mae'].append(abs(actual - new_pred))
                
                results['before']['predictions'].append({
                    'lap': lap.lap_number,
                    'actual': actual,
                    'predicted': old_pred,
                    'error': actual - old_pred
                })
                results['after']['predictions'].append({
                    'lap': lap.lap_number,
                    'actual': actual,
                    'predicted': new_pred,
                    'error': actual - new_pred
                })
        
        # 計算平均 MAE
        before_mae = np.mean(results['before']['mae']) if results['before']['mae'] else 0
        after_mae = np.mean(results['after']['mae']) if results['after']['mae'] else 0
        
        improvement = (before_mae - after_mae) / before_mae * 100 if before_mae > 0 else 0
        
        summary = {
            'test_year': test_year,
            'test_races': test_races,
            'before_mae': round(before_mae, 4),
            'after_mae': round(after_mae, 4),
            'improvement_pct': round(improvement, 2),
            'sample_count': len(results['before']['mae'])
        }
        
        logger.info(f"評估結果:")
        logger.info(f"  訓練前 MAE: {summary['before_mae']}s")
        logger.info(f"  訓練後 MAE: {summary['after_mae']}s")
        logger.info(f"  改善: {summary['improvement_pct']}%")
        
        return summary
    
    def _get_trained_coeffs(self, team: str, circuit: str, compound: str) -> Optional[Dict]:
        """獲取訓練後的係數"""
        for result in self.training_results:
            if result.team == team and result.circuit == circuit and result.compound == compound:
                return {
                    'base_rate': result.base_rate,
                    'acceleration': result.acceleration,
                    'fuel_effect': result.fuel_effect_per_kg,
                    'track_evo': result.track_evolution_per_lap
                }
        return None
    
    def save_results(self, output_path: str):
        """儲存訓練結果"""
        output = {
            'version': '1.0',
            'description': '車隊+賽道+輪胎維度的策略係數',
            'teams': {}
        }
        
        for result in self.training_results:
            if result.team not in output['teams']:
                output['teams'][result.team] = {'circuits': {}}
            
            if result.circuit not in output['teams'][result.team]['circuits']:
                output['teams'][result.team]['circuits'][result.circuit] = {
                    'compounds': {},
                    'fuel_effect_per_kg': result.fuel_effect_per_kg,
                    'track_evolution_baseline': result.track_evolution_per_lap
                }
            
            output['teams'][result.team]['circuits'][result.circuit]['compounds'][result.compound] = {
                'base_rate': result.base_rate,
                'acceleration': result.acceleration,
                'r2_score': result.r2_score,
                'sample_count': result.sample_count
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"結果已儲存: {output_path}")


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='F1 策略係數聯合訓練器')
    parser.add_argument('--years', nargs='+', type=int, default=[2023, 2024, 2025],
                        help='訓練年份')
    parser.add_argument('--test-year', type=int, default=2025,
                        help='測試年份')
    parser.add_argument('--test-races', nargs='+', default=['Abu Dhabi', 'Qatar'],
                        help='測試比賽')
    parser.add_argument('--output', type=str, 
                        default='config/team_strategy_coefficients.json',
                        help='輸出檔案路徑')
    parser.add_argument('--cache-dir', type=str, default='fastf1_cache',
                        help='FastF1 緩存目錄')
    
    args = parser.parse_args()
    
    # 固定 pandas import
    global pd
    import pandas as pd
    
    trainer = StrategyCoefficientsTrainer(cache_dir=args.cache_dir)
    
    # 1. 收集訓練數據（排除測試比賽）
    trainer.collect_training_data(args.years, test_races=args.test_races)
    
    # 2. 訓練係數
    trainer.train_coefficients()
    
    # 3. 評估準確性
    summary = trainer.evaluate_accuracy(args.test_year, args.test_races)
    
    # 4. 儲存結果
    trainer.save_results(args.output)
    
    print("\n" + "="*60)
    print("訓練完成!")
    print(f"  訓練前 MAE: {summary['before_mae']}s")
    print(f"  訓練後 MAE: {summary['after_mae']}s")
    print(f"  改善: {summary['improvement_pct']}%")
    print("="*60)


if __name__ == '__main__':
    main()
