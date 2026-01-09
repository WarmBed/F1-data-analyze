# -*- coding: utf-8 -*-
"""
Base Overtake Detector - 統一超車偵測基類
==========================================

提供標準化的超車分類邏輯，供 F100 和 F134 繼承使用。

超車分類標準（來自 F100 overtake_detector.py）：
1. on_track     - 賽道上真正的超車
2. pit_related  - 進站相關的位置變化
3. sc_related   - SC/VSC 期間的位置變化  
4. lap_one      - 第一圈起跑混戰

Author: F1T Team
Date: 2026-01-05
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class OvertakeType(Enum):
    """超車類型列舉"""
    ON_TRACK = "on_track"           # 賽道上真正超車
    PIT_RELATED = "pit_related"     # 進站相關位置變化
    SC_RELATED = "sc_related"       # SC/VSC 相關變化
    LAP_ONE = "lap_one"             # 第一圈位置變化


class TrackStatus(Enum):
    """賽道狀態列舉"""
    GREEN = 1       # 綠旗
    YELLOW = 2      # 黃旗
    SC = 4          # Safety Car
    RED = 5         # 紅旗
    VSC = 6         # Virtual Safety Car
    VSC_ENDING = 7  # VSC 結束中


# SC/VSC 狀態碼集合
SC_VSC_STATUS_CODES = {4, 6, 7}


@dataclass
class OvertakeEvent:
    """單次超車事件的標準數據結構"""
    # 基本資訊
    race: str                           # 賽事名稱
    track: str                          # 賽道名稱
    lap: int                            # 圈數
    timestamp: str = ""                 # 事件時間戳
    
    # 超車類型
    overtake_type: OvertakeType = OvertakeType.ON_TRACK
    overtake_success: bool = True       # 是否成功超車
    
    # 攻擊者資訊
    attacker_driver: str = ""           # 車手代碼 (TLA)
    attacker_driver_num: str = ""       # 車手編號
    attacker_team: str = ""             # 車隊名稱
    attacker_position_before: int = 0   # 超車前位置
    attacker_position_after: int = 0    # 超車後位置
    attacker_tyre_compound: str = ""    # 輪胎配方
    attacker_tyre_age: int = 0          # 輪胎使用圈數
    attacker_speed: float = 0.0         # 速度 (km/h)
    attacker_drs_active: bool = False   # DRS 是否啟動
    
    # 防守者資訊
    defender_driver: str = ""           # 車手代碼 (TLA)
    defender_driver_num: str = ""       # 車手編號
    defender_team: str = ""             # 車隊名稱
    defender_position_before: int = 0   # 被超車前位置
    defender_position_after: int = 0    # 被超車後位置
    defender_tyre_compound: str = ""    # 輪胎配方
    defender_tyre_age: int = 0          # 輪胎使用圈數
    defender_speed: float = 0.0         # 速度 (km/h)
    
    # 間距資訊
    gap_before_s: float = 0.0           # 超車前間距 (秒)
    gap_after_s: float = 0.0            # 超車後間距 (秒)
    
    # GPS 位置
    x: int = 0                          # GPS X 座標
    y: int = 0                          # GPS Y 座標
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "race": self.race,
            "track": self.track,
            "lap": self.lap,
            "timestamp": self.timestamp,
            "overtake_type": self.overtake_type.value,
            "overtake_success": self.overtake_success,
            "attacker": {
                "driver": self.attacker_driver,
                "driver_num": self.attacker_driver_num,
                "team": self.attacker_team,
                "position_before": self.attacker_position_before,
                "position_after": self.attacker_position_after,
                "tyre_compound": self.attacker_tyre_compound,
                "tyre_age_laps": self.attacker_tyre_age,
                "speed_kmh": self.attacker_speed,
                "drs_active": self.attacker_drs_active
            },
            "defender": {
                "driver": self.defender_driver,
                "driver_num": self.defender_driver_num,
                "team": self.defender_team,
                "position_before": self.defender_position_before,
                "position_after": self.defender_position_after,
                "tyre_compound": self.defender_tyre_compound,
                "tyre_age_laps": self.defender_tyre_age,
                "speed_kmh": self.defender_speed
            },
            "gap_before_s": self.gap_before_s,
            "gap_after_s": self.gap_after_s,
            "x": self.x,
            "y": self.y
        }


@dataclass
class OvertakeStatistics:
    """超車統計結果"""
    year: int
    race: str
    session: str = "R"
    
    # 統計數據
    total_overtakes: int = 0
    on_track_overtakes: int = 0
    pit_related_changes: int = 0
    sc_related_changes: int = 0
    lap_one_changes: int = 0
    
    # 詳細事件列表
    overtake_events: List[OvertakeEvent] = field(default_factory=list)
    
    # 車手統計
    driver_stats: Dict[str, Dict] = field(default_factory=dict)
    
    # 車隊統計
    team_stats: Dict[str, Dict] = field(default_factory=dict)
    
    # 賽道統計
    track_stats: Dict[str, Dict] = field(default_factory=dict)


class BaseOvertakeDetector(ABC):
    """
    超車偵測器基類
    
    提供統一的超車分類邏輯，子類實現具體的數據讀取方式。
    """
    
    def __init__(self, year: int, race: str, session: str = "R"):
        """
        初始化超車偵測器
        
        Args:
            year: 年份 (例如 2025)
            race: 賽事名稱 (例如 "Japan")
            session: 會話類型 (R=Race, Q=Qualifying)
        """
        self.year = year
        self.race = race
        self.session = session
        
        # 進站圈數追蹤: {driver_num: {lap1, lap2, ...}}
        self._pit_laps: Dict[str, Set[int]] = {}
        
        # SC/VSC 圈數追蹤
        self._sc_laps: Set[int] = set()
        
        # 車手資訊映射: {driver_num: {"tla": "VER", "team": "Red Bull"}}
        self._driver_info: Dict[str, Dict] = {}
        
        # 統計結果
        self._stats = OvertakeStatistics(year=year, race=race, session=session)
    
    # =========================================================================
    # 抽象方法 - 子類必須實現
    # =========================================================================
    
    @abstractmethod
    def load_data(self) -> bool:
        """
        載入數據源
        
        Returns:
            是否成功載入數據
        """
        pass
    
    @abstractmethod
    def detect_overtakes(self) -> List[OvertakeEvent]:
        """
        偵測所有超車事件
        
        Returns:
            超車事件列表
        """
        pass
    
    # =========================================================================
    # 通用分類邏輯 - 所有子類共用
    # =========================================================================
    
    def classify_overtake(
        self, 
        attacker_num: str,
        defender_num: str,
        current_lap: int,
        all_pit_laps: Set[int] = None
    ) -> OvertakeType:
        """
        分類超車類型 - 核心邏輯
        
        分類優先順序：
        1. 第一圈 -> LAP_ONE
        2. SC/VSC 期間 -> SC_RELATED
        3. 任何人進站圈 -> PIT_RELATED
        4. 其他 -> ON_TRACK
        
        Args:
            attacker_num: 攻擊者車手編號
            defender_num: 防守者車手編號
            current_lap: 當前圈數
            all_pit_laps: 所有進站圈的集合 (包含出站圈)
            
        Returns:
            OvertakeType 列舉值
        """
        # 1. 第一圈 (起跑混戰)
        if current_lap <= 1:
            return OvertakeType.LAP_ONE
        
        # 2. SC/VSC 期間
        if current_lap in self._sc_laps:
            return OvertakeType.SC_RELATED
        
        # 3. 進站相關 (任何人進站的圈數)
        if all_pit_laps is None:
            all_pit_laps = self._calculate_all_pit_laps()
        
        if current_lap in all_pit_laps:
            return OvertakeType.PIT_RELATED
        
        # 4. 賽道上真正超車
        return OvertakeType.ON_TRACK
    
    def _calculate_all_pit_laps(self) -> Set[int]:
        """
        計算所有進站圈 (包含出站圈)
        
        進站發生在 Lap N，但車手在 Lap N+1 才從維修站出來
        所以 Lap N+1 的「超車」實際上可能是對手出站，不是真正超車
        
        Returns:
            所有進站圈和出站圈的集合
        """
        all_pit_laps: Set[int] = set()
        
        for laps in self._pit_laps.values():
            all_pit_laps.update(laps)
            # 加入出站圈 (進站圈 + 1)
            all_pit_laps.update(lap + 1 for lap in laps)
        
        return all_pit_laps
    
    def is_driver_in_pit(
        self, 
        driver_num: str, 
        current_lap: int,
        in_pit_flag: bool = False,
        pit_out_flag: bool = False
    ) -> bool:
        """
        檢查車手是否在進站/出站狀態
        
        Args:
            driver_num: 車手編號
            current_lap: 當前圈數
            in_pit_flag: 當前快照的 in_pit 標記
            pit_out_flag: 當前快照的 pit_out 標記
            
        Returns:
            是否在進站/出站狀態
        """
        # 檢查 snapshot 標記
        if in_pit_flag or pit_out_flag:
            return True
        
        # 檢查進站圈數記錄
        driver_pit_laps = self._pit_laps.get(driver_num, set())
        if current_lap in driver_pit_laps or (current_lap - 1) in driver_pit_laps:
            return True
        
        return False
    
    def is_sc_active(self, current_lap: int) -> bool:
        """
        檢查是否在 SC/VSC 期間
        
        Args:
            current_lap: 當前圈數
            
        Returns:
            是否在 SC/VSC 期間
        """
        return current_lap in self._sc_laps
    
    # =========================================================================
    # 統計更新方法
    # =========================================================================
    
    def update_statistics(self, event: OvertakeEvent):
        """
        更新統計數據
        
        Args:
            event: 超車事件
        """
        self._stats.total_overtakes += 1
        
        # 按類型統計
        if event.overtake_type == OvertakeType.ON_TRACK:
            self._stats.on_track_overtakes += 1
        elif event.overtake_type == OvertakeType.PIT_RELATED:
            self._stats.pit_related_changes += 1
        elif event.overtake_type == OvertakeType.SC_RELATED:
            self._stats.sc_related_changes += 1
        elif event.overtake_type == OvertakeType.LAP_ONE:
            self._stats.lap_one_changes += 1
        
        # 更新車手統計
        self._update_driver_stats(event)
        
        # 更新車隊統計
        self._update_team_stats(event)
        
        # 添加到事件列表
        self._stats.overtake_events.append(event)
    
    def _update_driver_stats(self, event: OvertakeEvent):
        """更新車手統計"""
        # 攻擊者統計
        attacker = event.attacker_driver
        if attacker not in self._stats.driver_stats:
            self._stats.driver_stats[attacker] = {
                "total_attacks": 0,
                "successful_attacks": 0,
                "total_defenses": 0,
                "successful_defenses": 0,
                "team": event.attacker_team
            }
        
        self._stats.driver_stats[attacker]["total_attacks"] += 1
        if event.overtake_success:
            self._stats.driver_stats[attacker]["successful_attacks"] += 1
        
        # 防守者統計
        defender = event.defender_driver
        if defender and defender not in self._stats.driver_stats:
            self._stats.driver_stats[defender] = {
                "total_attacks": 0,
                "successful_attacks": 0,
                "total_defenses": 0,
                "successful_defenses": 0,
                "team": event.defender_team
            }
        
        if defender:
            self._stats.driver_stats[defender]["total_defenses"] += 1
            if not event.overtake_success:
                self._stats.driver_stats[defender]["successful_defenses"] += 1
    
    def _update_team_stats(self, event: OvertakeEvent):
        """更新車隊統計"""
        # 攻擊者車隊
        attacker_team = event.attacker_team
        if attacker_team and attacker_team not in self._stats.team_stats:
            self._stats.team_stats[attacker_team] = {
                "total_attacks": 0,
                "successful_attacks": 0,
                "total_defenses": 0,
                "successful_defenses": 0
            }
        
        if attacker_team:
            self._stats.team_stats[attacker_team]["total_attacks"] += 1
            if event.overtake_success:
                self._stats.team_stats[attacker_team]["successful_attacks"] += 1
        
        # 防守者車隊
        defender_team = event.defender_team
        if defender_team and defender_team not in self._stats.team_stats:
            self._stats.team_stats[defender_team] = {
                "total_attacks": 0,
                "successful_attacks": 0,
                "total_defenses": 0,
                "successful_defenses": 0
            }
        
        if defender_team:
            self._stats.team_stats[defender_team]["total_defenses"] += 1
            if not event.overtake_success:
                self._stats.team_stats[defender_team]["successful_defenses"] += 1
    
    # =========================================================================
    # 輔助方法
    # =========================================================================
    
    def get_driver_tla(self, driver_num: str) -> str:
        """獲取車手 TLA 代碼"""
        info = self._driver_info.get(driver_num, {})
        return info.get("tla", driver_num)
    
    def get_driver_team(self, driver_num: str) -> str:
        """獲取車手車隊"""
        info = self._driver_info.get(driver_num, {})
        return info.get("team", "")
    
    def parse_gap(self, gap_value) -> float:
        """
        解析間距值為浮點數秒
        
        Args:
            gap_value: 間距值 (可能是 float, int, str)
            
        Returns:
            間距秒數
        """
        if gap_value is None:
            return 0.0
        if isinstance(gap_value, (int, float)):
            return float(gap_value)
        if isinstance(gap_value, str):
            try:
                # 移除 's' 後綴和空白
                gap_str = gap_value.replace('s', '').strip()
                return float(gap_str)
            except ValueError:
                return 0.0
        return 0.0
    
    def get_statistics(self) -> OvertakeStatistics:
        """獲取統計結果"""
        return self._stats
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式 (用於 JSON 輸出)"""
        return {
            "year": self._stats.year,
            "race": self._stats.race,
            "session": self._stats.session,
            "total_overtakes": self._stats.total_overtakes,
            "on_track_overtakes": self._stats.on_track_overtakes,
            "pit_related_changes": self._stats.pit_related_changes,
            "sc_related_changes": self._stats.sc_related_changes,
            "lap_one_changes": self._stats.lap_one_changes,
            "driver_stats": self._stats.driver_stats,
            "team_stats": self._stats.team_stats,
            "overtake_events": [e.to_dict() for e in self._stats.overtake_events]
        }
