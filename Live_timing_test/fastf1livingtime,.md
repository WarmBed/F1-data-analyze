# F1 Live Timing 自建數據擷取系統架構指南

**文件版本**: 1.0  
**適用場景**: 構建獨立後端服務，直接連接 F1 官方 SignalR 伺服器，獲取比賽即時數據 (Live Data)。

---

## 1. 專案目標 (Project Goal)
不依賴 `fastf1` 等第三方套件，從零打造一個 Client 端程式，透過 **WebSocket** 與 **SignalR** 協定連接 F1 官方伺服器，實現毫秒級的數據擷取、解碼，並即時寫入時序資料庫 (Time-Series Database)。

## 2. 核心技術堆疊 (Tech Stack)
* **協定 (Protocol)**: ASP.NET SignalR (Client Protocol 1.5)
* **傳輸 (Transport)**: WebSocket (WSS)
* **加密 (Encryption)**: HTTPS / TLS 1.2+
* **數據壓縮 (Compression)**: Base64 Encoding + Zlib (Deflate, wbits=-15)
* **資料庫 (Database)**: InfluxDB (推薦) 或 TimescaleDB
* **程式語言 (Language)**: Python (建議使用 `aiohttp` 或 `websockets` 庫)

---

## 3. 系統運作流程 (System Flow)

```mermaid
sequenceDiagram
    participant App as 自建 Python Client
    participant Auth as F1 Auth API
    participant SignalR as F1 Live Timing Server
    participant DB as InfluxDB

    Note over App: 1. 認證階段 (Authentication)
    App->>Auth: POST /authenticate (帳號/密碼/APIKey)
    Auth-->>App: 回傳 Subscription Token (JWT)

    Note over App: 2. 協商階段 (Negotiation)
    App->>SignalR: GET /negotiate (帶入 Token)
    SignalR-->>App: 回傳 Connection Token & Connection ID

    Note over App: 3. 連線階段 (Connection)
    App->>SignalR: WebSocket Connect (WSS + Encoded Token)
    SignalR-->>App: 連線建立 (Open)

    Note over App: 4. 訂閱階段 (Subscription)
    App->>SignalR: Send "Subscribe" Payload
    
    loop 資料串流 (Stream)
        SignalR->>App: 接收原始封包 (JSON)
        App->>App: 提取 "A" 欄位
        App->>App: 解碼 (Base64 -> Zlib -> JSON)
        App->>DB: 寫入數據 (InfluxDB Point)
    end


    階段HTTP MethodURL Endpoint關鍵參數 (Params/Headers)1. 認證POSThttps://api.formula1.com/v2/account/subscriber/authenticate/by-passwordHeader: apiKey  Body: Login, Password2. 協商GEThttps://livetiming.formula1.com/signalr/negotiateclientProtocol=1.5  connectionData=[{"name":"Streaming"}]  access_token={JWT_FROM_STEP_1}3. 連線WSSwss://livetiming.formula1.com/signalr/connecttransport=webSockets  clientProtocol=1.5  connectionToken={URL_ENCODED_TOKEN}


    好的，這是一份整理好的完整技術文件。你可以點擊右上角的 "Copy" 按鈕複製內容，並將其儲存為 F1_Live_Timing_Architecture.md。Markdown# F1 Live Timing 自建數據擷取系統架構指南

**文件版本**: 1.0  
**適用場景**: 構建獨立後端服務，直接連接 F1 官方 SignalR 伺服器，獲取比賽即時數據 (Live Data)。

---

## 1. 專案目標 (Project Goal)
不依賴 `fastf1` 等第三方套件，從零打造一個 Client 端程式，透過 **WebSocket** 與 **SignalR** 協定連接 F1 官方伺服器，實現毫秒級的數據擷取、解碼，並即時寫入時序資料庫 (Time-Series Database)。

## 2. 核心技術堆疊 (Tech Stack)
* **協定 (Protocol)**: ASP.NET SignalR (Client Protocol 1.5)
* **傳輸 (Transport)**: WebSocket (WSS)
* **加密 (Encryption)**: HTTPS / TLS 1.2+
* **數據壓縮 (Compression)**: Base64 Encoding + Zlib (Deflate, wbits=-15)
* **資料庫 (Database)**: InfluxDB (推薦) 或 TimescaleDB
* **程式語言 (Language)**: Python (建議使用 `aiohttp` 或 `websockets` 庫)

---

## 3. 系統運作流程 (System Flow)

```mermaid
sequenceDiagram
    participant App as 自建 Python Client
    participant Auth as F1 Auth API
    participant SignalR as F1 Live Timing Server
    participant DB as InfluxDB

    Note over App: 1. 認證階段 (Authentication)
    App->>Auth: POST /authenticate (帳號/密碼/APIKey)
    Auth-->>App: 回傳 Subscription Token (JWT)

    Note over App: 2. 協商階段 (Negotiation)
    App->>SignalR: GET /negotiate (帶入 Token)
    SignalR-->>App: 回傳 Connection Token & Connection ID

    Note over App: 3. 連線階段 (Connection)
    App->>SignalR: WebSocket Connect (WSS + Encoded Token)
    SignalR-->>App: 連線建立 (Open)

    Note over App: 4. 訂閱階段 (Subscription)
    App->>SignalR: Send "Subscribe" Payload
    
    loop 資料串流 (Stream)
        SignalR->>App: 接收原始封包 (JSON)
        App->>App: 提取 "A" 欄位
        App->>App: 解碼 (Base64 -> Zlib -> JSON)
        App->>DB: 寫入數據 (InfluxDB Point)
    end
4. 關鍵 API 端點 (Endpoints)以下為 F1 官方真實運作之端點：階段HTTP MethodURL Endpoint關鍵參數 (Params/Headers)1. 認證POSThttps://api.formula1.com/v2/account/subscriber/authenticate/by-passwordHeader: apiKey  Body: Login, Password2. 協商GEThttps://livetiming.formula1.com/signalr/negotiateclientProtocol=1.5  connectionData=[{"name":"Streaming"}]  access_token={JWT_FROM_STEP_1}3. 連線WSSwss://livetiming.formula1.com/signalr/connecttransport=webSockets  clientProtocol=1.5  connectionToken={URL_ENCODED_TOKEN}5. 實作四部曲 (Implementation Steps)步驟一：獲取權限 (Authentication)模擬 F1 App 登入以取得 subscriptionToken。注意: apiKey 若失效，需透過瀏覽器開發者工具 (Network Tab) 抓取 F1 官網登入請求中的 Header。步驟二：協商 (Negotiation)在建立 WebSocket 前，必須與 SignalR 伺服器交換資訊。請求回應中會包含 ConnectionToken。重要: 此 Token 與步驟一的 Token 不同，是用於建立 WebSocket 握手的憑證。步驟三：建立 WebSocket 連線組合最終 WSS 網址。網址範例：Plaintextwss://[livetiming.formula1.com/signalr/connect?transport=webSockets&clientProtocol=1.5&connectionToken=](https://livetiming.formula1.com/signalr/connect?transport=webSockets&clientProtocol=1.5&connectionToken=){ENCODED_TOKEN}&connectionData=[{"name":"Streaming"}]&tid=10
Header 設定: 建議設定 User-Agent: BestHTTP 以降低被阻擋機率。步驟四：訂閱與解碼 (Subscribe & Decode)4.1 發送訂閱 Payload連線後必須主動發送以下 JSON 告知伺服器需要哪些頻道：JSON{
    "H": "Streaming",
    "M": "Subscribe",
    "A": [["Heartbeat", "CarData.z", "Position.z", "TimingData", "SessionInfo"]],
    "I": 1
}
4.2 解碼管道 (The Decoding Pipeline)針對 .z 結尾的 Topic (如 CarData.z)，必須執行特殊的解壓縮程序。Python 解碼邏輯範例:Pythonimport base64
import zlib
import json

def decode_f1_packet(raw_b64_string):
    try:
        # 1. Base64 Decode
        decoded_bytes = base64.b64decode(raw_b64_string)
        # 2. Zlib Decompress (wbits=-15 是忽略 Header 的關鍵)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        # 3. Decode to String & Parse JSON
        return json.loads(decompressed_bytes.decode('utf-8'))
    except Exception as e:
        print(f"Decode Error: {e}")
        return None
6. 資料儲存策略 (Database Schema)建議使用 InfluxDB 處理高頻寫入。Measurement: telemetry類型欄位名稱範例值說明Tagsdriver_no"16", "1"車手號碼Tagssession_id"2025_Bahrain_R"賽事唯一碼Fieldsspeed310 (int)時速 (km/h)Fieldsrpm11500 (int)引擎轉速Fieldsgear8 (int)檔位Fieldsthrottle100 (int)油門深度 %Fieldsbrake0 (int)煞車深度 %Timetime(UTC Timestamp)務必使用數據包內的 Date，勿用系統時間7. 重要限制與區別 (Critical Limitations)直播 vs 重播 (Live vs Replay):本架構 僅適用於 Live 直播 當下。歷史比賽 (如 2024 Japan) 無法透過 WebSocket 連線，必須透過靜態檔案下載 (Static URL) 方式獲取。反爬蟲機制:避免在極短時間內頻繁斷線重連。妥善保存並重複使用 Session Token，不要每次連線都重新登入。數據同步:CarData (遙測) 與 Position (GPS) 是分開的串流，寫入資料庫時建議分開處理，後端查詢時再透過時間戳對齊 (Time Alignment)。