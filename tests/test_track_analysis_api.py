#!/usr/bin/env python3
"""測試 Track Analysis API 請求"""

import requests
import time

base_url = "https://localhost:8000"
endpoint = f"{base_url}/api/v2/analysis/execute"

params = {
    "function_id": 2,
    "year": 2025,
    "race": "Singapore",
    "session": "R",
}

print(f"[TEST] 測試 Track Analysis API 請求")
print(f"[TEST] 端點: {endpoint}")
print(f"[TEST] 參數: {params}")
print(f"[TEST] Timeout: 30 秒")
print()

try:
    start = time.time()
    print(f"[TEST] 發送請求...")
    
    response = requests.post(
        endpoint,
        params=params,
        timeout=30.0,
        headers={"Accept": "application/json"}
    )
    
    elapsed = time.time() - start
    print(f"[TEST] ✅ 請求成功！耗時: {elapsed:.2f} 秒")
    print(f"[TEST] 狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[TEST] 回應結構:")
        print(f"[TEST]   success: {data.get('success')}")
        print(f"[TEST]   message: {data.get('message')}")
        print(f"[TEST]   data keys: {list(data.get('data', {}).keys())}")
    else:
        print(f"[TEST] ❌ 錯誤: {response.text}")
        
except requests.Timeout:
    print(f"[TEST] ❌ 請求超時（30 秒）")
except Exception as e:
    print(f"[TEST] ❌ 錯誤: {e}")
