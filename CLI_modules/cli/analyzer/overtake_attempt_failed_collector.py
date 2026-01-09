"""
F135: 超車嘗試失敗收集器 (Overtake Attempt Failed Collector)

目的: 識別超車嘗試但失敗的事件，補充 F134 的成功案例
數據來源: data/live_timing_cache/2025/*.pkl

繼承: 使用 BaseOvertakeDetector 的分類邏輯過濾

處理邏輯:
  1. 偵測 gap_ahead < 1.0s 且 DRS 可能啟動的情況
  2. 排除第一圈、SC/VSC 圈、進站圈
  3. 追蹤後續快照內是否完成超車
  4. 若未完成 -> 記錄為超車失敗事件

輸出: json/overtake_attempts_failed_2024_2025.json

建立日期: 2026-01-05
更新日期: 2026-01-05 (使用 BaseOvertakeDetector 過濾邏輯)
"""

import os
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict

# 導入基類常數
from CLI_modules.cli.utils.base_overtake_detector import SC_VSC_STATUS_CODES


class OvertakeAttemptFailedCollector:
    """超車嘗試失敗收集器"""
    
    def __init__(self, cache_dir: str = "data/live_timing_cache"):
        """
        初始化收集器
        
        Args:
            cache_dir: PKL 快取目錄路徑
        """
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path("json")
        self.output_dir.mkdir(exist_ok=True)
        
        # 統計數據
        self.total_failed_attempts = 0
        self.races_processed = 0
        
        # DRS 間距閾值 (秒)
        self.DRS_GAP_THRESHOLD = 1.0
        
        # 追蹤窗口 (快照數量，約 10 秒)
        self.TRACKING_WINDOW = 100  # 約 10 秒 (每快照約 0.1 秒)
        
    def collect_all_races(self, seasons: List[int] = None) -> Dict[str, Any]:
        """
        收集所有比賽的超車失敗事件
        
        Args:
            seasons: 要分析的賽季列表，預設 [2025]
            
        Returns:
            完整的超車失敗事件數據
        """
        if seasons is None:
            seasons = [2025]
            
        all_events = []
        
        for season in seasons:
            season_dir = self.cache_dir / str(season)
            if not season_dir.exists():
                print(f"[F135] Season {season} directory not found: {season_dir}")
                continue
                
            # 找出所有 Race PKL 檔案
            race_files = list(season_dir.glob("*_Race.pkl"))
            print(f"[F135] Found {len(race_files)} race files for {season}")
            
            for race_file in race_files:
                try:
                    events = self._process_race_file(race_file, season)
                    all_events.extend(events)
                    self.races_processed += 1
                except Exception as e:
                    print(f"[F135] Error processing {race_file.name}: {e}")
                    
        # 建立完整的輸出結構
        result = self._build_output_structure(all_events, seasons)
        
        # 儲存到 JSON
        output_file = self.output_dir / "overtake_attempts_failed_2024_2025.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print(f"\n[F135] Collection complete!")
        print(f"  - Races processed: {self.races_processed}")
        print(f"  - Total failed attempts: {self.total_failed_attempts}")
        print(f"  - Output: {output_file}")
        
        return result
        
    def _process_race_file(self, race_file: Path, season: int) -> List[Dict]:
        """
        處理單一比賽的 PKL 檔案
        
        Args:
            race_file: PKL 檔案路徑
            season: 賽季年份
            
        Returns:
            該場比賽的超車失敗事件列表
        """
        print(f"[F135] Processing: {race_file.name}")
        
        with open(race_file, 'rb') as f:
            data = pickle.load(f)
            
        snapshots = data.get('snapshots', [])
        driver_info = data.get('driver_info', {})
        driver_stints = data.get('driver_stints', {})
        
        if not snapshots:
            print(f"  - No snapshots found")
            return []
            
        # 從檔名提取賽道名稱
        race_name = race_file.stem
        track_name = self._extract_track_name(race_name)
        
        # 提取進站圈數 (車手 -> 進站圈集合)
        pit_laps = self._extract_pit_laps(snapshots)
        # 擴展進站圈，包含出站圈
        for driver_num in pit_laps:
            extended_laps = set()
            for lap in pit_laps[driver_num]:
                extended_laps.add(lap)
                extended_laps.add(lap + 1)  # 出站圈
            pit_laps[driver_num] = extended_laps
        
        # 提取 SC/VSC 圈數
        sc_laps = self._extract_sc_laps(data.get('track_status', []), snapshots)
        
        events = []
        
        # 追蹤正在進行的超車嘗試
        # key: (attacker_num, defender_num)
        # value: {'start_index': int, 'start_gap': float, 'closest_gap': float, ...}
        active_attempts: Dict[Tuple[str, str], Dict] = {}
        
        # 冷卻機制：避免同一對車輛在短時間內重複記錄
        # key: (attacker_num, defender_num), value: 最後記錄的快照索引
        cooldown_attempts: Dict[Tuple[str, str], int] = {}
        COOLDOWN_SNAPSHOTS = 200  # 約 20 秒冷卻時間
        
        # 采樣間隔
        sample_interval = 5
        total_snapshots = len(snapshots)
        
        for i in range(0, total_snapshots, sample_interval):
            snapshot = snapshots[i]
            drivers = snapshot.get('drivers', {})
            race_time = snapshot.get('race_time', '')
            current_lap = snapshot.get('current_lap', 0)
            
            # 排除第一圈 (起跑混戰)
            if current_lap <= 1:
                continue
            
            # 排除 SC/VSC 圈
            if current_lap in sc_laps:
                continue
            
            # 建立當前位置和間距映射
            current_state = {}
            for driver_num, driver_data in drivers.items():
                pos = driver_data.get('position')
                gap_ahead = self._parse_gap(driver_data.get('gap_to_ahead'))
                
                if pos is not None:
                    current_state[driver_num] = {
                        'position': pos,
                        'driver_tla': driver_data.get('driver_tla', ''),
                        'team_name': driver_data.get('team_name', ''),
                        'gap_ahead': gap_ahead,
                        'drs': driver_data.get('drs', 0),
                        'speed': driver_data.get('speed', 0),
                        'lap': driver_data.get('lap', 0),
                        'in_pit': driver_data.get('in_pit', False),
                        'x': driver_data.get('x', 0),
                        'y': driver_data.get('y', 0)
                    }
            
            # 偵測新的超車嘗試 (gap < 1.0s)
            for driver_num, state in current_state.items():
                if state['in_pit']:
                    continue
                    
                gap = state['gap_ahead']
                if gap is None or gap <= 0:
                    continue
                    
                # 間距在 DRS 範圍內 (< 1.0s)
                if gap < self.DRS_GAP_THRESHOLD:
                    # 找出前車
                    defender_num = self._find_car_ahead(driver_num, state['position'], current_state)
                    
                    if defender_num:
                        # 檢查攻擊者或防守者是否在進站圈
                        attacker_in_pit = current_lap in pit_laps.get(driver_num, set())
                        defender_in_pit = current_lap in pit_laps.get(defender_num, set())
                        if attacker_in_pit or defender_in_pit:
                            continue  # 跳過進站相關的間距
                        
                        attempt_key = (driver_num, defender_num)
                        
                        # 檢查冷卻時間
                        if attempt_key in cooldown_attempts:
                            if i - cooldown_attempts[attempt_key] < COOLDOWN_SNAPSHOTS:
                                continue  # 仍在冷卻中，跳過
                        
                        if attempt_key not in active_attempts:
                            # 新的超車嘗試開始
                            active_attempts[attempt_key] = {
                                'start_index': i,
                                'start_gap': gap,
                                'closest_gap': gap,
                                'start_time': race_time,
                                'start_lap': current_lap,
                                'attacker_tla': state['driver_tla'],
                                'attacker_team': state['team_name'],
                                'defender_tla': current_state.get(defender_num, {}).get('driver_tla', ''),
                                'defender_team': current_state.get(defender_num, {}).get('team_name', ''),
                                'drs_active': state['drs'] > 0,
                                'attacker_pos': state['position'],
                                'track_x': state['x'],
                                'track_y': state['y']
                            }
                        else:
                            # 更新最近間距
                            if gap < active_attempts[attempt_key]['closest_gap']:
                                active_attempts[attempt_key]['closest_gap'] = gap
                            # 更新 DRS 狀態
                            if state['drs'] > 0:
                                active_attempts[attempt_key]['drs_active'] = True
            
            # 檢查是否有超車嘗試超時 (失敗)
            completed_attempts = []
            for attempt_key, attempt in active_attempts.items():
                attacker_num, defender_num = attempt_key
                
                # 檢查是否已經完成超車 (位置交換)
                attacker_state = current_state.get(attacker_num)
                defender_state = current_state.get(defender_num)
                
                if attacker_state and defender_state:
                    # 如果攻擊者位置現在比防守者更靠前 = 超車成功
                    if attacker_state['position'] < defender_state['position']:
                        completed_attempts.append(attempt_key)
                        continue
                
                # 檢查是否超過追蹤窗口 (超時 = 失敗)
                elapsed_snapshots = i - attempt['start_index']
                if elapsed_snapshots > self.TRACKING_WINDOW:
                    # 超車失敗！
                    event = self._create_failed_event(
                        attempt, race_name, track_name, race_time, current_lap, driver_stints
                    )
                    events.append(event)
                    self.total_failed_attempts += 1
                    completed_attempts.append(attempt_key)
                    cooldown_attempts[attempt_key] = i  # 設定冷卻時間
                    
                # 檢查間距是否已經拉開 (放棄嘗試)
                if attacker_state:
                    current_gap = attacker_state.get('gap_ahead', 0)
                    if current_gap and current_gap > self.DRS_GAP_THRESHOLD * 1.5:
                        # 間距拉開太多，視為放棄
                        event = self._create_failed_event(
                            attempt, race_name, track_name, race_time, current_lap, driver_stints
                        )
                        events.append(event)
                        self.total_failed_attempts += 1
                        completed_attempts.append(attempt_key)
                        cooldown_attempts[attempt_key] = i  # 設定冷卻時間
                        
            # 移除已完成的嘗試
            for key in completed_attempts:
                if key in active_attempts:
                    del active_attempts[key]
                    
        print(f"  - Found {len(events)} failed attempts")
        return events
        
    def _find_car_ahead(self, driver_num: str, position: int, current_state: Dict) -> Optional[str]:
        """找出當前位置前方的車手"""
        target_pos = position - 1
        for num, state in current_state.items():
            if num != driver_num and state['position'] == target_pos:
                return num
        return None
        
    def _create_failed_event(
        self,
        attempt: Dict,
        race_name: str,
        track_name: str,
        end_time: str,
        end_lap: int,
        driver_stints: Dict
    ) -> Dict:
        """建立超車失敗事件記錄"""
        import math
        
        return {
            "race": race_name,
            "track": track_name,
            "lap": attempt['start_lap'],
            "race_time": attempt['start_time'],
            "attacker": attempt['attacker_tla'],
            "attacker_team": attempt['attacker_team'],
            "defender": attempt['defender_tla'],
            "defender_team": attempt['defender_team'],
            "gap_start_s": round(attempt['start_gap'], 3),
            "gap_closest_s": round(attempt['closest_gap'], 3),
            "drs_active": attempt['drs_active'],
            "duration_laps": end_lap - attempt['start_lap'],
            "reason": "defender_position_held",
            "track_position_m": math.sqrt(attempt['track_x']**2 + attempt['track_y']**2),
            "overtake_success": False
        }
        
    def _parse_gap(self, gap_value) -> Optional[float]:
        """解析間距值"""
        if gap_value is None:
            return None
        if isinstance(gap_value, (int, float)):
            return float(gap_value)
        if isinstance(gap_value, str):
            try:
                gap_str = gap_value.replace('s', '').strip()
                return float(gap_str)
            except ValueError:
                return None
        return None
        
    def _extract_track_name(self, race_name: str) -> str:
        """從比賽名稱提取賽道名稱"""
        parts = race_name.split('_')
        if len(parts) >= 2:
            track_parts = [p for p in parts[1:] if p != 'Race']
            return '_'.join(track_parts)
        return race_name
    
    def _extract_pit_laps(self, snapshots: List[Dict]) -> Dict[str, Set[int]]:
        """
        提取每位車手的進站圈
        
        Returns:
            Dict[str, Set[int]]: 車手號碼 -> 進站圈集合
        """
        pit_laps: Dict[str, Set[int]] = defaultdict(set)
        
        for snapshot in snapshots:
            # 使用 'drivers' key (PKL 結構)
            drivers = snapshot.get('drivers', {})
            if not drivers:
                continue
            
            # 當前圈數在 snapshot 頂層
            current_lap = snapshot.get('current_lap', 0)
                
            for driver_num, state in drivers.items():
                if not isinstance(state, dict):
                    continue
                    
                # 檢查是否在 pit lane
                in_pit = state.get('in_pit', False)
                if in_pit and current_lap > 0:
                    pit_laps[driver_num].add(current_lap)
                        
        return dict(pit_laps)
    
    def _extract_sc_laps(self, track_status: List[Dict], snapshots: List[Dict]) -> Set[int]:
        """
        從 PKL 頂層 track_status 提取 SC/VSC 圈
        
        Args:
            track_status: PKL 頂層的 track_status 陣列
            snapshots: 快照資料，用於對應時間戳到圈數
            
        Returns:
            Set[int]: SC/VSC 影響的圈數集合
        """
        sc_laps: Set[int] = set()
        
        if not track_status or not snapshots:
            return sc_laps
            
        # 建立時間戳到圈數的映射 (使用 race_time 而非 timestamp)
        timestamp_to_lap: List[tuple] = []
        for snapshot in snapshots:
            race_time = snapshot.get('race_time', '')
            current_lap = snapshot.get('current_lap', 0)
            if race_time and current_lap > 0:
                timestamp_to_lap.append((race_time, current_lap))
        
        # 排序時間戳
        timestamp_to_lap.sort(key=lambda x: x[0])
        
        # 處理每個 SC/VSC 事件
        for status in track_status:
            # Status 可能在頂層或 data 子物件中
            status_data = status.get('data', status)
            status_code = status_data.get('Status')
            
            # 轉換為整數進行比較
            try:
                status_int = int(status_code) if status_code else 0
            except (ValueError, TypeError):
                continue
                
            if status_int in SC_VSC_STATUS_CODES:
                event_ts = status.get('timestamp', status.get('race_time', ''))
                if event_ts:
                    # 二分搜尋找到對應的圈數
                    lap = self._find_lap_for_timestamp(event_ts, timestamp_to_lap)
                    if lap > 0:
                        sc_laps.add(lap)
                        # SC/VSC 通常影響多圈，加入前後圈
                        sc_laps.add(lap + 1)
                        if lap > 1:
                            sc_laps.add(lap - 1)
                            
        return sc_laps
    
    def _find_lap_for_timestamp(self, target_ts: str, timestamp_to_lap: List[tuple]) -> int:
        """使用時間戳找到對應的圈數"""
        if not timestamp_to_lap:
            return 0
        
        # 時間戳格式: HH:MM:SS.mmm
        # 找到第一個 >= target_ts 的時間戳
        for i, (ts, lap) in enumerate(timestamp_to_lap):
            if ts >= target_ts:
                return lap
                
        # 如果都比目標時間早，返回最後一圈
        return timestamp_to_lap[-1][1] if timestamp_to_lap else 0
        
    def _build_output_structure(self, events: List[Dict], seasons: List[int]) -> Dict:
        """建立完整的輸出結構"""
        
        # 統計每個車手的失敗次數
        attacker_fails = defaultdict(int)
        defender_holds = defaultdict(int)
        
        for event in events:
            attacker_fails[event['attacker']] += 1
            defender_holds[event['defender']] += 1
            
        return {
            "metadata": {
                "seasons": seasons,
                "total_races": self.races_processed,
                "total_failed_attempts": self.total_failed_attempts,
                "avg_attempts_per_race": round(self.total_failed_attempts / max(self.races_processed, 1), 1),
                "collection_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "Live Timing PKL Cache",
                "drs_gap_threshold_s": self.DRS_GAP_THRESHOLD
            },
            "events": events,
            "attacker_failed_stats": dict(attacker_fails),
            "defender_held_stats": dict(defender_holds)
        }


def execute_overtake_attempt_failed_collector(
    year: int = None,
    race: str = None,
    session: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    執行超車嘗試失敗收集器
    
    這是 CLI 模組的入口點
    """
    print("\n" + "="*60)
    print("F135: Overtake Attempt Failed Collector")
    print("="*60)
    
    collector = OvertakeAttemptFailedCollector()
    result = collector.collect_all_races(seasons=[2025])
    
    return result


# 直接執行測試
if __name__ == "__main__":
    result = execute_overtake_attempt_failed_collector()
    print(f"\nTotal failed attempts collected: {len(result.get('events', []))}")
