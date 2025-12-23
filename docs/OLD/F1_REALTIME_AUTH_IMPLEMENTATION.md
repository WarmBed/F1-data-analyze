# F1TV 帳號登入與 Realtime 模式整合方案

## 文件資訊
- **建立日期**: 2025-12-07
- **更新日期**: 2025-12-07
- **狀態**: 實作中
- **採用方案**: PyQtWebEngine 內嵌瀏覽器
- **下一場賽事**: 2025年2月 (澳洲站)

---

## 0. 實作進度

### 已完成
- [x] 建立 `F1TVWebAuthDialog` - 使用 PyQtWebEngine 內嵌瀏覽器
- [x] 更新 `f1tv_auth.py` - 移除 FastF1 中繼頁面，改用 WebEngine
- [x] 更新 `f1tv_auth_dialog.py` - 傳遞 parent widget

### 待完成
- [ ] 完整測試登入流程
- [ ] 確認 cookie 抓取機制
- [ ] 整合到主 GUI

---

## 1. 功能需求

### 1.1 GUI 整合需求

#### 需求 1: Help 選單新增「F1TV Account」
- 位置：主選單 Help (說明) 左側新增 F1TV Account 選項
- 點擊後開啟 F1TV 登入對話框
- 登入成功後儲存 Token

#### 需求 2: 狀態列新增 F1TV 登入狀態
- 位置：狀態列 `[API] ONLINE` 右側
- 顯示格式：
  - 未登入：`[F1TV] Not Logged In` (灰色)
  - 已登入：`[F1TV] Logged In` (綠色)
  - Token 過期：`[F1TV] Expired` (黃色)
- 點擊可快速開啟登入對話框

#### 需求 3: Live Timing Realtime 模式限制
- 未登入 F1TV 時：
  - Realtime Radio Button 禁用 (disabled)
  - 顯示提示：「需要 F1TV 帳號才能使用即時模式」
- 已登入 F1TV 時：
  - Realtime Radio Button 啟用
  - 正常連接 SignalR Core 獲取完整數據

---

## 2. 技術背景

### 2.1 為何需要 F1TV 帳號

F1 官方在 **2024年5月** 將 Live Timing API 從 `/signalr` 遷移到 `/signalrcore`：

| 端點 | 認證需求 | 可用數據 |
|------|---------|---------|
| `/signalr` (舊) | 無需認證 | TimingData, WeatherData 等基礎數據 |
| `/signalrcore` (新) | **需要 F1TV 帳號** | CarData.z, Position.z + 所有數據 |

### 2.2 Token 結構

F1TV 的 `subscriptionToken` 是一個 JWT (JSON Web Token)：

```json
{
  "payload": {
    "SubscriptionStatus": "Active",
    "SubscribedProduct": "F1 TV Pro",
    "exp": 1234567890
  }
}
```

驗證 JWKS 端點: `https://api.formula1.com/static/jwks.json`

---

## 3. GUI 實現設計

### 3.1 主選單結構變更

```
選單列 (現有)                              選單列 (變更後)
┌────┬────┬────┬──────────┬────┐          ┌────┬────┬────┬──────────┬───────────┬────┐
│File│View│Live│  Tools   │Help│    →     │File│View│Live│  Tools   │F1TV Account│Help│
└────┴────┴────┴──────────┴────┘          └────┴────┴────┴──────────┴───────────┴────┘
```

**程式碼位置**: `f1t_gui_main.py` 的 `_create_menu_bar()` 方法

**需要新增**:
```python
# 在 help_menu 之前新增 F1TV Account 選單
f1tv_menu = menubar.addMenu(tr('f1tv_account_menu', 'F1TV Account'))
f1tv_menu.addAction(
    tr('f1tv_login_action', 'Login / Manage Account'),
    self._open_f1tv_auth_dialog
)
f1tv_menu.addAction(
    tr('f1tv_logout_action', 'Logout'),
    self._logout_f1tv
)
```

### 3.2 狀態列變更

```
狀態列 (現有)                              狀態列 (變更後)
┌─────────────┐                           ┌─────────────┬─────────────────────┐
│[API] ONLINE │                     →     │[API] ONLINE │[F1TV] Not Logged In │
└─────────────┘                           └─────────────┴─────────────────────┘
```

**程式碼位置**: `f1t_gui_main.py` 的 `update_status_bar()` 方法

**需要新增**:
```python
# 在 self.api_status_label 後新增 F1TV 狀態標籤
self.f1tv_status_label = QLabel('[F1TV] Not Logged In')
self.f1tv_status_label.setObjectName('StatusF1TV')
self.f1tv_status_label.setStyleSheet('color: #888888; font-weight: bold;')
self.f1tv_status_label.setCursor(Qt.PointingHandCursor)
self.f1tv_status_label.mousePressEvent = self._on_f1tv_status_clicked
status_bar.addWidget(self.f1tv_status_label)
```

### 3.3 F1TV 狀態顯示邏輯

| 狀態 | 文字 | 顏色 | Tooltip |
|------|------|------|---------|
| 未登入 | `[F1TV] Not Logged In` | #888888 (灰) | 「點擊登入 F1TV 帳號」 |
| 已登入 | `[F1TV] Logged In` | #2ecc71 (綠) | 「F1TV Pro / 到期時間: ...」 |
| Token 過期 | `[F1TV] Expired` | #f1c40f (黃) | 「Token 已過期，點擊重新登入」 |
| 驗證中 | `[F1TV] Checking...` | #f1c40f (黃) | 「正在驗證 Token...」 |

### 3.4 Live Timing Control Dock 變更

**程式碼位置**: `modules/gui/live_timing/live_timing_modules/control_dock.py`

**現有程式碼** (第 193-195 行):
```python
self.radio_realtime = QRadioButton(tr("Realtime Live Timing", "Realtime"))
self.radio_realtime.toggled.connect(self._on_mode_changed)
self.btn_group_mode.addButton(self.radio_realtime)
```

**需要變更為**:
```python
self.radio_realtime = QRadioButton(tr("Realtime Live Timing", "Realtime"))
self.radio_realtime.toggled.connect(self._on_mode_changed)
self.radio_realtime.setEnabled(False)  # 預設禁用，等待 F1TV 登入
self.radio_realtime.setToolTip(tr(
    "realtime_requires_f1tv", 
    "Realtime mode requires F1TV account login"
))
self.btn_group_mode.addButton(self.radio_realtime)
```

**新增方法**:
```python
def set_f1tv_authenticated(self, authenticated: bool):
    """設定 F1TV 認證狀態，控制 Realtime 模式可用性"""
    self.radio_realtime.setEnabled(authenticated)
    if authenticated:
        self.radio_realtime.setToolTip(tr("realtime_available", "Realtime mode available"))
    else:
        self.radio_realtime.setToolTip(tr(
            "realtime_requires_f1tv", 
            "Realtime mode requires F1TV account login"
        ))
```

---

## 4. 認證模組設計

### 4.1 檔案結構

```
core/
├── f1tv_auth.py             # F1TV 認證管理器 (新增)
└── ...

modules/gui/live_timing/
├── core/
│   ├── signalr_client.py          # 現有 SignalR 客戶端 (舊端點，無認證)
│   └── signalr_core_client.py     # 新增：SignalR Core 客戶端 (新端點，需認證)
└── widgets/
    └── f1tv_auth_dialog.py        # 新增：F1TV 登入對話框
```

### 4.2 認證管理器 (`core/f1tv_auth.py`)

```python
"""
F1TV 認證模組

用途: 獲取 F1TV subscriptionToken 以連接 signalrcore 端點
"""

import json
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional
from datetime import datetime

import jwt
import requests
from PyQt5.QtCore import QObject, pyqtSignal


JWKS_URL = "https://api.formula1.com/static/jwks.json"
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"


class F1AuthHandler(BaseHTTPRequestHandler):
    """處理瀏覽器回傳的認證 Token"""
    
    token_received = None  # 類別變數存放 token
    
    def do_OPTIONS(self):
        """處理 CORS 預檢請求"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        """處理認證回傳"""
        if self.path == '/auth':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 從 loginSession cookie 解析 subscriptionToken
            cookie = data.get("loginSession")
            parsed_data = json.loads(urllib.parse.unquote(cookie))
            
            F1AuthHandler.token_received = parsed_data.get("data", {}).get("subscriptionToken")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
    
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')


class F1AuthManager(QObject):
    """F1TV 認證管理器"""
    
    auth_success = pyqtSignal(str)  # 認證成功，傳回 token
    auth_failed = pyqtSignal(str)   # 認證失敗，傳回錯誤訊息
    auth_status = pyqtSignal(str)   # 認證狀態更新
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._token: Optional[str] = None
        self._server: Optional[HTTPServer] = None
    
    def get_token(self) -> Optional[str]:
        """取得已存儲的 token"""
        if self._token:
            return self._token
        
        # 嘗試從檔案載入
        if AUTH_DATA_FILE.exists():
            try:
                with open(AUTH_DATA_FILE, 'r') as f:
                    self._token = f.read().strip()
                    if self._token and self._verify_token(self._token):
                        return self._token
            except Exception:
                pass
        
        return None
    
    def _verify_token(self, token: str) -> bool:
        """驗證 token 是否有效"""
        try:
            # 解碼但不驗證簽名（只檢查過期時間）
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get('exp', 0)
            return exp > datetime.now().timestamp()
        except Exception:
            return False
    
    def start_auth_flow(self):
        """啟動認證流程"""
        # 啟動本地 HTTP 服務器
        server_address = ('127.0.0.1', 0)  # 隨機端口
        self._server = HTTPServer(server_address, F1AuthHandler)
        port = self._server.server_port
        
        # 開啟認證頁面
        # 注意: 需要建立我們自己的認證中繼頁面
        auth_url = f"https://YOUR_AUTH_RELAY_PAGE?port={port}"
        webbrowser.open(auth_url)
        
        self.auth_status.emit(f"請在瀏覽器中登入 F1TV 帳號...")
        
        # 等待 token
        threading.Thread(target=self._wait_for_auth, daemon=True).start()
    
    def _wait_for_auth(self):
        """等待認證完成"""
        F1AuthHandler.token_received = None
        
        # 設置超時
        self._server.timeout = 300  # 5 分鐘
        
        while F1AuthHandler.token_received is None:
            self._server.handle_request()
        
        token = F1AuthHandler.token_received
        
        if token and self._verify_token(token):
            self._token = token
            self._save_token(token)
            self.auth_success.emit(token)
        else:
            self.auth_failed.emit("認證失敗或 token 無效")
    
    def _save_token(self, token: str):
        """儲存 token 到檔案"""
        AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUTH_DATA_FILE, 'w') as f:
            f.write(token)
    
    def clear_token(self):
        """清除已存儲的 token"""
        self._token = None
        if AUTH_DATA_FILE.exists():
            AUTH_DATA_FILE.unlink()
```

### 4.2 SignalR Core 客戶端 (`signalr_core_client.py`)

```python
"""
F1 SignalR Core Client - 認證版即時 Live Timing

連接 signalrcore 端點獲取完整遙測數據
"""

from signalrcore.hub_connection_builder import HubConnectionBuilder
from typing import List, Callable, Optional
import json
import base64
import zlib


class F1SignalRCoreClient:
    """
    F1 SignalR Core 客戶端 (需要認證)
    
    使用 signalrcore 套件連接 wss://livetiming.formula1.com/signalrcore
    """
    
    SIGNALRCORE_URL = "https://livetiming.formula1.com/signalrcore"
    
    def __init__(
        self,
        subscription_token: str,
        topics: List[str],
        on_data_callback: Optional[Callable] = None,
        on_status_callback: Optional[Callable] = None,
        on_error_callback: Optional[Callable] = None
    ):
        self.subscription_token = subscription_token
        self.topics = topics
        self._on_data = on_data_callback
        self._on_status = on_status_callback
        self._on_error = on_error_callback
        
        self._hub_connection = None
        self._running = False
    
    def _build_connection(self):
        """建立 Hub 連接"""
        self._hub_connection = HubConnectionBuilder() \
            .with_url(
                self.SIGNALRCORE_URL,
                options={
                    "headers": {
                        "Authorization": f"Bearer {self.subscription_token}"
                    }
                }
            ) \
            .with_automatic_reconnect({
                "type": "interval",
                "keep_alive_interval": 10,
                "intervals": [1, 3, 5, 10, 30]
            }) \
            .build()
        
        # 註冊事件處理
        self._hub_connection.on_open(self._on_open)
        self._hub_connection.on_close(self._on_close)
        self._hub_connection.on_error(self._on_hub_error)
        
        # 註冊 feed 消息處理
        self._hub_connection.on("feed", self._on_feed)
    
    def _on_open(self):
        """連接成功"""
        if self._on_status:
            self._on_status("SignalR Core 連接成功")
        
        # 訂閱 topics
        self._hub_connection.send("Subscribe", [self.topics])
    
    def _on_close(self):
        """連接關閉"""
        if self._on_status:
            self._on_status("SignalR Core 連接已關閉")
    
    def _on_hub_error(self, error):
        """連接錯誤"""
        if self._on_error:
            self._on_error(f"SignalR Core 錯誤: {error}")
    
    def _on_feed(self, args):
        """處理 feed 消息"""
        if len(args) >= 2:
            topic = args[0]
            data = args[1]
            
            # 處理壓縮數據
            if topic in ("CarData.z", "Position.z"):
                data = self._decode_compressed(data)
            
            if self._on_data:
                self._on_data(topic, data)
    
    def _decode_compressed(self, payload: str) -> dict:
        """解碼壓縮數據 (base64 + zlib)"""
        try:
            decoded = base64.b64decode(payload)
            decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
            return json.loads(decompressed.decode('utf-8'))
        except Exception as e:
            return {"error": str(e), "raw": payload[:100]}
    
    def start(self):
        """啟動連接"""
        self._build_connection()
        self._hub_connection.start()
        self._running = True
    
    def stop(self):
        """停止連接"""
        if self._hub_connection:
            self._hub_connection.stop()
        self._running = False
```

---

## 5. F1TV 登入對話框設計

### 5.1 對話框 UI 草圖

```
┌─────────────────────────────────────────────────┐
│              F1TV Account Login                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │                                           │  │
│  │            [F1TV Logo]                    │  │
│  │                                           │  │
│  │   Realtime Live Timing requires an        │  │
│  │   active F1TV Pro subscription.           │  │
│  │                                           │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  Status: [Not Logged In / Logged In / Expired]  │
│  Subscription: [F1TV Pro / N/A]                 │
│  Expires: [2025-12-31 / N/A]                    │
│                                                 │
│  ┌─────────────┐  ┌─────────────┐               │
│  │   Login     │  │   Logout    │               │
│  └─────────────┘  └─────────────┘               │
│                                                 │
│  [?] How to get F1TV subscription              │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 5.2 對話框類別 (`modules/gui/live_timing/widgets/f1tv_auth_dialog.py`)

```python
"""F1TV 登入對話框"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

from core.gui_i18n import tr
from core.f1tv_auth import F1TVAuthManager


class F1TVAuthDialog(QDialog):
    """F1TV 帳號登入對話框"""
    
    auth_state_changed = pyqtSignal(bool)  # True = 已登入, False = 未登入
    
    def __init__(self, auth_manager: F1TVAuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self._setup_ui()
        self._update_status_display()
        
        # 連接認證信號
        self.auth_manager.auth_success.connect(self._on_auth_success)
        self.auth_manager.auth_failed.connect(self._on_auth_failed)
    
    def _setup_ui(self):
        self.setWindowTitle(tr("f1tv_login_title", "F1TV Account"))
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # 說明區域
        info_group = QGroupBox(tr("f1tv_info", "Information"))
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel(tr(
            "f1tv_realtime_info",
            "Realtime Live Timing requires an active F1TV Pro subscription.\n"
            "Click 'Login' to authenticate with your F1TV account."
        ))
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)
        
        # 狀態區域
        status_group = QGroupBox(tr("f1tv_status", "Status"))
        status_layout = QVBoxLayout(status_group)
        
        self.lbl_status = QLabel()
        self.lbl_subscription = QLabel()
        self.lbl_expires = QLabel()
        
        status_layout.addWidget(self.lbl_status)
        status_layout.addWidget(self.lbl_subscription)
        status_layout.addWidget(self.lbl_expires)
        layout.addWidget(status_group)
        
        # 按鈕區域
        btn_layout = QHBoxLayout()
        
        self.btn_login = QPushButton(tr("f1tv_login", "Login"))
        self.btn_login.clicked.connect(self._on_login_clicked)
        btn_layout.addWidget(self.btn_login)
        
        self.btn_logout = QPushButton(tr("f1tv_logout", "Logout"))
        self.btn_logout.clicked.connect(self._on_logout_clicked)
        btn_layout.addWidget(self.btn_logout)
        
        btn_layout.addStretch()
        
        self.btn_close = QPushButton(tr("close", "Close"))
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
    
    def _update_status_display(self):
        """更新狀態顯示"""
        token_info = self.auth_manager.get_token_info()
        
        if token_info is None:
            self.lbl_status.setText(f"Status: {tr('not_logged_in', 'Not Logged In')}")
            self.lbl_status.setStyleSheet("color: #888888;")
            self.lbl_subscription.setText("Subscription: N/A")
            self.lbl_expires.setText("Expires: N/A")
            self.btn_login.setEnabled(True)
            self.btn_logout.setEnabled(False)
        elif token_info.get('expired'):
            self.lbl_status.setText(f"Status: {tr('expired', 'Expired')}")
            self.lbl_status.setStyleSheet("color: #f1c40f;")
            self.lbl_subscription.setText(f"Subscription: {token_info.get('product', 'N/A')}")
            self.lbl_expires.setText(f"Expired: {token_info.get('exp_str', 'N/A')}")
            self.btn_login.setEnabled(True)
            self.btn_logout.setEnabled(True)
        else:
            self.lbl_status.setText(f"Status: {tr('logged_in', 'Logged In')}")
            self.lbl_status.setStyleSheet("color: #2ecc71;")
            self.lbl_subscription.setText(f"Subscription: {token_info.get('product', 'N/A')}")
            self.lbl_expires.setText(f"Expires: {token_info.get('exp_str', 'N/A')}")
            self.btn_login.setEnabled(False)
            self.btn_logout.setEnabled(True)
    
    def _on_login_clicked(self):
        """開始登入流程"""
        self.btn_login.setEnabled(False)
        self.btn_login.setText(tr("logging_in", "Logging in..."))
        self.auth_manager.start_auth_flow()
    
    def _on_logout_clicked(self):
        """登出"""
        self.auth_manager.clear_token()
        self._update_status_display()
        self.auth_state_changed.emit(False)
    
    def _on_auth_success(self, token: str):
        """認證成功"""
        self.btn_login.setText(tr("f1tv_login", "Login"))
        self._update_status_display()
        self.auth_state_changed.emit(True)
        QMessageBox.information(
            self,
            tr("success", "Success"),
            tr("f1tv_login_success", "Successfully logged in to F1TV!")
        )
    
    def _on_auth_failed(self, error: str):
        """認證失敗"""
        self.btn_login.setEnabled(True)
        self.btn_login.setText(tr("f1tv_login", "Login"))
        QMessageBox.warning(
            self,
            tr("error", "Error"),
            tr("f1tv_login_failed", f"Login failed: {error}")
        )
```

---

## 6. 主 GUI 整合

### 6.1 F1TVAuthManager 全域實例

在 `f1t_gui_main.py` 的 `__init__` 中初始化：

```python
from core.f1tv_auth import F1TVAuthManager

class F1TMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 其他初始化 ...
        
        # F1TV 認證管理器
        self.f1tv_auth_manager = F1TVAuthManager(self)
        self.f1tv_auth_manager.auth_success.connect(self._on_f1tv_auth_changed)
        self.f1tv_auth_manager.auth_failed.connect(self._on_f1tv_auth_failed)
```

### 6.2 選單新增

在 `_create_menu_bar()` 方法中，`help_menu` 之前新增：

```python
def _create_menu_bar(self):
    menubar = self.menuBar()
    
    # ... 其他選單 ...
    
    # F1TV Account 選單 (在 Help 之前)
    f1tv_menu = menubar.addMenu(tr('f1tv_account_menu', 'F1TV Account'))
    
    self.f1tv_login_action = QAction(
        tr('f1tv_login_action', 'Login / Manage Account'), self
    )
    self.f1tv_login_action.triggered.connect(self._open_f1tv_auth_dialog)
    f1tv_menu.addAction(self.f1tv_login_action)
    
    f1tv_menu.addSeparator()
    
    self.f1tv_logout_action = QAction(
        tr('f1tv_logout_action', 'Logout'), self
    )
    self.f1tv_logout_action.triggered.connect(self._logout_f1tv)
    f1tv_menu.addAction(self.f1tv_logout_action)
    
    # 說明菜單
    help_menu = menubar.addMenu(tr('help_menu', '說明'))
    # ...
```

### 6.3 狀態列新增

在 `update_status_bar()` 方法中：

```python
def update_status_bar(self):
    status_bar = self.statusBar()
    status_bar.setFixedHeight(16)
    self.setStatusBar(status_bar)

    # API 狀態指示器
    self.api_status_label = QLabel('[API] Pending')
    self.api_status_label.setObjectName('StatusApi')
    self.api_status_label.setStyleSheet('color: #f1c40f; font-weight: bold;')
    status_bar.addWidget(self.api_status_label)
    
    # F1TV 狀態指示器 (新增)
    self.f1tv_status_label = QLabel('[F1TV] Not Logged In')
    self.f1tv_status_label.setObjectName('StatusF1TV')
    self.f1tv_status_label.setStyleSheet('color: #888888; font-weight: bold;')
    self.f1tv_status_label.setCursor(Qt.PointingHandCursor)
    self.f1tv_status_label.setToolTip(tr(
        'f1tv_click_to_login', 
        'Click to login to F1TV account'
    ))
    self.f1tv_status_label.mousePressEvent = lambda e: self._open_f1tv_auth_dialog()
    status_bar.addWidget(self.f1tv_status_label)
    
    # 初始化時檢查 F1TV 登入狀態
    self._update_f1tv_status_label()
```

### 6.4 新增方法

```python
def _open_f1tv_auth_dialog(self):
    """開啟 F1TV 登入對話框"""
    from modules.gui.live_timing.widgets.f1tv_auth_dialog import F1TVAuthDialog
    
    dialog = F1TVAuthDialog(self.f1tv_auth_manager, self)
    dialog.auth_state_changed.connect(self._on_f1tv_auth_changed)
    dialog.exec_()

def _logout_f1tv(self):
    """登出 F1TV"""
    reply = QMessageBox.question(
        self,
        tr('confirm', 'Confirm'),
        tr('f1tv_logout_confirm', 'Are you sure you want to logout from F1TV?'),
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        self.f1tv_auth_manager.clear_token()
        self._on_f1tv_auth_changed(False)

def _on_f1tv_auth_changed(self, authenticated: bool):
    """F1TV 認證狀態變更"""
    self._update_f1tv_status_label()
    
    # 通知所有 Live Timing 模組
    self._broadcast_f1tv_auth_state(authenticated)

def _on_f1tv_auth_failed(self, error: str):
    """F1TV 認證失敗"""
    print(f"[F1TV Auth] Failed: {error}")

def _update_f1tv_status_label(self):
    """更新 F1TV 狀態標籤"""
    if not hasattr(self, 'f1tv_status_label') or self.f1tv_status_label is None:
        return
    
    token_info = self.f1tv_auth_manager.get_token_info()
    
    if token_info is None:
        self.f1tv_status_label.setText('[F1TV] Not Logged In')
        self.f1tv_status_label.setStyleSheet('color: #888888; font-weight: bold;')
        self.f1tv_status_label.setToolTip(tr(
            'f1tv_click_to_login',
            'Click to login to F1TV account'
        ))
    elif token_info.get('expired'):
        self.f1tv_status_label.setText('[F1TV] Expired')
        self.f1tv_status_label.setStyleSheet('color: #f1c40f; font-weight: bold;')
        self.f1tv_status_label.setToolTip(tr(
            'f1tv_token_expired',
            'Token expired. Click to re-login.'
        ))
    else:
        self.f1tv_status_label.setText('[F1TV] Logged In')
        self.f1tv_status_label.setStyleSheet('color: #2ecc71; font-weight: bold;')
        product = token_info.get('product', 'F1TV')
        exp_str = token_info.get('exp_str', 'Unknown')
        self.f1tv_status_label.setToolTip(f"{product}\nExpires: {exp_str}")

def _broadcast_f1tv_auth_state(self, authenticated: bool):
    """廣播 F1TV 認證狀態到所有 Live Timing 模組"""
    # 更新 Control Dock
    if hasattr(self, '_live_timing_control_dock') and self._live_timing_control_dock:
        self._live_timing_control_dock.set_f1tv_authenticated(authenticated)
    
    # 更新所有已開啟的 Live Timing 視窗
    for sub_window in self.mdi_area.subWindowList():
        widget = sub_window.widget()
        if hasattr(widget, 'set_f1tv_authenticated'):
            widget.set_f1tv_authenticated(authenticated)
```

---

## 7. Live Timing Control Dock 整合

### 7.1 修改 control_dock.py

**位置**: `modules/gui/live_timing/live_timing_modules/control_dock.py`

**新增屬性和方法**:

```python
class ControlDock(QDockWidget):
    # ... 現有代碼 ...
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._f1tv_authenticated = False  # 新增: F1TV 認證狀態
        # ... 其他初始化 ...
    
    def set_f1tv_authenticated(self, authenticated: bool):
        """
        設定 F1TV 認證狀態，控制 Realtime 模式可用性
        
        Args:
            authenticated: True 表示已登入且 token 有效
        """
        self._f1tv_authenticated = authenticated
        self.radio_realtime.setEnabled(authenticated)
        
        if authenticated:
            self.radio_realtime.setToolTip(tr(
                "realtime_available", 
                "Realtime mode available - Connected to F1TV"
            ))
        else:
            self.radio_realtime.setToolTip(tr(
                "realtime_requires_f1tv", 
                "Realtime mode requires F1TV account login"
            ))
            
            # 如果當前在 Realtime 模式，強制切換到 Historical
            if self._mode == self.MODE_REALTIME:
                self.radio_historical.setChecked(True)
```

### 7.2 修改 _setup_ui 中的 Realtime Radio Button

```python
def _setup_ui(self):
    # ... 其他代碼 ...
    
    # 模式選擇
    row1_layout.addWidget(QLabel(tr("Mode", "Mode") + ":"))
    
    self.btn_group_mode = QButtonGroup(self)
    
    self.radio_realtime = QRadioButton(tr("Realtime Live Timing", "Realtime"))
    self.radio_realtime.setEnabled(False)  # 預設禁用
    self.radio_realtime.setToolTip(tr(
        "realtime_requires_f1tv", 
        "Realtime mode requires F1TV account login"
    ))
    self.radio_realtime.toggled.connect(self._on_mode_changed)
    self.btn_group_mode.addButton(self.radio_realtime)
    row1_layout.addWidget(self.radio_realtime)
    
    # ... 其他代碼 ...
```

### 7.3 使用者流程

```
使用者開啟 Live Timing
        │
        ▼
┌─────────────────────────────────────────┐
│  Control Dock 顯示                      │
│  - [x] Historical (預設選中)            │
│  - [ ] Realtime (禁用，灰色)            │
│                                         │
│  Tooltip: "需要 F1TV 帳號才能使用即時模式" │
└─────────────────────────────────────────┘
        │
        │ 使用者點擊 F1TV Account → Login
        ▼
┌─────────────────────────────────────────┐
│  F1TV 登入對話框                        │
│  - 開啟瀏覽器登入                       │
│  - 獲取 subscriptionToken               │
└─────────────────────────────────────────┘
        │
        │ 登入成功
        ▼
┌─────────────────────────────────────────┐
│  Control Dock 更新                      │
│  - [x] Historical                       │
│  - [ ] Realtime (啟用，可點選)          │
│                                         │
│  Tooltip: "即時模式可用 - 已連接 F1TV"   │
└─────────────────────────────────────────┘
        │
        │ 使用者選擇 Realtime
        ▼
┌─────────────────────────────────────────┐
│  使用 SignalR Core 連接                 │
│  - 帶 Authorization: Bearer token       │
│  - 訂閱 CarData.z, Position.z           │
└─────────────────────────────────────────┘
```

---

## 8. 認證中繼頁面方案

### 8.1 問題

F1 登入頁面有嚴格的 bot 檢測，無法直接透過程式自動登入。

### 8.2 解決方案選項

| 選項 | 優點 | 缺點 |
|------|------|------|
| **A. 使用 FastF1 的中繼頁面** | 簡單，已驗證可用 | 依賴第三方 |
| **B. 建立自己的中繼頁面** | 完全自主 | 需要 hosting |
| **C. 手動輸入 Token** | 最簡單 | 用戶體驗差 |

**暫時建議**: 先使用 FastF1 的中繼頁面 (`https://f1login.fastf1.dev`)，未來再建立自己的。

---

## 9. 實現優先順序

### Phase 1: GUI 基礎架構 (Week 1)
- [ ] 建立 `core/f1tv_auth.py` 認證管理器
- [ ] 實現 token 存儲和驗證
- [ ] 新增 F1TV Account 選單
- [ ] 新增狀態列 F1TV 狀態標籤

### Phase 2: 登入對話框 (Week 1-2)
- [ ] 建立 `f1tv_auth_dialog.py`
- [ ] 實現本地 HTTP 服務器接收 token
- [ ] 整合中繼頁面登入流程

### Phase 3: Live Timing 整合 (Week 2)
- [ ] 修改 Control Dock 禁用/啟用 Realtime
- [ ] 廣播認證狀態到所有模組
- [ ] 處理認證過期場景

### Phase 4: SignalR Core 客戶端 (Week 2-3)
- [ ] 建立 `signalr_core_client.py`
- [ ] 實現帶認證的訂閱
- [ ] 處理 CarData.z 和 Position.z
- [ ] 整合到現有 data_manager.py

### Phase 5: 測試和優化 (Week 3-4)
- [ ] 完整流程測試 (需等待下一場賽事)
- [ ] 錯誤處理和邊界情況
- [ ] 用戶文檔撰寫

---

## 10. 國際化 (i18n) 新增字串

需要在 `core/gui_i18n.py` 新增的翻譯：

```python
# F1TV Account 相關
'f1tv_account_menu': {'zh': 'F1TV 帳號', 'en': 'F1TV Account', 'ja': 'F1TVアカウント'},
'f1tv_login_action': {'zh': '登入 / 管理帳號', 'en': 'Login / Manage Account', 'ja': 'ログイン / アカウント管理'},
'f1tv_logout_action': {'zh': '登出', 'en': 'Logout', 'ja': 'ログアウト'},
'f1tv_login_title': {'zh': 'F1TV 帳號', 'en': 'F1TV Account', 'ja': 'F1TVアカウント'},
'f1tv_info': {'zh': '資訊', 'en': 'Information', 'ja': '情報'},
'f1tv_realtime_info': {
    'zh': '即時 Live Timing 需要有效的 F1TV Pro 訂閱。\n點擊「登入」以驗證您的 F1TV 帳號。',
    'en': 'Realtime Live Timing requires an active F1TV Pro subscription.\nClick "Login" to authenticate with your F1TV account.',
    'ja': 'リアルタイムライブタイミングには有効なF1TV Proサブスクリプションが必要です。'
},
'f1tv_status': {'zh': '狀態', 'en': 'Status', 'ja': 'ステータス'},
'f1tv_login': {'zh': '登入', 'en': 'Login', 'ja': 'ログイン'},
'f1tv_logout': {'zh': '登出', 'en': 'Logout', 'ja': 'ログアウト'},
'not_logged_in': {'zh': '未登入', 'en': 'Not Logged In', 'ja': '未ログイン'},
'logged_in': {'zh': '已登入', 'en': 'Logged In', 'ja': 'ログイン済み'},
'expired': {'zh': '已過期', 'en': 'Expired', 'ja': '期限切れ'},
'logging_in': {'zh': '登入中...', 'en': 'Logging in...', 'ja': 'ログイン中...'},
'f1tv_login_success': {'zh': '成功登入 F1TV！', 'en': 'Successfully logged in to F1TV!', 'ja': 'F1TVにログインしました！'},
'f1tv_login_failed': {'zh': '登入失敗', 'en': 'Login failed', 'ja': 'ログイン失敗'},
'f1tv_logout_confirm': {'zh': '確定要登出 F1TV 嗎？', 'en': 'Are you sure you want to logout from F1TV?', 'ja': 'F1TVからログアウトしますか？'},
'f1tv_click_to_login': {'zh': '點擊登入 F1TV 帳號', 'en': 'Click to login to F1TV account', 'ja': 'クリックしてF1TVアカウントにログイン'},
'f1tv_token_expired': {'zh': 'Token 已過期，點擊重新登入', 'en': 'Token expired. Click to re-login.', 'ja': 'トークンの有効期限が切れました。再ログインしてください。'},
'realtime_requires_f1tv': {'zh': '即時模式需要登入 F1TV 帳號', 'en': 'Realtime mode requires F1TV account login', 'ja': 'リアルタイムモードにはF1TVアカウントログインが必要です'},
'realtime_available': {'zh': '即時模式可用 - 已連接 F1TV', 'en': 'Realtime mode available - Connected to F1TV', 'ja': 'リアルタイムモード利用可能 - F1TV接続済み'},
```

---

## 11. 依賴套件

```
# 新增依賴 (requirements.txt)
signalrcore>=0.9.5    # SignalR Core 客戶端
PyJWT>=2.0            # JWT token 處理
```

**已安裝確認**:
- signalrcore: 0.9.5 ✅

---

## 12. 參考資源

### 12.1 FastF1 實現
- [PR #760](https://github.com/theOehrly/Fast-F1/pull/760) - SignalR Core + Auth 實現
- [Issue #753](https://github.com/theOehrly/Fast-F1/issues/753) - 問題討論
- [fastf1/internals/f1auth.py](https://github.com/theOehrly/Fast-F1/blob/master/fastf1/internals/f1auth.py) - 認證實現

### 12.2 signalrcore 套件
- [GitHub](https://github.com/mandrewcito/signalrcore)
- [PyPI](https://pypi.org/project/signalrcore/)

### 12.3 F1 API
- 公開 JWKS: `https://api.formula1.com/static/jwks.json`
- SignalR Core 端點: `https://livetiming.formula1.com/signalrcore`

---

## 13. 風險和注意事項

1. **F1 可能隨時改變 API** - 需要持續監控
2. **認證 token 有過期時間** - 需要處理 token 刷新
3. **需要 F1TV 訂閱** - 這是 F1 的付費功能
4. **Bot 檢測** - F1 登入有嚴格的反自動化措施
5. **用戶隱私** - 需要安全存儲 token

---

## 14. 結論

本文件定義了 F1TV 帳號登入功能的完整實現方案：

1. **GUI 整合**：Help 選單新增 F1TV Account，狀態列顯示登入狀態
2. **認證模組**：使用本地 HTTP 服務器 + 中繼頁面獲取 token
3. **Live Timing 整合**：未登入時禁用 Realtime 模式
4. **SignalR Core**：使用認證連接獲取完整遙測數據

我們有充足的時間 (到 2025 年 2 月) 來實現這個功能。
