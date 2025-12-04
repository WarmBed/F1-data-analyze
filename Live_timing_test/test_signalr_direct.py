"""
直接連接 F1 官方 SignalR WebSocket 測試
使用 websockets 套件 + negotiate
"""
import asyncio
import websockets
import requests
import json
import base64
import zlib
from datetime import datetime
from urllib.parse import urlencode, quote

def negotiate():
    """獲取 SignalR 連接 Token"""
    url = "https://livetiming.formula1.com/signalr/negotiate"
    params = {
        "connectionData": json.dumps([{"name": "Streaming"}]),
        "clientProtocol": "1.5"
    }
    headers = {
        "User-Agent": "BestHTTP/2 v2.8.6",
    }
    
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("ConnectionToken")
    return None

async def connect_f1_signalr():
    """連接 F1 Live Timing SignalR WebSocket"""
    
    print("=" * 60)
    print("F1 Live Timing SignalR WebSocket 直接連接測試")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Negotiate 獲取 token
    print("\n1. Negotiating...")
    token = negotiate()
    if not token:
        print("❌ 無法獲取 ConnectionToken")
        return
    print(f"✅ Token: {token[:50]}...")
    
    # Step 2: 構建 WebSocket URL
    hub = "Streaming"
    topics = ["CarData.z", "Position.z", "TimingData"]
    
    connection_data = json.dumps([{"name": hub}])
    params = {
        "transport": "webSockets",
        "connectionToken": token,
        "connectionData": connection_data,
        "clientProtocol": "1.5"
    }
    ws_url = f"wss://livetiming.formula1.com/signalr/connect?{urlencode(params)}"
    
    print(f"\n2. 連接 WebSocket...")
    
    headers = {
        "User-Agent": "BestHTTP/2 v2.8.6",
    }
    
    try:
        async with websockets.connect(ws_url, extra_headers=headers) as ws:
            print("✅ WebSocket 連接成功!")
            
            # Step 3: 訂閱數據流
            subscribe_msg = {
                "H": hub,
                "M": "Subscribe",
                "A": [topics],
                "I": 1
            }
            await ws.send(json.dumps(subscribe_msg))
            print(f"📤 已發送訂閱請求: {topics}")
            
            # Step 4: 接收數據
            print("\n3. 接收即時數據...")
            count = 0
            cardata_count = 0
            
            while count < 50:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    count += 1
                    
                    data = json.loads(msg)
                    now = datetime.now().strftime('%H:%M:%S')
                    
                    # 處理消息
                    if "M" in data:
                        for m in data["M"]:
                            topic = m.get("M", "Unknown")
                            args = m.get("A", [])
                            
                            if topic == "CarData.z" or topic == "CarData":
                                cardata_count += 1
                                print(f"\n🚗 [{now}] CarData.z #{cardata_count}")
                                if args:
                                    arg = args[0]
                                    # 嘗試解壓縮
                                    if isinstance(arg, str):
                                        try:
                                            decoded = base64.b64decode(arg)
                                            decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
                                            content = json.loads(decompressed)
                                            # 顯示部分車手數據
                                            if "Entries" in content:
                                                for entry in content["Entries"][:1]:
                                                    cars = entry.get("Cars", {})
                                                    for driver_no, car in list(cars.items())[:3]:
                                                        ch = car.get("Channels", {})
                                                        print(f"  車手 #{driver_no}: SPD={ch.get('2','-')} RPM={ch.get('0','-')} G={ch.get('3','-')} THR={ch.get('4','-')} BRK={ch.get('5','-')} DRS={ch.get('45','-')}")
                                            else:
                                                print(f"  {json.dumps(content)[:300]}")
                                        except Exception as e:
                                            print(f"  解壓縮失敗: {e}")
                                            print(f"  原始: {arg[:100]}")
                                    else:
                                        print(f"  {json.dumps(arg)[:300]}")
                                        
                            elif topic == "TimingData":
                                if count <= 5:  # 只顯示前幾筆
                                    print(f"\n⏱️ [{now}] TimingData")
                                    if args:
                                        print(f"  {json.dumps(args[0])[:200]}")
                                        
                            elif topic == "Position.z" or topic == "Position":
                                print(f"\n📍 [{now}] Position.z")
                                
                    elif "R" in data:
                        print(f"\n[{now}] 訂閱回應: R={data.get('R')}")
                    elif "S" in data:
                        print(f"\n[{now}] 連接建立: S={data.get('S')}")
                        
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
                except json.JSONDecodeError as e:
                    print(f"\n[JSON Error] {e}")
                    
            print(f"\n\n=== 統計 ===")
            print(f"總訊息數: {count}")
            print(f"CarData.z 數量: {cardata_count}")
                    
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(connect_f1_signalr())
