#!/usr/bin/env python3
"""
F1TV Chrome Cookie 解密器 - 最終版本

直接從 Chrome Profile 解密讀取 login-session cookie 並提取 token。
"""

import base64
import json
import re
import shutil
import sqlite3
import urllib.parse
from datetime import datetime
from pathlib import Path

# Chrome profile 目錄
CHROME_PROFILE_DIR = Path.home() / ".f1t" / "chrome_profile"

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"


def decrypt_and_extract_token():
    """解密 Chrome cookie 並提取 token"""
    
    print("=" * 60)
    print("F1TV Chrome Cookie Decryptor")
    print("=" * 60)
    
    # Step 1: 獲取加密密鑰
    print("\n[1] Getting Chrome encryption key...")
    local_state_path = CHROME_PROFILE_DIR / "Local State"
    
    if not local_state_path.exists():
        print(f"[ERROR] Local State not found: {local_state_path}")
        print("Please login via Chrome first using f1tv_chrome_login.py")
        return None
    
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    
    encrypted_key_b64 = local_state['os_crypt']['encrypted_key']
    encrypted_key = base64.b64decode(encrypted_key_b64)
    encrypted_key = encrypted_key[5:]  # 移除 'DPAPI' 前綴
    
    import win32crypt
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    print(f"[OK] Encryption key obtained ({len(key)} bytes)")
    
    # Step 2: 讀取加密的 cookie
    print("\n[2] Reading encrypted cookie from database...")
    cookies_db = CHROME_PROFILE_DIR / 'Default' / 'Network' / 'Cookies'
    if not cookies_db.exists():
        cookies_db = CHROME_PROFILE_DIR / 'Default' / 'Cookies'
    
    if not cookies_db.exists():
        print(f"[ERROR] Cookies database not found")
        return None
    
    temp_db = CHROME_PROFILE_DIR / 'cookies_temp.db'
    shutil.copy2(cookies_db, temp_db)
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT encrypted_value FROM cookies 
        WHERE name = 'login-session' AND host_key LIKE '%formula1%'
    """)
    row = cursor.fetchone()
    conn.close()
    temp_db.unlink()
    
    if not row:
        print("[ERROR] login-session cookie not found")
        print("Please login via Chrome first using f1tv_chrome_login.py")
        return None
    
    encrypted_value = row[0]
    print(f"[OK] Found encrypted cookie ({len(encrypted_value)} bytes)")
    
    # Step 3: 解密
    print("\n[3] Decrypting cookie...")
    
    from Crypto.Cipher import AES
    
    # v10 格式: v10 (3 bytes) + nonce (12 bytes) + ciphertext + tag (16 bytes)
    nonce = encrypted_value[3:15]
    ciphertext_with_tag = encrypted_value[15:]
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypted = cipher.decrypt_and_verify(ciphertext_with_tag[:-16], ciphertext_with_tag[-16:])
    
    # 轉換為文字，忽略開頭的垃圾字節
    text = decrypted.decode('utf-8', errors='replace')
    print(f"[OK] Decrypted ({len(text)} chars)")
    
    # Step 4: 提取 JSON
    print("\n[4] Extracting token from decrypted data...")
    
    # 尋找 URL 編碼的 JSON 開始位置
    # 格式: %7B%22data%22... = {"data"...
    json_match = re.search(r'(%7B%22data%22.+)', text)
    
    if json_match:
        url_encoded = json_match.group(1)
        # URL 解碼
        decoded_json = urllib.parse.unquote(url_encoded)
        
        # 清理可能的結尾垃圾
        # 找到最後一個完整的 }
        brace_count = 0
        end_pos = 0
        for i, c in enumerate(decoded_json):
            if c == '{':
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        
        if end_pos > 0:
            decoded_json = decoded_json[:end_pos]
        
        # 解析 JSON
        data = json.loads(decoded_json)
        token = data.get('data', {}).get('subscriptionToken')
        
        if token:
            print(f"[OK] Token extracted! (length: {len(token)})")
            return token
        else:
            print("[ERROR] subscriptionToken not found in JSON")
            print(f"Available keys: {list(data.keys())}")
            return None
    else:
        print("[ERROR] Could not find JSON pattern in decrypted data")
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
    
    print(f"\n[OK] Token saved to {AUTH_DATA_FILE}")


def main():
    """主程式"""
    token = decrypt_and_extract_token()
    
    if token:
        save_token(token)
        
        # 驗證 token
        try:
            import jwt
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get('exp', 0)
            exp_time = datetime.fromtimestamp(exp)
            status = decoded.get('SubscriptionStatus', 'Unknown')
            product = decoded.get('SubscribedProduct', 'Unknown')
            
            print("\n" + "=" * 60)
            print("TOKEN INFO:")
            print(f"  Status: {status}")
            print(f"  Product: {product}")
            print(f"  Expires: {exp_time}")
            print(f"  Valid: {exp > datetime.now().timestamp()}")
            print("=" * 60)
        except:
            pass
        
        print("\nSUCCESS! F1TV authentication completed.")
        return 0
    else:
        print("\nFAILED: Could not extract token.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
