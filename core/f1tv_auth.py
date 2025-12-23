# -*- coding: utf-8 -*-
"""
F1TV 認證管理器

用途: 管理 F1TV 帳號認證，獲取 subscriptionToken 以連接 signalrcore 端點
使用 PyQtWebEngine (QWebEngineView) 進行實際登入流程
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal

from core.logger import get_logger

logger = get_logger(__name__)

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"


class F1TVAuthManager(QObject):
    """
    F1TV 認證管理器
    
    負責管理 F1TV 帳號認證狀態，包括:
    - 儲存/讀取 token
    - 驗證 token 有效性
    - 啟動 QWebEngineView 登入對話框
    """
    
    # 信號
    auth_success = pyqtSignal(str)      # 認證成功，傳回 token
    auth_failed = pyqtSignal(str)       # 認證失敗，傳回錯誤訊息
    auth_status = pyqtSignal(str)       # 認證狀態更新
    auth_state_changed = pyqtSignal(bool)  # 認證狀態變更 (True = 已登入)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._token: Optional[str] = None
        self._auth_dialog = None  # QWebEngineView 對話框
        self._raw_cookie: Optional[str] = None  # 原始 login-session cookie
        
        # 嘗試載入已存儲的 token
        self._load_saved_token()
    
    def _load_saved_token(self):
        """載入已存儲的 token"""
        if not AUTH_DATA_FILE.exists():
            logger.debug("No saved token file found at %s", AUTH_DATA_FILE)
            return
        
        try:
            with open(AUTH_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            token = data.get('subscriptionToken')
            self._raw_cookie = data.get('rawCookie')
            
            if token and self._verify_token(token):
                self._token = token
                logger.info("Loaded valid token from storage")
                # 發送狀態變更信號
                self.auth_state_changed.emit(True)
            else:
                logger.warning("Saved token is expired or invalid")
                self._token = None
                
        except Exception as e:
            logger.error("Failed to load saved token: %s", e)
            self._token = None
    
    def _verify_token(self, token: str) -> bool:
        """驗證 token 是否有效（檢查過期時間）"""
        try:
            import jwt
            
            # 解碼但不驗證簽名（只檢查過期時間）
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get('exp', 0)
            
            is_valid = exp > datetime.now().timestamp()
            
            if is_valid:
                exp_time = datetime.fromtimestamp(exp)
                logger.debug("Token valid until: %s", exp_time)
            else:
                logger.warning("Token has expired")
            
            return is_valid
            
        except Exception as e:
            logger.error("Token verification error: %s", e)
            return False
    
    def is_authenticated(self) -> bool:
        """檢查是否已認證（有有效的 token）"""
        if not self._token:
            return False
        return self._verify_token(self._token)
    
    def get_token(self) -> Optional[str]:
        """獲取 token（如果有效）"""
        if self.is_authenticated():
            return self._token
        return None
    
    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """獲取 token 的詳細資訊"""
        if not self._token:
            return None
        
        try:
            import jwt
            
            decoded = jwt.decode(self._token, options={"verify_signature": False})
            
            exp = decoded.get('exp', 0)
            exp_time = datetime.fromtimestamp(exp) if exp else None
            is_expired = exp <= datetime.now().timestamp() if exp else True
            
            return {
                'subscription_status': decoded.get('SubscriptionStatus', 'Unknown'),
                'product': decoded.get('SubscribedProduct', 'F1TV'),
                'exp': exp,
                'exp_str': exp_time.strftime('%Y-%m-%d %H:%M') if exp_time else 'Unknown',
                'expired': is_expired,
                'is_valid': not is_expired
            }
            
        except Exception as e:
            logger.error("Error getting token info: %s", e)
            return {
                'error': str(e),
                'expired': True,
                'is_valid': False
            }
    
    def start_auth_flow(self, parent_widget=None):
        """
        啟動認證流程
        
        使用獨立進程運行 pywebview 登入，避免與 PyQt5 衝突。
        參考 undercut-f1 的實現方式。
        
        Args:
            parent_widget: 父視窗 widget（用於對話框）
        """
        logger.info("Starting F1TV authentication flow...")
        self.auth_status.emit("Starting authentication...")
        
        # 使用 Chrome Profile 登入 + Cookie 解密方式
        self._run_chrome_profile_auth()
    
    def _run_chrome_profile_auth(self):
        """
        使用 Chrome Profile 進行認證 - 主要方式
        
        流程:
        1. 啟動 Chrome 瀏覽器（使用獨立 profile）
        2. 用戶在瀏覽器中登入 F1TV
        3. 用戶關閉瀏覽器後自動解密 cookie 提取 token
        """
        import subprocess
        import os
        from pathlib import Path
        
        # Chrome Profile 目錄
        chrome_profile_dir = Path.home() / ".f1t" / "chrome_profile"
        chrome_profile_dir.mkdir(parents=True, exist_ok=True)
        
        # 找到瀏覽器
        browser_path = self._find_browser()
        if not browser_path:
            self._on_auth_failed("Cannot find Chrome or Edge browser. Please install Chrome.")
            return
        
        # F1 登入 URL
        login_url = "https://account.formula1.com/#/en/login?redirect=https%3A%2F%2Ff1tv.formula1.com%2F"
        
        # 瀏覽器啟動參數
        args = [
            str(browser_path),
            f"--user-data-dir={chrome_profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            login_url
        ]
        
        logger.info("Launching browser for F1TV login...")
        logger.info("Profile directory: %s", chrome_profile_dir)
        self.auth_status.emit("Opening browser for login...")
        
        try:
            # 啟動瀏覽器（阻塞直到關閉）
            process = subprocess.Popen(args)
            process.wait()
            
            logger.info("Browser closed, extracting token from cookies...")
            self.auth_status.emit("Extracting token from cookies...")
            
            # 解密 cookie 提取 token
            token = self._decrypt_chrome_cookie(chrome_profile_dir)
            
            if token:
                self._on_auth_success(token)
            else:
                self._on_auth_failed("Could not extract token. Please make sure you logged in successfully.")
                
        except Exception as e:
            error_msg = f"Browser login error: {e}"
            logger.error(error_msg)
            self._on_auth_failed(error_msg)
    
    def _find_browser(self) -> Optional[Path]:
        """尋找系統安裝的 Chrome 或 Edge"""
        import os
        
        # Chrome 路徑
        chrome_paths = [
            Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ]
        
        # Edge 路徑
        edge_paths = [
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ]
        
        # 優先 Chrome
        for path in chrome_paths:
            if path.exists():
                logger.info("Found Chrome: %s", path)
                return path
        
        # 其次 Edge
        for path in edge_paths:
            if path.exists():
                logger.info("Found Edge: %s", path)
                return path
        
        return None
    
    def _decrypt_chrome_cookie(self, profile_dir: Path) -> Optional[str]:
        """
        解密 Chrome cookie 提取 F1TV token
        
        Args:
            profile_dir: Chrome profile 目錄
            
        Returns:
            subscriptionToken 或 None
        """
        import base64
        import json
        import re
        import shutil
        import sqlite3
        import urllib.parse
        
        try:
            # Step 1: 獲取加密密鑰
            local_state_path = profile_dir / "Local State"
            if not local_state_path.exists():
                logger.error("Local State file not found")
                return None
            
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            encrypted_key_b64 = local_state['os_crypt']['encrypted_key']
            encrypted_key = base64.b64decode(encrypted_key_b64)
            encrypted_key = encrypted_key[5:]  # 移除 'DPAPI' 前綴
            
            # 使用 Windows DPAPI 解密
            import win32crypt
            key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            logger.debug("Got encryption key (%d bytes)", len(key))
            
            # Step 2: 讀取加密的 cookie
            cookies_db = profile_dir / 'Default' / 'Network' / 'Cookies'
            if not cookies_db.exists():
                cookies_db = profile_dir / 'Default' / 'Cookies'
            
            if not cookies_db.exists():
                logger.error("Cookies database not found")
                return None
            
            # 複製資料庫（避免鎖定問題）
            temp_db = profile_dir / 'cookies_temp.db'
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
                logger.warning("login-session cookie not found")
                return None
            
            encrypted_value = row[0]
            logger.debug("Found encrypted cookie (%d bytes)", len(encrypted_value))
            
            # Step 3: AES-256-GCM 解密
            from Crypto.Cipher import AES
            
            # v10 格式: v10 (3 bytes) + nonce (12 bytes) + ciphertext + tag (16 bytes)
            nonce = encrypted_value[3:15]
            ciphertext_with_tag = encrypted_value[15:]
            
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            decrypted = cipher.decrypt_and_verify(
                ciphertext_with_tag[:-16], 
                ciphertext_with_tag[-16:]
            )
            
            text = decrypted.decode('utf-8', errors='replace')
            logger.debug("Decrypted cookie (%d chars)", len(text))
            
            # Step 4: 提取 JSON
            # 尋找 URL 編碼的 JSON: %7B%22data%22 = {"data"
            json_match = re.search(r'(%7B%22data%22.+)', text)
            
            if not json_match:
                logger.error("Could not find JSON pattern in decrypted data")
                return None
            
            url_encoded = json_match.group(1)
            decoded_json = urllib.parse.unquote(url_encoded)
            
            # 清理結尾 - 找到最後完整的 }
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
            
            data = json.loads(decoded_json)
            token = data.get('data', {}).get('subscriptionToken')
            
            if token:
                logger.info("Token extracted successfully (length: %d)", len(token))
                return token
            else:
                logger.error("subscriptionToken not found in JSON")
                return None
                
        except ImportError as e:
            logger.error("Missing required module: %s", e)
            logger.error("Please install: pip install pywin32 pycryptodome")
            return None
        except Exception as e:
            logger.error("Cookie decryption error: %s", e)
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    # =========================================================================
    # 回調方法
    # =========================================================================
    
    def _on_auth_success(self, token: str):
        """認證成功回調"""
        logger.info("Authentication successful")
        self._token = token
        self._save_token(token)
        self.auth_success.emit(token)
        self.auth_state_changed.emit(True)
    
    def _on_auth_failed(self, error: str):
        """認證失敗回調"""
        logger.error("Authentication failed: %s", error)
        self.auth_failed.emit(error)
    
    def _on_auth_cancelled(self):
        """認證取消回調"""
        logger.info("Authentication cancelled by user")
        self.auth_failed.emit("Authentication cancelled")
    
    def _save_token(self, token: str, raw_cookie: Optional[str] = None):
        """
        儲存 token 到檔案
        
        Args:
            token: subscriptionToken
            raw_cookie: 原始 login-session cookie (可選，用於備份)
        """
        try:
            AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # 獲取 token 資訊
            token_info = self.get_token_info()
            
            data = {
                'subscriptionToken': token,
                'saved_at': datetime.now().isoformat(),
                'expires_at': token_info.get('exp_str') if token_info else None,
                'product': token_info.get('product') if token_info else None,
            }
            
            # 如果有原始 cookie，也儲存
            if raw_cookie:
                data['rawCookie'] = raw_cookie
            
            with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info("Token saved to %s", AUTH_DATA_FILE)
            
        except Exception as e:
            logger.error("Failed to save token: %s", e)
    
    def clear_token(self):
        """清除已存儲的 token"""
        self._token = None
        self._raw_cookie = None
        
        if AUTH_DATA_FILE.exists():
            try:
                AUTH_DATA_FILE.unlink()
                logger.info("Token file deleted: %s", AUTH_DATA_FILE)
            except Exception as e:
                logger.error("Failed to clear token file: %s", e)
        
        self.auth_state_changed.emit(False)
        logger.info("F1TV token cleared")
    
    def get_token_file_path(self) -> Path:
        """獲取 token 存儲路徑"""
        return AUTH_DATA_FILE
    
    def reload_token(self) -> bool:
        """
        重新載入 token
        
        Returns:
            True 如果成功載入有效 token
        """
        self._load_saved_token()
        return self.is_authenticated()
    
    def cancel_auth(self):
        """取消正在進行的認證"""
        if self._auth_dialog:
            self._auth_dialog.reject()
            self._auth_dialog = None
            logger.info("Authentication cancelled")
