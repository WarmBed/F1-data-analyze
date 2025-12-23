#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F87 - Real-Time Driver Strategy Predictor (即時車手策略預測器)

功能:
    每圈即時計算 tire saving 分數，動態預測進站圈數
    專為 Live Timing 設計的逐圈計算架構
    
核心邏輯:
    1. 使用滑動視窗 (最近 N 圈) 計算即時 tire saving score
    2. 隨著每圈數據更新，動態調整進站預測
    3. 補償公式: 預測進站圈 = 基準最佳圈數 x (1 + 累積補償係數)
    
即時計算指標:
    - coasting_trend: 滑行時間變化率
    - throttle_trend: 油門比例變化率
    - lap_time_trend: 圈速衰退率
    - pace_consistency: 配速穩定性
    
Live Timing 整合:
    - 每圈調用 update_lap() 更新數據
    - 即時獲取 get_pit_prediction() 預測進站圈數
    - 支援多車手同時追蹤

版本: 2.0.0 (逐圈即時計算版)
作者: F1T Team
日期: 2025-12-05
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import deque


# ============================================================================
# 數據結構定義
# ============================================================================

@dataclass
class LapMetrics:
    """單圈指標"""
    lap_number: int
    coasting_s: float
    full_throttle_ratio: float
    lap_time_s: float
    compound: str
    tyre_life: int
    stint: int
    sector_times: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RealTimeTireSaving:
    """即時省胎分析結果"""
    current_lap: int
    window_size: int
    
    # 即時趨勢 (最近 N 圈)
    coasting_trend: float       # >1.0 = 滑行增加 (省胎)
    throttle_trend: float       # <1.0 = 油門減少 (省胎)
    lap_time_trend: float       # 每圈慢多少秒
    pace_consistency: float     # 配速穩定性 (std/mean)
    
    # 即時分數
    instant_score: float        # 當前圈的省胎分數 (0-100)
    rolling_avg_score: float    # 滑動平均分數
    saving_level: str           # NONE/LIGHT/MODERATE/HEAVY
    
    # 累積統計
    stint_avg_score: float      # 整個 stint 平均分數
    cumulative_saving: float    # 累積省胎效果
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class PitPrediction:
    """進站預測"""
    driver_code: str
    current_lap: int
    current_stint: int
    compound: str
    tyre_life: int
    
    # 預測
    base_optimal_laps: int          # 大數據預估
    current_adjustment: float       # 當前補償係數
    predicted_pit_lap: int          # 預測進站圈
    confidence: float               # 信心度 (0-1)
    
    # 即時省胎分析
    tire_saving: RealTimeTireSaving
    
    # 預警
    warning_level: str              # SAFE/CAUTION/CRITICAL
    laps_remaining: int             # 預估剩餘圈數
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["tire_saving"] = self.tire_saving.to_dict()
        return result


# ============================================================================
# 即時省胎分數計算器
# ============================================================================

class RealTimeTireSavingCalculator:
    """即時省胎分數計算器 - 逐圈計算"""
    
    # 權重設定
    WEIGHTS = {
        "coasting": 0.30,      # 滑行時間權重
        "throttle": 0.25,      # 油門比例權重
        "lap_time": 0.25,      # 圈速衰退權重
        "consistency": 0.20,   # 配速穩定性權重
    }
    
    # 分數閾值
    THRESHOLDS = {
        "NONE": (0, 20),
        "LIGHT": (20, 40),
        "MODERATE": (40, 65),
        "HEAVY": (65, 100),
    }
    
    def __init__(self, window_size: int = 5):
        """
        初始化計算器
        
        Args:
            window_size: 滑動視窗大小 (預設 5 圈)
        """
        self.window_size = window_size
    
    def calculate_instant_score(self, laps: List[LapMetrics]) -> RealTimeTireSaving:
        """
        計算即時省胎分數
        
        Args:
            laps: 最近 N 圈的數據
            
        Returns:
            RealTimeTireSaving 即時分析結果
        """
        if len(laps) < 2:
            # 數據不足，返回預設值
            return RealTimeTireSaving(
                current_lap=laps[-1].lap_number if laps else 0,
                window_size=len(laps),
                coasting_trend=1.0,
                throttle_trend=1.0,
                lap_time_trend=0.0,
                pace_consistency=0.0,
                instant_score=0.0,
                rolling_avg_score=0.0,
                saving_level="NONE",
                stint_avg_score=0.0,
                cumulative_saving=0.0
            )
        
        # 取最近 window_size 圈
        recent_laps = laps[-self.window_size:] if len(laps) >= self.window_size else laps
        
        # 計算各項趨勢
        coasting_values = [lap.coasting_s for lap in recent_laps if lap.coasting_s is not None]
        throttle_values = [lap.full_throttle_ratio for lap in recent_laps if lap.full_throttle_ratio is not None]
        lap_time_values = [lap.lap_time_s for lap in recent_laps if lap.lap_time_s is not None and lap.lap_time_s > 0]
        
        # 1. 滑行趨勢 (後半 vs 前半)
        mid = len(coasting_values) // 2
        if mid > 0:
            early_coasting = np.mean(coasting_values[:mid])
            late_coasting = np.mean(coasting_values[mid:])
            coasting_trend = late_coasting / early_coasting if early_coasting > 0 else 1.0
        else:
            coasting_trend = 1.0
        
        # 2. 油門趨勢 (後半 vs 前半)
        if mid > 0:
            early_throttle = np.mean(throttle_values[:mid])
            late_throttle = np.mean(throttle_values[mid:])
            throttle_trend = late_throttle / early_throttle if early_throttle > 0 else 1.0
        else:
            throttle_trend = 1.0
        
        # 3. 圈速衰退 (線性迴歸斜率)
        if len(lap_time_values) >= 2:
            x = np.arange(len(lap_time_values))
            slope, _ = np.polyfit(x, lap_time_values, 1)
            lap_time_trend = slope  # 正值 = 變慢
        else:
            lap_time_trend = 0.0
        
        # 4. 配速穩定性 (變異係數)
        if len(lap_time_values) >= 2:
            pace_consistency = np.std(lap_time_values) / np.mean(lap_time_values) if np.mean(lap_time_values) > 0 else 0
        else:
            pace_consistency = 0.0
        
        # 計算即時分數 (0-100)
        instant_score = self._calculate_score(
            coasting_trend, throttle_trend, lap_time_trend, pace_consistency
        )
        
        # 滑動平均分數
        rolling_avg_score = instant_score  # 可以擴展為歷史平均
        
        # 判斷省胎等級
        saving_level = self._get_saving_level(instant_score)
        
        # 計算累積省胎效果
        cumulative_saving = self._calculate_cumulative_saving(laps)
        
        return RealTimeTireSaving(
            current_lap=laps[-1].lap_number,
            window_size=len(recent_laps),
            coasting_trend=round(coasting_trend, 4),
            throttle_trend=round(throttle_trend, 4),
            lap_time_trend=round(lap_time_trend, 4),
            pace_consistency=round(pace_consistency, 4),
            instant_score=round(instant_score, 1),
            rolling_avg_score=round(rolling_avg_score, 1),
            saving_level=saving_level,
            stint_avg_score=round(instant_score, 1),
            cumulative_saving=round(cumulative_saving, 2)
        )
    
    def _calculate_score(
        self,
        coasting_trend: float,
        throttle_trend: float,
        lap_time_trend: float,
        pace_consistency: float
    ) -> float:
        """
        計算省胎分數 (0-100)
        
        高分 = 強烈省胎行為：
        - 滑行時間增加 (coasting_trend > 1)
        - 油門比例降低 (throttle_trend < 1)
        - 圈速變慢但穩定
        - 配速一致
        """
        # 滑行分數: 增加 10% = +25 分
        coasting_score = min(100, max(0, (coasting_trend - 1.0) * 250))
        
        # 油門分數: 減少 5% = +25 分
        throttle_score = min(100, max(0, (1.0 - throttle_trend) * 500))
        
        # 圈速分數: 每圈慢 0.1 秒 = +10 分 (最高 40 分)
        lap_time_score = min(40, max(0, lap_time_trend * 100))
        
        # 穩定性分數: CV < 0.5% = 高分 (反向，越穩定越高)
        consistency_score = min(100, max(0, (0.02 - pace_consistency) * 2500))
        
        # 加權總分
        total = (
            coasting_score * self.WEIGHTS["coasting"] +
            throttle_score * self.WEIGHTS["throttle"] +
            lap_time_score * self.WEIGHTS["lap_time"] +
            consistency_score * self.WEIGHTS["consistency"]
        )
        
        return min(100, max(0, total))
    
    def _get_saving_level(self, score: float) -> str:
        """根據分數取得省胎等級"""
        if score < 20:
            return "NONE"
        elif score < 40:
            return "LIGHT"
        elif score < 65:
            return "MODERATE"
        else:
            return "HEAVY"
    
    def _calculate_cumulative_saving(self, laps: List[LapMetrics]) -> float:
        """計算累積省胎效果 (預估多跑幾圈)"""
        if len(laps) < 3:
            return 0.0
        
        # 基於滑行時間增加估算
        coasting_values = [lap.coasting_s for lap in laps]
        if len(coasting_values) >= 2:
            # 滑行時間增加 1 秒 ≈ 延長 0.5 圈
            avg_increase = np.mean(coasting_values[-3:]) - np.mean(coasting_values[:3])
            return max(0, avg_increase * 0.5)
        
        return 0.0


# ============================================================================
# 即時進站預測器
# ============================================================================

class RealTimePitPredictor:
    """即時進站預測器 - Live Timing 專用"""
    
    # 補償係數表 (根據 saving_level)
    ADJUSTMENT_TABLE = {
        "NONE": 0.0,
        "LIGHT": 0.08,       # +8%
        "MODERATE": 0.15,    # +15%
        "HEAVY": 0.25,       # +25%
    }
    
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
    
    def __init__(self, base_path: str = None, window_size: int = 5):
        """
        初始化預測器
        
        Args:
            base_path: 專案根目錄
            window_size: 滑動視窗大小
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
        self.base_path = Path(base_path)
        self.config_dir = self.base_path / "config"
        
        # 載入輪胎資料庫
        self.tire_db = self._load_tire_database()
        
        # 省胎計算器
        self.calculator = RealTimeTireSavingCalculator(window_size)
        
        # 車手數據追蹤 (driver_code -> List[LapMetrics])
        self.driver_laps: Dict[str, List[LapMetrics]] = {}
        
        # 當前賽事資訊
        self.current_race: str = ""
        self.current_session: str = "R"
    
    def _load_tire_database(self) -> Dict[str, Any]:
        """載入輪胎衰退資料庫"""
        db_path = self.config_dir / "tire_degradation_database.json"
        if db_path.exists():
            with open(db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
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
        return optimal.get(compound.upper(), 20)
    
    def set_race(self, race: str, session: str = "R"):
        """設定當前賽事"""
        self.current_race = race
        self.current_session = session
        self.driver_laps.clear()
    
    def update_lap(
        self,
        driver_code: str,
        lap_number: int,
        lap_time_s: float,
        coasting_s: float,
        full_throttle_ratio: float,
        compound: str,
        tyre_life: int,
        stint: int,
        sector_times: List[float] = None
    ) -> PitPrediction:
        """
        更新單圈數據並返回即時預測
        
        這是 Live Timing 的核心介面，每圈調用一次
        
        Args:
            driver_code: 車手代碼
            lap_number: 圈數
            lap_time_s: 圈速 (秒)
            coasting_s: 滑行時間 (秒)
            full_throttle_ratio: 油門比例
            compound: 輪胎種類
            tyre_life: 輪胎壽命
            stint: 當前 stint
            sector_times: 各 sector 時間
            
        Returns:
            PitPrediction 即時進站預測
        """
        # 建立圈數據
        lap = LapMetrics(
            lap_number=lap_number,
            coasting_s=coasting_s,
            full_throttle_ratio=full_throttle_ratio,
            lap_time_s=lap_time_s,
            compound=compound.upper(),
            tyre_life=tyre_life,
            stint=stint,
            sector_times=sector_times or []
        )
        
        # 初始化車手追蹤
        if driver_code not in self.driver_laps:
            self.driver_laps[driver_code] = []
        
        # 檢查是否換胎 (stint 改變)
        if self.driver_laps[driver_code]:
            last_lap = self.driver_laps[driver_code][-1]
            if last_lap.stint != stint:
                # 新 stint，清除舊數據
                self.driver_laps[driver_code] = []
        
        # 加入新數據
        self.driver_laps[driver_code].append(lap)
        
        # 計算即時省胎分數
        tire_saving = self.calculator.calculate_instant_score(
            self.driver_laps[driver_code]
        )
        
        # 計算進站預測
        return self._predict_pit(driver_code, lap, tire_saving)
    
    def _predict_pit(
        self,
        driver_code: str,
        current_lap: LapMetrics,
        tire_saving: RealTimeTireSaving
    ) -> PitPrediction:
        """計算進站預測"""
        # 取得基準最佳圈數
        base_optimal = self._get_optimal_stint_length(
            self.current_race,
            current_lap.compound
        )
        
        # 計算補償係數 (基於省胎等級 + 累積效果)
        base_adjustment = self.ADJUSTMENT_TABLE.get(tire_saving.saving_level, 0.0)
        
        # 動態調整: 分數越高，補償越多
        score_factor = tire_saving.rolling_avg_score / 100.0
        dynamic_adjustment = base_adjustment * (1 + score_factor * 0.5)
        
        # 計算預測進站圈
        predicted_laps = base_optimal * (1 + dynamic_adjustment)
        predicted_pit_lap = current_lap.stint * base_optimal + round(predicted_laps) - base_optimal
        
        # 簡化計算: 直接用輪胎壽命 + 預測剩餘
        laps_remaining = max(0, round(predicted_laps) - current_lap.tyre_life)
        predicted_pit_lap = current_lap.lap_number + laps_remaining
        
        # 計算信心度 (數據越多越有信心)
        data_points = len(self.driver_laps.get(driver_code, []))
        confidence = min(0.95, 0.5 + data_points * 0.05)
        
        # 判斷預警等級
        if laps_remaining <= 2:
            warning_level = "CRITICAL"
        elif laps_remaining <= 5:
            warning_level = "CAUTION"
        else:
            warning_level = "SAFE"
        
        return PitPrediction(
            driver_code=driver_code,
            current_lap=current_lap.lap_number,
            current_stint=current_lap.stint,
            compound=current_lap.compound,
            tyre_life=current_lap.tyre_life,
            base_optimal_laps=base_optimal,
            current_adjustment=round(dynamic_adjustment, 4),
            predicted_pit_lap=predicted_pit_lap,
            confidence=round(confidence, 2),
            tire_saving=tire_saving,
            warning_level=warning_level,
            laps_remaining=laps_remaining
        )
    
    def get_all_predictions(self) -> Dict[str, PitPrediction]:
        """取得所有車手的當前預測"""
        predictions = {}
        for driver_code, laps in self.driver_laps.items():
            if laps:
                tire_saving = self.calculator.calculate_instant_score(laps)
                predictions[driver_code] = self._predict_pit(
                    driver_code, laps[-1], tire_saving
                )
        return predictions


# ============================================================================
# 批次驗證器 (用於歷史數據測試)
# ============================================================================

class RealTimeValidation:
    """即時預測驗證器 - 用歷史數據模擬 Live Timing"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
        self.base_path = Path(base_path)
        self.json_dir = self.base_path / "json"
        
        self.predictor = RealTimePitPredictor(base_path)
    
    def validate_race(self, year: int, race: str, session: str = "R") -> Dict[str, Any]:
        """
        驗證單場比賽的預測準確度
        
        模擬 Live Timing 的逐圈輸入
        """
        # 載入 F54 數據
        f54_path = self.json_dir / f"driver_throttle_ratio_{year}_{race}_{session}.json"
        if not f54_path.exists():
            raise FileNotFoundError(f"找不到 F54 數據: {f54_path}")
        
        with open(f54_path, "r", encoding="utf-8") as f:
            f54_data = json.load(f)
        
        drivers = f54_data.get("data", {}).get("analysis", {}).get("drivers", [])
        
        # 設定賽事
        self.predictor.set_race(race, session)
        
        # 收集驗證結果
        results = {
            "race": race,
            "year": year,
            "session": session,
            "total_stints": 0,
            "predictions": [],
            "accuracy_by_lap": {},  # lap -> accuracy stats
        }
        
        # 收集進站事件: driver -> [(stint, actual_pit_lap), ...]
        actual_pit_events = {}
        
        # 第一次遍歷: 收集實際進站時機
        for driver_data in drivers:
            driver_code = driver_data.get("driver_code")
            laps = driver_data.get("laps", [])
            
            current_stint = 0
            for lap_data in laps:
                lap_num = lap_data.get("lap_number", 0)
                stint = lap_data.get("stint", 1)
                
                # 檢測換胎 (stint 變化代表進站)
                if stint != current_stint and current_stint > 0:
                    # 上一圈是進站圈
                    actual_pit_lap = lap_num - 1
                    if driver_code not in actual_pit_events:
                        actual_pit_events[driver_code] = []
                    actual_pit_events[driver_code].append({
                        "stint": current_stint,
                        "actual_pit_lap": actual_pit_lap
                    })
                
                current_stint = stint
        
        # 準確率統計
        results["stint_validations"] = []  # 每個 stint 的預測 vs 實際
        results["prediction_errors"] = []  # 預測誤差
        
        # 第二次遍歷: 模擬逐圈輸入並記錄預測
        for driver_data in drivers:
            driver_code = driver_data.get("driver_code")
            laps = driver_data.get("laps", [])
            
            current_stint = 0
            stint_predictions = []  # 當前 stint 的所有預測
            
            for lap_data in laps:
                lap_num = lap_data.get("lap_number", 0)
                stint = lap_data.get("stint", 1)
                
                # 檢測換胎
                if stint != current_stint:
                    if current_stint > 0 and stint_predictions:
                        # 評估上一個 stint 的預測準確性
                        actual_pit = None
                        if driver_code in actual_pit_events:
                            for event in actual_pit_events[driver_code]:
                                if event["stint"] == current_stint:
                                    actual_pit = event["actual_pit_lap"]
                                    break
                        
                        if actual_pit:
                            # 取進站前 3 圈的預測來評估
                            late_predictions = [
                                p for p in stint_predictions 
                                if p["lap"] >= actual_pit - 3
                            ]
                            if late_predictions:
                                avg_predicted = sum(p["predicted_pit_lap"] for p in late_predictions) / len(late_predictions)
                                error = avg_predicted - actual_pit
                                
                                results["stint_validations"].append({
                                    "driver": driver_code,
                                    "stint": current_stint,
                                    "actual_pit_lap": actual_pit,
                                    "avg_predicted_pit": round(avg_predicted, 1),
                                    "error": round(error, 1),
                                    "late_pred_count": len(late_predictions)
                                })
                                results["prediction_errors"].append(error)
                    
                    current_stint = stint
                    stint_predictions = []
                    results["total_stints"] += 1
                
                # 模擬 Live Timing 輸入
                prediction = self.predictor.update_lap(
                    driver_code=driver_code,
                    lap_number=lap_num,
                    lap_time_s=lap_data.get("lap_time_seconds", 0),
                    coasting_s=lap_data.get("coasting_duration_s", 0),
                    full_throttle_ratio=lap_data.get("full_throttle_ratio", 0),
                    compound=lap_data.get("compound", "MEDIUM"),
                    tyre_life=lap_data.get("tyre_life", 1),
                    stint=stint,
                    sector_times=[
                        lap_data.get("sector1_time"),
                        lap_data.get("sector2_time"),
                        lap_data.get("sector3_time")
                    ]
                )
                
                # 記錄預測
                pred_record = {
                    "driver": driver_code,
                    "lap": lap_num,
                    "stint": stint,
                    "tyre_life": lap_data.get("tyre_life", 1),
                    "compound": lap_data.get("compound"),
                    "instant_score": prediction.tire_saving.instant_score,
                    "saving_level": prediction.tire_saving.saving_level,
                    "predicted_pit_lap": prediction.predicted_pit_lap,
                    "adjustment": prediction.current_adjustment,
                    "warning_level": prediction.warning_level,
                    "laps_remaining": prediction.laps_remaining
                }
                results["predictions"].append(pred_record)
                stint_predictions.append(pred_record)
        
        # 計算整體統計
        if results["prediction_errors"]:
            errors = results["prediction_errors"]
            results["accuracy_stats"] = {
                "total_validated_stints": len(errors),
                "mae": round(sum(abs(e) for e in errors) / len(errors), 2),
                "mean_error": round(sum(errors) / len(errors), 2),
                "early_predictions": sum(1 for e in errors if e < -2),  # 預測太早進站 (>2圈)
                "accurate_predictions": sum(1 for e in errors if abs(e) <= 2),  # 誤差 ≤ 2圈
                "late_predictions": sum(1 for e in errors if e > 2),  # 預測太晚進站 (>2圈)
            }
            
            # 計算準確率
            total = len(errors)
            accurate = results["accuracy_stats"]["accurate_predictions"]
            results["accuracy_stats"]["accuracy_pct"] = round(accurate / total * 100, 1)
        
        return results
    
    def print_validation_report(self, results: Dict[str, Any]):
        """印出驗證報告"""
        print()
        print("=" * 90)
        print(f"F87 Real-Time Pit Prediction Validation - {results['year']} {results['race']} {results['session']}")
        print("=" * 90)
        print()
        print(f"Total Stints Processed: {results['total_stints']}")
        print(f"Total Predictions Made: {len(results['predictions'])}")
        print()
        
        # 準確率統計
        if "accuracy_stats" in results:
            stats = results["accuracy_stats"]
            print("【預測準確率統計】")
            print("-" * 60)
            print(f"  Validated Stints:      {stats['total_validated_stints']}")
            print(f"  Mean Absolute Error:   {stats['mae']:.2f} laps")
            print(f"  Mean Error (bias):     {stats['mean_error']:+.2f} laps")
            print()
            print(f"  Early Predictions (>2 laps early):   {stats['early_predictions']}")
            print(f"  Accurate (within 2 laps):            {stats['accurate_predictions']}")
            print(f"  Late Predictions (>2 laps late):     {stats['late_predictions']}")
            print()
            print(f"  ACCURACY RATE: {stats['accuracy_pct']:.1f}%")
            print("-" * 60)
            print()
        
        # 顯示每個 stint 的預測 vs 實際
        if results.get("stint_validations"):
            print("【各 Stint 預測 vs 實際進站圈數】")
            print("-" * 80)
            print(f"{'Driver':<8} {'Stint':<6} {'Actual':<10} {'Predicted':<12} {'Error':<10} {'Result':<10}")
            print("-" * 80)
            
            for sv in sorted(results["stint_validations"], key=lambda x: (x["driver"], x["stint"])):
                error = sv["error"]
                if abs(error) <= 2:
                    result = "OK"
                elif error < 0:
                    result = "TOO EARLY"
                else:
                    result = "TOO LATE"
                
                print(f"{sv['driver']:<8} {sv['stint']:<6} {sv['actual_pit_lap']:<10} "
                      f"{sv['avg_predicted_pit']:<12.1f} {error:+.1f}{'':>5} {result:<10}")
            print()
        
        # 按車手顯示最後預測
        print("【各車手最終狀態】")
        print("-" * 80)
        print(f"{'Driver':<8} {'Lap':<6} {'Stint':<6} {'TyreLife':<10} {'Score':<8} {'Level':<12} {'Warning':<10}")
        print("-" * 80)
        
        # 取每車手最後一筆
        last_predictions = {}
        for pred in results["predictions"]:
            last_predictions[pred["driver"]] = pred
        
        for driver, pred in sorted(last_predictions.items()):
            print(f"{driver:<8} {pred['lap']:<6} {pred['stint']:<6} "
                  f"{pred['tyre_life']:<10} {pred['instant_score']:<8.1f} "
                  f"{pred['saving_level']:<12} {pred['warning_level']:<10}")
        
        print()
        print("=" * 90)


# ============================================================================
# 模組入口函數
# ============================================================================

def run_realtime_validation(
    year: int,
    race: str,
    session: str = "R",
    base_path: str = None
) -> Dict[str, Any]:
    """
    執行即時預測驗證
    
    Args:
        year: 年份
        race: 賽事名稱
        session: 會話類型
        base_path: 專案根目錄
        
    Returns:
        驗證結果字典
    """
    validator = RealTimeValidation(base_path)
    results = validator.validate_race(year, race, session)
    validator.print_validation_report(results)
    
    return {
        "success": True,
        "message": f"F87 即時驗證完成，共 {results['total_stints']} 個 stint",
        "function_id": "87",
        "data": results
    }


# ============================================================================
# 直接執行測試
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # 預設測試 Bahrain 2025
    year = 2025
    race = "Bahrain"
    session = "R"
    
    if len(sys.argv) > 1:
        race = sys.argv[1]
    if len(sys.argv) > 2:
        year = int(sys.argv[2])
    
    result = run_realtime_validation(year, race, session)
    print(f"\n成功: {result['success']}")
