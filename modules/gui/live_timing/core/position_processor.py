"""
Live Timing 位置數據處理器
===========================

處理並對齊 Position、TimingData、CarData 等數據流，
產生統一的時間軸快照供 GUI 使用。

Author: F1T Team
Date: 2025-12-03
"""

import re
import copy
from typing import List, Dict, Any, Optional, Tuple, Union

# CarData.z Channels 定義
CAR_DATA_CHANNELS = {
    "0": "rpm",
    "2": "speed", 
    "3": "gear",
    "4": "throttle",
    "5": "brake",
    "45": "drs"
}

class LivePositionDataProcessor:
    """
    數據對齊/整理層 (Silver Layer)
    
    將原始 JSON 數據對齊到統一時間軸，包含：
    - 車手位置 (X, Y, Z)
    - 速度資料
    - 圈數/計時資料
    - 差距資訊
    - PIT 事件
    - 輪胎策略
    """

    def __init__(self, data_source):
        """
        初始化數據處理器
        
        Args:
            data_source: LocalLiveF1DataSource 或 LiveF1DataSource 實例
        """
        self.data_source = data_source
        
        # 對齊後的快照
        self._aligned_snapshots: List[Dict[str, Any]] = []
        
        # 索引結構
        self._timing_index_full: Dict[str, Dict[str, Any]] = {}
        self._cardata_index_full: Dict[str, Dict[str, Any]] = {}
        self._timing_timestamps: List[str] = []
        self._cardata_timestamps: List[str] = []
        
        # 展開的 CarData 索引 (高頻率)
        self._expanded_cardata_index: Dict[str, Dict[str, Any]] = {}
        self._expanded_cardata_timestamps: List[str] = []
        
        # 車手資訊
        self._driver_info = data_source.load_driver_list()
        
        # PIT 事件和輪胎資訊
        self._pit_events: List[Dict[str, Any]] = []
        self._driver_stints: Dict[str, List[Dict[str, Any]]] = {}
        self._driver_pit_states: Dict[str, Dict[str, Any]] = {}
        
        # 輪胎狀態索引
        self._tyre_state_index: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._tyre_timestamps: List[str] = []

    # ===========================================
    # 公開 API
    # ===========================================
    def process_and_align_data(self, downsample_factor: int = 10, progress_callback=None):
        """
        處理並對齊所有數據源 - 展開內層數據以獲得更高頻率的更新
        
        Position 和 CarData 的 jsonStream 格式中，每個外層記錄包含多個內層時間點，
        本方法會展開這些內層數據，實現約 3-4 Hz 的更新頻率。
        
        Args:
            downsample_factor: 降採樣因子（未使用）
            progress_callback: 進度回調函數 (percent, message) -> None
        """
        from datetime import datetime
        
        def _report(percent, msg):
            if progress_callback:
                progress_callback(percent, msg)
        
        print("\n")
        print("=" * 70)
        print("[PROCESSOR] 開始數據處理 (展開內層數據模式)...")
        print("=" * 70)

        position_data = self.data_source.get_position_data()
        timing_data = self.data_source.get_timing_data()
        cardata = self.data_source.get_cardata()
        
        print(f"[PROCESSOR] Position 外層記錄: {len(position_data)}")
        print(f"[PROCESSOR] Timing 記錄: {len(timing_data)}")
        print(f"[PROCESSOR] CarData 外層記錄: {len(cardata)}")

        if not position_data:
            print("[PROCESSOR] Position 數據為空！")
            return

        _report(0, "Building timing index...")
        
        # 建立 Timing 索引 (事件驅動，不需要展開)
        self._build_timing_index(timing_data)
        
        _report(10, "Expanding CarData...")
        
        # 建立展開的 CarData 索引 (使用內層 UTC 時間戳)
        self._build_expanded_cardata_index(cardata)
        
        _report(20, "Expanding Position data...")

        # 展開 Position 數據
        expanded_positions = self._expand_position_data(position_data)
        print(f"[PROCESSOR] Position 展開後: {len(expanded_positions)} 個時間點")

        aligned_count = 0
        skipped_no_lap = 0
        total_positions = len(expanded_positions)
        
        print(f"[PROCESSOR] 過濾並對齊資料...")
        print(f"[PROCESSOR] 策略: 只保留至少有一位車手有圈數的時間點")
        
        _report(25, f"Aligning {total_positions} snapshots...")
        last_report_percent = 25

        for idx, pos_entry in enumerate(expanded_positions):
            # 進度報告：25% ~ 90%
            if total_positions > 0:
                current_percent = 25 + int((idx / total_positions) * 65)
                if current_percent > last_report_percent and current_percent % 5 == 0:
                    _report(current_percent, f"Aligning... {idx}/{total_positions}")
                    last_report_percent = current_percent
            
            timestamp = pos_entry['timestamp']
            utc_timestamp = pos_entry.get('utc_timestamp')
            entries = pos_entry['entries']
            
            if not isinstance(entries, dict):
                continue

            # 查找 Timing 資料，檢查是否有圈數
            nearest_timing_ts = self._find_nearest_timestamp(timestamp, self._timing_timestamps)
            has_any_lap = False
            
            if nearest_timing_ts and nearest_timing_ts in self._timing_index_full:
                timing_state_all = self._timing_index_full[nearest_timing_ts]
                for driver_num in entries.keys():
                    if driver_num in timing_state_all:
                        lap = timing_state_all[driver_num].get('lap')
                        if lap is not None:
                            has_any_lap = True
                            break
            
            if not has_any_lap:
                skipped_no_lap += 1
                continue

            snapshot = {
                'race_time': timestamp,
                'race_time_seconds': self._time_str_to_seconds(timestamp),
                'drivers': {},
            }

            for driver_num, driver_pos in entries.items():
                driver_info = {
                    'driver_number': driver_num,
                    'status': driver_pos.get('Status', 'Unknown'),
                    'x': driver_pos.get('X'),
                    'y': driver_pos.get('Y'),
                    'z': driver_pos.get('Z'),
                }
                
                # 添加車手資訊
                if driver_num in self._driver_info:
                    info = self._driver_info[driver_num]
                    driver_info['driver_tla'] = info.get('tla', driver_num)
                    driver_info['driver_name'] = info.get('name', driver_num)
                    driver_info['team_name'] = info.get('team', '')
                    driver_info['team_color'] = info.get('team_color', 'CCCCCC')

                # 使用累積的 Timing 狀態
                if nearest_timing_ts and nearest_timing_ts in self._timing_index_full:
                    timing_state = self._timing_index_full[nearest_timing_ts].get(driver_num)
                    if timing_state:
                        # 調試：檢查 27 號車的 status
                        if driver_num == '27' and 'status' in timing_state:
                            if timing_state['status'] in ('STOPPED', 'RETIRED'):
                                print(f"[PROCESSOR_DEBUG] Snapshot {timestamp}: Driver 27 timing_state has status={timing_state['status']}")
                        driver_info.update(timing_state)

                # 使用展開的 CarData（包含所有遙測數據）
                cardata_state = self._find_nearest_cardata(timestamp, driver_num)
                if cardata_state:
                    for field in ['speed', 'rpm', 'gear', 'throttle', 'brake', 'drs']:
                        if field in cardata_state:
                            driver_info[field] = cardata_state[field]

                snapshot['drivers'][driver_num] = driver_info

            if snapshot['drivers']:
                self._aligned_snapshots.append(snapshot)
                aligned_count += 1

        _report(90, "Calculating rankings...")
        
        print(f"[PROCESSOR] 對齊完成！")
        print(f"[PROCESSOR]    保留快照: {aligned_count} 個")
        print(f"[PROCESSOR]    跳過記錄: {skipped_no_lap} 個 (無圈數資料)")
        
        if self._aligned_snapshots:
            first_time = self._aligned_snapshots[0]['race_time']
            last_time = self._aligned_snapshots[-1]['race_time']
            duration = self._aligned_snapshots[-1]['race_time_seconds'] - self._aligned_snapshots[0]['race_time_seconds']
            freq = aligned_count / duration if duration > 0 else 0
            print(f"[PROCESSOR]    時間範圍: {first_time} ~ {last_time}")
            print(f"[PROCESSOR]    更新頻率: {freq:.2f} Hz (每秒 {freq:.1f} 次更新)")
        
        self._calculate_rankings_and_gaps()
        
        _report(95, "Processing tyre data...")
        
        self._process_pit_and_tyre_data()
        
        _report(100, "Processing complete")

    def get_aligned_snapshots(self) -> List[Dict[str, Any]]:
        """獲取對齊後的快照列表"""
        return self._aligned_snapshots
    
    def get_pit_events(self) -> List[Dict[str, Any]]:
        """獲取所有 PIT 進站事件"""
        return self._pit_events
    
    def get_driver_stints(self) -> Dict[str, List[Dict[str, Any]]]:
        """獲取車手輪胎策略（各 stint）"""
        return self._driver_stints
    
    def get_driver_info(self) -> Dict[str, Dict[str, str]]:
        """獲取車手資訊"""
        return self._driver_info
    
    def get_tyre_state_at_time(self, timestamp: str) -> Dict[str, Dict[str, Any]]:
        """
        根據時間戳獲取所有車手的輪胎狀態
        
        Args:
            timestamp: 時間戳 (例如 "00:57:42.516")
            
        Returns:
            {driver_num: {compound, new, stint_count, stints}}
        """
        if not self._tyre_timestamps:
            return {}
        
        target_seconds = self._time_str_to_seconds(timestamp)
        if target_seconds is None:
            return {}
        
        # 找到最接近的時間戳（小於等於目標時間）
        target_ts = None
        for ts in self._tyre_timestamps:
            ts_seconds = self._time_str_to_seconds(ts)
            if ts_seconds is not None and ts_seconds <= target_seconds:
                target_ts = ts
            elif ts_seconds is not None and ts_seconds > target_seconds:
                break
        
        if target_ts and target_ts in self._tyre_state_index:
            return self._tyre_state_index[target_ts]
        
        return {}
    
    def get_track_status_at_time(self, timestamp: str) -> str:
        """
        根據時間戳獲取賽道狀態
        
        Args:
            timestamp: 時間戳 (例如 "00:57:42.516")
            
        Returns:
            status: 賽道狀態碼 ("1"=綠旗, "2"=黃旗, "4"=SC, "5"=紅旗, "6"=VSC)
        """
        track_status_data = self.data_source.get_track_status()
        if not track_status_data:
            print(f"[PROCESSOR] No track_status_data available")
            return "1"  # 預設綠旗
        
        target_seconds = self._time_str_to_seconds(timestamp)
        if target_seconds is None:
            return "1"
        
        # Debug: 顯示資料內容 (只在第一次)
        if not hasattr(self, '_track_status_debug_shown'):
            self._track_status_debug_shown = True
            print(f"[PROCESSOR] TrackStatus records count: {len(track_status_data)}")
            for i, rec in enumerate(track_status_data[:5]):
                print(f"[PROCESSOR] TrackStatus[{i}]: {rec}")
        
        # 找到最接近的狀態（小於等於目標時間）
        current_status = "1"
        for record in track_status_data:
            ts = record.get('timestamp', '')
            ts_seconds = self._time_str_to_seconds(ts)
            if ts_seconds is not None and ts_seconds <= target_seconds:
                data = record.get('data', {})
                status = data.get('Status')
                if status:
                    current_status = str(status)
            elif ts_seconds is not None and ts_seconds > target_seconds:
                break
        
        return current_status

    # ===========================================
    # 內部方法 - 數據展開
    # ===========================================
    def _expand_position_data(self, position_data: List[Dict]) -> List[Dict]:
        """
        展開 Position 數據的內層時間點
        
        原始格式:
        {
            "timestamp": "00:00:02.043",  # 外層時間戳
            "data": {
                "Position": [
                    {"Timestamp": "2023-11-26T12:01:02.527Z", "Entries": {...}},
                    {"Timestamp": "2023-11-26T12:01:02.887Z", "Entries": {...}},
                    ...
                ]
            }
        }
        """
        from datetime import datetime
        
        expanded = []
        base_utc = None
        base_race_seconds = None
        
        for pos_record in position_data:
            outer_timestamp = pos_record.get('timestamp')
            pos_data = pos_record.get('data', {})
            position_list = pos_data.get('Position', [])
            
            if not position_list or not isinstance(position_list, list):
                continue
            
            for pos_entry in position_list:
                inner_utc = pos_entry.get('Timestamp')
                entries = pos_entry.get('Entries')
                
                if not entries or not isinstance(entries, dict):
                    continue
                
                # 計算比賽時間
                if inner_utc:
                    try:
                        utc_str = inner_utc.replace('Z', '+00:00')
                        if '.' in utc_str:
                            parts = utc_str.split('.')
                            if len(parts[1]) > 7:
                                utc_str = parts[0] + '.' + parts[1][:6] + '+00:00'
                        
                        utc_dt = datetime.fromisoformat(utc_str.replace('+00:00', ''))
                        
                        if base_utc is None:
                            base_utc = utc_dt
                            base_race_seconds = self._time_str_to_seconds(outer_timestamp)
                        
                        delta_seconds = (utc_dt - base_utc).total_seconds()
                        race_seconds = base_race_seconds + delta_seconds
                        
                        hours = int(race_seconds // 3600)
                        minutes = int((race_seconds % 3600) // 60)
                        seconds = race_seconds % 60
                        race_time = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
                        
                    except Exception:
                        race_time = outer_timestamp
                        race_seconds = self._time_str_to_seconds(outer_timestamp)
                else:
                    race_time = outer_timestamp
                    race_seconds = self._time_str_to_seconds(outer_timestamp)
                
                expanded.append({
                    'timestamp': race_time,
                    'race_time_seconds': race_seconds,
                    'utc_timestamp': inner_utc,
                    'entries': entries
                })
        
        expanded.sort(key=lambda x: x.get('race_time_seconds', 0))
        return expanded
    
    def _build_expanded_cardata_index(self, cardata: List[Dict]):
        """建立展開的 CarData 索引，使用內層 UTC 時間戳"""
        from datetime import datetime
        
        print(f"[PROCESSOR] 展開 CarData 內層數據...")
        
        expanded_entries = []
        base_utc = None
        base_race_seconds = None
        
        for record in cardata:
            outer_timestamp = record.get('timestamp')
            data = record.get('data', {})
            entries = data.get('Entries', [])
            
            if not isinstance(entries, list):
                continue
            
            for entry in entries:
                inner_utc = entry.get('Utc')
                cars = entry.get('Cars', {})
                
                if not cars:
                    continue
                
                if inner_utc:
                    try:
                        utc_str = inner_utc.replace('Z', '')
                        if '.' in utc_str:
                            parts = utc_str.split('.')
                            if len(parts[1]) > 6:
                                utc_str = parts[0] + '.' + parts[1][:6]
                        
                        utc_dt = datetime.fromisoformat(utc_str)
                        
                        if base_utc is None:
                            base_utc = utc_dt
                            base_race_seconds = self._time_str_to_seconds(outer_timestamp)
                        
                        delta_seconds = (utc_dt - base_utc).total_seconds()
                        race_seconds = base_race_seconds + delta_seconds
                        
                        hours = int(race_seconds // 3600)
                        minutes = int((race_seconds % 3600) // 60)
                        seconds = race_seconds % 60
                        race_time = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
                        
                    except Exception:
                        race_time = outer_timestamp
                        race_seconds = self._time_str_to_seconds(outer_timestamp)
                else:
                    race_time = outer_timestamp
                    race_seconds = self._time_str_to_seconds(outer_timestamp)
                
                expanded_entries.append({
                    'timestamp': race_time,
                    'race_time_seconds': race_seconds,
                    'cars': cars
                })
        
        expanded_entries.sort(key=lambda x: x.get('race_time_seconds', 0))
        
        # 建立累積狀態索引
        latest_driver_state = {}
        self._expanded_cardata_index = {}
        self._expanded_cardata_timestamps = []
        
        for entry in expanded_entries:
            timestamp = entry['timestamp']
            cars = entry['cars']
            
            for driver_num, car_data in cars.items():
                channels = car_data.get('Channels', {})
                
                if driver_num not in latest_driver_state:
                    latest_driver_state[driver_num] = {}
                
                # 解析所有 Channels
                for channel_id, field_name in CAR_DATA_CHANNELS.items():
                    value = channels.get(channel_id) or channels.get(int(channel_id))
                    if value is not None:
                        latest_driver_state[driver_num][field_name] = value
            
            self._expanded_cardata_index[timestamp] = copy.deepcopy(latest_driver_state)
            self._expanded_cardata_timestamps.append(timestamp)
        
        print(f"[PROCESSOR] CarData 展開完成: {len(expanded_entries)} 個時間點")
        if self._expanded_cardata_timestamps:
            print(f"  第一個: {self._expanded_cardata_timestamps[0]}")
            print(f"  最後一個: {self._expanded_cardata_timestamps[-1]}")
    
    def _find_nearest_cardata(self, timestamp: str, driver_num: str) -> Optional[Dict]:
        """查找最接近的 CarData 狀態"""
        if not self._expanded_cardata_timestamps:
            # 回退到舊索引
            nearest_ts = self._find_nearest_timestamp(timestamp, self._cardata_timestamps)
            if nearest_ts and nearest_ts in self._cardata_index_full:
                return self._cardata_index_full[nearest_ts].get(driver_num)
            return None
        
        nearest_ts = self._find_nearest_timestamp(timestamp, self._expanded_cardata_timestamps)
        if nearest_ts and nearest_ts in self._expanded_cardata_index:
            return self._expanded_cardata_index[nearest_ts].get(driver_num)
        return None

    # ===========================================
    # 內部方法 - 索引建立
    # ===========================================
    def _build_timing_index(self, timing_data: List[Dict[str, Any]]):
        """建立 Timing 數據的累積狀態索引"""
        print(f"[PROCESSOR] _build_timing_index 開始, 輸入記錄數: {len(timing_data)}")
        sorted_timing = sorted(timing_data, key=lambda item: item.get('timestamp', ''))
        latest_driver_state: Dict[str, Dict[str, Any]] = {}
        index: Dict[str, Dict[str, Any]] = {}
        
        # 調試：追踪處理統計
        driver_27_records = 0
        driver_27_stopped_count = 0
        driver_27_retired_count = 0

        for record in sorted_timing:
            timestamp = record.get('timestamp')
            data = record.get('data', {})
            lines = data.get('Lines', {})
            if not isinstance(lines, dict):
                continue

            for driver_num, driver_data in lines.items():
                # 調試：統計 27 號車
                if driver_num == '27':
                    driver_27_records += 1
                    if driver_data.get('Stopped') is True:
                        driver_27_stopped_count += 1
                        print(f"[PROCESSOR_DEBUG] HUL Stopped=True at {timestamp}")
                    if driver_data.get('Retired') is True:
                        driver_27_retired_count += 1
                        print(f"[PROCESSOR_DEBUG] HUL Retired=True at {timestamp}")
                lap_num = driver_data.get('NumberOfLaps')
                last_lap = driver_data.get('LastLapTime', {})
                best_lap = driver_data.get('BestLapTime', {})
                gap_sec, gap_laps = self._parse_gap_value(driver_data.get('GapToLeader'))
                interval_sec, _ = self._parse_gap_value(driver_data.get('IntervalToPositionAhead'))
                position_val = self._safe_int(driver_data.get('Position'))
                
                # PIT 相關
                in_pit = driver_data.get('InPit')
                pit_out = driver_data.get('PitOut')
                num_pit_stops = driver_data.get('NumberOfPitStops')
                
                # 退賽/停止狀態 (DNF detection)
                retired = driver_data.get('Retired')
                stopped = driver_data.get('Stopped')

                if driver_num not in latest_driver_state:
                    latest_driver_state[driver_num] = {}

                # 增量式更新
                if lap_num is not None:
                    latest_driver_state[driver_num]['lap'] = lap_num
                
                # 上一圈時間
                if isinstance(last_lap, dict) and last_lap.get('Value'):
                    latest_driver_state[driver_num]['last_lap_time'] = last_lap.get('Value')
                    latest_driver_state[driver_num]['last_lap_personal_fastest'] = last_lap.get('PersonalFastest', False)
                    latest_driver_state[driver_num]['last_lap_overall_fastest'] = last_lap.get('OverallFastest', False)
                
                # Sector 時間
                sectors = driver_data.get('Sectors', {})
                if isinstance(sectors, dict):
                    for sector_idx, sector_key in enumerate(['0', '1', '2']):
                        sector_data = sectors.get(sector_key, {})
                        if isinstance(sector_data, dict) and sector_data.get('Value'):
                            sector_name = f's{sector_idx + 1}'
                            latest_driver_state[driver_num][f'{sector_name}_time'] = sector_data.get('Value')
                            latest_driver_state[driver_num][f'{sector_name}_personal_fastest'] = sector_data.get('PersonalFastest', False)
                            latest_driver_state[driver_num][f'{sector_name}_overall_fastest'] = sector_data.get('OverallFastest', False)
                
                # 最佳圈時
                if isinstance(best_lap, dict) and best_lap.get('Value'):
                    latest_driver_state[driver_num]['best_lap_time'] = best_lap.get('Value')
                    latest_driver_state[driver_num]['best_lap_number'] = best_lap.get('Lap')
                
                if gap_sec is not None or gap_laps > 0:
                    latest_driver_state[driver_num]['gap_to_leader'] = gap_sec
                    latest_driver_state[driver_num]['gap_to_leader_laps'] = gap_laps
                if interval_sec is not None:
                    latest_driver_state[driver_num]['gap_to_ahead'] = interval_sec
                if position_val is not None:
                    latest_driver_state[driver_num]['position'] = position_val
                
                # PIT 狀態
                if in_pit is not None:
                    latest_driver_state[driver_num]['in_pit'] = in_pit
                if pit_out is not None:
                    latest_driver_state[driver_num]['pit_out'] = pit_out
                if num_pit_stops is not None:
                    latest_driver_state[driver_num]['num_pit_stops'] = num_pit_stops
                
                # 退賽/停止狀態 - 設置 status 欄位供過濾使用
                if retired is True:
                    latest_driver_state[driver_num]['retired'] = True
                    latest_driver_state[driver_num]['status'] = 'RETIRED'
                    print(f"[PROCESSOR] Driver {driver_num} RETIRED at {timestamp}")
                if stopped is True:
                    latest_driver_state[driver_num]['stopped'] = True
                    # 只有在非 PIT 情況下才設為 STOPPED (PIT 時也會暫時 stopped)
                    if not in_pit:
                        latest_driver_state[driver_num]['status'] = 'STOPPED'
                        print(f"[PROCESSOR] Driver {driver_num} STOPPED at {timestamp}")

            if timestamp:
                index[timestamp] = copy.deepcopy(latest_driver_state)

        self._timing_timestamps = sorted(index.keys())
        self._timing_index_full = index
        
        # 輸出 27 號車統計
        print(f"[PROCESSOR] Driver 27 (HUL) 統計: 共 {driver_27_records} 筆記錄, Stopped={driver_27_stopped_count}, Retired={driver_27_retired_count}")
        
        print(f"[PROCESSOR] Timing 索引建立完成: {len(self._timing_timestamps)} 個時間戳")
        if self._timing_timestamps:
            print(f"  第一個: {self._timing_timestamps[0]}")
            print(f"  最後一個: {self._timing_timestamps[-1]}")

    def _build_cardata_index(self, cardata: List[Dict[str, Any]]):
        """建立 CarData 索引 (舊方法，作為備用)"""
        sorted_cardata = sorted(cardata, key=lambda item: item.get('timestamp', ''))
        latest_driver_state: Dict[str, Dict[str, Any]] = {}
        index: Dict[str, Dict[str, Any]] = {}

        for record in sorted_cardata:
            timestamp = record.get('timestamp')
            data = record.get('data', {})
            entries = data.get('Entries', [])
            if not isinstance(entries, list):
                continue

            for entry in entries:
                cars = entry.get('Cars', {})
                for driver_num, car_data in cars.items():
                    channels = car_data.get('Channels', {})
                    speed = channels.get('2')
                    if speed is not None:
                        if driver_num not in latest_driver_state:
                            latest_driver_state[driver_num] = {}
                        latest_driver_state[driver_num]['speed'] = speed

            if timestamp:
                index[timestamp] = copy.deepcopy(latest_driver_state)

        self._cardata_timestamps = sorted(index.keys())
        self._cardata_index_full = index

    def _calculate_rankings_and_gaps(self):
        """計算排名和差距"""
        print(f"[PROCESSOR] 計算排名和差距...")
        for snapshot in self._aligned_snapshots:
            drivers = snapshot['drivers']
            
            # 計算當前最大圈數
            current_lap = 0
            for driver_data in drivers.values():
                lap = driver_data.get('lap', 0)
                if lap and lap > current_lap:
                    current_lap = lap
            snapshot['current_lap'] = current_lap
            
            sorted_drivers = sorted(
                drivers.items(),
                key=lambda item: (
                    item[1].get('position') if item[1].get('position') is not None else 999,
                    -(item[1].get('lap') or 0),
                ),
            )

            for fallback_position, (driver_num, driver_data) in enumerate(sorted_drivers, start=1):
                official_position = driver_data.get('position')
                driver_data['position'] = official_position or fallback_position

                if driver_data['position'] == 1:
                    driver_data['gap_to_leader'] = 0.0
                    driver_data['gap_to_leader_laps'] = 0
                    driver_data['gap_to_leader_display'] = "0.000s"
                    # P1 沒有前車，強制設為空
                    driver_data['gap_to_ahead'] = None
                    driver_data['gap_to_ahead_display'] = ""
                else:
                    gap_seconds = driver_data.get('gap_to_leader')
                    gap_laps = driver_data.get('gap_to_leader_laps', 0)
                    driver_data['gap_to_leader_display'] = self._format_gap_label(gap_seconds, gap_laps)
                    interval_seconds = driver_data.get('gap_to_ahead')
                    driver_data['gap_to_ahead_display'] = self._format_interval_label(interval_seconds)

        print(f"[PROCESSOR] 排名計算完成")

    def _process_pit_and_tyre_data(self):
        """處理 PIT 事件和輪胎資訊"""
        print("[PROCESSOR] 處理 PIT 和輪胎數據...")
        
        timing_data = self.data_source.get_timing_data()
        timing_app_data = self.data_source.get_timing_app_data()
        
        # 1. 從 TimingData 中提取 PIT 事件
        driver_pit_states = {}
        pit_events = []
        
        for record in timing_data:
            timestamp = record.get('timestamp')
            data = record.get('data', {})
            lines = data.get('Lines', {})
            
            if not isinstance(lines, dict):
                continue
            
            for driver_num, driver_data in lines.items():
                if not isinstance(driver_data, dict):
                    continue
                
                if driver_num not in driver_pit_states:
                    driver_pit_states[driver_num] = {'in_pit': None, 'last_lap': 0}
                
                if 'NumberOfLaps' in driver_data:
                    driver_pit_states[driver_num]['last_lap'] = driver_data['NumberOfLaps']
                
                if 'InPit' in driver_data:
                    was_in_pit = driver_pit_states[driver_num]['in_pit']
                    now_in_pit = driver_data['InPit']
                    lap = driver_pit_states[driver_num]['last_lap']
                    
                    if was_in_pit is not None and lap > 0:
                        if not was_in_pit and now_in_pit:
                            pit_events.append({
                                'type': 'PIT_IN',
                                'timestamp': timestamp,
                                'driver': driver_num,
                                'lap': lap,
                            })
                        elif was_in_pit and not now_in_pit:
                            pit_events.append({
                                'type': 'PIT_OUT',
                                'timestamp': timestamp,
                                'driver': driver_num,
                                'lap': lap,
                            })
                    
                    driver_pit_states[driver_num]['in_pit'] = now_in_pit
        
        self._pit_events = pit_events
        
        # 2. 從 TimingAppData 中建立輪胎策略索引
        driver_stints_raw = {}
        latest_tyre_state = {}
        
        for record in timing_app_data:
            timestamp = record.get('timestamp')
            data = record.get('data', {})
            lines = data.get('Lines', {})
            
            if not isinstance(lines, dict):
                continue
            
            for driver_num, driver_data in lines.items():
                if not isinstance(driver_data, dict):
                    continue
                
                stints = driver_data.get('Stints')
                if not stints:
                    continue
                
                if driver_num not in driver_stints_raw:
                    driver_stints_raw[driver_num] = {}
                
                # 格式 1: 初始完整列表
                if isinstance(stints, list):
                    for i, stint in enumerate(stints):
                        if isinstance(stint, dict):
                            driver_stints_raw[driver_num][i] = {
                                'compound': stint.get('Compound', 'UNKNOWN'),
                                'new': stint.get('New') == 'true' or stint.get('New') is True,
                                'total_laps': stint.get('TotalLaps', 0),
                                'start_laps': stint.get('StartLaps', 0),
                            }
                
                # 格式 2: 增量更新
                elif isinstance(stints, dict):
                    for stint_index_str, stint_update in stints.items():
                        if not isinstance(stint_update, dict):
                            continue
                        
                        stint_index = int(stint_index_str)
                        
                        if stint_index not in driver_stints_raw[driver_num]:
                            driver_stints_raw[driver_num][stint_index] = {
                                'compound': 'UNKNOWN',
                                'new': False,
                                'total_laps': 0,
                                'start_laps': 0,
                            }
                        
                        if 'Compound' in stint_update:
                            driver_stints_raw[driver_num][stint_index]['compound'] = stint_update['Compound']
                        if 'New' in stint_update:
                            driver_stints_raw[driver_num][stint_index]['new'] = (
                                stint_update['New'] == 'true' or stint_update['New'] is True
                            )
                        if 'TotalLaps' in stint_update:
                            driver_stints_raw[driver_num][stint_index]['total_laps'] = stint_update['TotalLaps']
                        if 'StartLaps' in stint_update:
                            driver_stints_raw[driver_num][stint_index]['start_laps'] = stint_update['StartLaps']
                
                # 更新當前輪胎狀態
                if driver_stints_raw[driver_num]:
                    sorted_indices = sorted(driver_stints_raw[driver_num].keys())
                    parsed_stints = []
                    for idx in sorted_indices:
                        stint_data = driver_stints_raw[driver_num][idx]
                        parsed_stints.append({
                            'stint_number': idx + 1,
                            **stint_data
                        })
                    
                    current_stint = parsed_stints[-1]
                    latest_tyre_state[driver_num] = {
                        'compound': current_stint['compound'],
                        'new': current_stint['new'],
                        'stint_count': len(parsed_stints),
                        'stints': copy.deepcopy(parsed_stints),
                        'tyre_age': current_stint.get('total_laps', 0),
                    }
            
            if timestamp and latest_tyre_state:
                self._tyre_state_index[timestamp] = copy.deepcopy(latest_tyre_state)
        
        # 最終結果
        driver_stints = {}
        for driver_num, stints_dict in driver_stints_raw.items():
            sorted_indices = sorted(stints_dict.keys())
            driver_stints[driver_num] = [
                {'stint_number': idx + 1, **stints_dict[idx]}
                for idx in sorted_indices
            ]
        
        self._driver_stints = driver_stints
        self._tyre_timestamps = sorted(
            self._tyre_state_index.keys(),
            key=lambda ts: self._time_str_to_seconds(ts) or 0
        )
        
        pit_in_count = len([e for e in pit_events if e['type'] == 'PIT_IN'])
        print(f"[PROCESSOR] PIT 事件: {pit_in_count} 次進站")
        print(f"[PROCESSOR] 輪胎策略: {len(driver_stints)} 位車手")
        print(f"[PROCESSOR] 輪胎狀態索引: {len(self._tyre_timestamps)} 個時間戳")

    # ===========================================
    # 工具方法
    # ===========================================
    @staticmethod
    def _format_interval_label(seconds: Optional[float]) -> str:
        if seconds is None:
            return "-"
        return f"+{seconds:.3f}s"

    @staticmethod
    def _format_gap_label(seconds: Optional[float], laps: int) -> str:
        if laps and laps > 0:
            return f"+{laps} L"
        if seconds is None:
            return "N/A"
        return f"+{seconds:.3f}s"

    @staticmethod
    def _parse_gap_value(raw_value: Any) -> Tuple[Optional[float], int]:
        if raw_value is None:
            return None, 0

        value = raw_value
        units = None

        if isinstance(raw_value, dict):
            value = raw_value.get('Value')
            units = raw_value.get('Units')

        if isinstance(value, str):
            cleaned = value.strip().upper()
            match = re.match(r"([+-]?\d+[\.:]?\d*)", cleaned)
            if match:
                try:
                    seconds = float(match.group(1).replace(':', '.'))
                    if units and 'LAP' in units.upper():
                        return None, int(seconds)
                    if 'LAP' in cleaned:
                        return None, int(seconds)
                    return seconds, 0
                except ValueError:
                    return None, 0
            if 'LAP' in cleaned:
                digits = re.findall(r"\d+", cleaned)
                return None, int(digits[0]) if digits else 0
            try:
                return float(cleaned), 0
            except ValueError:
                return None, 0

        if isinstance(value, (int, float)):
            return float(value), 0

        return None, 0

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _time_str_to_seconds(time_str: Optional[str]) -> float:
        if not time_str:
            return 0.0
        try:
            # 優先嘗試 HH:MM:SS.mmm 格式
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 3:
                    h, m, s = parts
                    return int(h) * 3600 + int(m) * 60 + float(s)
            # 舊格式 HHMMSS
            hours = int(time_str[0:2])
            minutes = int(time_str[2:4])
            seconds = float(time_str[4:])
            return hours * 3600 + minutes * 60 + seconds
        except Exception:
            return 0.0

    def _find_nearest_timestamp(self, target: str, timestamp_list: List[str]) -> Optional[str]:
        """查找最近的過去時間戳（不包括未來時間戳）"""
        if not timestamp_list:
            return None
        if target in timestamp_list:
            return target
        
        target_seconds = self._time_str_to_seconds(target)
        
        # 二分查找
        left, right = 0, len(timestamp_list) - 1
        result = None
        
        while left <= right:
            mid = (left + right) // 2
            mid_seconds = self._time_str_to_seconds(timestamp_list[mid])
            
            if mid_seconds <= target_seconds:
                result = timestamp_list[mid]
                left = mid + 1
            else:
                right = mid - 1
        
        return result
