#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 策略預測準確度評估器

功能：
1. 對 2025 年 24 場比賽進行回測
2. 比較現有系統 vs Phase 1 訓練後的準確度
3. 計算 MAE、每圈誤差、進站預測準確度
4. 生成 Markdown 報告和趨勢圖

目標車手：VER, NOR, LEC

使用方式：
  python evaluate_strategy_accuracy.py --mode baseline
  python evaluate_strategy_accuracy.py --mode phase1
  python evaluate_strategy_accuracy.py --mode compare

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
from datetime import datetime

import numpy as np

# FastF1
try:
    import fastf1
    from fastf1 import Cache
    import pandas as pd
except ImportError:
    print("錯誤：請安裝 fastf1 和 pandas")
    sys.exit(1)

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

# 映射到係數檔案中的賽道名稱 (Phase 1)
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

# 現有系統的預設係數
DEFAULT_COEFFICIENTS = {
    'SOFT': {'base_rate': 0.08, 'acceleration': 0.003},
    'MEDIUM': {'base_rate': 0.05, 'acceleration': 0.002},
    'HARD': {'base_rate': 0.03, 'acceleration': 0.001}
}
DEFAULT_FUEL_EFFECT = -0.03  # s/kg
FUEL_KG_PER_LAP = 1.8


# ============================================================================
# 數據結構
# ============================================================================

@dataclass
class LapPrediction:
    """單圈預測結果"""
    lap_number: int
    actual_time: float
    predicted_time: float
    error: float  # actual - predicted
    compound: str
    tyre_age: int
    stint: int


@dataclass
class StintInfo:
    """Stint 資訊"""
    stint_number: int
    start_lap: int
    end_lap: int
    compound: str
    predicted_pit_lap: int = 0
    actual_pit_lap: int = 0


@dataclass
class DriverRaceResult:
    """單場比賽車手結果"""
    driver: str
    race: str
    circuit: str
    lap_predictions: List[LapPrediction] = field(default_factory=list)
    stints: List[StintInfo] = field(default_factory=list)
    
    @property
    def mae(self) -> float:
        if not self.lap_predictions:
            return 0.0
        errors = [abs(lp.error) for lp in self.lap_predictions]
        return np.mean(errors)
    
    @property
    def error_distribution(self) -> Dict[str, float]:
        """誤差分佈統計"""
        if not self.lap_predictions:
            return {}
        errors = [abs(lp.error) for lp in self.lap_predictions]
        return {
            'within_0.5s': sum(1 for e in errors if e <= 0.5) / len(errors) * 100,
            'within_1.0s': sum(1 for e in errors if e <= 1.0) / len(errors) * 100,
            'within_2.0s': sum(1 for e in errors if e <= 2.0) / len(errors) * 100,
            'max_error': max(errors),
            'min_error': min(errors),
            'std': np.std(errors)
        }
    
    @property
    def pit_prediction_error(self) -> List[int]:
        """進站預測誤差（圈數）"""
        errors = []
        for stint in self.stints:
            if stint.predicted_pit_lap > 0 and stint.actual_pit_lap > 0:
                errors.append(abs(stint.predicted_pit_lap - stint.actual_pit_lap))
        return errors


# ============================================================================
# 評估器類
# ============================================================================

class StrategyAccuracyEvaluator:
    """策略準確度評估器"""
    
    def __init__(self, cache_dir: str = "f1_analysis_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        Cache.enable_cache(str(self.cache_dir))
        
        # 載入現有係數資料庫
        self.tire_deg_database = self._load_tire_database()
        self.team_coefficients = {}  # Phase 1 訓練後的係數
        
        # 結果儲存
        self.baseline_results: Dict[str, List[DriverRaceResult]] = {}
        self.phase1_results: Dict[str, List[DriverRaceResult]] = {}
        
    def _load_tire_database(self) -> Dict:
        """載入輪胎衰退資料庫"""
        db_path = Path(__file__).parent.parent.parent.parent / 'config' / 'tire_degradation_database.json'
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_team_coefficients(self) -> Dict:
        """載入 Phase 1 訓練後的車隊係數"""
        coeff_path = Path(__file__).parent.parent.parent.parent / 'config' / 'team_strategy_coefficients.json'
        if coeff_path.exists():
            with open(coeff_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _get_baseline_coefficients(self, circuit: str, compound: str) -> Dict:
        """獲取基準係數（現有系統）"""
        circuits = self.tire_deg_database.get('circuits', {})
        circuit_data = circuits.get(circuit, {})
        
        if circuit_data:
            base_deg = circuit_data.get('base_degradation', {})
            deg_accel = circuit_data.get('degradation_acceleration', {})
            
            return {
                'base_rate': base_deg.get(compound, DEFAULT_COEFFICIENTS[compound]['base_rate']),
                'acceleration': deg_accel.get(compound, DEFAULT_COEFFICIENTS[compound]['acceleration']),
                'fuel_effect': DEFAULT_FUEL_EFFECT
            }
        
        return {
            'base_rate': DEFAULT_COEFFICIENTS.get(compound, DEFAULT_COEFFICIENTS['MEDIUM'])['base_rate'],
            'acceleration': DEFAULT_COEFFICIENTS.get(compound, DEFAULT_COEFFICIENTS['MEDIUM'])['acceleration'],
            'fuel_effect': DEFAULT_FUEL_EFFECT
        }
    
    def _get_phase1_coefficients(self, team: str, race_name: str, compound: str) -> Optional[Dict]:
        """獲取 Phase 1 訓練後的係數
        
        Args:
            team: 車隊名稱 (如 "Red Bull Racing")
            race_name: 賽事名稱 (如 "Bahrain", "Saudi Arabia")
            compound: 輪胎配方 (如 "SOFT", "MEDIUM", "HARD")
        """
        if not self.team_coefficients:
            return None
        
        # 將賽事名稱轉換為係數檔案格式
        coeff_circuit = COEFF_CIRCUIT_MAPPING.get(race_name, race_name.replace(' ', '_') + '_Grand_Prix')
        
        teams = self.team_coefficients.get('teams', {})
        team_data = teams.get(team, {})
        circuits = team_data.get('circuits', {})
        circuit_data = circuits.get(coeff_circuit, {})
        compounds = circuit_data.get('compounds', {})
        compound_data = compounds.get(compound, {})
        
        if compound_data:
            return {
                'base_rate': compound_data.get('base_rate', 0.05),
                'acceleration': compound_data.get('acceleration', 0.002),
                'fuel_effect': circuit_data.get('fuel_effect_per_kg', DEFAULT_FUEL_EFFECT),
                'track_evo': circuit_data.get('track_evolution_baseline', 0)
            }
        return None
    
    def _predict_lap_time(self, base_time: float, tyre_age: int, lap_number: int,
                          coeffs: Dict) -> float:
        """預測單圈圈速"""
        base_rate = coeffs['base_rate']
        acceleration = coeffs['acceleration']
        fuel_effect = coeffs.get('fuel_effect', DEFAULT_FUEL_EFFECT)
        track_evo = coeffs.get('track_evo', 0)
        
        # 輪胎衰退
        tyre_deg = base_rate * tyre_age + 0.5 * acceleration * (tyre_age ** 2)
        
        # 燃油效果（消耗燃油 = 變輕 = 變快）
        fuel_consumed = FUEL_KG_PER_LAP * (lap_number - 1)
        fuel_delta = fuel_effect * fuel_consumed
        
        # 賽道進化
        track_delta = track_evo * lap_number
        
        predicted = base_time + tyre_deg + fuel_delta + track_delta
        return predicted
    
    def _predict_optimal_pit_lap(self, stint_start: int, compound: str, 
                                  coeffs: Dict, total_laps: int) -> int:
        """預測最佳進站圈（簡化版：輪胎衰退 > 閾值時進站）"""
        # 使用衰退率估計最佳 stint 長度
        base_rate = coeffs['base_rate']
        acceleration = coeffs['acceleration']
        
        # 閾值：當單圈衰退超過 1.5 秒時進站
        threshold = 1.5
        
        for age in range(1, 50):
            deg = base_rate * age + 0.5 * acceleration * (age ** 2)
            if deg > threshold:
                return min(stint_start + age, total_laps)
        
        return min(stint_start + 25, total_laps)  # 預設 25 圈
    
    def evaluate_race(self, year: int, race_name: str, mode: str = 'baseline') -> List[DriverRaceResult]:
        """評估單場比賽"""
        results = []
        circuit = CIRCUIT_MAPPING.get(race_name, race_name.replace(' ', '_'))
        
        try:
            logger.info(f"載入 {year} {race_name}...")
            session = fastf1.get_session(year, race_name, 'R')
            session.load()
            
            laps = session.laps
            total_laps = session.total_laps if hasattr(session, 'total_laps') else 58
            
            for driver in TARGET_DRIVERS:
                driver_laps = laps[laps['Driver'] == driver]
                
                if driver_laps.empty:
                    logger.warning(f"  {driver} 無數據")
                    continue
                
                # 獲取車隊
                team = driver_laps.iloc[0].get('Team', 'Unknown')
                
                result = DriverRaceResult(
                    driver=driver,
                    race=race_name,
                    circuit=circuit
                )
                
                # 計算基準圈速（最快圈）
                valid_times = [lt.total_seconds() for lt in driver_laps['LapTime'].dropna() 
                              if lt.total_seconds() > 60 and lt.total_seconds() < 180]
                base_time = min(valid_times) if valid_times else 90.0
                
                # 追蹤 Stint
                current_stint = 1
                stint_start_lap = 1
                last_compound = None
                stint_info = None
                
                for _, lap in driver_laps.iterrows():
                    lap_time = lap.get('LapTime')
                    if lap_time is None or pd.isna(lap_time):
                        continue
                    
                    actual_time = lap_time.total_seconds()
                    if actual_time < 60 or actual_time > 180:
                        continue
                    
                    lap_number = int(lap.get('LapNumber', 0))
                    compound = str(lap.get('Compound', 'UNKNOWN')).upper()
                    tyre_age = int(lap.get('TyreLife', 1)) if not pd.isna(lap.get('TyreLife')) else 1
                    
                    # 跳過非標準配方
                    if compound not in ['SOFT', 'MEDIUM', 'HARD']:
                        continue
                    
                    # 偵測換胎（新 Stint）
                    if last_compound and compound != last_compound:
                        if stint_info:
                            stint_info.end_lap = lap_number - 1
                            stint_info.actual_pit_lap = lap_number - 1
                            result.stints.append(stint_info)
                        
                        current_stint += 1
                        stint_start_lap = lap_number
                    
                    if last_compound is None or compound != last_compound:
                        # 獲取係數
                        if mode == 'baseline':
                            coeffs = self._get_baseline_coefficients(circuit, compound)
                        else:
                            coeffs = self._get_phase1_coefficients(team, race_name, compound)
                            if not coeffs:
                                coeffs = self._get_baseline_coefficients(circuit, compound)
                        
                        predicted_pit = self._predict_optimal_pit_lap(
                            stint_start_lap, compound, coeffs, total_laps
                        )
                        stint_info = StintInfo(
                            stint_number=current_stint,
                            start_lap=stint_start_lap,
                            end_lap=0,
                            compound=compound,
                            predicted_pit_lap=predicted_pit
                        )
                    
                    last_compound = compound
                    
                    # 獲取係數並預測
                    if mode == 'baseline':
                        coeffs = self._get_baseline_coefficients(circuit, compound)
                    else:
                        coeffs = self._get_phase1_coefficients(team, race_name, compound)
                        if not coeffs:
                            coeffs = self._get_baseline_coefficients(circuit, compound)
                    
                    predicted_time = self._predict_lap_time(
                        base_time, tyre_age, lap_number, coeffs
                    )
                    
                    error = actual_time - predicted_time
                    
                    lap_pred = LapPrediction(
                        lap_number=lap_number,
                        actual_time=actual_time,
                        predicted_time=predicted_time,
                        error=error,
                        compound=compound,
                        tyre_age=tyre_age,
                        stint=current_stint
                    )
                    result.lap_predictions.append(lap_pred)
                
                # 最後一個 stint
                if stint_info:
                    stint_info.end_lap = lap_number
                    result.stints.append(stint_info)
                
                results.append(result)
                logger.info(f"  {driver}: {len(result.lap_predictions)} laps, MAE={result.mae:.3f}s")
                
        except Exception as e:
            logger.error(f"  評估失敗: {e}")
        
        return results
    
    def evaluate_all_races(self, year: int = 2025, mode: str = 'baseline'):
        """評估所有比賽"""
        logger.info(f"開始評估 {year} 年所有比賽 (模式: {mode})")
        
        if mode == 'phase1':
            self.team_coefficients = self._load_team_coefficients()
            if not self.team_coefficients:
                logger.warning("Phase 1 係數未找到，將使用 baseline 模式")
                mode = 'baseline'
        
        all_results = {}
        
        for race in RACES_2025:
            try:
                results = self.evaluate_race(year, race, mode)
                all_results[race] = results
            except Exception as e:
                logger.error(f"{race} 處理失敗: {e}")
                continue
        
        if mode == 'baseline':
            self.baseline_results = all_results
        else:
            self.phase1_results = all_results
        
        return all_results
    
    def generate_markdown_report(self, output_path: str = None):
        """生成 Markdown 報告"""
        if output_path is None:
            output_path = f"docs/Strategy_Accuracy_Report_{datetime.now().strftime('%Y%m%d')}.md"
        
        lines = [
            "# F1 策略預測準確度報告",
            "",
            f"**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**評估年份**: 2025",
            f"**目標車手**: VER, NOR, LEC",
            "",
            "---",
            "",
            "## 總覽",
            "",
        ]
        
        # 計算總體統計
        if self.baseline_results:
            all_mae = []
            for race, results in self.baseline_results.items():
                for r in results:
                    all_mae.append(r.mae)
            
            avg_mae = np.mean(all_mae) if all_mae else 0
            lines.append(f"**現有系統平均 MAE**: {avg_mae:.3f}s")
        
        if self.phase1_results:
            all_mae = []
            for race, results in self.phase1_results.items():
                for r in results:
                    all_mae.append(r.mae)
            
            avg_mae = np.mean(all_mae) if all_mae else 0
            lines.append(f"**Phase 1 系統平均 MAE**: {avg_mae:.3f}s")
        
        lines.extend(["", "---", ""])
        
        # 每場比賽詳細報告
        for race in RACES_2025:
            lines.append(f"## {race}")
            lines.append("")
            
            baseline = self.baseline_results.get(race, [])
            phase1 = self.phase1_results.get(race, [])
            
            if baseline:
                lines.append("### 現有系統 (Baseline)")
                lines.append("")
                lines.append("| 車手 | MAE (s) | ±0.5s % | ±1.0s % | 最大誤差 | 進站誤差 (圈) |")
                lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|")
                
                for r in baseline:
                    dist = r.error_distribution
                    pit_err = np.mean(r.pit_prediction_error) if r.pit_prediction_error else 0
                    lines.append(
                        f"| {r.driver} | {r.mae:.3f} | {dist.get('within_0.5s', 0):.1f}% | "
                        f"{dist.get('within_1.0s', 0):.1f}% | {dist.get('max_error', 0):.2f}s | {pit_err:.1f} |"
                    )
                lines.append("")
                
                # 每圈誤差表
                lines.append("<details>")
                lines.append("<summary>每圈誤差詳情</summary>")
                lines.append("")
                lines.append("| 圈數 | VER 誤差 | NOR 誤差 | LEC 誤差 |")
                lines.append("|:---:|:---:|:---:|:---:|")
                
                # 整理數據
                lap_errors = {d: {} for d in TARGET_DRIVERS}
                max_lap = 0
                for r in baseline:
                    for lp in r.lap_predictions:
                        lap_errors[r.driver][lp.lap_number] = lp.error
                        max_lap = max(max_lap, lp.lap_number)
                
                for lap in range(1, max_lap + 1):
                    ver_err = lap_errors['VER'].get(lap, '-')
                    nor_err = lap_errors['NOR'].get(lap, '-')
                    lec_err = lap_errors['LEC'].get(lap, '-')
                    
                    ver_str = f"{ver_err:.2f}s" if isinstance(ver_err, float) else ver_err
                    nor_str = f"{nor_err:.2f}s" if isinstance(nor_err, float) else nor_err
                    lec_str = f"{lec_err:.2f}s" if isinstance(lec_err, float) else lec_err
                    
                    lines.append(f"| {lap} | {ver_str} | {nor_str} | {lec_str} |")
                
                lines.append("")
                lines.append("</details>")
                lines.append("")
            
            if phase1:
                lines.append("### Phase 1 系統")
                lines.append("")
                lines.append("| 車手 | MAE (s) | ±0.5s % | ±1.0s % | 最大誤差 | 進站誤差 (圈) |")
                lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|")
                
                for r in phase1:
                    dist = r.error_distribution
                    pit_err = np.mean(r.pit_prediction_error) if r.pit_prediction_error else 0
                    lines.append(
                        f"| {r.driver} | {r.mae:.3f} | {dist.get('within_0.5s', 0):.1f}% | "
                        f"{dist.get('within_1.0s', 0):.1f}% | {dist.get('max_error', 0):.2f}s | {pit_err:.1f} |"
                    )
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # 趨勢圖數據
        lines.append("## 趨勢圖數據")
        lines.append("")
        lines.append("```")
        lines.append("Race,Baseline_MAE,Phase1_MAE")
        
        for race in RACES_2025:
            baseline = self.baseline_results.get(race, [])
            phase1 = self.phase1_results.get(race, [])
            
            baseline_mae = np.mean([r.mae for r in baseline]) if baseline else 0
            phase1_mae = np.mean([r.mae for r in phase1]) if phase1 else 0
            
            lines.append(f"{race},{baseline_mae:.3f},{phase1_mae:.3f}")
        
        lines.append("```")
        
        # 寫入檔案
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"報告已生成: {output_path}")
        return str(output_path)
    
    def save_results_json(self, output_path: str = None):
        """儲存結果為 JSON"""
        if output_path is None:
            output_path = f"json/strategy_accuracy_results_{datetime.now().strftime('%Y%m%d')}.json"
        
        data = {
            'generated': datetime.now().isoformat(),
            'year': 2025,
            'drivers': TARGET_DRIVERS,
            'baseline': {},
            'phase1': {}
        }
        
        for race, results in self.baseline_results.items():
            data['baseline'][race] = []
            for r in results:
                data['baseline'][race].append({
                    'driver': r.driver,
                    'mae': r.mae,
                    'error_distribution': r.error_distribution,
                    'pit_prediction_errors': r.pit_prediction_error,
                    'lap_count': len(r.lap_predictions)
                })
        
        for race, results in self.phase1_results.items():
            data['phase1'][race] = []
            for r in results:
                data['phase1'][race].append({
                    'driver': r.driver,
                    'mae': r.mae,
                    'error_distribution': r.error_distribution,
                    'pit_prediction_errors': r.pit_prediction_error,
                    'lap_count': len(r.lap_predictions)
                })
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON 結果已儲存: {output_path}")
        return str(output_path)


def main():
    parser = argparse.ArgumentParser(description='F1 策略預測準確度評估器')
    parser.add_argument('--mode', choices=['baseline', 'phase1', 'compare', 'all'],
                        default='baseline', help='評估模式')
    parser.add_argument('--year', type=int, default=2025, help='評估年份')
    parser.add_argument('--output', type=str, help='輸出檔案路徑')
    
    args = parser.parse_args()
    
    evaluator = StrategyAccuracyEvaluator()
    
    if args.mode == 'baseline' or args.mode == 'all':
        logger.info("=== 評估 Baseline 系統 ===")
        evaluator.evaluate_all_races(args.year, 'baseline')
    
    if args.mode == 'phase1' or args.mode == 'all':
        logger.info("=== 評估 Phase 1 系統 ===")
        evaluator.evaluate_all_races(args.year, 'phase1')
    
    if args.mode == 'compare' or args.mode == 'all':
        logger.info("=== 生成比較報告 ===")
    
    # 生成報告
    report_path = evaluator.generate_markdown_report(args.output)
    json_path = evaluator.save_results_json()
    
    print("\n" + "="*60)
    print("評估完成!")
    print(f"  Markdown 報告: {report_path}")
    print(f"  JSON 結果: {json_path}")
    print("="*60)


if __name__ == '__main__':
    main()
