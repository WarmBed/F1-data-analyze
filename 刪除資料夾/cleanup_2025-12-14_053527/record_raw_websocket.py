"""
F1 Live Timing 純原始數據錄製工具
==================================

完全不做任何處理，直接保存 WebSocket 收到的原始字串。
使用 JSONL 格式（每行一條訊息），方便後續逐行解析。

輸出格式 (.jsonl):
{"seq":1,"ts":"2025-12-07T21:15:30.123456","raw":"{原始WebSocket訊息}"}
{"seq":2,"ts":"2025-12-07T21:15:30.234567","raw":"{原始WebSocket訊息}"}
...

另外保存一個 metadata 檔案 (.meta.json)

用法:
    python record_raw_websocket.py --duration 60
    python record_raw_websocket.py --duration 3600 --output race_recording

Author: F1T Team
Date: 2025-12-07
"""

import sys
import os
import json
import time
import asyncio
import argparse
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("[ERROR] websockets not installed! Run: pip install websockets")
    sys.exit(1)


class PureRawRecorder:
    """純原始 WebSocket 錄製器"""
    
    SIGNALR_URL = "https://livetiming.formula1.com/signalr"
    HUB_NAME = "Streaming"
    PROTOCOL_VERSION = "1.5"
    
    # 所有 topics
    ALL_TOPICS = [
        "CarData.z", "Position.z",
        "TimingData", "TimingDataF1", "TimingAppData", "TimingStats",
        "DriverList", "SessionInfo", "SessionStatus", "SessionData",
        "TrackStatus", "WeatherData", "WeatherDataSeries",
        "RaceControlMessages", "LapCount", "LapSeries",
        "CurrentTyres", "TyreStintSeries",
        "PitStopSeries", "PitLaneTimeCollection",
        "TopThree", "Heartbeat", "ExtrapolatedClock", "TeamRadio",
        "ContentStreams", "AudioStreams", "ArchiveStatus",
        "ChampionshipPrediction", "DriverRaceInfo",
    ]
    
    def __init__(self, output_name: Optional[str] = None):
        self.output_dir = Path("data/live_timing_recordings")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = output_name or f"raw_{timestamp}"
        
        # 主要輸出：JSONL 格式（每行一條原始訊息）
        self.jsonl_path = self.output_dir / f"{base_name}.jsonl"
        # Metadata 檔案
        self.meta_path = self.output_dir / f"{base_name}.meta.json"
        
        self.seq = 0
        self.file_handle = None
        
        self._running = False
        self._session = None
        self._connection_token = None
        self._cookie = None
        
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{ts}] {msg}")
    
    def _negotiate(self) -> bool:
        self._log("Negotiating...")
        try:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "BestHTTP",
                "Accept-Encoding": "gzip, identity",
            })
            
            conn_data = json.dumps([{"name": self.HUB_NAME}])
            response = self._session.get(
                f"{self.SIGNALR_URL}/negotiate",
                params={"connectionData": conn_data, "clientProtocol": self.PROTOCOL_VERSION},
                timeout=10
            )
            
            if response.status_code != 200:
                self._log(f"Negotiate failed: {response.status_code}")
                return False
            
            data = response.json()
            self._connection_token = data.get("ConnectionToken")
            self._cookie = "; ".join([f"{k}={v}" for k, v in response.cookies.items()])
            
            self._log(f"Negotiate OK, Protocol: {data.get('ProtocolVersion')}")
            return True
        except Exception as e:
            self._log(f"Negotiate error: {e}")
            return False
    
    def _build_ws_url(self) -> str:
        conn_data = json.dumps([{"name": self.HUB_NAME}])
        params = {
            "transport": "webSockets",
            "connectionToken": self._connection_token,
            "connectionData": conn_data,
            "clientProtocol": self.PROTOCOL_VERSION
        }
        return f"wss://livetiming.formula1.com/signalr/connect?{urllib.parse.urlencode(params)}"
    
    def _write_raw(self, raw_msg: str):
        """直接寫入原始訊息（JSONL 格式）"""
        self.seq += 1
        ts = datetime.now().isoformat()
        
        # 構建 JSONL 行（最小化處理）
        # raw_msg 本身就是 JSON 字串，我們需要 escape 它
        line = json.dumps({
            "seq": self.seq,
            "ts": ts,
            "raw": raw_msg
        }, ensure_ascii=False)
        
        self.file_handle.write(line + "\n")
        self.file_handle.flush()  # 即時寫入，防止資料遺失
        
        if self.seq % 100 == 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self._log(f"Recorded {self.seq} messages ({self.seq/elapsed:.1f}/s)")
    
    async def _connect_and_record(self, duration: int):
        ws_url = self._build_ws_url()
        headers = {"User-Agent": "BestHTTP"}
        if self._cookie:
            headers["Cookie"] = self._cookie
        
        self._log("Connecting WebSocket...")
        
        try:
            async with websockets.connect(ws_url, extra_headers=headers) as ws:
                self._log("Connected")
                
                # 訂閱
                sub_msg = json.dumps({
                    "H": self.HUB_NAME,
                    "M": "Subscribe", 
                    "A": [self.ALL_TOPICS],
                    "I": 0
                })
                await ws.send(sub_msg)
                self._log(f"Subscribed to {len(self.ALL_TOPICS)} topics")
                
                # 開始錄製
                self.start_time = datetime.now()
                end_ts = self.start_time.timestamp() + duration
                
                self._log(f"Recording for {duration}s... (Ctrl+C to stop)")
                print("-" * 50)
                
                while self._running and time.time() < end_ts:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        if raw:
                            self._write_raw(raw)
                    except asyncio.TimeoutError:
                        await ws.ping()
                    except websockets.exceptions.ConnectionClosed:
                        self._log("Connection closed")
                        break
                        
        except Exception as e:
            self._log(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_metadata(self):
        """保存 metadata"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        
        meta = {
            "format": "jsonl",
            "version": "1.0",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(duration, 2),
            "total_messages": self.seq,
            "messages_per_second": round(self.seq / duration, 2) if duration > 0 else 0,
            "signalr": {
                "url": self.SIGNALR_URL,
                "hub": self.HUB_NAME,
                "protocol": self.PROTOCOL_VERSION,
                "topics": self.ALL_TOPICS
            },
            "files": {
                "data": self.jsonl_path.name,
                "metadata": self.meta_path.name
            }
        }
        
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    
    def record(self, duration: int = 60):
        """開始錄製"""
        print("=" * 50)
        print(" F1 Pure Raw WebSocket Recorder")
        print("=" * 50)
        print(f"Output: {self.jsonl_path}")
        print(f"Duration: {duration}s")
        print()
        
        if not self._negotiate():
            return
        
        # 開啟輸出檔案
        self.file_handle = open(self.jsonl_path, 'w', encoding='utf-8')
        
        self._running = True
        try:
            asyncio.run(self._connect_and_record(duration))
        except KeyboardInterrupt:
            self._log("Stopped by user")
        finally:
            self._running = False
            self.file_handle.close()
        
        self._save_metadata()
        
        print("-" * 50)
        print(f"Total: {self.seq} messages")
        print(f"Data:  {self.jsonl_path}")
        print(f"Meta:  {self.meta_path}")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="F1 Pure Raw WebSocket Recorder")
    parser.add_argument("--duration", "-d", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output base name")
    args = parser.parse_args()
    
    recorder = PureRawRecorder(output_name=args.output)
    recorder.record(duration=args.duration)


if __name__ == "__main__":
    main()
