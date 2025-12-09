#!/usr/bin/env python3
"""
F1TV WebEngine 登入對話框

使用 PyQtWebEngine 內嵌瀏覽器直接登入 F1TV 官方網站，
並自動抓取 loginSession cookie 中的 subscriptionToken。

優點:
- 無需安裝瀏覽器插件
- 無需依賴第三方中繼頁面
- 用戶直接在 GUI 內完成登入
"""

import json
import urllib.parse
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QFont

# WebEngine imports
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
    from PyQt5.QtWebChannel import QWebChannel
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    from core.logger import get_logger
    logger = get_logger("live_timing.f1tv_web_auth_dialog", component="gui")
    logger.warning("PyQtWebEngine not available")

from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger("live_timing.f1tv_web_auth_dialog", component="gui")


# F1TV 登入相關 URL
# 注意：使用 hash-based routing (#/) 而非 path-based routing
F1_LOGIN_URL = "https://account.formula1.com/#/en/login?redirect=https%3A%2F%2Ff1tv.formula1.com%2F"
F1_ACCOUNT_URL = "https://account.formula1.com"
F1TV_URL = "https://f1tv.formula1.com"


class F1TVWebAuthDialog(QDialog):
    """
    F1TV WebEngine 登入對話框
    
    使用內嵌瀏覽器讓用戶直接登入 F1TV，
    登入成功後自動抓取 subscriptionToken。
    """
    
    # 信號
    auth_success = pyqtSignal(str)  # 認證成功，傳回 token
    auth_failed = pyqtSignal(str)   # 認證失敗
    auth_cancelled = pyqtSignal()   # 認證取消
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._token: Optional[str] = None
        self._checking_cookie = False
        self._setup_ui()
    
    def _setup_ui(self):
        """設置 UI"""
        self.setWindowTitle(tr('f1tv_login_title', 'F1TV Login'))
        self.setMinimumSize(900, 700)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 頂部工具列
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 5, 10, 5)
        toolbar.setSpacing(10)
        
        # 標題
        title_label = QLabel(tr('f1tv_login_instruction', 'Please login with your F1TV account'))
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        toolbar.addWidget(title_label)
        
        toolbar.addStretch()
        
        # 狀態標籤
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666666;")
        toolbar.addWidget(self.status_label)
        
        # 取消按鈕
        self.btn_cancel = QPushButton(tr('cancel', 'Cancel'))
        self.btn_cancel.clicked.connect(self._on_cancel)
        toolbar.addWidget(self.btn_cancel)
        
        layout.addLayout(toolbar)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #e10600;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # WebEngine 視圖
        if WEBENGINE_AVAILABLE:
            self._setup_webengine()
            layout.addWidget(self.web_view, 1)
        else:
            error_label = QLabel(tr(
                'f1tv_webengine_not_available',
                'PyQtWebEngine is not installed.\n'
                'Please install it with: pip install PyQtWebEngine'
            ))
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: #e74c3c; padding: 50px;")
            layout.addWidget(error_label, 1)
    
    def _setup_webengine(self):
        """設置 WebEngine"""
        # 創建 off-the-record (隱私) profile 
        # 這樣不會影響用戶的其他 cookies，且 cookie 信號正常觸發
        self.profile = QWebEngineProfile(self)  # 無名稱 = off-the-record
        
        # 設置 User-Agent 以避免 "Unsupported Browser" 問題
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")
        self.profile.setHttpUserAgent(ua)
        
        # 創建頁面
        self.page = QWebEnginePage(self.profile, self)
        
        # 創建視圖
        self.web_view = QWebEngineView(self)
        self.web_view.setPage(self.page)
        
        # 連接信號
        self.web_view.loadStarted.connect(self._on_load_started)
        self.web_view.loadProgress.connect(self._on_load_progress)
        self.web_view.loadFinished.connect(self._on_load_finished)
        self.web_view.urlChanged.connect(self._on_url_changed)
        
        # Cookie store 連接
        cookie_store = self.profile.cookieStore()
        cookie_store.cookieAdded.connect(self._on_cookie_added)
        
        # 設置 cookie 過濾器來記錄所有 cookie 活動
        def cookie_filter(request):
            origin = request.origin.toString() if request.origin else "unknown"
            logger.debug("Cookie request from: %s", origin)
            return True  # 允許所有 cookies
        cookie_store.setCookieFilter(cookie_filter)
    
    def start_login(self):
        """開始登入流程"""
        if not WEBENGINE_AVAILABLE:
            self.auth_failed.emit("PyQtWebEngine not available")
            return
        
        self._token = None
        self._checking_cookie = False
        self.status_label.setText(tr('f1tv_loading', 'Loading...'))
        
        # Off-the-record profile 每次都是乾淨的，不需要清除 cookies
        logger.info("Starting login flow...")
        logger.debug("Loading URL: %s", F1_LOGIN_URL)
        
        # 載入 F1 登入頁面
        self.web_view.load(QUrl(F1_LOGIN_URL))
        
        # 顯示對話框
        self.show()
    
    def _on_load_started(self):
        """頁面開始載入"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
    
    def _on_load_progress(self, progress: int):
        """頁面載入進度"""
        self.progress_bar.setValue(progress)
    
    def _on_load_finished(self, ok: bool):
        """頁面載入完成"""
        self.progress_bar.setVisible(False)
        
        if ok:
            current_url = self.web_view.url().toString()
            self.status_label.setText(self._get_url_display(current_url))
            
            # 如果載入完成且已經在帳號頁面或 F1TV 頁面，嘗試檢查 cookie
            if 'account.formula1.com' in current_url or 'f1tv.formula1.com' in current_url:
                self._check_login_cookie()
        else:
            self.status_label.setText(tr('f1tv_load_error', 'Failed to load page'))
    
    def _on_url_changed(self, url: QUrl):
        """URL 變更"""
        url_str = url.toString()
        logger.debug("URL changed: %s", url_str)
        self.status_label.setText(self._get_url_display(url_str))
        
        # 檢測登入成功的跳轉
        # F1 登入成功後通常會跳轉回首頁或帳號頁面
        if any(domain in url_str for domain in ['account.formula1.com', 'f1tv.formula1.com']):
            if 'login' not in url_str.lower():
                # 可能已經登入成功，延遲檢查 cookie
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1000, self._check_login_cookie)
    
    def _on_cookie_added(self, cookie):
        """Cookie 添加事件"""
        try:
            # cookie.name() 和 cookie.value() 返回 QByteArray
            # cookie.domain() 返回 str
            name_raw = cookie.name()
            if hasattr(name_raw, 'data'):
                name = bytes(name_raw.data()).decode('utf-8', errors='ignore')
            else:
                name = str(name_raw)
            
            domain = cookie.domain()  # 已經是 str
            
            # 記錄所有 cookie 活動 (幫助偵錯)
            logger.debug("Cookie added: %s (domain: %s)", name, domain)
            
            # 檢查是否是 loginSession cookie
            if name == 'loginSession':
                logger.info("loginSession cookie detected")
                value_raw = cookie.value()
                if hasattr(value_raw, 'data'):
                    value = bytes(value_raw.data()).decode('utf-8', errors='ignore')
                else:
                    value = str(value_raw)
                logger.debug("Cookie value length: %s", len(value))
                self._extract_token_from_cookie(value)
        except Exception as e:
            logger.error("Error processing cookie: %s", e)
    
    def _check_login_cookie(self):
        """檢查登入 cookie"""
        if self._checking_cookie or self._token:
            return
        
        self._checking_cookie = True
        
        # 使用 JavaScript 檢查 cookie (備用方法)
        js_code = """
        (function() {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.startsWith('loginSession=')) {
                    return cookie.substring('loginSession='.length);
                }
            }
            return '';
        })();
        """
        self.page.runJavaScript(js_code, self._on_js_cookie_result)
    
    def _on_js_cookie_result(self, result):
        """JavaScript cookie 檢查結果"""
        self._checking_cookie = False
        
        if result and not self._token:
            logger.info("Found loginSession via JS (length: %s)", len(result))
            self._extract_token_from_cookie(result)
    
    def _extract_token_from_cookie(self, cookie_value: str):
        """從 cookie 值中提取 subscriptionToken"""
        if self._token:
            return  # 已經有 token 了
        
        try:
            # URL 解碼
            decoded = urllib.parse.unquote(cookie_value)
            
            # 解析 JSON
            data = json.loads(decoded)
            
            # 提取 subscriptionToken
            token = data.get('data', {}).get('subscriptionToken')
            
            if token:
                logger.info("Token extracted successfully (length: %s)", len(token))
                self._token = token
                self._on_login_success()
            else:
                logger.warning("No subscriptionToken in cookie data")
                logger.debug("Cookie keys: %s", list(data.keys()))
                if 'data' in data:
                    logger.debug("Data keys: %s", list(data.get('data', {}).keys()))
                    
        except json.JSONDecodeError as e:
            logger.error("Failed to parse cookie JSON: %s", e)
        except Exception as e:
            logger.error("Error extracting token: %s", e)
    
    def _on_login_success(self):
        """登入成功"""
        self.status_label.setText(tr('f1tv_login_success_msg', 'Login successful!'))
        self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        
        # 發送成功信號
        self.auth_success.emit(self._token)
        
        # 延遲關閉對話框
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, self.accept)
    
    def _on_cancel(self):
        """取消登入"""
        self.auth_cancelled.emit()
        self.reject()
    
    def _get_url_display(self, url: str) -> str:
        """獲取 URL 的顯示文字 (簡化)"""
        if 'account.formula1.com' in url:
            if 'login' in url.lower():
                return "F1 Account - Login"
            return "F1 Account"
        elif 'f1tv.formula1.com' in url:
            return "F1TV"
        elif 'formula1.com' in url:
            return "Formula1.com"
        return url[:50] + "..." if len(url) > 50 else url
    
    def get_token(self) -> Optional[str]:
        """獲取已取得的 token"""
        return self._token
    
    def closeEvent(self, event):
        """關閉事件"""
        if not self._token:
            self.auth_cancelled.emit()
        
        # 正確清理 WebEngine 資源
        if hasattr(self, 'web_view') and self.web_view:
            self.web_view.setPage(None)
            self.page.deleteLater()
            self.page = None
        
        super().closeEvent(event)


def test_f1tv_web_auth():
    """測試 F1TV WebEngine 登入"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = F1TVWebAuthDialog()
    
    def on_success(token):
        logger.info("[TEST] Login success! Token length: %s", len(token))
        logger.debug("[TEST] Token preview: %s...", token[:50])
    
    def on_failed(error):
        logger.error("[TEST] Login failed: %s", error)
    
    def on_cancelled():
        logger.info("[TEST] Login cancelled")
    
    dialog.auth_success.connect(on_success)
    dialog.auth_failed.connect(on_failed)
    dialog.auth_cancelled.connect(on_cancelled)
    
    dialog.start_login()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    test_f1tv_web_auth()
