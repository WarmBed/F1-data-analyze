#!/usr/bin/env python3
"""
Lap Simulator

Core lap-by-lap simulation engine for Race Strategy Simulator.
Calculates lap times considering:
- Tire degradation
- Fuel effect
- Pit stop losses

Author: F1T Team
Date: 2025-12-30
Updated: 2025-12-31 - Added trained compound delta database support
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json
from pathlib import Path


# 從訓練資料庫載入配方差異
def load_trained_compound_deltas(circuit: Optional[str] = None) -> Dict[str, float]:
    """
    Load compound deltas from trained database.
    
    Args:
        circuit: Optional circuit name (e.g., 'Yas_Marina', 'Silverstone')
                 If None, returns global averages
    
    Returns:
        Dict with compound deltas: {'SOFT': float, 'MEDIUM': 0.0, 'HARD': float}
        
    Note:
        2025-12-31 更新：
        - SOFT 訓練結果 (-0.2s) 較合理，直接使用
        - HARD 訓練結果有系統性偏差（因為 HARD 在比賽後期使用，
          享受更多燃油+賽道演化效應），需要應用物理修正
        - 物理預期：HARD 比 MEDIUM 慢約 0.3-0.5s
    """
    # Default values based on physics/Pirelli data
    default_deltas = {
        'SOFT': -0.4,    # SOFT faster than MEDIUM (Pirelli ~0.5-0.8s)
        'MEDIUM': 0.0,
        'HARD': 0.4,     # HARD slower than MEDIUM (Pirelli ~0.3-0.5s)
    }
    
    try:
        # Find the database file
        db_path = Path(__file__).parent.parent.parent / 'config' / 'compound_delta_database.json'
        if not db_path.exists():
            # Try alternative path
            db_path = Path('config/compound_delta_database.json')
        
        if not db_path.exists():
            return default_deltas
            
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 1. 嘗試使用賽道特定參數（僅用於 SOFT）
        soft_delta = default_deltas['SOFT']
        if circuit:
            circuit_key = circuit.replace(' ', '_')
            if circuit_key in data.get('circuits', {}):
                circuit_data = data['circuits'][circuit_key]
                if 'compound_deltas' in circuit_data:
                    circuit_deltas = circuit_data['compound_deltas']
                    # 只用訓練的 SOFT 值（如果是負值）
                    trained_soft = circuit_deltas.get('SOFT', soft_delta)
                    if trained_soft < 0:
                        soft_delta = trained_soft
        
        # 2. 使用全局平均值作為 fallback
        global_avgs = data.get('global_averages', {})
        
        # SOFT: 使用訓練結果（如果是負值）
        trained_soft = global_avgs.get('SOFT_vs_MEDIUM', {}).get('median', default_deltas['SOFT'])
        if trained_soft < 0:
            soft_delta = trained_soft
        
        # HARD: 使用物理經驗值，因為訓練數據有系統性偏差
        # 訓練結果 (-0.255s) 是錯誤的（HARD 在後期使用，享受燃油+賽道效應）
        # 物理預期：HARD 比 MEDIUM 慢約 0.3-0.5s
        hard_delta = 0.4  # 固定使用物理經驗值
        
        return {
            'SOFT': soft_delta,
            'MEDIUM': 0.0,
            'HARD': hard_delta,
        }
        
    except Exception:
        return default_deltas


class Compound(Enum):
    """Tire compound types"""
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    
    @classmethod
    def from_string(cls, s: str) -> 'Compound':
        """Convert string to Compound enum."""
        return cls(s.upper())
    
    def short_name(self) -> str:
        """Get single-letter abbreviation."""
        return self.value[0]  # S, M, H


@dataclass
class Stint:
    """A single stint (period between pit stops)"""
    compound: Compound
    laps: int
    start_lap: int = 1
    
    @property
    def end_lap(self) -> int:
        return self.start_lap + self.laps - 1
    
    def __repr__(self) -> str:
        return f"{self.compound.short_name()}({self.laps})"


@dataclass
class SimulationParams:
    """Parameters for race simulation"""
    # Race info
    race_laps: int = 53
    base_lap_time: float = 91.5  # seconds (fastest possible with new tires, full fuel)
    
    # First lap / traffic simulation options
    enable_first_lap_loss: bool = False  # Enable first lap time penalty
    first_lap_loss: float = 5.0  # Additional seconds for lap 1 (formation, start chaos)
    
    enable_traffic_simulation: bool = False  # Enable position-based traffic
    starting_position: int = 10  # Grid position (1-20)
    traffic_loss_per_position: float = 0.15  # seconds per position behind leader
    traffic_decay_rate: float = 0.05  # Traffic effect reduces by this factor per lap
    
    # DRS parameters (Q17 Enhancement)
    enable_drs: bool = False  # Enable DRS effect simulation
    drs_zones: int = 2  # Number of DRS zones on track
    drs_gain_per_zone: float = 0.15  # Lap time gain per DRS zone (seconds)
    drs_detection_gap: float = 1.0  # Gap threshold for DRS activation (seconds)
    
    # Lapping parameters (Q17 Enhancement)
    enable_lapping: bool = False  # Enable lapping (blue flag) effect
    lapping_loss_per_car: float = 0.3  # Time lost per lapped car (seconds)
    lapping_threshold_position: int = 3  # Only affects top N positions
    
    # Fuel parameters
    start_fuel_kg: float = 110.0
    fuel_kg_per_lap: float = 1.70
    fuel_effect_coefficient: float = 0.030  # seconds per kg
    
    # Degradation rates (seconds per lap) - base rate
    deg_rates: Dict[Compound, float] = field(default_factory=lambda: {
        Compound.SOFT: 0.120,
        Compound.MEDIUM: 0.080,
        Compound.HARD: 0.045,
    })
    
    # Degradation acceleration (seconds per lap^2) - time-varying model
    # degradation(t) = base_rate + acceleration * tire_age
    deg_acceleration: Dict[Compound, float] = field(default_factory=lambda: {
        Compound.SOFT: 0.003,
        Compound.MEDIUM: 0.002,
        Compound.HARD: 0.001,
    })
    
    # Pit loss
    pit_loss_green: float = 24.0
    pit_loss_sc: float = 12.0
    pit_loss_vsc: float = 9.0
    
    # Pit lane congestion parameters (Q17)
    enable_pit_congestion: bool = False  # Enable pit lane congestion simulation
    pit_congestion_penalty: float = 2.0  # Additional seconds per car ahead in pit lane
    
    # Compound base time deltas (relative to MEDIUM)
    # Updated 2025-12-31: Now uses trained values from real race data
    # Old hardcoded: SOFT=-0.8, HARD=+0.5
    # New trained: SOFT=-0.20, HARD=+0.15 (conservative estimate)
    compound_deltas: Dict[Compound, float] = field(default_factory=lambda: {
        Compound.SOFT: -0.20,   # Trained: -0.202s (was -0.8s - too aggressive)
        Compound.MEDIUM: 0.0,   # baseline
        Compound.HARD: 0.15,    # Conservative estimate (trained showed bias)
    })
    
    # Circuit name for loading circuit-specific parameters
    circuit: Optional[str] = None
    
    def __post_init__(self):
        """Load circuit-specific compound deltas if circuit is specified."""
        if self.circuit:
            trained_deltas = load_trained_compound_deltas(self.circuit)
            self.compound_deltas = {
                Compound.SOFT: trained_deltas.get('SOFT', -0.20),
                Compound.MEDIUM: 0.0,
                Compound.HARD: trained_deltas.get('HARD', 0.15),
            }
    
    def get_deg_rate(self, compound: Compound) -> float:
        """Get degradation rate for a compound."""
        return self.deg_rates.get(compound, 0.080)
    
    def get_deg_acceleration(self, compound: Compound) -> float:
        """Get degradation acceleration for a compound."""
        return self.deg_acceleration.get(compound, 0.002)
    
    def get_compound_delta(self, compound: Compound) -> float:
        """Get base time delta for a compound."""
        return self.compound_deltas.get(compound, 0.0)
    
    def fuel_at_lap(self, lap: int) -> float:
        """Calculate remaining fuel at a given lap."""
        consumed = (lap - 1) * self.fuel_kg_per_lap
        return max(0, self.start_fuel_kg - consumed)


@dataclass
class LapResult:
    """Result for a single lap simulation"""
    lap_number: int
    compound: Compound
    tyre_age: int
    fuel_remaining: float
    
    # Time components
    base_time: float
    compound_delta: float
    fuel_adjustment: float  # negative = lighter = faster
    degradation: float
    first_lap_loss: float = 0.0  # Additional time for lap 1
    traffic_loss: float = 0.0  # Position-based traffic loss
    drs_gain: float = 0.0  # DRS lap time gain (negative = faster)
    lapping_loss: float = 0.0  # Time lost overtaking lapped cars
    
    @property
    def net_time(self) -> float:
        """Calculate net lap time."""
        return (self.base_time + self.compound_delta + self.fuel_adjustment + 
                self.degradation + self.first_lap_loss + self.traffic_loss + 
                self.drs_gain + self.lapping_loss)
    
    def to_dict(self) -> dict:
        return {
            'lap': self.lap_number,
            'compound': self.compound.value,
            'tyre_age': self.tyre_age,
            'fuel_kg': round(self.fuel_remaining, 1),
            'base_time': round(self.base_time, 3),
            'compound_delta': round(self.compound_delta, 3),
            'fuel_adj': round(self.fuel_adjustment, 3),
            'deg': round(self.degradation, 3),
            'first_lap_loss': round(self.first_lap_loss, 3),
            'traffic_loss': round(self.traffic_loss, 3),
            'drs_gain': round(self.drs_gain, 3),
            'lapping_loss': round(self.lapping_loss, 3),
            'net_time': round(self.net_time, 3),
        }


@dataclass
class StrategySimulationResult:
    """Complete simulation result for a strategy"""
    strategy_name: str
    stints: List[Stint]
    lap_results: List[LapResult] = field(default_factory=list)
    pit_laps: List[int] = field(default_factory=list)
    total_pit_loss: float = 0.0
    
    @property
    def total_time(self) -> float:
        """Calculate total race time in seconds."""
        lap_time = sum(r.net_time for r in self.lap_results)
        return lap_time + self.total_pit_loss
    
    @property
    def total_time_formatted(self) -> str:
        """Format total time as H:MM:SS.mmm"""
        total = self.total_time
        hours = int(total // 3600)
        minutes = int((total % 3600) // 60)
        seconds = total % 60
        return f"{hours}:{minutes:02d}:{seconds:06.3f}"
    
    @property
    def num_stops(self) -> int:
        """Number of pit stops."""
        return len(self.stints) - 1
    
    def get_stint_notation(self) -> str:
        """Get strategy notation like 'M→H' or 'S→M→H'"""
        return "→".join(s.compound.short_name() for s in self.stints)
    
    def to_dict(self) -> dict:
        return {
            'name': self.strategy_name,
            'notation': self.get_stint_notation(),
            'stops': self.num_stops,
            'total_time': self.total_time,
            'total_time_formatted': self.total_time_formatted,
            'total_pit_loss': self.total_pit_loss,
            'pit_laps': self.pit_laps,
            'stints': [{'compound': s.compound.value, 'laps': s.laps, 
                       'start': s.start_lap, 'end': s.end_lap} for s in self.stints],
        }


class LapSimulator:
    """
    Lap-by-lap race simulation engine.
    
    Usage:
        params = SimulationParams(race_laps=53, ...)
        simulator = LapSimulator(params)
        
        strategy = [Stint(Compound.MEDIUM, 22), Stint(Compound.HARD, 31)]
        result = simulator.simulate_strategy(strategy)
        
        print(result.total_time_formatted)  # "1:32:45.234"
    """
    
    def __init__(self, params: SimulationParams):
        """
        Initialize LapSimulator.
        
        Args:
            params: Simulation parameters
        """
        self.params = params
    
    def calculate_lap_time(
        self,
        lap_number: int,
        compound: Compound,
        tyre_age: int,
        fuel_remaining: float,
        gap_to_ahead: float = None,
        lapped_cars_count: int = 0
    ) -> LapResult:
        """
        Calculate lap time for given conditions.
        
        Uses time-varying linear degradation model from Cappello & Hoegh 2025:
        degradation(t) = base_rate * t + 0.5 * acceleration * t^2
        
        Args:
            lap_number: Current lap number (1-based)
            compound: Tire compound
            tyre_age: How many laps on current tires
            fuel_remaining: Remaining fuel in kg
        
        Returns:
            LapResult with all time components
        """
        # Base time
        base_time = self.params.base_lap_time
        
        # Compound delta (SOFT faster, HARD slower)
        compound_delta = self.params.get_compound_delta(compound)
        
        # Fuel adjustment (lighter = faster)
        fuel_consumed = self.params.start_fuel_kg - fuel_remaining
        fuel_adjustment = -fuel_consumed * self.params.fuel_effect_coefficient
        
        # Time-varying degradation model:
        # The degradation effect on lap time increases as tires wear.
        # 
        # Model: Each lap, the tires are slower than new tires by an amount
        # that depends on tire age (tyre_age).
        # 
        # For a tire on its t-th lap (tyre_age = t):
        # - Marginal degradation rate = base_rate + accel * (t - 1)
        # - This is how much SLOWER this lap is compared to the previous lap
        #
        # Total lap time penalty (compared to new tires) after t laps:
        # = sum from i=1 to t of (base_rate + accel * (i - 1))
        # = base_rate * t + accel * (0 + 1 + ... + (t-1))
        # = base_rate * t + accel * t * (t - 1) / 2
        #
        # However, this formula calculates CUMULATIVE degradation from lap 1.
        # What we need for lap time calculation is the MARGINAL penalty for THIS lap:
        # 
        # Lap time = base_time + compound_delta + fuel_adj + deg_penalty
        # where deg_penalty = how much slower this lap is compared to a fresh tire
        # 
        # For a tire on lap t (tyre_age = t, meaning it has run t laps including this one):
        # deg_penalty = base_rate * (t - 1) + 0.5 * accel * (t - 1) * (t - 2)  for t >= 1
        # 
        # Simplified: On lap 1 (new tire), penalty = 0
        #             On lap 2, penalty = base_rate
        #             On lap 3, penalty = 2 * base_rate + accel
        #             etc.
        
        deg_rate = self.params.get_deg_rate(compound)
        deg_accel = self.params.get_deg_acceleration(compound)
        
        # Lap time penalty compared to new tires
        # tyre_age = 1 means first lap on this tire → penalty = 0
        # tyre_age = 2 means second lap → penalty = deg_rate
        # etc.
        if tyre_age <= 1:
            degradation = 0.0
        else:
            t = tyre_age - 1  # laps completed on this tire before this lap
            degradation = deg_rate * t + 0.5 * deg_accel * t * (t - 1)
        
        # First lap loss (formation lap, start chaos, dirty air on lap 1)
        first_lap_loss = 0.0
        if self.params.enable_first_lap_loss and lap_number == 1:
            first_lap_loss = self.params.first_lap_loss
        
        # Traffic loss (position-based, decays over time)
        traffic_loss = 0.0
        if self.params.enable_traffic_simulation:
            # Traffic effect based on starting position (P1 = 0 loss, P20 = max loss)
            position = self.params.starting_position
            base_traffic = (position - 1) * self.params.traffic_loss_per_position
            # Decay exponentially over laps
            decay = max(0, 1 - self.params.traffic_decay_rate * (lap_number - 1))
            traffic_loss = base_traffic * decay
        
        # DRS gain (negative time = faster lap)
        drs_gain = 0.0
        if self.params.enable_drs and gap_to_ahead is not None:
            # DRS available if:
            # 1. Not first 3 laps (safety car restriction)
            # 2. Within detection gap (default 1.0s) of car ahead
            if lap_number > 3 and gap_to_ahead < self.params.drs_detection_gap:
                # Multiple DRS zones multiply the benefit
                drs_gain = -self.params.drs_zones * self.params.drs_gain_per_zone
        
        # Lapping loss (front runners losing time lapping backmarkers)
        lapping_loss = 0.0
        if self.params.enable_lapping and lapped_cars_count > 0:
            # Only leaders experience lapping loss
            if self.params.starting_position <= self.params.lapping_threshold_position:
                lapping_loss = lapped_cars_count * self.params.lapping_loss_per_car
        
        return LapResult(
            lap_number=lap_number,
            compound=compound,
            tyre_age=tyre_age,
            fuel_remaining=fuel_remaining,
            base_time=base_time,
            compound_delta=compound_delta,
            fuel_adjustment=fuel_adjustment,
            degradation=degradation,
            first_lap_loss=first_lap_loss,
            traffic_loss=traffic_loss,
            drs_gain=drs_gain,
            lapping_loss=lapping_loss,
        )
    
    def simulate_strategy(
        self,
        stints: List[Stint],
        name: str = None,
        pit_loss_type: str = "green",
        opponent_pit_laps: Dict[str, List[int]] = None
    ) -> StrategySimulationResult:
        """
        Simulate a complete race with given strategy.
        
        Args:
            stints: List of Stint objects defining the strategy
            name: Optional strategy name
            pit_loss_type: "green", "sc", or "vsc" for pit loss calculation
            opponent_pit_laps: Dict mapping driver code to their pit laps (for congestion)
        
        Returns:
            StrategySimulationResult with complete simulation data
        """
        if not stints:
            raise ValueError("Strategy must have at least one stint")
        
        # Calculate total laps in strategy
        total_stint_laps = sum(s.laps for s in stints)
        if total_stint_laps != self.params.race_laps:
            # Adjust last stint to match race laps
            diff = self.params.race_laps - total_stint_laps
            stints[-1] = Stint(
                compound=stints[-1].compound,
                laps=stints[-1].laps + diff,
                start_lap=stints[-1].start_lap
            )
        
        # Select pit loss
        if pit_loss_type == "sc":
            pit_loss = self.params.pit_loss_sc
        elif pit_loss_type == "vsc":
            pit_loss = self.params.pit_loss_vsc
        else:
            pit_loss = self.params.pit_loss_green
        
        # Simulate each lap
        lap_results: List[LapResult] = []
        pit_laps: List[int] = []
        current_lap = 1
        
        for stint_idx, stint in enumerate(stints):
            stint.start_lap = current_lap
            
            for lap_in_stint in range(stint.laps):
                # Calculate fuel remaining
                fuel = self.params.fuel_at_lap(current_lap)
                
                # Tyre age (1-based)
                tyre_age = lap_in_stint + 1
                
                # Calculate lap time
                result = self.calculate_lap_time(
                    lap_number=current_lap,
                    compound=stint.compound,
                    tyre_age=tyre_age,
                    fuel_remaining=fuel
                )
                lap_results.append(result)
                current_lap += 1
            
            # Record pit lap (except for last stint)
            if stint_idx < len(stints) - 1:
                pit_laps.append(current_lap - 1)
        
        # Calculate total pit loss (with optional congestion)
        total_pit_loss = self._calculate_pit_loss(pit_laps, pit_loss, opponent_pit_laps)
        
        # Generate name if not provided
        if name is None:
            name = f"Plan {'ABCDEFGHIJ'[0]}"  # Will be set by optimizer
        
        return StrategySimulationResult(
            strategy_name=name,
            stints=stints,
            lap_results=lap_results,
            pit_laps=pit_laps,
            total_pit_loss=total_pit_loss,
        )
    
    def _calculate_pit_loss(self, pit_laps: List[int], base_pit_loss: float,
                            opponent_pit_laps: Dict[str, List[int]] = None) -> float:
        """
        Calculate total pit loss including optional congestion penalty.
        
        Q17: Pit lane congestion - adds penalty when multiple cars pit on same lap.
        
        Args:
            pit_laps: List of laps where this strategy pits
            base_pit_loss: Base pit stop time loss
            opponent_pit_laps: Dict mapping driver code to their pit laps
            
        Returns:
            Total pit loss time in seconds
        """
        if not pit_laps:
            return 0.0
        
        total_loss = 0.0
        
        for pit_lap in pit_laps:
            # Base pit loss
            lap_loss = base_pit_loss
            
            # Add congestion penalty if enabled
            if self.params.enable_pit_congestion and opponent_pit_laps:
                # Count cars pitting within +/-1 lap window
                cars_in_window = 0
                for driver, opp_pits in opponent_pit_laps.items():
                    for opp_pit in opp_pits:
                        if abs(pit_lap - opp_pit) <= 1:
                            cars_in_window += 1
                            break  # Count each driver only once
                
                # Apply congestion penalty
                if cars_in_window > 0:
                    congestion_penalty = cars_in_window * self.params.pit_congestion_penalty
                    lap_loss += congestion_penalty
            
            total_loss += lap_loss
        
        return total_loss
    
    def simulate_strategy_with_sc(
        self,
        stints: List[Stint],
        sc_lap: int,
        sc_duration: int,
        is_vsc: bool = False,
        name: str = None,
    ) -> StrategySimulationResult:
        """
        Simulate a strategy with SC/VSC at specified lap.
        
        Pit stops during SC window use reduced pit loss.
        
        Args:
            stints: List of Stint objects defining the strategy
            sc_lap: Lap when SC/VSC appears
            sc_duration: How many laps SC lasts
            is_vsc: True for VSC, False for full SC
            name: Optional strategy name
        
        Returns:
            StrategySimulationResult with SC-adjusted times
        """
        if not stints:
            raise ValueError("Strategy must have at least one stint")
        
        # SC window: from sc_lap to sc_lap + sc_duration - 1
        sc_start = sc_lap
        sc_end = sc_lap + sc_duration - 1
        
        # SC pit loss
        pit_loss_sc = self.params.pit_loss_vsc if is_vsc else self.params.pit_loss_sc
        pit_loss_green = self.params.pit_loss_green
        
        # Adjust last stint to match race laps
        total_stint_laps = sum(s.laps for s in stints)
        if total_stint_laps != self.params.race_laps:
            diff = self.params.race_laps - total_stint_laps
            stints[-1] = Stint(
                compound=stints[-1].compound,
                laps=stints[-1].laps + diff,
                start_lap=stints[-1].start_lap
            )
        
        # Simulate each lap
        lap_results: List[LapResult] = []
        pit_laps: List[int] = []
        current_lap = 1
        
        for stint_idx, stint in enumerate(stints):
            stint.start_lap = current_lap
            
            for lap_in_stint in range(stint.laps):
                fuel = self.params.fuel_at_lap(current_lap)
                tyre_age = lap_in_stint + 1
                
                result = self.calculate_lap_time(
                    lap_number=current_lap,
                    compound=stint.compound,
                    tyre_age=tyre_age,
                    fuel_remaining=fuel
                )
                lap_results.append(result)
                current_lap += 1
            
            # Record pit lap (except for last stint)
            if stint_idx < len(stints) - 1:
                pit_laps.append(current_lap - 1)
        
        # Calculate total pit loss - check if each pit is in SC window
        total_pit_loss = 0.0
        pit_in_sc_count = 0
        pit_not_in_sc_count = 0
        
        for pit_lap in pit_laps:
            if sc_start <= pit_lap <= sc_end:
                total_pit_loss += pit_loss_sc
                pit_in_sc_count += 1
            else:
                total_pit_loss += pit_loss_green
                pit_not_in_sc_count += 1
        
        if name is None:
            name = "Plan A"
        
        result = StrategySimulationResult(
            strategy_name=name,
            stints=stints,
            lap_results=lap_results,
            pit_laps=pit_laps,
            total_pit_loss=total_pit_loss,
        )
        
        # Add SC analysis metadata
        result.sc_pits = pit_in_sc_count
        result.green_pits = pit_not_in_sc_count
        
        return result
    
    def simulate_multiple(
        self,
        strategies: List[List[Stint]],
        names: List[str] = None
    ) -> List[StrategySimulationResult]:
        """
        Simulate multiple strategies.
        
        Args:
            strategies: List of stint lists
            names: Optional list of strategy names
        
        Returns:
            List of simulation results, sorted by total time
        """
        if names is None:
            names = [f"Plan {chr(65+i)}" for i in range(len(strategies))]
        
        results = []
        for i, stints in enumerate(strategies):
            name = names[i] if i < len(names) else f"Plan {chr(65+i)}"
            result = self.simulate_strategy(stints, name=name)
            results.append(result)
        
        # Sort by total time
        results.sort(key=lambda r: r.total_time)
        
        # Rename based on ranking
        for i, result in enumerate(results):
            result.strategy_name = f"Plan {chr(65+i)}"
        
        return results


__all__ = ['Compound', 'Stint', 'SimulationParams', 'LapResult', 
           'StrategySimulationResult', 'LapSimulator']
