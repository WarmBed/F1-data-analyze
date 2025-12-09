# -*- coding: utf-8 -*-
"""
Overtake Data Collector (F81)
=============================

從 Live F1 JSON 數據收集超車事件，生成訓練數據。

數據來源:
- json/LiveF1/{year}/{race}/Position.json      - 車手位置座標
- json/LiveF1/{year}/{race}/TimingData.json    - 間距、位置、Catching 狀態
- json/LiveF1/{year}/{race}/TyreStintSeries.json - 輪胎策略
- json/LiveF1/{year}/{race}/TrackStatus.json   - 賽道狀態 (黃旗/SC)
- json/LiveF1/{year}/{race}/LapCount.json      - 圈數

輸出:
- data/overtake_prediction/overtake_events_{year}.csv
- data/overtake_prediction/training_samples_{year}.csv

Author: F1T Team
Date: 2025-12-05
"""

import os
import json
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field, asdict

import pandas as pd
import numpy as np


# ============================================================================
# 賽事名稱映射 (複用自 local_source.py)
# ============================================================================
RACE_NAME_TO_FOLDER = {
    "Japan": "Japanese_Race",
    "China": "Chinese_Race",
    "Singapore": "Singapore_Race",
    "Azerbaijan": "Azerbaijan_Race",
    "Bahrain": "Bahrain_Race",
    "Saudi Arabia": "Saudi_Arabian_Race",
    "Qatar": "Qatar_Race",
    "Abu Dhabi": "Abu_Dhabi_Race",
    "Great Britain": "British_Race",
    "Belgium": "Belgian_Race",
    "Netherlands": "Dutch_Race",
    "Italy": "Italian_Race",
    "Spain": "Spanish_Race",
    "Hungary": "Hungarian_Race",
    "Austria": "Austrian_Race",
    "Monaco": "Monaco_Race",
    "Emilia Romagna": "Emilia_Romagna_Race",
    "United States": "United_States_Race",
    "Las Vegas": "Las_Vegas_Race",
    "Mexico": "Mexico_City_Race",
    "Brazil": "São_Paulo_Race",
    "Miami": "Miami_Race",
    "Canada": "Canadian_Race",
    "Australia": "Australian_Race",
}


@dataclass
class OvertakeEvent:
    """超車事件數據結構"""
    timestamp: str
    lap: int
    overtaker: str          # 超車者車號
    overtaken: str          # 被超車者車號
    overtaker_new_pos: int  # 超車後位置
    overtaken_new_pos: int  # 被超車後位置
    
    # 超車前狀態
    gap_before: float       # 超車前間距 (秒)
    catching_before: bool   # 超車前是否在追近
    
    # 輪胎狀態
    overtaker_tyre: str = ""
    overtaker_tyre_age: int = 0
    overtaken_tyre: str = ""
    overtaken_tyre_age: int = 0
    
    # 賽道狀態
    track_status: str = "GREEN"
    
    # 額外資訊
    year: int = 0
    race: str = ""


@dataclass 
class TrainingSample:
    """訓練樣本數據結構"""
    # 標籤
    overtake_happened: int  # 1 = 發生超車, 0 = 未發生
    
    # 間距特徵
    gap_seconds: float
    gap_delta: float        # 間距變化 (負值 = 追近)
    is_catching: int        # 1 = 正在追近
    
    # DRS 特徵
    drs_available: int      # 1 = 間距 < 1 秒
    
    # 輪胎特徵
    attacker_tyre_compound: int   # 0=S, 1=M, 2=H, 3=I, 4=W
    defender_tyre_compound: int
    tyre_age_diff: int            # 防守者壽命 - 進攻者壽命
    
    # 賽道特徵
    track_status_green: int       # 1 = 綠旗
    
    # 位置特徵
    attacker_position: int
    
    # 比賽進度
    race_progress: float          # 0.0 ~ 1.0
    
    # F85 新增特徵 (近距離接觸預測) - 帶默認值的欄位必須在最後
    close_combat_happened: int = 0        # F85: 1 = 會進入 0.2-0.3s, 0 = 不會
    gap_trend_3lap: float = 0.0          # 過去 3 圈的 gap 趨勢斜率
    min_gap_last_5lap: float = 999.0     # 過去 5 圈的最小 gap
    consecutive_catching_laps: int = 0    # 連續追近圈數
    
    # 元數據 (不用於訓練)
    year: int = 0
    race: str = ""
    lap: int = 0
    attacker: str = ""
    defender: str = ""


class OvertakeDataCollector:
    """
    超車事件數據收集器
    
    從 Live F1 JSON 數據收集超車事件，並生成訓練樣本。
    
    使用方式:
        collector = OvertakeDataCollector()
        collector.collect_year(2024)
        collector.save_training_data()
    """
    
    def __init__(self, 
                 livef1_dir: str = None,
                 output_dir: str = None,
                 verbose: bool = True):
        """
        初始化收集器
        
        Args:
            livef1_dir: Live F1 JSON 根目錄
            output_dir: 輸出目錄
            verbose: 是否顯示詳細輸出
        """
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        
        if livef1_dir is None:
            self.livef1_dir = project_root / "json" / "LiveF1"
        else:
            self.livef1_dir = Path(livef1_dir)
        
        if output_dir is None:
            self.output_dir = project_root / "data" / "overtake_prediction"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # 收集的數據
        self.overtake_events: List[OvertakeEvent] = []
        self.training_samples: List[TrainingSample] = []
        
        # 統計
        self.stats = {
            'races_processed': 0,
            'total_overtakes': 0,
            'total_samples': 0,
        }
        
        if self.verbose:
            print(f"[F81] OvertakeDataCollector 初始化")
            print(f"[F81] LiveF1 目錄: {self.livef1_dir}")
            print(f"[F81] 輸出目錄: {self.output_dir}")
    
    def collect_all(self, years: List[int] = None) -> Dict[str, Any]:
        """
        收集所有可用年份的數據
        
        Args:
            years: 要收集的年份列表，None 則收集所有可用年份
            
        Returns:
            收集統計
        """
        if years is None:
            # 自動偵測可用年份
            years = []
            for item in self.livef1_dir.iterdir():
                if item.is_dir() and item.name.isdigit():
                    years.append(int(item.name))
            years.sort()
        
        if self.verbose:
            print(f"[F81] 準備收集年份: {years}")
        
        for year in years:
            self.collect_year(year)
        
        return self.stats
    
    def collect_year(self, year: int) -> int:
        """
        收集指定年份的所有賽事數據
        
        Args:
            year: 年份
            
        Returns:
            該年份收集到的超車事件數量
        """
        year_dir = self.livef1_dir / str(year)
        
        if not year_dir.exists():
            if self.verbose:
                print(f"[F81] 年份目錄不存在: {year_dir}")
            return 0
        
        races = [d.name for d in year_dir.iterdir() if d.is_dir()]
        
        if self.verbose:
            print(f"\n[F81] ===== {year} 年 ({len(races)} 場比賽) =====")
        
        year_overtakes = 0
        
        for race in races:
            try:
                count = self.collect_race(year, race)
                year_overtakes += count
            except Exception as e:
                if self.verbose:
                    print(f"[F81]   {race}: ERROR - {str(e)[:50]}")
        
        if self.verbose:
            print(f"[F81] {year} 年共收集 {year_overtakes} 次超車事件")
        
        return year_overtakes
    
    def collect_race(self, year: int, race: str) -> int:
        """
        收集單場比賽的超車事件
        
        Args:
            year: 年份
            race: 賽事名稱 (資料夾名稱)
            
        Returns:
            收集到的超車事件數量
        """
        race_dir = self.livef1_dir / str(year) / race
        
        if not race_dir.exists():
            return 0
        
        # 載入必要的 JSON 檔案
        timing_data = self._load_json(race_dir / "TimingData.json")
        lap_count_data = self._load_json(race_dir / "LapCount.json")
        tyre_data = self._load_json(race_dir / "TyreStintSeries.json")
        track_status_data = self._load_json(race_dir / "TrackStatus.json")
        # DRS 數據從 CarData.json 提取 (大檔案，使用抽樣載入)
        car_data = self._load_cardata_sampled(race_dir / "CarData.json")
        
        if not timing_data:
            if self.verbose:
                print(f"[F81]   {race}: 無 TimingData")
            return 0
        
        # 解析數據
        position_timeline = self._build_position_timeline(timing_data)
        tyre_state = self._build_tyre_state(tyre_data)
        track_status_timeline = self._build_track_status_timeline(track_status_data)
        lap_timeline = self._build_lap_timeline(lap_count_data)
        total_laps = self._get_total_laps(lap_count_data)
        drs_timeline = self._build_drs_timeline(car_data)  # 建立 DRS 時間線
        
        # 偵測超車事件
        overtakes = self._detect_overtakes(
            position_timeline, 
            tyre_state,
            track_status_timeline,
            lap_timeline,
            total_laps,
            year, 
            race
        )
        
        # 生成訓練樣本
        samples = self._generate_training_samples(
            timing_data,
            position_timeline,
            tyre_state,
            track_status_timeline,
            lap_timeline,
            total_laps,
            overtakes,
            year,
            race,
            drs_timeline  # 傳遞 DRS 時間線
        )
        
        self.overtake_events.extend(overtakes)
        self.training_samples.extend(samples)
        
        self.stats['races_processed'] += 1
        self.stats['total_overtakes'] += len(overtakes)
        self.stats['total_samples'] += len(samples)
        
        if self.verbose:
            print(f"[F81]   {race}: {len(overtakes)} 超車, {len(samples)} 樣本")
        
        return len(overtakes)
    
    def _load_json(self, filepath: Path) -> List[Dict[str, Any]]:
        """載入 JSON 檔案"""
        if not filepath.exists():
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 處理不同格式
            if isinstance(data, dict) and 'records' in data:
                return data['records']
            if isinstance(data, list):
                return data
            return []
            
        except Exception as e:
            if self.verbose:
                print(f"[F81] 載入 {filepath.name} 失敗: {e}")
            return []
    
    def _load_cardata_sampled(self, filepath: Path, max_records: int = 5000) -> List[Dict[str, Any]]:
        """
        載入 CarData.json (抽樣版本，避免記憶體問題)
        
        注意: CarData.json 通常很大 (50MB+)，為了效能暫時跳過載入。
        DRS 可用性改用間距 < 1 秒來判斷，這是 F1 DRS 規則的條件。
        
        Args:
            filepath: CarData.json 路徑
            max_records: 最大記錄數 (抽樣)
            
        Returns:
            空列表 (暫時跳過大檔案)
        """
        # 暫時跳過 CarData.json 載入，使用間距來判斷 DRS
        # 因為根據 F1 規則，間距 < 1 秒 = DRS 可用
        return []
    
    def _build_position_timeline(self, timing_data: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """
        建立位置時間線（包含 Pit 狀態）
        
        Returns:
            {timestamp: {driver_num: {'position': int, 'gap': float, 'catching': bool, 'in_pit': bool, 'lap': int}}}
        """
        timeline = {}
        current_state = {}  # {driver_num: state}
        
        for record in timing_data:
            timestamp = record.get('timestamp', '')
            data = record.get('data', {})
            lines = data.get('Lines', {})
            
            if not lines:
                continue
            
            # 更新狀態
            for driver_num, driver_data in lines.items():
                if driver_num not in current_state:
                    current_state[driver_num] = {
                        'position': 99,
                        'gap': 999.0,
                        'gap_to_leader': '',
                        'catching': False,
                        'in_pit': False,
                        'lap': 0
                    }
                
                # 更新位置
                if 'Position' in driver_data:
                    current_state[driver_num]['position'] = int(driver_data['Position'])
                
                # 更新 Pit 狀態
                if 'InPit' in driver_data:
                    current_state[driver_num]['in_pit'] = bool(driver_data['InPit'])
                
                # 更新圈數
                if 'NumberOfLaps' in driver_data:
                    current_state[driver_num]['lap'] = int(driver_data['NumberOfLaps'])
                
                # 更新間距
                if 'IntervalToPositionAhead' in driver_data:
                    interval = driver_data['IntervalToPositionAhead']
                    if isinstance(interval, dict):
                        value = interval.get('Value', '')
                        if value and not value.endswith('L'):
                            try:
                                current_state[driver_num]['gap'] = float(value)
                            except:
                                pass
                        current_state[driver_num]['catching'] = interval.get('Catching', False)
                
                if 'GapToLeader' in driver_data:
                    current_state[driver_num]['gap_to_leader'] = driver_data['GapToLeader']
            
            # 保存快照
            if current_state:
                timeline[timestamp] = {k: v.copy() for k, v in current_state.items()}
        
        return timeline
    
    def _build_tyre_state(self, tyre_data: List[Dict]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        建立輪胎狀態時間線
        
        TyreStintSeries 格式:
        {"timestamp": "00:49:22", "data": {"Stints": {
            "3": {"0": {"Compound": "MEDIUM", "TotalLaps": 0}},
            "4": {"1": {"Compound": "HARD", "TotalLaps": 5}}
        }}}
        
        Returns:
            {timestamp: {driver_num: {'compound': str, 'age': int}}}
        """
        timeline = {}
        current_state = {}  # 追蹤每個車手的當前輪胎狀態
        
        for record in tyre_data:
            timestamp = record.get('timestamp', '')
            data = record.get('data', {})
            stints = data.get('Stints', {})
            
            for driver_num, driver_stints in stints.items():
                # driver_stints 是 dict: {"0": {...}, "1": {...}}
                if not isinstance(driver_stints, dict):
                    continue
                
                # 找最新的 stint (stint index 最大的)
                latest_stint_idx = None
                latest_stint_data = None
                
                for stint_idx, stint_info in driver_stints.items():
                    if not isinstance(stint_info, dict):
                        continue
                    
                    idx = int(stint_idx) if stint_idx.isdigit() else -1
                    if latest_stint_idx is None or idx > latest_stint_idx:
                        latest_stint_idx = idx
                        latest_stint_data = stint_info
                
                if latest_stint_data:
                    # 更新當前狀態
                    compound = latest_stint_data.get('Compound', current_state.get(driver_num, {}).get('compound', 'UNKNOWN'))
                    age = latest_stint_data.get('TotalLaps', current_state.get(driver_num, {}).get('age', 0))
                    
                    # 忽略 UNKNOWN 配方，保留之前的
                    if compound == 'UNKNOWN' and driver_num in current_state:
                        compound = current_state[driver_num].get('compound', 'MEDIUM')
                    
                    current_state[driver_num] = {
                        'compound': compound,
                        'age': age
                    }
            
            # 記錄此時間點的完整狀態
            if timestamp:
                timeline[timestamp] = dict(current_state)
        
        return timeline
    
    def _build_track_status_timeline(self, track_status_data: List[Dict]) -> Dict[str, str]:
        """
        建立賽道狀態時間線
        
        Returns:
            {timestamp: status}
        """
        timeline = {}
        current_status = "GREEN"
        
        status_map = {
            '1': 'GREEN',
            '2': 'YELLOW',
            '4': 'SC',
            '5': 'RED',
            '6': 'VSC',
            '7': 'VSC_ENDING'
        }
        
        for record in track_status_data:
            timestamp = record.get('timestamp', '')
            data = record.get('data', {})
            status_code = data.get('Status', '')
            
            if status_code in status_map:
                current_status = status_map[status_code]
            
            timeline[timestamp] = current_status
        
        return timeline
    
    def _build_lap_timeline(self, lap_count_data: List[Dict]) -> Dict[str, int]:
        """
        建立圈數時間線
        
        Returns:
            {timestamp: lap_number}
        """
        timeline = {}
        current_lap = 0
        
        for record in lap_count_data:
            timestamp = record.get('timestamp', '')
            data = record.get('data', {})
            
            if 'CurrentLap' in data:
                current_lap = int(data['CurrentLap'])
            
            timeline[timestamp] = current_lap
        
        return timeline
    
    def _build_drs_timeline(self, car_data: List[Dict]) -> Dict[str, Dict[str, int]]:
        """
        建立 DRS 狀態時間線
        
        CarData.json 格式:
        - Channel 45 = DRS (0=關閉, 1=開啟)
        - 車號是字串 (如 "1", "44", "77")
        
        Returns:
            {timestamp: {driver_num: drs_state (0 or 1)}}
        """
        timeline = {}
        
        if not car_data:
            return timeline
        
        for record in car_data:
            timestamp = record.get('timestamp', '')
            data = record.get('data', {})
            entries = data.get('Entries', [])
            
            for entry in entries:
                cars = entry.get('Cars', {})
                drs_states = {}
                
                for driver_num, car_info in cars.items():
                    channels = car_info.get('Channels', {})
                    # Channel 45 = DRS
                    drs_value = channels.get('45', 0)
                    # 確保是整數
                    if isinstance(drs_value, (int, float)):
                        drs_states[driver_num] = 1 if drs_value > 0 else 0
                    else:
                        drs_states[driver_num] = 0
                
                if drs_states:
                    timeline[timestamp] = drs_states
        
        return timeline
    
    def _get_total_laps(self, lap_count_data: List[Dict]) -> int:
        """獲取總圈數"""
        total_laps = 0
        
        for record in lap_count_data:
            data = record.get('data', {})
            if 'TotalLaps' in data:
                total_laps = int(data['TotalLaps'])
                break
        
        return total_laps if total_laps > 0 else 53  # 預設 53 圈
    
    def _detect_overtakes(self,
                         position_timeline: Dict[str, Dict],
                         tyre_state: Dict[str, Dict[str, Dict[str, Any]]],
                         track_status_timeline: Dict[str, str],
                         lap_timeline: Dict[str, int],
                         total_laps: int,
                         year: int,
                         race: str) -> List[OvertakeEvent]:
        """
        從位置時間線偵測超車事件
        
        Args:
            tyre_state: {timestamp: {driver_num: {'compound': str, 'age': int}}}
        """
        overtakes = []
        timestamps = sorted(position_timeline.keys())
        
        if len(timestamps) < 2:
            return overtakes
        
        prev_positions = {}  # {driver: position}
        
        for i, timestamp in enumerate(timestamps):
            current = position_timeline[timestamp]
            
            # 獲取當前圈數和賽道狀態
            lap = self._get_value_at_time(lap_timeline, timestamp, 1)
            track_status = self._get_value_at_time(track_status_timeline, timestamp, "GREEN")
            
            # 跳過非綠旗狀態 (SC/VSC 期間的位置變化不算超車)
            if track_status not in ['GREEN']:
                prev_positions = {d: s['position'] for d, s in current.items()}
                continue
            
            # 比較位置變化
            for driver, state in current.items():
                curr_pos = state['position']
                prev_pos = prev_positions.get(driver)
                
                if prev_pos is None:
                    continue
                
                # 位置提升 = 可能的超車
                if curr_pos < prev_pos:
                    # 找出被超越的車手
                    for other_driver, other_state in current.items():
                        if other_driver == driver:
                            continue
                        
                        other_curr = other_state['position']
                        other_prev = prev_positions.get(other_driver)
                        
                        if other_prev is None:
                            continue
                        
                        # 確認超車: driver 從 prev > other_prev 變成 curr < other_curr
                        if prev_pos > other_prev and curr_pos < other_curr:
                            # 獲取超車前的間距
                            gap_before = state.get('gap', 0)
                            catching_before = state.get('catching', False)
                            
                            # 獲取輪胎狀態 (從時間線查詢)
                            tyre_at_time = self._get_value_at_time(tyre_state, timestamp, {})
                            overtaker_tyre = tyre_at_time.get(driver, {})
                            overtaken_tyre = tyre_at_time.get(other_driver, {})
                            
                            event = OvertakeEvent(
                                timestamp=timestamp,
                                lap=lap,
                                overtaker=driver,
                                overtaken=other_driver,
                                overtaker_new_pos=curr_pos,
                                overtaken_new_pos=other_curr,
                                gap_before=gap_before,
                                catching_before=catching_before,
                                overtaker_tyre=overtaker_tyre.get('compound', ''),
                                overtaker_tyre_age=overtaker_tyre.get('age', 0),
                                overtaken_tyre=overtaken_tyre.get('compound', ''),
                                overtaken_tyre_age=overtaken_tyre.get('age', 0),
                                track_status=track_status,
                                year=year,
                                race=race
                            )
                            overtakes.append(event)
            
            # 更新前一狀態
            prev_positions = {d: s['position'] for d, s in current.items()}
        
        # 去重 (同圈同對只算一次)
        unique_overtakes = []
        seen = set()
        
        for ot in overtakes:
            key = (ot.lap, ot.overtaker, ot.overtaken)
            if key not in seen:
                seen.add(key)
                unique_overtakes.append(ot)
        
        return unique_overtakes
    
    def _generate_training_samples(self,
                                   timing_data: List[Dict],
                                   position_timeline: Dict[str, Dict],
                                   tyre_state: Dict[str, Dict[str, Dict[str, Any]]],
                                   track_status_timeline: Dict[str, str],
                                   lap_timeline: Dict[str, int],
                                   total_laps: int,
                                   overtakes: List[OvertakeEvent],
                                   year: int,
                                   race: str,
                                   drs_timeline: Dict[str, Dict[str, int]] = None) -> List[TrainingSample]:
        """
        生成訓練樣本
        
        正樣本: 超車發生
        負樣本: 間距 < 2 秒但未發生超車的情況
        
        Args:
            tyre_state: {timestamp: {driver_num: {'compound': str, 'age': int}}}
            drs_timeline: {timestamp: {driver_num: drs_state (0 or 1)}}
        """
        samples = []
        
        if drs_timeline is None:
            drs_timeline = {}
        
        # 建立超車索引 (用於標記正樣本)
        overtake_keys = set()
        for ot in overtakes:
            overtake_keys.add((ot.lap, ot.overtaker, ot.overtaken))
        
        # 遍歷時間線，找出所有潛在超車機會
        timestamps = sorted(position_timeline.keys())
        prev_gaps = {}  # {(attacker, defender): prev_gap}
        
        sample_interval = max(1, len(timestamps) // 500)  # 限制樣本數量
        
        for idx, timestamp in enumerate(timestamps):
            if idx % sample_interval != 0:
                continue
            
            current = position_timeline[timestamp]
            lap = self._get_value_at_time(lap_timeline, timestamp, 1)
            track_status = self._get_value_at_time(track_status_timeline, timestamp, "GREEN")
            
            # 按位置排序車手
            sorted_drivers = sorted(
                [(d, s['position']) for d, s in current.items()],
                key=lambda x: x[1]
            )
            
            # 分析相鄰車手對
            for i in range(1, len(sorted_drivers)):
                attacker = sorted_drivers[i][0]
                defender = sorted_drivers[i-1][0]
                
                attacker_state = current[attacker]
                defender_state = current[defender]
                
                gap = attacker_state.get('gap', 999)
                current_lap = attacker_state.get('lap', lap)
                
                # ⚠️ 過濾 Pit 進站樣本
                if attacker_state.get('in_pit', False) or defender_state.get('in_pit', False):
                    continue
                
                # 只分析間距 < 3 秒的情況
                if gap > 3.0:
                    continue
                
                # 計算間距變化
                pair_key = (attacker, defender)
                prev_gap = prev_gaps.get(pair_key, gap)
                gap_delta = gap - prev_gap
                prev_gaps[pair_key] = gap
                
                # 檢查是否為超車事件
                is_overtake = (lap, attacker, defender) in overtake_keys
                
                # 檢查未來 5 圈內是否會發生近距離接觸 (0.2s ≤ gap ≤ 0.3s)
                close_combat_happened = 0
                target_lap_limit = current_lap + 5  # 未來 5 圈
                
                # 向前檢查未來時間點
                for future_idx in range(idx + 1, len(timestamps)):
                    future_timestamp = timestamps[future_idx]
                    future_positions = position_timeline.get(future_timestamp, {})
                    
                    # 檢查這兩個車手在未來的狀態
                    if attacker not in future_positions or defender not in future_positions:
                        continue
                    
                    future_attacker_state = future_positions[attacker]
                    future_defender_state = future_positions[defender]
                    future_lap = future_attacker_state.get('lap', 0)
                    
                    # 超過 5 圈，停止檢查
                    if future_lap > target_lap_limit:
                        break
                    
                    # 如果任一車手進站，停止檢查（Pit 進站會導致 gap 異常）
                    if future_attacker_state.get('in_pit', False) or future_defender_state.get('in_pit', False):
                        break
                    
                    future_gap = future_attacker_state.get('gap', 999)
                    
                    # 如果未來間距進入 0.2-0.3s 區間，標記為近距離接觸
                    if 0.2 <= future_gap <= 0.3:
                        close_combat_happened = 1
                        break
                    
                    # 如果間距擴大超過 2 秒，停止檢查（已經被拉開）
                    if future_gap > gap + 2.0:
                        break
                
                # 獲取輪胎狀態 (從時間線查詢)
                tyre_at_time = self._get_value_at_time(tyre_state, timestamp, {})
                attacker_tyre = tyre_at_time.get(attacker, {})
                defender_tyre = tyre_at_time.get(defender, {})
                
                # 獲取真實的 DRS 狀態 (從 CarData Channel 45)
                drs_at_time = self._get_value_at_time(drs_timeline, timestamp, {})
                attacker_drs = drs_at_time.get(attacker, 0)
                # 如果沒有 DRS 數據，回退到間距判斷
                if not drs_at_time:
                    attacker_drs = 1 if gap < 1.0 else 0
                
                sample = TrainingSample(
                    overtake_happened=1 if is_overtake else 0,
                    gap_seconds=gap,
                    gap_delta=gap_delta,
                    is_catching=1 if attacker_state.get('catching', False) else 0,
                    drs_available=attacker_drs,  # 使用真實 DRS 狀態
                    attacker_tyre_compound=self._encode_compound(attacker_tyre.get('compound', '')),
                    defender_tyre_compound=self._encode_compound(defender_tyre.get('compound', '')),
                    tyre_age_diff=defender_tyre.get('age', 0) - attacker_tyre.get('age', 0),
                    track_status_green=1 if track_status == 'GREEN' else 0,
                    attacker_position=attacker_state['position'],
                    race_progress=lap / total_laps if total_laps > 0 else 0,
                    year=year,
                    race=race,
                    lap=lap,
                    attacker=attacker,
                    defender=defender,
                    close_combat_happened=close_combat_happened  # F85: 近距離接觸標籤
                )
                samples.append(sample)
        
        return samples
    
    def _encode_compound(self, compound: str) -> int:
        """輪胎配方編碼"""
        mapping = {
            'SOFT': 0, 'S': 0,
            'MEDIUM': 1, 'M': 1,
            'HARD': 2, 'H': 2,
            'INTERMEDIATE': 3, 'I': 3,
            'WET': 4, 'W': 4
        }
        return mapping.get(compound.upper(), 1)  # 預設 MEDIUM
    
    def _get_value_at_time(self, timeline: Dict[str, Any], timestamp: str, default: Any) -> Any:
        """獲取時間點的值 (使用最近的較早時間)"""
        if not timeline:
            return default
        
        sorted_times = sorted(timeline.keys())
        
        # 先嘗試找最近的較早時間
        for t in reversed(sorted_times):
            if t <= timestamp:
                value = timeline[t]
                # 如果值是非空字典，直接返回
                if value and (not isinstance(value, dict) or len(value) > 0):
                    return value
        
        # 如果沒找到或值為空，嘗試找第一個非空值
        for t in sorted_times:
            value = timeline[t]
            if value and (not isinstance(value, dict) or len(value) > 0):
                return value
        
        return default
    
    def save_training_data(self, split_by_year: bool = False, validation_year: int = 2025) -> Tuple[Path, Path]:
        """
        保存訓練數據（支援訓練集/驗證集分割）
        
        Args:
            split_by_year: 是否按年份分割訓練集/驗證集
            validation_year: 驗證集的年份閾值（>= 此年份的數據進入驗證集）
        
        Returns:
            (超車事件檔案路徑, 訓練樣本檔案路徑)
        """
        # 保存超車事件
        events_df = pd.DataFrame([asdict(e) for e in self.overtake_events])
        events_path = self.output_dir / "overtake_events.csv"
        events_df.to_csv(events_path, index=False, encoding='utf-8-sig')
        
        # 保存訓練樣本（支援分割模式）
        samples_df = pd.DataFrame([asdict(s) for s in self.training_samples])
        
        if split_by_year:
            # 分割訓練集/驗證集
            train_df = samples_df[samples_df['year'] < validation_year]
            val_df = samples_df[samples_df['year'] >= validation_year]
            
            train_path = self.output_dir / "training_samples.csv"
            val_path = self.output_dir / "validation_samples.csv"
            
            # 檢查是否存在舊檔案
            train_exists = train_path.exists()
            val_exists = val_path.exists()
            
            # 讀取舊資料並合併
            if train_exists:
                old_train_df = pd.read_csv(train_path, encoding='utf-8-sig')
                train_df = pd.concat([old_train_df, train_df], ignore_index=True).drop_duplicates()
            
            if val_exists:
                old_val_df = pd.read_csv(val_path, encoding='utf-8-sig')
                val_df = pd.concat([old_val_df, val_df], ignore_index=True).drop_duplicates()
            
            # 儲存分割後的檔案
            train_df.to_csv(train_path, index=False, encoding='utf-8-sig')
            val_df.to_csv(val_path, index=False, encoding='utf-8-sig')
            
            if self.verbose:
                print(f"\n[F81] ===== 數據保存完成（分割模式）=====")
                print(f"[F81] 超車事件: {events_path} ({len(self.overtake_events)} 筆)")
                print(f"[F81] 訓練樣本: {train_path} ({len(train_df)} 筆)")
                print(f"[F81] 驗證樣本: {val_path} ({len(val_df)} 筆)")
                
                # 統計訓練集
                if len(train_df) > 0:
                    train_positive = (train_df['overtake_happened'] == 1).sum()
                    train_negative = len(train_df) - train_positive
                    print(f"[F81] 訓練集 正樣本: {train_positive}, 負樣本: {train_negative}, 比例: {train_positive/len(train_df):.2%}")
                
                # 統計驗證集
                if len(val_df) > 0:
                    val_positive = (val_df['overtake_happened'] == 1).sum()
                    val_negative = len(val_df) - val_positive
                    print(f"[F81] 驗證集 正樣本: {val_positive}, 負樣本: {val_negative}, 比例: {val_positive/len(val_df):.2%}")
            
            samples_path = train_path
        
        else:
            # 原始模式：統一保存
            samples_path = self.output_dir / "training_samples.csv"
            samples_df.to_csv(samples_path, index=False, encoding='utf-8-sig')
            
            if self.verbose:
                print(f"\n[F81] ===== 數據保存完成 =====")
                print(f"[F81] 超車事件: {events_path} ({len(self.overtake_events)} 筆)")
                print(f"[F81] 訓練樣本: {samples_path} ({len(self.training_samples)} 筆)")
                
                # 統計
                if self.training_samples:
                    positive = sum(1 for s in self.training_samples if s.overtake_happened == 1)
                    negative = len(self.training_samples) - positive
                    print(f"[F81] 正樣本: {positive}, 負樣本: {negative}, 比例: {positive/len(self.training_samples):.2%}")
        
        return events_path, samples_path
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取收集統計摘要"""
        summary = {
            **self.stats,
            'overtake_events': len(self.overtake_events),
            'training_samples': len(self.training_samples),
        }
        
        if self.training_samples:
            positive = sum(1 for s in self.training_samples if s.overtake_happened == 1)
            summary['positive_samples'] = positive
            summary['negative_samples'] = len(self.training_samples) - positive
            summary['positive_ratio'] = positive / len(self.training_samples)
        
        return summary


# ============================================================================
# CLI 入口點
# ============================================================================
def run_f81_data_collection(years: List[int] = None, 
                            split_by_year: bool = False,
                            validation_year: int = 2025,
                            verbose: bool = True) -> Dict[str, Any]:
    """
    執行 F81 超車數據收集
    
    Args:
        years: 要收集的年份列表，None 則收集所有可用年份
        split_by_year: 是否按年份分割訓練集/驗證集（預設 False）
        validation_year: 驗證集的年份閾值（>= 此年份的數據進入驗證集，預設 2025）
        verbose: 是否顯示詳細輸出
        
    Returns:
        收集統計
    """
    print("=" * 70)
    print("F81: 超車事件數據收集器")
    if split_by_year:
        print(f"模式: 訓練集（< {validation_year}）/ 驗證集（>= {validation_year}）分割")
    else:
        print("模式: 統一收集")
    print("=" * 70)
    
    collector = OvertakeDataCollector(verbose=verbose)
    collector.collect_all(years=years)
    collector.save_training_data(split_by_year=split_by_year, validation_year=validation_year)
    
    summary = collector.get_summary()
    
    print("\n" + "=" * 70)
    print("收集完成!")
    print(f"  - 處理賽事: {summary['races_processed']}")
    print(f"  - 超車事件: {summary['total_overtakes']}")
    print(f"  - 訓練樣本: {summary['total_samples']}")
    if 'positive_ratio' in summary:
        print(f"  - 正樣本比例: {summary['positive_ratio']:.2%}")
    print("=" * 70)
    
    return summary


if __name__ == "__main__":
    # 測試執行
    run_f81_data_collection(years=[2024])
