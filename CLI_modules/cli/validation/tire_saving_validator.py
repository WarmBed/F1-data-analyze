#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F86 Tire Saving Behavior Validator

驗證 F86 省輪胎行為分析的準確度：
- 使用 2023-2024 年數據作為訓練/驗證集
- 使用 2025 年數據作為測試集
- 計算 "比預期還晚換輪胎" 的預測成功率

驗證邏輯：
- 高省輪胎分數 (>= 40) 的車手，應該比預期 stint 長度更長
- 成功 = 實際 stint 長度 > optimal_stint_length

Author: F1T Team
Version: 1.0.0
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import os
import glob
import numpy as np


@dataclass
class StintValidationRecord:
    """單一 stint 驗證記錄"""
    year: int
    race: str
    session: str
    driver: str
    stint_number: int
    compound: str
    actual_stint_length: int
    expected_stint_length: int
    saving_score: float
    saving_level: str
    is_longer_than_expected: bool  # 實際 > 預期
    is_saving_predicted: bool      # 分數 >= 閾值表示預測會省
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RaceValidationResult:
    """單場比賽驗證結果"""
    year: int
    race: str
    session: str
    total_stints: int
    true_positives: int   # 預測省輪胎 + 實際更長
    false_positives: int  # 預測省輪胎 + 實際沒更長
    true_negatives: int   # 預測不省 + 實際沒更長
    false_negatives: int  # 預測不省 + 實際更長
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    stints: List[StintValidationRecord] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "year": self.year,
            "race": self.race,
            "session": self.session,
            "total_stints": self.total_stints,
            "metrics": {
                "true_positives": self.true_positives,
                "false_positives": self.false_positives,
                "true_negatives": self.true_negatives,
                "false_negatives": self.false_negatives,
                "accuracy": round(self.accuracy, 4),
                "precision": round(self.precision, 4),
                "recall": round(self.recall, 4),
                "f1_score": round(self.f1_score, 4)
            },
            "stints": [s.to_dict() for s in self.stints]
        }


@dataclass
class ValidationSummary:
    """驗證總結"""
    training_years: List[int]
    test_years: List[int]
    total_races: int
    total_stints: int
    overall_accuracy: float
    overall_precision: float
    overall_recall: float
    overall_f1: float
    saving_threshold: float
    by_compound: Dict[str, Dict[str, float]]
    best_threshold: float
    best_f1: float
    
    def to_dict(self) -> Dict:
        return {
            "training_years": self.training_years,
            "test_years": self.test_years,
            "total_races": self.total_races,
            "total_stints": self.total_stints,
            "overall_metrics": {
                "accuracy": round(self.overall_accuracy, 4),
                "precision": round(self.overall_precision, 4),
                "recall": round(self.overall_recall, 4),
                "f1_score": round(self.overall_f1, 4)
            },
            "saving_threshold": self.saving_threshold,
            "by_compound": self.by_compound,
            "optimal": {
                "best_threshold": self.best_threshold,
                "best_f1": round(self.best_f1, 4)
            }
        }


class TireSavingValidator:
    """
    F86 省輪胎行為驗證器
    
    驗證方法：
    1. 載入 F86 分析結果（省輪胎分數）
    2. 載入輪胎衰退資料庫（預期 stint 長度）
    3. 比較：高分車手是否實際 stint > 預期
    """
    
    def __init__(self, base_path: str = None):
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(__file__).resolve().parents[3]
        
        self.json_path = self.base_path / "json"
        self.config_path = self.base_path / "config"
        self.validation_output_path = self.base_path / "data" / "validation"
        self.validation_output_path.mkdir(parents=True, exist_ok=True)
        
        # 載入輪胎衰退資料庫
        self.tire_database = self._load_tire_database()
        
        # 賽事名稱對應賽道
        self.race_to_circuit = {
            "Bahrain": "Bahrain", "Saudi Arabia": "Jeddah", "Australia": "Melbourne",
            "Japan": "Suzuka", "China": "Shanghai", "Miami": "Miami",
            "Emilia Romagna": "Imola", "Monaco": "Monaco", "Canada": "Montreal",
            "Spain": "Barcelona", "Austria": "Spielberg", "Great Britain": "Silverstone",
            "Hungary": "Budapest", "Belgium": "Spa", "Netherlands": "Zandvoort",
            "Italy": "Monza", "Azerbaijan": "Baku", "Singapore": "Singapore",
            "USA": "Austin", "Mexico": "Mexico", "Brazil": "Interlagos",
            "Las Vegas": "Las_Vegas", "Qatar": "Lusail", "Abu Dhabi": "Yas_Marina"
        }
        
        # 預設省輪胎閾值
        self.saving_threshold = 40  # 分數 >= 40 視為 "省輪胎"
        
        # 驗證記錄
        self.validation_records: List[StintValidationRecord] = []
        self.race_results: List[RaceValidationResult] = []
    
    def _load_tire_database(self) -> Dict[str, Any]:
        """載入輪胎衰退係數資料庫"""
        db_path = self.config_path / "tire_degradation_database.json"
        try:
            if db_path.exists():
                with open(db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"[WARNING] 找不到輪胎衰退資料庫: {db_path}")
                return {"circuits": {}}
        except Exception as e:
            print(f"[ERROR] 載入輪胎衰退資料庫失敗: {e}")
            return {"circuits": {}}
    
    def _get_expected_stint_length(self, race: str, compound: str) -> int:
        """獲取預期 stint 長度"""
        circuit = self.race_to_circuit.get(race, race)
        compound_upper = compound.upper() if compound else "MEDIUM"
        
        circuits = self.tire_database.get("circuits", {})
        if circuit in circuits:
            optimal = circuits[circuit].get("optimal_stint_length", {})
            if compound_upper in optimal:
                return optimal[compound_upper]
        
        # 預設值
        defaults = {"SOFT": 15, "MEDIUM": 25, "HARD": 35}
        return defaults.get(compound_upper, 25)
    
    def _find_f86_files(self, years: List[int]) -> List[Path]:
        """搜尋 F86 分析結果檔案"""
        files = []
        for year in years:
            pattern = f"tire_saving_analysis_{year}_*_R_*.json"
            matches = glob.glob(str(self.json_path / pattern))
            files.extend([Path(f) for f in matches])
        
        return sorted(files)
    
    def _load_f86_result(self, file_path: Path) -> Optional[Dict]:
        """載入 F86 分析結果"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get("success"):
                return data
            return None
        except Exception as e:
            print(f"[ERROR] 載入 F86 結果失敗 {file_path}: {e}")
            return None
    
    def _validate_single_race(
        self, 
        f86_data: Dict, 
        threshold: float = None
    ) -> RaceValidationResult:
        """
        驗證單場比賽
        
        Args:
            f86_data: F86 分析結果
            threshold: 省輪胎分數閾值
        """
        if threshold is None:
            threshold = self.saving_threshold
        
        metadata = f86_data.get("data", {}).get("metadata", {})
        year = metadata.get("year", 0)
        race = metadata.get("race", "Unknown")
        session = metadata.get("session", "R")
        
        drivers = f86_data.get("data", {}).get("drivers", [])
        
        stints = []
        tp, fp, tn, fn = 0, 0, 0, 0
        
        for driver_data in drivers:
            driver_code = driver_data.get("driver_code", "UNK")
            
            for stint_data in driver_data.get("stints", []):
                stint_num = stint_data.get("stint_number", 0)
                compound = stint_data.get("compound", "MEDIUM")
                total_laps = stint_data.get("total_laps", 0)
                
                analysis = stint_data.get("saving_analysis", {})
                saving_score = analysis.get("overall_score", 0)
                saving_level = analysis.get("saving_level", "NONE")
                
                # 獲取預期 stint 長度
                expected = self._get_expected_stint_length(race, compound)
                
                # 判斷
                is_longer = total_laps > expected
                is_saving_predicted = saving_score >= threshold
                
                # 建立記錄
                record = StintValidationRecord(
                    year=year,
                    race=race,
                    session=session,
                    driver=driver_code,
                    stint_number=stint_num,
                    compound=compound,
                    actual_stint_length=total_laps,
                    expected_stint_length=expected,
                    saving_score=saving_score,
                    saving_level=saving_level,
                    is_longer_than_expected=is_longer,
                    is_saving_predicted=is_saving_predicted
                )
                stints.append(record)
                
                # 計算 TP/FP/TN/FN
                if is_saving_predicted and is_longer:
                    tp += 1
                elif is_saving_predicted and not is_longer:
                    fp += 1
                elif not is_saving_predicted and not is_longer:
                    tn += 1
                else:  # not is_saving_predicted and is_longer
                    fn += 1
        
        # 計算指標
        total = tp + fp + tn + fn
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return RaceValidationResult(
            year=year,
            race=race,
            session=session,
            total_stints=len(stints),
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            stints=stints
        )
    
    def _find_optimal_threshold(
        self, 
        all_stints: List[StintValidationRecord]
    ) -> Tuple[float, float]:
        """
        尋找最佳省輪胎分數閾值
        
        測試閾值從 20 到 70，找出 F1 最高的
        """
        best_threshold = 40
        best_f1 = 0
        
        for threshold in range(20, 75, 5):
            tp, fp, tn, fn = 0, 0, 0, 0
            
            for stint in all_stints:
                is_saving = stint.saving_score >= threshold
                is_longer = stint.is_longer_than_expected
                
                if is_saving and is_longer:
                    tp += 1
                elif is_saving and not is_longer:
                    fp += 1
                elif not is_saving and not is_longer:
                    tn += 1
                else:
                    fn += 1
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold
        
        return best_threshold, best_f1
    
    def _compute_by_compound(
        self, 
        all_stints: List[StintValidationRecord],
        threshold: float
    ) -> Dict[str, Dict[str, float]]:
        """計算各輪胎配方的指標"""
        compounds = ["SOFT", "MEDIUM", "HARD"]
        by_compound = {}
        
        for compound in compounds:
            compound_stints = [s for s in all_stints if s.compound.upper() == compound]
            if not compound_stints:
                continue
            
            tp, fp, tn, fn = 0, 0, 0, 0
            for stint in compound_stints:
                is_saving = stint.saving_score >= threshold
                is_longer = stint.is_longer_than_expected
                
                if is_saving and is_longer:
                    tp += 1
                elif is_saving and not is_longer:
                    fp += 1
                elif not is_saving and not is_longer:
                    tn += 1
                else:
                    fn += 1
            
            total = tp + fp + tn + fn
            accuracy = (tp + tn) / total if total > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            by_compound[compound] = {
                "sample_count": len(compound_stints),
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4)
            }
        
        return by_compound
    
    def validate(
        self,
        training_years: List[int] = None,
        test_years: List[int] = None,
        saving_threshold: float = None,
        save_results: bool = True
    ) -> ValidationSummary:
        """
        執行驗證
        
        Args:
            training_years: 訓練年份（用於尋找最佳閾值）
            test_years: 測試年份
            saving_threshold: 固定閾值（若為 None，則自動尋找最佳）
            save_results: 是否儲存結果
        """
        if training_years is None:
            training_years = [2023, 2024]
        if test_years is None:
            test_years = [2025]
        
        print("[INFO] 啟動 F86 驗證程序")
        print(f"  - 訓練年份: {training_years}")
        print(f"  - 測試年份: {test_years}")
        
        # 階段 1: 載入訓練數據
        print("\n[STEP 1] 載入訓練數據...")
        train_files = self._find_f86_files(training_years)
        print(f"  - 找到 {len(train_files)} 個訓練檔案")
        
        train_stints = []
        for file in train_files:
            data = self._load_f86_result(file)
            if data:
                result = self._validate_single_race(data, threshold=40)  # 先用預設閾值收集
                train_stints.extend(result.stints)
        
        print(f"  - 收集 {len(train_stints)} 個訓練 stint")
        
        # 階段 2: 尋找最佳閾值（若未指定）
        if saving_threshold is None:
            print("\n[STEP 2] 尋找最佳閾值...")
            best_threshold, best_f1 = self._find_optimal_threshold(train_stints)
            print(f"  - 最佳閾值: {best_threshold}")
            print(f"  - 訓練 F1: {best_f1:.4f}")
        else:
            best_threshold = saving_threshold
            _, best_f1 = self._find_optimal_threshold(train_stints)
            print(f"\n[STEP 2] 使用固定閾值: {best_threshold}")
        
        self.saving_threshold = best_threshold
        
        # 階段 3: 測試數據驗證
        print("\n[STEP 3] 載入測試數據...")
        test_files = self._find_f86_files(test_years)
        print(f"  - 找到 {len(test_files)} 個測試檔案")
        
        test_results = []
        all_test_stints = []
        
        for file in test_files:
            data = self._load_f86_result(file)
            if data:
                result = self._validate_single_race(data, threshold=best_threshold)
                test_results.append(result)
                all_test_stints.extend(result.stints)
                
                race_name = result.race
                acc = result.accuracy
                f1 = result.f1_score
                print(f"  ↳ {result.year} {race_name}: Accuracy={acc:.2%}, F1={f1:.4f}")
        
        # 階段 4: 計算總體指標
        print("\n[STEP 4] 計算總體指標...")
        
        total_tp = sum(r.true_positives for r in test_results)
        total_fp = sum(r.false_positives for r in test_results)
        total_tn = sum(r.true_negatives for r in test_results)
        total_fn = sum(r.false_negatives for r in test_results)
        total = total_tp + total_fp + total_tn + total_fn
        
        overall_accuracy = (total_tp + total_tn) / total if total > 0 else 0
        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        overall_f1 = (
            2 * overall_precision * overall_recall / (overall_precision + overall_recall) 
            if (overall_precision + overall_recall) > 0 else 0
        )
        
        # 各輪胎配方指標
        by_compound = self._compute_by_compound(all_test_stints, best_threshold)
        
        summary = ValidationSummary(
            training_years=training_years,
            test_years=test_years,
            total_races=len(test_results),
            total_stints=len(all_test_stints),
            overall_accuracy=overall_accuracy,
            overall_precision=overall_precision,
            overall_recall=overall_recall,
            overall_f1=overall_f1,
            saving_threshold=best_threshold,
            by_compound=by_compound,
            best_threshold=best_threshold,
            best_f1=best_f1
        )
        
        # 輸出總結
        print("\n" + "=" * 60)
        print("F86 驗證結果總結")
        print("=" * 60)
        print(f"訓練年份: {training_years}")
        print(f"測試年份: {test_years}")
        print(f"省輪胎閾值: {best_threshold}")
        print(f"總比賽數: {len(test_results)}")
        print(f"總 stint 數: {len(all_test_stints)}")
        print(f"\n總體指標:")
        print(f"  - Accuracy (準確率): {overall_accuracy:.2%}")
        print(f"  - Precision (精確率): {overall_precision:.2%}")
        print(f"  - Recall (召回率): {overall_recall:.2%}")
        print(f"  - F1 Score: {overall_f1:.4f}")
        
        if by_compound:
            print(f"\n各輪胎配方:")
            for compound, metrics in by_compound.items():
                print(f"  {compound}: F1={metrics['f1_score']:.4f}, n={metrics['sample_count']}")
        
        # 儲存結果
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.validation_output_path / f"f86_validation_{timestamp}.json"
            
            output_data = {
                "summary": summary.to_dict(),
                "race_results": [r.to_dict() for r in test_results],
                "validation_timestamp": timestamp,
                "notes": "Validation of F86 Tire Saving Behavior Prediction"
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n[SUCCESS] 驗證結果已儲存: {output_file}")
        
        return summary


# ============================================================================
# CLI 入口函數
# ============================================================================

def run_tire_saving_validation(
    training_years: List[int] = None,
    test_years: List[int] = None,
    saving_threshold: float = None,
    base_path: str = None
) -> Dict[str, Any]:
    """
    執行 F86 驗證
    
    Args:
        training_years: 訓練年份
        test_years: 測試年份
        saving_threshold: 省輪胎分數閾值
        base_path: 專案根目錄
    """
    validator = TireSavingValidator(base_path)
    summary = validator.validate(
        training_years=training_years,
        test_years=test_years,
        saving_threshold=saving_threshold,
        save_results=True
    )
    
    return {
        "success": True,
        "message": "F86 驗證完成",
        "data": summary.to_dict()
    }


# ============================================================================
# 直接執行
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # 預設: 2023-2024 訓練, 2025 測試
    train = [2023, 2024]
    test = [2025]
    
    if len(sys.argv) >= 2:
        # 可以傳入自定義測試年份
        test = [int(sys.argv[1])]
    
    result = run_tire_saving_validation(
        training_years=train,
        test_years=test
    )
    
    if result["success"]:
        print("\n驗證成功完成")
    else:
        print(f"\n驗證失敗: {result.get('message', 'Unknown error')}")
