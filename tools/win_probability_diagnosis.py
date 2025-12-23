#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
勝率預測診斷工具 - LLM 輔助分析

此工具用於：
1. 收集訓練數據中的預測 vs 實際結果
2. 計算預測誤差並識別問題模式
3. 生成結構化報告供 LLM 分析

使用方法：
    python tools/win_probability_diagnosis.py

作者: F1T Dev Team
日期: 2025-12-05
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

import numpy as np
import pandas as pd

# 添加專案根目錄到路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 嘗試載入預測器
try:
    from CLI_modules.cli.prediction.live_win_probability.predictor import (
        LiveWinProbabilityPredictor,
        DRIVER_CIRCUIT_AFFINITY,
        CIRCUIT_OVERTAKE_DIFFICULTY,
    )
    PREDICTOR_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] 無法載入預測器: {e}")
    PREDICTOR_AVAILABLE = False


@dataclass
class RacePredictionError:
    """單場比賽的預測誤差"""
    year: int
    race_name: str
    lap: int
    driver_code: str
    position: int
    gap_to_leader: float
    laps_remaining: int
    tyre_compound: int
    tyre_age: int
    qualifying_position: int
    final_position: int
    predicted_position: float = 0.0
    position_error: float = 0.0
    p1_predicted: float = 0.0
    p1_actual: float = 0.0  # 1 if winner, 0 otherwise


@dataclass
class DiagnosisReport:
    """診斷報告"""
    total_samples: int
    total_races: int
    years: List[int]
    
    # 整體誤差
    mean_position_error: float
    median_position_error: float
    
    # 按情境分類的誤差
    errors_by_circuit_type: Dict[str, float]
    errors_by_position_group: Dict[str, float]
    errors_by_lap_phase: Dict[str, float]
    errors_by_tyre: Dict[str, float]
    
    # 最大誤差案例
    worst_predictions: List[Dict]
    
    # 車手特定問題
    driver_specific_errors: Dict[str, Dict]
    
    # 賽道特定問題
    circuit_specific_errors: Dict[str, Dict]
    
    # 建議調整
    suggested_adjustments: List[Dict]


class WinProbabilityDiagnoser:
    """勝率預測診斷器"""
    
    # 賽道類型映射
    CIRCUIT_TYPES = {
        "Monaco": "street",
        "Singapore": "street", 
        "Azerbaijan": "street",
        "Saudi_Arabian": "street",
        "Las_Vegas": "street",
        "Monza": "high_speed",
        "Italian": "high_speed",
        "Belgian": "high_speed",
        "Spa": "high_speed",
        "British": "high_speed",
        "Japanese": "technical",
        "Hungarian": "technical",
        "Dutch": "technical",
        "Spanish": "technical",
        "Mexican": "high_altitude",
        "Brazilian": "mixed",
        "Abu_Dhabi": "mixed",
        "Bahrain": "mixed",
        "Australian": "mixed",
        "Canadian": "mixed",
        "Austrian": "high_speed",
        "Miami": "mixed",
        "Qatar": "high_speed",
        "Chinese": "mixed",
        "Emilia_Romagna": "mixed",
    }
    
    # 輪胎類型名稱
    TYRE_NAMES = {
        1: "SOFT",
        2: "MEDIUM", 
        3: "HARD",
        4: "INTERMEDIATE",
        5: "WET",
    }
    
    def __init__(self, training_data_path: str = None):
        """
        初始化診斷器
        
        Args:
            training_data_path: 訓練數據 CSV 路徑
        """
        self.training_data_path = training_data_path or str(
            PROJECT_ROOT / "data" / "live_win_probability" / "training_data.csv"
        )
        self.df: pd.DataFrame = None
        self.errors: List[RacePredictionError] = []
        self.predictor = None
        
    def load_data(self) -> bool:
        """載入訓練數據"""
        try:
            self.df = pd.read_csv(self.training_data_path)
            print(f"[OK] 載入 {len(self.df)} 筆訓練數據")
            print(f"    年份: {sorted(self.df['year'].unique())}")
            print(f"    比賽數: {self.df['race_name'].nunique()}")
            return True
        except Exception as e:
            print(f"[ERROR] 載入數據失敗: {e}")
            return False
    
    def load_predictor(self, model_path: str = None) -> bool:
        """載入預測模型"""
        if not PREDICTOR_AVAILABLE:
            print("[WARN] 預測器不可用，將使用簡化分析")
            return False
            
        try:
            self.predictor = LiveWinProbabilityPredictor()
            model_path = model_path or str(
                PROJECT_ROOT / "models" / "win_probability_xgb_v2.pkl"
            )
            if os.path.exists(model_path):
                self.predictor.load_model(model_path)
                print(f"[OK] 載入預測模型: {model_path}")
                return True
            else:
                print(f"[WARN] 模型檔案不存在: {model_path}")
                return False
        except Exception as e:
            print(f"[ERROR] 載入預測器失敗: {e}")
            return False
    
    def analyze_errors(self) -> DiagnosisReport:
        """分析預測誤差"""
        if self.df is None:
            raise ValueError("請先呼叫 load_data()")
        
        print("\n[分析中] 計算預測誤差...")
        
        # 收集比賽中段的預測誤差 (更能反映預測能力)
        errors_data = []
        
        # 定義要分析的圈數點 (比賽進度 25%, 50%, 75%)
        analysis_points = [0.25, 0.50, 0.75]
        
        # 按比賽分組
        for (year, race), race_df in self.df.groupby(['year', 'race_name']):
            total_laps = race_df['current_lap'].max()
            
            for progress in analysis_points:
                target_lap = int(total_laps * progress)
                if target_lap < 1:
                    target_lap = 1
                
                # 找最接近目標圈數的數據
                lap_df = race_df[race_df['current_lap'] == target_lap]
                if lap_df.empty:
                    # 找最接近的圈數
                    available_laps = race_df['current_lap'].unique()
                    closest_lap = min(available_laps, key=lambda x: abs(x - target_lap))
                    lap_df = race_df[race_df['current_lap'] == closest_lap]
                
                for _, row in lap_df.iterrows():
                    # 使用當前位置作為預測位置 (baseline)
                    # 這代表「如果位置不變」的預測
                    predicted_pos = row['position']
                    actual_pos = row['final_position']
                    
                    error = RacePredictionError(
                        year=int(year),
                        race_name=race,
                        lap=int(row['current_lap']),
                        driver_code=row['driver_code'],
                        position=int(row['position']),
                        gap_to_leader=float(row['gap_to_leader']),
                        laps_remaining=int(row['laps_remaining']),
                        tyre_compound=int(row['tyre_compound']),
                        tyre_age=int(row['tyre_age']),
                        qualifying_position=int(row['qualifying_position']),
                        final_position=int(actual_pos),
                        predicted_position=predicted_pos,
                        position_error=abs(predicted_pos - actual_pos),
                        p1_predicted=1.0 if row['position'] == 1 else 0.0,
                        p1_actual=1.0 if actual_pos == 1 else 0.0,
                    )
                    errors_data.append(error)
        
        self.errors = errors_data
        print(f"    收集 {len(errors_data)} 筆最終圈預測數據")
        
        # 計算統計
        errors_df = pd.DataFrame([asdict(e) for e in errors_data])
        
        # 1. 整體誤差
        mean_error = errors_df['position_error'].mean()
        median_error = errors_df['position_error'].median()
        
        # 2. 按賽道類型分類
        errors_df['circuit_type'] = errors_df['race_name'].map(
            lambda x: self.CIRCUIT_TYPES.get(x, "unknown")
        )
        errors_by_circuit = errors_df.groupby('circuit_type')['position_error'].mean().to_dict()
        
        # 3. 按位置分組 (前3, 4-10, 11-20)
        def position_group(pos):
            if pos <= 3:
                return "P1-P3"
            elif pos <= 10:
                return "P4-P10"
            else:
                return "P11-P20"
        
        errors_df['position_group'] = errors_df['position'].apply(position_group)
        errors_by_position = errors_df.groupby('position_group')['position_error'].mean().to_dict()
        
        # 4. 按比賽階段分組 (開始, 中段, 結尾)
        def lap_phase(remaining, total=57):
            progress = 1 - (remaining / total)
            if progress < 0.33:
                return "early"
            elif progress < 0.67:
                return "middle"
            else:
                return "late"
        
        errors_df['lap_phase'] = errors_df['laps_remaining'].apply(lap_phase)
        errors_by_phase = errors_df.groupby('lap_phase')['position_error'].mean().to_dict()
        
        # 5. 按輪胎類型
        errors_df['tyre_name'] = errors_df['tyre_compound'].map(
            lambda x: self.TYRE_NAMES.get(x, "UNKNOWN")
        )
        errors_by_tyre = errors_df.groupby('tyre_name')['position_error'].mean().to_dict()
        
        # 6. 最大誤差案例
        worst = errors_df.nlargest(10, 'position_error')[
            ['year', 'race_name', 'driver_code', 'position', 'final_position', 
             'position_error', 'gap_to_leader', 'qualifying_position']
        ].to_dict('records')
        
        # 7. 車手特定問題
        driver_errors = {}
        for driver, grp in errors_df.groupby('driver_code'):
            driver_errors[driver] = {
                'mean_error': float(grp['position_error'].mean()),
                'samples': len(grp),
                'p1_accuracy': float((grp['p1_predicted'] == grp['p1_actual']).mean()),
                'gained_positions': float((grp['position'] - grp['final_position']).mean()),
            }
        
        # 8. 賽道特定問題
        circuit_errors = {}
        for circuit, grp in errors_df.groupby('race_name'):
            circuit_errors[circuit] = {
                'mean_error': float(grp['position_error'].mean()),
                'samples': len(grp),
                'circuit_type': self.CIRCUIT_TYPES.get(circuit, "unknown"),
                'position_changes': float(abs(grp['position'] - grp['final_position']).mean()),
            }
        
        # 9. 建議調整
        suggestions = self._generate_suggestions(
            errors_df, driver_errors, circuit_errors
        )
        
        report = DiagnosisReport(
            total_samples=len(errors_data),
            total_races=self.df['race_name'].nunique(),
            years=sorted(self.df['year'].unique().tolist()),
            mean_position_error=float(mean_error),
            median_position_error=float(median_error),
            errors_by_circuit_type=errors_by_circuit,
            errors_by_position_group=errors_by_position,
            errors_by_lap_phase=errors_by_phase,
            errors_by_tyre=errors_by_tyre,
            worst_predictions=worst,
            driver_specific_errors=driver_errors,
            circuit_specific_errors=circuit_errors,
            suggested_adjustments=suggestions,
        )
        
        return report
    
    def _generate_suggestions(
        self, 
        errors_df: pd.DataFrame,
        driver_errors: Dict,
        circuit_errors: Dict,
    ) -> List[Dict]:
        """生成調整建議"""
        suggestions = []
        
        # 1. 找出預測誤差最大的車手
        worst_drivers = sorted(
            driver_errors.items(), 
            key=lambda x: x[1]['mean_error'], 
            reverse=True
        )[:5]
        
        for driver, stats in worst_drivers:
            if stats['mean_error'] > 2.0:  # 平均誤差超過 2 個位置
                gained = stats['gained_positions']
                suggestions.append({
                    'type': 'driver_adjustment',
                    'driver': driver,
                    'issue': f"平均預測誤差 {stats['mean_error']:.2f} 個位置",
                    'observation': f"平均每場{'上升' if gained > 0 else '下降'} {abs(gained):.1f} 個位置",
                    'suggestion': f"考慮{'降低' if gained > 0 else '提高'} {driver} 的基礎預測排名",
                    'priority': 'high' if stats['mean_error'] > 3.0 else 'medium',
                })
        
        # 2. 找出預測誤差最大的賽道
        worst_circuits = sorted(
            circuit_errors.items(),
            key=lambda x: x[1]['mean_error'],
            reverse=True
        )[:5]
        
        for circuit, stats in worst_circuits:
            if stats['mean_error'] > 2.5:
                suggestions.append({
                    'type': 'circuit_adjustment',
                    'circuit': circuit,
                    'circuit_type': stats['circuit_type'],
                    'issue': f"平均預測誤差 {stats['mean_error']:.2f} 個位置",
                    'observation': f"平均位置變動 {stats['position_changes']:.1f}",
                    'suggestion': f"調整 {circuit} ({stats['circuit_type']}) 的超車難度係數",
                    'priority': 'high' if stats['mean_error'] > 3.5 else 'medium',
                })
        
        # 3. 賽道類型整體問題
        circuit_type_avg = errors_df.groupby('circuit_type')['position_error'].mean()
        overall_avg = errors_df['position_error'].mean()
        
        for ctype, error in circuit_type_avg.items():
            if error > overall_avg * 1.3:  # 比平均高 30%
                suggestions.append({
                    'type': 'circuit_type_adjustment',
                    'circuit_type': ctype,
                    'issue': f"此類賽道誤差 ({error:.2f}) 高於平均 ({overall_avg:.2f})",
                    'suggestion': f"檢視 {ctype} 賽道的 Q 補償權重和超車難度設定",
                    'priority': 'medium',
                })
        
        return suggestions
    
    def generate_llm_prompt(self, report: DiagnosisReport) -> str:
        """生成供 LLM 分析的提示"""
        prompt = f"""# F1 勝率預測模型診斷報告

## 數據概覽
- 總樣本數: {report.total_samples}
- 涵蓋比賽: {report.total_races} 場
- 年份: {report.years}

## 整體表現
- 平均位置預測誤差: {report.mean_position_error:.2f} 個位置
- 中位數位置預測誤差: {report.median_position_error:.2f} 個位置

## 按賽道類型分析
"""
        for ctype, error in sorted(report.errors_by_circuit_type.items(), key=lambda x: x[1], reverse=True):
            prompt += f"- {ctype}: 平均誤差 {error:.2f}\n"
        
        prompt += f"""
## 按位置分組分析
"""
        for group, error in report.errors_by_position_group.items():
            prompt += f"- {group}: 平均誤差 {error:.2f}\n"
        
        prompt += f"""
## 按輪胎類型分析
"""
        for tyre, error in sorted(report.errors_by_tyre.items(), key=lambda x: x[1], reverse=True):
            prompt += f"- {tyre}: 平均誤差 {error:.2f}\n"

        prompt += f"""
## 最大預測誤差案例 (Top 10)
"""
        for i, case in enumerate(report.worst_predictions, 1):
            prompt += f"{i}. {case['year']} {case['race_name']}: {case['driver_code']} "
            prompt += f"P{case['position']}→P{case['final_position']} "
            prompt += f"(誤差: {case['position_error']:.0f}, Q: P{case['qualifying_position']})\n"
        
        prompt += f"""
## 車手特定問題 (誤差最大的 5 位)
"""
        sorted_drivers = sorted(
            report.driver_specific_errors.items(),
            key=lambda x: x[1]['mean_error'],
            reverse=True
        )[:5]
        for driver, stats in sorted_drivers:
            prompt += f"- {driver}: 平均誤差 {stats['mean_error']:.2f}, "
            prompt += f"樣本數 {stats['samples']}, "
            prompt += f"平均位置變動 {stats['gained_positions']:+.1f}\n"
        
        prompt += f"""
## 賽道特定問題 (誤差最大的 5 場)
"""
        sorted_circuits = sorted(
            report.circuit_specific_errors.items(),
            key=lambda x: x[1]['mean_error'],
            reverse=True
        )[:5]
        for circuit, stats in sorted_circuits:
            prompt += f"- {circuit} ({stats['circuit_type']}): "
            prompt += f"平均誤差 {stats['mean_error']:.2f}, "
            prompt += f"位置變動 {stats['position_changes']:.1f}\n"
        
        prompt += f"""
## 自動生成的調整建議
"""
        for i, sug in enumerate(report.suggested_adjustments, 1):
            prompt += f"\n### 建議 {i} [{sug['priority'].upper()}]\n"
            prompt += f"- 類型: {sug['type']}\n"
            prompt += f"- 問題: {sug['issue']}\n"
            prompt += f"- 觀察: {sug.get('observation', 'N/A')}\n"
            prompt += f"- 建議: {sug['suggestion']}\n"
        
        prompt += """
---

## 請分析以上報告並回答:

1. **主要問題識別**: 預測模型最大的問題是什麼？

2. **根本原因分析**: 為什麼會出現這些預測誤差？

3. **具體調整建議**: 
   - 哪些硬編碼的權重需要調整？
   - 是否需要增加或移除某些特徵？
   - 模型架構是否需要改變？

4. **優先級排序**: 應該先修正哪些問題？

5. **驗證方法**: 如何驗證調整後的效果？
"""
        return prompt
    
    def save_report(self, report: DiagnosisReport, output_dir: str = None):
        """儲存報告"""
        output_dir = Path(output_dir or PROJECT_ROOT / "reports")
        output_dir.mkdir(exist_ok=True)
        
        # 儲存 JSON 報告
        json_path = output_dir / "win_probability_diagnosis.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        print(f"[OK] JSON 報告: {json_path}")
        
        # 儲存 LLM 提示
        prompt = self.generate_llm_prompt(report)
        prompt_path = output_dir / "win_probability_diagnosis_prompt.md"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"[OK] LLM 提示: {prompt_path}")
        
        return json_path, prompt_path


def main():
    """主函數"""
    print("=" * 60)
    print("F1 勝率預測診斷工具")
    print("=" * 60)
    
    diagnoser = WinProbabilityDiagnoser()
    
    # 載入數據
    if not diagnoser.load_data():
        return
    
    # 載入預測器 (可選)
    diagnoser.load_predictor()
    
    # 分析誤差
    report = diagnoser.analyze_errors()
    
    # 顯示摘要
    print("\n" + "=" * 60)
    print("診斷摘要")
    print("=" * 60)
    print(f"平均位置預測誤差: {report.mean_position_error:.2f}")
    print(f"中位數誤差: {report.median_position_error:.2f}")
    print(f"\n按賽道類型誤差:")
    for ctype, error in sorted(report.errors_by_circuit_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ctype}: {error:.2f}")
    
    print(f"\n建議調整數量: {len(report.suggested_adjustments)}")
    
    # 儲存報告
    json_path, prompt_path = diagnoser.save_report(report)
    
    print("\n" + "=" * 60)
    print("下一步")
    print("=" * 60)
    print(f"1. 查看 LLM 提示檔案: {prompt_path}")
    print("2. 將提示內容貼給 Claude/GPT 進行深度分析")
    print("3. 根據建議調整 predictor.py 中的權重")
    

if __name__ == "__main__":
    main()
