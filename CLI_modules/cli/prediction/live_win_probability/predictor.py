"""
Live Win Probability Predictor - GUI 整合模組 (v3.4 Dynamic Strategy)

提供即時勝率預測功能，用於 Live Demo GUI 整合。

v3.4 更新 (2025-12-01):
- **訓練賽道難度**: 使用 2023-2024 數據計算 (analyze_circuit_overtake_v2.py)
- **輪胎策略因子**: TyreStrategyCalculator - 計算輪胎優勢/劣勢
- **進站時間因子**: PitStopCalculator - 評估進站對勝率的影響
- **綜合調整因子**: quality * circuit_affinity * fp3q_factor * tyre_advantage

v3.3 更新 (2025-12-01):
- **動態 Q 補償**: 只在前 10 圈有效，被超車則歸零
- **賽道權重**: Monaco (0.76) 難超車, Monza (0.44) 易超車
- **Sinkhorn-Knopp 雙隨機矩陣**: 確保機率約束正確
- 基於 2023-2024 統計: Q Position 相關性 0.6737, 桿位勝率 58.7%

v3.2 更新 (2025-12-01):
- 新增 FP3/Q 補償因子 (FP3QCompensationCalculator 類)
- 收集 2023-2024 FP3/Q 數據 (919 筆記錄)

v3.1 更新 (2025-11-29):
- 新增 SHAP 可解釋性功能 (SHAPExplainer 類)
- 新增賽道適應性因子 (CircuitAffinityCalculator 類)

v3.0 重大更新 (2025-11-27):
- 基於學術研究 (arXiv:2508.00200) 的專業預測架構
- 動態機率計算，考慮 gap_to_leader、laps_remaining 等因素

使用方法:
```python
predictor = LiveWinProbabilityPredictor()
predictor.load_model("models/win_probability_xgb_v2.pkl")

# v3.4: 設置排位結果和賽道
predictor.set_qualifying_positions({'VER': 1, 'LEC': 2, 'NOR': 3, ...})
predictor.set_circuit("Monaco")  # 影響 Q 補償權重 (0.76)

# 每圈調用 - 動態計算:
# - Q 補償: Lap 1-10 有效，被超車歸零，賽道權重
# - 輪胎優勢: 新軟胎 vs 舊硬胎
# - 進站影響: undercut/overcut 策略
probabilities = predictor.predict_for_snapshot(snapshot, tyre_state, race_info)
```

作者: F1T Dev Team
日期: 2025-12-01
參考: 
- arXiv:2508.00200 - "Predicting Formula 1 Race Outcomes"
- IEEE MELECON 2025 - "F1 Race Winner Prediction Using RF and SHAP Analysis"
"""

import os
import pickle
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

import numpy as np

# SHAP 可選導入 (避免強制依賴)
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# 賽道適應性計算器 (v3.1 新增)
# ============================================================================

# 車手在各賽道的適應性因子 (基於 2020-2024 歷史數據)
# 值 > 1.0 表示該車手在此賽道表現優於平均
# 值 < 1.0 表示該車手在此賽道表現劣於平均
DRIVER_CIRCUIT_AFFINITY = {
    "VER": {
        "Monaco": 0.85,       # 街道賽相對較弱 (2022 P3, 2023 P1, 2024 P6)
        "Singapore": 0.90,    # 街道賽
        "Baku": 0.88,         # 街道賽
        "Jeddah": 0.92,       # 街道賽
        "Las Vegas": 0.95,
        "Monza": 1.05,        # 高速賽道
        "Spa": 1.25,          # 雨戰專家 (2021-2024 統治)
        "Suzuka": 1.20,       # 技術賽道 (2022 冠, 2023 冠, 2024 冠)
        "Silverstone": 1.10,
        "Hungary": 1.15,      # 技術賽道
        "Mexico": 1.20,       # 高海拔優勢
        "Brazil": 1.15,       # 雨戰優勢
        "Abu Dhabi": 1.10,
        "Bahrain": 1.10,
        "Australia": 1.05,
        "Canada": 1.05,
        "Austria": 1.15,      # 主場優勢
        "Netherlands": 1.30,  # 絕對主場 (2021-2024 全冠)
        "USA": 1.05,
        "Qatar": 1.10,
        "default": 1.05,
    },
    "LEC": {
        "Monaco": 1.35,       # 街道賽專家 + 主場 (雖然多次失利但速度頂尖)
        "Singapore": 1.20,    # 街道賽專家 (2022 冠)
        "Baku": 1.15,         # 街道賽
        "Jeddah": 1.10,
        "Las Vegas": 1.05,
        "Monza": 1.15,        # 主場 (2019 冠, 2024 冠)
        "Spa": 0.90,          # 2022 引擎爆炸陰影
        "Suzuka": 0.95,
        "Silverstone": 1.00,
        "Hungary": 1.05,
        "Mexico": 0.95,
        "Brazil": 0.95,
        "Abu Dhabi": 1.00,
        "Bahrain": 1.10,      # 2022 冠
        "Australia": 1.10,    # 2022 冠, 2024 冠
        "Canada": 0.90,
        "Austria": 1.05,      # 2022 冠
        "Netherlands": 0.90,
        "USA": 1.05,          # 2023 冠
        "Qatar": 0.95,
        "default": 1.00,
    },
    "NOR": {
        "Monaco": 1.20,       # 街道賽強
        "Singapore": 1.15,
        "Baku": 1.05,
        "Jeddah": 1.00,
        "Las Vegas": 1.00,
        "Monza": 1.05,
        "Spa": 1.00,
        "Suzuka": 1.05,
        "Silverstone": 1.10,  # 主場優勢
        "Hungary": 1.15,      # 2024 冠
        "Mexico": 1.00,
        "Brazil": 1.05,
        "Abu Dhabi": 1.10,    # 2024 冠
        "Bahrain": 0.95,
        "Australia": 1.00,
        "Canada": 1.00,
        "Austria": 1.00,
        "Netherlands": 1.10,  # 2024 冠
        "USA": 1.05,
        "Qatar": 1.05,
        "Miami": 1.15,        # 2024 冠
        "default": 1.00,
    },
    "HAM": {
        "Monaco": 0.95,       # 困難賽道
        "Singapore": 1.10,    # 2017-2018 統治
        "Baku": 1.00,
        "Jeddah": 1.05,
        "Las Vegas": 1.05,
        "Monza": 1.10,
        "Spa": 1.15,          # 多次勝利
        "Suzuka": 1.05,
        "Silverstone": 1.25,  # 主場 (8 冠紀錄)
        "Hungary": 1.20,      # 歷史統治
        "Mexico": 1.10,
        "Brazil": 1.20,       # 傳奇比賽
        "Abu Dhabi": 1.05,
        "Bahrain": 1.10,
        "Australia": 1.05,
        "Canada": 1.20,       # 歷史統治
        "Austria": 0.95,
        "Netherlands": 0.90,
        "USA": 1.10,
        "Qatar": 1.05,
        "default": 1.05,
    },
    "SAI": {
        "Monaco": 1.10,
        "Singapore": 1.20,    # 2023 冠
        "Baku": 1.00,
        "Jeddah": 1.05,
        "Las Vegas": 1.00,
        "Monza": 1.05,
        "Spa": 0.95,
        "Suzuka": 1.00,
        "Silverstone": 1.15,  # 2022 冠
        "Hungary": 0.95,
        "Mexico": 1.10,       # 2024 冠
        "Brazil": 0.95,
        "Abu Dhabi": 1.00,
        "Bahrain": 0.95,
        "Australia": 1.15,    # 2024 冠
        "Canada": 1.00,
        "Austria": 1.00,
        "Netherlands": 0.95,
        "USA": 1.00,
        "Qatar": 0.95,
        "default": 1.00,
    },
    "RUS": {
        "Monaco": 0.90,
        "Singapore": 1.00,
        "Baku": 1.00,
        "Jeddah": 1.00,
        "Las Vegas": 1.15,    # 2024 冠
        "Monza": 1.00,
        "Spa": 1.10,          # 2024 冠
        "Suzuka": 1.00,
        "Silverstone": 1.05,
        "Hungary": 1.00,
        "Mexico": 0.95,
        "Brazil": 1.10,       # 2022 冠
        "Abu Dhabi": 1.05,
        "Bahrain": 0.95,
        "Australia": 1.00,
        "Canada": 0.95,
        "Austria": 1.10,      # 2024 冠
        "Netherlands": 0.95,
        "USA": 0.95,
        "Qatar": 0.95,
        "default": 1.00,
    },
    "PIA": {
        "Monaco": 1.05,
        "Singapore": 1.00,
        "Baku": 1.05,
        "Jeddah": 1.00,
        "Las Vegas": 1.00,
        "Monza": 1.00,
        "Spa": 1.00,
        "Suzuka": 1.00,
        "Silverstone": 1.10,  # 2024 冠
        "Hungary": 1.15,      # 2024 冠
        "Mexico": 1.00,
        "Brazil": 1.10,
        "Abu Dhabi": 1.05,
        "Bahrain": 1.00,
        "Australia": 1.00,
        "Canada": 1.00,
        "Austria": 1.00,
        "Netherlands": 1.00,
        "USA": 1.00,
        "Qatar": 1.05,        # 2024 Sprint 冠
        "default": 1.00,
    },
    "ALO": {
        "Monaco": 1.15,       # 街道賽經驗
        "Singapore": 1.10,    # 2023 經典防守
        "Baku": 1.05,
        "Jeddah": 1.10,       # 2023 P2
        "Las Vegas": 0.95,
        "Monza": 1.00,
        "Spa": 1.05,
        "Suzuka": 1.00,
        "Silverstone": 1.00,
        "Hungary": 1.05,
        "Mexico": 1.00,
        "Brazil": 1.00,
        "Abu Dhabi": 1.00,
        "Bahrain": 1.10,      # 2023 P3
        "Australia": 1.00,
        "Canada": 1.10,       # 2023 P2
        "Austria": 0.95,
        "Netherlands": 0.90,
        "USA": 1.00,
        "Qatar": 0.95,
        "default": 1.00,
    },
    "PER": {
        "Monaco": 1.25,       # 2022 冠, 街道賽專家
        "Singapore": 1.20,    # 2022 冠
        "Baku": 1.25,         # 2021 冠, 2023 冠
        "Jeddah": 1.15,       # 2023 冠
        "Las Vegas": 0.90,
        "Monza": 0.85,        # 高速賽道弱
        "Spa": 0.85,
        "Suzuka": 0.90,
        "Silverstone": 0.90,
        "Hungary": 0.85,
        "Mexico": 1.10,       # 主場
        "Brazil": 0.95,
        "Abu Dhabi": 1.00,
        "Bahrain": 1.00,
        "Australia": 0.95,
        "Canada": 0.95,
        "Austria": 0.95,
        "Netherlands": 0.90,
        "USA": 0.95,
        "Qatar": 0.90,
        "Miami": 1.10,        # 2023 冠
        "default": 0.95,
    },
    "GAS": {
        "Monaco": 1.10,
        "Singapore": 1.05,
        "Baku": 1.00,
        "Jeddah": 1.00,
        "Las Vegas": 1.00,
        "Monza": 1.10,        # 2020 冠
        "Spa": 1.00,
        "Suzuka": 1.00,
        "Silverstone": 1.00,
        "Hungary": 1.00,
        "Mexico": 1.00,
        "Brazil": 0.95,
        "Abu Dhabi": 1.00,
        "Bahrain": 1.00,
        "Australia": 0.95,
        "Canada": 1.00,
        "Austria": 1.00,
        "Netherlands": 1.05,
        "USA": 1.00,
        "Qatar": 1.00,
        "default": 1.00,
    },
}

# 賽道類型分類
CIRCUIT_TYPES = {
    "Monaco": "street",
    "Singapore": "street",
    "Baku": "street",
    "Jeddah": "street",
    "Las Vegas": "street",
    "Monza": "high_speed",
    "Spa": "high_speed",
    "Silverstone": "high_speed",
    "Suzuka": "technical",
    "Hungary": "technical",
    "Mexico": "high_altitude",
    "Brazil": "mixed",
    "Abu Dhabi": "mixed",
    "Bahrain": "mixed",
    "Australia": "mixed",
    "Canada": "mixed",
    "Austria": "high_speed",
    "Netherlands": "technical",
    "USA": "technical",
    "Qatar": "high_speed",
    "Miami": "mixed",
}


@dataclass
class CircuitAffinityConfig:
    """賽道適應性計算配置"""
    # 預設適應性值 (用於未知車手/賽道)
    default_affinity: float = 1.0
    
    # 賽道類型對特定風格車手的加成
    street_circuit_bonus: float = 0.1  # 街道賽專家額外加成
    high_speed_bonus: float = 0.08     # 高速賽道專家額外加成
    
    # 適應性值的有效範圍
    min_affinity: float = 0.7
    max_affinity: float = 1.4


class CircuitAffinityCalculator:
    """
    賽道適應性計算器
    
    基於歷史數據計算車手在特定賽道的適應性因子
    """
    
    def __init__(self, config: CircuitAffinityConfig = None):
        self.config = config or CircuitAffinityConfig()
        self._affinity_data = DRIVER_CIRCUIT_AFFINITY
        self._circuit_types = CIRCUIT_TYPES
        
    def get_circuit_affinity(
        self, 
        driver_code: str, 
        circuit_name: str
    ) -> float:
        """
        獲取車手在特定賽道的適應性因子
        
        Args:
            driver_code: 車手代碼 (例如 "VER", "LEC")
            circuit_name: 賽道名稱 (例如 "Monaco", "Spa")
            
        Returns:
            適應性因子 [0.7, 1.4]，1.0 為平均水平
        """
        # 標準化賽道名稱
        circuit_key = self._normalize_circuit_name(circuit_name)
        
        # 獲取車手數據
        driver_data = self._affinity_data.get(driver_code, {})
        
        if not driver_data:
            return self.config.default_affinity
            
        # 查找特定賽道
        affinity = driver_data.get(circuit_key, driver_data.get("default", self.config.default_affinity))
        
        # 限制範圍
        return np.clip(affinity, self.config.min_affinity, self.config.max_affinity)
        
    def _normalize_circuit_name(self, circuit_name: str) -> str:
        """標準化賽道名稱"""
        if not circuit_name:
            return ""
            
        # 常見名稱映射
        name_map = {
            "japan": "Suzuka",
            "japanese": "Suzuka",
            "suzuka": "Suzuka",
            "italy": "Monza",
            "italian": "Monza",
            "monza": "Monza",
            "belgium": "Spa",
            "belgian": "Spa",
            "spa": "Spa",
            "monaco": "Monaco",
            "singapore": "Singapore",
            "azerbaijan": "Baku",
            "baku": "Baku",
            "saudi": "Jeddah",
            "jeddah": "Jeddah",
            "vegas": "Las Vegas",
            "las vegas": "Las Vegas",
            "uk": "Silverstone",
            "british": "Silverstone",
            "silverstone": "Silverstone",
            "hungary": "Hungary",
            "hungarian": "Hungary",
            "hungaroring": "Hungary",
            "mexico": "Mexico",
            "mexican": "Mexico",
            "brazil": "Brazil",
            "brazilian": "Brazil",
            "interlagos": "Brazil",
            "sao paulo": "Brazil",
            "abu dhabi": "Abu Dhabi",
            "uae": "Abu Dhabi",
            "bahrain": "Bahrain",
            "australia": "Australia",
            "australian": "Australia",
            "melbourne": "Australia",
            "canada": "Canada",
            "canadian": "Canada",
            "montreal": "Canada",
            "austria": "Austria",
            "austrian": "Austria",
            "spielberg": "Austria",
            "netherlands": "Netherlands",
            "dutch": "Netherlands",
            "zandvoort": "Netherlands",
            "usa": "USA",
            "cota": "USA",
            "austin": "USA",
            "qatar": "Qatar",
            "miami": "Miami",
            "china": "China",
            "chinese": "China",
            "shanghai": "China",
            "emilia": "Imola",
            "imola": "Imola",
        }
        
        normalized = name_map.get(circuit_name.lower().strip())
        if normalized:
            return normalized
            
        # 嘗試首字母大寫
        return circuit_name.strip().title()
        
    def get_circuit_type(self, circuit_name: str) -> str:
        """獲取賽道類型"""
        circuit_key = self._normalize_circuit_name(circuit_name)
        return self._circuit_types.get(circuit_key, "mixed")


# ============================================================================
# FP3/Q 補償計算器 (v3.4 動態版本)
# ============================================================================

# 賽道超車難度權重 (越難超車，Q 補償越重要)
# 基於 2023-2024 數據訓練計算 (analyze_circuit_overtake_v2.py)
# 公式: 0.40*Q相關性 + 0.25*位置保持率 + 0.20*Q1勝率 + 0.15*(1-進步率)
CIRCUIT_OVERTAKE_DIFFICULTY = {
    # === 極難超車 (difficulty > 0.65) ===
    "Monaco": 0.76,       # Q_corr=0.88, Q1_win=100% - 幾乎不可能超車
    "Imola": 0.68,        # Q_corr=0.88, Q1_win=100%
    "Suzuka": 0.66,       # Q_corr=0.81, Q1_win=100% - 技術賽道
    
    # === 難超車 (difficulty 0.55-0.65) ===
    "Yas Marina": 0.62,   # Q_corr=0.68, Q1_win=100%
    "Abu Dhabi": 0.62,    # 別名
    "Shanghai": 0.60,     # Q_corr=0.77, Q1_win=100%
    "Jeddah": 0.59,       # Q_corr=0.72, Q1_win=100%
    "Sakhir": 0.59,       # Q_corr=0.70, Q1_win=100%
    "Bahrain": 0.59,      # 別名
    "Zandvoort": 0.58,    # Q_corr=0.65, Q1_win=100%
    "Catalunya": 0.58,    # Q_corr=0.77, Q1_win=50%
    "Barcelona": 0.58,    # 別名
    "Lusail": 0.57,       # Q_corr=0.67, Q1_win=100%
    "Qatar": 0.57,        # 別名
    "Singapore": 0.55,    # Q_corr=0.63, Q1_win=100%
    
    # === 中等難度 (difficulty 0.40-0.55) ===
    "Silverstone": 0.52,  # Q_corr=0.73, Q1_win=50%
    "Spielberg": 0.47,    # Q_corr=0.66, Q1_win=50%
    "Austria": 0.47,      # 別名
    "Miami": 0.47,        # Q_corr=0.80, Q1_win=0%
    "Spa": 0.47,          # Q_corr=0.71, Q1_win=50%
    "Monza": 0.44,        # Q_corr=0.87, Q1_win=0% - Q 相關高但超車機會多
    "Mexico City": 0.44,  # Q_corr=0.61, Q1_win=50%
    "Mexico": 0.44,       # 別名
    "Las Vegas": 0.44,    # Q_corr=0.52, Q1_win=50%
    "Montreal": 0.43,     # Q_corr=0.60, Q1_win=50%
    "Canada": 0.43,       # 別名
    
    # === 容易超車 (difficulty < 0.40) ===
    "Budapest": 0.39,     # Q_corr=0.72, Q1_win=0% - 意外結果高
    "Hungary": 0.39,      # 別名
    "Interlagos": 0.38,   # Q_corr=0.49, Q1_win=50% - 天氣變數大
    "Brazil": 0.38,       # 別名
    "Baku": 0.36,         # Q_corr=0.68, Q1_win=0% - 街道賽但事故多
    "Azerbaijan": 0.36,   # 別名
    "Austin": 0.31,       # Q_corr=0.47, Q1_win=0% - 最易逆轉
    "COTA": 0.31,         # 別名
    "Melbourne": 0.29,    # Q_corr=0.29, Q1_win=50% - DNF 率高
    "Australia": 0.29,    # 別名
    
    # 預設值
    "default": 0.50,
}

# ============================================================================
# 輪胎策略因子 (v3.4 新增 - 基於 2023-2024 真實數據)
# ============================================================================

# 輪胎類型的相對性能 (單圈速度)
# 基於 2024 Bahrain/Japan/China 等比賽分析:
# - SOFT 基準 = 1.000 (約 98s/圈)
# =============================================================================
# 輪胎性能參數 - 2023-2024 完整訓練結果
# =============================================================================
# 訓練數據: 2023-2024 共 46 場比賽, 2210 個 stint
# 訓練日期: 2025-12-01
#
# 訓練發現:
# - SOFT cliff 很早 (第11圈)，衰退快
# - MEDIUM 最常用 (863 stints)，cliff 第13圈
# - HARD cliff 最晚 (第17圈)，衰退最慢
# - INTERMEDIATE 在濕地實際上更快 (負衰退 = 賽道變乾)
#
# speed: 相對 SOFT 的速度 (>1 = 比 SOFT 慢)
# deg_per_lap: 每圈性能衰退係數
# cliff_lap: cliff 開始圈數 (訓練檢測)
TYRE_PERFORMANCE = {
    "SOFT": {
        "speed": 1.000,           # 基準 (295 stints)
        "deg_per_lap": 0.0001,    # 每圈降 0.01%
        "ideal_laps": 7,          # cliff 前 70%
        "cliff_lap": 11,          # 訓練檢測: 71.9% 在第11圈 cliff
    },
    "MEDIUM": {
        "speed": 1.0113,          # 比 SOFT 慢 1.13% (863 stints)
        "deg_per_lap": 0.00038,   # 每圈降 0.038%
        "ideal_laps": 9,
        "cliff_lap": 13,          # 訓練檢測: 81.3% 在第13圈 cliff
    },
    "HARD": {
        "speed": 1.0195,          # 比 SOFT 慢 1.95% (911 stints)
        "deg_per_lap": 0.0001,    # 每圈降 0.01% (最穩定)
        "ideal_laps": 11,
        "cliff_lap": 17,          # 訓練檢測: 70.9% 在第17圈 cliff
    },
    "INTERMEDIATE": {
        "speed": 0.9547,          # 濕地比 SOFT 快 4.5% (135 stints)
        "deg_per_lap": 0.0001,    # 濕地變乾時負衰退，取 0
        "ideal_laps": 9,
        "cliff_lap": 14,          # 訓練檢測: 65.2%
    },
    "WET": {
        "speed": 0.940,           # 全雨估計 (樣本不足: 5 stints)
        "deg_per_lap": 0.0001,
        "ideal_laps": 15,
        "cliff_lap": 20,
    },
}

# 輪胎 cliff 效應
# 超過 cliff_lap 後，衰退率急劇增加
TYRE_CLIFF_MULTIPLIER = 5.0  # cliff 後衰退率 x5


# ============================================================================
# 進站時間因子 (v3.4 新增)
# ============================================================================

# 進站時間統計 (秒)
PIT_STOP_STATS = {
    "excellent": {"time": 2.0, "factor": 1.02},   # < 2.2s - 提升 2%
    "good": {"time": 2.5, "factor": 1.01},        # 2.2-2.5s - 提升 1%
    "average": {"time": 3.0, "factor": 1.00},     # 2.5-3.0s - 中性
    "slow": {"time": 3.5, "factor": 0.99},        # 3.0-4.0s - 降低 1%
    "disaster": {"time": 5.0, "factor": 0.95},    # > 4.0s - 降低 5%
}

# 進站窗口優勢 (undercut/overcut)
PIT_WINDOW_ADVANTAGE = {
    "undercut_success": 1.05,     # 成功 undercut 提升 5%
    "overcut_success": 1.03,      # 成功 overcut 提升 3%
    "pit_before_leader": 1.02,    # 比領先者先進站
    "pit_after_leader": 0.98,     # 比領先者後進站
}


@dataclass
class FP3QCompensationConfig:
    """FP3/Q 補償配置"""
    # Q 補償有效圈數 (只在前 N 圈生效)
    effective_laps: int = 10
    
    # Q 位置基礎補償強度
    q_base_strength: float = 0.30  # Q1 最多提升 30%
    
    # FP3 節奏優勢權重 (相關性 0.1781)
    fp3_pace_weight: float = 0.05
    
    # 最小/最大補償因子
    min_compensation: float = 0.6
    max_compensation: float = 1.3


class FP3QCompensationCalculator:
    """
    FP3/Q 補償因子計算器 (v3.3 動態版本)
    
    核心規則:
    1. **只在前 10 圈有效**: Lap 1-10 有補償，Lap 11+ 歸零
    2. **賽道權重不同**: Monaco 權重高，Monza 權重低
    3. **被超車歸零**: 一旦當前位置 > Q 位置，補償 = 1.0
    
    基於 2023-2024 歷史數據:
    - Q Position vs Final Position 相關性: 0.6737
    - 桿位出發贏得 58.7% 勝利
    - Monaco Q1 幾乎等於 P1，Monza 則不一定
    
    使用方法:
    ```python
    calc = FP3QCompensationCalculator()
    
    # 動態計算 (每圈調用)
    factor = calc.get_dynamic_compensation(
        driver_code="VER",
        circuit="Monaco",
        q_position=1,
        current_position=1,  # 仍在 Q1 位置
        current_lap=5,       # 第 5 圈
        total_laps=78,
    )
    # Monaco Q1 且仍在 P1 → factor = 1.285 (提升 28.5%)
    
    # 如果被超車
    factor = calc.get_dynamic_compensation(
        driver_code="VER",
        circuit="Monaco",
        q_position=1,
        current_position=2,  # 掉到 P2
        current_lap=5,
    )
    # 被超車 → factor = 1.0 (無補償)
    ```
    """
    
    def __init__(self, config: FP3QCompensationConfig = None):
        """初始化補償計算器"""
        self.config = config or FP3QCompensationConfig()
        
        # 載入的補償數據
        self._compensation_data = {}
        self._data_loaded = False
        
        # 賽道超車難度
        self._circuit_difficulty = CIRCUIT_OVERTAKE_DIFFICULTY.copy()
        
        # v3.4: 情境修正因子 (雨戰、SC、DRS 等)
        self._situation_modifier = 1.0
        
        # 車手 Q 位置記錄 (用於追蹤是否被超車)
        self._driver_q_positions: Dict[str, int] = {}
        
        # 統計數據
        self._q_position_win_rates = {
            1: 0.587, 2: 0.174, 3: 0.087, 4: 0.065, 5: 0.022,
        }
        
    def load_compensation_data(self, csv_path: str) -> bool:
        """
        從 CSV 載入補償數據
        
        Args:
            csv_path: CSV 檔案路徑
            
        Returns:
            是否載入成功
        """
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():
                key = (row['race'], row['driver_code'])
                self._compensation_data[key] = {
                    'q_position': row.get('q_position', 10),
                    'q_gap_to_pole': row.get('q_gap_to_pole', 1.0),
                    'fp3_pace_advantage': row.get('fp3_pace_advantage', 0.1),
                    'fp3_tyre_deg_rate': row.get('fp3_tyre_deg_rate', 0.05),
                    'combined_compensation': row.get('combined_compensation', 1.0),
                }
            
            self._data_loaded = True
            logger.info(f"Loaded {len(self._compensation_data)} FP3/Q compensation records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load FP3/Q compensation data: {e}")
            return False
    
    def get_compensation_factor(
        self,
        driver_code: str,
        race: str = None,
        q_position: int = None,
        fp3_pace_advantage: float = None,
        q_gap_to_pole: float = None,
    ) -> float:
        """
        計算補償因子
        
        基於 2023-2024 數據分析:
        - Q1: 58.7% 勝率 → factor = 1.30 (提升 30%)
        - Q2: 17.4% 勝率 → factor = 1.15
        - Q3: 8.7% 勝率 → factor = 1.05
        - Q4-Q10: 逐漸下降到 0.85
        - Q11-Q20: 逐漸下降到 0.60
        
        Args:
            driver_code: 車手代碼
            race: 賽事名稱 (用於查詢歷史數據)
            q_position: 排位位置 (1-20)
            fp3_pace_advantage: FP3 節奏優勢 (相對最快，越小越好)
            q_gap_to_pole: 與桿位的差距 (秒)
            
        Returns:
            補償因子 [0.5, 1.5]
        """
        # 嘗試從載入的數據中獲取
        if race and self._data_loaded:
            key = (race, driver_code)
            if key in self._compensation_data:
                data = self._compensation_data[key]
                q_position = q_position or data.get('q_position')
                fp3_pace_advantage = fp3_pace_advantage or data.get('fp3_pace_advantage')
                q_gap_to_pole = q_gap_to_pole or data.get('q_gap_to_pole')
        
        # 計算 Q 位置補償 (基於實際統計的平滑曲線)
        q_factor = 1.0
        if q_position is not None:
            # 使用對數曲線: Q1 = 1.30, Q20 = 0.60
            # factor = 1.30 - 0.70 * log10(position) / log10(20)
            # 簡化為線性衰減: factor = 1.30 - 0.035 * (position - 1)
            if q_position <= 3:
                # Q1-Q3: 桿位優勢區
                q_factor = 1.30 - 0.075 * (q_position - 1)  # Q1=1.30, Q2=1.225, Q3=1.15
            elif q_position <= 10:
                # Q4-Q10: 中段位置
                q_factor = 1.15 - 0.043 * (q_position - 3)  # Q4=1.107, Q10=0.85
            else:
                # Q11-Q20: 後段位置
                q_factor = 0.85 - 0.025 * (q_position - 10)  # Q11=0.825, Q20=0.60
            
            q_factor = np.clip(q_factor, 0.60, 1.30)
        
        # 計算 FP3 節奏補償
        pace_factor = 1.0
        if fp3_pace_advantage is not None:
            # 節奏優勢 (相對最快) 越大，補償越低
            # 最快 (0%) = 1.05, 慢 10% = 0.95
            pace_factor = 1.05 - fp3_pace_advantage * 1.0
            pace_factor = np.clip(pace_factor, 0.90, 1.10)
        
        # 計算 Q 差距補償
        gap_factor = 1.0
        if q_gap_to_pole is not None:
            # 與桿位差距越大，補償越低
            # 0 秒 = 1.0, 1 秒 = 0.90, 2 秒 = 0.80
            gap_factor = 1.0 - (q_gap_to_pole / 10.0)  # 每差 10 秒降 10%
            gap_factor = np.clip(gap_factor, 0.80, 1.0)
        
        # 綜合補償因子
        combined = q_factor * pace_factor * gap_factor
        
        # 限制範圍
        return float(np.clip(combined, self.config.min_compensation, self.config.max_compensation))
    
    def get_dynamic_compensation(
        self,
        driver_code: str,
        circuit: str,
        q_position: int,
        current_position: int,
        current_lap: int,
        total_laps: int = 53,
    ) -> float:
        """
        動態計算補償因子 (v3.3 核心方法)
        
        規則:
        1. **只在前 10 圈有效**: Lap 1-10 有補償，Lap 11+ 返回 1.0
        2. **賽道權重不同**: Monaco 權重高 (0.95)，Monza 權重低 (0.25)
        3. **被超車歸零**: current_position > q_position → 返回 1.0
        
        Args:
            driver_code: 車手代碼
            circuit: 賽道名稱
            q_position: 排位位置 (起跑位置)
            current_position: 當前位置
            current_lap: 當前圈數
            total_laps: 總圈數
            
        Returns:
            補償因子 [0.6, 1.3] 或 1.0 (無補償)
        """
        # 規則 1: 超過有效圈數，無補償
        if current_lap > self.config.effective_laps:
            return 1.0
        
        # 規則 3: 被超車 (當前位置比 Q 位置差)，無補償
        if current_position > q_position:
            return 1.0
        
        # 規則 2: 獲取賽道超車難度權重
        circuit_weight = self._get_circuit_weight(circuit)
        
        # 計算基礎 Q 補償 (Q1=1.30, Q20=0.60)
        base_q_factor = self._calculate_base_q_factor(q_position)
        
        # 計算圈數衰減 (Lap 1 = 100%, Lap 10 = 10%)
        lap_decay = 1.0 - (current_lap - 1) / self.config.effective_laps
        lap_decay = max(0.1, lap_decay)  # 最低 10%
        
        # 獲取情境修正因子 (雨戰、SC、DRS 等)
        situation_modifier = self._situation_modifier
        
        # 綜合計算
        # effective_factor = 1.0 + (base_factor - 1.0) * circuit_weight * lap_decay * situation_modifier
        raw_boost = (base_q_factor - 1.0) * circuit_weight * lap_decay * situation_modifier
        final_factor = 1.0 + raw_boost
        
        return float(np.clip(final_factor, self.config.min_compensation, self.config.max_compensation))
    
    def set_situation_modifier(
        self,
        is_wet: bool = False,
        is_sc_restart: bool = False,
        drs_enabled: bool = True,
        laps_since_restart: int = 99,
    ):
        """
        設置比賽情境修正因子 (v3.4 新增)
        
        情境會暫時影響超車難度 (modifier > 1 = 更難超車，Q補償更重要):
        - 雨戰: +20% 難度 (濕地更難超車)
        - SC 重啟: -30% 難度 (輪胎溫度差、重啟混戰)，持續 3 圈
        - DRS 啟用: -15% 難度 (DRS 讓超車更容易)
        - DRS 禁用: 維持正常難度 (1.0)
        
        Args:
            is_wet: 是否濕地
            is_sc_restart: 是否剛 SC 重啟
            drs_enabled: DRS 是否啟用 (啟用時超車更容易)
            laps_since_restart: SC 重啟後的圈數
        """
        modifier = 1.0
        
        # 雨戰: 更難超車
        if is_wet:
            modifier *= 1.20
        
        # SC 重啟: 短暫更容易超車 (3 圈內)
        if is_sc_restart and laps_since_restart <= 3:
            # 第 1 圈 -30%, 第 2 圈 -20%, 第 3 圈 -10%
            restart_bonus = 0.30 - (laps_since_restart - 1) * 0.10
            modifier *= (1.0 - restart_bonus)
        
        # DRS 啟用: 超車更容易 (難度降低)
        if drs_enabled:
            modifier *= 0.85  # -15% 難度
        # DRS 禁用: 維持正常難度 (不加成)
        
        self._situation_modifier = modifier
    
    def _get_circuit_weight(self, circuit: str) -> float:
        """獲取賽道超車難度權重"""
        if not circuit:
            return self._circuit_difficulty.get("default", 0.50)
        
        # 標準化賽道名稱
        circuit_lower = circuit.lower().strip()
        
        # 直接匹配
        for key, weight in self._circuit_difficulty.items():
            if key.lower() in circuit_lower or circuit_lower in key.lower():
                return weight
        
        # 常見別名
        aliases = {
            "japan": "Suzuka",
            "japanese": "Suzuka",
            "italy": "Monza",
            "italian": "Monza",
            "belgium": "Spa",
            "belgian": "Spa",
            "uk": "Silverstone",
            "british": "Silverstone",
            "brazil": "Interlagos",
            "brazilian": "Interlagos",
            "sao paulo": "Interlagos",
            "qatar": "Lusail",
            "usa": "Austin",
            "united states": "Austin",
            "spain": "Barcelona",
            "spanish": "Barcelona",
            "netherlands": "Zandvoort",
            "dutch": "Zandvoort",
            "australia": "Melbourne",
            "australian": "Melbourne",
            "mexico": "Mexico City",
            "mexican": "Mexico City",
            "canada": "Montreal",
            "canadian": "Montreal",
            "uae": "Abu Dhabi",
            "emilia": "Imola",
            "china": "Shanghai",
            "chinese": "Shanghai",
            "saudi": "Jeddah",
            "saudi arabia": "Jeddah",
        }
        
        for alias, canonical in aliases.items():
            if alias in circuit_lower:
                return self._circuit_difficulty.get(canonical, 0.50)
        
        return self._circuit_difficulty.get("default", 0.50)
    
    def _calculate_base_q_factor(self, q_position: int) -> float:
        """計算基礎 Q 補償因子"""
        if q_position <= 3:
            # Q1-Q3: 桿位優勢區
            return 1.30 - 0.075 * (q_position - 1)  # Q1=1.30, Q2=1.225, Q3=1.15
        elif q_position <= 10:
            # Q4-Q10: 中段位置
            return 1.15 - 0.043 * (q_position - 3)  # Q4=1.107, Q10=0.85
        else:
            # Q11-Q20: 後段位置
            return 0.85 - 0.025 * (q_position - 10)  # Q11=0.825, Q20=0.60
    
    def set_qualifying_results(self, q_results: Dict[str, int]):
        """
        設置排位結果
        
        Args:
            q_results: {driver_code: q_position}
        """
        self._driver_q_positions = q_results.copy()
        logger.info(f"Set qualifying results for {len(q_results)} drivers")
    
    def get_q_position_boost(self, q_position: int) -> float:
        """
        獲取基於 Q 位置的勝率提升因子
        
        基於 2023-2024 統計:
        - Q1: 58.7% 勝率 → factor = 11.74 (相對平均 5%)
        - Q2: 17.4% 勝率 → factor = 3.48
        - Q3: 8.7% 勝率 → factor = 1.74
        
        Args:
            q_position: 排位位置
            
        Returns:
            勝率提升因子
        """
        win_rate = self._q_position_win_rates.get(q_position, 0.01)
        avg_win_rate = 1 / 20  # 5%
        return win_rate / avg_win_rate


# ============================================================================
# 輪胎策略因子計算器 (v3.4 新增)
# ============================================================================

@dataclass
class TyreState:
    """輪胎狀態"""
    compound: str = "MEDIUM"       # SOFT, MEDIUM, HARD, INTERMEDIATE, WET
    age: int = 0                   # 輪胎圈數
    stint_number: int = 1          # 第幾個 stint
    laps_since_pit: int = 0        # 距離上次進站的圈數


class TyreStrategyCalculator:
    """
    輪胎策略因子計算器 (v3.4 新增)
    
    計算輪胎狀態對勝率的影響:
    1. 輪胎相對性能 (新軟 vs 舊硬)
    2. 輪胎衰退預測
    3. 策略窗口優勢 (undercut/overcut)
    
    使用方法:
    ```python
    calc = TyreStrategyCalculator()
    
    # 計算兩車手的輪胎優勢
    driver_tyre = TyreState(compound="SOFT", age=5)
    rival_tyre = TyreState(compound="HARD", age=15)
    
    factor = calc.get_tyre_advantage_factor(
        driver_tyre=driver_tyre,
        rival_tyre=rival_tyre,
        laps_remaining=20,
    )
    # 新軟胎 vs 舊硬胎 → factor > 1.0 (有優勢)
    ```
    """
    
    def __init__(self):
        self._tyre_performance = TYRE_PERFORMANCE
        self._cliff_multiplier = TYRE_CLIFF_MULTIPLIER
    
    def get_tyre_performance(self, compound: str, age: int) -> float:
        """
        計算當前輪胎性能
        
        Args:
            compound: 輪胎類型
            age: 輪胎圈數
            
        Returns:
            性能係數 [0.80, 1.00]
        """
        compound_upper = compound.upper() if compound else "MEDIUM"
        tyre_data = self._tyre_performance.get(compound_upper, self._tyre_performance["MEDIUM"])
        
        # 基礎速度
        base_speed = tyre_data["speed"]
        
        # 衰退計算 (基於 2023-2024 真實數據)
        deg_rate = tyre_data["deg_per_lap"]
        cliff_lap = tyre_data.get("cliff_lap", 40)
        
        # 正常衰退
        if age <= cliff_lap:
            degradation = age * deg_rate
        else:
            # cliff 效應: 超過 cliff_lap 後衰退率急劇增加
            normal_deg = cliff_lap * deg_rate
            cliff_laps = age - cliff_lap
            cliff_deg = cliff_laps * deg_rate * TYRE_CLIFF_MULTIPLIER
            degradation = normal_deg + cliff_deg
        
        performance = base_speed - degradation
        return max(0.80, performance)
    
    def get_tyre_advantage_factor(
        self,
        driver_tyre: TyreState,
        rival_tyre: TyreState = None,
        laps_remaining: int = 20,
    ) -> float:
        """
        計算相對輪胎優勢因子
        
        Args:
            driver_tyre: 車手輪胎狀態
            rival_tyre: 對手輪胎狀態 (如果 None，使用平均假設)
            laps_remaining: 剩餘圈數
            
        Returns:
            優勢因子 [0.90, 1.10]
        """
        driver_perf = self.get_tyre_performance(driver_tyre.compound, driver_tyre.age)
        
        if rival_tyre:
            rival_perf = self.get_tyre_performance(rival_tyre.compound, rival_tyre.age)
        else:
            # 假設對手使用中等狀態
            rival_perf = self.get_tyre_performance("MEDIUM", 15)
        
        # 性能差異轉換為優勢因子
        # 每 1% 性能差 → 1% 勝率差
        perf_diff = driver_perf - rival_perf
        
        # 考慮剩餘圈數: 圈數越少，輪胎優勢越重要
        laps_factor = min(1.0, 30 / max(laps_remaining, 1))  # 最後 30 圈最重要
        
        # 最終因子
        factor = 1.0 + (perf_diff * laps_factor * 2.0)  # 放大輪胎效應
        
        return float(np.clip(factor, 0.90, 1.10))
    
    def predict_tyre_life(self, tyre: TyreState, target_laps: int) -> Dict[str, Any]:
        """
        預測輪胎到目標圈數時的狀態
        
        Args:
            tyre: 當前輪胎狀態
            target_laps: 目標圈數 (從現在開始)
            
        Returns:
            {"can_finish": bool, "performance_at_end": float, "cliff_risk": bool}
        """
        compound = tyre.compound.upper() if tyre.compound else "MEDIUM"
        tyre_data = self._tyre_performance.get(compound, self._tyre_performance["MEDIUM"])
        
        future_age = tyre.age + target_laps
        ideal_laps = tyre_data["ideal_laps"]
        
        # 計算終點性能
        end_performance = self.get_tyre_performance(compound, future_age)
        
        # cliff 風險: 超過理想圈數 1.5 倍
        cliff_threshold = int(ideal_laps * 1.5)
        cliff_risk = future_age > cliff_threshold
        
        # 能否完成: 性能不低於 85%
        can_finish = end_performance >= 0.85
        
        return {
            "can_finish": can_finish,
            "performance_at_end": end_performance,
            "cliff_risk": cliff_risk,
            "future_age": future_age,
        }


# ============================================================================
# 進站時間因子計算器 (v3.4 新增)
# ============================================================================

@dataclass
class PitStopEvent:
    """進站事件"""
    lap: int
    duration: float        # 秒
    position_before: int
    position_after: int
    undercut_target: str = None  # 嘗試 undercut 的對象


class PitStopCalculator:
    """
    進站時間因子計算器 (v3.4 新增)
    
    計算進站對勝率的影響:
    1. 進站時間好壞
    2. Undercut/Overcut 成功與否
    3. 策略時機
    
    使用方法:
    ```python
    calc = PitStopCalculator()
    
    # 評估進站
    pit_event = PitStopEvent(
        lap=20, duration=2.3, 
        position_before=2, position_after=1
    )
    factor = calc.evaluate_pit_stop(pit_event)
    # 快速進站 + 超車 → factor > 1.0
    
    # 評估進站策略
    factor = calc.evaluate_pit_strategy(
        driver_pit_laps=[15, 35],
        rival_pit_laps=[18, 38],
        current_lap=40,
    )
    # 先進站策略 → undercut 優勢
    ```
    """
    
    def __init__(self):
        self._pit_stats = PIT_STOP_STATS
        self._window_advantage = PIT_WINDOW_ADVANTAGE
        
        # 車隊進站速度統計 (2024 平均)
        self._team_pit_speed = {
            "Red Bull Racing": 2.2,
            "McLaren": 2.3,
            "Ferrari": 2.4,
            "Mercedes": 2.3,
            "Aston Martin": 2.5,
            "Alpine": 2.6,
            "Williams": 2.5,
            "RB": 2.4,
            "Haas": 2.5,
            "Sauber": 2.6,
            "default": 2.5,
        }
    
    def evaluate_pit_stop(self, pit_event: PitStopEvent) -> float:
        """
        評估單次進站對勝率的影響
        
        Args:
            pit_event: 進站事件
            
        Returns:
            因子 [0.90, 1.10]
        """
        duration = pit_event.duration
        
        # 進站時間評級
        if duration < 2.2:
            time_factor = self._pit_stats["excellent"]["factor"]
        elif duration < 2.5:
            time_factor = self._pit_stats["good"]["factor"]
        elif duration < 3.0:
            time_factor = self._pit_stats["average"]["factor"]
        elif duration < 4.0:
            time_factor = self._pit_stats["slow"]["factor"]
        else:
            time_factor = self._pit_stats["disaster"]["factor"]
        
        # 位置變化因子
        position_change = pit_event.position_before - pit_event.position_after
        if position_change > 0:
            # 進站後位置提升 (undercut 成功)
            position_factor = 1.0 + (position_change * 0.01)  # 每超一位 +1%
        elif position_change < 0:
            # 進站後位置下降
            position_factor = 1.0 + (position_change * 0.005)  # 每掉一位 -0.5%
        else:
            position_factor = 1.0
        
        combined = time_factor * position_factor
        return float(np.clip(combined, 0.90, 1.10))
    
    def evaluate_pit_strategy(
        self,
        driver_pit_laps: List[int],
        rival_pit_laps: List[int],
        current_lap: int,
        total_laps: int = 53,
    ) -> float:
        """
        評估進站策略優勢
        
        Args:
            driver_pit_laps: 車手進站圈數列表
            rival_pit_laps: 對手進站圈數列表
            current_lap: 當前圈數
            total_laps: 總圈數
            
        Returns:
            策略優勢因子 [0.95, 1.05]
        """
        if not driver_pit_laps or not rival_pit_laps:
            return 1.0
        
        # 計算平均進站時機
        driver_avg = sum(driver_pit_laps) / len(driver_pit_laps)
        rival_avg = sum(rival_pit_laps) / len(rival_pit_laps)
        
        # 早進站 (undercut) 通常有利
        if driver_avg < rival_avg:
            # 先進站策略
            advantage = (rival_avg - driver_avg) / total_laps * 0.1
            factor = 1.0 + min(advantage, 0.03)
        else:
            # 後進站策略 (overcut)
            disadvantage = (driver_avg - rival_avg) / total_laps * 0.05
            factor = 1.0 - min(disadvantage, 0.02)
        
        return float(np.clip(factor, 0.95, 1.05))
    
    def get_expected_pit_time(self, team: str) -> float:
        """
        獲取車隊預期進站時間
        
        Args:
            team: 車隊名稱
            
        Returns:
            預期進站時間 (秒)
        """
        return self._team_pit_speed.get(team, self._team_pit_speed["default"])


# ============================================================================
# SHAP 可解釋性模組 (v3.1 新增)
# ============================================================================

@dataclass
class SHAPExplanation:
    """SHAP 解釋結果"""
    driver_code: str
    win_probability: float
    feature_contributions: List[Tuple[str, float]]  # [(feature_name, contribution), ...]
    base_value: float  # 基準值 (平均預測)
    total_drivers: int


class SHAPExplainer:
    """
    SHAP 可解釋性模組
    
    為 XGBoost 模型提供特徵重要性解釋，幫助用戶理解：
    「為什麼這個車手有 X% 的勝率？」
    
    參考: "F1 Race Winner Prediction Using RF and SHAP Analysis" (IEEE 2025)
    """
    
    def __init__(self, model=None, feature_names: List[str] = None):
        """
        初始化 SHAP 解釋器
        
        Args:
            model: XGBoost 模型
            feature_names: 特徵名稱列表
        """
        self.model = model
        self.feature_names = feature_names or []
        self._explainer = None
        self._last_shap_values = None
        self._last_features = None
        
        # 特徵名稱的中文翻譯
        self.feature_labels = {
            'position': '目前位置',
            'gap_to_leader': '與領先者差距',
            'gap_to_ahead': '與前車差距',
            'lap_time': '圈時',
            'best_lap_time': '最快圈',
            'tyre_compound': '輪胎類型',
            'tyre_age': '輪胎年齡',
            'pit_count': '進站次數',
            'laps_remaining': '剩餘圈數',
            'track_status': '賽道狀態',
            'air_temp': '氣溫',
            'rainfall': '下雨',
            'driver_win_rate': '車手勝率',
            'driver_podium_rate': '車手領獎台率',
            'team_rating': '車隊評分',
            'circuit_overtake_rate': '賽道超車率',
            'circuit_sc_rate': '賽道 SC 率',
            'qualifying_position': '排位成績',
            'position_delta': '位置變化',
            'log_gap': '差距(log)',
            'race_progress': '比賽進度',
            'circuit_affinity': '賽道適應性',
        }
        
    def setup(self, model, feature_names: List[str]) -> bool:
        """
        設置 SHAP 解釋器
        
        Args:
            model: XGBoost 模型
            feature_names: 特徵名稱列表
            
        Returns:
            是否設置成功
        """
        if not SHAP_AVAILABLE:
            logger.warning("SHAP library not available. Install with: pip install shap")
            return False
            
        try:
            self.model = model
            self.feature_names = feature_names
            self._explainer = shap.TreeExplainer(model)
            logger.info("SHAP explainer initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")
            return False
            
    def explain(
        self, 
        features: np.ndarray, 
        driver_codes: List[str],
        win_probabilities: Dict[str, float]
    ) -> Dict[str, SHAPExplanation]:
        """
        為所有車手生成 SHAP 解釋
        
        Args:
            features: 特徵矩陣 (n_drivers x n_features)
            driver_codes: 車手代碼列表
            win_probabilities: {driver_code: win_prob}
            
        Returns:
            {driver_code: SHAPExplanation}
        """
        if not SHAP_AVAILABLE or self._explainer is None:
            return self._generate_fallback_explanation(features, driver_codes, win_probabilities)
            
        try:
            # 計算 SHAP 值
            shap_values = self._explainer.shap_values(features)
            self._last_shap_values = shap_values
            self._last_features = features
            
            # 基準值 (expected value)
            base_value = float(self._explainer.expected_value)
            
            explanations = {}
            for i, driver_code in enumerate(driver_codes):
                # 獲取該車手的 SHAP 值
                driver_shap = shap_values[i]
                
                # 組合特徵名稱和貢獻值
                contributions = []
                for j, feat_name in enumerate(self.feature_names):
                    contrib = float(driver_shap[j])
                    if abs(contrib) > 0.001:  # 只保留有意義的貢獻
                        contributions.append((feat_name, contrib))
                
                # 按絕對值排序
                contributions.sort(key=lambda x: abs(x[1]), reverse=True)
                
                explanations[driver_code] = SHAPExplanation(
                    driver_code=driver_code,
                    win_probability=win_probabilities.get(driver_code, 0),
                    feature_contributions=contributions[:10],  # 只保留前 10 個
                    base_value=base_value,
                    total_drivers=len(driver_codes)
                )
                
            return explanations
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return self._generate_fallback_explanation(features, driver_codes, win_probabilities)
            
    def _generate_fallback_explanation(
        self,
        features: np.ndarray,
        driver_codes: List[str],
        win_probabilities: Dict[str, float]
    ) -> Dict[str, SHAPExplanation]:
        """
        生成回退解釋 (當 SHAP 不可用時)
        
        使用簡單的特徵值差異作為「貢獻度」近似
        """
        explanations = {}
        
        # 計算每個特徵的平均值
        mean_features = np.mean(features, axis=0) if len(features) > 0 else np.zeros(len(self.feature_names))
        
        for i, driver_code in enumerate(driver_codes):
            contributions = []
            
            for j, feat_name in enumerate(self.feature_names):
                if j < len(features[i]):
                    diff = features[i][j] - mean_features[j]
                    # 標準化貢獻值
                    contrib = diff * 0.01  # 簡單縮放
                    
                    # 特殊處理某些特徵
                    if feat_name == 'position':
                        contrib = -diff * 0.05  # 位置越前越好
                    elif feat_name in ['gap_to_leader', 'gap_to_ahead']:
                        contrib = -diff * 0.02  # 差距越小越好
                    elif feat_name in ['driver_win_rate', 'driver_podium_rate']:
                        contrib = diff * 0.1   # 歷史表現越好越好
                        
                    if abs(contrib) > 0.001:
                        contributions.append((feat_name, contrib))
            
            contributions.sort(key=lambda x: abs(x[1]), reverse=True)
            
            explanations[driver_code] = SHAPExplanation(
                driver_code=driver_code,
                win_probability=win_probabilities.get(driver_code, 0),
                feature_contributions=contributions[:10],
                base_value=0.05,  # 假設基準勝率 5%
                total_drivers=len(driver_codes)
            )
            
        return explanations
        
    def format_explanation(self, explanation: SHAPExplanation, language: str = "zh") -> str:
        """
        格式化 SHAP 解釋為可讀字串
        
        Args:
            explanation: SHAP 解釋結果
            language: 語言 ("zh" 或 "en")
            
        Returns:
            格式化的字串
        """
        lines = []
        
        if language == "zh":
            lines.append(f"=== {explanation.driver_code} 勝率分析 ===")
            lines.append(f"勝率: {explanation.win_probability*100:.1f}%")
            lines.append(f"基準值: {explanation.base_value*100:.1f}%")
            lines.append("\n主要影響因素:")
            
            for feat_name, contrib in explanation.feature_contributions[:7]:
                label = self.feature_labels.get(feat_name, feat_name)
                sign = "+" if contrib > 0 else ""
                lines.append(f"  {label}: {sign}{contrib*100:.1f}%")
        else:
            lines.append(f"=== {explanation.driver_code} Win Probability Analysis ===")
            lines.append(f"Win Prob: {explanation.win_probability*100:.1f}%")
            lines.append(f"Base Value: {explanation.base_value*100:.1f}%")
            lines.append("\nTop Contributing Factors:")
            
            for feat_name, contrib in explanation.feature_contributions[:7]:
                sign = "+" if contrib > 0 else ""
                lines.append(f"  {feat_name}: {sign}{contrib*100:.1f}%")
                
        return "\n".join(lines)


# ============================================================================
# 動態機率計算器 (v3.0 新增)
# ============================================================================
@dataclass
class DynamicProbabilityConfig:
    """動態機率計算配置"""
    # Gap 衰減係數 (lambda): gap_factor = exp(-gap / lambda)
    gap_decay_lambda: float = 8.0  # 8 秒後機率降至 1/e
    
    # 剩餘圈數因子: 比賽後期翻盤難度增加
    laps_importance_exponent: float = 1.5
    
    # 進站圈檢測閾值 (秒)
    pit_lap_threshold: float = 110.0  # 1:50
    
    # 車隊/車手影響比例 (基於學術研究)
    constructor_weight: float = 0.64  # 64% 來自車隊
    driver_weight: float = 0.36  # 36% 來自車手
    
    # Softmax 溫度參數
    softmax_temperature: float = 2.0
    
    # 最小勝率 (防止極端值)
    min_win_prob: float = 0.001
    max_win_prob: float = 0.999


class DynamicProbabilityCalculator:
    """
    動態勝率計算器
    
    基於以下研究和工程實踐:
    1. arXiv:2508.00200 - F1 結果預測的車隊/車手分解
    2. 賽車策略工程中的即時勝率評估方法
    3. 蒙地卡羅模擬中的狀態轉移機率
    """
    
    def __init__(self, config: DynamicProbabilityConfig = None):
        self.config = config or DynamicProbabilityConfig()
        
        # 歷史圈時記錄 (用於進站圈檢測)
        self._lap_time_history: Dict[str, List[float]] = {}
        
    def reset_history(self):
        """重置歷史記錄 (新比賽開始時調用)"""
        self._lap_time_history.clear()
        
    def update_lap_time(self, driver_num: str, lap_time: float):
        """更新車手圈時歷史"""
        if driver_num not in self._lap_time_history:
            self._lap_time_history[driver_num] = []
        self._lap_time_history[driver_num].append(lap_time)
        # 只保留最近 10 圈
        if len(self._lap_time_history[driver_num]) > 10:
            self._lap_time_history[driver_num].pop(0)
            
    def is_pit_lap(self, driver_num: str, lap_time: float) -> bool:
        """
        檢測是否為進站圈
        
        Args:
            driver_num: 車手編號
            lap_time: 當前圈時 (秒)
            
        Returns:
            是否為進站圈
        """
        # 方法 1: 絕對閾值
        if lap_time > self.config.pit_lap_threshold:
            return True
            
        # 方法 2: 相對於歷史平均
        history = self._lap_time_history.get(driver_num, [])
        if len(history) >= 3:
            avg_lap_time = np.mean(history[-3:])
            # 如果圈時比平均慢 20 秒以上，視為進站圈
            if lap_time > avg_lap_time + 20:
                return True
                
        return False
        
    def calculate_gap_factor(self, gap_to_leader: float) -> float:
        """
        計算差距因子
        
        差距越大，追上領先者的機率越低
        使用指數衰減模型: factor = exp(-gap / lambda)
        
        Args:
            gap_to_leader: 與領先者的差距 (秒)
            
        Returns:
            差距因子 [0, 1]，1 表示領先者，越小表示追上機率越低
        """
        if gap_to_leader <= 0:
            return 1.0
        return np.exp(-gap_to_leader / self.config.gap_decay_lambda)
        
    def calculate_laps_factor(self, laps_remaining: int, total_laps: int) -> float:
        """
        計算剩餘圈數因子
        
        比賽後期翻盤難度增加，領先者優勢更大
        
        Args:
            laps_remaining: 剩餘圈數
            total_laps: 總圈數
            
        Returns:
            剩餘圈數因子 [0, 1]，越小表示翻盤機會越少
        """
        if total_laps <= 0:
            return 0.5
        race_progress = 1 - (laps_remaining / total_laps)  # 0 -> 1
        # 比賽越後期，因子越小，表示翻盤機會越少
        return 1 - (race_progress ** self.config.laps_importance_exponent) * 0.5
        
    def calculate_dynamic_win_probability(
        self,
        predicted_position: float,
        gap_to_leader: float,
        laps_remaining: int,
        total_laps: int,
        is_pit_lap: bool = False,
        driver_quality: float = 0.5,
        team_quality: float = 0.5
    ) -> Dict[str, float]:
        """
        計算動態勝率
        
        整合多個因素計算最終勝率:
        1. XGBoost 預測位置 (基礎分數)
        2. gap_to_leader (差距因子)
        3. laps_remaining (時間因子)
        4. 進站圈標記 (特殊處理)
        5. 車手/車隊品質 (歷史因子)
        
        Args:
            predicted_position: XGBoost 預測的位置
            gap_to_leader: 與領先者差距 (秒)
            laps_remaining: 剩餘圈數
            total_laps: 總圈數
            is_pit_lap: 是否為進站圈
            driver_quality: 車手品質 [0, 1]
            team_quality: 車隊品質 [0, 1]
            
        Returns:
            {'p1': 勝率, 'p2': 前二率, 'p3': 領獎台率, 'base_score': 基礎分數}
        """
        # 1. 基礎分數: 基於預測位置的 sigmoid
        # 預測位置 1 -> 分數 ~1, 預測位置 20 -> 分數 ~0
        base_score = 1 / (1 + np.exp((predicted_position - 5) * 0.5))
        
        # 2. 差距因子
        gap_factor = self.calculate_gap_factor(gap_to_leader)
        
        # 3. 剩餘圈數因子 (只影響非領先者)
        laps_factor = self.calculate_laps_factor(laps_remaining, total_laps)
        
        # 4. 車手/車隊品質因子
        quality_factor = (
            self.config.driver_weight * driver_quality +
            self.config.constructor_weight * team_quality
        )
        # 標準化為 [0.5, 1.5] 範圍
        quality_factor = 0.5 + quality_factor
        
        # 5. 進站圈處理: 暫時降低權重，但不完全歸零
        if is_pit_lap:
            pit_adjustment = 0.3  # 進站圈期間機率降低
        else:
            pit_adjustment = 1.0
            
        # 6. 組合計算 P1
        if gap_to_leader <= 0:
            # 領先者: 勝率主要取決於剩餘圈數和進站因素
            raw_p1 = base_score * (0.7 + 0.3 * (1 - laps_factor)) * quality_factor * pit_adjustment
        else:
            # 追趕者: 勝率取決於差距、剩餘圈數和品質
            raw_p1 = base_score * gap_factor * laps_factor * quality_factor * pit_adjustment
            
        # 7. 限制範圍
        p1 = np.clip(raw_p1, self.config.min_win_prob, self.config.max_win_prob)
        
        # 8. P2 和 P3 (基於預測位置的累積機率)
        p2 = 1 / (1 + np.exp((predicted_position - 2.5) * 0.8)) * pit_adjustment
        p3 = 1 / (1 + np.exp((predicted_position - 3.5) * 0.6)) * pit_adjustment
        
        return {
            'p1': float(p1),
            'p2': float(np.clip(p2, self.config.min_win_prob, self.config.max_win_prob)),
            'p3': float(np.clip(p3, self.config.min_win_prob, self.config.max_win_prob)),
            'base_score': float(base_score),
            'gap_factor': float(gap_factor),
            'laps_factor': float(laps_factor),
        }
        
    def normalize_probabilities_softmax(
        self,
        raw_probabilities: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        使用 Sinkhorn-Knopp 算法創建雙隨機矩陣歸一化
        
        確保：
        1. 每位車手的 P1+P2+P3+...+P20 = 100% (行加總)
        2. 所有車手的 P1 加總 = 100% (列加總)
        3. 所有車手的 P2 加總 = 100% (列加總)
        ... 以此類推
        
        Args:
            raw_probabilities: {driver_num: {'p1': raw_p1, 'p2': raw_p2, 'p3': raw_p3, ...}}
            
        Returns:
            雙隨機矩陣歸一化後的機率
        """
        if not raw_probabilities:
            return {}
        
        driver_nums = list(raw_probabilities.keys())
        n_drivers = len(driver_nums)
        
        # 構建完整的機率矩陣 (n_drivers x n_positions)
        # 使用預測位置生成每個車手獲得各個名次的原始機率
        n_positions = min(n_drivers, 20)  # 最多 20 個名次
        
        # 初始化矩陣
        prob_matrix = np.zeros((n_drivers, n_positions))
        
        for i, dn in enumerate(driver_nums):
            raw = raw_probabilities[dn]
            predicted_pos = raw.get('predicted_pos', 10)
            
            # 為每個位置計算機率 (基於預測位置的高斯分佈)
            for pos in range(n_positions):
                # 預測位置越接近，機率越高
                distance = abs((pos + 1) - predicted_pos)
                prob_matrix[i, pos] = np.exp(-distance * 0.5)
        
        # Sinkhorn-Knopp 迭代 (使矩陣成為雙隨機矩陣)
        for _ in range(50):  # 最多 50 次迭代
            # 行歸一化 (每位車手的機率加總 = 1)
            row_sums = prob_matrix.sum(axis=1, keepdims=True)
            row_sums = np.where(row_sums > 0, row_sums, 1)
            prob_matrix = prob_matrix / row_sums
            
            # 列歸一化 (每個名次的機率加總 = 1)
            col_sums = prob_matrix.sum(axis=0, keepdims=True)
            col_sums = np.where(col_sums > 0, col_sums, 1)
            prob_matrix = prob_matrix / col_sums
        
        # 最後一次行歸一化確保每位車手加總 = 100%
        row_sums = prob_matrix.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums > 0, row_sums, 1)
        prob_matrix = prob_matrix / row_sums
        
        # 組裝結果
        result = {}
        for i, dn in enumerate(driver_nums):
            result[dn] = {
                'p1': float(prob_matrix[i, 0]),  # P1 機率
                'p2': float(prob_matrix[i, 1]) if n_positions > 1 else 0.0,  # P2 機率
                'p3': float(prob_matrix[i, 2]) if n_positions > 2 else 0.0,  # P3 機率
                'raw_p1': raw_probabilities[dn]['p1'],  # 保留原始值供調試
                'position_probs': prob_matrix[i, :].tolist(),  # 完整的位置機率分佈
            }
            
        return result


# ============================================================================
# 常量定義
# ============================================================================

# 輪胎類型映射
TYRE_COMPOUND_MAP = {
    'SOFT': 1, 'S': 1,
    'MEDIUM': 2, 'M': 2,
    'HARD': 3, 'H': 3,
    'INTERMEDIATE': 4, 'I': 4,
    'WET': 5, 'W': 5,
    'UNKNOWN': 0, '?': 0
}

# 賽道狀態映射
TRACK_STATUS_MAP = {
    'GREEN': 1, '1': 1,
    'YELLOW': 2, '2': 2,
    'SC': 3, '4': 3,
    'VSC': 4, '6': 4, '7': 4,
    'RED': 5, '5': 5,
}

# 車隊評級 (基於 2024-2025 賽季表現)
DEFAULT_TEAM_RATINGS = {
    'red_bull': 0.95,
    'ferrari': 0.88,
    'mclaren': 0.90,
    'mercedes': 0.85,
    'aston_martin': 0.70,
    'alpine': 0.55,
    'williams': 0.50,
    'rb': 0.55,  # RB (前 AlphaTauri)
    'kick_sauber': 0.45,
    'haas': 0.50,
}

# 頂級車手評級
DEFAULT_DRIVER_RATINGS = {
    'VER': 0.98,  # Verstappen
    'HAM': 0.92,  # Hamilton
    'LEC': 0.90,  # Leclerc
    'NOR': 0.88,  # Norris
    'SAI': 0.85,  # Sainz
    'RUS': 0.84,  # Russell
    'PIA': 0.82,  # Piastri
    'ALO': 0.85,  # Alonso
    'PER': 0.78,  # Perez
    'GAS': 0.75,  # Gasly
    # 其他車手預設 0.70
}


class LiveWinProbabilityPredictor:
    """
    即時勝率預測器 (v3.1)
    
    整合預訓練的 XGBoost 模型，在每圈提供動態勝率預測。
    
    v3.1 新功能:
    - SHAP 可解釋性：解釋為什麼預測該車手勝率高/低
    - 賽道適應性因子：考慮車手在特定賽道的歷史表現
    
    v3.0 功能:
    - 動態機率計算，考慮 gap_to_leader、laps_remaining
    - 進站圈檢測和特殊處理
    - 車隊/車手品質因子
    - Softmax 歸一化確保機率總和為 1
    """
    
    # 特徵順序（必須與訓練時一致）- v2 增加了衍生特徵
    FEATURE_COLUMNS = [
        'position',
        'gap_to_leader',
        'gap_to_ahead',
        'lap_time',
        'best_lap_time',
        'tyre_compound',
        'tyre_age',
        'pit_count',
        'laps_remaining',
        'track_status',
        'air_temp',
        'rainfall',
        'driver_win_rate',
        'driver_podium_rate',
        'team_rating',
        'circuit_overtake_rate',
        'circuit_sc_rate',
        'qualifying_position',
        # v2 新增特徵
        'position_delta',
        'log_gap',
        'race_progress',
    ]
    
    def __init__(self, config: DynamicProbabilityConfig = None):
        """初始化預測器"""
        self.model = None
        self.model_loaded = False
        self.feature_importance = None
        
        # v3.0: 動態機率計算器
        self.dynamic_calculator = DynamicProbabilityCalculator(config)
        
        # v3.1: SHAP 解釋器
        self.shap_explainer = SHAPExplainer(feature_names=self.FEATURE_COLUMNS)
        self._shap_enabled = SHAP_AVAILABLE
        
        # v3.1: 賽道適應性計算器
        self.circuit_affinity_calculator = CircuitAffinityCalculator()
        self._current_circuit: str = ""
        
        # v3.2: FP3/Q 補償計算器
        self.fp3q_compensator = FP3QCompensationCalculator()
        self._fp3q_data_loaded = False
        
        # v3.4: 輪胎策略計算器
        self.tyre_strategy_calculator = TyreStrategyCalculator()
        
        # v3.4: 進站計算器
        self.pit_stop_calculator = PitStopCalculator()
        self._driver_pit_history: Dict[str, List[PitStopEvent]] = {}  # 進站歷史
        
        # 歷史統計（預設值，可以從外部載入）
        self._driver_stats = {}  # {driver_code: {'win_rate': 0.5, 'podium_rate': 0.7}}
        self._team_ratings = {}  # {team_name: rating}
        self._circuit_stats = {}  # {circuit: {'overtake_rate': 0.5, 'sc_rate': 0.3}}
        
        # v3.0: 車手/車隊品質評級
        self._driver_quality = DEFAULT_DRIVER_RATINGS.copy()
        self._team_quality = DEFAULT_TEAM_RATINGS.copy()
        
        # v3.0: 調試模式
        self._debug_mode = True
        self._last_lap_debug = -1
        
        # v3.1: 緩存最新預測數據供 SHAP 使用
        self._last_prediction_features: Dict[str, np.ndarray] = {}
        self._last_prediction_results: Dict[str, Dict] = {}
        
        # v3.2: Q 位置數據 (當前賽事)
        self._current_q_positions: Dict[str, int] = {}  # {driver_code: q_position}
        
    def load_model(self, model_path: str) -> bool:
        """
        載入預訓練模型
        
        Args:
            model_path: 模型檔案路徑 (.pkl)
            
        Returns:
            是否載入成功
        """
        try:
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found: {model_path}")
                return False
                
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                
            self.model = model_data.get('model')
            self.feature_importance = model_data.get('feature_importance', {})
            self.model_loaded = True
            
            # v3.1: 初始化 SHAP 解釋器
            if self._shap_enabled and self.model is not None:
                self.shap_explainer.setup(self.model, self.FEATURE_COLUMNS)
            
            logger.info(f"Model loaded from: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def load_fp3q_compensation_data(self, csv_path: str) -> bool:
        """
        載入 FP3/Q 補償數據 (v3.2)
        
        Args:
            csv_path: CSV 檔案路徑
            
        Returns:
            是否載入成功
        """
        self._fp3q_data_loaded = self.fp3q_compensator.load_compensation_data(csv_path)
        return self._fp3q_data_loaded
    
    def set_qualifying_positions(self, q_positions: Dict[str, int]):
        """
        設置當前賽事的排位結果 (v3.2)
        
        Args:
            q_positions: {driver_code: position} 例如 {'VER': 1, 'LEC': 2, 'NOR': 3}
        """
        self._current_q_positions = q_positions
        logger.info(f"Set qualifying positions for {len(q_positions)} drivers")
    
    def set_circuit(self, circuit_name: str):
        """
        設置當前賽道 (v3.1)
        
        Args:
            circuit_name: 賽道名稱
        """
        self._current_circuit = circuit_name
        logger.info(f"Circuit set to: {circuit_name}")
    
    def set_driver_stats(self, driver_stats: Dict[str, Dict[str, float]]):
        """設置車手歷史統計"""
        self._driver_stats = driver_stats
        
    def set_team_ratings(self, team_ratings: Dict[str, float]):
        """設置車隊評級"""
        self._team_ratings = team_ratings
        
    def set_circuit_stats(self, circuit_stats: Dict[str, Dict[str, float]]):
        """設置賽道統計"""
        self._circuit_stats = circuit_stats
    
    def predict_for_snapshot(
        self,
        snapshot: Dict[str, Any],
        tyre_state: Dict[str, Dict[str, Any]],
        race_info: Dict[str, Any],
        weather: Dict[str, Any] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        為當前快照預測所有車手的勝率 (v3.1 + SHAP + CircuitAffinity)
        
        Args:
            snapshot: 當前時間快照 {'drivers': {driver_num: {...}}, 'race_time': ...}
            tyre_state: 輪胎狀態 {driver_num: {'compound': 'MEDIUM', 'stint_count': 1, ...}}
            race_info: 比賽資訊 {'total_laps': 53, 'current_lap': 30, 'track_status': 'GREEN', 'circuit': 'Suzuka'}
            weather: 天氣資訊 {'air_temp': 25, 'rainfall': False}
            
        Returns:
            {driver_num: {'win_prob': 0.72, 'podium_prob': 0.95, 'predicted_pos': 1.2, 'circuit_affinity': 1.2}}
        """
        if not self.model_loaded:
            logger.warning("Model not loaded, returning empty predictions")
            return {}
            
        drivers = snapshot.get('drivers', {})
        if not drivers:
            return {}
        
        current_lap = race_info.get('current_lap', 0)
        total_laps = race_info.get('total_laps', 53)
        laps_remaining = max(0, total_laps - current_lap)
        
        # v3.1: 獲取賽道名稱
        circuit_name = race_info.get('circuit', self._current_circuit)
        if circuit_name:
            self._current_circuit = circuit_name
        
        # v3.0: 收集所有車手的特徵和額外資訊
        all_features = []
        driver_nums = []
        driver_codes = []
        driver_extra_info = []
        
        for driver_num, driver_data in drivers.items():
            features = self._extract_features(
                driver_num, driver_data, tyre_state, race_info, weather
            )
            all_features.append(features)
            driver_nums.append(driver_num)
            
            # 額外資訊用於動態計算
            gap_to_leader = self._parse_gap(driver_data.get('gap_to_leader', 0))
            lap_time = self._parse_lap_time(driver_data.get('last_lap_time', ''))
            driver_code = driver_data.get('driver_tla', driver_num)
            driver_codes.append(driver_code)
            
            # 更新圈時歷史並檢測進站圈
            self.dynamic_calculator.update_lap_time(driver_num, lap_time)
            is_pit_lap = self.dynamic_calculator.is_pit_lap(driver_num, lap_time)
            
            # v3.1: 獲取賽道適應性
            circuit_affinity = self.circuit_affinity_calculator.get_circuit_affinity(
                driver_code, self._current_circuit
            )
            
            # v3.3: 獲取當前位置 (用於動態 Q 補償)
            current_position = driver_data.get('position', 10)
            if isinstance(current_position, str):
                try:
                    current_position = int(current_position)
                except:
                    current_position = 10
            
            # v3.3: 獲取 Q 位置
            q_position = self._current_q_positions.get(driver_code, current_position)
            
            # v3.3: 動態 Q 補償 (前 10 圈有效，被超車歸零，賽道權重)
            fp3q_compensation = self.fp3q_compensator.get_dynamic_compensation(
                driver_code=driver_code,
                circuit=self._current_circuit,
                q_position=q_position,
                current_position=current_position,
                current_lap=current_lap,
                total_laps=total_laps,
            )
            
            # v3.4: 輪胎策略因子
            tyre_info = tyre_state.get(driver_num, {})
            driver_tyre = TyreState(
                compound=tyre_info.get('compound', 'MEDIUM'),
                age=tyre_info.get('tyre_age', 0) or 0,
                stint_number=tyre_info.get('stint_count', 1),
            )
            tyre_advantage = self.tyre_strategy_calculator.get_tyre_advantage_factor(
                driver_tyre=driver_tyre,
                rival_tyre=None,  # 與平均比較
                laps_remaining=laps_remaining,
            )
            
            driver_extra_info.append({
                'gap_to_leader': gap_to_leader,
                'lap_time': lap_time,
                'driver_code': driver_code,
                'is_pit_lap': is_pit_lap,
                'circuit_affinity': circuit_affinity,
                'q_position': q_position,  # v3.3
                'current_position': current_position,  # v3.3: 新增
                'fp3q_compensation': fp3q_compensation,  # v3.3: 動態版本
                'tyre_advantage': tyre_advantage,  # v3.4: 新增
                'tyre_state': driver_tyre,  # v3.4: 新增
            })
        
        if not all_features:
            return {}
            
        # XGBoost 批量預測位置
        X = np.array(all_features)
        predicted_positions = self.model.predict(X)
        
        # v3.1: 緩存特徵供 SHAP 使用
        self._last_prediction_features = {
            driver_codes[i]: X[i] for i in range(len(driver_codes))
        }
        
        # v3.0: 使用動態計算器計算機率
        raw_probabilities = {}
        for i, driver_num in enumerate(driver_nums):
            extra = driver_extra_info[i]
            driver_code = extra['driver_code']
            
            # 獲取車手和車隊品質
            driver_quality = self._driver_quality.get(driver_code, 0.70)
            team_quality = 0.70  # TODO: 從 driver_data 中獲取車隊名稱
            
            # v3.1: 賽道適應性調整車手品質
            circuit_affinity = extra['circuit_affinity']
            
            # v3.2: FP3/Q 補償因子
            fp3q_factor = extra['fp3q_compensation']
            
            # v3.4: 輪胎策略因子
            tyre_factor = extra['tyre_advantage']
            
            # 綜合調整因子 (賽道適應性 * FP3/Q 補償 * 輪胎優勢)
            adjusted_driver_quality = driver_quality * circuit_affinity * fp3q_factor * tyre_factor
            
            # 計算動態機率
            probs = self.dynamic_calculator.calculate_dynamic_win_probability(
                predicted_position=predicted_positions[i],
                gap_to_leader=extra['gap_to_leader'],
                laps_remaining=laps_remaining,
                total_laps=total_laps,
                is_pit_lap=extra['is_pit_lap'],
                driver_quality=adjusted_driver_quality,  # v3.4: 使用綜合調整品質
                team_quality=team_quality,
            )
            
            raw_probabilities[driver_num] = {
                'p1': probs['p1'],
                'p2': probs['p2'],
                'p3': probs['p3'],
                'predicted_pos': predicted_positions[i],
                'is_pit_lap': extra['is_pit_lap'],
                'gap_factor': probs['gap_factor'],
                'laps_factor': probs['laps_factor'],
                'circuit_affinity': circuit_affinity,  # v3.1
                'q_position': extra['q_position'],  # v3.2: 新增
                'fp3q_compensation': fp3q_factor,  # v3.2: 新增
                'tyre_advantage': tyre_factor,  # v3.4: 新增
            }
        
        # v3.0: Sinkhorn-Knopp 雙隨機矩陣歸一化
        normalized_probs = self.dynamic_calculator.normalize_probabilities_softmax(raw_probabilities)
        
        # 組裝最終結果
        results = {}
        for driver_num in driver_nums:
            norm = normalized_probs.get(driver_num, {})
            raw = raw_probabilities.get(driver_num, {})
            
            results[driver_num] = {
                'win_prob': norm.get('p1', raw.get('p1', 0)),
                'p2_prob': norm.get('p2', raw.get('p2', 0)),
                'podium_prob': norm.get('p3', raw.get('p3', 0)),
                'predicted_pos': raw.get('predicted_pos', 10),
                'is_pit_lap': raw.get('is_pit_lap', False),
                'circuit_affinity': raw.get('circuit_affinity', 1.0),  # v3.1
                'q_position': raw.get('q_position', 10),  # v3.2
                'fp3q_compensation': raw.get('fp3q_compensation', 1.0),  # v3.3
                'tyre_advantage': raw.get('tyre_advantage', 1.0),  # v3.4
            }
        
        # v3.1: 緩存預測結果
        self._last_prediction_results = results
        
        # v3.4: 調試輸出 (顯示賽道適應性 + FP3/Q 補償 + 輪胎優勢)
        if self._debug_mode and 30 <= current_lap <= 40 and current_lap != self._last_lap_debug:
            self._last_lap_debug = current_lap
            print(f"\n[PREDICTOR v3.4] Lap {current_lap} / {total_laps} @ {self._current_circuit}:")
            
            # 按 win_prob 排序顯示前 5 名
            sorted_results = sorted(results.items(), key=lambda x: x[1]['win_prob'], reverse=True)[:5]
            for driver_num, data in sorted_results:
                extra = next((e for i, e in enumerate(driver_extra_info) if driver_nums[i] == driver_num), {})
                pit_flag = " [PIT]" if data.get('is_pit_lap') else ""
                gap = extra.get('gap_to_leader', 0)
                affinity = data.get('circuit_affinity', 1.0)
                affinity_str = f" CA:{affinity:.2f}" if abs(affinity - 1.0) > 0.05 else ""
                tyre_adv = data.get('tyre_advantage', 1.0)
                tyre_str = f" TY:{tyre_adv:.2f}" if abs(tyre_adv - 1.0) > 0.01 else ""
                print(f"  {driver_num}: P1%={data['win_prob']*100:.1f}%, pos={data['predicted_pos']:.2f}, gap={gap:.1f}s{pit_flag}{affinity_str}{tyre_str}")
            
        return results
    
    def _extract_features(
        self,
        driver_num: str,
        driver_data: Dict[str, Any],
        tyre_state: Dict[str, Dict[str, Any]],
        race_info: Dict[str, Any],
        weather: Dict[str, Any] = None
    ) -> List[float]:
        """
        提取單個車手的特徵向量
        
        Returns:
            21 維特徵向量 (v2 格式)
        """
        weather = weather or {}
        tyre_info = tyre_state.get(driver_num, {})
        
        # 基礎特徵
        position = driver_data.get('position', 10)
        gap_to_leader = self._parse_gap(driver_data.get('gap_to_leader', 0))
        gap_to_ahead = self._parse_gap(driver_data.get('gap_to_ahead', 0))
        
        # 圈時
        lap_time = self._parse_lap_time(driver_data.get('last_lap_time', ''))
        best_lap_time = self._parse_lap_time(driver_data.get('best_lap_time', ''))
        
        # 輪胎
        compound_str = tyre_info.get('compound', 'UNKNOWN')
        tyre_compound = TYRE_COMPOUND_MAP.get(compound_str.upper(), 0)
        tyre_age = tyre_info.get('tyre_age', 0) or 0
        pit_count = tyre_info.get('stint_count', 1) - 1  # stint_count - 1 = pit_count
        if pit_count < 0:
            pit_count = 0
            
        # 比賽資訊
        total_laps = race_info.get('total_laps', 53)
        current_lap = race_info.get('current_lap', 1)
        laps_remaining = max(0, total_laps - current_lap)
        
        track_status_str = str(race_info.get('track_status', '1'))
        track_status = TRACK_STATUS_MAP.get(track_status_str, 1)
        
        # 天氣
        air_temp = weather.get('air_temp', 25.0)
        rainfall = 1 if weather.get('rainfall', False) else 0
        
        # 歷史統計（使用預設值）
        driver_code = driver_data.get('driver_tla', driver_num)
        driver_stats = self._driver_stats.get(driver_code, {})
        driver_win_rate = driver_stats.get('win_rate', 0.0)
        driver_podium_rate = driver_stats.get('podium_rate', 0.0)
        
        team_rating = 5.0  # 預設值
        circuit_overtake_rate = 0.5
        circuit_sc_rate = 0.3
        
        # 注意：訓練數據中 qualifying_position 全部是 10（placeholder）
        qualifying_position = 10  # 暫時使用固定值，與訓練數據一致
        
        # v2 新增特徵
        position_delta = qualifying_position - position
        log_gap = np.log1p(abs(gap_to_leader))
        race_progress = 1 - (laps_remaining / max(total_laps, 1))
        
        # 組裝特徵向量（順序必須與 FEATURE_COLUMNS 一致）
        features = [
            float(position),
            float(gap_to_leader),
            float(gap_to_ahead),
            float(lap_time),
            float(best_lap_time),
            float(tyre_compound),
            float(tyre_age),
            float(pit_count),
            float(laps_remaining),
            float(track_status),
            float(air_temp),
            float(rainfall),
            float(driver_win_rate),
            float(driver_podium_rate),
            float(team_rating),
            float(circuit_overtake_rate),
            float(circuit_sc_rate),
            float(qualifying_position),
            # v2 新增特徵
            float(position_delta),
            float(log_gap),
            float(race_progress),
        ]
        
        return features
    
    def _parse_gap(self, gap_value: Any) -> float:
        """解析差距值"""
        if gap_value is None:
            return 0.0
        if isinstance(gap_value, (int, float)):
            return float(gap_value)
        if isinstance(gap_value, str):
            # 處理字串格式如 "+1.234", "+1.234s", "1L"
            gap_value = gap_value.strip()
            if gap_value.startswith('+'):
                gap_value = gap_value[1:]
            # 移除尾部的 's' (秒)
            if gap_value.endswith('s'):
                gap_value = gap_value[:-1]
            if 'L' in gap_value.upper():
                # 被套圈，估算為 90 秒/圈
                try:
                    laps = int(gap_value.upper().replace('L', '').strip())
                    return laps * 90.0
                except:
                    return 90.0
            try:
                return float(gap_value)
            except:
                return 0.0
        return 0.0
    
    def _parse_lap_time(self, lap_time_str: str) -> float:
        """解析圈時字串為秒數"""
        if not lap_time_str:
            return 90.0  # 預設值
        try:
            if ':' in lap_time_str:
                parts = lap_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(lap_time_str)
        except:
            return 90.0
    
    def _convert_to_probabilities(self, predicted_positions: np.ndarray) -> List[Dict[str, float]]:
        """
        [已棄用] 舊版固定 Sigmoid 機率計算
        
        v3.0 已改用 DynamicProbabilityCalculator
        此方法僅保留供回退測試使用
        """
        logger.warning("Using deprecated _convert_to_probabilities. Consider using DynamicProbabilityCalculator.")
        
        results = []
        sorted_indices = np.argsort(predicted_positions)
        ranks = np.empty_like(sorted_indices)
        ranks[sorted_indices] = np.arange(1, len(predicted_positions) + 1)
        
        for i, pred_pos in enumerate(predicted_positions):
            rank = ranks[i]
            p1 = 1 / (1 + np.exp((rank - 1.5) * 1.8))
            p2 = 1 / (1 + np.exp((rank - 2.5) * 1.5))
            p3 = 1 / (1 + np.exp((rank - 3.5) * 1.2))
            
            results.append({
                'p1': min(1.0, max(0.0, p1)),
                'p2': min(1.0, max(0.0, p2)),
                'p3': min(1.0, max(0.0, p3)),
            })
            
        return results
    
    def reset_for_new_race(self):
        """重置預測器狀態（新比賽開始時調用）"""
        self.dynamic_calculator.reset_history()
        self._last_lap_debug = -1
        self._last_prediction_features.clear()
        self._last_prediction_results.clear()
        self._current_circuit = ""
        
    def set_debug_mode(self, enabled: bool):
        """設置調試模式"""
        self._debug_mode = enabled
        
    # =========================================================================
    # v3.1 SHAP 解釋方法
    # =========================================================================
    
    def explain_prediction(self, driver_code: str, language: str = "zh") -> Optional[str]:
        """
        獲取特定車手的 SHAP 解釋
        
        Args:
            driver_code: 車手代碼 (例如 "VER")
            language: 語言 ("zh" 或 "en")
            
        Returns:
            格式化的解釋字串，或 None 如果無法生成
        """
        if driver_code not in self._last_prediction_features:
            logger.warning(f"No prediction data found for {driver_code}")
            return None
            
        # 構建 SHAP 所需數據
        features = np.array([self._last_prediction_features[driver_code]])
        win_probs = {
            dc: self._last_prediction_results.get(dn, {}).get('win_prob', 0)
            for dn, dc_info in self._last_prediction_results.items()
            for dc in [driver_code] if dc_info  # 簡化處理
        }
        
        # 從緩存的結果中找到對應的 win_prob
        for driver_num, result in self._last_prediction_results.items():
            if driver_code in self._last_prediction_features:
                win_probs[driver_code] = result.get('win_prob', 0)
                break
        
        explanations = self.shap_explainer.explain(
            features, 
            [driver_code], 
            win_probs
        )
        
        if driver_code in explanations:
            return self.shap_explainer.format_explanation(
                explanations[driver_code], 
                language
            )
        return None
        
    def explain_all_predictions(self, top_n: int = 5, language: str = "zh") -> Dict[str, str]:
        """
        獲取所有車手（或前 N 名）的 SHAP 解釋
        
        Args:
            top_n: 返回前 N 名的解釋
            language: 語言
            
        Returns:
            {driver_code: 解釋字串}
        """
        if not self._last_prediction_results:
            return {}
            
        # 按勝率排序
        sorted_drivers = sorted(
            self._last_prediction_results.items(),
            key=lambda x: x[1].get('win_prob', 0),
            reverse=True
        )[:top_n]
        
        results = {}
        for driver_num, result in sorted_drivers:
            # 尋找對應的 driver_code
            for dc, features in self._last_prediction_features.items():
                explanation = self.explain_prediction(dc, language)
                if explanation:
                    results[dc] = explanation
                break
                    
        return results
        
    def get_circuit_affinity_info(self, driver_code: str) -> Dict[str, Any]:
        """
        獲取車手的賽道適應性資訊
        
        Args:
            driver_code: 車手代碼
            
        Returns:
            {'circuit': 賽道名, 'affinity': 適應性值, 'circuit_type': 類型}
        """
        affinity = self.circuit_affinity_calculator.get_circuit_affinity(
            driver_code, self._current_circuit
        )
        circuit_type = self.circuit_affinity_calculator.get_circuit_type(self._current_circuit)
        
        return {
            'circuit': self._current_circuit,
            'affinity': affinity,
            'circuit_type': circuit_type,
            'is_favorable': affinity > 1.05,
            'is_unfavorable': affinity < 0.95,
        }


# 全域單例
_predictor_instance: Optional[LiveWinProbabilityPredictor] = None


def get_predictor(config: DynamicProbabilityConfig = None) -> LiveWinProbabilityPredictor:
    """
    獲取全域預測器實例
    
    Args:
        config: 動態機率計算配置 (可選)
        
    Returns:
        LiveWinProbabilityPredictor 實例
    """
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = LiveWinProbabilityPredictor(config)
        # 嘗試載入預設模型 (v2)
        default_model_paths = [
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "models", "win_probability_xgb_v2.pkl"
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "models", "win_probability_xgb_v1.pkl"
            ),
        ]
        for model_path in default_model_paths:
            if os.path.exists(model_path):
                _predictor_instance.load_model(model_path)
                break
    return _predictor_instance


def reset_predictor():
    """重置全域預測器實例"""
    global _predictor_instance
    _predictor_instance = None
