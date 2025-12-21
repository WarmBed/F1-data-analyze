#!/usr/bin/env python3
"""
F1TV 獨立登入腳本

此腳本作為獨立進程運行，使用 pywebview (Edge WebView2) 進行 F1TV 登入。
參考 undercut-f1 的實現方式，避免與 PyQt5 GUI 產生衝突。

使用方式:
    python scripts/f1tv_login.py
    
成功後 token 會保存到 ~/.f1t/f1auth.json
"""

import json
import sys
import urllib.parse
from pathlib import Path
from datetime import datetime

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"

# F1TV 登入 URL
F1_LOGIN_URL = "https://account.formula1.com/#/en/login?redirect=https%3A%2F%2Ff1tv.formula1.com%2F"


def get_init_script():
    """
    獲取注入到 WebView 的 JavaScript 腳本
    參考 undercut-f1 的 GetInitScript() 方法
    """
    return """
    function getCookie(name) {
        return (name = (document.cookie + ';').match(new RegExp(name + '=.*;'))) && name[0].split(/=|;/)[1];
    }
    
    var previousCookie = "";
    setInterval(() => {
        let cookie = getCookie('login-session');
        if (cookie && previousCookie !== cookie) {
            // 通知 Python 端
            window.pywebview.api.on_cookie_found(cookie);
            previousCookie = cookie;
        }
    }, 1000);
    """


class F1TVLoginAPI:
    """暴露給 JavaScript 的 API"""
    
    def __init__(self, window_ref):
        self._window_ref = window_ref
        self.token = None
        self.raw_cookie = None
    
    def on_cookie_found(self, cookie_value):
        """當找到 login-session cookie 時調用"""
        print(f"[F1TV Login] Found login-session cookie (length: {len(cookie_value)})")
        
        try:
            # URL 解碼
            decoded = urllib.parse.unquote(cookie_value)
            data = json.loads(decoded)
            
            # 提取 subscriptionToken
            token = data.get('data', {}).get('subscriptionToken')
            
            if token:
                print(f"[F1TV Login] SUCCESS! Token extracted (length: {len(token)})")
                self.token = token
                self.raw_cookie = cookie_value
                
                # 保存 token
                save_token(token, cookie_value)
                
                # 延遲關閉視窗
                import time
                time.sleep(1)
                
                if self._window_ref:
                    self._window_ref[0].destroy()
            else:
                print("[F1TV Login] No subscriptionToken in cookie data")
                
        except Exception as e:
            print(f"[F1TV Login] Error parsing cookie: {e}")


def save_token(token: str, raw_cookie: str = None):
    """保存 token 到檔案"""
    try:
        AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # 獲取 token 資訊
        token_info = get_token_info(token)
        
        data = {
            'subscriptionToken': token,
            'formula1AccessToken': raw_cookie,  # 與 undercut-f1 兼容
            'saved_at': datetime.now().isoformat(),
            'expires_at': token_info.get('expires_at'),
            'product': token_info.get('subscribed_product'),
            'subscription_status': token_info.get('subscription_status'),
        }
        
        with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[F1TV Login] Token saved to {AUTH_DATA_FILE}")
        
    except Exception as e:
        print(f"[F1TV Login] Failed to save token: {e}")


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


def run_login():
    """運行登入流程"""
    try:
        import webview
    except ImportError:
        print("[F1TV Login] ERROR: pywebview not installed")
        print("[F1TV Login] Please install with: pip install pywebview")
        sys.exit(1)
    
    print("=" * 60)
    print("F1TV Login - Edge WebView2")
    print("=" * 60)
    print()
    print("A browser window will open.")
    print("Please login with your F1TV account.")
    print("The window will close automatically after successful login.")
    print()
    
    # 用於保存視窗引用
    window_ref = [None]
    
    # 創建 API 實例
    api = F1TVLoginAPI(window_ref)
    
    # 創建 webview 視窗
    window = webview.create_window(
        title='F1TV Login - Please login with your F1TV account',
        url=F1_LOGIN_URL,
        width=1000,
        height=750,
        resizable=True,
        text_select=True,
        js_api=api
    )
    window_ref[0] = window
    
    def on_loaded():
        """頁面載入完成時注入腳本"""
        if window:
            window.evaluate_js(get_init_script())
    
    window.events.loaded += on_loaded
    
    # 啟動 webview（阻塞直到視窗關閉）
    webview.start(private_mode=False, debug=False)
    
    print()
    print("=" * 60)
    if api.token:
        print("[F1TV Login] Login successful!")
        print(f"[F1TV Login] Token saved to: {AUTH_DATA_FILE}")
        
        # 顯示 token 資訊
        info = get_token_info(api.token)
        print(f"[F1TV Login] Product: {info.get('subscribed_product', 'Unknown')}")
        print(f"[F1TV Login] Expires: {info.get('expires_at', 'Unknown')}")
        
        sys.exit(0)
    else:
        print("[F1TV Login] Login cancelled or failed")
        sys.exit(1)


def check_existing_token():
    """檢查是否有有效的 token"""
    if not AUTH_DATA_FILE.exists():
        return None
    
    try:
        with open(AUTH_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        token = data.get('subscriptionToken')
        if not token:
            return None
        
        info = get_token_info(token)
        if info.get('is_valid'):
            return {
                'token': token,
                'info': info
            }
        else:
            print("[F1TV Login] Existing token has expired")
            return None
            
    except Exception as e:
        print(f"[F1TV Login] Error reading token: {e}")
        return None


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='F1TV Login Tool')
    parser.add_argument('--check', action='store_true', help='Check existing token')
    parser.add_argument('--clear', action='store_true', help='Clear existing token')
    parser.add_argument('--info', action='store_true', help='Show token info')
    
    args = parser.parse_args()
    
    if args.clear:
        if AUTH_DATA_FILE.exists():
            AUTH_DATA_FILE.unlink()
            print(f"[F1TV Login] Token cleared: {AUTH_DATA_FILE}")
        else:
            print("[F1TV Login] No token to clear")
        return
    
    if args.check or args.info:
        existing = check_existing_token()
        if existing:
            print("[F1TV Login] Valid token found")
            info = existing['info']
            print(f"  Product: {info.get('subscribed_product', 'Unknown')}")
            print(f"  Status: {info.get('subscription_status', 'Unknown')}")
            print(f"  Expires: {info.get('expires_at', 'Unknown')}")
        else:
            print("[F1TV Login] No valid token found")
        return
    
    # 檢查是否已有有效 token
    existing = check_existing_token()
    if existing:
        print("[F1TV Login] You already have a valid token.")
        info = existing['info']
        print(f"  Product: {info.get('subscribed_product', 'Unknown')}")
        print(f"  Expires: {info.get('expires_at', 'Unknown')}")
        print()
        
        response = input("Do you want to re-login? (y/N): ")
        if response.lower() != 'y':
            print("[F1TV Login] Keeping existing token")
            return
    
    # 運行登入
    run_login()


if __name__ == '__main__':
    main()
