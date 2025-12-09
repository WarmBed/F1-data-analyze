# -*- coding: utf-8 -*-
"""
Close Combat Predictor (F85)
============================

使用訓練好的模型預測近距離接觸機率 (0.2-0.3s)。

Author: F1T Team
Date: 2025-12-09
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np

try:
    import xgboost as xgb
except ImportError:
    xgb = None


@dataclass
class CloseCombatPrediction:
    """近距離接觸預測結果"""
    attacker: str
    defender: str
    probability: float      # 進入 0.2-0.3s 的機率 (0-1)
    confidence: str         # LOW/MEDIUM/HIGH
    key_factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'attacker': self.attacker,
            'defender': self.defender,
            'probability': round(self.probability, 4),
            'confidence': self.confidence,
            'key_factors': self.key_factors
        }


class CloseCombatPredictor:
    """
    F85: 近距離接觸預測器
    
    預測車手對進入 0.2-0.3s 近距離接觸的機率。
    
    Usage:
        predictor = CloseCombatPredictor()
        result = predictor.predict(
            gap_seconds=0.8,
            gap_trend_3lap=-0.15,
            ...
        )
        print(f"CC機率: {result.probability:.1%}")
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
        'gap_trend_3lap',
        'min_gap_last_5lap',
        'consecutive_catching_laps',
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
        """初始化預測器"""
        if xgb is None:
            raise ImportError("請安裝 xgboost: pip install xgboost")
        
        self.verbose = verbose
        self.model = None
        self.model_version = None
        
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
        
        models = list(model_dir.glob("close_combat_xgb_*.json"))
        if not models:
            return None
        
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
        """載入訓練好的模型"""
        try:
            model_path = Path(model_path)
            
            if not model_path.exists():
                if self.verbose:
                    print(f"[F85] 模型不存在: {model_path}")
                return False
            
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(model_path))
            
            # 提取版本號
            name = model_path.stem
            if '_v' in name:
                self.model_version = name.split('_v')[-1]
            else:
                self.model_version = "unknown"
            
            if self.verbose:
                print(f"[F85] 模型載入成功: close_combat_xgb_{self.model_version}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"[F85] 模型載入失敗: {e}")
            return False
    
    def predict(self,
                gap_seconds: float,
                gap_delta: float = 0.0,
                is_catching: bool = False,
                drs_available: bool = None,
                attacker_tyre: str = 'MEDIUM',
                defender_tyre: str = 'MEDIUM',
                tyre_age_diff: int = 0,
                track_status_green: bool = True,
                attacker_position: int = 5,
                race_progress: float = 0.5,
                gap_trend_3lap: float = 0.0,
                min_gap_last_5lap: float = None,
                consecutive_catching_laps: int = 0) -> CloseCombatPrediction:
        """
        預測近距離接觸機率
        
        Args:
            gap_seconds: 間距 (秒)
            gap_delta: 間距變化 (負值表示追近)
            is_catching: 是否追近中
            drs_available: DRS 可用 (None 則自動判斷)
            attacker_tyre: 進攻者輪胎
            defender_tyre: 防守者輪胎
            tyre_age_diff: 輪胎壽命差 (defender - attacker)
            track_status_green: 綠旗狀態
            attacker_position: 進攻者位置
            race_progress: 比賽進度 (0-1)
            gap_trend_3lap: 過去 3 圈的 gap 趨勢斜率
            min_gap_last_5lap: 過去 5 圈的最小 gap
            consecutive_catching_laps: 連續追近圈數
        
        Returns:
            CloseCombatPrediction 預測結果
        """
        if self.model is None:
            raise RuntimeError("模型尚未載入")
        
        # 自動判斷 DRS
        if drs_available is None:
            drs_available = gap_seconds < 1.0
        
        # 自動計算 min_gap_last_5lap
        if min_gap_last_5lap is None:
            min_gap_last_5lap = gap_seconds
        
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
            race_progress,
            gap_trend_3lap,
            min_gap_last_5lap,
            consecutive_catching_laps,
        ]])
        
        # 預測
        probability = self.model.predict_proba(features)[0][1]
        
        # 判斷信心等級
        if probability >= 0.75:
            confidence = "HIGH"
        elif probability >= 0.5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        # 分析關鍵因素
        key_factors = self._analyze_key_factors(
            gap_seconds, gap_delta, is_catching, drs_available,
            gap_trend_3lap, min_gap_last_5lap, consecutive_catching_laps,
            tyre_age_diff
        )
        
        return CloseCombatPrediction(
            attacker="",
            defender="",
            probability=probability,
            confidence=confidence,
            key_factors=key_factors
        )
    
    def _analyze_key_factors(self,
                             gap_seconds: float,
                             gap_delta: float,
                             is_catching: bool,
                             drs_available: bool,
                             gap_trend_3lap: float,
                             min_gap_last_5lap: float,
                             consecutive_catching_laps: int,
                             tyre_age_diff: int) -> List[str]:
        """分析關鍵因素"""
        factors = []
        
        # 持續追近趨勢
        if gap_trend_3lap < -0.15:
            factors.append("Strong catching trend (3 laps)")
        elif gap_trend_3lap < -0.05:
            factors.append("Moderate catching trend")
        
        # 連續追近
        if consecutive_catching_laps >= 3:
            factors.append(f"Consecutive catching ({consecutive_catching_laps} laps)")
        
        # 曾經很接近
        if min_gap_last_5lap < 0.5:
            factors.append(f"Very close recently ({min_gap_last_5lap:.2f}s)")
        
        # DRS 優勢
        if drs_available:
            factors.append("DRS zone")
        
        # 輪胎優勢
        if tyre_age_diff > 5:
            factors.append(f"Fresher tyres (+{tyre_age_diff} laps)")
        
        # 間距已經很近
        if gap_seconds < 1.0:
            factors.append("Already in striking distance")
        
        return factors


def run_f85_prediction(attacker: str = "VER",
                      defender: str = "LEC",
                      gap: float = 0.8,
                      gap_trend_3lap: float = -0.1,
                      consecutive_catching: int = 3,
                      tyre_diff: int = 0,
                      race_progress: float = 0.5,
                      verbose: bool = True) -> Dict[str, Any]:
    """
    執行 F85 近距離接觸預測 (CLI 調用)
    
    Args:
        attacker: 進攻者代碼
        defender: 防守者代碼
        gap: 間距 (秒)
        gap_trend_3lap: 3 圈趨勢
        consecutive_catching: 連續追近圈數
        tyre_diff: 輪胎年齡差
        race_progress: 比賽進度
        verbose: 顯示詳細輸出
    
    Returns:
        預測結果字典
    """
    try:
        predictor = CloseCombatPredictor(verbose=verbose)
        
        if predictor.model is None:
            return {
                "success": False,
                "message": "F85 模型未載入 (請先執行 -f 85 訓練模型)"
            }
        
        result = predictor.predict(
            gap_seconds=gap,
            gap_delta=-0.05,
            is_catching=True,
            gap_trend_3lap=gap_trend_3lap,
            consecutive_catching_laps=consecutive_catching,
            tyre_age_diff=tyre_diff,
            race_progress=race_progress
        )
        
        result.attacker = attacker
        result.defender = defender
        
        if verbose:
            print(f"\n進攻者: {attacker} vs 防守者: {defender}")
            print(f"Close Combat 機率: {result.probability:.1%}")
            print(f"信心等級: {result.confidence}")
            print(f"關鍵因素:")
            for factor in result.key_factors:
                print(f"  - {factor}")
        
        return {
            "success": True,
            "message": "F85 預測完成",
            "prediction": result.to_dict()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"預測失敗: {str(e)}",
            "error": str(e)
        }


def run_f86_prediction(
    attacker: str = "VER",
    defender: str = "LEC",
    gap: float = 0.8,
    gap_trend_3lap: float = -0.1,
    consecutive_catching: int = 3,
    tyre_diff: int = 0,
    race_progress: float = 0.5,
    version: int = 1,
    verbose: bool = True
) -> Dict:
    """
    F86: 近距離接觸預測器 CLI 接口
    
    Args:
        attacker: 進攻者代碼
        defender: 防守者代碼
        gap: 間距 (秒)
        gap_trend_3lap: 3 圈趨勢
        consecutive_catching: 連續追近圈數
        tyre_diff: 輪胎年齡差
        race_progress: 比賽進度
        version: 模型版本號
        verbose: 顯示詳細輸出
    
    Returns:
        預測結果字典
    """
    # F86 實際上是 F85 系統的推理引擎
    return run_f85_prediction(
        attacker=attacker,
        defender=defender,
        gap=gap,
        gap_trend_3lap=gap_trend_3lap,
        consecutive_catching=consecutive_catching,
        tyre_diff=tyre_diff,
        race_progress=race_progress,
        verbose=verbose
    )


if __name__ == "__main__":
    print("=" * 70)
    print("F85: Close Combat Predictor - Test")
    print("=" * 70)
    
    result = run_f85_prediction(
        attacker="VER",
        defender="HAM",
        gap=0.85,
        gap_trend_3lap=-0.12,
        consecutive_catching=4,
        tyre_diff=5,
        verbose=True
    )
    
    if not result['success']:
        print(f"\n[ERROR] {result['message']}")
