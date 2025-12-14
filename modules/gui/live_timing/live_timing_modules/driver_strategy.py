# -*- coding: utf-8 -*-
"""
Driver Strategy Widget - PyQt5 Native Drawing Version
=====================================================
Displays predicted vs actual lap times for drivers.

Features:
- Actual lap time curve (cyan, solid line with circle markers)
- Predicted lap time curve (red, dashed line)
- Prediction range fill (red, semi-transparent)
- SC/VSC zones (yellow fill)
- Pit stop markers (yellow vertical lines with "PIT" text)
- Current lap indicator (cyan dotted vertical line)
- Interactive context menu
- Multi-driver tracking (all 20 drivers tracked simultaneously)

Uses PyQt5 native QPainter for optimal real-time performance.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal, pyqtSlot, QEvent
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPainterPath, QLinearGradient, QPolygonF
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QMenu, QAction, QMdiSubWindow
)

from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)


logger = get_logger("live_timing.driver_strategy", component="gui")


# =============================================================================
# Throttle Baseline Database Loader (API-ONLY Mode)
# =============================================================================
_THROTTLE_BASELINE_DATABASE: Optional[Dict] = None

def set_throttle_baseline_database(db: Dict):
    """
    設定 Throttle Baseline Database (由 API 載入後調用)
    
    Args:
        db: 從 API 獲取的 throttle_baseline 數據
    """
    global _THROTTLE_BASELINE_DATABASE
    _THROTTLE_BASELINE_DATABASE = db


def _load_throttle_baseline_database() -> Dict:
    """
    獲取 Throttle Baseline Database
    
    優先使用 API 設定的數據，若未設定則返回預設值。
    注意：此函數不再直接讀取本地檔案，符合 API-ONLY 模式。
    
    Returns:
        {
            "global_baseline": {...},
            "circuits": {...}
        }
    """
    global _THROTTLE_BASELINE_DATABASE
    
    if _THROTTLE_BASELINE_DATABASE is not None:
        return _THROTTLE_BASELINE_DATABASE
    
    # API 未設定時使用預設值
    logger.warning("[driver_strategy] Throttle baseline not loaded from API, using defaults")
    return {
        "global_baseline": {
            "full_throttle_ratio": {"mean": 0.35, "std": 0.05},
            "avg_throttle": {"mean": 43.0, "std": 5.0}
        },
        "circuits": {}
    }


def get_throttle_baseline_for_circuit(circuit_name: str) -> Dict:
    """
    獲取特定賽道的 Throttle Baseline
    
    Args:
        circuit_name: 賽道名稱 (例如 "Monza", "Suzuka")
        
    Returns:
        {
            "full_throttle_ratio": {"mean": float, "std": float, ...},
            "avg_throttle": float,
            "is_global": bool
        }
    """
    db = _load_throttle_baseline_database()
    circuits = db.get("circuits", {})
    global_baseline = db.get("global_baseline", {})
    
    # 嘗試直接匹配
    if circuit_name in circuits:
        data = circuits[circuit_name].copy()
        data["is_global"] = False
        return data
    
    # 嘗試模糊匹配
    for key in circuits:
        if key.lower() == circuit_name.lower():
            data = circuits[key].copy()
            data["is_global"] = False
            return data
        # 部分匹配
        if circuit_name.lower() in key.lower() or key.lower() in circuit_name.lower():
            data = circuits[key].copy()
            data["is_global"] = False
            return data
    
    # 使用全局基準值
    return {
        "full_throttle_ratio": global_baseline.get("full_throttle_ratio", {"mean": 0.35, "std": 0.05}),
        "avg_throttle": global_baseline.get("avg_throttle", {"mean": 43.0}),
        "is_global": True
    }


# =============================================================================
# Color Palette
# =============================================================================
COLOR_BACKGROUND = '#1a1a1a'
COLOR_CHART_BG = '#242424'
COLOR_GRID = '#3a3a3a'
COLOR_AXIS = '#888888'
COLOR_TEXT = '#ffffff'
COLOR_TEXT_DIM = '#888888'

COLOR_ACTUAL = '#4ECDC4'      # Cyan - actual lap times (default)
COLOR_PREDICTED = '#BB86FC'   # Light purple - predicted lap times
COLOR_PREDICTION_FILL = '#BB86FC'  # Light purple fill for prediction range
COLOR_SC_ZONE = '#FFD700'     # Yellow - SC/VSC zones
COLOR_PIT_MARKER = '#FFD700'  # Yellow - pit stop markers
COLOR_CURRENT_LAP = '#4ECDC4' # Cyan - current lap indicator
COLOR_FUEL_SAVING = '#00CC00' # Green - fuel saving zones

# Tyre compound colors
COLOR_TYRE_SOFT = '#FF3333'      # Red
COLOR_TYRE_MEDIUM = '#FFCC00'    # Yellow
COLOR_TYRE_HARD = '#FFFFFF'      # White
COLOR_TYRE_INTERMEDIATE = '#00CC00'  # Green
COLOR_TYRE_WET = '#0066FF'       # Blue


# =============================================================================
# DriverLapData - Lightweight Data Structure for Per-Driver Tracking
# =============================================================================
@dataclass
class DriverLapData:
    """
    Lightweight data structure to store per-driver lap data.
    Uses __slots__ equivalent via dataclass for memory efficiency.
    
    Tracks all 20 drivers simultaneously so switching is instant with full history.
    """
    driver_num: str = ""
    driver_tla: str = ""
    team_color: str = "FFFFFF"
    
    # Actual lap times: {lap_number: lap_time_seconds}
    actual_lap_times: Dict[int, float] = field(default_factory=dict)
    
    # Tyre compound per lap: {lap_number: compound_str}
    lap_compounds: Dict[int, str] = field(default_factory=dict)
    
    # Pit stop laps
    pit_laps: List[int] = field(default_factory=list)
    
    # PIT out laps (lap after pit - excluded from prediction)
    pit_out_laps: set = field(default_factory=set)
    
    # Last recorded lap number (to avoid duplicate processing)
    last_lap_recorded: int = 0
    
    # Current compound
    current_compound: str = ""
    
    # =========================================================================
    # F87 逐圈 Throttle 追蹤 (用於省胎評估)
    # =========================================================================
    # 當前圈的 throttle 樣本累積
    current_lap_throttle_samples: List[int] = field(default_factory=list)
    current_lap_being_tracked: int = 0
    
    # 每圈的 full throttle ratio: {lap_number: ratio (0.0-1.0)}
    lap_throttle_ratios: Dict[int, float] = field(default_factory=dict)
    
    # F87 省胎評估結果 (每圈更新)
    tire_saving_score: float = 0.0      # 0-100 (當前圈)
    tire_saving_level: str = "NONE"     # NONE/LIGHT/MODERATE/HEAVY
    tire_saving_adjustment: float = 0.0  # 補償係數 0-0.25
    lap_tire_saving_scores: Dict[int, float] = field(default_factory=dict)  # {圈數: 分數}
    
    def reset(self):
        """Reset all data for race restart."""
        self.actual_lap_times.clear()
        self.lap_compounds.clear()
        self.pit_laps.clear()
        self.pit_out_laps.clear()
        self.last_lap_recorded = 0
        self.current_compound = ""
        self.current_lap_throttle_samples.clear()
        self.current_lap_being_tracked = 0
        self.lap_throttle_ratios.clear()
        self.tire_saving_score = 0.0
        self.tire_saving_level = "NONE"
        self.tire_saving_adjustment = 0.0
        self.lap_tire_saving_scores.clear()


# =============================================================================
# F87 省胎分數計算 (靜態函數，可供任何車手使用)
# =============================================================================
def calculate_tire_saving_for_driver_data(
    driver_data: DriverLapData,
    sc_laps: set = None,
    pit_out_laps: set = None,
    circuit_name: str = None
) -> Tuple[float, str, float]:
    """
    F87: 計算單一車手的即時省胎分數 (使用 Throttle Baseline Database)
    
    省胎是**罕見行為**，正常比賽 SF% 應該接近 0%。
    只有當 full_throttle_ratio 明顯低於該賽道的基準值時才開始計分。
    
    算法:
    1. 從 database 獲取該賽道的 full_throttle_ratio 基準值
    2. 計算當前車手的實際 full_throttle_ratio
    3. SF% = max(0, (baseline - current) / baseline * 100)
    
    Args:
        driver_data: 車手的圈速數據
        sc_laps: SC 圈集合 (會排除)
        pit_out_laps: PIT 出站圈集合 (會排除)
        circuit_name: 賽道名稱 (用於獲取基準值)
        
    Returns:
        (score, level, adjustment): 分數(0-100), 等級, 補償係數
    """
    sc_laps = sc_laps or set()
    pit_out_laps = pit_out_laps or driver_data.pit_out_laps
    
    # 補償係數表
    ADJUSTMENTS = {
        "NONE": 0.0,
        "LIGHT": 0.08,
        "MODERATE": 0.15,
        "HEAVY": 0.25,
    }
    
    # 獲取賽道的 Throttle Baseline
    if circuit_name:
        baseline_data = get_throttle_baseline_for_circuit(circuit_name)
    else:
        baseline_data = get_throttle_baseline_for_circuit("")  # 使用全局基準
    
    baseline_ratio = baseline_data.get("full_throttle_ratio", {}).get("mean", 0.35)
    baseline_std = baseline_data.get("full_throttle_ratio", {}).get("std", 0.05)
    
    # 找到當前 stint 的起始圈
    stint_start_lap = 1
    if driver_data.pit_laps:
        stint_start_lap = max(driver_data.pit_laps) + 1
    
    # 獲取當前 stint 的有效圈數 (排除 SC 和 PIT OUT)
    stint_laps = [lap for lap in sorted(driver_data.actual_lap_times.keys())
                  if lap >= stint_start_lap
                  and lap not in sc_laps
                  and lap not in pit_out_laps]
    
    if len(stint_laps) < 3:
        return 0.0, "NONE", 0.0
    
    # 使用最近 5 圈
    window_size = 5
    recent_laps = stint_laps[-window_size:]
    
    # =====================================================================
    # 使用 Throttle Baseline Database 計算 SF%
    # =====================================================================
    if not driver_data.lap_throttle_ratios:
        return 0.0, "NONE", 0.0
    
    recent_throttle = [driver_data.lap_throttle_ratios.get(lap, 0.0) 
                       for lap in recent_laps 
                       if lap in driver_data.lap_throttle_ratios]
    
    if len(recent_throttle) < 2:
        return 0.0, "NONE", 0.0
    
    # 當前車手的 full_throttle_ratio
    current_ratio = sum(recent_throttle) / len(recent_throttle)
    
    # =====================================================================
    # SF% 計算公式:
    # - 只有低於 (baseline - threshold) 才開始計分
    # - threshold = baseline_std (通常 0.03-0.05)
    # - SF% = max(0, (baseline - current) / baseline * 100)
    # 
    # 例如 Monza: baseline = 0.42, std = 0.03
    # - current = 0.42 → SF = 0% (正常推進)
    # - current = 0.38 → SF = (0.42-0.38)/0.42*100 = 9.5%
    # - current = 0.30 → SF = (0.42-0.30)/0.42*100 = 28.6%
    # =====================================================================
    
    # 閾值: 低於 baseline - std 才開始計分省胎
    threshold = baseline_ratio - baseline_std
    
    if current_ratio >= threshold:
        score = 0.0
    else:
        # SF% = (baseline - current) / baseline * 100
        # 但要確保 baseline > 0 避免除以零
        if baseline_ratio > 0:
            score = max(0, (baseline_ratio - current_ratio) / baseline_ratio * 100)
        else:
            score = 0.0
        
        # 限制最大值為 50% (避免過度敏感)
        score = min(50, score)
    
    score = min(100, max(0, score))
    
    # 判斷等級 (基於 database 的閾值調整)
    # 正常比賽 SF% 應該是很小的數字
    if score < 5:
        level = "NONE"
    elif score < 15:
        level = "LIGHT"
    elif score < 30:
        level = "MODERATE"
    else:
        level = "HEAVY"
    
    adjustment = ADJUSTMENTS.get(level, 0.0)
    
    return score, level, adjustment


# =============================================================================
# DriverStrategyWidget - Main PyQt5 Native Drawing Widget
# =============================================================================
class DriverStrategyWidget(QWidget):
    """
    Driver strategy visualization using PyQt5 native drawing.
    
    Displays actual vs predicted lap times with SC zones, pit markers,
    and prediction range.
    """
    
    # Signals
    error_occurred = pyqtSignal(str)
    data_updated = pyqtSignal()
    driver_change_requested = pyqtSignal(str)  # 請求切換車手
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Chart area margins
        self._margin_left = 60
        self._margin_right = 20
        self._margin_top = 30  # Space for info bar
        self._margin_bottom = 35
        
        # Available drivers for context menu
        self._available_drivers: Dict[str, Dict[str, Any]] = {}
        
        # Data storage
        self._total_laps: int = 0
        self._current_lap: int = 0
        self._driver_code: str = ""
        self._driver_name: str = ""
        self._team_name: str = ""
        self._team_color: str = "4ECDC4"  # Default cyan
        self._current_compound: str = ""
        self._circuit_key: str = ""
        
        # Actual lap data: {lap_number: lap_time_seconds}
        self._actual_lap_times: Dict[int, float] = {}
        
        # Predicted lap data: {lap_number: lap_time_seconds}
        self._predicted_lap_times: Dict[int, float] = {}
        
        # Prediction range: {lap_number: (min_time, max_time)}
        self._prediction_range: Dict[int, Tuple[float, float]] = {}
        
        # Multi-compound prediction lines (三條配方預測線 S/M/H)
        # 格式: {compound: {lap_number: predicted_time}}
        self._multi_compound_predictions: Dict[str, Dict[int, float]] = {
            'SOFT': {},
            'MEDIUM': {},
            'HARD': {}
        }
        self._show_multi_compound: bool = True  # 是否顯示三條配方線
        
        # Pit stop laps: [lap1, lap2, ...]
        self._pit_laps: List[int] = []
        
        # SC/VSC zones: [(start_lap, end_lap), ...]
        self._sc_zones: List[Tuple[int, int]] = []
        
        # SC lap set for exclusion (laps under SC/VSC should not be displayed or predicted)
        self._sc_laps: set = set()
        
        # SC restart laps (lap after SC ends - also excluded)
        self._sc_restart_laps: set = set()
        
        # PIT out laps (lap after pit stop - excluded from prediction)
        self._pit_out_laps: set = set()
        
        # Tyre compound per lap: {lap_number: compound_str}
        self._lap_compounds: Dict[int, str] = {}
        
        # Stint tracking for pit prediction
        self._stint_start_lap: int = 1  # 當前 stint 開始圈數
        # List of (predicted_lap, actual_pit_lap) - actual_pit_lap=0 means not yet pitted
        self._predicted_pit_laps: List[Tuple[int, int]] = []
        self._current_predicted_pit: int = 0  # 當前 stint 的預估換胎圈數
        
        # =====================================================================
        # F87 即時省胎評估系統 (逐圈計算)
        # =====================================================================
        # 用於動態調整 PIT Est：根據 throttle 使用率和 lap_time 趨勢判斷車手是否在省胎
        self._tire_saving_adjustment: float = 0.0  # 當前省胎補償 (0-25%)
        self._tire_saving_level: str = "NONE"  # NONE/LIGHT/MODERATE/HEAVY
        self._tire_saving_score: float = 0.0  # 省胎分數 (0-100)
        
        # 逐圈數據追蹤 (用於省胎計算)
        self._lap_throttle_samples: List[int] = []  # 當前圈的 throttle 樣本 (每次 snapshot 更新)
        self._lap_throttle_ratios: Dict[int, float] = {}  # {lap: full_throttle_ratio}
        self._lap_times_for_saving: Dict[int, float] = {}  # {lap: lap_time_seconds}
        self._current_lap_for_throttle: int = 0  # 用於追蹤圈數變化
        
        # 補償係數表 (與 F87 realtime_pit_predictor 一致)
        self._TIRE_SAVING_ADJUSTMENTS = {
            "NONE": 0.0,
            "LIGHT": 0.08,      # +8%
            "MODERATE": 0.15,   # +15%
            "HEAVY": 0.25,      # +25%
        }
        
        # 省胎評估權重 (與 F87 一致)
        self._SAVING_WEIGHTS = {
            "throttle": 0.50,      # 油門使用率權重
            "lap_time": 0.30,      # 圈速趨勢權重
            "consistency": 0.20,   # 穩定性權重
        }
        
        # Prediction error correction
        self._correction_factor: float = 0.0
        self._correction_enabled: bool = True
        
        # Database references
        self._strategy_database: Dict[str, Any] = {}
        self._tyre_deg_database: Dict[str, Any] = {}
        self._fuel_coeff_database: Dict[str, Any] = {}
        
        # Y-axis range (lap time in seconds)
        self._y_min: float = 0.0
        self._y_max: float = 120.0
        
        # Cached fonts
        self._font_title = QFont("Arial", 11, QFont.Bold)
        self._font_label = QFont("Arial", 9)
        self._font_axis = QFont("Arial", 8)
        self._font_legend = QFont("Arial", 9)
        
        # Initialize UI
        self._setup_ui()
        self._load_databases()
        
        # Update timer for smooth animations
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self.update)
        
        self.setMinimumSize(200, 150)  # 允許更小的視窗尺寸
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def _setup_ui(self):
        """Setup the main UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(2)
        
        # Info bar at top (using layout, not frame)
        self._setup_info_bar(main_layout)
        
        # Add stretch for chart area (widget draws itself via paintEvent)
        main_layout.addStretch()
        
        # Chart area (this widget draws itself)
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        
        # Right-click menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _show_context_menu(self, pos):
        """Show context menu at position."""
        global_pos = self.mapToGlobal(pos)
        
        class FakeEvent:
            def globalPos(self_inner):
                return global_pos
        
        self.contextMenuEvent(FakeEvent())
        
    def _setup_info_bar(self, layout: QVBoxLayout):
        """Setup the information bar at the top using layout."""
        info_layout = QHBoxLayout()
        info_layout.setSpacing(15)
        
        # Driver label
        self._driver_label = QLabel(tr("Driver") + ": --")
        self._driver_label.setStyleSheet(f"color: {COLOR_ACTUAL}; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(self._driver_label)
        
        # Tyre label
        self._tyre_label = QLabel(tr("Tyre") + ": --")
        self._tyre_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 11px;")
        info_layout.addWidget(self._tyre_label)
        
        # Estimated lap time label
        self._est_label = QLabel("Est: --")
        self._est_label.setStyleSheet(f"color: {COLOR_PREDICTED}; font-size: 11px;")
        info_layout.addWidget(self._est_label)
        
        # Last lap time label
        self._last_label = QLabel("Last: --")
        self._last_label.setStyleSheet(f"color: {COLOR_ACTUAL}; font-size: 11px;")
        info_layout.addWidget(self._last_label)
        
        # Delta label (difference between Est and Last)
        self._delta_label = QLabel("Δ: --")
        self._delta_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 11px;")
        info_layout.addWidget(self._delta_label)
        
        info_layout.addStretch()
        
        # Lap counter
        self._lap_counter_label = QLabel(tr("Lap") + ": 0/0")
        self._lap_counter_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(self._lap_counter_label)
        
        layout.addLayout(info_layout)
        
    def _load_databases(self):
        """Load strategy, tyre degradation, and fuel coefficient databases.
        
        僅使用 API 獲取，禁止本地回退
        """
        # 僅通過 API 獲取
        if self._load_databases_via_api():
            return
        
        # API 失敗，顯示錯誤（禁止本地回退）
        logger.error("[DRIVER_STRATEGY] API 獲取配置失敗，請確認 API 服務器已啟動")
    
    def _load_databases_via_api(self) -> bool:
        """通過 API 獲取所有配置數據庫"""
        try:
            from modules.gui.live_timing.core.api_client import get_api_client
            
            api_client = get_api_client()
            
            # 一次性獲取所有配置
            all_configs = api_client.get_all_configs()
            
            if all_configs:
                self._strategy_database = all_configs.get('track_features', {})
                self._tyre_deg_database = all_configs.get('tire_degradation', {})
                self._fuel_coeff_database = all_configs.get('fuel_coefficients', {})
                
                # 載入 Throttle Baseline Database (F87 省胎分析)
                throttle_baseline = all_configs.get('throttle_baseline', {})
                if throttle_baseline:
                    set_throttle_baseline_database(throttle_baseline)
                    circuits_count = len(throttle_baseline.get('circuits', {}))
                else:
                    circuits_count = 0
                
                logger.info(
                    "[DRIVER_STRATEGY] 配置載入成功 (API): track_features=%d, tire_deg=%d, fuel_coeff=%d, throttle_baseline=%d circuits",
                    len(self._strategy_database),
                    len(self._tyre_deg_database),
                    len(self._fuel_coeff_database),
                    circuits_count,
                )
                return True
            
            return False
            
        except Exception as e:
            logger.exception("[DRIVER_STRATEGY] API 獲取配置失敗: %s", e)
            return False
    
    # =========================================================================
    # Data Setters
    # =========================================================================
    
    def set_total_laps(self, laps: int):
        """Set total laps for the race."""
        self._total_laps = laps
        self._update_lap_counter()
        self.update()
        
    def set_driver_info(self, driver_code: str, driver_name: str = "", team_color: str = ""):
        """Set driver information with team color."""
        self._driver_code = driver_code
        self._driver_name = driver_name or driver_code
        self._team_color = team_color or "4ECDC4"  # Default cyan
        
        # Update label with team color
        self._driver_label.setText(f"{tr('Driver')}: {self._driver_code}")
        self._driver_label.setStyleSheet(f"color: #{self._team_color}; font-weight: bold; font-size: 11px;")
        self.update()
        
    def set_circuit(self, circuit_key: str):
        """Set circuit key for database lookups."""
        self._circuit_key = circuit_key
        
    def set_compound(self, compound: str):
        """Set current tyre compound with color coding."""
        self._current_compound = compound
        
        # 輪胎顏色: M=黃色, S=紅色, H=白色, I=綠色
        compound_colors = {
            'SOFT': '#FF3333',      # 紅色
            'S': '#FF3333',
            'MEDIUM': '#FFCC00',    # 黃色
            'M': '#FFCC00',
            'HARD': '#FFFFFF',      # 白色
            'H': '#FFFFFF',
            'INTERMEDIATE': '#00CC00',  # 綠色
            'I': '#00CC00',
            'WET': '#0066FF',       # 藍色
            'W': '#0066FF',
        }
        
        color = compound_colors.get(compound.upper(), '#CCCCCC')
        self._tyre_label.setText(f"{tr('Tyre')}: {compound}")
        self._tyre_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
        
    def select_driver(self, driver_code: str, driver_name: str = "", team_color: str = ""):
        """Select a driver and reset data for fresh display."""
        self._reset_driver_data()
        self.set_driver_info(driver_code, driver_name, team_color)
        
    def _reset_driver_data(self):
        """Reset all driver-specific data."""
        self._actual_lap_times.clear()
        self._predicted_lap_times.clear()
        self._prediction_range.clear()
        self._multi_compound_predictions['SOFT'].clear()
        self._multi_compound_predictions['MEDIUM'].clear()
        self._multi_compound_predictions['HARD'].clear()
        self._pit_laps.clear()
        self._sc_zones.clear()
        self._sc_laps.clear()
        self._sc_restart_laps.clear()
        self._pit_out_laps.clear()
        self._lap_compounds.clear()
        self._predicted_pit_laps.clear()  # Clear predicted pit history
        self._current_predicted_pit = 0
        self._stint_start_lap = 1
        self._current_lap = 0
        self._correction_factor = 0.0
        self._current_compound = ""
        self._update_lap_counter()
        self.update()
        
    def load_driver_history(self, actual_lap_times: Dict[int, float],
                            lap_compounds: Dict[int, str],
                            pit_laps: List[int],
                            pit_out_laps: set,
                            sc_laps: set = None,
                            sc_restart_laps: set = None,
                            current_compound: str = "",
                            current_lap: int = 0,
                            lap_throttle_ratios: Dict[int, float] = None,
                            lap_tire_saving_scores: Dict[int, float] = None):
        """
        Load complete driver history from MDI's multi-driver tracking.
        
        This enables instant switching between drivers with full history preserved.
        Called when user switches to a different driver.
        
        Args:
            actual_lap_times: {lap_number: lap_time_seconds}
            lap_compounds: {lap_number: compound_str}
            pit_laps: List of pit stop lap numbers
            pit_out_laps: Set of pit out lap numbers
            sc_laps: Set of SC/VSC lap numbers (global)
            sc_restart_laps: Set of SC restart lap numbers (global)
            current_compound: Current tyre compound
            current_lap: Current/last lap number
            lap_throttle_ratios: {lap_number: full_throttle_ratio} for F87 tire saving
            lap_tire_saving_scores: {lap_number: score} 每圈省胎分數
        """
        # Reset first to clear old data
        self._reset_driver_data()
        
        # Load all historical data
        self._actual_lap_times = actual_lap_times
        self._lap_compounds = lap_compounds
        self._pit_laps = list(pit_laps)
        self._pit_out_laps = pit_out_laps
        self._current_compound = current_compound
        self._current_lap = current_lap
        
        # F87: 載入 throttle 數據
        if lap_throttle_ratios:
            self._lap_throttle_ratios = lap_throttle_ratios
            self._lap_times_for_saving = {k: v for k, v in actual_lap_times.items()}
        
        # F87: 載入每圈省胎分數
        if lap_tire_saving_scores:
            self._lap_tire_saving_scores = lap_tire_saving_scores
        else:
            self._lap_tire_saving_scores = {}
        
        # Calculate stint start lap from last pit stop
        if pit_laps:
            self._stint_start_lap = max(pit_laps) + 1
        else:
            self._stint_start_lap = 1
        
        # Load global SC data and generate zones for drawing
        if sc_laps is not None:
            self._sc_laps = sc_laps
            # Generate _sc_zones from _sc_laps for drawing
            self._generate_sc_zones_from_laps()
        if sc_restart_laps is not None:
            self._sc_restart_laps = sc_restart_laps
        
        # Update compound display
        if current_compound:
            self.set_compound(current_compound)
        
        # Recalculate predictions based on loaded history
        # Use lap-by-lap simulation to match Realtime correction behavior
        if self._actual_lap_times and self._correction_enabled:
            self._simulate_realtime_corrections(actual_lap_times, pit_laps)
        elif self._actual_lap_times:
            self._calculate_all_predictions()
            
        # Backfill historical stint predictions for each stint
        self._backfill_historical_pit_predictions(pit_laps, lap_compounds)
        
        # F87: 更新進站預測 (SF% 由 DataManager 計算)
        self._update_predicted_pit_lap()
        
        # 重新計算預測以包含多配方線（需要在 _update_predicted_pit_lap 之後）
        if self._actual_lap_times:
            self._calculate_all_predictions()
        
        self._calculate_y_range()
        
        # Update UI
        self._update_lap_counter()
        self.update()
        self.data_updated.emit()
        
        logger.info(
            "[DRIVER_STRATEGY] load_driver_history: loaded %d laps, sc=%d laps, current=%s, correction_factor=%.4f, tire_saving=%s",
            len(actual_lap_times),
            len(sc_laps or set()),
            current_lap,
            self._correction_factor,
            self._tire_saving_level,
        )
        
    # =========================================================================
    # Lap Data Update
    # =========================================================================
    
    def update_lap_data(self, lap_number: int, lap_time: Optional[float],
                        compound: str = "", is_pit_lap: bool = False,
                        is_sc_lap: bool = False, is_vsc_lap: bool = False):
        """
        Update data for a specific lap.
        
        Args:
            lap_number: The lap number
            lap_time: Actual lap time in seconds (None if not available)
            compound: Tyre compound
            is_pit_lap: Whether this lap includes a pit stop
            is_sc_lap: Whether SC was deployed
            is_vsc_lap: Whether VSC was deployed
        """
        logger.debug(
            "[DRIVER_STRATEGY] update_lap_data: lap=%s, time=%s, compound=%s, SC=%s, VSC=%s",
            lap_number,
            lap_time,
            compound,
            is_sc_lap,
            is_vsc_lap,
        )
        
        self._current_lap = lap_number
        
        # Update compound and store for this lap
        if compound:
            self.set_compound(compound)
            self._lap_compounds[lap_number] = compound
        elif self._current_compound:
            # Use current compound if not specified
            self._lap_compounds[lap_number] = self._current_compound
        
        # Track SC/VSC zones and exclude SC laps
        if is_sc_lap or is_vsc_lap:
            self._update_sc_zone(lap_number)
            self._sc_laps.add(lap_number)
            logger.info("[DRIVER_STRATEGY] SC/VSC lap %s excluded from display and prediction", lap_number)
            # Don't store SC lap time, just update UI and return
            self._update_lap_counter()
            self.update()
            self.data_updated.emit()
            return
        
        # Check if this is a SC restart lap (previous lap was SC)
        if (lap_number - 1) in self._sc_laps:
            self._sc_restart_laps.add(lap_number)
            logger.info("[DRIVER_STRATEGY] SC restart lap %s excluded from display and prediction", lap_number)
            # Don't store SC restart lap time, but still update predictions and UI
            self._calculate_all_predictions()
            self._calculate_y_range()
            self._update_lap_counter()
            self.update()
            self.data_updated.emit()
            return
        
        # Check if this is a PIT out lap (previous lap was pit)
        if (lap_number - 1) in self._pit_laps:
            self._pit_out_laps.add(lap_number)
            logger.info("[DRIVER_STRATEGY] PIT out lap %s - not used for prediction", lap_number)
            # Store the time but mark for exclusion in prediction
            
        # Check if this is a PIT lap
        is_excluded_pit = is_pit_lap or lap_number in self._pit_out_laps
        
        # Store actual lap time (excluding SC, SC restart, PIT, PIT out laps)
        if lap_time is not None and lap_time > 0 and not is_excluded_pit:
            self._actual_lap_times[lap_number] = lap_time
            logger.debug(
                "[DRIVER_STRATEGY] Stored lap time: lap %s = %.3fs, total points: %d",
                lap_number,
                lap_time,
                len(self._actual_lap_times),
            )
        elif lap_time is not None and lap_time > 0 and is_excluded_pit:
            logger.info(
                "[DRIVER_STRATEGY] PIT/PIT-out lap %s time=%.3fs excluded from prediction",
                lap_number,
                lap_time,
            )
            
        # Track pit stops
        if is_pit_lap and lap_number not in self._pit_laps:
            self._pit_laps.append(lap_number)
            # Mark next lap as pit out lap for future reference
            self._pit_out_laps.add(lap_number + 1)
            # Reset stint start lap for new tyres
            self._stint_start_lap = lap_number + 1
            logger.info(
                "[DRIVER_STRATEGY] PIT at lap %s, new stint starts at lap %s",
                lap_number,
                self._stint_start_lap,
            )
            
        # Calculate predictions
        self._calculate_all_predictions()
        
        # Update predicted pit lap based on optimal stint length
        self._update_predicted_pit_lap()
        
        # Apply self-correction if enabled
        if self._correction_enabled:
            self._apply_self_correction()
            
        # Update Y range
        self._calculate_y_range()
        
        # Update UI
        self._update_lap_counter()
        self.update()
        self.data_updated.emit()
        
    def _update_sc_zone(self, lap_number: int):
        """Update SC/VSC zones with the given lap."""
        if not self._sc_zones:
            self._sc_zones.append((lap_number, lap_number))
        else:
            # Extend the last zone if consecutive
            last_start, last_end = self._sc_zones[-1]
            if lap_number == last_end + 1:
                self._sc_zones[-1] = (last_start, lap_number)
            elif lap_number > last_end + 1:
                self._sc_zones.append((lap_number, lap_number))
                
    def _generate_sc_zones_from_laps(self):
        """
        Generate _sc_zones list from _sc_laps set.
        Converts individual SC laps into continuous zones for drawing.
        """
        self._sc_zones.clear()
        if not self._sc_laps:
            return
            
        sorted_laps = sorted(self._sc_laps)
        if not sorted_laps:
            return
            
        # Build zones from consecutive laps
        zone_start = sorted_laps[0]
        zone_end = sorted_laps[0]
        
        for lap in sorted_laps[1:]:
            if lap == zone_end + 1:
                # Extend current zone
                zone_end = lap
            else:
                # Save current zone and start new one
                self._sc_zones.append((zone_start, zone_end))
                zone_start = lap
                zone_end = lap
        
        # Don't forget the last zone
        self._sc_zones.append((zone_start, zone_end))
        logger.debug("[DRIVER_STRATEGY] Generated SC zones: %s", self._sc_zones)
                
    def _update_lap_counter(self):
        """Update the lap counter label."""
        self._lap_counter_label.setText(f"{tr('Lap')}: {self._current_lap}/{self._total_laps}")
        
        # 更新 Est、Last、Δ 標籤
        self._update_timing_labels()
    
    def _update_timing_labels(self):
        """Update Est, Last, and Delta labels based on current lap data."""
        # 獲取上一圈的實際圈速
        last_lap = self._current_lap - 1 if self._current_lap > 1 else self._current_lap
        last_time = self._actual_lap_times.get(last_lap)
        
        # 獲取當前圈的預測圈速
        est_time = self._predicted_lap_times.get(self._current_lap)
        
        # 如果沒有當前圈預測，使用上一圈預測
        if est_time is None and last_lap in self._predicted_lap_times:
            est_time = self._predicted_lap_times.get(last_lap)
        
        # 更新 Est 標籤
        if est_time is not None:
            est_str = self._format_lap_time(est_time)
            self._est_label.setText(f"Est: {est_str}")
            self._est_label.setStyleSheet(f"color: {COLOR_PREDICTED}; font-size: 11px; font-weight: bold;")
        else:
            self._est_label.setText("Est: --")
            self._est_label.setStyleSheet(f"color: {COLOR_PREDICTED}; font-size: 11px;")
        
        # 更新 Last 標籤
        if last_time is not None:
            last_str = self._format_lap_time(last_time)
            self._last_label.setText(f"Last: {last_str}")
            self._last_label.setStyleSheet(f"color: {COLOR_ACTUAL}; font-size: 11px; font-weight: bold;")
        else:
            self._last_label.setText("Last: --")
            self._last_label.setStyleSheet(f"color: {COLOR_ACTUAL}; font-size: 11px;")
        
        # 更新 Δ 標籤 (Est - Last，負值表示比預測快)
        if est_time is not None and last_time is not None:
            delta = last_time - est_time  # 正值 = 比預測慢，負值 = 比預測快
            delta_str = f"{delta:+.3f}" if abs(delta) < 10 else f"{delta:+.1f}"
            
            # 顏色：綠色 = 比預測快，紅色 = 比預測慢
            if delta < -0.1:
                delta_color = "#00FF00"  # 綠色 - 比預測快
            elif delta > 0.1:
                delta_color = "#FF4444"  # 紅色 - 比預測慢
            else:
                delta_color = COLOR_TEXT  # 接近預測
            
            self._delta_label.setText(f"Δ: {delta_str}")
            self._delta_label.setStyleSheet(f"color: {delta_color}; font-size: 11px; font-weight: bold;")
        else:
            self._delta_label.setText("Δ: --")
            self._delta_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 11px;")
    
    def _format_lap_time(self, seconds: float) -> str:
        """Format lap time in seconds to M:SS.mmm format."""
        if seconds <= 0:
            return "--"
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    # 賽事名稱到賽道名稱的映射 (race name -> circuit key in database)
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
    
    def _backfill_historical_pit_predictions(self, pit_laps, lap_compounds: Dict[int, str]):
        """
        Backfill predicted pit laps for historical stints.
        
        When loading historical data, we need to calculate what the predicted
        pit lap would have been for each past stint based on optimal stint length.
        """
        logger.debug(
            "[DRIVER_STRATEGY] _backfill called: circuit=%s, pit_laps=%s, lap_compounds keys=%s",
            self._circuit_key,
            pit_laps,
            list(lap_compounds.keys())[:5],
        )
        
        if not self._circuit_key:
            logger.info("[DRIVER_STRATEGY] Backfill skipped: no circuit_key")
            return
            
        # Get circuit data for optimal stint calculation
        circuit_db_key = self.RACE_TO_CIRCUIT_MAP.get(self._circuit_key, self._circuit_key)
        circuits = self._tyre_deg_database.get('circuits', {})
        
        # 調試: 輸出可用的賽道列表
        if not circuits:
            logger.debug("[DRIVER_STRATEGY] Backfill: _tyre_deg_database is empty or has no 'circuits' key")
            logger.debug("[DRIVER_STRATEGY] Backfill: _tyre_deg_database keys = %s", list(self._tyre_deg_database.keys())[:5])
        else:
            logger.debug("[DRIVER_STRATEGY] Backfill: Available circuits = %s", list(circuits.keys()))
        
        circuit_data = circuits.get(circuit_db_key, {})
        
        if not circuit_data:
            for key, data in circuits.items():
                if circuit_db_key.lower() in key.lower() or key.lower() in circuit_db_key.lower():
                    circuit_data = data
                    break
        
        if not circuit_data:
            logger.info("[DRIVER_STRATEGY] Backfill skipped: no circuit_data for %s", circuit_db_key)
            return
            
        optimal_stint = circuit_data.get('optimal_stint_length', {})
        
        # Sort pit laps - handle both Set and List
        sorted_pits = sorted(list(pit_laps)) if pit_laps else []
        logger.debug("[DRIVER_STRATEGY] Backfill sorted_pits=%s", sorted_pits)
        
        # Calculate stint boundaries: [(stint_start, stint_end, compound), ...]
        stint_boundaries = []
        
        # First stint starts at lap 1
        prev_stint_start = 1
        for pit_lap in sorted_pits:
            # Find compound for this stint - search from stint start to pit lap
            compound = ''
            for lap in range(prev_stint_start, pit_lap + 1):
                compound = lap_compounds.get(lap, '')
                if compound:
                    break
            logger.debug("[DRIVER_STRATEGY] Backfill stint: start=%s, pit=%s, compound=%s", prev_stint_start, pit_lap, compound)
            if compound:
                stint_boundaries.append((prev_stint_start, pit_lap, compound))
            prev_stint_start = pit_lap + 1
        
        # Calculate predicted pit for each historical stint
        for stint_start, actual_pit, compound in stint_boundaries:
            compound_key = compound.upper()
            if compound_key in ['S', 'SOFT']:
                compound_key = 'SOFT'
            elif compound_key in ['M', 'MEDIUM']:
                compound_key = 'MEDIUM'
            elif compound_key in ['H', 'HARD']:
                compound_key = 'HARD'
            elif compound_key in ['I', 'INTERMEDIATE']:
                compound_key = 'INTERMEDIATE'
            elif compound_key in ['W', 'WET']:
                compound_key = 'WET'
            
            stint_length = optimal_stint.get(compound_key, 0)
            if stint_length <= 0:
                defaults = {'SOFT': 18, 'MEDIUM': 28, 'HARD': 40, 'INTERMEDIATE': 25, 'WET': 20}
                stint_length = defaults.get(compound_key, 25)
            
            predicted_lap = stint_start + stint_length
            
            if predicted_lap < self._total_laps:
                # Check if this prediction already exists
                existing = [p for p, a in self._predicted_pit_laps if p == predicted_lap]
                if not existing:
                    self._predicted_pit_laps.append((predicted_lap, actual_pit))
                    logger.debug(
                        "[DRIVER_STRATEGY] Backfilled historical PIT prediction: lap %s, actual=%s (stint %s-%s, %s)",
                        predicted_lap,
                        actual_pit,
                        stint_start,
                        actual_pit,
                        compound_key,
                    )
    
    def _update_predicted_pit_lap(self):
        """
        Update predicted pit lap based on optimal stint length from database.
        
        Uses current compound and circuit to look up optimal stint length,
        then calculates when the driver should pit based on stint start lap.
        
        F87 Enhancement: Applies tire saving adjustment to extend predicted stint.
        """
        if not self._circuit_key or not self._current_compound:
            self._current_predicted_pit = 0
            logger.info(
                "[DRIVER_STRATEGY] PIT prediction skipped: circuit=%s, compound=%s",
                self._circuit_key,
                self._current_compound,
            )
            return
        
        # 將賽事名稱映射到資料庫中的賽道 key
        circuit_db_key = self.RACE_TO_CIRCUIT_MAP.get(self._circuit_key, self._circuit_key)
            
        # Get circuit data from database
        circuits = self._tyre_deg_database.get('circuits', {})
        
        # 調試輸出
        if not circuits:
            logger.warning("[DRIVER_STRATEGY] PIT: _tyre_deg_database has no 'circuits' key")
            logger.warning("[DRIVER_STRATEGY] PIT: _tyre_deg_database keys = %s", list(self._tyre_deg_database.keys()))
        
        circuit_data = circuits.get(circuit_db_key, {})
        
        if not circuit_data:
            # Try matching by partial name using the mapped key
            for key, data in circuits.items():
                if circuit_db_key.lower() in key.lower() or key.lower() in circuit_db_key.lower():
                    circuit_data = data
                    logger.info("[DRIVER_STRATEGY] Circuit matched: %s -> %s", self._circuit_key, key)
                    break
        
        if not circuit_data:
            self._current_predicted_pit = 0
            logger.info(
                "[DRIVER_STRATEGY] PIT prediction skipped: no circuit data for '%s' (mapped: %s)",
                self._circuit_key,
                circuit_db_key,
            )
            return
            
        # Get optimal stint length for current compound
        optimal_stint = circuit_data.get('optimal_stint_length', {})
        compound_key = self._current_compound.upper()
        
        # Handle compound name variations
        if compound_key in ['S', 'SOFT']:
            compound_key = 'SOFT'
        elif compound_key in ['M', 'MEDIUM']:
            compound_key = 'MEDIUM'
        elif compound_key in ['H', 'HARD']:
            compound_key = 'HARD'
        elif compound_key in ['I', 'INTERMEDIATE']:
            compound_key = 'INTERMEDIATE'
        elif compound_key in ['W', 'WET']:
            compound_key = 'WET'
            
        stint_length = optimal_stint.get(compound_key, 0)
        
        if stint_length <= 0:
            # Use default values if not in database
            defaults = {'SOFT': 18, 'MEDIUM': 28, 'HARD': 40, 'INTERMEDIATE': 25, 'WET': 20}
            stint_length = defaults.get(compound_key, 25)
        
        # =====================================================================
        # F87: 應用省胎補償
        # =====================================================================
        base_stint = stint_length
        adjusted_stint = int(stint_length * (1 + self._tire_saving_adjustment))
        stint_length = adjusted_stint
        
        # Calculate predicted pit lap
        predicted_lap = self._stint_start_lap + stint_length
        
        # Don't predict beyond total laps
        if predicted_lap >= self._total_laps:
            self._current_predicted_pit = 0  # No pit needed - can finish on current tyres
            logger.info(
                "[DRIVER_STRATEGY] No PIT needed - predicted %s >= total %s (base: %s, F87 adj: +%s = %s laps for %s)",
                predicted_lap,
                self._total_laps,
                base_stint,
                f"{self._tire_saving_adjustment:.0%}",
                adjusted_stint,
                compound_key,
            )
        else:
            self._current_predicted_pit = predicted_lap
            # Add to history if not already there (0 means not yet pitted)
            existing = [p for p, a in self._predicted_pit_laps if p == predicted_lap]
            if not existing:
                self._predicted_pit_laps.append((predicted_lap, 0))
                logger.info(
                    "[DRIVER_STRATEGY] Predicted PIT at lap %s (base: %s, F87 adj: +%s = %s laps, %s)",
                    predicted_lap,
                    base_stint,
                    f"{self._tire_saving_adjustment:.0%}",
                    adjusted_stint,
                    self._tire_saving_level,
                )
        
    # =========================================================================
    # Prediction Calculations - Stint-Based Model
    # =========================================================================
    
    def _calculate_all_predictions(self):
        """
        Calculate predicted lap times for ALL laps using stint-based model.
        
        Each stint (between pit stops) has its own prediction curve based on:
        1. Base lap time from actual data
        2. Tyre degradation (compound-specific from database)
        3. Fuel effect (lighter car = faster)
        4. Self-correction factor
        
        This ensures prediction slopes change after each pit stop.
        """
        if self._total_laps <= 0:
            return
        
        # 收集所有需要排除的圈數
        excluded_laps = self._sc_laps | self._sc_restart_laps | set(self._pit_laps) | self._pit_out_laps
        
        # 建立 stint 邊界: [(stint_start, stint_end, compound), ...]
        stints = self._build_stint_boundaries()
        
        if not stints:
            return
        
        # 計算基準圈速（從實際數據中獲取）
        base_lap_time = self._calculate_base_lap_time(excluded_laps)
        if base_lap_time <= 0:
            base_lap_time = 90.0  # 預設值
        
        # 獲取賽道數據
        circuit_db_key = self.RACE_TO_CIRCUIT_MAP.get(self._circuit_key, self._circuit_key)
        circuits = self._tyre_deg_database.get('circuits', {})
        circuit_data = circuits.get(circuit_db_key, {})
        
        # 如果找不到賽道數據，嘗試模糊匹配
        if not circuit_data:
            for key, data in circuits.items():
                if circuit_db_key.lower() in key.lower() or key.lower() in circuit_db_key.lower():
                    circuit_data = data
                    break
        
        # 預測所有圈數
        self._predicted_lap_times.clear()
        self._prediction_range.clear()
        self._multi_compound_predictions['SOFT'].clear()
        self._multi_compound_predictions['MEDIUM'].clear()
        self._multi_compound_predictions['HARD'].clear()
        
        for lap in range(1, self._total_laps + 1):
            if lap in excluded_laps:
                continue
            
            # 找到這一圈所屬的 stint
            stint_info = self._get_stint_for_lap(lap, stints)
            if not stint_info:
                continue
            
            stint_start, stint_end, compound = stint_info
            tyre_age = lap - stint_start + 1  # 輪胎圈數（從 1 開始）
            
            # 計算當前配方的預測圈速
            predicted = self._calculate_stint_prediction(
                lap, tyre_age, compound, base_lap_time, circuit_data
            )
            
            # 加入修正因子
            predicted += self._correction_factor
            
            # 確保在合理範圍
            predicted = max(predicted, 60.0)
            predicted = min(predicted, 180.0)
            
            self._predicted_lap_times[lap] = predicted
            
            # 預測範圍 (+-3%)
            margin = predicted * 0.03
            self._prediction_range[lap] = (predicted - margin, predicted + margin)
            
            # =====================================================================
            # 計算三種配方的預測曲線 (S/M/H)
            # 
            # ⚠️ 關鍵邏輯: 只在 PIT Est 之後顯示三條配方線
            # - 目的: 比較換胎後選擇不同配方的策略效果
            # - 起始圈: self._current_predicted_pit (預估進站圈數)
            # - 三條線從進站後的第一圈開始 (tyre_age=1)
            # =====================================================================
            if self._show_multi_compound and self._current_predicted_pit > 0:
                # 只在預估進站圈之後才繪製多配方線
                if lap >= self._current_predicted_pit:
                    # 計算換胎後的輪胎圈數 (從進站後重新計算)
                    alt_tyre_age = lap - self._current_predicted_pit + 1
                    
                    for alt_compound in ['SOFT', 'MEDIUM', 'HARD']:
                        # 假設在 PIT Est 進站後換成該配方
                        alt_predicted = self._calculate_stint_prediction(
                            lap, alt_tyre_age, alt_compound, base_lap_time, circuit_data
                        )
                        alt_predicted += self._correction_factor
                        alt_predicted = max(alt_predicted, 60.0)
                        alt_predicted = min(alt_predicted, 180.0)
                        self._multi_compound_predictions[alt_compound][lap] = alt_predicted
    
    def _build_stint_boundaries(self) -> List[Tuple[int, int, str]]:
        """
        Build stint boundaries from pit stops and compound data.
        
        Returns:
            List of (stint_start, stint_end, compound) tuples
        """
        stints = []
        sorted_pits = sorted(self._pit_laps) if self._pit_laps else []
        
        # 第一個 stint
        stint_start = 1
        
        for pit_lap in sorted_pits:
            stint_end = pit_lap
            compound = self._get_compound_for_stint(stint_start, stint_end)
            if compound:
                stints.append((stint_start, stint_end, compound))
            stint_start = pit_lap + 1
        
        # 最後一個 stint（從最後一個 PIT 到比賽結束）
        compound = self._get_compound_for_stint(stint_start, self._total_laps)
        if not compound:
            compound = self._current_compound or 'MEDIUM'
        stints.append((stint_start, self._total_laps, compound))
        
        logger.debug("[DRIVER_STRATEGY] Built %s stints: %s", len(stints), stints)
        return stints
    
    def _get_compound_for_stint(self, stint_start: int, stint_end: int) -> str:
        """Get the compound used in a stint."""
        # 從 stint 中找第一個有記錄的配方
        for lap in range(stint_start, stint_end + 1):
            compound = self._lap_compounds.get(lap, '')
            if compound:
                return compound.upper()
        return ''
    
    def _get_stint_for_lap(self, lap: int, stints: List[Tuple[int, int, str]]) -> Optional[Tuple[int, int, str]]:
        """Find which stint a lap belongs to."""
        for stint_start, stint_end, compound in stints:
            if stint_start <= lap <= stint_end:
                return (stint_start, stint_end, compound)
        return None
    
    def _calculate_base_lap_time(self, excluded_laps: set) -> float:
        """Calculate base lap time from actual data."""
        valid_times = [
            time for lap, time in self._actual_lap_times.items()
            if lap not in excluded_laps and time > 0
        ]
        if valid_times:
            # 使用最快圈速作為基準（排除最快的 5% 以避免異常值）
            sorted_times = sorted(valid_times)
            n = len(sorted_times)
            
            # 🔍 調試輸出：Driver Strategy 基準計算
            logger.debug("[BASE_TIME_DEBUG] Driver Strategy 基準計算:")
            logger.debug("  總圈數: %s", n)
            logger.debug("  最快圈: %.3fs", min(sorted_times))
            logger.debug("  最慢圈: %.3fs", max(sorted_times))
            logger.debug("  圈速範圍: %s ... %s", sorted_times[:3], sorted_times[-3:])
            
            if n > 5:
                # 取第 5-25 百分位的平均作為基準
                start_idx = max(1, n // 20)
                end_idx = max(2, n // 4)
                selected_times = sorted_times[start_idx:end_idx]
                base_time = sum(selected_times) / len(selected_times)
                
                logger.debug(
                    "  使用百分位平均: [%s:%s] (%s 圈), 選中圈速: %s, 平均值: %.3fs",
                    start_idx,
                    end_idx,
                    len(selected_times),
                    selected_times,
                    base_time,
                )
                return base_time
            elif n == 5:
                # ✅ 5 圈特殊處理：取中間 3 圈平均（排除極端值）
                selected_times = sorted_times[1:4]  # 去除最快和最慢
                base_time = sum(selected_times) / len(selected_times)
                logger.debug("  5 圈數據，使用中間 3 圈平均: %.3fs, 選中圈速: %s", base_time, selected_times)
                return base_time
            else:
                base_time = min(sorted_times)
                logger.debug("  圈數不足 (%s 圈)，使用最快圈: %.3fs", n, base_time)
                return base_time
        return 0.0
    
    def _calculate_stint_prediction(self, lap: int, tyre_age: int, compound: str,
                                     base_lap_time: float, circuit_data: Dict) -> float:
        """
        Calculate predicted lap time for a specific lap within a stint.
        
        Uses time-varying linear degradation model:
        degradation(t) = base_rate + acceleration * tyre_age
        
        Args:
            lap: The lap number
            tyre_age: Laps on current tyres (1-based)
            compound: Tyre compound (SOFT, MEDIUM, HARD, etc.)
            base_lap_time: Base lap time (fastest clean lap)
            circuit_data: Circuit-specific data from database
        """
        # 標準化配方名稱
        compound_key = compound.upper()
        if compound_key in ['S', 'SOFT']:
            compound_key = 'SOFT'
        elif compound_key in ['M', 'MEDIUM']:
            compound_key = 'MEDIUM'
        elif compound_key in ['H', 'HARD']:
            compound_key = 'HARD'
        elif compound_key in ['I', 'INTERMEDIATE']:
            compound_key = 'INTERMEDIATE'
        elif compound_key in ['W', 'WET']:
            compound_key = 'WET'
        
        # 獲取衰退參數
        base_deg = circuit_data.get('base_degradation', {})
        deg_accel = circuit_data.get('degradation_acceleration', {})
        
        # 預設衰退值（如果資料庫沒有）
        default_base_deg = {'SOFT': 0.08, 'MEDIUM': 0.05, 'HARD': 0.03, 'INTERMEDIATE': 0.06, 'WET': 0.04}
        default_deg_accel = {'SOFT': 0.003, 'MEDIUM': 0.002, 'HARD': 0.001, 'INTERMEDIATE': 0.002, 'WET': 0.0015}
        
        base_rate = base_deg.get(compound_key, default_base_deg.get(compound_key, 0.05))
        acceleration = deg_accel.get(compound_key, default_deg_accel.get(compound_key, 0.002))
        
        # 計算輪胎衰退效果（時變線性模型）
        # degradation(t) = base_rate * t + 0.5 * acceleration * t^2
        tyre_degradation = base_rate * tyre_age + 0.5 * acceleration * (tyre_age ** 2)
        
        # 計算燃油效果（油量減少 = 車更輕 = 更快）
        fuel_effect = self._get_fuel_effect(lap)
        
        # 配方抓地力優勢
        grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0, 'INTERMEDIATE': -0.3, 'WET': -0.2}
        compound_advantage = grip_advantage.get(compound_key, 0.0)
        
        # 最終預測 = 基準時間 + 輪胎衰退 + 燃油效果 + 配方優勢
        predicted = base_lap_time + tyre_degradation + fuel_effect + compound_advantage
        
        return predicted
                
    def _calculate_predicted_lap_time(self, lap_number: int) -> float:
        """
        Calculate predicted lap time for a specific lap.
        Uses stint-based tyre degradation and fuel effect models.
        """
        # Get base lap time from actual data or estimate
        if self._actual_lap_times:
            base_time = min(self._actual_lap_times.values())
        else:
            # Default base time
            base_time = 90.0
        
        # 找到這一圈所屬的 stint
        stints = self._build_stint_boundaries()
        stint_info = self._get_stint_for_lap(lap_number, stints)
        
        if stint_info:
            stint_start, stint_end, compound = stint_info
            tyre_age = lap_number - stint_start + 1
            
            # 獲取賽道數據
            circuit_db_key = self.RACE_TO_CIRCUIT_MAP.get(self._circuit_key, self._circuit_key)
            circuits = self._tyre_deg_database.get('circuits', {})
            circuit_data = circuits.get(circuit_db_key, {})
            
            # 使用 stint-based 計算
            predicted = self._calculate_stint_prediction(
                lap_number, tyre_age, compound, base_time, circuit_data
            )
        else:
            # Fallback to simple calculation
            tyre_deg = self._get_tyre_degradation(lap_number)
            fuel_effect = self._get_fuel_effect(lap_number)
            predicted = base_time + tyre_deg + fuel_effect
        
        return max(predicted + self._correction_factor, 60.0)
        
    def _get_tyre_degradation(self, lap_number: int) -> float:
        """Get tyre degradation effect for the lap (fallback method)."""
        if not self._current_compound or not self._circuit_key:
            return 0.0
        
        # 計算 tyre age（從最後一個 PIT 開始）
        if self._pit_laps:
            last_pit = max(self._pit_laps)
            if lap_number > last_pit:
                tyre_age = lap_number - last_pit
            else:
                tyre_age = lap_number
        else:
            tyre_age = lap_number
            
        # Look up in database
        circuit_db_key = self.RACE_TO_CIRCUIT_MAP.get(self._circuit_key, self._circuit_key)
        circuits = self._tyre_deg_database.get('circuits', {})
        circuit_data = circuits.get(circuit_db_key, {})
        
        base_deg = circuit_data.get('base_degradation', {})
        compound_deg = base_deg.get(self._current_compound.upper(), 0.05)
        
        # Degradation increases with tyre age
        return compound_deg * tyre_age
        
    def _get_fuel_effect(self, lap_number: int) -> float:
        """Get fuel effect for the lap (negative = faster)."""
        if self._total_laps <= 0:
            return 0.0
        
        # 獲取燃油係數
        circuit_db_key = self.RACE_TO_CIRCUIT_MAP.get(self._circuit_key, self._circuit_key)
        fuel_data = self._fuel_coeff_database.get('circuits', {})
        circuit_fuel = fuel_data.get(circuit_db_key, {})
        
        fuel_kg_per_lap = circuit_fuel.get('fuel_kg_per_lap', 1.8)
        fuel_effect_coef = circuit_fuel.get('fuel_effect_coefficient', 0.03)
        
        # 每圈燃油減少 = 車更輕 = 更快
        # 燃油效果 = -fuel_effect_coef * fuel_kg_consumed
        fuel_consumed_kg = fuel_kg_per_lap * (lap_number - 1)
        return -fuel_effect_coef * fuel_consumed_kg
        
    def _apply_self_correction(self):
        """Apply self-correction based on prediction errors."""
        if len(self._actual_lap_times) < 3:
            return
            
        # Calculate average error between actual and predicted
        errors = []
        for lap, actual in self._actual_lap_times.items():
            if lap in self._predicted_lap_times:
                predicted = self._predicted_lap_times[lap]
                errors.append(actual - predicted)
                
        if errors:
            avg_error = sum(errors) / len(errors)
            # Smooth correction factor update
            self._correction_factor = self._correction_factor * 0.7 + avg_error * 0.3
    
    def _simulate_realtime_corrections(self, full_lap_times: Dict[int, float], pit_laps: List[int]):
        """
        Simulate Realtime lap-by-lap correction process for Historical data.
        
        This ensures Historical replay produces the same prediction results
        as Realtime viewing by processing laps sequentially and applying
        corrections at each step.
        
        Args:
            full_lap_times: Complete {lap_number: lap_time_seconds} from history
            pit_laps: List of pit stop lap numbers
        """
        if not full_lap_times:
            return
        
        # Reset correction factor to start fresh
        self._correction_factor = 0.0
        
        # Get sorted lap numbers
        sorted_laps = sorted(full_lap_times.keys())
        
        # Laps to exclude from prediction (SC, PIT, etc.)
        excluded_laps = self._sc_laps | self._sc_restart_laps | set(pit_laps) | self._pit_out_laps
        
        # Temporary storage to simulate incremental data arrival
        simulated_lap_times: Dict[int, float] = {}
        
        logger.debug("[DRIVER_STRATEGY] Simulating Realtime corrections for %s laps...", len(sorted_laps))
        
        # Process each lap sequentially, simulating Realtime behavior
        for lap_num in sorted_laps:
            # Skip excluded laps (they don't contribute to prediction)
            if lap_num in excluded_laps:
                continue
            
            # Add this lap's data (simulating Realtime data arrival)
            simulated_lap_times[lap_num] = full_lap_times[lap_num]
            
            # Need at least 3 valid laps to start predictions
            if len(simulated_lap_times) < 3:
                continue
            
            # Calculate predictions with current data (simulating _calculate_all_predictions)
            self._calculate_predictions_with_data(simulated_lap_times, excluded_laps)
            
            # Apply self-correction (simulating _apply_self_correction)
            self._apply_correction_with_data(simulated_lap_times)
        
        # Final prediction calculation with full data and accumulated correction
        self._calculate_all_predictions()
        
        logger.debug("[DRIVER_STRATEGY] Simulation complete: correction_factor=%.4f", self._correction_factor)
    
    def _calculate_predictions_with_data(self, lap_times: Dict[int, float], excluded_laps: set):
        """
        Calculate predictions using specific lap time data with stint-based model.
        Used by _simulate_realtime_corrections to simulate incremental prediction.
        """
        if not lap_times or self._total_laps <= 0:
            return
        
        # 使用主要的 stint-based 計算方法
        # 臨時儲存實際圈速數據
        original_lap_times = self._actual_lap_times.copy()
        self._actual_lap_times = lap_times
        
        # 使用 stint-based 計算
        self._calculate_all_predictions()
        
        # 恢復原始數據
        self._actual_lap_times = original_lap_times
    
    def _apply_correction_with_data(self, lap_times: Dict[int, float]):
        """
        Apply self-correction using specific lap time data.
        Used by _simulate_realtime_corrections to simulate incremental correction.
        """
        if len(lap_times) < 3:
            return
        
        errors = []
        for lap, actual in lap_times.items():
            if lap in self._predicted_lap_times:
                predicted = self._predicted_lap_times[lap]
                errors.append(actual - predicted)
        
        if errors:
            avg_error = sum(errors) / len(errors)
            # Same smoothing as Realtime: 70% old + 30% new
            self._correction_factor = self._correction_factor * 0.7 + avg_error * 0.3
            
    # =========================================================================
    # Y-Axis Range Calculation
    # =========================================================================
    
    def _calculate_y_range(self):
        """Calculate Y-axis range based on valid data only.
        
        Excludes SC, SC restart, and PIT out laps from Y-axis calculation.
        """
        all_times = []
        
        # Laps to exclude from Y-axis calculation
        excluded_laps = self._sc_laps | self._sc_restart_laps | self._pit_out_laps
        
        # Collect only valid actual times (exclude SC/PIT out laps)
        for lap, time in self._actual_lap_times.items():
            if lap not in excluded_laps:
                all_times.append(time)
        
        # Collect all predicted times (already excludes SC/PIT)
        all_times.extend(self._predicted_lap_times.values())
        
        # Collect prediction range bounds
        for min_t, max_t in self._prediction_range.values():
            all_times.extend([min_t, max_t])
            
        if all_times:
            self._y_min = min(all_times) - 2.0
            self._y_max = max(all_times) + 2.0
        else:
            self._y_min = 80.0
            self._y_max = 100.0
            
    # =========================================================================
    # Context Menu
    # =========================================================================
    
    def contextMenuEvent(self, event):
        """Show context menu."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLOR_CHART_BG};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_GRID};
            }}
            QMenu::item:selected {{
                background-color: {COLOR_GRID};
            }}
        """)
        
        # Toggle correction
        correction_action = QAction(
            tr("Disable Correction") if self._correction_enabled else tr("Enable Correction"),
            self
        )
        correction_action.triggered.connect(self._toggle_correction)
        menu.addAction(correction_action)
        
        # Reset correction
        reset_action = QAction(tr("Reset Correction"), self)
        reset_action.triggered.connect(self._reset_correction)
        menu.addAction(reset_action)
        
        menu.addSeparator()
        
        # Driver selection submenu
        if self._available_drivers:
            driver_menu = menu.addMenu(tr("Select Driver"))
            
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
                team_color = info.get('team_color', 'FFFFFF')
                
                # 顯示格式: P1 VER (位置 + 車手代碼)
                display_text = f"P{position} {tla}" if position else tla
                action = driver_menu.addAction(display_text)
                action.setData(driver_num)
                
                # 標記當前選中
                if tla == self._driver_code:
                    action.setCheckable(True)
                    action.setChecked(True)
                
                action.triggered.connect(lambda checked, d=driver_num: self.driver_change_requested.emit(d))
        
        menu.exec_(event.globalPos())
    
    def set_available_drivers(self, drivers: Dict[str, Dict[str, Any]]):
        """Set available drivers for context menu selection."""
        self._available_drivers = drivers
        
    def _toggle_correction(self):
        """Toggle prediction correction on/off."""
        self._correction_enabled = not self._correction_enabled
        if not self._correction_enabled:
            self._correction_factor = 0.0
        self.update()
        
    def _reset_correction(self):
        """Reset correction factor to zero."""
        self._correction_factor = 0.0
        self._calculate_all_predictions()
        self.update()
        
    # =========================================================================
    # PyQt5 Native Drawing
    # =========================================================================
    
    def paintEvent(self, event):
        """Main paint event for custom drawing."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(COLOR_BACKGROUND))
        
        # Calculate chart area
        # Use margin_top to account for info bar space (similar to Speed Trace)
        chart_rect = QRectF(
            self._margin_left,
            self._margin_top,
            self.width() - self._margin_left - self._margin_right,
            self.height() - self._margin_top - self._margin_bottom
        )
        
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return
            
        # Draw chart background
        painter.fillRect(chart_rect, QColor(COLOR_CHART_BG))
        
        # Draw grid
        self._draw_grid(painter, chart_rect)
        
        # Draw fuel saving zones - 暫時隱藏
        # self._draw_fuel_saving_zones(painter, chart_rect)
        
        # Draw SC/VSC zones (higher priority than fuel saving)
        self._draw_sc_zones(painter, chart_rect)
        
        # Draw prediction range fill
        self._draw_prediction_range(painter, chart_rect)
        
        # Draw multi-compound prediction lines (S/M/H) - 在主預測線之前繪製
        self._draw_multi_compound_lines(painter, chart_rect)
        
        # Draw prediction line
        self._draw_prediction_line(painter, chart_rect)
        
        # Draw actual lap times
        self._draw_actual_lap_times(painter, chart_rect)
        
        # Draw pit markers
        self._draw_pit_markers(painter, chart_rect)
        
        # Draw predicted pit marker
        self._draw_predicted_pit_marker(painter, chart_rect)
        
        # Draw current lap indicator
        self._draw_current_lap_indicator(painter, chart_rect)
        
        # Draw axes
        self._draw_axes(painter, chart_rect)
        
        # Draw legend - 隱藏圖例
        # self._draw_legend(painter, chart_rect)
        
        painter.end()
        
    def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
        """Draw grid lines."""
        pen = QPen(QColor(COLOR_GRID))
        pen.setStyle(Qt.DotLine)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Horizontal grid lines (Y-axis)
        y_range = self._y_max - self._y_min
        if y_range <= 0:
            return
            
        # Calculate nice tick interval
        tick_interval = self._calculate_tick_interval(y_range)
        
        y_start = math.ceil(self._y_min / tick_interval) * tick_interval
        y = y_start
        while y <= self._y_max:
            py = self._value_to_y(y, chart_rect)
            painter.drawLine(
                QPointF(chart_rect.left(), py),
                QPointF(chart_rect.right(), py)
            )
            y += tick_interval
            
        # Vertical grid lines (X-axis / laps)
        if self._total_laps > 0:
            lap_interval = max(1, self._total_laps // 10)
            for lap in range(0, self._total_laps + 1, lap_interval):
                if lap == 0:
                    continue
                px = self._lap_to_x(lap, chart_rect)
                painter.drawLine(
                    QPointF(px, chart_rect.top()),
                    QPointF(px, chart_rect.bottom())
                )
    
    def _draw_fuel_saving_zones(self, painter: QPainter, chart_rect: QRectF):
        """Draw fuel saving zones as green fills.
        
        When a lap has tire saving score >= 15%, draw a green semi-transparent zone.
        SC zones have higher priority - don't draw fuel saving for SC laps.
        Lap 1, 2 are excluded.
        """
        if not hasattr(self, '_lap_tire_saving_scores') or not self._lap_tire_saving_scores:
            return
        if self._total_laps <= 0:
            return
        
        # Get SC laps set for exclusion
        sc_laps = self._sc_laps | self._sc_restart_laps
        
        color = QColor(COLOR_FUEL_SAVING)
        color.setAlpha(40)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        for lap, saving_score in self._lap_tire_saving_scores.items():
            # Skip lap 1, 2
            if lap <= 2:
                continue
            
            # Skip SC laps (SC has higher priority)
            if lap in sc_laps:
                continue
            
            # Only draw if saving score >= 15%
            if saving_score >= 15:
                x1 = self._lap_to_x(lap - 0.5, chart_rect)
                x2 = self._lap_to_x(lap + 0.5, chart_rect)
                painter.drawRect(QRectF(x1, chart_rect.top(), x2 - x1, chart_rect.height()))
                
    def _draw_sc_zones(self, painter: QPainter, chart_rect: QRectF):
        """Draw SC/VSC zones as yellow fills with SC label."""
        if not self._sc_zones or self._total_laps <= 0:
            return
            
        color = QColor(COLOR_SC_ZONE)
        color.setAlpha(50)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        for start_lap, end_lap in self._sc_zones:
            x1 = self._lap_to_x(start_lap - 0.5, chart_rect)
            x2 = self._lap_to_x(end_lap + 0.5, chart_rect)
            painter.drawRect(QRectF(x1, chart_rect.top(), x2 - x1, chart_rect.height()))
            
            # Draw "SC" label at top of zone (consistent with S1/S2/S3)
            painter.setFont(self._font_label)
            painter.setPen(QColor(COLOR_SC_ZONE))
            mid_x = (x1 + x2) / 2
            painter.drawText(QPointF(mid_x - 8, chart_rect.top() + 15), "SC")
            
    def _draw_prediction_range(self, painter: QPainter, chart_rect: QRectF):
        """Draw prediction range as semi-transparent fill."""
        if not self._prediction_range or self._total_laps <= 0:
            return
            
        color = QColor(COLOR_PREDICTION_FILL)
        color.setAlpha(30)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        # Build polygon for the range
        upper_points = []
        lower_points = []
        
        for lap in sorted(self._prediction_range.keys()):
            min_t, max_t = self._prediction_range[lap]
            x = self._lap_to_x(lap, chart_rect)
            upper_points.append(QPointF(x, self._value_to_y(max_t, chart_rect)))
            lower_points.append(QPointF(x, self._value_to_y(min_t, chart_rect)))
            
        if upper_points and lower_points:
            polygon = QPolygonF()
            for p in upper_points:
                polygon.append(p)
            for p in reversed(lower_points):
                polygon.append(p)
            painter.drawPolygon(polygon)
            
    def _draw_prediction_line(self, painter: QPainter, chart_rect: QRectF):
        """Draw predicted lap times as dashed red line."""
        if not self._predicted_lap_times or self._total_laps <= 0:
            return
            
        pen = QPen(QColor(COLOR_PREDICTED))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Create path
        path = QPainterPath()
        first = True
        
        for lap in sorted(self._predicted_lap_times.keys()):
            time = self._predicted_lap_times[lap]
            x = self._lap_to_x(lap, chart_rect)
            y = self._value_to_y(time, chart_rect)
            
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
                
        painter.drawPath(path)
        
    def _draw_multi_compound_lines(self, painter: QPainter, chart_rect: QRectF):
        """
        繪製三條配方預測線 (SOFT/MEDIUM/HARD)
        
        顏色方案:
        - SOFT: 紅色虛線 (#FF3333)
        - MEDIUM: 黃色虛線 (#FFCC00)
        - HARD: 白色虛線 (#FFFFFF)
        
        線條樣式: 半透明細虛線，避免干擾主要數據
        """
        if not self._show_multi_compound or self._total_laps <= 0:
            return
        
        # 配方顏色與線條樣式
        compound_styles = {
            'SOFT': {'color': COLOR_TYRE_SOFT, 'width': 2, 'alpha': 120},
            'MEDIUM': {'color': COLOR_TYRE_MEDIUM, 'width': 2, 'alpha': 120},
            'HARD': {'color': COLOR_TYRE_HARD, 'width': 2, 'alpha': 120}
        }
        
        painter.setBrush(Qt.NoBrush)
        
        for compound, predictions in self._multi_compound_predictions.items():
            if not predictions:
                continue
            
            style = compound_styles.get(compound, {})
            if not style:
                continue
            
            # 設置顏色與透明度
            color = QColor(style['color'])
            color.setAlpha(style['alpha'])
            pen = QPen(color)
            pen.setWidth(style['width'])
            pen.setStyle(Qt.DashDotLine)  # 使用點劃線區分
            painter.setPen(pen)
            
            # 繪製路徑
            path = QPainterPath()
            first = True
            
            for lap in sorted(predictions.keys()):
                time = predictions[lap]
                x = self._lap_to_x(lap, chart_rect)
                y = self._value_to_y(time, chart_rect)
                
                if first:
                    path.moveTo(x, y)
                    first = False
                else:
                    path.lineTo(x, y)
            
            painter.drawPath(path)
        
    def _draw_actual_lap_times(self, painter: QPainter, chart_rect: QRectF):
        """Draw actual lap times with tyre compound colors and small markers.
        
        Excludes SC, SC restart, and PIT out laps from display.
        """
        if not self._actual_lap_times or self._total_laps <= 0:
            return
        
        # Laps to exclude from display
        excluded_laps = self._sc_laps | self._sc_restart_laps | self._pit_out_laps
        
        # Collect points with compound info (excluding SC/PIT out laps)
        points = []  # (x, y, lap, diff, compound)
        
        for lap in sorted(self._actual_lap_times.keys()):
            # Skip excluded laps
            if lap in excluded_laps:
                continue
                
            actual_time = self._actual_lap_times[lap]
            x = self._lap_to_x(lap, chart_rect)
            y = self._value_to_y(actual_time, chart_rect)
            
            # Calculate diff with predicted
            diff = None
            if lap in self._predicted_lap_times:
                predicted_time = self._predicted_lap_times[lap]
                diff = actual_time - predicted_time
            
            # Get compound for this lap
            compound = self._lap_compounds.get(lap, self._current_compound)
            
            points.append((x, y, lap, diff, compound))
        
        # Draw line segments with tyre compound colors
        if len(points) >= 2:
            for i in range(len(points) - 1):
                x1, y1, lap1, _, compound1 = points[i]
                x2, y2, lap2, _, compound2 = points[i + 1]
                
                # Use the compound of the ending lap for segment color
                color = self._get_compound_color(compound2)
                pen = QPen(QColor(color))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        # Draw small circle markers with compound colors
        for x, y, lap, diff, compound in points:
            color = self._get_compound_color(compound)
            painter.setPen(QPen(QColor(color)))
            painter.setBrush(QBrush(QColor(color)))
            painter.drawEllipse(QPointF(x, y), 2.5, 2.5)  # Smaller circles
        
        # Draw diff label only for the CURRENT lap (latest actual lap)
        if points:
            # Get the last point (current lap)
            x, y, lap, diff, compound = points[-1]
            if diff is not None:
                painter.setFont(QFont("Arial", 9, QFont.Bold))
                # Format diff text
                sign = "+" if diff >= 0 else ""
                diff_text = f"{sign}{diff:.2f}s"
                
                # Color: red if slower than predicted, green if faster
                color = QColor('#FF6B6B') if diff >= 0 else QColor('#4ECDC4')
                painter.setPen(color)
                
                # Position label above the point
                label_y = y - 14 if y > chart_rect.top() + 25 else y + 18
                painter.drawText(QPointF(x - 18, label_y), diff_text)
    
    def _get_compound_color(self, compound: str) -> str:
        """Get color for tyre compound."""
        compound_upper = compound.upper() if compound else ''
        if 'SOFT' in compound_upper or compound_upper == 'S':
            return COLOR_TYRE_SOFT
        elif 'MEDIUM' in compound_upper or compound_upper == 'M':
            return COLOR_TYRE_MEDIUM
        elif 'HARD' in compound_upper or compound_upper == 'H':
            return COLOR_TYRE_HARD
        elif 'INTER' in compound_upper or compound_upper == 'I':
            return COLOR_TYRE_INTERMEDIATE
        elif 'WET' in compound_upper or compound_upper == 'W':
            return COLOR_TYRE_WET
        else:
            return COLOR_ACTUAL  # Default cyan
            
    def _draw_pit_markers(self, painter: QPainter, chart_rect: QRectF):
        """Draw pit stop markers as vertical lines with PIT label."""
        if not self._pit_laps or self._total_laps <= 0:
            return
            
        pen = QPen(QColor(COLOR_PIT_MARKER))
        pen.setWidth(2)
        pen.setStyle(Qt.DashDotLine)
        painter.setPen(pen)
        
        painter.setFont(self._font_axis)
        
        for lap in self._pit_laps:
            x = self._lap_to_x(lap, chart_rect)
            painter.drawLine(
                QPointF(x, chart_rect.top()),
                QPointF(x, chart_rect.bottom())
            )
            
            # Check if this pit was predicted (within ±1 lap tolerance)
            prediction_matched = any(
                abs(lap - pred) <= 1 
                for pred, actual in self._predicted_pit_laps if pred > 0
            )
            
            # Draw checkmark if prediction matched
            if prediction_matched:
                painter.save()
                painter.setPen(QPen(QColor('#00FF00')))  # Green checkmark
                painter.setFont(self._font_axis)
                painter.translate(x - 5, chart_rect.top() + 28)
                painter.rotate(-90)
                painter.drawText(0, 0, "✓")
                painter.restore()
            
            # Draw PIT label
            painter.save()
            painter.setPen(pen)  # Reset pen color
            painter.translate(x - 5, chart_rect.top() + 15)
            painter.rotate(-90)
            painter.drawText(0, 0, "PIT")
            painter.restore()
            
    def _draw_predicted_pit_marker(self, painter: QPainter, chart_rect: QRectF):
        """Draw all predicted pit stop markers (historical and current).
        
        Logic:
        1. If prediction accurate (actual within ±1 lap): Show checkmark on PIT line (handled in _draw_pit_markers)
        2. If pitted early (actual < predicted): Hide PIT? line
        3. If pitted late (actual > predicted): Keep PIT? line visible
        4. If not yet pitted (actual = 0): Show PIT? line
        """
        if self._total_laps <= 0:
            return
        
        painter.setFont(self._font_axis)
        
        # Draw predictions based on logic
        for predicted_lap, actual_pit in self._predicted_pit_laps:
            if predicted_lap <= 0:
                continue
            
            # Determine if we should show this prediction
            if actual_pit > 0:  # This stint has ended with a pit
                if abs(actual_pit - predicted_lap) <= 1:
                    # Accurate prediction - checkmark shown on PIT line, skip drawing PIT? here
                    continue
                elif actual_pit < predicted_lap:
                    # Pitted early - hide PIT? line
                    continue
                # else: pitted late - show PIT? line (fall through)
            # else: not yet pitted - show PIT? line (fall through)
            
            is_past = predicted_lap <= self._current_lap
            
            # 統一線條樣式與 S1/S2/S3 Comparison 一致
            # PIT 預測線: width=1, DashLine
            if is_past:
                pen = QPen(QColor('#CC7000'))  # Darker orange for past
            else:
                pen = QPen(QColor('#FF8C00'))  # Bright orange for future
            
            pen.setWidth(1)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            
            x = self._lap_to_x(predicted_lap, chart_rect)
            painter.drawLine(
                QPointF(x, chart_rect.top()),
                QPointF(x, chart_rect.bottom())
            )
            
            # Draw PIT label with translation
            # F87: 若有省胎調整則顯示 *
            pit_label = tr("PIT Est.")
            if self._tire_saving_adjustment > 0:
                pit_label += "*"
            
            painter.save()
            painter.translate(x + 8, chart_rect.top() + 15)
            painter.rotate(-90)
            painter.drawText(0, 0, pit_label)
            painter.restore()
            
    def _draw_current_lap_indicator(self, painter: QPainter, chart_rect: QRectF):
        """Draw current lap indicator as dotted cyan line."""
        if self._current_lap <= 0 or self._total_laps <= 0:
            return
            
        pen = QPen(QColor(COLOR_CURRENT_LAP))
        pen.setWidth(1)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        
        x = self._lap_to_x(self._current_lap, chart_rect)
        painter.drawLine(
            QPointF(x, chart_rect.top()),
            QPointF(x, chart_rect.bottom())
        )
        
    def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
        """Draw X and Y axes with labels."""
        pen = QPen(QColor(COLOR_AXIS))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setFont(self._font_axis)
        
        # Y-axis (left side)
        painter.drawLine(
            QPointF(chart_rect.left(), chart_rect.top()),
            QPointF(chart_rect.left(), chart_rect.bottom())
        )
        
        # Y-axis labels
        y_range = self._y_max - self._y_min
        if y_range > 0:
            tick_interval = self._calculate_tick_interval(y_range)
            y_start = math.ceil(self._y_min / tick_interval) * tick_interval
            y = y_start
            while y <= self._y_max:
                py = self._value_to_y(y, chart_rect)
                # Tick mark
                painter.drawLine(
                    QPointF(chart_rect.left() - 5, py),
                    QPointF(chart_rect.left(), py)
                )
                # Label
                label = f"{y:.1f}"
                fm = QFontMetrics(self._font_axis)
                text_width = fm.horizontalAdvance(label)
                painter.drawText(
                    int(chart_rect.left() - text_width - 8),
                    int(py + fm.height() / 4),
                    label
                )
                y += tick_interval
                
        # Y-axis title (rotated)
        painter.save()
        painter.setFont(self._font_label)
        painter.setPen(QPen(QColor(COLOR_TEXT)))
        title = tr("Lap Time (s)")
        fm = QFontMetrics(self._font_label)
        title_width = fm.horizontalAdvance(title)
        painter.translate(15, chart_rect.center().y() + title_width / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, title)
        painter.restore()
        
        # X-axis (bottom)
        painter.setPen(pen)
        painter.drawLine(
            QPointF(chart_rect.left(), chart_rect.bottom()),
            QPointF(chart_rect.right(), chart_rect.bottom())
        )
        
        # X-axis labels (laps)
        if self._total_laps > 0:
            lap_interval = max(1, self._total_laps // 10)
            for lap in range(0, self._total_laps + 1, lap_interval):
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
        title = tr("Lap")
        fm = QFontMetrics(self._font_label)
        title_width = fm.horizontalAdvance(title)
        painter.drawText(
            int(chart_rect.center().x() - title_width / 2),
            int(chart_rect.bottom() + 35),
            title
        )
        
    def _draw_legend(self, painter: QPainter, chart_rect: QRectF):
        """Draw legend at top right of chart with multi-compound lines."""
        painter.setFont(self._font_legend)
        
        # Legend items: 三條配方預測線
        legend_items = []
        
        if self._show_multi_compound:
            legend_items.extend([
                (COLOR_TYRE_SOFT, tr("Soft Strategy")),
                (COLOR_TYRE_MEDIUM, tr("Medium Strategy")),
                (COLOR_TYRE_HARD, tr("Hard Strategy")),
            ])
        
        if not legend_items:
            return
        
        x = chart_rect.right() - 150
        y = chart_rect.top() + 15
        
        for color, label in legend_items:
            # Color box with dash-dot pattern
            color_obj = QColor(color)
            color_obj.setAlpha(120)
            pen = QPen(color_obj)
            pen.setWidth(2)
            pen.setStyle(Qt.DashDotLine)
            painter.setPen(pen)
            painter.drawLine(int(x), int(y), int(x + 20), int(y))
            
            # Label
            painter.setPen(QPen(QColor(COLOR_TEXT)))
            painter.drawText(int(x + 25), int(y + 4), label)
            
            y += 18
            
    # =========================================================================
    # Coordinate Conversion Helpers
    # =========================================================================
    
    def _lap_to_x(self, lap: float, chart_rect: QRectF) -> float:
        """Convert lap number to X coordinate."""
        if self._total_laps <= 0:
            return chart_rect.left()
        return chart_rect.left() + (lap / self._total_laps) * chart_rect.width()
        
    def _value_to_y(self, value: float, chart_rect: QRectF) -> float:
        """Convert lap time value to Y coordinate (inverted)."""
        y_range = self._y_max - self._y_min
        if y_range <= 0:
            return chart_rect.center().y()
        ratio = (value - self._y_min) / y_range
        return chart_rect.bottom() - ratio * chart_rect.height()
        
    def _calculate_tick_interval(self, data_range: float) -> float:
        """Calculate nice tick interval for axis."""
        if data_range <= 0:
            return 1.0
        rough_tick = data_range / 5
        magnitude = math.pow(10, math.floor(math.log10(rough_tick)))
        residual = rough_tick / magnitude
        
        if residual > 5:
            return 10 * magnitude
        elif residual > 2:
            return 5 * magnitude
        elif residual > 1:
            return 2 * magnitude
        else:
            return magnitude


# =============================================================================
# LiveTimingDriverStrategy - MDI Integration
# =============================================================================
from ..core.base_live_mdi import BaseLiveTimingMDI


class LiveTimingDriverStrategy(BaseLiveTimingMDI):
    """
    MDI sub-window wrapper for Driver Strategy widget.
    Inherits from BaseLiveTimingMDI for proper signal handling.
    
    ARCHITECTURE: Tracks ALL 20 drivers simultaneously for instant switching.
    - _all_drivers_lap_data: Dict[str, DriverLapData] stores all driver data
    - Widget only displays the currently selected driver
    - Switching drivers loads from _all_drivers_lap_data (no reset)
    
    性能優化: 只在車手完成圈數時更新 (檢測 max lap 變化)
    """
    
    MODULE_ID = "live_timing_driver_strategy"
    DEFAULT_TITLE = "Driver Strategy"
    
    def __init__(self, parent=None, data_manager=None):
        self._current_driver: str = ""
        self._drivers_data: Dict[str, Any] = {}
        self._current_race_time: str = ""  # 當前 snapshot 的 race_time
        self._current_circuit: str = ""  # 當前賽道名稱 (用於 SF% 計算)
        
        # Multi-driver tracking: stores data for ALL drivers
        self._all_drivers_lap_data: Dict[str, DriverLapData] = {}
        
        # Global SC data (shared across all drivers)
        self._sc_laps: set = set()
        self._sc_zones: List[Tuple[int, int]] = []
        self._sc_restart_laps: set = set()
        
        # 性能優化: 追蹤上次的最大圈數
        self._last_max_lap: int = 0
        
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(self.DEFAULT_TITLE)
        self.resize(600, 400)
        
        # 連接 DataManager 車手選擇信號
        if self._data_manager:
            self._data_manager.driver_selected.connect(self._on_driver_selected)
        
        logger.info("[DRIVER_STRATEGY_MDI] LiveTimingDriverStrategy initialized (multi-driver tracking)")
        
    def _setup_ui(self):
        """Setup the UI layout."""
        # Create strategy widget and add to main_layout from BaseLiveTimingMDI
        self._strategy_widget = DriverStrategyWidget(self)
        self._main_layout.addWidget(self._strategy_widget)
        
        # 連接車手切換請求信號
        self._strategy_widget.driver_change_requested.connect(self._on_driver_change_requested)
    
    def _on_driver_change_requested(self, driver_num: str):
        """處理車手切換請求"""
        logger.info("[DRIVER_STRATEGY_MDI] Driver change requested: %s", driver_num)
        self.select_driver(driver_num)
        
    def _on_driver_selected(self, driver_num: str):
        """處理車手選擇信號"""
        logger.info("[DRIVER_STRATEGY_MDI] Driver selected from external: %s", driver_num)
        if hasattr(self, '_strategy_widget'):
            self.select_driver(driver_num)
    
    def _batch_update_all_drivers_tire_saving(self):
        """
        F87: 從 snapshot 批量更新所有車手的 SF%
        
        SF% 由 DataManager._update_tire_saving_scores() 計算並合併到 drivers 字典。
        此函數從 _drivers_data (最新 snapshot) 讀取 SF% 並同步到 driver_data。
        """
        if not hasattr(self, '_drivers_data') or not self._drivers_data:
            return
        
        for driver_num, driver_info in self._drivers_data.items():
            if driver_num not in self._all_drivers_lap_data:
                continue
            
            driver_data = self._all_drivers_lap_data[driver_num]
            
            # 從 snapshot 讀取 SF% (由 DataManager 計算)
            score = driver_info.get('tire_saving_score', 0.0)
            level = driver_info.get('tire_saving_level', 'NONE')
            
            # 更新 driver_data
            driver_data.tire_saving_score = score
            driver_data.tire_saving_level = level
            
            # 記錄到每圈歷史 (只有當分數 > 0 時)
            lap_num = driver_data.last_lap_recorded
            if score > 0 and lap_num > 0:
                driver_data.lap_tire_saving_scores[lap_num] = score
        
    def _get_or_create_driver_data(self, driver_num: str, driver_info: Dict[str, Any]) -> DriverLapData:
        """
        Get existing driver data or create new one.
        Efficient memory usage - only creates data structure when needed.
        """
        if driver_num not in self._all_drivers_lap_data:
            self._all_drivers_lap_data[driver_num] = DriverLapData(
                driver_num=driver_num,
                driver_tla=driver_info.get("driver_tla", driver_num),
                team_color=driver_info.get("team_color", "FFFFFF")
            )
        return self._all_drivers_lap_data[driver_num]
        
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """
        處理快照更新 - 更新 ALL 車手資料，不只當前車手。
        
        性能優化: 只在車手完成圈數時才更新
        """
        if not hasattr(self, '_strategy_widget'):
            return
            
        # 從快照提取資料
        drivers = snapshot.get('drivers', {})
        
        # 性能優化: 檢查是否有圈數變化
        current_max_lap = 0
        for driver_data in drivers.values():
            lap = driver_data.get('lap', 0)
            if lap and lap > current_max_lap:
                current_max_lap = lap
        
        # 如果圈數沒變且已經有數據，跳過更新
        if current_max_lap == self._last_max_lap and self._last_max_lap > 0:
            return
        
        self._last_max_lap = current_max_lap
        
        # 儲存當前 snapshot 的 race_time（用於查詢 track_status）
        self._current_race_time = snapshot.get('race_time', '')
        
        # 調試: 打印第一次收到的資料結構
        if drivers and not self._current_driver:
            sample_driver = next(iter(drivers.keys()))
            sample_data = drivers[sample_driver]
            logger.debug(
                "[DRIVER_STRATEGY_MDI] Sample driver data keys: %s",
                list(sample_data.keys()) if isinstance(sample_data, dict) else 'N/A',
            )
        
        # 儲存車手資料
        self._drivers_data = drivers
        
        # 傳遞車手列表給 widget（供右鍵選單使用）
        self._strategy_widget.set_available_drivers(drivers)
        
        # 設定總圈數
        total_laps = snapshot.get('total_laps', 0)
        if total_laps > 0:
            self._strategy_widget.set_total_laps(total_laps)
        
        # 自動選擇 P1 車手
        if not self._current_driver and drivers:
            self._auto_select_p1_driver(drivers)
        
        # ========== 關鍵變更: 更新 ALL 車手資料 ==========
        # 檢查 track status（全域，所有車手共用）
        is_sc_lap = False
        is_vsc_lap = False
        if self._data_manager and self._current_race_time:
            track_status = self._data_manager.get_track_status_at_time(self._current_race_time)
            is_sc_lap = (track_status == '4')
            is_vsc_lap = (track_status == '6')
        
        # 獲取輪胎狀態（一次性獲取，供所有車手使用）
        tyre_state = {}
        if self._data_manager:
            tyre_state = self._data_manager.get_tyre_state()
        
        # 更新所有車手的圈速資料
        for driver_num, driver_info in drivers.items():
            if not isinstance(driver_info, dict):
                continue
            # 獲取當前圈數以記錄 SC
            lap_num = driver_info.get("lap")
            if lap_num is not None:
                try:
                    lap_num = int(lap_num)
                    # 記錄 SC/VSC 圈到全域 (只需記錄一次)
                    if is_sc_lap or is_vsc_lap:
                        if lap_num not in self._sc_laps:
                            self._sc_laps.add(lap_num)
                            logger.debug("[DRIVER_STRATEGY_MDI] SC lap recorded: %s", lap_num)
                    # 檢查是否為 SC restart 圈 (前一圈是 SC)
                    elif (lap_num - 1) in self._sc_laps:
                        if lap_num not in self._sc_restart_laps:
                            self._sc_restart_laps.add(lap_num)
                            logger.debug("[DRIVER_STRATEGY_MDI] SC restart lap recorded: %s", lap_num)
                except (ValueError, TypeError):
                    pass
            self._update_single_driver_data(driver_num, driver_info, tyre_state, is_sc_lap, is_vsc_lap)
        
        # =====================================================================
        # F87: 批量計算所有車手的 SF% 並同步到 DataManager
        # 
        # 問題: _update_single_driver_data 只在「新圈速記錄」時計算 SF%
        #       歷史回放時，如果圈速已經載入過，SF% 就不會被計算
        # 解決: 在 snapshot 處理結束後，批量計算所有車手的 SF%
        # =====================================================================
        self._batch_update_all_drivers_tire_saving()
        
        # 只更新當前顯示車手的 Widget
        if self._current_driver and self._current_driver in self._all_drivers_lap_data:
            self._refresh_widget_from_driver_data(self._current_driver)
            
    def _update_single_driver_data(self, driver_num: str, driver_info: Dict[str, Any],
                                    tyre_state: Dict[str, Any], is_sc_lap: bool, is_vsc_lap: bool):
        """
        更新單一車手的資料到 _all_drivers_lap_data。
        這會處理所有 20 位車手，不只當前選中的。
        
        此方法在每次 snapshot 更新時調用，用於：
        1. 累積 throttle 樣本（每次 snapshot）
        2. 在圈數變化時計算 full_throttle_ratio 並記錄圈速
        """
        # 獲取或創建車手資料
        driver_data = self._get_or_create_driver_data(driver_num, driver_info)
        
        # 獲取當前圈數
        lap_num = driver_info.get("lap")
        if lap_num is None:
            return
            
        try:
            lap_num = int(lap_num)
        except (ValueError, TypeError):
            return
        
        # =====================================================================
        # F87: 累積 throttle 樣本（每次 snapshot 都執行）
        # =====================================================================
        throttle = driver_info.get("throttle", 0)
        if throttle is not None:
            try:
                throttle_val = int(throttle)
                # 檢查是否圈數變化
                if lap_num != driver_data.current_lap_being_tracked:
                    # 圈數變化：計算上一圈的 throttle ratio
                    if driver_data.current_lap_being_tracked > 0 and driver_data.current_lap_throttle_samples:
                        samples = driver_data.current_lap_throttle_samples
                        # Full throttle = throttle >= 95
                        full_throttle_count = sum(1 for s in samples if s >= 95)
                        ratio = full_throttle_count / len(samples) if samples else 0.0
                        driver_data.lap_throttle_ratios[driver_data.current_lap_being_tracked] = ratio
                        
                        # 只在當前車手時輸出調試信息
                        if driver_num == self._current_driver:
                            logger.debug(
                                "[DRIVER_STRATEGY_MDI] Lap %s throttle: %s samples, full_throttle_ratio=%.3f",
                                driver_data.current_lap_being_tracked,
                                len(samples),
                                ratio,
                            )
                    
                    # 重置為新圈
                    driver_data.current_lap_throttle_samples = [throttle_val]
                    driver_data.current_lap_being_tracked = lap_num
                else:
                    # 同一圈：累積樣本
                    driver_data.current_lap_throttle_samples.append(throttle_val)
            except (ValueError, TypeError):
                pass
        
        # =====================================================================
        # 原有邏輯：圈速記錄（只在圈數變化時）
        # =====================================================================
        # 檢查是否已記錄過這一圈
        if lap_num <= driver_data.last_lap_recorded:
            return
        
        # 獲取單圈時間
        lap_time_str = driver_info.get("last_lap_time", "")
        if not lap_time_str:
            return
        
        # 解析時間為秒數
        lap_time = self._parse_time_to_seconds(lap_time_str)
        if lap_time is None or lap_time <= 0:
            return
        
        # 獲取輪胎資訊
        compound = ""
        if driver_num in tyre_state:
            stints = tyre_state[driver_num].get('stints', [])
            if stints:
                compound = stints[-1].get('compound', '')
        driver_data.current_compound = compound
        
        # 獲取進站狀態
        is_pit = driver_info.get("in_pit", False) or driver_info.get("pit_out", False)
        
        # 記錄資料（排除 SC/VSC 圈）
        if not is_sc_lap and not is_vsc_lap:
            driver_data.actual_lap_times[lap_num] = lap_time
            if compound:
                driver_data.lap_compounds[lap_num] = compound
        
        # 記錄進站
        if is_pit:
            if lap_num not in driver_data.pit_laps:
                driver_data.pit_laps.append(lap_num)
            driver_data.pit_out_laps.add(lap_num + 1)
        
        # 更新最後記錄圈數
        driver_data.last_lap_recorded = lap_num
        
        # =====================================================================
        # F87: 從 snapshot 讀取省胎分數 (DataManager 計算)
        # DataManager._update_tire_saving_scores() 已計算並合併到 drivers 字典
        # =====================================================================
        score = driver_info.get('tire_saving_score', 0.0)
        level = driver_info.get('tire_saving_level', 'NONE')
        adjustment = 0.0  # DataManager 不計算 adjustment
        
        # 存儲當前圈分數 (只有當分數 > 0 時才記錄)
        driver_data.tire_saving_score = score
        driver_data.tire_saving_level = level
        driver_data.tire_saving_adjustment = adjustment
        if score > 0:
            driver_data.lap_tire_saving_scores[lap_num] = score
        
    def _refresh_widget_from_driver_data(self, driver_num: str):
        """
        從 _all_drivers_lap_data 刷新 Widget 顯示。
        這使得切換車手時可以立即顯示完整歷史資料。
        """
        if driver_num not in self._all_drivers_lap_data:
            return
            
        driver_data = self._all_drivers_lap_data[driver_num]
        
        # 批量載入所有圈速資料到 Widget（包含全域 SC 資料和 throttle 數據）
        self._strategy_widget.load_driver_history(
            actual_lap_times=driver_data.actual_lap_times.copy(),
            lap_compounds=driver_data.lap_compounds.copy(),
            pit_laps=driver_data.pit_laps.copy(),
            pit_out_laps=driver_data.pit_out_laps.copy(),
            sc_laps=self._sc_laps.copy(),
            sc_restart_laps=self._sc_restart_laps.copy(),
            current_compound=driver_data.current_compound,
            current_lap=driver_data.last_lap_recorded,
            # F87: 傳遞 throttle 數據和省胎分數 (SF% 由 DataManager 計算)
            lap_throttle_ratios=driver_data.lap_throttle_ratios.copy(),
            lap_tire_saving_scores=driver_data.lap_tire_saving_scores.copy()
        )
        
        # F87: 同步 SF% 到 Widget (從 driver_data 讀取，由 DataManager 計算)
        self._strategy_widget._tire_saving_score = driver_data.tire_saving_score
        self._strategy_widget._tire_saving_level = driver_data.tire_saving_level
        self._strategy_widget._tire_saving_adjustment = driver_data.tire_saving_adjustment
            
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """賽事載入完成"""
        logger.info("[DRIVER_STRATEGY_MDI] Race loaded: %s", race_info.get('name', 'Unknown'))
        
        # 設定賽道
        circuit = race_info.get('circuit', '')
        self._current_circuit = circuit  # 存儲賽道名稱供 SF% 計算使用
        if circuit and hasattr(self, '_strategy_widget'):
            self._strategy_widget.set_circuit(circuit)
            
        # 設定總圈數
        total_laps = race_info.get('total_laps', 0)
        if total_laps > 0 and hasattr(self, '_strategy_widget'):
            self._strategy_widget.set_total_laps(total_laps)
            
    def _on_race_unloaded(self):
        """賽事卸載 - 清除所有車手資料"""
        logger.info("[DRIVER_STRATEGY_MDI] Race unloaded - clearing all driver data")
        self._current_driver = ""
        self._drivers_data.clear()
        
        # 清除所有車手歷史資料
        self._all_drivers_lap_data.clear()
        self._sc_laps.clear()
        self._sc_zones.clear()
        self._sc_restart_laps.clear()
        
        if hasattr(self, '_strategy_widget'):
            self._strategy_widget._reset_driver_data()
        
    def get_strategy_widget(self) -> DriverStrategyWidget:
        """Get the strategy widget for external access."""
        return self._strategy_widget
        
    # =========================================================================
    # Driver Selection and Update
    # =========================================================================
    
    def _auto_select_p1_driver(self, drivers: Dict[str, Any]):
        """Auto-select the P1 driver."""
        p1_driver = None
        
        for driver_num, data in drivers.items():
            if isinstance(data, dict):
                position = data.get("position", 99)
                if position == 1:
                    p1_driver = driver_num
                    break
                
        if p1_driver:
            self.select_driver(p1_driver)
        elif drivers:
            # Fallback to first driver
            self.select_driver(list(drivers.keys())[0])
            
    def select_driver(self, driver_num: str):
        """
        Select a driver to display.
        
        ARCHITECTURE: Loads complete history from _all_drivers_lap_data.
        No data reset - instant switching with full history preserved.
        """
        if self._current_driver == driver_num:
            return  # Already selected, no action needed
            
        self._current_driver = driver_num
        
        driver_info = self._drivers_data.get(driver_num, {})
        if isinstance(driver_info, dict):
            # 獲取車手代碼 (TLA) - 欄位名稱是 driver_tla
            driver_code = driver_info.get("driver_tla", driver_num)
            driver_name = driver_info.get("name", driver_code)
            team_color = driver_info.get("team_color", "FFFFFF")
            
            logger.info(
                "[DRIVER_STRATEGY] select_driver: %s -> TLA=%s, color=%s",
                driver_num,
                driver_code,
                team_color,
            )
            
            # 設定車手基本資訊
            self._strategy_widget.select_driver(driver_code, driver_name, team_color)
            
            # 從 _all_drivers_lap_data 載入完整歷史資料
            if driver_num in self._all_drivers_lap_data:
                self._refresh_widget_from_driver_data(driver_num)
            else:
                # 首次選擇此車手，確保創建資料結構
                self._get_or_create_driver_data(driver_num, driver_info)
    
    def _parse_time_to_seconds(self, time_str: str) -> Optional[float]:
        """將時間字串解析為秒數 (參照 lap_history)"""
        if not time_str:
            return None
        
        try:
            # 格式: "1:23.456" 或 "23.456"
            if ':' in str(time_str):
                parts = str(time_str).split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except (ValueError, IndexError):
            return None
            
    def get_current_driver(self) -> str:
        """Get the currently selected driver number."""
        return self._current_driver
        
    def get_available_drivers(self) -> List[str]:
        """Get list of available driver numbers."""
        return list(self._drivers_data.keys())
