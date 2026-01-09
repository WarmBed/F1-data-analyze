# -*- coding: utf-8 -*-
"""
F134: 超車事件歷史收集器 (Overtake History Collector)
=====================================================

目的: 從 PKL 快取提取 2024-2025 所有超車事件
數據來源: data/live_timing_cache/2025/*.pkl

繼承: BaseOvertakeDetector - 統一的超車分類邏輯

超車分類標準（與 F100 一致）：
  1. on_track     - 賽道上真正的超車
  2. pit_related  - 進站相關的位置變化
  3. sc_related   - SC/VSC 期間的位置變化
  4. lap_one      - 第一圈起跑混戰

輸出: json/overtake_events_history_2024_2025.json

建立日期: 2026-01-05
更新日期: 2026-01-05 (重構繼承 BaseOvertakeDetector)
"""

import os
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

# 導入基類
from CLI_modules.cli.utils.base_overtake_detector import (
    BaseOvertakeDetector,
    OvertakeEvent,
    OvertakeStatistics,
    OvertakeType,
    SC_VSC_STATUS_CODES
)


class PKLOvertakeDetector(BaseOvertakeDetector):
    """
    基於 PKL 快取的超車偵測器
    
    繼承 BaseOvertakeDetector，使用 PKL 作為數據源
    """
    
    def __init__(
        self, 
        year: int, 
        race: str, 
        session: str = "R",
        cache_dir: str = "data/live_timing_cache"
    ):
        """
        初始化 PKL 超車偵測器
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型
            cache_dir: PKL 快取目錄
        """
        super().__init__(year, race, session)
        
        self.cache_dir = Path(cache_dir)
        self.pkl_path: Optional[Path] = None
        
        # PKL 數據
        self._snapshots: List[Dict] = []
        self._driver_stints: Dict[str, List] = {}
        self._race_info: Dict = {}
        
        # 賽道名稱
        self.track_name = self._extract_track_name(race)
        
    def _extract_track_name(self, race_name: str) -> str:
        """從賽事名稱提取賽道名稱"""
        # 格式: "2025_Japanese_Race" -> "Japanese"
        if "_Race" in race_name:
            parts = race_name.split('_')
            track_parts = [p for p in parts if p != 'Race' and not p.isdigit()]
            return '_'.join(track_parts)
        return race_name
    
    def _find_pkl_file(self) -> Optional[Path]:
        """找到對應的 PKL 檔案"""
        season_dir = self.cache_dir / str(self.year)
        if not season_dir.exists():
            return None
        
        # 嘗試多種命名格式
        patterns = [
            f"{self.year}_{self.race}.pkl",
            f"{self.race}.pkl",
            f"*{self.race}*.pkl"
        ]
        
        for pattern in patterns:
            matches = list(season_dir.glob(pattern))
            if matches:
                return matches[0]
        
        return None
    
    def load_data(self) -> bool:
        """
        載入 PKL 數據
        
        Returns:
            是否成功載入
        """
        self.pkl_path = self._find_pkl_file()
        if not self.pkl_path or not self.pkl_path.exists():
            print(f"[F134] PKL file not found for {self.year} {self.race}")
            return False
        
        print(f"[F134] Loading: {self.pkl_path.name}")
        
        try:
            with open(self.pkl_path, 'rb') as f:
                data = pickle.load(f)
        except Exception as e:
            print(f"[F134] Error loading PKL: {e}")
            return False
        
        self._snapshots = data.get('snapshots', [])
        self._driver_stints = data.get('driver_stints', {})
        self._race_info = data.get('race_info', {})
        
        # 載入車手資訊
        driver_info_raw = data.get('driver_info', {})
        for driver_num, info in driver_info_raw.items():
            self._driver_info[driver_num] = {
                "tla": info.get('driver_tla', driver_num),
                "team": info.get('team_name', '')
            }
        
        # 從 snapshots 提取進站圈數
        self._extract_pit_laps_from_snapshots()
        
        # 從 snapshots 提取 SC/VSC 圈數
        self._extract_sc_laps_from_snapshots()
        
        print(f"[F134]   - {len(self._snapshots)} snapshots")
        print(f"[F134]   - {len(self._driver_info)} drivers")
        print(f"[F134]   - Pit laps: {sorted(self._calculate_all_pit_laps())[:10]}...")
        print(f"[F134]   - SC laps: {sorted(self._sc_laps)}")
        
        return len(self._snapshots) > 0
    
    def _extract_pit_laps_from_snapshots(self):
        """從 snapshots 提取進站圈數"""
        driver_pit_detected: Dict[str, Set[int]] = defaultdict(set)
        
        for snapshot in self._snapshots:
            drivers = snapshot.get('drivers', {})
            current_lap = snapshot.get('current_lap', 0)
            
            for driver_num, driver_data in drivers.items():
                # 檢查進站狀態
                in_pit = driver_data.get('in_pit', False)
                pit_out = driver_data.get('pit_out', False)
                
                if in_pit or pit_out:
                    driver_pit_detected[driver_num].add(current_lap)
        
        self._pit_laps = dict(driver_pit_detected)
    
    def _extract_sc_laps_from_snapshots(self):
        """從 snapshots 提取 SC/VSC 圈數 (舊方法，保留相容性)"""
        for snapshot in self._snapshots:
            track_status = snapshot.get('track_status', 1)
            current_lap = snapshot.get('current_lap', 0)
            
            # 檢查是否為 SC/VSC 狀態
            if isinstance(track_status, (int, str)):
                status_code = int(track_status) if str(track_status).isdigit() else 1
                if status_code in SC_VSC_STATUS_CODES:
                    self._sc_laps.add(current_lap)
    
    def extract_sc_laps_from_track_status(self, track_status_events: List[Dict]):
        """
        從 PKL 頂層的 track_status 事件列表提取 SC/VSC 圈數
        
        Args:
            track_status_events: PKL 頂層的 track_status 列表
        """
        if not track_status_events or not self._snapshots:
            return
        
        # 建立 race_time -> current_lap 映射
        time_to_lap = {}
        for snapshot in self._snapshots[::50]:  # 每 50 個取樣
            race_time = snapshot.get('race_time', '')
            current_lap = snapshot.get('current_lap', 0)
            if race_time:
                time_to_lap[race_time] = current_lap
        
        # 解析 track_status 事件
        for event in track_status_events:
            status = event.get('data', {}).get('Status', '1')
            timestamp = event.get('timestamp', '')
            
            # 檢查是否為 SC/VSC 狀態 (4=SC, 6=VSC, 7=VSC Ending)
            if status in {'4', '6', '7'}:
                # 找到最接近的圈數
                lap = self._find_lap_for_timestamp(timestamp)
                if lap > 0:
                    self._sc_laps.add(lap)
    
    def _find_lap_for_timestamp(self, timestamp: str) -> int:
        """
        根據 timestamp 找到對應的圈數
        
        Args:
            timestamp: 格式 HH:MM:SS.mmm
            
        Returns:
            對應的圈數，找不到返回 0
        """
        if not timestamp or not self._snapshots:
            return 0
        
        # 解析 timestamp
        try:
            parts = timestamp.split(':')
            if len(parts) == 3:
                h, m, s = parts
                target_sec = int(h) * 3600 + int(m) * 60 + float(s)
            else:
                return 0
        except (ValueError, TypeError):
            return 0
        
        # 二分搜索找到最接近的 snapshot
        best_lap = 0
        best_diff = float('inf')
        
        for snapshot in self._snapshots[::100]:  # 每 100 個取樣
            race_time = snapshot.get('race_time', '')
            current_lap = snapshot.get('current_lap', 0)
            
            if not race_time:
                continue
            
            try:
                parts = race_time.split(':')
                if len(parts) == 3:
                    h, m, s = parts
                    snap_sec = int(h) * 3600 + int(m) * 60 + float(s)
                    diff = abs(snap_sec - target_sec)
                    if diff < best_diff:
                        best_diff = diff
                        best_lap = current_lap
            except (ValueError, TypeError):
                continue
        
        return best_lap
    
    def detect_overtakes(self) -> List[OvertakeEvent]:
        """
        偵測所有超車事件
        
        Returns:
            超車事件列表
        """
        if not self._snapshots:
            return []
        
        events = []
        prev_positions: Dict[str, Dict] = {}
        
        # 預計算所有進站圈
        all_pit_laps = self._calculate_all_pit_laps()
        
        # 采樣間隔：每 10 個快照檢查一次，提升效能
        sample_interval = 10
        total_snapshots = len(self._snapshots)
        
        for i in range(0, total_snapshots, sample_interval):
            snapshot = self._snapshots[i]
            drivers = snapshot.get('drivers', {})
            race_time = snapshot.get('race_time', '')
            current_lap = snapshot.get('current_lap', 0)
            
            # 建立當前位置映射
            current_positions = self._build_position_map(drivers)
            
            # 偵測位置變化 (超車)
            if prev_positions:
                snapshot_events = self._detect_position_changes(
                    prev_positions,
                    current_positions,
                    race_time,
                    current_lap,
                    all_pit_laps
                )
                events.extend(snapshot_events)
            
            prev_positions = current_positions
        
        return events
    
    def _build_position_map(self, drivers: Dict) -> Dict[str, Dict]:
        """建立當前位置映射"""
        position_map = {}
        
        for driver_num, driver_data in drivers.items():
            pos = driver_data.get('position')
            if pos is not None:
                position_map[driver_num] = {
                    'position': pos,
                    'driver_tla': driver_data.get('driver_tla', ''),
                    'team_name': driver_data.get('team_name', ''),
                    'speed': driver_data.get('speed', 0),
                    'drs': driver_data.get('drs', 0),
                    'gap_to_leader': driver_data.get('gap_to_leader', 0),
                    'gap_to_ahead': driver_data.get('gap_to_ahead'),
                    'lap': driver_data.get('lap', 0),
                    'x': driver_data.get('x', 0),
                    'y': driver_data.get('y', 0),
                    'in_pit': driver_data.get('in_pit', False),
                    'pit_out': driver_data.get('pit_out', False)
                }
        
        return position_map
    
    def _detect_position_changes(
        self,
        prev_positions: Dict[str, Dict],
        current_positions: Dict[str, Dict],
        race_time: str,
        current_lap: int,
        all_pit_laps: Set[int]
    ) -> List[OvertakeEvent]:
        """偵測兩個快照之間的超車事件"""
        events = []
        
        for driver_num, curr_data in current_positions.items():
            if driver_num not in prev_positions:
                continue
            
            prev_data = prev_positions[driver_num]
            prev_pos = prev_data['position']
            curr_pos = curr_data['position']
            
            # 位置提升 (數字變小) = 超車成功
            if curr_pos < prev_pos:
                # 檢查進站狀態 (使用基類方法)
                attacker_in_pit = self.is_driver_in_pit(
                    driver_num, current_lap,
                    curr_data.get('in_pit', False),
                    curr_data.get('pit_out', False)
                )
                
                if attacker_in_pit:
                    continue
                
                # 找出被超車的車手
                defender_info = self._find_defender(
                    driver_num, prev_pos, curr_pos, 
                    prev_positions, current_positions,
                    current_lap
                )
                
                if defender_info:
                    # 分類超車類型 (使用基類方法)
                    overtake_type = self.classify_overtake(
                        driver_num,
                        defender_info['driver_num'],
                        current_lap,
                        all_pit_laps
                    )
                    
                    # 獲取輪胎資訊
                    attacker_tyre = self._get_tyre_info(driver_num)
                    defender_tyre = self._get_tyre_info(defender_info['driver_num'])
                    
                    # 建立事件
                    event = OvertakeEvent(
                        race=f"{self.year}_{self.race}",
                        track=self.track_name,
                        lap=current_lap,
                        timestamp=race_time,
                        overtake_type=overtake_type,
                        overtake_success=True,
                        # 攻擊者資訊
                        attacker_driver=curr_data['driver_tla'],
                        attacker_driver_num=driver_num,
                        attacker_team=curr_data['team_name'],
                        attacker_position_before=prev_pos,
                        attacker_position_after=curr_pos,
                        attacker_tyre_compound=attacker_tyre.get('compound', 'UNKNOWN'),
                        attacker_tyre_age=attacker_tyre.get('age', 0),
                        attacker_speed=curr_data['speed'],
                        attacker_drs_active=curr_data['drs'] > 0,
                        # 防守者資訊
                        defender_driver=defender_info['driver_tla'],
                        defender_driver_num=defender_info['driver_num'],
                        defender_team=defender_info['team_name'],
                        defender_position_before=defender_info['prev_pos'],
                        defender_position_after=defender_info['curr_pos'],
                        defender_tyre_compound=defender_tyre.get('compound', 'UNKNOWN'),
                        defender_tyre_age=defender_tyre.get('age', 0),
                        defender_speed=defender_info['speed'],
                        # 間距
                        gap_before_s=self.parse_gap(prev_data.get('gap_to_ahead')),
                        gap_after_s=self.parse_gap(curr_data.get('gap_to_ahead')),
                        # GPS
                        x=curr_data.get('x', 0),
                        y=curr_data.get('y', 0)
                    )
                    
                    # 更新統計 (使用基類方法)
                    self.update_statistics(event)
                    events.append(event)
        
        return events
    
    def _find_defender(
        self,
        attacker_num: str,
        prev_pos: int,
        curr_pos: int,
        prev_positions: Dict[str, Dict],
        current_positions: Dict[str, Dict],
        current_lap: int
    ) -> Optional[Dict]:
        """找出被超車的車手"""
        target_pos = curr_pos  # 超車者現在的位置
        
        for driver_num, prev_data in prev_positions.items():
            if driver_num == attacker_num:
                continue
            
            # 這個車手原本在超車者要去的位置
            if prev_data['position'] == target_pos:
                # 確認這個車手現在位置掉了
                if driver_num in current_positions:
                    curr_data = current_positions[driver_num]
                    if curr_data['position'] > prev_data['position']:
                        # 檢查防守者是否在進站
                        defender_in_pit = self.is_driver_in_pit(
                            driver_num, current_lap,
                            curr_data.get('in_pit', False),
                            curr_data.get('pit_out', False)
                        )
                        
                        if defender_in_pit:
                            continue
                        
                        return {
                            'driver_num': driver_num,
                            'driver_tla': prev_data['driver_tla'],
                            'team_name': prev_data['team_name'],
                            'prev_pos': prev_data['position'],
                            'curr_pos': curr_data['position'],
                            'speed': curr_data.get('speed', 0)
                        }
        
        return None
    
    def _get_tyre_info(self, driver_num: str) -> Dict:
        """獲取車手當前輪胎資訊"""
        stints = self._driver_stints.get(driver_num, [])
        if stints:
            last_stint = stints[-1]
            return {
                'compound': last_stint.get('compound', 'UNKNOWN'),
                'age': last_stint.get('total_laps', 0)
            }
        return {'compound': 'UNKNOWN', 'age': 0}


class OvertakeHistoryCollector:
    """
    超車事件歷史收集器
    
    收集多場比賽的超車事件並彙整統計
    """
    
    def __init__(self, cache_dir: str = "data/live_timing_cache"):
        """初始化收集器"""
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path("json")
        self.output_dir.mkdir(exist_ok=True)
        
        # 統計數據
        self.total_overtakes = 0
        self.races_processed = 0
        
        # 彙整統計
        self.driver_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_attacks": 0,
            "successful_attacks": 0,
            "total_defenses": 0,
            "successful_defenses": 0,
            "team": ""
        })
        self.team_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_attacks": 0,
            "successful_attacks": 0,
            "total_defenses": 0,
            "successful_defenses": 0
        })
        self.track_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_overtakes": 0,
            "on_track_overtakes": 0,
            "pit_related": 0,
            "sc_related": 0,
            "lap_one": 0,
            "total_laps": 0,
            "races_analyzed": 0
        })
    
    def collect_all_races(self, seasons: List[int] = None) -> Dict[str, Any]:
        """收集所有比賽的超車事件"""
        if seasons is None:
            seasons = [2024, 2025]
        
        all_events = []
        
        for season in seasons:
            season_dir = self.cache_dir / str(season)
            if not season_dir.exists():
                print(f"[F134] Season {season} directory not found: {season_dir}")
                continue
            
            # 找出所有 Race PKL 檔案
            race_files = list(season_dir.glob("*_Race.pkl"))
            print(f"[F134] Found {len(race_files)} race files for {season}")
            
            for race_file in race_files:
                try:
                    events = self._process_race_file(race_file, season)
                    all_events.extend(events)
                    self.races_processed += 1
                except Exception as e:
                    print(f"[F134] Error processing {race_file.name}: {e}")
        
        # 建立完整的輸出結構
        result = self._build_output_structure(all_events, seasons)
        
        # 儲存到 JSON
        output_file = self.output_dir / "overtake_events_history_2024_2025.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n[F134] Collection complete!")
        print(f"  - Races processed: {self.races_processed}")
        print(f"  - Total overtakes: {self.total_overtakes}")
        print(f"  - Output: {output_file}")
        
        return result
    
    def _process_race_file(self, race_file: Path, season: int) -> List[Dict]:
        """處理單一比賽的 PKL 檔案"""
        race_name = race_file.stem  # e.g., "2025_Japanese_Race"
        
        # 使用 PKLOvertakeDetector
        detector = PKLOvertakeDetector(
            year=season,
            race=race_name,
            session="R",
            cache_dir=str(self.cache_dir)
        )
        
        # 直接設定 pkl_path
        detector.pkl_path = race_file
        
        # 載入數據
        try:
            with open(race_file, 'rb') as f:
                data = pickle.load(f)
        except Exception as e:
            print(f"[F134] Error loading {race_file.name}: {e}")
            return []
        
        detector._snapshots = data.get('snapshots', [])
        detector._driver_stints = data.get('driver_stints', {})
        detector._race_info = data.get('race_info', {})
        
        # 載入車手資訊
        driver_info_raw = data.get('driver_info', {})
        for driver_num, info in driver_info_raw.items():
            detector._driver_info[driver_num] = {
                "tla": info.get('driver_tla', driver_num),
                "team": info.get('team_name', '')
            }
        
        # 提取進站圈數
        detector._extract_pit_laps_from_snapshots()
        
        # 提取 SC/VSC 圈數 (使用頂層 track_status)
        track_status_events = data.get('track_status', [])
        detector.extract_sc_laps_from_track_status(track_status_events)
        
        print(f"[F134] Processing: {race_file.name}")
        print(f"[F134]   - {len(detector._snapshots)} snapshots")
        print(f"[F134]   - SC/VSC laps: {sorted(detector._sc_laps)}" if detector._sc_laps else "[F134]   - No SC/VSC")
        
        # 偵測超車
        events = detector.detect_overtakes()
        
        # 更新彙整統計
        self._update_aggregate_stats(detector, race_name)
        
        # 轉換為字典格式
        event_dicts = [e.to_dict() for e in events]
        
        print(f"[F134]   - Found {len(events)} overtakes:")
        stats = detector.get_statistics()
        print(f"[F134]     on_track={stats.on_track_overtakes}, "
              f"pit_related={stats.pit_related_changes}, "
              f"sc_related={stats.sc_related_changes}, "
              f"lap_one={stats.lap_one_changes}")
        
        return event_dicts
    
    def _update_aggregate_stats(self, detector: PKLOvertakeDetector, race_name: str):
        """更新彙整統計"""
        stats = detector.get_statistics()
        track = detector.track_name
        
        self.total_overtakes += stats.total_overtakes
        
        # 更新賽道統計
        self.track_stats[track]["total_overtakes"] += stats.total_overtakes
        self.track_stats[track]["on_track_overtakes"] += stats.on_track_overtakes
        self.track_stats[track]["pit_related"] += stats.pit_related_changes
        self.track_stats[track]["sc_related"] += stats.sc_related_changes
        self.track_stats[track]["lap_one"] += stats.lap_one_changes
        self.track_stats[track]["races_analyzed"] += 1
        
        # 估算總圈數
        if detector._snapshots:
            max_lap = max(
                snap.get('current_lap', 0) for snap in detector._snapshots
            )
            self.track_stats[track]["total_laps"] += max_lap
        
        # 更新車手統計
        for driver, ds in stats.driver_stats.items():
            self.driver_stats[driver]["total_attacks"] += ds.get("total_attacks", 0)
            self.driver_stats[driver]["successful_attacks"] += ds.get("successful_attacks", 0)
            self.driver_stats[driver]["total_defenses"] += ds.get("total_defenses", 0)
            self.driver_stats[driver]["successful_defenses"] += ds.get("successful_defenses", 0)
            if ds.get("team"):
                self.driver_stats[driver]["team"] = ds["team"]
        
        # 更新車隊統計
        for team, ts in stats.team_stats.items():
            self.team_stats[team]["total_attacks"] += ts.get("total_attacks", 0)
            self.team_stats[team]["successful_attacks"] += ts.get("successful_attacks", 0)
            self.team_stats[team]["total_defenses"] += ts.get("total_defenses", 0)
            self.team_stats[team]["successful_defenses"] += ts.get("successful_defenses", 0)
    
    def _build_output_structure(self, events: List[Dict], seasons: List[int]) -> Dict:
        """建立完整的輸出結構"""
        
        # 計算車手統計
        driver_stats_output = {}
        for driver, stats in self.driver_stats.items():
            attack_rate = (
                stats["successful_attacks"] / stats["total_attacks"]
                if stats["total_attacks"] > 0 else 0.0
            )
            defense_rate = (
                stats["successful_defenses"] / stats["total_defenses"]
                if stats["total_defenses"] > 0 else 0.0
            )
            driver_stats_output[driver] = {
                "total_attacks": stats["total_attacks"],
                "successful_attacks": stats["successful_attacks"],
                "attack_success_rate": round(attack_rate, 3),
                "total_defenses": stats["total_defenses"],
                "successful_defenses": stats["successful_defenses"],
                "defense_success_rate": round(defense_rate, 3),
                "team": stats["team"]
            }
        
        # 計算車隊統計
        team_stats_output = {}
        for team, stats in self.team_stats.items():
            attack_rate = (
                stats["successful_attacks"] / stats["total_attacks"]
                if stats["total_attacks"] > 0 else 0.0
            )
            defense_rate = (
                stats["successful_defenses"] / stats["total_defenses"]
                if stats["total_defenses"] > 0 else 0.0
            )
            team_stats_output[team] = {
                "total_attacks": stats["total_attacks"],
                "successful_attacks": stats["successful_attacks"],
                "avg_attack_success": round(attack_rate, 3),
                "total_defenses": stats["total_defenses"],
                "successful_defenses": stats["successful_defenses"],
                "avg_defense_success": round(defense_rate, 3)
            }
        
        # 計算賽道統計
        track_stats_output = {}
        for track, stats in self.track_stats.items():
            overtake_rate = (
                stats["total_overtakes"] / stats["total_laps"]
                if stats["total_laps"] > 0 else 0.0
            )
            avg_per_race = (
                stats["total_overtakes"] / stats["races_analyzed"]
                if stats["races_analyzed"] > 0 else 0.0
            )
            on_track_rate = (
                stats["on_track_overtakes"] / stats["total_overtakes"]
                if stats["total_overtakes"] > 0 else 0.0
            )
            track_stats_output[track] = {
                "total_overtakes": stats["total_overtakes"],
                "on_track_overtakes": stats["on_track_overtakes"],
                "pit_related": stats["pit_related"],
                "sc_related": stats["sc_related"],
                "lap_one": stats["lap_one"],
                "on_track_rate": round(on_track_rate, 3),
                "total_laps": stats["total_laps"],
                "races_analyzed": stats["races_analyzed"],
                "overtake_rate_per_lap": round(overtake_rate, 3),
                "avg_overtakes_per_race": round(avg_per_race, 1)
            }
        
        return {
            "metadata": {
                "seasons": seasons,
                "total_races": self.races_processed,
                "total_overtakes": self.total_overtakes,
                "collection_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "Live Timing PKL Cache",
                "classification_logic": "BaseOvertakeDetector (unified with F100)"
            },
            "events": events,
            "driver_stats": driver_stats_output,
            "team_stats": team_stats_output,
            "track_stats": track_stats_output
        }


def execute_overtake_history_collector(
    year: int = None,
    race: str = None,
    session: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    執行超車事件歷史收集器
    
    這是 CLI 模組的入口點，被 function_mapper.py 調用
    """
    print("\n" + "="*60)
    print("F134: Overtake History Collector")
    print("       (Using unified BaseOvertakeDetector)")
    print("="*60)
    
    collector = OvertakeHistoryCollector()
    result = collector.collect_all_races(seasons=[2025])  # 目前只有 2025 數據
    
    return result


# 直接執行測試
if __name__ == "__main__":
    result = execute_overtake_history_collector()
    print(f"\nTotal events collected: {len(result.get('events', []))}")
