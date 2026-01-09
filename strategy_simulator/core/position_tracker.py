"""
Position Tracker - 位置追蹤模擬器

核心模組，負責模擬 20 台車的全場位置追蹤。

特性:
- 時間步長模擬 (預設 1 秒)
- 速度曲線計算
- DRS 判定與加成
- 超車事件偵測與執行
- SC/VSC 處理
- Lapping (被套圈) 處理
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import copy
import random
import json
from pathlib import Path

from .overtake_calculator import (
    CarState, OvertakeAttempt, OvertakeCalculator, get_overtake_calculator
)
from ..data.track_config import TrackConfig, get_track_config
from ..data.team_performance_loader import TeamPerformanceLoader, get_team_performance_loader
from ..data.longrun_loader import LongRunLoader, LongRunData


@dataclass
class SimulationState:
    """模擬狀態快照"""
    time_s: float
    lap: int
    car_states: List[CarState]
    sc_active: bool = False
    vsc_active: bool = False
    drs_enabled: bool = False  # 前 2 圈 DRS 關閉


@dataclass
class SimulationResult:
    """模擬結果"""
    total_laps: int
    total_time_s: float
    final_positions: List[str]  # 按位置排序的車手列表
    overtake_attempts: List[OvertakeAttempt]
    position_history: List[Dict[str, int]]  # 每圈結束時的位置
    lap_times: Dict[str, List[float]]  # 每位車手的圈時
    final_car_states: Dict[str, dict] = None  # 每位車手的最終狀態 (position_m, lap_number)
    
    
class PositionTracker:
    """
    位置追蹤模擬器
    
    模擬 20 台車的完整比賽過程
    """
    
    # DRS 開啟的最小圈數
    DRS_ENABLE_LAP = 3
    
    # DRS 速度加成 (km/h)
    DRS_SPEED_BOOST = 12.0
    
    # SC 期間的速度 (km/h)
    SC_SPEED = 180.0
    
    # VSC 速度限制比例
    VSC_SPEED_RATIO = 0.6
    
    # SC 聚集效果：間距縮減比例 (每秒縮減多少秒的間距)
    SC_GAP_COMPRESSION_RATE = 0.1  # 每秒縮減 0.1 秒間距
    
    # SC 重啟後的領先者優勢持續時間 (秒)
    SC_RESTART_ADVANTAGE_DURATION = 10.0
    
    # SC 重啟後領先者速度加成比例
    SC_RESTART_ADVANTAGE_FACTOR = 1.02  # 2% 速度優勢
    
    # 超車嘗試的最大間距 (秒) - DRS 範圍內才能嘗試
    OVERTAKE_GAP_THRESHOLD_S = 1.0  # 1 秒內才能嘗試超車
    
    # 超車冷卻時間 (秒) - 同一對車手之間的冷卻
    OVERTAKE_COOLDOWN_S = 30.0  # 增加到 30 秒防止頻繁嘗試
    
    # 每圈最多超車嘗試次數 (全場總計)
    MAX_ATTEMPTS_PER_LAP = 2  # 全場每圈最多 2 次超車嘗試
    
    # 速度隨機波動範圍 (比例) - 降低以穩定位置
    SPEED_VARIANCE_RATIO = 0.001  # ±0.1% 隨機波動（極低變異）
    
    # 輪胎衰退對速度的影響 (每圈衰退比例)
    # 此為預設值，實際使用時從 LongRunLoader 動態載入
    DEFAULT_TYRE_DEGRADATION = 0.0005  # 預設每圈衰退 0.05% 速度
    
    # 合成衰退率字典 {車手: {合成: 衰退率}}
    # 從 Long Run 分析動態載入，單位: 秒/圈
    compound_degradation: Dict[str, Dict[str, float]] = {}
    
    # 備用車隊速度係數 (僅當 F125 車手數據和車隊數據都不可用時使用)
    # 正常情況下應使用 TeamPerformanceLoader 載入的車手/車隊速度係數
    # 車手係數優先，車隊係數次之，此為最後備用
    DEFAULT_TEAM_SPEED_FACTORS = {
        "McLaren": 1.010,
        "Ferrari": 1.008,
        "Red Bull Racing": 1.007,
        "Mercedes": 1.005,
        "Aston Martin": 1.002,
        "Racing Bulls": 1.000,
        "Alpine": 0.998,
        "Williams": 0.996,
        "Haas F1 Team": 0.995,
        "Kick Sauber": 0.993,
    }
    
    def __init__(
        self,
        track_config: TrackConfig,
        time_step: float = 1.0,
        total_laps: int = 50,
        year: int = 2025,
        race: str = ""
    ):
        """
        初始化位置追蹤器
        
        Args:
            track_config: 賽道配置
            time_step: 時間步長 (秒)
            total_laps: 比賽總圈數
            year: 年份 (用於載入車隊性能數據)
            race: 賽事名稱 (用於載入車隊性能數據)
        """
        self.track_config = track_config
        self.time_step = time_step
        self.total_laps = total_laps
        
        # 超車計算器
        self.overtake_calculator = get_overtake_calculator()
        
        # 車隊性能載入器
        self.team_performance_loader = get_team_performance_loader()
        self.team_profiles = {}
        self.driver_profiles = {}  # 車手級別速度配置
        self.longrun_data: Optional[LongRunData] = None  # Long Run 數據
        
        if race:
            self.team_profiles = self.team_performance_loader.load_for_race(year, race, "FP2")
            if self.team_profiles:
                print(f"[PositionTracker] 載入 {len(self.team_profiles)} 個車隊性能數據")
            
            # 載入車手級別速度係數
            self.driver_profiles = self.team_performance_loader.driver_profiles
            if self.driver_profiles:
                print(f"[PositionTracker] 載入 {len(self.driver_profiles)} 個車手速度係數")
                # 打印車手速度係數摘要
                self.team_performance_loader.print_driver_summary()
            
            # 載入 Long Run 輪胎衰退數據
            self._load_longrun_data(year, race)
        
        # 狀態
        self.car_states: List[CarState] = []
        self.current_time_s = 0.0
        self.current_lap = 1
        self.drs_enabled = False
        self.sc_active = False
        self.vsc_active = False
        
        # SC 重啟相關狀態
        self.sc_restart_time_s: Optional[float] = None  # SC 解除時間
        self.sc_previous_active = False  # 用於檢測 SC 解除
        
        # 記錄
        self.overtake_attempts: List[OvertakeAttempt] = []
        self.position_history: List[Dict[str, int]] = []
        self.lap_times: Dict[str, List[float]] = {}
        self.lap_start_times: Dict[str, float] = {}
        
        # 超車冷卻追蹤 {(attacker, defender): last_attempt_time}
        self.overtake_cooldowns: Dict[Tuple[str, str], float] = {}
        
        # 每圈超車嘗試計數 {driver: count}
        self.lap_attempt_counts: Dict[str, int] = {}
        self.last_lap_reset = 0
        
        # 快照記錄追蹤（確保每圈只記錄一次）
        self.last_snapshot_lap = 0
        
        # 🔍 診斷模式：輸出車手速度係數到 TXT
        self._write_speed_factor_diagnostics()
    
    def _write_speed_factor_diagnostics(self) -> None:
        """
        寫入車手速度係數診斷到 TXT 檔案
        
        直接使用 open() 寫入，避開 logger 系統
        """
        import os
        from datetime import datetime
        
        diag_file = os.path.join(os.path.dirname(__file__), "..", "..", "speed_factor_diagnostics.txt")
        diag_file = os.path.abspath(diag_file)
        
        with open(diag_file, "w", encoding="utf-8") as f:
            f.write("="*80 + "\n")
            f.write(f"速度係數診斷報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # 1. 車手級別速度係數 (從 F125 載入)
            f.write("[1] 車手速度係數 (driver_profiles):\n")
            f.write("-"*60 + "\n")
            if self.driver_profiles:
                # 按速度係數排序
                sorted_drivers = sorted(
                    self.driver_profiles.items(),
                    key=lambda x: x[1].speed_factor,
                    reverse=True
                )
                for driver, profile in sorted_drivers:
                    f.write(f"  {driver:5s}: speed_factor={profile.speed_factor:.4f}, "
                            f"straight={profile.straight_speed_kmh:.1f}km/h, "
                            f"corner={profile.avg_corner_speed_kmh:.1f}km/h\n")
            else:
                f.write("  (無車手速度數據)\n")
            f.write("\n")
            
            # 2. 車隊速度係數
            f.write("[2] 車隊速度係數 (team_profiles):\n")
            f.write("-"*60 + "\n")
            if self.team_profiles:
                for team, profile in self.team_profiles.items():
                    f.write(f"  {team:20s}: straight={profile.straight_speed_factor:.4f}, "
                            f"corner={profile.corner_speed_factor:.4f}\n")
            else:
                f.write("  (無車隊數據，使用 DEFAULT_TEAM_SPEED_FACTORS)\n")
                for team, factor in self.DEFAULT_TEAM_SPEED_FACTORS.items():
                    f.write(f"  {team:20s}: {factor:.4f}\n")
            f.write("\n")
            
            # 3. Long Run 輪胎衰退數據
            f.write("[3] Long Run 輪胎衰退數據:\n")
            f.write("-"*60 + "\n")
            if self.longrun_data and self.longrun_data.degradation:
                for compound, deg_data in self.longrun_data.degradation.items():
                    f.write(f"  {compound}: {deg_data.deg_per_lap:.4f} 秒/圈\n")
            else:
                f.write(f"  (無 Long Run 數據，使用預設衰退率: {self.DEFAULT_TYRE_DEGRADATION})\n")
            f.write("\n")
            
            # 4. 關鍵參數
            f.write("[4] 模擬參數:\n")
            f.write("-"*60 + "\n")
            f.write(f"  總圈數: {self.total_laps}\n")
            f.write(f"  時間步長: {self.time_step}s\n")
            f.write(f"  賽道: {self.track_config.track_name} ({self.track_config.track_length_m}m)\n")
            f.write(f"  速度波動範圍: ±{self.SPEED_VARIANCE_RATIO*100:.2f}%\n")
            f.write(f"  超車冒却時間: {self.OVERTAKE_COOLDOWN_S}s\n")
            f.write(f"  每圈最多超車嘗試: {self.MAX_ATTEMPTS_PER_LAP}\n")
            f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("診斷檔案生成完成\n")
        
        import sys
        sys.stdout.write(f"[DIAG] 速度係數診斷已寫入: {diag_file}\n")
        sys.stdout.flush()
    
    def _load_longrun_data(self, year: int, race: str) -> None:
        """
        載入 Long Run 輪胎衰退數據
        
        從 LongRunLoader 獲取各合成的真實衰退率，
        用於替代硬編碼的 TYRE_DEGRADATION_FACTOR。
        """
        try:
            loader = LongRunLoader()
            self.longrun_data = loader.load_fp2_data(year, race)
            
            if self.longrun_data and self.longrun_data.degradation:
                print(f"[PositionTracker] 載入 Long Run 衰退數據:")
                for compound, deg_data in self.longrun_data.degradation.items():
                    print(f"  {compound}: {deg_data.deg_per_lap:.4f} 秒/圈")
            else:
                print("[PositionTracker] 無 Long Run 數據，使用預設衰退率")
        except Exception as e:
            print(f"[PositionTracker] 載入 Long Run 失敗: {e}")
            self.longrun_data = None
    
    def _get_tyre_degradation_factor(self, compound: str, driver: str = "") -> float:
        """
        獲取輪胎衰退係數
        
        優先使用 Long Run 數據的真實衰退率，
        無數據時使用預設值。
        
        Args:
            compound: 輪胎合成 ("S", "M", "H")
            driver: 車手代碼 (可選，用於車手級別衰退率)
            
        Returns:
            衰退係數 (每圈速度降低比例)
        """
        # 嘗試從 Long Run 數據獲取
        if self.longrun_data:
            # 標準化合成名稱
            compound_map = {"S": "SOFT", "M": "MEDIUM", "H": "HARD"}
            compound_name = compound_map.get(compound.upper(), compound.upper())
            
            # 嘗試獲取車手級別衰退率
            if driver:
                driver_deg = self.longrun_data.get_driver_deg_rate(driver, compound_name)
                if driver_deg is not None:
                    # 將秒/圈轉換為速度比例 (假設基準圈時 ~85 秒)
                    return driver_deg / 85.0 * 0.01
            
            # 獲取合成平均衰退率
            avg_deg = self.longrun_data.get_deg_rate(compound_name)
            if avg_deg > 0:
                return avg_deg / 85.0 * 0.01
        
        # 回退到預設值
        return self.DEFAULT_TYRE_DEGRADATION
    
    def _get_team_speed_factor(self, team: str, is_corner: bool = False) -> float:
        """
        獲取車隊速度係數
        
        優先使用 TeamPerformanceLoader 從 F125/F120/F121 載入的動態數據，
        若無數據則使用預設係數。
        
        Args:
            team: 車隊名稱
            is_corner: 是否在彎道區域 (True=使用彎道係數, False=使用直線係數)
            
        Returns:
            速度係數 (通常在 0.99~1.01 範圍)
        """
        # 優先使用動態載入的數據
        if self.team_profiles:
            profile = self.team_profiles.get(team)
            if profile:
                if is_corner:
                    return profile.corner_speed_factor
                else:
                    return profile.straight_speed_factor
        
        # 回退到預設係數
        return self.DEFAULT_TEAM_SPEED_FACTORS.get(team, 1.0)
    
    def _get_driver_speed_factor(self, driver: str, is_corner: bool = False, team: str = None) -> float:
        """
        獲取車手速度係數 (基於 F125 圈時數據)
        
        使用車手的最佳圈時計算相對速度係數：
        - 最快車手 = 1.0
        - 較慢車手 < 1.0 (如 0.978 表示比最快慢 2.2%)
        
        Args:
            driver: 車手代碼 (如 "VER", "NOR")
            is_corner: 是否在彎道區域 (目前未區分直線/彎道)
            team: 車手所屬車隊 (用於回退到車隊係數)
            
        Returns:
            速度係數 (0.95 ~ 1.0 範圍)
        """
        if self.driver_profiles:
            profile = self.driver_profiles.get(driver)
            if profile:
                # 使用車手整體速度係數
                return profile.speed_factor
        
        # 無車手數據時，回退到車隊係數
        if team and self.team_profiles:
            team_profile = self.team_profiles.get(team)
            if team_profile:
                # 使用車隊係數 (取平均)
                avg_factor = (team_profile.straight_speed_factor + team_profile.corner_speed_factor) / 2
                return avg_factor
        
        # 最後回退到預設值 0.98 (比最快車手慢 2%)
        return 0.98
        
    def initialize_grid(self, grid: List[Dict]) -> None:
        """
        初始化發車格
        
        Args:
            grid: 發車順序，格式: [{"driver": "VER", "team": "Red Bull Racing", "tyre": "M"}, ...]
        """
        self.car_states = []
        
        for pos, entry in enumerate(grid, 1):
            # 計算起始位置 (間隔 8 米)
            start_position_m = self.track_config.track_length_m - (pos * 8)
            if start_position_m < 0:
                start_position_m += self.track_config.track_length_m
                
            car = CarState(
                driver=entry["driver"],
                team=entry.get("team", "Unknown"),
                position=pos,
                position_m=start_position_m,
                lap_number=0,
                tyre_compound=entry.get("tyre", "M"),
                tyre_age_laps=0,
                gap_ahead_s=0.0 if pos == 1 else 0.5,
                gap_behind_s=0.0 if pos == len(grid) else 0.5
            )
            self.car_states.append(car)
            self.lap_times[car.driver] = []
            self.lap_start_times[car.driver] = 0.0
            
        print(f"[PositionTracker] 初始化 {len(self.car_states)} 台車")
        
    def simulate_step(self) -> None:
        """
        模擬一個時間步長
        
        執行順序:
        1. 更新每台車的位置
        2. 檢測圈數變化
        3. 更新間距
        4. 檢測並執行超車
        5. 更新位置排名
        """
        # 1. 更新位置
        for car in self.car_states:
            if car.is_in_pit:
                continue
                
            # 獲取當前位置的基礎速度 (來自 track_circuit_data 的真實彎道速度)
            base_speed = self.track_config.get_speed_at_position(car.position_m)
            
            # SC/VSC 處理
            if self.sc_active:
                base_speed = min(base_speed, self.SC_SPEED)
            elif self.vsc_active:
                base_speed *= self.VSC_SPEED_RATIO
            else:
                # 正常比賽時添加車手性能差異和隨機性
                
                # 判斷彎道類型 (用於選擇適當的速度因子)
                corner_type = self.track_config.get_corner_type(car.position_m)
                is_corner = corner_type != "straight"
                
                # 2a. 獲取車手的 driver_profile (用於 driver_factor 回退)
                # 注意：不再用車手速度數據調整 base_speed，因為這會導致不公平的差異
                # 車手速度差異應該只通過 driver_factor (基於 F125 圈時) 來體現
                driver_profile = self.driver_profiles.get(car.driver)
                original_base_speed = base_speed  # 保存原始值用於調試
                
                # 2b. 車手速度係數 (基於 F125 圈時) - 這是最重要的差異來源！
                driver_factor = self._get_driver_speed_factor(car.driver, is_corner, car.team)
                
                # 🔍 調試：NOR, VER 和 PER 的速度計算詳細 (每 500 步輸出一次)
                if car.driver in ["NOR", "VER", "PER"] and int(self.current_time_s) % 500 == 0 and int(self.current_time_s) > 0:
                    import sys
                    final_speed = base_speed * driver_factor
                    sys.stdout.write(f"[SPEED_CALC] t={self.current_time_s:.0f}s {car.driver}: base={original_base_speed:.2f}km/h, factor={driver_factor:.4f}, final={final_speed:.2f}km/h, pos_m={car.position_m:.1f}m, lap={car.lap_number}\n")
                    sys.stdout.flush()
                    
                base_speed *= driver_factor
                
                # 2c. 輪胎衰退影響 (使用 Long Run 動態數據)
                tyre_deg_factor = self._get_tyre_degradation_factor(car.tyre_compound, car.driver)
                tyre_penalty = 1.0 - (car.tyre_age_laps * tyre_deg_factor)
                tyre_penalty = max(tyre_penalty, 0.95)  # 最多降 5%
                base_speed *= tyre_penalty
                
                # 2d. 隨機速度波動 (±0.1% - 極低變異)
                random_factor = 1.0 + random.uniform(-self.SPEED_VARIANCE_RATIO, self.SPEED_VARIANCE_RATIO)
                base_speed *= random_factor
                
                # 2e. SC 重啟後領先者優勢
                if self.sc_restart_time_s is not None:
                    time_since_restart = self.current_time_s - self.sc_restart_time_s
                    if time_since_restart < self.SC_RESTART_ADVANTAGE_DURATION:
                        # 前 3 名車手獲得重啟優勢
                        if car.position <= 3:
                            advantage_decay = 1.0 - (time_since_restart / self.SC_RESTART_ADVANTAGE_DURATION)
                            restart_factor = 1.0 + (self.SC_RESTART_ADVANTAGE_FACTOR - 1.0) * advantage_decay
                            base_speed *= restart_factor
                    else:
                        # 超過優勢持續時間，清除重啟狀態
                        self.sc_restart_time_s = None
                
            # DRS 加成
            if self.drs_enabled and car.drs_active:
                base_speed += self.DRS_SPEED_BOOST
                
            # 計算移動距離
            distance_m = base_speed * (1000 / 3600) * self.time_step  # km/h -> m/s
            
            # 更新位置
            old_position = car.position_m
            car.position_m = (car.position_m + distance_m) % self.track_config.track_length_m
            
            # 2. 檢測圈數變化 (跨越起終點)
            if car.position_m < old_position:
                # 傳遞移動距離，用於插值計算精確跨越時刻
                self._on_lap_complete(car, distance_m, old_position)
        
        # 2.5 SC 聚集效果：縮減車隊間距
        if self.sc_active or self.vsc_active:
            self._apply_sc_gap_compression()
        
        # 2.6 檢測 SC 解除 (重啟)
        if self.sc_previous_active and not self.sc_active and not self.vsc_active:
            self.sc_restart_time_s = self.current_time_s
            print(f"[PositionTracker] SC 重啟 @ {self.current_time_s:.1f}s")
        self.sc_previous_active = self.sc_active or self.vsc_active
                
        # 3. 更新間距
        self._update_gaps()
        
        # 4. 更新 DRS 狀態
        if self.drs_enabled and not self.sc_active and not self.vsc_active:
            self._update_drs_status()
            
        # 5. 檢測超車機會
        overtakes = self._detect_overtake_opportunities()
        
        # 6. 執行超車
        for attacker, defender in overtakes:
            self._execute_overtake_attempt(attacker, defender)
            
        # 7. 更新位置排名
        self._update_positions()
        
        # 更新時間
        self.current_time_s += self.time_step
        
        # 更新圈數 (以領先者為準)
        leader = min(self.car_states, key=lambda c: c.position)
        self.current_lap = leader.lap_number
        
        # 每圈重置嘗試計數
        if self.current_lap > self.last_lap_reset:
            self.lap_attempt_counts.clear()
            self.last_lap_reset = self.current_lap
        
        # 記錄位置快照（每圈只記錄一次，在位置更新後，只記錄到 total_laps）
        if self.current_lap > self.last_snapshot_lap and self.current_lap > 0 and self.current_lap <= self.total_laps:
            self._record_position_snapshot()
            self.last_snapshot_lap = self.current_lap
            import sys
            sys.stdout.write(f"[SNAPSHOT] L{self.current_lap}: 記錄位置快照 (總 {len(self.position_history)} 個)\n")
            sys.stdout.flush()
        
        # 檢查 DRS 啟用
        if self.current_lap >= self.DRS_ENABLE_LAP and not self.drs_enabled:
            self.drs_enabled = True
            print(f"[PositionTracker] DRS 已啟用 (第 {self.current_lap} 圈)")
            
    def _on_lap_complete(self, car: CarState, distance_m: float = 0, old_position_m: float = 0) -> None:
        """
        處理車輛完成一圈
        
        使用插值計算精確的跨越終點線時刻，解決離散時間步長導致的圈時誤差。
        
        Args:
            car: 車輛狀態
            distance_m: 這一步的移動距離 (米)
            old_position_m: 移動前的賽道位置 (米)
        """
        import sys
        
        # 計算精確的跨越終點線時刻
        # old_position_m 接近 track_length, car.position_m 接近 0
        # 我們需要計算從 old_position_m 到終點線的距離佔總移動距離的比例
        track_length = self.track_config.track_length_m
        
        if distance_m > 0 and old_position_m > 0:
            # 跨越終點線前需要走的距離
            distance_to_finish = track_length - old_position_m
            # 跨越比例 (0~1 之間)
            cross_ratio = distance_to_finish / distance_m
            cross_ratio = max(0.0, min(1.0, cross_ratio))  # 確保在 [0,1] 範圍內
            # 精確的跨越時刻
            precise_cross_time = self.current_time_s + cross_ratio * self.time_step
        else:
            precise_cross_time = self.current_time_s
        
        # 🔍 前 2 圈強制顯示
        if car.lap_number < 2:
            sys.stdout.write(f"[ON_LAP_COMPLETE] {car.driver} 完成第 {car.lap_number} 圈\n")
            sys.stdout.flush()
        
        car.lap_number += 1
        car.tyre_age_laps += 1
        
        # 記錄圈時（使用精確跨越時刻）
        lap_time = precise_cross_time - self.lap_start_times[car.driver]
        if lap_time > 0:
            self.lap_times[car.driver].append(lap_time)
            
            # 🔍 調試：NOR 和 VER 的圈時詳細 (每 10 圈輸出一次 + 最後 3 圈)
            if car.driver in ["NOR", "VER"] and (car.lap_number % 10 == 0 or car.lap_number >= 56):
                total_time = sum(self.lap_times[car.driver])
                sys.stdout.write(f"[LAP_TIME] {car.driver} L{car.lap_number}: this_lap={lap_time:.3f}s, total={total_time:.2f}s\n")
                sys.stdout.flush()
        
        # 更新圈開始時間（使用精確跨越時刻）
        self.lap_start_times[car.driver] = precise_cross_time
        
        # 注意：快照記錄已移至 simulate_step 中，確保在位置更新後進行
            
    def _record_position_snapshot(self) -> None:
        """記錄當前位置快照"""
        snapshot = {car.driver: car.position for car in self.car_states}
        self.position_history.append(snapshot)
    
    def _apply_sc_gap_compression(self) -> None:
        """
        SC 期間縮減車隊間距 (聚集效果)
        
        在 SC 期間，後方車輛會逐漸縮短與前車的距離，
        模擬真實 SC 期間車隊聚集在一起的效果。
        """
        # 按位置排序
        sorted_cars = sorted(self.car_states, key=lambda c: c.position)
        
        for i, car in enumerate(sorted_cars):
            if i == 0:
                continue  # 領先者不動
                
            # 計算與前車的距離
            ahead_car = sorted_cars[i - 1]
            distance = self._get_track_distance(car.position_m, ahead_car.position_m)
            
            # SC 期間目標間距：約 30-50 公尺 (真實 SC 列隊)
            target_distance_m = 40.0
            
            if distance > target_distance_m:
                # 縮減距離：每秒縮短一定比例
                compression_speed = self.SC_SPEED * (1000 / 3600) * self.SC_GAP_COMPRESSION_RATE
                new_distance = max(distance - compression_speed * self.time_step, target_distance_m)
                
                # 移動車輛位置
                move_distance = distance - new_distance
                car.position_m = (car.position_m + move_distance) % self.track_config.track_length_m
        
    def _update_gaps(self) -> None:
        """更新所有車輛的間距"""
        # 按位置排序
        sorted_cars = sorted(self.car_states, key=lambda c: c.position)
        
        for i, car in enumerate(sorted_cars):
            # 與前車的間距
            if i == 0:
                car.gap_ahead_s = float('inf')
            else:
                ahead_car = sorted_cars[i - 1]
                # 計算距離差
                distance_diff = self._get_track_distance(car.position_m, ahead_car.position_m)
                # 估算時間差 (使用當前速度)
                speed = self.track_config.get_speed_at_position(car.position_m)
                speed_ms = speed * (1000 / 3600)
                car.gap_ahead_s = distance_diff / speed_ms if speed_ms > 0 else 10.0
                
            # 與後車的間距
            if i == len(sorted_cars) - 1:
                car.gap_behind_s = float('inf')
            else:
                behind_car = sorted_cars[i + 1]
                distance_diff = self._get_track_distance(behind_car.position_m, car.position_m)
                speed = self.track_config.get_speed_at_position(behind_car.position_m)
                speed_ms = speed * (1000 / 3600)
                car.gap_behind_s = distance_diff / speed_ms if speed_ms > 0 else 10.0
                
    def _get_track_distance(self, from_m: float, to_m: float) -> float:
        """計算賽道上兩點的距離 (考慮環繞)"""
        if to_m >= from_m:
            return to_m - from_m
        else:
            return (self.track_config.track_length_m - from_m) + to_m
            
    def _update_drs_status(self) -> None:
        """更新每台車的 DRS 狀態"""
        for car in self.car_states:
            # 在 DRS 區域內且前車在 1 秒內
            in_drs_zone = self.track_config.is_in_drs_zone(car.position_m)
            close_enough = car.gap_ahead_s < 1.0
            car.drs_active = in_drs_zone and close_enough
            
    def _detect_overtake_opportunities(self) -> List[Tuple[CarState, CarState]]:
        """
        偵測超車機會
        
        返回可能發生超車的 (攻擊者, 防守者) 對
        
        限制條件:
        1. 間距在 DRS 範圍內 (1 秒)
        2. 冷卻時間已過 (30 秒)
        3. 該車手本圈嘗試次數未超限 (1 次/圈)
        4. 必須在 DRS 區域內
        """
        opportunities = []
        
        for car in self.car_states:
            if car.position == 1:
                continue  # 領先者無法超車
                
            # 找到前一位車手
            ahead_cars = [c for c in self.car_states if c.position == car.position - 1]
            if not ahead_cars:
                continue
                
            ahead_car = ahead_cars[0]
            
            # 檢查間距是否足夠接近 (使用時間間距)
            if car.gap_ahead_s > self.OVERTAKE_GAP_THRESHOLD_S:
                continue
            
            # 必須在 DRS 區域內才能嘗試超車
            if not self.track_config.is_in_drs_zone(car.position_m):
                continue
                
            # 檢查冷卻時間
            cooldown_key = (car.driver, ahead_car.driver)
            last_attempt = self.overtake_cooldowns.get(cooldown_key, 0)
            if self.current_time_s - last_attempt < self.OVERTAKE_COOLDOWN_S:
                continue
                
            # 檢查每圈嘗試次數限制 (每車手每圈最多 1 次)
            if self.lap_attempt_counts.get(car.driver, 0) >= 1:
                continue
            
            # 全場每圈總嘗試次數限制
            total_attempts_this_lap = sum(self.lap_attempt_counts.values())
            if total_attempts_this_lap >= self.MAX_ATTEMPTS_PER_LAP:
                continue
                
            if self.overtake_calculator.can_attempt_overtake(car, ahead_car):
                opportunities.append((car, ahead_car))
                    
        return opportunities
        
    def _execute_overtake_attempt(
        self,
        attacker: CarState,
        defender: CarState
    ) -> None:
        """執行超車嘗試"""
        # 更新冷卻時間和計數
        cooldown_key = (attacker.driver, defender.driver)
        self.overtake_cooldowns[cooldown_key] = self.current_time_s
        self.lap_attempt_counts[attacker.driver] = self.lap_attempt_counts.get(attacker.driver, 0) + 1
        
        success, attempt = self.overtake_calculator.attempt_overtake(
            attacker=attacker,
            defender=defender,
            track_name=self.track_config.track_name,
            lap=self.current_lap,
            race_time_s=self.current_time_s
        )
        
        self.overtake_attempts.append(attempt)
        
        if success:
            # 交換位置 (名次和物理位置都交換)
            attacker.position, defender.position = defender.position, attacker.position
            
            # 交換物理賽道位置 (關鍵！這樣超車結果會在 _update_positions 中保持)
            attacker.position_m, defender.position_m = defender.position_m, attacker.position_m
            
    def _update_positions(self) -> None:
        """
        根據賽道位置更新比賽位置
        
        重要：位置變化只發生在以下情況：
        1. 成功超車（已在 _execute_overtake_attempt 中處理）
        2. 落後一整圈（lapped）
        3. 進站導致的位置變化
        
        這裡只處理落後一圈的情況，避免因速度波動導致頻繁位置變化。
        """
        # 只在圈數不同時才重新排序（處理被套圈的情況）
        # 按 (圈數, 當前位置) 排序，圈數優先
        sorted_cars = sorted(
            self.car_states,
            key=lambda c: (-c.lap_number, c.position)  # 圈數多的在前，位置小的優先
        )
        
        for pos, car in enumerate(sorted_cars, 1):
            car.position = pos
            
    def run_simulation(self) -> SimulationResult:
        """
        執行完整模擬
        
        返回模擬結果
        """
        print(f"\n[PositionTracker] 開始模擬: {self.total_laps} 圈")
        print(f"[PositionTracker] 賽道: {self.track_config.track_name} ({self.track_config.track_length_m}m)")
        print(f"[PositionTracker] 時間步長: {self.time_step}s")
        
        # 模擬直到所有車完成
        steps = 0
        max_steps = int(self.total_laps * 200 * 60 / self.time_step)  # 最大步數保護（提升至200倍）
        race_finished = False
        finish_lap_time = None  # 領先者完成比賽的時刻
        
        while steps < max_steps:
            self.simulate_step()
            steps += 1
            
            # 檢查比賽是否結束
            leader = min(self.car_states, key=lambda c: c.position)
            if leader.lap_number >= self.total_laps and not race_finished:
                # 領先者完成比賽，記錄時間
                race_finished = True
                finish_lap_time = self.current_time_s
                print(f"[RACE] 領先者 {leader.driver} 完成 {leader.lap_number} 圈，比賽時間: {finish_lap_time:.1f}s")
            
            if race_finished:
                # 給其他車手額外時間完成同樣圈數（最多 3 圈時間 = 約 300s）
                time_since_finish = self.current_time_s - finish_lap_time
                if time_since_finish > 300:
                    print(f"[RACE_END] 超時結束: 額外時間 {time_since_finish:.1f}s > 300s")
                    break
                # 檢查所有車手是否也完成 total_laps 圈
                # 只有被套圈的車手才會 < total_laps
                lap_counts = [car.lap_number for car in self.car_states]
                all_finished = all(l >= self.total_laps for l in lap_counts)
                if all_finished:
                    print(f"[RACE_END] 所有車手完成 {self.total_laps} 圈")
                    break
                # 每 10 秒輸出一次進度
                if steps % 10 == 0:
                    min_laps = min(lap_counts)
                    print(f"[RACE_WAIT] 等待: 最少圈數={min_laps}/{self.total_laps}, 額外時間={time_since_finish:.1f}s")
                
            # 進度報告 (每圈)
            if steps % int(100 / self.time_step) == 0:
                print(f"[PositionTracker] 圈 {self.current_lap}/{self.total_laps}, "
                      f"時間 {self.current_time_s:.1f}s, "
                      f"超車 {len([a for a in self.overtake_attempts if a.success])}")
                      
        # 生成結果
        final_positions = [car.driver for car in sorted(self.car_states, key=lambda c: c.position)]
        
        # 記錄每位車手的最終狀態
        final_car_states = {}
        for car in self.car_states:
            final_car_states[car.driver] = {
                "position_m": car.position_m,
                "lap_number": car.lap_number,
                "position": car.position,
                "tyre_compound": car.tyre_compound,
                "tyre_age_laps": car.tyre_age_laps
            }
        
        result = SimulationResult(
            total_laps=self.total_laps,
            total_time_s=self.current_time_s,
            final_positions=final_positions,
            overtake_attempts=self.overtake_attempts,
            position_history=self.position_history,
            lap_times=self.lap_times,
            final_car_states=final_car_states
        )
        
        # 統計
        successful_overtakes = sum(1 for a in self.overtake_attempts if a.success)
        print(f"\n[PositionTracker] 模擬完成!")
        print(f"[PositionTracker] 總時間: {self.current_time_s:.1f}s")
        print(f"[PositionTracker] 總超車嘗試: {len(self.overtake_attempts)}")
        print(f"[PositionTracker] 成功超車: {successful_overtakes}")
        print(f"[PositionTracker] 最終位置: {final_positions[:5]}...")
        
        # 🔍 寫入詳細診斷報告
        self._write_race_result_diagnostics(final_positions, successful_overtakes)
        
        return result
    
    def _write_race_result_diagnostics(self, final_positions: List[str], successful_overtakes: int) -> None:
        """
        寫入比賽結果詳細診斷到 TXT 檔案
        
        分析每位車手的位置變化、超車記錄等
        """
        import os
        from datetime import datetime
        
        diag_file = os.path.join(os.path.dirname(__file__), "..", "..", "race_result_diagnostics.txt")
        diag_file = os.path.abspath(diag_file)
        
        with open(diag_file, "w", encoding="utf-8") as f:
            f.write("="*80 + "\n")
            f.write(f"比賽結果診斷報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # 1. 位置變化摘要
            f.write("[1] 位置變化摘要 (發車 -> 最終):\n")
            f.write("-"*60 + "\n")
            
            # 從 position_history 獲取起始和最終位置
            if self.position_history:
                start_positions = self.position_history[0]
                end_positions = self.position_history[-1]
                
                # 計算位置變化並排序
                position_changes = []
                for driver in start_positions:
                    start_pos = start_positions.get(driver, 20)
                    end_pos = end_positions.get(driver, 20)
                    change = start_pos - end_pos  # 正數=進步，負數=退步
                    position_changes.append((driver, start_pos, end_pos, change))
                
                # 按位置變化排序 (最大進步在前)
                position_changes.sort(key=lambda x: -x[3])
                
                for driver, start, end, change in position_changes:
                    change_str = f"+{change}" if change > 0 else str(change)
                    # 標記異常大的位置變化
                    flag = " ⚠️ 異常!" if abs(change) >= 10 else ""
                    f.write(f"  {driver:5s}: P{start:2d} -> P{end:2d} ({change_str:4s}){flag}\n")
            f.write("\n")
            
            # 2. 超車記錄詳情
            f.write("[2] 超車記錄詳情:\n")
            f.write("-"*60 + "\n")
            f.write(f"  總嘗試次數: {len(self.overtake_attempts)}\n")
            f.write(f"  成功次數: {successful_overtakes}\n")
            f.write(f"  成功率: {(successful_overtakes/len(self.overtake_attempts)*100) if self.overtake_attempts else 0:.1f}%\n\n")
            
            if self.overtake_attempts:
                f.write("  成功超車詳情:\n")
                for attempt in self.overtake_attempts:
                    if attempt.success:
                        f.write(f"    L{attempt.lap:2d} @ {attempt.race_time_s:.0f}s: "
                                f"{attempt.attacker} 超越 {attempt.defender}\n")
            f.write("\n")
            
            # 3. 各車手超車統計
            f.write("[3] 各車手超車統計:\n")
            f.write("-"*60 + "\n")
            
            overtake_stats = {}  # {driver: {"gained": X, "lost": Y}}
            for attempt in self.overtake_attempts:
                if attempt.success:
                    if attempt.attacker not in overtake_stats:
                        overtake_stats[attempt.attacker] = {"gained": 0, "lost": 0}
                    if attempt.defender not in overtake_stats:
                        overtake_stats[attempt.defender] = {"gained": 0, "lost": 0}
                    overtake_stats[attempt.attacker]["gained"] += 1
                    overtake_stats[attempt.defender]["lost"] += 1
            
            for driver, stats in sorted(overtake_stats.items(), key=lambda x: -(x[1]["gained"] - x[1]["lost"])):
                net = stats["gained"] - stats["lost"]
                net_str = f"+{net}" if net > 0 else str(net)
                f.write(f"  {driver:5s}: 超越 {stats['gained']:2d} 次, 被超 {stats['lost']:2d} 次 (淨: {net_str})\n")
            f.write("\n")
            
            # 4. 圈時分析 (關注 TSU, HAM)
            f.write("[4] 關鍵車手圈時分析 (TSU, HAM, NOR, VER):\n")
            f.write("-"*60 + "\n")
            
            key_drivers = ["TSU", "HAM", "NOR", "VER"]
            for driver in key_drivers:
                if driver in self.lap_times and self.lap_times[driver]:
                    laps = self.lap_times[driver]
                    avg_lap = sum(laps) / len(laps)
                    min_lap = min(laps)
                    max_lap = max(laps)
                    f.write(f"  {driver}: {len(laps)} 圈, "
                            f"平均 {avg_lap:.3f}s, 最快 {min_lap:.3f}s, 最慢 {max_lap:.3f}s\n")
            f.write("\n")
            
            # 5. 速度係數確認
            f.write("[5] 關鍵車手速度係數:\n")
            f.write("-"*60 + "\n")
            for driver in key_drivers:
                factor = self._get_driver_speed_factor(driver, False)
                profile = self.driver_profiles.get(driver)
                if profile:
                    f.write(f"  {driver}: speed_factor={factor:.4f}, "
                            f"straight={profile.straight_speed_kmh:.1f}km/h, "
                            f"corner={profile.avg_corner_speed_kmh:.1f}km/h\n")
                else:
                    f.write(f"  {driver}: speed_factor={factor:.4f} (無 driver_profile)\n")
            f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("診斷報告生成完成\n")
        
        import sys
        sys.stdout.write(f"[DIAG] 比賽結果診斷已寫入: {diag_file}\n")
        sys.stdout.flush()
        
    def set_safety_car(self, active: bool) -> None:
        """設置 Safety Car 狀態"""
        self.sc_active = active
        if active:
            self.drs_enabled = False
            print(f"[PositionTracker] Safety Car 已部署")
        else:
            print(f"[PositionTracker] Safety Car 已結束")
            
    def set_virtual_safety_car(self, active: bool) -> None:
        """設置 Virtual Safety Car 狀態"""
        self.vsc_active = active
        if active:
            print(f"[PositionTracker] VSC 已啟動")
        else:
            print(f"[PositionTracker] VSC 已結束")
            
    def pit_stop(self, driver: str, new_tyre: str, pit_time_s: float = 22.0) -> None:
        """
        執行進站
        
        Args:
            driver: 車手代碼
            new_tyre: 新輪胎複合物
            pit_time_s: 進站時間 (秒)
        """
        for car in self.car_states:
            if car.driver == driver:
                car.is_in_pit = True
                car.tyre_compound = new_tyre
                car.tyre_age_laps = 0
                # 簡化處理：直接加時間損失
                # 實際上應該模擬進站過程
                print(f"[PositionTracker] {driver} 進站換 {new_tyre} 胎")
                break


def create_position_tracker(
    track_name: str,
    time_step: float = 1.0,
    total_laps: int = 50,
    year: int = 2025,
    race: str = ""
) -> PositionTracker:
    """
    便捷函數：創建位置追蹤器
    
    Args:
        track_name: 賽道名稱
        time_step: 時間步長 (秒)
        total_laps: 比賽總圈數
        year: 年份 (用於載入車隊/車手性能數據和 Long Run 數據)
        race: 賽事名稱 (用於載入車隊/車手性能數據和 Long Run 數據)
    """
    track_config = get_track_config(track_name)
    # 如果沒有提供 race，使用 track_name 作為預設值
    race_name = race if race else track_name
    return PositionTracker(track_config, time_step, total_laps, year, race_name)
