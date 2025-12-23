#!/usr/bin/env python3
"""
測試 F1 SignalR Core (認證版) 連接

驗證使用 subscriptionToken 是否能接收 CarData.z 和 Position.z

Usage:
    python test_signalr_core_auth.py

Requirements:
    pip install signalrcore websockets
"""

import asyncio
import json
import base64
import zlib
import sys
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到 path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 檢查 signalrcore 是否可用
try:
    from signalrcore.hub_connection_builder import HubConnectionBuilder
    SIGNALRCORE_AVAILABLE = True
except ImportError:
    SIGNALRCORE_AVAILABLE = False
    print("[ERROR] signalrcore not installed. Run: pip install signalrcore")

# 載入 F1TV Token
def load_f1tv_token() -> str | None:
    """從本地 JSON 載入 F1TV token"""
    token_path = project_root / "f1auth.json"
    if not token_path.exists():
        print(f"[ERROR] Token file not found: {token_path}")
        return None
    
    try:
        with open(token_path, 'r') as f:
            data = json.load(f)
            token = data.get('subscriptionToken')
            if token:
                print(f"[OK] Token loaded (length: {len(token)})")
                return token
            else:
                print("[ERROR] No subscriptionToken in file")
                return None
    except Exception as e:
        print(f"[ERROR] Failed to load token: {e}")
        return None


def decode_z_data(encoded: str) -> dict | None:
    """解碼 .z 壓縮數據"""
    try:
        decoded = base64.b64decode(encoded)
        decompressed = zlib.decompress(decoded, wbits=-15)
        return json.loads(decompressed.decode('utf-8'))
    except Exception as e:
        print(f"[DECODE_ERROR] {e}")
        return None


class SignalRCoreTest:
    """SignalR Core 測試類"""
    
    # 新的認證端點
    SIGNALRCORE_URL = "https://livetiming.formula1.com/signalrcore"
    
    # 訂閱的主題
    TOPICS = [
        "CarData.z",
        "Position.z", 
        "TimingData",
        "DriverList",
        "WeatherData",
        "TrackStatus",
        "SessionInfo",
        "SessionStatus"
    ]
    
    def __init__(self, token: str):
        self.token = token
        self.hub_connection = None
        self.message_count = 0
        self.cardata_count = 0
        self.position_count = 0
        
    def build_connection(self):
        """建立 Hub 連接"""
        print(f"[INFO] Connecting to: {self.SIGNALRCORE_URL}")
        print(f"[INFO] Token length: {len(self.token)}")
        
        # 使用 access_token_factory 傳遞 token
        self.hub_connection = HubConnectionBuilder()\
            .with_url(self.SIGNALRCORE_URL, options={
                "access_token_factory": lambda: self.token,
                "headers": {
                    "User-Agent": "F1T/1.0"
                }
            })\
            .configure_logging(logging_level=20)\
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5
            })\
            .build()
            
    def setup_handlers(self):
        """設置消息處理器"""
        
        # 連接事件
        self.hub_connection.on_open(self._on_open)
        self.hub_connection.on_close(self._on_close)
        self.hub_connection.on_error(self._on_error)
        
        # 數據事件 - 使用 feed 方法 (參考 FastF1)
        self.hub_connection.on("feed", self._on_feed)
        
    def _on_open(self):
        print("\n[CONNECTED] SignalR Core connection established!")
        print("[INFO] Subscribing to topics...")
        
        # 訂閱主題
        for topic in self.TOPICS:
            self.hub_connection.send("Subscribe", [[topic]])
            print(f"  -> Subscribed: {topic}")
            
    def _on_close(self):
        print("\n[DISCONNECTED] SignalR Core connection closed")
        
    def _on_error(self, error):
        print(f"\n[ERROR] {error}")
        
    def _on_feed(self, data):
        """處理 feed 消息"""
        self.message_count += 1
        
        if isinstance(data, list) and len(data) >= 2:
            topic = data[0]
            payload = data[1]
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            if topic == "CarData.z":
                self.cardata_count += 1
                decoded = decode_z_data(payload) if isinstance(payload, str) else payload
                if decoded:
                    entries = decoded.get("Entries", [])
                    print(f"[{timestamp}] CarData.z #{self.cardata_count}: {len(entries)} entries")
                    if entries and self.cardata_count <= 3:
                        # 顯示前幾筆車手數據
                        sample = entries[0] if entries else {}
                        cars = sample.get("Cars", {})
                        print(f"  -> Sample: {list(cars.keys())[:5]} ...")
                        
            elif topic == "Position.z":
                self.position_count += 1
                decoded = decode_z_data(payload) if isinstance(payload, str) else payload
                if decoded:
                    positions = decoded.get("Position", [])
                    print(f"[{timestamp}] Position.z #{self.position_count}: {len(positions)} positions")
                    
            elif topic in ["TimingData", "DriverList", "WeatherData", "TrackStatus", "SessionInfo"]:
                print(f"[{timestamp}] {topic}: received")
                
            else:
                print(f"[{timestamp}] {topic}: (unknown)")
                
    def run(self, duration_seconds: int = 30):
        """運行測試"""
        print("\n" + "="*60)
        print("F1 SignalR Core (認證版) 連接測試")
        print("="*60)
        print(f"Duration: {duration_seconds} seconds")
        print(f"Topics: {', '.join(self.TOPICS)}")
        print("="*60 + "\n")
        
        self.build_connection()
        self.setup_handlers()
        
        # 開始連接
        print("[INFO] Starting connection...")
        self.hub_connection.start()
        
        try:
            # 等待指定時間
            import time
            for i in range(duration_seconds):
                time.sleep(1)
                if i % 10 == 9:
                    print(f"\n[STATS] {i+1}s: messages={self.message_count}, cardata={self.cardata_count}, position={self.position_count}")
                    
        except KeyboardInterrupt:
            print("\n[INFO] Interrupted by user")
            
        finally:
            # 停止連接
            print("\n[INFO] Stopping connection...")
            self.hub_connection.stop()
            
            # 顯示統計
            print("\n" + "="*60)
            print("測試結果統計")
            print("="*60)
            print(f"Total messages:    {self.message_count}")
            print(f"CarData.z count:   {self.cardata_count}")
            print(f"Position.z count:  {self.position_count}")
            print("="*60)
            
            if self.cardata_count > 0:
                print("\n✅ SUCCESS: CarData.z 接收正常！認證有效！")
            else:
                print("\n❌ FAILED: 未收到 CarData.z")
                print("   可能原因:")
                print("   1. 目前沒有 Live Session (賽事未進行)")
                print("   2. Token 已過期")
                print("   3. 認證失敗")


def main():
    if not SIGNALRCORE_AVAILABLE:
        print("\n[ERROR] signalrcore not installed")
        print("Run: pip install signalrcore")
        return 1
        
    # 載入 token
    token = load_f1tv_token()
    if not token:
        print("\n[ERROR] Cannot proceed without F1TV token")
        print("Please login via GUI first")
        return 1
        
    # 運行測試
    test = SignalRCoreTest(token)
    test.run(duration_seconds=30)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
