#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F1 策略係數訓練器 V2 - XGBoost 版本

改進點：
1. 使用 XGBoost 非線性模型
2. 目標變量改為 delta（相對於 stint 基準圈速的差異）
3. 增加特徵工程（stint 內位置、累積圈數等）
4. 5-fold 交叉驗證
5. 異常值過濾（IQR 方法）
6. 嚴格的係數範圍限制

作者: F1 Analysis Team
版本: 2.0.0
日期: 2026-01-11
"""

import argparse
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import fastf1
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 常數定義
# ============================================================================

TARGET_DRIVERS = ['VER', 'NOR', 'LEC']

RACES_2025 = [
    'Bahrain', 'Saudi Arabia', 'Australia', 'Japan', 'China',
    'Miami', 'Emilia Romagna', 'Monaco', 'Canada', 'Spain',
    'Austria', 'Great Britain', 'Hungary', 'Belgium', 'Netherlands',
    'Italy', 'Azerbaijan', 'Singapore', 'United States', 'Mexico',
    'Brazil', 'Las Vegas', 'Qatar', 'Abu Dhabi'
]

# 賽道特性分類
CIRCUIT_TYPES = {
    'street': ['Monaco', 'Singapore', 'Azerbaijan', 'Las Vegas', 'Saudi Arabia', 'Miami'],
    'high_deg': ['Bahrain', 'Spain', 'Hungary', 'China', 'Mexico'],
    'low_deg': ['Italy', 'Belgium', 'Great Britain', 'Austria', 'Netherlands'],
    'mixed': ['Japan', 'Australia', 'Canada', 'Brazil', 'Qatar', 'Abu Dhabi', 'United States', 'Emilia Romagna']
}

# 賽道名稱映射到係數檔案格式
COEFF_CIRCUIT_MAPPING = {
    'Bahrain': 'Bahrain_Grand_Prix',
    'Saudi Arabia': 'Saudi_Arabian_Grand_Prix',
    'Australia': 'Australian_Grand_Prix',
    'Japan': 'Japanese_Grand_Prix',
    'China': 'Chinese_Grand_Prix',
    'Miami': 'Miami_Grand_Prix',
    'Emilia Romagna': 'Emilia_Romagna_Grand_Prix',
    'Monaco': 'Monaco_Grand_Prix',
    'Canada': 'Canadian_Grand_Prix',
    'Spain': 'Spanish_Grand_Prix',
    'Austria': 'Austrian_Grand_Prix',
    'Great Britain': 'British_Grand_Prix',
    'Hungary': 'Hungarian_Grand_Prix',
    'Belgium': 'Belgian_Grand_Prix',
    'Netherlands': 'Dutch_Grand_Prix',
    'Italy': 'Italian_Grand_Prix',
    'Azerbaijan': 'Azerbaijan_Grand_Prix',
    'Singapore': 'Singapore_Grand_Prix',
    'United States': 'United_States_Grand_Prix',
    'Mexico': 'Mexico_City_Grand_Prix',
    'Brazil': 'São_Paulo_Grand_Prix',
    'Las Vegas': 'Las_Vegas_Grand_Prix',
    'Qatar': 'Qatar_Grand_Prix',
    'Abu Dhabi': 'Abu_Dhabi_Grand_Prix',
}

# 車隊名稱標準化
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
    'Racing Bulls': 'Racing Bulls',
    'Alfa Romeo': 'Alfa Romeo',
    'Haas F1 Team': 'Haas',
    'Haas': 'Haas',
    'Sauber': 'Sauber',
    'Kick Sauber': 'Sauber',
}

# Baseline 係數（作為 fallback）
BASELINE_COEFFICIENTS = {
    'SOFT': {'base_rate': 0.08, 'acceleration': 0.003},
    'MEDIUM': {'base_rate': 0.05, 'acceleration': 0.002},
    'HARD': {'base_rate': 0.03, 'acceleration': 0.001}
}
DEFAULT_FUEL_EFFECT = -0.03

# ============================================================================
# 數據結構
# ============================================================================

@dataclass
class StintData:
    """Stint 數據"""
    year: int
    race: str
    circuit: str
    driver: str
    team: str
    stint_number: int
    compound: str
    start_lap: int
    end_lap: int
    base_time: float  # stint 的基準圈速
    laps: List[Dict] = field(default_factory=list)


@dataclass 
class TrainingResult:
    """訓練結果"""
    circuit: str
    compound: str
    base_rate: float
    acceleration: float
    fuel_effect: float
    r2_score: float
    mae: float
    cv_mae: float  # 交叉驗證 MAE
    sample_count: int
    feature_importance: Dict[str, float] = field(default_factory=dict)


# ============================================================================
# XGBoost 訓練器
# ============================================================================

class XGBoostStrategyTrainer:
    """XGBoost 策略係數訓練器"""
    
    def __init__(self, cache_dir: str = 'f1_analysis_cache'):
        self.cache_dir = cache_dir
        fastf1.Cache.enable_cache(cache_dir)
        
        self.fuel_kg_per_lap = 1.8
        self.all_stints: List[StintData] = []
        self.training_data: pd.DataFrame = None
        self.models: Dict[str, Dict[str, xgb.XGBRegressor]] = {}  # circuit -> compound -> model
        self.results: List[TrainingResult] = []
        
    def load_race_stints(self, year: int, race_name: str) -> List[StintData]:
        """載入單場比賽的 stint 數據"""
        stints = []
        
        try:
            session = fastf1.get_session(year, race_name, 'R')
            session.load(telemetry=False, weather=False, messages=False)
            
            laps = session.laps
            if laps.empty:
                return []
            
            circuit = COEFF_CIRCUIT_MAPPING.get(race_name, race_name.replace(' ', '_') + '_Grand_Prix')
            
            # 按車手分組處理
            for driver in laps['Driver'].unique():
                driver_laps = laps[laps['Driver'] == driver].copy()
                driver_laps = driver_laps.sort_values('LapNumber')
                
                if driver_laps.empty:
                    continue
                
                team = driver_laps.iloc[0]['Team']
                if pd.isna(team):
                    team = 'Unknown'
                team = TEAM_MAPPING.get(team, team)
                
                # 識別 stints（通過輪胎配方變化）
                current_stint = None
                stint_number = 0
                
                for _, lap in driver_laps.iterrows():
                    lap_time = lap['LapTime']
                    if pd.isna(lap_time):
                        continue
                    
                    lap_time_sec = lap_time.total_seconds()
                    if lap_time_sec < 60 or lap_time_sec > 180:
                        continue
                    
                    # 跳過 PIT 圈
                    if not pd.isna(lap['PitInTime']) or not pd.isna(lap['PitOutTime']):
                        continue
                    
                    compound = lap['Compound']
                    if pd.isna(compound) or compound.upper() not in ['SOFT', 'MEDIUM', 'HARD']:
                        continue
                    compound = compound.upper()
                    
                    tyre_age = lap['TyreLife']
                    if pd.isna(tyre_age):
                        tyre_age = 1
                    tyre_age = int(tyre_age)
                    
                    lap_number = int(lap['LapNumber'])
                    
                    # 檢查 SC/VSC
                    track_status = lap['TrackStatus'] if 'TrackStatus' in lap.index else '1'
                    if pd.isna(track_status):
                        track_status = '1'
                    is_sc = str(track_status) in ['4', '5', '6', '7']
                    if is_sc:
                        continue
                    
                    # 偵測新 stint
                    if current_stint is None or current_stint.compound != compound:
                        if current_stint is not None and len(current_stint.laps) >= 3:
                            # 計算 base_time（前 3 圈最快）
                            first_laps = [l['lap_time'] for l in current_stint.laps[:5]]
                            current_stint.base_time = min(first_laps) if first_laps else 90.0
                            current_stint.end_lap = current_stint.laps[-1]['lap_number']
                            stints.append(current_stint)
                        
                        stint_number += 1
                        current_stint = StintData(
                            year=year,
                            race=race_name,
                            circuit=circuit,
                            driver=driver,
                            team=team,
                            stint_number=stint_number,
                            compound=compound,
                            start_lap=lap_number,
                            end_lap=0,
                            base_time=0
                        )
                    
                    # 添加圈速數據
                    fuel_consumed = self.fuel_kg_per_lap * (lap_number - 1)
                    
                    current_stint.laps.append({
                        'lap_number': lap_number,
                        'lap_time': lap_time_sec,
                        'tyre_age': tyre_age,
                        'fuel_consumed': fuel_consumed,
                        'stint_lap': len(current_stint.laps) + 1  # stint 內的圈數
                    })
                
                # 保存最後一個 stint
                if current_stint is not None and len(current_stint.laps) >= 3:
                    first_laps = [l['lap_time'] for l in current_stint.laps[:5]]
                    current_stint.base_time = min(first_laps) if first_laps else 90.0
                    current_stint.end_lap = current_stint.laps[-1]['lap_number']
                    stints.append(current_stint)
            
            return stints
            
        except Exception as e:
            logger.error(f"  載入失敗: {e}")
            return []
    
    def collect_training_data(self, years: List[int], test_year: int = None):
        """收集所有訓練數據"""
        logger.info(f"收集訓練數據：{years}")
        
        for year in years:
            try:
                schedule = fastf1.get_event_schedule(year)
                
                for _, event in schedule.iterrows():
                    race_name = event['EventName']
                    
                    if 'Test' in race_name or 'Pre-Season' in race_name:
                        continue
                    
                    logger.info(f"載入 {year} {race_name}...")
                    stints = self.load_race_stints(year, race_name)
                    
                    if stints:
                        self.all_stints.extend(stints)
                        logger.info(f"  載入 {len(stints)} 個 stints")
                        
            except Exception as e:
                logger.error(f"年份 {year} 處理失敗: {e}")
                continue
        
        logger.info(f"數據收集完成: {len(self.all_stints)} 個 stints")
        
        # 轉換為 DataFrame
        self._build_training_dataframe()
    
    def _build_training_dataframe(self):
        """構建訓練用的 DataFrame"""
        rows = []
        
        for stint in self.all_stints:
            if stint.base_time <= 0:
                continue
                
            for lap in stint.laps:
                # 計算 delta（相對於 base_time 的差異）
                delta = lap['lap_time'] - stint.base_time
                
                # 跳過極端異常值
                if delta < -5 or delta > 30:
                    continue
                
                rows.append({
                    'year': stint.year,
                    'circuit': stint.circuit,
                    'team': stint.team,
                    'driver': stint.driver,
                    'compound': stint.compound,
                    'stint_number': stint.stint_number,
                    'lap_number': lap['lap_number'],
                    'stint_lap': lap['stint_lap'],
                    'tyre_age': lap['tyre_age'],
                    'fuel_consumed': lap['fuel_consumed'],
                    'base_time': stint.base_time,
                    'lap_time': lap['lap_time'],
                    'delta': delta  # 目標變量
                })
        
        self.training_data = pd.DataFrame(rows)
        logger.info(f"訓練數據: {len(self.training_data)} 筆")
        
        # 異常值過濾（IQR 方法）
        self._filter_outliers()
    
    def _filter_outliers(self):
        """使用 IQR 過濾異常值"""
        original_count = len(self.training_data)
        
        # 按 circuit + compound 分組過濾
        filtered_dfs = []
        
        for (circuit, compound), group in self.training_data.groupby(['circuit', 'compound']):
            if len(group) < 10:
                continue
            
            Q1 = group['delta'].quantile(0.25)
            Q3 = group['delta'].quantile(0.75)
            IQR = Q3 - Q1
            
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            
            filtered = group[(group['delta'] >= lower) & (group['delta'] <= upper)]
            filtered_dfs.append(filtered)
        
        if filtered_dfs:
            self.training_data = pd.concat(filtered_dfs, ignore_index=True)
        
        removed = original_count - len(self.training_data)
        logger.info(f"異常值過濾: 移除 {removed} 筆 ({removed/original_count*100:.1f}%)")
    
    def train_models(self, min_samples: int = 50):
        """訓練 XGBoost 模型"""
        logger.info("開始訓練 XGBoost 模型...")
        
        # 按 circuit + compound 分組訓練
        for (circuit, compound), group in self.training_data.groupby(['circuit', 'compound']):
            if len(group) < min_samples:
                continue
            
            result = self._train_single_model(circuit, compound, group)
            
            if result:
                self.results.append(result)
                
                if circuit not in self.models:
                    self.models[circuit] = {}
                # 模型儲存在 result 中的 feature_importance 裡
        
        logger.info(f"訓練完成: {len(self.results)} 組模型")
    
    def _train_single_model(self, circuit: str, compound: str, 
                            data: pd.DataFrame) -> Optional[TrainingResult]:
        """訓練單個模型"""
        try:
            # 特徵工程
            X = data[['tyre_age', 'fuel_consumed', 'stint_lap', 'lap_number']].copy()
            
            # 添加非線性特徵
            X['tyre_age_sq'] = X['tyre_age'] ** 2
            X['tyre_age_sqrt'] = np.sqrt(X['tyre_age'])
            X['stint_lap_sq'] = X['stint_lap'] ** 2
            
            y = data['delta'].values
            
            # XGBoost 參數（防止過擬合）
            params = {
                'n_estimators': 100,
                'max_depth': 4,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
                'random_state': 42,
                'verbosity': 0
            }
            
            model = xgb.XGBRegressor(**params)
            
            # 5-fold 交叉驗證
            kfold = KFold(n_splits=5, shuffle=True, random_state=42)
            cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_absolute_error')
            cv_mae = -cv_scores.mean()
            
            # 全數據訓練
            model.fit(X, y)
            y_pred = model.predict(X)
            
            mae = mean_absolute_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            
            # 提取等效線性係數（用於與 Baseline 相容）
            # 使用模型在 tyre_age=1-20 的預測來擬合線性
            base_rate, acceleration = self._extract_linear_coefficients(model, X.columns)
            
            # 燃油效果（從 fuel_consumed 的影響估計）
            fuel_effect = self._estimate_fuel_effect(model, X.columns)
            
            # 特徵重要性
            importance = dict(zip(X.columns, model.feature_importances_))
            
            return TrainingResult(
                circuit=circuit,
                compound=compound,
                base_rate=round(max(0.02, min(0.15, base_rate)), 5),
                acceleration=round(max(0.0005, min(0.01, acceleration)), 6),
                fuel_effect=round(max(-0.05, min(-0.01, fuel_effect)), 5),
                r2_score=round(r2, 4),
                mae=round(mae, 4),
                cv_mae=round(cv_mae, 4),
                sample_count=len(data),
                feature_importance=importance
            )
            
        except Exception as e:
            logger.warning(f"  訓練失敗 {circuit}/{compound}: {e}")
            return None
    
    def _extract_linear_coefficients(self, model: xgb.XGBRegressor, 
                                      feature_names: pd.Index) -> Tuple[float, float]:
        """從 XGBoost 模型提取等效線性係數"""
        # 創建模擬數據：tyre_age 從 1 到 20
        ages = np.arange(1, 21)
        
        # 固定其他特徵
        X_sim = pd.DataFrame({
            'tyre_age': ages,
            'fuel_consumed': 30.0,  # 假設中間圈
            'stint_lap': ages,
            'lap_number': 20 + ages,
            'tyre_age_sq': ages ** 2,
            'tyre_age_sqrt': np.sqrt(ages),
            'stint_lap_sq': ages ** 2
        })
        
        # 預測
        y_sim = model.predict(X_sim)
        
        # 擬合二次函數: y = a + b*x + c*x^2
        # 這裡 b = base_rate, c = 0.5 * acceleration
        from numpy.polynomial import polynomial as P
        coeffs = np.polyfit(ages, y_sim, 2)
        
        acceleration = coeffs[0] * 2  # 二次項係數
        base_rate = coeffs[1]  # 一次項係數
        
        return base_rate, acceleration
    
    def _estimate_fuel_effect(self, model: xgb.XGBRegressor, 
                               feature_names: pd.Index) -> float:
        """估計燃油效果"""
        # 固定其他特徵，變化 fuel_consumed
        fuels = np.array([10, 30, 50, 70, 90])
        
        X_sim = pd.DataFrame({
            'tyre_age': 10,
            'fuel_consumed': fuels,
            'stint_lap': 10,
            'lap_number': 30,
            'tyre_age_sq': 100,
            'tyre_age_sqrt': np.sqrt(10),
            'stint_lap_sq': 100
        })
        
        y_sim = model.predict(X_sim)
        
        # 線性擬合
        slope, _ = np.polyfit(fuels, y_sim, 1)
        
        # 燃油消耗應該讓車變輕變快，所以效果應該是負的
        return -abs(slope) if slope > 0 else slope
    
    def evaluate_on_2025(self, races: List[str] = None) -> Dict[str, Any]:
        """在 2025 年數據上評估"""
        if races is None:
            races = RACES_2025
        
        logger.info(f"評估 2025 年 {len(races)} 場比賽...")
        
        results = {
            'total_laps': 0,
            'total_mae': 0,
            'races': {}
        }
        
        all_errors = []
        
        for race in races:
            stints = self.load_race_stints(2025, race)
            
            if not stints:
                continue
            
            race_errors = []
            circuit = COEFF_CIRCUIT_MAPPING.get(race, race.replace(' ', '_') + '_Grand_Prix')
            
            for stint in stints:
                if stint.base_time <= 0:
                    continue
                
                # 獲取該 circuit + compound 的訓練結果
                result = self._get_result(circuit, stint.compound)
                
                if result is None:
                    # Fallback to baseline
                    coeffs = BASELINE_COEFFICIENTS.get(stint.compound, BASELINE_COEFFICIENTS['MEDIUM'])
                    base_rate = coeffs['base_rate']
                    acceleration = coeffs['acceleration']
                    fuel_effect = DEFAULT_FUEL_EFFECT
                else:
                    base_rate = result.base_rate
                    acceleration = result.acceleration
                    fuel_effect = result.fuel_effect
                
                for lap in stint.laps:
                    # 預測 delta
                    tyre_age = lap['tyre_age']
                    fuel_consumed = lap['fuel_consumed']
                    
                    pred_delta = (
                        base_rate * tyre_age +
                        0.5 * acceleration * (tyre_age ** 2) +
                        fuel_effect * fuel_consumed
                    )
                    
                    pred_time = stint.base_time + pred_delta
                    actual_time = lap['lap_time']
                    
                    error = abs(actual_time - pred_time)
                    race_errors.append(error)
                    all_errors.append(error)
            
            if race_errors:
                race_mae = np.mean(race_errors)
                results['races'][race] = {
                    'mae': round(race_mae, 3),
                    'laps': len(race_errors)
                }
                logger.info(f"  {race}: MAE={race_mae:.3f}s ({len(race_errors)} laps)")
        
        if all_errors:
            results['total_mae'] = round(np.mean(all_errors), 4)
            results['total_laps'] = len(all_errors)
        
        return results
    
    def _get_result(self, circuit: str, compound: str) -> Optional[TrainingResult]:
        """獲取訓練結果"""
        for r in self.results:
            if r.circuit == circuit and r.compound == compound:
                return r
        return None
    
    def save_coefficients(self, output_path: str):
        """保存係數到 JSON"""
        output = {
            'version': '2.0-xgboost',
            'description': 'XGBoost 訓練的策略係數 (Circuit + Compound)',
            'training_info': {
                'model': 'XGBoost',
                'total_stints': len(self.all_stints),
                'total_samples': len(self.training_data) if self.training_data is not None else 0,
                'total_coefficients': len(self.results)
            },
            'circuits': {}
        }
        
        for result in self.results:
            if result.circuit not in output['circuits']:
                output['circuits'][result.circuit] = {
                    'compounds': {}
                }
            
            output['circuits'][result.circuit]['compounds'][result.compound] = {
                'base_rate': result.base_rate,
                'acceleration': result.acceleration,
                'fuel_effect': result.fuel_effect,
                'r2_score': result.r2_score,
                'mae': result.mae,
                'cv_mae': result.cv_mae,
                'sample_count': result.sample_count
            }
        
        # 確保目錄存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"係數已保存: {output_path}")


# ============================================================================
# 主程式
# ============================================================================

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='F1 策略係數 XGBoost 訓練器 V2')
    parser.add_argument('--train-years', nargs='+', type=int, default=[2023, 2024],
                        help='訓練年份')
    parser.add_argument('--test-year', type=int, default=2025,
                        help='測試年份')
    parser.add_argument('--output', type=str, 
                        default='config/strategy_coefficients_xgboost.json',
                        help='輸出檔案路徑')
    parser.add_argument('--cache-dir', type=str, default='f1_analysis_cache',
                        help='FastF1 緩存目錄')
    parser.add_argument('--min-samples', type=int, default=50,
                        help='最小樣本數')
    
    args = parser.parse_args()
    
    trainer = XGBoostStrategyTrainer(cache_dir=args.cache_dir)
    
    # 1. 收集訓練數據
    trainer.collect_training_data(args.train_years)
    
    # 2. 訓練模型
    trainer.train_models(min_samples=args.min_samples)
    
    # 3. 評估
    eval_results = trainer.evaluate_on_2025()
    
    # 4. 保存結果
    trainer.save_coefficients(args.output)
    
    print("\n" + "="*60)
    print("XGBoost 訓練完成!")
    print(f"  訓練樣本: {len(trainer.training_data)} 筆")
    print(f"  訓練係數: {len(trainer.results)} 組")
    print(f"  2025 評估 MAE: {eval_results['total_mae']:.4f}s")
    print("="*60)
    
    # 顯示各賽道結果
    print("\n2025 各賽道 MAE:")
    for race, data in sorted(eval_results['races'].items(), key=lambda x: x[1]['mae']):
        print(f"  {race:20}: {data['mae']:.3f}s ({data['laps']} laps)")


if __name__ == '__main__':
    main()
