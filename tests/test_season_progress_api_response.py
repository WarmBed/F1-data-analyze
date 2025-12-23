#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Season Progress API 響應格式
驗證外網 API 返回的資訊是否符合 GUI 期望
"""

import sys
import json
import requests
from typing import Dict, Any

# 設定 UTF-8 編碼
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 80)
print("Season Progress API 響應測試")
print("=" * 80)
print()

# API 配置
API_BASE_URL = "https://api.f1telemetrystationpro.org"
FUNCTION_ID = 97
YEAR = 2025

print(f"[配置]")
print(f"  API URL: {API_BASE_URL}")
print(f"  Function ID: {FUNCTION_ID}")
print(f"  Year: {YEAR}")
print()

# 步驟 1: 發送 API 請求
print("=" * 80)
print("[步驟 1] 發送 API 請求")
print("=" * 80)

try:
    endpoint = f"{API_BASE_URL}/api/v2/analysis/execute"
    params = {
        "function_id": FUNCTION_ID,
        "year": YEAR
    }
    
    print(f"請求 URL: {endpoint}")
    print(f"參數: {params}")
    print()
    print("發送請求中...")
    
    response = requests.post(endpoint, params=params, timeout=30)
    
    print(f"[OK] HTTP 狀態碼: {response.status_code}")
    
    if response.status_code != 200:
        print(f"[ERROR] HTTP 錯誤: {response.status_code}")
        print(f"響應內容: {response.text[:500]}")
        sys.exit(1)
    
    # 解析 JSON
    api_response = response.json()
    print(f"[OK] JSON 解析成功")
    
except Exception as e:
    print(f"[ERROR] API 請求失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 步驟 2: 檢查響應結構
print()
print("=" * 80)
print("[步驟 2] 檢查響應結構")
print("=" * 80)

print(f"響應頂層鍵: {list(api_response.keys())}")
print()

# 檢查 success 欄位
success = api_response.get("success")
print(f"success: {success}")
if not success:
    print(f"[ERROR] API 返回 success=False")
    print(f"message: {api_response.get('message')}")
    sys.exit(1)

# 檢查 data 欄位
data = api_response.get("data")
if not isinstance(data, dict):
    print(f"[ERROR] data 欄位不是 dict，而是 {type(data)}")
    sys.exit(1)

print(f"[OK] data 欄位存在且為 dict")
print(f"data 鍵: {list(data.keys())}")
print()

# 步驟 3: 檢查數據結構（模擬 MDI 的處理邏輯）
print("=" * 80)
print("[步驟 3] 檢查數據結構（模擬 MDI 處理）")
print("=" * 80)

# 檢測嵌套結構
if "data" in data and isinstance(data["data"], dict):
    print("[檢測] Double-nested structure (data.data)")
    metadata = data.get("metadata", {})
    data_payload = data.get("data", {})
else:
    print("[檢測] Single-layer structure")
    metadata = data.get("metadata", {})
    data_payload = data

print()

# 檢查必要欄位
drivers = data_payload.get("drivers", [])
constructors = data_payload.get("constructors", [])

print(f"drivers: {len(drivers)} 項")
print(f"constructors: {len(constructors)} 項")
print(f"metadata: {metadata}")
print()

if not drivers and not constructors:
    print("[ERROR] 缺少 drivers 和 constructors 資料")
    sys.exit(1)

print(f"[OK] 數據包含 {len(drivers)} 位車手和 {len(constructors)} 支車隊")

# 步驟 4: 檢查第一位車手資料結構
print()
print("=" * 80)
print("[步驟 4] 檢查車手資料結構")
print("=" * 80)

if drivers:
    first_driver = drivers[0]
    print(f"第一位車手資料鍵: {list(first_driver.keys())}")
    print()
    print(f"車手詳細資料:")
    print(f"  driver: {first_driver.get('driver', {})}")
    print(f"  points: {first_driver.get('points')}")
    print(f"  constructors: {first_driver.get('constructors', [])}")
else:
    print("[WARN] 無車手資料")

# 步驟 5: 模擬 DataLoader 轉換
print()
print("=" * 80)
print("[步驟 5] 模擬 DataLoader 轉換")
print("=" * 80)

try:
    from modules.gui.season_progress.season_progress_data_loader import SeasonProgressDataLoader
    
    loader = SeasonProgressDataLoader(str(YEAR))
    
    # 構建 raw_data（模擬 MDI 的處理）
    raw_data_for_transform = {
        "success": True,
        "data": {
            "drivers": drivers,
            "constructors": constructors,
            "metadata": metadata
        }
    }
    
    print("[執行] loader._transform_data_for_display()")
    display_data = loader._transform_data_for_display(raw_data_for_transform)
    
    print(f"[OK] 轉換成功")
    print()
    print(f"轉換後的資料鍵: {list(display_data.keys())}")
    print()
    print(f"詳細資料:")
    print(f"  season_year: {display_data.get('season_year')}")
    print(f"  round: {display_data.get('round')}")
    print(f"  leaders: {display_data.get('leaders')}")
    print(f"  calendar: {display_data.get('calendar')}")
    
except Exception as e:
    print(f"[ERROR] 轉換失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 步驟 6: 檢查 Widget 期望的資料
print()
print("=" * 80)
print("[步驟 6] 檢查 Widget 期望的資料格式")
print("=" * 80)

required_keys = ["season_year", "round", "leaders", "calendar", "metadata"]
missing_keys = [key for key in required_keys if key not in display_data]

if missing_keys:
    print(f"[ERROR] 缺少必要鍵: {missing_keys}")
    sys.exit(1)
else:
    print(f"[OK] 所有必要鍵都存在")

# 檢查 leaders 結構
leaders = display_data.get("leaders", {})
if "driver" not in leaders or "constructor" not in leaders:
    print(f"[ERROR] leaders 缺少 driver 或 constructor")
    sys.exit(1)

print(f"[OK] leaders 結構正確")
print(f"  driver: {leaders.get('driver')}")
print(f"  constructor: {leaders.get('constructor')}")

# 檢查 calendar 結構
calendar = display_data.get("calendar", {})
calendar_keys = ["completed", "remaining", "total", "next_race"]
missing_calendar = [key for key in calendar_keys if key not in calendar]

if missing_calendar:
    print(f"[WARN] calendar 缺少某些鍵: {missing_calendar}")
else:
    print(f"[OK] calendar 結構完整")
    print(f"  completed: {calendar.get('completed')}")
    print(f"  remaining: {calendar.get('remaining')}")
    print(f"  total: {calendar.get('total')}")
    print(f"  next_race: {calendar.get('next_race')}")

# 最終結果
print()
print("=" * 80)
print("[SUCCESS] 所有測試通過！")
print("=" * 80)
print()
print("結論:")
print("  ✓ API 響應格式正確")
print("  ✓ 數據結構符合預期")
print("  ✓ DataLoader 轉換成功")
print("  ✓ Widget 可以正確讀取資料")
print()
print("建議:")
print("  → 可以安全地在 Season Progress GUI 中使用外網 API")
