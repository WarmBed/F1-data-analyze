#!/usr/bin/env python3
"""
F87 - Driver Strategy Predictor (車手策略預測器)

功能:
    根據車手的 Tire Saving 行為模式，個人化調整進站圈數預測
    
核心邏輯:
    個人化進站圈數 = 大數據預估圈數 × (1 + Tire Saving Adjustment Factor)
    
補償係數對照表:
    - NONE (0-20):     +0%      維持原始預估
    - LIGHT (20-40):   +5~10%   略延長 stint
    - MODERATE (40-65): +10~20% 中度延長
    - HEAVY (65-100):  +20~35%  大幅延長
    
數據來源:
    - F86 Tire Saving Analysis (json/tire_saving_analysis_*.json)
    - Tire Degradation Database (config/tire_degradation_database.json)
    
輸出:
    - 每車手個人化進站預測
    - 預測 vs 實際比較
    - 準確度統計報告

版本: 1.0.0
作者: F1T Team
日期: 2025-12-05
"""

import os
import json
import glob
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict
import numpy as np


# ============================================================================
# 數據結構定義
# ============================================================================

@dataclass
class StintPrediction:
    """單一 Stint 預測結果"""
    driver_code: str
    stint_number: int
    compound: str
    
    # 預測相關
    base_optimal_laps: int          # 大數據預估 (來自 tire_degradation_database)
    tire_saving_score: float        # F86 分數
    tire_saving_level: str          # NONE/LIGHT/MODERATE/HEAVY
    adjustment_factor: float        # 補償係數
    predicted_laps: int             # 個人化預測圈數
    
    # 實際結果
    actual_laps: int                # 實際圈數
    
    # 驗證
    prediction_error: int           # 預測誤差 (圈)
    is_accurate: bool               # 誤差 <= 3 圈視為準確
    is_direction_correct: bool      # 方向正確 (有 saving → 實際晚換)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DriverPredictionSummary:
    """車手預測摘要"""
    driver_code: str
    team: str
    total_stints: int
    avg_tire_saving_score: float
    avg_adjustment_factor: float
    total_prediction_error: int
    accurate_predictions: int
    accuracy_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    """驗證報告"""
    race_name: str
    year: int
    session: str
    total_stints: int
    
    # 整體指標
    overall_accuracy: float         # 誤差 <= 3 圈的比例
    mean_absolute_error: float      # 平均絕對誤差
    rmse: float                     # 均方根誤差
    direction_accuracy: float       # 方向正確率
    
    # 對比: 有/無補償
    baseline_mae: float             # 無補償時的 MAE
    adjusted_mae: float             # 有補償時的 MAE
    improvement: float              # 改善百分比
    
    # 分類詳情
    by_compound: Dict[str, Dict]
    by_saving_level: Dict[str, Dict]
    
    # 車手詳情
    driver_summaries: List[DriverPredictionSummary]
    stint_predictions: List[StintPrediction]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["driver_summaries"] = [d.to_dict() for d in self.driver_summaries]
        result["stint_predictions"] = [s.to_dict() for s in self.stint_predictions]
        return result


# ============================================================================
# 補償係數計算
# ============================================================================

class TireSavingAdjustmentCalculator:
    """Tire Saving 補償係數計算器"""
    
    # 補償係數對照表 (可調整)
    ADJUSTMENT_TABLE = {
        "NONE": (0.0, 0.0),         # 0-20: +0%
        "LIGHT": (0.05, 0.10),       # 20-40: +5~10%
        "MODERATE": (0.10, 0.20),    # 40-65: +10~20%
        "HEAVY": (0.20, 0.35),       # 65-100: +20~35%
    }
    
    # 分數閾值
    THRESHOLDS = {
        "NONE": (0, 20),
        "LIGHT": (20, 40),
        "MODERATE": (40, 65),
        "HEAVY": (65, 100),
    }
    
    @classmethod
    def get_saving_level(cls, score: float) -> str:
        """根據分數取得省胎等級"""
        if score < 20:
            return "NONE"
        elif score < 40:
            return "LIGHT"
        elif score < 65:
            return "MODERATE"
        else:
            return "HEAVY"
    
    @classmethod
    def calculate_adjustment_factor(cls, score: float) -> float:
        """
        根據 F86 分數計算補償係數
        
        使用線性插值在等級範圍內計算精確係數
        """
        level = cls.get_saving_level(score)
        min_adj, max_adj = cls.ADJUSTMENT_TABLE[level]
        min_score, max_score = cls.THRESHOLDS[level]
        
        if min_score == max_score:
            return min_adj
        
        # 線性插值
        ratio = (score - min_score) / (max_score - min_score)
        adjustment = min_adj + ratio * (max_adj - min_adj)
        
        return round(adjustment, 4)
    
    @classmethod
    def predict_stint_length(cls, base_optimal: int, score: float) -> int:
        """
        計算個人化 stint 長度預測
        
        Args:
            base_optimal: 大數據預估的最佳 stint 長度
            score: F86 Tire Saving 分數
            
        Returns:
            個人化預測圈數
        """
        adjustment = cls.calculate_adjustment_factor(score)
        predicted = base_optimal * (1 + adjustment)
        return round(predicted)


# ============================================================================
# 主要預測器
# ============================================================================

class DriverStrategyPredictor:
    """F87 - 車手策略預測器"""
    
    def __init__(self, base_path: str = None):
        """
        初始化預測器
        
        Args:
            base_path: 專案根目錄
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
        self.base_path = Path(base_path)
        
        self.json_dir = self.base_path / "json"
        self.config_dir = self.base_path / "config"
        
        # 載入輪胎衰退資料庫
        self.tire_db = self._load_tire_database()
        
        # 補償計算器
        self.calculator = TireSavingAdjustmentCalculator()
    
    def _load_tire_database(self) -> Dict[str, Any]:
        """載入輪胎衰退資料庫"""
        db_path = self.config_dir / "tire_degradation_database.json"
        if db_path.exists():
            with open(db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    # 賽事名稱到賽道名稱的映射
    RACE_TO_CIRCUIT = {
        "Japan": "Suzuka",
        "Australia": "Melbourne",
        "China": "Shanghai",
        "Saudi Arabia": "Jeddah",
        "United States": "Austin",
        "USA": "Austin",
        "Abu Dhabi": "Yas_Marina",
        "Great Britain": "Silverstone",
        "UK": "Silverstone",
        "Italy": "Monza",
        "Belgium": "Spa",
        "Netherlands": "Zandvoort",
        "Azerbaijan": "Baku",
        "Las Vegas": "Las_Vegas",
        "Singapore": "Singapore",
        "Mexico": "Mexico_City",
        "Brazil": "Interlagos",
        "Qatar": "Qatar",
        "Bahrain": "Bahrain",
        "Monaco": "Monaco",
        "Canada": "Montreal",
        "Austria": "Spielberg",
        "Hungary": "Budapest",
        "Spain": "Barcelona",
        "Miami": "Miami",
        "Emilia Romagna": "Imola",
    }
    
    def _get_optimal_stint_length(self, circuit: str, compound: str) -> int:
        """取得特定賽道/胎種的最佳 stint 長度"""
        circuits = self.tire_db.get("circuits", {})
        
        # 先嘗試映射表
        mapped_circuit = self.RACE_TO_CIRCUIT.get(circuit, circuit)
        
        # 嘗試直接匹配
        circuit_data = circuits.get(mapped_circuit, {})
        
        # 如果沒找到，嘗試原始名稱
        if not circuit_data:
            circuit_data = circuits.get(circuit, {})
        
        # 如果還是沒找到，嘗試部分匹配
        if not circuit_data:
            for name, data in circuits.items():
                if circuit.lower() in name.lower() or name.lower() in circuit.lower():
                    circuit_data = data
                    break
        
        optimal = circuit_data.get("optimal_stint_length", {})
        return optimal.get(compound.upper(), 20)  # 預設 20 圈
    
    def _load_f86_analysis(self, year: int, race: str, session: str) -> Optional[Dict]:
        """載入 F86 分析結果"""
        pattern = f"tire_saving_analysis_{year}_{race}_{session}.json"
        file_path = self.json_dir / pattern
        
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # 嘗試搜尋
        search_pattern = str(self.json_dir / f"tire_saving_analysis_{year}_{race}*.json")
        files = glob.glob(search_pattern)
        if files:
            with open(files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        
        return None
    
    def predict(self, year: int, race: str, session: str = "R") -> ValidationReport:
        """
        執行預測並產生驗證報告
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型 (預設 R)
            
        Returns:
            ValidationReport 驗證報告
        """
        # 載入 F86 分析結果
        f86_data = self._load_f86_analysis(year, race, session)
        if not f86_data:
            raise FileNotFoundError(f"找不到 F86 分析結果: {year} {race} {session}")
        
        drivers = f86_data.get("data", {}).get("drivers", [])
        if not drivers:
            raise ValueError("F86 分析結果中沒有車手數據")
        
        # 收集所有 stint 預測
        stint_predictions: List[StintPrediction] = []
        driver_summaries: List[DriverPredictionSummary] = []
        
        for driver in drivers:
            driver_code = driver.get("driver_code")
            team = driver.get("team", "Unknown")
            stints = driver.get("stints", [])
            
            driver_errors = []
            driver_accurate = 0
            driver_scores = []
            driver_adjustments = []
            
            for stint in stints:
                stint_num = stint.get("stint_number")
                compound = stint.get("compound", "MEDIUM").upper()
                actual_laps = stint.get("total_laps", 0)
                
                saving = stint.get("saving_analysis", {})
                score = saving.get("overall_score", 0)
                level = saving.get("saving_level", "NONE")
                
                # 取得大數據預估
                base_optimal = self._get_optimal_stint_length(race, compound)
                
                # 計算補償係數
                adjustment = self.calculator.calculate_adjustment_factor(score)
                
                # 計算個人化預測
                predicted = self.calculator.predict_stint_length(base_optimal, score)
                
                # 計算誤差
                error = abs(predicted - actual_laps)
                is_accurate = error <= 3
                
                # 方向正確: 有 saving → 實際晚換 (actual > base)
                has_saving = level in ["LIGHT", "MODERATE", "HEAVY"]
                actually_late = actual_laps > base_optimal
                direction_correct = (has_saving and actually_late) or (not has_saving and not actually_late)
                
                prediction = StintPrediction(
                    driver_code=driver_code,
                    stint_number=stint_num,
                    compound=compound,
                    base_optimal_laps=base_optimal,
                    tire_saving_score=score,
                    tire_saving_level=level,
                    adjustment_factor=adjustment,
                    predicted_laps=predicted,
                    actual_laps=actual_laps,
                    prediction_error=error,
                    is_accurate=is_accurate,
                    is_direction_correct=direction_correct
                )
                
                stint_predictions.append(prediction)
                driver_errors.append(error)
                if is_accurate:
                    driver_accurate += 1
                driver_scores.append(score)
                driver_adjustments.append(adjustment)
            
            # 車手摘要
            if stints:
                summary = DriverPredictionSummary(
                    driver_code=driver_code,
                    team=team,
                    total_stints=len(stints),
                    avg_tire_saving_score=np.mean(driver_scores) if driver_scores else 0,
                    avg_adjustment_factor=np.mean(driver_adjustments) if driver_adjustments else 0,
                    total_prediction_error=sum(driver_errors),
                    accurate_predictions=driver_accurate,
                    accuracy_rate=driver_accurate / len(stints) * 100 if stints else 0
                )
                driver_summaries.append(summary)
        
        # 計算整體指標
        errors = [p.prediction_error for p in stint_predictions]
        baseline_errors = [abs(p.base_optimal_laps - p.actual_laps) for p in stint_predictions]
        
        overall_accuracy = sum(1 for p in stint_predictions if p.is_accurate) / len(stint_predictions) * 100
        direction_accuracy = sum(1 for p in stint_predictions if p.is_direction_correct) / len(stint_predictions) * 100
        mae = np.mean(errors) if errors else 0
        rmse = np.sqrt(np.mean([e**2 for e in errors])) if errors else 0
        baseline_mae = np.mean(baseline_errors) if baseline_errors else 0
        
        improvement = (baseline_mae - mae) / baseline_mae * 100 if baseline_mae > 0 else 0
        
        # 按胎種分類
        by_compound = {}
        compounds = set(p.compound for p in stint_predictions)
        for compound in compounds:
            c_preds = [p for p in stint_predictions if p.compound == compound]
            c_errors = [p.prediction_error for p in c_preds]
            c_baseline = [abs(p.base_optimal_laps - p.actual_laps) for p in c_preds]
            by_compound[compound] = {
                "count": len(c_preds),
                "mae": np.mean(c_errors) if c_errors else 0,
                "baseline_mae": np.mean(c_baseline) if c_baseline else 0,
                "accuracy": sum(1 for p in c_preds if p.is_accurate) / len(c_preds) * 100 if c_preds else 0
            }
        
        # 按省胎等級分類
        by_saving_level = {}
        levels = ["NONE", "LIGHT", "MODERATE", "HEAVY"]
        for level in levels:
            l_preds = [p for p in stint_predictions if p.tire_saving_level == level]
            if l_preds:
                l_errors = [p.prediction_error for p in l_preds]
                l_baseline = [abs(p.base_optimal_laps - p.actual_laps) for p in l_preds]
                by_saving_level[level] = {
                    "count": len(l_preds),
                    "mae": np.mean(l_errors) if l_errors else 0,
                    "baseline_mae": np.mean(l_baseline) if l_baseline else 0,
                    "accuracy": sum(1 for p in l_preds if p.is_accurate) / len(l_preds) * 100 if l_preds else 0
                }
        
        # 建立報告
        report = ValidationReport(
            race_name=race,
            year=year,
            session=session,
            total_stints=len(stint_predictions),
            overall_accuracy=round(overall_accuracy, 2),
            mean_absolute_error=round(mae, 2),
            rmse=round(rmse, 2),
            direction_accuracy=round(direction_accuracy, 2),
            baseline_mae=round(baseline_mae, 2),
            adjusted_mae=round(mae, 2),
            improvement=round(improvement, 2),
            by_compound=by_compound,
            by_saving_level=by_saving_level,
            driver_summaries=driver_summaries,
            stint_predictions=stint_predictions
        )
        
        return report
    
    def save_report(self, report: ValidationReport, output_path: str = None) -> str:
        """
        儲存驗證報告
        
        Args:
            report: 驗證報告
            output_path: 輸出路徑 (可選)
            
        Returns:
            儲存的檔案路徑
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"driver_strategy_prediction_{report.year}_{report.race_name}_{report.session}.json"
            output_path = self.json_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        # 同時儲存帶時間戳的版本
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_path = str(output_path).replace(".json", f"_{timestamp}.json")
        with open(timestamped_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def print_report(self, report: ValidationReport):
        """印出報告摘要"""
        print()
        print("=" * 80)
        print(f"F87 Driver Strategy Prediction Report - {report.year} {report.race_name} {report.session}")
        print("=" * 80)
        print()
        
        print("【整體指標】")
        print("-" * 40)
        print(f"  總 Stint 數:        {report.total_stints}")
        print(f"  整體準確率:         {report.overall_accuracy:.1f}%  (誤差 <= 3 圈)")
        print(f"  方向正確率:         {report.direction_accuracy:.1f}%")
        print()
        print(f"  有補償 MAE:         {report.adjusted_mae:.2f} 圈")
        print(f"  無補償 MAE:         {report.baseline_mae:.2f} 圈")
        print(f"  改善幅度:           {report.improvement:.1f}%")
        print(f"  RMSE:               {report.rmse:.2f} 圈")
        print()
        
        print("【按輪胎分類】")
        print("-" * 60)
        print(f"{'Compound':<10} {'Count':<8} {'有補償 MAE':<12} {'無補償 MAE':<12} {'準確率':<10}")
        print("-" * 60)
        for compound, stats in sorted(report.by_compound.items()):
            print(f"{compound:<10} {stats['count']:<8} {stats['mae']:.2f} 圈      "
                  f"{stats['baseline_mae']:.2f} 圈      {stats['accuracy']:.1f}%")
        print()
        
        print("【按省胎等級分類】")
        print("-" * 60)
        print(f"{'Level':<12} {'Count':<8} {'有補償 MAE':<12} {'無補償 MAE':<12} {'準確率':<10}")
        print("-" * 60)
        for level in ["NONE", "LIGHT", "MODERATE", "HEAVY"]:
            if level in report.by_saving_level:
                stats = report.by_saving_level[level]
                print(f"{level:<12} {stats['count']:<8} {stats['mae']:.2f} 圈      "
                      f"{stats['baseline_mae']:.2f} 圈      {stats['accuracy']:.1f}%")
        print()
        
        print("【車手摘要 (按準確率排序)】")
        print("-" * 80)
        print(f"{'Driver':<8} {'Team':<20} {'Stints':<8} {'Avg Score':<12} {'Adj Factor':<12} {'準確率':<10}")
        print("-" * 80)
        sorted_drivers = sorted(report.driver_summaries, key=lambda x: -x.accuracy_rate)
        for d in sorted_drivers[:10]:  # 顯示前 10
            print(f"{d.driver_code:<8} {d.team[:18]:<20} {d.total_stints:<8} "
                  f"{d.avg_tire_saving_score:.1f}        {d.avg_adjustment_factor:.2%}       "
                  f"{d.accuracy_rate:.1f}%")
        print()
        
        print("【詳細預測 (前 15 筆)】")
        print("-" * 100)
        print(f"{'Driver':<6} {'Stint':<6} {'Compound':<8} {'Score':<7} {'Level':<10} "
              f"{'Base':<6} {'Adj':<8} {'Pred':<6} {'Actual':<8} {'Error':<6} {'Result':<8}")
        print("-" * 100)
        for p in report.stint_predictions[:15]:
            result = "✓" if p.is_accurate else "✗"
            print(f"{p.driver_code:<6} {p.stint_number:<6} {p.compound:<8} "
                  f"{p.tire_saving_score:<7.1f} {p.tire_saving_level:<10} "
                  f"{p.base_optimal_laps:<6} {p.adjustment_factor:<8.2%} "
                  f"{p.predicted_laps:<6} {p.actual_laps:<8} {p.prediction_error:<6} {result:<8}")
        print()
        print("=" * 80)


# ============================================================================
# 模組入口函數
# ============================================================================

def run_driver_strategy_prediction(
    year: int,
    race: str,
    session: str = "R",
    base_path: str = None,
    save_output: bool = True,
    print_report: bool = True
) -> Dict[str, Any]:
    """
    執行 F87 車手策略預測
    
    Args:
        year: 年份
        race: 賽事名稱
        session: 會話類型
        base_path: 專案根目錄
        save_output: 是否儲存輸出
        print_report: 是否印出報告
        
    Returns:
        預測報告字典
    """
    predictor = DriverStrategyPredictor(base_path)
    report = predictor.predict(year, race, session)
    
    if print_report:
        predictor.print_report(report)
    
    output_path = None
    if save_output:
        output_path = predictor.save_report(report)
        print(f"\n報告已儲存至: {output_path}")
    
    return {
        "success": True,
        "message": f"F87 預測完成，共 {report.total_stints} 個 stint",
        "function_id": "87",
        "data": report.to_dict(),
        "output_path": output_path
    }


# ============================================================================
# 直接執行測試
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # 預設測試 Japan 2025
    year = 2025
    race = "Japan"
    session = "R"
    
    if len(sys.argv) > 1:
        race = sys.argv[1]
    if len(sys.argv) > 2:
        year = int(sys.argv[2])
    
    result = run_driver_strategy_prediction(year, race, session)
    print(f"\n成功: {result['success']}")
