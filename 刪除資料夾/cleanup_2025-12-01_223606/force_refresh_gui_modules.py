#!/usr/bin/env python3
"""強制刷新 Season Progress 和 Weather Timeline 數據"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("強制刷新 GUI 模組數據")
print("=" * 80)
print()

# 1. 強制刷新 Season Progress (Function 97 - 2025)
print("🔄 [1/2] 強制刷新 Season Progress (Function 97)...")
print("-" * 80)

params_97 = {
    'function_id': '97',
    'year': 2025,
    'force_refresh': True
}

try:
    start = datetime.now()
    resp = requests.post(f'{API_BASE_URL}/api/v2/analysis/execute', params=params_97, timeout=120)
    elapsed = (datetime.now() - start).total_seconds()
    
    result = resp.json()
    print(f"   ✅ 完成 (耗時: {elapsed:.2f}s)")
    print(f"   ├─ 狀態: {result.get('success')}")
    print(f"   ├─ 來源: {result.get('source')}")
    print(f"   └─ 訊息: {result.get('message')}")
    
    data = result.get('data', {})
    drivers = data.get('drivers', [])
    constructors = data.get('constructors', [])
    print(f"   📊 數據: {len(drivers)} 車手, {len(constructors)} 車隊")
    
except Exception as e:
    print(f"   ❌ 失敗: {e}")

print()

# 2. 強制刷新 Weather Timeline (Function 96 - 2025 Las Vegas)
print("🔄 [2/2] 強制刷新 Weather Timeline (Function 96)...")
print("-" * 80)

params_96 = {
    'function_id': '96',
    'year': 2025,
    'race': 'Las Vegas',  # 下一場比賽
    'force_refresh': True
}

try:
    start = datetime.now()
    resp = requests.post(f'{API_BASE_URL}/api/v2/analysis/execute', params=params_96, timeout=120)
    elapsed = (datetime.now() - start).total_seconds()
    
    result = resp.json()
    print(f"   ✅ 完成 (耗時: {elapsed:.2f}s)")
    print(f"   ├─ 狀態: {result.get('success')}")
    print(f"   ├─ 來源: {result.get('source')}")
    print(f"   └─ 訊息: {result.get('message')}")
    
    data = result.get('data', {})
    if 'forecast' in data:
        forecast = data['forecast']
        print(f"   🌤️ 天氣預報: {len(forecast.get('hourly', []))} 小時數據")
    
except Exception as e:
    print(f"   ❌ 失敗: {e}")

print()
print("=" * 80)
print("✅ 所有數據已刷新完成")
print("=" * 80)
