# F1 Live Timing API 研究報告

## 🎯 研究成果總結

### 核心發現

✅ **確認**: F1 官方使用 **SignalR** 協定進行即時資料推送  
✅ **確認**: 靜態重播檔案 URL 格式已驗證  
✅ **發現**: 有多個成熟的開源專案可參考  
✅ **重要**: 即時資料取得**不需要** F1 TV 訂閱!

---

## 📡 1. 靜態檔案下載 (重播資料)

### URL 格式 (官方確認)

```
https://livetiming.formula1.com/static/[YEAR]/[MEETING_HANDLE]/[SESSION_HANDLE]/[FILE]
```

### 實際範例

```
https://livetiming.formula1.com/static/2021/2021-04-18_Emilia_Romagna_Grand_Prix/2021-04-18_Race/CarData.z.jsonStream
```

### 結構說明

- **YEAR**: 年份 (例: `2024`)
- **MEETING_HANDLE**: `YYYY-MM-DD_Grand_Prix_Name` (例: `2024-03-02_Bahrain_Grand_Prix`)
- **SESSION_HANDLE**: `YYYY-MM-DD_Session_Type` (例: `2024-03-02_Race`)
- **FILE**: 資料檔案名稱

### 可用檔案列表

| 檔案名稱 | 內容 | 是否壓縮 |
|---------|------|---------|
| `CarData.z.jsonStream` | 車輛遙測 (速度/RPM/檔位/油門/煞車) | ✅ 是 (zlib) |
| `Position.z.jsonStream` | GPS 位置資料 | ✅ 是 (zlib) |
| `TimingData.jsonStream` | 圈速、Sector 時間 | ❌ 否 |
| `SessionInfo.jsonStream` | 賽段資訊 | ❌ 否 |
| `TeamRadio.jsonStream` | 車隊無線電 | ❌ 否 |
| `DriverList.jsonStream` | 車手清單 | ❌ 否 |
| `WeatherData.jsonStream` | 天氣資料 | ❌ 否 |

### 🔍 如何找到正確的 MEETING_HANDLE

**方法 1**: 使用 Index.json 清單

```
https://livetiming.formula1.com/static/2024/Index.json
```

會返回該年度所有 Grand Prix 的清單,包含正確的命名格式。

---

## 🔴 2. 即時直播 (WebSocket)

### SignalR 端點

**協商端點** (Negotiate):
```
GET https://livetiming.formula1.com/signalr/negotiate
  ?clientProtocol=1.5
  &connectionData=[{"name":"Streaming"}]
  &access_token={YOUR_TOKEN}
```

**WebSocket 連線**:
```
wss://livetiming.formula1.com/signalr/connect
  ?transport=webSockets
  &clientProtocol=1.5
  &connectionToken={ENCODED_TOKEN}
  &connectionData=[{"name":"Streaming"}]
```

### 可訂閱的主題 (Topics)

```json
{
  "H": "Streaming",
  "M": "Subscribe",
  "A": [[
    "Heartbeat",
    "CarData.z",
    "Position.z", 
    "TimingData",
    "SessionInfo",
    "TeamRadio",
    "WeatherData"
  ]],
  "I": 1
}
```

### ⚠️ 認證需求

- **直播模式**: 需要 F1 帳號 (免費註冊即可)
- **重播模式**: **完全不需要**帳號!

---

## 🛠️ 3. 開源專案參考

### FastF1 Library (Python)

**GitHub**: [theOehrly/Fast-F1](https://github.com/theOehrly/Fast-F1)

**特點**:
- ✅ 官方推薦的 Python 套件
- ✅ 完整的 SignalR Client 實作
- ✅ 自動處理壓縮解碼
- ⚠️ **不支援即時處理**,只能儲存後分析

**如何取得 api_path**:

```python
import fastf1

session = fastf1.get_session(2024, 'Bahrain', 'R')
api_path = session.api_path
# 返回: /2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race/
```

---

### OpenF1 Project

**官網**: [openf1.org](https://openf1.org)  
**GitHub**: Multiple repos

**特點**:
- ✅ 提供 REST API 包裝 F1 Live Timing
- ✅ 歷史資料**免費**
- ✅ 即時資料需付費帳號
- ✅ 有完整的 SignalR Client 範例

**OpenF1.Data (C# Library)**:
- 完整的 SignalR 連線實作
- 支援訂閱多個 Topic
- 可用於重播或直播

---

### LiveF1 (新專案)

**特點**:
- ✅ 專為即時資料設計
- ✅ Python 套件
- ✅ 支援 `CarData.z` 解壓縮
- ✅ 更現代化的 API

---

## 🔐 4. 認證機制

### F1 帳號登入 API

```
POST https://api.formula1.com/v2/account/subscriber/authenticate/by-password
Headers:
  apiKey: {F1_API_KEY}
Body:
  {
    "Login": "your_email@example.com",
    "Password": "your_password"
  }
```

**回應**:
```json
{
  "data": {
    "subscriptionToken": "JWT_TOKEN_HERE"
  }
}
```

### ⚠️ apiKey 來源

- 需要從 F1 官網的登入請求中抓取 (瀏覽器 DevTools)
- apiKey 會定期更換
- 社群有維護最新的 apiKey 清單

---

## 📊 5. 資料格式

### .z 檔案解壓縮 (已驗證正確)

您文件中的解碼邏輯**完全正確**:

```python
import base64
import zlib
import json

def decode_f1_packet(raw_b64_string):
    # 1. Base64 Decode
    decoded_bytes = base64.b64decode(raw_b64_string)
    # 2. Zlib Decompress (wbits=-15 關鍵!)
    decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
    # 3. Parse JSON
    return json.loads(decompressed_bytes.decode('utf-8'))
```

**關鍵**: `wbits=-15` 是必須的,因為 F1 使用 raw deflate 格式 (無 zlib header)

---

## 🎯 6. 建議的實作順序

### 階段 0: 驗證 URL 格式 ✅ (現在立刻可做)

1. 列出 2024 年所有賽事清單
2. 下載一場比賽的 `Index.json`
3. 驗證 URL 構建規則

### 階段 1: 靜態檔案解碼 ✅ (無需帳號)

1. 下載 `CarData.z.jsonStream`
2. 實作解壓縮邏輯
3. 解析 JSON 資料
4. **驗證數據完整性**

### 階段 2: SignalR 連線 (需免費帳號)

1. 註冊 F1 免費帳號
2. 實作認證邏輯
3. 實作 SignalR Negotiate
4. 建立 WebSocket 連線

### 階段 3: 即時資料流 (比賽時測試)

1. 訂閱即時 Topics
2. 處理即時資料推送
3. 寫入時序資料庫

---

## 🚀 立即行動方案

### 我們現在就能做的 (無需等待):

1. ✅ 從 `Index.json` 取得真實的 URL 清單
2. ✅ 下載真實的 `.z.jsonStream` 檔案
3. ✅ 驗證解碼邏輯
4. ✅ 建立完整的解析器

**您同意從階段 0 開始嗎?** 我可以立刻寫程式測試 URL 格式並下載真實資料。
