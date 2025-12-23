# -*- coding: utf-8 -*-
"""
SignalR Recorder Core

負責連接 F1 SignalR 端點並錄製原始訊號。
"""

import asyncio
import json
import base64
import zlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt5.QtCore import QObject, pyqtSignal, QThread


class SignalRRecorderWorker(QThread):
    """SignalR 錄製工作執行緒"""
    
    message_received = pyqtSignal(str, dict, str)  # topic, parsed_data, raw
    connection_status = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    recording_stopped = pyqtSignal(str)  # filepath
    
    # SignalR 端點
    SIGNALR_URL = "wss://livetiming.formula1.com/signalrcore"
    
    # 訂閱的數據流
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
        "TimingDataF1",
        "TeamRadio",
        "CarData.z",
        "Position.z",
        "ChampionshipPrediction",
        "PitLaneTimeCollection",
        "PitStopSeries",
        "TyreStintSeries",
        "CurrentTyres",
        "TopThree",
    ]
    
    # CarData.z 頻道定義
    CAR_DATA_CHANNELS = {
        "0": "rpm",
        "2": "speed",
        "3": "n_gear",
        "4": "throttle",
        "5": "brake",
        "45": "drs"
    }
    
    def __init__(self, output_dir: Path, access_token: Optional[str] = None):
        super().__init__()
        self.output_dir = output_dir
        self.access_token = access_token
        self._running = False
        self._file_handle = None
        self._filepath: Optional[Path] = None
        self._seq = 0
        self._start_time: Optional[datetime] = None
        
    def run(self):
        """執行錄製"""
        self._running = True
        self._start_time = datetime.now()
        
        # 建立輸出檔案
        timestamp = self._start_time.strftime("%Y%m%d_%H%M%S")
        self._filepath = self.output_dir / f"signalr_{timestamp}.jsonl"
        
        try:
            self._file_handle = open(self._filepath, 'w', encoding='utf-8')
            self.connection_status.emit("Connecting...")
            
            # 執行 asyncio 事件迴圈
            asyncio.run(self._connect_and_record())
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._save_metadata()
            if self._file_handle:
                self._file_handle.close()
            self.recording_stopped.emit(str(self._filepath) if self._filepath else "")
            
    async def _connect_and_record(self):
        """連接並錄製"""
        try:
            import websockets
        except ImportError:
            self.error_occurred.emit("websockets not installed. Run: pip install websockets")
            return
            
        url = self.SIGNALR_URL
        
        # 添加 token 到 URL
        if self.access_token:
            url += f"?token={self.access_token}"
            
        try:
            async with websockets.connect(
                url,
                extra_headers={
                    "User-Agent": "BestHTTP/2 v2.8.5",
                    "Accept-Encoding": "gzip, identity",
                },
                ping_interval=25,
                ping_timeout=10,
            ) as ws:
                self.connection_status.emit("Connected, sending handshake...")
                
                # 發送握手
                await ws.send('{"protocol":"json","version":1}\x1e')
                
                # 等待握手回應
                response = await ws.recv()
                self.connection_status.emit("Handshake complete, subscribing...")
                
                # 訂閱所有 topics
                await self._subscribe_topics(ws)
                
                self.connection_status.emit(f"Recording... ({len(self.DEFAULT_TOPICS)} topics)")
                
                # 持續接收訊息
                while self._running:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        self._process_message(message)
                    except asyncio.TimeoutError:
                        continue
                    except websockets.ConnectionClosed:
                        self.connection_status.emit("Connection closed by server")
                        break
                        
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {e}")
            
    async def _subscribe_topics(self, ws):
        """訂閱所有 topics"""
        for topic in self.DEFAULT_TOPICS:
            msg = {
                "type": 1,
                "invocationId": str(self._get_next_id()),
                "target": "Subscribe",
                "arguments": [[topic]]
            }
            await ws.send(json.dumps(msg) + '\x1e')
            
    def _get_next_id(self) -> int:
        """獲取下一個 invocation ID"""
        self._seq += 1
        return self._seq
        
    def _process_message(self, raw_message: str):
        """處理收到的訊息"""
        # SignalR 訊息以 \x1e 分隔
        for msg in raw_message.split('\x1e'):
            if not msg.strip():
                continue
                
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                continue
                
            # 記錄原始訊息
            self._write_record(msg)
            
            # 解析並發送信號
            if data.get("type") == 1 and "arguments" in data:
                args = data.get("arguments", [])
                if len(args) >= 2:
                    topic = args[0]
                    payload = args[1]
                    
                    # 解壓縮 .z 數據
                    parsed = self._parse_payload(topic, payload)
                    
                    self.message_received.emit(topic, parsed, msg[:500])
                    
    def _parse_payload(self, topic: str, payload: Any) -> Dict[str, Any]:
        """解析訊息 payload"""
        if topic.endswith('.z') and isinstance(payload, str):
            # base64 + zlib 壓縮的數據
            try:
                decoded = base64.b64decode(payload)
                decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
                return json.loads(decompressed.decode('utf-8'))
            except Exception as e:
                return {"error": str(e), "raw": payload[:100]}
        elif isinstance(payload, dict):
            return payload
        else:
            return {"data": payload}
            
    def _write_record(self, raw_message: str):
        """寫入錄製記錄"""
        if self._file_handle:
            record = {
                "seq": self._seq,
                "ts": datetime.now().isoformat(),
                "raw": raw_message
            }
            self._file_handle.write(json.dumps(record, ensure_ascii=False) + '\n')
            self._file_handle.flush()
            
    def _save_metadata(self):
        """儲存 metadata"""
        if not self._filepath:
            return
            
        meta_path = self._filepath.with_suffix('.meta.json')
        end_time = datetime.now()
        
        metadata = {
            "format": "jsonl",
            "version": "2.0",
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - self._start_time).total_seconds() if self._start_time else 0,
            "total_messages": self._seq,
            "signalr": {
                "url": self.SIGNALR_URL,
                "protocol": "ASP.NET Core SignalR",
                "topics": self.DEFAULT_TOPICS,
                "has_token": bool(self.access_token)
            },
            "files": {
                "data": self._filepath.name,
                "metadata": meta_path.name
            }
        }
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
    def stop(self):
        """停止錄製"""
        self._running = False


class SignalRRecorder(QObject):
    """SignalR 錄製器"""
    
    message_received = pyqtSignal(str, dict, str)  # topic, data, raw
    connection_status = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    recording_stopped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._worker: Optional[SignalRRecorderWorker] = None
        self._output_dir = Path.home() / ".f1t" / "signalr_recordings"
        self._access_token: Optional[str] = None
        
    def set_output_dir(self, path: Path):
        """設置輸出目錄"""
        self._output_dir = path
        self._output_dir.mkdir(parents=True, exist_ok=True)
        
    def set_access_token(self, token: Optional[str]):
        """設置 F1TV access token"""
        self._access_token = token
        
    def start_recording(self):
        """開始錄製"""
        if self._worker and self._worker.isRunning():
            return
            
        self._output_dir.mkdir(parents=True, exist_ok=True)
        
        self._worker = SignalRRecorderWorker(self._output_dir, self._access_token)
        self._worker.message_received.connect(self.message_received)
        self._worker.connection_status.connect(self.connection_status)
        self._worker.error_occurred.connect(self.error_occurred)
        self._worker.recording_stopped.connect(self.recording_stopped)
        self._worker.start()
        
    def stop_recording(self):
        """停止錄製"""
        if self._worker:
            self._worker.stop()
            
    def is_recording(self) -> bool:
        """是否正在錄製"""
        return self._worker is not None and self._worker.isRunning()
