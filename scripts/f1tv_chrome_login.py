#!/usr/bin/env python3
"""
F1TV Chrome Profile 登入

模仿 MultiViewer 的 Chrome Profile 登入方式：
1. 啟動系統 Chrome/Edge，使用獨立的 profile 目錄
2. 用戶在真正的瀏覽器中登入（不會被偵測）
3. 登入後從 profile 的 cookies 中讀取 login-session

這是最可靠的登入方式，因為使用的是真正的瀏覽器。
"""

import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# F1TV URLs
F1_LOGIN_URL = "https://account.formula1.com/#/en/login?redirect=https%3A%2F%2Ff1tv.formula1.com%2F"
F1TV_URL = "https://f1tv.formula1.com"

# 獨立的 Chrome profile 目錄
CHROME_PROFILE_DIR = Path.home() / ".f1t" / "chrome_profile"

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"


def find_browser() -> Tuple[Optional[Path], str]:
    """尋找系統安裝的 Chrome 或 Edge"""
    
    # 常見的 Chrome 路徑
    chrome_paths = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    ]
    
    # 常見的 Edge 路徑
    edge_paths = [
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ]
    
    # 優先使用 Chrome
    for path in chrome_paths:
        if path.exists():
            return path, "chrome"
    
    # 其次使用 Edge
    for path in edge_paths:
        if path.exists():
            return path, "edge"
    
    return None, ""


def launch_browser_for_login():
    """啟動瀏覽器進行登入"""
    
    browser_path, browser_type = find_browser()
    
    if not browser_path:
        print("Error: Cannot find Chrome or Edge browser!")
        print("Please install Google Chrome or Microsoft Edge.")
        return False
    
    print(f"Found browser: {browser_type} at {browser_path}")
    
    # 確保 profile 目錄存在
    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 啟動瀏覽器參數
    args = [
        str(browser_path),
        f"--user-data-dir={CHROME_PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        F1_LOGIN_URL
    ]
    
    print("\n" + "=" * 60)
    print("F1TV Chrome Profile Login")
    print("=" * 60)
    print(f"\nLaunching {browser_type.upper()} with isolated profile...")
    print(f"Profile directory: {CHROME_PROFILE_DIR}")
    print("\nPlease login with your F1TV account in the browser window.")
    print("After successful login, close the browser window.")
    print("=" * 60 + "\n")
    
    # 啟動瀏覽器並等待它關閉
    try:
        process = subprocess.Popen(args)
        process.wait()  # 等待瀏覽器關閉
        print("\nBrowser closed. Checking for login session...")
        return True
    except Exception as e:
        print(f"Error launching browser: {e}")
        return False


def read_cookies_from_profile() -> Optional[str]:
    """從 Chrome profile 讀取 cookies"""
    
    # Chrome/Edge cookies 資料庫路徑
    cookies_db = CHROME_PROFILE_DIR / "Default" / "Network" / "Cookies"
    
    if not cookies_db.exists():
        # 舊版路徑
        cookies_db = CHROME_PROFILE_DIR / "Default" / "Cookies"
    
    if not cookies_db.exists():
        print(f"Cookies database not found: {cookies_db}")
        return None
    
    print(f"Reading cookies from: {cookies_db}")
    
    try:
        # 複製資料庫（因為可能被鎖定）
        import shutil
        temp_db = CHROME_PROFILE_DIR / "cookies_temp.db"
        shutil.copy2(cookies_db, temp_db)
        
        # 連接資料庫
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        
        # 查詢 F1 相關的 cookies
        cursor.execute("""
            SELECT name, value, host_key, encrypted_value 
            FROM cookies 
            WHERE host_key LIKE '%formula1%' OR host_key LIKE '%f1tv%'
        """)
        
        cookies = cursor.fetchall()
        conn.close()
        
        # 清理臨時檔案
        temp_db.unlink()
        
        print(f"Found {len(cookies)} F1-related cookies")
        
        for name, value, host, encrypted_value in cookies:
            print(f"  - {name} @ {host} (value length: {len(value) if value else 'encrypted'})")
            
            if name == "login-session" and value:
                return value
            elif name == "login-session" and encrypted_value:
                # Chrome 80+ 加密了 cookies，需要解密
                decrypted = decrypt_chrome_cookie(encrypted_value)
                if decrypted:
                    return decrypted
        
        return None
        
    except Exception as e:
        print(f"Error reading cookies: {e}")
        return None


def decrypt_chrome_cookie(encrypted_value: bytes) -> Optional[str]:
    """解密 Chrome 加密的 cookie（Windows）"""
    try:
        import base64
        import win32crypt
        from Crypto.Cipher import AES
        
        # Chrome 80+ 使用 v10/v11 前綴的 AES-GCM 加密
        if encrypted_value[:3] == b'v10' or encrypted_value[:3] == b'v11':
            # 需要從 Local State 讀取密鑰
            local_state_path = CHROME_PROFILE_DIR / "Local State"
            
            if not local_state_path.exists():
                print("Local State not found, cannot decrypt cookies")
                return None
            
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            # 獲取加密密鑰
            encrypted_key = local_state['os_crypt']['encrypted_key']
            encrypted_key = base64.b64decode(encrypted_key)
            encrypted_key = encrypted_key[5:]  # 移除 'DPAPI' 前綴
            
            # 使用 DPAPI 解密密鑰
            key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            
            # 解密 cookie - Chrome 使用 AES-256-GCM
            # 格式: v10/v11 (3 bytes) + nonce (12 bytes) + ciphertext + tag (16 bytes)
            nonce = encrypted_value[3:15]
            ciphertext_with_tag = encrypted_value[15:]
            
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            decrypted = cipher.decrypt_and_verify(ciphertext_with_tag[:-16], ciphertext_with_tag[-16:])
            
            return decrypted.decode('utf-8')
        else:
            # 舊版 DPAPI 加密（Chrome 80 之前）
            decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1]
            return decrypted.decode('utf-8')
            
    except ImportError as e:
        print(f"Note: pywin32 and pycryptodome are required for cookie decryption: {e}")
        print("Install with: pip install pywin32 pycryptodome")
        return None
    except ValueError as e:
        # MAC 驗證失敗，嘗試不驗證的方式
        print(f"MAC verification failed, trying without verification: {e}")
        try:
            import base64
            import win32crypt
            from Crypto.Cipher import AES
            
            local_state_path = CHROME_PROFILE_DIR / "Local State"
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            encrypted_key = local_state['os_crypt']['encrypted_key']
            encrypted_key = base64.b64decode(encrypted_key)
            encrypted_key = encrypted_key[5:]
            key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            
            nonce = encrypted_value[3:15]
            ciphertext = encrypted_value[15:]
            
            # 只解密不驗證（某些情況下 tag 位置不同）
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            decrypted = cipher.decrypt(ciphertext)
            
            # 嘗試找到有效的 JSON 結尾
            try:
                # 尋找最後一個 } 的位置
                text = decrypted.decode('utf-8', errors='ignore')
                last_brace = text.rfind('}')
                if last_brace > 0:
                    return text[:last_brace + 1]
            except:
                pass
            
            return decrypted.decode('utf-8', errors='ignore')
        except Exception as e2:
            print(f"Fallback decryption also failed: {e2}")
            return None
    except Exception as e:
        print(f"Cookie decryption error: {e}")
        return None


def extract_token_from_cookie(cookie_value: str) -> Optional[str]:
    """從 login-session cookie 提取 subscriptionToken"""
    try:
        # 調試輸出
        print(f"Cookie value preview: {cookie_value[:200] if len(cookie_value) > 200 else cookie_value}...")
        print(f"Cookie value length: {len(cookie_value)}")
        
        # URL 解碼
        decoded = urllib.parse.unquote(cookie_value)
        print(f"Decoded preview: {decoded[:200] if len(decoded) > 200 else decoded}...")
        
        # 解析 JSON
        data = json.loads(decoded)
        
        # 提取 subscriptionToken
        token = data.get('data', {}).get('subscriptionToken')
        
        if token:
            print(f"Successfully extracted subscriptionToken (length: {len(token)})")
            return token
        else:
            print("No subscriptionToken found in cookie data")
            print(f"Available keys: {list(data.keys())}")
            if 'data' in data:
                print(f"Data keys: {list(data.get('data', {}).keys())}")
            return None
            
    except json.JSONDecodeError as e:
        print(f"Failed to parse cookie JSON: {e}")
        print(f"Raw cookie for manual inspection: {cookie_value[:500]}")
        return None
    except Exception as e:
        print(f"Error extracting token: {e}")
        return None


def save_token(token: str):
    """儲存 token"""
    AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'subscriptionToken': token,
        'saved_at': datetime.now().isoformat(),
        'source': 'chrome_profile'
    }
    
    with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Token saved to {AUTH_DATA_FILE}")


def main():
    """主程式"""
    import base64  # 確保 import 在這裡
    
    print("\n" + "=" * 60)
    print("F1TV Chrome Profile Authentication")
    print("=" * 60)
    
    # 1. 啟動瀏覽器
    if not launch_browser_for_login():
        return 1
    
    # 2. 讀取 cookies
    cookie_value = read_cookies_from_profile()
    
    if not cookie_value:
        print("\nFailed to read login-session cookie.")
        print("This might be because:")
        print("  1. You didn't login successfully")
        print("  2. The cookies are encrypted (need pywin32 + pycryptodome)")
        print("\nAlternative: Use the JavaScript console method")
        return 1
    
    # 3. 提取 token
    token = extract_token_from_cookie(cookie_value)
    
    if not token:
        print("\nFailed to extract token from cookie.")
        return 1
    
    # 4. 儲存 token
    save_token(token)
    
    print("\n" + "=" * 60)
    print("SUCCESS! F1TV authentication completed.")
    print(f"Token saved to: {AUTH_DATA_FILE}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    import base64
    sys.exit(main())
