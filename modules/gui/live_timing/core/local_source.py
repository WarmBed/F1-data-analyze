"""
Live Timing 本地數據源
======================

從本地 JSON 檔案讀取 F1 Live Timing 歷史數據。

數據來源：
- json/LiveF1/{year}/{race}_{session}/ 目錄下的 JSON 檔案
- 包含 Position, TimingData, CarData, TimingAppData 等

Author: F1T Team
Date: 2025-12-03
"""

import os
import sys
import json
import base64
import zlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional


# 賽事名稱映射（SeasonCalendar → LiveF1 資料夾格式）
# SeasonCalendarProvider 輸出: "Japan", "Australia" 等
# LiveF1 資料夾格式: "Japanese_Race", "Australian_Race" 等
RACE_NAME_TO_FOLDER = {
    # 亞洲賽事
    "Japan": "Japanese_Race",
    "China": "Chinese_Race",
    "Singapore": "Singapore_Race",
    "Azerbaijan": "Azerbaijan_Race",
    "Bahrain": "Bahrain_Race",
    "Saudi Arabia": "Saudi_Arabian_Race",
    "Qatar": "Qatar_Race",
    "Abu Dhabi": "Abu_Dhabi_Race",
    # 歐洲賽事
    "Great Britain": "British_Race",
    "Belgium": "Belgian_Race",
    "Netherlands": "Dutch_Race",
    "Italy": "Italian_Race",
    "Spain": "Spanish_Race",
    "Hungary": "Hungarian_Race",
    "Austria": "Austrian_Race",
    "Monaco": "Monaco_Race",
    "Emilia Romagna": "Emilia_Romagna_Race",
    # 美洲賽事
    "United States": "United_States_Race",
    "Las Vegas": "Las_Vegas_Race",
    "Mexico": "Mexico_City_Race",
    "Brazil": "São_Paulo_Race",
    "Miami": "Miami_Race",
    "Canada": "Canadian_Race",
    # 大洋洲賽事
    "Australia": "Australian_Race",
}


class LocalLiveF1DataSource:
    """
    本地 Live F1 數據源 - 讀取已下載的 JSON 檔案
    
    JSON 檔案格式:
    {
        "metadata": {...},
        "records": [{"timestamp": "...", "data": {...}}, ...]
    }
    """
    
    def __init__(self, year: int, race: str, base_dir: str = None):
        """
        初始化本地數據源
        
        Args:
            year: 年份 (例如 2025)
            race: 賽事名稱 (支援 "Japan" 或 "Japanese_Race" 格式)
            base_dir: 本地 LiveF1 JSON 根目錄
        """
        self.year = str(year)
        
        # 標準化賽事名稱（支援兩種格式）
        self.race = self._normalize_race_name(race)
        
        if base_dir is None:
            # 檢查是否為 EXE 模式
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # EXE 模式：使用 EXE 所在目錄
                exe_dir = Path(sys.executable).parent
                base_dir = os.path.join(exe_dir, "json", "LiveF1")
            else:
                # 開發模式：從 modules/gui/live_timing/core 回到專案根目錄
                project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
                base_dir = os.path.join(project_root, "json", "LiveF1")
        
        self.data_dir = os.path.join(base_dir, self.year, self.race)
        
        # 數據存儲
        self._position_data: List[Dict[str, Any]] = []
        self._timing_data: List[Dict[str, Any]] = []
        self._cardata: List[Dict[str, Any]] = []
        self._timing_app_data: List[Dict[str, Any]] = []
        self._weather_data: List[Dict[str, Any]] = []
        self._race_control_messages: List[Dict[str, Any]] = []
        self._track_status: List[Dict[str, Any]] = []
        self._lap_count: List[Dict[str, Any]] = []
        self._pit_lane_times: List[Dict[str, Any]] = []
        self._driver_list_data: List[Dict[str, Any]] = []
        
        print(f"[LOCAL_DATASOURCE] 初始化: {self.year} {self.race}")
        print(f"[LOCAL_DATASOURCE] 資料目錄: {self.data_dir}")
    
    def _normalize_race_name(self, race: str) -> str:
        """
        標準化賽事名稱
        
        支援輸入格式：
        - "Japan" (來自 SeasonCalendarProvider)
        - "Japanese_Race" (已是 LiveF1 格式)
        
        Returns:
            LiveF1 資料夾格式的賽事名稱 (例如 "Japanese_Race")
        """
        # 如果已經是 LiveF1 格式（包含 "_Race" 後綴），直接返回
        if "_Race" in race:
            return race
        
        # 使用映射表轉換
        if race in RACE_NAME_TO_FOLDER:
            normalized = RACE_NAME_TO_FOLDER[race]
            print(f"[LOCAL_DATASOURCE] 賽事名稱轉換: {race} -> {normalized}")
            return normalized
        
        # 嘗試自動轉換（加上形容詞形式 + _Race）
        # 例如: Japan -> Japanese_Race
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
        }
        
        if race in adjective_map:
            normalized = f"{adjective_map[race]}_Race"
            print(f"[LOCAL_DATASOURCE] 賽事名稱轉換 (形容詞): {race} -> {normalized}")
            return normalized
        
        # 最後嘗試：直接添加 _Race 後綴
        normalized = race.replace(" ", "_") + "_Race"
        print(f"[LOCAL_DATASOURCE] 賽事名稱轉換 (預設): {race} -> {normalized}")
        return normalized
    
    def load_all_data(self, progress_callback=None) -> bool:
        """
        載入所有本地 JSON 數據
        
        Args:
            progress_callback: 可選的進度回調函數 (current, total, filename) -> None
        
        Returns:
            是否載入成功
        """
        print(f"[LOCAL_DATASOURCE] 載入本地 JSON 數據...")
        
        if not os.path.exists(self.data_dir):
            print(f"[LOCAL_DATASOURCE] 資料目錄不存在: {self.data_dir}")
            return False
        
        # 定義要載入的檔案列表
        files_to_load = [
            ("Position.json", "_position_data"),
            ("TimingData.json", "_timing_data"),
            ("CarData.json", "_cardata"),
            ("TimingAppData.json", "_timing_app_data"),
            ("WeatherData.json", "_weather_data"),
            ("RaceControlMessages.json", "_race_control_messages"),
            ("TrackStatus.json", "_track_status"),
            ("LapCount.json", "_lap_count"),
            ("PitLaneTimeCollection.json", "_pit_lane_times"),
            ("DriverList.json", "_driver_list_data"),
        ]
        
        total_files = len(files_to_load)
        
        # 載入各種數據流
        for idx, (filename, attr_name) in enumerate(files_to_load):
            if progress_callback:
                progress_callback(idx, total_files, filename)
            
            data = self._load_json_file(filename)
            setattr(self, attr_name, data)
        
        # 完成
        if progress_callback:
            progress_callback(total_files, total_files, "Done")
        
        # 輸出統計
        if self._position_data:
            print(f"[LOCAL_DATASOURCE] Position 記錄: {len(self._position_data)}")
        else:
            print("[LOCAL_DATASOURCE] Position 數據載入失敗")
        
        if self._timing_data:
            print(f"[LOCAL_DATASOURCE] Timing 記錄: {len(self._timing_data)}")
        
        if self._cardata:
            print(f"[LOCAL_DATASOURCE] CarData 記錄: {len(self._cardata)}")
        
        if self._timing_app_data:
            print(f"[LOCAL_DATASOURCE] TimingAppData 記錄: {len(self._timing_app_data)}")
        
        success = all([self._position_data, self._timing_data, self._cardata])
        if success:
            print("[LOCAL_DATASOURCE] 數據載入完成")
        
        return success
    
    def _load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """載入單個 JSON 檔案"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 下載器產生的格式: {"metadata": {...}, "records": [...]}
            if isinstance(data, dict) and 'records' in data:
                return data['records']
            
            # 舊格式: 直接是列表
            if isinstance(data, list):
                return data
            
            return []
            
        except Exception as e:
            print(f"[LOCAL_DATASOURCE] 載入 {filename} 失敗: {e}")
            return []
    
    def load_driver_list(self) -> Dict[str, Dict[str, str]]:
        """載入車手列表"""
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
        
        print(f"[LOCAL_DATASOURCE] 載入 {len(driver_map)} 位車手資訊")
        return driver_map
    
    # Getter 方法
    def get_position_data(self) -> List[Dict[str, Any]]:
        return self._position_data
    
    def get_timing_data(self) -> List[Dict[str, Any]]:
        return self._timing_data
    
    def get_cardata(self) -> List[Dict[str, Any]]:
        return self._cardata
    
    def get_timing_app_data(self) -> List[Dict[str, Any]]:
        return self._timing_app_data
    
    def get_weather_data(self) -> List[Dict[str, Any]]:
        return self._weather_data
    
    def get_race_control_messages(self) -> List[Dict[str, Any]]:
        return self._race_control_messages
    
    def get_track_status(self) -> List[Dict[str, Any]]:
        return self._track_status
    
    def get_lap_count(self) -> List[Dict[str, Any]]:
        return self._lap_count
    
    def get_pit_lane_times(self) -> List[Dict[str, Any]]:
        return self._pit_lane_times


class LiveF1DataSource:
    """
    Live F1 數據源 - 從網路下載 jsonStream 或讀取本地快取
    
    數據來源：
    - 即時模式：F1 Live Timing 官方 API
    - 快取模式：本地 jsonStream 檔案
    """

    def __init__(
        self,
        year: int,
        meeting: str,
        session: str,
        base_url: str = "https://livetiming.formula1.com/static",
        local_cache_dir: Optional[str] = None,
    ):
        self.year = str(year)
        self.meeting = meeting
        self.session = session
        self.base_url = base_url.rstrip('/')
        
        if local_cache_dir is None:
            # 檢查是否為 EXE 模式
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # EXE 模式：使用 EXE 所在目錄
                exe_dir = Path(sys.executable).parent
                local_cache_dir = os.path.join(exe_dir, "live_timing_cache")
            else:
                # 開發模式
                project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
                local_cache_dir = os.path.join(project_root, "data", "live_timing")
        self.local_cache_dir = local_cache_dir

        self._position_data: List[Dict[str, Any]] = []
        self._timing_data: List[Dict[str, Any]] = []
        self._cardata: List[Dict[str, Any]] = []
        self._timing_app_data: List[Dict[str, Any]] = []
        self._weather_data: List[Dict[str, Any]] = []
        self._race_control_messages: List[Dict[str, Any]] = []
        self._track_status: List[Dict[str, Any]] = []
        self._lap_count: List[Dict[str, Any]] = []
        self._pit_lane_times: List[Dict[str, Any]] = []

    def load_all_data(self) -> bool:
        """載入所有數據流"""
        print("[DATASOURCE] 下載/載入 Live Timing 數據...")
        
        self._position_data = self._load_stream("Position.z.jsonStream", compressed=True)
        self._timing_data = self._load_stream("TimingData.jsonStream", compressed=False)
        self._cardata = self._load_stream("CarData.z.jsonStream", compressed=True)
        self._timing_app_data = self._load_stream("TimingAppData.jsonStream", compressed=False)
        self._weather_data = self._load_stream("WeatherData.jsonStream", compressed=False)
        self._race_control_messages = self._load_stream("RaceControlMessages.jsonStream", compressed=False)
        self._track_status = self._load_stream("TrackStatus.jsonStream", compressed=False)
        self._lap_count = self._load_stream("LapCount.jsonStream", compressed=False)
        self._pit_lane_times = self._load_stream("PitLaneTimeCollection.jsonStream", compressed=False)

        if self._position_data:
            print(f"[DATASOURCE] Position 記錄: {len(self._position_data)}")
        else:
            print("[DATASOURCE] Position 數據載入失敗")

        if self._timing_data:
            print(f"[DATASOURCE] Timing 記錄: {len(self._timing_data)}")

        if self._cardata:
            print(f"[DATASOURCE] CarData 記錄: {len(self._cardata)}")
        
        if self._timing_app_data:
            print(f"[DATASOURCE] TimingAppData 記錄: {len(self._timing_app_data)}")

        success = all([self._position_data, self._timing_data, self._cardata])
        if success:
            print("[DATASOURCE] 數據載入完成")
        return success
    
    def load_driver_list(self) -> Dict[str, Dict[str, str]]:
        """載入車手列表"""
        driver_list_data = self._load_stream("DriverList.jsonStream", compressed=False)
        
        driver_map = {}
        if driver_list_data:
            for record in driver_list_data:
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
            print(f"[DATASOURCE] 載入 {len(driver_map)} 位車手資訊")
        else:
            print("[DATASOURCE] DriverList 載入失敗")
        
        return driver_map

    # Getter 方法
    def get_position_data(self) -> List[Dict[str, Any]]:
        return self._position_data

    def get_timing_data(self) -> List[Dict[str, Any]]:
        return self._timing_data

    def get_cardata(self) -> List[Dict[str, Any]]:
        return self._cardata
    
    def get_timing_app_data(self) -> List[Dict[str, Any]]:
        return self._timing_app_data
    
    def get_weather_data(self) -> List[Dict[str, Any]]:
        return self._weather_data
    
    def get_race_control_messages(self) -> List[Dict[str, Any]]:
        return self._race_control_messages
    
    def get_track_status(self) -> List[Dict[str, Any]]:
        return self._track_status
    
    def get_lap_count(self) -> List[Dict[str, Any]]:
        return self._lap_count
    
    def get_pit_lane_times(self) -> List[Dict[str, Any]]:
        return self._pit_lane_times

    # 內部方法
    def _load_stream(self, file_name: str, compressed: bool) -> List[Dict[str, Any]]:
        """載入並解析 jsonStream 檔案"""
        stream_text = self._fetch_stream_text(file_name)
        if not stream_text:
            return []

        lines = [line for line in stream_text.splitlines() if line.strip()]
        records: List[Dict[str, Any]] = []

        for idx, line in enumerate(lines):
            if len(line) <= 12:
                continue

            timestamp = line[:12]
            payload_text = line[12:]

            try:
                decoded_payload = self._decode_payload(payload_text, compressed)
            except Exception as exc:
                print(f"[DATASOURCE] 解碼失敗 (line {idx}): {exc}")
                continue

            normalized = self._normalize_payload(decoded_payload)
            if normalized is None:
                continue

            if isinstance(normalized, list):
                for entry in normalized:
                    records.append({'timestamp': timestamp, 'data': entry})
            else:
                records.append({'timestamp': timestamp, 'data': normalized})

        return records

    def _fetch_stream_text(self, file_name: str) -> Optional[str]:
        """獲取 stream 文本（優先本地，回退線上）"""
        # 1) 優先讀取本地快取
        local_path = self._resolve_local_path(file_name)
        if local_path:
            try:
                with open(local_path, 'r', encoding='utf-8-sig') as file:
                    return file.read()
            except FileNotFoundError:
                pass
            except Exception as exc:
                print(f"[DATASOURCE] 讀取本地檔案失敗 {local_path}: {exc}")

        # 2) 回退至線上下載
        url = self._build_remote_url(file_name)
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.content.decode('utf-8-sig')
        except Exception as exc:
            print(f"[DATASOURCE] 無法下載 {file_name}: {exc}")
            return None

    def _resolve_local_path(self, file_name: str) -> Optional[str]:
        """解析本地檔案路徑"""
        if not self.local_cache_dir:
            return None

        candidate = os.path.join(
            self.local_cache_dir,
            self.year,
            self.meeting,
            self.session,
            file_name,
        )
        return candidate if os.path.exists(candidate) else None

    def _build_remote_url(self, file_name: str) -> str:
        """構建遠端 URL"""
        return f"{self.base_url}/{self.year}/{self.meeting}/{self.session}/{file_name}"

    @staticmethod
    def _decode_payload(payload: str, compressed: bool) -> Any:
        """解碼 payload"""
        if not payload:
            return None

        if compressed:
            decoded = base64.b64decode(payload)
            inflated = zlib.decompress(decoded, wbits=-15)
            return json.loads(inflated.decode('utf-8'))
        return json.loads(payload)

    def _normalize_payload(self, payload: Any) -> Any:
        """標準化 payload 格式"""
        if isinstance(payload, dict) and 'A' in payload and isinstance(payload['A'], list):
            normalized_entries: List[Any] = []
            for entry in payload['A']:
                decoded = self._decode_signalr_message(entry)
                if decoded is not None:
                    normalized_entries.append(decoded)
            return normalized_entries
        return payload

    @staticmethod
    def _decode_signalr_message(message: Any) -> Optional[Any]:
        """解碼 SignalR 訊息"""
        if isinstance(message, dict):
            return message

        if not isinstance(message, str):
            return None

        try:
            return json.loads(message)
        except json.JSONDecodeError:
            pass

        try:
            decoded = base64.b64decode(message)
            inflated = zlib.decompress(decoded, wbits=-15)
            return json.loads(inflated.decode('utf-8'))
        except Exception:
            return None
