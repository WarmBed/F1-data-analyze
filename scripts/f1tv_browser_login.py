#!/usr/bin/env python3
"""
F1TV 瀏覽器登入腳本 - 使用系統預設瀏覽器

方案: 開啟系統瀏覽器登入 F1TV，然後用戶手動複製 cookie
或使用本地 HTTP 服務器接收 cookie。

使用方式:
    python scripts/f1tv_browser_login.py
"""

import json
import sys
import webbrowser
import urllib.parse
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import socket

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"

# 找到一個可用的端口
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


# 生成用於注入到 F1 頁面的 JavaScript（通過 bookmarklet）
def get_bookmarklet_code(port):
    """生成 bookmarklet 代碼"""
    js_code = f"""
    javascript:(function(){{
        var cookie = document.cookie.split(';').find(c => c.trim().startsWith('login-session='));
        if(cookie){{
            var value = cookie.split('=')[1];
            fetch('http://127.0.0.1:{port}/auth', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{cookie: value}})
            }}).then(()=>alert('Token sent! You can close this tab.')).catch(e=>alert('Error: '+e));
        }} else {{
            alert('Please login first, then run this bookmarklet again.');
        }}
    }})();
    """
    return js_code.replace('\n', '').replace('    ', '')


class AuthHandler(BaseHTTPRequestHandler):
    """處理認證回調"""
    
    token_received = None
    raw_cookie = None
    
    def log_message(self, format, *args):
        """覆蓋以抑制日誌輸出"""
        pass
    
    def do_OPTIONS(self):
        """處理 CORS 預檢"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        """處理認證數據"""
        if self.path == '/auth':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                cookie_value = data.get('cookie', '')
                if cookie_value:
                    # URL 解碼
                    decoded = urllib.parse.unquote(cookie_value)
                    parsed = json.loads(decoded)
                    token = parsed.get('data', {}).get('subscriptionToken')
                    
                    if token:
                        AuthHandler.token_received = token
                        AuthHandler.raw_cookie = cookie_value
                        print(f"\n[SUCCESS] Token received! (length: {len(token)})")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())
                
            except Exception as e:
                print(f"[ERROR] {e}")
                self.send_response(500)
                self.end_headers()
    
    def do_GET(self):
        """提供說明頁面"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>F1TV Token Extractor</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    h1 { color: #e10600; }
                    .step { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    code { background: #333; color: #0f0; padding: 10px; display: block; margin: 10px 0; word-wrap: break-word; }
                    button { background: #e10600; color: white; border: none; padding: 10px 20px; cursor: pointer; font-size: 16px; }
                    button:hover { background: #b30500; }
                    #status { margin-top: 20px; padding: 10px; }
                    .success { background: #d4edda; color: #155724; }
                    .error { background: #f8d7da; color: #721c24; }
                </style>
            </head>
            <body>
                <h1>F1TV Token Extractor</h1>
                
                <div class="step">
                    <h3>Step 1: Login to F1TV</h3>
                    <p>Click the button below to open the F1TV login page:</p>
                    <button onclick="window.open('https://account.formula1.com/#/en/login?redirect=https%3A%2F%2Ff1tv.formula1.com%2F', '_blank')">
                        Open F1TV Login
                    </button>
                </div>
                
                <div class="step">
                    <h3>Step 2: After Login</h3>
                    <p>After you've successfully logged in (you should see the F1TV homepage), 
                       come back to this page and click "Extract Token":</p>
                    <button onclick="extractToken()">Extract Token</button>
                </div>
                
                <div id="status"></div>
                
                <script>
                function extractToken() {
                    document.getElementById('status').innerHTML = '<p>Attempting to extract token...</p>';
                    
                    // Try to get cookie from F1TV (this won't work due to CORS, but we try)
                    // The user needs to manually copy the cookie
                    
                    var manualInput = prompt(
                        'Please paste your login-session cookie value here.\\n\\n' +
                        'To get it:\\n' +
                        '1. Open F1TV in a new tab\\n' +
                        '2. Press F12 to open Developer Tools\\n' +
                        '3. Go to Application > Cookies > formula1.com\\n' +
                        '4. Find "login-session" and copy its value'
                    );
                    
                    if (manualInput) {
                        fetch('/auth', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({cookie: manualInput})
                        })
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('status').innerHTML = 
                                '<p class="success">Token received! You can close this page.</p>';
                        })
                        .catch(err => {
                            document.getElementById('status').innerHTML = 
                                '<p class="error">Error: ' + err + '</p>';
                        });
                    }
                }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')


def save_token(token: str, raw_cookie: str = None):
    """保存 token"""
    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        exp = decoded.get('exp', 0)
        exp_time = datetime.fromtimestamp(exp) if exp else None
        
        AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'subscriptionToken': token,
            'formula1AccessToken': raw_cookie,
            'saved_at': datetime.now().isoformat(),
            'expires_at': exp_time.isoformat() if exp_time else None,
            'product': decoded.get('SubscribedProduct', 'Unknown'),
            'subscription_status': decoded.get('SubscriptionStatus', 'Unknown'),
        }
        
        with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] Token saved to {AUTH_DATA_FILE}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to save token: {e}")
        return False


def run_server_mode():
    """運行服務器模式"""
    port = find_free_port()
    
    print("=" * 60)
    print("F1TV Browser Login - Server Mode")
    print("=" * 60)
    print()
    print(f"Local server running on: http://127.0.0.1:{port}")
    print()
    print("Opening browser...")
    
    # 開啟本地頁面
    webbrowser.open(f"http://127.0.0.1:{port}/")
    
    print()
    print("Waiting for token...")
    print("(Press Ctrl+C to cancel)")
    print()
    
    # 啟動服務器
    server = HTTPServer(('127.0.0.1', port), AuthHandler)
    server.timeout = 300  # 5 分鐘超時
    
    try:
        while AuthHandler.token_received is None:
            server.handle_request()
        
        if AuthHandler.token_received:
            save_token(AuthHandler.token_received, AuthHandler.raw_cookie)
            print()
            print("=" * 60)
            print("[SUCCESS] Login complete!")
            print("=" * 60)
            return True
            
    except KeyboardInterrupt:
        print("\n[CANCELLED] User cancelled")
        return False
    finally:
        server.server_close()
    
    return False


def manual_token_input():
    """手動輸入 token 模式"""
    print("=" * 60)
    print("F1TV Manual Token Input")
    print("=" * 60)
    print()
    print("Instructions:")
    print("1. Open https://account.formula1.com in your browser")
    print("2. Login with your F1TV account")
    print("3. After login, open Developer Tools (F12)")
    print("4. Go to Application > Cookies > formula1.com")
    print("5. Find 'login-session' cookie")
    print("6. Copy its entire value")
    print()
    
    cookie_value = input("Paste the login-session cookie value here:\n> ")
    
    if not cookie_value:
        print("[ERROR] No value provided")
        return False
    
    try:
        # URL 解碼
        decoded = urllib.parse.unquote(cookie_value)
        data = json.loads(decoded)
        token = data.get('data', {}).get('subscriptionToken')
        
        if token:
            if save_token(token, cookie_value):
                print()
                print("=" * 60)
                print("[SUCCESS] Token extracted and saved!")
                print("=" * 60)
                return True
        else:
            print("[ERROR] No subscriptionToken found in cookie")
            return False
            
    except json.JSONDecodeError:
        print("[ERROR] Invalid cookie format")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='F1TV Browser Login')
    parser.add_argument('--manual', action='store_true', help='Manual token input mode')
    parser.add_argument('--server', action='store_true', help='Server mode (default)')
    
    args = parser.parse_args()
    
    if args.manual:
        success = manual_token_input()
    else:
        success = run_server_mode()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
