"""
Overtake Calculator - 超車判定計算器

整合 F138 超車成功率模型，用於模擬中的超車判定。

特性:
- 使用訓練好的 Logistic Regression 模型
- 結合賽道難度、車隊性能、車手係數
- DRS 和輪胎狀態影響
- Monte Carlo 隨機判定
"""

import json
import pickle
import random
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List


@dataclass
class CarState:
    """車輛狀態"""
    driver: str
    team: str
    position: int  # 當前位置 (1-20)
    position_m: float  # 賽道位置 (米)
    lap_number: int
    tyre_compound: str  # "S", "M", "H"
    tyre_age_laps: int
    gap_ahead_s: float  # 與前車的間距 (秒)
    gap_behind_s: float  # 與後車的間距 (秒)
    drs_active: bool = False
    is_in_pit: bool = False
    is_out_lap: bool = False


@dataclass
class OvertakeAttempt:
    """超車嘗試記錄"""
    lap: int
    race_time_s: float
    attacker: str
    defender: str
    attacker_team: str
    defender_team: str
    track_position_m: float
    success_probability: float
    drs_active: bool
    tyre_age_delta: int
    success: bool  # 是否成功


class OvertakeCalculator:
    """
    超車判定計算器
    
    整合 F138 訓練的模型和所有係數數據
    """
    
    # 超車嘗試的最小間距閾值 (秒)
    MIN_GAP_FOR_ATTEMPT = 1.0
    
    # DRS 區域內的額外成功率加成 (提高以符合現實)
    DRS_BONUS = 0.30  # DRS 可增加 30% 相對成功率
    
    # 輪胎圈數差的影響係數
    TYRE_AGE_COEFFICIENT = 0.01  # 每圈差 1% 成功率
    
    # 賽道名稱映射 (用於處理不同格式的賽道名稱)
    TRACK_NAME_ALIASES = {
        "Japan": "Japanese",
        "Japanese": "Japanese",
        "Saudi Arabia": "Saudi Arabian",
        "Great Britain": "British",
        "United States": "United States",
        "Abu Dhabi": "Abu Dhabi",
        "Netherlands": "Dutch",
        "Mexico": "Mexico City",
        "Australia": "Australian",
        "China": "Chinese",
        "Spain": "Spanish",
        "Canada": "Canadian",
        "Austria": "Austrian",
        "Hungary": "Hungarian",
        "Belgium": "Belgian",
        "Italy": "Italian",
        "Brazil": "São Paulo",
    }
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.json_dir = self.base_dir / "json"
        self.models_dir = self.base_dir / "models"
        
        # 載入的數據
        self.track_difficulty: Dict[str, float] = {}
        self.team_attack_rates: Dict[str, float] = {}
        self.team_defense_rates: Dict[str, float] = {}
        self.driver_coefficients: Dict[str, Dict] = {}
        
        # F138 模型
        self.model = None
        self.scaler = None
        self.model_coefficients: Dict[str, float] = {}
        
        # 全場平均值 (fallback)
        self.global_attack_rate = 0.12  # 12% 預設
        self.global_defense_rate = 0.88  # 88% 預設
        
        # 載入所有數據
        self._load_all_data()
        
    def _normalize_track_name(self, track_name: str) -> str:
        """正規化賽道名稱"""
        return self.TRACK_NAME_ALIASES.get(track_name, track_name)
        
    def _load_all_data(self) -> None:
        """載入所有必要數據"""
        self._load_track_difficulty()
        self._load_team_performance()
        self._load_driver_coefficients()
        self._load_model()
        
    def _load_track_difficulty(self) -> None:
        """從 F136 載入賽道難度係數"""
        path = self.json_dir / "track_overtake_difficulty.json"
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for track, info in data.get("tracks", {}).items():
                    self.track_difficulty[track] = info.get("difficulty_coefficient", 0.5)
                print(f"[OvertakeCalculator] 載入 {len(self.track_difficulty)} 個賽道難度")
            except Exception as e:
                print(f"[OvertakeCalculator] 載入賽道難度失敗: {e}")
                
    def _load_team_performance(self) -> None:
        """從 F137 載入車隊性能矩陣"""
        path = self.json_dir / "team_performance_matrix.json"
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for team, stats in data.get("team_stats", {}).items():
                    self.team_attack_rates[team] = stats.get("attack_success_rate", 0.12)
                    self.team_defense_rates[team] = stats.get("defense_success_rate", 0.88)
                print(f"[OvertakeCalculator] 載入 {len(self.team_attack_rates)} 個車隊性能")
            except Exception as e:
                print(f"[OvertakeCalculator] 載入車隊性能失敗: {e}")
                
    def _load_driver_coefficients(self) -> None:
        """從 F139 載入車手係數"""
        path = self.json_dir / "driver_coefficients_complete.json"
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 更新全場平均
                global_stats = data.get("global_stats", {})
                self.global_attack_rate = global_stats.get("avg_attack_success_rate", 0.12)
                self.global_defense_rate = global_stats.get("avg_defense_success_rate", 0.88)
                
                # 載入車手係數
                self.driver_coefficients = data.get("drivers", {})
                print(f"[OvertakeCalculator] 載入 {len(self.driver_coefficients)} 個車手係數")
            except Exception as e:
                print(f"[OvertakeCalculator] 載入車手係數失敗: {e}")
                
    def _load_model(self) -> None:
        """載入 F138 訓練的模型"""
        model_path = self.models_dir / "overtake_success_model.pkl"
        scaler_path = self.models_dir / "overtake_feature_scaler.pkl"
        coef_path = self.json_dir / "overtake_model_coefficients.json"
        
        # 載入模型
        if model_path.exists():
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print("[OvertakeCalculator] 載入超車模型成功")
            except Exception as e:
                print(f"[OvertakeCalculator] 載入模型失敗: {e}")
                
        # 載入 scaler
        if scaler_path.exists():
            try:
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            except Exception as e:
                print(f"[OvertakeCalculator] 載入 scaler 失敗: {e}")
                
        # 載入係數 (用於 fallback)
        if coef_path.exists():
            try:
                with open(coef_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.model_coefficients = data.get("coefficients", {})
            except Exception as e:
                print(f"[OvertakeCalculator] 載入係數失敗: {e}")
                
    def can_attempt_overtake(self, attacker: CarState, defender: CarState) -> bool:
        """
        檢查是否可以嘗試超車
        
        條件:
        1. 間距小於閾值
        2. 不在維修站
        3. 不是出站圈
        """
        if attacker.is_in_pit or defender.is_in_pit:
            return False
        if attacker.is_out_lap:
            return False
        if attacker.gap_ahead_s > self.MIN_GAP_FOR_ATTEMPT:
            return False
        return True
        
    def calculate_success_probability(
        self,
        attacker: CarState,
        defender: CarState,
        track_name: str
    ) -> float:
        """
        計算超車成功機率
        
        注意：暫時使用 fallback 計算而非 ML 模型
        因為模型的訓練數據有選擇偏差 (DRS 區嘗試次數多導致統計失真)
        """
        # 獲取賽道難度 (標準化的名稱查找)
        normalized_name = self._normalize_track_name(track_name)
        track_diff = self.track_difficulty.get(normalized_name, 0.5)
        
        # 獲取車隊係數
        attacker_team_attack = self.team_attack_rates.get(
            attacker.team, self.global_attack_rate
        )
        defender_team_defense = self.team_defense_rates.get(
            defender.team, self.global_defense_rate
        )
        
        # 獲取車手係數
        attacker_coef = self.driver_coefficients.get(attacker.driver, {})
        defender_coef = self.driver_coefficients.get(defender.driver, {})
        
        attacker_attack_rate = attacker_coef.get(
            "attack_success_rate", self.global_attack_rate
        )
        defender_defense_rate = defender_coef.get(
            "defense_success_rate", self.global_defense_rate
        )
        
        # 輪胎圈數差 (負數 = 攻擊方輪胎更新)
        tyre_delta = defender.tyre_age_laps - attacker.tyre_age_laps
        
        # DRS 狀態
        drs_active = 1.0 if attacker.drs_active else 0.0
        
        # 使用 fallback 計算 (ML 模型暫時禁用)
        # TODO: 修正訓練數據的選擇偏差後重新啟用模型
                
        # Fallback: 簡化計算
        return self._fallback_probability(
            track_diff,
            attacker_team_attack,
            defender_team_defense,
            attacker_attack_rate,
            defender_defense_rate,
            tyre_delta,
            drs_active
        )
        
    def _fallback_probability(
        self,
        track_diff: float,
        team_attack: float,
        team_defense: float,
        driver_attack: float,
        driver_defense: float,
        tyre_delta: int,
        drs_active: float
    ) -> float:
        """
        Fallback 機率計算
        
        使用調整後的公式，基於真實超車成功率 (~12%)
        """
        # 基礎成功率 (全場平均)
        base_prob = self.global_attack_rate  # ~12%
        
        # 賽道難度影響 (0=容易, 1=困難)
        # 使用較溫和的調整: 難度 0.5 = 無影響, 難度 1.0 = -50%
        track_factor = 1.0 - (track_diff - 0.5) * 0.5  # 0.75 to 1.25
        
        # 車隊因素: 攻擊方車隊攻擊能力 / 全場平均
        team_attack_factor = team_attack / self.global_attack_rate if self.global_attack_rate > 0 else 1.0
        # 車隊因素: 防守方車隊防守能力 / 全場平均 (越高越難超車)
        team_defense_factor = self.global_defense_rate / team_defense if team_defense > 0 else 1.0
        
        # 車手因素: 使用係數 (相對於全場平均)
        attacker_factor = driver_attack / self.global_attack_rate if self.global_attack_rate > 0 else 1.0
        defender_factor = self.global_defense_rate / driver_defense if driver_defense > 0 else 1.0
        
        # 輪胎因素 (每圈差增加 1% 成功率)
        tyre_factor = 1.0 + tyre_delta * self.TYRE_AGE_COEFFICIENT
        tyre_factor = max(0.5, min(1.5, tyre_factor))  # 限制範圍
        
        # DRS 加成 (提供約 30% 額外成功率)
        drs_factor = 1.0 + drs_active * self.DRS_BONUS
        
        # 組合: 使用加權平均而非純乘法
        # 這樣可以避免多個因素相乘導致極端值
        combined_factor = (
            track_factor * 0.25 +
            team_attack_factor * 0.15 +
            team_defense_factor * 0.15 +
            attacker_factor * 0.15 +
            defender_factor * 0.15 +
            tyre_factor * 0.05 +
            drs_factor * 0.10
        )
        
        # 最終機率
        probability = base_prob * combined_factor
        
        # 限制在合理範圍 (5% - 35%)
        return max(0.05, min(0.35, probability))
        
    def attempt_overtake(
        self,
        attacker: CarState,
        defender: CarState,
        track_name: str,
        lap: int,
        race_time_s: float
    ) -> Tuple[bool, OvertakeAttempt]:
        """
        執行超車嘗試
        
        返回 (成功與否, 超車記錄)
        """
        probability = self.calculate_success_probability(
            attacker, defender, track_name
        )
        
        # Monte Carlo 隨機判定
        success = random.random() < probability
        
        attempt = OvertakeAttempt(
            lap=lap,
            race_time_s=race_time_s,
            attacker=attacker.driver,
            defender=defender.driver,
            attacker_team=attacker.team,
            defender_team=defender.team,
            track_position_m=attacker.position_m,
            success_probability=probability,
            drs_active=attacker.drs_active,
            tyre_age_delta=defender.tyre_age_laps - attacker.tyre_age_laps,
            success=success
        )
        
        return success, attempt
        
    def get_driver_overtake_skill(self, driver: str) -> Dict[str, float]:
        """
        獲取車手的超車能力係數
        
        返回 attack_coefficient 和 defense_coefficient
        """
        coef = self.driver_coefficients.get(driver, {})
        return {
            "attack_coefficient": coef.get("attack_coefficient", 1.0),
            "defense_coefficient": coef.get("defense_coefficient", 1.0),
            "attack_success_rate": coef.get("attack_success_rate", self.global_attack_rate),
            "defense_success_rate": coef.get("defense_success_rate", self.global_defense_rate)
        }
        
    def get_team_performance(self, team: str) -> Dict[str, float]:
        """獲取車隊的超車/防守性能"""
        return {
            "attack_success_rate": self.team_attack_rates.get(team, self.global_attack_rate),
            "defense_success_rate": self.team_defense_rates.get(team, self.global_defense_rate)
        }


# 全局實例
_calculator: Optional[OvertakeCalculator] = None

def get_overtake_calculator() -> OvertakeCalculator:
    """獲取全局 OvertakeCalculator 實例"""
    global _calculator
    if _calculator is None:
        _calculator = OvertakeCalculator()
    return _calculator
