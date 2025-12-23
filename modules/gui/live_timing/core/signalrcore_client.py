# -*- coding: utf-8 -*-
"""
F1 SignalRCore Client - 即時 Live Timing 連接 (ASP.NET Core SignalR)
====================================================================

使用新的 ASP.NET Core SignalR 協議連接 F1 官方 Live Timing 服務。
參考 undercut-f1 (JustAman62/undercut-f1) 的實現。

新端點: wss://livetiming.formula1.com/signalrcore
協議: ASP.NET Core SignalR (JSON Hub Protocol)

數據格式:
- CarData.z: base64 + zlib 壓縮，包含 Channels (0=RPM, 2=Speed, 3=Gear, 4=Throttle, 5=Brake, 45=DRS)
- Position.z: base64 + zlib 壓縮，包含車輛 X, Y, Z 座標
- TimingData: JSON 格式，包含位置、差距、圈速等

需要 F1TV 訂閱才能獲取的數據 (2025 Dutch GP 之後):
- CarData.z / Position.z (車輛位置)
- ChampionshipPrediction (冠軍預測)
- PitLaneTimeCollection (進站時間)

Author: F1T Team
Date: 2025-12-20
"""

import json
import base64
import zlib
import asyncio
import threading
from typing import Dict, List, Any, Optional, Callable
from queue import Queue, Empty
from datetime import datetime
import urllib.parse

from PyQt5.QtCore import QThread, pyqtSignal

from core.logger import get_logger

logger = get_logger("live_timing.signalrcore_client", component="gui")

# 檢查 websockets 是否可用
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets not available. Install with: pip install websockets")


class F1SignalRCoreClient:
    """
    F1 官方 SignalRCore 客戶端 (ASP.NET Core SignalR)
    
    使用新的 SignalRCore 端點連接 F1 Live Timing 服務
    支持 F1TV 認證以獲取完整數據
    """
    
    # 新端點 (ASP.NET Core SignalR)
    SIGNALR_URL = "wss://livetiming.formula1.com/signalrcore"
    
    # CarData.z Channels 定義
    CAR_DATA_CHANNELS = {
        "0": "rpm",
        "2": "speed", 
        "3": "n_gear",
        "4": "throttle",
        "5": "brake",
        "45": "drs"
    }
    
    # 訂閱的數據流 (參考 undercut-f1)
    DEFAULT_TOPICS = [
        "Heartbeat",
        "ExtrapolatedClock",
        "TimingStats",
        "TimingAppData",
        "WeatherData",
        "TrackStatus",
        "DriverList",
        "RaceControlMessages",
        "SessionInfo",
        "SessionData",
        "LapCount",
        "TimingData",
        "TeamRadio",
        # 以下需要 F1TV 訂閱
        "CarData.z",
        "Position.z",
        "ChampionshipPrediction",
        "PitLaneTimeCollection",
        # 賽後可用
        "PitStopSeries",
    ]
    
    def __init__(
        self, 
        topics: Optional[List[str]] = None,
        access_token: Optional[str] = None,
        on_data_callback: Optional[Callable[[str, Any], None]] = None, 
        on_status_callback: Optional[Callable[[str], None]] = None, 
        on_error_callback: Optional[Callable[[str], None]] = None
    ):
        """
        初始化 SignalRCore 客戶端
        
        Args:
            topics: 訂閱的數據主題列表
            access_token: F1TV subscriptionToken (用於獲取完整數據)
            on_data_callback: 數據回調函數 (topic, data)
            on_status_callback: 狀態回調函數 (status_message)
            on_error_callback: 錯誤回調函數 (error_message)
        """
        self.topics = topics or self.DEFAULT_TOPICS
        self._access_token = access_token
        self._on_data = on_data_callback
        self._on_status = on_status_callback
        self._on_error = on_error_callback
        
        self._running = False
        self._ws = None
        self._invocation_id = 0
        
        # 統計
        self._topic_counts: Dict[str, int] = {}
        self._last_log_time = 0
        
    def set_access_token(self, token: Optional[str]):
        """設置 F1TV access token"""
        self._access_token = token
        if token:
            logger.info("Access token set (length: %d)", len(token))
        else:
            logger.info("Access token cleared")
        
    def _emit_status(self, msg: str):
        """發送狀態訊息"""
        logger.info("[SignalRCore] %s", msg)
        if self._on_status:
            self._on_status(msg)
            
    def _emit_error(self, msg: str):
        """發送錯誤訊息"""
        logger.error("[SignalRCore] %s", msg)
        if self._on_error:
            self._on_error(msg)
            
    def _emit_data(self, topic: str, data: Any):
        """發送數據"""
        if self._on_data:
            self._on_data(topic, data)
    
    def _build_ws_url(self) -> str:
        """構建 WebSocket 連接 URL"""
        url = self.SIGNALR_URL
        
        # 如果有 access token，添加到 URL (作為查詢參數)
        if self._access_token:
            url = f"{url}?access_token={urllib.parse.quote(self._access_token)}"
        
        return url
    
    def _decode_compressed_data(self, data: str) -> dict:
        """
        解碼 base64 + zlib 壓縮的數據
        
        Args:
            data: base64 編碼的壓縮字串
            
        Returns:
            解碼後的 JSON 數據
        """
        try:
            if data.startswith('{'):
                return json.loads(data)
            if data.startswith('"'):
                data = data.strip('"')
            
            decoded = base64.b64decode(data)
            decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
            return json.loads(decompressed.decode("utf-8-sig"))
        except Exception as e:
            logger.debug("Decompress failed: %s", e)
            return {}
    
    def _parse_car_data(self, raw_data: dict) -> List[Dict]:
        """解析 CarData.z 數據"""
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
                
                for channel_id, field_name in self.CAR_DATA_CHANNELS.items():
                    if channel_id in channels:
                        record[field_name] = channels[channel_id]
                    elif int(channel_id) in channels:
                        record[field_name] = channels[int(channel_id)]
                
                results.append(record)
        
        return results
    
    def _parse_position_data(self, raw_data: dict) -> List[Dict]:
        """解析 Position.z 數據"""
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
        """解析 TimingData 數據"""
        results = []
        
        if "Lines" in raw_data:
            lines = raw_data["Lines"]
        else:
            lines = raw_data
        
        for driver_no, timing in lines.items():
            if not isinstance(timing, dict):
                continue
                
            record = {"DriverNo": driver_no}
            
            for key, value in timing.items():
                if isinstance(value, dict):
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
    
    async def _send_handshake(self, ws):
        """發送 SignalR 握手訊息"""
        # ASP.NET Core SignalR 使用 JSON Hub Protocol
        # 握手格式: {"protocol":"json","version":1}\x1e
        handshake = json.dumps({"protocol": "json", "version": 1}) + "\x1e"
        await ws.send(handshake)
        self._emit_status("Sent handshake")
    
    async def _subscribe(self, ws):
        """發送訂閱請求"""
        self._invocation_id += 1
        
        # ASP.NET Core SignalR 調用格式
        # {"type":1,"invocationId":"1","target":"Subscribe","arguments":[["topic1","topic2"]]}
        subscribe_msg = {
            "type": 1,  # Invocation
            "invocationId": str(self._invocation_id),
            "target": "Subscribe",
            "arguments": [self.topics]
        }
        
        msg = json.dumps(subscribe_msg) + "\x1e"
        await ws.send(msg)
        self._emit_status(f"Subscribed to {len(self.topics)} topics")
    
    async def _process_message(self, raw_message: str):
        """
        處理 SignalR 消息
        
        ASP.NET Core SignalR 消息格式:
        - 類型 1: Invocation (方法調用)
        - 類型 2: StreamItem
        - 類型 3: Completion (調用完成)
        - 類型 6: Ping
        """
        import time
        current_time = time.time()
        
        # 消息以 \x1e 分隔
        messages = raw_message.split("\x1e")
        
        for msg_str in messages:
            if not msg_str.strip():
                continue
            
            try:
                msg = json.loads(msg_str)
            except json.JSONDecodeError:
                continue
            
            msg_type = msg.get("type")
            
            # Ping
            if msg_type == 6:
                continue
            
            # Completion (訂閱回應)
            if msg_type == 3:
                result = msg.get("result")
                if result and isinstance(result, dict):
                    self._emit_status("Processing subscription response...")
                    await self._process_subscription_response(result)
                continue
            
            # Invocation (數據推送)
            if msg_type == 1:
                target = msg.get("target", "")
                arguments = msg.get("arguments", [])
                
                if target == "feed" and len(arguments) >= 2:
                    topic = arguments[0]
                    data = arguments[1]
                    # 第三個參數是 timestamp (如果有)
                    timestamp = arguments[2] if len(arguments) > 2 else None
                    
                    # 統計
                    self._topic_counts[topic] = self._topic_counts.get(topic, 0) + 1
                    
                    # 每 30 秒輸出統計
                    if current_time - self._last_log_time > 30:
                        self._last_log_time = current_time
                        logger.debug("Topic stats: %s", self._topic_counts)
                    
                    await self._process_topic_data(topic, data)
    
    async def _process_subscription_response(self, result: dict):
        """處理訂閱回應中的初始數據"""
        for topic, data in result.items():
            if topic.startswith("_"):
                continue
            
            try:
                await self._process_topic_data(topic, data, is_initial=True)
            except Exception as e:
                logger.error("Error processing initial %s: %s", topic, e)
    
    async def _process_topic_data(self, topic: str, data: Any, is_initial: bool = False):
        """處理單個 topic 的數據"""
        try:
            if topic in ["CarData.z", "CarData"]:
                if isinstance(data, str):
                    raw = self._decode_compressed_data(data)
                    parsed = self._parse_car_data(raw)
                    if parsed:
                        self._emit_data("CarData.z", parsed)
                        
            elif topic in ["Position.z", "Position"]:
                if isinstance(data, str):
                    raw = self._decode_compressed_data(data)
                    parsed = self._parse_position_data(raw)
                    if parsed:
                        self._emit_data("Position.z", parsed)
                        
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
                          "SessionInfo", "LapCount", "SessionStatus", "SessionData",
                          "ExtrapolatedClock", "Heartbeat"]:
                if isinstance(data, dict):
                    self._emit_data(topic, [data])
                elif isinstance(data, list):
                    self._emit_data(topic, data)
                    
            elif topic == "TimingAppData":
                # TimingAppData 包含輪胎資訊
                if isinstance(data, dict):
                    self._emit_data(topic, [data])
                    
            elif topic == "TeamRadio":
                if isinstance(data, dict):
                    self._emit_data(topic, [data])
                    
            elif topic == "ChampionshipPrediction":
                if isinstance(data, dict):
                    self._emit_data(topic, [data])
                    
            elif topic == "PitLaneTimeCollection":
                if isinstance(data, dict):
                    self._emit_data(topic, [data])
                    
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
                # 其他 topic 直接傳遞
                if isinstance(data, dict):
                    self._emit_data(topic, [data])
                elif isinstance(data, list):
                    self._emit_data(topic, data)
                    
        except Exception as e:
            logger.error("Parse %s error: %s", topic, e)
    
    async def _connect_and_run(self):
        """連接 WebSocket 並開始接收數據"""
        if not WEBSOCKETS_AVAILABLE:
            self._emit_error("websockets package not installed")
            return
        
        ws_url = self._build_ws_url()
        
        # 構建 headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        # 如果有 access token，也添加到 header
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        
        self._emit_status("Connecting to SignalRCore...")
        
        try:
            async with websockets.connect(
                ws_url, 
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=20
            ) as ws:
                self._ws = ws
                self._emit_status("WebSocket connected")
                
                # 發送握手
                await self._send_handshake(ws)
                
                # 等待握手回應
                handshake_response = await ws.recv()
                if "{}" in handshake_response:
                    self._emit_status("Handshake successful")
                else:
                    self._emit_error(f"Handshake failed: {handshake_response}")
                    return
                
                # 發送訂閱
                await self._subscribe(ws)
                
                # 接收消息循環
                while self._running:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30)
                        if msg:
                            await self._process_message(msg)
                            
                    except asyncio.TimeoutError:
                        # 發送 ping
                        ping_msg = json.dumps({"type": 6}) + "\x1e"
                        await ws.send(ping_msg)
                        
                    except websockets.exceptions.ConnectionClosed as e:
                        self._emit_status(f"Connection closed: {e}")
                        break
                        
                    except Exception as e:
                        logger.error("Receive error: %s", e)
                        
        except Exception as e:
            self._emit_error(f"Connection failed: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """開始運行客戶端 (阻塞)"""
        self._running = True
        
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


class RealTimeLiveF1CoreWorker(QThread):
    """
    即時 Live F1 數據擷取 Worker 執行緒 (SignalRCore)
    
    使用新的 ASP.NET Core SignalR 端點連接 Live Timing 服務
    支持 F1TV 認證獲取完整數據
    """
    
    # 信號
    data_received = pyqtSignal(str, object)  # (topic, data_list)
    connection_status = pyqtSignal(str)       # 連接狀態
    error_occurred = pyqtSignal(str)          # 錯誤訊息
    
    def __init__(
        self, 
        topics: Optional[List[str]] = None, 
        access_token: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.topics = topics or F1SignalRCoreClient.DEFAULT_TOPICS
        self._access_token = access_token
        self._running = False
        self._client: Optional[F1SignalRCoreClient] = None
        self._data_queue: Queue = Queue()
        
    def set_access_token(self, token: Optional[str]):
        """設置 F1TV access token"""
        self._access_token = token
        if self._client:
            self._client.set_access_token(token)
        
    def run(self):
        """執行緒主迴圈"""
        self._running = True
        
        if not WEBSOCKETS_AVAILABLE:
            self.error_occurred.emit("websockets package not installed")
            return
        
        self.connection_status.emit("Initializing SignalRCore connection...")
        logger.info("Starting SignalRCore client...")
        
        if self._access_token:
            logger.info("Using F1TV access token for authentication")
        else:
            logger.warning("No F1TV access token - some data may be unavailable")
        
        def on_data(topic, data_list):
            self._data_queue.put((topic, data_list))
        
        def on_status(msg):
            self.connection_status.emit(msg)
        
        def on_error(msg):
            self.error_occurred.emit(msg)
        
        try:
            self._client = F1SignalRCoreClient(
                topics=self.topics,
                access_token=self._access_token,
                on_data_callback=on_data,
                on_status_callback=on_status,
                on_error_callback=on_error
            )
            
            # 啟動隊列處理
            def process_queue():
                while self._running:
                    try:
                        topic, data_list = self._data_queue.get(timeout=0.1)
                        self.data_received.emit(topic, data_list)
                    except Empty:
                        continue
                    except Exception as e:
                        logger.error("Queue processing error: %s", e)
            
            queue_thread = threading.Thread(target=process_queue, daemon=True)
            queue_thread.start()
            
            self._client.run()
            
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {str(e)}")
            logger.error("Connection error: %s", e)
        finally:
            self._running = False
            self.connection_status.emit("Connection closed")
    
    def stop(self):
        """停止執行緒"""
        self._running = False
        if self._client:
            self._client.stop()
        self.wait(3000)


# 導出
__all__ = ['F1SignalRCoreClient', 'RealTimeLiveF1CoreWorker', 'WEBSOCKETS_AVAILABLE']
