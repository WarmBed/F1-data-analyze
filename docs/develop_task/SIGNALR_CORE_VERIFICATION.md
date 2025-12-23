# F1TV SignalR Core 認證驗證任務

## 任務狀態: 待驗證 (等待下次 Live Session)

## 背景

2024年5月，F1 官方將 Live Timing API 從 `/signalr` 遷移到 `/signalrcore`：

| 端點 | 認證需求 | 可用數據 |
|------|----------|----------|
| `/signalr` (舊) | 無需認證 | TimingData, WeatherData 等基礎數據 |
| `/signalrcore` (新) | **需要 F1TV 帳號** | CarData.z, Position.z + 所有數據 |

## 已完成工作 (2025-12-07)

### 1. F1TV 登入功能
- [x] 使用 pywebview (Edge WebView2) 實現內嵌瀏覽器登入
- [x] 正確抓取 `login-session` cookie (注意: 是 hyphen 不是 camelCase)
- [x] Token 儲存到專案根目錄 `f1auth.json`
- [x] GUI 狀態列顯示 F1TV 登入狀態
- [x] F1TV Account 選單整合到主 GUI
- [x] Control Dock 的 Realtime 模式根據 F1TV 認證狀態啟用/禁用

### 2. 關鍵檔案
- `core/f1tv_auth.py` - F1TV 認證管理器 (pywebview 版本)
- `f1auth.json` - Token 儲存檔案 (專案根目錄)
- `modules/gui/live_timing/core/signalr_client.py` - 舊版 SignalR 客戶端 (無認證)
- `test_signalr_core_auth.py` - SignalR Core 測試腳本

### 3. Token 資訊
```json
{
  "subscriptionToken": "...",
  "saved_at": "2025-12-07T23:25:53.441586"
}
```

Token 包含：
- `SubscriptionStatus`: "active"
- `SubscribedProduct`: "F1 TV Pro Monthly"
- `exp`: Token 過期時間戳

## 待驗證任務 (下次比賽時)

### 任務 1: 驗證 SignalR Core 連接
**測試腳本**: `test_signalr_core_auth.py`

```powershell
python test_signalr_core_auth.py
```

**預期結果**:
- 連接成功
- 收到 `CarData.z` 數據
- 收到 `Position.z` 數據

**當前狀態**: 
- 2025-12-07 測試時返回 404 (可能因為沒有 Live Session)
- FastF1 使用的端點: `wss://livetiming.formula1.com/signalrcore`
- FastF1 使用的 negotiate URL: `https://livetiming.formula1.com/signalrcore/negotiate`

### 任務 2: 更新 signalr_client.py
如果 SignalR Core 驗證成功，需要更新現有的 `signalr_client.py`:

1. 添加認證支援 (`access_token_factory`)
2. 切換到 `/signalrcore` 端點
3. 使用 `signalrcore` 套件的 Hub 連接

**參考實現**: FastF1 的 `fastf1/livetiming/client.py`

```python
from signalrcore.hub_connection_builder import HubConnectionBuilder
from fastf1.internals.f1auth import get_auth_token

class SignalRClient:
    _connection_url = 'wss://livetiming.formula1.com/signalrcore'
    _negotiate_url = 'https://livetiming.formula1.com/signalrcore/negotiate'
    
    def _run(self):
        # Pre-negotiate to get AWSALBCORS cookie
        r = requests.options(self._negotiate_url, headers=self.headers)
        self.headers.update({"Cookie": f"AWSALBCORS={r.cookies['AWSALBCORS']}"})
        
        options = {
            "verify_ssl": True,
            "access_token_factory": get_auth_token,  # 我們的 f1tv_auth.get_token
            "headers": self.headers
        }
        
        self._connection = HubConnectionBuilder() \
            .with_url(self._connection_url, options=options) \
            .build()
        
        self._connection.on('feed', self._on_message)
        self._connection.start()
        
        # 訂閱
        self._connection.send("Subscribe", [self.topics], on_invocation=self._on_message)
```

### 任務 3: GUI 整合測試
1. 啟動 GUI
2. 確認 F1TV 狀態顯示 "Logged In"
3. 開啟 Live Timing 模組
4. 切換到 Realtime 模式
5. 點擊 Connect
6. 驗證是否收到 CarData.z 和 Position.z

## 下次比賽時間表

2025 賽季:
- **2025年2月**: 季前測試 (巴林)
- **2025年3月**: 澳洲站 (首站)

## 技術參考

### FastF1 v3.7.0 更新說明
> The livetiming client now uses a new endpoint and protocol. This follows changes by Formula 1, who have gradually phased out the old endpoints.
> 
> Support for authentication with an F1TV Access/Pro/Premium subscription has been added. Authentication is only required when using the new live timing client.

### 關鍵發現
1. **Cookie 名稱**: `login-session` (帶 hyphen)，不是 `loginSession`
2. **端點**: `/signalrcore` (不是 `/signalr`)
3. **協議**: 使用 `signalrcore` 套件 (SignalR Core / ASP.NET Core)
4. **認證**: 通過 `access_token_factory` 傳遞 token
5. **訂閱方法**: `connection.send("Subscribe", [topics])`
6. **數據接收**: 監聽 `'feed'` 事件

### 重要限制
- **Live Session Only**: SignalR 連接僅在比賽/練習/排位期間有效
- **無法重播**: 歷史賽事無法通過 WebSocket 獲取，必須使用靜態 JSON 下載
- **Token 過期**: Token 有效期約 30 天，需要定期重新登入

## 相關文件
- `docs/F1_REALTIME_AUTH_IMPLEMENTATION.md` - 完整實作文檔
- `Live_timing_test/fastf1livingtime.md` - SignalR 架構說明
- `modules/gui/live_timing/widgets/f1tv_webview_auth.py` - WebView 認證測試模組
