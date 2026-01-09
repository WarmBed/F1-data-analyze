#!/usr/bin/env python3
"""
Full Race Simulator for 20-Driver Competition

Simulates a complete F1 race with:
1. All 20 drivers with individual strategies
2. Position changes lap-by-lap
3. SC/VSC events affecting the entire field
4. Pit stop overlapping and track position effects

Integrates with:
- FP2->Q predictions for driver rankings
- Long Run data for degradation estimates
- Monte Carlo for SC probability

Author: F1T Team
Date: 2025-01-07
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from pathlib import Path
import random
import copy
import json

from strategy_simulator.core.lap_simulator import (
    SimulationParams, Stint, Compound, LapSimulator
)
from strategy_simulator.core.blocking_analyzer import DriverPaceInfo
from strategy_simulator.core.position_tracker import (
    PositionTracker, SimulationResult as PTSimulationResult,
    create_position_tracker
)
from strategy_simulator.core.overtake_calculator import OvertakeAttempt


@dataclass
class DriverRaceState:
    """State of a driver during race simulation."""
    driver_code: str
    team: str
    
    # Current position (race classification)
    position: int = 1
    grid_position: int = 1
    
    # Track position system
    # track_position = cumulative distance traveled (in seconds equivalent)
    # Higher = further ahead on track
    track_position: float = 0.0
    
    # Timing
    total_time: float = 0.0
    gap_to_leader: float = 0.0
    gap_to_ahead: float = 0.0
    
    # Strategy
    current_stint: int = 0
    stints: List[Stint] = field(default_factory=list)
    current_tire: Compound = Compound.MEDIUM
    tire_age: int = 0
    
    # Pace parameters
    base_pace: float = 90.0  # Base lap time
    degradation_per_lap: float = 0.05  # Per-lap deg
    
    # Pit stops
    pit_stops_made: int = 0
    in_pit: bool = False
    laps_since_pit: int = 0  # Track fresh tire advantage
    
    # Status
    retired: bool = False
    dnf_reason: str = ""
    
    def get_current_pace(
        self, 
        params: SimulationParams, 
        sc_active: bool = False,
        track_evolution_rate: float = 0.015,
        fuel_effect_coef: Optional[float] = None,
        current_lap: int = 0
    ) -> float:
        """
        Calculate current lap time based on tire state and conditions.
        
        Args:
            params: Simulation parameters
            sc_active: Whether SC is active (slower pace)
            track_evolution_rate: Long Run 的賽道進化率 (秒/圈)，預設 0.015
            fuel_effect_coef: Long Run 的燃油效應係數，預設使用 params 的值
            current_lap: 當前圈數 (用於更準確計算燃油和賽道進化)
            
        Returns:
            Expected lap time in seconds
        """
        if sc_active:
            # SC lap time is approximately base lap time + 30 seconds
            return params.base_lap_time + 30.0
        
        if self.retired:
            return float('inf')
        
        # Base pace + tire degradation
        tire_deg = self.tire_age * self.degradation_per_lap
        
        # ✅ 燃油效應 (使用 Long Run 參數或預設值)
        # laps_completed 改用 current_lap (更準確)
        laps_completed = current_lap if current_lap > 0 else self.tire_age
        
        # 使用 Long Run 燃油係數（如果提供）
        fuel_coef = fuel_effect_coef if fuel_effect_coef else params.fuel_effect_coefficient
        
        # 燃油越輕，圈速越快（正值 = 更慢）
        # 公式：剩餘燃油比例 × 燃油係數 × 總圈數 × 每圈燃油重量效應
        fuel_load_remaining = max(0, (params.race_laps - laps_completed) / params.race_laps)
        fuel_weight_effect = fuel_load_remaining * fuel_coef * params.race_laps * 0.05
        
        # ✅ 賽道進化 (使用 Long Run 參數)
        # 比賽越久，橡膠越多，賽道越快
        # 負值 = 更快
        track_evolution = -laps_completed * track_evolution_rate
        
        # ✅ 微小圈間隨機波動（僅模擬車手執行差異）
        # 範圍：±0.05s
        # 原因：模擬微小的車手失誤、彎角執行差異、風速影響等
        # 真實 F1 即使在穩定情況下也有小幅波動
        lap_to_lap_variation = random.uniform(-0.05, 0.05)
        
        return self.base_pace + tire_deg + fuel_weight_effect + track_evolution + lap_to_lap_variation


@dataclass
class LapState:
    """State of all drivers at a specific lap."""
    lap: int
    positions: Dict[str, int]  # driver -> position
    gaps: Dict[str, float]  # driver -> gap to leader
    tire_ages: Dict[str, int]  # driver -> tire age
    compounds: Dict[str, str]  # driver -> compound
    pit_stops: List[str]  # drivers who pitted this lap
    sc_active: bool = False


@dataclass
class RaceResult:
    """Final race result for a driver."""
    driver_code: str
    team: str
    final_position: int
    grid_position: int
    positions_gained: int
    total_time: float
    gap_to_winner: float
    pit_stops: int
    strategy_notation: str
    retired: bool = False
    dnf_reason: str = ""


@dataclass
class FullRaceSimulation:
    """Complete race simulation result."""
    race_laps: int
    total_drivers: int
    
    # Lap-by-lap data
    lap_states: List[LapState] = field(default_factory=list)
    
    # Final results
    final_standings: List[RaceResult] = field(default_factory=list)
    
    # SC events that occurred
    sc_events: List[Dict] = field(default_factory=list)
    
    # Statistics
    total_pit_stops: int = 0
    total_overtakes: int = 0
    
    # Overtake attempts (from PositionTracker)
    overtake_attempts: List[OvertakeAttempt] = field(default_factory=list)
    
    # Our driver's analysis
    our_driver: str = ""
    our_result: Optional[RaceResult] = None
    
    # Traffic analysis data
    traffic_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_position_history(self, driver_code: str) -> List[int]:
        """Get position history for a driver across all laps."""
        return [
            lap_state.positions.get(driver_code, 20)
            for lap_state in self.lap_states
        ]
    
    def get_gap_history(self, driver_code: str) -> List[float]:
        """Get gap-to-leader history for a driver."""
        return [
            lap_state.gaps.get(driver_code, 999.0)
            for lap_state in self.lap_states
        ]


class FullRaceSimulator:
    """
    Simulates a complete F1 race with all 20 drivers.
    
    Uses:
    - FP2->Q predictions for driver pace rankings
    - Long Run data for degradation estimates
    - Opponent strategies from OpponentStrategyPanel
    - SC/VSC probability from Monte Carlo parameters
    
    Example:
        simulator = FullRaceSimulator(sim_params)
        simulator.load_drivers(fp2_predictions, long_run_data)
        simulator.set_opponent_strategies(opponent_settings)
        simulator.set_our_strategy("VER", strategy_stints)
        result = simulator.simulate_race()
    """
    
    def __init__(
        self,
        sim_params: SimulationParams,
        sc_probability: float = 0.5,  # Probability of at least one SC
        vsc_probability: float = 0.3,  # Probability of VSC instead of SC
        overtaking_difficulty: float = 0.5,  # 0 = easy, 1 = hard
        simple_mode: bool = False,  # NEW: Simple mode (no position tracking)
        track_name: str = "",  # Track name for PositionTracker
        year: int = 2025,  # Year for team performance data
    ):
        """
        Initialize race simulator.
        
        Args:
            sim_params: Simulation parameters (race laps, pit loss, etc.)
            sc_probability: Probability of SC per race
            vsc_probability: Probability of VSC (given an incident)
            overtaking_difficulty: Track-specific overtaking difficulty
            simple_mode: If True, use simplified lap-time simulation without position tracking
            track_name: Track name (required for Complete mode with PositionTracker)
            year: Year for team performance data
        """
        self.sim_params = sim_params
        self.sc_probability = sc_probability
        self.vsc_probability = vsc_probability
        self.overtaking_difficulty = overtaking_difficulty
        self.simple_mode = simple_mode  # NEW
        self.track_name = track_name
        self.year = year
        
        # 載入賽道專屬係數
        self._track_coefficients = self._load_track_coefficients()
        self._track_pace_coefficient = self._get_track_coefficient(track_name)
        
        # Long Run 數據參數 (會在 load_drivers 時更新)
        self._long_run_base_lap_time: Optional[float] = None
        self._long_run_fuel_effect: float = 0.030  # 預設值
        self._long_run_fuel_kg_per_lap: float = 1.70  # 預設值
        self._long_run_track_evolution: float = 0.015  # 預設值 (秒/圈)
        self._long_run_degradation: Dict[str, float] = {}  # 各胎質衰退率
        
        # Driver states
        self._drivers: Dict[str, DriverRaceState] = {}
        self._our_driver: Optional[str] = None
        
        # Pre-calculated strategies per driver
        self._strategies: Dict[str, List[Stint]] = {}
        
        # Default pit window
        self._default_pit_windows = {
            1: [(15, 25)],  # 1-stop: pit around lap 20
            2: [(12, 18), (30, 38)],  # 2-stop windows
        }
    
    def _load_track_coefficients(self) -> Dict:
        """
        載入賽道專屬 race_pace_delta 係數。
        
        基於 2023-2025 真實數據分析，各賽道差距特性不同：
        - 街道賽道 (Singapore, Monaco): 超車困難，差距小
        - 高速賽道 (Australia, Mexico): 差距大
        - 標準賽道 (Japan, Italy): 中等差距
        
        Returns:
            Dict with track coefficients
        """
        try:
            json_path = Path(__file__).parent.parent.parent / "json" / "track_gap_coefficients.json"
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[RACE_SIM] 無法載入賽道係數: {e}")
        
        # 預設係數（如果 JSON 不存在）
        return {
            "default_coefficient": 0.20,
            "track_coefficients": {}
        }
    
    def _get_track_coefficient(self, track_name: str) -> float:
        """
        根據賽道名稱取得專屬 race_pace_delta 係數。
        
        Args:
            track_name: 賽道名稱 (e.g., "Japan", "Singapore")
            
        Returns:
            賽道專屬係數 (每圈每位置的差距秒數)
        """
        default_coef = self._track_coefficients.get("default_coefficient", 0.20)
        
        if not track_name:
            print(f"[RACE_SIM] 未指定賽道，使用預設係數: {default_coef}")
            return default_coef
        
        # 標準化賽道名稱
        normalized = track_name.lower().replace(" ", "_")
        
        track_coefs = self._track_coefficients.get("track_coefficients", {})
        
        # 嘗試精確匹配
        if normalized in track_coefs:
            coef = track_coefs[normalized]["coefficient"]
            print(f"[RACE_SIM] 賽道 {track_name}: 使用專屬係數 {coef:.3f}")
            return coef
        
        # 嘗試部分匹配
        for track_key, track_data in track_coefs.items():
            if track_key in normalized or normalized in track_key:
                coef = track_data["coefficient"]
                print(f"[RACE_SIM] 賽道 {track_name} 匹配 {track_key}: 使用係數 {coef:.3f}")
                return coef
        
        print(f"[RACE_SIM] 賽道 {track_name} 無專屬係數，使用預設: {default_coef}")
        return default_coef
        
    def load_drivers(
        self,
        fp2_predictions: List[Dict],
        long_run_data: Optional[Dict] = None
    ):
        """
        Load all drivers from FP2->Q prediction.
        
        Args:
            fp2_predictions: List of driver predictions from FP2
            long_run_data: Optional Long Run data for better pace estimates
                           Structure: LongRunData.to_dict() format with:
                           - base_lap_time: 基準圈時間
                           - fuel_effect: 燃油效應係數 (秒/公斤)
                           - fuel_kg_per_lap: 每圈燃油消耗 (公斤)
                           - track_evolution_per_lap: 賽道進化 (秒/圈)
                           - degradation: Dict[compound, DegradationData]
                           - driver_results: Dict[driver, List[result]]
        """
        self._drivers.clear()
        
        # ✅ 先從 Long Run 數據提取全局參數
        if long_run_data:
            # 基準圈時間 (如果有計算過)
            if long_run_data.get('base_lap_time'):
                self._long_run_base_lap_time = long_run_data['base_lap_time']
                print(f"[RACE_SIM] 使用 Long Run 基準圈時間: {self._long_run_base_lap_time:.3f}s")
            
            # 燃油效應係數
            if long_run_data.get('fuel_effect'):
                self._long_run_fuel_effect = long_run_data['fuel_effect']
                print(f"[RACE_SIM] 使用 Long Run 燃油效應: {self._long_run_fuel_effect:.4f}s/kg")
            
            # 每圈燃油消耗
            if long_run_data.get('fuel_kg_per_lap'):
                self._long_run_fuel_kg_per_lap = long_run_data['fuel_kg_per_lap']
                print(f"[RACE_SIM] 使用 Long Run 燃油消耗: {self._long_run_fuel_kg_per_lap:.2f}kg/lap")
            
            # 賽道進化
            if long_run_data.get('track_evolution_per_lap'):
                # Long Run 提供的是總變化量，轉為每圈進化率 (通常是負值=更快)
                self._long_run_track_evolution = abs(long_run_data['track_evolution_per_lap'])
                print(f"[RACE_SIM] 使用 Long Run 賽道進化: {self._long_run_track_evolution:.4f}s/lap")
            
            # 各胎質平均衰退率
            degradation = long_run_data.get('degradation', {})
            for compound_name, deg_data in degradation.items():
                if isinstance(deg_data, dict):
                    self._long_run_degradation[compound_name.upper()] = deg_data.get('deg_per_lap', 0.05)
                else:
                    self._long_run_degradation[compound_name.upper()] = 0.05
            if self._long_run_degradation:
                print(f"[RACE_SIM] 使用 Long Run 衰退率: {self._long_run_degradation}")
        
        for pred in fp2_predictions:
            driver_code = pred.get('driver', '')
            if not driver_code:
                continue
            
            position = pred.get('rank', 20)
            predicted_q_time = pred.get('predicted_time', 90.0)
            
            # ✅ 方法 1: 優先使用該車手的 Long Run 個別 base_lap_time
            driver_base_from_longrun = None
            driver_deg_from_longrun = 0.05  # 預設值
            
            if long_run_data:
                driver_lr = long_run_data.get('driver_results', {}).get(driver_code, [])
                if driver_lr and len(driver_lr) > 0:
                    first_stint = driver_lr[0]
                    
                    # 從 fuel_corrected_times[0] 取得該車手的 base_lap_time
                    fuel_corrected_times = first_stint.get('fuel_corrected_times', [])
                    if fuel_corrected_times and len(fuel_corrected_times) > 0:
                        driver_base_from_longrun = fuel_corrected_times[0]
                        print(f"[RACE_SIM] {driver_code}: 使用 Long Run 個別 base_lap_time={driver_base_from_longrun:.3f}s")
                    
                    # 取得該車手的真實衰退率
                    driver_deg_from_longrun = first_stint.get('deg_per_lap', first_stint.get('degradation', 0.05))
            
            # ✅ 確定 base_pace
            if driver_base_from_longrun:
                # 最佳方案：使用該車手的 Long Run base_lap_time
                base_pace = driver_base_from_longrun
            elif self._long_run_base_lap_time:
                # 備案 1：使用全局 Long Run base + Q 差距
                best_q_time = min(p.get('predicted_time', 999) for p in fp2_predictions)
                gap_to_best = predicted_q_time - best_q_time
                base_pace = self._long_run_base_lap_time + gap_to_best
                print(f"[RACE_SIM] {driver_code}: base_pace={base_pace:.3f}s (全局 Long Run base + Q gap {gap_to_best:.3f}s)")
            else:
                # 備案 2：Q 圈時間轉正賽配速
                race_pace_delta = 2.0  # 固定 +2.0s（Q→Race 的典型差距）
                base_pace = predicted_q_time + race_pace_delta
                print(f"[RACE_SIM] {driver_code}: base_pace={base_pace:.3f}s (Q time + {race_pace_delta}s)")
            
            # ❌ 移除個體差異（改為使用 Long Run 真實數據）
            # 原因：每次蒙地卡羅模擬應該使用相同的基礎參數，隨機性應只來自賽事過程
            # individual_variation = random.uniform(-0.3, 0.3)
            # base_pace += individual_variation
            
            # ✅ Degradation: 使用該車手的 Long Run 數據
            deg_per_lap = driver_deg_from_longrun
            
            # ❌ 移除輪胎衰退差異（改為使用 Long Run 真實數據）
            # 原因：Long Run 已經包含該車手的真實衰退率，不應再加隨機變異
            # deg_per_lap += random.uniform(-0.02, 0.04)
            
            state = DriverRaceState(
                driver_code=driver_code,
                team=pred.get('team', ''),
                position=position,
                grid_position=position,
                base_pace=base_pace,
                degradation_per_lap=abs(deg_per_lap),
                current_tire=Compound.MEDIUM,  # Default start tire
            )
            
            self._drivers[driver_code] = state
        
        print(f"[RACE_SIM] Loaded {len(self._drivers)} drivers")
        
    def set_opponent_strategies(self, opponent_settings: Dict[str, Dict]):
        """
        Set opponent strategies from OpponentStrategyPanel.
        
        Args:
            opponent_settings: Dict mapping driver_code to strategy settings
        """
        for driver_code, settings in opponent_settings.items():
            if driver_code not in self._drivers:
                continue
            
            # Parse tire sequence
            tire_sequence = settings.get('tire_sequence', ['M', 'H'])
            
            # Convert to Stints (pass driver_code for varied pit timing)
            stints = self._create_stints_from_sequence(tire_sequence, driver_code)
            self._strategies[driver_code] = stints
            
            # Set initial tire
            if stints:
                self._drivers[driver_code].stints = stints
                self._drivers[driver_code].current_tire = stints[0].compound
                
                # Log pit lap for this driver
                if len(stints) > 1:
                    pit_lap = stints[0].start_lap + stints[0].laps
                    print(f"[RACE_SIM] {driver_code} strategy: {'-'.join(tire_sequence)}, "
                          f"pit L{pit_lap}")
                
    def _create_stints_from_sequence(
        self, 
        tire_sequence: List[str],
        driver_code: str = ""
    ) -> List[Stint]:
        """
        Convert tire sequence to Stint objects with varied lap splits.
        
        Key improvement: Add position-based and random offset to pit laps
        so not all drivers pit on the same lap.
        
        Args:
            tire_sequence: List of tire compound letters ['M', 'H']
            driver_code: Driver code for position-based offset
            
        Returns:
            List of Stint objects with varied pit windows
        """
        stints = []
        total_laps = self.sim_params.race_laps
        laps_per_stint = total_laps // len(tire_sequence)
        
        # Calculate offset based on driver (spread pit stops across field)
        # Use driver code hash for deterministic but varied offset
        if driver_code:
            driver_hash = sum(ord(c) for c in driver_code)
            position_offset = (driver_hash % 7) - 3  # -3 to +3 laps offset
        else:
            position_offset = random.randint(-3, 3)
        
        current_lap = 1
        for i, tire in enumerate(tire_sequence):
            compound = {
                'S': Compound.SOFT,
                'M': Compound.MEDIUM,
                'H': Compound.HARD,
            }.get(tire.upper(), Compound.MEDIUM)
            
            # Last stint gets remaining laps
            if i == len(tire_sequence) - 1:
                stint_laps = total_laps - current_lap + 1
            else:
                # Add offset to spread out pit stops (except last stint)
                stint_laps = laps_per_stint + position_offset
                stint_laps = max(8, stint_laps)  # Minimum 8 laps per stint
            
            stints.append(Stint(
                compound=compound,
                laps=stint_laps,
                start_lap=current_lap
            ))
            current_lap += stint_laps
            
        return stints
    
    def set_our_strategy(self, driver_code: str, stints: List[Stint]):
        """
        Set our driver and strategy.
        
        Args:
            driver_code: Our driver code
            stints: Our strategy (list of Stints)
        """
        self._our_driver = driver_code
        
        if driver_code in self._drivers:
            self._drivers[driver_code].stints = stints
            if stints:
                self._drivers[driver_code].current_tire = stints[0].compound
        else:
            # Create driver if not exists
            state = DriverRaceState(
                driver_code=driver_code,
                team="",
                position=10,  # Default mid-grid
                grid_position=10,
                stints=stints,
            )
            if stints:
                state.current_tire = stints[0].compound
            self._drivers[driver_code] = state
            
        self._strategies[driver_code] = stints
    
    def inject_sc_events(self, events: List[Tuple[int, int, bool]]):
        """
        Inject predetermined SC events (for Monte Carlo).
        
        Args:
            events: List of (start_lap, duration, is_vsc) tuples
        """
        self._injected_sc_events = events
    
    def _simulate_with_position_tracker(self, seed: Optional[int] = None) -> FullRaceSimulation:
        """
        Simulate race using PositionTracker for detailed position tracking.
        
        This provides accurate lap-by-lap position changes with realistic
        overtaking based on F138 trained model.
        
        Args:
            seed: Random seed for reproducibility
            
        Returns:
            FullRaceSimulation with complete results including overtake_attempts
        """
        import sys
        sys.stdout.write("\n" + "="*70 + "\n")
        sys.stdout.write("[RACE_SIM] \u26a1 COMPLETE MODE \u5df2\u555f\u52d5 - \u4f7f\u7528 PositionTracker\n")
        sys.stdout.write(f"[RACE_SIM] \u8a2d\u5b9a\u5708\u6578: {self.sim_params.race_laps}\n")
        sys.stdout.write(f"[RACE_SIM] \u8eca\u624b\u6578\u91cf: {len(self._drivers)}\n")
        sys.stdout.write("="*70 + "\n\n")
        sys.stdout.flush()
        
        if seed is not None:
            # ✅ 確保每次執行都有不同結果
            random.seed(seed)
        else:
            # 使用時間戳確保隨機性
            import time
            random.seed(int(time.time() * 1000) % (2**32))
            
        print(f"[RACE_SIM] Using PositionTracker for Complete mode simulation")
        print(f"[RACE_SIM] Track: {self.track_name}, Laps: {self.sim_params.race_laps}")
        
        # Create PositionTracker
        try:
            tracker = create_position_tracker(
                track_name=self.track_name,
                time_step=1.0,
                total_laps=self.sim_params.race_laps,
                year=self.year,
                race=self.track_name  # 使用 track_name 作為 race 參數
            )
        except Exception as e:
            print(f"[RACE_SIM] Failed to create PositionTracker: {e}")
            print(f"[RACE_SIM] Falling back to simple mode")
            return self._simulate_simple_mode(seed)
        
        # Build grid from our drivers
        grid = []
        sorted_drivers = sorted(
            self._drivers.values(),
            key=lambda d: d.grid_position
        )
        for driver in sorted_drivers:
            # Get starting tire from strategy
            stints = self._strategies.get(driver.driver_code, [])
            start_tire = stints[0].compound.value[0] if stints else "M"
            grid.append({
                "driver": driver.driver_code,
                "team": driver.team,
                "tyre": start_tire
            })
        
        # Initialize grid
        tracker.initialize_grid(grid)
        
        # Generate or use injected SC events
        if hasattr(self, '_injected_sc_events') and self._injected_sc_events:
            sc_events = self._injected_sc_events
            self._injected_sc_events = None
        else:
            sc_events = self._generate_sc_events()
        
        # Build SC lap set
        sc_laps = {}
        for start, duration, is_vsc in sc_events:
            for lap in range(start, start + duration):
                if lap <= self.sim_params.race_laps:
                    sc_laps[lap] = is_vsc
        
        # Run simulation with SC/VSC events
        # Note: PositionTracker runs its own loop, we need to inject SC at right times
        previous_lap = 0
        # ✅ 提升 max_steps 上限以確保所有車手完成比賽
        # 200 * 60 = 每圈最多 12000 步（足夠處理慢車和被套圈情況）
        max_steps = int(self.sim_params.race_laps * 200 * 60 / tracker.time_step)
        steps = 0
        last_progress = 0
        race_finished = False  # ✅ 標記領先者是否完成
        finish_time = 0  # ✅ 領先者完成時間
        
        print(f"[POSITION_TRACKER] 開始模擬：總步數上限 = {max_steps:,}")
        print(f"[POSITION_TRACKER] 第一個 while 迴圈即將開始...")
        
        while steps < max_steps:
            # Check if lap changed and update SC status
            current_lap = tracker.current_lap
            if current_lap != previous_lap:
                previous_lap = current_lap
                # 每圈顯示進度
                progress = int((current_lap / self.sim_params.race_laps) * 100)
                if progress > last_progress:
                    print(f"[POSITION_TRACKER] 進度：L{current_lap}/{self.sim_params.race_laps} ({progress}%)", flush=True)
                    last_progress = progress
                
                if current_lap in sc_laps:
                    if sc_laps[current_lap]:
                        tracker.set_virtual_safety_car(True)
                    else:
                        tracker.set_safety_car(True)
                else:
                    # Check if SC should end
                    if tracker.sc_active or tracker.vsc_active:
                        tracker.set_safety_car(False)
                        tracker.set_virtual_safety_car(False)
            
            tracker.simulate_step()
            steps += 1
            
            # Check if race complete (領先者完成 race_laps 圈即結束)
            leader = min(tracker.car_states, key=lambda c: c.position)
            if leader.lap_number >= self.sim_params.race_laps and not race_finished:
                import sys
                race_finished = True
                finish_time = tracker.current_time_s
                sys.stdout.write("\n" + "="*70 + "\n")
                sys.stdout.write(f"[RACE_END] 領先者 {leader.driver} 完成 {leader.lap_number} 圈\n")
                sys.stdout.write(f"[RACE_END] 設定圈數: {self.sim_params.race_laps}\n")
                sys.stdout.write(f"[RACE_END] position_history 記錄數: {len(tracker.position_history)}\n")
                sys.stdout.write(f"[RACE_END] 總步數: {steps:,}\n")
                
                # 檢查所有車手的圈時記錄
                for driver_code in list(tracker.lap_times.keys())[:5]:  # 只顯示前5個
                    lap_count = len(tracker.lap_times[driver_code])
                    total_time = sum(tracker.lap_times[driver_code]) if tracker.lap_times[driver_code] else 0
                    sys.stdout.write(f"[RACE_END] {driver_code}: {lap_count} 圈, 總時間 {total_time:.1f}s\n")
                
                sys.stdout.write("="*70 + "\n")
                sys.stdout.flush()
            
            # 如果比賽已結束，等待其他車手完成（最多 300 秒額外時間）
            if race_finished:
                time_since_finish = tracker.current_time_s - finish_time
                if time_since_finish > 300:
                    print(f"[RACE] 超時結束: 額外時間 {time_since_finish:.1f}s")
                    break
                # 檢查所有車手是否完成
                all_finished = all(car.lap_number >= self.sim_params.race_laps for car in tracker.car_states)
                if all_finished:
                    print(f"[RACE] 所有車手完成 {self.sim_params.race_laps} 圈")
                    break
        
        # Generate final result
        final_positions = [car.driver for car in sorted(tracker.car_states, key=lambda c: c.position)]
        
        # 記錄每位車手的最終狀態
        final_car_states = {}
        for car in tracker.car_states:
            final_car_states[car.driver] = {
                "position_m": car.position_m,
                "lap_number": car.lap_number,
                "position": car.position,
                "tyre_compound": car.tyre_compound,
                "tyre_age_laps": car.tyre_age_laps
            }
        
        pt_result = PTSimulationResult(
            total_laps=self.sim_params.race_laps,
            total_time_s=tracker.current_time_s,
            final_positions=final_positions,
            overtake_attempts=tracker.overtake_attempts,
            position_history=tracker.position_history,
            lap_times=tracker.lap_times,
            final_car_states=final_car_states
        )
        
        # Convert to FullRaceSimulation
        return self._convert_from_position_tracker(pt_result, sc_events)
    
    def _convert_from_position_tracker(
        self,
        pt_result: PTSimulationResult,
        sc_events: List[Tuple[int, int, bool]]
    ) -> FullRaceSimulation:
        """
        Convert PositionTracker result to FullRaceSimulation format.
        
        Args:
            pt_result: SimulationResult from PositionTracker
            sc_events: List of (start_lap, duration, is_vsc) tuples
            
        Returns:
            FullRaceSimulation compatible with FullRaceTab
        """
        # Build SC lap lookup
        sc_lap_set = set()
        for start, duration, _ in sc_events:
            for lap in range(start, start + duration):
                sc_lap_set.add(lap)
        
        # Build lap states from position_history
        lap_states = []
        for lap_idx, positions in enumerate(pt_result.position_history):
            lap_num = lap_idx + 1
            
            # Build gaps (approximate from lap times)
            gaps = {}
            leader_time = 0.0
            for driver, pos in sorted(positions.items(), key=lambda x: x[1]):
                if pos == 1:
                    gaps[driver] = 0.0
                    driver_lap_times = pt_result.lap_times.get(driver, [])
                    if lap_idx < len(driver_lap_times):
                        leader_time = sum(driver_lap_times[:lap_idx + 1])
                else:
                    driver_lap_times = pt_result.lap_times.get(driver, [])
                    if lap_idx < len(driver_lap_times):
                        driver_total = sum(driver_lap_times[:lap_idx + 1])
                        gaps[driver] = driver_total - leader_time
                    else:
                        gaps[driver] = (pos - 1) * 1.5  # Approximate 1.5s per position
            
            # Tire info (not available in PT result, use defaults)
            tire_ages = {d: lap_num for d in positions.keys()}
            compounds = {d: "M" for d in positions.keys()}
            
            lap_state = LapState(
                lap=lap_num,
                positions=positions,
                gaps=gaps,
                tire_ages=tire_ages,
                compounds=compounds,
                pit_stops=[],  # PT doesn't track pit stops yet
                sc_active=lap_num in sc_lap_set
            )
            lap_states.append(lap_state)
        
        # Build final standings
        final_standings = []
        race_laps = self.sim_params.race_laps
        
        # 🔧 Complete Mode 差距計算 (修正版 v4)
        # 問題 v3：圈時總和不準確，因為：
        #   1. 離散時間步長導致量化誤差
        #   2. 模擬結束時各車手圈數不同
        # 解決：使用「賽道位置差」計算 gap
        
        winner_code = pt_result.final_positions[0] if pt_result.final_positions else ""
        final_car_states = pt_result.final_car_states or {}
        
        # 計算平均圈時和平均速度（用於 gap 轉換）
        winner_lap_times = pt_result.lap_times.get(winner_code, [])
        if winner_lap_times:
            # ⚠️ 重要：只取前 race_laps 圈計算，模擬可能多跑幾圈
            winner_lap_times_for_race = winner_lap_times[:race_laps]
            avg_lap_time = sum(winner_lap_times_for_race) / len(winner_lap_times_for_race) if winner_lap_times_for_race else 90.0
            # ⚠️ 重要：winner_total_time 必須是 winner 完成 race_laps 圈的時間
            winner_total_time = sum(winner_lap_times_for_race)
        else:
            avg_lap_time = pt_result.total_time_s / race_laps
            winner_total_time = pt_result.total_time_s
        
        # 獲取賽道長度
        track_length_m = 5281.0  # 預設值
        if hasattr(self, '_position_tracker') and self._position_tracker:
            track_length_m = self._position_tracker.track_config.track_length_m
        
        # 每米需要多少秒
        seconds_per_meter = avg_lap_time / track_length_m
        
        # 🔍 調試輸出
        import sys
        sys.stdout.write(f"\n[GAP_CALC_v7] Winner: {winner_code}\n")
        sys.stdout.write(f"[GAP_CALC_v7] Winner 圈數: {len(winner_lap_times)}, 總時間: {winner_total_time:.2f}s\n")
        sys.stdout.write(f"[GAP_CALC_v7] 平均圈時: {avg_lap_time:.2f}s\n")
        sys.stdout.write(f"\n[GAP_DEBUG_v4] Winner: {winner_code}\n")
        sys.stdout.write(f"[GAP_DEBUG_v4] 平均圈時: {avg_lap_time:.2f}s\n")
        sys.stdout.write(f"[GAP_DEBUG_v4] 賽道長度: {track_length_m:.0f}m\n")
        sys.stdout.write(f"[GAP_DEBUG_v4] 每米時間: {seconds_per_meter:.4f}s/m\n")
        
        # 獲取 winner 的狀態
        winner_state_data = final_car_states.get(winner_code, {})
        winner_lap = winner_state_data.get("lap_number", race_laps)
        winner_pos_m = winner_state_data.get("position_m", 0)
        
        # 計算 winner 的總行駛距離（作為基準）
        winner_total_distance = winner_lap * track_length_m + winner_pos_m
        
        sys.stdout.write(f"[GAP_DEBUG_v4] Winner 狀態: L{winner_lap}, pos_m={winner_pos_m:.0f}m, 總距離={winner_total_distance:.0f}m\n")
        
        # 顯示前 5 名車手的賽道位置差 + 圈時總和差
        sys.stdout.write(f"[GAP_DEBUG_v4] ⚠️ 注意: pos_m 是模數位置，不代表真實差距！圈時總和才是正確的！\n")
        for i, driver_code in enumerate(pt_result.final_positions[:5]):
            driver_state_data = final_car_states.get(driver_code, {})
            driver_lap = driver_state_data.get("lap_number", 0)
            driver_pos_m = driver_state_data.get("position_m", 0)
            driver_total_distance = driver_lap * track_length_m + driver_pos_m
            distance_delta = winner_total_distance - driver_total_distance
            
            # 更重要：顯示圈時總和差
            driver_lap_times_debug = pt_result.lap_times.get(driver_code, [])[:race_laps]
            driver_total_time_debug = sum(driver_lap_times_debug) if driver_lap_times_debug else 0
            time_gap_from_laps = driver_total_time_debug - winner_total_time
            
            sys.stdout.write(f"[GAP_DEBUG_v4] P{i+1} {driver_code}: L{driver_lap}, 圈時總和={driver_total_time_debug:.2f}s, 真實gap={time_gap_from_laps:.2f}s\n")
        sys.stdout.flush()
        
        print(f"[RACE_SIM] Winner: {winner_code}, 使用賽道位置差計算 gap")
        
        # 取得 winner 的 base_pace 作為預設值
        winner_state = self._drivers.get(winner_code)
        winner_base_pace = winner_state.base_pace if winner_state else 90.0
        
        for pos_idx, driver_code in enumerate(pt_result.final_positions):
            position = pos_idx + 1
            driver_state = self._drivers.get(driver_code)
            
            if driver_state:
                grid_pos = driver_state.grid_position
                team = driver_state.team
                driver_base_pace = driver_state.base_pace
                driver_deg = driver_state.degradation_per_lap
            else:
                grid_pos = 20
                team = ""
                driver_base_pace = winner_base_pace + 1.0
                driver_deg = 0.05
            
            # 🔧 使用圈時總和差計算 gap (v9 - 取前 race_laps 圈)
            # ⚠️ 關鍵修正：模擬可能讓車手多跑幾圈，但 gap 只計算前 race_laps 圈
            #    1. 取前 race_laps 圈的圈時總和
            #    2. gap = sum(driver_lap_times[:race_laps]) - sum(winner_lap_times[:race_laps])
            #    3. 如果車手未完成 race_laps 圈，視為被套圈
            driver_lap_times_all = pt_result.lap_times.get(driver_code, [])
            winner_lap_times_all = winner_lap_times
            
            # 取前 race_laps 圈的圈時
            driver_lap_times = driver_lap_times_all[:race_laps]
            winner_lap_times_for_gap = winner_lap_times_all[:race_laps]
            
            driver_laps = len(driver_lap_times)  # 實際完成的圈數（最多 race_laps）
            winner_laps_for_gap = len(winner_lap_times_for_gap)
            
            if position == 1:
                gap = 0.0
                total_time = sum(winner_lap_times_for_gap) if winner_lap_times_for_gap else winner_total_time
            else:
                # 計算車手完成 race_laps 圈的時間
                if driver_lap_times:
                    total_time = sum(driver_lap_times)
                    
                    # 檢查圈數差異
                    lap_diff = race_laps - driver_laps
                    if lap_diff > 0:
                        # 被套圈：gap = 圈數差 × 平均圈時
                        gap = lap_diff * avg_lap_time
                    else:
                        # 圈數相同：gap = 此車手總時間 - 冠軍總時間
                        gap = total_time - winner_total_time
                else:
                    # 沒有圈時記錄，退回使用位置估算
                    driver_state_data = final_car_states.get(driver_code, {})
                    driver_lap = driver_state_data.get("lap_number", 0)
                    lap_diff = winner_lap - driver_lap
                    gap = lap_diff * avg_lap_time if lap_diff > 0 else 5.0
                    total_time = winner_total_time + gap
                
                # 確保 gap 為正值（落後 = 正值）
                gap = max(0.0, gap)
            
            # 🔍 調試：NOR 和 VER 的 gap 計算詳細
            if driver_code in ["NOR", "VER"]:
                sys.stdout.write(f"[GAP_CALC] {driver_code} P{position}: ")
                sys.stdout.write(f"laps={driver_laps}/{race_laps}, total_time={total_time:.2f}s, ")
                sys.stdout.write(f"winner_time={winner_total_time:.2f}s, gap={gap:.2f}s\n")
                sys.stdout.flush()
            
            # Get strategy notation from our data
            stints = self._strategies.get(driver_code, [])
            if stints:
                notation = "-".join(s.compound.value[0] for s in stints)
            else:
                notation = "M-H"
            
            result = RaceResult(
                driver_code=driver_code,
                team=team,
                final_position=position,
                grid_position=grid_pos,
                positions_gained=grid_pos - position,
                total_time=total_time,
                gap_to_winner=gap,
                pit_stops=len(stints) - 1 if stints else 1,
                strategy_notation=notation
            )
            final_standings.append(result)
        
        # Count successful overtakes
        successful_overtakes = sum(1 for a in pt_result.overtake_attempts if a.success)
        
        # Build result
        simulation = FullRaceSimulation(
            race_laps=pt_result.total_laps,
            total_drivers=len(pt_result.final_positions),
            lap_states=lap_states,
            final_standings=final_standings,
            sc_events=[
                {'lap': e[0], 'duration': e[1], 'is_vsc': e[2]}
                for e in sc_events
            ],
            total_pit_stops=sum(len(self._strategies.get(d, [])) - 1 for d in pt_result.final_positions),
            total_overtakes=successful_overtakes,
            overtake_attempts=pt_result.overtake_attempts,
            our_driver=self._our_driver or ""
        )
        
        # Find our result
        if self._our_driver:
            for standing in final_standings:
                if standing.driver_code == self._our_driver:
                    simulation.our_result = standing
                    break
        
        print(f"[RACE_SIM] Converted PT result: {len(lap_states)} laps, "
              f"{successful_overtakes} overtakes, "
              f"Winner: {pt_result.final_positions[0] if pt_result.final_positions else 'N/A'}")
        
        return simulation
    
    def _simulate_simple_mode(self, seed: Optional[int] = None) -> FullRaceSimulation:
        """
        Original simple simulation mode (existing logic).
        
        Uses lap-time based simulation without detailed position tracking.
        
        Args:
            seed: Random seed for reproducibility
            
        Returns:
            FullRaceSimulation with complete results
        """
        if seed is not None:
            random.seed(seed)
        
        # Initialize
        result = FullRaceSimulation(
            race_laps=self.sim_params.race_laps,
            total_drivers=len(self._drivers),
            our_driver=self._our_driver or ""
        )
        
        # Reset driver states
        for driver in self._drivers.values():
            driver.total_time = 0.0
            driver.tire_age = 0
            driver.pit_stops_made = 0
            driver.current_stint = 0
            driver.retired = False
            driver.laps_since_pit = 0
            driver.in_pit = False
            
            # Initialize track_position based on grid position
            # P1 starts with advantage, P20 starts behind
            # ✅ 增加 grid 位置初始差距（模擬起跑後的初始間距）
            # F1 起跑後 P1 vs P10 可能已經有 5-8 秒差距
            grid_gap = 0.8  # 每個位置 0.8 秒（原本 0.5）
            driver.track_position = (20 - driver.grid_position) * grid_gap
        
        print(f"[RACE_SIM] Race initialized with {len(self._drivers)} drivers")
        
        # Use injected SC events or generate random ones
        if hasattr(self, '_injected_sc_events') and self._injected_sc_events:
            sc_events = self._injected_sc_events
            self._injected_sc_events = None  # Clear after use
        else:
            sc_events = self._generate_sc_events()
        
        result.sc_events = [
            {'lap': e[0], 'duration': e[1], 'is_vsc': e[2]}
            for e in sc_events
        ]
        
        # Build SC lap set for quick lookup with VSC flag
        sc_laps = {}  # lap -> is_vsc
        for start, duration, is_vsc in sc_events:
            for lap in range(start, start + duration):
                if lap <= self.sim_params.race_laps:
                    sc_laps[lap] = is_vsc
        
        # Simulate each lap
        for lap in range(1, self.sim_params.race_laps + 1):
            sc_active = lap in sc_laps
            is_vsc = sc_laps.get(lap, False) if sc_active else False
            lap_state = self._simulate_lap(lap, sc_active, is_vsc)
            result.lap_states.append(lap_state)
            result.total_pit_stops += len(lap_state.pit_stops)
        
        # Calculate final standings
        result.final_standings = self._calculate_final_standings()
        
        # Find our result
        if self._our_driver:
            for standing in result.final_standings:
                if standing.driver_code == self._our_driver:
                    result.our_result = standing
                    break
        
        # ⚠️ 性能優化：預設不執行 Traffic Analysis
        # Traffic Analysis 很慢（20 車手 x 58 圈 = 1160 次檢查）
        # 在 Monte Carlo 和 Competitive Optimization 中執行 100-1000 次會非常慢
        # 改為：只在用戶明確查看 Traffic Analysis 標籤時才執行（延遲載入）
        result.traffic_data = {}  # 空字典表示尚未分析
        
        return result
    
    def simulate_race(self, seed: Optional[int] = None) -> FullRaceSimulation:
        """
        Simulate a complete race.
        
        Routes to either PositionTracker-based simulation (Complete mode)
        or simple lap-time simulation based on simple_mode flag.
        
        Args:
            seed: Random seed for reproducibility
            
        Returns:
            FullRaceSimulation with complete results
        """
        if self.simple_mode:
            print(f"[RACE_SIM] Running Simple mode simulation")
            return self._simulate_simple_mode(seed)
        else:
            # Complete mode: use PositionTracker if track_name is set
            if self.track_name:
                print(f"[RACE_SIM] Running Complete mode with PositionTracker")
                return self._simulate_with_position_tracker(seed)
            else:
                print(f"[RACE_SIM] No track_name set, falling back to Simple mode")
                return self._simulate_simple_mode(seed)
    
    def _generate_sc_events(self) -> List[Tuple[int, int, bool]]:
        """
        Generate SC/VSC events for the race.
        
        Returns:
            List of (start_lap, duration, is_vsc) tuples
        """
        events = []
        
        # Determine if SC occurs
        if random.random() < self.sc_probability:
            # Generate 1-2 SC events
            num_events = random.choices([1, 2], weights=[0.7, 0.3])[0]
            
            for _ in range(num_events):
                start_lap = random.randint(5, self.sim_params.race_laps - 5)
                duration = random.randint(3, 6)
                is_vsc = random.random() < self.vsc_probability
                events.append((start_lap, duration, is_vsc))
        
        return sorted(events, key=lambda x: x[0])
    
    def _simulate_lap(self, lap: int, sc_active: bool, is_vsc: bool = False) -> LapState:
        """
        Simulate a single lap for all drivers with REAL TRACK POSITION SYSTEM.
        
        Key concepts:
        1. track_position = cumulative "progress" on track (higher = further ahead)
        2. When pitting: loses pit_loss seconds of track_position
        3. Exit position determined by where others are when you rejoin
        4. Overtaking possible based on pace difference + track difficulty
        
        Args:
            lap: Current lap number
            sc_active: Whether SC is active
            is_vsc: Whether this is VSC (not full SC)
            
        Returns:
            LapState with positions and gaps
        """
        pit_stops_this_lap = []
        overtakes_this_lap = 0
        
        # ========== PHASE 1: Determine pit stops ==========
        drivers_wanting_to_pit = []
        for driver_code, state in self._drivers.items():
            if state.retired:
                continue
            if self._should_pit(driver_code, lap, sc_active, is_vsc):
                drivers_wanting_to_pit.append(driver_code)
        
        # Reactive pit decisions (cover pit)
        for driver_code, state in self._drivers.items():
            if state.retired or driver_code in drivers_wanting_to_pit:
                continue
            if self._should_reactive_pit(driver_code, lap, sc_active, drivers_wanting_to_pit):
                drivers_wanting_to_pit.append(driver_code)
        
        # Calculate pit lane traffic delays
        pit_traffic_delays = self._calculate_pit_traffic_delays(drivers_wanting_to_pit, sc_active)
        
        # ========== PHASE 2: Update track positions ==========
        # Each driver gains track_position based on their pace (faster = more progress)
        # Reference lap time for normalization
        reference_lap_time = self.sim_params.base_lap_time
        
        for driver_code, state in self._drivers.items():
            if state.retired:
                continue
            
            is_pitting = driver_code in drivers_wanting_to_pit
            
            # ✅ Calculate lap time (使用 Long Run 參數)
            base_lap_time = state.get_current_pace(
                self.sim_params, 
                sc_active,
                track_evolution_rate=self._long_run_track_evolution,
                fuel_effect_coef=self._long_run_fuel_effect,
                current_lap=lap
            )
            
            if is_pitting:
                # Pitting: lose time = pit_loss + traffic + random variation
                base_pit_loss = self.sim_params.pit_loss_sc if sc_active else self.sim_params.pit_loss_green
                
                # ✅ 降低進站隨機變異（保持合理真實性但減少過度隨機）
                # 模擬：輪胎槍故障、慢速換胎、定位錯誤、pit crew 表現等
                # 原本：-2.0 到 +4.0s（過於極端）
                # 修正：-0.5 到 +1.5s（更符合現代 F1 進站穩定性）
                pit_variation = random.uniform(-0.5, 1.5)
                pit_loss = base_pit_loss + pit_variation
                
                traffic_delay = pit_traffic_delays.get(driver_code, 0)
                total_pit_loss = pit_loss + traffic_delay
                
                actual_lap_time = base_lap_time + total_pit_loss
                pit_stops_this_lap.append(driver_code)
                
                # Update stint info
                state.pit_stops_made += 1
                state.current_stint += 1
                state.tire_age = 0
                state.laps_since_pit = 0
                state.in_pit = True
                
                # New tire compound
                if state.current_stint < len(state.stints):
                    state.current_tire = state.stints[state.current_stint].compound
                else:
                    # ✅ 額外進站時選擇輪胎
                    # 優先使用效益計算推薦的輪胎
                    from strategy_simulator.core.lap_simulator import Compound
                    
                    if hasattr(state, '_recommended_tire') and state._recommended_tire:
                        new_tire = state._recommended_tire
                        state._recommended_tire = None  # 清除推薦
                        print(f"[RACE_SIM] L{lap}: {driver_code} 使用推薦輪胎 {new_tire.value}")
                    else:
                        # 備用邏輯：根據剩餘圈數選擇
                        remaining_laps = self.sim_params.race_laps - lap
                        current_compound = state.current_tire.value if hasattr(state.current_tire, 'value') else str(state.current_tire)
                        
                        if remaining_laps <= 12:
                            # 短距離：可以用軟胎沖刺
                            new_tire = Compound.SOFT
                        elif remaining_laps <= 20:
                            # 中距離：用中性胎
                            new_tire = Compound.MEDIUM
                        else:
                            # 長距離：用硬胎
                            new_tire = Compound.HARD
                        
                        # 避免換相同的輪胎（除非必要）
                        if new_tire.value.upper() == current_compound.upper() and remaining_laps > 12:
                            # 換成更硬一級的輪胎
                            if current_compound.upper() == 'SOFT':
                                new_tire = Compound.MEDIUM
                            elif current_compound.upper() == 'MEDIUM':
                                new_tire = Compound.HARD
                        
                        print(f"[RACE_SIM] L{lap}: {driver_code} 額外進站換 {new_tire.value} (剩 {remaining_laps} 圈)")
                    
                    state.current_tire = new_tire
                
                print(f"[RACE_SIM] L{lap}: {driver_code} PITS - loss={total_pit_loss:.1f}s "
                      f"(base={pit_loss:.1f}s, traffic={traffic_delay:.1f}s, variation={pit_variation:+.1f}s)")
            else:
                actual_lap_time = base_lap_time
                state.laps_since_pit += 1
                state.in_pit = False
            
            # Update timing
            state.tire_age += 1
            state.total_time += actual_lap_time
            
            # KEY: Update track_position
            # Progress = reference_lap_time - actual_lap_time (faster = more progress)
            # Accumulate relative to a reference pace
            lap_progress = reference_lap_time - actual_lap_time
            state.track_position += lap_progress
        
        # ========== PHASE 3: Calculate positions based on track_position ==========
        # Sort by track_position (higher = ahead)
        active_drivers = [
            (code, state) for code, state in self._drivers.items()
            if not state.retired
        ]
        sorted_by_track = sorted(
            active_drivers,
            key=lambda x: x[1].track_position,
            reverse=True  # Higher track_position = ahead
        )
        
        # ========== PHASE 4: Simulate overtaking ==========
        # ⚠️ CRITICAL: No overtaking allowed under SC/VSC (F1 rules)
        # ⚠️ Simple mode: Skip overtaking simulation for faster performance
        if sc_active:
            print(f"[RACE_SIM] L{lap}: SC/VSC active - overtaking prohibited")
            # Skip overtaking phase, maintain current order
            new_order = list(sorted_by_track)
        elif self.simple_mode:
            # Simple mode: no overtaking simulation
            new_order = list(sorted_by_track)
        else:
            # Check if faster car behind can overtake slower car ahead
            new_order = list(sorted_by_track)  # Copy to modify
            
            for i in range(1, len(new_order)):
                behind_code, behind_state = new_order[i]
                ahead_code, ahead_state = new_order[i - 1]
                
                # Calculate gap (in track_position units, which is like seconds)
                gap = ahead_state.track_position - behind_state.track_position
                
                # Only attempt overtake if within DRS range (~1 second)
                if gap > 1.5:
                    continue
                
                # ✅ Calculate pace difference (使用 Long Run 參數)
                behind_pace = behind_state.get_current_pace(
                    self.sim_params, sc_active,
                    track_evolution_rate=self._long_run_track_evolution,
                    fuel_effect_coef=self._long_run_fuel_effect,
                    current_lap=lap
                )
                ahead_pace = ahead_state.get_current_pace(
                    self.sim_params, sc_active,
                    track_evolution_rate=self._long_run_track_evolution,
                    fuel_effect_coef=self._long_run_fuel_effect,
                    current_lap=lap
                )
                pace_diff = ahead_pace - behind_pace  # Positive = behind is faster
                
                # Fresh tire advantage (just pitted = big advantage)
                tire_advantage = 0
                if behind_state.laps_since_pit <= 3:  # Fresh tires
                    tire_advantage += 0.3
                if ahead_state.tire_age > 20:  # Worn tires ahead
                    tire_advantage += 0.2
                
                # Overtake probability
                # Base: pace_diff * factor + tire_advantage - track_difficulty
                overtake_chance = (pace_diff * 0.5) + tire_advantage - (self.overtaking_difficulty * 0.3)
                overtake_chance = max(0.0, min(0.8, overtake_chance))  # Clamp 0-80%
                
                # Attempt overtake
                if random.random() < overtake_chance:
                    # Successful overtake: swap positions
                    new_order[i - 1], new_order[i] = new_order[i], new_order[i - 1]
                    
                    # Also update track_position to reflect the pass
                    # The overtaking car gains a small track position advantage
                    behind_state.track_position += 0.3
                    ahead_state.track_position -= 0.3
                    
                    overtakes_this_lap += 1
                    print(f"[RACE_SIM] L{lap}: {behind_code} OVERTAKES {ahead_code} "
                          f"(gap={gap:.2f}s, pace_diff={pace_diff:.2f}s, prob={overtake_chance:.0%})")
        
        # ========== PHASE 5: Assign final positions ==========
        gaps = {}
        leader_total_time = new_order[0][1].total_time if new_order else 0.0
        
        for pos, (driver_code, state) in enumerate(new_order, 1):
            old_pos = state.position
            state.position = pos
            
            # ✅ Calculate gap to leader using cumulative time (not track_position)
            # This shows the true time difference, including pit stops and pace variations
            gap_to_leader = state.total_time - leader_total_time
            gaps[driver_code] = gap_to_leader
            state.gap_to_leader = gap_to_leader
            
            # Log significant position changes
            if old_pos != pos and abs(old_pos - pos) >= 2:
                direction = "gained" if pos < old_pos else "lost"
                print(f"[RACE_SIM] L{lap}: {driver_code} {direction} {abs(old_pos - pos)} positions "
                      f"(P{old_pos} -> P{pos})")
        
        return LapState(
            lap=lap,
            positions={code: state.position for code, state in self._drivers.items()},
            gaps=gaps,
            tire_ages={code: state.tire_age for code, state in self._drivers.items()},
            compounds={code: state.current_tire.value for code, state in self._drivers.items()},
            pit_stops=pit_stops_this_lap,
            sc_active=sc_active
        )
    
    def _should_reactive_pit(
        self, 
        driver_code: str, 
        lap: int, 
        sc_active: bool,
        drivers_pitting: List[str]
    ) -> bool:
        """
        Determine if driver should make a reactive pit stop to cover rivals.
        
        Implements real F1 strategy dynamics:
        1. Defensive cover: React to rival pitting (prevent undercut)
        2. Offensive undercut: Pit before rival if they're vulnerable
        3. Position-based aggression: Lower positions more aggressive
        
        Args:
            driver_code: Driver to check
            lap: Current lap
            sc_active: Whether SC is active
            drivers_pitting: List of drivers already planning to pit
            
        Returns:
            True if should make cover pit or undercut attempt
        """
        state = self._drivers[driver_code]
        
        if state.retired:
            return False
        
        # Already completed all planned stops
        if state.current_stint >= len(state.stints) - 1:
            return False
        
        # Check if tire life allows staying out
        tire_durability = {'SOFT': 18, 'MEDIUM': 28, 'HARD': 40}
        current_compound = state.current_tire.value if hasattr(state.current_tire, 'value') else str(state.current_tire)
        max_tire_life = tire_durability.get(current_compound.upper(), 28)
        
        # ✅ 改進 1: 更真實的輪胎狀況評估
        tire_worn_percentage = state.tire_age / max_tire_life
        tire_viable = tire_worn_percentage >= 0.4  # 40% 以上才考慮進站
        
        if not tire_viable:
            # 輪胎太新，不會反應進站
            return False
        
        # ✅ 改進 2: 防守性反制 (Defensive Cover)
        # 檢查直接對手是否正在進站
        for rival_code in drivers_pitting:
            rival = self._drivers.get(rival_code)
            if not rival:
                continue
            
            pos_diff = abs(state.position - rival.position)
            gap_diff = abs(state.gap_to_leader - rival.gap_to_leader)
            
            # 近距離對手進站 - 強烈考慮反制
            if pos_diff <= 3 and gap_diff <= 5.0:
                # 根據位置調整反應機率
                if state.position <= 5:
                    # 前排車手：非常保守防守（80-90% 反制）
                    cover_probability = 0.85 if sc_active else 0.80
                elif state.position <= 12:
                    # 中游車手：標準防守（60-70% 反制）
                    cover_probability = 0.70 if sc_active else 0.60
                else:
                    # 後排車手：較不在意防守（40-50% 反制）
                    cover_probability = 0.50 if sc_active else 0.40
                
                if random.random() < cover_probability:
                    print(f"[STRATEGY] L{lap}: {driver_code} (P{state.position}) "
                          f"反制 {rival_code} 進站 - Defensive Cover")
                    return True
        
        # ✅ 改進 3: 進攻性 Undercut（針對前車）
        # 如果前車輪胎老化且即將進站，搶先進站嘗試 undercut
        if tire_worn_percentage >= 0.6:  # 自己輪胎已用 60% 以上
            # 找出正前方的對手
            sorted_drivers = sorted(
                [(code, s) for code, s in self._drivers.items() if not s.retired],
                key=lambda x: x[1].position
            )
            
            for i, (code, s) in enumerate(sorted_drivers):
                if code == driver_code and i > 0:
                    # 找到前一位車手
                    ahead_code, ahead_state = sorted_drivers[i - 1]
                    
                    # 檢查前車是否即將進站（輪胎老化）
                    if ahead_state.stints and ahead_state.current_stint < len(ahead_state.stints):
                        ahead_stint = ahead_state.stints[ahead_state.current_stint]
                        ahead_planned_pit_lap = ahead_stint.start_lap + ahead_stint.laps
                        
                        # 前車預計在未來 2-4 圈進站
                        laps_until_ahead_pits = ahead_planned_pit_lap - lap
                        
                        if 2 <= laps_until_ahead_pits <= 4:
                            # 檢查差距是否適合 undercut（5 秒內）
                            gap = abs(state.gap_to_leader - ahead_state.gap_to_leader)
                            
                            if gap <= 5.0:
                                # 根據位置決定激進程度
                                if state.position <= 5:
                                    undercut_probability = 0.4  # 前排較保守
                                elif state.position <= 12:
                                    undercut_probability = 0.6  # 中游標準
                                else:
                                    undercut_probability = 0.8  # 後排激進
                                
                                if random.random() < undercut_probability:
                                    print(f"[STRATEGY] L{lap}: {driver_code} (P{state.position}) "
                                          f"嘗試 Undercut {ahead_code} (P{ahead_state.position}) "
                                          f"- 提前 {laps_until_ahead_pits} 圈進站")
                                    return True
                    break
        
        return False
    
    def _calculate_pit_traffic_delays(
        self, 
        drivers_pitting: List[str],
        sc_active: bool
    ) -> Dict[str, float]:
        """
        Calculate pit lane traffic delays for each pitting driver.
        
        Factors:
        - Number of cars pitting on same lap
        - Same team double-stack (teammate has priority)
        - Position order (front runners pit first)
        
        Args:
            drivers_pitting: List of driver codes pitting this lap
            sc_active: Whether SC is active (more traffic under SC)
            
        Returns:
            Dict of driver_code -> additional delay in seconds
        """
        delays = {}
        
        if len(drivers_pitting) <= 1:
            # No traffic
            return {d: 0 for d in drivers_pitting}
        
        # Sort by current position (front runners arrive at pit lane first)
        sorted_pitters = sorted(
            drivers_pitting,
            key=lambda d: self._drivers[d].position if d in self._drivers else 20
        )
        
        # Base delay per car in front: 2-3 seconds under green, 3-5 under SC
        base_delay_per_car = 4.0 if sc_active else 2.5
        
        # Track team pit boxes for double-stack calculation
        team_pit_order = {}  # team -> list of drivers in pit order
        
        for i, driver_code in enumerate(sorted_pitters):
            state = self._drivers.get(driver_code)
            if not state:
                delays[driver_code] = 0
                continue
            
            # Base traffic delay
            traffic_delay = 0
            
            # Delay based on pit lane congestion
            # More cars = potential for slow lane traffic
            if len(drivers_pitting) >= 5:
                traffic_delay += random.uniform(1.0, 3.0)  # High traffic
            elif len(drivers_pitting) >= 3:
                traffic_delay += random.uniform(0.5, 1.5)  # Moderate traffic
            
            # Double-stack calculation (same team)
            team = state.team
            if team:
                if team not in team_pit_order:
                    team_pit_order[team] = []
                
                # If teammate already pitting, add double-stack delay
                if len(team_pit_order[team]) > 0:
                    # Second car in stack waits ~2-4 seconds extra
                    traffic_delay += random.uniform(2.0, 4.0)
                    print(f"[RACE_SIM] Double stack: {driver_code} waits for teammate")
                
                team_pit_order[team].append(driver_code)
            
            # Unsafe release risk (small random delay)
            if random.random() < 0.05:  # 5% chance
                traffic_delay += random.uniform(1.0, 2.0)
            
            delays[driver_code] = traffic_delay
        
        return delays
    
    def _estimate_pit_queue_size(self, lap: int, sc_type: str) -> int:
        """
        估算 SC/VSC 期間會有多少車進站（用於塞車預測）
        
        Simple 模式：根據輪胎年齡統計
        Complete 模式：根據各車策略和位置預測
        
        ✅ 使用 SimulationParams 中的 Long Run 數據估算輪胎壽命
        
        Args:
            lap: 當前圈數
            sc_type: 'SC' 或 'VSC'
            
        Returns:
            預計進站車輛數
        """
        from strategy_simulator.core.lap_simulator import Compound
        
        # 使用 SimulationParams 估算輪胎壽命
        def estimate_tire_life(compound: Compound) -> int:
            base = self.sim_params.get_deg_rate(compound)
            if base > 0:
                return int(min(2.5 / base, 50))
            return 30
        
        tire_life = {
            'SOFT': estimate_tire_life(Compound.SOFT),
            'MEDIUM': estimate_tire_life(Compound.MEDIUM),
            'HARD': estimate_tire_life(Compound.HARD),
        }
        
        if self.simple_mode:
            # ========== Simple 模式：根據輪胎年齡統計 ==========
            old_tire_count = 0
            for driver_code, state in self._drivers.items():
                if state.retired:
                    continue
                current_compound = state.current_tire.value if hasattr(state.current_tire, 'value') else str(state.current_tire)
                max_life = tire_life.get(current_compound.upper(), 28)
                # 輪胎用了 50% 以上視為「老胎」
                if state.tire_age >= max_life * 0.5:
                    old_tire_count += 1
            return old_tire_count
        else:
            # ========== Complete 模式：根據策略和位置預測 ==========
            likely_pitters = 0
            for driver_code, state in self._drivers.items():
                if state.retired:
                    continue
                
                current_compound = state.current_tire.value if hasattr(state.current_tire, 'value') else str(state.current_tire)
                max_life = tire_life.get(current_compound.upper(), 28)
                remaining_laps = self.sim_params.race_laps - lap
                
                # 計算是否會進站的條件
                has_planned_stop = state.current_stint < len(state.stints) - 1
                tire_worn = state.tire_age >= max_life * 0.4
                enough_laps = remaining_laps >= 10
                
                # 有計劃進站且輪胎老化 → 高機率進站
                if has_planned_stop and tire_worn:
                    likely_pitters += 1
                # 沒有計劃進站但輪胎很老 → 可能額外進站
                elif not has_planned_stop and state.tire_age >= max_life * 0.6 and enough_laps:
                    likely_pitters += 0.5  # 半個車的權重
            
            return int(likely_pitters)
    
    def _calculate_sc_pit_benefit(
        self, 
        driver_code: str, 
        lap: int, 
        sc_type: str,
        pit_queue_size: int
    ) -> tuple:
        """
        計算 SC/VSC 期間進站的淨效益
        
        使用圈對圈模擬比較：
        - 選項 A：繼續用老胎跑完剩餘圈數
        - 選項 B：進站換新胎
        
        ✅ 使用 SimulationParams 中的 Long Run 數據，非硬編碼
        
        Args:
            driver_code: 車手代碼
            lap: 當前圈數
            sc_type: 'SC' 或 'VSC'
            pit_queue_size: 預計進站車輛數
            
        Returns:
            (net_benefit, recommended_tire, should_pit)
        """
        from strategy_simulator.core.lap_simulator import Compound
        
        state = self._drivers[driver_code]
        remaining_laps = self.sim_params.race_laps - lap
        
        # ========== 從 SimulationParams 獲取輪胎參數 ==========
        # 這些參數來自 Long Run 數據或賽道配置
        def get_deg_params(compound: Compound):
            """獲取輪胎退化參數"""
            base = self.sim_params.get_deg_rate(compound)
            accel = self.sim_params.get_deg_acceleration(compound)
            delta = self.sim_params.get_compound_delta(compound)
            return base, accel, delta
        
        # 輪胎耐久度估算（基於退化率計算）
        # 當累積退化超過 2.5s 時視為「懸崖」
        def estimate_tire_life(compound: Compound) -> int:
            base, accel, _ = get_deg_params(compound)
            # 解二次方程：base * t + 0.5 * accel * t² = 2.5
            # 簡化估算：life ≈ 2.5 / base
            if base > 0:
                return int(min(2.5 / base, 50))  # 上限 50 圈
            return 30
        
        tire_life = {
            Compound.SOFT: estimate_tire_life(Compound.SOFT),
            Compound.MEDIUM: estimate_tire_life(Compound.MEDIUM),
            Compound.HARD: estimate_tire_life(Compound.HARD),
        }
        
        current_compound_enum = None
        current_compound_str = state.current_tire.value if hasattr(state.current_tire, 'value') else str(state.current_tire)
        current_compound_str = current_compound_str.upper()
        
        # 轉換為 Compound enum
        for c in [Compound.SOFT, Compound.MEDIUM, Compound.HARD]:
            if c.value.upper() == current_compound_str:
                current_compound_enum = c
                break
        if not current_compound_enum:
            current_compound_enum = Compound.MEDIUM
        
        current_tire_age = state.tire_age
        
        # ========== 選項 A：繼續用老胎 ==========
        def calc_remaining_time_on_old_tire():
            """計算繼續用老胎跑完剩餘圈數的總時間損失"""
            total_loss = 0.0
            base, accel, delta = get_deg_params(current_compound_enum)
            max_life = tire_life[current_compound_enum]
            cliff_lap = int(max_life * 1.3)
            
            for i in range(remaining_laps):
                age = current_tire_age + i
                
                if age > cliff_lap:
                    # 超過懸崖點，大幅掉速
                    lap_degradation = base * cliff_lap + accel * (cliff_lap ** 2)
                    lap_degradation += (age - cliff_lap) * 0.8  # 懸崖後每圈額外 +0.8s
                else:
                    # 累積退化：base × age + accel × age²
                    lap_degradation = base * age + accel * (age ** 2)
                
                total_loss += lap_degradation
            
            return total_loss
        
        old_tire_loss = calc_remaining_time_on_old_tire()
        
        # ========== 選項 B：換新胎 ==========
        best_tire = None
        best_total_time = float('inf')
        best_tire_detail = {}
        
        for compound in [Compound.SOFT, Compound.MEDIUM, Compound.HARD]:
            compound_name = compound.value.upper()
            max_life = tire_life[compound]
            cliff_lap = int(max_life * 1.3)
            
            # 獲取該輪胎的實際參數
            base, accel, pace_delta = get_deg_params(compound)
            
            total_time = 0.0
            for i in range(remaining_laps):
                tire_age_on_new = i + 1  # 新胎從第 1 圈開始
                
                # 速度優勢（相對於 baseline）
                lap_time = pace_delta
                
                # 退化
                if tire_age_on_new > cliff_lap:
                    # 超過懸崖點，大幅掉速
                    lap_time += base * cliff_lap + accel * (cliff_lap ** 2)
                    lap_time += (tire_age_on_new - cliff_lap) * 0.8
                else:
                    lap_time += base * tire_age_on_new + accel * (tire_age_on_new ** 2)
                
                total_time += lap_time
            
            # SC 重啟優勢（軟胎加熱快）
            restart_bonus = 0.0
            if compound_name == 'SOFT' and sc_type == 'SC':
                restart_bonus = -1.5  # 重啟時快 1.5s
            
            total_time += restart_bonus
            
            # 記錄最佳選擇
            if total_time < best_total_time:
                best_total_time = total_time
                best_tire = compound
                best_tire_detail = {
                    'compound': compound_name,
                    'total_time': total_time,
                    'restart_bonus': restart_bonus,
                    'base_deg': base,
                    'pace_delta': pace_delta
                }
        
        # ========== 進站成本 ==========
        pit_green = self.sim_params.pit_loss_green
        if sc_type == 'VSC':
            pit_sc = self.sim_params.pit_loss_vsc
        else:
            pit_sc = self.sim_params.pit_loss_sc
        
        # 塞車損失
        traffic_loss = pit_queue_size * 2.5
        
        total_pit_cost = pit_sc + traffic_loss
        
        # ========== 淨效益計算 ==========
        new_tire_total_cost = best_total_time + total_pit_cost
        net_benefit = old_tire_loss - new_tire_total_cost
        
        # 如果車手還沒完成計劃進站，SC 進站可以省下未來的正常進站成本
        has_planned_stop = state.current_stint < len(state.stints) - 1
        if has_planned_stop:
            future_pit_saving = pit_green - pit_sc
            net_benefit += future_pit_saving
        
        # ========== 決策閾值 ==========
        if sc_type == 'VSC':
            threshold = 6.0
        else:
            threshold = 4.0
        
        should_pit = net_benefit > threshold
        
        # Debug 輸出
        print(f"[SC_BENEFIT] {driver_code} {sc_type} (Lap {lap}, 剩 {remaining_laps} 圈):")
        print(f"  老 {current_compound_str} (age={current_tire_age}): 剩餘退化損失 = {old_tire_loss:.1f}s")
        print(f"  新 {best_tire_detail.get('compound', 'N/A')} (deg={best_tire_detail.get('base_deg', 0):.3f}, delta={best_tire_detail.get('pace_delta', 0):.2f}s): "
              f"總時間 = {best_total_time:.1f}s + 進站 {total_pit_cost:.1f}s = {new_tire_total_cost:.1f}s")
        print(f"  {'✅' if has_planned_stop else '❌'} 有計劃進站 → {'節省 ' + f'{future_pit_saving:.0f}s' if has_planned_stop else '額外進站'}")
        print(f"  淨效益 = {net_benefit:.1f}s → {'PIT' if should_pit else 'STAY'} (閾值={threshold}s)")
        
        return (net_benefit, best_tire, should_pit)
    
    def _should_pit(self, driver_code: str, lap: int, sc_active: bool, is_vsc: bool = False) -> bool:
        """
        Determine if driver should pit on this lap.
        
        使用效益計算邏輯決定 SC/VSC 期間是否進站。
        
        Args:
            driver_code: Driver to check
            lap: Current lap
            sc_active: Whether SC is active (opportunistic pit)
            is_vsc: Whether this is VSC (different strategy than full SC)
            
        Returns:
            True if should pit
        """
        state = self._drivers[driver_code]
        
        if state.retired:
            return False
        
        # Check planned pit lap first (always execute planned stops)
        if state.stints and state.current_stint < len(state.stints) - 1:
            current_stint = state.stints[state.current_stint]
            planned_pit_lap = current_stint.start_lap + current_stint.laps
            
            # Pit on planned lap
            if lap == planned_pit_lap:
                return True
        
        # ========== SC/VSC 效益計算進站決策 ==========
        if sc_active:
            sc_type = 'VSC' if is_vsc else 'SC'
            remaining_laps = self.sim_params.race_laps - lap
            
            # 如果剩餘圈數太少，不進站
            if remaining_laps < 8:
                return False
            
            # 估算塞車情況
            pit_queue_size = self._estimate_pit_queue_size(lap, sc_type)
            
            # 計算進站效益
            net_benefit, recommended_tire, should_pit = self._calculate_sc_pit_benefit(
                driver_code, lap, sc_type, pit_queue_size
            )
            
            # 已完成計劃進站的車手：需要更高效益才會額外進站
            if state.current_stint >= len(state.stints) - 1:
                # 額外進站需要淨效益 > 10s
                if net_benefit > 10.0:
                    # 加入一些隨機性（60% 機率執行）
                    if random.random() < 0.6:
                        # 儲存推薦輪胎供進站時使用
                        state._recommended_tire = recommended_tire
                        print(f"[RACE_SIM] {driver_code} {sc_type} 額外進站 (benefit={net_benefit:.1f}s)")
                        return True
            else:
                # 有計劃進站：使用標準閾值
                if should_pit:
                    # 檢查是否在合理的進站窗口內
                    current_stint = state.stints[state.current_stint]
                    planned_pit_lap = current_stint.start_lap + current_stint.laps
                    in_window = abs(lap - planned_pit_lap) <= 8
                    
                    # 在窗口內或效益特別大時進站
                    if in_window or net_benefit > 12.0:
                        # 加入隨機性（80% 機率執行）
                        if random.random() < 0.8:
                            print(f"[RACE_SIM] {driver_code} {sc_type} 機會進站 (benefit={net_benefit:.1f}s)")
                            return True
        
        return False
    
    def _calculate_final_standings(self) -> List[RaceResult]:
        """Calculate final race standings."""
        standings = []
        
        # Sort by total time (finished) then position (DNF)
        sorted_drivers = sorted(
            self._drivers.values(),
            key=lambda d: (d.retired, d.total_time)
        )
        
        winner_time = sorted_drivers[0].total_time if sorted_drivers else 0
        
        for pos, state in enumerate(sorted_drivers, 1):
            # Build strategy notation
            notation = "-".join(s.compound.value[0] for s in state.stints) if state.stints else "N/A"
            
            standings.append(RaceResult(
                driver_code=state.driver_code,
                team=state.team,
                final_position=pos,
                grid_position=state.grid_position,
                positions_gained=state.grid_position - pos,
                total_time=state.total_time,
                gap_to_winner=state.total_time - winner_time,
                pit_stops=state.pit_stops_made,
                strategy_notation=notation,
                retired=state.retired,
                dnf_reason=state.dnf_reason
            ))
        
        return standings
    
    def _analyze_all_drivers_traffic(self, lap_states: List[LapState]) -> Dict[str, Dict[str, Any]]:
        """
        分析所有車手的 traffic 影響。
        
        Args:
            lap_states: 所有圈的狀態列表
            
        Returns:
            Dict[driver_code, traffic_info]: 每個車手的 traffic 數據
        """
        # 快速模式：跳過詳細分析以提升性能
        # Traffic analysis 很慢（20 車手 x 58 圈 = 1160 次檢查）
        
        if not lap_states:
            return {}
        
        all_drivers = set()
        for lap_state in lap_states:
            all_drivers.update(lap_state.positions.keys())
        
        print(f"[TRAFFIC_ANALYSIS] ⚡ 快速模式：{len(all_drivers)} 位車手", flush=True)
        
        all_drivers_traffic = {}
        
        # 為每位車手分析 traffic（簡化版）
        for idx, driver_code in enumerate(all_drivers):
            # 每 5 位車手顯示一次進度
            if idx % 5 == 0:
                print(f"[TRAFFIC_ANALYSIS] 進度：{idx + 1}/{len(all_drivers)}", flush=True)
            lap_details = {}
            total_blocked_laps = 0
            clean_laps = 0
            sc_vsc_laps = 0
            
            for lap_state in lap_states:
                lap_num = lap_state.lap
                
                # 檢查該車手是否在這圈中
                our_pos = lap_state.positions.get(driver_code)
                if our_pos is None:
                    continue
                
                # SC/VSC 檢測
                sc_active = getattr(lap_state, 'sc_active', False)
                vsc_active = getattr(lap_state, 'vsc_active', False)
                
                if sc_active or vsc_active:
                    lap_details[lap_num] = {
                        'sc_active': sc_active,
                        'vsc_active': vsc_active,
                        'blocked': False,
                        'clean': False
                    }
                    sc_vsc_laps += 1
                    continue
                
                # 如果是領先，標記為 clean
                if our_pos == 1:
                    lap_details[lap_num] = {
                        'sc_active': False,
                        'vsc_active': False,
                        'blocked': False,
                        'clean': True
                    }
                    clean_laps += 1
                    continue
                
                # 找到前面的車手
                driver_ahead = None
                for other_driver, pos in lap_state.positions.items():
                    if pos == our_pos - 1:
                        driver_ahead = other_driver
                        break
                
                if not driver_ahead:
                    lap_details[lap_num] = {
                        'sc_active': False,
                        'vsc_active': False,
                        'blocked': False,
                        'clean': True
                    }
                    clean_laps += 1
                    continue
                
                # 計算與前車的間隙
                our_gap = lap_state.gaps.get(driver_code, 999.0)
                ahead_gap = lap_state.gaps.get(driver_ahead, 0.0)
                gap_to_ahead = our_gap - ahead_gap
                
                # Traffic threshold: < 1.5 秒 = blocked
                blocked = 0 < gap_to_ahead < 1.5
                
                lap_details[lap_num] = {
                    'sc_active': False,
                    'vsc_active': False,
                    'blocked': blocked,
                    'clean': not blocked,
                    'gap_to_ahead': gap_to_ahead,
                    'driver_ahead': driver_ahead
                }
                
                if blocked:
                    total_blocked_laps += 1
                else:
                    clean_laps += 1
            
            all_drivers_traffic[driver_code] = {
                'lap_details': lap_details,
                'total_blocked_laps': total_blocked_laps,
                'clean_laps': clean_laps,
                'sc_vsc_laps': sc_vsc_laps
            }
        
        print(f"[TRAFFIC_ANALYSIS] ✅ 完成，返回 {len(all_drivers_traffic)} 位車手的數據")
        return all_drivers_traffic
    
    def _analyze_traffic(self, lap_states: List[LapState]) -> Dict[str, Any]:
        """
        Analyze traffic impact on our driver.
        
        Args:
            lap_states: List of lap states from simulation
            
        Returns:
            Dictionary with traffic statistics
        """
        if not self._our_driver:
            print(f"[TRAFFIC_ANALYSIS] ⚠️ 無法分析：未設置 our_driver")
            return {}
        
        print(f"[TRAFFIC_ANALYSIS] 開始分析 {self._our_driver} 的 traffic 影響...")
        print(f"[TRAFFIC_ANALYSIS] 總圈數: {len(lap_states)}")
        
        blocked_laps = []
        blocker_stats = defaultdict(lambda: {'count': 0, 'estimated_loss': 0.0})
        total_estimated_loss = 0.0
        drs_train_laps = 0
        
        for lap_state in lap_states:
            our_pos = lap_state.positions.get(self._our_driver)
            our_gap = lap_state.gaps.get(self._our_driver, 999.0)
            
            if our_pos is None or our_pos == 1:
                continue  # Leading or not in race
            
            # Find driver directly ahead
            driver_ahead = None
            for driver_code, pos in lap_state.positions.items():
                if pos == our_pos - 1:
                    driver_ahead = driver_code
                    break
            
            if not driver_ahead:
                continue
            
            # Calculate gap to car ahead (approximate)
            ahead_gap = lap_state.gaps.get(driver_ahead, 0.0)
            gap_to_ahead = our_gap - ahead_gap
            
            # Traffic threshold: < 1.5 seconds = blocked
            if 0 < gap_to_ahead < 1.5:
                blocked_laps.append({
                    'lap': lap_state.lap,
                    'blocker': driver_ahead,
                    'gap': gap_to_ahead,
                    'position': our_pos
                })
                
                # Estimate time loss: closer gap = more loss
                # Max ~0.3s per lap when very close
                estimated_loss = max(0.0, (1.5 - gap_to_ahead) * 0.2)
                blocker_stats[driver_ahead]['count'] += 1
                blocker_stats[driver_ahead]['estimated_loss'] += estimated_loss
                total_estimated_loss += estimated_loss
                
                # Check for DRS train (multiple cars close)
                drs_train = sum(1 for g in lap_state.gaps.values() 
                               if abs(g - our_gap) < 1.5) >= 3
                if drs_train:
                    drs_train_laps += 1
        
        # Sort blockers by frequency
        top_blockers = sorted(
            blocker_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:5]  # Top 5 blockers
        
        # ✅ 調試輸出
        print(f"[TRAFFIC_ANALYSIS] 結果: {len(blocked_laps)} 圈受阻擋，預估損失 {total_estimated_loss:.1f}s")
        if top_blockers:
            print(f"[TRAFFIC_ANALYSIS] 主要阻擋者: {top_blockers[0][0]} ({top_blockers[0][1]['count']} 圈)")
        
        result = {
            'total_blocked_laps': len(blocked_laps),
            'total_estimated_loss': total_estimated_loss,
            'drs_train_laps': drs_train_laps,
            'top_blockers': [
                {
                    'driver': blocker,
                    'laps_blocked': stats['count'],
                    'estimated_loss': stats['estimated_loss']
                }
                for blocker, stats in top_blockers
            ],
            'blocked_lap_details': blocked_laps[:10]  # Keep first 10 for detail view
        }
        
        print(f"[TRAFFIC_ANALYSIS] 返回數據: {result}")
        return result
    
    def run_multiple_simulations(
        self, 
        iterations: int = 100,
        seed_offset: int = 0,
        strategy_pool: list = None
    ) -> Dict[str, Any]:
        """
        Run multiple race simulations for statistical analysis.
        
        Args:
            iterations: Number of simulations
            seed_offset: Random seed offset to ensure different results each run
            strategy_pool: List of strategy dicts with 'name', 'notation', 'stints'
            
        Returns:
            Dictionary with aggregated statistics
        """
        position_counts = defaultdict(lambda: defaultdict(int))
        total_gains = defaultdict(list)
        win_counts = defaultdict(int)
        strategy_stats = defaultdict(lambda: {'wins': 0, 'positions': []})
        
        for i in range(iterations):
            # Rotate through strategy pool if provided
            if strategy_pool and len(strategy_pool) > 0:
                strategy_idx = i % len(strategy_pool)
                current_strategy = strategy_pool[strategy_idx]
                # Update our driver's strategy for this iteration
                if self._our_driver:
                    self.set_our_strategy(self._our_driver, current_strategy['stints'])
            
            result = self.simulate_race(seed=seed_offset + i)
            
            for standing in result.final_standings:
                driver = standing.driver_code
                pos = standing.final_position
                position_counts[driver][pos] += 1
                total_gains[driver].append(standing.positions_gained)
                
                if pos == 1:
                    win_counts[driver] += 1
                
                # Track strategy for our driver
                if driver == self._our_driver:
                    strategy = standing.strategy_notation
                    strategy_stats[strategy]['positions'].append(pos)
                    if pos == 1:
                        strategy_stats[strategy]['wins'] += 1
        
        # Calculate statistics
        statistics = {}
        for driver in self._drivers.keys():
            positions = []
            for pos, count in position_counts[driver].items():
                positions.extend([pos] * count)
            
            avg_position = sum(positions) / len(positions) if positions else 20
            avg_gain = sum(total_gains[driver]) / len(total_gains[driver]) if total_gains[driver] else 0
            
            statistics[driver] = {
                'avg_position': avg_position,
                'avg_gain': avg_gain,
                'win_probability': win_counts[driver] / iterations * 100,
                'podium_probability': sum(
                    position_counts[driver][p] for p in [1, 2, 3]
                ) / iterations * 100,
                'points_probability': sum(
                    position_counts[driver][p] for p in range(1, 11)
                ) / iterations * 100,
            }
        
        # Calculate strategy statistics
        strategy_performance = {}
        for strategy, stats in strategy_stats.items():
            if stats['positions']:
                # 計算最可能的名次（出現最多次的名次）
                from collections import Counter
                position_counts_for_strategy = Counter(stats['positions'])
                most_common_pos, most_common_count = position_counts_for_strategy.most_common(1)[0]
                most_likely_position_pct = (most_common_count / len(stats['positions'])) * 100
                
                strategy_performance[strategy] = {
                    'win_rate': stats['wins'] / iterations * 100,
                    'avg_position': sum(stats['positions']) / len(stats['positions']),
                    'best_position': min(stats['positions']),  # Best (lowest number)
                    'worst_position': max(stats['positions']),  # Worst (highest number)
                    'most_likely_position': most_common_pos,  # 最常出現的名次
                    'most_likely_position_pct': most_likely_position_pct,  # 該名次的出現百分比
                    'appearances': len(stats['positions'])
                }
        
        return {
            'iterations': iterations,
            'driver_statistics': statistics,
            'our_driver': self._our_driver,
            'our_stats': statistics.get(self._our_driver, {}),
            'strategy_performance': strategy_performance
        }
