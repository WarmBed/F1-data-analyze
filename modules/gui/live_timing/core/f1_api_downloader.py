"""
F1 Official API Downloader
===========================

從 F1 官方 livetiming API 下載歷史數據並轉換為 PKL 快取。

數據來源：
- https://livetiming.formula1.com/static

數據流程：
1. 從官方 API 下載 jsonStream 檔案
2. 解析並處理數據
3. 直接儲存為 PKL 快取

Author: F1T Team
Date: 2025-12-04
"""

import os
import sys
import json
import zlib
import base64
import pickle
import hashlib
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime


class F1APIDownloader:
    """
    F1 Official API Downloader
    
    從官方 API 下載歷史數據並直接轉換為 PKL 快取，
    跳過中間 JSON 檔案，減少磁碟 I/O。
    """
    
    BASE_URL = "https://livetiming.formula1.com/static"
    
    # 核心數據流（必須下載）
    CORE_STREAMS = [
        ("Position.z.jsonStream", True),           # 車手位置 (壓縮)
        ("TimingData.jsonStream", False),          # 計時數據
        ("CarData.z.jsonStream", True),            # 車輛遙測 (壓縮)
        ("TimingAppData.jsonStream", False),       # 輪胎策略
        ("WeatherData.jsonStream", False),         # 天氣數據
        ("RaceControlMessages.jsonStream", False), # 比賽控制訊息
        ("TrackStatus.jsonStream", False),         # 賽道狀態
        ("LapCount.jsonStream", False),            # 圈數進度
        ("DriverList.jsonStream", False),          # 車手列表
    ]
    
    # 可選數據流
    OPTIONAL_STREAMS = [
        ("PitLaneTimeCollection.jsonStream", False),
        ("SessionInfo.jsonStream", False),
        ("SessionData.jsonStream", False),
        ("LapSeries.jsonStream", False),
        ("TopThree.jsonStream", False),
        ("TimingStats.jsonStream", False),
        ("ExtrapolatedClock.jsonStream", False),
        ("TeamRadio.jsonStream", False),
        ("TyreStintSeries.jsonStream", False),
    ]
    
    # PKL 快取版本
    CACHE_VERSION = "2.0"  # 區別於舊的 JSON 快取版本
    
    def __init__(self, cache_dir: str = None):
        """
        初始化下載器
        
        Args:
            cache_dir: PKL 快取目錄
                - EXE 模式：EXE 同目錄的 live_timing_cache/
                - 開發模式：data/live_timing_cache/
        """
        if cache_dir is None:
            # 檢查是否為 EXE 模式
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # EXE 模式：使用 EXE 所在目錄
                exe_dir = Path(sys.executable).parent
                cache_dir = exe_dir / "live_timing_cache"
            else:
                # 開發模式：使用專案目錄
                project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
                cache_dir = project_root / "data" / "live_timing_cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 請求設定
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 60
    
    # ===========================================
    # 公開方法
    # ===========================================
    
    def get_cache_path(self, year: int, race: str, session: str = "Race") -> Path:
        """
        獲取 PKL 快取路徑
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型
            
        Returns:
            PKL 快取檔案路徑
        """
        # 標準化名稱
        race_normalized = self._normalize_race_name(race)
        session_normalized = self._normalize_session_name(session)
        
        return self.cache_dir / str(year) / f"{race_normalized}_{session_normalized}.pkl"
    
    def is_cache_valid(self, year: int, race: str, session: str = "Race") -> bool:
        """
        檢查 PKL 快取是否存在且有效
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型
            
        Returns:
            快取是否有效
        """
        cache_path = self.get_cache_path(year, race, session)
        
        if not cache_path.exists():
            return False
        
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            # 檢查版本
            if data.get('version') != self.CACHE_VERSION:
                print(f"[F1API] 快取版本不匹配: {data.get('version')}")
                return False
            
            # 檢查快照數量
            if len(data.get('snapshots', [])) == 0:
                print("[F1API] 快取中無快照數據")
                return False
            
            return True
            
        except Exception as e:
            print(f"[F1API] 驗證快取失敗: {e}")
            return False
    
    def load_cache(self, year: int, race: str, session: str = "Race") -> Optional[Dict[str, Any]]:
        """
        載入 PKL 快取
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型
            
        Returns:
            快取數據字典，或 None（如果載入失敗）
        """
        cache_path = self.get_cache_path(year, race, session)
        
        if not cache_path.exists():
            return None
        
        try:
            start_time = time.time()
            
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            load_time = time.time() - start_time
            snapshot_count = len(data.get('snapshots', []))
            
            print(f"[F1API] PKL 快取載入完成: {snapshot_count} 個快照, {load_time:.2f} 秒")
            
            return data
            
        except Exception as e:
            print(f"[F1API] 載入快取失敗: {e}")
            return None
    
    def download_and_cache(
        self, 
        year: int, 
        race: str, 
        session: str = "Race",
        force: bool = False,
        progress_callback: Callable[[int, str], None] = None
    ) -> Optional[Dict[str, Any]]:
        """
        從官方 API 下載數據並儲存為 PKL 快取
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型
            force: 是否強制重新下載
            progress_callback: 進度回調 (percent, message)
            
        Returns:
            處理後的數據字典，或 None（如果失敗）
        """
        def _report(percent, msg):
            if progress_callback:
                progress_callback(percent, msg)
        
        # 檢查快取
        if not force and self.is_cache_valid(year, race, session):
            _report(5, "Loading from cache...")
            return self.load_cache(year, race, session)
        
        _report(5, "Finding session path...")
        
        # 獲取會話路徑
        session_path = self._find_session_path(year, race, session)
        if not session_path:
            print(f"[F1API] 找不到賽事路徑: {year} {race} {session}")
            return None
        
        print(f"[F1API] 會話路徑: {session_path}")
        
        _report(10, "Downloading data streams...")
        
        # 下載所有數據流
        raw_data = self._download_all_streams(session_path, progress_callback)
        
        if not raw_data.get('position') or not raw_data.get('timing'):
            print("[F1API] 核心數據下載失敗")
            return None
        
        _report(60, "Processing data...")
        
        # 處理並對齊數據
        processed_data = self._process_raw_data(raw_data, year, race, session, progress_callback)
        
        if not processed_data:
            print("[F1API] 數據處理失敗")
            return None
        
        _report(90, "Saving cache...")
        
        # 儲存 PKL 快取
        self._save_cache(processed_data, year, race, session)
        
        _report(100, "Done")
        
        return processed_data
    
    # ===========================================
    # 索引與路徑解析
    # ===========================================
    
    def get_year_index(self, year: int) -> Optional[Dict]:
        """獲取年度賽事索引"""
        url = f"{self.BASE_URL}/{year}/Index.json"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                content = resp.content.decode('utf-8-sig')
                return json.loads(content)
            else:
                print(f"[F1API] 無法取得 {year} 年索引: HTTP {resp.status_code}")
                return None
        except Exception as e:
            print(f"[F1API] 取得 {year} 年索引失敗: {e}")
            return None
    
    def list_meetings(self, year: int) -> List[Dict]:
        """列出指定年份的所有賽事"""
        index = self.get_year_index(year)
        if not index:
            return []
        return index.get("Meetings", [])
    
    def _find_session_path(self, year: int, race: str, session: str) -> Optional[str]:
        """
        查找會話的 API 路徑
        
        Args:
            year: 年份
            race: 賽事名稱（例如 "Japan", "Japanese Grand Prix"）
            session: 會話類型（R, Q, FP1, Race, Qualifying 等）
            
        Returns:
            會話路徑（例如 "2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/"）
        """
        meetings = self.list_meetings(year)
        if not meetings:
            return None
        
        # 標準化搜索關鍵字
        race_lower = race.lower().replace("_", " ")
        
        # 查找匹配的賽事
        target_meeting = None
        for meeting in meetings:
            name = meeting.get("Name", "").lower()
            key = str(meeting.get("Key", "")).lower()
            
            if race_lower in name or race_lower in key:
                target_meeting = meeting
                break
            
            # 嘗試形容詞匹配（Japan -> Japanese）
            adjective = self._to_adjective(race)
            if adjective and adjective.lower() in name:
                target_meeting = meeting
                break
        
        if not target_meeting:
            print(f"[F1API] 找不到賽事: {race}")
            return None
        
        # 查找匹配的會話
        available_sessions = target_meeting.get("Sessions", [])
        session_upper = session.upper()
        
        # 標準化會話名稱（支援多種格式）
        # 同時支援 "Practice_1" 和 "Practice 1" 格式
        session_mapping = {
            "RACE": "R",
            "QUALIFYING": "Q",
            "PRACTICE_1": "FP1",
            "PRACTICE_2": "FP2",
            "PRACTICE_3": "FP3",
            "PRACTICE 1": "FP1",  # 支援空格格式
            "PRACTICE 2": "FP2",
            "PRACTICE 3": "FP3",
            "SPRINT": "S",
            "SPRINT_QUALIFYING": "SQ",
            "SPRINT QUALIFYING": "SQ",  # 支援空格格式
            "SPRINT_SHOOTOUT": "SS",
            "SPRINT SHOOTOUT": "SS",  # 支援空格格式
        }
        
        # 如果是長名稱，轉換為短名稱
        if session_upper in session_mapping:
            session_upper = session_mapping[session_upper]
        
        for sess in available_sessions:
            sess_name = sess.get("Name", "").upper()
            sess_path = sess.get("Path")
            
            if not sess_path:
                continue
            
            # 匹配邏輯
            if session_upper == "R" and "RACE" in sess_name and "SPRINT" not in sess_name:
                return sess_path
            elif session_upper == "Q" and "QUALIFYING" in sess_name and "SPRINT" not in sess_name:
                return sess_path
            elif session_upper in ["FP1", "FP2", "FP3"]:
                if session_upper.replace("FP", "PRACTICE ") in sess_name or session_upper in sess_name:
                    return sess_path
            elif session_upper == "S" and "SPRINT" in sess_name and "QUALIFYING" not in sess_name and "SHOOTOUT" not in sess_name:
                return sess_path
            elif session_upper == "SQ" and "SPRINT" in sess_name and "QUALIFYING" in sess_name:
                return sess_path
        
        # ===== 新增：Index.json 中 Path 為 None 時，嘗試猜測路徑 =====
        # 這通常發生在賽事剛結束、Index.json 尚未更新的情況
        print(f"[F1API] Index.json 中找不到 {session}，嘗試猜測路徑...")
        guessed_path = self._guess_session_path(target_meeting, session_upper, year)
        if guessed_path:
            return guessed_path
        
        print(f"[F1API] 找不到會話: {session}")
        return None
    
    def _guess_session_path(self, meeting: Dict, session_code: str, year: int) -> Optional[str]:
        """
        當 Index.json 中 Path 為 None 時，嘗試猜測並驗證路徑
        
        Args:
            meeting: 賽事資訊字典
            session_code: 會話代碼 (FP1, FP2, Q, R 等)
            year: 年份
            
        Returns:
            驗證成功的路徑，或 None
        """
        # 從已有的 session 中找到一個有效路徑作為參考
        available_sessions = meeting.get("Sessions", [])
        reference_path = None
        
        for sess in available_sessions:
            path = sess.get("Path")
            if path:
                reference_path = path
                break
        
        if not reference_path:
            print("[F1API] 無參考路徑可用於猜測")
            return None
        
        # 解析參考路徑以獲取賽事目錄
        # 例如: "2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-05_Practice_1/"
        parts = reference_path.split("/")
        if len(parts) < 3:
            return None
        
        meeting_dir = parts[1]  # "2025-12-07_Abu_Dhabi_Grand_Prix"
        session_date_part = parts[2].split("_")[0]  # "2025-12-05"
        
        # 會話名稱映射
        session_name_map = {
            "FP1": "Practice_1",
            "FP2": "Practice_2", 
            "FP3": "Practice_3",
            "Q": "Qualifying",
            "R": "Race",
            "S": "Sprint",
            "SQ": "Sprint_Qualifying",
            "SS": "Sprint_Shootout",
        }
        
        session_name = session_name_map.get(session_code.upper())
        if not session_name:
            return None
        
        # 構建猜測路徑
        guessed_path = f"{year}/{meeting_dir}/{session_date_part}_{session_name}/"
        
        # 驗證路徑是否可訪問
        test_url = f"{self.BASE_URL}/{guessed_path}DriverList.jsonStream"
        try:
            resp = self.session.head(test_url, timeout=10)
            if resp.status_code == 200:
                print(f"[F1API] 猜測路徑成功: {guessed_path}")
                return guessed_path
            else:
                print(f"[F1API] 猜測路徑 {guessed_path} 不可訪問 (HTTP {resp.status_code})")
        except Exception as e:
            print(f"[F1API] 驗證猜測路徑失敗: {e}")
        
        return None
    
    # ===========================================
    # 數據下載
    # ===========================================
    
    def _download_all_streams(
        self, 
        session_path: str,
        progress_callback: Callable[[int, str], None] = None
    ) -> Dict[str, List[Dict]]:
        """
        下載所有數據流
        
        Args:
            session_path: 會話路徑
            progress_callback: 進度回調
            
        Returns:
            原始數據字典
        """
        def _report(percent, msg):
            if progress_callback:
                progress_callback(percent, msg)
        
        raw_data = {}
        stream_mapping = {
            "Position.z.jsonStream": "position",
            "TimingData.jsonStream": "timing",
            "CarData.z.jsonStream": "cardata",
            "TimingAppData.jsonStream": "timing_app",
            "WeatherData.jsonStream": "weather",
            "RaceControlMessages.jsonStream": "race_control",
            "TrackStatus.jsonStream": "track_status",
            "LapCount.jsonStream": "lap_count",
            "DriverList.jsonStream": "driver_list",
        }
        
        total_streams = len(self.CORE_STREAMS)
        
        for idx, (stream_name, compressed) in enumerate(self.CORE_STREAMS):
            percent = 10 + int((idx / total_streams) * 45)
            _report(percent, f"Downloading {stream_name}...")
            
            url = f"{self.BASE_URL}/{session_path}{stream_name}"
            records = self._download_stream(url, compressed)
            
            key = stream_mapping.get(stream_name)
            if key:
                raw_data[key] = records
                if records:
                    print(f"[F1API] {stream_name}: {len(records)} records")
            
            # 短暫延遲避免請求過快
            time.sleep(0.1)
        
        return raw_data
    
    def _download_stream(self, url: str, compressed: bool) -> List[Dict]:
        """下載並解析單個數據流"""
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                return []
            
            content = resp.content.decode('utf-8-sig')
            return self._parse_stream(content, compressed)
            
        except Exception as e:
            print(f"[F1API] 下載失敗 {url}: {e}")
            return []
    
    def _parse_stream(self, stream_text: str, compressed: bool) -> List[Dict]:
        """解析 jsonStream 格式"""
        records = []
        lines = stream_text.strip().split('\n')
        
        for line in lines:
            if len(line) <= 12:
                continue
            
            timestamp = line[:12]
            payload_text = line[12:]
            
            try:
                decoded = self._decode_payload(payload_text, compressed)
                records.append({
                    "timestamp": timestamp,
                    "data": decoded
                })
            except Exception:
                continue
        
        return records
    
    def _decode_payload(self, payload_text: str, compressed: bool) -> Any:
        """解碼 payload"""
        if compressed:
            try:
                decoded = base64.b64decode(payload_text)
                decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
                return json.loads(decompressed.decode('utf-8'))
            except Exception:
                return json.loads(payload_text)
        else:
            return json.loads(payload_text)
    
    # ===========================================
    # 數據處理
    # ===========================================
    
    def _process_raw_data(
        self,
        raw_data: Dict[str, List[Dict]],
        year: int,
        race: str,
        session: str,
        progress_callback: Callable[[int, str], None] = None
    ) -> Optional[Dict[str, Any]]:
        """
        處理原始數據並建立快照
        
        這裡我們使用一個簡化版的處理器，
        直接從原始數據建立對齊的快照。
        """
        def _report(percent, msg):
            if progress_callback:
                progress_callback(percent, msg)
        
        try:
            from .position_processor import LivePositionDataProcessor
            
            # 創建一個模擬的數據源
            class MockDataSource:
                def __init__(self, raw_data):
                    self._position_data = raw_data.get('position', [])
                    self._timing_data = raw_data.get('timing', [])
                    self._cardata = raw_data.get('cardata', [])
                    self._timing_app_data = raw_data.get('timing_app', [])
                    self._weather_data = raw_data.get('weather', [])
                    self._race_control_messages = raw_data.get('race_control', [])
                    self._track_status = raw_data.get('track_status', [])
                    self._lap_count = raw_data.get('lap_count', [])
                    self._driver_list_data = raw_data.get('driver_list', [])
                
                def get_position_data(self): return self._position_data
                def get_timing_data(self): return self._timing_data
                def get_cardata(self): return self._cardata
                def get_timing_app_data(self): return self._timing_app_data
                def get_weather_data(self): return self._weather_data
                def get_race_control_messages(self): return self._race_control_messages
                def get_track_status(self): return self._track_status
                def get_lap_count(self): return self._lap_count
                
                def load_driver_list(self):
                    driver_map = {}
                    for record in self._driver_list_data:
                        data = record.get('data', {})
                        if isinstance(data, dict):
                            for driver_num, driver_info in data.items():
                                if isinstance(driver_info, dict) and driver_info:
                                    if 'Tla' in driver_info or 'TeamColour' in driver_info:
                                        driver_map[driver_num] = {
                                            'tla': driver_info.get('Tla', driver_num),
                                            'name': driver_info.get('BroadcastName', driver_num),
                                            'full_name': driver_info.get('FullName', ''),
                                            'team': driver_info.get('TeamName', ''),
                                            'team_color': driver_info.get('TeamColour', 'CCCCCC')
                                        }
                    return driver_map
            
            mock_source = MockDataSource(raw_data)
            
            _report(65, "Processing position data...")
            
            # 使用現有的處理器
            processor = LivePositionDataProcessor(mock_source)
            
            def processor_progress(percent, msg):
                mapped = 65 + int(percent * 0.2)
                _report(mapped, msg)
            
            processor.process_and_align_data(progress_callback=processor_progress)
            
            _report(88, "Building snapshots...")
            
            snapshots = processor.get_aligned_snapshots()
            
            if not snapshots:
                print("[F1API] 無可用快照")
                return None
            
            print(f"[F1API] 處理完成: {len(snapshots)} 個快照")
            
            # 計算總圈數
            total_laps = 0
            if snapshots:
                last_snapshot = snapshots[-1]
                for driver_data in last_snapshot.get('drivers', {}).values():
                    lap = driver_data.get('lap', 0)
                    if lap and lap > total_laps:
                        total_laps = lap
            
            # 建立結果
            result = {
                'version': self.CACHE_VERSION,
                'created_at': datetime.now().isoformat(),
                'source': 'F1_OFFICIAL_API',
                'snapshots': snapshots,
                'race_info': {
                    'year': year,
                    'race': race,
                    'session': session,
                    'total_snapshots': len(snapshots),
                    'total_laps': total_laps,
                    'duration_seconds': (
                        snapshots[-1]['race_time_seconds'] - 
                        snapshots[0]['race_time_seconds']
                    ) if snapshots else 0,
                },
                'driver_info': processor.get_driver_info(),
                'pit_events': processor.get_pit_events(),
                'driver_stints': processor.get_driver_stints(),
                'tyre_state_index': processor._tyre_state_index,
                'tyre_timestamps': processor._tyre_timestamps,
                'race_control_messages': raw_data.get('race_control', []),
                'track_status': raw_data.get('track_status', []),
            }
            
            return result
            
        except Exception as e:
            print(f"[F1API] 處理數據失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_cache(self, data: Dict[str, Any], year: int, race: str, session: str) -> bool:
        """儲存 PKL 快取"""
        try:
            cache_path = self.get_cache_path(year, race, session)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            start_time = time.time()
            
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            save_time = time.time() - start_time
            cache_size = cache_path.stat().st_size / (1024 * 1024)
            
            print(f"[F1API] PKL 快取已儲存: {cache_path}")
            print(f"[F1API] 檔案大小: {cache_size:.2f} MB, 耗時: {save_time:.2f} 秒")
            
            return True
            
        except Exception as e:
            print(f"[F1API] 儲存快取失敗: {e}")
            return False
    
    # ===========================================
    # 輔助方法
    # ===========================================
    
    def _normalize_race_name(self, race: str) -> str:
        """標準化賽事名稱"""
        # 移除常見後綴
        race = race.replace(" Grand Prix", "").replace("_Grand_Prix", "")
        race = race.replace("_Race", "").replace(" Race", "")
        
        # 轉換為形容詞形式
        adjective = self._to_adjective(race)
        if adjective:
            return adjective
        
        # 預設處理
        return race.replace(" ", "_")
    
    def _normalize_session_name(self, session: str) -> str:
        """標準化會話名稱"""
        mapping = {
            "R": "Race",
            "Q": "Qualifying",
            "FP1": "Practice_1",
            "FP2": "Practice_2",
            "FP3": "Practice_3",
            "S": "Sprint",
            "SQ": "Sprint_Qualifying",
            "SS": "Sprint_Shootout",
        }
        return mapping.get(session.upper(), session)
    
    def _to_adjective(self, country: str) -> Optional[str]:
        """將國家名轉換為形容詞形式"""
        adjective_map = {
            "Japan": "Japanese",
            "China": "Chinese",
            "Australia": "Australian",
            "Austria": "Austrian",
            "Belgium": "Belgian",
            "Great Britain": "British",
            "Canada": "Canadian",
            "Netherlands": "Dutch",
            "Hungary": "Hungarian",
            "Italy": "Italian",
            "Spain": "Spanish",
            "Monaco": "Monaco",
            "Singapore": "Singapore",
            "Azerbaijan": "Azerbaijan",
            "Bahrain": "Bahrain",
            "Saudi Arabia": "Saudi_Arabian",
            "Qatar": "Qatar",
            "Abu Dhabi": "Abu_Dhabi",
            "United States": "United_States",
            "Las Vegas": "Las_Vegas",
            "Mexico": "Mexico_City",
            "Brazil": "Sao_Paulo",
            "Miami": "Miami",
            "Emilia Romagna": "Emilia_Romagna",
        }
        return adjective_map.get(country)


# 便捷函數
def download_race_data(
    year: int, 
    race: str, 
    session: str = "Race",
    force: bool = False,
    progress_callback: Callable[[int, str], None] = None
) -> Optional[Dict[str, Any]]:
    """
    便捷函數：下載賽事數據
    
    Args:
        year: 年份
        race: 賽事名稱
        session: 會話類型
        force: 是否強制重新下載
        progress_callback: 進度回調
        
    Returns:
        處理後的數據字典
    """
    downloader = F1APIDownloader()
    return downloader.download_and_cache(year, race, session, force, progress_callback)


def is_race_cached(year: int, race: str, session: str = "Race") -> bool:
    """
    便捷函數：檢查賽事是否已快取
    
    Args:
        year: 年份
        race: 賽事名稱
        session: 會話類型
        
    Returns:
        是否已快取
    """
    downloader = F1APIDownloader()
    return downloader.is_cache_valid(year, race, session)


def load_race_cache(year: int, race: str, session: str = "Race") -> Optional[Dict[str, Any]]:
    """
    便捷函數：載入賽事快取
    
    Args:
        year: 年份
        race: 賽事名稱
        session: 會話類型
        
    Returns:
        快取數據
    """
    downloader = F1APIDownloader()
    return downloader.load_cache(year, race, session)
