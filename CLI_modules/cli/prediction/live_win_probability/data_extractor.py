"""
Live Win Probability - Training Data Extractor

此模組負責從 LiveF1 JSON 數據提取訓練用特徵，用於勝率預測模型。

資料來源:
- LapSeries.json: 每圈位置，用於生成標籤（最終名次）
- Position.json: 即時 GPS 位置
- TimingData.json: 圈時、差距、最佳圈時等
- TyreStintSeries.json: 輪胎配方和 stint 數據
- DriverList.json: 車手資訊（車號對應車手代碼）

特徵說明 (18 個):
[即時特徵 - 12 個]
1. position: 當前位置 (1-20)
2. gap_to_leader: 與領先者差距（秒）
3. gap_to_ahead: 與前車差距（秒）
4. lap_time: 當圈圈時（秒）
5. best_lap_time: 個人最佳圈時（秒）
6. tyre_compound: 輪胎配方 (SOFT=1, MEDIUM=2, HARD=3, INTER=4, WET=5)
7. tyre_age: 輪胎使用圈數
8. pit_count: 進站次數
9. laps_remaining: 剩餘圈數
10. track_status: 賽道狀態 (GREEN=1, YELLOW=2, SC=3, VSC=4, RED=5)
11. air_temp: 空氣溫度（攝氏）
12. rainfall: 降雨量 (0=乾燥, 1=潮濕, 2=大雨)

[歷史/靜態特徵 - 6 個]
13. driver_win_rate: 車手歷史勝率
14. driver_podium_rate: 車手歷史登台率
15. team_rating: 車隊評分 (1-10)
16. circuit_overtake_rate: 賽道超車率
17. circuit_sc_rate: 賽道安全車出動率
18. qualifying_position: 排位賽位置

標籤:
- final_position: 最終名次 (1-20, DNF=21)

作者: F1T Dev Team
日期: 2025-01
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DriverState:
    """車手當前圈的狀態"""
    driver_number: str
    driver_code: str = ""
    position: int = 0
    gap_to_leader: float = 0.0
    gap_to_ahead: float = 0.0
    lap_time: float = 0.0
    best_lap_time: float = 0.0
    tyre_compound: int = 2  # 預設 MEDIUM
    tyre_age: int = 0
    pit_count: int = 0
    current_lap: int = 0


@dataclass
class RaceState:
    """比賽當前圈的狀態"""
    current_lap: int = 0
    total_laps: int = 0
    laps_remaining: int = 0
    track_status: int = 1  # GREEN
    air_temp: float = 25.0
    rainfall: int = 0
    drivers: Dict[str, DriverState] = field(default_factory=dict)


@dataclass
class TrainingSample:
    """一個訓練樣本"""
    # 識別資訊
    year: int
    race_name: str
    driver_code: str
    current_lap: int
    
    # 即時特徵
    position: int
    gap_to_leader: float
    gap_to_ahead: float
    lap_time: float
    best_lap_time: float
    tyre_compound: int
    tyre_age: int
    pit_count: int
    laps_remaining: int
    track_status: int
    air_temp: float
    rainfall: int
    
    # 歷史特徵
    driver_win_rate: float = 0.0
    driver_podium_rate: float = 0.0
    team_rating: float = 5.0
    circuit_overtake_rate: float = 0.5
    circuit_sc_rate: float = 0.3
    qualifying_position: int = 10
    
    # 標籤
    final_position: int = 21  # 預設 DNF


class LiveWinProbabilityDataExtractor:
    """
    從 LiveF1 JSON 數據提取訓練特徵
    
    使用方法:
    ```python
    extractor = LiveWinProbabilityDataExtractor(base_path="json/LiveF1")
    samples = extractor.extract_race_data(2025, "Japanese")
    df = extractor.to_dataframe(samples)
    ```
    """
    
    # 輪胎配方編碼
    TYRE_COMPOUND_MAP = {
        'SOFT': 1, 'S': 1,
        'MEDIUM': 2, 'M': 2,
        'HARD': 3, 'H': 3,
        'INTERMEDIATE': 4, 'I': 4,
        'WET': 5, 'W': 5,
    }
    
    # 賽道狀態編碼
    TRACK_STATUS_MAP = {
        'GREEN': 1, 'AllClear': 1, '1': 1,
        'YELLOW': 2, 'Yellow': 2, '2': 2,
        'SC': 3, 'SCDeployed': 3, '4': 3,
        'VSC': 4, 'VSCDeployed': 4, '6': 4,
        'RED': 5, 'Red': 5, '5': 5,
    }
    
    def __init__(self, base_path: str = "json/LiveF1"):
        """
        初始化數據提取器
        
        Args:
            base_path: LiveF1 JSON 數據的根目錄
        """
        self.base_path = Path(base_path)
        self._driver_code_cache: Dict[str, str] = {}  # driver_number -> driver_code
        self._historical_stats = self._load_historical_stats()
        
    def _load_historical_stats(self) -> Dict:
        """載入車手和車隊歷史統計數據"""
        # TODO: 從外部 JSON 檔案載入
        # 暫時使用預設值
        return {
            'driver_win_rate': {},
            'driver_podium_rate': {},
            'team_rating': {},
            'circuit_overtake_rate': {},
            'circuit_sc_rate': {},
        }
    
    def _find_race_folder(self, year: int, race_name: str) -> Optional[Path]:
        """
        尋找比賽資料夾
        
        Args:
            year: 年份
            race_name: 比賽名稱（支援部分匹配）
            
        Returns:
            比賽資料夾路徑，若未找到則返回 None
        """
        year_path = self.base_path / str(year)
        if not year_path.exists():
            logger.warning(f"Year folder not found: {year_path}")
            return None
            
        # 尋找匹配的比賽資料夾
        race_name_lower = race_name.lower()
        for folder in year_path.iterdir():
            if folder.is_dir():
                folder_name_lower = folder.name.lower()
                # 支援 "Japanese_Race", "Japan", "japanese" 等格式
                if race_name_lower in folder_name_lower or folder_name_lower.startswith(race_name_lower):
                    return folder
                    
        logger.warning(f"Race folder not found for {race_name} in {year_path}")
        return None
    
    def _load_json_file(self, file_path: Path) -> Optional[Any]:
        """
        載入 JSON 檔案
        
        Args:
            file_path: JSON 檔案路徑
            
        Returns:
            解析後的 JSON 數據，若失敗則返回 None
        """
        if not file_path.exists():
            logger.debug(f"JSON file not found: {file_path}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {file_path}, error: {e}")
            return None
    
    def _get_records(self, data: Any) -> List[Dict]:
        """
        從 JSON 數據中提取記錄列表
        
        支援兩種格式:
        1. {"metadata": {...}, "records": [...]}
        2. [...]  (直接列表)
        
        Args:
            data: JSON 數據
            
        Returns:
            記錄列表
        """
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'records' in data:
            return data['records']
        return []
    
    def _parse_timestamp(self, timestamp_str: str) -> float:
        """
        解析時間戳字串為秒數
        
        格式: "HH:MM:SS.mmm" 或 "MM:SS.mmm"
        
        Args:
            timestamp_str: 時間戳字串
            
        Returns:
            總秒數
        """
        if not timestamp_str:
            return 0.0
            
        try:
            parts = timestamp_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
            else:
                return float(timestamp_str)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_lap_time(self, lap_time_str: str) -> float:
        """
        解析圈時字串
        
        格式: "1:32.456" 或 "92.456"
        
        Args:
            lap_time_str: 圈時字串
            
        Returns:
            圈時（秒）
        """
        if not lap_time_str or lap_time_str in ['', 'None', 'null']:
            return 0.0
            
        try:
            # 處理 "1:32.456" 格式
            if ':' in str(lap_time_str):
                parts = str(lap_time_str).split(':')
                if len(parts) == 2:
                    return float(parts[0]) * 60 + float(parts[1])
            return float(lap_time_str)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_gap(self, gap_str: str) -> float:
        """
        解析差距字串
        
        格式: "+1.234", "1 LAP", "2 LAPS", "-"
        
        Args:
            gap_str: 差距字串
            
        Returns:
            差距（秒），圈數差用 999 表示
        """
        if not gap_str or gap_str in ['', '-', 'None', 'null']:
            return 0.0
            
        gap_str = str(gap_str).strip().upper()
        
        # 處理圈數差
        if 'LAP' in gap_str:
            try:
                laps = int(re.search(r'(\d+)', gap_str).group(1))
                return laps * 90  # 假設每圈約 90 秒
            except (AttributeError, ValueError):
                return 999.0
                
        # 處理秒數差
        try:
            gap_str = gap_str.replace('+', '').replace('S', '')
            return float(gap_str)
        except (ValueError, TypeError):
            return 0.0
    
    def _build_driver_code_map(self, race_folder: Path) -> Dict[str, str]:
        """
        建立車號到車手代碼的映射
        
        Args:
            race_folder: 比賽資料夾路徑
            
        Returns:
            {driver_number: driver_code} 映射
        """
        driver_list_path = race_folder / "DriverList.json"
        data = self._load_json_file(driver_list_path)
        
        if not data:
            logger.warning(f"DriverList.json not found in {race_folder}")
            return {}
            
        driver_map = {}
        
        # 處理不同格式
        if isinstance(data, dict):
            if 'records' in data:
                # 新格式：有 metadata
                for record in data['records']:
                    if 'data' in record:
                        for num, info in record['data'].items():
                            if 'Tla' in info:
                                driver_map[num] = info['Tla']
            else:
                # 舊格式：直接 {driver_number: info}
                for num, info in data.items():
                    if isinstance(info, dict) and 'Tla' in info:
                        driver_map[num] = info['Tla']
                        
        return driver_map
    
    def _extract_total_laps(self, lap_series_data: Any) -> int:
        """
        從 LapSeries 數據提取總圈數
        
        Args:
            lap_series_data: LapSeries JSON 數據
            
        Returns:
            總圈數
        """
        records = self._get_records(lap_series_data)
        max_lap = 0
        
        for record in records:
            if 'data' not in record:
                continue
            for driver_num, driver_data in record['data'].items():
                if 'LapPosition' in driver_data:
                    lap_position = driver_data['LapPosition']
                    if isinstance(lap_position, dict):
                        for lap_str in lap_position.keys():
                            try:
                                lap = int(lap_str)
                                max_lap = max(max_lap, lap)
                            except ValueError:
                                continue
                                
        return max_lap
    
    def _extract_final_positions(self, lap_series_data: Any, total_laps: int) -> Dict[str, int]:
        """
        從 LapSeries 數據提取最終名次
        
        Args:
            lap_series_data: LapSeries JSON 數據
            total_laps: 總圈數
            
        Returns:
            {driver_number: final_position} 映射
        """
        records = self._get_records(lap_series_data)
        final_positions = {}
        
        # 從最後一圈的記錄提取位置
        for record in reversed(records):
            if 'data' not in record:
                continue
            for driver_num, driver_data in record['data'].items():
                if driver_num in final_positions:
                    continue
                if 'LapPosition' in driver_data:
                    lap_position = driver_data['LapPosition']
                    if isinstance(lap_position, dict):
                        # 尋找最後一圈的位置
                        for lap_str, position_str in lap_position.items():
                            try:
                                lap = int(lap_str)
                                # 找接近總圈數的記錄
                                if lap >= total_laps - 2:
                                    final_positions[driver_num] = int(position_str)
                            except ValueError:
                                continue
                                
        return final_positions
    
    def _build_lap_positions_index(self, lap_series_data: Any) -> Dict[int, Dict[str, int]]:
        """
        建立每圈位置索引
        
        Args:
            lap_series_data: LapSeries JSON 數據
            
        Returns:
            {lap_number: {driver_number: position}} 索引
        """
        records = self._get_records(lap_series_data)
        lap_positions = {}  # {lap: {driver_num: position}}
        
        for record in records:
            if 'data' not in record:
                continue
            for driver_num, driver_data in record['data'].items():
                if 'LapPosition' in driver_data:
                    lap_position = driver_data['LapPosition']
                    if isinstance(lap_position, dict):
                        for lap_str, position_str in lap_position.items():
                            try:
                                lap = int(lap_str)
                                position = int(position_str)
                                if lap not in lap_positions:
                                    lap_positions[lap] = {}
                                lap_positions[lap][driver_num] = position
                            except ValueError:
                                continue
                    elif isinstance(lap_position, list):
                        # 第一條記錄的初始位置格式
                        for idx, pos in enumerate(lap_position):
                            if 0 not in lap_positions:
                                lap_positions[0] = {}
                            lap_positions[0][driver_num] = idx + 1
                                
        return lap_positions
    
    def _build_timing_index_by_lap(self, timing_data: Any, lap_series_data: Any) -> Dict[int, Dict[str, Dict[str, Any]]]:
        """
        建立按圈數組織的計時數據索引
        
        由於 TimingData 是增量更新，我們需要按時間戳追蹤每位車手的最新狀態。
        然後根據 LapSeries 的時間戳來對應每圈的數據。
        
        Args:
            timing_data: TimingData JSON 數據
            lap_series_data: LapSeries JSON 數據
            
        Returns:
            {lap_number: {driver_number: {timing_info}}} 索引
        """
        # 首先，建立按時間戳組織的 timing 狀態
        timing_records = self._get_records(timing_data)
        
        # 累積每位車手的最新狀態
        driver_state = {}  # {driver_num: {最新完整狀態}}
        
        # 按時間順序處理所有 timing 記錄，累積狀態
        for record in timing_records:
            if 'data' not in record:
                continue
            data = record['data']
            lines = data.get('Lines', data)
            
            for driver_num, timing_info in lines.items():
                if driver_num == 'Lines':
                    continue
                if driver_num not in driver_state:
                    driver_state[driver_num] = {}
                if isinstance(timing_info, dict):
                    for key, value in timing_info.items():
                        if value is not None and value != '':
                            driver_state[driver_num][key] = value
        
        # 返回最終狀態（簡化版，對所有圈使用相同狀態）
        # TODO: 未來可以改進為按時間戳精確對應每圈
        return driver_state
    
    def _build_timing_index(self, timing_data: Any) -> Dict[str, Dict[str, Any]]:
        """
        建立計時數據索引（車手最新狀態）
        
        TimingData.json 格式:
        {"records": [{"timestamp": "...", "data": {"Lines": {"driver_num": {...}}}}]}
        
        Args:
            timing_data: TimingData JSON 數據
            
        Returns:
            {driver_number: {timing_info}} 索引
        """
        records = self._get_records(timing_data)
        driver_timing = {}  # {driver_num: latest_timing}
        
        for record in records:
            if 'data' not in record:
                continue
                
            data = record['data']
            
            # TimingData 使用 "Lines" 作為車手數據的容器
            lines = data.get('Lines', data)  # 兼容兩種格式
            
            for driver_num, timing_info in lines.items():
                if driver_num == 'Lines':  # 跳過 key 本身
                    continue
                if driver_num not in driver_timing:
                    driver_timing[driver_num] = {}
                # 更新最新資訊（增量合併）
                if isinstance(timing_info, dict):
                    for key, value in timing_info.items():
                        if value is not None and value != '':
                            driver_timing[driver_num][key] = value
                            
        return driver_timing
    
    def _build_tyre_index(self, tyre_data: Any) -> Dict[str, Dict[str, Any]]:
        """
        建立輪胎數據索引
        
        TyreStintSeries.json 格式:
        {"records": [{"timestamp": "...", "data": {"Stints": {"driver_num": {"stint_num": {...}}}}}]}
        
        stint 編號解讀:
        - "0": 起始輪胎 (pit_count = 0)
        - "1": 第一次進站後 (pit_count = 1)
        - "2": 第二次進站後 (pit_count = 2)
        
        Args:
            tyre_data: TyreStintSeries JSON 數據
            
        Returns:
            {driver_number: {tyre_info}} 索引，包含當前配方、使用圈數、stint 次數
        """
        records = self._get_records(tyre_data)
        driver_tyre = {}  # {driver_num: {compound, age, pit_count, max_stint}}
        
        for record in records:
            if 'data' not in record:
                continue
                
            data = record['data']
            stints_data = data.get('Stints', {})
            
            if not isinstance(stints_data, dict):
                continue
                
            # stints_data: {"driver_num": {"stint_num": {...}}}
            for driver_num, driver_stints in stints_data.items():
                if not isinstance(driver_stints, dict):
                    continue
                    
                if driver_num not in driver_tyre:
                    driver_tyre[driver_num] = {
                        'compound': 'MEDIUM',
                        'age': 0,
                        'pit_count': 0,
                        'max_stint': 0
                    }
                
                # driver_stints: {"0": {...}, "1": {...}}
                for stint_num, stint_data in driver_stints.items():
                    if not stint_num.isdigit():
                        continue
                        
                    stint_int = int(stint_num)
                    
                    # 更新最大 stint 編號（即 pit_count）
                    if stint_int > driver_tyre[driver_num]['max_stint']:
                        driver_tyre[driver_num]['max_stint'] = stint_int
                        driver_tyre[driver_num]['pit_count'] = stint_int
                    
                    # 如果是當前最大 stint，更新配方和圈數
                    if stint_int == driver_tyre[driver_num]['max_stint']:
                        if isinstance(stint_data, dict):
                            # 更新配方
                            if 'Compound' in stint_data:
                                compound = stint_data['Compound']
                                if compound and compound != 'UNKNOWN':
                                    driver_tyre[driver_num]['compound'] = compound
                            # 更新圈數
                            if 'TotalLaps' in stint_data:
                                try:
                                    driver_tyre[driver_num]['age'] = int(stint_data['TotalLaps'])
                                except (ValueError, TypeError):
                                    pass
                                
        return driver_tyre
    
    def extract_race_data(self, year: int, race_name: str) -> List[TrainingSample]:
        """
        從指定比賽提取所有訓練樣本
        
        每圈為每位車手生成一個樣本，標籤為最終名次。
        
        Args:
            year: 年份
            race_name: 比賽名稱
            
        Returns:
            訓練樣本列表
        """
        # 尋找比賽資料夾
        race_folder = self._find_race_folder(year, race_name)
        if not race_folder:
            logger.error(f"Race folder not found: {year} {race_name}")
            return []
            
        logger.info(f"Extracting data from: {race_folder}")
        
        # 載入所有 JSON 數據
        lap_series_data = self._load_json_file(race_folder / "LapSeries.json")
        timing_data = self._load_json_file(race_folder / "TimingData.json")
        tyre_data = self._load_json_file(race_folder / "TyreStintSeries.json")
        
        if not lap_series_data:
            logger.error(f"LapSeries.json not found in {race_folder}")
            return []
            
        # 建立索引
        driver_code_map = self._build_driver_code_map(race_folder)
        total_laps = self._extract_total_laps(lap_series_data)
        final_positions = self._extract_final_positions(lap_series_data, total_laps)
        lap_positions = self._build_lap_positions_index(lap_series_data)
        timing_index = self._build_timing_index(timing_data) if timing_data else {}
        tyre_index = self._build_tyre_index(tyre_data) if tyre_data else {}
        
        logger.info(f"Total laps: {total_laps}, Drivers: {len(driver_code_map)}")
        logger.info(f"Final positions: {final_positions}")
        
        # 生成訓練樣本
        samples = []
        
        for lap in range(1, total_laps + 1):
            if lap not in lap_positions:
                continue
                
            laps_remaining = total_laps - lap
            
            for driver_num, position in lap_positions[lap].items():
                driver_code = driver_code_map.get(driver_num, f"D{driver_num}")
                
                # 獲取計時數據
                timing_info = timing_index.get(driver_num, {})
                
                # 計算差距
                gap_to_leader = 0.0
                gap_to_ahead = 0.0
                
                if position == 1:
                    gap_to_leader = 0.0
                    gap_to_ahead = 0.0
                else:
                    # 從 TimingData 獲取差距
                    if 'GapToLeader' in timing_info:
                        gap_to_leader = self._parse_gap(timing_info['GapToLeader'])
                    if 'IntervalToPositionAhead' in timing_info:
                        gap_to_ahead = self._parse_gap(timing_info['IntervalToPositionAhead'].get('Value', ''))
                
                # 獲取圈時
                lap_time = 0.0
                best_lap_time = 0.0
                if 'LastLapTime' in timing_info:
                    last_lap_info = timing_info['LastLapTime']
                    if isinstance(last_lap_info, dict):
                        lap_time = self._parse_lap_time(last_lap_info.get('Value', ''))
                    else:
                        lap_time = self._parse_lap_time(last_lap_info)
                if 'BestLapTime' in timing_info:
                    best_lap_info = timing_info['BestLapTime']
                    if isinstance(best_lap_info, dict):
                        best_lap_time = self._parse_lap_time(best_lap_info.get('Value', ''))
                    else:
                        best_lap_time = self._parse_lap_time(best_lap_info)
                
                # 獲取輪胎數據
                tyre_info = tyre_index.get(driver_num, {'compound': 'MEDIUM', 'age': 0, 'pit_count': 0})
                tyre_compound = self.TYRE_COMPOUND_MAP.get(tyre_info['compound'].upper(), 2)
                tyre_age = tyre_info['age']
                pit_count = tyre_info.get('pit_count', 0)  # pit_count = max stint number
                
                # 獲取最終名次
                final_position = final_positions.get(driver_num, 21)  # DNF = 21
                
                sample = TrainingSample(
                    year=year,
                    race_name=race_name,
                    driver_code=driver_code,
                    current_lap=lap,
                    position=position,
                    gap_to_leader=gap_to_leader,
                    gap_to_ahead=gap_to_ahead,
                    lap_time=lap_time,
                    best_lap_time=best_lap_time,
                    tyre_compound=tyre_compound,
                    tyre_age=tyre_age,
                    pit_count=pit_count,
                    laps_remaining=laps_remaining,
                    track_status=1,  # TODO: 從 RaceControlMessages 獲取
                    air_temp=25.0,  # TODO: 從 WeatherData 獲取
                    rainfall=0,  # TODO: 從 WeatherData 獲取
                    final_position=final_position,
                )
                samples.append(sample)
                
        logger.info(f"Generated {len(samples)} samples from {race_name} {year}")
        return samples
    
    def to_dataframe(self, samples: List[TrainingSample]):
        """
        將樣本列表轉換為 pandas DataFrame
        
        Args:
            samples: 訓練樣本列表
            
        Returns:
            pandas DataFrame
        """
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas not installed. Please install pandas to use this method.")
            raise
            
        data = []
        for sample in samples:
            data.append({
                'year': sample.year,
                'race_name': sample.race_name,
                'driver_code': sample.driver_code,
                'current_lap': sample.current_lap,
                'position': sample.position,
                'gap_to_leader': sample.gap_to_leader,
                'gap_to_ahead': sample.gap_to_ahead,
                'lap_time': sample.lap_time,
                'best_lap_time': sample.best_lap_time,
                'tyre_compound': sample.tyre_compound,
                'tyre_age': sample.tyre_age,
                'pit_count': sample.pit_count,
                'laps_remaining': sample.laps_remaining,
                'track_status': sample.track_status,
                'air_temp': sample.air_temp,
                'rainfall': sample.rainfall,
                'driver_win_rate': sample.driver_win_rate,
                'driver_podium_rate': sample.driver_podium_rate,
                'team_rating': sample.team_rating,
                'circuit_overtake_rate': sample.circuit_overtake_rate,
                'circuit_sc_rate': sample.circuit_sc_rate,
                'qualifying_position': sample.qualifying_position,
                'final_position': sample.final_position,
            })
            
        return pd.DataFrame(data)
    
    def extract_all_races(self, year: int) -> List[TrainingSample]:
        """
        提取指定年份所有比賽的數據
        
        Args:
            year: 年份
            
        Returns:
            所有比賽的訓練樣本列表
        """
        year_path = self.base_path / str(year)
        if not year_path.exists():
            logger.warning(f"Year folder not found: {year_path}")
            return []
            
        all_samples = []
        race_folders = [f for f in year_path.iterdir() if f.is_dir() and 'Race' in f.name]
        
        logger.info(f"Found {len(race_folders)} races in {year}")
        
        for race_folder in sorted(race_folders):
            race_name = race_folder.name.replace('_Race', '')
            try:
                samples = self.extract_race_data(year, race_name)
                all_samples.extend(samples)
            except Exception as e:
                logger.error(f"Failed to extract {race_name}: {e}")
                continue
                
        logger.info(f"Total samples from {year}: {len(all_samples)}")
        return all_samples


def main():
    """測試數據提取器"""
    extractor = LiveWinProbabilityDataExtractor(base_path="json/LiveF1")
    
    # 測試提取 2025 日本站數據
    samples = extractor.extract_race_data(2025, "Japanese")
    
    if samples:
        print(f"\nTotal samples: {len(samples)}")
        print(f"\nFirst 5 samples:")
        for sample in samples[:5]:
            print(f"  Lap {sample.current_lap}: {sample.driver_code} P{sample.position} -> Final P{sample.final_position}")
            
        # 轉換為 DataFrame
        try:
            df = extractor.to_dataframe(samples)
            print(f"\nDataFrame shape: {df.shape}")
            print(f"\nDataFrame columns: {list(df.columns)}")
            print(f"\nDataFrame head:\n{df.head()}")
        except ImportError:
            print("pandas not available for DataFrame conversion")


if __name__ == "__main__":
    main()
