"""
F1 官方 SignalR API 連接測試

測試項目:
1. Negotiate 請求
2. WebSocket 連接
3. 數據訂閱和接收
"""

import os
import sys
import json
import base64
import zlib
import asyncio
import requests
import urllib.parse

# 添加根目錄
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 檢查 websockets
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("[ERROR] websockets 未安裝. 執行: pip install websockets")


SIGNALR_URL = "https://livetiming.formula1.com/signalr"
HUB_NAME = "Streaming"
PROTOCOL_VERSION = "1.5"


def negotiate():
    """測試 Negotiate 請求"""
    print("=" * 60)
    print("測試 1: Negotiate 請求")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "BestHTTP",
        "Accept-Encoding": "gzip, identity",
    })
    
    conn_data = json.dumps([{"name": HUB_NAME}])
    params = {
        "connectionData": conn_data,
        "clientProtocol": PROTOCOL_VERSION
    }
    
    print(f"請求 URL: {SIGNALR_URL}/negotiate")
    print(f"參數: {params}")
    
    response = session.get(f"{SIGNALR_URL}/negotiate", params=params, timeout=10)
    
    print(f"\n狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Protocol Version: {data.get('ProtocolVersion')}")
        print(f"Connection Token (前50字): {data.get('ConnectionToken', '')[:50]}...")
        print(f"Disconnect Timeout: {data.get('DisconnectTimeout')}")
        print(f"Keep Alive Timeout: {data.get('KeepAliveTimeout')}")
        print(f"Transport Connect Timeout: {data.get('TransportConnectTimeout')}")
        print("\n[SUCCESS] Negotiate 成功!")
        return session, data.get("ConnectionToken"), response.cookies
    else:
        print(f"[ERROR] Negotiate 失敗: {response.text}")
        return None, None, None


async def test_websocket(token, cookies):
    """測試 WebSocket 連接"""
    if not WEBSOCKETS_AVAILABLE:
        print("[ERROR] websockets 未安裝，跳過 WebSocket 測試")
        return
    
    print("\n" + "=" * 60)
    print("測試 2: WebSocket 連接")
    print("=" * 60)
    
    conn_data = json.dumps([{"name": HUB_NAME}])
    params = {
        "transport": "webSockets",
        "connectionToken": token,
        "connectionData": conn_data,
        "clientProtocol": PROTOCOL_VERSION
    }
    query = urllib.parse.urlencode(params)
    ws_url = f"wss://livetiming.formula1.com/signalr/connect?{query}"
    
    print(f"WebSocket URL (前100字): {ws_url[:100]}...")
    
    # 構建 headers
    headers = {
        "User-Agent": "BestHTTP",
        "Accept-Encoding": "gzip, identity",
    }
    cookie_str = "; ".join([f"{name}={value}" for name, value in cookies.items()])
    if cookie_str:
        headers["Cookie"] = cookie_str
    
    try:
        async with websockets.connect(ws_url, extra_headers=headers) as ws:
            print("[SUCCESS] WebSocket 連接成功!")
            
            # 發送訂閱請求
            topics = [
                "CarData.z",
                "Position.z", 
                "TimingData",
                "DriverList",
                "SessionInfo",
                "WeatherData",
                "TrackStatus"
            ]
            
            subscribe_msg = {
                "H": HUB_NAME,
                "M": "Subscribe",
                "A": [topics],
                "I": 0
            }
            
            print(f"\n發送訂閱請求: {topics}")
            await ws.send(json.dumps(subscribe_msg))
            
            # 接收消息
            print("\n等待數據 (最多 10 秒)...")
            message_count = 0
            data_topics_received = set()
            
            try:
                for _ in range(10):  # 最多等待 10 秒
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1)
                        if msg:
                            data = json.loads(msg)
                            message_count += 1
                            
                            # 檢查消息內容
                            if "M" in data:
                                for m in data["M"]:
                                    if "A" in m and len(m["A"]) >= 1:
                                        topic = m["A"][0]
                                        data_topics_received.add(topic)
                                        
                                        if len(data_topics_received) % 3 == 1:  # 每收到新 topic 打印
                                            print(f"  收到 Topic: {topic}")
                            
                            if "R" in data:
                                print("  [INFO] 訂閱回應已收到")
                            
                            if "S" in data:
                                print("  [INFO] 連接確認已收到")
                            
                            # 收到足夠數據後退出
                            if len(data_topics_received) >= 5:
                                print(f"\n已收到 {len(data_topics_received)} 種數據類型，測試成功!")
                                break
                                
                    except asyncio.TimeoutError:
                        continue
                    
            except Exception as e:
                print(f"接收錯誤: {e}")
            
            print(f"\n總共收到 {message_count} 條消息")
            print(f"數據類型: {data_topics_received}")
            
            if data_topics_received:
                print("\n[SUCCESS] WebSocket 數據接收成功!")
            else:
                print("\n[WARNING] 未收到任何數據 (可能沒有進行中的賽事)")
                
    except Exception as e:
        print(f"[ERROR] WebSocket 連接失敗: {e}")
        import traceback
        traceback.print_exc()


def test_decompress():
    """測試數據解壓縮"""
    print("\n" + "=" * 60)
    print("測試 3: 數據解壓縮邏輯")
    print("=" * 60)
    
    # 模擬壓縮數據 (CarData.z 格式)
    test_data = {
        "Entries": [{
            "Utc": "2024-07-28T12:06:49.419Z",
            "Cars": {
                "1": {"Channels": {"0": 10500, "2": 320, "3": 8, "4": 100, "5": 0, "45": 1}},
                "4": {"Channels": {"0": 10200, "2": 315, "3": 7, "4": 85, "5": 10, "45": 0}}
            }
        }]
    }
    
    # 壓縮
    json_str = json.dumps(test_data)
    compressed = zlib.compress(json_str.encode("utf-8"), level=9)
    # 移除 zlib header (因為解壓用 -MAX_WBITS)
    # 需要用 raw deflate
    import io
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    compressed = compressor.compress(json_str.encode("utf-8")) + compressor.flush()
    encoded = base64.b64encode(compressed).decode("utf-8")
    
    print(f"原始數據大小: {len(json_str)} bytes")
    print(f"壓縮後大小: {len(compressed)} bytes")
    print(f"Base64 編碼後: {len(encoded)} bytes")
    print(f"Base64 數據 (前50字): {encoded[:50]}...")
    
    # 解壓縮
    try:
        decoded = base64.b64decode(encoded)
        decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
        result = json.loads(decompressed.decode("utf-8"))
        print(f"\n解壓縮結果: {result}")
        print("\n[SUCCESS] 解壓縮邏輯正確!")
    except Exception as e:
        print(f"[ERROR] 解壓縮失敗: {e}")


def main():
    print("=" * 60)
    print("F1 官方 SignalR API 連接測試")
    print("=" * 60)
    
    # 測試 1: Negotiate
    session, token, cookies = negotiate()
    if not token:
        print("\n[ABORT] Negotiate 失敗，無法繼續測試")
        return
    
    # 測試 2: WebSocket
    if WEBSOCKETS_AVAILABLE:
        asyncio.run(test_websocket(token, cookies))
    
    # 測試 3: 解壓縮
    test_decompress()
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
