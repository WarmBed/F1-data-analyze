#!/usr/bin/env python3
"""
F1TV Chrome Cookie 解密器

直接從 Chrome Profile 解密讀取 login-session cookie。
"""

import base64
import json
import os
import shutil
import sqlite3
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Chrome profile 目錄
CHROME_PROFILE_DIR = Path.home() / ".f1t" / "chrome_profile"

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"


def get_chrome_encryption_key() -> Optional[bytes]:
    """從 Chrome Local State 獲取加密密鑰"""
    local_state_path = CHROME_PROFILE_DIR / "Local State"
    
    if not local_state_path.exists():
        print(f"[ERROR] Local State not found: {local_state_path}")
        return None
    
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        
        # 獲取加密的密鑰
        encrypted_key_b64 = local_state['os_crypt']['encrypted_key']
        encrypted_key = base64.b64decode(encrypted_key_b64)
        
        # 移除 'DPAPI' 前綴 (5 bytes)
        encrypted_key = encrypted_key[5:]
        
        # 使用 Windows DPAPI 解密
        import win32crypt
        decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        
        print(f"[OK] Encryption key obtained (length: {len(decrypted_key)})")
        return decrypted_key
        
    except ImportError:
        print("[ERROR] pywin32 not installed. Run: pip install pywin32")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to get encryption key: {e}")
        return None


def decrypt_cookie_value(encrypted_value: bytes, key: bytes) -> Optional[str]:
    """解密 Chrome cookie 值"""
    try:
        from Crypto.Cipher import AES
        
        # 檢查前綴
        if encrypted_value[:3] == b'v10' or encrypted_value[:3] == b'v11':
            # Chrome 80+ 使用 AES-256-GCM
            # 格式: v10/v11 (3 bytes) + nonce (12 bytes) + ciphertext + tag (16 bytes)
            nonce = encrypted_value[3:15]
            ciphertext_with_tag = encrypted_value[15:]
            
            # 分離 ciphertext 和 tag
            # tag 在最後 16 bytes
            ciphertext = ciphertext_with_tag[:-16]
            tag = ciphertext_with_tag[-16:]
            
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            
            return decrypted.decode('utf-8')
        else:
            # 舊版 DPAPI 加密
            import win32crypt
            decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1]
            return decrypted.decode('utf-8')
            
    except ValueError as e:
        # MAC 驗證失敗，嘗試不驗證直接解密
        print(f"[WARN] MAC verification failed: {e}")
        try:
            from Crypto.Cipher import AES
            
            nonce = encrypted_value[3:15]
            ciphertext_with_tag = encrypted_value[15:]
            
            # 嘗試不同的 tag 位置
            for tag_size in [16, 0]:
                try:
                    if tag_size > 0:
                        ciphertext = ciphertext_with_tag[:-tag_size]
                    else:
                        ciphertext = ciphertext_with_tag
                    
                    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                    decrypted = cipher.decrypt(ciphertext)
                    
                    # 嘗試解碼
                    text = decrypted.decode('utf-8', errors='ignore')
                    
                    # 檢查是否包含有效 JSON
                    if '{' in text and '}' in text:
                        # 找到 JSON 邊界
                        start = text.find('{')
                        end = text.rfind('}') + 1
                        if start >= 0 and end > start:
                            json_str = text[start:end]
                            # 驗證是否為有效 JSON
                            json.loads(json_str)
                            return json_str
                except:
                    continue
                    
        except Exception as e2:
            print(f"[ERROR] Fallback decryption failed: {e2}")
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Decryption error: {e}")
        return None


def read_cookies_from_chrome() -> Optional[str]:
    """從 Chrome Profile 讀取 login-session cookie"""
    
    # 找到 cookies 資料庫
    cookies_db = CHROME_PROFILE_DIR / "Default" / "Network" / "Cookies"
    if not cookies_db.exists():
        cookies_db = CHROME_PROFILE_DIR / "Default" / "Cookies"
    
    if not cookies_db.exists():
        print(f"[ERROR] Cookies database not found: {cookies_db}")
        return None
    
    print(f"[OK] Found cookies database: {cookies_db}")
    
    # 獲取加密密鑰
    key = get_chrome_encryption_key()
    if not key:
        return None
    
    try:
        # 複製資料庫（避免鎖定問題）
        temp_db = CHROME_PROFILE_DIR / "cookies_temp.db"
        shutil.copy2(cookies_db, temp_db)
        
        # 連接資料庫
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        
        # 查詢 login-session cookie
        cursor.execute("""
            SELECT name, encrypted_value, host_key 
            FROM cookies 
            WHERE name = 'login-session' AND host_key LIKE '%formula1%'
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # 清理臨時檔案
        temp_db.unlink()
        
        if not rows:
            print("[ERROR] login-session cookie not found")
            return None
        
        print(f"[OK] Found {len(rows)} login-session cookie(s)")
        
        for name, encrypted_value, host in rows:
            print(f"[INFO] Processing cookie from {host}...")
            
            decrypted = decrypt_cookie_value(encrypted_value, key)
            
            if decrypted:
                print(f"[OK] Successfully decrypted cookie (length: {len(decrypted)})")
                return decrypted
            else:
                print(f"[WARN] Failed to decrypt cookie from {host}")
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return None


def extract_token_from_cookie(cookie_value: str) -> Optional[str]:
    """從 cookie 值中提取 subscriptionToken"""
    try:
        # URL 解碼
        decoded = urllib.parse.unquote(cookie_value)
        
        # 解析 JSON
        data = json.loads(decoded)
        
        # 提取 subscriptionToken
        token = data.get('data', {}).get('subscriptionToken')
        
        if token:
            print(f"[OK] Extracted subscriptionToken (length: {len(token)})")
            return token
        else:
            print("[ERROR] No subscriptionToken in cookie data")
            print(f"[DEBUG] Available keys: {list(data.keys())}")
            if 'data' in data:
                print(f"[DEBUG] data keys: {list(data.get('data', {}).keys())}")
            return None
            
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error: {e}")
        print(f"[DEBUG] Cookie value (first 200 chars): {cookie_value[:200]}")
        return None
    except Exception as e:
        print(f"[ERROR] Token extraction error: {e}")
        return None


def save_token(token: str):
    """儲存 token"""
    AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'subscriptionToken': token,
        'saved_at': datetime.now().isoformat(),
        'source': 'chrome_cookie_decrypt'
    }
    
    with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"[OK] Token saved to {AUTH_DATA_FILE}")


def main():
    """主程式"""
    print("\n" + "=" * 60)
    print("F1TV Chrome Cookie Decryptor")
    print("=" * 60 + "\n")
    
    # 檢查 Chrome Profile 是否存在
    if not CHROME_PROFILE_DIR.exists():
        print(f"[ERROR] Chrome profile not found: {CHROME_PROFILE_DIR}")
        print("\nPlease run f1tv_chrome_login.py first to login via Chrome.")
        return 1
    
    # 讀取並解密 cookie
    cookie_value = read_cookies_from_chrome()
    
    if not cookie_value:
        print("\n[FAILED] Could not read login-session cookie.")
        return 1
    
    # 提取 token
    token = extract_token_from_cookie(cookie_value)
    
    if not token:
        print("\n[FAILED] Could not extract token from cookie.")
        return 1
    
    # 儲存 token
    save_token(token)
    
    print("\n" + "=" * 60)
    print("SUCCESS! Token extracted and saved.")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
