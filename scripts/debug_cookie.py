#!/usr/bin/env python3
"""Debug Chrome Cookie"""

import sqlite3
import shutil
from pathlib import Path

CHROME_PROFILE_DIR = Path.home() / '.f1t' / 'chrome_profile'
cookies_db = CHROME_PROFILE_DIR / 'Default' / 'Network' / 'Cookies'

# 複製資料庫
temp_db = CHROME_PROFILE_DIR / 'cookies_temp.db'
shutil.copy2(cookies_db, temp_db)

conn = sqlite3.connect(str(temp_db))
cursor = conn.cursor()

cursor.execute('''
    SELECT name, encrypted_value, host_key 
    FROM cookies 
    WHERE name = 'login-session'
''')

for name, enc_val, host in cursor.fetchall():
    print(f'Host: {host}')
    print(f'Encrypted value length: {len(enc_val)}')
    print(f'First 20 bytes (hex): {enc_val[:20].hex()}')
    print(f'Prefix bytes: {enc_val[:3]}')
    print(f'Is v10/v11: {enc_val[:3] in [b"v10", b"v11"]}')
    print()

conn.close()
temp_db.unlink()
