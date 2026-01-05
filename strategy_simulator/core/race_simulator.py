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
import random
import copy

from strategy_simulator.core.lap_simulator import (
    SimulationParams, Stint, Compound, LapSimulator
)
from strategy_simulator.core.blocking_analyzer import DriverPaceInfo


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
    
    def get_current_pace(self, params: SimulationParams, sc_active: bool = False) -> float:
        """
        Calculate current lap time based on tire state and conditions.
        
        Args:
            params: Simulation parameters
            sc_active: Whether SC is active (slower pace)
            
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
        
        # Fuel effect (decreases over race)
        fuel_remaining = max(0, params.race_laps - self.tire_age)
        fuel_weight_effect = fuel_remaining * params.fuel_effect_coefficient
        
        return self.base_pace + tire_deg + fuel_weight_effect


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
    
    # Our driver's analysis
    our_driver: str = ""
    our_result: Optional[RaceResult] = None
    
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
    ):
        """
        Initialize race simulator.
        
        Args:
            sim_params: Simulation parameters (race laps, pit loss, etc.)
            sc_probability: Probability of SC per race
            vsc_probability: Probability of VSC (given an incident)
            overtaking_difficulty: Track-specific overtaking difficulty
        """
        self.sim_params = sim_params
        self.sc_probability = sc_probability
        self.vsc_probability = vsc_probability
        self.overtaking_difficulty = overtaking_difficulty
        
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
        """
        self._drivers.clear()
        
        for pred in fp2_predictions:
            driver_code = pred.get('driver', '')
            if not driver_code:
                continue
            
            position = pred.get('rank', 20)
            
            # Estimate base pace from prediction
            predicted_q_time = pred.get('predicted_time', 90.0)
            # Race pace is typically 1-2s slower than Q pace
            base_pace = predicted_q_time + 1.5
            
            # Degradation estimate (from Long Run if available)
            deg_per_lap = 0.05  # Default
            if long_run_data:
                driver_lr = long_run_data.get('driver_results', {}).get(driver_code, [])
                if driver_lr:
                    # Use first stint's degradation
                    deg_per_lap = driver_lr[0].get('degradation', 0.05)
            
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
        
    def simulate_race(self, seed: Optional[int] = None) -> FullRaceSimulation:
        """
        Simulate a complete race.
        
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
            # Gap between grid positions: ~0.5 seconds equivalent
            grid_gap = 0.5
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
        
        return result
    
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
            
            # Calculate lap time
            base_lap_time = state.get_current_pace(self.sim_params, sc_active)
            
            if is_pitting:
                # Pitting: lose time = pit_loss + traffic + random variation
                base_pit_loss = self.sim_params.pit_loss_sc if sc_active else self.sim_params.pit_loss_green
                
                # ✅ Add random pit stop variation (1.8s ~ 5.0s variation)
                # Simulate: tire gun issues, slow wheel changes, positioning errors
                pit_variation = random.uniform(-1.8, 2.0)  # Can be faster or slower
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
        if sc_active:
            print(f"[RACE_SIM] L{lap}: SC/VSC active - overtaking prohibited")
            # Skip overtaking phase, maintain current order
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
                
                # Calculate pace difference
                behind_pace = behind_state.get_current_pace(self.sim_params, sc_active)
                ahead_pace = ahead_state.get_current_pace(self.sim_params, sc_active)
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
        leader_track_pos = new_order[0][1].track_position if new_order else 0
        
        for pos, (driver_code, state) in enumerate(new_order, 1):
            old_pos = state.position
            state.position = pos
            
            # Calculate gap to leader
            gap_to_leader = leader_track_pos - state.track_position
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
    
    def _should_pit(self, driver_code: str, lap: int, sc_active: bool, is_vsc: bool = False) -> bool:
        """
        Determine if driver should pit on this lap.
        
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
        
        # Already completed all planned stops
        if state.current_stint >= len(state.stints) - 1:
            return False
        
        # Check planned pit lap
        if state.stints and state.current_stint < len(state.stints):
            current_stint = state.stints[state.current_stint]
            planned_pit_lap = current_stint.start_lap + current_stint.laps
            
            # Pit on planned lap
            if lap == planned_pit_lap:
                return True
            
            # Opportunistic pit under SC/VSC
            if sc_active:
                # Check tire condition for opportunistic pit
                tire_durability = {'SOFT': 18, 'MEDIUM': 28, 'HARD': 40}
                current_compound = state.current_tire.value if hasattr(state.current_tire, 'value') else str(state.current_tire)
                max_tire_life = tire_durability.get(current_compound.upper(), 28)
                
                # VSC: More conservative (only pit if tires are 50%+ worn or close to window)
                # Full SC: More aggressive (pit if tires are 40%+ worn or within window)
                if is_vsc:
                    # VSC 機會進站條件：
                    # 1. 在計劃窗口 ±5 圈內，或
                    # 2. 輪胎已用 50% 以上 + 還有至少 10 圈可跑
                    in_window = abs(lap - planned_pit_lap) <= 5
                    tire_worn = state.tire_age >= max_tire_life * 0.5
                    enough_laps_remaining = lap < self.sim_params.race_laps - 10
                    
                    if in_window or (tire_worn and enough_laps_remaining):
                        # 60% 機率抓住 VSC 機會（模擬車隊決策猶豫）
                        if random.random() < 0.6:
                            print(f"[RACE_SIM] {driver_code} 抓住 VSC 機會進站 (Lap {lap}, tire_age={state.tire_age})")
                            return True
                else:
                    # Full SC 機會進站條件：更激進
                    in_window = abs(lap - planned_pit_lap) <= 6
                    tire_worn = state.tire_age >= max_tire_life * 0.4
                    enough_laps_remaining = lap < self.sim_params.race_laps - 8
                    
                    # ✅ Early SC special case: If SC in first 15 laps, be more aggressive
                    is_early_sc = lap <= 15
                    if is_early_sc:
                        # Early SC: Pit if tire age > 8 laps OR within window
                        early_pit_condition = state.tire_age >= 8 or in_window
                        if early_pit_condition and enough_laps_remaining:
                            if random.random() < 0.75:  # 75% probability for early SC
                                print(f"[RACE_SIM] {driver_code} 利用 Early SC 進站 (Lap {lap}, tire_age={state.tire_age})")
                                return True
                    else:
                        # Normal SC: Use tire wear condition
                        if in_window or (tire_worn and enough_laps_remaining):
                            # 80% 機率利用 SC 進站
                            if random.random() < 0.8:
                                print(f"[RACE_SIM] {driver_code} 利用 SC 進站 (Lap {lap}, tire_age={state.tire_age})")
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
    
    def run_multiple_simulations(
        self, 
        iterations: int = 100
    ) -> Dict[str, Any]:
        """
        Run multiple race simulations for statistical analysis.
        
        Args:
            iterations: Number of simulations
            
        Returns:
            Dictionary with aggregated statistics
        """
        position_counts = defaultdict(lambda: defaultdict(int))
        total_gains = defaultdict(list)
        win_counts = defaultdict(int)
        
        for i in range(iterations):
            result = self.simulate_race(seed=i)
            
            for standing in result.final_standings:
                driver = standing.driver_code
                pos = standing.final_position
                position_counts[driver][pos] += 1
                total_gains[driver].append(standing.positions_gained)
                
                if pos == 1:
                    win_counts[driver] += 1
        
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
        
        return {
            'iterations': iterations,
            'driver_statistics': statistics,
            'our_driver': self._our_driver,
            'our_stats': statistics.get(self._our_driver, {})
        }
