#!/usr/bin/env python3
"""
F1TV WebView2 認證模組

使用 pywebview (Edge WebView2) 進行 F1TV 登入，
這是 Windows 上最接近真實瀏覽器的方案。

優點:
- 使用真正的 Edge WebView2 渲染引擎
- 不會被網站偵測為非標準瀏覽器
- 完整的 cookie 存取能力
- Windows 10/11 已預裝 Edge WebView2 Runtime
"""

import json
import threading
import urllib.parse
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

# F1TV 登入相關 URL
F1_LOGIN_URL = "https://account.formula1.com/#/en/login?redirect=https%3A%2F%2Ff1tv.formula1.com%2F"
F1TV_URL = "https://f1tv.formula1.com"

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"


class F1TVWebViewAuth:
    """
    F1TV WebView2 認證管理器
    
    使用 pywebview 開啟真正的 Edge 瀏覽器視窗進行登入，
    登入成功後自動抓取 loginSession cookie 中的 subscriptionToken。
    """
    
    def __init__(self):
        self._token: Optional[str] = None
        self._window = None
        self._success_callback: Optional[Callable[[str], None]] = None
        self._failed_callback: Optional[Callable[[str], None]] = None
        self._cancelled_callback: Optional[Callable[[], None]] = None
        self._check_interval_ms = 2000  # 每 2 秒檢查一次
        self._checking = False
    
    def start_auth(
        self,
        on_success: Optional[Callable[[str], None]] = None,
        on_failed: Optional[Callable[[str], None]] = None,
        on_cancelled: Optional[Callable[[], None]] = None
    ):
        """
        啟動認證流程
        
        Args:
            on_success: 認證成功回調，參數為 token
            on_failed: 認證失敗回調，參數為錯誤訊息
            on_cancelled: 認證取消回調
        
        ⚠️ 注意：pywebview.start() 必須在主執行緒中運行
        此方法會阻塞直到用戶完成登入或關閉視窗
        """
        self._success_callback = on_success
        self._failed_callback = on_failed
        self._cancelled_callback = on_cancelled
        
        # 直接在主執行緒執行（pywebview 要求）
        self._run_webview()
    
    def _run_webview(self):
        """在獨立執行緒中執行 webview"""
        try:
            import webview
            
            print("[F1TV_WEBVIEW] Starting Edge WebView2 authentication...")
            
            # 創建 webview 視窗
            self._window = webview.create_window(
                title='F1TV Login - Please login with your F1TV account',
                url=F1_LOGIN_URL,
                width=1000,
                height=750,
                resizable=True,
                text_select=True,
                confirm_close=False
            )
            
            # 設置事件處理
            self._window.events.loaded += self._on_page_loaded
            self._window.events.closing += self._on_window_closing
            
            # 啟動 webview（這會阻塞直到視窗關閉）
            webview.start(
                self._start_cookie_check,
                private_mode=False,  # 使用正常模式以保留 cookies
                debug=False
            )
            
            print("[F1TV_WEBVIEW] WebView window closed")
            
            # 視窗關閉後，如果沒有獲取到 token，視為取消
            if not self._token:
                if self._cancelled_callback:
                    self._cancelled_callback()
                    
        except ImportError as e:
            error_msg = f"pywebview not installed: {e}"
            print(f"[F1TV_WEBVIEW] Error: {error_msg}")
            if self._failed_callback:
                self._failed_callback(error_msg)
        except Exception as e:
            error_msg = f"WebView error: {e}"
            print(f"[F1TV_WEBVIEW] Error: {error_msg}")
            if self._failed_callback:
                self._failed_callback(error_msg)
    
    def _start_cookie_check(self):
        """開始定期檢查 cookie"""
        import time
        
        self._checking = True
        print("[F1TV_WEBVIEW] Starting cookie check loop...")
        
        while self._checking and self._window:
            try:
                self._check_cookies()
                if self._token:
                    print("[F1TV_WEBVIEW] Token obtained, closing window...")
                    self._checking = False
                    # 延遲關閉以顯示成功訊息
                    time.sleep(1)
                    if self._window:
                        self._window.destroy()
                    break
                time.sleep(self._check_interval_ms / 1000)
            except Exception as e:
                print(f"[F1TV_WEBVIEW] Cookie check error: {e}")
                time.sleep(self._check_interval_ms / 1000)
    
    def _on_page_loaded(self):
        """頁面載入完成"""
        if self._window:
            url = self._window.get_current_url()
            print(f"[F1TV_WEBVIEW] Page loaded: {url}")
            
            # 如果跳轉到 F1TV 首頁，表示登入成功
            if 'f1tv.formula1.com' in url and 'login' not in url.lower():
                print("[F1TV_WEBVIEW] Redirected to F1TV, checking cookies...")
                self._check_cookies()
    
    def _on_window_closing(self):
        """視窗正在關閉"""
        print("[F1TV_WEBVIEW] Window closing...")
        self._checking = False
    
    def _check_cookies(self):
        """檢查是否有 loginSession cookie"""
        if not self._window or self._token:
            return
        
        try:
            # 使用 JavaScript 獲取所有 cookies
            js_code = """
            (function() {
                var cookies = document.cookie.split(';');
                var result = {};
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    var eqPos = cookie.indexOf('=');
                    if (eqPos > 0) {
                        var name = cookie.substring(0, eqPos);
                        var value = cookie.substring(eqPos + 1);
                        result[name] = value;
                    }
                }
                return JSON.stringify(result);
            })();
            """
            
            result = self._window.evaluate_js(js_code)
            
            if result:
                cookies = json.loads(result)
                
                # 檢查 login-session (注意：有連字符，不是 loginSession)
                # F1TV 在 2024 年後改用 'login-session' 作為 cookie 名稱
                login_session_key = 'login-session'
                if login_session_key in cookies:
                    login_session = cookies[login_session_key]
                    print(f"[F1TV_WEBVIEW] Found {login_session_key} cookie (length: {len(login_session)})")
                    self._extract_token(login_session)
                    
        except Exception as e:
            print(f"[F1TV_WEBVIEW] Error checking cookies: {e}")
    
    def _extract_token(self, cookie_value: str):
        """從 loginSession cookie 中提取 subscriptionToken"""
        try:
            # URL 解碼
            decoded = urllib.parse.unquote(cookie_value)
            
            # 解析 JSON
            data = json.loads(decoded)
            
            # 提取 subscriptionToken
            token = data.get('data', {}).get('subscriptionToken')
            
            if token:
                print(f"[F1TV_WEBVIEW] Extracted subscriptionToken (length: {len(token)})")
                self._token = token
                
                # 儲存 token
                self._save_token(token)
                
                # 觸發成功回調
                if self._success_callback:
                    self._success_callback(token)
            else:
                print("[F1TV_WEBVIEW] No subscriptionToken in cookie data")
                print(f"[F1TV_WEBVIEW] Cookie keys: {list(data.keys())}")
                if 'data' in data:
                    print(f"[F1TV_WEBVIEW] Data keys: {list(data.get('data', {}).keys())}")
                    
        except json.JSONDecodeError as e:
            print(f"[F1TV_WEBVIEW] Failed to parse cookie JSON: {e}")
        except Exception as e:
            print(f"[F1TV_WEBVIEW] Error extracting token: {e}")
    
    def _save_token(self, token: str):
        """儲存 token 到檔案"""
        try:
            AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # 儲存為 JSON 格式
            data = {
                'subscriptionToken': token,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"[F1TV_WEBVIEW] Token saved to {AUTH_DATA_FILE}")
            
        except Exception as e:
            print(f"[F1TV_WEBVIEW] Failed to save token: {e}")
    
    def get_token(self) -> Optional[str]:
        """獲取已存儲的 token"""
        if self._token:
            return self._token
        
        # 嘗試從檔案載入
        return self.load_saved_token()
    
    @staticmethod
    def load_saved_token() -> Optional[str]:
        """從檔案載入已存儲的 token"""
        if not AUTH_DATA_FILE.exists():
            return None
        
        try:
            with open(AUTH_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            token = data.get('subscriptionToken')
            
            if token and F1TVWebViewAuth.verify_token(token):
                return token
            else:
                print("[F1TV_WEBVIEW] Saved token is expired or invalid")
                return None
                
        except Exception as e:
            print(f"[F1TV_WEBVIEW] Failed to load saved token: {e}")
            return None
    
    @staticmethod
    def verify_token(token: str) -> bool:
        """驗證 token 是否有效（檢查過期時間）"""
        try:
            import jwt
            
            # 解碼但不驗證簽名（只檢查過期時間）
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get('exp', 0)
            
            is_valid = exp > datetime.now().timestamp()
            
            if is_valid:
                exp_time = datetime.fromtimestamp(exp)
                print(f"[F1TV_WEBVIEW] Token valid until: {exp_time}")
            else:
                print("[F1TV_WEBVIEW] Token has expired")
            
            return is_valid
            
        except Exception as e:
            print(f"[F1TV_WEBVIEW] Token verification error: {e}")
            return False
    
    @staticmethod
    def clear_saved_token():
        """清除已存儲的 token"""
        if AUTH_DATA_FILE.exists():
            AUTH_DATA_FILE.unlink()
            print("[F1TV_WEBVIEW] Saved token cleared")
    
    @staticmethod
    def get_token_info(token: str) -> dict:
        """獲取 token 的詳細資訊"""
        try:
            import jwt
            
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            exp = decoded.get('exp', 0)
            exp_time = datetime.fromtimestamp(exp) if exp else None
            
            return {
                'subscription_status': decoded.get('SubscriptionStatus', 'Unknown'),
                'subscribed_product': decoded.get('SubscribedProduct', 'Unknown'),
                'expires_at': exp_time.isoformat() if exp_time else None,
                'is_valid': exp > datetime.now().timestamp() if exp else False
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'is_valid': False
            }


def test_webview_auth():
    """測試 WebView2 認證"""
    import webview
    
    print("=" * 60)
    print("F1TV WebView2 Authentication Test")
    print("=" * 60)
    
    token_result = {'token': None}
    
    def check_cookies(window):
        """定期檢查 cookies"""
        import time
        
        print("[TEST] Starting cookie check loop...")
        
        while True:
            try:
                url = window.get_current_url()
                print(f"[TEST] Current URL: {url}")
                
                # 使用 JavaScript 獲取 cookies
                js_code = """
                (function() {
                    var cookies = document.cookie.split(';');
                    var result = {};
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = cookies[i].trim();
                        var eqPos = cookie.indexOf('=');
                        if (eqPos > 0) {
                            var name = cookie.substring(0, eqPos);
                            var value = cookie.substring(eqPos + 1);
                            result[name] = value;
                        }
                    }
                    return JSON.stringify(result);
                })();
                """
                
                result = window.evaluate_js(js_code)
                
                if result:
                    cookies = json.loads(result)
                    print(f"[TEST] Cookies found: {list(cookies.keys())}")
                    
                    # 檢查 login-session (注意：有連字符，不是 loginSession)
                    login_session_key = 'login-session'
                    if login_session_key in cookies:
                        login_session = cookies[login_session_key]
                        print(f"[TEST] Found {login_session_key}! Length: {len(login_session)}")
                        
                        # 解析 token
                        try:
                            decoded = urllib.parse.unquote(login_session)
                            data = json.loads(decoded)
                            token = data.get('data', {}).get('subscriptionToken')
                            
                            if token:
                                print(f"[TEST] SUCCESS! Token extracted (length: {len(token)})")
                                token_result['token'] = token
                                
                                # 儲存 token
                                AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
                                save_data = {
                                    'subscriptionToken': token,
                                    'saved_at': datetime.now().isoformat()
                                }
                                with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
                                    json.dump(save_data, f, indent=2)
                                print(f"[TEST] Token saved to {AUTH_DATA_FILE}")
                                
                                # 關閉視窗
                                time.sleep(1)
                                window.destroy()
                                return
                            else:
                                print(f"[TEST] No subscriptionToken in data. Keys: {list(data.keys())}")
                                if 'data' in data:
                                    print(f"[TEST] data.data keys: {list(data.get('data', {}).keys())}")
                        except Exception as e:
                            print(f"[TEST] Error parsing token: {e}")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"[TEST] Check error: {e}")
                time.sleep(2)
    
    print("\nStarting authentication...")
    print("A browser window will open. Please login with your F1TV account.\n")
    
    # 創建 webview 視窗
    window = webview.create_window(
        title='F1TV Login - Please login with your F1TV account',
        url=F1_LOGIN_URL,
        width=1000,
        height=750,
        resizable=True,
        text_select=True
    )
    
    # 啟動 webview（在主執行緒）
    webview.start(check_cookies, window, private_mode=False, debug=False)
    
    print("\n" + "=" * 60)
    if token_result['token']:
        print("Authentication successful!")
        print(f"Token: {token_result['token'][:50]}...")
    else:
        print("Authentication cancelled or failed")
    print("=" * 60)


if __name__ == '__main__':
    test_webview_auth()
