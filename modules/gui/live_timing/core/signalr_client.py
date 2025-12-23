"""
F1 SignalR Client - 即時 Live Timing 連接
==========================================

直接連接 F1 官方 SignalR WebSocket API 獲取即時數據

官方 API 端點:
- Negotiate: https://livetiming.formula1.com/signalr/negotiate
- Connect:   wss://livetiming.formula1.com/signalr/connect
- Hub:       Streaming

數據格式:
- CarData.z: base64 + zlib 壓縮，包含 Channels (0=RPM, 2=Speed, 3=Gear, 4=Throttle, 5=Brake, 45=DRS)
- Position.z: base64 + zlib 壓縮，包含車輛 X, Y, Z 座標
- TimingData: JSON 格式，包含位置、差距、圈速等

Author: F1T Team
Date: 2025-12-05
"""

import json
import base64
import zlib
import asyncio
import threading
import urllib.parse
from typing import Dict, List, Any, Optional, Callable
from queue import Queue, Empty
from datetime import datetime

import requests

from PyQt5.QtCore import QThread, pyqtSignal

# 檢查 websockets 是否可用
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("[WARNING] websockets not available. Install with: pip install websockets")


class F1SignalRClient:
    """
    F1 官方 SignalR 客戶端
    
    直接連接 F1 Live Timing SignalR WebSocket API
    不依賴任何第三方套件 (除了 websockets 和 requests)
    """
    
    SIGNALR_URL = "https://livetiming.formula1.com/signalr"
    HUB_NAME = "Streaming"
    PROTOCOL_VERSION = "1.5"
    
    # CarData.z Channels 定義 (參考 LiveF1 專案 constants.py)
    # LiveF1 的 channel_name_map: {'0': 'rpm', '2': 'speed', '3': 'n_gear', '4': 'throttle', '5': 'brake', '45': 'drs'}
    CAR_DATA_CHANNELS = {
        "0": "rpm",
        "2": "speed", 
        "3": "n_gear",  # LiveF1 使用 n_gear
        "4": "throttle",
        "5": "brake",
        "45": "drs"
    }
    
    def __init__(
        self, 
        topics: List[str], 
        on_data_callback: Optional[Callable[[str, Any], None]] = None, 
        on_status_callback: Optional[Callable[[str], None]] = None, 
        on_error_callback: Optional[Callable[[str], None]] = None
    ):
        """
        初始化 SignalR 客戶端
        
        Args:
            topics: 訂閱的數據主題列表
            on_data_callback: 數據回調函數 (topic, data)
            on_status_callback: 狀態回調函數 (status_message)
            on_error_callback: 錯誤回調函數 (error_message)
        """
        self.topics = topics
        self._on_data = on_data_callback
        self._on_status = on_status_callback
        self._on_error = on_error_callback
        
        self._running = False
        self._ws = None
        self._session = None
        self._connection_token = None
        self._cookie = None
        
    def _emit_status(self, msg: str):
        """發送狀態訊息"""
        print(f"[F1_SIGNALR] {msg}")
        if self._on_status:
            self._on_status(msg)
            
    def _emit_error(self, msg: str):
        """發送錯誤訊息"""
        print(f"[F1_SIGNALR] ERROR: {msg}")
        if self._on_error:
            self._on_error(msg)
            
    def _emit_data(self, topic: str, data: Any):
        """發送數據"""
        if self._on_data:
            self._on_data(topic, data)
    
    def _negotiate(self) -> bool:
        """
        與 SignalR 服務器協商連接
        
        Returns:
            成功返回 True，失敗返回 False
        """
        self._emit_status("Negotiating SignalR connection...")
        
        try:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "BestHTTP",
                "Accept-Encoding": "gzip, identity",
                "Connection": "keep-alive, Upgrade"
            })
            
            # 構建連接數據
            conn_data = json.dumps([{"name": self.HUB_NAME}])
            
            # 發送 negotiate 請求
            negotiate_url = f"{self.SIGNALR_URL}/negotiate"
            params = {
                "connectionData": conn_data,
                "clientProtocol": self.PROTOCOL_VERSION
            }
            
            response = self._session.get(negotiate_url, params=params, timeout=10)
            
            if response.status_code != 200:
                self._emit_error(f"Negotiate failed: HTTP {response.status_code}")
                return False
            
            # 解析回應
            data = response.json()
            self._connection_token = data.get("ConnectionToken")
            protocol_version = data.get("ProtocolVersion", self.PROTOCOL_VERSION)
            
            if not self._connection_token:
                self._emit_error("Negotiate failed: No ConnectionToken received")
                return False
            
            # 保存 Cookie
            self._cookie = "; ".join([f"{name}={value}" for name, value in response.cookies.items()])
            
            self._emit_status(f"Negotiate successful, Protocol: {protocol_version}")
            return True
            
        except Exception as e:
            self._emit_error(f"Negotiate exception: {e}")
            return False
    
    def _build_ws_url(self) -> str:
        """構建 WebSocket 連接 URL"""
        conn_data = json.dumps([{"name": self.HUB_NAME}])
        params = {
            "transport": "webSockets",
            "connectionToken": self._connection_token,
            "connectionData": conn_data,
            "clientProtocol": self.PROTOCOL_VERSION
        }
        query = urllib.parse.urlencode(params)
        return f"wss://livetiming.formula1.com/signalr/connect?{query}"
    
    def _decode_compressed_data(self, data: str) -> dict:
        """
        解碼 base64 + zlib 壓縮的數據
        
        參考 LiveF1 專案 helper.py 的 parse() 函數:
        - 如果以 '{' 開頭，直接解析 JSON
        - 如果以 '"' 開頭，去除引號
        - 使用 zlib.decompress(decoded, -zlib.MAX_WBITS) 解壓
        - 使用 utf-8-sig 編碼解碼 (處理 BOM)
        
        Args:
            data: base64 編碼的壓縮字串
            
        Returns:
            解碼後的 JSON 數據
        """
        try:
            # LiveF1 的解析邏輯
            if data.startswith('{'):
                return json.loads(data)
            if data.startswith('"'):
                data = data.strip('"')
            
            decoded = base64.b64decode(data)
            decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
            # 使用 utf-8-sig 處理可能的 BOM
            return json.loads(decompressed.decode("utf-8-sig"))
        except Exception as e:
            print(f"[F1_SIGNALR] Decompress failed: {e}")
            return {}
    
    def _parse_car_data(self, raw_data: dict) -> List[Dict]:
        """
        解析 CarData.z 數據
        
        Returns:
            標準化的車輛數據列表 [{"DriverNo": "1", "speed": 320, "rpm": 10500, ...}, ...]
        """
        results = []
        
        entries = raw_data.get("Entries", [])
        for entry in entries:
            utc = entry.get("Utc", "")
            cars = entry.get("Cars", {})
            
            for driver_no, car_data in cars.items():
                channels = car_data.get("Channels", {})
                
                record = {
                    "DriverNo": driver_no,
                    "timestamp": utc
                }
                
                # 映射 Channels 到標準欄位名
                for channel_id, field_name in self.CAR_DATA_CHANNELS.items():
                    if channel_id in channels:
                        record[field_name] = channels[channel_id]
                    elif int(channel_id) in channels:
                        record[field_name] = channels[int(channel_id)]
                
                results.append(record)
        
        return results
    
    def _parse_position_data(self, raw_data: dict) -> List[Dict]:
        """
        解析 Position.z 數據
        
        Returns:
            標準化的位置數據列表 [{"DriverNo": "1", "X": 1234, "Y": 5678, "Z": 90, ...}, ...]
        """
        results = []
        
        positions = raw_data.get("Position", [])
        for pos in positions:
            timestamp = pos.get("Timestamp", "")
            entries = pos.get("Entries", {})
            
            for driver_no, pos_data in entries.items():
                record = {
                    "DriverNo": driver_no,
                    "timestamp": timestamp,
                    "Status": pos_data.get("Status", "Unknown"),
                    "X": pos_data.get("X", 0),
                    "Y": pos_data.get("Y", 0),
                    "Z": pos_data.get("Z", 0)
                }
                results.append(record)
        
        return results
    
    def _parse_timing_data(self, raw_data: dict) -> List[Dict]:
        """
        解析 TimingData 數據 (增量或完整)
        
        Returns:
            標準化的計時數據列表
        """
        results = []
        
        # 檢查是否為完整格式
        if "Lines" in raw_data:
            lines = raw_data["Lines"]
        else:
            lines = raw_data
        
        for driver_no, timing in lines.items():
            if not isinstance(timing, dict):
                continue
                
            record = {"DriverNo": driver_no}
            
            # 複製所有欄位
            for key, value in timing.items():
                if isinstance(value, dict):
                    # 展平嵌套結構
                    for sub_key, sub_value in value.items():
                        record[f"{key}_{sub_key}"] = sub_value
                else:
                    record[key] = value
            
            results.append(record)
        
        return results
    
    def _parse_driver_list(self, raw_data: dict) -> List[Dict]:
        """解析 DriverList 數據"""
        results = []
        
        for driver_no, info in raw_data.items():
            if not isinstance(info, dict):
                continue
            
            record = {
                "RacingNumber": driver_no,
                "Tla": info.get("Tla", driver_no),
                "BroadcastName": info.get("BroadcastName", ""),
                "FullName": info.get("FullName", ""),
                "TeamName": info.get("TeamName", ""),
                "TeamColour": info.get("TeamColour", "CCCCCC"),
                "HeadshotUrl": info.get("HeadshotUrl", "")
            }
            results.append(record)
        
        return results
    
    async def _process_message(self, message: dict):
        """
        處理 SignalR 消息
        
        消息格式:
        {
            "C": "...",  # 連接 ID
            "M": [       # 消息列表
                {
                    "H": "Streaming",  # Hub 名稱
                    "M": "feed",       # 方法名稱
                    "A": [             # 參數
                        "CarData.z",   # Topic
                        "base64data..."  # 數據 (可能是壓縮的)
                    ]
                }
            ]
        }
        """
        # DEBUG: 每 60 秒輸出所有 topic 的統計
        if not hasattr(self, '_all_topic_counts'):
            self._all_topic_counts = {}
            self._last_topic_log_time = 0
        
        import time
        current_time = time.time()
        
        # 處理消息列表
        messages = message.get("M", [])
        for msg in messages:
            hub = msg.get("H", "")
            method = msg.get("M", "")
            args = msg.get("A", [])
            
            if len(args) < 2:
                continue
            
            topic = args[0]
            data = args[1]
            
            # 統計所有 topic
            self._all_topic_counts[topic] = self._all_topic_counts.get(topic, 0) + 1
            
            # 每 30 秒輸出一次統計
            if current_time - self._last_topic_log_time > 30:
                self._last_topic_log_time = current_time
                print(f"[F1_SIGNALR] Topic stats: {dict(self._all_topic_counts)}")
            
            # 調試：記錄收到的所有 topic
            if not hasattr(self, '_topic_debug_counts'):
                self._topic_debug_counts = {}
            self._topic_debug_counts[topic] = self._topic_debug_counts.get(topic, 0) + 1
            
            # 對 CarData.z 和 Position.z 特別調試
            if topic in ["CarData.z", "Position.z"]:
                count = self._topic_debug_counts[topic]
                if count <= 3:
                    print(f"[F1_SIGNALR] DEBUG {topic} #{count}: data type={type(data).__name__}, len={len(data) if hasattr(data, '__len__') else 'N/A'}")
                    if isinstance(data, str):
                        print(f"[F1_SIGNALR] DEBUG {topic}: first 100 chars: {data[:100]}")
                    elif isinstance(data, dict):
                        print(f"[F1_SIGNALR] DEBUG {topic}: keys={list(data.keys())}")
            
            # 根據 topic 解析數據
            try:
                if topic in ["CarData.z", "CarData"]:
                    if isinstance(data, str):
                        raw = self._decode_compressed_data(data)
                        if self._topic_debug_counts.get(topic, 0) <= 3:
                            print(f"[F1_SIGNALR] DEBUG {topic}: decoded raw keys={list(raw.keys()) if raw else 'EMPTY'}")
                        parsed = self._parse_car_data(raw)
                        if self._topic_debug_counts.get(topic, 0) <= 3:
                            print(f"[F1_SIGNALR] DEBUG {topic}: parsed count={len(parsed) if parsed else 0}")
                        if parsed:
                            self._emit_data("CarData.z", parsed)
                    else:
                        if self._topic_debug_counts.get(topic, 0) <= 3:
                            print(f"[F1_SIGNALR] DEBUG {topic}: data is NOT str, skipping")
                    
                elif topic in ["Position.z", "Position"]:
                    if isinstance(data, str):
                        raw = self._decode_compressed_data(data)
                        if self._topic_debug_counts.get(topic, 0) <= 3:
                            print(f"[F1_SIGNALR] DEBUG {topic}: decoded raw keys={list(raw.keys()) if raw else 'EMPTY'}")
                        parsed = self._parse_position_data(raw)
                        if self._topic_debug_counts.get(topic, 0) <= 3:
                            print(f"[F1_SIGNALR] DEBUG {topic}: parsed count={len(parsed) if parsed else 0}")
                        if parsed:
                            self._emit_data("Position.z", parsed)
                    else:
                        if self._topic_debug_counts.get(topic, 0) <= 3:
                            print(f"[F1_SIGNALR] DEBUG {topic}: data is NOT str, skipping")
                    
                elif topic == "TimingData":
                    if isinstance(data, dict):
                        parsed = self._parse_timing_data(data)
                        if parsed:
                            self._emit_data("TimingData", parsed)
                    
                elif topic == "DriverList":
                    if isinstance(data, dict):
                        parsed = self._parse_driver_list(data)
                        if parsed:
                            self._emit_data("DriverList", parsed)
                    
                elif topic in ["WeatherData", "TrackStatus", "RaceControlMessages", 
                              "SessionInfo", "LapCount", "SessionStatus"]:
                    if isinstance(data, dict):
                        self._emit_data(topic, [data])
                    elif isinstance(data, list):
                        self._emit_data(topic, data)
                    
                elif topic == "CurrentTyres":
                    # 增量更新格式可能是 {"Tyres": {...}} 或直接 {"1": {...}}
                    if isinstance(data, dict):
                        tyres_data = data.get("Tyres", data)
                        results = []
                        for key, value in tyres_data.items():
                            if key.startswith("_"):
                                continue
                            if isinstance(value, dict):
                                value["DriverNo"] = key
                                results.append(value)
                        if results:
                            self._emit_data(topic, results)
                    
                elif topic == "TyreStintSeries":
                    # 增量更新格式可能是 {"Stints": {...}} 或直接 {"1": [...]}
                    if isinstance(data, dict):
                        stints_data = data.get("Stints", data)
                        results = []
                        for key, value in stints_data.items():
                            if key.startswith("_"):
                                continue
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, dict):
                                        item_copy = item.copy()
                                        item_copy["DriverNo"] = key
                                        results.append(item_copy)
                            elif isinstance(value, dict):
                                value["DriverNo"] = key
                                results.append(value)
                        if results:
                            self._emit_data(topic, results)
                
                elif topic == "PitStopSeries":
                    if isinstance(data, dict):
                        results = []
                        for key, value in data.items():
                            if key.startswith("_"):
                                continue
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, dict):
                                        item["DriverNo"] = key
                                        results.append(item)
                            elif isinstance(value, dict):
                                value["DriverNo"] = key
                                results.append(value)
                        if results:
                            self._emit_data(topic, results)
                    
                else:
                    # 其他 topic，直接傳遞
                    if isinstance(data, dict):
                        self._emit_data(topic, [data])
                    elif isinstance(data, list):
                        self._emit_data(topic, data)
                    
            except Exception as e:
                print(f"[F1_SIGNALR] Parse {topic} error: {e}")
                import traceback
                traceback.print_exc()
        
        # 處理訂閱回應 - 包含所有 topic 的初始數據
        if "R" in message:
            r_data = message["R"]
            if isinstance(r_data, dict):
                print(f"[F1_SIGNALR] Processing initial data from subscription response...")
                # 解析初始數據
                for topic, data in r_data.items():
                    try:
                        if topic in ["LapCount", "SessionInfo", "SessionStatus", 
                                     "WeatherData", "TrackStatus"]:
                            # 這些 topic 的數據直接是 dict，包裝成 list 發送
                            if isinstance(data, dict):
                                self._emit_data(topic, [data])
                                print(f"[F1_SIGNALR] Initial {topic}: {data}")
                        elif topic == "RaceControlMessages":
                            # RaceControlMessages 可能是 dict 或包含 Messages 的結構
                            if isinstance(data, dict) and "Messages" in data:
                                # 轉換為列表格式
                                messages = data.get("Messages", {})
                                if isinstance(messages, dict):
                                    self._emit_data(topic, [{"Messages": messages}])
                            elif isinstance(data, dict):
                                self._emit_data(topic, [data])
                        elif topic == "TimingData":
                            # TimingData 需要特殊解析
                            if isinstance(data, dict):
                                parsed = self._parse_timing_data(data)
                                if parsed:
                                    self._emit_data("TimingData", parsed)
                        elif topic == "DriverList":
                            if isinstance(data, dict):
                                parsed = self._parse_driver_list(data)
                                if parsed:
                                    self._emit_data("DriverList", parsed)
                        elif topic == "CurrentTyres":
                            # CurrentTyres 格式: {"Tyres": {"1": {...}, "4": {...}}, "_kf": true}
                            if isinstance(data, dict):
                                tyres_data = data.get("Tyres", data)  # 嘗試獲取 Tyres，否則使用整個 data
                                results = []
                                for driver_no, tyre_info in tyres_data.items():
                                    if driver_no.startswith("_"):  # 跳過 _kf 等元數據
                                        continue
                                    if isinstance(tyre_info, dict):
                                        tyre_info["DriverNo"] = driver_no
                                        results.append(tyre_info)
                                if results:
                                    self._emit_data(topic, results)
                                    print(f"[F1_SIGNALR] Initial {topic}: {len(results)} drivers")
                        elif topic == "TyreStintSeries":
                            # TyreStintSeries 格式: {"Stints": {"1": [...], "4": [...]}, "_kf": true}
                            if isinstance(data, dict):
                                stints_data = data.get("Stints", data)  # 嘗試獲取 Stints，否則使用整個 data
                                results = []
                                for driver_no, stint_list in stints_data.items():
                                    if driver_no.startswith("_"):  # 跳過 _kf 等元數據
                                        continue
                                    if isinstance(stint_list, list):
                                        for stint in stint_list:
                                            if isinstance(stint, dict):
                                                stint_copy = stint.copy()
                                                stint_copy["DriverNo"] = driver_no
                                                results.append(stint_copy)
                                    elif isinstance(stint_list, dict):
                                        stint_list["DriverNo"] = driver_no
                                        results.append(stint_list)
                                if results:
                                    self._emit_data(topic, results)
                                    print(f"[F1_SIGNALR] Initial {topic}: {len(results)} stint records")
                        elif topic == "PitStopSeries":
                            if isinstance(data, dict):
                                results = []
                                for key, value in data.items():
                                    if key.startswith("_"):
                                        continue
                                    if isinstance(value, list):
                                        for item in value:
                                            if isinstance(item, dict):
                                                item["DriverNo"] = key
                                                results.append(item)
                                    elif isinstance(value, dict):
                                        value["DriverNo"] = key
                                        results.append(value)
                                if results:
                                    self._emit_data(topic, results)
                    except Exception as e:
                        print(f"[F1_SIGNALR] Error parsing initial {topic}: {e}")
            
            self._emit_status("Subscription confirmed, waiting for data...")
        
        # 處理連接建立
        if "S" in message and message["S"] == 1:
            self._emit_status("SignalR connection established")
    
    async def _connect_and_run(self):
        """連接 WebSocket 並開始接收數據"""
        if not WEBSOCKETS_AVAILABLE:
            self._emit_error("websockets package not installed. Run: pip install websockets")
            return
        
        ws_url = self._build_ws_url()
        
        # 構建 headers
        headers = {
            "User-Agent": "BestHTTP",
            "Accept-Encoding": "gzip, identity",
        }
        if self._cookie:
            headers["Cookie"] = self._cookie
        
        self._emit_status("Establishing WebSocket connection...")
        
        try:
            async with websockets.connect(ws_url, extra_headers=headers) as ws:
                self._ws = ws
                self._emit_status("WebSocket connected")
                
                # 發送訂閱請求
                subscribe_msg = {
                    "H": self.HUB_NAME,
                    "M": "Subscribe",
                    "A": [self.topics],
                    "I": 0
                }
                await ws.send(json.dumps(subscribe_msg))
                self._emit_status(f"Subscribed to: {', '.join(self.topics)}")
                
                # 接收消息循環
                while self._running:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30)
                        
                        if msg:
                            data = json.loads(msg)
                            await self._process_message(data)
                            
                    except asyncio.TimeoutError:
                        # 發送心跳
                        try:
                            await ws.ping()
                        except:
                            pass
                    except websockets.exceptions.ConnectionClosed:
                        self._emit_status("WebSocket connection closed")
                        break
                    except Exception as e:
                        print(f"[F1_SIGNALR] Receive error: {e}")
                        
        except Exception as e:
            self._emit_error(f"WebSocket connection failed: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """開始運行客戶端 (阻塞)"""
        self._running = True
        
        # 1. Negotiate
        if not self._negotiate():
            return
        
        # 2. Connect and run
        try:
            asyncio.run(self._connect_and_run())
        except KeyboardInterrupt:
            self._emit_status("User interrupted")
        finally:
            self._running = False
            self._emit_status("Client stopped")
    
    def stop(self):
        """停止客戶端"""
        self._running = False


class RealTimeLiveF1Worker(QThread):
    """
    即時 Live F1 數據擷取 Worker 執行緒
    
    使用 F1 官方 SignalR API 直接連接 Live Timing 服務
    """
    
    # 信號
    data_received = pyqtSignal(str, object)  # (topic, data_list)
    connection_status = pyqtSignal(str)       # 連接狀態
    error_occurred = pyqtSignal(str)          # 錯誤訊息
    
    # 訂閱的數據流
    DEFAULT_TOPICS = [
        "CarData.z",        # 車輛遙測 (Speed, RPM, Gear, Throttle, Brake, DRS)
        "Position.z",       # 位置數據 (X, Y, Z)
        "TimingData",       # 計時數據 (Position, Gap, Interval, LapTime)
        "DriverList",       # 車手列表 (Name, Team, TeamColour)
        "WeatherData",      # 天氣數據
        "TrackStatus",      # 賽道狀態 (綠旗/黃旗/紅旗)
        "RaceControlMessages",  # 賽事控制訊息
        "SessionInfo",      # 賽事資訊
        "SessionStatus",    # 賽事狀態
        "LapCount",         # 圈數
        "CurrentTyres",     # 當前輪胎 (Compound)
        "TyreStintSeries",  # 輪胎 stint 資訊
        "PitStopSeries",    # 進站資訊
    ]
    
    def __init__(self, topics: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.topics = topics or self.DEFAULT_TOPICS
        self._running = False
        self._client = None
        self._data_queue = Queue()
        
    def run(self):
        """執行緒主迴圈"""
        self._running = True
        
        if not WEBSOCKETS_AVAILABLE:
            self.error_occurred.emit("websockets package not installed. Run: pip install websockets")
            return
        
        self.connection_status.emit("Initializing F1 Live Timing connection...")
        print("[REALTIME] Initializing F1 SignalR client...")
        
        # 數據回調
        def on_data(topic, data_list):
            self._data_queue.put((topic, data_list))
        
        # 狀態回調
        def on_status(msg):
            self.connection_status.emit(msg)
        
        # 錯誤回調
        def on_error(msg):
            self.error_occurred.emit(msg)
        
        try:
            # 創建 SignalR 客戶端
            self._client = F1SignalRClient(
                topics=self.topics,
                on_data_callback=on_data,
                on_status_callback=on_status,
                on_error_callback=on_error
            )
            
            # 啟動隊列處理執行緒
            def process_queue():
                while self._running:
                    try:
                        topic, data_list = self._data_queue.get(timeout=0.1)
                        self.data_received.emit(topic, data_list)
                        if data_list:
                            print(f"[REALTIME] Received {topic}: {len(data_list)} records")
                    except Empty:
                        continue
                    except Exception as e:
                        print(f"[REALTIME] Queue processing error: {e}")
            
            queue_thread = threading.Thread(target=process_queue, daemon=True)
            queue_thread.start()
            
            # 運行客戶端 (阻塞)
            self._client.run()
            
        except KeyboardInterrupt:
            print("[REALTIME] User interrupted")
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {str(e)}")
            print(f"[REALTIME] Connection error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._running = False
            self.connection_status.emit("Connection closed")
    
    def stop(self):
        """停止執行緒"""
        self._running = False
        if self._client:
            self._client.stop()
        self.wait(3000)  # 等待最多 3 秒


# 導出
__all__ = ['F1SignalRClient', 'RealTimeLiveF1Worker', 'WEBSOCKETS_AVAILABLE']
