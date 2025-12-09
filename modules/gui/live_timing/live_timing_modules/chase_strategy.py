"""
Live Timing Chase Strategy
==========================

P2 追趕 P1 策略建議模組 - 分析追趕策略可行性。
顯示 5 種策略的追上機率、預計圈數、總優勢等資訊。

功能：
- 策略 1: 繼續當前輪胎 (輪胎齡優勢)
- 策略 2: 立即進站 Undercut
- 策略 3: 等待安全車機會
- 策略 4: 主動進站模擬 (用戶自定義)
- 策略 5: 雙重進站分析 (P1/P2 都進站的情境)

Author: F1T Team
Date: 2025-12-08
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import numpy as np
import math
import json
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QLabel, QPushButton, QDialog,
    QFormLayout, QSpinBox, QComboBox, QDialogButtonBox, QMenu, QAction,
    QFrame, QSizePolicy
)
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush, QFontMetrics, QPainterPath

# =============================================================================
# Color Constants (與 Driver Strategy 完全一致)
# =============================================================================
COLOR_BG = '#1a1a1a'
COLOR_CHART_BG = '#242424'     # 圖表背景顏色 (與 Driver Strategy 一致)
COLOR_GRID = '#3a3a3a'         # 網格線顏色 (與 Driver Strategy 一致)
COLOR_AXIS = '#888888'         # 座標軸顏色 (與 Driver Strategy 一致)
COLOR_TEXT = '#ffffff'         # 文字顏色 (與 Driver Strategy 一致)

# Gap Chart 專用顏色
COLOR_P2_ACTUAL = '#00FF00'    # 綠色 - P2 實際 Gap
COLOR_P1_ACTUAL = '#3671C6'    # 藍色 - P1 實際 Gap
COLOR_P2_PREDICT = '#FFCC00'   # 黃色 - P2 預測 Gap
COLOR_P1_PREDICT = '#FF8000'   # 橙色 - P1 預測 Gap
COLOR_CURRENT_LAP = '#FF3333'  # 紅色 - 當前圈數標記
COLOR_CATCHUP_LAP = '#4ECDC4'  # 青色 - 追上圈數標記
COLOR_PIT_MARKER = '#FFD700'   # 黃色 - Pit 標記 (與 Driver Strategy 一致)

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr

# 導入車手顏色
try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
except ImportError:
    COLOR_PALETTE_AVAILABLE = False
    color_palette_provider = None

# 輪胎顏色定義
COLOR_TYRE_SOFT = '#FF3333'      # Red
COLOR_TYRE_MEDIUM = '#FFCC00'    # Yellow
COLOR_TYRE_HARD = '#FFFFFF'      # White
COLOR_TYRE_INTERMEDIATE = '#00CC00'  # Green
COLOR_TYRE_WET = '#0066FF'       # Blue


# =============================================================================
# Constants
# =============================================================================

# 輪胎衰減率 (秒/圈)
TYRE_DEGRADATION_PER_LAP = 0.08

# [已廢棄] 進站損失 (秒) - 現在改用賽道專屬資料庫 (config/pit_loss_database.json)
# PIT_LOSS_NORMAL = 22.0
# PIT_LOSS_SC = 8.0

# 新胎優勢 (秒/圈)
NEW_TYRE_ADVANTAGE = {
    'SOFT': 1.5,
    'MEDIUM': 1.2,
    'HARD': 1.0
}

# 差距分類閾值 (秒)
GAP_CLOSE = 3.0
GAP_MEDIUM = 10.0
GAP_LARGE = 20.0

# 賽事名稱到賽道名稱的映射（與 Driver Strategy 完全一致）
RACE_TO_CIRCUIT_MAP = {
    'Qatar': 'Lusail',
    'Abu Dhabi': 'Yas_Marina',
    'Saudi Arabia': 'Jeddah',
    'Australia': 'Melbourne',
    'Japan': 'Suzuka',
    'China': 'Shanghai',
    'Emilia Romagna': 'Imola',
    'Canada': 'Montreal',
    'Spain': 'Barcelona',
    'Austria': 'Spielberg',
    'Great Britain': 'Silverstone',
    'Britain': 'Silverstone',
    'Hungary': 'Budapest',
    'Belgium': 'Spa',
    'Netherlands': 'Zandvoort',
    'Italy': 'Monza',
    'Azerbaijan': 'Baku',
    'United States': 'Austin',
    'USA': 'Austin',
    'Mexico': 'Mexico',
    'Brazil': 'Interlagos',
    'Las Vegas': 'Las_Vegas',
}


# =============================================================================
# Pit Loss Database Loader
# =============================================================================

def load_pit_loss_database() -> Dict[str, Any]:
    """載入賽道進站損失資料庫"""
    try:
        # 路徑: chase_strategy.py -> live_timing_modules -> live_timing -> gui -> modules -> 專案根目錄
        db_path = Path(__file__).parent.parent.parent.parent.parent / "config" / "pit_loss_database.json"
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[CHASE_STRATEGY] [WARNING] 無法載入 pit_loss_database.json: {e}")
        return {}

def get_pit_loss_for_circuit(circuit_name: str = None) -> Dict[str, float]:
    """
    獲取特定賽道的進站損失時間
    
    Args:
        circuit_name: 賽道名稱（例如 "Suzuka", "Monaco"）
    
    Returns:
        包含 green_flag, safety_car, virtual_safety_car 的字典
    """
    database = load_pit_loss_database()
    
    if not database or 'circuits' not in database:
        # 資料庫載入失敗，使用預設值
        return {
            'green_flag': 22.0,
            'safety_car': 11.0,
            'virtual_safety_car': 8.0
        }
    
    circuits = database['circuits']
    
    # 如果沒有指定賽道，使用預設值
    if not circuit_name:
        return {
            'green_flag': 22.0,
            'safety_car': 11.0,
            'virtual_safety_car': 8.0
        }
    
    # 嘗試各種賽道名稱變體
    circuit_variants = [
        circuit_name,
        circuit_name.title(),
        circuit_name.upper(),
        circuit_name.lower()
    ]
    
    for variant in circuit_variants:
        if variant in circuits:
            pit_times = circuits[variant].get('pit_loss_times', {})
            return {
                'green_flag': pit_times.get('green_flag', 22.0),
                'safety_car': pit_times.get('safety_car', 11.0),
                'virtual_safety_car': pit_times.get('virtual_safety_car', 8.0)
            }
    
    # 找不到賽道，使用預設值
    print(f"[CHASE_STRATEGY] [WARNING] 找不到賽道 '{circuit_name}' 的 pit_loss 資料，使用預設值")
    return {
        'green_flag': 22.0,
        'safety_car': 11.0,
        'virtual_safety_car': 8.0
    }


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class StrategyResult:
    """單一策略計算結果"""
    strategy_id: int
    name: str
    feasible: bool
    catchup_lap: Optional[int]  # 預計追上的圈數 (None = 無法追上)
    total_advantage: float       # 總優勢 (秒)
    drs_required: int           # 需要 DRS 次數
    rating: int                 # 推薦度 (1-3 星)
    details: str                # 詳細說明
    
    # 真實追趕數據 (用於圖表繪製)
    advantage_per_lap: float = 0.0  # 每圈優勢 (秒/圈)
    pit_loss: float = 0.0           # 進站損失 (秒)
    sc_lap_offset: int = 0          # 安全車圈數偏移


# =============================================================================
# Strategy Calculator
# =============================================================================

class StrategyCalculator:
    """策略計算引擎"""
    
    def __init__(self, circuit_name: str = None):
        self._total_laps = 58  # 預設總圈數
        self._circuit_name = circuit_name
        
        #  從資料庫載入賽道專屬的 pit_loss
        pit_loss_data = get_pit_loss_for_circuit(circuit_name)
        self._pit_loss_green = pit_loss_data['green_flag']
        self._pit_loss_sc = pit_loss_data['safety_car']
        self._pit_loss_vsc = pit_loss_data['virtual_safety_car']
        
        #  載入輪胎衰退資料庫（與 Driver Strategy 完全一致）
        self._tyre_deg_database = self._load_tyre_degradation_database()
        
        print(f"[CHASE_STRATEGY] [CIRCUIT] 賽道: {circuit_name or '預設'}")
        print(f"[CHASE_STRATEGY] [PIT_LOSS] Green: {self._pit_loss_green}s, SC: {self._pit_loss_sc}s, VSC: {self._pit_loss_vsc}s")
        
        # 調試輪胎衰退資料庫載入
        circuits_count = len(self._tyre_deg_database.get('circuits', {}))
        print(f"[CHASE_STRATEGY] [TYRE_DEG] Loaded {circuits_count} circuits from database")
    
    def _load_tyre_degradation_database(self) -> Dict[str, Any]:
        """載入輪胎衰退資料庫（與 Driver Strategy 完全一致）"""
        try:
            db_path = Path(__file__).parent.parent.parent.parent.parent / "config" / "tire_degradation_database.json"
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[CHASE_STRATEGY] [WARNING] 無法載入 tire_degradation_database.json: {e}")
            return {}
    
    def set_total_laps(self, total_laps: int):
        """設定總圈數"""
        self._total_laps = total_laps
    
    def _get_compound_degradation_rate(self, compound: str, tyre_age: int) -> float:
        """
        計算輪胎的即時衰退速度（秒/圈）
        使用與 Driver Strategy 完全一致的二次方程式模型
        
        Args:
            compound: 輪胎配方 (SOFT/MEDIUM/HARD)
            tyre_age: 輪胎齡（圈數）
            
        Returns:
            當前圈的衰退速度（秒/圈）
        """
        if not self._circuit_name:
            # 預設值（無賽道資訊時）
            default_base = {'SOFT': 0.08, 'MEDIUM': 0.06, 'HARD': 0.05}
            default_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001}
            base_rate = default_base.get(compound, 0.06)
            acceleration = default_accel.get(compound, 0.002)
        else:
            # 從資料庫獲取賽道專屬係數
            circuit_db_key = RACE_TO_CIRCUIT_MAP.get(self._circuit_name, self._circuit_name)
            circuits = self._tyre_deg_database.get('circuits', {})
            circuit_data = circuits.get(circuit_db_key, {})
            
            if circuit_data:
                base_degradation = circuit_data.get('base_degradation', {})
                degradation_acceleration = circuit_data.get('degradation_acceleration', {})
                
                compound_key = compound.upper() if compound else 'MEDIUM'
                base_rate = base_degradation.get(compound_key, 0.06)
                acceleration = degradation_acceleration.get(compound_key, 0.002)
            else:
                # 預設值
                default_base = {'SOFT': 0.08, 'MEDIUM': 0.06, 'HARD': 0.05}
                default_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001}
                base_rate = default_base.get(compound, 0.06)
                acceleration = default_accel.get(compound, 0.002)
        
        # 計算即時衰退速度（導數）
        # degradation(t) = base_rate * t + 0.5 * acceleration * t²
        # d(degradation)/dt = base_rate + acceleration * t
        instantaneous_degradation_rate = base_rate + acceleration * tyre_age
        
        return instantaneous_degradation_rate
    
    def _calculate_new_tyre_advantage(self, new_compound: str, old_compound: str, old_tyre_age: int) -> float:
        """
        計算新胎相對於舊胎的速度優勢（秒/圈）
        
        Args:
            new_compound: 新輪胎配方
            old_compound: 舊輪胎配方
            old_tyre_age: 舊輪胎齡
            
        Returns:
            新胎每圈優勢（正值 = 新胎更快）
        """
        # 新胎從 age=1 開始（剛換上）
        new_tyre_rate = self._get_compound_degradation_rate(new_compound, 1)
        old_tyre_rate = self._get_compound_degradation_rate(old_compound, old_tyre_age)
        
        # 配方抓地力優勢（與 Driver Strategy 一致）
        # 負值 = 更快（相對於 HARD 基準）
        grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0}
        new_grip = grip_advantage.get(new_compound.upper(), -0.25)
        old_grip = grip_advantage.get(old_compound.upper(), -0.25)
        
        # 計算兩個分量
        degradation_diff = old_tyre_rate - new_tyre_rate  # 衰退差異（正值 = 舊胎衰退更嚴重）
        grip_diff = old_grip - new_grip  # 配方差異（正值 = 新配方更快）
        
        # 總優勢 = (舊胎衰退速度 - 新胎衰退速度) + (舊胎抓地力 - 新胎抓地力)
        # 注意：grip_advantage 負值 = 更快，所以用 old_grip - new_grip
        # 例如：SOFT(-0.5) vs MEDIUM(-0.25) → (-0.25) - (-0.5) = +0.25 s/lap（SOFT 更快）
        advantage = degradation_diff + grip_diff
        
        return advantage
    
    def set_circuit(self, circuit_name: str):
        """
        設定賽道名稱並重新載入 pit_loss
        
        Args:
            circuit_name: 賽道名稱（例如 "Suzuka", "Monaco"）
        """
        self._circuit_name = circuit_name
        pit_loss_data = get_pit_loss_for_circuit(circuit_name)
        self._pit_loss_green = pit_loss_data['green_flag']
        self._pit_loss_sc = pit_loss_data['safety_car']
        self._pit_loss_vsc = pit_loss_data['virtual_safety_car']
        
        print(f"[CHASE_STRATEGY] [UPDATE_CIRCUIT] 更新賽道: {circuit_name}")
        print(f"[CHASE_STRATEGY] [PIT_LOSS] Green: {self._pit_loss_green}s, SC: {self._pit_loss_sc}s, VSC: {self._pit_loss_vsc}s")
    
    def calculate_all_strategies(
        self,
        current_lap: int,
        gap_seconds: float,
        p1_tyre_age: int,
        p2_tyre_age: int,
        p1_compound: str = 'MEDIUM',
        p2_compound: str = 'MEDIUM',
        active_pit_lap: Optional[int] = None,
        active_compound: Optional[str] = None,
        p2_gap_trend: float = 0.0
    ) -> List[StrategyResult]:
        """
        計算所有 5 種策略
        
        Args:
            current_lap: 當前圈數
            gap_seconds: P2 與 P1 的差距 (秒)
            p1_tyre_age: P1 輪胎齡
            p2_tyre_age: P2 輪胎齡
            p1_compound: P1 輪胎配方
            p2_compound: P2 輪胎配方
            active_pit_lap: 主動模擬進站圈數 (策略 4)
            active_compound: 主動模擬輪胎配方 (策略 4)
            
        Returns:
            5 個策略結果列表
        """
        results = []
        remaining_laps = self._total_laps - current_lap
        
        # 策略 1: 繼續當前輪胎
        results.append(self._calc_tire_age_strategy(
            current_lap, gap_seconds, p1_tyre_age, p2_tyre_age, 
            p1_compound, p2_compound, remaining_laps, p2_gap_trend
        ))
        
        # 策略 2: 立即進站 Undercut（傳遞 P1 輪胎配方）
        results.append(self._calc_undercut_strategy(
            current_lap, gap_seconds, p1_tyre_age, p2_tyre_age, remaining_laps, p1_compound
        ))
        
        # 策略 3: 等待安全車機會（傳遞 P1 輪胎配方和齡）
        results.append(self._calc_sc_opportunity_strategy(
            current_lap, gap_seconds, remaining_laps, p1_compound, p1_tyre_age
        ))
        
        # 策略 4: 主動進站模擬（傳遞 P1 輪胎配方和齡）
        if active_pit_lap and active_compound:
            results.append(self._calc_active_pit_simulation(
                current_lap, gap_seconds, active_pit_lap, active_compound, remaining_laps, p1_compound, p1_tyre_age
            ))
        else:
            # 未設定時顯示佔位
            results.append(StrategyResult(
                strategy_id=4,
                name=tr("strategy_active_pit", "Active Pit Simulation"),
                feasible=False,
                catchup_lap=None,
                total_advantage=0.0,
                drs_required=0,
                rating=0,
                details=tr("strategy_not_configured", "Not configured - use Active Simulation button"),
                advantage_per_lap=0.0,
                pit_loss=0.0,
                sc_lap_offset=0
            ))
        
        # 策略 5: P1 先進站分析（傳遞雙方輪胎配方）
        results.append(self._calc_both_pit_scenario(
            current_lap, gap_seconds, p1_tyre_age, p2_tyre_age, remaining_laps, p1_compound, p2_compound
        ))
        
        return results
    
    def _calc_tire_age_strategy(
        self, current_lap: int, gap: float, p1_age: int, p2_age: int,
        p1_compound: str, p2_compound: str, remaining: int, p2_gap_trend: float = 0.0
    ) -> StrategyResult:
        """
        策略 1: 繼續當前輪胎 - 加權 Trend+Theory 模型
        
        整合實際趨勢數據 (Trend) 與理論輪胎衰退模型 (Theory)：
        - Trend: 從 DataManager 獲取的實際單圈 gap 變化（負值 = P2 追近）
        - Theory: 二次方程式輪胎衰退模型（配方 + 齡期）
        - 加權公式: weighted_advantage = w_trend × trend + w_theory × theory
        - 權重分配: 根據 |trend| 強度動態調整（>>> 90%, >> 70%, > 50%, - 20%）
        """
        # ========== 理論計算 (Theory) ==========
        # 計算 P1 和 P2 的即時衰退速度（秒/圈）
        p1_deg_rate = self._get_compound_degradation_rate(p1_compound, p1_age)
        p2_deg_rate = self._get_compound_degradation_rate(p2_compound, p2_age)
        
        # 理論每圈優勢 = P1 衰退 - P2 衰退（正值 = P2 可追上）
        theoretical_advantage = p1_deg_rate - p2_deg_rate
        
        # ========== 實際趨勢 (Trend) ==========
        # p2_gap_trend 是 P2 對 P1 的單圈變化（負值 = gap 縮小 = P2 追近）
        # 需要轉換為「P2 每圈優勢」：trend_advantage = -gap_trend
        # 例如: gap_trend = -0.95 → P2 每圈追近 0.95s → trend_advantage = +0.95
        trend_advantage = -p2_gap_trend
        
        # ========== 動態權重分配 ==========
        # 根據 |trend| 強度決定權重（參考 Ranking Tower 的分級）
        abs_trend = abs(p2_gap_trend)
        if abs_trend >= 0.5:  # >>> 強勢
            weight_trend = 0.90
            trend_level = ">>>"
        elif abs_trend >= 0.3:  # >> 中等
            weight_trend = 0.70
            trend_level = ">>"
        elif abs_trend >= 0.1:  # > 輕微
            weight_trend = 0.50
            trend_level = ">"
        else:  # - 無明顯趨勢
            weight_trend = 0.20
            trend_level = "-"
        
        weight_theory = 1.0 - weight_trend
        
        # ========== 加權計算 ==========
        weighted_advantage = weight_trend * trend_advantage + weight_theory * theoretical_advantage
        
        # 調試輸出
        print(f"[CHASE_STRATEGY] [STRATEGY_1] === 加權計算 ===")
        print(f"  Theory: P1 {p1_compound}({p1_age}) → {p1_deg_rate:.4f} s/lap")
        print(f"  Theory: P2 {p2_compound}({p2_age}) → {p2_deg_rate:.4f} s/lap")
        print(f"  Theory Advantage: {theoretical_advantage:+.4f} s/lap")
        print(f"  Trend: gap_trend = {p2_gap_trend:+.4f} → advantage = {trend_advantage:+.4f} s/lap")
        print(f"  Trend Level: {trend_level} (|trend| = {abs_trend:.3f})")
        print(f"  Weights: Trend {weight_trend:.0%}, Theory {weight_theory:.0%}")
        print(f"  Weighted Advantage: {weighted_advantage:+.4f} s/lap")
        
        # 使用加權優勢判斷可行性
        if weighted_advantage <= 0:
            return StrategyResult(
                strategy_id=1,
                name=tr("strategy_tire_age", "Continue Current Tyres"),
                feasible=False,
                catchup_lap=None,
                total_advantage=weighted_advantage * remaining,
                drs_required=0,
                rating=0,
                details=f"❌ {tr('strategy_no_advantage', 'No advantage')} | "
                       f"Trend {trend_level}: {trend_advantage:+.3f} s/lap | "
                       f"Theory: {theoretical_advantage:+.3f} s/lap | "
                       f"Weighted: {weighted_advantage:+.3f} s/lap",
                advantage_per_lap=weighted_advantage,
                pit_loss=0.0,
                sc_lap_offset=0
            )
        
        # 計算追趕圈數（使用加權優勢）
        laps_to_catch = int(gap / weighted_advantage) + 1
        catchup_lap = current_lap + laps_to_catch
        
        # 超出剩餘圈數，不可行
        if laps_to_catch > remaining:
            return StrategyResult(
                strategy_id=1,
                name=tr("strategy_tire_age", "Continue Current Tyres"),
                feasible=False,
                catchup_lap=catchup_lap,
                total_advantage=weighted_advantage * remaining,
                drs_required=0,
                rating=0,
                details=f"⏳ {tr('strategy_insufficient_laps', 'Insufficient laps')} (need {laps_to_catch}/{remaining}) | "
                       f"Trend {trend_level}: {trend_advantage:+.3f} | "
                       f"Theory: {theoretical_advantage:+.3f} | "
                       f"Weighted: {weighted_advantage:+.3f} s/lap",
                advantage_per_lap=weighted_advantage,
                pit_loss=0.0,
                sc_lap_offset=0
            )
        
        # 可行策略
        total_advantage = weighted_advantage * laps_to_catch
        
        # 評級: 根據追趕圈數和 Trend 可信度
        # Trend 強勢 (>>>) 且 10 圈內 = 3 星
        # Trend 中等 (>>) 且 15 圈內 = 2 星
        # 其他 = 1 星
        if trend_level == ">>>" and laps_to_catch <= 10:
            rating = 3
        elif trend_level in [">>" , ">>>"] and laps_to_catch <= 15:
            rating = 2
        else:
            rating = 1
        
        # 構建詳細說明（包含加權計算細節）
        details = (
            f"✅ Lap {catchup_lap} ({laps_to_catch} laps) | "
            f"Trend {trend_level}: {trend_advantage:+.3f} ({weight_trend:.0%}) | "
            f"Theory: {theoretical_advantage:+.3f} ({weight_theory:.0%}) | "
            f"Weighted: {weighted_advantage:+.3f} s/lap"
        )
        
        return StrategyResult(
            strategy_id=1,
            name=tr("strategy_tire_age", "Continue Current Tyres"),
            feasible=True,
            catchup_lap=catchup_lap,
            total_advantage=total_advantage,
            drs_required=0,
            rating=rating,
            details=details,
            advantage_per_lap=weighted_advantage,
            pit_loss=0.0,
            sc_lap_offset=0
        )
    
    def _calc_undercut_strategy(
        self, current_lap: int, gap: float, p1_age: int, p2_age: int, remaining: int, p1_compound: str = 'MEDIUM'
    ) -> StrategyResult:
        """
        策略 2: 立即進站 Undercut
        使用精確輪胎衰退模型計算新胎優勢
        P2 換與 P1 相同配方的新胎，利用新胎優勢 undercut
        """
        # P2 換新胎（與 P1 相同配方），P1 保持舊胎
        new_compound = p1_compound  # 使用與 P1 相同的配方
        new_tyre_adv = self._calculate_new_tyre_advantage(new_compound, p1_compound, p1_age)
        
        # 出站後差距 = 原差距 + Pit Loss
        gap_after_pit = gap + self._pit_loss_green
        
        # 每圈追近 = 新胎優勢
        if new_tyre_adv <= 0:
            # 新胎沒有優勢（不應該發生，但防禦性編程）
            return StrategyResult(
                strategy_id=2,
                name=tr("strategy_undercut", "Immediate Pit (Undercut)"),
                feasible=False,
                catchup_lap=None,
                total_advantage=0.0,
                drs_required=0,
                rating=0,
                details="New tyre has no advantage",
                advantage_per_lap=0.0,
                pit_loss=self._pit_loss_green,
                sc_lap_offset=0
            )
        
        laps_to_catch = int(gap_after_pit / new_tyre_adv) + 1
        catchup_lap = current_lap + 1 + laps_to_catch  # +1 for pit lap
        
        # 計算總優勢（扣除進站損失）
        total_adv = new_tyre_adv * (remaining - 1) - self._pit_loss_green
        
        # 調試輸出
        print(f"[CHASE_STRATEGY] [STRATEGY_2] New {new_compound} vs Old {p1_compound}(age={p1_age})")
        print(f"[CHASE_STRATEGY] [STRATEGY_2] Advantage: {new_tyre_adv:.4f} s/lap, Total: {total_adv:.2f}s")
        
        if catchup_lap > self._total_laps:
            return StrategyResult(
                strategy_id=2,
                name=tr("strategy_undercut", "Immediate Pit (Undercut)"),
                feasible=False,
                catchup_lap=catchup_lap,  # 顯示計算值而非 None
                total_advantage=total_adv,
                drs_required=0,
                rating=1,
                details=tr("strategy_undercut_fail", "Not enough laps"),
                advantage_per_lap=new_tyre_adv,
                pit_loss=self._pit_loss_green,
                sc_lap_offset=0
            )
        
        rating = 3 if total_adv > 10 else (2 if total_adv > 0 else 1)
        
        return StrategyResult(
            strategy_id=2,
            name=tr("strategy_undercut", "Immediate Pit (Undercut)"),
            feasible=True,
            catchup_lap=catchup_lap,
            total_advantage=total_adv,
            drs_required=max(0, int(gap_after_pit / 0.3)),
            rating=rating,
            details=f"New {new_compound}: +{new_tyre_adv:.3f}s/lap",
            advantage_per_lap=new_tyre_adv,
            pit_loss=self._pit_loss_green,
            sc_lap_offset=0
        )
    
    def _calc_sc_opportunity_strategy(
        self, current_lap: int, gap: float, remaining: int, p1_compound: str = 'MEDIUM', p1_age: int = 10
    ) -> StrategyResult:
        """
        策略 3: 等待安全車機會
        使用精確輪胎衰退模型 + SC 進站優勢
        P2 在 SC 期間換與 P1 相同配方的新胎
        """
        # SC 進站損失較小
        pit_saving = self._pit_loss_green - self._pit_loss_sc
        
        # P2 在 SC 期間換新胎（與 P1 相同配方）
        new_compound = p1_compound  # 使用與 P1 相同的配方
        new_tyre_adv = self._calculate_new_tyre_advantage(new_compound, p1_compound, p1_age + 5)  # 假設 5 圈後 P1 輪胎又老了 5 圈
        
        # 假設 SC 出現，進站損失減少
        gap_after_sc_pit = gap + self._pit_loss_sc
        
        laps_to_catch = int(gap_after_sc_pit / new_tyre_adv) + 1 if new_tyre_adv > 0 else 999
        catchup_lap = current_lap + 5 + laps_to_catch  # 假設 SC 在 5 圈後出現
        
        # 修正邏輯：如果無法在比賽內追上，標記為不可行
        if catchup_lap > self._total_laps:
            # 但如果差距很小且有正優勢，仍然標記為可行（接近但不一定追上）
            total_adv = new_tyre_adv * max(0, remaining - 6) + pit_saving
            if total_adv > gap * 0.8:  # 如果總優勢 > 80% 差距，認為有機會
                feasible = True
                catchup_lap = self._total_laps  # 顯示最後一圈（接近但未必追上）
            else:
                feasible = False
                catchup_lap = None
        else:
            feasible = True
            total_adv = new_tyre_adv * max(0, remaining - 6) + pit_saving
        
        rating = 3 if gap > 10 else 2  # 大差距時 SC 策略更有價值
        
        print(f"[CHASE_STRATEGY] [STRATEGY_3] SC Strategy: advantage={new_tyre_adv:.4f} s/lap, saving={pit_saving:.1f}s")
        
        return StrategyResult(
            strategy_id=3,
            name=tr("strategy_sc_opportunity", "Wait for Safety Car"),
            feasible=feasible,
            catchup_lap=catchup_lap,
            total_advantage=total_adv,
            drs_required=0,
            rating=rating,
            details=f"SC saving: {pit_saving:.1f}s, New tyre: +{new_tyre_adv:.3f}s/lap",
            advantage_per_lap=new_tyre_adv,
            pit_loss=self._pit_loss_sc,
            sc_lap_offset=5  # 假設 5 圈後 SC
        )
    
    def _calc_active_pit_simulation(
        self, current_lap: int, gap: float, pit_lap: int, compound: str, remaining: int, p1_compound: str = 'MEDIUM', p1_age: int = 10
    ) -> StrategyResult:
        """
        策略 4: 主動進站模擬
        使用精確輪胎衰退模型計算指定圈數換指定配方的效果
        """
        # 計算進站時 P1 的輪胎齡
        p1_age_at_pit = p1_age + (pit_lap - current_lap)
        
        # P2 換新胎（用戶指定配方）
        new_tyre_adv = self._calculate_new_tyre_advantage(compound, p1_compound, p1_age_at_pit)
        
        laps_on_new = self._total_laps - pit_lap
        gap_after_pit = gap + self._pit_loss_green
        
        if new_tyre_adv <= 0:
            laps_to_catch = 999
        else:
            laps_to_catch = int(gap_after_pit / new_tyre_adv) + 1
        
        catchup_lap = pit_lap + laps_to_catch
        
        feasible = catchup_lap <= self._total_laps
        total_adv = new_tyre_adv * laps_on_new - self._pit_loss_green
        rating = 3 if feasible and total_adv > 10 else (2 if total_adv > 0 else 1)
        
        print(f"[CHASE_STRATEGY] [STRATEGY_4] Pit at lap {pit_lap}, {compound}: advantage={new_tyre_adv:.4f} s/lap")
        
        return StrategyResult(
            strategy_id=4,
            name=tr("strategy_active_pit", "Active Pit Simulation"),
            feasible=feasible,
            catchup_lap=catchup_lap if feasible else None,
            total_advantage=total_adv,
            drs_required=max(0, int(gap_after_pit / 0.3)),
            rating=rating,
            details=f"Lap {pit_lap}, {compound}: +{new_tyre_adv:.3f}s/lap",
            advantage_per_lap=new_tyre_adv,
            pit_loss=self._pit_loss_green,
            sc_lap_offset=0
        )
    
    def _calc_both_pit_scenario(
        self, current_lap: int, gap: float, p1_age: int, p2_age: int, remaining: int, p1_compound: str = 'MEDIUM', p2_compound: str = 'MEDIUM'
    ) -> StrategyResult:
        """
        策略 5: P1 先進站 - 分析 P1 先進站的情況
        使用精確輪胎衰退模型計算 P1 新胎 vs P2 舊胎的速度差異
        P1 換與當前相同配方的新胎
        """
        # P1 先進站換新胎（與當前相同配方），P2 保持舊胎
        new_compound = p1_compound  # P1 換與當前相同配方的新胎
        
        # P1 出站後的差距 = Pit Loss - 原差距
        gap_after_p1_pit = self._pit_loss_green - gap
        
        if gap_after_p1_pit < 0:
            # P1 Undercut 成功，已經領先
            # 計算 P1 新胎 vs P2 舊胎的速度差異（P2 會越來越慢）
            p1_advantage = self._calculate_new_tyre_advantage(new_compound, p2_compound, p2_age)
            
            feasible = True
            advantage = -gap_after_p1_pit + p1_advantage * remaining  # 領先優勢會繼續擴大
            rating = 3
            details = f"P1 leads by {-gap_after_p1_pit:.1f}s, +{p1_advantage:.3f}s/lap advantage"
        else:
            # P1 還是落後，但有新胎優勢
            # 計算 P1 能否追上 P2
            p1_advantage = self._calculate_new_tyre_advantage(new_compound, p2_compound, p2_age)
            
            if p1_advantage > 0:
                laps_to_catch = int(gap_after_p1_pit / p1_advantage) + 1
                if current_lap + laps_to_catch <= self._total_laps:
                    feasible = True
                    rating = 2
                    details = f"Can catch in {laps_to_catch} laps (+{p1_advantage:.3f}s/lap)"
                else:
                    feasible = False
                    rating = 1
                    details = f"Not enough laps (+{p1_advantage:.3f}s/lap)"
            else:
                feasible = False
                rating = 1
                details = "P1 new tyre slower than P2 old tyre"
            
            advantage = p1_advantage * remaining - gap_after_p1_pit
        
        print(f"[CHASE_STRATEGY] [STRATEGY_5] P1 pits first: gap_after={gap_after_p1_pit:.2f}s, advantage={advantage:.2f}s")
        
        return StrategyResult(
            strategy_id=5,
            name=tr("strategy_p1_pits_first", "P1 Pits First"),
            feasible=feasible,
            catchup_lap=None,
            total_advantage=advantage,
            drs_required=0,
            rating=rating,
            details=details,
            advantage_per_lap=self._calculate_new_tyre_advantage(new_compound, p2_compound, p2_age) if gap_after_p1_pit >= 0 else 0.0,
            pit_loss=self._pit_loss_green,
            sc_lap_offset=0
        )


# =============================================================================
# Active Simulation Dialog
# =============================================================================

class ActiveSimulationDialog(QDialog):
    """主動進站模擬對話框"""
    
    def __init__(self, current_lap: int, total_laps: int, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(tr("active_simulation_title", "Active Pit Simulation"))
        self.setMinimumWidth(300)
        
        # 設定深色主題
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
            }
            QSpinBox, QComboBox {
                background-color: #3a3a3a;
                color: #E0E0E0;
                border: 1px solid #555555;
                padding: 5px;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #E0E0E0;
                border: 1px solid #555555;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        
        layout = QFormLayout(self)
        
        # 進站圈數
        self.pit_lap_spin = QSpinBox()
        self.pit_lap_spin.setRange(current_lap + 1, total_laps - 1)
        self.pit_lap_spin.setValue(current_lap + 5)
        layout.addRow(tr("pit_lap", "Pit Lap:"), self.pit_lap_spin)
        
        # 目標輪胎
        self.compound_combo = QComboBox()
        self.compound_combo.addItems(["SOFT", "MEDIUM", "HARD"])
        self.compound_combo.setCurrentText("MEDIUM")
        layout.addRow(tr("target_compound", "Target Compound:"), self.compound_combo)
        
        # 按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def get_values(self) -> tuple:
        """返回 (pit_lap, compound)"""
        return self.pit_lap_spin.value(), self.compound_combo.currentText()


# =============================================================================
# Chase Strategy Widget
# =============================================================================

class ChaseStrategyWidget(QWidget):
    """
    Chase Strategy Widget - 顯示策略對比表
    """
    
    # 信號
    driver_selection_changed = pyqtSignal(str, str)  # (p1_num, p2_num)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設定深色主題背景
        self.setStyleSheet("QWidget { background-color: #1a1a1a; }")
        
        # 當前快照
        self._current_snapshot: Optional[Dict] = None
        self._tyre_state: Dict[str, Dict] = {}
        self._available_drivers: Dict[str, Dict] = {}
        
        # 選中的車手 (預設 P1, P2)
        self._selected_p1: Optional[str] = None
        self._selected_p2: Optional[str] = None
        
        #  自動追蹤模式標誌（True = 自動跟隨排名前兩名，False = 用戶手動鎖定）
        self._auto_track_leaders: bool = True
        
        # 總圈數
        self._total_laps: int = 58
        
        # 策略計算器
        self._calculator = StrategyCalculator()
        
        # 主動模擬參數
        self._active_pit_lap: Optional[int] = None
        self._active_compound: Optional[str] = None
        
        #  追蹤打開的 Gap Evolution 視窗（用於即時更新）
        self._gap_evolution_widgets: List[GapEvolutionChartWidget] = []
        
        # 保存當前計算結果 (用於右鍵繪圖)
        self._current_results: List[StrategyResult] = []
        self._current_lap: int = 0
        self._current_gap: float = 0.0
        self._p1_tla: str = ""
        self._p2_tla: str = ""
        
        self._init_ui()
        
        # 設定最小寬度和高度以確保內容可見
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)  # 設定最小高度
        
        # 設定 size policy 讓 Widget 能隨 MDI 視窗調整
        from PyQt5.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        print("[ChaseStrategyWidget] initialized")
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)  # 減少間距以移除黑色區域
        
        # 控制面板容器 (設定黑色背景以消除白色區域)
        control_container = QWidget()
        control_container.setStyleSheet("background-color: #1a1a1a;")
        # 設定 size policy 讓控制面板只使用最小需要的高度
        from PyQt5.QtWidgets import QSizePolicy
        control_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(4, 4, 4, 4)  # 減少邊距
        control_layout.setSpacing(6)  # 減少間距以節省空間
        
        # P1 選擇器
        p1_label = QLabel("P1")
        p1_label.setStyleSheet("color: #E0E0E0; font-weight: bold; background-color: transparent;")
        control_layout.addWidget(p1_label)
        self.p1_combo = QComboBox()
        self.p1_combo.setMinimumWidth(100)
        self.p1_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #E0E0E0;
                border: 1px solid #444444;
                padding: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: #E0E0E0;
                selection-background-color: #3a3a3a;
            }
        """)
        self.p1_combo.currentIndexChanged.connect(self._on_p1_changed)
        control_layout.addWidget(self.p1_combo)
        
        # P2 選擇器
        p2_label = QLabel("P2")
        p2_label.setStyleSheet("color: #E0E0E0; font-weight: bold; background-color: transparent;")
        control_layout.addWidget(p2_label)
        self.p2_combo = QComboBox()
        self.p2_combo.setMinimumWidth(100)
        self.p2_combo.setStyleSheet(self.p1_combo.styleSheet())
        self.p2_combo.currentIndexChanged.connect(self._on_p2_changed)
        control_layout.addWidget(self.p2_combo)
        
        #  Reset 按鈕（恢復自動追蹤模式）
        self.reset_btn = QPushButton(tr("reset_tracking", "Reset"))
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f2a2a;
                color: #E0E0E0;
                border: none;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8f3a3a;
            }
        """)
        self.reset_btn.setToolTip(tr("reset_tooltip", "恢復自動追蹤排名前兩名車手"))
        self.reset_btn.clicked.connect(self._reset_to_auto_track)
        control_layout.addWidget(self.reset_btn)
        
        control_layout.addStretch()
        
        # 刷新策略按鈕 (隱藏，自動刷新)
        self.refresh_btn = QPushButton(tr("refresh_strategy", "Refresh"))
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a6f2a;
                color: #E0E0E0;
                border: none;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a8f3a;
            }
        """)
        self.refresh_btn.clicked.connect(self._refresh_strategies)
        self.refresh_btn.hide()  # 隱藏刷新按鈕
        control_layout.addWidget(self.refresh_btn)
        
        # 主動模擬按鈕
        self.simulate_btn = QPushButton(tr("active_simulation", "Active Simulation"))
        self.simulate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a6f;
                color: #E0E0E0;
                border: none;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #3a3a8f;
            }
        """)
        self.simulate_btn.clicked.connect(self._open_simulation_dialog)
        control_layout.addWidget(self.simulate_btn)
        
        layout.addWidget(control_container)
        
        # 資訊標籤
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: #888888;
                font-size: 12px;
                padding: 4px;
            }
        """)
        self.info_label.setAlignment(Qt.AlignCenter)
        # 設定 size policy 讓標籤只使用最小需要的高度
        from PyQt5.QtWidgets import QSizePolicy
        self.info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self.info_label)
        
        # 策略表格
        self.strategy_table = QTableWidget()
        self.strategy_table.setColumnCount(5)
        self.strategy_table.setHorizontalHeaderLabels([
            "#",
            tr("strategy_name", "Strategy"),
            tr("feasible", "Feasible"),
            tr("catchup_lap", "Catchup Lap"),
            tr("total_advantage", "Advantage")
        ])
        self.strategy_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.strategy_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.strategy_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 欄位寬度 - 混合模式：前三欄固定，後兩欄自適應
        header = self.strategy_table.horizontalHeader()
        
        # 前三欄：固定寬度
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.strategy_table.setColumnWidth(0, 30)   # #
        
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.strategy_table.setColumnWidth(1, 180)  # Strategy
        
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.strategy_table.setColumnWidth(2, 70)   # Feasible
        
        # 後兩欄：自適應寬度（按比例分配剩餘空間）
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Catchup Lap
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Advantage
        
        self.strategy_table.verticalHeader().setVisible(False)
        
        # 設定表格 size policy 讓它占用所有可用的垂直空間
        from PyQt5.QtWidgets import QSizePolicy
        self.strategy_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 禁用交替行顏色
        self.strategy_table.setAlternatingRowColors(False)
        
        # 設定 frame 樣式
        self.strategy_table.setFrameShape(QFrame.NoFrame)
        self.strategy_table.setShowGrid(True)
        
        # 深色主題樣式
        self.strategy_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                alternate-background-color: #1a1a1a;
                color: #E0E0E0;
                gridline-color: #333333;
                border: none;
                outline: none;
                selection-background-color: #3a3a3a;
                selection-color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 4px;
                background-color: #1a1a1a;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3a3a3a;
            }
            QHeaderView {
                background-color: #2a2a2a;
                border: none;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #E0E0E0;
                padding: 4px;
                border: none;
                border-right: 1px solid #333333;
                border-bottom: 1px solid #333333;
                font-weight: bold;
            }
            QHeaderView::section:last {
                border-right: none;
            }
            QTableCornerButton::section {
                background-color: #2a2a2a;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background-color: #1a1a1a;
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #1a1a1a;
                height: 12px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #3a3a3a;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background-color: #1a1a1a;
                width: 0px;
            }
        """)
        
        # 啟用右鍵選單 (顯示 Gap 曲線圖)
        self.strategy_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.strategy_table.customContextMenuRequested.connect(self._show_strategy_chart_menu)
        
        layout.addWidget(self.strategy_table)
    
    def set_total_laps(self, total_laps: int):
        """設定總圈數"""
        self._total_laps = total_laps
        self._calculator.set_total_laps(total_laps)
    
    def set_available_drivers(self, drivers: Dict[str, Dict[str, Any]]):
        """設定可用車手列表"""
        self._available_drivers = drivers
        
        #  自動追蹤模式：選擇排名前兩名
        if self._auto_track_leaders:
            self._auto_select_leaders(drivers)
        
        self._update_driver_combos()
    
    def _auto_select_leaders(self, drivers: Dict[str, Dict]):
        """自動選擇排名前兩名車手"""
        sorted_drivers = sorted(
            drivers.items(),
            key=lambda x: x[1].get('position', 999) if isinstance(x[1], dict) else 999
        )
        
        if len(sorted_drivers) >= 2:
            p1_number = sorted_drivers[0][0]
            p2_number = sorted_drivers[1][0]
            
            # 只在車手真正變化時更新（避免無限循環）
            if self._selected_p1 != p1_number or self._selected_p2 != p2_number:
                prev_p1 = self._selected_p1
                prev_p2 = self._selected_p2
                
                self._selected_p1 = p1_number
                self._selected_p2 = p2_number
                
                p1_info = sorted_drivers[0][1]
                p2_info = sorted_drivers[1][1]
                p1_pos = p1_info.get('position', '?') if isinstance(p1_info, dict) else '?'
                p2_pos = p2_info.get('position', '?') if isinstance(p2_info, dict) else '?'
                p1_tla = p1_info.get('driver_tla', p1_info.get('tla', p1_number)) if isinstance(p1_info, dict) else p1_number
                p2_tla = p2_info.get('driver_tla', p2_info.get('tla', p2_number)) if isinstance(p2_info, dict) else p2_number
                
                print(f"[CHASE_STRATEGY]  自動追蹤: P1={p1_tla} (#{p1_number}, Pos {p1_pos}), P2={p2_tla} (#{p2_number}, Pos {p2_pos})")
                
                #  通知所有 Gap Evolution 視窗更新車手信息
                if prev_p1 is not None or prev_p2 is not None:
                    self._notify_gap_evolution_driver_change(p1_tla, p2_tla, p1_info, p2_info)
    
    def _notify_gap_evolution_driver_change(self, p1_tla: str, p2_tla: str, 
                                             p1_info: Dict, p2_info: Dict):
        """通知所有 Gap Evolution 視窗更新車手信息"""
        if not hasattr(self, '_gap_evolution_widgets'):
            return
        
        p1_color = p1_info.get('team_color', '3671C6') if isinstance(p1_info, dict) else '3671C6'
        p2_color = p2_info.get('team_color', 'FF8800') if isinstance(p2_info, dict) else 'FF8800'
        
        print(f"[CHASE_STRATEGY]  通知 {len(self._gap_evolution_widgets)} 個 Gap Evolution 視窗更新車手")
        
        for widget in self._gap_evolution_widgets:
            if widget and not widget.isHidden():
                widget.update_driver_info(p1_tla, p2_tla, p1_color, p2_color)
    
    def _update_driver_combos(self):
        """更新車手下拉選單"""
        if not self._available_drivers:
            return
        
        # 保存當前選擇
        current_p1 = self.p1_combo.currentData()
        current_p2 = self.p2_combo.currentData()
        
        # 清空並重新填充
        self.p1_combo.blockSignals(True)
        self.p2_combo.blockSignals(True)
        
        self.p1_combo.clear()
        self.p2_combo.clear()
        
        # 按位置排序
        sorted_drivers = sorted(
            self._available_drivers.items(),
            key=lambda x: x[1].get('position', 99) if isinstance(x[1], dict) else 99
        )
        
        for driver_num, info in sorted_drivers:
            if not isinstance(info, dict):
                continue
            
            tla = info.get('driver_tla', info.get('tla', driver_num))
            position = info.get('position', '')
            display_text = f"P{position} {tla}" if position else tla
            
            self.p1_combo.addItem(display_text, driver_num)
            self.p2_combo.addItem(display_text, driver_num)
        
        #  恢復或設定預設選擇（優先使用 _selected_p1/_selected_p2）
        # 自動追蹤模式下，_auto_select_leaders 已經設定了 _selected_p1/_selected_p2
        target_p1 = self._selected_p1 if self._selected_p1 else current_p1
        target_p2 = self._selected_p2 if self._selected_p2 else current_p2
        
        if target_p1:
            idx = self.p1_combo.findData(target_p1)
            if idx >= 0:
                self.p1_combo.setCurrentIndex(idx)
            else:
                print(f"[CHASE_STRATEGY]  P1={target_p1} not found in combo box")
        elif self.p1_combo.count() > 0:
            self.p1_combo.setCurrentIndex(0)  # P1
            self._selected_p1 = self.p1_combo.currentData()
        
        if target_p2:
            idx = self.p2_combo.findData(target_p2)
            if idx >= 0:
                self.p2_combo.setCurrentIndex(idx)
            else:
                print(f"[CHASE_STRATEGY]  P2={target_p2} not found in combo box")
        elif self.p2_combo.count() > 1:
            self.p2_combo.setCurrentIndex(1)  # P2
            self._selected_p2 = self.p2_combo.currentData()
        
        self.p1_combo.blockSignals(False)
        self.p2_combo.blockSignals(False)
    
    def _on_p1_changed(self, index: int):
        """P1 選擇改變（用戶手動選擇，鎖定模式）"""
        self._selected_p1 = self.p1_combo.currentData()
        #  用戶手動選擇 → 關閉自動追蹤
        self._auto_track_leaders = False
        print(f"[CHASE_STRATEGY]  用戶手動選擇 P1={self._selected_p1}，自動追蹤已關閉")
        self._on_driver_selection_changed()
        self._refresh_strategies()
    
    def _on_p2_changed(self, index: int):
        """P2 選擇改變（用戶手動選擇，鎖定模式）"""
        self._selected_p2 = self.p2_combo.currentData()
        #  用戶手動選擇 → 關閉自動追蹤
        self._auto_track_leaders = False
        print(f"[CHASE_STRATEGY]  用戶手動選擇 P2={self._selected_p2}，自動追蹤已關閉")
        self._on_driver_selection_changed()
        self._refresh_strategies()
    
    def _reset_to_auto_track(self):
        """重置為自動追蹤模式"""
        self._auto_track_leaders = True
        self._selected_p1 = None
        self._selected_p2 = None
        print(f"[CHASE_STRATEGY]  恢復自動追蹤模式，將追蹤排名前兩名車手")
        
        # 重新應用當前快照以更新車手選擇
        if self._current_snapshot:
            drivers = self._current_snapshot.get('drivers', {})
            if drivers:
                self._auto_select_leaders(drivers)
                self._refresh_strategies()
    
    def _on_driver_selection_changed(self):
        """當車手選擇變更時，重置所有 Gap Evolution 視窗數據（不關閉窗口）"""
        if not hasattr(self, '_gap_evolution_widgets'):
            return
        
        #  獲取新的車手信息
        if not self._selected_p1 or not self._selected_p2:
            print("[CHASE_STRATEGY]  車手選擇不完整，跳過 Gap Evolution 更新")
            return
        
        p1_info = self._available_drivers.get(self._selected_p1, {})
        p2_info = self._available_drivers.get(self._selected_p2, {})
        
        p1_tla = p1_info.get('driver_tla', p1_info.get('tla', self._selected_p1)) if isinstance(p1_info, dict) else self._selected_p1
        p2_tla = p2_info.get('driver_tla', p2_info.get('tla', self._selected_p2)) if isinstance(p2_info, dict) else self._selected_p2
        p1_color = p1_info.get('team_color', '3671C6') if isinstance(p1_info, dict) else '3671C6'
        p2_color = p2_info.get('team_color', 'FF8800') if isinstance(p2_info, dict) else 'FF8800'
        
        print(f"[CHASE_STRATEGY]  車手選擇變更，更新 {len(self._gap_evolution_widgets)} 個 Gap Evolution 視窗")
        print(f"[CHASE_STRATEGY]    新車手: P1={p1_tla} (#{self._selected_p1}), P2={p2_tla} (#{self._selected_p2})")
        
        #  更新所有 Gap Evolution 視窗的車手信息和數據
        for widget in self._gap_evolution_widgets[:]:
            try:
                # 1. 更新車手信息（會自動清空歷史數據）
                widget.update_driver_info(p1_tla, p2_tla, p1_color, p2_color)
                
                # 2. 重置狀態
                widget.current_lap = 0
                widget.current_gap = 0.0
                
                print(f"[CHASE_STRATEGY]  已更新 Gap Evolution widget: {p1_tla} vs {p2_tla}")
            except Exception as e:
                print(f"[CHASE_STRATEGY]  更新 Gap Evolution widget 失敗: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"[CHASE_STRATEGY] 車手選擇變更完成，Gap Evolution 視窗將自動更新新車手數據")
    
    def update_snapshot(self, snapshot: Dict[str, Any], tyre_state: Dict[str, Dict] = None):
        """更新快照數據"""
        self._current_snapshot = snapshot
        self._tyre_state = tyre_state or {}
        
        #  從快照中提取賽道名稱並更新 StrategyCalculator
        circuit_name = snapshot.get('circuit', None)  # 例如 "Suzuka", "Monaco"
        if circuit_name and circuit_name != getattr(self._calculator, '_circuit_name', None):
            print(f"[CHASE_STRATEGY]  從 Snapshot 偵測到賽道: {circuit_name}")
            self._calculator.set_circuit(circuit_name)
        
        # 更新車手列表
        drivers = snapshot.get('drivers', {})
        if drivers:
            self.set_available_drivers(drivers)
        
        # 更新總圈數
        total_laps = snapshot.get('total_laps', 0)
        if total_laps > 0:
            self.set_total_laps(total_laps)
        
        # 刷新策略
        self._refresh_strategies()
    
    def _refresh_strategies(self):
        """刷新策略計算"""
        if not self._current_snapshot:
            self.info_label.setText(tr("no_data", "No data available"))
            self.info_label.show()
            return
        
        if not self._selected_p1 or not self._selected_p2:
            self.info_label.setText(tr("select_drivers", "Please select P1 and P2"))
            self.info_label.show()
            return
        
        drivers = self._current_snapshot.get('drivers', {})
        p1_data = drivers.get(self._selected_p1, {})
        p2_data = drivers.get(self._selected_p2, {})
        
        if not p1_data or not p2_data:
            self.info_label.setText(tr("driver_not_found", "Selected driver not found"))
            self.info_label.show()
            return
        
        # 獲取數據
        current_lap = self._current_snapshot.get('current_lap', 0)
        
        # 調試：顯示當前圈數
        print(f"[CHASE_STRATEGY]  Snapshot current_lap: {current_lap}")
        
        # 計算差距 (P2 落後 P1 多少秒)
        # 使用 gap_to_leader_raw 獲取精確數值
        p1_gap_raw = p1_data.get('gap_to_leader_raw', 0.0)
        p2_gap_raw = p2_data.get('gap_to_leader_raw', 0.0)
        
        # 如果沒有 raw 數據，嘗試解析 display 文字
        if p1_gap_raw is None or p1_gap_raw == 0.0:
            p1_gap_raw = self._parse_gap(p1_data.get('gap_to_leader_display', '0')) or 0.0
        if p2_gap_raw is None or p2_gap_raw == 0.0:
            p2_gap_raw = self._parse_gap(p2_data.get('gap_to_leader_display', '0')) or 0.0
        
        # P2 落後 P1 的秒數 = P2 離領先者距離 - P1 離領先者距離
        gap_seconds = p2_gap_raw - p1_gap_raw
        
        # 如果 P1 就是領先者
        if p1_data.get('position', 99) == 1:
            gap_seconds = p2_gap_raw
        
        # 調試輸出
        print(f"[CHASE_STRATEGY] P1 {self._selected_p1}: gap_raw={p1_gap_raw}, pos={p1_data.get('position')}")
        print(f"[CHASE_STRATEGY] P2 {self._selected_p2}: gap_raw={p2_gap_raw}, pos={p2_data.get('position')}")
        print(f"[CHASE_STRATEGY] Calculated gap_seconds: {gap_seconds:.3f}s")
        
        # 獲取輪胎資訊 - 優先從 snapshot 的 driver data 中獲取
        p1_tyre = {}
        p2_tyre = {}
        
        # 方法 1: 從 tyre_state 獲取（已經從 snapshot drivers 提取）
        if self._tyre_state:
            p1_tyre = self._tyre_state.get(self._selected_p1, {})
            p2_tyre = self._tyre_state.get(self._selected_p2, {})
            print(f"[CHASE_STRATEGY]  Widget received tyre_state: {len(self._tyre_state)} drivers")
            print(f"[CHASE_STRATEGY]  Method 1 - From tyre_state:")
            print(f"   P1 ({self._selected_p1}): {p1_tyre}")
            print(f"   P2 ({self._selected_p2}): {p2_tyre}")
        else:
            print(f"[CHASE_STRATEGY]  Widget._tyre_state is EMPTY!")
        
        # 方法 2: 直接從 driver data 中獲取 (備用)
        if not p1_tyre or not p1_tyre.get('compound'):
            print(f"[CHASE_STRATEGY]  Method 1 failed for P1, trying Method 2 (driver_data)...")
            p1_tyre = {
                'compound': p1_data.get('compound', 'MEDIUM'),
                'tyre_age': p1_data.get('tyre_age', 0)  # 改為 'tyre_age' 鍵
            }
            print(f"[CHASE_STRATEGY]  Method 2 - P1 from driver_data: compound={p1_data.get('compound')}, tyre_age={p1_data.get('tyre_age')} → {p1_tyre}")
        if not p2_tyre or not p2_tyre.get('compound'):
            print(f"[CHASE_STRATEGY]  Method 1 failed for P2, trying Method 2 (driver_data)...")
            p2_tyre = {
                'compound': p2_data.get('compound', 'MEDIUM'),
                'tyre_age': p2_data.get('tyre_age', 0)  # 改為 'tyre_age' 鍵
            }
            print(f"[CHASE_STRATEGY]  Method 2 - P2 from driver_data: compound={p2_data.get('compound')}, tyre_age={p2_data.get('tyre_age')} → {p2_tyre}")
        
        p1_age = p1_tyre.get('tyre_age', 0)  # 改為讀取 'tyre_age' 鍵
        p2_age = p2_tyre.get('tyre_age', 0)  # 改為讀取 'tyre_age' 鍵
        p1_compound = p1_tyre.get('compound', 'MEDIUM')
        p2_compound = p2_tyre.get('compound', 'MEDIUM')
        
        # 調試輸出最終使用的輪胎資訊
        print(f"[CHASE_STRATEGY]  Final values for display:")
        print(f"   P1 ({self._selected_p1}): {p1_compound}({p1_age}) - 'tyre_age' key value = {p1_tyre.get('tyre_age', 'KEY_NOT_FOUND')}")
        print(f"   P2 ({self._selected_p2}): {p2_compound}({p2_age}) - 'tyre_age' key value = {p2_tyre.get('tyre_age', 'KEY_NOT_FOUND')}")
        
        # 更新資訊標籤 (使用車手和輪胎顏色，與 Ranking Tower 一致)
        p1_tla = p1_data.get('driver_tla', self._selected_p1)
        p2_tla = p2_data.get('driver_tla', self._selected_p2)
        
        # 獲取車手背景顏色
        p1_bg_color = self._get_driver_color(p1_tla, p1_data)
        p2_bg_color = self._get_driver_color(p2_tla, p2_data)
        
        # 根據背景亮度計算文字顏色（與 Ranking Tower 一致）
        p1_text_color = self._get_text_color_for_background(p1_bg_color)
        p2_text_color = self._get_text_color_for_background(p2_bg_color)
        
        # 獲取輪胎顏色
        p1_tyre_color = self._get_tyre_color(p1_compound)
        p2_tyre_color = self._get_tyre_color(p2_compound)
        
        # 使用 HTML 格式化顏色（背景色 + 對比文字色）
        info_html = (
            f"<span style='color: #888888;'>{tr('lap', 'Lap')}: {current_lap}/{self._total_laps} | "
            f"{tr('gap', 'Gap')}: {gap_seconds:.2f}s | </span>"
            f"<span style='background-color: {p1_bg_color}; color: {p1_text_color}; "
            f"font-weight: bold; padding: 2px 6px;'>P1 {p1_tla}</span>: "
            f"<span style='color: {p1_tyre_color}; font-weight: bold;'>{p1_compound}({p1_age})</span> | "
            f"<span style='background-color: {p2_bg_color}; color: {p2_text_color}; "
            f"font-weight: bold; padding: 2px 6px;'>P2 {p2_tla}</span>: "
            f"<span style='color: {p2_tyre_color}; font-weight: bold;'>{p2_compound}({p2_age})</span>"
        )
        self.info_label.setText(info_html)
        self.info_label.show()
        
        # 檢查圈數是否有效
        if current_lap == 0:
            print(f"[CHASE_STRATEGY]  current_lap is 0 - API data not yet available")
            # 清除任何現有的合併儲存格
            self.strategy_table.clearSpans()
            self.strategy_table.setRowCount(1)
            msg_item = QTableWidgetItem(tr("waiting_for_lap_data", "Waiting for lap data from API..."))
            msg_item.setTextAlignment(Qt.AlignCenter)
            msg_item.setForeground(QColor('#888888'))
            self.strategy_table.setItem(0, 0, msg_item)
            self.strategy_table.setSpan(0, 0, 1, 5)  # 合併所有欄位
            return
        
        # 前兩圈不計算策略（Lap 1-2）
        if current_lap <= 2:
            print(f"[CHASE_STRATEGY]  current_lap={current_lap} - Too early for strategy analysis")
            # 清除任何現有的合併儲存格
            self.strategy_table.clearSpans()
            self.strategy_table.setRowCount(1)
            msg_item = QTableWidgetItem(tr("early_laps_no_strategy", "Strategy analysis available from Lap 3 onwards"))
            msg_item.setTextAlignment(Qt.AlignCenter)
            msg_item.setForeground(QColor('#888888'))
            self.strategy_table.setItem(0, 0, msg_item)
            self.strategy_table.setSpan(0, 0, 1, 5)  # 合併所有欄位
            return
        
        print(f"[CHASE_STRATEGY]  current_lap={current_lap} - Calculating strategies...")
        
        # 獲取 P2 的 gap_trend（P2 相對 P1 的單圈變化）
        # 注意：DataManager 計算的是對前車的 trend，所以直接讀取 P2 的 gap_trend
        p2_gap_trend = p2_data.get('gap_trend', 0.0)
        
        # 調試輸出
        print(f"[CHASE_STRATEGY]  P2 gap_trend from snapshot: {p2_gap_trend:+.4f} s/lap")
        
        # 計算策略
        results = self._calculator.calculate_all_strategies(
            current_lap=current_lap,
            gap_seconds=gap_seconds,
            p1_tyre_age=p1_age,
            p2_tyre_age=p2_age,
            p1_compound=p1_compound,
            p2_compound=p2_compound,
            active_pit_lap=self._active_pit_lap,
            active_compound=self._active_compound,
            p2_gap_trend=p2_gap_trend
        )
        
        # 保存當前計算結果 (用於右鍵繪圖)
        self._current_results = results
        self._current_lap = current_lap
        self._current_gap = gap_seconds
        self._p1_tla = p1_data.get('driver_tla', p1_data.get('tla', str(self._selected_p1)))
        self._p2_tla = p2_data.get('driver_tla', p2_data.get('tla', str(self._selected_p2)))
        
        # 填充表格
        self._populate_table(results)
    
    def _parse_gap(self, gap_str: str) -> Optional[float]:
        """解析差距字串"""
        if not gap_str:
            return 0.0
        gap_str = str(gap_str).strip().upper()
        if 'LAP' in gap_str:
            return None
        gap_str = gap_str.replace('+', '').replace('S', '').strip()
        try:
            return float(gap_str)
        except ValueError:
            return 0.0
    
    def _populate_table(self, results: List[StrategyResult]):
        """填充策略表格"""
        # 清除任何現有的合併儲存格（例如早期圈數訊息）
        self.strategy_table.clearSpans()
        self.strategy_table.setRowCount(len(results))
        
        # 找到策略 5 的詳情
        strategy5_details = None
        
        for row, result in enumerate(results):
            # #
            id_item = QTableWidgetItem(str(result.strategy_id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.strategy_table.setItem(row, 0, id_item)
            
            # Strategy Name
            name_item = QTableWidgetItem(result.name)
            self.strategy_table.setItem(row, 1, name_item)
            
            # Feasible
            feasible_text = "Yes" if result.feasible else "No"
            feasible_item = QTableWidgetItem(feasible_text)
            feasible_item.setTextAlignment(Qt.AlignCenter)
            if result.feasible:
                feasible_item.setForeground(QColor('#00FF00'))
            else:
                feasible_item.setForeground(QColor('#FF6666'))
            self.strategy_table.setItem(row, 2, feasible_item)
            
            # Catchup Lap
            if result.catchup_lap:
                if result.feasible:
                    catchup_text = str(result.catchup_lap)
                else:
                    # 不可行但有計算值：顯示帶括號的圈數表示「理論上需要這麼多圈」
                    catchup_text = f"({result.catchup_lap})"
            else:
                catchup_text = "-"
            catchup_item = QTableWidgetItem(catchup_text)
            catchup_item.setTextAlignment(Qt.AlignCenter)
            self.strategy_table.setItem(row, 3, catchup_item)
            
            # Total Advantage
            adv_text = f"{result.total_advantage:.1f}s" if result.total_advantage else "-"
            adv_item = QTableWidgetItem(adv_text)
            adv_item.setTextAlignment(Qt.AlignCenter)
            if result.total_advantage > 0:
                adv_item.setForeground(QColor('#00FF00'))
            elif result.total_advantage < 0:
                adv_item.setForeground(QColor('#FF6666'))
            self.strategy_table.setItem(row, 4, adv_item)
    
    def _get_driver_color(self, driver_tla: str, driver_data: Dict = None) -> str:
        """獲取車手顏色（與 Driver Strategy 一致：優先使用 snapshot team_color）"""
        team_color = None
        
        #  優先使用 snapshot 的 team_color（與 Driver Strategy 一致）
        if driver_data:
            team_color = driver_data.get('team_color', None)
            if team_color and not team_color.startswith('#'):
                team_color = f'#{team_color}'
        
        # 回退到 ColorPaletteProvider（如果 snapshot 沒有顏色）
        if not team_color and COLOR_PALETTE_AVAILABLE and color_palette_provider:
            try:
                team_color_qcolor = color_palette_provider.get_driver_color(driver_tla, fallback=True)
                if team_color_qcolor:
                    team_color = team_color_qcolor.name()
            except Exception:
                pass
        
        # 最終預設值：青色（與 Driver Strategy 一致）
        return team_color or '#4ECDC4'
    
    def _get_tyre_color(self, compound: str) -> str:
        """獲取輪胎顏色"""
        compound_upper = compound.upper() if compound else ''
        if 'SOFT' in compound_upper:
            return COLOR_TYRE_SOFT
        elif 'MEDIUM' in compound_upper:
            return COLOR_TYRE_MEDIUM
        elif 'HARD' in compound_upper:
            return COLOR_TYRE_HARD
        elif 'INTERMEDIATE' in compound_upper or 'INTER' in compound_upper:
            return COLOR_TYRE_INTERMEDIATE
        elif 'WET' in compound_upper:
            return COLOR_TYRE_WET
        return '#CCCCCC'
    
    def _get_text_color_for_background(self, bg_color: str) -> str:
        """
        根據背景顏色計算最佳文字顏色（黑色或白色）
        與 Ranking Tower 一致的實現
        """
        try:
            from PyQt5.QtGui import QColor
            color = QColor(bg_color)
            # 計算亮度 (Luminance)
            luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
            # 亮度低於 0.5 使用白色，否則使用黑色
            return '#FFFFFF' if luminance < 0.5 else '#000000'
        except:
            return '#FFFFFF'
    
    def _show_strategy_chart_menu(self, pos):
        """顯示策略 Gap 曲線圖右鍵選單"""
        print(f"[CHASE_STRATEGY] Right-click menu triggered at pos: {pos}")
        
        # 獲取點擊的行
        row = self.strategy_table.rowAt(pos.y())
        print(f"[CHASE_STRATEGY] Clicked row: {row}, total results: {len(self._current_results)}")
        
        if row < 0 or row >= len(self._current_results):
            print(f"[CHASE_STRATEGY] Invalid row, returning")
            return
        
        strategy_result = self._current_results[row]
        print(f"[CHASE_STRATEGY] Strategy selected: {strategy_result.name}")
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2a2a2a;
                color: #E0E0E0;
                border: 1px solid #444444;
            }
            QMenu::item:selected {
                background-color: #3a3a3a;
            }
        """)
        
        # 顯示 Gap 曲線
        show_chart_action = menu.addAction(tr("show_gap_chart", "Show Gap Evolution Chart"))
        show_chart_action.triggered.connect(lambda: self._show_gap_chart(strategy_result))
        
        print(f"[CHASE_STRATEGY] Showing menu...")
        menu.exec_(self.strategy_table.mapToGlobal(pos))
    
    def _on_gap_widget_closed(self, widget):
        """當 Gap Evolution 視窗關閉時移除追蹤"""
        try:
            if widget in self._gap_evolution_widgets:
                self._gap_evolution_widgets.remove(widget)
                print(f"[CHASE_STRATEGY]  Gap Evolution widget closed, remaining: {len(self._gap_evolution_widgets)}")
        except (ValueError, RuntimeError) as e:
            # 忽略 widget 已被刪除或不在列表中的錯誤
            print(f"[CHASE_STRATEGY] Gap widget cleanup: {e}")
    
    def _show_gap_chart(self, strategy: StrategyResult):
        """在 MDI 子視窗中顯示 Gap 變化曲線圖"""
        print(f"[CHASE_STRATEGY] _show_gap_chart called for strategy: {strategy.name}")
        print(f"[CHASE_STRATEGY] Strategy feasible: {strategy.feasible}, ID: {strategy.strategy_id}")
        
        # 移除 feasibility 檢查 - 允許顯示所有策略的 Gap 圖表
        # 即使策略不可行，用戶也可能想看到假設性的演變
        
        print(f"[CHASE_STRATEGY] Creating Gap Evolution MDI window...")
        
        # 獲取父級 MDI Area
        from PyQt5.QtWidgets import QMdiArea
        parent_widget = self.parent()
        while parent_widget and not isinstance(parent_widget, QMdiArea):
            parent_widget = parent_widget.parent()
        
        if not parent_widget:
            print(f"[CHASE_STRATEGY] Cannot find MDI area, fallback to dialog")
            return
        
        # 獲取 P1 和 P2 的車手顏色
        drivers = self._current_snapshot.get('drivers', {}) if self._current_snapshot else {}
        p1_data = drivers.get(self._selected_p1, {})
        p2_data = drivers.get(self._selected_p2, {})
        
        p1_color = self._get_driver_color(self._p1_tla, p1_data)
        p2_color = self._get_driver_color(self._p2_tla, p2_data)
        
        # 移除 '#' 前綴（如果有）
        p1_color = p1_color.lstrip('#') if p1_color else "3671C6"
        p2_color = p2_color.lstrip('#') if p2_color else "FF8800"
        
        print(f"[CHASE_STRATEGY] P1 {self._p1_tla} color: #{p1_color}, P2 {self._p2_tla} color: #{p2_color}")
        
        # 獲取輪胎資訊（修正：使用 'compound'，不是 'tyre_compound'）
        p1_compound = p1_data.get('compound', '--') if p1_data else '--'
        p2_compound = p2_data.get('compound', '--') if p2_data else '--'
        
        print(f"[CHASE_STRATEGY] P1 {self._p1_tla} compound: {p1_compound}, P2 {self._p2_tla} compound: {p2_compound}")
        
        # 創建自繪圖表 Widget
        chart_widget = GapEvolutionChartWidget(
            strategy=strategy,
            current_lap=self._current_lap,
            current_gap=self._current_gap,
            total_laps=self._total_laps,
            p1_tla=self._p1_tla,
            p2_tla=self._p2_tla,
            p1_color=p1_color,
            p2_color=p2_color,
            active_pit_lap=self._active_pit_lap,
            p1_compound=p1_compound,
            p2_compound=p2_compound,
            strategy_id=strategy.strategy_id  #  傳遞 strategy_id 以支援 Workspace 儲存
        )
        
        #  設定 StrategyCalculator 引用（用於精確輪胎衰退計算）
        chart_widget.set_strategy_calculator(self._calculator)
        
        #  追蹤 widget 以便即時更新
        self._gap_evolution_widgets.append(chart_widget)
        
        #  連接 destroyed 信號，當視窗關閉時移除追蹤
        # 使用 functools.partial 避免 lambda 持有 widget 引用導致 RuntimeError
        from functools import partial
        chart_widget.destroyed.connect(partial(self._on_gap_widget_closed, chart_widget))
        
        #  使用 PopoutSubWindow 代替 QMdiSubWindow（提供完整 MDI 功能）
        # 注意：從 f1t_gui_main.py 導入（全域定義）
        import sys
        main_module = sys.modules.get('__main__')
        if main_module and hasattr(main_module, 'PopoutSubWindow'):
            PopoutSubWindow = main_module.PopoutSubWindow
        else:
            # 備用：如果無法導入，回退到 QMdiSubWindow
            print(f"[CHASE_STRATEGY]  無法導入 PopoutSubWindow，回退到 QMdiSubWindow")
            from PyQt5.QtWidgets import QMdiSubWindow
            sub_window = QMdiSubWindow()
            sub_window.setWidget(chart_widget)
            sub_window.setWindowTitle(f"{strategy.name} - Gap Evolution")
            sub_window.setAttribute(Qt.WA_DeleteOnClose)
            sub_window.resize(900, 600)
            parent_widget.addSubWindow(sub_window)
            sub_window.show()
            return
        
        # 創建 PopoutSubWindow（提供標題欄、最大化/最小化/關閉按鈕等）
        window_title = f"{strategy.name} - Gap Evolution"
        sub_window = PopoutSubWindow(
            window_title, 
            parent_widget,
            analysis_module=None,  # Gap Chart 不是標準分析模組
            sync_enabled=False  # 不需要參數同步
        )
        sub_window.setWidget(chart_widget)
        sub_window.resize(900, 600)
        
        # 添加到 MDI Area
        parent_widget.addSubWindow(sub_window)
        sub_window.show()
        
        print(f"[CHASE_STRATEGY]  Gap Evolution PopoutSubWindow 創建成功")
    
    def _open_simulation_dialog(self):
        """開啟主動模擬對話框"""
        current_lap = self._current_snapshot.get('current_lap', 1) if self._current_snapshot else 1
        
        dialog = ActiveSimulationDialog(current_lap, self._total_laps, self)
        if dialog.exec_() == QDialog.Accepted:
            self._active_pit_lap, self._active_compound = dialog.get_values()
            self._refresh_strategies()
    
    def _toggle_detail_widget(self):
        """切換詳情區域顯示（已移除）"""
        pass


# =============================================================================
# Gap Evolution Chart Widget (使用 QPainter 自繪)
# =============================================================================

class GapEvolutionChartWidget(QWidget):
    """
    Lap Time Evolution Chart Widget (雙圈速演變圖表)
    
    使用 QPainter 繪製雙車手圈速演變曲線
     支援即時更新：隨著比賽進行自動刷新數據
     支援 Workspace 儲存/載入
     顯示真實圈速（圓點）+ 預測圈速（虛線）
     雙曲線：P1（藍色）、P2（橙色）
    """
    
    #  Workspace 儲存/載入支援
    analysis_type = "gap_evolution_chart"
    
    def __init__(self, strategy: StrategyResult, current_lap: int, current_gap: float,
                 total_laps: int, p1_tla: str, p2_tla: str, 
                 p1_color: str = "3671C6", p2_color: str = "FF8800",
                 active_pit_lap: Optional[int] = None,
                 p1_compound: str = "--", p2_compound: str = "--",
                 strategy_id: str = None):
        super().__init__()
        
        self.strategy = strategy
        self.strategy_id = strategy_id or (strategy.strategy_id if strategy else "unknown")
        self.current_lap = current_lap
        self.current_gap = current_gap
        self.total_laps = total_laps
        self.p1_tla = p1_tla
        self.p2_tla = p2_tla
        self.p1_color = f"#{p1_color}" if not p1_color.startswith('#') else p1_color
        self.p2_color = f"#{p2_color}" if not p2_color.startswith('#') else p2_color
        self.active_pit_lap = active_pit_lap
        self.p1_compound = p1_compound
        self.p2_compound = p2_compound
        
        #  儲存 StrategyCalculator 引用（用於精確輪胎衰退計算）
        self._strategy_calculator = None  # 稍後由 ChaseStrategyWidget 設定
        self._calculator_ready = False  # 追蹤 calculator 是否已設定
        
        #  新增：圈速歷史記錄（lap_number → lap_time_seconds）
        self.p1_lap_times = {}  # {lap: lap_time_seconds}
        self.p2_lap_times = {}  # {lap: lap_time_seconds}
        
        #  進站追蹤（參考 Driver Strategy）
        self.p1_pit_laps = []  # P1 進站圈數列表
        self.p2_pit_laps = []  # P2 進站圈數列表
        self.p1_pit_out_laps = set()  # P1 出站圈數（進站後的下一圈）
        self.p2_pit_out_laps = set()  # P2 出站圈數
        
        #  輪胎更換追蹤（用於重置衰退起始點）
        self.p1_last_compound = p1_compound  # 上一圈的輪胎配方
        self.p2_last_compound = p2_compound
        self.p1_stint_start_lap = 1  # P1 當前 stint 起始圈數
        self.p2_stint_start_lap = 1  # P2 當前 stint 起始圈數
        
        # 圖表邊距（與 Driver Strategy 完全一致）
        self._margin_left = 60
        self._margin_right = 20
        self._margin_top = 30  # Space for info bar
        self._margin_bottom = 35
        
        #  改為圈速範圍（秒） - 動態計算
        self._laptime_min = 80.0  # 預設最快圈速
        self._laptime_max = 95.0  # 預設最慢圈速
        self._calculate_laptime_range()  # 動態調整 Y 軸範圍
        
        # 字體（與 Driver Strategy 完全一致）
        self._font_title = QFont("Arial", 12, QFont.Bold)
        self._font_label = QFont("Arial", 10)
        self._font_axis = QFont("Arial", 8)  # 與 Driver Strategy 一致
        self._font_legend = QFont("Arial", 9)
        
        #  使用 QLabel 架構（與 Driver Strategy 一致）
        self._setup_ui()
        
        #  改進 1: 移除最小尺寸限制（參考 Driver Strategy）
        self.setMinimumSize(200, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def _setup_ui(self):
        """Setup UI layout with QLabel info bar (與 Driver Strategy 一致)"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(2)
        
        # Info bar at top (使用 QLabel)
        self._setup_info_bar(main_layout)
        
        # Add stretch for chart area
        main_layout.addStretch()
        
        # Background color
        self.setStyleSheet(f"background-color: {COLOR_BG};")
    
    def _setup_info_bar(self, layout: QVBoxLayout):
        """Setup information bar using QLabel (與 Driver Strategy 完全一致)"""
        info_layout = QHBoxLayout()
        info_layout.setSpacing(15)
        
        # 1. Driver P1 label
        self._p1_driver_label = QLabel(f"Driver: {self.p1_tla}")
        self._p1_driver_label.setStyleSheet(f"color: {self.p1_color}; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(self._p1_driver_label)
        
        # 2. P1 Tyre label
        self._p1_tyre_label = QLabel(f"Tyre: {self.p1_compound}")
        p1_tyre_color = self._get_tyre_color(self.p1_compound)
        self._p1_tyre_label.setStyleSheet(f"color: {p1_tyre_color}; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(self._p1_tyre_label)
        
        # 3. Gap/Delta label
        sign = "+" if self.current_gap >= 0 else ""
        self._gap_label = QLabel(f"Δ: {sign}{self.current_gap:.3f}s")
        self._gap_label.setStyleSheet(f"color: {self.p2_color}; font-size: 12px;")
        info_layout.addWidget(self._gap_label)
        
        # 4. Driver P2 label
        self._p2_driver_label = QLabel(f"Driver: {self.p2_tla}")
        self._p2_driver_label.setStyleSheet(f"color: {self.p2_color}; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(self._p2_driver_label)
        
        # 5. P2 Tyre label
        self._p2_tyre_label = QLabel(f"Tyre: {self.p2_compound}")
        p2_tyre_color = self._get_tyre_color(self.p2_compound)
        self._p2_tyre_label.setStyleSheet(f"color: {p2_tyre_color}; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(self._p2_tyre_label)
        
        info_layout.addStretch()
        
        # 6. Lap counter (最右側)
        self._lap_label = QLabel(f"Lap: {self.current_lap}/{self.total_laps}")
        self._lap_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(self._lap_label)
        
        layout.addLayout(info_layout)
    
    def set_strategy_calculator(self, calculator):
        """
        設定 StrategyCalculator 並觸發重繪
        
         重要：從 Workspace 載入時，此方法必須被調用以啟用預測曲線
        """
        self._strategy_calculator = calculator
        self._calculator_ready = True
        print(f"[GAP_EVO]  StrategyCalculator 已設定，觸發重繪")
        # 觸發重繪以顯示預測曲線
        self.update()
    
    def update_driver_info(self, p1_tla: str, p2_tla: str, 
                           p1_color: str = None, p2_color: str = None):
        """更新車手信息（用於自動追蹤模式）"""
        self.p1_tla = p1_tla
        self.p2_tla = p2_tla
        
        if p1_color:
            self.p1_color = f"#{p1_color}" if not p1_color.startswith('#') else p1_color
        if p2_color:
            self.p2_color = f"#{p2_color}" if not p2_color.startswith('#') else p2_color
        
        # 更新 UI 標籤
        self._p1_driver_label.setText(f"Driver: {self.p1_tla}")
        self._p1_driver_label.setStyleSheet(f"color: {self.p1_color}; font-weight: bold; font-size: 12px;")
        
        self._p2_driver_label.setText(f"Driver: {self.p2_tla}")
        self._p2_driver_label.setStyleSheet(f"color: {self.p2_color}; font-weight: bold; font-size: 12px;")
        
        # 清空圈速歷史（新車手）
        self.p1_lap_times.clear()
        self.p2_lap_times.clear()
        
        # ✅ 清空進站追蹤（新車手）
        self.p1_pit_laps.clear()
        self.p2_pit_laps.clear()
        self.p1_pit_out_laps.clear()
        self.p2_pit_out_laps.clear()
        
        # ✅ 重置 stint 起始圈
        self.p1_stint_start_lap = 1
        self.p2_stint_start_lap = 1
        
        print(f"[GAP_EVOLUTION]  更新車手: P1={p1_tla} ({self.p1_color}), P2={p2_tla} ({self.p2_color})")
        
        # 重繪
        self.update()
    
    def update_data(self, current_lap: int, current_gap: float, 
                    p1_compound: str = None, p2_compound: str = None,
                    p1_lap_time: float = None, p2_lap_time: float = None,
                    p1_tyre_age: int = None, p2_tyre_age: int = None):
        """
        更新圖表數據（支援即時更新）
        
        Args:
            current_lap: 當前圈數
            current_gap: 當前 Gap 差距
            p1_compound: P1 輪胎類型（可選）
            p2_compound: P2 輪胎類型（可選）
            p1_lap_time: P1 當前圈速（秒，可選）
            p2_lap_time: P2 當前圈速（秒，可選）
            p1_tyre_age: P1 輪胎齡（可選）
            p2_tyre_age: P2 輪胎齡（可選）
        """
        print(f"\n[UPDATE_DATA_DEBUG] 更新數據:")
        print(f"  當前圈: {current_lap}, Gap: {current_gap}")
        print(f"  P1 圈速: {p1_lap_time}, P2 圈速: {p2_lap_time}")
        print(f"  P1 數據量: {len(self.p1_lap_times)}, P2 數據量: {len(self.p2_lap_times)}")
        
        # ✅ 倒帶檢測：如果圈數倒退，清空未來圈的數據
        if current_lap < self.current_lap:
            print(f"[GAP_EVO] ⏪ 倒帶檢測: {self.current_lap} → {current_lap}，清空未來圈數據")
            # 移除所有大於 current_lap 的圈數數據
            self.p1_lap_times = {lap: time for lap, time in self.p1_lap_times.items() if lap <= current_lap}
            self.p2_lap_times = {lap: time for lap, time in self.p2_lap_times.items() if lap <= current_lap}
            print(f"[GAP_EVO]  清空後 P1 數據量: {len(self.p1_lap_times)}, P2 數據量: {len(self.p2_lap_times)}")
        
        self.current_lap = current_lap
        self.current_gap = current_gap
        
        #  輪胎更換偵測（重置 stint 起始圈數）
        if p1_compound and p1_compound != self.p1_last_compound:
            print(f"[GAP_EVO] P1 輪胎更換: {self.p1_last_compound} → {p1_compound}")
            self.p1_last_compound = p1_compound
            self.p1_stint_start_lap = current_lap  # 重置起始圈
        
        if p2_compound and p2_compound != self.p2_last_compound:
            print(f"[GAP_EVO] P2 輪胎更換: {self.p2_last_compound} → {p2_compound}")
            self.p2_last_compound = p2_compound
            self.p2_stint_start_lap = current_lap  # 重置起始圈
        
        #  進站偵測（參考 Driver Strategy）
        # 如果圈速異常高（> 基準 + 20 秒），判定為進站圈
        p1_is_pit_lap = False
        p2_is_pit_lap = False
        
        if p1_lap_time is not None and len(self.p1_lap_times) > 0:
            avg_time = sum(self.p1_lap_times.values()) / len(self.p1_lap_times)
            if p1_lap_time > avg_time + 20:  # 圈速飆高 > 20 秒
                p1_is_pit_lap = True
                if current_lap not in self.p1_pit_laps:
                    self.p1_pit_laps.append(current_lap)
                    self.p1_pit_out_laps.add(current_lap + 1)  # 標記下一圈為出站圈
                    print(f"[GAP_EVO] ⚠️  P1 進站偵測: Lap {current_lap}, 圈速 {p1_lap_time:.3f}s")
        
        if p2_lap_time is not None and len(self.p2_lap_times) > 0:
            avg_time = sum(self.p2_lap_times.values()) / len(self.p2_lap_times)
            if p2_lap_time > avg_time + 20:
                p2_is_pit_lap = True
                if current_lap not in self.p2_pit_laps:
                    self.p2_pit_laps.append(current_lap)
                    self.p2_pit_out_laps.add(current_lap + 1)
                    print(f"[GAP_EVO] ⚠️  P2 進站偵測: Lap {current_lap}, 圈速 {p2_lap_time:.3f}s")
        
        #  記錄圈速歷史（排除進站圈和出站圈）
        p1_is_pit_out = current_lap in self.p1_pit_out_laps
        p2_is_pit_out = current_lap in self.p2_pit_out_laps
        
        if p1_lap_time is not None and not p1_is_pit_lap and not p1_is_pit_out:
            self.p1_lap_times[current_lap] = p1_lap_time
            print(f"[LAP_TIME] ✅ P1 Lap {current_lap}: {p1_lap_time:.3f}s (正常圈速)")
        elif p1_lap_time is not None:
            print(f"[LAP_TIME] ❌ P1 Lap {current_lap}: {p1_lap_time:.3f}s (進站/出站，已排除)")
        
        if p2_lap_time is not None and not p2_is_pit_lap and not p2_is_pit_out:
            self.p2_lap_times[current_lap] = p2_lap_time
            print(f"[LAP_TIME] ✅ P2 Lap {current_lap}: {p2_lap_time:.3f}s (正常圈速)")
        elif p2_lap_time is not None:
            print(f"[LAP_TIME] ❌ P2 Lap {current_lap}: {p2_lap_time:.3f}s (進站/出站，已排除)")
        
        #  新增：記錄輪胎齡（用於預測計算）
        if p1_tyre_age is not None:
            self._p1_tyre_age = p1_tyre_age
        
        if p2_tyre_age is not None:
            self._p2_tyre_age = p2_tyre_age
        
        # 更新輪胎資訊（如果提供）
        if p1_compound:
            self.p1_compound = p1_compound
            p1_tyre_color = self._get_tyre_color(p1_compound)
            self._p1_tyre_label.setText(f"Tyre: {p1_compound}")
            self._p1_tyre_label.setStyleSheet(f"color: {p1_tyre_color}; font-weight: bold; font-size: 12px;")
        
        if p2_compound:
            self.p2_compound = p2_compound
            p2_tyre_color = self._get_tyre_color(p2_compound)
            self._p2_tyre_label.setText(f"Tyre: {p2_compound}")
            self._p2_tyre_label.setStyleSheet(f"color: {p2_tyre_color}; font-weight: bold; font-size: 12px;")
        
        # 更新 Gap 標籤
        sign = "+" if self.current_gap >= 0 else ""
        self._gap_label.setText(f"Δ: {sign}{self.current_gap:.3f}s")
        
        # 更新圈數標籤
        self._lap_label.setText(f"Lap: {self.current_lap}/{self.total_laps}")
        
        #  改為重新計算圈速範圍（而非 Gap 範圍）
        self._calculate_laptime_range()
        
        # 重繪圖表
        self.update()
    
    def _get_tyre_color(self, compound: str) -> str:
        """獲取輪胎顏色（與 Driver Strategy 完全一致）"""
        compound_colors = {
            'SOFT': '#FF3333',      # 紅色
            'S': '#FF3333',
            'MEDIUM': '#FFCC00',    # 黃色
            'M': '#FFCC00',
            'HARD': '#FFFFFF',      # 白色
            'H': '#FFFFFF',
            'INTERMEDIATE': '#00CC00',  # 綠色
            'I': '#00CC00',
            'WET': '#0066FF',       # 藍色（與 Driver Strategy 一致）
            'W': '#0066FF',
        }
        return compound_colors.get(compound.upper() if compound else '', '#CCCCCC')
    
    def _calculate_laptime_range(self):
        """動態計算 Y 軸圈速範圍（帶防禦性檢查）"""
        print(f"\n[LAPTIME_RANGE_DEBUG] 計算圈速範圍:")
        # 收集所有真實圈速數據
        all_lap_times = []
        
        #  防禦性檢查：確保字典不為 None
        if self.p1_lap_times:
            all_lap_times.extend([t for t in self.p1_lap_times.values() if t > 0])
        if self.p2_lap_times:
            all_lap_times.extend([t for t in self.p2_lap_times.values() if t > 0])
        
        # 計算預測圈速
        try:
            _, future_p1_times, future_p2_times = self._calculate_future_lap_times()
            if future_p1_times:
                all_lap_times.extend([t for t in future_p1_times if t > 0])
            if future_p2_times:
                all_lap_times.extend([t for t in future_p2_times if t > 0])
        except Exception as e:
            print(f"[WARNING] _calculate_future_lap_times() failed: {e}")
            # 繼續使用真實數據，忽略預測
        
        if not all_lap_times:
            # 沒有數據時使用預設範圍
            self._laptime_min = 80.0
            self._laptime_max = 95.0
            return
        
        # 找到所有圈速的範圍
        min_time = min(all_lap_times)
        max_time = max(all_lap_times)
        
        # 添加 10% 的邊距
        time_range = max_time - min_time
        margin = max(time_range * 0.1, 1.0)  # 至少 1 秒邊距
        
        self._laptime_min = min_time - margin
        self._laptime_max = max_time + margin
        
        print(f"[LAP_TIME_CHART] Dynamic Y-axis range: {self._laptime_min:.1f}s to {self._laptime_max:.1f}s")
    
    def paintEvent(self, event):
        """主要繪製事件（帶異常處理防止白屏）"""
        print(f"\n[PAINT_EVENT_DEBUG] paintEvent 開始")
        print(f"  Widget 大小: {self.width()}x{self.height()}")
        print(f"  P1 數據: {len(self.p1_lap_times)} 圈, P2 數據: {len(self.p2_lap_times)} 圈")
        print(f"  當前圈: {self.current_lap}/{self.total_laps}")
        
        painter = QPainter(self)
        print(f"  QPainter 創建成功: {painter.isActive()}")
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        try:
            # 繪製背景
            print(f"  [1/8] 繪製背景...")
            painter.fillRect(self.rect(), QColor(COLOR_BG))
            
            # 計算圖表區域
            print(f"  [2/8] 計算圖表區域...")
            chart_rect = QRectF(
                self._margin_left,
                self._margin_top,
                self.width() - self._margin_left - self._margin_right,
                self.height() - self._margin_top - self._margin_bottom
            )
            print(f"    圖表區域: {chart_rect.width():.0f}x{chart_rect.height():.0f}")
            
            if chart_rect.width() <= 0 or chart_rect.height() <= 0:
                print(f"   圖表區域無效，結束繪製")
                return
            
            # 繪製圖表背景
            print(f"  [3/8] 繪製圖表背景...")
            painter.fillRect(chart_rect, QColor(COLOR_CHART_BG))
            
            #  防禦性檢查：數據為空時顯示等待訊息
            if not self.p1_lap_times and not self.p2_lap_times:
                print(f"   數據為空，顯示等待訊息")
                self._draw_no_data_message(painter, chart_rect)
                return  # painter.end() 由 finally 處理
            
            # 繪製網格
            print(f"  [4/8] 繪製網格...")
            self._draw_grid(painter, chart_rect)
            
            # 繪製曲線
            print(f"  [5/8] 繪製曲線...")
            self._draw_gap_lines(painter, chart_rect)
            
            #  改進 2: 繪製當前圈垂直線（參考 Driver Strategy）
            print(f"  [6/9] 繪製當前圈指示器...")
            self._draw_current_lap_indicator(painter, chart_rect)
            
            #  繪製進站標記（參考 Driver Strategy）
            print(f"  [7/9] 繪製進站標記...")
            self._draw_pit_markers(painter, chart_rect)
            
            # 繪製標記
            print(f"  [8/9] 繪製標記...")
            self._draw_markers(painter, chart_rect)
            
            # 繪製座標軸
            print(f"  [9/9] 繪製座標軸...")
            self._draw_axes(painter, chart_rect)
            
            #  資訊欄已改用 QLabel，不需要在 paintEvent 中繪製
            
            #  改進 1: 取消圖例顯示
            # self._draw_legend(painter, chart_rect)
            
        except Exception as e:
            #  異常處理：避免白屏崩潰
            print(f"\n [PAINT_ERROR] paintEvent 發生異常: {e}")
            import traceback
            traceback.print_exc()
            print(f"  Painter 狀態: {painter.isActive()}")
            if 'chart_rect' in locals():
                print(f"  Chart Rect: {chart_rect}")
            self._draw_error_message(painter, chart_rect if 'chart_rect' in locals() else self.rect())
        finally:
            if painter.isActive():
                print(f"   painter.end() 執行")
                painter.end()
            else:
                print(f"   painter 已結束，跳過 end()")
            print(f"[PAINT_EVENT_DEBUG] paintEvent 完成\n")
    
    def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
        """繪製網格線（圈速軸）"""
        pen = QPen(QColor(COLOR_GRID))
        pen.setStyle(Qt.DotLine)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 水平網格線 (圈速軸)
        time_range = self._laptime_max - self._laptime_min
        if time_range <= 0:
            return
        
        tick_interval = self._calculate_tick_interval(time_range)
        time_start = math.ceil(self._laptime_min / tick_interval) * tick_interval
        lap_time = time_start
        while lap_time <= self._laptime_max:
            py = self._laptime_to_y(lap_time, chart_rect)
            painter.drawLine(
                QPointF(chart_rect.left(), py),
                QPointF(chart_rect.right(), py)
            )
            lap_time += tick_interval
        
        # 垂直網格線 (圈數軸)
        if self.total_laps > 0:
            lap_interval = max(1, self.total_laps // 10)
            for lap in range(0, self.total_laps + 1, lap_interval):
                px = self._lap_to_x(lap, chart_rect)
                painter.drawLine(
                    QPointF(px, chart_rect.top()),
                    QPointF(px, chart_rect.bottom())
                )
    
    def _draw_gap_lines(self, painter: QPainter, chart_rect: QRectF):
        """繪製雙車手圈速曲線（P1藍色、P2橙色）"""
        #  改為繪製兩條圈速曲線：P1（藍色）、P2（橙色）
        
        # === 繪製 P1 圈速曲線 ===
        self._draw_single_lap_time_curve(
            painter, chart_rect, 
            self.p1_lap_times, 
            self.p1_color, 
            is_p1=True
        )
        
        # === 繪製 P2 圈速曲線 ===
        self._draw_single_lap_time_curve(
            painter, chart_rect, 
            self.p2_lap_times, 
            self.p2_color, 
            is_p1=False
        )
        
        #  在當前圈顯示時間差
        self._draw_lap_time_delta(painter, chart_rect)
    
    def _draw_single_lap_time_curve(self, painter: QPainter, chart_rect: QRectF,
                                     lap_times_dict: dict, color: str, is_p1: bool):
        """
        繪製單條圈速曲線
        
        Args:
            painter: QPainter 物件
            chart_rect: 圖表區域
            lap_times_dict: {lap: lap_time_seconds} 字典
            color: 曲線顏色（十六進位）
            is_p1: 是否為 P1 車手
        """
        if not lap_times_dict:
            return
        
        driver_label = self.p1_tla if is_p1 else self.p2_tla
        
        # === 過去實際圈速 (實線 + 圓點) ===
        pen_actual = QPen(QColor(color))
        pen_actual.setWidth(2)
        pen_actual.setStyle(Qt.SolidLine)
        painter.setPen(pen_actual)
        
        sorted_laps = sorted(lap_times_dict.keys())
        
        # ✅ 過濾進站圈和出站圈（與 Driver Strategy 一致）
        pit_laps_set = self.p1_pit_laps if is_p1 else self.p2_pit_laps
        pit_out_laps_set = self.p1_pit_out_laps if is_p1 else self.p2_pit_out_laps
        
        # 繪製實線連接圓點（跳過進站圈）
        for i in range(len(sorted_laps) - 1):
            lap1 = sorted_laps[i]
            lap2 = sorted_laps[i + 1]
            
            # ✅ 跳過進站圈和出站圈之間的連線
            if lap1 in pit_laps_set or lap1 in pit_out_laps_set:
                continue
            if lap2 in pit_laps_set or lap2 in pit_out_laps_set:
                continue
            
            time1 = lap_times_dict[lap1]
            time2 = lap_times_dict[lap2]
            
            x1 = self._lap_to_x(lap1, chart_rect)
            y1 = self._laptime_to_y(time1, chart_rect)
            x2 = self._lap_to_x(lap2, chart_rect)
            y2 = self._laptime_to_y(time2, chart_rect)
            
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        # 繪製實際圈速的圓點標記
        painter.setBrush(QBrush(QColor(color)))
        
        # ✅ 過濾進站圈和出站圈（這些圈速不具代表性）
        pit_laps_set = self.p1_pit_laps if is_p1 else self.p2_pit_laps
        pit_out_laps_set = self.p1_pit_out_laps if is_p1 else self.p2_pit_out_laps
        
        for lap in sorted_laps:
            # 跳過進站圈和出站圈
            if lap in pit_laps_set or lap in pit_out_laps_set:
                continue
            
            time = lap_times_dict[lap]
            x = self._lap_to_x(lap, chart_rect)
            y = self._laptime_to_y(time, chart_rect)
            painter.drawEllipse(QPointF(x, y), 2.5, 2.5)  # 圓點半徑 2.5px（與 Driver Strategy 一致）
        
        # === 預測未來圈速 (虛線) - 使用 QPainterPath 繪製連續路徑 ===
        pen_predict = QPen(QColor(color))
        pen_predict.setWidth(2)
        pen_predict.setStyle(Qt.DashLine)  # 虛線樣式
        painter.setPen(pen_predict)
        painter.setBrush(Qt.NoBrush)
        
        future_laps, future_p1_times, future_p2_times = self._calculate_future_lap_times()
        future_times = future_p1_times if is_p1 else future_p2_times
        
        if len(future_laps) > 0 and len(future_times) > 0:
            # 創建 QPainterPath（參考 Driver Strategy 實現）
            path = QPainterPath()
            first = True
            
            # 從當前圈的最後一個實際數據點開始
            if len(sorted_laps) > 0:
                last_actual_lap = sorted_laps[-1]
                last_actual_time = lap_times_dict[last_actual_lap]
                x = self._lap_to_x(last_actual_lap, chart_rect)
                y = self._laptime_to_y(last_actual_time, chart_rect)
                path.moveTo(x, y)
                first = False
            
            # 繪製所有預測點的連續路徑
            for i, lap in enumerate(future_laps):
                time = future_times[i]
                x = self._lap_to_x(lap, chart_rect)
                y = self._laptime_to_y(time, chart_rect)
                
                if first:
                    path.moveTo(x, y)
                    first = False
                else:
                    path.lineTo(x, y)
            
            # 繪製完整路徑（虛線會自動連續）
            painter.drawPath(path)
    
    def _draw_lap_time_delta(self, painter: QPainter, chart_rect: QRectF):
        """
        在當前圈顯示圈速差異（P2 - P1）
        
        注意：
        - Delta (Δ): 當前圈的圈速差異（本圈 P2 比 P1 快/慢多少秒）
        - Gap: 累積的總時間差（從比賽開始的總差距）
        
        例如：Gap = 1.977s（P2 落後 P1 總共 1.977 秒）
             Delta = +0.105s（本圈 P2 比 P1 慢 0.105 秒）
        """
        if self.current_lap <= 0:
            return
        
        # 檢查兩位車手的當前圈速是否都存在
        p1_time = self.p1_lap_times.get(self.current_lap)
        p2_time = self.p2_lap_times.get(self.current_lap)
        
        if p1_time is None or p2_time is None:
            return
        
        # 計算圈速差異（P2 - P1）：
        # 正值 = P2 本圈慢（Gap 增加）
        # 負值 = P2 本圈快（Gap 縮小）
        delta = p2_time - p1_time
        
        # 計算顯示位置（在較慢車手的曲線上方）
        x = self._lap_to_x(self.current_lap, chart_rect)
        y_p1 = self._laptime_to_y(p1_time, chart_rect)
        y_p2 = self._laptime_to_y(p2_time, chart_rect)
        
        #  修正：顯示在較慢車手上方 15 像素
        # 較慢車手的 Y 座標較大（圖表上方是慢圈速）
        slower_y = max(y_p1, y_p2)
        y_text = slower_y - 15  # 往上移 15 像素
        
        # 繪製時間差文字
        painter.setFont(self._font_axis)
        
        # 根據正負值設定顏色
        if delta > 0:
            # P2 慢：紅色
            painter.setPen(QPen(QColor('#FF6B6B')))
        elif delta < 0:
            # P2 快：綠色
            painter.setPen(QPen(QColor('#51CF66')))
        else:
            # 相同：白色
            painter.setPen(QPen(QColor(COLOR_TEXT)))
        
        # 格式化時間差（帶正負號）
        sign = "+" if delta >= 0 else ""
        delta_text = f"Δ {sign}{delta:.3f}s"
        
        fm = QFontMetrics(self._font_axis)
        text_width = fm.horizontalAdvance(delta_text)
        
        # 繪製文字（置中，往上偏移）
        painter.drawText(int(x - text_width / 2), int(y_text), delta_text)
    
    def _draw_current_lap_indicator(self, painter: QPainter, chart_rect: QRectF):
        """繪製當前圈指示線（青色虛線，參考 Driver Strategy）"""
        if self.current_lap <= 0 or self.total_laps <= 0:
            return
        
        # 使用與 Driver Strategy 相同的顏色和樣式
        pen = QPen(QColor('#4ECDC4'))  # COLOR_CURRENT_LAP
        pen.setWidth(1)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        
        x = self._lap_to_x(self.current_lap, chart_rect)
        painter.drawLine(
            QPointF(x, chart_rect.top()),
            QPointF(x, chart_rect.bottom())
        )
    
    def _draw_gap_values_on_line(self, painter: QPainter, chart_rect: QRectF, 
                                  past_laps: list, future_laps: list, future_gap_p2: list):
        """在線上顯示 Gap 數值（參考 Driver Strategy）"""
        painter.setFont(self._font_axis)
        
        # 在當前圈顯示當前 Gap
        if self.current_lap > 0:
            x = self._lap_to_x(self.current_lap, chart_rect)
            y = self._gap_to_y(self.current_gap, chart_rect)
            
            painter.setPen(QPen(QColor(self.p2_color)))
            gap_text = f"{self.current_gap:.2f}s"
            fm = QFontMetrics(self._font_axis)
            text_width = fm.horizontalAdvance(gap_text)
            painter.drawText(int(x - text_width / 2), int(y - 10), gap_text)
        
        # 在最後一圈顯示預測 Gap
        if len(future_laps) > 0 and len(future_gap_p2) > 0:
            last_lap = future_laps[-1]
            last_gap = future_gap_p2[-1]
            
            x = self._lap_to_x(last_lap, chart_rect)
            y = self._gap_to_y(last_gap, chart_rect)
            
            painter.setPen(QPen(QColor(self.p2_color)))
            gap_text = f"{last_gap:.2f}s"
            fm = QFontMetrics(self._font_axis)
            text_width = fm.horizontalAdvance(gap_text)
            painter.drawText(int(x - text_width / 2), int(y - 10), gap_text)
    
    def _calculate_future_lap_times(self):
        """
        計算未來圈速演變（使用策略的加權優勢值）
        
        ⚠️ 重要變更 (2025-12-09)：
        - 直接使用 strategy.advantage_per_lap（已包含 Trend+Theory 加權）
        - 不再重新計算理論輪胎衰退（避免與策略表格不一致）
        - Gap Evolution 預測線將與策略計算完全同步
        
        Returns:
            future_laps: 未來圈數列表
            future_p1_times: P1 預測圈速列表
            future_p2_times: P2 預測圈速列表
        """
        future_laps = list(range(self.current_lap + 1, self.total_laps + 1))  # 從下一圈開始預測
        future_p1_times = []
        future_p2_times = []
        
        #  修正：使用與 Driver Strategy 一致的基準圈速計算
        # 使用最快圈速作為基準（理想狀態），而非最近平均（當前狀態）
        # ✅ 傳入 stint 起始圈數，只計算當前 stint 的基準
        p1_base_time = self._calculate_base_lap_time(self.p1_lap_times, self.p1_stint_start_lap)
        p2_base_time = self._calculate_base_lap_time(self.p2_lap_times, self.p2_stint_start_lap)
        
        # ✅ 關鍵修正：直接使用策略計算的加權優勢值
        # advantage_per_lap 已經包含 Trend+Theory 加權，不需要重新計算
        advantage_per_lap = self.strategy.advantage_per_lap  # 加權後的每圈優勢
        pit_loss = self.strategy.pit_loss
        
        print(f"[LAP_TIME_PRED] ✅ 使用加權優勢值: {advantage_per_lap:+.4f} s/lap")
        print(f"  P1 base: {p1_base_time:.3f}s (stint from Lap {self.p1_stint_start_lap})")
        print(f"  P2 base: {p2_base_time:.3f}s (stint from Lap {self.p2_stint_start_lap})")
        
        #  強制要求 StrategyCalculator（無降級機制）
        strategy_calc = getattr(self, '_strategy_calculator', None)
        if not strategy_calc:
            print("[LAP_TIME_PRED]  StrategyCalculator 未載入，等待初始化完成...")
            return [], [], []  # 返回空列表，等待 calculator 設定完成
        
        # ✅ 簡化邏輯：只針對策略 1 使用加權優勢
        # 其他策略（進站、安全車）仍使用原有的詳細計算
        if self.strategy.strategy_id == 1:
            # 策略 1: 繼續當前輪胎 - P1 和 P2 都有輪胎衰退，但 P2 相對快 advantage_per_lap
            
            # 獲取當前輪胎齡
            p1_current_tyre_age = getattr(self, '_p1_tyre_age', 10)
            p2_current_tyre_age = getattr(self, '_p2_tyre_age', 10)
            
            # 獲取輪胎配方
            p1_compound = self.p1_compound if hasattr(self, 'p1_compound') else 'MEDIUM'
            p2_compound = self.p2_compound if hasattr(self, 'p2_compound') else 'MEDIUM'
            
            # 獲取賽道輪胎衰退數據
            circuit_db_key = RACE_TO_CIRCUIT_MAP.get(strategy_calc._circuit_name, strategy_calc._circuit_name)
            circuits = strategy_calc._tyre_deg_database.get('circuits', {})
            circuit_data = circuits.get(circuit_db_key, {})
            
            if circuit_data:
                base_deg_p1 = circuit_data.get('base_degradation', {}).get(p1_compound.upper(), 0.08)
                accel_p1 = circuit_data.get('degradation_acceleration', {}).get(p1_compound.upper(), 0.003)
                base_deg_p2 = circuit_data.get('base_degradation', {}).get(p2_compound.upper(), 0.05)
                accel_p2 = circuit_data.get('degradation_acceleration', {}).get(p2_compound.upper(), 0.002)
            else:
                default_base = {'SOFT': 0.08, 'MEDIUM': 0.05, 'HARD': 0.03}
                default_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001}
                base_deg_p1 = default_base.get(p1_compound.upper(), 0.05)
                accel_p1 = default_accel.get(p1_compound.upper(), 0.002)
                base_deg_p2 = default_base.get(p2_compound.upper(), 0.05)
                accel_p2 = default_accel.get(p2_compound.upper(), 0.002)
            
            # 配方抓地力優勢
            grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0}
            p1_grip = grip_advantage.get(p1_compound.upper(), 0.0)
            p2_grip = grip_advantage.get(p2_compound.upper(), 0.0)
            
            for lap in future_laps:
                laps_ahead = lap - self.current_lap
                
                # 計算未來輪胎齡
                p1_future_age = p1_current_tyre_age + laps_ahead
                p2_future_age = p2_current_tyre_age + laps_ahead
                
                # 輪胎衰退（二次方程式）
                p1_degradation = base_deg_p1 * p1_future_age + 0.5 * accel_p1 * (p1_future_age ** 2)
                p2_degradation = base_deg_p2 * p2_future_age + 0.5 * accel_p2 * (p2_future_age ** 2)
                
                # ✅ 關鍵修正：P2 每圈比 P1 快 advantage_per_lap
                # 所以 P2 的實際圈速 = base + degradation + grip - advantage_per_lap
                # P1 的實際圈速 = base + degradation + grip
                p1_time = p1_base_time + p1_degradation + p1_grip
                p2_time = p2_base_time + p2_degradation + p2_grip - advantage_per_lap
                
                future_p1_times.append(p1_time)
                future_p2_times.append(p2_time)
            
            return future_laps, future_p1_times, future_p2_times
        
        # 策略 2-5：保持原有詳細計算邏輯
        # 獲取當前輪胎齡（從 widget）
        p1_current_tyre_age = getattr(self, '_p1_tyre_age', 10)  # 預設 10 圈
        p2_current_tyre_age = getattr(self, '_p2_tyre_age', 10)
        
        # 獲取輪胎配方
        p1_compound = self.p1_compound if hasattr(self, 'p1_compound') else 'MEDIUM'
        p2_compound = self.p2_compound if hasattr(self, 'p2_compound') else 'MEDIUM'
        
        print(f"[LAP_TIME_PRED] P1: age={p1_current_tyre_age}, {p1_compound} | P2: age={p2_current_tyre_age}, {p2_compound}")
        
        for lap in future_laps:
            laps_ahead = lap - self.current_lap
            
            if self.strategy.strategy_id == 2:
                #  策略 1: 繼續當前輪胎 - 使用與 Driver Strategy 完全一致的二次方程式
                # 計算未來輪胎齡
                p1_future_age = p1_current_tyre_age + laps_ahead
                p2_future_age = p2_current_tyre_age + laps_ahead
                
                # 獲取賽道數據（與 Driver Strategy 一致）
                circuit_db_key = RACE_TO_CIRCUIT_MAP.get(strategy_calc._circuit_name, strategy_calc._circuit_name)
                circuits = strategy_calc._tyre_deg_database.get('circuits', {})
                circuit_data = circuits.get(circuit_db_key, {})
                
                if circuit_data:
                    base_deg_p1 = circuit_data.get('base_degradation', {}).get(p1_compound.upper(), 0.08)
                    accel_p1 = circuit_data.get('degradation_acceleration', {}).get(p1_compound.upper(), 0.003)
                    base_deg_p2 = circuit_data.get('base_degradation', {}).get(p2_compound.upper(), 0.05)
                    accel_p2 = circuit_data.get('degradation_acceleration', {}).get(p2_compound.upper(), 0.002)
                else:
                    # 預設值
                    default_base = {'SOFT': 0.08, 'MEDIUM': 0.05, 'HARD': 0.03}
                    default_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001}
                    base_deg_p1 = default_base.get(p1_compound.upper(), 0.05)
                    accel_p1 = default_accel.get(p1_compound.upper(), 0.002)
                    base_deg_p2 = default_base.get(p2_compound.upper(), 0.05)
                    accel_p2 = default_accel.get(p2_compound.upper(), 0.002)
                
                # 與 Driver Strategy 完全一致的二次方程式：
                # tyre_degradation = base_rate * tyre_age + 0.5 * acceleration * (tyre_age ** 2)
                p1_degradation = base_deg_p1 * p1_future_age + 0.5 * accel_p1 * (p1_future_age ** 2)
                p2_degradation = base_deg_p2 * p2_future_age + 0.5 * accel_p2 * (p2_future_age ** 2)
                
                # 配方抓地力優勢（與 Driver Strategy 一致）
                grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0}
                p1_grip = grip_advantage.get(p1_compound.upper(), 0.0)
                p2_grip = grip_advantage.get(p2_compound.upper(), 0.0)
                
                # 最終圈速 = 基準時間 + 輪胎衰退 + 配方優勢
                p1_time = p1_base_time + p1_degradation + p1_grip
                p2_time = p2_base_time + p2_degradation + p2_grip
            
            elif self.strategy.strategy_id == 2:
                #  策略 2: 立即進站 - P2 換新胎（使用與策略 1 一致的二次方程式）
                # 計算未來輪胎齡
                p1_future_age = p1_current_tyre_age + laps_ahead  # P1 輪胎繼續老化
                
                # P2 在第一圈進站，新胎齡從 0 開始
                if laps_ahead == 0:
                    # 進站當圈
                    p2_future_age = p2_current_tyre_age  # 進站前使用舊胎
                else:
                    p2_future_age = laps_ahead - 1  # 新胎齡（進站後重置）
                
                # 獲取賽道數據（與策略 1 完全一致）
                circuit_db_key = RACE_TO_CIRCUIT_MAP.get(strategy_calc._circuit_name, strategy_calc._circuit_name)
                circuits = strategy_calc._tyre_deg_database.get('circuits', {})
                circuit_data = circuits.get(circuit_db_key, {})
                
                if circuit_data:
                    base_deg_p1 = circuit_data.get('base_degradation', {}).get(p1_compound.upper(), 0.08)
                    accel_p1 = circuit_data.get('degradation_acceleration', {}).get(p1_compound.upper(), 0.003)
                    base_deg_p2 = circuit_data.get('base_degradation', {}).get(p2_compound.upper(), 0.05)
                    accel_p2 = circuit_data.get('degradation_acceleration', {}).get(p2_compound.upper(), 0.002)
                else:
                    # 預設值
                    default_base = {'SOFT': 0.08, 'MEDIUM': 0.05, 'HARD': 0.03}
                    default_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001}
                    base_deg_p1 = default_base.get(p1_compound.upper(), 0.05)
                    accel_p1 = default_accel.get(p1_compound.upper(), 0.002)
                    base_deg_p2 = default_base.get(p2_compound.upper(), 0.05)
                    accel_p2 = default_accel.get(p2_compound.upper(), 0.002)
                
                # 與 Driver Strategy 完全一致的二次方程式
                p1_degradation = base_deg_p1 * p1_future_age + 0.5 * accel_p1 * (p1_future_age ** 2)
                p2_degradation = base_deg_p2 * p2_future_age + 0.5 * accel_p2 * (p2_future_age ** 2)
                
                # 配方抓地力優勢
                grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0}
                p1_grip = grip_advantage.get(p1_compound.upper(), 0.0)
                p2_grip = grip_advantage.get(p2_compound.upper(), 0.0)
                
                # 計算圈速
                p1_time = p1_base_time + p1_degradation + p1_grip
                
                if laps_ahead == 0:
                    # 進站當圈：使用舊胎 + 進站損失
                    p2_time = p2_base_time + p2_degradation + p2_grip + pit_loss
                else:
                    # 進站後：新胎優勢（重置衰退）
                    p2_time = p2_base_time + p2_degradation + p2_grip
            
            elif self.strategy.strategy_id == 3:
                #  策略 3: 安全車 - 使用與策略 1 一致的二次方程式
                sc_lap_offset = self.strategy.sc_lap_offset
                
                # 計算未來輪胎齡
                if laps_ahead < sc_lap_offset:
                    # SC 前輪胎繼續老化
                    p1_future_age = p1_current_tyre_age + laps_ahead
                    p2_future_age = p2_current_tyre_age + laps_ahead
                else:
                    # SC 後輪胎繼續老化
                    p1_future_age = p1_current_tyre_age + laps_ahead
                    p2_future_age = p2_current_tyre_age + laps_ahead
                
                # 獲取賽道數據
                circuit_db_key = RACE_TO_CIRCUIT_MAP.get(strategy_calc._circuit_name, strategy_calc._circuit_name)
                circuits = strategy_calc._tyre_deg_database.get('circuits', {})
                circuit_data = circuits.get(circuit_db_key, {})
                
                if circuit_data:
                    base_deg_p1 = circuit_data.get('base_degradation', {}).get(p1_compound.upper(), 0.08)
                    accel_p1 = circuit_data.get('degradation_acceleration', {}).get(p1_compound.upper(), 0.003)
                    base_deg_p2 = circuit_data.get('base_degradation', {}).get(p2_compound.upper(), 0.05)
                    accel_p2 = circuit_data.get('degradation_acceleration', {}).get(p2_compound.upper(), 0.002)
                else:
                    default_base = {'SOFT': 0.08, 'MEDIUM': 0.05, 'HARD': 0.03}
                    default_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001}
                    base_deg_p1 = default_base.get(p1_compound.upper(), 0.05)
                    accel_p1 = default_accel.get(p1_compound.upper(), 0.002)
                    base_deg_p2 = default_base.get(p2_compound.upper(), 0.05)
                    accel_p2 = default_accel.get(p2_compound.upper(), 0.002)
                
                # 二次方程式計算輪胎衰退
                p1_degradation = base_deg_p1 * p1_future_age + 0.5 * accel_p1 * (p1_future_age ** 2)
                p2_degradation = base_deg_p2 * p2_future_age + 0.5 * accel_p2 * (p2_future_age ** 2)
                
                grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0}
                p1_grip = grip_advantage.get(p1_compound.upper(), 0.0)
                p2_grip = grip_advantage.get(p2_compound.upper(), 0.0)
                
                if laps_ahead < sc_lap_offset:
                    # SC 前速度變慢（+2秒罰時）
                    p1_time = p1_base_time + p1_degradation + p1_grip + 2.0
                    p2_time = p2_base_time + p2_degradation + p2_grip + 2.0
                else:
                    # SC 後恢復正常
                    p1_time = p1_base_time + p1_degradation + p1_grip
                    p2_time = p2_base_time + p2_degradation + p2_grip
            
            elif self.strategy.strategy_id == 4:
                #  策略 4: 主動模擬進站 - 使用與策略 1 一致的二次方程式
                # 計算未來輪胎齡
                p1_future_age = p1_current_tyre_age + laps_ahead  # P1 輪胎持續老化
                
                # P2 進站邏輯
                if self.active_pit_lap and lap >= self.active_pit_lap:
                    pit_offset = lap - self.active_pit_lap
                    if pit_offset == 0:
                        # 進站當圈：使用舊胎
                        p2_future_age = p2_current_tyre_age + laps_ahead
                    else:
                        # 進站後：新胎齡從 0 開始
                        p2_future_age = pit_offset - 1
                else:
                    # 還沒進站：繼續使用舊胎
                    p2_future_age = p2_current_tyre_age + laps_ahead
                
                # 獲取賽道數據
                circuit_db_key = RACE_TO_CIRCUIT_MAP.get(strategy_calc._circuit_name, strategy_calc._circuit_name)
                circuits = strategy_calc._tyre_deg_database.get('circuits', {})
                circuit_data = circuits.get(circuit_db_key, {})
                
                if circuit_data:
                    base_deg_p1 = circuit_data.get('base_degradation', {}).get(p1_compound.upper(), 0.08)
                    accel_p1 = circuit_data.get('degradation_acceleration', {}).get(p1_compound.upper(), 0.003)
                    base_deg_p2 = circuit_data.get('base_degradation', {}).get(p2_compound.upper(), 0.05)
                    accel_p2 = circuit_data.get('degradation_acceleration', {}).get(p2_compound.upper(), 0.002)
                else:
                    default_base = {'SOFT': 0.08, 'MEDIUM': 0.05, 'HARD': 0.03}
                    default_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001}
                    base_deg_p1 = default_base.get(p1_compound.upper(), 0.05)
                    accel_p1 = default_accel.get(p1_compound.upper(), 0.002)
                    base_deg_p2 = default_base.get(p2_compound.upper(), 0.05)
                    accel_p2 = default_accel.get(p2_compound.upper(), 0.002)
                
                # 二次方程式計算輪胎衰退
                p1_degradation = base_deg_p1 * p1_future_age + 0.5 * accel_p1 * (p1_future_age ** 2)
                p2_degradation = base_deg_p2 * p2_future_age + 0.5 * accel_p2 * (p2_future_age ** 2)
                
                grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0}
                p1_grip = grip_advantage.get(p1_compound.upper(), 0.0)
                p2_grip = grip_advantage.get(p2_compound.upper(), 0.0)
                
                # 計算圈速
                p1_time = p1_base_time + p1_degradation + p1_grip
                
                if self.active_pit_lap and lap >= self.active_pit_lap:
                    pit_offset = lap - self.active_pit_lap
                    if pit_offset == 0:
                        # 進站當圈：加上進站損失
                        p2_time = p2_base_time + p2_degradation + p2_grip + pit_loss
                    else:
                        # 進站後：新胎
                        p2_time = p2_base_time + p2_degradation + p2_grip
                else:
                    # 還沒進站
                    p2_time = p2_base_time + p2_degradation + p2_grip
            
            elif self.strategy.strategy_id == 5:
                #  策略 5: P1 先進站 - 使用與策略 1 一致的二次方程式
                p1_pit_lap_offset = 3
                
                if strategy_calc:
                    # 計算未來輪胎齡
                    if laps_ahead < p1_pit_lap_offset:
                        # P1 還沒進站，輪胎繼續老化
                        p1_future_age = p1_current_tyre_age + laps_ahead
                        p2_future_age = p2_current_tyre_age + laps_ahead
                    elif laps_ahead == p1_pit_lap_offset:
                        # P1 進站當圈：使用舊胎
                        p1_future_age = p1_current_tyre_age + laps_ahead
                        p2_future_age = p2_current_tyre_age + laps_ahead
                    else:
                        # P1 進站後：新胎齡從 0 開始
                        p1_future_age = laps_ahead - p1_pit_lap_offset - 1
                        # P2 繼續使用舊胎
                        p2_future_age = p2_current_tyre_age + laps_ahead
                    
                    # 獲取賽道數據
                    circuit_db_key = RACE_TO_CIRCUIT_MAP.get(strategy_calc._circuit_name, strategy_calc._circuit_name)
                    circuits = strategy_calc._tyre_deg_database.get('circuits', {})
                    circuit_data = circuits.get(circuit_db_key, {})
                    
                    if circuit_data:
                        base_deg_p1 = circuit_data.get('base_degradation', {}).get(p1_compound.upper(), 0.08)
                        accel_p1 = circuit_data.get('degradation_acceleration', {}).get(p1_compound.upper(), 0.003)
                        base_deg_p2 = circuit_data.get('base_degradation', {}).get(p2_compound.upper(), 0.05)
                        accel_p2 = circuit_data.get('degradation_acceleration', {}).get(p2_compound.upper(), 0.002)
                    else:
                        default_base = {'SOFT': 0.08, 'MEDIUM': 0.05, 'HARD': 0.03}
                        default_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001}
                        base_deg_p1 = default_base.get(p1_compound.upper(), 0.05)
                        accel_p1 = default_accel.get(p1_compound.upper(), 0.002)
                        base_deg_p2 = default_base.get(p2_compound.upper(), 0.05)
                        accel_p2 = default_accel.get(p2_compound.upper(), 0.002)
                    
                    # 二次方程式計算輪胎衰退
                    p1_degradation = base_deg_p1 * p1_future_age + 0.5 * accel_p1 * (p1_future_age ** 2)
                    p2_degradation = base_deg_p2 * p2_future_age + 0.5 * accel_p2 * (p2_future_age ** 2)
                    
                    grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0}
                    p1_grip = grip_advantage.get(p1_compound.upper(), 0.0)
                    p2_grip = grip_advantage.get(p2_compound.upper(), 0.0)
                    
                # 計算圈速
                if laps_ahead == p1_pit_lap_offset:
                    # P1 進站當圈：加上進站損失
                    p1_time = p1_base_time + p1_degradation + p1_grip + pit_loss
                    p2_time = p2_base_time + p2_degradation + p2_grip
                else:
                    # 正常圈速
                    p1_time = p1_base_time + p1_degradation + p1_grip
                    p2_time = p2_base_time + p2_degradation + p2_grip
            
            else:
                # 預設：兩者都正常衰減（使用二次方程式）
                p1_future_age = p1_current_tyre_age + laps_ahead
                p2_future_age = p2_current_tyre_age + laps_ahead
                
                circuit_db_key = RACE_TO_CIRCUIT_MAP.get(strategy_calc._circuit_name, strategy_calc._circuit_name)
                circuits = strategy_calc._tyre_deg_database.get('circuits', {})
                circuit_data = circuits.get(circuit_db_key, {})
                
                if circuit_data:
                    base_deg_p1 = circuit_data.get('base_degradation', {}).get(p1_compound.upper(), 0.08)
                    accel_p1 = circuit_data.get('degradation_acceleration', {}).get(p1_compound.upper(), 0.003)
                    base_deg_p2 = circuit_data.get('base_degradation', {}).get(p2_compound.upper(), 0.05)
                    accel_p2 = circuit_data.get('degradation_acceleration', {}).get(p2_compound.upper(), 0.002)
                else:
                    default_base = {'SOFT': 0.08, 'MEDIUM': 0.05, 'HARD': 0.03}
                    default_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001}
                    base_deg_p1 = default_base.get(p1_compound.upper(), 0.05)
                    accel_p1 = default_accel.get(p1_compound.upper(), 0.002)
                    base_deg_p2 = default_base.get(p2_compound.upper(), 0.05)
                    accel_p2 = default_accel.get(p2_compound.upper(), 0.002)
                
                p1_degradation = base_deg_p1 * p1_future_age + 0.5 * accel_p1 * (p1_future_age ** 2)
                p2_degradation = base_deg_p2 * p2_future_age + 0.5 * accel_p2 * (p2_future_age ** 2)
                
                grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0}
                p1_grip = grip_advantage.get(p1_compound.upper(), 0.0)
                p2_grip = grip_advantage.get(p2_compound.upper(), 0.0)
                
                p1_time = p1_base_time + p1_degradation + p1_grip
                p2_time = p2_base_time + p2_degradation + p2_grip
            
            future_p1_times.append(p1_time)
            future_p2_times.append(p2_time)
        
        return future_laps, future_p1_times, future_p2_times
    
    def _calculate_base_lap_time(self, lap_times_dict: dict, stint_start_lap: int = 1) -> float:
        """
        計算基準圈速（僅使用當前 stint 的數據）
        
        ⚠️ 重要變更 (2025-12-09)：
        - 只使用當前 stint 的圈速計算基準（從 stint_start_lap 開始）
        - 輪胎更換後會重置 stint_start_lap，確保衰退計算正確
        - 與 Driver Strategy 保持一致：5-25 百分位平均
        
        Args:
            lap_times_dict: {圈數: 圈速} 字典
            stint_start_lap: 當前 stint 的起始圈數（輪胎更換後重置）
            
        Returns:
            基準圈速（秒）
        """
        if not lap_times_dict:
            return 90.0  # 預設值
        
        # ✅ 只使用當前 stint 的圈速數據
        stint_times = [t for lap, t in lap_times_dict.items() if lap >= stint_start_lap and t > 0]
        if not stint_times:
            return 90.0
        
        sorted_times = sorted(stint_times)
        n = len(sorted_times)
        
        #  調試輸出：基準圈速計算細節
        print(f"\n[BASE_TIME_DEBUG] Gap Evolution 基準計算 (Stint from Lap {stint_start_lap}):")
        print(f"  Stint 圈數: {n}")
        print(f"  最快圈: {min(sorted_times):.3f}s")
        print(f"  最慢圈: {max(sorted_times):.3f}s")
        
        if n > 5:
            # 取第 5-25 百分位的平均（與 Driver Strategy 一致）
            start_idx = max(1, n // 20)  # 5th percentile
            end_idx = max(2, n // 4)     # 25th percentile
            selected_times = sorted_times[start_idx:end_idx]
            base_time = sum(selected_times) / len(selected_times)
            
            print(f"  使用百分位平均:")
            print(f"    - 索引範圍: [{start_idx}:{end_idx}] ({len(selected_times)} 圈)")
            print(f"    - 選中圈速: {selected_times}")
            print(f"    - 平均值: {base_time:.3f}s")
            return base_time
        elif n == 5:
            #  5 圈特殊處理：取中間 3 圈平均（排除極端值）
            selected_times = sorted_times[1:4]  # 去除最快和最慢
            base_time = sum(selected_times) / len(selected_times)
            print(f"  5 圈數據，使用中間 3 圈平均: {base_time:.3f}s")
            print(f"    - 選中圈速: {selected_times}")
            return base_time
        else:
            base_time = min(sorted_times)
            print(f"  圈數不足 ({n} 圈)，使用最快圈: {base_time:.3f}s")
            return base_time
    
    def _calculate_recent_avg_lap_time(self, lap_times_dict: dict, window: int = 3) -> float:
        """計算最近 N 圈的平均圈速"""
        if not lap_times_dict:
            return 90.0  # 預設值
        
        sorted_laps = sorted(lap_times_dict.keys())
        if not sorted_laps:
            return 90.0
        
        # 取最後 window 圈
        recent_laps = sorted_laps[-window:]
        recent_times = [lap_times_dict[lap] for lap in recent_laps]
        
        if not recent_times:
            return 90.0
        
        return sum(recent_times) / len(recent_times)
    
    def _calculate_average_lap_time(self, lap_times_dict: dict) -> float:
        """計算平均圈速（排除異常值）"""
        if not lap_times_dict:
            return 90.0  # 預設值
        
        times = list(lap_times_dict.values())
        if len(times) < 3:
            return sum(times) / len(times)
        
        # 排除最快和最慢的圈（避免異常值影響）
        sorted_times = sorted(times)
        middle_times = sorted_times[1:-1]
        
        if not middle_times:
            return sum(times) / len(times)
        
        return sum(middle_times) / len(middle_times)
    
    def _parse_lap_time_to_seconds(self, lap_time_str: str) -> float:
        """
        將圈速字串轉換為秒數
        
        Args:
            lap_time_str: 圈速字串，例如 "1:23.456" 或 "23.456"
        
        Returns:
            圈速秒數，例如 83.456
        """
        if not lap_time_str or lap_time_str == "" or lap_time_str == "--":
            return None
        
        try:
            # 處理格式: "1:23.456"
            if ':' in lap_time_str:
                parts = lap_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            # 處理格式: "23.456"
            else:
                return float(lap_time_str)
        except (ValueError, IndexError) as e:
            print(f"[LAP_TIME_PARSE]  無法解析圈速: {lap_time_str}, error: {e}")
            return None
    
    def _calculate_future_gap(self):
        """計算未來 Gap 演變（根據策略類型，使用真實數據）"""
        future_laps = list(range(self.current_lap, self.total_laps + 1))
        future_gap_p2 = []
        future_gap_p1 = []
        
        # 從 strategy 物件獲取真實數據
        advantage_per_lap = self.strategy.advantage_per_lap
        pit_loss = self.strategy.pit_loss
        sc_lap_offset = self.strategy.sc_lap_offset
        
        for lap in future_laps:
            laps_ahead = lap - self.current_lap
            
            if self.strategy.strategy_id == 1:
                # 策略 1: 繼續當前輪胎 - 使用真實的 advantage_per_lap
                gap_p2 = max(0, self.current_gap - advantage_per_lap * laps_ahead)
                gap_p1 = 0.0
            elif self.strategy.strategy_id == 2:
                # 策略 2: 立即進站 - 先擴大再縮小
                gap_p2 = self.current_gap + pit_loss - advantage_per_lap * laps_ahead
                gap_p1 = 0.0
            elif self.strategy.strategy_id == 3:
                # 策略 3: 安全車 - 使用真實的 sc_lap_offset
                if laps_ahead < sc_lap_offset:
                    gap_p2 = self.current_gap - 0.05 * laps_ahead  # SC 前緩慢縮小
                else:
                    gap_p2 = max(0, 5.0 - advantage_per_lap * (laps_ahead - sc_lap_offset))
                gap_p1 = 0.0
            elif self.strategy.strategy_id == 4:
                # 策略 4: 主動模擬
                if self.active_pit_lap and lap >= self.active_pit_lap:
                    pit_offset = lap - self.active_pit_lap
                    gap_p2 = self.current_gap + pit_loss - advantage_per_lap * pit_offset
                else:
                    gap_p2 = self.current_gap - 0.05 * laps_ahead
                gap_p1 = 0.0
            elif self.strategy.strategy_id == 5:
                # 策略 5: P1 先進站
                p1_pit_lap_offset = 3
                if laps_ahead < p1_pit_lap_offset:
                    gap_p1 = 0.0
                    gap_p2 = self.current_gap - advantage_per_lap * laps_ahead
                else:
                    gap_p1 = -pit_loss + advantage_per_lap * (laps_ahead - p1_pit_lap_offset)
                    gap_p2 = self.current_gap - advantage_per_lap * laps_ahead
            else:
                gap_p2 = self.current_gap
                gap_p1 = 0.0
            
            future_gap_p2.append(gap_p2)
            future_gap_p1.append(gap_p1)
        
        return future_laps, future_gap_p2, future_gap_p1
    
    def _draw_pit_markers(self, painter: QPainter, chart_rect: QRectF):
        """繪製進站標記（垂直線 + PIT 標籤，使用車手顏色）"""
        if self.total_laps <= 0:
            return
        
        painter.setFont(self._font_axis)
        
        # ✅ 合併所有進站圈，避免重複繪製垂直線
        all_pit_laps = set(self.p1_pit_laps) | set(self.p2_pit_laps)
        
        for lap in sorted(all_pit_laps):
            # 判斷此圈是哪位車手進站（或兩者都進站）
            p1_pitted = lap in self.p1_pit_laps
            p2_pitted = lap in self.p2_pit_laps
            
            # 選擇顏色：如果兩者都進站，使用混合色（或優先 P1）
            if p1_pitted and p2_pitted:
                color = self.p1_color  # 兩者都進站時優先顯示 P1 顏色
            elif p1_pitted:
                color = self.p1_color
            else:
                color = self.p2_color
            
            # 繪製垂直線（每個圈只畫一次）
            pen = QPen(QColor(color))
            pen.setWidth(2)
            pen.setStyle(Qt.DashDotLine)
            painter.setPen(pen)
            
            x = self._lap_to_x(lap, chart_rect)
            painter.drawLine(
                QPointF(x, chart_rect.top()),
                QPointF(x, chart_rect.bottom())
            )
            
            # ✅ 繪製 PIT 標籤（不顯示車手代碼，用顏色區分）
            painter.save()
            painter.setPen(pen)  # 重置筆觸（防止字體變粗）
            painter.translate(x - 5, chart_rect.top() + 15)
            painter.rotate(-90)
            painter.drawText(0, 0, "PIT")
            painter.restore()
    
    def _draw_markers(self, painter: QPainter, chart_rect: QRectF):
        """繪製標記（與 Driver Strategy 樣式一致）"""
        painter.setFont(self._font_axis)
        
        # 不再繪製 NOW 標記線，當前圈已經有圓點標記
        
        # Pit 標記 (策略 2: 立即進站, 策略 4: 主動模擬)
        if self.strategy.strategy_id in [2, 4] and self.active_pit_lap:
            pen_pit = QPen(QColor(COLOR_PIT_MARKER))
            pen_pit.setWidth(2)
            pen_pit.setStyle(Qt.DashDotLine)  # 與 Driver Strategy Pit 標記一致
            painter.setPen(pen_pit)
            
            x_pit = self._lap_to_x(self.active_pit_lap, chart_rect)
            painter.drawLine(
                QPointF(x_pit, chart_rect.top()),
                QPointF(x_pit, chart_rect.bottom())
            )
            
            # 繪製 "PIT" 標籤
            painter.save()
            painter.translate(x_pit - 5, chart_rect.top() + 15)
            painter.rotate(-90)
            painter.drawText(0, 0, "PIT")
            painter.restore()
        
        # 追上圈數標記 - 青色虛線
        if self.strategy.catchup_lap:
            pen = QPen(QColor(COLOR_CATCHUP_LAP))
            pen.setWidth(1)  # 改為較細的線
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            
            x_catchup = self._lap_to_x(self.strategy.catchup_lap, chart_rect)
            painter.drawLine(
                QPointF(x_catchup, chart_rect.top()),
                QPointF(x_catchup, chart_rect.bottom())
            )
            
            # 繪製 "CATCHUP" 標籤
            painter.save()
            painter.translate(x_catchup - 5, chart_rect.top() + 15)
            painter.rotate(-90)
            painter.drawText(0, 0, f"CATCHUP L{self.strategy.catchup_lap}")
            painter.restore()
    
    def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
        """繪製座標軸（顯示圈速而非 Gap）"""
        # 使用與 Driver Strategy 相同的座標軸顏色
        pen = QPen(QColor(COLOR_AXIS))  # '#888888'
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setFont(self._font_axis)
        
        # Y-axis (left side) - 圈速軸
        painter.drawLine(
            QPointF(chart_rect.left(), chart_rect.top()),
            QPointF(chart_rect.left(), chart_rect.bottom())
        )
        
        # Y-axis labels - 顯示圈速（秒）
        time_range = self._laptime_max - self._laptime_min
        if time_range > 0:
            tick_interval = self._calculate_tick_interval(time_range)
            time_start = math.ceil(self._laptime_min / tick_interval) * tick_interval
            lap_time = time_start
            while lap_time <= self._laptime_max:
                py = self._laptime_to_y(lap_time, chart_rect)
                # Tick mark
                painter.drawLine(
                    QPointF(chart_rect.left() - 5, py),
                    QPointF(chart_rect.left(), py)
                )
                # Label - 顯示圈速（例如："85.0s"）
                label = f"{lap_time:.1f}s"
                fm = QFontMetrics(self._font_axis)
                text_width = fm.horizontalAdvance(label)
                painter.drawText(
                    int(chart_rect.left() - text_width - 8),
                    int(py + fm.height() / 4),
                    label
                )
                lap_time += tick_interval
        
        # Y-axis title (rotated)
        painter.save()
        painter.setFont(self._font_label)
        painter.setPen(QPen(QColor(COLOR_TEXT)))
        title = "Lap Time (s)"  # 改為 "圈速（秒）"
        fm = QFontMetrics(self._font_label)
        title_width = fm.horizontalAdvance(title)
        painter.translate(15, chart_rect.center().y() + title_width / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, title)
        painter.restore()
        
        # X-axis (bottom) - 圈數軸
        painter.setPen(pen)
        painter.drawLine(
            QPointF(chart_rect.left(), chart_rect.bottom()),
            QPointF(chart_rect.right(), chart_rect.bottom())
        )
        
        # X-axis labels (laps)
        if self.total_laps > 0:
            lap_interval = max(1, self.total_laps // 10)
            for lap in range(0, self.total_laps + 1, lap_interval):
                if lap == 0:
                    continue
                px = self._lap_to_x(lap, chart_rect)
                # Tick mark
                painter.drawLine(
                    QPointF(px, chart_rect.bottom()),
                    QPointF(px, chart_rect.bottom() + 5)
                )
                # Label
                label = str(lap)
                fm = QFontMetrics(self._font_axis)
                text_width = fm.horizontalAdvance(label)
                painter.drawText(
                    int(px - text_width / 2),
                    int(chart_rect.bottom() + 18),
                    label
                )
        
        # X-axis title
        painter.setFont(self._font_label)
        painter.setPen(QPen(QColor(COLOR_TEXT)))
        title = "Lap"
        fm = QFontMetrics(self._font_label)
        title_width = fm.horizontalAdvance(title)
        painter.drawText(
            int(chart_rect.center().x() - title_width / 2),
            int(chart_rect.bottom() + 35),
            title
        )
    
    def _draw_legend(self, painter: QPainter, chart_rect: QRectF):
        """繪製圖例（與 Driver Strategy 一致）"""
        painter.setFont(self._font_legend)
        
        legend_x = chart_rect.right() - 200
        legend_y = chart_rect.top() + 10
        line_height = 20
        
        legends = [
            (self.p2_color, Qt.SolidLine, f"{self.p2_tla} (Actual)"),
            (self.p1_color, Qt.SolidLine, f"{self.p1_tla} (Actual)"),
            (self.p2_color, Qt.DashLine, f"{self.p2_tla} (Predicted)"),
            (self.p1_color, Qt.DashLine, f"{self.p1_tla} (Predicted)"),
        ]
        
        # 添加 Pit 標記到圖例
        if self.strategy.strategy_id in [2, 4] and self.active_pit_lap:
            legends.append((COLOR_PIT_MARKER, Qt.DashDotLine, f"Pit Stop (L{self.active_pit_lap})"))
        
        if self.strategy.catchup_lap:
            legends.append((COLOR_CATCHUP_LAP, Qt.DashLine, f"Catchup L{self.strategy.catchup_lap}"))
        
        for i, (color, style, label) in enumerate(legends):
            y = legend_y + i * line_height
            
            # 繪製線條
            pen = QPen(QColor(color))
            pen.setWidth(2)
            pen.setStyle(style)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(legend_x, y + 8),
                QPointF(legend_x + 30, y + 8)
            )
            
            # 繪製文字
            painter.setPen(QColor(COLOR_TEXT))
            painter.drawText(
                QRectF(legend_x + 35, y, 150, line_height),
                Qt.AlignLeft | Qt.AlignVCenter,
                label
            )
    
    def _draw_no_data_message(self, painter: QPainter, chart_rect: QRectF):
        """繪製無數據訊息"""
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.setPen(QPen(QColor(COLOR_TEXT)))
        
        message = "Waiting for lap time data..."
        fm = QFontMetrics(painter.font())
        text_width = fm.horizontalAdvance(message)
        text_height = fm.height()
        
        center_x = chart_rect.center().x()
        center_y = chart_rect.center().y()
        
        painter.drawText(
            int(center_x - text_width / 2),
            int(center_y - text_height / 2),
            message
        )
        
        # 副標題
        painter.setFont(QFont("Segoe UI", 10))
        sub_message = "Switch drivers to load data"
        fm = QFontMetrics(painter.font())
        sub_width = fm.horizontalAdvance(sub_message)
        sub_height = fm.height()
        
        painter.drawText(
            int(center_x - sub_width / 2),
            int(center_y + sub_height),
            sub_message
        )
    
    def _draw_error_message(self, painter: QPainter, chart_rect):
        """繪製錯誤訊息（防止白屏）"""
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.setPen(QPen(QColor('#FF6B6B')))  # 紅色
        
        message = "Rendering Error - Check console"
        fm = QFontMetrics(painter.font())
        text_width = fm.horizontalAdvance(message)
        
        if isinstance(chart_rect, QRectF):
            center_x = chart_rect.center().x()
            center_y = chart_rect.center().y()
        else:
            center_x = chart_rect.width() / 2
            center_y = chart_rect.height() / 2
        
        painter.drawText(
            int(center_x - text_width / 2),
            int(center_y),
            message
        )
    
    def _lap_to_x(self, lap: float, chart_rect: QRectF) -> float:
        """將圈數轉換為 X 座標"""
        if self.total_laps <= 0:
            return chart_rect.left()
        return chart_rect.left() + (lap / self.total_laps) * chart_rect.width()
    
    def _gap_to_y(self, gap: float, chart_rect: QRectF) -> float:
        """將 Gap 值轉換為 Y 座標"""
        gap_range = self._gap_max - self._gap_min
        if gap_range <= 0:
            return chart_rect.center().y()
        
        ratio = (gap - self._gap_min) / gap_range
        return chart_rect.bottom() - ratio * chart_rect.height()
    
    def _laptime_to_y(self, lap_time: float, chart_rect: QRectF) -> float:
        """將圈速值轉換為 Y 座標"""
        time_range = self._laptime_max - self._laptime_min
        if time_range <= 0:
            return chart_rect.center().y()
        
        ratio = (lap_time - self._laptime_min) / time_range
        # 注意：Y 軸反轉（越快的圈速在越上方）
        return chart_rect.bottom() - ratio * chart_rect.height()
    
    def _calculate_tick_interval(self, value_range: float) -> float:
        """計算合適的刻度間距"""
        if value_range <= 0:
            return 1.0
        
        magnitude = math.floor(math.log10(value_range))
        base = 10 ** magnitude
        
        if value_range / base > 5:
            return base * 2
        elif value_range / base > 2:
            return base
        else:
            return base / 2


# =============================================================================
# Chase Strategy MDI
# =============================================================================

class ChaseStrategyMDI(BaseLiveTimingMDI):
    """
    Chase Strategy MDI
    
    Live Timing MDI for P2 to P1 strategy analysis.
    """
    
    _window_title_key = "chase_strategy"
    _default_title = "Chase Strategy"
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr(self._window_title_key, self._default_title))
        # 只設定最小尺寸，不設定預設大小，讓 workspace 能正確恢復
        self.setMinimumSize(500, 300)  # 高度 350 -> 300
        # self.resize(800, 500)  # 移除預設大小，避免覆蓋 workspace 設定
        
        # 覆蓋基類樣式，確保表格邊框可見
        self.setStyleSheet("""
            QWidget#LiveTiming_ChaseStrategyMDI {
                background-color: #1a1a1a;
            }
            QWidget#LiveTiming_ChaseStrategyMDI QTableWidget {
                gridline-color: #333333;
            }
        """)
        
        print("[CHASE_STRATEGY_MDI] initialized")
    
    def _setup_ui(self):
        """Setup UI components"""
        self._widget = ChaseStrategyWidget(self)
        self._main_layout.addWidget(self._widget)
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Handle snapshot update"""
        # 獲取輪胎狀態 - 與 Ranking Tower 一致的邏輯
        # 1. 優先從 snapshot drivers 中提取（即時模式）
        # 2. 備用從 DataManager 獲取（歷史模式）
        tyre_state = {}
        drivers = snapshot.get('drivers', {})
        
        # 調試：檢查 snapshot.drivers 的內容
        if drivers:
            sample_num = next(iter(drivers.keys()))
            sample = drivers[sample_num]
            print(f"[CHASE_STRATEGY]  Snapshot has {len(drivers)} drivers")
            print(f"[CHASE_STRATEGY] Sample driver {sample_num}: pos={sample.get('position')}, tla={sample.get('tla')}")
            print(f"[CHASE_STRATEGY] Sample has compound={sample.get('compound')}, tyre_age={sample.get('tyre_age')}")
        
        # 優先從 snapshot 的 drivers 中提取
        print(f"[CHASE_STRATEGY]  Extracting tyre data from snapshot.drivers: {len(drivers)} drivers")
        for driver_num, driver_data in drivers.items():
            compound = driver_data.get('compound')
            tyre_age_raw = driver_data.get('tyre_age')
            driver_tla = driver_data.get('tla', driver_data.get('driver_tla', '???'))
            
            if compound or tyre_age_raw is not None:
                tyre_state[driver_num] = {
                    'compound': compound or 'UNKNOWN',
                    'tyre_age': tyre_age_raw if tyre_age_raw is not None else 0,  # 與 Ranking Tower 一致：使用 'tyre_age'
                    'tyre_new': driver_data.get('tyre_new', False),
                    'stint_count': driver_data.get('pit_count', 0) + 1,
                    'stints': driver_data.get('stints', []),
                }
                print(f"[CHASE_STRATEGY]  Driver {driver_num} ({driver_tla}): compound={compound}, tyre_age={tyre_age_raw} → stored as 'tyre_age'={tyre_state[driver_num]['tyre_age']}")
            else:
                print(f"[CHASE_STRATEGY]  Driver {driver_num} ({driver_tla}): NO tyre data (compound={compound}, tyre_age={tyre_age_raw})")
        
        # 如果 snapshot 沒有輪胎數據，嘗試從 DataManager 獲取
        if not tyre_state:
            print(f"[CHASE_STRATEGY]  No tyre data in snapshot, trying DataManager...")
            if self._data_manager and hasattr(self._data_manager, 'get_tyre_state'):
                tyre_state = self._data_manager.get_tyre_state()
                print(f"[CHASE_STRATEGY] DataManager returned {len(tyre_state)} drivers")
        else:
            print(f"[CHASE_STRATEGY]  Total tyre_state extracted: {len(tyre_state)} drivers")
        
        # 調試：顯示傳遞給 widget 的 tyre_state（只顯示前3個）
        if tyre_state:
            sample_drivers = list(tyre_state.items())[:3]
            print(f"[CHASE_STRATEGY]  Passing to widget: {len(tyre_state)} drivers, sample: {sample_drivers}")
        
        self._widget.update_snapshot(snapshot, tyre_state)
        
        #  更新所有打開的 Gap Evolution 視窗
        # 注意：追蹤列表在 self._widget 中，需要通過 _widget 訪問
        gap_widgets = getattr(self._widget, '_gap_evolution_widgets', [])
        print(f"[CHASE_STRATEGY_MDI]  Calling _update_gap_evolution_widgets, tracked widgets: {len(gap_widgets)}")
        self._update_gap_evolution_widgets(snapshot)
    
    def _update_gap_evolution_widgets(self, snapshot: Dict[str, Any]):
        """更新所有打開的 Gap Evolution 視窗"""
        #  修正：追蹤列表在 self._widget 中
        if not hasattr(self, '_widget') or not self._widget:
            return
        
        gap_widgets = getattr(self._widget, '_gap_evolution_widgets', [])
        
        # 移除已關閉的 widget
        gap_widgets = [w for w in gap_widgets if w and not w.isHidden()]
        self._widget._gap_evolution_widgets = gap_widgets  # 更新原列表
        
        if not gap_widgets:
            return  # 沒有打開的視窗
        
        print(f"[GAP_EVOLUTION_UPDATE]  Updating {len(gap_widgets)} widgets")
        
        # 從 widget 獲取當前選擇的車手和數據
        selected_p1 = getattr(self._widget, '_selected_p1', None)
        selected_p2 = getattr(self._widget, '_selected_p2', None)
        current_lap = getattr(self._widget, '_current_lap', 0)
        current_gap = getattr(self._widget, '_current_gap', 0.0)
        
        #  修復：從 tyre_state 獲取輪胎資訊（與 _refresh_strategies 一致）
        # 原本直接從 snapshot['drivers'] 獲取 compound，但該欄位可能不存在
        # 正確做法是從 tyre_state 獲取（由 _on_snapshot_updated 提取）
        tyre_state = getattr(self._widget, '_tyre_state', {})
        
        drivers = snapshot.get('drivers', {})
        print(f"[GAP_EVOLUTION_UPDATE]  Snapshot drivers: {list(drivers.keys())[:5]}...")
        print(f"[GAP_EVOLUTION_UPDATE]  Tyre state: {len(tyre_state)} drivers")
        print(f"[GAP_EVOLUTION_UPDATE]  Selected P1={selected_p1}, P2={selected_p2}")
        
        # 方法 1: 從 tyre_state 獲取（優先）
        p1_tyre = tyre_state.get(selected_p1, {})
        p2_tyre = tyre_state.get(selected_p2, {})
        
        p1_compound = p1_tyre.get('compound', None)
        p2_compound = p2_tyre.get('compound', None)
        
        # 方法 2: 如果 tyre_state 沒有數據，嘗試從 driver_data 獲取（備用）
        if not p1_compound:
            p1_data = drivers.get(selected_p1, {})
            p1_compound = p1_data.get('compound', None)
            print(f"[GAP_EVOLUTION_UPDATE]  P1 compound not in tyre_state, trying driver_data: {p1_compound}")
        
        if not p2_compound:
            p2_data = drivers.get(selected_p2, {})
            p2_compound = p2_data.get('compound', None)
            print(f"[GAP_EVOLUTION_UPDATE]  P2 compound not in tyre_state, trying driver_data: {p2_compound}")
        
        #  新增：提取圈速數據和輪胎齡
        p1_data = drivers.get(selected_p1, {})
        p2_data = drivers.get(selected_p2, {})
        
        # 從 snapshot 中獲取 last_lap_time (格式: "1:23.456")
        p1_last_lap_str = p1_data.get('last_lap_time', '')
        p2_last_lap_str = p2_data.get('last_lap_time', '')
        
        # 轉換為秒數
        p1_lap_time = self._parse_lap_time_to_seconds(p1_last_lap_str) if p1_last_lap_str else None
        p2_lap_time = self._parse_lap_time_to_seconds(p2_last_lap_str) if p2_last_lap_str else None
        
        #  新增：提取輪胎齡
        p1_tyre_age = p1_tyre.get('tyre_age', 0)
        p2_tyre_age = p2_tyre.get('tyre_age', 0)
        
        print(f"[GAP_EVOLUTION_UPDATE]  P1 compound={p1_compound}, P2 compound={p2_compound}")
        print(f"[GAP_EVOLUTION_UPDATE]  Current lap={current_lap}, gap={current_gap:.3f}s")
        print(f"[GAP_EVOLUTION_UPDATE]   P1 lap time={p1_lap_time}s, P2 lap time={p2_lap_time}s")
        print(f"[GAP_EVOLUTION_UPDATE]  P1 tyre age={p1_tyre_age}, P2 tyre age={p2_tyre_age}")
        
        # 更新每個 widget
        for widget in gap_widgets:
            try:
                widget.update_data(
                    current_lap=current_lap,
                    current_gap=current_gap,
                    p1_compound=p1_compound,
                    p2_compound=p2_compound,
                    p1_lap_time=p1_lap_time,
                    p2_lap_time=p2_lap_time,
                    p1_tyre_age=p1_tyre_age,
                    p2_tyre_age=p2_tyre_age
                )
            except Exception as e:
                print(f"[CHASE_STRATEGY]  更新 Gap Evolution widget 失敗: {e}")
    
    def _parse_lap_time_to_seconds(self, lap_time_str: str) -> float:
        """
        將圈速字串轉換為秒數
        
        Args:
            lap_time_str: 圈速字串，例如 "1:23.456" 或 "23.456"
        
        Returns:
            圈速秒數，例如 83.456
        """
        if not lap_time_str or lap_time_str == "" or lap_time_str == "--":
            return None
        
        try:
            # 處理格式: "1:23.456"
            if ':' in lap_time_str:
                parts = lap_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            # 處理格式: "23.456"
            else:
                return float(lap_time_str)
        except (ValueError, IndexError) as e:
            print(f"[LAP_TIME_PARSE]  無法解析圈速: {lap_time_str}, error: {e}")
            return None
    
    def _on_gap_widget_closed(self, widget: GapEvolutionChartWidget):
        """當 Gap Evolution 視窗關閉時移除追蹤"""
        #  修正：追蹤列表在 self._widget 中
        if hasattr(self, '_widget') and self._widget:
            gap_widgets = getattr(self._widget, '_gap_evolution_widgets', [])
            if widget in gap_widgets:
                gap_widgets.remove(widget)
                print(f"[CHASE_STRATEGY] Gap Evolution widget closed, remaining: {len(gap_widgets)}")
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Handle race loaded"""
        print(f"[CHASE_STRATEGY_MDI] Race loaded: {race_info.get('race', 'Unknown')}")
    
    def _on_race_unloaded(self):
        """Handle race unloaded"""
        self._widget.strategy_table.setRowCount(0)
        self._widget.info_label.setText(tr("no_data", "No data available"))
