#!/usr/bin/env python3
"""
F1TV Cookie 直接提取工具

在瀏覽器中執行 JavaScript 獲取 cookie，不需要解密本地資料庫。
"""

import json
import subprocess
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"
CHROME_PROFILE_DIR = Path.home() / ".f1t" / "chrome_profile"


def find_browser():
    """尋找瀏覽器"""
    import os
    
    paths = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ]
    
    for path in paths:
        if path.exists():
            return path
    return None


def main():
    print("\n" + "=" * 70)
    print("F1TV Cookie 提取工具")
    print("=" * 70)
    
    # 建立一個 HTML 頁面來提取和顯示 cookie
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>F1TV Token Extractor</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #1a1a2e; color: #eee; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #e10600; }
        .token-box { 
            background: #16213e; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            word-break: break-all;
            font-family: monospace;
            font-size: 12px;
        }
        .success { color: #00ff00; }
        .error { color: #ff6b6b; }
        button {
            background: #e10600;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
        }
        button:hover { background: #ff1a1a; }
        #status { margin: 20px 0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>F1TV Token Extractor</h1>
        <div id="status">Checking login status...</div>
        <div id="token-display"></div>
        <div id="actions" style="display:none;">
            <button onclick="copyToken()">Copy Token</button>
            <button onclick="window.close()">Close</button>
        </div>
    </div>
    <script>
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }
        
        function extractToken() {
            const loginSession = getCookie('login-session');
            const statusDiv = document.getElementById('status');
            const tokenDiv = document.getElementById('token-display');
            const actionsDiv = document.getElementById('actions');
            
            if (!loginSession) {
                statusDiv.innerHTML = '<span class="error">Not logged in. Please login first at <a href="https://f1tv.formula1.com" style="color:#e10600">f1tv.formula1.com</a></span>';
                return;
            }
            
            try {
                const decoded = decodeURIComponent(loginSession);
                const data = JSON.parse(decoded);
                const token = data.data?.subscriptionToken;
                
                if (token) {
                    statusDiv.innerHTML = '<span class="success">✓ Token extracted successfully!</span>';
                    tokenDiv.innerHTML = `
                        <h3>Subscription Token:</h3>
                        <div class="token-box" id="token-value">${token}</div>
                        <p>Token length: ${token.length} characters</p>
                    `;
                    actionsDiv.style.display = 'block';
                    
                    // 也顯示在控制台
                    console.log('='.repeat(60));
                    console.log('F1TV_TOKEN_START');
                    console.log(token);
                    console.log('F1TV_TOKEN_END');
                    console.log('='.repeat(60));
                    
                    // 存到 localStorage 方便讀取
                    localStorage.setItem('f1tv_token', token);
                } else {
                    statusDiv.innerHTML = '<span class="error">Token not found in cookie data</span>';
                    tokenDiv.innerHTML = `<div class="token-box">Cookie data: ${JSON.stringify(data, null, 2)}</div>`;
                }
            } catch (e) {
                statusDiv.innerHTML = `<span class="error">Error parsing cookie: ${e.message}</span>`;
                tokenDiv.innerHTML = `<div class="token-box">Raw cookie: ${loginSession.substring(0, 500)}...</div>`;
            }
        }
        
        function copyToken() {
            const token = document.getElementById('token-value')?.innerText;
            if (token) {
                navigator.clipboard.writeText(token).then(() => {
                    alert('Token copied to clipboard!');
                });
            }
        }
        
        // 自動執行
        setTimeout(extractToken, 500);
    </script>
</body>
</html>'''
    
    # 保存 HTML 檔案
    html_file = Path.home() / ".f1t" / "token_extractor.html"
    html_file.parent.mkdir(parents=True, exist_ok=True)
    html_file.write_text(html_content, encoding='utf-8')
    
    browser = find_browser()
    if not browser:
        print("Error: No browser found!")
        return 1
    
    print(f"\n使用瀏覽器: {browser}")
    print("\n步驟:")
    print("1. 瀏覽器會開啟 F1TV 網站")
    print("2. 如果已登入，會自動跳轉到 Token 提取頁面")
    print("3. 複製顯示的 Token")
    print("4. 關閉瀏覽器後，將 Token 貼到這裡\n")
    
    # 創建一個會自動導航的頁面
    redirect_html = '''<!DOCTYPE html>
<html>
<head>
    <title>F1TV Token Extractor</title>
    <script>
        // 先檢查是否已登入
        function checkAndRedirect() {
            const loginSession = document.cookie.split(';').find(c => c.trim().startsWith('login-session='));
            if (loginSession) {
                // 已登入，提取 token
                extractAndShow();
            } else {
                // 未登入，顯示提示
                document.body.innerHTML = '<h1>Please login first</h1><p>Redirecting to F1TV login...</p>';
                setTimeout(() => {
                    window.location.href = 'https://account.formula1.com/#/en/login?redirect=https%3A%2F%2Ff1tv.formula1.com%2F';
                }, 2000);
            }
        }
        
        function extractAndShow() {
            const loginSession = document.cookie.split(';').find(c => c.trim().startsWith('login-session='));
            if (loginSession) {
                const value = loginSession.split('=').slice(1).join('=');
                try {
                    const decoded = decodeURIComponent(value);
                    const data = JSON.parse(decoded);
                    const token = data.data?.subscriptionToken;
                    if (token) {
                        document.body.innerHTML = `
                            <div style="font-family:Arial;padding:20px;background:#1a1a2e;color:#eee;min-height:100vh;">
                                <h1 style="color:#e10600;">✓ Token Extracted!</h1>
                                <p>Copy the token below:</p>
                                <textarea id="token" style="width:100%;height:200px;background:#16213e;color:#0f0;border:none;padding:10px;font-family:monospace;">${token}</textarea>
                                <br><br>
                                <button onclick="navigator.clipboard.writeText(document.getElementById('token').value);alert('Copied!')" 
                                        style="background:#e10600;color:white;border:none;padding:10px 20px;cursor:pointer;">
                                    Copy Token
                                </button>
                                <p style="margin-top:20px;color:#888;">After copying, close this window and paste the token.</p>
                            </div>
                        `;
                    }
                } catch(e) {
                    document.body.innerHTML = '<h1>Error: ' + e.message + '</h1>';
                }
            }
        }
        
        // 等待頁面載入
        if (document.readyState === 'complete') {
            checkAndRedirect();
        } else {
            window.onload = checkAndRedirect;
        }
    </script>
</head>
<body style="font-family:Arial;padding:20px;background:#1a1a2e;color:#eee;">
    <h1>Loading...</h1>
</body>
</html>'''
    
    # F1TV 頁面上執行的 bookmarklet
    print("=" * 70)
    print("方法: 在 F1TV 頁面執行 JavaScript")
    print("=" * 70)
    print("\n1. 瀏覽器會開啟 F1TV")
    print("2. 確認已登入後，按 F12 開啟開發者工具")
    print("3. 切換到 Console 分頁")
    print("4. 貼上以下程式碼並按 Enter:\n")
    
    js_code = '''(function(){var c=document.cookie.split(';').find(x=>x.trim().startsWith('login-session='));if(c){var v=c.split('=').slice(1).join('=');var d=JSON.parse(decodeURIComponent(v));var t=d.data?.subscriptionToken;if(t){console.log('TOKEN:',t);prompt('Copy this token:',t);}else{alert('No token found');}}else{alert('Not logged in');}})();'''
    
    print(js_code)
    print("\n" + "=" * 70)
    
    # 啟動瀏覽器
    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    args = [
        str(browser),
        f"--user-data-dir={CHROME_PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://f1tv.formula1.com"
    ]
    
    subprocess.Popen(args)
    
    print("\n瀏覽器已開啟。請在 Console 執行上面的 JavaScript 程式碼。")
    print("複製 Token 後，貼到下面：\n")
    
    token = input("請貼上 Token (或按 Enter 取消): ").strip()
    
    if token:
        # 驗證 token 格式
        if len(token) > 100 and '.' in token:
            # 儲存 token
            AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'subscriptionToken': token,
                'saved_at': datetime.now().isoformat(),
                'source': 'manual_js_extract'
            }
            with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"\n✓ Token 已儲存到 {AUTH_DATA_FILE}")
            print("認證完成！")
            return 0
        else:
            print("Token 格式不正確，請確認複製完整。")
            return 1
    else:
        print("已取消。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
