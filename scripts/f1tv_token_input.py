#!/usr/bin/env python3
"""
F1TV Token 輸入工具

手動輸入 login-session cookie 值來保存 token。
這是當自動方式失敗時的備用方案。

使用方式:
    python scripts/f1tv_token_input.py "cookie_value"
    
或者不帶參數運行，會提示輸入：
    python scripts/f1tv_token_input.py
"""

import json
import sys
import urllib.parse
from pathlib import Path
from datetime import datetime

# Token 存儲路徑
AUTH_DATA_FILE = Path.home() / ".f1t" / "f1auth.json"


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
            'subscriber_id': decoded.get('SubscriberId', 'Unknown'),
            'first_name': decoded.get('FirstName', ''),
            'last_name': decoded.get('LastName', ''),
            'expires_at': exp_time.isoformat() if exp_time else None,
            'is_valid': exp > datetime.now().timestamp() if exp else False
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'is_valid': False
        }


def save_token(cookie_value: str) -> bool:
    """從 cookie 值提取並保存 token"""
    try:
        # URL 解碼
        decoded = urllib.parse.unquote(cookie_value)
        
        # 解析 JSON
        data = json.loads(decoded)
        
        # 提取 subscriptionToken
        token = data.get('data', {}).get('subscriptionToken')
        
        if not token:
            print("[ERROR] No subscriptionToken found in cookie data")
            print(f"[DEBUG] Cookie keys: {list(data.keys())}")
            if 'data' in data:
                print(f"[DEBUG] data keys: {list(data.get('data', {}).keys())}")
            return False
        
        print(f"[OK] Token extracted (length: {len(token)})")
        
        # 獲取 token 資訊
        info = get_token_info(token)
        
        if not info.get('is_valid'):
            print("[WARNING] Token appears to be expired or invalid")
        
        # 保存到檔案
        AUTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        save_data = {
            'subscriptionToken': token,
            'formula1AccessToken': cookie_value,
            'saved_at': datetime.now().isoformat(),
            'expires_at': info.get('expires_at'),
            'product': info.get('subscribed_product'),
            'subscription_status': info.get('subscription_status'),
            'subscriber_id': info.get('subscriber_id'),
            'name': f"{info.get('first_name', '')} {info.get('last_name', '')}".strip(),
        }
        
        with open(AUTH_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Token saved to: {AUTH_DATA_FILE}")
        print()
        print("=== Token Info ===")
        print(f"  Name: {save_data.get('name', 'Unknown')}")
        print(f"  Product: {info.get('subscribed_product', 'Unknown')}")
        print(f"  Status: {info.get('subscription_status', 'Unknown')}")
        print(f"  Expires: {info.get('expires_at', 'Unknown')}")
        print()
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse cookie as JSON: {e}")
        print("[TIP] Make sure you copied the entire cookie value")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    print("=" * 60)
    print("F1TV Token Input Tool")
    print("=" * 60)
    print()
    
    # 從命令行參數或提示輸入
    if len(sys.argv) > 1:
        cookie_value = sys.argv[1]
    else:
        print("Please paste your login-session cookie value below.")
        print("(You can get it from F1TV website -> F12 -> Application -> Cookies -> login-session)")
        print()
        cookie_value = input("Cookie value: ").strip()
    
    if not cookie_value:
        print("[ERROR] No cookie value provided")
        sys.exit(1)
    
    print()
    print(f"[INFO] Received cookie (length: {len(cookie_value)})")
    
    if save_token(cookie_value):
        print("[SUCCESS] Token saved successfully!")
        sys.exit(0)
    else:
        print("[FAILED] Could not save token")
        sys.exit(1)


if __name__ == '__main__':
    main()
