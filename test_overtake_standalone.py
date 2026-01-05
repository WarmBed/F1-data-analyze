"""測試超車 GPS 功能 + 視覺化 - 獨立運行版本"""
# 此檔案可以獨立運行，不依賴任何模組導入

import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

# =============================================================================
# Constants
# =============================================================================

SC_VSC_TRACK_STATUS = {'4', '6', '7'}
NON_RACE_CAR_NUMBERS = {'241', '242', '243'}


class SimpleLogger:
    def info(self, msg, *args): print(f"[INFO] {msg % args if args else msg}")
    def debug(self, msg, *args): pass
    def warning(self, msg, *args): print(f"[WARN] {msg % args if args else msg}")
    def error(self, msg, *args): print(f"[ERROR] {msg % args if args else msg}")

logger = SimpleLogger()


@dataclass
class OvertakeEvent:
    """單次超車事件"""
    timestamp: str
    lap: int
    overtaking_driver: str
    overtaken_driver: str = ""
    overtaking_driver_tla: str = ""
    overtaken_driver_tla: str = ""
    new_position: int = 0
    old_position: int = 0
    overtake_type: str = "on_track"
    x: int = 0
    y: int = 0
    location_type: str = "unknown"


@dataclass
class OvertakeStatistics:
    """超車統計結果"""
    year: int
    race: str
    session: str = "R"
    total_overtakes: int = 0
    on_track_overtakes: int = 0
    pit_related_changes: int = 0
    sc_related_changes: int = 0
    lap_one_changes: int = 0
    overtake_events: List[OvertakeEvent] = field(default_factory=list)
    driver_overtakes: Dict[str, int] = field(default_factory=dict)
    driver_overtaken: Dict[str, int] = field(default_factory=dict)


class LiveTimingOvertakeDetector:
    def __init__(self, year: int, race: str, session: str = "R", base_dir: str = None):
        self.year = year
        self.race = race
        self.session = session
        self.race_folder = self._normalize_race_name(race)
        
        if base_dir is None:
            base_dir = os.path.join("json", "LiveF1")
        self.data_dir = os.path.join(base_dir, str(year), self.race_folder)
        
        self._driver_map: Dict[str, str] = {}
        self._pit_laps: Dict[str, Set[int]] = defaultdict(set)
        self._sc_laps: Set[int] = set()
        self._position_records: List[Dict] = []
        self._stats = OvertakeStatistics(year=year, race=race, session=session)
        
        logger.info("[OVERTAKE_DETECTOR] Initialized for %d %s %s", year, race, session)

    def _normalize_race_name(self, race: str) -> str:
        if "_Race" in race:
            return race
        race_clean = race.replace(" Grand Prix", "").strip()
        mapping = {
            "Abu Dhabi": "Abu_Dhabi_Race",
            "Japan": "Japanese_Race",
            "Australia": "Australian_Race",
        }
        if race_clean in mapping:
            return mapping[race_clean]
        if race in mapping:
            return mapping[race]
        return race_clean.replace(" ", "_") + "_Race"

    def _load_json_file(self, filename: str) -> List[Dict]:
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

    def _parse_timestamp_to_seconds(self, ts: str) -> float:
        try:
            parts = ts.split(':')
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
        except:
            pass
        return 0.0

    def _find_position_at_time(self, target_ts: str, driver_num: str, tolerance_sec: float = 3.0) -> tuple:
        if not self._position_records:
            return (0, 0)
        
        target_sec = self._parse_timestamp_to_seconds(target_ts)
        best_x, best_y = 0, 0
        best_diff = float('inf')
        
        for record in self._position_records:
            record_sec = self._parse_timestamp_to_seconds(record.get('timestamp', ''))
            diff = abs(record_sec - target_sec)
            
            if diff > tolerance_sec or diff >= best_diff:
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

    def analyze(self) -> OvertakeStatistics:
        logger.info("[OVERTAKE_DETECTOR] Starting analysis...")
        
        if not os.path.exists(self.data_dir):
            logger.error("[OVERTAKE_DETECTOR] Data directory not found: %s", self.data_dir)
            return self._stats
        
        # 載入車手列表
        for record in self._load_json_file("DriverList.json"):
            data = record.get('data', {})
            for driver_num, info in data.items():
                if driver_num in NON_RACE_CAR_NUMBERS:
                    continue
                if isinstance(info, dict) and 'Tla' in info:
                    self._driver_map[driver_num] = info['Tla']
        
        logger.info("[OVERTAKE_DETECTOR] Loaded %d drivers", len(self._driver_map))
        
        # 載入進站數據
        for record in self._load_json_file("PitLaneTimeCollection.json"):
            pit_times = record.get('data', {}).get('PitTimes', {})
            for driver_num, pit_info in pit_times.items():
                if driver_num == '_deleted' or driver_num in NON_RACE_CAR_NUMBERS:
                    continue
                if isinstance(pit_info, dict):
                    lap = pit_info.get('Lap')
                    if lap:
                        self._pit_laps[driver_num].add(int(lap))
        
        # 載入 GPS 位置數據
        self._position_records = self._load_json_file("Position.json")
        logger.info("[OVERTAKE_DETECTOR] Loaded %d Position records", len(self._position_records))
        
        # 執行主要分析
        timing_data = self._load_json_file("TimingData.json")
        timing_app = self._load_json_file("TimingAppData.json")
        
        # 建立圈數更新列表
        lap_updates: List[tuple] = []
        for record in timing_data:
            ts = record.get('timestamp', '')
            data = record.get('data', {})
            if 'Lines' in data:
                for driver_num, line_data in data['Lines'].items():
                    if isinstance(line_data, dict) and 'NumberOfLaps' in line_data:
                        lap_updates.append((ts, driver_num, line_data['NumberOfLaps']))
        
        all_pit_laps: Set[int] = set()
        for laps in self._pit_laps.values():
            all_pit_laps.update(laps)
            # 加入出站圈 (進站圈 + 1)
            all_pit_laps.update(lap + 1 for lap in laps)
        
        current_laps: Dict[str, int] = defaultdict(int)
        last_positions: Dict[str, int] = {}
        overtake_events: List[OvertakeEvent] = []
        lap_update_idx = 0
        
        for record in timing_app:
            ts = record.get('timestamp', '')
            data = record.get('data', {})
            
            while lap_update_idx < len(lap_updates) and lap_updates[lap_update_idx][0] <= ts:
                _, d_num, lap = lap_updates[lap_update_idx]
                current_laps[d_num] = lap
                lap_update_idx += 1
            
            if 'Lines' not in data:
                continue
            
            for driver_num, line_data in data['Lines'].items():
                if driver_num in NON_RACE_CAR_NUMBERS or not isinstance(line_data, dict):
                    continue
                if 'Line' not in line_data:
                    continue
                
                new_pos = line_data['Line']
                old_pos = last_positions.get(driver_num, new_pos)
                
                if new_pos < old_pos:
                    change = old_pos - new_pos
                    current_lap = current_laps.get(driver_num, 1)
                    
                    # 分類
                    if current_lap <= 1:
                        overtake_type = "lap_one"
                        self._stats.lap_one_changes += change
                    elif current_lap in all_pit_laps:
                        overtake_type = "pit_related"
                        self._stats.pit_related_changes += change
                    else:
                        overtake_type = "on_track"
                        self._stats.on_track_overtakes += change
                    
                    self._stats.total_overtakes += change
                    
                    # 查找 GPS 座標
                    x, y = self._find_position_at_time(ts, driver_num)
                    
                    event = OvertakeEvent(
                        timestamp=ts,
                        lap=current_lap,
                        overtaking_driver=driver_num,
                        overtaking_driver_tla=self._driver_map.get(driver_num, driver_num),
                        new_position=new_pos,
                        old_position=old_pos,
                        overtake_type=overtake_type,
                        x=x,
                        y=y
                    )
                    overtake_events.append(event)
                
                last_positions[driver_num] = new_pos
        
        overtake_events.sort(key=lambda e: e.lap)
        self._stats.overtake_events = overtake_events
        
        logger.info("[OVERTAKE_DETECTOR] Analysis complete")
        return self._stats


# =============================================================================
# 主程式
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("測試 Abu Dhabi 2025 超車位置追蹤")
    print("=" * 60)
    
    detector = LiveTimingOvertakeDetector(2025, "Abu Dhabi", "R")
    stats = detector.analyze()
    
    print(f"\n統計結果:")
    print(f"  總超車: {stats.total_overtakes}")
    print(f"  賽道超車: {stats.on_track_overtakes}")
    print(f"  進站相關: {stats.pit_related_changes}")
    print(f"  第一圈: {stats.lap_one_changes}")
    
    # 只統計真正的賽道超車 (排除進站相關和第一圈)
    on_track_events = [e for e in stats.overtake_events if e.overtake_type == "on_track"]
    on_track_with_gps = [e for e in on_track_events if e.x != 0 or e.y != 0]
    
    print(f"\n超車事件分類統計:")
    print(f"  總事件數: {len(stats.overtake_events)}")
    print(f"  第一圈: {len([e for e in stats.overtake_events if e.overtake_type == 'lap_one'])}")
    print(f"  進站相關: {len([e for e in stats.overtake_events if e.overtake_type == 'pit_related'])}")
    print(f"  真正賽道超車: {len(on_track_events)}")
    
    print(f"\n真正賽道超車 GPS 統計:")
    print(f"  有 GPS 座標: {len(on_track_with_gps)}")
    if on_track_events:
        print(f"  GPS 覆蓋率: {len(on_track_with_gps) / len(on_track_events) * 100:.1f}%")
    
    print(f"\n前 10 個真正賽道超車事件:")
    for i, e in enumerate(on_track_with_gps[:10]):
        print(f"  {i+1}. Lap {e.lap:2d} | {e.overtaking_driver_tla:3s} | P{e.old_position}→P{e.new_position} | GPS: ({e.x:5d}, {e.y:5d})")
    
    # 統計超車熱點 - 只使用真正的賽道超車
    print(f"\n真正賽道超車熱點分析 (排除進站/第一圈):")
    location_counts: Dict[tuple, int] = {}
    for e in on_track_with_gps:
        key = (round(e.x / 200) * 200, round(e.y / 200) * 200)
        location_counts[key] = location_counts.get(key, 0) + 1
    
    # 排序取前 10 個熱點
    hotspots = sorted(location_counts.items(), key=lambda x: -x[1])[:10]
    for i, ((x, y), count) in enumerate(hotspots):
        print(f"  {i+1}. GPS ({x:5d}, {y:5d}): {count} 次超車")
    
    print("\n測試完成!")
