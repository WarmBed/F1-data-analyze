#!/usr/bin/env python3
"""手動解密 Chrome Cookie"""

import sqlite3
import shutil
import base64
import json
from pathlib import Path

CHROME_PROFILE_DIR = Path.home() / '.f1t' / 'chrome_profile'

# Step 1: 獲取加密密鑰
print("Step 1: Getting encryption key...")
local_state_path = CHROME_PROFILE_DIR / "Local State"

with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)

encrypted_key_b64 = local_state['os_crypt']['encrypted_key']
encrypted_key = base64.b64decode(encrypted_key_b64)
encrypted_key = encrypted_key[5:]  # 移除 'DPAPI' 前綴

import win32crypt
key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
print(f"Key length: {len(key)} bytes")
print(f"Key (hex): {key.hex()}")

# Step 2: 讀取加密的 cookie
print("\nStep 2: Reading encrypted cookie...")
cookies_db = CHROME_PROFILE_DIR / 'Default' / 'Network' / 'Cookies'
temp_db = CHROME_PROFILE_DIR / 'cookies_temp.db'
shutil.copy2(cookies_db, temp_db)

conn = sqlite3.connect(str(temp_db))
cursor = conn.cursor()
cursor.execute("SELECT encrypted_value FROM cookies WHERE name = 'login-session' AND host_key LIKE '%formula1%'")
row = cursor.fetchone()
conn.close()
temp_db.unlink()

if not row:
    print("Cookie not found!")
    exit(1)

encrypted_value = row[0]
print(f"Encrypted value length: {len(encrypted_value)}")
print(f"Prefix: {encrypted_value[:3]}")

# Step 3: 解密
print("\nStep 3: Decrypting...")

# v10 格式: v10 (3 bytes) + nonce (12 bytes) + ciphertext + tag (16 bytes)
nonce = encrypted_value[3:15]
ciphertext_with_tag = encrypted_value[15:]

print(f"Nonce (hex): {nonce.hex()}")
print(f"Ciphertext+tag length: {len(ciphertext_with_tag)}")

from Crypto.Cipher import AES

# 方法 1: 標準 GCM 解密
print("\nTrying standard GCM decrypt...")
try:
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    # Chrome 的格式是 ciphertext 後面直接跟著 tag
    decrypted = cipher.decrypt_and_verify(ciphertext_with_tag[:-16], ciphertext_with_tag[-16:])
    print(f"SUCCESS! Decrypted length: {len(decrypted)}")
    print(f"First 100 chars: {decrypted[:100]}")
except Exception as e:
    print(f"Failed: {e}")

# 方法 2: 只解密不驗證
print("\nTrying decrypt without verify...")
try:
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypted = cipher.decrypt(ciphertext_with_tag)
    
    # 嘗試找到 JSON
    text = decrypted.decode('utf-8', errors='replace')
    print(f"Raw decrypted (first 200): {repr(text[:200])}")
    
    # 尋找 JSON 開始位置
    if '{' in text:
        start = text.find('{')
        print(f"JSON starts at position: {start}")
        print(f"JSON preview: {text[start:start+200]}")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
