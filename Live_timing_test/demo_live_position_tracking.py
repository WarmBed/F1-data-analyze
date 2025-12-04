"""
F1 即時車手位置追蹤系統 - Real-Time Live Timing
Live Position Tracking System - Real-Time Mode

功能：
1. 即時連接 F1 Live Timing SignalR 服務
2. 顯示即時車手位置/排名/速度/輪胎/差距
3. 支援歷史數據播放模式
4. 完全獨立運行，不整合到 F1T GUI

數據來源：
- 即時模式：F1 Live Timing SignalR WebSocket
- 歷史模式：本地 JSON 檔案 (json/LiveF1/{year}/{race}_{session}/)

作者：F1T Team
日期：2025-11-22
更新：2025-12-01 - 新增即時 Live Timing 連接功能
"""

import os
import sys
import json
import base64
import zlib
import re
import requests
import asyncio
import threading
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from queue import Queue, Empty

# 添加根目錄到 sys.path 以便 import CLI_modules
_root_dir = Path(__file__).resolve().parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QSlider, QLabel,
    QHeaderView, QAbstractItemView, QComboBox, QGroupBox, QSplitter,
    QMessageBox, QRadioButton, QButtonGroup, QListWidget, QListWidgetItem,
    QMenu
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QPointF, QThread, QObject, QRectF
from PyQt5.QtGui import QColor, QFont, QBrush, QPainter, QPen, QPainterPath

# 嘗試導入 SignalR 客戶端
try:
    from signalrcore.hub_connection_builder import HubConnectionBuilder
    SIGNALR_AVAILABLE = True
except ImportError:
    SIGNALR_AVAILABLE = False
    print("[WARNING] signalrcore not available. Install with: pip install signalrcore")

# 嘗試導入 websockets
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("[WARNING] websockets not available. Install with: pip install websockets")

# 嘗試導入 livef1
try:
    from livef1.adapters import RealF1Client
    LIVEF1_AVAILABLE = True
except ImportError:
    LIVEF1_AVAILABLE = False
    print("[WARNING] livef1 not available. Install with: pip install livef1")

# 勝率預測器
try:
    from CLI_modules.cli.prediction.live_win_probability.predictor import LiveWinProbabilityPredictor
    WIN_PROBABILITY_AVAILABLE = True
except ImportError as e:
    WIN_PROBABILITY_AVAILABLE = False
    print(f"[WARNING] Win probability predictor not available: {e}")
    print("[WARNING] Win probability predictor not available")


# ============================================================
# 即時 Live F1 數據源 - 直接連接 F1 官方 SignalR API
# ============================================================

class F1SignalRClient:
    """
    F1 官方 SignalR 客戶端
    
    直接連接 F1 Live Timing SignalR WebSocket API
    不依賴任何第三方套件 (除了 websockets 和 requests)
    
    官方 API 端點:
    - Negotiate: https://livetiming.formula1.com/signalr/negotiate
    - Connect:   wss://livetiming.formula1.com/signalr/connect
    - Hub:       Streaming
    
    數據格式:
    - CarData.z: base64 + zlib 壓縮，包含 Channels (0=RPM, 2=Speed, 3=Gear, 4=Throttle, 5=Brake, 45=DRS)
    - Position.z: base64 + zlib 壓縮，包含車輛 X, Y, Z 座標
    - TimingData: JSON 格式，包含位置、差距、圈速等
    """
    
    SIGNALR_URL = "https://livetiming.formula1.com/signalr"
    HUB_NAME = "Streaming"
    PROTOCOL_VERSION = "1.5"
    
    # CarData.z Channels 定義
    CAR_DATA_CHANNELS = {
        "0": "rpm",
        "2": "speed", 
        "3": "gear",
        "4": "throttle",
        "5": "brake",
        "45": "drs"
    }
    
    def __init__(self, topics: list, on_data_callback=None, on_status_callback=None, on_error_callback=None):
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
            
    def _emit_data(self, topic: str, data):
        """發送數據"""
        if self._on_data:
            self._on_data(topic, data)
    
    def _negotiate(self) -> bool:
        """
        與 SignalR 服務器協商連接
        
        Returns:
            成功返回 True，失敗返回 False
        """
        self._emit_status("正在協商 SignalR 連接...")
        
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
                self._emit_error(f"Negotiate 失敗: HTTP {response.status_code}")
                return False
            
            # 解析回應
            data = response.json()
            self._connection_token = data.get("ConnectionToken")
            protocol_version = data.get("ProtocolVersion", self.PROTOCOL_VERSION)
            
            if not self._connection_token:
                self._emit_error("Negotiate 失敗: 未獲得 ConnectionToken")
                return False
            
            # 保存 Cookie
            self._cookie = "; ".join([f"{name}={value}" for name, value in response.cookies.items()])
            
            self._emit_status(f"Negotiate 成功，Protocol: {protocol_version}")
            return True
            
        except Exception as e:
            self._emit_error(f"Negotiate 異常: {e}")
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
        
        Args:
            data: base64 編碼的壓縮字串
            
        Returns:
            解碼後的 JSON 數據
        """
        try:
            decoded = base64.b64decode(data)
            decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
            return json.loads(decompressed.decode("utf-8"))
        except Exception as e:
            print(f"[F1_SIGNALR] 解壓縮失敗: {e}")
            return {}
    
    def _parse_car_data(self, raw_data: dict) -> list:
        """
        解析 CarData.z 數據
        
        原始格式:
        {
            "Entries": [{
                "Utc": "2024-07-28T12:06:49.419Z",
                "Cars": {
                    "1": {"Channels": {"0": 10500, "2": 320, "3": 8, "4": 100, "5": 0, "45": 1}},
                    ...
                }
            }]
        }
        
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
    
    def _parse_position_data(self, raw_data: dict) -> list:
        """
        解析 Position.z 數據
        
        原始格式:
        {
            "Position": [{
                "Timestamp": "2024-07-28T12:06:49.419Z",
                "Entries": {
                    "1": {"Status": "OnTrack", "X": 1234, "Y": 5678, "Z": 90},
                    ...
                }
            }]
        }
        
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
    
    def _parse_timing_data(self, raw_data: dict) -> list:
        """
        解析 TimingData 數據 (增量或完整)
        
        格式可能是:
        1. 完整格式: {"Lines": {"1": {...}, "4": {...}}}
        2. 增量格式: {"1": {"Position": "1"}, "4": {"GapToLeader": "+5.0"}}
        
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
    
    def _parse_driver_list(self, raw_data: dict) -> list:
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
            
            # 根據 topic 解析數據
            try:
                if topic in ["CarData.z", "CarData"]:
                    # 解壓縮並解析
                    if isinstance(data, str):
                        raw = self._decode_compressed_data(data)
                        parsed = self._parse_car_data(raw)
                        if parsed:
                            self._emit_data("CarData.z", parsed)
                    
                elif topic in ["Position.z", "Position"]:
                    # 解壓縮並解析
                    if isinstance(data, str):
                        raw = self._decode_compressed_data(data)
                        parsed = self._parse_position_data(raw)
                        if parsed:
                            self._emit_data("Position.z", parsed)
                    
                elif topic == "TimingData":
                    # JSON 格式，直接解析
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
                    # 直接傳遞 JSON 數據
                    if isinstance(data, dict):
                        self._emit_data(topic, [data])
                    elif isinstance(data, list):
                        self._emit_data(topic, data)
                    
                elif topic in ["CurrentTyres", "TyreStintSeries", "PitStopSeries"]:
                    # 輪胎相關數據
                    if isinstance(data, dict):
                        # 可能是 {"Stints": {"1": [...], "4": [...]}} 格式
                        results = []
                        for key, value in data.items():
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
                            self._emit_data(topic, [data])
                    
                else:
                    # 其他 topic，直接傳遞
                    if isinstance(data, dict):
                        self._emit_data(topic, [data])
                    elif isinstance(data, list):
                        self._emit_data(topic, data)
                    
            except Exception as e:
                print(f"[F1_SIGNALR] 解析 {topic} 錯誤: {e}")
                import traceback
                traceback.print_exc()
        
        # 處理訂閱回應
        if "R" in message:
            self._emit_status("訂閱成功，等待數據...")
        
        # 處理連接建立
        if "S" in message and message["S"] == 1:
            self._emit_status("SignalR 連接已建立")
    
    async def _connect_and_run(self):
        """連接 WebSocket 並開始接收數據"""
        if not WEBSOCKETS_AVAILABLE:
            self._emit_error("websockets 套件未安裝，請執行: pip install websockets")
            return
        
        ws_url = self._build_ws_url()
        
        # 構建 headers
        headers = {
            "User-Agent": "BestHTTP",
            "Accept-Encoding": "gzip, identity",
        }
        if self._cookie:
            headers["Cookie"] = self._cookie
        
        self._emit_status("正在建立 WebSocket 連接...")
        
        try:
            async with websockets.connect(ws_url, extra_headers=headers) as ws:
                self._ws = ws
                self._emit_status("WebSocket 連接成功")
                
                # 發送訂閱請求
                subscribe_msg = {
                    "H": self.HUB_NAME,
                    "M": "Subscribe",
                    "A": [self.topics],
                    "I": 0
                }
                await ws.send(json.dumps(subscribe_msg))
                self._emit_status(f"已訂閱: {', '.join(self.topics)}")
                
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
                        self._emit_status("WebSocket 連接已關閉")
                        break
                    except Exception as e:
                        print(f"[F1_SIGNALR] 接收錯誤: {e}")
                        
        except Exception as e:
            self._emit_error(f"WebSocket 連接失敗: {e}")
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
            self._emit_status("使用者中斷")
        finally:
            self._running = False
            self._emit_status("客戶端已停止")
    
    def stop(self):
        """停止客戶端"""
        self._running = False


class RealTimeLiveF1Worker(QThread):
    """
    即時 Live F1 數據擷取 Worker 執行緒
    
    使用 F1 官方 SignalR API 直接連接 Live Timing 服務
    (不依賴 livef1 套件)
    """
    
    # 信號
    data_received = pyqtSignal(str, object)  # (topic, data_list)
    connection_status = pyqtSignal(str)       # 連接狀態
    error_occurred = pyqtSignal(str)          # 錯誤訊息
    
    # 訂閱的數據流
    TOPICS = [
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._client = None
        self._data_queue = Queue()
        
    def run(self):
        """執行緒主迴圈"""
        self._running = True
        
        if not WEBSOCKETS_AVAILABLE:
            self.error_occurred.emit("websockets 套件未安裝，請執行: pip install websockets")
            return
        
        self.connection_status.emit("正在初始化 F1 官方 API 連接...")
        print("[REALTIME] 初始化 F1 官方 SignalR 客戶端...")
        
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
                topics=self.TOPICS,
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
                            print(f"[REALTIME] 收到 {topic}: {len(data_list)} 筆記錄")
                    except Empty:
                        continue
                    except Exception as e:
                        print(f"[REALTIME] 處理隊列錯誤: {e}")
            
            queue_thread = threading.Thread(target=process_queue, daemon=True)
            queue_thread.start()
            
            # 運行客戶端 (阻塞)
            self._client.run()
            
        except KeyboardInterrupt:
            print("[REALTIME] 使用者中斷")
        except Exception as e:
            self.error_occurred.emit(f"連接錯誤: {str(e)}")
            print(f"[REALTIME] 連接錯誤: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._running = False
            self.connection_status.emit("連接已關閉")
    
    def stop(self):
        """停止執行緒"""
        self._running = False
        if self._client:
            self._client.stop()
        self.wait(3000)  # 等待最多 3 秒


class RealTimeLiveF1DataSource(QObject):
    """
    即時 Live F1 數據源
    
    通過 SignalR WebSocket 連接 F1 官方 Live Timing 服務
    """
    
    # 信號
    data_updated = pyqtSignal(str)  # 數據更新信號 (topic)
    connection_changed = pyqtSignal(str)  # 連接狀態變更
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據存儲 (保存最新狀態)
        self._position_data: Dict[str, Any] = {}  # driver_num -> position data
        self._timing_data: Dict[str, Any] = {}    # driver_num -> timing data
        self._car_data: Dict[str, Any] = {}       # driver_num -> car data
        self._timing_app_data: Dict[str, Any] = {}  # driver_num -> tyre data
        self._weather_data: Dict[str, Any] = {}
        self._track_status: str = "1"  # 1=綠旗
        self._race_control_messages: List[Dict] = []
        self._lap_count: Dict[str, Any] = {"CurrentLap": 0, "TotalLaps": 0}
        self._driver_list: Dict[str, Dict] = {}
        self._session_info: Dict[str, Any] = {}
        
        # 即時快照 (用於 UI 更新)
        self._current_snapshot: Dict[str, Any] = {
            "race_time": "",
            "race_time_seconds": 0.0,
            "drivers": {}
        }
        
        # Worker 執行緒
        self._worker: Optional[RealTimeLiveF1Worker] = None
        self._is_connected = False
        
        # 時間戳記錄
        self._last_update_time = datetime.now()
        
    def start_connection(self):
        """開始即時連接"""
        if self._worker is not None and self._worker.isRunning():
            print("[REALTIME_SOURCE] 連接已在運行中")
            return
        
        print("[REALTIME_SOURCE] 啟動即時連接...")
        
        self._worker = RealTimeLiveF1Worker(self)
        self._worker.data_received.connect(self._on_data_received)
        self._worker.connection_status.connect(self._on_connection_status)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()
        
    def stop_connection(self):
        """停止即時連接"""
        if self._worker is not None:
            print("[REALTIME_SOURCE] 停止即時連接...")
            self._worker.stop()
            self._worker = None
        self._is_connected = False
        
    def is_connected(self) -> bool:
        """檢查是否已連接"""
        return self._is_connected
    
    @pyqtSlot(str, object)
    def _on_data_received(self, topic: str, data_list):
        """處理接收到的數據 (來自 livef1 的格式: topic -> list of records)"""
        self._last_update_time = datetime.now()
        
        # livef1 返回的是 record list
        if not isinstance(data_list, list):
            data_list = [data_list]
        
        # 根據 topic 處理不同數據
        for record in data_list:
            if not isinstance(record, dict):
                continue
                
            if topic == "Position.z" or topic == "Position":
                self._process_position_record(record)
            elif topic == "CarData.z" or topic == "CarData":
                self._process_car_data_record(record)
            elif topic == "TimingData":
                self._process_timing_data_record(record)
            elif topic == "WeatherData":
                self._weather_data.update(record)
            elif topic == "TrackStatus":
                status = record.get("Status")
                if status:
                    self._track_status = str(status)
            elif topic == "RaceControlMessages":
                self._race_control_messages.append(record)
            elif topic == "LapCount":
                self._lap_count.update(record)
            elif topic == "DriverList":
                self._process_driver_list_record(record)
            elif topic == "SessionInfo":
                self._session_info.update(record)
            elif topic == "CurrentTyres":
                self._process_current_tyres_record(record)
            elif topic == "TyreStintSeries":
                self._process_tyre_stint_record(record)
            elif topic == "PitStopSeries":
                self._process_pit_stop_record(record)
        
        # 更新即時快照
        self._update_current_snapshot()
        
        # 發送更新信號
        self.data_updated.emit(topic)
    
    def _process_position_record(self, record: dict):
        """處理單筆位置數據 (livef1 格式)"""
        # livef1 Position.z 格式: {'SessionKey': ..., 'timestamp': ..., 'DriverNo': '1', 'Status': 'OnTrack', 'X': ..., 'Y': ..., 'Z': ...}
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._position_data:
            self._position_data[driver_num] = {}
        
        self._position_data[driver_num].update({
            "X": record.get("X", 0),
            "Y": record.get("Y", 0),
            "Z": record.get("Z", 0),
            "Status": record.get("Status", "OnTrack"),
            "timestamp": record.get("timestamp", "")
        })
    
    def _process_car_data_record(self, record: dict):
        """
        處理單筆車輛遙測數據
        
        支援兩種格式:
        1. 官方 SignalR (小寫): {'DriverNo': '1', 'speed': 320, 'rpm': 10500, ...}
        2. livef1 格式 (大寫): {'DriverNo': '1', 'Speed': 320, 'RPM': 10500, ...}
        """
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._car_data:
            self._car_data[driver_num] = {}
        
        # 支援大小寫欄位名 (優先使用小寫 - 官方格式)
        self._car_data[driver_num].update({
            "rpm": record.get("rpm") or record.get("RPM", 0),
            "speed": record.get("speed") or record.get("Speed", 0),
            "gear": record.get("gear") or record.get("nGear", 0),
            "throttle": record.get("throttle") or record.get("Throttle", 0),
            "brake": record.get("brake") or record.get("Brake", 0),
            "drs": record.get("drs") or record.get("DRS", 0)
        })
    
    def _process_timing_data_record(self, record: dict):
        """處理單筆計時數據 (livef1 格式)"""
        # livef1 TimingData 格式: {'SessionKey': ..., 'timestamp': ..., 'DriverNo': '81', 'Position': '1', 'GapToLeader': '+7.540', ...}
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._timing_data:
            self._timing_data[driver_num] = {}
        
        # 更新所有非空值
        for key, value in record.items():
            if key not in ["SessionKey", "timestamp"] and value is not None:
                self._timing_data[driver_num][key] = value
    
    def _process_timing_app_data_record(self, record: dict):
        """處理單筆輪胎策略數據 (livef1 格式)"""
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._timing_app_data:
            self._timing_app_data[driver_num] = {}
        
        # 更新輪胎數據
        for key, value in record.items():
            if key not in ["SessionKey", "timestamp"] and value is not None:
                self._timing_app_data[driver_num][key] = value
    
    def _process_driver_list_record(self, record: dict):
        """處理單筆車手資訊 (livef1 格式)"""
        # livef1 DriverList 格式: {'RacingNumber': '81', 'Tla': 'PIA', 'TeamName': 'McLaren', 'TeamColour': 'F47600', ...}
        driver_num = str(record.get("RacingNumber", ""))
        if not driver_num:
            return
        
        self._driver_list[driver_num] = {
            "tla": record.get("Tla", driver_num),
            "name": record.get("BroadcastName", driver_num),
            "full_name": record.get("FullName", ""),
            "team": record.get("TeamName", ""),
            "team_color": record.get("TeamColour", "CCCCCC"),
            "headshot_url": record.get("HeadshotUrl", "")
        }
    
    def _process_current_tyres_record(self, record: dict):
        """處理當前輪胎數據"""
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._timing_app_data:
            self._timing_app_data[driver_num] = {}
        
        self._timing_app_data[driver_num]["CurrentTyre"] = {
            "Compound": record.get("Compound", ""),
            "New": record.get("New", False),
            "TotalLaps": record.get("TotalLaps", 0)
        }
    
    def _process_tyre_stint_record(self, record: dict):
        """處理輪胎 stint 數據 (TyreStintSeries)"""
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._timing_app_data:
            self._timing_app_data[driver_num] = {}
        
        # TyreStintSeries 格式: {'DriverNo': '6', 'PitCount': '2', 'TotalLaps': 14}
        pit_count = record.get("PitCount", "0")
        if isinstance(pit_count, str):
            pit_count = int(pit_count) if pit_count.isdigit() else 0
        
        self._timing_app_data[driver_num]["PitCount"] = pit_count
        self._timing_app_data[driver_num]["TyreTotalLaps"] = record.get("TotalLaps", 0)
    
    def _process_pit_stop_record(self, record: dict):
        """處理進站數據 (PitStopSeries)"""
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._timing_app_data:
            self._timing_app_data[driver_num] = {}
        
        # 更新進站次數
        pit_count = record.get("PitCount", 0)
        if isinstance(pit_count, str):
            pit_count = int(pit_count) if pit_count.isdigit() else 0
        self._timing_app_data[driver_num]["PitCount"] = pit_count
    
    def _update_current_snapshot(self):
        """更新當前快照 (用於 UI 顯示)"""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"
        
        self._current_snapshot = {
            "race_time": time_str,
            "race_time_seconds": (now - datetime(now.year, now.month, now.day)).total_seconds(),
            "drivers": {}
        }
        
        # 合併所有數據源到 snapshot
        all_drivers = set(self._position_data.keys()) | set(self._timing_data.keys()) | set(self._driver_list.keys())
        
        for driver_num in all_drivers:
            driver_info = {}
            
            # 位置數據
            if driver_num in self._position_data:
                pos = self._position_data[driver_num]
                driver_info["x"] = pos.get("X")
                driver_info["y"] = pos.get("Y")
                driver_info["z"] = pos.get("Z")
                driver_info["status"] = pos.get("Status", "Unknown")
            
            # 計時數據 (livef1 格式是扁平的)
            if driver_num in self._timing_data:
                timing = self._timing_data[driver_num]
                
                # 直接取得 Position (livef1 格式)
                pos_value = timing.get("Position")
                if pos_value:
                    driver_info["position"] = int(pos_value) if str(pos_value).isdigit() else None
                
                driver_info["lap"] = timing.get("NumberOfLaps")
                
                # GapToLeader 和 IntervalToPositionAhead (livef1 格式是字串)
                gap = timing.get("GapToLeader")
                if gap:
                    driver_info["gap_to_leader_display"] = str(gap)
                
                interval = timing.get("IntervalToPositionAhead_Value")
                if interval:
                    driver_info["gap_to_ahead_display"] = str(interval)
                
                # LastLapTime (可能是嵌套或扁平)
                last_lap = timing.get("LastLapTime")
                if isinstance(last_lap, dict):
                    driver_info["last_lap_time"] = last_lap.get("Value")
                    driver_info["last_lap_personal_fastest"] = last_lap.get("PersonalFastest", False)
                    driver_info["last_lap_overall_fastest"] = last_lap.get("OverallFastest", False)
                elif last_lap:
                    driver_info["last_lap_time"] = str(last_lap)
                
                # BestLapTime
                best_lap = timing.get("BestLapTime")
                if isinstance(best_lap, dict):
                    driver_info["best_lap_time"] = best_lap.get("Value")
                elif best_lap:
                    driver_info["best_lap_time"] = str(best_lap)
                
                driver_info["in_pit"] = timing.get("InPit", False)
                driver_info["pit_out"] = timing.get("PitOut", False)
                driver_info["retired"] = timing.get("Retired", False)
                driver_info["stopped"] = timing.get("Stopped", False)
            
            # 遙測數據
            if driver_num in self._car_data:
                car = self._car_data[driver_num]
                driver_info["speed"] = car.get("speed")
                driver_info["rpm"] = car.get("rpm")
                driver_info["gear"] = car.get("gear")
                driver_info["throttle"] = car.get("throttle")
                driver_info["brake"] = car.get("brake")
                driver_info["drs"] = car.get("drs")
            
            # 輪胎數據 (來自 CurrentTyres 和 TyreStintSeries)
            if driver_num in self._timing_app_data:
                tyre_data = self._timing_app_data[driver_num]
                
                # 從 CurrentTyre 獲取 (來自 CurrentTyres topic)
                current_tyre = tyre_data.get("CurrentTyre", {})
                if current_tyre:
                    driver_info["tyre_compound"] = current_tyre.get("Compound", "")
                    driver_info["tyre_new"] = current_tyre.get("New", False)
                
                # 從 TyreStintSeries 獲取輪胎圈數和進站次數
                driver_info["tyre_laps"] = tyre_data.get("TyreTotalLaps", 0)
                driver_info["num_pit_stops"] = tyre_data.get("PitCount", 0)
            
            # 車手資訊
            if driver_num in self._driver_list:
                dl = self._driver_list[driver_num]
                driver_info["driver_tla"] = dl.get("tla", driver_num)
                driver_info["driver_name"] = dl.get("name", driver_num)
                driver_info["team_name"] = dl.get("team", "")
                driver_info["team_color"] = dl.get("team_color", "CCCCCC")
            else:
                driver_info["driver_tla"] = driver_num
            
            driver_info["driver_number"] = driver_num
            self._current_snapshot["drivers"][driver_num] = driver_info
    
    @pyqtSlot(str)
    def _on_connection_status(self, status: str):
        """處理連接狀態變更"""
        print(f"[REALTIME_SOURCE] 連接狀態: {status}")
        if "成功" in status or "接收中" in status:
            self._is_connected = True
        self.connection_changed.emit(status)
    
    @pyqtSlot(str)
    def _on_error(self, error: str):
        """處理錯誤"""
        print(f"[REALTIME_SOURCE] 錯誤: {error}")
        self._is_connected = False
        self.connection_changed.emit(f"錯誤: {error}")
    
    # === 公開 API (與歷史數據源相容) ===
    
    def get_current_snapshot(self) -> Dict[str, Any]:
        """獲取當前快照"""
        return self._current_snapshot
    
    def get_weather_data(self) -> Dict[str, Any]:
        """獲取天氣數據"""
        return self._weather_data
    
    def get_track_status(self) -> str:
        """獲取賽道狀態"""
        return self._track_status
    
    def get_lap_count(self) -> Dict[str, Any]:
        """獲取圈數"""
        return self._lap_count
    
    def get_race_control_messages(self) -> List[Dict]:
        """獲取比賽控制訊息"""
        return self._race_control_messages
    
    def get_driver_list(self) -> Dict[str, Dict]:
        """獲取車手列表"""
        return self._driver_list
    
    def get_tyre_state(self) -> Dict[str, Dict]:
        """獲取輪胎狀態"""
        result = {}
        for driver_num, app_data in self._timing_app_data.items():
            stints = app_data.get("Stints", [])
            if isinstance(stints, list) and stints:
                last_stint = stints[-1]
                result[driver_num] = {
                    "compound": last_stint.get("Compound", "UNKNOWN"),
                    "new": last_stint.get("New", False),
                    "tyre_age": last_stint.get("TotalLaps", 0),
                    "stint_count": len(stints)
                }
            elif isinstance(stints, dict):
                # 增量格式
                sorted_keys = sorted(stints.keys(), key=int)
                if sorted_keys:
                    last_stint = stints[sorted_keys[-1]]
                    result[driver_num] = {
                        "compound": last_stint.get("Compound", "UNKNOWN"),
                        "new": last_stint.get("New", False),
                        "tyre_age": last_stint.get("TotalLaps", 0),
                        "stint_count": len(sorted_keys)
                    }
        return result
    
    def get_session_info(self) -> Dict[str, Any]:
        """獲取賽事資訊"""
        return self._session_info


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
        """
        處理並對齊所有數據源 - 展開內層數據以獲得更高頻率的更新
        
        Position 和 CarData 的 jsonStream 格式中，每個外層記錄包含多個內層時間點，
        本方法會展開這些內層數據，實現約 3-4 Hz 的更新頻率。
        """
        from datetime import datetime
        
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
            print("[PROCESSOR] ❌ Position 數據為空！")
            return

        # 建立 Timing 索引 (這個不需要展開，是事件驅動的)
        self._build_timing_index(timing_data)
        
        # 建立展開的 CarData 索引 (使用內層 UTC 時間戳)
        self._build_expanded_cardata_index(cardata)

        # 展開 Position 數據
        expanded_positions = self._expand_position_data(position_data)
        print(f"[PROCESSOR] Position 展開後: {len(expanded_positions)} 個時間點")

        aligned_count = 0
        skipped_no_lap = 0
        
        print(f"[PROCESSOR] 🔍 過濾並對齊資料...")
        print(f"[PROCESSOR] 策略: 只保留至少有一位車手有圈數的時間點")

        for pos_entry in expanded_positions:
            timestamp = pos_entry['timestamp']  # 比賽時間格式 "HH:MM:SS.mmm"
            utc_timestamp = pos_entry.get('utc_timestamp')  # UTC 時間戳
            entries = pos_entry['entries']
            
            if not isinstance(entries, dict):
                continue

            # 先查找 Timing 資料，檢查是否有圈數
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
                        driver_info.update(timing_state)

                # 使用展開的 CarData (優先用 UTC 時間戳匹配)
                cardata_state = self._find_nearest_cardata(timestamp, driver_num)
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
            duration = self._aligned_snapshots[-1]['race_time_seconds'] - self._aligned_snapshots[0]['race_time_seconds']
            freq = aligned_count / duration if duration > 0 else 0
            print(f"[PROCESSOR]    時間範圍: {first_time} ~ {last_time}")
            print(f"[PROCESSOR]    更新頻率: {freq:.2f} Hz (每秒 {freq:.1f} 次更新)")
        
        self._calculate_rankings_and_gaps()
        self._process_pit_and_tyre_data()
    
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
        
        展開為:
        [
            {"timestamp": "00:00:02.043", "utc_timestamp": "...", "entries": {...}},
            {"timestamp": "00:00:02.403", "utc_timestamp": "...", "entries": {...}},
            ...
        ]
        """
        from datetime import datetime
        
        expanded = []
        base_utc = None  # 用於計算相對時間
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
                        # 解析 UTC 時間戳
                        utc_str = inner_utc.replace('Z', '+00:00')
                        if '.' in utc_str:
                            # 處理微秒
                            parts = utc_str.split('.')
                            if len(parts[1]) > 7:
                                utc_str = parts[0] + '.' + parts[1][:6] + '+00:00'
                        
                        utc_dt = datetime.fromisoformat(utc_str.replace('+00:00', ''))
                        
                        # 設置基準時間
                        if base_utc is None:
                            base_utc = utc_dt
                            base_race_seconds = self._time_str_to_seconds(outer_timestamp)
                        
                        # 計算相對時間
                        delta_seconds = (utc_dt - base_utc).total_seconds()
                        race_seconds = base_race_seconds + delta_seconds
                        
                        # 格式化為比賽時間
                        hours = int(race_seconds // 3600)
                        minutes = int((race_seconds % 3600) // 60)
                        seconds = race_seconds % 60
                        race_time = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
                        
                    except Exception as e:
                        # 如果解析失敗，使用外層時間戳
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
        
        # 按時間排序
        expanded.sort(key=lambda x: x.get('race_time_seconds', 0))
        
        return expanded
    
    def _build_expanded_cardata_index(self, cardata: List[Dict]):
        """
        建立展開的 CarData 索引，使用內層 UTC 時間戳
        """
        import copy
        from datetime import datetime
        
        print(f"[PROCESSOR] 展開 CarData 內層數據...")
        
        # 展開所有 CarData 條目
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
                
                # 計算比賽時間
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
        
        # 按時間排序
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
                speed = channels.get('2') or channels.get(2)
                
                if speed is not None:
                    if driver_num not in latest_driver_state:
                        latest_driver_state[driver_num] = {}
                    latest_driver_state[driver_num]['speed'] = speed
            
            self._expanded_cardata_index[timestamp] = copy.deepcopy(latest_driver_state)
            self._expanded_cardata_timestamps.append(timestamp)
        
        print(f"[PROCESSOR] ✅ CarData 展開完成: {len(expanded_entries)} 個時間點")
        if self._expanded_cardata_timestamps:
            print(f"  第一個: {self._expanded_cardata_timestamps[0]}")
            print(f"  最後一個: {self._expanded_cardata_timestamps[-1]}")
    
    def _find_nearest_cardata(self, timestamp: str, driver_num: str) -> Optional[Dict]:
        """查找最接近的 CarData 狀態"""
        if not hasattr(self, '_expanded_cardata_timestamps') or not self._expanded_cardata_timestamps:
            # 回退到舊方法
            nearest_ts = self._find_nearest_timestamp(timestamp, self._cardata_timestamps)
            if nearest_ts and nearest_ts in self._cardata_index_full:
                return self._cardata_index_full[nearest_ts].get(driver_num)
            return None
        
        # 使用展開的索引
        nearest_ts = self._find_nearest_timestamp(timestamp, self._expanded_cardata_timestamps)
        if nearest_ts and nearest_ts in self._expanded_cardata_index:
            return self._expanded_cardata_index[nearest_ts].get(driver_num)
        return None

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
            return "1"  # 預設綠旗
        
        # 將目標時間戳轉換為秒數進行比較
        target_seconds = self._time_str_to_seconds(timestamp)
        if target_seconds is None:
            return "1"
        
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
                
                # === Sector 時間 (S1/S2/S3) ===
                sectors = driver_data.get('Sectors', {})
                if isinstance(sectors, dict):
                    # Sector 0 = S1, Sector 1 = S2, Sector 2 = S3
                    for sector_idx, sector_key in enumerate(['0', '1', '2']):
                        sector_data = sectors.get(sector_key, {})
                        if isinstance(sector_data, dict) and sector_data.get('Value'):
                            sector_name = f's{sector_idx + 1}'  # s1, s2, s3
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
        
        # 車隊顏色
        self.team_colors = {
            'Red Bull Racing': '#3671C6',
            'Ferrari': '#E8002D',
            'Mercedes': '#27F4D2',
            'McLaren': '#FF8000',
            'Aston Martin': '#229971',
            'Alpine': '#FF87BC',
            'Williams': '#64C4FF',
            'RB': '#6692FF',
            'Kick Sauber': '#52E252',
            'Haas F1 Team': '#B6BABD',
            'default': '#888888'
        }
        
        # 車號對應顏色
        self.driver_colors = {
            '1': '#3671C6', '11': '#3671C6',
            '16': '#E8002D', '55': '#E8002D',
            '44': '#27F4D2', '63': '#27F4D2',
            '4': '#FF8000', '81': '#FF8000',
            '14': '#229971', '18': '#229971',
            '10': '#FF87BC', '31': '#FF87BC',
            '23': '#64C4FF', '2': '#64C4FF',
            '22': '#6692FF', '30': '#6692FF',
            '77': '#52E252', '24': '#52E252',
            '20': '#B6BABD', '27': '#B6BABD',
        }
        
        # 車手資訊 (用於顏色查詢)
        self.driver_info: Dict[str, Dict[str, Any]] = {}
        
        # 彎道資料 (FastF1 official corners)
        self.official_corners: List[Dict[str, Any]] = []

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
            # 過濾 DNF/Retired 車手
            status = driver_data.get('status', '')
            if status and status.upper() in ('DNF', 'RETIRED', 'OUT'):
                continue
            
            # 直接使用 Position 資料中的真實 X/Y 座標
            x = driver_data.get('x')
            y = driver_data.get('y')
            
            # 如果沒有座標，跳過
            if x is None or y is None:
                continue
            
            # 獲取車手縮寫 (TLA)，如果沒有則使用車號
            driver_tla = driver_data.get('driver_tla', driver_num)
            
            markers.append({
                'driver': driver_num,
                'driver_tla': driver_tla,
                'x': x,
                'y': y,
                'position': driver_data.get('position'),
                'status': driver_data.get('status', 'Unknown'),
                'team_color': driver_data.get('team_color')
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
            self._draw_corner_markers(painter, transform)  # 繪製彎道編號 (淺綠色)
            self._draw_sector_markers(painter, transform)  # 繪製 FIN/S1/S2 標記
            self._draw_driver_markers(painter, transform)
        else:
            painter.setPen(QColor(200, 200, 200))
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "載入賽道輪廓中...")

        # 圖例已取消

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
        
        # 起始點圓點已取消，改由 _draw_sector_markers 顯示 FIN/S1/S2

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
        """繪製車手標記 - 圓點 + 連接線 + Flag 標籤"""
        if not self._marker_positions:
            return

        for marker in self._marker_positions:
            screen_x, screen_y = self._world_to_screen((marker['x'], marker['y']), transform)
            driver_num = marker.get('driver', '')
            driver_tla = marker.get('driver_tla', driver_num)
            
            # 獲取車手顏色
            color = self._get_driver_color(driver_num, marker)
            
            # 1. 繪製賽道上的小圓點
            dot_radius = 5
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawEllipse(QPointF(screen_x, screen_y), dot_radius, dot_radius)
            
            # 2. 計算 Flag 位置 (在圓點旁邊偏移)
            # 根據位置決定偏移方向，避免 Flag 重疊
            position = marker.get('position', 99)
            offset_x = 25
            offset_y = -15 + (position % 5) * 5  # 輕微錯開
            
            flag_x = screen_x + offset_x
            flag_y = screen_y + offset_y
            
            # 3. 繪製連接線 (從圓點到 Flag)
            painter.setPen(QPen(color, 1))
            painter.drawLine(QPointF(screen_x, screen_y), QPointF(flag_x, flag_y))
            
            # 4. 繪製 Flag 標籤
            self._draw_flag_label(painter, flag_x, flag_y, driver_tla, color)
    
    def _get_driver_color(self, driver_num: str, marker: dict = None) -> QColor:
        """獲取車手顏色"""
        # 從 marker 的 team_color
        if marker:
            tc = marker.get('team_color')
            if tc:
                color_str = f'#{tc}' if not tc.startswith('#') else tc
                return QColor(color_str)
        
        # 從 driver_info
        if driver_num in self.driver_info:
            team = self.driver_info[driver_num].get('team', '')
            if team in self.team_colors:
                return QColor(self.team_colors[team])
        
        # 從車號顏色映射
        if driver_num in self.driver_colors:
            return QColor(self.driver_colors[driver_num])
        
        return QColor(self.team_colors['default'])
    
    def _draw_flag_label(self, painter: QPainter, x: float, y: float, tla: str, color: QColor):
        """繪製 Flag 標籤"""
        w, h = 30, 14
        flag_x = x
        flag_y = y - h / 2
        
        # 繪製背景矩形
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(QRectF(flag_x, flag_y, w, h))
        
        # 繪製文字
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        rect = painter.fontMetrics().boundingRect(tla)
        text_x = flag_x + (w - rect.width()) / 2
        text_y = flag_y + h - 3
        painter.drawText(int(text_x), int(text_y), tla)
    
    def set_driver_info(self, driver_info: Dict):
        """設置車手資訊"""
        self.driver_info = driver_info or {}
    
    def set_official_corners(self, corners: List[Dict[str, Any]]):
        """設置彎道資料 (FastF1 official corners)"""
        self.official_corners = corners or []
        if self.official_corners:
            print(f"[TRACK_MAP] 設置 {len(self.official_corners)} 個彎道標記")
        self.update()
    
    def _draw_corner_markers(self, painter: QPainter, transform: Dict[str, float]):
        """繪製彎道編號標記 - 淺綠色線條 + 標籤 (與 FIN/S1/S2 一致)"""
        if not self.official_corners or not self.track_points:
            return
        
        # 淺綠色
        corner_color = QColor(144, 238, 144)  # LightGreen
        
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        for corner in self.official_corners:
            corner_num = corner.get('number', 0)
            corner_x = corner.get('x', 0)
            corner_y = corner.get('y', 0)
            corner_distance = corner.get('distance', 0)
            
            if corner_x == 0 and corner_y == 0:
                # 如果沒有 x/y 座標，嘗試從 distance 計算
                if corner_distance > 0 and self.track_length > 0:
                    progress = corner_distance / self.track_length
                    target_distance = progress * self.track_length
                    
                    # 找最近的賽道點
                    for pt in self.track_points:
                        if pt['distance'] >= target_distance:
                            corner_x = pt['x']
                            corner_y = pt['y']
                            break
            
            if corner_x == 0 and corner_y == 0:
                continue
            
            # 找最近的賽道點索引來計算法線方向
            nearest_idx = 0
            min_dist = float('inf')
            for i, pt in enumerate(self.track_points):
                dx = corner_x - pt['x']
                dy = corner_y - pt['y']
                dist = dx*dx + dy*dy
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = i
            
            # 取得相鄰點來計算切線方向
            prev_idx = max(0, nearest_idx - 1)
            next_idx = min(len(self.track_points) - 1, nearest_idx + 1)
            prev_pt = self.track_points[prev_idx]
            next_pt = self.track_points[next_idx]
            
            # 計算賽道切線方向
            dx = next_pt['x'] - prev_pt['x']
            dy = next_pt['y'] - prev_pt['y']
            length = (dx**2 + dy**2)**0.5
            if length == 0:
                continue
            
            # 法線方向 (垂直於賽道)
            nx = -dy / length
            ny = dx / length
            
            # 轉換為螢幕座標
            screen_x, screen_y = self._world_to_screen((corner_x, corner_y), transform)
            
            line_length = 10  # 線條長度 (像素)
            
            # 繪製垂直於賽道的淺綠色線條
            painter.setPen(QPen(corner_color, 1))  # 寬度 1 (原本 2)
            painter.drawLine(
                QPointF(screen_x - nx * line_length, screen_y - ny * line_length),
                QPointF(screen_x + nx * line_length, screen_y + ny * line_length)
            )
            
            # 繪製彎道編號標籤 (在線條旁邊)
            painter.setPen(corner_color)
            label = str(corner_num)
            text_rect = painter.fontMetrics().boundingRect(label)
            
            # 標籤偏移，放在法線方向外側
            label_x = screen_x + nx * (line_length + 6) - text_rect.width() / 2
            label_y = screen_y + ny * (line_length + 6) + text_rect.height() / 4
            
            painter.drawText(int(label_x), int(label_y), label)
    
    def _draw_sector_markers(self, painter: QPainter, transform: Dict[str, float]):
        """繪製 FIN/S1/S2 標記 - 線條方式 (與圓形賽道圖一致)"""
        if not self.track_points or len(self.track_points) < 3:
            return
        
        # 計算 Sector 位置 (約均分賽道)
        # FIN = 起點 (0%), S1 = 33%, S2 = 66%
        sector_positions = [
            ('FIN', 0.0),
            ('S1', 0.33),
            ('S2', 0.66),
        ]
        
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        for label, progress in sector_positions:
            # 找到賽道上對應進度的點和相鄰點
            target_distance = progress * self.track_length
            
            # 找最近的賽道點索引
            nearest_idx = 0
            for i, pt in enumerate(self.track_points):
                if pt['distance'] >= target_distance:
                    nearest_idx = i
                    break
            
            # 取得當前點和相鄰點來計算切線方向
            curr_pt = self.track_points[nearest_idx]
            prev_idx = max(0, nearest_idx - 1)
            next_idx = min(len(self.track_points) - 1, nearest_idx + 1)
            prev_pt = self.track_points[prev_idx]
            next_pt = self.track_points[next_idx]
            
            # 計算賽道切線方向
            dx = next_pt['x'] - prev_pt['x']
            dy = next_pt['y'] - prev_pt['y']
            length = (dx**2 + dy**2)**0.5
            if length == 0:
                continue
            
            # 法線方向 (垂直於賽道)
            nx = -dy / length
            ny = dx / length
            
            # 轉換為螢幕座標
            screen_x, screen_y = self._world_to_screen((curr_pt['x'], curr_pt['y']), transform)
            
            # 計算法線在螢幕上的方向 (需要考慮 scale)
            scale = transform['scale']
            line_length = 15  # 線條長度 (像素)
            
            # 繪製垂直於賽道的線條
            start_x = screen_x - nx * scale * 0.5 * line_length / scale
            start_y = screen_y - ny * scale * 0.5 * line_length / scale
            end_x = screen_x + nx * scale * 0.5 * line_length / scale
            end_y = screen_y + ny * scale * 0.5 * line_length / scale
            
            # 簡化：直接用固定長度的線
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(
                QPointF(screen_x - nx * line_length, screen_y - ny * line_length),
                QPointF(screen_x + nx * line_length, screen_y + ny * line_length)
            )
            
            # 繪製標籤 (在線條旁邊)
            painter.setPen(QColor(255, 255, 255))
            text_rect = painter.fontMetrics().boundingRect(label)
            
            # 標籤偏移，放在法線方向外側
            label_x = screen_x + nx * (line_length + 8) - text_rect.width() / 2
            label_y = screen_y + ny * (line_length + 8) + text_rect.height() / 4
            
            painter.drawText(int(label_x), int(label_y), label)

    def _draw_legend(self, painter: QPainter):
        """圖例已取消"""
        pass  # 不再繪製圖例

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


class CircleMapWidget(QWidget):
    """
    圓形賽道地圖 Widget
    
    以圓環形式顯示所有車手在賽道上的相對位置。
    使用真實 X/Y 座標計算車手在賽道上的位置，
    並映射到圓環上顯示。
    
    參考 Circle Map Viewer 設計。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        
        # 車手數據
        self.driver_positions: Dict[str, Dict[str, Any]] = {}
        self.driver_info: Dict[str, Dict[str, Any]] = {}
        
        # 賽道資訊
        self.track_points: List[Dict[str, float]] = []  # 賽道輪廓點 [{x, y, distance}]
        self.track_length = 5380.0
        self.total_laps = 55
        self.current_lap = 0
        self.race_time_str = "00:00:00"
        
        # 車隊顏色
        self.team_colors = {
            'Red Bull Racing': '#3671C6',
            'Ferrari': '#E8002D',
            'Mercedes': '#27F4D2',
            'McLaren': '#FF8000',
            'Aston Martin': '#229971',
            'Alpine': '#FF87BC',
            'Williams': '#64C4FF',
            'RB': '#6692FF',
            'Kick Sauber': '#52E252',
            'Haas F1 Team': '#B6BABD',
            'default': '#888888'
        }
        
        # 車號對應顏色
        self.driver_colors = {
            '1': '#3671C6', '11': '#3671C6',
            '16': '#E8002D', '55': '#E8002D',
            '44': '#27F4D2', '63': '#27F4D2',
            '4': '#FF8000', '81': '#FF8000',
            '14': '#229971', '18': '#229971',
            '10': '#FF87BC', '31': '#FF87BC',
            '23': '#64C4FF', '2': '#64C4FF',
            '22': '#6692FF', '30': '#6692FF',
            '77': '#52E252', '24': '#52E252',
            '20': '#B6BABD', '27': '#B6BABD',
        }
        
        print("[CIRCLE_MAP] CircleMapWidget 初始化完成 (GPS 座標模式)")
    
    def load_track_data(self, track_data: Dict):
        """載入賽道輪廓數據"""
        try:
            position_records = track_data.get('position_records', [])
            if not position_records:
                print("[CIRCLE_MAP] ⚠️ 無賽道輪廓數據")
                return
            
            self.track_points = []
            total_distance = 0.0
            prev_x, prev_y = None, None
            
            for record in position_records:
                x = record.get('position_x') or record.get('x')
                y = record.get('position_y') or record.get('y')
                if x is None or y is None:
                    continue
                
                # 計算累積距離
                if prev_x is not None:
                    dx = x - prev_x
                    dy = y - prev_y
                    total_distance += (dx**2 + dy**2)**0.5
                
                self.track_points.append({
                    'x': x, 'y': y, 'distance': total_distance
                })
                prev_x, prev_y = x, y
            
            if self.track_points:
                self.track_length = self.track_points[-1]['distance']
                print(f"[CIRCLE_MAP] ✅ 賽道輪廓載入: {len(self.track_points)} 點, 長度 {self.track_length:.0f}m")
            
        except Exception as e:
            print(f"[CIRCLE_MAP] ❌ 載入賽道輪廓失敗: {e}")
    
    def set_track_length(self, length: float):
        if length and length > 0:
            self.track_length = length
    
    def set_total_laps(self, laps: int):
        if laps and laps > 0:
            self.total_laps = laps
    
    def set_driver_info(self, driver_info: Dict):
        self.driver_info = driver_info or {}
    
    def update_positions(self, drivers_data: Dict, current_lap: int = 0, race_time: str = "00:00:00"):
        """更新車手位置 - 過濾 DNF 車手"""
        # 過濾掉 DNF/Retired 車手
        if drivers_data:
            filtered_drivers = {}
            for driver_num, driver_data in drivers_data.items():
                status = driver_data.get('status', '')
                if status and status.upper() in ('DNF', 'RETIRED', 'OUT'):
                    continue
                filtered_drivers[driver_num] = driver_data
            self.driver_positions = filtered_drivers
        else:
            self.driver_positions = {}
        
        self.current_lap = current_lap
        self.race_time_str = race_time
        self.update()
    
    def paintEvent(self, event):
        """繪製圓形賽道地圖"""
        import math
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        width = self.width()
        height = self.height()
        cx = width / 2
        cy = height / 2
        
        # 圓環尺寸
        margin = 60  # 縮小 margin 讓外圈更大
        radius = min(width, height) / 2 - margin
        inner_radius = radius * 0.85  # 軌道寬度
        track_center_r = (radius + inner_radius) / 2  # 軌道中心線半徑
        
        # 繪製賽道圓環
        self._draw_track_ring(painter, cx, cy, radius, inner_radius)
        
        # 繪製 Sector 標記
        self._draw_sector_markers(painter, cx, cy, radius)
        
        # 繪製車手標記
        self._draw_driver_markers(painter, cx, cy, radius, inner_radius, track_center_r)
        
        # 繪製中央資訊
        self._draw_center_info(painter, cx, cy, inner_radius)
    
    def _draw_track_ring(self, painter: QPainter, cx: float, cy: float, 
                         outer_r: float, inner_r: float):
        """繪製賽道圓環"""
        # 外環
        painter.setPen(QPen(QColor(80, 80, 80), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), outer_r, outer_r)
        
        # 內環
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)
        
        # 軌道填充
        path = QPainterPath()
        path.addEllipse(QPointF(cx, cy), outer_r, outer_r)
        inner_path = QPainterPath()
        inner_path.addEllipse(QPointF(cx, cy), inner_r, inner_r)
        track_path = path - inner_path
        
        painter.setBrush(QBrush(QColor(50, 50, 50, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(track_path)
    
    def _draw_sector_markers(self, painter: QPainter, cx: float, cy: float, outer_r: float):
        """繪製 Sector 標記"""
        import math
        
        sectors = [
            ('FIN', -90),
            ('S1', 30),
            ('S2', 150),
        ]
        
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        for label, angle_deg in sectors:
            angle_rad = math.radians(angle_deg)
            
            # 線條從外緣向外
            start_x = cx + outer_r * math.cos(angle_rad)
            start_y = cy + outer_r * math.sin(angle_rad)
            end_x = cx + (outer_r + 10) * math.cos(angle_rad)
            end_y = cy + (outer_r + 10) * math.sin(angle_rad)
            
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
            
            # 標籤
            label_r = outer_r + 22
            label_x = cx + label_r * math.cos(angle_rad)
            label_y = cy + label_r * math.sin(angle_rad)
            
            painter.setPen(QColor(255, 255, 255))
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(int(label_x - text_rect.width()/2), 
                           int(label_y + text_rect.height()/4), label)
    
    def _draw_driver_markers(self, painter: QPainter, cx: float, cy: float,
                             outer_r: float, inner_r: float, track_r: float):
        """繪製車手標記 - 使用真實座標計算位置"""
        import math
        
        if not self.driver_positions:
            return
        
        # 收集所有車手資料並計算角度
        markers = []
        
        for driver_num, data in self.driver_positions.items():
            x = data.get('x')
            y = data.get('y')
            position = data.get('position', 99)
            gap_str = data.get('gap_to_leader_display', '')
            driver_tla = data.get('driver_tla', driver_num)
            color = self._get_driver_color(driver_num, data)
            
            # 計算角度 (基於座標或名次)
            if x is not None and y is not None and self.track_points:
                # 使用真實座標
                angle_deg = self._xy_to_angle(x, y)
            else:
                # 無座標時使用名次計算
                angle_deg = -90 + (position - 1) * (330 / 20)
            
            markers.append({
                'driver_num': driver_num,
                'driver_tla': driver_tla,
                'position': position,
                'gap_str': gap_str,
                'angle_deg': angle_deg,
                'color': color
            })
        
        # 按位置排序 (P1 在最上層)
        markers.sort(key=lambda x: -x['position'])
        
        # 繪製所有車手 (允許重疊，固定半徑)
        for m in markers:
            angle_rad = math.radians(m['angle_deg'])
            color = QColor(m['color'])
            
            # 在軌道上的彩色短線
            track_band = (outer_r - inner_r) / 2
            line_inner = track_r - track_band * 0.4
            line_outer = track_r + track_band * 0.4
            
            inner_x = cx + line_inner * math.cos(angle_rad)
            inner_y = cy + line_inner * math.sin(angle_rad)
            outer_x = cx + line_outer * math.cos(angle_rad)
            outer_y = cy + line_outer * math.sin(angle_rad)
            
            # 繪製軌道上的彩色標記線
            painter.setPen(QPen(color, 4))
            painter.drawLine(QPointF(inner_x, inner_y), QPointF(outer_x, outer_y))
            
            # Flag 位置 (編短距離避免超出視窗)
            flag_r = outer_r + 12
            flag_x = cx + flag_r * math.cos(angle_rad)
            flag_y = cy + flag_r * math.sin(angle_rad)
            
            # 連接線 (從軌道外緣到 Flag)
            painter.setPen(QPen(color, 2))
            painter.drawLine(QPointF(outer_x, outer_y), QPointF(flag_x, flag_y))
            
            # 繪製 Flag
            self._draw_flag(painter, flag_x, flag_y, m['driver_tla'], color)
            
            # 秒數顯示已取消
    
    def _xy_to_angle(self, x: float, y: float) -> float:
        """將 X/Y 座標轉換為圓環角度"""
        import math
        
        if not self.track_points:
            return -90  # 預設頂部
        
        # 找最近的賽道點
        min_dist = float('inf')
        nearest_idx = 0
        
        for i, pt in enumerate(self.track_points):
            dx = x - pt['x']
            dy = y - pt['y']
            dist = dx*dx + dy*dy
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        # 計算在賽道上的進度 (0-1)
        track_distance = self.track_points[nearest_idx]['distance']
        progress = track_distance / self.track_length if self.track_length > 0 else 0
        
        # 轉換為角度 (-90 為頂部/終點線，順時針增加)
        # progress=0 (起點) → -90°
        # progress=0.5 → 90° (底部)
        # progress=1 (終點) → 270° → -90°
        angle_deg = -90 + progress * 360
        
        return angle_deg
    
    def _calculate_offsets(self, markers: list) -> list:
        """計算錯開偏移避免重疊"""
        offsets = [0] * len(markers)
        min_angle = 10
        step = 22
        
        for i in range(1, len(markers)):
            diff = abs(markers[i]['angle_deg'] - markers[i-1]['angle_deg'])
            if diff < min_angle:
                prev = offsets[i-1]
                if prev == 0:
                    offsets[i] = step
                elif prev > 0:
                    offsets[i] = prev + step
                else:
                    offsets[i] = prev - step
        
        return offsets
    
    def _get_driver_color(self, driver_num: str, data: dict = None) -> str:
        """獲取車手顏色"""
        # 從數據中的 team_color
        if data:
            tc = data.get('team_color')
            if tc:
                return f'#{tc}' if not tc.startswith('#') else tc
        
        # driver_info
        if driver_num in self.driver_info:
            team = self.driver_info[driver_num].get('team', '')
            if team in self.team_colors:
                return self.team_colors[team]
        
        # 車號顏色
        if driver_num in self.driver_colors:
            return self.driver_colors[driver_num]
        
        return self.team_colors['default']
    
    def _draw_flag(self, painter: QPainter, x: float, y: float, tla: str, color: QColor):
        """繪製 Flag 標籤"""
        w, h = 28, 12
        flag_x = x - w/2
        flag_y = y - h/2
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(QRectF(flag_x, flag_y, w, h))
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        
        rect = painter.fontMetrics().boundingRect(tla)
        painter.drawText(int(flag_x + (w - rect.width())/2), int(flag_y + h - 2), tla)
    
    def _draw_gap(self, painter: QPainter, x: float, y: float, gap_str: str):
        """繪製秒數標籤"""
        display = gap_str
        if not gap_str.endswith('s') and 'LAP' not in gap_str.upper():
            display = f"+{gap_str}s" if not gap_str.startswith('+') else f"{gap_str}s"
        
        painter.setPen(QColor(180, 180, 180))
        font = QFont()
        font.setPointSize(7)
        painter.setFont(font)
        
        rect = painter.fontMetrics().boundingRect(display)
        painter.drawText(int(x - rect.width()/2), int(y + rect.height()/4), display)
    
    def _draw_center_info(self, painter: QPainter, cx: float, cy: float, inner_r: float):
        """繪製中央資訊"""
        # 圈數
        lap_text = f"Lap {self.current_lap}/{self.total_laps}"
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        
        rect = painter.fontMetrics().boundingRect(lap_text)
        painter.drawText(int(cx - rect.width()/2), int(cy - 10), lap_text)
        
        # 時間
        font.setPointSize(14)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 200))
        
        rect = painter.fontMetrics().boundingRect(self.race_time_str)
        painter.drawText(int(cx - rect.width()/2), int(cy + 20), self.race_time_str)


# ============================================================
# Lap Time Distribution Widget - 單圈時間分佈視覺化
# ============================================================

class LapTimeDistributionWidget(QWidget):
    """
    單圈時間分佈視覺化 Widget
    
    顯示所有車手的圈速差距分佈：
    - Y 軸：以最快圈速為基準，向下遞增顯示差距
    - 左側：Y 軸刻度
    - 中間：車隊顏色圓點 (可重疊) + 連接線 + Flag 標籤 (避免重疊)
    - 右側：輪胎配方圓形標記
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 300)  # 增加最小寬度
        
        # 車手數據: {driver_num: {tla, lap_time, gap, team_color, compound}}
        self._driver_data: Dict[str, Dict[str, Any]] = {}
        self._fastest_time: float = 0.0  # 最快圈速 (秒)
        self._fastest_time_str: str = ""  # 最快圈速 (格式化字串)
        self._fastest_driver: str = ""  # 最快車手
        
        # 車隊顏色
        self.team_colors = {
            'Red Bull Racing': '#3671C6',
            'Ferrari': '#E8002D',
            'Mercedes': '#27F4D2',
            'McLaren': '#FF8000',
            'Aston Martin': '#229971',
            'Alpine': '#FF87BC',
            'Williams': '#64C4FF',
            'RB': '#6692FF',
            'Kick Sauber': '#52E252',
            'Haas F1 Team': '#B6BABD',
            'default': '#888888'
        }
        
        # 輪胎顏色
        self.tyre_colors = {
            'SOFT': '#FF3333',
            'MEDIUM': '#FFDD00',
            'HARD': '#FFFFFF',
            'INTERMEDIATE': '#43B02A',
            'WET': '#0066FF',
            'UNKNOWN': '#888888'
        }
        
        print("[LAP_TIME_DIST] LapTimeDistributionWidget 初始化完成")
    
    def update_data(self, drivers_data: Dict[str, Dict[str, Any]]):
        """
        更新車手圈速數據
        
        Args:
            drivers_data: {driver_num: {
                'driver_tla': str,
                'best_lap_time': float (秒) 或 str,
                'last_lap_time': float (秒) 或 str,
                'team_color': str,
                'compound': str (SOFT/MEDIUM/HARD/...),
                'status': str (可選, DNF/RETIRED/OUT 會被過濾)
            }}
        """
        self._driver_data = {}
        self._fastest_time = float('inf')
        self._fastest_driver = ""
        
        for driver_num, data in drivers_data.items():
            # 過濾 DNF/Retired 車手
            status = data.get('status', '')
            if status and status.upper() in ('DNF', 'RETIRED', 'OUT'):
                continue
            
            # 解析圈速 (優先使用 best_lap_time，其次 last_lap_time)
            lap_time = data.get('best_lap_time') or data.get('last_lap_time')
            if lap_time is None:
                continue
            
            # 轉換為秒數
            lap_time_sec = self._parse_lap_time(lap_time)
            if lap_time_sec is None or lap_time_sec <= 0:
                continue
            
            self._driver_data[driver_num] = {
                'driver_tla': data.get('driver_tla', driver_num),
                'lap_time_sec': lap_time_sec,
                'team_color': data.get('team_color', '888888'),
                'compound': data.get('compound', 'UNKNOWN'),
            }
            
            # 更新最快圈速
            if lap_time_sec < self._fastest_time:
                self._fastest_time = lap_time_sec
                self._fastest_driver = driver_num
        
        # 計算差距
        for driver_num, data in self._driver_data.items():
            data['gap'] = data['lap_time_sec'] - self._fastest_time
        
        # 格式化最快圈速
        if self._fastest_time < float('inf'):
            self._fastest_time_str = self._format_lap_time(self._fastest_time)
        else:
            self._fastest_time_str = "--:--.---"
        
        self.update()
    
    def _parse_lap_time(self, lap_time) -> Optional[float]:
        """解析圈速為秒數"""
        if lap_time is None:
            return None
        
        if isinstance(lap_time, (int, float)):
            return float(lap_time)
        
        if isinstance(lap_time, str):
            try:
                # 格式: "M:SS.mmm" 或 "MM:SS.mmm"
                if ':' in lap_time:
                    parts = lap_time.split(':')
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
                else:
                    return float(lap_time)
            except:
                return None
        
        return None
    
    def _format_lap_time(self, seconds: float) -> str:
        """格式化秒數為圈速字串"""
        if seconds <= 0 or seconds == float('inf'):
            return "--:--.---"
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def paintEvent(self, event):
        """繪製單圈時間分佈"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        if not self._driver_data:
            # 無數據時顯示提示
            painter.setPen(QColor(128, 128, 128))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "Waiting for data...")
            return
        
        width = self.width()
        height = self.height()
        
        # 繪圖參數
        margin_top = 30
        margin_bottom = 10
        margin_left = 10
        margin_right = 10
        
        chart_height = height - margin_top - margin_bottom
        
        # 按差距排序車手
        sorted_drivers = sorted(
            self._driver_data.items(),
            key=lambda x: x[1]['gap']
        )
        
        if not sorted_drivers:
            return
        
        # 計算最大差距 (用於 Y 軸縮放)
        max_gap = max(d[1]['gap'] for d in sorted_drivers)
        max_gap = max(max_gap, 0.5)  # 至少 0.5 秒
        
        # 繪製最快圈速標題
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(margin_left, 18, self._fastest_time_str)
        
        # 繪製 Y 軸刻度和車手標記
        self._draw_y_axis_and_drivers(painter, sorted_drivers, 
                                       margin_left, margin_top, 
                                       width - margin_left - margin_right,
                                       chart_height, max_gap)
    
    def _draw_y_axis_and_drivers(self, painter: QPainter, sorted_drivers: list,
                                  left: int, top: int, width: int, height: int,
                                  max_gap: float):
        """繪製 Y 軸刻度和車手標記 - 圈圈可重疊但 Flag 避免重疊"""
        
        # 計算 Y 軸刻度間隔 (每 0.2 秒一個刻度)
        tick_interval = 0.2
        num_ticks = int(max_gap / tick_interval) + 2
        
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        # Y 軸參數
        y_axis_x = left + 35  # Y 軸 X 位置
        
        # 繪製 Y 軸刻度
        painter.setPen(QColor(100, 100, 100))
        for i in range(num_ticks + 1):
            gap_value = i * tick_interval
            if gap_value > max_gap + tick_interval:
                break
            
            y = top + (gap_value / (max_gap + tick_interval)) * height
            
            # 刻度線 (短)
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawLine(int(y_axis_x - 5), int(y), int(y_axis_x), int(y))
            
            # 刻度標籤
            painter.setPen(QColor(120, 120, 120))
            if i == 0:
                label = ""  # 第一個刻度不顯示 (最快圈速已在上方)
            else:
                label = f"+ {gap_value:.1f}"
            painter.drawText(int(left), int(y + 4), label)
        
        # 繪製 Y 軸主線
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawLine(int(y_axis_x), int(top), int(y_axis_x), int(top + height))
        
        # 計算所有車手的原始 Y 位置
        markers = []
        for driver_num, data in sorted_drivers:
            gap = data['gap']
            y = top + (gap / (max_gap + tick_interval)) * height
            markers.append({
                'driver_num': driver_num,
                'data': data,
                'original_y': y,
                'flag_y': y  # 初始化 flag Y 位置
            })
        
        # 計算 Flag 避免重疊的 Y 位置
        flag_height = 14  # Flag 高度
        min_spacing = flag_height + 2  # 最小間距
        
        for i, marker in enumerate(markers):
            if i == 0:
                continue
            
            # 檢查與前面所有標記的重疊
            for j in range(i - 1, -1, -1):
                prev_flag_y = markers[j]['flag_y']
                current_y = marker['flag_y']
                
                if abs(current_y - prev_flag_y) < min_spacing:
                    # 需要調整，向下移動
                    marker['flag_y'] = prev_flag_y + min_spacing
        
        # 繪製所有車手 (先繪製圈圈和連接線，再繪製 Flag)
        dot_x = y_axis_x + 8  # 圓點 X 位置
        
        # 第一遍：繪製圓點 (允許重疊)
        for marker in markers:
            data = marker['data']
            original_y = marker['original_y']
            team_color = data['team_color']
            
            if not team_color.startswith('#'):
                team_color = f'#{team_color}'
            color = QColor(team_color)
            
            # 繪製圓點
            dot_radius = 5
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            painter.drawEllipse(QPointF(dot_x, original_y), dot_radius, dot_radius)
        
        # 第二遍：繪製連接線和 Flag
        for marker in markers:
            data = marker['data']
            original_y = marker['original_y']
            flag_y = marker['flag_y']
            
            self._draw_driver_marker_with_offset(painter, data, dot_x, original_y, flag_y, width, left)
    
    def _draw_driver_marker_with_offset(self, painter: QPainter, data: Dict,
                                         dot_x: float, original_y: float, flag_y: float,
                                         width: int, left: int):
        """繪製車手標記 - 圓點在原始位置，Flag 可偏移"""
        tla = data['driver_tla']
        gap = data['gap']
        team_color = data['team_color']
        compound = data['compound']
        
        # 車隊顏色
        if not team_color.startswith('#'):
            team_color = f'#{team_color}'
        color = QColor(team_color)
        
        # 從圓點到 Flag 的連接線
        line_start_x = dot_x + 7
        flag_x = dot_x + 25
        
        # 繪製連接線 (從圓點到 Flag)
        painter.setPen(QPen(color, 2))
        painter.drawLine(QPointF(line_start_x, original_y), QPointF(flag_x, flag_y))
        
        # 車手代碼和差距 (在 flag_y 位置)
        text_x = flag_x + 5
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        if gap < 0.001:
            gap_str = ""
        else:
            gap_str = f"+ {gap:.3f}"
        
        display_text = f"{tla}  {gap_str}"
        painter.drawText(int(text_x), int(flag_y + 4), display_text)
        
        # 右側輪胎配方圓形 (在 flag_y 位置)
        tyre_x = left + width - 8
        tyre_radius = 6
        tyre_color = QColor(self.tyre_colors.get(compound, self.tyre_colors['UNKNOWN']))
        
        painter.setBrush(QBrush(tyre_color))
        # 硬胎和中性胎用深色邊框
        if compound in ['HARD', 'MEDIUM']:
            painter.setPen(QPen(QColor(0, 0, 0), 1))
        else:
            painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawEllipse(QPointF(tyre_x, flag_y), tyre_radius, tyre_radius)
    
    def _draw_driver_marker(self, painter: QPainter, driver_num: str, 
                            data: Dict, left: int, y: float, width: int):
        """繪製單個車手標記 (舊方法，保留兼容性)"""
        self._draw_driver_marker_with_offset(painter, data, left + 45, y, y, width, left)

    
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
# 輪胎策略長條圖 Widget (QPainter 繪製)
# ============================================================

class TyreStrategyChartWidget(QWidget):
    """
    輪胎策略長條圖 - 使用 QPainter 繪製
    
    顯示所有車手的輪胎策略：
    - Y 軸：車手代碼（按排名排序）
    - X 軸：圈數 (0 ~ 總圈數)
    - 每個 stint 用對應顏色的長條表示
    - 進站點用垂直線標記
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據
        self._driver_stints: Dict[str, List[Dict]] = {}  # driver_num -> [stint1, stint2, ...]
        self._driver_info: Dict[str, Dict] = {}  # driver_num -> {tla, team_color, ...}
        self._driver_positions: Dict[str, int] = {}  # driver_num -> position
        self._total_laps: int = 53
        self._current_lap: int = 0
        
        # 繪圖參數
        self._margin_left = 50  # 左邊距（車手名稱）
        self._margin_right = 20
        self._margin_top = 30
        self._margin_bottom = 15  # 底部（X 軸標籤）- 因圖例已移除所以減少
        self._row_height = 22
        self._row_spacing = 3
        
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #1a1a1a;")
    
    def set_data(self, driver_stints: Dict[str, List[Dict]], 
                 driver_info: Dict[str, Dict],
                 driver_positions: Dict[str, int],
                 total_laps: int,
                 current_lap: int = 0):
        """
        設置數據
        
        Args:
            driver_stints: {driver_num: [{compound, start_lap, end_lap, new}, ...]}
            driver_info: {driver_num: {tla, team_color, ...}}
            driver_positions: {driver_num: position}
            total_laps: 總圈數
            current_lap: 當前圈數（用於標記進度線）
        """
        self._driver_stints = driver_stints
        self._driver_info = driver_info
        self._driver_positions = driver_positions
        self._total_laps = total_laps
        self._current_lap = current_lap
        self.update()
    
    def update_current_lap(self, current_lap: int):
        """更新當前圈數"""
        self._current_lap = current_lap
        self.update()
    
    def paintEvent(self, event):
        """繪製事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 背景
        painter.fillRect(0, 0, width, height, QColor('#1a1a1a'))
        
        # 計算繪圖區域
        chart_left = self._margin_left
        chart_right = width - self._margin_right
        chart_top = self._margin_top
        chart_bottom = height - self._margin_bottom
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        
        if chart_width <= 0 or chart_height <= 0:
            return
        
        # 按排名排序車手
        sorted_drivers = sorted(
            self._driver_positions.items(),
            key=lambda x: x[1]
        )
        
        if not sorted_drivers:
            # 無數據時顯示提示
            painter.setPen(QColor('#888888'))
            painter.setFont(QFont('Arial', 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "No tyre data available")
            return
        
        num_drivers = len(sorted_drivers)
        row_height = min(self._row_height, (chart_height - (num_drivers - 1) * self._row_spacing) / num_drivers)
        
        # 繪製 X 軸（圈數）
        self._draw_x_axis(painter, chart_left, chart_right, chart_bottom, chart_width)
        
        # 繪製每位車手的輪胎策略
        for i, (driver_num, position) in enumerate(sorted_drivers):
            y = chart_top + i * (row_height + self._row_spacing)
            self._draw_driver_row(painter, driver_num, chart_left, y, chart_width, row_height)
        
        # 繪製當前圈數指示線
        if self._current_lap > 0 and self._total_laps > 0:
            progress = self._current_lap / self._total_laps
            x = chart_left + progress * chart_width
            painter.setPen(QPen(QColor('#00FF00'), 2, Qt.DashLine))
            painter.drawLine(int(x), chart_top - 5, int(x), chart_bottom + 5)
            
            # 當前圈數標籤
            painter.setPen(QColor('#00FF00'))
            painter.setFont(QFont('Arial', 9))
            painter.drawText(int(x) - 15, chart_top - 8, f"L{self._current_lap}")
        
        # 繪製圖例
        self._draw_legend(painter, width, height)
    
    def _draw_x_axis(self, painter: QPainter, left: int, right: int, bottom: int, width: float):
        """繪製 X 軸"""
        painter.setPen(QColor('#666666'))
        painter.drawLine(left, bottom, right, bottom)
        
        # 圈數標籤 (每 10 圈一個)
        painter.setFont(QFont('Arial', 9))
        painter.setPen(QColor('#AAAAAA'))
        
        step = 10
        if self._total_laps <= 30:
            step = 5
        elif self._total_laps >= 70:
            step = 15
        
        for lap in range(0, self._total_laps + 1, step):
            x = left + (lap / self._total_laps) * width
            painter.drawLine(int(x), bottom, int(x), bottom + 5)
            painter.drawText(int(x) - 10, bottom + 18, str(lap))
        
        # 最後一圈
        if self._total_laps % step != 0:
            x = right
            painter.drawLine(int(x), bottom, int(x), bottom + 5)
            painter.drawText(int(x) - 10, bottom + 18, str(self._total_laps))
    
    def _draw_driver_row(self, painter: QPainter, driver_num: str, 
                         left: int, y: float, width: float, height: float):
        """繪製單個車手的輪胎策略行"""
        # 車手名稱
        driver_info = self._driver_info.get(driver_num, {})
        tla = driver_info.get('tla', driver_num)
        team_color = driver_info.get('team_color', 'CCCCCC')
        
        # 車手標籤背景
        painter.fillRect(2, int(y), self._margin_left - 5, int(height), 
                        QColor(f'#{team_color}'))
        
        # 車手名稱文字
        text_color = '#000000' if self._is_light_color(team_color) else '#FFFFFF'
        painter.setPen(QColor(text_color))
        painter.setFont(QFont('Arial', 9, QFont.Bold))
        painter.drawText(5, int(y) + int(height) - 5, tla)
        
        # 繪製輪胎 stint 長條
        stints = self._driver_stints.get(driver_num, [])
        
        for stint in stints:
            compound = stint.get('compound', 'UNKNOWN')
            start_lap = stint.get('start_lap', 0)
            end_lap = stint.get('end_lap', self._total_laps)
            is_new = stint.get('new', True)
            
            # 計算長條位置
            x1 = left + (start_lap / self._total_laps) * width
            x2 = left + (end_lap / self._total_laps) * width
            bar_width = max(x2 - x1, 2)  # 最小寬度 2px
            
            # 輪胎顏色
            color = TYRE_COLORS.get(compound, TYRE_COLORS['UNKNOWN'])
            painter.fillRect(int(x1), int(y) + 1, int(bar_width), int(height) - 2, QColor(color))
            
            # 進站標記（stint 之間的垂直線）
            if start_lap > 0:
                painter.setPen(QPen(QColor('#FFFFFF'), 2))
                painter.drawLine(int(x1), int(y), int(x1), int(y) + int(height))
            
            # 輪胎縮寫標籤（如果長條夠寬）
            if bar_width > 25:
                abbrev = TYRE_ABBREV.get(compound, '?')
                text_color = '#000000' if compound in ['HARD', 'MEDIUM'] else '#FFFFFF'
                painter.setPen(QColor(text_color))
                painter.setFont(QFont('Arial', 8, QFont.Bold))
                text_x = int(x1 + bar_width / 2 - 5)
                text_y = int(y + height / 2 + 4)
                painter.drawText(text_x, text_y, abbrev)
    
    def _draw_legend(self, painter: QPainter, width: int, height: int):
        """繪製圖例 - 已禁用以節省高度"""
        # 圖例已移除以節省高度
        pass
    
    def _is_light_color(self, hex_color: str) -> bool:
        """判斷顏色是否為淺色"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return luminance > 0.5
        except:
            return False


class TyreStrategyChartDialog(QWidget):
    """
    輪胎策略圖獨立視窗
    """
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Tyre Strategy Chart")
        self.setMinimumSize(800, 500)
        self.resize(1000, 600)
        
        # 佈局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 圖表 Widget
        self.chart = TyreStrategyChartWidget()
        layout.addWidget(self.chart)
        
        # 底部資訊列
        info_layout = QHBoxLayout()
        self.lbl_info = QLabel("Lap: 0 / 0")
        self.lbl_info.setStyleSheet("color: #AAAAAA;")
        info_layout.addWidget(self.lbl_info)
        info_layout.addStretch()
        
        # 關閉按鈕
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        info_layout.addWidget(btn_close)
        
        layout.addLayout(info_layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #333333;
                border: 1px solid #555555;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
    
    def set_data(self, driver_stints: Dict[str, List[Dict]], 
                 driver_info: Dict[str, Dict],
                 driver_positions: Dict[str, int],
                 total_laps: int,
                 current_lap: int = 0):
        """設置數據"""
        self.chart.set_data(driver_stints, driver_info, driver_positions, total_laps, current_lap)
        self.lbl_info.setText(f"Lap: {current_lap} / {total_laps}")
    
    def update_current_lap(self, current_lap: int, total_laps: int = None):
        """更新當前圈數"""
        self.chart.update_current_lap(current_lap)
        if total_laps:
            self.lbl_info.setText(f"Lap: {current_lap} / {total_laps}")
        else:
            self.lbl_info.setText(f"Lap: {current_lap}")


# ============================================================
# Pit Loss Configuration Loader - 進站時間設定載入器
# ============================================================

class PitLossConfigLoader:
    """
    從 config/pit_loss_database.json 載入賽道進站時間設定
    支援賽道別名解析和預設值回退
    """
    
    _instance = None
    _config = None
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """載入進站時間設定檔"""
        config_paths = [
            Path(__file__).parent.parent / "config" / "pit_loss_database.json",
            Path(__file__).parent / "config" / "pit_loss_database.json",
            Path("config/pit_loss_database.json"),
        ]
        
        for path in config_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        print(f"[PIT_CONFIG] Loaded pit loss config from {path}")
                        return config
                except Exception as e:
                    print(f"[PIT_CONFIG] Error loading {path}: {e}")
        
        print("[PIT_CONFIG] No config file found, using defaults")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """預設設定"""
        return {
            "circuits": {},
            "aliases": {},
            "default": {
                "pit_loss_times": {
                    "green_flag": 22.0,
                    "safety_car": 11.5,
                    "virtual_safety_car": 8.0
                }
            }
        }
    
    def get_pit_loss_times(self, meeting_name: str) -> Tuple[float, float, float]:
        """
        根據 meeting name 獲取進站時間設定
        
        Args:
            meeting_name: 例如 "2025-04-06_Japanese_Grand_Prix" 或 "Japan" 或 "Suzuka"
            
        Returns:
            Tuple[green_flag, safety_car, virtual_safety_car]
        """
        circuit_key = self._resolve_circuit_key(meeting_name)
        
        if circuit_key and circuit_key in self._config.get("circuits", {}):
            pit_times = self._config["circuits"][circuit_key].get("pit_loss_times", {})
            green = pit_times.get("green_flag", 22.0)
            sc = pit_times.get("safety_car", 11.5)
            vsc = pit_times.get("virtual_safety_car", 8.0)
            print(f"[PIT_CONFIG] {meeting_name} -> {circuit_key}: Green={green}s, SC={sc}s, VSC={vsc}s")
            return (green, sc, vsc)
        
        # Fallback to default
        default = self._config.get("default", {}).get("pit_loss_times", {})
        green = default.get("green_flag", 22.0)
        sc = default.get("safety_car", 11.5)
        vsc = default.get("virtual_safety_car", 8.0)
        print(f"[PIT_CONFIG] {meeting_name} -> (default): Green={green}s, SC={sc}s, VSC={vsc}s")
        return (green, sc, vsc)
    
    def _resolve_circuit_key(self, meeting_name: str) -> Optional[str]:
        """解析 meeting name 到 circuit key"""
        if not meeting_name:
            return None
            
        # 直接匹配 circuits
        circuits = self._config.get("circuits", {})
        if meeting_name in circuits:
            return meeting_name
        
        # 檢查別名
        aliases = self._config.get("aliases", {})
        if meeting_name in aliases:
            return aliases[meeting_name]
        
        # 嘗試從 meeting name 提取賽道關鍵字
        # 例如 "2025-04-06_Japanese_Grand_Prix" -> "Japanese"
        keywords = [
            "Japanese", "Japan", "Suzuka",
            "Bahrain",
            "Saudi", "Jeddah",
            "Australian", "Australia", "Melbourne",
            "Chinese", "China", "Shanghai",
            "Miami",
            "Emilia", "Imola",
            "Monaco",
            "Canadian", "Canada", "Montreal",
            "Spanish", "Spain", "Barcelona",
            "Austrian", "Austria", "Spielberg",
            "British", "Silverstone",
            "Hungarian", "Hungary", "Hungaroring",
            "Belgian", "Belgium", "Spa",
            "Dutch", "Netherlands", "Zandvoort",
            "Italian", "Italy", "Monza",
            "Azerbaijan", "Baku",
            "Singapore",
            "United_States", "USA", "Austin", "COTA",
            "Mexican", "Mexico",
            "Brazilian", "Brazil", "Interlagos", "Sao_Paulo",
            "Las_Vegas",
            "Qatar", "Lusail",
            "Abu_Dhabi", "Yas"
        ]
        
        meeting_upper = meeting_name.upper().replace("_", " ")
        for keyword in keywords:
            if keyword.upper() in meeting_upper:
                # 找到關鍵字，檢查別名
                if keyword in aliases:
                    return aliases[keyword]
                elif keyword in circuits:
                    return keyword
        
        return None
    
    def list_circuits(self) -> List[str]:
        """列出所有可用的賽道"""
        return list(self._config.get("circuits", {}).keys())


# ============================================================
# Pit Window Widget - 進站策略窗口
# ============================================================

class PitWindowWidget(QWidget):
    """
    Pit Window 進站策略視覺化工具
    
    顯示車手相對位置與進站損失時間的關係：
    - X 軸 (白色線): 相對時間差 (秒)
    - 深紅色區域: Pit Loss Zone (進站損失時間約 20-25 秒)
    - 白色垂直線: 綠旗狀態下的預估掉落位置
    - 黃色區域: SC/VSC 狀態下的預估掉落位置
    - 車手標記在 X 軸上
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 80)  # 增加高度讓 PIT LANE 下方文字可見
        
        # 數據
        self._driver_positions: Dict[str, Dict[str, Any]] = {}
        self._driver_info: Dict[str, Dict[str, Any]] = {}
        self._reference_driver: Optional[str] = None  # 參考車手 (預設 P1)
        self._use_p1_as_reference = True  # 是否使用 P1 作為參考點
        self._track_status = "GREEN"  # GREEN, SC, VSC
        
        # 進站時間設定
        self._time_range = 30.0  # 顯示範圍: +/- 30 秒
        self._pit_loss_green = 22.0  # 綠旗進站損失時間 (秒)
        self._pit_loss_sc = 12.0  # SC 進站損失時間 (秒)
        self._pit_loss_vsc = 8.0  # VSC 進站損失時間 (秒)
        
        # 繪圖參數
        self._margin_left = 50
        self._margin_right = 20
        self._margin_top = 30  # 上方留空給 Flag 標籤
        self._margin_bottom = 25  # 增加底部 margin 讓 X 軸刻度可見
        
        # 右鍵選單
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # 車隊顏色
        self.team_colors = {
            'Red Bull Racing': '#3671C6',
            'Ferrari': '#E8002D',
            'Mercedes': '#27F4D2',
            'McLaren': '#FF8000',
            'Aston Martin': '#229971',
            'Alpine': '#FF87BC',
            'Williams': '#64C4FF',
            'RB': '#6692FF',
            'Kick Sauber': '#52E252',
            'Haas F1 Team': '#B6BABD',
            'default': '#888888'
        }
        
        # 車號對應顏色
        self.driver_colors = {
            '1': '#3671C6', '11': '#3671C6',
            '16': '#E8002D', '55': '#E8002D',
            '44': '#27F4D2', '63': '#27F4D2',
            '4': '#FF8000', '81': '#FF8000',
            '14': '#229971', '18': '#229971',
            '10': '#FF87BC', '31': '#FF87BC',
            '23': '#64C4FF', '2': '#64C4FF',
            '22': '#6692FF', '30': '#6692FF',
            '77': '#52E252', '24': '#52E252',
            '20': '#B6BABD', '27': '#B6BABD',
        }
        
        self.setStyleSheet("background-color: #1E1E1E;")
        print("[PIT_WINDOW] PitWindowWidget initialized")
    
    def set_driver_info(self, driver_info: Dict):
        """設置車手資訊"""
        self._driver_info = driver_info or {}
    
    def set_pit_loss(self, green: float = 22.0, sc: float = 12.0, vsc: float = 8.0):
        """設置進站損失時間"""
        self._pit_loss_green = green
        self._pit_loss_sc = sc
        self._pit_loss_vsc = vsc
    
    def set_track_status(self, status: str):
        """設置賽道狀態 (GREEN, SC, VSC)"""
        if status in ("GREEN", "SC", "VSC"):
            self._track_status = status
            self.update()
    
    def set_time_range(self, range_seconds: float):
        """設置顯示時間範圍"""
        if range_seconds > 0:
            self._time_range = range_seconds
    
    def set_reference_driver(self, driver_num: str):
        """設置參考車手 (X 軸 0 點)"""
        self._reference_driver = driver_num
        self._use_p1_as_reference = False
        self.update()
        print(f"[PIT_WINDOW] 參考車手設為: {driver_num}")
    
    def reset_to_p1(self):
        """重設為 P1 作為參考點"""
        self._use_p1_as_reference = True
        self._reference_driver = None
        self.update()
        print("[PIT_WINDOW] 重設為 P1 作為參考點")
    
    def _show_context_menu(self, pos):
        """顯示右鍵選單"""
        menu = QMenu(self)
        
        # 回到預設 P1
        reset_action = menu.addAction("回到預設 (P1)")
        reset_action.triggered.connect(self.reset_to_p1)
        
        # 顯示當前參考車手
        if self._reference_driver and not self._use_p1_as_reference:
            ref_tla = self._driver_positions.get(self._reference_driver, {}).get('driver_tla', self._reference_driver)
            menu.addSeparator()
            current_action = menu.addAction(f"當前參考: {ref_tla}")
            current_action.setEnabled(False)
        
        menu.exec_(self.mapToGlobal(pos))
    
    def update_positions(self, drivers_data: Dict[str, Dict[str, Any]]):
        """更新車手位置數據"""
        self._driver_positions = drivers_data or {}
        
        # 如果使用 P1 作為參考點，更新參考車手
        if self._use_p1_as_reference:
            for driver_num, data in self._driver_positions.items():
                if data.get('position') == 1:
                    self._reference_driver = driver_num
                    break
        
        self.update()
    
    def paintEvent(self, event):
        """繪製 Pit Window"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 深灰色背景
        painter.fillRect(0, 0, width, height, QColor('#1E1E1E'))
        
        # 計算繪圖區域
        chart_left = self._margin_left
        chart_right = width - self._margin_right
        chart_top = self._margin_top
        chart_bottom = height - self._margin_bottom
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        
        if chart_width <= 0 or chart_height <= 0:
            return
        
        # X 軸 Y 位置 (車手標記將在此線上)
        axis_y = chart_top + chart_height / 2
        
        # 繪製 Pit Loss Zone (深紅色區域)
        self._draw_pit_loss_zone(painter, chart_left, chart_top, chart_width, chart_height, axis_y)
        
        # 繪製白色 X 軸
        self._draw_x_axis(painter, chart_left, chart_right, axis_y, chart_width, chart_bottom)
        
        # 繪製車手標記 (在 X 軸上)
        self._draw_driver_markers(painter, chart_left, chart_width, axis_y)
        
        # 如果沒有車手數據，顯示提示
        if not self._driver_positions:
            painter.setPen(QColor(150, 150, 150))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(int(width / 2 - 60), int(height / 2), "Waiting for data...")
    
    def _draw_pit_loss_zone(self, painter: QPainter, left: float, top: float,
                            width: float, height: float, axis_y: float):
        """繪製 Pit Loss Zone (進站損失時間區域)
        
        顯示進站會損失的時間區域 (底色區分)：
        - 深紅色區域 = 綠旗進站損失
        - 橙色區域 = SC 進站損失
        - 黃色區域 = VSC 進站損失
        - 白色虛線 = 各區間邊界
        """
        center_x = left + width / 2
        
        # 計算各區域寬度 (像素)
        green_width_px = (self._pit_loss_green / self._time_range) * (width / 2)
        sc_width_px = (self._pit_loss_sc / self._time_range) * (width / 2)
        vsc_width_px = (self._pit_loss_vsc / self._time_range) * (width / 2)
        
        # === 左側 (進站後會掉落到的位置) ===
        pit_zone_left = center_x - green_width_px
        sc_zone_left = center_x - sc_width_px
        vsc_zone_left = center_x - vsc_width_px
        
        # 1. 深紅色區域 (Green Flag) - 從 green 邊界到 sc 邊界
        painter.fillRect(
            int(pit_zone_left), int(top),
            int(green_width_px - sc_width_px), int(height),
            QColor(80, 20, 20)  # 深紅色
        )
        
        # 2. 橙色區域 (SC) - 從 sc 邊界到 vsc 邊界
        painter.fillRect(
            int(sc_zone_left), int(top),
            int(sc_width_px - vsc_width_px), int(height),
            QColor(180, 80, 0)  # 橙色
        )
        
        # 3. 黃色區域 (VSC) - 從 vsc 邊界到中心
        painter.fillRect(
            int(vsc_zone_left), int(top),
            int(vsc_width_px), int(height),
            QColor(180, 150, 0)  # 黃色
        )
        
        # 白色虛線 - 各區間邊界 (左側)
        pen_white_dash = QPen(QColor(255, 255, 255), 1, Qt.DashLine)
        pen_white_dash.setDashPattern([4, 4])
        painter.setPen(pen_white_dash)
        painter.drawLine(int(pit_zone_left), int(top), int(pit_zone_left), int(top + height))
        painter.drawLine(int(sc_zone_left), int(top), int(sc_zone_left), int(top + height))
        painter.drawLine(int(vsc_zone_left), int(top), int(vsc_zone_left), int(top + height))
        
        # === 右側 (對稱顯示) ===
        pit_zone_right = center_x + green_width_px
        sc_zone_right = center_x + sc_width_px
        vsc_zone_right = center_x + vsc_width_px
        
        # 1. 黃色區域 (VSC) - 從中心到 vsc 邊界
        painter.fillRect(
            int(center_x), int(top),
            int(vsc_width_px), int(height),
            QColor(180, 150, 0)  # 黃色
        )
        
        # 2. 橙色區域 (SC) - 從 vsc 邊界到 sc 邊界
        painter.fillRect(
            int(vsc_zone_right), int(top),
            int(sc_width_px - vsc_width_px), int(height),
            QColor(180, 80, 0)  # 橙色
        )
        
        # 3. 深紅色區域 (Green Flag) - 從 sc 邊界到 green 邊界
        painter.fillRect(
            int(sc_zone_right), int(top),
            int(green_width_px - sc_width_px), int(height),
            QColor(80, 20, 20)  # 深紅色
        )
        
        # 白色虛線 - 各區間邊界 (右側)
        painter.setPen(pen_white_dash)
        painter.drawLine(int(pit_zone_right), int(top), int(pit_zone_right), int(top + height))
        painter.drawLine(int(sc_zone_right), int(top), int(sc_zone_right), int(top + height))
        painter.drawLine(int(vsc_zone_right), int(top), int(vsc_zone_right), int(top + height))
        
        # === 中央 0 秒位置虛線 ===
        painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
        painter.drawLine(int(center_x), int(top), int(center_x), int(top + height))
    
    def _draw_x_axis(self, painter: QPainter, left: float, right: float,
                     axis_y: float, width: float, bottom: float):
        """繪製 X 軸 (白色線)"""
        # 白色 X 軸線
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(int(left), int(axis_y), int(right), int(axis_y))
        
        # 刻度和標籤
        tick_interval = 5.0
        center_x = left + width / 2
        
        painter.setPen(QColor(200, 200, 200))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        
        current = -self._time_range
        while current <= self._time_range:
            x = center_x + (current / self._time_range) * (width / 2)
            
            # 刻度線
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawLine(int(x), int(axis_y - 3), int(x), int(axis_y + 3))
            
            # 標籤 (反轉：左邊正數，右邊負數)
            # 左邊 = 進站後會掉落到的位置 (+秒)
            # 右邊 = 落後於領先者 (-秒)
            display_value = -current  # 反轉顯示
            if display_value == 0:
                label = "0"
            elif display_value > 0:
                label = f"+{display_value:.0f}"
            else:
                label = f"{display_value:.0f}"
            
            painter.setPen(QColor(200, 200, 200))
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(int(x - text_rect.width() / 2), int(bottom + 15), label)
            
            current += tick_interval
    
    def _draw_driver_markers(self, painter: QPainter, left: float, width: float, axis_y: float):
        """繪製車手標記 (在 X 軸上)
        
        X 軸定義：
        - 0 點 = P1 位置（中心）
        - 左側正數 (+5, +10, +15...) = 進站後會掉落到的位置
        - 右側負數 (-5, -10, -15...) = 落後於參考車手的時間
        
        車手定位：
        - 參考車手在 0 點（中心）
        - 其他車手根據與參考車手的差距定位
        """
        if not self._driver_positions:
            return
        
        center_x = left + width / 2
        
        # 獲取參考車手的 gap_to_leader
        ref_gap = 0.0
        if self._reference_driver and self._reference_driver in self._driver_positions:
            ref_gap = self._driver_positions[self._reference_driver].get('gap_to_leader', 0.0) or 0.0
        
        # 收集並排序車手
        markers = []
        for driver_num, data in self._driver_positions.items():
            position = data.get('position', 99)
            gap_to_leader = data.get('gap_to_leader', 0.0)
            gap_laps = data.get('gap_to_leader_laps', 0)
            driver_tla = data.get('driver_tla', driver_num)
            # 嘗試多個可能的欄位名稱
            pit_count = data.get('pit_count') or data.get('PitCount') or data.get('num_pit_stops') or 0
            
            # 落後圈數則跳過
            if gap_laps and gap_laps > 0:
                continue
            
            if gap_to_leader is None:
                gap_to_leader = 0.0
            
            # 計算相對於參考車手的差距
            relative_gap = gap_to_leader - ref_gap
            
            # 超出顯示範圍則跳過
            if abs(relative_gap) > self._time_range:
                continue
            
            # 參考車手在 0 點 (中心), 落後的車手向右 (負方向)
            x = center_x - (relative_gap / self._time_range) * (width / 2)
            
            color = self._get_driver_color(driver_num, data)
            
            markers.append({
                'driver_num': driver_num,
                'driver_tla': driver_tla,
                'position': position,
                'gap': gap_to_leader,
                'pit_count': pit_count if isinstance(pit_count, int) else 0,
                'x': x,
                'color': color
            })
        
        # 按位置排序 (P1 最後繪製，在最上層)
        markers.sort(key=lambda m: -m['position'])
        
        # 繪製所有車手
        for m in markers:
            self._draw_single_marker(painter, m, axis_y)
    
    def _draw_single_marker(self, painter: QPainter, marker: Dict, axis_y: float):
        """繪製單個車手標記"""
        x = marker['x']
        tla = marker['driver_tla']
        pit_count = marker['pit_count']
        color = QColor(marker['color'])
        
        # 1. 彩色圓點 (在 X 軸上)
        dot_radius = 5
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawEllipse(QPointF(x, axis_y), dot_radius, dot_radius)
        
        # 2. 連接線 (向上)
        line_length = 18
        painter.setPen(QPen(color, 2))
        painter.drawLine(QPointF(x, axis_y - dot_radius), QPointF(x, axis_y - dot_radius - line_length))
        
        # 3. Flag 標籤
        flag_y = axis_y - dot_radius - line_length - 8
        self._draw_flag(painter, x, flag_y, tla, color)
        
        # 4. 進站次數氣泡 (在 Flag 右上角，避免蓋住車手)
        bubble_x = x + 18  # 移到右側
        bubble_y = flag_y - 8
        self._draw_pit_bubble(painter, bubble_x, bubble_y, pit_count)
    
    def _draw_flag(self, painter: QPainter, x: float, y: float, tla: str, color: QColor):
        """繪製 Flag 標籤"""
        w, h = 30, 14
        flag_x = x - w / 2
        flag_y = y - h / 2
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(QRectF(flag_x, flag_y, w, h))
        
        text_color = QColor(255, 255, 255) if self._is_dark_color(color) else QColor(0, 0, 0)
        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        text_rect = painter.fontMetrics().boundingRect(tla)
        text_x = flag_x + (w - text_rect.width()) / 2
        text_y = flag_y + h - 3
        painter.drawText(int(text_x), int(text_y), tla)
    
    def _draw_pit_bubble(self, painter: QPainter, x: float, y: float, pit_count: int):
        """繪製進站次數氣泡"""
        # 確保 pit_count 是整數
        if pit_count is None:
            pit_count = 0
        try:
            pit_count = int(pit_count)
        except (ValueError, TypeError):
            pit_count = 0
        
        radius = 7
        
        if pit_count == 0:
            bg_color = QColor(0, 180, 0)  # 綠色 - 未進站
        else:
            bg_color = QColor(0, 100, 255)  # 藍色 - 已進站
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawEllipse(QPointF(x, y), radius, radius)
        
        # 繪製數字
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        
        text = str(pit_count)
        text_rect = painter.fontMetrics().boundingRect(text)
        painter.drawText(int(x - text_rect.width() / 2), int(y + text_rect.height() / 4), text)
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        
        text = str(pit_count)
        text_rect = painter.fontMetrics().boundingRect(text)
        painter.drawText(int(x - text_rect.width() / 2), int(y + text_rect.height() / 4), text)
    
    def _get_driver_color(self, driver_num: str, data: Dict = None) -> str:
        """獲取車手顏色"""
        # 從數據中的 team_color
        if data:
            tc = data.get('team_color')
            if tc:
                return f'#{tc}' if not tc.startswith('#') else tc
        
        # driver_info
        if driver_num in self._driver_info:
            team = self._driver_info[driver_num].get('team', '')
            if team in self.team_colors:
                return self.team_colors[team]
        
        # 車號顏色
        if driver_num in self.driver_colors:
            return self.driver_colors[driver_num]
        
        return self.team_colors['default']
    
    def _is_dark_color(self, color: QColor) -> bool:
        """判斷顏色是否為深色"""
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
        return luminance < 0.5


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
        # SC 使用橘色 (#FF8C00)
        status_map = {
            "1": ("GREEN", "#00FF00", "#000000"),
            "2": ("YELLOW", "#FFFF00", "#000000"),
            "4": ("SAFETY CAR", "#FF8C00", "#FFFFFF"),  # 橘色
            "5": ("RED", "#FF0000", "#FFFFFF"),
            "6": ("VSC", "#FFD700", "#000000"),
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
        layout.setContentsMargins(2, 2, 2, 2)  # 減少邊距
        
        # 標題已移除
        
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
        
        # 啟用自動換行
        self.message_list.setWordWrap(True)
        self.message_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # === 輸出比賽控制訊息欄位寬度 ===
        print("=" * 60)
        print("[RaceControlMessagesWidget] 欄位寬度設定 (共3欄):")
        print(f"  0:圈=35, 1:類型=70, 2:訊息=自動填滿(自動換行)")
        print("=" * 60)
        
        layout.addWidget(self.message_list)
    
    def set_messages(self, messages: List[Dict[str, Any]]):
        """設置所有訊息"""
        self._all_messages = messages
    
    def _get_message_type_and_color(self, msg: Dict) -> tuple:
        """
        根據訊息內容判斷類型和顏色
        
        Returns:
            (type_text, bg_color, fg_color)
        """
        flag = msg.get('Flag', '')
        category = msg.get('Category', '')
        message = msg.get('Message', '').upper()
        
        # 優先檢查訊息內容關鍵字
        if 'SAFETY CAR' in message or 'SC ' in message or category == 'SafetyCar':
            return ('SC', '#FF8C00', '#FFFFFF')  # 橘色 - Safety Car
        elif 'DRS' in message:
            return ('Drs', '#00FF00', '#000000')  # 綠色 - DRS
        elif 'PENALTY' in message or category == 'Penalty':
            return ('Penalty', '#1E90FF', '#FFFFFF')  # 藍色 - Penalty
        elif 'DOUBLE YELLOW' in message:
            return ('YELLOW', '#FFFF00', '#000000')  # 黃色 - Double Yellow
        elif 'VSC' in message:
            return ('VSC', '#FFD700', '#000000')  # 金黃色 - VSC
        
        # 根據 Flag 設置顏色
        if flag == 'GREEN':
            return ('GREEN', '#00FF00', '#000000')
        elif flag == 'YELLOW':
            return ('YELLOW', '#FFFF00', '#000000')
        elif flag == 'RED':
            return ('RED', '#FF0000', '#FFFFFF')
        elif flag == 'BLUE':
            return ('BLUE', '#0000FF', '#FFFFFF')
        elif flag == 'CHEQUERED':
            return ('CHEQUERED', '#000000', '#FFFFFF')
        elif flag:
            return (flag, '#888888', '#FFFFFF')
        
        # 使用 Category
        return (category if category else 'Other', '#555555', '#FFFFFF')
    
    def update_for_lap(self, current_lap: int):
        """根據當前圈數更新顯示"""
        self._current_lap = current_lap
        
        # 過濾只顯示當前圈數之前的訊息
        visible_messages = [
            msg for msg in self._all_messages 
            if msg.get('Lap', 0) <= current_lap
        ]
        
        # 分離重要訊息 (SC/Penalty) 和一般訊息
        priority_messages = []
        normal_messages = []
        
        for msg in visible_messages:
            message_text = msg.get('Message', '').upper()
            category = msg.get('Category', '').upper()
            
            # SC 和 Penalty 為高優先級
            is_priority = (
                'SAFETY CAR' in message_text or 
                'SC ' in message_text or 
                category == 'SAFETYCAR' or
                'PENALTY' in message_text or 
                category == 'PENALTY'
            )
            
            if is_priority:
                priority_messages.append(msg)
            else:
                normal_messages.append(msg)
        
        # 分別按圈數倒序排列
        priority_messages = sorted(priority_messages, key=lambda m: m.get('Lap', 0), reverse=True)
        normal_messages = sorted(normal_messages, key=lambda m: m.get('Lap', 0), reverse=True)
        
        # 合併: 優先訊息在前
        all_sorted = priority_messages + normal_messages
        
        # 限制顯示數量
        visible_messages = all_sorted[:20]
        
        self.message_list.setRowCount(len(visible_messages))
        
        for row, msg in enumerate(visible_messages):
            lap = msg.get('Lap', '?')
            message = msg.get('Message', '')
            
            # 獲取類型和顏色
            type_text, bg_color, fg_color = self._get_message_type_and_color(msg)
            
            # 設置圈數
            lap_item = QTableWidgetItem(str(lap))
            lap_item.setTextAlignment(Qt.AlignCenter)
            self.message_list.setItem(row, 0, lap_item)
            
            # 設置類型（帶顏色）
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setBackground(QColor(bg_color))
            type_item.setForeground(QColor(fg_color))
            self.message_list.setItem(row, 1, type_item)
            
            # 設置訊息
            msg_item = QTableWidgetItem(message)
            self.message_list.setItem(row, 2, msg_item)


class SHAPExplanationWidget(QWidget):
    """
    SHAP 特徵解釋面板
    
    顯示選定車手的勝率預測解釋：
    - 勝率百分比
    - 主要影響因素 (正面/負面)
    - 基準值說明
    
    參考: "F1 Race Winner Prediction Using RF and SHAP Analysis" (IEEE 2025)
    """
    
    # 特徵名稱的中文翻譯
    FEATURE_LABELS = {
        # v3.4 動態因子 (新增，優先顯示)
        'tyre_advantage': '輪胎優勢',
        'circuit_affinity': '賽道適應性',
        'fp3q_compensation': 'FP3/Q補償',
        # 基礎 XGBoost 特徵
        'position': '目前位置',
        'gap_to_leader': '與領先者差距',
        'gap_to_ahead': '與前車差距',
        'lap_time': '圈時',
        'best_lap_time': '最快圈',
        'tyre_compound': '輪胎類型',
        'tyre_age': '輪胎年齡',
        'pit_count': '進站次數',
        'laps_remaining': '剩餘圈數',
        'track_status': '賽道狀態',
        'air_temp': '氣溫',
        'rainfall': '下雨',
        'driver_win_rate': '車手勝率',
        'driver_podium_rate': '車手領獎台率',
        'team_rating': '車隊評分',
        'circuit_overtake_rate': '賽道超車率',
        'circuit_sc_rate': '賽道 SC 率',
        'qualifying_position': '排位成績',
        'position_delta': '位置變化',
        'log_gap': '差距(log)',
        'race_progress': '比賽進度',
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_driver: Optional[str] = None
        self._explanations: Dict[str, Dict] = {}
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 標題
        title = QLabel("SHAP 勝率分析")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 說明文字
        self.lbl_info = QLabel("v3.4 動態策略: 輪胎(2023-24訓練) + 賽道適應性 + FP3/Q補償")
        self.lbl_info.setStyleSheet("color: #888888; font-size: 9px;")
        layout.addWidget(self.lbl_info)
        
        # 車手選擇
        driver_layout = QHBoxLayout()
        driver_layout.addWidget(QLabel("車手:"))
        self.cmb_driver = QComboBox()
        self.cmb_driver.setMinimumWidth(80)
        self.cmb_driver.currentTextChanged.connect(self._on_driver_changed)
        driver_layout.addWidget(self.cmb_driver)
        driver_layout.addStretch()
        layout.addLayout(driver_layout)
        
        # 勝率標籤
        self.lbl_win_prob = QLabel("勝率: --")
        self.lbl_win_prob.setStyleSheet("font-size: 16px; font-weight: bold; color: #00FF00;")
        layout.addWidget(self.lbl_win_prob)
        
        # 貢獻因素表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["因素", "貢獻"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 欄位寬度
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 60)
        
        # === 輸出 SHAP 面板欄位寬度 ===
        print("=" * 60)
        print("[SHAPExplanationWidget] 欄位寬度設定 (共2欄):")
        print(f"  0:因素=100, 1:貢獻=60")
        print(f"  總寬度: 160px")
        print("=" * 60)
        
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(self.table)
        
        # 基準值說明
        self.lbl_base = QLabel("基準值: -- (平均勝率)")
        self.lbl_base.setStyleSheet("color: #888888; font-size: 9px;")
        layout.addWidget(self.lbl_base)
    
    def update_explanations(self, explanations: Dict[str, Dict], predictions: Dict[str, Dict]):
        """
        更新 SHAP 解釋數據
        
        Args:
            explanations: {driver_code: {contributions: [...], base_value: float}}
            predictions: {driver_num: {win_prob, p2_prob, p3_prob, driver_tla}}
        """
        self._explanations = explanations
        
        # 更新車手下拉選單
        current_driver = self.cmb_driver.currentText()
        self.cmb_driver.blockSignals(True)
        self.cmb_driver.clear()
        
        # 按勝率排序
        sorted_drivers = sorted(
            [(dn, pred.get('win_probability', 0), pred.get('driver_tla', dn)) 
             for dn, pred in predictions.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        for driver_num, win_prob, driver_tla in sorted_drivers:
            self.cmb_driver.addItem(driver_tla, driver_num)
        
        # 恢復選擇
        if current_driver:
            idx = self.cmb_driver.findText(current_driver, Qt.MatchStartsWith)
            if idx >= 0:
                self.cmb_driver.setCurrentIndex(idx)
        
        self.cmb_driver.blockSignals(False)
        
        # 更新顯示
        self._update_display()
    
    def _on_driver_changed(self, text: str):
        """車手選擇變更"""
        self._update_display()
    
    def _update_display(self):
        """更新顯示"""
        driver_code = self.cmb_driver.currentData()
        if not driver_code or driver_code not in self._explanations:
            self.lbl_win_prob.setText("勝率: --")
            self.lbl_base.setText("基準值: -- (平均勝率)")
            self.table.setRowCount(0)
            return
        
        explanation = self._explanations[driver_code]
        win_prob = explanation.get('win_probability', 0)
        base_value = explanation.get('base_value', 0.05)  # 預設 5% (1/20)
        contributions = explanation.get('feature_contributions', [])
        
        # 更新勝率標籤 (黑字)
        self.lbl_win_prob.setText(f"勝率: {win_prob:.1f}%")
        self.lbl_win_prob.setStyleSheet("font-size: 16px; font-weight: bold; color: #000000;")
        
        # 更新基準值
        self.lbl_base.setText(f"基準值: {base_value*100:.1f}% (平均勝率)")
        
        # 更新貢獻因素表格
        # 說明：貢獻值表示該因素對勝率的影響
        # 正值 = 提升勝率的因素，負值 = 降低勝率的因素
        # v3.4: 顯示 10 個因素 (包含輪胎優勢、賽道適應性、FP3/Q補償)
        max_display = 10
        self.table.setRowCount(min(len(contributions), max_display))
        
        for row, (feat_name, contrib) in enumerate(contributions[:max_display]):
            # 因素名稱 (翻譯)
            label = self.FEATURE_LABELS.get(feat_name, feat_name)
            feat_item = QTableWidgetItem(label)
            feat_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            feat_item.setForeground(QColor('#000000'))  # 黑字
            self.table.setItem(row, 0, feat_item)
            
            # 貢獻值 - 直接顯示 SHAP 值（不乘100、不顯示%）
            if contrib > 0:
                contrib_text = f"+{contrib:.2f}"
                bg_color = QColor('#90EE90')  # 淺綠色底 - 正面影響
            else:
                contrib_text = f"{contrib:.2f}"
                bg_color = QColor('#FFB6C1')  # 淺紅色底 - 負面影響
            
            contrib_item = QTableWidgetItem(contrib_text)
            contrib_item.setTextAlignment(Qt.AlignCenter)
            contrib_item.setForeground(QColor('#000000'))  # 黑字
            contrib_item.setBackground(bg_color)
            font = contrib_item.font()
            font.setBold(True)
            contrib_item.setFont(font)
            self.table.setItem(row, 1, contrib_item)


class RaceInsightsWidget(QWidget):
    """
    賽況提示面板 - 顯示場上值得關注的事件
    
    自動檢測並提示：
    1. DRS Zone (DRS 攻擊範圍) - 差距 < 1.0s，後車在 DRS 範圍內可開啟 DRS 超車
    2. Fight (近距離纏鬥) - 差距 < 1.5s，雙方正在激烈纏鬥
    3. Close (接近) - 差距 < 2.5s，後車正在逼近
    4. Tyre Cliff Warning (輪胎懸崖警告) - 輪胎已達到性能急劇下降的臨界圈數
    5. Undercut Window (進站策略窗口) - 可透過提前進站獲得 undercut 優勢
    6. Lead/Podium/P10 Battle (領先/領獎台/積分區爭奪) - 關鍵位置的爭奪戰
    7. Train Leader (路隊長) - 前方差距大但後方車隊密集的車手
    
    圖示說明：
    - 綠色圓點: DRS 攻擊範圍 (最高優先級)
    - 橙色圓點: 近距離纏鬥
    - 藍色圓點: 接近中
    - 黃色警告: 輪胎將達 cliff
    - 紅色警告: 輪胎已過 cliff
    - 扳手圖示: Undercut 機會
    - 獎盃圖示: 領獎台爭奪
    - 皇冠圖示: 領先爭奪
    - 積分圖示: P10 積分區爭奪
    - 火車圖示: 路隊長 (擋車)
    """
    
    # 閾值設定
    DRS_THRESHOLD = 1.0      # DRS 範圍 (秒)
    FIGHT_THRESHOLD = 1.5    # 纏鬥範圍 (秒)
    CLOSE_THRESHOLD = 2.5    # 接近範圍 (秒)
    UNDERCUT_WINDOW = 3.0    # 進站策略窗口 (秒)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._insights: List[Dict[str, Any]] = []
        self._last_update_lap: int = -1
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 提示列表 - 與控制訊息一致的樣式
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet("""
            QListWidget {
                font-size: 12px;
                font-family: "Consolas", "Microsoft JhengHei", monospace;
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                color: #000000;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #E0E0E0;
                color: #000000;
            }
            QListWidget::item:alternate {
                background-color: #F5F5F5;
            }
        """)
        layout.addWidget(self.list_widget)
        
        # 設置最小高度
        self.setMinimumHeight(120)
    
    def update_insights(
        self, 
        drivers: Dict[str, Dict], 
        tyre_state: Dict[str, Dict],
        current_lap: int,
        total_laps: int,
        predictions: Dict[str, Dict] = None
    ):
        """
        更新賽況提示
        
        Args:
            drivers: {driver_num: {position, gap_to_ahead, driver_tla, ...}}
            tyre_state: {driver_num: {compound, tyre_age, stint_count}}
            current_lap: 當前圈數
            total_laps: 總圈數
            predictions: {driver_num: {win_prob, tyre_advantage, ...}}
        """
        self._insights.clear()
        predictions = predictions or {}
        
        # 按位置排序
        sorted_drivers = sorted(
            drivers.items(),
            key=lambda x: x[1].get('position', 99)
        )
        
        # 1. 檢測 Fight 和 DRS 機會
        self._detect_battles(sorted_drivers, tyre_state, predictions)
        
        # 2. 檢測輪胎警告
        self._detect_tyre_warnings(sorted_drivers, tyre_state, current_lap)
        
        # 3. 檢測進站窗口
        self._detect_pit_windows(sorted_drivers, tyre_state, current_lap, total_laps)
        
        # 4. 檢測位置爭奪
        self._detect_position_battles(sorted_drivers, predictions)
        
        # 更新 UI
        self._refresh_display()
    
    def _detect_battles(
        self, 
        sorted_drivers: List[Tuple[str, Dict]], 
        tyre_state: Dict,
        predictions: Dict
    ):
        """檢測纏鬥和 DRS 機會"""
        for i in range(1, len(sorted_drivers)):
            driver_num, driver_data = sorted_drivers[i]
            prev_num, prev_data = sorted_drivers[i - 1]
            
            gap = self._parse_gap(driver_data.get('gap_to_ahead_display', ''))
            if gap is None or gap > self.CLOSE_THRESHOLD:
                continue
            
            driver_tla = driver_data.get('driver_tla', driver_num)
            prev_tla = prev_data.get('driver_tla', prev_num)
            position = driver_data.get('position', i + 1)
            
            # 獲取輪胎資訊
            driver_tyre = tyre_state.get(driver_num, {})
            prev_tyre = tyre_state.get(prev_num, {})
            driver_age = driver_tyre.get('tyre_age', 0) or 0
            prev_age = prev_tyre.get('tyre_age', 0) or 0
            tyre_diff = prev_age - driver_age  # 正值 = 後車輪胎更新
            
            # DRS 範圍
            if gap <= self.DRS_THRESHOLD:
                priority = 10  # DRS 不置頂
                tyre_hint = ""
                if tyre_diff > 5:
                    tyre_hint = f" [新胎+{tyre_diff}圈]"
                elif tyre_diff < -5:
                    tyre_hint = f" [舊胎{tyre_diff}圈]"
                
                self._insights.append({
                    'type': 'DRS',
                    'priority': priority,
                    'icon': '🟢',
                    'text': f"DRS! P{position} {driver_tla} -> {prev_tla} ({gap:.1f}s){tyre_hint}",
                    'color': '#00CC00',
                })
            # 纏鬥範圍
            elif gap <= self.FIGHT_THRESHOLD:
                priority = 11
                self._insights.append({
                    'type': 'FIGHT',
                    'priority': priority,
                    'icon': '🟠',
                    'text': f"Fight! P{position} {driver_tla} vs {prev_tla} ({gap:.1f}s)",
                    'color': '#FFA500',
                })
            # 接近
            elif gap <= self.CLOSE_THRESHOLD:
                priority = 12
                self._insights.append({
                    'type': 'CLOSE',
                    'priority': priority,
                    'icon': '🔵',
                    'text': f"Close: P{position} {driver_tla} -> {prev_tla} ({gap:.1f}s)",
                    'color': '#4488FF',
                })
    
    def _detect_tyre_warnings(
        self, 
        sorted_drivers: List[Tuple[str, Dict]], 
        tyre_state: Dict,
        current_lap: int
    ):
        """檢測輪胎懸崖警告"""
        # 輪胎 cliff 圈數 (基於 2023-2024 訓練數據)
        CLIFF_LAPS = {
            'SOFT': 11,
            'MEDIUM': 13,
            'HARD': 17,
            'INTERMEDIATE': 14,
            'WET': 20,
        }
        
        for driver_num, driver_data in sorted_drivers[:10]:  # 只看前 10 名
            tyre_info = tyre_state.get(driver_num, {})
            compound = tyre_info.get('compound', 'MEDIUM').upper()
            tyre_age = tyre_info.get('tyre_age', 0) or 0
            
            cliff_lap = CLIFF_LAPS.get(compound, 15)
            
            driver_tla = driver_data.get('driver_tla', driver_num)
            position = driver_data.get('position', 99)
            
            # 已過 cliff
            if tyre_age > cliff_lap + 3:
                self._insights.append({
                    'type': 'TYRE_CLIFF',
                    'priority': 4,
                    'icon': '⚠️',
                    'text': f"P{position} {driver_tla} 輪胎過 cliff! ({compound} {tyre_age}圈)",
                    'color': '#FF6B6B',
                })
            # 接近 cliff
            elif tyre_age >= cliff_lap - 2:
                self._insights.append({
                    'type': 'TYRE_WARNING',
                    'priority': 5,
                    'icon': '🟨',
                    'text': f"P{position} {driver_tla} 輪胎將 cliff ({compound} {tyre_age}/{cliff_lap}圈)",
                    'color': '#FFD93D',
                })
    
    def _detect_pit_windows(
        self, 
        sorted_drivers: List[Tuple[str, Dict]], 
        tyre_state: Dict,
        current_lap: int,
        total_laps: int
    ):
        """檢測進站窗口"""
        laps_remaining = total_laps - current_lap
        
        # 最後 5 圈不提示進站
        if laps_remaining <= 5:
            return
        
        # 檢測 undercut 機會
        for i in range(1, min(6, len(sorted_drivers))):  # 前 6 名
            driver_num, driver_data = sorted_drivers[i]
            prev_num, prev_data = sorted_drivers[i - 1]
            
            gap = self._parse_gap(driver_data.get('gap_to_ahead_display', ''))
            if gap is None or gap > self.UNDERCUT_WINDOW:
                continue
            
            driver_tyre = tyre_state.get(driver_num, {})
            prev_tyre = tyre_state.get(prev_num, {})
            
            driver_age = driver_tyre.get('tyre_age', 0) or 0
            prev_age = prev_tyre.get('tyre_age', 0) or 0
            driver_pits = driver_tyre.get('stint_count', 1) - 1
            prev_pits = prev_tyre.get('stint_count', 1) - 1
            
            driver_tla = driver_data.get('driver_tla', driver_num)
            prev_tla = prev_data.get('driver_tla', prev_num)
            position = driver_data.get('position', i + 1)
            
            # Undercut 機會: 後車輪胎較新且差距在窗口內
            if driver_pits <= prev_pits and driver_age < prev_age - 3 and gap <= 2.5:
                self._insights.append({
                    'type': 'UNDERCUT',
                    'priority': 3,
                    'icon': '🔧',
                    'text': f"Undercut? P{position} {driver_tla} 可先進站超 {prev_tla}",
                    'color': '#4ECDC4',
                })
    
    def _detect_position_battles(
        self, 
        sorted_drivers: List[Tuple[str, Dict]], 
        predictions: Dict
    ):
        """檢測重要位置爭奪和路隊長"""
        # 領先爭奪 (P1-P2) - 置頂 priority=1
        if len(sorted_drivers) >= 2:
            p1_num, p1_data = sorted_drivers[0]
            p2_num, p2_data = sorted_drivers[1]
            
            gap = self._parse_gap(p2_data.get('gap_to_ahead_display', ''))
            if gap is not None and gap <= 2.0:
                p1_tla = p1_data.get('driver_tla', p1_num)
                p2_tla = p2_data.get('driver_tla', p2_num)
                self._insights.append({
                    'type': 'LEAD_BATTLE',
                    'priority': 1,
                    'icon': '👑',
                    'text': f"領先爭奪! {p2_tla} 追擊 {p1_tla} ({gap:.1f}s)",
                    'color': '#FF69B4',
                })
        
        # 領獎台爭奪 (P3-P4) - 置頂 priority=2
        if len(sorted_drivers) >= 4:
            p3_num, p3_data = sorted_drivers[2]
            p4_num, p4_data = sorted_drivers[3]
            
            gap = self._parse_gap(p4_data.get('gap_to_ahead_display', ''))
            if gap is not None and gap <= 3.0:
                p3_tla = p3_data.get('driver_tla', p3_num)
                p4_tla = p4_data.get('driver_tla', p4_num)
                self._insights.append({
                    'type': 'PODIUM_BATTLE',
                    'priority': 2,
                    'icon': '🏆',
                    'text': f"領獎台爭奪! {p4_tla} vs {p3_tla} ({gap:.1f}s)",
                    'color': '#FFD700',
                })
        
        # P10 積分區爭奪 (P10-P11) - 置頂 priority=3
        if len(sorted_drivers) >= 11:
            p10_num, p10_data = sorted_drivers[9]
            p11_num, p11_data = sorted_drivers[10]
            
            gap = self._parse_gap(p11_data.get('gap_to_ahead_display', ''))
            if gap is not None and gap <= 2.5:
                p10_tla = p10_data.get('driver_tla', p10_num)
                p11_tla = p11_data.get('driver_tla', p11_num)
                self._insights.append({
                    'type': 'POINTS_BATTLE',
                    'priority': 3,
                    'icon': '🎯',
                    'text': f"積分區爭奪! {p11_tla} vs {p10_tla} ({gap:.1f}s)",
                    'color': '#9932CC',
                })
        
        # 路隊長檢測 - 前方差距大但後方車隊密集
        self._detect_train_leaders(sorted_drivers)
    
    def _detect_train_leaders(self, sorted_drivers: List[Tuple[str, Dict]]):
        """
        檢測路隊長 (Train Leader)
        
        條件：
        1. 與前車差距 > 3.0s (明顯落後)
        2. 後方至少有 2 台車
        3. 後方車隊平均間距 < 1.5s (密集)
        4. 位置在 P5-P15 之間 (不是領跑者)
        """
        if len(sorted_drivers) < 5:
            return
        
        for i in range(4, min(15, len(sorted_drivers) - 2)):  # P5 到 P15
            driver_num, driver_data = sorted_drivers[i]
            
            # 計算與前車差距
            gap_to_ahead = self._parse_gap(driver_data.get('gap_to_ahead_display', ''))
            if gap_to_ahead is None or gap_to_ahead < 3.0:
                continue  # 與前車太近，不是路隊長
            
            # 檢查後方車隊 (最多看 4 台)
            train_cars = []
            for j in range(i + 1, min(i + 5, len(sorted_drivers))):
                behind_num, behind_data = sorted_drivers[j]
                behind_gap = self._parse_gap(behind_data.get('gap_to_ahead_display', ''))
                if behind_gap is not None and behind_gap <= 2.0:
                    train_cars.append((behind_data.get('driver_tla', behind_num), behind_gap))
                else:
                    break  # 後方有大間距，車隊結束
            
            # 至少 2 台車被堵住才算路隊長
            if len(train_cars) >= 2:
                driver_tla = driver_data.get('driver_tla', driver_num)
                position = driver_data.get('position', i + 1)
                avg_gap = sum(g for _, g in train_cars) / len(train_cars)
                
                train_tlas = ', '.join([tla for tla, _ in train_cars[:3]])
                if len(train_cars) > 3:
                    train_tlas += f" +{len(train_cars)-3}"
                
                self._insights.append({
                    'type': 'TRAIN_LEADER',
                    'priority': 5,  # 中等優先級
                    'icon': '🚂',
                    'text': f"路隊長! P{position} {driver_tla} 擋住 {train_tlas} (前{gap_to_ahead:.1f}s/後{avg_gap:.1f}s)",
                    'color': '#FF6B6B',
                })
    
    def _parse_gap(self, gap_str: str) -> Optional[float]:
        """解析差距字串"""
        if not gap_str:
            return None
        try:
            gap_str = gap_str.replace('+', '').replace('s', '').strip()
            if 'LAP' in gap_str.upper() or 'L' in gap_str.upper():
                return None
            return float(gap_str)
        except (ValueError, TypeError):
            return None
    
    def _refresh_display(self):
        """刷新顯示"""
        self.list_widget.clear()
        
        if not self._insights:
            item = QListWidgetItem("目前無特別事件")
            item.setForeground(QColor('#888888'))
            self.list_widget.addItem(item)
            return
        
        # 按優先級排序
        sorted_insights = sorted(self._insights, key=lambda x: x['priority'])
        
        for insight in sorted_insights[:10]:  # 最多顯示 10 個
            text = f"{insight['icon']} {insight['text']}"
            item = QListWidgetItem(text)
            item.setForeground(QColor(insight['color']))
            self.list_widget.addItem(item)


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
        self.table.setColumnWidth(4, 120)  # 輪胎策略
        self.table.setColumnWidth(5, 45)   # 當前輪胎+圈數
        
        # === 輸出 PIT 統計表欄位寬度 ===
        print("=" * 60)
        print("[PitStopTableWidget] 欄位寬度設定 (共6欄):")
        print(f"  0:車手=40, 1:進站=65, 2:進站圈數=65, 3:PIT耗時=65, 4:輪胎策略=120, 5:當前=45")
        total_width = 40+65+65+65+120+45
        print(f"  總寬度: {total_width}px")
        print("=" * 60)
        
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
            
            # 當前輪胎 (使用即時狀態的最後一個輪胎) + 使用圈數
            tyre_age = tyre_info.get('tyre_age', 0) or 0
            if tyre_age > 0:
                current_text = f"{current_tyre}{tyre_age}"
            else:
                current_text = current_tyre
            
            current_item = QTableWidgetItem(current_text)
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
        """初始化 UI - Super Table (包含 PIT 資訊)"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 表格 - Super Table: 合併排名 + PIT 資訊
        # 欄位: P, +/-, No, 胎, TyreAge, Pit#, TyreHist, 車手, S1-S3, 上圈, 最佳, 差距, 領先, 前車, 圈, P1-3%, SPD, G, DRS
        self.table = QTableWidget()
        self.table.setColumnCount(22)  # 精簡版: 移除 RPM/THR/BRK，新增 TyreAge/Pit#/TyreHist
        self.table.setHorizontalHeaderLabels([
            "P", "+/-", "No", "胎", "齡", "Pit", "換胎",  # 基本 + PIT 資訊
            "車手", "S1", "S2", "S3",  # 車手 + 區間
            "上圈", "最佳", "差距", "領先", "前車", "圈",  # 時間
            "P1%", "P2%", "P3%",  # 勝率
            "SPD", "DRS"  # 遙測 (精簡)
        ])
        
        # 啟用排序功能
        self.table.setSortingEnabled(True)
        
        # 設置表格屬性
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 緊湊欄位寬度 (Super Table)
        self.table.setColumnWidth(0, 22)   # P 排名
        self.table.setColumnWidth(1, 33)   # +/- (+5px)
        self.table.setColumnWidth(2, 26)   # No 車號
        self.table.hideColumn(2)           # 隱藏 No 欄位
        self.table.setColumnWidth(3, 22)   # 胎 (輪胎種類)
        self.table.setColumnWidth(4, 26)   # 齡 (輪胎年齡)
        self.table.setColumnWidth(5, 26)   # Pit (進站次數)
        self.table.setColumnWidth(6, 70)   # 換胎 (TyreHist: M→H→S)
        self.table.hideColumn(6)           # 隱藏換胎欄位
        self.table.setColumnWidth(7, 45)   # 車手 (+5px)
        self.table.setColumnWidth(8, 58)   # S1
        self.table.setColumnWidth(9, 58)   # S2
        self.table.setColumnWidth(10, 58)  # S3
        self.table.setColumnWidth(11, 70)  # 上圈
        self.table.setColumnWidth(12, 70)  # 最佳
        self.table.setColumnWidth(13, 60)  # 差距 (Gap to Best: 當前圈速與個人最佳的差距)
        self.table.setColumnWidth(14, 75)  # 領先 (Gap to Leader: 與P1的累計時間差)
        self.table.setColumnWidth(15, 75)  # 前車 (Interval: 與前一名的間隔)
        self.table.setColumnWidth(16, 28)  # 圈
        self.table.setColumnWidth(17, 41)  # P1%
        self.table.setColumnWidth(18, 41)  # P2%
        self.table.setColumnWidth(19, 41)  # P3%
        self.table.setColumnWidth(20, 36)  # SPD
        self.table.setColumnWidth(21, 32)  # DRS
        
        # 表頭設置
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # 緊湊行高
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.verticalHeader().setVisible(False)
        
        # 右鍵選單
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Pit Window 參考 (會在主視窗中設置)
        self._pit_window = None
        
        layout.addWidget(self.table)
    
    def set_pit_window(self, pit_window):
        """設置關聯的 Pit Window (用於右鍵選單)"""
        self._pit_window = pit_window
    
    def _show_context_menu(self, pos):
        """顯示右鍵選單"""
        item = self.table.itemAt(pos)
        if item is None:
            return
        
        row = item.row()
        driver_item = self.table.item(row, 7)  # 車手欄位
        if driver_item is None:
            return
        
        driver_data = driver_item.data(Qt.UserRole)
        if not driver_data:
            return
        
        driver_num = driver_data.get('driver_num', '')
        driver_tla = driver_data.get('driver_tla', driver_num)
        
        menu = QMenu(self.table)
        
        # 設為 Pit Window 中心點
        if self._pit_window:
            set_ref_action = menu.addAction(f"設 {driver_tla} 為 Pit Window 中心點")
            set_ref_action.triggered.connect(lambda: self._set_pit_reference(driver_num))
        
        menu.exec_(self.table.viewport().mapToGlobal(pos))
    
    def _set_pit_reference(self, driver_num: str):
        """設置 Pit Window 的參考車手"""
        if self._pit_window:
            self._pit_window.set_reference_driver(driver_num)
    
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
        # 修復：確保 position 為 None 時使用 999 作為預設值
        def get_sort_key(item):
            pos = item[1].get('position')
            if pos is None:
                return 999
            try:
                return int(pos)
            except (ValueError, TypeError):
                return 999
        
        sorted_drivers = sorted(drivers.items(), key=get_sort_key)
        
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
            
            # No - 車號 (欄位 2)
            num_item = QTableWidgetItem(driver_num)
            num_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, num_item)
            
            # === PIT 相關欄位 (欄位 3-6) ===
            tyre_info = self._current_tyre_state.get(driver_num, {})
            compound = tyre_info.get('compound', 'UNKNOWN')
            tyre_abbrev = TYRE_ABBREV.get(compound, '?')
            tyre_color = TYRE_COLORS.get(compound, TYRE_COLORS['UNKNOWN'])
            
            # 胎 - 輪胎 (欄位 3)
            tyre_item = QTableWidgetItem(tyre_abbrev)
            tyre_item.setTextAlignment(Qt.AlignCenter)
            tyre_item.setBackground(QColor(tyre_color))
            if compound in ['HARD', 'MEDIUM']:
                tyre_item.setForeground(QColor('#000000'))
            else:
                tyre_item.setForeground(QColor('#FFFFFF'))
            tyre_font = tyre_item.font()
            tyre_font.setBold(True)
            tyre_item.setFont(tyre_font)
            self.table.setItem(row, 3, tyre_item)
            
            # 齡 - 輪胎壽命 (欄位 4)
            tyre_age = tyre_info.get('tyre_age', tyre_info.get('stint_length', ''))
            age_item = QTableWidgetItem(str(tyre_age) if tyre_age else '')
            age_item.setTextAlignment(Qt.AlignCenter)
            # 顏色編碼：>20圈黃色、>30圈橙色、>40圈紅色
            if tyre_age:
                try:
                    age_val = int(tyre_age)
                    if age_val >= 40:
                        age_item.setBackground(QColor('#FF4444'))  # 紅色
                        age_item.setForeground(QColor('#FFFFFF'))
                    elif age_val >= 30:
                        age_item.setBackground(QColor('#FFA500'))  # 橙色
                        age_item.setForeground(QColor('#000000'))
                    elif age_val >= 20:
                        age_item.setBackground(QColor('#FFFF00'))  # 黃色
                        age_item.setForeground(QColor('#000000'))
                except (ValueError, TypeError):
                    pass
            self.table.setItem(row, 4, age_item)
            
            # Pit - 進站次數 (欄位 5)
            stint_count = tyre_info.get('stint_count', 0)
            pit_count = max(0, stint_count - 1) if stint_count else 0
            pit_item = QTableWidgetItem(str(pit_count) if pit_count > 0 else '0')
            pit_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, pit_item)
            
            # 換胎 - 輪胎歷史 (欄位 6)
            stints = tyre_info.get('stints', [])
            if stints:
                tyre_hist = '→'.join([TYRE_ABBREV.get(s.get('compound', 'UNKNOWN'), '?') for s in stints])
            else:
                tyre_hist = tyre_abbrev  # 只顯示當前輪胎
            hist_item = QTableWidgetItem(tyre_hist)
            hist_item.setTextAlignment(Qt.AlignCenter)
            hist_item.setToolTip(f"輪胎策略: {tyre_hist}")
            self.table.setItem(row, 6, hist_item)
            
            # 車手 (欄位 7) - 添加車隊顏色背景
            driver_display = driver_data.get('driver_tla', driver_num)
            driver_item = QTableWidgetItem(driver_display)
            driver_item.setTextAlignment(Qt.AlignCenter)
            
            # 設置車隊顏色背景
            team_color = driver_data.get('team_color', 'CCCCCC')
            if team_color and not team_color.startswith('#'):
                team_color = f'#{team_color}'
            driver_item.setBackground(QColor(team_color))
            # 根據背景色調調整文字顏色
            bg_color = QColor(team_color)
            luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()) / 255
            if luminance < 0.5:
                driver_item.setForeground(QColor('#FFFFFF'))  # 深色背景用白字
            else:
                driver_item.setForeground(QColor('#000000'))  # 淺色背景用黑字
            driver_font = driver_item.font()
            driver_font.setBold(True)
            driver_item.setFont(driver_font)
            # 儲存車手資訊以便右鍵選單使用
            driver_item.setData(Qt.UserRole, {'driver_num': driver_num, 'driver_tla': driver_display})
            self.table.setItem(row, 7, driver_item)
            
            # === Sector 時間 (欄位 8-10) ===
            for sector_idx in range(3):
                sector_name = f's{sector_idx + 1}'
                sector_time = driver_data.get(f'{sector_name}_time', '')
                sector_personal = driver_data.get(f'{sector_name}_personal_fastest', False)
                sector_overall = driver_data.get(f'{sector_name}_overall_fastest', False)
                
                sector_item = QTableWidgetItem(sector_time if sector_time else '')
                sector_item.setTextAlignment(Qt.AlignCenter)
                
                # Sector 顏色編碼
                if sector_overall:
                    sector_item.setBackground(QColor('#FF00FF'))  # 紫色底 - 全場最快
                    sector_item.setForeground(QColor('#000000'))
                    sector_font = sector_item.font()
                    sector_font.setBold(True)
                    sector_item.setFont(sector_font)
                elif sector_personal:
                    sector_item.setBackground(QColor('#00FF00'))  # 綠色底 - 個人最快
                    sector_item.setForeground(QColor('#000000'))
                    sector_font = sector_item.font()
                    sector_font.setBold(True)
                    sector_item.setFont(sector_font)
                
                self.table.setItem(row, 8 + sector_idx, sector_item)
            
            # 上圈 - Last Lap Time (欄位 11)
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
            
            self.table.setItem(row, 11, last_lap_item)
            
            # 最佳 - Best Lap Time (欄位 12)
            best_lap_time = driver_data.get('best_lap_time', '')
            best_lap_item = QTableWidgetItem(best_lap_time if best_lap_time else '')
            best_lap_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 12, best_lap_item)
            
            # 差距 - Delta (Last - Best) (欄位 13)
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
            
            self.table.setItem(row, 13, delta_item)
            
            # 領先 - Gap to Leader (欄位 14)
            gap_leader_text = driver_data.get('gap_to_leader_display')
            if not gap_leader_text:
                gap_leader_text = "" if driver_data.get('position') == 1 else ""
            gap_leader_item = QTableWidgetItem(gap_leader_text)
            gap_leader_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 14, gap_leader_item)
            
            # 前車 - Gap to Ahead (欄位 15)
            gap_ahead_text = driver_data.get('gap_to_ahead_display')
            if not gap_ahead_text:
                gap_ahead_text = "" if driver_data.get('position') == 1 else ""
            gap_ahead_item = QTableWidgetItem(gap_ahead_text)
            gap_ahead_item.setTextAlignment(Qt.AlignCenter)
            
            # 前車顏色編碼：越接近0秒越綠色，越接近5秒越紅色，5秒以後白色
            if gap_ahead_text and gap_ahead_text not in ('', '-', 'LAP'):
                try:
                    # 解析秒數 (可能是 "+1.234" 或 "1.234" 或 "1.234s")
                    gap_str = gap_ahead_text.replace('+', '').replace('s', '').strip()
                    gap_seconds = float(gap_str)
                    
                    if gap_seconds >= 5.0:
                        # 5秒以上: 白色背景
                        gap_ahead_item.setBackground(QColor('#FFFFFF'))
                        gap_ahead_item.setForeground(QColor('#000000'))
                    elif gap_seconds <= 0.0:
                        # 0秒以下: 綠色
                        gap_ahead_item.setBackground(QColor('#00FF00'))
                        gap_ahead_item.setForeground(QColor('#000000'))
                    else:
                        # 0~5秒: 漸變 (綠色 -> 黃色 -> 紅色)
                        ratio = gap_seconds / 5.0  # 0.0 ~ 1.0
                        if ratio < 0.5:
                            # 0~2.5秒: 綠色 -> 黃色
                            r = int(255 * (ratio * 2))
                            g = 255
                            b = 0
                        else:
                            # 2.5~5秒: 黃色 -> 紅色
                            r = 255
                            g = int(255 * (1 - (ratio - 0.5) * 2))
                            b = 0
                        gap_ahead_item.setBackground(QColor(r, g, b))
                        gap_ahead_item.setForeground(QColor('#000000'))
                except (ValueError, AttributeError):
                    pass  # 無法解析時不設置顏色
            
            self.table.setItem(row, 15, gap_ahead_item)
            
            # 圈 - 圈數 (欄位 16)
            lap_item = QTableWidgetItem(str(driver_data.get('lap') or ''))
            lap_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 16, lap_item)
            
            # === 勝率欄位 (欄位 17-19) ===
            win_prob = driver_data.get('win_probability', '')
            p2_prob = driver_data.get('p2_probability', '')
            p3_prob = driver_data.get('p3_probability', '')
            
            # P1% (欄位 17)
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
            self.table.setItem(row, 17, win_item)
            
            # P2% (欄位 18)
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
            self.table.setItem(row, 18, p2_item)
            
            # P3% (欄位 19)
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
            self.table.setItem(row, 19, p3_item)
            
            # === 遙測資料 (欄位 20-21) ===
            car_data = self._current_car_data.get(driver_num, {})
            
            # Speed (欄位 20)
            speed = car_data.get('speed', '')
            speed_item = QTableWidgetItem(str(speed) if speed else '')
            speed_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 20, speed_item)
            
            # DRS (欄位 21)
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
            self.table.setItem(row, 21, drs_item)
    
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
    progress_updated = pyqtSignal(int, int)  # 發送當前索引和總數
    play_state_changed = pyqtSignal(bool)  # 發送播放狀態 (True=播放中)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._snapshots = []
        self._current_index = 0
        self._is_playing = False
        self._playback_speed = 1.0
        
        # 真實時間播放相關
        self._playback_time = 0.0  # 當前播放的比賽時間 (秒)
        self._last_tick_time = 0.0  # 上次 tick 的系統時間
        
        # 防止 slider 回調干擾播放時間
        self._programmatic_slider_update = False
        
        # 定時器 - 固定 50ms 間隔用於流暢 UI
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.setInterval(50)  # 固定 50ms (20fps UI 更新)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI - 水平佈局版本"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # 時間顯示
        self.lbl_time = QLabel("00:00:00")
        time_font = QFont()
        time_font.setPointSize(9)
        time_font.setBold(True)
        self.lbl_time.setFont(time_font)
        self.lbl_time.setMinimumWidth(70)
        layout.addWidget(self.lbl_time)
        
        # 播放按鈕
        self.btn_play = QPushButton("播放")
        self.btn_play.clicked.connect(self._on_play_clicked)
        self.btn_play.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_play.setFixedWidth(50)
        layout.addWidget(self.btn_play)
        
        # 暫停按鈕
        self.btn_pause = QPushButton("暫停")
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        self.btn_pause.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.btn_pause.setEnabled(False)
        self.btn_pause.setFixedWidth(50)
        layout.addWidget(self.btn_pause)
        
        # 速度選擇
        layout.addWidget(QLabel("速度:"))
        self.cmb_speed = QComboBox()
        self.cmb_speed.addItems(["1x", "2x", "4x", "8x", "16x", "32x", "64x"])
        self.cmb_speed.currentTextChanged.connect(self._on_speed_changed)
        self.cmb_speed.setFixedWidth(55)
        layout.addWidget(self.cmb_speed)
        
        # 時間軸滑桿
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.slider.setMinimumWidth(150)
        layout.addWidget(self.slider, stretch=1)
        
        # 進度顯示
        self.lbl_progress = QLabel("0 / 0")
        self.lbl_progress.setMinimumWidth(60)
        layout.addWidget(self.lbl_progress)
    
    def set_snapshots(self, snapshots: List[Dict]):
        """設置數據源"""
        self._snapshots = snapshots
        maximum = max(0, len(snapshots) - 1)
        self.slider.setMaximum(maximum)
        if maximum == 0:
            self.slider.setValue(0)
        else:
            # 初始化播放時間為第一幀的比賽時間
            self._playback_time = snapshots[0].get('race_time_seconds', 0.0)
        self._update_display()
    
    def _get_snapshot_time(self, index: int) -> float:
        """獲取指定索引 snapshot 的比賽時間 (秒)"""
        if 0 <= index < len(self._snapshots):
            return self._snapshots[index].get('race_time_seconds', 0.0)
        return 0.0
    
    def _find_index_for_time(self, target_time: float) -> int:
        """根據目標比賽時間找到對應的 snapshot 索引"""
        if not self._snapshots:
            return 0
        
        # 二分搜索找到最接近的索引
        left, right = 0, len(self._snapshots) - 1
        while left < right:
            mid = (left + right) // 2
            mid_time = self._get_snapshot_time(mid)
            if mid_time < target_time:
                left = mid + 1
            else:
                right = mid
        
        return left
    
    def _on_timer_tick(self):
        """
        定時器回調 - 基於真實時間播放
        
        邏輯：
        1. 計算自上次 tick 經過的真實時間
        2. 乘以播放速度，得到比賽時間增量
        3. 更新播放時間，找到對應的 snapshot
        """
        import time
        
        current_time = time.time()
        if self._last_tick_time == 0:
            self._last_tick_time = current_time
            return
        
        # 計算經過的真實時間 (秒)
        elapsed_real = current_time - self._last_tick_time
        self._last_tick_time = current_time
        
        # 計算比賽時間增量 (乘以播放速度)
        elapsed_race = elapsed_real * self._playback_speed
        old_playback_time = self._playback_time
        self._playback_time += elapsed_race
        
        # 調試輸出 (每 20 次輸出一次)
        if not hasattr(self, '_tick_count'):
            self._tick_count = 0
        self._tick_count += 1
        if self._tick_count % 20 == 0:
            print(f"[PLAYBACK] elapsed_real={elapsed_real:.3f}s, speed={self._playback_speed}x, "
                  f"playback_time={self._playback_time:.3f}s, index={self._current_index}")
        
        # 找到對應的 snapshot 索引
        new_index = self._find_index_for_time(self._playback_time)
        
        # 檢查是否到達結尾
        if new_index >= len(self._snapshots) - 1:
            self._current_index = len(self._snapshots) - 1
            self._programmatic_slider_update = True
            self.slider.setValue(self._current_index)
            self._programmatic_slider_update = False
            self._on_pause_clicked()
            return
        
        # 只有索引變化時才更新 UI
        if new_index != self._current_index:
            self._current_index = new_index
            # 使用標記防止 slider 回調重設播放時間
            self._programmatic_slider_update = True
            self.slider.setValue(self._current_index)
            self._programmatic_slider_update = False
    
    def _on_slider_changed(self, value: int):
        """時間軸拖動（僅在用戶手動拖動時重設播放時間）"""
        self._current_index = value
        # 只有用戶手動拖動時才重設播放時間
        if not self._programmatic_slider_update:
            self._playback_time = self._get_snapshot_time(value)
        self._update_display()
        self.time_changed.emit(self._current_index)
    
    def _on_play_clicked(self):
        """播放"""
        import time
        
        self._is_playing = True
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.play_state_changed.emit(True)
        
        # 初始化播放時間和上次 tick 時間
        self._playback_time = self._get_snapshot_time(self._current_index)
        self._last_tick_time = time.time()
        
        # 啟動定時器 (固定 50ms 間隔)
        self._timer.start()
    
    def _on_pause_clicked(self):
        """暫停"""
        self._is_playing = False
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.play_state_changed.emit(False)
        self._timer.stop()
        self._last_tick_time = 0  # 重置
    
    def _on_speed_changed(self, text: str):
        """速度變更"""
        speed_map = {"1x": 1.0, "2x": 2.0, "4x": 4.0, "8x": 8.0, "16x": 16.0, "32x": 32.0, "64x": 64.0}
        self._playback_speed = speed_map.get(text, 1.0)
        # 不需要重啟定時器，因為是固定間隔
    
    def _update_display(self):
        """更新顯示"""
        if 0 <= self._current_index < len(self._snapshots):
            snapshot = self._snapshots[self._current_index]
            # 只顯示時間，不顯示「比賽時間:」前綴
            race_time = snapshot.get('race_time', '00:00:00')
            # 如果時間太長，截取到秒
            if '.' in race_time:
                race_time = race_time.split('.')[0]
            self.lbl_time.setText(race_time)
            self.lbl_progress.setText(f"{self._current_index + 1} / {len(self._snapshots)}")
            # 發送進度更新 signal
            self.progress_updated.emit(self._current_index + 1, len(self._snapshots))
    
    def get_current_index(self) -> int:
        """獲取當前索引"""
        return self._current_index


class LivePositionTrackingMainWindow(QMainWindow):
    """主視窗 - 支援即時模式和歷史回放模式"""
    
    # 模式常數
    MODE_HISTORICAL = "historical"
    MODE_REALTIME = "realtime"
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.setWindowTitle("F1 即時車手位置追蹤系統 - Live Timing")
        self.setGeometry(100, 100, 1600, 900)
        
        # 當前模式
        self._mode = self.MODE_REALTIME  # 預設即時模式
        
        # 數據處理器
        self.processor = None
        self._snapshots: List[Dict[str, Any]] = []
        self._total_race_duration_seconds: float = 0.0
        self._total_laps: int = 57  # Qatar 預設圈數
        self._car_data: Dict = {}   # CarData 遙測資料
        
        # 即時數據源
        self._realtime_source: Optional[RealTimeLiveF1DataSource] = None
        self._realtime_update_timer: Optional[QTimer] = None
        
        # 賽事選擇 (歷史模式)
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
        
        # 預設啟動即時模式
        self._switch_to_realtime_mode()
    
    def _init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # === 模式選擇區域 ===
        mode_layout = QHBoxLayout()
        
        # 模式選擇
        mode_layout.addWidget(QLabel("模式:"))
        self.btn_group_mode = QButtonGroup(self)
        
        self.radio_realtime = QRadioButton("即時 Live Timing")
        self.radio_realtime.setChecked(True)
        self.radio_realtime.toggled.connect(self._on_mode_changed)
        self.btn_group_mode.addButton(self.radio_realtime)
        mode_layout.addWidget(self.radio_realtime)
        
        self.radio_historical = QRadioButton("歷史回放")
        self.btn_group_mode.addButton(self.radio_historical)
        mode_layout.addWidget(self.radio_historical)
        
        mode_layout.addWidget(QLabel("  |  "))
        
        # 即時模式控制
        self.btn_connect = QPushButton("連接 Live Timing")
        self.btn_connect.clicked.connect(self._on_connect_clicked)
        self.btn_connect.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        mode_layout.addWidget(self.btn_connect)
        
        self.btn_disconnect = QPushButton("斷開連接")
        self.btn_disconnect.clicked.connect(self._on_disconnect_clicked)
        self.btn_disconnect.setEnabled(False)
        mode_layout.addWidget(self.btn_disconnect)
        
        # 連接狀態
        self.lbl_connection_status = QLabel("連接已關閉")
        self.lbl_connection_status.setStyleSheet("color: #888888; font-weight: bold;")
        mode_layout.addWidget(self.lbl_connection_status)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # === 歷史模式賽事選擇區域 (預設隱藏) ===
        self.historical_widget = QWidget()
        race_selector_layout = QHBoxLayout(self.historical_widget)
        race_selector_layout.setContentsMargins(0, 0, 0, 0)
        
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
        
        # 賽事資訊標籤
        self.lbl_race_info = QLabel("請選擇賽事")
        self.lbl_race_info.setStyleSheet("color: #888888;")
        race_selector_layout.addWidget(self.lbl_race_info)
        
        race_selector_layout.addStretch()
        
        self.historical_widget.hide()  # 預設隱藏
        layout.addWidget(self.historical_widget)
        
        # === 時間軸控制器 (水平版，放在上方) ===
        self.timeline_control = TimelineControlWidget()
        self.timeline_control.time_changed.connect(self._on_time_changed)
        self.timeline_control.setVisible(False)  # 預設隱藏，歷史模式才顯示
        mode_layout.addWidget(self.timeline_control, stretch=1)
        
        mode_layout.addWidget(QLabel("  |  "))  # 分隔線
        
        # 隱藏/顯示比賽控制訊息按鈕 (放在模式列)
        self.btn_toggle_race_control = QPushButton("隱藏訊息")
        self.btn_toggle_race_control.setCheckable(True)
        self.btn_toggle_race_control.clicked.connect(self._toggle_race_control)
        mode_layout.addWidget(self.btn_toggle_race_control)
        
        # 隱藏/顯示 SHAP 面板按鈕 (預設隱藏)
        self.btn_toggle_shap = QPushButton("顯示SHAP")
        self.btn_toggle_shap.setCheckable(True)
        self.btn_toggle_shap.setChecked(True)  # 預設 checked = 隱藏狀態
        self.btn_toggle_shap.clicked.connect(self._toggle_shap)
        mode_layout.addWidget(self.btn_toggle_shap)
        
        # 輪胎策略圖按鈕 (內嵌版本 toggle)
        self.btn_tyre_strategy = QPushButton("隱藏輪胎")
        self.btn_tyre_strategy.setCheckable(True)
        self.btn_tyre_strategy.clicked.connect(self._toggle_tyre_strategy)
        self.btn_tyre_strategy.setStyleSheet("background-color: #FF6600; color: white; font-weight: bold;")
        mode_layout.addWidget(self.btn_tyre_strategy)
        
        # Pit Window 按鈕 (toggle)
        self.btn_pit_window = QPushButton("隱藏Pit")
        self.btn_pit_window.setCheckable(True)
        self.btn_pit_window.clicked.connect(self._toggle_pit_window)
        self.btn_pit_window.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")
        mode_layout.addWidget(self.btn_pit_window)
        
        # Print 寬度按鈕 (用於調試)
        self.btn_print_widths = QPushButton("Print 寬度")
        self.btn_print_widths.clicked.connect(self._print_all_widths)
        self.btn_print_widths.setStyleSheet("background-color: #666666; color: white;")
        mode_layout.addWidget(self.btn_print_widths)
        
        # === 頂部區域：賽事資訊面板（圈數、天氣、賽道狀態） ===
        self.race_info = RaceInfoWidget()
        layout.addWidget(self.race_info)
        
        # === 三欄式主分割器 (Single Pane of Glass 設計) ===
        # 比例 3:6:3 → 左(地圖+圈速分佈) : 中(排名+輪胎策略) : 右(控制訊息+賽況)
        main_splitter = QSplitter(Qt.Horizontal)
        
        # === 左欄：水平分割 (地圖區 | 圈速分佈) ===
        left_panel = QSplitter(Qt.Horizontal)
        
        # 左側：地圖區垂直堆疊 (賽道地圖 + 圓形地圖)
        left_maps_panel = QSplitter(Qt.Vertical)
        
        # 左上：賽道地圖
        map_group = QGroupBox("賽道地圖")
        map_layout = QVBoxLayout()
        map_layout.setContentsMargins(2, 2, 2, 2)
        self.track_map = TrackMapWidget()
        map_layout.addWidget(self.track_map)
        map_group.setLayout(map_layout)
        left_maps_panel.addWidget(map_group)
        
        # 左中：圓形賽道地圖
        circle_map_group = QGroupBox("圓形賽道圖")
        circle_map_layout = QVBoxLayout()
        circle_map_layout.setContentsMargins(2, 2, 2, 2)
        self.circle_map = CircleMapWidget()
        circle_map_layout.addWidget(self.circle_map)
        circle_map_group.setLayout(circle_map_layout)
        left_maps_panel.addWidget(circle_map_group)
        
        # 左下：SHAP 勝率分析 (預設隱藏)
        self.shap_group = QGroupBox("SHAP 勝率分析")
        shap_layout = QVBoxLayout()
        shap_layout.setContentsMargins(2, 2, 2, 2)
        self.shap_widget = SHAPExplanationWidget()
        shap_layout.addWidget(self.shap_widget)
        self.shap_group.setLayout(shap_layout)
        left_maps_panel.addWidget(self.shap_group)
        
        # 地圖區垂直比例 (地圖:圓形圖:SHAP = 300:300:0)
        left_maps_panel.setSizes([300, 300, 0])
        self.shap_group.hide()  # 預設隱藏 SHAP 面板
        
        left_panel.addWidget(left_maps_panel)
        
        # 右側：圈速分佈 Widget
        lap_time_group = QGroupBox("Lap Time")
        lap_time_layout = QVBoxLayout()
        lap_time_layout.setContentsMargins(2, 2, 2, 2)
        self.lap_time_dist = LapTimeDistributionWidget()
        lap_time_layout.addWidget(self.lap_time_dist)
        lap_time_group.setLayout(lap_time_layout)
        left_panel.addWidget(lap_time_group)
        
        # 左欄水平比例 (地圖區:圈速分佈 = 452:207)
        left_panel.setSizes([452, 207])
        
        main_splitter.addWidget(left_panel)
        
        # === 中欄：排名表 + Pit Window + 輪胎策略圖 垂直堆疊 ===
        center_panel = QSplitter(Qt.Vertical)
        
        # 中上：實時排名表
        table_group = QGroupBox("實時排名")
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(2, 2, 2, 2)
        self.ranking_table = LiveRankingTableWidget()
        table_layout.addWidget(self.ranking_table)
        table_group.setLayout(table_layout)
        center_panel.addWidget(table_group)
        
        # 中間：Pit Window (進站策略窗口)
        self.pit_window_group = QGroupBox("Pit Window")
        pit_window_layout = QVBoxLayout()
        pit_window_layout.setContentsMargins(2, 2, 2, 2)
        self.pit_window = PitWindowWidget()
        pit_window_layout.addWidget(self.pit_window)
        self.pit_window_group.setLayout(pit_window_layout)
        center_panel.addWidget(self.pit_window_group)
        
        # 連接 Ranking Table 和 Pit Window (右鍵選單功能)
        self.ranking_table.set_pit_window(self.pit_window)
        
        # 中下：輪胎策略圖
        self.tyre_strategy_group = QGroupBox("輪胎策略")
        tyre_strategy_layout = QVBoxLayout()
        tyre_strategy_layout.setContentsMargins(2, 2, 2, 2)
        self.tyre_strategy_chart = TyreStrategyChartWidget()
        tyre_strategy_layout.addWidget(self.tyre_strategy_chart)
        self.tyre_strategy_group.setLayout(tyre_strategy_layout)
        center_panel.addWidget(self.tyre_strategy_group)
        
        # 中欄垂直比例 (排名:Pit Window:輪胎策略)
        # 預設值基於實際測量: 排名533px, Pit105px, 輪胎498px
        center_panel.setSizes([533, 105, 498])
        
        # 保存中欄分割器引用
        self.center_splitter = center_panel
        
        main_splitter.addWidget(center_panel)
        
        # === 右欄：控制訊息 + 賽況提示 垂直堆疊 ===
        right_panel = QSplitter(Qt.Vertical)
        
        # 右上：比賽控制訊息
        self.race_control_group = QGroupBox("比賽控制訊息")
        race_control_layout = QVBoxLayout()
        race_control_layout.setContentsMargins(2, 2, 2, 2)
        self.race_control_widget = RaceControlMessagesWidget()
        race_control_layout.addWidget(self.race_control_widget)
        self.race_control_group.setLayout(race_control_layout)
        right_panel.addWidget(self.race_control_group)
        
        # 右下：賽況提示
        insights_group = QGroupBox("賽況提示")
        insights_layout = QVBoxLayout()
        insights_layout.setContentsMargins(2, 2, 2, 2)
        self.insights_widget = RaceInsightsWidget()
        insights_layout.addWidget(self.insights_widget)
        insights_group.setLayout(insights_layout)
        right_panel.addWidget(insights_group)
        
        # 右欄垂直比例 (控制訊息:賽況提示)
        # 預設值基於實際測量: 控制訊息582px, 賽況提示581px
        right_panel.setSizes([582, 581])
        
        main_splitter.addWidget(right_panel)
        
        # 主分割器水平比例 (左:中:右)
        # 預設值基於 2560px 寬度螢幕優化
        main_splitter.setSizes([665, 1050, 813])
        main_splitter.setStretchFactor(0, 3)  # 左欄
        main_splitter.setStretchFactor(1, 5)  # 中欄
        main_splitter.setStretchFactor(2, 4)  # 右欄
        
        # 保存引用
        self.main_splitter = main_splitter
        self.left_splitter = left_panel  # 保持相容性
        self.right_panel = right_panel
        
        # === 輸出分割器寬度設定 ===
        print("=" * 60)
        print("[UI 佈局] 三欄式 Single Pane of Glass 設計:")
        print(f"  主分割器比例: 左欄:中欄:右欄 = 3:6:3")
        print(f"  左欄: 賽道地圖(上) + SHAP分析(下)")
        print(f"  中欄: 實時排名(上) + 輪胎策略圖(下)")
        print(f"  右欄: 控制訊息(上) + 賽況提示(下)")
        print("=" * 60)
        
        layout.addWidget(main_splitter, stretch=1)
        
        # 狀態列
        self.statusBar().showMessage("準備就緒 - 點擊「連接 Live Timing」開始接收即時數據")
    
    # === 模式切換相關方法 ===
    
    def _on_mode_changed(self, checked: bool):
        """模式切換"""
        if self.radio_realtime.isChecked():
            self._switch_to_realtime_mode()
        else:
            self._switch_to_historical_mode()
    
    def _switch_to_realtime_mode(self):
        """切換到即時模式"""
        self._mode = self.MODE_REALTIME
        
        # 顯示即時模式控制
        self.btn_connect.setVisible(True)
        self.btn_disconnect.setVisible(True)
        self.lbl_connection_status.setVisible(True)
        
        # 隱藏歷史模式選擇
        self.historical_widget.hide()
        
        # 隱藏時間軸控制器
        self.timeline_control.setVisible(False)
        
        # 更新狀態列
        self.statusBar().showMessage("即時模式 - 正在自動連接 Live Timing...")
        
        # 初始化即時數據源
        if self._realtime_source is None:
            self._realtime_source = RealTimeLiveF1DataSource(self)
            self._realtime_source.data_updated.connect(self._on_realtime_data_updated)
            self._realtime_source.connection_changed.connect(self._on_realtime_connection_changed)
        
        # 載入 Qatar 賽道輪廓
        self._load_qatar_track()
        
        # 自動啟動連接
        QTimer.singleShot(500, self._on_connect_clicked)
    
    def _switch_to_historical_mode(self):
        """切換到歷史回放模式"""
        self._mode = self.MODE_HISTORICAL
        
        # 停止即時連接
        if self._realtime_source is not None:
            self._realtime_source.stop_connection()
        
        # 停止即時更新定時器
        if self._realtime_update_timer is not None:
            self._realtime_update_timer.stop()
        
        # 隱藏即時模式控制
        self.btn_connect.setVisible(False)
        self.btn_disconnect.setVisible(False)
        self.lbl_connection_status.setVisible(False)
        
        # 顯示歷史模式選擇
        self.historical_widget.show()
        
        # 顯示時間軸控制器
        self.timeline_control.setVisible(True)
        
        # 更新狀態列
        self.statusBar().showMessage("歷史回放模式 - 請選擇賽事並點擊「載入賽事」")
        
        # 自動載入第一個賽事
        self._auto_select_first_race()
    
    def _load_qatar_track(self):
        """載入 Qatar 賽道輪廓"""
        try:
            # 嘗試載入 Qatar 賽道數據 - 優先使用 2025 (完整數據 304 點)，2024 只有 50 點
            track_data = self._load_fastf1_track_data("2025", "Qatar")
            if track_data:
                self.track_map.load_track_outline(track_data)
                self.circle_map.load_track_data(track_data)  # 圓形賽道圖也載入
                
                # 設置彎道資料
                official_corners = track_data.get('official_corners', {})
                if official_corners:
                    corners_list = official_corners.get('corners', [])
                    if corners_list:
                        self.track_map.set_official_corners(corners_list)
                
                print("[MAIN] Qatar 賽道輪廓載入成功")
            else:
                print("[MAIN] 無法載入 Qatar 賽道輪廓")
        except Exception as e:
            print(f"[MAIN] 載入 Qatar 賽道輪廓失敗: {e}")
    
    # === 即時模式相關方法 ===
    
    def _on_connect_clicked(self):
        """連接 Live Timing"""
        if not LIVEF1_AVAILABLE:
            QMessageBox.warning(
                self, 
                "缺少依賴", 
                "需要安裝 livef1 模組才能使用即時功能。\n\n"
                "請執行: pip install livef1"
            )
            return
        
        self.btn_connect.setEnabled(False)
        self.btn_disconnect.setEnabled(True)
        self.lbl_connection_status.setText("連接中...")
        self.lbl_connection_status.setStyleSheet("color: #FFAA00; font-weight: bold;")
        
        # 開始連接
        if self._realtime_source is not None:
            self._realtime_source.start_connection()
        
        # 啟動 UI 更新定時器
        if self._realtime_update_timer is None:
            self._realtime_update_timer = QTimer(self)
            self._realtime_update_timer.timeout.connect(self._update_realtime_display)
        
        self._realtime_update_timer.start(50)  # 每 50ms 更新一次 UI (約 20fps)
    
    def _on_disconnect_clicked(self):
        """斷開連接"""
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.lbl_connection_status.setText("連接已關閉")
        self.lbl_connection_status.setStyleSheet("color: #888888; font-weight: bold;")
        
        # 停止連接
        if self._realtime_source is not None:
            self._realtime_source.stop_connection()
        
        # 停止更新定時器
        if self._realtime_update_timer is not None:
            self._realtime_update_timer.stop()
    
    @pyqtSlot(str)
    def _on_realtime_connection_changed(self, status: str):
        """即時連接狀態變更"""
        self.lbl_connection_status.setText(status)
        
        if "成功" in status or "接收中" in status:
            self.lbl_connection_status.setStyleSheet("color: #00FF00; font-weight: bold;")
            self.statusBar().showMessage("即時數據接收中 - Qatar 2025")
        elif "錯誤" in status:
            self.lbl_connection_status.setStyleSheet("color: #FF0000; font-weight: bold;")
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
        else:
            self.lbl_connection_status.setStyleSheet("color: #FFAA00; font-weight: bold;")
    
    @pyqtSlot(str)
    def _on_realtime_data_updated(self, topic: str):
        """即時數據更新 (由信號觸發，不直接更新 UI)"""
        # 數據已在 RealTimeLiveF1DataSource 中更新
        # UI 更新由定時器控制
        pass
    
    def _update_realtime_display(self):
        """更新即時顯示 (由定時器觸發)"""
        if self._realtime_source is None or not self._realtime_source.is_connected():
            return
        
        # 獲取當前快照
        snapshot = self._realtime_source.get_current_snapshot()
        if not snapshot or not snapshot.get("drivers"):
            return
        
        # 獲取輪胎狀態
        tyre_state = self._realtime_source.get_tyre_state()
        
        # 獲取車輛遙測數據 (已包含在 snapshot 中)
        car_data = {}
        for driver_num, driver_data in snapshot.get("drivers", {}).items():
            car_data[driver_num] = {
                "speed": driver_data.get("speed"),
                "rpm": driver_data.get("rpm"),
                "gear": driver_data.get("gear"),
                "throttle": driver_data.get("throttle"),
                "brake": driver_data.get("brake"),
                "drs": driver_data.get("drs"),
            }
        
        # 更新排名表
        self.ranking_table.set_car_data(car_data)
        self.ranking_table.set_tyre_state(tyre_state)
        self.ranking_table.update_display(snapshot, tyre_state)
        
        # 更新賽事資訊
        lap_count = self._realtime_source.get_lap_count()
        current_lap = lap_count.get("CurrentLap", 0)
        total_laps = lap_count.get("TotalLaps", self._total_laps)
        self.race_info.update_lap(current_lap, total_laps)
        
        # 更新天氣
        weather = self._realtime_source.get_weather_data()
        if weather:
            self.race_info.update_weather(weather)
        
        # 更新賽道狀態
        track_status = self._realtime_source.get_track_status()
        self.race_info.update_track_status(track_status)
        
        # 更新 Pit Window 的賽道狀態
        pit_status = "GREEN"
        if track_status == "4":
            pit_status = "SC"
        elif track_status == "6":
            pit_status = "VSC"
        self.pit_window.set_track_status(pit_status)
        
        # 更新比賽控制訊息
        messages = self._realtime_source.get_race_control_messages()
        if messages:
            self.race_control_widget.set_messages(messages)
            self.race_control_widget.update_for_lap(current_lap)
        
        # 更新賽道地圖
        self.track_map.update_driver_positions(
            snapshot.get("drivers", {}),
            frame_index=0,
            total_frames=1,
            race_time_seconds=snapshot.get("race_time_seconds", 0)
        )
        
        # 更新圓形賽道圖
        race_time_str = snapshot.get("race_time", "00:00:00")
        self.circle_map.set_total_laps(total_laps)
        self.circle_map.update_positions(
            snapshot.get("drivers", {}),
            current_lap=current_lap,
            race_time=race_time_str
        )
        
        # 更新 Pit Window
        self.pit_window.update_positions(snapshot.get("drivers", {}))
        
        # 更新 Lap Time Distribution (圈速分佈)
        lap_time_data = {}
        for driver_num, driver_data in snapshot.get("drivers", {}).items():
            lap_time_data[driver_num] = {
                'driver_tla': driver_data.get('driver_tla', driver_num),
                'best_lap_time': driver_data.get('best_lap_time'),
                'last_lap_time': driver_data.get('last_lap_time'),
                'team_color': driver_data.get('team_color', '888888'),
                'compound': tyre_state.get(driver_num, {}).get('compound', 'UNKNOWN'),
            }
        self.lap_time_dist.update_data(lap_time_data)
        
        # 更新 PIT 統計 (簡化版)
        driver_laps = {}
        driver_positions = {}
        for driver_num, driver_data in snapshot.get("drivers", {}).items():
            driver_laps[driver_num] = driver_data.get("lap", 0) or 0
            pos = driver_data.get("position")
            if pos is not None:
                driver_positions[driver_num] = int(pos)
        
        # PIT 資訊已整合到 Super Table (ranking_table) 中
        # self.pit_table 已移除
    
    # === 歷史模式相關方法 ===
    
    def _auto_select_first_race(self):
        """自動選擇第一個可用的賽事 - 預設 2025 Qatar Race"""
        if not self._available_races:
            self.lbl_race_info.setText("未找到本地 LiveF1 數據，請先下載")
            self.lbl_race_info.setStyleSheet("color: #FF0000;")
            return
        
        # 預設選擇 2025 Qatar_Race (用於勝率預測測試)
        default_year = "2025"
        default_race = "Qatar_Race"
        
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
    
    def _print_all_widths(self):
        """Print 所有欄位和分割器的寬度"""
        print("\n" + "=" * 80)
        print("[Print 寬度] 所有 UI 元件寬度資訊")
        print("=" * 80)
        
        # === 1. 分割器寬度 ===
        print("\n[1] 分割器 (Splitter) 實際寬度:")
        if hasattr(self, 'main_splitter'):
            sizes = self.main_splitter.sizes()
            print(f"    main_splitter: {sizes}")
            for i, size in enumerate(sizes):
                print(f"      - 區域{i}: {size}px")
        
        if hasattr(self, 'left_splitter'):
            sizes = self.left_splitter.sizes()
            print(f"    left_splitter: {sizes}")
            for i, size in enumerate(sizes):
                print(f"      - 區域{i}: {size}px")
        
        # === 2. 排名表欄位寬度 ===
        print("\n[2] LiveRankingTableWidget 欄位寬度 (共23欄):")
        if hasattr(self, 'ranking_table') and hasattr(self.ranking_table, 'table'):
            table = self.ranking_table.table
            total = 0
            for col in range(table.columnCount()):
                w = table.columnWidth(col)
                total += w
                header = table.horizontalHeaderItem(col)
                header_text = header.text() if header else f"Col{col}"
                print(f"    [{col:2d}] {header_text:6s}: {w:4d}px")
            print(f"    --- 總寬度: {total}px ---")
        
        # === 3. PIT 表格已整合到 Super Table ===
        
        # === 4. SHAP 表格欄位寬度 ===
        print("\n[4] SHAPExplanationWidget 欄位寬度 (共2欄):")
        if hasattr(self, 'shap_widget') and hasattr(self.shap_widget, 'table'):
            table = self.shap_widget.table
            total = 0
            for col in range(table.columnCount()):
                w = table.columnWidth(col)
                total += w
                header = table.horizontalHeaderItem(col)
                header_text = header.text() if header else f"Col{col}"
                print(f"    [{col}] {header_text:8s}: {w:4d}px")
            print(f"    --- 總寬度: {total}px ---")
        
        # === 5. Widget 實際尺寸 ===
        print("\n[5] Widget 實際尺寸 (width x height):")
        widgets_to_check = [
            ('track_map', '賽道地圖'),
            ('circle_map', '圓形賽道圖'),
            ('lap_time_dist', '圈速分佈'),
            ('ranking_table', '實時排名'),
            ('pit_window', 'Pit Window'),
            ('tyre_strategy_chart', '輪胎策略圖'),
            ('shap_widget', 'SHAP分析'),
            ('race_control_widget', '比賽控制訊息'),
            ('insights_widget', '賽況提示'),
            ('race_info', '賽事資訊'),
            ('timeline_control', '時間軸控制'),
        ]
        for attr_name, display_name in widgets_to_check:
            if hasattr(self, attr_name):
                widget = getattr(self, attr_name)
                print(f"    {display_name:14s}: {widget.width():4d}x{widget.height():4d}px")
        
        # === 6. 比賽控制訊息欄位寬度 ===
        print("\n[6] RaceControlMessagesWidget 欄位寬度 (共3欄):")
        if hasattr(self, 'race_control_widget') and hasattr(self.race_control_widget, 'message_list'):
            table = self.race_control_widget.message_list
            total = 0
            for col in range(table.columnCount()):
                w = table.columnWidth(col)
                total += w
                header = table.horizontalHeaderItem(col)
                header_text = header.text() if header else f"Col{col}"
                print(f"    [{col}] {header_text:8s}: {w:4d}px")
            print(f"    --- 總寬度: {total}px ---")
        
        # === 7. 主視窗尺寸 ===
        print("\n[7] 主視窗尺寸:")
        print(f"    視窗大小: {self.width()}x{self.height()}px")
        print(f"    視窗位置: ({self.x()}, {self.y()})")
        
        print("\n" + "=" * 80)
        print("[Print 寬度] 完成")
        print("=" * 80 + "\n")
    
    def _toggle_race_control(self):
        """切換比賽控制訊息的顯示/隱藏"""
        if self.btn_toggle_race_control.isChecked():
            # 隱藏
            self.race_control_group.hide()
            self.btn_toggle_race_control.setText("顯示訊息")
            # 左側區塊佔滿
            # 三欄式佈局：調整中欄和右欄比例
            self.main_splitter.setSizes([400, 1600, 0])
        else:
            # 顯示
            self.race_control_group.show()
            self.btn_toggle_race_control.setText("隱藏訊息")
            # 恢復三欄式比例
            self.main_splitter.setSizes([400, 1200, 400])
    
    def _toggle_shap(self):
        """切換 SHAP 面板的顯示/隱藏"""
        if self.btn_toggle_shap.isChecked():
            # 隱藏 SHAP
            self.shap_group.hide()
            self.btn_toggle_shap.setText("顯示SHAP")
            # 左欄只剩地圖
            self.left_splitter.setSizes([600, 0])
        else:
            # 顯示 SHAP
            self.shap_group.show()
            self.btn_toggle_shap.setText("隱藏SHAP")
            # 恢復原始比例 (地圖:SHAP = 6:4)
            self.left_splitter.setSizes([360, 240])
    
    def _toggle_tyre_strategy(self):
        """切換輪胎策略圖的顯示/隱藏"""
        if self.btn_tyre_strategy.isChecked():
            # 隱藏輪胎策略圖
            self.tyre_strategy_group.hide()
            self.btn_tyre_strategy.setText("顯示輪胎")
            # 調整中欄比例 (排名:Pit Window:輪胎)
            self._adjust_center_splitter()
        else:
            # 顯示輪胎策略圖
            self.tyre_strategy_group.show()
            self.btn_tyre_strategy.setText("隱藏輪胎")
            # 調整中欄比例
            self._adjust_center_splitter()
            # 更新輪胎策略圖數據
            self._update_tyre_strategy_chart_for_current_time()
    
    def _toggle_pit_window(self):
        """切換 Pit Window 的顯示/隱藏"""
        if self.btn_pit_window.isChecked():
            # 隱藏 Pit Window
            self.pit_window_group.hide()
            self.btn_pit_window.setText("顯示Pit")
            # 調整中欄比例
            self._adjust_center_splitter()
        else:
            # 顯示 Pit Window
            self.pit_window_group.show()
            self.btn_pit_window.setText("隱藏Pit")
            # 調整中欄比例
            self._adjust_center_splitter()
    
    def _adjust_center_splitter(self):
        """調整中欄分割器的大小比例"""
        # 根據各元件的可見性調整
        ranking_visible = True  # 排名表始終顯示
        pit_visible = self.pit_window_group.isVisible()
        tyre_visible = self.tyre_strategy_group.isVisible()
        
        if pit_visible and tyre_visible:
            # 三者皆顯示 (排名:Pit:輪胎 = 50:15:35)
            self.center_splitter.setSizes([300, 120, 180])
        elif pit_visible and not tyre_visible:
            # 排名 + Pit
            self.center_splitter.setSizes([400, 150, 0])
        elif not pit_visible and tyre_visible:
            # 排名 + 輪胎
            self.center_splitter.setSizes([360, 0, 240])
        else:
            # 只有排名
            self.center_splitter.setSizes([600, 0, 0])
    
    def _update_tyre_strategy_chart_for_current_time(self):
        """使用當前時間點的數據更新輪胎策略圖 (內嵌版本)"""
        if not hasattr(self, 'tyre_strategy_chart'):
            return
        
        if not hasattr(self, 'processor') or self.processor is None:
            return
        
        if not hasattr(self, '_snapshots') or not self._snapshots:
            return
        
        # 獲取當前播放位置的快照
        current_index = self.timeline_control.get_current_index() if hasattr(self, 'timeline_control') else 0
        if current_index < 0 or current_index >= len(self._snapshots):
            return
        
        snapshot = self._snapshots[current_index]
        current_timestamp = snapshot.get('race_time', '')
        
        # 獲取當前時間點的輪胎狀態
        tyre_state = self.processor.get_tyre_state_at_time(current_timestamp)
        
        # 獲取車手排名和當前圈數
        driver_positions = {}
        current_lap = 0
        
        for driver_num, data in snapshot.get('drivers', {}).items():
            pos = data.get('position')
            if pos is not None:
                driver_positions[driver_num] = pos
            
            lap = data.get('lap', 0)
            if lap and lap > current_lap:
                current_lap = lap
        
        # 使用即時狀態更新內嵌的圖表
        self._update_embedded_tyre_chart(tyre_state, driver_positions, current_lap)
    
    def _update_embedded_tyre_chart(self, tyre_state: Dict, driver_positions: Dict, current_lap: int):
        """
        使用即時輪胎狀態更新內嵌的輪胎策略圖
        
        Args:
            tyre_state: 即時輪胎狀態 {driver_num: {compound, new, stint_count, stints, tyre_age}}
            driver_positions: 車手排名 {driver_num: position}
            current_lap: 當前圈數
        """
        if not hasattr(self, 'tyre_strategy_chart') or self.tyre_strategy_chart is None:
            return
        
        # 從 processor 獲取車手資訊
        driver_info = {}
        if hasattr(self, 'processor') and self.processor is not None:
            driver_info = self.processor._driver_info if hasattr(self.processor, '_driver_info') else {}
        
        # 從 tyre_state 構建動態 stint 數據
        driver_stints = {}
        
        for driver_num, state in tyre_state.items():
            stints_raw = state.get('stints', [])
            driver_stints[driver_num] = []
            current_start = 0
            
            for stint in stints_raw:
                compound = stint.get('compound', 'UNKNOWN')
                is_new = stint.get('new', False)
                total_laps = stint.get('total_laps', 0)
                
                end_lap = current_start + total_laps
                
                # 如果這個 stint 的起點已經超過當前圈數，跳過
                if current_start > current_lap:
                    break
                
                # 截斷到當前圈數
                display_end_lap = min(end_lap, current_lap)
                
                if display_end_lap > current_start:
                    driver_stints[driver_num].append({
                        'compound': compound,
                        'start_lap': current_start,
                        'end_lap': display_end_lap,
                        'new': is_new
                    })
                
                current_start = end_lap
        
        # 更新內嵌圖表
        total_laps = self._total_laps if hasattr(self, '_total_laps') else 53
        self.tyre_strategy_chart.set_data(
            driver_stints=driver_stints,
            driver_info=driver_info,
            driver_positions=driver_positions,
            total_laps=total_laps,
            current_lap=current_lap
        )
    
    def _update_tyre_strategy_chart_data(self):
        """更新輪胎策略圖的數據"""
        if self._tyre_strategy_dialog is None:
            return
        
        # 從 processor 獲取 stint 數據
        if not hasattr(self, 'processor') or self.processor is None:
            return
        
        driver_stints_raw = self.processor.get_driver_stints()
        driver_info = self.processor._driver_info if hasattr(self.processor, '_driver_info') else {}
        
        # 從當前快照獲取排名
        driver_positions = {}
        current_lap = 0
        
        if hasattr(self, '_snapshots') and self._snapshots:
            # 獲取當前播放位置的快照
            current_index = self.timeline_control.get_current_index() if hasattr(self, 'timeline_control') else 0
            if 0 <= current_index < len(self._snapshots):
                snapshot = self._snapshots[current_index]
                drivers_data = snapshot.get('drivers', {})
                
                for driver_num, data in drivers_data.items():
                    pos = data.get('position')
                    if pos is not None:
                        driver_positions[driver_num] = pos
                    
                    # 獲取當前圈數（取最大值）
                    lap = data.get('lap', 0)
                    if lap and lap > current_lap:
                        current_lap = lap
        
        # 轉換 stint 數據格式
        # 原始格式: {driver: [{stint_number, compound, new, total_laps, start_laps}, ...]}
        # 目標格式: {driver: [{compound, start_lap, end_lap, new}, ...]}
        driver_stints = {}
        
        for driver_num, stints in driver_stints_raw.items():
            driver_stints[driver_num] = []
            current_start = 0
            
            for stint in stints:
                compound = stint.get('compound', 'UNKNOWN')
                is_new = stint.get('new', False)
                total_laps = stint.get('total_laps', 0)
                
                end_lap = current_start + total_laps
                
                driver_stints[driver_num].append({
                    'compound': compound,
                    'start_lap': current_start,
                    'end_lap': end_lap,
                    'new': is_new
                })
                
                current_start = end_lap
        
        # 更新圖表
        total_laps = self._total_laps if hasattr(self, '_total_laps') else 53
        self._tyre_strategy_dialog.set_data(
            driver_stints=driver_stints,
            driver_info=driver_info,
            driver_positions=driver_positions,
            total_laps=total_laps,
            current_lap=current_lap
        )
    
    def _update_tyre_strategy_chart_with_state(self, tyre_state: Dict, driver_positions: Dict, current_lap: int):
        """
        使用即時輪胎狀態更新輪胎策略圖
        
        Args:
            tyre_state: 即時輪胎狀態 {driver_num: {compound, new, stint_count, stints, tyre_age}}
            driver_positions: 車手排名 {driver_num: position}
            current_lap: 當前圈數
        """
        if self._tyre_strategy_dialog is None:
            return
        
        # 從 processor 獲取車手資訊
        driver_info = {}
        if hasattr(self, 'processor') and self.processor is not None:
            driver_info = self.processor._driver_info if hasattr(self.processor, '_driver_info') else {}
        
        # 從 tyre_state 構建動態 stint 數據
        # tyre_state 格式: {driver_num: {compound, new, stint_count, stints: [{stint_number, compound, new, total_laps, start_laps}, ...]}}
        driver_stints = {}
        
        for driver_num, state in tyre_state.items():
            stints_raw = state.get('stints', [])
            driver_stints[driver_num] = []
            current_start = 0
            
            for stint in stints_raw:
                compound = stint.get('compound', 'UNKNOWN')
                is_new = stint.get('new', False)
                total_laps = stint.get('total_laps', 0)
                
                # 動態截斷：只顯示到當前圈數為止
                end_lap = current_start + total_laps
                
                # 如果這個 stint 的起點已經超過當前圈數，跳過
                if current_start > current_lap:
                    break
                
                # 截斷到當前圈數
                display_end_lap = min(end_lap, current_lap)
                
                if display_end_lap > current_start:
                    driver_stints[driver_num].append({
                        'compound': compound,
                        'start_lap': current_start,
                        'end_lap': display_end_lap,
                        'new': is_new
                    })
                
                current_start = end_lap
        
        # 更新圖表
        total_laps = self._total_laps if hasattr(self, '_total_laps') else 53
        self._tyre_strategy_dialog.set_data(
            driver_stints=driver_stints,
            driver_info=driver_info,
            driver_positions=driver_positions,
            total_laps=total_laps,
            current_lap=current_lap
        )

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
            # 步驟 0: 載入進站時間設定
            pit_config = PitLossConfigLoader.get_instance()
            green, sc, vsc = pit_config.get_pit_loss_times(race)
            self.pit_window.set_pit_loss(green=green, sc=sc, vsc=vsc)
            print(f"[MAIN] Pit loss times set: Green={green}s, SC={sc}s, VSC={vsc}s")
            
            # 步驟 1: 載入 FastF1 賽道輪廓數據 (如果有的話)
            track_data = self._load_fastf1_track_data(year, race)
            if track_data:
                self.track_map.load_track_outline(track_data)
                self.circle_map.load_track_data(track_data)  # 圓形賽道圖也載入
                
                # 設置彎道資料
                official_corners = track_data.get('official_corners', {})
                if official_corners:
                    corners_list = official_corners.get('corners', [])
                    if corners_list:
                        self.track_map.set_official_corners(corners_list)
                
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
                
                # PIT 資訊已整合到 Super Table，不再使用獨立的 pit_table
                # self.pit_table.set_driver_info(self.processor._driver_info)
                # self.pit_table.set_pit_data(pit_events, driver_stints)
                
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
        
        # 維修站時間 (PIT 資訊已整合到 Super Table)
        pit_lane_times = data_source.get_pit_lane_times()
        # self.pit_table.set_pit_lane_times(pit_lane_times)
        
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
                
                # 定義搜索優先級：當年 > 其他年份（2025 優先，因為完整數據較多）
                years_to_try = [year]
                for fallback_year in ["2025", "2024", "2023"]:
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
        
        # 更新賽道狀態 (根據當前時間點)
        if hasattr(self, 'processor') and hasattr(self.processor, 'get_track_status_at_time'):
            track_status = self.processor.get_track_status_at_time(current_timestamp)
            self.race_info.update_track_status(track_status)
        
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
                
                # === 更新 SHAP 解釋 (v3.4: 包含動態因子) ===
                try:
                    shap_explanations = {}
                    for driver_num, probs in predictions.items():
                        driver_tla = snapshot['drivers'].get(driver_num, {}).get('driver_tla', driver_num)
                        # 嘗試獲取 SHAP 解釋
                        explanation_str = self._predictor.explain_prediction(driver_tla, language="zh")
                        
                        # 解析基礎 SHAP 特徵
                        base_contributions = self._parse_shap_explanation(explanation_str) if explanation_str else []
                        
                        # v3.4: 添加動態因子到 SHAP 解釋
                        tyre_adv = probs.get('tyre_advantage', 1.0)
                        circuit_aff = probs.get('circuit_affinity', 1.0)
                        fp3q_comp = probs.get('fp3q_compensation', 1.0)
                        
                        # 將因子轉換為貢獻值 (1.0 = 0%, 1.10 = +10%)
                        dynamic_contributions = []
                        if abs(tyre_adv - 1.0) > 0.01:
                            dynamic_contributions.append(('tyre_advantage', (tyre_adv - 1.0)))
                        if abs(circuit_aff - 1.0) > 0.01:
                            dynamic_contributions.append(('circuit_affinity', (circuit_aff - 1.0)))
                        if abs(fp3q_comp - 1.0) > 0.01:
                            dynamic_contributions.append(('fp3q_compensation', (fp3q_comp - 1.0)))
                        
                        # 合併貢獻 (動態因子放前面)
                        all_contributions = dynamic_contributions + base_contributions
                        
                        # 構建 SHAP 解釋數據
                        shap_explanations[driver_num] = {
                            'win_probability': probs.get('win_prob', 0) * 100,
                            'base_value': 0.05,  # 預設基準值 5%
                            'feature_contributions': all_contributions,
                            # v3.4: 額外數據供 widget 顯示
                            'tyre_advantage': tyre_adv,
                            'circuit_affinity': circuit_aff,
                            'fp3q_compensation': fp3q_comp,
                        }
                    
                    # 構建 predictions 格式供 SHAP widget 使用
                    shap_predictions = {}
                    for driver_num, probs in predictions.items():
                        driver_info = snapshot['drivers'].get(driver_num, {})
                        shap_predictions[driver_num] = {
                            'win_probability': probs.get('win_prob', 0) * 100,
                            'p2_probability': probs.get('p2_prob', 0) * 100,
                            'p3_probability': probs.get('podium_prob', 0) * 100,
                            'driver_tla': driver_info.get('driver_tla', driver_num)
                        }
                    
                    # 更新 SHAP widget
                    if hasattr(self, 'shap_widget'):
                        self.shap_widget.update_explanations(shap_explanations, shap_predictions)
                    
                    # 更新賽況提示 widget
                    if hasattr(self, 'insights_widget'):
                        total_laps = getattr(self, '_total_laps', 60)
                        self.insights_widget.update_insights(
                            drivers=snapshot['drivers'],
                            tyre_state=tyre_state,
                            current_lap=current_lap,
                            total_laps=total_laps,
                            predictions=predictions
                        )
                        
                except Exception as shap_e:
                    print(f"[WARNING] SHAP explanation update failed: {shap_e}")
                
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
        
        # 更新內嵌輪胎策略圖 (如果顯示中)
        if hasattr(self, 'tyre_strategy_group') and self.tyre_strategy_group.isVisible():
            self._update_embedded_tyre_chart(tyre_state, driver_positions, current_lap)
        
        # PIT 統計已整合到 Super Table (ranking_table) 中

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
        
        # 更新圓形賽道圖
        race_time_str = snapshot.get('race_time', '00:00:00')
        self.circle_map.set_total_laps(self._total_laps)
        self.circle_map.update_positions(
            snapshot['drivers'],
            current_lap=current_lap,
            race_time=race_time_str
        )
        
        # 更新 Pit Window
        self.pit_window.update_positions(snapshot['drivers'])
        
        # 更新 Lap Time Distribution (圈速分佈)
        lap_time_data = {}
        for driver_num, driver_data in snapshot.get('drivers', {}).items():
            lap_time_data[driver_num] = {
                'driver_tla': driver_data.get('driver_tla', driver_num),
                'best_lap_time': driver_data.get('best_lap_time'),
                'last_lap_time': driver_data.get('last_lap_time'),
                'team_color': driver_data.get('team_color', '888888'),
                'compound': tyre_state.get(driver_num, {}).get('compound', 'UNKNOWN'),
            }
        self.lap_time_dist.update_data(lap_time_data)
    
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
    
    def _parse_shap_explanation(self, explanation_str: str) -> List[Tuple[str, float]]:
        """
        解析 SHAP 解釋字串，提取特徵貢獻
        
        Args:
            explanation_str: 格式化的解釋字串
            
        Returns:
            [(feature_name, contribution), ...]
        """
        if not explanation_str:
            return []
        
        contributions = []
        
        # 解析格式: "  目前位置: +25.0%"
        import re
        pattern = r'^\s+(.+?):\s*([+-]?\d+\.?\d*)%?$'
        
        for line in explanation_str.split('\n'):
            match = re.match(pattern, line)
            if match:
                feature_name = match.group(1).strip()
                value_str = match.group(2).strip()
                try:
                    # 轉換百分比為小數
                    contribution = float(value_str) / 100.0
                    
                    # 反向映射中文名稱到英文鍵名
                    reverse_labels = {v: k for k, v in SHAPExplanationWidget.FEATURE_LABELS.items()}
                    feature_key = reverse_labels.get(feature_name, feature_name)
                    
                    contributions.append((feature_key, contribution))
                except ValueError:
                    pass
        
        return contributions
    
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
    
    def closeEvent(self, event):
        """視窗關閉事件"""
        # 停止即時連接
        if self._realtime_source is not None:
            self._realtime_source.stop_connection()
        
        # 停止更新定時器
        if self._realtime_update_timer is not None:
            self._realtime_update_timer.stop()
        
        event.accept()


# ========== 主程式 ==========

def main():
    print("="*70)
    print("F1 即時車手位置追蹤系統 - Real-Time Live Timing")
    print("="*70)
    print("Qatar 2025 Grand Prix - 即時數據追蹤")
    print("="*70)
    
    # 檢查依賴
    if not WEBSOCKETS_AVAILABLE:
        print("[WARNING] websockets 未安裝，即時功能不可用")
        print("[WARNING] 請執行: pip install websockets")
    
    app = QApplication(sys.argv)
    window = LivePositionTrackingMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
