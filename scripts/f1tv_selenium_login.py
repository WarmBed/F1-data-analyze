#!/usr/bin/env python3
"""
F1TV Selenium 自動登入

使用 Selenium 控制真正的 Chrome 瀏覽器進行登入。
登入成功後直接用 driver.get_cookies() 讀取 cookies（不需解密）。

這是最可靠的自動化登入方式。
"""

import json
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

# F1TV URLs
F1_LOGIN_URL = "https://account.formula1.com/#/en/login?redirect=https%3A%2F%2Ff1tv.formula1.com%2F"
F1TV_URL = "https://f1tv.formula1.com"

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"

# Chrome profile 目錄（保持登入狀態）
CHROME_PROFILE_DIR = Path.home() / ".f1t" / "selenium_chrome_profile"


def get_chrome_driver():
    """獲取 Chrome WebDriver"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    
    options = Options()
    
    # 使用獨立的 profile 目錄（保持登入狀態）
    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    
    # 禁用自動化檢測
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # 其他設定
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--start-maximized")
    
    try:
        # 嘗試使用 webdriver-manager 自動管理 ChromeDriver
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except ImportError:
        # 如果沒有 webdriver-manager，嘗試直接使用系統的 chromedriver
        driver = webdriver.Chrome(options=options)
    
    # 移除 webdriver 標記
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def wait_for_login_and_get_token(driver, timeout=300) -> Optional[str]:
    """等待用戶登入並獲取 token"""
    print("\n" + "=" * 60)
    print("Please login with your F1TV account in the browser window.")
    print("The script will automatically detect when you're logged in.")
    print("=" * 60 + "\n")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            current_url = driver.current_url
            
            # 檢查是否已跳轉到 F1TV 首頁（登入成功）
            if 'f1tv.formula1.com' in current_url and 'login' not in current_url.lower():
                print(f"Detected redirect to F1TV: {current_url}")
                
                # 獲取 cookies
                cookies = driver.get_cookies()
                
                for cookie in cookies:
                    if cookie['name'] == 'login-session':
                        print(f"Found login-session cookie!")
                        
                        # 解析 cookie 值
                        cookie_value = cookie['value']
                        decoded = urllib.parse.unquote(cookie_value)
                        
                        try:
                            data = json.loads(decoded)
                            token = data.get('data', {}).get('subscriptionToken')
                            
                            if token:
                                print(f"Successfully extracted subscriptionToken (length: {len(token)})")
                                return token
                            else:
                                print("No subscriptionToken in cookie data")
                                print(f"Available keys: {list(data.keys())}")
                                if 'data' in data:
                                    print(f"Data keys: {list(data.get('data', {}).keys())}")
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse cookie JSON: {e}")
                
                # 如果在 F1TV 但沒找到 cookie，再等一下
                print("On F1TV but login-session cookie not found yet, waiting...")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"Check error: {e}")
            time.sleep(2)
    
    print("Timeout waiting for login")
    return None


def save_token(token: str):
    """儲存 token"""
    AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'subscriptionToken': token,
        'saved_at': datetime.now().isoformat(),
        'source': 'selenium_chrome'
    }
    
    with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Token saved to {AUTH_DATA_FILE}")


def main():
    """主程式"""
    print("\n" + "=" * 60)
    print("F1TV Selenium Authentication")
    print("=" * 60)
    
    driver = None
    
    try:
        print("\nStarting Chrome browser...")
        driver = get_chrome_driver()
        
        print(f"Navigating to F1TV login page...")
        driver.get(F1_LOGIN_URL)
        
        # 等待登入並獲取 token
        token = wait_for_login_and_get_token(driver)
        
        if token:
            save_token(token)
            print("\n" + "=" * 60)
            print("SUCCESS! F1TV authentication completed.")
            print(f"Token saved to: {AUTH_DATA_FILE}")
            print("=" * 60)
            
            # 給用戶看一下成功訊息
            time.sleep(2)
            return 0
        else:
            print("\n" + "=" * 60)
            print("FAILED: Could not obtain token.")
            print("=" * 60)
            return 1
            
    except ImportError as e:
        print(f"\nError: Missing dependency - {e}")
        print("\nPlease install selenium:")
        print("  pip install selenium webdriver-manager")
        return 1
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
        
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()


if __name__ == "__main__":
    import sys
    sys.exit(main())
