"""
F1 實時車手位置追蹤系統 - Stage 1 Demo
Live Position Tracking System - Demonstration

目標：
1. 顯示每個時間點所有車手的位置/排名/速度/與前車差距
2. 時間軸控制器（播放/暫停/拖動）
3. 完全獨立運行，不整合到 F1T GUI

數據來源：本地 JSON 檔案 (json/LiveF1/{year}/{race}_{session}/)

作者：F1T Team
日期：2025-11-22
更新：2025-11-26 - 新增本地 JSON 讀取和賽事選擇功能
"""

import os
import sys
import json
import base64
import zlib
import re
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import timedelta

# 添加根目錄到 sys.path 以便 import CLI_modules
_root_dir = Path(__file__).resolve().parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QSlider, QLabel,
    QHeaderView, QAbstractItemView, QComboBox, QGroupBox, QSplitter,
    QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QPointF
from PyQt5.QtGui import QColor, QFont, QBrush, QPainter, QPen

# 勝率預測器
try:
    from CLI_modules.cli.prediction.live_win_probability.predictor import LiveWinProbabilityPredictor
    WIN_PROBABILITY_AVAILABLE = True
except ImportError as e:
    WIN_PROBABILITY_AVAILABLE = False
    print(f"[WARNING] Win probability predictor not available: {e}")
    print("[WARNING] Win probability predictor not available")


# ============================================================
# 賽事選擇器 - 掃描本地 LiveF1 JSON 檔案
# ============================================================

def scan_available_races(base_dir: str = None) -> Dict[str, List[str]]:
    """
    掃描本地 LiveF1 JSON 目錄，返回可用的年份和賽事
    
    Returns:
        {year: [race1, race2, ...]}
    """
    if base_dir is None:
        # 預設路徑: 專案根目錄/json/LiveF1/
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", "LiveF1")
    
    available = {}
    
    if not os.path.exists(base_dir):
        print(f"[SCAN] 本地 LiveF1 目錄不存在: {base_dir}")
        return available
    
    # 掃描年份資料夾
    for year_dir in sorted(os.listdir(base_dir)):
        year_path = os.path.join(base_dir, year_dir)
        if not os.path.isdir(year_path):
            continue
        
        # 檢查是否為有效年份
        try:
            year = int(year_dir)
        except ValueError:
            continue
        
        # 掃描賽事資料夾
        races = []
        for race_dir in sorted(os.listdir(year_path)):
            race_path = os.path.join(year_path, race_dir)
            if not os.path.isdir(race_path):
                continue
            
            # 檢查是否有 Position.json 檔案
            if os.path.exists(os.path.join(race_path, "Position.json")):
                races.append(race_dir)
        
        if races:
            available[str(year)] = races
    
    return available


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
            race: 賽事名稱 (例如 "Japanese_Race")
            base_dir: 本地 LiveF1 JSON 根目錄
        """
        self.year = str(year)
        self.race = race
        
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", "LiveF1")
        
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
    
    def load_all_data(self) -> bool:
        """載入所有本地 JSON 數據"""
        print(f"[LOCAL_DATASOURCE] 載入本地 JSON 數據...")
        
        if not os.path.exists(self.data_dir):
            print(f"[LOCAL_DATASOURCE] 資料目錄不存在: {self.data_dir}")
            return False
        
        # 載入各種數據流
        self._position_data = self._load_json_file("Position.json")
        self._timing_data = self._load_json_file("TimingData.json")
        self._cardata = self._load_json_file("CarData.json")
        self._timing_app_data = self._load_json_file("TimingAppData.json")
        self._weather_data = self._load_json_file("WeatherData.json")
        self._race_control_messages = self._load_json_file("RaceControlMessages.json")
        self._track_status = self._load_json_file("TrackStatus.json")
        self._lap_count = self._load_json_file("LapCount.json")
        self._pit_lane_times = self._load_json_file("PitLaneTimeCollection.json")
        self._driver_list_data = self._load_json_file("DriverList.json")
        
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
    
    # Getter 方法 (與 LiveF1DataSource 保持相同介面)
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
    """簡易資料來源層：讀取/下載 Live Timing jsonStream 檔案."""

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
        self.local_cache_dir = local_cache_dir or os.path.join(os.path.dirname(__file__), "data")

        self._position_data: List[Dict[str, Any]] = []
        self._timing_data: List[Dict[str, Any]] = []
        self._cardata: List[Dict[str, Any]] = []
        self._timing_app_data: List[Dict[str, Any]] = []  # 輪胎資訊
        
        # 新增資料流
        self._weather_data: List[Dict[str, Any]] = []  # 天氣資訊
        self._race_control_messages: List[Dict[str, Any]] = []  # 比賽控制訊息
        self._track_status: List[Dict[str, Any]] = []  # 賽道狀態
        self._lap_count: List[Dict[str, Any]] = []  # 圈數進度
        self._pit_lane_times: List[Dict[str, Any]] = []  # 維修站時間

    # ----------------------------
    # Public API
    # ----------------------------
    def load_all_data(self) -> bool:
        print("[DATASOURCE] 下載/載入 Live Timing 數據...")
        self._position_data = self._load_stream("Position.z.jsonStream", compressed=True)
        self._timing_data = self._load_stream("TimingData.jsonStream", compressed=False)
        self._cardata = self._load_stream("CarData.z.jsonStream", compressed=True)
        self._timing_app_data = self._load_stream("TimingAppData.jsonStream", compressed=False)
        
        # 載入新資料流
        self._weather_data = self._load_stream("WeatherData.jsonStream", compressed=False)
        self._race_control_messages = self._load_stream("RaceControlMessages.jsonStream", compressed=False)
        self._track_status = self._load_stream("TrackStatus.jsonStream", compressed=False)
        self._lap_count = self._load_stream("LapCount.jsonStream", compressed=False)
        self._pit_lane_times = self._load_stream("PitLaneTimeCollection.jsonStream", compressed=False)

        if self._position_data:
            print(f"[DATASOURCE] Position 記錄: {len(self._position_data)}")
        else:
            print("[DATASOURCE] ⚠️ Position 數據載入失敗")

        if self._timing_data:
            print(f"[DATASOURCE] Timing 記錄: {len(self._timing_data)}")
        else:
            print("[DATASOURCE] ⚠️ Timing 數據載入失敗")

        if self._cardata:
            print(f"[DATASOURCE] CarData 記錄: {len(self._cardata)}")
        else:
            print("[DATASOURCE] ⚠️ CarData 數據載入失敗")
        
        if self._timing_app_data:
            print(f"[DATASOURCE] TimingAppData 記錄: {len(self._timing_app_data)} (輪胎資訊)")
        else:
            print("[DATASOURCE] ⚠️ TimingAppData 數據載入失敗")

        success = all([self._position_data, self._timing_data, self._cardata])
        if success:
            print("[DATASOURCE] ✅ 數據載入完成")
        return success
    
    def load_driver_list(self) -> Dict[str, Dict[str, str]]:
        """載入車手列表，返回車號 -> 車手資訊的映射"""
        driver_list_data = self._load_stream("DriverList.jsonStream", compressed=False)
        
        driver_map = {}
        if driver_list_data:
            # DriverList 可能有多筆記錄，需要合併所有資訊
            for record in driver_list_data:
                data = record.get('data', {})
                if isinstance(data, dict):
                    # data 格式: {'1': {車手資訊}, '4': {車手資訊}, ...}
                    for driver_num, driver_info in data.items():
                        if isinstance(driver_info, dict) and driver_info:  # 確保不是空字典
                            # 只在有實際資料時才更新（避免被空記錄覆蓋）
                            if 'Tla' in driver_info or 'TeamColour' in driver_info:
                                driver_map[driver_num] = {
                                    'tla': driver_info.get('Tla', driver_num),  # 三字代碼 (VER, HAM, ...)
                                    'name': driver_info.get('BroadcastName', driver_num),  # 廣播名稱
                                    'full_name': driver_info.get('FullName', ''),
                                    'team': driver_info.get('TeamName', ''),
                                    'team_color': driver_info.get('TeamColour', 'CCCCCC')  # 車隊顏色 (hex)
                                }
            print(f"[DATASOURCE] ✅ 載入 {len(driver_map)} 位車手資訊")
        else:
            print("[DATASOURCE] ⚠️ DriverList 載入失敗")
        
        return driver_map

    def get_position_data(self) -> List[Dict[str, Any]]:
        return self._position_data

    def get_timing_data(self) -> List[Dict[str, Any]]:
        return self._timing_data

    def get_cardata(self) -> List[Dict[str, Any]]:
        return self._cardata
    
    def get_timing_app_data(self) -> List[Dict[str, Any]]:
        """獲取輪胎/策略資訊 (TimingAppData)"""
        return self._timing_app_data
    
    def get_weather_data(self) -> List[Dict[str, Any]]:
        """獲取天氣資訊"""
        return self._weather_data
    
    def get_race_control_messages(self) -> List[Dict[str, Any]]:
        """獲取比賽控制訊息"""
        return self._race_control_messages
    
    def get_track_status(self) -> List[Dict[str, Any]]:
        """獲取賽道狀態"""
        return self._track_status
    
    def get_lap_count(self) -> List[Dict[str, Any]]:
        """獲取圈數進度"""
        return self._lap_count
    
    def get_pit_lane_times(self) -> List[Dict[str, Any]]:
        """獲取維修站時間"""
        return self._pit_lane_times

    # ----------------------------
    # Internal helpers
    # ----------------------------
    def _load_stream(self, file_name: str, compressed: bool) -> List[Dict[str, Any]]:
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
            except Exception as exc:  # noqa: BLE001
                print(f"[DATASOURCE] ⚠️ 解碼失敗 (line {idx}): {exc}")
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
        # 1) 優先讀取本地快取
        local_path = self._resolve_local_path(file_name)
        if local_path:
            try:
                with open(local_path, 'r', encoding='utf-8-sig') as file:
                    return file.read()
            except FileNotFoundError:
                pass
            except Exception as exc:  # noqa: BLE001
                print(f"[DATASOURCE] ⚠️ 讀取本地檔案失敗 {local_path}: {exc}")

        # 2) 回退至線上下載
        url = self._build_remote_url(file_name)
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.content.decode('utf-8-sig')
        except Exception as exc:  # noqa: BLE001
            print(f"[DATASOURCE] ❌ 無法下載 {file_name}: {exc}")
            return None

    def _resolve_local_path(self, file_name: str) -> Optional[str]:
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
        return f"{self.base_url}/{self.year}/{self.meeting}/{self.session}/{file_name}"

    @staticmethod
    def _decode_payload(payload: str, compressed: bool) -> Any:
        if not payload:
            return None

        if compressed:
            decoded = base64.b64decode(payload)
            inflated = zlib.decompress(decoded, wbits=-15)
            return json.loads(inflated.decode('utf-8'))
        return json.loads(payload)

    def _normalize_payload(self, payload: Any) -> Any:
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
        except Exception:  # noqa: BLE001
            return None


class LivePositionDataProcessor:
    """資料對齊/整理層 (Silver Layer)."""

    def __init__(self, data_source: LiveF1DataSource):
        self.data_source = data_source
        self._aligned_snapshots: List[Dict[str, Any]] = []
        self._timing_index_full: Dict[str, Dict[str, Any]] = {}
        self._cardata_index_full: Dict[str, Dict[str, Any]] = {}
        self._timing_timestamps: List[str] = []
        self._cardata_timestamps: List[str] = []
        
        # 載入車手資訊
        self._driver_info = data_source.load_driver_list()
        
        # PIT 事件和輪胎資訊
        self._pit_events: List[Dict[str, Any]] = []  # 所有 PIT 事件
        self._driver_stints: Dict[str, List[Dict[str, Any]]] = {}  # 車手 -> 輪胎策略列表
        self._driver_pit_states: Dict[str, Dict[str, Any]] = {}  # 車手當前 PIT 狀態

    # ----------------------------
    # 公開 API
    # ----------------------------
    def process_and_align_data(self, downsample_factor: int = 10):
        """處理並對齊所有數據源 (不再使用降採樣，直接保留所有原始數據點)."""
        print("\n")
        print("=" * 70)
        print("[PROCESSOR] 開始數據處理...")
        print("=" * 70)

        position_data = self.data_source.get_position_data()
        timing_data = self.data_source.get_timing_data()
        cardata = self.data_source.get_cardata()
        
        # 不再降採樣，保留所有原始數據點
        print(f"[PROCESSOR] Position 記錄: {len(position_data)}")
        print(f"[PROCESSOR] Timing 記錄: {len(timing_data)}")
        print(f"[PROCESSOR] CarData 記錄: {len(cardata)}")

        if not position_data:
            print("[PROCESSOR] ❌ Position 數據為空！")
            return

        # 建立索引
        self._build_timing_index(timing_data)
        self._build_cardata_index(cardata)

        aligned_count = 0
        skipped_no_lap = 0
        
        print(f"[PROCESSOR] 🔍 過濾並對齊資料...")
        print(f"[PROCESSOR] 策略: 只保留至少有一位車手有圈數的時間點")

        for pos_record in position_data:
            timestamp = pos_record.get('timestamp')
            pos_data = pos_record.get('data', {})
            position_list = pos_data.get('Position')
            if not position_list or not isinstance(position_list, list):
                continue
            position_entry = position_list[0]
            entries = position_entry.get('Entries')
            if not isinstance(entries, dict):
                continue

            # 先查找 Timing 資料，檢查是否有圈數
            nearest_timing_ts = self._find_nearest_timestamp(timestamp, self._timing_timestamps)
            has_any_lap = False
            
            if nearest_timing_ts and nearest_timing_ts in self._timing_index_full:
                timing_state_all = self._timing_index_full[nearest_timing_ts]
                # 檢查是否至少有一位車手有圈數
                for driver_num in entries.keys():
                    if driver_num in timing_state_all:
                        lap = timing_state_all[driver_num].get('lap')
                        if lap is not None:
                            has_any_lap = True
                            break
            
            # 跳過沒有任何車手有圈數的時間點
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
                
                # 添加車手資訊（名稱、車隊、顏色）
                if driver_num in self._driver_info:
                    info = self._driver_info[driver_num]
                    driver_info['driver_tla'] = info.get('tla', driver_num)  # 三字代碼
                    driver_info['driver_name'] = info.get('name', driver_num)  # 廣播名稱
                    driver_info['team_name'] = info.get('team', '')
                    driver_info['team_color'] = info.get('team_color', 'CCCCCC')

                # 使用累積的最新狀態
                if nearest_timing_ts and nearest_timing_ts in self._timing_index_full:
                    timing_state = self._timing_index_full[nearest_timing_ts].get(driver_num)
                    if timing_state:
                        driver_info.update(timing_state)

                # CarData 使用最近的速度資料
                nearest_cardata_ts = self._find_nearest_timestamp(timestamp, self._cardata_timestamps)
                if nearest_cardata_ts and nearest_cardata_ts in self._cardata_index_full:
                    cardata_state = self._cardata_index_full[nearest_cardata_ts].get(driver_num)
                    if cardata_state and cardata_state.get('speed') is not None:
                        driver_info['speed'] = cardata_state.get('speed')

                snapshot['drivers'][driver_num] = driver_info

            if snapshot['drivers']:
                self._aligned_snapshots.append(snapshot)
                aligned_count += 1

        print(f"[PROCESSOR] ✅ 對齊完成！")
        print(f"[PROCESSOR]    保留快照: {aligned_count} 個")
        print(f"[PROCESSOR]    跳過記錄: {skipped_no_lap} 個 (無圈數資料)")
        
        if self._aligned_snapshots:
            first_time = self._aligned_snapshots[0]['race_time']
            last_time = self._aligned_snapshots[-1]['race_time']
            print(f"[PROCESSOR]    時間範圍: {first_time} ~ {last_time}")
        
        self._calculate_rankings_and_gaps()
        
        # 處理 PIT 事件和輪胎資訊
        self._process_pit_and_tyre_data()

    def get_aligned_snapshots(self) -> List[Dict[str, Any]]:
        return self._aligned_snapshots
    
    def get_pit_events(self) -> List[Dict[str, Any]]:
        """獲取所有 PIT 進站事件"""
        return self._pit_events
    
    def get_driver_stints(self) -> Dict[str, List[Dict[str, Any]]]:
        """獲取車手輪胎策略（各 stint）"""
        return self._driver_stints
    
    def get_tyre_state_at_time(self, timestamp: str) -> Dict[str, Dict[str, Any]]:
        """
        根據時間戳獲取所有車手的輪胎狀態
        
        Args:
            timestamp: 時間戳 (例如 "00:57:42.516")
            
        Returns:
            {driver_num: {compound, new, stint_count, stints}}
        """
        if not hasattr(self, '_tyre_timestamps') or not self._tyre_timestamps:
            return {}
        
        # 將目標時間戳轉換為秒數進行比較
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
    
    def _process_pit_and_tyre_data(self):
        """處理 PIT 事件和輪胎資訊"""
        print("[PROCESSOR] 處理 PIT 和輪胎數據...")
        
        timing_data = self.data_source.get_timing_data()
        timing_app_data = self.data_source.get_timing_app_data()
        
        # 1. 從 TimingData 中提取 PIT 事件
        driver_pit_states = {}  # driver -> {'in_pit': False, 'last_lap': 0}
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
                
                # 初始化
                if driver_num not in driver_pit_states:
                    driver_pit_states[driver_num] = {'in_pit': None, 'last_lap': 0}
                
                # 更新圈數
                if 'NumberOfLaps' in driver_data:
                    driver_pit_states[driver_num]['last_lap'] = driver_data['NumberOfLaps']
                
                # 檢測進站/出站
                if 'InPit' in driver_data:
                    was_in_pit = driver_pit_states[driver_num]['in_pit']
                    now_in_pit = driver_data['InPit']
                    lap = driver_pit_states[driver_num]['last_lap']
                    
                    # 跳過初始狀態的 InPit=True（發車前）
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
        
        # 2. 從 TimingAppData 中建立時間索引的輪胎策略
        # 這樣可以根據當前時間戳查詢車手的輪胎狀態
        # 
        # 【重要】Live F1 的 Stints 資料有兩種格式：
        # 格式 1 (初始): list - [{"Compound": "MEDIUM", ...}]
        # 格式 2 (更新): dict - {"0": {"TotalLaps": 1}} 或 {"1": {"Compound": "HARD", ...}}
        #
        driver_stints_raw = {}  # driver -> {stint_index: {stint_data}}（累積狀態）
        self._tyre_state_index = {}  # timestamp -> {driver -> current_tyre_info}
        
        import copy
        latest_tyre_state = {}  # driver -> current_tyre_info
        
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
                
                # 初始化車手的 stint 字典
                if driver_num not in driver_stints_raw:
                    driver_stints_raw[driver_num] = {}
                
                # 格式 1: 初始完整列表 [{"Compound": "MEDIUM", ...}]
                if isinstance(stints, list):
                    for i, stint in enumerate(stints):
                        if isinstance(stint, dict):
                            driver_stints_raw[driver_num][i] = {
                                'compound': stint.get('Compound', 'UNKNOWN'),
                                'new': stint.get('New') == 'true' or stint.get('New') == True,
                                'total_laps': stint.get('TotalLaps', 0),
                                'start_laps': stint.get('StartLaps', 0),
                            }
                
                # 格式 2: 增量更新 {"0": {"TotalLaps": 5}} 或 {"1": {"Compound": "HARD", ...}}
                elif isinstance(stints, dict):
                    for stint_index_str, stint_update in stints.items():
                        if not isinstance(stint_update, dict):
                            continue
                        
                        stint_index = int(stint_index_str)
                        
                        # 如果是新的 stint，初始化
                        if stint_index not in driver_stints_raw[driver_num]:
                            driver_stints_raw[driver_num][stint_index] = {
                                'compound': 'UNKNOWN',
                                'new': False,
                                'total_laps': 0,
                                'start_laps': 0,
                            }
                        
                        # 合併更新
                        if 'Compound' in stint_update:
                            driver_stints_raw[driver_num][stint_index]['compound'] = stint_update['Compound']
                        if 'New' in stint_update:
                            driver_stints_raw[driver_num][stint_index]['new'] = (
                                stint_update['New'] == 'true' or stint_update['New'] == True
                            )
                        if 'TotalLaps' in stint_update:
                            driver_stints_raw[driver_num][stint_index]['total_laps'] = stint_update['TotalLaps']
                        if 'StartLaps' in stint_update:
                            driver_stints_raw[driver_num][stint_index]['start_laps'] = stint_update['StartLaps']
                
                # 將累積狀態轉換為列表格式，並更新 latest_tyre_state
                if driver_stints_raw[driver_num]:
                    # 按 stint index 排序，轉成列表
                    sorted_indices = sorted(driver_stints_raw[driver_num].keys())
                    parsed_stints = []
                    for idx in sorted_indices:
                        stint_data = driver_stints_raw[driver_num][idx]
                        parsed_stints.append({
                            'stint_number': idx + 1,
                            **stint_data
                        })
                    
                    # 更新當前輪胎狀態（使用最後一個 stint）
                    current_stint = parsed_stints[-1]
                    latest_tyre_state[driver_num] = {
                        'compound': current_stint['compound'],
                        'new': current_stint['new'],
                        'stint_count': len(parsed_stints),
                        'stints': copy.deepcopy(parsed_stints),
                        # 添加 tyre_age：當前 stint 的使用圈數
                        'tyre_age': current_stint.get('total_laps', 0),
                    }
            
            # 保存當前時間戳的輪胎狀態快照
            if timestamp and latest_tyre_state:
                self._tyre_state_index[timestamp] = copy.deepcopy(latest_tyre_state)
        
        # 最終結果：將 raw dict 轉成 list 格式
        driver_stints = {}
        for driver_num, stints_dict in driver_stints_raw.items():
            sorted_indices = sorted(stints_dict.keys())
            driver_stints[driver_num] = [
                {'stint_number': idx + 1, **stints_dict[idx]}
                for idx in sorted_indices
            ]
        
        self._driver_stints = driver_stints
        # 用秒數排序時間戳，確保順序正確
        self._tyre_timestamps = sorted(
            self._tyre_state_index.keys(),
            key=lambda ts: self._time_str_to_seconds(ts) or 0
        )
        
        # 統計輸出
        pit_in_count = len([e for e in pit_events if e['type'] == 'PIT_IN'])
        print(f"[PROCESSOR] ✅ PIT 事件: {pit_in_count} 次進站")
        print(f"[PROCESSOR] ✅ 輪胎策略: {len(driver_stints)} 位車手")
        print(f"[PROCESSOR] ✅ 輪胎狀態索引: {len(self._tyre_timestamps)} 個時間戳")

    # ----------------------------
    # 索引/計算 helpers
    # ----------------------------
    def _build_timing_index(self, timing_data: List[Dict[str, Any]]):
        import copy  # 添加 copy 模組
        
        sorted_timing = sorted(timing_data, key=lambda item: item.get('timestamp', ''))
        latest_driver_state: Dict[str, Dict[str, Any]] = {}
        index: Dict[str, Dict[str, Any]] = {}

        for record in sorted_timing:
            timestamp = record.get('timestamp')
            data = record.get('data', {})
            lines = data.get('Lines', {})
            if not isinstance(lines, dict):
                continue

            for driver_num, driver_data in lines.items():
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
                
                # Sector 時間 (S1/S2/S3)
                sectors = driver_data.get('Sectors', {})

                # 初始化車手狀態（如果不存在）
                if driver_num not in latest_driver_state:
                    latest_driver_state[driver_num] = {}

                # 增量式更新：只更新有值的欄位
                if lap_num is not None:
                    latest_driver_state[driver_num]['lap'] = lap_num
                
                # 上一圈時間
                if isinstance(last_lap, dict) and last_lap.get('Value'):
                    latest_driver_state[driver_num]['last_lap_time'] = last_lap.get('Value')
                    latest_driver_state[driver_num]['last_lap_personal_fastest'] = last_lap.get('PersonalFastest', False)
                    latest_driver_state[driver_num]['last_lap_overall_fastest'] = last_lap.get('OverallFastest', False)
                
                # 最佳圈時
                if isinstance(best_lap, dict) and best_lap.get('Value'):
                    latest_driver_state[driver_num]['best_lap_time'] = best_lap.get('Value')
                    latest_driver_state[driver_num]['best_lap_number'] = best_lap.get('Lap')
                
                # Sector 時間 - S1 (index "0"), S2 (index "1"), S3 (index "2")
                if isinstance(sectors, dict):
                    for sector_idx, sector_key in [('0', 's1'), ('1', 's2'), ('2', 's3')]:
                        sector_data = sectors.get(sector_idx, {})
                        if isinstance(sector_data, dict):
                            sector_value = sector_data.get('Value')
                            if sector_value:
                                latest_driver_state[driver_num][f'{sector_key}_time'] = sector_value
                                # 記錄顏色狀態 (PersonalFastest/OverallFastest)
                                latest_driver_state[driver_num][f'{sector_key}_personal_fastest'] = sector_data.get('PersonalFastest', False)
                                latest_driver_state[driver_num][f'{sector_key}_overall_fastest'] = sector_data.get('OverallFastest', False)
                
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

            if timestamp:
                # 使用深拷貝確保每個時間戳的狀態獨立
                index[timestamp] = copy.deepcopy(latest_driver_state)

        self._timing_timestamps = sorted(index.keys())
        self._timing_index_full = index
        
        print(f"[PROCESSOR] ✅ Timing 索引建立完成: {len(self._timing_timestamps)} 個時間戳")
        if self._timing_timestamps:
            print(f"  第一個: {self._timing_timestamps[0]}")
            print(f"  最後一個: {self._timing_timestamps[-1]}")
            first_ts_data = self._timing_index_full[self._timing_timestamps[0]]
            print(f"  第一個時間戳包含 {len(first_ts_data)} 位車手")

    def _build_cardata_index(self, cardata: List[Dict[str, Any]]):
        import copy  # 添加 copy 模組
        
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
                        # 初始化車手狀態（如果不存在）
                        if driver_num not in latest_driver_state:
                            latest_driver_state[driver_num] = {}
                        # 更新速度
                        latest_driver_state[driver_num]['speed'] = speed

            if timestamp:
                # 使用深拷貝確保每個時間戳的狀態獨立
                index[timestamp] = copy.deepcopy(latest_driver_state)

        self._cardata_timestamps = sorted(index.keys())
        self._cardata_index_full = index
        
        print(f"[PROCESSOR] ✅ CarData 索引建立完成: {len(self._cardata_timestamps)} 個時間戳")
        if self._cardata_timestamps:
            print(f"  第一個: {self._cardata_timestamps[0]}")
            print(f"  最後一個: {self._cardata_timestamps[-1]}")
            first_ts_data = self._cardata_index_full[self._cardata_timestamps[0]]
            print(f"  第一個時間戳包含 {len(first_ts_data)} 位車手")

    def _calculate_rankings_and_gaps(self):
        print(f"[PROCESSOR] 計算排名和差距...")
        for snapshot in self._aligned_snapshots:
            drivers = snapshot['drivers']
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
                else:
                    gap_seconds = driver_data.get('gap_to_leader')
                    gap_laps = driver_data.get('gap_to_leader_laps', 0)
                    driver_data['gap_to_leader_display'] = self._format_gap_label(gap_seconds, gap_laps)

                interval_seconds = driver_data.get('gap_to_ahead')
                driver_data['gap_to_ahead_display'] = self._format_interval_label(interval_seconds)

        print(f"[PROCESSOR] ✅ 排名計算完成")

    # ----------------------------
    # Formatting helpers
    # ----------------------------
    @staticmethod
    def _format_interval_label(seconds: Optional[float]) -> str:
        if seconds is None:
            return "—"
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
            hours = int(time_str[0:2])
            minutes = int(time_str[2:4])
            seconds = float(time_str[4:])
            return hours * 3600 + minutes * 60 + seconds
        except Exception:
            try:
                h, m, s = time_str.split(':')
                return int(h) * 3600 + int(m) * 60 + float(s)
            except Exception:
                return 0.0

    def _find_nearest_timestamp(self, target: str, timestamp_list: List[str]) -> Optional[str]:
        """查找最近的**過去**時間戳（不包括未來時間戳）"""
        if not timestamp_list:
            return None
        if target in timestamp_list:
            return target
        
        target_seconds = self._time_str_to_seconds(target)
        
        # 二分查找：找到 <= target 的最大時間戳
        left, right = 0, len(timestamp_list) - 1
        result = None
        
        while left <= right:
            mid = (left + right) // 2
            mid_seconds = self._time_str_to_seconds(timestamp_list[mid])
            
            if mid_seconds <= target_seconds:
                # 這個時間戳在目標之前，記錄並繼續向右查找
                result = timestamp_list[mid]
                left = mid + 1
            else:
                # 這個時間戳在目標之後，向左查找
                right = mid - 1
        
        return result


class TrackMapWidget(QWidget):
    """賽道地圖顯示元件."""


    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(400, 400)

        self.track_outline: List[Tuple[float, float]] = []
        self.track_points: List[Dict[str, float]] = []
        self.track_bounds: Dict[str, float] = {}
        self.track_length = 0.0

        self.driver_positions: Dict[str, Dict[str, Any]] = {}
        self._marker_positions: List[Dict[str, Any]] = []

        self.timeline_index = 0
        self.timeline_total = 1
        self.current_race_time_seconds = 0.0
        self.total_race_duration_seconds = 1.0
        self._default_speed_kmh = 220.0

        self.position_colors = {
            1: QColor(255, 215, 0),
            2: QColor(192, 192, 192),
            3: QColor(205, 127, 50),
        }

        print("[TRACK_MAP] TrackMapWidget 初始化完成")

    def set_race_duration(self, seconds: float):
        if seconds and seconds > 0:
            self.total_race_duration_seconds = seconds

    def load_track_outline(self, track_data: Dict):
        try:
            position_records = track_data.get('position_records', [])
            if not position_records:
                print("[TRACK_MAP] ⚠️  無賽道位置記錄")
                return

            self.track_outline = []
            self.track_points = []
            self.track_bounds = track_data.get('track_bounds', {}) or {}
            self.track_length = 0.0

            for record in position_records:
                x = record.get('position_x')
                y = record.get('position_y')
                distance = record.get('distance_m') or record.get('distance')
                if x is None or y is None:
                    continue
                self.track_outline.append((x, y))
                if distance is None:
                    if self.track_points:
                        prev = self.track_points[-1]
                        dx = x - prev['x']
                        dy = y - prev['y']
                        distance = prev['distance'] + (dx ** 2 + dy ** 2) ** 0.5
                    else:
                        distance = 0.0
                self.track_points.append({'x': x, 'y': y, 'distance': float(distance)})
                if distance > self.track_length:
                    self.track_length = float(distance)

            self.track_points.sort(key=lambda item: item['distance'])
            print(f"[TRACK_MAP] ✅ 賽道輪廓載入: {len(self.track_outline)} 個點 (長度 {self.track_length:.1f} m)")
            print(f"[TRACK_MAP] 📏 賽道邊界: {self.track_bounds}")
            self.update()

        except Exception as e:
            print(f"[TRACK_MAP] ❌ 載入賽道輪廓失敗: {e}")
            import traceback
            traceback.print_exc()

    def update_driver_positions(
        self,
        drivers_data: Dict,
        frame_index: int = 0,
        total_frames: int = 1,
        race_time_seconds: float = 0.0,
    ):
        self.driver_positions = drivers_data or {}
        self.timeline_index = frame_index
        self.timeline_total = max(1, total_frames)
        self.current_race_time_seconds = race_time_seconds
        self._prepare_marker_positions()
        self.update()

    def _prepare_marker_positions(self):
        """準備車手標記位置（直接使用 Position 資料的真實 X/Y 座標）"""
        if not self.driver_positions:
            self._marker_positions = []
            return

        markers = []
        for driver_num, driver_data in self.driver_positions.items():
            # 直接使用 Position 資料中的真實 X/Y 座標
            x = driver_data.get('x')
            y = driver_data.get('y')
            
            # 如果沒有座標，跳過
            if x is None or y is None:
                continue
            
            markers.append({
                'driver': driver_num,
                'x': x,
                'y': y,
                'position': driver_data.get('position'),
                'status': driver_data.get('status', 'Unknown')
            })
        
        self._marker_positions = markers

    def _estimate_leader_distance(self) -> float:
        if self.track_length <= 0:
            return 0.0
        frame_ratio = 0.0
        if self.timeline_total > 1:
            frame_ratio = self.timeline_index / (self.timeline_total - 1)
        time_ratio = min(1.0, self.current_race_time_seconds / self.total_race_duration_seconds) if self.total_race_duration_seconds else 0.0
        progress = max(frame_ratio, time_ratio)
        return progress * self.track_length

    def _estimate_driver_distance(self, leader_distance: float, driver_data: Dict, order: int) -> float:
        track_length = self.track_length or 1.0
        gap_laps = driver_data.get('gap_to_leader_laps', 0) or 0
        base_distance = leader_distance - gap_laps * track_length

        gap_seconds = driver_data.get('gap_to_leader')
        speed = driver_data.get('speed') or self._default_speed_kmh
        speed_mps = (speed or self._default_speed_kmh) * 1000 / 3600
        if gap_seconds is not None and speed_mps:
            base_distance -= gap_seconds * speed_mps

        # 避免重疊：按順序減少少量距離
        base_distance -= order * 5.0
        base_distance %= track_length
        return base_distance

    def _interpolate_point(self, distance: float) -> Tuple[Optional[float], Optional[float]]:
        if not self.track_points:
            return None, None
        distance %= self.track_length
        prev_point = self.track_points[0]
        for point in self.track_points[1:]:
            if point['distance'] >= distance:
                segment = point['distance'] - prev_point['distance']
                if segment == 0:
                    ratio = 0.0
                else:
                    ratio = (distance - prev_point['distance']) / segment
                x = prev_point['x'] + ratio * (point['x'] - prev_point['x'])
                y = prev_point['y'] + ratio * (point['y'] - prev_point['y'])
                return x, y
            prev_point = point
        return self.track_points[-1]['x'], self.track_points[-1]['y']

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        transform = self._compute_transform()
        if transform and self.track_outline:
            self._draw_track_outline(painter, transform)
            self._draw_driver_markers(painter, transform)
        else:
            painter.setPen(QColor(200, 200, 200))
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "載入賽道輪廓中...")

        self._draw_legend(painter)

    def _compute_transform(self) -> Optional[Dict[str, float]]:
        if not self.track_outline:
            return None

        margin = 50
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin

        x_min = self.track_bounds.get('x_min') if self.track_bounds else min(x for x, _ in self.track_outline)
        x_max = self.track_bounds.get('x_max') if self.track_bounds else max(x for x, _ in self.track_outline)
        y_min = self.track_bounds.get('y_min') if self.track_bounds else min(y for _, y in self.track_outline)
        y_max = self.track_bounds.get('y_max') if self.track_bounds else max(y for _, y in self.track_outline)

        x_range = x_max - x_min if x_max != x_min else 1
        y_range = y_max - y_min if y_max != y_min else 1

        scale = min(width / x_range, height / y_range)
        offset_x = (width - x_range * scale) / 2
        offset_y = (height - y_range * scale) / 2

        return {
            'margin': margin,
            'scale': scale,
            'offset_x': offset_x,
            'offset_y': offset_y,
            'x_min': x_min,
            'y_min': y_min,
        }

    def _draw_track_outline(self, painter: QPainter, transform: Dict[str, float]):
        painter.setPen(QPen(QColor(100, 100, 100), 3))
        for i in range(len(self.track_outline) - 1):
            x1, y1 = self._world_to_screen(self.track_outline[i], transform)
            x2, y2 = self._world_to_screen(self.track_outline[i + 1], transform)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        if self.track_outline:
            x_start, y_start = self._world_to_screen(self.track_outline[0], transform)
            painter.setBrush(QBrush(QColor(0, 255, 0)))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawEllipse(QPointF(x_start, y_start), 8, 8)

    def _world_to_screen(self, point: Tuple[float, float], transform: Dict[str, float]) -> Tuple[float, float]:
        x, y = point
        margin = transform['margin']
        scale = transform['scale']
        x_min = transform['x_min']
        y_min = transform['y_min']
        offset_x = transform['offset_x']
        offset_y = transform['offset_y']
        screen_x = margin + offset_x + (x - x_min) * scale
        screen_y = margin + offset_y + (y - y_min) * scale
        return screen_x, screen_y

    def _draw_driver_markers(self, painter: QPainter, transform: Dict[str, float]):
        if not self._marker_positions:
            return

        for marker in self._marker_positions:
            screen_x, screen_y = self._world_to_screen((marker['x'], marker['y']), transform)

            position = marker.get('position', 999)
            status = marker.get('status', 'Unknown')

            if position in self.position_colors:
                color = self.position_colors[position]
                radius = 12
            else:
                if status == 'OnTrack':
                    color = QColor(100, 200, 100)
                elif status == 'Stopped':
                    color = QColor(200, 100, 100)
                else:
                    color = QColor(150, 150, 150)
                radius = 8

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawEllipse(QPointF(screen_x, screen_y), radius, radius)

            painter.setPen(QColor(255, 255, 255))
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            text_rect = painter.fontMetrics().boundingRect(marker['driver'])
            text_x = screen_x - text_rect.width() / 2
            text_y = screen_y + text_rect.height() / 2 - 2
            painter.drawText(int(text_x), int(text_y), marker['driver'])

    def _draw_legend(self, painter: QPainter):
        legend_x = 12
        legend_y = 12

        painter.setPen(QColor(200, 200, 200))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(legend_x, legend_y + 12, "圖例:")

        legend_items = [
            (self.position_colors.get(1, QColor(255, 215, 0)), "P1"),
            (self.position_colors.get(2, QColor(192, 192, 192)), "P2"),
            (self.position_colors.get(3, QColor(205, 127, 50)), "P3"),
            (QColor(100, 200, 100), "在場上"),
            (QColor(200, 100, 100), "停下"),
            (QColor(150, 150, 150), "其他"),
        ]

        y_offset = legend_y + 30
        for color, label in legend_items:
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(legend_x, y_offset - 6, 12, 12)
            painter.setPen(QColor(220, 220, 220))
            painter.drawText(legend_x + 20, y_offset + 2, label)
            y_offset += 18

    @staticmethod
    def _format_interval_label(seconds: Optional[float]) -> str:
        if seconds is None:
            return "—"
        return f"{seconds:.3f}s"
    
    def _parse_timestamp(self, ts_str: str) -> timedelta:
        """解析時間戳 'HH:MM:SS.mmm' -> timedelta"""
        parts = ts_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    
    def _format_timedelta(self, td: timedelta) -> str:
        """格式化 timedelta 為 'HH:MM:SS.mmm'"""
        total_seconds = td.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    
    def _find_nearest_timestamp(self, target: str, timestamp_list: List[str]) -> Optional[str]:
        """查找最近的時間戳（使用字串直接比較）"""
        if not timestamp_list:
            return None
        
        # 直接返回相同時間戳
        if target in timestamp_list:
            return target
        
        # 找最近的（使用字串比較，時間戳格式為 HH:MM:SS.mmm）
        closest = None
        min_diff = None
        
        for ts in timestamp_list:
            diff = abs(self._timestamp_diff(target, ts))
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest = ts
                
                # 如果差異小於 1 秒，直接返回（性能優化）
                if min_diff < 1.0:
                    break
        
        return closest
    
    def _timestamp_diff(self, ts1: str, ts2: str) -> float:
        """計算兩個時間戳的差異（秒）"""
        try:
            # 解析時間戳 "HH:MM:SS.mmm"
            t1 = self._parse_timestamp(ts1)
            t2 = self._parse_timestamp(ts2)
            return abs(t1.total_seconds() - t2.total_seconds())
        except:
            return float('inf')
    
    def process_and_align_data(self):
        """處理並對齊所有數據源"""
        print("\n" + "="*70)
        print("[PROCESSOR] 開始數據處理...")
        print("="*70)
        
        position_data = self.data_source.get_position_data()
        timing_data = self.data_source.get_timing_data()
        cardata = self.data_source.get_cardata()
        
        if not position_data:
            print("[PROCESSOR] ❌ Position 數據為空！")
            return
        
        print(f"[PROCESSOR] Position 記錄: {len(position_data)}")
        print(f"[PROCESSOR] Timing 記錄: {len(timing_data)}")
        print(f"[PROCESSOR] CarData 記錄: {len(cardata)}")
        
        # 建立時間戳索引
        timing_dict = self._build_timing_index(timing_data)
        cardata_dict = self._build_cardata_index(cardata)
        
        print(f"[PROCESSOR] 建立索引完成")
        print(f"[PROCESSOR] 開始對齊時間戳...")
        
        # 遍歷 Position 數據，對齊其他數據源
        aligned_count = 0
        
        # 預先獲取最新狀態（避免每次循環查找）
        latest_timing_state = {}
        latest_cardata_state = {}
        
        print(f"[PROCESSOR] 預處理 Timing 和 CarData 索引...")
        
        # 遍歷 Timing 數據，保存每位車手的最新狀態
        for timing_record in timing_data:
            data = timing_record['data']
            if 'Lines' in data:
                for driver_num, driver_data in data['Lines'].items():
                    lap_num = driver_data.get('NumberOfLaps')
                    if lap_num:
                        latest_timing_state[driver_num] = {
                            'lap': lap_num,
                            'last_lap_time': driver_data.get('LastLapTime', {}).get('Value')
                        }
        
        # 遍歷 CarData，保存每位車手的最新速度
        for cardata_record in cardata:
            data = cardata_record['data']
            if 'Entries' in data:
                for entry in data['Entries']:
                    cars = entry.get('Cars', {})
                    for driver_num, car_data in cars.items():
                        channels = car_data.get('Channels', {})
                        speed = channels.get('2')  # Channel 2 = Speed (km/h)
                        if speed is not None:
                            latest_cardata_state[driver_num] = {'speed': speed}
        
        print(f"[PROCESSOR] 預處理完成！開始生成快照...")
        
        for pos_record in position_data:
            timestamp = pos_record['timestamp']
            pos_data = pos_record['data']
            
            # 提取 Position 數據
            if 'Position' not in pos_data:
                continue
            
            # Position 是列表，取第一個元素
            position_list = pos_data['Position']
            if not position_list or not isinstance(position_list, list):
                continue
            
            # 取第一個元素的 Entries
            position_entry = position_list[0]
            if 'Entries' not in position_entry:
                continue
            
            # 構建完整快照
            snapshot = {
                'race_time': timestamp,
                'race_time_seconds': self._time_str_to_seconds(timestamp),
                'drivers': {}
            }
            
            # 遍歷所有車手
            for driver_num, driver_pos in position_entry['Entries'].items():
                # 基本位置信息
                driver_info = {
                    'driver_number': driver_num,
                    'status': driver_pos.get('Status', 'Unknown'),
                    'x': driver_pos.get('X'),
                    'y': driver_pos.get('Y'),
                    'z': driver_pos.get('Z'),
                }
                
                # 從預處理的最新狀態獲取圈數和圈時
                timing_state = latest_timing_state.get(driver_num)
                if timing_state:
                    driver_info['lap'] = timing_state.get('lap')
                    driver_info['last_lap_time'] = timing_state.get('last_lap_time')
                    driver_info['last_lap_personal_fastest'] = timing_state.get('last_lap_personal_fastest', False)
                    driver_info['last_lap_overall_fastest'] = timing_state.get('last_lap_overall_fastest', False)
                    driver_info['best_lap_time'] = timing_state.get('best_lap_time')
                    driver_info['best_lap_number'] = timing_state.get('best_lap_number')
                    driver_info['gap_to_leader'] = timing_state.get('gap_to_leader')
                    driver_info['gap_to_leader_laps'] = timing_state.get('gap_to_leader_laps', 0)
                    driver_info['gap_to_ahead'] = timing_state.get('gap_to_ahead')
                    driver_info['position'] = timing_state.get('position')
                    # PIT 狀態
                    driver_info['in_pit'] = timing_state.get('in_pit')
                    driver_info['pit_out'] = timing_state.get('pit_out')
                    driver_info['num_pit_stops'] = timing_state.get('num_pit_stops')
                
                # 從預處理的最新狀態獲取速度
                if driver_num in latest_cardata_state:
                    driver_info['speed'] = latest_cardata_state[driver_num].get('speed')
                
                snapshot['drivers'][driver_num] = driver_info
            
            if snapshot['drivers']:
                self._aligned_snapshots.append(snapshot)
                aligned_count += 1
        
        print(f"[PROCESSOR] ✅ 對齊完成！生成 {aligned_count} 個時間快照")
        
        # 計算排名和差距
        self._calculate_rankings_and_gaps()
    
    def _build_timing_index(self, timing_data: List[Dict]) -> Dict[str, Dict[str, Dict]]:
        """建立 TimingData 的時間戳索引（使用最近鄰匹配）"""
        # 先按時間戳排序
        sorted_timing = sorted(timing_data, key=lambda x: x['timestamp'])
        
        # 建立完整索引（保留所有車手的最新狀態）
        latest_driver_state = {}  # 保存每位車手的最新狀態
        index = {}
        
        for record in sorted_timing:
            timestamp = record['timestamp']
            data = record['data']
            
            if 'Lines' not in data:
                continue
            
            # 更新車手狀態
            for driver_num, driver_data in data['Lines'].items():
                lap_num = driver_data.get('NumberOfLaps')
                last_lap = driver_data.get('LastLapTime', {})
                gap_sec, gap_laps = self._parse_gap_value(driver_data.get('GapToLeader'))
                interval_sec, _ = self._parse_gap_value(driver_data.get('IntervalToPositionAhead'))
                position_val = self._safe_int(driver_data.get('Position'))
                
                latest_driver_state[driver_num] = {
                    'lap': lap_num,
                    'last_lap_time': last_lap.get('Value') if isinstance(last_lap, dict) else None,
                    'gap_to_leader': gap_sec,
                    'gap_to_leader_laps': gap_laps,
                    'gap_to_ahead': interval_sec,
                    'position': position_val
                }
            
            # 保存當前時間點所有車手的狀態（使用最新狀態）
            index[timestamp] = dict(latest_driver_state)
        
        # 建立時間戳列表用於最近鄰查找
        self._timing_timestamps = sorted(index.keys())
        self._timing_index_full = index
        
        return index
    
    def _build_cardata_index(self, cardata: List[Dict]) -> Dict[str, Dict[str, Dict]]:
        """建立 CarData 的時間戳索引（使用最近鄰匹配）"""
        # 先按時間戳排序
        sorted_cardata = sorted(cardata, key=lambda x: x['timestamp'])
        
        # 建立完整索引（保留所有車手的最新狀態）
        latest_driver_state = {}
        index = {}
        
        for record in sorted_cardata:
            timestamp = record['timestamp']
            data = record['data']
            
            if 'Entries' not in data:
                continue
            
            # 更新車手狀態
            for entry in data['Entries']:
                cars = entry.get('Cars', {})
                for driver_num, car_data in cars.items():
                    channels = car_data.get('Channels', {})
                    speed = channels.get('2')  # ✅ 修復: Channel 2 = Speed (km/h), Channel 0 = RPM
                    
                    if speed is not None:
                        latest_driver_state[driver_num] = {
                            'speed': speed
                        }
            
            # 保存當前時間點所有車手的狀態
            index[timestamp] = dict(latest_driver_state)
        
        # 建立時間戳列表用於最近鄰查找
        self._cardata_timestamps = sorted(index.keys())
        self._cardata_index_full = index
        
        return index
    
    def _calculate_rankings_and_gaps(self):
        """計算排名和與前車差距"""
        print(f"[PROCESSOR] 計算排名和差距...")
        
        for snapshot in self._aligned_snapshots:
            drivers = snapshot['drivers']
            
            sorted_drivers = sorted(
                drivers.items(),
                key=lambda item: (
                    item[1].get('position') if item[1].get('position') is not None else 999,
                    -(item[1].get('lap') or 0)
                )
            )
            
            for fallback_position, (driver_num, driver_data) in enumerate(sorted_drivers, start=1):
                official_position = driver_data.get('position')
                driver_data['position'] = official_position or fallback_position
                
                if driver_data['position'] == 1:
                    driver_data['gap_to_leader'] = 0.0
                    driver_data['gap_to_leader_laps'] = 0
                    driver_data['gap_to_leader_display'] = "0.000s"
                else:
                    gap_seconds = driver_data.get('gap_to_leader')
                    gap_laps = driver_data.get('gap_to_leader_laps', 0)
                    driver_data['gap_to_leader_display'] = self._format_gap_label(gap_seconds, gap_laps)
                
                interval_seconds = driver_data.get('gap_to_ahead')
                driver_data['gap_to_ahead_display'] = self._format_interval_label(interval_seconds)
        
        print(f"[PROCESSOR] ✅ 排名計算完成")
    
    def get_aligned_snapshots(self) -> List[Dict]:
        """獲取對齊後的時間快照"""
        return self._aligned_snapshots


# ========== GUI 展示層 (Gold Layer) ==========


# 輪胎顏色映射
TYRE_COLORS = {
    'SOFT': '#FF3333',      # 紅色
    'MEDIUM': '#FFDD00',    # 黃色
    'HARD': '#FFFFFF',      # 白色
    'INTERMEDIATE': '#43B02A',  # 綠色
    'WET': '#0066FF',       # 藍色
    'UNKNOWN': '#888888',   # 灰色
}

TYRE_ABBREV = {
    'SOFT': 'S',
    'MEDIUM': 'M', 
    'HARD': 'H',
    'INTERMEDIATE': 'I',
    'WET': 'W',
    'UNKNOWN': '?',
}


def create_tyre_label(compound: str, is_new: bool = True, show_new_indicator: bool = True) -> QLabel:
    """
    建立一個帶顏色的輪胎標籤
    
    Args:
        compound: 輪胎種類 (SOFT, MEDIUM, HARD, etc.)
        is_new: 是否為新胎
        show_new_indicator: 是否顯示 N/U 標記
    
    Returns:
        QLabel: 帶顏色背景的輪胎標籤
    """
    abbrev = TYRE_ABBREV.get(compound, '?')
    color = TYRE_COLORS.get(compound, TYRE_COLORS['UNKNOWN'])
    
    # 文字內容
    if show_new_indicator:
        new_indicator = "N" if is_new else "U"
        text = f" {abbrev}({new_indicator}) "
    else:
        text = f" {abbrev} "
    
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    
    # 設置背景顏色和文字顏色
    if compound in ['HARD', 'MEDIUM']:
        text_color = '#000000'
    else:
        text_color = '#FFFFFF'
    
    label.setStyleSheet(f"""
        QLabel {{
            background-color: {color};
            color: {text_color};
            font-weight: bold;
            border-radius: 3px;
            padding: 1px 3px;
            margin: 1px;
        }}
    """)
    
    return label


class TyreStrategyWidget(QWidget):
    """
    輪胎策略顯示 widget - 用於在表格中顯示帶顏色的輪胎序列
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(2)
        self._layout.addStretch()  # 初始填充
    
    def set_strategy(self, stints: list, pit_count: int = 0, pit_laps: list = None):
        """
        設置輪胎策略
        
        Args:
            stints: stint 列表，每個 stint 包含 compound, new 等資訊
            pit_count: 進站次數（用於補足缺失的 stint 資訊）
            pit_laps: 進站圈數列表
        """
        # 清除現有 widgets
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 如果沒有進站，顯示 "-"
        if pit_count == 0 and len(stints) <= 1:
            label = QLabel("-")
            label.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(label)
            return
        
        # 遍歷 stints（跳過第一個，因為那是起跑輪胎）
        displayed_count = 0
        for i, stint in enumerate(stints):
            if i == 0:
                continue  # 跳過起跑輪胎
            
            if displayed_count > 0:
                # 添加箭頭
                arrow = QLabel("->")
                arrow.setAlignment(Qt.AlignCenter)
                self._layout.addWidget(arrow)
            
            compound = stint.get('compound', 'UNKNOWN')
            is_new = stint.get('new', False)
            
            tyre_label = create_tyre_label(compound, is_new, show_new_indicator=True)
            self._layout.addWidget(tyre_label)
            displayed_count += 1
        
        # 如果有進站但 stint 資料不足，用 "PIT@圈數" 補足
        if pit_laps is None:
            pit_laps = []
        
        if pit_count > displayed_count:
            missing_count = pit_count - displayed_count
            for idx in range(missing_count):
                if displayed_count + idx > 0:
                    arrow = QLabel("->")
                    arrow.setAlignment(Qt.AlignCenter)
                    self._layout.addWidget(arrow)
                
                pit_lap = pit_laps[displayed_count + idx] if displayed_count + idx < len(pit_laps) else "?"
                pit_label = QLabel(f" PIT@{pit_lap} ")
                pit_label.setAlignment(Qt.AlignCenter)
                pit_label.setStyleSheet("""
                    QLabel {
                        background-color: #666666;
                        color: #FFFFFF;
                        font-weight: bold;
                        border-radius: 3px;
                        padding: 1px 3px;
                        margin: 1px;
                    }
                """)
                self._layout.addWidget(pit_label)
        
        # 如果還是空的，顯示 "-"
        if self._layout.count() == 0:
            label = QLabel("-")
            label.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(label)


# ============================================================
# 賽事資訊 Widget
# ============================================================

class RaceInfoWidget(QWidget):
    """
    賽事資訊面板 - 顯示圈數進度、天氣、賽道狀態
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._current_lap = 0
        self._total_laps = 53
        self._track_status = "1"  # 1=綠旗, 2=黃旗, 4=SC, 5=紅旗, 6=VSC
        self._weather = {}
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(15)
        
        # 圈數進度
        self.lap_label = QLabel("圈數: 0/53")
        self.lap_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.lap_label)
        
        # 賽道狀態指示器
        self.status_label = QLabel(" GREEN ")
        self.status_label.setStyleSheet("""
            background-color: #00FF00;
            color: #000000;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 3px;
        """)
        layout.addWidget(self.status_label)
        
        # 天氣資訊
        self.weather_label = QLabel("氣溫: --°C | 賽道: --°C | 濕度: --%")
        self.weather_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.weather_label)
        
        layout.addStretch()
    
    def update_lap(self, current_lap: int, total_laps: int = None):
        """更新圈數"""
        self._current_lap = current_lap
        if total_laps:
            self._total_laps = total_laps
        self.lap_label.setText(f"圈數: {self._current_lap}/{self._total_laps}")
    
    def update_track_status(self, status: str, message: str = ""):
        """更新賽道狀態"""
        self._track_status = status
        
        # 狀態對應的顏色和文字
        status_map = {
            "1": ("GREEN", "#00FF00", "#000000"),
            "2": ("YELLOW", "#FFFF00", "#000000"),
            "4": ("SC", "#FFD700", "#000000"),
            "5": ("RED", "#FF0000", "#FFFFFF"),
            "6": ("VSC", "#FFFF00", "#000000"),
            "7": ("VSC END", "#00FF00", "#000000"),
        }
        
        text, bg_color, text_color = status_map.get(status, ("UNKNOWN", "#888888", "#FFFFFF"))
        
        self.status_label.setText(f" {text} ")
        self.status_label.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 3px;
        """)
    
    def update_weather(self, weather_data: Dict[str, Any]):
        """更新天氣資訊"""
        self._weather = weather_data
        
        air_temp = weather_data.get('AirTemp', '--')
        track_temp = weather_data.get('TrackTemp', '--')
        humidity = weather_data.get('Humidity', '--')
        rainfall = weather_data.get('Rainfall', '0')
        
        rain_icon = " [Rain]" if rainfall != '0' else ""
        
        self.weather_label.setText(
            f"氣溫: {air_temp}°C | 賽道: {track_temp}°C | 濕度: {humidity}%{rain_icon}"
        )


class RaceControlMessagesWidget(QWidget):
    """
    比賽控制訊息面板 - 顯示黃旗、處罰、調查等訊息
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._all_messages: List[Dict[str, Any]] = []
        self._current_lap = 0
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 標題
        title = QLabel("比賽控制訊息")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 訊息列表
        self.message_list = QTableWidget()
        self.message_list.setColumnCount(3)
        self.message_list.setHorizontalHeaderLabels(["圈", "類型", "訊息"])
        self.message_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.message_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.message_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.message_list.setColumnWidth(0, 35)
        self.message_list.setColumnWidth(1, 70)
        self.message_list.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.message_list)
    
    def set_messages(self, messages: List[Dict[str, Any]]):
        """設置所有訊息"""
        self._all_messages = messages
    
    def update_for_lap(self, current_lap: int):
        """根據當前圈數更新顯示"""
        self._current_lap = current_lap
        
        # 過濾只顯示當前圈數之前的訊息
        visible_messages = [
            msg for msg in self._all_messages 
            if msg.get('Lap', 0) <= current_lap
        ]
        
        # 按圈數倒序排列（最新的在上面）
        visible_messages = sorted(visible_messages, key=lambda m: m.get('Lap', 0), reverse=True)
        
        # 限制顯示數量
        visible_messages = visible_messages[:20]
        
        self.message_list.setRowCount(len(visible_messages))
        
        for row, msg in enumerate(visible_messages):
            lap = msg.get('Lap', '?')
            category = msg.get('Category', '?')
            flag = msg.get('Flag', '')
            message = msg.get('Message', '')
            
            # 類型欄位 (使用 Flag 或 Category)
            type_text = flag if flag else category
            
            # 設置圈數
            lap_item = QTableWidgetItem(str(lap))
            lap_item.setTextAlignment(Qt.AlignCenter)
            self.message_list.setItem(row, 0, lap_item)
            
            # 設置類型（帶顏色）
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignCenter)
            
            # 根據類型設置顏色
            if flag == 'GREEN':
                type_item.setBackground(QColor('#00FF00'))
                type_item.setForeground(QColor('#000000'))
            elif flag == 'YELLOW':
                type_item.setBackground(QColor('#FFFF00'))
                type_item.setForeground(QColor('#000000'))
            elif flag == 'RED':
                type_item.setBackground(QColor('#FF0000'))
                type_item.setForeground(QColor('#FFFFFF'))
            elif flag == 'BLUE':
                type_item.setBackground(QColor('#0000FF'))
                type_item.setForeground(QColor('#FFFFFF'))
            elif flag == 'CHEQUERED':
                type_item.setBackground(QColor('#000000'))
                type_item.setForeground(QColor('#FFFFFF'))
            
            self.message_list.setItem(row, 1, type_item)
            
            # 設置訊息
            msg_item = QTableWidgetItem(message)
            self.message_list.setItem(row, 2, msg_item)


class PitStopTableWidget(QWidget):
    """
    PIT 進站統計表 (動態版本)
    
    根據當前時間點動態顯示：
    - 車手
    - 進站次數 (到當前時間為止)
    - 各次進站圈數
    - 各次更換的輪胎 (到當前時間為止)
    - 當前輪胎
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._pit_events: List[Dict[str, Any]] = []
        self._driver_stints: Dict[str, List[Dict[str, Any]]] = {}
        self._driver_info: Dict[str, Dict[str, str]] = {}
        self._current_timestamp: str = ''  # 當前時間戳
        self._current_lap: int = 0  # 當前圈數 (用於過濾)
        self._current_tyre_state: Dict[str, Dict[str, Any]] = {}  # 當前輪胎狀態
        self._driver_positions: Dict[str, int] = {}  # 車手排名 (用於排序)
        self._pit_lane_times: Dict[str, List[Dict[str, Any]]] = {}  # 維修站時間 {driver: [{lap, duration, timestamp}]}
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 標題
        title = QLabel("PIT 進站統計")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "車手", "進站", "進站圈數", "PIT耗時", "輪胎策略", "當前"
        ])
        
        # 設置表格屬性
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 欄位寬度
        self.table.setColumnWidth(0, 40)   # 車手
        self.table.setColumnWidth(1, 65)   # 進站次數
        self.table.setColumnWidth(2, 65)   # 進站圈數
        self.table.setColumnWidth(3, 65)   # PIT耗時
        self.table.setColumnWidth(4, 95)   # 輪胎策略
        self.table.setColumnWidth(5, 30)   # 當前輪胎
        
        # 表頭設置 - 不自動伸展最後一欄，但允許用戶拖曳調整
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)  # 關閉自動伸展
        header.setSectionResizeMode(QHeaderView.Interactive)  # 允許用戶調整寬度
        
        layout.addWidget(self.table)
    
    def set_driver_info(self, driver_info: Dict[str, Dict[str, str]]):
        """設置車手資訊"""
        self._driver_info = driver_info
    
    def set_pit_data(self, pit_events: List[Dict[str, Any]], driver_stints: Dict[str, List[Dict[str, Any]]]):
        """設置 PIT 事件資料 (全量資料，用於進站圈數過濾)"""
        self._pit_events = pit_events
        self._driver_stints = driver_stints  # 備用，主要用即時狀態
        # 不立即更新顯示，等待 update_for_time 調用
    
    def set_pit_lane_times(self, pit_lane_times: List[Dict[str, Any]]):
        """設置維修站時間資料"""
        # 按車手分組
        self._pit_lane_times = {}
        for record in pit_lane_times:
            data = record.get('data', {})
            timestamp = record.get('timestamp', '')
            pit_times = data.get('PitTimes', {})
            for driver_num, pit_info in pit_times.items():
                # 跳過 _deleted 欄位
                if driver_num == '_deleted':
                    continue
                # 確認 pit_info 是字典
                if not isinstance(pit_info, dict):
                    continue
                    
                if driver_num not in self._pit_lane_times:
                    self._pit_lane_times[driver_num] = []
                
                # 取得圈數和時間
                lap_str = pit_info.get('Lap', '0')
                duration_str = pit_info.get('Duration', '?')
                
                try:
                    lap_val = int(lap_str)
                except (ValueError, TypeError):
                    lap_val = 0
                
                self._pit_lane_times[driver_num].append({
                    'lap': lap_val,
                    'duration': duration_str,
                    'timestamp': timestamp
                })
    
    def update_for_time(self, timestamp: str, current_lap: int, driver_laps: Dict[str, int], 
                        tyre_state: Dict[str, Dict[str, Any]] = None,
                        driver_positions: Dict[str, int] = None):
        """
        根據當前時間更新 PIT 統計 (使用 Live F1 即時數據)
        
        Args:
            timestamp: 當前時間戳
            current_lap: 領先車手的當前圈數
            driver_laps: 每位車手的當前圈數 {driver_num: lap}
            tyre_state: 即時輪胎狀態 {driver_num: {compound, new, stint_count, stints}}
            driver_positions: 車手排名 {driver_num: position} (用於排序)
        """
        self._current_timestamp = timestamp
        self._current_lap = current_lap
        self._current_tyre_state = tyre_state or {}
        self._driver_positions = driver_positions or {}
        self._update_display(timestamp, driver_laps)
    
    def _update_display(self, current_timestamp: str = '', driver_laps: Dict[str, int] = None):
        """更新顯示 - 使用 Live F1 即時數據"""
        if driver_laps is None:
            driver_laps = {}
        
        # 按車手分組進站事件 - 只包含當前圈數之前的事件
        driver_pits = {}  # driver -> [lap1, lap2, ...]
        for event in self._pit_events:
            if event['type'] == 'PIT_IN':
                driver = event['driver']
                event_lap = event.get('lap', 0)
                
                # 過濾：只顯示進站圈數 <= 車手當前圈數的事件
                driver_current_lap = driver_laps.get(driver, 0)
                if event_lap > driver_current_lap:
                    continue  # 這個進站還沒發生
                    
                if driver not in driver_pits:
                    driver_pits[driver] = []
                driver_pits[driver].append(event_lap)
        
        # 只顯示當前有圈數的車手（即正在比賽的車手）
        all_drivers = set(driver_laps.keys())
        
        self.table.setRowCount(len(all_drivers))
        
        # 按當前排名順序排列（如果有排名資訊），否則按車號排序
        def sort_key(driver_num):
            if self._driver_positions and driver_num in self._driver_positions:
                return self._driver_positions[driver_num]
            # 沒有排名時按車號排序
            return 999 + (int(driver_num) if driver_num.isdigit() else 0)
        
        for row, driver_num in enumerate(sorted(all_drivers, key=sort_key)):
            # 車手名稱
            driver_name = driver_num
            if driver_num in self._driver_info:
                driver_name = self._driver_info[driver_num].get('tla', driver_num)
            
            driver_item = QTableWidgetItem(driver_name)
            driver_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, driver_item)
            
            # 進站次數 (到當前圈數為止)
            pit_laps = driver_pits.get(driver_num, [])
            pit_count = len(pit_laps)
            count_item = QTableWidgetItem(str(pit_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, count_item)
            
            # 進站圈數
            laps_text = ", ".join(str(lap) for lap in pit_laps) if pit_laps else "-"
            laps_item = QTableWidgetItem(laps_text)
            laps_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, laps_item)
            
            # PIT 耗時 - 從 PitLaneTimeCollection 取得
            pit_times = self._pit_lane_times.get(driver_num, [])
            # 過濾：只顯示當前圈數之前的維修站時間
            driver_current_lap = driver_laps.get(driver_num, 0)
            valid_pit_times = [pt for pt in pit_times if pt.get('lap', 0) <= driver_current_lap]
            
            if valid_pit_times:
                # 顯示所有進站耗時
                durations = [f"{pt.get('duration', '?')}s" for pt in valid_pit_times]
                pit_time_text = ", ".join(durations)
            else:
                pit_time_text = "-"
            
            pit_time_item = QTableWidgetItem(pit_time_text)
            pit_time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, pit_time_item)
            
            # 輪胎策略 - 使用即時輪胎狀態 (來自 Live F1)
            # 使用 TyreStrategyWidget 顯示帶顏色的輪胎
            tyre_info = self._current_tyre_state.get(driver_num, {})
            stints = tyre_info.get('stints', [])
            current_tyre = "?"
            current_compound = "UNKNOWN"
            
            # 找出當前輪胎（最後一個 stint）
            if stints:
                last_stint = stints[-1]
                current_compound = last_stint.get('compound', 'UNKNOWN')
                current_tyre = TYRE_ABBREV.get(current_compound, '?')
            
            # 建立輪胎策略 widget
            strategy_widget = TyreStrategyWidget()
            strategy_widget.set_strategy(stints, pit_count, pit_laps)
            self.table.setCellWidget(row, 4, strategy_widget)
            
            # 當前輪胎 (使用即時狀態的最後一個輪胎)
            current_item = QTableWidgetItem(current_tyre)
            current_item.setTextAlignment(Qt.AlignCenter)
            
            # 設置輪胎顏色
            color = TYRE_COLORS.get(current_compound, TYRE_COLORS['UNKNOWN'])
            current_item.setBackground(QColor(color))
            if current_compound in ['HARD', 'MEDIUM']:
                current_item.setForeground(QColor('#000000'))
            else:
                current_item.setForeground(QColor('#FFFFFF'))
            
            font = current_item.font()
            font.setBold(True)
            current_item.setFont(font)
            self.table.setItem(row, 5, current_item)


class LiveRankingTableWidget(QWidget):
    """
    實時排名表元件
    
    顯示欄位：
    - Pos (排名)
    - +/- (名次變動：與發車位置比較)
    - No (車號)
    - Tyre (當前輪胎)
    - Driver (車手編號)
    - Last (上一圈時間)
    - Best (最佳時間)
    - Delta (與最佳差距)
    - Gap (與領先者)
    - Int (與前車間隔)
    - Lap (圈數)
    - Speed (速度)
    - RPM
    - Gear (檔位)
    - Throttle (油門)
    - Brake (煞車)
    - DRS
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._current_snapshot = None
        self._grid_positions: Dict[str, int] = {}  # 發車位置記錄
        self._grid_initialized = False
        self._driver_stints: Dict[str, List[Dict[str, Any]]] = {}  # 輪胎策略
        self._pit_events: List[Dict[str, Any]] = []  # PIT 事件列表
        self._current_tyre_state: Dict[str, Dict[str, Any]] = {}  # 即時輪胎狀態 (來自 Live F1)
        self._current_car_data: Dict[str, Dict[str, Any]] = {}  # 車輛遙測資料
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 標題
        title = QLabel("實時車手排名")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 表格 (新增 S1/S2/S3 和 P1%/P2%/P3% 欄位)
        self.table = QTableWidget()
        self.table.setColumnCount(23)  # 原 17 + S1/S2/S3 + P1%/P2%/P3%
        self.table.setHorizontalHeaderLabels([
            "P", "+/-", "No", "胎", "車手", "S1", "S2", "S3", "上圈", "最佳", "差距", "領先", "前車", "圈",
            "P1%", "P2%", "P3%",  # 勝率欄位
            "SPD", "RPM", "G", "THR", "BRK", "DRS"
        ])
        
        # 啟用排序功能
        self.table.setSortingEnabled(True)
        
        # 設置表格屬性
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 欄位寬度
        self.table.setColumnWidth(0, 25)   # P (排名)
        self.table.setColumnWidth(1, 30)   # +/-
        self.table.setColumnWidth(2, 28)   # No (車號)
        self.table.setColumnWidth(3, 25)   # 胎 (輪胎)
        self.table.setColumnWidth(4, 45)   # 車手
        self.table.setColumnWidth(5, 55)   # S1
        self.table.setColumnWidth(6, 55)   # S2
        self.table.setColumnWidth(7, 55)   # S3
        self.table.setColumnWidth(8, 70)   # 上圈
        self.table.setColumnWidth(9, 70)   # 最佳
        self.table.setColumnWidth(10, 65)  # 差距
        self.table.setColumnWidth(11, 70)  # 領先
        self.table.setColumnWidth(12, 60)  # 前車
        self.table.setColumnWidth(13, 30)  # 圈數
        self.table.setColumnWidth(14, 40)  # P1% (勝率)
        self.table.setColumnWidth(15, 40)  # P2% (亞軍機率)
        self.table.setColumnWidth(16, 40)  # P3% (頒獎台機率)
        self.table.setColumnWidth(17, 40)  # 速度
        self.table.setColumnWidth(18, 50)  # RPM
        self.table.setColumnWidth(19, 22)  # 檔位
        self.table.setColumnWidth(20, 40)  # 油門
        self.table.setColumnWidth(21, 40)  # 煞車
        self.table.setColumnWidth(22, 30)  # DRS
        
        # 表頭設置 - 使用固定寬度以提升效能
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)  # 最後一欄自動填滿
        
        layout.addWidget(self.table)
    
    def set_driver_stints(self, driver_stints: Dict[str, List[Dict[str, Any]]]):
        """設置車手輪胎策略 (備用)"""
        self._driver_stints = driver_stints
    
    def set_car_data(self, car_data: Dict[str, Dict[str, Any]]):
        """設置車輛遙測資料"""
        self._current_car_data = car_data
    
    def set_pit_events(self, pit_events: List[Dict[str, Any]]):
        """設置 PIT 事件列表"""
        self._pit_events = pit_events
    
    def set_tyre_state(self, tyre_state: Dict[str, Dict[str, Any]]):
        """設置即時輪胎狀態 (來自 Live F1)"""
        self._current_tyre_state = tyre_state
    
    def update_display(self, snapshot: Dict, tyre_state: Dict[str, Dict[str, Any]] = None):
        """
        更新顯示 - 使用 Live F1 即時數據
        
        Args:
            snapshot: 當前時間快照
            tyre_state: 即時輪胎狀態 {driver_num: {compound, new, stint_count, stints}}
        """
        self._current_snapshot = snapshot
        self._current_tyre_state = tyre_state or getattr(self, '_current_tyre_state', {})
        drivers = snapshot['drivers']
        
        # 第一次更新時，記錄發車位置（grid position）
        if not self._grid_initialized:
            for driver_num, driver_data in drivers.items():
                pos = driver_data.get('position')
                if pos is not None:
                    self._grid_positions[driver_num] = pos
            self._grid_initialized = True
        
        # 按排名排序（排名 1 永遠在最上面，排名 20 永遠在最下面）
        sorted_drivers = sorted(
            drivers.items(),
            key=lambda x: x[1].get('position', 999)
        )
        
        # 暫時禁用排序功能以保持排名順序
        self.table.setSortingEnabled(False)
        
        # 更新表格（顯示全部車手）
        self.table.setRowCount(len(sorted_drivers))
        
        for row, (driver_num, driver_data) in enumerate(sorted_drivers):
            # P - 排名 (欄位 0)
            pos_item = QTableWidgetItem(str(driver_data.get('position', 'N/A')))
            pos_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, pos_item)
            
            # +/- 名次變動 (欄位 1)
            current_pos = driver_data.get('position')
            grid_pos = self._grid_positions.get(driver_num)
            
            if current_pos is not None and grid_pos is not None:
                change = grid_pos - current_pos  # 正數=進步，負數=退步
                if change > 0:
                    change_text = f"+{change}"
                    change_color = QColor(50, 180, 50)  # 綠色 - 進步
                elif change < 0:
                    change_text = f"{change}"
                    change_color = QColor(220, 50, 50)  # 紅色 - 退步
                else:
                    change_text = "—"
                    change_color = QColor(150, 150, 150)  # 灰色 - 不變
            else:
                change_text = "—"
                change_color = QColor(150, 150, 150)
            
            change_item = QTableWidgetItem(change_text)
            change_item.setTextAlignment(Qt.AlignCenter)
            change_item.setForeground(change_color)
            font = change_item.font()
            font.setBold(True)
            change_item.setFont(font)
            self.table.setItem(row, 1, change_item)
            
            # 胎 - 輪胎 (欄位 3) - 使用 Live F1 即時輪胎狀態
            tyre_info = self._current_tyre_state.get(driver_num, {})
            compound = tyre_info.get('compound', 'UNKNOWN')
            tyre_abbrev = TYRE_ABBREV.get(compound, '?')
            tyre_color = TYRE_COLORS.get(compound, TYRE_COLORS['UNKNOWN'])
            
            tyre_item = QTableWidgetItem(tyre_abbrev)
            tyre_item.setTextAlignment(Qt.AlignCenter)
            tyre_item.setBackground(QColor(tyre_color))
            # 設置文字顏色
            if compound in ['HARD', 'MEDIUM']:
                tyre_item.setForeground(QColor('#000000'))
            else:
                tyre_item.setForeground(QColor('#FFFFFF'))
            tyre_font = tyre_item.font()
            tyre_font.setBold(True)
            tyre_item.setFont(tyre_font)
            self.table.setItem(row, 3, tyre_item)
            
            # No - 車號 (欄位 2)
            num_item = QTableWidgetItem(driver_num)
            num_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, num_item)
            
            # 車手 (欄位 4)
            driver_display = driver_data.get('driver_tla', driver_num)
            driver_item = QTableWidgetItem(driver_display)
            driver_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, driver_item)
            
            # === Sector 時間 (欄位 5-7) ===
            # S1 (欄位 5)
            s1_time = driver_data.get('s1_time', '')
            s1_personal = driver_data.get('s1_personal_fastest', False)
            s1_overall = driver_data.get('s1_overall_fastest', False)
            s1_item = QTableWidgetItem(s1_time if s1_time else '')
            s1_item.setTextAlignment(Qt.AlignCenter)
            if s1_overall:
                s1_item.setBackground(QColor('#FF00FF'))  # 紫色底 - 全場最快
                s1_item.setForeground(QColor('#000000'))
                s1_font = s1_item.font()
                s1_font.setBold(True)
                s1_item.setFont(s1_font)
            elif s1_personal:
                s1_item.setBackground(QColor('#00FF00'))  # 綠色底 - 個人最快
                s1_item.setForeground(QColor('#000000'))
                s1_font = s1_item.font()
                s1_font.setBold(True)
                s1_item.setFont(s1_font)
            self.table.setItem(row, 5, s1_item)
            
            # S2 (欄位 6)
            s2_time = driver_data.get('s2_time', '')
            s2_personal = driver_data.get('s2_personal_fastest', False)
            s2_overall = driver_data.get('s2_overall_fastest', False)
            s2_item = QTableWidgetItem(s2_time if s2_time else '')
            s2_item.setTextAlignment(Qt.AlignCenter)
            if s2_overall:
                s2_item.setBackground(QColor('#FF00FF'))  # 紫色底 - 全場最快
                s2_item.setForeground(QColor('#000000'))
                s2_font = s2_item.font()
                s2_font.setBold(True)
                s2_item.setFont(s2_font)
            elif s2_personal:
                s2_item.setBackground(QColor('#00FF00'))  # 綠色底 - 個人最快
                s2_item.setForeground(QColor('#000000'))
                s2_font = s2_item.font()
                s2_font.setBold(True)
                s2_item.setFont(s2_font)
            self.table.setItem(row, 6, s2_item)
            
            # S3 (欄位 7)
            s3_time = driver_data.get('s3_time', '')
            s3_personal = driver_data.get('s3_personal_fastest', False)
            s3_overall = driver_data.get('s3_overall_fastest', False)
            s3_item = QTableWidgetItem(s3_time if s3_time else '')
            s3_item.setTextAlignment(Qt.AlignCenter)
            if s3_overall:
                s3_item.setBackground(QColor('#FF00FF'))  # 紫色底 - 全場最快
                s3_item.setForeground(QColor('#000000'))
                s3_font = s3_item.font()
                s3_font.setBold(True)
                s3_item.setFont(s3_font)
            elif s3_personal:
                s3_item.setBackground(QColor('#00FF00'))  # 綠色底 - 個人最快
                s3_item.setForeground(QColor('#000000'))
                s3_font = s3_item.font()
                s3_font.setBold(True)
                s3_item.setFont(s3_font)
            self.table.setItem(row, 7, s3_item)
            
            # 上圈 - Last Lap Time (欄位 8)
            last_lap_time = driver_data.get('last_lap_time', '')
            last_lap_personal = driver_data.get('last_lap_personal_fastest', False)
            last_lap_overall = driver_data.get('last_lap_overall_fastest', False)
            
            last_lap_item = QTableWidgetItem(last_lap_time if last_lap_time else '')
            last_lap_item.setTextAlignment(Qt.AlignCenter)
            
            # 圈時顏色編碼 (黑字+底色)
            if last_lap_overall:
                last_lap_item.setBackground(QColor('#FF00FF'))  # 紫色底 - 全場最快
                last_lap_item.setForeground(QColor('#000000'))  # 黑字
                last_lap_font = last_lap_item.font()
                last_lap_font.setBold(True)
                last_lap_item.setFont(last_lap_font)
            elif last_lap_personal:
                last_lap_item.setBackground(QColor('#00FF00'))  # 綠色底 - 個人最快
                last_lap_item.setForeground(QColor('#000000'))  # 黑字
                last_lap_font = last_lap_item.font()
                last_lap_font.setBold(True)
                last_lap_item.setFont(last_lap_font)
            
            self.table.setItem(row, 8, last_lap_item)
            
            # 最佳 - Best Lap Time (欄位 9)
            best_lap_time = driver_data.get('best_lap_time', '')
            best_lap_item = QTableWidgetItem(best_lap_time if best_lap_time else '')
            best_lap_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 9, best_lap_item)
            
            # 差距 - Delta (Last - Best) (欄位 10)
            delta_text = ''
            if last_lap_time and best_lap_time:
                try:
                    last_secs = self._parse_lap_time(last_lap_time)
                    best_secs = self._parse_lap_time(best_lap_time)
                    if last_secs is not None and best_secs is not None:
                        delta = last_secs - best_secs
                        if delta > 0:
                            delta_text = f"+{delta:.3f}"
                        elif delta < 0:
                            delta_text = f"{delta:.3f}"
                        else:
                            delta_text = "0.000"
                except:
                    pass
            
            delta_item = QTableWidgetItem(delta_text)
            delta_item.setTextAlignment(Qt.AlignCenter)
            
            # 差距顏色：正數黃底，0綠底 (黑字)
            if delta_text.startswith('+') and delta_text != '+0.000':
                delta_item.setBackground(QColor('#FFAA00'))  # 橙黃底
                delta_item.setForeground(QColor('#000000'))  # 黑字
            elif delta_text == '0.000':
                delta_item.setBackground(QColor('#00FF00'))  # 綠底 - 正好是最佳圈
                delta_item.setForeground(QColor('#000000'))  # 黑字
            
            self.table.setItem(row, 10, delta_item)
            
            # 領先 - Gap to Leader (欄位 11)
            gap_leader_text = driver_data.get('gap_to_leader_display')
            if not gap_leader_text:
                gap_leader_text = "" if driver_data.get('position') == 1 else ""
            gap_leader_item = QTableWidgetItem(gap_leader_text)
            gap_leader_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 11, gap_leader_item)
            
            # 前車 - Gap to Ahead (欄位 12)
            gap_ahead_text = driver_data.get('gap_to_ahead_display')
            if not gap_ahead_text:
                gap_ahead_text = "" if driver_data.get('position') == 1 else ""
            gap_ahead_item = QTableWidgetItem(gap_ahead_text)
            gap_ahead_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 12, gap_ahead_item)
            
            # 圈 - 圈數 (欄位 13)
            lap_item = QTableWidgetItem(str(driver_data.get('lap') or ''))
            lap_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 13, lap_item)
            
            # === 勝率欄位 (欄位 14-16) ===
            win_prob = driver_data.get('win_probability', '')
            p2_prob = driver_data.get('p2_probability', '')
            p3_prob = driver_data.get('p3_probability', '')
            
            # P1% (欄位 14)
            if isinstance(win_prob, (int, float)):
                win_text = f"{int(round(win_prob))}%"  # 不顯示小數點
            else:
                win_text = str(win_prob) if win_prob else '-'
            win_item = QTableWidgetItem(win_text)
            win_item.setTextAlignment(Qt.AlignCenter)
            win_item.setForeground(QColor('#000000'))  # 黑色字體
            # P1% 底色編碼
            if isinstance(win_prob, (int, float)):
                if win_prob >= 50:
                    win_item.setBackground(QColor('#00FF00'))  # 綠色底
                elif win_prob >= 20:
                    win_item.setBackground(QColor('#FFFF00'))  # 黃色底
                elif win_prob >= 5:
                    win_item.setBackground(QColor('#FFA500'))  # 橙色底
                # 低於 5% 不設底色
            self.table.setItem(row, 14, win_item)
            
            # P2% (欄位 15)
            if isinstance(p2_prob, (int, float)):
                p2_text = f"{int(round(p2_prob))}%"  # 不顯示小數點
            else:
                p2_text = str(p2_prob) if p2_prob else '-'
            p2_item = QTableWidgetItem(p2_text)
            p2_item.setTextAlignment(Qt.AlignCenter)
            p2_item.setForeground(QColor('#000000'))  # 黑色字體
            # P2% 底色編碼
            if isinstance(p2_prob, (int, float)):
                if p2_prob >= 70:
                    p2_item.setBackground(QColor('#00FF00'))  # 綠色底
                elif p2_prob >= 40:
                    p2_item.setBackground(QColor('#FFFF00'))  # 黃色底
                elif p2_prob >= 15:
                    p2_item.setBackground(QColor('#FFA500'))  # 橙色底
                # 低於 15% 不設底色
            self.table.setItem(row, 15, p2_item)
            
            # P3% (欄位 16)
            if isinstance(p3_prob, (int, float)):
                p3_text = f"{int(round(p3_prob))}%"  # 不顯示小數點
            else:
                p3_text = str(p3_prob) if p3_prob else '-'
            p3_item = QTableWidgetItem(p3_text)
            p3_item.setTextAlignment(Qt.AlignCenter)
            p3_item.setForeground(QColor('#000000'))  # 黑色字體
            # P3% 底色編碼
            if isinstance(p3_prob, (int, float)):
                if p3_prob >= 80:
                    p3_item.setBackground(QColor('#00FF00'))  # 綠色底
                elif p3_prob >= 50:
                    p3_item.setBackground(QColor('#FFFF00'))  # 黃色底
                elif p3_prob >= 20:
                    p3_item.setBackground(QColor('#FFA500'))  # 橙色底
                # 低於 20% 不設底色
            self.table.setItem(row, 16, p3_item)
            
            # === 遙測資料 (欄位 17-22) ===
            car_data = self._current_car_data.get(driver_num, {})
            
            # Speed (欄位 17)
            speed = car_data.get('speed', '')
            speed_item = QTableWidgetItem(str(speed) if speed else '')
            speed_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 17, speed_item)
            
            # RPM (欄位 18)
            rpm = car_data.get('rpm', '')
            rpm_item = QTableWidgetItem(str(rpm) if rpm else '')
            rpm_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 18, rpm_item)
            
            # Gear (欄位 19)
            gear = car_data.get('gear', '')
            gear_item = QTableWidgetItem(str(gear) if gear else '')
            gear_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 19, gear_item)
            
            # Throttle (欄位 20)
            throttle = car_data.get('throttle', '')
            throttle_item = QTableWidgetItem(str(throttle) if throttle else '')
            throttle_item.setTextAlignment(Qt.AlignCenter)
            # 油門顏色：高油門綠色
            if throttle and int(throttle) > 80:
                throttle_item.setForeground(QColor('#00FF00'))
            self.table.setItem(row, 20, throttle_item)
            
            # Brake (欄位 21)
            brake = car_data.get('brake', '')
            brake_item = QTableWidgetItem(str(brake) if brake else '')
            brake_item.setTextAlignment(Qt.AlignCenter)
            # 煞車顏色：煞車中紅色
            if brake and int(brake) > 0:
                brake_item.setForeground(QColor('#FF0000'))
                brake_font = brake_item.font()
                brake_font.setBold(True)
                brake_item.setFont(brake_font)
            self.table.setItem(row, 21, brake_item)
            
            # DRS (欄位 22)
            drs = car_data.get('drs', '')
            drs_text = ''
            if drs:
                drs_val = int(drs)
                if drs_val >= 10:
                    drs_text = 'ON'
                elif drs_val > 0:
                    drs_text = 'RDY'
            drs_item = QTableWidgetItem(drs_text)
            drs_item.setTextAlignment(Qt.AlignCenter)
            if drs_text == 'ON':
                drs_item.setBackground(QColor('#00FF00'))  # 綠色背景
                drs_item.setForeground(QColor('#000000'))  # 黑色字體
                drs_font = drs_item.font()
                drs_font.setBold(True)
                drs_item.setFont(drs_font)
            elif drs_text == 'RDY':
                drs_item.setBackground(QColor('#FFFF00'))  # 黃色背景
                drs_item.setForeground(QColor('#000000'))  # 黑色字體
            self.table.setItem(row, 22, drs_item)
    
    def _parse_lap_time(self, lap_time_str: str) -> Optional[float]:
        """解析圈時字串為秒數 (例如 '1:33.943' -> 93.943)"""
        if not lap_time_str:
            return None
        try:
            if ':' in lap_time_str:
                parts = lap_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(lap_time_str)
        except (ValueError, IndexError):
            return None


class TimelineControlWidget(QWidget):
    """
    時間軸控制器
    
    功能：
    - 播放/暫停
    - 拖動時間軸
    - 速度控制（1x/2x/4x/8x）
    """
    
    time_changed = pyqtSignal(int)  # 發送當前索引
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._snapshots = []
        self._current_index = 0
        self._is_playing = False
        self._playback_speed = 1.0
        
        # 定時器
        self._timer = QTimer()
        self._timer.timeout.connect(self._advance_frame)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 時間顯示
        time_layout = QHBoxLayout()
        self.lbl_time = QLabel("比賽時間: 00:00:00.000")
        time_font = QFont()
        time_font.setPointSize(11)
        time_font.setBold(True)
        self.lbl_time.setFont(time_font)
        time_layout.addWidget(self.lbl_time)
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        # 時間軸
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)
        
        # 控制按鈕
        control_layout = QHBoxLayout()
        
        self.btn_play = QPushButton("▶️ 播放")
        self.btn_play.clicked.connect(self._on_play_clicked)
        control_layout.addWidget(self.btn_play)
        
        self.btn_pause = QPushButton("⏸️ 暫停")
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        self.btn_pause.setEnabled(False)
        control_layout.addWidget(self.btn_pause)
        
        # 速度選擇
        control_layout.addWidget(QLabel("速度:"))
        self.cmb_speed = QComboBox()
        self.cmb_speed.addItems(["1x", "2x", "4x", "8x", "16x", "32x", "64x"])
        self.cmb_speed.currentTextChanged.connect(self._on_speed_changed)
        control_layout.addWidget(self.cmb_speed)
        
        control_layout.addStretch()
        
        # 進度顯示
        self.lbl_progress = QLabel("0 / 0")
        control_layout.addWidget(self.lbl_progress)
        
        layout.addLayout(control_layout)
    
    def set_snapshots(self, snapshots: List[Dict]):
        """設置數據源"""
        self._snapshots = snapshots
        maximum = max(0, len(snapshots) - 1)
        self.slider.setMaximum(maximum)
        if maximum == 0:
            self.slider.setValue(0)
        self._update_display()
    
    def _advance_frame(self):
        """前進到下一幀"""
        if self._current_index < len(self._snapshots) - 1:
            self._current_index += 1
            self.slider.setValue(self._current_index)
        else:
            self._on_pause_clicked()  # 播放完畢
    
    def _on_slider_changed(self, value: int):
        """時間軸拖動"""
        self._current_index = value
        self._update_display()
        self.time_changed.emit(self._current_index)
    
    def _on_play_clicked(self):
        """播放"""
        self._is_playing = True
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        
        # 根據速度設置定時器間隔
        # Live F1 數據約每秒1個點，所以基礎間隔設為 1000ms
        base_interval = 1000  # 1秒
        interval = max(50, int(base_interval / self._playback_speed))
        self._timer.start(interval)
    
    def _on_pause_clicked(self):
        """暫停"""
        self._is_playing = False
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self._timer.stop()
    
    def _on_speed_changed(self, text: str):
        """速度變更"""
        speed_map = {"1x": 1.0, "2x": 2.0, "4x": 4.0, "8x": 8.0, "16x": 16.0, "32x": 32.0, "64x": 64.0}
        self._playback_speed = speed_map.get(text, 1.0)
        
        # 更新定時器間隔 (最快 30ms = 每秒 33 幀)
        if self._is_playing:
            base_interval = 1000  # 1 秒
            interval = max(30, int(base_interval / self._playback_speed))
            self._timer.start(interval)
    
    def _update_display(self):
        """更新顯示"""
        if 0 <= self._current_index < len(self._snapshots):
            snapshot = self._snapshots[self._current_index]
            self.lbl_time.setText(f"比賽時間: {snapshot['race_time']}")
            self.lbl_progress.setText(f"{self._current_index + 1} / {len(self._snapshots)}")


class LivePositionTrackingMainWindow(QMainWindow):
    """主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.setWindowTitle("F1 實時車手位置追蹤系統 - Demo")
        self.setGeometry(100, 100, 1600, 900)
        
        # 數據處理器
        self.processor = None
        self._snapshots: List[Dict[str, Any]] = []
        self._total_race_duration_seconds: float = 0.0
        self._total_laps: int = 53  # 預設圈數
        self._car_data: Dict = {}   # CarData 遙測資料
        
        # 賽事選擇
        self._available_races = scan_available_races()
        self._current_year = None
        self._current_race = None
        
        # 勝率預測器
        self._predictor = None
        if WIN_PROBABILITY_AVAILABLE:
            try:
                self._predictor = LiveWinProbabilityPredictor()
                # 模型路徑
                model_path = _root_dir / 'models' / 'win_probability_xgb_v2.pkl'
                if not self._predictor.load_model(str(model_path)):
                    print(f"[WARNING] Failed to load win probability model from: {model_path}")
                    self._predictor = None
                else:
                    print("[INFO] Win probability predictor loaded successfully")
            except Exception as e:
                print(f"[WARNING] Win probability predictor init failed: {e}")
                self._predictor = None
        
        # 初始化 UI
        self._init_ui()
        
        # 初始載入（選擇第一個可用的賽事）
        self._auto_select_first_race()
    
    def _init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 標題
        title = QLabel("F1 實時車手位置追蹤系統 - Stage 1 Demo")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # === 賽事選擇區域 ===
        race_selector_layout = QHBoxLayout()
        
        # 年份選擇
        race_selector_layout.addWidget(QLabel("年份:"))
        self.cmb_year = QComboBox()
        self.cmb_year.setMinimumWidth(80)
        years = sorted(self._available_races.keys(), reverse=True)
        self.cmb_year.addItems(years)
        self.cmb_year.currentTextChanged.connect(self._on_year_changed)
        race_selector_layout.addWidget(self.cmb_year)
        
        # 賽事選擇
        race_selector_layout.addWidget(QLabel("賽事:"))
        self.cmb_race = QComboBox()
        self.cmb_race.setMinimumWidth(200)
        race_selector_layout.addWidget(self.cmb_race)
        
        # 載入按鈕
        self.btn_load = QPushButton("載入賽事")
        self.btn_load.clicked.connect(self._on_load_race_clicked)
        race_selector_layout.addWidget(self.btn_load)
        
        # 隱藏/顯示比賽控制訊息按鈕
        self.btn_toggle_race_control = QPushButton("隱藏訊息")
        self.btn_toggle_race_control.setCheckable(True)
        self.btn_toggle_race_control.clicked.connect(self._toggle_race_control)
        race_selector_layout.addWidget(self.btn_toggle_race_control)
        
        # 賽事資訊標籤
        self.lbl_race_info = QLabel("請選擇賽事")
        self.lbl_race_info.setStyleSheet("color: #888888;")
        race_selector_layout.addWidget(self.lbl_race_info)
        
        race_selector_layout.addStretch()
        layout.addLayout(race_selector_layout)
        
        # === 頂部區域：賽事資訊面板（圈數、天氣、賽道狀態） ===
        self.race_info = RaceInfoWidget()
        layout.addWidget(self.race_info)
        
        # 創建主分割器（左：地圖+排名，右：控制訊息）
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左側分割器（地圖、排名、PIT）
        left_splitter = QSplitter(Qt.Horizontal)
        
        # 左側：賽道地圖
        map_group = QGroupBox("賽道地圖")
        map_layout = QVBoxLayout()
        self.track_map = TrackMapWidget()
        map_layout.addWidget(self.track_map)
        map_group.setLayout(map_layout)
        left_splitter.addWidget(map_group)
        
        # 中間：排名表
        table_group = QGroupBox("實時排名")
        table_layout = QVBoxLayout()
        self.ranking_table = LiveRankingTableWidget()
        table_layout.addWidget(self.ranking_table)
        table_group.setLayout(table_layout)
        left_splitter.addWidget(table_group)
        
        # 右側：PIT 進站統計
        pit_group = QGroupBox("PIT 進站統計")
        pit_layout = QVBoxLayout()
        self.pit_table = PitStopTableWidget()
        pit_layout.addWidget(self.pit_table)
        pit_group.setLayout(pit_layout)
        left_splitter.addWidget(pit_group)
        
        # 設置左側分割比例（賽道150px，車手排名810px，PIT統計360px）
        left_splitter.setSizes([150, 810, 360])
        
        main_splitter.addWidget(left_splitter)
        
        # 右側：比賽控制訊息 (可隱藏)
        self.race_control_group = QGroupBox("比賽控制訊息")
        race_control_layout = QVBoxLayout()
        self.race_control_widget = RaceControlMessagesWidget()
        race_control_layout.addWidget(self.race_control_widget)
        self.race_control_group.setLayout(race_control_layout)
        main_splitter.addWidget(self.race_control_group)
        
        # 保存 main_splitter 引用以便切換
        self.main_splitter = main_splitter
        
        # 設置主分割比例（左側，右側控制訊息）
        main_splitter.setSizes([1160, 240])
        
        # 預設隱藏比賽控制訊息
        self.race_control_group.hide()
        
        layout.addWidget(main_splitter, stretch=3)
        
        # 時間軸控制器
        self.timeline_control = TimelineControlWidget()
        self.timeline_control.time_changed.connect(self._on_time_changed)
        layout.addWidget(self.timeline_control, stretch=1)
        
        # 狀態列
        self.statusBar().showMessage("準備就緒 - 請選擇賽事並點擊「載入賽事」")
    
    def _auto_select_first_race(self):
        """自動選擇第一個可用的賽事 - 預設 2025 United States Race"""
        if not self._available_races:
            self.lbl_race_info.setText("未找到本地 LiveF1 數據，請先下載")
            self.lbl_race_info.setStyleSheet("color: #FF0000;")
            return
        
        # 預設選擇 2025 United_States_Race (用於勝率預測測試)
        default_year = "2025"
        default_race = "United_States_Race"
        
        years = sorted(self._available_races.keys(), reverse=True)
        
        # 檢查預設賽事是否存在
        if default_year in self._available_races and default_race in self._available_races[default_year]:
            self.cmb_year.setCurrentText(default_year)
            self._on_year_changed(default_year)
            # 選擇 United States Race
            for i in range(self.cmb_race.count()):
                if self.cmb_race.itemData(i) == default_race:
                    self.cmb_race.setCurrentIndex(i)
                    break
        elif years:
            # 回退：選擇最新年份的第一個賽事
            self.cmb_year.setCurrentText(years[0])
            self._on_year_changed(years[0])
            
        # 自動載入賽事
        if self.cmb_race.count() > 0:
            self._on_load_race_clicked()
    
    def _on_year_changed(self, year: str):
        """年份變更"""
        self.cmb_race.clear()
        
        if year in self._available_races:
            races = self._available_races[year]
            # 顯示更友好的賽事名稱
            for race in races:
                display_name = race.replace("_", " ")
                self.cmb_race.addItem(display_name, race)  # userData 存儲原始名稱
    
    def _toggle_race_control(self):
        """切換比賽控制訊息的顯示/隱藏"""
        if self.btn_toggle_race_control.isChecked():
            # 隱藏
            self.race_control_group.hide()
            self.btn_toggle_race_control.setText("顯示訊息")
            # 左側區塊佔滿
            self.main_splitter.setSizes([1400, 0])
        else:
            # 顯示
            self.race_control_group.show()
            self.btn_toggle_race_control.setText("隱藏訊息")
            # 恢復原始比例
            self.main_splitter.setSizes([1160, 240])
    
    def _on_load_race_clicked(self):
        """載入選中的賽事"""
        year = self.cmb_year.currentText()
        race = self.cmb_race.currentData()  # 獲取 userData (原始名稱)
        
        if not year or not race:
            QMessageBox.warning(self, "警告", "請選擇年份和賽事")
            return
        
        self._current_year = year
        self._current_race = race
        
        self._load_race_data(year, race)
    
    def _load_race_data(self, year: str, race: str):
        """載入指定賽事的數據"""
        self.statusBar().showMessage(f"正在載入 {year} {race}...")
        self.lbl_race_info.setText(f"載入中: {year} {race}")
        self.lbl_race_info.setStyleSheet("color: #FFAA00;")
        
        # 強制更新 UI
        QApplication.processEvents()
        
        try:
            # 步驟 1: 載入 FastF1 賽道輪廓數據 (如果有的話)
            track_data = self._load_fastf1_track_data(year, race)
            if track_data:
                self.track_map.load_track_outline(track_data)
                print(f"[MAIN] FastF1 賽道輪廓載入成功")
            
            # 步驟 2: 使用本地數據源載入 LiveF1 數據
            data_source = LocalLiveF1DataSource(year=int(year), race=race)
            
            if not data_source.load_all_data():
                raise Exception(f"無法載入 {year} {race} 的數據")
            
            # 步驟 3: 設置各種數據
            self._setup_race_data(data_source)
            
            # 步驟 4: 處理並對齊數據
            self.processor = LivePositionDataProcessor(data_source)
            self.processor.process_and_align_data(downsample_factor=10)
            
            # 步驟 5: 獲取快照並設置 UI
            snapshots = self.processor.get_aligned_snapshots()
            self._snapshots = snapshots
            
            if snapshots:
                # 設置時間軸
                last_snapshot = snapshots[-1]
                duration_seconds = last_snapshot.get('race_time_seconds', 0.0) or 0.0
                if duration_seconds > 0:
                    self._total_race_duration_seconds = duration_seconds
                    self.track_map.set_race_duration(duration_seconds)
                
                self.timeline_control.set_snapshots(snapshots)
                
                # 設置 PIT 和輪胎資料
                pit_events = self.processor.get_pit_events()
                driver_stints = self.processor.get_driver_stints()
                
                self.pit_table.set_driver_info(self.processor._driver_info)
                self.pit_table.set_pit_data(pit_events, driver_stints)
                
                self.ranking_table.set_driver_stints(driver_stints)
                self.ranking_table.set_pit_events(pit_events)
                
                # 顯示第一幀
                self._on_time_changed(0)
                
                # 更新 UI 狀態
                display_race = race.replace("_", " ")
                self.lbl_race_info.setText(f"{year} {display_race} | {len(snapshots)} 個時間點")
                self.lbl_race_info.setStyleSheet("color: #00FF00;")
                self.statusBar().showMessage(f"載入完成！{year} {display_race} - {len(snapshots)} 個時間點")
                
                print(f"\n[MAIN] 成功載入 {year} {race}")
                print(f"[MAIN] 時間快照: {len(snapshots)} 個")
            else:
                raise Exception("數據處理失敗，無法生成時間快照")
                
        except Exception as e:
            print(f"[MAIN] 載入失敗: {e}")
            import traceback
            traceback.print_exc()
            
            self.lbl_race_info.setText(f"載入失敗: {e}")
            self.lbl_race_info.setStyleSheet("color: #FF0000;")
            self.statusBar().showMessage(f"載入失敗: {e}")
    
    def _setup_race_data(self, data_source):
        """設置賽事相關數據"""
        # 設置圈數進度
        lap_count_data = data_source.get_lap_count()
        if lap_count_data:
            if isinstance(lap_count_data, list) and lap_count_data:
                latest_lap_count = lap_count_data[-1]
                data_part = latest_lap_count.get('data', {})
                self._total_laps = data_part.get('TotalLaps', 53)
            elif isinstance(lap_count_data, dict):
                self._total_laps = lap_count_data.get('TotalLaps', 53)
            else:
                self._total_laps = 53
            print(f"[MAIN] 圈數資料: {self._total_laps} 圈")
        
        # 設置天氣資料
        weather_data = data_source.get_weather_data()
        if weather_data:
            if isinstance(weather_data, list) and weather_data:
                latest_weather = weather_data[-1].get('data', {})
                self.race_info.update_weather(latest_weather)
            elif isinstance(weather_data, dict):
                self.race_info.update_weather(weather_data)
        
        # 設置賽道狀態
        track_status = data_source.get_track_status()
        if track_status:
            if isinstance(track_status, list) and track_status:
                latest_status = track_status[-1].get('data', {})
                status_val = latest_status.get('Status', '1')
                self.race_info.update_track_status(str(status_val) if status_val else "1")
        
        # 設置比賽控制訊息
        race_control_messages = data_source.get_race_control_messages()
        if race_control_messages:
            formatted_messages = []
            for record in race_control_messages:
                data = record.get('data', {})
                messages_raw = data.get('Messages', {})
                
                if isinstance(messages_raw, list):
                    for msg in messages_raw:
                        if isinstance(msg, dict):
                            formatted_messages.append(msg)
                elif isinstance(messages_raw, dict):
                    for key, msg in messages_raw.items():
                        if isinstance(msg, dict):
                            formatted_messages.append(msg)
            
            self.race_control_widget.set_messages(formatted_messages)
            print(f"[MAIN] 比賽控制訊息: {len(formatted_messages)} 條")
        
        # 設置維修站時間
        pit_lane_times = data_source.get_pit_lane_times()
        if pit_lane_times:
            self.pit_table.set_pit_lane_times(pit_lane_times)
        
        # 儲存 CarData
        self._car_data = data_source.get_cardata()
        if self._car_data:
            print(f"[MAIN] CarData 載入成功，共 {len(self._car_data)} 筆")
    
    def _load_fastf1_track_data(self, year: str = None, race: str = None) -> Optional[Dict]:
        """載入 FastF1 賽道數據"""
        try:
            # 嘗試根據賽事名稱找到對應的賽道數據
            if race:
                # 從 race 名稱提取賽道名稱 (例如 "Japanese_Race" -> "Japan")
                race_name = race.replace("_Race", "").replace("_", " ")
                # 完整的 LiveF1 → FastF1 名稱映射
                # LiveF1 使用形容詞 (Japanese, British)
                # FastF1 使用國家/城市名 (Japan, Great Britain)
                name_map = {
                    # 亞洲賽事
                    "Japanese": "Japan",
                    "Chinese": "China",
                    "Singapore": "Singapore",
                    "Azerbaijan": "Azerbaijan",
                    "Bahrain": "Bahrain",
                    "Saudi Arabian": "Saudi Arabia",
                    "Qatar": "Qatar",
                    "Abu Dhabi": "Abu Dhabi",
                    # 歐洲賽事
                    "British": "Great Britain",
                    "Belgian": "Belgium",
                    "Dutch": "Netherlands",
                    "Italian": "Italy",
                    "Spanish": "Spain",
                    "Hungarian": "Hungary",
                    "Austrian": "Austria",
                    "Monaco": "Monaco",
                    "Emilia Romagna": "Italy",  # 伊莫拉賽道也在義大利
                    # 美洲賽事
                    "United States": "United States",
                    "Las Vegas": "Las Vegas",
                    "Mexico City": "Mexico",
                    "São Paulo": "Brazil",
                    "Miami": "Miami",
                    "Canadian": "Canada",
                    # 大洋洲賽事
                    "Australian": "Australia",
                }
                
                track_name = name_map.get(race_name, race_name)
                print(f"[MAIN] 賽道名稱映射: '{race_name}' -> '{track_name}'")
                
                # 嘗試找到對應的 JSON 檔案，優先使用當年的數據，否則降級到其他年份
                json_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json")
                
                # 定義搜索優先級：當年 > 其他年份（2024, 2025, 2023 順序）
                years_to_try = [year]
                for fallback_year in ["2024", "2025", "2023"]:
                    if fallback_year != year:
                        years_to_try.append(fallback_year)
                
                for try_year in years_to_try:
                    json_patterns = [
                        f"track_position_analysis_{try_year}_{track_name}_R.json",
                        f"track_position_analysis_{try_year}_{race_name}_R.json",
                    ]
                    
                    for pattern in json_patterns:
                        json_file = os.path.join(json_dir, pattern)
                        if os.path.exists(json_file):
                            with open(json_file, 'r', encoding='utf-8') as f:
                                api_response = json.load(f)
                            
                            data = api_response.get('data', {})
                            track_data = {
                                'position_records': data.get('position_records', []),
                                'track_bounds': data.get('track_bounds', {}),
                                'official_corners': data.get('official_corners', {})
                            }
                            
                            if try_year != year:
                                print(f"[MAIN] 使用 {try_year} 年賽道數據 (原 {year} 年無數據)")
                            print(f"[MAIN] 賽道數據: {len(track_data['position_records'])} 個位置點")
                            return track_data
            
            print(f"[MAIN] 未找到 {year} {race} 的賽道數據 (已嘗試所有年份)")
            return None
            
        except Exception as e:
            print(f"[MAIN] 載入 FastF1 賽道數據失敗: {e}")
            return None
    
    @pyqtSlot(int)
    def _on_time_changed(self, index: int):
        """時間變更"""
        if not self._snapshots:
            return

        total_frames = len(self._snapshots)
        if total_frames == 0:
            return

        clamped_index = max(0, min(index, total_frames - 1))
        snapshot = self._snapshots[clamped_index]

        # 獲取當前時間點的輪胎狀態 (來自 Live F1)
        # 注意: snapshot 使用 'race_time' 欄位儲存時間戳
        current_timestamp = snapshot.get('race_time', '')
        tyre_state = self.processor.get_tyre_state_at_time(current_timestamp) if hasattr(self, 'processor') else {}

        # 計算當前圈數
        current_lap = 0
        driver_laps = {}
        driver_positions = {}  # 車手排名 {driver_num: position}
        for driver_num, driver_data in snapshot.get('drivers', {}).items():
            lap = driver_data.get('lap', 0) or 0
            driver_laps[driver_num] = lap
            if lap > current_lap:
                current_lap = lap
            # 取得車手排名
            position = driver_data.get('position')
            if position is not None:
                try:
                    driver_positions[driver_num] = int(position)
                except (ValueError, TypeError):
                    pass
        
        # === 更新賽事資訊面板 ===
        # 更新圈數進度
        if hasattr(self, '_total_laps'):
            self.race_info.update_lap(current_lap, self._total_laps)
        
        # 更新比賽控制訊息 - 顯示到當前圈數的訊息
        if hasattr(self, 'race_control_widget'):
            self.race_control_widget.update_for_lap(current_lap)
        
        # === 準備遙測資料 ===
        car_data_for_display = {}
        if hasattr(self, '_car_data') and self._car_data:
            # 從 CarData 中提取當前時間點的遙測資料
            car_data_for_display = self._extract_car_data_for_timestamp(current_timestamp)
        
        # 設置遙測資料到排名表
        self.ranking_table.set_car_data(car_data_for_display)
        
        # === 計算勝率預測 (只在圈數變化時計算，避免效能問題) ===
        last_prediction_lap = getattr(self, '_last_prediction_lap', -1)
        
        # 只在圈數變化且有預測器時才計算
        should_predict = (self._predictor is not None and 
                         current_lap > 0 and 
                         current_lap != last_prediction_lap)
        
        if should_predict:
            try:
                # 構建比賽資訊
                race_info = {
                    'total_laps': self._total_laps,
                    'current_lap': current_lap,
                    'track_status': 'GREEN'
                }
                
                # 構建輪胎狀態格式
                tyre_state_for_predictor = {}
                for driver_num, tyre_info in tyre_state.items():
                    tyre_state_for_predictor[driver_num] = {
                        'compound': tyre_info.get('compound', 'MEDIUM'),
                        'tyre_age': tyre_info.get('tyre_age', 0),
                        'stint_count': tyre_info.get('stint_count', 1)
                    }
                
                # 構建預測器所需的快照格式（轉換欄位名稱）
                predictor_snapshot = self._build_predictor_snapshot(
                    snapshot, tyre_state, current_lap, driver_laps
                )
                
                # 獲取勝率預測
                predictions = self._predictor.predict_for_snapshot(
                    predictor_snapshot, tyre_state_for_predictor, race_info
                )
                
                # 緩存預測結果
                self._cached_predictions = predictions
                self._last_prediction_lap = current_lap
                
            except Exception as e:
                print(f"[WARNING] Win probability prediction failed: {e}")
        
        # 使用緩存的預測結果更新 snapshot
        cached_predictions = getattr(self, '_cached_predictions', {})
        if cached_predictions:
            for driver_num, probs in cached_predictions.items():
                if driver_num in snapshot['drivers']:
                    snapshot['drivers'][driver_num]['win_probability'] = probs.get('win_prob', 0) * 100
                    snapshot['drivers'][driver_num]['p2_probability'] = probs.get('p2_prob', 0) * 100
                    snapshot['drivers'][driver_num]['p3_probability'] = probs.get('podium_prob', 0) * 100

        # 更新排名表 (傳遞即時輪胎狀態)
        self.ranking_table.update_display(snapshot, tyre_state)
        
        # 更新 PIT 統計表 - 動態顯示到當前時間為止的 PIT 事件
        self.pit_table.update_for_time(current_timestamp, current_lap, driver_laps, tyre_state, driver_positions)

        race_time_seconds = snapshot.get('race_time_seconds', 0.0) or 0.0
        if race_time_seconds > self._total_race_duration_seconds:
            self._total_race_duration_seconds = race_time_seconds
            self.track_map.set_race_duration(race_time_seconds)

        # 更新賽道地圖（提供時間軸資訊以估算距離）
        self.track_map.update_driver_positions(
            snapshot['drivers'],
            frame_index=clamped_index,
            total_frames=total_frames,
            race_time_seconds=race_time_seconds,
        )
    
    def _build_predictor_snapshot(self, snapshot: Dict, tyre_state: Dict, current_lap: int, driver_laps: Dict) -> Dict:
        """
        構建預測器所需的快照格式
        
        Args:
            snapshot: 原始時間快照
            tyre_state: 輪胎狀態
            current_lap: 當前圈數
            driver_laps: 各車手圈數
            
        Returns:
            預測器格式的快照
        """
        predictor_snapshot = {
            'current_lap': current_lap,
            'total_laps': self._total_laps,
            'laps_remaining': max(0, self._total_laps - current_lap),
            'track_status': 1,  # 1=綠旗，預設為正常比賽狀態
            'drivers': {}
        }
        
        # 獲取領先者的圈時作為基準
        leader_lap_time = None
        for driver_num, driver_data in snapshot.get('drivers', {}).items():
            if driver_data.get('position') == 1:
                last_lap = driver_data.get('last_lap_time')
                if last_lap:
                    leader_lap_time = self._parse_lap_time_to_seconds(last_lap)
                break
        
        for driver_num, driver_data in snapshot.get('drivers', {}).items():
            position = driver_data.get('position')
            if position is None:
                continue
            
            # 獲取車手代碼
            driver_tla = driver_data.get('driver_tla', driver_num)
            
            # 解析圈時
            last_lap_time = driver_data.get('last_lap_time')
            best_lap_time = driver_data.get('best_lap_time')
            
            lap_time_seconds = self._parse_lap_time_to_seconds(last_lap_time) if last_lap_time else None
            best_lap_seconds = self._parse_lap_time_to_seconds(best_lap_time) if best_lap_time else None
            
            # 計算與領先者差距（秒）
            # gap_to_leader_display 格式: "+9.734s" 或 "+1 L" (套圈)
            gap_to_leader = 0.0
            gap_display = driver_data.get('gap_to_leader_display', '')
            if gap_display and position != 1:
                try:
                    # 移除 + 號
                    gap_str = gap_display.lstrip('+')
                    # 移除 s 後綴
                    gap_str = gap_str.rstrip('s')
                    if 'LAP' not in gap_display.upper() and 'L' not in gap_display.upper():
                        gap_to_leader = float(gap_str)
                except (ValueError, TypeError):
                    pass
            
            # 與前車差距
            # gap_to_ahead_display 格式: "+1.234s" 或 "+1 L"
            gap_to_ahead = 0.0
            gap_ahead_display = driver_data.get('gap_to_ahead_display', '')
            if gap_ahead_display and position != 1:
                try:
                    gap_str = gap_ahead_display.lstrip('+')
                    gap_str = gap_str.rstrip('s')
                    if 'LAP' not in gap_ahead_display.upper() and 'L' not in gap_ahead_display.upper():
                        gap_to_ahead = float(gap_str)
                except (ValueError, TypeError):
                    pass
            
            # 獲取輪胎資訊
            tyre_info = tyre_state.get(driver_num, {})
            compound = tyre_info.get('compound', 'MEDIUM')
            tyre_age = tyre_info.get('tyre_age', 0)
            pit_count = tyre_info.get('stint_count', 1) - 1  # stint_count 從 1 開始
            if pit_count < 0:
                pit_count = 0
            
            # 構建車手數據 (欄位名稱需與 predictor._extract_features 期望一致)
            # 獲取發車位置 (grid position) - 從 ranking_table 獲取
            grid_position = position  # 預設用當前位置
            if hasattr(self, 'ranking_table') and hasattr(self.ranking_table, '_grid_positions'):
                grid_position = self.ranking_table._grid_positions.get(driver_num, position)
            
            predictor_snapshot['drivers'][driver_num] = {
                'driver_tla': driver_tla,  # predictor 用 driver_tla
                'position': position,
                'gap_to_leader': gap_to_leader,  # 數值格式
                'gap_to_ahead': gap_to_ahead,    # 數值格式
                'last_lap_time': last_lap_time or '',  # 保持字串格式，predictor 會解析
                'best_lap_time': best_lap_time or '',  # 保持字串格式
                'tyre_compound': compound,
                'tyre_age': tyre_age,
                'pit_count': pit_count,
                'lap': driver_laps.get(driver_num, current_lap),
                'grid_position': grid_position,  # 發車位置，用於計算 position_delta
            }
        
        return predictor_snapshot
    
    def _parse_lap_time_to_seconds(self, lap_time_str: str) -> Optional[float]:
        """解析圈時字串為秒數"""
        if not lap_time_str:
            return None
        try:
            if ':' in lap_time_str:
                parts = lap_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(lap_time_str)
        except (ValueError, IndexError):
            return None

    def _extract_car_data_for_timestamp(self, timestamp: str) -> Dict[str, Dict]:
        """從 CarData 中提取指定時間點的遙測資料"""
        result = {}
        if not hasattr(self, '_car_data') or not self._car_data:
            return result
        
        # CarData 格式: [{"timestamp": "...", "data": {"Entries": [{"Cars": {...}}]}}]
        # 找到最接近當前時間的記錄
        target_record = None
        for record in self._car_data:
            record_time = record.get('timestamp', '')
            if record_time <= timestamp:
                target_record = record
            else:
                break  # 已經超過當前時間
        
        if not target_record:
            # 沒有找到，使用第一個
            target_record = self._car_data[0] if self._car_data else None
        
        if not target_record:
            return result
        
        data = target_record.get('data', {})
        entries = data.get('Entries', [])
        
        if not isinstance(entries, list):
            return result
        
        # 取最新的 entry
        if entries:
            latest_entry = entries[-1] if len(entries) > 0 else {}
            cars = latest_entry.get('Cars', {})
            for driver_num, car_info in cars.items():
                channels = car_info.get('Channels', {})
                if channels:
                    result[driver_num] = {
                        'rpm': channels.get('0', ''),       # Channel 0 = RPM
                        'speed': channels.get('2', ''),     # Channel 2 = Speed
                        'gear': channels.get('3', ''),      # Channel 3 = Gear
                        'throttle': channels.get('4', ''),  # Channel 4 = Throttle
                        'brake': channels.get('5', ''),     # Channel 5 = Brake
                        'drs': channels.get('45', ''),      # Channel 45 = DRS
                    }
        
        return result


# ========== 主程式 ==========

def main():
    print("="*70)
    print("F1 實時車手位置追蹤系統 - Stage 1 Demo")
    print("="*70)
    
    app = QApplication(sys.argv)
    window = LivePositionTrackingMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
