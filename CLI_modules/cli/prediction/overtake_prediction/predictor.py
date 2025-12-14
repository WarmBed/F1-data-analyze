#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F83: 超車預測器

即時預測超車發生的機率，用於 Live Timing 整合。

Features:
- 載入訓練好的 XGBoost 模型
- 即時預測超車機率
- 批次預測多個車手對
- 提供預測解釋

Author: F1T Team
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import xgboost as xgb
except ImportError:
    xgb = None


@dataclass
class OvertakePrediction:
    """超車預測結果"""
    attacker: str           # 進攻者車號
    defender: str           # 防守者車號
    probability: float      # 超車機率 (0-1)
    confidence: str         # 信心等級 (LOW/MEDIUM/HIGH)
    key_factors: List[str]  # 關鍵因素
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'attacker': self.attacker,
            'defender': self.defender,
            'probability': round(self.probability, 4),
            'confidence': self.confidence,
            'key_factors': self.key_factors
        }


class OvertakePredictor:
    """
    F83: 超車預測器
    
    用於即時預測超車機率的核心類別
    
    Usage:
        predictor = OvertakePredictor()
        result = predictor.predict(
            gap_seconds=0.8,
            tyre_age_diff=5,
            attacker_position=3,
            race_progress=0.6
        )
        print(f"超車機率: {result.probability:.1%}")
    """
    
    # 特徵列表 (必須與訓練時一致)
    FEATURE_COLUMNS = [
        'gap_seconds',
        'gap_delta',
        'is_catching',
        'drs_available',
        'attacker_tyre_compound',
        'defender_tyre_compound',
        'tyre_age_diff',
        'track_status_green',
        'attacker_position',
        'race_progress',
    ]
    
    # 輪胎編碼
    COMPOUND_ENCODING = {
        'SOFT': 0, 'S': 0,
        'MEDIUM': 1, 'M': 1,
        'HARD': 2, 'H': 2,
        'INTERMEDIATE': 3, 'I': 3,
        'WET': 4, 'W': 4
    }
    
    def __init__(self, model_path: str = None, verbose: bool = False):
        """
        初始化預測器
        
        Args:
            model_path: 模型檔案路徑 (預設使用最新版本)
            verbose: 是否顯示詳細輸出
        """
        if xgb is None:
            raise ImportError("請安裝 xgboost: pip install xgboost")
        
        self.verbose = verbose
        self.model = None
        self.model_version = None
        self.feature_importance = {}
        
        # 尋找模型路徑
        if model_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            model_dir = project_root / "models" / "overtake_prediction"
            model_path = self._find_latest_model(model_dir)
        
        if model_path:
            self.load_model(model_path)
    
    def _find_latest_model(self, model_dir: Path) -> Optional[Path]:
        """尋找最新版本的模型"""
        if not model_dir.exists():
            return None
        
        # 尋找所有模型檔案
        models = list(model_dir.glob("overtake_xgb_*.json"))
        if not models:
            return None
        
        # 按版本號排序
        def get_version(p):
            name = p.stem
            if '_v' in name:
                try:
                    return int(name.split('_v')[-1])
                except ValueError:
                    return 0
            return 0
        
        models.sort(key=get_version, reverse=True)
        return models[0]
    
    def load_model(self, model_path: str) -> bool:
        """
        載入訓練好的模型
        
        Args:
            model_path: 模型檔案路徑
            
        Returns:
            是否載入成功
        """
        try:
            model_path = Path(model_path)
            
            if not model_path.exists():
                if self.verbose:
                    print(f"[F83] 模型檔案不存在: {model_path}")
                return False
            
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(model_path))
            
            # 提取版本號
            name = model_path.stem
            if '_v' in name:
                self.model_version = name.split('_v')[-1]
            else:
                self.model_version = "unknown"
            
            # 載入特徵重要性
            importance_path = model_path.parent / f"feature_importance_v{self.model_version}.csv"
            if importance_path.exists():
                self._load_feature_importance(importance_path)
            
            if self.verbose:
                print(f"[F83] 模型載入成功: v{self.model_version}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"[F83] 模型載入失敗: {e}")
            return False
    
    def _load_feature_importance(self, path: Path):
        """載入特徵重要性"""
        try:
            import pandas as pd
            df = pd.read_csv(path)
            self.feature_importance = dict(zip(df['feature'], df['importance']))
        except Exception:
            pass
    
    def predict(self,
                gap_seconds: float,
                gap_delta: float = 0.0,
                is_catching: bool = True,
                drs_available: bool = None,
                attacker_tyre: str = 'MEDIUM',
                defender_tyre: str = 'MEDIUM',
                tyre_age_diff: int = 0,
                track_status_green: bool = True,
                attacker_position: int = 5,
                race_progress: float = 0.5) -> OvertakePrediction:
        """
        預測單次超車機率
        
        Args:
            gap_seconds: 間距 (秒)
            gap_delta: 間距變化 (負值表示追近)
            is_catching: 是否追近中
            drs_available: DRS 可用 (None 則自動判斷)
            attacker_tyre: 進攻者輪胎 (SOFT/MEDIUM/HARD)
            defender_tyre: 防守者輪胎
            tyre_age_diff: 輪胎壽命差 (defender - attacker)
            track_status_green: 綠旗狀態
            attacker_position: 進攻者位置
            race_progress: 比賽進度 (0-1)
            
        Returns:
            OvertakePrediction 預測結果
        """
        if self.model is None:
            raise RuntimeError("模型尚未載入")
        
        # 自動判斷 DRS
        if drs_available is None:
            drs_available = gap_seconds < 1.0
        
        # 編碼輪胎
        attacker_compound = self.COMPOUND_ENCODING.get(attacker_tyre.upper(), 1)
        defender_compound = self.COMPOUND_ENCODING.get(defender_tyre.upper(), 1)
        
        # 建立特徵向量
        features = np.array([[
            gap_seconds,
            gap_delta,
            1 if is_catching else 0,
            1 if drs_available else 0,
            attacker_compound,
            defender_compound,
            tyre_age_diff,
            1 if track_status_green else 0,
            attacker_position,
            race_progress
        ]])
        
        # 預測
        probability = self.model.predict_proba(features)[0][1]
        
        # 判斷信心等級
        if probability >= 0.7:
            confidence = "HIGH"
        elif probability >= 0.4:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        # 分析關鍵因素
        key_factors = self._analyze_key_factors(
            gap_seconds, gap_delta, is_catching, drs_available,
            attacker_tyre, defender_tyre, tyre_age_diff,
            track_status_green, attacker_position, race_progress
        )
        
        return OvertakePrediction(
            attacker="",
            defender="",
            probability=probability,
            confidence=confidence,
            key_factors=key_factors
        )
    
    def predict_pair(self,
                     attacker: str,
                     defender: str,
                     attacker_state: Dict[str, Any],
                     defender_state: Dict[str, Any],
                     race_state: Dict[str, Any]) -> OvertakePrediction:
        """
        預測車手對的超車機率
        
        Args:
            attacker: 進攻者車號
            defender: 防守者車號
            attacker_state: 進攻者狀態 {position, tyre_compound, tyre_age, gap}
            defender_state: 防守者狀態 {position, tyre_compound, tyre_age}
            race_state: 比賽狀態 {current_lap, total_laps, track_status}
            
        Returns:
            OvertakePrediction
        """
        # 提取特徵
        gap = attacker_state.get('gap', 2.0)
        gap_delta = attacker_state.get('gap_delta', 0.0)
        is_catching = gap_delta < 0
        
        attacker_tyre = attacker_state.get('tyre_compound', 'MEDIUM')
        defender_tyre = defender_state.get('tyre_compound', 'MEDIUM')
        tyre_age_diff = defender_state.get('tyre_age', 0) - attacker_state.get('tyre_age', 0)
        
        current_lap = race_state.get('current_lap', 1)
        total_laps = race_state.get('total_laps', 50)
        race_progress = current_lap / total_laps if total_laps > 0 else 0.5
        
        track_status = race_state.get('track_status', 'GREEN')
        track_status_green = track_status.upper() == 'GREEN'
        
        # 預測
        result = self.predict(
            gap_seconds=gap,
            gap_delta=gap_delta,
            is_catching=is_catching,
            attacker_tyre=attacker_tyre,
            defender_tyre=defender_tyre,
            tyre_age_diff=tyre_age_diff,
            track_status_green=track_status_green,
            attacker_position=attacker_state.get('position', 5),
            race_progress=race_progress
        )
        
        # 設定車手資訊
        result.attacker = attacker
        result.defender = defender
        
        return result
    
    def predict_all_pairs(self,
                          drivers: Dict[str, Dict[str, Any]],
                          race_state: Dict[str, Any],
                          max_gap: float = 2.0) -> List[OvertakePrediction]:
        """
        預測所有潛在超車對
        
        Args:
            drivers: 所有車手狀態 {driver_num: {position, gap, tyre_compound, tyre_age}}
            race_state: 比賽狀態
            max_gap: 最大間距閾值 (秒)
            
        Returns:
            按機率排序的預測列表
        """
        predictions = []
        
        # 按位置排序
        sorted_drivers = sorted(
            [(num, state) for num, state in drivers.items()],
            key=lambda x: x[1].get('position', 99)
        )
        
        # 預測相鄰車手對
        for i in range(1, len(sorted_drivers)):
            attacker_num, attacker_state = sorted_drivers[i]
            defender_num, defender_state = sorted_drivers[i-1]
            
            gap = attacker_state.get('gap', 999)
            
            if gap <= max_gap:
                pred = self.predict_pair(
                    attacker=attacker_num,
                    defender=defender_num,
                    attacker_state=attacker_state,
                    defender_state=defender_state,
                    race_state=race_state
                )
                predictions.append(pred)
        
        # 按機率排序
        predictions.sort(key=lambda x: x.probability, reverse=True)
        
        return predictions
    
    def _analyze_key_factors(self,
                             gap_seconds: float,
                             gap_delta: float,
                             is_catching: bool,
                             drs_available: bool,
                             attacker_tyre: str,
                             defender_tyre: str,
                             tyre_age_diff: int,
                             track_status_green: bool,
                             attacker_position: int,
                             race_progress: float) -> List[str]:
        """分析關鍵因素"""
        factors = []
        
        # DRS 優勢
        if drs_available:
            factors.append("DRS zone available")
        
        # 輪胎優勢
        if tyre_age_diff > 5:
            factors.append(f"Fresher tyres (+{tyre_age_diff} laps)")
        elif tyre_age_diff < -5:
            factors.append(f"Older tyres ({tyre_age_diff} laps)")
        
        # 輪胎類型優勢
        attacker_soft = attacker_tyre.upper() in ['SOFT', 'S']
        defender_hard = defender_tyre.upper() in ['HARD', 'H']
        if attacker_soft and defender_hard:
            factors.append("Softer compound advantage")
        
        # 追近趨勢
        if is_catching and gap_delta < -0.2:
            factors.append("Rapidly closing gap")
        elif gap_delta > 0.2:
            factors.append("Gap increasing")
        
        # 間距
        if gap_seconds < 0.5:
            factors.append("Very close proximity")
        elif gap_seconds < 1.0:
            factors.append("DRS range")
        
        # 位置因素
        if attacker_position <= 3:
            factors.append("Fighting for podium")
        
        # 比賽階段
        if race_progress > 0.8:
            factors.append("Final stint pressure")
        
        # 非綠旗
        if not track_status_green:
            factors.append("Caution period (limited overtaking)")
        
        return factors[:5]  # 最多返回 5 個因素
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型資訊"""
        return {
            'version': self.model_version,
            'loaded': self.model is not None,
            'feature_columns': self.FEATURE_COLUMNS,
            'feature_importance': self.feature_importance
        }


# ============================================================================
# CLI 入口點
# ============================================================================
def run_f83_prediction(attacker: str = None,
                       defender: str = None,
                       gap: float = 1.0,
                       tyre_diff: int = 0,
                       race_progress: float = 0.5,
                       verbose: bool = True) -> Dict[str, Any]:
    """
    執行 F83 超車預測
    
    Args:
        attacker: 進攻者
        defender: 防守者
        gap: 間距 (秒)
        tyre_diff: 輪胎壽命差
        race_progress: 比賽進度
        verbose: 詳細輸出
        
    Returns:
        預測結果
    """
    print("=" * 70)
    print("F83: 超車預測器")
    print("=" * 70)
    
    predictor = OvertakePredictor(verbose=verbose)
    
    if predictor.model is None:
        return {
            'success': False,
            'message': '模型載入失敗，請先執行 F82 訓練模型'
        }
    
    # 執行預測
    result = predictor.predict(
        gap_seconds=gap,
        tyre_age_diff=tyre_diff,
        race_progress=race_progress
    )
    
    if attacker:
        result.attacker = attacker
    if defender:
        result.defender = defender
    
    print(f"\n預測結果:")
    print(f"  超車機率: {result.probability:.1%}")
    print(f"  信心等級: {result.confidence}")
    print(f"  關鍵因素:")
    for factor in result.key_factors:
        print(f"    - {factor}")
    
    return {
        'success': True,
        'prediction': result.to_dict(),
        'model_version': predictor.model_version
    }


if __name__ == "__main__":
    # 測試預測
    run_f83_prediction(
        attacker="VER",
        defender="LEC",
        gap=0.8,
        tyre_diff=5,
        race_progress=0.6
    )
