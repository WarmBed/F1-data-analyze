#!/usr/bin/env python3
"""
F101 起跑反應分析數據載入器
Start Reaction Analysis Data Loader

從 Live Timing JSON 數據中分析：
- 起跑反應速度（第二批次時的速度，確保所有車手都有數據）
- 0-10 km/h 離合器反應時間
- 0-20 km/h 加速時間（起步反應）
- 首圈位置變化

作者: F1T Team
日期: 2025-12-22
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# 使用標準 logging 避免 core.logger 卡住
logger = logging.getLogger(__name__)


# 2025 車手代號對照
DRIVER_NAMES = {
    '1': 'VER', '4': 'NOR', '5': 'BEA', '6': 'TSU', '10': 'GAS',
    '12': 'DOO', '14': 'ALO', '16': 'LEC', '18': 'STR', '22': 'ANT',
    '23': 'ALB', '27': 'HUL', '30': 'RIC', '31': 'OCO', '43': 'COL',
    '44': 'HAM', '55': 'SAI', '63': 'RUS', '81': 'PIA', '87': 'HAD'
}


def parse_timestamp(ts: str) -> float:
    """解析 timestamp 字串為秒數"""
    if not ts:
        return 0.0
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def interpolate_time(t1: float, v1: float, t2: float, v2: float, target_v: float) -> float:
    """線性插值計算達到目標速度的時間"""
    if v2 == v1:
        return t1
    ratio = (target_v - v1) / (v2 - v1)
    return t1 + ratio * (t2 - t1)


class StartReactionDataLoader:
    """
    起跑反應數據載入器
    
    從 Live Timing JSON 文件載入並分析起跑數據
    """
    
    def __init__(self, year: int, race: str, session: str = "R"):
        """
        初始化載入器
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 場次 (預設 R = Race)
        """
        self.year = year
        self.race = race
        self.session = session
        
        # 構建 Live Timing 目錄路徑
        race_folder_name = f"{race.replace(' ', '_')}_{self._session_to_folder(session)}"
        self.race_dir = Path(f"json/LiveF1/{year}/{race_folder_name}")
        
        logger.debug(f"[START_REACTION_LOADER] Init: {self.race_dir}")
    
    def _session_to_folder(self, session: str) -> str:
        """將 session 代碼轉換為資料夾名稱"""
        mapping = {
            'R': 'Race',
            'Q': 'Qualifying',
            'SQ': 'Sprint_Qualifying',
            'S': 'Sprint',
            'FP1': 'Practice_1',
            'FP2': 'Practice_2',
            'FP3': 'Practice_3',
        }
        return mapping.get(session.upper(), session)
    
    def load_data(self) -> Optional[Dict[str, Any]]:
        """
        載入並分析起跑反應數據
        
        Returns:
            分析結果字典，包含所有車手數據
        """
        if not self.race_dir.exists():
            logger.warning(f"[START_REACTION_LOADER] Race directory not found: {self.race_dir}")
            return None
        
        try:
            # 1. 獲取賽事開始時間
            race_start_ts = self._get_race_start_time()
            if race_start_ts is None:
                logger.error("[START_REACTION_LOADER] Cannot determine race start time")
                return None
            
            logger.info(f"[START_REACTION_LOADER] Race start: {race_start_ts:.2f}s")
            
            # 2. 獲取 Lap 2 開始時間（用於確定首圈結束）
            lap2_start_ts = self._get_lap2_start_time()
            
            # 3. 分析加速數據
            accel_data = self._analyze_acceleration(race_start_ts)
            
            # 4. 分析起跑反應速度（第二批次）
            reaction_data = self._analyze_reaction_speed(race_start_ts)
            
            # 5. 分析位置變化
            position_data = self._analyze_position_changes(lap2_start_ts)
            
            # 6. 合併數據
            drivers = self._merge_data(accel_data, position_data, reaction_data)
            
            return {
                'year': self.year,
                'race': self.race,
                'session': self.session,
                'race_start_ts': race_start_ts,
                'reaction_batch_time': reaction_data.get('batch_time', 0),
                'drivers': drivers
            }
            
        except Exception as e:
            logger.error(f"[START_REACTION_LOADER] Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_race_start_time(self) -> Optional[float]:
        """從 SessionData 獲取燈滅起跑時間"""
        session_file = self.race_dir / 'SessionData.json'
        
        if not session_file.exists():
            return None
        
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for rec in data.get('records', []):
            status = rec.get('data', {}).get('StatusSeries', {})
            if isinstance(status, dict):
                for key, val in status.items():
                    if isinstance(val, dict) and val.get('SessionStatus') == 'Started':
                        return parse_timestamp(rec.get('timestamp', ''))
        
        return None
    
    def _get_lap2_start_time(self) -> float:
        """從 LapCount 獲取 Lap 2 開始時間"""
        lapcount_file = self.race_dir / 'LapCount.json'
        
        if not lapcount_file.exists():
            return 9999999
        
        with open(lapcount_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for rec in data.get('records', []):
            if rec.get('data', {}).get('CurrentLap', 0) == 2:
                return parse_timestamp(rec.get('timestamp', ''))
        
        return 9999999
    
    def _analyze_acceleration(self, race_start_ts: float) -> Dict[str, Dict]:
        """分析加速數據"""
        cardata_file = self.race_dir / 'CarData.json'
        
        if not cardata_file.exists():
            return {}
        
        with open(cardata_file, 'r', encoding='utf-8') as f:
            cardata = json.load(f)
        
        # 初始化車手速度歷史
        driver_speeds: Dict[str, List[Tuple[float, int]]] = {
            d: [] for d in DRIVER_NAMES.keys()
        }
        
        records = cardata.get('records', [])
        
        for rec in records:
            ts = parse_timestamp(rec.get('timestamp', ''))
            
            # 只分析起跑後 30 秒內的數據
            if ts < race_start_ts or ts > race_start_ts + 30:
                continue
            
            entries = rec.get('data', {}).get('Entries', [])
            if not entries:
                continue
            
            cars = entries[0].get('Cars', {})
            
            for drv in DRIVER_NAMES.keys():
                if drv in cars:
                    speed = cars[drv].get('Channels', {}).get('2', 0)
                    relative_time = ts - race_start_ts
                    driver_speeds[drv].append((relative_time, speed))
        
        # 計算加速時間（使用插值）
        results = {}
        
        for drv, speeds in driver_speeds.items():
            if not speeds:
                results[drv] = {'t10': None, 't20': None, 'max_speed': 0}
                continue
            
            t10, t20 = None, None
            max_spd = 0
            
            for i in range(1, len(speeds)):
                t_prev, v_prev = speeds[i-1]
                t_curr, v_curr = speeds[i]
                max_spd = max(max_spd, v_curr)
                
                # 插值計算 0-10 km/h (離合器反應)
                if t10 is None and v_prev < 10 <= v_curr:
                    t10 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 10)
                
                # 插值計算 0-20 km/h (起步反應)
                if t20 is None and v_prev < 20 <= v_curr:
                    t20 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 20)
            
            results[drv] = {'t10': t10, 't20': t20, 'max_speed': max_spd}
        
        return results
    
    def _analyze_reaction_speed(self, race_start_ts: float) -> Dict[str, Any]:
        """
        分析起跑反應速度（使用第二批次數據）
        
        第二批次確保所有車手都有數據，速度越高代表反應越快
        """
        cardata_file = self.race_dir / 'CarData.json'
        
        if not cardata_file.exists():
            return {'batch_time': 0, 'speeds': {}}
        
        with open(cardata_file, 'r', encoding='utf-8') as f:
            cardata = json.load(f)
        
        records = cardata.get('records', [])
        batches = []
        
        for rec in records:
            ts = parse_timestamp(rec.get('timestamp', ''))
            
            # 只看綠燈後 5 秒內
            if ts < race_start_ts or ts > race_start_ts + 5:
                continue
            
            entries = rec.get('data', {}).get('Entries', [])
            if not entries:
                continue
            
            cars = entries[0].get('Cars', {})
            
            # 收集這批次有速度的車手
            batch_speeds = {}
            for drv_num, name in DRIVER_NAMES.items():
                if drv_num in cars:
                    speed = cars[drv_num].get('Channels', {}).get('2', 0)
                    if speed > 0:
                        batch_speeds[drv_num] = speed
            
            if batch_speeds:
                batches.append({
                    'time': ts - race_start_ts,
                    'speeds': batch_speeds
                })
        
        # 使用第二批次（確保所有車手都有數據）
        if len(batches) >= 2:
            second_batch = batches[1]
            return {
                'batch_time': second_batch['time'],
                'speeds': second_batch['speeds']
            }
        elif len(batches) == 1:
            return {
                'batch_time': batches[0]['time'],
                'speeds': batches[0]['speeds']
            }
        
        return {'batch_time': 0, 'speeds': {}}
    
    def _analyze_position_changes(self, lap2_start_ts: float) -> Dict[str, Dict]:
        """分析首圈位置變化"""
        timing_file = self.race_dir / 'TimingData.json'
        
        if not timing_file.exists():
            return {}
        
        with open(timing_file, 'r', encoding='utf-8') as f:
            timing = json.load(f)
        
        drivers_pos = {}
        
        for rec in timing.get('records', []):
            ts = parse_timestamp(rec.get('timestamp', ''))
            lines = rec.get('data', {}).get('Lines', {})
            
            for drv, data in lines.items():
                if not isinstance(data, dict):
                    continue
                
                pos = data.get('Position')
                if pos is None:
                    continue
                
                pos = int(pos)
                
                if drv not in drivers_pos:
                    drivers_pos[drv] = {'grid': pos, 'lap1_pos': None}
                
                if drivers_pos[drv]['grid'] is None:
                    drivers_pos[drv]['grid'] = pos
                
                if ts < lap2_start_ts:
                    drivers_pos[drv]['lap1_pos'] = pos
        
        return drivers_pos
    
    def _merge_data(self, accel_data: Dict, position_data: Dict, reaction_data: Dict) -> List[Dict]:
        """合併加速、位置和反應速度數據"""
        drivers = []
        
        reaction_speeds = reaction_data.get('speeds', {})
        all_driver_nums = set(accel_data.keys()) | set(position_data.keys()) | set(reaction_speeds.keys())
        
        for drv_num in all_driver_nums:
            name = DRIVER_NAMES.get(drv_num, f'#{drv_num}')
            
            accel = accel_data.get(drv_num, {})
            pos = position_data.get(drv_num, {})
            
            grid = pos.get('grid')
            lap1_pos = pos.get('lap1_pos')
            position_delta = (grid - lap1_pos) if grid and lap1_pos else 0
            
            # 起跑反應速度（第二批次時的速度）
            reaction_speed = reaction_speeds.get(drv_num, 0)
            
            driver_data = {
                'driver_num': drv_num,
                'name': name,
                'reaction_speed': reaction_speed,  # 新增：起跑反應速度
                't10': accel.get('t10'),
                't20': accel.get('t20'),
                'max_speed': accel.get('max_speed', 0),
                'grid': grid,
                'lap1_pos': lap1_pos,
                'position_delta': position_delta
            }
            
            drivers.append(driver_data)
        
        # 按 grid 排序
        drivers.sort(key=lambda d: d.get('grid') or 99)
        
        return drivers
