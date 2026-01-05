#!/usr/bin/env python3
"""
Opponent Strategy Predictor

Predicts opponent pit stop timing and strategy based on:
- FP2 Long Run data
- Tire degradation rates
- Race parameters

Author: F1T Team
Date: 2025-12-31
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class TireCompound(Enum):
    """Tire compound types."""
    SOFT = "S"
    MEDIUM = "M"
    HARD = "H"


@dataclass
class OpponentStrategy:
    """
    Opponent strategy prediction.
    
    Attributes:
        driver_code: 3-letter driver code (e.g., "VER")
        team: Team name
        starting_position: Grid position
        num_stops: Number of pit stops (1, 2, or 3)
        tire_sequence: List of tire compounds ["S", "M", "H"]
        pit_laps: Predicted pit stop laps
        is_custom: True if manually overridden, False if auto-predicted
    """
    driver_code: str
    team: str = ""
    starting_position: int = 0
    num_stops: int = 1
    tire_sequence: List[str] = field(default_factory=lambda: ["M", "H"])
    pit_laps: List[int] = field(default_factory=list)
    is_custom: bool = False
    
    def get_notation(self) -> str:
        """Get strategy notation like 'S-M' or 'S-M-H'."""
        return "-".join(self.tire_sequence)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "driver_code": self.driver_code,
            "team": self.team,
            "starting_position": self.starting_position,
            "num_stops": self.num_stops,
            "tire_sequence": self.tire_sequence,
            "pit_laps": self.pit_laps,
            "is_custom": self.is_custom,
        }


@dataclass
class GlobalStrategySettings:
    """
    Global default settings for opponent strategies.
    """
    default_num_stops: int = 1
    default_tire_sequence: List[str] = field(default_factory=lambda: ["M", "H"])
    use_fp2_prediction: bool = True
    
    # Tire life estimates (laps)
    soft_life: int = 18
    medium_life: int = 28
    hard_life: int = 40


class OpponentStrategyPredictor:
    """
    Predicts opponent pit strategies for blocking analysis.
    
    Uses FP2 Long Run data and tire degradation rates to estimate
    when each opponent will pit and what tires they will use.
    """
    
    def __init__(self):
        self._global_settings = GlobalStrategySettings()
        self._opponent_strategies: Dict[str, OpponentStrategy] = {}
        self._race_laps: int = 53
        self._fp2_predictions: List[Dict] = []
        
    def set_race_laps(self, laps: int):
        """Set total race laps."""
        self._race_laps = laps
        
    def set_global_settings(self, settings: GlobalStrategySettings):
        """Set global default strategy settings."""
        self._global_settings = settings
        
    def load_fp2_predictions(self, predictions: List[Dict]):
        """
        Load FP2->Q predictions for all drivers.
        
        Args:
            predictions: List of prediction dicts with driver, rank, team, etc.
        """
        self._fp2_predictions = predictions
        
        # Initialize strategies for all drivers
        for pred in predictions:
            driver = pred.get("driver", "")
            if driver and driver not in self._opponent_strategies:
                self._opponent_strategies[driver] = OpponentStrategy(
                    driver_code=driver,
                    team=pred.get("team", ""),
                    starting_position=pred.get("rank", 20),
                )
                
    def set_custom_strategy(self, driver_code: str, num_stops: int, 
                           tire_sequence: List[str], pit_laps: Optional[List[int]] = None):
        """
        Set a custom strategy for a specific driver.
        
        Args:
            driver_code: 3-letter driver code
            num_stops: Number of pit stops
            tire_sequence: List of tire compounds
            pit_laps: Optional specific pit laps (auto-calculated if None)
        """
        if driver_code not in self._opponent_strategies:
            self._opponent_strategies[driver_code] = OpponentStrategy(driver_code=driver_code)
            
        strategy = self._opponent_strategies[driver_code]
        strategy.num_stops = num_stops
        strategy.tire_sequence = tire_sequence
        strategy.is_custom = True
        
        if pit_laps:
            strategy.pit_laps = pit_laps
        else:
            strategy.pit_laps = self._calculate_pit_laps(
                num_stops, tire_sequence, strategy.starting_position
            )
            
    def reset_to_default(self, driver_code: str):
        """Reset a driver's strategy to use global defaults."""
        if driver_code in self._opponent_strategies:
            strategy = self._opponent_strategies[driver_code]
            strategy.num_stops = self._global_settings.default_num_stops
            strategy.tire_sequence = self._global_settings.default_tire_sequence.copy()
            strategy.is_custom = False
            strategy.pit_laps = self._calculate_pit_laps(
                strategy.num_stops, strategy.tire_sequence, strategy.starting_position
            )
            
    def predict_all_strategies(self):
        """
        Predict/calculate pit laps for all opponents based on settings.
        """
        for driver_code, strategy in self._opponent_strategies.items():
            if not strategy.is_custom:
                # Use global defaults
                strategy.num_stops = self._global_settings.default_num_stops
                strategy.tire_sequence = self._global_settings.default_tire_sequence.copy()
                
            # Calculate pit laps
            strategy.pit_laps = self._calculate_pit_laps(
                strategy.num_stops, strategy.tire_sequence, strategy.starting_position
            )
            
    def _calculate_pit_laps(self, num_stops: int, tire_sequence: List[str], 
                           starting_position: int = 10) -> List[int]:
        """
        Calculate optimal pit stop laps based on tire strategy.
        
        Uses tire life estimates to determine when each stint should end.
        Adds randomization to simulate realistic strategy variations:
        - Different teams have different risk appetites
        - Track position considerations (front runners vs midfield vs backmarkers)
        - Undercut/overcut opportunities
        
        Real F1 teams typically vary pit timing by ±3-5 laps from the "optimal" window.
        
        Args:
            num_stops: Number of pit stops
            tire_sequence: List of tire compounds
            starting_position: Grid position (1-20) - affects pit strategy aggressiveness
        """
        import random
        
        if num_stops == 0:
            return []
            
        pit_laps = []
        current_lap = 1
        
        for i in range(num_stops):
            tire = tire_sequence[i] if i < len(tire_sequence) else "M"
            
            # Get tire life
            if tire == "S":
                tire_life = self._global_settings.soft_life
            elif tire == "H":
                tire_life = self._global_settings.hard_life
            else:  # Medium
                tire_life = self._global_settings.medium_life
                
            # Calculate stint length
            remaining_laps = self._race_laps - current_lap + 1
            remaining_stops = num_stops - i
            
            if remaining_stops == 1:
                # Last pit stop - use remaining laps divided roughly
                stint_length = min(tire_life, remaining_laps // 2)
            else:
                # Not last stop - use tire life as guideline
                stint_length = min(tire_life, remaining_laps // (remaining_stops + 1))
            
            # ✅ 真實化改進：基於位置的進站策略差異
            # 前排車手（P1-P5）：保守策略，傾向較晚進站（保護賽道位置）
            # 中游車手（P6-P12）：平衡策略，正常窗口進站
            # 後排車手（P13-P20）：激進策略，傾向較早進站（嘗試 undercut）
            
            if starting_position <= 5:
                # 前排：傾向延遲進站 +1 到 +3 圈（保護位置）
                position_bias = random.randint(1, 3)
                randomization_window = 3  # 較小的隨機範圍（更保守）
            elif starting_position <= 12:
                # 中游：平衡策略，正常隨機化
                position_bias = random.randint(-2, 2)
                randomization_window = 4  # 標準隨機範圍
            else:
                # 後排：傾向提前進站 -3 到 -1 圈（激進 undercut）
                position_bias = random.randint(-3, -1)
                randomization_window = 5  # 較大的隨機範圍（更激進）
            
            # 加入隨機化模擬不同車隊的策略風格
            team_randomization = random.randint(-randomization_window, randomization_window)
            
            # 總調整 = 位置偏差 + 車隊隨機化
            total_adjustment = position_bias + team_randomization
            
            # 確保進站圈數合理（不能太早或太晚）
            min_stint = max(8, tire_life // 3)  # 最短單段至少 8 圈
            max_stint = min(tire_life, remaining_laps - remaining_stops)  # 最長不超過輪胎壽命
            
            stint_length = max(min_stint, min(max_stint, stint_length + total_adjustment))
                
            pit_lap = current_lap + stint_length
            pit_laps.append(pit_lap)
            current_lap = pit_lap + 1
            
        return pit_laps
    
    def get_strategy(self, driver_code: str) -> Optional[OpponentStrategy]:
        """Get strategy for a specific driver."""
        return self._opponent_strategies.get(driver_code)
    
    def get_all_strategies(self) -> Dict[str, OpponentStrategy]:
        """Get all opponent strategies."""
        return self._opponent_strategies.copy()
    
    def predict_all_opponents(self, driver_settings: Dict[str, Dict]) -> Dict[str, OpponentStrategy]:
        """
        Predict strategies for all opponents based on provided settings.
        
        This is the main entry point for the GUI to get opponent predictions.
        
        Args:
            driver_settings: Dict mapping driver code to settings dict:
                {
                    'VER': {'num_stops': 1, 'tire_sequence': ['M', 'H'], 'use_global': False},
                    'LEC': {'use_global': True},
                    ...
                }
                
        Returns:
            Dict mapping driver code to OpponentStrategy
        """
        for driver_code, settings in driver_settings.items():
            if settings.get('use_global', True):
                # Use global settings
                if driver_code not in self._opponent_strategies:
                    self._opponent_strategies[driver_code] = OpponentStrategy(driver_code=driver_code)
                    
                strategy = self._opponent_strategies[driver_code]
                strategy.num_stops = self._global_settings.default_num_stops
                strategy.tire_sequence = self._global_settings.default_tire_sequence.copy()
                strategy.is_custom = False
            else:
                # Use custom settings
                num_stops = settings.get('num_stops', 1)
                tire_sequence = settings.get('tire_sequence', ['M', 'H'])
                
                if driver_code not in self._opponent_strategies:
                    self._opponent_strategies[driver_code] = OpponentStrategy(driver_code=driver_code)
                    
                strategy = self._opponent_strategies[driver_code]
                strategy.num_stops = num_stops
                strategy.tire_sequence = tire_sequence
                strategy.is_custom = True
                
            # Calculate pit laps for all
            strategy.pit_laps = self._calculate_pit_laps(
                strategy.num_stops, strategy.tire_sequence, strategy.starting_position
            )
                
        return self._opponent_strategies.copy()
    
    def get_drivers_pitting_on_lap(self, lap: int, window: int = 2) -> List[str]:
        """
        Get list of drivers expected to pit on or near a specific lap.
        
        Args:
            lap: The lap to check
            window: Number of laps +/- to consider (default: 2)
            
        Returns:
            List of driver codes expected to pit in that window
        """
        drivers = []
        for driver_code, strategy in self._opponent_strategies.items():
            for pit_lap in strategy.pit_laps:
                if abs(pit_lap - lap) <= window:
                    drivers.append(driver_code)
                    break
        return drivers
    
    def analyze_blocking_on_exit(self, our_driver: str, our_pit_lap: int, 
                                  our_position: int) -> Dict:
        """
        Analyze which drivers might block us when we exit the pits.
        
        Args:
            our_driver: Our driver code
            our_pit_lap: The lap we are pitting
            our_position: Our current race position
            
        Returns:
            Dict with blocking analysis:
            - drivers_blocking: List of drivers who might block
            - position_after_stop: Predicted position after pit exit
            - time_lost_estimate: Estimated time lost to traffic
        """
        drivers_blocking = []
        
        for driver_code, strategy in self._opponent_strategies.items():
            if driver_code == our_driver:
                continue
                
            # Check if this driver is NOT pitting around the same time
            # and will be ahead of us on track
            is_pitting_same_time = any(
                abs(pit_lap - our_pit_lap) <= 1 
                for pit_lap in strategy.pit_laps
            )
            
            if not is_pitting_same_time:
                # They're staying out - might block us
                if strategy.starting_position < our_position + 5:  # Roughly near us
                    drivers_blocking.append({
                        "driver": driver_code,
                        "position": strategy.starting_position,
                        "tire": strategy.tire_sequence[0] if strategy.tire_sequence else "M",
                        "next_pit": strategy.pit_laps[0] if strategy.pit_laps else None,
                    })
                    
        # Sort by position
        drivers_blocking.sort(key=lambda x: x["position"])
        
        # Estimate position after stop
        # Rough estimate: lose ~3 positions per pit stop if traffic
        position_after = our_position + len(drivers_blocking) // 2
        
        # Estimate time loss (rough: 0.5s per driver in dirty air)
        time_lost = len(drivers_blocking) * 0.5
        
        return {
            "drivers_blocking": drivers_blocking,
            "position_after_stop": min(position_after, 20),
            "time_lost_estimate": time_lost,
            "pit_lap": our_pit_lap,
        }
    
    def auto_assign_strategies_by_position(
        self,
        fp2_predictions: List[Dict],
        race_laps: int,
        track_type: str = "normal",
        tire_deg_level: str = "medium"
    ) -> Dict[str, OpponentStrategy]:
        """
        Automatically assign suitable strategies to each driver based on:
        - Grid position (front = aggressive, back = conservative)
        - Track type (high deg = more stops, low deg = fewer stops)
        - Tire degradation level
        
        Args:
            fp2_predictions: FP2->Q predictions list with driver, rank, team
            race_laps: Total race laps
            track_type: "high_deg" (e.g., Barcelona), "normal", "low_deg" (e.g., Monaco)
            tire_deg_level: "high", "medium", "low"
            
        Returns:
            Dict mapping driver_code to OpponentStrategy with auto-assigned strategies
        """
        self._race_laps = race_laps
        self._fp2_predictions = fp2_predictions
        
        # Define strategy templates based on track type
        strategy_templates = self._get_strategy_templates(track_type, tire_deg_level, race_laps)
        
        print(f"[STRATEGY_PREDICTOR] Auto-assigning strategies for {len(fp2_predictions)} drivers")
        print(f"[STRATEGY_PREDICTOR] Track type: {track_type}, Tire deg: {tire_deg_level}")
        
        for pred in fp2_predictions:
            driver = pred.get("driver", "")
            if not driver:
                continue
            
            rank = pred.get("rank", 20)
            team = pred.get("team", "")
            
            # Select strategy based on position
            tire_seq = self._select_strategy_for_position(rank, strategy_templates, team)
            
            strategy = OpponentStrategy(
                driver_code=driver,
                team=team,
                starting_position=rank,
                num_stops=len(tire_seq) - 1,
                tire_sequence=tire_seq,
                is_custom=False,
            )
            
            # Calculate pit laps
            strategy.pit_laps = self._calculate_pit_laps(
                strategy.num_stops, strategy.tire_sequence, strategy.starting_position
            )
            
            self._opponent_strategies[driver] = strategy
            
            print(f"[STRATEGY_PREDICTOR] P{rank:2d} {driver}: {strategy.get_notation()} "
                  f"(pits: {strategy.pit_laps})")
        
        return self._opponent_strategies.copy()
    
    def _get_strategy_templates(
        self, 
        track_type: str, 
        tire_deg: str,
        race_laps: int
    ) -> Dict[str, List[str]]:
        """
        Get strategy templates for different grid positions.
        
        Returns dict with keys 'front', 'midfield', 'back' mapping to tire sequences.
        """
        # High degradation tracks favor 2-stops
        if track_type == "high_deg" or tire_deg == "high":
            if race_laps > 60:
                return {
                    "front": ["S", "M", "H"],      # Front runners: S-M-H 2-stop
                    "front_alt": ["M", "M", "H"],  # Alternative: M-M-H
                    "midfield": ["M", "H", "S"],   # Midfield: Offset timing
                    "midfield_alt": ["H", "S", "M"],
                    "back": ["H", "M"],            # Backmarkers: Conservative 1-stop
                    "back_alt": ["M", "M"],
                }
            else:
                return {
                    "front": ["S", "M"],
                    "front_alt": ["S", "H"],
                    "midfield": ["M", "H"],
                    "midfield_alt": ["H", "M"],
                    "back": ["H", "M"],
                    "back_alt": ["M", "H"],
                }
        
        # Low degradation (e.g., Monaco) - mostly 1-stop
        elif track_type == "low_deg" or tire_deg == "low":
            return {
                "front": ["S", "H"],       # Aggressive start
                "front_alt": ["M", "H"],
                "midfield": ["M", "H"],    # Standard 1-stop
                "midfield_alt": ["M", "S"],
                "back": ["H", "M"],        # Long first stint
                "back_alt": ["H", "S"],
            }
        
        # Normal track - mixed strategies
        else:
            if race_laps > 55:
                return {
                    "front": ["S", "M", "H"],  # 2-stop for long races
                    "front_alt": ["S", "H"],   # 1-stop aggressive
                    "midfield": ["M", "H"],    # Standard 1-stop
                    "midfield_alt": ["S", "M"],
                    "back": ["H", "M"],        # Conservative
                    "back_alt": ["M", "H"],
                }
            else:
                return {
                    "front": ["S", "H"],
                    "front_alt": ["S", "M"],
                    "midfield": ["M", "H"],
                    "midfield_alt": ["M", "S"],
                    "back": ["H", "M"],
                    "back_alt": ["M", "H"],
                }
    
    def _select_strategy_for_position(
        self, 
        position: int, 
        templates: Dict[str, List[str]],
        team: str = ""
    ) -> List[str]:
        """
        Select appropriate strategy for a grid position.
        
        Front runners (P1-5): More aggressive, shorter first stint
        Midfield (P6-14): Standard strategies
        Backmarkers (P15-20): Conservative, offset timing
        """
        import random
        
        # Top teams tend to be more aggressive
        top_teams = ["Red Bull Racing", "Ferrari", "McLaren", "Mercedes"]
        is_top_team = any(t.lower() in team.lower() for t in top_teams)
        
        if position <= 5:
            # Front runners: aggressive strategies
            if random.random() < 0.7:
                return templates.get("front", ["S", "H"]).copy()
            else:
                return templates.get("front_alt", ["S", "M"]).copy()
                
        elif position <= 10:
            # Upper midfield: mix of aggressive and standard
            if is_top_team or random.random() < 0.5:
                return templates.get("front_alt", ["S", "H"]).copy()
            else:
                return templates.get("midfield", ["M", "H"]).copy()
                
        elif position <= 14:
            # Lower midfield: standard strategies
            if random.random() < 0.7:
                return templates.get("midfield", ["M", "H"]).copy()
            else:
                return templates.get("midfield_alt", ["M", "S"]).copy()
                
        else:
            # Backmarkers: conservative or offset strategies
            if random.random() < 0.6:
                return templates.get("back", ["H", "M"]).copy()
            else:
                return templates.get("back_alt", ["M", "H"]).copy()
    
    def get_strategy_summary(self) -> str:
        """
        Get a text summary of all assigned strategies.
        
        Returns:
            Formatted string showing all driver strategies
        """
        if not self._opponent_strategies:
            return "No strategies assigned"
        
        lines = ["Driver Strategies:"]
        lines.append("-" * 50)
        
        # Sort by starting position
        sorted_strategies = sorted(
            self._opponent_strategies.values(),
            key=lambda s: s.starting_position
        )
        
        for strategy in sorted_strategies:
            custom_mark = "*" if strategy.is_custom else " "
            pit_str = ", ".join(f"L{p}" for p in strategy.pit_laps) if strategy.pit_laps else "-"
            lines.append(
                f"P{strategy.starting_position:2d} {strategy.driver_code:3s}{custom_mark}: "
                f"{strategy.get_notation():10s} | Pits: {pit_str}"
            )
        
        lines.append("-" * 50)
        lines.append("* = Custom strategy")
        
        return "\n".join(lines)
