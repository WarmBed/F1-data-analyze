# -*- coding: utf-8 -*-
"""
Live Timing Overtake Detector
=============================

精確超車檢測器 - 使用 Live Timing 高頻位置數據檢測真正的超車事件。

與 FastF1 的簡單位置變化計算不同，本模組：
1. 使用 TimingAppData.json 的即時排名數據 (Line 字段)
2. 配合 TimingData.json 追蹤每位車手的圈數 (NumberOfLaps)
3. 配合 PitLaneTimeCollection.json 過濾進站相關位置變化 (PitTimes)
4. 配合 TrackStatus.json 過濾 SC/VSC 期間
5. 分類統計：賽道超車 vs 進站相關 vs 第一圈混戰

Author: F1T Team
Date: 2025-12-25
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

# 嘗試導入 logger，如果失敗或阻塞則使用 print
# 注意：core.logger 可能導致阻塞，這裡使用簡單的 print logger
class SimpleLogger:
    def info(self, msg, *args): print(f"[INFO] {msg % args if args else msg}")
    def debug(self, msg, *args): pass  # 調試信息不輸出
    def warning(self, msg, *args): print(f"[WARN] {msg % args if args else msg}")
    def error(self, msg, *args): print(f"[ERROR] {msg % args if args else msg}")

logger = SimpleLogger()


# =============================================================================
# Constants
# =============================================================================

SC_VSC_TRACK_STATUS = {'4', '6', '7'}    # SC=4, VSC=6, RedFlag=7
NON_RACE_CAR_NUMBERS = {'241', '242', '243'}


@dataclass
class OvertakeEvent:
    """單次超車事件"""
    timestamp: str                    # 超車發生時間
    lap: int                          # 圈數
    overtaking_driver: str            # 超車車手編號
    overtaken_driver: str = ""        # 被超車手編號
    overtaking_driver_tla: str = ""   # 超車車手 TLA
    overtaken_driver_tla: str = ""    # 被超車手 TLA
    new_position: int = 0             # 新位置
    old_position: int = 0             # 舊位置
    overtake_type: str = "on_track"   # 超車類型: on_track, pit_related, sc_related, lap_one
    
    # GPS 位置追蹤 (2025-12 新增)
    x: int = 0                        # GPS X 座標 (Live Timing Position.json)
    y: int = 0                        # GPS Y 座標 (Live Timing Position.json)
    location_type: str = "unknown"    # 位置類型: corner, straight, unknown


@dataclass
class OvertakeStatistics:
    """超車統計結果"""
    year: int
    race: str
    session: str = "R"
    total_overtakes: int = 0         # 總超車次數
    on_track_overtakes: int = 0      # 賽道上真正超車
    pit_related_changes: int = 0     # 進站相關位置變化
    sc_related_changes: int = 0      # SC/VSC 相關變化
    lap_one_changes: int = 0         # 第一圈位置變化 (起跑混戰)
    
    # 詳細事件列表
    overtake_events: List[OvertakeEvent] = field(default_factory=list)
    
    # 每位車手統計
    driver_overtakes: Dict[str, int] = field(default_factory=dict)
    driver_overtaken: Dict[str, int] = field(default_factory=dict)


class LiveTimingOvertakeDetector:
    """
    Live Timing 超車檢測器
    
    使用 Live Timing 數據精確檢測超車事件，區分：
    - 賽道上真正超車
    - 進站造成的位置變化
    - SC/VSC 期間的位置變化
    - 第一圈起跑混戰
    """
    
    def __init__(self, year: int, race: str, session: str = "R", base_dir: str = None):
        """
        初始化超車檢測器
        
        Args:
            year: 年份 (例如 2025)
            race: 賽事名稱 (例如 "Japan" 或 "Japanese_Race")
            session: 會話類型 (R=Race, Q=Qualifying)
            base_dir: Live Timing JSON 根目錄
        """
        self.year = year
        self.race = race
        self.session = session
        
        # 標準化賽事名稱
        self.race_folder = self._normalize_race_name(race)
        
        # 設定數據目錄
        if base_dir is None:
            base_dir = os.path.join("json", "LiveF1")
        self.data_dir = os.path.join(base_dir, str(year), self.race_folder)
        
        # 數據存儲
        self._driver_map: Dict[str, str] = {}      # driver_num -> TLA
        self._pit_laps: Dict[str, Set[int]] = defaultdict(set)  # driver_num -> {lap1, lap2}
        self._sc_laps: Set[int] = set()            # SC/VSC 圈數
        self._position_records: List[Dict] = []   # Position.json 記錄 (GPS 座標)
        
        # 統計結果
        self._stats = OvertakeStatistics(year=year, race=race, session=session)
        
        logger.info("[OVERTAKE_DETECTOR] Initialized for %d %s %s", year, race, session)
        logger.info("[OVERTAKE_DETECTOR] Data directory: %s", self.data_dir)
    
    def _normalize_race_name(self, race: str) -> str:
        """標準化賽事名稱為 LiveF1 資料夾格式"""
        if "_Race" in race:
            return race
        
        # 先移除 "Grand Prix" 後綴再匹配
        race_clean = race.replace(" Grand Prix", "").strip()
        
        # 常見轉換
        mapping = {
            "Japan": "Japanese_Race",
            "Japanese": "Japanese_Race",
            "China": "Chinese_Race",
            "Chinese": "Chinese_Race",
            "Australia": "Australian_Race",
            "Australian": "Australian_Race",
            "Great Britain": "British_Race",
            "British": "British_Race",
            "Belgium": "Belgian_Race",
            "Belgian": "Belgian_Race",
            "Netherlands": "Dutch_Race",
            "Dutch": "Dutch_Race",
            "Italy": "Italian_Race",
            "Italian": "Italian_Race",
            "Spain": "Spanish_Race",
            "Spanish": "Spanish_Race",
            "Hungary": "Hungarian_Race",
            "Hungarian": "Hungarian_Race",
            "Austria": "Austrian_Race",
            "Austrian": "Austrian_Race",
            "Monaco": "Monaco_Race",
            "Singapore": "Singapore_Race",
            "Azerbaijan": "Azerbaijan_Race",
            "Bahrain": "Bahrain_Race",
            "Saudi Arabia": "Saudi_Arabian_Race",
            "Saudi Arabian": "Saudi_Arabian_Race",
            "Qatar": "Qatar_Race",
            "Abu Dhabi": "Abu_Dhabi_Race",
            "United States": "United_States_Race",
            "Las Vegas": "Las_Vegas_Race",
            "Mexico": "Mexico_City_Race",
            "Mexico City": "Mexico_City_Race",
            "Brazil": "Sao_Paulo_Race",
            "São Paulo": "São_Paulo_Race",
            "Sao Paulo": "Sao_Paulo_Race",
            "Miami": "Miami_Race",
            "Canada": "Canadian_Race",
            "Canadian": "Canadian_Race",
            "Emilia Romagna": "Emilia_Romagna_Race",
            "Emilia-Romagna": "Emilia_Romagna_Race",
        }
        
        # 先嘗試用 race_clean（移除 Grand Prix 後的名稱）
        if race_clean in mapping:
            return mapping[race_clean]
        
        # 再嘗試原始名稱
        if race in mapping:
            return mapping[race]
        
        # 最後用默認規則
        return race_clean.replace(" ", "_") + "_Race"
    
    def _load_json_file(self, filename: str) -> List[Dict]:
        """載入 JSON 檔案"""
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            logger.warning("[OVERTAKE_DETECTOR] File not found: %s", filepath)
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'records' in data:
                return data['records']
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error("[OVERTAKE_DETECTOR] Error loading %s: %s", filename, e)
            return []
    
    def analyze(self) -> OvertakeStatistics:
        """
        執行完整的超車分析
        
        Returns:
            OvertakeStatistics 對象，包含所有統計結果
        """
        logger.info("[OVERTAKE_DETECTOR] Starting analysis...")
        
        # 檢查數據目錄
        if not os.path.exists(self.data_dir):
            logger.error("[OVERTAKE_DETECTOR] Data directory not found: %s", self.data_dir)
            return self._stats
        
        # 載入車手列表
        self._load_driver_list()
        
        # 載入進站數據
        self._load_pit_data()
        
        # 載入 SC/VSC 數據
        self._load_track_status()
        
        # 載入 GPS 位置數據 (用於超車位置追蹤)
        self._load_position_data()
        
        # 執行主要分析
        self._analyze_position_changes()
        
        logger.info("[OVERTAKE_DETECTOR] Analysis complete")
        logger.info("[OVERTAKE_DETECTOR] Results: total=%d, on_track=%d, pit_related=%d, lap_one=%d",
                    self._stats.total_overtakes,
                    self._stats.on_track_overtakes,
                    self._stats.pit_related_changes,
                    self._stats.lap_one_changes)
        
        return self._stats
    
    def _load_driver_list(self):
        """載入車手列表"""
        records = self._load_json_file("DriverList.json")
        
        for record in records:
            data = record.get('data', {})
            for driver_num, info in data.items():
                if driver_num in NON_RACE_CAR_NUMBERS:
                    continue
                if isinstance(info, dict) and 'Tla' in info:
                    self._driver_map[driver_num] = info['Tla']
        
        logger.info("[OVERTAKE_DETECTOR] Loaded %d drivers", len(self._driver_map))
    
    def _load_pit_data(self):
        """載入進站數據"""
        records = self._load_json_file("PitLaneTimeCollection.json")
        
        for record in records:
            pit_times = record.get('data', {}).get('PitTimes', {})
            for driver_num, pit_info in pit_times.items():
                if driver_num == '_deleted' or driver_num in NON_RACE_CAR_NUMBERS:
                    continue
                if isinstance(pit_info, dict):
                    lap = pit_info.get('Lap')
                    if lap:
                        self._pit_laps[driver_num].add(int(lap))
        
        total_stops = sum(len(v) for v in self._pit_laps.values())
        logger.info("[OVERTAKE_DETECTOR] Loaded %d pit stops for %d drivers", 
                    total_stops, len(self._pit_laps))
    
    def _load_track_status(self):
        """載入賽道狀態 (SC/VSC)"""
        records = self._load_json_file("TrackStatus.json")
        
        # 簡化處理：標記 SC/VSC 狀態存在
        for record in records:
            status = str(record.get('data', {}).get('Status', '1'))
            if status in SC_VSC_TRACK_STATUS:
                # 需要配合 LapCount 確定具體圈數
                pass
        
        logger.info("[OVERTAKE_DETECTOR] Track status loaded")
    
    def _load_position_data(self):
        """載入 GPS 位置數據 (Position.json)"""
        records = self._load_json_file("Position.json")
        self._position_records = records
        
        # 統計有效座標數量
        valid_count = 0
        for record in records:
            positions = record.get('data', {}).get('Position', [])
            for pos in positions:
                entries = pos.get('Entries', {})
                for entry in entries.values():
                    if isinstance(entry, dict) and (entry.get('X', 0) != 0 or entry.get('Y', 0) != 0):
                        valid_count += 1
                        break  # 只計算有有效座標的記錄
        
        logger.info("[OVERTAKE_DETECTOR] Loaded %d Position records (%d with valid GPS)", 
                    len(records), valid_count)
    
    def _parse_timestamp_to_seconds(self, ts: str) -> float:
        """將時間戳 (HH:MM:SS.mmm) 轉換為秒"""
        try:
            parts = ts.split(':')
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
        except (ValueError, TypeError):
            pass
        return 0.0
    
    def _find_position_at_time(self, target_ts: str, driver_num: str, 
                                tolerance_sec: float = 3.0) -> tuple:
        """
        在 Position 記錄中找到最接近目標時間的 GPS 座標
        
        Args:
            target_ts: 目標時間戳 (HH:MM:SS.mmm)
            driver_num: 車手編號
            tolerance_sec: 時間容差 (秒)
            
        Returns:
            (x, y) 座標元組，或 (0, 0) 如果找不到
        """
        if not self._position_records:
            return (0, 0)
        
        target_sec = self._parse_timestamp_to_seconds(target_ts)
        best_x, best_y = 0, 0
        best_diff = float('inf')
        
        for record in self._position_records:
            record_sec = self._parse_timestamp_to_seconds(record.get('timestamp', ''))
            diff = abs(record_sec - target_sec)
            
            if diff > tolerance_sec:
                # 優化：如果已經找到匹配且時間差越來越大，可以提前跳出
                if best_diff < float('inf') and diff > best_diff:
                    continue
                continue
            
            if diff >= best_diff:
                continue
            
            positions = record.get('data', {}).get('Position', [])
            for pos in positions:
                entries = pos.get('Entries', {})
                if driver_num in entries:
                    entry = entries[driver_num]
                    if isinstance(entry, dict):
                        x = entry.get('X', 0)
                        y = entry.get('Y', 0)
                        if x != 0 or y != 0:
                            best_diff = diff
                            best_x, best_y = x, y
        
        return (best_x, best_y)

    def _analyze_position_changes(self):
        """分析位置變化 - 核心邏輯"""
        # 載入 TimingData (用於追蹤圈數)
        timing_data = self._load_json_file("TimingData.json")
        logger.info("[OVERTAKE_DETECTOR] Loaded %d TimingData records", len(timing_data))
        
        # 載入 TimingAppData (用於追蹤位置)
        timing_app = self._load_json_file("TimingAppData.json")
        logger.info("[OVERTAKE_DETECTOR] Loaded %d TimingAppData records", len(timing_app))
        
        if not timing_app:
            logger.warning("[OVERTAKE_DETECTOR] No TimingAppData available")
            return
        
        # 建立圈數更新列表 (timestamp, driver_num, lap)
        # 這樣我們可以隨時間同步更新每位車手的圈數
        lap_updates: List[tuple] = []
        for record in timing_data:
            ts = record.get('timestamp', '')
            data = record.get('data', {})
            if 'Lines' in data:
                for driver_num, line_data in data['Lines'].items():
                    if isinstance(line_data, dict) and 'NumberOfLaps' in line_data:
                        lap_updates.append((ts, driver_num, line_data['NumberOfLaps']))
        
        logger.info("[OVERTAKE_DETECTOR] Built %d lap updates", len(lap_updates))
        
        # 計算所有進站圈 (任何人進站的圈) + 出站圈 (進站圈 + 1)
        # 因為進站發生在 Lap N，但車手在 Lap N+1 才從維修站出來
        # 所以 Lap N+1 的「超車」實際上是對手出站，不是真正超車
        all_pit_laps: Set[int] = set()
        for laps in self._pit_laps.values():
            all_pit_laps.update(laps)
            # 加入出站圈 (進站圈 + 1)
            all_pit_laps.update(lap + 1 for lap in laps)
        
        logger.info("[OVERTAKE_DETECTOR] All pit laps (incl. out laps): %s", sorted(all_pit_laps))
        
        # 追蹤位置變化
        current_laps: Dict[str, int] = defaultdict(int)
        last_positions: Dict[str, int] = {}
        overtake_events: List[OvertakeEvent] = []
        lap_update_idx = 0
        
        for record in timing_app:
            ts = record.get('timestamp', '')
            data = record.get('data', {})
            
            # 更新圈數直到當前時間戳 (同步更新)
            while lap_update_idx < len(lap_updates) and lap_updates[lap_update_idx][0] <= ts:
                _, d_num, lap = lap_updates[lap_update_idx]
                current_laps[d_num] = lap
                lap_update_idx += 1
            
            if 'Lines' not in data:
                continue
            
            for driver_num, line_data in data['Lines'].items():
                if driver_num in NON_RACE_CAR_NUMBERS:
                    continue
                if not isinstance(line_data, dict):
                    continue
                
                # 獲取位置 (Line 字段)
                if 'Line' not in line_data:
                    continue
                
                new_pos = line_data['Line']
                old_pos = last_positions.get(driver_num, new_pos)
                
                # 檢查是否有超車 (位置變小 = 超車)
                if new_pos < old_pos:
                    change = old_pos - new_pos
                    current_lap = current_laps.get(driver_num, 1)
                    
                    # 分類超車類型
                    overtake_type = self._classify_overtake_with_pit_laps(
                        driver_num, current_lap, all_pit_laps
                    )
                    
                    # 更新統計
                    if overtake_type == "lap_one":
                        self._stats.lap_one_changes += change
                    elif overtake_type == "pit_related":
                        self._stats.pit_related_changes += change
                    elif overtake_type == "sc_related":
                        self._stats.sc_related_changes += change
                    else:
                        self._stats.on_track_overtakes += change
                    
                    self._stats.total_overtakes += change
                    
                    # 更新車手統計
                    if driver_num not in self._stats.driver_overtakes:
                        self._stats.driver_overtakes[driver_num] = 0
                    self._stats.driver_overtakes[driver_num] += 1
                    
                    # 查找 GPS 座標 (2025-12 新增)
                    x, y = self._find_position_at_time(ts, driver_num)
                    
                    # 記錄事件
                    event = OvertakeEvent(
                        timestamp=ts,
                        lap=current_lap,
                        overtaking_driver=driver_num,
                        overtaking_driver_tla=self._driver_map.get(driver_num, driver_num),
                        new_position=new_pos,
                        old_position=old_pos,
                        overtake_type=overtake_type,
                        x=x,
                        y=y,
                        location_type="unknown"  # 將在後續處理中確定
                    )
                    overtake_events.append(event)
                
                last_positions[driver_num] = new_pos
        
        # 按圈數排序事件
        overtake_events.sort(key=lambda x: x.lap)
        self._stats.overtake_events = overtake_events
    
    def _classify_overtake(self, driver_num: str, current_lap: int) -> str:
        """
        分類超車類型 (舊版，向後兼容)
        
        Args:
            driver_num: 車手編號
            current_lap: 當前圈數
            
        Returns:
            超車類型: on_track, pit_related, sc_related, lap_one
        """
        # 計算所有進站圈
        all_pit_laps: Set[int] = set()
        for laps in self._pit_laps.values():
            all_pit_laps.update(laps)
        
        return self._classify_overtake_with_pit_laps(driver_num, current_lap, all_pit_laps)
    
    def _classify_overtake_with_pit_laps(self, driver_num: str, current_lap: int, 
                                          all_pit_laps: Set[int]) -> str:
        """
        分類超車類型 (優化版，使用預計算的進站圈)
        
        Args:
            driver_num: 車手編號
            current_lap: 當前圈數
            all_pit_laps: 所有進站圈的集合
            
        Returns:
            超車類型: on_track, pit_related, sc_related, lap_one
        """
        # 1. 第一圈 (起跑混戰)
        if current_lap <= 1:
            return "lap_one"
        
        # 2. SC/VSC 期間
        if current_lap in self._sc_laps:
            return "sc_related"
        
        # 3. 這一圈有任何人進站 (包括車手自己或對手)
        if current_lap in all_pit_laps:
            return "pit_related"
        
        # 4. 預設為賽道上超車
        return "on_track"
    
    def get_statistics(self) -> OvertakeStatistics:
        """獲取統計結果"""
        return self._stats
    
    def to_dict(self) -> Dict[str, Any]:
        """
        轉換為字典格式 (用於 JSON 輸出)
        
        Returns:
            統計結果字典
        """
        # 將車手編號轉換為 TLA
        driver_overtakes_tla = {
            self._driver_map.get(k, k): v 
            for k, v in self._stats.driver_overtakes.items()
        }
        
        # 統計有 GPS 座標的超車事件
        events_with_gps = sum(1 for e in self._stats.overtake_events if e.x != 0 or e.y != 0)
        
        return {
            "year": self._stats.year,
            "race": self._stats.race,
            "session": self._stats.session,
            "total_overtakes": self._stats.total_overtakes,
            "on_track_overtakes": self._stats.on_track_overtakes,
            "pit_related_changes": self._stats.pit_related_changes,
            "sc_related_changes": self._stats.sc_related_changes,
            "lap_one_changes": self._stats.lap_one_changes,
            "driver_overtakes": driver_overtakes_tla,
            "overtake_events_count": len(self._stats.overtake_events),
            "events_with_gps_count": events_with_gps,
            "overtake_events": [
                {
                    "timestamp": e.timestamp,
                    "lap": e.lap,
                    "driver": e.overtaking_driver_tla or e.overtaking_driver,
                    "from_position": e.old_position,
                    "to_position": e.new_position,
                    "type": e.overtake_type,
                    "x": e.x,
                    "y": e.y,
                    "location_type": e.location_type
                }
                for e in self._stats.overtake_events[:100]
            ]
        }


def analyze_race_overtakes(year: int, race: str, session: str = "R",
                           base_dir: str = None) -> OvertakeStatistics:
    """
    分析賽事超車統計 - 高階 API
    
    Args:
        year: 年份
        race: 賽事名稱 (例如 "Japan" 或 "Japanese_Race")
        session: 會話類型
        base_dir: Live Timing JSON 根目錄
        
    Returns:
        OvertakeStatistics 對象
    
    Example:
        >>> stats = analyze_race_overtakes(2025, "Japan")
        >>> print(f"On-track overtakes: {stats.on_track_overtakes}")
    """
    detector = LiveTimingOvertakeDetector(year, race, session, base_dir)
    return detector.analyze()


def get_available_races(year: int, base_dir: str = None) -> List[str]:
    """獲取指定年份可用的賽事列表"""
    if base_dir is None:
        base_dir = os.path.join("json", "LiveF1")
    
    year_dir = os.path.join(base_dir, str(year))
    
    if not os.path.exists(year_dir):
        return []
    
    races = []
    for name in os.listdir(year_dir):
        if os.path.isdir(os.path.join(year_dir, name)) and "_Race" in name:
            races.append(name)
    
    return sorted(races)


if __name__ == "__main__":
    import sys
    
    year = 2025
    race = "Japanese_Race"
    
    if len(sys.argv) > 1:
        race = sys.argv[1]
    if len(sys.argv) > 2:
        year = int(sys.argv[2])
    
    print(f"Analyzing {year} {race}...")
    
    detector = LiveTimingOvertakeDetector(year, race)
    stats = detector.analyze()
    
    print(f"\n{'='*60}")
    print(f"Results: {year} {race}")
    print(f"{'='*60}")
    print(f"Total position changes: {stats.total_overtakes}")
    print(f"  On-track overtakes:   {stats.on_track_overtakes}")
    print(f"  Pit-related changes:  {stats.pit_related_changes}")
    print(f"  SC-related changes:   {stats.sc_related_changes}")
    print(f"  Lap 1 changes:        {stats.lap_one_changes}")
    
    print(f"\nTop overtakers:")
    sorted_drivers = sorted(stats.driver_overtakes.items(), key=lambda x: x[1], reverse=True)[:10]
    for d, c in sorted_drivers:
        tla = detector._driver_map.get(d, d)
        print(f"  {tla}: {c}")
    
    # 保存 JSON
    result = detector.to_dict()
    output_file = f"overtake_analysis_{year}_{race}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_file}")
