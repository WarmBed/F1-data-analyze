#!/usr/bin/env python3
"""測試 API F127 回應"""
import sys
import json

print("=" * 60, flush=True)
print("Testing API F127 (Traffic Timeline)", flush=True)
print("=" * 60, flush=True)

try:
    import requests
    print("requests imported OK", flush=True)
except ImportError as e:
    print(f"ERROR: {e}", flush=True)
    sys.exit(1)

# API 基礎 URL - 使用公開 API
API_BASE = "https://api.f1telemetrystationpro.org"

# 測試健康端點
print("\n[TEST 1] Health check...", flush=True)
try:
    r = requests.get(f"{API_BASE}/health", timeout=10)
    print(f"  Status: {r.status_code}", flush=True)
    print(f"  Response: {r.text[:200]}", flush=True)
except Exception as e:
    print(f"  ERROR: {e}", flush=True)
    print("  API 可能未運行!", flush=True)
    sys.exit(1)

# 測試 F127 端點
print("\n[TEST 2] F127 Traffic Timeline...", flush=True)
try:
    r = requests.post(
        f"{API_BASE}/api/v2/analysis/execute",
        params={
            "function_id": 127,
            "year": 2025,
            "race": "Qatar",
            "session": "R"
        },
        timeout=180
    )
    print(f"  Status: {r.status_code}", flush=True)
    
    if r.status_code == 200:
        data = r.json()
        print(f"  Success: {data.get('success')}", flush=True)
        print(f"  Message: {data.get('message', 'N/A')}", flush=True)
        
        if "data" in data:
            inner_data = data["data"]
            if isinstance(inner_data, dict):
                print(f"  Data keys: {list(inner_data.keys())}", flush=True)
                if "drivers" in inner_data:
                    drivers = inner_data["drivers"]
                    print(f"  Drivers count: {len(drivers)}", flush=True)
                    if drivers:
                        first_driver = list(drivers.keys())[0]
                        print(f"  First driver: {first_driver}", flush=True)
                        driver_data = drivers[first_driver]
                        print(f"  Driver data keys: {list(driver_data.keys())}", flush=True)
    else:
        print(f"  Response: {r.text[:500]}", flush=True)
        
except Exception as e:
    print(f"  ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60, flush=True)
print("Test complete", flush=True)
