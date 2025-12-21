"""
F1 Live Timing 原始數據錄製工具
================================

完整錄製 F1 官方 SignalR Live Timing 的原始 WebSocket 訊息。
不做任何解析或處理，保留完整的原始數據格式。

輸出格式:
{
    "start_time": "2025-12-07T21:15:30",
    "metadata": {
        "protocol_version": "1.5",
        "subscribed_topics": [...],
        "connection_token": "..."
    },
    "messages": [
        {
            "seq": 1,
            "timestamp": "2025-12-07T21:15:30.123456",
            "raw": "{...原始 WebSocket 訊息...}"
        },
        ...
    ],
    "end_time": "2025-12-07T21:16:30",
    "total_messages": 586,
    "duration_seconds": 60
}

用法:
    python record_live_timing_raw.py --duration 60
    python record_live_timing_raw.py --duration 300 --output my_recording.json

Author: F1T Team
Date: 2025-12-07
"""

import sys
import os
import json
import time
import asyncio
import threading
import argparse
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

# 檢查 websockets
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("[ERROR] websockets not installed! Run: pip install websockets")
    sys.exit(1)


class RawLiveTimingRecorder:
    """原始 Live Timing 錄製器"""
    
    SIGNALR_URL = "https://livetiming.formula1.com/signalr"
    HUB_NAME = "Streaming"
    PROTOCOL_VERSION = "1.5"
    
    # 所有可用的 topics
    ALL_TOPICS = [
        # 壓縮數據 (最重要)
        "CarData.z",
        "Position.z",
        # 計時數據
        "TimingData",
        "TimingDataF1",
        "TimingAppData",
        "TimingStats",
        # 車手和賽事
        "DriverList",
        "SessionInfo",
        "SessionStatus",
        "SessionData",
        # 賽道狀態
        "TrackStatus",
        "WeatherData",
        "WeatherDataSeries",
        # 賽事控制
        "RaceControlMessages",
        "LapCount",
        "LapSeries",
        # 輪胎
        "CurrentTyres",
        "TyreStintSeries",
        # 進站
        "PitStopSeries",
        "PitLaneTimeCollection",
        # 其他
        "TopThree",
        "Heartbeat",
        "ExtrapolatedClock",
        "TeamRadio",
        "ContentStreams",
        "AudioStreams",
        "ArchiveStatus",
        "ChampionshipPrediction",
        "DriverRaceInfo",
    ]
    
    def __init__(self, output_path: Optional[str] = None):
        """
        初始化錄製器
        
        Args:
            output_path: 輸出檔案路徑，None 則自動生成
        """
        self.output_dir = Path("data/live_timing_recordings")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if output_path:
            self.output_path = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_path = self.output_dir / f"raw_recording_{timestamp}.json"
        
        # 錄製數據
        self.messages: List[Dict] = []
        self.subscription_response: Dict = {}  # R key 的初始數據
        self.seq = 0
        
        # 連接狀態
        self._running = False
        self._ws = None
        self._session = None
        self._connection_token = None
        self._cookie = None
        
        # 時間戳
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # 統計
        self.topic_counts: Dict[str, int] = {}
        
    def _log(self, msg: str, level: str = "INFO"):
        """輸出日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {msg}")
    
    def _negotiate(self) -> bool:
        """與 SignalR 協商連接"""
        self._log("Negotiating SignalR connection...")
        
        try:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "BestHTTP",
                "Accept-Encoding": "gzip, identity",
                "Connection": "keep-alive, Upgrade"
            })
            
            conn_data = json.dumps([{"name": self.HUB_NAME}])
            negotiate_url = f"{self.SIGNALR_URL}/negotiate"
            params = {
                "connectionData": conn_data,
                "clientProtocol": self.PROTOCOL_VERSION
            }
            
            response = self._session.get(negotiate_url, params=params, timeout=10)
            
            if response.status_code != 200:
                self._log(f"Negotiate failed: HTTP {response.status_code}", "ERROR")
                return False
            
            data = response.json()
            self._connection_token = data.get("ConnectionToken")
            protocol_version = data.get("ProtocolVersion", self.PROTOCOL_VERSION)
            
            if not self._connection_token:
                self._log("Negotiate failed: No ConnectionToken", "ERROR")
                return False
            
            self._cookie = "; ".join([f"{name}={value}" for name, value in response.cookies.items()])
            
            self._log(f"Negotiate successful, Protocol: {protocol_version}")
            return True
            
        except Exception as e:
            self._log(f"Negotiate exception: {e}", "ERROR")
            return False
    
    def _build_ws_url(self) -> str:
        """構建 WebSocket URL"""
        conn_data = json.dumps([{"name": self.HUB_NAME}])
        params = {
            "transport": "webSockets",
            "connectionToken": self._connection_token,
            "connectionData": conn_data,
            "clientProtocol": self.PROTOCOL_VERSION
        }
        query = urllib.parse.urlencode(params)
        return f"wss://livetiming.formula1.com/signalr/connect?{query}"
    
    def _record_message(self, raw_msg: str):
        """記錄原始訊息"""
        self.seq += 1
        now = datetime.now()
        
        # 記錄完整的原始訊息
        record = {
            "seq": self.seq,
            "timestamp": now.isoformat(),
            "raw": raw_msg
        }
        self.messages.append(record)
        
        # 嘗試解析以統計 topic（但不影響原始錄製）
        try:
            data = json.loads(raw_msg)
            
            # 處理訂閱回應 (R key)
            if "R" in data and not self.subscription_response:
                self.subscription_response = data["R"]
                self._log(f"Received subscription response with {len(self.subscription_response)} topics")
            
            # 統計 topic
            messages = data.get("M", [])
            for msg in messages:
                args = msg.get("A", [])
                if args:
                    topic = args[0]
                    self.topic_counts[topic] = self.topic_counts.get(topic, 0) + 1
                    
        except:
            pass
        
        # 顯示進度
        if self.seq % 50 == 0:
            elapsed = (now - self.start_time).total_seconds()
            rate = self.seq / elapsed if elapsed > 0 else 0
            self._log(f"Recorded {self.seq} messages ({rate:.1f}/s)")
    
    async def _connect_and_record(self, duration_seconds: int):
        """連接並錄製"""
        ws_url = self._build_ws_url()
        
        headers = {
            "User-Agent": "BestHTTP",
            "Accept-Encoding": "gzip, identity",
        }
        if self._cookie:
            headers["Cookie"] = self._cookie
        
        self._log("Establishing WebSocket connection...")
        
        try:
            async with websockets.connect(ws_url, extra_headers=headers) as ws:
                self._ws = ws
                self._log("WebSocket connected")
                
                # 發送訂閱請求
                subscribe_msg = {
                    "H": self.HUB_NAME,
                    "M": "Subscribe",
                    "A": [self.ALL_TOPICS],
                    "I": 0
                }
                await ws.send(json.dumps(subscribe_msg))
                self._log(f"Subscribed to {len(self.ALL_TOPICS)} topics")
                
                # 錄製開始
                self.start_time = datetime.now()
                end_time = self.start_time.timestamp() + duration_seconds
                
                self._log(f"Recording for {duration_seconds} seconds...")
                self._log("Press Ctrl+C to stop early")
                print("-" * 60)
                
                while self._running and time.time() < end_time:
                    try:
                        # 接收原始訊息
                        raw_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        
                        if raw_msg:
                            self._record_message(raw_msg)
                            
                    except asyncio.TimeoutError:
                        # 發送心跳保持連接
                        try:
                            await ws.ping()
                        except:
                            pass
                    except websockets.exceptions.ConnectionClosed:
                        self._log("WebSocket connection closed", "WARNING")
                        break
                    except Exception as e:
                        self._log(f"Receive error: {e}", "ERROR")
                        
        except Exception as e:
            self._log(f"WebSocket connection failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
    
    def _save_recording(self):
        """保存錄製結果"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        
        # 構建完整的錄製檔案
        recording = {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "metadata": {
                "protocol_version": self.PROTOCOL_VERSION,
                "subscribed_topics": self.ALL_TOPICS,
                "hub_name": self.HUB_NAME,
                "signalr_url": self.SIGNALR_URL,
                "recorder_version": "1.0"
            },
            "subscription_response": self.subscription_response,
            "messages": self.messages,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_messages": len(self.messages),
            "duration_seconds": round(duration, 2),
            "topic_counts": self.topic_counts,
            "messages_per_second": round(len(self.messages) / duration, 2) if duration > 0 else 0
        }
        
        # 保存主錄製檔案
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(recording, f, indent=2, ensure_ascii=False)
        
        self._log(f"Recording saved: {self.output_path}")
        
        # 另外保存訂閱回應（初始狀態）
        if self.subscription_response:
            sub_path = self.output_path.parent / f"subscription_{self.output_path.stem}.json"
            with open(sub_path, 'w', encoding='utf-8') as f:
                json.dump(self.subscription_response, f, indent=2, ensure_ascii=False)
            self._log(f"Subscription response saved: {sub_path}")
        
        return recording
    
    def record(self, duration_seconds: int = 60) -> Dict:
        """
        開始錄製
        
        Args:
            duration_seconds: 錄製時長（秒）
            
        Returns:
            錄製結果
        """
        print("=" * 60)
        print(" F1 Live Timing Raw Recorder")
        print("=" * 60)
        print(f"Output: {self.output_path}")
        print(f"Duration: {duration_seconds} seconds")
        print()
        
        # 1. Negotiate
        if not self._negotiate():
            return {}
        
        # 2. Connect and record
        self._running = True
        try:
            asyncio.run(self._connect_and_record(duration_seconds))
        except KeyboardInterrupt:
            self._log("Stopped by user")
        finally:
            self._running = False
        
        # 3. Save
        print("-" * 60)
        result = self._save_recording()
        
        # 4. Print summary
        print()
        print("=" * 60)
        print(" Recording Summary")
        print("=" * 60)
        print(f"Total messages: {result.get('total_messages', 0)}")
        print(f"Duration: {result.get('duration_seconds', 0):.1f} seconds")
        print(f"Rate: {result.get('messages_per_second', 0):.1f} messages/second")
        print()
        print("Topic counts:")
        for topic, count in sorted(self.topic_counts.items(), key=lambda x: -x[1]):
            print(f"  {topic:<25}: {count:>6}")
        print()
        print(f"Output file: {self.output_path}")
        print("=" * 60)
        
        return result


def main():
    parser = argparse.ArgumentParser(
        description="F1 Live Timing Raw Recorder - 完整錄製原始 SignalR 訊息"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=60,
        help="錄製時長（秒），預設 60 秒"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="輸出檔案路徑，預設自動生成"
    )
    
    args = parser.parse_args()
    
    recorder = RawLiveTimingRecorder(output_path=args.output)
    recorder.record(duration_seconds=args.duration)


if __name__ == "__main__":
    main()
